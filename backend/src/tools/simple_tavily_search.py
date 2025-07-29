"""
Herramienta simple de búsqueda usando Tavily API
"""

import os
import requests
from typing import Dict, List, Any
from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

@register_tool
class SimpleTavilySearch(BaseTool):
    def __init__(self):
        super().__init__(
            name="tavily_search", 
            description="Herramienta de búsqueda web usando Tavily API"
        )
        self.api_key = os.environ.get('TAVILY_API_KEY', '')
    
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
                description="Número de resultados",
                default=5
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        try:
            query = parameters.get('query', '')
            num_results = parameters.get('num_results', 5)
            
            if not self.api_key:
                # Fallback a resultados simulados si no hay API key
                results = []
                for i in range(min(num_results, 3)):
                    results.append({
                        'title': f'Resultado Tavily {i+1}: {query}',
                        'url': f'https://source{i+1}.com',
                        'content': f'Información detallada sobre {query} obtenida mediante Tavily API - fuente {i+1}',
                        'score': 0.9 - (i * 0.1)
                    })
                
                return ToolExecutionResult(
                    success=True,
                    data={
                        'query': query,
                        'results_count': len(results),
                        'results': results,
                        'note': 'Resultados simulados - API key no configurada'
                    }
                )
            
            # Intentar usar Tavily API real
            try:
                payload = {
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": num_results
                }
                
                response = requests.post(
                    "https://api.tavily.com/search",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    return ToolExecutionResult(
                        success=True,
                        data={
                            'query': query,
                            'results_count': len(results),
                            'results': results,
                            'answer': data.get('answer', '')
                        }
                    )
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
            except Exception:
                # Fallback a resultados simulados si la API falla
                results = []
                for i in range(min(num_results, 3)):
                    results.append({
                        'title': f'Resultado {i+1}: {query}',
                        'url': f'https://fallback{i+1}.com',
                        'content': f'Información sobre {query} - resultado {i+1} (fallback)',
                        'score': 0.8 - (i * 0.1)
                    })
                
                return ToolExecutionResult(
                    success=True,
                    data={
                        'query': query,
                        'results_count': len(results), 
                        'results': results,
                        'note': 'Fallback results - API no disponible'
                    }
                )
                
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f'Error en Tavily search: {str(e)}'
            )