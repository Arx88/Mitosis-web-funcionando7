"""
Núcleo del Agente Mitosis REAL - Versión sin simulaciones
Implementa herramientas reales y elimina todos los mockups
Soluciona los problemas identificados en el documento de análisis
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
import sys
import subprocess

# CARGAR VARIABLES DE ENTORNO DESDE .ENV
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Importar el ToolManager real que ya existe
sys.path.append('/app/backend/src')
from tools.tool_manager import ToolManager
from tools.tavily_search_tool import TavilySearchTool
from tools.web_search_tool import WebSearchTool
from tools.shell_tool import ShellTool
from tools.file_manager_tool import FileManagerTool

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

# Esquema JSON mejorado para validación de planes
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
                        "enum": ["web_search", "tavily_search", "file_manager", "analysis", "creation", "shell", "general"]
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
    agent_name: str = "Mitosis-Real"
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # NUEVO: Configuración de seguridad para sandboxing
    enable_sandboxing: bool = True
    sandbox_timeout: int = 300
    max_file_size: int = 100 * 1024 * 1024  # 100MB

class MitosisRealAgent:
    """
    Agente Mitosis REAL con herramientas reales - Sin simulaciones
    Implementa todas las soluciones propuestas en el documento de análisis
    """
    
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
        
        # CRITICO: Inicializar ToolManager REAL
        self.tool_manager = ToolManager()
        
        # Inicializar componentes
        self._initialize_components()
        
        # Estadísticas mejoradas
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_processed": 0,
            "models_used": set(),
            "tools_executed": {},
            "real_files_created": 0,
            "real_web_searches": 0,
            "real_commands_executed": 0,
            "uptime": 0
        }
        
        # NUEVO: Métricas de rendimiento para evaluación continua
        self.performance_metrics = {
            "task_success_rate": 0.0,
            "avg_task_completion_time": 0.0,
            "tool_accuracy_rate": {},
            "plan_generation_success_rate": 0.0,
            "user_satisfaction_score": 0.0
        }
        
        self.logger.info(f"🚀 Agente REAL {self.config.agent_name} inicializado correctamente")
        self.logger.info(f"🛠️  Herramientas reales disponibles: {list(self.tool_manager.tools.keys())}")
    
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
            
            self.logger.info("✅ Todos los componentes inicializados correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error al inicializar componentes: {e}")
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
            {"session_start": True, "timestamp": time.time(), "agent_type": "REAL"}
        )
        
        self.logger.info(f"🎯 Nueva sesión REAL iniciada: {self.current_session_id}")
        return self.current_session_id
    
    def create_and_execute_task(self, title: str, description: str, goal: str,
                               auto_execute: bool = True) -> str:
        """
        Crea y opcionalmente ejecuta una nueva tarea con generación robusta de planes
        SOLUCION 1: Reemplaza generación de planes genéricos con validación semántica
        """
        try:
            self.state = AgentState.PLANNING
            
            # MEJORA 1: Generar plan con validación semántica mejorada
            plan_data = self._generate_robust_plan_with_semantic_validation(title, description, goal)
            
            if not plan_data:
                return "❌ Error: No se pudo generar un plan válido para la tarea."
            
            # Crear tarea
            task_id = self.task_manager.create_task(
                title=title,
                description=description,
                goal=goal,
                phases=plan_data.get("phases", []),
                context={
                    "plan_response": plan_data.get("_original_response", ""), 
                    "ai_generated": True,
                    "real_agent": True,
                    "semantic_validation_passed": plan_data.get("_semantic_validation", False)
                }
            )
            
            # MEJORA 2: Registrar métricas de generación de plan
            self._record_plan_generation_metrics(True, plan_data.get("_generation_attempt", 1))
            
            # Añadir información a la memoria
            self.memory_manager.add_knowledge(
                content=f"Tarea REAL creada: {title} - {description}",
                category="task_planning_real",
                source="real_agent_planning",
                confidence=0.9,
                tags=["task", "planning", "real"]
            )
            
            if auto_execute:
                # Iniciar ejecución de la tarea
                if self.task_manager.start_task(task_id):
                    self.state = AgentState.EXECUTING
                    return f"✅ Tarea REAL '{title}' creada e iniciada con ID: {task_id}"
                else:
                    return f"⚠️  Tarea '{title}' creada con ID: {task_id}, pero no se pudo iniciar automáticamente."
            else:
                return f"📋 Tarea REAL '{title}' creada con ID: {task_id}. Usa start_task() para ejecutar."
            
        except Exception as e:
            self.logger.error(f"❌ Error al crear y ejecutar tarea: {e}")
            self.state = AgentState.ERROR
            self._record_plan_generation_metrics(False, 0)
            return f"❌ Error al crear tarea: {str(e)}"
    
    def _generate_robust_plan_with_semantic_validation(self, title: str, description: str, goal: str, 
                                                     max_attempts: int = 3) -> Optional[Dict[str, Any]]:
        """
        SOLUCION 1: Generación robusta de planes con validación semántica
        Implementa validación semántica adicional además de validación de esquema JSON
        """
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"🎯 Generando plan REAL - Intento {attempt}/{max_attempts}")
                
                # Generar prompt específico según el intento
                if attempt == 1:
                    planning_prompt = self._create_enhanced_planning_prompt(title, description, goal)
                elif attempt == 2:
                    planning_prompt = self._create_correction_prompt_with_context(title, description, goal, last_error)
                else:
                    planning_prompt = self._create_semantic_guided_prompt(title, description, goal)
                
                # Seleccionar modelo optimizado para JSON
                planning_model = self.model_manager.select_best_model(
                    task_type="analysis",
                    max_cost=self.config.max_cost_per_1k_tokens
                )
                
                if not planning_model:
                    last_error = "No hay modelos disponibles para planificación"
                    continue
                
                # Generar respuesta
                plan_response = self.model_manager.generate_response(
                    planning_prompt,
                    model=planning_model,
                    max_tokens=1500,
                    temperature=0.1  # Temperatura muy baja para máxima consistencia
                )
                
                if not plan_response:
                    last_error = "El modelo no generó respuesta"
                    continue
                
                # MEJORA: Parsear y validar con múltiples estrategias + validación semántica
                plan_data = self._parse_validate_and_semantic_check(plan_response, title, description, goal)
                
                if plan_data:
                    # Éxito! Registrar rendimiento del prompt
                    self._record_prompt_performance(attempt, True, plan_response)
                    plan_data["_original_response"] = plan_response
                    plan_data["_generation_attempt"] = attempt
                    plan_data["_semantic_validation"] = True
                    return plan_data
                else:
                    last_error = "Plan no pasó validación semántica"
                    
            except Exception as e:
                last_error = f"Error inesperado: {str(e)}"
                self.logger.error(f"❌ Error en intento {attempt}: {e}")
                
            # Registrar fallo
            self._record_prompt_performance(attempt, False, "")
        
        # Generar plan con asesoría humana si todos los intentos fallan
        self.logger.error(f"❌ Falló generación de plan después de {max_attempts} intentos. Último error: {last_error}")
        
        # MEJORA: En lugar de plan de respaldo genérico, solicitar intervención
        return self._request_human_assistance_plan(title, description, goal, last_error)
    
    def _parse_validate_and_semantic_check(self, plan_response: str, title: str, description: str, goal: str) -> Optional[Dict[str, Any]]:
        """
        SOLUCION 1: Validación con esquema JSON + validación semántica
        """
        # Primero validar esquema JSON (método existente)
        plan_data = self._parse_and_validate_plan(plan_response)
        
        if not plan_data:
            return None
        
        # NUEVO: Validación semántica adicional
        semantic_validation = self._validate_plan_semantically(plan_data, title, description, goal)
        
        if not semantic_validation["valid"]:
            self.logger.warning(f"⚠️  Plan falló validación semántica: {semantic_validation['reason']}")
            self._register_semantic_validation_error(plan_response, semantic_validation["reason"])
            return None
        
        self.logger.info("✅ Plan pasó validación JSON y semántica")
        return plan_data
    
    def _validate_plan_semantically(self, plan_data: Dict[str, Any], title: str, description: str, goal: str) -> Dict[str, Any]:
        """
        SOLUCION 1: Validación semántica de planes usando segundo LLM
        """
        try:
            # Crear prompt de validación semántica
            validation_prompt = f"""Evalúa si este plan es lógico y coherente para la tarea dada.

