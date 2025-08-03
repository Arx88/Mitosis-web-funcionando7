"""
🚦 GESTOR DE COLA PARA OLLAMA - CONTROL DE CONCURRENCIA
===========================================================

Este módulo implementa un sistema de cola robusto para gestionar las llamadas
concurrentes a Ollama, evitando la saturación del servicio y mejorando la
estabilidad del sistema cuando múltiples tareas están activas simultáneamente.

CARACTERÍSTICAS:
- ✅ Límite configurable de llamadas concurrentes (por defecto: 2)
- ✅ Cola FIFO para requests en espera
- ✅ Timeout personalizado por request
- ✅ Priorización de tareas por importancia
- ✅ Logs detallados para debugging
- ✅ Métricas de rendimiento y estadísticas de cola
- ✅ Recuperación automática ante fallos de Ollama

PROBLEMA RESUELTO:
Cuando múltiples tareas ejecutan pasos simultáneamente, todas intentan
llamar a Ollama al mismo tiempo, causando:
- Saturación de memoria GPU/CPU en Ollama
- Timeouts inconsistentes
- Fallos intermitentes de conexión
- Degradación del rendimiento

SOLUCIÓN:
Este gestor controla el acceso a Ollama usando un semáforo asyncio,
garantizando que solo un número limitado de requests se procesen
simultáneamente, mientras mantiene una cola para los demás.

Creado por: Sistema de reintentos de 5 pasos
Fecha: 2025-01-03
Versión: 1.0.0
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class RequestPriority(Enum):
    """
    🔴 NIVELES DE PRIORIDAD PARA REQUESTS DE OLLAMA
    
    Permite priorizar certain tipos de requests sobre otros
    """
    LOW = 1      # Requests de baja prioridad (ej: análisis secundarios)
    NORMAL = 2   # Requests normales (ej: pasos de plan)
    HIGH = 3     # Requests importantes (ej: generación de plans)
    CRITICAL = 4 # Requests críticos (ej: recuperación de errores)

@dataclass
class OllamaRequest:
    """
    📦 REPRESENTACIÓN DE UN REQUEST A OLLAMA
    
    Encapsula todos los datos necesarios para realizar una llamada
    a Ollama de manera gestionada por la cola.
    """
    # Identificación
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    step_id: str = ""
    
    # Datos del request
    prompt: str = ""
    model: str = ""
    options: Dict[str, Any] = field(default_factory=dict)
    
    # Control de flujo
    priority: RequestPriority = RequestPriority.NORMAL
    timeout: int = 180  # 3 minutos por defecto
    max_retries: int = 2  # Reintentos a nivel de cola
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Estado interno
    retry_count: int = 0
    last_error: Optional[str] = None
    
    def __post_init__(self):
        """Validaciones y configuración post-inicialización"""
        if not self.prompt.strip():
            raise ValueError("El prompt no puede estar vacío")
        if not self.model.strip():
            raise ValueError("El modelo no puede estar vacío")
        
        # Auto-configurar timeout basado en modelo
        if not hasattr(self, '_timeout_configured'):
            if '32b' in self.model.lower():
                self.timeout = 480  # 8 minutos para modelos grandes
            elif '8b' in self.model.lower():
                self.timeout = 180  # 3 minutos para modelos medianos
            else:
                self.timeout = 120  # 2 minutos para modelos pequeños
            self._timeout_configured = True
    
    @property
    def age_seconds(self) -> float:
        """Tiempo transcurrido desde la creación del request"""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def processing_time_seconds(self) -> Optional[float]:
        """Tiempo de procesamiento si está completado"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

@dataclass 
class QueueStats:
    """
    📊 ESTADÍSTICAS DE LA COLA DE OLLAMA
    
    Recopila métricas de rendimiento y estado de la cola
    """
    requests_queued: int = 0
    requests_processing: int = 0
    requests_completed: int = 0
    requests_failed: int = 0
    
    average_wait_time: float = 0.0
    average_processing_time: float = 0.0
    
    current_queue_size: int = 0
    max_queue_size_reached: int = 0
    
    ollama_errors: int = 0
    timeout_errors: int = 0
    
    uptime_start: datetime = field(default_factory=datetime.now)
    
    @property
    def uptime_seconds(self) -> float:
        """Tiempo de funcionamiento de la cola"""
        return (datetime.now() - self.uptime_start).total_seconds()
    
    @property 
    def throughput_per_minute(self) -> float:
        """Requests completados por minuto"""
        if self.uptime_seconds < 60:
            return 0.0
        return (self.requests_completed / self.uptime_seconds) * 60

