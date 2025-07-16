"""
Rutas API del agente - Versión simplificada
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
from pathlib import Path
from werkzeug.utils import secure_filename
from src.utils.json_encoder import MongoJSONEncoder, mongo_json_serializer

logger = logging.getLogger(__name__)

agent_bp = Blueprint('agent', __name__)

# Almacenamiento temporal para compartir conversaciones
shared_conversations = {}

# Almacenamiento temporal para archivos por tarea
task_files = {}

# Inicializar servicios básicos
from src.services.ollama_service import OllamaService
from src.tools.tool_manager import ToolManager

ollama_service = OllamaService()
tool_manager = ToolManager()

@agent_bp.route('/health', methods=['GET'])
def health_check():
    """Verificar salud del agente"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'agent_version': '1.0.0',
        'memory_status': 'disabled'
    })

@agent_bp.route('/status', methods=['GET'])
def get_status():
    """Obtener estado del agente"""
    try:
        # Verificar modelos disponibles
        models = ollama_service.get_available_models()
        tools = tool_manager.get_available_tools()
        
        return jsonify({
            'status': 'operational',
            'ollama_status': 'connected' if models else 'disconnected',
            'available_models': models,
            'available_tools': [tool['name'] for tool in tools],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@agent_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal para chat - Versión simplificada
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Obtener task_id del contexto
        task_id = context.get('task_id', str(uuid.uuid4()))
        
        # Detectar modo de búsqueda desde el mensaje
        original_message = message
        search_mode = None
        if message.startswith('[WebSearch]'):
            search_mode = 'websearch'
            message = message.replace('[WebSearch]', '').strip()
        elif message.startswith('[DeepResearch]'):
            search_mode = 'deepsearch'
            message = message.replace('[DeepResearch]', '').strip()
        
        def is_task_requiring_tools(message):
            """Detectar si el mensaje es una tarea específica que requiere herramientas"""
            message_lower = message.lower()
            
            # Primero: Detectar saludos y conversación casual (retorna False inmediatamente)
            casual_only_phrases = [
                'hola', 'hello', 'hi', 'buenos días', 'buenas tardes', 'buenas noches',
                'gracias', 'thank you', 'thanks', 'de nada', 'por favor',
                'qué tal', 'cómo estás', 'how are you', 'adiós', 'bye', 'hasta luego',
                'cómo te llamas', 'what is your name', 'quien eres', 'who are you'
            ]
            
            # Si es SOLO una frase casual (sin más contenido), no es tarea
            if any(phrase == message_lower.strip() for phrase in casual_only_phrases):
                return False
            
            # Segundo: Detectar indicadores de TAREA (retorna True si encuentra)
            task_indicators = [
                # Comandos explícitos
                'ejecuta', 'ejecutar', 'run', 'comando', 'command',
                # Análisis y procesamiento
                'analiza', 'analizar', 'analyze', 'procesa', 'procesar',
                # Búsqueda activa
                'busca', 'buscar', 'search', 'encuentra', 'encontrar',
                # Creación/modificación/generación
                'crea', 'crear', 'create', 'genera', 'generar', 'generate', 'modifica', 'modificar',
                'haz', 'hacer', 'do', 'make', 'build', 'construye', 'construir',
                'desarrolla', 'desarrollar', 'develop', 'programa', 'programar',
                # Gestión de archivos
                'lista', 'listar', 'list', 'mostrar archivos', 'show files',
                'descarga', 'descargar', 'download', 'sube', 'subir', 'upload',
                # Investigación y reportes
                'investiga', 'investigar', 'research', 'explora', 'explorar',
                'informe', 'report', 'reporte', 'estudio', 'study', 'análisis',
                # Operaciones de sistema
                'verifica', 'verificar', 'check', 'monitorea', 'monitorear', 'instala', 'instalar',
                # Palabras clave de resultado
                'sobre', 'acerca de', 'about', 'mejores prácticas', 'best practices'
            ]
            
            # Verificar si contiene indicadores de tarea
            has_task_indicator = any(indicator in message_lower for indicator in task_indicators)
            
            # Verificar comandos específicos de sistema
            command_patterns = ['ls ', 'cd ', 'pwd', 'ps ', 'mkdir', 'rm ', 'cp ', 'mv ', 'chmod', 'grep']
            has_command = any(cmd in message_lower for cmd in command_patterns)
            
            # Verificar patrones de solicitud de trabajo
            work_patterns = [
                'web sobre', 'sitio web', 'website', 'aplicación', 'app',
                'base de datos', 'database', 'sistema', 'system'
            ]
            has_work_pattern = any(pattern in message_lower for pattern in work_patterns)
            
            return has_task_indicator or has_command or has_work_pattern
        
        # Verificar si es una tarea que requiere herramientas
        if not is_task_requiring_tools(message) and not search_mode:
            # Es conversación normal - usar respuesta estándar del LLM
            logger.info(f"💬 Conversación normal detectada - no ejecutar herramientas")
            
            # Generar respuesta normal usando Ollama
            response_data = ollama_service.generate_response(message)
            
            if response_data.get('error'):
                raise Exception(response_data['error'])
            
            agent_response = response_data.get('response', 'No se pudo generar respuesta')
            
            return jsonify({
                'response': agent_response,
                'task_id': task_id,
                'model': response_data.get('model', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'memory_used': False,
                'conversation_mode': True
            })
        
        # Es una tarea específica - ejecutar herramientas
        logger.info(f"🛠️ Tarea específica detectada - ejecutar herramientas")
        
        # Función para ejecutar herramientas
        def execute_task_with_tools():
            """Ejecutar tarea con herramientas automáticamente"""
            # Analizar el mensaje para determinar qué herramientas usar
            tools_to_use = []
            
            # Detectar si necesita ejecutar comandos shell
            if any(keyword in message.lower() for keyword in ['comando', 'ejecuta', 'shell', 'ls', 'cd', 'mkdir', 'rm', 'cat', 'grep', 'find', 'chmod', 'chown', 'ps', 'kill', 'pwd']):
                tools_to_use.append('shell')
            
            # Detectar si necesita gestión de archivos
            if any(keyword in message.lower() for keyword in ['archivo', 'file', 'directorio', 'folder', 'lista', 'listar', 'mostrar', 'crear', 'eliminar', 'leer', 'escribir', 'copiar', 'mover']):
                tools_to_use.append('file_manager')
            
            # Detectar si necesita búsqueda web (mejorado)
            if any(keyword in message.lower() for keyword in ['buscar', 'busca', 'search', 'información', 'noticias', 'web', 'internet', 'google', 'investiga', 'investigar', 'informe', 'report', 'reporte', 'sobre', 'acerca de', 'about', 'mejores prácticas', 'best practices']) or search_mode:
                tools_to_use.append('web_search')
            
            # Si no detecta herramientas específicas, usar herramientas por defecto según el contexto
            if not tools_to_use:
                if any(keyword in message.lower() for keyword in ['analiza', 'analizar', 'procesa', 'procesar', 'verifica', 'verificar', 'genera', 'generar', 'crea', 'crear', 'haz', 'hacer', 'informe', 'report']):
                    tools_to_use = ['web_search']  # Para tareas de investigación/generación
                else:
                    tools_to_use = ['shell']  # Por defecto para tareas generales
            
            # Ejecutar herramientas detectadas
            results = []
            for tool_name in tools_to_use:
                try:
                    # Preparar parámetros según el tipo de herramienta
                    if tool_name == 'shell':
                        # Extraer comando del mensaje
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
                    
                    # Ejecutar herramienta
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
            
            return results
        
        # Ejecutar tareas con herramientas
        tool_results = execute_task_with_tools()
        
        # Generar respuesta inteligente basada en los resultados
        if search_mode == 'websearch' or search_mode == 'deepsearch':
            # Para búsquedas, formatear resultados de manera más útil
            response_parts = [f"🔍 **Búsqueda Completada**\n\n**Consulta:** {message}\n"]
            
            # Buscar resultados de web_search
            web_results = [r for r in tool_results if r['tool'] == 'web_search']
            if web_results and web_results[0]['success']:
                search_data = web_results[0]['result']
                if 'results' in search_data:
                    response_parts.append("📊 **Resultados Encontrados:**\n")
                    for i, result in enumerate(search_data['results'][:5], 1):
                        title = result.get('title', 'Sin título')
                        url = result.get('url', 'Sin URL')
                        snippet = result.get('snippet', 'Sin descripción')
                        response_parts.append(f"**{i}. {title}**")
                        response_parts.append(f"   🔗 {url}")
                        response_parts.append(f"   📝 {snippet[:150]}...")
                        response_parts.append("")
                    
                    # Agregar un análisis inteligente usando Ollama
                    analysis_prompt = f"Basándote en los siguientes resultados de búsqueda sobre '{message}', proporciona un análisis útil y un resumen de los hallazgos principales:\n\n"
                    for result in search_data['results'][:3]:
                        analysis_prompt += f"- {result.get('title', 'Sin título')}: {result.get('snippet', 'Sin descripción')}\n"
                    
                    try:
                        analysis_response = ollama_service.generate_response(analysis_prompt)
                        if not analysis_response.get('error'):
                            response_parts.append("🧠 **Análisis Inteligente:**\n")
                            response_parts.append(analysis_response.get('response', 'No se pudo generar análisis'))
                    except Exception as e:
                        logger.warning(f"Error generando análisis: {e}")
            
            final_response = "\n".join(response_parts)
        else:
            # Para otras tareas, usar formato estándar
            response_parts = [f"🤖 **Ejecución Completada**\n\n**Tarea:** {message}\n"]
            
            if tool_results:
                response_parts.append("🛠️ **Herramientas Ejecutadas:**\n")
                for i, result in enumerate(tool_results, 1):
                    status = "✅ EXITOSO" if result['success'] else "❌ ERROR"
                    response_parts.append(f"{i}. **{result['tool']}**: {status}")
                    
                    if result['success'] and result['result']:
                        # Formatear resultado según el tipo de herramienta
                        if result['tool'] == 'shell':
                            if 'output' in result['result']:
                                response_parts.append(f"```\n{result['result']['output']}\n```")
                        elif result['tool'] == 'file_manager':
                            if 'files' in result['result']:
                                response_parts.append("📁 **Archivos encontrados:**")
                                for file_info in result['result']['files'][:5]:  # Mostrar solo los primeros 5
                                    response_parts.append(f"• {file_info}")
                        elif result['tool'] == 'web_search':
                            if 'results' in result['result']:
                                response_parts.append("🔍 **Resultados de búsqueda:**")
                                for search_result in result['result']['results'][:3]:  # Mostrar solo los primeros 3
                                    response_parts.append(f"• {search_result.get('title', 'Sin título')}")
                        else:
                            response_parts.append(f"📊 **Resultado:** {str(result['result'])[:200]}...")
                    elif not result['success']:
                        response_parts.append(f"⚠️ **Error:** {result['result'].get('error', 'Error desconocido')}")
                    
                    response_parts.append("")  # Línea en blanco
            
            final_response = "\n".join(response_parts)
        
        return jsonify({
            'response': final_response,
            'tool_results': tool_results,
            'tools_executed': len(tool_results),
            'task_id': task_id,
            'execution_status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'model': 'tool-execution-agent',
            'memory_used': False,
            'search_mode': search_mode
        })
            
    except Exception as e:
        logger.error(f"Error en chat: {str(e)}")
        return jsonify({
            'error': f'Error procesando mensaje: {str(e)}',
            'task_id': context.get('task_id', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }), 500

@agent_bp.route('/generate-suggestions', methods=['POST'])
def generate_suggestions():
    """Generar sugerencias dinámicas"""
    try:
        data = request.get_json()
        context = data.get('context', {})
        
        # Sugerencias básicas
        suggestions = [
            {
                'title': 'Buscar noticias de tecnología',
                'description': 'Realizar búsqueda web sobre tecnología actual',
                'type': 'web_search'
            },
            {
                'title': 'Listar archivos del proyecto',
                'description': 'Mostrar estructura de archivos',
                'type': 'file_manager'
            },
            {
                'title': 'Verificar estado del sistema',
                'description': 'Ejecutar comandos de diagnóstico',
                'type': 'shell'
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
            'suggestions': []
        }), 500

@agent_bp.route('/generate-plan', methods=['POST'])
def generate_plan():
    """Generar plan de tarea"""
    try:
        data = request.get_json()
        task_title = data.get('task_title', '')
        
        # Plan básico basado en el título
        plan = []
        if 'web' in task_title.lower() or 'search' in task_title.lower():
            plan = [
                {'step': 1, 'title': 'Inicializar búsqueda', 'description': 'Preparar parámetros de búsqueda', 'completed': False, 'active': True},
                {'step': 2, 'title': 'Ejecutar búsqueda web', 'description': 'Buscar información relevante', 'completed': False, 'active': False},
                {'step': 3, 'title': 'Procesar resultados', 'description': 'Analizar y formatear resultados', 'completed': False, 'active': False},
                {'step': 4, 'title': 'Generar informe', 'description': 'Crear resumen de hallazgos', 'completed': False, 'active': False}
            ]
        elif 'archivo' in task_title.lower() or 'file' in task_title.lower():
            plan = [
                {'step': 1, 'title': 'Verificar ruta', 'description': 'Confirmar ubicación de archivos', 'completed': False, 'active': True},
                {'step': 2, 'title': 'Listar contenido', 'description': 'Mostrar archivos y directorios', 'completed': False, 'active': False},
                {'step': 3, 'title': 'Procesar archivos', 'description': 'Ejecutar operaciones requeridas', 'completed': False, 'active': False}
            ]
        else:
            plan = [
                {'step': 1, 'title': 'Analizar tarea', 'description': 'Entender requisitos', 'completed': False, 'active': True},
                {'step': 2, 'title': 'Ejecutar herramientas', 'description': 'Usar herramientas necesarias', 'completed': False, 'active': False},
                {'step': 3, 'title': 'Generar resultado', 'description': 'Compilar resultados finales', 'completed': False, 'active': False}
            ]
        
        return jsonify({
            'plan': plan,
            'task_title': task_title,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generando plan: {str(e)}")
        return jsonify({
            'error': str(e),
            'plan': []
        }), 500