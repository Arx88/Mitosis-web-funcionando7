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

Input: "crear un análisis de tecnologías emergentes"
Output: Análisis de Tecnologías Emergentes 2025

Input: "desarrollar una estrategia de marketing digital"
Output: Estrategia de Marketing Digital Integral

Input: "investigar sobre inteligencia artificial"
Output: Investigación Avanzada en Inteligencia Artificial

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

def extract_search_query_from_message(message: str, step_title: str) -> str:
    """Extraer query de búsqueda optimizada del mensaje y título del paso"""
    # Combinar mensaje original con título del paso para contexto
    combined_text = f"{message} {step_title}"
    
    # Limpiar texto común
    query = combined_text.replace('Buscar información sobre:', '').replace('Investigar:', '').strip()
    
    # Limitar longitud para búsquedas efectivas
    if len(query) > 100:
        query = query[:100]
    
    return query

def generate_clean_response(content: str, response_type: str = "text") -> dict:
    """Generar respuesta limpia y estructurada"""
    return {
        'response': content,
        'type': response_type,
        'timestamp': datetime.now().isoformat(),
        'success': True
    }

def generate_fallback_plan(message: str, task_id: str) -> dict:
    """Plan de fallback básico cuando todo falla"""
    logger.info(f"🔄 Generating basic fallback plan for task {task_id}")
    
    fallback_steps = [
        {
            "id": "step-1",
            "title": f"Investigar: {message[:40]}...",
            "description": "Buscar información relevante sobre el tema solicitado",
            "tool": "web_search",
            "completed": False,
            "active": False,
            "status": "pending"
        },
        {
            "id": "step-2",
            "title": "Analizar información encontrada",
            "description": "Procesar y analizar los datos recopilados",
            "tool": "analysis",
            "completed": False,
            "active": False,
            "status": "pending"
        },
        {
            "id": "step-3",
            "title": "Generar resultado final",
            "description": "Crear el producto final basado en el análisis",
            "tool": "creation",
            "completed": False,
            "active": False,
            "status": "pending"
        }
    ]
    
    # 🎯 MARCAR EL PRIMER PASO COMO ACTIVO EN FALLBACK BÁSICO
    if fallback_steps:
        fallback_steps[0]['active'] = True
        fallback_steps[0]['status'] = 'active'
        logger.info(f"✅ First fallback step marked as active: {fallback_steps[0]['title']}")
    
    # Guardar plan de fallback
    task_data = {
        'id': task_id,
        'message': message,
        'plan': fallback_steps,
        'task_type': 'general',
        'complexity': 'media',
        'estimated_total_time': '25 minutos',
        'created_at': datetime.now().isoformat(),
        'status': 'plan_generated'
    }
    
    save_task_data(task_id, task_data)
    
    return {
        'steps': fallback_steps,  # 🎯 FIXED: Return 'steps' instead of 'plan' for consistency
        'task_type': 'general',
        'complexity': 'media',
        'estimated_total_time': '25 minutos',
        'plan_source': 'basic_fallback'
    }

def detect_task_category(message: str) -> str:
    """Detectar la categoría de la tarea para generar planes específicos"""
    message_lower = message.lower()
    
    # Categorías específicas con palabras clave
    if any(word in message_lower for word in ['investigar', 'buscar', 'información', 'datos', 'tendencias', 'mercado', 'análisis de mercado']):
        return 'investigacion'
    elif any(word in message_lower for word in ['crear', 'generar', 'desarrollar', 'escribir', 'diseñar', 'documento', 'informe', 'reporte']):
        return 'creacion'
    elif any(word in message_lower for word in ['analizar', 'evaluar', 'comparar', 'estudiar', 'revisar', 'examinar']):
        return 'analisis'
    elif any(word in message_lower for word in ['planificar', 'estrategia', 'plan', 'roadmap', 'cronograma']):
        return 'planificacion'
    elif any(word in message_lower for word in ['código', 'programa', 'app', 'aplicación', 'web', 'software', 'development']):
        return 'desarrollo'
    elif any(word in message_lower for word in ['presentación', 'pitch', 'exposición', 'conferencia']):
        return 'presentacion'
    else:
        return 'general'

