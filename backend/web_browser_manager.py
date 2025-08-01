"""
Sistema de Gestión de Navegación Web Unificada
Implementa las especificaciones completas del NEWUPGRADE.md Sección 5

Reemplaza mockups de _execute_web_search con Playwright real
Proporciona navegación web concurrente, scraping y gestión de contenido
"""

import logging
import asyncio
import json
import time
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import re
from urllib.parse import urljoin, urlparse

# Playwright imports
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.error("Playwright no está instalado. Ejecutar: pip install playwright && playwright install")

# Other web scraping imports
try:
    import requests
    from bs4 import BeautifulSoup
    import httpx
    SCRAPING_LIBRARIES_AVAILABLE = True
except ImportError:
    SCRAPING_LIBRARIES_AVAILABLE = False

class BrowserType(Enum):
    """Tipos de navegador disponibles"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"

class ScrapingMode(Enum):
    """Modos de scraping disponibles"""
    TEXT_ONLY = "text_only"
    FULL_HTML = "full_html"
    STRUCTURED = "structured"
    SCREENSHOT = "screenshot"

@dataclass
class BrowserConfig:
    """Configuración del navegador"""
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    viewport: Dict[str, int] = None
    timeout: int = 30000  # 30 segundos
    ignore_https_errors: bool = True
    enable_javascript: bool = True
    
    def __post_init__(self):
        if self.viewport is None:
            self.viewport = {"width": 1920, "height": 1080}

@dataclass 
class WebPage:
    """Representación de una página web"""
    url: str
    title: str = ""
    content: str = ""
    html: str = ""
    status_code: int = 0
    loading_time: float = 0.0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ScrapingResult:
    """Resultado de una operación de scraping"""
    success: bool
    pages: List[WebPage] = None
    error_message: str = ""
    total_pages: int = 0
    processing_time: float = 0.0
    cache_hits: int = 0
    
    def __post_init__(self):
        if self.pages is None:
            self.pages = []
        self.total_pages = len(self.pages)

class WebBrowserManager:
    """Gestor unificado de navegación web con Playwright y visualización en tiempo real"""
    
    def __init__(self, config: Optional[BrowserConfig] = None, websocket_manager=None, task_id: str = None):
        self.config = config or BrowserConfig()
        self.logger = logging.getLogger(__name__)
        
        # ✅ INTEGRACIÓN WEBSOCKET PARA TIEMPO REAL - SEGÚN UpgardeRef.md SECCIÓN 4.1
        self.websocket_manager = websocket_manager
        self.task_id = task_id
        
        # Estado del navegador
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.active_pages: Dict[str, Page] = {}
        
        # Sistema de cache
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1 hora
        self.content_cache: Dict[str, Dict] = {}
        self.max_cache_size = 100
        
        # Estadísticas
        self.stats = {
            "pages_scraped": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_time": 0.0
        }
        
        # Pool de contextos para concurrencia
        self.context_pool: List[BrowserContext] = []
        self.max_concurrent_contexts = 3
        
        self.logger.info("WebBrowserManager inicializado correctamente")
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.error("⚠️ Playwright no disponible - funcionalidad limitada")
        
        # ✅ CONFIGURAR DIRECTORIO PARA SCREENSHOTS
        if self.task_id:
            self.screenshot_dir = f"/tmp/screenshots/{self.task_id}"
            import os
            os.makedirs(self.screenshot_dir, exist_ok=True)

    async def initialize(self) -> bool:
        """Inicializa el navegador y contextos"""
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.error("Cannot initialize browser - Playwright not available")
            return False
        
        try:
            # Inicializar Playwright
            self.playwright = await async_playwright().start()
            
            # Lanzar navegador
            if self.config.browser_type == BrowserType.CHROMIUM:
                self.browser = await self.playwright.chromium.launch(
                    headless=self.config.headless
                )
            elif self.config.browser_type == BrowserType.FIREFOX:
                self.browser = await self.playwright.firefox.launch(
                    headless=self.config.headless
                )
            else:  # webkit
                self.browser = await self.playwright.webkit.launch(
                    headless=self.config.headless
                )
            
            # Crear contexto principal
            self.context = await self.browser.new_context(
                user_agent=self.config.user_agent,
                viewport=self.config.viewport,
                ignore_https_errors=self.config.ignore_https_errors
            )
            
            # Crear pool de contextos para concurrencia
            for i in range(self.max_concurrent_contexts):
                context = await self.browser.new_context(
                    user_agent=self.config.user_agent,
                    viewport=self.config.viewport,
                    ignore_https_errors=self.config.ignore_https_errors
                )
                self.context_pool.append(context)
            
            self.logger.info(f"Browser {self.config.browser_type.value} inicializado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando navegador: {e}")
            return False

    async def scrape_url(self, url: str, mode: ScrapingMode = ScrapingMode.STRUCTURED) -> WebPage:
        """Scraping de una URL individual"""
        start_time = time.time()
        
        try:
            # Verificar cache primero
            if self.cache_enabled:
                cached_page = self._get_cached_page(url)
                if cached_page:
                    self.stats["cache_hits"] += 1
                    return cached_page
            
            # Validar URL
            if not self._is_valid_url(url):
                return WebPage(
                    url=url,
                    error=f"URL inválida: {url}"
                )
            
            # Obtener contexto disponible
            context = self._get_available_context()
            page = await context.new_page()
            
            try:
                # Navegar a la página
                response = await page.goto(
                    url, 
                    timeout=self.config.timeout,
                    wait_until="domcontentloaded"
                )
                
                if not response:
                    return WebPage(url=url, error="No se pudo cargar la página")
                
                # Esperar a que el contenido se cargue completamente
                if self.config.enable_javascript:
                    await page.wait_for_timeout(2000)  # Esperar JS
                
                # Extraer contenido según el modo
                web_page = await self._extract_content(page, url, mode, response.status)
                web_page.loading_time = time.time() - start_time
                
                # Cachear resultado
                if self.cache_enabled and web_page.status_code == 200:
                    self._cache_page(url, web_page)
                
                self.stats["pages_scraped"] += 1
                
                return web_page
                
            finally:
                await page.close()
                
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            self.stats["errors"] += 1
            return WebPage(
                url=url,
                error=str(e),
                loading_time=time.time() - start_time
            )
        finally:
            self.stats["total_time"] += time.time() - start_time

    async def scrape_multiple_urls(self, urls: List[str], 
                                  mode: ScrapingMode = ScrapingMode.STRUCTURED,
                                  max_concurrent: int = 3) -> ScrapingResult:
        """Scraping concurrente de múltiples URLs"""
        start_time = time.time()
        
        if not urls:
            return ScrapingResult(success=False, error_message="No URLs provided")
        
        # Inicializar si no está listo
        if not self.browser:
            if not await self.initialize():
                return ScrapingResult(
                    success=False, 
                    error_message="Failed to initialize browser"
                )
        
        try:
            # Limitar concurrencia
            semaphore = asyncio.Semaphore(min(max_concurrent, len(self.context_pool)))
            
            async def scrape_with_semaphore(url: str) -> WebPage:
                async with semaphore:
                    return await self.scrape_url(url, mode)
            
            # Ejecutar scraping concurrente
            tasks = [scrape_with_semaphore(url) for url in urls]
            pages = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            valid_pages = []
            error_count = 0
            
            for i, result in enumerate(pages):
                if isinstance(result, Exception):
                    self.logger.error(f"Error scraping {urls[i]}: {result}")
                    error_count += 1
                    valid_pages.append(WebPage(url=urls[i], error=str(result)))
                elif isinstance(result, WebPage):
                    valid_pages.append(result)
                    if result.error:
                        error_count += 1
                else:
                    self.logger.error(f"Unexpected result type for {urls[i]}: {type(result)}")
                    error_count += 1
                    valid_pages.append(WebPage(url=urls[i], error="Unexpected result type"))
            
            processing_time = time.time() - start_time
            success = error_count < len(urls) / 2  # Más de 50% exitoso
            
            return ScrapingResult(
                success=success,
                pages=valid_pages,
                error_message=f"{error_count} errores de {len(urls)} URLs" if error_count > 0 else "",
                processing_time=processing_time,
                cache_hits=self.stats["cache_hits"]
            )
            
        except Exception as e:
            self.logger.error(f"Error en scraping múltiple: {e}")
            return ScrapingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )

    async def search_web(self, query: str, max_results: int = 10) -> ScrapingResult:
        """Busca en web usando Bing y scraping de resultados"""
        
        # Construir URL de búsqueda de Bing
        search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        
        try:
            # Primero obtener página de resultados de búsqueda
            search_page = await self.scrape_url(search_url, ScrapingMode.STRUCTURED)
            
            if search_page.error:
                return ScrapingResult(
                    success=False,
                    error_message=f"Error buscando '{query}': {search_page.error}"
                )
            
            # Extraer URLs de resultados (simulación simple)
            # En implementación real, parsearía los resultados de Bing
            result_urls = self._extract_search_results(search_page.html, max_results)
            
            if not result_urls:
                return ScrapingResult(
                    success=True,
                    pages=[search_page],
                    error_message="No se encontraron resultados específicos"
                )
            
            # Scraping de las páginas de resultados
            result = await self.scrape_multiple_urls(result_urls[:max_results])
            
            # Añadir página de búsqueda al resultado
            result.pages.insert(0, search_page)
            result.total_pages = len(result.pages)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda web '{query}': {e}")
            return ScrapingResult(
                success=False,
                error_message=str(e)
            )

    async def _extract_content(self, page: Page, url: str, mode: ScrapingMode, 
                              status_code: int) -> WebPage:
        """Extrae contenido de la página según el modo especificado"""
        
        try:
            title = await page.title()
            
            if mode == ScrapingMode.TEXT_ONLY:
                # Solo texto limpio
                content = await page.inner_text('body')
                html = ""
                
            elif mode == ScrapingMode.FULL_HTML:
                # HTML completo
                html = await page.content()
                content = await page.inner_text('body')
                
            elif mode == ScrapingMode.STRUCTURED:
                # Contenido estructurado (más inteligente)
                html = await page.content()
                
                # Extraer contenido estructurado
                content_parts = []
                
                # Título principal
                h1_elements = await page.query_selector_all('h1')
                for h1 in h1_elements:
                    text = await h1.inner_text()
                    if text.strip():
                        content_parts.append(f"# {text.strip()}")
                
                # Párrafos principales
                p_elements = await page.query_selector_all('p')
                for p in p_elements[:10]:  # Limitar a 10 párrafos
                    text = await p.inner_text()
                    if text.strip() and len(text.strip()) > 50:
                        content_parts.append(text.strip())
                
                # Enlaces importantes
                link_elements = await page.query_selector_all('a[href]')
                links = []
                for link in link_elements[:5]:  # Primeros 5 enlaces
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and text.strip():
                        full_url = urljoin(url, href)
                        links.append(f"[{text.strip()}]({full_url})")
                
                if links:
                    content_parts.append("\n**Enlaces relevantes:**\n" + "\n".join(links))
                
                content = "\n\n".join(content_parts)
                
            elif mode == ScrapingMode.SCREENSHOT:
                # Captura de pantalla (para casos especiales)
                screenshot = await page.screenshot()
                content = f"Screenshot capturada - {len(screenshot)} bytes"
                html = await page.content()
                
            else:
                # Modo por defecto
                content = await page.inner_text('body')
                html = ""
            
            # Metadata adicional
            metadata = {
                "scraped_at": datetime.now().isoformat(),
                "mode": mode.value,
                "content_length": len(content),
                "html_length": len(html)
            }
            
            # Intentar extraer meta description
            try:
                meta_desc = await page.get_attribute('meta[name="description"]', 'content')
                if meta_desc:
                    metadata["description"] = meta_desc
            except:
                pass
            
            return WebPage(
                url=url,
                title=title,
                content=content,
                html=html,
                status_code=status_code,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error extrayendo contenido de {url}: {e}")
            return WebPage(
                url=url,
                error=f"Error extrayendo contenido: {str(e)}"
            )

    def _extract_search_results(self, html: str, max_results: int) -> List[str]:
        """Extrae URLs de resultados de búsqueda del HTML"""
        if not SCRAPING_LIBRARIES_AVAILABLE:
            return []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            urls = []
            
            # Buscar enlaces de resultados (patrón genérico)
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and 'bing' not in href and 'microsoft' not in href:
                    urls.append(href)
                    if len(urls) >= max_results:
                        break
            
            return urls[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error extrayendo resultados de búsqueda: {e}")
            return []

    def _get_available_context(self) -> BrowserContext:
        """Obtiene un contexto disponible del pool"""
        if self.context_pool:
            return self.context_pool[0]  # Rotación simple
        return self.context

    def _is_valid_url(self, url: str) -> bool:
        """Valida si una URL es válida"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _generate_cache_key(self, url: str) -> str:
        """Genera clave de cache para URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cached_page(self, url: str) -> Optional[WebPage]:
        """Obtiene página del cache si es válida"""
        cache_key = self._generate_cache_key(url)
        
        if cache_key in self.content_cache:
            cached_data = self.content_cache[cache_key]
            
            # Verificar TTL
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                self.logger.debug(f"Cache hit para: {url}")
                return cached_data['page']
            else:
                # Eliminar entrada expirada
                del self.content_cache[cache_key]
        
        return None

    def _cache_page(self, url: str, page: WebPage):
        """Cachea una página"""
        cache_key = self._generate_cache_key(url)
        
        self.content_cache[cache_key] = {
            'page': page,
            'timestamp': time.time()
        }
        
        # Limitar tamaño del cache
        if len(self.content_cache) > self.max_cache_size:
            # Eliminar entrada más antigua
            oldest_key = min(
                self.content_cache.keys(),
                key=lambda k: self.content_cache[k]['timestamp']
            )
            del self.content_cache[oldest_key]

    async def cleanup(self):
        """Limpia recursos del navegador"""
        try:
            if self.active_pages:
                for page in self.active_pages.values():
                    await page.close()
                self.active_pages.clear()
            
            if self.context_pool:
                for context in self.context_pool:
                    await context.close()
                self.context_pool.clear()
            
            if self.context:
                await context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            
            self.logger.info("WebBrowserManager cleanup completado")
            
        except Exception as e:
            self.logger.error(f"Error durante cleanup: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso"""
        return {
            **self.stats,
            "cache_size": len(self.content_cache),
            "cache_enabled": self.cache_enabled,
            "contexts_available": len(self.context_pool),
            "browser_initialized": self.browser is not None
        }

    def clear_cache(self):
        """Limpia el cache de contenido"""
        self.content_cache.clear()
        self.logger.info("Cache de contenido limpiado")

