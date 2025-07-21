"""
Sistema de Clasificación de Intenciones Basado en LLM
Reemplaza la detección heurística simple con un clasificador inteligente

Implementa las especificaciones completas del NEWUPGRADE.md Sección 4
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import logging
import re
import time
from datetime import datetime

class IntentionType(Enum):
    """Tipos de intención identificables por el clasificador"""
    CASUAL_CONVERSATION = "casual_conversation"
    INFORMATION_REQUEST = "information_request"
    SIMPLE_TASK = "simple_task"
    COMPLEX_TASK = "complex_task"
    TASK_MANAGEMENT = "task_management"
    AGENT_CONFIGURATION = "agent_configuration"
    UNCLEAR = "unclear"

@dataclass
class IntentionResult:
    """Resultado de la clasificación de intención"""
    intention_type: IntentionType
    confidence: float
    reasoning: str
    extracted_entities: Dict[str, Any]
    suggested_action: str
    requires_clarification: bool = False
    clarification_questions: List[str] = None

class IntentionClassifier:
    """Clasificador de intenciones usando LLM dedicado"""
    
    def __init__(self, model_manager, memory_manager):
        self.model_manager = model_manager
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(__name__)
        
        # Configuración del clasificador
        self.classification_model = None
        self.confidence_threshold = 0.7
        self.max_retries = 2
        
        # Plantilla de prompt especializada
        self.classification_prompt_template = self._create_classification_prompt_template()
        
        # Cache de resultados para optimización
        self.result_cache = {}
        self.cache_ttl = 300  # 5 minutos
        
        self.logger.info("IntentionClassifier inicializado correctamente")
        
    def _create_classification_prompt_template(self) -> str:
        """Crea la plantilla de prompt para clasificación de intenciones"""
        return """Eres un clasificador de intenciones especializado. Tu tarea es analizar el mensaje del usuario y determinar su intención principal.

MENSAJE DEL USUARIO: {user_message}

CONTEXTO DE CONVERSACIÓN RECIENTE:
{conversation_context}

TAREAS ACTIVAS DEL USUARIO:
{active_tasks}

INSTRUCCIONES:
Analiza el mensaje y clasifícalo en una de estas categorías:

1. **casual_conversation**: Saludos, charla informal, preguntas generales sin solicitud de acción
2. **information_request**: Preguntas que requieren búsqueda o consulta de información específica
3. **simple_task**: Solicitudes de acciones simples que no requieren planificación compleja
4. **complex_task**: Solicitudes que requieren planificación multi-fase y múltiples herramientas
5. **task_management**: Comandos para gestionar tareas existentes (pausar, reanudar, consultar estado)
6. **agent_configuration**: Solicitudes para cambiar configuración o comportamiento del agente
7. **unclear**: Mensaje ambiguo que requiere clarificación

FORMATO DE RESPUESTA (JSON obligatorio):
{{
    "intention_type": "tipo_de_intencion",
    "confidence": 0.95,
    "reasoning": "Explicación detallada del por qué se clasificó así",
    "extracted_entities": {{
        "task_title": "título si es una tarea",
        "task_description": "descripción si es una tarea",
        "mentioned_tools": ["herramienta1", "herramienta2"],
        "time_constraints": "restricciones de tiempo si las hay",
        "priority_level": "alta/media/baja si se menciona"
    }},
    "suggested_action": "Acción recomendada para el agente",
    "requires_clarification": false,
    "clarification_questions": []
}}

EJEMPLOS:

Usuario: "Hola, ¿cómo estás?"
Respuesta: {{"intention_type": "casual_conversation", "confidence": 0.98, "reasoning": "Saludo simple sin solicitud de acción", "extracted_entities": {{}}, "suggested_action": "Responder cordialmente", "requires_clarification": false}}

Usuario: "Necesito crear un dashboard de ventas con datos de los últimos 6 meses"
Respuesta: {{"intention_type": "complex_task", "confidence": 0.92, "reasoning": "Solicitud de creación que requiere múltiples pasos: obtener datos, procesarlos, crear visualizaciones", "extracted_entities": {{"task_title": "Dashboard de ventas", "task_description": "Dashboard con datos de últimos 6 meses", "time_constraints": "últimos 6 meses"}}, "suggested_action": "Crear plan de tarea complejo", "requires_clarification": false}}

Usuario: "¿Cuál es el estado de mi tarea de análisis?"
Respuesta: {{"intention_type": "task_management", "confidence": 0.95, "reasoning": "Consulta sobre el estado de una tarea existente", "extracted_entities": {{"task_reference": "tarea de análisis"}}, "suggested_action": "Consultar estado de tareas activas", "requires_clarification": false}}

