"""
SelfReflectionEngine - Auto-reflexión y Metacognición para Mitosis V5
======================================================================

Este módulo implementa la capacidad de auto-reflexión y metacognición del agente.
El agente evalúa su propio rendimiento, aprende de sus acciones y mejora continuamente.

Características clave:
- Evaluación de calidad de respuestas
- Análisis de eficiencia de planes
- Aprendizaje de patrones exitosos y fallidos
- Actualización automática de estrategias
- Metacognición sobre proceso de pensamiento
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import statistics
from collections import defaultdict

from src.tools.task_planner import TaskPlan, TaskStep, ExecutionStrategy
from src.tools.execution_engine import ExecutionContext, StepExecution, StepStatus
from src.memory.advanced_memory_manager import AdvancedMemoryManager
from src.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class ReflectionDimension(Enum):
    """Dimensiones de reflexión"""
    TASK_QUALITY = "task_quality"              # Calidad de la tarea completada
    EXECUTION_EFFICIENCY = "execution_efficiency"  # Eficiencia de ejecución
    RESOURCE_UTILIZATION = "resource_utilization"  # Uso de recursos
    ERROR_HANDLING = "error_handling"          # Manejo de errores
    LEARNING_OUTCOMES = "learning_outcomes"    # Resultados de aprendizaje
    USER_SATISFACTION = "user_satisfaction"    # Satisfacción del usuario
    STRATEGIC_THINKING = "strategic_thinking"  # Pensamiento estratégico
    ADAPTABILITY = "adaptability"              # Capacidad de adaptación

class ReflectionLevel(Enum):
    """Niveles de reflexión"""
    STEP_LEVEL = "step_level"          # Reflexión a nivel de paso
    TASK_LEVEL = "task_level"          # Reflexión a nivel de tarea
    SESSION_LEVEL = "session_level"    # Reflexión a nivel de sesión
    STRATEGIC_LEVEL = "strategic_level"  # Reflexión estratégica a largo plazo

class InsightType(Enum):
    """Tipos de insights"""
    IMPROVEMENT_OPPORTUNITY = "improvement_opportunity"
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    EFFICIENCY_GAIN = "efficiency_gain"
    STRATEGIC_INSIGHT = "strategic_insight"
    LEARNING_POINT = "learning_point"

@dataclass
class ReflectionMetrics:
    """Métricas para reflexión"""
    execution_time: float
    success_rate: float
    error_count: int
    retries_used: int
    resources_consumed: Dict[str, float]
    user_feedback_score: Optional[float] = None
    complexity_score: float = 0.0
    innovation_score: float = 0.0
    
@dataclass
class ReflectionInsight:
    """Insight generado por reflexión"""
    id: str
    type: InsightType
    dimension: ReflectionDimension
    level: ReflectionLevel
    title: str
    description: str
    confidence: float
    actionable_recommendations: List[str]
    supporting_evidence: List[str]
    priority: float
    timestamp: datetime
    
@dataclass
class ReflectionResult:
    """Resultado de reflexión"""
    task_id: str
    reflection_id: str
    overall_performance_score: float
    dimensional_scores: Dict[ReflectionDimension, float]
    insights: List[ReflectionInsight]
    learning_points: List[str]
    improvement_actions: List[str]
    strengths_identified: List[str]
    weaknesses_identified: List[str]
    strategic_recommendations: List[str]
    confidence_score: float
    timestamp: datetime

class SelfReflectionEngine:
    """Motor de auto-reflexión y metacognición"""
    
    def __init__(self, 
                 memory_manager: AdvancedMemoryManager,
                 ollama_service: OllamaService,
                 config: Dict[str, Any] = None):
        """
        Inicializar SelfReflectionEngine
        
        Args:
            memory_manager: Gestor de memoria avanzado
            ollama_service: Servicio LLM para análisis
            config: Configuración del motor
        """
        self.memory_manager = memory_manager
        self.ollama_service = ollama_service
        self.config = config or {}
        
        # Configuración por defecto
        self.min_reflection_interval = self.config.get('min_reflection_interval', 300)  # 5 minutos
        self.enable_deep_reflection = self.config.get('enable_deep_reflection', True)
        self.enable_metacognition = self.config.get('enable_metacognition', True)
        self.reflection_depth = self.config.get('reflection_depth', 'comprehensive')
        
        # Estadísticas
        self.reflections_performed = 0
        self.insights_generated = 0
        self.improvements_implemented = 0
        self.average_performance_score = 0.0
        
        # Tracking de patrones
        self.success_patterns = defaultdict(int)
        self.failure_patterns = defaultdict(int)
        self.improvement_history = []
        
        # Cache de reflexiones recientes
        self.recent_reflections = {}
        
        logger.info("🧠 SelfReflectionEngine inicializado")
    
    async def reflect_on_task_execution(self, 
                                      execution_context: ExecutionContext,
                                      additional_metrics: Dict[str, Any] = None) -> ReflectionResult:
        """
        Reflexionar sobre la ejecución de una tarea
        
        Args:
            execution_context: Contexto de ejecución de la tarea
            additional_metrics: Métricas adicionales
            
        Returns:
            Resultado de reflexión
        """
        try:
            logger.info(f"🧠 Iniciando reflexión sobre tarea: {execution_context.task_id}")
            
            # Incrementar contador
            self.reflections_performed += 1
            
            # 1. Recopilar métricas de ejecución
            metrics = await self._collect_execution_metrics(execution_context, additional_metrics)
            
            # 2. Analizar rendimiento por dimensiones
            dimensional_scores = await self._analyze_performance_dimensions(execution_context, metrics)
            
            # 3. Generar insights usando LLM
            insights = await self._generate_insights(execution_context, metrics, dimensional_scores)
            
            # 4. Realizar análisis de metacognición
            metacognition_results = await self._perform_metacognition_analysis(execution_context, insights)
            
            # 5. Identificar patrones y aprendizajes
            patterns = await self._identify_patterns(execution_context, insights)
            
            # 6. Calcular puntuación general
            overall_score = await self._calculate_overall_performance(dimensional_scores, insights)
            
            # 7. Generar recomendaciones
            recommendations = await self._generate_recommendations(insights, patterns)
            
            # 8. Crear resultado de reflexión
            reflection_result = ReflectionResult(
                task_id=execution_context.task_id,
                reflection_id=str(uuid.uuid4()),
                overall_performance_score=overall_score,
                dimensional_scores=dimensional_scores,
                insights=insights,
                learning_points=metacognition_results.get('learning_points', []),
                improvement_actions=recommendations.get('improvement_actions', []),
                strengths_identified=recommendations.get('strengths', []),
                weaknesses_identified=recommendations.get('weaknesses', []),
                strategic_recommendations=recommendations.get('strategic', []),
                confidence_score=self._calculate_confidence(insights),
                timestamp=datetime.now()
            )
            
            # 9. Registrar en memoria para aprendizaje
            await self._record_reflection_in_memory(reflection_result)
            
            # 10. Actualizar estadísticas
            await self._update_statistics(reflection_result)
            
            # 11. Aplicar mejoras automáticas si es posible
            await self._apply_automatic_improvements(reflection_result)
            
            logger.info(f"✅ Reflexión completada con score: {overall_score:.2f}")
            return reflection_result
            
        except Exception as e:
            logger.error(f"❌ Error en reflexión: {str(e)}")
            # Crear resultado de error
            return ReflectionResult(
                task_id=execution_context.task_id,
                reflection_id=str(uuid.uuid4()),
                overall_performance_score=0.0,
                dimensional_scores={},
                insights=[],
                learning_points=[f"Error en reflexión: {str(e)}"],
                improvement_actions=[],
                strengths_identified=[],
                weaknesses_identified=[],
                strategic_recommendations=[],
                confidence_score=0.0,
                timestamp=datetime.now()
            )
    
    async def _collect_execution_metrics(self, 
                                       context: ExecutionContext,
                                       additional_metrics: Dict[str, Any] = None) -> ReflectionMetrics:
        """Recopilar métricas de ejecución"""
        
        # Métricas básicas
        total_steps = len(context.step_executions)
        completed_steps = sum(1 for se in context.step_executions if se.status == StepStatus.COMPLETED)
        error_count = sum(1 for se in context.step_executions if se.status == StepStatus.FAILED)
        retries_used = sum(se.retry_count for se in context.step_executions)
        
        # Recursos utilizados
        resources_consumed = {
            'execution_time': context.total_execution_time,
            'api_calls': len(context.step_executions),
            'memory_operations': context.variables.get('memory_operations', 0),
            'network_requests': sum(1 for se in context.step_executions if se.step.tool in ['web_search', 'enhanced_web_search'])
        }
        
        # Métricas de complejidad
        complexity_score = await self._calculate_complexity_score(context)
        
        return ReflectionMetrics(
            execution_time=context.total_execution_time,
            success_rate=context.success_rate,
            error_count=error_count,
            retries_used=retries_used,
            resources_consumed=resources_consumed,
            user_feedback_score=additional_metrics.get('user_feedback_score') if additional_metrics else None,
            complexity_score=complexity_score,
            innovation_score=await self._calculate_innovation_score(context)
        )
    
    async def _analyze_performance_dimensions(self, 
                                            context: ExecutionContext,
                                            metrics: ReflectionMetrics) -> Dict[ReflectionDimension, float]:
        """Analizar rendimiento por dimensiones"""
        
        scores = {}
        
        # Task Quality - Basado en tasa de éxito y complejidad
        task_quality = (metrics.success_rate * 0.7 + 
                       (1.0 - min(metrics.error_count / len(context.step_executions), 1.0)) * 0.3)
        scores[ReflectionDimension.TASK_QUALITY] = task_quality
        
        # Execution Efficiency - Basado en tiempo y reintentos
        expected_time = context.execution_plan.total_estimated_duration
        time_efficiency = min(expected_time / max(metrics.execution_time, 1), 1.0) if expected_time > 0 else 0.5
        retry_efficiency = 1.0 - min(metrics.retries_used / len(context.step_executions), 1.0)
        execution_efficiency = (time_efficiency * 0.6 + retry_efficiency * 0.4)
        scores[ReflectionDimension.EXECUTION_EFFICIENCY] = execution_efficiency
        
        # Resource Utilization - Basado en uso de recursos
        resource_efficiency = await self._calculate_resource_efficiency(metrics)
        scores[ReflectionDimension.RESOURCE_UTILIZATION] = resource_efficiency
        
        # Error Handling - Basado en recuperación de errores
        error_handling = await self._calculate_error_handling_score(context)
        scores[ReflectionDimension.ERROR_HANDLING] = error_handling
        
        # Learning Outcomes - Basado en mejoras aplicadas
        learning_outcomes = await self._calculate_learning_score(context)
        scores[ReflectionDimension.LEARNING_OUTCOMES] = learning_outcomes
        
        # User Satisfaction - Basado en feedback si está disponible
        user_satisfaction = metrics.user_feedback_score or 0.7  # Default neutral
        scores[ReflectionDimension.USER_SATISFACTION] = user_satisfaction
        
        # Strategic Thinking - Basado en selección de herramientas y enfoques
        strategic_thinking = await self._calculate_strategic_thinking_score(context)
        scores[ReflectionDimension.STRATEGIC_THINKING] = strategic_thinking
        
        # Adaptability - Basado en replanificación y ajustes
        adaptability = await self._calculate_adaptability_score(context)
        scores[ReflectionDimension.ADAPTABILITY] = adaptability
        
        return scores
    
    async def _generate_insights(self, 
                               context: ExecutionContext,
                               metrics: ReflectionMetrics,
                               dimensional_scores: Dict[ReflectionDimension, float]) -> List[ReflectionInsight]:
        """Generar insights usando LLM"""
        
        insights = []
        
        try:
            # Construir prompt para análisis
            prompt = self._build_insight_prompt(context, metrics, dimensional_scores)
            
            # Generar análisis con LLM
            response = await self.ollama_service.generate_response(prompt, {
                'max_tokens': 1000,
                'temperature': 0.4,
                'task_type': 'reflection_analysis'
            })
            
            if response.get('error'):
                logger.warning(f"Error en análisis LLM: {response['error']}")
                return self._generate_fallback_insights(dimensional_scores)
            
            # Parsear respuesta
            analysis_text = response.get('response', '')
            parsed_insights = self._parse_llm_insights(analysis_text)
            
            # Convertir a objetos ReflectionInsight
            for insight_data in parsed_insights:
                insight = ReflectionInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType(insight_data.get('type', 'learning_point')),
                    dimension=ReflectionDimension(insight_data.get('dimension', 'task_quality')),
                    level=ReflectionLevel.TASK_LEVEL,
                    title=insight_data.get('title', 'Insight'),
                    description=insight_data.get('description', ''),
                    confidence=insight_data.get('confidence', 0.5),
                    actionable_recommendations=insight_data.get('recommendations', []),
                    supporting_evidence=insight_data.get('evidence', []),
                    priority=insight_data.get('priority', 0.5),
                    timestamp=datetime.now()
                )
                insights.append(insight)
            
            # Incrementar contador
            self.insights_generated += len(insights)
            
        except Exception as e:
            logger.warning(f"Error generando insights: {str(e)}")
            insights = self._generate_fallback_insights(dimensional_scores)
        
        return insights
    
    def _build_insight_prompt(self, 
                            context: ExecutionContext,
                            metrics: ReflectionMetrics,
                            dimensional_scores: Dict[ReflectionDimension, float]) -> str:
        """Construir prompt para análisis de insights"""
        
        # Preparar información del contexto
        plan_info = {
            'title': context.execution_plan.title,
            'strategy': context.execution_plan.strategy.value,
            'total_steps': len(context.step_executions),
            'completed_steps': sum(1 for se in context.step_executions if se.status == StepStatus.COMPLETED),
            'failed_steps': sum(1 for se in context.step_executions if se.status == StepStatus.FAILED)
        }
        
        # Preparar scores
        scores_text = '\n'.join([
            f"- {dim.value}: {score:.2f}" 
            for dim, score in dimensional_scores.items()
        ])
        
        return f"""
