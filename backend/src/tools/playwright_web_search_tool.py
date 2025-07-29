"""
Wrapper para PlaywrightTool que actúa como playwright_web_search
Esto mantiene compatibilidad con el código existente del agente
"""

from typing import Dict, List, Any
from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult
from .playwright_tool import PlaywrightTool

class PlaywrightWebSearchTool(BaseTool):
    """Wrapper para PlaywrightTool que actúa como playwright_web_search"""
    
    def __init__(self):
        super().__init__()
        self._playwright_tool = PlaywrightTool()
    
    def get_name(self) -> str:
        return "playwright_web_search"
    
    def get_description(self) -> str:
        return "Herramienta de búsqueda web automatizada con Playwright para scraping y navegación"
    
    def get_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="query",
                param_type="string",
                required=True,
                description="Consulta de búsqueda"
            ),
            ParameterDefinition(
                name="max_results",
                param_type="integer",
                required=False,
                description="Número máximo de resultados",
                default=5
            ),
            ParameterDefinition(
                name="search_engine",
                param_type="string",
                required=False,
                description="Motor de búsqueda a usar (google, bing, duckduckgo)",
                default="google"
            ),
            ParameterDefinition(
                name="extract_content",
                param_type="boolean",
                required=False,
                description="Si extraer contenido de las páginas",
                default=True
            )
        ]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros para búsqueda web"""
        if not parameters.get('query'):
            return {'valid': False, 'error': 'Parámetro "query" es requerido'}
        
        return {'valid': True}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar búsqueda web usando Playwright"""
        try:
            query = parameters.get('query', '')
            max_results = parameters.get('max_results', 5)
            search_engine = parameters.get('search_engine', 'google')
            extract_content = parameters.get('extract_content', True)
            
            # Construir URL de búsqueda
            search_urls = {
                'google': f'https://www.google.com/search?q={query}',
                'bing': f'https://www.bing.com/search?q={query}',
                'duckduckgo': f'https://duckduckgo.com/?q={query}'
            }
            
            search_url = search_urls.get(search_engine, search_urls['google'])
            
            # Usar PlaywrightTool para navegar y extraer resultados
            nav_result = self._playwright_tool.execute({
                'action': 'navigate',
                'url': search_url
            }, config)
            
            if not nav_result.get('success', False):
                return {
                    'success': False,
                    'error': f'Error navegando a {search_engine}: {nav_result.get("error", "")}',
                    'tool_name': 'playwright_web_search',
                    'results': []
                }
            
            # Intentar extraer resultados de búsqueda
            scrape_result = self._playwright_tool.execute({
                'action': 'scrape_links'
            }, config)
            
            results = []
            if scrape_result.get('success', False) and scrape_result.get('links'):
                links = scrape_result.get('links', [])[:max_results]
                
                for i, link in enumerate(links):
                    result_item = {
                        'title': link.get('text', f'Resultado {i+1}'),
                        'url': link.get('url', ''),
                        'snippet': f'Resultado de búsqueda para: {query}'
                    }
                    
                    # Extraer contenido si se solicita
                    if extract_content and link.get('url'):
                        try:
                            content_result = self._playwright_tool.execute({
                                'action': 'navigate',
                                'url': link['url']
                            }, config)
                            
                            if content_result.get('success', False):
                                text_result = self._playwright_tool.execute({
                                    'action': 'scrape_text'
                                }, config)
                                
                                if text_result.get('success', False):
                                    result_item['content'] = text_result.get('text', '')[:1000]  # Limitar a 1000 chars
                        except Exception:
                            pass  # Continuar sin contenido si falla
                    
                    results.append(result_item)
            
            return {
                'success': True,
                'tool_name': 'playwright_web_search',
                'query': query,
                'search_engine': search_engine,
                'results_count': len(results),
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en búsqueda web: {str(e)}',
                'tool_name': 'playwright_web_search',
                'results': []
            }