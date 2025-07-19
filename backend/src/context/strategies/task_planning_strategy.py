"""
Estrategia de Contexto para Planificación de Tareas
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskPlanningContextStrategy:
    """Estrategia para contexto de planificación de tareas"""
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        context = {
            'type': 'task_planning',
            'query': query,
            'similar_plans': [],
            'available_resources': [],
            'constraints': [],
            'success_patterns': [],
            'planning_templates': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Obtener planes similares exitosos
            if memory_manager:
                context['similar_plans'] = await self._get_similar_plans(memory_manager, query)
                context['success_patterns'] = await self._get_success_patterns(memory_manager, query)
            
            # Identificar recursos disponibles
            context['available_resources'] = await self._identify_available_resources(task_manager)
            
            # Identificar restricciones
            context['constraints'] = self._identify_constraints(query)
            
            # Obtener templates de planificación
            context['planning_templates'] = self._get_planning_templates(query)
                
        except Exception as e:
            logger.error(f"Error building planning context: {e}")
            
        return context
    
    async def _get_similar_plans(self, memory_manager, query: str) -> List[Dict[str, Any]]:
        """Obtiene planes similares exitosos"""
        plans = []
        try:
            if hasattr(memory_manager, 'get_successful_plans'):
                similar = await memory_manager.get_successful_plans(query_similarity=query, limit=3)
                plans = similar
            elif hasattr(memory_manager, 'get_recent_episodes'):
                episodes = await memory_manager.get_recent_episodes(limit=5, include_successful=True)
                for episode in episodes[:3]:
                    if hasattr(episode, 'title') and 'plan' in episode.title.lower():
                        plans.append({
                            'title': episode.title,
                            'approach': getattr(episode, 'description', ''),
                            'success': getattr(episode, 'success', True)
                        })
        except Exception as e:
            logger.error(f"Error getting similar plans: {e}")
        return plans
    
    async def _get_success_patterns(self, memory_manager, query: str) -> List[Dict[str, Any]]:
        """Obtiene patrones de éxito en planificación"""
        patterns = []
        try:
            # Patrones básicos conocidos
            patterns = [
                {
                    'pattern': 'divide_and_conquer',
                    'description': 'Dividir tarea compleja en subtareas más simples',
                    'success_rate': 0.85
                },
                {
                    'pattern': 'iterative_refinement',
                    'description': 'Refinamiento iterativo del plan',
                    'success_rate': 0.78
                },
                {
                    'pattern': 'resource_first',
                    'description': 'Identificar recursos antes de planificar',
                    'success_rate': 0.82
                }
            ]
        except Exception as e:
            logger.error(f"Error getting success patterns: {e}")
        return patterns
    
    async def _identify_available_resources(self, task_manager) -> List[Dict[str, Any]]:
        """Identifica recursos disponibles"""
        resources = [
            {'type': 'computational', 'name': 'web_search', 'availability': 'high'},
            {'type': 'computational', 'name': 'analysis', 'availability': 'high'},
            {'type': 'computational', 'name': 'content_generation', 'availability': 'high'},
            {'type': 'knowledge', 'name': 'memory_system', 'availability': 'high'}
        ]
        
        try:
            if task_manager and hasattr(task_manager, 'get_available_resources'):
                additional = await task_manager.get_available_resources()
                resources.extend(additional)
        except Exception as e:
            logger.error(f"Error identifying resources: {e}")
            
        return resources
    
    def _identify_constraints(self, query: str) -> List[Dict[str, Any]]:
        """Identifica restricciones basadas en la consulta"""
        constraints = []
        
        # Análisis básico de restricciones en el texto
        if 'urgente' in query.lower() or 'rápido' in query.lower():
            constraints.append({'type': 'time', 'description': 'Restricción de tiempo - urgente'})
        
        if 'simple' in query.lower() or 'básico' in query.lower():
            constraints.append({'type': 'complexity', 'description': 'Mantener simplicidad'})
        
        if 'detallado' in query.lower() or 'completo' in query.lower():
            constraints.append({'type': 'completeness', 'description': 'Requiere análisis detallado'})
        
        return constraints
    
    def _get_planning_templates(self, query: str) -> List[Dict[str, Any]]:
        """Obtiene templates de planificación aplicables"""
        templates = [
            {
                'name': 'research_task',
                'steps': ['información', 'análisis', 'síntesis', 'entrega'],
                'applicable': any(word in query.lower() for word in ['investigar', 'buscar', 'información'])
            },
            {
                'name': 'creation_task', 
                'steps': ['planificación', 'desarrollo', 'revisión', 'finalización'],
                'applicable': any(word in query.lower() for word in ['crear', 'generar', 'desarrollar'])
            },
            {
                'name': 'analysis_task',
                'steps': ['recopilación', 'análisis', 'conclusiones', 'recomendaciones'],
                'applicable': any(word in query.lower() for word in ['analizar', 'evaluar', 'estudiar'])
            }
        ]
        
        # Filtrar templates aplicables
        applicable_templates = [t for t in templates if t['applicable']]
        return applicable_templates if applicable_templates else templates[:1]