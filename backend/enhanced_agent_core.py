"""
Enhanced Agent Core - El Cerebro de la Autonomía
Núcleo del sistema de ejecución autónoma para el agente Mitosis-Beta
Gestiona el ciclo de vida completo de tareas complejas con salida en terminal
"""

import logging
import json
import time
import os
import asyncio
import sys
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from collections import defaultdict

# Configurar logging para terminal
terminal_logger = logging.getLogger('MITOSIS')
terminal_handler = logging.StreamHandler(sys.stdout)
terminal_handler.setLevel(logging.INFO)
terminal_formatter = logging.Formatter('%(asctime)s - [MITOSIS] - %(message)s')
terminal_handler.setFormatter(terminal_formatter)
terminal_logger.addHandler(terminal_handler)
terminal_logger.setLevel(logging.INFO)

# Importar componentes base (con manejo de errores)
try:
    from agent_core import MitosisAgent, AgentConfig, AgentState
except ImportError:
    # Fallback si no están disponibles
    MitosisAgent = None
    AgentConfig = None
    AgentState = None

try:
    from enhanced_memory_manager import EnhancedMemoryManager, VectorKnowledgeItem
    from enhanced_task_manager import EnhancedTaskManager
    from model_manager import ModelManager, UnifiedModel, ModelProvider
    from enhanced_prompts import EnhancedPromptManager, PromptType
except ImportError as e:
    terminal_logger.warning(f"⚠️ Algunos componentes no disponibles: {e}")

# ==================================================================================
# CLASES Y ESTRUCTURAS DE DATOS FUNDAMENTALES PARA EJECUCIÓN AUTÓNOMA
# ==================================================================================

class TaskStatus(Enum):
    """Estados posibles de una tarea o paso individual"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class TaskStep:
    """Representa un paso individual dentro de un plan de acción"""
    id: str
    title: str
    description: str
    tool: str
    status: TaskStatus
    result: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self):
        """Convierte el paso a diccionario para serialización"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'tool': self.tool,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

@dataclass  
class AutonomousTask:
    """Representa una tarea autónoma completa con plan de acción"""
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
    
    def calculate_progress(self):
        """Calcula el porcentaje de progreso basado en pasos completados"""
        if not self.steps:
            return 0.0
        
        completed_steps = sum(1 for step in self.steps if step.status == TaskStatus.COMPLETED)
        self.progress_percentage = (completed_steps / len(self.steps)) * 100.0
        return self.progress_percentage
    
    def to_dict(self):
        """Convierte la tarea a diccionario para serialización"""
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
            'progress_percentage': self.progress_percentage
        }

# ==================================================================================
# CLASE PRINCIPAL DEL NÚCLEO AUTÓNOMO
# ==================================================================================

