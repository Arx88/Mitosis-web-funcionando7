"""
Rutas API del agente - Versión limpia
Endpoints para comunicación con el frontend
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from datetime import datetime
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

agent_bp = Blueprint('agent', __name__)

# Almacenamiento temporal para compartir conversaciones
shared_conversations = {}

# Almacenamiento temporal para archivos por tarea
task_files = {}

# Inicializar Environment Setup Manager
environment_setup_manager = EnvironmentSetupManager()

# Inicializar Task Planner
task_planner = TaskPlanner()

# Inicializar Execution Engine
execution_engine = ExecutionEngine(
    tool_manager=current_app.tool_manager if current_app else None,
    environment_manager=environment_setup_manager
)

@agent_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud del agente"""
    try:
        # Obtener servicios
        ollama_service = current_app.ollama_service
        tool_manager = current_app.tool_manager
        database_service = current_app.database_service
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'ollama': ollama_service.is_healthy(),
                'tools': len(tool_manager.get_available_tools()),
                'database': database_service.is_connected()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        return jsonify({
            'error': str(e),
            'models': [],
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/generate-plan', methods=['POST'])
def generate_dynamic_plan():
    """Generar plan dinámico REAL usando DynamicTaskPlanner"""
    try:
        data = request.get_json()
        task_title = data.get('task_title', '')
        
        if not task_title:
            return jsonify({'error': 'task_title is required'}), 400
        
        # Obtener servicios
        tool_manager = current_app.tool_manager
        
        # Usar DynamicTaskPlanner REAL para generar plan
        from src.tools.dynamic_task_planner import get_dynamic_task_planner
        dynamic_planner = get_dynamic_task_planner()
        
        # Crear plan dinámico real
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            execution_plan = loop.run_until_complete(
                dynamic_planner.create_dynamic_plan(
                    task_id=f"plan_{int(time.time())}",
                    task_description=task_title,
                    context={
                        'available_tools': tool_manager.get_available_tools() if tool_manager else [],
                        'environment_state': {'initial_tools': tool_manager.get_available_tools() if tool_manager else []}
                    }
                )
            )
            
            # Convertir ExecutionPlan a formato frontend
            plan = []
            for i, step in enumerate(execution_plan.steps):
                plan.append({
                    'id': step.id,
                    'title': step.title,
                    'description': step.description,
                    'completed': False,
                    'active': i == 0,  # Primer paso activo
                    'tool': step.tool,
                    'estimated_duration': step.estimated_duration,
                    'complexity': step.complexity
                })
            
            return jsonify({
                'plan': plan,
                'total_estimated_duration': execution_plan.total_estimated_duration,
                'complexity_score': execution_plan.complexity_score,
                'success_probability': execution_plan.success_probability,
                'generated_dynamically': True
            })
            
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/generate-suggestions', methods=['POST'])
def generate_dynamic_suggestions():
    """Generar sugerencias dinámicas REALES usando capacidades del agente"""
    try:
        # Obtener servicios
        tool_manager = current_app.tool_manager
        
        # Generar sugerencias basadas en herramientas disponibles
        available_tools = tool_manager.get_available_tools() if tool_manager else []
        
        suggestions = []
        
        # Sugerencias basadas en herramientas disponibles
        tool_suggestions = {
            'web_search': ['Investigar últimas tendencias en tecnología', 'Buscar información sobre un tema específico'],
            'deep_research': ['Realizar análisis profundo sobre un tema', 'Investigar tecnologías emergentes'],
            'file_manager': ['Crear documentos estructurados', 'Generar reportes profesionales'],
            'shell': ['Automatizar tareas del sistema', 'Ejecutar procesos de configuración'],
            'comprehensive_research': ['Análisis completo de mercado', 'Investigación académica detallada']
        }
        
        # Generar sugerencias dinámicas
        for tool_info in available_tools[:5]:  # Máximo 5 sugerencias
            tool_name = tool_info['name']
            if tool_name in tool_suggestions:
                import random
                suggestion = random.choice(tool_suggestions[tool_name])
                suggestions.append({
                    'title': suggestion,
                    'tool': tool_name,
                    'description': tool_info.get('description', '')
                })
        
        # Si no hay suficientes sugerencias, agregar algunas genéricas
        if len(suggestions) < 3:
            generic_suggestions = [
                {'title': 'Analizar un problema complejo', 'tool': 'analysis', 'description': 'Análisis detallado de cualquier situación'},
                {'title': 'Crear contenido profesional', 'tool': 'content', 'description': 'Generar documentos o contenido estructurado'},
                {'title': 'Optimizar un proceso', 'tool': 'optimization', 'description': 'Mejorar eficiencia de procesos existentes'}
            ]
            
            suggestions.extend(generic_suggestions[:3-len(suggestions)])
        
        return jsonify({
            'suggestions': suggestions[:3],  # Máximo 3 sugerencias
            'generated_dynamically': True,
            'based_on_available_tools': [tool['name'] for tool in available_tools]
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/chat', methods=['POST'])
def chat():
    """Endpoint principal para chat con el agente - EJECUCIÓN AUTÓNOMA REAL"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})
        search_mode = data.get('search_mode', None)
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Obtener servicios
        ollama_service = current_app.ollama_service
        tool_manager = current_app.tool_manager
        database_service = current_app.database_service
        
        # Obtener task_id del contexto
        task_id = context.get('task_id', f"task_{int(time.time())}")
        
        # Detectar modo de búsqueda desde el mensaje
        original_message = message
        if message.startswith('[WebSearch]'):
            search_mode = 'websearch'
            message = message.replace('[WebSearch]', '').strip()
        elif message.startswith('[DeepResearch]'):
            search_mode = 'deepsearch'
            message = message.replace('[DeepResearch]', '').strip()
        
        # **NUEVO: Usar ExecutionEngine para ejecución autónoma REAL**
        if not search_mode:
            # Para tareas generales, usar ExecutionEngine
            try:
                print(f"🚀 Iniciando ejecución autónoma para tarea: {task_id}")
                
                # Configurar endpoint Ollama
                ollama_endpoint = "https://9g1hiqvg9k@wnbaldwy.com"
                ollama_model = "llama3.1:8b"
                
                # Actualizar configuración de Ollama
                ollama_service.base_url = ollama_endpoint
                ollama_service.current_model = ollama_model
                
                # Crear ExecutionEngine con las herramientas disponibles
                execution_engine = ExecutionEngine(
                    tool_manager=tool_manager,
                    environment_manager=environment_setup_manager
                )
                
                # Agregar WebSocket callbacks si está disponible
                def notify_progress(notification):
                    print(f"📈 Progress: {notification}")
                    # Aquí se puede integrar con WebSocket para notificaciones en tiempo real
                
                execution_engine.add_progress_callback(notify_progress)
                
                # Ejecutar tarea de manera autónoma
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    execution_context = loop.run_until_complete(
                        execution_engine.execute_task(
                            task_id=task_id,
                            task_title=message,
                            task_description=f"Tarea iniciada por usuario: {message}",
                            config={'dynamic_planning': True, 'auto_recovery': True}
                        )
                    )
                    
                    # Generar respuesta basada en el contexto de ejecución
                    if execution_context.status.value == 'completed':
                        # Tarea completada exitosamente
                        completion_summary = f"✅ Tarea completada exitosamente\n\n"
                        completion_summary += f"📊 **Resumen de ejecución:**\n"
                        completion_summary += f"- Pasos completados: {len([se for se in execution_context.step_executions if se.status.value == 'completed'])}\n"
                        completion_summary += f"- Tiempo total: {execution_context.total_execution_time:.2f} segundos\n"
                        completion_summary += f"- Tasa de éxito: {execution_context.success_rate:.1%}\n\n"
                        
                        # Mostrar resultados de cada paso
                        completion_summary += "📋 **Pasos ejecutados:**\n"
                        for step_exec in execution_context.step_executions:
                            status_icon = "✅" if step_exec.status.value == 'completed' else "❌"
                            completion_summary += f"{status_icon} {step_exec.step.title}\n"
                            if step_exec.result and step_exec.status.value == 'completed':
                                if isinstance(step_exec.result, dict) and 'response' in step_exec.result:
                                    completion_summary += f"   💡 {step_exec.result['response'][:100]}...\n"
                        
                        response_text = completion_summary
                        
                    else:
                        # Tarea falló o completada parcialmente
                        failure_summary = f"⚠️ Tarea completada parcialmente\n\n"
                        failure_summary += f"📊 **Estado de ejecución:**\n"
                        failure_summary += f"- Estado: {execution_context.status.value}\n"
                        failure_summary += f"- Pasos completados: {len([se for se in execution_context.step_executions if se.status.value == 'completed'])}\n"
                        failure_summary += f"- Pasos fallidos: {len([se for se in execution_context.step_executions if se.status.value == 'failed'])}\n"
                        failure_summary += f"- Tasa de éxito: {execution_context.success_rate:.1%}\n"
                        
                        response_text = failure_summary
                    
                    # Obtener archivos generados
                    created_files = []
                    # Buscar archivos creados en los resultados de los pasos
                    for step_exec in execution_context.step_executions:
                        if step_exec.result and isinstance(step_exec.result, dict):
                            if 'file_path' in step_exec.result or 'report_file' in step_exec.result:
                                file_path = step_exec.result.get('file_path') or step_exec.result.get('report_file')
                                if file_path and os.path.exists(file_path):
                                    created_files.append({
                                        'id': str(uuid.uuid4()),
                                        'file_id': str(uuid.uuid4()),
                                        'task_id': task_id,
                                        'name': os.path.basename(file_path),
                                        'path': file_path,
                                        'size': os.path.getsize(file_path),
                                        'type': 'file',
                                        'mime_type': 'text/plain',
                                        'source': 'agent',
                                        'created_at': datetime.now().isoformat()
                                    })
                    
                    return jsonify({
                        'response': response_text,
                        'execution_context': {
                            'task_id': task_id,
                            'status': execution_context.status.value,
                            'success_rate': execution_context.success_rate,
                            'total_execution_time': execution_context.total_execution_time,
                            'steps_completed': len([se for se in execution_context.step_executions if se.status.value == 'completed']),
                            'steps_failed': len([se for se in execution_context.step_executions if se.status.value == 'failed'])
                        },
                        'created_files': created_files,
                        'autonomous_execution': True,
                        'model': ollama_model,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                finally:
                    loop.close()
                    
            except Exception as e:
                print(f"❌ Error en ejecución autónoma: {str(e)}")
                # Fallback a ejecución con Ollama
                response = ollama_service.generate_response(message, context, use_tools=True)
                return jsonify({
                    'response': response.get('response', f"Error en ejecución autónoma: {str(e)}"),
                    'tool_calls': response.get('tool_calls', []),
                    'autonomous_execution': False,
                    'fallback_used': True,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'model': response.get('model', 'unknown')
                })
        
        # Mantener comportamiento existente para WebSearch y DeepSearch
        tool_results = []
        created_files = []
        
        if search_mode == 'websearch':
            # Usar web_search para WebSearch
            try:
                result = tool_manager.execute_tool('web_search', {
                    'query': message,
                    'max_results': 10
                })
                tool_results.append({
                    'tool': 'web_search',
                    'parameters': {'query': message, 'max_results': 10},
                    'result': result
                })
            except Exception as e:
                tool_results.append({
                    'tool': 'web_search',
                    'parameters': {'query': message},
                    'result': {'error': str(e)}
                })
        
        elif search_mode == 'deepsearch':
            # Usar deep_research para DeepResearch
            try:
                result = tool_manager.execute_tool('deep_research', {
                    'query': message,
                    'max_sources': 20,
                    'research_depth': 'comprehensive'
                })
                tool_results.append({
                    'tool': 'deep_research',
                    'parameters': {'query': message, 'max_sources': 20, 'research_depth': 'comprehensive'},
                    'result': result
                })
                
                # Si hay un archivo de informe, agregarlo a los archivos de la tarea
                if result.get('success') and result.get('report_file'):
                    report_file_path = result['report_file']
                    file_info = {
                        'id': str(uuid.uuid4()),
                        'file_id': str(uuid.uuid4()),
                        'task_id': task_id,
                        'name': f'informe_{message.replace(" ", "_")[:30]}.md',
                        'path': report_file_path,
                        'size': os.path.getsize(report_file_path) if os.path.exists(report_file_path) else 0,
                        'type': 'file',
                        'mime_type': 'text/markdown',
                        'source': 'agent',
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Agregar archivo a la tarea
                    if task_id not in task_files:
                        task_files[task_id] = []
                    task_files[task_id].append(file_info)
                    created_files.append(file_info)
                    
            except Exception as e:
                tool_results.append({
                    'tool': 'deep_research',
                    'parameters': {'query': message, 'max_sources': 20, 'research_depth': 'comprehensive'},
                    'result': {'error': str(e)}
                })
        
        # Crear respuesta para search modes
        if search_mode:
            if tool_results and tool_results[0]['result'].get('success'):
                tool_result = tool_results[0]['result']
                
                if search_mode == 'websearch':
                    # Datos estructurados para WebSearch
                    search_results = tool_result.get('search_results', [])
                    summary = tool_result.get('summary', '')
                    
                    # Formatear fuentes para el componente SearchResults
                    formatted_sources = []
                    for i, result in enumerate(search_results[:5]):
                        formatted_sources.append({
                            'title': result.get('title', f'Resultado {i+1}'),
                            'content': result.get('snippet', 'Sin descripción'),
                            'url': result.get('url', ''),
                            'domain': result.get('domain', ''),
                            'score': result.get('score', 0)
                        })
                    
                    response = {
                        'response': f"🌐 **Búsqueda Web**\n\n**Pregunta:** {message}\n\n**Resumen:**\n{summary}\n\n**Resultados encontrados:** {len(search_results)}\n\n**Fuentes principales:**\n" + 
                                  "\n".join([f"{i+1}. **{result.get('title', 'Sin título')}**\n   {result.get('snippet', 'Sin descripción')[:150]}...\n   🔗 {result.get('url', '')}" 
                                            for i, result in enumerate(search_results[:3])]),
                        'model': 'web-search',
                        'search_data': {
                            'query': message,
                            'directAnswer': summary,
                            'sources': formatted_sources,
                            'images': [],
                            'summary': summary,
                            'search_stats': {'total_sources': len(search_results)},
                            'type': 'websearch'
                        }
                    }
                
                elif search_mode == 'deepsearch':
                    # Datos estructurados para DeepResearch
                    analysis = tool_result.get('analysis', '')
                    key_findings = tool_result.get('key_findings', [])
                    recommendations = tool_result.get('recommendations', [])
                    sources = tool_result.get('sources', [])
                    
                    # Formatear fuentes para el componente SearchResults
                    formatted_sources = []
                    for i, source in enumerate(sources[:5]):
                        formatted_sources.append({
                            'title': f'Fuente {i+1}',
                            'content': source if isinstance(source, str) else str(source),
                            'url': ''
                        })
                    
                    response = {
                        'response': f"🔬 **Investigación Profunda**\n\n**Tema:** {message}\n\n**Análisis Comprehensivo:**\n{analysis}\n\n**Hallazgos Clave:**\n" + 
                                  "\n".join([f"• {finding}" for finding in key_findings[:3]]) + 
                                  "\n\n**Recomendaciones:**\n" + 
                                  "\n".join([f"• {rec}" for rec in recommendations[:3]]),
                        'model': 'deep-research',
                        'search_data': {
                            'query': message,
                            'directAnswer': analysis,
                            'sources': formatted_sources,
                            'type': 'deepsearch',
                            'key_findings': key_findings,
                            'recommendations': recommendations
                        }
                    }
            else:
                # Error en la búsqueda
                error_msg = tool_results[0]['result'].get('error', 'Error desconocido') if tool_results else 'No se pudo realizar la búsqueda'
                response = {
                    'response': f"❌ Error en la búsqueda: {error_msg}",
                    'model': f'{search_mode}-error'
                }
            
            return jsonify({
                'response': response.get('response', 'Sin respuesta'),
                'tool_calls': response.get('tool_calls', []),
                'tool_results': tool_results,
                'created_files': created_files,
                'search_mode': search_mode,
                'search_data': response.get('search_data'),
                'timestamp': datetime.now().isoformat(),
                'model': response.get('model', 'unknown')
            })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/upload-files', methods=['POST'])
def upload_files():
    """Subir archivos para procesamiento"""
    try:
        task_id = request.form.get('task_id')
        if not task_id:
            return jsonify({'error': 'task_id is required'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        uploaded_files = []
        upload_dir = os.path.join('/tmp', 'agent_uploads', task_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                
                file_info = {
                    'id': str(uuid.uuid4()),
                    'name': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'mime_type': file.mimetype or 'application/octet-stream',
                    'uploaded_at': datetime.now().isoformat()
                }
                uploaded_files.append(file_info)
        
        return jsonify({
            'success': True,
            'files': uploaded_files,
            'task_id': task_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/status', methods=['GET'])
def status():
    """Obtener estado del agente y servicios"""
    try:
        ollama_service = current_app.ollama_service
        tool_manager = current_app.tool_manager
        
        # Verificar estado de Ollama
        ollama_healthy = ollama_service.is_healthy()
        available_models = ollama_service.get_available_models() if ollama_healthy else []
        current_model = ollama_service.get_current_model()
        
        # Obtener herramientas disponibles
        tools = tool_manager.get_available_tools()
        
        return jsonify({
            'status': 'healthy' if ollama_healthy else 'degraded',
            'ollama_status': 'connected' if ollama_healthy else 'disconnected',
            'available_models': available_models,
            'current_model': current_model,
            'tools_count': len(tools),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/tools', methods=['GET'])
def tools():
    """Obtener lista de herramientas disponibles"""
    try:
        tool_manager = current_app.tool_manager
        available_tools = tool_manager.get_available_tools()
        
        return jsonify({
            'tools': available_tools,
            'count': len(available_tools),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500