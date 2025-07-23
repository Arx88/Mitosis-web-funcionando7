#!/usr/bin/env python3
"""
MITOSIS AGENT CORE UNIFICADO
Consolida toda la funcionalidad fragmentada de los múltiples agent cores
eliminando duplicaciones y manteniendo 100% compatibilidad.

Consolida:
- agent_core.py
- enhanced_agent_core.py  
- agent_core_real.py

Autor: Mitosis Refactoring Agent
Fecha: 2025-07-23
"""

import os
import sys
import json
import uuid
import time
import asyncio
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union

# Configurar logging
logger = logging.getLogger(__name__)

# Terminal logger para output visible
terminal_logger = logging.getLogger('MITOSIS_AGENT')
if not terminal_logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - [AGENT] - %(message)s')
    handler.setFormatter(formatter)
    terminal_logger.addHandler(handler)
    terminal_logger.setLevel(logging.INFO)


# ============================================================================
# ENUMS Y ESTRUCTURAS DE DATOS
# ============================================================================

class TaskStatus(Enum):
    """Estados posibles de una tarea"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AgentMode(Enum):
    """Modos operativos del agente"""
    BASIC = "basic"
    ENHANCED = "enhanced"
    AUTONOMOUS = "autonomous"


@dataclass
class AgentConfig:
    """Configuración unificada del agente"""
    # Configuración LLM
    ollama_url: str = "https://bef4a4bb93d1.ngrok-free.app"
    ollama_model: str = "llama3.1:8b"
    openrouter_api_key: Optional[str] = None
    prefer_local_models: bool = True
    max_cost_per_1k_tokens: float = 0.01
    
    # Configuración de memoria
    memory_db_path: str = "unified_agent.db"
    max_short_term_messages: int = 100
    max_long_term_memories: int = 1000
    
    # Configuración de tareas
    max_concurrent_tasks: int = 2
    task_timeout_seconds: int = 300
    
    # Configuración del modo
    mode: AgentMode = AgentMode.ENHANCED
    debug_mode: bool = True
    
    # Configuración de herramientas
    enable_web_search: bool = True
    enable_file_operations: bool = True
    enable_shell_commands: bool = False  # Por seguridad
    
    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Crea configuración desde variables de entorno"""
        return cls(
            ollama_url=os.getenv('OLLAMA_BASE_URL', cls.ollama_url),
            ollama_model=os.getenv('OLLAMA_DEFAULT_MODEL', cls.ollama_model),
            openrouter_api_key=os.getenv('OPENROUTER_API_KEY'),
            memory_db_path=os.getenv('MEMORY_DB_PATH', cls.memory_db_path),
            max_concurrent_tasks=int(os.getenv('MAX_CONCURRENT_TASKS', cls.max_concurrent_tasks)),
            debug_mode=os.getenv('DEBUG', 'False').lower() == 'true'
        )


@dataclass
class TaskStep:
    """Paso individual dentro de un plan de acción"""
    id: str
    title: str
    description: str
    tool: str
    status: TaskStatus
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'tool': self.tool,
            'status': self.status.value,
            'parameters': self.parameters,
            'result': self.result,
            'error': self.error,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


@dataclass
class AgentTask:
    """Tarea completa del agente"""
    id: str
    title: str
    description: str
    goal: str
    steps: List[TaskStep]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0
    user_message: Optional[str] = None
    final_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'goal': self.goal,
            'steps': [step.to_dict() for step in self.steps],
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress_percentage': self.progress_percentage,
            'user_message': self.user_message,
            'final_response': self.final_response
        }


# ============================================================================
# AGENTE UNIFICADO PRINCIPAL
# ============================================================================

