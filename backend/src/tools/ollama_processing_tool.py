"""
Herramienta de procesamiento final usando Ollama
Genera contenido final procesado basado en todo el contexto de la tarea
"""

import logging
import sys
import os
import time
from typing import Dict, Any, List

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool
from ..services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

@register_tool
class OllamaProcessingTool(BaseTool):
    """
    Herramienta de procesamiento final usando Ollama
    Genera contenido final procesado basado en todo el contexto de la tarea
    """
    
    def __init__(self):
        super().__init__(
            name="ollama_processing",
            description="Procesa y genera contenido final usando Ollama basado en todo el contexto"
        )
    
    def _define_parameters(self) -> List[ParameterDefinition]:
        """Definir parámetros específicos del procesamiento Ollama"""
        return [
            ParameterDefinition(
                name="prompt",
                param_type="string",
                required=True,
                description="Prompt completo para el procesamiento final",
                min_value=10  # Mínimo 10 caracteres
            ),
            ParameterDefinition(
                name="max_tokens",
                param_type="integer",
                required=False,
                description="Máximo número de tokens para la respuesta",
                default=1500,
                min_value=100,
                max_value=4000
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        """
        Ejecutar procesamiento final usando Ollama
        """
        try:
            prompt = parameters.get('prompt', '')
            max_tokens = parameters.get('max_tokens', 1500)
            
            # Crear instancia de OllamaService
            ollama_service = OllamaService()
            
            # Configurar contexto con parámetros de generación para procesamiento final
            context = {
                'max_tokens': max_tokens,
                'temperature': 0.8,
                'system_prompt': "Eres un asistente experto en generar contenido final completo y detallado. Tu tarea es crear el resultado final exacto que se solicita basándote en toda la información recopilada previamente. Sé específico, detallado y útil."
            }
            
            # Generar respuesta final usando Ollama
            logger.info(f"🔄 Iniciando procesamiento final con Ollama - Prompt: {prompt[:100]}...")
            
            response = ollama_service.generate_response(
                prompt=prompt,
                context=context,
                use_tools=False,  # No necesitamos tools para procesamiento final
                task_id=config.get('task_id', 'unknown'),
                step_id=f"processing_{int(time.time())}"
            )
            
            if response and 'response' in response:
                processed_content = response['response']
                
                result_data = {
                    'type': 'processing',
                    'content': processed_content,
                    'summary': f"Procesamiento completado: {len(processed_content)} caracteres generados",
                    'tool_used': 'ollama_processing',
                    'final_result': processed_content,
                    'processed_content': processed_content,
                    'prompt_length': len(prompt),
                    'response_length': len(processed_content)
                }
                
                return self._create_success_result(result_data)
            else:
                return self._create_error_result(f'No se pudo generar contenido procesado con Ollama: {response}')
                
        except Exception as e:
            logger.error(f"Error en procesamiento Ollama: {e}")
            return self._create_error_result(f'Error interno en procesamiento: {str(e)}')