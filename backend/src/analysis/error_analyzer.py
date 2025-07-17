"""
ErrorAnalyzer - Análisis Sofisticado de Errores para Mitosis V5
===============================================================

Este módulo implementa análisis profundo de errores para informar replanificación y aprendizaje.
Categoriza errores, analiza causas raíz y proporciona recomendaciones estratégicas.

Características clave:
- Análisis de causas raíz de errores
- Categorización inteligente de tipos de errores
- Detección de patrones de errores
- Recomendaciones para prevención
- Integración con sistema de memoria
- Métricas de calidad de análisis
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import re
import statistics
from collections import defaultdict, Counter

# Forward references to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.tools.execution_engine import ExecutionContext, StepExecution, StepStatus

from src.memory.advanced_memory_manager import AdvancedMemoryManager
from src.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Severidad de errores"""
    LOW = "low"                    # Error menor, recuperable
    MEDIUM = "medium"              # Error moderado, afecta rendimiento
    HIGH = "high"                  # Error grave, afecta funcionalidad
    CRITICAL = "critical"          # Error crítico, falla total

class ErrorType(Enum):
    """Tipos de errores"""
    SYSTEM_ERROR = "system_error"              # Error del sistema
    TOOL_ERROR = "tool_error"                  # Error de herramienta
    PARAMETER_ERROR = "parameter_error"        # Error de parámetros
    NETWORK_ERROR = "network_error"            # Error de red
    TIMEOUT_ERROR = "timeout_error"            # Error de timeout
    PERMISSION_ERROR = "permission_error"      # Error de permisos
    RESOURCE_ERROR = "resource_error"          # Error de recursos
    LOGIC_ERROR = "logic_error"                # Error lógico
    DATA_ERROR = "data_error"                  # Error de datos
    INTEGRATION_ERROR = "integration_error"    # Error de integración

class ErrorPattern(Enum):
    """Patrones de errores"""
    RECURRING = "recurring"                    # Error recurrente
    CASCADING = "cascading"                    # Error en cascada
    INTERMITTENT = "intermittent"              # Error intermitente
    SYSTEMATIC = "systematic"                  # Error sistemático
    ENVIRONMENTAL = "environmental"            # Error ambiental
    DEPENDENCY = "dependency"                  # Error de dependencia

class AnalysisDepth(Enum):
    """Profundidad de análisis"""
    BASIC = "basic"                # Análisis básico
    DETAILED = "detailed"          # Análisis detallado
    COMPREHENSIVE = "comprehensive"  # Análisis comprehensivo
    DEEP = "deep"                  # Análisis profundo

@dataclass
class ErrorContext:
    """Contexto de error para análisis"""
    execution_context: 'ExecutionContext'
    failed_step: 'StepExecution'
    error_message: str
    error_type: str
    stack_trace: Optional[str] = None
    system_state: Dict[str, Any] = field(default_factory=dict)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    related_errors: List[Dict[str, Any]] = field(default_factory=list)
    
@dataclass
class RootCause:
    """Causa raíz identificada"""
    id: str
    category: str
    description: str
    confidence: float
    evidence: List[str]
    contributing_factors: List[str]
    impact_assessment: str
    
@dataclass
class ErrorAnalysisResult:
    """Resultado del análisis de errores"""
    error_id: str
    analysis_timestamp: datetime
    error_type: ErrorType
    error_severity: ErrorSeverity
    error_pattern: ErrorPattern
    root_causes: List[RootCause]
    immediate_causes: List[str]
    contributing_factors: List[str]
    impact_analysis: Dict[str, Any]
    prevention_recommendations: List[str]
    recovery_strategies: List[str]
    similar_errors: List[Dict[str, Any]]
    confidence_score: float
    analysis_depth: AnalysisDepth
    
