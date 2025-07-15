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
from src.orchestration.task_orchestrator import TaskOrchestrator, OrchestrationContext

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
    """Generar plan dinámico REAL usando TaskPlanner"""
    try:
        data = request.get_json()
        task_title = data.get('task_title', '')
        
        if not task_title:
            return jsonify({'error': 'task_title is required'}), 400
        
        # Obtener servicios
        tool_manager = current_app.tool_manager
        
        # Usar TaskPlanner estático para generar plan
        # Esto es más confiable que DynamicTaskPlanner que tiene problemas de compatibilidad
        from src.tools.task_planner import TaskPlanner
        
        task_planner = TaskPlanner()
        
        # Generar plan usando el TaskPlanner base
        execution_plan = task_planner.generate_execution_plan(
            task_id=f"plan_{int(time.time())}",
            task_title=task_title,
            task_description=task_title
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
        ollama_service = current_app.ollama_service
        
        # Generar sugerencias basadas en herramientas disponibles
        available_tools = tool_manager.get_available_tools() if tool_manager else []
        
        suggestions = []
        
        # Generar sugerencias dinámicas basadas en análisis real de herramientas
        if available_tools:
            # Usar Ollama para generar sugerencias contextualmente relevantes
            tool_capabilities = []
            for tool_info in available_tools:
                tool_capabilities.append(f"- {tool_info['name']}: {tool_info.get('description', 'Herramienta disponible')}")
            
            tools_context = "\n".join(tool_capabilities)
            
            # Prompt para generar sugerencias dinámicas
            suggestion_prompt = f"""Basándote en las siguientes herramientas disponibles, genera exactamente 3 sugerencias prácticas y específicas que un usuario real podría querer hacer:

Herramientas disponibles:
{tools_context}

Reglas importantes:
1. Cada sugerencia debe ser UNA SOLA ORACIÓN CLARA
2. Las sugerencias deben ser ESPECÍFICAS y PRÁCTICAS
3. Deben ser tareas reales que alguien querría realizar
4. NO uses formato de "SUGERENCIA 1" o "PLAN DE ACCIÓN"
5. Responde SOLO las 3 sugerencias, una por línea

Ejemplo de formato correcto:
Analizar tendencias de ventas del último trimestre
Crear un sitio web para mi negocio local
Automatizar el backup de archivos importantes

Ahora genera 3 sugerencias específicas y únicas:"""
            
            try:
                # Generar sugerencias usando Ollama
                response = ollama_service.generate_response(
                    suggestion_prompt,
                    context={'generate_suggestions': True},
                    use_tools=False
                )
                
                if response and response.get('response'):
                    suggestion_lines = response['response'].strip().split('\n')
                    
                    # Procesar sugerencias generadas
                    for i, line in enumerate(suggestion_lines[:3]):
                        if line.strip():
                            # Determinar herramienta más relevante basada en el contenido
                            relevant_tool = 'general'
                            line_lower = line.lower()
                            
                            if any(word in line_lower for word in ['buscar', 'investigar', 'web', 'información']):
                                relevant_tool = 'web_search'
                            elif any(word in line_lower for word in ['análisis', 'profundo', 'investigación', 'research']):
                                relevant_tool = 'deep_research'
                            elif any(word in line_lower for word in ['archivo', 'documento', 'crear', 'generar']):
                                relevant_tool = 'file_manager'
                            elif any(word in line_lower for word in ['comando', 'ejecutar', 'sistema']):
                                relevant_tool = 'shell'
                            
                            suggestions.append({
                                'title': line.strip(),
                                'tool': relevant_tool,
                                'description': f'Tarea generada dinámicamente usando {relevant_tool}'
                            })
                
            except Exception as ollama_error:
                print(f"Error generating suggestions with Ollama: {ollama_error}")
                # Fallback: generar sugerencias basadas en análisis de herramientas
                pass
        
        # Si no se generaron sugerencias, usar análisis de herramientas como fallback
        if not suggestions and available_tools:
            # Generar sugerencias basadas en capacidades reales de las herramientas
            tool_categories = {}
            for tool_info in available_tools:
                tool_name = tool_info['name']
                tool_desc = tool_info.get('description', '').lower()
                
                if 'search' in tool_desc or 'web' in tool_desc:
                    tool_categories.setdefault('research', []).append(tool_name)
                elif 'file' in tool_desc or 'document' in tool_desc:
                    tool_categories.setdefault('content', []).append(tool_name)
                elif 'shell' in tool_desc or 'command' in tool_desc:
                    tool_categories.setdefault('automation', []).append(tool_name)
                else:
                    tool_categories.setdefault('general', []).append(tool_name)
            
            # Generar sugerencias basadas en categorías
            category_suggestions = {
                'research': 'Investigar un tema específico de tu interés',
                'content': 'Crear y organizar documentos profesionales',
                'automation': 'Automatizar tareas repetitivas del sistema',
                'general': 'Resolver un problema específico que tengas'
            }
            
            for category, tools in tool_categories.items():
                if len(suggestions) < 3:
                    suggestions.append({
                        'title': category_suggestions.get(category, f'Usar {category}'),
                        'tool': tools[0] if tools else 'general',
                        'description': f'Capacidad disponible usando {", ".join(tools[:2])}'
                    })
        
        # Si aún no hay sugerencias, usar capacidades básicas del sistema
        if not suggestions:
            suggestions = [
                {
                    'title': 'Analizar información específica',
                    'tool': 'analysis',
                    'description': 'Analizar datos o información que necesites procesar'
                },
                {
                    'title': 'Buscar información actualizada',
                    'tool': 'search',
                    'description': 'Encontrar información reciente sobre cualquier tema'
                },
                {
                    'title': 'Procesar y organizar contenido',
                    'tool': 'processing',
                    'description': 'Organizar y estructurar información de manera eficiente'
                }
            ]
        
        return jsonify({
            'suggestions': suggestions[:3],  # Máximo 3 sugerencias
            'generated_dynamically': True,
            'based_on_available_tools': [tool['name'] for tool in available_tools],
            'generation_method': 'dynamic_analysis'
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
        
        # **NUEVO: Usar AutomaticExecutionOrchestrator para ejecución autónoma REAL**
        if not search_mode:
            # Para tareas generales, usar AutomaticExecutionOrchestrator
            try:
                print(f"🚀 Iniciando ejecución autónoma con AutomaticExecutionOrchestrator para tarea: {task_id}")
                
                # Configurar endpoint Ollama
                ollama_endpoint = "https://78d08925604a.ngrok-free.app"
                ollama_model = "llama3.1:8b"
                
                # Actualizar configuración de Ollama
                ollama_service.base_url = ollama_endpoint
                ollama_service.current_model = ollama_model
                
                # **NUEVO: Usar AutomaticExecutionOrchestrator**
                from src.services.automatic_execution_orchestrator import AutomaticExecutionOrchestrator
                
                # Crear instancia del orquestador
                orchestrator = AutomaticExecutionOrchestrator(ollama_service, tool_manager)
                
                # Ejecutar tarea con herramientas automáticamente (sin await ya que no es async)
                result = orchestrator.execute_task_with_tools_sync(message, task_id)
                
                print(f"✅ AutomaticExecutionOrchestrator completó tarea con {result.get('tools_count', 0)} herramientas")
                
                return jsonify({
                    'response': result.get('final_response', result.get('plan', 'Tarea procesada')),
                    'execution_plan': {
                        'task_id': task_id,
                        'title': message,
                        'executed_tools': result.get('executed_tools', []),
                        'tools_count': result.get('tools_count', 0),
                        'execution_time': result.get('execution_time', 0),
                        'autonomous_execution': result.get('autonomous_execution', True)
                    },
                    'tool_calls': result.get('executed_tools', []),
                    'autonomous_execution': result.get('autonomous_execution', True),
                    'orchestrator_used': True,
                    'model': ollama_model,
                    'timestamp': datetime.now().isoformat()
                })
                    
            except Exception as e:
                print(f"❌ Error en AutomaticExecutionOrchestrator: {str(e)}")
                # Fallback a ejecución con Ollama
                try:
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
                except Exception as fallback_error:
                    print(f"❌ Error en fallback: {str(fallback_error)}")
                    return jsonify({
                        'response': f"Error procesando tarea: {message}",
                        'autonomous_execution': False,
                        'error': str(e),
                        'fallback_error': str(fallback_error),
                        'timestamp': datetime.now().isoformat()
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