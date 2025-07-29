"""
Herramienta simple de gestión de archivos
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

@register_tool  
class SimpleFileManager(BaseTool):
    def __init__(self):
        super().__init__(
            name="file_manager",
            description="Herramienta simple de gestión de archivos"
        )
    
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="action", 
                param_type="string",
                required=True,
                description="Acción: read, write, list, create, delete"
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
                description="Contenido para escribir"
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        try:
            action = parameters.get('action', '')
            path = parameters.get('path', '')
            content = parameters.get('content', '')
            
            if action == 'read':
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    return ToolExecutionResult(
                        success=True,
                        data={
                            'path': path,
                            'content': file_content,
                            'size': len(file_content)
                        }
                    )
                except Exception as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f'Error leyendo archivo: {str(e)}'
                    )
            
            elif action == 'write':
                try:
                    # Crear directorio si no existe
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    return ToolExecutionResult(
                        success=True,
                        data={
                            'path': path,
                            'bytes_written': len(content),
                            'message': 'Archivo escrito exitosamente'
                        }
                    )
                except Exception as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f'Error escribiendo archivo: {str(e)}'
                    )
            
            elif action == 'list':
                try:
                    if os.path.isdir(path):
                        files = []
                        for item in os.listdir(path):
                            item_path = os.path.join(path, item)
                            files.append({
                                'name': item,
                                'path': item_path,
                                'type': 'directory' if os.path.isdir(item_path) else 'file',
                                'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                            })
                        
                        return ToolExecutionResult(
                            success=True,
                            data={
                                'path': path,
                                'files': files,
                                'count': len(files)
                            }
                        )
                    else:
                        return ToolExecutionResult(
                            success=False,
                            error=f'La ruta no es un directorio: {path}'
                        )
                except Exception as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f'Error listando directorio: {str(e)}'
                    )
            
            else:
                return ToolExecutionResult(
                    success=False,
                    error=f'Acción no soportada: {action}'
                )
                
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f'Error en file manager: {str(e)}'
            )