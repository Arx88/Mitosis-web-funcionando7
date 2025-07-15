"""
Dynamic Task Planner - Planificador dinámico con re-planificación automática
Extiende TaskPlanner para adaptación en tiempo real durante la ejecución
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Importar clases base
from .task_planner import TaskPlanner, ExecutionPlan, TaskStep

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReplanReason(Enum):
    STEP_FAILED = "step_failed"
    CONTEXT_CHANGED = "context_changed"
    NEW_REQUIREMENTS = "new_requirements"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DEPENDENCY_CHANGED = "dependency_changed"
    RESOURCE_AVAILABILITY = "resource_availability"
    USER_FEEDBACK = "user_feedback"

@dataclass
class PlanChange:
    """Representa un cambio en el plan de ejecución"""
    change_id: str
    timestamp: datetime
    reason: ReplanReason
    description: str
    steps_added: List[TaskStep]
    steps_removed: List[str]  # step_ids
    steps_modified: List[TaskStep]
    impact_score: float  # 0-1, donde 1 es cambio completo
    confidence: float  # 0-1, confianza en el cambio

@dataclass
class ExecutionContext:
    """Contexto actual de ejecución para toma de decisiones"""
    task_id: str
    current_step: Optional[str]
    completed_steps: List[str]
    failed_steps: List[str]
    available_tools: List[str]
    execution_results: Dict[str, Any]
    performance_metrics: Dict[str, float]
    user_feedback: List[str]
    environment_state: Dict[str, Any]
    resource_usage: Dict[str, float]

class DynamicTaskPlanner(TaskPlanner):
    """
    Planificador dinámico que adapta planes en tiempo real durante la ejecución
    """
    
    def __init__(self):
        super().__init__()
        self.name = "dynamic_task_planner"
        self.description = "Planificador dinámico con re-planificación automática en tiempo real"
        
        # Estado interno para seguimiento
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.execution_contexts: Dict[str, ExecutionContext] = {}
        self.plan_history: Dict[str, List[PlanChange]] = {}
        
        # Callbacks para notificaciones
        self.plan_update_callback: Optional[Callable] = None
        self.context_change_callback: Optional[Callable] = None
        
        # Configuración de re-planificación
        self.replan_threshold = 0.3  # Umbral para disparar re-planificación
        self.max_replans_per_task = 5  # Máximo número de re-planificaciones
        self.context_check_interval = 30  # Segundos entre verificaciones de contexto
        
        logger.info("DynamicTaskPlanner initialized")
    
    def set_callbacks(self, plan_update_callback: Callable = None, 
                     context_change_callback: Callable = None):
        """Configurar callbacks para notificaciones"""
        self.plan_update_callback = plan_update_callback
        self.context_change_callback = context_change_callback
    
    async def create_dynamic_plan(self, task_id: str, user_input: str, 
                                 context: Dict[str, Any] = None) -> ExecutionPlan:
        """
        Crear un plan de ejecución dinámico inicial
        """
        logger.info(f"Creating dynamic plan for task: {task_id}")
        
        # Crear plan base usando TaskPlanner
        base_plan = self.create_execution_plan(task_id, user_input, context or {})
        
        # Inicializar contexto de ejecución
        execution_context = ExecutionContext(
            task_id=task_id,
            current_step=None,
            completed_steps=[],
            failed_steps=[],
            available_tools=context.get('available_tools', []) if context else [],
            execution_results={},
            performance_metrics={},
            user_feedback=[],
            environment_state=context.get('environment_state', {}) if context else {},
            resource_usage={}
        )
        
        # Guardar en estado interno
        self.active_plans[task_id] = base_plan
        self.execution_contexts[task_id] = execution_context
        self.plan_history[task_id] = []
        
        logger.info(f"Dynamic plan created for task {task_id} with {len(base_plan.steps)} steps")
        return base_plan
    
    async def update_execution_context(self, task_id: str, 
                                     step_id: str = None,
                                     step_result: Dict[str, Any] = None,
                                     step_failed: bool = False,
                                     user_feedback: str = None,
                                     environment_changes: Dict[str, Any] = None):
        """
        Actualizar contexto de ejecución y disparar re-planificación si es necesario
        """
        if task_id not in self.execution_contexts:
            logger.warning(f"Task {task_id} not found in execution contexts")
            return
        
        context = self.execution_contexts[task_id]
        
        # Actualizar contexto
        if step_id:
            context.current_step = step_id
            if step_failed:
                context.failed_steps.append(step_id)
            else:
                context.completed_steps.append(step_id)
        
        if step_result:
            context.execution_results[step_id] = step_result
        
        if user_feedback:
            context.user_feedback.append(user_feedback)
        
        if environment_changes:
            context.environment_state.update(environment_changes)
        
        # Verificar si necesitamos re-planificar
        should_replan = await self._should_replan(task_id, context)
        
        if should_replan:
            await self._trigger_replan(task_id, context)
    
    async def _should_replan(self, task_id: str, context: ExecutionContext) -> bool:
        """
        Determinar si se debe re-planificar basado en el contexto actual
        """
        # Verificar número máximo de re-planificaciones
        if len(self.plan_history[task_id]) >= self.max_replans_per_task:
            logger.info(f"Max replans reached for task {task_id}")
            return False
        
        # Verificar si hay pasos fallidos
        if context.failed_steps:
            logger.info(f"Failed steps detected for task {task_id}: {context.failed_steps}")
            return True
        
        # Verificar cambios significativos en el ambiente
        if self._detect_environment_changes(context):
            logger.info(f"Environment changes detected for task {task_id}")
            return True
        
        # Verificar feedback del usuario
        if context.user_feedback:
            logger.info(f"User feedback received for task {task_id}")
            return True
        
        # Verificar rendimiento
        if self._performance_requires_replan(context):
            logger.info(f"Performance issues detected for task {task_id}")
            return True
        
        return False
    
    def _detect_environment_changes(self, context: ExecutionContext) -> bool:
        """Detectar cambios significativos en el ambiente"""
        # Implementar lógica para detectar cambios de contexto
        # Por ahora, detectamos cambios básicos
        
        # Verificar cambios en herramientas disponibles
        current_tools = context.available_tools
        initial_tools = context.environment_state.get('initial_tools', [])
        
        if set(current_tools) != set(initial_tools):
            return True
        
        # Verificar cambios en recursos
        if context.resource_usage:
            avg_usage = sum(context.resource_usage.values()) / len(context.resource_usage)
            if avg_usage > 0.8:  # Uso alto de recursos
                return True
        
        return False
    
    def _performance_requires_replan(self, context: ExecutionContext) -> bool:
        """Verificar si el rendimiento requiere re-planificación"""
        if not context.performance_metrics:
            return False
        
        # Verificar tiempo de ejecución excesivo
        avg_step_time = context.performance_metrics.get('avg_step_time', 0)
        if avg_step_time > 300:  # 5 minutos por paso
            return True
        
        # Verificar tasa de éxito baja
        success_rate = context.performance_metrics.get('success_rate', 1.0)
        if success_rate < 0.7:  # Menos del 70% de éxito
            return True
        
        return False
    
    async def _trigger_replan(self, task_id: str, context: ExecutionContext):
        """
        Disparar re-planificación automática
        """
        logger.info(f"Triggering replan for task {task_id}")
        
        # Determinar razón de la re-planificación
        reason = self._determine_replan_reason(context)
        
        # Generar nuevo plan
        new_plan = await self._generate_adapted_plan(task_id, context, reason)
        
        # Calcular cambios
        plan_change = self._calculate_plan_changes(task_id, new_plan, reason)
        
        # Actualizar plan activo
        self.active_plans[task_id] = new_plan
        self.plan_history[task_id].append(plan_change)
        
        # Notificar cambios
        if self.plan_update_callback:
            await self._notify_plan_update(task_id, new_plan, plan_change)
        
        logger.info(f"Replan completed for task {task_id}: {reason.value}")
    
    def _determine_replan_reason(self, context: ExecutionContext) -> ReplanReason:
        """Determinar la razón principal para re-planificar"""
        if context.failed_steps:
            return ReplanReason.STEP_FAILED
        
        if context.user_feedback:
            return ReplanReason.USER_FEEDBACK
        
        if self._detect_environment_changes(context):
            return ReplanReason.CONTEXT_CHANGED
        
        if self._performance_requires_replan(context):
            return ReplanReason.PERFORMANCE_OPTIMIZATION
        
        return ReplanReason.NEW_REQUIREMENTS
    
    async def _generate_adapted_plan(self, task_id: str, context: ExecutionContext, 
                                   reason: ReplanReason) -> ExecutionPlan:
        """
        Generar un plan adaptado basado en el contexto y razón
        """
        current_plan = self.active_plans[task_id]
        
        # Crear copia del plan actual
        adapted_steps = []
        
        for step in current_plan.steps:
            # Mantener pasos completados
            if step.id in context.completed_steps:
                adapted_steps.append(step)
                continue
            
            # Saltear pasos fallidos y crear alternativas
            if step.id in context.failed_steps:
                alternative_steps = self._create_alternative_steps(step, context, reason)
                adapted_steps.extend(alternative_steps)
                continue
            
            # Optimizar pasos pendientes
            if step.id not in context.completed_steps:
                optimized_step = self._optimize_step(step, context, reason)
                adapted_steps.append(optimized_step)
        
        # Agregar pasos adicionales si es necesario
        additional_steps = self._generate_additional_steps(context, reason)
        adapted_steps.extend(additional_steps)
        
        # Crear nuevo plan
        adapted_plan = ExecutionPlan(
            task_id=task_id,
            title=current_plan.title,
            steps=adapted_steps,
            total_estimated_duration=sum(step.estimated_duration for step in adapted_steps),
            complexity_score=self._calculate_complexity_score(adapted_steps),
            required_tools=list(set(step.tool for step in adapted_steps)),
            success_probability=self._calculate_success_probability(adapted_steps, context),
            risk_factors=self._identify_risk_factors(adapted_steps, context),
            prerequisites=current_plan.prerequisites
        )
        
        return adapted_plan
    
    def _create_alternative_steps(self, failed_step: TaskStep, context: ExecutionContext, 
                                reason: ReplanReason) -> List[TaskStep]:
        """Crear pasos alternativos para un paso fallido"""
        alternatives = []
        
        # Crear paso alternativo básico
        alt_step = TaskStep(
            id=f"{failed_step.id}_alt",
            title=f"Alternativa: {failed_step.title}",
            description=f"Enfoque alternativo para: {failed_step.description}",
            tool=failed_step.tool,
            parameters=failed_step.parameters.copy(),
            dependencies=failed_step.dependencies,
            estimated_duration=failed_step.estimated_duration * 1.2,  # 20% más tiempo
            complexity='medium',
            required_skills=failed_step.required_skills
        )
        
        # Agregar paso de diagnóstico si es necesario
        if reason == ReplanReason.STEP_FAILED:
            diagnostic_step = TaskStep(
                id=f"{failed_step.id}_diagnosis",
                title=f"Diagnóstico: {failed_step.title}",
                description=f"Analizar por qué falló: {failed_step.description}",
                tool="diagnosis",
                parameters={"failed_step": failed_step.id},
                dependencies=[],
                estimated_duration=60,
                complexity='low',
                required_skills=['troubleshooting']
            )
            alternatives.append(diagnostic_step)
        
        alternatives.append(alt_step)
        return alternatives
    
    def _optimize_step(self, step: TaskStep, context: ExecutionContext, 
                      reason: ReplanReason) -> TaskStep:
        """Optimizar un paso basado en el contexto"""
        optimized_step = TaskStep(
            id=step.id,
            title=step.title,
            description=step.description,
            tool=step.tool,
            parameters=step.parameters.copy(),
            dependencies=step.dependencies,
            estimated_duration=step.estimated_duration,
            complexity=step.complexity,
            required_skills=step.required_skills
        )
        
        # Optimizar según la razón
        if reason == ReplanReason.PERFORMANCE_OPTIMIZATION:
            # Reducir tiempo estimado si es posible
            optimized_step.estimated_duration = int(step.estimated_duration * 0.8)
            
            # Simplificar parámetros si es posible
            optimized_step.parameters = self._simplify_parameters(step.parameters)
        
        elif reason == ReplanReason.CONTEXT_CHANGED:
            # Adaptar herramientas disponibles
            if step.tool not in context.available_tools and context.available_tools:
                optimized_step.tool = context.available_tools[0]
        
        return optimized_step
    
    def _generate_additional_steps(self, context: ExecutionContext, 
                                 reason: ReplanReason) -> List[TaskStep]:
        """Generar pasos adicionales según el contexto"""
        additional_steps = []
        
        # Agregar paso de verificación si hay muchos fallos
        if len(context.failed_steps) > 2:
            verification_step = TaskStep(
                id=f"verify_{len(context.failed_steps)}",
                title="Verificación de Estado",
                description="Verificar estado del sistema antes de continuar",
                tool="verification",
                parameters={"check_type": "system_health"},
                dependencies=[],
                estimated_duration=30,
                complexity='low',
                required_skills=['verification']
            )
            additional_steps.append(verification_step)
        
        # Agregar paso de optimización si hay problemas de rendimiento
        if reason == ReplanReason.PERFORMANCE_OPTIMIZATION:
            optimization_step = TaskStep(
                id=f"optimize_{datetime.now().strftime('%H%M%S')}",
                title="Optimización de Rendimiento",
                description="Optimizar configuración para mejor rendimiento",
                tool="optimizer",
                parameters={"optimization_type": "performance"},
                dependencies=[],
                estimated_duration=90,
                complexity='medium',
                required_skills=['optimization']
            )
            additional_steps.append(optimization_step)
        
        return additional_steps
    
    def _calculate_plan_changes(self, task_id: str, new_plan: ExecutionPlan, 
                              reason: ReplanReason) -> PlanChange:
        """Calcular cambios entre plan actual y nuevo plan"""
        current_plan = self.active_plans[task_id]
        
        # Identificar cambios
        current_step_ids = {step.id for step in current_plan.steps}
        new_step_ids = {step.id for step in new_plan.steps}
        
        added_steps = [step for step in new_plan.steps if step.id not in current_step_ids]
        removed_step_ids = list(current_step_ids - new_step_ids)
        
        # Encontrar pasos modificados
        modified_steps = []
        for new_step in new_plan.steps:
            if new_step.id in current_step_ids:
                current_step = next(s for s in current_plan.steps if s.id == new_step.id)
                if self._step_changed(current_step, new_step):
                    modified_steps.append(new_step)
        
        # Calcular impacto
        total_steps = len(current_plan.steps)
        changes_count = len(added_steps) + len(removed_step_ids) + len(modified_steps)
        impact_score = min(changes_count / total_steps, 1.0) if total_steps > 0 else 0.0
        
        return PlanChange(
            change_id=f"change_{task_id}_{len(self.plan_history[task_id]) + 1}",
            timestamp=datetime.now(),
            reason=reason,
            description=f"Plan actualizado: {reason.value}",
            steps_added=added_steps,
            steps_removed=removed_step_ids,
            steps_modified=modified_steps,
            impact_score=impact_score,
            confidence=0.85  # Confianza base del 85%
        )
    
    def _step_changed(self, old_step: TaskStep, new_step: TaskStep) -> bool:
        """Verificar si un paso ha cambiado"""
        return (old_step.title != new_step.title or
                old_step.description != new_step.description or
                old_step.tool != new_step.tool or
                old_step.parameters != new_step.parameters or
                old_step.estimated_duration != new_step.estimated_duration)
    
    async def _notify_plan_update(self, task_id: str, new_plan: ExecutionPlan, 
                                 plan_change: PlanChange):
        """Notificar actualización del plan"""
        if self.plan_update_callback:
            try:
                await self.plan_update_callback({
                    'task_id': task_id,
                    'new_plan': asdict(new_plan),
                    'plan_change': asdict(plan_change),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error notifying plan update: {e}")
    
    def _calculate_complexity_score(self, steps: List[TaskStep]) -> float:
        """Calcular puntuación de complejidad del plan"""
        if not steps:
            return 0.0
        
        complexity_weights = {'low': 1, 'medium': 2, 'high': 3}
        total_complexity = sum(complexity_weights.get(step.complexity, 2) for step in steps)
        max_complexity = len(steps) * 3
        
        return total_complexity / max_complexity
    
    def _calculate_success_probability(self, steps: List[TaskStep], 
                                     context: ExecutionContext) -> float:
        """Calcular probabilidad de éxito del plan"""
        if not steps:
            return 1.0
        
        # Probabilidad base por complejidad
        complexity_prob = {
            'low': 0.95,
            'medium': 0.85,
            'high': 0.75
        }
        
        step_probs = [complexity_prob.get(step.complexity, 0.85) for step in steps]
        
        # Ajustar por historial de fallos
        if context.failed_steps:
            failure_rate = len(context.failed_steps) / (len(context.completed_steps) + len(context.failed_steps))
            adjustment = 1.0 - (failure_rate * 0.3)
            step_probs = [prob * adjustment for prob in step_probs]
        
        # Calcular probabilidad total (multiplicativa)
        total_prob = 1.0
        for prob in step_probs:
            total_prob *= prob
        
        return max(total_prob, 0.1)  # Mínimo 10% de probabilidad
    
    def _identify_risk_factors(self, steps: List[TaskStep], 
                              context: ExecutionContext) -> List[str]:
        """Identificar factores de riesgo del plan"""
        risks = []
        
        # Riesgo por complejidad alta
        high_complexity_steps = [s for s in steps if s.complexity == 'high']
        if len(high_complexity_steps) > len(steps) * 0.5:
            risks.append("Alta proporción de pasos complejos")
        
        # Riesgo por dependencias
        dependency_count = sum(len(step.dependencies) for step in steps)
        if dependency_count > len(steps) * 1.5:
            risks.append("Muchas dependencias entre pasos")
        
        # Riesgo por historial de fallos
        if len(context.failed_steps) > 2:
            risks.append("Historial de fallos previos")
        
        # Riesgo por duración
        total_duration = sum(step.estimated_duration for step in steps)
        if total_duration > 3600:  # Más de 1 hora
            risks.append("Duración estimada muy larga")
        
        return risks
    
    def _simplify_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simplificar parámetros para optimización"""
        simplified = parameters.copy()
        
        # Reducir valores numéricos si es posible
        for key, value in simplified.items():
            if isinstance(value, int) and value > 10:
                simplified[key] = max(int(value * 0.8), 1)
            elif isinstance(value, float) and value > 1.0:
                simplified[key] = max(value * 0.8, 0.1)
        
        return simplified
    
    def get_plan_status(self, task_id: str) -> Dict[str, Any]:
        """Obtener estado actual del plan"""
        if task_id not in self.active_plans:
            return {'error': 'Task not found'}
        
        plan = self.active_plans[task_id]
        context = self.execution_contexts[task_id]
        
        return {
            'task_id': task_id,
            'plan': asdict(plan),
            'context': asdict(context),
            'plan_changes': [asdict(change) for change in self.plan_history[task_id]],
            'total_replans': len(self.plan_history[task_id]),
            'current_step': context.current_step,
            'progress': len(context.completed_steps) / len(plan.steps) if plan.steps else 0
        }
    
    def cleanup_task(self, task_id: str):
        """Limpiar recursos de una tarea completada"""
        if task_id in self.active_plans:
            del self.active_plans[task_id]
        if task_id in self.execution_contexts:
            del self.execution_contexts[task_id]
        if task_id in self.plan_history:
            del self.plan_history[task_id]
        
        logger.info(f"Cleaned up resources for task {task_id}")

# Instancia global
dynamic_task_planner = DynamicTaskPlanner()

def get_dynamic_task_planner() -> DynamicTaskPlanner:
    """Obtener instancia global del planificador dinámico"""
    return dynamic_task_planner