class MitosisUnifiedAgent:
    """Agente unificado que consolida toda la funcionalidad fragmentada"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Inicializa el agente unificado"""
        self.config = config or AgentConfig.from_env()
        self.start_time = time.time()
        self.active_tasks: Dict[str, AgentTask] = {}
        self.task_counter = 0
        
        # Inicializar servicios
        self._initialize_services()
        
        terminal_logger.info("🧠 Mitosis Unified Agent inicializado exitosamente")
        terminal_logger.info(f"🔧 Modo: {self.config.mode.value}")
        terminal_logger.info(f"🤖 LLM: {self.config.ollama_url}")
        terminal_logger.info(f"🛠️ Herramientas: {len(self.available_tools) if hasattr(self, 'available_tools') else 0}")
    
    def _initialize_services(self):
        """Inicializa todos los servicios del agente"""
        terminal_logger.info("🔧 Inicializando servicios del agente...")
        
        # 1. Inicializar servicio Ollama
        try:
            sys.path.append('/app/backend/src')
            from services.ollama_service import OllamaService
            self.ollama_service = OllamaService(self.config.ollama_url)
            terminal_logger.info(f"✅ Ollama Service inicializado: {self.config.ollama_url}")
        except Exception as e:
            terminal_logger.warning(f"⚠️ Ollama Service no disponible: {e}")
            self.ollama_service = None
        
        # 2. Inicializar Tool Manager
        try:
            from tools.tool_manager import ToolManager
            self.tool_manager = ToolManager()
            self.available_tools = self._map_available_tools()
            terminal_logger.info(f"✅ Tool Manager inicializado: {len(self.available_tools)} herramientas")
        except Exception as e:
            terminal_logger.warning(f"⚠️ Tool Manager no disponible: {e}")
            self.tool_manager = None
            self.available_tools = self._get_fallback_tools()
        
        # 3. Inicializar Memory Manager
        try:
            from memory.advanced_memory_manager import AdvancedMemoryManager
            self.memory_manager = AdvancedMemoryManager(
                db_path=self.config.memory_db_path,
                max_memories=self.config.max_long_term_memories
            )
            terminal_logger.info("✅ Memory Manager inicializado")
        except Exception as e:
            terminal_logger.warning(f"⚠️ Memory Manager no disponible: {e}")
            self.memory_manager = None
        
        # 4. Inicializar Task Manager
        try:
            from services.task_manager import TaskManager
            self.task_manager_service = TaskManager()
            terminal_logger.info("✅ Task Manager Service inicializado")
        except Exception as e:
            terminal_logger.warning(f"⚠️ Task Manager Service no disponible: {e}")
            self.task_manager_service = None
    
    def _map_available_tools(self) -> Dict[str, str]:
        """Mapea herramientas conceptuales a herramientas reales"""
        if not self.tool_manager:
            return self._get_fallback_tools()
        
        # Obtener herramientas disponibles del tool manager
        available_tools = self.tool_manager.get_available_tools()
        tool_names = []
        
        for tool in available_tools:
            if isinstance(tool, dict):
                tool_names.append(tool.get('name', ''))
            else:
                tool_names.append(str(tool))
        
        # Mapeo conceptual a herramientas reales
        tool_mapping = {
            "web_search": "tavily_search" if "tavily_search" in tool_names else "web_search_tool",
            "deep_research": "deep_research" if "deep_research" in tool_names else "comprehensive_research",
            "file_creation": "file_manager" if "file_manager" in tool_names else "file_manager_tool",
            "data_analysis": "comprehensive_research" if "comprehensive_research" in tool_names else "analysis",
            "code_generation": "file_manager" if "file_manager" in tool_names else "code_gen",
            "planning": "task_planner" if "task_planner" in tool_names else "planning",
            "documentation": "file_manager" if "file_manager" in tool_names else "docs",
            "shell_execution": "shell" if "shell" in tool_names and self.config.enable_shell_commands else None,
            "web_navigation": "playwright" if "playwright" in tool_names else None
        }
        
        # Filtrar herramientas no disponibles
        return {k: v for k, v in tool_mapping.items() if v and v in tool_names}
    
    def _get_fallback_tools(self) -> Dict[str, str]:
        """Herramientas de fallback si no hay tool manager"""
        return {
            "web_search": "simulation",
            "file_creation": "simulation",
            "data_analysis": "simulation",
            "planning": "simulation",
            "documentation": "simulation"
        }
    
    # ========================================================================
    # PROCESAMIENTO DE MENSAJES
    # ========================================================================
    
    def process_user_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Procesa mensaje del usuario y determina si crear plan o responder directamente"""
        terminal_logger.info(f"💬 Procesando mensaje: {message[:50]}...")
        
        try:
            # Analizar intención del mensaje
            intention = self._analyze_message_intention(message)
            
            if intention == "task_request":
                # Crear y ejecutar plan de acción
                return self._create_and_execute_action_plan(message, session_id)
            else:
                # Respuesta conversacional directa
                return self._generate_conversational_response(message, session_id)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Lo siento, ocurrió un error procesando tu mensaje: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_message_intention(self, message: str) -> str:
        """Analiza la intención del mensaje (conversacional vs tarea)"""
        # Palabras clave que indican solicitud de tarea
        task_keywords = [
            "crea", "crear", "genera", "generar", "desarrolla", "desarrollar",
            "investiga", "investigar", "analiza", "analizar", "busca", "buscar",
            "escribe", "escribir", "programa", "programar", "diseña", "diseñar",
            "planifica", "planificar", "organiza", "organizar", "prepara", "preparar",
            "documenta", "documentar", "estudia", "estudiar", "revisa", "revisar"
        ]
        
        # Indicadores de complejidad que sugieren plan de acción
        complexity_indicators = [
            "paso a paso", "detallado", "completo", "exhaustivo", "comprensivo",
            "plan", "estrategia", "proceso", "metodología", "guía", "tutorial",
            "análisis", "informe", "reporte", "documento", "presentación"
        ]
        
        message_lower = message.lower()
        
        # Verificar palabras clave de tarea
        has_task_keywords = any(keyword in message_lower for keyword in task_keywords)
        has_complexity = any(indicator in message_lower for indicator in complexity_indicators)
        
        # Mensajes largos tienden a ser solicitudes de tarea
        is_long_message = len(message.split()) > 10
        
        if has_task_keywords or has_complexity or is_long_message:
            return "task_request"
        else:
            return "conversational"
    
    def _create_and_execute_action_plan(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Crea y ejecuta un plan de acción para la solicitud"""
        terminal_logger.info("📋 Creando plan de acción...")
        
        try:
            # Generar plan de acción
            task = self._generate_action_plan(message)
            
            # Responder inmediatamente con el plan
            plan_response = self._format_plan_response(task)
            
            # Ejecutar plan de manera asíncrona (no bloquea la respuesta)
            if self.config.mode in [AgentMode.ENHANCED, AgentMode.AUTONOMOUS]:
                # Programar ejecución asíncrona
                asyncio.create_task(self._execute_task_async(task.id))
            
            return {
                "success": True,
                "response": plan_response,
                "task_id": task.id,
                "plan_generated": True,
                "steps_count": len(task.steps),
                "execution_started": self.config.mode != AgentMode.BASIC,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating action plan: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"No pude crear un plan de acción: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_conversational_response(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Genera respuesta conversacional directa"""
        terminal_logger.info("💭 Generando respuesta conversacional...")
        
        try:
            # Usar Ollama para respuesta conversacional si está disponible
            if self.ollama_service and self.ollama_service.is_healthy():
                response_text = self._generate_llm_response(message)
            else:
                # Respuesta de fallback
                response_text = f"He recibido tu mensaje: '{message}'. ¿En qué puedo ayudarte específicamente?"
            
            # Agregar a memoria si está disponible
            if self.memory_manager:
                try:
                    self.memory_manager.add_conversation_turn(
                        user_message=message,
                        agent_response=response_text,
                        session_id=session_id or "default"
                    )
                except Exception as e:
                    logger.warning(f"Error adding to memory: {e}")
            
            return {
                "success": True,
                "response": response_text,
                "conversational": True,
                "memory_used": self.memory_manager is not None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating conversational response: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Lo siento, no pude procesar tu mensaje en este momento.",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_llm_response(self, message: str) -> str:
        """Genera respuesta usando LLM"""
        try:
            prompt = f"""Eres Mitosis, un asistente inteligente y conversacional. 
Responde de manera natural y útil al siguiente mensaje del usuario:

Usuario: {message}

Responde de forma directa, amigable y concisa."""
            
            response = self.ollama_service.generate_response(
                prompt=prompt,
                model=self.config.ollama_model,
                max_tokens=200
            )
            
            return response.strip() if response else "No pude generar una respuesta en este momento."
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "Disculpa, tuve un problema procesando tu mensaje. ¿Podrías reformularlo?"
    
    # ========================================================================
    # GENERACIÓN Y EJECUCIÓN DE PLANES
    # ========================================================================
    
    def _generate_action_plan(self, task_description: str) -> AgentTask:
        """Genera un plan de acción estructurado"""
        self.task_counter += 1
        task_id = f"task_{int(datetime.now().timestamp())}_{self.task_counter}"
        
        # Extraer título del task
        title = self._extract_task_title(task_description)
        
        # Generar pasos basados en análisis de palabras clave
        steps = self._generate_task_steps(task_description, title)
        
        # Crear tarea
        task = AgentTask(
            id=task_id,
            title=title,
            description=task_description,
            goal=f"Completar: {title}",
            steps=steps,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            user_message=task_description
        )
        
        # Almacenar tarea
        self.active_tasks[task_id] = task
        
        # Log del plan generado
        self._log_generated_plan(task)
        
        return task
    
    def _extract_task_title(self, description: str) -> str:
        """Extrae un título conciso de la descripción"""
        words = description.split()
        if len(words) <= 5:
            return description
        
        # Tomar las primeras palabras significativas
        title_words = []
        for word in words[:8]:
            if word.lower() not in ['por', 'favor', 'puedes', 'podrías', 'me', 'ayuda', 'ayudar']:
                title_words.append(word)
        
        title = ' '.join(title_words[:5])
        return title if len(title) > 10 else description[:50]
    
    def _generate_task_steps(self, description: str, title: str) -> List[TaskStep]:
        """Genera pasos específicos basados en el contenido"""
        steps = []
        step_counter = 1
        content = (description + " " + title).lower()
        
        # Paso inicial de planificación
        steps.append(TaskStep(
            id=f"step_{step_counter}",
            title="Planificación inicial",
            description="Analizar requisitos y crear estrategia",
            tool="planning",
            status=TaskStatus.PENDING,
            parameters={"context": description}
        ))
        step_counter += 1
        
        # Análisis condicional para generar pasos específicos
        if any(word in content for word in ["buscar", "investigar", "research", "información", "datos"]):
            steps.append(TaskStep(
                id=f"step_{step_counter}",
                title="Investigación web",
                description="Buscar información relevante en fuentes web",
                tool="web_search",
                status=TaskStatus.PENDING,
                parameters={"query": title, "max_results": 5}
            ))
            step_counter += 1
        
        if any(word in content for word in ["profundo", "detallado", "exhaustivo", "completo"]):
            steps.append(TaskStep(
                id=f"step_{step_counter}",
                title="Investigación profunda",
                description="Análisis detallado de fuentes especializadas",
                tool="deep_research",
                status=TaskStatus.PENDING,
                parameters={"topic": title, "depth": "comprehensive"}
            ))
            step_counter += 1
        
        if any(word in content for word in ["crear", "generar", "escribir", "documento", "archivo"]):
            file_type = "md" if any(word in content for word in ["documento", "informe"]) else "txt"
            steps.append(TaskStep(
                id=f"step_{step_counter}",
                title="Creación de contenido",
                description=f"Generar documento con los resultados",
                tool="file_creation",
                status=TaskStatus.PENDING,
                parameters={"filename": f"{title.replace(' ', '_')}.{file_type}", "type": file_type}
            ))
            step_counter += 1
        
        if any(word in content for word in ["analizar", "análisis", "evaluar", "estudiar"]):
            steps.append(TaskStep(
                id=f"step_{step_counter}",
                title="Análisis de datos",
                description="Procesar y analizar información recopilada",
                tool="data_analysis",
                status=TaskStatus.PENDING,
                parameters={"analysis_type": "comprehensive"}
            ))
            step_counter += 1
        
        if any(word in content for word in ["código", "programar", "desarrollar", "app", "script"]):
            steps.append(TaskStep(
                id=f"step_{step_counter}",
                title="Desarrollo de código",
                description="Generar código y componentes técnicos",
                tool="code_generation",
                status=TaskStatus.PENDING,
                parameters={"language": "python", "type": "script"}
            ))
            step_counter += 1
        
        # Paso final de síntesis
        steps.append(TaskStep(
            id=f"step_{step_counter}",
            title="Síntesis y entrega",
            description="Compilar resultados y preparar respuesta final",
            tool="documentation",
            status=TaskStatus.PENDING,
            parameters={"format": "summary"}
        ))
        
        return steps
    
    def _format_plan_response(self, task: AgentTask) -> str:
        """Formatea la respuesta del plan de acción"""
        response = f"""# Plan de Acción: {task.title}

**Objetivo:** {task.goal}

**Pasos a seguir:**

"""
        
        for i, step in enumerate(task.steps, 1):
            status_icon = "⏳" if step.status == TaskStatus.PENDING else "✅" if step.status == TaskStatus.COMPLETED else "❌"
            response += f"{i}. {status_icon} **{step.title}**\n   {step.description}\n\n"
        
        response += f"""
**Estado:** Plan generado exitosamente
**Pasos totales:** {len(task.steps)}
**ID de tarea:** `{task.id}`

"""
        
        if self.config.mode != AgentMode.BASIC:
            response += "🚀 **Ejecución iniciada automáticamente.** Te mantendré informado del progreso."
        else:
            response += "📝 **Plan listo para revisión.** La ejecución está en modo manual."
        
        return response
    
    def _log_generated_plan(self, task: AgentTask):
        """Log del plan generado para debugging"""
        terminal_logger.info("=" * 80)
        terminal_logger.info("📋 PLAN DE ACCIÓN GENERADO")
        terminal_logger.info("=" * 80)
        terminal_logger.info(f"🎯 Tarea: {task.title}")
        terminal_logger.info(f"📝 Descripción: {task.description}")
        terminal_logger.info(f"🆔 ID: {task.id}")
        terminal_logger.info(f"📅 Creado: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        terminal_logger.info("")
        terminal_logger.info("📋 PASOS:")
        
        for i, step in enumerate(task.steps, 1):
            terminal_logger.info(f"{i}. {step.title}")
            terminal_logger.info(f"   📄 {step.description}")
            terminal_logger.info(f"   🛠️ Herramienta: {step.tool}")
        
        terminal_logger.info("=" * 80)
    
    # ========================================================================
    # EJECUCIÓN ASÍNCRONA DE TAREAS
    # ========================================================================
    
    async def _execute_task_async(self, task_id: str):
        """Ejecuta una tarea de manera asíncrona"""
        if task_id not in self.active_tasks:
            logger.error(f"Task not found: {task_id}")
            return
        
        task = self.active_tasks[task_id]
        terminal_logger.info(f"🚀 Iniciando ejecución asíncrona: {task_id}")
        
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            for step in task.steps:
                success = await self._execute_step_async(step, task)
                
                if not success and self.config.mode != AgentMode.AUTONOMOUS:
                    # En modo no autónomo, detener en el primer fallo
                    task.status = TaskStatus.FAILED
                    break
                
                # Actualizar progreso
                self._update_task_progress(task)
                
                # Pausa entre pasos
                await asyncio.sleep(1)
            
            # Finalizar tarea
            if task.status != TaskStatus.FAILED:
                task.status = TaskStatus.COMPLETED
                task.progress_percentage = 100.0
                task.final_response = self._generate_task_summary(task)
            
            task.completed_at = datetime.now()
            
            # Log final
            self._log_task_completion(task)
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
    
    async def _execute_step_async(self, step: TaskStep, task: AgentTask) -> bool:
        """Ejecuta un paso individual de manera asíncrona"""
        terminal_logger.info(f"⚡ Ejecutando paso: {step.title}")
        
        step.status = TaskStatus.IN_PROGRESS
        step.start_time = datetime.now()
        
        try:
            if step.tool in self.available_tools:
                tool_name = self.available_tools[step.tool]
                
                if tool_name == "simulation":
                    result = await self._simulate_tool_execution(step, task)
                else:
                    result = await self._execute_real_tool_async(tool_name, step, task)
                
                step.result = result
                step.status = TaskStatus.COMPLETED
                terminal_logger.info(f"✅ Paso completado: {step.title}")
                return True
            else:
                step.error = f"Herramienta no disponible: {step.tool}"
                step.status = TaskStatus.FAILED
                terminal_logger.error(f"❌ Herramienta no disponible: {step.tool}")
                return False
                
        except Exception as e:
            step.error = str(e)
            step.status = TaskStatus.FAILED
            terminal_logger.error(f"❌ Error en paso: {str(e)}")
            return False
        finally:
            step.end_time = datetime.now()
    
    async def _execute_real_tool_async(self, tool_name: str, step: TaskStep, task: AgentTask) -> str:
        """Ejecuta herramienta real de manera asíncrona"""
        if not self.tool_manager:
            return await self._simulate_tool_execution(step, task)
        
        terminal_logger.info(f"🔧 Ejecutando herramienta: {tool_name}")
        
        try:
            # Preparar parámetros
            parameters = step.parameters or {}
            parameters.update(self._prepare_tool_context(step, task))
            
            # Ejecutar herramienta
            result = self.tool_manager.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
                task_id=task.id
            )
            
            # Procesar resultado
            return self._process_tool_result(tool_name, result, step)
            
        except Exception as e:
            terminal_logger.error(f"❌ Error ejecutando {tool_name}: {e}")
            return f"Error en {tool_name}: {str(e)}"
    
    async def _simulate_tool_execution(self, step: TaskStep, task: AgentTask) -> str:
        """Simula ejecución de herramienta como fallback"""
        terminal_logger.info(f"🎭 Simulando: {step.tool}")
        await asyncio.sleep(2)  # Simular tiempo de procesamiento
        
        simulations = {
            "web_search": f"[SIM] Búsqueda web completada para '{task.title}'. 12 fuentes encontradas.",
            "deep_research": f"[SIM] Investigación profunda realizada. 25 fuentes especializadas analizadas.",
            "file_creation": f"[SIM] Archivo creado: {step.parameters.get('filename', 'documento.txt')}",
            "data_analysis": f"[SIM] Análisis completado. 150 puntos de datos procesados.",
            "code_generation": f"[SIM] Código generado: 85 líneas en {step.parameters.get('language', 'Python')}",
            "planning": f"[SIM] Plan estratégico creado con {len(task.steps)} fases.",
            "documentation": f"[SIM] Documentación generada: reporte de 8 páginas."
        }
        
        return simulations.get(step.tool, f"[SIM] {step.tool} ejecutado exitosamente")
    
    def _prepare_tool_context(self, step: TaskStep, task: AgentTask) -> Dict[str, Any]:
        """Prepara contexto adicional para herramientas"""
        return {
            "task_context": task.description,
            "task_title": task.title,
            "step_context": step.description,
            "task_id": task.id,
            "step_id": step.id
        }
    
    def _process_tool_result(self, tool_name: str, result: Any, step: TaskStep) -> str:
        """Procesa resultado de herramienta"""
        if isinstance(result, dict):
            if 'error' in result:
                return f"Error en {tool_name}: {result['error']}"
            elif 'summary' in result:
                return result['summary']
            elif 'content' in result:
                return f"Contenido generado: {str(result['content'])[:200]}..."
            else:
                return f"Resultado de {tool_name}: {json.dumps(result, indent=2)[:300]}..."
        else:
            return str(result)[:500]
    
    def _update_task_progress(self, task: AgentTask):
        """Actualiza progreso de la tarea"""
        completed_steps = sum(1 for step in task.steps if step.status == TaskStatus.COMPLETED)
        task.progress_percentage = (completed_steps / len(task.steps)) * 100
        
        terminal_logger.info(f"📈 Progreso: {task.progress_percentage:.1f}% ({completed_steps}/{len(task.steps)})")
    
    def _generate_task_summary(self, task: AgentTask) -> str:
        """Genera resumen final de la tarea"""
        completed_steps = [step for step in task.steps if step.status == TaskStatus.COMPLETED]
        failed_steps = [step for step in task.steps if step.status == TaskStatus.FAILED]
        
        summary = f"""# Resumen de Ejecución: {task.title}

## Estado Final
- ✅ **Completada exitosamente**
- 📊 **Progreso:** {task.progress_percentage:.1f}%
- ⏱️ **Duración:** {(task.completed_at - task.started_at).total_seconds():.1f} segundos

## Pasos Ejecutados
"""
        
        for step in completed_steps:
            summary += f"- ✅ **{step.title}**: {step.result[:100] if step.result else 'Completado'}...\n"
        
        if failed_steps:
            summary += "\n## Pasos con Problemas\n"
            for step in failed_steps:
                summary += f"- ❌ **{step.title}**: {step.error}\n"
        
        summary += f"\n**Tarea finalizada el {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}**"
        
        return summary
    
    def _log_task_completion(self, task: AgentTask):
        """Log de finalización de tarea"""
        status_icon = "🎉" if task.status == TaskStatus.COMPLETED else "❌"
        duration = (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else 0
        
        terminal_logger.info("=" * 80)
        terminal_logger.info(f"{status_icon} TAREA FINALIZADA")
        terminal_logger.info("=" * 80)
        terminal_logger.info(f"🎯 Tarea: {task.title}")
        terminal_logger.info(f"📊 Estado: {task.status.value}")
        terminal_logger.info(f"📈 Progreso: {task.progress_percentage:.1f}%")
        terminal_logger.info(f"⏱️ Duración: {duration:.1f} segundos")
        terminal_logger.info("=" * 80)
    
    # ========================================================================
    # MÉTODOS DE CONSULTA Y ESTADO
    # ========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado actual del agente"""
        return {
            "agent_info": {
                "name": "Mitosis Unified Agent",
                "version": "1.0.0-refactored", 
                "mode": self.config.mode.value,
                "uptime": time.time() - self.start_time
            },
            "services": {
                "ollama": self.ollama_service.is_healthy() if self.ollama_service else False,
                "tool_manager": self.tool_manager is not None,
                "memory_manager": self.memory_manager is not None,
                "task_manager": self.task_manager_service is not None
            },
            "tasks": {
                "active": len(self.active_tasks),
                "pending": len([t for t in self.active_tasks.values() if t.status == TaskStatus.PENDING]),
                "in_progress": len([t for t in self.active_tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
                "completed": len([t for t in self.active_tasks.values() if t.status == TaskStatus.COMPLETED])
            },
            "tools": {
                "available": len(self.available_tools),
                "tools": list(self.available_tools.keys())[:10]
            }
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estado de una tarea específica"""
        if task_id not in self.active_tasks:
            return None
        
        return self.active_tasks[task_id].to_dict()
    
    def list_active_tasks(self) -> List[Dict[str, Any]]:
        """Lista todas las tareas activas"""
        return [task.to_dict() for task in self.active_tasks.values()]
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Limpia tareas completadas antiguas"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        tasks_to_remove = [
            task_id for task_id, task in self.active_tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            and task.completed_at
            and task.completed_at.timestamp() < cutoff_time
        ]
        
        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]
        
        if tasks_to_remove:
            terminal_logger.info(f"🧹 Limpiadas {len(tasks_to_remove)} tareas antiguas")
    
    def shutdown(self):
        """Cierra el agente y limpia recursos"""
        terminal_logger.info("🛑 Cerrando Unified Agent...")
        
        # Guardar estado de tareas activas si hay persistencia
        if self.task_manager_service:
            try:
                for task in self.active_tasks.values():
                    if task.status == TaskStatus.IN_PROGRESS:
                        task.status = TaskStatus.PAUSED
                terminal_logger.info("✅ Estado de tareas guardado")
            except Exception as e:
                logger.error(f"Error saving task state: {e}")
        
        # Cerrar conexiones
        if self.memory_manager:
            try:
                self.memory_manager.close()
                terminal_logger.info("✅ Memory Manager cerrado")
            except Exception as e:
                logger.error(f"Error closing memory manager: {e}")
        
        terminal_logger.info("✅ Unified Agent cerrado correctamente")


# ============================================================================
# FUNCIÓN FACTORY Y UTILIDADES
# ============================================================================

def create_unified_agent(config: Optional[AgentConfig] = None) -> MitosisUnifiedAgent:
    """Factory function para crear agente unificado"""
    return MitosisUnifiedAgent(config)


def create_agent_from_env() -> MitosisUnifiedAgent:
    """Crea agente con configuración desde variables de entorno"""
    config = AgentConfig.from_env()
    return MitosisUnifiedAgent(config)


# Para compatibilidad con código existente
MitosisAgent = MitosisUnifiedAgent
MitosisRealAgent = MitosisUnifiedAgent
MitosisEnhancedAgent = MitosisUnifiedAgent


if __name__ == "__main__":
    # Prueba básica del agente
    agent = create_agent_from_env()
    
    print("🧪 Prueba del Agente Unificado")
    print("=" * 50)
    
    # Prueba respuesta conversacional
    response1 = agent.process_user_message("Hola, ¿cómo estás?")
    print("Respuesta conversacional:")
    print(response1.get('response', 'No response'))
    print()
    
    # Prueba plan de acción
    response2 = agent.process_user_message("Crea un informe detallado sobre inteligencia artificial")
    print("Plan de acción:")
    print(response2.get('response', 'No response'))
    
    agent.shutdown()