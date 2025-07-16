"""
Gestor avanzado de memoria para el agente autónomo
Integra múltiples tipos de memoria y proporciona interfaz unificada
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .working_memory_store import WorkingMemoryStore
from .episodic_memory_store import EpisodicMemoryStore, Episode
from .semantic_memory_store import SemanticMemoryStore, SemanticConcept, SemanticFact
from .procedural_memory_store import ProceduralMemoryStore, Procedure, ToolStrategy
from .semantic_indexer import SemanticIndexer
from .embedding_service import EmbeddingService

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
        
        Args:
            experience: Diccionario con datos de la experiencia
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            # Extraer información de la experiencia
            task_context = experience.get('context', {})
            execution_steps = experience.get('execution_steps', [])
            outcomes = experience.get('outcomes', [])
            success = experience.get('success', False)
            execution_time = experience.get('execution_time', 0)
            
            # 1. Almacenar en memoria de trabajo (contexto inmediato)
            context_id = f"ctx_{datetime.now().timestamp()}"
            self.working_memory.store_context(context_id, {
                'task_context': task_context,
                'execution_summary': {
                    'steps_count': len(execution_steps),
                    'success': success,
                    'execution_time': execution_time
                },
                'timestamp': datetime.now().isoformat()
            })
            
            # 2. Almacenar en memoria episódica
            episode_id = f"ep_{datetime.now().timestamp()}"
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