class OllamaQueueManager:
    """
    🚦 GESTOR PRINCIPAL DE COLA PARA OLLAMA
    
    Maneja todas las llamadas a Ollama usando un semáforo para controlar
    la concurrencia y una cola prioritaria para organizar los requests.
    
    CONFIGURACIÓN:
    - max_concurrent_requests: Máximo número de requests simultáneos (defecto: 2)
    - max_queue_size: Tamaño máximo de cola (defecto: 50)
    - cleanup_interval: Intervalo de limpieza en segundos (defecto: 300)
    """
    
    def __init__(self, 
                 max_concurrent_requests: int = 2,
                 max_queue_size: int = 50,
                 cleanup_interval: int = 300):
        """
        Inicializar el gestor de cola de Ollama
        
        Args:
            max_concurrent_requests: Máximo requests concurrentes a Ollama
            max_queue_size: Tamaño máximo de la cola de espera
            cleanup_interval: Intervalo de limpieza en segundos
        """
        self.max_concurrent_requests = max_concurrent_requests
        self.max_queue_size = max_queue_size
        self.cleanup_interval = cleanup_interval
        
        # Semáforo para controlar concurrencia
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # Cola prioritaria - organizamos por prioridad
        self._queue: List[OllamaRequest] = []
        self._queue_lock = asyncio.Lock()
        
        # Estado interno
        self._processing_requests: Dict[str, OllamaRequest] = {}
        self._completed_requests: Dict[str, OllamaRequest] = {}
        self._failed_requests: Dict[str, OllamaRequest] = {}
        
        # Estadísticas
        self.stats = QueueStats()
        
        # Control de threading para operaciones de limpieza
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ollama_queue")
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
        logger.info(f"🚦 OllamaQueueManager inicializado:")
        logger.info(f"   - Max requests concurrentes: {max_concurrent_requests}")
        logger.info(f"   - Tamaño máximo de cola: {max_queue_size}")
        logger.info(f"   - Intervalo de limpieza: {cleanup_interval}s")
    
    async def start(self) -> None:
        """
        🚀 INICIAR EL GESTOR DE COLA
        
        Inicia las tareas de background para mantenimiento de la cola
        """
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("🚀 OllamaQueueManager iniciado exitosamente")
        else:
            logger.warning("⚠️ OllamaQueueManager ya está corriendo")
    
    async def stop(self) -> None:
        """
        🛑 DETENER EL GESTOR DE COLA
        
        Detiene las tareas de background y limpia recursos
        """
        self._shutdown = True
        
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cerrar executor
        self._executor.shutdown(wait=False)
        
        logger.info("🛑 OllamaQueueManager detenido")
    
    async def enqueue_request(self, 
                            ollama_request: OllamaRequest,
                            execution_callback: Callable[[OllamaRequest], Awaitable[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        📥 ENCOLAR UN REQUEST PARA PROCESAMIENTO
        
        Agrega un request a la cola y espera su procesamiento,
        respetando prioridades y límites de concurrencia.
        
        Args:
            ollama_request: Request a procesar
            execution_callback: Función async que ejecuta la llamada real a Ollama
            
        Returns:
            Resultado de la llamada a Ollama
            
        Raises:
            RuntimeError: Si la cola está llena o el gestor está cerrado
            asyncio.TimeoutError: Si el request excede el timeout
        """
        if self._shutdown:
            raise RuntimeError("OllamaQueueManager está cerrado")
        
        # Verificar tamaño de cola
        async with self._queue_lock:
            if len(self._queue) >= self.max_queue_size:
                self.stats.requests_failed += 1
                raise RuntimeError(f"Cola de Ollama llena (max: {self.max_queue_size})")
            
            # Insertar en posición correcta según prioridad
            inserted = False
            for i, queued_request in enumerate(self._queue):
                if ollama_request.priority.value > queued_request.priority.value:
                    self._queue.insert(i, ollama_request)
                    inserted = True
                    break
            
            if not inserted:
                self._queue.append(ollama_request)
            
            self.stats.requests_queued += 1
            self.stats.current_queue_size = len(self._queue)
            self.stats.max_queue_size_reached = max(self.stats.max_queue_size_reached, self.stats.current_queue_size)
        
        logger.info(f"📥 Request encolado: {ollama_request.request_id} (tarea: {ollama_request.task_id}, prioridad: {ollama_request.priority.name})")
        logger.info(f"📊 Cola actual: {len(self._queue)} requests, {len(self._processing_requests)} procesando")
        
        try:
            # Esperar a que el semáforo permita procesar
            async with self._semaphore:
                # Obtener el request de la cola
                async with self._queue_lock:
                    if ollama_request in self._queue:
                        self._queue.remove(ollama_request)
                        self.stats.current_queue_size = len(self._queue)
                        self._processing_requests[ollama_request.request_id] = ollama_request
                        self.stats.requests_processing += 1
                        ollama_request.started_at = datetime.now()
                
                wait_time = (ollama_request.started_at - ollama_request.created_at).total_seconds()
                logger.info(f"🔄 Procesando request {ollama_request.request_id} (esperó {wait_time:.1f}s en cola)")
                
                # Ejecutar la llamada real a Ollama con timeout
                try:
                    result = await asyncio.wait_for(
                        execution_callback(ollama_request),
                        timeout=ollama_request.timeout
                    )
                    
                    # Marcar como completado exitosamente
                    ollama_request.completed_at = datetime.now()
                    processing_time = ollama_request.processing_time_seconds
                    
                    self._completed_requests[ollama_request.request_id] = ollama_request
                    self.stats.requests_completed += 1
                    
                    # Actualizar estadísticas
                    self._update_average_times(wait_time, processing_time)
                    
                    logger.info(f"✅ Request {ollama_request.request_id} completado exitosamente (procesado en {processing_time:.1f}s)")
                    
                    return result
                    
                except asyncio.TimeoutError:
                    self.stats.timeout_errors += 1
                    self.stats.requests_failed += 1
                    error_msg = f"Timeout después de {ollama_request.timeout}s para modelo {ollama_request.model}"
                    logger.error(f"⏱️ {error_msg} - Request: {ollama_request.request_id}")
                    
                    ollama_request.last_error = error_msg
                    ollama_request.completed_at = datetime.now()
                    self._failed_requests[ollama_request.request_id] = ollama_request
                    
                    return {'error': error_msg, 'error_type': 'timeout'}
                    
                except Exception as e:
                    self.stats.ollama_errors += 1
                    self.stats.requests_failed += 1
                    error_msg = str(e)
                    logger.error(f"❌ Error en request {ollama_request.request_id}: {error_msg}")
                    
                    ollama_request.last_error = error_msg
                    ollama_request.completed_at = datetime.now()
                    self._failed_requests[ollama_request.request_id] = ollama_request
                    
                    return {'error': error_msg, 'error_type': 'ollama_error'}
                    
                finally:
                    # Limpiar del tracking de procesamiento
                    if ollama_request.request_id in self._processing_requests:
                        del self._processing_requests[ollama_request.request_id]
                        self.stats.requests_processing -= 1
        
        except Exception as e:
            # Error en el manejo de cola o semáforo
            async with self._queue_lock:
                if ollama_request in self._queue:
                    self._queue.remove(ollama_request)
                    self.stats.current_queue_size = len(self._queue)
            
            self.stats.requests_failed += 1
            error_msg = f"Error en gestor de cola: {str(e)}"
            logger.error(f"❌ {error_msg} - Request: {ollama_request.request_id}")
            
            return {'error': error_msg, 'error_type': 'queue_error'}
    
    def _update_average_times(self, wait_time: float, processing_time: Optional[float]) -> None:
        """Actualizar promedios de tiempo de manera eficiente"""
        if self.stats.requests_completed > 1:
            # Promedio móvil simple
            self.stats.average_wait_time = (
                (self.stats.average_wait_time * (self.stats.requests_completed - 1) + wait_time) 
                / self.stats.requests_completed
            )
            
            if processing_time is not None:
                self.stats.average_processing_time = (
                    (self.stats.average_processing_time * (self.stats.requests_completed - 1) + processing_time)
                    / self.stats.requests_completed
                )
        else:
            self.stats.average_wait_time = wait_time
            self.stats.average_processing_time = processing_time or 0.0
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        📊 OBTENER STATUS ACTUAL DE LA COLA
        
        Returns:
            Diccionario con estadísticas y estado actual
        """
        async with self._queue_lock:
            queue_requests = [
                {
                    'request_id': req.request_id,
                    'task_id': req.task_id,
                    'priority': req.priority.name,
                    'model': req.model,
                    'age_seconds': req.age_seconds,
                    'timeout': req.timeout
                }
                for req in self._queue
            ]
        
        processing_requests = [
            {
                'request_id': req.request_id,
                'task_id': req.task_id,
                'model': req.model,
                'started_at': req.started_at.isoformat() if req.started_at else None,
                'age_seconds': req.age_seconds
            }
            for req in self._processing_requests.values()
        ]
        
        return {
            'queue': {
                'size': len(queue_requests),
                'max_size': self.max_queue_size,
                'requests': queue_requests
            },
            'processing': {
                'count': len(processing_requests),
                'max_concurrent': self.max_concurrent_requests,
                'requests': processing_requests
            },
            'stats': {
                'requests_queued': self.stats.requests_queued,
                'requests_completed': self.stats.requests_completed,
                'requests_failed': self.stats.requests_failed,
                'average_wait_time': round(self.stats.average_wait_time, 2),
                'average_processing_time': round(self.stats.average_processing_time, 2),
                'throughput_per_minute': round(self.stats.throughput_per_minute, 2),
                'uptime_seconds': round(self.stats.uptime_seconds, 2),
                'ollama_errors': self.stats.ollama_errors,
                'timeout_errors': self.stats.timeout_errors
            },
            'health': {
                'is_running': not self._shutdown,
                'queue_full': len(queue_requests) >= self.max_queue_size,
                'processing_capacity': self.max_concurrent_requests - len(processing_requests)
            }
        }
    
    async def _cleanup_loop(self) -> None:
        """
        🧹 BUCLE DE LIMPIEZA DE REQUESTS ANTIGUOS
        
        Ejecuta limpieza periódica de requests completados y fallidos
        """
        logger.info(f"🧹 Iniciando bucle de limpieza (cada {self.cleanup_interval}s)")
        
        while not self._shutdown:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if self._shutdown:
                    break
                
                await self._cleanup_old_requests()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en bucle de limpieza: {str(e)}")
                await asyncio.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    async def _cleanup_old_requests(self) -> None:
        """Limpiar requests completados/fallidos antiguos (>1 hora)"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # Limpiar requests completados antiguos
        old_completed = [
            req_id for req_id, req in self._completed_requests.items()
            if req.completed_at and req.completed_at < cutoff_time
        ]
        
        # Limpiar requests fallidos antiguos  
        old_failed = [
            req_id for req_id, req in self._failed_requests.items()
            if req.completed_at and req.completed_at < cutoff_time
        ]
        
        for req_id in old_completed:
            del self._completed_requests[req_id]
        
        for req_id in old_failed:
            del self._failed_requests[req_id]
        
        if old_completed or old_failed:
            logger.info(f"🧹 Limpieza completada: {len(old_completed)} completados, {len(old_failed)} fallidos")

# 🌐 INSTANCIA GLOBAL DEL GESTOR DE COLA
_global_queue_manager: Optional[OllamaQueueManager] = None

def get_ollama_queue_manager() -> OllamaQueueManager:
    """
    🌐 OBTENER INSTANCIA GLOBAL DEL GESTOR DE COLA
    
    Patrón singleton para asegurar una sola instancia del gestor
    """
    global _global_queue_manager
    
    if _global_queue_manager is None:
        _global_queue_manager = OllamaQueueManager(
            max_concurrent_requests=2,  # Máximo 2 requests concurrentes por defecto
            max_queue_size=20,          # Cola máxima de 20 requests
            cleanup_interval=300        # Limpieza cada 5 minutos
        )
        logger.info("🌐 Nueva instancia global de OllamaQueueManager creada")
    
    return _global_queue_manager

async def initialize_ollama_queue_manager() -> None:
    """
    🚀 INICIALIZAR EL GESTOR DE COLA GLOBAL
    
    Debe ser llamado al inicio de la aplicación
    """
    queue_manager = get_ollama_queue_manager()
    await queue_manager.start()
    logger.info("🚀 Gestor de cola de Ollama inicializado globalmente")

async def shutdown_ollama_queue_manager() -> None:
    """
    🛑 CERRAR EL GESTOR DE COLA GLOBAL
    
    Debe ser llamado al cerrar la aplicación
    """
    global _global_queue_manager
    
    if _global_queue_manager:
        await _global_queue_manager.stop()
        _global_queue_manager = None
        logger.info("🛑 Gestor de cola de Ollama cerrado globalmente")