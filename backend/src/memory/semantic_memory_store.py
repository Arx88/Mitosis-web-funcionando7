"""
Almacén de memoria semántica
Gestiona conocimiento general, hechos y relaciones conceptuales
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import json
import logging
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class SemanticConcept:
    """Representa un concepto semántico"""
    id: str
    name: str
    description: str
    category: str
    attributes: Dict[str, Any]
    relations: Dict[str, List[str]]  # tipo_relación -> [conceptos_relacionados]
    confidence: float = 1.0
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = None  # Agregado para compatibilidad con rutas
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        
        # Auto-generar ID si no se proporciona
        if not self.id:
            self.id = f"concept_{datetime.now().timestamp()}"

@dataclass
class SemanticFact:
    """Representa un hecho semántico"""
    id: str
    subject: str
    predicate: str
    object: str
    context: Dict[str, Any]
    confidence: float = 1.0
    source: str = "unknown"
    created_at: datetime = None
    verified: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class SemanticMemoryStore:
    """Almacén de memoria semántica para conocimiento general"""
    
    def __init__(self, max_concepts: int = 10000, max_facts: int = 50000):
        """
        Inicializa el almacén de memoria semántica
        
        Args:
            max_concepts: Número máximo de conceptos
            max_facts: Número máximo de hechos
        """
        self.max_concepts = max_concepts
        self.max_facts = max_facts
        self.concepts: Dict[str, SemanticConcept] = {}
        self.facts: Dict[str, SemanticFact] = {}
        self.concept_index: Dict[str, Set[str]] = defaultdict(set)  # índice por categoría
        self.fact_index: Dict[str, Set[str]] = defaultdict(set)  # índice por sujeto
        
    def store_concept(self, concept: SemanticConcept):
        """
        Almacena un concepto semántico
        
        Args:
            concept: Concepto a almacenar
        """
        try:
            # Aplicar límite de capacidad
            if len(self.concepts) >= self.max_concepts:
                self._remove_least_confident_concept()
            
            # Actualizar si ya existe
            if concept.id in self.concepts:
                existing_concept = self.concepts[concept.id]
                concept.created_at = existing_concept.created_at
                concept.updated_at = datetime.now()
            
            # Almacenar concepto
            self.concepts[concept.id] = concept
            
            # Actualizar índices
            self.concept_index[concept.category].add(concept.id)
            
            logger.debug(f"Concepto {concept.id} almacenado en memoria semántica")
            
        except Exception as e:
            logger.error(f"Error almacenando concepto {concept.id}: {e}")
    
    def store_fact(self, fact: SemanticFact):
        """
        Almacena un hecho semántico
        
        Args:
            fact: Hecho a almacenar
        """
        try:
            # Aplicar límite de capacidad
            if len(self.facts) >= self.max_facts:
                self._remove_least_confident_fact()
            
            # Almacenar hecho
            self.facts[fact.id] = fact
            
            # Actualizar índices
            self.fact_index[fact.subject].add(fact.id)
            
            logger.debug(f"Hecho {fact.id} almacenado en memoria semántica")
            
        except Exception as e:
            logger.error(f"Error almacenando hecho {fact.id}: {e}")
    
    def retrieve_concept(self, concept_id: str) -> Optional[SemanticConcept]:
        """
        Recupera un concepto específico
        
        Args:
            concept_id: ID del concepto
            
        Returns:
            Concepto o None si no existe
        """
        return self.concepts.get(concept_id)
    
    def retrieve_fact(self, fact_id: str) -> Optional[SemanticFact]:
        """
        Recupera un hecho específico
        
        Args:
            fact_id: ID del hecho
            
        Returns:
            Hecho o None si no existe
        """
        return self.facts.get(fact_id)
    
    def search_concepts(self, query: str, category: str = None, limit: int = 10) -> List[SemanticConcept]:
        """
        Busca conceptos por nombre o descripción
        
        Args:
            query: Consulta de búsqueda
            category: Categoría específica (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de conceptos coincidentes
        """
        try:
            results = []
            query_lower = query.lower()
            
            # Filtrar por categoría si se especifica
            concepts_to_search = self.concepts.values()
            if category:
                concept_ids = self.concept_index.get(category, set())
                concepts_to_search = [self.concepts[cid] for cid in concept_ids]
            
            for concept in concepts_to_search:
                # Buscar en nombre y descripción
                if (query_lower in concept.name.lower() or 
                    query_lower in concept.description.lower()):
                    results.append(concept)
                    
                    if len(results) >= limit:
                        break
            
            # Ordenar por relevancia (confianza)
            results.sort(key=lambda x: x.confidence, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error buscando conceptos: {e}")
            return []
    
    def search_facts(self, subject: str = None, predicate: str = None, object: str = None, limit: int = 10) -> List[SemanticFact]:
        """
        Busca hechos por sujeto, predicado u objeto
        
        Args:
            subject: Sujeto del hecho (opcional)
            predicate: Predicado del hecho (opcional)
            object: Objeto del hecho (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de hechos coincidentes
        """
        try:
            results = []
            
            # Filtrar por sujeto si se especifica
            facts_to_search = self.facts.values()
            if subject:
                fact_ids = self.fact_index.get(subject, set())
                facts_to_search = [self.facts[fid] for fid in fact_ids]
            
            for fact in facts_to_search:
                match = True
                
                # Verificar predicado
                if predicate and predicate.lower() not in fact.predicate.lower():
                    match = False
                
                # Verificar objeto
                if object and object.lower() not in fact.object.lower():
                    match = False
                
                if match:
                    results.append(fact)
                    
                    if len(results) >= limit:
                        break
            
            # Ordenar por confianza
            results.sort(key=lambda x: x.confidence, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error buscando hechos: {e}")
            return []
    
    def get_related_concepts(self, concept_id: str, relation_type: str = None, limit: int = 10) -> List[SemanticConcept]:
        """
        Obtiene conceptos relacionados
        
        Args:
            concept_id: ID del concepto base
            relation_type: Tipo de relación (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de conceptos relacionados
        """
        try:
            concept = self.concepts.get(concept_id)
            if not concept:
                return []
            
            related_concepts = []
            
            # Buscar en relaciones directas
            for rel_type, related_ids in concept.relations.items():
                if relation_type is None or rel_type == relation_type:
                    for related_id in related_ids:
                        if related_id in self.concepts:
                            related_concepts.append(self.concepts[related_id])
            
            # Buscar en relaciones inversas
            for other_concept in self.concepts.values():
                for rel_type, related_ids in other_concept.relations.items():
                    if concept_id in related_ids:
                        if relation_type is None or rel_type == relation_type:
                            related_concepts.append(other_concept)
            
            # Eliminar duplicados y ordenar por confianza
            unique_concepts = list({c.id: c for c in related_concepts}.values())
            unique_concepts.sort(key=lambda x: x.confidence, reverse=True)
            
            return unique_concepts[:limit]
            
        except Exception as e:
            logger.error(f"Error obteniendo conceptos relacionados: {e}")
            return []
    
    def infer_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """
        Infiere conocimiento basado en hechos y relaciones
        
        Args:
            query: Consulta para inferencia
            
        Returns:
            Lista de inferencias
        """
        try:
            inferences = []
            query_lower = query.lower()
            
            # Buscar hechos relacionados
            related_facts = []
            for fact in self.facts.values():
                if (query_lower in fact.subject.lower() or 
                    query_lower in fact.predicate.lower() or 
                    query_lower in fact.object.lower()):
                    related_facts.append(fact)
            
            # Inferencia simple: transitividad
            for fact1 in related_facts:
                for fact2 in related_facts:
                    if fact1.object == fact2.subject and fact1.predicate == fact2.predicate:
                        # Inferir relación transitiva
                        inferences.append({
                            'type': 'transitive',
                            'subject': fact1.subject,
                            'predicate': fact1.predicate,
                            'object': fact2.object,
                            'confidence': min(fact1.confidence, fact2.confidence) * 0.8,
                            'supporting_facts': [fact1.id, fact2.id]
                        })
            
            # Ordenar por confianza
            inferences.sort(key=lambda x: x['confidence'], reverse=True)
            
            return inferences[:10]  # Limitar resultados
            
        except Exception as e:
            logger.error(f"Error infiriendo conocimiento: {e}")
            return []
    
    def update_concept_confidence(self, concept_id: str, confidence_delta: float):
        """
        Actualiza la confianza de un concepto
        
        Args:
            concept_id: ID del concepto
            confidence_delta: Cambio en confianza
        """
        try:
            if concept_id in self.concepts:
                concept = self.concepts[concept_id]
                concept.confidence = max(0.0, min(1.0, concept.confidence + confidence_delta))
                concept.updated_at = datetime.now()
                
        except Exception as e:
            logger.error(f"Error actualizando confianza del concepto {concept_id}: {e}")
    
    def update_fact_confidence(self, fact_id: str, confidence_delta: float):
        """
        Actualiza la confianza de un hecho
        
        Args:
            fact_id: ID del hecho
            confidence_delta: Cambio en confianza
        """
        try:
            if fact_id in self.facts:
                fact = self.facts[fact_id]
                fact.confidence = max(0.0, min(1.0, fact.confidence + confidence_delta))
                
        except Exception as e:
            logger.error(f"Error actualizando confianza del hecho {fact_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la memoria semántica
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            concepts_by_category = defaultdict(int)
            for concept in self.concepts.values():
                concepts_by_category[concept.category] += 1
            
            facts_by_subject = defaultdict(int)
            for fact in self.facts.values():
                facts_by_subject[fact.subject] += 1
            
            avg_concept_confidence = (
                sum(c.confidence for c in self.concepts.values()) / len(self.concepts)
                if self.concepts else 0
            )
            
            avg_fact_confidence = (
                sum(f.confidence for f in self.facts.values()) / len(self.facts)
                if self.facts else 0
            )
            
            return {
                'total_concepts': len(self.concepts),
                'total_facts': len(self.facts),
                'concepts_by_category': dict(concepts_by_category),
                'top_subjects': dict(sorted(facts_by_subject.items(), key=lambda x: x[1], reverse=True)[:10]),
                'average_concept_confidence': avg_concept_confidence,
                'average_fact_confidence': avg_fact_confidence,
                'verified_facts': sum(1 for f in self.facts.values() if f.verified)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def _remove_least_confident_concept(self):
        """Elimina el concepto con menor confianza"""
        if not self.concepts:
            return
            
        least_confident = min(self.concepts.items(), key=lambda x: x[1].confidence)
        concept_id = least_confident[0]
        concept = least_confident[1]
        
        # Eliminar del almacén e índices
        del self.concepts[concept_id]
        self.concept_index[concept.category].discard(concept_id)
    
    def _remove_least_confident_fact(self):
        """Elimina el hecho con menor confianza"""
        if not self.facts:
            return
            
        least_confident = min(self.facts.items(), key=lambda x: x[1].confidence)
        fact_id = least_confident[0]
        fact = least_confident[1]
        
        # Eliminar del almacén e índices
        del self.facts[fact_id]
        self.fact_index[fact.subject].discard(fact_id)