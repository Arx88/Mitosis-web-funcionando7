"""
Herramienta de shell - Ejecuta comandos de terminal
"""

import subprocess
import os
import time
from typing import Dict, Any, List

class ShellTool:
    def __init__(self):
        self.name = "shell"
        self.description = "Ejecuta comandos de terminal de forma segura"
        self.parameters = [
            {
                "name": "command",
                "type": "string",
                "required": True,
                "description": "Comando a ejecutar en el terminal"
            }
        ]
    
    def get_description(self) -> str:
        return self.description
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        return self.parameters
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros de entrada"""
        if not isinstance(parameters, dict):
            return {'valid': False, 'error': 'Parameters must be a dictionary'}
        
        if 'command' not in parameters:
            return {'valid': False, 'error': 'command parameter is required'}
        
        if not isinstance(parameters['command'], str):
            return {'valid': False, 'error': 'command must be a string'}
        
        if not parameters['command'].strip():
            return {'valid': False, 'error': 'command cannot be empty'}
        
        return {'valid': True}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar comando de shell"""
        if config is None:
            config = {}
        
        command = parameters['command'].strip()
        timeout = config.get('timeout', 30)
        
        try:
            # Ejecutar comando
            start_time = time.time()
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=config.get('working_directory', '/tmp')
            )
            
            execution_time = time.time() - start_time
            
            return {
                'command': command,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': execution_time,
                'success': result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                'command': command,
                'error': f'Command timed out after {timeout} seconds',
                'success': False
            }
        
        except Exception as e:
            return {
                'command': command,
                'error': str(e),
                'success': False
            }
    
    def get_working_directory(self) -> str:
        """Obtener directorio de trabajo actual"""
        return os.getcwd()
    
    def set_working_directory(self, path: str) -> bool:
        """Cambiar directorio de trabajo"""
        try:
            os.chdir(path)
            return True
        except:
            return False