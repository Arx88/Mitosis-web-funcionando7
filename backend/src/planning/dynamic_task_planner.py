"""
DynamicTaskPlanner - Planificación Dinámica con LLM para Mitosis V5
===================================================================

Este módulo implementa un planificador de tareas dinámico que usa LLM para descomposición inteligente.
Mejora la planificación actual con razonamiento semántico y selección inteligente de herramientas.

Características clave:
- Planificación usando LLM (Ollama)
- Descomposición inteligente de tareas complejas
- Selección de herramientas basada en razonamiento
- Generación de planes jerárquicos (DAG)
- Estimación de dependencias y tiempos
- Integración con sistema de memoria
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import re
from collections import defaultdict

from src.tools.task_planner import TaskPlan, TaskStep, ExecutionPlan
from src.tools.execution_engine import ExecutionStrategy
from src.memory.advanced_memory_manager import AdvancedMemoryManager
from src.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class PlanningApproach(Enum):
    """Enfoques de planificación"""
    SEQUENTIAL = "sequential"        # Planificación secuencial
    PARALLEL = "parallel"           # Planificación paralela
    HIERARCHICAL = "hierarchical"   # Planificación jerárquica
    ADAPTIVE = "adaptive"           # Planificación adaptativa
    ITERATIVE = "iterative"         # Planificación iterativa

class TaskComplexity(Enum):
    """Niveles de complejidad de tareas"""
    SIMPLE = "simple"               # Tarea simple (1-2 pasos)
    MODERATE = "moderate"           # Tarea moderada (3-5 pasos)
    COMPLEX = "complex"             # Tarea compleja (6-10 pasos)
    VERY_COMPLEX = "very_complex"   # Tarea muy compleja (10+ pasos)

class ToolCategory(Enum):
    """Categorías de herramientas"""
    SEARCH = "search"               # Herramientas de búsqueda
    ANALYSIS = "analysis"           # Herramientas de análisis
    CREATION = "creation"           # Herramientas de creación
    COMMUNICATION = "communication"  # Herramientas de comunicación
    SYSTEM = "system"               # Herramientas de sistema
    FILE_MANAGEMENT = "file_management"  # Gestión de archivos
    COMPUTATION = "computation"      # Herramientas de cálculo

@dataclass
class PlanningContext:
    """Contexto para planificación"""
    task_id: str
    task_description: str
    user_intent: str
    available_tools: List[str]
    constraints: Dict[str, Any]
    preferences: Dict[str, Any]
    historical_patterns: List[Dict[str, Any]]
    session_context: Dict[str, Any]
    
@dataclass
class PlanningResult:
    """Resultado de planificación"""
    plan: TaskPlan
    reasoning: str
    confidence_score: float
    complexity_assessment: TaskComplexity
    approach_used: PlanningApproach
    alternative_plans: List[TaskPlan]
    planning_time: float
    estimated_success_probability: float
    
@dataclass
class StepDependency:
    """Dependencia entre pasos"""
    step_id: str
    depends_on: str
    dependency_type: str  # 'sequential', 'resource', 'data', 'conditional'
    strength: float  # 0.0 - 1.0

class EnhancedDynamicTaskPlanner:
    """Planificador dinámico de tareas mejorado"""
    
    def __init__(self, 
                 memory_manager: AdvancedMemoryManager,
                 ollama_service: OllamaService,
                 config: Dict[str, Any] = None):
        """
        Inicializar DynamicTaskPlanner
        
        Args:
            memory_manager: Gestor de memoria avanzado
            ollama_service: Servicio LLM para planificación
            config: Configuración del planificador
        """
        self.memory_manager = memory_manager
        self.ollama_service = ollama_service
        self.config = config or {}
        
        # Configuración por defecto
        self.max_planning_iterations = self.config.get('max_planning_iterations', 3)
        self.enable_multi_approach = self.config.get('enable_multi_approach', True)
        self.planning_depth = self.config.get('planning_depth', 'comprehensive')
        self.enable_dependency_optimization = self.config.get('enable_dependency_optimization', True)
        
        # Estadísticas
        self.plans_generated = 0
        self.successful_plans = 0
        self.average_planning_time = 0.0
        self.complexity_distribution = defaultdict(int)
        
        # Mapeo de herramientas por categoría
        self.tool_categories = {
            'web_search': ToolCategory.SEARCH,
            'enhanced_web_search': ToolCategory.SEARCH,
            'comprehensive_research': ToolCategory.SEARCH,
            'deep_research': ToolCategory.ANALYSIS,
            'file_manager': ToolCategory.FILE_MANAGEMENT,
            'shell': ToolCategory.SYSTEM,
            'python_executor': ToolCategory.COMPUTATION,
            'data_analyzer': ToolCategory.ANALYSIS,
            'content_generator': ToolCategory.CREATION,
            'email_sender': ToolCategory.COMMUNICATION
        }
        
        # Patrones de planificación aprendidos
        self.planning_patterns = {}
        
        logger.info("🚀 EnhancedDynamicTaskPlanner inicializado")
    
    async def create_dynamic_plan(self, 
                                task_id: str,
                                task_description: str,
                                context: Dict[str, Any] = None) -> TaskPlan:
        """
        Crear plan dinámico usando LLM
        
        Args:
            task_id: ID de la tarea
            task_description: Descripción de la tarea
            context: Contexto adicional
            
        Returns:
            Plan de tareas generado
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Iniciando planificación dinámica para: {task_description}")
            
            # Incrementar contador
            self.plans_generated += 1
            
            # 1. Crear contexto de planificación
            planning_context = await self._create_planning_context(
                task_id, task_description, context
            )
            
            # 2. Analizar complejidad de la tarea
            complexity = await self._analyze_task_complexity(planning_context)
            
            # 3. Determinar enfoque de planificación
            approach = await self._determine_planning_approach(planning_context, complexity)
            
            # 4. Generar plan usando LLM
            plan_result = await self._generate_plan_with_llm(planning_context, approach, complexity)
            
            # 5. Optimizar dependencias
            if self.enable_dependency_optimization:
                plan_result.plan = await self._optimize_dependencies(plan_result.plan)
            
            # 6. Validar y ajustar plan
            validated_plan = await self._validate_and_adjust_plan(plan_result.plan, planning_context)
            
            # 7. Calcular métricas finales
            planning_time = (datetime.now() - start_time).total_seconds()
            self.average_planning_time = (
                (self.average_planning_time * (self.plans_generated - 1) + planning_time) / 
                self.plans_generated
            )
            
            # 8. Registrar en memoria
            await self._record_planning_in_memory(validated_plan, planning_context, approach)
            
            # 9. Actualizar estadísticas
            self.complexity_distribution[complexity] += 1
            
            logger.info(f"✅ Plan generado exitosamente con {len(validated_plan.steps)} pasos")
            return validated_plan
            
        except Exception as e:
            logger.error(f"❌ Error en planificación dinámica: {str(e)}")
            # Fallback a planificación simple
            return await self._generate_fallback_plan(task_id, task_description, context)
    
    async def _create_planning_context(self, 
                                     task_id: str,
                                     task_description: str,
                                     context: Dict[str, Any] = None) -> PlanningContext:
        """Crear contexto de planificación"""
        
        context = context or {}
        
        # Analizar intención del usuario
        user_intent = await self._analyze_user_intent(task_description)
        
        # Obtener herramientas disponibles
        available_tools = context.get('available_tools', [])
        
        # Obtener patrones históricos
        historical_patterns = await self._get_historical_patterns(task_description)
        
        # Preparar contexto
        return PlanningContext(
            task_id=task_id,
            task_description=task_description,
            user_intent=user_intent,
            available_tools=available_tools,
            constraints=context.get('constraints', {}),
            preferences=context.get('preferences', {}),
            historical_patterns=historical_patterns,
            session_context=context.get('session_context', {})
        )
    
    async def _analyze_task_complexity(self, context: PlanningContext) -> TaskComplexity:
        """Analizar complejidad de la tarea"""
        
        complexity_factors = []
        
        # Factor 1: Longitud y detalle de descripción
        desc_length = len(context.task_description.split())
        if desc_length < 10:
            complexity_factors.append(1)
        elif desc_length < 30:
            complexity_factors.append(2)
        elif desc_length < 100:
            complexity_factors.append(3)
        else:
            complexity_factors.append(4)
        
        # Factor 2: Palabras clave de complejidad
        complex_keywords = [
            'analizar', 'investigar', 'comparar', 'evaluar', 'desarrollar',
            'crear', 'diseñar', 'implementar', 'optimizar', 'integrar'
        ]
        
        moderate_keywords = [
            'buscar', 'encontrar', 'obtener', 'procesar', 'generar',
            'calcular', 'convertir', 'formatear', 'organizar'
        ]
        
        desc_lower = context.task_description.lower()
        complex_count = sum(1 for word in complex_keywords if word in desc_lower)
        moderate_count = sum(1 for word in moderate_keywords if word in desc_lower)
        
        if complex_count > 2:
            complexity_factors.append(4)
        elif complex_count > 0:
            complexity_factors.append(3)
        elif moderate_count > 1:
            complexity_factors.append(2)
        else:
            complexity_factors.append(1)
        
        # Factor 3: Múltiples objetivos
        objectives = len(re.findall(r'[.!?]', context.task_description))
        if objectives > 3:
            complexity_factors.append(4)
        elif objectives > 1:
            complexity_factors.append(3)
        else:
            complexity_factors.append(2)
        
        # Factor 4: Dependencias implícitas
        dependency_words = ['luego', 'después', 'primero', 'finalmente', 'entonces']
        dep_count = sum(1 for word in dependency_words if word in desc_lower)
        if dep_count > 2:
            complexity_factors.append(4)
        elif dep_count > 0:
            complexity_factors.append(3)
        else:
            complexity_factors.append(1)
        
        # Calcular complejidad promedio
        avg_complexity = sum(complexity_factors) / len(complexity_factors)
        
        if avg_complexity <= 1.5:
            return TaskComplexity.SIMPLE
        elif avg_complexity <= 2.5:
            return TaskComplexity.MODERATE
        elif avg_complexity <= 3.5:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.VERY_COMPLEX
    
    async def _determine_planning_approach(self, 
                                         context: PlanningContext,
                                         complexity: TaskComplexity) -> PlanningApproach:
        """Determinar enfoque de planificación"""
        
        # Mapeo de complejidad a enfoque
        approach_map = {
            TaskComplexity.SIMPLE: PlanningApproach.SEQUENTIAL,
            TaskComplexity.MODERATE: PlanningApproach.HIERARCHICAL,
            TaskComplexity.COMPLEX: PlanningApproach.ADAPTIVE,
            TaskComplexity.VERY_COMPLEX: PlanningApproach.ITERATIVE
        }
        
        base_approach = approach_map[complexity]
        
        # Ajustar según contexto
        if 'parallel' in context.task_description.lower():
            return PlanningApproach.PARALLEL
        elif 'step by step' in context.task_description.lower():
            return PlanningApproach.SEQUENTIAL
        elif 'adapt' in context.task_description.lower():
            return PlanningApproach.ADAPTIVE
        
        return base_approach
    
    async def _generate_plan_with_llm(self, 
                                    context: PlanningContext,
                                    approach: PlanningApproach,
                                    complexity: TaskComplexity) -> PlanningResult:
        """Generar plan usando LLM"""
        
        try:
            # Construir prompt especializado
            prompt = self._build_planning_prompt(context, approach, complexity)
            
            # Generar plan con LLM
            response = await self.ollama_service.generate_response(prompt, {
                'max_tokens': 1500,
                'temperature': 0.3,
                'task_type': 'task_planning'
            })
            
            if response.get('error'):
                logger.warning(f"Error en LLM: {response['error']}")
                return await self._generate_fallback_plan_result(context)
            
            # Parsear respuesta
            plan_data = self._parse_llm_plan(response.get('response', ''))
            
            # Convertir a TaskPlan
            task_plan = await self._convert_to_task_plan(plan_data, context)
            
            # Crear resultado
            return PlanningResult(
                plan=task_plan,
                reasoning=plan_data.get('reasoning', 'Generated with LLM'),
                confidence_score=plan_data.get('confidence', 0.8),
                complexity_assessment=complexity,
                approach_used=approach,
                alternative_plans=[],
                planning_time=0.0,
                estimated_success_probability=plan_data.get('success_probability', 0.75)
            )
            
        except Exception as e:
            logger.error(f"Error en generación LLM: {str(e)}")
            return await self._generate_fallback_plan_result(context)
    
    def _build_planning_prompt(self, 
                              context: PlanningContext,
                              approach: PlanningApproach,
                              complexity: TaskComplexity) -> str:
        """Construir prompt para planificación"""
        
        # Preparar herramientas disponibles
        tools_info = self._format_tools_info(context.available_tools)
        
        # Preparar ejemplos históricos
        historical_examples = self._format_historical_examples(context.historical_patterns)
        
        return f"""
Actúa como un planificador experto de tareas. Tu objetivo es descomponer la siguiente tarea en pasos ejecutables.

**TAREA A PLANIFICAR:**
{context.task_description}

**INFORMACIÓN DEL CONTEXTO:**
- Intención del usuario: {context.user_intent}
- Complejidad evaluada: {complexity.value}
- Enfoque sugerido: {approach.value}
- Restricciones: {json.dumps(context.constraints, indent=2)}

**HERRAMIENTAS DISPONIBLES:**
{tools_info}

**EJEMPLOS HISTÓRICOS RELEVANTES:**
{historical_examples}

**INSTRUCCIONES DE PLANIFICACIÓN:**
1. Descompón la tarea en pasos específicos y ejecutables
2. Asigna la herramienta más apropiada para cada paso
3. Establece dependencias entre pasos cuando sea necesario
4. Estima duración realista para cada paso
5. Incluye manejo de errores y puntos de control
6. Optimiza para eficiencia y robustez

**CRITERIOS DE CALIDAD:**
- Cada paso debe ser atómico y verificable
- Las dependencias deben estar claramente definidas
- Los parámetros deben ser específicos y completos
- El plan debe ser resistente a fallos

Responde ÚNICAMENTE en formato JSON:
{{
  "plan": {{
    "title": "Título descriptivo del plan",
    "strategy": "comprehensive|efficient|adaptive|robust",
    "steps": [
      {{
        "id": "step_1",
        "title": "Título del paso",
        "tool": "herramienta_a_usar",
        "parameters": {{
          "param1": "valor1",
          "param2": "valor2"
        }},
        "description": "Descripción detallada del paso",
        "dependencies": ["step_id_previo"],
        "estimated_duration": 30,
        "success_criteria": ["criterio1", "criterio2"],
        "error_handling": "estrategia_manejo_errores"
      }}
    ]
  }},
  "reasoning": "Explicación del razonamiento usado",
  "confidence": 0.85,
  "success_probability": 0.80,
  "complexity_factors": ["factor1", "factor2"],
  "optimization_notes": ["nota1", "nota2"]
}}
"""
    
    def _format_tools_info(self, available_tools: List[str]) -> str:
        """Formatear información de herramientas"""
        
        if not available_tools:
            return "No hay herramientas disponibles"
        
        tool_descriptions = {
            'web_search': 'Búsqueda web básica con query',
            'enhanced_web_search': 'Búsqueda web avanzada con filtros',
            'comprehensive_research': 'Investigación exhaustiva multi-fuente',
            'deep_research': 'Investigación profunda con análisis',
            'file_manager': 'Gestión de archivos (crear, leer, escribir)',
            'shell': 'Ejecución de comandos del sistema',
            'python_executor': 'Ejecución de código Python',
            'data_analyzer': 'Análisis de datos y estadísticas',
            'content_generator': 'Generación de contenido',
            'email_sender': 'Envío de correos electrónicos'
        }
        
        tools_info = []
        for tool in available_tools:
            description = tool_descriptions.get(tool, f'Herramienta {tool}')
            category = self.tool_categories.get(tool, ToolCategory.SYSTEM)
            tools_info.append(f"- {tool}: {description} (Categoría: {category.value})")
        
        return '\n'.join(tools_info)
    
    def _format_historical_examples(self, patterns: List[Dict[str, Any]]) -> str:
        """Formatear ejemplos históricos"""
        
        if not patterns:
            return "No hay ejemplos históricos disponibles"
        
        examples = []
        for pattern in patterns[:3]:  # Máximo 3 ejemplos
            examples.append(f"- {pattern.get('description', 'Ejemplo')}: {pattern.get('outcome', 'Resultado')}")
        
        return '\n'.join(examples)
    
    def _parse_llm_plan(self, response_text: str) -> Dict[str, Any]:
        """Parsear plan del LLM"""
        
        try:
            # Limpiar respuesta si es necesario
            response_text = response_text.strip()
            
            # Extraer JSON si está en markdown
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            
            # Parsear JSON
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON: {str(e)}")
            return self._generate_fallback_plan_data()
        except Exception as e:
            logger.error(f"Error inesperado parseando plan: {str(e)}")
            return self._generate_fallback_plan_data()
    
    def _generate_fallback_plan_data(self) -> Dict[str, Any]:
        """Generar datos de plan fallback"""
        
        return {
            'plan': {
                'title': 'Plan básico',
                'strategy': 'efficient',
                'steps': [
                    {
                        'id': 'step_1',
                        'title': 'Ejecutar tarea',
                        'tool': 'shell',
                        'parameters': {'command': 'echo "Ejecutando tarea"'},
                        'description': 'Paso básico de ejecución',
                        'dependencies': [],
                        'estimated_duration': 30,
                        'success_criteria': ['Ejecución exitosa'],
                        'error_handling': 'retry'
                    }
                ]
            },
            'reasoning': 'Plan fallback generado automáticamente',
            'confidence': 0.5,
            'success_probability': 0.6,
            'complexity_factors': ['simple_task'],
            'optimization_notes': ['Plan básico']
        }
    
    async def _convert_to_task_plan(self, 
                                  plan_data: Dict[str, Any],
                                  context: PlanningContext) -> TaskPlan:
        """Convertir datos de plan a TaskPlan"""
        
        plan_info = plan_data.get('plan', {})
        
        # Convertir estrategia
        strategy_map = {
            'comprehensive': ExecutionStrategy.COMPREHENSIVE,
            'efficient': ExecutionStrategy.EFFICIENT,
            'adaptive': ExecutionStrategy.ADAPTIVE,
            'robust': ExecutionStrategy.ROBUST
        }
        
        strategy = strategy_map.get(plan_info.get('strategy', 'efficient'), ExecutionStrategy.EFFICIENT)
        
        # Convertir pasos
        steps = []
        for step_data in plan_info.get('steps', []):
            step = TaskStep(
                id=step_data.get('id', f'step_{len(steps) + 1}'),
                title=step_data.get('title', 'Paso sin título'),
                tool=step_data.get('tool', 'shell'),
                parameters=step_data.get('parameters', {}),
                dependencies=step_data.get('dependencies', []),
                estimated_duration=step_data.get('estimated_duration', 30),
                description=step_data.get('description', '')
            )
            steps.append(step)
        
        # Calcular duración total
        total_duration = sum(step.estimated_duration for step in steps)
        
        # Calcular score de complejidad
        complexity_score = len(steps) * 0.5 + len([s for s in steps if s.dependencies]) * 0.3
        
        return TaskPlan(
            id=context.task_id,
            title=plan_info.get('title', 'Plan generado'),
            strategy=strategy,
            steps=steps,
            total_estimated_duration=total_duration,
            complexity_score=complexity_score,
            success_probability=plan_data.get('success_probability', 0.75),
            created_at=datetime.now()
        )
    
    async def _optimize_dependencies(self, plan: TaskPlan) -> TaskPlan:
        """Optimizar dependencias del plan"""
        
        try:
            # Analizar dependencias actuales
            dependencies = self._analyze_dependencies(plan.steps)
            
            # Optimizar orden de ejecución
            optimized_steps = self._optimize_execution_order(plan.steps, dependencies)
            
            # Crear plan optimizado
            optimized_plan = TaskPlan(
                id=plan.id,
                title=plan.title,
                strategy=plan.strategy,
                steps=optimized_steps,
                total_estimated_duration=plan.total_estimated_duration,
                complexity_score=plan.complexity_score,
                success_probability=plan.success_probability,
                created_at=plan.created_at
            )
            
            return optimized_plan
            
        except Exception as e:
            logger.warning(f"Error optimizando dependencias: {str(e)}")
            return plan
    
    def _analyze_dependencies(self, steps: List[TaskStep]) -> List[StepDependency]:
        """Analizar dependencias entre pasos"""
        
        dependencies = []
        
        for step in steps:
            for dep_id in step.dependencies:
                dependency = StepDependency(
                    step_id=step.id,
                    depends_on=dep_id,
                    dependency_type='sequential',
                    strength=1.0
                )
                dependencies.append(dependency)
        
        return dependencies
    
    def _optimize_execution_order(self, 
                                steps: List[TaskStep],
                                dependencies: List[StepDependency]) -> List[TaskStep]:
        """Optimizar orden de ejecución"""
        
        # Implementar ordenamiento topológico simple
        ordered_steps = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            # Buscar pasos sin dependencias pendientes
            executable_steps = []
            for step in remaining_steps:
                can_execute = True
                for dep in dependencies:
                    if dep.step_id == step.id:
                        # Verificar si la dependencia ya está en ordered_steps
                        if not any(s.id == dep.depends_on for s in ordered_steps):
                            can_execute = False
                            break
                
                if can_execute:
                    executable_steps.append(step)
            
            # Agregar pasos ejecutables
            for step in executable_steps:
                ordered_steps.append(step)
                remaining_steps.remove(step)
            
            # Evitar bucles infinitos
            if not executable_steps and remaining_steps:
                # Agregar el primer paso restante (romper ciclo)
                ordered_steps.append(remaining_steps[0])
                remaining_steps.remove(remaining_steps[0])
        
        return ordered_steps
    
    async def _validate_and_adjust_plan(self, 
                                      plan: TaskPlan,
                                      context: PlanningContext) -> TaskPlan:
        """Validar y ajustar plan"""
        
        validated_steps = []
        
        for step in plan.steps:
            # Validar herramienta disponible
            if step.tool not in context.available_tools:
                # Buscar herramienta alternativa
                alternative_tool = self._find_alternative_tool(step.tool, context.available_tools)
                if alternative_tool:
                    step.tool = alternative_tool
                    logger.info(f"🔄 Herramienta {step.tool} no disponible, usando {alternative_tool}")
                else:
                    logger.warning(f"⚠️ Herramienta {step.tool} no disponible, manteniendo para verificación")
            
            # Validar parámetros
            if not step.parameters:
                step.parameters = self._generate_default_parameters(step.tool)
            
            # Ajustar duración si es necesario
            if step.estimated_duration <= 0:
                step.estimated_duration = self._estimate_default_duration(step.tool)
            
            validated_steps.append(step)
        
        # Crear plan validado
        validated_plan = TaskPlan(
            id=plan.id,
            title=plan.title,
            strategy=plan.strategy,
            steps=validated_steps,
            total_estimated_duration=sum(step.estimated_duration for step in validated_steps),
            complexity_score=plan.complexity_score,
            success_probability=plan.success_probability,
            created_at=plan.created_at
        )
        
        return validated_plan
    
    def _find_alternative_tool(self, original_tool: str, available_tools: List[str]) -> Optional[str]:
        """Encontrar herramienta alternativa"""
        
        alternatives = {
            'web_search': ['enhanced_web_search', 'comprehensive_research'],
            'enhanced_web_search': ['web_search', 'comprehensive_research'],
            'file_manager': ['shell', 'python_executor'],
            'python_executor': ['shell', 'file_manager'],
            'data_analyzer': ['python_executor', 'shell'],
            'comprehensive_research': ['web_search', 'enhanced_web_search']
        }
        
        for alternative in alternatives.get(original_tool, []):
            if alternative in available_tools:
                return alternative
        
        return None
    
    def _generate_default_parameters(self, tool: str) -> Dict[str, Any]:
        """Generar parámetros por defecto para herramienta"""
        
        defaults = {
            'web_search': {'query': 'información general'},
            'enhanced_web_search': {'query': 'búsqueda avanzada'},
            'shell': {'command': 'ls -la'},
            'file_manager': {'action': 'list', 'path': '.'},
            'python_executor': {'code': 'print("Hello World")'},
            'comprehensive_research': {'topic': 'investigación general'}
        }
        
        return defaults.get(tool, {})
    
    def _estimate_default_duration(self, tool: str) -> int:
        """Estimar duración por defecto para herramienta"""
        
        durations = {
            'web_search': 15,
            'enhanced_web_search': 30,
            'comprehensive_research': 60,
            'shell': 5,
            'file_manager': 10,
            'python_executor': 20,
            'data_analyzer': 45
        }
        
        return durations.get(tool, 30)
    
    async def _analyze_user_intent(self, task_description: str) -> str:
        """Analizar intención del usuario"""
        
        # Análisis simple de intención basado en palabras clave
        desc_lower = task_description.lower()
        
        if any(word in desc_lower for word in ['buscar', 'encontrar', 'investigar']):
            return 'search_and_research'
        elif any(word in desc_lower for word in ['crear', 'generar', 'desarrollar']):
            return 'create_and_develop'
        elif any(word in desc_lower for word in ['analizar', 'evaluar', 'comparar']):
            return 'analyze_and_evaluate'
        elif any(word in desc_lower for word in ['procesar', 'transformar', 'convertir']):
            return 'process_and_transform'
        elif any(word in desc_lower for word in ['automatizar', 'ejecutar', 'correr']):
            return 'automate_and_execute'
        else:
            return 'general_task'
    
    async def _get_historical_patterns(self, task_description: str) -> List[Dict[str, Any]]:
        """Obtener patrones históricos relevantes"""
        
        patterns = []
        
        try:
            # Buscar en memoria episódica
            if self.memory_manager.is_initialized:
                similar_episodes = await self.memory_manager.semantic_memory.semantic_search(
                    query=task_description,
                    max_results=5
                )
                
                for episode in similar_episodes:
                    if episode.get('type') == 'task_execution':
                        patterns.append({
                            'description': episode.get('description', ''),
                            'outcome': episode.get('outcome', ''),
                            'success': episode.get('success', False),
                            'tools_used': episode.get('tools_used', [])
                        })
            
        except Exception as e:
            logger.warning(f"Error obteniendo patrones históricos: {str(e)}")
        
        return patterns
    
    async def _generate_fallback_plan_result(self, context: PlanningContext) -> PlanningResult:
        """Generar resultado de plan fallback"""
        
        fallback_plan = await self._generate_fallback_plan(
            context.task_id,
            context.task_description,
            {'available_tools': context.available_tools}
        )
        
        return PlanningResult(
            plan=fallback_plan,
            reasoning='Plan fallback generado automáticamente',
            confidence_score=0.5,
            complexity_assessment=TaskComplexity.SIMPLE,
            approach_used=PlanningApproach.SEQUENTIAL,
            alternative_plans=[],
            planning_time=0.0,
            estimated_success_probability=0.6
        )
    
    async def _generate_fallback_plan(self, 
                                    task_id: str,
                                    task_description: str,
                                    context: Dict[str, Any] = None) -> TaskPlan:
        """Generar plan fallback simple"""
        
        available_tools = context.get('available_tools', []) if context else []
        
        # Seleccionar herramienta por defecto
        default_tool = 'shell'
        if 'web_search' in available_tools:
            default_tool = 'web_search'
        elif available_tools:
            default_tool = available_tools[0]
        
        # Crear paso simple
        step = TaskStep(
            id='fallback_step',
            title=f'Ejecutar: {task_description}',
            tool=default_tool,
            parameters=self._generate_default_parameters(default_tool),
            dependencies=[],
            estimated_duration=60,
            description=f'Paso fallback para: {task_description}'
        )
        
        return TaskPlan(
            id=task_id,
            title='Plan fallback',
            strategy=ExecutionStrategy.EFFICIENT,
            steps=[step],
            total_estimated_duration=60,
            complexity_score=1.0,
            success_probability=0.6,
            created_at=datetime.now()
        )
    
    async def _record_planning_in_memory(self, 
                                       plan: TaskPlan,
                                       context: PlanningContext,
                                       approach: PlanningApproach):
        """Registrar planificación en memoria"""
        
        try:
            # Preparar datos para memoria
            planning_data = {
                'type': 'task_planning',
                'timestamp': datetime.now().isoformat(),
                'task_id': plan.id,
                'task_description': context.task_description,
                'approach_used': approach.value,
                'complexity': self.complexity_distribution,
                'steps_count': len(plan.steps),
                'estimated_duration': plan.total_estimated_duration,
                'success_probability': plan.success_probability,
                'tools_used': [step.tool for step in plan.steps]
            }
            
            # Almacenar en memoria episódica
            if self.memory_manager.is_initialized:
                from src.memory.episodic_memory_store import Episode
                
                episode = Episode(
                    id=str(uuid.uuid4()),
                    title=f"Planificación: {plan.title}",
                    description=f"Planificación de tarea con {len(plan.steps)} pasos",
                    context=planning_data,
                    actions=[{
                        'type': 'task_planning',
                        'approach': approach.value,
                        'timestamp': datetime.now().isoformat()
                    }],
                    outcomes=[{
                        'type': 'plan_generated',
                        'steps_count': len(plan.steps),
                        'estimated_duration': plan.total_estimated_duration,
                        'timestamp': datetime.now().isoformat()
                    }],
                    timestamp=datetime.now(),
                    success=True,
                    importance=3,
                    tags=['task_planning', 'dynamic_planning', approach.value]
                )
                
                await self.memory_manager.episodic_memory.store_episode(episode)
                logger.info("🧠 Planificación almacenada en memoria")
            
            # Almacenar patrón de planificación
            pattern_key = f"{approach.value}_{len(plan.steps)}"
            self.planning_patterns[pattern_key] = self.planning_patterns.get(pattern_key, 0) + 1
            
        except Exception as e:
            logger.warning(f"Error almacenando planificación en memoria: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del planificador"""
        
        success_rate = (
            self.successful_plans / self.plans_generated 
            if self.plans_generated > 0 else 0
        )
        
        return {
            'plans_generated': self.plans_generated,
            'successful_plans': self.successful_plans,
            'success_rate': success_rate,
            'average_planning_time': self.average_planning_time,
            'complexity_distribution': dict(self.complexity_distribution),
            'planning_patterns': self.planning_patterns,
            'most_used_approach': max(self.planning_patterns.keys(), key=self.planning_patterns.get) if self.planning_patterns else None,
            'configuration': {
                'max_planning_iterations': self.max_planning_iterations,
                'enable_multi_approach': self.enable_multi_approach,
                'planning_depth': self.planning_depth,
                'enable_dependency_optimization': self.enable_dependency_optimization
            }
        }
    
    def reset_statistics(self):
        """Resetear estadísticas"""
        self.plans_generated = 0
        self.successful_plans = 0
        self.average_planning_time = 0.0
        self.complexity_distribution.clear()
        self.planning_patterns.clear()
        logger.info("🚀 Estadísticas de planificación reseteadas")

# Instancia global del planificador
_dynamic_task_planner = None

def get_enhanced_dynamic_task_planner(memory_manager=None, ollama_service=None, config=None):
    """Obtener instancia del planificador dinámico mejorado"""
    global _dynamic_task_planner
    
    if _dynamic_task_planner is None and memory_manager and ollama_service:
        _dynamic_task_planner = EnhancedDynamicTaskPlanner(
            memory_manager=memory_manager,
            ollama_service=ollama_service,
            config=config
        )
    
    return _dynamic_task_planner