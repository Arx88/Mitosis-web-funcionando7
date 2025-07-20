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
        """Crea y opcionalmente ejecuta una nueva tarea"""
        try:
            self.state = AgentState.PLANNING
            
            # Generar plan de tarea usando el prompt manager
            planning_prompt = self.prompt_manager.generate_task_planning_prompt(
                goal=goal,
                description=description,
                context=f"Título: {title}"
            )
            
            # Seleccionar modelo para planificación
            planning_model = self.model_manager.select_best_model(
                task_type="analysis",
                max_cost=self.config.max_cost_per_1k_tokens
            )
            
            if not planning_model:
                return "Error: No hay modelos disponibles para planificación."
            
            # Generar plan
            plan_response = self.model_manager.generate_response(
                planning_prompt,
                model=planning_model,
                max_tokens=1500,
                temperature=0.3
            )
            
            if not plan_response:
                return "Error: No se pudo generar el plan de tarea."
            
            # Parsear el plan (asumiendo formato JSON)
            try:
                # Extraer JSON del response si está envuelto en texto
                start_idx = plan_response.find('{')
                end_idx = plan_response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    plan_json = plan_response[start_idx:end_idx]
                    plan_data = json.loads(plan_json)
                else:
                    # Si no hay JSON, crear plan básico
                    plan_data = {
                        "goal": goal,
                        "phases": [
                            {"id": 1, "title": "Análisis", "description": description, "required_capabilities": ["analysis"]},
                            {"id": 2, "title": "Ejecución", "description": "Ejecutar la tarea", "required_capabilities": ["general"]},
                            {"id": 3, "title": "Entrega", "description": "Entregar resultados", "required_capabilities": ["communication"]}
                        ]
                    }
            except json.JSONDecodeError:
                # Plan de respaldo
                plan_data = {
                    "goal": goal,
                    "phases": [
                        {"id": 1, "title": "Análisis", "description": description, "required_capabilities": ["analysis"]},
                        {"id": 2, "title": "Ejecución", "description": "Ejecutar la tarea", "required_capabilities": ["general"]},
                        {"id": 3, "title": "Entrega", "description": "Entregar resultados", "required_capabilities": ["communication"]}
                    ]
                }
            
            # Crear tarea
            task_id = self.task_manager.create_task(
                title=title,
                description=description,
                goal=goal,
                phases=plan_data.get("phases", []),
                context={"plan_response": plan_response}
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
                self.state = AgentState.IDLE
                return f"Tarea '{title}' creada con ID: {task_id}. Use execute_task() para iniciarla."
            
        except Exception as e:
            self.logger.error(f"Error al crear/ejecutar tarea: {e}")
            self.state = AgentState.ERROR
            return f"Error al crear tarea: {str(e)}"
    
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

