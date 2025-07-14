"""
Núcleo del Agente Mitosis Mejorado con Capacidades Cognitivas Avanzadas
Incluye aprendizaje reforzado, auto-mejora de prompts y razonamiento avanzado
"""

import logging
import json
import time
import os
import random
import numpy as np
from typing import List, Dict, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum
from collections import defaultdict, deque

from agent_core import MitosisAgent, AgentConfig, AgentState
from enhanced_memory_manager import EnhancedMemoryManager, VectorKnowledgeItem
from enhanced_task_manager import EnhancedTaskManager
from model_manager import ModelManager, UnifiedModel, ModelProvider
from enhanced_prompts import EnhancedPromptManager, PromptType

@dataclass
class ReflectionEntry:
    """Entrada de reflexión para aprendizaje"""
    id: str
    action: str
    expected_outcome: str
    actual_outcome: str
    success: bool
    confidence: float
    context: Dict[str, Any]
    timestamp: float
    learned_patterns: List[str] = None
    
    def __post_init__(self):
        if self.learned_patterns is None:
            self.learned_patterns = []

@dataclass
class PromptTemplate:
    """Plantilla de prompt mejorada"""
    id: str
    name: str
    template: str
    variables: List[str]
    success_rate: float = 0.0
    usage_count: int = 0
    average_quality_score: float = 0.0
    context_types: List[str] = None
    
    def __post_init__(self):
        if self.context_types is None:
            self.context_types = []

@dataclass
class LearningMetrics:
    """Métricas de aprendizaje del agente"""
    total_reflections: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    success_rate: float = 0.0
    improvement_rate: float = 0.0
    knowledge_growth: float = 0.0
    prompt_optimization_score: float = 0.0

class CognitiveMode(Enum):
    """Modos cognitivos del agente"""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    PRACTICAL = "practical"
    REFLECTIVE = "reflective"
    ADAPTIVE = "adaptive"

class EnhancedMitosisAgent(MitosisAgent):
    """Agente Mitosis mejorado con capacidades cognitivas avanzadas"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        # Usar gestores mejorados
        if config is None:
            config = AgentConfig()
        
        # Inicializar componentes base
        super().__init__(config)
        
        # Reemplazar con versiones mejoradas
        self.memory_manager = EnhancedMemoryManager(
            db_path=config.memory_db_path,
            max_short_term_messages=config.max_short_term_messages
        )
        
        self.task_manager = EnhancedTaskManager(self.memory_manager)
        
        # Nuevas capacidades cognitivas
        self.reflection_history: List[ReflectionEntry] = []
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.learning_metrics = LearningMetrics()
        self.cognitive_mode = CognitiveMode.ADAPTIVE
        
        # Configuración de aprendizaje
        self.learning_enabled = True
        self.reflection_threshold = 0.7  # Umbral para reflexión automática
        self.prompt_optimization_enabled = True
        self.max_reflection_history = 1000
        
        # Patrones aprendidos
        self.learned_patterns: Dict[str, float] = {}  # patrón -> confianza
        self.action_outcomes: Dict[str, List[bool]] = defaultdict(list)  # acción -> resultados
        
        # Inicializar plantillas de prompts
        self._initialize_prompt_templates()
        
        # Estadísticas cognitivas
        self.cognitive_stats = {
            "reflections_performed": 0,
            "patterns_learned": 0,
            "prompts_optimized": 0,
            "cognitive_mode_changes": 0,
            "successful_adaptations": 0
        }
        
        self.logger.info(f"Enhanced Mitosis Agent inicializado con capacidades cognitivas avanzadas")
    
    def _initialize_prompt_templates(self):
        """Inicializa plantillas de prompts optimizables"""
        templates = [
            PromptTemplate(
                id="task_planning",
                name="Planificación de Tareas",
                template="""Como un agente inteligente, necesito planificar la siguiente tarea:

Objetivo: {goal}
Descripción: {description}
Contexto: {context}

