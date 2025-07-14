"""
Execution Engine - Motor de ejecución de planes de tareas
Coordina la ejecución automática de pasos de tareas con manejo de errores y recuperación
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

from .task_planner import TaskPlanner, ExecutionPlan, TaskStep
from .tool_manager import ToolManager
from .environment_setup_manager import EnvironmentSetupManager

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

class ExecutionEngine:
    def __init__(self, tool_manager: ToolManager, environment_manager: EnvironmentSetupManager):
        self.tool_manager = tool_manager
        self.environment_manager = environment_manager
        self.task_planner = TaskPlanner()
        
        # Configuración de ejecución
        self.config = {
            'max_retries': 3,
            'retry_delay': 2.0,  # segundos
            'timeout_per_step': 300,  # 5 minutos
            'parallel_execution': False,
            'fail_fast': False,
            'auto_recovery': True
        }
        
        # Contextos de ejecución activos
        self.execution_contexts: Dict[str, ExecutionContext] = {}
        
        # Callbacks para notificaciones
        self.progress_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
    
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
        """Ejecutar una tarea completa de manera autónoma"""
        
        if config:
            self.config.update(config)
        
        try:
            # Generar plan de ejecución
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
                start_time=datetime.now()
            )
            
            self.execution_contexts[task_id] = context
            
            # Notificar inicio
            await self._notify_progress(context, "execution_started", {
                'plan': asdict(execution_plan),
                'estimated_duration': execution_plan.total_estimated_duration
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
            
            # Notificar completación
            await self._notify_completion(context)
            
            return context
            
        except Exception as e:
            # Manejo de errores a nivel de tarea
            if task_id in self.execution_contexts:
                context = self.execution_contexts[task_id]
                context.status = StepStatus.FAILED
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
            # Preparar parámetros del paso
            parameters = await self._prepare_step_parameters(context, step)
            
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
                # Extraer variables del resultado para pasos posteriores
                await self._extract_variables_from_result(context, step, result)
            
            return success
            
        except Exception as e:
            step_execution.error = str(e)
            step_execution.end_time = datetime.now()
            if step_execution.start_time:
                step_execution.execution_time = (
                    step_execution.end_time - step_execution.start_time
                ).total_seconds()
            
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
    
    async def _prepare_step_parameters(self, context: ExecutionContext, 
                                     step: TaskStep) -> Dict[str, Any]:
        """Preparar parámetros para un paso, resolviendo variables"""
        
        parameters = step.parameters.copy()
        
        # Resolver variables en parámetros
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                var_name = value[2:-1]
                if var_name in context.variables:
                    parameters[key] = context.variables[var_name]
        
        return parameters
    
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
            del self.execution_contexts[task_id]