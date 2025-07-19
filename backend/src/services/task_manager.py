"""
Task Manager Service - Persistencia del Estado de Tareas
Mejora implementada según UPGRADE.md Sección 5: Persistencia del Estado de Tareas

Centraliza la gestión de tareas migrando del almacenamiento en memoria a MongoDB
para garantizar resiliencia y capacidad de recuperación.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import uuid
from .database import DatabaseService

logger = logging.getLogger(__name__)

class TaskManager:
    """Gestor centralizado de tareas con persistencia en MongoDB"""
    
    def __init__(self, db_service: DatabaseService = None):
        self.db_service = db_service or DatabaseService()
        self.active_cache = {}  # Caché de corta duración para reducir latencia
        logger.info("✅ TaskManager initialized with MongoDB persistence")
    
    def create_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """
        Crear una nueva tarea y persistirla en MongoDB
        
        Args:
            task_id: ID único de la tarea
            task_data: Datos completos de la tarea
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            task_document = {
                'task_id': task_id,
                'status': task_data.get('status', 'created'),
                'plan': task_data.get('plan', []),
                'current_step': task_data.get('current_step', 0),
                'message': task_data.get('message', ''),
                'task_type': task_data.get('task_type', 'general'),
                'complexity': task_data.get('complexity', 'media'),
                'ai_generated': task_data.get('ai_generated', False),
                'plan_source': task_data.get('plan_source', 'unknown'),
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'start_time': task_data.get('start_time', datetime.now()),
                'completed_at': task_data.get('completed_at'),
                'final_result': task_data.get('final_result'),
                'error': task_data.get('error'),
                'fallback_reason': task_data.get('fallback_reason'),
                'warning': task_data.get('warning'),
                'metadata': task_data.get('metadata', {})
            }
            
            # Guardar en MongoDB
            result = self.db_service.save_task(task_document)
            
            if result:
                # Actualizar caché
                self.active_cache[task_id] = task_document
                logger.info(f"✅ Task {task_id} created and persisted to MongoDB")
                return True
            else:
                logger.error(f"❌ Failed to persist task {task_id} to MongoDB")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating task {task_id}: {str(e)}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener tarea por ID, primero del caché, luego de MongoDB
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Dict con datos de la tarea o None si no existe
        """
        try:
            # Verificar caché primero
            if task_id in self.active_cache:
                logger.debug(f"📱 Task {task_id} retrieved from cache")
                return self.active_cache[task_id].copy()
            
            # Buscar en MongoDB
            task_data = self.db_service.get_task(task_id)
            
            if task_data:
                # Actualizar caché
                self.active_cache[task_id] = task_data
                logger.debug(f"📥 Task {task_id} retrieved from MongoDB and cached")
                return task_data.copy()
            else:
                logger.warning(f"⚠️ Task {task_id} not found in database")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error retrieving task {task_id}: {str(e)}")
            return None
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Actualizar tarea en MongoDB y caché
        
        Args:
            task_id: ID de la tarea
            updates: Campos a actualizar
            
        Returns:
            bool: True si se actualizó exitosamente
        """
        try:
            # Agregar timestamp de actualización
            updates['updated_at'] = datetime.now()
            
            # Actualizar en MongoDB
            success = self.db_service.update_task(task_id, updates)
            
            if success:
                # Actualizar caché si existe
                if task_id in self.active_cache:
                    self.active_cache[task_id].update(updates)
                
                logger.debug(f"✅ Task {task_id} updated successfully")
                return True
            else:
                logger.error(f"❌ Failed to update task {task_id} in MongoDB")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating task {task_id}: {str(e)}")
            return False
    
    def update_task_step_status(self, task_id: str, step_id: str, new_status: str, 
                              result_summary: str = None, error: str = None) -> bool:
        """
        Actualizar estado específico de un paso de tarea
        
        Args:
            task_id: ID de la tarea
            step_id: ID del paso
            new_status: Nuevo estado del paso
            result_summary: Resumen del resultado (opcional)
            error: Mensaje de error (opcional)
            
        Returns:
            bool: True si se actualizó exitosamente
        """
        try:
            # Obtener tarea actual
            task_data = self.get_task(task_id)
            if not task_data:
                logger.error(f"❌ Task {task_id} not found for step update")
                return False
            
            # Actualizar el paso específico
            plan = task_data.get('plan', [])
            step_updated = False
            
            for step in plan:
                if step.get('id') == step_id:
                    step['status'] = new_status
                    step['updated_at'] = datetime.now().isoformat()
                    
                    if result_summary:
                        step['result_summary'] = result_summary
                    if error:
                        step['error'] = error
                    if new_status == 'completed':
                        step['completed'] = True
                        step['completed_at'] = datetime.now().isoformat()
                    elif new_status == 'failed':
                        step['completed'] = False
                    
                    step_updated = True
                    break
            
            if step_updated:
                # Actualizar toda la tarea con el plan modificado
                updates = {
                    'plan': plan,
                    'updated_at': datetime.now()
                }
                return self.update_task(task_id, updates)
            else:
                logger.warning(f"⚠️ Step {step_id} not found in task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating task step {task_id}/{step_id}: {str(e)}")
            return False
    
    def get_all_tasks(self, limit: int = 100, include_completed: bool = True) -> List[Dict[str, Any]]:
        """
        Obtener todas las tareas con filtros opcionales
        
        Args:
            limit: Número máximo de tareas a retornar
            include_completed: Si incluir tareas completadas
            
        Returns:
            Lista de tareas
        """
        try:
            tasks = self.db_service.get_all_tasks(limit)
            
            if not include_completed:
                tasks = [task for task in tasks if task.get('status') != 'completed']
            
            logger.info(f"📋 Retrieved {len(tasks)} tasks from database")
            return tasks
            
        except Exception as e:
            logger.error(f"❌ Error retrieving all tasks: {str(e)}")
            return []
    
    def get_incomplete_tasks(self) -> List[Dict[str, Any]]:
        """
        Obtener tareas incompletas para recuperación al iniciar
        
        Returns:
            Lista de tareas incompletas
        """
        try:
            all_tasks = self.get_all_tasks(include_completed=False)
            
            # Filtrar tareas en progreso o pendientes
            incomplete_statuses = ['executing', 'in-progress', 'pending', 'created']
            incomplete_tasks = [
                task for task in all_tasks 
                if task.get('status') in incomplete_statuses
            ]
            
            logger.info(f"🔄 Found {len(incomplete_tasks)} incomplete tasks for recovery")
            return incomplete_tasks
            
        except Exception as e:
            logger.error(f"❌ Error retrieving incomplete tasks: {str(e)}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """
        Eliminar tarea y toda su información relacionada
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            # Eliminar de MongoDB
            success = self.db_service.delete_task(task_id)
            
            if success:
                # Eliminar del caché
                if task_id in self.active_cache:
                    del self.active_cache[task_id]
                
                logger.info(f"✅ Task {task_id} deleted successfully")
                return True
            else:
                logger.error(f"❌ Failed to delete task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting task {task_id}: {str(e)}")
            return False
    
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtener historial de tareas para análisis y revisión
        
        Args:
            limit: Número máximo de tareas en el historial
            
        Returns:
            Lista de tareas ordenadas por fecha de creación
        """
        try:
            tasks = self.db_service.get_all_tasks(limit)
            
            # Agregar información de resumen para el historial
            for task in tasks:
                task['summary'] = self._generate_task_summary(task)
            
            logger.info(f"📚 Retrieved task history: {len(tasks)} tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"❌ Error retrieving task history: {str(e)}")
            return []
    
    def cleanup_old_tasks(self, days_old: int = 30) -> Dict[str, int]:
        """
        Limpiar tareas antiguas para mantener la base de datos eficiente
        
        Args:
            days_old: Días de antigüedad para considerar tareas como viejas
            
        Returns:
            Dict con estadísticas de limpieza
        """
        try:
            result = self.db_service.cleanup_old_data(days_old)
            
            # Limpiar caché de tareas eliminadas
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_cache_keys = [
                task_id for task_id, task_data in self.active_cache.items()
                if task_data.get('created_at', datetime.now()) < cutoff_date
            ]
            
            for key in old_cache_keys:
                del self.active_cache[key]
            
            logger.info(f"🧹 Cleanup completed: {result.get('tasks_deleted', 0)} tasks deleted")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old tasks: {str(e)}")
            return {'error': str(e)}
    
    def recover_incomplete_tasks_on_startup(self) -> List[str]:
        """
        Recuperar tareas incompletas al iniciar el backend
        
        Returns:
            Lista de task_ids recuperados
        """
        try:
            incomplete_tasks = self.get_incomplete_tasks()
            recovered_task_ids = []
            
            for task in incomplete_tasks:
                task_id = task.get('task_id')
                if task_id:
                    # Cargar en caché para acceso rápido
                    self.active_cache[task_id] = task
                    recovered_task_ids.append(task_id)
                    
                    # Log del estado de recuperación
                    logger.info(f"🔄 Recovered task {task_id}: {task.get('status')} - {task.get('message', '')[:50]}...")
            
            logger.info(f"✅ Recovery completed: {len(recovered_task_ids)} tasks loaded into memory")
            return recovered_task_ids
            
        except Exception as e:
            logger.error(f"❌ Error recovering incomplete tasks: {str(e)}")
            return []
    
    def _generate_task_summary(self, task_data: Dict[str, Any]) -> str:
        """
        Generar resumen de tarea para historial
        
        Args:
            task_data: Datos de la tarea
            
        Returns:
            String con resumen de la tarea
        """
        try:
            message = task_data.get('message', 'Sin mensaje')[:50]
            status = task_data.get('status', 'unknown')
            steps_count = len(task_data.get('plan', []))
            task_type = task_data.get('task_type', 'general')
            
            summary = f"{message}... | {status.upper()} | {steps_count} pasos | {task_type}"
            
            if task_data.get('completed_at'):
                summary += f" | Completado: {task_data['completed_at'][:10]}"
            
            return summary
            
        except Exception:
            return "Resumen no disponible"
    
    def get_task_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de tareas
        
        Returns:
            Dict con estadísticas
        """
        try:
            db_stats = self.db_service.get_stats()
            
            # Estadísticas de caché
            cache_stats = {
                'cached_tasks': len(self.active_cache),
                'cache_memory_mb': sum(len(str(task)) for task in self.active_cache.values()) / (1024 * 1024)
            }
            
            return {
                'database_stats': db_stats,
                'cache_stats': cache_stats,
                'recovery_capable': self.db_service.is_connected()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting task stats: {str(e)}")
            return {'error': str(e)}

# Instancia global del task manager
_task_manager_instance = None

def get_task_manager() -> TaskManager:
    """Obtener instancia singleton del TaskManager"""
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
    return _task_manager_instance

def initialize_task_manager(db_service: DatabaseService = None) -> TaskManager:
    """Inicializar TaskManager con servicio de base de datos específico"""
    global _task_manager_instance
    _task_manager_instance = TaskManager(db_service)
    return _task_manager_instance