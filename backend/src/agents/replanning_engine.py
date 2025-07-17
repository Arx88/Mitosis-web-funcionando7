"""
ReplanningEngine - Replanificación Dinámica para Mitosis V5
===========================================================

Este módulo implementa la capacidad de replanificación dinámica del agente.
Cuando una herramienta falla, el agente analiza el error y genera un plan alternativo automáticamente.

Características clave:
- Análisis de errores en tiempo real
- Generación de planes alternativos
- Integración con sistema de memoria
- Estrategias de contingencia
- Puntos de control para rollback
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from src.tools.task_planner import ExecutionPlan, TaskStep, ExecutionStrategy
from src.tools.execution_engine import ExecutionContext, StepExecution, StepStatus
from src.memory.advanced_memory_manager import AdvancedMemoryManager
from src.services.ollama_service import OllamaService
from src.analysis.error_analyzer import ErrorAnalyzer

logger = logging.getLogger(__name__)

class ReplanningStrategy(Enum):
    """Estrategias de replanificación disponibles"""
    TOOL_SUBSTITUTION = "tool_substitution"        # Cambiar herramienta fallida por alternativa
    PARAMETER_ADJUSTMENT = "parameter_adjustment"   # Ajustar parámetros de la herramienta
    STEP_DECOMPOSITION = "step_decomposition"      # Descomponer paso complejo en pasos simples
    ALTERNATIVE_APPROACH = "alternative_approach"   # Enfoque completamente diferente
    ROLLBACK_AND_RETRY = "rollback_and_retry"      # Volver a punto anterior y reintentar
    SKIP_AND_CONTINUE = "skip_and_continue"        # Saltar paso y continuar
    HUMAN_INTERVENTION = "human_intervention"       # Solicitar ayuda humana

class ErrorCategory(Enum):
    """Categorías de errores para análisis"""
    TOOL_UNAVAILABLE = "tool_unavailable"          # Herramienta no disponible
    INVALID_PARAMETERS = "invalid_parameters"      # Parámetros incorrectos
    NETWORK_ERROR = "network_error"                # Error de red/conectividad
    PERMISSION_ERROR = "permission_error"          # Error de permisos
    RESOURCE_EXHAUSTED = "resource_exhausted"      # Recursos agotados
    TIMEOUT_ERROR = "timeout_error"                # Timeout en ejecución
    UNEXPECTED_RESULT = "unexpected_result"        # Resultado inesperado
    DEPENDENCY_FAILED = "dependency_failed"        # Dependencia falló
    UNKNOWN_ERROR = "unknown_error"                # Error desconocido

@dataclass
class ReplanningContext:
    """Contexto para replanificación"""
    original_plan: ExecutionPlan
    failed_step: TaskStep
    error_info: Dict[str, Any]
    execution_context: 'ExecutionContext'  # Forward reference para evitar importación circular
    failed_step_execution: 'StepExecution'  # Forward reference para evitar importación circular
    available_tools: List[str]
    previous_attempts: List[Dict[str, Any]] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class ReplanningResult:
    """Resultado de replanificación"""
    success: bool
    new_plan: Optional[ExecutionPlan] = None
    strategy_used: Optional[ReplanningStrategy] = None
    modifications: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    reasoning: str = ""
    estimated_success_probability: float = 0.0
    fallback_options: List[Dict[str, Any]] = field(default_factory=list)

class ReplanningEngine:
    """Motor de replanificación dinámica"""
    
    def __init__(self, 
                 memory_manager: AdvancedMemoryManager,
                 ollama_service: OllamaService,
                 config: Dict[str, Any] = None):
        """
        Inicializar ReplanningEngine
        
        Args:
            memory_manager: Gestor de memoria avanzado
            ollama_service: Servicio LLM para análisis
            config: Configuración del motor
        """
        self.memory_manager = memory_manager
        self.ollama_service = ollama_service
        self.config = config or {}
        
        # Configuración por defecto
        self.max_replanning_attempts = self.config.get('max_replanning_attempts', 3)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        self.enable_aggressive_replanning = self.config.get('enable_aggressive_replanning', True)
        self.enable_llm_analysis = self.config.get('enable_llm_analysis', True)
        
        # Estadísticas
        self.replannings_performed = 0
        self.successful_replannings = 0
        self.strategies_used = {}
        
        # Mapeo de herramientas alternativas
        self.tool_alternatives = {
            'web_search': ['enhanced_web_search', 'duckduckgo_search', 'comprehensive_research'],
            'enhanced_web_search': ['web_search', 'duckduckgo_search', 'comprehensive_research'],
            'file_manager': ['shell', 'python_executor'],
            'shell': ['python_executor', 'file_manager'],
            'python_executor': ['shell', 'file_manager'],
            'comprehensive_research': ['web_search', 'enhanced_web_search', 'deep_research'],
            'deep_research': ['comprehensive_research', 'web_search', 'enhanced_web_search']
        }
        
        logger.info("🔄 ReplanningEngine inicializado")
    
    async def analyze_failure_and_replan(self, 
                                       context: ReplanningContext) -> ReplanningResult:
        """
        Analizar fallo y generar nuevo plan
        
        Args:
            context: Contexto de replanificación
            
        Returns:
            Resultado de replanificación
        """
        try:
            logger.info(f"🔍 Analizando fallo en paso: {context.failed_step.id}")
            
            # Incrementar contador
            self.replannings_performed += 1
            
            # 1. Categorizar error
            error_category = await self._categorize_error(context)
            logger.info(f"📊 Error categorizado como: {error_category.value}")
            
            # 2. Analizar con LLM si está habilitado
            llm_analysis = {}
            if self.enable_llm_analysis:
                llm_analysis = await self._analyze_with_llm(context, error_category)
            
            # 3. Determinar estrategia de replanificación
            strategy = await self._determine_strategy(context, error_category, llm_analysis)
            logger.info(f"🎯 Estrategia seleccionada: {strategy.value}")
            
            # 4. Generar nuevo plan según estrategia
            new_plan = await self._generate_new_plan(context, strategy, llm_analysis)
            
            # 5. Evaluar confianza y probabilidad de éxito
            confidence_score = await self._evaluate_confidence(context, new_plan, strategy)
            success_probability = await self._estimate_success_probability(context, new_plan)
            
            # 6. Crear resultado
            result = ReplanningResult(
                success=new_plan is not None,
                new_plan=new_plan,
                strategy_used=strategy,
                confidence_score=confidence_score,
                reasoning=llm_analysis.get('reasoning', f"Applied {strategy.value} strategy"),
                estimated_success_probability=success_probability,
                fallback_options=await self._generate_fallback_options(context, strategy)
            )
            
            # 7. Registrar en memoria para aprendizaje
            await self._record_replanning_in_memory(context, result)
            
            # 8. Actualizar estadísticas
            if result.success:
                self.successful_replannings += 1
                self.strategies_used[strategy.value] = self.strategies_used.get(strategy.value, 0) + 1
            
            logger.info(f"✅ Replanificación {'exitosa' if result.success else 'fallida'}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en replanificación: {str(e)}")
            return ReplanningResult(
                success=False,
                reasoning=f"Error en replanificación: {str(e)}"
            )
    
    async def _categorize_error(self, context: ReplanningContext) -> ErrorCategory:
        """Categorizar el error para determinar estrategia"""
        
        error_info = context.error_info
        error_message = str(error_info.get('error', '')).lower()
        
        # Análisis de patrones en el mensaje de error
        if any(pattern in error_message for pattern in ['not found', 'unavailable', 'not available']):
            return ErrorCategory.TOOL_UNAVAILABLE
        elif any(pattern in error_message for pattern in ['invalid', 'parameter', 'argument']):
            return ErrorCategory.INVALID_PARAMETERS
        elif any(pattern in error_message for pattern in ['network', 'connection', 'host', 'dns']):
            return ErrorCategory.NETWORK_ERROR
        elif any(pattern in error_message for pattern in ['permission', 'access', 'forbidden', 'unauthorized']):
            return ErrorCategory.PERMISSION_ERROR
        elif any(pattern in error_message for pattern in ['timeout', 'time out', 'timed out']):
            return ErrorCategory.TIMEOUT_ERROR
        elif any(pattern in error_message for pattern in ['memory', 'disk', 'space', 'limit']):
            return ErrorCategory.RESOURCE_EXHAUSTED
        elif context.failed_step_execution.retry_count > 0:
            return ErrorCategory.DEPENDENCY_FAILED
        else:
            return ErrorCategory.UNKNOWN_ERROR
    
    async def _analyze_with_llm(self, 
                              context: ReplanningContext, 
                              error_category: ErrorCategory) -> Dict[str, Any]:
        """Analizar fallo con LLM para obtener insights"""
        
        try:
            # Construir prompt para análisis
            prompt = self._build_analysis_prompt(context, error_category)
            
            # Generar análisis con LLM
            response = await self.ollama_service.generate_response(prompt, {
                'max_tokens': 500,
                'temperature': 0.3,
                'task_type': 'error_analysis'
            })
            
            if response.get('error'):
                logger.warning(f"Error en análisis LLM: {response['error']}")
                return {'reasoning': 'LLM analysis failed'}
            
            # Parsear respuesta
            analysis_text = response.get('response', '')
            return self._parse_llm_analysis(analysis_text)
            
        except Exception as e:
            logger.warning(f"Error en análisis LLM: {str(e)}")
            return {'reasoning': 'LLM analysis failed'}
    
    def _build_analysis_prompt(self, 
                              context: ReplanningContext, 
                              error_category: ErrorCategory) -> str:
        """Construir prompt para análisis LLM"""
        
        return f"""
