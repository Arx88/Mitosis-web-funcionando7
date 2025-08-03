"""
Almacén de memoria de trabajo
Gestiona el contexto inmediato de la conversación
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class WorkingMemoryStore:
    """Almacén de memoria de trabajo para contexto inmediato"""
    
    def __init__(self, max_capacity: int = 50, ttl_minutes: int = 60):
        """
        Inicializa el almacén de memoria de trabajo
        
        Args:
            max_capacity: Capacidad máxima de elementos
            ttl_minutes: Tiempo de vida en minutos
        """
        self.max_capacity = max_capacity
        self.ttl_minutes = ttl_minutes
        self.store: Dict[str, Dict[str, Any]] = {}
        self.access_order: List[str] = []  # Para LRU
        
    def store_context(self, context_id: str, context_data: Dict[str, Any]):
        """
        Almacena contexto en memoria de trabajo
        
        Args:
            context_id: ID único del contexto
            context_data: Datos del contexto
        """
        try:
            # Limpiar contextos expirados
            self._cleanup_expired()
            
            # Si ya existe, actualizar orden de acceso
            if context_id in self.store:
                self.access_order.remove(context_id)
            
            # Aplicar límite de capacidad (LRU)
            if len(self.store) >= self.max_capacity:
                oldest_id = self.access_order.pop(0)
                del self.store[oldest_id]
            
            # Almacenar contexto
            self.store[context_id] = {
                'data': context_data,
                'created_at': datetime.now(),
                'last_accessed': datetime.now(),
                'access_count': 1
            }
            
            # Actualizar orden de acceso
            self.access_order.append(context_id)
            
            logger.debug(f"Contexto {context_id} almacenado en memoria de trabajo")
            
        except Exception as e:
            logger.error(f"Error almacenando contexto {context_id}: {e}")
    
    def retrieve_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera contexto de memoria de trabajo
        
        Args:
            context_id: ID del contexto
            
        Returns:
            Datos del contexto o None si no existe
        """
        try:
            if context_id not in self.store:
                return None
                
            context_entry = self.store[context_id]
            
            # Verificar si ha expirado
            if self._is_expired(context_entry):
                self._remove_context(context_id)
                return None
            
            # Actualizar estadísticas de acceso
            context_entry['last_accessed'] = datetime.now()
            context_entry['access_count'] += 1
            
            # Actualizar orden LRU
            self.access_order.remove(context_id)
            self.access_order.append(context_id)
            
            return context_entry['data']
            
        except Exception as e:
            logger.error(f"Error recuperando contexto {context_id}: {e}")
            return None
    
    def get_recent_contexts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los contextos más recientes
        
        Args:
            limit: Número máximo de contextos
            
        Returns:
            Lista de contextos recientes
        """
        try:
            # Limpiar expirados
            self._cleanup_expired()
            
            # Ordenar por último acceso
            recent_ids = self.access_order[-limit:]
            recent_contexts = []
            
            for context_id in reversed(recent_ids):
                if context_id in self.store:
                    context_data = self.store[context_id]
                    recent_contexts.append({
                        'id': context_id,
                        'data': context_data['data'],
                        'created_at': context_data['created_at'],
                        'last_accessed': context_data['last_accessed'],
                        'access_count': context_data['access_count']
                    })
            
            return recent_contexts
            
        except Exception as e:
            logger.error(f"Error obteniendo contextos recientes: {e}")
            return []
    
    def search_contexts(self, query: str, limit: int = 5, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Busca contextos por contenido
        UPGRADE AI: Modificado para soportar filtrado por task_id
        
        Args:
            query: Consulta de búsqueda
            limit: Número máximo de resultados
            task_id: ID de tarea para filtrar resultados (opcional)
            
        Returns:
            Lista de contextos coincidentes
        """
        try:
            self._cleanup_expired()
            
            results = []
            query_lower = query.lower()
            
            for context_id, context_entry in self.store.items():
                # UPGRADE AI: Filtrar por task_id si se proporciona
                if task_id is not None:
                    entry_task_id = context_entry['data'].get('task_id')
                    if entry_task_id != task_id:
                        continue
                
                # Búsqueda simple en contenido
                content_str = json.dumps(context_entry['data']).lower()
                
                if query_lower in content_str:
                    results.append({
                        'id': context_id,
                        'data': context_entry['data'],
                        'created_at': context_entry['created_at'],
                        'last_accessed': context_entry['last_accessed'],
                        'access_count': context_entry['access_count'],
                        'task_id': context_entry['data'].get('task_id', 'unknown')  # UPGRADE AI: Incluir task_id en respuesta
                    })
                    
                    if len(results) >= limit:
                        break
            
            # Ordenar por relevancia (acceso reciente)
            results.sort(key=lambda x: x['last_accessed'], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error buscando contextos: {e}")
            return []
    
    def clear_expired(self):
        """Limpia contextos expirados"""
        self._cleanup_expired()
    
    def clear_all(self):
        """Limpia toda la memoria de trabajo"""
        self.store.clear()
        self.access_order.clear()
        logger.info("Memoria de trabajo limpiada")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la memoria de trabajo
        
        Returns:
            Diccionario con estadísticas
        """
        self._cleanup_expired()
        
        total_contexts = len(self.store)
        total_accesses = sum(entry['access_count'] for entry in self.store.values())
        
        return {
            'total_contexts': total_contexts,
            'capacity_used': f"{total_contexts}/{self.max_capacity}",
            'total_accesses': total_accesses,
            'ttl_minutes': self.ttl_minutes,
            'oldest_context': min(
                (entry['created_at'] for entry in self.store.values()),
                default=None
            ),
            'newest_context': max(
                (entry['created_at'] for entry in self.store.values()),
                default=None
            )
        }
    
    def _cleanup_expired(self):
        """Limpia contextos expirados"""
        try:
            expired_ids = []
            
            for context_id, context_entry in self.store.items():
                if self._is_expired(context_entry):
                    expired_ids.append(context_id)
            
            for context_id in expired_ids:
                self._remove_context(context_id)
                
        except Exception as e:
            logger.error(f"Error limpiando contextos expirados: {e}")
    
    def _is_expired(self, context_entry: Dict[str, Any]) -> bool:
        """Verifica si un contexto ha expirado"""
        expiry_time = context_entry['created_at'] + timedelta(minutes=self.ttl_minutes)
        return datetime.now() > expiry_time
    
    def _remove_context(self, context_id: str):
        """Elimina un contexto específico"""
        if context_id in self.store:
            del self.store[context_id]
            
        if context_id in self.access_order:
            self.access_order.remove(context_id)