"""
Almacén de memoria episódica
Gestiona experiencias específicas y eventos temporales
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
@dataclass
class Episode:
    """Representa un episodio en memoria"""
    id: str
    title: str
    description: str
    context: Dict[str, Any]
    actions: List[Dict[str, Any]]
    outcomes: List[Dict[str, Any]]
    timestamp: datetime
    duration: Optional[timedelta] = None
    success: bool = True
    tags: List[str] = None
    importance: int = 3  # 1-5 scale
    
    # Campos adicionales para compatibilidad con rutas
    user_query: str = None
    agent_response: str = None
    tools_used: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.tools_used is None:
            self.tools_used = []
        if self.metadata is None:
            self.metadata = {}
        
        # Auto-generar ID si no se proporciona
        if not self.id:
            self.id = f"ep_{datetime.now().timestamp()}"
            
        # Auto-generar timestamp si no se proporciona
        if not self.timestamp:
            self.timestamp = datetime.now()
    
    @classmethod
    def from_chat_interaction(cls, user_query: str, agent_response: str, 
                             success: bool, context: Dict[str, Any] = None, 
                             tools_used: List[str] = None, importance: float = 0.5, 
                             metadata: Dict[str, Any] = None):
        """
        Crear Episode desde interacción de chat
        
        Args:
            user_query: Consulta del usuario
            agent_response: Respuesta del agente
            success: Si la interacción fue exitosa
            context: Contexto adicional
            tools_used: Herramientas utilizadas
            importance: Importancia (0.0-1.0), se convertirá a escala 1-5
            metadata: Metadatos adicionales
        
        Returns:
            Episode: Nuevo episodio creado
        """
        episode_id = f"ep_{datetime.now().timestamp()}"
        
        # Convertir importancia de 0.0-1.0 a escala 1-5
        importance_scale = max(1, min(5, int(importance * 5)))
        
        return cls(
            id=episode_id,
            title=f"Chat: {user_query[:50]}..." if len(user_query) > 50 else f"Chat: {user_query}",
            description=f"Interacción de chat entre usuario y agente",
            context=context or {},
            actions=[{
                'type': 'user_query',
                'content': user_query,
                'timestamp': datetime.now().isoformat()
            }],
            outcomes=[{
                'type': 'agent_response',
                'content': agent_response,
                'success': success,
                'timestamp': datetime.now().isoformat()
            }],
            timestamp=datetime.now(),
            success=success,
            tags=['chat', 'user_interaction'],
            importance=importance_scale,
            user_query=user_query,
            agent_response=agent_response,
            tools_used=tools_used or [],
            metadata=metadata or {}
        )

class EpisodicMemoryStore:
    """Almacén de memoria episódica para experiencias y eventos"""
    
    def __init__(self, max_episodes: int = 1000):
        """
        Inicializa el almacén de memoria episódica
        
        Args:
            max_episodes: Número máximo de episodios a mantener
        """
        self.max_episodes = max_episodes
        self.episodes: Dict[str, Episode] = {}
        self.episode_order: List[str] = []  # Orden cronológico
        
    def store_episode(self, episode: Episode):
        """
        Almacena un episodio en memoria
        
        Args:
            episode: Episodio a almacenar
        """
        try:
            # Aplicar límite de capacidad
            if len(self.episodes) >= self.max_episodes:
                # Eliminar el episodio más antiguo con menor importancia
                oldest_id = self._find_least_important_episode()
                if oldest_id:
                    self._remove_episode(oldest_id)
            
            # Almacenar episodio
            self.episodes[episode.id] = episode
            self.episode_order.append(episode.id)
            
            logger.debug(f"Episodio {episode.id} almacenado en memoria episódica")
            
        except Exception as e:
            logger.error(f"Error almacenando episodio {episode.id}: {e}")
    
    def retrieve_episode(self, episode_id: str) -> Optional[Episode]:
        """
        Recupera un episodio específico
        
        Args:
            episode_id: ID del episodio
            
        Returns:
            Episodio o None si no existe
        """
        return self.episodes.get(episode_id)
    
    def get_recent_episodes(self, limit: int = 10) -> List[Episode]:
        """
        Obtiene episodios recientes
        
        Args:
            limit: Número máximo de episodios
            
        Returns:
            Lista de episodios recientes
        """
        try:
            recent_ids = self.episode_order[-limit:]
            return [self.episodes[ep_id] for ep_id in reversed(recent_ids) if ep_id in self.episodes]
            
        except Exception as e:
            logger.error(f"Error obteniendo episodios recientes: {e}")
            return []
    
    def search_episodes(self, query: str, limit: int = 10, task_id: Optional[str] = None) -> List[Episode]:
        """
        Busca episodios por contenido
        UPGRADE AI: Modificado para soportar filtrado por task_id
        
        Args:
            query: Consulta de búsqueda
            limit: Número máximo de resultados  
            task_id: ID de tarea para filtrar resultados (opcional)
            
        Returns:
            Lista de episodios coincidentes
        """
        try:
            results = []
            query_lower = query.lower()
            
            for episode in self.episodes.values():
                # UPGRADE AI: Filtrar por task_id si se proporciona
                if task_id is not None:
                    episode_task_id = episode.context.get('task_id') if hasattr(episode, 'context') else None
                    if episode_task_id != task_id:
                        continue
                
                # Buscar en título, descripción y tags
                if (query_lower in episode.title.lower() or 
                    query_lower in episode.description.lower() or
                    any(query_lower in tag.lower() for tag in episode.tags)):
                    results.append(episode)
                    
                    if len(results) >= limit:
                        break
            
            # Ordenar por importancia y fecha
            results.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error buscando episodios: {e}")
            return []
    
    def find_similar_episodes(self, context: Dict[str, Any], limit: int = 5) -> List[Episode]:
        """
        Encuentra episodios similares basados en contexto
        
        Args:
            context: Contexto de referencia
            limit: Número máximo de resultados
            
        Returns:
            Lista de episodios similares
        """
        try:
            scored_episodes = []
            
            for episode in self.episodes.values():
                similarity_score = self._calculate_context_similarity(context, episode.context)
                
                if similarity_score > 0.3:  # Umbral de similitud
                    scored_episodes.append((episode, similarity_score))
            
            # Ordenar por similitud
            scored_episodes.sort(key=lambda x: x[1], reverse=True)
            
            return [episode for episode, _ in scored_episodes[:limit]]
            
        except Exception as e:
            logger.error(f"Error encontrando episodios similares: {e}")
            return []
    
    def get_successful_episodes(self, context_keywords: List[str] = None, limit: int = 10) -> List[Episode]:
        """
        Obtiene episodios exitosos, opcionalmente filtrados por contexto
        
        Args:
            context_keywords: Palabras clave del contexto
            limit: Número máximo de resultados
            
        Returns:
            Lista de episodios exitosos
        """
        try:
            successful_episodes = [ep for ep in self.episodes.values() if ep.success]
            
            if context_keywords:
                filtered_episodes = []
                for episode in successful_episodes:
                    context_str = json.dumps(episode.context).lower()
                    if any(keyword.lower() in context_str for keyword in context_keywords):
                        filtered_episodes.append(episode)
                successful_episodes = filtered_episodes
            
            # Ordenar por importancia y fecha
            successful_episodes.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
            
            return successful_episodes[:limit]
            
        except Exception as e:
            logger.error(f"Error obteniendo episodios exitosos: {e}")
            return []
    
    def get_failure_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Analiza patrones de fallo para aprendizaje
        
        Args:
            limit: Número máximo de patrones
            
        Returns:
            Lista de patrones de fallo
        """
        try:
            failed_episodes = [ep for ep in self.episodes.values() if not ep.success]
            
            # Agrupar por patrones comunes
            failure_patterns = {}
            
            for episode in failed_episodes:
                # Extraer características del contexto
                context_keys = set(episode.context.keys())
                actions_taken = [action.get('type', 'unknown') for action in episode.actions]
                
                pattern_key = f"{sorted(context_keys)}_{sorted(actions_taken)}"
                
                if pattern_key not in failure_patterns:
                    failure_patterns[pattern_key] = {
                        'pattern': {
                            'context_keys': list(context_keys),
                            'actions': actions_taken
                        },
                        'episodes': [],
                        'frequency': 0
                    }
                
                failure_patterns[pattern_key]['episodes'].append(episode)
                failure_patterns[pattern_key]['frequency'] += 1
            
            # Ordenar por frecuencia
            sorted_patterns = sorted(
                failure_patterns.values(),
                key=lambda x: x['frequency'],
                reverse=True
            )
            
            return sorted_patterns[:limit]
            
        except Exception as e:
            logger.error(f"Error analizando patrones de fallo: {e}")
            return []
    
    def clear_old_episodes(self, days_old: int = 30):
        """
        Limpia episodios antiguos
        
        Args:
            days_old: Días de antigüedad para limpieza
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            episodes_to_remove = []
            
            for episode_id, episode in self.episodes.items():
                if episode.timestamp < cutoff_date and episode.importance < 4:
                    episodes_to_remove.append(episode_id)
            
            for episode_id in episodes_to_remove:
                self._remove_episode(episode_id)
                
            logger.info(f"Eliminados {len(episodes_to_remove)} episodios antiguos")
            
        except Exception as e:
            logger.error(f"Error limpiando episodios antiguos: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la memoria episódica
        
        Returns:
            Diccionario con estadísticas
        """
        total_episodes = len(self.episodes)
        successful_episodes = sum(1 for ep in self.episodes.values() if ep.success)
        
        if total_episodes > 0:
            success_rate = successful_episodes / total_episodes
            avg_importance = sum(ep.importance for ep in self.episodes.values()) / total_episodes
        else:
            success_rate = 0
            avg_importance = 0
        
        return {
            'total_episodes': total_episodes,
            'successful_episodes': successful_episodes,
            'failed_episodes': total_episodes - successful_episodes,
            'success_rate': success_rate,
            'average_importance': avg_importance,
            'oldest_episode': min(
                (ep.timestamp for ep in self.episodes.values()),
                default=None
            ),
            'newest_episode': max(
                (ep.timestamp for ep in self.episodes.values()),
                default=None
            )
        }
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """
        Calcula similitud entre contextos
        
        Args:
            context1: Primer contexto
            context2: Segundo contexto
            
        Returns:
            Score de similitud (0-1)
        """
        try:
            # Similitud simple basada en claves comunes
            keys1 = set(context1.keys())
            keys2 = set(context2.keys())
            
            if not keys1 or not keys2:
                return 0.0
            
            common_keys = keys1.intersection(keys2)
            total_keys = keys1.union(keys2)
            
            key_similarity = len(common_keys) / len(total_keys)
            
            # Similitud de valores para claves comunes
            value_similarity = 0.0
            if common_keys:
                value_matches = 0
                for key in common_keys:
                    if str(context1[key]).lower() == str(context2[key]).lower():
                        value_matches += 1
                value_similarity = value_matches / len(common_keys)
            
            # Combinar similitudes
            return (key_similarity + value_similarity) / 2
            
        except Exception as e:
            logger.error(f"Error calculando similitud de contexto: {e}")
            return 0.0
    
    def _find_least_important_episode(self) -> Optional[str]:
        """
        Encuentra el episodio menos importante para eliminar
        
        Returns:
            ID del episodio menos importante
        """
        if not self.episodes:
            return None
            
        # Encontrar el episodio con menor importancia y más antiguo
        least_important = min(
            self.episodes.items(),
            key=lambda x: (x[1].importance, x[1].timestamp)
        )
        
        return least_important[0]
    
    def _remove_episode(self, episode_id: str):
        """
        Elimina un episodio específico
        
        Args:
            episode_id: ID del episodio a eliminar
        """
        if episode_id in self.episodes:
            del self.episodes[episode_id]
            
        if episode_id in self.episode_order:
            self.episode_order.remove(episode_id)