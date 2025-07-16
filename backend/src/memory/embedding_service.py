"""
Servicio de embeddings para búsqueda semántica
Implementa generación de embeddings y búsqueda por similitud
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Servicio para generar embeddings y realizar búsqueda semántica"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", storage_path: str = "embeddings"):
        """
        Inicializa el servicio de embeddings
        
        Args:
            model_name: Nombre del modelo SentenceTransformer
            storage_path: Ruta para almacenar índices
        """
        self.model_name = model_name
        self.storage_path = storage_path
        self.model = None
        self.index = None
        self.document_map = {}  # Mapeo de ID a documento
        self.is_initialized = False
        
        # Crear directorio de almacenamiento
        os.makedirs(storage_path, exist_ok=True)
        
    async def initialize(self):
        """Inicializa el modelo de embeddings"""
        try:
            # Cargar modelo en thread pool para evitar bloqueo
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                lambda: SentenceTransformer(self.model_name)
            )
            
            # Cargar índice existente si existe
            await self._load_index()
            
            self.is_initialized = True
            logger.info(f"EmbeddingService inicializado con modelo {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error inicializando EmbeddingService: {e}")
            raise
    
    async def embed_text(self, text: str) -> np.ndarray:
        """
        Genera embedding para un texto
        
        Args:
            text: Texto a procesar
            
        Returns:
            Array numpy con el embedding
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            # Generar embedding en thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode([text])
            )
            
            return embedding[0]
            
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Genera embeddings para múltiples textos
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de embeddings
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(texts)
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generando embeddings batch: {e}")
            raise
    
    async def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """
        Añade un documento al índice
        
        Args:
            doc_id: ID único del documento
            content: Contenido del documento
            metadata: Metadatos adicionales
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            # Generar embedding
            embedding = await self.embed_text(content)
            
            # Inicializar índice FAISS si no existe
            if self.index is None:
                dimension = embedding.shape[0]
                self.index = faiss.IndexFlatIP(dimension)  # Inner product para similitud coseno
                
            # Normalizar embedding para similitud coseno
            embedding_norm = embedding / np.linalg.norm(embedding)
            
            # Añadir al índice
            self.index.add(embedding_norm.reshape(1, -1))
            
            # Guardar mapeo
            self.document_map[doc_id] = {
                'content': content,
                'metadata': metadata or {},
                'index_id': self.index.ntotal - 1,
                'created_at': datetime.now().isoformat()
            }
            
            # Persistir índice
            await self._save_index()
            
            logger.info(f"Documento {doc_id} añadido al índice semántico")
            
        except Exception as e:
            logger.error(f"Error añadiendo documento {doc_id}: {e}")
            raise
    
    async def search_similar(self, query: str, top_k: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Busca documentos similares a la consulta
        
        Args:
            query: Consulta de búsqueda
            top_k: Número máximo de resultados
            threshold: Umbral de similitud mínima
            
        Returns:
            Lista de documentos similares con scores
        """
        if not self.is_initialized:
            await self.initialize()
            
        if self.index is None or self.index.ntotal == 0:
            return []
            
        try:
            # Generar embedding de consulta
            query_embedding = await self.embed_text(query)
            query_embedding_norm = query_embedding / np.linalg.norm(query_embedding)
            
            # Buscar similares
            scores, indices = self.index.search(
                query_embedding_norm.reshape(1, -1), 
                min(top_k, self.index.ntotal)
            )
            
            # Procesar resultados
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= threshold:
                    # Encontrar documento por índice
                    doc_id = None
                    for doc_id, doc_data in self.document_map.items():
                        if doc_data['index_id'] == idx:
                            break
                    
                    if doc_id:
                        results.append({
                            'document_id': doc_id,
                            'content': doc_data['content'],
                            'metadata': doc_data['metadata'],
                            'similarity_score': float(score),
                            'created_at': doc_data['created_at']
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda semántica: {e}")
            raise
    
    async def remove_document(self, doc_id: str):
        """
        Elimina un documento del índice
        
        Args:
            doc_id: ID del documento a eliminar
        """
        if doc_id in self.document_map:
            del self.document_map[doc_id]
            # Nota: FAISS no soporta eliminación directa, 
            # sería necesario reconstruir el índice
            await self._save_index()
            logger.info(f"Documento {doc_id} eliminado del índice")
    
    async def clear_index(self):
        """Limpia completamente el índice"""
        self.index = None
        self.document_map = {}
        await self._save_index()
        logger.info("Índice semántico limpiado")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice
        
        Returns:
            Diccionario con estadísticas
        """
        total_docs = len(self.document_map)
        index_size = self.index.ntotal if self.index else 0
        
        return {
            'total_documents': total_docs,
            'index_size': index_size,
            'model_name': self.model_name,
            'is_initialized': self.is_initialized,
            'storage_path': self.storage_path
        }
    
    async def _save_index(self):
        """Guarda el índice en disco"""
        try:
            if self.index is not None:
                # Guardar índice FAISS
                index_path = os.path.join(self.storage_path, 'faiss_index.idx')
                faiss.write_index(self.index, index_path)
                
            # Guardar mapeo de documentos
            map_path = os.path.join(self.storage_path, 'document_map.pkl')
            with open(map_path, 'wb') as f:
                pickle.dump(self.document_map, f)
                
        except Exception as e:
            logger.error(f"Error guardando índice: {e}")
    
    async def _load_index(self):
        """Carga el índice desde disco"""
        try:
            # Cargar índice FAISS
            index_path = os.path.join(self.storage_path, 'faiss_index.idx')
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
                
            # Cargar mapeo de documentos
            map_path = os.path.join(self.storage_path, 'document_map.pkl')
            if os.path.exists(map_path):
                with open(map_path, 'rb') as f:
                    self.document_map = pickle.load(f)
                    
        except Exception as e:
            logger.error(f"Error cargando índice: {e}")