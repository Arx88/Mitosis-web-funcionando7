"""
Orquestador de tareas principal para Mitosis
Coordina la planificación jerárquica, ejecución adaptativa y gestión de recursos
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
import time
import json
import uuid

from .hierarchical_planning_engine import HierarchicalPlanningEngine, PlanningContext
from .adaptive_execution_engine import AdaptiveExecutionEngine, ExecutionContext, ExecutionResult
from .dependency_resolver import DependencyResolver
from .resource_manager import ResourceManager, ResourceRequest, ResourceType
from .planning_algorithms import ExecutionPlan, TaskStep, PlanningStrategy

logger = logging.getLogger(__name__)

@dataclass
class OrchestrationContext:
    """Contexto completo de orquestación"""
    task_id: str
    user_id: str
    session_id: str
    task_description: str
    priority: int = 1
    timeout: Optional[float] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OrchestrationResult:
    """Resultado de orquestación"""
    task_id: str
    success: bool
    execution_plan: Optional[ExecutionPlan] = None
    execution_results: Dict[str, ExecutionResult] = field(default_factory=dict)
    total_execution_time: float = 0.0
    steps_completed: int = 0
    steps_failed: int = 0
    adaptations_made: int = 0
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TaskOrchestrator:
    """Orquestador principal de tareas"""
    
    def __init__(self, tool_manager=None, memory_manager=None, llm_service=None):
        self.tool_manager = tool_manager
        self.memory_manager = memory_manager
        self.llm_service = llm_service
        
        # Componentes especializados
        self.planning_engine = HierarchicalPlanningEngine(
            llm_service=llm_service,
            tool_manager=tool_manager,
            memory_manager=memory_manager
        )
        
        self.execution_engine = AdaptiveExecutionEngine(
            tool_manager=tool_manager,
            memory_manager=memory_manager,
            llm_service=llm_service
        )
        
        self.dependency_resolver = DependencyResolver()
        self.resource_manager = ResourceManager()
        
        # Estado de orquestación
        self.active_orchestrations = {}
        self.orchestration_history = []
        
        # Configuración
        self.config = {
            "max_concurrent_tasks": 5,
            "enable_resource_management": True,
            "enable_dependency_optimization": True,
            "enable_adaptive_execution": True,
            "enable_progress_tracking": True,
            "default_timeout": 1800,  # 30 minutos
            "retry_failed_steps": True,
            "max_retries": 3
        }
        
        # Callbacks
        self.orchestration_callbacks = {
            "on_start": [],
            "on_progress": [],
            "on_step_complete": [],
            "on_adaptation": [],
            "on_error": [],
            "on_complete": []
        }
        
        # Métricas
        self.orchestration_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_execution_time": 0.0,
            "total_steps_executed": 0,
            "total_adaptations": 0,
            "resource_efficiency": 0.0
        }
    
    async def orchestrate_task(self, context: OrchestrationContext) -> OrchestrationResult:
        """Orquesta la ejecución completa de una tarea"""
        
        logger.info(f"Iniciando orquestación de tarea: {context.task_id}")
        
        start_time = time.time()
        self.orchestration_metrics["total_tasks"] += 1
        
        try:
            # 1. Validar contexto
            if not self._validate_context(context):
                raise ValueError("Contexto de orquestación inválido")
            
            # 2. Verificar límites de concurrencia
            if not self._check_concurrency_limits():
                raise RuntimeError("Límite de concurrencia alcanzado")
            
            # 3. Registrar orquestación activa
            self.active_orchestrations[context.task_id] = {
                "context": context,
                "start_time": start_time,
                "status": "starting"
            }
            
            # 4. Notificar inicio
            await self._notify_callbacks("on_start", context)
            
            # 5. Crear plan de ejecución
            logger.info(f"Creando plan de ejecución para tarea: {context.task_id}")
            execution_plan = await self._create_execution_plan(context)
            
            # 6. Optimizar dependencias
            if self.config["enable_dependency_optimization"]:
                execution_plan = await self._optimize_dependencies(execution_plan)
            
            # 7. Asignar recursos
            if self.config["enable_resource_management"]:
                await self._allocate_resources(execution_plan, context)
            
            # 8. Ejecutar plan
            logger.info(f"Ejecutando plan para tarea: {context.task_id}")
            execution_results = await self._execute_plan(execution_plan, context)
            
            # 9. Liberar recursos
            if self.config["enable_resource_management"]:
                await self._release_resources(context.task_id)
            
            # 10. Generar resultado
            result = self._generate_result(context, execution_plan, execution_results, start_time)
            
            # 11. Actualizar métricas
            self._update_metrics(result)
            
            # 12. Notificar finalización
            await self._notify_callbacks("on_complete", result)
            
            # 13. Limpiar estado
            self._cleanup_orchestration(context.task_id)
            
            logger.info(f"Orquestación completada para tarea: {context.task_id}, "
                       f"éxito: {result.success}, tiempo: {result.total_execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en orquestación de tarea {context.task_id}: {e}")
            
            # Crear resultado de error
            error_result = OrchestrationResult(
                task_id=context.task_id,
                success=False,
                error_message=str(e),
                total_execution_time=time.time() - start_time
            )
            
            # Notificar error
            await self._notify_callbacks("on_error", error_result)
            
            # Limpiar estado
            self._cleanup_orchestration(context.task_id)
            
            self.orchestration_metrics["failed_tasks"] += 1
            
            return error_result
    
    async def _create_execution_plan(self, context: OrchestrationContext) -> ExecutionPlan:
        """Crea un plan de ejecución usando el motor de planificación"""
        
        # Crear contexto de planificación
        planning_context = PlanningContext(
            user_id=context.user_id,
            session_id=context.session_id,
            task_history=await self._get_task_history(context.user_id),
            available_resources=self.resource_manager.get_resource_status(),
            constraints=context.constraints,
            preferences=context.preferences
        )
        
        # Obtener herramientas disponibles
        available_tools = []
        if self.tool_manager:
            tools = self.tool_manager.get_available_tools()
            available_tools = [tool.get("name", "") for tool in tools]
        
        # Crear plan
        plan = await self.planning_engine.create_plan(
            context.task_description,
            planning_context,
            available_tools
        )
        
        return plan
    
    async def _optimize_dependencies(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Optimiza las dependencias del plan"""
        
        logger.info("Optimizando dependencias del plan")
        
        # Analizar dependencias
        dependencies = self.dependency_resolver.analyze_dependencies(plan.steps)
        
        # Validar dependencias
        issues = self.dependency_resolver.validate_dependencies(plan.steps)
        
        if issues:
            logger.warning(f"Problemas de dependencias detectados: {issues}")
            # Intentar resolver problemas
            plan = await self._resolve_dependency_issues(plan, issues)
        
        # Optimizar para ejecución paralela
        optimized_order = self.dependency_resolver.optimize_parallel_execution(plan.steps)
        
        # Actualizar metadatos del plan
        plan.metadata.update({
            "dependency_analysis": dependencies,
            "execution_order": optimized_order,
            "optimization_applied": True
        })
        
        return plan
    
    async def _allocate_resources(self, plan: ExecutionPlan, context: OrchestrationContext):
        """Asigna recursos para el plan de ejecución"""
        
        logger.info(f"Asignando recursos para plan: {plan.id}")
        
        for step in plan.steps:
            # Determinar recursos requeridos
            resource_requirements = self._calculate_resource_requirements(step)
            
            # Crear solicitudes de recursos
            for resource_type, amount in resource_requirements.items():
                request = ResourceRequest(
                    step_id=step.id,
                    resource_type=resource_type,
                    requested_amount=amount,
                    priority=step.priority,
                    timeout=step.estimated_duration * 2  # Timeout 2x duración estimada
                )
                
                # Solicitar recursos
                allocation = await self.resource_manager.request_resources(request)
                
                if not allocation:
                    logger.warning(f"No se pudieron asignar recursos para paso: {step.id}")
                    # Podría implementar estrategia de espera o reducción de recursos
    
    async def _execute_plan(self, plan: ExecutionPlan, context: OrchestrationContext) -> Dict[str, ExecutionResult]:
        """Ejecuta el plan usando el motor de ejecución adaptativa"""
        
        # Crear contexto de ejecución
        execution_context = ExecutionContext(
            task_id=context.task_id,
            session_id=context.session_id,
            user_id=context.user_id,
            environment={"orchestrator": "TaskOrchestrator"},
            resources=self.resource_manager.get_resource_status(),
            constraints=context.constraints,
            variables=context.metadata
        )
        
        # Configurar callbacks
        self.execution_engine.set_callbacks(
            progress_callback=self._on_step_progress,
            completion_callback=self._on_execution_complete,
            error_callback=self._on_execution_error,
            adaptation_callback=self._on_adaptation
        )
        
        # Ejecutar plan
        execution_summary = await self.execution_engine.execute_plan(
            plan, execution_context
        )
        
        return execution_summary.get("results", {})
    
    async def _release_resources(self, task_id: str):
        """Libera recursos asignados a la tarea"""
        
        logger.info(f"Liberando recursos para tarea: {task_id}")
        
        # Obtener pasos de la tarea
        if task_id in self.active_orchestrations:
            orchestration = self.active_orchestrations[task_id]
            # Liberar recursos paso por paso
            # (implementación específica dependería de cómo se rastrean los recursos por paso)
        
        # Limpiar asignaciones caducadas
        self.resource_manager.cleanup_expired_allocations()
    
    def _generate_result(self, context: OrchestrationContext, plan: ExecutionPlan,
                        execution_results: Dict[str, ExecutionResult], start_time: float) -> OrchestrationResult:
        """Genera el resultado de orquestación"""
        
        total_execution_time = time.time() - start_time
        
        # Calcular estadísticas
        completed_steps = sum(1 for result in execution_results.values() 
                            if result.status.value == "completed")
        failed_steps = sum(1 for result in execution_results.values() 
                          if result.status.value == "failed")
        
        total_adaptations = sum(len(result.adaptations_made) for result in execution_results.values())
        
        # Determinar éxito general
        success = failed_steps == 0 and completed_steps > 0
        
        # Calcular uso de recursos
        resource_usage = self._calculate_resource_usage(execution_results)
        
        result = OrchestrationResult(
            task_id=context.task_id,
            success=success,
            execution_plan=plan,
            execution_results=execution_results,
            total_execution_time=total_execution_time,
            steps_completed=completed_steps,
            steps_failed=failed_steps,
            adaptations_made=total_adaptations,
            resource_usage=resource_usage,
            metadata={
                "planning_strategy": plan.strategy.value,
                "total_steps": len(plan.steps),
                "success_rate": completed_steps / len(plan.steps) if plan.steps else 0,
                "context": context.metadata
            }
        )
        
        return result
    
    async def _on_step_progress(self, step_id: str, result: ExecutionResult, 
                              execution_state: Dict[str, Any]):
        """Callback para progreso de pasos"""
        
        # Actualizar uso de recursos
        self.resource_manager.update_resource_usage(
            step_id, 
            result.resources_used
        )
        
        # Notificar progreso
        await self._notify_callbacks("on_progress", {
            "step_id": step_id,
            "result": result,
            "execution_state": execution_state
        })
    
    async def _on_execution_complete(self, execution_summary: Dict[str, Any]):
        """Callback para finalización de ejecución"""
        
        logger.info(f"Ejecución completada: {execution_summary}")
    
    async def _on_execution_error(self, error: Exception):
        """Callback para errores de ejecución"""
        
        logger.error(f"Error en ejecución: {error}")
        
        await self._notify_callbacks("on_error", {
            "error": str(error),
            "type": "execution_error"
        })
    
    async def _on_adaptation(self, original_step: TaskStep, adapted_step: TaskStep, trigger):
        """Callback para adaptaciones"""
        
        logger.info(f"Adaptación aplicada: {original_step.id} -> {adapted_step.id}")
        
        await self._notify_callbacks("on_adaptation", {
            "original_step": original_step,
            "adapted_step": adapted_step,
            "trigger": trigger
        })
    
    def _validate_context(self, context: OrchestrationContext) -> bool:
        """Valida el contexto de orquestación"""
        
        if not context.task_id:
            logger.error("ID de tarea requerido")
            return False
        
        if not context.task_description:
            logger.error("Descripción de tarea requerida")
            return False
        
        if not context.user_id:
            logger.error("ID de usuario requerido")
            return False
        
        return True
    
    def _check_concurrency_limits(self) -> bool:
        """Verifica límites de concurrencia"""
        
        max_concurrent = self.config["max_concurrent_tasks"]
        current_active = len(self.active_orchestrations)
        
        if current_active >= max_concurrent:
            logger.warning(f"Límite de concurrencia alcanzado: {current_active}/{max_concurrent}")
            return False
        
        return True
    
    async def _get_task_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene historial de tareas del usuario"""
        
        # Filtrar historial por usuario
        user_history = [
            entry for entry in self.orchestration_history
            if entry.get("user_id") == user_id
        ]
        
        return user_history[-10:]  # Últimas 10 tareas
    
    async def _resolve_dependency_issues(self, plan: ExecutionPlan, 
                                       issues: Dict[str, List[str]]) -> ExecutionPlan:
        """Resuelve problemas de dependencias"""
        
        logger.info(f"Resolviendo {len(issues)} problemas de dependencias")
        
        for step_id, step_issues in issues.items():
            step = next((s for s in plan.steps if s.id == step_id), None)
            if step:
                # Resolver dependencias faltantes
                valid_dependencies = []
                for dep_id in step.dependencies:
                    if any(s.id == dep_id for s in plan.steps):
                        valid_dependencies.append(dep_id)
                
                step.dependencies = valid_dependencies
        
        return plan
    
    def _calculate_resource_requirements(self, step: TaskStep) -> Dict[ResourceType, float]:
        """Calcula requerimientos de recursos para un paso"""
        
        requirements = {}
        
        # Requerimientos basados en herramienta
        tool_requirements = {
            "web_search": {ResourceType.MEMORY: 100, ResourceType.CPU: 10},
            "deep_research": {ResourceType.MEMORY: 200, ResourceType.CPU: 20},
            "comprehensive_research": {ResourceType.MEMORY: 300, ResourceType.CPU: 30},
            "file_manager": {ResourceType.MEMORY: 50, ResourceType.DISK: 100},
            "shell": {ResourceType.MEMORY: 100, ResourceType.CPU: 15},
            "playwright": {ResourceType.MEMORY: 150, ResourceType.CPU: 25}
        }
        
        if step.tool in tool_requirements:
            requirements.update(tool_requirements[step.tool])
        
        # Ajustar por complejidad
        complexity_multiplier = 1.0 + (step.complexity * 0.5)
        
        for resource_type, amount in requirements.items():
            requirements[resource_type] = amount * complexity_multiplier
        
        return requirements
    
    def _calculate_resource_usage(self, execution_results: Dict[str, ExecutionResult]) -> Dict[str, Any]:
        """Calcula el uso total de recursos"""
        
        total_memory = sum(result.resources_used.get("memory", 0) 
                          for result in execution_results.values())
        
        total_cpu = sum(result.resources_used.get("cpu", 0) 
                       for result in execution_results.values())
        
        avg_memory = total_memory / len(execution_results) if execution_results else 0
        avg_cpu = total_cpu / len(execution_results) if execution_results else 0
        
        return {
            "total_memory": total_memory,
            "total_cpu": total_cpu,
            "avg_memory": avg_memory,
            "avg_cpu": avg_cpu,
            "resource_efficiency": self._calculate_resource_efficiency(execution_results)
        }
    
    def _calculate_resource_efficiency(self, execution_results: Dict[str, ExecutionResult]) -> float:
        """Calcula eficiencia de uso de recursos"""
        
        if not execution_results:
            return 0.0
        
        total_allocated = 0
        total_used = 0
        
        for result in execution_results.values():
            # Aproximación de recursos asignados vs utilizados
            allocated = result.resources_used.get("allocated", 100)  # Default
            used = result.resources_used.get("actual", 0)
            
            total_allocated += allocated
            total_used += used
        
        return (total_used / total_allocated) if total_allocated > 0 else 0.0
    
    def _update_metrics(self, result: OrchestrationResult):
        """Actualiza métricas de orquestación"""
        
        if result.success:
            self.orchestration_metrics["successful_tasks"] += 1
        else:
            self.orchestration_metrics["failed_tasks"] += 1
        
        # Actualizar tiempo promedio
        current_avg = self.orchestration_metrics["avg_execution_time"]
        total_tasks = self.orchestration_metrics["total_tasks"]
        
        new_avg = ((current_avg * (total_tasks - 1)) + result.total_execution_time) / total_tasks
        self.orchestration_metrics["avg_execution_time"] = new_avg
        
        # Actualizar contadores
        self.orchestration_metrics["total_steps_executed"] += result.steps_completed
        self.orchestration_metrics["total_adaptations"] += result.adaptations_made
        
        # Actualizar eficiencia de recursos
        if result.resource_usage:
            efficiency = result.resource_usage.get("resource_efficiency", 0)
            current_efficiency = self.orchestration_metrics["resource_efficiency"]
            
            new_efficiency = ((current_efficiency * (total_tasks - 1)) + efficiency) / total_tasks
            self.orchestration_metrics["resource_efficiency"] = new_efficiency
    
    def _cleanup_orchestration(self, task_id: str):
        """Limpia el estado de orquestación"""
        
        if task_id in self.active_orchestrations:
            orchestration = self.active_orchestrations[task_id]
            
            # Agregar al historial
            self.orchestration_history.append({
                "task_id": task_id,
                "user_id": orchestration["context"].user_id,
                "start_time": orchestration["start_time"],
                "end_time": time.time(),
                "description": orchestration["context"].task_description
            })
            
            # Mantener tamaño del historial
            if len(self.orchestration_history) > 1000:
                self.orchestration_history = self.orchestration_history[-800:]
            
            del self.active_orchestrations[task_id]
    
    async def _notify_callbacks(self, event_type: str, data: Any):
        """Notifica callbacks registrados"""
        
        if event_type in self.orchestration_callbacks:
            for callback in self.orchestration_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error en callback {event_type}: {e}")
    
    def add_callback(self, event_type: str, callback: Callable):
        """Agrega un callback para un evento"""
        
        if event_type in self.orchestration_callbacks:
            self.orchestration_callbacks[event_type].append(callback)
        else:
            logger.warning(f"Tipo de evento desconocido: {event_type}")
    
    def remove_callback(self, event_type: str, callback: Callable):
        """Remueve un callback"""
        
        if event_type in self.orchestration_callbacks:
            try:
                self.orchestration_callbacks[event_type].remove(callback)
            except ValueError:
                logger.warning(f"Callback no encontrado para evento: {event_type}")
    
    def get_orchestration_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estado de orquestación"""
        
        if task_id in self.active_orchestrations:
            orchestration = self.active_orchestrations[task_id]
            return {
                "task_id": task_id,
                "status": orchestration.get("status", "unknown"),
                "start_time": orchestration["start_time"],
                "elapsed_time": time.time() - orchestration["start_time"],
                "context": orchestration["context"]
            }
        
        return None
    
    def get_active_orchestrations(self) -> List[Dict[str, Any]]:
        """Obtiene todas las orquestaciones activas"""
        
        return [
            self.get_orchestration_status(task_id)
            for task_id in self.active_orchestrations.keys()
        ]
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de orquestación"""
        
        metrics = self.orchestration_metrics.copy()
        
        # Agregar métricas de componentes
        metrics.update({
            "planning_engine": self.planning_engine.get_metrics(),
            "execution_engine": self.execution_engine.get_execution_metrics(),
            "resource_manager": self.resource_manager.get_allocation_metrics()
        })
        
        return metrics
    
    def update_config(self, new_config: Dict[str, Any]):
        """Actualiza configuración"""
        
        self.config.update(new_config)
        
        # Propagar configuración a componentes
        if "planning_config" in new_config:
            self.planning_engine.update_config(new_config["planning_config"])
        
        if "execution_config" in new_config:
            self.execution_engine.update_config(new_config["execution_config"])
        
        logger.info(f"Configuración actualizada: {new_config}")
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene configuración actual"""
        
        return {
            "orchestrator": self.config.copy(),
            "planning_engine": self.planning_engine.get_config(),
            "execution_engine": self.execution_engine.get_config()
        }
    
    async def cancel_orchestration(self, task_id: str) -> bool:
        """Cancela una orquestación activa"""
        
        if task_id in self.active_orchestrations:
            logger.info(f"Cancelando orquestación: {task_id}")
            
            # Marcar como cancelada
            self.active_orchestrations[task_id]["status"] = "cancelled"
            
            # Liberar recursos
            await self._release_resources(task_id)
            
            # Limpiar estado
            self._cleanup_orchestration(task_id)
            
            return True
        
        return False
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones de optimización"""
        
        recommendations = []
        
        # Recomendaciones basadas en métricas
        metrics = self.orchestration_metrics
        
        if metrics["total_tasks"] > 10:
            success_rate = metrics["successful_tasks"] / metrics["total_tasks"]
            
            if success_rate < 0.8:
                recommendations.append({
                    "type": "low_success_rate",
                    "message": f"Tasa de éxito baja: {success_rate:.1%}",
                    "recommendation": "Revisar configuración de timeouts y recursos"
                })
        
        if metrics["avg_execution_time"] > 300:  # 5 minutos
            recommendations.append({
                "type": "slow_execution",
                "message": f"Tiempo promedio alto: {metrics['avg_execution_time']:.1f}s",
                "recommendation": "Considerar optimización de recursos o paralelización"
            })
        
        if metrics["resource_efficiency"] < 0.5:
            recommendations.append({
                "type": "low_efficiency",
                "message": f"Eficiencia de recursos baja: {metrics['resource_efficiency']:.1%}",
                "recommendation": "Optimizar asignación de recursos"
            })
        
        # Agregar recomendaciones de componentes
        recommendations.extend(self.resource_manager.get_resource_recommendations())
        
        return recommendations
    
    def __del__(self):
        """Destructor para limpiar recursos"""
        
        # Limpiar orquestaciones activas
        for task_id in list(self.active_orchestrations.keys()):
            asyncio.create_task(self.cancel_orchestration(task_id))
        
        # Detener resource manager
        if hasattr(self.resource_manager, '__del__'):
            self.resource_manager.__del__()