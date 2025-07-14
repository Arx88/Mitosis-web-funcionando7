"""
Sistema de Gestión de Memoria Mejorado para el agente Mitosis
Incluye integración con base de datos vectorial para búsquedas semánticas
"""

import sqlite3
import json
import logging
import time
import hashlib
import threading
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pickle
import os
import chromadb
from chromadb.config import Settings
import numpy as np

from memory_manager import Message, TaskMemory, KnowledgeItem, MemoryManager

@dataclass
class VectorKnowledgeItem:
    """Representa un elemento de conocimiento con embedding vectorial"""
    id: str
    content: str
    category: str
    source: str
    confidence: float
    created_at: float
    accessed_count: int = 0
    last_accessed: float = 0
    tags: List[str] = None
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class EnhancedMemoryManager(MemoryManager):
    """Gestor de memoria mejorado con capacidades vectoriales y optimizaciones"""
    
    def __init__(self, db_path: str = "mitosis_memory.db", 
                 vector_db_path: str = "./chroma_db",
                 max_short_term_messages: int = 50):
        super().__init__(db_path, max_short_term_messages)
        
        # Configuración de la base de datos vectorial
        self.vector_db_path = vector_db_path
        self.chroma_client = None
        self.knowledge_collection = None
        
        # Cache mejorado
        self._vector_cache: Dict[str, VectorKnowledgeItem] = {}
        self._cache_lock = threading.RLock()
        
        # Configuración de compresión
        self.compression_enabled = True
        self.compression_threshold_days = 7
        
        # Inicializar base de datos vectorial
        self._init_vector_database()
        
        # Estadísticas mejoradas
        self.stats = {
            "vector_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "compressions_performed": 0,
            "knowledge_items_compressed": 0
        }
        
        self.logger.info("Enhanced Memory Manager inicializado con base de datos vectorial")
    
    def _init_vector_database(self):
        """Inicializa la base de datos vectorial ChromaDB"""
        try:
            # Configurar ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=self.vector_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Crear o obtener la colección de conocimiento
            self.knowledge_collection = self.chroma_client.get_or_create_collection(
                name="knowledge_base",
                metadata={"description": "Base de conocimiento del agente Mitosis"}
            )
            
            self.logger.info(f"Base de datos vectorial inicializada en: {self.vector_db_path}")
            
        except Exception as e:
            self.logger.error(f"Error al inicializar base de datos vectorial: {e}")
            self.chroma_client = None
            self.knowledge_collection = None
    
    def add_knowledge_enhanced(self, content: str, category: str, source: str, 
                              confidence: float = 1.0, tags: Optional[List[str]] = None) -> str:
        """Añade un elemento de conocimiento con embedding vectorial"""
        knowledge_id = hashlib.md5(f"{content}{category}{source}".encode()).hexdigest()
        
        knowledge_item = VectorKnowledgeItem(
            id=knowledge_id,
            content=content,
            category=category,
            source=source,
            confidence=confidence,
            created_at=time.time(),
            tags=tags or []
        )
        
        try:
            # Añadir a SQLite (base de datos tradicional)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge_base 
                (id, content, category, source, confidence, created_at, accessed_count, last_accessed, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge_item.id,
                knowledge_item.content,
                knowledge_item.category,
                knowledge_item.source,
                knowledge_item.confidence,
                knowledge_item.created_at,
                knowledge_item.accessed_count,
                knowledge_item.last_accessed,
                json.dumps(knowledge_item.tags)
            ))
            
            conn.commit()
            conn.close()
            
            # Añadir a la base de datos vectorial
            if self.knowledge_collection is not None:
                self.knowledge_collection.upsert(
                    documents=[content],
                    metadatas=[{
                        "category": category,
                        "source": source,
                        "confidence": confidence,
                        "created_at": knowledge_item.created_at,
                        "tags": json.dumps(tags or [])
                    }],
                    ids=[knowledge_id]
                )
            
            # Actualizar cache
            with self._cache_lock:
                self._vector_cache[knowledge_id] = knowledge_item
                self._manage_cache_size()
            
            self.logger.info(f"Conocimiento mejorado añadido: {knowledge_id}")
            return knowledge_id
            
        except Exception as e:
            self.logger.error(f"Error al añadir conocimiento mejorado: {e}")
            return ""
    
    def search_knowledge_semantic(self, query: str, n_results: int = 10, 
                                 category: Optional[str] = None,
                                 min_confidence: float = 0.5) -> List[VectorKnowledgeItem]:
        """Busca elementos de conocimiento usando búsqueda semántica"""
        if self.knowledge_collection is None:
            self.logger.warning("Base de datos vectorial no disponible, usando búsqueda tradicional")
            return self._convert_to_vector_items(
                self.search_knowledge(query, category, n_results, min_confidence)
            )
        
        try:
            self.stats["vector_searches"] += 1
            
            # Preparar filtros de metadatos
            where_clause = {}
            if category:
                where_clause["category"] = category
            if min_confidence > 0:
                where_clause["confidence"] = {"$gte": min_confidence}
            
            # Realizar búsqueda vectorial
            results = self.knowledge_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Convertir resultados a VectorKnowledgeItem
            vector_items = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    item_id = results['ids'][0][i]
                    
                    # Verificar cache primero
                    with self._cache_lock:
                        if item_id in self._vector_cache:
                            self.stats["cache_hits"] += 1
                            vector_items.append(self._vector_cache[item_id])
                            continue
                    
                    self.stats["cache_misses"] += 1
                    
                    # Crear VectorKnowledgeItem
                    vector_item = VectorKnowledgeItem(
                        id=item_id,
                        content=doc,
                        category=metadata.get('category', ''),
                        source=metadata.get('source', ''),
                        confidence=metadata.get('confidence', 0.0),
                        created_at=metadata.get('created_at', time.time()),
                        tags=json.loads(metadata.get('tags', '[]'))
                    )
                    
                    vector_items.append(vector_item)
                    
                    # Actualizar contador de acceso
                    self._update_access_count(item_id)
                    
                    # Añadir al cache
                    with self._cache_lock:
                        self._vector_cache[item_id] = vector_item
            
            return vector_items
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda semántica: {e}")
            # Fallback a búsqueda tradicional
            return self._convert_to_vector_items(
                self.search_knowledge(query, category, n_results, min_confidence)
            )
    
    def _convert_to_vector_items(self, knowledge_items: List[KnowledgeItem]) -> List[VectorKnowledgeItem]:
        """Convierte KnowledgeItem a VectorKnowledgeItem"""
        vector_items = []
        for item in knowledge_items:
            vector_item = VectorKnowledgeItem(
                id=item.id,
                content=item.content,
                category=item.category,
                source=item.source,
                confidence=item.confidence,
                created_at=item.created_at,
                accessed_count=item.accessed_count,
                last_accessed=item.last_accessed,
                tags=item.tags
            )
            vector_items.append(vector_item)
        return vector_items
    
    def compress_old_conversations(self, days_old: int = None) -> Dict[str, int]:
        """Comprime conversaciones antiguas para optimizar el espacio"""
        if days_old is None:
            days_old = self.compression_threshold_days
        
        if not self.compression_enabled:
            return {"compressed_sessions": 0, "messages_compressed": 0}
        
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener sesiones antiguas
            cursor.execute('''
                SELECT session_id, COUNT(*) as message_count
                FROM conversation_history 
                WHERE timestamp < ?
                GROUP BY session_id
            ''', (cutoff_time,))
            
            old_sessions = cursor.fetchall()
            compressed_sessions = 0
            total_messages_compressed = 0
            
            for session_id, message_count in old_sessions:
                # Obtener mensajes de la sesión
                cursor.execute('''
                    SELECT role, content, timestamp, metadata
                    FROM conversation_history
                    WHERE session_id = ? AND timestamp < ?
                    ORDER BY timestamp
                ''', (session_id, cutoff_time))
                
                messages = cursor.fetchall()
                
                if len(messages) > 5:  # Solo comprimir si hay suficientes mensajes
                    # Crear resumen de la conversación
                    summary = self._create_conversation_summary(messages)
                    
                    # Eliminar mensajes originales
                    cursor.execute('''
                        DELETE FROM conversation_history
                        WHERE session_id = ? AND timestamp < ?
                    ''', (session_id, cutoff_time))
                    
                    # Insertar resumen comprimido
                    cursor.execute('''
                        INSERT INTO conversation_history
                        (session_id, role, content, timestamp, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        session_id,
                        'system',
                        f"[RESUMEN COMPRIMIDO] {summary}",
                        cutoff_time,
                        json.dumps({
                            "compressed": True,
                            "original_message_count": len(messages),
                            "compression_date": time.time()
                        })
                    ))
                    
                    compressed_sessions += 1
                    total_messages_compressed += len(messages)
            
            conn.commit()
            conn.close()
            
            self.stats["compressions_performed"] += compressed_sessions
            self.stats["knowledge_items_compressed"] += total_messages_compressed
            
            self.logger.info(f"Compresión completada: {compressed_sessions} sesiones, {total_messages_compressed} mensajes")
            
            return {
                "compressed_sessions": compressed_sessions,
                "messages_compressed": total_messages_compressed
            }
            
        except Exception as e:
            self.logger.error(f"Error durante la compresión: {e}")
            return {"compressed_sessions": 0, "messages_compressed": 0}
    
    def _create_conversation_summary(self, messages: List[Tuple]) -> str:
        """Crea un resumen de una conversación"""
        # Extraer contenido de los mensajes
        conversation_text = []
        for role, content, timestamp, metadata in messages:
            if not content.startswith("[RESUMEN COMPRIMIDO]"):
                conversation_text.append(f"{role}: {content}")
        
        # Crear resumen simple (en una implementación real, se usaría un LLM)
        if len(conversation_text) > 10:
            # Tomar los primeros y últimos mensajes
            summary_parts = conversation_text[:3] + ["..."] + conversation_text[-3:]
            summary = " | ".join(summary_parts)
        else:
            summary = " | ".join(conversation_text)
        
        return summary[:500]  # Limitar longitud del resumen
    
    def optimize_vector_database(self) -> Dict[str, Any]:
        """Optimiza la base de datos vectorial"""
        if self.knowledge_collection is None:
            return {"status": "vector_db_not_available"}
        
        try:
            # Obtener estadísticas de la colección
            collection_count = self.knowledge_collection.count()
            
            # Limpiar elementos con baja confianza y poco acceso
            # (En ChromaDB, esto requeriría consultar y eliminar elementos específicos)
            
            self.logger.info(f"Optimización de base de datos vectorial completada. Elementos: {collection_count}")
            
            return {
                "status": "optimized",
                "collection_count": collection_count,
                "cache_size": len(self._vector_cache)
            }
            
        except Exception as e:
            self.logger.error(f"Error durante la optimización: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_enhanced_memory_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas mejoradas de la memoria"""
        base_stats = self.get_memory_stats()
        
        # Añadir estadísticas vectoriales
        vector_stats = {
            "vector_database": {
                "available": self.knowledge_collection is not None,
                "collection_count": self.knowledge_collection.count() if self.knowledge_collection else 0,
                "vector_cache_size": len(self._vector_cache)
            },
            "performance": self.stats.copy(),
            "compression": {
                "enabled": self.compression_enabled,
                "threshold_days": self.compression_threshold_days
            }
        }
        
        # Combinar estadísticas
        enhanced_stats = {**base_stats, **vector_stats}
        
        return enhanced_stats
    
    def _manage_cache_size(self):
        """Gestiona el tamaño del cache vectorial mejorado"""
        if len(self._vector_cache) > self._cache_max_size:
            # Remover elementos menos accedidos
            sorted_items = sorted(
                self._vector_cache.items(),
                key=lambda x: (x[1].accessed_count, x[1].last_accessed)
            )
            items_to_remove = len(self._vector_cache) - self._cache_max_size
            for i in range(items_to_remove):
                del self._vector_cache[sorted_items[i][0]]
    
    def backup_memory(self, backup_path: str) -> bool:
        """Crea una copia de seguridad de toda la memoria"""
        try:
            import shutil
            
            # Backup de SQLite
            sqlite_backup = f"{backup_path}_sqlite.db"
            shutil.copy2(self.db_path, sqlite_backup)
            
            # Backup de ChromaDB
            if os.path.exists(self.vector_db_path):
                vector_backup = f"{backup_path}_chroma"
                shutil.copytree(self.vector_db_path, vector_backup, dirs_exist_ok=True)
            
            self.logger.info(f"Backup de memoria creado en: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al crear backup: {e}")
            return False
    
    def restore_memory(self, backup_path: str) -> bool:
        """Restaura la memoria desde una copia de seguridad"""
        try:
            import shutil
            
            # Restaurar SQLite
            sqlite_backup = f"{backup_path}_sqlite.db"
            if os.path.exists(sqlite_backup):
                shutil.copy2(sqlite_backup, self.db_path)
            
            # Restaurar ChromaDB
            vector_backup = f"{backup_path}_chroma"
            if os.path.exists(vector_backup):
                if os.path.exists(self.vector_db_path):
                    shutil.rmtree(self.vector_db_path)
                shutil.copytree(vector_backup, self.vector_db_path)
                
                # Reinicializar conexión vectorial
                self._init_vector_database()
            
            self.logger.info(f"Memoria restaurada desde: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al restaurar memoria: {e}")
            return False

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear gestor de memoria mejorado
    enhanced_memory = EnhancedMemoryManager()
    
    # Probar funcionalidades mejoradas
    print("🧠 Probando Enhanced Memory Manager...")
    
    # Añadir conocimiento con búsqueda vectorial
    knowledge_id = enhanced_memory.add_knowledge_enhanced(
        content="Python es un lenguaje de programación interpretado de alto nivel con sintaxis clara",
        category="programming",
        source="test",
        confidence=0.9,
        tags=["python", "programming", "language"]
    )
    
    print(f"✅ Conocimiento añadido: {knowledge_id}")
    
    # Búsqueda semántica
    results = enhanced_memory.search_knowledge_semantic("lenguaje de programación", n_results=5)
    print(f"🔍 Resultados de búsqueda semántica: {len(results)}")
    for result in results:
        print(f"  - {result.content[:50]}... (confianza: {result.confidence})")
    
    # Estadísticas mejoradas
    stats = enhanced_memory.get_enhanced_memory_stats()
    print(f"📊 Estadísticas mejoradas:")
    print(f"  Base de datos vectorial disponible: {stats['vector_database']['available']}")
    print(f"  Elementos en colección: {stats['vector_database']['collection_count']}")
    print(f"  Búsquedas vectoriales: {stats['performance']['vector_searches']}")
    
    # Probar compresión
    compression_result = enhanced_memory.compress_old_conversations(days_old=0)
    print(f"🗜️ Compresión: {compression_result}")
    
    print("✅ Pruebas completadas")

