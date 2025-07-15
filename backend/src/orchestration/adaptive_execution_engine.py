"""
Motor de ejecución adaptativa para Mitosis
Implementa capacidades avanzadas de ejecución con adaptación dinámica
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json

from .planning_algorithms import ExecutionPlan, TaskStep

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    """Estados de ejecución"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ADAPTING = "adapting"

class AdaptationTrigger(Enum):
    """Triggers para adaptación"""
    ERROR = "error"
    TIMEOUT = "timeout"
    RESOURCE_CONSTRAINT = "resource_constraint"
    UNEXPECTED_RESULT = "unexpected_result"
    PERFORMANCE_ISSUE = "performance_issue"
    CONTEXT_CHANGE = "context_change"

@dataclass
class ExecutionContext:
    """Contexto de ejecución"""
    task_id: str
    session_id: str
    user_id: str
    environment: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    """Resultado de ejecución"""
    step_id: str
    status: ExecutionStatus
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    resources_used: Dict[str, Any] = field(default_factory=dict)
    adaptations_made: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AdaptationEvent:
    """Evento de adaptación"""
    trigger: AdaptationTrigger
    step_id: str
    original_plan: TaskStep
    adapted_plan: TaskStep
    reason: str
    timestamp: float
    success: bool = False

class ExecutionMonitor:
    """Monitor de ejecución para detectar problemas"""
    
    def __init__(self):
        self.metrics = {
            "steps_executed": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "adaptations_made": 0,
            "avg_execution_time": 0.0,
            "resource_usage": {}
        }
        
        self.active_executions = {}
        self.adaptation_history = []
    
    def start_monitoring(self, step_id: str, step: TaskStep):
        """Inicia monitoreo de un paso"""
        
        self.active_executions[step_id] = {
            "step": step,
            "start_time": time.time(),
            "timeout": step.estimated_duration * 2,  # Timeout 2x duración estimada
            "resource_baseline": self._get_resource_baseline()
        }
        
        logger.info(f"Iniciando monitoreo para paso: {step_id}")
    
    def update_progress(self, step_id: str, progress: float, metrics: Dict[str, Any]):
        """Actualiza progreso del paso"""
        
        if step_id in self.active_executions:
            execution = self.active_executions[step_id]
            execution["progress"] = progress
            execution["metrics"] = metrics
            
            # Detectar problemas
            issues = self._detect_issues(step_id, execution)
            if issues:
                logger.warning(f"Problemas detectados en {step_id}: {issues}")
                return issues
        
        return []
    
    def stop_monitoring(self, step_id: str, result: ExecutionResult):
        """Detiene monitoreo de un paso"""
        
        if step_id in self.active_executions:
            execution = self.active_executions[step_id]
            execution_time = time.time() - execution["start_time"]
            
            # Actualizar métricas
            self.metrics["steps_executed"] += 1
            if result.status == ExecutionStatus.COMPLETED:
                self.metrics["successful_steps"] += 1
            else:
                self.metrics["failed_steps"] += 1
            
            # Actualizar tiempo promedio
            current_avg = self.metrics["avg_execution_time"]
            new_avg = (current_avg * 0.8) + (execution_time * 0.2)
            self.metrics["avg_execution_time"] = new_avg
            
            del self.active_executions[step_id]
            
            logger.info(f"Monitoreo terminado para paso: {step_id}, tiempo: {execution_time:.2f}s")
    
    def _detect_issues(self, step_id: str, execution: Dict[str, Any]) -> List[AdaptationTrigger]:
        """Detecta problemas en la ejecución"""
        
        issues = []
        current_time = time.time()
        
        # Detectar timeout
        if current_time - execution["start_time"] > execution["timeout"]:
            issues.append(AdaptationTrigger.TIMEOUT)
        
        # Detectar uso excesivo de recursos
        current_resources = self._get_current_resources()
        baseline = execution["resource_baseline"]
        
        if current_resources.get("memory", 0) > baseline.get("memory", 0) * 2:
            issues.append(AdaptationTrigger.RESOURCE_CONSTRAINT)
        
        # Detectar problemas de rendimiento
        progress = execution.get("progress", 0)
        expected_progress = (current_time - execution["start_time"]) / execution["timeout"]
        
        if progress < expected_progress * 0.5:  # 50% del progreso esperado
            issues.append(AdaptationTrigger.PERFORMANCE_ISSUE)
        
        return issues
    
    def _get_resource_baseline(self) -> Dict[str, Any]:
        """Obtiene baseline de recursos"""
        
        import psutil
        
        return {
            "memory": psutil.virtual_memory().used,
            "cpu": psutil.cpu_percent(),
            "disk": psutil.disk_usage('/').used
        }
    
    def _get_current_resources(self) -> Dict[str, Any]:
        """Obtiene recursos actuales"""
        
        import psutil
        
        return {
            "memory": psutil.virtual_memory().used,
            "cpu": psutil.cpu_percent(),
            "disk": psutil.disk_usage('/').used
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de monitoreo"""
        
        return self.metrics.copy()

class ErrorRecoverySystem:
    """Sistema de recuperación de errores"""
    
    def __init__(self):
        self.recovery_strategies = {
            "timeout": self._handle_timeout,
            "resource_constraint": self._handle_resource_constraint,
            "tool_error": self._handle_tool_error,
            "network_error": self._handle_network_error,
            "permission_error": self._handle_permission_error
        }
        
        self.recovery_history = []
    
    async def recover_from_error(self, step: TaskStep, error: Exception, 
                               context: ExecutionContext) -> Optional[TaskStep]:
        """Intenta recuperarse de un error"""
        
        error_type = self._classify_error(error)
        logger.info(f"Intentando recuperación para error tipo: {error_type}")
        
        if error_type in self.recovery_strategies:
            recovery_strategy = self.recovery_strategies[error_type]
            adapted_step = await recovery_strategy(step, error, context)
            
            if adapted_step:
                self.recovery_history.append({
                    "step_id": step.id,
                    "error_type": error_type,
                    "error_message": str(error),
                    "recovery_applied": True,
                    "timestamp": time.time()
                })
                
                logger.info(f"Recuperación exitosa para paso: {step.id}")
                return adapted_step
        
        # Recuperación fallida
        self.recovery_history.append({
            "step_id": step.id,
            "error_type": error_type,
            "error_message": str(error),
            "recovery_applied": False,
            "timestamp": time.time()
        })
        
        logger.error(f"No se pudo recuperar del error en paso: {step.id}")
        return None
    
    def _classify_error(self, error: Exception) -> str:
        """Clasifica el tipo de error"""
        
        error_str = str(error).lower()
        
        if "timeout" in error_str or "time" in error_str:
            return "timeout"
        elif "memory" in error_str or "resource" in error_str:
            return "resource_constraint"
        elif "permission" in error_str or "access" in error_str:
            return "permission_error"
        elif "network" in error_str or "connection" in error_str:
            return "network_error"
        elif "tool" in error_str or "command" in error_str:
            return "tool_error"
        else:
            return "unknown"
    
    async def _handle_timeout(self, step: TaskStep, error: Exception, 
                            context: ExecutionContext) -> Optional[TaskStep]:
        """Maneja errores de timeout"""
        
        # Estrategia: Incrementar timeout y reducir alcance
        adapted_step = TaskStep(
            id=f"{step.id}_timeout_recovery",
            title=f"{step.title} (Timeout Recovery)",
            description=f"Versión adaptada con timeout extendido: {step.description}",
            tool=step.tool,
            parameters=step.parameters.copy(),
            dependencies=step.dependencies.copy(),
            estimated_duration=step.estimated_duration * 2,
            complexity=step.complexity * 0.8,  # Reducir complejidad
            priority=step.priority,
            can_parallelize=step.can_parallelize
        )
        
        # Ajustar parámetros para reducir alcance
        if "max_results" in adapted_step.parameters:
            adapted_step.parameters["max_results"] = min(
                adapted_step.parameters["max_results"] // 2, 5
            )
        
        return adapted_step
    
    async def _handle_resource_constraint(self, step: TaskStep, error: Exception,
                                        context: ExecutionContext) -> Optional[TaskStep]:
        """Maneja restricciones de recursos"""
        
        # Estrategia: Reducir uso de recursos
        adapted_step = TaskStep(
            id=f"{step.id}_resource_recovery",
            title=f"{step.title} (Resource Recovery)",
            description=f"Versión optimizada para recursos: {step.description}",
            tool=step.tool,
            parameters=step.parameters.copy(),
            dependencies=step.dependencies.copy(),
            estimated_duration=step.estimated_duration * 1.5,
            complexity=step.complexity * 0.6,
            priority=step.priority,
            can_parallelize=False  # Deshabilitar paralelismo
        )
        
        # Reducir batch size si está disponible
        if "batch_size" in adapted_step.parameters:
            adapted_step.parameters["batch_size"] = max(
                adapted_step.parameters["batch_size"] // 2, 1
            )
        
        return adapted_step
    
    async def _handle_tool_error(self, step: TaskStep, error: Exception,
                               context: ExecutionContext) -> Optional[TaskStep]:
        """Maneja errores de herramientas"""
        
        # Estrategia: Cambiar a herramienta alternativa
        alternative_tools = {
            "web_search": "deep_research",
            "deep_research": "comprehensive_research",
            "comprehensive_research": "web_search",
            "shell": "file_manager",
            "file_manager": "shell"
        }
        
        alternative_tool = alternative_tools.get(step.tool)
        if not alternative_tool:
            return None
        
        adapted_step = TaskStep(
            id=f"{step.id}_tool_recovery",
            title=f"{step.title} (Tool Recovery)",
            description=f"Usando herramienta alternativa: {step.description}",
            tool=alternative_tool,
            parameters=self._adapt_parameters_for_tool(step.parameters, alternative_tool),
            dependencies=step.dependencies.copy(),
            estimated_duration=step.estimated_duration * 1.2,
            complexity=step.complexity * 1.1,
            priority=step.priority,
            can_parallelize=step.can_parallelize
        )
        
        return adapted_step
    
    async def _handle_network_error(self, step: TaskStep, error: Exception,
                                  context: ExecutionContext) -> Optional[TaskStep]:
        """Maneja errores de red"""
        
        # Estrategia: Retry con backoff exponencial
        adapted_step = TaskStep(
            id=f"{step.id}_network_recovery",
            title=f"{step.title} (Network Recovery)",
            description=f"Reintento con backoff: {step.description}",
            tool=step.tool,
            parameters=step.parameters.copy(),
            dependencies=step.dependencies.copy(),
            estimated_duration=step.estimated_duration * 1.5,
            complexity=step.complexity,
            priority=step.priority,
            can_parallelize=step.can_parallelize
        )
        
        # Agregar configuración de retry
        adapted_step.parameters["retry_count"] = adapted_step.parameters.get("retry_count", 0) + 1
        adapted_step.parameters["retry_delay"] = min(
            adapted_step.parameters.get("retry_delay", 1) * 2, 30
        )
        
        return adapted_step
    
    async def _handle_permission_error(self, step: TaskStep, error: Exception,
                                     context: ExecutionContext) -> Optional[TaskStep]:
        """Maneja errores de permisos"""
        
        # Estrategia: Cambiar a operación de solo lectura
        adapted_step = TaskStep(
            id=f"{step.id}_permission_recovery",
            title=f"{step.title} (Permission Recovery)",
            description=f"Versión de solo lectura: {step.description}",
            tool=step.tool,
            parameters=step.parameters.copy(),
            dependencies=step.dependencies.copy(),
            estimated_duration=step.estimated_duration * 0.8,
            complexity=step.complexity * 0.7,
            priority=step.priority,
            can_parallelize=step.can_parallelize
        )
        
        # Cambiar a operaciones de solo lectura
        adapted_step.parameters["read_only"] = True
        if "action" in adapted_step.parameters:
            adapted_step.parameters["action"] = "read"
        
        return adapted_step
    
    def _adapt_parameters_for_tool(self, parameters: Dict[str, Any], new_tool: str) -> Dict[str, Any]:
        """Adapta parámetros para nueva herramienta"""
        
        adapted = parameters.copy()
        
        # Mapeos de parámetros entre herramientas
        if new_tool == "deep_research" and "query" in adapted:
            adapted["research_query"] = adapted.pop("query")
        elif new_tool == "web_search" and "research_query" in adapted:
            adapted["query"] = adapted.pop("research_query")
        
        return adapted

class AdaptationEngine:
    """Motor de adaptación para ajustar planes durante ejecución"""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self.adaptation_strategies = {
            AdaptationTrigger.ERROR: self._adapt_for_error,
            AdaptationTrigger.TIMEOUT: self._adapt_for_timeout,
            AdaptationTrigger.RESOURCE_CONSTRAINT: self._adapt_for_resources,
            AdaptationTrigger.UNEXPECTED_RESULT: self._adapt_for_unexpected_result,
            AdaptationTrigger.PERFORMANCE_ISSUE: self._adapt_for_performance,
            AdaptationTrigger.CONTEXT_CHANGE: self._adapt_for_context_change
        }
        
        self.adaptation_history = []
    
    async def adapt_step(self, step: TaskStep, trigger: AdaptationTrigger,
                        context: ExecutionContext, 
                        additional_info: Dict[str, Any] = None) -> Optional[TaskStep]:
        """Adapta un paso basado en el trigger"""
        
        logger.info(f"Adaptando paso {step.id} por trigger: {trigger}")
        
        if trigger in self.adaptation_strategies:
            strategy = self.adaptation_strategies[trigger]
            adapted_step = await strategy(step, context, additional_info or {})
            
            if adapted_step:
                adaptation_event = AdaptationEvent(
                    trigger=trigger,
                    step_id=step.id,
                    original_plan=step,
                    adapted_plan=adapted_step,
                    reason=additional_info.get("reason", f"Adaptación por {trigger.value}"),
                    timestamp=time.time(),
                    success=True
                )
                
                self.adaptation_history.append(adaptation_event)
                logger.info(f"Adaptación exitosa para paso: {step.id}")
                return adapted_step
        
        logger.warning(f"No se pudo adaptar paso {step.id} para trigger: {trigger}")
        return None
    
    async def _adapt_for_error(self, step: TaskStep, context: ExecutionContext,
                             info: Dict[str, Any]) -> Optional[TaskStep]:
        """Adapta paso para errores"""
        
        error_type = info.get("error_type", "unknown")
        
        # Usar LLM para adaptación si está disponible
        if self.llm_service:
            return await self._llm_based_adaptation(step, f"error: {error_type}", context)
        
        # Adaptación básica: reducir complejidad
        return TaskStep(
            id=f"{step.id}_error_adapted",
            title=f"{step.title} (Error Adapted)",
            description=f"Versión simplificada: {step.description}",
            tool=step.tool,
            parameters=step.parameters.copy(),
            dependencies=step.dependencies.copy(),
            estimated_duration=step.estimated_duration * 1.5,
            complexity=max(step.complexity * 0.7, 0.1),
            priority=step.priority,
            can_parallelize=False
        )
    
    async def _adapt_for_timeout(self, step: TaskStep, context: ExecutionContext,
                               info: Dict[str, Any]) -> Optional[TaskStep]:
        """Adapta paso para timeouts"""
        
        return TaskStep(
            id=f"{step.id}_timeout_adapted",
            title=f"{step.title} (Timeout Adapted)",
            description=f"Versión con timeout extendido: {step.description}",
            tool=step.tool,
            parameters=step.parameters.copy(),
            dependencies=step.dependencies.copy(),
            estimated_duration=step.estimated_duration * 2,
            complexity=step.complexity * 0.8,
            priority=step.priority,
            can_parallelize=step.can_parallelize
        )
    
    async def _adapt_for_resources(self, step: TaskStep, context: ExecutionContext,
                                 info: Dict[str, Any]) -> Optional[TaskStep]:
        """Adapta paso para restricciones de recursos"""
        
        resource_type = info.get("resource_type", "memory")
        
        adapted_params = step.parameters.copy()
        
        # Reducir uso de recursos basado en tipo
        if resource_type == "memory":
            if "batch_size" in adapted_params:
                adapted_params["batch_size"] = max(adapted_params["batch_size"] // 2, 1)
            if "max_results" in adapted_params:
                adapted_params["max_results"] = min(adapted_params["max_results"], 5)
        
        return TaskStep(
            id=f"{step.id}_resource_adapted",
            title=f"{step.title} (Resource Adapted)",
            description=f"Versión optimizada para recursos: {step.description}",
            tool=step.tool,
            parameters=adapted_params,
            dependencies=step.dependencies.copy(),
            estimated_duration=step.estimated_duration * 1.3,
            complexity=step.complexity * 0.6,
            priority=step.priority,
            can_parallelize=False
        )
    
    async def _adapt_for_unexpected_result(self, step: TaskStep, context: ExecutionContext,
                                         info: Dict[str, Any]) -> Optional[TaskStep]:
        """Adapta paso para resultados inesperados"""
        
        result_type = info.get("result_type", "empty")
        
        if result_type == "empty":
            # Cambiar enfoque si no hay resultados
            adapted_params = step.parameters.copy()
            if "query" in adapted_params:
                adapted_params["query"] = f"alternative search for {adapted_params['query']}"
            
            return TaskStep(
                id=f"{step.id}_result_adapted",
                title=f"{step.title} (Result Adapted)",
                description=f"Enfoque alternativo: {step.description}",
                tool=step.tool,
                parameters=adapted_params,
                dependencies=step.dependencies.copy(),
                estimated_duration=step.estimated_duration,
                complexity=step.complexity * 1.1,
                priority=step.priority,
                can_parallelize=step.can_parallelize
            )
        
        return None
    
    async def _adapt_for_performance(self, step: TaskStep, context: ExecutionContext,
                                   info: Dict[str, Any]) -> Optional[TaskStep]:
        """Adapta paso para problemas de rendimiento"""
        
        performance_issue = info.get("issue", "slow")
        
        if performance_issue == "slow":
            # Simplificar operación
            adapted_params = step.parameters.copy()
            if "max_results" in adapted_params:
                adapted_params["max_results"] = min(adapted_params["max_results"], 3)
            
            return TaskStep(
                id=f"{step.id}_performance_adapted",
                title=f"{step.title} (Performance Adapted)",
                description=f"Versión optimizada: {step.description}",
                tool=step.tool,
                parameters=adapted_params,
                dependencies=step.dependencies.copy(),
                estimated_duration=step.estimated_duration * 0.7,
                complexity=step.complexity * 0.5,
                priority=step.priority,
                can_parallelize=step.can_parallelize
            )
        
        return None
    
    async def _adapt_for_context_change(self, step: TaskStep, context: ExecutionContext,
                                      info: Dict[str, Any]) -> Optional[TaskStep]:
        """Adapta paso para cambios de contexto"""
        
        context_change = info.get("change_type", "unknown")
        
        # Usar LLM para adaptación contextual si está disponible
        if self.llm_service:
            return await self._llm_based_adaptation(step, f"context change: {context_change}", context)
        
        # Adaptación básica: mantener funcionalidad core
        return TaskStep(
            id=f"{step.id}_context_adapted",
            title=f"{step.title} (Context Adapted)",
            description=f"Adaptado al contexto: {step.description}",
            tool=step.tool,
            parameters=step.parameters.copy(),
            dependencies=step.dependencies.copy(),
            estimated_duration=step.estimated_duration * 1.1,
            complexity=step.complexity,
            priority=step.priority,
            can_parallelize=step.can_parallelize
        )
    
    async def _llm_based_adaptation(self, step: TaskStep, reason: str, 
                                  context: ExecutionContext) -> Optional[TaskStep]:
        """Adaptación basada en LLM"""
        
        if not self.llm_service:
            return None
        
        prompt = f"""
        Adapta el siguiente paso de ejecución debido a: {reason}
        
        Paso original:
        - ID: {step.id}
        - Título: {step.title}
        - Descripción: {step.description}
        - Herramienta: {step.tool}
        - Parámetros: {json.dumps(step.parameters, indent=2)}
        - Duración estimada: {step.estimated_duration}s
        - Complejidad: {step.complexity}
        
        Contexto de ejecución:
        - Variables: {json.dumps(context.variables, indent=2)}
        - Restricciones: {json.dumps(context.constraints, indent=2)}
        
        Genera una adaptación que:
        1. Mantenga el objetivo principal
        2. Ajuste los parámetros apropiadamente
        3. Considere las restricciones
        4. Proporcione una solución viable
        
        Responde en formato JSON:
        {{
            "title": "título adaptado",
            "description": "descripción adaptada",
            "tool": "herramienta (mantener la misma si es posible)",
            "parameters": {{"param": "valor"}},
            "estimated_duration": número_en_segundos,
            "complexity": número_entre_0_y_1,
            "reasoning": "explicación de los cambios"
        }}
        """
        
        try:
            response = await self.llm_service.generate_response(prompt)
            adaptation_data = json.loads(response.get('response', '{}'))
            
            return TaskStep(
                id=f"{step.id}_llm_adapted",
                title=adaptation_data.get('title', step.title),
                description=adaptation_data.get('description', step.description),
                tool=adaptation_data.get('tool', step.tool),
                parameters=adaptation_data.get('parameters', step.parameters),
                dependencies=step.dependencies.copy(),
                estimated_duration=adaptation_data.get('estimated_duration', step.estimated_duration),
                complexity=adaptation_data.get('complexity', step.complexity),
                priority=step.priority,
                can_parallelize=step.can_parallelize
            )
            
        except Exception as e:
            logger.error(f"Error en adaptación LLM: {e}")
            return None

class AdaptiveExecutionEngine:
    """Motor de ejecución adaptativa principal"""
    
    def __init__(self, tool_manager=None, memory_manager=None, llm_service=None):
        self.tool_manager = tool_manager
        self.memory_manager = memory_manager
        self.llm_service = llm_service
        
        # Componentes especializados
        self.execution_monitor = ExecutionMonitor()
        self.error_recovery = ErrorRecoverySystem()
        self.adaptation_engine = AdaptationEngine(llm_service)
        
        # Estado de ejecución
        self.active_executions = {}
        self.execution_history = []
        
        # Configuración
        self.config = {
            "enable_monitoring": True,
            "enable_adaptation": True,
            "enable_error_recovery": True,
            "max_adaptation_attempts": 3,
            "parallel_execution": True,
            "resource_monitoring": True
        }
        
        # Callbacks
        self.progress_callback = None
        self.completion_callback = None
        self.error_callback = None
        self.adaptation_callback = None
    
    async def execute_plan(self, plan: ExecutionPlan, context: ExecutionContext,
                          progress_callback: Optional[Callable] = None,
                          completion_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Ejecuta un plan de forma adaptativa"""
        
        logger.info(f"Iniciando ejecución adaptativa del plan: {plan.id}")
        
        # Configurar callbacks
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        
        # Inicializar estado de ejecución
        execution_state = {
            "plan_id": plan.id,
            "context": context,
            "start_time": time.time(),
            "steps_completed": 0,
            "steps_failed": 0,
            "adaptations_made": 0,
            "results": {},
            "errors": []
        }
        
        try:
            # Ejecutar pasos del plan
            for step in plan.steps:
                logger.info(f"Ejecutando paso: {step.id}")
                
                # Verificar dependencias
                if not await self._check_dependencies(step, execution_state):
                    logger.warning(f"Dependencias no satisfechas para paso: {step.id}")
                    continue
                
                # Ejecutar paso con monitoreo y adaptación
                result = await self._execute_step_with_adaptation(step, context, execution_state)
                
                # Procesar resultado
                execution_state["results"][step.id] = result
                
                if result.status == ExecutionStatus.COMPLETED:
                    execution_state["steps_completed"] += 1
                    logger.info(f"Paso completado exitosamente: {step.id}")
                else:
                    execution_state["steps_failed"] += 1
                    logger.error(f"Paso falló: {step.id}, error: {result.error}")
                
                # Notificar progreso
                if self.progress_callback:
                    await self.progress_callback(step.id, result, execution_state)
                
                # Verificar si continuar
                if not await self._should_continue_execution(execution_state):
                    logger.info("Deteniendo ejecución por criterios de parada")
                    break
            
            # Finalizar ejecución
            execution_summary = await self._finalize_execution(plan, execution_state)
            
            # Notificar finalización
            if self.completion_callback:
                await self.completion_callback(execution_summary)
            
            return execution_summary
            
        except Exception as e:
            logger.error(f"Error en ejecución adaptativa: {e}")
            execution_state["errors"].append(str(e))
            
            return {
                "success": False,
                "error": str(e),
                "execution_state": execution_state
            }
    
    async def _execute_step_with_adaptation(self, step: TaskStep, context: ExecutionContext,
                                          execution_state: Dict[str, Any]) -> ExecutionResult:
        """Ejecuta un paso con capacidades de adaptación"""
        
        current_step = step
        adaptation_attempts = 0
        
        while adaptation_attempts < self.config["max_adaptation_attempts"]:
            try:
                # Iniciar monitoreo
                if self.config["enable_monitoring"]:
                    self.execution_monitor.start_monitoring(current_step.id, current_step)
                
                # Ejecutar paso
                result = await self._execute_single_step(current_step, context)
                
                # Detener monitoreo
                if self.config["enable_monitoring"]:
                    self.execution_monitor.stop_monitoring(current_step.id, result)
                
                # Si el paso fue exitoso, retornar resultado
                if result.status == ExecutionStatus.COMPLETED:
                    return result
                
                # Si falló, intentar adaptación
                if self.config["enable_adaptation"] and result.error:
                    adapted_step = await self._attempt_adaptation(
                        current_step, result.error, context, execution_state
                    )
                    
                    if adapted_step:
                        current_step = adapted_step
                        adaptation_attempts += 1
                        execution_state["adaptations_made"] += 1
                        
                        logger.info(f"Adaptación {adaptation_attempts} aplicada para paso: {step.id}")
                        continue
                
                # Si no se pudo adaptar, retornar el resultado fallido
                return result
                
            except Exception as e:
                logger.error(f"Error ejecutando paso {current_step.id}: {e}")
                
                # Intentar recuperación de errores
                if self.config["enable_error_recovery"]:
                    recovered_step = await self.error_recovery.recover_from_error(
                        current_step, e, context
                    )
                    
                    if recovered_step:
                        current_step = recovered_step
                        adaptation_attempts += 1
                        execution_state["adaptations_made"] += 1
                        
                        logger.info(f"Recuperación de error aplicada para paso: {step.id}")
                        continue
                
                # Error irrecuperable
                return ExecutionResult(
                    step_id=current_step.id,
                    status=ExecutionStatus.FAILED,
                    error=str(e),
                    execution_time=0.0
                )
        
        # Se agotaron los intentos de adaptación
        logger.error(f"Se agotaron los intentos de adaptación para paso: {step.id}")
        return ExecutionResult(
            step_id=current_step.id,
            status=ExecutionStatus.FAILED,
            error="Maximum adaptation attempts exceeded",
            execution_time=0.0
        )
    
    async def _execute_single_step(self, step: TaskStep, context: ExecutionContext) -> ExecutionResult:
        """Ejecuta un solo paso sin adaptación"""
        
        start_time = time.time()
        
        try:
            if not self.tool_manager:
                raise Exception("Tool manager not available")
            
            # Preparar parámetros de ejecución
            execution_params = step.parameters.copy()
            execution_params.update({
                "context": context.variables,
                "task_id": context.task_id,
                "step_id": step.id
            })
            
            # Ejecutar herramienta
            result = self.tool_manager.execute_tool(
                step.tool, 
                execution_params,
                task_id=context.task_id
            )
            
            execution_time = time.time() - start_time
            
            # Verificar resultado
            if result.get("error"):
                return ExecutionResult(
                    step_id=step.id,
                    status=ExecutionStatus.FAILED,
                    error=result["error"],
                    execution_time=execution_time
                )
            
            return ExecutionResult(
                step_id=step.id,
                status=ExecutionStatus.COMPLETED,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                step_id=step.id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _attempt_adaptation(self, step: TaskStep, error: str, context: ExecutionContext,
                                execution_state: Dict[str, Any]) -> Optional[TaskStep]:
        """Intenta adaptar un paso fallido"""
        
        # Determinar trigger de adaptación
        trigger = self._determine_adaptation_trigger(error)
        
        # Aplicar adaptación
        adapted_step = await self.adaptation_engine.adapt_step(
            step, trigger, context, {"error": error}
        )
        
        if adapted_step and self.adaptation_callback:
            await self.adaptation_callback(step, adapted_step, trigger)
        
        return adapted_step
    
    def _determine_adaptation_trigger(self, error: str) -> AdaptationTrigger:
        """Determina el trigger de adaptación basado en el error"""
        
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            return AdaptationTrigger.TIMEOUT
        elif "resource" in error_lower or "memory" in error_lower:
            return AdaptationTrigger.RESOURCE_CONSTRAINT
        elif "unexpected" in error_lower or "empty" in error_lower:
            return AdaptationTrigger.UNEXPECTED_RESULT
        elif "performance" in error_lower or "slow" in error_lower:
            return AdaptationTrigger.PERFORMANCE_ISSUE
        else:
            return AdaptationTrigger.ERROR
    
    async def _check_dependencies(self, step: TaskStep, execution_state: Dict[str, Any]) -> bool:
        """Verifica que las dependencias del paso estén satisfechas"""
        
        for dep_id in step.dependencies:
            if dep_id not in execution_state["results"]:
                return False
            
            dep_result = execution_state["results"][dep_id]
            if dep_result.status != ExecutionStatus.COMPLETED:
                return False
        
        return True
    
    async def _should_continue_execution(self, execution_state: Dict[str, Any]) -> bool:
        """Determina si continuar con la ejecución"""
        
        # Verificar criterios de parada
        total_steps = execution_state["steps_completed"] + execution_state["steps_failed"]
        
        if total_steps > 0:
            failure_rate = execution_state["steps_failed"] / total_steps
            
            # Detener si hay muchos fallos
            if failure_rate > 0.5:
                logger.warning(f"Deteniendo ejecución por alta tasa de fallos: {failure_rate}")
                return False
        
        # Verificar si hay muchas adaptaciones
        if execution_state["adaptations_made"] > 10:
            logger.warning("Deteniendo ejecución por excesivas adaptaciones")
            return False
        
        return True
    
    async def _finalize_execution(self, plan: ExecutionPlan, execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """Finaliza la ejecución y genera resumen"""
        
        execution_time = time.time() - execution_state["start_time"]
        
        # Calcular métricas
        total_steps = execution_state["steps_completed"] + execution_state["steps_failed"]
        success_rate = execution_state["steps_completed"] / total_steps if total_steps > 0 else 0
        
        # Generar resumen
        summary = {
            "success": success_rate > 0.5,
            "plan_id": plan.id,
            "execution_time": execution_time,
            "total_steps": total_steps,
            "steps_completed": execution_state["steps_completed"],
            "steps_failed": execution_state["steps_failed"],
            "success_rate": success_rate,
            "adaptations_made": execution_state["adaptations_made"],
            "results": execution_state["results"],
            "errors": execution_state["errors"],
            "metrics": {
                "avg_step_time": execution_time / total_steps if total_steps > 0 else 0,
                "adaptation_rate": execution_state["adaptations_made"] / total_steps if total_steps > 0 else 0
            }
        }
        
        # Guardar en historial
        self.execution_history.append(summary)
        
        logger.info(f"Ejecución finalizada - Éxito: {summary['success']}, "
                   f"Pasos completados: {summary['steps_completed']}/{summary['total_steps']}")
        
        return summary
    
    def set_callbacks(self, progress_callback: Optional[Callable] = None,
                     completion_callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None,
                     adaptation_callback: Optional[Callable] = None):
        """Configura callbacks para eventos de ejecución"""
        
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
        self.adaptation_callback = adaptation_callback
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de ejecución"""
        
        if not self.execution_history:
            return {"no_executions": True}
        
        # Calcular métricas agregadas
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for ex in self.execution_history if ex["success"])
        
        avg_execution_time = sum(ex["execution_time"] for ex in self.execution_history) / total_executions
        avg_success_rate = sum(ex["success_rate"] for ex in self.execution_history) / total_executions
        total_adaptations = sum(ex["adaptations_made"] for ex in self.execution_history)
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "execution_success_rate": successful_executions / total_executions,
            "avg_execution_time": avg_execution_time,
            "avg_step_success_rate": avg_success_rate,
            "total_adaptations": total_adaptations,
            "adaptations_per_execution": total_adaptations / total_executions,
            "monitor_metrics": self.execution_monitor.get_metrics()
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Actualiza configuración del motor"""
        
        self.config.update(new_config)
        logger.info(f"Configuración actualizada: {new_config}")
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene configuración actual"""
        
        return self.config.copy()