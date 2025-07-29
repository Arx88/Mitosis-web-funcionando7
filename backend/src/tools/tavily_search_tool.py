"""
Herramienta REAL de búsqueda web usando Tavily API
"""

import os
import requests
from typing import Dict, List, Any
from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

@register_tool
class TavilySearchTool(BaseTool):
    """Herramienta REAL para búsquedas web usando Tavily API"""
    
    def __init__(self):
        super().__init__(
            name="tavily_search",
            description="Búsqueda web REAL usando Tavily API - Resultados actualizados y relevantes"
        )
        self.api_key = os.environ.get('TAVILY_API_KEY', '')
        self.base_url = "https://api.tavily.com"
    
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="query",
                param_type="string",
                required=True,
                description="Consulta de búsqueda"
            ),
            ParameterDefinition(
                name="num_results",
                param_type="integer",
                required=False,
                description="Número de resultados a retornar",
                default=5
            ),
            ParameterDefinition(
                name="search_depth",
                param_type="string",
                required=False,
                description="Profundidad de búsqueda (basic, advanced)",
                default="basic"
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        """Ejecutar búsqueda REAL usando Tavily API"""
        if not self.api_key:
            return ToolExecutionResult(
                success=False,
                error='TAVILY_API_KEY no está configurada en las variables de entorno'
            )
        
        query = parameters.get('query', '')
        num_results = parameters.get('num_results', 5)
        search_depth = parameters.get('search_depth', 'basic')
        
        # Preparar payload para la API
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "include_answer": True,
            "include_raw_content": False,
            "max_results": num_results
        }
        
        try:
            # Hacer petición a Tavily API
            response = requests.post(
                f"{self.base_url}/search",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Procesar resultados
                results = []
                if 'results' in data:
                    for item in data['results']:
                        result_item = {
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'content': item.get('content', ''),
                            'score': item.get('score', 0),
                            'published_date': item.get('published_date', '')
                        }
                        results.append(result_item)
                
                return ToolExecutionResult(
                    success=True,
                    data={
                        'query': query,
                        'answer': data.get('answer', ''),
                        'results_count': len(results),
                        'results': results,
                        'search_results': results,  # Para compatibilidad con el sistema
                        'search_depth': search_depth
                    }
                )
            else:
                return ToolExecutionResult(
                    success=False,
                    error=f'Error en Tavily API: {response.status_code} - {response.text}'
                )
                
        except requests.exceptions.Timeout:
            return ToolExecutionResult(
                success=False,
                error='Timeout en petición a Tavily API'
            )
        except requests.exceptions.RequestException as e:
            return ToolExecutionResult(
                success=False,
                error=f'Error de conexión con Tavily API: {str(e)}'
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f'Error inesperado en Tavily search: {str(e)}'
            )

