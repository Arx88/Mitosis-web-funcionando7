"""
Gestor de recursos para el sistema de orquestación
Maneja la asignación y monitoreo de recursos del sistema
"""

import logging
import psutil
import threading
import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Tipos de recursos del sistema"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"
    CUSTOM = "custom"

@dataclass
class ResourceLimit:
    """Límites de recursos"""
    resource_type: ResourceType
    max_value: float
    current_value: float = 0.0
    unit: str = ""
    threshold_warning: float = 0.8  # 80% para warning
    threshold_critical: float = 0.9  # 90% para critical

@dataclass
class ResourceRequest:
    """Solicitud de recursos"""
    step_id: str
    resource_type: ResourceType
    requested_amount: float
    priority: int = 1
    timeout: float = 300.0  # 5 minutos
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceAllocation:
    """Asignación de recursos"""
    step_id: str
    resource_type: ResourceType
    allocated_amount: float
    start_time: float
    expected_duration: float
    actual_usage: float = 0.0
    peak_usage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResourceMonitor:
    """Monitor de recursos del sistema"""
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Métricas actuales
        self.current_metrics = {
            ResourceType.CPU: 0.0,
            ResourceType.MEMORY: 0.0,
            ResourceType.DISK: 0.0,
            ResourceType.NETWORK: 0.0
        }
        
        # Historial de métricas
        self.metrics_history = []
        self.max_history_size = 3600  # 1 hora con intervalos de 1 segundo
        
        # Callbacks para alertas
        self.alert_callbacks = []
    
    def start_monitoring(self):
        """Inicia el monitoreo de recursos"""
        
        if self.monitoring_active:
            logger.warning("El monitoreo ya está activo")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Monitoreo de recursos iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo de recursos"""
        
        self.monitoring_active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        logger.info("Monitoreo de recursos detenido")
    
    def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        
        while self.monitoring_active:
            try:
                # Recolectar métricas
                metrics = self._collect_metrics()
                
                # Actualizar métricas actuales
                self.current_metrics.update(metrics)
                
                # Agregar al historial
                self._add_to_history(metrics)
                
                # Verificar alertas
                self._check_alerts(metrics)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error en monitoreo de recursos: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_metrics(self) -> Dict[ResourceType, float]:
        """Recolecta métricas actuales del sistema"""
        
        metrics = {}
        
        try:
            # CPU
            metrics[ResourceType.CPU] = psutil.cpu_percent(interval=None)
            
            # Memoria
            memory = psutil.virtual_memory()
            metrics[ResourceType.MEMORY] = memory.percent
            
            # Disco
            disk = psutil.disk_usage('/')
            metrics[ResourceType.DISK] = (disk.used / disk.total) * 100
            
            # Red (aproximado)
            network = psutil.net_io_counters()
            metrics[ResourceType.NETWORK] = 0.0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error recolectando métricas: {e}")
        
        return metrics
    
    def _add_to_history(self, metrics: Dict[ResourceType, float]):
        """Agrega métricas al historial"""
        
        timestamp = time.time()
        
        history_entry = {
            'timestamp': timestamp,
            'metrics': metrics.copy()
        }
        
        self.metrics_history.append(history_entry)
        
        # Mantener tamaño del historial
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
    
    def _check_alerts(self, metrics: Dict[ResourceType, float]):
        """Verifica condiciones de alerta"""
        
        for resource_type, value in metrics.items():
            # Alertas por thresholds
            if value > 90:
                self._trigger_alert("critical", resource_type, value)
            elif value > 80:
                self._trigger_alert("warning", resource_type, value)
    
    def _trigger_alert(self, level: str, resource_type: ResourceType, value: float):
        """Dispara una alerta"""
        
        alert = {
            'timestamp': time.time(),
            'level': level,
            'resource_type': resource_type,
            'value': value,
            'message': f"{resource_type.value} usage at {value:.1f}%"
        }
        
        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")
    
    def get_current_metrics(self) -> Dict[ResourceType, float]:
        """Obtiene métricas actuales"""
        
        return self.current_metrics.copy()
    
    def get_historical_metrics(self, duration: int = 300) -> List[Dict[str, Any]]:
        """Obtiene métricas históricas"""
        
        cutoff_time = time.time() - duration
        
        return [
            entry for entry in self.metrics_history
            if entry['timestamp'] >= cutoff_time
        ]
    
    def add_alert_callback(self, callback):
        """Agrega callback para alertas"""
        
        self.alert_callbacks.append(callback)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información del sistema"""
        
        try:
            return {
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total,
                'system': psutil.uname()._asdict()
            }
        except Exception as e:
            logger.error(f"Error obteniendo información del sistema: {e}")
            return {}

