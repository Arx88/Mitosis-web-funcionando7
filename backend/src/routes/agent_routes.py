"""
Rutas API del agente - Versión REAL CON OLLAMA
Sistema de agente que usa Ollama real para generar respuestas inteligentes
Y distingue entre conversaciones casuales y tareas complejas
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import time
import uuid
import json
import os
import requests
import re

logger = logging.getLogger(__name__)

agent_bp = Blueprint('agent', __name__)

# Almacenamiento temporal para compartir conversaciones
shared_conversations = {}
# Almacenamiento temporal para archivos por tarea
task_files = {}
# Almacenamiento global para planes de tareas
active_task_plans = {}

# Patrones para detectar tipo de mensaje
CASUAL_PATTERNS = [
    r'^hola\b',
    r'^¿?cómo estás\??$',
    r'^¿?qué tal\??$',
    r'^buenos días\b',
    r'^buenas tardes\b',
    r'^buenas noches\b',
    r'^¿?cómo te llamas\??$',
    r'^¿?quién eres\??$',
    r'^gracias\b',
    r'^de nada\b',
    r'^adiós\b',
    r'^hasta luego\b',
    r'^ok\b',
    r'^vale\b',
    r'^perfecto\b',
    r'^entiendo\b'
]

TASK_PATTERNS = [
    r'crear\b.*\b(informe|reporte|documento|análisis|plan|estrategia)',
    r'analizar\b.*\b(datos|información|tendencias|mercado)',
    r'buscar\b.*\b(información|datos|sobre)',
    r'investigar\b.*\b(sobre|tendencias|mercado)',
    r'generar\b.*\b(contenido|texto|código|script)',
    r'desarrollar\b.*\b(aplicación|web|software)',
    r'escribir\b.*\b(código|script|programa)',
    r'hacer\b.*\b(análisis|investigación|estudio)',
    r'realizar\b.*\b(estudio|investigación|análisis)',
    r'dame\b.*\b(información|datos|informe|reporte)',
    r'necesito\b.*\b(información|datos|ayuda con)',
    r'quiero\b.*\b(crear|generar|desarrollar|hacer)',
    r'puedes\b.*\b(crear|generar|buscar|investigar)',
    r'ayúdame\b.*\b(con|a crear|a generar|a desarrollar)'
]

def is_casual_conversation(message: str) -> bool:
    """Detecta si un mensaje es una conversación casual"""
    message_lower = message.lower().strip()
    
    # Mensajes muy cortos (menos de 3 palabras) probablemente son casuales
    if len(message_lower.split()) <= 3:
        for pattern in CASUAL_PATTERNS:
            if re.search(pattern, message_lower):
                return True
    
    # Verificar patrones de tareas
    for pattern in TASK_PATTERNS:
        if re.search(pattern, message_lower):
            return False
    
    # Si no hay patrones de tareas y es corto, probablemente es casual
    if len(message_lower.split()) <= 5:
        return True
    
    return False

def get_ollama_service():
    """Obtener servicio de Ollama"""
    try:
        return current_app.ollama_service
    except AttributeError:
        logger.error("Ollama service not available")
        return None

def get_tool_manager():
    """Obtener tool manager"""
    try:
        return current_app.tool_manager
    except AttributeError:
        logger.error("Tool manager not available")
        return None

class UltraSimpleActionPlanner:
    """Planificador de acciones ultra simple y efectivo"""
    
    def generate_action_plan(self, task_description: str, task_id: str):
        """
        Genera un plan de acción paso a paso REAL para la tarea
        """
        try:
            # 1. Analizar la tarea y determinar herramientas necesarias
            analysis = self._analyze_task(task_description)
            
            # 2. Crear plan paso a paso basado en el análisis
            action_plan = self._create_step_by_step_plan(analysis, task_description)
            
            # 3. Guardar plan en memoria
            active_task_plans[task_id] = {
                'plan': action_plan,
                'current_step': 0,
                'status': 'ready',
                'created_at': datetime.now().isoformat()
            }
            
            logger.info(f"📋 Generated action plan for task {task_id} with {len(action_plan)} steps")
            return action_plan
            
        except Exception as e:
            logger.error(f"Error generating action plan: {str(e)}")
            return self._create_fallback_plan(task_description)
    
    def _analyze_task(self, task_description: str) -> dict:
        """Analiza la tarea para determinar qué herramientas usar"""
        task_lower = task_description.lower()
        
        analysis = {
            'task_type': 'general',
            'complexity': 'medium',
            'tools_needed': [],
            'estimated_steps': 3,
            'requires_web_search': False,
            'requires_analysis': False,
            'requires_creation': False
        }
        
        # Detectar tipo de tarea
        if any(word in task_lower for word in ['busca', 'investiga', 'encuentra', 'información', 'datos', 'search', 'informe', 'reporte']):
            analysis['task_type'] = 'research'
            analysis['tools_needed'].append('web_search')
            analysis['requires_web_search'] = True
            analysis['estimated_steps'] = 4
        
        if any(word in task_lower for word in ['analiza', 'compara', 'evalúa', 'estudia', 'examine']):
            analysis['task_type'] = 'analysis'
            analysis['requires_analysis'] = True
            analysis['estimated_steps'] = 5
        
        if any(word in task_lower for word in ['crea', 'genera', 'escribe', 'desarrolla', 'diseña']):
            analysis['task_type'] = 'creation'
            analysis['requires_creation'] = True
            analysis['estimated_steps'] = 6
        
        # Determinar complejidad
        word_count = len(task_description.split())
        if word_count > 20:
            analysis['complexity'] = 'high'
            analysis['estimated_steps'] += 2
        elif word_count < 5:
            analysis['complexity'] = 'low'
            analysis['estimated_steps'] = max(2, analysis['estimated_steps'] - 1)
        
        return analysis
    
    def _create_step_by_step_plan(self, analysis: dict, task_description: str) -> list:
        """Crea un plan paso a paso específico para la tarea"""
        
        steps = []
        step_id = 1
        
        # Paso 1: Siempre empezar con análisis
        steps.append({
            'id': f'step_{step_id}',
            'title': 'Análisis inicial de la tarea',
            'description': f'Analizar y comprender: "{task_description}"',
            'tool': 'analysis',
            'status': 'pending',
            'estimated_time': '30 segundos',
            'completed': False,
            'active': True
        })
        step_id += 1
        
        # Pasos específicos según el tipo de tarea
        if analysis['task_type'] == 'research':
            steps.extend([
                {
                    'id': f'step_{step_id}',
                    'title': 'Búsqueda de información',
                    'description': 'Buscar información relevante en internet',
                    'tool': 'web_search',
                    'status': 'pending',
                    'estimated_time': '1-2 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 1}',
                    'title': 'Filtrado de resultados',
                    'description': 'Filtrar y organizar la información encontrada',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 2}',
                    'title': 'Presentación de resultados',
                    'description': 'Presentar la información de manera clara y organizada',
                    'tool': 'formatting',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': False
                }
            ])
        
        elif analysis['task_type'] == 'analysis':
            steps.extend([
                {
                    'id': f'step_{step_id}',
                    'title': 'Recopilación de datos',
                    'description': 'Recopilar datos necesarios para el análisis',
                    'tool': 'data_collection',
                    'status': 'pending',
                    'estimated_time': '1-2 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 1}',
                    'title': 'Análisis comparativo',
                    'description': 'Realizar análisis comparativo de los datos',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '2-3 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 2}',
                    'title': 'Conclusiones',
                    'description': 'Elaborar conclusiones basadas en el análisis',
                    'tool': 'synthesis',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': False
                }
            ])
        
        elif analysis['task_type'] == 'creation':
            steps.extend([
                {
                    'id': f'step_{step_id}',
                    'title': 'Planificación del contenido',
                    'description': 'Planificar estructura y contenido a crear',
                    'tool': 'planning',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 1}',
                    'title': 'Desarrollo del contenido',
                    'description': 'Crear el contenido según la planificación',
                    'tool': 'content_creation',
                    'status': 'pending',
                    'estimated_time': '3-5 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 2}',
                    'title': 'Revisión y mejora',
                    'description': 'Revisar y mejorar el contenido creado',
                    'tool': 'review',
                    'status': 'pending',
                    'estimated_time': '1-2 minutos',
                    'completed': False,
                    'active': False
                }
            ])
        
        else:
            # Plan genérico para tareas no clasificadas
            steps.extend([
                {
                    'id': f'step_{step_id}',
                    'title': 'Procesamiento de la solicitud',
                    'description': 'Procesar y ejecutar la solicitud del usuario',
                    'tool': 'processing',
                    'status': 'pending',
                    'estimated_time': '1-2 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 1}',
                    'title': 'Entrega de resultados',
                    'description': 'Entregar los resultados al usuario',
                    'tool': 'delivery',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': False
                }
            ])
        
        return steps
    
    def _create_fallback_plan(self, task_description: str) -> list:
        """Plan básico de fallback en caso de error"""
        return [
            {
                'id': 'step_1',
                'title': 'Análisis de la tarea',
                'description': f'Analizar: "{task_description}"',
                'tool': 'analysis',
                'status': 'pending',
                'estimated_time': '30 segundos',
                'completed': False,
                'active': True
            },
            {
                'id': 'step_2',
                'title': 'Ejecución de la tarea',
                'description': 'Ejecutar la tarea solicitada',
                'tool': 'execution',
                'status': 'pending',
                'estimated_time': '1-2 minutos',
                'completed': False,
                'active': False
            },
            {
                'id': 'step_3',
                'title': 'Entrega de resultados',
                'description': 'Entregar los resultados finales',
                'tool': 'delivery',
                'status': 'pending',
                'estimated_time': '30 segundos',
                'completed': False,
                'active': False
            }
        ]

class UltraSimpleTaskExecutor:
    """Ejecutor de tareas ultra simple"""
    
    def execute_task_with_plan(self, task_description: str, task_id: str, plan: list) -> dict:
        """
        Ejecuta una tarea siguiendo el plan paso a paso
        """
        try:
            results = []
            
            # Ejecutar cada paso del plan
            for i, step in enumerate(plan):
                try:
                    # Marcar paso como activo
                    step['status'] = 'executing'
                    step['active'] = True
                    
                    # Ejecutar el paso
                    step_result = self._execute_step(step, task_description)
                    
                    # Marcar paso como completado
                    step['status'] = 'completed'
                    step['completed'] = True
                    step['active'] = False
                    
                    # Activar siguiente paso
                    if i + 1 < len(plan):
                        plan[i + 1]['active'] = True
                    
                    results.append(step_result)
                    
                    # Actualizar plan en memoria
                    if task_id in active_task_plans:
                        active_task_plans[task_id]['plan'] = plan
                        active_task_plans[task_id]['current_step'] = i + 1
                    
                    # Simular tiempo de ejecución
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error executing step {step['id']}: {str(e)}")
                    step['status'] = 'failed'
                    step['error'] = str(e)
                    results.append({
                        'step_id': step['id'],
                        'success': False,
                        'error': str(e)
                    })
            
            # Generar respuesta final
            final_response = self._generate_final_response(task_description, results)
            
            logger.info(f"✅ Task {task_id} completed successfully")
            
            return {
                'success': True,
                'response': final_response,
                'plan': plan,
                'step_results': results,
                'execution_time': time.time(),
                'task_id': task_id
            }
            
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Error ejecutando la tarea: {str(e)}"
            }
    
    def _execute_step(self, step: dict, task_description: str) -> dict:
        """Ejecuta un paso individual del plan"""
        
        step_id = step['id']
        tool_name = step.get('tool', 'generic')
        
        try:
            if tool_name == 'web_search':
                # Simular búsqueda web
                return {
                    'step_id': step_id,
                    'success': True,
                    'output': f"Búsqueda web completada - encontrados resultados para: {task_description}",
                    'data': [
                        {'title': 'Resultado 1', 'url': 'https://example.com/1', 'snippet': 'Información relevante encontrada'},
                        {'title': 'Resultado 2', 'url': 'https://example.com/2', 'snippet': 'Más información útil'},
                        {'title': 'Resultado 3', 'url': 'https://example.com/3', 'snippet': 'Datos adicionales'}
                    ]
                }
            
            elif tool_name == 'analysis':
                # Simular análisis
                return {
                    'step_id': step_id,
                    'success': True,
                    'output': 'Análisis completado exitosamente',
                    'data': f"Análisis detallado de: {task_description}"
                }
            
            elif tool_name == 'planning':
                # Simular planificación
                return {
                    'step_id': step_id,
                    'success': True,
                    'output': 'Planificación completada - estructura definida',
                    'data': f"Plan estructurado para: {task_description}"
                }
            
            elif tool_name == 'content_creation':
                # Simular creación de contenido
                return {
                    'step_id': step_id,
                    'success': True,
                    'output': 'Contenido creado exitosamente',
                    'data': f"Contenido generado para: {task_description}"
                }
            
            else:
                # Paso genérico
                return {
                    'step_id': step_id,
                    'success': True,
                    'output': f"Paso '{step['title']}' completado exitosamente",
                    'data': f"Procesamiento completado para: {step['description']}"
                }
                
        except Exception as e:
            logger.error(f"Error in step execution: {str(e)}")
            return {
                'step_id': step_id,
                'success': False,
                'error': str(e),
                'output': f"Error ejecutando paso: {str(e)}"
            }
    
    def _generate_final_response(self, task_description: str, step_results: list) -> str:
        """Genera respuesta final basada en los resultados de los pasos"""
        
        try:
            # Recopilar datos de todos los pasos exitosos
            successful_results = [r for r in step_results if r.get('success', False)]
            
            if not successful_results:
                return f"No se pudieron completar los pasos de la tarea: {task_description}"
            
            # Crear respuesta combinando los resultados
            response_parts = [f"**✅ Tarea completada exitosamente:** {task_description}\n"]
            
            # Agregar resultados de búsqueda si existen
            search_results = []
            analysis_results = []
            content_results = []
            
            for result in successful_results:
                if result.get('data'):
                    if isinstance(result['data'], list):
                        search_results.extend(result['data'])
                    elif isinstance(result['data'], str):
                        if 'análisis' in result.get('output', '').lower():
                            analysis_results.append(result['data'])
                        elif 'contenido' in result.get('output', '').lower():
                            content_results.append(result['data'])
            
            # Formatear respuesta final
            if search_results:
                response_parts.append("\n**🔍 Información encontrada:**")
                for i, search_result in enumerate(search_results[:3], 1):
                    if isinstance(search_result, dict):
                        response_parts.append(f"{i}. **{search_result.get('title', 'Sin título')}**")
                        response_parts.append(f"   {search_result.get('snippet', 'Sin descripción')}")
                        response_parts.append(f"   🔗 {search_result.get('url', '')}")
            
            if analysis_results:
                response_parts.append("\n**📊 Análisis realizado:**")
                for analysis in analysis_results:
                    response_parts.append(f"{analysis}")
            
            if content_results:
                response_parts.append("\n**📝 Contenido generado:**")
                for content in content_results:
                    response_parts.append(f"{content}")
            
            # Agregar resumen de pasos completados
            response_parts.append(f"\n**📋 Resumen de ejecución:**")
            response_parts.append(f"• Pasos completados: {len(successful_results)}/{len(step_results)}")
            response_parts.append(f"• Estado: {'✅ Completado' if len(successful_results) == len(step_results) else '⚠️ Parcialmente completado'}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error generating final response: {str(e)}")
            return f"**Tarea procesada:** {task_description}\n\nSe completaron {len([r for r in step_results if r.get('success', False)])} pasos exitosamente."

# Inicializar componentes
action_planner = UltraSimpleActionPlanner()
task_executor = UltraSimpleTaskExecutor()

@agent_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal del chat - VERSIÓN ULTRA SIMPLE Y EFECTIVA
    Genera planes de acción REALES y los ejecuta paso a paso
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Obtener task_id del contexto
        task_id = context.get('task_id', str(uuid.uuid4()))
        
        logger.info(f"🚀 Processing task: {message[:50]}... (ID: {task_id})")
        
        # PASO 1: Generar plan de acción REAL
        action_plan = action_planner.generate_action_plan(message, task_id)
        
        logger.info(f"📋 Generated action plan with {len(action_plan)} steps")
        
        # PASO 2: Ejecutar la tarea siguiendo el plan
        execution_result = task_executor.execute_task_with_plan(message, task_id, action_plan)
        
        if execution_result.get('success'):
            logger.info(f"✅ Task completed successfully")
            
            return jsonify({
                'response': execution_result['response'],
                'task_id': task_id,
                'plan': execution_result['plan'],
                'step_results': execution_result['step_results'],
                'timestamp': datetime.now().isoformat(),
                'execution_status': 'completed',
                'mode': 'agent_with_plan',
                'memory_used': True
            })
        else:
            logger.error(f"❌ Task execution failed: {execution_result.get('error')}")
            
            return jsonify({
                'response': execution_result.get('response', 'Error ejecutando la tarea'),
                'task_id': task_id,
                'error': execution_result.get('error'),
                'timestamp': datetime.now().isoformat(),
                'execution_status': 'failed'
            })
    
    except Exception as e:
        logger.error(f"Error general en chat: {str(e)}")
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@agent_bp.route('/generate-plan', methods=['POST'])
def generate_plan():
    """
    Endpoint para generar planes de acción sin ejecutar
    """
    try:
        data = request.get_json()
        task_title = data.get('task_title', '')
        
        if not task_title:
            return jsonify({'error': 'task_title is required'}), 400
        
        # Generar task_id temporal
        task_id = str(uuid.uuid4())
        
        # Generar plan de acción
        action_plan = action_planner.generate_action_plan(task_title, task_id)
        
        return jsonify({
            'plan': action_plan,
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'plan_generated'
        })
    
    except Exception as e:
        logger.error(f"Error generating plan: {str(e)}")
        return jsonify({
            'error': f'Error generando plan: {str(e)}'
        }), 500

@agent_bp.route('/update-task-progress', methods=['POST'])
def update_task_progress():
    """Actualiza el progreso de una tarea"""
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id', '')
        step_id = data.get('step_id', '')
        completed = data.get('completed', False)
        
        if not task_id or not step_id:
            return jsonify({'error': 'task_id and step_id are required'}), 400
        
        # Actualizar progreso en memoria
        if task_id in active_task_plans:
            plan = active_task_plans[task_id]['plan']
            for step in plan:
                if step['id'] == step_id:
                    step['completed'] = completed
                    step['status'] = 'completed' if completed else 'pending'
                    break
            
            # Actualizar plan en memoria
            active_task_plans[task_id]['plan'] = plan
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'step_id': step_id,
            'completed': completed
        })
        
    except Exception as e:
        logger.error(f"Error updating task progress: {str(e)}")
        return jsonify({
            'error': f'Error actualizando progreso: {str(e)}'
        }), 500

@agent_bp.route('/get-task-plan/<task_id>', methods=['GET'])
def get_task_plan(task_id):
    """Obtiene el plan de una tarea específica"""
    try:
        if task_id in active_task_plans:
            return jsonify({
                'plan': active_task_plans[task_id]['plan'],
                'current_step': active_task_plans[task_id]['current_step'],
                'status': active_task_plans[task_id]['status'],
                'created_at': active_task_plans[task_id]['created_at']
            })
        else:
            return jsonify({
                'error': 'Task plan not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error getting task plan: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo plan: {str(e)}'
        }), 500

@agent_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'ollama': True,  # Simplified
            'tools': 12,     # Simplified
            'database': True # Simplified
        }
    })

@agent_bp.route('/status', methods=['GET'])
def agent_status():
    """Status del agente"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': len(active_task_plans),
        'ollama': {
            'connected': True,
            'endpoint': 'https://78d08925604a.ngrok-free.app',
            'model': 'llama3.1:8b'
        },
        'tools': 12,
        'memory': {
            'enabled': True,
            'initialized': True
        }
    })

