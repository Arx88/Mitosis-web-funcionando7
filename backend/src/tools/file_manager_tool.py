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

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

@register_tool
class FileManagerTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="file_manager",
            description="Gestiona archivos y directorios de forma segura"
        )
    
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="action",
                param_type="string",
                required=True,
                description="Acción a realizar: read, write, create, delete, list, copy, move, mkdir"
            ),
            ParameterDefinition(
                name="path",
                param_type="string",
                required=True,
                description="Ruta del archivo o directorio"
            ),
            ParameterDefinition(
                name="content",
                param_type="string",
                required=False,
                description="Contenido para escribir (solo para write/create)"
            ),
            ParameterDefinition(
                name="destination",
                param_type="string",
                required=False,
                description="Ruta de destino (solo para copy/move)"
            ),
            ParameterDefinition(
                name="encoding",
                param_type="string",
                required=False,
                description="Codificación del archivo",
                default="utf-8"
            )
        ]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros específicos del file manager"""
        action = parameters.get('action')
        path = parameters.get('path')
        
        if not action:
            return {'valid': False, 'error': 'Parámetro "action" es requerido'}
        
        if not path:
            return {'valid': False, 'error': 'Parámetro "path" es requerido'}
        
        valid_actions = ['read', 'write', 'create', 'delete', 'list', 'copy', 'move', 'mkdir']
        if action not in valid_actions:
            return {'valid': False, 'error': f'Acción inválida. Debe ser una de: {valid_actions}'}
        
        if action in ['write', 'create'] and not parameters.get('content'):
            return {'valid': False, 'error': f'Parámetro "content" es requerido para {action}'}
        
        if action in ['copy', 'move'] and not parameters.get('destination'):
            return {'valid': False, 'error': f'Parámetro "destination" es requerido para {action}'}
        
        return {'valid': True}
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> ToolExecutionResult:
        """Ejecutar operación de gestión de archivos"""
        if config is None:
            config = {}
        
        action = parameters['action']
        path = parameters['path']
        
        try:
            if action == 'read':
                result = self._read_file(path, parameters.get('encoding', 'utf-8'))
            elif action == 'write':
                result = self._write_file(path, parameters['content'], parameters.get('encoding', 'utf-8'))
            elif action == 'create':
                result = self._create_file(path, parameters['content'], parameters.get('encoding', 'utf-8'))
            elif action == 'delete':
                result = self._delete_path(path)
            elif action == 'list':
                result = self._list_directory(path)
            elif action == 'copy':
                result = self._copy_path(path, parameters['destination'])
            elif action == 'move':
                result = self._move_path(path, parameters['destination'])
            elif action == 'mkdir':
                result = self._create_directory(path)
            else:
                return ToolExecutionResult(
                    success=False,
                    data={'error': 'Invalid action specified', 'action': action, 'path': path},
                    error='Invalid action specified'
                )
            
            # Si el resultado tiene 'error', es un fallo
            if 'error' in result:
                return ToolExecutionResult(
                    success=False,
                    data=result,
                    error=result['error']
                )
            else:
                return ToolExecutionResult(
                    success=True,
                    data=result
                )
                
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                data={'error': str(e), 'action': action, 'path': path, 'exception': type(e).__name__},
                error=str(e)
            )
    
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