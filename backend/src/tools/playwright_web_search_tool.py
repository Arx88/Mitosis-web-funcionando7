"""
Herramienta de búsqueda web usando Playwright - Sin rate limits
Usa un navegador real para hacer búsquedas y evitar bloqueos
"""

import os
import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime
import re
import json

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

@register_tool
class PlaywrightWebSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="playwright_web_search",
            description="Busca información en internet usando un navegador real (Playwright) - Sin rate limits"
        )
        self.playwright_available = PLAYWRIGHT_AVAILABLE
    
    def _define_parameters(self) -> List[ParameterDefinition]:
        """Definir parámetros específicos de PlaywrightWebSearch"""
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
                name="search_engine", 
                param_type="string",
                required=False,
                description="Motor de búsqueda: SOLO 'bing' (DuckDuckGo eliminado)",
                default="bing",
                choices=["bing"]
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
                description="Extraer contenido de los primeros resultados",
                default=True
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar búsqueda web con Playwright"""
        if config is None:
            config = {}
        
        if not self.playwright_available:
            return {'error': 'Playwright not available', 'success': False}
        
        query = parameters['query'].strip()
        search_engine = parameters.get('search_engine', 'bing').lower()  # Cambiar default a bing
        max_results = min(parameters.get('max_results', 8), config.get('max_results', 15))
        extract_content = parameters.get('extract_content', True)
        
        try:
            # Ejecutar búsqueda usando asyncio con event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self._search_with_playwright(query, search_engine, max_results, extract_content)
                )
                return result
            finally:
                loop.close()
                
        except Exception as e:
            return {
                'query': query,
                'search_engine': search_engine,
                'error': str(e),
                'success': False
            }
    
    async def _search_with_playwright(self, query: str, search_engine: str, max_results: int, extract_content: bool) -> Dict[str, Any]:
        """Realizar búsqueda usando Playwright"""
        async with async_playwright() as p:
            # Lanzar navegador en modo headless
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            try:
                # Crear contexto con user agent real
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                # Crear página
                page = await context.new_page()
                page.set_default_timeout(30000)  # 30 segundos
                
                # Construir URL de búsqueda según el motor
                search_url = self._build_search_url(query, search_engine)
                
                print(f"🔍 Buscando en {search_engine}: {query}")
                print(f"🌐 URL: {search_url}")
                
                # Navegar a la página de resultados
                await page.goto(search_url, wait_until='networkidle')
                
                # Esperar un poco para que cargue completamente
                await page.wait_for_timeout(2000)
                
                # Extraer resultados según el motor de búsqueda
                results = await self._extract_search_results(page, search_engine, max_results)
                
                # Extraer contenido de los primeros resultados si se solicita
                if extract_content and results:
                    print(f"📄 Extrayendo contenido de {min(3, len(results))} primeros resultados...")
                    for i, result in enumerate(results[:3]):  # Solo primeros 3 para evitar timeout
                        try:
                            content = await self._extract_page_content(page, result['url'])
                            result['content'] = content
                            result['content_extracted'] = True
                            print(f"   ✅ Contenido extraído de: {result['title'][:50]}...")
                        except Exception as e:
                            print(f"   ⚠️ Error extrayendo contenido de {result['url']}: {str(e)}")
                            result['content'] = ''
                            result['content_extracted'] = False
                
                return {
                    'query': query,
                    'search_engine': search_engine,
                    'search_url': search_url,
                    'results': results,
                    'count': len(results),
                    'results_count': len(results),  # 🔥 FIX: Agregar results_count para compatibility
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'search_results': results  # Para compatibilidad con otras herramientas
                }
                
            finally:
                await browser.close()
    
    def _build_search_url(self, query: str, search_engine: str) -> str:
        """Construir URL de búsqueda según el motor"""
        # Limpiar y codificar query
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        
        # FORZAR SOLO BING - ELIMINAR DUCKDUCKGO
        search_engine = "bing"  # SOLO BING PERMITIDO
        
        if search_engine == 'google':
            return f"https://www.google.com/search?q={encoded_query}"
        elif search_engine == 'bing':
            return f"https://www.bing.com/search?q={encoded_query}&count=20"
        else:
            # DEFAULT: USAR BING
            return f"https://www.bing.com/search?q={encoded_query}&count=20"
    
    async def _extract_search_results(self, page, search_engine: str, max_results: int) -> List[Dict[str, Any]]:
        """Extraer resultados de búsqueda - SOLO BING SOPORTADO"""
        # FORZAR SOLO BING - ELIMINAR DUCKDUCKGO
        search_engine = "bing"  # SOLO BING PERMITIDO
        
        results = []
        
        try:
            if search_engine == 'google':
                results = await self._extract_google_results(page, max_results)
            elif search_engine == 'bing':
                results = await self._extract_bing_results(page, max_results)
            else:
                # DEFAULT: USAR BING
                results = await self._extract_bing_results(page, max_results)
                
        except Exception as e:
            print(f"❌ Error extrayendo resultados de {search_engine}: {str(e)}")
        
        return results[:max_results]
    
    async def _extract_google_results(self, page, max_results: int) -> List[Dict[str, Any]]:
        """Extraer resultados de Google"""
        results = []
        
        # Selectores para resultados de Google
        result_selector = 'div.g, div[data-ved]'
        
        # Obtener elementos de resultados
        result_elements = await page.query_selector_all(result_selector)
        
        for element in result_elements[:max_results]:
            try:
                # Extraer título
                title_element = await element.query_selector('h3')
                title = await title_element.text_content() if title_element else ''
                
                # Extraer URL
                link_element = await element.query_selector('a')
                url = await link_element.get_attribute('href') if link_element else ''
                
                # Extraer snippet/descripción
                snippet_element = await element.query_selector('.VwiC3b, .s3v9rd, .st')
                snippet = await snippet_element.text_content() if snippet_element else ''
                
                if title and url and url.startswith('http'):
                    results.append({
                        'title': title.strip(),
                        'url': url.strip(),
                        'snippet': snippet.strip(),
                        'source': 'google'
                    })
                    
            except Exception as e:
                continue
        
        return results
    
    async def _extract_bing_results(self, page, max_results: int) -> List[Dict[str, Any]]:
        """Extraer resultados de Bing"""
        results = []
        
        # Selectores actualizados para resultados de Bing
        result_selector = 'li.b_algo'
        
        # Obtener elementos de resultados
        result_elements = await page.query_selector_all(result_selector)
        print(f"🔍 Encontrados {len(result_elements)} elementos de resultado en Bing")
        
        for element in result_elements[:max_results]:
            try:
                # Extraer título
                title_element = await element.query_selector('h2')
                title = await title_element.text_content() if title_element else ''
                
                # Extraer URL del enlace en el título
                link_element = await element.query_selector('h2 a')
                url = await link_element.get_attribute('href') if link_element else ''
                
                # Extraer snippet
                snippet_element = await element.query_selector('.b_caption')
                snippet = await snippet_element.text_content() if snippet_element else ''
                
                if title and url and url.startswith('http'):
                    result_data = {
                        'title': title.strip(),
                        'url': url.strip(),
                        'snippet': snippet.strip(),
                        'source': 'bing'
                    }
                    results.append(result_data)
                    print(f"   ✅ Resultado: {title.strip()[:50]}...")
                    
            except Exception as e:
                print(f"   ⚠️ Error procesando resultado: {str(e)}")
                continue
        
        print(f"✅ Total {len(results)} resultados válidos extraídos de Bing")
        return results
    
    # MÉTODO DUCKDUCKGO ELIMINADO - SOLO BING SOPORTADO
    
    async def _extract_page_content(self, page, url: str) -> str:
        """Extraer contenido de una página específica"""
        try:
            # Navegar a la página
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            
            # Esperar un poco para que cargue
            await page.wait_for_timeout(1000)
            
            # Extraer contenido principal
            content = await page.evaluate('''
                () => {
                    // Remover elementos innecesarios
                    const elementsToRemove = ['script', 'style', 'nav', 'header', 'footer', 'aside', '.ad', '.advertisement'];
                    elementsToRemove.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => el.remove());
                    });
                    
                    // Buscar contenido principal
                    const mainSelectors = ['main', 'article', '.content', '.post-content', '.entry-content', '#content'];
                    
                    for (let selector of mainSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            return element.innerText.trim();
                        }
                    }
                    
                    // Fallback al body
                    return document.body.innerText.trim();
                }
            ''')
            
            # Limpiar y limitar contenido
            if content:
                # Remover líneas en blanco excesivas
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                clean_content = '\n'.join(lines)
                
                # Limitar tamaño
                if len(clean_content) > 3000:
                    clean_content = clean_content[:3000] + '...'
                
                return clean_content
            else:
                return ''
                
        except Exception as e:
            print(f"   ⚠️ Error extrayendo contenido de {url}: {str(e)}")
            return ''
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información adicional de la herramienta"""
        return {
            'category': 'web_search_advanced',
            'version': '1.0.0',
            'advantages': [
                'No rate limits - usa navegador real',
                'Múltiples motores de búsqueda',
                'Extracción de contenido real',
                'JavaScript support completo',
                'User agent real',
                'Resultados más actualizados'
            ],
            'supported_engines': ['bing'],  # SOLO BING SOPORTADO
            'playwright_required': True,
            'playwright_available': self.playwright_available
        }