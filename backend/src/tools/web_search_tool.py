"""
Herramienta de búsqueda web - Busca información en internet
"""

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import time
from typing import Dict, Any, List
from urllib.parse import urljoin, urlparse

# CARGAR VARIABLES DE ENTORNO
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

class WebSearchTool:
    def __init__(self):
        self.name = "web_search"
        self.description = "Busca información en internet y extrae contenido de páginas web"
        self.parameters = [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Términos de búsqueda"
            },
            {
                "name": "action",
                "type": "string",
                "required": False,
                "description": "Acción a realizar: 'search' o 'extract'",
                "default": "search"
            },
            {
                "name": "url",
                "type": "string",
                "required": False,
                "description": "URL para extraer contenido (solo para action='extract')"
            },
            {
                "name": "max_results",
                "type": "integer",
                "required": False,
                "description": "Número máximo de resultados",
                "default": 5
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
        
        action = parameters.get('action', 'search')
        
        if action == 'search':
            if 'query' not in parameters:
                return {'valid': False, 'error': 'query parameter is required for search'}
            if not isinstance(parameters['query'], str) or not parameters['query'].strip():
                return {'valid': False, 'error': 'query must be a non-empty string'}
        
        elif action == 'extract':
            if 'url' not in parameters:
                return {'valid': False, 'error': 'url parameter is required for extract'}
            if not isinstance(parameters['url'], str) or not parameters['url'].strip():
                return {'valid': False, 'error': 'url must be a non-empty string'}
        
        else:
            return {'valid': False, 'error': 'action must be either "search" or "extract"'}
        
        return {'valid': True}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar búsqueda web o extracción de contenido"""
        if config is None:
            config = {}
        
        action = parameters.get('action', 'search')
        
        try:
            if action == 'search':
                return self._search_web(parameters, config)
            elif action == 'extract':
                return self._extract_content(parameters, config)
            else:
                return {'error': 'Invalid action specified'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _search_web(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Realizar búsqueda web"""
        query = parameters['query'].strip()
        max_results = min(parameters.get('max_results', 5), config.get('max_results', 10))
        
        try:
            # Usar DuckDuckGo para búsqueda
            ddgs = DDGS()
            results = []
            
            search_results = ddgs.text(query, max_results=max_results)
            for result in search_results:
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', ''),
                    'source': 'duckduckgo'
                })
            
            return {
                'query': query,
                'results': results,
                'count': len(results),
                'success': True
            }
            
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'success': False
            }
    
    def _extract_content(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer contenido de una URL"""
        url = parameters['url'].strip()
        timeout = config.get('timeout', 15)
        
        try:
            # Validar URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {'error': 'Invalid URL format'}
            
            # Realizar petición HTTP
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Extraer contenido con BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remover scripts y estilos
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extraer texto principal
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ''
            
            # Buscar contenido principal
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main_content:
                content = main_content.get_text(separator='\n', strip=True)
            else:
                content = soup.get_text(separator='\n', strip=True)
            
            # Limpiar contenido
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            clean_content = '\n'.join(lines)
            
            # Limitar longitud
            if len(clean_content) > 5000:
                clean_content = clean_content[:5000] + '...'
            
            return {
                'url': url,
                'title': title_text,
                'content': clean_content,
                'length': len(clean_content),
                'success': True
            }
            
        except requests.RequestException as e:
            return {
                'url': url,
                'error': f'HTTP error: {str(e)}',
                'success': False
            }
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'success': False
            }