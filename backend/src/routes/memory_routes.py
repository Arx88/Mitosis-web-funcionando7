"""
Rutas específicas para el sistema de memoria avanzado
Endpoints dedicados para operaciones de memoria del agente
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import asyncio
from typing import Dict, List, Any, Optional

from src.memory.advanced_memory_manager import AdvancedMemoryManager
from src.memory.episodic_memory_store import Episode
from src.memory.semantic_memory_store import SemanticConcept, SemanticFact
from src.memory.procedural_memory_store import Procedure, ToolStrategy

logger = logging.getLogger(__name__)

memory_bp = Blueprint('memory', __name__)

# Obtener el gestor de memoria
def get_memory_manager():
    """Obtiene el gestor de memoria del contexto de la aplicación"""
    return current_app.memory_manager if hasattr(current_app, 'memory_manager') else None

@memory_bp.route('/semantic-search', methods=['POST'])
async def semantic_search():
    """
    Búsqueda semántica en el sistema de memoria
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        max_results = data.get('max_results', 10)
        memory_types = data.get('memory_types', ['all'])
        
        memory_manager = get_memory_manager()
        if not memory_manager:
            return jsonify({'error': 'Memory manager not available'}), 503
            
        # Inicializar si es necesario
        if not memory_manager.is_initialized:
            await memory_manager.initialize()
        
        # Realizar búsqueda semántica
        results = await memory_manager.semantic_search(
            query=query,
            max_results=max_results,
            memory_types=memory_types
        )
        
        return jsonify({
            'query': query,
            'results': results,
            'total_results': len(results),
            'search_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@memory_bp.route('/store-episode', methods=['POST'])
async def store_episode():
    """
    Almacenar un episodio en la memoria episódica
    """
    try:
        data = request.get_json()
        
        required_fields = ['user_query', 'agent_response', 'success']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        memory_manager = get_memory_manager()
        if not memory_manager:
            return jsonify({'error': 'Memory manager not available'}), 503
            
        # Crear episodio usando el método de factory
        episode = Episode.from_chat_interaction(
            user_query=data['user_query'],
            agent_response=data['agent_response'],
            success=data['success'],
            context=data.get('context', {}),
            tools_used=data.get('tools_used', []),
            importance=data.get('importance', 0.5),
            metadata=data.get('metadata', {})
        )
        
        # Almacenar episodio
        memory_manager.episodic_memory.store_episode(episode)
        
        return jsonify({
            'success': True,
            'episode_id': episode.id,
            'stored_at': episode.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error storing episode: {str(e)}")
        return jsonify({'error': f'Failed to store episode: {str(e)}'}), 500

@memory_bp.route('/store-knowledge', methods=['POST'])
async def store_knowledge():
    """
    Almacenar conocimiento en memoria semántica
    """
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400
        
        memory_manager = get_memory_manager()
        if not memory_manager:
            return jsonify({'error': 'Memory manager not available'}), 503
            
        knowledge_type = data.get('type', 'fact')  # 'fact' o 'concept'
        content = data['content']
        
        if knowledge_type == 'concept':
            concept = SemanticConcept(
                id=f"concept_{datetime.now().timestamp()}",
                name=data.get('name', 'Unknown Concept'),
                description=content,
                category=data.get('category', 'general'),
                attributes=data.get('attributes', {}),
                relations=data.get('relations', {}),
                confidence=data.get('confidence', 0.8),
                metadata=data.get('metadata', {})
            )
            memory_manager.semantic_memory.store_concept(concept)
            stored_id = concept.id
            
        else:  # fact
            fact = SemanticFact(
                id=f"fact_{datetime.now().timestamp()}",
                subject=data.get('subject', 'Unknown Subject'),
                predicate=data.get('predicate', 'relates to'),
                object=data.get('object', content),
                confidence=data.get('confidence', 0.8),
                context=data.get('context', {}),
            )
            memory_manager.semantic_memory.store_fact(fact)
            stored_id = fact.id
        
        return jsonify({
            'success': True,
            'knowledge_id': stored_id,
            'type': knowledge_type,
            'stored_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error storing knowledge: {str(e)}")
        return jsonify({'error': f'Failed to store knowledge: {str(e)}'}), 500

@memory_bp.route('/store-procedure', methods=['POST'])
async def store_procedure():
    """
    Almacenar un procedimiento en memoria procedimental
    """
    try:
        data = request.get_json()
        
        required_fields = ['name', 'steps', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        memory_manager = get_memory_manager()
        if not memory_manager:
            return jsonify({'error': 'Memory manager not available'}), 503
            
        procedure = Procedure(
            id=f"proc_{datetime.now().timestamp()}",
            name=data['name'],
            description=data.get('description', f"Procedimiento: {data['name']}"),
            steps=data['steps'],
            context_conditions=data.get('context_conditions', {}),
            category=data['category'],
            effectiveness=data.get('effectiveness', 0.5),
            usage_count=data.get('usage_count', 0),
            metadata=data.get('metadata', {})
        )
        
        memory_manager.procedural_memory.store_procedure(procedure)
        
        return jsonify({
            'success': True,
            'procedure_id': procedure.id,
            'stored_at': procedure.created_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error storing procedure: {str(e)}")
        return jsonify({'error': f'Failed to store procedure: {str(e)}'}), 500

@memory_bp.route('/retrieve-context', methods=['POST'])
async def retrieve_context():
    """
    Recuperar contexto relevante para una consulta
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        memory_manager = get_memory_manager()
        if not memory_manager:
            return jsonify({'error': 'Memory manager not available'}), 503
            
        query = data['query']
        context_type = data.get('context_type', 'all')
        max_results = data.get('max_results', 10)
        
        # Recuperar contexto relevante
        context = await memory_manager.retrieve_relevant_context(
            query=query,
            context_type=context_type,
            max_results=max_results
        )
        
        return jsonify({
            'query': query,
            'context': context,
            'retrieved_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        return jsonify({'error': f'Failed to retrieve context: {str(e)}'}), 500

@memory_bp.route('/memory-analytics', methods=['GET'])
async def memory_analytics():
    """
    Obtener analytics detallados del sistema de memoria
    """
    try:
        memory_manager = get_memory_manager()
        if not memory_manager:
            return jsonify({'error': 'Memory manager not available'}), 503
            
        # Obtener estadísticas detalladas
        stats = await memory_manager.get_memory_stats()
        
        # Análisis adicional
        analytics = {
            'overview': stats,
            'memory_efficiency': {
                'total_capacity_used': (
                    stats['working_memory']['total_contexts'] +
                    stats['episodic_memory']['total_episodes'] +
                    stats['semantic_memory']['total_concepts'] +
                    stats['semantic_memory']['total_facts'] +
                    stats['procedural_memory']['total_procedures']
                ),
                'embedding_efficiency': stats['embedding_service']['index_size'],
                'search_performance': stats['semantic_indexer']['total_documents']
            },
            'learning_insights': {
                'episode_success_rate': stats['episodic_memory']['success_rate'],
                'procedure_effectiveness': stats['procedural_memory']['average_procedure_effectiveness'],
                'knowledge_confidence': stats['semantic_memory']['average_fact_confidence']
            }
        }
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting memory analytics: {str(e)}")
        return jsonify({'error': f'Failed to get analytics: {str(e)}'}), 500

@memory_bp.route('/compress-memory', methods=['POST'])
async def compress_memory():
    """
    Comprimir memoria antigua para optimizar rendimiento
    """
    try:
        data = request.get_json()
        
        memory_manager = get_memory_manager()
        if not memory_manager:
            return jsonify({'error': 'Memory manager not available'}), 503
            
        compression_config = data.get('config', {})
        
        # Realizar compresión
        result = await memory_manager.compress_old_memory(compression_config)
        
        return jsonify({
            'success': True,
            'compressed_items': result.get('compressed_items', 0),
            'memory_saved': result.get('memory_saved', 0),
            'compression_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error compressing memory: {str(e)}")
        return jsonify({'error': f'Failed to compress memory: {str(e)}'}), 500

@memory_bp.route('/export-memory', methods=['GET'])
async def export_memory():
    """
    Exportar datos de memoria para backup
    """
    try:
        memory_manager = get_memory_manager()
        if not memory_manager:
            return jsonify({'error': 'Memory manager not available'}), 503
            
        # Exportar todos los datos de memoria
        export_data = await memory_manager.export_memory_data()
        
        return jsonify({
            'success': True,
            'export_data': export_data,
            'export_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error exporting memory: {str(e)}")
        return jsonify({'error': f'Failed to export memory: {str(e)}'}), 500