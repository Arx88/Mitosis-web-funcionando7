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
        """Ejecutar búsqueda usando Tavily API"""
        if not self.api_key:
            return self._create_error_result('TAVILY_API_KEY no está configurada en las variables de entorno')
        
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
                
                return self._create_success_result({
                    'query': query,
                    'answer': data.get('answer', ''),
                    'results_count': len(results),
                    'results': results,
                    'search_depth': search_depth
                })
            else:
                return self._create_error_result(f'Error en Tavily API: {response.status_code} - {response.text}')
                
        except requests.exceptions.Timeout:
            return self._create_error_result('Timeout en petición a Tavily API')
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f'Error de conexión con Tavily API: {str(e)}')
        except Exception as e:
            return self._create_error_result(f'Error inesperado en Tavily search: {str(e)}')

    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros para Tavily"""
        if not self.api_key:
            return {'valid': False, 'error': 'TAVILY_API_KEY no está configurada'}
        
        if not parameters.get('query'):
            return {'valid': False, 'error': 'Parámetro "query" es requerido'}
        
        return {'valid': True}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar búsqueda usando Tavily API"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'TAVILY_API_KEY no está configurada en las variables de entorno',
                    'tool_name': 'tavily_search',
                    'results': []
                }
            
            query = parameters.get('query', '')
            num_results = parameters.get('num_results', 5)
            search_depth = parameters.get('search_depth', 'basic')
            include_answer = parameters.get('include_answer', True)
            include_raw_content = parameters.get('include_raw_content', False)
            
            # Preparar payload para la API
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "include_answer": include_answer,
                "include_raw_content": include_raw_content,
                "max_results": num_results
            }
            
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
                
                return {
                    'success': True,
                    'tool_name': 'tavily_search',
                    'query': query,
                    'answer': data.get('answer', '') if include_answer else '',
                    'results_count': len(results),
                    'results': results,
                    'search_depth': search_depth
                }
            else:
                return {
                    'success': False,
                    'error': f'Error en Tavily API: {response.status_code} - {response.text}',
                    'tool_name': 'tavily_search',
                    'results': []
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout en petición a Tavily API',
                'tool_name': 'tavily_search',
                'results': []
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Error de conexión con Tavily API: {str(e)}',
                'tool_name': 'tavily_search',
                'results': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error inesperado en Tavily search: {str(e)}',
                'tool_name': 'tavily_search',
                'results': []
            }