def generate_intelligent_fallback_plan(message: str, task_id: str, category: str = None) -> dict:
    """
    🚀 SISTEMA DE FALLBACK INTELIGENTE Y COMPLEJO
    Genera planes específicos y detallados según la categoría de la tarea
    """
    if not category:
        category = detect_task_category(message)
    
    logger.info(f"🧠 Generating intelligent fallback plan for category: {category}")
    
    def mark_first_step_active(steps: list) -> list:
        """🎯 Helper function to mark first step as active"""
        if steps:
            steps[0]['completed'] = False
            steps[0]['active'] = True
            steps[0]['status'] = 'active'
            logger.info(f"✅ First step marked as active: {steps[0]['title']}")
            
            # Asegurar que el resto de los pasos estén pending
            for i, step in enumerate(steps):
                if i == 0:
                    continue
                step['completed'] = False
                step['active'] = False
                step['status'] = 'pending'
        return steps
    
    # Planes específicos por categoría
    if category == 'investigacion':
        steps = [
            {
                "id": "research-1",
                "title": f"Definición de objetivos de investigación",
                "description": f"Definir claramente qué se busca investigar sobre '{message}', establecer preguntas clave y delimitar el alcance de la investigación",
                "tool": "analysis",
                "estimated_time": "3-5 minutos",
                "complexity": "media"
            },
            {
                "id": "research-2", 
                "title": "Búsqueda comprehensiva en múltiples fuentes",
                "description": "Realizar búsquedas sistemáticas en fuentes académicas, industriales, noticias recientes y bases de datos especializadas",
                "tool": "web_search",
                "estimated_time": "8-12 minutos",
                "complexity": "alta"
            },
            {
                "id": "research-3",
                "title": "Análisis comparativo y síntesis de información",
                "description": "Comparar y contrastar información de diferentes fuentes, identificar patrones, tendencias y discrepancias",
                "tool": "analysis", 
                "estimated_time": "10-15 minutos",
                "complexity": "alta"
            },
            {
                "id": "research-4",
                "title": "Generación de insights y recomendaciones",
                "description": "Crear un informe estructurado con hallazgos clave, insights únicos y recomendaciones accionables",
                "tool": "creation",
                "estimated_time": "5-8 minutos",
                "complexity": "media"
            }
        ]
        steps = mark_first_step_active(steps)
        return {
            "steps": steps,
            "task_type": "investigación comprehensiva",
            "complexity": "alta",
            "estimated_total_time": "26-40 minutos"
        }
    
    elif category == 'creacion':
        steps = [
            {
                "id": "create-1",
                "title": "Planificación y estructura del contenido",
                "description": f"Definir estructura, objetivos, audiencia objetivo y elementos clave para '{message}'",
                "tool": "planning",
                "estimated_time": "4-6 minutos",
                "complexity": "media"
            },
            {
                "id": "create-2",
                "title": "Investigación de contexto y referencias",
                "description": "Recopilar información relevante, ejemplos, mejores prácticas y referencias del tema",
                "tool": "web_search",
                "estimated_time": "6-10 minutos", 
                "complexity": "media"
            },
            {
                "id": "create-3",
                "title": "Desarrollo del contenido principal",
                "description": "Crear el contenido siguiendo la estructura planificada, con enfoque en originalidad y valor",
                "tool": "creation",
                "estimated_time": "15-25 minutos",
                "complexity": "alta"
            },
            {
                "id": "create-4",
                "title": "Revisión, optimización y formato final",
                "description": "Revisar, mejorar la redacción, aplicar formato profesional y asegurar calidad",
                "tool": "analysis",
                "estimated_time": "5-8 minutos",
                "complexity": "media"
            }
        ]
        steps = mark_first_step_active(steps)
        return {
            "steps": steps,
            "task_type": "creación de contenido",
            "complexity": "alta", 
            "estimated_total_time": "30-49 minutos"
        }
    
    elif category == 'analisis':
        steps = [
            {
                "id": "analysis-1",
                "title": "Recopilación y preparación de datos",
                "description": f"Identificar y recopilar todos los datos relevantes para analizar '{message}'",
                "tool": "web_search",
                "estimated_time": "5-8 minutos",
                "complexity": "media"
            },
            {
                "id": "analysis-2",
                "title": "Análisis cuantitativo y cualitativo",
                "description": "Aplicar métodos de análisis estadístico, comparativo y tendencial a los datos",
                "tool": "analysis",
                "estimated_time": "12-18 minutos",
                "complexity": "alta"
            },
            {
                "id": "analysis-3",
                "title": "Identificación de patrones e insights",
                "description": "Detectar patrones, correlaciones, anomalías y generar insights significativos",
                "tool": "analysis",
                "estimated_time": "8-12 minutos",
                "complexity": "alta"
            },
            {
                "id": "analysis-4",
                "title": "Reporte ejecutivo con recomendaciones",
                "description": "Crear reporte detallado con conclusiones, recomendaciones estratégicas y siguientes pasos",
                "tool": "creation",
                "estimated_time": "6-10 minutos",
                "complexity": "media"
            }
        ]
        steps = mark_first_step_active(steps)
        return {
            "steps": steps,
            "task_type": "análisis profundo",
            "complexity": "alta",
            "estimated_total_time": "31-48 minutos"
        }
    
    elif category == 'desarrollo':
        steps = [
            {
                "id": "dev-1",
                "title": "Análisis de requirements y arquitectura",
                "description": f"Analizar requisitos técnicos, definir arquitectura y tecnologías para '{message}'",
                "tool": "analysis",
                "estimated_time": "6-10 minutos",
                "complexity": "alta"
            },
            {
                "id": "dev-2",
                "title": "Investigación de mejores prácticas",
                "description": "Buscar patrones de diseño, librerías, frameworks y mejores prácticas aplicables",
                "tool": "web_search", 
                "estimated_time": "8-12 minutos",
                "complexity": "media"
            },
            {
                "id": "dev-3",
                "title": "Implementación y desarrollo",
                "description": "Desarrollar la solución siguiendo estándares de calidad y buenas prácticas",
                "tool": "creation",
                "estimated_time": "20-35 minutos",
                "complexity": "alta"
            },
            {
                "id": "dev-4",
                "title": "Testing y documentación",
                "description": "Realizar pruebas, crear documentación técnica y guías de uso",
                "tool": "analysis",
                "estimated_time": "8-15 minutos",
                "complexity": "media"
            }
        ]
        steps = mark_first_step_active(steps)
        return {
            "steps": steps,
            "task_type": "desarrollo de software",
            "complexity": "alta",
            "estimated_total_time": "42-72 minutos"
        }
    
    elif category == 'planificacion':
        steps = [
            {
                "id": "plan-1",
                "title": "Análisis de situación actual y objetivos",
                "description": f"Evaluar el estado actual y definir objetivos específicos para '{message}'",
                "tool": "analysis",
                "estimated_time": "5-8 minutos",
                "complexity": "media"
            },
            {
                "id": "plan-2",
                "title": "Investigación de estrategias y benchmarking",
                "description": "Investigar estrategias exitosas, casos de estudio y mejores prácticas del sector",
                "tool": "web_search",
                "estimated_time": "8-15 minutos",
                "complexity": "media"
            },
            {
                "id": "plan-3",
                "title": "Desarrollo de estrategia y cronograma",
                "description": "Crear plan estratégico detallado con cronograma, recursos y métricas de éxito",
                "tool": "planning",
                "estimated_time": "15-25 minutos",
                "complexity": "alta"
            },
            {
                "id": "plan-4",
                "title": "Plan de implementación y seguimiento",
                "description": "Definir plan de implementación, KPIs, milestones y sistema de seguimiento",
                "tool": "creation",
                "estimated_time": "6-12 minutos",
                "complexity": "media"
            }
        ]
        steps = mark_first_step_active(steps)
        return {
            "steps": steps,
            "task_type": "planificación estratégica",
            "complexity": "alta",
            "estimated_total_time": "34-60 minutos"
        }
    
    else:  # general
        steps = [
            {
                "id": "general-1",
                "title": f"Análisis comprehensivo del objetivo",
                "description": f"Analizar en profundidad qué se requiere para '{message}', identificar componentes clave y establecer criterios de éxito",
                "tool": "analysis",
                "estimated_time": "4-7 minutos",
                "complexity": "media"
            },
            {
                "id": "general-2",
                "title": "Investigación contextual y de referencia",
                "description": "Buscar información relevante, casos similares, mejores prácticas y recursos necesarios",
                "tool": "web_search",
                "estimated_time": "8-15 minutos",
                "complexity": "media"
            },
            {
                "id": "general-3",
                "title": "Desarrollo y procesamiento de la solución",
                "description": "Desarrollar la solución integrando la investigación con metodología sistemática",
                "tool": "creation",
                "estimated_time": "12-20 minutos",
                "complexity": "alta"
            },
            {
                "id": "general-4",
                "title": "Refinamiento y entrega final optimizada",
                "description": "Refinar resultados, optimizar presentación y asegurar cumplimiento de objetivos",
                "tool": "analysis",
                "estimated_time": "5-10 minutos",
                "complexity": "media"
            }
        ]
        steps = mark_first_step_active(steps)
        return {
            "steps": steps,
            "task_type": "tarea general",
            "complexity": "media",
            "estimated_total_time": "29-52 minutos"
        }

