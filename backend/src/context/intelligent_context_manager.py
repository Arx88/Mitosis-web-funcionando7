"""
Sistema de Contexto Dinámico Inteligente
Implementación según UPGRADE.md Sección 1.1
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class IntelligentContextManager:
    """
    Gestor de Contexto Inteligente que proporciona contexto optimizado
    para cada tipo de tarea usando estrategias especializadas.
    """
    
    def __init__(self, memory_manager, task_manager, model_manager):
        self.memory_manager = memory_manager
        self.task_manager = task_manager
        self.model_manager = model_manager
        self.context_strategies = {}
        self.context_cache = {}
        self.context_performance = {}
        
        # Cargar estrategias de contexto especializadas
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Inicializa las estrategias de contexto especializadas"""
        try:
            from .strategies.chat_context_strategy import ChatContextStrategy
            from .strategies.task_planning_strategy import TaskPlanningContextStrategy
            from .strategies.task_execution_strategy import TaskExecutionContextStrategy
            from .strategies.reflection_strategy import ReflectionContextStrategy
            from .strategies.error_handling_strategy import ErrorHandlingContextStrategy
            
            self.context_strategies = {
                'chat': ChatContextStrategy(),
                'task_planning': TaskPlanningContextStrategy(),
                'task_execution': TaskExecutionContextStrategy(),
                'reflection': ReflectionContextStrategy(),
                'error_handling': ErrorHandlingContextStrategy()
            }
            
            logger.info(f"✅ Initialized {len(self.context_strategies)} context strategies")
            
        except ImportError as e:
            logger.warning(f"⚠️ Could not import some context strategies: {e}")
            # Inicializar estrategias básicas como fallback
            self.context_strategies = {
                'chat': BasicContextStrategy(),
                'task_planning': BasicContextStrategy(),
                'task_execution': BasicContextStrategy(),
                'reflection': BasicContextStrategy(),
                'error_handling': BasicContextStrategy()
            }
    
    async def build_context(self, context_type: str, query: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Construye contexto optimizado basado en el tipo de interacción
        
        Args:
            context_type: Tipo de contexto ('chat', 'task_planning', 'task_execution', etc.)
            query: Consulta/mensaje para el cual construir contexto
            max_tokens: Límite máximo de tokens para el contexto
            
        Returns:
            Diccionario con contexto optimizado
        """
        start_time = time.time()
        
        try:
            # Verificar cache de contexto
            cache_key = self._generate_cache_key(context_type, query, max_tokens)
            if cache_key in self.context_cache:
                cached_context = self.context_cache[cache_key]
                if self._is_cache_valid(cached_context):
                    logger.debug(f"📋 Using cached context for {context_type}")
                    return cached_context['context']
            
            # Obtener estrategia apropiada
            strategy = self.context_strategies.get(context_type)
            if not strategy:
                logger.warning(f"⚠️ No strategy found for context type: {context_type}, using default")
                return await self._build_default_context(query, max_tokens)
            
            # Construir contexto usando estrategia especializada
            context = await strategy.build_context(
                query=query,
                memory_manager=self.memory_manager,
                task_manager=self.task_manager,
                max_tokens=max_tokens
            )
            
            # Enriquecer contexto con información adicional
            enriched_context = await self._enrich_context(context, query, context_type)
            
            # Cachear contexto para futuros usos
            self.context_cache[cache_key] = {
                'context': enriched_context,
                'timestamp': datetime.now(),
                'query': query,
                'type': context_type
            }
            
            # Registrar rendimiento
            execution_time = time.time() - start_time
            self._track_context_performance(context_type, execution_time, len(str(enriched_context)))
            
            logger.info(f"✅ Built {context_type} context in {execution_time:.2f}s")
            return enriched_context
            
        except Exception as e:
            logger.error(f"❌ Error building context for {context_type}: {e}")
            return await self._build_default_context(query, max_tokens)
    
    async def _build_default_context(self, query: str, max_tokens: int) -> Dict[str, Any]:
        """Construye contexto por defecto cuando no hay estrategia específica"""
        
        context = {
            'type': 'default',
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'memory_context': None,
            'relevant_knowledge': [],
            'conversation_history': [],
            'system_state': 'available'
        }
        
        try:
            # Intentar obtener contexto básico de memoria si está disponible
            if self.memory_manager:
                memory_context = await self.memory_manager.retrieve_context(
                    query=query,
                    max_items=5,
                    include_episodic=True,
                    include_semantic=True
                )
                context['memory_context'] = memory_context
                
        except Exception as e:
            logger.error(f"Error getting basic memory context: {e}")
        
        return context
    
    async def _enrich_context(self, context: Dict[str, Any], query: str, context_type: str) -> Dict[str, Any]:
        """Enriquece el contexto con información adicional del sistema"""
        
        enriched = context.copy()
        
        try:
            # Agregar información del sistema
            enriched['system_info'] = {
                'context_type': context_type,
                'generation_time': datetime.now().isoformat(),
                'query_length': len(query),
                'context_version': '1.0'
            }
            
            # Agregar métricas de rendimiento si están disponibles
            if context_type in self.context_performance:
                perf = self.context_performance[context_type]
                enriched['performance_info'] = {
                    'avg_build_time': perf.get('avg_time', 0),
                    'usage_count': perf.get('count', 0),
                    'success_rate': perf.get('success_rate', 1.0)
                }
            
            # Agregar relevancia semántica si es posible
            if self.memory_manager and hasattr(self.memory_manager, 'calculate_relevance'):
                relevance_score = await self.memory_manager.calculate_relevance(query, context)
                enriched['relevance_score'] = relevance_score
                
        except Exception as e:
            logger.error(f"Error enriching context: {e}")
            
        return enriched
    
    def _generate_cache_key(self, context_type: str, query: str, max_tokens: int) -> str:
        """Genera clave de cache para el contexto"""
        import hashlib
        
        content = f"{context_type}:{query[:100]}:{max_tokens}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_context: Dict[str, Any], max_age_seconds: int = 300) -> bool:
        """Verifica si el contexto cacheado sigue siendo válido"""
        try:
            cached_time = cached_context['timestamp']
            age = (datetime.now() - cached_time).total_seconds()
            return age < max_age_seconds
        except:
            return False
    
    def _track_context_performance(self, context_type: str, execution_time: float, context_size: int):
        """Rastrea el rendimiento de la construcción de contexto"""
        if context_type not in self.context_performance:
            self.context_performance[context_type] = {
                'total_time': 0,
                'count': 0,
                'total_size': 0,
                'success_count': 0
            }
        
        perf = self.context_performance[context_type]
        perf['total_time'] += execution_time
        perf['count'] += 1
        perf['total_size'] += context_size
        perf['success_count'] += 1
        
        # Calcular promedios
        perf['avg_time'] = perf['total_time'] / perf['count']
        perf['avg_size'] = perf['total_size'] / perf['count']
        perf['success_rate'] = perf['success_count'] / perf['count']
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento del gestor de contexto"""
        return {
            'strategies_loaded': len(self.context_strategies),
            'cache_size': len(self.context_cache),
            'performance_by_type': self.context_performance.copy(),
            'total_contexts_built': sum(p.get('count', 0) for p in self.context_performance.values())
        }
    
    def clear_cache(self):
        """Limpia el cache de contextos"""
        self.context_cache.clear()
        logger.info("🧹 Context cache cleared")


class BasicContextStrategy:
    """Estrategia básica de contexto como fallback"""
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        """Construye contexto básico"""
        return {
            'type': 'basic',
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'available_tools': [],
            'relevant_knowledge': [],
            'conversation_history': []
        }