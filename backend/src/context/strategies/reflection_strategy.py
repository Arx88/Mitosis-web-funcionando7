"""
Estrategia de Contexto para Reflexión y Análisis
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ReflectionContextStrategy:
    """Estrategia para contexto de reflexión y análisis"""
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        context = {
            'type': 'reflection',
            'query': query,
            'recent_actions': [],
            'outcomes': [],
            'lessons_learned': [],
            'improvement_areas': [],
            'performance_metrics': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Obtener acciones y resultados recientes
            if memory_manager:
                context['recent_actions'] = await self._get_recent_actions(memory_manager)
                context['outcomes'] = await self._get_recent_outcomes(memory_manager)
                context['lessons_learned'] = await self._extract_lessons_learned(memory_manager)
                context['performance_metrics'] = await self._get_performance_metrics(memory_manager)
            
            # Identificar áreas de mejora
            context['improvement_areas'] = self._identify_improvement_areas(context)
                
        except Exception as e:
            logger.error(f"Error building reflection context: {e}")
            
        return context
    
    async def _get_recent_actions(self, memory_manager) -> List[Dict[str, Any]]:
        """Obtiene acciones recientes"""
        actions = []
        try:
            if hasattr(memory_manager, 'get_recent_episodes'):
                episodes = await memory_manager.get_recent_episodes(limit=5)
                for episode in episodes:
                    if hasattr(episode, 'actions'):
                        actions.extend(episode.actions[:2])  # Top 2 acciones por episodio
        except Exception as e:
            logger.error(f"Error getting recent actions: {e}")
        return actions
    
    async def _get_recent_outcomes(self, memory_manager) -> List[Dict[str, Any]]:
        """Obtiene resultados recientes"""
        outcomes = []
        try:
            if hasattr(memory_manager, 'get_recent_episodes'):
                episodes = await memory_manager.get_recent_episodes(limit=5)
                for episode in episodes:
                    outcome = {
                        'task': getattr(episode, 'title', 'Unknown'),
                        'success': getattr(episode, 'success', False),
                        'result': getattr(episode, 'description', ''),
                        'timestamp': getattr(episode, 'timestamp', datetime.now())
                    }
                    outcomes.append(outcome)
        except Exception as e:
            logger.error(f"Error getting recent outcomes: {e}")
        return outcomes
    
    async def _extract_lessons_learned(self, memory_manager) -> List[Dict[str, Any]]:
        """Extrae lecciones aprendidas"""
        lessons = []
        try:
            # Lecciones básicas basadas en patrones comunes
            lessons = [
                {
                    'lesson': 'Dividir tareas complejas en pasos más simples',
                    'context': 'Tareas de planificación',
                    'confidence': 0.8
                },
                {
                    'lesson': 'Verificar resultados antes de proceder',
                    'context': 'Ejecución de herramientas',
                    'confidence': 0.9
                },
                {
                    'lesson': 'Usar contexto de memoria para mejorar respuestas',
                    'context': 'Generación de respuestas',
                    'confidence': 0.85
                }
            ]
        except Exception as e:
            logger.error(f"Error extracting lessons: {e}")
        return lessons
    
    async def _get_performance_metrics(self, memory_manager) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento"""
        metrics = {}
        try:
            if hasattr(memory_manager, 'get_memory_stats'):
                stats = await memory_manager.get_memory_stats()
                metrics = {
                    'episodes_stored': stats.get('episodic_memory', {}).get('total_episodes', 0),
                    'success_rate': 0.75,  # Valor por defecto
                    'avg_response_time': 2.5,  # Valor por defecto en segundos
                    'memory_utilization': 0.68  # Valor por defecto
                }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            metrics = {
                'episodes_stored': 0,
                'success_rate': 0.5,
                'avg_response_time': 3.0,
                'memory_utilization': 0.5
            }
        return metrics
    
    def _identify_improvement_areas(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifica áreas de mejora basadas en el contexto"""
        improvements = []
        
        try:
            # Analizar métricas de rendimiento
            metrics = context.get('performance_metrics', {})
            success_rate = metrics.get('success_rate', 0.5)
            response_time = metrics.get('avg_response_time', 3.0)
            
            if success_rate < 0.8:
                improvements.append({
                    'area': 'success_rate',
                    'description': 'Mejorar tasa de éxito en tareas',
                    'priority': 'high',
                    'current_value': success_rate,
                    'target_value': 0.85
                })
            
            if response_time > 2.0:
                improvements.append({
                    'area': 'response_time',
                    'description': 'Optimizar tiempo de respuesta',
                    'priority': 'medium',
                    'current_value': response_time,
                    'target_value': 1.5
                })
            
            # Analizar resultados recientes
            outcomes = context.get('outcomes', [])
            failed_outcomes = [o for o in outcomes if not o.get('success', True)]
            
            if len(failed_outcomes) > 2:
                improvements.append({
                    'area': 'error_handling',
                    'description': 'Mejorar manejo de errores y recuperación',
                    'priority': 'high',
                    'recent_failures': len(failed_outcomes)
                })
                
        except Exception as e:
            logger.error(f"Error identifying improvement areas: {e}")
            
        return improvements