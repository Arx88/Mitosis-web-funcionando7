"""
Enhanced Unified Mitosis API - El Puente entre la Autonomía y la Interfaz
Extiende la UnifiedMitosisAPI original con capacidades de ejecución autónoma
y salida en tiempo real en terminal
"""

import logging
import json
import time
import threading
import asyncio
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Configurar logging para terminal
terminal_logger = logging.getLogger('MITOSIS')
terminal_handler = logging.StreamHandler(sys.stdout)
terminal_handler.setLevel(logging.INFO)
terminal_formatter = logging.Formatter('%(asctime)s - [MITOSIS] - %(message)s')
terminal_handler.setFormatter(terminal_formatter)
terminal_logger.addHandler(terminal_handler)
terminal_logger.setLevel(logging.INFO)

class EnhancedUnifiedMitosisAPI:
    """API Unificada Mejorada que extiende las capacidades base con autonomía"""
    
    def __init__(self, config: Optional[Any] = None):
        """Inicializar la API mejorada"""
        
        # Configuración base
        self.config = config
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
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )
        
        # Estado de ejecución autónoma
        self.autonomous_execution_active = False
        self.current_autonomous_task_id = None
        
        # Páginas del monitor (para compatibilidad con UI)
        self.monitor_pages = []
        self.page_counter = 0
        
        # Importar y inicializar el agente autónomo
        try:
            from enhanced_agent_core import AutonomousAgentCore
            # Simulamos el agente base para inicialización
            base_agent = None  # Se inicializaría con el MitosisAgent real
            self.autonomous_agent = AutonomousAgentCore(base_agent)
            terminal_logger.info("✅ AutonomousAgentCore inicializado exitosamente")
        except Exception as e:
            terminal_logger.error(f"❌ Error inicializando AutonomousAgentCore: {e}")
            self.autonomous_agent = None
        
        # Registrar rutas
        self._register_routes()
        self._register_websocket_events()
        
        terminal_logger.info("🚀 Enhanced Unified Mitosis API inicializada exitosamente")
    
    def _register_routes(self):
        """Registra todas las rutas de la API mejorada"""
        
        # Ruta de salud básica
        @self.app.route('/api/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'enhanced': True,
                'autonomous_execution': self.autonomous_execution_active
            })
        
        # Ruta mejorada para inicializar tareas autónomas
        @self.app.route('/api/agent/initialize-task', methods=['POST'])
        def initialize_task():
            """Inicializa una nueva tarea con ejecución autónoma opcional"""
            try:
                data = request.get_json()
                
                task_title = data.get('title', 'Tarea Autónoma')
                task_description = data.get('description', '')
                auto_execute = data.get('auto_execute', False)
                task_id = data.get('task_id', f"task_{int(time.time())}")
                
                terminal_logger.info(f"📋 Inicializando tarea: {task_title}")
                
                if self.autonomous_agent:
                    # Generar plan de acción
                    task = self.autonomous_agent.generate_action_plan(
                        task_title, task_description
                    )
                    
                    # Crear página del monitor
                    self._add_monitor_page(
                        title=f"Tarea Inicializada: {task_title}",
                        content=f"""**ID:** {task_id}
**Descripción:** {task_description}
**Auto-ejecutar:** {auto_execute}""",
                        page_type="task-creation",
                        metadata={
                            "task_id": task_id,
                            "auto_execute": auto_execute
                        }
                    )
                    
                    # Iniciar ejecución autónoma si es requerido
                    if auto_execute:
                        self._start_autonomous_execution(task.id)
                    
                    return jsonify({
                        'success': True,
                        'task_id': task.id,
                        'plan': self._serialize_task_plan(task),
                        'auto_execution_started': auto_execute
                    })
                
                return jsonify({
                    'error': 'Agente autónomo no disponible'
                }), 500
                
            except Exception as e:
                terminal_logger.error(f"❌ Error inicializando tarea: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Ruta para iniciar ejecución de tarea
        @self.app.route('/api/agent/start-task-execution/<task_id>', methods=['POST'])
        def start_task_execution(task_id):
            """Inicia la ejecución autónoma de una tarea planificada"""
            try:
                if self.autonomous_agent:
                    success = self._start_autonomous_execution(task_id)
                    return jsonify({
                        'success': success,
                        'task_id': task_id,
                        'execution_started': success
                    })
                
                return jsonify({
                    'error': 'Agente autónomo no disponible'
                }), 500
                
            except Exception as e:
                terminal_logger.error(f"❌ Error iniciando ejecución: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Ruta para obtener plan de tarea
        @self.app.route('/api/agent/get-task-plan/<task_id>', methods=['GET'])
        def get_task_plan(task_id):
            """Obtiene el plan detallado y estado actual de una tarea"""
            try:
                if self.autonomous_agent:
                    task_status = self.autonomous_agent.get_task_status(task_id)
                    if task_status:
                        return jsonify({
                            'success': True,
                            'task_plan': task_status
                        })
                
                return jsonify({
                    'error': 'Tarea no encontrada'
                }), 404
                
            except Exception as e:
                terminal_logger.error(f"❌ Error obteniendo plan: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Ruta de chat mejorada con detección de intención autónoma
        @self.app.route('/api/agent/chat', methods=['POST'])
        def enhanced_chat():
            """Procesa mensajes con detección de intención autónoma"""
            try:
                data = request.get_json()
                message = data.get('message', '')
                
                # Añadir mensaje del usuario al monitor
                self._add_monitor_page(
                    title="Mensaje del Usuario",
                    content=f"**Usuario:** {message}",
                    page_type="USER-MESSAGE",
                    metadata={"session_id": "current"}
                )
                
                # Detectar si requiere ejecución autónoma
                if self._should_execute_autonomously(message):
                    terminal_logger.info("🤖 Detección de intención autónoma activada")
                    
                    # Generar plan de acción
                    if self.autonomous_agent:
                        task = self.autonomous_agent.generate_action_plan(
                            f"Tarea autónoma: {message[:50]}...",
                            message
                        )
                        
                        # Iniciar ejecución autónoma
                        self._start_autonomous_execution(task.id)
                        
                        response = f"""He generado un plan de acción para tu solicitud y comenzaré la ejecución autónoma. Puedes seguir el progreso en tiempo real en la terminal y en el monitor de ejecución.

**Plan generado:**
{self._format_plan_for_response(task)}

**ID de tarea:** {task.id}
**Estado:** Ejecutándose autónomamente"""
                        
                        return jsonify({
                            'response': response,
                            'autonomous_execution': True,
                            'execution_plan': self._serialize_task_plan(task),
                            'timestamp': datetime.now().isoformat(),
                            'model': 'autonomous_agent_enhanced',
                            'memory_used': True,
                            'task_id': task.id
                        })
                
                # Respuesta conversacional normal (simulada)
                response = f"He recibido tu mensaje: '{message}'. Como agente mejorado, puedo ayudarte con tareas complejas de forma autónoma."
                
                return jsonify({
                    'response': response,
                    'autonomous_execution': False,
                    'timestamp': datetime.now().isoformat(),
                    'model': 'conversational_mode',
                    'memory_used': True,
                    'task_id': f"chat_{int(time.time())}"
                })
                
            except Exception as e:
                terminal_logger.error(f"❌ Error en chat mejorado: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Ruta de estado mejorada
        @self.app.route('/api/agent/status', methods=['GET'])
        def enhanced_status():
            """Proporciona estado detallado del agente incluyendo capacidades autónomas"""
            try:
                status = {
                    'status': 'operational',
                    'timestamp': datetime.now().isoformat(),
                    'uptime': time.time(),
                    'autonomous_execution': {
                        'active': self.autonomous_execution_active,
                        'current_task_id': self.current_autonomous_task_id,
                        'active_tasks': len(self.autonomous_agent.list_active_tasks()) if self.autonomous_agent else 0
                    },
                    'capabilities': [
                        'autonomous_task_execution',
                        'real_time_terminal_output',
                        'step_by_step_progress',
                        'websocket_communication',
                        'plan_generation',
                        'tool_execution',
                        'error_recovery'
                    ],
                    'models_available': ['llama3.1:8b'],
                    'tools_available': 12,
                    'memory_enabled': True,
                    'enhanced_features': True
                }
                
                return jsonify(status)
                
            except Exception as e:
                terminal_logger.error(f"❌ Error obteniendo estado: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Rutas de monitor (compatibilidad con UI)
        @self.app.route('/api/monitor/pages', methods=['GET'])
        def get_monitor_pages():
            """Obtiene páginas del monitor con paginación"""
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            
            pages_slice = self.monitor_pages[start_idx:end_idx]
            
            return jsonify({
                'pages': pages_slice,
                'total_pages': len(self.monitor_pages),
                'current_page': page,
                'per_page': per_page,
                'has_next': end_idx < len(self.monitor_pages),
                'has_prev': page > 1
            })
        
        @self.app.route('/api/monitor/latest', methods=['GET'])
        def get_latest_monitor():
            """Obtiene la última página del monitor"""
            if self.monitor_pages:
                return jsonify(self.monitor_pages[-1])
            return jsonify({'title': 'No hay páginas disponibles', 'content': ''})
    
    def _register_websocket_events(self):
        """Registra eventos WebSocket para comunicación en tiempo real"""
        
        @self.socketio.on('connect')
        def on_connect():
            terminal_logger.info("🔌 Cliente WebSocket conectado")
            emit('connection_status', {'status': 'connected', 'enhanced': True})
        
        @self.socketio.on('disconnect')
        def on_disconnect():
            terminal_logger.info("🔌 Cliente WebSocket desconectado")
        
        @self.socketio.on('join_task_room')
        def on_join_task_room(data):
            task_id = data.get('task_id')
            if task_id:
                join_room(f"task_{task_id}")
                terminal_logger.info(f"🔌 Cliente unido a sala de tarea: {task_id}")
        
        @self.socketio.on('leave_task_room')
        def on_leave_task_room(data):
            task_id = data.get('task_id')
            if task_id:
                leave_room(f"task_{task_id}")
                terminal_logger.info(f"🔌 Cliente salió de sala de tarea: {task_id}")
    
    def _should_execute_autonomously(self, message: str) -> bool:
        """Determina si un mensaje debe activar ejecución autónoma"""
        autonomous_triggers = [
            "crear", "generar", "desarrollar", "implementar", "construir",
            "buscar", "investigar", "analizar", "estudiar", "examinar",
            "planificar", "organizar", "diseñar", "estructurar",
            "automatizar", "optimizar", "mejorar", "resolver",
            "informe", "documento", "plan", "estrategia"
        ]
        
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in autonomous_triggers)
    
    def _start_autonomous_execution(self, task_id: str) -> bool:
        """Inicia la ejecución autónoma en segundo plano"""
        try:
            terminal_logger.info(f"🚀 Iniciando ejecución autónoma para tarea: {task_id}")
            
            self.autonomous_execution_active = True
            self.current_autonomous_task_id = task_id
            
            # Ejecutar en hilo separado para no bloquear
            def run_autonomous_execution():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    if self.autonomous_agent:
                        success = loop.run_until_complete(
                            self.autonomous_agent.execute_task_autonomously(task_id)
                        )
                        
                        # Crear página de reporte final
                        status = "completada exitosamente" if success else "falló"
                        self._add_monitor_page(
                            title="Ejecución Autónoma Finalizada",
                            content=f"""**Tarea ID:** {task_id}
**Estado:** {status}
**Timestamp:** {datetime.now().isoformat()}""",
                            page_type="report",
                            metadata={
                                "task_id": task_id,
                                "success": success
                            }
                        )
                        
                        # Emitir evento WebSocket
                        self.socketio.emit('autonomous_execution_completed', {
                            'task_id': task_id,
                            'success': success,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    self.autonomous_execution_active = False
                    self.current_autonomous_task_id = None
                    
                except Exception as e:
                    terminal_logger.error(f"❌ Error en ejecución autónoma: {e}")
                    self.autonomous_execution_active = False
                    self.current_autonomous_task_id = None
            
            # Iniciar en hilo separado
            execution_thread = threading.Thread(target=run_autonomous_execution)
            execution_thread.daemon = True
            execution_thread.start()
            
            return True
            
        except Exception as e:
            terminal_logger.error(f"❌ Error iniciando ejecución autónoma: {e}")
            self.autonomous_execution_active = False
            return False
    
    def _add_monitor_page(self, title: str, content: str, page_type: str, 
                         metadata: Optional[Dict] = None):
        """Añade una página al monitor con salida en terminal"""
        
        self.page_counter += 1
        timestamp = datetime.now().isoformat()
        
        # Crear página para la UI
        page = {
            'id': self.page_counter,
            'title': title,
            'content': content,
            'type': page_type,
            'timestamp': timestamp,
            'metadata': metadata or {},
            'page_number': self.page_counter
        }
        
        self.monitor_pages.append(page)
        
        # Emitir evento WebSocket para la UI
        self.socketio.emit('new_monitor_page', page)
        
        # SALIDA EN TERMINAL FORMATEADA
        terminal_output = f"""
{'='*80}
{'='*80}
📄 NUEVA PÁGINA DEL MONITOR (Tipo: {page_type.upper()})
Título: {title}
Timestamp: {timestamp}
Metadatos: {json.dumps(metadata or {}, indent=2)}
{'-'*80}
Contenido:
{content}
{'='*80}"""
        
        terminal_logger.info(terminal_output)
        
        # Limitar número de páginas en memoria
        if len(self.monitor_pages) > 100:
            self.monitor_pages.pop(0)
    
    def _serialize_task_plan(self, task) -> Dict[str, Any]:
        """Serializa un plan de tarea para respuesta API"""
        if not task:
            return {}
        
        return {
            'task_id': task.id,
            'title': task.title,
            'description': task.description,
            'steps': [
                {
                    'id': step.id,
                    'title': step.title,
                    'description': step.description,
                    'tool': step.tool,
                    'status': step.status.value
                }
                for step in task.steps
            ],
            'status': task.status.value,
            'progress_percentage': task.progress_percentage,
            'created_at': task.created_at.isoformat() if hasattr(task.created_at, 'isoformat') else str(task.created_at)
        }
    
    def _format_plan_for_response(self, task) -> str:
        """Formatea un plan para mostrar en la respuesta"""
        if not task or not task.steps:
            return "Plan no disponible"
        
        steps_text = []
        for i, step in enumerate(task.steps, 1):
            steps_text.append(f"{i}. {step.title}")
        
        return "\n".join(steps_text)
    
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