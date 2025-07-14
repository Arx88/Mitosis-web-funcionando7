"""
Sistema de Monitoreo y Depuración Avanzado para el agente Mitosis
Incluye alertas configurables, análisis de causa raíz y métricas avanzadas
"""

import logging
import json
import time
import threading
import asyncio
from typing import List, Dict, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
import queue
import statistics
from collections import defaultdict, deque
import traceback
import psutil
import os

class AlertLevel(Enum):
    """Niveles de alerta"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Tipos de métricas"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Alert:
    """Definición de una alerta"""
    id: str
    title: str
    message: str
    level: AlertLevel
    timestamp: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class Metric:
    """Métrica del sistema"""
    name: str
    type: MetricType
    value: Union[int, float]
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

@dataclass
class ErrorAnalysis:
    """Análisis de causa raíz de un error"""
    error_id: str
    error_message: str
    error_type: str
    stack_trace: str
    timestamp: float
    context: Dict[str, Any]
    root_cause: Optional[str] = None
    suggested_fixes: List[str] = field(default_factory=list)
    similar_errors: List[str] = field(default_factory=list)
    confidence_score: float = 0.0

@dataclass
class PerformanceProfile:
    """Perfil de rendimiento"""
    component: str
    operation: str
    duration: float
    memory_usage: float
    cpu_usage: float
    timestamp: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

class EnhancedMonitoringSystem:
    """Sistema de monitoreo y depuración avanzado"""
    
    def __init__(self, memory_manager=None, task_manager=None):
        self.memory_manager = memory_manager
        self.task_manager = task_manager
        self.logger = logging.getLogger(__name__)
        
        # Configuración
        self.alert_enabled = True
        self.metrics_enabled = True
        self.performance_profiling_enabled = True
        self.auto_error_analysis_enabled = True
        
        # Almacenamiento de datos
        self.alerts: List[Alert] = []
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.error_analyses: List[ErrorAnalysis] = []
        self.performance_profiles: List[PerformanceProfile] = []
        
        # Configuración de alertas
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_callbacks: Dict[str, Callable] = {}
        self.max_alerts = 1000
        self.max_metrics_per_type = 10000
        
        # Cola de eventos para procesamiento asíncrono
        self.event_queue = queue.Queue()
        self.processing_thread = None
        self.running = False
        
        # Métricas del sistema
        self.system_metrics = {
            "cpu_usage": deque(maxlen=100),
            "memory_usage": deque(maxlen=100),
            "disk_usage": deque(maxlen=100),
            "network_io": deque(maxlen=100)
        }
        
        # Patrones de errores conocidos
        self.error_patterns = {
            "connection_timeout": {
                "keywords": ["timeout", "connection", "failed to connect"],
                "root_cause": "Problema de conectividad de red",
                "fixes": [
                    "Verificar conexión a internet",
                    "Aumentar timeout de conexión",
                    "Implementar reintentos automáticos"
                ]
            },
            "memory_error": {
                "keywords": ["memory", "out of memory", "allocation failed"],
                "root_cause": "Insuficiente memoria disponible",
                "fixes": [
                    "Optimizar uso de memoria",
                    "Implementar liberación de memoria",
                    "Aumentar límites de memoria"
                ]
            },
            "permission_error": {
                "keywords": ["permission", "access denied", "forbidden"],
                "root_cause": "Permisos insuficientes",
                "fixes": [
                    "Verificar permisos de archivo/directorio",
                    "Ejecutar con privilegios elevados",
                    "Configurar permisos apropiados"
                ]
            },
            "api_error": {
                "keywords": ["api", "http", "status code", "request failed"],
                "root_cause": "Error en llamada a API externa",
                "fixes": [
                    "Verificar credenciales de API",
                    "Revisar límites de tasa",
                    "Implementar manejo de errores HTTP"
                ]
            }
        }
        
        # Inicializar reglas de alerta por defecto
        self._initialize_default_alert_rules()
        
        # Iniciar sistema de monitoreo
        self.start_monitoring()
        
        self.logger.info("Enhanced Monitoring System inicializado")
    
    def _initialize_default_alert_rules(self):
        """Inicializa reglas de alerta por defecto"""
        default_rules = {
            "high_cpu_usage": {
                "metric": "cpu_usage",
                "condition": "greater_than",
                "threshold": 80.0,
                "level": AlertLevel.WARNING,
                "message": "Uso de CPU alto: {value}%"
            },
            "high_memory_usage": {
                "metric": "memory_usage",
                "condition": "greater_than",
                "threshold": 85.0,
                "level": AlertLevel.WARNING,
                "message": "Uso de memoria alto: {value}%"
            },
            "task_failure_rate": {
                "metric": "task_failure_rate",
                "condition": "greater_than",
                "threshold": 0.2,
                "level": AlertLevel.ERROR,
                "message": "Tasa de fallo de tareas alta: {value}%"
            },
            "error_frequency": {
                "metric": "error_count",
                "condition": "greater_than",
                "threshold": 10,
                "level": AlertLevel.CRITICAL,
                "message": "Frecuencia de errores alta: {value} errores en la última hora"
            }
        }
        
        for rule_id, rule in default_rules.items():
            self.add_alert_rule(rule_id, rule)
    
    def start_monitoring(self):
        """Inicia el sistema de monitoreo"""
        if self.running:
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.processing_thread.start()
        
        # Iniciar recolección de métricas del sistema
        self._start_system_metrics_collection()
        
        self.logger.info("Sistema de monitoreo iniciado")
    
    def stop_monitoring(self):
        """Detiene el sistema de monitoreo"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        self.logger.info("Sistema de monitoreo detenido")
    
    def _monitoring_loop(self):
        """Bucle principal de monitoreo"""
        while self.running:
            try:
                # Procesar eventos de la cola
                try:
                    event = self.event_queue.get(timeout=1.0)
                    self._process_event(event)
                except queue.Empty:
                    continue
                
                # Evaluar reglas de alerta
                self._evaluate_alert_rules()
                
                # Limpiar datos antiguos
                self._cleanup_old_data()
                
            except Exception as e:
                self.logger.error(f"Error en bucle de monitoreo: {e}")
                time.sleep(1.0)
    
    def _start_system_metrics_collection(self):
        """Inicia la recolección de métricas del sistema"""
        def collect_system_metrics():
            while self.running:
                try:
                    # CPU
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.record_metric("cpu_usage", cpu_percent, MetricType.GAUGE, unit="%")
                    
                    # Memoria
                    memory = psutil.virtual_memory()
                    self.record_metric("memory_usage", memory.percent, MetricType.GAUGE, unit="%")
                    
                    # Disco
                    disk = psutil.disk_usage('/')
                    disk_percent = (disk.used / disk.total) * 100
                    self.record_metric("disk_usage", disk_percent, MetricType.GAUGE, unit="%")
                    
                    # Red (simplificado)
                    net_io = psutil.net_io_counters()
                    self.record_metric("network_bytes_sent", net_io.bytes_sent, MetricType.COUNTER, unit="bytes")
                    self.record_metric("network_bytes_recv", net_io.bytes_recv, MetricType.COUNTER, unit="bytes")
                    
                except Exception as e:
                    self.logger.error(f"Error recolectando métricas del sistema: {e}")
                
                time.sleep(5.0)  # Recolectar cada 5 segundos
        
        metrics_thread = threading.Thread(target=collect_system_metrics, daemon=True)
        metrics_thread.start()
    
    def record_metric(self, name: str, value: Union[int, float], 
                     metric_type: MetricType, tags: Optional[Dict[str, str]] = None,
                     unit: str = ""):
        """Registra una métrica"""
        if not self.metrics_enabled:
            return
        
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            unit=unit
        )
        
        self.metrics[name].append(metric)
        
        # Mantener límite de métricas
        if len(self.metrics[name]) > self.max_metrics_per_type:
            self.metrics[name].pop(0)
        
        # Añadir a cola de eventos para procesamiento
        self.event_queue.put({"type": "metric", "data": metric})
    
    def create_alert(self, title: str, message: str, level: AlertLevel,
                    source: str = "system", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Crea una nueva alerta"""
        if not self.alert_enabled:
            return ""
        
        alert_id = f"alert_{int(time.time())}_{len(self.alerts)}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            level=level,
            timestamp=time.time(),
            source=source,
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        
        # Mantener límite de alertas
        if len(self.alerts) > self.max_alerts:
            self.alerts.pop(0)
        
        # Ejecutar callbacks de alerta
        self._execute_alert_callbacks(alert)
        
        # Añadir a cola de eventos
        self.event_queue.put({"type": "alert", "data": alert})
        
        self.logger.info(f"Alerta creada: {title} ({level.value})")
        return alert_id
    
    def add_alert_rule(self, rule_id: str, rule: Dict[str, Any]):
        """Añade una regla de alerta"""
        self.alert_rules[rule_id] = rule
        self.logger.info(f"Regla de alerta añadida: {rule_id}")
    
    def add_alert_callback(self, callback_id: str, callback: Callable):
        """Añade un callback para alertas"""
        self.alert_callbacks[callback_id] = callback
        self.logger.info(f"Callback de alerta añadido: {callback_id}")
    
    def _execute_alert_callbacks(self, alert: Alert):
        """Ejecuta callbacks de alerta"""
        for callback_id, callback in self.alert_callbacks.items():
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error ejecutando callback {callback_id}: {e}")
    
    def _evaluate_alert_rules(self):
        """Evalúa las reglas de alerta"""
        for rule_id, rule in self.alert_rules.items():
            try:
                metric_name = rule.get("metric")
                if not metric_name or metric_name not in self.metrics:
                    continue
                
                # Obtener métricas recientes
                recent_metrics = [m for m in self.metrics[metric_name] 
                                if time.time() - m.timestamp < 300]  # Últimos 5 minutos
                
                if not recent_metrics:
                    continue
                
                # Calcular valor actual
                if rule.get("aggregation") == "average":
                    current_value = statistics.mean(m.value for m in recent_metrics)
                elif rule.get("aggregation") == "max":
                    current_value = max(m.value for m in recent_metrics)
                elif rule.get("aggregation") == "min":
                    current_value = min(m.value for m in recent_metrics)
                else:
                    current_value = recent_metrics[-1].value  # Último valor
                
                # Evaluar condición
                threshold = rule.get("threshold", 0)
                condition = rule.get("condition", "greater_than")
                
                triggered = False
                if condition == "greater_than" and current_value > threshold:
                    triggered = True
                elif condition == "less_than" and current_value < threshold:
                    triggered = True
                elif condition == "equals" and current_value == threshold:
                    triggered = True
                
                if triggered:
                    # Verificar si ya existe una alerta similar reciente
                    recent_alerts = [a for a in self.alerts 
                                   if time.time() - a.timestamp < 600 and  # Últimos 10 minutos
                                   rule_id in a.metadata.get("rule_id", "")]
                    
                    if not recent_alerts:
                        # Crear alerta
                        message = rule.get("message", "Regla de alerta activada").format(
                            value=current_value, threshold=threshold
                        )
                        
                        self.create_alert(
                            title=f"Alerta: {rule_id}",
                            message=message,
                            level=AlertLevel(rule.get("level", "warning")),
                            source="alert_rule",
                            metadata={"rule_id": rule_id, "current_value": current_value}
                        )
                
            except Exception as e:
                self.logger.error(f"Error evaluando regla {rule_id}: {e}")
    
    def analyze_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorAnalysis:
        """Analiza un error y proporciona diagnóstico de causa raíz"""
        error_id = f"error_{int(time.time())}_{len(self.error_analyses)}"
        
        # Obtener información del error
        error_message = str(error)
        error_type = type(error).__name__
        stack_trace = traceback.format_exc()
        
        # Crear análisis base
        analysis = ErrorAnalysis(
            error_id=error_id,
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            timestamp=time.time(),
            context=context or {}
        )
        
        if self.auto_error_analysis_enabled:
            # Análisis automático de causa raíz
            analysis.root_cause, analysis.suggested_fixes, analysis.confidence_score = (
                self._perform_root_cause_analysis(error_message, error_type, stack_trace)
            )
            
            # Buscar errores similares
            analysis.similar_errors = self._find_similar_errors(error_message, error_type)
        
        self.error_analyses.append(analysis)
        
        # Crear alerta para errores críticos
        if error_type in ["SystemError", "MemoryError", "OSError"]:
            self.create_alert(
                title=f"Error crítico: {error_type}",
                message=f"Error crítico detectado: {error_message}",
                level=AlertLevel.CRITICAL,
                source="error_analysis",
                metadata={"error_id": error_id, "error_type": error_type}
            )
        
        self.logger.info(f"Análisis de error completado: {error_id}")
        return analysis
    
    def _perform_root_cause_analysis(self, error_message: str, error_type: str, 
                                   stack_trace: str) -> Tuple[str, List[str], float]:
        """Realiza análisis de causa raíz automático"""
        error_text = f"{error_message} {error_type} {stack_trace}".lower()
        
        best_match = None
        best_score = 0.0
        
        # Buscar patrones conocidos
        for pattern_name, pattern_info in self.error_patterns.items():
            score = 0.0
            keywords = pattern_info["keywords"]
            
            # Calcular puntuación basada en palabras clave
            for keyword in keywords:
                if keyword in error_text:
                    score += 1.0 / len(keywords)
            
            if score > best_score:
                best_score = score
                best_match = pattern_info
        
        if best_match and best_score > 0.5:
            return (
                best_match["root_cause"],
                best_match["fixes"],
                best_score
            )
        
        # Análisis genérico si no hay coincidencias
        generic_fixes = [
            "Revisar logs para más detalles",
            "Verificar configuración del sistema",
            "Reintentar la operación",
            "Contactar soporte técnico si persiste"
        ]
        
        return "Causa raíz no determinada automáticamente", generic_fixes, 0.3
    
    def _find_similar_errors(self, error_message: str, error_type: str) -> List[str]:
        """Encuentra errores similares en el historial"""
        similar_errors = []
        
        for analysis in self.error_analyses[-50:]:  # Últimos 50 errores
            if analysis.error_type == error_type:
                # Calcular similitud simple basada en palabras
                words1 = set(error_message.lower().split())
                words2 = set(analysis.error_message.lower().split())
                
                if words1 and words2:
                    similarity = len(words1 & words2) / len(words1 | words2)
                    if similarity > 0.3:
                        similar_errors.append(analysis.error_id)
        
        return similar_errors
    
    def profile_performance(self, component: str, operation: str):
        """Decorator/context manager para perfilar rendimiento"""
        class PerformanceProfiler:
            def __init__(self, monitoring_system, component, operation):
                self.monitoring_system = monitoring_system
                self.component = component
                self.operation = operation
                self.start_time = None
                self.start_memory = None
                self.start_cpu = None
            
            def __enter__(self):
                self.start_time = time.time()
                self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                self.start_cpu = psutil.Process().cpu_percent()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                end_cpu = psutil.Process().cpu_percent()
                
                duration = end_time - self.start_time
                memory_usage = end_memory - self.start_memory
                cpu_usage = end_cpu - self.start_cpu
                success = exc_type is None
                
                profile = PerformanceProfile(
                    component=self.component,
                    operation=self.operation,
                    duration=duration,
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage,
                    timestamp=self.start_time,
                    success=success,
                    metadata={
                        "start_memory": self.start_memory,
                        "end_memory": end_memory,
                        "exception_type": str(exc_type) if exc_type else None
                    }
                )
                
                self.monitoring_system._record_performance_profile(profile)
        
        return PerformanceProfiler(self, component, operation)
    
    def _record_performance_profile(self, profile: PerformanceProfile):
        """Registra un perfil de rendimiento"""
        if not self.performance_profiling_enabled:
            return
        
        self.performance_profiles.append(profile)
        
        # Mantener límite
        if len(self.performance_profiles) > 10000:
            self.performance_profiles.pop(0)
        
        # Registrar métricas
        self.record_metric(f"{profile.component}_{profile.operation}_duration", 
                          profile.duration, MetricType.TIMER, unit="seconds")
        self.record_metric(f"{profile.component}_{profile.operation}_memory", 
                          profile.memory_usage, MetricType.GAUGE, unit="MB")
    
    def _process_event(self, event: Dict[str, Any]):
        """Procesa un evento del sistema"""
        event_type = event.get("type")
        
        if event_type == "metric":
            # Procesar métrica
            pass
        elif event_type == "alert":
            # Procesar alerta
            pass
        elif event_type == "error":
            # Procesar error
            pass
    
    def _cleanup_old_data(self):
        """Limpia datos antiguos"""
        current_time = time.time()
        cutoff_time = current_time - (24 * 60 * 60)  # 24 horas
        
        # Limpiar alertas antiguas resueltas
        self.alerts = [a for a in self.alerts 
                      if not a.resolved or current_time - a.timestamp < cutoff_time]
        
        # Limpiar análisis de errores antiguos
        if len(self.error_analyses) > 1000:
            self.error_analyses = self.error_analyses[-500:]
        
        # Limpiar perfiles de rendimiento antiguos
        if len(self.performance_profiles) > 10000:
            self.performance_profiles = self.performance_profiles[-5000:]
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Obtiene datos para el dashboard de monitoreo"""
        current_time = time.time()
        
        # Alertas activas
        active_alerts = [a for a in self.alerts if not a.resolved]
        
        # Métricas recientes
        recent_metrics = {}
        for metric_name, metric_list in self.metrics.items():
            recent = [m for m in metric_list if current_time - m.timestamp < 300]
            if recent:
                recent_metrics[metric_name] = {
                    "current": recent[-1].value,
                    "average": statistics.mean(m.value for m in recent),
                    "min": min(m.value for m in recent),
                    "max": max(m.value for m in recent),
                    "unit": recent[-1].unit
                }
        
        # Errores recientes
        recent_errors = [e for e in self.error_analyses 
                        if current_time - e.timestamp < 3600]  # Última hora
        
        # Rendimiento por componente
        component_performance = defaultdict(list)
        for profile in self.performance_profiles[-100:]:  # Últimos 100
            component_performance[profile.component].append(profile.duration)
        
        avg_performance = {}
        for component, durations in component_performance.items():
            avg_performance[component] = statistics.mean(durations)
        
        return {
            "timestamp": current_time,
            "alerts": {
                "active_count": len(active_alerts),
                "by_level": {
                    level.value: len([a for a in active_alerts if a.level == level])
                    for level in AlertLevel
                },
                "recent": [asdict(a) for a in active_alerts[-10:]]
            },
            "metrics": recent_metrics,
            "errors": {
                "recent_count": len(recent_errors),
                "by_type": {
                    error_type: len([e for e in recent_errors if e.error_type == error_type])
                    for error_type in set(e.error_type for e in recent_errors)
                }
            },
            "performance": {
                "average_by_component": avg_performance,
                "total_profiles": len(self.performance_profiles)
            },
            "system_health": {
                "monitoring_active": self.running,
                "queue_size": self.event_queue.qsize(),
                "total_metrics": sum(len(metrics) for metrics in self.metrics.values())
            }
        }

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear sistema de monitoreo
    monitoring = EnhancedMonitoringSystem()
    
    print("📊 Probando Enhanced Monitoring System...")
    
    # Registrar algunas métricas
    monitoring.record_metric("test_counter", 42, MetricType.COUNTER)
    monitoring.record_metric("test_gauge", 75.5, MetricType.GAUGE, unit="%")
    
    # Crear alerta
    alert_id = monitoring.create_alert(
        title="Prueba de alerta",
        message="Esta es una alerta de prueba",
        level=AlertLevel.WARNING,
        source="test"
    )
    print(f"✅ Alerta creada: {alert_id}")
    
    # Simular error y análisis
    try:
        raise ValueError("Error de prueba para análisis")
    except Exception as e:
        analysis = monitoring.analyze_error(e, {"test": True})
        print(f"🔍 Análisis de error: {analysis.root_cause}")
        print(f"   Sugerencias: {analysis.suggested_fixes}")
    
    # Probar perfilado de rendimiento
    with monitoring.profile_performance("test_component", "test_operation"):
        time.sleep(0.1)  # Simular trabajo
    
    # Obtener datos del dashboard
    dashboard_data = monitoring.get_monitoring_dashboard_data()
    print(f"📈 Dashboard data:")
    print(f"   Alertas activas: {dashboard_data['alerts']['active_count']}")
    print(f"   Métricas: {len(dashboard_data['metrics'])}")
    print(f"   Errores recientes: {dashboard_data['errors']['recent_count']}")
    
    # Detener monitoreo
    monitoring.stop_monitoring()
    
    print("✅ Pruebas completadas")

