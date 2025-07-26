"""
Tool Registry - Sistema de auto-discovery y lazy loading para herramientas
Fase 4: Abstracción de Herramientas - Elimina duplicación en tool_manager.py
"""

import os
import importlib
import inspect
from typing import Dict, Any, List, Optional, Type
import logging
from pathlib import Path

from .base_tool import BaseTool, get_registered_tools

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Registro centralizado de herramientas con auto-discovery y lazy loading
    Elimina la necesidad de registrar manualmente cada herramienta
    """
    
    def __init__(self, tools_directory: str = None):
        self.tools_directory = tools_directory or os.path.dirname(__file__)
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._tool_instances: Dict[str, BaseTool] = {}
        self._initialized = False
        
    def initialize(self) -> None:
        """Inicializar el registro descubriendo todas las herramientas"""
        if self._initialized:
            return
            
        logger.info("Inicializando Tool Registry...")
        
        # Auto-descubrir herramientas
        self._discover_tools()
        
        # Registrar herramientas que usan el decorador
        decorator_tools = get_registered_tools()
        self._tool_classes.update(decorator_tools)
        
        self._initialized = True
        logger.info(f"Tool Registry inicializado con {len(self._tool_classes)} herramientas")
    
    def _discover_tools(self) -> None:
        """Descubrir automáticamente todas las herramientas en el directorio"""
        tools_path = Path(self.tools_directory)
        
        for python_file in tools_path.glob("*_tool.py"):
            if python_file.name.startswith('_'):
                continue
                
            try:
                # Importar módulo
                module_name = python_file.stem
                spec = importlib.util.spec_from_file_location(module_name, python_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Buscar clases que hereden de BaseTool
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (obj != BaseTool and 
                            issubclass(obj, BaseTool) and 
                            not inspect.isabstract(obj)):
                            
                            # Crear instancia temporal para obtener el nombre
                            try:
                                temp_instance = obj()
                                tool_name = temp_instance.get_name()
                                self._tool_classes[tool_name] = obj
                                logger.debug(f"Discovered tool: {tool_name} from {python_file.name}")
                            except Exception as e:
                                logger.warning(f"Could not instantiate tool {name} from {python_file.name}: {e}")
                                
            except Exception as e:
                logger.warning(f"Could not import tool from {python_file.name}: {e}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Obtener instancia de herramienta (lazy loading)
        """
        if not self._initialized:
            self.initialize()
        
        # Si ya está instanciada, devolverla
        if tool_name in self._tool_instances:
            return self._tool_instances[tool_name]
        
        # Si la clase está registrada, instanciarla
        if tool_name in self._tool_classes:
            try:
                tool_class = self._tool_classes[tool_name]
                tool_instance = tool_class()
                self._tool_instances[tool_name] = tool_instance
                logger.debug(f"Lazy loaded tool: {tool_name}")
                return tool_instance
            except Exception as e:
                logger.error(f"Error instantiating tool {tool_name}: {e}")
                return None
        
        logger.warning(f"Tool not found: {tool_name}")
        return None
    
    def get_available_tools(self) -> List[str]:
        """Obtener lista de nombres de herramientas disponibles"""
        if not self._initialized:
            self.initialize()
        
        return list(self._tool_classes.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Obtener información de una herramienta sin instanciarla"""
        if not self._initialized:
            self.initialize()
        
        if tool_name not in self._tool_classes:
            return None
        
        # Si ya está instanciada, usar la instancia
        if tool_name in self._tool_instances:
            tool = self._tool_instances[tool_name]
            return {
                'name': tool.get_name(),
                'description': tool.get_description(),
                'parameters': tool.get_parameters()
            }
        
        # Si no, crear instancia temporal
        try:
            tool_class = self._tool_classes[tool_name]
            temp_tool = tool_class()
            return {
                'name': temp_tool.get_name(),
                'description': temp_tool.get_description(),
                'parameters': temp_tool.get_parameters()
            }
        except Exception as e:
            logger.error(f"Error getting info for tool {tool_name}: {e}")
            return None
    
    def get_all_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """Obtener información de todas las herramientas disponibles"""
        if not self._initialized:
            self.initialize()
        
        tools_info = {}
        for tool_name in self._tool_classes:
            info = self.get_tool_info(tool_name)
            if info:
                tools_info[tool_name] = info
        
        return tools_info
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], 
                    config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecutar herramienta por nombre
        Interfaz simplificada para el tool_manager
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                'success': False,
                'error': f'Tool "{tool_name}" not found',
                'tool_name': tool_name,
                'available_tools': self.get_available_tools()
            }
        
        return tool.execute(parameters, config)
    
    def validate_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros de una herramienta sin ejecutarla"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                'valid': False,
                'error': f'Tool "{tool_name}" not found'
            }
        
        return tool.validate_parameters(parameters)
    
    def register_tool_class(self, tool_class: Type[BaseTool]) -> bool:
        """Registrar manualmente una clase de herramienta"""
        try:
            if not issubclass(tool_class, BaseTool):
                logger.error(f"Class {tool_class.__name__} does not inherit from BaseTool")
                return False
            
            temp_instance = tool_class()
            tool_name = temp_instance.get_name()
            self._tool_classes[tool_name] = tool_class
            
            # Si ya había una instancia, eliminarla para forzar recreación
            if tool_name in self._tool_instances:
                del self._tool_instances[tool_name]
            
            logger.info(f"Manually registered tool: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering tool class {tool_class.__name__}: {e}")
            return False
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Desregistrar una herramienta"""
        success = False
        
        if tool_name in self._tool_classes:
            del self._tool_classes[tool_name]
            success = True
        
        if tool_name in self._tool_instances:
            del self._tool_instances[tool_name]
            success = True
        
        if success:
            logger.info(f"Unregistered tool: {tool_name}")
        
        return success
    
    def reload_tool(self, tool_name: str) -> bool:
        """Recargar una herramienta (útil para desarrollo)"""
        if tool_name not in self._tool_classes:
            logger.warning(f"Cannot reload unknown tool: {tool_name}")
            return False
        
        # Eliminar instancia existente
        if tool_name in self._tool_instances:
            del self._tool_instances[tool_name]
        
        logger.info(f"Reloaded tool: {tool_name}")
        return True
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del registro"""
        return {
            'total_registered_classes': len(self._tool_classes),
            'total_instantiated_tools': len(self._tool_instances),
            'available_tools': list(self._tool_classes.keys()),
            'instantiated_tools': list(self._tool_instances.keys()),
            'initialized': self._initialized
        }

# ========================================================================
# INSTANCIA GLOBAL DEL REGISTRY
# ========================================================================

# Crear instancia global del registry
_global_registry = None

def get_tool_registry() -> ToolRegistry:
    """Obtener la instancia global del tool registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry

def initialize_tool_registry() -> None:
    """Inicializar el registry global"""
    registry = get_tool_registry()
    registry.initialize()

# ========================================================================
# FUNCIONES DE CONVENIENCIA
# ========================================================================

def get_tool(tool_name: str) -> Optional[BaseTool]:
    """Función de conveniencia para obtener una herramienta"""
    return get_tool_registry().get_tool(tool_name)

def execute_tool(tool_name: str, parameters: Dict[str, Any], 
                config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Función de conveniencia para ejecutar una herramienta"""
    return get_tool_registry().execute_tool(tool_name, parameters, config)

def get_available_tools() -> List[str]:
    """Función de conveniencia para obtener herramientas disponibles"""
    return get_tool_registry().get_available_tools()

def get_all_tools_info() -> Dict[str, Dict[str, Any]]:
    """Función de conveniencia para obtener info de todas las herramientas"""
    return get_tool_registry().get_all_tools_info()