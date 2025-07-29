"""
Herramienta de gestión de archivos - Maneja operaciones con archivos y directorios
"""

import os
import shutil
import json
import mimetypes
from pathlib import Path
from typing import Dict, Any, List
import time

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult

class FileManagerTool(BaseTool):
    def __init__(self):
        self.name = "file_manager"
        self.description = "Gestiona archivos y directorios de forma segura"
        self.parameters = [
            {
                "name": "action",
                "type": "string",
                "required": True,
                "description": "Acción a realizar: read, write, create, delete, list, copy, move, mkdir"
            },
            {
                "name": "path",
                "type": "string",
                "required": True,
                "description": "Ruta del archivo o directorio"
            },
            {
                "name": "content",
                "type": "string",
                "required": False,
                "description": "Contenido para escribir (solo para write/create)"
            },
            {
                "name": "destination",
                "type": "string",
                "required": False,
                "description": "Ruta de destino (solo para copy/move)"
            },
            {
                "name": "encoding",
                "type": "string",
                "required": False,
                "description": "Codificación del archivo",
                "default": "utf-8"
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
        
        if 'action' not in parameters:
            return {'valid': False, 'error': 'action parameter is required'}
        
        if 'path' not in parameters:
            return {'valid': False, 'error': 'path parameter is required'}
        
        action = parameters['action']
        valid_actions = ['read', 'write', 'create', 'delete', 'list', 'copy', 'move', 'mkdir']
        
        if action not in valid_actions:
            return {'valid': False, 'error': f'action must be one of: {valid_actions}'}
        
        if action in ['write', 'create'] and 'content' not in parameters:
            return {'valid': False, 'error': f'content parameter is required for {action}'}
        
        if action in ['copy', 'move'] and 'destination' not in parameters:
            return {'valid': False, 'error': f'destination parameter is required for {action}'}
        
        return {'valid': True}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar operación de gestión de archivos"""
        if config is None:
            config = {}
        
        action = parameters['action']
        path = parameters['path']
        
        try:
            if action == 'read':
                return self._read_file(path, parameters.get('encoding', 'utf-8'))
            elif action == 'write':
                return self._write_file(path, parameters['content'], parameters.get('encoding', 'utf-8'))
            elif action == 'create':
                return self._create_file(path, parameters['content'], parameters.get('encoding', 'utf-8'))
            elif action == 'delete':
                return self._delete_path(path)
            elif action == 'list':
                return self._list_directory(path)
            elif action == 'copy':
                return self._copy_path(path, parameters['destination'])
            elif action == 'move':
                return self._move_path(path, parameters['destination'])
            elif action == 'mkdir':
                return self._create_directory(path)
            else:
                return {'error': 'Invalid action specified'}
                
        except Exception as e:
            return {'error': str(e), 'action': action, 'path': path}
    
    def _read_file(self, path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Leer archivo"""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                return {'error': 'File does not exist'}
            
            if not path_obj.is_file():
                return {'error': 'Path is not a file'}
            
            # Obtener información del archivo
            stat = path_obj.stat()
            mime_type, _ = mimetypes.guess_type(str(path_obj))
            
            # Leer contenido
            if mime_type and mime_type.startswith('text/'):
                content = path_obj.read_text(encoding=encoding)
            else:
                # Para archivos binarios, leer como bytes y convertir a base64
                import base64
                content = base64.b64encode(path_obj.read_bytes()).decode('ascii')
            
            return {
                'path': str(path_obj),
                'content': content,
                'size': stat.st_size,
                'mime_type': mime_type,
                'modified': stat.st_mtime,
                'is_binary': not (mime_type and mime_type.startswith('text/')),
                'success': True
            }
            
        except UnicodeDecodeError:
            return {'error': f'Unable to decode file with encoding {encoding}'}
        except Exception as e:
            return {'error': str(e)}
    
    def _write_file(self, path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Escribir archivo (sobrescribir si existe)"""
        try:
            path_obj = Path(path)
            
            # Crear directorio padre si no existe
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Escribir archivo
            path_obj.write_text(content, encoding=encoding)
            
            return {
                'path': str(path_obj),
                'size': len(content.encode(encoding)),
                'success': True
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _create_file(self, path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Crear archivo (fallar si existe)"""
        try:
            path_obj = Path(path)
            
            if path_obj.exists():
                return {'error': 'File already exists'}
            
            # Crear directorio padre si no existe
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear archivo
            path_obj.write_text(content, encoding=encoding)
            
            return {
                'path': str(path_obj),
                'size': len(content.encode(encoding)),
                'success': True
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _delete_path(self, path: str) -> Dict[str, Any]:
        """Eliminar archivo o directorio"""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                return {'error': 'Path does not exist'}
            
            if path_obj.is_file():
                path_obj.unlink()
                return {'path': str(path_obj), 'type': 'file', 'success': True}
            elif path_obj.is_dir():
                shutil.rmtree(path_obj)
                return {'path': str(path_obj), 'type': 'directory', 'success': True}
            else:
                return {'error': 'Path is neither file nor directory'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _list_directory(self, path: str) -> Dict[str, Any]:
        """Listar contenido de directorio"""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                return {'error': 'Directory does not exist'}
            
            if not path_obj.is_dir():
                return {'error': 'Path is not a directory'}
            
            items = []
            for item in sorted(path_obj.iterdir()):
                stat = item.stat()
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': stat.st_size if item.is_file() else None,
                    'modified': stat.st_mtime,
                    'permissions': oct(stat.st_mode)[-3:]
                })
            
            return {
                'path': str(path_obj),
                'items': items,
                'count': len(items),
                'success': True
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _copy_path(self, source: str, destination: str) -> Dict[str, Any]:
        """Copiar archivo o directorio"""
        try:
            source_obj = Path(source)
            dest_obj = Path(destination)
            
            if not source_obj.exists():
                return {'error': 'Source path does not exist'}
            
            if source_obj.is_file():
                dest_obj.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_obj, dest_obj)
                return {'source': str(source_obj), 'destination': str(dest_obj), 'type': 'file', 'success': True}
            elif source_obj.is_dir():
                shutil.copytree(source_obj, dest_obj)
                return {'source': str(source_obj), 'destination': str(dest_obj), 'type': 'directory', 'success': True}
            else:
                return {'error': 'Source is neither file nor directory'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _move_path(self, source: str, destination: str) -> Dict[str, Any]:
        """Mover archivo o directorio"""
        try:
            source_obj = Path(source)
            dest_obj = Path(destination)
            
            if not source_obj.exists():
                return {'error': 'Source path does not exist'}
            
            dest_obj.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_obj), str(dest_obj))
            
            return {
                'source': str(source_obj),
                'destination': str(dest_obj),
                'success': True
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _create_directory(self, path: str) -> Dict[str, Any]:
        """Crear directorio"""
        try:
            path_obj = Path(path)
            path_obj.mkdir(parents=True, exist_ok=True)
            
            return {
                'path': str(path_obj),
                'success': True
            }
            
        except Exception as e:
            return {'error': str(e)}