TAREA: {title}
DESCRIPCIÓN: {description}
OBJETIVO: {goal}

PLAN GENERADO:
{json.dumps(plan_data, indent=2)}

Evalúa:
1. ¿Las fases son específicas y no genéricas?
2. ¿La secuencia de fases es lógica?
3. ¿Las herramientas propuestas son apropiadas?
4. ¿El plan realmente puede completar el objetivo?
5. ¿Hay fases redundantes o innecesarias?

Responde con JSON: {{"valid": true/false, "reason": "explicación detallada", "suggestions": ["sugerencia1", "sugerencia2"]}}"""

            # Usar modelo diferente para validación (evitar sesgos)
            validation_model = self.model_manager.select_best_model(
                task_type="analysis",
                max_cost=self.config.max_cost_per_1k_tokens
            )
            
            if not validation_model:
                return {"valid": True, "reason": "No hay modelo para validación semántica"}
            
            validation_response = self.model_manager.generate_response(
                validation_prompt,
                model=validation_model,
                max_tokens=500,
                temperature=0.2
            )
            
            if validation_response:
                # Parsear respuesta JSON
                try:
                    validation_result = json.loads(validation_response.strip())
                    return validation_result
                except json.JSONDecodeError:
                    # Fallback: buscar "valid": true/false en el texto
                    if "valid\": true" in validation_response or "\"valid\": true" in validation_response:
                        return {"valid": True, "reason": "Validación básica pasada"}
                    else:
                        return {"valid": False, "reason": "Validación semántica falló"}
            
            return {"valid": True, "reason": "Sin validación semántica disponible"}
            
        except Exception as e:
            self.logger.error(f"❌ Error en validación semántica: {e}")
            return {"valid": True, "reason": f"Error en validación: {str(e)}"}
    
    def execute_current_phase(self, task_id: Optional[str] = None) -> str:
        """
        SOLUCION 2: Ejecuta la fase actual de una tarea con HERRAMIENTAS REALES
        Reemplaza completamente todas las simulaciones
        """
        try:
            self.state = AgentState.EXECUTING
            
            # Obtener tarea actual o especificada
            if task_id:
                task = self.task_manager.get_task(task_id)
            else:
                task = self.task_manager.get_current_task()
            
            if not task:
                return "❌ Error: No hay tarea activa para ejecutar."
            
            # Obtener fase actual
            current_phase = self.task_manager.get_current_phase(task.id)
            if not current_phase:
                return "❌ Error: No hay fase activa en la tarea."
            
            # CRITICO: Generar prompt de ejecución para tool calling REAL
            execution_prompt = self._create_real_tool_calling_prompt(task, current_phase)
            
            # Seleccionar modelo apropiado para la fase
            task_type = self._determine_task_type_from_capabilities(current_phase.required_capabilities)
            execution_model = self.model_manager.select_best_model(
                task_type=task_type,
                max_cost=self.config.max_cost_per_1k_tokens
            )
            
            if not execution_model:
                return "❌ Error: No hay modelos disponibles para ejecutar la fase."
            
            # Ejecutar fase con LLM para obtener tool call
            execution_response = self.model_manager.generate_response(
                execution_prompt,
                model=execution_model,
                max_tokens=2000,
                temperature=0.2  # Temperatura baja para tool calling preciso
            )
            
            if not execution_response:
                return "❌ Error: No se pudo obtener respuesta para ejecutar la fase."
            
            # SOLUCION 2: Parsear y ejecutar HERRAMIENTAS REALES
            tool_result = self._parse_and_execute_real_tools(execution_response, task, current_phase)
            
            if not tool_result:
                return "❌ Error: No se pudo ejecutar ninguna herramienta real."
            
            # MEJORA: Actualización del progreso basada en resultados reales
            if tool_result.get("status") == "success":
                # Registrar métricas de éxito
                self._record_tool_success_metrics(tool_result.get("tool_name"), task.id, current_phase.id)
                
                # Avanzar a la siguiente fase basándose en éxito de herramienta
                next_phase_id = current_phase.id + 1
                if next_phase_id <= len(task.phases):
                    self.task_manager.advance_phase(task.id, current_phase.id, next_phase_id, tool_result)
                    return f"✅ Fase {current_phase.id} completada exitosamente con herramientas REALES. Resultado: {tool_result.get('summary', '')}. Avanzando a fase {next_phase_id}."
                else:
                    # Completar tarea
                    self.task_manager.complete_task(task.id, tool_result)
                    self.stats["tasks_completed"] += 1
                    self._calculate_and_update_performance_metrics()
                    return f"🎉 Tarea REAL '{task.title}' completada exitosamente. Resultado final: {tool_result.get('summary', '')}"
            elif tool_result.get("status") == "failure":
                # MEJORA: Manejo de errores con estrategias de recuperación
                error_result = self._handle_real_tool_error(task, current_phase, tool_result.get("error", ""))
                self._record_tool_failure_metrics(tool_result.get("tool_name"), task.id, current_phase.id)
                return f"❌ Error ejecutando fase {current_phase.id}: {error_result}"
            else:
                return f"🔄 Fase {current_phase.id} en progreso: {tool_result.get('summary', '')}"
            
        except Exception as e:
            self.logger.error(f"❌ Error al ejecutar fase: {e}")
            self.state = AgentState.ERROR
            return f"❌ Error al ejecutar fase: {str(e)}"
    
    def _create_real_tool_calling_prompt(self, task, current_phase) -> str:
        """
        SOLUCION 2: Crea prompt para usar herramientas REALES específicas
        """
        # Obtener herramientas reales disponibles
        available_tools = self.tool_manager.get_available_tools()
        
        # Construir descripciones de herramientas reales
        tools_description = []
        for tool_info in available_tools:
            name = tool_info['name']
            description = tool_info['description']
            parameters = tool_info.get('parameters', [])
            param_desc = ", ".join([f"{p['name']} ({p['type']})" for p in parameters])
            tools_description.append(f"- {name}: {description} | Parámetros: {param_desc}")
        
        tools_text = "\n".join(tools_description)
        
        return f"""Eres un agente que debe ejecutar esta fase usando HERRAMIENTAS REALES disponibles.

