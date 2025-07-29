"""
Algoritmos de planificación para el motor de planificación jerárquica
Implementa diferentes estrategias de descomposición y optimización de tareas
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)

class PlanningStrategy(Enum):
    """Estrategias de planificación disponibles"""
    HIERARCHICAL = "hierarchical"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"
    GOAL_ORIENTED = "goal_oriented"

@dataclass
class TaskStep:
    """Representa un paso individual en el plan de ejecución"""
    id: str
    title: str
    description: str
    tool: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    estimated_duration: int
    complexity: float
    priority: int
    can_parallelize: bool
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class ExecutionPlan:
    """Plan de ejecución completo con metadatos"""
    id: str
    title: str
    description: str
    steps: List[TaskStep]
    total_estimated_duration: int
    complexity_score: float
    success_probability: float
    strategy: PlanningStrategy
    created_at: str
    metadata: Dict[str, Any]

class PlanningAlgorithms:
    """Algoritmos de planificación para descomposición de tareas"""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self.planning_strategies = {
            PlanningStrategy.HIERARCHICAL: self._hierarchical_planning,
            PlanningStrategy.SEQUENTIAL: self._sequential_planning,
            PlanningStrategy.PARALLEL: self._parallel_planning,
            PlanningStrategy.ADAPTIVE: self._adaptive_planning,
            PlanningStrategy.GOAL_ORIENTED: self._goal_oriented_planning
        }
        
        # Patrones de descomposición de tareas
        self.task_patterns = {
            "research": {
                "steps": ["analyze_query", "search_sources", "extract_information", "synthesize_results"],
                "tools": ["web_search", "deep_research", "comprehensive_research"],
                "parallel_capable": True
            },
            "analysis": {
                "steps": ["gather_data", "process_data", "analyze_patterns", "generate_insights"],
                "tools": ["file_manager", "web_search", "shell"],
                "parallel_capable": False
            },
            "development": {
                "steps": ["design_solution", "implement_code", "test_solution", "deploy_solution"],
                "tools": ["shell", "file_manager", "container_manager"],
                "parallel_capable": True
            },
            "automation": {
                "steps": ["identify_process", "design_automation", "implement_automation", "validate_automation"],
                "tools": ["shell", "playwright", "file_manager"],
                "parallel_capable": False
            }
        }
    
    async def decompose_task(self, task_description: str, context: Dict[str, Any], 
                           available_tools: List[str]) -> ExecutionPlan:
        """Descompone una tarea en pasos ejecutables"""
        
        # 1. Analizar la tarea para determinar el tipo y estrategia
        task_type = self._analyze_task_type(task_description)
        strategy = self._select_planning_strategy(task_type, context)
        
        logger.info(f"Descomponiendo tarea: {task_description}")
        logger.info(f"Tipo identificado: {task_type}, Estrategia: {strategy}")
        
        # 2. Aplicar algoritmo de planificación apropiado
        steps = await self.planning_strategies[strategy](
            task_description, task_type, available_tools, context
        )
        
        # 3. Optimizar el plan
        optimized_steps = await self._optimize_plan(steps, available_tools)
        
        # 4. Calcular métricas del plan
        total_duration = sum(step.estimated_duration for step in optimized_steps)
        complexity_score = self._calculate_complexity(optimized_steps)
        success_probability = self._calculate_success_probability(optimized_steps)
        
        # 5. Crear plan de ejecución
        plan = ExecutionPlan(
            id=f"plan_{int(time.time())}",
            title=task_description,
            description=f"Plan {strategy.value} para: {task_description}",
            steps=optimized_steps,
            total_estimated_duration=total_duration,
            complexity_score=complexity_score,
            success_probability=success_probability,
            strategy=strategy,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "task_type": task_type,
                "total_steps": len(optimized_steps),
                "parallel_steps": len([s for s in optimized_steps if s.can_parallelize]),
                "available_tools": available_tools
            }
        )
        
        return plan
    
    def _analyze_task_type(self, task_description: str) -> str:
        """Analiza el tipo de tarea basado en palabras clave"""
        
        task_lower = task_description.lower()
        
        # Patrones de investigación
        if any(word in task_lower for word in ["investigar", "buscar", "analizar", "research", "información"]):
            return "research"
        
        # Patrones de análisis
        if any(word in task_lower for word in ["analizar", "procesar", "evaluar", "examinar", "datos"]):
            return "analysis"
        
        # Patrones de desarrollo
        if any(word in task_lower for word in ["crear", "desarrollar", "programar", "código", "implementar"]):
            return "development"
        
        # Patrones de automatización
        if any(word in task_lower for word in ["automatizar", "script", "proceso", "repetir", "programar"]):
            return "automation"
        
        # Tipo general por defecto
        return "general"
    
    def _select_planning_strategy(self, task_type: str, context: Dict[str, Any]) -> PlanningStrategy:
        """Selecciona la estrategia de planificación más apropiada"""
        
        # Estrategias basadas en el tipo de tarea
        strategy_map = {
            "research": PlanningStrategy.PARALLEL,
            "analysis": PlanningStrategy.SEQUENTIAL,
            "development": PlanningStrategy.HIERARCHICAL,
            "automation": PlanningStrategy.ADAPTIVE,
            "general": PlanningStrategy.GOAL_ORIENTED
        }
        
        return strategy_map.get(task_type, PlanningStrategy.HIERARCHICAL)
    
    async def _hierarchical_planning(self, task_description: str, task_type: str, 
                                   available_tools: List[str], context: Dict[str, Any]) -> List[TaskStep]:
        """Planificación jerárquica con descomposición en niveles"""
        
        steps = []
        
        # Usar patrón si está disponible
        if task_type in self.task_patterns:
            pattern = self.task_patterns[task_type]
            
            for i, step_name in enumerate(pattern["steps"]):
                # Seleccionar herramienta más apropiada
                tool = self._select_best_tool(step_name, pattern["tools"], available_tools)
                
                step = TaskStep(
                    id=f"step_{i+1}",
                    title=step_name.replace("_", " ").title(),
                    description=f"Ejecutar {step_name} para {task_description}",
                    tool=tool,
                    parameters=self._generate_step_parameters(step_name, task_description, tool),
                    dependencies=[] if i == 0 else [f"step_{i}"],
                    estimated_duration=self._estimate_duration(step_name, tool),
                    complexity=self._estimate_complexity(step_name, tool),
                    priority=len(pattern["steps"]) - i,
                    can_parallelize=pattern["parallel_capable"] and i > 0
                )
                
                steps.append(step)
        
        else:
            # Planificación genérica usando LLM si está disponible
            if self.llm_service:
                steps = await self._llm_based_planning(task_description, available_tools)
            else:
                steps = await self._fallback_planning(task_description, available_tools)
        
        return steps
    
    async def _sequential_planning(self, task_description: str, task_type: str,
                                 available_tools: List[str], context: Dict[str, Any]) -> List[TaskStep]:
        """Planificación secuencial paso a paso"""
        
        # Crear pasos secuenciales básicos
        steps = [
            TaskStep(
                id="step_1",
                title="Preparación",
                description=f"Preparar recursos para: {task_description}",
                tool="file_manager",
                parameters={"action": "prepare", "context": task_description},
                dependencies=[],
                estimated_duration=30,
                complexity=0.2,
                priority=3,
                can_parallelize=False
            ),
            TaskStep(
                id="step_2", 
                title="Ejecución",
                description=f"Ejecutar tarea principal: {task_description}",
                tool=self._select_primary_tool(task_type, available_tools),
                parameters=self._generate_execution_parameters(task_description),
                dependencies=["step_1"],
                estimated_duration=120,
                complexity=0.7,
                priority=2,
                can_parallelize=False
            ),
            TaskStep(
                id="step_3",
                title="Finalización",
                description=f"Finalizar y reportar resultados de: {task_description}",
                tool="file_manager",
                parameters={"action": "finalize", "context": task_description},
                dependencies=["step_2"],
                estimated_duration=30,
                complexity=0.3,
                priority=1,
                can_parallelize=False
            )
        ]
        
        return steps
    
    async def _parallel_planning(self, task_description: str, task_type: str,
                               available_tools: List[str], context: Dict[str, Any]) -> List[TaskStep]:
        """Planificación paralela para tareas que pueden ejecutarse simultáneamente"""
        
        steps = []
        
        # Paso inicial de preparación
        prep_step = TaskStep(
            id="step_prep",
            title="Preparación",
            description=f"Preparar recursos para ejecución paralela: {task_description}",
            tool="file_manager",
            parameters={"action": "prepare_parallel", "context": task_description},
            dependencies=[],
            estimated_duration=20,
            complexity=0.2,
            priority=4,
            can_parallelize=False
        )
        steps.append(prep_step)
        
        # Pasos paralelos
        parallel_tools = ["web_search", "deep_research", "comprehensive_research"]
        available_parallel_tools = [t for t in parallel_tools if t in available_tools]
        
        for i, tool in enumerate(available_parallel_tools[:3]):  # Máximo 3 paralelos
            step = TaskStep(
                id=f"step_parallel_{i+1}",
                title=f"Ejecución Paralela {i+1}",
                description=f"Ejecutar {tool} para: {task_description}",
                tool=tool,
                parameters=self._generate_parallel_parameters(task_description, tool),
                dependencies=["step_prep"],
                estimated_duration=90,
                complexity=0.6,
                priority=3,
                can_parallelize=True
            )
            steps.append(step)
        
        # Paso de síntesis
        synthesis_step = TaskStep(
            id="step_synthesis",
            title="Síntesis",
            description=f"Sintetizar resultados paralelos: {task_description}",
            tool="file_manager",
            parameters={"action": "synthesize", "context": task_description},
            dependencies=[f"step_parallel_{i+1}" for i in range(len(available_parallel_tools))],
            estimated_duration=60,
            complexity=0.5,
            priority=2,
            can_parallelize=False
        )
        steps.append(synthesis_step)
        
        return steps
    
    async def _adaptive_planning(self, task_description: str, task_type: str,
                               available_tools: List[str], context: Dict[str, Any]) -> List[TaskStep]:
        """Planificación adaptativa que se ajusta dinámicamente"""
        
        # Comenzar con un plan básico que puede adaptarse
        steps = [
            TaskStep(
                id="step_adaptive_1",
                title="Análisis Inicial",
                description=f"Analizar requerimientos para: {task_description}",
                tool="web_search",
                parameters={"query": task_description, "analysis_mode": True},
                dependencies=[],
                estimated_duration=45,
                complexity=0.4,
                priority=3,
                can_parallelize=False
            ),
            TaskStep(
                id="step_adaptive_2",
                title="Ejecución Adaptativa",
                description=f"Ejecutar estrategia adaptativa para: {task_description}",
                tool=self._select_adaptive_tool(task_type, available_tools),
                parameters={"adaptive_mode": True, "context": task_description},
                dependencies=["step_adaptive_1"],
                estimated_duration=120,
                complexity=0.8,
                priority=2,
                can_parallelize=False
            ),
            TaskStep(
                id="step_adaptive_3",
                title="Validación y Ajuste",
                description=f"Validar resultados y ajustar si es necesario: {task_description}",
                tool="file_manager",
                parameters={"action": "validate", "adaptive": True},
                dependencies=["step_adaptive_2"],
                estimated_duration=30,
                complexity=0.3,
                priority=1,
                can_parallelize=False
            )
        ]
        
        return steps
    
    async def _goal_oriented_planning(self, task_description: str, task_type: str,
                                    available_tools: List[str], context: Dict[str, Any]) -> List[TaskStep]:
        """Planificación orientada a objetivos"""
        
        # Identificar objetivo principal
        main_goal = self._extract_main_goal(task_description)
        
        steps = [
            TaskStep(
                id="step_goal_1",
                title="Definición de Objetivo",
                description=f"Definir objetivo claro: {main_goal}",
                tool="file_manager",
                parameters={"action": "define_goal", "goal": main_goal},
                dependencies=[],
                estimated_duration=20,
                complexity=0.2,
                priority=4,
                can_parallelize=False
            ),
            TaskStep(
                id="step_goal_2",
                title="Estrategia de Cumplimiento",
                description=f"Desarrollar estrategia para cumplir: {main_goal}",
                tool=self._select_goal_tool(main_goal, available_tools),
                parameters={"goal_oriented": True, "target": main_goal},
                dependencies=["step_goal_1"],
                estimated_duration=90,
                complexity=0.6,
                priority=3,
                can_parallelize=False
            ),
            TaskStep(
                id="step_goal_3",
                title="Verificación de Objetivo",
                description=f"Verificar cumplimiento del objetivo: {main_goal}",
                tool="file_manager",
                parameters={"action": "verify_goal", "goal": main_goal},
                dependencies=["step_goal_2"],
                estimated_duration=30,
                complexity=0.4,
                priority=2,
                can_parallelize=False
            )
        ]
        
        return steps
    
    async def _llm_based_planning(self, task_description: str, available_tools: List[str]) -> List[TaskStep]:
        """Planificación asistida por LLM"""
        
        if not self.llm_service:
            return await self._fallback_planning(task_description, available_tools)
        
        # Prompt para generar plan detallado
        prompt = f"""
        Descompón la siguiente tarea en pasos específicos y ejecutables:
        
        Tarea: {task_description}
        Herramientas disponibles: {', '.join(available_tools)}
        
        Genera un plan con pasos detallados en formato JSON:
        {{
            "steps": [
                {{
                    "title": "Título del paso",
                    "description": "Descripción detallada",
                    "tool": "herramienta_a_usar",
                    "parameters": {{"param": "valor"}},
                    "estimated_duration": 60,
                    "complexity": 0.5,
                    "can_parallelize": false
                }}
            ]
        }}
        
        Reglas:
        - Máximo 5 pasos
        - Duración en segundos
        - Complejidad de 0.0 a 1.0
        - Usar solo herramientas disponibles
        """
        
        try:
            response = await self.llm_service.generate_response(prompt)
            plan_data = json.loads(response.get('response', '{}'))
            
            steps = []
            for i, step_data in enumerate(plan_data.get('steps', [])):
                step = TaskStep(
                    id=f"step_{i+1}",
                    title=step_data.get('title', f'Paso {i+1}'),
                    description=step_data.get('description', ''),
                    tool=step_data.get('tool', 'file_manager'),
                    parameters=step_data.get('parameters', {}),
                    dependencies=[] if i == 0 else [f"step_{i}"],
                    estimated_duration=step_data.get('estimated_duration', 60),
                    complexity=step_data.get('complexity', 0.5),
                    priority=len(plan_data.get('steps', [])) - i,
                    can_parallelize=step_data.get('can_parallelize', False)
                )
                steps.append(step)
            
            return steps
            
        except Exception as e:
            logger.error(f"Error en planificación LLM: {e}")
            return await self._fallback_planning(task_description, available_tools)
    
    async def _fallback_planning(self, task_description: str, available_tools: List[str]) -> List[TaskStep]:
        """Planificación de respaldo cuando no hay LLM disponible"""
        
        # Plan genérico básico
        primary_tool = available_tools[0] if available_tools else "file_manager"
        
        steps = [
            TaskStep(
                id="step_1",
                title="Inicialización",
                description=f"Inicializar proceso para: {task_description}",
                tool="file_manager",
                parameters={"action": "init", "task": task_description},
                dependencies=[],
                estimated_duration=30,
                complexity=0.2,
                priority=3,
                can_parallelize=False
            ),
            TaskStep(
                id="step_2",
                title="Procesamiento",
                description=f"Procesar tarea: {task_description}",
                tool=primary_tool,
                parameters={"task": task_description},
                dependencies=["step_1"],
                estimated_duration=90,
                complexity=0.6,
                priority=2,
                can_parallelize=False
            ),
            TaskStep(
                id="step_3",
                title="Finalización",
                description=f"Finalizar proceso: {task_description}",
                tool="file_manager",
                parameters={"action": "finalize", "task": task_description},
                dependencies=["step_2"],
                estimated_duration=30,
                complexity=0.3,
                priority=1,
                can_parallelize=False
            )
        ]
        
        return steps
    
    async def _optimize_plan(self, steps: List[TaskStep], available_tools: List[str]) -> List[TaskStep]:
        """Optimiza el plan para mejorar eficiencia"""
        
        # 1. Verificar disponibilidad de herramientas
        for step in steps:
            if step.tool not in available_tools:
                step.tool = self._find_alternative_tool(step.tool, available_tools)
        
        # 2. Optimizar dependencias
        optimized_steps = self._optimize_dependencies(steps)
        
        # 3. Balancear carga
        balanced_steps = self._balance_workload(optimized_steps)
        
        return balanced_steps
    
    def _optimize_dependencies(self, steps: List[TaskStep]) -> List[TaskStep]:
        """Optimiza las dependencias entre pasos"""
        
        # Identificar pasos que pueden ejecutarse en paralelo
        for i, step in enumerate(steps):
            if step.can_parallelize and i > 0:
                # Verificar si realmente necesita depender del paso anterior
                prev_step = steps[i-1]
                if not self._requires_dependency(step, prev_step):
                    step.dependencies = []
        
        return steps
    
    def _balance_workload(self, steps: List[TaskStep]) -> List[TaskStep]:
        """Balancea la carga de trabajo entre pasos"""
        
        # Ajustar duraciones basado en complejidad
        for step in steps:
            if step.complexity > 0.8:
                step.estimated_duration = int(step.estimated_duration * 1.2)
            elif step.complexity < 0.3:
                step.estimated_duration = int(step.estimated_duration * 0.8)
        
        return steps
    
    def _requires_dependency(self, step: TaskStep, prev_step: TaskStep) -> bool:
        """Determina si un paso realmente requiere depender del anterior"""
        
        # Pasos de herramientas diferentes pueden ejecutarse en paralelo
        if step.tool != prev_step.tool:
            return False
        
        # Pasos de lectura pueden ejecutarse en paralelo
        read_actions = ["search", "analyze", "read", "get"]
        if any(action in step.description.lower() for action in read_actions):
            return False
        
        return True
    
    def _calculate_complexity(self, steps: List[TaskStep]) -> float:
        """Calcula la complejidad total del plan"""
        
        if not steps:
            return 0.0
        
        total_complexity = sum(step.complexity for step in steps)
        avg_complexity = total_complexity / len(steps)
        
        # Ajustar por dependencias
        dependency_factor = sum(len(step.dependencies) for step in steps) / len(steps)
        
        return min(avg_complexity + (dependency_factor * 0.1), 1.0)
    
    def _calculate_success_probability(self, steps: List[TaskStep]) -> float:
        """Calcula la probabilidad de éxito del plan"""
        
        if not steps:
            return 0.0
        
        # Probabilidad base por complejidad
        base_prob = 1.0 - (self._calculate_complexity(steps) * 0.3)
        
        # Ajustar por número de pasos
        step_penalty = min(len(steps) * 0.02, 0.2)
        
        # Ajustar por herramientas disponibles
        tool_bonus = min(len(set(step.tool for step in steps)) * 0.05, 0.1)
        
        return max(base_prob - step_penalty + tool_bonus, 0.1)
    
    def _select_best_tool(self, step_name: str, preferred_tools: List[str], 
                         available_tools: List[str]) -> str:
        """Selecciona la mejor herramienta para un paso"""
        
        # Preferir herramientas específicas para el paso
        for tool in preferred_tools:
            if tool in available_tools:
                return tool
        
        # Fallback a herramientas genéricas
        generic_tools = ["file_manager", "shell", "web_search"]
        for tool in generic_tools:
            if tool in available_tools:
                return tool
        
        return available_tools[0] if available_tools else "file_manager"
    
    def _select_primary_tool(self, task_type: str, available_tools: List[str]) -> str:
        """Selecciona la herramienta principal para un tipo de tarea"""
        
        primary_tools = {
            "research": ["web_search", "deep_research", "comprehensive_research"],
            "analysis": ["file_manager", "shell"],
            "development": ["shell", "file_manager"],
            "automation": ["shell", "playwright"],
            "general": ["file_manager", "web_search"]
        }
        
        preferred = primary_tools.get(task_type, ["file_manager"])
        
        for tool in preferred:
            if tool in available_tools:
                return tool
        
        return available_tools[0] if available_tools else "file_manager"
    
    def _select_adaptive_tool(self, task_type: str, available_tools: List[str]) -> str:
        """Selecciona herramienta para planificación adaptativa"""
        
        adaptive_tools = {
            "research": "comprehensive_research",
            "analysis": "deep_research",
            "development": "shell",
            "automation": "playwright",
            "general": "web_search"
        }
        
        preferred = adaptive_tools.get(task_type, "web_search")
        
        return preferred if preferred in available_tools else self._select_primary_tool(task_type, available_tools)
    
    def _select_goal_tool(self, goal: str, available_tools: List[str]) -> str:
        """Selecciona herramienta basada en el objetivo"""
        
        goal_lower = goal.lower()
        
        if any(word in goal_lower for word in ["buscar", "encontrar", "investigar"]):
            return "web_search" if "web_search" in available_tools else "file_manager"
        
        if any(word in goal_lower for word in ["crear", "generar", "escribir"]):
            return "file_manager" if "file_manager" in available_tools else "shell"
        
        if any(word in goal_lower for word in ["ejecutar", "correr", "comando"]):
            return "shell" if "shell" in available_tools else "file_manager"
        
        return available_tools[0] if available_tools else "file_manager"
    
    def _find_alternative_tool(self, original_tool: str, available_tools: List[str]) -> str:
        """Encuentra una herramienta alternativa"""
        
        alternatives = {
            "web_search": ["deep_research", "comprehensive_research"],
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
        
        return available_tools[0] if available_tools else "file_manager"
    
    def _extract_main_goal(self, task_description: str) -> str:
        """Extrae el objetivo principal de la descripción de la tarea"""
        
        # Buscar patrones de objetivo
        goal_patterns = [
            r"(crear|generar|desarrollar|construir)\s+(.+)",
            r"(analizar|examinar|evaluar)\s+(.+)",
            r"(buscar|encontrar|obtener)\s+(.+)",
            r"(automatizar|programar|configurar)\s+(.+)"
        ]
        
        import re
        for pattern in goal_patterns:
            match = re.search(pattern, task_description.lower())
            if match:
                return match.group(2).strip()
        
        return task_description
    
    def _generate_step_parameters(self, step_name: str, task_description: str, tool: str) -> Dict[str, Any]:
        """Genera parámetros específicos para un paso"""
        
        base_params = {
            "context": task_description,
            "step": step_name,
            "tool": tool
        }
        
        # Parámetros específicos por herramienta
        if tool == "web_search":
            base_params.update({
                "query": task_description,
                "max_results": 10
            })
        elif tool == "deep_research":
            base_params.update({
                "query": task_description,
                "max_sources": 15,
                "research_depth": "comprehensive"
            })
        elif tool == "file_manager":
            base_params.update({
                "action": step_name,
                "context": task_description
            })
        elif tool == "shell":
            base_params.update({
                "command": f"echo 'Ejecutando {step_name} para {task_description}'",
                "timeout": 30
            })
        
        return base_params
    
    def _generate_execution_parameters(self, task_description: str) -> Dict[str, Any]:
        """Genera parámetros para ejecución principal"""
        
        return {
            "task": task_description,
            "execution_mode": "main",
            "timeout": 120
        }
    
    def _generate_parallel_parameters(self, task_description: str, tool: str) -> Dict[str, Any]:
        """Genera parámetros para ejecución paralela"""
        
        params = {
            "task": task_description,
            "parallel_mode": True,
            "tool": tool
        }
        
        if tool == "web_search":
            params.update({
                "query": task_description,
                "max_results": 5,
                "parallel_search": True
            })
        elif tool == "deep_research":
            params.update({
                "query": task_description,
                "max_sources": 10,
                "parallel_research": True
            })
        
        return params
    
    def _estimate_duration(self, step_name: str, tool: str) -> int:
        """Estima la duración de un paso en segundos"""
        
        # Duraciones base por herramienta
        tool_durations = {
            "web_search": 45,
            "deep_research": 120,
            "comprehensive_research": 180,
            "file_manager": 30,
            "shell": 60,
            "playwright": 90,
            "tavily_search": 45
        }
        
        base_duration = tool_durations.get(tool, 60)
        
        # Ajustar por complejidad del paso
        if "analyze" in step_name.lower():
            base_duration *= 1.5
        elif "prepare" in step_name.lower():
            base_duration *= 0.5
        
        return int(base_duration)
    
    def _estimate_complexity(self, step_name: str, tool: str) -> float:
        """Estima la complejidad de un paso"""
        
        # Complejidad base por herramienta
        tool_complexity = {
            "web_search": 0.4,
            "deep_research": 0.7,
            "comprehensive_research": 0.8,
            "file_manager": 0.3,
            "shell": 0.5,
            "playwright": 0.6,
            "tavily_search": 0.4
        }
        
        base_complexity = tool_complexity.get(tool, 0.5)
        
        # Ajustar por tipo de paso
        if "analyze" in step_name.lower():
            base_complexity += 0.2
        elif "synthesize" in step_name.lower():
            base_complexity += 0.3
        elif "prepare" in step_name.lower():
            base_complexity -= 0.1
        
        return max(0.1, min(base_complexity, 1.0))