Realiza un análisis profundo de reflexión sobre la ejecución de esta tarea:

**INFORMACIÓN DE LA TAREA:**
- Título: {plan_info['title']}
- Estrategia: {plan_info['strategy']}
- Pasos totales: {plan_info['total_steps']}
- Pasos completados: {plan_info['completed_steps']}
- Pasos fallidos: {plan_info['failed_steps']}

**MÉTRICAS DE RENDIMIENTO:**
- Tiempo de ejecución: {metrics.execution_time:.2f} segundos
- Tasa de éxito: {metrics.success_rate:.2f}
- Errores: {metrics.error_count}
- Reintentos: {metrics.retries_used}
- Complejidad: {metrics.complexity_score:.2f}
- Innovación: {metrics.innovation_score:.2f}

**PUNTUACIONES DIMENSIONALES:**
{scores_text}

**ANÁLISIS REQUERIDO:**
Por favor, genera insights específicos y accionables en las siguientes áreas:
1. Identificar patrones de éxito y fallo
2. Oportunidades de mejora concretas
3. Fortalezas a potenciar
4. Debilidades a abordar
5. Recomendaciones estratégicas

Responde en formato JSON con un array de insights:
{{
  "insights": [
    {{
      "type": "improvement_opportunity|success_pattern|failure_pattern|efficiency_gain|strategic_insight|learning_point",
      "dimension": "task_quality|execution_efficiency|resource_utilization|error_handling|learning_outcomes|user_satisfaction|strategic_thinking|adaptability",
      "title": "Título del insight",
      "description": "Descripción detallada",
      "confidence": 0.8,
      "recommendations": ["Recomendación 1", "Recomendación 2"],
      "evidence": ["Evidencia 1", "Evidencia 2"],
      "priority": 0.9
    }}
  ]
}}
"""
    
    def _parse_llm_insights(self, analysis_text: str) -> List[Dict[str, Any]]:
        """Parsear insights del LLM"""
        
        try:
            # Intentar parsear como JSON
            if analysis_text.strip().startswith('{'):
                parsed = json.loads(analysis_text)
                return parsed.get('insights', [])
            
            # Fallback: generar insights básicos
            return [
                {
                    'type': 'learning_point',
                    'dimension': 'task_quality',
                    'title': 'Análisis automático',
                    'description': analysis_text[:200] + '...' if len(analysis_text) > 200 else analysis_text,
                    'confidence': 0.5,
                    'recommendations': ['Revisar análisis detallado'],
                    'evidence': ['Análisis LLM'],
                    'priority': 0.5
                }
            ]
            
        except json.JSONDecodeError:
            return [
                {
                    'type': 'learning_point',
                    'dimension': 'task_quality',
                    'title': 'Error de parseo',
                    'description': 'No se pudo parsear el análisis del LLM',
                    'confidence': 0.3,
                    'recommendations': ['Verificar formato de respuesta'],
                    'evidence': ['Error de parseo'],
                    'priority': 0.3
                }
            ]
    
    def _generate_fallback_insights(self, 
                                  dimensional_scores: Dict[ReflectionDimension, float]) -> List[ReflectionInsight]:
        """Generar insights básicos como fallback"""
        
        insights = []
        
        # Identificar dimensiones con scores bajos
        for dimension, score in dimensional_scores.items():
            if score < 0.6:
                insight = ReflectionInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType.IMPROVEMENT_OPPORTUNITY,
                    dimension=dimension,
                    level=ReflectionLevel.TASK_LEVEL,
                    title=f"Mejorar {dimension.value}",
                    description=f"La dimensión {dimension.value} tiene un score bajo ({score:.2f})",
                    confidence=0.7,
                    actionable_recommendations=[f"Enfocarse en mejorar {dimension.value}"],
                    supporting_evidence=[f"Score actual: {score:.2f}"],
                    priority=1.0 - score,
                    timestamp=datetime.now()
                )
                insights.append(insight)
        
        # Identificar dimensiones con scores altos
        for dimension, score in dimensional_scores.items():
            if score > 0.8:
                insight = ReflectionInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType.SUCCESS_PATTERN,
                    dimension=dimension,
                    level=ReflectionLevel.TASK_LEVEL,
                    title=f"Fortaleza en {dimension.value}",
                    description=f"La dimensión {dimension.value} tiene un score alto ({score:.2f})",
                    confidence=0.8,
                    actionable_recommendations=[f"Continuar aplicando estrategias exitosas en {dimension.value}"],
                    supporting_evidence=[f"Score actual: {score:.2f}"],
                    priority=score,
                    timestamp=datetime.now()
                )
                insights.append(insight)
        
        return insights
    
    async def _perform_metacognition_analysis(self, 
                                            context: ExecutionContext,
                                            insights: List[ReflectionInsight]) -> Dict[str, Any]:
        """Realizar análisis de metacognición"""
        
        if not self.enable_metacognition:
            return {'learning_points': []}
        
        try:
            # Analizar proceso de pensamiento
            thinking_patterns = await self._analyze_thinking_patterns(context)
            
            # Analizar toma de decisiones
            decision_quality = await self._analyze_decision_quality(context)
            
            # Analizar adaptabilidad
            adaptability_patterns = await self._analyze_adaptability_patterns(context)
            
            # Generar learning points
            learning_points = []
            learning_points.extend(thinking_patterns.get('learning_points', []))
            learning_points.extend(decision_quality.get('learning_points', []))
            learning_points.extend(adaptability_patterns.get('learning_points', []))
            
            return {
                'learning_points': learning_points,
                'thinking_patterns': thinking_patterns,
                'decision_quality': decision_quality,
                'adaptability_patterns': adaptability_patterns
            }
            
        except Exception as e:
            logger.warning(f"Error en análisis de metacognición: {str(e)}")
            return {'learning_points': []}
    
    async def _analyze_thinking_patterns(self, context: ExecutionContext) -> Dict[str, Any]:
        """Analizar patrones de pensamiento"""
        
        patterns = {
            'planning_quality': 0.0,
            'tool_selection': 0.0,
            'problem_solving': 0.0,
            'learning_points': []
        }
        
        # Analizar calidad de planificación
        if context.execution_plan.strategy == ExecutionStrategy.COMPREHENSIVE:
            patterns['planning_quality'] = 0.8
            patterns['learning_points'].append("Estrategia comprehensiva muestra planificación detallada")
        elif context.execution_plan.strategy == ExecutionStrategy.ADAPTIVE:
            patterns['planning_quality'] = 0.9
            patterns['learning_points'].append("Estrategia adaptiva muestra flexibilidad en planificación")
        
        # Analizar selección de herramientas
        tools_used = set(se.step.tool for se in context.step_executions)
        if len(tools_used) > 3:
            patterns['tool_selection'] = 0.8
            patterns['learning_points'].append("Diversidad de herramientas indica pensamiento versátil")
        
        # Analizar resolución de problemas
        if context.variables.get('replanning_attempts', 0) > 0:
            patterns['problem_solving'] = 0.9
            patterns['learning_points'].append("Uso de replanificación muestra capacidad de resolución de problemas")
        
        return patterns
    
    async def _analyze_decision_quality(self, context: ExecutionContext) -> Dict[str, Any]:
        """Analizar calidad de toma de decisiones"""
        
        quality = {
            'strategic_decisions': 0.0,
            'tactical_decisions': 0.0,
            'learning_points': []
        }
        
        # Analizar decisiones estratégicas
        if context.success_rate > 0.8:
            quality['strategic_decisions'] = 0.8
            quality['learning_points'].append("Decisiones estratégicas resultaron en alta tasa de éxito")
        
        # Analizar decisiones tácticas
        retry_efficiency = 1.0 - min(sum(se.retry_count for se in context.step_executions) / len(context.step_executions), 1.0)
        quality['tactical_decisions'] = retry_efficiency
        if retry_efficiency > 0.7:
            quality['learning_points'].append("Decisiones tácticas eficientes con pocos reintentos")
        
        return quality
    
    async def _analyze_adaptability_patterns(self, context: ExecutionContext) -> Dict[str, Any]:
        """Analizar patrones de adaptabilidad"""
        
        adaptability = {
            'flexibility_score': 0.0,
            'recovery_capability': 0.0,
            'learning_points': []
        }
        
        # Analizar flexibilidad
        if context.variables.get('plan_modifications', 0) > 0:
            adaptability['flexibility_score'] = 0.8
            adaptability['learning_points'].append("Modificaciones de plan muestran flexibilidad")
        
        # Analizar capacidad de recuperación
        failed_steps = sum(1 for se in context.step_executions if se.status == StepStatus.FAILED)
        if failed_steps > 0 and context.success_rate > 0.5:
            adaptability['recovery_capability'] = 0.9
            adaptability['learning_points'].append("Buena capacidad de recuperación ante fallos")
        
        return adaptability
    
    async def _identify_patterns(self, 
                               context: ExecutionContext,
                               insights: List[ReflectionInsight]) -> Dict[str, Any]:
        """Identificar patrones en ejecución"""
        
        patterns = {
            'success_patterns': [],
            'failure_patterns': [],
            'efficiency_patterns': [],
            'learning_patterns': []
        }
        
        # Identificar patrones de éxito
        if context.success_rate > 0.8:
            success_key = f"{context.execution_plan.strategy.value}_{len(context.step_executions)}"
            self.success_patterns[success_key] += 1
            patterns['success_patterns'].append({
                'pattern': success_key,
                'frequency': self.success_patterns[success_key],
                'description': f"Estrategia {context.execution_plan.strategy.value} con {len(context.step_executions)} pasos"
            })
        
        # Identificar patrones de fallo
        if context.success_rate < 0.5:
            failure_key = f"failure_{context.execution_plan.strategy.value}"
            self.failure_patterns[failure_key] += 1
            patterns['failure_patterns'].append({
                'pattern': failure_key,
                'frequency': self.failure_patterns[failure_key],
                'description': f"Fallos con estrategia {context.execution_plan.strategy.value}"
            })
        
        # Identificar patrones de eficiencia
        if context.total_execution_time < context.execution_plan.total_estimated_duration:
            patterns['efficiency_patterns'].append({
                'pattern': 'faster_than_expected',
                'description': 'Ejecución más rápida que lo estimado',
                'time_saved': context.execution_plan.total_estimated_duration - context.total_execution_time
            })
        
        return patterns
    
    async def _calculate_overall_performance(self, 
                                           dimensional_scores: Dict[ReflectionDimension, float],
                                           insights: List[ReflectionInsight]) -> float:
        """Calcular puntuación general de rendimiento"""
        
        # Pesos para cada dimensión
        weights = {
            ReflectionDimension.TASK_QUALITY: 0.25,
            ReflectionDimension.EXECUTION_EFFICIENCY: 0.20,
            ReflectionDimension.RESOURCE_UTILIZATION: 0.15,
            ReflectionDimension.ERROR_HANDLING: 0.15,
            ReflectionDimension.LEARNING_OUTCOMES: 0.10,
            ReflectionDimension.USER_SATISFACTION: 0.10,
            ReflectionDimension.STRATEGIC_THINKING: 0.03,
            ReflectionDimension.ADAPTABILITY: 0.02
        }
        
        # Calcular score ponderado
        weighted_score = sum(
            dimensional_scores.get(dim, 0.0) * weight
            for dim, weight in weights.items()
        )
        
        # Ajustar por insights positivos y negativos
        positive_insights = sum(1 for insight in insights if insight.type == InsightType.SUCCESS_PATTERN)
        negative_insights = sum(1 for insight in insights if insight.type == InsightType.FAILURE_PATTERN)
        
        insight_adjustment = (positive_insights - negative_insights) * 0.05
        
        return max(0.0, min(1.0, weighted_score + insight_adjustment))
    
    async def _generate_recommendations(self, 
                                      insights: List[ReflectionInsight],
                                      patterns: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generar recomendaciones basadas en insights y patrones"""
        
        recommendations = {
            'improvement_actions': [],
            'strengths': [],
            'weaknesses': [],
            'strategic': []
        }
        
        # Procesar insights
        for insight in insights:
            if insight.type == InsightType.IMPROVEMENT_OPPORTUNITY:
                recommendations['improvement_actions'].extend(insight.actionable_recommendations)
                recommendations['weaknesses'].append(insight.title)
            elif insight.type == InsightType.SUCCESS_PATTERN:
                recommendations['strengths'].append(insight.title)
            elif insight.type == InsightType.STRATEGIC_INSIGHT:
                recommendations['strategic'].extend(insight.actionable_recommendations)
        
        # Procesar patrones
        for pattern in patterns.get('success_patterns', []):
            recommendations['strengths'].append(f"Patrón exitoso: {pattern['description']}")
        
        for pattern in patterns.get('failure_patterns', []):
            recommendations['weaknesses'].append(f"Patrón problemático: {pattern['description']}")
        
        return recommendations
    
    def _calculate_confidence(self, insights: List[ReflectionInsight]) -> float:
        """Calcular confianza en la reflexión"""
        
        if not insights:
            return 0.5
        
        # Promedio de confianza de insights
        avg_confidence = statistics.mean(insight.confidence for insight in insights)
        
        # Ajustar por cantidad de insights
        quantity_factor = min(len(insights) / 10, 1.0)
        
        return avg_confidence * quantity_factor
    
    async def _record_reflection_in_memory(self, reflection_result: ReflectionResult):
        """Registrar reflexión en memoria para aprendizaje"""
        
        try:
            # Preparar datos para memoria
            reflection_data = {
                'type': 'self_reflection',
                'timestamp': reflection_result.timestamp.isoformat(),
                'task_id': reflection_result.task_id,
                'reflection_id': reflection_result.reflection_id,
                'overall_score': reflection_result.overall_performance_score,
                'dimensional_scores': {dim.value: score for dim, score in reflection_result.dimensional_scores.items()},
                'insights_count': len(reflection_result.insights),
                'learning_points': reflection_result.learning_points,
                'improvement_actions': reflection_result.improvement_actions,
                'strengths': reflection_result.strengths_identified,
                'weaknesses': reflection_result.weaknesses_identified,
                'strategic_recommendations': reflection_result.strategic_recommendations,
                'confidence': reflection_result.confidence_score
            }
            
            # Almacenar en memoria episódica
            if self.memory_manager.is_initialized:
                from src.memory.episodic_memory_store import Episode
                
                episode = Episode(
                    id=str(uuid.uuid4()),
                    title=f"Auto-reflexión: Task {reflection_result.task_id}",
                    description=f"Reflexión sobre rendimiento con score {reflection_result.overall_performance_score:.2f}",
                    context=reflection_data,
                    actions=[{
                        'type': 'self_reflection',
                        'score': reflection_result.overall_performance_score,
                        'timestamp': datetime.now().isoformat()
                    }],
                    outcomes=[{
                        'type': 'learning_outcomes',
                        'insights_generated': len(reflection_result.insights),
                        'improvements_identified': len(reflection_result.improvement_actions),
                        'timestamp': datetime.now().isoformat()
                    }],
                    timestamp=datetime.now(),
                    success=reflection_result.overall_performance_score > 0.6,
                    importance=5,  # Muy alta importancia para aprendizaje
                    tags=['self_reflection', 'metacognition', 'performance_analysis']
                )
                
                await self.memory_manager.episodic_memory.store_episode(episode)
                logger.info("🧠 Reflexión almacenada en memoria episódica")
            
            # También almacenar insights como conocimiento semántico
            for insight in reflection_result.insights:
                fact_id = f"insight_{insight.dimension.value}_{insight.type.value}"
                await self.memory_manager.semantic_memory.store_fact(
                    fact_id,
                    {
                        'insight_type': insight.type.value,
                        'dimension': insight.dimension.value,
                        'title': insight.title,
                        'description': insight.description,
                        'recommendations': insight.actionable_recommendations,
                        'confidence': insight.confidence,
                        'priority': insight.priority
                    },
                    source="self_reflection_engine",
                    confidence=insight.confidence
                )
            
        except Exception as e:
            logger.warning(f"Error almacenando reflexión en memoria: {str(e)}")
    
    async def _update_statistics(self, reflection_result: ReflectionResult):
        """Actualizar estadísticas del motor"""
        
        # Actualizar promedio de performance
        self.average_performance_score = (
            (self.average_performance_score * (self.reflections_performed - 1) + 
             reflection_result.overall_performance_score) / self.reflections_performed
        )
        
        # Actualizar historial de mejoras
        self.improvement_history.append({
            'timestamp': reflection_result.timestamp,
            'score': reflection_result.overall_performance_score,
            'improvements': len(reflection_result.improvement_actions)
        })
        
        # Mantener solo últimas 100 reflexiones
        if len(self.improvement_history) > 100:
            self.improvement_history = self.improvement_history[-100:]
    
    async def _apply_automatic_improvements(self, reflection_result: ReflectionResult):
        """Aplicar mejoras automáticas basadas en reflexión"""
        
        try:
            # Aplicar mejoras de alta prioridad automáticamente
            high_priority_insights = [
                insight for insight in reflection_result.insights 
                if insight.priority > 0.8 and insight.type == InsightType.IMPROVEMENT_OPPORTUNITY
            ]
            
            for insight in high_priority_insights:
                # Simular aplicación de mejora
                # En implementación real, aquí se aplicarían las mejoras específicas
                logger.info(f"🔧 Aplicando mejora automática: {insight.title}")
                self.improvements_implemented += 1
                
        except Exception as e:
            logger.warning(f"Error aplicando mejoras automáticas: {str(e)}")
    
    async def _calculate_complexity_score(self, context: ExecutionContext) -> float:
        """Calcular score de complejidad de la tarea"""
        
        factors = []
        
        # Factor de número de pasos
        steps_factor = min(len(context.step_executions) / 10, 1.0)
        factors.append(steps_factor)
        
        # Factor de diversidad de herramientas
        tools_used = set(se.step.tool for se in context.step_executions)
        tools_factor = min(len(tools_used) / 5, 1.0)
        factors.append(tools_factor)
        
        # Factor de dependencias
        total_dependencies = sum(len(se.step.dependencies) for se in context.step_executions)
        deps_factor = min(total_dependencies / (len(context.step_executions) * 2), 1.0)
        factors.append(deps_factor)
        
        return statistics.mean(factors)
    
    async def _calculate_innovation_score(self, context: ExecutionContext) -> float:
        """Calcular score de innovación"""
        
        # Uso de replanificación como indicador de innovación
        replanning_used = context.variables.get('replanning_attempts', 0) > 0
        
        # Uso de herramientas menos comunes
        common_tools = {'shell', 'file_manager', 'web_search'}
        tools_used = set(se.step.tool for se in context.step_executions)
        uncommon_tools = tools_used - common_tools
        
        innovation_factors = []
        innovation_factors.append(0.8 if replanning_used else 0.2)
        innovation_factors.append(min(len(uncommon_tools) / 3, 1.0))
        
        return statistics.mean(innovation_factors)
    
    async def _calculate_resource_efficiency(self, metrics: ReflectionMetrics) -> float:
        """Calcular eficiencia de recursos"""
        
        # Eficiencia basada en uso de recursos
        factors = []
        
        # Eficiencia de tiempo
        if metrics.execution_time > 0:
            time_efficiency = min(300 / metrics.execution_time, 1.0)  # 5 minutos como baseline
            factors.append(time_efficiency)
        
        # Eficiencia de API calls
        api_calls = metrics.resources_consumed.get('api_calls', 0)
        if api_calls > 0:
            api_efficiency = min(10 / api_calls, 1.0)  # 10 calls como baseline
            factors.append(api_efficiency)
        
        return statistics.mean(factors) if factors else 0.5
    
    async def _calculate_error_handling_score(self, context: ExecutionContext) -> float:
        """Calcular score de manejo de errores"""
        
        failed_steps = sum(1 for se in context.step_executions if se.status == StepStatus.FAILED)
        total_steps = len(context.step_executions)
        
        if failed_steps == 0:
            return 1.0
        
        # Score basado en recuperación
        recovery_score = context.success_rate  # Si se recuperó, el success rate será mayor
        
        # Bonus por usar replanificación
        if context.variables.get('replanning_attempts', 0) > 0:
            recovery_score += 0.2
        
        return min(recovery_score, 1.0)
    
    async def _calculate_learning_score(self, context: ExecutionContext) -> float:
        """Calcular score de aprendizaje"""
        
        # Factores de aprendizaje
        factors = []
        
        # Uso de memoria
        if context.variables.get('memory_used', False):
            factors.append(0.8)
        
        # Aplicación de mejoras
        if context.variables.get('improvements_applied', 0) > 0:
            factors.append(0.9)
        
        # Adaptación durante ejecución
        if context.variables.get('plan_modifications', 0) > 0:
            factors.append(0.7)
        
        return statistics.mean(factors) if factors else 0.5
    
    async def _calculate_strategic_thinking_score(self, context: ExecutionContext) -> float:
        """Calcular score de pensamiento estratégico"""
        
        # Factores estratégicos
        factors = []
        
        # Selección de estrategia apropiada
        if context.execution_plan.strategy == ExecutionStrategy.ADAPTIVE:
            factors.append(0.9)
        elif context.execution_plan.strategy == ExecutionStrategy.COMPREHENSIVE:
            factors.append(0.8)
        else:
            factors.append(0.6)
        
        # Planificación proactiva
        if context.execution_plan.total_estimated_duration > 0:
            factors.append(0.7)
        
        return statistics.mean(factors) if factors else 0.5
    
    async def _calculate_adaptability_score(self, context: ExecutionContext) -> float:
        """Calcular score de adaptabilidad"""
        
        # Factores de adaptabilidad
        adaptability_indicators = []
        
        # Replanificación exitosa
        if context.variables.get('replanning_attempts', 0) > 0:
            adaptability_indicators.append(0.9)
        
        # Recuperación de errores
        if context.success_rate > 0.5 and sum(1 for se in context.step_executions if se.status == StepStatus.FAILED) > 0:
            adaptability_indicators.append(0.8)
        
        # Modificaciones de plan
        if context.variables.get('plan_modifications', 0) > 0:
            adaptability_indicators.append(0.7)
        
        return statistics.mean(adaptability_indicators) if adaptability_indicators else 0.5
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del motor de reflexión"""
        
        return {
            'reflections_performed': self.reflections_performed,
            'insights_generated': self.insights_generated,
            'improvements_implemented': self.improvements_implemented,
            'average_performance_score': self.average_performance_score,
            'success_patterns_count': len(self.success_patterns),
            'failure_patterns_count': len(self.failure_patterns),
            'recent_performance_trend': self._calculate_performance_trend(),
            'top_success_patterns': dict(sorted(self.success_patterns.items(), key=lambda x: x[1], reverse=True)[:5]),
            'top_failure_patterns': dict(sorted(self.failure_patterns.items(), key=lambda x: x[1], reverse=True)[:5]),
            'configuration': {
                'min_reflection_interval': self.min_reflection_interval,
                'enable_deep_reflection': self.enable_deep_reflection,
                'enable_metacognition': self.enable_metacognition,
                'reflection_depth': self.reflection_depth
            }
        }
    
    def _calculate_performance_trend(self) -> str:
        """Calcular tendencia de rendimiento"""
        
        if len(self.improvement_history) < 2:
            return "insufficient_data"
        
        recent_scores = [entry['score'] for entry in self.improvement_history[-10:]]
        if len(recent_scores) < 2:
            return "insufficient_data"
        
        avg_recent = statistics.mean(recent_scores)
        avg_older = statistics.mean([entry['score'] for entry in self.improvement_history[-20:-10]]) if len(self.improvement_history) >= 20 else avg_recent
        
        if avg_recent > avg_older + 0.1:
            return "improving"
        elif avg_recent < avg_older - 0.1:
            return "declining"
        else:
            return "stable"
    
    def reset_statistics(self):
        """Resetear estadísticas"""
        self.reflections_performed = 0
        self.insights_generated = 0
        self.improvements_implemented = 0
        self.average_performance_score = 0.0
        self.success_patterns.clear()
        self.failure_patterns.clear()
        self.improvement_history.clear()
        logger.info("🧠 Estadísticas de reflexión reseteadas")