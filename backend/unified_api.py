#!/usr/bin/env python3
"""
Unified API for Mitosis Agent
Integrates the core functionality from Mitosis_Enhanced with a RESTful API
for frontend communication and real-time monitoring.
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Import Mitosis Enhanced modules
from agent_core import MitosisAgent, AgentConfig
from memory_manager import MemoryManager
from task_manager import TaskManager
from model_manager import ModelManager
from enhanced_prompts import PromptManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MonitorPage:
    """Data structure for monitor pages"""
    id: str
    title: str
    content: str
    type: str  # 'plan', 'tool-execution', 'report', 'file', 'error'
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class AgentStatus:
    """Data structure for agent status"""
    state: str
    uptime_seconds: float
    statistics: Dict[str, Any]
    available_models: List[str]
    current_model: Optional[str]
    memory_stats: Dict[str, Any]

class UnifiedMitosisAPI:
    """Unified API for Mitosis Agent with real-time monitoring"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.app = Flask(__name__)
        CORS(self.app, origins="*")  # Allow all origins for development
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize agent with default config if none provided
        if config is None:
            config = AgentConfig(
                ollama_url="http://localhost:11434",
                openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
                prefer_local_models=True,
                max_cost_per_1k_tokens=0.01,
                memory_db_path="unified_agent.db",
                max_short_term_messages=100,
                max_concurrent_tasks=2,
                debug_mode=True
            )
        
        self.agent = MitosisAgent(config)
        self.start_time = time.time()
        self.monitor_pages: List[MonitorPage] = []
        self.active_sessions: Dict[str, str] = {}  # session_id -> room_id mapping
        
        # Initialize with TODO.md page
        self._create_initial_todo_page()
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio_events()
        
        logger.info("Unified Mitosis API initialized successfully")
    
    def _create_initial_todo_page(self):
        """Create the initial TODO.md page"""
        todo_content = """# TODO - Plan de Acción del Agente

## Estado Actual
- ✅ Agente inicializado correctamente
- ✅ Conexión con modelos establecida
- ✅ Sistema de memoria activado
- ✅ Monitor de ejecución en línea

## Próximos Pasos
- 🔄 Esperando instrucciones del usuario
- 📝 Listo para procesar consultas
- 🛠️ Herramientas disponibles para ejecución
- 📊 Monitoreo en tiempo real activo

## Capacidades Disponibles
- Procesamiento de lenguaje natural
- Gestión de tareas complejas
- Memoria a corto y largo plazo
- Integración con múltiples modelos de IA
- Ejecución de herramientas especializadas
"""
        
        page = MonitorPage(
            id="todo_initial",
            title="TODO.md - Plan de Acción",
            content=todo_content,
            type="plan",
            timestamp=datetime.now(),
            metadata={
                "lineCount": len(todo_content.split('\n')),
                "fileSize": len(todo_content.encode('utf-8')),
                "status": "active"
            }
        )
        self.monitor_pages.append(page)
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - self.start_time
            })
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get agent status"""
            try:
                agent_status = self.agent.get_status()
                memory_stats = self.agent.memory_manager.get_memory_stats()
                
                status = AgentStatus(
                    state=agent_status.get('state', 'unknown'),
                    uptime_seconds=time.time() - self.start_time,
                    statistics=agent_status.get('statistics', {}),
                    available_models=agent_status.get('available_models', []),
                    current_model=agent_status.get('current_model'),
                    memory_stats=memory_stats
                )
                
                return jsonify(asdict(status))
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/message', methods=['POST'])
        def process_message():
            """Process user message"""
            try:
                data = request.get_json()
                if not data or 'message' not in data:
                    return jsonify({"error": "Message is required"}), 400
                
                user_message = data['message']
                session_id = data.get('session_id', str(uuid.uuid4()))
                
                # Start session if not exists
                if session_id not in self.active_sessions:
                    self.agent.start_session()
                    self.active_sessions[session_id] = session_id
                
                # Create monitor page for user message
                self._add_monitor_page(
                    title=f"Mensaje del Usuario",
                    content=f"**Usuario:** {user_message}",
                    page_type="user-message",
                    metadata={"session_id": session_id}
                )
                
                # Process message
                response = self.agent.process_user_message(user_message)
                
                # Create monitor page for agent response
                self._add_monitor_page(
                    title=f"Respuesta del Agente",
                    content=f"**Agente:** {response}",
                    page_type="agent-response",
                    metadata={"session_id": session_id}
                )
                
                return jsonify({
                    "response": response,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                self._add_monitor_page(
                    title="Error de Procesamiento",
                    content=f"**Error:** {str(e)}",
                    page_type="error",
                    metadata={"error_type": "message_processing"}
                )
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/tasks', methods=['GET'])
        def get_tasks():
            """Get all tasks"""
            try:
                tasks = self.agent.task_manager.get_all_tasks()
                return jsonify({"tasks": tasks})
            except Exception as e:
                logger.error(f"Error getting tasks: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/tasks/create', methods=['POST'])
        def create_task():
            """Create a new task"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "Task data is required"}), 400
                
                title = data.get('title', 'Untitled Task')
                description = data.get('description', '')
                goal = data.get('goal', '')
                tools = data.get('tools', [])
                
                task_id = self.agent.create_and_execute_task(title, description, goal)
                
                # Create monitor page for task creation
                self._add_monitor_page(
                    title=f"Tarea Creada: {title}",
                    content=f"**ID:** {task_id}\n**Descripción:** {description}\n**Objetivo:** {goal}",
                    page_type="task-creation",
                    metadata={"task_id": task_id}
                )
                
                return jsonify({
                    "task_id": task_id,
                    "status": "created",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error creating task: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/monitor/pages', methods=['GET'])
        def get_monitor_pages():
            """Get monitor pages with pagination"""
            try:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 10))
                
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                
                pages_data = []
                for monitor_page in self.monitor_pages[start_idx:end_idx]:
                    pages_data.append({
                        "id": monitor_page.id,
                        "title": monitor_page.title,
                        "content": monitor_page.content,
                        "type": monitor_page.type,
                        "timestamp": monitor_page.timestamp.isoformat(),
                        "metadata": monitor_page.metadata
                    })
                
                return jsonify({
                    "pages": pages_data,
                    "total_pages": len(self.monitor_pages),
                    "current_page": page,
                    "per_page": per_page,
                    "has_next": end_idx < len(self.monitor_pages),
                    "has_prev": page > 1
                })
                
            except Exception as e:
                logger.error(f"Error getting monitor pages: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/monitor/latest', methods=['GET'])
        def get_latest_page():
            """Get the latest monitor page"""
            try:
                if not self.monitor_pages:
                    return jsonify({"error": "No pages available"}), 404
                
                latest_page = self.monitor_pages[-1]
                return jsonify({
                    "id": latest_page.id,
                    "title": latest_page.title,
                    "content": latest_page.content,
                    "type": latest_page.type,
                    "timestamp": latest_page.timestamp.isoformat(),
                    "metadata": latest_page.metadata,
                    "page_number": len(self.monitor_pages)
                })
                
            except Exception as e:
                logger.error(f"Error getting latest page: {e}")
                return jsonify({"error": str(e)}), 500
    
    def _setup_socketio_events(self):
        """Setup SocketIO events for real-time communication"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            room_id = str(uuid.uuid4())
            join_room(room_id)
            emit('connected', {'room_id': room_id})
            logger.info(f"Client connected to room: {room_id}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info("Client disconnected")
        
        @self.socketio.on('join_monitoring')
        def handle_join_monitoring(data):
            """Handle client joining monitoring room"""
            room_id = data.get('room_id')
            if room_id:
                join_room(f"monitor_{room_id}")
                emit('monitoring_joined', {'status': 'success'})
    
    def _add_monitor_page(self, title: str, content: str, page_type: str, metadata: Optional[Dict] = None):
        """Add a new monitor page and notify clients"""
        if metadata is None:
            metadata = {}
        
        page = MonitorPage(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            type=page_type,
            timestamp=datetime.now(),
            metadata={
                **metadata,
                "lineCount": len(content.split('\n')),
                "fileSize": len(content.encode('utf-8'))
            }
        )
        
        self.monitor_pages.append(page)
        
        # Notify all monitoring clients
        self.socketio.emit('new_monitor_page', {
            "id": page.id,
            "title": page.title,
            "content": page.content,
            "type": page.type,
            "timestamp": page.timestamp.isoformat(),
            "metadata": page.metadata,
            "page_number": len(self.monitor_pages)
        }, room='monitoring')
        
        logger.info(f"Added monitor page: {title}")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the unified API server"""
        logger.info(f"Starting Unified Mitosis API on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    
    def shutdown(self):
        """Shutdown the agent and cleanup resources"""
        logger.info("Shutting down Unified Mitosis API")
        self.agent.shutdown()

def create_unified_api(config: Optional[AgentConfig] = None) -> UnifiedMitosisAPI:
    """Factory function to create unified API instance"""
    return UnifiedMitosisAPI(config)

if __name__ == "__main__":
    # Create and run the unified API
    api = create_unified_api()
    
    try:
        api.run(debug=True)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        api.shutdown()

