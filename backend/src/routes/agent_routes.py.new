"""
Rutas API del agente - Versión limpia
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
import asyncio
from pathlib import Path
from werkzeug.utils import secure_filename
from src.utils.json_encoder import MongoJSONEncoder, mongo_json_serializer
from src.tools.environment_setup_manager import EnvironmentSetupManager
from src.tools.task_planner import TaskPlanner
from src.tools.execution_engine import ExecutionEngine
from src.tools.tool_manager import ToolManager
from src.orchestration.task_orchestrator import TaskOrchestrator, OrchestrationContext

logger = logging.getLogger(__name__)

agent_bp = Blueprint('agent', __name__)

# Almacenamiento temporal para compartir conversaciones
shared_conversations = {}

# Almacenamiento temporal para archivos por tarea
task_files = {}

# Inicializar componentes
tool_manager = ToolManager()
task_planner = TaskPlanner(tool_manager)
execution_engine = ExecutionEngine(tool_manager)
environment_setup_manager = EnvironmentSetupManager(tool_manager)

# Nuevo sistema de orquestación avanzada
from src.services.ollama_service import OllamaService
ollama_service = OllamaService()

task_orchestrator = TaskOrchestrator(
    tool_manager=tool_manager,
    memory_manager=None,  # Se integrará en fase 2
    llm_service=ollama_service
)

@agent_bp.route('/orchestrate', methods=['POST'])
async def orchestrate_task():
    """
    Endpoint para orquestar tareas usando el nuevo sistema de orquestación avanzada
    """
    try:
        data = request.get_json()
        
        if not data or 'task_description' not in data:
            return jsonify({
                'error': 'task_description es requerido'
            }), 400
        
        task_description = data['task_description']
        user_id = data.get('user_id', 'default_user')
        session_id = data.get('session_id', str(uuid.uuid4()))
        priority = data.get('priority', 1)
        constraints = data.get('constraints', {})
        preferences = data.get('preferences', {})
        
        # Crear contexto de orquestación
        context = OrchestrationContext(
            task_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            task_description=task_description,
            priority=priority,
            constraints=constraints,
            preferences=preferences,
            metadata=data.get('metadata', {})
        )
        
        # Ejecutar orquestación
        result = await task_orchestrator.orchestrate_task(context)
        
        # Preparar respuesta
        response = {
            'task_id': result.task_id,
            'success': result.success,
            'total_execution_time': result.total_execution_time,
            'steps_completed': result.steps_completed,
            'steps_failed': result.steps_failed,
            'adaptations_made': result.adaptations_made,
            'resource_usage': result.resource_usage,
            'metadata': result.metadata
        }
        
        if result.error_message:
            response['error'] = result.error_message
        
        if result.execution_plan:
            response['execution_plan'] = {
                'id': result.execution_plan.id,
                'title': result.execution_plan.title,
                'strategy': result.execution_plan.strategy.value,
                'total_steps': len(result.execution_plan.steps),
                'estimated_duration': result.execution_plan.total_estimated_duration,
                'complexity_score': result.execution_plan.complexity_score,
                'success_probability': result.execution_plan.success_probability
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error en orquestación: {str(e)}")
        return jsonify({
            'error': f'Error en orquestación: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/status/<task_id>', methods=['GET'])
async def get_orchestration_status(task_id):
    """
    Obtiene el estado de una orquestación
    """
    try:
        status = task_orchestrator.get_orchestration_status(task_id)
        
        if status:
            return jsonify(status)
        else:
            return jsonify({
                'error': 'Orquestación no encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo estado: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/metrics', methods=['GET'])
async def get_orchestration_metrics():
    """
    Obtiene métricas de orquestación
    """
    try:
        metrics = task_orchestrator.get_orchestration_metrics()
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo métricas: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/active', methods=['GET'])
async def get_active_orchestrations():
    """
    Obtiene todas las orquestaciones activas
    """
    try:
        active_orchestrations = task_orchestrator.get_active_orchestrations()
        return jsonify(active_orchestrations)
        
    except Exception as e:
        logger.error(f"Error obteniendo orquestaciones activas: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo orquestaciones activas: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/cancel/<task_id>', methods=['POST'])
async def cancel_orchestration(task_id):
    """
    Cancela una orquestación activa
    """
    try:
        cancelled = await task_orchestrator.cancel_orchestration(task_id)
        
        if cancelled:
            return jsonify({
                'success': True,
                'message': f'Orquestación {task_id} cancelada exitosamente'
            })
        else:
            return jsonify({
                'error': 'Orquestación no encontrada o ya finalizada'
            }), 404
            
    except Exception as e:
        logger.error(f"Error cancelando orquestación: {str(e)}")
        return jsonify({
            'error': f'Error cancelando orquestación: {str(e)}'
        }), 500

@agent_bp.route('/orchestration/recommendations', methods=['GET'])
async def get_orchestration_recommendations():
    """
    Obtiene recomendaciones de optimización
    """
    try:
        recommendations = task_orchestrator.get_recommendations()
        return jsonify(recommendations)
        
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo recomendaciones: {str(e)}'
        }), 500