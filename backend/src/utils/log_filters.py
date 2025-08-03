"""
Log Filters - Filtros de Logging con Contexto de Tarea
Implementa filtros para enriquecer logs con información de contexto
Basado en las especificaciones del UpgradeAI.md - Sección 5.1.2
"""

import logging
import time
from typing import Any, Dict, Optional
from .task_context import get_current_task_context, TASK_CONTEXT_NOT_SET

class TaskContextFilter(logging.Filter):
    """
    Filtro de logging que inyecta información del contexto de tarea
    en cada registro de log para facilitar el aislamiento y debugging
    """
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.default_values = {
            'task_id': TASK_CONTEXT_NOT_SET,
            'user_id': TASK_CONTEXT_NOT_SET,
            'session_id': TASK_CONTEXT_NOT_SET,
            'task_description': TASK_CONTEXT_NOT_SET
        }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Procesa cada registro de log añadiendo información del contexto de tarea
        
        Args:
            record: Registro de logging a procesar
            
        Returns:
            True para permitir que el log continúe procesándose
        """
        try:
            # Obtener contexto actual
            context = get_current_task_context()
            
            if context:
                # Inyectar información del contexto en el registro
                record.task_id = context.task_id
                record.user_id = context.user_id
                record.session_id = context.session_id
                record.task_description = context.task_description or TASK_CONTEXT_NOT_SET
                record.task_priority = str(context.priority)
                record.task_timestamp = str(context.timestamp)
                
                # Agregar metadatos adicionales si existen
                if hasattr(context, 'metadata') and context.metadata:
                    record.task_metadata = str(context.metadata)
                else:
                    record.task_metadata = TASK_CONTEXT_NOT_SET
                    
                # Indicar que hay contexto disponible
                record.has_task_context = True
                
            else:
                # No hay contexto, usar valores por defecto
                record.task_id = self.default_values['task_id']
                record.user_id = self.default_values['user_id']
                record.session_id = self.default_values['session_id']
                record.task_description = self.default_values['task_description']
                record.task_priority = TASK_CONTEXT_NOT_SET
                record.task_timestamp = TASK_CONTEXT_NOT_SET
                record.task_metadata = TASK_CONTEXT_NOT_SET
                record.has_task_context = False
                
            # Agregar timestamp formateado para debugging
            record.filter_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            return True
            
        except Exception as e:
            # Si hay error en el filtro, no bloquear el logging
            record.task_id = f"ERROR:{str(e)[:20]}"
            record.user_id = TASK_CONTEXT_NOT_SET
            record.session_id = TASK_CONTEXT_NOT_SET
            record.task_description = TASK_CONTEXT_NOT_SET
            record.task_priority = TASK_CONTEXT_NOT_SET
            record.task_timestamp = TASK_CONTEXT_NOT_SET
            record.task_metadata = TASK_CONTEXT_NOT_SET
            record.has_task_context = False
            record.filter_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            return True

class DetailedTaskContextFilter(TaskContextFilter):
    """
    Versión extendida del filtro que incluye información adicional de debugging
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Aplicar filtro base
        result = super().filter(record)
        
        try:
            context = get_current_task_context()
            
            if context:
                # Agregar información adicional para debugging avanzado
                record.task_elapsed_time = time.time() - context.timestamp
                record.task_constraints_count = len(context.constraints) if context.constraints else 0
                record.task_preferences_count = len(context.preferences) if context.preferences else 0
                record.task_metadata_count = len(context.metadata) if context.metadata else 0
                
                # Información del timeout si existe
                if context.timeout:
                    record.task_timeout = context.timeout
                    record.task_time_remaining = context.timeout - (time.time() - context.timestamp)
                else:
                    record.task_timeout = TASK_CONTEXT_NOT_SET
                    record.task_time_remaining = TASK_CONTEXT_NOT_SET
            else:
                # Valores por defecto para información extendida
                record.task_elapsed_time = 0
                record.task_constraints_count = 0
                record.task_preferences_count = 0
                record.task_metadata_count = 0
                record.task_timeout = TASK_CONTEXT_NOT_SET
                record.task_time_remaining = TASK_CONTEXT_NOT_SET
                
        except Exception:
            # Si hay error, establecer valores seguros
            record.task_elapsed_time = 0
            record.task_constraints_count = 0
            record.task_preferences_count = 0
            record.task_metadata_count = 0
            record.task_timeout = TASK_CONTEXT_NOT_SET
            record.task_time_remaining = TASK_CONTEXT_NOT_SET
            
        return result

