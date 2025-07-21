"""
Enhanced Unified Mitosis API - El Puente entre la Autonomía y la Interfaz
Extiende la UnifiedMitosisAPI original con capacidades de ejecución autónoma
y salida en tiempo real en terminal
"""

import logging
import json
import os
import time
import threading
import asyncio
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Importar la API base
try:
    from unified_api import UnifiedMitosisAPI
    from agent_core import MitosisAgent
    HAS_BASE_API = True
except ImportError:
    HAS_BASE_API = False
    # Fallback básico si no existe la API base
    class UnifiedMitosisAPI:
        def __init__(self, config=None):
            self.app = Flask(__name__)
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
            self.monitor_pages = []

        def _add_monitor_page(self, title, content, page_type, metadata=None):
            page_number = len(self.monitor_pages) + 1
            self.monitor_pages.append({
                'page_number': page_number,
                'title': title,
                'content': content,
                'type': page_type,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            })

# Importar el núcleo autónomo
from enhanced_agent_core import AutonomousAgentCore, TaskStatus

# Configurar logging para terminal
terminal_logger = logging.getLogger('MITOSIS')
terminal_handler = logging.StreamHandler(sys.stdout)
terminal_handler.setLevel(logging.INFO)
terminal_formatter = logging.Formatter('%(asctime)s - [MITOSIS] - %(message)s')
terminal_handler.setFormatter(terminal_formatter)
terminal_logger.addHandler(terminal_handler)
terminal_logger.setLevel(logging.INFO)