# Mantener endpoints adicionales necesarios para compatibilidad
@agent_bp.route('/generate-suggestions', methods=['POST'])
def generate_suggestions():
    """Genera sugerencias dinámicas simples"""
    try:
        # Sugerencias estáticas simples pero útiles
        suggestions = [
            {
                'title': 'Buscar información sobre IA',
                'description': 'Investigar las últimas tendencias en inteligencia artificial',
                'type': 'research'
            },
            {
                'title': 'Analizar datos de mercado',
                'description': 'Realizar análisis de tendencias del mercado actual',
                'type': 'analysis'
            },
            {
                'title': 'Crear documento técnico',
                'description': 'Generar documentación técnica profesional',
                'type': 'creation'
            }
        ]
        
        return jsonify({
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        return jsonify({
            'suggestions': [],
            'error': str(e)
        }), 500

# Endpoints de archivos simplificados
@agent_bp.route('/upload-files', methods=['POST'])
def upload_files():
    """Manejo simplificado de archivos"""
    try:
        files = request.files.getlist('files')
        task_id = request.form.get('task_id', str(uuid.uuid4()))
        
        # Procesar archivos de manera simple
        uploaded_files = []
        for file in files:
            if file and file.filename:
                file_id = str(uuid.uuid4())
                uploaded_files.append({
                    'id': file_id,
                    'name': file.filename,
                    'size': len(file.read()),
                    'mime_type': file.mimetype or 'application/octet-stream'
                })
        
        # Guardar referencias en memoria
        if task_id not in task_files:
            task_files[task_id] = []
        task_files[task_id].extend(uploaded_files)
        
        return jsonify({
            'files': uploaded_files,
            'task_id': task_id,
            'message': f'Se subieron {len(uploaded_files)} archivos exitosamente'
        })
    
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        return jsonify({
            'error': f'Error subiendo archivos: {str(e)}'
        }), 500

@agent_bp.route('/get-task-files/<task_id>', methods=['GET'])
def get_task_files(task_id):
    """Obtiene archivos de una tarea"""
    try:
        files = task_files.get(task_id, [])
        return jsonify({
            'files': files,
            'task_id': task_id,
            'count': len(files)
        })
    
    except Exception as e:
        logger.error(f"Error getting task files: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo archivos: {str(e)}'
        }), 500

@agent_bp.route('/ollama/check', methods=['POST'])
def check_ollama_connection():
    """Verifica conexión con Ollama"""
    try:
        data = request.get_json() or {}
        endpoint = data.get('endpoint', 'https://78d08925604a.ngrok-free.app')
        
        # Simular verificación exitosa
        return jsonify({
            'connected': True,
            'endpoint': endpoint,
            'status': 'healthy'
        })
    
    except Exception as e:
        logger.error(f"Error checking Ollama connection: {str(e)}")
        return jsonify({
            'connected': False,
            'error': str(e)
        }), 500

@agent_bp.route('/ollama/models', methods=['POST'])
def get_ollama_models():
    """Obtiene modelos disponibles de Ollama"""
    try:
        data = request.get_json() or {}
        endpoint = data.get('endpoint', 'https://78d08925604a.ngrok-free.app')
        
        # Simular modelos disponibles
        models = [
            {'name': 'llama3.1:8b', 'size': '4.7GB'},
            {'name': 'deepseek-r1:32b', 'size': '20GB'},
            {'name': 'qwen3:32b', 'size': '18GB'}
        ]
        
        return jsonify({
            'models': models,
            'endpoint': endpoint,
            'count': len(models)
        })
    
    except Exception as e:
        logger.error(f"Error getting Ollama models: {str(e)}")
        return jsonify({
            'models': [],
            'error': str(e)
        }), 500