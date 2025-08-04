"""
Herramientas de Ollama para análisis y procesamiento inteligente
Estas herramientas utilizan Ollama para generar contenido relevante
en lugar de hacer búsquedas web irrelevantes.
"""

import logging
import sys
import os
from typing import Dict, Any

# Add the backend src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.base_tool import BaseTool, register_tool
from services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

@register_tool
class OllamaAnalysisTool(BaseTool):
    """
    Herramienta de análisis inteligente usando Ollama
    Genera análisis detallados basados en datos previos y contexto
    """
    
    @classmethod
    def get_name(cls) -> str:
        return "ollama_analysis"
    
    @classmethod
    def get_description(cls) -> str:
        return "Realiza análisis inteligentes usando Ollama basado en contexto previo"
    
    @classmethod
    def get_parameters_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Prompt para el análisis inteligente"
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Máximo número de tokens para la respuesta",
                    "default": 1000
                }
            },
            "required": ["prompt"]
        }
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecutar análisis usando Ollama
        """
        try:
            prompt = parameters.get('prompt', '')
            max_tokens = parameters.get('max_tokens', 1000)
            
            if not prompt:
                return {
                    'success': False,
                    'error': 'Prompt es requerido para el análisis'
                }
            
            # Crear instancia de OllamaService
            ollama_service = OllamaService()
            
            # Configurar parámetros de generación
            generation_params = {
                'max_tokens': max_tokens,
                'temperature': 0.7,
                'system_prompt': "Eres un asistente experto en análisis. Proporciona análisis detallados, estructurados y útiles basados en la información proporcionada."
            }
            
            # Generar respuesta usando Ollama
            logger.info(f"🧠 Iniciando análisis con Ollama - Prompt: {prompt[:100]}...")
            
            response = ollama_service.generate_response(
                prompt=prompt,
                **generation_params
            )
            
            if response and 'response' in response:
                analysis_content = response['response']
                
                return {
                    'success': True,
                    'type': 'analysis',
                    'content': analysis_content,
                    'summary': f"Análisis completado: {len(analysis_content)} caracteres generados",
                    'tool_used': 'ollama_analysis',
                    'analysis_result': analysis_content
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudo generar análisis con Ollama',
                    'details': response
                }
                
        except Exception as e:
            logger.error(f"Error en análisis Ollama: {e}")
            return {
                'success': False,
                'error': f'Error interno en análisis: {str(e)}'
            }