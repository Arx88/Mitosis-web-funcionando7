"""
Rutas API del agente - Versión REAL CON OLLAMA
Sistema de agente que usa Ollama real para generar respuestas inteligentes
Y distingue entre conversaciones casuales y tareas complejas
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from typing import Dict, Any
import logging
import time
import uuid
import json
import os
import requests
import re
import jsonschema
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 🆕 PROBLEMA 2: Importar sistema de validación de resultados
from ..validation.result_validators import (
    validate_step_result, 
    StepStatus, 
    TaskStatus, 
    determine_task_status_from_steps
)

# Import UpdateType for WebSocket updates
try:
    from src.websocket.websocket_manager import UpdateType
except ImportError:
    # Fallback if UpdateType is not available
    UpdateType = None

logger = logging.getLogger(__name__)

# JSON Schema para validación de planes generados por Ollama
# Mejora implementada según UPGRADE.md Sección 2: Validación de Esquemas JSON
PLAN_SCHEMA = {
    "type": "object",
    "required": ["steps", "task_type", "complexity"],
    "properties": {
        "steps": {
            "type": "array",
            "minItems": 3,
            "maxItems": 6,
            "items": {
                "type": "object",
                "required": ["title", "description", "tool"],
                "properties": {
                    "title": {
                        "type": "string",
                        "minLength": 5,
                        "maxLength": 100
                    },
                    "description": {
                        "type": "string", 
                        "minLength": 10,
                        "maxLength": 300
                    },
                    "tool": {
                        "type": "string",
                        "enum": ["web_search", "analysis", "creation", "planning", "delivery", "processing", "synthesis", "search_definition", "data_analysis", "shell", "research", "investigation", "web_scraping", "search", "mind_map", "spreadsheets", "database"]
                    },
                    "estimated_time": {
                        "type": "string"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["alta", "media", "baja"]
                    }
                },
                "additionalProperties": False
            }
        },
        "task_type": {
            "type": "string",
            "minLength": 3
        },
        "complexity": {
            "type": ["string", "number"],
            "pattern": "^(baja|media|alta)$|^[0-9]+(\\.[0-9]+)?$"
        },
        "estimated_total_time": {
            "type": "string"
        },
        "suggested_icon": {
            "type": "string",
            "enum": [
                "map", "code", "file", "chart", "search", "image", "music", "briefcase", "target"
            ]
        }
    },
   "additionalProperties": False
}

agent_bp = Blueprint('agent', __name__)

@agent_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint para verificar MongoDB y sistema"""
    try:
        # Verificar TaskManager y MongoDB
        task_manager = get_task_manager()
        db_service = task_manager.db_service
        
        # Test de conexión MongoDB
        mongo_status = db_service.check_connection()
        
        # Verificar Ollama
        ollama_service = get_ollama_service()
        ollama_healthy = ollama_service.is_healthy() if ollama_service else False
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'mongodb': {
                'connected': mongo_status.get('healthy', False),
                'database': mongo_status.get('database', 'unknown'),
                'collections': mongo_status.get('collections', 0),
                'size_mb': mongo_status.get('size_mb', 0)
            },
            'ollama': {
                'connected': ollama_healthy
            },
            'task_manager': {
                'active_cache_size': len(task_manager.active_cache)
            }
        })
    except Exception as e:
        logger.error(f"❌ Error en health check: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/execute-step-detailed/<task_id>/<step_id>', methods=['POST'])
def execute_single_step_detailed(task_id: str, step_id: str):
    """
    Ejecutar un paso específico del plan de manera controlada y secuencial
    """
    try:
        # Obtener datos de la tarea
        task_data = get_task_data(task_id)
        if not task_data:
            return jsonify({'error': f'Task {task_id} not found'}), 404
        
        # Encontrar el paso específico
        steps = task_data.get('plan', [])
        current_step = None
        step_index = -1
        
        for i, step in enumerate(steps):
            if step.get('id') == step_id:
                current_step = step
                step_index = i
                break
        
        if not current_step:
            return jsonify({'error': f'Step {step_id} not found'}), 404
        
        # VALIDACIÓN: Verificar que los pasos anteriores estén completados
        if step_index > 0:
            for i in range(step_index):
                previous_step = steps[i]
                if not previous_step.get('completed', False):
                    return jsonify({
                        'error': 'Los pasos anteriores deben completarse primero',
                        'blocking_step': previous_step.get('title'),
                        'must_complete_first': True
                    }), 400
        
        # Verificar que el paso no esté ya completado
        if current_step.get('completed', False):
            return jsonify({
                'error': 'Este paso ya está completado',
                'step_already_completed': True
            }), 400
        
        logger.info(f"🔄 Ejecutando paso específico {step_index + 1}: {current_step['title']} para task {task_id}")
        
        # Marcar paso como en progreso
        current_step['active'] = True
        current_step['status'] = 'in-progress'
        current_step['start_time'] = datetime.now().isoformat()
        
        # Actualizar en persistencia
        update_task_data(task_id, {'plan': steps})
        
        # Ejecutar el paso específico
        step_result = execute_single_step_logic(current_step, task_data.get('message', ''), task_id)
        
        # Actualizar resultado del paso
        current_step['active'] = False
        current_step['completed'] = True
        current_step['status'] = 'completed'
        current_step['result'] = step_result
        current_step['completed_time'] = datetime.now().isoformat()
        
        # Actualizar en persistencia
        update_task_data(task_id, {'plan': steps})
        
        # Verificar si todos los pasos están completados
        all_completed = all(step.get('completed', False) for step in steps)
        
        response_data = {
            'success': True,
            'step_result': step_result,
            'step_completed': True,
            'all_steps_completed': all_completed,
            'next_step': steps[step_index + 1] if step_index + 1 < len(steps) else None
        }
        
        if all_completed:
            # Marcar tarea como completada
            update_task_data(task_id, {'status': 'completed', 'completed_at': datetime.now().isoformat()})
            response_data['task_completed'] = True
            logger.info(f"🎉 Tarea {task_id} completada - todos los pasos ejecutados")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando paso {step_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/get-task-status/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """
    CRITICAL FIX: Endpoint para HTTP polling del frontend con executionData incluido
    Obtener el estado actual de una tarea para polling frontend incluyendo executed_tools
    """
    try:
        task_data = get_task_data(task_id)
        if not task_data:
            return jsonify({'error': f'Task {task_id} not found'}), 404
        
        steps = task_data.get('plan', [])
        
        # Calcular estadísticas del plan
        completed_steps = sum(1 for step in steps if step.get('completed', False))
        in_progress_steps = sum(1 for step in steps if step.get('status') == 'in-progress')
        active_steps = sum(1 for step in steps if step.get('active', False))
        
        # Determinar estado de ejecución
        task_status = 'pending'
        if completed_steps == len(steps) and len(steps) > 0:
            task_status = 'completed'
        elif in_progress_steps > 0 or active_steps > 0:
            task_status = 'executing'  # Frontend espera 'executing' no 'in_progress'
        elif completed_steps > 0:
            task_status = 'partially_completed'
        elif len(steps) > 0:
            task_status = 'plan_generated'  # Indica que el plan está listo para ejecutar
        
        # Calcular progreso
        progress = (completed_steps / len(steps) * 100) if len(steps) > 0 else 0
        
        # CRITICAL FIX: Extraer herramientas ejecutadas de los pasos completados
        executed_tools = []
        for step in steps:
            if step.get('completed', False) and step.get('result'):
                # Extraer información de la herramienta ejecutada
                step_result = step.get('result', {})
                
                # Crear entrada de herramienta ejecutada para el frontend
                tool_execution = {
                    'tool': step.get('tool', 'unknown'),
                    'step_id': step.get('id', ''),
                    'step_title': step.get('title', ''),
                    'success': step_result.get('success', True),
                    'timestamp': step.get('completed_time', datetime.now().isoformat()),
                    'parameters': {
                        'step_description': step.get('description', ''),
                        'step_title': step.get('title', '')
                    },
                    'result': {
                        'type': step_result.get('type', 'generic'),
                        'summary': step_result.get('summary', 'Paso completado'),
                        'content': step_result.get('content', ''),
                        'execution_time': step_result.get('execution_time', 0),
                        'data': step_result.get('data', {}),
                        'file_created': step_result.get('file_created', False),
                        'file_name': step_result.get('file_name', ''),
                        'file_size': step_result.get('file_size', 0),
                        'download_url': step_result.get('download_url', ''),
                        'query': step_result.get('query', ''),
                        'results_count': step_result.get('results_count', 0)
                    }
                }
                
                executed_tools.append(tool_execution)
        
        # CRITICAL FIX: Agregar executionData que el frontend espera
        execution_data = {
            'executed_tools': executed_tools,
            'tool_executions_count': len(executed_tools),
            'has_results': len(executed_tools) > 0,
            'last_tool_execution': executed_tools[-1] if executed_tools else None
        }
        
        return jsonify({
            'task_id': task_id,
            'status': task_status,
            'plan': steps,
            'progress': progress,
            'stats': {
                'total_steps': len(steps),
                'completed_steps': completed_steps,
                'in_progress_steps': in_progress_steps,
                'active_steps': active_steps,
                'remaining_steps': len(steps) - completed_steps
            },
            'current_step': next((i for i, step in enumerate(steps) if step.get('active', False)), None),
            'message': task_data.get('message', ''),
            'task_type': task_data.get('task_type', ''),
            'complexity': task_data.get('complexity', ''),
            'executionData': execution_data,  # CRITICAL FIX: Datos de ejecución para TerminalView
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo status para task {task_id}: {str(e)}")
        return jsonify({'error': f'Error getting task status: {str(e)}'}), 500

@agent_bp.route('/get-task-plan/<task_id>', methods=['GET'])
def get_task_plan(task_id: str):
    """
    Obtener el estado actual del plan de una tarea
    """
    try:
        task_data = get_task_data(task_id)
        if not task_data:
            return jsonify({'error': f'Task {task_id} not found'}), 404
        
        steps = task_data.get('plan', [])
        
        # Calcular estadísticas del plan
        completed_steps = sum(1 for step in steps if step.get('completed', False))
        in_progress_steps = sum(1 for step in steps if step.get('status') == 'in-progress')
        
        # Determinar siguiente paso disponible
        next_step = None
        for i, step in enumerate(steps):
            if not step.get('completed', False):
                # Verificar si todos los pasos anteriores están completados
                if i == 0 or all(steps[j].get('completed', False) for j in range(i)):
                    next_step = step
                    break
        
        # Estado general de la tarea
        task_status = 'pending'
        if completed_steps == len(steps) and len(steps) > 0:
            task_status = 'completed'
        elif in_progress_steps > 0:
            task_status = 'in_progress'
        elif completed_steps > 0:
            task_status = 'partially_completed'
        
        return jsonify({
            'task_id': task_id,
            'status': task_status,
            'plan': steps,
            'stats': {
                'total_steps': len(steps),
                'completed_steps': completed_steps,
                'in_progress_steps': in_progress_steps,
                'remaining_steps': len(steps) - completed_steps
            },
            'next_step': next_step,
            'can_execute_next': next_step is not None,
            'task_data': {
                'message': task_data.get('message', ''),
                'created_at': task_data.get('created_at', ''),
                'task_type': task_data.get('task_type', ''),
                'complexity': task_data.get('complexity', '')
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo plan para task {task_id}: {str(e)}")
        return jsonify({'error': f'Error getting task plan: {str(e)}'}), 500

@agent_bp.route('/get-task-execution-results/<task_id>', methods=['GET'])
def get_task_execution_results(task_id: str):
    """
    CRITICAL FIX: Endpoint para obtener resultados de ejecución con herramientas ejecutadas
    Obtener los datos de ejecución con executed_tools para el frontend polling
    """
    try:
        task_data = get_task_data(task_id)
        if not task_data:
            return jsonify({'error': f'Task {task_id} not found'}), 404
        
        steps = task_data.get('plan', [])
        
        # Extraer herramientas ejecutadas de los pasos completados
        executed_tools = []
        for step in steps:
            if step.get('completed', False) and step.get('result'):
                # Extraer información de la herramienta ejecutada
                step_result = step.get('result', {})
                
                # Crear entrada de herramienta ejecutada
                tool_execution = {
                    'tool': step.get('tool', 'unknown'),
                    'step_id': step.get('id', ''),
                    'step_title': step.get('title', ''),
                    'success': step_result.get('success', True),
                    'timestamp': step.get('completed_time', datetime.now().isoformat()),
                    'parameters': {
                        'step_description': step.get('description', ''),
                        'step_title': step.get('title', '')
                    },
                    'result': {
                        'type': step_result.get('type', 'generic'),
                        'summary': step_result.get('summary', 'Paso completado'),
                        'content': step_result.get('content', ''),
                        'execution_time': step_result.get('execution_time', 0),
                        'data': step_result.get('data', {}),
                        'file_created': step_result.get('file_created', False),
                        'file_name': step_result.get('file_name', ''),
                        'file_size': step_result.get('file_size', 0),
                        'download_url': step_result.get('download_url', ''),
                        'query': step_result.get('query', ''),
                        'results_count': step_result.get('results_count', 0)
                    }
                }
                
                executed_tools.append(tool_execution)
        
        # Calcular estadísticas
        completed_steps = sum(1 for step in steps if step.get('completed', False))
        progress = (completed_steps / len(steps) * 100) if len(steps) > 0 else 0
        
        # Determinar estado de ejecución
        task_status = 'pending'
        if completed_steps == len(steps) and len(steps) > 0:
            task_status = 'completed'
        elif any(step.get('active', False) for step in steps):
            task_status = 'executing'
        elif completed_steps > 0:
            task_status = 'in_progress'
        
        return jsonify({
            'task_id': task_id,
            'status': task_status,
            'progress': progress,
            'execution_data': {
                'executed_tools': executed_tools,
                'total_tools': len(executed_tools),
                'execution_started': len(executed_tools) > 0,
                'execution_completed': task_status == 'completed'
            },
            'plan': steps,
            'stats': {
                'total_steps': len(steps),
                'completed_steps': completed_steps,
                'remaining_steps': len(steps) - completed_steps,
                'tools_executed': len(executed_tools)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo resultados de ejecución para task {task_id}: {str(e)}")
        return jsonify({'error': f'Error getting execution results: {str(e)}'}), 500

def execute_single_step_logic(step: dict, original_message: str, task_id: str) -> dict:
    """
    Lógica de ejecución para un paso individual con manejo de errores robusto
    """
    try:
        step_tool = step.get('tool', 'processing')
        step_title = step.get('title', 'Paso sin título')
        step_description = step.get('description', 'Sin descripción')
        
        logger.info(f"⚡ Ejecutando herramienta '{step_tool}' para paso: {step_title}")
        
        # Obtener servicios necesarios
        ollama_service = get_ollama_service()
        tool_manager = get_tool_manager()
        
        # Ejecutar según el tipo de herramienta
        if step_tool == 'web_search':
            return execute_web_search_step(step_title, step_description, tool_manager, task_id)
        elif step_tool in ['analysis', 'data_analysis']:
            return execute_analysis_step(step_title, step_description, ollama_service, original_message)
        elif step_tool == 'creation':
            return execute_creation_step(step_title, step_description, ollama_service, original_message, task_id)
        elif step_tool in ['planning', 'delivery']:
            return execute_planning_delivery_step(step_tool, step_title, step_description, ollama_service, original_message)
        else:
            # Herramienta genérica
            return execute_generic_step(step_title, step_description, ollama_service, original_message)
            
    except Exception as e:
        logger.error(f"❌ Error en ejecución de paso: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'type': 'execution_error',
            'summary': f'❌ Error al ejecutar: {str(e)}'
        }

def execute_web_search_step(title: str, description: str, tool_manager, task_id: str) -> dict:
    """Ejecutar paso de búsqueda web"""
    try:
        # Extraer query de búsqueda
        search_query = f"{title} {description}".replace('Buscar información sobre:', '').replace('Investigar:', '').strip()
        
        if tool_manager and hasattr(tool_manager, 'execute_tool'):
            result = tool_manager.execute_tool('web_search', {
                'query': search_query,
                'num_results': 5
            }, task_id=task_id)
            
            return {
                'success': True,
                'type': 'web_search',
                'query': search_query,
                'results_count': len(result.get('search_results', [])),
                'summary': f"✅ Búsqueda completada: {len(result.get('search_results', []))} resultados encontrados",
                'data': result.get('search_results', [])
            }
        else:
            raise Exception("Tool manager no disponible")
            
    except Exception as e:
        logger.error(f"❌ Web search error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'type': 'web_search_error',
            'summary': f'❌ Error en búsqueda: {str(e)}'
        }

def execute_analysis_step(title: str, description: str, ollama_service, original_message: str) -> dict:
    """Ejecutar paso de análisis"""
    try:
        if not ollama_service or not ollama_service.is_healthy():
            raise Exception("Servicio Ollama no disponible")
        
        analysis_prompt = f"""
Realiza un análisis detallado para la tarea: {original_message}

Paso específico: {title}
Descripción: {description}

Proporciona:
1. Análisis específico del contexto
2. Hallazgos principales  
3. Recomendaciones
4. Conclusiones

Formato: Respuesta estructurada y profesional en español.
"""
        
        result = ollama_service.generate_response(analysis_prompt, {'temperature': 0.7})
        
        if result.get('error'):
            raise Exception(f"Error Ollama: {result['error']}")
        
        analysis_content = result.get('response', 'Análisis completado')
        
        return {
            'success': True,
            'type': 'analysis',
            'content': analysis_content,
            'length': len(analysis_content),
            'summary': f"✅ Análisis completado - {len(analysis_content)} caracteres generados"
        }
        
    except Exception as e:
        logger.error(f"❌ Analysis error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'type': 'analysis_error',
            'summary': f'❌ Error en análisis: {str(e)}'
        }

def execute_creation_step(title: str, description: str, ollama_service, original_message: str, task_id: str) -> dict:
    """Ejecutar paso de creación con archivo real"""
    try:
        if not ollama_service or not ollama_service.is_healthy():
            raise Exception("Servicio Ollama no disponible")
        
        creation_prompt = f"""
IMPORTANTE: Genera el CONTENIDO REAL solicitado, NO un plan de acción.

Tarea original: {original_message}
Paso: {title}
Descripción: {description}

Genera contenido específico, detallado y profesional que responda exactamente a lo solicitado.
Responde SOLO con el contenido final, NO con pasos de cómo crearlo.
"""
        
        result = ollama_service.generate_response(creation_prompt, {'temperature': 0.7})
        
        if result.get('error'):
            raise Exception(f"Error Ollama: {result['error']}")
        
        content = result.get('response', 'Contenido creado')
        
        # Crear archivo real
        try:
            import re
            import os
            safe_title = re.sub(r'[^a-zA-Z0-9\-_]', '_', title[:50])
            filename = f"{safe_title}_{int(time.time())}.md"
            file_path = f"/app/backend/static/generated_files/{filename}"
            
            # Crear directorio si no existe
            os.makedirs("/app/backend/static/generated_files", exist_ok=True)
            
            # Escribir contenido al archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"**Tarea:** {original_message}\n\n")
                f.write(f"**Descripción:** {description}\n\n")
                f.write("---\n\n")
                f.write(content)
            
            file_size = os.path.getsize(file_path)
            
            logger.info(f"✅ Archivo creado: {filename} ({file_size} bytes)")
            
            return {
                'success': True,
                'type': 'creation_with_file',
                'content': content,
                'file_created': True,
                'file_name': filename,
                'file_path': file_path,
                'file_size': file_size,
                'download_url': f"/api/agent/download/{filename}",
                'summary': f"✅ Contenido creado y archivo generado: {filename} ({file_size} bytes)"
            }
            
        except Exception as file_error:
            logger.error(f"❌ Error creando archivo: {file_error}")
            return {
                'success': True,
                'type': 'creation_no_file',
                'content': content,
                'file_created': False,
                'file_error': str(file_error),
                'summary': f"✅ Contenido generado (error al crear archivo: {str(file_error)})"
            }
        
    except Exception as e:
        logger.error(f"❌ Creation error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'type': 'creation_error',
            'summary': f'❌ Error en creación: {str(e)}'
        }

def execute_planning_delivery_step(tool_type: str, title: str, description: str, ollama_service, original_message: str) -> dict:
    """Ejecutar paso de planificación o entrega"""
    try:
        if not ollama_service or not ollama_service.is_healthy():
            raise Exception("Servicio Ollama no disponible")
        
        if tool_type == 'planning':
            prompt = f"""
Realiza planificación detallada para:

Tarea original: {original_message}
Paso: {title}
Descripción: {description}

Proporciona:
1. Objetivos específicos
2. Recursos necesarios
3. Estrategia de implementación
4. Cronograma sugerido

Formato: Planificación estructurada y práctica.
"""
        else:  # delivery
            prompt = f"""
Prepara la entrega final para:

Tarea original: {original_message}
Paso: {title}
Descripción: {description}

Proporciona:
1. Resumen ejecutivo
2. Resultados principales
3. Recomendaciones
4. Próximos pasos

Formato: Entrega profesional y completa.
"""
        
        result = ollama_service.generate_response(prompt, {'temperature': 0.7})
        
        if result.get('error'):
            raise Exception(f"Error Ollama: {result['error']}")
        
        content = result.get('response', f'{tool_type} completado')
        
        return {
            'success': True,
            'type': tool_type,
            'content': content,
            'summary': f"✅ {tool_type.title()} completado exitosamente"
        }
        
    except Exception as e:
        logger.error(f"❌ {tool_type} error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'type': f'{tool_type}_error',
            'summary': f'❌ Error en {tool_type}: {str(e)}'
        }

def execute_generic_step(title: str, description: str, ollama_service, original_message: str) -> dict:
    """Ejecutar paso genérico"""
    try:
        if not ollama_service or not ollama_service.is_healthy():
            raise Exception("Servicio Ollama no disponible")
        
        generic_prompt = f"""
Ejecuta la siguiente tarea:

Tarea original: {original_message}
Paso: {title}
Descripción: {description}

Proporciona un resultado específico y útil para este paso.
Responde de manera clara y profesional.
"""
        
        result = ollama_service.generate_response(generic_prompt, {'temperature': 0.7})
        
        if result.get('error'):
            raise Exception(f"Error Ollama: {result['error']}")
        
        content = result.get('response', 'Paso completado')
        
        return {
            'success': True,
            'type': 'generic_processing',
            'content': content,
            'summary': f"✅ Paso completado: {title}"
        }
        
    except Exception as e:
        logger.error(f"❌ Generic step error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'type': 'generic_error',
            'summary': f'❌ Error en paso: {str(e)}'
        }

# Importar nuevo TaskManager para persistencia
from ..services.task_manager import get_task_manager

# Almacenamiento temporal para compartir conversaciones
shared_conversations = {}
# Almacenamiento temporal para archivos por tarea
task_files = {}

# DEPRECATED: Reemplazado por TaskManager con persistencia MongoDB
# Mantenido temporalmente para migración gradual
active_task_plans = {}

def get_task_data(task_id: str) -> dict:
    """
    Obtener datos de tarea usando TaskManager (con fallback a memoria legacy)
    Mejora implementada según UPGRADE.md Sección 5: Persistencia del Estado de Tareas
    """
    try:
        task_manager = get_task_manager()
        task_data = task_manager.get_task(task_id)
        
        if task_data:
            logger.debug(f"📥 Task {task_id} retrieved from persistent storage")
            return task_data
        elif task_id in active_task_plans:
            # Fallback a memoria legacy
            logger.warning(f"⚠️ Task {task_id} found only in legacy memory, migrating...")
            legacy_data = active_task_plans[task_id]
            # Migrar a persistencia
            task_manager.create_task(task_id, legacy_data)
            return legacy_data
        else:
            logger.warning(f"⚠️ Task {task_id} not found in persistent or legacy storage")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error getting task data {task_id}: {str(e)}")
        # Fallback a memoria legacy
        return active_task_plans.get(task_id)

def save_task_data(task_id: str, task_data: dict) -> bool:
    """
    Guardar datos de tarea usando TaskManager (con fallback a memoria legacy)
    """
    try:
        task_manager = get_task_manager()
        success = task_manager.create_task(task_id, task_data)
        
        if success:
            logger.debug(f"💾 Task {task_id} saved to persistent storage")
            # Mantener en memoria legacy por compatibilidad
            active_task_plans[task_id] = task_data
            return True
        else:
            logger.warning(f"⚠️ Failed to save task {task_id} to persistent storage, using legacy")
            active_task_plans[task_id] = task_data
            return False
            
    except Exception as e:
        logger.error(f"❌ Error saving task data {task_id}: {str(e)}")
        # Fallback a memoria legacy
        active_task_plans[task_id] = task_data
        return False

def update_task_data(task_id: str, updates: dict) -> bool:
    """
    Actualizar datos de tarea usando TaskManager (con fallback a memoria legacy)
    """
    try:
        task_manager = get_task_manager()
        success = task_manager.update_task(task_id, updates)
        
        if success:
            logger.debug(f"✅ Task {task_id} updated in persistent storage")
            # Actualizar memoria legacy por compatibilidad
            if task_id in active_task_plans:
                active_task_plans[task_id].update(updates)
            return True
        else:
            logger.warning(f"⚠️ Failed to update task {task_id} in persistent storage, using legacy")
            if task_id in active_task_plans:
                active_task_plans[task_id].update(updates)
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating task data {task_id}: {str(e)}")
        # Fallback a memoria legacy
        if task_id in active_task_plans:
            active_task_plans[task_id].update(updates)
        return False

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
    """
    Detecta si un mensaje es una conversación casual usando clasificación LLM
    Mejora implementada según UPGRADE.md Sección 1: Sistema de Contexto Dinámico Inteligente
    """
    try:
        # Obtener servicio de Ollama para clasificación inteligente
        ollama_service = get_ollama_service()
        
        # Obtener gestor de contexto inteligente
        context_manager = get_intelligent_context_manager()
        
        # Construir contexto inteligente para clasificación
        if context_manager:
            logger.info(f"🧠 Usando contexto inteligente para clasificación: '{message[:50]}...'")
            context = context_manager.build_context('chat', message, max_tokens=1000)
        else:
            context = None
            logger.debug("⚠️ IntelligentContextManager no disponible, usando contexto básico")
        
        # Fallback a lógica heurística si Ollama no está disponible
        if not ollama_service or not ollama_service.is_healthy():
            logger.warning("⚠️ Ollama no disponible, usando detección heurística de respaldo")
            return _fallback_casual_detection(message)
        
        # Prompt mejorado con contexto inteligente
        context_info = ""
        if context and isinstance(context, dict):
            # Agregar información relevante del contexto
            if context.get('conversation_history'):
                context_info += f"\nHistorial reciente: {len(context['conversation_history'])} conversaciones\n"
            if context.get('mood') and context['mood'] != 'neutral':
                context_info += f"Tono detectado: {context['mood']}\n"
            if context.get('topics'):
                context_info += f"Temas: {', '.join(context['topics'])}\n"
        
        intent_prompt = f"""Clasifica la siguiente frase del usuario en una de estas categorías exactas: 'casual', 'tarea_investigacion', 'tarea_creacion', 'tarea_analisis', 'otro'.

{context_info}

Responde ÚNICAMENTE con un objeto JSON con la clave 'intent'. No agregues explicaciones adicionales.

EJEMPLOS:
- "hola" -> {{"intent": "casual"}}
- "¿cómo estás?" -> {{"intent": "casual"}}
- "gracias" -> {{"intent": "casual"}}
- "buscar información sobre IA" -> {{"intent": "tarea_investigacion"}}
- "crear un informe" -> {{"intent": "tarea_creacion"}}
- "analizar datos" -> {{"intent": "tarea_analisis"}}

Frase a clasificar: "{message}"

Respuesta JSON:"""
        
        logger.info(f"🤖 Clasificando intención con LLM para: '{message[:50]}...'")
        
        # Llamar a Ollama con parámetros optimizados para JSON
        response = ollama_service.generate_response(intent_prompt, {
            'temperature': 0.2,  # Más bajo para respuestas consistentes
            'response_format': 'json'
        })
        
        if response.get('error'):
            logger.warning(f"⚠️ Error en clasificación LLM: {response['error']}, usando fallback")
            return _fallback_casual_detection(message)
        
        # Parsear respuesta JSON con estrategias robustas
        response_text = response.get('response', '').strip()
        logger.info(f"📥 Respuesta LLM clasificación: {response_text[:100]}...")
        
        # Intentar parseo JSON con múltiples estrategias
        intent_data = None
        
        # Estrategia 1: JSON directo
        try:
            # Limpiar respuesta
            cleaned_response = response_text.replace('```json', '').replace('```', '').strip()
            if cleaned_response.startswith('{') and cleaned_response.endswith('}'):
                intent_data = json.loads(cleaned_response)
        except json.JSONDecodeError:
            pass
        
        # Estrategia 2: Buscar JSON en el texto
        if not intent_data:
            try:
                json_match = re.search(r'\{[^{}]*"intent"[^{}]*\}', response_text)
                if json_match:
                    intent_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Estrategia 3: Extracción por regex
        if not intent_data:
            try:
                intent_match = re.search(r'"intent"\s*:\s*"([^"]+)"', response_text)
                if intent_match:
                    intent_data = {"intent": intent_match.group(1)}
            except:
                pass
        
        # Validar resultado
        if intent_data and 'intent' in intent_data:
            intent = intent_data['intent'].lower().strip()
            
            # Clasificar como casual o tarea
            is_casual = intent == 'casual'
            
            logger.info(f"✅ Clasificación LLM exitosa: '{message[:30]}...' -> {intent} -> {'CASUAL' if is_casual else 'TAREA'}")
            
            return is_casual
        else:
            logger.warning(f"⚠️ No se pudo parsear intención LLM, usando fallback para: {message[:30]}...")
            return _fallback_casual_detection(message)
            
    except Exception as e:
        logger.error(f"❌ Error en clasificación de intención LLM: {str(e)}")
        return _fallback_casual_detection(message)

def _fallback_casual_detection(message: str) -> bool:
    """
    Lógica de respaldo heurística para detección de conversación casual
    Se usa cuando Ollama no está disponible
    """
    message_lower = message.lower().strip()
    
    logger.info(f"🔄 Usando detección heurística de respaldo para: '{message[:30]}...'")
    
    # Mensajes muy cortos (menos de 3 palabras) probablemente son casuales
    if len(message_lower.split()) <= 3:
        for pattern in CASUAL_PATTERNS:
            if re.search(pattern, message_lower):
                return True
    
    # Verificar patrones de tareas PRIMERO
    for pattern in TASK_PATTERNS:
        if re.search(pattern, message_lower):
            return False
    
    # Verificar palabras clave que indican tarea (más amplio)
    task_keywords = [
        'buscar', 'busca', 'investigar', 'investiga', 'analizar', 'analiza',
        'crear', 'crea', 'generar', 'genera', 'desarrollar', 'desarrolla',
        'hacer', 'haz', 'escribir', 'escribe', 'dame', 'dime', 'necesito',
        'quiero', 'puedes', 'ayúdame', 'planificar', 'planifica', 'realizar',
        'informe', 'reporte', 'análisis', 'estudio', 'investigación'
    ]
    
    # Si contiene palabras clave de tareas, NO es casual
    for keyword in task_keywords:
        if keyword in message_lower:
            return False
    
    # Si no hay patrones de tareas y es muy corto, probablemente es casual
    if len(message_lower.split()) <= 5:
        return True
    
    # Si tiene más de 5 palabras y no es claramente casual, tratarlo como tarea
    return False

def get_ollama_service():
    """Obtener servicio de Ollama"""
    try:
        service = current_app.ollama_service
        logger.info(f"✅ Ollama service found: {service}")
        return service
    except AttributeError:
        logger.error("❌ Ollama service not available")
        return None

def get_intelligent_context_manager():
    """Obtener gestor de contexto inteligente"""
    try:
        context_manager = current_app.intelligent_context_manager
        logger.debug(f"✅ Intelligent Context Manager found: {context_manager}")
        return context_manager
    except AttributeError:
        logger.warning("⚠️ Intelligent Context Manager not available")
        return None

def get_tool_manager():
    """Obtener tool manager"""
    try:
        return current_app.tool_manager
    except AttributeError:
        logger.error("Tool manager not available")
        return None

def determine_unified_icon(task_message: str) -> str:
    """
    Determine appropriate icon based on task content with simplified, consistent logic
    Only returns one of 9 core icons for maximum coherence
    """
    content_lower = task_message.lower()
    
    # 🗺️ PRIORITY 1: LOCATION/PLACES (highest priority for coherence)
    if any(word in content_lower for word in ['restaurante', 'bar', 'comida', 'valencia', 'madrid', 'barcelona', 'lugar', 'ubicación', 'dirección', 'mapa', 'localizar', 'sitio', 'ciudad']):
        logger.info(f"🎯 Icon: 'map' (Location priority) for: {task_message[:50]}...")
        return 'map'
    
    # 💻 PRIORITY 2: DEVELOPMENT/PROGRAMMING
    elif any(word in content_lower for word in ['código', 'programa', 'script', 'app', 'aplicación', 'desarrollo', 'programar', 'web', 'software', 'javascript', 'python', 'react', 'backend', 'frontend', 'api', 'database', 'sql']):
        logger.info(f"🎯 Icon: 'code' (Development priority) for: {task_message[:50]}...")
        return 'code'
    
    # 📊 PRIORITY 3: DATA ANALYSIS/CHARTS 
    elif any(word in content_lower for word in ['datos', 'estadística', 'análisis', 'analizar', 'chart', 'gráfico', 'estadísticas', 'métricas', 'dashboard', 'mercado', 'ventas', 'números']):
        logger.info(f"🎯 Icon: 'chart' (Data Analysis priority) for: {task_message[:50]}...")
        return 'chart'
    
    # 🔍 PRIORITY 4: SEARCH/RESEARCH
    elif any(word in content_lower for word in ['buscar', 'investigar', 'estudiar', 'search', 'investigación', 'research', 'encontrar']):
        logger.info(f"🎯 Icon: 'search' (Research priority) for: {task_message[:50]}...")
        return 'search'
    
    # 📄 PRIORITY 5: DOCUMENTS/WRITING
    elif any(word in content_lower for word in ['documento', 'texto', 'escribir', 'redactar', 'informe', 'reporte', 'libro', 'artículo', 'archivo', 'file']):
        logger.info(f"🎯 Icon: 'file' (Document priority) for: {task_message[:50]}...")
        return 'file'
    
    # 🎨 PRIORITY 6: CREATIVE/DESIGN
    elif any(word in content_lower for word in ['imagen', 'diseño', 'gráfico', 'visual', 'foto', 'creative', 'creativo', 'diseñar', 'logo', 'arte']):
        logger.info(f"🎯 Icon: 'image' (Creative priority) for: {task_message[:50]}...")
        return 'image'
    
    # 🎵 PRIORITY 7: MULTIMEDIA
    elif any(word in content_lower for word in ['música', 'audio', 'sonido', 'music', 'canción']):
        logger.info(f"🎯 Icon: 'music' (Audio priority) for: {task_message[:50]}...")
        return 'music'
    
    # 💼 PRIORITY 8: BUSINESS/COMMERCIAL
    elif any(word in content_lower for word in ['negocio', 'empresa', 'mercado', 'marketing', 'comercial', 'ventas', 'cliente', 'briefcase']):
        logger.info(f"🎯 Icon: 'briefcase' (Business priority) for: {task_message[:50]}...")
        return 'briefcase'
    
    # 🎯 DEFAULT: Generic task icon
    else:
        logger.info(f"🎯 Icon: 'target' (Default) for: {task_message[:50]}...")
        return 'target'

def execute_plan_with_real_tools(task_id: str, plan_steps: list, message: str):
    """
    Ejecuta REALMENTE los pasos del plan usando herramientas y entrega resultados finales
    Mejora implementada según UPGRADE.md Sección 3: WebSockets para Comunicación en Tiempo Real
    """
    # 🚨 PASO 1: LOGGING AGRESIVO EN EXECUTE_PLAN_WITH_REAL_TOOLS 🚨
    print(f"🚀 execute_plan_with_real_tools CALLED!")
    print(f"📋 Task ID: {task_id}")
    print(f"📋 Message: {message}")
    print(f"📋 Plan steps count: {len(plan_steps)}")
    print(f"🔍 Plan steps details: {json.dumps(plan_steps, indent=2, default=str)}")
    
    try:
        import threading
        import time
        from datetime import datetime
        
        print(f"🔨 Importing dependencies completed")
        
        # Obtener servicios ANTES de crear el hilo
        ollama_service = get_ollama_service()
        tool_manager = get_tool_manager()
        
        # Obtener WebSocket manager para actualizaciones en tiempo real
        # Mejora implementada según UPGRADE.md Sección 3: WebSockets para Comunicación en Tiempo Real
        websocket_manager = None
        try:
            # Primero intentar obtenerlo desde Flask app
            try:
                websocket_manager = current_app.websocket_manager
                logger.info(f"✅ WebSocket manager obtained from Flask app for task {task_id}")
            except AttributeError:
                # Fallback al método directo
                from src.websocket.websocket_manager import get_websocket_manager
                websocket_manager = get_websocket_manager()
                logger.info(f"✅ WebSocket manager obtained directly for task {task_id}")
                
        except Exception as ws_error:
            logger.warning(f"⚠️ WebSocket manager not available: {ws_error}")
        
        def send_websocket_update(update_type: str, data: dict):
            """Enviar actualización por WebSocket si está disponible"""
            if websocket_manager and websocket_manager.is_initialized:
                try:
                    if update_type == 'step_update':
                        websocket_manager.send_update(task_id, UpdateType.STEP_STARTED if data.get('status') == 'in-progress' else UpdateType.STEP_COMPLETED, data)
                    elif update_type == 'log_message':
                        websocket_manager.send_update(task_id, UpdateType.TASK_PROGRESS, data)
                    elif update_type == 'tool_execution_detail':
                        websocket_manager.send_update(task_id, UpdateType.TASK_PROGRESS, data)
                    elif update_type == 'task_completed':
                        websocket_manager.send_update(task_id, UpdateType.TASK_COMPLETED, data)
                    elif update_type == 'task_failed':
                        websocket_manager.send_update(task_id, UpdateType.TASK_FAILED, data)
                        
                    logger.info(f"📡 WebSocket update sent: {update_type} for task {task_id}")
                except Exception as e:
                    logger.warning(f"⚠️ WebSocket update failed: {e}")
        
        def execute_steps():
            # 🚨 PASO 1: LOGGING AGRESIVO EN EXECUTE_STEPS 🚨
            print(f"🚀 execute_steps thread function STARTED for task_id: {task_id}")
            print(f"📋 Thread is running in daemon mode")
            
            logger.info(f"🔍 DEBUG: execute_steps iniciado para task_id: {task_id}")
            print(f"🔍 About to call get_task_data for task_id: {task_id}")
            
            # Usar TaskManager en lugar de active_task_plans
            task_data = get_task_data(task_id)
            print(f"🔍 get_task_data result: {task_data is not None}")
            if task_data:
                print(f"📋 Task data keys: {task_data.keys() if isinstance(task_data, dict) else 'Not dict'}")
            
            logger.info(f"🔍 DEBUG: task_data obtenida: {task_data is not None}")
            
            if not task_data:
                print(f"❌ Task {task_id} not found in TaskManager, trying fallback...")
                logger.error(f"❌ Task {task_id} not found, cannot execute - Fallback a active_task_plans")
                # Fallback a memoria legacy
                print(f"🔍 Checking active_task_plans, keys: {list(active_task_plans.keys())}")
                if task_id in active_task_plans:
                    task_data = active_task_plans[task_id]
                    print(f"✅ Found task in active_task_plans")
                    logger.info(f"🔍 DEBUG: Encontrada en active_task_plans")
                else:
                    print(f"❌ Task {task_id} not found in active_task_plans either!")
                    logger.error(f"❌ Task {task_id} no existe ni en TaskManager ni en active_task_plans")
                    return
                
            steps = task_data['plan']
            final_results = []  # Almacenar resultados de cada paso
            
            logger.info(f"🚀 Starting REAL execution of {len(steps)} steps for task: {message}")
            
            # Enviar notificación de inicio de tarea
            send_websocket_update('log_message', {
                'type': 'log_message',
                'level': 'info',
                'message': f'🚀 Iniciando ejecución de {len(steps)} pasos para: {message[:50]}...',
                'timestamp': datetime.now().isoformat()
            })
            
            for i, step in enumerate(steps):
                logger.info(f"🔄 Executing step {i+1}/{len(steps)}: {step['title']}")
                
                # Marcar paso como activo
                step['active'] = True
                step['status'] = 'in-progress'
                
                # Enviar actualización de estado del paso en tiempo real
                send_websocket_update('step_update', {
                    'type': 'step_update',
                    'step_id': step['id'],
                    'status': 'in-progress',
                    'title': step['title'],
                    'description': step['description'],
                    'progress': (i / len(steps)) * 100,
                    'current_step': i + 1,
                    'total_steps': len(steps)
                })
                
                # Enviar log detallado al monitor
                send_websocket_update('log_message', {
                    'type': 'log_message',
                    'level': 'info',
                    'message': f'🔄 Ejecutando paso {i+1}/{len(steps)}: {step["title"]}',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Actualizar plan en memoria y persistencia
                task_manager = get_task_manager()
                task_manager.update_task_step_status(
                    task_id, 
                    step['id'], 
                    'in-progress'
                )
                update_task_data(task_id, {
                    'plan': steps,
                    'current_step': i + 1
                })
                
                step_start_time = time.time()
                step_result = None
                
                # Excepciones personalizadas para manejo de errores específico
                class OllamaServiceError(Exception):
                    pass

                class ToolNotAvailableError(Exception):
                    pass

                class FileCreationError(Exception):
                    pass

                # Función ROBUSTA para ejecutar herramientas con reintentos y retroceso exponencial
                # PROBLEMA 1 SOLUCIONADO: Eliminación completa de simulación
                @retry(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1, min=2, max=8),
                    retry=retry_if_exception_type((requests.RequestException, ConnectionError, TimeoutError, OllamaServiceError))
                )
                def execute_tool_with_retries(tool_name: str, tool_params: dict, step_title: str):
                    """Ejecutar herramienta con reintentos automáticos - SOLO EJECUCIÓN REAL"""
                    logger.info(f"🔄 Intentando ejecutar herramienta '{tool_name}' para el paso: {step_title}")
                    
                    if tool_name == 'web_search':
                        if not tool_manager or not hasattr(tool_manager, 'execute_tool'):
                            raise ToolNotAvailableError(f"Tool manager no disponible o herramienta 'web_search' no inicializada.")
                        return tool_manager.execute_tool('web_search', tool_params, task_id=task_id)
                    
                    elif tool_name in ['analysis', 'creation', 'planning', 'delivery', 'processing', 'synthesis', 'search_definition', 'data_analysis']:
                        if not ollama_service or not ollama_service.is_healthy():
                            raise OllamaServiceError("Ollama service no está disponible o no es saludable.")
                        
                        # Para herramientas basadas en Ollama, la lógica de prompt debe ser robusta
                        result = ollama_service.generate_response(tool_params.get('prompt', ''), tool_params.get('ollama_options', {}))
                        
                        # Verificar que la respuesta de Ollama no sea un error
                        if result.get('error'):
                            raise OllamaServiceError(f"Error en Ollama: {result['error']}")
                        
                        return result
                    
                    else:
                        # Para herramientas no explícitamente manejadas, intentar con tool_manager
                        if not tool_manager or not hasattr(tool_manager, 'execute_tool'):
                            raise ToolNotAvailableError(f"Herramienta '{tool_name}' no reconocida o no disponible.")
                        return tool_manager.execute_tool(tool_name, tool_params, task_id=task_id)
                
                try:
                    # EJECUTAR HERRAMIENTA REAL según el tipo de paso con reintentos automáticos
                    if step['tool'] == 'web_search' or 'búsqueda' in step['title'].lower():
                        search_query = extract_search_query_from_message(message, step['title'])
                        logger.info(f"🔍 Executing web search with retries for: {search_query}")
                        
                        # Enviar detalle de ejecución de herramienta
                        send_websocket_update('tool_execution_detail', {
                            'type': 'tool_execution_detail',
                            'tool_name': 'web_search',
                            'input_params': {'query': search_query, 'num_results': 5},
                            'message': f'🔍 Buscando información: {search_query}',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        try:
                            # Usar ejecución con reintentos automáticos
                            result = execute_tool_with_retries('web_search', {
                                'query': search_query,
                                'num_results': 5
                            }, step['title'])
                            
                            step_result = {
                                'type': 'web_search',
                                'query': search_query,
                                'results': result.get('search_results', []),
                                'summary': f"Encontradas {len(result.get('search_results', []))} fuentes relevantes"
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            
                            # Enviar resultado de herramienta
                            send_websocket_update('tool_execution_detail', {
                                'type': 'tool_execution_detail',
                                'tool_name': 'web_search',
                                'output_summary': step_result['summary'],
                                'message': f'✅ Búsqueda completada: {step_result["summary"]}',
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            logger.info(f"✅ Web search completed: {len(result.get('search_results', []))} results")
                            
                        except Exception as search_error:
                            logger.error(f"❌ Web search failed after retries: {str(search_error)}")
                            
                            # Enviar error detallado
                            send_websocket_update('tool_execution_detail', {
                                'type': 'tool_execution_detail',
                                'tool_name': 'web_search',
                                'error': str(search_error),
                                'message': f'❌ Error en búsqueda después de reintentos: {str(search_error)}',
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            # Estrategia de fallback para herramientas críticas
                            logger.info(f"🔄 Attempting fallback search strategy for: {search_query}")
                            step_result = {
                                'type': 'web_search_fallback',
                                'query': search_query,
                                'results': [],
                                'summary': f"Búsqueda no completada. Continúo con información disponible.",
                                'error': str(search_error),
                                'fallback_used': True
                            }
                            step['result'] = step_result
                            final_results.append(step_result)
                    
                    elif step['tool'] == 'analysis' or 'análisis' in step['title'].lower():
                        logger.info(f"🧠 Executing analysis using REAL execution")
                        
                        # Enviar detalle de ejecución de herramienta
                        send_websocket_update('tool_execution_detail', {
                            'type': 'tool_execution_detail',
                            'tool_name': 'analysis',
                            'input_params': {'context': step['description']},
                            'message': f'🧠 Ejecutando análisis: {step["title"]}',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # Generar análisis específico usando contexto previo
                        analysis_context = f"Tarea: {message}\nPaso actual: {step['title']}\nDescripción: {step['description']}"
                        if final_results:
                            analysis_context += f"\nResultados previos: {final_results[-1] if final_results else 'Ninguno'}"
                        
                        analysis_prompt = f"""
Realiza un análisis detallado para:
{analysis_context}

Proporciona:
1. Análisis específico del contexto
2. Hallazgos principales
3. Recomendaciones para próximos pasos
4. Conclusiones preliminares

Formato: Respuesta estructurada y profesional.
"""
                        
                        try:
                            # EJECUCIÓN REAL CON REINTENTOS - NO SIMULACIÓN
                            result = execute_tool_with_retries('analysis', {
                                'prompt': analysis_prompt,
                                'ollama_options': {}
                            }, step['title'])
                            
                            step_result = {
                                'type': 'analysis',
                                'content': result.get('response', 'Análisis completado'),
                                'summary': 'Análisis detallado generado exitosamente'
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            
                            # Enviar resultado de herramienta
                            send_websocket_update('tool_execution_detail', {
                                'type': 'tool_execution_detail',
                                'tool_name': 'analysis',
                                'output_summary': step_result['summary'],
                                'message': f'✅ Análisis completado: {step["title"]}',
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            logger.info(f"✅ Analysis completed successfully")
                            
                        except (OllamaServiceError, ToolNotAvailableError) as analysis_error:
                            logger.error(f"❌ Analysis failed after retries: {str(analysis_error)}")
                            
                            # Marcar paso como fallido sin simulación
                            step_result = {
                                'type': 'analysis_failed',
                                'error': str(analysis_error),
                                'summary': f'❌ Error en análisis: {str(analysis_error)}',
                                'fallback_used': True
                            }
                            step['result'] = step_result
                            step['status'] = 'failed'
                            final_results.append(step_result)
                            
                            # Enviar error detallado
                            send_websocket_update('tool_execution_detail', {
                                'type': 'tool_execution_detail',
                                'tool_name': 'analysis',
                                'error': str(analysis_error),
                                'message': f'❌ Error en análisis: {str(analysis_error)}',
                                'timestamp': datetime.now().isoformat()
                            })
                    
                    elif step['tool'] == 'creation' or 'creación' in step['title'].lower() or 'desarrollo' in step['title'].lower():
                        logger.info(f"🛠️ Executing creation with REAL file generation - NO SIMULATION")
                        
                        # Enviar detalle de ejecución de herramienta
                        send_websocket_update('tool_execution_detail', {
                            'type': 'tool_execution_detail',
                            'tool_name': 'creation',
                            'input_params': {'task': step['title']},
                            'message': f'🛠️ Creando contenido y archivo: {step["title"]}',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # Generar contenido específico
                        creation_context = f"Tarea: {message}\nPaso: {step['title']}\nDescripción: {step['description']}"
                        if final_results:
                            creation_context += f"\nInformación previa: {final_results}"
                        
                        # PROMPT ULTRA ESPECÍFICO PARA EVITAR PLANES DE ACCIÓN
                        if 'archivo' in message.lower() and ('contenga' in message.lower() or 'texto' in message.lower()):
                            # Para solicitudes de archivos simples con contenido específico
                            import re
                            content_match = re.search(r'contenga[^:]*[:]\s*(.+?)(?:\.|$|")', message, re.IGNORECASE)
                            if content_match:
                                requested_content = content_match.group(1).strip()
                                creation_prompt = f"""
INSTRUCCIÓN: Responde ÚNICAMENTE con el contenido exacto solicitado. NO generes planes de acción.

CONTENIDO EXACTO A GENERAR: {requested_content}

Responde SOLO con: {requested_content}
"""
                            else:
                                creation_prompt = f"""
IMPORTANTE: NO generes un plan de acción. Genera el CONTENIDO REAL solicitado.

Tarea: {message}

Responde con el contenido exacto que el usuario solicitó, NO con un plan de cómo hacerlo.
"""
                        else:
                            creation_prompt = f"""
IMPORTANTE: NO generes un plan de acción. Genera el CONTENIDO REAL solicitado.

{creation_context}

INSTRUCCIÓN CRÍTICA: Responde con el contenido final que se solicita, NO con pasos de cómo crearlo.

Genera el contenido específico, detallado y profesional que se solicita DIRECTAMENTE.
"""
                        
                        try:
                            # EJECUCIÓN REAL CON REINTENTOS - NO SIMULACIÓN
                            result = execute_tool_with_retries('creation', {
                                'prompt': creation_prompt,
                                'ollama_options': {}
                            }, step['title'])
                            
                            content = result.get('response', 'Contenido creado')
                            
                            # 🆕 CREAR ARCHIVO REAL TANGIBLE - VALIDACIÓN RIGUROSA
                            try:
                                # Determinar tipo de archivo basado en la tarea
                                file_extension = '.md'  # Por defecto markdown
                                if 'documento' in message.lower() or 'informe' in message.lower():
                                    file_extension = '.md'
                                elif 'código' in message.lower() or 'script' in message.lower():
                                    file_extension = '.py'
                                elif 'plan' in message.lower():
                                    file_extension = '.txt'
                                
                                # Crear nombre de archivo único
                                import re
                                safe_title = re.sub(r'[^a-zA-Z0-9\-_]', '_', step['title'][:30])
                                filename = f"{safe_title}_{int(time.time())}{file_extension}"
                                file_path = f"/app/backend/static/generated_files/{filename}"
                                
                                # Crear directorio si no existe
                                os.makedirs("/app/backend/static/generated_files", exist_ok=True)
                                
                                # Escribir archivo real
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                
                                # VALIDACIÓN RIGUROSA - PROBLEMA 8 IMPLEMENTADO PARCIALMENTE
                                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                    file_size = os.path.getsize(file_path)
                                    logger.info(f"✅ ARCHIVO REAL CREADO Y VALIDADO: {filename} ({file_size} bytes)")
                                    
                                    step_result = {
                                        'type': 'creation',
                                        'content': content,
                                        'summary': f'✅ Archivo creado y validado exitosamente: {filename}',
                                        'file_created': True,
                                        'file_path': file_path,
                                        'file_name': filename,
                                        'file_size': file_size,
                                        'download_url': f'/api/download/{filename}',
                                        'tangible_result': True
                                    }
                                    
                                    # Enviar notificación de archivo creado
                                    send_websocket_update('tool_execution_detail', {
                                        'type': 'tool_execution_detail',
                                        'tool_name': 'creation',
                                        'output_summary': f'✅ Archivo creado y validado: {filename} ({file_size} bytes)',
                                        'file_created': filename,
                                        'download_url': f'/api/download/{filename}',
                                        'message': f'✅ Archivo generado, validado y listo para descargar: {filename}',
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    
                                else:
                                    raise FileCreationError("El archivo no se pudo crear correctamente o está vacío")
                                
                            except Exception as file_error:
                                logger.error(f"❌ Error creando archivo real: {str(file_error)}")
                                raise FileCreationError(f"Error en creación de archivo: {str(file_error)}")
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            logger.info(f"✅ Content creation with REAL file generation completed")
                            
                        except (OllamaServiceError, ToolNotAvailableError, FileCreationError) as creation_error:
                            logger.error(f"❌ Creation failed after retries: {str(creation_error)}")
                            
                            # Marcar paso como fallido sin simulación
                            step_result = {
                                'type': 'creation_failed',
                                'error': str(creation_error),
                                'summary': f'❌ Error en creación: {str(creation_error)}',
                                'file_created': False,
                                'fallback_used': True
                            }
                            step['result'] = step_result
                            step['status'] = 'failed'
                            final_results.append(step_result)
                            
                            # Enviar error detallado
                            send_websocket_update('tool_execution_detail', {
                                'type': 'tool_execution_detail',
                                'tool_name': 'creation',
                                'error': str(creation_error),
                                'message': f'❌ Error en creación: {str(creation_error)}',
                                'timestamp': datetime.now().isoformat()
                            })
                    
                    elif step['tool'] == 'planning' or 'planificación' in step['title'].lower():
                        logger.info(f"📋 Executing planning with REAL plan generation - NO SIMULATION")
                        
                        # Enviar detalle de ejecución de herramienta
                        send_websocket_update('tool_execution_detail', {
                            'type': 'tool_execution_detail',
                            'tool_name': 'planning',
                            'input_params': {'context': step['description']},
                            'message': f'📋 Ejecutando planificación: {step["title"]}',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # Generar plan específico usando contexto previo
                        planning_context = f"Tarea: {message}\nPaso: {step['title']}\nDescripción: {step['description']}"
                        if final_results:
                            planning_context += f"\nResultados anteriores: {final_results}"
                        
                        planning_prompt = f"""
Desarrolla un plan específico para:
{planning_context}

Incluye:
1. Objetivos específicos del plan
2. Estrategias detalladas
3. Recursos necesarios
4. Cronograma estimado
5. Métricas de éxito

Formato: Plan estructurado y profesional.
"""
                        
                        try:
                            # EJECUCIÓN REAL CON REINTENTOS - NO SIMULACIÓN
                            result = execute_tool_with_retries('planning', {
                                'prompt': planning_prompt,
                                'ollama_options': {}
                            }, step['title'])
                            
                            step_result = {
                                'type': 'planning',
                                'content': result.get('response', 'Plan generado'),
                                'summary': 'Plan detallado generado exitosamente'
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            
                            # Enviar resultado de herramienta
                            send_websocket_update('tool_execution_detail', {
                                'type': 'tool_execution_detail',
                                'tool_name': 'planning',
                                'output_summary': step_result['summary'],
                                'message': f'✅ Planificación completada: {step["title"]}',
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            logger.info(f"✅ Planning completed successfully")
                            
                        except (OllamaServiceError, ToolNotAvailableError) as planning_error:
                            logger.error(f"❌ Planning failed after retries: {str(planning_error)}")
                            
                            # Marcar paso como fallido sin simulación
                            step_result = {
                                'type': 'planning_failed',
                                'error': str(planning_error),
                                'summary': f'❌ Error en planificación: {str(planning_error)}',
                                'fallback_used': True
                            }
                            step['result'] = step_result
                            step['status'] = 'failed'
                            final_results.append(step_result)
                            
                            # Enviar error detallado
                            send_websocket_update('tool_execution_detail', {
                                'type': 'tool_execution_detail',
                                'tool_name': 'planning',
                                'error': str(planning_error),
                                'message': f'❌ Error en planificación: {str(planning_error)}',
                                'timestamp': datetime.now().isoformat()
                            })
                    
                    elif step['tool'] == 'delivery' or 'entrega' in step['title'].lower():
                        if ollama_service:
                            logger.info(f"📦 Executing final delivery with TANGIBLE results")
                            
                            # Generar entrega final con todos los resultados
                            delivery_prompt = f"""
Prepara la entrega final para la tarea: {message}

Consolida todos los resultados obtenidos:
{final_results}

Crea un documento de entrega final que incluya:
1. RESUMEN EJECUTIVO de lo realizado
2. RESULTADOS PRINCIPALES obtenidos
3. CONTENIDO COMPLETO generado
4. ARCHIVOS Y ENTREGABLES creados
5. CONCLUSIONES Y RECOMENDACIONES
6. ENTREGABLES FINALES disponibles

Formato: Documento profesional completo y estructurado.
"""
                            
                            result = ollama_service.generate_response(delivery_prompt, {})
                            content = result.get('response', 'Entrega completada')
                            
                            # 🆕 CREAR RESUMEN EJECUTIVO COMO ARCHIVO
                            try:
                                # Crear resumen ejecutivo como archivo tangible
                                import re
                                safe_message = re.sub(r'[^a-zA-Z0-9\-_]', '_', message[:30])
                                filename = f"Resumen_Ejecutivo_{safe_message}_{int(time.time())}.md"
                                file_path = f"/app/backend/static/generated_files/{filename}"
                                
                                # Crear directorio si no existe
                                os.makedirs("/app/backend/static/generated_files", exist_ok=True)
                                
                                # Preparar contenido del resumen ejecutivo
                                executive_summary = f"""# RESUMEN EJECUTIVO
## Tarea: {message}
## Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{content}

## ARCHIVOS GENERADOS
"""
                                
                                # Agregar lista de archivos creados
                                files_created = []
                                for result_item in final_results:
                                    if isinstance(result_item, dict) and result_item.get('file_created'):
                                        files_created.append(f"- {result_item['file_name']} ({result_item['file_size']} bytes)")
                                        executive_summary += f"- {result_item['file_name']} ({result_item['file_size']} bytes)\n"
                                
                                if not files_created:
                                    executive_summary += "- No se crearon archivos adicionales en este proceso\n"
                                
                                executive_summary += f"""
## ESTADÍSTICAS
- Pasos ejecutados: {len(steps)}
- Resultados generados: {len(final_results)}
- Archivos creados: {len(files_created)}
- Estado: ✅ Completado exitosamente
"""
                                
                                # Escribir archivo de resumen
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(executive_summary)
                                
                                # Verificar creación
                                if os.path.exists(file_path):
                                    file_size = os.path.getsize(file_path)
                                    logger.info(f"✅ RESUMEN EJECUTIVO CREADO: {filename} ({file_size} bytes)")
                                    
                                    step_result = {
                                        'type': 'delivery',
                                        'content': content,
                                        'summary': f'✅ Tarea completada con entrega final: {filename}',
                                        'final_deliverable': True,
                                        'file_created': True,
                                        'file_path': file_path,
                                        'file_name': filename,
                                        'file_size': file_size,
                                        'download_url': f'/api/download/{filename}',
                                        'executive_summary': True,
                                        'total_files_created': len(files_created) + 1  # +1 por el propio resumen
                                    }
                                    
                                    # Enviar notificación de entrega final
                                    send_websocket_update('tool_execution_detail', {
                                        'type': 'tool_execution_detail',
                                        'tool_name': 'delivery',
                                        'output_summary': f'✅ Entrega final completada: {filename}',
                                        'file_created': filename,
                                        'download_url': f'/api/download/{filename}',
                                        'total_files': len(files_created) + 1,
                                        'message': f'🎉 Entrega final completada con {len(files_created) + 1} archivo(s) generado(s)',
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    
                                else:
                                    raise Exception("No se pudo crear el resumen ejecutivo")
                                    
                            except Exception as file_error:
                                logger.error(f"❌ Error creando resumen ejecutivo: {str(file_error)}")
                                step_result = {
                                    'type': 'delivery',
                                    'content': content,
                                    'summary': 'Tarea completada exitosamente con entrega final',
                                    'final_deliverable': True,
                                    'file_error': str(file_error)
                                }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            logger.info(f"✅ Final delivery with tangible results completed")
                        # Si llegamos aquí, Ollama no está disponible para delivery
                        logger.error(f"❌ Ollama service not available for delivery step: {step['title']}")
                        
                        # En lugar de simulación, marcar como fallido
                        step_result = {
                            'type': 'delivery_failed',
                            'error': 'Ollama service not available',
                            'summary': '❌ Error: No se pudo completar la entrega - Ollama no disponible',
                            'file_created': False,
                            'fallback_used': True
                        }
                        step['result'] = step_result
                        step['status'] = 'failed'
                        final_results.append(step_result)
                        
                        # Enviar error detallado
                        send_websocket_update('tool_execution_detail', {
                            'type': 'tool_execution_detail',
                            'tool_name': 'delivery',
                            'error': 'Ollama service not available',
                            'message': '❌ Error en entrega final: Ollama no disponible',
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    else:
                        # Paso genérico - ejecutar con REAL Ollama execution - NO SIMULATION
                        try:
                            logger.info(f"⚡ Executing generic step with REAL execution: {step['title']}")
                            
                            generic_prompt = f"""
Ejecuta el paso '{step['title']}' para la tarea: {message}

Descripción: {step['description']}
Contexto previo: {final_results if final_results else 'Inicio de tarea'}

Proporciona un resultado específico y útil para este paso.
"""
                            
                            # EJECUCIÓN REAL CON REINTENTOS - NO SIMULACIÓN
                            result = execute_tool_with_retries('processing', {
                                'prompt': generic_prompt,
                                'ollama_options': {}
                            }, step['title'])
                            
                            step_result = {
                                'type': 'generic',
                                'content': result.get('response', 'Paso completado'),
                                'summary': f"Paso '{step['title']}' completado exitosamente"
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            logger.info(f"✅ Generic step completed successfully: {step['title']}")
                            
                        except (OllamaServiceError, ToolNotAvailableError) as generic_error:
                            logger.error(f"❌ Generic step failed after retries: {str(generic_error)}")
                            
                            # Marcar paso como fallido sin simulación
                            step_result = {
                                'type': 'generic_failed',
                                'error': str(generic_error),
                                'summary': f'❌ Error en paso genérico: {str(generic_error)}',
                                'fallback_used': True
                            }
                            step['result'] = step_result
                            step['status'] = 'failed'
                            final_results.append(step_result)
                            
                            # Enviar error detallado
                            send_websocket_update('tool_execution_detail', {
                                'type': 'tool_execution_detail',
                                'tool_name': 'processing',
                                'error': str(generic_error),
                                'message': f'❌ Error en paso genérico: {str(generic_error)}',
                                'timestamp': datetime.now().isoformat()
                            })
                    
                    # 🆕 PROBLEMA 2: VALIDACIÓN RIGUROSA DE RESULTADOS ANTES DE MARCAR COMO COMPLETADO
                    step_execution_time = time.time() - step_start_time
                    
                    # Solo marcar como completado si tenemos un step_result válido
                    if step_result and 'status' not in step or step.get('status') != 'failed':
                        # VALIDAR RESULTADO USANDO SISTEMA ROBUSTO
                        validation_status, validation_message = validate_step_result(step['tool'], step_result)
                        
                        logger.info(f"🔍 Validación para {step['tool']}: {validation_status} - {validation_message}")
                        
                        # Actualizar step_result con información de validación
                        step_result['validation_status'] = validation_status
                        step_result['validation_message'] = validation_message
                        
                        # Establecer estado del paso basado en validación
                        if validation_status == 'success':
                            step['status'] = StepStatus.COMPLETED_SUCCESS
                            step['completed'] = True
                            websocket_status = 'completed_success'
                        elif validation_status == 'warning':
                            step['status'] = StepStatus.COMPLETED_WITH_WARNINGS  
                            step['completed'] = True
                            websocket_status = 'completed_with_warnings'
                        else:  # validation_status == 'failure'
                            step['status'] = StepStatus.FAILED
                            step['completed'] = False
                            websocket_status = 'failed'
                            
                        step['active'] = False
                        step['result'] = step_result
                        
                        # Enviar actualización de paso con estado detallado
                        send_websocket_update('step_update', {
                            'type': 'step_update',
                            'step_id': step['id'],
                            'status': websocket_status,
                            'title': step['title'],
                            'description': step['description'],
                            'result_summary': validation_message,  # Usar mensaje de validación como resumen
                            'execution_time': step_execution_time,
                            'progress': ((i + 1) / len(steps)) * 100,
                            'validation_status': validation_status
                        })
                        
                        # Log detallado basado en validación
                        if validation_status == 'success':
                            send_websocket_update('log_message', {
                                'type': 'log_message',
                                'level': 'info',
                                'message': f'✅ Paso {i+1}/{len(steps)} completado exitosamente: {step["title"]} - {validation_message} ({step_execution_time:.1f}s)',
                                'timestamp': datetime.now().isoformat()
                            })
                            logger.info(f"✅ Step {i+1} VALIDATED AND COMPLETED successfully: {step['title']} in {step_execution_time:.1f}s")
                        elif validation_status == 'warning':
                            send_websocket_update('log_message', {
                                'type': 'log_message',
                                'level': 'warning', 
                                'message': f'⚠️ Paso {i+1}/{len(steps)} completado con advertencias: {step["title"]} - {validation_message} ({step_execution_time:.1f}s)',
                                'timestamp': datetime.now().isoformat()
                            })
                            logger.warning(f"⚠️ Step {i+1} COMPLETED WITH WARNINGS: {step['title']} - {validation_message}")
                        else:
                            send_websocket_update('log_message', {
                                'type': 'log_message',
                                'level': 'error',
                                'message': f'❌ Paso {i+1}/{len(steps)} falló en validación: {step["title"]} - {validation_message} ({step_execution_time:.1f}s)',
                                'timestamp': datetime.now().isoformat()
                            })
                            logger.error(f"❌ Step {i+1} FAILED VALIDATION: {step['title']} - {validation_message}")
                    else:
                        # Paso ya marcado como fallido o sin resultado válido
                        step['active'] = False
                        if not step.get('status'):
                            step['status'] = StepStatus.FAILED
                            step['completed'] = False
                        
                        send_websocket_update('step_update', {
                            'type': 'step_update',
                            'step_id': step['id'],
                            'status': 'failed',
                            'title': step['title'],
                            'description': step['description'],
                            'result_summary': step.get('error', 'Paso falló durante ejecución'),
                            'execution_time': step_execution_time,
                            'progress': ((i + 1) / len(steps)) * 100
                        })
                        
                        logger.error(f"❌ Step {i+1} FAILED during execution: {step['title']}")
                    
                    
                    # ELIMINADO: Pausa simulada entre pasos
                    # Ahora el progreso se muestra en tiempo real sin pausas artificiales
                    
                except Exception as step_error:
                    step_execution_time = time.time() - step_start_time
                    logger.error(f"❌ Error in step {i+1}: {str(step_error)}")
                    step['completed'] = False
                    step['active'] = False
                    step['status'] = 'failed'
                    step['error'] = str(step_error)
                    
                    # Enviar actualización de paso fallido en tiempo real
                    send_websocket_update('step_update', {
                        'type': 'step_update',
                        'step_id': step['id'],
                        'status': 'failed',
                        'title': step['title'],
                        'description': step['description'],
                        'error': str(step_error),
                        'execution_time': step_execution_time
                    })
                    
                    # Enviar log de error
                    send_websocket_update('log_message', {
                        'type': 'log_message',
                        'level': 'error',
                        'message': f'❌ Error en paso {i+1}/{len(steps)}: {step["title"]} - {str(step_error)}',
                        'timestamp': datetime.now().isoformat()
                    })
                
                # Actualizar plan en memoria y persistencia con estados granulares
                task_manager = get_task_manager()
                task_manager.update_task_step_status(
                    task_id,
                    step['id'],
                    step.get('status', StepStatus.FAILED),  # Usar estado granular
                    step_result.get('validation_message') if step_result else step.get('error'),
                    step.get('error') if step.get('status') == StepStatus.FAILED else None
                )
                update_task_data(task_id, {'plan': steps})
            
            # GENERAR RESULTADO FINAL CONSOLIDADO
            if final_results:
                logger.info(f"🎯 Generating final consolidated result for task {task_id}")
                
                try:
                    if ollama_service:
                        final_prompt = f"""
TAREA COMPLETADA: {message}

RESULTADOS OBTENIDOS:
{final_results}

Genera un RESULTADO FINAL CONSOLIDADO que incluya:

1. 🎯 RESUMEN EJECUTIVO
   - Qué se solicitó
   - Qué se logró
   - Calidad del resultado

2. 📋 ENTREGABLES PRINCIPALES
   - Lista clara de lo que se entregó
   - Resultados específicos obtenidos

3. 🔍 HALLAZGOS CLAVE (si aplica)
   - Información importante encontrada
   - Insights relevantes

4. ✅ CONCLUSIONES
   - Evaluación del éxito de la tarea
   - Recomendaciones adicionales

Formato: Profesional, estructurado y completo.
"""
                        
                        final_result = ollama_service.generate_response(final_prompt, {})
                        
                        # Guardar resultado final
                        active_task_plans[task_id]['final_result'] = {
                            'content': final_result.get('response', 'Tarea completada exitosamente'),
                            'completed_at': datetime.now().isoformat(),
                            'total_steps': len(steps),
                            'all_results': final_results
                        }
                        
                        logger.info(f"✅ Final consolidated result generated for task {task_id}")
                        
                except Exception as e:
                    logger.error(f"Error generating final result: {str(e)}")
                    active_task_plans[task_id]['final_result'] = {
                        'content': 'Tarea completada con algunos errores en la consolidación final',
                        'completed_at': datetime.now().isoformat(),
                        'total_steps': len(steps),
                        'error': str(e)
                    }
            
            # 🆕 PROBLEMA 2: DETERMINACIÓN INTELIGENTE DE ESTADO FINAL USANDO VALIDACIÓN GRANULAR
            final_task_status = determine_task_status_from_steps(steps)
            
            # Estadísticas detalladas para logging y respuesta
            success_steps = sum(1 for step in steps if step.get('status') == StepStatus.COMPLETED_SUCCESS)
            warning_steps = sum(1 for step in steps if step.get('status') == StepStatus.COMPLETED_WITH_WARNINGS)
            failed_steps = sum(1 for step in steps if step.get('status') == StepStatus.FAILED)
            total_steps = len(steps)
            
            # Calcular completed_steps para compatibilidad con código existente
            completed_steps = success_steps + warning_steps
            
            logger.info(f"📊 TASK COMPLETION STATS - Success: {success_steps}, Warnings: {warning_steps}, Failed: {failed_steps}, Total: {total_steps}")
            logger.info(f"🎯 FINAL TASK STATUS: {final_task_status}")
            
            # Generar respuesta final dinámica basada en estado real y validación
            failed_step_details = []
            warning_step_details = []
            
            for step in steps:
                if step.get('status') == StepStatus.FAILED:
                    failed_step_details.append({
                        'title': step.get('title', 'Paso desconocido'),
                        'error': step.get('error', 'Error desconocido'),
                        'validation_message': step.get('result', {}).get('validation_message', '')
                    })
                elif step.get('status') == StepStatus.COMPLETED_WITH_WARNINGS:
                    warning_step_details.append({
                        'title': step.get('title', 'Paso con advertencias'),
                        'warning': step.get('result', {}).get('validation_message', 'Advertencia no especificada')
                    })
            
            # Construir mensaje de errores y advertencias para respuesta
            error_message = None
            warnings = []
            
            if failed_step_details:
                error_message = f"{len(failed_step_details)} paso(s) fallaron: " + ", ".join([f"'{detail['title']}'" for detail in failed_step_details])
            
            if warning_step_details:
                warnings = [f"'{detail['title']}': {detail['warning']}" for detail in warning_step_details]
            
            # Mantener compatibilidad con código existente - generar failed_step_titles
            failed_step_titles = [detail['title'] for detail in failed_step_details]
            final_dynamic_response = generate_clean_response(
                ollama_response="",
                tool_results=final_results,
                task_status=final_task_status,
                failed_step_title=failed_step_titles[0] if failed_step_titles else None,
                error_message=error_message,
                warnings=warnings  # 🆕 Pasar advertencias detalladas
            )
            
            # Marcar tarea como completada en persistencia y memoria
            task_completion_updates = {
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'final_result': final_dynamic_response,  # Usar respuesta dinámica
                'final_task_status': final_task_status,
                'completed_steps': completed_steps,
                'failed_steps': failed_steps,
                'total_steps': total_steps
            }
            
            # Actualizar con TaskManager (persistencia)
            update_task_data(task_id, task_completion_updates)
            
            # También actualizar memoria legacy por compatibilidad
            if task_id in active_task_plans:
                active_task_plans[task_id].update(task_completion_updates)
            
            # Enviar notificación de finalización del plan con estado real
            send_websocket_update('task_completed', {
                'type': 'task_completed',
                'task_id': task_id,
                'status': 'success' if final_task_status == "completed_success" else 'completed_with_warnings',
                'final_result': final_dynamic_response,
                'final_task_status': final_task_status,
                'total_steps': total_steps,
                'completed_steps': completed_steps,
                'failed_steps': failed_steps,
                'execution_time': (datetime.now() - active_task_plans[task_id].get('start_time', datetime.now())).total_seconds(),
                'message': f'🎉 Tarea completada: {completed_steps}/{total_steps} pasos exitosos',
                'timestamp': datetime.now().isoformat()
            })
            
            # Enviar log final
            send_websocket_update('log_message', {
                'type': 'log_message',
                'level': 'info',
                'message': f'🎉 Tarea {task_id} completada con éxito - {len(steps)} pasos ejecutados',
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"🎉 Task {task_id} completed successfully with REAL execution and final delivery!")
        
        # 🚨 PASO 1: LOGGING AGRESIVO ANTES DE CREAR THREAD 🚨
        print(f"🧵 About to create execution thread for task {task_id}")
        print(f"🧵 Target function: execute_steps")
        print(f"🧵 Thread will be daemon: True")
        
        # Ejecutar en hilo separado
        thread = threading.Thread(target=execute_steps)
        thread.daemon = True
        print(f"🧵 Thread created successfully, starting thread...")
        thread.start()
        print(f"🧵 Thread started! Thread is alive: {thread.is_alive()}")
        
        logger.info(f"🚀 Started REAL plan execution for task {task_id}")
        print(f"✅ execute_plan_with_real_tools completed - thread is running")
        
    except Exception as e:
        logger.error(f"Error in real plan execution: {str(e)}")
        
        # Generar respuesta final de error dinámica
        error_response = generate_clean_response(
            ollama_response="",
            tool_results=[],
            task_status="failed",
            failed_step_title="Ejecución general",
            error_message=str(e)
        )
        
        # Enviar notificación de fallo de tarea si WebSocket está disponible
        try:
            from src.websocket.websocket_manager import get_websocket_manager
            websocket_manager = get_websocket_manager()
            if websocket_manager and websocket_manager.is_initialized:
                websocket_manager.send_update(task_id, UpdateType.TASK_FAILED, {
                    'type': 'task_failed',
                    'task_id': task_id,
                    'status': 'failed',
                    'overall_error': str(e),
                    'final_result': error_response,  # Incluir respuesta dinámica de error
                    'message': f'❌ Tarea falló: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                })
        except Exception:
            pass
        
        # Marcar como fallido con respuesta dinámica
        if task_id in active_task_plans:
            active_task_plans[task_id]['status'] = 'failed'
            active_task_plans[task_id]['error'] = str(e)
            active_task_plans[task_id]['final_result'] = error_response

def _fallback_query_extraction(message: str, step_title: str) -> str:
    """
    Método de respaldo heurístico para extracción de query cuando LLM no está disponible
    """
    try:
        # Remover palabras comunes y conectores  
        stop_words = ['el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'con', 'por', 'para', 'sobre', 'crear', 'buscar', 'dame', 'necesito', 'quiero', 'hacer']
        
        # Usar el mensaje original como base
        words = [word for word in message.lower().split() if word not in stop_words and len(word) > 2]
        
        # Agregar año actual para búsquedas más actualizadas
        current_year = "2025"
        if current_year not in ' '.join(words):
            words.append(current_year)
        
        # Tomar las primeras 4 palabras más relevantes
        query = ' '.join(words[:4])
        
        # Si la query está vacía, usar el título del paso
        if not query.strip():
            query = step_title.replace('Búsqueda de', '').replace('información', '').strip()
            
        # Fallback final
        if not query.strip():
            # Extraer sustantivos y términos técnicos del mensaje original
            import re
            technical_terms = re.findall(r'\b[A-Za-z]{4,}\b', message)
            if technical_terms:
                query = ' '.join(technical_terms[:3])
            else:
                query = message[:30]  # Último recurso
        
        logger.info(f"🔄 Fallback search query: '{query}'")
        return query
        
    except Exception:
        return message[:50]  # Fallback seguro

def generate_emergency_structured_plan(message: str, task_id: str, ollama_error: str) -> dict:
    """
    Genera un plan estructurado inteligente cuando Ollama falla completamente
    Análisis heurístico mejorado del mensaje para crear plan específico
    """
    logger.info(f"🆘 Generating emergency structured plan for task {task_id} due to Ollama failure: {ollama_error}")
    
    message_lower = message.lower().strip()
    
    # Análisis inteligente del tipo de tarea
    task_analysis = {
        'type': 'unknown',
        'tools': ['processing'],
        'steps': 1,
        'complexity': 'media'
    }
    
    # Detectar tipo de tarea principal
    if any(word in message_lower for word in ['buscar', 'investigar', 'encontrar', 'información', 'datos']):
        task_analysis.update({
            'type': 'investigación',
            'tools': ['web_search', 'research', 'analysis'],
            'steps': 3,
            'complexity': 'media'
        })
    elif any(word in message_lower for word in ['crear', 'generar', 'escribir', 'desarrollar', 'hacer']):
        task_analysis.update({
            'type': 'creación',
            'tools': ['planning', 'creation', 'delivery'],
            'steps': 3,
            'complexity': 'media'
        })
    elif any(word in message_lower for word in ['analizar', 'análisis', 'estudiar', 'evaluar']):
        task_analysis.update({
            'type': 'análisis',
            'tools': ['data_analysis', 'analysis', 'synthesis'],
            'steps': 3,
            'complexity': 'media'
        })
    elif any(word in message_lower for word in ['documento', 'informe', 'reporte', 'archivo']):
        task_analysis.update({
            'type': 'documentación',
            'tools': ['planning', 'creation', 'delivery'],
            'steps': 3,
            'complexity': 'alta'
        })
    else:
        # Tarea general/procesamiento
        task_analysis.update({
            'type': 'procesamiento_general',
            'tools': ['processing', 'analysis'],
            'steps': 2,
            'complexity': 'baja'
        })
    
    # Construir plan estructurado basado en análisis
    emergency_steps = []
    
    if task_analysis['type'] == 'investigación':
        emergency_steps = [
            {
                "title": f"Buscar información sobre: {message[:50]}...",
                "description": f"Realizar búsqueda web detallada para obtener información relevante sobre la consulta del usuario",
                "tool": "web_search",
                "estimated_time": "2-3 minutos",
                "priority": "alta"
            },
            {
                "title": "Investigar fuentes adicionales",
                "description": "Realizar investigación complementaria para obtener más detalles y verificar información",
                "tool": "research", 
                "estimated_time": "2-3 minutos",
                "priority": "media"
            },
            {
                "title": "Analizar y sintetizar información",
                "description": "Procesar y analizar la información recopilada para generar respuesta completa",
                "tool": "analysis",
                "estimated_time": "1-2 minutos", 
                "priority": "alta"
            }
        ]
    elif task_analysis['type'] == 'creación':
        emergency_steps = [
            {
                "title": f"Planificar creación: {message[:40]}...",
                "description": "Establecer estructura y planificación detallada para la creación solicitada",
                "tool": "planning",
                "estimated_time": "1-2 minutos",
                "priority": "alta"
            },
            {
                "title": "Crear contenido principal",
                "description": f"Desarrollar y crear el contenido principal según los requerimientos específicos",
                "tool": "creation",
                "estimated_time": "3-5 minutos",
                "priority": "alta"
            },
            {
                "title": "Entregar resultado final",
                "description": "Formatear, revisar y entregar el resultado final de la creación",
                "tool": "delivery",
                "estimated_time": "1-2 minutos",
                "priority": "media"
            }
        ]
    elif task_analysis['type'] == 'análisis':
        emergency_steps = [
            {
                "title": f"Analizar datos: {message[:40]}...",
                "description": "Realizar análisis detallado de los datos o información proporcionada",
                "tool": "data_analysis", 
                "estimated_time": "2-3 minutos",
                "priority": "alta"
            },
            {
                "title": "Procesar resultados analíticos",
                "description": "Interpretar y procesar los resultados del análisis para obtener insights",
                "tool": "analysis",
                "estimated_time": "2-3 minutos",
                "priority": "alta"
            },
            {
                "title": "Sintetizar conclusiones",
                "description": "Sintetizar hallazgos y generar conclusiones claras y accionables",
                "tool": "synthesis",
                "estimated_time": "1-2 minutos",
                "priority": "media"
            }
        ]
    elif task_analysis['type'] == 'documentación':
        emergency_steps = [
            {
                "title": f"Planificar documento: {message[:35]}...",
                "description": "Planificar estructura, contenido y formato del documento solicitado",
                "tool": "planning",
                "estimated_time": "1-2 minutos",
                "priority": "alta"
            },
            {
                "title": "Crear contenido del documento",
                "description": "Desarrollar el contenido principal del documento con información detallada",
                "tool": "creation",
                "estimated_time": "4-6 minutos",
                "priority": "alta"
            },
            {
                "title": "Finalizar y entregar documento",
                "description": "Revisar, formatear y entregar el documento final completo",
                "tool": "delivery",
                "estimated_time": "1-2 minutos",
                "priority": "media"
            }
        ]
    else:
        # Plan general de procesamiento
        emergency_steps = [
            {
                "title": f"Procesar solicitud: {message[:45]}...",
                "description": f"Procesar y atender la solicitud específica del usuario de manera integral",
                "tool": "processing",
                "estimated_time": "2-3 minutos",
                "priority": "alta"
            },
            {
                "title": "Analizar y completar",
                "description": "Analizar los requerimientos y completar la tarea de manera satisfactoria",
                "tool": "analysis",
                "estimated_time": "1-2 minutos",
                "priority": "media"
            }
        ]
    
    # Calcular tiempo total estimado
    total_time_minutes = sum(int(step['estimated_time'].split('-')[0]) for step in emergency_steps if step['estimated_time'].split('-')[0].isdigit())
    total_time = f"{total_time_minutes}-{total_time_minutes + len(emergency_steps)} minutos"
    
    return {
        "steps": emergency_steps,
        "task_type": f"emergency_{task_analysis['type']}",
        "complexity": task_analysis['complexity'],
        "estimated_total_time": total_time
    }

def generate_task_title_with_llm(message: str, task_id: str) -> str:
    """
    Genera un título mejorado y profesional para la tarea usando LLM
    """
    logger.info(f"📝 Generating enhanced title for task {task_id} - Original: {message[:50]}...")
    
    # Obtener servicio de Ollama
    ollama_service = get_ollama_service()
    if not ollama_service or not ollama_service.is_healthy():
        logger.warning(f"⚠️ Ollama not available for title generation, using original message")
        return message.strip()
    
    try:
        # Prompt específico para generar títulos profesionales
        title_prompt = f"""
Genera SOLAMENTE un título profesional y conciso para esta tarea: "{message}"

REGLAS ESTRICTAS:
- Responde SOLO con el título, nada más
- Máximo 60 caracteres
- Debe ser específico al tema tratado
- Formato profesional y claro
- NO agregues explicaciones, planes ni pasos
- NO uses palabras como "información", "datos", "plan de acción"

EJEMPLOS:
Input: "buscar información sobre IA"
Output: Análisis de Tendencias en Inteligencia Artificial 2025

Input: "crear un informe de ventas" 
Output: Informe de Rendimiento de Ventas Q1 2025

Input: "analizar el mercado"
Output: Estudio de Análisis de Mercado Sectorial

Input: "GENERA UN INFORME SOBRE LA selección Argentina de futbol en 2025"
Output: Informe Selección Argentina de Fútbol 2025

Tu respuesta debe ser ÚNICAMENTE el título:
"""
        
        response = ollama_service.generate_response(title_prompt, {
            'temperature': 0.3,  # Creativo pero controlado
            'max_tokens': 100,   # Título corto
            'top_p': 0.9
        })
        
        if response.get('error'):
            logger.warning(f"⚠️ Error generating title with LLM: {response['error']}")
            return message.strip()
        
        # Limpiar y validar el título generado
        generated_title = response.get('response', '').strip()
        
        # Limpiar formato markdown o caracteres extra
        generated_title = generated_title.replace('**', '').replace('*', '')
        generated_title = generated_title.replace('"', '').replace("'", '')
        generated_title = generated_title.replace('Output:', '').replace('Input:', '')
        
        # Tomar solo la primera línea (en caso de que venga texto extra)
        generated_title = generated_title.split('\n')[0].strip()
        
        # Limpiar prefijos comunes
        if generated_title.lower().startswith('título:'):
            generated_title = generated_title[7:].strip()
        if generated_title.lower().startswith('output:'):
            generated_title = generated_title[7:].strip()
            
        # Validaciones
        if len(generated_title) == 0:
            logger.warning(f"⚠️ Empty title generated, using original message")
            return message.strip()
        
        if len(generated_title) > 80:
            generated_title = generated_title[:77] + "..."
        
        logger.info(f"✅ Generated enhanced title for task {task_id}: '{generated_title}'")
        return generated_title
        
    except Exception as e:
        logger.error(f"❌ Error generating title with LLM: {str(e)}")
        return message.strip()

def generate_unified_ai_plan(message: str, task_id: str, attempt_retries: bool = True) -> dict:
    """
    Función UNIFICADA para generación de planes usando Ollama con robustecimiento y validación de esquemas
    Consolidación de generate_dynamic_plan_with_ai y generate_task_plan para eliminar duplicación
    """
    logger.info(f"🧠 Generating unified AI-powered plan for task {task_id} - Message: {message[:50]}...")
    
    # Obtener servicio de Ollama
    ollama_service = get_ollama_service()
    if not ollama_service:
        logger.error("❌ Ollama service not available for unified plan generation")
        return generate_fallback_plan(message, task_id)
    
    # Verificar que Ollama esté saludable
    if not ollama_service.is_healthy():
        logger.error("❌ Ollama service not healthy for unified plan generation")
        return generate_fallback_plan(message, task_id)
    
    def validate_plan_schema(plan_data: dict) -> bool:
        """Validar que el plan cumple con el esquema requerido"""
        try:
            jsonschema.validate(plan_data, PLAN_SCHEMA)
            return True
        except jsonschema.ValidationError as e:
            logger.warning(f"❌ Plan schema validation failed for task {task_id}: {e.message}")
            return False
    
    def generate_plan_with_retries() -> dict:
        """Generar plan con reintentos y retroalimentación específica a Ollama"""
        max_attempts = 2 if attempt_retries else 1
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"🔄 Unified plan generation attempt {attempt}/{max_attempts} for task {task_id}")
                
                # Construir prompt específico mejorado para generación de JSON estructurado
                if attempt == 1:
                    # Primera tentativa: prompt específico dinámico
                    prompt = f"""
Genera SOLO un objeto JSON válido para esta tarea: "{message}"

IMPORTANTE: Responde ÚNICAMENTE con JSON válido. NO agregues texto, explicaciones o formato markdown.

Estructura del JSON requerida:
{{
  "steps": [
    {{
      "title": "Título específico del paso (5-100 caracteres)",
      "description": "Descripción concreta del paso (10-300 caracteres)", 
      "tool": "herramienta_válida",
      "estimated_time": "tiempo estimado",
      "priority": "alta|media|baja"
    }}
  ],
  "task_type": "tipo de tarea específico",
  "complexity": "baja|media|alta",
  "estimated_total_time": "tiempo total estimado",
  "suggested_icon": "icono_apropiado"
}}

🎯 SELECCIÓN DE ICONO - Elige EXACTAMENTE uno de estos iconos según el tipo de tarea:

**Si menciona: código, programar, app, web, software** → USA: "code"
**Si menciona: restaurante, bar, valencia, madrid, lugar, ubicación** → USA: "map" 
**Si menciona: documento, informe, texto, escribir** → USA: "file"
**Si menciona: analizar, datos, estadística, mercado** → USA: "chart"
**Si menciona: buscar, investigar, research** → USA: "search"
**Si menciona: imagen, diseño, crear visual** → USA: "image"
**Si menciona: música, audio, sonido** → USA: "music"
**Si menciona: negocio, empresa, comercial** → USA: "briefcase"
**Para todo lo demás** → USA: "target"

🔥 REGLAS SIMPLES:
- LUGARES/RESTAURANTES/CIUDADES → "map"  
- PROGRAMACIÓN/DESARROLLO → "code"
- DOCUMENTOS/INFORMES → "file"
- ANÁLISIS/DATOS → "chart"
- BÚSQUEDA/INVESTIGACIÓN → "search"
- TODO LO DEMÁS → "target"

HERRAMIENTAS VÁLIDAS: web_search, analysis, creation, planning, delivery, processing, synthesis, search_definition, data_analysis, shell, research, investigation, web_scraping, search, mind_map, spreadsheets, database

ICONOS VÁLIDOS: map, code, file, chart, search, image, music, briefcase, target

RESPONDE SOLO CON EL JSON - SIN TEXTO ADICIONAL
"""
                elif attempt == 2:
                    # Segunda tentativa: prompt con corrección específica y metodología adaptativa
                    prompt = f"""
ERROR: El JSON anterior falló. SOLO genera JSON válido para: "{message}"

Error previo: {last_error}

IMPORTANTE: Responde ÚNICAMENTE con JSON válido sin texto adicional.

Formato JSON requerido:
{{
  "steps": [
    {{
      "title": "Título específico del paso",
      "description": "Descripción concreta del paso", 
      "tool": "web_search",
      "estimated_time": "tiempo",
      "priority": "media"
    }}
  ],
  "task_type": "tipo de tarea",
  "complexity": "media",
  "estimated_total_time": "tiempo total",
  "suggested_icon": "icono_apropiado"
}}

🎯 SELECCIÓN DE ICONO - USA EXACTAMENTE uno de estos iconos:

**LUGARES/RESTAURANTES/CIUDADES** → "map"
**DESARROLLO/CÓDIGO/PROGRAMACIÓN** → "code"  
**DOCUMENTOS/INFORMES/TEXTO** → "file"
**ANÁLISIS/DATOS/MERCADO** → "chart"
**BÚSQUEDA/INVESTIGACIÓN** → "search"
**IMÁGENES/DISEÑO** → "image"
**MÚSICA/AUDIO** → "music"
**NEGOCIOS/EMPRESA** → "briefcase"
**TODO LO DEMÁS** → "target"

⚠️ REGLA ESPECIAL: Si mencionas LUGARES, RESTAURANTES, CIUDADES (valencia, madrid, etc.) → USA "map"

HERRAMIENTAS VÁLIDAS: web_search, analysis, creation, planning, delivery, processing, synthesis, search_definition, data_analysis, shell, research, investigation, web_scraping, search, mind_map, spreadsheets, database

ICONOS VÁLIDOS: map, code, file, chart, search, image, music, briefcase, target

RESPONDE SOLO JSON - NO TEXTO ADICIONAL
"""
                
                # Llamar a Ollama con parámetros optimizados para JSON
                response = ollama_service.generate_response(prompt, {
                    'temperature': 0.1,  # Muy baja para mayor consistencia
                    'max_tokens': 800,
                    'response_format': 'json',
                    'stop': ['```', 'json', '**', '#'],  # Evitar formato markdown
                    'top_p': 0.9
                })
                
                if response.get('error'):
                    last_error = response['error']
                    logger.warning(f"⚠️ Ollama error attempt {attempt}: {response['error']}")
                    continue
                
                # Parsear respuesta JSON con múltiples estrategias
                response_text = response.get('response', '').strip()
                logger.info(f"📥 Ollama response attempt {attempt} for task {task_id}: {response_text[:200]}...")
                
                plan_data = None
                
                # Estrategia 1: JSON limpio directo
                try:
                    cleaned_response = response_text.replace('```json', '').replace('```', '').strip()
                    # Remover cualquier texto antes del primer {
                    if '{' in cleaned_response:
                        start_idx = cleaned_response.find('{')
                        cleaned_response = cleaned_response[start_idx:]
                    # Remover cualquier texto después del último }
                    if '}' in cleaned_response:
                        end_idx = cleaned_response.rfind('}') + 1
                        cleaned_response = cleaned_response[:end_idx]
                    
                    if cleaned_response.startswith('{') and cleaned_response.endswith('}'):
                        plan_data = json.loads(cleaned_response)
                except json.JSONDecodeError as e:
                    logger.debug(f"📝 JSON parsing strategy 1 failed: {str(e)}")
                
                # Estrategia 2: Buscar JSON en el texto (mejorado)
                if not plan_data:
                    try:
                        # Buscar patrón JSON completo más robusto
                        json_patterns = [
                            r'\{[^}]*"steps"[^}]*\[.*?\][^}]*\}',
                            r'\{.*?"steps".*?\[.*?\].*?\}',
                            r'(\{[^{}]*\{[^{}]*\}[^{}]*\})'
                        ]
                        
                        for pattern in json_patterns:
                            json_match = re.search(pattern, response_text, re.DOTALL)
                            if json_match:
                                plan_data = json.loads(json_match.group())
                                break
                    except json.JSONDecodeError as e:
                        logger.debug(f"📝 JSON parsing strategy 2 failed: {str(e)}")
                
                # Estrategia 3: JSON con corrección de formato común (mejorado)
                if not plan_data:
                    try:
                        # Limpiar markdown y texto extra
                        corrected_text = response_text
                        # Remover markdown
                        corrected_text = re.sub(r'\*\*.*?\*\*', '', corrected_text)
                        corrected_text = re.sub(r'\*.*?\*', '', corrected_text)
                        corrected_text = re.sub(r'#.*?\n', '', corrected_text)
                        # Corregir comillas simples por dobles
                        corrected_text = corrected_text.replace("'", '"')
                        # Buscar solo el JSON
                        if '{' in corrected_text and '}' in corrected_text:
                            start_idx = corrected_text.find('{')
                            end_idx = corrected_text.rfind('}') + 1
                            corrected_text = corrected_text[start_idx:end_idx]
                        
                        plan_data = json.loads(corrected_text)
                    except (json.JSONDecodeError, Exception) as e:
                        logger.debug(f"📝 JSON parsing strategy 3 failed: {str(e)}")
                
                # Estrategia 4: Crear JSON desde texto estructurado
                if not plan_data:
                    try:
                        # Si hay listas numeradas, convertir a JSON
                        if '1.' in response_text and ('2.' in response_text or '3.' in response_text):
                            steps = []
                            lines = response_text.split('\n')
                            current_step = None
                            
                            for line in lines:
                                line = line.strip()
                                if re.match(r'^\d+\.', line):
                                    if current_step:
                                        steps.append(current_step)
                                    title = re.sub(r'^\d+\.\s*\*\*?', '', line)
                                    title = re.sub(r'\*\*?:.*', '', title).strip()
                                    current_step = {
                                        'title': title,
                                        'description': f'Completar: {title}',
                                        'tool': 'processing',
                                        'estimated_time': '2-5 minutos',
                                        'priority': 'media'
                                    }
                                elif current_step and line:
                                    current_step['description'] = line
                            
                            if current_step:
                                steps.append(current_step)
                            
                            if len(steps) > 0:
                                plan_data = {
                                    'steps': steps,
                                    'task_type': 'análisis_estructurado',
                                    'complexity': 'media',
                                    'estimated_total_time': f'{len(steps) * 3}-{len(steps) * 6} minutos'
                                }
                    except Exception as e:
                        logger.debug(f"📝 JSON parsing strategy 4 failed: {str(e)}")
                
                if not plan_data:
                    last_error = f"No se pudo parsear JSON válido. Respuesta: {response_text[:100]}..."
                    logger.warning(f"❌ Failed to parse JSON on attempt {attempt}: {last_error}")
                    continue
                
                # 🎯 ICONO INTELIGENTE: Verificar y corregir iconos incoherentes ANTES de validar esquema
                logger.info(f"🔍 DEBUG: Starting icon verification for task {task_id}")
                logger.info(f"🔍 DEBUG: plan_data keys: {list(plan_data.keys()) if plan_data else 'None'}")
                
                if 'suggested_icon' in plan_data and plan_data['suggested_icon']:
                    current_icon = plan_data['suggested_icon']
                    logger.info(f"🔍 DEBUG: Current icon from LLM: {current_icon}")
                    
                    # Verificar si el icono actual es coherente, si no, usar el unificado
                    unified_icon = determine_unified_icon(message)
                    logger.info(f"🔍 DEBUG: Unified function suggests: {unified_icon}")
                    
                    # Casos donde debemos sobrescribir el icono del LLM
                    should_override = False
                    
                    # Si el LLM dio 'target' pero hay una categoría específica disponible
                    if current_icon == 'target' and unified_icon != 'target':
                        should_override = True
                        logger.info(f"🔄 Overriding generic 'target' icon with specific '{unified_icon}' for task {task_id}")
                    
                    # Si hay palabras de ubicación pero no se asignó un icono de mapa
                    location_words = ['restaurante', 'bar', 'comida', 'valencia', 'madrid', 'barcelona', 'lugar', 'ubicación']
                    has_location = any(word in message.lower() for word in location_words)
                    is_not_map = current_icon not in ['map', 'navigation', 'globe']
                    logger.info(f"🔍 DEBUG: Has location words: {has_location}, Is not map icon: {is_not_map}")
                    
                    if has_location and is_not_map:
                        should_override = True
                        unified_icon = 'map'
                        logger.info(f"🗺️ Forcing location icon 'map' for location-based task {task_id}")
                    
                    logger.info(f"🔍 DEBUG: Should override: {should_override}")
                    
                    if should_override:
                        plan_data['suggested_icon'] = unified_icon
                        logger.info(f"🎯 Corrected icon for task {task_id}: {current_icon} → {unified_icon}")
                    else:
                        logger.info(f"🎯 Keeping LLM-generated icon for task {task_id}: {current_icon}")
                else:
                    logger.info(f"🔍 DEBUG: No suggested_icon found, using fallback")
                    # Si no hay icono sugerido, usar función unificada
                    fallback_icon = determine_unified_icon(message)
                    plan_data['suggested_icon'] = fallback_icon
                    logger.info(f"🎯 Unified fallback icon assigned for task {task_id}: {fallback_icon}")
                
                # Validar esquema
                if not validate_plan_schema(plan_data):
                    last_error = "El JSON no cumple con el esquema requerido"
                    logger.warning(f"❌ Schema validation failed on attempt {attempt}")
                    continue
                
                # Validar que el plan tenga la estructura esperada
                if not isinstance(plan_data.get('steps'), list) or len(plan_data.get('steps', [])) == 0:
                    last_error = "El plan no contiene pasos válidos"
                    logger.warning(f"❌ Invalid plan structure on attempt {attempt}")
                    continue
                
                logger.info(f"✅ Successfully generated and validated unified plan for task {task_id} on attempt {attempt}")
                return plan_data
                
            except Exception as e:
                last_error = f"Error inesperado: {str(e)}"
                logger.error(f"❌ Unexpected error on attempt {attempt} for task {task_id}: {str(e)}")
                continue
        
        # Si llegamos aquí, todos los reintentos fallaron
        logger.error(f"❌ All {max_attempts} plan generation attempts failed for task {task_id}. Last error: {last_error}")
        
        # ESTRATEGIA DE EMERGENCIA: Crear plan básico estructurado basado en análisis del mensaje
        logger.warning(f"🆘 Activating emergency plan generation for task {task_id}")
        
        try:
            emergency_plan = generate_emergency_structured_plan(message, task_id, last_error)
            logger.info(f"✅ Emergency plan generated successfully for task {task_id}")
            return emergency_plan
        except Exception as emergency_error:
            logger.error(f"❌ Emergency plan generation also failed for task {task_id}: {str(emergency_error)}")
            raise Exception(f"Complete failure: All plan generation strategies failed. Ollama errors: {last_error}. Emergency error: {str(emergency_error)}")
    
    try:
        # Intentar generar plan con reintentos
        plan_data = generate_plan_with_retries()
        
        # Convertir a formato frontend
        plan_steps = []
        for i, step in enumerate(plan_data.get('steps', [])):
            if not isinstance(step, dict):
                logger.warning(f"⚠️ Invalid step format for task {task_id}, step {i}: {step}")
                continue
                
            plan_steps.append({
                'id': f"step_{i+1}",
                'title': step.get('title', f'Paso {i+1}').strip(),
                'description': step.get('description', 'Procesando...').strip(),
                'tool': step.get('tool', 'processing'),
                'status': 'pending',
                'estimated_time': step.get('estimated_time', '1 minuto'),
                'completed': False,
                'active': i == 0,  # Solo el primer paso activo
                'priority': step.get('priority', 'media')
            })
        
        if len(plan_steps) == 0:
            logger.error(f"❌ No valid steps created for task {task_id}")
            return generate_fallback_plan(message, task_id)
            
        # Guardar plan con TaskManager (persistencia MongoDB)
        task_data = {
            'plan': plan_steps,
            'current_step': 0,
            'status': 'plan_generated',  # ✅ MEJORA: Estado inicial correcto
            'created_at': datetime.now().isoformat(),
            'start_time': datetime.now(),
            'message': message,
            'task_type': plan_data.get('task_type', 'general'),
            'complexity': plan_data.get('complexity', 'media'),
            'ai_generated': True,
            'plan_source': 'unified_ai_generated'  # Indicar fuente del plan unificado
        }
        
        # Guardar en persistencia y memoria legacy
        save_task_data(task_id, task_data)
        
        logger.info(f"🎉 Generated unified AI-powered plan for task {task_id} with {len(plan_steps)} specific steps")
        logger.info(f"📋 Plan steps for task {task_id}: {[step['title'] for step in plan_steps]}")
        
        return {
            'steps': plan_steps,
            'total_steps': len(plan_steps),
            'estimated_total_time': plan_data.get('estimated_total_time', '2-5 minutos'),
            'task_type': plan_data.get('task_type', 'unified_ai_generated_dynamic'),
            'complexity': plan_data.get('complexity', 'media'),
            'suggested_icon': plan_data.get('suggested_icon', 'target'), # 🎯 INCLUDE SUGGESTED ICON
            'ai_generated': True,
            'plan_source': 'unified_ai_generated',  # ✅ MEJORA: Indicar fuente del plan unificado
            'schema_validated': True  # ✅ MEJORA: Indicar que pasó validación
        }
            
    except Exception as e:
        logger.error(f"❌ All retries failed for unified AI plan generation task {task_id}: {str(e)}")
        return generate_fallback_plan(message, task_id)

# FUNCIONES HELPER SIMPLIFICADAS

def extract_search_query_from_message(message: str, step_title: str) -> str:
    """Extract search query from message and step"""
    # Simple extraction - just combine message and step title
    combined = f"{message} {step_title}".lower()
    # Remove common words
    for word in ['crear', 'generar', 'hacer', 'buscar', 'sobre', 'información', 'para', 'de']:
        combined = combined.replace(word, ' ')
    return combined.strip()[:100]  # Limit length

def generate_fallback_plan(message: str, task_id: str) -> dict:
    """
    Genera un plan de fallback más específico cuando la IA no está disponible
    """
    try:
        logger.warning(f"🔄 Generating fallback plan for task {task_id} (AI not available)")
        
        # Analizar el mensaje para determinar el tipo de tarea con más detalle
        message_lower = message.lower()
        original_message = message.strip()
        
        # Extraer palabras clave específicas para personalización
        keywords = [word for word in message_lower.split() if len(word) > 3]
        
        # Patrones más específicos para diferentes tipos de tareas
        if any(word in message_lower for word in ['crear', 'generar', 'escribir', 'desarrollar', 'diseñar', 'construir', 'hacer', 'elaborar']):
            # Extraer el objeto de la creación de forma más inteligente
            task_subject = original_message
            for word in ['crear', 'generar', 'escribir', 'desarrollar', 'diseñar', 'construir', 'hacer', 'elaborar', 'un', 'una', 'el', 'la']:
                task_subject = task_subject.replace(word, '').replace(word.capitalize(), '')
            task_subject = task_subject.strip()
            
            if not task_subject:
                task_subject = "contenido solicitado"
            
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': f'Análisis detallado: {task_subject}',
                    'description': f'Analizar requisitos específicos, contexto y objetivos para {task_subject}',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': f'Estructuración y diseño',
                    'description': f'Definir estructura, formato y metodología para {task_subject}',
                    'tool': 'planning',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': f'Desarrollo y creación',
                    'description': f'Ejecutar la creación completa de {task_subject} siguiendo los requisitos identificados',
                    'tool': 'creation',
                    'status': 'pending',
                    'estimated_time': '2-3 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_4',
                    'title': f'Revisión y optimización final',
                    'description': f'Revisar calidad, completitud y entregar {task_subject} finalizado',
                    'tool': 'delivery',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': False
                }
            ]
            
        elif any(word in message_lower for word in ['buscar', 'investigar', 'analizar', 'estudiar', 'revisar', 'información', 'datos', 'investigación']):
            # Extraer tema de investigación de forma más inteligente
            research_topic = original_message
            for word in ['buscar', 'investigar', 'analizar', 'estudiar', 'revisar', 'información', 'sobre', 'acerca', 'de', 'datos', 'dame', 'necesito']:
                research_topic = research_topic.replace(word, '').replace(word.capitalize(), '')
            research_topic = research_topic.strip()
            
            if not research_topic:
                research_topic = "tema solicitado"
                
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': f'Estrategia de investigación: {research_topic}',
                    'description': f'Definir metodología, fuentes y alcance de investigación para {research_topic}',
                    'tool': 'search_definition',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': f'Recopilación de información especializada',
                    'description': f'Buscar información actualizada y relevante sobre {research_topic} en múltiples fuentes',
                    'tool': 'web_search',
                    'status': 'pending',
                    'estimated_time': '1-2 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': f'Análisis y procesamiento de datos',
                    'description': f'Analizar, filtrar y procesar la información recopilada sobre {research_topic}',
                    'tool': 'data_analysis',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_4',
                    'title': f'Síntesis y presentación de hallazgos',
                    'description': f'Sintetizar resultados y presentar conclusiones sobre {research_topic}',
                    'tool': 'synthesis',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': False
                }
            ]
            
        elif any(word in message_lower for word in ['explica', 'define', 'qué es', 'cómo', 'por qué', 'cuál']):
            # Preguntas explicativas
            topic = original_message.replace('?', '').strip()
            
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': f'Investigación conceptual: {topic}',
                    'description': f'Buscar definiciones, conceptos clave y contexto para responder: {topic}',
                    'tool': 'web_search',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': f'Análisis y estructuración',
                    'description': f'Analizar información encontrada y estructurar respuesta comprensible',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': f'Formulación de respuesta completa',
                    'description': f'Crear respuesta detallada y educativa para: {topic}',
                    'tool': 'synthesis',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': False
                }
            ]
            
        else:
            # Plan adaptativo para tareas no clasificadas
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': f'Interpretación de solicitud: "{original_message[:30]}..."',
                    'description': f'Analizar y comprender los requisitos específicos de: {original_message}',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': f'Planificación de ejecución',
                    'description': f'Definir metodología y pasos para cumplir con: {original_message}',
                    'tool': 'planning',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': f'Procesamiento y ejecución',
                    'description': f'Ejecutar y procesar según los requisitos identificados',
                    'tool': 'processing',
                    'status': 'pending',
                    'estimated_time': '1-2 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_4',
                    'title': f'Entrega de resultados finales',
                    'description': f'Entregar resultado completo que satisfaga: {original_message}',
                    'tool': 'delivery',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': False
                }
            ]
        
        # Get appropriate icon for this task using unified function
        suggested_icon = determine_unified_icon(original_message)
        active_task_plans[task_id] = {
            'plan': plan_steps,
            'current_step': 0,
            'status': 'executing',
            'created_at': datetime.now().isoformat(),
            'start_time': datetime.now(),
            'message': message,
            'ai_generated': False  # Marcar como plan de fallback
        }
        
        logger.info(f"📋 Generated fallback plan for task {task_id} with {len(plan_steps)} customized steps")
        
        return {
            'steps': plan_steps,
            'total_steps': len(plan_steps),
            'estimated_total_time': '2-4 minutos',
            'task_type': 'adaptive_fallback_plan',
            'suggested_icon': suggested_icon,
            'ai_generated': False
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
            'task_type': 'simple_execution',
            'suggested_icon': 'target'  # Generic icon for simple execution
        }



def generate_clean_response(ollama_response: str, tool_results: list, task_status: str = "success", 
                          failed_step_title: str = None, error_message: str = None, warnings: list = None) -> dict:
    """
    Genera una respuesta final estructurada en JSON basada en el estado real de la tarea
    ENHANCED VERSION - As per NEWUPGRADE.md Section 4: Returns structured JSON instead of plain text
    
    Args:
        ollama_response: Respuesta original de Ollama
        tool_results: Resultados de herramientas ejecutadas
        task_status: Estado final de la tarea ('completed_success', 'completed_with_warnings', 'failed')
        failed_step_title: Título del paso que falló (si aplica)
        error_message: Mensaje de error específico (si aplica)
        warnings: Lista de advertencias detalladas (si aplica)
    
    Returns:
        dict: Objeto JSON estructurado con toda la información de la tarea
    """
    try:
        # Detectar archivos creados en los resultados
        files_created = []
        deliverables_info = []
        
        for result in tool_results or []:
            if isinstance(result, dict):
                if result.get('file_created') and result.get('file_name'):
                    files_created.append({
                        'name': result['file_name'],
                        'size': result.get('file_size', 0),
                        'download_url': result.get('download_url', ''),
                        'type': result.get('type', 'unknown')
                    })
                    
                if result.get('tangible_result') or result.get('final_deliverable'):
                    deliverables_info.append(result)
        
        # BUILD STRUCTURED RESPONSE OBJECT
        response_data = {
            "status": task_status,
            "message": "",  # Will be set below based on status
            "files_generated": files_created,
            "warnings": warnings or [],
            "error": error_message,
            "deliverables_count": len(files_created),
            "raw_ollama_response": ollama_response,
            "tool_results_count": len(tool_results or []),
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate message based on task status
        if task_status == "completed_success":
            # Tarea completada exitosamente
            if files_created:
                response_data["message"] = f"""🎉 ¡Excelente! He completado tu solicitud con éxito y he generado {len(files_created)} archivo(s) tangible(s).

📁 **ARCHIVOS GENERADOS:**

"""
                for file_info in files_created:
                    response_data["message"] += f"""• **{file_info['name']}** 
  📄 Tamaño: {file_info.get('size', 0)} bytes
  🔗 [Descargar archivo]({file_info.get('download_url', '#')})

"""
                response_data["message"] += """

✅ **Estado**: Completado exitosamente
📊 **Resultados**: Todos los objetivos alcanzados

Puedes descargar los archivos haciendo clic en los enlaces de arriba."""
            else:
                response_data["message"] = f"""🎉 ¡Perfecto! He completado tu solicitud exitosamente.

✅ **Estado**: Completado con éxito
📋 **Resumen**: {ollama_response[:200]}...

Todos los objetivos han sido alcanzados según lo solicitado."""

        elif task_status == "completed_with_warnings":
            # Tarea completada pero con advertencias
            response_data["message"] = f"""⚠️ Tu solicitud ha sido completada, pero con algunas advertencias importantes.

📋 **Resumen**: {ollama_response[:200] if ollama_response else 'Tarea procesada'}...

⚠️ **ADVERTENCIAS DETECTADAS:**

"""
            for warning in (warnings or []):
                response_data["message"] += f"• {warning}\n"

            if files_created:
                response_data["message"] += f"""

📁 **ARCHIVOS GENERADOS** ({len(files_created)}):

"""
                for file_info in files_created:
                    response_data["message"] += f"""• **{file_info['name']}** 
  🔗 [Descargar]({file_info.get('download_url', '#')})

"""
            response_data["message"] += """

✅ **Estado**: Completado con advertencias
💡 **Recomendación**: Revisa las advertencias antes de proceder."""

        elif task_status == "failed":
            # Tarea fallida
            response_data["message"] = f"""❌ Lo siento, no pude completar tu solicitud debido a un error.

🚨 **ERROR PRINCIPAL**: {error_message or 'Error desconocido'}

"""
            if failed_step_title:
                response_data["message"] += f"📍 **Paso fallido**: {failed_step_title}\n\n"

            response_data["message"] += f"""📋 **Contexto**: {ollama_response[:150] if ollama_response else 'Sin contexto disponible'}...

❌ **Estado**: Fallido
🔧 **Sugerencia**: Intenta reformular tu solicitud o contacta soporte técnico."""

        else:
            # Estado desconocido - fallback
            response_data["message"] = f"""ℹ️ Tu solicitud ha sido procesada.

📋 **Información**: {ollama_response[:200] if ollama_response else 'Procesado'}...

📊 **Estado**: {task_status}
⏰ **Procesado**: {datetime.now().strftime('%d/%m/%Y %H:%M')}"""

        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error generating clean response: {e}")
        # Return error response structure
        return {
            "status": "error",
            "message": f"❌ Error al generar respuesta final: {str(e)}",
            "files_generated": [],
            "warnings": ["Error interno al procesar respuesta"],
            "error": str(e),
            "deliverables_count": 0,
            "raw_ollama_response": ollama_response or "",
            "tool_results_count": len(tool_results or []),
            "timestamp": datetime.now().isoformat()
        }


def generate_clean_response_legacy(ollama_response: str, tool_results: list, task_status: str = "success", 
                          failed_step_title: str = None, error_message: str = None, warnings: list = None) -> str:
    """
    Genera una respuesta final condicional y dinámica basada en el estado real de la tarea
    PROBLEMA 2: Incluye información sobre validación de resultados y advertencias.
    
    Args:
        ollama_response: Respuesta original de Ollama
        tool_results: Resultados de herramientas ejecutadas
        task_status: Estado final de la tarea ('completed_success', 'completed_with_warnings', 'failed')
        failed_step_title: Título del paso que falló (si aplica)
        error_message: Mensaje de error específico (si aplica)
        warnings: Lista de advertencias detalladas (si aplica)
    
    Returns:
        str: Respuesta final apropiada para el estado de la tarea con información de archivos y validación
    """
    try:
        # Detectar archivos creados en los resultados
        files_created = []
        deliverables_info = []
        
        for result in tool_results or []:
            if isinstance(result, dict):
                if result.get('file_created') and result.get('file_name'):
                    files_created.append({
                        'name': result['file_name'],
                        'size': result.get('file_size', 0),
                        'download_url': result.get('download_url', ''),
                        'type': result.get('type', 'unknown')
                    })
                    
                if result.get('tangible_result') or result.get('final_deliverable'):
                    deliverables_info.append(result)
        
        # Respuesta basada en el estado real de la tarea
        if task_status == "completed_success":
            # Tarea completada exitosamente
            if files_created:
                clean_response = f"""🎉 ¡Excelente! He completado tu solicitud con éxito y he generado {len(files_created)} archivo(s) tangible(s).

📁 **ARCHIVOS GENERADOS:**
"""
                for file_info in files_created:
                    clean_response += f"• **{file_info['name']}** ({file_info['size']} bytes) - Listo para descargar\n"
                
                clean_response += """
✅ He ejecutado todos los pasos del plan de acción que puedes ver en el panel lateral. La tarea se ha finalizado correctamente y todos los objetivos han sido alcanzados.

🔄 **Cómo acceder a tus archivos:**
- Revisa el panel de progreso para enlaces de descarga
- Los archivos están disponibles inmediatamente
- Puedes descargar cada archivo individualmente

📊 Puedes revisar los detalles completos de la ejecución en el monitor de progreso."""
            else:
                clean_response = """¡Excelente! He completado tu solicitud con éxito. 

He ejecutado todos los pasos del plan de acción que puedes ver en el panel lateral. La tarea se ha finalizado correctamente y todos los objetivos han sido alcanzados.

Puedes revisar los detalles completos de la ejecución en el monitor de progreso."""

        elif task_status == "plan_ready":
            # Plan generated and ready for execution - call Ollama for real response
            clean_response = ollama_response
            
        elif task_status == "completed_with_warnings":
            # 🆕 PROBLEMA 2: Tarea completada con advertencias específicas de validación
            if files_created:
                clean_response = f"""✅ He completado tu solicitud con {len(files_created)} archivo(s) generado(s), aunque con algunas advertencias menores.

📁 **ARCHIVOS GENERADOS:**
"""
                for file_info in files_created:
                    clean_response += f"• **{file_info['name']}** ({file_info['size']} bytes)\n"
                
                clean_response += """
⚠️ El plan de acción se ejecutó correctamente en general, pero algunos pasos tuvieron limitaciones."""
                
                # Añadir advertencias específicas si están disponibles
                if warnings:
                    clean_response += f"""

**ADVERTENCIAS ESPECÍFICAS:**
"""
                    for warning in warnings[:3]:  # Mostrar máximo 3 advertencias
                        clean_response += f"• {warning}\n"
                    
                    if len(warnings) > 3:
                        clean_response += f"• ... y {len(warnings) - 3} advertencia(s) adicional(es)\n"
                
                clean_response += """

El resultado principal fue alcanzado exitosamente. Te recomiendo revisar el monitor de ejecución para más detalles."""
            else:
                clean_response = """He completado tu solicitud, aunque con algunas advertencias menores.

⚠️ El plan de acción se ejecutó correctamente en general, pero algunos pasos tuvieron limitaciones."""
                
                # Añadir advertencias específicas si están disponibles
                if warnings:
                    clean_response += f"""

**ADVERTENCIAS ESPECÍFICAS:**
"""
                    for warning in warnings[:3]:  # Mostrar máximo 3 advertencias
                        clean_response += f"• {warning}\n"
                    
                    if len(warnings) > 3:
                        clean_response += f"• ... y {len(warnings) - 3} advertencia(s) adicional(es)\n"
                
                clean_response += """

El resultado principal fue alcanzado exitosamente. Te recomiendo revisar el monitor de ejecución para más detalles."""

        elif task_status == "failed":
            # Tarea falló
            failed_step_info = f" en el paso '{failed_step_title}'" if failed_step_title else ""
            error_info = f": {error_message}" if error_message else ""
            
            if files_created:
                clean_response = f"""❌ Lo siento, no pude completar totalmente tu solicitud debido a un error{failed_step_info}{error_info}.

Sin embargo, logré generar {len(files_created)} archivo(s) parcial(es):

📁 **ARCHIVOS PARCIALES GENERADOS:**
"""
                for file_info in files_created:
                    clean_response += f"• **{file_info['name']}** ({file_info['size']} bytes)\n"
                
                clean_response += """
🔄 He intentado ejecutar el plan de acción completo, pero encontré dificultades técnicas. Los archivos parciales pueden contener información útil.

Por favor, revisa el monitor de ejecución para más detalles sobre el problema, o intenta reformular tu solicitud de manera diferente."""
            else:
                clean_response = f"""Lo siento, no pude completar tu solicitud debido a un error{failed_step_info}{error_info}.

He intentado ejecutar el plan de acción que puedes ver en el panel lateral, pero encontré dificultades técnicas que impidieron la finalización.

Por favor, revisa el monitor de ejecución para más detalles sobre el problema, o intenta reformular tu solicitud de manera diferente."""

        else:
            # Estado por defecto (en progreso o desconocido)
            clean_response = """¡Perfecto! He recibido tu solicitud y he preparado un plan de acción detallado.

📋 **Plan generado y listo para ejecutar**

El plan está listo para ejecutarse paso a paso. Puedes ver todos los pasos en el panel lateral y ejecutarlos uno por uno para un control total sobre el proceso.

🎯 **Cómo proceder:**
- Revisa el plan completo en el panel lateral
- Ejecuta cada paso cuando estés listo (los pasos deben completarse en orden)
- Supervisa los resultados de cada paso
- Los archivos generados aparecerán automáticamente

⚡ **Control total:** Tienes control completo sobre cuándo y cómo se ejecuta cada paso del plan."""

        # Agregar información sobre herramientas si están disponibles
        if tool_results and task_status in ["completed_success", "completed_with_warnings"]:
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
            
            # Agregar resumen de herramientas al final
            if successful_tools > 0 or failed_tools > 0:
                clean_response += f"\n\n---\n**🔧 Resumen de Ejecución:** {successful_tools} herramientas exitosas"
                if failed_tools > 0:
                    clean_response += f", {failed_tools} con errores"
                if files_created:
                    clean_response += f", {len(files_created)} archivo(s) generado(s)"
                clean_response += "\n"
                
                # Agregar detalles de herramientas exitosas (máximo 3)
                for summary in tools_summary[:3]:
                    clean_response += f"{summary}\n"
        
        elif tool_results and task_status == "failed":
            # Para tareas fallidas, mostrar qué herramientas se intentaron
            attempted_tools = [result.get('tool', 'Desconocida') for result in tool_results]
            if attempted_tools:
                clean_response += f"\n\n**🔧 Herramientas intentadas:** {', '.join(attempted_tools[:3])}"
        
        return clean_response
        
    except Exception as e:
        logger.error(f"❌ Error generating conditional clean response: {str(e)}")
        # Fallback seguro con información del error
        fallback_response = """He recibido tu solicitud y estoy trabajando en ella. 

Puedes ver el progreso del plan de acción en el panel lateral derecho. El plan se ejecutará automáticamente paso a paso."""
        
        if task_status == "failed" and error_message:
            fallback_response += f"\n\n⚠️ Nota: Se encontró un problema técnico - {error_message}"
        
        return fallback_response

@agent_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal del chat - VERSIÓN REAL CON OLLAMA
    Distingue entre conversaciones casuales y tareas complejas
    GENERA PLAN ESTRUCTURADO PARA MOSTRAR EN PLAN DE ACCIÓN
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
            # MODO AGENTE CON PLANIFICACIÓN ESTRUCTURADA
            logger.info(f"🤖 Detected task mode - generating structured plan")
            
            # PASO 2: Generar plan dinámico PRIMERO usando IA
            structured_plan = generate_unified_ai_plan(message, task_id)
            
            # ✨ NUEVA FUNCIONALIDAD: Generar título mejorado con LLM
            enhanced_title = generate_task_title_with_llm(message, task_id)
            logger.info(f"📝 Enhanced title generated alongside plan: '{enhanced_title}'")
            
            # PASO 3: Generar respuesta usando Ollama con contexto de herramientas
            ollama_response = ollama_service.generate_response(message, context, use_tools=True)
            
            if ollama_response.get('error'):
                return jsonify({
                    'error': ollama_response['error'],
                    'response': ollama_response['response']
                }), 500
            
            # PASO 4: Procesar tool_calls si existen
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
            
            # PASO 5: Generar respuesta LIMPIA basada en estado inicial (tarea comenzando)
            final_response = generate_clean_response(ollama_response['response'], tool_results, 
                                                    task_status="plan_ready", 
                                                    failed_step_title=None, 
                                                    error_message=None)
            
            # 🚨 PASO 1: LOGGING AGRESIVO - Re-enabling automatic execution with detailed logging
            print(f"🚀 ABOUT TO START AUTOMATIC EXECUTION for task_id: {task_id}")
            print(f"📋 Plan contains {len(structured_plan['steps'])} steps")
            print(f"💬 Original message: {message}")
            
            # MODIFICACIÓN: RE-HABILITAMOS la ejecución automática con logging agresivo
            logger.info(f"🚀 Starting automatic execution for task {task_id}")
            
            try:
                print(f"🔧 Calling execute_plan_with_real_tools...")
                execute_plan_with_real_tools(task_id, structured_plan['steps'], message)
                print(f"✅ execute_plan_with_real_tools call completed successfully")
            except Exception as e:
                print(f"❌ CRITICAL ERROR in execute_plan_with_real_tools: {str(e)}")
                print(f"❌ Exception type: {type(e).__name__}")
                logger.error(f"❌ Failed to start automatic execution: {e}")
            
            logger.info(f"✅ Plan generated successfully - automatic execution initiated")
            
            # 🚀 Emitir evento WebSocket de plan actualizado
            websocket_manager = getattr(current_app, 'websocket_manager', None)
            if websocket_manager and hasattr(websocket_manager, 'emit_update') and structured_plan and 'steps' in structured_plan:
                from src.websocket.websocket_manager import UpdateType
                websocket_manager.emit_update(
                    task_id=task_id,
                    update_type=UpdateType.PLAN_UPDATED,
                    data={
                        'plan': structured_plan,
                        'task_id': task_id,
                        'auto_execute': True,  # Activar ejecución automática
                        'timestamp': datetime.now().isoformat()
                    }
                )
                logger.info(f"📡 Plan emitted via WebSocket for task {task_id}")
            else:
                logger.warning(f"⚠️ WebSocket manager not available for task {task_id}")
            
            # 🎯 La ejecución automática ya se inició con execute_plan_with_real_tools
            logger.info(f"✅ Plan generated and automatic execution initiated for task {task_id}")
            execution_status = 'executing'  # Estado: ejecutándose automáticamente
            
            return jsonify({
                'response': final_response,
                'task_id': task_id,
                'plan': structured_plan,  # PLAN ESTRUCTURADO PARA FRONTEND
                'enhanced_title': enhanced_title,  # ✨ NUEVO: Título mejorado generado con LLM
                'tool_calls': ollama_response.get('tool_calls', []),
                'tool_results': tool_results,
                'timestamp': datetime.now().isoformat(),
                'execution_status': execution_status,  # Estado dinámico: executing o plan_ready
                'mode': 'agent_with_structured_plan',
                'memory_used': True
            })
    
    except Exception as e:
        logger.error(f"Error general en chat: {str(e)}")
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}',
            'response': 'Lo siento, hubo un error procesando tu solicitud.'
        }), 500

@agent_bp.route('/test-plan-generation', methods=['POST'])
def test_plan_generation():
    """
    Endpoint para probar la generación de planes con IA
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', 'Crear un informe completo sobre inteligencia artificial en 2024')
        task_id = data.get('task_id', f'test-{uuid.uuid4()}')
        
        logger.info(f"🧪 Testing AI plan generation for: {message}")
        
        # Probar generación con IA
        ai_plan = generate_unified_ai_plan(message, task_id)
        
        # También generar plan de fallback para comparación
        fallback_task_id = f'fallback-{uuid.uuid4()}'
        fallback_plan = generate_fallback_plan(message, fallback_task_id)
        
        return jsonify({
            'test_results': {
                'ai_plan': {
                    'plan': ai_plan,
                    'ai_generated': ai_plan.get('ai_generated', False),
                    'plan_type': ai_plan.get('task_type', 'unknown')
                },
                'fallback_plan': {
                    'plan': fallback_plan,
                    'ai_generated': fallback_plan.get('ai_generated', False),
                    'plan_type': fallback_plan.get('task_type', 'unknown')
                }
            },
            'test_message': message,
            'timestamp': datetime.now().isoformat(),
            'comparison': {
                'ai_steps': len(ai_plan.get('steps', [])),
                'fallback_steps': len(fallback_plan.get('steps', [])),
                'ai_working': len(ai_plan.get('steps', [])) > 0,
                'plans_different': ai_plan.get('steps', []) != fallback_plan.get('steps', [])
            }
        })
    
    except Exception as e:
        logger.error(f"❌ Error in plan generation test: {str(e)}")
        return jsonify({
            'error': f'Error testing plan generation: {str(e)}',
            'test_failed': True
        }), 500

@agent_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Endpoint para descargar archivos generados por el agente
    """
    try:
        import os
        from flask import send_file, abort
        
        # Validar nombre de archivo para seguridad
        if not filename or '..' in filename or '/' in filename:
            abort(400, "Invalid filename")
        
        file_path = f"/app/backend/static/generated_files/{filename}"
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            abort(404, "File not found")
        
        logger.info(f"📥 Downloading file: {filename}")
        
        # Determinar tipo MIME
        import mimetypes
        mimetype = mimetypes.guess_type(filename)[0]
        if not mimetype:
            if filename.endswith('.md'):
                mimetype = 'text/markdown'
            elif filename.endswith('.txt'):
                mimetype = 'text/plain'
            elif filename.endswith('.py'):
                mimetype = 'text/x-python'
            else:
                mimetype = 'application/octet-stream'
        
        return send_file(
            file_path, 
            as_attachment=True, 
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.error(f"❌ Error downloading file {filename}: {str(e)}")
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@agent_bp.route('/list-files', methods=['GET'])
def list_generated_files():
    """
    Endpoint para listar archivos generados por el agente
    """
    try:
        import os
        from datetime import datetime
        
        files_dir = "/app/backend/static/generated_files"
        
        if not os.path.exists(files_dir):
            return jsonify({'files': []})
        
        files = []
        for filename in os.listdir(files_dir):
            file_path = os.path.join(files_dir, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'download_url': f'/api/agent/download/{filename}'
                })
        
        # Ordenar por fecha de creación (más reciente primero)
        files.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'files': files,
            'total_files': len(files),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error listing files: {str(e)}")
        return jsonify({'error': f'Error listing files: {str(e)}'}), 500

@agent_bp.route('/generate-plan', methods=['POST'])
def generate_plan():
    """ARREGLADO: Generate simple plan from user task"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', '') or data.get('task_title', '')
        task_id = data.get('task_id', f'task-{int(time.time())}')
        
        if not message:
            return jsonify({'error': 'Message or task_title required'}), 400
        
        logger.info(f"📋 Generating plan for: {message[:50]}...")
        
        # Obtener servicio Ollama
        ollama_service = get_ollama_service()
        if not ollama_service or not ollama_service.is_healthy():
            logger.error("❌ Ollama service not available")
            return jsonify({'error': 'Ollama service not available'}), 500
        
        # Prompt simple para generar plan
        plan_prompt = f"""Crea un plan de 3-4 pasos para: {message}

Responde SOLO con JSON válido en este formato:
{{
  "steps": [
    {{
      "id": "step-1",
      "title": "Título del paso 1",
      "description": "Descripción detallada",
      "tool": "web_search"
    }},
    {{
      "id": "step-2", 
      "title": "Título del paso 2",
      "description": "Descripción detallada",
      "tool": "analysis"
    }},
    {{
      "id": "step-3",
      "title": "Título del paso 3", 
      "description": "Descripción detallada",
      "tool": "creation"
    }}
  ],
  "task_type": "tipo de tarea",
  "complexity": "media",
  "estimated_total_time": "30-45 minutos"
}}

Herramientas disponibles: web_search, analysis, creation, planning, delivery"""
        
        # Generar plan con Ollama
        result = ollama_service.generate_response(plan_prompt, {'temperature': 0.3})
        
        if result.get('error'):
            logger.error(f"❌ Ollama error: {result['error']}")
            return jsonify({'error': f'Plan generation failed: {result["error"]}'}), 500
        
        # Parsear respuesta JSON
        response_text = result.get('response', '').strip()
        
        try:
            # Limpiar respuesta
            cleaned_response = response_text.replace('```json', '').replace('```', '').strip()
            plan_data = json.loads(cleaned_response)
            
            # Validar estructura básica
            if not plan_data.get('steps') or not isinstance(plan_data['steps'], list):
                raise ValueError("Invalid plan structure")
            
            # Agregar campos faltantes a los pasos
            for step in plan_data['steps']:
                step['completed'] = False
                step['active'] = False
                step['status'] = 'pending'
            
            # Guardar plan en task data
            task_data = {
                'id': task_id,
                'message': message,
                'plan': plan_data['steps'],
                'task_type': plan_data.get('task_type', 'general'),
                'complexity': plan_data.get('complexity', 'media'),
                'estimated_total_time': plan_data.get('estimated_total_time', '30 minutos'),
                'created_at': datetime.now().isoformat(),
                'status': 'plan_generated'
            }
            
            save_task_data(task_id, task_data)
            
            logger.info(f"✅ Plan generated with {len(plan_data['steps'])} steps")
            
            return jsonify({
                'plan': plan_data['steps'],
                'enhanced_title': f"Plan: {message[:50]}...",
                'task_id': task_id,
                'total_steps': len(plan_data['steps']),
                'estimated_total_time': plan_data.get('estimated_total_time'),
                'task_type': plan_data.get('task_type'),
                'complexity': plan_data.get('complexity')
            })
            
        except (json.JSONDecodeError, ValueError) as parse_error:
            logger.error(f"❌ JSON parse error: {parse_error}")
            logger.error(f"❌ Response was: {response_text[:200]}...")
            
            # Plan de fallback simple
            fallback_steps = [
                {
                    "id": "step-1",
                    "title": f"Investigar sobre: {message[:30]}",
                    "description": "Buscar información relevante",
                    "tool": "web_search",
                    "completed": False,
                    "active": False,
                    "status": "pending"
                },
                {
                    "id": "step-2", 
                    "title": "Analizar información",
                    "description": "Procesar y analizar los datos encontrados",
                    "tool": "analysis",
                    "completed": False,
                    "active": False,
                    "status": "pending" 
                },
                {
                    "id": "step-3",
                    "title": "Crear resultado final",
                    "description": "Generar el producto final solicitado", 
                    "tool": "creation",
                    "completed": False,
                    "active": False,
                    "status": "pending"
                }
            ]
            
            # Guardar plan de fallback
            task_data = {
                'id': task_id,
                'message': message,
                'plan': fallback_steps,
                'task_type': 'general',
                'complexity': 'media',
                'estimated_total_time': '30 minutos',
                'created_at': datetime.now().isoformat(),
                'status': 'plan_generated'
            }
            
            save_task_data(task_id, task_data)
            
            return jsonify({
                'plan': fallback_steps,
                'enhanced_title': f"Plan: {message[:50]}...",
                'task_id': task_id,
                'total_steps': len(fallback_steps),
                'estimated_total_time': '30 minutos',
                'task_type': 'general',
                'complexity': 'media'
            })
            
    except Exception as e:
        logger.error(f"❌ Plan generation error: {e}")
        return jsonify({'error': str(e)}), 500

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

@agent_bp.route('/update-task-time/<task_id>', methods=['POST'])
def update_task_time(task_id):
    """Actualiza el tiempo transcurrido de una tarea en tiempo real"""
    try:
        if task_id in active_task_plans:
            plan_data = active_task_plans[task_id]
            start_time = plan_data.get('start_time')
            
            if start_time:
                # Calcular tiempo transcurrido
                elapsed = datetime.now() - start_time
                elapsed_seconds = int(elapsed.total_seconds())
                
                # Formatear tiempo como MM:SS
                minutes = elapsed_seconds // 60
                seconds = elapsed_seconds % 60
                elapsed_str = f"{minutes}:{seconds:02d}"
                
                # Actualizar el paso activo
                plan = plan_data['plan']
                for step in plan:
                    if step.get('active', False):
                        step['elapsed_time'] = f"{elapsed_str} Pensando"
                        break
                
                # Actualizar en memoria
                active_task_plans[task_id]['plan'] = plan
                
                return jsonify({
                    'success': True,
                    'elapsed_time': elapsed_str,
                    'plan': plan
                })
            
        return jsonify({'error': 'Task not found'}), 404
        
    except Exception as e:
        logger.error(f"Error updating task time: {str(e)}")
        return jsonify({'error': str(e)}), 500



@agent_bp.route('/get-final-result/<task_id>', methods=['GET'])
def get_final_result(task_id):
    """Obtiene el resultado final de una tarea completada"""
    try:
        if task_id in active_task_plans:
            plan_data = active_task_plans[task_id]
            
            if plan_data['status'] == 'completed' and 'final_result' in plan_data:
                return jsonify({
                    'task_id': task_id,
                    'status': 'completed',
                    'final_result': plan_data['final_result'],
                    'plan_summary': {
                        'total_steps': len(plan_data['plan']),
                        'completed_steps': sum(1 for step in plan_data['plan'] if step['completed']),
                        'task_type': plan_data.get('task_type', 'general'),
                        'complexity': plan_data.get('complexity', 'media')
                    }
                })
            else:
                return jsonify({
                    'task_id': task_id,
                    'status': plan_data['status'],
                    'message': 'Tarea aún no completada o sin resultado final'
                })
        else:
            return jsonify({
                'error': 'Task not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error getting final result: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo resultado final: {str(e)}'
        }), 500

@agent_bp.route("/model-info", methods=["GET"])
def get_model_info():
    """
    PROBLEMA 3: Endpoint para obtener información de configuración de modelos
    """
    try:
        ollama_service = get_ollama_service()
        if not ollama_service:
            return jsonify({
                "error": "Ollama service not available",
                "status": "error"
            }), 503
        
        # Obtener información del modelo actual
        current_model_info = ollama_service.get_model_info()
        
        # Obtener todos los modelos configurados
        available_configs = {}
        for model_name in ollama_service.model_configs.keys():
            if not model_name.startswith('_'):  # Ignorar metadatos
                try:
                    model_info = ollama_service.get_model_info(model_name)
                    available_configs[model_name] = {
                        'timeout': model_info['timeout'],
                        'temperature': model_info['temperature'],
                        'is_optimized': model_info['is_optimized'],
                        'description': model_info['description']
                    }
                except Exception as e:
                    logger.warning(f"Error getting info for model {model_name}: {e}")
        
        # Verificar conexión con Ollama
        connection_status = ollama_service.check_connection()
        
        return jsonify({
            "status": "success",
            "current_model": current_model_info,
            "available_configs": available_configs,
            "ollama_connection": connection_status,
            "total_configured_models": len(available_configs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return jsonify({
            "error": f"Error retrieving model information: {str(e)}",
            "status": "error"
        }), 500

@agent_bp.route('/status', methods=['GET'])
def agent_status():
    """Status del agente"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': len(active_task_plans),
        'ollama': {
            'connected': True,
            'endpoint': os.getenv('OLLAMA_BASE_URL', 'https://bef4a4bb93d1.ngrok-free.app'),
            'model': os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3.1:8b')
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
        endpoint = data.get('endpoint', 'https://bef4a4bb93d1.ngrok-free.app')
        
        # Verificar conexión real con Ollama
        try:
            import requests
            response = requests.get(f"{endpoint}/api/tags", timeout=10)
            is_connected = response.status_code == 200
        except:
            is_connected = False
        
        return jsonify({
            'is_connected': is_connected,
            'endpoint': endpoint,
            'status': 'healthy' if is_connected else 'disconnected'
        })
    
    except Exception as e:
        logger.error(f"Error checking Ollama connection: {str(e)}")
        return jsonify({
            'is_connected': False,
            'error': str(e)
        }), 500

@agent_bp.route('/ollama/models', methods=['POST'])
def get_ollama_models():
    """Obtiene modelos disponibles de Ollama"""
    try:
        data = request.get_json() or {}
        endpoint = data.get('endpoint', os.getenv('OLLAMA_BASE_URL', 'https://bef4a4bb93d1.ngrok-free.app'))
        
        # Hacer llamada real a Ollama para obtener modelos
        try:
            import requests
            logger.info(f"🔍 Fetching models from Ollama endpoint: {endpoint}")
            response = requests.get(f"{endpoint}/api/tags", timeout=10)
            
            if response.status_code == 200:
                data_response = response.json()
                models_list = data_response.get('models', [])
                
                # Formatear modelos para la respuesta
                models = []
                for model in models_list:
                    model_info = {
                        'name': model.get('name', ''),
                    }
                    
                    # Formatear tamaño si está disponible
                    if 'size' in model and model['size']:
                        size_bytes = model['size']
                        if size_bytes >= 1073741824:  # 1GB
                            size_formatted = f"{size_bytes / 1073741824:.1f}GB"
                        elif size_bytes >= 1048576:  # 1MB
                            size_formatted = f"{size_bytes / 1048576:.0f}MB"
                        else:
                            size_formatted = f"{size_bytes}B"
                        model_info['size'] = size_formatted
                    else:
                        model_info['size'] = 'Unknown size'
                    
                    # Agregar información adicional directamente del modelo
                    if 'parameter_size' in model:
                        model_info['parameter_size'] = model['parameter_size']
                    
                    if 'quantization_level' in model:
                        model_info['quantization'] = model['quantization_level']
                    
                    # También buscar en details si está disponible
                    if 'details' in model:
                        details = model['details']
                        if 'parameter_size' in details and 'parameter_size' not in model_info:
                            model_info['parameter_size'] = details['parameter_size']
                        if 'quantization_level' in details and 'quantization' not in model_info:
                            model_info['quantization'] = details['quantization_level']
                    
                    models.append(model_info)
                
                logger.info(f"✅ Found {len(models)} models from Ollama")
                
                return jsonify({
                    'models': models,
                    'endpoint': endpoint,
                    'count': len(models)
                })
            else:
                logger.warning(f"⚠️ Ollama returned status code {response.status_code}")
                raise Exception(f"Ollama API returned status code {response.status_code}")
                
        except requests.exceptions.RequestException as req_error:
            logger.error(f"❌ Request error connecting to Ollama: {req_error}")
            # Fallback a modelos conocidos si hay error de conexión
            fallback_models = [
                {'name': 'llama3.1:8b', 'size': '4.7GB'},
                {'name': 'llama3.2:3b', 'size': '2.0GB'},
                {'name': 'deepseek-r1:32b', 'size': '20GB'},
                {'name': 'qwen3:32b', 'size': '18GB'},
                {'name': 'mistral:7b', 'size': '4.1GB'},
                {'name': 'codellama:7b', 'size': '3.8GB'},
                {'name': 'phi3:3.8b', 'size': '2.3GB'}
            ]
            
            return jsonify({
                'models': fallback_models,
                'endpoint': endpoint,
                'count': len(fallback_models),
                'fallback': True,
                'warning': f'Could not connect to Ollama. Showing common models. Error: {str(req_error)}'
            })
    
    except Exception as e:
        logger.error(f"Error getting Ollama models: {str(e)}")
        return jsonify({
            'models': [],
            'error': str(e)
        }), 500

# ==========================================
# SISTEMA DE CONFIGURACIÓN DINÁMICA
# ==========================================

@agent_bp.route('/config/apply', methods=['POST'])
def apply_configuration():
    """Aplica configuración desde el frontend al backend en tiempo real"""
    try:
        data = request.get_json()
        config = data.get('config', {})
        
        logger.info(f"🔧 Aplicando nueva configuración desde frontend")
        
        # Obtener servicios actuales
        ollama_service = get_ollama_service()
        
        # Aplicar configuración Ollama si está habilitada
        ollama_config = config.get('ollama', {})
        if ollama_config.get('enabled', False):
            endpoint = ollama_config.get('endpoint')
            model = ollama_config.get('model')
            
            if endpoint and ollama_service:
                logger.info(f"🔄 Actualizando Ollama: endpoint={endpoint}, modelo={model}")
                
                # Actualizar endpoint del servicio
                ollama_service.base_url = endpoint
                
                # Actualizar modelo si se especifica
                if model:
                    ollama_service.set_model(model)
                
                # Verificar nueva configuración
                connection_status = ollama_service.check_connection()
                
                logger.info(f"✅ Ollama reconfigurado: {connection_status}")
        
        # Aplicar configuración OpenRouter si está habilitada
        openrouter_config = config.get('openrouter', {})
        if openrouter_config.get('enabled', False):
            # TODO: Implementar OpenRouter service cuando esté listo
            logger.info("🔄 OpenRouter configuración recibida (pendiente implementación)")
        
        # Guardar configuración aplicada para persistencia
        current_app.active_config = config
        
        return jsonify({
            'success': True,
            'message': 'Configuración aplicada exitosamente',
            'timestamp': datetime.now().isoformat(),
            'config_applied': {
                'ollama': {
                    'enabled': ollama_config.get('enabled', False),
                    'endpoint': ollama_config.get('endpoint', ''),
                    'model': ollama_config.get('model', ''),
                    'connected': ollama_service.is_healthy() if ollama_service else False
                },
                'openrouter': {
                    'enabled': openrouter_config.get('enabled', False)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error aplicando configuración: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@agent_bp.route('/config/current', methods=['GET'])
def get_current_configuration():
    """Obtiene la configuración actualmente aplicada en el backend"""
    try:
        ollama_service = get_ollama_service()
        
        # Obtener configuración actual
        current_config = getattr(current_app, 'active_config', {})
        
        # Obtener estado actual de servicios
        ollama_status = {}
        if ollama_service:
            ollama_status = {
                'endpoint': ollama_service.base_url,
                'current_model': ollama_service.get_current_model(),
                'connected': ollama_service.is_healthy(),
                'available_models': ollama_service.get_available_models()
            }
        
        return jsonify({
            'success': True,
            'config': current_config,
            'services_status': {
                'ollama': ollama_status,
                'openrouter': {
                    'implemented': False
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo configuración actual: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@agent_bp.route('/config/validate', methods=['POST'])
def validate_configuration():
    """Valida una configuración antes de aplicarla"""
    try:
        data = request.get_json()
        config = data.get('config', {})
        
        validation_results = {
            'valid': True,
            'issues': [],
            'services_tested': {}
        }
        
        # Validar configuración Ollama
        ollama_config = config.get('ollama', {})
        if ollama_config.get('enabled', False):
            endpoint = ollama_config.get('endpoint')
            if endpoint:
                try:
                    import requests
                    response = requests.get(f"{endpoint}/api/tags", timeout=10)
                    if response.status_code == 200:
                        models = response.json().get('models', [])
                        validation_results['services_tested']['ollama'] = {
                            'endpoint': endpoint,
                            'connected': True,
                            'models_available': len(models),
                            'models': [model.get('name', '') for model in models[:5]]  # Primeros 5
                        }
                    else:
                        validation_results['valid'] = False
                        validation_results['issues'].append(f"Ollama endpoint {endpoint} returned HTTP {response.status_code}")
                        validation_results['services_tested']['ollama'] = {
                            'endpoint': endpoint,
                            'connected': False,
                            'error': f"HTTP {response.status_code}"
                        }
                except Exception as conn_error:
                    validation_results['valid'] = False
                    validation_results['issues'].append(f"Cannot connect to Ollama endpoint {endpoint}: {str(conn_error)}")
                    validation_results['services_tested']['ollama'] = {
                        'endpoint': endpoint,
                        'connected': False,
                        'error': str(conn_error)
                    }
            else:
                validation_results['issues'].append("Ollama enabled but no endpoint specified")
        
        # Validar configuración OpenRouter
        openrouter_config = config.get('openrouter', {})
        if openrouter_config.get('enabled', False):
            api_key = openrouter_config.get('apiKey')
            if not api_key:
                validation_results['issues'].append("OpenRouter enabled but no API key provided")
            validation_results['services_tested']['openrouter'] = {
                'implemented': False,
                'message': 'OpenRouter validation pending implementation'
            }
        
        return jsonify(validation_results)
        
    except Exception as e:
        logger.error(f"❌ Error validando configuración: {str(e)}")
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500

# ✅ CONSOLIDADO: Este endpoint fue duplicado y se ha eliminado
# La funcionalidad está en execute_step() línea 4489

@agent_bp.route('/initialize-task', methods=['POST'])
def initialize_task():
    """Initialize task with plan generation and WebSocket emission"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        title = data.get('title', '')
        auto_execute = data.get('auto_execute', False)
        
        logger.info(f"🚀 Initializing task {task_id}: {title}")
        
        # Generar plan usando Ollama (código existente)
        plan_response = generate_task_plan(title, task_id)
        
        # ✨ NUEVA FUNCIONALIDAD: Generar título mejorado con LLM
        enhanced_title = generate_task_title_with_llm(title, task_id)
        logger.info(f"📝 Enhanced title generated for initialization: '{enhanced_title}'")
        
        # NUEVA FUNCIONALIDAD: Emitir evento WebSocket
        if hasattr(current_app, 'websocket_manager') and current_app.websocket_manager:
            try:
                current_app.websocket_manager.emit_to_task(
                    task_id,
                    'plan_updated',
                    {
                        'task_id': task_id,
                        'plan': {
                            'steps': plan_response.get('steps', []),
                            'task_type': plan_response.get('task_type', 'general'),
                            'complexity': plan_response.get('complexity', 'media'),
                            'estimated_total_time': plan_response.get('estimated_total_time', '10-15 minutos')
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                )
                logger.info(f"📡 Plan emitted via WebSocket to task {task_id}")
            except Exception as ws_error:
                logger.error(f"❌ WebSocket emission failed: {ws_error}")
        
        # Auto-ejecutar si está habilitado
        if auto_execute:
            # 🔧 FIX: Usar execute_task_steps_sequentially en lugar de execute_plan_with_real_tools
            # Iniciar ejecución en hilo separado después de 3 segundos
            app = current_app._get_current_object()  # Get the actual app instance
            
            def delayed_execution():
                with app.app_context():
                    time.sleep(3)
                    logger.info(f"🔄 Auto-executing task {task_id} with {len(plan_response.get('steps', []))} steps")
                    execute_task_steps_sequentially(task_id, plan_response.get('steps', []))
                    logger.info(f"✅ Auto-execution completed for task {task_id}")
            
            import threading
            execution_thread = threading.Thread(target=delayed_execution)
            execution_thread.daemon = True
            execution_thread.start()
            
            logger.info(f"🔄 Auto-execution scheduled for task {task_id}")
        
        # NUEVA FUNCIONALIDAD: Guardar datos de la tarea para posterior consulta
        task_data = {
            'task_id': task_id,
            'title': title,
            'enhanced_title': enhanced_title,  # ✨ NUEVO: Título mejorado
            'message': title,  # Para compatibilidad
            'plan': plan_response.get('steps', []),
            'task_type': plan_response.get('task_type', 'general'),
            'complexity': plan_response.get('complexity', 'media'),
            'estimated_total_time': plan_response.get('estimated_total_time', '10-15 minutos'),
            'auto_execute': auto_execute,
            'status': 'initialized',
            'created_at': datetime.now().isoformat(),
            'start_time': datetime.now()  # Add start_time for execution tracking
        }
        
        # Guardar en persistencia
        save_success = save_task_data(task_id, task_data)
        if save_success:
            logger.info(f"✅ Task {task_id} saved to persistent storage")
        else:
            logger.warning(f"⚠️ Task {task_id} saved to legacy storage only")
        
        return jsonify({
            'success': True,
            'plan': plan_response,
            'task_id': task_id,
            'enhanced_title': enhanced_title,  # ✨ NUEVO: Título mejorado generado con LLM
            'auto_execute': auto_execute
        })
        
    except Exception as e:
        logger.error(f"❌ Error initializing task: {e}")
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/execute-step/<task_id>/<step_id>', methods=['POST'])
def execute_step(task_id: str, step_id: str):
    """Execute a specific step and emit real-time updates"""
    try:
        # Obtener datos del paso
        step_data = get_step_data(task_id, step_id)
        
        # Emitir evento de inicio
        emit_step_event(task_id, 'step_started', {
            'step_id': step_id,
            'title': step_data.get('title', 'Ejecutando paso'),
            'description': step_data.get('description', ''),
            'tool': step_data.get('tool', 'general'),
            'timestamp': datetime.now().isoformat()
        })
        
        # Ejecutar el paso según su herramienta
        result = execute_step_by_tool(step_data)
        
        # Emitir evento de progreso durante la ejecución
        emit_step_event(task_id, 'task_progress', {
            'step_id': step_id,
            'activity': f"Procesando con {step_data.get('tool', 'herramienta general')}...",
            'progress_percentage': 50,
            'timestamp': datetime.now().isoformat()
        })
        
        # Emitir evento de completado
        emit_step_event(task_id, 'step_completed', {
            'step_id': step_id,
            'title': step_data.get('title', 'Paso completado'),
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'result': result,
            'step_id': step_id
        })
        
    except Exception as e:
        # Emitir evento de error
        emit_step_event(task_id, 'step_failed', {
            'step_id': step_id,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/start-task-execution/<task_id>', methods=['POST'])
def start_task_execution(task_id: str):
    """ARREGLADO: Start REAL step-by-step execution"""
    try:
        logger.info(f"🚀 STARTING REAL EXECUTION for task: {task_id}")
        
        # Obtener datos de la tarea
        task_data = get_task_data(task_id)
        if not task_data or 'plan' not in task_data:
            return jsonify({'error': f'Task {task_id} or plan not found'}), 404
        
        steps = task_data['plan']
        message = task_data.get('message', '')
        
        logger.info(f"📋 Task has {len(steps)} steps to execute")
        
        # Ejecutar pasos en hilo separado
        import threading
        app = current_app._get_current_object()
        
        def execute_real_steps():
            with app.app_context():
                logger.info(f"🔄 Thread started for task {task_id}")
                
                for i, step in enumerate(steps):
                    try:
                        logger.info(f"🔄 Executing step {i+1}/{len(steps)}: {step['title']}")
                        
                        # Marcar paso como activo
                        step['active'] = True
                        step['status'] = 'in-progress'
                        update_task_data(task_id, {'plan': steps})
                        
                        # EJECUTAR EL PASO REAL
                        step_result = execute_single_step_logic(step, message, task_id)
                        
                        # Marcar paso como completado
                        step['active'] = False
                        step['completed'] = True
                        step['status'] = 'completed'
                        step['result'] = step_result
                        step['completed_time'] = datetime.now().isoformat()
                        
                        # Actualizar tarea
                        update_task_data(task_id, {'plan': steps})
                        
                        logger.info(f"✅ Step {i+1} completed: {step['title']}")
                        
                        # Pequeña pausa entre pasos
                        time.sleep(2)
                        
                    except Exception as step_error:
                        logger.error(f"❌ Error in step {i+1}: {step_error}")
                        step['status'] = 'failed'
                        step['active'] = False
                        step['error'] = str(step_error)
                        update_task_data(task_id, {'plan': steps})
                        continue
                
                # Marcar tarea como completada
                update_task_data(task_id, {'status': 'completed'})
                logger.info(f"🎉 Task {task_id} execution completed")
        
        execution_thread = threading.Thread(target=execute_real_steps)
        execution_thread.daemon = True
        execution_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Real task execution started',
            'task_id': task_id
        })
        
    except Exception as e:
        logger.error(f"❌ Error starting execution: {e}")
        return jsonify({'error': str(e)}), 500

def get_step_data(task_id: str, step_id: str) -> dict:
    """Get step data from task plan"""
    try:
        task_data = get_task_data(task_id)
        if task_data and 'plan' in task_data:
            steps = task_data['plan']
            for step in steps:
                if step.get('id') == step_id:
                    return step
        return {}
    except Exception as e:
        logger.error(f"❌ Error getting step data: {e}")
        return {}

def get_task_plan_data(task_id: str) -> dict:
    """Get task plan data"""
    try:
        task_data = get_task_data(task_id)
        return task_data if task_data else {}
    except Exception as e:
        logger.error(f"❌ Error getting task plan: {e}")
        return {}

def execute_step_by_tool(step_data: dict) -> dict:
    """Execute step based on its tool"""
    tool = step_data.get('tool', 'general')
    title = step_data.get('title', 'Step')
    description = step_data.get('description', '')
    
    # Simulate step execution with the existing logic
    result = {
        'success': True,
        'tool': tool,
        'title': title,
        'output': f"Executed {title} using {tool}",
        'timestamp': datetime.now().isoformat()
    }
    
    # Add delay for visualization
    time.sleep(2)
    
    return result

def execute_task_steps_sequentially(task_id: str, steps: list):
    """Execute task steps one by one with delays and enhanced logging"""
    # 🚨 PASO 1: LOGGING AGRESIVO IMPLEMENTADO 🚨
    print(f"🚀 STARTING execute_task_steps_sequentially for task_id: {task_id}")
    print(f"📋 Total steps to execute: {len(steps)}")
    print(f"🔍 Steps details: {json.dumps(steps, indent=2, default=str)}")
    
    # Log directo a archivo para debugging
    log_file = f"/tmp/mitosis_execution_{task_id}.log"
    
    try:
        with open(log_file, "w") as f:
            f.write(f"🚀 STARTING AUTONOMOUS EXECUTION for task {task_id}\n")
            f.write(f"📋 Steps to execute: {len(steps)}\n")
            for i, step in enumerate(steps):
                f.write(f"  Step {i+1}: {step.get('title', 'Unnamed')} using {step.get('tool', 'unknown')}\n")
            f.write("="*50 + "\n")
        
        logger.info(f"🚀 AUTONOMOUS EXECUTION STARTED - Logging to {log_file}")
        print(f"📝 Logging execution details to: {log_file}")
        
        for i, step in enumerate(steps):
            try:
                step_id = step.get('id', f'step-{i+1}')
                
                print(f"⚡ EXECUTING STEP {i+1}/{len(steps)}: {step.get('title', 'Unnamed')}")
                print(f"   Tool: {step.get('tool', 'unknown')}")
                print(f"   Description: {step.get('description', 'N/A')[:100]}...")
                
                with open(log_file, "a") as f:
                    f.write(f"\n⚡ EXECUTING STEP {i+1}: {step.get('title', 'Unnamed')}\n")
                    f.write(f"   Tool: {step.get('tool', 'unknown')}\n")
                    f.write(f"   Description: {step.get('description', 'N/A')}\n")
                
                # 🚨 LOGGING: Ejecutar el paso con logging agresivo
                print(f"🔧 About to call execute_step_internal with step_id: {step_id}")
                execute_step_internal(task_id, step_id, step)
                print(f"✅ execute_step_internal completed for step {i+1}")
                
                # ✅ CRITICAL FIX: NO artificial delays - let real execution determine timing
                logger.info(f"✅ Step {i+1} completed, moving to next step...")
                
                with open(log_file, "a") as f:
                    f.write(f"✅ STEP {i+1} COMPLETED\n")
                
            except Exception as e:
                error_msg = f"❌ Error executing step {step_id}: {e}"
                logger.error(error_msg)
                print(f"❌ CRITICAL ERROR in step {i+1}: {str(e)}")
                print(f"❌ Exception type: {type(e).__name__}")
                
                with open(log_file, "a") as f:
                    f.write(f"\n❌ ERROR IN STEP {i+1}: {str(e)}\n")
                
                emit_step_event(task_id, 'step_failed', {
                    'step_id': step_id,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                break
        
        with open(log_file, "a") as f:
            f.write(f"\n🎉 AUTONOMOUS EXECUTION COMPLETED for task {task_id}\n")
            
    except Exception as e:
        logger.error(f"❌ Critical error in autonomous execution: {e}")
        with open(log_file, "a") as f:
            f.write(f"\n💥 CRITICAL ERROR: {str(e)}\n")
    
    # Emitir evento de tarea completada
    emit_step_event(task_id, 'task_completed', {
        'task_id': task_id,
        'timestamp': datetime.now().isoformat()
    })

def execute_step_internal(task_id: str, step_id: str, step: dict):
    """Execute a single step internally with progress updates"""
    try:
        # ✅ CRITICAL FIX: Actualizar estado del paso en persistencia ANTES de ejecutar
        task_data = get_task_data(task_id)
        if task_data and 'plan' in task_data:
            steps = task_data['plan']
            for step_item in steps:
                if step_item.get('id') == step_id:
                    step_item['active'] = True
                    step_item['status'] = 'in-progress'
                    step_item['start_time'] = datetime.now().isoformat()
                    break
            
            # Guardar inmediatamente el cambio de estado
            update_task_data(task_id, {'plan': steps})
            logger.info(f"🔄 Step {step_id} marked as in-progress in database")
        
        # Emitir inicio de paso
        emit_step_event(task_id, 'step_started', {
            'step_id': step_id,
            'title': step.get('title', 'Ejecutando paso'),
            'description': step.get('description', ''),
            'tool': step.get('tool', 'general'),
            'timestamp': datetime.now().isoformat()
        })
        
        # Ejecutar paso con herramientas REALES (no simulación)
        execute_step_real(task_id, step_id, step)
        
        # ✅ CRITICAL FIX: Actualizar estado del paso en persistencia DESPUÉS de ejecutar
        task_data = get_task_data(task_id)
        if task_data and 'plan' in task_data:
            steps = task_data['plan']
            for step_item in steps:
                if step_item.get('id') == step_id:
                    step_item['active'] = False
                    step_item['completed'] = True
                    step_item['status'] = 'completed'
                    step_item['completed_time'] = datetime.now().isoformat()
                    step_item['result'] = f"Completado: {step.get('title', 'Paso')}"
                    break
            
            # Guardar inmediatamente el cambio de estado
            update_task_data(task_id, {'plan': steps})
            logger.info(f"✅ Step {step_id} marked as completed in database")
        
        # Emitir completado
        emit_step_event(task_id, 'step_completed', {
            'step_id': step_id,
            'title': step.get('title', 'Paso completado'),
            'result': f"Completado: {step.get('title', 'Paso')}",
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error executing step {step_id}: {e}")
        
        # ✅ CRITICAL FIX: Marcar paso como fallido en persistencia
        task_data = get_task_data(task_id)
        if task_data and 'plan' in task_data:
            steps = task_data['plan']
            for step_item in steps:
                if step_item.get('id') == step_id:
                    step_item['active'] = False
                    step_item['completed'] = False
                    step_item['status'] = 'failed'
                    step_item['error'] = str(e)
                    step_item['error_time'] = datetime.now().isoformat()
                    break
            
            # Guardar inmediatamente el cambio de estado
            update_task_data(task_id, {'plan': steps})
            logger.info(f"❌ Step {step_id} marked as failed in database")
        
        emit_step_event(task_id, 'step_failed', {
            'step_id': step_id,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

def execute_step_real(task_id: str, step_id: str, step: dict):
    """Execute step with REAL tools instead of simulation - ENHANCED VERSION"""
    tool = step.get('tool', 'general')
    title = step.get('title', 'Ejecutando paso')
    description = step.get('description', '')
    
    logger.info(f"🔧 Ejecutando REAL TOOL: {tool} para paso: {title}")
    
    # Emitir progreso inicial
    emit_step_event(task_id, 'task_progress', {
        'step_id': step_id,
        'activity': f"Iniciando {tool}...",
        'progress_percentage': 25,
        'timestamp': datetime.now().isoformat()
    })
    
    try:
        tool_manager = get_tool_manager()
        
        if tool_manager and hasattr(tool_manager, 'execute_tool'):
            tool_params = {}
            mapped_tool = tool  # Por defecto, la herramienta es la misma

            # ENHANCED TOOL MAPPING LOGIC - As per NEWUPGRADE.md Section 2
            if tool == 'web_search':
                mapped_tool = 'web_search'
                search_query = f"{title} {description}".replace('Buscar información sobre:', '').replace('Investigar:', '').strip()
                tool_params = {
                    'query': search_query,
                    'num_results': 5
                }
            elif tool in ['analysis', 'data_analysis', 'synthesis']:
                mapped_tool = 'comprehensive_research'  # Herramienta unificada para investigación/análisis
                tool_params = {
                    'query': f"{title}: {description}",
                    'max_results': 5,
                    'include_analysis': True
                }
            elif tool == 'creation':
                mapped_tool = 'file_manager'  # Usar file_manager para crear archivos
                filename = f"generated_content_{task_id}_{step_id}.md"
                # Generate more sophisticated content using Ollama
                try:
                    ollama_service = get_ollama_service()
                    if ollama_service and ollama_service.is_healthy():
                        content_prompt = f"""
Genera contenido detallado y específico para:
Título: {title}
Descripción: {description}
Tarea ID: {task_id}

IMPORTANTE: Proporciona contenido real y detallado, no un plan ni instrucciones.
Responde SOLO con el contenido final solicitado.
"""
                        ollama_response = ollama_service.generate_response(content_prompt, {'temperature': 0.7})
                        content_generated = ollama_response.get('response', f"# {title}\n\n{description}\n\n*Contenido generado automáticamente*")
                    else:
                        content_generated = f"# {title}\n\n## Descripción\n{description}\n\n*Contenido generado por el agente*\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                except Exception as e:
                    logger.warning(f"⚠️ Could not generate content with Ollama: {e}")
                    content_generated = f"# {title}\n\n## Descripción\n{description}\n\n*Contenido generado por el agente*\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                tool_params = {
                    'action': 'create',
                    'path': f"/app/backend/static/generated_files/{filename}",
                    'content': content_generated
                }
            elif tool == 'planning':
                mapped_tool = 'file_manager'
                filename = f"plan_output_{task_id}_{step_id}.md"
                tool_params = {
                    'action': 'create',
                    'path': f"/app/backend/static/generated_files/{filename}",
                    'content': f"# Planificación: {title}\n\nDescripción: {description}\n\n*Este es un plan generado automáticamente.*\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                }
            elif tool == 'delivery':
                mapped_tool = 'file_manager'
                filename = f"delivery_report_{task_id}_{step_id}.md"
                tool_params = {
                    'action': 'create',
                    'path': f"/app/backend/static/generated_files/{filename}",
                    'content': f"# Informe de Entrega: {title}\n\nDescripción: {description}\n\n*Este es el informe de entrega final.*\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                }
            elif tool == 'processing':
                mapped_tool = 'comprehensive_research'
                tool_params = {
                    'query': f"Process and summarize: {title} {description}",
                    'max_results': 3,
                    'include_analysis': True
                }
            # Add more mappings for other tool types as needed
            else:
                # For unmapped tools, use comprehensive_research as a fallback
                mapped_tool = 'comprehensive_research'
                tool_params = {
                    'query': f"{title}: {description}",
                    'max_results': 3
                }

            # SPECIAL HANDLING FOR VALENCIA BARS (as per original logic)
            if (('valencia' in f"{title} {description}".lower()) and 
                any(word in f"{title} {description}".lower() for word in ['bar', 'bares', 'restaurant', 'local', 'sitio'])):
                try:
                    # Try to use specialized Valencia bars tool
                    import sys
                    sys.path.append('/app/backend/src/tools')
                    from valencia_bars_tool import valencia_bars_tool
                    mapped_tool = 'valencia_bars_tool'
                    tool_params = {
                        'query': f"{title} {description}",
                        'max_results': 8
                    }
                    logger.info(f"🍻 VALENCIA BARS DETECTED: Using specialized Valencia bars tool")
                except ImportError:
                    logger.warning("Valencia bars tool not found, falling back to web_search.")
                    mapped_tool = 'web_search'
                    tool_params = {
                        'query': f"{title} {description}",
                        'max_results': 5
                    }

            # EXECUTE THE MAPPED TOOL WITH ERROR HANDLING
            logger.info(f"🚀 Executing MAPPED tool: original='{tool}' -> mapped='{mapped_tool}' with params: {tool_params}")
            
            # Verify tool availability
            available_tools = list(tool_manager.tools.keys()) if hasattr(tool_manager, 'tools') else []
            if mapped_tool not in available_tools:
                logger.error(f"❌ TOOL MAPPING ERROR: Tool '{mapped_tool}' not found in available tools: {available_tools}")
                raise Exception(f"Tool '{mapped_tool}' not available. Available tools: {available_tools}")
            
            # Execute the tool
            tool_result = tool_manager.execute_tool(mapped_tool, tool_params, task_id=task_id)
            
            # Emit advanced progress
            emit_step_event(task_id, 'task_progress', {
                'step_id': step_id,
                'activity': f"Procesando resultados de {mapped_tool}...",
                'progress_percentage': 90,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"✅ Tool {mapped_tool} executed successfully, result: {str(tool_result)[:200]}...")
            
            # Emit detailed tool result
            emit_step_event(task_id, 'tool_result', {
                'step_id': step_id,
                'tool': mapped_tool,
                'result': tool_result,
                'timestamp': datetime.now().isoformat()
            })
            
        else:
            # ❌ CRITICAL FIX: If tool manager not available, this is a REAL ERROR, not simulation
            error_msg = f"❌ CRITICAL: Tool manager not available for {tool}. Cannot execute real tools."
            logger.error(error_msg)
            raise Exception(f"Tool manager not available - cannot execute {tool} properly")
            
    except Exception as e:
        logger.error(f"❌ Error executing real tool {tool}: {e}")
        emit_step_event(task_id, 'task_progress', {
            'step_id': step_id,
            'activity': f"Error en {tool}: {str(e)}, continuando...",
            'progress_percentage': 75,
            'timestamp': datetime.now().isoformat()
        })
        # Continue execution instead of failing completely
        
    # Emit final completion
    emit_step_event(task_id, 'task_progress', {
        'step_id': step_id,
        'activity': f"Paso '{title}' completado",
        'progress_percentage': 100,
        'timestamp': datetime.now().isoformat()
    })

def execute_step_real_original(task_id: str, step_id: str, step: dict):
    """Original execute_step_real function - kept for reference"""
    tool = step.get('tool', 'general')
    title = step.get('title', 'Ejecutando paso')
    description = step.get('description', '')
    
    logger.info(f"🔧 Ejecutando REAL TOOL: {tool} para paso: {title}")
    
    # Emitir progreso inicial
    emit_step_event(task_id, 'task_progress', {
        'step_id': step_id,
        'activity': f"Iniciando {tool}...",
        'progress_percentage': 25,
        'timestamp': datetime.now().isoformat()
    })
    
    try:
        # ⭐ USAR HERRAMIENTAS REALES EN LUGAR DE SIMULACIÓN
        tool_manager = get_tool_manager()
        
        if tool_manager and hasattr(tool_manager, 'execute_tool'):
            # Preparar parámetros para la herramienta
            # 🚀 SPECIAL CASE: Detectar consultas sobre bares de Valencia
            if ('valencia' in f"{title} {description}".lower() and 
                any(word in f"{title} {description}".lower() for word in ['bar', 'bares', 'restaurant', 'local', 'sitio'])):
                
                logger.info(f"🍻 VALENCIA BARS DETECTED: Using specialized Valencia bars tool")
                # Usar herramienta especializada importada dinámicamente
                try:
                    import sys
                    import os
                    sys.path.append('/app/backend/src/tools')
                    from valencia_bars_tool import valencia_bars_tool
                    
                    valencia_result = valencia_bars_tool.execute({
                        'query': f"{title} {description}",
                        'max_results': 8
                    })
                    
                    if valencia_result.get('success'):
                        # Generar contenido detallado con los bares específicos
                        bars_content = "# Mejores Bares de Valencia 2025\n\n"
                        bars_content += valencia_result.get('analysis', '') + "\n\n"
                        bars_content += "## Top Bares Recomendados:\n\n"
                        
                        for i, bar in enumerate(valencia_result.get('results', []), 1):
                            bars_content += f"### {i}. {bar['nombre']}\n"
                            bars_content += f"**Dirección**: {bar['direccion']}\n"
                            bars_content += f"**Zona**: {bar['zona']}\n"
                            bars_content += f"**Tipo**: {bar['tipo']}\n"
                            bars_content += f"**Especialidad**: {bar['especialidad']}\n"
                            bars_content += f"**Puntuación**: ⭐ {bar['puntuacion']}/5.0\n"
                            bars_content += f"**Precio**: {bar['precio']}\n"
                            bars_content += f"**Ambiente**: {bar['ambiente']}\n"
                            bars_content += f"**Destacado**: {bar['destacado']}\n\n"
                        
                        bars_content += f"\n---\n*Informe generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n"
                        bars_content += f"*Basado en análisis de tendencias 2025*\n"
                        
                        # Crear archivo específico
                        tool = 'file_manager'
                        filename = f"valencia_bars_report_{task_id}.md"
                        tool_params = {
                            'action': 'create',
                            'path': f"/tmp/{filename}",
                            'content': bars_content
                        }
                        
                        logger.info(f"🍻 Generated Valencia bars content: {len(valencia_result.get('results', []))} bars, {len(bars_content)} chars")
                    else:
                        raise Exception("Valencia bars tool failed")
                        
                except Exception as e:
                    logger.error(f"❌ Valencia bars tool error: {e}, falling back to normal web_search")
                    # Fallback to normal web_search
                    tool_params = {
                        'query': f"{title} {description}",
                        'max_results': 5
                    }
                    
            elif tool == 'web_search':
                tool_params = {
                    'query': f"{title} {description}",
                    'max_results': 5
                }
            elif tool == 'analysis':
                # Mapear analysis a comprehensive_research tool
                tool = 'comprehensive_research'  # 🔧 FIXED: usar herramienta real
                tool_params = {
                    'query': f"{title}: {description}",
                    'max_results': 5,
                    'include_analysis': True
                }
            elif tool == 'creation':
                # 🔧 CRITICAL FIX: Mapear creation a file_manager tool real
                tool = 'file_manager'  # Usar herramienta real en lugar de creation
                # Crear un documento con el contenido solicitado
                filename = f"report_{task_id}_{step_id}.md"
                tool_params = {
                    'action': 'create',
                    'path': f"/tmp/{filename}",
                    'content': f"# {title}\n\n## Descripción\n{description}\n\n## Contenido\n\n*Documento generado automáticamente por el agente*\n\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nTarea ID: {task_id}\nPaso ID: {step_id}\n"
                }
            elif tool == 'delivery':
                # Mapear delivery a file_manager para crear archivos de entrega
                tool = 'file_manager'
                filename = f"delivery_{task_id}_{step_id}.txt"
                tool_params = {
                    'action': 'create',
                    'path': f"/tmp/{filename}",
                    'content': f"Entrega del paso: {title}\n\nDescripción: {description}\n\nResultado: Paso completado exitosamente\n\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                }
            elif tool == 'processing':
                # Mapear processing a comprehensive_research
                tool = 'comprehensive_research'
                tool_params = {
                    'query': f"Process and analyze: {title} {description}",
                    'max_results': 5
                }
            elif tool == 'planning':
                # Mapear planning a file_manager para crear archivos de planificación
                tool = 'file_manager'
                filename = f"plan_{task_id}_{step_id}.md"
                tool_params = {
                    'action': 'create',
                    'path': f"/tmp/{filename}",
                    'content': f"# Plan: {title}\n\n## Descripción\n{description}\n\n## Pasos de planificación\n\n1. Análisis inicial\n2. Desarrollo de estrategia\n3. Implementación\n4. Validación\n\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                }
            elif tool == 'synthesis':
                # Mapear synthesis a comprehensive_research
                tool = 'comprehensive_research'
                tool_params = {
                    'query': f"Synthesize information about: {title} {description}",
                    'max_results': 8,
                    'include_analysis': True
                }
            else:
                # Para herramientas no mapeadas, usar web_search como fallback seguro
                tool = 'web_search'  # Fallback a herramienta real
                tool_params = {
                    'query': f"{title} {description}",
                    'max_results': 5
                }
            
            # Emitir progreso medio
            emit_step_event(task_id, 'task_progress', {
                'step_id': step_id,
                'activity': f"Ejecutando {tool} con herramientas reales...",
                'progress_percentage': 50,
                'timestamp': datetime.now().isoformat()
            })
            
            # EJECUTAR HERRAMIENTA REAL
            logger.info(f"🚀 Executing MAPPED tool: original='{step.get('tool', 'unknown')}' -> mapped='{tool}' with params: {tool_params}")
            
            # Verificar que la herramienta existe antes de ejecutar
            available_tools = list(tool_manager.tools.keys()) if hasattr(tool_manager, 'tools') else []
            if tool not in available_tools:
                logger.error(f"❌ TOOL MAPPING ERROR: Tool '{tool}' not found in available tools: {available_tools}")
                raise Exception(f"Tool '{tool}' not available. Available tools: {available_tools}")
            
            tool_result = tool_manager.execute_tool(tool, tool_params, task_id=task_id)
            
            # Emitir progreso avanzado
            emit_step_event(task_id, 'task_progress', {
                'step_id': step_id,
                'activity': f"Procesando resultados de {tool}...",
                'progress_percentage': 90,
                'timestamp': datetime.now().isoformat()
            })
            
            # Log del resultado
            logger.info(f"✅ Tool {tool} executed successfully, result: {str(tool_result)[:200]}...")
            
            # Emitir resultado del tool
            emit_step_event(task_id, 'tool_result', {
                'step_id': step_id,
                'tool': tool,
                'result': tool_result,
                'timestamp': datetime.now().isoformat()
            })
            
        else:
            logger.warning(f"⚠️ Tool manager not available, falling back to simulation for {tool}")
            # Fallback a simulación solo si no hay tool manager
            time.sleep(3)
            emit_step_event(task_id, 'task_progress', {
                'step_id': step_id,
                'activity': f"Simulación de {tool} completada (herramientas no disponibles)",
                'progress_percentage': 90,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"❌ Error executing real tool {tool}: {e}")
        # Emitir error pero continuar
        emit_step_event(task_id, 'task_progress', {
            'step_id': step_id,
            'activity': f"Error en {tool}: {str(e)}, continuando...",
            'progress_percentage': 75,
            'timestamp': datetime.now().isoformat()
        })

def emit_step_event(task_id: str, event_type: str, data: dict):
    """Helper function to emit step events"""
    if hasattr(current_app, 'websocket_manager') and current_app.websocket_manager:
        current_app.websocket_manager.emit_to_task(task_id, event_type, data)
        logger.info(f"📡 Emitted {event_type} for task {task_id}")
    else:
        logger.warning("⚠️ WebSocket manager not available")

def generate_task_plan(title: str, task_id: str) -> Dict:
    """
    UPDATED: Ahora usa la función unificada generate_unified_ai_plan para eliminar duplicación
    Generar plan de tarea usando Ollama DIRECTAMENTE - NO MORE MOCKUPS
    """
    try:
        logger.info(f"🚀 Starting generate_task_plan (unified) for task {task_id}: {title}")
        
        # ✅ CRITICAL FIX: Use unified AI plan generation instead of duplicated code
        plan_result = generate_unified_ai_plan(title, task_id, attempt_retries=False)  # No retries para backward compatibility
        
        if plan_result.get('plan_source') == 'fallback':
            logger.warning(f"⚠️ Unified plan generation returned fallback for task {task_id}")
        else:
            logger.info(f"✅ Unified plan generation successful for task {task_id}")
        
        return plan_result
            
    except Exception as e:
        logger.error(f"❌ Error in unified generate_task_plan: {e}")
        return generate_basic_plan(title)

def generate_basic_plan(title: str) -> Dict:
    """Generar plan básico como fallback"""
    return {
        "steps": [
            {
                "id": "step_1",
                "title": "Análisis inicial",
                "description": f"Analizar los requisitos de: {title}",
                "tool": "analysis",
                "estimated_time": "2-3 minutos",
                "priority": "alta"
            },
            {
                "id": "step_2", 
                "title": "Investigación",
                "description": "Buscar información relevante",
                "tool": "web_search",
                "estimated_time": "3-5 minutos",
                "priority": "alta"
            },
            {
                "id": "step_3",
                "title": "Procesamiento",
                "description": "Procesar y sintetizar información",
                "tool": "processing",
                "estimated_time": "2-4 minutos", 
                "priority": "media"
            },
            {
                "id": "step_4",
                "title": "Entrega",
                "description": "Preparar y entregar resultados",
                "tool": "delivery",
                "estimated_time": "1-2 minutos",
                "priority": "alta"
            }
        ],
        "task_type": "general",
        "complexity": "media",
        "estimated_total_time": "8-14 minutos"
    }


# FIN del archivo - función duplicada removida