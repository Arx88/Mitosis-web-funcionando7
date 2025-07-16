"""
Indexador semántico para búsqueda eficiente en memoria
Combina indexación tradicional con búsqueda semántica
"""

import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SemanticIndexer:
    """Indexador semántico para búsqueda eficiente"""
    
    def __init__(self, embedding_service=None):
        """
        Inicializa el indexador semántico
        
        Args:
            embedding_service: Servicio de embeddings para búsqueda semántica
        """
        self.embedding_service = embedding_service
        self.keyword_index: Dict[str, Set[str]] = defaultdict(set)  # palabra -> doc_ids
        self.document_metadata: Dict[str, Dict[str, Any]] = {}
        self.category_index: Dict[str, Set[str]] = defaultdict(set)  # categoría -> doc_ids
        self.temporal_index: Dict[str, List[str]] = defaultdict(list)  # fecha -> doc_ids
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializa el indexador"""
        try:
            if self.embedding_service:
                await self.embedding_service.initialize()
            self.is_initialized = True
            logger.info("SemanticIndexer inicializado")
            
        except Exception as e:
            logger.error(f"Error inicializando SemanticIndexer: {e}")
            raise
    
    async def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """
        Añade un documento al índice
        
        Args:
            doc_id: ID único del documento
            content: Contenido del documento
            metadata: Metadatos del documento
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            # Procesar metadatos
            metadata = metadata or {}
            self.document_metadata[doc_id] = {
                **metadata,
                'content': content,
                'indexed_at': datetime.now(),
                'word_count': len(content.split())
            }
            
            # Indexación por palabras clave
            keywords = self._extract_keywords(content)
            for keyword in keywords:
                self.keyword_index[keyword].add(doc_id)
            
            # Indexación por categoría
            category = metadata.get('category', 'general')
            self.category_index[category].add(doc_id)
            
            # Indexación temporal
            date_key = datetime.now().strftime('%Y-%m-%d')
            self.temporal_index[date_key].append(doc_id)
            
            # Indexación semántica si está disponible
            if self.embedding_service:
                await self.embedding_service.add_document(doc_id, content, metadata)
            
            logger.debug(f"Documento {doc_id} añadido al índice semántico")
            
        except Exception as e:
            logger.error(f"Error añadiendo documento {doc_id} al índice: {e}")
            raise
    
    async def search(self, query: str, search_type: str = 'hybrid', limit: int = 10, 
                    category: str = None, date_range: Tuple[str, str] = None) -> List[Dict[str, Any]]:
        """
        Busca documentos usando múltiples estrategias
        
        Args:
            query: Consulta de búsqueda
            search_type: Tipo de búsqueda ('keyword', 'semantic', 'hybrid')
            limit: Número máximo de resultados
            category: Categoría específica (opcional)
            date_range: Rango de fechas (inicio, fin) (opcional)
            
        Returns:
            Lista de documentos con scores
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            results = []
            
            if search_type in ['keyword', 'hybrid']:
                keyword_results = await self._keyword_search(query, limit)
                results.extend(keyword_results)
            
            if search_type in ['semantic', 'hybrid'] and self.embedding_service:
                semantic_results = await self.embedding_service.search_similar(query, limit)
                
                # Convertir formato de resultados semánticos
                for result in semantic_results:
                    results.append({
                        'document_id': result['document_id'],
                        'content': result['content'],
                        'metadata': result['metadata'],
                        'score': result['similarity_score'],
                        'search_type': 'semantic'
                    })
            
            # Eliminar duplicados y combinar scores
            unique_results = self._merge_results(results)
            
            # Aplicar filtros
            if category:
                unique_results = [r for r in unique_results if r['metadata'].get('category') == category]
            
            if date_range:
                unique_results = self._filter_by_date_range(unique_results, date_range)
            
            # Ordenar por score
            unique_results.sort(key=lambda x: x['score'], reverse=True)
            
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    async def find_similar(self, query: str, memory_types: str = "all", max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Encuentra documentos similares (compatibilidad con AdvancedMemoryManager)
        
        Args:
            query: Consulta de búsqueda
            memory_types: Tipos de memoria a buscar
            max_results: Número máximo de resultados
            
        Returns:
            Lista de documentos similares
        """
        return await self.search(query, 'hybrid', max_results)
    
    async def remove_document(self, doc_id: str):
        """
        Elimina un documento del índice
        
        Args:
            doc_id: ID del documento a eliminar
        """
        try:
            # Eliminar de metadatos
            if doc_id in self.document_metadata:
                del self.document_metadata[doc_id]
            
            # Eliminar de índice de palabras clave
            for keyword_set in self.keyword_index.values():
                keyword_set.discard(doc_id)
            
            # Eliminar de índice de categorías
            for category_set in self.category_index.values():
                category_set.discard(doc_id)
            
            # Eliminar de índice temporal
            for doc_list in self.temporal_index.values():
                if doc_id in doc_list:
                    doc_list.remove(doc_id)
            
            # Eliminar de índice semántico
            if self.embedding_service:
                await self.embedding_service.remove_document(doc_id)
            
            logger.debug(f"Documento {doc_id} eliminado del índice")
            
        except Exception as e:
            logger.error(f"Error eliminando documento {doc_id}: {e}")
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            total_docs = len(self.document_metadata)
            total_keywords = len(self.keyword_index)
            
            # Distribución por categorías
            category_distribution = {
                category: len(doc_ids) 
                for category, doc_ids in self.category_index.items()
            }
            
            # Documentos por día
            daily_distribution = {
                date: len(doc_ids) 
                for date, doc_ids in self.temporal_index.items()
            }
            
            # Palabras clave más comunes
            keyword_frequency = {
                keyword: len(doc_ids) 
                for keyword, doc_ids in self.keyword_index.items()
            }
            
            top_keywords = sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            
            stats = {
                'total_documents': total_docs,
                'total_keywords': total_keywords,
                'category_distribution': category_distribution,
                'daily_distribution': daily_distribution,
                'top_keywords': dict(top_keywords),
                'is_initialized': self.is_initialized
            }
            
            # Añadir estadísticas de embedding si está disponible
            if self.embedding_service:
                embedding_stats = await self.embedding_service.get_stats()
                stats['embedding_stats'] = embedding_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """
        Extrae palabras clave del texto
        
        Args:
            text: Texto a procesar
            
        Returns:
            Set de palabras clave
        """
        try:
            # Limpiar y tokenizar
            text = re.sub(r'[^\w\s]', ' ', text.lower())
            words = text.split()
            
            # Filtrar palabras vacías y muy cortas
            stop_words = {
                'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo',
                'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las',
                'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for',
                'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by'
            }
            
            keywords = set()
            for word in words:
                if len(word) > 2 and word not in stop_words:
                    keywords.add(word)
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extrayendo palabras clave: {e}")
            return set()
    
    async def _keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Realiza búsqueda por palabras clave
        
        Args:
            query: Consulta de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Lista de resultados
        """
        try:
            query_keywords = self._extract_keywords(query)
            
            # Contar coincidencias por documento
            doc_scores = defaultdict(float)
            
            for keyword in query_keywords:
                if keyword in self.keyword_index:
                    for doc_id in self.keyword_index[keyword]:
                        doc_scores[doc_id] += 1.0
            
            # Normalizar scores
            for doc_id in doc_scores:
                doc_scores[doc_id] /= len(query_keywords)
            
            # Crear resultados
            results = []
            for doc_id, score in doc_scores.items():
                if doc_id in self.document_metadata:
                    metadata = self.document_metadata[doc_id]
                    results.append({
                        'document_id': doc_id,
                        'content': metadata['content'],
                        'metadata': metadata,
                        'score': score,
                        'search_type': 'keyword'
                    })
            
            # Ordenar por score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error en búsqueda por palabras clave: {e}")
            return []
    
    def _merge_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fusiona resultados de diferentes tipos de búsqueda
        
        Args:
            results: Lista de resultados
            
        Returns:
            Lista de resultados fusionados
        """
        try:
            # Agrupar por documento
            doc_results = defaultdict(list)
            for result in results:
                doc_id = result['document_id']
                doc_results[doc_id].append(result)
            
            # Fusionar scores
            merged_results = []
            for doc_id, doc_result_list in doc_results.items():
                # Combinar scores (promedio ponderado)
                total_score = 0
                total_weight = 0
                
                for result in doc_result_list:
                    weight = 1.0
                    if result['search_type'] == 'semantic':
                        weight = 1.2  # Dar más peso a búsqueda semántica
                    
                    total_score += result['score'] * weight
                    total_weight += weight
                
                final_score = total_score / total_weight if total_weight > 0 else 0
                
                # Usar el primer resultado como base
                merged_result = doc_result_list[0].copy()
                merged_result['score'] = final_score
                merged_result['search_types'] = [r['search_type'] for r in doc_result_list]
                
                merged_results.append(merged_result)
            
            return merged_results
            
        except Exception as e:
            logger.error(f"Error fusionando resultados: {e}")
            return results
    
    def _filter_by_date_range(self, results: List[Dict[str, Any]], 
                            date_range: Tuple[str, str]) -> List[Dict[str, Any]]:
        """
        Filtra resultados por rango de fechas
        
        Args:
            results: Lista de resultados
            date_range: Tupla con fecha inicio y fin
            
        Returns:
            Lista de resultados filtrados
        """
        try:
            start_date, end_date = date_range
            
            filtered_results = []
            for result in results:
                indexed_at = result['metadata'].get('indexed_at')
                if indexed_at:
                    date_str = indexed_at.strftime('%Y-%m-%d')
                    if start_date <= date_str <= end_date:
                        filtered_results.append(result)
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error filtrando por fecha: {e}")
            return results