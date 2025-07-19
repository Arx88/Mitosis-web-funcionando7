"""
Estrategias de Contexto Especializadas
Implementación según UPGRADE.md Sección 1.1.B
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatContextStrategy:
    """Estrategia para contexto de conversación casual"""
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        context = {
            'type': 'chat',
            'query': query,
            'conversation_history': [],
            'user_profile': {},
            'mood': 'neutral',
            'topics': []
        }
        
        try:
            # Obtener historial reciente de conversación
            if memory_manager and hasattr(memory_manager, 'get_recent_conversations'):
                recent = await memory_manager.get_recent_conversations(limit=5)
                context['conversation_history'] = recent
                
        except Exception as e:
            logger.error(f"Error building chat context: {e}")
            
        return context

class TaskPlanningContextStrategy:
    """Estrategia para contexto de planificación de tareas"""
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        context = {
            'type': 'task_planning',
            'query': query,
            'similar_plans': [],
            'available_resources': [],
            'constraints': [],
            'success_patterns': []
        }
        
        try:
            # Obtener planes similares exitosos
            if memory_manager and hasattr(memory_manager, 'get_successful_plans'):
                similar = await memory_manager.get_successful_plans(query_similarity=query, limit=3)
                context['similar_plans'] = similar
                
        except Exception as e:
            logger.error(f"Error building planning context: {e}")
            
        return context

class ReflectionContextStrategy:
    """Estrategia para contexto de reflexión y análisis"""
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        context = {
            'type': 'reflection',
            'query': query,
            'recent_actions': [],
            'outcomes': [],
            'lessons_learned': [],
            'improvement_areas': []
        }
        
        try:
            # Obtener acciones y resultados recientes
            if memory_manager and hasattr(memory_manager, 'get_recent_episodes'):
                episodes = await memory_manager.get_recent_episodes(limit=5)
                context['recent_actions'] = episodes
                
        except Exception as e:
            logger.error(f"Error building reflection context: {e}")
            
        return context

class ErrorHandlingContextStrategy:
    """Estrategia para contexto de manejo de errores"""
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        context = {
            'type': 'error_handling',
            'query': query,
            'error_patterns': [],
            'successful_recoveries': [],
            'available_fixes': [],
            'escalation_options': []
        }
        
        try:
            # Obtener patrones de error similares
            if memory_manager and hasattr(memory_manager, 'get_error_patterns'):
                patterns = await memory_manager.get_error_patterns(query)
                context['error_patterns'] = patterns
                
        except Exception as e:
            logger.error(f"Error building error handling context: {e}")
            
        return context