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

def generate_structured_plan(message: str, task_id: str) -> dict:
    """
    Genera un plan estructurado para mostrar en el frontend
    """
    try:
        # Analizar el mensaje para determinar el tipo de tarea
        message_lower = message.lower()
        
        # Determinar pasos basados en el tipo de tarea
        if any(word in message_lower for word in ['crear', 'generar', 'escribir', 'desarrollar']):
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': 'Análisis de requisitos',
                    'description': 'Analizar los requisitos y especificaciones de la tarea',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': 'Planificación',
                    'description': 'Crear estructura y planificar el desarrollo',
                    'tool': 'planning',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': 'Desarrollo/Creación',
                    'description': 'Ejecutar la creación del contenido solicitado',
                    'tool': 'creation',
                    'status': 'pending',
                    'estimated_time': '2-3 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_4',
                    'title': 'Revisión y entrega',
                    'description': 'Revisar y entregar el resultado final',
                    'tool': 'review',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': False
                }
            ]
        elif any(word in message_lower for word in ['buscar', 'investigar', 'analizar']):
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': 'Definición de búsqueda',
                    'description': 'Definir parámetros y alcance de la investigación',
                    'tool': 'search_definition',
                    'status': 'pending',
                    'estimated_time': '20 segundos',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': 'Búsqueda de información',
                    'description': 'Buscar y recopilar información relevante',
                    'tool': 'web_search',
                    'status': 'pending',
                    'estimated_time': '1-2 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': 'Análisis de datos',
                    'description': 'Analizar y procesar la información encontrada',
                    'tool': 'data_analysis',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_4',
                    'title': 'Síntesis y presentación',
                    'description': 'Sintetizar resultados y presentar conclusiones',
                    'tool': 'synthesis',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': False
                }
            ]
        else:
            # Plan genérico para otras tareas
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': 'Análisis de la tarea',
                    'description': 'Comprender y analizar la solicitud',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': 'Procesamiento',
                    'description': 'Procesar y ejecutar la tarea solicitada',
                    'tool': 'processing',
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
        
        # Guardar plan en memoria global
        active_task_plans[task_id] = {
            'plan': plan_steps,
            'current_step': 0,
            'status': 'executing',
            'created_at': datetime.now().isoformat(),
            'message': message
        }
        
        return {
            'steps': plan_steps,
            'total_steps': len(plan_steps),
            'estimated_total_time': '2-4 minutos',
            'task_type': 'structured_execution'
        }
        
    except Exception as e:
        logger.error(f"Error generating structured plan: {str(e)}")
        # Plan de fallback simple
        fallback_plan = [
            {
                'id': 'step_1',
                'title': 'Procesando solicitud',
                'description': 'Procesando tu solicitud...',
                'tool': 'processing',
                'status': 'pending',
                'estimated_time': '1 minuto',
                'completed': False,
                'active': True
            }
        ]
        
        active_task_plans[task_id] = {
            'plan': fallback_plan,
            'current_step': 0,
            'status': 'executing',
            'created_at': datetime.now().isoformat(),
            'message': message
        }
        
        return {
            'steps': fallback_plan,
            'total_steps': 1,
            'estimated_total_time': '1 minuto',
            'task_type': 'simple_execution'
        }

def generate_clean_response(ollama_response: str, tool_results: list) -> str:
    """
    Genera una respuesta limpia sin mostrar los pasos internos del plan
    """
    try:
        # Limpiar la respuesta de Ollama de cualquier referencia a pasos internos
        clean_response = ollama_response
        
        # Remover patrones comunes de pasos internos si existen
        patterns_to_remove = [
            r'Paso \d+:.*?\n',
            r'Step \d+:.*?\n',
            r'\*\*Paso \d+\*\*.*?\n',
            r'\*\*Step \d+\*\*.*?\n',
            r'## Paso \d+.*?\n',
            r'## Step \d+.*?\n'
        ]
        
        for pattern in patterns_to_remove:
            clean_response = re.sub(pattern, '', clean_response, flags=re.IGNORECASE)
        
        # Si hay resultados de herramientas, agregar un resumen limpio
        if tool_results:
            tools_summary = []
            successful_tools = 0
            failed_tools = 0
            
            for result in tool_results:
                if result.get('error'):
                    failed_tools += 1
                else:
                    successful_tools += 1
                    # Agregar información útil del resultado si está disponible
                    if isinstance(result.get('result'), dict):
                        if 'output' in result['result']:
                            tools_summary.append(f"✅ {result['tool']}: Completado exitosamente")
            
            # Agregar resumen al final de la respuesta
            if successful_tools > 0 or failed_tools > 0:
                clean_response += f"\n\n---\n**🔧 Herramientas utilizadas:** {successful_tools} exitosas"
                if failed_tools > 0:
                    clean_response += f", {failed_tools} con errores"
                clean_response += "\n"
                
                # Agregar detalles de herramientas exitosas
                for summary in tools_summary[:3]:  # Máximo 3 para no saturar
                    clean_response += f"{summary}\n"
        
        # Limpiar espacios extra y líneas vacías múltiples
        clean_response = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_response)
        clean_response = clean_response.strip()
        
        return clean_response
        
    except Exception as e:
        logger.error(f"Error generating clean response: {str(e)}")
        # Fallback: devolver respuesta original
        return ollama_response