class ResourceManager:
    """Gestor principal de recursos"""
    
    def __init__(self):
        self.resource_limits = {}
        self.active_allocations = {}
        self.allocation_queue = []
        self.resource_monitor = ResourceMonitor()
        
        # Configuración por defecto
        self._set_default_limits()
        
        # Iniciar monitoreo
        self.resource_monitor.start_monitoring()
        
        # Configurar alertas
        self.resource_monitor.add_alert_callback(self._handle_resource_alert)
        
        # Métricas
        self.allocation_metrics = {
            'total_requests': 0,
            'successful_allocations': 0,
            'failed_allocations': 0,
            'timeout_allocations': 0,
            'avg_allocation_time': 0.0
        }
    
    def __del__(self):
        """Destructor para limpiar recursos"""
        if hasattr(self, 'resource_monitor'):
            self.resource_monitor.stop_monitoring()
    
    def _set_default_limits(self):
        """Establece límites por defecto"""
        
        try:
            # CPU: 80% máximo
            self.resource_limits[ResourceType.CPU] = ResourceLimit(
                resource_type=ResourceType.CPU,
                max_value=80.0,
                unit="percent"
            )
            
            # Memoria: 80% máximo
            memory_info = psutil.virtual_memory()
            self.resource_limits[ResourceType.MEMORY] = ResourceLimit(
                resource_type=ResourceType.MEMORY,
                max_value=memory_info.total * 0.8,
                unit="bytes"
            )
            
            # Disco: 90% máximo
            disk_info = psutil.disk_usage('/')
            self.resource_limits[ResourceType.DISK] = ResourceLimit(
                resource_type=ResourceType.DISK,
                max_value=disk_info.total * 0.9,
                unit="bytes"
            )
            
        except Exception as e:
            logger.error(f"Error estableciendo límites por defecto: {e}")
    
    async def request_resources(self, request: ResourceRequest) -> Optional[ResourceAllocation]:
        """Solicita recursos para un paso"""
        
        logger.info(f"Solicitando recursos para paso {request.step_id}: "
                   f"{request.requested_amount} {request.resource_type.value}")
        
        start_time = time.time()
        self.allocation_metrics['total_requests'] += 1
        
        try:
            # Verificar disponibilidad
            if not self._check_resource_availability(request):
                logger.warning(f"Recursos no disponibles para {request.step_id}")
                await self._queue_request(request)
                return None
            
            # Asignar recursos
            allocation = self._allocate_resources(request)
            
            if allocation:
                self.active_allocations[request.step_id] = allocation
                self.allocation_metrics['successful_allocations'] += 1
                
                # Actualizar tiempo promedio
                allocation_time = time.time() - start_time
                self._update_avg_allocation_time(allocation_time)
                
                logger.info(f"Recursos asignados exitosamente para {request.step_id}")
                return allocation
            else:
                self.allocation_metrics['failed_allocations'] += 1
                logger.error(f"Error asignando recursos para {request.step_id}")
                return None
                
        except Exception as e:
            self.allocation_metrics['failed_allocations'] += 1
            logger.error(f"Error en solicitud de recursos: {e}")
            return None
    
    def release_resources(self, step_id: str):
        """Libera recursos de un paso"""
        
        if step_id in self.active_allocations:
            allocation = self.active_allocations[step_id]
            
            # Actualizar métricas finales
            allocation.actual_usage = self._calculate_actual_usage(allocation)
            
            # Liberar recursos
            self._deallocate_resources(allocation)
            
            del self.active_allocations[step_id]
            
            logger.info(f"Recursos liberados para paso {step_id}")
            
            # Procesar cola de espera
            asyncio.create_task(self._process_queue())
    
    def update_resource_usage(self, step_id: str, usage_metrics: Dict[str, float]):
        """Actualiza métricas de uso de recursos"""
        
        if step_id in self.active_allocations:
            allocation = self.active_allocations[step_id]
            
            # Actualizar uso actual
            if allocation.resource_type.value in usage_metrics:
                current_usage = usage_metrics[allocation.resource_type.value]
                allocation.actual_usage = current_usage
                
                # Actualizar pico de uso
                if current_usage > allocation.peak_usage:
                    allocation.peak_usage = current_usage
    
    def _check_resource_availability(self, request: ResourceRequest) -> bool:
        """Verifica disponibilidad de recursos"""
        
        resource_type = request.resource_type
        
        if resource_type not in self.resource_limits:
            logger.warning(f"Límite no definido para {resource_type}")
            return True
        
        limit = self.resource_limits[resource_type]
        
        # Calcular uso actual
        current_usage = self._calculate_current_usage(resource_type)
        
        # Verificar si hay suficientes recursos
        if current_usage + request.requested_amount > limit.max_value:
            logger.info(f"Recursos insuficientes: {current_usage + request.requested_amount} > {limit.max_value}")
            return False
        
        return True
    
    def _calculate_current_usage(self, resource_type: ResourceType) -> float:
        """Calcula el uso actual de un tipo de recurso"""
        
        current_usage = 0.0
        
        # Sumar uso de asignaciones activas
        for allocation in self.active_allocations.values():
            if allocation.resource_type == resource_type:
                current_usage += allocation.allocated_amount
        
        return current_usage
    
    def _allocate_resources(self, request: ResourceRequest) -> Optional[ResourceAllocation]:
        """Asigna recursos a un paso"""
        
        allocation = ResourceAllocation(
            step_id=request.step_id,
            resource_type=request.resource_type,
            allocated_amount=request.requested_amount,
            start_time=time.time(),
            expected_duration=request.timeout,
            metadata=request.metadata.copy()
        )
        
        # Actualizar límite actual
        if request.resource_type in self.resource_limits:
            limit = self.resource_limits[request.resource_type]
            limit.current_value += request.requested_amount
        
        return allocation
    
    def _deallocate_resources(self, allocation: ResourceAllocation):
        """Libera recursos de una asignación"""
        
        # Actualizar límite actual
        if allocation.resource_type in self.resource_limits:
            limit = self.resource_limits[allocation.resource_type]
            limit.current_value -= allocation.allocated_amount
            
            # Asegurar que no sea negativo
            limit.current_value = max(0, limit.current_value)
    
    def _calculate_actual_usage(self, allocation: ResourceAllocation) -> float:
        """Calcula el uso real de recursos"""
        
        # Obtener métricas actuales del monitor
        current_metrics = self.resource_monitor.get_current_metrics()
        
        if allocation.resource_type in current_metrics:
            return current_metrics[allocation.resource_type]
        
        return 0.0
    
    async def _queue_request(self, request: ResourceRequest):
        """Agrega solicitud a la cola"""
        
        self.allocation_queue.append(request)
        logger.info(f"Solicitud {request.step_id} agregada a cola")
    
    async def _process_queue(self):
        """Procesa la cola de solicitudes"""
        
        if not self.allocation_queue:
            return
        
        processed_requests = []
        
        for request in self.allocation_queue:
            if self._check_resource_availability(request):
                allocation = self._allocate_resources(request)
                
                if allocation:
                    self.active_allocations[request.step_id] = allocation
                    processed_requests.append(request)
                    
                    logger.info(f"Solicitud en cola procesada: {request.step_id}")
        
        # Remover solicitudes procesadas
        for request in processed_requests:
            self.allocation_queue.remove(request)
    
    def _handle_resource_alert(self, alert: Dict[str, Any]):
        """Maneja alertas de recursos"""
        
        logger.warning(f"Alerta de recursos: {alert}")
        
        if alert['level'] == 'critical':
            # Implementar acciones de emergencia
            self._handle_critical_resource_alert(alert)
    
    def _handle_critical_resource_alert(self, alert: Dict[str, Any]):
        """Maneja alertas críticas de recursos"""
        
        resource_type = alert['resource_type']
        
        # Buscar asignaciones del tipo de recurso problemático
        critical_allocations = [
            allocation for allocation in self.active_allocations.values()
            if allocation.resource_type == resource_type
        ]
        
        if critical_allocations:
            # Ordenar por prioridad (asignaciones más recientes primero)
            critical_allocations.sort(key=lambda x: x.start_time, reverse=True)
            
            # Considerar liberar recursos de asignaciones de baja prioridad
            for allocation in critical_allocations[:2]:  # Máximo 2
                logger.warning(f"Considerando liberar recursos de {allocation.step_id} "
                             f"debido a alerta crítica")
    
    def _update_avg_allocation_time(self, allocation_time: float):
        """Actualiza el tiempo promedio de asignación"""
        
        current_avg = self.allocation_metrics['avg_allocation_time']
        total_allocations = self.allocation_metrics['successful_allocations']
        
        if total_allocations > 1:
            new_avg = ((current_avg * (total_allocations - 1)) + allocation_time) / total_allocations
            self.allocation_metrics['avg_allocation_time'] = new_avg
        else:
            self.allocation_metrics['avg_allocation_time'] = allocation_time
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Obtiene estado actual de recursos"""
        
        current_metrics = self.resource_monitor.get_current_metrics()
        
        status = {
            'current_usage': current_metrics,
            'limits': {
                rt.value: {
                    'max_value': limit.max_value,
                    'current_value': limit.current_value,
                    'unit': limit.unit,
                    'utilization': (limit.current_value / limit.max_value) * 100 if limit.max_value > 0 else 0
                }
                for rt, limit in self.resource_limits.items()
            },
            'active_allocations': len(self.active_allocations),
            'queued_requests': len(self.allocation_queue),
            'system_info': self.resource_monitor.get_system_info()
        }
        
        return status
    
    def get_allocation_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de asignaciones"""
        
        return self.allocation_metrics.copy()
    
    def set_resource_limit(self, resource_type: ResourceType, max_value: float, unit: str = ""):
        """Establece límite para un tipo de recurso"""
        
        self.resource_limits[resource_type] = ResourceLimit(
            resource_type=resource_type,
            max_value=max_value,
            unit=unit
        )
        
        logger.info(f"Límite establecido para {resource_type.value}: {max_value} {unit}")
    
    def get_resource_recommendations(self) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones de optimización de recursos"""
        
        recommendations = []
        
        # Analizar uso histórico
        historical_metrics = self.resource_monitor.get_historical_metrics(duration=1800)  # 30 minutos
        
        if historical_metrics:
            # Calcular promedios
            avg_metrics = {}
            for resource_type in ResourceType:
                if resource_type in [ResourceType.CPU, ResourceType.MEMORY, ResourceType.DISK]:
                    values = [
                        entry['metrics'].get(resource_type, 0.0)
                        for entry in historical_metrics
                    ]
                    avg_metrics[resource_type] = sum(values) / len(values) if values else 0.0
            
            # Generar recomendaciones
            for resource_type, avg_usage in avg_metrics.items():
                if avg_usage > 80:
                    recommendations.append({
                        'type': 'high_usage',
                        'resource': resource_type.value,
                        'message': f"Uso elevado de {resource_type.value}: {avg_usage:.1f}%",
                        'recommendation': "Considerar optimización o aumento de límites"
                    })
                elif avg_usage < 20:
                    recommendations.append({
                        'type': 'low_usage',
                        'resource': resource_type.value,
                        'message': f"Uso bajo de {resource_type.value}: {avg_usage:.1f}%",
                        'recommendation': "Recursos subutilizados, considerar reducir límites"
                    })
        
        return recommendations
    
    def optimize_resource_allocation(self):
        """Optimiza la asignación de recursos"""
        
        logger.info("Iniciando optimización de recursos")
        
        # Analizar asignaciones activas
        for step_id, allocation in self.active_allocations.items():
            # Verificar si la asignación está subutilizada
            if allocation.actual_usage < allocation.allocated_amount * 0.5:
                logger.info(f"Asignación subutilizada detectada: {step_id}")
                
                # Considerar reducir asignación
                new_amount = max(allocation.actual_usage * 1.2, allocation.allocated_amount * 0.6)
                difference = allocation.allocated_amount - new_amount
                
                if difference > 0:
                    allocation.allocated_amount = new_amount
                    
                    # Actualizar límite
                    if allocation.resource_type in self.resource_limits:
                        limit = self.resource_limits[allocation.resource_type]
                        limit.current_value -= difference
                    
                    logger.info(f"Asignación optimizada para {step_id}: {new_amount}")
        
        # Procesar cola después de optimización
        asyncio.create_task(self._process_queue())
    
    def cleanup_expired_allocations(self):
        """Limpia asignaciones expiradas"""
        
        current_time = time.time()
        expired_allocations = []
        
        for step_id, allocation in self.active_allocations.items():
            if current_time - allocation.start_time > allocation.expected_duration:
                expired_allocations.append(step_id)
        
        for step_id in expired_allocations:
            logger.warning(f"Liberando asignación expirada: {step_id}")
            self.release_resources(step_id)
            self.allocation_metrics['timeout_allocations'] += 1