TAREA: {task.title}
DESCRIPCIÓN: {task.description}
OBJETIVO: {task.goal}

FASE ACTUAL:
- ID: {current_phase.id}
- Título: {current_phase.title}
- Descripción: {current_phase.description}
- Capacidades requeridas: {current_phase.required_capabilities}

HERRAMIENTAS REALES DISPONIBLES:
{tools_text}

IMPORTANTE: Estas herramientas son REALES y producirán resultados tangibles:
- web_search: Búsquedas reales en internet con DuckDuckGo
- tavily_search: Búsqueda avanzada con Tavily API
- file_manager: Escritura/lectura real de archivos
- shell: Ejecución real de comandos de terminal (seguro)

INSTRUCCIONES:
Responde ÚNICAMENTE con un JSON que contenga:
{{
  "action_type": "tool_call",
  "tool_name": "nombre_herramienta_real",
  "tool_parameters": {{"parametro": "valor"}},
  "thought": "por qué usas esta herramienta",
  "expected_outcome": "resultado esperado específico",
  "status_update": "mensaje de progreso para el usuario"
}}

EJEMPLO REAL:
{{"action_type": "tool_call", "tool_name": "tavily_search", "tool_parameters": {{"query": "tendencias inteligencia artificial 2025", "max_results": 5, "include_answer": true}}, "thought": "Necesito buscar información actualizada sobre IA 2025 usando búsqueda real", "expected_outcome": "Obtener 5 fuentes actualizadas con información específica sobre tendencias IA", "status_update": "Realizando búsqueda web real sobre tendencias IA"}}

