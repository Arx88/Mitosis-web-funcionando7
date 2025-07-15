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
    PLAN_UPDATED = "plan_updated"
    ERROR = "error"

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
        self.socketio = SocketIO(
            app, 
            cors_allowed_origins="*",
            async_mode='threading',
            logger=False,
            engineio_logger=False
        )
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
            """Client joins a task room for updates"""
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
            
            logger.info(f"Client {session_id} joined task {task_id}")
            emit('joined_task', {'task_id': task_id, 'status': 'joined'})
            
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
        """Send update to all clients listening to a task"""
        if not self.is_initialized or not self.socketio:
            logger.warning("WebSocket not initialized, cannot send update")
            return
            
        if task_id not in self.active_connections:
            logger.debug(f"No active connections for task {task_id}")
            return
            
        update_data = {
            'task_id': task_id,
            'type': update_type.value,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            # Send to all clients in the task room
            self.socketio.emit('task_update', update_data, room=task_id)
            logger.info(f"Sent {update_type.value} update for task {task_id}")
        except Exception as e:
            logger.error(f"Error sending WebSocket update: {e}")
            
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

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

def initialize_websocket(app: Flask):
    """Initialize WebSocket with Flask app"""
    websocket_manager.initialize(app)
    return websocket_manager

def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance"""
    return websocket_manager