class TaskIsolationFormatter(logging.Formatter):
    """
    Formateador personalizado que incluye información del contexto de tarea
    en el formato del mensaje de log
    """
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, 
                 include_context: bool = True, compact_format: bool = False):
        """
        Args:
            fmt: Formato del mensaje (si None, usa formato por defecto)
            datefmt: Formato de fecha
            include_context: Si incluir información del contexto en el mensaje
            compact_format: Si usar formato compacto para el contexto
        """
        
        if fmt is None:
            if compact_format:
                # Formato compacto: [Task:ID] Mensaje
                fmt = '[%(filter_timestamp)s][%(levelname)s][Task:%(task_id)s] %(message)s'
            else:
                # Formato detallado
                fmt = ('[%(filter_timestamp)s][%(levelname)s]'
                       '[Task:%(task_id)s][User:%(user_id)s][Session:%(session_id)s] '
                       '%(message)s')
        
        super().__init__(fmt, datefmt)
        self.include_context = include_context
        self.compact_format = compact_format
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro de log incluyendo información del contexto
        """
        # Asegurar que los atributos existen
        if not hasattr(record, 'task_id'):
            record.task_id = TASK_CONTEXT_NOT_SET
        if not hasattr(record, 'user_id'):
            record.user_id = TASK_CONTEXT_NOT_SET
        if not hasattr(record, 'session_id'):
            record.session_id = TASK_CONTEXT_NOT_SET
        if not hasattr(record, 'filter_timestamp'):
            record.filter_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
        # Formatear usando el formato base
        formatted = super().format(record)
        
        # Agregar información adicional si se solicita y hay contexto
        if (self.include_context and 
            hasattr(record, 'has_task_context') and 
            record.has_task_context and 
            not self.compact_format):
            
            additional_info = []
            
            if hasattr(record, 'task_description') and record.task_description != TASK_CONTEXT_NOT_SET:
                additional_info.append(f"Desc: {record.task_description[:50]}")
            
            if hasattr(record, 'task_priority'):
                additional_info.append(f"Priority: {record.task_priority}")
                
            if hasattr(record, 'task_elapsed_time') and record.task_elapsed_time > 0:
                additional_info.append(f"Elapsed: {record.task_elapsed_time:.2f}s")
            
            if additional_info:
                formatted += f" | {' | '.join(additional_info)}"
                
        return formatted

def setup_task_context_logging(logger_instance: logging.Logger, 
                             use_detailed_filter: bool = False,
                             use_custom_formatter: bool = True,
                             compact_format: bool = True) -> logging.Logger:
    """
    Configura un logger para usar los filtros y formateadores de contexto de tarea
    
    Args:
        logger_instance: Instancia de logger a configurar
        use_detailed_filter: Si usar el filtro detallado
        use_custom_formatter: Si usar el formateador personalizado
        compact_format: Si usar formato compacto
        
    Returns:
        Logger configurado
    """
    # Agregar filtro apropiado
    if use_detailed_filter:
        filter_instance = DetailedTaskContextFilter()
    else:
        filter_instance = TaskContextFilter()
    
    # Aplicar filtro a todos los handlers
    for handler in logger_instance.handlers:
        handler.addFilter(filter_instance)
        
        # Configurar formateador personalizado si se solicita
        if use_custom_formatter:
            formatter = TaskIsolationFormatter(compact_format=compact_format)
            handler.setFormatter(formatter)
    
    # Si no hay handlers, crear uno básico
    if not logger_instance.handlers:
        handler = logging.StreamHandler()
        handler.addFilter(filter_instance)
        
        if use_custom_formatter:
            formatter = TaskIsolationFormatter(compact_format=compact_format)
            handler.setFormatter(formatter)
            
        logger_instance.addHandler(handler)
    
    return logger_instance

# Función de conveniencia para configurar logging global
def configure_global_task_logging(level: int = logging.INFO, 
                                compact_format: bool = True) -> None:
    """
    Configura el logging global para incluir contexto de tarea
    
    Args:
        level: Nivel de logging mínimo
        compact_format: Si usar formato compacto
    """
    # Obtener logger root
    root_logger = logging.getLogger()
    
    # Configurar filtros y formateadores
    setup_task_context_logging(
        root_logger,
        use_detailed_filter=False,
        use_custom_formatter=True,
        compact_format=compact_format
    )
    
    # Establecer nivel
    root_logger.setLevel(level)
    
    logging.info("Sistema de logging con contexto de tarea configurado")