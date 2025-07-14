"""
Herramienta de búsqueda web usando Tavily API
"""

import os
import requests
from typing import Dict, Any, List
from tavily import TavilyClient

class TavilySearchTool:
    def __init__(self):
        self.name = "tavily_search"
        self.description = "Busca información en internet usando Tavily API - más preciso y actualizado que otras herramientas"
        self.api_key = os.getenv('TAVILY_API_KEY')
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None
        self.parameters = [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Términos de búsqueda"
            },
            {
                "name": "search_depth",
                "type": "string",
                "required": False,
                "description": "Profundidad de búsqueda: 'basic' o 'advanced'",
                "default": "basic"
            },
            {
                "name": "max_results",
                "type": "integer",
                "required": False,
                "description": "Número máximo de resultados",
                "default": 5
            },
            {
                "name": "include_answer",
                "type": "boolean",
                "required": False,
                "description": "Incluir respuesta resumida",
                "default": True
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
        
        if 'query' not in parameters:
            return {'valid': False, 'error': 'query parameter is required'}
        
        if not isinstance(parameters['query'], str) or not parameters['query'].strip():
            return {'valid': False, 'error': 'query must be a non-empty string'}
        
        if not self.api_key:
            return {'valid': False, 'error': 'Tavily API key not configured'}
        
        return {'valid': True}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar búsqueda web con Tavily"""
        if config is None:
            config = {}
        
        # Validar parámetros
        validation = self.validate_parameters(parameters)
        if not validation['valid']:
            return {'error': validation['error'], 'success': False}
        
        query = parameters['query'].strip()
        search_depth = parameters.get('search_depth', 'basic')
        max_results = min(parameters.get('max_results', 5), config.get('max_results', 10))
        include_answer = parameters.get('include_answer', True)
        
        try:
            # Realizar búsqueda con Tavily
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=include_answer
            )
            
            # Formatear resultados
            results = []
            for result in response.get('results', []):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('content', ''),
                    'source': 'tavily',
                    'score': result.get('score', 0)
                })
            
            return {
                'query': query,
                'answer': response.get('answer', '') if include_answer else '',
                'results': results,
                'count': len(results),
                'search_depth': search_depth,
                'success': True
            }
            
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'success': False
            }