class ErrorAnalyzer:
    """Analizador sofisticado de errores"""
    
    def __init__(self, 
                 memory_manager: AdvancedMemoryManager,
                 ollama_service: OllamaService,
                 config: Dict[str, Any] = None):
        """
        Inicializar ErrorAnalyzer
        
        Args:
            memory_manager: Gestor de memoria avanzado
            ollama_service: Servicio LLM para análisis
            config: Configuración del analizador
        """
        self.memory_manager = memory_manager
        self.ollama_service = ollama_service
        self.config = config or {}
        
        # Configuración por defecto
        self.analysis_depth = AnalysisDepth(self.config.get('analysis_depth', 'detailed'))
        self.enable_pattern_detection = self.config.get('enable_pattern_detection', True)
        self.enable_llm_analysis = self.config.get('enable_llm_analysis', True)
        self.max_similar_errors = self.config.get('max_similar_errors', 5)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        
        # Estadísticas
        self.analyses_performed = 0
        self.patterns_detected = 0
        self.root_causes_found = 0
        self.prevention_success_rate = 0.0
        
        # Bases de conocimiento
        self.error_patterns = defaultdict(int)
        self.error_signatures = {}
        self.recovery_success_rates = {}
        
        # Reglas de análisis
        self.analysis_rules = self._initialize_analysis_rules()
        
        logger.info("🔍 ErrorAnalyzer inicializado")
    
    async def analyze_error(self, error_context: ErrorContext) -> ErrorAnalysisResult:
        """
        Analizar error de forma comprehensiva
        
        Args:
            error_context: Contexto del error
            
        Returns:
            Resultado del análisis
        """
        try:
            logger.info(f"🔍 Iniciando análisis de error: {error_context.error_message}")
            
            # Incrementar contador
            self.analyses_performed += 1
            
            # 1. Clasificar error
            error_type = await self._classify_error(error_context)
            error_severity = await self._assess_severity(error_context)
            
            # 2. Detectar patrones
            error_pattern = await self._detect_patterns(error_context)
            
            # 3. Buscar errores similares
            similar_errors = await self._find_similar_errors(error_context)
            
            # 4. Analizar causas raíz
            root_causes = await self._analyze_root_causes(error_context, similar_errors)
            
            # 5. Identificar causas inmediatas
            immediate_causes = await self._identify_immediate_causes(error_context)
            
            # 6. Analizar factores contribuyentes
            contributing_factors = await self._analyze_contributing_factors(error_context)
            
            # 7. Evaluar impacto
            impact_analysis = await self._assess_impact(error_context)
            
            # 8. Generar recomendaciones
            prevention_recommendations = await self._generate_prevention_recommendations(
                error_context, root_causes
            )
            
            # 9. Sugerir estrategias de recuperación
            recovery_strategies = await self._suggest_recovery_strategies(
                error_context, root_causes
            )
            
            # 10. Calcular confianza
            confidence_score = await self._calculate_confidence(
                error_context, root_causes, similar_errors
            )
            
            # 11. Crear resultado
            analysis_result = ErrorAnalysisResult(
                error_id=str(uuid.uuid4()),
                analysis_timestamp=datetime.now(),
                error_type=error_type,
                error_severity=error_severity,
                error_pattern=error_pattern,
                root_causes=root_causes,
                immediate_causes=immediate_causes,
                contributing_factors=contributing_factors,
                impact_analysis=impact_analysis,
                prevention_recommendations=prevention_recommendations,
                recovery_strategies=recovery_strategies,
                similar_errors=similar_errors,
                confidence_score=confidence_score,
                analysis_depth=self.analysis_depth
            )
            
            # 12. Registrar en memoria
            await self._record_analysis_in_memory(analysis_result)
            
            # 13. Actualizar estadísticas
            await self._update_statistics(analysis_result)
            
            logger.info(f"✅ Análisis completado con confianza: {confidence_score:.2f}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error en análisis: {str(e)}")
            return await self._generate_fallback_analysis(error_context)
    
    async def _classify_error(self, error_context: ErrorContext) -> ErrorType:
        """Clasificar tipo de error"""
        
        error_message = error_context.error_message.lower()
        
        # Clasificación basada en patrones
        if any(pattern in error_message for pattern in ['connection', 'network', 'host', 'dns']):
            return ErrorType.NETWORK_ERROR
        elif any(pattern in error_message for pattern in ['timeout', 'time out', 'timed out']):
            return ErrorType.TIMEOUT_ERROR
        elif any(pattern in error_message for pattern in ['permission', 'access', 'forbidden', 'unauthorized']):
            return ErrorType.PERMISSION_ERROR
        elif any(pattern in error_message for pattern in ['not found', 'missing', 'unavailable']):
            return ErrorType.TOOL_ERROR
        elif any(pattern in error_message for pattern in ['invalid', 'parameter', 'argument']):
            return ErrorType.PARAMETER_ERROR
        elif any(pattern in error_message for pattern in ['memory', 'disk', 'resource', 'limit']):
            return ErrorType.RESOURCE_ERROR
        elif any(pattern in error_message for pattern in ['api', 'service', 'integration']):
            return ErrorType.INTEGRATION_ERROR
        elif any(pattern in error_message for pattern in ['data', 'format', 'parsing']):
            return ErrorType.DATA_ERROR
        elif any(pattern in error_message for pattern in ['logic', 'assertion', 'validation']):
            return ErrorType.LOGIC_ERROR
        else:
            return ErrorType.SYSTEM_ERROR
    
    async def _assess_severity(self, error_context: ErrorContext) -> ErrorSeverity:
        """Evaluar severidad del error"""
        
        severity_factors = []
        
        # Factor 1: Impacto en ejecución
        if error_context.failed_step.status == StepStatus.FAILED:
            if error_context.execution_context.success_rate < 0.5:
                severity_factors.append(4)  # Crítico
            elif error_context.execution_context.success_rate < 0.8:
                severity_factors.append(3)  # Alto
            else:
                severity_factors.append(2)  # Medio
        
        # Factor 2: Recuperabilidad
        if error_context.failed_step.retry_count > 2:
            severity_factors.append(3)  # Difícil de recuperar
        elif error_context.failed_step.retry_count > 0:
            severity_factors.append(2)  # Parcialmente recuperable
        else:
            severity_factors.append(1)  # Fácilmente recuperable
        
        # Factor 3: Herramienta crítica
        critical_tools = ['system', 'database', 'authentication']
        if any(tool in error_context.failed_step.step.tool.lower() for tool in critical_tools):
            severity_factors.append(4)
        
        # Factor 4: Errores en cascada
        if len(error_context.related_errors) > 2:
            severity_factors.append(3)
        
        # Calcular severidad promedio
        avg_severity = statistics.mean(severity_factors)
        
        if avg_severity >= 3.5:
            return ErrorSeverity.CRITICAL
        elif avg_severity >= 2.5:
            return ErrorSeverity.HIGH
        elif avg_severity >= 1.5:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    async def _detect_patterns(self, error_context: ErrorContext) -> ErrorPattern:
        """Detectar patrones de errores"""
        
        if not self.enable_pattern_detection:
            return ErrorPattern.SYSTEMATIC
        
        # Analizar historial de errores similares
        error_signature = self._create_error_signature(error_context)
        
        # Contar ocurrencias
        if error_signature in self.error_signatures:
            occurrence_count = self.error_signatures[error_signature]
            
            # Determinar patrón basado en frecuencia
            if occurrence_count > 5:
                return ErrorPattern.RECURRING
            elif occurrence_count > 2:
                return ErrorPattern.INTERMITTENT
        
        # Analizar errores relacionados
        if len(error_context.related_errors) > 1:
            return ErrorPattern.CASCADING
        
        # Analizar contexto ambiental
        if error_context.environment_info.get('unstable_network', False):
            return ErrorPattern.ENVIRONMENTAL
        
        # Analizar dependencias
        if error_context.failed_step.step.dependencies:
            return ErrorPattern.DEPENDENCY
        
        return ErrorPattern.SYSTEMATIC
    
    def _create_error_signature(self, error_context: ErrorContext) -> str:
        """Crear firma única del error"""
        
        # Combinar elementos clave
        elements = [
            error_context.failed_step.step.tool,
            error_context.error_type[:20],  # Primeros 20 caracteres
            str(len(error_context.failed_step.step.dependencies))
        ]
        
        return '_'.join(elements)
    
    async def _find_similar_errors(self, error_context: ErrorContext) -> List[Dict[str, Any]]:
        """Buscar errores similares en memoria"""
        
        similar_errors = []
        
        try:
            # Buscar en memoria semántica
            if self.memory_manager.is_initialized:
                search_query = f"error {error_context.error_message[:50]}"
                
                similar_episodes = await self.memory_manager.semantic_memory.semantic_search(
                    query=search_query,
                    max_results=self.max_similar_errors
                )
                
                for episode in similar_episodes:
                    if episode.get('type') == 'error_analysis':
                        similar_errors.append({
                            'error_type': episode.get('error_type', 'unknown'),
                            'solution': episode.get('solution', 'No solution recorded'),
                            'success_rate': episode.get('recovery_success_rate', 0.0),
                            'timestamp': episode.get('timestamp', ''),
                            'similarity_score': episode.get('similarity_score', 0.0)
                        })
        
        except Exception as e:
            logger.warning(f"Error buscando errores similares: {str(e)}")
        
        return similar_errors
    
    async def _analyze_root_causes(self, 
                                 error_context: ErrorContext,
                                 similar_errors: List[Dict[str, Any]]) -> List[RootCause]:
        """Analizar causas raíz del error"""
        
        root_causes = []
        
        # Análisis usando LLM si está habilitado
        if self.enable_llm_analysis:
            llm_causes = await self._analyze_root_causes_with_llm(error_context, similar_errors)
            root_causes.extend(llm_causes)
        
        # Análisis basado en reglas
        rule_causes = await self._analyze_root_causes_with_rules(error_context)
        root_causes.extend(rule_causes)
        
        # Análisis basado en patrones históricos
        pattern_causes = await self._analyze_root_causes_with_patterns(error_context, similar_errors)
        root_causes.extend(pattern_causes)
        
        # Eliminar duplicados y ordenar por confianza
        unique_causes = {}
        for cause in root_causes:
            if cause.id not in unique_causes or cause.confidence > unique_causes[cause.id].confidence:
                unique_causes[cause.id] = cause
        
        return sorted(unique_causes.values(), key=lambda x: x.confidence, reverse=True)
    
    async def _analyze_root_causes_with_llm(self, 
                                          error_context: ErrorContext,
                                          similar_errors: List[Dict[str, Any]]) -> List[RootCause]:
        """Analizar causas raíz usando LLM"""
        
        try:
            # Construir prompt para análisis
            prompt = self._build_root_cause_prompt(error_context, similar_errors)
            
            # Generar análisis con LLM
            response = await self.ollama_service.generate_response(prompt, {
                'max_tokens': 800,
                'temperature': 0.2,
                'task_type': 'error_analysis'
            })
            
            if response.get('error'):
                logger.warning(f"Error en análisis LLM: {response['error']}")
                return []
            
            # Parsear respuesta
            analysis_text = response.get('response', '')
            return self._parse_llm_root_causes(analysis_text)
            
        except Exception as e:
            logger.warning(f"Error en análisis LLM de causas raíz: {str(e)}")
            return []
    
    def _build_root_cause_prompt(self, 
                               error_context: ErrorContext,
                               similar_errors: List[Dict[str, Any]]) -> str:
        """Construir prompt para análisis de causas raíz"""
        
        similar_errors_text = '\n'.join([
            f"- {error.get('error_type', 'unknown')}: {error.get('solution', 'No solution')}"
            for error in similar_errors[:3]
        ])
        
        return f"""
Analiza el siguiente error y determina las causas raíz más probables:

**ERROR INFORMACIÓN:**
- Mensaje: {error_context.error_message}
- Tipo: {error_context.error_type}
- Herramienta: {error_context.failed_step.step.tool}
- Parámetros: {json.dumps(error_context.failed_step.step.parameters, indent=2)}
- Reintentos: {error_context.failed_step.retry_count}

**CONTEXTO DE EJECUCIÓN:**
- Pasos totales: {len(error_context.execution_context.step_executions)}
- Tasa de éxito: {error_context.execution_context.success_rate:.2f}
- Tiempo total: {error_context.execution_context.total_execution_time:.2f}s

**ERRORES SIMILARES HISTÓRICOS:**
{similar_errors_text}

**ANÁLISIS REQUERIDO:**
1. Identifica 2-3 causas raíz más probables
2. Proporciona evidencia específica para cada causa
3. Evalúa factores contribuyentes
4. Asigna nivel de confianza (0-1)
5. Sugiere estrategias de prevención

Responde en formato JSON:
{{
  "root_causes": [
    {{
      "id": "cause_1",
      "category": "technical|operational|environmental|human",
      "description": "Descripción detallada",
      "confidence": 0.85,
      "evidence": ["evidencia1", "evidencia2"],
      "contributing_factors": ["factor1", "factor2"],
      "impact_assessment": "Descripción del impacto",
      "prevention_strategy": "Estrategia de prevención"
    }}
  ]
}}
"""
    
    def _parse_llm_root_causes(self, analysis_text: str) -> List[RootCause]:
        """Parsear causas raíz del LLM"""
        
        try:
            # Limpiar y parsear JSON
            if analysis_text.strip().startswith('{'):
                parsed = json.loads(analysis_text)
            else:
                return []
            
            root_causes = []
            for cause_data in parsed.get('root_causes', []):
                cause = RootCause(
                    id=cause_data.get('id', f'cause_{len(root_causes)}'),
                    category=cause_data.get('category', 'technical'),
                    description=cause_data.get('description', ''),
                    confidence=cause_data.get('confidence', 0.5),
                    evidence=cause_data.get('evidence', []),
                    contributing_factors=cause_data.get('contributing_factors', []),
                    impact_assessment=cause_data.get('impact_assessment', '')
                )
                root_causes.append(cause)
            
            return root_causes
            
        except json.JSONDecodeError:
            logger.warning("Error parseando análisis LLM de causas raíz")
            return []
    
    async def _analyze_root_causes_with_rules(self, error_context: ErrorContext) -> List[RootCause]:
        """Analizar causas raíz usando reglas"""
        
        rule_causes = []
        
        # Aplicar reglas de análisis
        for rule in self.analysis_rules:
            if rule['condition'](error_context):
                cause = RootCause(
                    id=rule['id'],
                    category=rule['category'],
                    description=rule['description'],
                    confidence=rule['confidence'],
                    evidence=rule['evidence_generator'](error_context),
                    contributing_factors=rule['factors_generator'](error_context),
                    impact_assessment=rule['impact_assessment']
                )
                rule_causes.append(cause)
        
        return rule_causes
    
    async def _analyze_root_causes_with_patterns(self, 
                                               error_context: ErrorContext,
                                               similar_errors: List[Dict[str, Any]]) -> List[RootCause]:
        """Analizar causas raíz usando patrones históricos"""
        
        pattern_causes = []
        
        # Analizar patrones en errores similares
        if similar_errors:
            # Agrupar por tipo de solución
            solution_groups = defaultdict(list)
            for error in similar_errors:
                solution = error.get('solution', 'unknown')
                solution_groups[solution].append(error)
            
            # Identificar patrones comunes
            for solution, errors in solution_groups.items():
                if len(errors) > 1:  # Patrón recurrente
                    avg_success_rate = statistics.mean(
                        e.get('success_rate', 0.0) for e in errors
                    )
                    
                    if avg_success_rate > 0.6:  # Solución efectiva
                        cause = RootCause(
                            id=f"pattern_{solution.replace(' ', '_')[:20]}",
                            category='pattern',
                            description=f"Patrón recurrente: {solution}",
                            confidence=min(avg_success_rate, 0.8),
                            evidence=[f"Encontrado en {len(errors)} casos similares"],
                            contributing_factors=['Patrón histórico recurrente'],
                            impact_assessment=f"Impacto similar en {len(errors)} casos"
                        )
                        pattern_causes.append(cause)
        
        return pattern_causes
    
    def _initialize_analysis_rules(self) -> List[Dict[str, Any]]:
        """Inicializar reglas de análisis"""
        
        rules = [
            {
                'id': 'network_connectivity_issue',
                'category': 'technical',
                'description': 'Problema de conectividad de red',
                'confidence': 0.9,
                'condition': lambda ctx: any(
                    word in ctx.error_message.lower() 
                    for word in ['connection', 'network', 'host', 'dns']
                ),
                'evidence_generator': lambda ctx: [
                    'Mensaje de error contiene términos de red',
                    f'Herramienta afectada: {ctx.failed_step.step.tool}'
                ],
                'factors_generator': lambda ctx: [
                    'Conectividad de red',
                    'Configuración de firewall',
                    'Resolución DNS'
                ],
                'impact_assessment': 'Impacto en herramientas que requieren conectividad'
            },
            {
                'id': 'insufficient_permissions',
                'category': 'operational',
                'description': 'Permisos insuficientes para ejecutar operación',
                'confidence': 0.85,
                'condition': lambda ctx: any(
                    word in ctx.error_message.lower()
                    for word in ['permission', 'access', 'forbidden', 'unauthorized']
                ),
                'evidence_generator': lambda ctx: [
                    'Mensaje de error indica problema de permisos',
                    f'Operación: {ctx.failed_step.step.tool}'
                ],
                'factors_generator': lambda ctx: [
                    'Configuración de permisos',
                    'Autenticación de usuario',
                    'Políticas de seguridad'
                ],
                'impact_assessment': 'Impacto en operaciones que requieren privilegios'
            },
            {
                'id': 'resource_exhaustion',
                'category': 'environmental',
                'description': 'Agotamiento de recursos del sistema',
                'confidence': 0.8,
                'condition': lambda ctx: any(
                    word in ctx.error_message.lower()
                    for word in ['memory', 'disk', 'resource', 'limit']
                ),
                'evidence_generator': lambda ctx: [
                    'Mensaje de error indica agotamiento de recursos',
                    f'Contexto del sistema: {ctx.system_state}'
                ],
                'factors_generator': lambda ctx: [
                    'Uso de memoria',
                    'Espacio en disco',
                    'Límites del sistema'
                ],
                'impact_assessment': 'Impacto en rendimiento general del sistema'
            },
            {
                'id': 'invalid_parameters',
                'category': 'technical',
                'description': 'Parámetros inválidos o incorrectos',
                'confidence': 0.75,
                'condition': lambda ctx: any(
                    word in ctx.error_message.lower()
                    for word in ['invalid', 'parameter', 'argument', 'format']
                ),
                'evidence_generator': lambda ctx: [
                    'Mensaje de error indica problema con parámetros',
                    f'Parámetros utilizados: {ctx.failed_step.step.parameters}'
                ],
                'factors_generator': lambda ctx: [
                    'Validación de entrada',
                    'Formato de datos',
                    'Configuración de herramienta'
                ],
                'impact_assessment': 'Impacto en funcionalidad específica'
            }
        ]
        
        return rules
    
    async def _identify_immediate_causes(self, error_context: ErrorContext) -> List[str]:
        """Identificar causas inmediatas"""
        
        immediate_causes = []
        
        # Análisis del mensaje de error
        error_message = error_context.error_message.lower()
        
        # Causas inmediatas comunes
        if 'not found' in error_message:
            immediate_causes.append('Recurso o archivo no encontrado')
        
        if 'timeout' in error_message:
            immediate_causes.append('Operación excedió tiempo límite')
        
        if 'connection' in error_message:
            immediate_causes.append('Falla en conexión')
        
        if 'permission' in error_message:
            immediate_causes.append('Acceso denegado')
        
        if 'invalid' in error_message:
            immediate_causes.append('Entrada o parámetro inválido')
        
        # Análisis del contexto de ejecución
        if error_context.failed_step.retry_count > 0:
            immediate_causes.append(f'Falla después de {error_context.failed_step.retry_count} reintentos')
        
        if error_context.failed_step.step.dependencies:
            immediate_causes.append('Posible falla en dependencias')
        
        return immediate_causes
    
    async def _analyze_contributing_factors(self, error_context: ErrorContext) -> List[str]:
        """Analizar factores contribuyentes"""
        
        factors = []
        
        # Factores del sistema
        if error_context.system_state.get('high_memory_usage', False):
            factors.append('Alto uso de memoria del sistema')
        
        if error_context.system_state.get('high_cpu_usage', False):
            factors.append('Alto uso de CPU')
        
        # Factores ambientales
        if error_context.environment_info.get('unstable_network', False):
            factors.append('Conectividad de red inestable')
        
        if error_context.environment_info.get('maintenance_mode', False):
            factors.append('Sistema en modo mantenimiento')
        
        # Factores de ejecución
        if error_context.execution_context.success_rate < 0.5:
            factors.append('Baja tasa de éxito general')
        
        if error_context.execution_context.total_execution_time > 300:  # 5 minutos
            factors.append('Tiempo de ejecución prolongado')
        
        # Factores de herramientas
        if error_context.failed_step.step.tool in ['web_search', 'enhanced_web_search']:
            factors.append('Dependencia de servicios externos')
        
        return factors
    
    async def _assess_impact(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Evaluar impacto del error"""
        
        impact = {
            'execution_impact': 'low',
            'system_impact': 'low',
            'user_impact': 'low',
            'business_impact': 'low',
            'affected_components': [],
            'recovery_time_estimate': '0-5 minutes'
        }
        
        # Impacto en ejecución
        if error_context.execution_context.success_rate < 0.3:
            impact['execution_impact'] = 'critical'
        elif error_context.execution_context.success_rate < 0.6:
            impact['execution_impact'] = 'high'
        elif error_context.execution_context.success_rate < 0.8:
            impact['execution_impact'] = 'medium'
        
        # Impacto del sistema
        if error_context.system_state.get('service_degradation', False):
            impact['system_impact'] = 'high'
        
        # Componentes afectados
        impact['affected_components'] = [
            error_context.failed_step.step.tool,
            error_context.failed_step.step.id
        ]
        
        # Estimación de tiempo de recuperación
        if error_context.failed_step.retry_count > 2:
            impact['recovery_time_estimate'] = '5-15 minutes'
        elif error_context.failed_step.retry_count > 0:
            impact['recovery_time_estimate'] = '1-5 minutes'
        
        return impact
    
    async def _generate_prevention_recommendations(self, 
                                                 error_context: ErrorContext,
                                                 root_causes: List[RootCause]) -> List[str]:
        """Generar recomendaciones de prevención"""
        
        recommendations = []
        
        # Recomendaciones basadas en causas raíz
        for cause in root_causes:
            if cause.category == 'technical':
                if 'network' in cause.description.lower():
                    recommendations.append('Implementar retry logic con backoff exponencial')
                    recommendations.append('Agregar validación de conectividad antes de operaciones')
                elif 'parameter' in cause.description.lower():
                    recommendations.append('Mejorar validación de parámetros de entrada')
                    recommendations.append('Implementar sanitización de datos')
            
            elif cause.category == 'operational':
                if 'permission' in cause.description.lower():
                    recommendations.append('Verificar permisos antes de ejecución')
                    recommendations.append('Implementar manejo escalado de privilegios')
            
            elif cause.category == 'environmental':
                if 'resource' in cause.description.lower():
                    recommendations.append('Implementar monitoreo de recursos')
                    recommendations.append('Agregar límites de recursos por operación')
        
        # Recomendaciones generales
        if error_context.failed_step.retry_count > 2:
            recommendations.append('Reducir número máximo de reintentos')
            recommendations.append('Implementar circuit breaker pattern')
        
        if len(error_context.related_errors) > 1:
            recommendations.append('Implementar manejo de errores en cascada')
            recommendations.append('Agregar puntos de control entre operaciones')
        
        return list(set(recommendations))  # Eliminar duplicados
    
    async def _suggest_recovery_strategies(self, 
                                         error_context: ErrorContext,
                                         root_causes: List[RootCause]) -> List[str]:
        """Sugerir estrategias de recuperación"""
        
        strategies = []
        
        # Estrategias basadas en tipo de error
        error_type = await self._classify_error(error_context)
        
        if error_type == ErrorType.NETWORK_ERROR:
            strategies.extend([
                'Reintentar con delay incremental',
                'Verificar conectividad y DNS',
                'Usar herramientas alternativas si disponibles'
            ])
        
        elif error_type == ErrorType.PERMISSION_ERROR:
            strategies.extend([
                'Verificar y ajustar permisos',
                'Ejecutar con privilegios elevados si necesario',
                'Usar métodos alternativos de acceso'
            ])
        
        elif error_type == ErrorType.TIMEOUT_ERROR:
            strategies.extend([
                'Aumentar tiempo límite',
                'Dividir operación en pasos más pequeños',
                'Verificar carga del sistema'
            ])
        
        elif error_type == ErrorType.TOOL_ERROR:
            strategies.extend([
                'Usar herramienta alternativa',
                'Verificar disponibilidad de herramienta',
                'Actualizar configuración de herramienta'
            ])
        
        elif error_type == ErrorType.PARAMETER_ERROR:
            strategies.extend([
                'Validar y corregir parámetros',
                'Usar valores por defecto seguros',
                'Consultar documentación de herramienta'
            ])
        
        # Estrategias basadas en patrón
        error_pattern = await self._detect_patterns(error_context)
        
        if error_pattern == ErrorPattern.RECURRING:
            strategies.append('Implementar solución permanente')
            strategies.append('Revisar configuración del sistema')
        
        elif error_pattern == ErrorPattern.CASCADING:
            strategies.append('Abordar error inicial en la cadena')
            strategies.append('Implementar rollback automático')
        
        return strategies
    
    async def _calculate_confidence(self, 
                                  error_context: ErrorContext,
                                  root_causes: List[RootCause],
                                  similar_errors: List[Dict[str, Any]]) -> float:
        """Calcular confianza en el análisis"""
        
        confidence_factors = []
        
        # Factor 1: Confianza en causas raíz
        if root_causes:
            avg_cause_confidence = statistics.mean(cause.confidence for cause in root_causes)
            confidence_factors.append(avg_cause_confidence)
        
        # Factor 2: Disponibilidad de errores similares
        if similar_errors:
            similarity_factor = min(len(similar_errors) / 5, 1.0)
            confidence_factors.append(similarity_factor)
        
        # Factor 3: Claridad del mensaje de error
        if len(error_context.error_message) > 10:
            clarity_factor = 0.8
        else:
            clarity_factor = 0.5
        confidence_factors.append(clarity_factor)
        
        # Factor 4: Contexto disponible
        context_factor = 0.6
        if error_context.stack_trace:
            context_factor += 0.2
        if error_context.system_state:
            context_factor += 0.1
        if error_context.environment_info:
            context_factor += 0.1
        confidence_factors.append(context_factor)
        
        return statistics.mean(confidence_factors)
    
    async def _record_analysis_in_memory(self, analysis_result: ErrorAnalysisResult):
        """Registrar análisis en memoria"""
        
        try:
            # Preparar datos para memoria
            analysis_data = {
                'type': 'error_analysis',
                'timestamp': analysis_result.analysis_timestamp.isoformat(),
                'error_id': analysis_result.error_id,
                'error_type': analysis_result.error_type.value,
                'error_severity': analysis_result.error_severity.value,
                'error_pattern': analysis_result.error_pattern.value,
                'root_causes_count': len(analysis_result.root_causes),
                'confidence_score': analysis_result.confidence_score,
                'analysis_depth': analysis_result.analysis_depth.value,
                'prevention_recommendations': analysis_result.prevention_recommendations,
                'recovery_strategies': analysis_result.recovery_strategies
            }
            
            # Almacenar en memoria episódica
            if self.memory_manager.is_initialized:
                from src.memory.episodic_memory_store import Episode
                
                episode = Episode(
                    id=str(uuid.uuid4()),
                    title=f"Análisis de Error: {analysis_result.error_type.value}",
                    description=f"Análisis detallado con {len(analysis_result.root_causes)} causas raíz",
                    context=analysis_data,
                    actions=[{
                        'type': 'error_analysis',
                        'depth': analysis_result.analysis_depth.value,
                        'timestamp': datetime.now().isoformat()
                    }],
                    outcomes=[{
                        'type': 'analysis_completed',
                        'confidence': analysis_result.confidence_score,
                        'recommendations_count': len(analysis_result.prevention_recommendations),
                        'timestamp': datetime.now().isoformat()
                    }],
                    timestamp=datetime.now(),
                    success=analysis_result.confidence_score > self.confidence_threshold,
                    importance=4,
                    tags=['error_analysis', analysis_result.error_type.value, analysis_result.error_severity.value]
                )
                
                await self.memory_manager.episodic_memory.store_episode(episode)
                logger.info("🧠 Análisis de error almacenado en memoria")
            
            # Actualizar firmas de errores
            error_signature = f"{analysis_result.error_type.value}_{analysis_result.error_severity.value}"
            self.error_signatures[error_signature] = self.error_signatures.get(error_signature, 0) + 1
            
        except Exception as e:
            logger.warning(f"Error almacenando análisis en memoria: {str(e)}")
    
    async def _update_statistics(self, analysis_result: ErrorAnalysisResult):
        """Actualizar estadísticas"""
        
        # Actualizar contadores
        self.root_causes_found += len(analysis_result.root_causes)
        
        if analysis_result.error_pattern != ErrorPattern.SYSTEMATIC:
            self.patterns_detected += 1
        
        # Actualizar patrones
        pattern_key = f"{analysis_result.error_type.value}_{analysis_result.error_pattern.value}"
        self.error_patterns[pattern_key] += 1
    
    async def _generate_fallback_analysis(self, error_context: ErrorContext) -> ErrorAnalysisResult:
        """Generar análisis fallback"""
        
        fallback_cause = RootCause(
            id='fallback_cause',
            category='technical',
            description='Análisis automático fallback',
            confidence=0.3,
            evidence=['Análisis fallback debido a error en procesamiento'],
            contributing_factors=['Error en sistema de análisis'],
            impact_assessment='Impacto desconocido'
        )
        
        return ErrorAnalysisResult(
            error_id=str(uuid.uuid4()),
            analysis_timestamp=datetime.now(),
            error_type=ErrorType.SYSTEM_ERROR,
            error_severity=ErrorSeverity.MEDIUM,
            error_pattern=ErrorPattern.SYSTEMATIC,
            root_causes=[fallback_cause],
            immediate_causes=['Error en análisis automático'],
            contributing_factors=['Sistema de análisis falló'],
            impact_analysis={'execution_impact': 'medium'},
            prevention_recommendations=['Verificar sistema de análisis'],
            recovery_strategies=['Reintentar análisis'],
            similar_errors=[],
            confidence_score=0.3,
            analysis_depth=AnalysisDepth.BASIC
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del analizador"""
        
        return {
            'analyses_performed': self.analyses_performed,
            'patterns_detected': self.patterns_detected,
            'root_causes_found': self.root_causes_found,
            'prevention_success_rate': self.prevention_success_rate,
            'error_patterns': dict(self.error_patterns),
            'most_common_error_type': max(self.error_patterns.keys(), key=self.error_patterns.get) if self.error_patterns else None,
            'error_signatures_count': len(self.error_signatures),
            'analysis_rules_count': len(self.analysis_rules),
            'configuration': {
                'analysis_depth': self.analysis_depth.value,
                'enable_pattern_detection': self.enable_pattern_detection,
                'enable_llm_analysis': self.enable_llm_analysis,
                'confidence_threshold': self.confidence_threshold
            }
        }
    
    def reset_statistics(self):
        """Resetear estadísticas"""
        self.analyses_performed = 0
        self.patterns_detected = 0
        self.root_causes_found = 0
        self.prevention_success_rate = 0.0
        self.error_patterns.clear()
        self.error_signatures.clear()
        self.recovery_success_rates.clear()
        logger.info("🔍 Estadísticas de análisis de errores reseteadas")