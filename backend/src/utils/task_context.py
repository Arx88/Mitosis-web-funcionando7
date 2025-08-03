"""
Task Context Holder - Sistema de Propagación de Contexto de Tareas
Implementa contexto thread-safe para aislamiento de tareas usando contextvars
Basado en las especificaciones del UpgradeAI.md - Sección 5.1.1
"""

import contextvars
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass, field
import time

logger = logging.getLogger(__name__)

@dataclass
class OrchestrationContext:
    """
    Contexto completo de orquestación de tareas
    Contiene toda la información necesaria para el aislamiento de tareas
    """
    task_id: str
    user_id: str
    session_id: str
    task_description: Optional[str] = None
    priority: int = 1
    timeout: Optional[float] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el contexto a diccionario para serialización"""
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "task_description": self.task_description,
            "priority": self.priority,
            "timeout": self.timeout,
            "constraints": self.constraints,
            "preferences": self.preferences,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrchestrationContext':
        """Crea un contexto desde un diccionario"""
        return cls(
            task_id=data.get("task_id", ""),
            user_id=data.get("user_id", ""),
            session_id=data.get("session_id", ""),
            task_description=data.get("task_description"),
            priority=data.get("priority", 1),
            timeout=data.get("timeout"),
            constraints=data.get("constraints", {}),
            preferences=data.get("preferences", {}),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", time.time())
        )

# Variable de contexto global para almacenar el contexto de tarea actual
current_task_context_var = contextvars.ContextVar(
    'current_task_context', 
    default=None
)

def set_current_task_context(context: OrchestrationContext) -> contextvars.Token:
    """
    Establece el contexto de tarea actual
    
    Args:
        context: El contexto de orquestación a establecer
        
    Returns:
        Token para restablecer el contexto posteriormente
    """
    if not isinstance(context, OrchestrationContext):
        raise TypeError("El contexto debe ser una instancia de OrchestrationContext")
        
    logger.debug(f"Estableciendo contexto para tarea: {context.task_id}")
    
    token = current_task_context_var.set(context)
    
    # Registrar establecimiento de contexto para debugging
    logger.debug(f"Contexto establecido - Task ID: {context.task_id}, "
                f"User ID: {context.user_id}, Session ID: {context.session_id}")
    
    return token

def get_current_task_context() -> Optional[OrchestrationContext]:
    """
    Obtiene el contexto de tarea actual
    
    Returns:
        El contexto actual o None si no hay contexto establecido
    """
    context = current_task_context_var.get()
    
    if context:
        logger.debug(f"Contexto obtenido - Task ID: {context.task_id}")
    else:
        logger.debug("No hay contexto de tarea establecido")
    
    return context

def reset_current_task_context(token: contextvars.Token):
    """
    Restablece el contexto de tarea usando el token proporcionado
    
    Args:
        token: Token obtenido de set_current_task_context
    """
    try:
        current_task_context_var.reset(token)
        logger.debug("Contexto de tarea restablecido")
    except Exception as e:
        logger.error(f"Error restableciendo contexto de tarea: {e}")

def get_current_task_id() -> Optional[str]:
    """
    Obtiene el task_id actual de forma conveniente
    
    Returns:
        El task_id actual o None si no hay contexto
    """
    context = get_current_task_context()
    return context.task_id if context else None

def get_current_user_id() -> Optional[str]:
    """
    Obtiene el user_id actual de forma conveniente
    
    Returns:
        El user_id actual o None si no hay contexto
    """
    context = get_current_task_context()
    return context.user_id if context else None

def get_current_session_id() -> Optional[str]:
    """
    Obtiene el session_id actual de forma conveniente
    
    Returns:
        El session_id actual o None si no hay contexto
    """
    context = get_current_task_context()
    return context.session_id if context else None

def require_task_context() -> OrchestrationContext:
    """
    Obtiene el contexto actual, lanzando excepción si no existe
    
    Returns:
        El contexto actual
        
    Raises:
        RuntimeError: Si no hay contexto establecido
    """
    context = get_current_task_context()
    if context is None:
        raise RuntimeError("Se requiere un contexto de tarea, pero no hay ninguno establecido")
    return context

def update_task_context(updates: Dict[str, Any]):
    """
    Actualiza el contexto de tarea actual con nuevos valores
    
    Args:
        updates: Diccionario con los valores a actualizar
    """
    context = get_current_task_context()
    if context is None:
        logger.warning("Intentando actualizar contexto pero no hay contexto establecido")
        return
        
    # Actualizar metadatos del contexto
    context.metadata.update(updates.get('metadata', {}))
    
    # Actualizar otros campos si se proporcionan
    if 'task_description' in updates:
        context.task_description = updates['task_description']
    if 'priority' in updates:
        context.priority = updates['priority']
    if 'constraints' in updates:
        context.constraints.update(updates['constraints'])
    if 'preferences' in updates:
        context.preferences.update(updates['preferences'])
        
    logger.debug(f"Contexto actualizado para tarea: {context.task_id}")

def create_context_decorator(func):
    """
    Decorator para funciones que necesitan acceso automático al contexto de tarea
    
    Usage:
        @create_context_decorator
        def my_function(task_context, other_args):
            # task_context será inyectado automáticamente
            pass
    """
    def wrapper(*args, **kwargs):
        context = get_current_task_context()
        if context is None:
            logger.warning(f"Función {func.__name__} llamada sin contexto de tarea")
            return func(None, *args, **kwargs)
        return func(context, *args, **kwargs)
    return wrapper

# Función de utilidad para logging con contexto automático
def log_with_context(level: int, message: str, extra_data: Optional[Dict[str, Any]] = None):
    """
    Función de logging que incluye automáticamente información del contexto de tarea
    
    Args:
        level: Nivel de logging (logging.INFO, etc.)
        message: Mensaje a loggear
        extra_data: Datos adicionales a incluir
    """
    context = get_current_task_context()
    
    if context:
        enhanced_message = f"[Task:{context.task_id}][User:{context.user_id}] {message}"
        extra = {
            'task_id': context.task_id,
            'user_id': context.user_id,
            'session_id': context.session_id,
            **(extra_data or {})
        }
    else:
        enhanced_message = f"[NoContext] {message}"
        extra = extra_data or {}
    
    logger.log(level, enhanced_message, extra=extra)

# Constantes para facilitar el uso
TASK_CONTEXT_NOT_SET = "N/A"

def get_context_info_dict() -> Dict[str, str]:
    """
    Obtiene información del contexto como diccionario para logging/debugging
    
    Returns:
        Diccionario con información del contexto o valores por defecto
    """
    context = get_current_task_context()
    
    if context:
        return {
            'task_id': context.task_id,
            'user_id': context.user_id,
            'session_id': context.session_id,
            'task_description': context.task_description or 'N/A',
            'priority': str(context.priority),
            'timestamp': str(context.timestamp)
        }
    else:
        return {
            'task_id': TASK_CONTEXT_NOT_SET,
            'user_id': TASK_CONTEXT_NOT_SET,
            'session_id': TASK_CONTEXT_NOT_SET,
            'task_description': TASK_CONTEXT_NOT_SET,
            'priority': TASK_CONTEXT_NOT_SET,
            'timestamp': TASK_CONTEXT_NOT_SET
        }