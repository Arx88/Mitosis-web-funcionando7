"""
Gestor avanzado de memoria para el agente autónomo
Integra múltiples tipos de memoria y proporciona interfaz unificada
UPGRADE AI: Modificado para usar contexto de tareas y filtrado por task_id
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import pandas as pd

from .working_memory_store import WorkingMemoryStore
from .episodic_memory_store import EpisodicMemoryStore, Episode
from .semantic_memory_store import SemanticMemoryStore, SemanticConcept, SemanticFact
from .procedural_memory_store import ProceduralMemoryStore, Procedure, ToolStrategy
from .semantic_indexer import SemanticIndexer
from .embedding_service import EmbeddingService
from ..utils.task_context import get_current_task_context, log_with_context

logger = logging.getLogger(__name__)

class AdvancedMemoryManager:
    """
    Gestor avanzado de memoria que integra múltiples tipos de memoria
    para proporcionar capacidades de aprendizaje y contextualización al agente
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el gestor avanzado de memoria
        
        Args:
            config: Configuración del sistema de memoria
        """
        self.config = config or {}
        
        # Inicializar componentes de memoria
        self.working_memory = WorkingMemoryStore(
            max_capacity=self.config.get('working_memory_capacity', 50),
            ttl_minutes=self.config.get('working_memory_ttl', 60)
        )
        
        self.episodic_memory = EpisodicMemoryStore(
            max_episodes=self.config.get('episodic_memory_capacity', 1000)
        )
        
        self.semantic_memory = SemanticMemoryStore(
            max_concepts=self.config.get('semantic_concepts_capacity', 10000),
            max_facts=self.config.get('semantic_facts_capacity', 50000)
        )
        
        self.procedural_memory = ProceduralMemoryStore(
            max_procedures=self.config.get('procedural_capacity', 1000),
            max_strategies=self.config.get('tool_strategies_capacity', 5000)
        )
        
        # Servicios de soporte
        self.embedding_service = EmbeddingService(
            model_name=self.config.get('embedding_model', 'all-MiniLM-L6-v2'),
            storage_path=self.config.get('embedding_storage', 'embeddings')
        )
        
        self.semantic_indexer = SemanticIndexer(self.embedding_service)
        
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializa el gestor de memoria"""
        try:
            # Inicializar servicios
            await self.embedding_service.initialize()
            await self.semantic_indexer.initialize()
            
            self.is_initialized = True
            logger.info("AdvancedMemoryManager inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando AdvancedMemoryManager: {e}")
            raise
    
    async def store_experience(self, experience: Dict[str, Any]):
        """
        Almacena una experiencia completa en múltiples tipos de memoria
        UPGRADE AI: Modificado para incluir task_id en todas las operaciones de memoria
        
        Args:
            experience: Diccionario con datos de la experiencia
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            # UPGRADE AI: Obtener contexto de tarea actual
            current_context = get_current_task_context()
            task_id = current_context.task_id if current_context else experience.get('task_id', 'unknown')
            
            # Extraer información de la experiencia
            task_context = experience.get('context', {})
            execution_steps = experience.get('execution_steps', [])
            outcomes = experience.get('outcomes', [])
            success = experience.get('success', False)
            execution_time = experience.get('execution_time', 0)
            
            # UPGRADE AI: Asegurar que task_id esté presente en todos los datos
            task_context['task_id'] = task_id
            for step in execution_steps:
                step['task_id'] = task_id
            for outcome in outcomes:
                outcome['task_id'] = task_id
            
            log_with_context(logging.INFO, f"Almacenando experiencia con {len(execution_steps)} pasos")
            
            # 1. Almacenar en memoria de trabajo (contexto inmediato)
            context_id = f"ctx_{task_id}_{datetime.now().timestamp()}"
            self.working_memory.store_context(context_id, {
                'task_id': task_id,  # UPGRADE AI: Agregar task_id explícito
                'task_context': task_context,
                'execution_summary': {
                    'steps_count': len(execution_steps),
                    'success': success,
                    'execution_time': execution_time
                },
                'timestamp': datetime.now().isoformat()
            })
            
            # 2. Almacenar en memoria episódica
            episode_id = f"ep_{task_id}_{datetime.now().timestamp()}"
            episode = Episode(
                id=episode_id,
                title=f"Tarea: {task_context.get('task_type', 'general')}",
                description=task_context.get('description', 'Tarea ejecutada por el agente'),
                context=task_context,
                actions=execution_steps,
                outcomes=outcomes,
                timestamp=datetime.now(),
                duration=timedelta(seconds=execution_time),
                success=success,
                tags=task_context.get('tags', []),
                importance=self._calculate_importance(task_context, success, execution_time)
            )
            
            self.episodic_memory.store_episode(episode)
            
            # 3. Extraer y almacenar conocimiento semántico
            await self._extract_semantic_knowledge(experience)
            
            # 4. Aprender procedimientos
            self.procedural_memory.learn_from_execution(
                task_context, execution_steps, success, execution_time
            )
            
            # 5. Indexar para búsqueda semántica
            await self._index_experience(experience)
            
            logger.debug(f"Experiencia almacenada en memoria: éxito={success}, duración={execution_time}s")
            
        except Exception as e:
            logger.error(f"Error almacenando experiencia: {e}")
            raise
    
    async def retrieve_relevant_context(self, query: str, context_type: str = "all", 
                                      max_results: int = 10) -> Dict[str, Any]:
        """
        Recupera contexto relevante de todos los tipos de memoria
        
        Args:
            query: Consulta de búsqueda
            context_type: Tipo de contexto ('working', 'episodic', 'semantic', 'procedural', 'all')
            max_results: Número máximo de resultados
            
        Returns:
            Diccionario con contexto relevante
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            context = {
                'query': query,
                'retrieved_at': datetime.now().isoformat(),
                'working_memory': [],
                'episodic_memory': [],
                'semantic_memory': [],
                'procedural_memory': [],
                'synthesized_context': ''
            }
            
            # Búsqueda en memoria de trabajo
            if context_type in ['working', 'all']:
                working_contexts = self.working_memory.search_contexts(query, max_results)
                context['working_memory'] = working_contexts
            
            # Búsqueda en memoria episódica
            if context_type in ['episodic', 'all']:
                similar_episodes = self.episodic_memory.search_episodes(query, max_results)
                context['episodic_memory'] = [
                    {
                        'id': ep.id,
                        'title': ep.title,
                        'description': ep.description,
                        'success': ep.success,
                        'timestamp': ep.timestamp.isoformat(),
                        'importance': ep.importance
                    }
                    for ep in similar_episodes
                ]
            
            # Búsqueda en memoria semántica
            if context_type in ['semantic', 'all']:
                relevant_concepts = self.semantic_memory.search_concepts(query, limit=max_results)
                relevant_facts = self.semantic_memory.search_facts(subject=query, limit=max_results)
                
                context['semantic_memory'] = {
                    'concepts': [
                        {
                            'id': concept.id,
                            'name': concept.name,
                            'description': concept.description,
                            'category': concept.category,
                            'confidence': concept.confidence
                        }
                        for concept in relevant_concepts
                    ],
                    'facts': [
                        {
                            'id': fact.id,
                            'subject': fact.subject,
                            'predicate': fact.predicate,
                            'object': fact.object,
                            'confidence': fact.confidence
                        }
                        for fact in relevant_facts
                    ]
                }
            
            # Búsqueda en memoria procedimental
            if context_type in ['procedural', 'all']:
                # Crear contexto simulado para búsqueda de procedimientos
                search_context = {'task_type': query, 'complexity': 'medium'}
                applicable_procedures = self.procedural_memory.find_applicable_procedures(search_context)
                
                context['procedural_memory'] = [
                    {
                        'id': proc.id,
                        'name': proc.name,
                        'description': proc.description,
                        'success_rate': proc.success_rate,
                        'effectiveness_score': proc.effectiveness_score,
                        'usage_count': proc.usage_count
                    }
                    for proc in applicable_procedures
                ]
            
            # Sintetizar contexto
            context['synthesized_context'] = await self._synthesize_context(context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error recuperando contexto relevante: {e}")
            return {'error': str(e)}
    
    async def semantic_search(self, query: str, max_results: int = 10, 
                            memory_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica a través de todos los tipos de memoria
        
        Args:
            query: Consulta de búsqueda
            max_results: Número máximo de resultados
            memory_types: Tipos de memoria a buscar (default: all)
        
        Returns:
            Lista de resultados de búsqueda ordenados por relevancia
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            results = []
            
            # Si no se especifican tipos de memoria, buscar en todos
            if memory_types is None:
                memory_types = ['working', 'episodic', 'semantic', 'procedural']
            
            # Búsqueda en memoria de trabajo
            if 'working' in memory_types:
                working_contexts = self.working_memory.search_contexts(query, max_results)
                for context in working_contexts:
                    results.append({
                        'type': 'working_memory',
                        'content': context,
                        'relevance_score': 0.8,  # Score base para memoria de trabajo
                        'source': 'working_memory_context'
                    })
            
            # Búsqueda en memoria episódica
            if 'episodic' in memory_types:
                similar_episodes = self.episodic_memory.search_episodes(query, max_results)
                for episode in similar_episodes:
                    results.append({
                        'type': 'episodic_memory',
                        'content': {
                            'id': episode.id,
                            'title': episode.title,
                            'description': episode.description,
                            'success': episode.success,
                            'timestamp': episode.timestamp.isoformat(),
                            'importance': episode.importance
                        },
                        'relevance_score': episode.importance / 5.0,  # Normalizar importancia
                        'source': 'episodic_memory_episode'
                    })
            
            # Búsqueda en memoria semántica
            if 'semantic' in memory_types:
                # Buscar conceptos relevantes
                relevant_concepts = self.semantic_memory.search_concepts(query, limit=max_results)
                for concept in relevant_concepts:
                    results.append({
                        'type': 'semantic_memory',
                        'content': {
                            'id': concept.id,
                            'name': concept.name,
                            'description': concept.description,
                            'category': concept.category,
                            'confidence': concept.confidence
                        },
                        'relevance_score': concept.confidence,
                        'source': 'semantic_memory_concept'
                    })
                
                # Buscar hechos relevantes
                relevant_facts = self.semantic_memory.search_facts(subject=query, limit=max_results)
                for fact in relevant_facts:
                    results.append({
                        'type': 'semantic_memory',
                        'content': {
                            'id': fact.id,
                            'subject': fact.subject,
                            'predicate': fact.predicate,
                            'object': fact.object,
                            'confidence': fact.confidence
                        },
                        'relevance_score': fact.confidence,
                        'source': 'semantic_memory_fact'
                    })
            
            # Búsqueda en memoria procedimental
            if 'procedural' in memory_types:
                # Crear contexto simulado para búsqueda de procedimientos
                search_context = {'task_type': query, 'complexity': 'medium'}
                applicable_procedures = self.procedural_memory.find_applicable_procedures(search_context)
                
                for procedure in applicable_procedures:
                    results.append({
                        'type': 'procedural_memory',
                        'content': {
                            'id': procedure.id,
                            'name': procedure.name,
                            'description': procedure.description,
                            'success_rate': procedure.success_rate,
                            'effectiveness_score': procedure.effectiveness_score,
                            'usage_count': procedure.usage_count
                        },
                        'relevance_score': procedure.effectiveness_score,
                        'source': 'procedural_memory_procedure'
                    })
            
            # Búsqueda semántica usando semantic_indexer
            try:
                semantic_results = await self.semantic_indexer.search_similar_documents(query, max_results)
                for doc_result in semantic_results:
                    results.append({
                        'type': 'semantic_index',
                        'content': {
                            'document_id': doc_result.get('id'),
                            'content': doc_result.get('content'),
                            'metadata': doc_result.get('metadata', {})
                        },
                        'relevance_score': doc_result.get('similarity', 0.5),
                        'source': 'semantic_indexer'
                    })
            except Exception as e:
                logger.warning(f"Error en búsqueda semántica indexada: {e}")
            
            # Ordenar resultados por relevancia
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Limitar resultados
            results = results[:max_results]
            
            logger.debug(f"Búsqueda semántica completada: {len(results)} resultados para query '{query}'")
            
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda semántica: {e}")
            return []
    
    async def get_learning_recommendations(self, current_task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Obtiene recomendaciones basadas en aprendizaje previo
        
        Args:
            current_task: Tarea actual
            
        Returns:
            Lista de recomendaciones
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            recommendations = []
            
            # 1. Buscar episodios similares exitosos
            similar_episodes = self.episodic_memory.find_similar_episodes(
                current_task, limit=5
            )
            
            successful_episodes = [ep for ep in similar_episodes if ep.success]
            
            if successful_episodes:
                recommendations.append({
                    'type': 'successful_pattern',
                    'description': f'Encontrados {len(successful_episodes)} episodios similares exitosos',
                    'confidence': 0.8,
                    'details': {
                        'episodes': [
                            {
                                'title': ep.title,
                                'success_rate': ep.success_rate if hasattr(ep, 'success_rate') else 1.0,
                                'actions_count': len(ep.actions)
                            }
                            for ep in successful_episodes
                        ]
                    }
                })
            
            # 2. Buscar procedimientos aplicables
            applicable_procedures = self.procedural_memory.find_applicable_procedures(current_task)
            
            if applicable_procedures:
                best_procedure = max(applicable_procedures, key=lambda p: p.effectiveness_score)
                recommendations.append({
                    'type': 'procedure_recommendation',
                    'description': f'Procedimiento recomendado: {best_procedure.name}',
                    'confidence': best_procedure.effectiveness_score,
                    'details': {
                        'procedure_id': best_procedure.id,
                        'success_rate': best_procedure.success_rate,
                        'usage_count': best_procedure.usage_count,
                        'steps': best_procedure.steps
                    }
                })
            
            # 3. Buscar mejores estrategias de herramientas
            task_tools = current_task.get('required_tools', [])
            for tool_name in task_tools:
                best_strategy = self.procedural_memory.get_best_tool_strategy(tool_name)
                
                if best_strategy:
                    recommendations.append({
                        'type': 'tool_strategy',
                        'description': f'Estrategia recomendada para {tool_name}',
                        'confidence': best_strategy.success_rate,
                        'details': {
                            'tool_name': tool_name,
                            'strategy_id': best_strategy.id,
                            'parameters': best_strategy.parameters,
                            'avg_execution_time': best_strategy.avg_execution_time
                        }
                    })
            
            # 4. Analizar patrones de fallo para evitar
            failure_patterns = self.episodic_memory.get_failure_patterns(limit=3)
            
            if failure_patterns:
                recommendations.append({
                    'type': 'failure_avoidance',
                    'description': 'Patrones de fallo identificados a evitar',
                    'confidence': 0.7,
                    'details': {
                        'patterns': [
                            {
                                'context_keys': pattern['pattern']['context_keys'],
                                'actions': pattern['pattern']['actions'],
                                'frequency': pattern['frequency']
                            }
                            for pattern in failure_patterns
                        ]
                    }
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones de aprendizaje: {e}")
            return []
    
    async def update_learning_feedback(self, execution_result: Dict[str, Any]):
        """
        Actualiza el aprendizaje basado en feedback de ejecución
        
        Args:
            execution_result: Resultado de ejecución con feedback
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            # Actualizar efectividad de procedimientos utilizados
            used_procedures = execution_result.get('used_procedures', [])
            for proc_info in used_procedures:
                proc_id = proc_info.get('id')
                success = proc_info.get('success', False)
                execution_time = proc_info.get('execution_time', 0)
                
                if proc_id:
                    self.procedural_memory.update_procedure_effectiveness(
                        proc_id, success, execution_time
                    )
            
            # Actualizar estrategias de herramientas
            used_strategies = execution_result.get('used_strategies', [])
            for strategy_info in used_strategies:
                strategy_id = strategy_info.get('id')
                success = strategy_info.get('success', False)
                execution_time = strategy_info.get('execution_time', 0)
                
                if strategy_id:
                    self.procedural_memory.update_strategy_effectiveness(
                        strategy_id, success, execution_time
                    )
            
            # Actualizar confianza en conocimiento semántico
            validated_concepts = execution_result.get('validated_concepts', [])
            for concept_info in validated_concepts:
                concept_id = concept_info.get('id')
                confidence_delta = concept_info.get('confidence_delta', 0)
                
                if concept_id:
                    self.semantic_memory.update_concept_confidence(concept_id, confidence_delta)
            
            logger.debug("Feedback de aprendizaje actualizado")
            
        except Exception as e:
            logger.error(f"Error actualizando feedback de aprendizaje: {e}")
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas del sistema de memoria
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            stats = {
                'system_info': {
                    'initialized': self.is_initialized,
                    'config': self.config,
                    'timestamp': datetime.now().isoformat()
                },
                'working_memory': self.working_memory.get_stats(),
                'episodic_memory': self.episodic_memory.get_stats(),
                'semantic_memory': self.semantic_memory.get_stats(),
                'procedural_memory': self.procedural_memory.get_stats(),
                'semantic_indexer': await self.semantic_indexer.get_document_stats(),
                'embedding_service': await self.embedding_service.get_stats()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de memoria: {e}")
            return {'error': str(e)}
    
    def _calculate_importance(self, context: Dict[str, Any], success: bool, execution_time: float) -> int:
        """
        Calcula la importancia de un episodio
        
        Args:
            context: Contexto de la tarea
            success: Si fue exitoso
            execution_time: Tiempo de ejecución
            
        Returns:
            Nivel de importancia (1-5)
        """
        try:
            importance = 3  # Base
            
            # Incrementar por éxito
            if success:
                importance += 1
            
            # Incrementar por complejidad
            complexity = context.get('complexity', 'medium')
            if complexity == 'high':
                importance += 1
            elif complexity == 'low':
                importance -= 1
            
            # Ajustar por tiempo de ejecución
            if execution_time > 300:  # > 5 minutos
                importance += 1
            elif execution_time < 30:  # < 30 segundos
                importance -= 1
            
            return max(1, min(5, importance))
            
        except Exception as e:
            logger.error(f"Error calculando importancia: {e}")
            return 3
    
    async def _extract_semantic_knowledge(self, experience: Dict[str, Any]):
        """
        Extrae conocimiento semántico de una experiencia
        
        Args:
            experience: Experiencia a procesar
        """
        try:
            task_context = experience.get('context', {})
            execution_steps = experience.get('execution_steps', [])
            success = experience.get('success', False)
            
            # Extraer conceptos del contexto
            task_type = task_context.get('task_type', 'general')
            
            if task_type != 'general':
                concept_id = f"concept_{task_type}"
                concept = SemanticConcept(
                    id=concept_id,
                    name=task_type,
                    description=f"Concepto relacionado con tareas de tipo {task_type}",
                    category="task_type",
                    attributes=task_context,
                    relations={},
                    confidence=0.8 if success else 0.6
                )
                
                self.semantic_memory.store_concept(concept)
            
            # Extraer hechos de los pasos de ejecución
            for i, step in enumerate(execution_steps):
                if step.get('tool_name') and step.get('result'):
                    fact_id = f"fact_{datetime.now().timestamp()}_{i}"
                    fact = SemanticFact(
                        id=fact_id,
                        subject=step['tool_name'],
                        predicate="produces_result",
                        object=str(step['result'])[:100],  # Limitar tamaño
                        context={'task_type': task_type, 'step_index': i},
                        confidence=0.9 if success else 0.5,
                        source="agent_execution"
                    )
                    
                    self.semantic_memory.store_fact(fact)
            
        except Exception as e:
            logger.error(f"Error extrayendo conocimiento semántico: {e}")
    
    async def _index_experience(self, experience: Dict[str, Any]):
        """
        Indexa una experiencia para búsqueda semántica
        
        Args:
            experience: Experiencia a indexar
        """
        try:
            # Crear contenido indexable
            task_context = experience.get('context', {})
            execution_steps = experience.get('execution_steps', [])
            outcomes = experience.get('outcomes', [])
            
            content_parts = []
            
            # Añadir contexto
            content_parts.append(f"Tarea: {task_context.get('task_type', 'general')}")
            if task_context.get('description'):
                content_parts.append(f"Descripción: {task_context['description']}")
            
            # Añadir pasos de ejecución
            for step in execution_steps:
                if step.get('tool_name'):
                    content_parts.append(f"Herramienta: {step['tool_name']}")
                if step.get('description'):
                    content_parts.append(f"Acción: {step['description']}")
            
            # Añadir resultados
            for outcome in outcomes:
                if outcome.get('description'):
                    content_parts.append(f"Resultado: {outcome['description']}")
            
            content = " | ".join(content_parts)
            
            # Indexar
            doc_id = f"exp_{datetime.now().timestamp()}"
            metadata = {
                'type': 'experience',
                'success': experience.get('success', False),
                'execution_time': experience.get('execution_time', 0),
                'task_type': task_context.get('task_type', 'general'),
                'category': 'agent_experience'
            }
            
            await self.semantic_indexer.add_document(doc_id, content, metadata)
            
        except Exception as e:
            logger.error(f"Error indexando experiencia: {e}")
    
    async def index_episode(self, episode):
        """
        Indexa un episodio específico para búsqueda semántica
        
        Args:
            episode: Episodio a indexar
        """
        try:
            # Crear contenido indexable del episodio
            content_parts = []
            
            # Añadir título y descripción
            content_parts.append(f"Título: {episode.title}")
            content_parts.append(f"Descripción: {episode.description}")
            
            # Añadir contexto si existe
            if episode.context:
                user_message = episode.context.get('user_message', '')
                agent_response = episode.context.get('agent_response', '')
                
                if user_message:
                    content_parts.append(f"Usuario: {user_message}")
                if agent_response:
                    content_parts.append(f"Agente: {agent_response}")
            
            # Añadir acciones
            for action in episode.actions:
                if action.get('content'):
                    content_parts.append(f"Acción: {action['content']}")
            
            # Añadir resultados
            for outcome in episode.outcomes:
                if outcome.get('content'):
                    content_parts.append(f"Resultado: {outcome['content']}")
            
            # Añadir tags
            if episode.tags:
                content_parts.append(f"Tags: {', '.join(episode.tags)}")
            
            content = " | ".join(content_parts)
            
            # Indexar episodio
            doc_id = f"episode_{episode.id}"
            metadata = {
                'type': 'episode',
                'episode_id': episode.id,
                'success': episode.success,
                'importance': episode.importance,
                'timestamp': episode.timestamp.isoformat(),
                'category': 'conversation_episode',
                'tags': episode.tags
            }
            
            await self.semantic_indexer.add_document(doc_id, content, metadata)
            logger.debug(f"Episodio {episode.id} indexado semánticamente")
            
        except Exception as e:
            logger.error(f"Error indexando episodio {episode.id}: {e}")
    
    async def _synthesize_context(self, context: Dict[str, Any]) -> str:
        """
        Sintetiza el contexto recuperado en un resumen útil
        
        Args:
            context: Contexto recuperado
            
        Returns:
            Resumen sintetizado
        """
        try:
            synthesis_parts = []
            
            # Memoria de trabajo
            working_memory = context.get('working_memory', [])
            if working_memory:
                synthesis_parts.append(f"Contexto reciente: {len(working_memory)} elementos en memoria de trabajo")
            
            # Memoria episódica
            episodic_memory = context.get('episodic_memory', [])
            if episodic_memory:
                successful_episodes = [ep for ep in episodic_memory if ep.get('success')]
                synthesis_parts.append(f"Experiencias similares: {len(successful_episodes)} episodios exitosos de {len(episodic_memory)} totales")
            
            # Memoria semántica
            semantic_memory = context.get('semantic_memory', {})
            concepts = semantic_memory.get('concepts', [])
            facts = semantic_memory.get('facts', [])
            if concepts or facts:
                synthesis_parts.append(f"Conocimiento relacionado: {len(concepts)} conceptos, {len(facts)} hechos")
            
            # Memoria procedimental
            procedural_memory = context.get('procedural_memory', [])
            if procedural_memory:
                avg_effectiveness = sum(p.get('effectiveness_score', 0) for p in procedural_memory) / len(procedural_memory)
                synthesis_parts.append(f"Procedimientos aplicables: {len(procedural_memory)} con efectividad promedio {avg_effectiveness:.2f}")
            
            if synthesis_parts:
                return "Contexto sintetizado: " + " | ".join(synthesis_parts)
            else:
                return "No se encontró contexto relevante previo"
                
        except Exception as e:
            logger.error(f"Error sintetizando contexto: {e}")
            return f"Error en síntesis: {str(e)}"
    
    async def export_memory_data(self, export_format: str = 'json', 
                                include_compressed: bool = False, 
                                output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Exporta datos de memoria para respaldo o análisis
        
        Args:
            export_format: Formato de exportación ('json', 'csv', 'xml')
            include_compressed: Si incluir datos comprimidos
            output_file: Archivo de salida (opcional)
            
        Returns:
            Diccionario con datos exportados y estadísticas
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            export_stats = {
                'started_at': datetime.now().isoformat(),
                'export_format': export_format,
                'include_compressed': include_compressed,
                'output_file': output_file,
                'exported_episodes': 0,
                'exported_concepts': 0,
                'exported_facts': 0,
                'exported_procedures': 0,
                'export_size': 0,
                'success': False
            }
            
            # Preparar datos para exportación
            export_data = {
                'metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'system_version': '2.0.0',
                    'export_format': export_format,
                    'memory_manager_config': self.config
                },
                'working_memory': {},
                'episodic_memory': [],
                'semantic_memory': {
                    'concepts': [],
                    'facts': []
                },
                'procedural_memory': {
                    'procedures': [],
                    'tool_strategies': []
                },
                'statistics': {}
            }
            
            # 1. Exportar memoria de trabajo
            working_contexts = []
            for context_id, context_data in self.working_memory.store.items():
                working_contexts.append({
                    'id': context_id,
                    'data': context_data,
                    'timestamp': context_data.get('timestamp', datetime.now().isoformat())
                })
            export_data['working_memory'] = working_contexts
            
            # 2. Exportar memoria episódica
            for episode_id, episode in self.episodic_memory.episodes.items():
                # Filtrar episodios comprimidos si no se incluyen
                if not include_compressed and episode.context.get('compressed', False):
                    continue
                
                episode_data = {
                    'id': episode.id,
                    'title': episode.title,
                    'description': episode.description,
                    'context': episode.context,
                    'actions': episode.actions,
                    'outcomes': episode.outcomes,
                    'timestamp': episode.timestamp.isoformat(),
                    'duration': episode.duration.total_seconds() if episode.duration else 0,
                    'success': episode.success,
                    'importance': episode.importance,
                    'tags': episode.tags
                }
                export_data['episodic_memory'].append(episode_data)
                export_stats['exported_episodes'] += 1
            
            # 3. Exportar memoria semántica
            for concept_id, concept in self.semantic_memory.concepts.items():
                # Filtrar conceptos comprimidos si no se incluyen
                if not include_compressed and concept.attributes.get('compressed', False):
                    continue
                
                concept_data = {
                    'id': concept.id,
                    'name': concept.name,
                    'description': concept.description,
                    'category': concept.category,
                    'attributes': concept.attributes,
                    'relations': concept.relations,
                    'confidence': concept.confidence,
                    'created_at': getattr(concept, 'created_at', datetime.now()).isoformat() if hasattr(concept, 'created_at') else datetime.now().isoformat(),
                    'usage_count': getattr(concept, 'usage_count', 0)
                }
                export_data['semantic_memory']['concepts'].append(concept_data)
                export_stats['exported_concepts'] += 1
            
            for fact_id, fact in self.semantic_memory.facts.items():
                # Filtrar hechos comprimidos si no se incluyen
                if not include_compressed and fact.context.get('compressed', False):
                    continue
                
                fact_data = {
                    'id': fact.id,
                    'subject': fact.subject,
                    'predicate': fact.predicate,
                    'object': fact.object,
                    'context': fact.context,
                    'confidence': fact.confidence,
                    'source': fact.source,
                    'created_at': getattr(fact, 'created_at', datetime.now()).isoformat() if hasattr(fact, 'created_at') else datetime.now().isoformat(),
                    'validated': getattr(fact, 'validated', False)
                }
                export_data['semantic_memory']['facts'].append(fact_data)
                export_stats['exported_facts'] += 1
            
            # 4. Exportar memoria procedimental
            for procedure_id, procedure in self.procedural_memory.procedures.items():
                procedure_data = {
                    'id': procedure.id,
                    'name': procedure.name,
                    'description': procedure.description,
                    'steps': procedure.steps,
                    'success_rate': procedure.success_rate,
                    'effectiveness_score': procedure.effectiveness_score,
                    'usage_count': procedure.usage_count,
                    'created_at': procedure.created_at.isoformat() if hasattr(procedure, 'created_at') else datetime.now().isoformat(),
                    'last_used': procedure.last_used.isoformat() if hasattr(procedure, 'last_used') and procedure.last_used else None,
                    'conditions': procedure.context_conditions
                }
                export_data['procedural_memory']['procedures'].append(procedure_data)
                export_stats['exported_procedures'] += 1
            
            for strategy_id, strategy in self.procedural_memory.tool_strategies.items():
                strategy_data = {
                    'id': strategy.id,
                    'tool_name': strategy.tool_name,
                    'parameters': strategy.parameters,
                    'success_rate': strategy.success_rate,
                    'avg_execution_time': strategy.avg_execution_time,
                    'usage_count': strategy.usage_count,
                    'created_at': strategy.created_at.isoformat() if hasattr(strategy, 'created_at') else datetime.now().isoformat(),
                    'last_used': strategy.last_used.isoformat() if hasattr(strategy, 'last_used') and strategy.last_used else None
                }
                export_data['procedural_memory']['tool_strategies'].append(strategy_data)
            
            # 5. Agregar estadísticas del sistema
            export_data['statistics'] = await self.get_memory_stats()
            
            # 6. Convertir a formato solicitado
            if export_format.lower() == 'json':
                import json
                formatted_data = json.dumps(export_data, indent=2, ensure_ascii=False, default=self._json_serializer)
            elif export_format.lower() == 'csv':
                formatted_data = self._export_to_csv(export_data)
            elif export_format.lower() == 'xml':
                formatted_data = self._export_to_xml(export_data)
            else:
                formatted_data = str(export_data)
            
            # 7. Guardar en archivo si se especifica
            if output_file:
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(formatted_data)
                    logger.info(f"Datos de memoria exportados a {output_file}")
                except Exception as e:
                    logger.error(f"Error escribiendo archivo de exportación: {e}")
                    export_stats['file_error'] = str(e)
            
            # 8. Calcular tamaño de exportación
            export_stats['export_size'] = len(formatted_data.encode('utf-8'))
            export_stats['success'] = True
            export_stats['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Exportación de memoria completada: {export_stats['exported_episodes']} episodios, {export_stats['exported_concepts']} conceptos, {export_stats['exported_facts']} hechos, {export_stats['exported_procedures']} procedimientos")
            
            return {
                'export_stats': export_stats,
                'data': export_data if not output_file else None,
                'formatted_data': formatted_data if not output_file else None,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error exportando datos de memoria: {e}")
            export_stats['success'] = False
            export_stats['error'] = str(e)
            export_stats['completed_at'] = datetime.now().isoformat()
            return {
                'export_stats': export_stats,
                'error': str(e),
                'success': False
            }
    
    def _export_to_csv(self, data: Dict[str, Any]) -> str:
        """
        Convierte datos de memoria a formato CSV
        
        Args:
            data: Datos a convertir
            
        Returns:
            String en formato CSV
        """
        try:
            import io
            import csv
            
            output = io.StringIO()
            
            # Exportar episodios
            if data['episodic_memory']:
                output.write("=== EPISODIC MEMORY ===\n")
                writer = csv.writer(output)
                writer.writerow(['ID', 'Title', 'Description', 'Success', 'Importance', 'Timestamp', 'Tags'])
                
                for episode in data['episodic_memory']:
                    writer.writerow([
                        episode['id'],
                        episode['title'],
                        episode['description'][:100] + '...' if len(episode['description']) > 100 else episode['description'],
                        episode['success'],
                        episode['importance'],
                        episode['timestamp'],
                        ', '.join(episode['tags'])
                    ])
                output.write("\n")
            
            # Exportar conceptos
            if data['semantic_memory']['concepts']:
                output.write("=== SEMANTIC CONCEPTS ===\n")
                writer = csv.writer(output)
                writer.writerow(['ID', 'Name', 'Description', 'Category', 'Confidence'])
                
                for concept in data['semantic_memory']['concepts']:
                    writer.writerow([
                        concept['id'],
                        concept['name'],
                        concept['description'][:100] + '...' if len(concept['description']) > 100 else concept['description'],
                        concept['category'],
                        concept['confidence']
                    ])
                output.write("\n")
            
            # Exportar hechos
            if data['semantic_memory']['facts']:
                output.write("=== SEMANTIC FACTS ===\n")
                writer = csv.writer(output)
                writer.writerow(['ID', 'Subject', 'Predicate', 'Object', 'Confidence', 'Source'])
                
                for fact in data['semantic_memory']['facts']:
                    writer.writerow([
                        fact['id'],
                        fact['subject'],
                        fact['predicate'],
                        fact['object'],
                        fact['confidence'],
                        fact['source']
                    ])
                output.write("\n")
            
            # Exportar procedimientos
            if data['procedural_memory']['procedures']:
                output.write("=== PROCEDURAL MEMORY ===\n")
                writer = csv.writer(output)
                writer.writerow(['ID', 'Name', 'Description', 'Success Rate', 'Effectiveness', 'Usage Count'])
                
                for procedure in data['procedural_memory']['procedures']:
                    writer.writerow([
                        procedure['id'],
                        procedure['name'],
                        procedure['description'][:100] + '...' if len(procedure['description']) > 100 else procedure['description'],
                        procedure['success_rate'],
                        procedure['effectiveness_score'],
                        procedure['usage_count']
                    ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting to CSV: {e}")
            return f"Error generating CSV: {str(e)}"
    
    def _export_to_xml(self, data: Dict[str, Any]) -> str:
        """
        Convierte datos de memoria a formato XML
        
        Args:
            data: Datos a convertir
            
        Returns:
            String en formato XML
        """
        try:
            import xml.etree.ElementTree as ET
            from xml.dom import minidom
            
            # Crear elemento raíz
            root = ET.Element('memory_export')
            
            # Agregar metadata
            metadata = ET.SubElement(root, 'metadata')
            for key, value in data['metadata'].items():
                meta_elem = ET.SubElement(metadata, key)
                meta_elem.text = str(value)
            
            # Agregar memoria episódica
            episodic = ET.SubElement(root, 'episodic_memory')
            for episode in data['episodic_memory']:
                ep_elem = ET.SubElement(episodic, 'episode')
                ep_elem.set('id', episode['id'])
                
                for key, value in episode.items():
                    if key != 'id':
                        elem = ET.SubElement(ep_elem, key)
                        if isinstance(value, list):
                            elem.text = ', '.join(str(v) for v in value)
                        else:
                            elem.text = str(value)
            
            # Agregar memoria semántica
            semantic = ET.SubElement(root, 'semantic_memory')
            
            # Conceptos
            concepts = ET.SubElement(semantic, 'concepts')
            for concept in data['semantic_memory']['concepts']:
                c_elem = ET.SubElement(concepts, 'concept')
                c_elem.set('id', concept['id'])
                
                for key, value in concept.items():
                    if key != 'id':
                        elem = ET.SubElement(c_elem, key)
                        if isinstance(value, (dict, list)):
                            elem.text = str(value)
                        else:
                            elem.text = str(value)
            
            # Hechos
            facts = ET.SubElement(semantic, 'facts')
            for fact in data['semantic_memory']['facts']:
                f_elem = ET.SubElement(facts, 'fact')
                f_elem.set('id', fact['id'])
                
                for key, value in fact.items():
                    if key != 'id':
                        elem = ET.SubElement(f_elem, key)
                        if isinstance(value, (dict, list)):
                            elem.text = str(value)
                        else:
                            elem.text = str(value)
            
            # Agregar memoria procedimental
            procedural = ET.SubElement(root, 'procedural_memory')
            
            # Procedimientos
            procedures = ET.SubElement(procedural, 'procedures')
            for procedure in data['procedural_memory']['procedures']:
                p_elem = ET.SubElement(procedures, 'procedure')
                p_elem.set('id', procedure['id'])
                
                for key, value in procedure.items():
                    if key != 'id':
                        elem = ET.SubElement(p_elem, key)
                        if isinstance(value, (dict, list)):
                            elem.text = str(value)
                        else:
                            elem.text = str(value)
            
            # Formatear XML
            rough_string = ET.tostring(root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
            
        except Exception as e:
            logger.error(f"Error converting to XML: {e}")
            return f"<error>Error generating XML: {str(e)}</error>"
    
    async def compress_old_memory(self, compression_threshold_days: int = 30, 
                                 compression_ratio: float = 0.5) -> Dict[str, Any]:
        """
        Comprime memoria antigua para optimizar el almacenamiento
        
        Args:
            compression_threshold_days: Días después de los cuales comprimir memoria
            compression_ratio: Ratio de compresión (0.0 a 1.0)
            
        Returns:
            Diccionario con estadísticas de compresión
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            compression_stats = {
                'started_at': datetime.now().isoformat(),
                'threshold_days': compression_threshold_days,
                'compression_ratio': compression_ratio,
                'compressed_episodes': 0,
                'compressed_concepts': 0,
                'compressed_facts': 0,
                'compressed_procedures': 0,
                'space_saved': 0
            }
            
            # Calcular fecha umbral
            threshold_date = datetime.now() - timedelta(days=compression_threshold_days)
            
            # 1. Comprimir episodios antiguos
            all_episodes = [ep for ep in self.episodic_memory.episodes.values() if ep.timestamp < threshold_date]
            for episode in all_episodes:
                if episode.importance < 4:  # Solo comprimir episodios de baja importancia
                    # Comprimir descripción y contexto
                    original_size = len(str(episode.description)) + len(str(episode.context))
                    
                    # Comprimir manteniendo información esencial
                    compressed_description = episode.description[:int(len(episode.description) * compression_ratio)]
                    compressed_context = {
                        'task_type': episode.context.get('task_type', 'unknown'),
                        'success': episode.context.get('success', False),
                        'compressed': True,
                        'original_timestamp': episode.timestamp.isoformat()
                    }
                    
                    # Actualizar episodio
                    episode.description = compressed_description
                    episode.context = compressed_context
                    
                    # Reducir número de acciones y outcomes
                    if len(episode.actions) > 3:
                        episode.actions = episode.actions[:3]
                    if len(episode.outcomes) > 3:
                        episode.outcomes = episode.outcomes[:3]
                    
                    compressed_size = len(str(episode.description)) + len(str(episode.context))
                    compression_stats['space_saved'] += (original_size - compressed_size)
                    compression_stats['compressed_episodes'] += 1
            
            # 2. Comprimir conceptos semánticos antiguos
            all_concepts = [concept for concept in self.semantic_memory.concepts.values() 
                          if hasattr(concept, 'created_at') and concept.created_at < threshold_date]
            for concept in all_concepts:
                if concept.confidence < 0.7:  # Solo comprimir conceptos de baja confianza
                    # Comprimir descripción y atributos
                    original_size = len(str(concept.description)) + len(str(concept.attributes))
                    
                    concept.description = concept.description[:int(len(concept.description) * compression_ratio)]
                    # Mantener solo atributos esenciales
                    essential_attrs = ['type', 'category', 'importance']
                    concept.attributes = {k: v for k, v in concept.attributes.items() if k in essential_attrs}
                    
                    compressed_size = len(str(concept.description)) + len(str(concept.attributes))
                    compression_stats['space_saved'] += (original_size - compressed_size)
                    compression_stats['compressed_concepts'] += 1
            
            # 3. Comprimir hechos semánticos antiguos
            all_facts = [fact for fact in self.semantic_memory.facts.values() 
                        if hasattr(fact, 'created_at') and fact.created_at < threshold_date]
            for fact in all_facts:
                if fact.confidence < 0.6:  # Solo comprimir hechos de baja confianza
                    # Comprimir contexto
                    original_size = len(str(fact.context))
                    
                    fact.context = {
                        'compressed': True,
                        'original_confidence': fact.confidence,
                        'compressed_at': datetime.now().isoformat()
                    }
                    
                    compressed_size = len(str(fact.context))
                    compression_stats['space_saved'] += (original_size - compressed_size)
                    compression_stats['compressed_facts'] += 1
            
            # 4. Comprimir procedimientos antiguos
            all_procedures = [proc for proc in self.procedural_memory.procedures.values() 
                            if hasattr(proc, 'created_at') and proc.created_at < threshold_date]
            for procedure in all_procedures:
                if procedure.effectiveness_score < 0.5:  # Solo comprimir procedimientos poco efectivos
                    # Comprimir pasos
                    original_size = len(str(procedure.steps))
                    
                    if len(procedure.steps) > 5:
                        procedure.steps = procedure.steps[:5]  # Mantener solo primeros 5 pasos
                    
                    compressed_size = len(str(procedure.steps))
                    compression_stats['space_saved'] += (original_size - compressed_size)
                    compression_stats['compressed_procedures'] += 1
            
            # 5. Limpiar memoria de trabajo antigua
            # Use the existing cleanup method
            self.working_memory._cleanup_expired()
            
            compression_stats['completed_at'] = datetime.now().isoformat()
            compression_stats['total_space_saved_kb'] = compression_stats['space_saved'] / 1024
            
            logger.info(f"Compresión de memoria completada: {compression_stats}")
            
            return compression_stats
            
        except Exception as e:
            logger.error(f"Error comprimiendo memoria antigua: {e}")
            return {
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            }
    
    def _json_serializer(self, obj):
        """
        JSON serializer para objetos no serializables por defecto
        
        Args:
            obj: Objeto a serializar
            
        Returns:
            String serializable o None
        """
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '__str__'):
            return str(obj)
        return None
    
    def get_task_state(self, task_id: str) -> Dict[str, Any]:
        """
        🚨 PASO 3: CREAR EL CANAL DE COMUNICACIÓN - get_task_state function
        Obtiene el estado actual de una tarea específica
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Diccionario con el estado de la tarea
        """
        try:
            # 🚨 LOGGING AGRESIVO EN GET_TASK_STATE
            print(f"🔍 get_task_state called for task_id: {task_id}")
            
            # Importar las funciones necesarias
            from ..routes.agent_routes import get_task_data, active_task_plans
            
            # Intentar obtener datos de la tarea
            task_data = get_task_data(task_id)
            print(f"🔍 Task data from get_task_data: {task_data is not None}")
            
            if not task_data:
                # Fallback a active_task_plans
                print(f"🔍 Checking active_task_plans for task_id: {task_id}")
                if task_id in active_task_plans:
                    task_data = active_task_plans[task_id]
                    print(f"✅ Found task in active_task_plans")
                else:
                    print(f"❌ Task {task_id} not found anywhere")
                    return {
                        'task_id': task_id,
                        'status': 'not_found',
                        'message': f'Task {task_id} not found',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Extraer información del estado
            plan_steps = task_data.get('plan', [])
            current_step = task_data.get('current_step', 0)
            completed_steps = [step for step in plan_steps if step.get('status') == 'completed']
            failed_steps = [step for step in plan_steps if step.get('status') == 'failed']
            in_progress_steps = [step for step in plan_steps if step.get('status') == 'in-progress']
            
            # Calcular progreso
            total_steps = len(plan_steps)
            completed_count = len(completed_steps)
            progress_percentage = (completed_count / total_steps * 100) if total_steps > 0 else 0
            
            # Determinar estado general
            if len(failed_steps) > 0:
                overall_status = 'failed'
            elif len(in_progress_steps) > 0:
                overall_status = 'running'
            elif completed_count == total_steps and total_steps > 0:
                overall_status = 'completed'
            elif total_steps > 0:
                overall_status = 'pending'
            else:
                overall_status = 'initialized'
            
            task_state = {
                'task_id': task_id,
                'status': overall_status,
                'progress': {
                    'total_steps': total_steps,
                    'completed_steps': completed_count,
                    'failed_steps': len(failed_steps),
                    'in_progress_steps': len(in_progress_steps),
                    'percentage': round(progress_percentage, 2)
                },
                'current_step': current_step,
                'steps': plan_steps,
                'metadata': {
                    'created_at': task_data.get('created_at', datetime.now().isoformat()),
                    'last_updated': task_data.get('last_updated', datetime.now().isoformat()),
                    'title': task_data.get('title', f'Task {task_id}'),
                    'description': task_data.get('description', 'No description available')
                },
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Task state generated successfully: {overall_status}, {progress_percentage}% complete")
            return task_state
            
        except Exception as e:
            logger.error(f"Error getting task state for {task_id}: {e}")
            print(f"❌ Error in get_task_state: {str(e)}")
            return {
                'task_id': task_id,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
