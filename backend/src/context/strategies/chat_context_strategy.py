"""
Estrategia de Contexto para Conversación Casual
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatContextStrategy:
    """Estrategia para contexto de conversación casual"""
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        context = {
            'type': 'chat',
            'query': query,
            'conversation_history': [],
            'user_profile': {},
            'mood': 'neutral',
            'topics': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Obtener historial reciente de conversación
            if memory_manager and hasattr(memory_manager, 'get_recent_conversations'):
                recent = await memory_manager.get_recent_conversations(limit=5)
                context['conversation_history'] = recent
            
            # Análisis básico del mood de la conversación
            context['mood'] = self._analyze_mood(query)
            
            # Extraer temas de la consulta
            context['topics'] = self._extract_topics(query)
                
        except Exception as e:
            logger.error(f"Error building chat context: {e}")
            
        return context
    
    def _analyze_mood(self, query: str) -> str:
        """Analiza el mood básico de la consulta"""
        positive_words = ['bien', 'bueno', 'excelente', 'genial', 'perfecto', 'gracias']
        negative_words = ['mal', 'error', 'problema', 'fallo', 'difícil', 'complicado']
        
        query_lower = query.lower()
        positive_count = sum(1 for word in positive_words if word in query_lower)
        negative_count = sum(1 for word in negative_words if word in query_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        return 'neutral'
    
    def _extract_topics(self, query: str) -> List[str]:
        """Extrae temas básicos de la consulta"""
        topics = []
        topic_keywords = {
            'saludo': ['hola', 'buenos', 'buenas', 'saludos'],
            'despedida': ['adiós', 'hasta', 'nos vemos', 'chau'],
            'agradecimiento': ['gracias', 'gracias', 'agradezco'],
            'estado': ['cómo estás', 'qué tal', 'cómo te va']
        }
        
        query_lower = query.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ['conversacion_general']