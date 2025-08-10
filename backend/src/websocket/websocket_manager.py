"""
WebSocket Manager for Real-time Task Updates
Provides real-time communication between backend execution and frontend UI
"""

import asyncio
import json
import logging
import threading
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UpdateType(Enum):
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_UPDATE = "step_update"  # Enhanced step updates
    TOOL_EXECUTION_DETAIL = "tool_execution_detail"  # Detailed tool execution info
    PLAN_UPDATED = "plan_updated"
    ERROR = "error"
    # ✅ NUEVOS TIPOS PARA VISUALIZACIÓN EN TIEMPO REAL
    BROWSER_ACTIVITY = "browser_activity"  # Para eventos de navegación web
    DATA_COLLECTION_UPDATE = "data_collection_update"  # Para datos recolectados incrementalmente
    REPORT_PROGRESS = "report_progress"  # Para actualizaciones incrementales del informe
    LOG_MESSAGE = "log_message"  # Para mensajes de log genéricos

class WebSocketManager:
    """Manages WebSocket connections and real-time updates"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.socketio = None
        self.active_connections: Dict[str, List[str]] = {}  # task_id -> [session_ids]
        self.session_tasks: Dict[str, str] = {}  # session_id -> task_id
        self.update_queue = asyncio.Queue()
        self.is_initialized = False
        
    def initialize(self, app: Flask):
        """Initialize WebSocket with Flask app"""
        self.app = app
        
        # 🚀 CRITICAL FIX: Use existing SocketIO instance from app instead of creating new one
        if hasattr(app, 'socketio') and app.socketio:
            logger.info("📡 Using existing SocketIO instance from app")
            self.socketio = app.socketio
        else:
            logger.info("🔧 Creating new SocketIO instance")
            self.socketio = SocketIO(
                app, 
                cors_allowed_origins="*",
                async_mode='eventlet',
                logger=False,
                engineio_logger=False,
                ping_timeout=60,  # 60 segundos para ping timeout
                ping_interval=25,  # 25 segundos entre pings
                max_http_buffer_size=1000000  # 1MB buffer
            )
            app.socketio = self.socketio
        
        self.setup_event_handlers()
        self.is_initialized = True
        logger.info("WebSocket Manager initialized")
        
    def setup_event_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"WebSocket client connected: {request.sid}")
            emit('connection_established', {'status': 'connected'})
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"WebSocket client disconnected: {request.sid}")
            self.handle_client_disconnect(request.sid)
            
        @self.socketio.on('join_task')
        def handle_join_task(data):
            """Client joins a task room for updates - ENHANCED VERSION WITH MESSAGE DELIVERY"""
            task_id = data.get('task_id')
            session_id = request.sid
            
            if not task_id:
                emit('error', {'message': 'task_id is required'})
                return
                
            # Join room for this task
            join_room(task_id)
            
            # Track connection
            if task_id not in self.active_connections:
                self.active_connections[task_id] = []
            self.active_connections[task_id].append(session_id)
            self.session_tasks[session_id] = task_id
            
            logger.info(f"🔌 Client {session_id} joined task {task_id}")
            logger.info(f"📊 Total active connections for task {task_id}: {len(self.active_connections[task_id])}")
            
            # 🚀 CRITICAL FIX: Send stored messages to the newly connected client
            try:
                self.send_stored_messages_to_client(session_id, task_id)
                logger.info(f"📦 Sent stored messages to newly connected client {session_id}")
            except Exception as e:
                logger.error(f"❌ Error sending stored messages to client {session_id}: {e}")
            
            emit('joined_task', {
                'task_id': task_id, 
                'status': 'joined',
                'stored_messages_sent': True,
                'active_connections': len(self.active_connections[task_id])
            })
            
        @self.socketio.on('leave_task')
        def handle_leave_task(data):
            """Client leaves a task room"""
            task_id = data.get('task_id')
            session_id = request.sid
            
            if task_id:
                leave_room(task_id)
                self.remove_client_from_task(session_id, task_id)
                logger.info(f"Client {session_id} left task {task_id}")
                emit('left_task', {'task_id': task_id, 'status': 'left'})
                
        @self.socketio.on('request_status')
        def handle_status_request(data):
            """Client requests current status of a task"""
            task_id = data.get('task_id')
            # Here you would query the execution engine for current status
            # For now, just acknowledge
            emit('status_response', {'task_id': task_id, 'status': 'requested'})
            
    def handle_client_disconnect(self, session_id: str):
        """Handle client disconnection cleanup"""
        if session_id in self.session_tasks:
            task_id = self.session_tasks[session_id]
            self.remove_client_from_task(session_id, task_id)
            del self.session_tasks[session_id]
            
    def remove_client_from_task(self, session_id: str, task_id: str):
        """Remove client from task tracking"""
        if task_id in self.active_connections:
            if session_id in self.active_connections[task_id]:
                self.active_connections[task_id].remove(session_id)
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]
                    
    def send_update(self, task_id: str, update_type: UpdateType, data: Dict[str, Any]):
        """Send update to all clients listening to a task - ENHANCED VERSION WITH MESSAGE PERSISTENCE"""
        if not self.is_initialized or not self.socketio:
            logger.warning("WebSocket not initialized, cannot send update")
            return
        
        # 🔧 CRITICAL FIX: Store messages even if no active connections
        # This ensures messages are available when clients connect later
        if not hasattr(self, 'stored_messages'):
            self.stored_messages = {}
        if task_id not in self.stored_messages:
            self.stored_messages[task_id] = []
        
        update_data = {
            'task_id': task_id,
            'type': update_type.value,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Store message for late-joining clients (keep last 50 messages per task)
        self.stored_messages[task_id].append(update_data)
        if len(self.stored_messages[task_id]) > 50:
            self.stored_messages[task_id] = self.stored_messages[task_id][-50:]
        
        # 🚀 ENHANCED LOGGING for debugging
        logger.info(f"📡 Storing and attempting to send {update_type.value} update for task {task_id}")
        logger.info(f"🔌 Active connections for task {task_id}: {len(self.active_connections.get(task_id, []))}")
        logger.info(f"📦 Message data preview: {str(data)[:100]}...")
        
        try:
            # Send to all clients in the task room (even if no active connections tracked)
            self.socketio.emit('task_update', update_data, room=task_id)
            
            # 🔧 ADDITIONAL EMIT STRATEGIES for maximum compatibility
            # Strategy 1: Emit to individual sessions if room fails
            if task_id in self.active_connections:
                for session_id in self.active_connections[task_id]:
                    self.socketio.emit('task_update', update_data, room=session_id)
                    logger.info(f"📡 Sent to individual session: {session_id}")
            
            # Strategy 2: ELIMINADA - Causa principal de contaminación entre tareas
            # UPGRADE AI: Las emisiones globales han sido eliminadas para prevenir
            # la contaminación de contenido entre tareas y el problema de "PENSANDO" 
            # en todas las tareas simultáneamente
            # Referencia: UpgradeAI.md Sección 4.2, Mejora 1
            
            # Todas las actualizaciones ahora se envían ÚNICAMENTE a la room específica de la tarea
            
            # Strategy 3: Store in session storage for retrieval
            if not hasattr(self, 'session_messages'):
                self.session_messages = {}
            for session_id in self.active_connections.get(task_id, []):
                if session_id not in self.session_messages:
                    self.session_messages[session_id] = []
                self.session_messages[session_id].append(update_data)
                # Keep last 20 messages per session
                if len(self.session_messages[session_id]) > 20:
                    self.session_messages[session_id] = self.session_messages[session_id][-20:]
            
            logger.info(f"✅ Successfully processed {update_type.value} update for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending WebSocket update for task {task_id}: {e}")
            # Even if sending fails, we still have the message stored
    
    def get_stored_messages(self, task_id: str) -> List[Dict[str, Any]]:
        """Get stored messages for a task (for late-joining clients)"""
        if not hasattr(self, 'stored_messages'):
            self.stored_messages = {}
        return self.stored_messages.get(task_id, [])
    
    def send_stored_messages_to_client(self, session_id: str, task_id: str):
        """Send all stored messages for a task to a specific client"""
        if not self.is_initialized or not self.socketio:
            return
        
        stored_messages = self.get_stored_messages(task_id)
        if stored_messages:
            logger.info(f"📦 Sending {len(stored_messages)} stored messages to client {session_id} for task {task_id}")
            for message in stored_messages:
                try:
                    self.socketio.emit('task_update', message, room=session_id)
                except Exception as e:
                    logger.error(f"❌ Error sending stored message to {session_id}: {e}")
            
    def send_task_started(self, task_id: str, task_title: str, execution_plan: Dict[str, Any]):
        """Send task started notification"""
        self.send_update(task_id, UpdateType.TASK_STARTED, {
            'task_title': task_title,
            'execution_plan': execution_plan,
            'message': 'Task execution started'
        })
        
    def send_task_progress(self, task_id: str, progress: float, current_step: int, total_steps: int, step_title: str = ""):
        """Send task progress update"""
        self.send_update(task_id, UpdateType.TASK_PROGRESS, {
            'progress': progress,
            'current_step': current_step,
            'total_steps': total_steps,
            'step_title': step_title,
            'message': f'Step {current_step}/{total_steps}: {step_title}'
        })
        
    def send_task_completed(self, task_id: str, success_rate: float, total_execution_time: float, summary: Dict[str, Any]):
        """Send task completion notification"""
        self.send_update(task_id, UpdateType.TASK_COMPLETED, {
            'success_rate': success_rate,
            'total_execution_time': total_execution_time,
            'summary': summary,
            'message': 'Task completed successfully'
        })
        
    def send_task_failed(self, task_id: str, error: str, context: Dict[str, Any] = None):
        """Send task failure notification"""
        self.send_update(task_id, UpdateType.TASK_FAILED, {
            'error': error,
            'context': context or {},
            'message': f'Task failed: {error}'
        })
        
    def send_step_started(self, task_id: str, step_id: str, step_title: str, step_description: str):
        """Send step started notification"""
        self.send_update(task_id, UpdateType.STEP_STARTED, {
            'step_id': step_id,
            'step_title': step_title,
            'step_description': step_description,
            'message': f'Started: {step_title}'
        })
        
    def send_step_completed(self, task_id: str, step_id: str, step_title: str, execution_time: float, result: Dict[str, Any]):
        """Send step completion notification"""
        self.send_update(task_id, UpdateType.STEP_COMPLETED, {
            'step_id': step_id,
            'step_title': step_title,
            'execution_time': execution_time,
            'result': result,
            'message': f'Completed: {step_title}'
        })
        
    def send_step_failed(self, task_id: str, step_id: str, step_title: str, error: str):
        """Send step failure notification"""
        self.send_update(task_id, UpdateType.STEP_FAILED, {
            'step_id': step_id,
            'step_title': step_title,
            'error': error,
            'message': f'Failed: {step_title} - {error}'
        })
        
    def send_plan_updated(self, task_id: str, updated_plan: Dict[str, Any], changes: List[Dict[str, Any]]):
        """Send plan update notification"""
        self.send_update(task_id, UpdateType.PLAN_UPDATED, {
            'updated_plan': updated_plan,
            'changes': changes,
            'message': 'Execution plan updated'
        })
        
    def send_error(self, task_id: str, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Send error notification"""
        self.send_update(task_id, UpdateType.ERROR, {
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
            'message': f'Error: {error_message}'
        })

    def emit_update(self, task_id: str, update_type: UpdateType, data: Dict[str, Any]):
        """Emit update to all clients in task room"""
        if not self.is_initialized or not self.socketio:
            logger.warning("WebSocket not initialized, cannot emit update")
            return
            
        try:
            self.socketio.emit(
                update_type.value,
                data,
                room=task_id
            )
            logger.info(f"Emitted {update_type.value} to task {task_id}")
        except Exception as e:
            logger.error(f"Error emitting update: {e}")

    def emit_activity(self, task_id: str, activity: str, tool: str = None):
        """Emit real-time activity to terminal"""
        self.emit_update(
            task_id=task_id,
            update_type=UpdateType.TASK_PROGRESS,
            data={
                'activity': activity,
                'tool': tool,
                'timestamp': datetime.now().isoformat()
            }
        )

    def emit_to_task(self, task_id: str, event: str, data: Dict[str, Any]):
        """Emit event to all clients connected to a specific task - ENHANCED VERSION"""
        if not self.is_initialized or not self.socketio:
            logger.warning("WebSocket not initialized, cannot emit event")
            return
            
        try:
            logger.info(f"🚀 Attempting to emit {event} to task {task_id}")
            logger.info(f"🔌 Active connections for task {task_id}: {len(self.active_connections.get(task_id, []))}")
            
            # Enhanced data with more information
            enhanced_data = {
                **data,
                'task_id': task_id,
                'event': event,
                'server_timestamp': datetime.now().isoformat()
            }
            
            # CRITICAL FIX: Store the event for later retrieval even if no connections
            if not hasattr(self, 'stored_events'):
                self.stored_events = {}
            if task_id not in self.stored_events:
                self.stored_events[task_id] = []
            
            # Store last 10 events per task for late-joining clients
            self.stored_events[task_id].append(enhanced_data)
            if len(self.stored_events[task_id]) > 10:
                self.stored_events[task_id] = self.stored_events[task_id][-10:]
            
            # Emit to task room regardless of active connections
            self.socketio.emit(event, enhanced_data, room=task_id)
            logger.info(f"✅ Emitted {event} to task room {task_id}")
            
            # Also emit to individual sessions if room doesn't work
            if task_id in self.active_connections:
                for session_id in self.active_connections[task_id]:
                    self.socketio.emit(event, enhanced_data, room=session_id)
                    logger.info(f"✅ Emitted {event} to session {session_id}")
            else:
                logger.warning(f"⚠️ No active connections found for task {task_id} - Event stored for later retrieval")
            
            # Also emit generic events that frontend might be listening for
            generic_events = ['task_update', 'progress_update', 'agent_activity']
            for generic_event in generic_events:
                self.socketio.emit(generic_event, enhanced_data, room=task_id)
                if task_id in self.active_connections:
                    for session_id in self.active_connections[task_id]:
                        self.socketio.emit(generic_event, enhanced_data, room=session_id)
                        
        except Exception as e:
            logger.error(f"❌ Error emitting to task {task_id}: {e}")
            import traceback
            traceback.print_exc()
    
    def get_stored_events(self, task_id: str) -> List[Dict[str, Any]]:
        """Get stored events for a task (for late-joining clients)"""
        if not hasattr(self, 'stored_events'):
            self.stored_events = {}
        return self.stored_events.get(task_id, [])
    
    def send_orchestration_progress(self, task_id: str, step_id: str, progress: float, 
                                   current_step: str, total_steps: int):
        """Send orchestration progress notification"""
        self.send_update(task_id, UpdateType.TASK_PROGRESS, {
            'step_id': step_id,
            'progress': progress,
            'current_step': current_step,
            'total_steps': total_steps,
            'execution_type': 'orchestration',
            'message': f'Step {step_id}: {current_step} ({progress:.1f}%)'
        })
        
    def get_active_connections(self) -> Dict[str, List[str]]:
        """Get active connections for debugging"""
        return self.active_connections.copy()
        
    def get_connection_count(self, task_id: str) -> int:
        """Get number of active connections for a task"""
        return len(self.active_connections.get(task_id, []))
        
    def create_execution_callbacks(self, task_id: str) -> Dict[str, Callable]:
        """Create callback functions for ExecutionEngine integration"""
        
        def progress_callback(notification: Dict[str, Any]):
            """Callback for progress updates"""
            event = notification.get('event', '')
            data = notification.get('data', {})
            
            if event == 'execution_started':
                self.send_task_started(
                    task_id=task_id,
                    task_title=data.get('task_title', 'Unknown Task'),
                    execution_plan=data.get('plan', {})
                )
            elif event == 'step_completed':
                progress = data.get('progress', 0)
                step_index = data.get('step_index', 0)
                step_id = data.get('step_id', '')
                
                self.send_task_progress(
                    task_id=task_id,
                    progress=progress,
                    current_step=step_index + 1,
                    total_steps=data.get('total_steps', 1),
                    step_title=step_id
                )
                
        def completion_callback(notification: Dict[str, Any]):
            """Callback for task completion"""
            success_rate = notification.get('success_rate', 0)
            total_execution_time = notification.get('total_execution_time', 0)
            summary = notification.get('execution_summary', {})
            
            self.send_task_completed(
                task_id=task_id,
                success_rate=success_rate,
                total_execution_time=total_execution_time,
                summary=summary
            )
            
        def error_callback(notification: Dict[str, Any]):
            """Callback for errors"""
            error = notification.get('error', 'Unknown error')
            context = notification.get('context', {})
            
            self.send_task_failed(
                task_id=task_id,
                error=error,
                context=context
            )
            
        return {
            'progress_callback': progress_callback,
            'completion_callback': completion_callback,
            'error_callback': error_callback
        }
    
    # ENHANCED WEBSOCKET METHODS - As per NEWUPGRADE.md Section 3
    def send_enhanced_step_update(self, task_id: str, step_data: Dict[str, Any]):
        """Send enhanced step update with complete information"""
        enhanced_data = {
            'type': 'step_update',
            'step_id': step_data.get('step_id'),
            'status': step_data.get('status', 'unknown'),  # 'in-progress', 'completed_success', 'failed'
            'title': step_data.get('title', ''),
            'description': step_data.get('description', ''),
            'result_summary': step_data.get('result_summary', ''),
            'execution_time': step_data.get('execution_time', 0),
            'progress': step_data.get('progress', 0),  # Overall task progress percentage
            'current_step': step_data.get('current_step', 0),
            'total_steps': step_data.get('total_steps', 0),
            'validation_status': step_data.get('validation_status', ''),
            'error': step_data.get('error', None),
            'timestamp': datetime.now().isoformat()
        }
        
        self.emit_update(task_id, UpdateType.STEP_UPDATE, enhanced_data)
        
    def send_tool_execution_detail(self, task_id: str, tool_data: Dict[str, Any]):
        """Send detailed tool execution information"""
        tool_detail = {
            'type': 'tool_execution_detail',
            'tool_name': tool_data.get('tool_name', ''),
            'input_params': tool_data.get('input_params', {}),
            'message': tool_data.get('message', ''),
            'level': tool_data.get('level', 'info'),  # 'info', 'warning', 'error'
            'file_created': tool_data.get('file_created', None),
            'download_url': tool_data.get('download_url', None),
            'execution_status': tool_data.get('execution_status', 'running'),
            'timestamp': datetime.now().isoformat()
        }
        
        self.emit_update(task_id, UpdateType.TOOL_EXECUTION_DETAIL, tool_detail)
        
    def send_enhanced_task_completed(self, task_id: str, completion_data: Dict[str, Any]):
        """Send enhanced task completion with comprehensive information"""
        completion_info = {
            'type': 'task_completed',
            'task_id': task_id,
            'status': completion_data.get('status', 'success'),  # 'success' or 'completed_with_warnings'
            'final_result': completion_data.get('final_result', ''),  # The final message for user
            'final_task_status': completion_data.get('final_task_status', ''),
            'total_steps': completion_data.get('total_steps', 0),
            'completed_steps': completion_data.get('completed_steps', 0),
            'failed_steps': completion_data.get('failed_steps', 0),
            'execution_time': completion_data.get('execution_time', 0),
            'files_generated': completion_data.get('files_generated', []),
            'warnings': completion_data.get('warnings', []),
            'message': completion_data.get('message', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        self.emit_update(task_id, UpdateType.TASK_COMPLETED, completion_info)

    # ✅ NUEVOS MÉTODOS PARA VISUALIZACIÓN EN TIEMPO REAL - SEGÚN UpgardeRef.md SECCIÓN 5.1
    def send_log_message(self, task_id: str, level: str, message: str):
        """Send generic log message to terminal for comprehensive logging"""
        # ✅ VALIDACIONES PARA EVITAR ERRORES DE UNDEFINED EN FRONTEND
        if not level or not isinstance(level, str):
            level = "info"
        
        if not message or not isinstance(message, str):
            message = "Empty message"
        
        # Asegurar que level sea válido para el frontend
        valid_levels = ["info", "warn", "error", "debug", "success"]
        if level.lower() not in valid_levels:
            level = "info"
        
        self.send_update(task_id, UpdateType.LOG_MESSAGE, {
            'level': level.lower(),  # Normalizar a minúsculas
            'message': str(message),  # Asegurar que sea string
            'timestamp': datetime.now().isoformat(),
            'type': 'log_message'  # ✅ Añadir campo type explícito para el frontend
        })

    def send_browser_activity(self, task_id: str, activity_type: str, url: str, title: str = "", screenshot_url: str = ""):
        """Send browser activity notification for real-time web navigation tracking"""
        # ✅ VALIDACIONES PARA EVITAR ERRORES DE UNDEFINED EN FRONTEND
        if not activity_type or not isinstance(activity_type, str):
            activity_type = "unknown"
            
        if not url or not isinstance(url, str):
            url = "about:blank"
            
        title = str(title) if title else ""
        screenshot_url = str(screenshot_url) if screenshot_url else ""
        
        self.send_update(task_id, UpdateType.BROWSER_ACTIVITY, {
            'activity_type': activity_type,  # 'url_changed', 'page_loaded', 'click', 'input', etc.
            'url': url,
            'title': title,
            'screenshot_url': screenshot_url,
            'message': f'Navegando a: {url}' if activity_type == 'page_loaded' else f'Actividad en navegador: {activity_type}',
            'timestamp': datetime.now().isoformat(),
            'type': 'browser_activity'  # ✅ Añadir campo type explícito para el frontend
        })

    def send_data_collection_update(self, task_id: str, step_id: str, data_summary: str, partial_data: Any = None):
        """Send incremental data collection update for granular progress tracking"""
        # ✅ VALIDACIONES PARA EVITAR ERRORES DE UNDEFINED EN FRONTEND
        if not step_id or not isinstance(step_id, str):
            step_id = "unknown_step"
            
        if not data_summary or not isinstance(data_summary, str):
            data_summary = "Data collected"
        
        self.send_update(task_id, UpdateType.DATA_COLLECTION_UPDATE, {
            'step_id': str(step_id),
            'data_summary': str(data_summary),
            'partial_data': partial_data,
            'message': f'Datos recolectados: {data_summary}',
            'timestamp': datetime.now().isoformat(),
            'type': 'data_collection_update'  # ✅ Añadir campo type explícito para el frontend
        })

    def send_report_progress(self, task_id: str, section_title: str, content_delta: str, full_report_so_far: str = ""):
        """Send incremental report progress update for real-time report building"""
        # ✅ VALIDACIONES PARA EVITAR ERRORES DE UNDEFINED EN FRONTEND
        if not section_title or not isinstance(section_title, str):
            section_title = "Report Section"
            
        if not content_delta or not isinstance(content_delta, str):
            content_delta = "Content generated"
            
        full_report_so_far = str(full_report_so_far) if full_report_so_far else ""
        
        self.send_update(task_id, UpdateType.REPORT_PROGRESS, {
            'section_title': str(section_title),
            'content_delta': str(content_delta),
            'full_report_so_far': full_report_so_far,
            'message': f'Generando informe: {section_title}',
            'timestamp': datetime.now().isoformat(),
            'type': 'report_progress'  # ✅ Añadir campo type explícito para el frontend
        })

    def send_browser_visual_event(self, task_id: str, event_data: Dict[str, Any]):
        """Send browser visual event for real-time web navigation visualization - CRITICAL FIX"""
        try:
            # Asegurar campos requeridos con valores por defecto
            event_type = event_data.get('type', 'navigation_update')
            message = event_data.get('message', 'Browser activity')
            url = event_data.get('url', '')
            screenshot_url = event_data.get('screenshot_url', '')
            
            # Crear evento browser_visual estructurado
            browser_visual_data = {
                'type': event_type,
                'message': message,
                'url': url,
                'screenshot_url': screenshot_url,
                'timestamp': event_data.get('timestamp', datetime.now().isoformat()),
                'task_id': task_id,
                **event_data  # Incluir cualquier dato adicional
            }
            
            # Enviar como evento browser_visual específico
            self.emit_to_task(task_id, 'browser_visual', browser_visual_data)
            
            # También enviar como browser_activity para compatibilidad
            activity_type = event_type.replace('_', ' ').title()
            self.send_browser_activity(
                task_id=task_id,
                activity_type=activity_type,
                url=url,
                title=event_data.get('title', ''),
                screenshot_url=screenshot_url
            )
            
            logger.info(f"✅ Browser visual event sent: {event_type} for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending browser visual event for task {task_id}: {e}")
            import traceback
            traceback.print_exc()

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

def initialize_websocket(app: Flask):
    """Initialize WebSocket with Flask app"""
    websocket_manager.initialize(app)
    return websocket_manager

def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance"""
    return websocket_manager