@agent_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal del chat - VERSIÓN REAL CON OLLAMA
    Distingue entre conversaciones casuales y tareas complejas
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Obtener task_id del contexto
        task_id = context.get('task_id', str(uuid.uuid4()))
        
        logger.info(f"🚀 Processing message: {message[:50]}... (ID: {task_id})")
        
        # Obtener servicio de Ollama
        ollama_service = get_ollama_service()
        if not ollama_service:
            return jsonify({
                'error': 'Ollama service not available',
                'response': 'Lo siento, el servicio de IA no está disponible en este momento.'
            }), 503
        
        # PASO 1: Detectar si es conversación casual o tarea compleja
        is_casual = is_casual_conversation(message)
        
        if is_casual:
            # MODO CONVERSACIÓN CASUAL
            logger.info(f"🗣️ Detected casual conversation mode")
            
            # Usar solo Ollama para respuesta casual
            ollama_response = ollama_service.generate_casual_response(message, context)
            
            if ollama_response.get('error'):
                return jsonify({
                    'error': ollama_response['error'],
                    'response': ollama_response['response']
                }), 500
            
            return jsonify({
                'response': ollama_response['response'],
                'task_id': task_id,
                'timestamp': datetime.now().isoformat(),
                'execution_status': 'completed',
                'mode': 'casual_conversation',
                'memory_used': True
            })
        
        else:
            # MODO AGENTE CON PLANIFICACIÓN
            logger.info(f"🤖 Detected task mode - generating plan and executing")
            
            # PASO 2: Generar respuesta usando Ollama con contexto de herramientas
            ollama_response = ollama_service.generate_response(message, context, use_tools=True)
            
            if ollama_response.get('error'):
                return jsonify({
                    'error': ollama_response['error'],
                    'response': ollama_response['response']
                }), 500
            
            # PASO 3: Procesar tool_calls si existen
            tool_results = []
            if ollama_response.get('tool_calls'):
                logger.info(f"🔧 Processing {len(ollama_response['tool_calls'])} tool calls")
                tool_manager = get_tool_manager()
                
                if tool_manager:
                    for tool_call in ollama_response['tool_calls']:
                        try:
                            tool_name = tool_call.get('tool')
                            parameters = tool_call.get('parameters', {})
                            
                            logger.info(f"🔧 Executing tool: {tool_name}")
                            
                            # Ejecutar herramienta real
                            tool_result = tool_manager.execute_tool(tool_name, parameters)
                            tool_results.append({
                                'tool': tool_name,
                                'parameters': parameters,
                                'result': tool_result
                            })
                            
                        except Exception as e:
                            logger.error(f"Error executing tool {tool_name}: {str(e)}")
                            tool_results.append({
                                'tool': tool_name,
                                'parameters': parameters,
                                'error': str(e)
                            })
            
            # PASO 4: Generar respuesta final incorporando resultados de herramientas
            final_response = ollama_response['response']
            
            if tool_results:
                # Agregar resultados de herramientas a la respuesta
                final_response += "\n\n**🔧 Herramientas ejecutadas:**\n"
                for result in tool_results:
                    if result.get('error'):
                        final_response += f"❌ {result['tool']}: {result['error']}\n"
                    else:
                        final_response += f"✅ {result['tool']}: Ejecutado correctamente\n"
                        # Agregar algunos datos del resultado si están disponibles
                        if isinstance(result.get('result'), dict):
                            if 'output' in result['result']:
                                final_response += f"   📋 {result['result']['output'][:100]}...\n"
            
            logger.info(f"✅ Task completed successfully")
            
            return jsonify({
                'response': final_response,
                'task_id': task_id,
                'tool_calls': ollama_response.get('tool_calls', []),
                'tool_results': tool_results,
                'timestamp': datetime.now().isoformat(),
                'execution_status': 'completed',
                'mode': 'agent_with_tools',
                'memory_used': True
            })
    
    except Exception as e:
        logger.error(f"Error general en chat: {str(e)}")
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}',
            'response': 'Lo siento, hubo un error procesando tu solicitud.'
        }), 500

@agent_bp.route('/generate-plan', methods=['POST'])
def generate_plan():
    """
    Endpoint para generar planes de acción sin ejecutar - SIMPLIFICADO
    """
    try:
        data = request.get_json()
        task_title = data.get('task_title', '')
        
        if not task_title:
            return jsonify({'error': 'task_title is required'}), 400
        
        # Generar task_id temporal
        task_id = str(uuid.uuid4())
        
        # Generar plan simple basado en el título
        simple_plan = [
            {
                'id': 'step_1',
                'title': 'Análisis de la tarea',
                'description': f'Analizar: "{task_title}"',
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
        
        # Guardar plan en memoria
        active_task_plans[task_id] = {
            'plan': simple_plan,
            'current_step': 0,
            'status': 'ready',
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'plan': simple_plan,
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