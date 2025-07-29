"""
Motor de planificación jerárquica para Mitosis
Implementa capacidades avanzadas de descomposición y planificación de tareas
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

from .planning_algorithms import PlanningAlgorithms, ExecutionPlan, TaskStep, PlanningStrategy

logger = logging.getLogger(__name__)

@dataclass
class PlanningContext:
    """Contexto para la planificación de tareas"""
    user_id: str
    session_id: str
    task_history: List[Dict[str, Any]]
    available_resources: Dict[str, Any]
    constraints: Dict[str, Any]
    preferences: Dict[str, Any]

class HierarchicalPlanningEngine:
    """Motor de planificación jerárquica avanzado"""
    
    def __init__(self, llm_service=None, tool_manager=None, memory_manager=None):
        self.llm_service = llm_service
        self.tool_manager = tool_manager
        self.memory_manager = memory_manager
        self.planning_algorithms = PlanningAlgorithms(llm_service)
        
        # Cache de planes para optimización
        self.plan_cache = {}
        
        # Métricas de planificación
        self.planning_metrics = {
            "plans_generated": 0,
            "plans_executed": 0,
            "success_rate": 0.0,
            "avg_planning_time": 0.0
        }
        
        # Configuración de planificación
        self.config = {
            "max_depth": 5,
            "max_steps_per_level": 10,
            "enable_caching": True,
            "enable_optimization": True,
            "enable_learning": True,
            "parallel_planning": True
        }
    
    async def create_plan(self, task_description: str, context: PlanningContext,
                         available_tools: List[str]) -> ExecutionPlan:
        """Crea un plan de ejecución jerárquico para una tarea"""
        
        start_time = time.time()
        
        try:
            logger.info(f"Iniciando planificación jerárquica para: {task_description}")
            
            # 1. Verificar cache si está habilitado
            if self.config["enable_caching"]:
                cached_plan = await self._check_plan_cache(task_description, available_tools)
                if cached_plan:
                    logger.info("Plan recuperado desde cache")
                    return cached_plan
            
            # 2. Analizar el contexto y requerimientos
            analysis_result = await self._analyze_task_requirements(
                task_description, context, available_tools
            )
            
            # 3. Generar plan jerárquico
            plan = await self._generate_hierarchical_plan(
                task_description, analysis_result, available_tools, context
            )
            
            # 4. Optimizar el plan si está habilitado
            if self.config["enable_optimization"]:
                plan = await self._optimize_plan(plan, context)
            
            # 5. Validar el plan
            validation_result = await self._validate_plan(plan, available_tools)
            if not validation_result["valid"]:
                logger.warning(f"Plan inválido: {validation_result['errors']}")
                plan = await self._fix_plan_issues(plan, validation_result["errors"])
            
            # 6. Cachear el plan
            if self.config["enable_caching"]:
                await self._cache_plan(task_description, plan, available_tools)
            
            # 7. Actualizar métricas
            self._update_planning_metrics(time.time() - start_time, True)
            
            logger.info(f"Plan generado exitosamente: {len(plan.steps)} pasos, "
                       f"duración estimada: {plan.total_estimated_duration}s")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error en planificación jerárquica: {e}")
            self._update_planning_metrics(time.time() - start_time, False)
            
            # Generar plan de fallback
            return await self._generate_fallback_plan(task_description, available_tools)
    
    async def _analyze_task_requirements(self, task_description: str, 
                                       context: PlanningContext,
                                       available_tools: List[str]) -> Dict[str, Any]:
        """Analiza los requerimientos de la tarea"""
        
        # Análisis básico de la tarea
        analysis = {
            "task_type": self._classify_task_type(task_description),
            "complexity_level": self._assess_task_complexity(task_description),
            "required_resources": self._identify_required_resources(task_description),
            "time_constraints": self._extract_time_constraints(task_description),
            "dependencies": self._identify_dependencies(task_description),
            "parallel_opportunities": self._identify_parallel_opportunities(task_description)
        }
        
        # Análisis de contexto
        if context.task_history:
            analysis["historical_patterns"] = self._analyze_historical_patterns(
                context.task_history, task_description
            )
        
        # Análisis de recursos disponibles
        analysis["resource_availability"] = self._analyze_resource_availability(
            available_tools, context.available_resources
        )
        
        # Análisis de restricciones
        analysis["constraints"] = self._analyze_constraints(
            context.constraints, task_description
        )
        
        return analysis
    
    async def _generate_hierarchical_plan(self, task_description: str, 
                                        analysis: Dict[str, Any],
                                        available_tools: List[str],
                                        context: PlanningContext) -> ExecutionPlan:
        """Genera un plan jerárquico basado en el análisis"""
        
        # Determinar estrategia de planificación
        strategy = self._select_planning_strategy(analysis)
        
        # Generar plan usando algoritmos apropiados
        plan = await self.planning_algorithms.decompose_task(
            task_description, 
            {
                "analysis": analysis,
                "context": context,
                "strategy": strategy
            },
            available_tools
        )
        
        # Agregar información jerárquica
        plan = await self._add_hierarchical_structure(plan, analysis)
        
        return plan
    
    async def _add_hierarchical_structure(self, plan: ExecutionPlan, 
                                        analysis: Dict[str, Any]) -> ExecutionPlan:
        """Agrega estructura jerárquica al plan"""
        
        # Organizar pasos en niveles jerárquicos
        hierarchical_steps = []
        current_level = 0
        
        for step in plan.steps:
            # Calcular nivel jerárquico basado en dependencias
            level = self._calculate_hierarchy_level(step, plan.steps)
            
            # Agregar metadatos jerárquicos
            step.metadata = getattr(step, 'metadata', {})
            step.metadata.update({
                "hierarchy_level": level,
                "parent_steps": self._find_parent_steps(step, plan.steps),
                "child_steps": self._find_child_steps(step, plan.steps),
                "criticality": self._calculate_step_criticality(step, plan.steps)
            })
            
            hierarchical_steps.append(step)
        
        # Actualizar plan con estructura jerárquica
        plan.steps = hierarchical_steps
        plan.metadata.update({
            "hierarchy_levels": max(step.metadata.get("hierarchy_level", 0) for step in hierarchical_steps) + 1,
            "critical_path": self._identify_critical_path(hierarchical_steps),
            "parallel_branches": self._identify_parallel_branches(hierarchical_steps)
        })
        
        return plan
    
    async def _optimize_plan(self, plan: ExecutionPlan, context: PlanningContext) -> ExecutionPlan:
        """Optimiza el plan para mejorar eficiencia"""
        
        logger.info("Optimizando plan de ejecución")
        
        # 1. Optimización de secuencia
        optimized_steps = await self._optimize_step_sequence(plan.steps, context)
        
        # 2. Optimización de recursos
        optimized_steps = await self._optimize_resource_usage(optimized_steps, context)
        
        # 3. Optimización de paralelización
        optimized_steps = await self._optimize_parallelization(optimized_steps)
        
        # 4. Optimización de tiempo
        optimized_steps = await self._optimize_timing(optimized_steps)
        
        # Actualizar plan con pasos optimizados
        plan.steps = optimized_steps
        
        # Recalcular métricas
        plan.total_estimated_duration = sum(step.estimated_duration for step in optimized_steps)
        plan.complexity_score = self._recalculate_complexity(optimized_steps)
        plan.success_probability = self._recalculate_success_probability(optimized_steps)
        
        return plan
    
    async def _validate_plan(self, plan: ExecutionPlan, available_tools: List[str]) -> Dict[str, Any]:
        """Valida que el plan sea ejecutable"""
        
        errors = []
        warnings = []
        
        # Validar herramientas disponibles
        for step in plan.steps:
            if step.tool not in available_tools:
                errors.append(f"Herramienta no disponible: {step.tool} en paso {step.id}")
        
        # Validar dependencias
        step_ids = {step.id for step in plan.steps}
        for step in plan.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    errors.append(f"Dependencia no encontrada: {dep} en paso {step.id}")
        
        # Validar ciclos en dependencias
        if self._has_dependency_cycles(plan.steps):
            errors.append("Ciclos detectados en dependencias")
        
        # Validar tiempos estimados
        for step in plan.steps:
            if step.estimated_duration <= 0:
                warnings.append(f"Duración inválida en paso {step.id}")
        
        # Validar complejidad
        if plan.complexity_score > 1.0:
            warnings.append("Complejidad del plan muy alta")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _fix_plan_issues(self, plan: ExecutionPlan, errors: List[str]) -> ExecutionPlan:
        """Corrige problemas en el plan"""
        
        logger.info(f"Corrigiendo {len(errors)} problemas en el plan")
        
        # Corregir herramientas no disponibles
        available_tools = self.tool_manager.get_available_tools() if self.tool_manager else []
        available_tool_names = [tool.get("name", "") for tool in available_tools]
        
        for step in plan.steps:
            if step.tool not in available_tool_names:
                alternative = self._find_alternative_tool(step.tool, available_tool_names)
                if alternative:
                    step.tool = alternative
                    logger.info(f"Herramienta {step.tool} reemplazada por {alternative}")
        
        # Corregir dependencias inválidas
        valid_step_ids = {step.id for step in plan.steps}
        for step in plan.steps:
            step.dependencies = [dep for dep in step.dependencies if dep in valid_step_ids]
        
        # Corregir ciclos en dependencias
        if self._has_dependency_cycles(plan.steps):
            plan.steps = self._remove_dependency_cycles(plan.steps)
        
        return plan
    
    async def _check_plan_cache(self, task_description: str, available_tools: List[str]) -> Optional[ExecutionPlan]:
        """Verifica si existe un plan en cache"""
        
        cache_key = self._generate_cache_key(task_description, available_tools)
        
        if cache_key in self.plan_cache:
            cached_entry = self.plan_cache[cache_key]
            
            # Verificar si el cache no ha expirado (1 hora)
            if time.time() - cached_entry["timestamp"] < 3600:
                return cached_entry["plan"]
        
        return None
    
    async def _cache_plan(self, task_description: str, plan: ExecutionPlan, available_tools: List[str]):
        """Cachea un plan para uso futuro"""
        
        cache_key = self._generate_cache_key(task_description, available_tools)
        
        self.plan_cache[cache_key] = {
            "plan": plan,
            "timestamp": time.time()
        }
        
        # Limpiar cache si está muy lleno
        if len(self.plan_cache) > 100:
            await self._cleanup_cache()
    
    async def _cleanup_cache(self):
        """Limpia el cache de planes"""
        
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.plan_cache.items():
            if current_time - entry["timestamp"] > 3600:  # 1 hora
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.plan_cache[key]
    
    def _generate_cache_key(self, task_description: str, available_tools: List[str]) -> str:
        """Genera una clave única para el cache"""
        
        import hashlib
        
        content = f"{task_description}:{sorted(available_tools)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _classify_task_type(self, task_description: str) -> str:
        """Clasifica el tipo de tarea"""
        
        task_lower = task_description.lower()
        
        # Mapeo de palabras clave a tipos de tarea
        task_types = {
            "research": ["investigar", "buscar", "analizar", "research", "información", "datos"],
            "creation": ["crear", "generar", "desarrollar", "construir", "diseñar", "producir"],
            "analysis": ["analizar", "examinar", "evaluar", "procesar", "revisar", "estudiar"],
            "automation": ["automatizar", "programar", "configurar", "setup", "instalar"],
            "communication": ["enviar", "comunicar", "notificar", "compartir", "publicar"],
            "management": ["gestionar", "administrar", "organizar", "coordinar", "supervisar"]
        }
        
        for task_type, keywords in task_types.items():
            if any(keyword in task_lower for keyword in keywords):
                return task_type
        
        return "general"
    
    def _assess_task_complexity(self, task_description: str) -> str:
        """Evalúa la complejidad de la tarea"""
        
        complexity_indicators = {
            "low": ["simple", "básico", "fácil", "rápido", "directo"],
            "medium": ["moderado", "normal", "estándar", "típico"],
            "high": ["complejo", "avanzado", "difícil", "extenso", "detallado", "comprehensivo"]
        }
        
        task_lower = task_description.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                return level
        
        # Evaluar por longitud y palabras
        words = task_lower.split()
        if len(words) < 5:
            return "low"
        elif len(words) < 15:
            return "medium"
        else:
            return "high"
    
    def _identify_required_resources(self, task_description: str) -> List[str]:
        """Identifica los recursos requeridos"""
        
        resource_keywords = {
            "web_access": ["web", "internet", "sitio", "página", "url", "buscar"],
            "file_system": ["archivo", "documento", "carpeta", "directorio", "guardar"],
            "computation": ["calcular", "procesar", "analizar", "ejecutar", "código"],
            "external_api": ["api", "servicio", "integración", "conexión", "datos externos"],
            "storage": ["almacenar", "guardar", "persistir", "base de datos", "memoria"]
        }
        
        task_lower = task_description.lower()
        required = []
        
        for resource, keywords in resource_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                required.append(resource)
        
        return required
    
    def _extract_time_constraints(self, task_description: str) -> Dict[str, Any]:
        """Extrae restricciones de tiempo"""
        
        import re
        
        constraints = {
            "deadline": None,
            "urgency": "normal",
            "max_duration": None
        }
        
        task_lower = task_description.lower()
        
        # Detectar urgencia
        if any(word in task_lower for word in ["urgente", "rápido", "inmediato", "asap"]):
            constraints["urgency"] = "high"
        elif any(word in task_lower for word in ["lento", "pausado", "cuando puedas"]):
            constraints["urgency"] = "low"
        
        # Detectar límites de tiempo
        time_patterns = [
            r"en (\d+) (minutos?|horas?|días?)",
            r"antes de (\d+) (minutos?|horas?|días?)",
            r"máximo (\d+) (minutos?|horas?|días?)"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, task_lower)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                
                # Convertir a segundos
                multipliers = {
                    "minuto": 60, "minutos": 60,
                    "hora": 3600, "horas": 3600,
                    "día": 86400, "días": 86400
                }
                
                if unit in multipliers:
                    constraints["max_duration"] = amount * multipliers[unit]
                    break
        
        return constraints
    
    def _identify_dependencies(self, task_description: str) -> List[str]:
        """Identifica dependencias de la tarea"""
        
        dependencies = []
        task_lower = task_description.lower()
        
        # Detectar dependencias comunes
        dependency_patterns = {
            "file_dependency": ["usando", "con el archivo", "del documento", "desde el archivo"],
            "data_dependency": ["con los datos", "usando la información", "basado en"],
            "service_dependency": ["conectar con", "acceder a", "usar el servicio"],
            "previous_task": ["después de", "una vez que", "cuando termine"]
        }
        
        for dep_type, patterns in dependency_patterns.items():
            if any(pattern in task_lower for pattern in patterns):
                dependencies.append(dep_type)
        
        return dependencies
    
    def _identify_parallel_opportunities(self, task_description: str) -> List[str]:
        """Identifica oportunidades de paralelización"""
        
        opportunities = []
        task_lower = task_description.lower()
        
        # Detectar tareas que pueden paralelizarse
        parallel_indicators = {
            "multiple_sources": ["varias fuentes", "múltiples", "diferentes sitios"],
            "batch_processing": ["todos los", "cada uno", "en lote", "masivo"],
            "independent_tasks": ["independiente", "por separado", "simultáneo"],
            "concurrent_operations": ["al mismo tiempo", "concurrente", "paralelo"]
        }
        
        for opportunity, indicators in parallel_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                opportunities.append(opportunity)
        
        return opportunities
    
    def _analyze_historical_patterns(self, task_history: List[Dict[str, Any]], 
                                   current_task: str) -> Dict[str, Any]:
        """Analiza patrones históricos de tareas similares"""
        
        patterns = {
            "similar_tasks": [],
            "success_rate": 0.0,
            "avg_duration": 0.0,
            "common_issues": [],
            "recommended_tools": []
        }
        
        # Buscar tareas similares
        for task in task_history:
            similarity = self._calculate_task_similarity(current_task, task.get("description", ""))
            if similarity > 0.7:  # 70% similitud
                patterns["similar_tasks"].append({
                    "task": task,
                    "similarity": similarity
                })
        
        # Calcular métricas
        if patterns["similar_tasks"]:
            successful_tasks = [t for t in patterns["similar_tasks"] 
                             if t["task"].get("status") == "completed"]
            patterns["success_rate"] = len(successful_tasks) / len(patterns["similar_tasks"])
            
            durations = [t["task"].get("duration", 0) for t in successful_tasks]
            patterns["avg_duration"] = sum(durations) / len(durations) if durations else 0
        
        return patterns
    
    def _calculate_task_similarity(self, task1: str, task2: str) -> float:
        """Calcula similitud entre dos tareas"""
        
        # Implementación simple basada en palabras comunes
        words1 = set(task1.lower().split())
        words2 = set(task2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _analyze_resource_availability(self, available_tools: List[str], 
                                     available_resources: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza disponibilidad de recursos"""
        
        analysis = {
            "tool_count": len(available_tools),
            "tool_categories": self._categorize_tools(available_tools),
            "resource_constraints": self._identify_resource_constraints(available_resources),
            "capability_gaps": self._identify_capability_gaps(available_tools)
        }
        
        return analysis
    
    def _categorize_tools(self, tools: List[str]) -> Dict[str, List[str]]:
        """Categoriza herramientas disponibles"""
        
        categories = {
            "search": [],
            "analysis": [],
            "automation": [],
            "file_management": [],
            "communication": [],
            "development": []
        }
        
        tool_categories = {
            "search": ["web_search", "deep_research", "comprehensive_research"],
            "analysis": ["deep_research", "comprehensive_research"],
            "automation": ["shell", "playwright", "qstash"],
            "file_management": ["file_manager"],
            "communication": ["email", "notification"],
            "development": ["shell", "container_manager"]
        }
        
        for tool in tools:
            for category, category_tools in tool_categories.items():
                if tool in category_tools:
                    categories[category].append(tool)
        
        return categories
    
    def _identify_resource_constraints(self, available_resources: Dict[str, Any]) -> List[str]:
        """Identifica restricciones de recursos"""
        
        constraints = []
        
        # Verificar limitaciones comunes
        if available_resources.get("memory_limit", 0) < 1000:  # MB
            constraints.append("limited_memory")
        
        if available_resources.get("cpu_cores", 0) < 2:
            constraints.append("limited_cpu")
        
        if not available_resources.get("internet_access", True):
            constraints.append("no_internet")
        
        if available_resources.get("storage_space", 0) < 1000:  # MB
            constraints.append("limited_storage")
        
        return constraints
    
    def _identify_capability_gaps(self, available_tools: List[str]) -> List[str]:
        """Identifica gaps en capacidades"""
        
        essential_capabilities = {
            "web_browsing": ["web_search", "playwright"],
            "file_operations": ["file_manager"],
            "system_commands": ["shell"],
            "research": ["deep_research", "comprehensive_research"],
            "automation": ["shell", "playwright"]
        }
        
        gaps = []
        
        for capability, required_tools in essential_capabilities.items():
            if not any(tool in available_tools for tool in required_tools):
                gaps.append(capability)
        
        return gaps
    
    def _analyze_constraints(self, constraints: Dict[str, Any], task_description: str) -> Dict[str, Any]:
        """Analiza restricciones del contexto"""
        
        analysis = {
            "time_constraints": constraints.get("time_limit", None),
            "resource_constraints": constraints.get("resource_limits", {}),
            "security_constraints": constraints.get("security_level", "normal"),
            "compliance_requirements": constraints.get("compliance", []),
            "user_preferences": constraints.get("preferences", {})
        }
        
        return analysis
    
    def _select_planning_strategy(self, analysis: Dict[str, Any]) -> PlanningStrategy:
        """Selecciona la estrategia de planificación más apropiada"""
        
        task_type = analysis.get("task_type", "general")
        complexity = analysis.get("complexity_level", "medium")
        parallel_opportunities = analysis.get("parallel_opportunities", [])
        
        # Lógica de selección de estrategia
        if len(parallel_opportunities) > 2:
            return PlanningStrategy.PARALLEL
        elif complexity == "high":
            return PlanningStrategy.HIERARCHICAL
        elif task_type in ["automation", "analysis"]:
            return PlanningStrategy.ADAPTIVE
        elif complexity == "low":
            return PlanningStrategy.SEQUENTIAL
        else:
            return PlanningStrategy.GOAL_ORIENTED
    
    async def _optimize_step_sequence(self, steps: List[TaskStep], context: PlanningContext) -> List[TaskStep]:
        """Optimiza la secuencia de pasos"""
        
        # Reordenar pasos para optimizar eficiencia
        optimized_steps = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            # Buscar próximo paso que se puede ejecutar
            next_step = None
            for step in remaining_steps:
                if all(dep_id in [s.id for s in optimized_steps] for dep_id in step.dependencies):
                    next_step = step
                    break
            
            if next_step:
                optimized_steps.append(next_step)
                remaining_steps.remove(next_step)
            else:
                # Si no hay próximo paso válido, agregar el primero disponible
                optimized_steps.append(remaining_steps.pop(0))
        
        return optimized_steps
    
    async def _optimize_resource_usage(self, steps: List[TaskStep], context: PlanningContext) -> List[TaskStep]:
        """Optimiza el uso de recursos"""
        
        # Balancear uso de herramientas
        tool_usage = {}
        for step in steps:
            tool_usage[step.tool] = tool_usage.get(step.tool, 0) + 1
        
        # Redistribuir si hay desequilibrio
        for step in steps:
            if tool_usage[step.tool] > 3:  # Muchos usos de la misma herramienta
                alternative = self._find_alternative_tool(step.tool, list(tool_usage.keys()))
                if alternative and tool_usage[alternative] < 2:
                    step.tool = alternative
                    tool_usage[step.tool] -= 1
                    tool_usage[alternative] += 1
        
        return steps
    
    async def _optimize_parallelization(self, steps: List[TaskStep]) -> List[TaskStep]:
        """Optimiza oportunidades de paralelización"""
        
        # Identificar pasos que pueden ejecutarse en paralelo
        for i, step in enumerate(steps):
            if step.can_parallelize:
                # Verificar si realmente puede paralelizarse
                for j, other_step in enumerate(steps):
                    if i != j and not self._steps_conflict(step, other_step):
                        # Remover dependencia si no es necesaria
                        if step.id in other_step.dependencies:
                            other_step.dependencies.remove(step.id)
        
        return steps
    
    async def _optimize_timing(self, steps: List[TaskStep]) -> List[TaskStep]:
        """Optimiza los tiempos de ejecución"""
        
        # Ajustar duraciones estimadas basado en complejidad
        for step in steps:
            if step.complexity < 0.3:
                step.estimated_duration = int(step.estimated_duration * 0.8)
            elif step.complexity > 0.7:
                step.estimated_duration = int(step.estimated_duration * 1.2)
        
        return steps
    
    def _steps_conflict(self, step1: TaskStep, step2: TaskStep) -> bool:
        """Determina si dos pasos tienen conflictos"""
        
        # Pasos que usan la misma herramienta pueden conflictuar
        if step1.tool == step2.tool:
            return True
        
        # Pasos que modifican los mismos recursos
        if (step1.parameters.get("file_path") == step2.parameters.get("file_path") and
            step1.parameters.get("file_path") is not None):
            return True
        
        return False
    
    def _calculate_hierarchy_level(self, step: TaskStep, all_steps: List[TaskStep]) -> int:
        """Calcula el nivel jerárquico de un paso"""
        
        if not step.dependencies:
            return 0
        
        max_parent_level = 0
        for dep_id in step.dependencies:
            parent_step = next((s for s in all_steps if s.id == dep_id), None)
            if parent_step:
                parent_level = self._calculate_hierarchy_level(parent_step, all_steps)
                max_parent_level = max(max_parent_level, parent_level)
        
        return max_parent_level + 1
    
    def _find_parent_steps(self, step: TaskStep, all_steps: List[TaskStep]) -> List[str]:
        """Encuentra los pasos padre de un paso"""
        
        return step.dependencies.copy()
    
    def _find_child_steps(self, step: TaskStep, all_steps: List[TaskStep]) -> List[str]:
        """Encuentra los pasos hijo de un paso"""
        
        children = []
        for other_step in all_steps:
            if step.id in other_step.dependencies:
                children.append(other_step.id)
        
        return children
    
    def _calculate_step_criticality(self, step: TaskStep, all_steps: List[TaskStep]) -> float:
        """Calcula la criticidad de un paso"""
        
        # Criticidad basada en dependencias
        dependents = len(self._find_child_steps(step, all_steps))
        dependency_factor = dependents / len(all_steps) if all_steps else 0
        
        # Criticidad basada en complejidad
        complexity_factor = step.complexity
        
        # Criticidad basada en duración
        total_duration = sum(s.estimated_duration for s in all_steps)
        duration_factor = step.estimated_duration / total_duration if total_duration > 0 else 0
        
        return (dependency_factor + complexity_factor + duration_factor) / 3
    
    def _identify_critical_path(self, steps: List[TaskStep]) -> List[str]:
        """Identifica la ruta crítica del plan"""
        
        # Implementación simple: pasos con mayor criticidad
        critical_steps = sorted(steps, 
                              key=lambda s: s.metadata.get("criticality", 0), 
                              reverse=True)
        
        return [step.id for step in critical_steps[:min(3, len(critical_steps))]]
    
    def _identify_parallel_branches(self, steps: List[TaskStep]) -> List[List[str]]:
        """Identifica ramas paralelas del plan"""
        
        branches = []
        processed = set()
        
        for step in steps:
            if step.id in processed or not step.can_parallelize:
                continue
            
            # Encontrar pasos que pueden ejecutarse en paralelo
            branch = [step.id]
            for other_step in steps:
                if (other_step.id != step.id and 
                    other_step.can_parallelize and 
                    other_step.id not in processed and
                    not self._steps_conflict(step, other_step)):
                    branch.append(other_step.id)
            
            if len(branch) > 1:
                branches.append(branch)
                processed.update(branch)
        
        return branches
    
    def _has_dependency_cycles(self, steps: List[TaskStep]) -> bool:
        """Detecta ciclos en las dependencias"""
        
        # Implementación simple de detección de ciclos
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id):
            if step_id in rec_stack:
                return True
            if step_id in visited:
                return False
            
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = next((s for s in steps if s.id == step_id), None)
            if step:
                for dep in step.dependencies:
                    if has_cycle(dep):
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        for step in steps:
            if step.id not in visited:
                if has_cycle(step.id):
                    return True
        
        return False
    
    def _remove_dependency_cycles(self, steps: List[TaskStep]) -> List[TaskStep]:
        """Remueve ciclos en las dependencias"""
        
        # Implementación simple: remover dependencias que causan ciclos
        for step in steps:
            safe_dependencies = []
            for dep in step.dependencies:
                # Verificar si agregar esta dependencia causa un ciclo
                test_step = TaskStep(
                    id=step.id,
                    title=step.title,
                    description=step.description,
                    tool=step.tool,
                    parameters=step.parameters,
                    dependencies=safe_dependencies + [dep],
                    estimated_duration=step.estimated_duration,
                    complexity=step.complexity,
                    priority=step.priority,
                    can_parallelize=step.can_parallelize
                )
                
                temp_steps = [s for s in steps if s.id != step.id] + [test_step]
                if not self._has_dependency_cycles(temp_steps):
                    safe_dependencies.append(dep)
            
            step.dependencies = safe_dependencies
        
        return steps
    
    def _find_alternative_tool(self, original_tool: str, available_tools: List[str]) -> Optional[str]:
        """Encuentra una herramienta alternativa"""
        
        alternatives = {
            "web_search": ["deep_research", "comprehensive_research", "tavily_search"],
            "deep_research": ["web_search", "comprehensive_research"],
            "comprehensive_research": ["deep_research", "web_search"],
            "shell": ["file_manager"],
            "file_manager": ["shell"],
            "playwright": ["web_search"],
            "tavily_search": ["web_search"]
        }
        
        for alt in alternatives.get(original_tool, []):
            if alt in available_tools:
                return alt
        
        return None
    
    def _recalculate_complexity(self, steps: List[TaskStep]) -> float:
        """Recalcula la complejidad del plan"""
        
        if not steps:
            return 0.0
        
        avg_complexity = sum(step.complexity for step in steps) / len(steps)
        dependency_factor = sum(len(step.dependencies) for step in steps) / len(steps)
        
        return min(avg_complexity + (dependency_factor * 0.1), 1.0)
    
    def _recalculate_success_probability(self, steps: List[TaskStep]) -> float:
        """Recalcula la probabilidad de éxito"""
        
        if not steps:
            return 0.0
        
        complexity = self._recalculate_complexity(steps)
        base_prob = 1.0 - (complexity * 0.3)
        
        # Ajustar por optimizaciones
        optimization_bonus = 0.1
        
        return max(base_prob + optimization_bonus, 0.1)
    
    def _update_planning_metrics(self, planning_time: float, success: bool):
        """Actualiza métricas de planificación"""
        
        self.planning_metrics["plans_generated"] += 1
        
        if success:
            self.planning_metrics["plans_executed"] += 1
        
        self.planning_metrics["success_rate"] = (
            self.planning_metrics["plans_executed"] / 
            self.planning_metrics["plans_generated"]
        )
        
        # Promedio móvil del tiempo de planificación
        current_avg = self.planning_metrics["avg_planning_time"]
        new_avg = (current_avg * 0.8) + (planning_time * 0.2)
        self.planning_metrics["avg_planning_time"] = new_avg
    
    async def _generate_fallback_plan(self, task_description: str, available_tools: List[str]) -> ExecutionPlan:
        """Genera un plan de fallback básico"""
        
        logger.info("Generando plan de fallback")
        
        # Plan simple de 3 pasos
        steps = [
            TaskStep(
                id="fallback_1",
                title="Inicialización",
                description=f"Inicializar {task_description}",
                tool=available_tools[0] if available_tools else "file_manager",
                parameters={"task": task_description},
                dependencies=[],
                estimated_duration=30,
                complexity=0.3,
                priority=3,
                can_parallelize=False
            ),
            TaskStep(
                id="fallback_2",
                title="Ejecución",
                description=f"Ejecutar {task_description}",
                tool=available_tools[1] if len(available_tools) > 1 else available_tools[0] if available_tools else "file_manager",
                parameters={"task": task_description},
                dependencies=["fallback_1"],
                estimated_duration=90,
                complexity=0.6,
                priority=2,
                can_parallelize=False
            ),
            TaskStep(
                id="fallback_3",
                title="Finalización",
                description=f"Finalizar {task_description}",
                tool="file_manager",
                parameters={"task": task_description},
                dependencies=["fallback_2"],
                estimated_duration=30,
                complexity=0.3,
                priority=1,
                can_parallelize=False
            )
        ]
        
        return ExecutionPlan(
            id=f"fallback_{int(time.time())}",
            title=f"Plan de fallback: {task_description}",
            description=f"Plan básico para {task_description}",
            steps=steps,
            total_estimated_duration=150,
            complexity_score=0.4,
            success_probability=0.7,
            strategy=PlanningStrategy.SEQUENTIAL,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "fallback": True,
                "total_steps": len(steps),
                "available_tools": available_tools
            }
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de planificación"""
        
        return self.planning_metrics.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """Actualiza la configuración del motor"""
        
        self.config.update(new_config)
        logger.info(f"Configuración actualizada: {new_config}")
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración actual"""
        
        return self.config.copy()