class AutonomousAgentCore:
    """El Cerebro de la Autonomía - Gestiona el ciclo completo de tareas autónomas"""
    
    def __init__(self, base_agent=None):
        """Inicializa el núcleo autónomo con acceso al agente base"""
        self.base_agent = base_agent
        self.active_tasks: Dict[str, AutonomousTask] = {}
        self.logger = terminal_logger
        
        # Registro de herramientas disponibles
        self.available_tools = {
            "web_search": self._execute_web_search,
            "file_creation": self._execute_file_creation,
            "data_analysis": self._execute_data_analysis,
            "code_generation": self._execute_code_generation,
            "research": self._execute_research,
            "planning": self._execute_planning,
            "documentation": self._execute_documentation,
            "testing": self._execute_testing,
        }
        
        self.logger.info("🧠 AutonomousAgentCore inicializado exitosamente")
    
    def generate_action_plan(self, task_title: str, task_description: str = "") -> AutonomousTask:
        """Transforma una solicitud en un AutonomousTask estructurado"""
        try:
            task_id = f"task_{int(time.time())}_{len(self.active_tasks)}"
            
            self.logger.info(f"📋 Generando plan de acción para: {task_title}")
            
            # Generar pasos basado en análisis heurístico
            steps = self._analyze_and_generate_steps(task_title, task_description)
            
            # Crear tarea autónoma
            task = AutonomousTask(
                id=task_id,
                title=task_title,
                description=task_description,
                goal=task_description or task_title,
                steps=steps,
                status=TaskStatus.PENDING,
                created_at=datetime.now()
            )
            
            # Almacenar tarea
            self.active_tasks[task_id] = task
            
            # Mostrar plan en terminal
            self._display_action_plan(task)
            
            return task
            
        except Exception as e:
            self.logger.error(f"❌ Error generando plan de acción: {e}")
            raise
    
    def _analyze_and_generate_steps(self, title: str, description: str) -> List[TaskStep]:
        """Descompone la tarea en pasos ejecutables basado en palabras clave"""
        steps = []
        
        # Paso inicial siempre presente
        steps.append(TaskStep(
            id="step_1",
            title="Planificación inicial",
            description="Analizar los requisitos y crear un plan detallado",
            tool="planning",
            status=TaskStatus.PENDING
        ))
        
        # Análisis heurístico para determinar pasos
        content = (title + " " + description).lower()
        step_id = 2
        
        # Pasos basados en palabras clave
        if any(word in content for word in ["buscar", "investigar", "información", "datos"]):
            steps.append(TaskStep(
                id=f"step_{step_id}",
                title="Investigación y búsqueda",
                description="Buscar información relevante en la web",
                tool="web_search",
                status=TaskStatus.PENDING
            ))
            step_id += 1
        
        if any(word in content for word in ["crear", "generar", "documento", "archivo"]):
            steps.append(TaskStep(
                id=f"step_{step_id}",
                title="Creación de contenido",
                description="Crear archivos y documentos necesarios",
                tool="file_creation",
                status=TaskStatus.PENDING
            ))
            step_id += 1
        
        if any(word in content for word in ["código", "programar", "desarrollar", "implementar"]):
            steps.append(TaskStep(
                id=f"step_{step_id}",
                title="Generación de código",
                description="Desarrollar código y componentes técnicos",
                tool="code_generation",
                status=TaskStatus.PENDING
            ))
            step_id += 1
        
        if any(word in content for word in ["analizar", "estudiar", "evaluar"]):
            steps.append(TaskStep(
                id=f"step_{step_id}",
                title="Análisis de datos",
                description="Analizar y procesar información recopilada",
                tool="data_analysis",
                status=TaskStatus.PENDING
            ))
            step_id += 1
        
        if any(word in content for word in ["documentar", "explicar", "manual"]):
            steps.append(TaskStep(
                id=f"step_{step_id}",
                title="Documentación",
                description="Crear documentación detallada",
                tool="documentation",
                status=TaskStatus.PENDING
            ))
            step_id += 1
        
        # Paso final siempre presente
        steps.append(TaskStep(
            id=f"step_{step_id}",
            title="Validación y entrega",
            description="Verificar resultados y preparar entrega final",
            tool="testing",
            status=TaskStatus.PENDING
        ))
        
        return steps
    
    def _display_action_plan(self, task: AutonomousTask):
        """Muestra el plan de acción en terminal de forma legible"""
        plan_output = f"""
{'='*80}
{'='*80}
📋 PLAN DE ACCIÓN GENERADO
{'='*80}
🎯 Tarea: {task.title}
📝 Descripción: {task.description}
🆔 ID: {task.id}
📅 Creado: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}

📋 PASOS A EJECUTAR:
"""
        
        for i, step in enumerate(task.steps, 1):
            plan_output += f"""
{i}. {step.title}
📄 {step.description}
🛠 Herramienta: {step.tool}
📊 Estado: {step.status.value}"""
        
        plan_output += f"\n{'='*80}"
        
        self.logger.info(plan_output)
    
    async def execute_task_autonomously(self, task_id: str) -> bool:
        """Ejecuta una tarea de forma autónoma paso a paso"""
        try:
            task = self.active_tasks.get(task_id)
            if not task:
                self.logger.error(f"❌ Tarea {task_id} no encontrada")
                return False
            
            self.logger.info("🚀 INICIANDO EJECUCIÓN AUTÓNOMA")
            self.logger.info("="*80)
            
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            for step in task.steps:
                # Actualizar estado del paso
                step.status = TaskStatus.IN_PROGRESS
                step.start_time = datetime.now()
                
                self.logger.info(f"⚡ Ejecutando paso: {step.title}")
                self.logger.info(f"📄 Descripción: {step.description}")
                self.logger.info(f"🛠 Herramienta: {step.tool}")
                
                # Ejecutar herramienta
                try:
                    tool_function = self.available_tools.get(step.tool)
                    if tool_function:
                        result = await tool_function(step, task)
                        step.result = result
                        step.status = TaskStatus.COMPLETED
                        self.logger.info("✅ Paso completado exitosamente")
                        self.logger.info(f"📊 Resultado: {result}")
                    else:
                        step.error = f"Herramienta {step.tool} no disponible"
                        step.status = TaskStatus.FAILED
                        self.logger.error(f"❌ Herramienta {step.tool} no disponible")
                        
                except Exception as e:
                    step.error = str(e)
                    step.status = TaskStatus.FAILED
                    self.logger.error(f"❌ Error ejecutando paso: {e}")
                
                step.end_time = datetime.now()
                
                # Actualizar progreso
                task.calculate_progress()
                self.logger.info(f"📈 Progreso: {task.progress_percentage:.1f}% ({sum(1 for s in task.steps if s.status == TaskStatus.COMPLETED)}/{len(task.steps)})")
                self.logger.info("-" * 40)
                
                # Pausa entre pasos para visibilidad
                await asyncio.sleep(1)
            
            # Finalizar tarea
            all_completed = all(step.status == TaskStatus.COMPLETED for step in task.steps)
            task.status = TaskStatus.COMPLETED if all_completed else TaskStatus.FAILED
            task.completed_at = datetime.now()
            
            if all_completed:
                self.logger.info("🎉 TAREA COMPLETADA EXITOSAMENTE")
            else:
                self.logger.info("⚠️ TAREA COMPLETADA CON ALGUNOS FALLOS")
            
            # Mostrar resumen final
            self._display_task_summary(task)
            
            return all_completed
            
        except Exception as e:
            self.logger.error(f"❌ Error crítico en ejecución autónoma: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id].status = TaskStatus.FAILED
            return False
    
    def _display_task_summary(self, task: AutonomousTask):
        """Muestra resumen final de la ejecución"""
        duration = 0
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
        
        summary = f"""
{'='*80}
📊 RESUMEN DE EJECUCIÓN
{'='*80}
🎯 Tarea: {task.title}
📊 Estado final: {task.status.value}
📈 Progreso: {task.progress_percentage}%
⏱️ Duración: {duration:.1f} segundos

📋 RESUMEN DE PASOS:
"""
        
        for step in task.steps:
            status_icon = "✅" if step.status == TaskStatus.COMPLETED else "❌"
            summary += f"{status_icon} {step.id}. {step.title} - {step.status.value}\n"
        
        summary += "="*80
        
        self.logger.info(summary)
    
    # ==================================================================================
    # MÉTODOS DE HERRAMIENTAS (SIMULADOS)
    # ==================================================================================
    
    async def _execute_web_search(self, step: TaskStep, task: AutonomousTask) -> str:
        """Simula búsqueda web"""
        self.logger.info("🔍 Ejecutando búsqueda web...")
        await asyncio.sleep(2)  # Simular tiempo de ejecución
        return f"Búsqueda completada para: {task.title}. Se encontraron 15 resultados relevantes."
    
    async def _execute_file_creation(self, step: TaskStep, task: AutonomousTask) -> str:
        """Simula creación de archivos"""
        self.logger.info("📄 Creando archivos...")
        await asyncio.sleep(1)
        return f"Archivo creado exitosamente para: {step.title}"
    
    async def _execute_data_analysis(self, step: TaskStep, task: AutonomousTask) -> str:
        """Simula análisis de datos"""
        self.logger.info("📊 Analizando datos...")
        await asyncio.sleep(3)
        return f"Análisis de datos completado. Se identificaron 8 patrones relevantes."
    
    async def _execute_code_generation(self, step: TaskStep, task: AutonomousTask) -> str:
        """Simula generación de código"""
        self.logger.info("💻 Generando código...")
        await asyncio.sleep(2)
        return f"Código generado exitosamente para: {step.title}"
    
    async def _execute_research(self, step: TaskStep, task: AutonomousTask) -> str:
        """Simula investigación"""
        self.logger.info("🔬 Realizando investigación...")
        await asyncio.sleep(2)
        return f"Investigación completada. Se recopilaron 12 fuentes relevantes."
    
    async def _execute_planning(self, step: TaskStep, task: AutonomousTask) -> str:
        """Simula planificación"""
        self.logger.info("📋 Realizando planificación detallada...")
        await asyncio.sleep(1)
        return f"Plan detallado creado con {len(task.steps)} pasos y cronograma definido."
    
    async def _execute_documentation(self, step: TaskStep, task: AutonomousTask) -> str:
        """Simula documentación"""
        self.logger.info("📚 Creando documentación...")
        await asyncio.sleep(1)
        return f"Documentación creada exitosamente para: {step.title}"
    
    async def _execute_testing(self, step: TaskStep, task: AutonomousTask) -> str:
        """Simula testing y validación"""
        self.logger.info("🧪 Ejecutando validación y testing...")
        await asyncio.sleep(1)
        return f"Validación completada. Todos los criterios de éxito cumplidos."
    
    # ==================================================================================
    # MÉTODOS DE GESTIÓN Y ESTADO
    # ==================================================================================
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado detallado de una tarea específica"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status.value,
            'progress': task.progress_percentage,
            'steps': [step.to_dict() for step in task.steps],
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'statistics': {
                'total_steps': len(task.steps),
                'completed_steps': sum(1 for step in task.steps if step.status == TaskStatus.COMPLETED),
                'in_progress_steps': sum(1 for step in task.steps if step.status == TaskStatus.IN_PROGRESS),
                'failed_steps': sum(1 for step in task.steps if step.status == TaskStatus.FAILED)
            }
        }
    
    def list_active_tasks(self) -> List[Dict[str, Any]]:
        """Lista todas las tareas activas con resumen de estado"""
        return [
            {
                'task_id': task.id,
                'title': task.title,
                'status': task.status.value,
                'progress': task.progress_percentage,
                'created_at': task.created_at.isoformat()
            }
            for task in self.active_tasks.values()
        ]

