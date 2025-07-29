"""
Herramienta de shell refactorizada - Usa BaseTool
Eliminada duplicación de código de validación y error handling
"""

import subprocess
import os
import time
from typing import Dict, Any, List

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

@register_tool
class ShellTool(BaseTool):
    """
    Herramienta de shell que ejecuta comandos de terminal de forma segura
    Refactorizada para usar BaseTool y eliminar código duplicado
    """
    
    def __init__(self):
        super().__init__(
            name="shell",
            description="Ejecuta comandos de terminal de forma segura"
        )
    
    def _define_parameters(self) -> List[ParameterDefinition]:
        """Definir parámetros específicos del shell"""
        return [
            ParameterDefinition(
                name="command",
                param_type="string",
                required=True,
                description="Comando a ejecutar en el terminal",
                min_value=1  # No puede estar vacío
            ),
            ParameterDefinition(
                name="working_directory",
                param_type="string",
                required=False,
                description="Directorio de trabajo para ejecutar el comando",
                default="/app"
            ),
            ParameterDefinition(
                name="timeout",
                param_type="integer",
                required=False,
                description="Timeout en segundos para la ejecución",
                default=30,
                min_value=1,
                max_value=300
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        """Ejecutar comando de shell"""
        command = parameters['command'].strip()
        working_directory = parameters.get('working_directory', '/app')
        timeout = parameters.get('timeout', 30)
        
        # Validaciones de seguridad adicionales
        security_check = self._security_check(command)
        if not security_check['allowed']:
            return self._create_error_result(f"Security check failed: {security_check['reason']}")
        
        try:
            # Verificar directorio de trabajo
            if not os.path.exists(working_directory):
                return self._create_error_result(f"Working directory does not exist: {working_directory}")
            
            if not os.path.isdir(working_directory):
                return self._create_error_result(f"Working directory is not a directory: {working_directory}")
            
            # Ejecutar comando
            start_time = time.time()
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_directory
            )
            
            execution_time = time.time() - start_time
            
            # Preparar datos de resultado
            result_data = {
                'command': command,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'working_directory': working_directory,
                'command_execution_time': execution_time
            }
            
            # Determinar si fue exitoso
            if result.returncode == 0:
                return self._create_success_result(result_data)
            else:
                # Comando ejecutado pero con error
                result_data['error'] = f"Command failed with exit code {result.returncode}"
                return ToolExecutionResult(success=False, data=result_data, error=result_data['error'])
            
        except subprocess.TimeoutExpired:
            return self._create_error_result(f'Command timed out after {timeout} seconds')
        
        except FileNotFoundError:
            return self._create_error_result('Command not found or not executable')
        
        except PermissionError:
            return self._create_error_result('Permission denied to execute command')
        
        except Exception as e:
            return self._create_error_result(f'Unexpected error executing command: {str(e)}')
    
    def _security_check(self, command: str) -> Dict[str, Any]:
        """
        Verificaciones de seguridad para comandos
        Previene comandos potencialmente peligrosos
        """
        command_lower = command.lower().strip()
        
        # Lista de comandos/patrones prohibidos
        dangerous_patterns = [
            'rm -rf /',
            'rm -rf *',
            'format c:',
            'del /f /s /q',
            'shutdown',
            'reboot',
            'halt',
            'init 0',
            'init 6',
            'kill -9 1',
            'killall',
            'pkill -f',
            'chmod 777 /',
            'chown -R',
            'dd if=/dev/zero',
            'dd if=/dev/random',
            ':(){ :|:& };:',  # Fork bomb
            'wget http',
            'curl http',
            'nc -l',
            'netcat -l'
        ]
        
        # Verificar patrones peligrosos
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return {
                    'allowed': False,
                    'reason': f'Command contains dangerous pattern: {pattern}'
                }
        
        # Verificar comandos que requieren privilegios root
        root_commands = ['sudo', 'su -', 'passwd', 'useradd', 'userdel', 'usermod']
        for root_cmd in root_commands:
            if command_lower.startswith(root_cmd):
                return {
                    'allowed': False,
                    'reason': f'Command requires root privileges: {root_cmd}'
                }
        
        # Verificar longitud máxima del comando
        if len(command) > 1000:
            return {
                'allowed': False,
                'reason': 'Command too long (max 1000 characters)'
            }
        
        return {'allowed': True, 'reason': 'Command passed security checks'}
    
    # ========================================================================
    # MÉTODOS ADICIONALES ESPECÍFICOS DE SHELL (MANTENER COMPATIBILIDAD)
    # ========================================================================
    
    def get_working_directory(self) -> str:
        """Obtener directorio de trabajo actual"""
        return os.getcwd()
    
    def set_working_directory(self, path: str) -> bool:
        """Cambiar directorio de trabajo"""
        try:
            if os.path.exists(path) and os.path.isdir(path):
                os.chdir(path)
                return True
            return False
        except:
            return False
    
    def execute_safe(self, command: str, working_directory: str = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Método de conveniencia para mantener compatibilidad con código existente
        """
        parameters = {
            'command': command,
            'timeout': timeout
        }
        
        if working_directory:
            parameters['working_directory'] = working_directory
        
        return self.execute(parameters)