Analiza el siguiente fallo en la ejecución de una tarea y proporciona recomendaciones:

**TAREA ORIGINAL:**
- Título: {context.original_plan.title}
- Estrategia: {context.original_plan.strategy.value}

**PASO FALLIDO:**
- ID: {context.failed_step.id}
- Título: {context.failed_step.title}
- Herramienta: {context.failed_step.tool}
- Parámetros: {json.dumps(context.failed_step.parameters, indent=2)}

**ERROR:**
- Categoría: {error_category.value}
- Mensaje: {context.error_info.get('error', 'No error message')}
- Intentos: {context.failed_step_execution.retry_count}

**HERRAMIENTAS DISPONIBLES:**
{', '.join(context.available_tools)}

**ANÁLISIS REQUERIDO:**
1. Identifica la causa raíz del fallo
2. Sugiere 2-3 estrategias alternativas específicas
3. Recomienda modificaciones a parámetros si es necesario
4. Evalúa la probabilidad de éxito de cada alternativa
5. Proporciona razonamiento detallado

Responde en formato JSON con las siguientes claves:
- "root_cause": string
- "recommended_strategies": array of strings
- "parameter_modifications": object
- "success_probabilities": array of numbers (0-1)
- "reasoning": string
"""
    
    def _parse_llm_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parsear análisis LLM"""
        
        try:
            # Intentar parsear como JSON
            if analysis_text.strip().startswith('{'):
                return json.loads(analysis_text)
            
            # Fallback: extraer información manualmente
            return {
                'root_cause': 'Unable to parse LLM analysis',
                'recommended_strategies': ['tool_substitution'],
                'reasoning': analysis_text[:200] + '...' if len(analysis_text) > 200 else analysis_text
            }
            
        except json.JSONDecodeError:
            return {
                'root_cause': 'JSON parsing failed',
                'recommended_strategies': ['tool_substitution'],
                'reasoning': analysis_text[:200] + '...' if len(analysis_text) > 200 else analysis_text
            }
    
    async def _determine_strategy(self, 
                                context: ReplanningContext, 
                                error_category: ErrorCategory,
                                llm_analysis: Dict[str, Any]) -> ReplanningStrategy:
        """Determinar estrategia de replanificación"""
        
        # Estrategia basada en análisis LLM si está disponible
        if llm_analysis.get('recommended_strategies'):
            recommended = llm_analysis['recommended_strategies'][0]
            try:
                return ReplanningStrategy(recommended)
            except ValueError:
                pass
        
        # Estrategia basada en categoría de error
        strategy_map = {
            ErrorCategory.TOOL_UNAVAILABLE: ReplanningStrategy.TOOL_SUBSTITUTION,
            ErrorCategory.INVALID_PARAMETERS: ReplanningStrategy.PARAMETER_ADJUSTMENT,
            ErrorCategory.NETWORK_ERROR: ReplanningStrategy.ROLLBACK_AND_RETRY,
            ErrorCategory.PERMISSION_ERROR: ReplanningStrategy.PARAMETER_ADJUSTMENT,
            ErrorCategory.TIMEOUT_ERROR: ReplanningStrategy.PARAMETER_ADJUSTMENT,
            ErrorCategory.RESOURCE_EXHAUSTED: ReplanningStrategy.STEP_DECOMPOSITION,
            ErrorCategory.DEPENDENCY_FAILED: ReplanningStrategy.ALTERNATIVE_APPROACH,
            ErrorCategory.UNKNOWN_ERROR: ReplanningStrategy.TOOL_SUBSTITUTION
        }
        
        return strategy_map.get(error_category, ReplanningStrategy.ALTERNATIVE_APPROACH)
    
    async def _generate_new_plan(self, 
                               context: ReplanningContext, 
                               strategy: ReplanningStrategy,
                               llm_analysis: Dict[str, Any]) -> Optional[ExecutionPlan]:
        """Generar nuevo plan según estrategia"""
        
        try:
            if strategy == ReplanningStrategy.TOOL_SUBSTITUTION:
                return await self._apply_tool_substitution(context)
            elif strategy == ReplanningStrategy.PARAMETER_ADJUSTMENT:
                return await self._apply_parameter_adjustment(context, llm_analysis)
            elif strategy == ReplanningStrategy.STEP_DECOMPOSITION:
                return await self._apply_step_decomposition(context)
            elif strategy == ReplanningStrategy.ALTERNATIVE_APPROACH:
                return await self._apply_alternative_approach(context)
            elif strategy == ReplanningStrategy.ROLLBACK_AND_RETRY:
                return await self._apply_rollback_and_retry(context)
            elif strategy == ReplanningStrategy.SKIP_AND_CONTINUE:
                return await self._apply_skip_and_continue(context)
            else:
                logger.warning(f"Estrategia no implementada: {strategy.value}")
                return None
                
        except Exception as e:
            logger.error(f"Error generando plan para estrategia {strategy.value}: {str(e)}")
            return None
    
    async def _apply_tool_substitution(self, context: ReplanningContext) -> Optional[ExecutionPlan]:
        """Aplicar sustitución de herramienta"""
        
        failed_tool = context.failed_step.tool
        alternatives = self.tool_alternatives.get(failed_tool, [])
        
        # Filtrar alternativas disponibles
        available_alternatives = [
            tool for tool in alternatives 
            if tool in context.available_tools
        ]
        
        if not available_alternatives:
            logger.warning(f"No hay alternativas disponibles para {failed_tool}")
            return None
        
        # Seleccionar mejor alternativa
        best_alternative = available_alternatives[0]
        
        # Crear nuevo plan
        new_plan = context.original_plan
        new_steps = []
        
        for step in new_plan.steps:
            if step.id == context.failed_step.id:
                # Reemplazar herramienta fallida
                new_step = TaskStep(
                    id=f"{step.id}_alt",
                    title=f"{step.title} (alternativa)",
                    tool=best_alternative,
                    parameters=self._adapt_parameters_for_tool(step.parameters, best_alternative),
                    dependencies=step.dependencies,
                    estimated_duration=step.estimated_duration,
                    description=f"Alternativa usando {best_alternative}: {step.description}"
                )
                new_steps.append(new_step)
            else:
                new_steps.append(step)
        
        new_plan.steps = new_steps
        new_plan.total_estimated_duration = sum(step.estimated_duration for step in new_steps)
        
        return new_plan
    
    async def _apply_parameter_adjustment(self, 
                                        context: ReplanningContext,
                                        llm_analysis: Dict[str, Any]) -> Optional[ExecutionPlan]:
        """Aplicar ajuste de parámetros"""
        
        # Obtener modificaciones sugeridas por LLM
        modifications = llm_analysis.get('parameter_modifications', {})
        
        # Aplicar modificaciones automáticas basadas en tipo de error
        new_parameters = context.failed_step.parameters.copy()
        
        # Ajustes específicos por herramienta
        if context.failed_step.tool in ['web_search', 'enhanced_web_search']:
            # Simplificar query si es muy compleja
            if 'query' in new_parameters:
                query = new_parameters['query']
                if len(query.split()) > 10:
                    new_parameters['query'] = ' '.join(query.split()[:5])
            
            # Añadir timeout si no existe
            if 'timeout' not in new_parameters:
                new_parameters['timeout'] = 30
        
        elif context.failed_step.tool == 'shell':
            # Añadir sudo si es error de permisos
            if 'command' in new_parameters:
                command = new_parameters['command']
                if not command.startswith('sudo'):
                    new_parameters['command'] = f"sudo {command}"
        
        # Aplicar modificaciones del LLM
        new_parameters.update(modifications)
        
        # Crear nuevo plan
        new_plan = context.original_plan
        new_steps = []
        
        for step in new_plan.steps:
            if step.id == context.failed_step.id:
                # Crear paso con parámetros ajustados
                new_step = TaskStep(
                    id=f"{step.id}_adj",
                    title=f"{step.title} (ajustado)",
                    tool=step.tool,
                    parameters=new_parameters,
                    dependencies=step.dependencies,
                    estimated_duration=step.estimated_duration,
                    description=f"Parámetros ajustados: {step.description}"
                )
                new_steps.append(new_step)
            else:
                new_steps.append(step)
        
        new_plan.steps = new_steps
        return new_plan
    
    async def _apply_step_decomposition(self, context: ReplanningContext) -> Optional[ExecutionPlan]:
        """Aplicar descomposición de paso"""
        
        failed_step = context.failed_step
        
        # Descomponer según herramienta
        if failed_step.tool in ['web_search', 'enhanced_web_search']:
            # Descomponer búsqueda compleja en búsquedas simples
            query = failed_step.parameters.get('query', '')
            sub_queries = query.split(' AND ')
            
            if len(sub_queries) > 1:
                new_substeps = []
                for i, sub_query in enumerate(sub_queries):
                    substep = TaskStep(
                        id=f"{failed_step.id}_part_{i}",
                        title=f"Búsqueda parte {i+1}",
                        tool=failed_step.tool,
                        parameters={**failed_step.parameters, 'query': sub_query.strip()},
                        dependencies=failed_step.dependencies if i == 0 else [f"{failed_step.id}_part_{i-1}"],
                        estimated_duration=failed_step.estimated_duration // len(sub_queries),
                        description=f"Búsqueda parcial: {sub_query.strip()}"
                    )
                    new_substeps.append(substep)
                
                # Crear nuevo plan
                new_plan = context.original_plan
                new_steps = []
                
                for step in new_plan.steps:
                    if step.id == failed_step.id:
                        new_steps.extend(new_substeps)
                    else:
                        new_steps.append(step)
                
                new_plan.steps = new_steps
                new_plan.total_estimated_duration = sum(step.estimated_duration for step in new_steps)
                return new_plan
        
        # Fallback: usar enfoque alternativo
        return await self._apply_alternative_approach(context)
    
    async def _apply_alternative_approach(self, context: ReplanningContext) -> Optional[ExecutionPlan]:
        """Aplicar enfoque alternativo"""
        
        failed_step = context.failed_step
        
        # Enfoques alternativos por herramienta
        if failed_step.tool in ['web_search', 'enhanced_web_search']:
            # Cambiar a enfoque de investigación profunda
            alternative_step = TaskStep(
                id=f"{failed_step.id}_alt_approach",
                title="Investigación con enfoque alternativo",
                tool='comprehensive_research',
                parameters={
                    'topic': failed_step.parameters.get('query', ''),
                    'depth': 'moderate',
                    'sources': 'multiple'
                },
                dependencies=failed_step.dependencies,
                estimated_duration=failed_step.estimated_duration * 1.5,
                description="Investigación usando enfoque alternativo"
            )
        
        elif failed_step.tool == 'file_manager':
            # Cambiar a operaciones shell
            alternative_step = TaskStep(
                id=f"{failed_step.id}_alt_approach",
                title="Operación de archivo vía shell",
                tool='shell',
                parameters={
                    'command': self._convert_file_op_to_shell(failed_step.parameters)
                },
                dependencies=failed_step.dependencies,
                estimated_duration=failed_step.estimated_duration,
                description="Operación de archivo usando shell"
            )
        
        else:
            # Enfoque genérico: usar shell como fallback
            alternative_step = TaskStep(
                id=f"{failed_step.id}_alt_approach",
                title="Enfoque alternativo genérico",
                tool='shell',
                parameters={
                    'command': 'echo "Ejecutando enfoque alternativo"'
                },
                dependencies=failed_step.dependencies,
                estimated_duration=failed_step.estimated_duration,
                description="Enfoque alternativo usando shell"
            )
        
        # Crear nuevo plan
        new_plan = context.original_plan
        new_steps = []
        
        for step in new_plan.steps:
            if step.id == failed_step.id:
                new_steps.append(alternative_step)
            else:
                new_steps.append(step)
        
        new_plan.steps = new_steps
        return new_plan
    
    async def _apply_rollback_and_retry(self, context: ReplanningContext) -> Optional[ExecutionPlan]:
        """Aplicar rollback y reintentar"""
        
        # Crear plan que incluya rollback
        rollback_step = TaskStep(
            id=f"{context.failed_step.id}_rollback",
            title="Rollback automático",
            tool='shell',
            parameters={
                'command': 'echo "Realizando rollback automático"'
            },
            dependencies=[],
            estimated_duration=10,
            description="Rollback automático antes de reintentar"
        )
        
        # Paso de reintento con parámetros ajustados
        retry_step = TaskStep(
            id=f"{context.failed_step.id}_retry",
            title=f"{context.failed_step.title} (reintento)",
            tool=context.failed_step.tool,
            parameters=context.failed_step.parameters.copy(),
            dependencies=[rollback_step.id],
            estimated_duration=context.failed_step.estimated_duration,
            description=f"Reintento después de rollback: {context.failed_step.description}"
        )
        
        # Crear nuevo plan
        new_plan = context.original_plan
        new_steps = []
        
        for step in new_plan.steps:
            if step.id == context.failed_step.id:
                new_steps.extend([rollback_step, retry_step])
            else:
                new_steps.append(step)
        
        new_plan.steps = new_steps
        new_plan.total_estimated_duration = sum(step.estimated_duration for step in new_steps)
        return new_plan
    
    async def _apply_skip_and_continue(self, context: ReplanningContext) -> Optional[ExecutionPlan]:
        """Aplicar saltar y continuar"""
        
        # Crear paso de skip
        skip_step = TaskStep(
            id=f"{context.failed_step.id}_skip",
            title="Paso saltado",
            tool='shell',
            parameters={
                'command': f'echo "Saltando paso: {context.failed_step.title}"'
            },
            dependencies=context.failed_step.dependencies,
            estimated_duration=5,
            description=f"Paso saltado debido a fallo: {context.failed_step.description}"
        )
        
        # Crear nuevo plan
        new_plan = context.original_plan
        new_steps = []
        
        for step in new_plan.steps:
            if step.id == context.failed_step.id:
                new_steps.append(skip_step)
            else:
                # Actualizar dependencias si referenciaban al paso fallido
                updated_dependencies = []
                for dep in step.dependencies:
                    if dep == context.failed_step.id:
                        updated_dependencies.append(skip_step.id)
                    else:
                        updated_dependencies.append(dep)
                
                step.dependencies = updated_dependencies
                new_steps.append(step)
        
        new_plan.steps = new_steps
        return new_plan
    
    def _adapt_parameters_for_tool(self, 
                                  original_params: Dict[str, Any], 
                                  new_tool: str) -> Dict[str, Any]:
        """Adaptar parámetros para nueva herramienta"""
        
        # Mapeo de parámetros entre herramientas
        if new_tool == 'enhanced_web_search' and 'query' in original_params:
            return {
                'query': original_params['query'],
                'search_type': 'comprehensive',
                'max_results': original_params.get('max_results', 10)
            }
        
        elif new_tool == 'comprehensive_research' and 'query' in original_params:
            return {
                'topic': original_params['query'],
                'depth': 'moderate',
                'sources': 'multiple'
            }
        
        elif new_tool == 'shell' and 'command' in original_params:
            return {'command': original_params['command']}
        
        # Fallback: mantener parámetros originales
        return original_params
    
    def _convert_file_op_to_shell(self, file_params: Dict[str, Any]) -> str:
        """Convertir operación de archivo a comando shell"""
        
        action = file_params.get('action', 'list')
        path = file_params.get('path', '.')
        
        if action == 'list':
            return f'ls -la {path}'
        elif action == 'read':
            return f'cat {path}'
        elif action == 'write':
            content = file_params.get('content', '')
            return f'echo "{content}" > {path}'
        elif action == 'mkdir':
            return f'mkdir -p {path}'
        elif action == 'delete':
            return f'rm -rf {path}'
        else:
            return f'ls -la {path}'
    
    async def _evaluate_confidence(self, 
                                 context: ReplanningContext, 
                                 new_plan: Optional[ExecutionPlan], 
                                 strategy: ReplanningStrategy) -> float:
        """Evaluar confianza en el nuevo plan"""
        
        if not new_plan:
            return 0.0
        
        # Factores de confianza
        confidence_factors = {
            ReplanningStrategy.TOOL_SUBSTITUTION: 0.8,
            ReplanningStrategy.PARAMETER_ADJUSTMENT: 0.7,
            ReplanningStrategy.STEP_DECOMPOSITION: 0.6,
            ReplanningStrategy.ALTERNATIVE_APPROACH: 0.5,
            ReplanningStrategy.ROLLBACK_AND_RETRY: 0.4,
            ReplanningStrategy.SKIP_AND_CONTINUE: 0.3,
            ReplanningStrategy.HUMAN_INTERVENTION: 0.9
        }
        
        base_confidence = confidence_factors.get(strategy, 0.5)
        
        # Ajustar por intentos previos
        penalty = context.failed_step_execution.retry_count * 0.1
        
        # Ajustar por disponibilidad de herramientas alternativas
        if strategy == ReplanningStrategy.TOOL_SUBSTITUTION:
            alternatives = self.tool_alternatives.get(context.failed_step.tool, [])
            available_alternatives = [t for t in alternatives if t in context.available_tools]
            if available_alternatives:
                base_confidence += 0.1
        
        return max(0.0, min(1.0, base_confidence - penalty))
    
    async def _estimate_success_probability(self, 
                                          context: ReplanningContext, 
                                          new_plan: Optional[ExecutionPlan]) -> float:
        """Estimar probabilidad de éxito del nuevo plan"""
        
        if not new_plan:
            return 0.0
        
        # Consultar memoria para patrones históricos
        try:
            # Buscar episodios similares en memoria
            similar_episodes = await self.memory_manager.semantic_memory.semantic_search(
                query=f"replanning {context.failed_step.tool} error",
                max_results=5
            )
            
            if similar_episodes:
                # Calcular tasa de éxito histórica
                success_count = sum(1 for ep in similar_episodes if ep.get('success', False))
                total_count = len(similar_episodes)
                historical_success_rate = success_count / total_count
                
                # Combinar con estimación base
                base_estimate = 0.6
                return (historical_success_rate + base_estimate) / 2
        
        except Exception as e:
            logger.warning(f"Error consultando memoria histórica: {str(e)}")
        
        # Estimación base
        return 0.6
    
    async def _generate_fallback_options(self, 
                                       context: ReplanningContext, 
                                       primary_strategy: ReplanningStrategy) -> List[Dict[str, Any]]:
        """Generar opciones de fallback"""
        
        fallback_options = []
        
        # Estrategias alternativas ordenadas por preferencia
        all_strategies = [
            ReplanningStrategy.TOOL_SUBSTITUTION,
            ReplanningStrategy.PARAMETER_ADJUSTMENT,
            ReplanningStrategy.STEP_DECOMPOSITION,
            ReplanningStrategy.ALTERNATIVE_APPROACH,
            ReplanningStrategy.ROLLBACK_AND_RETRY,
            ReplanningStrategy.SKIP_AND_CONTINUE,
            ReplanningStrategy.HUMAN_INTERVENTION
        ]
        
        for strategy in all_strategies:
            if strategy != primary_strategy:
                fallback_options.append({
                    'strategy': strategy.value,
                    'description': self._get_strategy_description(strategy),
                    'estimated_effort': self._estimate_strategy_effort(strategy),
                    'success_probability': await self._estimate_strategy_success_probability(context, strategy)
                })
        
        return fallback_options[:3]  # Top 3 fallbacks
    
    def _get_strategy_description(self, strategy: ReplanningStrategy) -> str:
        """Obtener descripción de estrategia"""
        
        descriptions = {
            ReplanningStrategy.TOOL_SUBSTITUTION: "Reemplazar herramienta fallida con alternativa",
            ReplanningStrategy.PARAMETER_ADJUSTMENT: "Ajustar parámetros de la herramienta",
            ReplanningStrategy.STEP_DECOMPOSITION: "Descomponer paso en subtareas más simples",
            ReplanningStrategy.ALTERNATIVE_APPROACH: "Usar enfoque completamente diferente",
            ReplanningStrategy.ROLLBACK_AND_RETRY: "Volver a estado anterior y reintentar",
            ReplanningStrategy.SKIP_AND_CONTINUE: "Saltar paso problemático",
            ReplanningStrategy.HUMAN_INTERVENTION: "Solicitar intervención humana"
        }
        
        return descriptions.get(strategy, "Estrategia desconocida")
    
    def _estimate_strategy_effort(self, strategy: ReplanningStrategy) -> str:
        """Estimar esfuerzo requerido para estrategia"""
        
        effort_levels = {
            ReplanningStrategy.TOOL_SUBSTITUTION: "Bajo",
            ReplanningStrategy.PARAMETER_ADJUSTMENT: "Muy Bajo",
            ReplanningStrategy.STEP_DECOMPOSITION: "Medio",
            ReplanningStrategy.ALTERNATIVE_APPROACH: "Alto",
            ReplanningStrategy.ROLLBACK_AND_RETRY: "Medio",
            ReplanningStrategy.SKIP_AND_CONTINUE: "Muy Bajo",
            ReplanningStrategy.HUMAN_INTERVENTION: "Variable"
        }
        
        return effort_levels.get(strategy, "Desconocido")
    
    async def _estimate_strategy_success_probability(self, 
                                                   context: ReplanningContext, 
                                                   strategy: ReplanningStrategy) -> float:
        """Estimar probabilidad de éxito de estrategia"""
        
        # Probabilidades base por estrategia
        base_probabilities = {
            ReplanningStrategy.TOOL_SUBSTITUTION: 0.8,
            ReplanningStrategy.PARAMETER_ADJUSTMENT: 0.7,
            ReplanningStrategy.STEP_DECOMPOSITION: 0.6,
            ReplanningStrategy.ALTERNATIVE_APPROACH: 0.5,
            ReplanningStrategy.ROLLBACK_AND_RETRY: 0.4,
            ReplanningStrategy.SKIP_AND_CONTINUE: 0.9,  # Siempre funciona técnicamente
            ReplanningStrategy.HUMAN_INTERVENTION: 0.95
        }
        
        return base_probabilities.get(strategy, 0.5)
    
    async def _record_replanning_in_memory(self, 
                                         context: ReplanningContext, 
                                         result: ReplanningResult):
        """Registrar replanificación en memoria para aprendizaje"""
        
        try:
            # Preparar datos para memoria
            replanning_data = {
                'type': 'replanning_event',
                'timestamp': datetime.now().isoformat(),
                'original_step_id': context.failed_step.id,
                'original_tool': context.failed_step.tool,
                'error_category': self._categorize_error(context).value,
                'strategy_used': result.strategy_used.value if result.strategy_used else None,
                'success': result.success,
                'confidence_score': result.confidence_score,
                'estimated_success_probability': result.estimated_success_probability,
                'reasoning': result.reasoning,
                'modifications': result.modifications
            }
            
            # Almacenar en memoria episódica
            if self.memory_manager.is_initialized:
                from src.memory.episodic_memory_store import Episode
                
                episode = Episode(
                    id=str(uuid.uuid4()),
                    title=f"Replanificación: {context.failed_step.tool}",
                    description=f"Replanificación para paso fallido usando {result.strategy_used.value if result.strategy_used else 'unknown'}",
                    context=replanning_data,
                    actions=[{
                        'type': 'replanning',
                        'strategy': result.strategy_used.value if result.strategy_used else 'unknown',
                        'timestamp': datetime.now().isoformat()
                    }],
                    outcomes=[{
                        'type': 'replanning_result',
                        'success': result.success,
                        'confidence': result.confidence_score,
                        'timestamp': datetime.now().isoformat()
                    }],
                    timestamp=datetime.now(),
                    success=result.success,
                    importance=4,  # Alta importancia para aprendizaje
                    tags=['replanning', 'error_recovery', context.failed_step.tool]
                )
                
                await self.memory_manager.episodic_memory.store_episode(episode)
                logger.info("🧠 Episodio de replanificación almacenado en memoria")
            
            # También almacenar en memoria semántica como conocimiento
            await self.memory_manager.semantic_memory.store_fact(
                f"replanning_strategy_{context.failed_step.tool}_{result.strategy_used.value if result.strategy_used else 'unknown'}",
                replanning_data,
                source="replanning_engine",
                confidence=result.confidence_score
            )
            
        except Exception as e:
            logger.warning(f"Error almacenando replanificación en memoria: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del motor de replanificación"""
        
        success_rate = (
            self.successful_replannings / self.replannings_performed 
            if self.replannings_performed > 0 else 0
        )
        
        return {
            'total_replannings': self.replannings_performed,
            'successful_replannings': self.successful_replannings,
            'success_rate': success_rate,
            'strategies_used': self.strategies_used,
            'most_used_strategy': max(self.strategies_used.keys(), key=self.strategies_used.get) if self.strategies_used else None,
            'configuration': {
                'max_replanning_attempts': self.max_replanning_attempts,
                'confidence_threshold': self.confidence_threshold,
                'enable_aggressive_replanning': self.enable_aggressive_replanning,
                'enable_llm_analysis': self.enable_llm_analysis
            }
        }
    
    def reset_statistics(self):
        """Resetear estadísticas"""
        self.replannings_performed = 0
        self.successful_replannings = 0
        self.strategies_used = {}
        logger.info("🔄 Estadísticas de replanificación reseteadas")