# ==================================================================================
# CLASES HEREDADAS PARA COMPATIBILIDAD
# ==================================================================================

@dataclass
class ReflectionEntry:
    """Entrada de reflexión para aprendizaje (compatibilidad)"""
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
    """Plantilla de prompt mejorada (compatibilidad)"""
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
    """Métricas de aprendizaje del agente (compatibilidad)"""
    total_reflections: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    success_rate: float = 0.0
    improvement_rate: float = 0.0
    knowledge_growth: float = 0.0
    prompt_optimization_score: float = 0.0

class CognitiveMode(Enum):
    """Modos cognitivos del agente (compatibilidad)"""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    PRACTICAL = "practical"
    REFLECTIVE = "reflective"
    ADAPTIVE = "adaptive"

class EnhancedMitosisAgent:
    """Agente Mitosis mejorado con capacidades cognitivas avanzadas y autonomía"""
    
    def __init__(self, config=None):
        """Inicializa el agente mejorado con núcleo autónomo"""
        self.config = config or {}
        self.logger = terminal_logger
        
        # Núcleo autónomo integrado
        self.autonomous_core = AutonomousAgentCore(self)
        
        # Capacidades cognitivas (compatibilidad)
        self.reflection_history: List[ReflectionEntry] = []
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.learning_metrics = LearningMetrics()
        self.cognitive_mode = CognitiveMode.ADAPTIVE
        
        # Configuración de aprendizaje
        self.learning_enabled = True
        self.reflection_threshold = 0.7
        self.prompt_optimization_enabled = True
        self.max_reflection_history = 1000
        
        # Patrones aprendidos
        self.learned_patterns: Dict[str, float] = {}
        self.action_outcomes: Dict[str, List[bool]] = defaultdict(list)
        
        # Estadísticas cognitivas
        self.cognitive_stats = {
            "reflections_performed": 0,
            "patterns_learned": 0,
            "prompts_optimized": 0,
            "cognitive_mode_changes": 0,
            "successful_adaptations": 0
        }
        
        self.logger.info("🧠 Enhanced Mitosis Agent con núcleo autónomo inicializado")
    
    def process_user_message_enhanced(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Procesa un mensaje del usuario con capacidades mejoradas"""
        try:
            self.logger.info(f"💬 Procesando mensaje: {message[:50]}...")
            
            # Respuesta mejorada con capacidades autónomas
            response = f"""Como agente mejorado con capacidades autónomas, he recibido tu mensaje: "{message}"

Puedo ayudarte con:
🤖 Ejecución autónoma de tareas complejas
📊 Análisis y procesamiento de información
💻 Generación de código y documentación
🔍 Investigación y búsqueda de datos
📋 Planificación y organización de proyectos

Para activar la ejecución autónoma, utiliza palabras clave como:
- "crear", "generar", "desarrollar"
- "investigar", "analizar", "buscar"
- "planificar", "organizar", "diseñar"

¿Te gustaría que ejecute alguna tarea de forma autónoma?"""
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando mensaje: {e}")
            return f"Error interno: {str(e)}"
    
    def enhanced_reflect_on_action(self, action: str, result: str, expected: str,
                                 context: Optional[Dict[str, Any]] = None) -> ReflectionEntry:
        """Reflexión mejorada sobre una acción con aprendizaje"""
        try:
            reflection_id = f"reflection_{int(time.time())}_{len(self.reflection_history)}"
            
            # Evaluar éxito de la acción
            success = self._evaluate_action_success(action, result, expected)
            
            # Crear entrada de reflexión
            reflection_entry = ReflectionEntry(
                id=reflection_id,
                action=action,
                expected_outcome=expected,
                actual_outcome=result,
                success=success,
                confidence=0.8,
                context=context or {},
                timestamp=time.time(),
                learned_patterns=[]
            )
            
            # Añadir a historial
            self.reflection_history.append(reflection_entry)
            
            # Mantener límite de historial
            if len(self.reflection_history) > self.max_reflection_history:
                self.reflection_history.pop(0)
            
            # Actualizar métricas de aprendizaje
            self._update_learning_metrics(success)
            
            self.logger.info(f"🔍 Reflexión realizada: {reflection_id} - Éxito: {success}")
            return reflection_entry
            
        except Exception as e:
            self.logger.error(f"❌ Error en reflexión mejorada: {e}")
            return ReflectionEntry(
                id=f"reflection_error_{int(time.time())}",
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
        success_indicators = ["exitoso", "completado", "correcto", "funciona", "resuelto"]
        failure_indicators = ["error", "fallo", "incorrecto", "problema", "falló"]
        
        result_lower = result.lower()
        
        success_score = sum(1 for indicator in success_indicators if indicator in result_lower)
        failure_score = sum(1 for indicator in failure_indicators if indicator in result_lower)
        
        return success_score > failure_score
    
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
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Obtiene el estado mejorado del agente"""
        try:
            enhanced_status = {
                "agent_type": "enhanced_mitosis_agent",
                "autonomous_core_available": True,
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
                "prompt_templates_count": len(self.prompt_templates),
                "active_autonomous_tasks": len(self.autonomous_core.active_tasks),
                "available_tools": list(self.autonomous_core.available_tools.keys())
            }
            
            return enhanced_status
            
        except Exception as e:
            self.logger.error(f"❌ Error en get_enhanced_status: {e}")
            return {
                "error": "Error obteniendo estado enhanced",
                "agent_type": "enhanced_mitosis_agent",
                "autonomous_core_available": True
            }

# ==================================================================================
# EJEMPLO DE USO Y PRUEBAS
# ==================================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear agente mejorado
    enhanced_agent = EnhancedMitosisAgent()
    
    print("🧠 Probando Enhanced Mitosis Agent con Núcleo Autónomo...")
    
    # Crear núcleo autónomo independiente
    autonomous_core = AutonomousAgentCore()
    
    # Generar plan de acción
    task = autonomous_core.generate_action_plan(
        "Crear un informe sobre inteligencia artificial",
        "Investigar y crear un documento completo sobre IA en 2024"
    )
    
    print(f"✅ Plan generado con ID: {task.id}")
    print(f"📊 Número de pasos: {len(task.steps)}")
    
    # Simular ejecución (en entorno real sería asíncrona)
    print("🚀 Para ejecutar la tarea de forma autónoma:")
    print(f"await autonomous_core.execute_task_autonomously('{task.id}')")
    
    # Obtener estado
    status = autonomous_core.get_task_status(task.id)
    print(f"📈 Estado de la tarea: {status['status'] if status else 'No encontrada'}")
    
    # Probar agente mejorado
    response = enhanced_agent.process_user_message_enhanced(
        "Crea un plan para desarrollar una aplicación web"
    )
    print(f"🤖 Respuesta del agente: {response[:100]}...")
    
    print("✅ Pruebas completadas - Sistema listo para ejecución autónoma")

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

class EnhancedMitosisAgent:
    """Agente Mitosis mejorado con capacidades cognitivas avanzadas y autonomía"""
    
    def __init__(self, config=None):
        """Inicializa el agente mejorado con núcleo autónomo"""
        self.config = config or {}
        self.logger = terminal_logger
        
        # Núcleo autónomo integrado
        self.autonomous_core = AutonomousAgentCore(self)
        
        # Capacidades cognitivas (compatibilidad)
        self.reflection_history: List[ReflectionEntry] = []
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.learning_metrics = LearningMetrics()
        self.cognitive_mode = CognitiveMode.ADAPTIVE
        
        # Configuración de aprendizaje
        self.learning_enabled = True
        self.reflection_threshold = 0.7
        self.prompt_optimization_enabled = True
        self.max_reflection_history = 1000
        
        # Patrones aprendidos
        self.learned_patterns: Dict[str, float] = {}
        self.action_outcomes: Dict[str, List[bool]] = defaultdict(list)
        
        # Estadísticas cognitivas
        self.cognitive_stats = {
            "reflections_performed": 0,
            "patterns_learned": 0,
            "prompts_optimized": 0,
            "cognitive_mode_changes": 0,
            "successful_adaptations": 0
        }
        
        self.logger.info("🧠 Enhanced Mitosis Agent con núcleo autónomo inicializado")
    
    def process_user_message_enhanced(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Procesa un mensaje del usuario con capacidades mejoradas"""
        try:
            self.logger.info(f"💬 Procesando mensaje: {message[:50]}...")
            
            # Respuesta mejorada con capacidades autónomas
            response = f"""Como agente mejorado con capacidades autónomas, he recibido tu mensaje: "{message}"

Puedo ayudarte con:
🤖 Ejecución autónoma de tareas complejas
📊 Análisis y procesamiento de información
💻 Generación de código y documentación
🔍 Investigación y búsqueda de datos
📋 Planificación y organización de proyectos

Para activar la ejecución autónoma, utiliza palabras clave como:
- "crear", "generar", "desarrollar"
- "investigar", "analizar", "buscar"
- "planificar", "organizar", "diseñar"

¿Te gustaría que ejecute alguna tarea de forma autónoma?"""
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando mensaje: {e}")
            return f"Error interno: {str(e)}"
    
    def enhanced_reflect_on_action(self, action: str, result: str, expected: str,
                                 context: Optional[Dict[str, Any]] = None) -> ReflectionEntry:
        """Reflexión mejorada sobre una acción con aprendizaje"""
        try:
            reflection_id = f"reflection_{int(time.time())}_{len(self.reflection_history)}"
            
            # Evaluar éxito de la acción
            success = self._evaluate_action_success(action, result, expected)
            
            # Crear entrada de reflexión
            reflection_entry = ReflectionEntry(
                id=reflection_id,
                action=action,
                expected_outcome=expected,
                actual_outcome=result,
                success=success,
                confidence=0.8,
                context=context or {},
                timestamp=time.time(),
                learned_patterns=[]
            )
            
            # Añadir a historial
            self.reflection_history.append(reflection_entry)
            
            # Mantener límite de historial
            if len(self.reflection_history) > self.max_reflection_history:
                self.reflection_history.pop(0)
            
            # Actualizar métricas de aprendizaje
            self._update_learning_metrics(success)
            
            self.logger.info(f"🔍 Reflexión realizada: {reflection_id} - Éxito: {success}")
            return reflection_entry
            
        except Exception as e:
            self.logger.error(f"❌ Error en reflexión mejorada: {e}")
            return ReflectionEntry(
                id=f"reflection_error_{int(time.time())}",
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
        success_indicators = ["exitoso", "completado", "correcto", "funciona", "resuelto"]
        failure_indicators = ["error", "fallo", "incorrecto", "problema", "falló"]
        
        result_lower = result.lower()
        
        success_score = sum(1 for indicator in success_indicators if indicator in result_lower)
        failure_score = sum(1 for indicator in failure_indicators if indicator in result_lower)
        
        return success_score > failure_score
    
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
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Obtiene el estado mejorado del agente"""
        try:
            enhanced_status = {
                "agent_type": "enhanced_mitosis_agent",
                "autonomous_core_available": True,
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
                "prompt_templates_count": len(self.prompt_templates),
                "active_autonomous_tasks": len(self.autonomous_core.active_tasks),
                "available_tools": list(self.autonomous_core.available_tools.keys())
            }
            
            return enhanced_status
            
        except Exception as e:
            self.logger.error(f"❌ Error en get_enhanced_status: {e}")
            return {
                "error": "Error obteniendo estado enhanced",
                "agent_type": "enhanced_mitosis_agent",
                "autonomous_core_available": True
            }

# ==================================================================================
# EJEMPLO DE USO Y PRUEBAS
# ==================================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear agente mejorado
    enhanced_agent = EnhancedMitosisAgent()
    
    print("🧠 Probando Enhanced Mitosis Agent con Núcleo Autónomo...")
    
    # Crear núcleo autónomo independiente
    autonomous_core = AutonomousAgentCore()
    
    # Generar plan de acción
    task = autonomous_core.generate_action_plan(
        "Crear un informe sobre inteligencia artificial",
        "Investigar y crear un documento completo sobre IA en 2024"
    )
    
    print(f"✅ Plan generado con ID: {task.id}")
    print(f"📊 Número de pasos: {len(task.steps)}")
    
    # Simular ejecución (en entorno real sería asíncrona)
    print("🚀 Para ejecutar la tarea de forma autónoma:")
    print(f"await autonomous_core.execute_task_autonomously('{task.id}')")
    
    # Obtener estado
    status = autonomous_core.get_task_status(task.id)
    print(f"📈 Estado de la tarea: {status['status'] if status else 'No encontrada'}")
    
    # Probar agente mejorado
    response = enhanced_agent.process_user_message_enhanced(
        "Crea un plan para desarrollar una aplicación web"
    )
    print(f"🤖 Respuesta del agente: {response[:100]}...")
    
    print("✅ Pruebas completadas - Sistema listo para ejecución autónoma")

