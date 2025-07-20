"""
Núcleo del Agente Mitosis Mejorado
Integra todos los componentes: modelos, memoria, tareas y prompts
"""

import logging
import json
import time
import os
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
import asyncio
from enum import Enum
import jsonschema
import re

from model_manager import ModelManager, UnifiedModel, ModelProvider
from memory_manager import MemoryManager, Message, TaskMemory, KnowledgeItem
from task_manager import TaskManager, Task, TaskPhase, TaskStatus
from enhanced_prompts import EnhancedPromptManager, PromptType

class AgentState(Enum):
    """Estados del agente"""
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    WAITING_USER = "waiting_user"
    ERROR = "error"

# Esquema JSON para validación de planes generados según UPGRADE.md
PLAN_SCHEMA = {
    "type": "object",
    "required": ["goal", "phases"],
    "properties": {
        "goal": {
            "type": "string",
            "minLength": 3
        },
        "phases": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10,
            "items": {
                "type": "object",
                "required": ["id", "title", "description", "required_capabilities"],
                "properties": {
                    "id": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "title": {
                        "type": "string",
                        "minLength": 5,
                        "maxLength": 100
                    },
                    "description": {
                        "type": "string", 
                        "minLength": 10,
                        "maxLength": 300
                    },
                    "required_capabilities": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["analysis", "web_search", "creation", "planning", "delivery", "processing", "synthesis", "general", "communication"]
                        }
                    },
                    "estimated_time": {
                        "type": "string"
                    },
                    "tool_name": {
                        "type": "string",
                        "enum": ["web_search", "file_write", "analysis", "creation", "shell_exec", "general"]
                    }
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

@dataclass
class AgentConfig:
    """Configuración del agente"""
    # Configuración de modelos
    ollama_url: str = "http://localhost:11434"
    openrouter_api_key: Optional[str] = None
    prefer_local_models: bool = True
    max_cost_per_1k_tokens: float = 0.01
    
    # Configuración de memoria
    memory_db_path: str = "mitosis_memory.db"
    max_short_term_messages: int = 50
    
    # Configuración de tareas
    max_concurrent_tasks: int = 1
    auto_retry_failed_phases: bool = True
    
    # Configuración de prompts
    max_context_tokens: int = 4000
    include_memory_context: bool = True
    
    # Configuración general
    agent_name: str = "Mitosis"
    debug_mode: bool = False
    log_level: str = "INFO"

class MitosisAgent:
    """Agente Mitosis mejorado con integración completa"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        
        # Configurar logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Estado del agente
        self.state = AgentState.IDLE
        self.current_session_id = None
        self.startup_time = time.time()
        
        # Inicializar componentes
        self._initialize_components()
        
        # Estadísticas
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_processed": 0,
            "models_used": set(),
            "uptime": 0
        }
        
        self.logger.info(f"Agente {self.config.agent_name} inicializado correctamente")
    
    def _initialize_components(self):
        """Inicializa todos los componentes del agente"""
        try:
            # Inicializar gestor de memoria
            self.memory_manager = MemoryManager(
                db_path=self.config.memory_db_path,
                max_short_term_messages=self.config.max_short_term_messages
            )
            
            # Inicializar gestor de tareas
            self.task_manager = TaskManager(self.memory_manager)
            self.task_manager.max_concurrent_tasks = self.config.max_concurrent_tasks
            self.task_manager.auto_retry_failed_phases = self.config.auto_retry_failed_phases
            
            # Inicializar gestor de modelos
            self.model_manager = ModelManager(
                ollama_url=self.config.ollama_url,
                openrouter_api_key=self.config.openrouter_api_key
            )
            self.model_manager.prefer_local = self.config.prefer_local_models
            
            # Inicializar gestor de prompts
            self.prompt_manager = EnhancedPromptManager(
                self.memory_manager, 
                self.task_manager
            )
            self.prompt_manager.max_context_tokens = self.config.max_context_tokens
            self.prompt_manager.include_memory_context = self.config.include_memory_context
            
            # Actualizar modelos disponibles
            self.model_manager.refresh_models()
            
            self.logger.info("Todos los componentes inicializados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al inicializar componentes: {e}")
            raise
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """Inicia una nueva sesión de conversación"""
        if session_id:
            self.current_session_id = session_id
        else:
            self.current_session_id = f"session_{int(time.time())}"
        
        # Limpiar memoria a corto plazo para nueva sesión
        self.memory_manager.clear_short_term_memory(persist=True)
        
        # Añadir mensaje de inicio de sesión
        self.memory_manager.add_message(
            "system", 
            f"Sesión iniciada: {self.current_session_id}",
            {"session_start": True, "timestamp": time.time()}
        )
        
        self.logger.info(f"Nueva sesión iniciada: {self.current_session_id}")
        return self.current_session_id
    
    def process_user_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Procesa un mensaje del usuario y genera una respuesta"""
        try:
            self.state = AgentState.THINKING
            self.stats["messages_processed"] += 1
            
            # Añadir mensaje del usuario a la memoria
            self.memory_manager.add_message("user", message, context or {})
            
            # Generar prompt del sistema con contexto
            system_prompt = self.prompt_manager.generate_system_prompt(
                context=f"Mensaje del usuario: {message}"
            )
            
            # Seleccionar mejor modelo para la respuesta
            best_model = self.model_manager.select_best_model(
                task_type="chat",
                max_cost=self.config.max_cost_per_1k_tokens
            )
            
            if not best_model:
                return "Error: No hay modelos disponibles para procesar la solicitud."
            
            # Cargar modelo si es necesario
            if not self.model_manager.load_model(best_model):
                return "Error: No se pudo cargar el modelo seleccionado."
            
            # Preparar mensajes para el modelo
            conversation_context = self.memory_manager.get_conversation_context(
                max_tokens=self.config.max_context_tokens // 2
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Contexto de conversación:\n{conversation_context}\n\nMensaje actual: {message}"}
            ]
            
            # Generar respuesta
            self.stats["models_used"].add(best_model.name)
            response = self.model_manager.chat_completion(
                messages=messages,
                model=best_model,
                max_tokens=1000,
                temperature=0.7
            )
            
            if not response:
                return "Error: No se pudo generar una respuesta."
            
            # Añadir respuesta a la memoria
            self.memory_manager.add_message(
                "assistant", 
                response,
                {"model_used": best_model.name, "provider": best_model.provider.value}
            )
            
            # Extraer conocimiento si es relevante
            self._extract_knowledge_from_conversation(message, response)
            
            self.state = AgentState.IDLE
            return response
            
        except Exception as e:
            self.logger.error(f"Error al procesar mensaje del usuario: {e}")
            self.state = AgentState.ERROR
            return f"Error interno: {str(e)}"
    
    def create_and_execute_task(self, title: str, description: str, goal: str,
                               auto_execute: bool = True) -> str:
        """
        Crea y opcionalmente ejecuta una nueva tarea con generación robusta de planes
        Implementa mejoras según UPGRADE.md Problema 1: Generación de Planes Genéricos
        """
        try:
            self.state = AgentState.PLANNING
            
            # Generar plan usando la nueva función robusta
            plan_data = self._generate_robust_plan_with_retries(title, description, goal)
            
            if not plan_data:
                return "Error: No se pudo generar un plan válido para la tarea."
            
            # Crear tarea
            task_id = self.task_manager.create_task(
                title=title,
                description=description,
                goal=goal,
                phases=plan_data.get("phases", []),
                context={"plan_response": plan_data.get("_original_response", ""), "ai_generated": True}
            )
            
            # Añadir información a la memoria
            self.memory_manager.add_knowledge(
                content=f"Tarea creada: {title} - {description}",
                category="task_planning",
                source="agent_planning",
                confidence=0.9,
                tags=["task", "planning"]
            )
            
            if auto_execute:
                # Iniciar ejecución de la tarea
                if self.task_manager.start_task(task_id):
                    self.state = AgentState.EXECUTING
                    return f"Tarea '{title}' creada e iniciada con ID: {task_id}"
                else:
                    return f"Tarea '{title}' creada con ID: {task_id}, pero no se pudo iniciar automáticamente."
            else:
                return f"Tarea '{title}' creada con ID: {task_id}. Usa start_task() para ejecutar."
            
        except Exception as e:
            self.logger.error(f"Error al crear y ejecutar tarea: {e}")
            self.state = AgentState.ERROR
            return f"Error al crear tarea: {str(e)}"
    
    def _generate_robust_plan_with_retries(self, title: str, description: str, goal: str, 
                                         max_attempts: int = 3) -> Optional[Dict[str, Any]]:
        """
        Genera un plan robusto con reintentos y validación de esquemas
        Implementa mejoras según UPGRADE.md Problema 1: Validación y Reintento Robusto
        """
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"Generando plan - Intento {attempt}/{max_attempts}")
                
                # Generar prompt específico según el intento
                if attempt == 1:
                    # Primera tentativa: prompt con ejemplos (few-shot learning)
                    planning_prompt = self._create_coercive_planning_prompt(title, description, goal)
                elif attempt == 2:
                    # Segunda tentativa: prompt con corrección específica
                    planning_prompt = self._create_correction_prompt(title, description, goal, last_error)
                else:
                    # Tercera tentativa: prompt simplificado de emergencia
                    planning_prompt = self._create_emergency_fallback_prompt(title, description, goal)
                
                # Seleccionar modelo optimizado para JSON
                planning_model = self.model_manager.select_best_model(
                    task_type="analysis",
                    max_cost=self.config.max_cost_per_1k_tokens,
                    preferred_capabilities=["json", "structured_output"]  # Priorizar modelos para JSON
                )
                
                if not planning_model:
                    last_error = "No hay modelos disponibles para planificación"
                    continue
                
                # Generar respuesta
                plan_response = self.model_manager.generate_response(
                    planning_prompt,
                    model=planning_model,
                    max_tokens=1500,
                    temperature=0.2  # Temperatura baja para mayor consistencia
                )
                
                if not plan_response:
                    last_error = "El modelo no generó respuesta"
                    continue
                
                # Parsear y validar con múltiples estrategias
                plan_data = self._parse_and_validate_plan(plan_response)
                
                if plan_data:
                    # Éxito! Registrar rendimiento del prompt
                    self._record_prompt_performance(attempt, True, plan_response)
                    plan_data["_original_response"] = plan_response
                    plan_data["_generation_attempt"] = attempt
                    return plan_data
                else:
                    last_error = "JSON generado no cumple con el esquema requerido"
                    
            except Exception as e:
                last_error = f"Error inesperado: {str(e)}"
                self.logger.error(f"Error en intento {attempt}: {e}")
                
            # Registrar fallo
            self._record_prompt_performance(attempt, False, "")
        
        # Si llegamos aquí, todos los intentos fallaron
        self.logger.error(f"Falló generación de plan después de {max_attempts} intentos. Último error: {last_error}")
        
        # Generar plan de respaldo SOLO después de agotar reintentos
        self.logger.warning("Generando plan de respaldo genérico como último recurso")
        fallback_plan = self._create_fallback_plan_with_notification(title, description, goal, last_error)
        return fallback_plan
    
    def _create_coercive_planning_prompt(self, title: str, description: str, goal: str) -> str:
        """
        Crea un prompt coercitivo con ejemplos según UPGRADE.md
        Incluye instrucciones más imperativas y ejemplos en contexto (few-shot learning)
        """
        return f"""¡ADVERTENCIA! La respuesta DEBE ser un JSON válido y nada más. No incluyas texto explicativo antes o después del JSON.

TAREA: {title}
DESCRIPCIÓN: {description}
OBJETIVO: {goal}

EJEMPLOS DE FORMATO CORRECTO:

Ejemplo 1 - Análisis:
{{"goal": "Analizar tendencias de IA en 2025", "phases": [{{"id": 1, "title": "Investigación de fuentes actuales", "description": "Buscar información actualizada sobre IA en 2025", "required_capabilities": ["web_search"], "tool_name": "web_search"}}, {{"id": 2, "title": "Análisis de datos encontrados", "description": "Procesar y analizar la información recolectada", "required_capabilities": ["analysis"], "tool_name": "analysis"}}, {{"id": 3, "title": "Redacción de informe detallado", "description": "Crear documento con conclusiones y tendencias identificadas", "required_capabilities": ["creation"], "tool_name": "creation"}}]}}

Ejemplo 2 - Creación:
{{"goal": "Crear script de automatización", "phases": [{{"id": 1, "title": "Definición de requisitos técnicos", "description": "Identificar funcionalidades específicas requeridas", "required_capabilities": ["analysis"], "tool_name": "analysis"}}, {{"id": 2, "title": "Desarrollo del código fuente", "description": "Escribir el script con las funcionalidades definidas", "required_capabilities": ["creation"], "tool_name": "creation"}}, {{"id": 3, "title": "Pruebas y optimización final", "description": "Validar funcionamiento y optimizar rendimiento", "required_capabilities": ["analysis"], "tool_name": "analysis"}}]}}

AHORA GENERA EL JSON PARA LA TAREA ACTUAL. Debe ser específico, NO genérico como "Análisis", "Ejecución", "Entrega".

ESQUEMA REQUERIDO:
- "goal": string (mínimo 3 caracteres)
- "phases": array de 1-10 objetos
  - Cada fase DEBE tener: "id" (integer), "title" (5-100 chars), "description" (10-300 chars), "required_capabilities" (array), "tool_name" (string)
  - Herramientas válidas: "web_search", "file_write", "analysis", "creation", "shell_exec", "general"

RESPUESTA (SOLO JSON):"""

    def _create_correction_prompt(self, title: str, description: str, goal: str, error: str) -> str:
        """
        Crea un prompt de corrección específica según UPGRADE.md
        """
        return f"""El JSON anterior tuvo errores. ERROR: {error}

Por favor, corrige el JSON y asegúrate de que cumpla con el esquema.

TAREA: {title}
OBJETIVO: {goal}

FORMATO CORRECTO REQUERIDO:
{{"goal": "objetivo específico aquí", "phases": [{{"id": 1, "title": "título específico NO genérico", "description": "descripción detallada de 10-300 caracteres", "required_capabilities": ["capability"], "tool_name": "herramienta_válida"}}]}}

HERRAMIENTAS VÁLIDAS: web_search, file_write, analysis, creation, shell_exec, general
CAPACIDADES VÁLIDAS: analysis, web_search, creation, planning, delivery, processing, synthesis, general, communication

NO uses títulos genéricos como "Análisis", "Ejecución", "Entrega". Sé específico para esta tarea.

RESPUESTA CORREGIDA (SOLO JSON):"""

    def _create_emergency_fallback_prompt(self, title: str, description: str, goal: str) -> str:
        """
        Crea un prompt simplificado de emergencia
        """
        return f"""Genera SOLO este JSON válido para: {title}

{{"goal": "completar la tarea solicitada", "phases": [{{"id": 1, "title": "Procesar solicitud específica", "description": "Analizar y procesar la solicitud del usuario de manera específica", "required_capabilities": ["analysis"], "tool_name": "analysis"}}, {{"id": 2, "title": "Ejecutar acciones necesarias", "description": "Realizar las acciones específicas requeridas para completar la tarea", "required_capabilities": ["general"], "tool_name": "general"}}]}}

Pero personalízalo para la tarea específica: {description}

SOLO JSON, sin explicaciones:"""

    def _parse_and_validate_plan(self, plan_response: str) -> Optional[Dict[str, Any]]:
        """
        Parsea y valida el plan usando múltiples estrategias según UPGRADE.md
        Implementa validación de esquema post-generación robusta
        """
        plan_data = None
        
        # Estrategia 1: JSON directo
        try:
            # Limpiar respuesta
            cleaned_response = plan_response.strip()
            if cleaned_response.startswith('{') and cleaned_response.endswith('}'):
                plan_data = json.loads(cleaned_response)
        except json.JSONDecodeError:
            pass
        
        # Estrategia 2: Buscar JSON en el texto
        if not plan_data:
            try:
                json_match = re.search(r'\{[^{}]*"goal"[^{}]*"phases"[^{}]*\[.*?\][^{}]*\}', plan_response, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Estrategia 3: JSON con corrección de formato
        if not plan_data:
            try:
                # Corregir comillas simples por dobles
                corrected_text = plan_response.replace("'", '"')
                # Buscar el JSON principal
                start_idx = corrected_text.find('{')
                end_idx = corrected_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_text = corrected_text[start_idx:end_idx]
                    plan_data = json.loads(json_text)
            except (json.JSONDecodeError, Exception):
                pass
        
        # Validar esquema usando jsonschema
        if plan_data:
            try:
                jsonschema.validate(plan_data, PLAN_SCHEMA)
                self.logger.info("Plan generado válido según esquema")
                return plan_data
            except jsonschema.ValidationError as e:
                self.logger.warning(f"Plan no cumple esquema: {e.message}")
                # Registrar error para análisis futuro (aprendizaje)
                self._register_validation_error(plan_response, str(e))
        
        return None
    
    def _create_fallback_plan_with_notification(self, title: str, description: str, goal: str, reason: str) -> Dict[str, Any]:
        """
        Crea plan de respaldo solo después de agotar reintentos según UPGRADE.md
        """
        self.logger.warning(f"Generando plan de respaldo para '{title}'. Razón: {reason}")
        
        return {
            "goal": goal,
            "phases": [
                {
                    "id": 1, 
                    "title": f"Análisis específico: {title}", 
                    "description": f"Analizar los requisitos específicos para: {description}", 
                    "required_capabilities": ["analysis"],
                    "tool_name": "analysis"
                },
                {
                    "id": 2, 
                    "title": f"Procesamiento de: {title}", 
                    "description": f"Procesar y trabajar en la tarea específica: {description}", 
                    "required_capabilities": ["general"],
                    "tool_name": "general"
                },
                {
                    "id": 3, 
                    "title": f"Entrega final de: {title}", 
                    "description": f"Completar y entregar los resultados finales de: {description}", 
                    "required_capabilities": ["delivery"],
                    "tool_name": "general"
                }
            ],
            "_fallback_used": True,
            "_fallback_reason": reason,
            "_warning": "Este plan fue generado como respaldo después de múltiples intentos fallidos"
        }
    
    def _record_prompt_performance(self, attempt: int, success: bool, response: str):
        """
        Registra el rendimiento del prompt para análisis futuro según UPGRADE.md
        Utiliza métricas de PromptPerformance para monitoreo
        """
        try:
            # Aquí se integraría con enhanced_prompts.py para registrar métricas
            performance_data = {
                "attempt": attempt,
                "success": success,
                "response_length": len(response) if response else 0,
                "timestamp": time.time()
            }
            
            # Añadir a memoria para análisis futuro
            self.memory_manager.add_knowledge(
                content=f"Prompt performance: {performance_data}",
                category="prompt_optimization",
                source="agent_planning",
                confidence=1.0,
                tags=["performance", "planning", "optimization"]
            )
            
        except Exception as e:
            self.logger.error(f"Error registrando performance: {e}")
    
    def _register_validation_error(self, response: str, error: str):
        """
        Registra errores de validación para análisis futuro según UPGRADE.md
        """
        try:
            self.memory_manager.add_knowledge(
                content=f"Validation error: {error} | Response: {response[:200]}...",
                category="validation_errors",
                source="agent_planning",
                confidence=0.8,
                tags=["error", "validation", "planning"]
            )
        except Exception as e:
            self.logger.error(f"Error registrando validation error: {e}")
    
    def execute_current_phase(self, task_id: Optional[str] = None) -> str:
        """Ejecuta la fase actual de una tarea"""
        try:
            self.state = AgentState.EXECUTING
            
            # Obtener tarea actual o especificada
            if task_id:
                task = self.task_manager.get_task(task_id)
            else:
                task = self.task_manager.get_current_task()
            
            if not task:
                return "Error: No hay tarea activa para ejecutar."
            
            # Obtener fase actual
            current_phase = self.task_manager.get_current_phase(task.id)
            if not current_phase:
                return "Error: No hay fase activa en la tarea."
            
            # Generar prompt de ejecución
            execution_prompt = self.prompt_manager.generate_phase_execution_prompt(task, current_phase)
            
            # Seleccionar modelo apropiado para la fase
            task_type = self._determine_task_type_from_capabilities(current_phase.required_capabilities)
            execution_model = self.model_manager.select_best_model(
                task_type=task_type,
                max_cost=self.config.max_cost_per_1k_tokens
            )
            
            if not execution_model:
                return "Error: No hay modelos disponibles para ejecutar la fase."
            
            # Ejecutar fase
            execution_response = self.model_manager.generate_response(
                execution_prompt,
                model=execution_model,
                max_tokens=2000,
                temperature=0.5
            )
            
            if not execution_response:
                return "Error: No se pudo ejecutar la fase."
            
            # Simular resultados de la fase (en una implementación real, aquí se ejecutarían herramientas)
            phase_results = {
                "execution_response": execution_response,
                "model_used": execution_model.name,
                "completed_at": time.time()
            }
            
            # Determinar si la fase está completa o necesita más trabajo
            if "completado" in execution_response.lower() or "finalizado" in execution_response.lower():
                # Avanzar a la siguiente fase
                next_phase_id = current_phase.id + 1
                if next_phase_id <= len(task.phases):
                    self.task_manager.advance_phase(task.id, current_phase.id, next_phase_id, phase_results)
                    return f"Fase {current_phase.id} completada. Avanzando a fase {next_phase_id}."
                else:
                    # Completar tarea
                    self.task_manager.complete_task(task.id, phase_results)
                    self.stats["tasks_completed"] += 1
                    return f"Tarea '{task.title}' completada exitosamente."
            else:
                return f"Fase {current_phase.id} en progreso: {execution_response[:200]}..."
            
        except Exception as e:
            self.logger.error(f"Error al ejecutar fase: {e}")
            self.state = AgentState.ERROR
            return f"Error al ejecutar fase: {str(e)}"
    
    def reflect_on_action(self, action: str, result: str, expected: str) -> str:
        """Reflexiona sobre una acción ejecutada"""
        try:
            self.state = AgentState.REFLECTING
            
            # Obtener contexto de tarea actual
            current_task = self.task_manager.get_current_task()
            task_context = ""
            if current_task:
                task_context = f"Tarea: {current_task.title}\nObjetivo: {current_task.goal}"
            
            # Generar prompt de reflexión
            reflection_prompt = self.prompt_manager.generate_reflection_prompt(
                action_taken=action,
                result=result,
                expected_outcome=expected,
                task_context=task_context
            )
            
            # Seleccionar modelo para reflexión
            reflection_model = self.model_manager.select_best_model(
                task_type="analysis",
                max_cost=self.config.max_cost_per_1k_tokens
            )
            
            if not reflection_model:
                return "Error: No hay modelos disponibles para reflexión."
            
            # Generar reflexión
            reflection_response = self.model_manager.generate_response(
                reflection_prompt,
                model=reflection_model,
                max_tokens=800,
                temperature=0.6
            )
            
            if reflection_response:
                # Añadir reflexión a la memoria como conocimiento
                self.memory_manager.add_knowledge(
                    content=f"Reflexión sobre acción: {action} -> {reflection_response}",
                    category="reflection",
                    source="agent_reflection",
                    confidence=0.8,
                    tags=["reflection", "learning"]
                )
                
                self.state = AgentState.IDLE
                return reflection_response
            else:
                return "Error: No se pudo generar reflexión."
            
        except Exception as e:
            self.logger.error(f"Error en reflexión: {e}")
            self.state = AgentState.ERROR
            return f"Error en reflexión: {str(e)}"
    
    def handle_error(self, error_message: str, failed_action: str, context: str = "") -> str:
        """Maneja errores y genera estrategias de recuperación"""
        try:
            self.state = AgentState.ERROR
            
            # Generar prompt de manejo de errores
            error_prompt = self.prompt_manager.generate_error_handling_prompt(
                error_message=error_message,
                failed_action=failed_action,
                context=context,
                additional_info=f"Estado del agente: {self.state.value}"
            )
            
            # Seleccionar modelo para manejo de errores
            error_model = self.model_manager.select_best_model(
                task_type="analysis",
                max_cost=self.config.max_cost_per_1k_tokens
            )
            
            if not error_model:
                self.state = AgentState.IDLE
                return "Error crítico: No hay modelos disponibles para manejo de errores."
            
            # Generar estrategia de recuperación
            recovery_response = self.model_manager.generate_response(
                error_prompt,
                model=error_model,
                max_tokens=1000,
                temperature=0.4
            )
            
            if recovery_response:
                # Registrar error y estrategia en memoria
                self.memory_manager.add_knowledge(
                    content=f"Error manejado: {error_message} -> Estrategia: {recovery_response}",
                    category="error_handling",
                    source="agent_error_handler",
                    confidence=0.7,
                    tags=["error", "recovery", "learning"]
                )
                
                self.state = AgentState.IDLE
                return recovery_response
            else:
                self.state = AgentState.IDLE
                return "Error: No se pudo generar estrategia de recuperación."
            
        except Exception as e:
            self.logger.error(f"Error en manejo de errores: {e}")
            self.state = AgentState.IDLE
            return f"Error crítico en manejo de errores: {str(e)}"
    
    def _extract_knowledge_from_conversation(self, user_message: str, agent_response: str):
        """Extrae conocimiento relevante de la conversación"""
        try:
            # Identificar si la conversación contiene información valiosa
            knowledge_indicators = [
                "aprendí", "descubrí", "encontré", "resultado", "solución",
                "importante", "clave", "fundamental", "técnica", "método"
            ]
            
            combined_text = (user_message + " " + agent_response).lower()
            
            if any(indicator in combined_text for indicator in knowledge_indicators):
                # Extraer conocimiento
                knowledge_content = f"Conversación: Usuario preguntó sobre '{user_message[:100]}...' y se determinó: {agent_response[:200]}..."
                
                self.memory_manager.add_knowledge(
                    content=knowledge_content,
                    category="conversation",
                    source="user_interaction",
                    confidence=0.6,
                    tags=["conversation", "user_query"]
                )
                
        except Exception as e:
            self.logger.error(f"Error al extraer conocimiento: {e}")
    
    def _determine_task_type_from_capabilities(self, capabilities: List[str]) -> str:
        """Determina el tipo de tarea basándose en las capacidades requeridas"""
        capability_mapping = {
            "code": ["code_generation", "programming", "development"],
            "analysis": ["analysis", "research", "investigation"],
            "chat": ["communication", "interaction", "conversation"],
            "general": ["general", "misc", "other"]
        }
        
        for task_type, keywords in capability_mapping.items():
            if any(keyword in cap.lower() for cap in capabilities for keyword in keywords):
                return task_type
        
        return "general"
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del agente"""
        self.stats["uptime"] = time.time() - self.startup_time
        
        return {
            "agent_name": self.config.agent_name,
            "state": self.state.value,
            "session_id": self.current_session_id,
            "uptime_seconds": self.stats["uptime"],
            "statistics": self.stats.copy(),
            "memory_stats": self.memory_manager.get_memory_stats(),
            "task_manager_status": self.task_manager.get_manager_status(),
            "model_manager_status": self.model_manager.get_status(),
            "available_models": len(self.model_manager.get_available_models())
        }
    
    def shutdown(self):
        """Cierra el agente de manera ordenada"""
        try:
            self.logger.info("Iniciando cierre del agente...")
            
            # Persistir memoria a corto plazo
            self.memory_manager.clear_short_term_memory(persist=True)
            
            # Detener monitoreo de tareas
            self.task_manager._stop_monitoring_thread()
            
            # Limpiar datos antiguos
            self.memory_manager.cleanup_old_data(days_old=30)
            
            self.state = AgentState.IDLE
            self.logger.info("Agente cerrado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error durante el cierre: {e}")

# Función de conveniencia para crear un agente con configuración por defecto
def create_mitosis_agent(ollama_url: str = "http://localhost:11434",
                        openrouter_api_key: Optional[str] = None,
                        prefer_local: bool = True) -> MitosisAgent:
    """Crea una instancia del agente Mitosis con configuración básica"""
    config = AgentConfig(
        ollama_url=ollama_url,
        openrouter_api_key=openrouter_api_key,
        prefer_local_models=prefer_local
    )
    return MitosisAgent(config)

# Ejemplo de uso
if __name__ == "__main__":
    # Crear agente
    agent = create_mitosis_agent()
    
    # Iniciar sesión
    session_id = agent.start_session()
    print(f"🚀 Sesión iniciada: {session_id}")
    
    # Procesar mensaje del usuario
    response = agent.process_user_message("Hola, ¿puedes ayudarme a crear un script de Python?")
    print(f"🤖 Respuesta: {response}")
    
    # Crear y ejecutar una tarea
    task_result = agent.create_and_execute_task(
        title="Crear script de Python",
        description="Desarrollar un script que procese archivos CSV",
        goal="Crear un script funcional para procesamiento de datos CSV"
    )
    print(f"📋 Resultado de tarea: {task_result}")
    
    # Obtener estado del agente
    status = agent.get_status()
    print(f"📊 Estado del agente: {status['state']}")
    print(f"📈 Mensajes procesados: {status['statistics']['messages_processed']}")
    
    # Cerrar agente
    agent.shutdown()
    print("✅ Agente cerrado correctamente")

