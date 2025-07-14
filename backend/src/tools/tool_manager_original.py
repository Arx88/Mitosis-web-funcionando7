"""
Gestor de herramientas del agente
Coordina la ejecución de diferentes herramientas disponibles
"""

import os
import json
from typing import Dict, List, Any, Optional
from .shell_tool import ShellTool
from .web_search_tool import WebSearchTool
from .file_manager_tool import FileManagerTool
from .tavily_search_tool import TavilySearchTool
from .deep_research_tool import DeepResearchTool
from .comprehensive_research_tool import ComprehensiveResearchTool
from .enhanced_deep_research_tool import EnhancedDeepResearchTool
from .enhanced_web_search_tool import EnhancedWebSearchTool

class ToolManager:
    def __init__(self):
        # Inicializar herramientas
        self.tools = {
            'shell': ShellTool(),
            'web_search': WebSearchTool(),
            'file_manager': FileManagerTool(),
            'tavily_search': TavilySearchTool(),
            'deep_research': DeepResearchTool(),
            'comprehensive_research': ComprehensiveResearchTool(),
            'enhanced_deep_research': EnhancedDeepResearchTool(),
            'enhanced_web_search': EnhancedWebSearchTool()
        }
        
        # Configuración de seguridad
        self.security_config = {
            'shell': {
                'enabled': True,
                'timeout': 30,
                'blocked_commands': [
                    'rm -rf /', 'mkfs', 'dd if=', 'format', 'del /s',
                    'shutdown', 'reboot', 'halt', 'poweroff'
                ]
            },
            'web_search': {
                'enabled': True,
                'max_results': 10,
                'timeout': 15
            },
            'file_manager': {
                'enabled': True,
                'allowed_paths': ['/tmp', '/var/tmp', '/app', '/home'],
                'blocked_paths': ['/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin']
            },
            'tavily_search': {
                'enabled': True,
                'max_results': 10,
                'timeout': 15
            },
            'deep_research': {
                'enabled': True,
                'max_sources': 15,
                'timeout': 30
            },
            'comprehensive_research': {
                'enabled': True,
                'max_sources': 15,
                'max_images': 20,
                'timeout': 45
            },
            'enhanced_deep_research': {
                'enabled': True,
                'max_sources': 20,
                'max_images': 15,
                'timeout': 60
            },
            'enhanced_web_search': {
                'enabled': True,
                'max_results': 15,
                'max_images': 10,
                'timeout': 30
            }
        }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Obtener lista de herramientas disponibles"""
        tools_list = []
        
        for name, tool in self.tools.items():
            if self.is_tool_enabled(name):
                tools_list.append({
                    'name': name,
                    'description': tool.get_description(),
                    'parameters': tool.get_parameters(),
                    'enabled': True
                })
        
        return tools_list
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """Verificar si una herramienta está habilitada"""
        return self.security_config.get(tool_name, {}).get('enabled', False)
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar una herramienta específica
        
        Args:
            tool_name: Nombre de la herramienta
            parameters: Parámetros para la herramienta
            
        Returns:
            Resultado de la ejecución
        """
        if tool_name not in self.tools:
            return {
                'error': f'Tool {tool_name} not found',
                'available_tools': list(self.tools.keys())
            }
        
        if not self.is_tool_enabled(tool_name):
            return {
                'error': f'Tool {tool_name} is disabled'
            }
        
        try:
            tool = self.tools[tool_name]
            config = self.security_config.get(tool_name, {})
            
            # Validar parámetros
            validation_result = tool.validate_parameters(parameters)
            if not validation_result['valid']:
                return {
                    'error': f'Invalid parameters: {validation_result["error"]}',
                    'expected_parameters': tool.get_parameters()
                }
            
            # Aplicar configuración de seguridad
            if tool_name == 'shell':
                if self._is_command_blocked(parameters.get('command', '')):
                    return {
                        'error': 'Command blocked for security reasons'
                    }
            
            elif tool_name == 'file_manager':
                if not self._is_path_allowed(parameters.get('path', '')):
                    return {
                        'error': 'Path not allowed for security reasons'
                    }
            
            # Ejecutar herramienta
            result = tool.execute(parameters, config)
            
            return {
                'success': True,
                'result': result,
                'tool': tool_name,
                'timestamp': __import__('time').time()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'tool': tool_name,
                'timestamp': __import__('time').time()
            }
    
    def _is_command_blocked(self, command: str) -> bool:
        """Verificar si un comando está bloqueado"""
        blocked_commands = self.security_config['shell']['blocked_commands']
        command_lower = command.lower().strip()
        
        for blocked in blocked_commands:
            if blocked.lower() in command_lower:
                return True
        
        return False
    
    def _is_path_allowed(self, path: str) -> bool:
        """Verificar si una ruta está permitida"""
        if not path:
            return False
        
        # Normalizar ruta
        normalized_path = os.path.normpath(path)
        
        # Verificar rutas bloqueadas
        blocked_paths = self.security_config['file_manager']['blocked_paths']
        for blocked in blocked_paths:
            if normalized_path.startswith(blocked):
                return False
        
        # Verificar rutas permitidas
        allowed_paths = self.security_config['file_manager']['allowed_paths']
        for allowed in allowed_paths:
            if normalized_path.startswith(allowed):
                return True
        
        return False
    
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """Obtener configuración de una herramienta"""
        return self.security_config.get(tool_name, {})
    
    def update_tool_config(self, tool_name: str, config: Dict[str, Any]) -> bool:
        """Actualizar configuración de una herramienta"""
        if tool_name in self.security_config:
            self.security_config[tool_name].update(config)
            return True
        return False