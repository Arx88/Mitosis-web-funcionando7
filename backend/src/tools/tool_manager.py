"""
Gestor de herramientas del agente - Versión mejorada
Coordina la ejecución de diferentes herramientas disponibles con mejoras integradas
"""

import os
import json
from typing import Dict, List, Any, Optional
from .shell_tool import ShellTool
from .file_manager_tool import FileManagerTool
from .tavily_search_tool import TavilySearchTool
from .comprehensive_research_tool import ComprehensiveResearchTool
from .web_search_tool import WebSearchTool  # Importar herramienta real

# Importar herramientas mejoradas
from .enhanced_web_search_tool_improved import EnhancedWebSearchTool
from .deep_research_tool_improved import DeepResearchTool

# Importar nuevas herramientas
from .firecrawl_tool import FirecrawlTool
from .qstash_tool import QStashTool
from .playwright_tool import PlaywrightTool
from .container_manager import ContainerManager
from .autonomous_web_navigation import AutonomousWebNavigation

class ToolManager:
    def __init__(self):
        # Inicializar herramientas con versiones REALES (no simuladas)
        self.tools = {
            'shell': ShellTool(),
            'web_search': WebSearchTool(),  # USAR HERRAMIENTA REAL
            'file_manager': FileManagerTool(),
            'tavily_search': TavilySearchTool(),
            'deep_research': DeepResearchTool(),  # Usar versión mejorada
            'comprehensive_research': ComprehensiveResearchTool(),
            'enhanced_web_search': WebSearchTool(),  # Usar herramienta real para compatibilidad
            'enhanced_deep_research': DeepResearchTool(),  # Alias para compatibilidad
            # Nuevas herramientas
            'firecrawl': FirecrawlTool(),
            'qstash': QStashTool(),
            'playwright': PlaywrightTool(),
            'autonomous_web_navigation': AutonomousWebNavigation()  # Navegación web autónoma GENERAL
        }
        
        # Inicializar container manager
        self.container_manager = ContainerManager()
        
        # Configuración de seguridad mejorada
        self.security_config = {
            'shell': {
                'enabled': True,
                'timeout': 30,
                'blocked_commands': [
                    'rm -rf /', 'mkfs', 'dd if=', 'format', 'del /s',
                    'shutdown', 'reboot', 'halt', 'poweroff', 'sudo rm',
                    'chmod 777', 'chown root', 'passwd', 'su -'
                ]
            },
            'web_search': {
                'enabled': True,
                'max_results': 10,
                'timeout': 15,
                'max_content_length': 8000,
                'retry_attempts': 3
            },
            'file_manager': {
                'enabled': True,
                'allowed_paths': ['/tmp', '/var/tmp', '/app', '/home', '/workspace'],
                'blocked_paths': ['/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/root'],
                'max_file_size': 100 * 1024 * 1024  # 100MB
            },
            'tavily_search': {
                'enabled': True,
                'max_results': 10,
                'timeout': 15
            },
            'deep_research': {
                'enabled': True,
                'max_sources': 15,
                'timeout': 30,
                'confidence_threshold': 0.7
            },
            'comprehensive_research': {
                'enabled': True,
                'max_sources': 15,
                'max_images': 20,
                'timeout': 45
            },
            'enhanced_web_search': {
                'enabled': True,
                'max_results': 15,
                'max_images': 10,
                'timeout': 30,
                'max_content_length': 8000
            },
            'enhanced_deep_research': {
                'enabled': True,
                'max_sources': 20,
                'max_images': 15,
                'timeout': 60,
                'confidence_threshold': 0.75
            },
            # Nuevas herramientas
            'firecrawl': {
                'enabled': True,
                'timeout': 30,
                'max_pages': 10,
                'include_images': True,
                'include_links': True
            },
            'qstash': {
                'enabled': True,
                'max_jobs': 100,
                'default_timeout': 300,
                'max_priority_jobs': 10
            },
            'playwright': {
                'enabled': True,
                'headless': True,
                'timeout': 30000,
                'viewport_width': 1920,
                'viewport_height': 1080
            },
            'autonomous_web_navigation': {
                'enabled': True,
                'headless': False,  # Navegación visible
                'timeout': 60000,
                'slow_motion': 1000,
                'visual_mode': True
            }
        }
        
        # Estadísticas de uso
        self.usage_stats = {
            tool_name: {'calls': 0, 'errors': 0, 'total_time': 0}
            for tool_name in self.tools.keys()
        }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Obtener lista de herramientas disponibles con información detallada"""
        tools_list = []
        
        for name, tool in self.tools.items():
            if self.is_tool_enabled(name):
                tool_info = {
                    'name': name,
                    'description': tool.get_description(),
                    'parameters': tool.get_parameters(),
                    'enabled': True,
                    'usage_stats': self.usage_stats.get(name, {}),
                    'config': self.security_config.get(name, {})
                }
                
                # Añadir información adicional si está disponible
                if hasattr(tool, 'get_tool_info'):
                    additional_info = tool.get_tool_info()
                    tool_info.update(additional_info)
                
                tools_list.append(tool_info)
        
        return tools_list
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """Verificar si una herramienta está habilitada"""
        return self.security_config.get(tool_name, {}).get('enabled', False)
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], 
                    config: Dict[str, Any] = None, task_id: str = None) -> Dict[str, Any]:
        """Ejecutar una herramienta con configuración y estadísticas mejoradas"""
        import time
        
        if config is None:
            config = {}
        
        # Verificar si la herramienta existe
        if tool_name not in self.tools:
            return {
                'error': f'Tool {tool_name} not found',
                'available_tools': list(self.tools.keys())
            }
        
        # Verificar si la herramienta está habilitada
        if not self.is_tool_enabled(tool_name):
            return {
                'error': f'Tool {tool_name} is disabled',
                'enabled': False
            }
        
        # Obtener herramienta
        tool = self.tools[tool_name]
        
        # Validar parámetros
        if hasattr(tool, 'validate_parameters'):
            validation = tool.validate_parameters(parameters)
            if not validation.get('valid', True):
                return {
                    'error': validation.get('error', 'Invalid parameters'),
                    'validation': validation
                }
        
        # Verificar restricciones de seguridad
        if not self._check_security_constraints(tool_name, parameters):
            return {
                'error': f'Security constraints violated for tool {tool_name}',
                'parameters': parameters
            }
        
        # Registrar inicio de ejecución
        start_time = time.time()
        self.usage_stats[tool_name]['calls'] += 1
        
        try:
            # Verificar si debemos ejecutar en container
            if task_id and self._should_execute_in_container(tool_name):
                result = self._execute_in_container(tool_name, parameters, config, task_id)
            else:
                # Ejecutar normalmente
                result = tool.execute(parameters, config)
            
            # Registrar tiempo de ejecución
            execution_time = time.time() - start_time
            self.usage_stats[tool_name]['total_time'] += execution_time
            
            # Agregar metadata
            if isinstance(result, dict):
                result['execution_time'] = execution_time
                result['tool_name'] = tool_name
                result['timestamp'] = time.time()
            
            return result
            
        except Exception as e:
            # Registrar error
            self.usage_stats[tool_name]['errors'] += 1
            execution_time = time.time() - start_time
            self.usage_stats[tool_name]['total_time'] += execution_time
            
            return {
                'error': str(e),
                'tool_name': tool_name,
                'execution_time': execution_time,
                'timestamp': time.time()
            }
    
    def _should_execute_in_container(self, tool_name: str) -> bool:
        """Determinar si una herramienta debe ejecutarse en container"""
        # Herramientas que se benefician de aislamiento
        containerized_tools = ['shell', 'file_manager']
        return tool_name in containerized_tools
    
    def _execute_in_container(self, tool_name: str, parameters: Dict[str, Any], 
                             config: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Ejecutar herramienta dentro de un container"""
        try:
            # Obtener información del container
            container_info = self.container_manager.get_container_info(task_id)
            
            if 'error' in container_info:
                # Fallback a ejecución normal
                return self.tools[tool_name].execute(parameters, config)
            
            # Para shell tool, ejecutar comando en container
            if tool_name == 'shell':
                command = parameters.get('command', '')
                timeout = config.get('timeout', 30)
                return self.container_manager.execute_command(task_id, command, timeout)
            
            # Para file manager, ajustar paths al workspace del container
            elif tool_name == 'file_manager':
                workspace_path = container_info.get('workspace_path', '')
                if workspace_path:
                    # Ajustar path relative al workspace del container
                    if 'path' in parameters:
                        rel_path = parameters['path']
                        if not rel_path.startswith('/'):
                            parameters['path'] = os.path.join(workspace_path, rel_path)
                
                return self.tools[tool_name].execute(parameters, config)
            
            else:
                # Para otras herramientas, ejecutar normalmente
                return self.tools[tool_name].execute(parameters, config)
        
        except Exception as e:
            # Fallback a ejecución normal en caso de error
            return self.tools[tool_name].execute(parameters, config)
    
    def _check_security_constraints(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Verificar restricciones de seguridad para una herramienta"""
        
        if tool_name == 'shell':
            command = parameters.get('command', '')
            blocked_commands = self.security_config['shell']['blocked_commands']
            
            # Verificar comandos bloqueados
            for blocked in blocked_commands:
                if blocked in command:
                    return False
            
            return True
        
        elif tool_name == 'file_manager':
            path = parameters.get('path', '')
            return self._is_path_allowed(path)
        
        # Para otras herramientas, permitir por defecto
        return True

    def _apply_security_checks(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Aplicar verificaciones de seguridad específicas por herramienta"""
        
        if tool_name == 'shell':
            command = parameters.get('command', '')
            if self._is_command_blocked(command):
                return {
                    'allowed': False,
                    'reason': 'Command blocked for security reasons'
                }
        
        elif tool_name == 'file_manager':
            path = parameters.get('path', '')
            if not self._is_path_allowed(path):
                return {
                    'allowed': False,
                    'reason': 'Path not allowed for security reasons'
                }
            
            # Verificar tamaño de archivo para operaciones de escritura
            if parameters.get('action') in ['write', 'create']:
                content = parameters.get('content', '')
                if len(content.encode('utf-8')) > self.security_config['file_manager']['max_file_size']:
                    return {
                        'allowed': False,
                        'reason': 'File size exceeds maximum allowed limit'
                    }
        
        elif tool_name in ['web_search', 'enhanced_web_search']:
            query = parameters.get('query', '')
            if len(query) > 500:  # Limitar longitud de consulta
                return {
                    'allowed': False,
                    'reason': 'Query too long'
                }
        
        return {'allowed': True}
    
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
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso de herramientas"""
        return {
            'tools': self.usage_stats,
            'total_calls': sum(stats['calls'] for stats in self.usage_stats.values()),
            'total_errors': sum(stats['errors'] for stats in self.usage_stats.values()),
            'total_time': sum(stats['total_time'] for stats in self.usage_stats.values())
        }
    
    def reset_usage_stats(self) -> None:
        """Reiniciar estadísticas de uso"""
        for tool_name in self.usage_stats:
            self.usage_stats[tool_name] = {'calls': 0, 'errors': 0, 'total_time': 0}
    
    def get_tool_health(self) -> Dict[str, Any]:
        """Obtener estado de salud de las herramientas"""
        health_status = {}
        
        for tool_name, tool in self.tools.items():
            stats = self.usage_stats[tool_name]
            error_rate = stats['errors'] / max(stats['calls'], 1)
            avg_time = stats['total_time'] / max(stats['calls'], 1)
            
            health_status[tool_name] = {
                'enabled': self.is_tool_enabled(tool_name),
                'error_rate': round(error_rate, 3),
                'avg_execution_time': round(avg_time, 3),
                'total_calls': stats['calls'],
                'status': 'healthy' if error_rate < 0.1 else 'warning' if error_rate < 0.3 else 'critical'
            }
        
        return health_status

