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

# Importar herramientas mejoradas
from .enhanced_web_search_tool_improved import EnhancedWebSearchTool
from .deep_research_tool_improved import DeepResearchTool

# Importar nuevas herramientas
from .firecrawl_tool import FirecrawlTool
from .qstash_tool import QStashTool
from .playwright_tool import PlaywrightTool

class ToolManager:
    def __init__(self):
        # Inicializar herramientas con versiones mejoradas
        self.tools = {
            'shell': ShellTool(),
            'web_search': EnhancedWebSearchTool(),  # Usar versión mejorada
            'file_manager': FileManagerTool(),
            'tavily_search': TavilySearchTool(),
            'deep_research': DeepResearchTool(),  # Usar versión mejorada
            'comprehensive_research': ComprehensiveResearchTool(),
            'enhanced_web_search': EnhancedWebSearchTool(),  # Alias para compatibilidad
            'enhanced_deep_research': DeepResearchTool()  # Alias para compatibilidad
        }
        
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
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar una herramienta específica con manejo mejorado de errores
        
        Args:
            tool_name: Nombre de la herramienta
            parameters: Parámetros para la herramienta
            
        Returns:
            Resultado de la ejecución
        """
        import time
        start_time = time.time()
        
        # Actualizar estadísticas
        if tool_name in self.usage_stats:
            self.usage_stats[tool_name]['calls'] += 1
        
        if tool_name not in self.tools:
            error_result = {
                'error': f'Tool {tool_name} not found',
                'available_tools': list(self.tools.keys()),
                'success': False
            }
            if tool_name in self.usage_stats:
                self.usage_stats[tool_name]['errors'] += 1
            return error_result
        
        if not self.is_tool_enabled(tool_name):
            error_result = {
                'error': f'Tool {tool_name} is disabled',
                'success': False
            }
            if tool_name in self.usage_stats:
                self.usage_stats[tool_name]['errors'] += 1
            return error_result
        
        try:
            tool = self.tools[tool_name]
            config = self.security_config.get(tool_name, {})
            
            # Validar parámetros si el método existe
            if hasattr(tool, 'validate_parameters'):
                validation_result = tool.validate_parameters(parameters)
                if not validation_result.get('valid', True):
                    error_result = {
                        'error': f'Invalid parameters: {validation_result.get("error", "Unknown validation error")}',
                        'expected_parameters': tool.get_parameters() if hasattr(tool, 'get_parameters') else [],
                        'success': False
                    }
                    self.usage_stats[tool_name]['errors'] += 1
                    return error_result
            
            # Aplicar configuración de seguridad
            security_check = self._apply_security_checks(tool_name, parameters)
            if not security_check['allowed']:
                error_result = {
                    'error': security_check['reason'],
                    'success': False
                }
                self.usage_stats[tool_name]['errors'] += 1
                return error_result
            
            # Ejecutar herramienta
            result = tool.execute(parameters, config)
            
            # Calcular tiempo de ejecución
            execution_time = time.time() - start_time
            self.usage_stats[tool_name]['total_time'] += execution_time
            
            # Formatear resultado
            if isinstance(result, dict) and 'success' in result:
                # La herramienta ya incluye el campo success
                final_result = result
            else:
                # Envolver resultado para consistencia
                final_result = {
                    'success': True,
                    'result': result
                }
            
            final_result.update({
                'tool': tool_name,
                'timestamp': time.time(),
                'execution_time': execution_time
            })
            
            return final_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.usage_stats[tool_name]['errors'] += 1
            self.usage_stats[tool_name]['total_time'] += execution_time
            
            return {
                'error': str(e),
                'tool': tool_name,
                'timestamp': time.time(),
                'execution_time': execution_time,
                'success': False
            }
    
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

