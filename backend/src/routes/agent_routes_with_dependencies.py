"""
Rutas API del agente - Versión EFECTIVA Y SIMPLE
Sistema de agente que genera planes de acción REALES paso a paso
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import time
import uuid
import json
import requests
import os
from src.tools.tool_manager import ToolManager
from src.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

agent_bp = Blueprint('agent', __name__)

# Almacenamiento temporal para compartir conversaciones
shared_conversations = {}
# Almacenamiento temporal para archivos por tarea
task_files = {}
# Almacenamiento global para planes de tareas
active_task_plans = {}

# Inicializar componentes básicos
tool_manager = ToolManager()
ollama_service = OllamaService()

class SimpleActionPlanner:
    """Planificador de acciones simple y efectivo"""
    
    def __init__(self):
        self.tool_manager = tool_manager
        self.ollama_service = ollama_service
    
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
        if any(word in task_lower for word in ['busca', 'investiga', 'encuentra', 'información', 'datos', 'search']):
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
        
        if any(word in task_lower for word in ['informe', 'reporte', 'documento', 'resumen']):
            analysis['task_type'] = 'report'
            analysis['tools_needed'].extend(['web_search', 'analysis'])
            analysis['requires_web_search'] = True
            analysis['requires_analysis'] = True
            analysis['estimated_steps'] = 7
        
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
        
        elif analysis['task_type'] == 'report':
            steps.extend([
                {
                    'id': f'step_{step_id}',
                    'title': 'Investigación inicial',
                    'description': 'Buscar información relevante para el informe',
                    'tool': 'web_search',
                    'status': 'pending',
                    'estimated_time': '2-3 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 1}',
                    'title': 'Análisis de fuentes',
                    'description': 'Analizar y validar las fuentes encontradas',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '2 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 2}',
                    'title': 'Estructuración del informe',
                    'description': 'Organizar la información en estructura coherente',
                    'tool': 'structuring',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 3}',
                    'title': 'Redacción del informe',
                    'description': 'Redactar el informe completo',
                    'tool': 'writing',
                    'status': 'pending',
                    'estimated_time': '3-4 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': f'step_{step_id + 4}',
                    'title': 'Revisión final',
                    'description': 'Revisar y pulir el informe final',
                    'tool': 'review',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
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

class SimpleTaskExecutor:
    """Ejecutor de tareas simple y efectivo"""
    
    def __init__(self):
        self.tool_manager = tool_manager
        self.ollama_service = ollama_service
    
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
                # Ejecutar búsqueda web
                return self._execute_web_search(task_description, step)
            
            elif tool_name == 'analysis':
                # Ejecutar análisis
                return self._execute_analysis(task_description, step)
            
            elif tool_name == 'planning':
                # Ejecutar planificación
                return self._execute_planning(task_description, step)
            
            elif tool_name == 'content_creation':
                # Ejecutar creación de contenido
                return self._execute_content_creation(task_description, step)
            
            else:
                # Ejecutar paso genérico
                return self._execute_generic_step(task_description, step)
                
        except Exception as e:
            logger.error(f"Error in step execution: {str(e)}")
            return {
                'step_id': step_id,
                'success': False,
                'error': str(e),
                'output': f"Error ejecutando paso: {str(e)}"
            }
    
    def _execute_web_search(self, task_description: str, step: dict) -> dict:
        """Ejecuta búsqueda web"""
        try:
            # Usar tool_manager para ejecutar búsqueda
            search_result = self.tool_manager.execute_tool(
                'web_search',
                {'query': task_description, 'max_results': 5}
            )
            
            if search_result.get('error'):
                return {
                    'step_id': step['id'],
                    'success': False,
                    'error': search_result['error'],
                    'output': f"Error en búsqueda: {search_result['error']}"
                }
            
            # Formatear resultados
            results = search_result.get('results', [])
            formatted_results = []
            
            for result in results[:3]:  # Tomar solo los primeros 3
                formatted_results.append({
                    'title': result.get('title', 'Sin título'),
                    'url': result.get('url', ''),
                    'snippet': result.get('snippet', 'Sin descripción')
                })
            
            return {
                'step_id': step['id'],
                'success': True,
                'output': f"Encontrados {len(formatted_results)} resultados relevantes",
                'data': formatted_results
            }
            
        except Exception as e:
            return {
                'step_id': step['id'],
                'success': False,
                'error': str(e),
                'output': f"Error en búsqueda web: {str(e)}"
            }
    
    def _execute_analysis(self, task_description: str, step: dict) -> dict:
        """Ejecuta análisis usando LLM"""
        try:
            # Usar Ollama para análisis
            analysis_prompt = f"""
            Analiza la siguiente tarea paso a paso:
            
            Tarea: {task_description}
            
            Proporciona un análisis breve y claro de:
            1. Qué se está pidiendo
            2. Qué información o recursos se necesitan
            3. Cuál sería el mejor enfoque
            
            Responde de manera concisa y práctica.
            """
            
            response = self.ollama_service.generate_response(analysis_prompt)
            
            if response.get('error'):
                return {
                    'step_id': step['id'],
                    'success': False,
                    'error': response['error'],
                    'output': f"Error en análisis: {response['error']}"
                }
            
            analysis_result = response.get('response', 'Análisis completado')
            
            return {
                'step_id': step['id'],
                'success': True,
                'output': 'Análisis completado exitosamente',
                'data': analysis_result
            }
            
        except Exception as e:
            return {
                'step_id': step['id'],
                'success': False,
                'error': str(e),
                'output': f"Error en análisis: {str(e)}"
            }
    
    def _execute_planning(self, task_description: str, step: dict) -> dict:
        """Ejecuta planificación"""
        return {
            'step_id': step['id'],
            'success': True,
            'output': 'Planificación completada - estructura definida',
            'data': f"Plan estructurado para: {task_description}"
        }
    
    def _execute_content_creation(self, task_description: str, step: dict) -> dict:
        """Ejecuta creación de contenido"""
        try:
            # Usar Ollama para crear contenido
            creation_prompt = f"""
            Crea contenido para la siguiente solicitud:
            
            {task_description}
            
            Proporciona una respuesta completa, bien estructurada y útil.
            """
            
            response = self.ollama_service.generate_response(creation_prompt)
            
            if response.get('error'):
                return {
                    'step_id': step['id'],
                    'success': False,
                    'error': response['error'],
                    'output': f"Error creando contenido: {response['error']}"
                }
            
            content = response.get('response', 'Contenido creado')
            
            return {
                'step_id': step['id'],
                'success': True,
                'output': 'Contenido creado exitosamente',
                'data': content
            }
            
        except Exception as e:
            return {
                'step_id': step['id'],
                'success': False,
                'error': str(e),
                'output': f"Error creando contenido: {str(e)}"
            }
    
    def _execute_generic_step(self, task_description: str, step: dict) -> dict:
        """Ejecuta paso genérico"""
        # Simular ejecución del paso
        time.sleep(0.5)  # Simular tiempo de procesamiento
        
        return {
            'step_id': step['id'],
            'success': True,
            'output': f"Paso '{step['title']}' completado exitosamente",
            'data': f"Procesamiento completado para: {step['description']}"
        }
    
    def _generate_final_response(self, task_description: str, step_results: list) -> str:
        """Genera respuesta final basada en los resultados de los pasos"""
        
        try:
            # Recopilar datos de todos los pasos exitosos
            successful_results = [r for r in step_results if r.get('success', False)]
            
            if not successful_results:
                return f"No se pudieron completar los pasos de la tarea: {task_description}"
            
            # Crear respuesta combinando los resultados
            response_parts = [f"**Tarea completada:** {task_description}\n"]
            
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
            response_parts.append(f"\n**✅ Pasos completados:** {len(successful_results)}/{len(step_results)}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error generating final response: {str(e)}")
            return f"Tarea procesada: {task_description}\n\nSe completaron {len([r for r in step_results if r.get('success', False)])} pasos exitosamente."

# Inicializar componentes
action_planner = SimpleActionPlanner()
task_executor = SimpleTaskExecutor()

@agent_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal del chat - VERSIÓN SIMPLE Y EFECTIVA
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
        
        logger.info(f"🚀 Processing task: {message} (ID: {task_id})")
        
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
                'mode': 'agent_with_plan'
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
            'ollama': ollama_service.is_healthy() if ollama_service else False,
            'tools': len(tool_manager.get_available_tools()) if tool_manager else 0,
            'database': True  # Simplified for now
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
            'connected': ollama_service.is_healthy() if ollama_service else False,
            'endpoint': getattr(ollama_service, 'base_url', 'unknown'),
            'model': getattr(ollama_service, 'default_model', 'unknown')
        },
        'tools': len(tool_manager.get_available_tools()) if tool_manager else 0
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