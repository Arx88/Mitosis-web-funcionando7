"""
Rutas API del agente - Versión limpia
Endpoints para comunicación con el frontend
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from datetime import datetime
import logging
import time
import uuid
import os
import json
import zipfile
import tempfile
import asyncio
from pathlib import Path
from werkzeug.utils import secure_filename
from src.utils.json_encoder import MongoJSONEncoder, mongo_json_serializer
from src.tools.environment_setup_manager import EnvironmentSetupManager
from src.tools.task_planner import TaskPlanner
from src.tools.execution_engine import ExecutionEngine
from src.tools.tool_manager import ToolManager
from src.orchestration.task_orchestrator import TaskOrchestrator, OrchestrationContext

logger = logging.getLogger(__name__)

agent_bp = Blueprint('agent', __name__)

# Almacenamiento temporal para compartir conversaciones
shared_conversations = {}

# Almacenamiento temporal para archivos por tarea
task_files = {}

# Inicializar componentes
tool_manager = ToolManager()
task_planner = TaskPlanner()
environment_setup_manager = EnvironmentSetupManager()
execution_engine = ExecutionEngine(tool_manager, environment_setup_manager)

# Nuevo sistema de orquestación avanzada
from src.services.ollama_service import OllamaService
from src.memory.advanced_memory_manager import AdvancedMemoryManager
from src.agents.self_reflection_engine import SelfReflectionEngine

ollama_service = OllamaService()

# Inicializar memoria avanzada
memory_manager = AdvancedMemoryManager({
    'working_memory_capacity': 100,
    'episodic_memory_capacity': 2000,
    'semantic_concepts_capacity': 20000,
    'semantic_facts_capacity': 100000,
    'procedural_capacity': 2000,
    'tool_strategies_capacity': 10000,
    'embedding_model': 'all-MiniLM-L6-v2',
    'embedding_storage': '/app/backend/embeddings'
})

# 🔄 Inicializar SelfReflectionEngine
self_reflection_engine = SelfReflectionEngine(
    memory_manager=memory_manager,
    ollama_service=ollama_service,
    config={
        'reflection_after_tasks': True,
        'reflection_after_errors': True,
        'enable_performance_analysis': True,
        'enable_llm_reflection': True,
        'min_reflection_interval': 5,  # minutos
        'max_reflection_interval': 60  # minutos
    }
)

task_orchestrator = TaskOrchestrator(
    tool_manager=tool_manager,
    memory_manager=memory_manager,
    llm_service=ollama_service
)

@agent_bp.route('/orchestrate', methods=['POST'])
async def orchestrate_task():
    """
    Endpoint para orquestar tareas usando el nuevo sistema de orquestación avanzada
    """
    try:
        data = request.get_json()
        
        if not data or 'task_description' not in data:
            return jsonify({
                'error': 'task_description es requerido'
            }), 400
        
        task_description = data['task_description']
        user_id = data.get('user_id', 'default_user')
        session_id = data.get('session_id', str(uuid.uuid4()))
        priority = data.get('priority', 1)
        constraints = data.get('constraints', {})
        preferences = data.get('preferences', {})
        
        # Crear contexto de orquestación
        context = OrchestrationContext(
            task_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            task_description=task_description,
            priority=priority,
            constraints=constraints,
            preferences=preferences,
            metadata=data.get('metadata', {})
        )
        
        # Ejecutar orquestación
        result = await task_orchestrator.orchestrate_task(context)
        
        # Preparar respuesta
        response = {
            'task_id': result.task_id,
            'success': result.success,
            'total_execution_time': result.total_execution_time,
            'steps_completed': result.steps_completed,
            'steps_failed': result.steps_failed,
            'adaptations_made': result.adaptations_made,
            'resource_usage': result.resource_usage,
            'metadata': result.metadata
        }
        
        if result.error_message:
            response['error'] = result.error_message
        
        if result.execution_plan:
            response['execution_plan'] = {
                'id': result.execution_plan.id,
                'title': result.execution_plan.title,
                'strategy': result.execution_plan.strategy.value,
                'total_steps': len(result.execution_plan.steps),
                'estimated_duration': result.execution_plan.total_estimated_duration,
                'complexity_score': result.execution_plan.complexity_score,
                'success_probability': result.execution_plan.success_probability
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error en orquestación: {str(e)}")
        return jsonify({
            'error': f'Error en orquestación: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/status/<task_id>', methods=['GET'])
async def get_orchestration_status(task_id):
    """
    Obtiene el estado de una orquestación
    """
    try:
        status = task_orchestrator.get_orchestration_status(task_id)
        
        if status:
            return jsonify(status)
        else:
            return jsonify({
                'error': 'Orquestación no encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo estado: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/metrics', methods=['GET'])
async def get_orchestration_metrics():
    """
    Obtiene métricas de orquestación
    """
    try:
        metrics = task_orchestrator.get_orchestration_metrics()
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo métricas: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/active', methods=['GET'])
async def get_active_orchestrations():
    """
    Obtiene todas las orquestaciones activas
    """
    try:
        active_orchestrations = task_orchestrator.get_active_orchestrations()
        return jsonify(active_orchestrations)
        
    except Exception as e:
        logger.error(f"Error obteniendo orquestaciones activas: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo orquestaciones activas: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/cancel/<task_id>', methods=['POST'])
async def cancel_orchestration(task_id):
    """
    Cancela una orquestación activa
    """
    try:
        cancelled = await task_orchestrator.cancel_orchestration(task_id)
        
        if cancelled:
            return jsonify({
                'success': True,
                'message': f'Orquestación {task_id} cancelada exitosamente'
            })
        else:
            return jsonify({
                'error': 'Orquestación no encontrada o ya finalizada'
            }), 404
            
    except Exception as e:
        logger.error(f"Error cancelando orquestación: {str(e)}")
        return jsonify({
            'error': f'Error cancelando orquestación: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/recommendations', methods=['GET'])
async def get_orchestration_recommendations():
    """
    Obtiene recomendaciones de optimización
    """
    try:
        recommendations = task_orchestrator.get_recommendations()
        return jsonify(recommendations)
        
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo recomendaciones: {str(e)}'
        }), 500

@agent_bp.route('/chat', methods=['POST'])
async def chat():
    """
    Endpoint principal para chat con integración de TaskOrchestrator
    Mantiene compatibilidad con el frontend existente
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})
        search_mode = data.get('search_mode', None)
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Obtener task_id del contexto
        task_id = context.get('task_id', str(uuid.uuid4()))
        user_id = context.get('user_id', 'default_user')
        session_id = context.get('session_id', str(uuid.uuid4()))
        
        # Detectar modo de búsqueda desde el mensaje
        original_message = message
        if message.startswith('[WebSearch]'):
            search_mode = 'websearch'
            message = message.replace('[WebSearch]', '').strip()
        elif message.startswith('[DeepResearch]'):
            search_mode = 'deepsearch'
            message = message.replace('[DeepResearch]', '').strip()
        
        # 🧠 INTEGRACIÓN AUTOMÁTICA DE MEMORIA - Recuperar contexto relevante
        relevant_context = ""
        try:
            # Inicializar memoria si no está inicializada
            if not memory_manager.is_initialized:
                await memory_manager.initialize()
            
            # Buscar contexto relevante de conversaciones anteriores
            context_results = await memory_manager.retrieve_relevant_context(
                query=message,
                context_type="all",
                max_results=5
            )
            
            if context_results and context_results != "No se encontró contexto relevante previo":
                relevant_context = f"\n\n[CONTEXTO PREVIO RELEVANTE]:\n{context_results}\n[FIN CONTEXTO]"
                logger.info(f"🧠 Contexto relevante encontrado para mejorar respuesta: {len(str(context_results))} caracteres")
            else:
                logger.info(f"🧠 No se encontró contexto relevante previo para la consulta")
        except Exception as e:
            logger.warning(f"Error recuperando contexto: {e}")

        # 🚀 NUEVO: Usar Enhanced Agent si está disponible
        if not search_mode:
            try:
                # Obtener servicios del contexto de aplicación
                from flask import current_app
                
                # Verificar si enhanced components están disponibles
                enhanced_agent = getattr(current_app, 'enhanced_agent', None)
                enhanced_memory = getattr(current_app, 'enhanced_memory', None)
                enhanced_task_manager = getattr(current_app, 'enhanced_task_manager', None)
                
                # Usar enhanced agent si está disponible
                if enhanced_agent and enhanced_memory and enhanced_task_manager:
                    logger.info(f"🧠 Usando Enhanced Agent para procesamiento avanzado")
                    
                    # Agregar contexto relevante al mensaje
                    enhanced_message = message + relevant_context
                    
                    # Usar enhanced agent para procesamiento cognitivo
                    enhanced_response = enhanced_agent.process_user_message_enhanced(
                        enhanced_message, context
                    )
                    
                    # 🧠 ALMACENAR EN MEMORIA EPISÓDICA
                    try:
                        from src.memory.episodic_memory_store import Episode
                        
                        # Asegurar que la memoria está inicializada
                        if not memory_manager.is_initialized:
                            await memory_manager.initialize()
                        
                        episode = Episode(
                            id=str(uuid.uuid4()),
                            title=f"Conversación con usuario",
                            description=f"Usuario: {message}\nAgente: {enhanced_response}",
                            context={
                                'user_message': message,
                                'agent_response': enhanced_response,
                                'session_id': session_id,
                                'task_id': task_id,
                                'enhanced_processing': True,
                                **context
                            },
                            actions=[{
                                'type': 'user_message',
                                'content': message,
                                'timestamp': datetime.now().isoformat()
                            }],
                            outcomes=[{
                                'type': 'agent_response',
                                'content': enhanced_response,
                                'timestamp': datetime.now().isoformat()
                            }],
                            timestamp=datetime.now(),
                            success=True,
                            importance=3,
                            tags=['chat', 'conversation', 'enhanced']
                        )
                        await memory_manager.episodic_memory.store_episode(episode)
                        logger.info(f"🧠 Episodio almacenado en memoria para aprendizaje futuro")
                    except Exception as e:
                        logger.warning(f"Error almacenando episodio: {e}")
                    
                    # Obtener estado cognitivo
                    cognitive_status = enhanced_agent.get_enhanced_status()
                    
                    return jsonify({
                        'response': enhanced_response,
                        'enhanced_processing': True,
                        'cognitive_mode': cognitive_status.get('cognitive_capabilities', {}).get('current_mode', 'adaptive'),
                        'task_id': task_id,
                        'execution_status': 'enhanced_completed',
                        'timestamp': datetime.now().isoformat(),
                        'model': 'enhanced-mitosis-agent',
                        'memory_used': bool(relevant_context)
                    })
                else:
                    # Si enhanced components no están disponibles, usar TaskOrchestrator
                    logger.info(f"⚠️ Enhanced components no disponibles, usando TaskOrchestrator")
                    
                # Crear contexto de orquestación (fallback)
                orchestration_context = OrchestrationContext(
                    task_id=task_id,
                    user_id=user_id,
                    session_id=session_id,
                    task_description=message,
                    priority=1,
                    constraints=context.get('constraints', {}),
                    preferences=context.get('preferences', {}),
                    metadata={
                        'original_message': original_message,
                        'frontend_context': context,
                        'execution_type': 'orchestrated'
                    }
                )
                
                # Configurar callbacks para WebSocket si está disponible
                try:
                    from src.websocket.websocket_manager import get_websocket_manager
                    websocket_manager = get_websocket_manager()
                    
                    # Crear callbacks para notificaciones en tiempo real
                    async def on_progress(step_id, result, execution_state):
                        websocket_manager.send_orchestration_progress(
                            task_id=task_id,
                            step_id=step_id,
                            progress=execution_state.get('progress', 0),
                            current_step=execution_state.get('current_step', 'Processing...'),
                            total_steps=execution_state.get('total_steps', 1)
                        )
                    
                    async def on_complete(result):
                        websocket_manager.send_task_completed(
                            task_id=task_id,
                            success_rate=result.success_rate if hasattr(result, 'success_rate') else 1.0,
                            total_execution_time=result.get('execution_time', 0),
                            summary=result
                        )
                    
                    async def on_error(error_data):
                        websocket_manager.send_task_failed(
                            task_id=task_id,
                            error=str(error_data.get('error', 'Unknown error')),
                            context={'execution_type': 'orchestrated'}
                        )
                    
                    # Configurar callbacks del orquestador
                    task_orchestrator.add_callback('on_progress', on_progress)
                    task_orchestrator.add_callback('on_complete', on_complete)
                    task_orchestrator.add_callback('on_error', on_error)
                    
                except ImportError:
                    logger.warning("WebSocket manager not available, continuing without real-time updates")
                
                # SOLUCIÓN: Obtener servicios ANTES del thread de background
                # Obtener servicios del contexto de aplicación
                from flask import current_app
                ollama_service = current_app.ollama_service
                tool_manager = current_app.tool_manager
                database_service = current_app.database_service
                
                # Ejecutar orquestación de manera síncrona con herramientas reales
                try:
                    # 🔍 SISTEMA DE CLASIFICACIÓN INTELIGENTE
                    def classify_message_mode(message: str) -> str:
                        """
                        Clasificar el mensaje entre 'discussion' y 'agent' según los criterios especificados
                        
                        Modo Discussion (por defecto):
                        - Conversaciones casuales: Saludos, preguntas sobre mí, charlas generales
                        - Tareas simples directas: traducciones, resúmenes cortos, conocimiento general
                        - Preguntas de búsqueda única: "¿Quién ganó el último mundial?"
                        
                        Modo Agent:
                        - Complejidad explícita: "investiga", "analiza", "crea", "planifica", "compara en una tabla"
                        - Múltiples pasos implícitos: tareas que requieren varias acciones coordinadas
                        - Herramientas avanzadas: código, APIs, archivos
                        - Ejecución programada: tareas en el tiempo
                        """
                        message_lower = message.lower().strip()
                        
                        # 1. MODO DISCUSIÓN - Conversaciones casuales
                        casual_patterns = [
                            # Saludos básicos
                            'hola', 'hi', 'hello', 'buenas', 'buenos días', 'buenas tardes', 'buenas noches',
                            'hey', 'qué tal', 'how are you', 'cómo estás', 'cómo va', 'how is it going',
                            
                            # Cortesías
                            'gracias', 'thanks', 'thank you', 'de nada', 'por favor', 'please',
                            'disculpa', 'perdón', 'sorry', 'excuse me',
                            
                            # Preguntas sobre el asistente
                            'quién eres', 'who are you', 'tu nombre', 'your name', 'cómo te llamas',
                            'qué puedes hacer', 'what can you do', 'cuáles son tus funciones',
                            
                            # Despedidas
                            'adiós', 'bye', 'goodbye', 'hasta luego', 'see you later', 'nos vemos',
                            
                            # Expresiones casuales
                            'está bien', 'ok', 'okay', 'entiendo', 'perfecto', 'genial'
                        ]
                        
                        # Si es claramente casual, usar modo discusión
                        if any(pattern in message_lower for pattern in casual_patterns):
                            return 'discussion'
                        
                        # 2. MODO DISCUSIÓN - Tareas simples directas
                        simple_task_patterns = [
                            # Traducciones
                            'traduce', 'translate', 'en inglés', 'en español', 'en francés',
                            'how do you say', 'cómo se dice', 'what does', 'qué significa',
                            
                            # Resúmenes simples
                            'resume', 'summarize', 'resumen de', 'summary of',
                            
                            # Definiciones y explicaciones directas
                            'define', 'explica', 'explain', 'qué es', 'what is', 'cuál es la diferencia',
                            'diferencia entre', 'difference between'
                        ]
                        
                        # Si es tarea simple Y no tiene indicadores complejos, usar modo discusión
                        if any(pattern in message_lower for pattern in simple_task_patterns):
                            # Verificar que no tenga indicadores complejos
                            complex_indicators = ['investiga', 'analiza', 'compara en una tabla', 'crea un informe']
                            if not any(indicator in message_lower for indicator in complex_indicators):
                                return 'discussion'
                        
                        # 3. MODO AGENTE - Tareas de listado y consulta de sistema
                        system_task_patterns = [
                            # Listado de archivos y directorios
                            'lista', 'listar', 'mostrar', 'show', 'ver', 'view',
                            'archivos', 'files', 'directorio', 'directories', 'folders', 'carpetas',
                            
                            # Comandos específicos
                            'ls', 'dir', 'cd', 'pwd', 'find', 'locate', 'which', 'where',
                            
                            # Consultas de sistema
                            'ejecuta', 'execute', 'run', 'comando', 'command',
                            'procesos', 'processes', 'servicios', 'services', 'estado', 'status'
                        ]
                        
                        # Si es tarea de sistema, usar modo agente
                        if any(pattern in message_lower for pattern in system_task_patterns):
                            return 'agent'
                        
                        # 4. MODO DISCUSIÓN - Preguntas de búsqueda única
                        single_search_patterns = [
                            # Preguntas directas que requieren una sola búsqueda
                            'quién ganó', 'who won', 'cuál es el', 'what is the', 'cuándo fue', 'when was',
                            'dónde está', 'where is', 'cuánto cuesta', 'how much', 'precio de', 'price of',
                            'último', 'latest', 'más reciente', 'most recent', 'actual', 'current'
                        ]
                        
                        # Si es pregunta directa simple, usar modo discusión
                        if any(pattern in message_lower for pattern in single_search_patterns) and len(message.split()) < 15:
                            return 'discussion'
                        
                        # 5. MODO AGENTE - Complejidad explícita
                        explicit_complexity_patterns = [
                            # Análisis y planificación
                            'investiga', 'investigate', 'analiza', 'analyze', 'planifica', 'plan',
                            'crea', 'create', 'desarrolla', 'develop', 'diseña', 'design',
                            'compara en una tabla', 'compare in a table', 'haz una comparación',
                            'elabora', 'elaborate', 'construye', 'build', 'implementa', 'implement',
                            
                            # Informes y documentos
                            'informe', 'report', 'reporte', 'documento', 'document',
                            'presentación', 'presentation', 'estudio', 'study', 'investigación',
                            
                            # Operaciones complejas
                            'busca y filtra', 'find and filter', 'evalúa y compara', 'evaluate and compare',
                            'procesa y analiza', 'process and analyze'
                        ]
                        
                        if any(pattern in message_lower for pattern in explicit_complexity_patterns):
                            return 'agent'
                        
                        # 6. MODO AGENTE - Múltiples pasos implícitos
                        multi_step_indicators = [
                            # Palabras que indican múltiples acciones
                            'luego', 'then', 'después', 'after', 'y luego', 'and then',
                            'primero', 'first', 'segundo', 'second', 'finalmente', 'finally',
                            'paso a paso', 'step by step', 'etapa por etapa',
                            
                            # Conectores complejos
                            'y también', 'and also', 'además', 'furthermore', 'por otro lado',
                            'mientras tanto', 'meanwhile', 'simultáneamente', 'simultaneously'
                        ]
                        
                        if any(pattern in message_lower for pattern in multi_step_indicators):
                            return 'agent'
                        
                        # 7. MODO AGENTE - Herramientas avanzadas
                        advanced_tools_patterns = [
                            # Programación y código
                            'código', 'code', 'script', 'programa', 'program', 'función', 'function',
                            'ejecuta', 'execute', 'run', 'comando', 'command', 'terminal',
                            
                            # Archivos y sistema
                            'archivo', 'file', 'directorio', 'directory', 'carpeta', 'folder',
                            'descarga', 'download', 'sube', 'upload', 'instala', 'install',
                            
                            # APIs y servicios
                            'api', 'servicio', 'service', 'integración', 'integration',
                            'conecta', 'connect', 'sincroniza', 'synchronize'
                        ]
                        
                        if any(pattern in message_lower for pattern in advanced_tools_patterns):
                            return 'agent'
                        
                        # 8. MODO AGENTE - Ejecución programada
                        scheduled_patterns = [
                            # Tiempo futuro
                            'mañana', 'tomorrow', 'la próxima semana', 'next week',
                            'todos los días', 'every day', 'cada hora', 'every hour',
                            'programa', 'schedule', 'automatiza', 'automate',
                            'recordatorio', 'reminder', 'notificación', 'notification'
                        ]
                        
                        if any(pattern in message_lower for pattern in scheduled_patterns):
                            return 'agent'
                        
                        # 9. ANÁLISIS ADICIONAL - Longitud y complejidad
                        word_count = len(message.split())
                        sentence_count = len([s for s in message.split('.') if s.strip()])
                        
                        # Si es muy largo o tiene múltiples oraciones, probablemente es complejo
                        if word_count > 20 or sentence_count > 2:
                            return 'agent'
                        
                        # Por defecto, usar modo discusión
                        return 'discussion'
                    
                    # Clasificar el mensaje para determinar el modo
                    message_mode = classify_message_mode(message)
                    logger.info(f"🔍 Modo clasificado para '{message}': {message_mode}")
                    
                    if message_mode == 'discussion':
                        # 💬 MODO DISCUSIÓN - Usar respuesta casual
                        logger.info(f"💬 Modo discusión activado - generando respuesta casual")
                        
                        # Generar respuesta casual usando Ollama con contexto de memoria
                        enhanced_message = message
                        if relevant_context:
                            enhanced_message = f"""
Contexto previo relevante:
{relevant_context}

Pregunta actual del usuario: {message}

Responde considerando el contexto previo para dar una respuesta más personalizada y coherente.
"""
                        
                        response_data = ollama_service.generate_casual_response(enhanced_message, {
                            'task_id': task_id,
                            'previous_messages': relevant_context.get('previous_messages', []) if relevant_context else [],
                            'memory_context': relevant_context if relevant_context else None
                        })
                        
                        if response_data.get('error'):
                            raise Exception(response_data['error'])
                        
                        agent_response = response_data.get('response', 'No se pudo generar respuesta')
                        logger.info(f"✅ Respuesta casual generada: '{agent_response[:100]}...'")
                        
                        # 🧠 ALMACENAR EN MEMORIA EPISÓDICA - MODO DISCUSIÓN
                        try:
                            from src.memory.episodic_memory_store import Episode
                            
                            # Asegurar que la memoria está inicializada
                            if not memory_manager.is_initialized:
                                await memory_manager.initialize()
                            
                            episode = Episode(
                                id=str(uuid.uuid4()),
                                title=f"Conversación casual - {message[:50]}...",
                                description=f"Usuario: {message}\nAgente: {agent_response}",
                                context={
                                    'user_message': message,
                                    'agent_response': agent_response,
                                    'session_id': session_id,
                                    'task_id': task_id,
                                    'mode': 'discussion',
                                    'memory_context_used': bool(relevant_context),
                                    'frontend_context': context
                                },
                                actions=[{
                                    'type': 'user_message',
                                    'content': message,
                                    'timestamp': datetime.now().isoformat()
                                }],
                                outcomes=[{
                                    'type': 'agent_response',
                                    'content': agent_response,
                                    'timestamp': datetime.now().isoformat()
                                }],
                                timestamp=datetime.now(),
                                success=True,
                                importance=2,  # Menor importancia para conversaciones casuales
                                tags=['chat', 'conversation', 'discussion', 'casual']
                            )
                            await memory_manager.episodic_memory.store_episode(episode)
                            logger.info(f"🧠 Episodio casual almacenado en memoria")
                        except Exception as e:
                            logger.warning(f"Error almacenando episodio casual: {e}")
                        
                        return jsonify({
                            'response': agent_response,
                            'task_id': task_id,
                            'model': response_data.get('model', 'unknown'),
                            'timestamp': datetime.now().isoformat(),
                            'memory_used': bool(relevant_context),
                            'conversation_mode': True,
                            'mode': 'discussion'
                        })
                    
                    else:  # message_mode == 'agent'
                        # 🤖 MODO AGENTE - Ejecutar herramientas y generar planes
                        start_time = time.time()  # Registrar tiempo de inicio para auto-reflexión
                        logger.info(f"🤖 Modo agente activado - ejecutando herramientas")
                        
                        # Crear un sistema de ejecución de herramientas inteligente
                        def execute_agent_task():
                            """Ejecutar tarea en modo agente con herramientas automáticamente y fallback inteligente"""
                            tools_to_use = []
                            
                            # Detectar herramientas necesarias basado en el mensaje
                            if any(keyword in message.lower() for keyword in ['comando', 'ejecuta', 'shell', 'ls', 'cd', 'mkdir', 'rm', 'cat', 'grep', 'find', 'chmod', 'chown', 'ps', 'kill', 'pwd']):
                                tools_to_use.append('shell')
                            
                            if any(keyword in message.lower() for keyword in ['archivo', 'file', 'directorio', 'folder', 'lista', 'listar', 'mostrar', 'crear', 'eliminar', 'leer', 'escribir', 'copiar', 'mover']):
                                tools_to_use.append('file_manager')
                            
                            if any(keyword in message.lower() for keyword in ['buscar', 'busca', 'search', 'información', 'noticias', 'web', 'internet', 'google', 'investiga', 'investigar', 'informe', 'report', 'reporte', 'sobre', 'acerca de', 'about', 'mejores prácticas', 'best practices']):
                                tools_to_use.append('web_search')
                            
                            # Si no detecta herramientas específicas, usar por defecto según el contexto
                            if not tools_to_use:
                                if any(keyword in message.lower() for keyword in ['analiza', 'analizar', 'procesa', 'procesar', 'verifica', 'verificar', 'genera', 'generar', 'crea', 'crear', 'haz', 'hacer', 'informe', 'report']):
                                    tools_to_use = ['web_search']
                                else:
                                    tools_to_use = ['shell']
                            
                            # Ejecutar herramientas detectadas
                            results = []
                            for tool_name in tools_to_use:
                                try:
                                    if tool_name == 'shell':
                                        if 'ls' in message.lower():
                                            params = {'command': 'ls -la /app'}
                                        elif 'pwd' in message.lower():
                                            params = {'command': 'pwd'}
                                        elif 'ps' in message.lower():
                                            params = {'command': 'ps aux'}
                                        else:
                                            params = {'command': 'ls -la'}
                                    elif tool_name == 'file_manager':
                                        params = {'action': 'list', 'path': '/app'}
                                    elif tool_name == 'web_search':
                                        params = {'query': message}
                                    else:
                                        params = {'input': message}
                                    
                                    result = tool_manager.execute_tool(tool_name, params, task_id=task_id)
                                    results.append({
                                        'tool': tool_name,
                                        'result': result,
                                        'success': not result.get('error')
                                    })
                                    
                                except Exception as e:
                                    results.append({
                                        'tool': tool_name,
                                        'result': {'error': str(e)},
                                        'success': False
                                    })
                            
                            # 🔄 FALLBACK: Si web_search falla, usar LLM con conocimiento interno
                            if tools_to_use == ['web_search'] and results and not results[0]['success']:
                                try:
                                    logger.info(f"🔄 Web search falló, usando LLM con conocimiento interno como fallback")
                                    
                                    # Generar respuesta usando conocimiento interno del LLM
                                    fallback_prompt = f"""
                                    No puedo acceder a internet en este momento, pero puedo ayudarte basándome en mi conocimiento interno.
                                    
                                    Pregunta: {message}
                                    
                                    Proporciona una respuesta útil y completa basada en tu conocimiento interno sobre este tema.
                                    Si es sobre mejores prácticas, tendencias actuales, o conceptos técnicos, puedes dar información valiosa.
                                    
                                    Estructura tu respuesta de manera clara y útil, mencionando que la información se basa en tu conocimiento interno.
                                    """
                                    
                                    fallback_response = ollama_service.generate_response(fallback_prompt)
                                    
                                    if fallback_response and not fallback_response.get('error'):
                                        # Reemplazar el resultado fallido con el fallback
                                        results[0] = {
                                            'tool': 'llm_fallback',
                                            'result': {
                                                'response': fallback_response.get('response', ''),
                                                'fallback_mode': True,
                                                'original_tool': 'web_search',
                                                'success': True
                                            },
                                            'success': True
                                        }
                                        logger.info(f"✅ Fallback LLM exitoso para tarea de búsqueda")
                                    
                                except Exception as e:
                                    logger.error(f"Error en fallback LLM: {str(e)}")
                            
                            return results
                        
                        # Ejecutar tareas en modo agente
                        tool_results = execute_agent_task()
                        
                        # 🧠 PROCESAR RESULTADOS CON LLM PARA GENERAR RESPUESTA ÚTIL
                        def process_tool_results_with_llm(tool_results, original_message):
                            """Procesa los resultados de las herramientas con el LLM para generar una respuesta coherente"""
                            try:
                                # Construir contexto con los resultados
                                context_parts = [f"TAREA SOLICITADA: {original_message}\n"]
                                
                                if tool_results:
                                    context_parts.append("RESULTADOS DE HERRAMIENTAS EJECUTADAS:")
                                    for i, result in enumerate(tool_results, 1):
                                        tool_name = result['tool']
                                        success = result['success']
                                        tool_result = result['result']
                                        
                                        if success:
                                            if tool_name == 'shell':
                                                if 'stdout' in tool_result:
                                                    context_parts.append(f"{i}. Comando shell ejecutado exitosamente:")
                                                    context_parts.append(f"   Salida: {tool_result['stdout']}")
                                                elif 'output' in tool_result:
                                                    context_parts.append(f"{i}. Comando shell ejecutado exitosamente:")
                                                    context_parts.append(f"   Salida: {tool_result['output']}")
                                            elif tool_name == 'web_search':
                                                if 'results' in tool_result:
                                                    context_parts.append(f"{i}. Búsqueda web ejecutada exitosamente:")
                                                    for search_result in tool_result['results'][:3]:
                                                        context_parts.append(f"   - {search_result.get('title', 'Sin título')}")
                                                        context_parts.append(f"     URL: {search_result.get('url', 'Sin URL')}")
                                                        context_parts.append(f"     Descripción: {search_result.get('snippet', 'Sin descripción')}")
                                            elif tool_name == 'llm_fallback':
                                                if 'response' in tool_result:
                                                    context_parts.append(f"{i}. Respuesta usando conocimiento interno (web no disponible):")
                                                    context_parts.append(f"   {tool_result['response']}")
                                            elif tool_name == 'file_manager':
                                                if 'files' in tool_result:
                                                    context_parts.append(f"{i}. Gestión de archivos ejecutada exitosamente:")
                                                    context_parts.append(f"   Archivos encontrados: {tool_result['files'][:10]}")
                                            else:
                                                context_parts.append(f"{i}. Herramienta {tool_name} ejecutada exitosamente:")
                                                context_parts.append(f"   Resultado: {str(tool_result)[:500]}...")
                                        else:
                                            context_parts.append(f"{i}. Error en herramienta {tool_name}: {tool_result.get('error', 'Error desconocido')}")
                                
                                # Agregar contexto de memoria si está disponible
                                if relevant_context:
                                    context_parts.insert(1, f"CONTEXTO DE MEMORIA RELEVANTE:\n{relevant_context}")
                                
                                # Crear prompt para el LLM
                                llm_prompt = f"""
                                Eres un asistente inteligente que ayuda a interpretar y presentar resultados de herramientas ejecutadas.
                                
                                {chr(10).join(context_parts)}
                                
                                INSTRUCCIONES:
                                1. Analiza los resultados de las herramientas ejecutadas
                                2. Considera el contexto de memoria relevante si está disponible
                                3. Proporciona una respuesta clara y útil que responda directamente a la tarea solicitada
                                4. Si hubo errores, explica qué salió mal y sugiere alternativas
                                5. Si hubo resultados exitosos, interpreta y presenta la información de manera útil
                                6. Mantén un tono profesional pero amigable
                                7. Estructura la respuesta de manera clara y organizada
                                
                                Responde directamente a la tarea solicitada basándote en los resultados obtenidos:
                                """
                                
                                # Generar respuesta usando Ollama
                                llm_response = ollama_service.generate_response(llm_prompt)
                                
                                if llm_response.get('error'):
                                    logger.warning(f"Error generando respuesta con LLM: {llm_response['error']}")
                                    return None
                                
                                return llm_response.get('response', '')
                                
                            except Exception as e:
                                logger.error(f"Error procesando resultados con LLM: {str(e)}")
                                return None
                        
                        # Generar respuesta usando el LLM
                        llm_response = process_tool_results_with_llm(tool_results, message)
                        
                        if llm_response:
                            # Usar respuesta del LLM como respuesta principal
                            final_response = llm_response
                        else:
                            # Fallback: usar respuesta estructurada simple
                            response_parts = [f"🤖 **Ejecución en Modo Agente**\n\n**Tarea:** {message}\n"]
                            
                            if tool_results:
                                response_parts.append("🛠️ **Herramientas Ejecutadas:**\n")
                                for i, result in enumerate(tool_results, 1):
                                    status = "✅ EXITOSO" if result['success'] else "❌ ERROR"
                                    response_parts.append(f"{i}. **{result['tool']}**: {status}")
                                    
                                    if result['success'] and result['result']:
                                        if result['tool'] == 'shell':
                                            if 'stdout' in result['result']:
                                                response_parts.append(f"```\n{result['result']['stdout']}\n```")
                                            elif 'output' in result['result']:
                                                response_parts.append(f"```\n{result['result']['output']}\n```")
                                        elif result['tool'] == 'file_manager':
                                            if 'files' in result['result']:
                                                response_parts.append("📁 **Archivos encontrados:**")
                                                for file_info in result['result']['files'][:5]:
                                                    response_parts.append(f"• {file_info}")
                                        elif result['tool'] == 'web_search':
                                            if 'results' in result['result']:
                                                response_parts.append("🔍 **Resultados de búsqueda:**")
                                                for search_result in result['result']['results'][:3]:
                                                    response_parts.append(f"• {search_result.get('title', 'Sin título')}")
                                        else:
                                            response_parts.append(f"📊 **Resultado:** {str(result['result'])[:200]}...")
                                    elif not result['success']:
                                        response_parts.append(f"⚠️ **Error:** {result['result'].get('error', 'Error desconocido')}")
                                    
                                    response_parts.append("")
                            
                            final_response = "\n".join(response_parts)
                        
                        # 🧠 ALMACENAR EN MEMORIA EPISÓDICA - MODO AGENTE
                        try:
                            from src.memory.episodic_memory_store import Episode
                            
                            # Asegurar que la memoria está inicializada
                            if not memory_manager.is_initialized:
                                await memory_manager.initialize()
                            
                            episode = Episode(
                                id=str(uuid.uuid4()),
                                title=f"Ejecución de agente - {message[:50]}...",
                                description=f"Usuario: {message}\nAgente: {final_response[:500]}...",
                                context={
                                    'user_message': message,
                                    'agent_response': final_response,
                                    'session_id': session_id,
                                    'task_id': task_id,
                                    'mode': 'agent',
                                    'memory_context_used': bool(relevant_context),
                                    'tools_executed': [r['tool'] for r in tool_results],
                                    'tools_success': [r['success'] for r in tool_results],
                                    'frontend_context': context
                                },
                                actions=[{
                                    'type': 'user_message',
                                    'content': message,
                                    'timestamp': datetime.now().isoformat()
                                }] + [{
                                    'type': 'tool_execution',
                                    'tool': result['tool'],
                                    'success': result['success'],
                                    'timestamp': datetime.now().isoformat()
                                } for result in tool_results],
                                outcomes=[{
                                    'type': 'agent_response',
                                    'content': final_response,
                                    'timestamp': datetime.now().isoformat()
                                }],
                                timestamp=datetime.now(),
                                success=any(r['success'] for r in tool_results) if tool_results else True,
                                importance=4,  # Mayor importancia para ejecuciones de agente
                                tags=['chat', 'conversation', 'agent', 'tools']
                            )
                            await memory_manager.episodic_memory.store_episode(episode)
                            logger.info(f"🧠 Episodio de agente almacenado en memoria")
                        except Exception as e:
                            logger.warning(f"Error almacenando episodio de agente: {e}")
                        
                        return jsonify({
                            'response': final_response,
                            'tool_results': tool_results,
                            'tools_executed': len(tool_results),
                            'task_id': task_id,
                            'execution_status': 'completed',
                            'timestamp': datetime.now().isoformat(),
                            'model': 'agent-mode',
                            'memory_used': bool(relevant_context),
                            'mode': 'agent'
                        })
                    
                except Exception as e:
                    logger.error(f"❌ Error executing tools: {str(e)}")
                    # Fallback a respuesta regular
                
            except Exception as e:
                logger.error(f"❌ Error in orchestration: {str(e)}")
                # Fallback a ejecución regular
                
        # 🔄 FALLBACK: Usar sistema anterior para WebSearch/DeepSearch o si falla orquestación
        
        # Obtener servicios del contexto de aplicación (necesario para todas las opciones)
        from flask import current_app
        ollama_service = current_app.ollama_service
        tool_manager = current_app.tool_manager
        database_service = current_app.database_service
        
        # Manejo de WebSearch
        if search_mode == 'websearch':
            try:
                # Ejecutar búsqueda web
                search_result = tool_manager.execute_tool(
                    'web_search',
                    {'query': message},
                    task_id=task_id
                )
                
                # Procesar resultado
                if search_result.get('error'):
                    raise Exception(search_result['error'])
                
                # Formatear respuesta
                response = f"🔍 **Resultados de Búsqueda Web**\n\n"
                response += f"**Consulta:** {message}\n\n"
                
                if search_result.get('results'):
                    response += "📋 **Resultados encontrados:**\n\n"
                    for i, result in enumerate(search_result['results'][:5], 1):
                        response += f"**{i}. {result.get('title', 'Sin título')}**\n"
                        response += f"🔗 {result.get('url', 'Sin URL')}\n"
                        response += f"📝 {result.get('snippet', 'Sin descripción')}\n\n"
                
                return jsonify({
                    'response': response,
                    'search_results': search_result.get('results', []),
                    'task_id': task_id,
                    'search_mode': 'websearch',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in web search: {str(e)}")
                return jsonify({
                    'error': f'Error en búsqueda web: {str(e)}'
                }), 500
        
        # Manejo de DeepSearch
        elif search_mode == 'deepsearch':
            try:
                # Ejecutar investigación profunda
                research_result = tool_manager.execute_tool(
                    'deep_research',
                    {'query': message},
                    task_id=task_id
                )
                
                # Procesar resultado
                if research_result.get('error'):
                    raise Exception(research_result['error'])
                
                # Formatear respuesta
                response = f"🔬 **Investigación Profunda Completada**\n\n"
                response += f"**Tema:** {message}\n\n"
                response += research_result.get('summary', 'No hay resumen disponible')
                
                return jsonify({
                    'response': response,
                    'research_data': research_result,
                    'task_id': task_id,
                    'search_mode': 'deepsearch',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in deep research: {str(e)}")
                return jsonify({
                    'error': f'Error en investigación profunda: {str(e)}'
                }), 500
        
        # Manejo de chat regular (fallback)
        else:
            try:
                # Agregar contexto relevante al mensaje
                enhanced_message = message + relevant_context
                
                # Generar respuesta usando Ollama
                response_data = ollama_service.generate_response(enhanced_message)
                
                if response_data.get('error'):
                    raise Exception(response_data['error'])
                
                agent_response = response_data.get('response', 'No se pudo generar respuesta')
                
                # 🧠 ALMACENAR EN MEMORIA EPISÓDICA
                try:
                    from src.memory.episodic_memory_store import Episode
                    
                    episode = Episode(
                        id=str(uuid.uuid4()),
                        title=f"Conversación con usuario",
                        description=f"Usuario: {message}\nAgente: {agent_response}",
                        context={
                            'user_message': message,
                            'agent_response': agent_response,
                            'session_id': session_id,
                            'task_id': task_id,
                            'fallback_mode': True,
                            **context
                        },
                        actions=[{
                            'type': 'user_message',
                            'content': message,
                            'timestamp': datetime.now().isoformat()
                        }],
                        outcomes=[{
                            'type': 'agent_response',
                            'content': agent_response,
                            'timestamp': datetime.now().isoformat()
                        }],
                        timestamp=datetime.now(),
                        success=True,
                        importance=2,
                        tags=['chat', 'conversation', 'fallback']
                    )
                    await memory_manager.episodic_memory.store_episode(episode)
                    logger.info(f"🧠 Episodio almacenado en memoria (modo fallback)")
                except Exception as e:
                    logger.warning(f"Error almacenando episodio: {e}")
                
                return jsonify({
                    'response': agent_response,
                    'task_id': task_id,
                    'model': response_data.get('model', 'unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'memory_used': bool(relevant_context)
                })
                
            except Exception as e:
                logger.error(f"Error in regular chat: {str(e)}")
                return jsonify({
                    'error': f'Error generando respuesta: {str(e)}'
                }), 500
        
    except Exception as e:
        logger.error(f"Error general en chat: {str(e)}")
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@agent_bp.route('/update-task-progress', methods=['POST'])
def update_task_progress():
    """Actualiza el progreso de una tarea - permite al agente marcar pasos como completados"""
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id', '')
        step_id = data.get('step_id', '')
        completed = data.get('completed', False)
        
        if not task_id or not step_id:
            return jsonify({'error': 'task_id and step_id are required'}), 400
        
        # Almacenar progreso de la tarea (aquí podrías usar una base de datos)
        # Por simplicidad, lo almacenaremos en memoria
        if not hasattr(update_task_progress, 'task_progress'):
            update_task_progress.task_progress = {}
        
        if task_id not in update_task_progress.task_progress:
            update_task_progress.task_progress[task_id] = {}
        
        update_task_progress.task_progress[task_id][step_id] = {
            'completed': completed,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'step_id': step_id,
            'completed': completed,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error actualizando progreso: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/get-task-progress/<task_id>', methods=['GET'])
def get_task_progress(task_id):
    """Obtiene el progreso de una tarea específica"""
    try:
        if not hasattr(update_task_progress, 'task_progress'):
            return jsonify({'task_progress': {}})
        
        task_progress = update_task_progress.task_progress.get(task_id, {})
        
        return jsonify({
            'task_id': task_id,
            'task_progress': task_progress,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo progreso: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/task/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Obtiene el estado de una tarea específica
    Compatible con tanto orquestación como ejecución regular
    """
    try:
        # Verificar si es una orquestación activa
        orchestration_status = task_orchestrator.get_orchestration_status(task_id)
        
        if orchestration_status:
            return jsonify({
                'task_id': task_id,
                'type': 'orchestration',
                'status': orchestration_status.get('status', 'unknown'),
                'progress': orchestration_status.get('progress', 0),
                'start_time': orchestration_status.get('start_time', 0),
                'elapsed_time': orchestration_status.get('elapsed_time', 0),
                'context': orchestration_status.get('context', {})
            })
        
        # Si no hay orquestación, buscar en el sistema anterior
        # TODO: Integrar con el sistema de ejecución anterior si es necesario
        
        return jsonify({
            'task_id': task_id,
            'type': 'regular',
            'status': 'not_found',
            'message': 'Task not found in active orchestrations'
        }), 404
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de tarea: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo estado: {str(e)}'
        }), 500

@agent_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint con información de orquestación
    """
    try:
        # Obtener métricas de orquestación
        orchestration_metrics = task_orchestrator.get_orchestration_metrics()
        active_orchestrations = task_orchestrator.get_active_orchestrations()
        
        # Obtener información de herramientas
        tool_manager = current_app.tool_manager
        available_tools = tool_manager.get_available_tools()
        
        # Obtener estado de Ollama
        ollama_service = current_app.ollama_service
        ollama_status = ollama_service.check_connection()
        
        # Obtener estado de base de datos
        database_service = current_app.database_service
        db_status = database_service.check_connection()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'orchestration': {
                    'active_tasks': len(active_orchestrations),
                    'total_tasks': orchestration_metrics.get('total_tasks', 0),
                    'success_rate': orchestration_metrics.get('successful_tasks', 0) / max(orchestration_metrics.get('total_tasks', 1), 1),
                    'avg_execution_time': orchestration_metrics.get('avg_execution_time', 0)
                },
                'ollama': ollama_status,
                'database': db_status,
                'tools': {
                    'available': len(available_tools),
                    'list': [tool.get('name', 'unknown') for tool in available_tools]
                }
            },
            'version': '2.0.0-orchestrated'
        })
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/ollama/check', methods=['POST'])
def check_ollama_connection():
    """Verificar conexión con un endpoint de Ollama específico"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint')
        
        if not endpoint:
            return jsonify({'error': 'endpoint is required'}), 400
        
        # Crear servicio temporal para verificar conexión
        from src.services.ollama_service import OllamaService
        temp_service = OllamaService(base_url=endpoint)
        
        is_healthy = temp_service.is_healthy()
        
        return jsonify({
            'is_connected': is_healthy,
            'endpoint': endpoint,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error verificando conexión Ollama: {str(e)}")
        return jsonify({
            'error': str(e),
            'is_connected': False,
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/ollama/models', methods=['POST'])
def get_ollama_models():
    """Obtener modelos de un endpoint de Ollama específico"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint')
        
        if not endpoint:
            return jsonify({'error': 'endpoint is required'}), 400
        
        # Crear servicio temporal para obtener modelos
        from src.services.ollama_service import OllamaService
        temp_service = OllamaService(base_url=endpoint)
        
        if not temp_service.is_healthy():
            return jsonify({
                'error': 'Cannot connect to Ollama endpoint',
                'models': [],
                'timestamp': datetime.now().isoformat()
            }), 503
        
        models = temp_service.get_available_models()
        
        return jsonify({
            'models': models,
            'endpoint': endpoint,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo modelos Ollama: {str(e)}")
        return jsonify({
            'error': str(e),
            'models': [],
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/memory/stats', methods=['GET'])
def get_memory_stats():
    """Obtiene estadísticas del sistema de memoria autónoma"""
    try:
        async def get_stats():
            # Inicializar memoria si no está inicializada
            if not memory_manager.is_initialized:
                await memory_manager.initialize()
            
            # Obtener estadísticas completas
            stats = await memory_manager.get_memory_stats()
            
            # Agregar estadísticas adicionales
            stats['total_orchestrations'] = len(task_orchestrator.orchestration_history)
            stats['active_orchestrations'] = len(task_orchestrator.active_orchestrations)
            
            return stats
        
        # Ejecutar función asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stats = loop.run_until_complete(get_stats())
        loop.close()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de memoria: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/memory/learning-insights', methods=['GET'])
def get_learning_insights():
    """Obtiene insights de aprendizaje del agente"""
    try:
        async def get_insights():
            # Inicializar memoria si no está inicializada
            if not memory_manager.is_initialized:
                await memory_manager.initialize()
            
            # Obtener insights de aprendizaje
            insights = memory_manager.procedural_memory.get_learning_insights()
            
            # Agregar métricas de orquestación
            orchestration_metrics = task_orchestrator.get_orchestration_metrics()
            
            return {
                'learning_insights': insights,
                'orchestration_metrics': orchestration_metrics,
                'timestamp': datetime.now().isoformat()
            }
        
        # Ejecutar función asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        insights = loop.run_until_complete(get_insights())
        loop.close()
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Error obteniendo insights de aprendizaje: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/memory/search', methods=['POST'])
def search_memory():
    """Busca en la memoria autónoma del agente"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        context_type = data.get('context_type', 'all')
        max_results = data.get('max_results', 10)
        
        if not query:
            return jsonify({'error': 'query is required'}), 400
        
        async def search():
            # Inicializar memoria si no está inicializada
            if not memory_manager.is_initialized:
                await memory_manager.initialize()
            
            # Buscar en memoria
            results = await memory_manager.retrieve_relevant_context(
                query, 
                context_type, 
                max_results
            )
            
            return results
        
        # Ejecutar función asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(search())
        loop.close()
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error buscando en memoria: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/memory/compress', methods=['POST'])
def compress_memory():
    """Comprime memoria antigua para optimizar almacenamiento"""
    try:
        data = request.get_json() or {}
        compression_threshold_days = data.get('compression_threshold_days', 30)
        compression_ratio = data.get('compression_ratio', 0.5)
        
        async def compress():
            # Inicializar memoria si no está inicializada
            if not memory_manager.is_initialized:
                await memory_manager.initialize()
            
            # Comprimir memoria
            result = await memory_manager.compress_old_memory(
                compression_threshold_days=compression_threshold_days,
                compression_ratio=compression_ratio
            )
            
            return result
        
        # Ejecutar función asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(compress())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error comprimiendo memoria: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/memory/export', methods=['POST'])
def export_memory():
    """Exporta datos de memoria para respaldo o análisis"""
    try:
        data = request.get_json() or {}
        export_format = data.get('export_format', 'json')
        include_compressed = data.get('include_compressed', False)
        output_file = data.get('output_file', None)
        
        async def export():
            # Inicializar memoria si no está inicializada
            if not memory_manager.is_initialized:
                await memory_manager.initialize()
            
            # Exportar memoria
            result = await memory_manager.export_memory_data(
                export_format=export_format,
                include_compressed=include_compressed,
                output_file=output_file
            )
            
            return result
        
        # Ejecutar función asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(export())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error exportando memoria: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Enhanced Agent Endpoints
@agent_bp.route('/enhanced/status', methods=['GET'])
def get_enhanced_status():
    """Obtiene el estado avanzado del enhanced agent"""
    try:
        enhanced_agent = current_app.enhanced_agent
        if not enhanced_agent:
            return jsonify({'error': 'Enhanced agent not available'}), 503
        
        status = enhanced_agent.get_enhanced_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado enhanced: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/enhanced/cognitive-mode', methods=['GET'])
def get_cognitive_mode():
    """Obtiene el modo cognitivo actual del enhanced agent"""
    try:
        enhanced_agent = current_app.enhanced_agent
        if not enhanced_agent:
            return jsonify({'error': 'Enhanced agent not available'}), 503
        
        return jsonify({
            'cognitive_mode': enhanced_agent.cognitive_mode.value,
            'learning_enabled': enhanced_agent.learning_enabled,
            'reflection_threshold': enhanced_agent.reflection_threshold,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo modo cognitivo: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/enhanced/memory/semantic-search', methods=['POST'])
def enhanced_semantic_search():
    """Búsqueda semántica usando enhanced memory manager"""
    try:
        enhanced_memory = current_app.enhanced_memory
        if not enhanced_memory:
            return jsonify({'error': 'Enhanced memory not available'}), 503
        
        data = request.get_json()
        query = data.get('query', '')
        n_results = data.get('n_results', 10)
        category = data.get('category', None)
        min_confidence = data.get('min_confidence', 0.5)
        
        if not query:
            return jsonify({'error': 'query is required'}), 400
        
        # Realizar búsqueda semántica
        results = enhanced_memory.search_knowledge_semantic(
            query=query,
            n_results=n_results,
            category=category,
            min_confidence=min_confidence
        )
        
        # Convertir resultados a formato JSON serializable
        serialized_results = []
        for result in results:
            serialized_results.append({
                'id': result.id,
                'content': result.content,
                'category': result.category,
                'source': result.source,
                'confidence': result.confidence,
                'created_at': result.created_at,
                'accessed_count': result.accessed_count,
                'tags': result.tags
            })
        
        return jsonify({
            'results': serialized_results,
            'query': query,
            'total_results': len(serialized_results),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/enhanced/memory/stats', methods=['GET'])
def get_enhanced_memory_stats():
    """Obtiene estadísticas de la memoria mejorada"""
    try:
        enhanced_memory = current_app.enhanced_memory
        if not enhanced_memory:
            return jsonify({'error': 'Enhanced memory not available'}), 503
        
        stats = enhanced_memory.get_enhanced_memory_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de memoria mejorada: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/enhanced/learning/patterns', methods=['GET'])
def get_learned_patterns():
    """Obtiene los patrones aprendidos por el enhanced agent"""
    try:
        enhanced_agent = current_app.enhanced_agent
        if not enhanced_agent:
            return jsonify({'error': 'Enhanced agent not available'}), 503
        
        return jsonify({
            'learned_patterns': enhanced_agent.learned_patterns,
            'total_patterns': len(enhanced_agent.learned_patterns),
            'learning_metrics': enhanced_agent.learning_metrics.__dict__,
            'cognitive_stats': enhanced_agent.cognitive_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo patrones aprendidos: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/generate-suggestions', methods=['POST'])
def generate_suggestions():
    """Genera sugerencias dinámicas para el frontend"""
    try:
        data = request.get_json() or {}
        context = data.get('context', {})
        
        # Generar sugerencias dinámicas basadas en herramientas disponibles
        suggestions = [
            {
                'title': 'Analizar tendencias de IA en 2025',
                'icon': 'search',
                'category': 'research'
            },
            {
                'title': 'Crear un informe técnico',
                'icon': 'document',
                'category': 'creation'
            },
            {
                'title': 'Buscar mejores prácticas de desarrollo',
                'icon': 'code',
                'category': 'development'
            }
        ]
        
        return jsonify({
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generando sugerencias: {str(e)}")
        return jsonify({
            'error': str(e),
            'suggestions': [],
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/generate-plan', methods=['POST'])
def generate_plan():
    """Genera un plan de acción dinámico para mostrar al usuario (3-6 pasos)"""
    try:
        data = request.get_json() or {}
        task_title = data.get('task_title', '')
        context = data.get('context', {})
        
        if not task_title:
            return jsonify({'error': 'task_title is required'}), 400
        
        # Generar plan de acción específico para el usuario
        plan_steps = []
        
        # Detectar tipo de tarea y generar pasos apropiados
        task_lower = task_title.lower()
        
        # Planes específicos para WebSearch
        if '[websearch]' in task_lower:
            clean_task = task_title.replace('[WebSearch]', '').strip()
            plan_steps = [
                {'id': 'step-1', 'title': 'Procesar consulta de búsqueda', 'completed': False, 'active': True},
                {'id': 'step-2', 'title': 'Buscar información en internet', 'completed': False, 'active': False},
                {'id': 'step-3', 'title': 'Filtrar resultados relevantes', 'completed': False, 'active': False},
                {'id': 'step-4', 'title': 'Presentar resultados organizados', 'completed': False, 'active': False}
            ]
        # Planes específicos para DeepSearch
        elif '[deepresearch]' in task_lower:
            clean_task = task_title.replace('[DeepResearch]', '').strip()
            plan_steps = [
                {'id': 'step-1', 'title': 'Definir objetivos de investigación', 'completed': False, 'active': True},
                {'id': 'step-2', 'title': 'Recopilar información de múltiples fuentes', 'completed': False, 'active': False},
                {'id': 'step-3', 'title': 'Analizar y sintetizar datos', 'completed': False, 'active': False},
                {'id': 'step-4', 'title': 'Generar informe detallado', 'completed': False, 'active': False}
            ]
        # Planes para análisis y investigación
        elif any(keyword in task_lower for keyword in ['analizar', 'analiza', 'investigar', 'investigación', 'informe', 'reporte', 'estudio']):
            plan_steps = [
                {'id': 'step-1', 'title': 'Definir objetivos de investigación', 'completed': False, 'active': True},
                {'id': 'step-2', 'title': 'Recopilar información relevante', 'completed': False, 'active': False},
                {'id': 'step-3', 'title': 'Analizar y procesar datos', 'completed': False, 'active': False},
                {'id': 'step-4', 'title': 'Generar conclusiones', 'completed': False, 'active': False},
                {'id': 'step-5', 'title': 'Crear documento final', 'completed': False, 'active': False}
            ]
        # Planes para desarrollo y creación
        elif any(keyword in task_lower for keyword in ['crear', 'desarrollar', 'diseñar', 'construir', 'implementar', 'programar']):
            plan_steps = [
                {'id': 'step-1', 'title': 'Planificar estructura y requisitos', 'completed': False, 'active': True},
                {'id': 'step-2', 'title': 'Desarrollar componentes principales', 'completed': False, 'active': False},
                {'id': 'step-3', 'title': 'Integrar y probar funcionalidad', 'completed': False, 'active': False},
                {'id': 'step-4', 'title': 'Revisar y optimizar', 'completed': False, 'active': False},
                {'id': 'step-5', 'title': 'Finalizar y documentar', 'completed': False, 'active': False}
            ]
        # Planes para comparación y evaluación
        elif any(keyword in task_lower for keyword in ['comparar', 'evaluar', 'revisar', 'mejores prácticas', 'best practices']):
            plan_steps = [
                {'id': 'step-1', 'title': 'Identificar criterios de evaluación', 'completed': False, 'active': True},
                {'id': 'step-2', 'title': 'Recopilar datos comparativos', 'completed': False, 'active': False},
                {'id': 'step-3', 'title': 'Analizar diferencias y similitudes', 'completed': False, 'active': False},
                {'id': 'step-4', 'title': 'Generar recomendaciones', 'completed': False, 'active': False}
            ]
        # Planes para archivos adjuntos
        elif 'archivos adjuntos' in task_lower:
            plan_steps = [
                {'id': 'step-1', 'title': 'Procesar archivos recibidos', 'completed': False, 'active': True},
                {'id': 'step-2', 'title': 'Analizar contenido', 'completed': False, 'active': False},
                {'id': 'step-3', 'title': 'Preparar archivos para uso', 'completed': False, 'active': False}
            ]
        # Planes para búsqueda simple
        elif any(keyword in task_lower for keyword in ['buscar', 'busca', 'información sobre', 'qué es', 'quién es', 'cuál es']):
            plan_steps = [
                {'id': 'step-1', 'title': 'Procesar consulta', 'completed': False, 'active': True},
                {'id': 'step-2', 'title': 'Buscar información', 'completed': False, 'active': False},
                {'id': 'step-3', 'title': 'Presentar resultados', 'completed': False, 'active': False}
            ]
        else:
            # Plan genérico para cualquier tarea
            plan_steps = [
                {'id': 'step-1', 'title': 'Analizar requerimientos', 'completed': False, 'active': True},
                {'id': 'step-2', 'title': 'Ejecutar tarea principal', 'completed': False, 'active': False},
                {'id': 'step-3', 'title': 'Verificar resultados', 'completed': False, 'active': False},
                {'id': 'step-4', 'title': 'Entregar respuesta final', 'completed': False, 'active': False}
            ]
        
        return jsonify({
            'plan': plan_steps,
            'task_title': task_title,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generando plan: {str(e)}")
        return jsonify({
            'error': str(e),
            'plan': [],
            'timestamp': datetime.now().isoformat()
        }), 500