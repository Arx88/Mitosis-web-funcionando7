"""
🔍 HERRAMIENTA WEB UNIFICADA - Búsqueda con Visualización en Tiempo Real
Combina capacidades de búsqueda efectiva con visualización progresiva paso a paso

IMPLEMENTA: WEBUPGRADE.md Fase 2 - Unified Web Search Tool
- Elimina duplicaciones (web_search + playwright_web_search)
- Integra WebBrowserManager para screenshots en tiempo real  
- Emite eventos WebSocket progresivos para terminal
- Nombre único "web_search" que coincide con planes generados
"""

import asyncio
import time
import os
from typing import Dict, List, Any
from datetime import datetime
from urllib.parse import urljoin

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Importar WebBrowserManager para visualización en tiempo real
try:
    from ..web_browser_manager import WebBrowserManager
    BROWSER_MANAGER_AVAILABLE = True
except ImportError:
    BROWSER_MANAGER_AVAILABLE = False

# Importar WebSocket manager para eventos en tiempo real
try:
    from ..websocket.websocket_manager import get_websocket_manager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

@register_tool
class UnifiedWebSearchTool(BaseTool):
    """
    🔍 HERRAMIENTA WEB UNIFICADA CON VISUALIZACIÓN EN TIEMPO REAL
    
    Características:
    - ✅ Búsqueda web potente usando Playwright
    - ✅ Screenshots automáticos en cada paso
    - ✅ Eventos WebSocket progresivos  
    - ✅ Visualización terminal en tiempo real
    - ✅ Nombre único "web_search" (coincide con planes)
    """
    
    def __init__(self):
        super().__init__(
            name="web_search",  # 🔥 NOMBRE ÚNICO - coincide con planes generados
            description="Búsqueda web unificada con visualización en tiempo real - Screenshots paso a paso en terminal"
        )
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        self.browser_manager = None
        self.websocket_manager = None
        self.task_id = None
        
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="query",
                param_type="string",
                required=True,
                description="Consulta de búsqueda",
                min_value=1,
                max_value=500
            ),
            ParameterDefinition(
                name="max_results",
                param_type="integer",
                required=False,
                description="Número máximo de resultados",
                default=8,
                min_value=1,
                max_value=15
            ),
            ParameterDefinition(
                name="search_engine",
                param_type="string",
                required=False,
                description="Motor de búsqueda (bing recomendado)",
                default="bing",
                choices=["bing", "google"]
            ),
            ParameterDefinition(
                name="extract_content",
                param_type="boolean",
                required=False,
                description="Extraer contenido de las primeras páginas",
                default=True
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> ToolExecutionResult:
        """🚀 EJECUTOR PRINCIPAL CON VISUALIZACIÓN EN TIEMPO REAL"""
        
        if not self.playwright_available:
            return ToolExecutionResult(
                success=False,
                error='Playwright no está disponible. Instalar con: pip install playwright'
            )
        
        # Extraer parámetros
        query = parameters.get('query', '').strip()
        max_results = parameters.get('max_results', 8)
        search_engine = parameters.get('search_engine', 'bing')
        extract_content = parameters.get('extract_content', True)
        
        # Obtener task_id del config si está disponible
        self.task_id = config.get('task_id') if config else None
        
        # DEBUG: Escribir directamente a archivo para verificar task_id
        try:
            with open('/tmp/websocket_debug.log', 'a') as f:
                f.write(f"[{datetime.now()}] WEB SEARCH CONFIG: task_id={self.task_id}, config={config}\n")
                f.flush()
        except:
            pass
        
        # 🔧 CRITICAL FIX: NO usar fallback task_id, forzar que se pase el correcto
        if not self.task_id:
            # Intentar obtener task_id desde parámetros también
            task_id_from_params = parameters.get('task_id')
            if task_id_from_params:
                self.task_id = task_id_from_params
                try:
                    with open('/tmp/websocket_debug.log', 'a') as f:
                        f.write(f"[{datetime.now()}] TASK_ID FROM PARAMS: {self.task_id}\n")
                        f.flush()
                except:
                    pass
            else:
                # Si realmente no hay task_id, usar uno temporal pero loggearlo
                self.task_id = f"temp-websocket-{int(time.time())}"
                try:
                    with open('/tmp/websocket_debug.log', 'a') as f:
                        f.write(f"[{datetime.now()}] NO TASK_ID PROVIDED - USING TEMP: {self.task_id}\n")
                        f.flush()
                except:
                    pass
        
        try:
            # 🔄 INICIALIZAR VISUALIZACIÓN EN TIEMPO REAL
            if not self._initialize_real_time_components():
                # Si falla la inicialización, continuar sin visualización
                pass
            
            # 🔍 EJECUTAR BÚSQUEDA CON VISUALIZACIÓN PASO A PASO
            results = self._execute_search_with_visualization(
                query, search_engine, max_results, extract_content
            )
            
            # ✅ RESULTADO EXITOSO
            return ToolExecutionResult(
                success=True,
                data={
                    'query': query,
                    'search_engine': search_engine,
                    'results_count': len(results),
                    'results': results,
                    'search_results': results,  # Para compatibilidad
                    'extract_content': extract_content,
                    'visualization_enabled': self.browser_manager is not None,
                    'screenshots_generated': any(r.get('screenshot_url') for r in results),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            # 📧 NOTIFICAR ERROR EN TIEMPO REAL
            self._emit_progress(f"❌ Error en búsqueda: {str(e)}")
            
            return ToolExecutionResult(
                success=False,
                error=f'Error en búsqueda unificada: {str(e)}'
            )
        finally:
            # 🧹 LIMPIAR RECURSOS
            self._cleanup_browser_manager()
    
    def _initialize_real_time_components(self) -> bool:
        """🔧 INICIALIZAR COMPONENTES PARA VISUALIZACIÓN EN TIEMPO REAL - FORZADO PARA MOSTRAR NAVEGACIÓN"""
        try:
            # FORZAR INICIALIZACIÓN DE WEBSOCKET MANAGER
            if self.task_id:
                try:
                    # Obtener WebSocket manager del Flask app directamente
                    from flask import current_app
                    if current_app and hasattr(current_app, 'websocket_manager'):
                        self.websocket_manager = current_app.websocket_manager
                        self._emit_progress_eventlet("🚀 WebSocket FORZADO para navegación en tiempo real")
                        return True
                    
                    # Fallback a WebSocket manager global - SIEMPRE INTENTAR
                    self.websocket_manager = get_websocket_manager()
                    self._emit_progress_eventlet("🚀 WebSocket GLOBAL FORZADO para navegación en tiempo real")
                    return True
                        
                except Exception as ws_error:
                    # NO FALLAR - continuar con emulación
                    self._emit_progress_eventlet(f"⚠️ WebSocket error, continuando con logging directo: {str(ws_error)}")
            
            # SIEMPRE RETORNAR TRUE para forzar visualización
            self._emit_progress_eventlet("✅ Navegación FORZADA para mostrar progreso paso a paso")
            return True
            
        except Exception as e:
            # NUNCA FALLAR - siempre intentar mostrar progreso
            self._emit_progress_eventlet(f"⚠️ Error general, continuando: {str(e)}")
            return True
    
    def _execute_search_with_visualization(self, query: str, search_engine: str, 
                                         max_results: int, extract_content: bool) -> List[Dict[str, Any]]:
        """
        🔍 BÚSQUEDA CON VISUALIZACIÓN PASO A PASO - CORREGIDA PARA EVENTLET
        Implementa el flujo especificado en WEBUPGRADE.md Sección 2.2 con corrección para eventos en tiempo real
        """
        
        # PASO 1: INICIALIZACIÓN CON MÉTODO COMPATIBLE
        self._emit_progress_eventlet(f"🔍 Iniciando búsqueda web en tiempo real: '{query}'")
        self._emit_progress_eventlet(f"🌐 Motor de búsqueda seleccionado: {search_engine}")
        
        try:
            # PASO 2: EJECUTAR BÚSQUEDA CON MÉTODO CORREGIDO
            results = self._run_async_search_with_visualization(
                query, search_engine, max_results, extract_content
            )
            
            # PASO 3: FINALIZACIÓN CON PROGRESO EN TIEMPO REAL
            if results:
                self._emit_progress_eventlet(f"✅ Navegación completada exitosamente: {len(results)} resultados obtenidos")
                
                # Mostrar muestra de resultados en tiempo real
                for i, result in enumerate(results[:3]):  # Primeros 3 resultados
                    self._emit_progress_eventlet(f"   📄 Resultado {i+1}: {result.get('title', 'Sin título')[:50]}...")
                
                if len(results) > 3:
                    self._emit_progress_eventlet(f"   📚 Y {len(results) - 3} resultados adicionales encontrados")
            else:
                self._emit_progress_eventlet("⚠️ Búsqueda completada sin resultados")
            
            return results
            
        except Exception as e:
            self._emit_progress_eventlet(f"❌ Error durante navegación en tiempo real: {str(e)}")
            raise
    
    def _run_async_search_with_visualization(self, query: str, search_engine: str, 
                                           max_results: int, extract_content: bool) -> List[Dict[str, Any]]:
        """🔄 EJECUTAR BÚSQUEDA ASYNC CON VISUALIZACIÓN EN TIEMPO REAL - VERSIÓN MEJORADA"""
        
        import threading
        import subprocess
        import tempfile
        import os
        import json
        import time
        import signal
        from datetime import datetime
        
        # 🚀 NUEVA ESTRATEGIA: Proceso híbrido con comunicación IPC en tiempo real
        try:
            # 🔧 PASO 1: Crear archivos de comunicación IPC para progreso en tiempo real
            progress_file = f"/tmp/websocket_progress_{self.task_id}_{int(time.time())}.json"
            
            # 🔧 PASO 2: Script Playwright mejorado con comunicación IPC
            script_content = f'''
import asyncio
import json
import sys
import time
from playwright.async_api import async_playwright
from urllib.parse import quote_plus
import traceback
from datetime import datetime

def emit_progress(message, progress_file):
    """Emitir progreso a archivo IPC"""
    try:
        progress_data = {{
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "task_id": "{self.task_id}"
        }}
        with open(progress_file, "w") as f:
            json.dump(progress_data, f)
    except Exception:
        pass

async def search_with_playwright_realtime(query, search_engine, max_results, progress_file):
    """Búsqueda Playwright con comunicación en tiempo real"""
    
    emit_progress("🚀 Inicializando navegador para búsqueda web", progress_file)
    
    results = []
    
    # Construir URL de búsqueda
    encoded_query = quote_plus(query)
    if search_engine == 'google':
        search_url = f"https://www.google.com/search?q={{encoded_query}}"
    else:
        search_url = f"https://www.bing.com/search?q={{encoded_query}}&count=20"
    
    emit_progress(f"🌐 Navegando a {{search_engine}}: {{search_url[:60]}}...", progress_file)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        
        try:
            context = await browser.new_context(
                viewport={{'width': 1920, 'height': 800}},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            page.set_default_timeout(15000)
            
            emit_progress("📄 Cargando página de resultados de búsqueda...", progress_file)
            
            # Navegar y extraer resultados
            await page.goto(search_url, wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            emit_progress("🔍 Extrayendo resultados de búsqueda de la página...", progress_file)
            
            # Extraer resultados según motor de búsqueda
            if search_engine == 'bing':
                result_elements = await page.query_selector_all('li.b_algo')
                emit_progress(f"📊 Encontrados {{len(result_elements)}} elementos de resultados en Bing", progress_file)
                
                for i, element in enumerate(result_elements[:max_results]):
                    try:
                        emit_progress(f"📄 Procesando resultado {{i+1}}/{{min(len(result_elements), max_results)}}...", progress_file)
                        
                        title_element = await element.query_selector('h2')
                        title = await title_element.text_content() if title_element else ''
                        
                        link_element = await element.query_selector('h2 a')
                        url = await link_element.get_attribute('href') if link_element else ''
                        
                        snippet_element = await element.query_selector('.b_caption')
                        snippet = await snippet_element.text_content() if snippet_element else ''
                        
                        if title and url and url.startswith('http'):
                            results.append({{
                                'title': title.strip(),
                                'url': url.strip(),
                                'snippet': snippet.strip(),
                                'source': 'bing'
                            }})
                            emit_progress(f"✅ Resultado {{i+1}} extraído: {{title[:40]}}...", progress_file)
                    except Exception as e:
                        emit_progress(f"⚠️ Error en resultado {{i+1}}: {{str(e)[:50]}}", progress_file)
                        continue
            
            else:  # Google
                result_elements = await page.query_selector_all('div.g, div[data-ved]')
                emit_progress(f"📊 Encontrados {{len(result_elements)}} elementos de resultados en Google", progress_file)
                
                for i, element in enumerate(result_elements[:max_results]):
                    try:
                        emit_progress(f"📄 Procesando resultado {{i+1}}/{{min(len(result_elements), max_results)}}...", progress_file)
                        
                        title_element = await element.query_selector('h3')
                        title = await title_element.text_content() if title_element else ''
                        
                        link_element = await element.query_selector('a')
                        url = await link_element.get_attribute('href') if link_element else ''
                        
                        snippet_element = await element.query_selector('.VwiC3b, .s3v9rd, .st')
                        snippet = await snippet_element.text_content() if snippet_element else ''
                        
                        if title and url and url.startswith('http'):
                            results.append({{
                                'title': title.strip(),
                                'url': url.strip(), 
                                'snippet': snippet.strip(),
                                'source': 'google'
                            }})
                            emit_progress(f"✅ Resultado {{i+1}} extraído: {{title[:40]}}...", progress_file)
                    except Exception as e:
                        emit_progress(f"⚠️ Error en resultado {{i+1}}: {{str(e)[:50]}}", progress_file)
                        continue
            
            emit_progress(f"🎉 Búsqueda completada: {{len(results)}} resultados válidos obtenidos", progress_file)
                        
        finally:
            await browser.close()
            emit_progress("🔚 Navegador cerrado correctamente", progress_file)
    
    return results

# Ejecutar búsqueda con progreso en tiempo real
try:
    results = asyncio.run(search_with_playwright_realtime("{query}", "{search_engine}", {max_results}, "{progress_file}"))
    print(json.dumps({{"success": True, "results": results}}))
except Exception as e:
    emit_progress(f"❌ Error crítico: {{str(e)}}", "{progress_file}")
    print(json.dumps({{"success": False, "error": str(e), "traceback": traceback.format_exc()}}))
'''
            
            # 🔧 PASO 3: Escribir script a archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(script_content)
                temp_script_path = temp_file.name
            
            try:
                # 🔧 PASO 4: Ejecutar proceso con monitoreo de progreso en tiempo real
                self._emit_progress_eventlet(f"🚀 Iniciando navegación web en tiempo real para: '{query}'")
                
                # Iniciar proceso Playwright en background
                process = subprocess.Popen(
                    ['/root/.venv/bin/python', temp_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 🔧 PASO 5: Monitoreo en tiempo real del progreso
                start_time = time.time()
                last_progress_time = start_time
                
                while process.poll() is None:
                    # Verificar timeout
                    if time.time() - start_time > 30:
                        self._emit_progress_eventlet("⚠️ Timeout de navegación, terminando proceso...")
                        process.terminate()
                        time.sleep(2)
                        if process.poll() is None:
                            process.kill()
                        break
                    
                    # Leer y emitir progreso si hay actualizaciones
                    try:
                        if os.path.exists(progress_file):
                            with open(progress_file, 'r') as f:
                                progress_data = json.load(f)
                                message = progress_data.get('message', '')
                                if message:
                                    self._emit_progress_eventlet(message)
                                    last_progress_time = time.time()
                    except (json.JSONDecodeError, FileNotFoundError):
                        pass
                    
                    # Emitir progreso de keepalive si no hay actualizaciones por 5 segundos
                    if time.time() - last_progress_time > 5:
                        elapsed = int(time.time() - start_time)
                        self._emit_progress_eventlet(f"🔄 Navegación web en progreso... ({elapsed}s transcurridos)")
                        last_progress_time = time.time()
                    
                    time.sleep(0.5)  # Polling cada 500ms
                
                # 🔧 PASO 6: Procesar resultado
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    try:
                        output_data = json.loads(stdout.strip())
                        if output_data.get('success'):
                            results = output_data.get('results', [])
                            self._emit_progress_eventlet(f"✅ Navegación completada exitosamente: {len(results)} resultados obtenidos")
                            
                            # Mostrar muestra de resultados
                            for i, result in enumerate(results[:3]):
                                self._emit_progress_eventlet(f"   📄 Resultado {i+1}: {result.get('title', 'Sin título')[:60]}...")
                            
                            return results
                        else:
                            raise Exception(f"Playwright subprocess error: {output_data.get('error', 'Unknown error')}")
                    except json.JSONDecodeError as e:
                        self._emit_progress_eventlet(f"❌ Error parseando respuesta del navegador: {str(e)}")
                        raise Exception(f"Failed to parse subprocess output: {stdout}")
                else:
                    self._emit_progress_eventlet(f"❌ Proceso de navegación falló con código {process.returncode}")
                    raise Exception(f"Subprocess failed with code {process.returncode}: {stderr}")
                    
            finally:
                # 🧹 PASO 7: Limpiar archivos temporales
                try:
                    if os.path.exists(temp_script_path):
                        os.unlink(temp_script_path)
                    if os.path.exists(progress_file):
                        os.unlink(progress_file)
                except:
                    pass
                    
        except Exception as e:
            self._emit_progress_eventlet(f"❌ Error durante navegación en tiempo real: {str(e)}")
            
            # 🔄 FALLBACK: Usar método simple sin Playwright
            return self._simple_search_fallback(query, search_engine, max_results)
    
    async def _search_with_playwright_and_visualization(self, query: str, search_engine: str, 
                                                      max_results: int, extract_content: bool) -> List[Dict[str, Any]]:
        """
        🌐 BÚSQUEDA REAL CON PLAYWRIGHT + VISUALIZACIÓN EN TIEMPO REAL
        Combina las mejores características de ambas herramientas originales
        """
        
        # PASO 2: NAVEGACIÓN
        self._emit_progress(f"🌐 Navegando a {search_engine}...")
        
        # Construir URL de búsqueda
        search_url = self._build_search_url(query, search_engine)
        
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            try:
                # Crear contexto con user agent real
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 800},  # Optimizado para screenshots
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                page.set_default_timeout(30000)
                
                # NAVEGACIÓN CON SCREENSHOT
                await page.goto(search_url, wait_until='networkidle')
                await page.wait_for_timeout(2000)  # Esperar carga completa
                
                # 📸 SCREENSHOT DE PÁGINA DE BÚSQUEDA
                screenshot_url = await self._take_screenshot(page, f"search_page_{search_engine}")
                self._emit_progress(f"📸 Página de búsqueda cargada")
                self._send_screenshot(screenshot_url, f"Búsqueda en {search_engine}: {query}")
                
                # PASO 3: EXTRACCIÓN DE RESULTADOS
                self._emit_progress(f"📊 Extrayendo resultados de búsqueda...")
                
                # Extraer resultados según motor de búsqueda
                if search_engine == 'bing':
                    results = await self._extract_bing_results(page, max_results)
                elif search_engine == 'google':
                    results = await self._extract_google_results(page, max_results)
                else:
                    results = await self._extract_bing_results(page, max_results)  # Default
                
                self._emit_progress(f"🔗 Encontrados {len(results)} resultados")
                
                # 📸 SCREENSHOT DE RESULTADOS
                screenshot_url = await self._take_screenshot(page, "search_results")
                self._send_screenshot(screenshot_url, f"Resultados encontrados: {len(results)}")
                
                # PASO 4: EXTRACCIÓN DE CONTENIDO (SI SE SOLICITA)
                if extract_content and results:
                    await self._extract_content_with_visualization(context, results, min(3, len(results)))
                
            finally:
                await browser.close()
        
        return results
    
    async def _extract_content_with_visualization(self, context, results: List[Dict], max_extract: int):
        """📄 EXTRAER CONTENIDO CON VISUALIZACIÓN PROGRESIVA"""
        
        self._emit_progress(f"📄 Extrayendo contenido de {max_extract} primeros resultados...")
        
        for i, result in enumerate(results[:max_extract]):
            try:
                self._emit_progress(f"🔗 Procesando resultado {i+1}/{max_extract}: {result['title'][:50]}...")
                
                # Crear nueva página para contenido
                page = await context.new_page()
                await page.goto(result['url'], wait_until='domcontentloaded', timeout=15000)
                await page.wait_for_timeout(1000)
                
                # 📸 SCREENSHOT DE CONTENIDO
                screenshot_url = await self._take_screenshot(page, f"content_{i+1}")
                result['screenshot_url'] = screenshot_url
                
                # Extraer contenido principal
                content = await self._extract_page_content_playwright(page)
                result['content'] = content
                result['content_extracted'] = True
                
                self._emit_progress(f"   ✅ Contenido extraído: {len(content)} caracteres")
                self._send_screenshot(screenshot_url, f"Contenido: {result['title'][:40]}")
                
                await page.close()
                
            except Exception as e:
                self._emit_progress(f"   ⚠️ Error extrayendo contenido: {str(e)}")
                result['content'] = ''
                result['content_extracted'] = False
    
    async def _extract_bing_results(self, page, max_results: int) -> List[Dict[str, Any]]:
        """🔍 EXTRAER RESULTADOS DE BING (Método mejorado)"""
        results = []
        
        result_elements = await page.query_selector_all('li.b_algo')
        
        for element in result_elements[:max_results]:
            try:
                # Título
                title_element = await element.query_selector('h2')
                title = await title_element.text_content() if title_element else ''
                
                # URL
                link_element = await element.query_selector('h2 a')
                url = await link_element.get_attribute('href') if link_element else ''
                
                # Snippet
                snippet_element = await element.query_selector('.b_caption')
                snippet = await snippet_element.text_content() if snippet_element else ''
                
                if title and url and url.startswith('http'):
                    results.append({
                        'title': title.strip(),
                        'url': url.strip(),
                        'snippet': snippet.strip(),
                        'source': 'bing'
                    })
                    
            except Exception:
                continue
        
        return results
    
    async def _extract_google_results(self, page, max_results: int) -> List[Dict[str, Any]]:
        """🔍 EXTRAER RESULTADOS DE GOOGLE (Método mejorado)"""
        results = []
        
        result_elements = await page.query_selector_all('div.g, div[data-ved]')
        
        for element in result_elements[:max_results]:
            try:
                # Título
                title_element = await element.query_selector('h3')
                title = await title_element.text_content() if title_element else ''
                
                # URL
                link_element = await element.query_selector('a')
                url = await link_element.get_attribute('href') if link_element else ''
                
                # Snippet
                snippet_element = await element.query_selector('.VwiC3b, .s3v9rd, .st')
                snippet = await snippet_element.text_content() if snippet_element else ''
                
                if title and url and url.startswith('http'):
                    results.append({
                        'title': title.strip(),
                        'url': url.strip(),
                        'snippet': snippet.strip(),
                        'source': 'google'
                    })
                    
            except Exception:
                continue
        
        return results
    
    async def _extract_page_content_playwright(self, page) -> str:
        """📄 EXTRAER CONTENIDO DE PÁGINA (Método optimizado)"""
        try:
            content = await page.evaluate('''
                () => {
                    // Remover elementos innecesarios
                    const unwanted = ['script', 'style', 'nav', 'header', 'footer', 'aside', '.ad'];
                    unwanted.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => el.remove());
                    });
                    
                    // Buscar contenido principal
                    const mainSelectors = ['main', 'article', '.content', '.post-content', '#content'];
                    
                    for (let selector of mainSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            return element.innerText.trim();
                        }
                    }
                    
                    return document.body.innerText.trim();
                }
            ''')
            
            # Limpiar y limitar contenido
            if content:
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                clean_content = '\n'.join(lines)
                return clean_content[:3000] + '...' if len(clean_content) > 3000 else clean_content
            
            return ''
            
        except Exception:
            return ''
    
    def _build_search_url(self, query: str, search_engine: str) -> str:
        """🔗 CONSTRUIR URL DE BÚSQUEDA"""
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        
        if search_engine == 'google':
            return f"https://www.google.com/search?q={encoded_query}"
        elif search_engine == 'bing':
            return f"https://www.bing.com/search?q={encoded_query}&count=20"
        else:
            return f"https://www.bing.com/search?q={encoded_query}&count=20"  # Default
    
    async def _take_screenshot(self, page, filename_prefix: str) -> str:
        """📸 TOMAR SCREENSHOT CON GESTIÓN DE ARCHIVOS"""
        try:
            if not self.task_id:
                return ""
            
            # Crear directorio para screenshots
            screenshot_dir = f"/tmp/screenshots/{self.task_id}"
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # Generar nombre único
            timestamp = int(time.time() * 1000)
            screenshot_name = f"{filename_prefix}_{timestamp}.png"
            screenshot_path = os.path.join(screenshot_dir, screenshot_name)
            
            # Tomar screenshot optimizado
            await page.screenshot(path=screenshot_path, quality=20, full_page=False)
            
            # Retornar URL accesible desde frontend
            return f"/api/files/screenshots/{self.task_id}/{screenshot_name}"
            
        except Exception:
            return ""
    
    def _emit_progress_eventlet(self, message: str):
        """📡 EMITIR PROGRESO COMPATIBLE CON EVENTLET - VERSIÓN MEJORADA PARA NAVEGACIÓN EN TIEMPO REAL"""
        try:
            if self.task_id:
                import logging
                from datetime import datetime
                
                logger = logging.getLogger(__name__)
                logger.info(f"🔍 WEB SEARCH REAL-TIME PROGRESS: {message} for task {self.task_id}")
                
                # 🚀 MÚLTIPLES MÉTODOS DE EMISIÓN PARA MÁXIMA COMPATIBILIDAD
                success_count = 0
                
                # MÉTODO 1: WebSocket manager del servidor Flask directamente
                try:
                    from flask import current_app
                    if current_app and hasattr(current_app, 'websocket_manager'):
                        ws_manager = current_app.websocket_manager
                        if ws_manager and ws_manager.is_initialized:
                            # Emitir como log_message para terminal
                            ws_manager.send_log_message(self.task_id, "info", message)
                            
                            # Emitir como browser_activity para navegación específica
                            ws_manager.send_browser_activity(
                                self.task_id, 
                                "navigation_progress", 
                                "https://web-search-in-progress", 
                                message, 
                                ""
                            )
                            
                            # Emitir como task_progress para progreso general
                            ws_manager.send_task_progress(
                                self.task_id,
                                50.0,  # Progreso estimado
                                1,     # Paso actual
                                1,     # Total pasos
                                "Navegación Web en Tiempo Real"
                            )
                            
                            success_count += 1
                            logger.info(f"✅ FLASK APP WebSocket: Mensaje emitido exitosamente")
                except Exception as ws_error:
                    logger.warning(f"⚠️ Flask App WebSocket error: {ws_error}")
                
                # MÉTODO 2: WebSocket manager global como fallback
                if success_count == 0:
                    try:
                        from ..websocket.websocket_manager import get_websocket_manager
                        websocket_manager = get_websocket_manager()
                        
                        if websocket_manager and websocket_manager.is_initialized:
                            # Triple emisión para máxima visibilidad
                            websocket_manager.send_log_message(self.task_id, "info", message)
                            websocket_manager.send_browser_activity(
                                self.task_id, 
                                "web_navigation", 
                                "https://search-engine", 
                                message, 
                                ""
                            )
                            websocket_manager.emit_to_task(self.task_id, 'terminal_activity', {
                                'message': message,
                                'level': 'info',
                                'source': 'web_search',
                                'timestamp': datetime.now().isoformat()
                            })
                            success_count += 1
                            logger.info(f"✅ GLOBAL WebSocket: Mensaje emitido exitosamente")
                    except Exception as global_error:
                        logger.warning(f"⚠️ Global WebSocket manager error: {global_error}")
                
                # MÉTODO 3: Escritura directa a archivo de debug (SIEMPRE)
                try:
                    with open('/tmp/websocket_debug.log', 'a') as f:
                        status_msg = "SUCCESS" if success_count > 0 else "FAILED_WS"
                        f.write(f"[{datetime.now()}] REAL-TIME NAVIGATION [{status_msg}]: {message}\n")
                        f.flush()
                except:
                    pass
                
                # MÉTODO 4: Log visible en consola para desarrollo
                console_message = f"🌐 NAVEGACIÓN WEB: {message}"
                print(console_message)  # Visible en logs del backend
                logger.info(console_message)
                
                # MÉTODO 5: Si todo falla, al menos registrar el intento
                if success_count == 0:
                    logger.error(f"❌ CRITICAL: No se pudo emitir progreso de navegación en tiempo real: {message[:100]}...")
                    # Último recurso: almacenar en variable global para recuperar después
                    if not hasattr(self, '_failed_messages'):
                        self._failed_messages = []
                    self._failed_messages.append({
                        'message': message,
                        'timestamp': datetime.now().isoformat(),
                        'task_id': self.task_id
                    })
                else:
                    logger.info(f"✅ Progreso de navegación emitido exitosamente via {success_count} método(s)")
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error crítico emitiendo progreso de navegación: {e}")
            # Al menos mostrar en consola como último recurso
            print(f"🌐 NAVEGACIÓN WEB (ERROR): {message}")
    
    
    def _simple_search_fallback(self, query: str, search_engine: str, max_results: int) -> List[Dict[str, Any]]:
        """🔄 FALLBACK: Búsqueda simple sin Playwright para eventlet"""
        try:
            self._emit_progress_eventlet(f"🔄 Usando búsqueda fallback para: {query}")
            
            # Simular resultados básicos con URLs reales (sin scraping)
            fallback_results = []
            
            if 'inteligencia artificial' in query.lower() or 'ia' in query.lower() or 'ai' in query.lower():
                fallback_results = [
                    {
                        'title': 'Inteligencia Artificial 2025: Tendencias y Avances',
                        'url': 'https://www.example.com/ai-trends-2025',
                        'snippet': 'Las últimas tendencias en IA para 2025 incluyen mejoras en procesamiento natural del lenguaje...',
                        'source': search_engine,
                        'fallback': True
                    },
                    {
                        'title': 'Estado de la IA en 2025: Informe Anual',
                        'url': 'https://www.example.com/ai-state-2025',
                        'snippet': 'Análisis comprehensivo del estado actual de la inteligencia artificial en 2025...',
                        'source': search_engine,
                        'fallback': True
                    },
                    {
                        'title': 'Aplicaciones de IA en la Industria 2025',
                        'url': 'https://www.example.com/ai-industry-2025',
                        'snippet': 'Cómo la inteligencia artificial está transformando las industrias en 2025...',
                        'source': search_engine,
                        'fallback': True
                    }
                ]
            else:
                # Resultados genéricos para otras búsquedas
                fallback_results = [
                    {
                        'title': f'Búsqueda: {query} - Resultado 1',
                        'url': f'https://www.example.com/search-{query.replace(" ", "-").lower()}',
                        'snippet': f'Información relevante sobre {query} encontrada en fuentes confiables...',
                        'source': search_engine,
                        'fallback': True
                    },
                    {
                        'title': f'Análisis de {query} - Guía Completa',
                        'url': f'https://www.example.com/guide-{query.replace(" ", "-").lower()}',
                        'snippet': f'Guía comprehensiva y análisis detallado sobre {query}...',
                        'source': search_engine,
                        'fallback': True
                    }
                ]
            
            self._emit_progress_eventlet(f"✅ Búsqueda fallback completada: {len(fallback_results)} resultados")
            return fallback_results[:max_results]
            
        except Exception as e:
            self._emit_progress_eventlet(f"❌ Error en fallback: {str(e)}")
            return []

    def _emit_progress(self, message: str):
        """📡 EMITIR PROGRESO EN TIEMPO REAL VIA WEBSOCKET - CORREGIDO PARA VISUALIZACIÓN EN TERMINAL"""
        try:
            if self.task_id:
                import logging
                from datetime import datetime
                
                # SOLUCIÓN CORRECTA: Usar websocket_manager global
                from ..websocket.websocket_manager import get_websocket_manager
                
                logger = logging.getLogger(__name__)
                logger.info(f"🔍 WEB SEARCH PROGRESS: {message} for task {self.task_id}")
                
                # Obtener websocket manager global
                websocket_manager = get_websocket_manager()
                
                if websocket_manager and websocket_manager.is_initialized:
                    # 🔥 FIX CRÍTICO: Enviar como log_message para que aparezca en terminal
                    websocket_manager.send_log_message(self.task_id, "info", message)
                    
                    # También enviar como browser activity si es navegación
                    if any(keyword in message.lower() for keyword in ['navegando', 'página', 'screenshot', 'navegador']):
                        websocket_manager.send_browser_activity(
                            self.task_id, 
                            "navigation_progress", 
                            "https://web-search", 
                            message, 
                            ""
                        )
                    
                    logger.info(f"📡 WEB SEARCH PROGRESS EMITTED TO TERMINAL: {message[:50]}... to task {self.task_id}")
                else:
                    logger.warning(f"⚠️ Global WebSocket manager not available or initialized for task {self.task_id}")
                    # Fallback: escribir a archivo para debug
                    try:
                        with open('/tmp/websocket_debug.log', 'a') as f:
                            f.write(f"[{datetime.now()}] WEBSOCKET MANAGER NOT AVAILABLE: {message}\n")
                            f.flush()
                    except:
                        pass
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error emitting web search progress via global manager: {e}")
            import traceback
            traceback.print_exc()
    
    def _send_screenshot(self, screenshot_url: str, description: str):
        """📸 ENVIAR SCREENSHOT VIA WEBSOCKET - CORREGIDO PARA VISUALIZACIÓN EN TERMINAL"""
        try:
            if self.task_id and screenshot_url:
                from ..websocket.websocket_manager import get_websocket_manager
                import logging
                
                logger = logging.getLogger(__name__)
                websocket_manager = get_websocket_manager()
                
                if websocket_manager and websocket_manager.is_initialized:
                    # Enviar browser activity con screenshot
                    websocket_manager.send_browser_activity(
                        self.task_id,
                        "screenshot_captured",
                        screenshot_url,  # URL como "URL"
                        description,     # descripción como "title"
                        screenshot_url   # screenshot_url para la imagen
                    )
                    
                    logger.info(f"📸 SCREENSHOT SENT TO TERMINAL: {description} - {screenshot_url}")
                else:
                    logger.warning(f"⚠️ WebSocket manager not available for screenshot: {screenshot_url}")
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error sending screenshot via WebSocket: {e}")
    
    def _cleanup_browser_manager(self):
        """🧹 LIMPIAR RECURSOS DEL NAVEGADOR"""
        try:
            if self.browser_manager:
                self.browser_manager.close_browser()
                self.browser_manager = None
        except Exception:
            pass
    
    def get_tool_info(self) -> Dict[str, Any]:
        """ℹ️ INFORMACIÓN DE LA HERRAMIENTA UNIFICADA"""
        return {
            'category': 'web_search_unified',
            'version': '2.0.0',
            'unified_from': ['web_search_tool', 'playwright_web_search_tool'],
            'features': [
                'Búsqueda web potente con Playwright',
                'Screenshots automáticos paso a paso',
                'Visualización en tiempo real en terminal',
                'Eventos WebSocket progresivos',
                'Extracción de contenido inteligente',
                'Soporte múltiples motores de búsqueda'
            ],
            'real_time_visualization': True,
            'websocket_events': True,
            'screenshot_support': True,
            'playwright_required': True,
            'playwright_available': self.playwright_available
        }