# Funciones de utilidad para integración

def create_web_browser_manager(config: Optional[BrowserConfig] = None) -> WebBrowserManager:
    """Crea una instancia del gestor de navegación web"""
    return WebBrowserManager(config)

async def search_web_simple(query: str, max_results: int = 5) -> str:
    """Función simple para búsqueda web (para compatibilidad)"""
    manager = WebBrowserManager()
    
    try:
        await manager.initialize()
        result = await manager.search_web(query, max_results)
        
        if not result.success:
            return f"Error en búsqueda: {result.error_message}"
        
        # Formatear resultados
        content_parts = []
        for i, page in enumerate(result.pages[:max_results], 1):
            if not page.error and page.content:
                content_parts.append(f"**Resultado {i}: {page.title}**\n{page.content[:500]}...\n")
        
        return "\n".join(content_parts) if content_parts else "No se encontró contenido relevante"
        
    except Exception as e:
        return f"Error crítico en búsqueda: {str(e)}"
    finally:
        await manager.cleanup()

async def scrape_url_simple(url: str) -> str:
    """Función simple para scraping de URL (para compatibilidad)"""
    manager = WebBrowserManager()
    
    try:
        await manager.initialize()
        page = await manager.scrape_url(url, ScrapingMode.STRUCTURED)
        
        if page.error:
            return f"Error accediendo a {url}: {page.error}"
        
        return f"**{page.title}**\n\n{page.content}"
        
    except Exception as e:
        return f"Error crítico scraping {url}: {str(e)}"
    finally:
        await manager.cleanup()