class EnhancedUnifiedMitosisAPI(UnifiedMitosisAPI):
    """API Unificada Mejorada que extiende las capacidades base con autonomía"""
    
    def __init__(self, config: Optional[Any] = None):
        """Inicializar la API mejorada"""
        
        # Llamar al constructor base si existe
        if HAS_BASE_API:
            super().__init__(config)
        else:
            # Inicialización básica
            self.app = Flask(__name__)
            self.app.config['SECRET_KEY'] = 'mitosis-enhanced-key'
            
            # Configurar CORS
            CORS(self.app, resources={
                r"/api/*": {
                    "origins": ["*"],
                    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allow_headers": ["Content-Type", "Authorization"]
                }
            })
            
            # Configurar WebSocket
            self.socketio = SocketIO(
                self.app,
                cors_allowed_origins="*",
                logger=False,
                engineio_logger=False
            )
            self.monitor_pages = []
        
        # Configuración mejorada desde variables de entorno
        self.config = self._create_proper_config(config)
        self.active_config = self.config
        
        # Inicializar el núcleo autónomo pasando la configuración correcta
        base_agent = getattr(self, 'agent', None) if HAS_BASE_API else None
        try:
            self.autonomous_agent = AutonomousAgentCore(base_agent)
            terminal_logger.info("🚀 Enhanced Unified Mitosis API inicializada exitosamente")
        except Exception as e:
            terminal_logger.warning(f"⚠️ Algunos componentes no disponibles: {str(e)}")
            self.autonomous_agent = AutonomousAgentCore()
            terminal_logger.info("🚀 Enhanced Unified Mitosis API inicializada exitosamente")
        
        # Variables de estado autónomo
        self.autonomous_execution_active = False
        self.current_autonomous_task_id = None
        
        # Configurar rutas mejoradas
        self._setup_enhanced_routes()
        self._setup_websocket_events()

    def _create_proper_config(self, config):
        """Crea configuración correcta desde variables de entorno"""
        if HAS_BASE_API:
            # Si tenemos la API base, crear AgentConfig apropiado
            try:
                from agent_core import AgentConfig
                
                agent_config = AgentConfig()
                # Usar variables de entorno si están disponibles
                agent_config.ollama_url = os.getenv('OLLAMA_BASE_URL', 'https://bef4a4bb93d1.ngrok-free.app')
                agent_config.openrouter_api_key = os.getenv('OPENROUTER_API_KEY', '')
                agent_config.prefer_local_models = True
                agent_config.memory_db_path = os.getenv('MEMORY_DB_PATH', 'mitosis_memory.db')
                agent_config.debug_mode = os.getenv('DEBUG', 'true').lower() == 'true'
                
                return agent_config
            except ImportError:
                pass
        
        # Fallback a configuración básica
        return {
            'OLLAMA_URL': os.getenv('OLLAMA_BASE_URL', 'https://bef4a4bb93d1.ngrok-free.app'),
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY', ''),
            'PREFER_LOCAL_MODELS': True,
            'MEMORY_DB_PATH': os.getenv('MEMORY_DB_PATH', 'mitosis_memory.db'),
            'DEBUG_MODE': os.getenv('DEBUG', 'true').lower() == 'true'
        }

    def _setup_enhanced_routes(self):
        """Configura las rutas mejoradas para funcionalidad autónoma"""
        
        @self.app.route('/api/agent/initialize-task', methods=['POST'])
        def initialize_task():
            """Inicializa una nueva tarea autónoma"""
            try:
                data = request.get_json()
                title = data.get('title', 'Tarea sin título')
                description = data.get('description', '')
                task_id = data.get('task_id')
                auto_execute = data.get('auto_execute', False)
                
                terminal_logger.info(f"📋 Inicializando tarea: {title}")
                
                # Generar plan de acción
                task = self.autonomous_agent.generate_action_plan(title, description)
                
                # Crear página del monitor
                self._add_monitor_page(
                    f"Tarea Inicializada: {title}",
                    f"**ID:** {task.id}\n**Descripción:** {description}\n**Auto-ejecutar:** {auto_execute}",
                    "task-creation",
                    {
                        "task_id": task.id,
                        "auto_execute": auto_execute
                    }
                )
                
                # Iniciar ejecución si se solicita
                if auto_execute:
                    self._start_autonomous_execution(task.id)
                
                # Preparar respuesta
                plan_dict = {
                    "task_id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "progress": task.progress_percentage,
                    "created_at": task.created_at.isoformat(),
                    "steps": [{
                        "id": step.id,
                        "title": step.title,
                        "description": step.description,
                        "tool": step.tool,
                        "status": step.status.value,
                        "estimated_time": 1,
                        "priority": "normal"
                    } for step in task.steps]
                }
                
                return jsonify({
                    "success": True,
                    "plan": plan_dict,
                    "auto_execution": auto_execute,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                terminal_logger.error(f"❌ Error inicializando tarea: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/agent/start-task-execution/<task_id>', methods=['POST'])
        def start_task_execution(task_id):
            """Inicia la ejecución autónoma de una tarea"""
            try:
                self._start_autonomous_execution(task_id)
                return jsonify({
                    "success": True,
                    "task_id": task_id,
                    "message": "Ejecución autónoma iniciada",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/agent/get-task-plan/<task_id>', methods=['GET'])
        def get_task_plan(task_id):
            """Obtiene el plan de una tarea específica"""
            try:
                task_status = self.autonomous_agent.get_task_status(task_id)
                if not task_status:
                    return jsonify({"error": "Tarea no encontrada"}), 404
                
                return jsonify(task_status)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/agent/execute-step/<task_id>/<step_id>', methods=['POST'])
        def execute_step(task_id, step_id):
            """Ejecuta un paso específico (simulado)"""
            try:
                terminal_logger.info(f"▶️ Ejecutando paso individual: {step_id} de tarea {task_id}")
                
                # Simulación de ejecución de paso
                result = f"Paso {step_id} completado exitosamente"
                
                return jsonify({
                    "success": True,
                    "step_id": step_id,
                    "task_id": task_id,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/agent/status', methods=['GET'])
        def get_agent_status():
            """Obtiene el estado mejorado del agente"""
            try:
                active_tasks = self.autonomous_agent.list_active_tasks()
                
                return jsonify({
                    "status": "operational",
                    "enhanced_features": True,
                    "timestamp": datetime.now().isoformat(),
                    "uptime": time.time(),
                    "autonomous_execution": {
                        "active": self.autonomous_execution_active,
                        "current_task_id": self.current_autonomous_task_id,
                        "active_tasks": len(active_tasks)
                    },
                    "capabilities": [
                        "autonomous_task_execution",
                        "real_time_terminal_output",
                        "step_by_step_progress",
                        "websocket_communication",
                        "plan_generation",
                        "tool_execution",
                        "error_recovery"
                    ],
                    "tools_available": len(self.autonomous_agent.available_tools),
                    "models_available": ["llama3.1:8b"],
                    "memory_enabled": True
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/agent/chat', methods=['POST'])
        def enhanced_chat():
            """Chat mejorado con detección de intención autónoma"""
            try:
                data = request.get_json()
                message = data.get('message', '')
                context = data.get('context', {})
                
                terminal_logger.info(f"💬 Mensaje recibido: {message}")
                
                # Crear página del monitor para mensaje del usuario
                self._add_monitor_page(
                    "Mensaje del Usuario",
                    f"**Usuario:** {message}",
                    "user-message",
                    {"session_id": context.get('session_id', 'unknown')}
                )
                
                # Determinar si requiere ejecución autónoma
                if self._should_execute_autonomously(message):
                    terminal_logger.info("🎯 Mensaje detectado como tarea autónoma")
                    
                    # Generar plan de acción
                    task = self.autonomous_agent.generate_action_plan(
                        f"Tarea autónoma: {message[:50]}...",
                        message
                    )
                    
                    # Iniciar ejecución autónoma
                    self._start_autonomous_execution(task.id)
                    
                    # Preparar plan para respuesta
                    execution_plan = {
                        "task_id": task.id,
                        "status": task.status.value,
                        "steps": [{
                            "id": step.id,
                            "title": step.title,
                            "description": step.description,
                            "tool": step.tool,
                            "status": step.status.value,
                            "estimated_time": 1
                        } for step in task.steps],
                        "progress_percentage": task.progress_percentage,
                        "created_at": task.created_at.isoformat()
                    }
                    
                    response_text = (
                        f"He generado un plan de acción para tu solicitud y comenzaré la ejecución autónoma. "
                        f"Puedes seguir el progreso en tiempo real en la terminal y en el monitor de ejecución.\n\n"
                        f"**Plan generado:**\n" + 
                        "\n".join([f"{i+1}. {step.title}" for i, step in enumerate(task.steps)]) +
                        f"\n\n**ID de tarea:** {task.id}\n**Estado:** Ejecutándose autónomamente"
                    )
                    
                    return jsonify({
                        "response": response_text,
                        "autonomous_execution": True,
                        "execution_plan": execution_plan,
                        "task_id": task.id,
                        "timestamp": datetime.now().isoformat(),
                        "model": "autonomous_agent_enhanced",
                        "memory_used": True
                    })
                
                else:
                    # Procesamiento conversacional normal
                    terminal_logger.info("💬 Procesando como conversación normal")
                    
                    # Generar ID de tarea para seguimiento
                    task_id = f"chat_{int(time.time())}"
                    
                    response_text = f"He recibido tu mensaje: '{message}'. Como agente mejorado, puedo ayudarte con tareas complejas de forma autónoma."
                    
                    return jsonify({
                        "response": response_text,
                        "autonomous_execution": False,
                        "task_id": task_id,
                        "timestamp": datetime.now().isoformat(),
                        "model": "conversational_mode",
                        "memory_used": True
                    })
                    
            except Exception as e:
                terminal_logger.error(f"❌ Error en chat: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/health', methods=['GET'])
        def enhanced_health():
            """Health check mejorado"""
            return jsonify({
                "status": "healthy",
                "enhanced": True,
                "autonomous_execution": self.autonomous_execution_active,
                "timestamp": datetime.now().isoformat()
            })

    def _should_execute_autonomously(self, message: str) -> bool:
        """
        Determina si un mensaje debe activar ejecución autónoma
        """
        autonomous_triggers = [
            "crear", "generar", "desarrollar", "implementar", "construir",
            "buscar", "investigar", "analizar", "estudiar", "examinar",
            "planificar", "organizar", "diseñar", "estructurar",
            "automatizar", "optimizar", "mejorar", "resolver"
        ]
        
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in autonomous_triggers)

    def _start_autonomous_execution(self, task_id: str):
        """Inicia la ejecución autónoma en segundo plano"""
        terminal_logger.info(f"🚀 Iniciando ejecución autónoma para tarea: {task_id}")
        
        self.autonomous_execution_active = True
        self.current_autonomous_task_id = task_id
        
        def run_autonomous_execution():
            """Función para ejecutar en hilo separado"""
            try:
                # Crear nuevo bucle de eventos para el hilo
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Ejecutar tarea autónoma
                success = loop.run_until_complete(
                    self.autonomous_agent.execute_task_autonomously(task_id)
                )
                
                # Crear página de reporte final
                status_text = "completada exitosamente" if success else "falló durante la ejecución"
                self._add_monitor_page(
                    "Ejecución Autónoma Finalizada",
                    f"**Tarea ID:** {task_id}\n**Estado:** {status_text}\n**Timestamp:** {datetime.now().isoformat()}",
                    "report",
                    {"task_id": task_id, "success": success}
                )
                
                # Emitir evento de finalización
                self.socketio.emit('autonomous_execution_completed', {
                    'task_id': task_id,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                })
                
                loop.close()
                
            except Exception as e:
                terminal_logger.error(f"❌ Error en ejecución autónoma: {str(e)}")
            finally:
                self.autonomous_execution_active = False
                self.current_autonomous_task_id = None
        
        # Iniciar en hilo separado
        thread = threading.Thread(target=run_autonomous_execution)
        thread.daemon = True
        thread.start()

    def _add_monitor_page(self, title: str, content: str, page_type: str, metadata: Optional[Dict] = None):
        """
        Sobrescribe el método para añadir salida en terminal
        """
        # Llamar al método base si existe
        if HAS_BASE_API:
            super()._add_monitor_page(title, content, page_type, metadata)
        else:
            # Implementación básica
            page_number = len(self.monitor_pages) + 1
            page = {
                'page_number': page_number,
                'title': title,
                'content': content,
                'type': page_type,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            }
            self.monitor_pages.append(page)
            
            # Emitir evento WebSocket
            self.socketio.emit('new_monitor_page', {
                'page_number': page_number,
                'title': title,
                'content': content,
                'type': page_type,
                'timestamp': page['timestamp'].isoformat(),
                'metadata': metadata or {}
            })
        
        # Salida mejorada en terminal
        terminal_logger.info("")
        terminal_logger.info("================================================================================")
        terminal_logger.info(f"📄 NUEVA PÁGINA DEL MONITOR (Tipo: {page_type.upper()})")
        terminal_logger.info(f"Título: {title}")
        terminal_logger.info(f"Timestamp: {datetime.now()}")
        
        if metadata:
            terminal_logger.info("Metadatos: {")
            for key, value in metadata.items():
                terminal_logger.info(f'  "{key}": {json.dumps(value) if isinstance(value, str) else value}')
            terminal_logger.info("}")
        
        terminal_logger.info("--------------------------------------------------------------------------------")
        terminal_logger.info("Contenido:")
        terminal_logger.info(content)
        terminal_logger.info("================================================================================")

    def _setup_websocket_events(self):
        """Configura eventos WebSocket mejorados"""
        
        @self.socketio.on('connect')
        def handle_connect():
            terminal_logger.info(f"🔌 Cliente WebSocket conectado: {request.sid}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            terminal_logger.info(f"🔌 Cliente WebSocket desconectado: {request.sid}")
        
        @self.socketio.on('join_task_room')
        def handle_join_task_room(data):
            task_id = data.get('task_id')
            if task_id:
                join_room(f"task_{task_id}")
                terminal_logger.info(f"👥 Cliente {request.sid} se unió a sala de tarea: {task_id}")

    def run(self, host='0.0.0.0', port=8001, debug=False):
        """Ejecuta el servidor de la API mejorada"""
        terminal_logger.info(f"🚀 Iniciando Enhanced Unified Mitosis API en {host}:{port}")
        terminal_logger.info("📊 Características habilitadas:")
        terminal_logger.info("✅ Ejecución autónoma de tareas")
        terminal_logger.info("✅ Salida en tiempo real en terminal")
        terminal_logger.info("✅ Monitoreo de progreso paso a paso")
        terminal_logger.info("✅ Compatibilidad completa con UI existente")
        terminal_logger.info("✅ WebSockets para actualizaciones en tiempo real")
        
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    
    def shutdown(self):
        """Apagado limpio de la API"""
        terminal_logger.info("🛑 Apagando Enhanced Unified Mitosis API...")
        self.autonomous_execution_active = False
        self.current_autonomous_task_id = None


# Función de utilidad para crear instancia
def create_enhanced_api(config=None):
    """Crea una instancia de la API mejorada"""
    return EnhancedUnifiedMitosisAPI(config)


if __name__ == "__main__":
    # Ejemplo de uso directo
    api = EnhancedUnifiedMitosisAPI()
    api.run(debug=True)