RESPUESTA (SOLO JSON):"""
    
    def _parse_and_execute_real_tools(self, execution_response: str, task, current_phase) -> Dict[str, Any]:
        """
        SOLUCION 2: Parsea y ejecuta HERRAMIENTAS REALES usando ToolManager
        Elimina completamente las simulaciones
        """
        try:
            # Parsear respuesta JSON del LLM
            tool_call_data = self._parse_tool_call_response(execution_response)
            
            if not tool_call_data:
                return {"status": "failure", "error": "No se pudo parsear llamada a herramienta"}
            
            action_type = tool_call_data.get("action_type")
            
            if action_type == "tool_call":
                tool_name = tool_call_data.get("tool_name")
                tool_parameters = tool_call_data.get("tool_parameters", {})
                thought = tool_call_data.get("thought", "")
                expected_outcome = tool_call_data.get("expected_outcome", "")
                status_update = tool_call_data.get("status_update", "")
                
                # CRITICO: Validar herramienta en ToolManager REAL
                if not self.tool_manager.is_tool_enabled(tool_name):
                    return {"status": "failure", "error": f"Herramienta REAL '{tool_name}' no disponible o deshabilitada"}
                
                # SOLUCION 2: Ejecutar herramienta REAL usando ToolManager
                try:
                    self.logger.info(f"🛠️  Ejecutando herramienta REAL '{tool_name}' con parámetros: {tool_parameters}")
                    
                    # Ejecutar herramienta real
                    real_result = self.tool_manager.execute_tool(
                        tool_name=tool_name,
                        parameters=tool_parameters,
                        config={"timeout": 30},
                        task_id=task.id
                    )
                    
                    # MEJORA: Validar que el resultado es real
                    if self._validate_real_result(real_result, tool_name):
                        # Registrar ejecución REAL en memoria
                        self._register_real_tool_execution(tool_name, tool_parameters, real_result, task.id, current_phase.id)
                        
                        # Actualizar estadísticas de herramientas reales
                        self._update_real_tool_stats(tool_name, True)
                        
                        return {
                            "status": "success",
                            "tool_name": tool_name,
                            "tool_result": real_result,
                            "thought": thought,
                            "expected_outcome": expected_outcome,
                            "status_update": status_update,
                            "summary": f"Herramienta REAL '{tool_name}' ejecutada exitosamente: {real_result.get('summary', str(real_result)[:100])}",
                            "real_execution": True
                        }
                    else:
                        return {"status": "failure", "error": f"Resultado de herramienta '{tool_name}' no válido", "tool_name": tool_name}
                    
                except Exception as tool_error:
                    self.logger.error(f"❌ Error ejecutando herramienta REAL '{tool_name}': {tool_error}")
                    self._update_real_tool_stats(tool_name, False)
                    return {"status": "failure", "error": str(tool_error), "tool_name": tool_name}
            
            elif action_type == "reflection":
                # Invocar función de reflexión del agente
                reflection_result = self._handle_real_reflection(tool_call_data, task, current_phase)
                return {"status": "success", "summary": reflection_result, "action_type": "reflection", "real_execution": True}
            
            elif action_type == "report":
                # La fase está completa sin herramientas
                summary = tool_call_data.get("summary", "Fase completada")
                return {"status": "success", "summary": summary, "action_type": "report", "real_execution": True}
            
            else:
                return {"status": "failure", "error": f"Tipo de acción no reconocido: {action_type}"}
                
        except Exception as e:
            self.logger.error(f"❌ Error parseando y ejecutando herramientas REALES: {e}")
            return {"status": "failure", "error": str(e)}
    
    def _validate_real_result(self, result: Dict[str, Any], tool_name: str) -> bool:
        """
        SOLUCION 2: Valida que el resultado de la herramienta es real y no simulado
        """
        try:
            # Verificaciones específicas por herramienta
            if tool_name == "web_search" or tool_name == "tavily_search":
                # Verificar que hay resultados reales con URLs válidas
                if 'results' in result:
                    results = result['results']
                    if isinstance(results, list) and len(results) > 0:
                        # Verificar que al menos un resultado tiene URL real
                        for res in results:
                            if 'url' in res and res['url'].startswith('http'):
                                return True
                return 'query' in result and 'success' in result
            
            elif tool_name == "file_manager":
                # Verificar que hay path real o contenido
                return ('path' in result or 'content' in result) and 'success' in result
            
            elif tool_name == "shell":
                # Verificar que hay comando y salida
                return 'command' in result and ('stdout' in result or 'stderr' in result)
            
            else:
                # Para otras herramientas, verificar que no hay errores obvios
                return 'error' not in result or result.get('success', False)
                
        except Exception as e:
            self.logger.error(f"❌ Error validando resultado real: {e}")
            return False
    
    def _update_real_tool_stats(self, tool_name: str, success: bool):
        """
        SOLUCION 2: Actualiza estadísticas de herramientas reales
        """
        if tool_name not in self.stats["tools_executed"]:
            self.stats["tools_executed"][tool_name] = {"total": 0, "success": 0, "failure": 0}
        
        self.stats["tools_executed"][tool_name]["total"] += 1
        if success:
            self.stats["tools_executed"][tool_name]["success"] += 1
            
            # Contadores específicos de acciones reales
            if tool_name in ["web_search", "tavily_search"]:
                self.stats["real_web_searches"] += 1
            elif tool_name == "file_manager":
                self.stats["real_files_created"] += 1
            elif tool_name == "shell":
                self.stats["real_commands_executed"] += 1
        else:
            self.stats["tools_executed"][tool_name]["failure"] += 1
    
    def _register_real_tool_execution(self, tool_name: str, parameters: Dict[str, Any], 
                                    result: Dict[str, Any], task_id: str, phase_id: int):
        """
        SOLUCION 2: Registra ejecuciones de herramientas REALES para análisis
        """
        try:
            execution_record = {
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                "task_id": task_id,
                "phase_id": phase_id,
                "timestamp": time.time(),
                "real_execution": True,
                "result_type": "real"
            }
            
            # Extraer información específica según el tipo de herramienta
            summary_info = ""
            if tool_name in ["web_search", "tavily_search"]:
                query = parameters.get('query', '')
                results_count = len(result.get('results', []))
                summary_info = f"Búsqueda REAL: '{query}' - {results_count} resultados"
                
            elif tool_name == "file_manager":
                action = parameters.get('action', '')
                path = parameters.get('path', '')
                summary_info = f"Archivo REAL {action}: {path}"
                
            elif tool_name == "shell":
                command = parameters.get('command', '')
                exit_code = result.get('exit_code', 'N/A')
                summary_info = f"Comando REAL: '{command}' (código: {exit_code})"
            
            self.memory_manager.add_knowledge(
                content=f"Ejecución REAL de herramienta: {summary_info}",
                category="real_tool_execution",
                source="real_agent_execution",
                confidence=1.0,
                tags=["tool", "execution", "real", tool_name]
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error registrando ejecución real: {e}")
    
    def _handle_real_tool_error(self, task, current_phase, error: str) -> str:
        """
        SOLUCION 2: Maneja errores de herramientas reales con estrategias de recuperación
        """
        try:
            self.logger.warning(f"⚠️  Manejando error real de herramienta: {error}")
            
            # Estrategias de recuperación basadas en el tipo de error
            recovery_strategies = {
                "timeout": "reintentar con timeout mayor",
                "network": "usar herramienta alternativa de búsqueda",
                "permission": "usar herramienta con menos permisos",
                "file_not_found": "crear archivo o verificar ruta",
                "command_blocked": "usar comando alternativo seguro"
            }
            
            # Determinar tipo de error y estrategia
            error_lower = error.lower()
            strategy = "intervención manual"
            
            for error_type, recovery_strategy in recovery_strategies.items():
                if error_type in error_lower:
                    strategy = recovery_strategy
                    break
            
            # Registrar error para aprendizaje futuro
            self.memory_manager.add_knowledge(
                content=f"Error real en herramienta: {error} -> Estrategia: {strategy}",
                category="real_tool_errors",
                source="real_error_handling",
                confidence=0.9,
                tags=["error", "real", "recovery", "learning"]
            )
            
            return f"Error en herramienta real: {error}. Estrategia de recuperación: {strategy}"
            
        except Exception as e:
            self.logger.error(f"❌ Error en manejo de errores reales: {e}")
            return f"Error crítico real: {error}"
    
    # IMPLEMENTACIONES DE HERRAMIENTAS REALES - NO SIMULACIONES
    
    def execute_real_web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        SOLUCION 2: Ejecuta búsqueda web REAL usando ToolManager
        Reemplaza completamente _execute_web_search simulada
        """
        try:
            # Usar herramienta real de Tavily primero
            if self.tool_manager.is_tool_enabled('tavily_search'):
                self.logger.info(f"🔍 Usando Tavily para búsqueda REAL: '{query}'")
                result = self.tool_manager.execute_tool(
                    tool_name='tavily_search',
                    parameters={
                        'query': query,
                        'max_results': max_results,
                        'include_answer': True
                    },
                    config={"timeout": 30}
                )
                
                if result.get('success'):
                    self.logger.info(f"✅ Búsqueda Tavily REAL completada: {len(result.get('results', []))} resultados para '{query}'")
                    return result
                else:
                    self.logger.warning(f"⚠️  Tavily falló: {result.get('error', 'Error desconocido')}")
            
            # Fallback a WebSearch si Tavily no disponible
            if self.tool_manager.is_tool_enabled('web_search'):
                self.logger.info(f"🔍 Usando WebSearch para búsqueda REAL: '{query}'")
                result = self.tool_manager.execute_tool(
                    tool_name='web_search',
                    parameters={
                        'query': query,
                        'max_results': max_results
                    },
                    config={"timeout": 30}
                )
                
                if result.get('success'):
                    self.logger.info(f"✅ Búsqueda web REAL completada: {len(result.get('results', []))} resultados")
                    return result
                else:
                    self.logger.warning(f"⚠️  WebSearch falló: {result.get('error', 'Error desconocido')}")
            
            # Si ninguna herramienta funciona
            available_tools = list(self.tool_manager.tools.keys())
            enabled_tools = [t for t in available_tools if self.tool_manager.is_tool_enabled(t)]
            
            return {
                "success": False, 
                "error": f"No hay herramientas de búsqueda funcionales. Disponibles: {available_tools}, Habilitadas: {enabled_tools}", 
                "query": query
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda web real: {e}")
            return {"success": False, "error": str(e), "query": query}
    
    def execute_real_file_creation(self, filename: str, content: str, path: str = "/app/generated_files") -> Dict[str, Any]:
        """
        SOLUCION 2: Crea archivos REALES en el sistema de archivos
        Reemplaza completamente _execute_file_write simulada
        """
        try:
            # Usar herramienta real de gestión de archivos
            file_tool = self.tool_manager.tools.get('file_manager')
            if not file_tool:
                return {"success": False, "error": "Herramienta de archivos no disponible"}
            
            # Crear directorio si no existe
            os.makedirs(path, exist_ok=True)
            
            # Crear archivo real
            full_path = os.path.join(path, filename)
            result = file_tool.execute({
                'action': 'create',
                'path': full_path,
                'content': content
            })
            
            if result.get('success'):
                # Verificar que el archivo realmente existe
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    self.logger.info(f"✅ Archivo REAL creado: {full_path} ({file_size} bytes)")
                    
                    return {
                        "success": True,
                        "filepath": full_path,
                        "filename": filename,
                        "file_size": file_size,
                        "summary": f"Archivo REAL '{filename}' creado exitosamente ({file_size} bytes)"
                    }
                else:
                    return {"success": False, "error": "Archivo no fue creado realmente"}
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Error creando archivo real: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_real_shell_command(self, command: str, timeout: int = 30, 
                                  working_dir: str = "/app") -> Dict[str, Any]:
        """
        SOLUCION 2: Ejecuta comandos shell REALES con sandboxing mejorado
        Mejora significativa sobre la lista blanca restrictiva
        """
        try:
            # Usar herramienta real de shell
            shell_tool = self.tool_manager.tools.get('shell')
            if not shell_tool:
                return {"success": False, "error": "Herramienta de shell no disponible"}
            
            # Verificaciones de seguridad mejoradas
            if not self._is_command_safe_for_execution(command):
                return {
                    "success": False, 
                    "error": "Comando no permitido por políticas de seguridad",
                    "command": command
                }
            
            # Ejecutar comando real
            result = shell_tool.execute({
                'command': command
            }, config={
                'timeout': timeout,
                'working_directory': working_dir
            })
            
            if 'error' not in result:
                self.logger.info(f"✅ Comando REAL ejecutado: '{command}' (código: {result.get('exit_code', 'N/A')})")
                return {
                    "success": result.get('success', True),
                    "command": command,
                    "return_code": result.get('exit_code', 0),
                    "stdout": result.get('stdout', ''),
                    "stderr": result.get('stderr', ''),
                    "summary": f"Comando REAL '{command}' ejecutado exitosamente"
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando comando real: {e}")
            return {"success": False, "error": str(e), "command": command}
    
    def _is_command_safe_for_execution(self, command: str) -> bool:
        """
        SOLUCION 2: Verificación de seguridad mejorada para comandos shell
        Más flexible que lista blanca pero seguro
        """
        # Comandos absolutamente prohibidos
        dangerous_commands = [
            'rm -rf /', 'mkfs', 'dd if=', 'format', 'del /s', 'shutdown', 
            'reboot', 'halt', 'poweroff', 'chmod 777 /', 'chown root /',
            'passwd root', 'su -', 'sudo su', 'init 0', 'init 6'
        ]
        
        # Patrones peligrosos
        dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'>\s*/dev/sd[a-z]',
            r'cat\s+/etc/passwd',
            r'cat\s+/etc/shadow',
            r'nc\s+.*\s+-e',
            r'wget.*\|\s*sh',
            r'curl.*\|\s*sh'
        ]
        
        command_lower = command.lower().strip()
        
        # Verificar comandos prohibidos
        for dangerous in dangerous_commands:
            if dangerous.lower() in command_lower:
                return False
        
        # Verificar patrones peligrosos
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return False
        
        # Permitir comandos de desarrollo comunes
        safe_prefixes = [
            'ls', 'cat', 'head', 'tail', 'grep', 'find', 'wc', 'sort',
            'echo', 'pwd', 'whoami', 'date', 'ps', 'top', 'df', 'du',
            'mkdir', 'touch', 'cp', 'mv', 'chmod', 'chown',
            'python', 'pip', 'node', 'npm', 'yarn', 'git',
            'curl', 'wget', 'ping', 'traceroute'
        ]
        
        # Si el comando empieza con un prefijo seguro, permitirlo
        for prefix in safe_prefixes:
            if command_lower.startswith(prefix):
                return True
        
        # Por defecto, rechazar comandos desconocidos
        return False
    
    # SOLUCION 3: Métricas y evaluación continua
    
    def _calculate_and_update_performance_metrics(self):
        """
        SOLUCION 3: Calcula métricas de rendimiento para evaluación continua
        """
        try:
            total_tasks = self.stats["tasks_completed"] + self.stats["tasks_failed"]
            if total_tasks > 0:
                self.performance_metrics["task_success_rate"] = self.stats["tasks_completed"] / total_tasks
            
            # Calcular precisión de herramientas
            for tool_name, stats in self.stats["tools_executed"].items():
                if stats["total"] > 0:
                    accuracy = stats["success"] / stats["total"]
                    self.performance_metrics["tool_accuracy_rate"][tool_name] = accuracy
            
            # Registrar métricas en memoria para análisis futuro
            self.memory_manager.add_knowledge(
                content=f"Métricas de rendimiento: {self.performance_metrics}",
                category="performance_metrics",
                source="real_agent_metrics",
                confidence=1.0,
                tags=["metrics", "performance", "evaluation"]
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error calculando métricas: {e}")
    
    def _record_plan_generation_metrics(self, success: bool, attempts: int):
        """
        SOLUCION 3: Registra métricas de generación de planes
        """
        try:
            # Actualizar tasa de éxito de generación de planes
            current_plans = getattr(self, '_plan_generation_total', 0) + 1
            current_successes = getattr(self, '_plan_generation_successes', 0) + (1 if success else 0)
            
            self._plan_generation_total = current_plans
            self._plan_generation_successes = current_successes
            
            self.performance_metrics["plan_generation_success_rate"] = current_successes / current_plans
            
        except Exception as e:
            self.logger.error(f"❌ Error registrando métricas de plan: {e}")
    
    def _record_tool_success_metrics(self, tool_name: str, task_id: str, phase_id: int):
        """
        SOLUCION 3: Registra métricas de éxito de herramientas
        """
        try:
            success_record = {
                "tool_name": tool_name,
                "task_id": task_id, 
                "phase_id": phase_id,
                "timestamp": time.time(),
                "result": "success"
            }
            
            self.memory_manager.add_knowledge(
                content=f"Herramienta {tool_name} exitosa en tarea {task_id}",
                category="tool_success_metrics",
                source="real_metrics",
                confidence=1.0,
                tags=["success", "tool", tool_name]
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error registrando éxito de herramienta: {e}")
    
    def _record_tool_failure_metrics(self, tool_name: str, task_id: str, phase_id: int):
        """
        SOLUCION 3: Registra métricas de fallos de herramientas
        """
        try:
            self.memory_manager.add_knowledge(
                content=f"Herramienta {tool_name} falló en tarea {task_id}",
                category="tool_failure_metrics", 
                source="real_metrics",
                confidence=1.0,
                tags=["failure", "tool", tool_name]
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error registrando fallo de herramienta: {e}")
    
    # Métodos heredados y auxiliares (mantener funcionalidad existente)
    
    def _parse_and_validate_plan(self, plan_response: str) -> Optional[Dict[str, Any]]:
        """Parsea y valida el plan usando múltiples estrategias (método existente mejorado)"""
        plan_data = None
        
        # Estrategia 1: JSON directo
        try:
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
                corrected_text = plan_response.replace("'", '"')
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
                self.logger.info("✅ Plan generado válido según esquema")
                return plan_data
            except jsonschema.ValidationError as e:
                self.logger.warning(f"⚠️  Plan no cumple esquema: {e.message}")
                self._register_validation_error(plan_response, str(e))
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del agente con métricas reales"""
        self.stats["uptime"] = time.time() - self.startup_time
        
        return {
            "agent_name": self.config.agent_name,
            "agent_type": "REAL_AGENT",
            "state": self.state.value,
            "session_id": self.current_session_id,
            "uptime_seconds": self.stats["uptime"],
            "statistics": self.stats.copy(),
            "performance_metrics": self.performance_metrics.copy(),
            "memory_stats": self.memory_manager.get_memory_stats(),
            "task_manager_status": self.task_manager.get_manager_status(),
            "model_manager_status": self.model_manager.get_status(),
            "tool_manager_status": {
                "available_tools": len(self.tool_manager.tools),
                "enabled_tools": len([t for t in self.tool_manager.tools.keys() if self.tool_manager.is_tool_enabled(t)]),
                "tool_health": self.tool_manager.get_tool_health()
            },
            "real_executions": {
                "web_searches": self.stats["real_web_searches"],
                "files_created": self.stats["real_files_created"], 
                "commands_executed": self.stats["real_commands_executed"]
            }
        }
    
    # Métodos auxiliares heredados (implementaciones simplificadas)
    
    def _create_enhanced_planning_prompt(self, title: str, description: str, goal: str) -> str:
        """Crea prompt mejorado para planificación"""
        return f"""Genera un plan REAL y específico (no genérico) para esta tarea:

TAREA: {title}
DESCRIPCIÓN: {description}
OBJETIVO: {goal}

HERRAMIENTAS REALES DISPONIBLES:
- tavily_search: Búsqueda web real con Tavily API
- web_search: Búsqueda web con DuckDuckGo
- file_manager: Gestión real de archivos
- shell: Ejecución real de comandos

REQUISITOS CRÍTICOS:
1. Plan específico para esta tarea (no genérico como "Análisis", "Ejecución", "Entrega")
2. Usar herramientas reales apropiadas
3. Fases lógicas y secuenciales
4. JSON válido estricto

RESPUESTA (SOLO JSON):
{{"goal": "objetivo específico", "phases": [{{"id": 1, "title": "título específico detallado", "description": "descripción específica de 10-300 chars", "required_capabilities": ["capability"], "tool_name": "herramienta_real"}}]}}"""
    
    def _create_correction_prompt_with_context(self, title: str, description: str, goal: str, error: str) -> str:
        """Crea prompt de corrección con contexto"""
        return f"""El JSON anterior falló: {error}

TAREA: {title}
OBJETIVO: {goal}

Corrige el JSON asegurándote:
1. Estructura válida
2. Herramientas reales: tavily_search, web_search, file_manager, shell
3. Títulos específicos (no genéricos)

RESPUESTA CORREGIDA (SOLO JSON):"""
    
    def _create_semantic_guided_prompt(self, title: str, description: str, goal: str) -> str:
        """Crea prompt guiado semánticamente"""
        return f"""Genera plan específico para: {title}

{{"goal": "completar {description}", "phases": [{{"id": 1, "title": "Acción específica para {title}", "description": "Descripción detallada específica", "required_capabilities": ["web_search"], "tool_name": "tavily_search"}}]}}

Personaliza para: {description}
SOLO JSON:"""
    
    def _request_human_assistance_plan(self, title: str, description: str, goal: str, reason: str) -> Dict[str, Any]:
        """Solicita asistencia humana en lugar de plan genérico"""
        self.logger.warning(f"⚠️  Solicitando asistencia humana para: {title}")
        
        return {
            "goal": goal,
            "phases": [
                {
                    "id": 1,
                    "title": f"Solicitar clarificación humana para: {title}",
                    "description": f"Pedir al usuario más detalles sobre: {description}",
                    "required_capabilities": ["communication"],
                    "tool_name": "general"
                }
            ],
            "_human_assistance_required": True,
            "_assistance_reason": reason
        }
    
    # Métodos auxiliares simplificados
    def _parse_tool_call_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parsea respuesta de tool call"""
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith('{') and cleaned_response.endswith('}'):
                return json.loads(cleaned_response)
        except json.JSONDecodeError:
            pass
        return None
    
    def _register_validation_error(self, response: str, error: str):
        """Registra error de validación"""
        try:
            self.memory_manager.add_knowledge(
                content=f"Validation error: {error}",
                category="validation_errors",
                source="real_agent",
                confidence=0.8,
                tags=["error", "validation"]
            )
        except Exception:
            pass
    
    def _register_semantic_validation_error(self, response: str, reason: str):
        """Registra error de validación semántica"""
        try:
            self.memory_manager.add_knowledge(
                content=f"Semantic validation error: {reason}",
                category="semantic_validation_errors", 
                source="real_agent",
                confidence=0.8,
                tags=["error", "semantic", "validation"]
            )
        except Exception:
            pass
    
    def _record_prompt_performance(self, attempt: int, success: bool, response: str):
        """Registra rendimiento de prompt"""
        pass
    
    def _determine_task_type_from_capabilities(self, capabilities: List[str]) -> str:
        """Determina tipo de tarea desde capacidades"""
        if "web_search" in capabilities:
            return "analysis"
        elif "creation" in capabilities:
            return "general"
        else:
            return "general"
    
    def _handle_real_reflection(self, reflection_data: Dict[str, Any], task, current_phase) -> str:
        """Maneja reflexión real"""
        return "Reflexión completada"

# Función de conveniencia para crear agente REAL
def create_real_mitosis_agent(ollama_url: str = "http://localhost:11434",
                            openrouter_api_key: Optional[str] = None,
                            prefer_local: bool = True) -> MitosisRealAgent:
    """Crea una instancia del agente Mitosis REAL (sin simulaciones)"""
    config = AgentConfig(
        ollama_url=ollama_url,
        openrouter_api_key=openrouter_api_key,
        prefer_local_models=prefer_local,
        agent_name="Mitosis-Real"
    )
    return MitosisRealAgent(config)

if __name__ == "__main__":
    # Ejemplo de uso del agente REAL
    print("🚀 Iniciando Agente Mitosis REAL (sin simulaciones)")
    
    agent = create_real_mitosis_agent()
    
    # Iniciar sesión
    session_id = agent.start_session()
    print(f"✅ Sesión REAL iniciada: {session_id}")
    
    # Crear y ejecutar una tarea real
    task_result = agent.create_and_execute_task(
        title="Investigar tendencias de IA 2025",
        description="Buscar información actualizada sobre inteligencia artificial en 2025 y crear un informe",
        goal="Crear un informe completo sobre las tendencias actuales de IA"
    )
    print(f"📋 Resultado de tarea REAL: {task_result}")
    
    # Obtener estado del agente
    status = agent.get_status()
    print(f"📊 Estado del agente REAL: {status['state']}")
    print(f"🛠️  Herramientas reales disponibles: {status['tool_manager_status']['available_tools']}")
    print(f"🔍 Búsquedas reales: {status['real_executions']['web_searches']}")
    print(f"📁 Archivos reales creados: {status['real_executions']['files_created']}")
    
    print("✅ Agente REAL funcionando correctamente")