"""
Herramienta REAL de búsqueda web usando Playwright
Automatización REAL con navegador para hacer búsquedas web potentes
"""

import asyncio
import re
from typing import Dict, List, Any
from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

@register_tool
class PlaywrightWebSearchTool(BaseTool):
    """Herramienta REAL de búsqueda web usando Playwright con navegador real"""
    
    def __init__(self):
        super().__init__(
            name="playwright_web_search",
            description="Búsqueda web REAL usando navegador automatizado Playwright - Resultados potentes y actualizados"
        )
        self.playwright_available = PLAYWRIGHT_AVAILABLE
    
    def _define_parameters(self) -> List[ParameterDefinition]:
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
                description="Motor de búsqueda (google, bing, duckduckgo)",
                default="google"
            ),
            ParameterDefinition(
                name="extract_content",
                param_type="boolean",
                required=False,
                description="Extraer contenido de páginas",
                default=True
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        """Ejecutar búsqueda REAL usando Playwright"""
        if not self.playwright_available:
            return ToolExecutionResult(
                success=False,
                error='Playwright no está instalado. Instalar con: pip install playwright && playwright install'
            )
        
        query = parameters.get('query', '')
        max_results = parameters.get('max_results', 5)
        search_engine = parameters.get('search_engine', 'google')
        extract_content = parameters.get('extract_content', True)
        
        try:
            # Ejecutar búsqueda con Playwright
            results = asyncio.run(self._search_with_playwright(
                query, search_engine, max_results, extract_content
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    'query': query,
                    'search_engine': search_engine,
                    'results_count': len(results),
                    'results': results,
                    'search_results': results,  # Para compatibilidad
                    'extract_content': extract_content
                }
            )
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f'Error en búsqueda Playwright: {str(e)}'
            )
    
    async def _search_with_playwright(self, query: str, search_engine: str, 
                                    max_results: int, extract_content: bool) -> List[Dict[str, Any]]:
        """Búsqueda REAL con Playwright"""
        search_urls = {
            'google': f'https://www.google.com/search?q={query}',
            'bing': f'https://www.bing.com/search?q={query}',
            'duckduckgo': f'https://duckduckgo.com/?q={query}'
        }
        
        search_url = search_urls.get(search_engine, search_urls['google'])
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            try:
                page = await browser.new_page()
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # Navegar a la página de búsqueda
                await page.goto(search_url, wait_until='networkidle')
                await page.wait_for_timeout(2000)  # Wait for results to load
                
                # Extraer resultados según el motor de búsqueda
                if search_engine == 'google':
                    results = await self._extract_google_results(page, max_results, extract_content)
                elif search_engine == 'bing':
                    results = await self._extract_bing_results(page, max_results, extract_content)
                elif search_engine == 'duckduckgo':
                    results = await self._extract_duckduckgo_results(page, max_results, extract_content)
                
            finally:
                await browser.close()
        
        return results
    
    async def _extract_google_results(self, page, max_results: int, extract_content: bool) -> List[Dict[str, Any]]:
        """Extraer resultados REALES de Google"""
        results = []
        
        # Selectores para resultados de Google
        result_elements = await page.query_selector_all('div.g, div[data-ved]')
        
        for i, element in enumerate(result_elements[:max_results]):
            try:
                # Extraer título
                title_elem = await element.query_selector('h3, [role="heading"]')
                title = await title_elem.inner_text() if title_elem else f'Resultado {i+1}'
                
                # Extraer URL
                link_elem = await element.query_selector('a')
                url = await link_elem.get_attribute('href') if link_elem else ''
                
                # Extraer snippet
                snippet_elem = await element.query_selector('span, div.VwiC3b, div.s3v9rd')
                snippet = await snippet_elem.inner_text() if snippet_elem else ''
                
                if title and url:
                    result_item = {
                        'title': title.strip(),
                        'url': url,
                        'snippet': snippet.strip(),
                        'source': 'google'
                    }
                    
                    # Extraer contenido si se solicita
                    if extract_content and url.startswith('http'):
                        content = await self._extract_page_content(page.context, url)
                        result_item['content'] = content
                    
                    results.append(result_item)
                    
            except Exception:
                continue  # Skip problematic results
        
        return results
    
    async def _extract_bing_results(self, page, max_results: int, extract_content: bool) -> List[Dict[str, Any]]:
        """Extraer resultados REALES de Bing"""
        results = []
        
        result_elements = await page.query_selector_all('li.b_algo')
        
        for i, element in enumerate(result_elements[:max_results]):
            try:
                # Título
                title_elem = await element.query_selector('h2 a')
                title = await title_elem.inner_text() if title_elem else f'Resultado {i+1}'
                
                # URL
                url = await title_elem.get_attribute('href') if title_elem else ''
                
                # Snippet
                snippet_elem = await element.query_selector('p, .b_caption p')
                snippet = await snippet_elem.inner_text() if snippet_elem else ''
                
                if title and url:
                    result_item = {
                        'title': title.strip(),
                        'url': url,
                        'snippet': snippet.strip(),
                        'source': 'bing'
                    }
                    
                    if extract_content and url.startswith('http'):
                        content = await self._extract_page_content(page.context, url)
                        result_item['content'] = content
                    
                    results.append(result_item)
                    
            except Exception:
                continue
        
        return results
    
    async def _extract_duckduckgo_results(self, page, max_results: int, extract_content: bool) -> List[Dict[str, Any]]:
        """Extraer resultados REALES de DuckDuckGo"""
        results = []
        
        result_elements = await page.query_selector_all('article, div.result')
        
        for i, element in enumerate(result_elements[:max_results]):
            try:
                # Título
                title_elem = await element.query_selector('h2 a, a.result__a')
                title = await title_elem.inner_text() if title_elem else f'Resultado {i+1}'
                
                # URL
                url = await title_elem.get_attribute('href') if title_elem else ''
                
                # Snippet
                snippet_elem = await element.query_selector('.result__snippet, a.result__snippet')
                snippet = await snippet_elem.inner_text() if snippet_elem else ''
                
                if title and url:
                    result_item = {
                        'title': title.strip(),
                        'url': url,
                        'snippet': snippet.strip(),
                        'source': 'duckduckgo'
                    }
                    
                    if extract_content and url.startswith('http'):
                        content = await self._extract_page_content(page.context, url)
                        result_item['content'] = content
                    
                    results.append(result_item)
                    
            except Exception:
                continue
        
        return results
    
    async def _extract_page_content(self, context, url: str) -> str:
        """Extraer contenido REAL de una página"""
        try:
            page = await context.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=10000)
            
            # Extraer texto principal
            content = await page.evaluate('''
                () => {
                    // Remover scripts, styles y elementos no deseados
                    const unwanted = document.querySelectorAll('script, style, nav, header, footer, aside, .ads');
                    unwanted.forEach(el => el.remove());
                    
                    // Obtener texto principal
                    const main = document.querySelector('main, article, .content, #content') || document.body;
                    return main.innerText.slice(0, 2000); // Limit to 2000 chars
                }
            ''')
            
            await page.close()
            return content.strip() if content else ''
            
        except Exception:
            return ''
