"""
Herramienta de búsqueda web - SOLO Playwright + Selenium + Bing
ELIMINA COMPLETAMENTE DuckDuckGo - USA SOLO BING CON PLAYWRIGHT
"""

import os
import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime
import re
import json

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# CARGAR VARIABLES DE ENTORNO
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

class WebSearchTool:
    def __init__(self):
        self.name = "web_search"
        self.description = "Busca información en internet usando Playwright + Selenium + Bing ÚNICAMENTE"
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        
        self.parameters = [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Términos de búsqueda"
            },
            {
                "name": "max_results",
                "type": "integer",
                "required": False,
                "description": "Número máximo de resultados",
                "default": 8
            },
            {
                "name": "extract_content",
                "type": "boolean",
                "required": False,
                "description": "Extraer contenido completo de los primeros resultados",
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
        
        return {'valid': True}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar búsqueda web usando Playwright + Bing"""
        if config is None:
            config = {}
        
        try:
            if not self.playwright_available:
                return {
                    'error': 'Playwright no está disponible. Instalar con: pip install playwright',
                    'success': False
                }
            
            # Ejecutar búsqueda asíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._search_with_playwright(parameters, config))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            return {
                'error': f'Error en búsqueda: {str(e)}',
                'success': False
            }
    
    async def _search_with_playwright(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Realizar búsqueda usando Playwright + Bing"""
        query = parameters['query'].strip()
        max_results = min(parameters.get('max_results', 8), config.get('max_results', 15))
        extract_content = parameters.get('extract_content', True)
        
        async with async_playwright() as p:
            try:
                # Lanzar navegador
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
                
                # Buscar en Bing
                bing_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
                await page.goto(bing_url, timeout=30000)
                
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
                                'title': title.strip(),
                                'url': url.strip(),
                                'snippet': snippet.strip(),
                                'source': 'bing',
                                'rank': i + 1
                            }
                            
                            # Extraer contenido si se solicita
                            if extract_content and i < 3:  # Solo primeros 3 resultados
                                content = await self._extract_page_content(context, url)
                                if content:
                                    result_data['content'] = content
                            
                            results.append(result_data)
                            
                    except Exception as e:
                        print(f"Error procesando resultado {i}: {e}")
                        continue
                
                await browser.close()
                
                return {
                    'query': query,
                    'results': results,
                    'count': len(results),
                    'source': 'bing_playwright',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }
                
            except Exception as e:
                if 'browser' in locals():
                    await browser.close()
                
                return {
                    'query': query,
                    'error': f'Error en Playwright: {str(e)}',
                    'success': False
                }
    
    async def _extract_page_content(self, context, url: str) -> str:
        """Extraer contenido de una página específica"""
        try:
            page = await context.new_page()
            await page.goto(url, timeout=15000)
            
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
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                clean_content = '\n'.join(lines)
                
                # Limitar longitud
                if len(clean_content) > 3000:
                    clean_content = clean_content[:3000] + '...'
                
                return clean_content
            
            return ""
            
        except Exception as e:
            print(f"Error extrayendo contenido de {url}: {e}")
            return ""