Por favor, crea un plan detallado con fases específicas, considerando:
1. Dependencias entre fases
2. Herramientas necesarias
3. Criterios de éxito
4. Estimación de tiempo

Responde en formato JSON con la estructura de fases.""",
                variables=["goal", "description", "context"],
                context_types=["task_planning"]
            ),
            PromptTemplate(
                id="reflection_analysis",
                name="Análisis de Reflexión",
                template="""Analiza la siguiente acción y su resultado:

Acción realizada: {action}
Resultado esperado: {expected}
Resultado actual: {actual}
Contexto: {context}

Evalúa:
1. ¿Fue exitosa la acción? (Sí/No)
2. ¿Qué patrones puedes identificar?
3. ¿Qué se puede aprender de esto?
4. ¿Cómo mejorar en el futuro?

Proporciona insights específicos y accionables.""",
                variables=["action", "expected", "actual", "context"],
                context_types=["reflection", "learning"]
            ),
            PromptTemplate(
                id="problem_solving",
                name="Resolución de Problemas",
                template="""Enfrentando el siguiente problema:

Problema: {problem}
Contexto disponible: {context}
Recursos disponibles: {resources}
Restricciones: {constraints}

Modo cognitivo actual: {cognitive_mode}

Desarrolla una solución considerando:
1. Análisis del problema
2. Opciones disponibles
3. Evaluación de riesgos
4. Plan de implementación
5. Métricas de éxito""",
                variables=["problem", "context", "resources", "constraints", "cognitive_mode"],
                context_types=["problem_solving", "analysis"]
            )
        ]
        
        for template in templates:
            self.prompt_templates[template.id] = template
    
    def process_user_message_enhanced(self, message: str, 
                                    context: Optional[Dict[str, Any]] = None) -> str:
        """Procesa un mensaje del usuario con capacidades cognitivas mejoradas"""
        try:
            self.state = AgentState.THINKING
            self.stats["messages_processed"] += 1
            
            # Determinar modo cognitivo apropiado
            self._adapt_cognitive_mode(message, context)
            
            # Añadir mensaje del usuario a la memoria
            self.memory_manager.add_message("user", message, context or {})
            
            # Buscar patrones aprendidos relevantes
            relevant_patterns = self._find_relevant_patterns(message)
            
            # Generar prompt optimizado
            optimized_prompt = self._generate_optimized_prompt(
                "user_interaction", 
                {
                    "message": message,
                    "context": context or {},
                    "cognitive_mode": self.cognitive_mode.value,
                    "relevant_patterns": relevant_patterns
                }
            )
            
            # Seleccionar mejor modelo considerando el modo cognitivo
            best_model = self._select_model_for_cognitive_mode()
            
            if not best_model:
                return "Error: No hay modelos disponibles para procesar la solicitud."
            
            # Preparar contexto de conversación con búsqueda semántica
            conversation_context = self._get_enhanced_conversation_context(message)
            
            messages = [
                {"role": "system", "content": optimized_prompt},
                {"role": "user", "content": f"Contexto: {conversation_context}\n\nMensaje: {message}"}
            ]
            
            # Generar respuesta
            response = self.model_manager.chat_completion(
                messages=messages,
                model=best_model,
                max_tokens=1000,
                temperature=self._get_temperature_for_mode()
            )
            
            if not response:
                return "Error: No se pudo generar una respuesta."
            
            # Añadir respuesta a la memoria
            self.memory_manager.add_message(
                "assistant", 
                response,
                {
                    "model_used": best_model.name,
                    "cognitive_mode": self.cognitive_mode.value,
                    "patterns_used": relevant_patterns
                }
            )
            
            # Reflexión automática si es necesario
            if self.learning_enabled:
                self._auto_reflect_on_interaction(message, response, context)
            
            # Extraer conocimiento mejorado
            self._extract_enhanced_knowledge(message, response)
            
            self.state = AgentState.IDLE
            return response
            
        except Exception as e:
            self.logger.error(f"Error al procesar mensaje del usuario: {e}")
            self.state = AgentState.ERROR
            return f"Error interno: {str(e)}"
    
    def _adapt_cognitive_mode(self, message: str, context: Optional[Dict[str, Any]]):
        """Adapta el modo cognitivo basándose en el mensaje y contexto"""
        message_lower = message.lower()
        
        # Determinar modo cognitivo apropiado
        if any(word in message_lower for word in ["analizar", "evaluar", "comparar", "estudiar"]):
            new_mode = CognitiveMode.ANALYTICAL
        elif any(word in message_lower for word in ["crear", "diseñar", "inventar", "imaginar"]):
            new_mode = CognitiveMode.CREATIVE
        elif any(word in message_lower for word in ["hacer", "ejecutar", "implementar", "resolver"]):
            new_mode = CognitiveMode.PRACTICAL
        elif any(word in message_lower for word in ["reflexionar", "aprender", "mejorar", "evaluar"]):
            new_mode = CognitiveMode.REFLECTIVE
        else:
            new_mode = CognitiveMode.ADAPTIVE
        
        if new_mode != self.cognitive_mode:
            self.cognitive_mode = new_mode
            self.cognitive_stats["cognitive_mode_changes"] += 1
            self.logger.info(f"Modo cognitivo cambiado a: {new_mode.value}")
    
    def _select_model_for_cognitive_mode(self) -> Optional[UnifiedModel]:
        """Selecciona el modelo más apropiado para el modo cognitivo actual"""
        if self.cognitive_mode == CognitiveMode.ANALYTICAL:
            return self.model_manager.select_best_model("analysis")
        elif self.cognitive_mode == CognitiveMode.CREATIVE:
            return self.model_manager.select_best_model("chat")  # Modelos más creativos
        elif self.cognitive_mode == CognitiveMode.PRACTICAL:
            return self.model_manager.select_best_model("code")
        else:
            return self.model_manager.select_best_model("general")
    
    def _get_temperature_for_mode(self) -> float:
        """Obtiene la temperatura apropiada para el modo cognitivo"""
        temperature_map = {
            CognitiveMode.ANALYTICAL: 0.3,
            CognitiveMode.CREATIVE: 0.8,
            CognitiveMode.PRACTICAL: 0.5,
            CognitiveMode.REFLECTIVE: 0.4,
            CognitiveMode.ADAPTIVE: 0.6
        }
        return temperature_map.get(self.cognitive_mode, 0.6)
    
    def _find_relevant_patterns(self, message: str) -> List[str]:
        """Encuentra patrones aprendidos relevantes para el mensaje"""
        relevant_patterns = []
        message_words = set(message.lower().split())
        
        for pattern, confidence in self.learned_patterns.items():
            pattern_words = set(pattern.lower().split())
            overlap = len(message_words & pattern_words) / len(pattern_words)
            
            if overlap > 0.3 and confidence > 0.6:  # Umbral de relevancia
                relevant_patterns.append(pattern)
        
        return relevant_patterns[:5]  # Limitar a los 5 más relevantes
    
    def _generate_optimized_prompt(self, prompt_type: str, variables: Dict[str, Any]) -> str:
        """Genera un prompt optimizado basándose en el historial de éxito"""
        # Buscar plantilla apropiada
        template = None
        for template_id, tmpl in self.prompt_templates.items():
            if prompt_type in tmpl.context_types:
                template = tmpl
                break
        
        if not template:
            # Prompt genérico
            return f"Como un agente inteligente en modo {self.cognitive_mode.value}, responde a la siguiente solicitud de manera útil y precisa."
        
        # Rellenar variables de la plantilla
        try:
            formatted_prompt = template.template.format(**variables)
            template.usage_count += 1
            return formatted_prompt
        except KeyError as e:
            self.logger.warning(f"Variable faltante en plantilla {template.id}: {e}")
            return template.template
    
    def _get_enhanced_conversation_context(self, current_message: str) -> str:
        """Obtiene contexto de conversación mejorado con búsqueda semántica"""
        # Búsqueda semántica en la base de conocimiento
        relevant_knowledge = self.memory_manager.search_knowledge_semantic(
            current_message, n_results=3, min_confidence=0.6
        )
        
        # Contexto de conversación reciente
        recent_context = self.memory_manager.get_conversation_context(max_tokens=2000)
        
        # Combinar contextos
        knowledge_context = ""
        if relevant_knowledge:
            knowledge_items = [f"- {item.content}" for item in relevant_knowledge]
            knowledge_context = f"Conocimiento relevante:\n" + "\n".join(knowledge_items)
        
        return f"{recent_context}\n\n{knowledge_context}"
    
    def _auto_reflect_on_interaction(self, user_message: str, agent_response: str, 
                                   context: Optional[Dict[str, Any]]):
        """Reflexión automática sobre la interacción"""
        # Evaluar si la respuesta fue apropiada (simplificado)
        response_quality = self._evaluate_response_quality(user_message, agent_response)
        
        if response_quality < self.reflection_threshold:
            # Realizar reflexión
            reflection = self.enhanced_reflect_on_action(
                action=f"Responder a: {user_message}",
                result=agent_response,
                expected="Respuesta útil y relevante",
                context=context or {}
            )
            
            self.cognitive_stats["reflections_performed"] += 1
    
    def _evaluate_response_quality(self, user_message: str, agent_response: str) -> float:
        """Evalúa la calidad de una respuesta (simplificado)"""
        # Métricas simples de calidad
        quality_score = 0.5  # Base
        
        # Longitud apropiada
        if 50 <= len(agent_response) <= 1000:
            quality_score += 0.2
        
        # Relevancia (palabras clave compartidas)
        user_words = set(user_message.lower().split())
        response_words = set(agent_response.lower().split())
        overlap = len(user_words & response_words) / max(len(user_words), 1)
        quality_score += overlap * 0.3
        
        return min(quality_score, 1.0)
    
    def enhanced_reflect_on_action(self, action: str, result: str, expected: str,
                                 context: Optional[Dict[str, Any]] = None) -> ReflectionEntry:
        """Reflexión mejorada sobre una acción con aprendizaje"""
        try:
            self.state = AgentState.REFLECTING
            
            # Crear entrada de reflexión
            reflection_id = f"reflection_{int(time.time())}_{len(self.reflection_history)}"
            
            # Generar prompt de reflexión optimizado
            reflection_prompt = self._generate_optimized_prompt(
                "reflection_analysis",
                {
                    "action": action,
                    "expected": expected,
                    "actual": result,
                    "context": json.dumps(context or {})
                }
            )
            
            # Usar modelo analítico para reflexión
            reflection_model = self.model_manager.select_best_model("analysis")
            
            if reflection_model:
                reflection_response = self.model_manager.generate_response(
                    reflection_prompt,
                    model=reflection_model,
                    max_tokens=800,
                    temperature=0.4
                )
                
                # Evaluar éxito de la acción
                success = self._evaluate_action_success(action, result, expected)
                
                # Extraer patrones aprendidos
                learned_patterns = self._extract_patterns_from_reflection(
                    action, result, reflection_response
                )
                
                # Crear entrada de reflexión
                reflection_entry = ReflectionEntry(
                    id=reflection_id,
                    action=action,
                    expected_outcome=expected,
                    actual_outcome=result,
                    success=success,
                    confidence=0.8,  # Simplificado
                    context=context or {},
                    timestamp=time.time(),
                    learned_patterns=learned_patterns
                )
                
                # Añadir a historial
                self.reflection_history.append(reflection_entry)
                
                # Mantener límite de historial
                if len(self.reflection_history) > self.max_reflection_history:
                    self.reflection_history.pop(0)
                
                # Actualizar patrones aprendidos
                self._update_learned_patterns(learned_patterns, success)
                
                # Actualizar métricas de aprendizaje
                self._update_learning_metrics(success)
                
                # Guardar reflexión en memoria
                self.memory_manager.add_knowledge_enhanced(
                    content=f"Reflexión: {action} -> {reflection_response}",
                    category="reflection",
                    source="agent_reflection",
                    confidence=0.8,
                    tags=["reflection", "learning", "self_improvement"]
                )
                
                self.state = AgentState.IDLE
                return reflection_entry
            
        except Exception as e:
            self.logger.error(f"Error en reflexión mejorada: {e}")
            self.state = AgentState.ERROR
        
        # Reflexión fallback
        return ReflectionEntry(
            id=reflection_id,
            action=action,
            expected_outcome=expected,
            actual_outcome=result,
            success=False,
            confidence=0.5,
            context=context or {},
            timestamp=time.time()
        )
    
    def _evaluate_action_success(self, action: str, result: str, expected: str) -> bool:
        """Evalúa si una acción fue exitosa"""
        # Evaluación simplificada basada en palabras clave
        success_indicators = ["exitoso", "completado", "correcto", "funciona", "resuelto"]
        failure_indicators = ["error", "fallo", "incorrecto", "problema", "falló"]
        
        result_lower = result.lower()
        
        success_score = sum(1 for indicator in success_indicators if indicator in result_lower)
        failure_score = sum(1 for indicator in failure_indicators if indicator in result_lower)
        
        return success_score > failure_score
    
    def _extract_patterns_from_reflection(self, action: str, result: str, 
                                        reflection: str) -> List[str]:
        """Extrae patrones de una reflexión"""
        patterns = []
        
        # Patrones simples basados en palabras clave
        if "siempre" in reflection.lower():
            patterns.append(f"Patrón: {action} -> resultado consistente")
        
        if "cuando" in reflection.lower() and "entonces" in reflection.lower():
            patterns.append(f"Patrón condicional identificado en: {action}")
        
        if "mejorar" in reflection.lower():
            patterns.append(f"Área de mejora: {action}")
        
        return patterns
    
    def _update_learned_patterns(self, patterns: List[str], success: bool):
        """Actualiza los patrones aprendidos"""
        confidence_delta = 0.1 if success else -0.05
        
        for pattern in patterns:
            if pattern in self.learned_patterns:
                self.learned_patterns[pattern] = min(1.0, 
                    max(0.0, self.learned_patterns[pattern] + confidence_delta))
            else:
                self.learned_patterns[pattern] = 0.6 if success else 0.4
                self.cognitive_stats["patterns_learned"] += 1
    
    def _update_learning_metrics(self, success: bool):
        """Actualiza las métricas de aprendizaje"""
        self.learning_metrics.total_reflections += 1
        
        if success:
            self.learning_metrics.successful_actions += 1
        else:
            self.learning_metrics.failed_actions += 1
        
        # Calcular tasa de éxito
        total_actions = (self.learning_metrics.successful_actions + 
                        self.learning_metrics.failed_actions)
        if total_actions > 0:
            self.learning_metrics.success_rate = (
                self.learning_metrics.successful_actions / total_actions
            )
        
        # Calcular tasa de mejora (simplificado)
        if len(self.reflection_history) > 10:
            recent_successes = sum(1 for r in self.reflection_history[-10:] if r.success)
            self.learning_metrics.improvement_rate = recent_successes / 10
    
    def optimize_prompt_template(self, template_id: str, success_feedback: bool,
                               quality_score: float = 0.5):
        """Optimiza una plantilla de prompt basándose en el feedback"""
        if not self.prompt_optimization_enabled:
            return
        
        template = self.prompt_templates.get(template_id)
        if not template:
            return
        
        # Actualizar métricas de la plantilla
        template.usage_count += 1
        
        # Actualizar tasa de éxito
        if template.usage_count == 1:
            template.success_rate = 1.0 if success_feedback else 0.0
        else:
            # Promedio móvil
            alpha = 0.1  # Factor de aprendizaje
            template.success_rate = (
                (1 - alpha) * template.success_rate + 
                alpha * (1.0 if success_feedback else 0.0)
            )
        
        # Actualizar puntuación de calidad
        template.average_quality_score = (
            (template.average_quality_score * (template.usage_count - 1) + quality_score) /
            template.usage_count
        )
        
        # Si el rendimiento es bajo, marcar para optimización
        if template.success_rate < 0.6 and template.usage_count > 5:
            self._schedule_prompt_optimization(template_id)
    
    def _schedule_prompt_optimization(self, template_id: str):
        """Programa la optimización de una plantilla de prompt"""
        # En una implementación completa, esto podría usar un LLM para reescribir la plantilla
        self.logger.info(f"Plantilla {template_id} programada para optimización")
        self.cognitive_stats["prompts_optimized"] += 1
    
    def _extract_enhanced_knowledge(self, user_message: str, agent_response: str):
        """Extrae conocimiento mejorado de la interacción"""
        # Identificar si la interacción contiene información valiosa
        knowledge_indicators = [
            "aprendí", "descubrí", "encontré", "resultado", "solución",
            "importante", "clave", "fundamental", "técnica", "método",
            "patrón", "regla", "principio"
        ]
        
        combined_text = (user_message + " " + agent_response).lower()
        
        if any(indicator in combined_text for indicator in knowledge_indicators):
            # Usar búsqueda semántica para evitar duplicados
            similar_knowledge = self.memory_manager.search_knowledge_semantic(
                user_message, n_results=3, min_confidence=0.8
            )
            
            # Solo añadir si no hay conocimiento muy similar
            if not similar_knowledge or len(similar_knowledge) == 0:
                knowledge_content = (
                    f"Interacción cognitiva (modo: {self.cognitive_mode.value}): "
                    f"Usuario: '{user_message[:100]}...' -> "
                    f"Agente: '{agent_response[:200]}...'"
                )
                
                self.memory_manager.add_knowledge_enhanced(
                    content=knowledge_content,
                    category="cognitive_interaction",
                    source="enhanced_user_interaction",
                    confidence=0.7,
                    tags=["interaction", "cognitive", self.cognitive_mode.value]
                )
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Obtiene el estado mejorado del agente"""
        base_status = self.get_status()
        
        enhanced_status = {
            **base_status,
            "cognitive_capabilities": {
                "current_mode": self.cognitive_mode.value,
                "learning_enabled": self.learning_enabled,
                "reflection_threshold": self.reflection_threshold,
                "prompt_optimization_enabled": self.prompt_optimization_enabled
            },
            "learning_metrics": asdict(self.learning_metrics),
            "cognitive_stats": self.cognitive_stats.copy(),
            "learned_patterns_count": len(self.learned_patterns),
            "reflection_history_size": len(self.reflection_history),
            "prompt_templates_count": len(self.prompt_templates)
        }
        
        return enhanced_status

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear agente mejorado
    enhanced_agent = EnhancedMitosisAgent()
    
    print("🧠 Probando Enhanced Mitosis Agent...")
    
    # Iniciar sesión
    session_id = enhanced_agent.start_session()
    print(f"🚀 Sesión iniciada: {session_id}")
    
    # Procesar mensaje con capacidades mejoradas
    response = enhanced_agent.process_user_message_enhanced(
        "Analiza cómo puedo mejorar mi productividad en el trabajo"
    )
    print(f"🤖 Respuesta: {response[:200]}...")
    
    # Realizar reflexión manual
    reflection = enhanced_agent.enhanced_reflect_on_action(
        action="Analizar productividad",
        result=response,
        expected="Consejos útiles y específicos",
        context={"domain": "productivity", "user_type": "professional"}
    )
    print(f"🔍 Reflexión realizada: {reflection.success}")
    
    # Obtener estado mejorado
    status = enhanced_agent.get_enhanced_status()
    print(f"📊 Estado cognitivo:")
    print(f"  Modo actual: {status['cognitive_capabilities']['current_mode']}")
    print(f"  Patrones aprendidos: {status['learned_patterns_count']}")
    print(f"  Reflexiones realizadas: {status['cognitive_stats']['reflections_performed']}")
    print(f"  Tasa de éxito: {status['learning_metrics']['success_rate']:.2f}")
    
    print("✅ Pruebas completadas")

