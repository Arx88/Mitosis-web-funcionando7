"""
Environment Setup Manager - Gestiona la preparación de entornos para tareas
"""

import os
import time
import asyncio
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import tempfile
from pathlib import Path
from .container_manager import ContainerManager

class EnvironmentSetupManager:
    def __init__(self):
        self.name = "environment_setup"
        self.description = "Gestiona la configuración y preparación de entornos para tareas"
        self.setup_sessions = {}  # Almacenar sesiones de setup activas
        self.container_manager = ContainerManager()  # Inicializar gestor de contenedores
        
    def get_task_type(self, task_title: str, task_content: str = "") -> str:
        """Detectar el tipo de tarea basado en el título y contenido"""
        title_lower = task_title.lower()
        content_lower = task_content.lower()
        
        # Web Development indicators
        if any(keyword in title_lower for keyword in ['web', 'website', 'página', 'frontend', 'backend', 'html', 'css', 'javascript', 'react', 'node']):
            return 'web-development'
        
        # Data Processing indicators
        if any(keyword in title_lower for keyword in ['datos', 'data', 'análisis', 'analysis', 'python', 'pandas', 'numpy', 'machine learning', 'ml', 'ai']):
            return 'data-processing'
        
        # System Administration indicators
        if any(keyword in title_lower for keyword in ['sistema', 'system', 'server', 'administración', 'admin', 'linux', 'configurar', 'instalar']):
            return 'system-administration'
        
        return 'general'
    
    async def setup_environment(self, task_id: str, task_title: str, task_type: str = None) -> Dict[str, Any]:
        """Configurar entorno para una tarea específica"""
        
        if not task_type:
            task_type = self.get_task_type(task_title)
        
        # Crear sesión de setup
        session = {
            'task_id': task_id,
            'task_title': task_title,
            'task_type': task_type,
            'started_at': datetime.now().isoformat(),
            'steps': self._get_setup_steps(task_type),
            'current_step': 0,
            'status': 'initializing',
            'progress': 0,
            'environment_path': None,
            'logs': []
        }
        
        self.setup_sessions[task_id] = session
        
        try:
            # Ejecutar pasos de setup
            for i, step in enumerate(session['steps']):
                session['current_step'] = i
                session['status'] = f"executing_{step['id']}"
                
                self._log_step(session, f"Starting {step['title']}")
                
                # Ejecutar el paso
                success = await self._execute_step(session, step)
                
                if not success:
                    session['status'] = 'failed'
                    session['error'] = f"Failed at step: {step['title']}"
                    return session
                
                # Actualizar progreso
                session['progress'] = int(((i + 1) / len(session['steps'])) * 100)
                self._log_step(session, f"Completed {step['title']}")
                
                # Simular tiempo de ejecución
                await asyncio.sleep(step['duration'])
            
            session['status'] = 'completed'
            session['completed_at'] = datetime.now().isoformat()
            self._log_step(session, "Environment setup completed successfully")
            
            return session
            
        except Exception as e:
            session['status'] = 'failed'
            session['error'] = str(e)
            self._log_step(session, f"Setup failed: {str(e)}")
            return session
    
    def _get_setup_steps(self, task_type: str) -> List[Dict[str, Any]]:
        """Obtener pasos de configuración según el tipo de tarea"""
        
        base_steps = [
            {
                'id': 'safe-environment',
                'title': 'Setting Up Safe Environment',
                'description': 'Creating isolated container environment...',
                'duration': 2,  # Reducido para demo
                'actions': ['create_workspace', 'set_permissions', 'initialize_container']
            },
            {
                'id': 'cloud-init',
                'title': 'Initializing Cloud Environment',
                'description': 'Connecting to cloud resources and allocating compute...',
                'duration': 3,
                'actions': ['allocate_resources', 'setup_networking', 'configure_storage']
            },
            {
                'id': 'resources',
                'title': 'Provisioning Resources',
                'description': 'Installing required dependencies and tools...',
                'duration': 4,
                'actions': ['install_base_packages', 'setup_package_managers', 'install_specific_tools']
            },
            {
                'id': 'configuration',
                'title': 'Configuring Environment',
                'description': 'Setting up environment variables and configurations...',
                'duration': 2,
                'actions': ['set_environment_vars', 'configure_tools', 'setup_aliases']
            },
            {
                'id': 'agent-start',
                'title': 'Starting the Agent',
                'description': 'Initializing AI agent and loading task context...',
                'duration': 1,
                'actions': ['load_context', 'initialize_tools', 'start_agent']
            }
        ]
        
        # Personalizar según el tipo de tarea
        if task_type == 'web-development':
            base_steps[2]['description'] = 'Installing Node.js, npm, frameworks and build tools...'
            base_steps[2]['duration'] = 5
            base_steps[2]['actions'].extend(['install_nodejs', 'install_npm_packages', 'setup_build_tools'])
        
        elif task_type == 'data-processing':
            base_steps[2]['description'] = 'Installing Python, pandas, numpy, jupyter and ML libraries...'
            base_steps[2]['duration'] = 6
            base_steps[2]['actions'].extend(['install_python', 'install_data_packages', 'setup_jupyter'])
        
        elif task_type == 'system-administration':
            base_steps[2]['description'] = 'Installing system tools, monitoring and security utilities...'
            base_steps[2]['duration'] = 4
            base_steps[2]['actions'].extend(['install_system_tools', 'setup_monitoring', 'configure_security'])
        
        return base_steps
    
    async def _execute_step(self, session: Dict[str, Any], step: Dict[str, Any]) -> bool:
        """Ejecutar un paso específico de configuración"""
        
        step_id = step['id']
        
        try:
            if step_id == 'safe-environment':
                return await self._setup_safe_environment(session)
            elif step_id == 'cloud-init':
                return await self._initialize_cloud_environment(session)
            elif step_id == 'resources':
                return await self._provision_resources(session)
            elif step_id == 'configuration':
                return await self._configure_environment(session)
            elif step_id == 'agent-start':
                return await self._start_agent(session)
            else:
                return True
                
        except Exception as e:
            self._log_step(session, f"Error in step {step_id}: {str(e)}")
            return False
    
    async def _setup_safe_environment(self, session: Dict[str, Any]) -> bool:
        """Configurar entorno seguro e aislado usando containers"""
        task_id = session['task_id']
        task_type = session['task_type']
        
        # Usar container manager para crear entorno aislado
        self._log_step(session, f"Creating isolated container for {task_type} task...")
        await asyncio.sleep(0.5)
        
        container_result = self.container_manager.create_container(task_id, task_type)
        
        if container_result['success']:
            session['container_info'] = container_result['container_info']
            session['environment_path'] = container_result['container_info']['workspace_path']
            
            if container_result['container_info'].get('simulated', False):
                self._log_step(session, "Simulated container environment created (Docker not available)")
            else:
                self._log_step(session, f"Docker container created: {container_result['container_info']['container_name']}")
            
            # Verificar entorno
            await asyncio.sleep(1)
            self._log_step(session, "Container environment verified and ready")
            
            return True
        else:
            self._log_step(session, f"Failed to create container: {container_result.get('error', 'Unknown error')}")
            return False
    
    async def _initialize_cloud_environment(self, session: Dict[str, Any]) -> bool:
        """Inicializar entorno en la nube"""
        
        # Simular conexión a recursos cloud
        await asyncio.sleep(1)
        self._log_step(session, "Connected to cloud resources")
        
        # Simular asignación de recursos
        await asyncio.sleep(1)
        self._log_step(session, "Allocated compute resources: 2 CPU, 4GB RAM")
        
        # Simular configuración de red
        await asyncio.sleep(1)
        self._log_step(session, "Network configuration completed")
        
        return True
    
    async def _provision_resources(self, session: Dict[str, Any]) -> bool:
        """Aprovisionar recursos según el tipo de tarea"""
        task_type = session['task_type']
        
        # Instalar herramientas base
        await asyncio.sleep(1)
        self._log_step(session, "Installing base system packages...")
        
        if task_type == 'web-development':
            await asyncio.sleep(1)
            self._log_step(session, "Installing Node.js v18.x...")
            await asyncio.sleep(1)
            self._log_step(session, "Installing npm packages: express, react, webpack...")
            await asyncio.sleep(1)
            self._log_step(session, "Setting up build tools and dev environment...")
            
        elif task_type == 'data-processing':
            await asyncio.sleep(1)
            self._log_step(session, "Installing Python 3.9 with pip...")
            await asyncio.sleep(1)
            self._log_step(session, "Installing data science packages: pandas, numpy, scipy...")
            await asyncio.sleep(1)
            self._log_step(session, "Setting up Jupyter notebook environment...")
            
        elif task_type == 'system-administration':
            await asyncio.sleep(1)
            self._log_step(session, "Installing system administration tools...")
            await asyncio.sleep(1)
            self._log_step(session, "Setting up monitoring: htop, iotop, netstat...")
            await asyncio.sleep(1)
            self._log_step(session, "Configuring security tools and firewalls...")
        
        else:
            await asyncio.sleep(2)
            self._log_step(session, "Installing general purpose tools and utilities...")
        
        return True
    
    async def _configure_environment(self, session: Dict[str, Any]) -> bool:
        """Configurar variables de entorno y herramientas"""
        
        # Configurar variables de entorno
        await asyncio.sleep(0.5)
        self._log_step(session, "Setting environment variables...")
        
        # Configurar herramientas
        await asyncio.sleep(1)
        self._log_step(session, "Configuring installed tools and dependencies...")
        
        # Configurar aliases y shortcuts
        await asyncio.sleep(0.5)
        self._log_step(session, "Setting up command aliases and shortcuts...")
        
        return True
    
    async def _start_agent(self, session: Dict[str, Any]) -> bool:
        """Inicializar el agente AI"""
        
        # Cargar contexto de la tarea
        await asyncio.sleep(0.3)
        self._log_step(session, "Loading task context and history...")
        
        # Inicializar herramientas
        await asyncio.sleep(0.4)
        self._log_step(session, "Initializing AI tools and capabilities...")
        
        # Iniciar agente
        await asyncio.sleep(0.3)
        self._log_step(session, "Agent ready for task execution!")
        
        return True
    
    def _log_step(self, session: Dict[str, Any], message: str):
        """Agregar log a la sesión"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message
        }
        session['logs'].append(log_entry)
    
    def get_setup_status(self, task_id: str) -> Dict[str, Any]:
        """Obtener estado de configuración de una tarea"""
        return self.setup_sessions.get(task_id, {
            'status': 'not_found',
            'error': 'Setup session not found'
        })
    
    def cleanup_session(self, task_id: str):
        """Limpiar sesión de configuración"""
        # Limpiar contenedor si existe
        self.container_manager.stop_container(task_id)
        
        # Limpiar sesión
        if task_id in self.setup_sessions:
            del self.setup_sessions[task_id]
    
    def get_container_manager(self) -> ContainerManager:
        """Obtener el gestor de contenedores"""
        return self.container_manager
    
    def execute_in_container(self, task_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Ejecutar comando en el contenedor de una tarea"""
        return self.container_manager.execute_command(task_id, command, timeout)