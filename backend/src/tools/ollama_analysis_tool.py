"""
Herramientas de Ollama para análisis y procesamiento inteligente
Estas herramientas utilizan Ollama para generar contenido relevante
en lugar de hacer búsquedas web irrelevantes.
"""

import logging
import sys
import os
from typing import Dict, Any, List

# Add the backend src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool
from services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

@register_tool
class OllamaAnalysisTool(BaseTool):
    """
    Herramienta de análisis inteligente usando Ollama
    Genera análisis detallados basados en datos previos y contexto
    """
    
    def __init__(self):
        super().__init__(
            name="ollama_analysis",
            description="Realiza análisis inteligentes usando Ollama basado en contexto previo"
        )
    
    def _define_parameters(self) -> List[ParameterDefinition]:
        """Definir parámetros específicos del análisis Ollama"""
        return [
            ParameterDefinition(
                name="prompt",
                param_type="string",
                required=True,
                description="Prompt para el análisis inteligente",
                min_value=10  # Mínimo 10 caracteres
            ),
            ParameterDefinition(
                name="max_tokens",
                param_type="integer",
                required=False,
                description="Máximo número de tokens para la respuesta",
                default=1000,
                min_value=100,
                max_value=4000
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        """
        Ejecutar análisis usando Ollama
        """
        try:
            prompt = parameters.get('prompt', '')
            max_tokens = parameters.get('max_tokens', 1000)
            
            # Crear instancia de OllamaService
            ollama_service = OllamaService()
            
            # Configurar contexto para generar respuesta
            context = {
                'system_prompt': "Eres un asistente experto en análisis. Proporciona análisis detallados, estructurados y útiles basados en la información proporcionada.",
                'max_tokens': max_tokens,
                'temperature': 0.7
            }
            
            # Generar respuesta usando Ollama
            logger.info(f"🧠 Iniciando análisis con Ollama - Prompt: {prompt[:100]}...")
            
            response = ollama_service.generate_response(
                prompt=prompt,
                context=context,
                use_tools=False,
                task_id=self.current_task_id or "analysis",
                step_id="analysis_step"
            )
            
            if response and 'response' in response:
                analysis_content = response['response']
                
                result_data = {
                    'type': 'analysis',
                    'content': analysis_content,
                    'summary': f"Análisis completado: {len(analysis_content)} caracteres generados",
                    'tool_used': 'ollama_analysis',
                    'analysis_result': analysis_content,
                    'prompt_length': len(prompt),
                    'response_length': len(analysis_content)
                }
                
                return self._create_success_result(result_data)
            else:
                return self._create_error_result(f'No se pudo generar análisis con Ollama: {response}')
                
        except Exception as e:
            logger.error(f"Error en análisis Ollama: {e}")
            return self._create_error_result(f'Error interno en análisis: {str(e)}')