"""
Herramienta de búsqueda web básica REAL
Implementa búsqueda real usando scraping directo cuando las APIs fallan
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, Any, List
import re
from urllib.parse import quote, urljoin, urlparse

# CARGAR VARIABLES DE ENTORNO
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

class BasicWebSearchTool:
    """Herramienta de búsqueda web básica usando scraping real"""
    
    def __init__(self):
        self.name = "basic_web_search"
        self.description = "Búsqueda web básica usando scraping real cuando otras APIs fallan"
        self.enabled = True
        self.parameters = [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Término de búsqueda"
            },
            {
                "name": "max_results",
                "type": "integer",
                "required": False,
                "description": "Número máximo de resultados (default: 5)"
            }
        ]
        
        # Headers para parecer un navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta búsqueda web REAL usando scraping"""
        start_time = time.time()
        
        try:
            query = parameters.get('query', '')
            max_results = parameters.get('max_results', 5)
            
            if not query:
                return {
                    'error': 'Query parameter is required',
                    'success': False
                }
            
            print(f"🔍 Ejecutando búsqueda REAL básica: '{query}'")
            
            # Usar múltiples fuentes de búsqueda
            results = []
            
            # Método 1: Buscar en sitios específicos
            specific_searches = [
                f"site:stackoverflow.com {query}",
                f"site:github.com {query}",
                f"site:docs.python.org {query}" if 'python' in query.lower() else f"{query} tutorial",
                f"{query} documentation",
                f"{query} examples"
            ]
            
            for search_term in specific_searches[:max_results]:
                try:
                    result = self._search_real_web(search_term)
                    if result:
                        results.extend(result)
                        if len(results) >= max_results:
                            break
                    
                    # Pausa para evitar rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"⚠️  Error en búsqueda específica '{search_term}': {e}")
                    continue
            
            # Si no hay resultados suficientes, intentar búsqueda general
            if len(results) < max_results:
                try:
                    general_results = self._search_wikipedia(query)
                    results.extend(general_results)
                except Exception as e:
                    print(f"⚠️  Error en Wikipedia: {e}")
            
            # Limpiar y limitar resultados
            unique_results = []
            seen_urls = set()
            
            for result in results:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
                    if len(unique_results) >= max_results:
                        break
            
            execution_time = time.time() - start_time
            
            if unique_results:
                return {
                    'query': query,
                    'results': unique_results,
                    'success': True,
                    'execution_time': execution_time,
                    'tool_name': self.name,
                    'timestamp': time.time(),
                    'method': 'real_scraping',
                    'total_found': len(unique_results)
                }
            else:
                return {
                    'query': query,
                    'results': [],
                    'success': False,
                    'error': 'No se encontraron resultados válidos',
                    'execution_time': execution_time,
                    'tool_name': self.name,
                    'timestamp': time.time()
                }
                
        except Exception as e:
            return {
                'query': parameters.get('query', ''),
                'error': str(e),
                'success': False,
                'execution_time': time.time() - start_time,
                'tool_name': self.name,
                'timestamp': time.time()
            }
    
    def _search_real_web(self, query: str) -> List[Dict[str, Any]]:
        """Búsqueda web real usando requests y scraping"""
        try:
            # Usar Bing como alternativa (menos restrictivo que Google)
            encoded_query = quote(query)
            search_url = f"https://www.bing.com/search?q={encoded_query}"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Parsear resultados de Bing
            for item in soup.find_all('li', class_='b_algo')[:3]:
                try:
                    title_tag = item.find('h2')
                    if not title_tag or not title_tag.find('a'):
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    url = title_tag.find('a').get('href', '')
                    
                    # Extraer snippet
                    snippet_tag = item.find('p') or item.find('div', class_='b_caption')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'bing_scraping'
                        })
                        
                except Exception as e:
                    print(f"⚠️  Error parseando resultado de Bing: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"❌ Error en búsqueda web real: {e}")
            return []
    
    def _search_wikipedia(self, query: str) -> List[Dict[str, Any]]:
        """Buscar en Wikipedia como fuente confiable"""
        try:
            # API de Wikipedia
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(query)}"
            
            response = requests.get(wiki_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                return [{
                    'title': data.get('title', query),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'snippet': data.get('extract', ''),
                    'source': 'wikipedia_api'
                }]
            else:
                return []
                
        except Exception as e:
            print(f"❌ Error en búsqueda de Wikipedia: {e}")
            return []
    
    def is_enabled(self) -> bool:
        """Verifica si la herramienta está habilitada"""
        return self.enabled
    
    def get_info(self) -> Dict[str, Any]:
        """Retorna información sobre la herramienta"""
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'enabled': self.enabled
        }