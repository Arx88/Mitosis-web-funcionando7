"""
Sistema de Administración de Tareas para el agente Mitosis
Maneja planificación, ejecución, monitoreo y adaptación de tareas
"""

import logging
import time
import json
import uuid
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from datetime import datetime

from memory_manager import MemoryManager, TaskMemory

class TaskStatus(Enum):
    """Estados posibles de una tarea"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PhaseStatus(Enum):
    """Estados posibles de una fase"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TaskPhase:
    """Representa una fase de una tarea"""
    id: int
    title: str
    description: str
    required_capabilities: List[str]
    status: PhaseStatus = PhaseStatus.PENDING
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    results: Dict[str, Any] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}

@dataclass
class Task:
    """Representa una tarea completa"""
    id: str
    title: str
    description: str
    goal: str
    phases: List[TaskPhase]
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1  # 1 = alta, 2 = media, 3 = baja
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    current_phase_id: Optional[int] = None
    context: Dict[str, Any] = None
    results: Dict[str, Any] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.context is None:
            self.context = {}
        if self.results is None:
            self.results = {}

class TaskManager:
    """Gestor de tareas para el agente Mitosis"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(__name__)
        
        # Estado del gestor
        self.active_tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []  # IDs de tareas en cola
        self.current_task_id: Optional[str] = None
        
        # Configuración
        self.max_concurrent_tasks = 1  # Por ahora, solo una tarea a la vez
        self.auto_retry_failed_phases = True
        self.max_retries = 3
        
        # Callbacks para herramientas y acciones
        self.tool_callbacks: Dict[str, Callable] = {}
        self.phase_callbacks: Dict[str, Callable] = {}
        
        # Monitoreo
        self.monitoring_enabled = True
        self.monitoring_interval = 30  # segundos
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        
    def create_task(self, title: str, description: str, goal: str, 
                   phases: List[Dict[str, Any]], priority: int = 1,
                   context: Optional[Dict[str, Any]] = None) -> str:
        """Crea una nueva tarea"""
        task_id = str(uuid.uuid4())
        
        # Convertir fases del diccionario a objetos TaskPhase
        task_phases = []
        for phase_data in phases:
            phase = TaskPhase(
                id=phase_data.get('id'),
                title=phase_data.get('title'),
                description=phase_data.get('description', ''),
                required_capabilities=phase_data.get('required_capabilities', [])
            )
            task_phases.append(phase)
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            goal=goal,
            phases=task_phases,
            priority=priority,
            context=context or {}
        )
        
        self.active_tasks[task_id] = task
        self.task_queue.append(task_id)
        
        # Guardar en memoria a largo plazo
        self._save_task_to_memory(task)
        
        self.logger.info(f"Tarea creada: {task_id} - {title}")
        return task_id
    
    def start_task(self, task_id: str) -> bool:
        """Inicia la ejecución de una tarea"""
        if task_id not in self.active_tasks:
            self.logger.error(f"Tarea {task_id} no encontrada")
            return False
        
        task = self.active_tasks[task_id]
        
        if task.status != TaskStatus.PENDING:
            self.logger.warning(f"Tarea {task_id} no está en estado pendiente")
            return False
        
        # Verificar si podemos ejecutar más tareas
        if self.current_task_id and self.max_concurrent_tasks <= 1:
            self.logger.info(f"Tarea {task_id} añadida a la cola (tarea actual: {self.current_task_id})")
            return True
        
        # Iniciar la tarea
        task.status = TaskStatus.ACTIVE
        task.started_at = time.time()
        self.current_task_id = task_id
        
        # Iniciar la primera fase
        if task.phases:
            task.current_phase_id = task.phases[0].id
            task.phases[0].status = PhaseStatus.ACTIVE
            task.phases[0].started_at = time.time()
        
        self._save_task_to_memory(task)
        
        # Iniciar monitoreo si no está activo
        if self.monitoring_enabled and not self._monitoring_thread:
            self._start_monitoring()
        
        self.logger.info(f"Tarea iniciada: {task_id}")
        return True
    
    def advance_phase(self, task_id: str, from_phase_id: int, to_phase_id: int,
                     results: Optional[Dict[str, Any]] = None) -> bool:
        """Avanza de una fase a la siguiente"""
        if task_id not in self.active_tasks:
            self.logger.error(f"Tarea {task_id} no encontrada")
            return False
        
        task = self.active_tasks[task_id]
        
        # Verificar que la fase actual es la correcta
        if task.current_phase_id != from_phase_id:
            self.logger.error(f"Fase actual {task.current_phase_id} no coincide con {from_phase_id}")
            return False
        
        # Encontrar las fases
        current_phase = None
        next_phase = None
        
        for phase in task.phases:
            if phase.id == from_phase_id:
                current_phase = phase
            elif phase.id == to_phase_id:
                next_phase = phase
        
        if not current_phase or not next_phase:
            self.logger.error(f"Fases {from_phase_id} o {to_phase_id} no encontradas")
            return False
        
        # Completar la fase actual
        current_phase.status = PhaseStatus.COMPLETED
        current_phase.completed_at = time.time()
        if results:
            current_phase.results.update(results)
        
        # Iniciar la siguiente fase
        next_phase.status = PhaseStatus.ACTIVE
        next_phase.started_at = time.time()
        task.current_phase_id = to_phase_id
        
        self._save_task_to_memory(task)
        
        self.logger.info(f"Tarea {task_id}: avanzado de fase {from_phase_id} a {to_phase_id}")
        return True
    
    def complete_task(self, task_id: str, results: Optional[Dict[str, Any]] = None) -> bool:
        """Completa una tarea"""
        if task_id not in self.active_tasks:
            self.logger.error(f"Tarea {task_id} no encontrada")
            return False
        
        task = self.active_tasks[task_id]
        
        # Completar la fase actual si está activa
        if task.current_phase_id:
            current_phase = next((p for p in task.phases if p.id == task.current_phase_id), None)
            if current_phase and current_phase.status == PhaseStatus.ACTIVE:
                current_phase.status = PhaseStatus.COMPLETED
                current_phase.completed_at = time.time()
        
        # Completar la tarea
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        if results:
            task.results.update(results)
        
        # Limpiar estado actual
        if self.current_task_id == task_id:
            self.current_task_id = None
        
        # Remover de la cola si está ahí
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
        
        self._save_task_to_memory(task)
        
        # Procesar siguiente tarea en la cola
        self._process_next_task()
        
        self.logger.info(f"Tarea completada: {task_id}")
        return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Marca una tarea como fallida"""
        if task_id not in self.active_tasks:
            self.logger.error(f"Tarea {task_id} no encontrada")
            return False
        
        task = self.active_tasks[task_id]
        
        # Fallar la fase actual si está activa
        if task.current_phase_id:
            current_phase = next((p for p in task.phases if p.id == task.current_phase_id), None)
            if current_phase and current_phase.status == PhaseStatus.ACTIVE:
                current_phase.status = PhaseStatus.FAILED
                current_phase.error_message = error_message
        
        # Fallar la tarea
        task.status = TaskStatus.FAILED
        task.error_message = error_message
        
        # Limpiar estado actual
        if self.current_task_id == task_id:
            self.current_task_id = None
        
        # Remover de la cola
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
        
        self._save_task_to_memory(task)
        
        # Procesar siguiente tarea en la cola
        self._process_next_task()
        
        self.logger.error(f"Tarea fallida: {task_id} - {error_message}")
        return True
    
    def pause_task(self, task_id: str) -> bool:
        """Pausa una tarea activa"""
        if task_id not in self.active_tasks:
            self.logger.error(f"Tarea {task_id} no encontrada")
            return False
        
        task = self.active_tasks[task_id]
        
        if task.status != TaskStatus.ACTIVE:
            self.logger.warning(f"Tarea {task_id} no está activa")
            return False
        
        task.status = TaskStatus.PAUSED
        
        # Limpiar estado actual si es la tarea actual
        if self.current_task_id == task_id:
            self.current_task_id = None
        
        self._save_task_to_memory(task)
        
        # Procesar siguiente tarea en la cola
        self._process_next_task()
        
        self.logger.info(f"Tarea pausada: {task_id}")
        return True
    
    def resume_task(self, task_id: str) -> bool:
        """Reanuda una tarea pausada"""
        if task_id not in self.active_tasks:
            self.logger.error(f"Tarea {task_id} no encontrada")
            return False
        
        task = self.active_tasks[task_id]
        
        if task.status != TaskStatus.PAUSED:
            self.logger.warning(f"Tarea {task_id} no está pausada")
            return False
        
        # Verificar si podemos reanudar
        if self.current_task_id and self.max_concurrent_tasks <= 1:
            # Añadir al frente de la cola
            if task_id in self.task_queue:
                self.task_queue.remove(task_id)
            self.task_queue.insert(0, task_id)
            self.logger.info(f"Tarea {task_id} añadida al frente de la cola")
            return True
        
        # Reanudar inmediatamente
        task.status = TaskStatus.ACTIVE
        self.current_task_id = task_id
        
        self._save_task_to_memory(task)
        
        self.logger.info(f"Tarea reanudada: {task_id}")
        return True
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Obtiene una tarea por su ID"""
        return self.active_tasks.get(task_id)
    
    def get_current_task(self) -> Optional[Task]:
        """Obtiene la tarea actualmente en ejecución"""
        if self.current_task_id:
            return self.active_tasks.get(self.current_task_id)
        return None
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Obtiene el estado de una tarea"""
        task = self.get_task(task_id)
        return task.status if task else None
    
    def get_current_phase(self, task_id: str) -> Optional[TaskPhase]:
        """Obtiene la fase actual de una tarea"""
        task = self.get_task(task_id)
        if task and task.current_phase_id:
            return next((p for p in task.phases if p.id == task.current_phase_id), None)
        return None
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """Lista todas las tareas, opcionalmente filtradas por estado"""
        tasks = list(self.active_tasks.values())
        if status:
            tasks = [task for task in tasks if task.status == status]
        
        # Ordenar por prioridad y fecha de creación
        tasks.sort(key=lambda t: (t.priority, t.created_at))
        return tasks
    
    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """Obtiene el progreso de una tarea"""
        task = self.get_task(task_id)
        if not task:
            return {}
        
        total_phases = len(task.phases)
        completed_phases = len([p for p in task.phases if p.status == PhaseStatus.COMPLETED])
        failed_phases = len([p for p in task.phases if p.status == PhaseStatus.FAILED])
        
        progress_percentage = (completed_phases / total_phases * 100) if total_phases > 0 else 0
        
        return {
            "task_id": task_id,
            "status": task.status.value,
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "failed_phases": failed_phases,
            "current_phase_id": task.current_phase_id,
            "progress_percentage": round(progress_percentage, 2),
            "elapsed_time": time.time() - task.created_at,
            "estimated_remaining": self._estimate_remaining_time(task)
        }
    
    def _estimate_remaining_time(self, task: Task) -> Optional[float]:
        """Estima el tiempo restante para completar una tarea"""
        if not task.started_at:
            return None
        
        completed_phases = [p for p in task.phases if p.status == PhaseStatus.COMPLETED]
        if not completed_phases:
            return None
        
        # Calcular tiempo promedio por fase completada
        total_time = 0
        for phase in completed_phases:
            if phase.started_at and phase.completed_at:
                total_time += phase.completed_at - phase.started_at
        
        avg_time_per_phase = total_time / len(completed_phases)
        remaining_phases = len([p for p in task.phases if p.status == PhaseStatus.PENDING])
        
        return avg_time_per_phase * remaining_phases
    
    def _process_next_task(self):
        """Procesa la siguiente tarea en la cola"""
        if self.current_task_id or not self.task_queue:
            return
        
        next_task_id = self.task_queue.pop(0)
        task = self.active_tasks.get(next_task_id)
        
        if task and task.status in [TaskStatus.PENDING, TaskStatus.PAUSED]:
            self.start_task(next_task_id)
    
    def _save_task_to_memory(self, task: Task):
        """Guarda una tarea en la memoria a largo plazo"""
        task_memory = TaskMemory(
            task_id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            created_at=task.created_at,
            updated_at=time.time(),
            phases=[asdict(phase) for phase in task.phases],
            results=task.results,
            tools_used=[]  # Se puede expandir para rastrear herramientas usadas
        )
        
        self.memory_manager.save_task_memory(task_memory)
    
    def _start_monitoring(self):
        """Inicia el hilo de monitoreo de tareas"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self._monitoring_thread.daemon = True
        self._monitoring_thread.start()
        
        self.logger.info("Monitoreo de tareas iniciado")
    
    def _stop_monitoring_thread(self):
        """Detiene el hilo de monitoreo"""
        self._stop_monitoring.set()
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        
        self.logger.info("Monitoreo de tareas detenido")
    
    def _monitoring_loop(self):
        """Bucle principal de monitoreo"""
        while not self._stop_monitoring.wait(self.monitoring_interval):
            try:
                self._check_task_health()
                self._cleanup_completed_tasks()
            except Exception as e:
                self.logger.error(f"Error en monitoreo: {e}")
    
    def _check_task_health(self):
        """Verifica la salud de las tareas activas"""
        current_time = time.time()
        
        for task in self.active_tasks.values():
            if task.status == TaskStatus.ACTIVE:
                # Verificar si la tarea está estancada
                if task.current_phase_id:
                    current_phase = next((p for p in task.phases if p.id == task.current_phase_id), None)
                    if current_phase and current_phase.started_at:
                        phase_duration = current_time - current_phase.started_at
                        
                        # Si una fase lleva más de 1 hora, marcarla como posiblemente estancada
                        if phase_duration > 3600:  # 1 hora
                            self.logger.warning(f"Fase {current_phase.id} de tarea {task.id} lleva {phase_duration/60:.1f} minutos")
    
    def _cleanup_completed_tasks(self):
        """Limpia tareas completadas antiguas de la memoria activa"""
        current_time = time.time()
        tasks_to_remove = []
        
        for task_id, task in self.active_tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                # Mantener tareas completadas por 24 horas
                if task.completed_at and (current_time - task.completed_at) > 86400:  # 24 horas
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]
            self.logger.info(f"Tarea {task_id} removida de memoria activa")
    
    def get_manager_status(self) -> Dict[str, Any]:
        """Obtiene el estado del gestor de tareas"""
        return {
            "active_tasks_count": len(self.active_tasks),
            "queue_length": len(self.task_queue),
            "current_task_id": self.current_task_id,
            "monitoring_enabled": self.monitoring_enabled,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_status_counts": {
                status.value: len([t for t in self.active_tasks.values() if t.status == status])
                for status in TaskStatus
            }
        }

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear gestor de memoria y tareas
    memory = MemoryManager()
    task_manager = TaskManager(memory)
    
    # Crear una tarea de ejemplo
    phases = [
        {"id": 1, "title": "Análisis", "required_capabilities": ["analysis"]},
        {"id": 2, "title": "Implementación", "required_capabilities": ["coding"]},
        {"id": 3, "title": "Testing", "required_capabilities": ["testing"]},
        {"id": 4, "title": "Documentación", "required_capabilities": ["writing"]}
    ]
    
    task_id = task_manager.create_task(
        title="Desarrollar función de cálculo",
        description="Crear una función para calcular estadísticas",
        goal="Implementar y documentar una función de cálculo estadístico",
        phases=phases,
        priority=1
    )
    
    print(f"✅ Tarea creada: {task_id}")
    
    # Iniciar la tarea
    task_manager.start_task(task_id)
    print(f"🚀 Tarea iniciada")
    
    # Simular progreso
    time.sleep(1)
    task_manager.advance_phase(task_id, 1, 2, {"analysis_results": "Análisis completado"})
    print(f"📈 Avanzado a fase 2")
    
    # Obtener progreso
    progress = task_manager.get_task_progress(task_id)
    print(f"📊 Progreso: {progress['progress_percentage']}%")
    
    # Completar tarea
    task_manager.complete_task(task_id, {"final_result": "Función implementada exitosamente"})
    print(f"✅ Tarea completada")
    
    # Mostrar estado del gestor
    status = task_manager.get_manager_status()
    print(f"📋 Estado del gestor: {status}")
    
    # Detener monitoreo
    task_manager._stop_monitoring_thread()

