"""
Container Manager - Gestiona contenedores aislados para cada tarea
"""

import os
import subprocess
import time
import json
import tempfile
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import uuid

class ContainerManager:
    def __init__(self):
        self.name = "container_manager"
        self.description = "Gestiona contenedores Docker aislados para ejecución de tareas"
        self.containers = {}  # Almacenar información de contenedores activos
        self.base_images = {
            'general': 'python:3.9-slim',
            'web-development': 'node:18-alpine',
            'data-processing': 'jupyter/scipy-notebook:latest',
            'system-administration': 'ubuntu:22.04'
        }
        
        # Verificar si Docker está disponible
        self.docker_available = self._check_docker_availability()
        
    def _check_docker_availability(self) -> bool:
        """Verificar si Docker está disponible en el sistema"""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def create_container(self, task_id: str, task_type: str = 'general', 
                        custom_requirements: List[str] = None) -> Dict[str, Any]:
        """Crear un contenedor aislado para una tarea específica"""
        
        if not self.docker_available:
            # Fallback: crear directorio aislado simulado
            return self._create_simulated_container(task_id, task_type)
        
        try:
            # Seleccionar imagen base según el tipo de tarea
            base_image = self.base_images.get(task_type, self.base_images['general'])
            
            # Crear directorio de trabajo para la tarea
            workspace_path = Path(tempfile.gettempdir()) / 'agent_containers' / task_id
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Crear Dockerfile personalizado
            dockerfile_content = self._generate_dockerfile(task_type, base_image, custom_requirements)
            dockerfile_path = workspace_path / 'Dockerfile'
            dockerfile_path.write_text(dockerfile_content)
            
            # Crear imagen personalizada
            image_name = f"agent-task-{task_id}"
            build_result = subprocess.run(
                ['docker', 'build', '-t', image_name, '.'],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if build_result.returncode != 0:
                raise Exception(f"Failed to build Docker image: {build_result.stderr}")
            
            # Crear y iniciar contenedor
            container_name = f"agent-container-{task_id}"
            
            # Comando para crear contenedor
            docker_cmd = [
                'docker', 'run', '-d',
                '--name', container_name,
                '--rm',  # Auto-remove cuando se detenga
                '-v', f"{workspace_path}:/workspace",
                '-w', '/workspace',
                '--memory', '1g',  # Límite de memoria
                '--cpus', '1.0',   # Límite de CPU
                '--network', 'none',  # Sin acceso a red por defecto (seguridad)
                image_name,
                'sleep', 'infinity'  # Mantener contenedor activo
            ]
            
            create_result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if create_result.returncode != 0:
                raise Exception(f"Failed to create container: {create_result.stderr}")
            
            container_id = create_result.stdout.strip()
            
            # Almacenar información del contenedor
            container_info = {
                'task_id': task_id,
                'container_id': container_id,
                'container_name': container_name,
                'image_name': image_name,
                'task_type': task_type,
                'workspace_path': str(workspace_path),
                'created_at': datetime.now().isoformat(),
                'status': 'running',
                'resources': {
                    'memory_limit': '1g',
                    'cpu_limit': '1.0'
                }
            }
            
            self.containers[task_id] = container_info
            
            return {
                'success': True,
                'container_info': container_info,
                'message': f'Container created successfully: {container_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fallback': 'Using simulated container environment'
            }
    
    def _create_simulated_container(self, task_id: str, task_type: str) -> Dict[str, Any]:
        """Crear entorno simulado cuando Docker no está disponible"""
        
        # Crear directorio aislado
        workspace_path = Path(tempfile.gettempdir()) / 'agent_workspaces' / task_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Crear script de inicialización
        init_script = self._generate_init_script(task_type)
        init_script_path = workspace_path / 'init.sh'
        init_script_path.write_text(init_script)
        init_script_path.chmod(0o755)
        
        # Ejecutar script de inicialización
        try:
            subprocess.run(['bash', str(init_script_path)], cwd=str(workspace_path), timeout=60)
        except Exception as e:
            print(f"Warning: Failed to run init script: {e}")
        
        container_info = {
            'task_id': task_id,
            'container_id': f'simulated-{task_id}',
            'container_name': f'simulated-container-{task_id}',
            'task_type': task_type,
            'workspace_path': str(workspace_path),
            'created_at': datetime.now().isoformat(),
            'status': 'running',
            'simulated': True,
            'resources': {
                'memory_limit': 'unlimited',
                'cpu_limit': 'unlimited'
            }
        }
        
        self.containers[task_id] = container_info
        
        return {
            'success': True,
            'container_info': container_info,
            'message': f'Simulated container environment created: {workspace_path}',
            'simulated': True
        }
    
    def _generate_dockerfile(self, task_type: str, base_image: str, 
                           custom_requirements: List[str] = None) -> str:
        """Generar Dockerfile personalizado según el tipo de tarea"""
        
        dockerfile_lines = [
            f"FROM {base_image}",
            "",
            "# Crear usuario no-root para seguridad",
            "RUN useradd -m -s /bin/bash agent",
            "USER agent",
            "WORKDIR /workspace",
            ""
        ]
        
        if task_type == 'web-development':
            dockerfile_lines.extend([
                "# Instalar herramientas de desarrollo web",
                "USER root",
                "RUN npm install -g create-react-app vue-cli @angular/cli",
                "RUN npm install -g webpack webpack-cli parcel-bundler",
                "RUN npm install -g typescript eslint prettier",
                "USER agent"
            ])
        
        elif task_type == 'data-processing':
            dockerfile_lines.extend([
                "# Instalar librerías de ciencia de datos",
                "USER root",
                "RUN pip install pandas numpy scipy matplotlib seaborn",
                "RUN pip install scikit-learn tensorflow keras",
                "RUN pip install jupyter jupyterlab plotly",
                "USER agent"
            ])
        
        elif task_type == 'system-administration':
            dockerfile_lines.extend([
                "# Instalar herramientas de administración",
                "USER root",
                "RUN apt-get update && apt-get install -y \\",
                "    curl wget git vim nano \\",
                "    htop iotop netstat-openbsd \\",
                "    unzip zip tar gzip \\",
                "    && rm -rf /var/lib/apt/lists/*",
                "USER agent"
            ])
        
        else:  # general
            dockerfile_lines.extend([
                "# Instalar herramientas generales",
                "USER root",
                "RUN pip install requests beautifulsoup4 lxml",
                "RUN pip install pyyaml python-dotenv",
                "USER agent"
            ])
        
        # Agregar requirements personalizados
        if custom_requirements:
            dockerfile_lines.extend([
                "",
                "# Instalar requirements personalizados",
                "USER root"
            ])
            for req in custom_requirements:
                dockerfile_lines.append(f"RUN {req}")
            dockerfile_lines.append("USER agent")
        
        dockerfile_lines.extend([
            "",
            "# Configurar entorno",
            "ENV PYTHONPATH=/workspace",
            "ENV PATH=/workspace:$PATH",
            "",
            "# Punto de entrada",
            "CMD [\"bash\"]"
        ])
        
        return "\n".join(dockerfile_lines)
    
    def _generate_init_script(self, task_type: str) -> str:
        """Generar script de inicialización para entorno simulado"""
        
        script_lines = [
            "#!/bin/bash",
            "# Script de inicialización para entorno simulado",
            "",
            "echo 'Initializing simulated container environment...'",
            ""
        ]
        
        if task_type == 'web-development':
            script_lines.extend([
                "# Verificar Node.js",
                "if command -v node >/dev/null 2>&1; then",
                "    echo 'Node.js is available'",
                "else",
                "    echo 'Warning: Node.js not found'",
                "fi",
                ""
            ])
        
        elif task_type == 'data-processing':
            script_lines.extend([
                "# Verificar Python y librerías",
                "python3 -c 'import sys; print(f\"Python {sys.version}\")' || echo 'Warning: Python not found'",
                ""
            ])
        
        script_lines.extend([
            "# Crear estructura de directorios",
            "mkdir -p src data output logs temp",
            "",
            "# Configurar variables de entorno",
            "export WORKSPACE=$(pwd)",
            "export PYTHONPATH=$WORKSPACE",
            "",
            "echo 'Environment initialization completed.'"
        ])
        
        return "\n".join(script_lines)
    
    def execute_command(self, task_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Ejecutar comando dentro del contenedor de una tarea"""
        
        if task_id not in self.containers:
            return {
                'success': False,
                'error': f'Container for task {task_id} not found'
            }
        
        container_info = self.containers[task_id]
        
        try:
            if container_info.get('simulated', False):
                # Ejecutar en entorno simulado
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=container_info['workspace_path']
                )
            else:
                # Ejecutar en contenedor Docker real
                docker_cmd = [
                    'docker', 'exec',
                    container_info['container_name'],
                    'bash', '-c', command
                ]
                
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': command,
                'container_id': container_info['container_id']
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Command timed out after {timeout} seconds',
                'command': command
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command
            }
    
    def get_container_info(self, task_id: str) -> Dict[str, Any]:
        """Obtener información de un contenedor"""
        return self.containers.get(task_id, {
            'error': 'Container not found'
        })
    
    def list_containers(self) -> Dict[str, Any]:
        """Listar todos los contenedores activos"""
        return {
            'containers': list(self.containers.values()),
            'total': len(self.containers)
        }
    
    def stop_container(self, task_id: str) -> Dict[str, Any]:
        """Detener y limpiar contenedor de una tarea"""
        
        if task_id not in self.containers:
            return {
                'success': False,
                'error': f'Container for task {task_id} not found'
            }
        
        container_info = self.containers[task_id]
        
        try:
            if not container_info.get('simulated', False):
                # Detener contenedor Docker real
                subprocess.run(
                    ['docker', 'stop', container_info['container_name']],
                    capture_output=True,
                    timeout=10
                )
                
                # Limpiar imagen personalizada
                subprocess.run(
                    ['docker', 'rmi', container_info['image_name']],
                    capture_output=True,
                    timeout=10
                )
            
            # Limpiar workspace (opcional)
            workspace_path = Path(container_info['workspace_path'])
            if workspace_path.exists():
                shutil.rmtree(workspace_path, ignore_errors=True)
            
            # Remover de la lista activa
            del self.containers[task_id]
            
            return {
                'success': True,
                'message': f'Container {container_info["container_name"]} stopped and cleaned'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_all_containers(self) -> Dict[str, Any]:
        """Limpiar todos los contenedores activos"""
        
        results = []
        for task_id in list(self.containers.keys()):
            result = self.stop_container(task_id)
            results.append({
                'task_id': task_id,
                'result': result
            })
        
        return {
            'success': True,
            'cleanup_results': results,
            'total_cleaned': len(results)
        }
    
    def get_resource_usage(self, task_id: str) -> Dict[str, Any]:
        """Obtener uso de recursos de un contenedor"""
        
        if task_id not in self.containers:
            return {
                'success': False,
                'error': f'Container for task {task_id} not found'
            }
        
        container_info = self.containers[task_id]
        
        if container_info.get('simulated', False):
            return {
                'success': True,
                'simulated': True,
                'cpu_usage': '0%',
                'memory_usage': '0 MB',
                'disk_usage': '0 MB'
            }
        
        try:
            # Obtener estadísticas del contenedor
            stats_result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 
                 'table {{.CPUPerc}}\t{{.MemUsage}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if stats_result.returncode == 0:
                lines = stats_result.stdout.strip().split('\n')
                if len(lines) > 1:
                    data = lines[1].split('\t')
                    return {
                        'success': True,
                        'cpu_usage': data[0] if len(data) > 0 else '0%',
                        'memory_usage': data[1] if len(data) > 1 else '0 MB'
                    }
            
            return {
                'success': False,
                'error': 'Failed to get container stats'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }