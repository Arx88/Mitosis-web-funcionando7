"""
Gestor de herramientas refactorizado - Usa ToolRegistry
Fase 4: Eliminada duplicación masiva de código y simplificada arquitectura
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

from .tool_registry import get_tool_registry, initialize_tool_registry
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class ToolManager:
    """
    Gestor de herramientas simplificado que usa ToolRegistry
    Eliminada duplicación de código y mejorada arquitectura
    """
    
    def __init__(self):
        self.registry = get_tool_registry()
        self._initialized = False
        
        # Configuración por defecto
        self.default_config = {
            'timeout': 30,
            'max_retries': 2,
            'working_directory': '/app'
        }
    
    def initialize(self) -> Dict[str, Any]:
        """Inicializar el gestor de herramientas"""
        if self._initialized:
            return {'status': 'already_initialized', 'tools_count': len(self.get_available_tools())}
        
        try:
            # Inicializar registry
            initialize_tool_registry()
            
            self._initialized = True
            available_tools = self.get_available_tools()
            
            logger.info(f"ToolManager initialized with {len(available_tools)} tools")
            
            return {
                'status': 'success',
                'tools_count': len(available_tools),
                'available_tools': available_tools
            }
            
        except Exception as e:
            logger.error(f"Error initializing ToolManager: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_available_tools(self) -> List[str]:
        """Obtener lista de herramientas disponibles"""
        return self.registry.get_available_tools()
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Obtener información detallada de una herramienta"""
        return self.registry.get_tool_info(tool_name)
    
    def get_all_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """Obtener información de todas las herramientas"""
        return self.registry.get_all_tools_info()
    
    def validate_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar llamada a herramienta sin ejecutarla
        Interfaz compatible con código existente
        """
        if not self._initialized:
            self.initialize()
        
        # Verificar que la herramienta existe
        if tool_name not in self.get_available_tools():
            return {
                'valid': False,
                'error': f'Tool "{tool_name}" not available',
                'available_tools': self.get_available_tools()
            }
        
        # Validar parámetros usando el registry
        return self.registry.validate_tool_parameters(tool_name, parameters)
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], 
                    config: Dict[str, Any] = None, task_id: str = None) -> Dict[str, Any]:
        """
        Ejecutar herramienta
        Interfaz compatible con código existente pero usando ToolRegistry
        """
        if not self._initialized:
            self.initialize()
        
        # Combinar configuración
        final_config = {**self.default_config}
        if config:
            final_config.update(config)
        
        # 🔧 FIX CRÍTICO: Agregar task_id al config para herramientas de navegación en tiempo real
        if task_id:
            final_config['task_id'] = task_id
        
        # Log de ejecución
        logger.info(f"Executing tool '{tool_name}' with parameters: {parameters}")
        if task_id:
            logger.info(f"Task ID for tool execution: {task_id}")
        
        # Ejecutar usando registry
        result = self.registry.execute_tool(tool_name, parameters, final_config)
        
        # Log resultado
        if result.get('success', False):
            logger.info(f"Tool '{tool_name}' executed successfully")
        else:
            logger.error(f"Tool '{tool_name}' failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def execute_tool_with_retry(self, tool_name: str, parameters: Dict[str, Any], 
                               config: Dict[str, Any] = None, max_retries: int = 2, task_id: str = None) -> Dict[str, Any]:
        """
        Ejecutar herramienta con reintentos automáticos
        Funcionalidad mejorada que mantiene compatibilidad
        """
        if not config:
            config = {}
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                result = self.execute_tool(tool_name, parameters, config, task_id)
                
                if result.get('success', False):
                    if attempt > 0:
                        logger.info(f"Tool '{tool_name}' succeeded on attempt {attempt + 1}")
                    return result
                else:
                    last_error = result.get('error', 'Unknown error')
                    if attempt < max_retries:
                        logger.warning(f"Tool '{tool_name}' failed on attempt {attempt + 1}, retrying...")
                    
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    logger.warning(f"Tool '{tool_name}' threw exception on attempt {attempt + 1}, retrying...")
        
        # Si llegamos aquí, todos los intentos fallaron
        logger.error(f"Tool '{tool_name}' failed after {max_retries + 1} attempts")
        return {
            'success': False,
            'error': f'Tool failed after {max_retries + 1} attempts. Last error: {last_error}',
            'tool_name': tool_name,
            'attempts': max_retries + 1
        }
    
    def execute_tool_chain(self, tool_calls: List[Dict[str, Any]], 
                          config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Ejecutar cadena de herramientas
        Funcionalidad nueva que aprovecha la arquitectura mejorada
        """
        if not config:
            config = {}
        
        results = []
        context = {}  # Contexto compartido entre herramientas
        
        for i, tool_call in enumerate(tool_calls):
            tool_name = tool_call.get('tool_name', '')
            parameters = tool_call.get('parameters', {})
            tool_config = {**config, **tool_call.get('config', {})}
            
            # Inyectar contexto de herramientas anteriores si se solicita
            if tool_call.get('use_context', False):
                parameters['_context'] = context
            
            try:
                result = self.execute_tool(tool_name, parameters, tool_config)
                
                # Agregar metadatos de la cadena
                result['chain_position'] = i
                result['tool_call'] = tool_call
                
                results.append(result)
                
                # Actualizar contexto si la herramienta fue exitosa
                if result.get('success', False):
                    context[f'tool_{i}_{tool_name}'] = result
                    
                    # Si la herramienta específica que debe exportar datos al contexto
                    if tool_call.get('export_to_context'):
                        context.update(tool_call['export_to_context'])
                else:
                    # Si una herramienta falla y es crítica, detener la cadena
                    if tool_call.get('critical', False):
                        logger.error(f"Critical tool '{tool_name}' failed, stopping chain")
                        break
                        
            except Exception as e:
                error_result = {
                    'success': False,
                    'error': f'Exception in tool chain: {str(e)}',
                    'tool_name': tool_name,
                    'chain_position': i,
                    'tool_call': tool_call
                }
                
                results.append(error_result)
                
                if tool_call.get('critical', False):
                    logger.error(f"Critical tool '{tool_name}' threw exception, stopping chain")
                    break
        
        return results
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso de herramientas"""
        stats = self.registry.get_registry_stats()
        
        # Agregar estadísticas del manager
        stats.update({
            'manager_initialized': self._initialized,
            'default_config': self.default_config
        })
        
        return stats
    
    def reload_tools(self) -> Dict[str, Any]:
        """Recargar todas las herramientas (útil para desarrollo)"""
        try:
            # Reinicializar registry
            self.registry._initialized = False
            self.registry._tool_instances.clear()
            
            initialize_tool_registry()
            
            available_tools = self.get_available_tools()
            
            logger.info(f"Tools reloaded: {len(available_tools)} available")
            
            return {
                'status': 'success',
                'tools_count': len(available_tools),
                'available_tools': available_tools
            }
            
        except Exception as e:
            logger.error(f"Error reloading tools: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def update_default_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar configuración por defecto"""
        old_config = self.default_config.copy()
        self.default_config.update(new_config)
        
        logger.info(f"Default config updated: {new_config}")
        
        return {
            'status': 'success',
            'old_config': old_config,
            'new_config': self.default_config
        }

# ========================================================================
# INSTANCIA GLOBAL PARA COMPATIBILIDAD
# ========================================================================

_global_tool_manager = None

def get_tool_manager() -> ToolManager:
    """Obtener instancia global del tool manager"""
    global _global_tool_manager
    if _global_tool_manager is None:
        _global_tool_manager = ToolManager()
        _global_tool_manager.initialize()
    return _global_tool_manager

# ========================================================================
# FUNCIONES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# ========================================================================

def initialize_tools() -> Dict[str, Any]:
    """Función de compatibilidad"""
    return get_tool_manager().initialize()

def get_available_tools() -> List[str]:
    """Función de compatibilidad"""
    return get_tool_manager().get_available_tools()

def execute_tool(tool_name: str, parameters: Dict[str, Any], 
                config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Función de compatibilidad"""
    return get_tool_manager().execute_tool(tool_name, parameters, config)

def validate_tool_call(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Función de compatibilidad"""
    return get_tool_manager().validate_tool_call(tool_name, parameters)