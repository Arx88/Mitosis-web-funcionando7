"""
Execution Engine - Motor de ejecución de planes de tareas
Coordina la ejecución automática de pasos de tareas con manejo de errores y recuperación
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

from .task_planner import TaskPlanner, ExecutionPlan, TaskStep
from .dynamic_task_planner import DynamicTaskPlanner, get_dynamic_task_planner
from .tool_manager import ToolManager
from .environment_setup_manager import EnvironmentSetupManager
from .context_manager import ContextManager, ContextScope, VariableType
from src.agents.replanning_engine import ReplanningEngine, ReplanningContext, ReplanningResult

logger = logging.getLogger(__name__)

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"

class ExecutionStrategy(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"

@dataclass
class StepExecution:
    step: TaskStep
    status: StepStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    execution_time: float = 0.0

@dataclass
class ExecutionContext:
    task_id: str
    execution_plan: ExecutionPlan
    step_executions: List[StepExecution]
    variables: Dict[str, Any]
    current_step_index: int = 0
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    total_execution_time: float = 0.0
    success_rate: float = 0.0
    context_session_id: Optional[str] = None  # ID de sesión del context manager

class ExecutionEngine:
    def __init__(self, tool_manager: ToolManager, environment_manager: EnvironmentSetupManager):
        self.tool_manager = tool_manager
        self.environment_manager = environment_manager
        self.task_planner = TaskPlanner()
        self.dynamic_task_planner = get_dynamic_task_planner()  # 🚀 Agregar planificador dinámico
        self.context_manager = ContextManager()  # Inicializar context manager
        
        # 🔄 Inicializar ReplanningEngine
        self.replanning_engine = None  # Se inicializará cuando se necesite
        
        # Configuración de ejecución
        self.config = {
            'max_retries': 3,
            'retry_delay': 2.0,  # segundos
            'timeout_per_step': 300,  # 5 minutos
            'parallel_execution': False,
            'fail_fast': False,
            'auto_recovery': True,
            'auto_checkpoint': True,  # Checkpoints automáticos
            'checkpoint_frequency': 3,  # Cada 3 pasos
            'dynamic_planning': True,  # 🚀 Habilitar planificación dinámica
            'context_monitoring': True,  # 🚀 Monitoreo de contexto
            'enable_replanning': True,  # 🔄 Habilitar replanificación dinámica
            'max_replanning_attempts': 3,  # 🔄 Máximo 3 intentos de replanificación
            'replanning_confidence_threshold': 0.6  # 🔄 Umbral de confianza para replanificación
        }
        
        # Contextos de ejecución activos
        self.execution_contexts: Dict[str, ExecutionContext] = {}
        
        # Callbacks para notificaciones
        self.progress_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # 🚀 Configurar callbacks del DynamicTaskPlanner
        self.dynamic_task_planner.set_callbacks(
            plan_update_callback=self._on_plan_updated,
            context_change_callback=self._on_context_changed
        )
    
    def _on_plan_updated(self, plan_data: Dict[str, Any]):
        """Callback para cuando se actualiza el plan de tareas"""
        print(f"📋 Plan updated: {plan_data}")
        # Aquí puedes agregar lógica para manejar actualizaciones del plan
        
    def _on_context_changed(self, context_data: Dict[str, Any]):
        """Callback para cuando cambia el contexto de ejecución"""
        print(f"🔄 Context changed: {context_data}")
        # Aquí puedes agregar lógica para manejar cambios de contexto
    
    def add_progress_callback(self, callback: Callable):
        """Agregar callback para actualizaciones de progreso"""
        self.progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable):
        """Agregar callback para completación de tareas"""
        self.completion_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Agregar callback para manejo de errores"""
        self.error_callbacks.append(callback)
    
    async def execute_task(self, task_id: str, task_title: str, 
                          task_description: str = "", config: Dict[str, Any] = None) -> ExecutionContext:
        """Ejecutar una tarea completa de manera autónoma con planificación dinámica"""
        
        if config:
            self.config.update(config)
        
        try:
            # Crear sesión de contexto para la tarea
            context_session_id = self.context_manager.create_session(
                task_id, 
                metadata={
                    'task_title': task_title,
                    'task_description': task_description,
                    'created_by': 'execution_engine'
                }
            )
            
            # 🚀 Generar plan de ejecución dinámico
            if self.config.get('dynamic_planning', True):
                execution_plan = await self.dynamic_task_planner.create_dynamic_plan(
                    task_id, 
                    f"{task_title}: {task_description}",
                    {
                        'available_tools': self.tool_manager.get_available_tools() if self.tool_manager else [],
                        'environment_state': {'initial_tools': self.tool_manager.get_available_tools() if self.tool_manager else []}
                    }
                )
            else:
                # Fallback al planificador estático
                execution_plan = self.task_planner.generate_execution_plan(
                    task_id, task_title, task_description
                )
            
            # Crear contexto de ejecución
            context = ExecutionContext(
                task_id=task_id,
                execution_plan=execution_plan,
                step_executions=[
                    StepExecution(step=step, status=StepStatus.PENDING)
                    for step in execution_plan.steps
                ],
                variables={},
                start_time=datetime.now(),
                context_session_id=context_session_id
            )
            
            self.execution_contexts[task_id] = context
            
            # Inicializar variables de contexto
            await self._initialize_context_variables(context, task_title, task_description)
            
            # Crear checkpoint inicial
            if self.config.get('auto_checkpoint', True):
                checkpoint_id = self.context_manager.create_checkpoint(
                    context_session_id,
                    "initial",
                    "Initial checkpoint before execution starts",
                    auto_created=True
                )
                
                # Guardar checkpoint ID en contexto
                self.context_manager.set_variable(
                    context_session_id,
                    "initial_checkpoint_id",
                    checkpoint_id,
                    VariableType.STRING,
                    ContextScope.TASK
                )
            
            # Notificar inicio
            await self._notify_progress(context, "execution_started", {
                'plan': asdict(execution_plan),
                'estimated_duration': execution_plan.total_estimated_duration,
                'context_session_id': context_session_id
            })
            
            # Ejecutar pasos según estrategia
            if self.config.get('parallel_execution', False):
                await self._execute_parallel(context)
            else:
                await self._execute_sequential(context)
            
            # Calcular métricas finales
            context.total_execution_time = (
                datetime.now() - context.start_time
            ).total_seconds()
            
            completed_steps = sum(
                1 for exec in context.step_executions 
                if exec.status == StepStatus.COMPLETED
            )
            context.success_rate = completed_steps / len(context.step_executions)
            
            # Determinar estado final
            if context.success_rate == 1.0:
                context.status = StepStatus.COMPLETED
            elif context.success_rate > 0.5:
                context.status = StepStatus.COMPLETED  # Parcialmente exitoso
            else:
                context.status = StepStatus.FAILED
            
            # Crear checkpoint final
            if self.config.get('auto_checkpoint', True):
                self.context_manager.create_checkpoint(
                    context_session_id,
                    "final",
                    f"Final checkpoint - Status: {context.status.value}, Success rate: {context.success_rate}",
                    auto_created=True
                )
            
            # Guardar métricas finales en contexto
            await self._save_final_metrics(context)
            
            # Notificar completación
            await self._notify_completion(context)
            
            return context
            
        except Exception as e:
            # Manejo de errores a nivel de tarea
            if task_id in self.execution_contexts:
                context = self.execution_contexts[task_id]
                context.status = StepStatus.FAILED
                
                # Crear checkpoint de error si existe sesión
                if context.context_session_id:
                    self.context_manager.create_checkpoint(
                        context.context_session_id,
                        "error",
                        f"Error checkpoint: {str(e)}",
                        auto_created=True
                    )
                
                await self._notify_error(context, str(e))
            
            raise
    
    async def _execute_sequential(self, context: ExecutionContext):
        """Ejecutar pasos de manera secuencial"""
        
        for i, step_execution in enumerate(context.step_executions):
            context.current_step_index = i
            
            # Verificar dependencias
            if not await self._check_dependencies(context, step_execution.step):
                step_execution.status = StepStatus.SKIPPED
                continue
            
            # Crear checkpoint automático cada N pasos
            if (self.config.get('auto_checkpoint', True) and 
                i % self.config.get('checkpoint_frequency', 3) == 0 and 
                i > 0):
                self.context_manager.create_checkpoint(
                    context.context_session_id,
                    f"step_{i}",
                    f"Auto checkpoint at step {i}",
                    auto_created=True
                )
            
            # Ejecutar paso con reintentos
            success = await self._execute_step_with_retries(context, step_execution)
            
            if not success and self.config.get('fail_fast', False):
                break
            
            # Notificar progreso
            await self._notify_progress(context, "step_completed", {
                'step_index': i,
                'step_id': step_execution.step.id,
                'status': step_execution.status.value,
                'progress': (i + 1) / len(context.step_executions)
            })
    
    async def _execute_parallel(self, context: ExecutionContext):
        """Ejecutar pasos en paralelo (donde sea posible)"""
        
        # Agrupar pasos por nivel de dependencias
        execution_levels = self._group_steps_by_dependencies(context.execution_plan.steps)
        
        for level_steps in execution_levels:
            # Ejecutar pasos del mismo nivel en paralelo
            tasks = []
            for step in level_steps:
                step_execution = next(
                    se for se in context.step_executions 
                    if se.step.id == step.id
                )
                tasks.append(self._execute_step_with_retries(context, step_execution))
            
            # Esperar a que todos los pasos del nivel se completen
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_step_with_retries(self, context: ExecutionContext, 
                                       step_execution: StepExecution) -> bool:
        """Ejecutar un paso con lógica de reintentos"""
        
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 2.0)
        
        for attempt in range(max_retries + 1):
            step_execution.retry_count = attempt
            
            if attempt > 0:
                step_execution.status = StepStatus.RETRYING
                await asyncio.sleep(retry_delay * attempt)  # Backoff exponencial
            else:
                step_execution.status = StepStatus.RUNNING
            
            try:
                success = await self._execute_single_step(context, step_execution)
                if success:
                    step_execution.status = StepStatus.COMPLETED
                    return True
                    
            except Exception as e:
                step_execution.error = str(e)
                
                # Intentar recuperación automática si está habilitada
                if self.config.get('auto_recovery', True) and attempt < max_retries:
                    recovery_success = await self._attempt_auto_recovery(
                        context, step_execution, e
                    )
                    if recovery_success:
                        continue
        
        # Todos los intentos fallaron
        step_execution.status = StepStatus.FAILED
        return False
    
    async def _execute_single_step(self, context: ExecutionContext, 
                                 step_execution: StepExecution) -> bool:
        """Ejecutar un paso individual"""
        
        step = step_execution.step
        step_execution.start_time = datetime.now()
        
        try:
            # Preparar parámetros del paso usando context manager
            parameters = await self._prepare_step_parameters_with_context(context, step)
            
            # Ejecutar herramienta
            result = self.tool_manager.execute_tool(
                tool_name=step.tool,
                parameters=parameters,
                config={'timeout': self.config.get('timeout_per_step', 300)},
                task_id=context.task_id
            )
            
            step_execution.result = result
            step_execution.end_time = datetime.now()
            step_execution.execution_time = (
                step_execution.end_time - step_execution.start_time
            ).total_seconds()
            
            # Verificar si la ejecución fue exitosa
            success = self._evaluate_step_result(result)
            
            if success:
                # Extraer y guardar variables del resultado en context manager
                await self._extract_and_store_variables(context, step, result)
                
                # Crear checkpoint del paso si fue exitoso
                if self.config.get('auto_checkpoint', True):
                    self.context_manager.create_checkpoint(
                        context.context_session_id,
                        step.id,
                        f"Step {step.id} completed successfully",
                        auto_created=True
                    )
            else:
                # Guardar error en contexto
                if context.context_session_id:
                    self.context_manager.set_variable(
                        context.context_session_id,
                        f"{step.id}_error",
                        result.get('error', 'Unknown error'),
                        VariableType.STRING,
                        ContextScope.STEP,
                        source_step=step.id
                    )
            
            return success
            
        except Exception as e:
            step_execution.error = str(e)
            step_execution.end_time = datetime.now()
            if step_execution.start_time:
                step_execution.execution_time = (
                    step_execution.end_time - step_execution.start_time
                ).total_seconds()
            
            # Guardar error en contexto
            if context.context_session_id:
                self.context_manager.set_variable(
                    context.context_session_id,
                    f"{step.id}_exception",
                    str(e),
                    VariableType.STRING,
                    ContextScope.STEP,
                    source_step=step.id
                )
            
            return False
    
    async def _check_dependencies(self, context: ExecutionContext, step: TaskStep) -> bool:
        """Verificar que las dependencias de un paso estén completadas"""
        
        if not step.dependencies:
            return True
        
        for dep_id in step.dependencies:
            dep_execution = next(
                (se for se in context.step_executions if se.step.id == dep_id),
                None
            )
            
            if not dep_execution or dep_execution.status != StepStatus.COMPLETED:
                return False
        
        return True
    
    async def _prepare_step_parameters_with_context(self, context: ExecutionContext, 
                                                  step: TaskStep) -> Dict[str, Any]:
        """Preparar parámetros para un paso, resolviendo variables del contexto"""
        
        parameters = step.parameters.copy()
        
        if not context.context_session_id:
            return parameters
        
        # Resolver variables en parámetros usando context manager
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                var_name = value[2:-1]
                
                # Buscar variable en context manager
                context_value = self.context_manager.get_variable(
                    context.context_session_id, var_name
                )
                
                if context_value is not None:
                    parameters[key] = context_value
                else:
                    # Fallback al contexto local
                    if var_name in context.variables:
                        parameters[key] = context.variables[var_name]
        
        return parameters
    
    async def _extract_and_store_variables(self, context: ExecutionContext, 
                                         step: TaskStep, result: Dict[str, Any]):
        """Extraer variables del resultado y guardarlas en context manager"""
        
        if not context.context_session_id:
            return
        
        # Extraer paths de archivos creados
        if step.tool == 'file_manager' and 'path' in result:
            self.context_manager.set_variable(
                context.context_session_id,
                f"{step.id}_file_path",
                result['path'],
                VariableType.FILE_PATH,
                ContextScope.STEP,
                source_step=step.id
            )
        
        # Extraer resultados de búsqueda
        if step.tool in ['web_search', 'enhanced_web_search'] and 'search_results' in result:
            self.context_manager.set_variable(
                context.context_session_id,
                f"{step.id}_search_results",
                result['search_results'],
                VariableType.RESULT,
                ContextScope.STEP,
                source_step=step.id
            )
        
        # Extraer output de comandos shell
        if step.tool == 'shell' and 'stdout' in result:
            self.context_manager.set_variable(
                context.context_session_id,
                f"{step.id}_output",
                result['stdout'],
                VariableType.STRING,
                ContextScope.STEP,
                source_step=step.id
            )
        
        # Guardar resultado completo
        self.context_manager.set_variable(
            context.context_session_id,
            f"{step.id}_result",
            result,
            VariableType.RESULT,
            ContextScope.STEP,
            source_step=step.id
        )
        
        # También mantener compatibilidad con el contexto local
        context.variables[f"{step.id}_file_path"] = result.get('path')
        context.variables[f"{step.id}_search_results"] = result.get('search_results')
        context.variables[f"{step.id}_output"] = result.get('stdout')
    
    async def _initialize_context_variables(self, context: ExecutionContext, 
                                          task_title: str, task_description: str):
        """Inicializar variables de contexto para la tarea"""
        
        if not context.context_session_id:
            return
        
        # Variables básicas de la tarea
        self.context_manager.set_variable(
            context.context_session_id,
            "task_title",
            task_title,
            VariableType.STRING,
            ContextScope.TASK
        )
        
        self.context_manager.set_variable(
            context.context_session_id,
            "task_description",
            task_description,
            VariableType.STRING,
            ContextScope.TASK
        )
        
        self.context_manager.set_variable(
            context.context_session_id,
            "task_id",
            context.task_id,
            VariableType.STRING,
            ContextScope.TASK
        )
        
        self.context_manager.set_variable(
            context.context_session_id,
            "execution_start_time",
            context.start_time.isoformat(),
            VariableType.STRING,
            ContextScope.TASK
        )
        
        # Variables del plan de ejecución
        self.context_manager.set_variable(
            context.context_session_id,
            "total_steps",
            len(context.execution_plan.steps),
            VariableType.NUMBER,
            ContextScope.TASK
        )
        
        self.context_manager.set_variable(
            context.context_session_id,
            "estimated_duration",
            context.execution_plan.total_estimated_duration,
            VariableType.NUMBER,
            ContextScope.TASK
        )
    
    async def _save_final_metrics(self, context: ExecutionContext):
        """Guardar métricas finales en el contexto"""
        
        if not context.context_session_id:
            return
        
        self.context_manager.set_variable(
            context.context_session_id,
            "final_status",
            context.status.value,
            VariableType.STRING,
            ContextScope.TASK
        )
        
        self.context_manager.set_variable(
            context.context_session_id,
            "success_rate",
            context.success_rate,
            VariableType.NUMBER,
            ContextScope.TASK
        )
        
        self.context_manager.set_variable(
            context.context_session_id,
            "total_execution_time",
            context.total_execution_time,
            VariableType.NUMBER,
            ContextScope.TASK
        )
        
        self.context_manager.set_variable(
            context.context_session_id,
            "completed_steps",
            sum(1 for se in context.step_executions if se.status == StepStatus.COMPLETED),
            VariableType.NUMBER,
            ContextScope.TASK
        )
        
        self.context_manager.set_variable(
            context.context_session_id,
            "failed_steps",
            sum(1 for se in context.step_executions if se.status == StepStatus.FAILED),
            VariableType.NUMBER,
            ContextScope.TASK
        )
    
    def _evaluate_step_result(self, result: Dict[str, Any]) -> bool:
        """Evaluar si el resultado de un paso indica éxito"""
        
        # Verificar indicadores comunes de éxito
        if 'success' in result:
            return result['success']
        
        if 'error' in result:
            return False
        
        # Si no hay indicadores claros, asumir éxito si hay resultado
        return result is not None
    
    async def _extract_variables_from_result(self, context: ExecutionContext, 
                                           step: TaskStep, result: Dict[str, Any]):
        """Extraer variables del resultado para uso en pasos posteriores"""
        
        # Extraer paths de archivos creados
        if step.tool == 'file_manager' and 'path' in result:
            context.variables[f"{step.id}_file_path"] = result['path']
        
        # Extraer resultados de búsqueda
        if step.tool in ['web_search', 'enhanced_web_search'] and 'search_results' in result:
            context.variables[f"{step.id}_search_results"] = result['search_results']
        
        # Extraer output de comandos shell
        if step.tool == 'shell' and 'stdout' in result:
            context.variables[f"{step.id}_output"] = result['stdout']
    
    async def _attempt_auto_recovery(self, context: ExecutionContext, 
                                   step_execution: StepExecution, error: Exception) -> bool:
        """Intentar recuperación automática de errores"""
        
        step = step_execution.step
        error_str = str(error).lower()
        
        # Estrategias de recuperación por tipo de herramienta
        if step.tool == 'shell':
            # Para comandos shell, intentar con sudo si es error de permisos
            if 'permission denied' in error_str:
                original_command = step.parameters.get('command', '')
                if not original_command.startswith('sudo'):
                    step.parameters['command'] = f"sudo {original_command}"
                    return True
        
        elif step.tool == 'file_manager':
            # Para file manager, intentar crear directorio padre si no existe
            if 'no such file or directory' in error_str:
                path = step.parameters.get('path', '')
                if path:
                    import os
                    parent_dir = os.path.dirname(path)
                    if parent_dir:
                        # Crear directorio padre primero
                        self.tool_manager.execute_tool(
                            'file_manager',
                            {'action': 'mkdir', 'path': parent_dir},
                            task_id=context.task_id
                        )
                        return True
        
        elif step.tool in ['web_search', 'enhanced_web_search']:
            # Para búsquedas web, intentar con query simplificada
            if 'timeout' in error_str or 'connection' in error_str:
                original_query = step.parameters.get('query', '')
                # Simplificar query removiendo palabras complejas
                simplified_query = ' '.join(original_query.split()[:3])
                step.parameters['query'] = simplified_query
                return True
        
        return False
    
    def _group_steps_by_dependencies(self, steps: List[TaskStep]) -> List[List[TaskStep]]:
        """Agrupar pasos por niveles de dependencias para ejecución paralela"""
        
        levels = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            current_level = []
            
            for step in remaining_steps[:]:
                # Un paso puede ejecutarse si todas sus dependencias están en niveles anteriores
                can_execute = True
                for dep_id in step.dependencies:
                    dep_in_previous_levels = any(
                        any(s.id == dep_id for s in level)
                        for level in levels
                    )
                    if not dep_in_previous_levels:
                        can_execute = False
                        break
                
                if can_execute:
                    current_level.append(step)
                    remaining_steps.remove(step)
            
            if current_level:
                levels.append(current_level)
            else:
                # Evitar bucles infinitos
                break
        
        return levels
    
    async def _notify_progress(self, context: ExecutionContext, event: str, data: Dict[str, Any]):
        """Notificar progreso a callbacks registrados"""
        
        notification = {
            'task_id': context.task_id,
            'event': event,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    async def _notify_completion(self, context: ExecutionContext):
        """Notificar completación de tarea"""
        
        notification = {
            'task_id': context.task_id,
            'status': context.status.value,
            'success_rate': context.success_rate,
            'total_execution_time': context.total_execution_time,
            'timestamp': datetime.now().isoformat(),
            'execution_summary': {
                'total_steps': len(context.step_executions),
                'completed_steps': sum(
                    1 for se in context.step_executions 
                    if se.status == StepStatus.COMPLETED
                ),
                'failed_steps': sum(
                    1 for se in context.step_executions 
                    if se.status == StepStatus.FAILED
                )
            }
        }
        
        for callback in self.completion_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                print(f"Error in completion callback: {e}")
    
    async def _notify_error(self, context: ExecutionContext, error: str):
        """Notificar errores críticos"""
        
        notification = {
            'task_id': context.task_id,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'context': {
                'current_step_index': context.current_step_index,
                'total_steps': len(context.step_executions)
            }
        }
        
        for callback in self.error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                print(f"Error in error callback: {e}")
    
    def get_execution_status(self, task_id: str) -> Dict[str, Any]:
        """Obtener estado actual de ejecución de una tarea"""
        
        if task_id not in self.execution_contexts:
            return {'error': 'Task not found'}
        
        context = self.execution_contexts[task_id]
        
        return {
            'task_id': task_id,
            'status': context.status.value,
            'progress': context.current_step_index / len(context.step_executions) if context.step_executions else 0,
            'current_step': context.current_step_index,
            'total_steps': len(context.step_executions),
            'execution_time': context.total_execution_time,
            'success_rate': context.success_rate,
            'steps': [
                {
                    'id': se.step.id,
                    'title': se.step.title,
                    'status': se.status.value,
                    'execution_time': se.execution_time,
                    'retry_count': se.retry_count
                }
                for se in context.step_executions
            ]
        }
    
    def stop_execution(self, task_id: str) -> bool:
        """Detener ejecución de una tarea"""
        
        if task_id in self.execution_contexts:
            context = self.execution_contexts[task_id]
            context.status = StepStatus.FAILED
            return True
        
        return False
    
    def cleanup_execution(self, task_id: str):
        """Limpiar contexto de ejecución de una tarea"""
        
        if task_id in self.execution_contexts:
            context = self.execution_contexts[task_id]
            
            # Cerrar sesión del context manager
            if context.context_session_id:
                self.context_manager.close_session(context.context_session_id)
            
            del self.execution_contexts[task_id]
    
    def get_context_info(self, task_id: str) -> Dict[str, Any]:
        """Obtener información del contexto de una tarea"""
        
        if task_id not in self.execution_contexts:
            return {'error': 'Task not found'}
        
        context = self.execution_contexts[task_id]
        
        if not context.context_session_id:
            return {'error': 'No context session found'}
        
        return self.context_manager.get_session_info(context.context_session_id)
    
    def create_manual_checkpoint(self, task_id: str, description: str = "") -> Dict[str, Any]:
        """Crear checkpoint manual"""
        
        if task_id not in self.execution_contexts:
            return {'error': 'Task not found'}
        
        context = self.execution_contexts[task_id]
        
        if not context.context_session_id:
            return {'error': 'No context session found'}
        
        try:
            checkpoint_id = self.context_manager.create_checkpoint(
                context.context_session_id,
                f"manual_{context.current_step_index}",
                description or f"Manual checkpoint at step {context.current_step_index}",
                auto_created=False
            )
            
            return {
                'success': True,
                'checkpoint_id': checkpoint_id,
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def restore_checkpoint(self, task_id: str, checkpoint_id: str) -> Dict[str, Any]:
        """Restaurar checkpoint"""
        
        if task_id not in self.execution_contexts:
            return {'error': 'Task not found'}
        
        context = self.execution_contexts[task_id]
        
        if not context.context_session_id:
            return {'error': 'No context session found'}
        
        try:
            success = self.context_manager.restore_checkpoint(
                context.context_session_id,
                checkpoint_id
            )
            
            if success:
                return {
                    'success': True,
                    'message': f'Checkpoint {checkpoint_id} restored successfully',
                    'restored_at': datetime.now().isoformat()
                }
            else:
                return {'error': 'Checkpoint not found or restoration failed'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def get_checkpoints(self, task_id: str) -> Dict[str, Any]:
        """Obtener lista de checkpoints"""
        
        if task_id not in self.execution_contexts:
            return {'error': 'Task not found'}
        
        context = self.execution_contexts[task_id]
        
        if not context.context_session_id:
            return {'error': 'No context session found'}
        
        try:
            checkpoints = self.context_manager.get_checkpoints(context.context_session_id)
            return {
                'success': True,
                'checkpoints': checkpoints,
                'total_checkpoints': len(checkpoints)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_context_variables(self, task_id: str, scope: str = None) -> Dict[str, Any]:
        """Obtener variables del contexto"""
        
        if task_id not in self.execution_contexts:
            return {'error': 'Task not found'}
        
        context = self.execution_contexts[task_id]
        
        if not context.context_session_id:
            return {'error': 'No context session found'}
        
        try:
            # Convertir scope string a enum
            context_scope = None
            if scope:
                try:
                    context_scope = ContextScope(scope)
                except ValueError:
                    return {'error': f'Invalid scope: {scope}'}
            
            variables = self.context_manager.get_all_variables(
                context.context_session_id,
                context_scope
            )
            
            return {
                'success': True,
                'variables': variables,
                'total_variables': len(variables),
                'scope': scope
            }
        except Exception as e:
            return {'error': str(e)}
    
    def set_context_variable(self, task_id: str, key: str, value: Any, 
                           var_type: str = "object", scope: str = "task") -> Dict[str, Any]:
        """Establecer variable en el contexto"""
        
        if task_id not in self.execution_contexts:
            return {'error': 'Task not found'}
        
        context = self.execution_contexts[task_id]
        
        if not context.context_session_id:
            return {'error': 'No context session found'}
        
        try:
            # Convertir strings a enums
            variable_type = VariableType(var_type)
            context_scope = ContextScope(scope)
            
            success = self.context_manager.set_variable(
                context.context_session_id,
                key,
                value,
                variable_type,
                context_scope,
                source_step="manual"
            )
            
            if success:
                return {
                    'success': True,
                    'message': f'Variable {key} set successfully',
                    'set_at': datetime.now().isoformat()
                }
            else:
                return {'error': 'Failed to set variable'}
                
        except ValueError as e:
            return {'error': f'Invalid type or scope: {str(e)}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_context_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del context manager"""
        
        try:
            stats = self.context_manager.get_statistics()
            return {
                'success': True,
                'statistics': stats,
                'active_executions': len(self.execution_contexts)
            }
        except Exception as e:
            return {'error': str(e)}