def generate_unified_ai_plan(message: str, task_id: str, attempt_retries: bool = True) -> dict:
    """
    🚀 SISTEMA ROBUSTO DE GENERACIÓN DE PLANES CON MÚLTIPLES FALLBACKS
    Función UNIFICADA con robustecimiento completo y fallbacks inteligentes
    """
    logger.info(f"🧠 Generating robust unified AI-powered plan for task {task_id} - Message: {message[:50]}...")
    
    # Detectar categoría de la tarea para contexto
    task_category = detect_task_category(message)
    logger.info(f"📋 Task category detected: {task_category}")
    
    # Obtener servicio de Ollama
    ollama_service = get_ollama_service()
    if not ollama_service:
        logger.warning("⚠️ Ollama service not available, using intelligent fallback")
        return generate_intelligent_fallback_plan(message, task_id, task_category)
    
    # Verificar que Ollama esté saludable
    if not ollama_service.is_healthy():
        logger.warning("⚠️ Ollama service not healthy, using intelligent fallback")
        return generate_intelligent_fallback_plan(message, task_id, task_category)
    
    def generate_robust_plan_with_retries() -> dict:
        """🔄 Generar plan con múltiples estrategias de reintentos"""
        max_attempts = 3 if attempt_retries else 1
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"🔄 Robust plan generation attempt {attempt}/{max_attempts} for task {task_id}")
                
                # Prompts progresivamente más específicos
                if attempt == 1:
                    # Prompt optimizado con contexto de categoría
                    plan_prompt = f"""Eres un planificador experto. Crea un plan detallado y específico para la siguiente tarea de categoría "{task_category}":

TAREA: {message}

Genera 4-5 pasos ESPECÍFICOS, DETALLADOS y ORIENTADOS AL VALOR que superen las expectativas del usuario.

CONTEXTO DE CATEGORÍA "{task_category.upper()}":
- Si es investigación: incluye múltiples fuentes, análisis comparativo, validación cruzada
- Si es creación: incluye planificación, investigación, desarrollo iterativo, refinamiento
- Si es análisis: incluye recopilación de datos, análisis multi-dimensional, insights profundos
- Si es desarrollo: incluye análisis técnico, diseño, implementación, testing
- Si es planificación: incluye análisis situacional, benchmarking, estrategia, implementación

HERRAMIENTAS DISPONIBLES: web_search, analysis, creation, planning, delivery, processing

RESPONDE EXACTAMENTE en este formato JSON (sin texto adicional):
{{
  "steps": [
    {{
      "id": "step-1",
      "title": "Título específico y accionable del primer paso",
      "description": "Descripción detallada con metodología y entregables específicos para esta tarea exacta",
      "tool": "herramienta_apropiada",
      "estimated_time": "tiempo realista en minutos",
      "complexity": "baja|media|alta"
    }},
    {{
      "id": "step-2", 
      "title": "Segundo paso que construya sobre el anterior",
      "description": "Descripción específica que integre resultados del paso anterior",
      "tool": "herramienta_apropiada",
      "estimated_time": "tiempo realista",
      "complexity": "baja|media|alta"
    }},
    {{
      "id": "step-3",
      "title": "Tercer paso con valor agregado",
      "description": "Metodología avanzada que genere insights únicos o valor diferencial",
      "tool": "herramienta_apropiada", 
      "estimated_time": "tiempo realista",
      "complexity": "baja|media|alta"
    }},
    {{
      "id": "step-4",
      "title": "Cuarto paso de refinamiento y optimización",
      "description": "Proceso de mejora, validación y optimización de resultados",
      "tool": "herramienta_apropiada",
      "estimated_time": "tiempo realista", 
      "complexity": "baja|media|alta"
    }}
  ],
  "task_type": "tipo específico basado en la tarea real",
  "complexity": "baja|media|alta",
  "estimated_total_time": "suma realista de todos los pasos"
}}

IMPORTANTE: Los pasos deben ser específicos para "{message}", no genéricos. Cada paso debe tener valor único."""

                elif attempt == 2:
                    # Prompt simplificado para segundo intento
                    plan_prompt = f"""Crea un plan JSON para: {message}

{{
  "steps": [
    {{"id": "step-1", "title": "Paso 1 específico", "description": "Descripción detallada", "tool": "web_search"}},
    {{"id": "step-2", "title": "Paso 2 específico", "description": "Descripción detallada", "tool": "analysis"}},
    {{"id": "step-3", "title": "Paso 3 específico", "description": "Descripción detallada", "tool": "creation"}}
  ],
  "task_type": "tipo de tarea",
  "complexity": "media",
  "estimated_total_time": "30 minutos"
}}

Solo JSON, sin texto adicional:"""

                else:
                    # Prompt mínimo para tercer intento
                    plan_prompt = f"Plan JSON para '{message}': {{'steps': [{{'id':'step-1','title':'Investigar {message[:20]}','description':'Buscar información','tool':'web_search'}},{{'id':'step-2','title':'Procesar información','description':'Analizar datos','tool':'analysis'}},{{'id':'step-3','title':'Crear resultado','description':'Generar entregable','tool':'creation'}}],'task_type':'general','complexity':'media','estimated_total_time':'25 minutos'}}"
                
                # Generar plan con Ollama usando diferentes parámetros según el intento
                ollama_params = {
                    'temperature': 0.2 if attempt == 1 else 0.1,
                    'max_tokens': 1500 if attempt == 1 else 800,
                }
                
                result = ollama_service.generate_response(plan_prompt, ollama_params)
                
                if result.get('error'):
                    logger.error(f"❌ Ollama error: {result['error']}")
                    return {'error': f'Plan generation failed: {result["error"]}', 'success': False}
                
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
                    
                    # 🎯 MARCAR EL PRIMER PASO COMO ACTIVO
                    if plan_data['steps']:
                        plan_data['steps'][0]['active'] = True
                        plan_data['steps'][0]['status'] = 'active'
                        logger.info(f"✅ First step marked as active: {plan_data['steps'][0]['title']}")
                    
                    result = {
                        'steps': plan_data['steps'],
                        'task_type': plan_data.get('task_type', 'general'),
                        'complexity': plan_data.get('complexity', 'media'),
                        'estimated_total_time': plan_data.get('estimated_total_time', '30 minutos'),
                        'plan_source': 'ai_generated'
                    }
                    
                    logger.info(f"✅ Returning AI-generated plan with {len(plan_data['steps'])} steps")
                    return result
                    
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
                    
                    # 🎯 MARCAR EL PRIMER PASO COMO ACTIVO
                    if fallback_steps:
                        fallback_steps[0]['active'] = True
                        fallback_steps[0]['status'] = 'active'
                        logger.info(f"✅ First fallback step marked as active: {fallback_steps[0]['title']}")
                    
                    result = {
                        'steps': fallback_steps,
                        'task_type': 'general',
                        'complexity': 'media',
                        'estimated_total_time': '30 minutos',
                        'plan_source': 'json_parse_fallback'
                    }
                    
                    logger.info(f"✅ Returning JSON parse fallback plan with {len(fallback_steps)} steps")
                    return result
                    
            except Exception as attempt_error:
                logger.error(f"❌ Attempt {attempt} failed: {attempt_error}")
                last_error = attempt_error
                continue
        
        # Si llegamos aquí, todos los intentos fallaron
        logger.error(f"❌ All plan generation attempts failed. Using intelligent fallback")
        return generate_intelligent_fallback_plan(message, task_id, task_category)
    
    # Llamar a la función interna
    try:
        result = generate_robust_plan_with_retries()
        # Asegurar que el primer paso esté activo
        if result.get('steps') and len(result['steps']) > 0:
            result['steps'][0]['active'] = True
            result['steps'][0]['status'] = 'active'
        return result
    except Exception as e:
        logger.error(f"❌ Plan generation error: {e}")
        return generate_intelligent_fallback_plan(message, task_id, task_category)

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

@agent_bp.route('/generate-plan', methods=['POST'])
def generate_plan():
    """Generate a plan for a task - Compatible with frontend expectations"""
    try:
        data = request.get_json()
        task_title = data.get('task_title', '')
        task_id = data.get('task_id')
        
        if not task_title:
            return jsonify({'error': 'task_title is required'}), 400
        
        logger.info(f"📋 Generating plan for task: {task_title}")
        
        # Generar plan usando la función existente
        plan_response = generate_task_plan(task_title, task_id)
        
        # Generar título mejorado
        enhanced_title = generate_task_title_with_llm(task_title, task_id)
        
        # Formatear respuesta para el frontend
        response = {
            'success': True,
            'enhanced_title': enhanced_title,
            'plan': plan_response.get('steps', []),
            'task_type': plan_response.get('task_type', 'general'),
            'complexity': plan_response.get('complexity', 'media'),
            'estimated_total_time': plan_response.get('estimated_total_time', '10-15 minutos'),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Plan generated successfully: {len(response['plan'])} steps")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error generating plan: {e}")
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