ANALIZA EL MENSAJE Y RESPONDE SOLO CON EL JSON:"""

    def classify_intention(self, user_message: str, conversation_context: str = "", 
                          active_tasks: List[Dict] = None) -> IntentionResult:
        """Clasifica la intención del mensaje del usuario"""
        if active_tasks is None:
            active_tasks = []
        
        # Verificar cache
        cache_key = self._generate_cache_key(user_message, conversation_context)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            self.logger.info(f"Usando resultado cacheado para: {user_message[:50]}...")
            return cached_result
        
        try:
            # Seleccionar modelo optimizado para clasificación
            classification_model = self.model_manager.select_best_model(
                task_type="analysis",
                max_cost=0.005  # Usar modelo económico para clasificación
            )
            
            if not classification_model:
                self.logger.error("No hay modelo disponible para clasificación")
                return self._create_fallback_result(user_message)
            
            # Preparar contexto
            tasks_summary = self._format_active_tasks(active_tasks)
            
            # Generar prompt
            prompt = self.classification_prompt_template.format(
                user_message=user_message,
                conversation_context=conversation_context[:1000],  # Limitar contexto
                active_tasks=tasks_summary
            )
            
            # Realizar clasificación con reintentos
            for attempt in range(self.max_retries + 1):
                try:
                    self.logger.info(f"Clasificando intención (intento {attempt + 1}): {user_message[:50]}...")
                    
                    response = self.model_manager.generate_response(
                        prompt,
                        model=classification_model,
                        max_tokens=500,
                        temperature=0.1  # Temperatura muy baja para consistencia
                    )
                    
                    if response:
                        result = self._parse_classification_response(response)
                        if result and result.confidence >= self.confidence_threshold:
                            self.logger.info(f"Intención clasificada: {result.intention_type.value} (confianza: {result.confidence})")
                            # Cachear resultado exitoso
                            self._cache_result(cache_key, result)
                            return result
                        elif result:
                            self.logger.warning(f"Clasificación con baja confianza: {result.confidence}")
                            if result.confidence > 0.5:  # Umbral mínimo
                                self._cache_result(cache_key, result)
                                return result
                    
                except Exception as e:
                    self.logger.error(f"Error en intento {attempt + 1} de clasificación: {e}")
                    if attempt == self.max_retries:
                        break
            
            # Si todos los intentos fallan, usar resultado de respaldo
            fallback_result = self._create_fallback_result(user_message)
            self._cache_result(cache_key, fallback_result)
            return fallback_result
            
        except Exception as e:
            self.logger.error(f"Error crítico en clasificación de intención: {e}")
            return self._create_fallback_result(user_message)
    
    def _parse_classification_response(self, response: str) -> Optional[IntentionResult]:
        """Parsea la respuesta JSON del clasificador"""
        try:
            # Limpiar respuesta
            response = response.strip()
            
            # Buscar JSON en la respuesta
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                # Validar campos requeridos
                required_fields = ['intention_type', 'confidence', 'reasoning', 'suggested_action']
                if not all(field in data for field in required_fields):
                    self.logger.error("Respuesta JSON incompleta")
                    return None
                
                # Crear resultado
                try:
                    intention_type = IntentionType(data['intention_type'])
                except ValueError:
                    self.logger.error(f"Tipo de intención inválido: {data['intention_type']}")
                    intention_type = IntentionType.UNCLEAR
                
                return IntentionResult(
                    intention_type=intention_type,
                    confidence=float(data['confidence']),
                    reasoning=data['reasoning'],
                    extracted_entities=data.get('extracted_entities', {}),
                    suggested_action=data['suggested_action'],
                    requires_clarification=data.get('requires_clarification', False),
                    clarification_questions=data.get('clarification_questions', [])
                )
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.error(f"Error parseando respuesta de clasificación: {e}")
            return None
        
        return None
    
    def _format_active_tasks(self, active_tasks: List[Dict]) -> str:
        """Formatea las tareas activas para el contexto"""
        if not active_tasks:
            return "No hay tareas activas"
        
        formatted_tasks = []
        for task in active_tasks[:3]:  # Limitar a 3 tareas más recientes
            formatted_tasks.append(f"- {task.get('title', 'Sin título')}: {task.get('status', 'desconocido')}")
        
        return "\n".join(formatted_tasks)
    
    def _create_fallback_result(self, user_message: str) -> IntentionResult:
        """Crea un resultado de respaldo cuando la clasificación falla"""
        # Heurística simple basada en palabras clave
        message_lower = user_message.lower()
        
        # Detectar saludos
        greetings = ['hola', 'hello', 'hi', 'buenos días', 'buenas tardes', 'buenas noches', 
                    'qué tal', 'cómo estás', 'saludos', 'hey']
        if any(greeting in message_lower for greeting in greetings) and len(user_message.split()) <= 5:
            return IntentionResult(
                intention_type=IntentionType.CASUAL_CONVERSATION,
                confidence=0.8,
                reasoning="Detectado como saludo por heurística de respaldo",
                extracted_entities={},
                suggested_action="Responder cordialmente"
            )
        
        # Detectar preguntas de información
        question_indicators = ['qué', 'cómo', 'cuándo', 'dónde', 'por qué', 'cuál', 'quién', '?']
        if any(indicator in message_lower for indicator in question_indicators):
            return IntentionResult(
                intention_type=IntentionType.INFORMATION_REQUEST,
                confidence=0.7,
                reasoning="Detectado como pregunta por heurística de respaldo",
                extracted_entities={},
                suggested_action="Buscar información y responder"
            )
        
        # Detectar solicitudes de tareas
        task_keywords = ['crear', 'hacer', 'generar', 'desarrollar', 'construir', 'escribir', 
                        'analizar', 'diseñar', 'implementar', 'buscar', 'investigar', 'estudiar']
        complex_indicators = ['plan', 'proyecto', 'sistema', 'aplicación', 'dashboard', 
                             'informe', 'análisis', 'estrategia', 'proceso']
        
        has_task_keyword = any(keyword in message_lower for keyword in task_keywords)
        has_complex_indicator = any(indicator in message_lower for indicator in complex_indicators)
        
        if has_task_keyword:
            if has_complex_indicator or len(user_message.split()) > 10:
                return IntentionResult(
                    intention_type=IntentionType.COMPLEX_TASK,
                    confidence=0.6,
                    reasoning="Detectado como tarea compleja por heurística de respaldo",
                    extracted_entities={"task_title": user_message[:50]},
                    suggested_action="Crear plan de tarea complejo"
                )
            else:
                return IntentionResult(
                    intention_type=IntentionType.SIMPLE_TASK,
                    confidence=0.6,
                    reasoning="Detectado como tarea simple por heurística de respaldo",
                    extracted_entities={"task_title": user_message[:50]},
                    suggested_action="Procesar como tarea simple"
                )
        
        # Detectar gestión de tareas
        task_management_keywords = ['estado', 'progreso', 'pausar', 'reanudar', 'cancelar', 'completar']
        if any(keyword in message_lower for keyword in task_management_keywords):
            return IntentionResult(
                intention_type=IntentionType.TASK_MANAGEMENT,
                confidence=0.7,
                reasoning="Detectado como gestión de tareas por heurística de respaldo",
                extracted_entities={},
                suggested_action="Consultar y gestionar tareas"
            )
        
        # Por defecto, tratar como conversación
        return IntentionResult(
            intention_type=IntentionType.CASUAL_CONVERSATION,
            confidence=0.5,
            reasoning="Clasificación de respaldo - tratado como conversación",
            extracted_entities={},
            suggested_action="Responder como conversación general"
        )
    
    def _generate_cache_key(self, message: str, context: str) -> str:
        """Genera clave de cache para el mensaje"""
        # Usar hash simple del mensaje y contexto
        import hashlib
        combined = f"{message[:100]}{context[:100]}"  # Limitar para cache
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[IntentionResult]:
        """Obtiene resultado del cache si es válido"""
        if cache_key in self.result_cache:
            cached_data = self.result_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['result']
            else:
                # Eliminar entrada expirada
                del self.result_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: IntentionResult):
        """Cachea un resultado de clasificación"""
        self.result_cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
        
        # Limitar tamaño del cache
        if len(self.result_cache) > 100:
            # Eliminar entradas más antiguas
            oldest_key = min(self.result_cache.keys(), 
                           key=lambda k: self.result_cache[k]['timestamp'])
            del self.result_cache[oldest_key]
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del clasificador"""
        return {
            'cache_size': len(self.result_cache),
            'cache_ttl': self.cache_ttl,
            'confidence_threshold': self.confidence_threshold,
            'max_retries': self.max_retries,
            'model_available': self.model_manager is not None
        }
    
    def clear_cache(self):
        """Limpia el cache de resultados"""
        self.result_cache.clear()
        self.logger.info("Cache de clasificación limpiado")

# Función de utilidad para crear instancia
def create_intention_classifier(model_manager, memory_manager):
    """Crea una instancia del clasificador de intenciones"""
    return IntentionClassifier(model_manager, memory_manager)