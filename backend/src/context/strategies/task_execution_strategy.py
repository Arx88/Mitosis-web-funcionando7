"""
Estrategia de Contexto para Ejecución de Tareas
Implementación según UPGRADE.md Sección 1.1.B
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskExecutionContextStrategy:
    """
    Estrategia especializada para construir contexto óptimo durante la ejecución de tareas.
    Integra información de la tarea actual, herramientas disponibles, conocimiento relevante
    y historial de ejecución.
    """
    
    def __init__(self):
        self.strategy_name = "task_execution"
        self.priority_weights = {
            'current_task': 0.3,
            'available_tools': 0.2,
            'relevant_knowledge': 0.25,
            'execution_history': 0.25
        }
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        """
        Construye contexto optimizado para ejecución de tareas
        
        Args:
            query: Consulta/mensaje para el cual construir contexto
            memory_manager: Gestor de memoria para obtener conocimiento relevante
            task_manager: Gestor de tareas para obtener información de la tarea actual
            max_tokens: Límite máximo de tokens para el contexto
            
        Returns:
            Diccionario con contexto optimizado para ejecución de tareas
        """
        
        context = {
            'type': 'task_execution',
            'strategy': self.strategy_name,
            'current_task': None,
            'current_phase': None,
            'available_tools': [],
            'relevant_knowledge': [],
            'conversation_history': [],
            'execution_history': [],
            'context_quality': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 1. Obtener información de la tarea actual
            current_task_context = await self._get_current_task_context(task_manager, query)
            context['current_task'] = current_task_context['task']
            context['current_phase'] = current_task_context['phase']
            
            # 2. Obtener herramientas disponibles y relevantes
            available_tools = await self._get_available_tools(task_manager, query)
            context['available_tools'] = available_tools
            
            # 3. Buscar conocimiento relevante en memoria
            if memory_manager:
                relevant_knowledge = await self._get_relevant_knowledge(memory_manager, query, max_tokens)
                context['relevant_knowledge'] = relevant_knowledge
            
            # 4. Obtener historial de ejecución de tareas similares
            if memory_manager:
                execution_history = await self._get_execution_history(memory_manager, query, context['current_task'])
                context['execution_history'] = execution_history
            
            # 5. Calcular calidad del contexto
            context['context_quality'] = self._calculate_context_quality(context)
            
            # 6. Optimizar contexto según límite de tokens
            optimized_context = self._optimize_context_size(context, max_tokens)
            
            logger.info(f"✅ Built task execution context with quality {optimized_context['context_quality']:.2f}")
            
            return optimized_context
            
        except Exception as e:
            logger.error(f"❌ Error building task execution context: {e}")
            return self._build_fallback_context(query)
    
    async def _get_current_task_context(self, task_manager, query: str) -> Dict[str, Any]:
        """Obtiene contexto de la tarea actual"""
        
        task_context = {'task': None, 'phase': None}
        
        try:
            if not task_manager:
                return task_context
            
            # Obtener tarea actual
            current_task = None
            if hasattr(task_manager, 'get_current_task'):
                current_task = await task_manager.get_current_task()
            elif hasattr(task_manager, 'get_active_tasks'):
                active_tasks = await task_manager.get_active_tasks()
                if active_tasks:
                    current_task = active_tasks[0]  # Tomar la más reciente
            
            if current_task:
                task_context['task'] = {
                    'id': getattr(current_task, 'id', 'unknown'),
                    'title': getattr(current_task, 'title', 'Unknown Task'),
                    'goal': getattr(current_task, 'goal', 'No goal specified'),
                    'description': getattr(current_task, 'description', 'No description available'),
                    'status': getattr(current_task, 'status', 'active'),
                    'priority': getattr(current_task, 'priority', 'medium')
                }
                
                # Obtener fase actual si está disponible
                if hasattr(task_manager, 'get_current_phase'):
                    current_phase = await task_manager.get_current_phase(current_task.id)
                    if current_phase:
                        task_context['phase'] = {
                            'id': getattr(current_phase, 'id', 'unknown'),
                            'title': getattr(current_phase, 'title', 'Unknown Phase'),
                            'description': getattr(current_phase, 'description', 'No description'),
                            'required_capabilities': getattr(current_phase, 'required_capabilities', []),
                            'expected_outcomes': getattr(current_phase, 'expected_outcomes', [])
                        }
                
        except Exception as e:
            logger.error(f"Error getting current task context: {e}")
            
        return task_context
    
    async def _get_available_tools(self, task_manager, query: str) -> List[Dict[str, Any]]:
        """Obtiene lista de herramientas disponibles y relevantes para la consulta"""
        
        tools = []
        
        try:
            # Lista básica de herramientas conocidas
            basic_tools = [
                {
                    'name': 'web_search',
                    'description': 'Búsqueda de información en internet',
                    'capabilities': ['search', 'information_gathering'],
                    'relevance': self._calculate_tool_relevance('web_search', query)
                },
                {
                    'name': 'analysis',
                    'description': 'Análisis y procesamiento de información',
                    'capabilities': ['analysis', 'data_processing'],
                    'relevance': self._calculate_tool_relevance('analysis', query)
                },
                {
                    'name': 'creation',
                    'description': 'Creación de contenido y documentos',
                    'capabilities': ['content_creation', 'document_generation'],
                    'relevance': self._calculate_tool_relevance('creation', query)
                },
                {
                    'name': 'planning',
                    'description': 'Planificación y organización de tareas',
                    'capabilities': ['planning', 'organization'],
                    'relevance': self._calculate_tool_relevance('planning', query)
                },
                {
                    'name': 'delivery',
                    'description': 'Entrega y presentación de resultados',
                    'capabilities': ['delivery', 'presentation'],
                    'relevance': self._calculate_tool_relevance('delivery', query)
                }
            ]
            
            # Ordenar por relevancia y tomar las más relevantes
            basic_tools.sort(key=lambda x: x['relevance'], reverse=True)
            tools = basic_tools[:4]  # Top 4 herramientas más relevantes
            
            # Intentar obtener herramientas desde task_manager si está disponible
            if task_manager and hasattr(task_manager, 'get_available_tools'):
                manager_tools = await task_manager.get_available_tools()
                if manager_tools:
                    tools.extend(manager_tools[:3])  # Agregar hasta 3 adicionales
                    
        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            
        return tools
    
    def _calculate_tool_relevance(self, tool_name: str, query: str) -> float:
        """Calcula relevancia de una herramienta para la consulta"""
        
        query_lower = query.lower()
        
        # Palabras clave por herramienta
        tool_keywords = {
            'web_search': ['buscar', 'información', 'internet', 'datos', 'investigar', 'encontrar'],
            'analysis': ['analizar', 'análisis', 'estudiar', 'examinar', 'evaluar', 'revisar'],
            'creation': ['crear', 'generar', 'producir', 'desarrollar', 'escribir', 'documento'],
            'planning': ['planificar', 'organizar', 'plan', 'estrategia', 'estructura', 'diseñar'],
            'delivery': ['entregar', 'presentar', 'finalizar', 'completar', 'resultado', 'informe']
        }
        
        keywords = tool_keywords.get(tool_name, [])
        matches = sum(1 for keyword in keywords if keyword in query_lower)
        
        # Calcular relevancia normalizada
        if keywords:
            relevance = min(matches / len(keywords), 1.0)
        else:
            relevance = 0.3  # Relevancia base
            
        return relevance
    
    async def _get_relevant_knowledge(self, memory_manager, query: str, max_tokens: int) -> List[Dict[str, Any]]:
        """Obtiene conocimiento relevante de la memoria"""
        
        knowledge = []
        
        try:
            # Buscar conocimiento semántico relevante
            if hasattr(memory_manager, 'search_knowledge'):
                search_results = await memory_manager.search_knowledge(
                    query=query,
                    limit=5,
                    min_confidence=0.7
                )
                
                for result in search_results:
                    knowledge.append({
                        'content': getattr(result, 'content', str(result))[:200],  # Limitar tamaño
                        'confidence': getattr(result, 'confidence', 0.8),
                        'source': getattr(result, 'source', 'memory'),
                        'type': 'semantic_knowledge'
                    })
            
            # Buscar episodios relevantes
            if hasattr(memory_manager, 'get_recent_episodes'):
                episodes = await memory_manager.get_recent_episodes(limit=3, include_successful=True)
                
                for episode in episodes[:2]:  # Top 2 episodios
                    if hasattr(episode, 'title') and hasattr(episode, 'outcomes'):
                        knowledge.append({
                            'content': f"Experiencia: {episode.title} - {episode.outcomes[0] if episode.outcomes else 'Sin resultado'}",
                            'confidence': 0.9,
                            'source': 'episodic_memory',
                            'type': 'experience'
                        })
                        
        except Exception as e:
            logger.error(f"Error getting relevant knowledge: {e}")
            
        return knowledge
    
    async def _get_execution_history(self, memory_manager, query: str, current_task: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Obtiene historial de ejecución de tareas similares"""
        
        history = []
        
        try:
            # Buscar tareas completadas similares
            if hasattr(memory_manager, 'get_recent_tasks'):
                similar_tasks = await memory_manager.get_recent_tasks(count=5, status='completed')
                
                for task in similar_tasks[:3]:  # Top 3 tareas similares
                    history.append({
                        'title': getattr(task, 'title', 'Unknown Task'),
                        'results': getattr(task, 'results', 'No results available'),
                        'success': getattr(task, 'success', True),
                        'execution_time': getattr(task, 'execution_time', 0),
                        'tools_used': getattr(task, 'tools_used', [])
                    })
            
            # Si no hay método específico, intentar buscar en memoria episódica
            elif hasattr(memory_manager, 'episodic_memory'):
                recent_episodes = await memory_manager.get_recent_episodes(limit=5, include_failed=False)
                
                for episode in recent_episodes[:3]:
                    if hasattr(episode, 'success') and episode.success:
                        history.append({
                            'title': getattr(episode, 'title', 'Unknown Episode'),
                            'results': getattr(episode, 'description', 'No description'),
                            'success': episode.success,
                            'execution_time': getattr(episode, 'duration', 0),
                            'tools_used': []
                        })
                        
        except Exception as e:
            logger.error(f"Error getting execution history: {e}")
            
        return history
    
    def _calculate_context_quality(self, context: Dict[str, Any]) -> float:
        """Calcula la calidad del contexto construido"""
        
        quality_score = 0.0
        
        try:
            # Evaluar componentes del contexto
            if context['current_task']:
                quality_score += self.priority_weights['current_task']
                
            if context['available_tools']:
                tool_quality = min(len(context['available_tools']) / 4.0, 1.0)
                quality_score += self.priority_weights['available_tools'] * tool_quality
                
            if context['relevant_knowledge']:
                knowledge_quality = min(len(context['relevant_knowledge']) / 3.0, 1.0)
                quality_score += self.priority_weights['relevant_knowledge'] * knowledge_quality
                
            if context['execution_history']:
                history_quality = min(len(context['execution_history']) / 3.0, 1.0)
                quality_score += self.priority_weights['execution_history'] * history_quality
                
        except Exception as e:
            logger.error(f"Error calculating context quality: {e}")
            quality_score = 0.5  # Calidad por defecto
            
        return min(quality_score, 1.0)
    
    def _optimize_context_size(self, context: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Optimiza el tamaño del contexto según el límite de tokens"""
        
        # Estimación aproximada: 4 caracteres = 1 token
        estimated_tokens = len(str(context)) // 4
        
        if estimated_tokens <= max_tokens:
            return context
        
        # Si excede el límite, reducir componentes menos importantes
        optimized = context.copy()
        
        # Reducir conocimiento relevante primero
        if len(optimized['relevant_knowledge']) > 3:
            optimized['relevant_knowledge'] = optimized['relevant_knowledge'][:3]
        
        # Reducir historial de ejecución
        if len(optimized['execution_history']) > 2:
            optimized['execution_history'] = optimized['execution_history'][:2]
        
        # Reducir herramientas disponibles
        if len(optimized['available_tools']) > 3:
            optimized['available_tools'] = optimized['available_tools'][:3]
        
        # Recalcular calidad después de la optimización
        optimized['context_quality'] = self._calculate_context_quality(optimized)
        optimized['optimized'] = True
        
        return optimized
    
    def _build_fallback_context(self, query: str) -> Dict[str, Any]:
        """Construye contexto de fallback en caso de error"""
        return {
            'type': 'task_execution_fallback',
            'strategy': self.strategy_name,
            'query': query,
            'current_task': None,
            'available_tools': [{'name': 'basic_processing', 'description': 'Procesamiento básico'}],
            'relevant_knowledge': [],
            'execution_history': [],
            'context_quality': 0.3,
            'fallback': True,
            'timestamp': datetime.now().isoformat()
        }