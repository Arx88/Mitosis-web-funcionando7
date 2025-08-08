"""
🌐 NAVEGACIÓN WEB EN TIEMPO REAL CON SCREENSHOTS REALES
Implementa navegación web verdadera con captura de pantalla en tiempo real
usando Playwright + Servidor X11 virtual para visualización completa

CARACTERÍSTICAS:
- ✅ Servidor X11 virtual (Xvfb) para navegación visible  
- ✅ Screenshots JPEG reales capturados durante navegación
- ✅ Eventos WebSocket browser_visual en tiempo real
- ✅ Browser visible navegando paso a paso
- ✅ Captura automática cada 2 segundos durante navegación
"""

import asyncio
import os
import sys
import time
import base64
import json
import subprocess
import threading
import signal
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Importar WebSocket manager para eventos en tiempo real
try:
    from ..websocket.websocket_manager import get_websocket_manager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

@register_tool
class RealTimeBrowserTool(BaseTool):
    """
    🌐 HERRAMIENTA DE NAVEGACIÓN WEB EN TIEMPO REAL
    
    Proporciona navegación web visible con:
    - Servidor X11 virtual para mostrar el browser navegando
    - Screenshots JPEG reales capturados automáticamente  
    - Eventos browser_visual enviados al frontend en tiempo real
    - Navegación paso a paso visible en el Monitor de Ejecución
    """
    
    def __init__(self):
        super().__init__(
            name="real_time_browser",
            description="Navegación web en tiempo real con screenshots reales y visualización paso a paso"
        )
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        self.websocket_manager = None
        self.task_id = None
        self.xvfb_process = None
        self.screenshot_thread = None
        self.is_navigating = False
        self.current_page = None
        
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="task_description",
                param_type="string", 
                required=True,
                description="Descripción de la tarea de navegación a realizar",
                min_value=10,
                max_value=500
            ),
            ParameterDefinition(
                name="start_url",
                param_type="string",
                required=False,
                description="URL inicial para comenzar navegación",
                default="https://www.google.com"
            ),
            ParameterDefinition(
                name="capture_interval",
                param_type="integer", 
                required=False,
                description="Intervalo de captura de screenshots en segundos",
                default=1,  # Captura cada 1 segundo para más screenshots
                min_value=1,
                max_value=5  # Máximo 5 segundos para navegación más fluida
            ),
            ParameterDefinition(
                name="max_duration",
                param_type="integer",
                required=False, 
                description="Duración máxima de navegación en segundos",
                default=90,  # Aumentar a 90 segundos para más capturas
                min_value=30,  # Mínimo 30 segundos
                max_value=180  # Máximo 3 minutos
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> ToolExecutionResult:
        """🚀 EJECUTOR PRINCIPAL CON NAVEGACIÓN VISUAL EN TIEMPO REAL"""
        
        if not self.playwright_available:
            return ToolExecutionResult(
                success=False,
                error='Playwright no está disponible. Instalar con: pip install playwright && playwright install'
            )
        
        # Extraer parámetros
        task_description = parameters.get('task_description', '').strip()
        start_url = parameters.get('start_url', 'https://www.google.com')
        capture_interval = int(parameters.get('capture_interval', 2))
        max_duration = int(parameters.get('max_duration', 60))
        
        # Obtener task_id del config
        self.task_id = config.get('task_id') if config else f"browser-{int(time.time())}"
        
        try:
            # 🖥️ CONFIGURAR SERVIDOR X11 VIRTUAL
            self._setup_x11_server()
            
            # 🔄 INICIALIZAR WEBSOCKET PARA EVENTOS EN TIEMPO REAL
            self._initialize_websocket()
            
            # 🌐 EJECUTAR NAVEGACIÓN CON VISUALIZACIÓN EN TIEMPO REAL
            results = self._execute_real_time_navigation(
                task_description, start_url, capture_interval, max_duration
            )
            
            # ✅ RESULTADO EXITOSO
            return ToolExecutionResult(
                success=True,
                data={
                    'task_description': task_description,
                    'start_url': start_url,
                    'navigation_results': results,
                    'screenshots_captured': len(results.get('screenshots', [])),
                    'real_time_navigation': True,
                    'x11_server_used': True,
                    'capture_interval': capture_interval,
                    'total_duration': results.get('duration', 0),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            # 📧 NOTIFICAR ERROR EN TIEMPO REAL
            self._emit_browser_visual({
                'type': 'navigation_error',
                'message': f"❌ Error en navegación: {str(e)}",
                'timestamp': time.time()
            })
            
            return ToolExecutionResult(
                success=False,
                error=f'Error en navegación en tiempo real: {str(e)}'
            )
        finally:
            # 🧹 LIMPIAR RECURSOS
            self._cleanup_resources()
    
    def _setup_x11_server(self):
        """🖥️ CONFIGURAR SERVIDOR X11 VIRTUAL PARA NAVEGACIÓN VISIBLE"""
        try:
            # Configurar display virtual
            display_num = 99
            os.environ['DISPLAY'] = f':{display_num}'
            
            # VERIFICAR SI YA HAY UN SERVIDOR X11 CORRIENDO
            try:
                # Verificar si el display :99 ya está en uso
                result = subprocess.run(['xset', '-display', f':{display_num}', 'q'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    self._emit_progress(f"✅ Servidor X11 virtual ya está corriendo en display :{display_num}")
                    self._emit_browser_visual({
                        'type': 'x11_server_ready',
                        'message': '🖥️ Servidor X11 virtual detectado y listo - Navegación visible habilitada',
                        'display': f':{display_num}',
                        'resolution': '1920x1080',
                        'reused_existing': True,
                        'timestamp': time.time()
                    })
                    return  # Servidor ya existe, no necesitamos crear uno nuevo
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                # xset no está disponible o display no existe, necesitamos crear servidor
                pass
            
            # CREAR NUEVO SERVIDOR X11 SOLO SI NO EXISTE UNO
            # Verificar si Xvfb está disponible
            if not subprocess.run(['which', 'Xvfb'], capture_output=True).returncode == 0:
                self._emit_progress("⚠️ Xvfb no disponible, instalando...")
                subprocess.run(['apt-get', 'update', '-qq'], check=False)
                subprocess.run(['apt-get', 'install', '-y', 'xvfb'], check=False)
            
            # Intentar iniciar servidor X11 virtual
            self._emit_progress(f"🖥️ Iniciando nuevo servidor X11 virtual en display :{display_num}")
            
            self.xvfb_process = subprocess.Popen([
                'Xvfb', f':{display_num}',
                '-screen', '0', '1920x1080x24',
                '-ac', '-nolisten', 'tcp'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Esperar a que el servidor se inicie
            time.sleep(2)
            
            # Verificar que el servidor está corriendo
            if self.xvfb_process.poll() is None:
                self._emit_progress("✅ Nuevo servidor X11 virtual iniciado correctamente")
                self._emit_browser_visual({
                    'type': 'x11_server_started',
                    'message': '🖥️ Nuevo servidor X11 virtual activo - Navegación visible habilitada',
                    'display': f':{display_num}',
                    'resolution': '1920x1080',
                    'reused_existing': False,
                    'timestamp': time.time()
                })
            else:
                raise Exception("Fallo al iniciar servidor Xvfb")
                
        except Exception as e:
            self._emit_progress(f"❌ Error configurando X11: {str(e)}")
            # No hacer raise - continuar sin servidor X11 propio pero usar el existente
            self._emit_progress("⚠️ Continuando con servidor X11 existente...")
            os.environ['DISPLAY'] = ':99'  # Usar el display existente
    
    def _initialize_websocket(self):
        """🔄 INICIALIZAR WEBSOCKET PARA EVENTOS EN TIEMPO REAL"""
        try:
            if WEBSOCKET_AVAILABLE and self.task_id:
                self.websocket_manager = get_websocket_manager()
                self._emit_progress("🔌 WebSocket inicializado para navegación en tiempo real")
            else:
                self._emit_progress("⚠️ WebSocket no disponible - usando logging básico")
        except Exception as e:
            self._emit_progress(f"⚠️ Error inicializando WebSocket: {str(e)}")
    
    
    def _run_navigation_in_new_thread(self, task_description: str, start_url: str, 
                                    capture_interval: int, max_duration: int, results: Dict[str, Any]) -> Dict[str, Any]:
        """🔧 EJECUTAR NAVEGACIÓN EN THREAD SEPARADO PARA EVITAR CONFLICTOS DE EVENT LOOP"""
        
        # Crear nuevo event loop en este thread
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        
        try:
            return new_loop.run_until_complete(
                self._async_navigate_with_real_time_capture(
                    task_description, start_url, capture_interval, max_duration, results
                )
            )
        finally:
            new_loop.close()
    
    def _execute_real_time_navigation(self, task_description: str, start_url: str, 
                                    capture_interval: int, max_duration: int) -> Dict[str, Any]:
        """🌐 EJECUTAR NAVEGACIÓN CON CAPTURA EN TIEMPO REAL"""
        
        results = {
            'task_description': task_description,
            'start_url': start_url,
            'screenshots': [],
            'pages_visited': [],
            'actions_performed': [],
            'duration': 0,
            'success': True
        }
        
        start_time = time.time()
        
        try:
            # 🚀 INICIAR NAVEGACIÓN ASÍNCRONA
            self._emit_browser_visual({
                'type': 'navigation_start_real',
                'message': f'🚀 NAVEGACIÓN REAL INICIADA: {task_description}',
                'task_description': task_description,
                'start_url': start_url,
                'timestamp': time.time()
            })
            
            # CORRECCIÓN CRÍTICA: MANEJAR EVENT LOOP EXISTENTE CORRECTAMENTE
            try:
                # Intentar obtener el loop actual
                current_loop = asyncio.get_running_loop()
                self._emit_progress("🔄 Usando event loop existente")
                
                # Usar asyncio.create_task para ejecutar en el loop actual
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Ejecutar la navegación en un thread separado para evitar conflictos
                    future = executor.submit(self._run_navigation_in_new_thread, 
                                           task_description, start_url, capture_interval, max_duration, results)
                    navigation_result = future.result()
                    results.update(navigation_result)
                    
            except RuntimeError:
                # No hay loop corriendo, podemos crear uno nuevo
                self._emit_progress("🔄 Creando nuevo event loop")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    navigation_result = loop.run_until_complete(
                        self._async_navigate_with_real_time_capture(
                            task_description, start_url, capture_interval, max_duration, results
                        )
                    )
                    results.update(navigation_result)
                finally:
                    loop.close()
            
            # Calcular duración total
            results['duration'] = time.time() - start_time
            
            # 🎉 NAVEGACIÓN COMPLETADA
            self._emit_browser_visual({
                'type': 'navigation_complete_real',
                'message': f'✅ NAVEGACIÓN REAL COMPLETADA: {len(results["screenshots"])} capturas realizadas',
                'total_screenshots': len(results['screenshots']),
                'total_duration': results['duration'],
                'pages_visited': len(results['pages_visited']),
                'timestamp': time.time()
            })
            
            return results
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            results['duration'] = time.time() - start_time
            
            self._emit_browser_visual({
                'type': 'navigation_error_real', 
                'message': f'❌ Error durante navegación: {str(e)}',
                'timestamp': time.time()
            })
            
            raise
    
    async def _async_navigate_with_real_time_capture(self, task_description: str, start_url: str,
                                                   capture_interval: int, max_duration: int, 
                                                   results: Dict[str, Any]) -> Dict[str, Any]:
        """🎭 NAVEGACIÓN ASÍNCRONA CON PLAYWRIGHT Y CAPTURA AUTOMÁTICA"""
        
        async with async_playwright() as p:
            # Configurar browser con argumentos para servidor X11
            browser = await p.chromium.launch(
                headless=False,  # 🚀 NAVEGACIÓN VISIBLE
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-ipc-flooding-protection',
                    f'--display={os.environ.get("DISPLAY", ":99")}',  # 🖥️ USAR DISPLAY X11
                    '--window-size=1920,1080'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            page = await context.new_page()
            self.current_page = page
            
            try:
                # 🎬 INICIAR HILO DE CAPTURA AUTOMÁTICA
                self.is_navigating = True
                self._start_screenshot_capture_thread(page, capture_interval, results)
                
                # 🌐 NAVEGAR A URL INICIAL  
                self._emit_browser_visual({
                    'type': 'page_navigation',
                    'message': f'🌐 Navegando a página inicial: {start_url}',
                    'url': start_url,
                    'timestamp': time.time()
                })
                
                await page.goto(start_url, wait_until='networkidle')
                
                # Registrar página visitada
                results['pages_visited'].append({
                    'url': start_url,
                    'title': await page.title(),
                    'timestamp': time.time()
                })
                
                # 🎯 SIMULAR NAVEGACIÓN INTELIGENTE BASADA EN TASK_DESCRIPTION
                await self._perform_intelligent_navigation(page, task_description, results)
                
                # Esperar un poco más para capturas finales
                await asyncio.sleep(3)
                
                return {'success': True}
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
            
            finally:
                # 🛑 DETENER CAPTURA Y CERRAR BROWSER
                self.is_navigating = False
                if self.screenshot_thread:
                    self.screenshot_thread.join(timeout=5)
                
                await context.close()
                await browser.close()
    
    async def _perform_intelligent_navigation(self, page, task_description: str, results: Dict[str, Any]):
        """🤖 REALIZAR NAVEGACIÓN INTELIGENTE BASADA EN LA DESCRIPCIÓN"""
        
        try:
            # Analizar task_description para determinar acciones
            if 'buscar' in task_description.lower() or 'search' in task_description.lower():
                await self._perform_search_task(page, task_description, results)
            elif 'pokemon' in task_description.lower():
                await self._perform_pokemon_search(page, results)
            elif 'inteligencia artificial' in task_description.lower() or 'ai' in task_description.lower():
                await self._perform_ai_search(page, results)
            else:
                # Navegación genérica - explorar la página actual
                await self._perform_generic_exploration(page, results)
                
        except Exception as e:
            self._emit_browser_visual({
                'type': 'navigation_step_error',
                'message': f'⚠️ Error en navegación inteligente: {str(e)}',
                'timestamp': time.time()
            })
    
    async def _perform_search_task(self, page, task_description: str, results: Dict[str, Any]):
        """🔍 REALIZAR TAREA DE BÚSQUEDA - VERSIÓN MEJORADA CON MÚLTIPLES ESTRATEGIAS"""
        
        try:
            # 1. EXTRAER TÉRMINOS DE BÚSQUEDA INTELIGENTES
            search_terms = self._extract_search_terms(task_description)
            self._emit_browser_visual({
                'type': 'search_terms_extracted',
                'message': f'📝 Términos extraídos: "{search_terms}"',
                'original_task': task_description,
                'extracted_terms': search_terms,
                'timestamp': time.time()
            })
            
            # 2. INTENTAR MÚLTIPLES SELECTORS DE CAMPO DE BÚSQUEDA
            search_selectors = [
                # Google y motores principales
                'input[name="q"]',
                'textarea[name="q"]',
                
                # Selectores genéricos de búsqueda
                'input[type="search"]',
                'input[placeholder*="search" i]', 
                'input[placeholder*="buscar" i]',
                'input[placeholder*="Buscar" i]',
                'input[placeholder*="Search" i]',
                
                # Clases comunes
                '.search-input',
                '.search-box',
                '.searchbox',
                '#search',
                '#search-input',
                '#searchbox',
                
                # Bing y otros motores
                'input[name="search"]',
                'input[id="sb_form_q"]',  # Bing específico
                
                # Fallbacks más generales
                'input[type="text"]',  # Último recurso
            ]
            
            search_input = None
            used_selector = None
            
            # Intentar cada selector con timeout progresivo
            for i, selector in enumerate(search_selectors):
                try:
                    self._emit_progress(f"🔍 Probando selector {i+1}: {selector}")
                    search_input = await page.wait_for_selector(selector, timeout=2000)
                    if search_input:
                        used_selector = selector
                        self._emit_progress(f"✅ Campo de búsqueda encontrado con: {selector}")
                        break
                except:
                    continue
            
            if not search_input:
                # Si no encontramos campo de búsqueda, buscar enlaces con texto relevante
                await self._perform_link_based_search(page, search_terms, results)
                return
                
            # 3. PREPARAR CAMPO DE BÚSQUEDA Y REALIZAR BÚSQUEDA
            self._emit_browser_visual({
                'type': 'search_field_found',
                'message': f'🎯 Campo de búsqueda encontrado: {used_selector}',
                'selector': used_selector,
                'timestamp': time.time()
            })
            
            try:
                # Limpiar campo existente
                self._emit_progress("🔄 Limpiando campo de búsqueda...")
                await search_input.click()
                await search_input.select_text()  # Corregido: select_text() en lugar de select_all()
                await asyncio.sleep(0.5)
                
                # Escribir términos de búsqueda
                self._emit_progress(f"⌨️ Escribiendo términos: '{search_terms}'")
                self._emit_browser_visual({
                    'type': 'typing_search',
                    'message': f'⌨️ Escribiendo: "{search_terms}"',
                    'search_terms': search_terms,
                    'timestamp': time.time()
                })
                
                await search_input.type(search_terms, delay=100)  # Escribir con delay más humano
                await asyncio.sleep(1)  # Pausa para ver el texto escrito
                self._emit_progress("✅ Términos de búsqueda escritos correctamente")
                
                # Registrar acción
                results['actions_performed'].append({
                    'action': 'search_typed',
                    'terms': search_terms,
                    'selector': used_selector,
                    'timestamp': time.time()
                })
                
            except Exception as e:
                self._emit_progress(f"❌ Error preparando búsqueda: {str(e)}")
                return
            
            # 4. ENVIAR BÚSQUEDA (múltiples métodos)
            search_submitted = False
            
            # Método 1: Presionar Enter
            try:
                self._emit_progress("🔍 Enviando búsqueda con Enter...")
                await search_input.press('Enter')
                search_submitted = True
                self._emit_progress("✅ Búsqueda enviada con Enter exitosamente")
            except Exception as e:
                self._emit_progress(f"⚠️ Error enviando búsqueda con Enter: {str(e)}")
                pass
            
            # Método 2: Buscar botón de búsqueda si Enter no funcionó
            if not search_submitted:
                search_button_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button[aria-label*="search" i]',
                    'button[aria-label*="buscar" i]',
                    '.search-button',
                    '#search-button',
                    'button:has-text("Search")',
                    'button:has-text("Buscar")',
                    '[data-ved]',  # Google específico
                ]
                
                for selector in search_button_selectors:
                    try:
                        search_button = await page.wait_for_selector(selector, timeout=1000)
                        if search_button:
                            self._emit_progress(f"🔍 Enviando búsqueda con botón: {selector}")
                            await search_button.click()
                            search_submitted = True
                            self._emit_progress(f"✅ Búsqueda enviada con botón: {selector}")
                            break
                    except Exception as e:
                        self._emit_progress(f"⚠️ Error con botón {selector}: {str(e)}")
                        continue
            
            if not search_submitted:
                self._emit_progress("⚠️ No se pudo enviar búsqueda - usando fallback URL")
                # Fallback: navegar directamente a URL de búsqueda
                try:
                    current_url = page.url
                    if 'google.com' in current_url:
                        search_url = f"https://www.google.com/search?q={search_terms.replace(' ', '+')}"
                    elif 'bing.com' in current_url:
                        search_url = f"https://www.bing.com/search?q={search_terms.replace(' ', '+')}"
                    else:
                        search_url = f"{current_url}?q={search_terms.replace(' ', '+')}"
                    
                    self._emit_progress(f"🔗 Navegando a URL de búsqueda: {search_url}")
                    await page.goto(search_url)
                    search_submitted = True
                    self._emit_progress("✅ Búsqueda enviada via URL fallback")
                except Exception as e:
                    self._emit_progress(f"❌ Error en navegación fallback: {str(e)}")
                    return
            
            # 5. ESPERAR RESULTADOS Y EXPLORAR
            self._emit_browser_visual({
                'type': 'waiting_results',
                'message': '⏳ Esperando resultados de búsqueda...',
                'timestamp': time.time()
            })
            
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Registrar página de resultados
            results['pages_visited'].append({
                'url': page.url,
                'title': await page.title(),
                'type': 'search_results',
                'search_terms': search_terms,
                'timestamp': time.time()
            })
            
            results['actions_performed'].append({
                'action': 'search_completed',
                'terms': search_terms,
                'results_url': page.url,
                'timestamp': time.time()
            })
            
            # 6. EXPLORAR PRIMEROS RESULTADOS
            await self._explore_search_results(page, search_terms, results)
                
        except Exception as e:
            self._emit_browser_visual({
                'type': 'search_error',
                'message': f'❌ Error en búsqueda: {str(e)}',
                'timestamp': time.time()
            })
            
            # Fallback: navegación genérica
            await self._perform_generic_exploration(page, results)
    
    async def _explore_search_results(self, page, search_terms: str, results: Dict[str, Any]):
        """🔍 EXPLORAR RESULTADOS DE BÚSQUEDA DE MANERA INTELIGENTE"""
        
        try:
            # Buscar enlaces de resultados con múltiples estrategias
            result_selectors = [
                'h3 a',  # Google, Bing estándar
                '.g h3 a',  # Google específico
                '.b_algo h2 a',  # Bing específico
                '[data-hveid] h3 a',  # Google alternativo
                '.result h3 a',  # Genérico
                'a[href*="http"]:has(h3)',  # Fallback general
                'a[href*="http"]:has(h2)',  # Fallback alternativo
            ]
            
            result_links = []
            
            for selector in result_selectors:
                try:
                    links = await page.query_selector_all(selector)
                    if links:
                        self._emit_progress(f"✅ Encontrados {len(links)} resultados con: {selector}")
                        result_links = links[:3]  # Tomar primeros 3 resultados
                        break
                except:
                    continue
            
            if not result_links:
                self._emit_progress("⚠️ No se encontraron enlaces de resultados, haciendo scroll")
                # Hacer scroll para cargar más contenido
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                await asyncio.sleep(2)
                return
            
            # 🚀 EXPLORAR MÁS RESULTADOS PARA MAYOR DIVERSIDAD DE FUENTES
            max_links_to_explore = min(8, len(result_links))  # 🔥 AUMENTADO DE 4 A 8 ENLACES
            self._emit_progress(f"🎯 Explorando hasta {max_links_to_explore} sitios web diferentes para mayor diversidad")
            
            explored_domains = set()  # Trackear dominios visitados para evitar duplicados
            successful_explorations = 0
            max_successful = 6  # Mínimo 6 sitios exitosos
            
            for i in range(max_links_to_explore):
                try:
                    # Re-consultar elementos para evitar contexto destruido
                    fresh_links = await page.query_selector_all('.b_algo h2 a')
                    if i >= len(fresh_links):
                        self._emit_progress(f"⚠️ No hay suficientes enlaces frescos para resultado {i+1}")
                        continue
                    
                    link = fresh_links[i]
                    href = await link.get_attribute('href')
                    link_text = await link.text_content()
                    
                    # FILTRO DE RELEVANCIA MEJORADO Y DIVERSIDAD DE DOMINIOS
                    if href and href.startswith('http'):
                        # Extraer dominio para verificar diversidad
                        import urllib.parse
                        domain = urllib.parse.urlparse(href).netloc.lower()
                        
                        # Saltar si ya visitamos este dominio (forzar diversidad)
                        if domain in explored_domains:
                            self._emit_progress(f"🔄 Saltando dominio ya explorado: {domain}")
                            continue
                        
                        # Filtrar enlaces comerciales y irrelevantes (más estricto)
                        irrelevant_domains = [
                            'amazon.com', 'ebay.com', 'aliexpress.com', 'mercadolibre.com', 
                            'shopping.', 'ads.', 'publicidad', 'tienda', 'shop', 
                            'marketplace', 'store', 'buy', 'comprar', 'precio'
                        ]
                        is_irrelevant = any(domain_filter in href.lower() for domain_filter in irrelevant_domains)
                        
                        # Filtrar por keywords comerciales en el título
                        commercial_keywords = [
                            'comprar', 'precio', 'tienda', 'shop', 'buy', 'sale', 'oferta', 
                            'descuento', 'venta', 'store', 'marketplace', 'shopping'
                        ]
                        has_commercial_keywords = any(keyword in link_text.lower() for keyword in commercial_keywords)
                        
                        if is_irrelevant or has_commercial_keywords:
                            self._emit_progress(f"⚠️ Saltando enlace comercial: {domain} - {link_text[:30]}...")
                            continue
                        
                        # Agregar dominio a lista de explorados
                        explored_domains.add(domain)
                        
                        print(f"🔍 SOURCES DEBUG: About to navigate to DIVERSE source #{successful_explorations + 1}: {domain}")
                        self._emit_browser_visual({
                            'type': 'exploring_diverse_source',
                            'message': f'🌐 Explorando fuente diversa {successful_explorations + 1}/6: {domain}',
                            'link_text': link_text,
                            'url': href,
                            'domain': domain,
                            'timestamp': time.time()
                        })
                        
                        # NAVEGACIÓN DIRECTA SIN PESTAÑAS - MÉTODO SIMPLIFICADO Y ROBUSTO
                        self._emit_progress(f"🌐 Navegando directamente a: {href[:50]}...")
                        
                        # Navegar directamente al enlace
                        await page.goto(href, wait_until='networkidle')
                        await asyncio.sleep(3)
                        
                        # Capturar screenshot de la página visitada
                        await self._capture_screenshot_async(page, i+10)
                        
                        # Registrar página visitada
                        current_title = await page.title()
                        current_url = page.url
                        
                        results['pages_visited'].append({
                            'url': current_url,
                            'title': current_title,
                            'type': 'search_result_page',
                            'result_index': i,
                            'search_terms': search_terms,
                            'timestamp': time.time(),
                            'content_extracted': True,
                            'navigation_method': 'direct_goto'
                        })
                        
                        self._emit_browser_visual({
                            'type': 'page_visited',
                            'message': f'✅ Navegado a: {current_title[:50]}...',
                            'url': current_url,
                            'title': current_title,
                            'result_index': i,
                            'timestamp': time.time()
                        })
                        
                        # 🚀 EXPLORAR MÁS A FONDO EL CONTENIDO DE LA PÁGINA
                        self._emit_progress(f"📄 Extrayendo contenido detallado de {domain}...")
                        
                        # Scroll más extensivo para cargar contenido dinámico
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 4)')
                        await asyncio.sleep(1)
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                        await asyncio.sleep(1)
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 3)')
                        await asyncio.sleep(2)
                        await self._capture_screenshot_async(page, successful_explorations+100)
                        
                        # 📝 EXTRAER CONTENIDO REAL EXTENSO Y DE CALIDAD
                        page_content = await page.evaluate('''
                            () => {
                                // ESTRATEGIA MULTI-SELECTOR PARA EXTRAER MÁXIMO CONTENIDO ÚTIL
                                let content = '';
                                let extractedSections = [];
                                
                                // 1. PRIORITIZAR CONTENIDO EDITORIAL Y ARTÍCULOS
                                const articleSelectors = [
                                    'article', 'main', '[role="main"]', '.article', '.post', 
                                    '.content', '.entry-content', '.post-content', '.article-content',
                                    '#content', '#main', '.main-content', '.page-content'
                                ];
                                
                                for (let selector of articleSelectors) {
                                    const element = document.querySelector(selector);
                                    if (element && element.innerText && element.innerText.length > 200) {
                                        content = element.innerText || element.textContent || '';
                                        extractedSections.push('article-content');
                                        break;
                                    }
                                }
                                
                                // 2. SI NO HAY ARTÍCULO, BUSCAR CONTENIDO EN SECCIONES ESPECÍFICAS
                                if (!content || content.length < 300) {
                                    const sectionSelectors = [
                                        '.bio', '.biography', '.about', '.description', '.summary',
                                        '.news-content', '.text-content', '.body-text', 'section',
                                        'p', '.paragraph', '.content-text'
                                    ];
                                    
                                    let sectionContent = '';
                                    for (let selector of sectionSelectors) {
                                        const elements = document.querySelectorAll(selector);
                                        for (let elem of elements) {
                                            if (elem.innerText && elem.innerText.length > 50) {
                                                sectionContent += elem.innerText + ' ';
                                                if (sectionContent.length > 1500) break; // Suficiente contenido
                                            }
                                        }
                                        if (sectionContent.length > 500) break;
                                    }
                                    
                                    if (sectionContent.length > content.length) {
                                        content = sectionContent;
                                        extractedSections.push('section-content');
                                    }
                                }
                                
                                // 3. ÚLTIMO RECURSO: BODY COMPLETO PERO FILTRADO
                                if (!content || content.length < 500) {
                                    content = document.body.innerText || document.body.textContent || '';
                                    extractedSections.push('body-fallback');
                                }
                                
                                // 4. LIMPIAR Y PROCESAR CONTENIDO
                                // Remover líneas duplicadas y espacios excesivos
                                content = content.replace(/\\s+/g, ' ').trim();
                                
                                // Remover texto de navegación común
                                const navigationText = [
                                    'Skip to content', 'Menu', 'Navigation', 'Home', 'About', 'Contact',
                                    'Privacy Policy', 'Terms', 'Cookie', 'Subscribe', 'Newsletter'
                                ];
                                
                                for (let navText of navigationText) {
                                    content = content.replace(new RegExp(navText, 'gi'), '');
                                }
                                
                                // 5. EXPANDIR LÍMITE DE CARACTERES PARA MÁS INFORMACIÓN
                                const maxChars = 3000; // 🔥 AUMENTADO DE 2000 A 3000 CARACTERES
                                content = content.substring(0, maxChars);
                                
                                // Retornar información de calidad sobre la extracción
                                return {
                                    content: content,
                                    length: content.length,
                                    extraction_method: extractedSections.join(', '),
                                    quality_score: content.length > 1000 ? 'high' : content.length > 500 ? 'medium' : 'low'
                                };
                            }
                        ''')
                        
                        # Procesar resultado de extracción
                        content_text = page_content.get('content', '') if isinstance(page_content, dict) else page_content
                        content_length = page_content.get('length', len(content_text)) if isinstance(page_content, dict) else len(content_text)
                        extraction_method = page_content.get('extraction_method', 'unknown') if isinstance(page_content, dict) else 'basic'
                        quality_score = page_content.get('quality_score', 'unknown') if isinstance(page_content, dict) else 'unknown'
                        
                        # 📊 LOGGING DETALLADO DE EXTRACCIÓN
                        self._emit_progress(f"📊 Contenido extraído de {domain}:")
                        self._emit_progress(f"   📝 Caracteres: {content_length}")
                        self._emit_progress(f"   🎯 Método: {extraction_method}")  
                        self._emit_progress(f"   ⭐ Calidad: {quality_score}")
                        
                        # Solo contar como exitoso si extrajo contenido suficiente
                        if content_length > 200:  # Mínimo 200 caracteres de contenido real
                            successful_explorations += 1
                        
                        self._emit_progress(f"📄 Contenido extraído: {content_length} caracteres de {current_title[:30]}...")
                        
                        results['actions_performed'].append({
                            'action': 'diverse_source_explored',
                            'result_index': successful_explorations,
                            'url': current_url,
                            'title': current_title,
                            'domain': domain,
                            'content_preview': content_text[:300] if content_text else '',
                            'content_length': content_length,
                            'extraction_method': extraction_method,
                            'quality_score': quality_score,
                            'timestamp': time.time(),
                            'navigation_method': 'direct_goto',
                            'content_extracted': content_length > 200
                        })
                        
                        # Scroll adicional para explorar más contenido
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                        await asyncio.sleep(2)
                        await self._capture_screenshot_async(page, successful_explorations+200)
                        
                        # 🎯 VERIFICAR SI YA TENEMOS SUFICIENTES FUENTES DIVERSAS
                        if successful_explorations >= max_successful:
                            self._emit_progress(f"🎉 ¡Objetivo cumplido! Se exploraron {successful_explorations} fuentes diversas exitosamente")
                            break
                        
                        # Volver a resultados de Bing para el siguiente enlace
                        self._emit_progress(f"🔄 Volviendo a resultados para siguiente enlace ({successful_explorations}/{max_successful} completados)...")
                        await page.go_back()
                        await asyncio.sleep(3)
                        await page.wait_for_load_state('networkidle')
                        await self._capture_screenshot_async(page, successful_explorations+300)
                        
                        self._emit_browser_visual({
                            'type': 'back_to_results_progress',
                            'message': f'↩️ De vuelta en resultados - Progreso: {successful_explorations}/{max_successful} fuentes exitosas',
                            'progress': f"{successful_explorations}/{max_successful}",
                            'timestamp': time.time()
                        })
                        
                except Exception as e:
                    self._emit_progress(f"⚠️ Error explorando resultado {i+1}: {str(e)}")
                    continue
                    
        except Exception as e:
            self._emit_progress(f"❌ Error explorando resultados: {str(e)}")
    
    async def _perform_link_based_search(self, page, search_terms: str, results: Dict[str, Any]):
        """🔗 BÚSQUEDA BASADA EN ENLACES CUANDO NO HAY CAMPO DE BÚSQUEDA"""
        
        try:
            self._emit_browser_visual({
                'type': 'link_based_search',
                'message': f'🔗 Sin campo de búsqueda, buscando enlaces relevantes para: {search_terms}',
                'search_terms': search_terms,
                'timestamp': time.time()
            })
            
            # Buscar enlaces que contengan palabras clave
            search_words = search_terms.lower().split()[:3]  # Primeras 3 palabras
            
            all_links = await page.query_selector_all('a[href]')
            relevant_links = []
            
            for link in all_links:
                try:
                    text = await link.text_content()
                    href = await link.get_attribute('href')
                    
                    if text and href:
                        text_lower = text.lower()
                        # Verificar si el texto del enlace contiene alguna palabra clave
                        relevance_score = sum(1 for word in search_words if word in text_lower)
                        
                        if relevance_score > 0 and len(text.strip()) > 5:
                            relevant_links.append({
                                'element': link,
                                'text': text.strip(),
                                'href': href,
                                'score': relevance_score
                            })
                except:
                    continue
            
            # Ordenar por relevancia y tomar los mejores
            relevant_links.sort(key=lambda x: x['score'], reverse=True)
            
            if relevant_links:
                best_link = relevant_links[0]
                self._emit_browser_visual({
                    'type': 'relevant_link_found',
                    'message': f'🎯 Enlace relevante encontrado: {best_link["text"][:50]}...',
                    'link_text': best_link['text'],
                    'url': best_link['href'],
                    'timestamp': time.time()
                })
                
                # Hacer clic en el enlace más relevante
                await best_link['element'].click()
                await page.wait_for_load_state('networkidle')
                
                results['actions_performed'].append({
                    'action': 'relevant_link_clicked',
                    'link_text': best_link['text'],
                    'url': best_link['href'],
                    'relevance_score': best_link['score'],
                    'timestamp': time.time()
                })
                
                # Registrar nueva página
                results['pages_visited'].append({
                    'url': page.url,
                    'title': await page.title(),
                    'type': 'link_exploration',
                    'search_terms': search_terms,
                    'timestamp': time.time()
                })
            else:
                self._emit_progress("⚠️ No se encontraron enlaces relevantes")
                await self._perform_generic_exploration(page, results)
                
        except Exception as e:
            self._emit_progress(f"❌ Error en búsqueda basada en enlaces: {str(e)}")
            await self._perform_generic_exploration(page, results)
    
    async def _perform_pokemon_search(self, page, results: Dict[str, Any]):
        """🎮 BÚSQUEDA ESPECÍFICA DE POKÉMON"""
        await self._perform_search_with_terms(page, "Pokemon información", results)
    
    async def _perform_ai_search(self, page, results: Dict[str, Any]):
        """🤖 BÚSQUEDA ESPECÍFICA DE IA"""
        await self._perform_search_with_terms(page, "inteligencia artificial 2025", results)
    
    async def _perform_search_with_terms(self, page, search_terms: str, results: Dict[str, Any]):
        """🔍 REALIZAR BÚSQUEDA CON TÉRMINOS ESPECÍFICOS"""
        
        # Buscar campo de búsqueda
        search_input = None
        search_selectors = ['input[name="q"]', 'input[type="search"]']
        
        for selector in search_selectors:
            try:
                search_input = await page.wait_for_selector(selector, timeout=3000)
                if search_input:
                    break
            except:
                continue
        
        if search_input:
            self._emit_browser_visual({
                'type': 'search_specific',
                'message': f'🔍 Búsqueda específica: {search_terms}',
                'terms': search_terms,
                'timestamp': time.time()
            })
            
            await search_input.fill(search_terms)
            await asyncio.sleep(1)
            await search_input.press('Enter')
            await page.wait_for_load_state('networkidle')
            
            results['actions_performed'].append({
                'action': 'specific_search',
                'terms': search_terms,
                'timestamp': time.time()
            })
    
    async def _perform_generic_exploration(self, page, results: Dict[str, Any]):
        """🗺️ EXPLORACIÓN GENÉRICA DE LA PÁGINA"""
        
        self._emit_browser_visual({
            'type': 'page_exploration',
            'message': '🗺️ Explorando página actual',
            'url': page.url,
            'timestamp': time.time()
        })
        
        # Hacer scroll para mostrar contenido
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
        await asyncio.sleep(2)
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(2)
        
        results['actions_performed'].append({
            'action': 'page_exploration',
            'url': page.url,
            'timestamp': time.time()
        })
    
    def _extract_search_terms(self, task_description: str) -> str:
        """📝 EXTRAER TÉRMINOS DE BÚSQUEDA INTELIGENTES DEL TASK_DESCRIPTION - SOLUCIÓN MEJORADA"""
        
        import re
        
        # DEBUG: Log de la descripción recibida
        self._emit_progress(f"🔍 EXTRAYENDO términos de: '{task_description}'")
        
        # 1. DETECTAR PATRÓN ESPECÍFICO: "Buscar información sobre 'QUERY' en MOTOR"
        # Este es el patrón más común que viene desde unified_web_search_tool
        specific_search_pattern = r"Buscar información sobre ['\"]([^'\"]+)['\"]"
        specific_match = re.search(specific_search_pattern, task_description, re.IGNORECASE)
        
        if specific_match:
            search_terms = specific_match.group(1).strip()
            self._emit_progress(f"✅ PATRÓN ESPECÍFICO detectado: '{search_terms}'")
            return search_terms
        
        # 2. DETECTAR OTROS PATRONES COMUNES DE BÚSQUEDA
        search_patterns = [
            r"buscar.*?sobre\s+([^'\"]+?)(?:\s+en\s|\s+y\s|$)",  # "buscar sobre XXX"
            r"información.*?sobre\s+([^'\"]+?)(?:\s+en\s|\s+y\s|$)",  # "información sobre XXX"
            r"investigar.*?sobre\s+([^'\"]+?)(?:\s+en\s|\s+y\s|$)",  # "investigar sobre XXX"
            r"['\"]([^'\"]+)['\"]",  # Cualquier texto entre comillas
            r"explorar.*?([^'\"]+?)(?:\s+con\s|\s+y\s|$)",  # "explorar XXX"
        ]
        
        for pattern in search_patterns:
            matches = re.findall(pattern, task_description, re.IGNORECASE)
            if matches:
                search_terms = matches[0].strip()
                if len(search_terms) > 3:  # Asegurar que no sea demasiado corto
                    self._emit_progress(f"✅ PATRÓN ALTERNATIVO detectado: '{search_terms}'")
                    return self._clean_search_terms(search_terms)
        
        # 3. FALLBACK: EXTRAER PALABRAS CLAVE SIGNIFICATIVAS
        self._emit_progress("⚠️ No se detectaron patrones específicos, usando extracción de keywords")
        
        # Remover palabras de instrucción común
        text = task_description.lower()
        instruction_words = [
            'buscar', 'información', 'sobre', 'acerca', 'de', 'investigar', 'analizar',
            'encontrar', 'obtener', 'datos', 'específicos', 'necesarios', 'completar',
            'realizar', 'web_search', 'para', 'explorar', 'resultados', 'primeros',
            'con', 'screenshots', 'continuos', 'web', 'motor', 'búsqueda', 'en'
        ]
        
        # Filtrar palabras significativas
        words = re.findall(r'\b[a-zA-ZáéíóúñÁÉÍÓÚÑ]+\b', task_description)
        keywords = []
        
        for word in words:
            word_lower = word.lower()
            if (len(word) > 3 and 
                word_lower not in instruction_words and
                not word_lower.isdigit()):
                keywords.append(word)
        
        # Tomar las primeras 3-4 palabras más relevantes
        search_terms = ' '.join(keywords[:4]) if keywords else ""
        
        if search_terms:
            self._emit_progress(f"✅ KEYWORDS extraídas: '{search_terms}'")
            return self._clean_search_terms(search_terms)
        
        # 4. ÚLTIMO FALLBACK
        fallback_terms = "información general"
        self._emit_progress(f"⚠️ FALLBACK usado: '{fallback_terms}'")
        return fallback_terms
    
    def _clean_search_terms(self, search_terms: str) -> str:
        """🧹 LIMPIAR Y OPTIMIZAR TÉRMINOS DE BÚSQUEDA"""
        
        # Remover conectores al final
        connectors = ['en', 'y', 'con', 'para', 'sobre', 'de', 'del', 'la', 'el', 'los', 'las']
        words = search_terms.strip().split()
        
        # Remover conectores del final
        while words and words[-1].lower() in connectors:
            words.pop()
        
        # Remover conectores del inicio
        while words and words[0].lower() in connectors:
            words.pop(0)
        
        clean_terms = ' '.join(words)
        
        # Limitar longitud
        if len(clean_terms) > 60:
            clean_terms = clean_terms[:57] + "..."
        
        return clean_terms if clean_terms else "información relevante"
    
    def _start_screenshot_capture_thread(self, page, capture_interval: int, results: Dict[str, Any]):
        """📸 INICIAR HILO DE CAPTURA AUTOMÁTICA DE SCREENSHOTS"""
        
        def capture_screenshots():
            """Función que ejecuta en hilo separado para capturar screenshots"""
            screenshot_count = 0
            
            while self.is_navigating:
                try:
                    # Programar captura asíncrona
                    if page:
                        screenshot_path = asyncio.run_coroutine_threadsafe(
                            self._capture_screenshot_async(page, screenshot_count), 
                            asyncio.get_event_loop()
                        ).result(timeout=10)
                        
                        if screenshot_path:
                            # Registrar screenshot
                            screenshot_data = {
                                'index': screenshot_count,
                                'path': screenshot_path,
                                'url': page.url if hasattr(page, 'url') else 'unknown',
                                'timestamp': time.time()
                            }
                            
                            results['screenshots'].append(screenshot_data)
                            
                            # 📸 EMITIR EVENTO BROWSER_VISUAL INMEDIATO CON SCREENSHOT DE ALTA RESOLUCIÓN
                            self._emit_browser_visual({
                                'type': 'screenshot_captured_real',
                                'message': f'📸 Screenshot #{screenshot_count + 1} - Navegación en tiempo real',
                                'screenshot_url': screenshot_path,
                                'screenshot_index': screenshot_count,
                                'current_url': screenshot_data['url'],
                                'timestamp': time.time(),
                                'resolution': '1920x1080',  # Información de resolución
                                'quality': 'high',  # Indicador de calidad
                                'capture_type': 'real_time_navigation',
                                'step_description': f'Captura automática durante navegación web paso {screenshot_count + 1}'
                            })
                            
                            # 🚀 TAMBIÉN EMITIR COMO PROGRESS_UPDATE PARA MEJOR COMPATIBILIDAD
                            if self.websocket_manager:
                                try:
                                    self.websocket_manager.emit_to_task(self.task_id, 'progress_update', {
                                        'type': 'navigation_screenshot',
                                        'message': f'📸 Navegación web: Screenshot #{screenshot_count + 1} capturado',
                                        'screenshot_url': screenshot_path,
                                        'current_url': screenshot_data['url'],
                                        'timestamp': time.time()
                                    })
                                except Exception as e:
                                    self._emit_progress(f"⚠️ Error emitiendo progress_update: {str(e)}")
                            
                            screenshot_count += 1
                    
                    # Esperar antes de próxima captura
                    time.sleep(capture_interval)
                    
                except Exception as e:
                    self._emit_progress(f"⚠️ Error capturando screenshot: {str(e)}")
                    time.sleep(capture_interval)  # Continuar a pesar del error
        
        # Iniciar hilo de captura
        self.screenshot_thread = threading.Thread(target=capture_screenshots, daemon=True)
        self.screenshot_thread.start()
        
        self._emit_progress(f"📸 Hilo de captura automática iniciado (intervalo: {capture_interval}s)")
    
    async def _capture_screenshot_async(self, page, screenshot_index: int) -> Optional[str]:
        """📸 CAPTURAR SCREENSHOT ASÍNCRONO Y RETORNAR PATH"""
        
        try:
            # Crear directorio de screenshots si no existe
            screenshots_dir = Path(f"/tmp/screenshots/{self.task_id}")
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar nombre de archivo
            timestamp = int(time.time() * 1000)
            filename = f"real_navigation_{screenshot_index:03d}_{timestamp}.jpeg"
            screenshot_path = screenshots_dir / filename
            
            # Capturar screenshot de mayor calidad y resolución
            try:
                await page.screenshot(
                    path=str(screenshot_path),
                    quality=70,  # Mayor calidad (aumentado de 30 a 70)
                    type='jpeg',  # Usar JPEG para mejor compresión
                    full_page=False,  # Captura solo viewport para mejor rendimiento y calidad
                    clip={
                        'x': 0,
                        'y': 0, 
                        'width': 1920,  # Ancho fijo para consistencia
                        'height': 1080   # Alto fijo para mejor visualización
                    }
                )
            except Exception as e:
                self._emit_progress(f"⚠️ Error en captura de screenshot: {str(e)}")
                return None
            
            # Retornar URL accesible para frontend
            return f"/api/files/screenshots/{self.task_id}/{filename}"
            
        except Exception as e:
            self._emit_progress(f"⚠️ Error en captura async: {str(e)}")
            return None
    
    def _emit_browser_visual(self, data: Dict[str, Any]):
        """📡 EMITIR EVENTO BROWSER_VISUAL AL FRONTEND"""
        
        if self.websocket_manager and self.task_id:
            try:
                # Añadir task_id y timestamp si no están presentes
                enhanced_data = {
                    'task_id': self.task_id,
                    'timestamp': data.get('timestamp', time.time()),
                    **data
                }
                
                # Emitir evento browser_visual
                self.websocket_manager.emit_to_task(self.task_id, 'browser_visual', enhanced_data)
                
                # También emitir como actividad del agente para compatibilidad
                self.websocket_manager.emit_to_task(self.task_id, 'agent_activity', {
                    'type': 'browser_visual',
                    'message': data.get('message', 'Navegación en tiempo real'),
                    **enhanced_data
                })
                
            except Exception as e:
                print(f"⚠️ Error emitiendo browser_visual: {str(e)}")
    
    def _emit_progress(self, message: str):
        """📝 EMITIR MENSAJE DE PROGRESO"""
        
        print(f"[REAL_TIME_BROWSER] {message}")
        
        if self.websocket_manager and self.task_id:
            try:
                self.websocket_manager.emit_to_task(self.task_id, 'terminal_activity', {
                    'message': message,
                    'timestamp': time.time()
                })
            except Exception:
                pass  # Continuar silenciosamente si WebSocket falla
    
    def _cleanup_resources(self):
        """🧹 LIMPIAR RECURSOS Y CERRAR PROCESOS"""
        
        try:
            # Detener captura de screenshots
            self.is_navigating = False
            if self.screenshot_thread and self.screenshot_thread.is_alive():
                self.screenshot_thread.join(timeout=3)
            
            # Cerrar servidor X11 virtual SOLO SI LO CREAMOS NOSOTROS
            if self.xvfb_process:
                try:
                    self.xvfb_process.terminate()
                    self.xvfb_process.wait(timeout=5)
                    self._emit_progress("🔒 Servidor X11 virtual creado por nosotros cerrado")
                except:
                    # Forzar cierre si no responde
                    self.xvfb_process.kill()
                finally:
                    self.xvfb_process = None
            else:
                # Si no creamos el servidor, solo emitir que seguirá corriendo
                self._emit_progress("ℹ️ Servidor X11 virtual existente continúa corriendo")
            
            # Emitir evento de limpieza
            self._emit_browser_visual({
                'type': 'resources_cleaned',
                'message': '🧹 Recursos de navegación limpiados correctamente',
                'server_closed': self.xvfb_process is None,
                'timestamp': time.time()
            })
            
        except Exception as e:
            self._emit_progress(f"⚠️ Error durante limpieza: {str(e)}")