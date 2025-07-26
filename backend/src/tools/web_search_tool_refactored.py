"""
Herramienta de búsqueda web refactorizada - Usa BaseTool
Eliminada duplicación de código y mejorada estructura
"""

import os
import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime
import re

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# CARGAR VARIABLES DE ENTORNO
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

@register_tool
class WebSearchTool(BaseTool):
    """
    Herramienta de búsqueda web usando Playwright + Bing
    Refactorizada para usar BaseTool y eliminar duplicación
    """
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Busca información en internet usando Playwright + Selenium + Bing ÚNICAMENTE"
        )
        self.playwright_available = PLAYWRIGHT_AVAILABLE
    
    def _define_parameters(self) -> List[ParameterDefinition]:
        """Definir parámetros específicos de búsqueda web"""
        return [
            ParameterDefinition(
                name="query",
                param_type="string",
                required=True,
                description="Términos de búsqueda",
                min_value=1,
                max_value=200
            ),
            ParameterDefinition(
                name="max_results",
                param_type="integer",
                required=False,
                description="Número máximo de resultados",
                default=8,
                min_value=1,
                max_value=20
            ),
            ParameterDefinition(
                name="extract_content",
                param_type="boolean",
                required=False,
                description="Extraer contenido completo de los primeros resultados",
                default=True
            ),
            ParameterDefinition(
                name="timeout",
                param_type="integer",
                required=False,
                description="Timeout en segundos para cada página",
                default=30,
                min_value=5,
                max_value=60
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        """Ejecutar búsqueda web usando Playwright + Bing"""
        
        # Verificar disponibilidad de Playwright
        if not self.playwright_available:
            return self._create_error_result(
                'Playwright no está disponible. Instalar con: pip install playwright && playwright install'
            )
        
        try:
            # Ejecutar búsqueda asíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._search_with_playwright(parameters, config))
                
                if result.success:
                    return result
                else:
                    return result
                    
            finally:
                loop.close()
                
        except Exception as e:
            return self._create_error_result(f'Error en configuración de búsqueda: {str(e)}')
    
    async def _search_with_playwright(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        """Realizar búsqueda usando Playwright + Bing"""
        query = parameters['query'].strip()
        max_results = min(parameters.get('max_results', 8), 20)
        extract_content = parameters.get('extract_content', True)
        timeout = parameters.get('timeout', 30) * 1000  # Convertir a ms
        
        browser = None
        
        try:
            async with async_playwright() as p:
                # Configurar navegador
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-images',
                        '--disable-javascript'
                    ]
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Realizar búsqueda en Bing
                search_results = await self._perform_bing_search(page, query, max_results, timeout)
                
                if not search_results['success']:
                    await browser.close()
                    return self._create_error_result(search_results['error'])
                
                results = search_results['results']
                
                # Extraer contenido si se solicita
                if extract_content and results:
                    content_results = await self._extract_content_from_results(
                        context, results[:3], timeout  # Solo primeros 3 resultados
                    )
                    
                    # Combinar resultados con contenido
                    for i, result in enumerate(results[:3]):
                        if i < len(content_results) and content_results[i]['content']:
                            result['content'] = content_results[i]['content']
                
                await browser.close()
                
                # Preparar datos de resultado
                result_data = {
                    'query': query,
                    'results': results,
                    'count': len(results),
                    'source': 'bing_playwright',
                    'timestamp': datetime.now().isoformat(),
                    'search_url': f"https://www.bing.com/search?q={query.replace(' ', '+')}"
                }
                
                return self._create_success_result(result_data)
                
        except asyncio.TimeoutError:
            if browser:
                await browser.close()
            return self._create_error_result(f'Búsqueda cancelada por timeout ({timeout/1000}s)')
        
        except Exception as e:
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            return self._create_error_result(f'Error durante la búsqueda: {str(e)}')
    
    async def _perform_bing_search(self, page, query: str, max_results: int, timeout: int) -> Dict[str, Any]:
        """Realizar búsqueda específica en Bing"""
        try:
            # Navegar a Bing
            bing_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
            await page.goto(bing_url, timeout=timeout)
            
            # Esperar a que carguen los resultados
            await page.wait_for_selector('.b_algo', timeout=10000)
            
            # Extraer resultados de búsqueda
            results = []
            search_results = await page.query_selector_all('.b_algo')
            
            for i, result_elem in enumerate(search_results[:max_results]):
                try:
                    # Extraer título
                    title_elem = await result_elem.query_selector('h2 a')
                    title = await title_elem.inner_text() if title_elem else 'Sin título'
                    
                    # Extraer URL
                    url = await title_elem.get_attribute('href') if title_elem else ''
                    
                    # Extraer snippet
                    snippet_elem = await result_elem.query_selector('.b_caption p, .b_caption .b_descript')
                    snippet = await snippet_elem.inner_text() if snippet_elem else ''
                    
                    if url and title:
                        result_data = {
                            'title': self._clean_text(title),
                            'url': url.strip(),
                            'snippet': self._clean_text(snippet),
                            'source': 'bing',
                            'rank': i + 1
                        }
                        
                        results.append(result_data)
                        
                except Exception as e:
                    self._logger.warning(f"Error procesando resultado {i}: {e}")
                    continue
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            return {'success': False, 'error': f'Error en búsqueda Bing: {str(e)}'}
    
    async def _extract_content_from_results(self, context, results: List[Dict], timeout: int) -> List[Dict]:
        """Extraer contenido de múltiples páginas"""
        content_results = []
        
        for result in results:
            url = result.get('url', '')
            if not url:
                content_results.append({'content': '', 'error': 'No URL provided'})
                continue
            
            content_data = await self._extract_page_content(context, url, timeout)
            content_results.append(content_data)
        
        return content_results
    
    async def _extract_page_content(self, context, url: str, timeout: int) -> Dict[str, Any]:
        """Extraer contenido de una página específica"""
        page = None
        try:
            page = await context.new_page()
            await page.goto(url, timeout=timeout)
            
            # Remover elementos no deseados
            await page.evaluate("""
                const elementsToRemove = document.querySelectorAll('script, style, nav, footer, header, .ads, .advertisement, .sidebar');
                elementsToRemove.forEach(el => el.remove());
            """)
            
            # Extraer contenido principal
            content_selectors = [
                'main',
                'article', 
                '.content',
                '.main-content',
                '.post-content',
                '.entry-content',
                'body'
            ]
            
            content = ""
            for selector in content_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        content = await element.inner_text()
                        if len(content.strip()) > 100:
                            break
                except:
                    continue
            
            await page.close()
            
            # Limpiar y limitar contenido
            if content:
                clean_content = self._clean_and_limit_content(content)
                return {'content': clean_content, 'extracted': True}
            else:
                return {'content': '', 'extracted': False, 'error': 'No content found'}
            
        except Exception as e:
            if page:
                try:
                    await page.close()
                except:
                    pass
            return {'content': '', 'extracted': False, 'error': f'Error extracting from {url}: {str(e)}'}
    
    def _clean_text(self, text: str) -> str:
        """Limpiar texto eliminando caracteres especiales y espacios extra"""
        if not text:
            return ""
        
        # Eliminar caracteres de control y espacios extra
        cleaned = re.sub(r'\s+', ' ', text.strip())
        # Eliminar caracteres no imprimibles
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\t')
        
        return cleaned
    
    def _clean_and_limit_content(self, content: str) -> str:
        """Limpiar y limitar contenido extraído"""
        if not content:
            return ""
        
        # Dividir en líneas y limpiar
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        clean_content = '\n'.join(lines)
        
        # Limitar longitud
        if len(clean_content) > 3000:
            clean_content = clean_content[:3000] + '...\n[Content truncated]'
        
        return clean_content