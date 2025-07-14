"""
Sistema de Gestión de Memoria para el agente Mitosis
Maneja memoria a corto plazo (contexto de conversación) y largo plazo (base de conocimientos)
"""

import sqlite3
import json
import logging
import time
import hashlib
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pickle
import os

@dataclass
class Message:
    """Representa un mensaje en la conversación"""
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    timestamp: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TaskMemory:
    """Representa la memoria de una tarea específica"""
    task_id: str
    title: str
    description: str
    status: str  # 'active', 'completed', 'failed', 'paused'
    created_at: float
    updated_at: float
    phases: List[Dict[str, Any]]
    results: Dict[str, Any] = None
    tools_used: List[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
        if self.tools_used is None:
            self.tools_used = []

@dataclass
class KnowledgeItem:
    """Representa un elemento de conocimiento en la memoria a largo plazo"""
    id: str
    content: str
    category: str
    source: str
    confidence: float
    created_at: float
    accessed_count: int = 0
    last_accessed: float = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class MemoryManager:
    """Gestor de memoria para el agente Mitosis"""
    
    def __init__(self, db_path: str = "mitosis_memory.db", max_short_term_messages: int = 50):
        self.db_path = db_path
        self.max_short_term_messages = max_short_term_messages
        self.logger = logging.getLogger(__name__)
        
        # Memoria a corto plazo (en memoria)
        self.short_term_memory: List[Message] = []
        self.current_session_id = self._generate_session_id()
        
        # Memoria a largo plazo (base de datos)
        self._init_database()
        
        # Cache para búsquedas frecuentes
        self._knowledge_cache: Dict[str, KnowledgeItem] = {}
        self._cache_max_size = 100
        
    def _generate_session_id(self) -> str:
        """Genera un ID único para la sesión actual"""
        timestamp = str(time.time())
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    def _init_database(self):
        """Inicializa la base de datos SQLite para la memoria a largo plazo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla para el historial de conversaciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # Tabla para la memoria de tareas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_memory (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    phases TEXT,
                    results TEXT,
                    tools_used TEXT
                )
            ''')
            
            # Tabla para elementos de conocimiento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at REAL NOT NULL,
                    accessed_count INTEGER DEFAULT 0,
                    last_accessed REAL DEFAULT 0,
                    tags TEXT
                )
            ''')
            
            # Índices para mejorar el rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_history(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_timestamp ON conversation_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON task_memory(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_confidence ON knowledge_base(confidence)')
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Base de datos de memoria inicializada: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Error al inicializar la base de datos: {e}")
            raise
    
    # === MEMORIA A CORTO PLAZO ===
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Añade un mensaje a la memoria a corto plazo"""
        message = Message(
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        self.short_term_memory.append(message)
        
        # Mantener el límite de mensajes en memoria
        if len(self.short_term_memory) > self.max_short_term_messages:
            # Mover mensajes antiguos a la base de datos
            old_messages = self.short_term_memory[:-self.max_short_term_messages]
            self._persist_messages_to_db(old_messages)
            self.short_term_memory = self.short_term_memory[-self.max_short_term_messages:]
        
        return message
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """Obtiene los mensajes más recientes de la memoria a corto plazo"""
        return self.short_term_memory[-count:] if count <= len(self.short_term_memory) else self.short_term_memory
    
    def get_conversation_context(self, max_tokens: int = 4000) -> str:
        """Obtiene el contexto de conversación formateado para el LLM"""
        context_parts = []
        total_tokens = 0
        
        # Estimar tokens (aproximadamente 4 caracteres por token)
        for message in reversed(self.short_term_memory):
            message_text = f"{message.role}: {message.content}\n"
            estimated_tokens = len(message_text) // 4
            
            if total_tokens + estimated_tokens > max_tokens:
                break
            
            context_parts.insert(0, message_text)
            total_tokens += estimated_tokens
        
        return "".join(context_parts)
    
    def clear_short_term_memory(self, persist: bool = True):
        """Limpia la memoria a corto plazo, opcionalmente persistiendo a la base de datos"""
        if persist and self.short_term_memory:
            self._persist_messages_to_db(self.short_term_memory)
        
        self.short_term_memory.clear()
        self.current_session_id = self._generate_session_id()
        self.logger.info("Memoria a corto plazo limpiada")
    
    def _persist_messages_to_db(self, messages: List[Message]):
        """Persiste mensajes a la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for message in messages:
                cursor.execute('''
                    INSERT INTO conversation_history 
                    (session_id, role, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    self.current_session_id,
                    message.role,
                    message.content,
                    message.timestamp,
                    json.dumps(message.metadata)
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error al persistir mensajes: {e}")
    
    # === MEMORIA A LARGO PLAZO - TAREAS ===
    
    def save_task_memory(self, task_memory: TaskMemory):
        """Guarda o actualiza la memoria de una tarea"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO task_memory 
                (task_id, title, description, status, created_at, updated_at, phases, results, tools_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_memory.task_id,
                task_memory.title,
                task_memory.description,
                task_memory.status,
                task_memory.created_at,
                task_memory.updated_at,
                json.dumps(task_memory.phases),
                json.dumps(task_memory.results),
                json.dumps(task_memory.tools_used)
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Memoria de tarea guardada: {task_memory.task_id}")
            
        except Exception as e:
            self.logger.error(f"Error al guardar memoria de tarea: {e}")
    
    def get_task_memory(self, task_id: str) -> Optional[TaskMemory]:
        """Recupera la memoria de una tarea específica"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM task_memory WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return TaskMemory(
                    task_id=row[0],
                    title=row[1],
                    description=row[2],
                    status=row[3],
                    created_at=row[4],
                    updated_at=row[5],
                    phases=json.loads(row[6]) if row[6] else [],
                    results=json.loads(row[7]) if row[7] else {},
                    tools_used=json.loads(row[8]) if row[8] else []
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error al recuperar memoria de tarea: {e}")
            return None
    
    def get_recent_tasks(self, count: int = 10, status: Optional[str] = None) -> List[TaskMemory]:
        """Obtiene las tareas más recientes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM task_memory 
                    WHERE status = ? 
                    ORDER BY updated_at DESC 
                    LIMIT ?
                ''', (status, count))
            else:
                cursor.execute('''
                    SELECT * FROM task_memory 
                    ORDER BY updated_at DESC 
                    LIMIT ?
                ''', (count,))
            
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                task = TaskMemory(
                    task_id=row[0],
                    title=row[1],
                    description=row[2],
                    status=row[3],
                    created_at=row[4],
                    updated_at=row[5],
                    phases=json.loads(row[6]) if row[6] else [],
                    results=json.loads(row[7]) if row[7] else {},
                    tools_used=json.loads(row[8]) if row[8] else []
                )
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"Error al recuperar tareas recientes: {e}")
            return []
    
    # === MEMORIA A LARGO PLAZO - CONOCIMIENTO ===
    
    def add_knowledge(self, content: str, category: str, source: str, 
                     confidence: float = 1.0, tags: Optional[List[str]] = None) -> str:
        """Añade un elemento de conocimiento a la base de datos"""
        knowledge_id = hashlib.md5(f"{content}{category}{source}".encode()).hexdigest()
        
        knowledge_item = KnowledgeItem(
            id=knowledge_id,
            content=content,
            category=category,
            source=source,
            confidence=confidence,
            created_at=time.time(),
            tags=tags or []
        )
        
        try:
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
            
            # Actualizar cache
            self._knowledge_cache[knowledge_id] = knowledge_item
            self._manage_cache_size()
            
            self.logger.info(f"Conocimiento añadido: {knowledge_id}")
            return knowledge_id
            
        except Exception as e:
            self.logger.error(f"Error al añadir conocimiento: {e}")
            return ""
    
    def search_knowledge(self, query: str, category: Optional[str] = None, 
                        limit: int = 10, min_confidence: float = 0.5) -> List[KnowledgeItem]:
        """Busca elementos de conocimiento relevantes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Búsqueda simple por contenido (se puede mejorar con FTS)
            if category:
                cursor.execute('''
                    SELECT * FROM knowledge_base 
                    WHERE category = ? AND confidence >= ? AND content LIKE ?
                    ORDER BY confidence DESC, accessed_count DESC
                    LIMIT ?
                ''', (category, min_confidence, f'%{query}%', limit))
            else:
                cursor.execute('''
                    SELECT * FROM knowledge_base 
                    WHERE confidence >= ? AND content LIKE ?
                    ORDER BY confidence DESC, accessed_count DESC
                    LIMIT ?
                ''', (min_confidence, f'%{query}%', limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            knowledge_items = []
            for row in rows:
                item = KnowledgeItem(
                    id=row[0],
                    content=row[1],
                    category=row[2],
                    source=row[3],
                    confidence=row[4],
                    created_at=row[5],
                    accessed_count=row[6],
                    last_accessed=row[7],
                    tags=json.loads(row[8]) if row[8] else []
                )
                knowledge_items.append(item)
                
                # Actualizar contador de acceso
                self._update_access_count(item.id)
            
            return knowledge_items
            
        except Exception as e:
            self.logger.error(f"Error al buscar conocimiento: {e}")
            return []
    
    def get_knowledge_by_category(self, category: str, limit: int = 20) -> List[KnowledgeItem]:
        """Obtiene elementos de conocimiento por categoría"""
        return self.search_knowledge("", category=category, limit=limit, min_confidence=0.0)
    
    def _update_access_count(self, knowledge_id: str):
        """Actualiza el contador de acceso de un elemento de conocimiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE knowledge_base 
                SET accessed_count = accessed_count + 1, last_accessed = ?
                WHERE id = ?
            ''', (time.time(), knowledge_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error al actualizar contador de acceso: {e}")
    
    def _manage_cache_size(self):
        """Gestiona el tamaño del cache de conocimiento"""
        if len(self._knowledge_cache) > self._cache_max_size:
            # Remover elementos menos accedidos
            sorted_items = sorted(
                self._knowledge_cache.items(),
                key=lambda x: x[1].accessed_count
            )
            items_to_remove = len(self._knowledge_cache) - self._cache_max_size
            for i in range(items_to_remove):
                del self._knowledge_cache[sorted_items[i][0]]
    
    # === UTILIDADES ===
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la memoria"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Estadísticas de conversaciones
            cursor.execute('SELECT COUNT(*) FROM conversation_history')
            total_messages = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT session_id) FROM conversation_history')
            total_sessions = cursor.fetchone()[0]
            
            # Estadísticas de tareas
            cursor.execute('SELECT COUNT(*) FROM task_memory')
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT status, COUNT(*) FROM task_memory GROUP BY status')
            task_status_counts = dict(cursor.fetchall())
            
            # Estadísticas de conocimiento
            cursor.execute('SELECT COUNT(*) FROM knowledge_base')
            total_knowledge = cursor.fetchone()[0]
            
            cursor.execute('SELECT category, COUNT(*) FROM knowledge_base GROUP BY category')
            knowledge_categories = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "short_term_memory": {
                    "current_messages": len(self.short_term_memory),
                    "max_messages": self.max_short_term_messages,
                    "current_session_id": self.current_session_id
                },
                "long_term_memory": {
                    "total_messages": total_messages,
                    "total_sessions": total_sessions,
                    "total_tasks": total_tasks,
                    "task_status_counts": task_status_counts,
                    "total_knowledge": total_knowledge,
                    "knowledge_categories": knowledge_categories
                },
                "cache": {
                    "knowledge_cache_size": len(self._knowledge_cache),
                    "cache_max_size": self._cache_max_size
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error al obtener estadísticas: {e}")
            return {}
    
    def cleanup_old_data(self, days_old: int = 30):
        """Limpia datos antiguos de la base de datos"""
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Limpiar conversaciones antiguas
            cursor.execute('DELETE FROM conversation_history WHERE timestamp < ?', (cutoff_time,))
            deleted_messages = cursor.rowcount
            
            # Limpiar tareas completadas antiguas
            cursor.execute('''
                DELETE FROM task_memory 
                WHERE status = 'completed' AND updated_at < ?
            ''', (cutoff_time,))
            deleted_tasks = cursor.rowcount
            
            # Limpiar conocimiento con baja confianza y poco acceso
            cursor.execute('''
                DELETE FROM knowledge_base 
                WHERE confidence < 0.3 AND accessed_count < 2 AND created_at < ?
            ''', (cutoff_time,))
            deleted_knowledge = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Limpieza completada: {deleted_messages} mensajes, {deleted_tasks} tareas, {deleted_knowledge} elementos de conocimiento eliminados")
            
        except Exception as e:
            self.logger.error(f"Error durante la limpieza: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear gestor de memoria
    memory = MemoryManager()
    
    # Probar memoria a corto plazo
    memory.add_message("user", "Hola, ¿cómo estás?")
    memory.add_message("assistant", "¡Hola! Estoy bien, gracias por preguntar. ¿En qué puedo ayudarte?")
    memory.add_message("user", "Necesito ayuda con un proyecto de Python")
    
    print("📝 Mensajes recientes:")
    for msg in memory.get_recent_messages():
        print(f"  {msg.role}: {msg.content}")
    
    # Probar memoria de tareas
    task = TaskMemory(
        task_id="test-task-001",
        title="Proyecto de Python",
        description="Ayudar al usuario con su proyecto de Python",
        status="active",
        created_at=time.time(),
        updated_at=time.time(),
        phases=[{"id": 1, "title": "Análisis de requisitos"}]
    )
    memory.save_task_memory(task)
    
    # Probar base de conocimiento
    memory.add_knowledge(
        content="Python es un lenguaje de programación interpretado de alto nivel",
        category="programming",
        source="user_conversation",
        confidence=0.9,
        tags=["python", "programming", "language"]
    )
    
    # Buscar conocimiento
    results = memory.search_knowledge("Python")
    print(f"\n🔍 Resultados de búsqueda para 'Python': {len(results)}")
    for result in results:
        print(f"  - {result.content[:50]}... (confianza: {result.confidence})")
    
    # Mostrar estadísticas
    stats = memory.get_memory_stats()
    print(f"\n📊 Estadísticas de memoria:")
    print(f"  Mensajes a corto plazo: {stats['short_term_memory']['current_messages']}")
    print(f"  Total de conocimiento: {stats['long_term_memory']['total_knowledge']}")
    print(f"  Total de tareas: {stats['long_term_memory']['total_tasks']}")

