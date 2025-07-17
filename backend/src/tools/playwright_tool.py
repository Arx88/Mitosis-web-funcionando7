"""
Herramienta de Automatización de Navegadores con Playwright VISUAL
Para scraping avanzado y automatización web con feedback visual en tiempo real
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import base64
import tempfile
from pathlib import Path
import time

# Playwright será instalado como dependencia
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright")

class PlaywrightTool:
    def __init__(self):
        self.name = "playwright_automation"
        self.description = "Herramienta de automatización de navegadores con Playwright VISUAL - Muestra interacciones paso a paso"
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        
        # Configuración por defecto
        self.default_config = {
            'headless': False,  # Cambiado a False para ser más visual por defecto
            'timeout': 30000,  # 30 segundos
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'visual_mode': True,  # Nuevo: modo visual activado por defecto
            'step_screenshots': True,  # Nuevo: screenshots automáticos en cada paso
            'highlight_elements': True,  # Nuevo: resaltar elementos antes de interactuar
            'slow_motion': 500  # Nuevo: ralentizar acciones para mejor visualización (ms)
        }
        
        # Lista para almacenar todos los pasos visuales
        self.visual_steps = []
    
    def get_description(self) -> str:
        return self.description
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "action",
                "type": "string",
                "description": "Acción a realizar",
                "required": True,
                "enum": ["navigate", "screenshot", "extract_text", "extract_links", "fill_form", "click_element", "scroll_page", "wait_for_element", "execute_script", "get_page_info"]
            },
            {
                "name": "url",
                "type": "string",
                "description": "URL de la página web",
                "required": True
            },
            {
                "name": "selector",
                "type": "string",
                "description": "Selector CSS para elementos específicos",
                "required": False
            },
            {
                "name": "text",
                "type": "string",
                "description": "Texto para rellenar campos o buscar",
                "required": False
            },
            {
                "name": "script",
                "type": "string",
                "description": "JavaScript para ejecutar en la página",
                "required": False
            },
            {
                "name": "wait_for",
                "type": "string",
                "description": "Selector o condición para esperar",
                "required": False
            },
            {
                "name": "timeout",
                "type": "integer",
                "description": "Tiempo límite en milisegundos",
                "default": 30000
            },
            {
                "name": "headless",
                "type": "boolean",
                "description": "Ejecutar en modo headless",
                "default": True
            },
            {
                "name": "full_page",
                "type": "boolean",
                "description": "Captura de pantalla completa",
                "default": False
            },
            {
                "name": "viewport_width",
                "type": "integer",
                "description": "Ancho del viewport",
                "default": 1920
            },
            {
                "name": "visual_mode",
                "type": "boolean",
                "description": "Activar modo visual (no-headless + screenshots automáticos)",
                "default": True
            },
            {
                "name": "step_screenshots",
                "type": "boolean", 
                "description": "Tomar screenshots automáticos en cada paso",
                "default": True
            },
            {
                "name": "highlight_elements",
                "type": "boolean",
                "description": "Resaltar elementos antes de interactuar",
                "default": True
            },
            {
                "name": "slow_motion",
                "type": "integer",
                "description": "Ralentizar acciones para mejor visualización (milisegundos)",
                "default": 500
            }
        ]
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecutar automatización con Playwright
        
        Args:
            parameters: Parámetros de la herramienta
            config: Configuración adicional
            
        Returns:
            Resultado de la automatización
        """
        try:
            if not self.playwright_available:
                return {
                    'success': False,
                    'error': 'Playwright not installed',
                    'suggestion': 'Install Playwright with: pip install playwright && playwright install'
                }
            
            action = parameters.get('action')
            url = parameters.get('url')
            
            if not url:
                return {
                    'success': False,
                    'error': 'URL is required'
                }
            
            # Validar URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Ejecutar acción usando asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(self._execute_action(action, url, parameters))
                return result
            finally:
                loop.close()
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _log_visual_step(self, page, step_name: str, details: str = "", screenshot: bool = True) -> Dict[str, Any]:
        """Registrar paso visual con screenshot y logs detallados"""
        timestamp = datetime.now().isoformat()
        
        print(f"\n🎬 [{timestamp}] PASO VISUAL: {step_name}")
        print(f"   📄 URL: {page.url}")
        print(f"   📝 Detalles: {details}")
        
        step_data = {
            'step': step_name,
            'details': details,
            'url': page.url,
            'timestamp': timestamp
        }
        
        if screenshot:
            try:
                # Crear screenshot del paso
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    screenshot_path = tmp_file.name
                
                await page.screenshot(path=screenshot_path, full_page=False)
                
                # Convertir a base64
                with open(screenshot_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                os.unlink(screenshot_path)
                
                step_data['screenshot'] = image_data
                print(f"   📸 Screenshot capturado")
                
            except Exception as e:
                print(f"   ⚠️  Error capturando screenshot: {e}")
        
        self.visual_steps.append(step_data)
        return step_data
    
    async def _highlight_element(self, page, selector: str) -> bool:
        """Resaltar elemento antes de interactuar con él"""
        try:
            await page.evaluate(f'''
                (selector) => {{
                    const element = document.querySelector(selector);
                    if (element) {{
                        element.style.outline = '3px solid #ff6b6b';
                        element.style.backgroundColor = 'rgba(255, 107, 107, 0.1)';
                        element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                        return true;
                    }}
                    return false;
                }}
            ''', selector)
            
            # Esperar un poco para que se vea el resaltado
            await page.wait_for_timeout(800)
            return True
            
        except Exception as e:
            print(f"   ⚠️  No se pudo resaltar elemento {selector}: {e}")
            return False
    
    async def _remove_highlight(self, page, selector: str):
        """Quitar resaltado del elemento"""
        try:
            await page.evaluate(f'''
                (selector) => {{
                    const element = document.querySelector(selector);
                    if (element) {{
                        element.style.outline = '';
                        element.style.backgroundColor = '';
                    }}
                }}
            ''', selector)
        except:
            pass

    async def _execute_action(self, action: str, url: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar acción específica"""
        async with async_playwright() as p:
            # Configurar navegador
            browser = await p.chromium.launch(
                headless=parameters.get('headless', self.default_config['headless'])
            )
            
            try:
                # Crear contexto
                context = await browser.new_context(
                    viewport={
                        'width': parameters.get('viewport_width', self.default_config['viewport']['width']),
                        'height': parameters.get('viewport_height', self.default_config['viewport']['height'])
                    },
                    user_agent=self.default_config['user_agent']
                )
                
                # Crear página
                page = await context.new_page()
                
                # Configurar timeout
                timeout = parameters.get('timeout', self.default_config['timeout'])
                page.set_default_timeout(timeout)
                
                # Navegar a la URL
                await page.goto(url, wait_until='domcontentloaded')
                
                # Ejecutar acción específica
                if action == 'navigate':
                    return await self._navigate(page, parameters)
                elif action == 'screenshot':
                    return await self._screenshot(page, parameters)
                elif action == 'extract_text':
                    return await self._extract_text(page, parameters)
                elif action == 'extract_links':
                    return await self._extract_links(page, parameters)
                elif action == 'fill_form':
                    return await self._fill_form(page, parameters)
                elif action == 'click_element':
                    return await self._click_element(page, parameters)
                elif action == 'scroll_page':
                    return await self._scroll_page(page, parameters)
                elif action == 'wait_for_element':
                    return await self._wait_for_element(page, parameters)
                elif action == 'execute_script':
                    return await self._execute_script(page, parameters)
                elif action == 'get_page_info':
                    return await self._get_page_info(page, parameters)
                else:
                    return {
                        'success': False,
                        'error': f'Invalid action: {action}'
                    }
            
            finally:
                await browser.close()
    
    async def _navigate(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Navegar a página"""
        try:
            wait_for = parameters.get('wait_for')
            if wait_for:
                await page.wait_for_selector(wait_for)
            
            title = await page.title()
            url = page.url
            
            return {
                'success': True,
                'action': 'navigate',
                'url': url,
                'title': title,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Navigation failed: {str(e)}'
            }
    
    async def _screenshot(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Capturar pantalla"""
        try:
            full_page = parameters.get('full_page', False)
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                screenshot_path = tmp_file.name
            
            # Capturar pantalla
            await page.screenshot(
                path=screenshot_path,
                full_page=full_page
            )
            
            # Convertir a base64
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Limpiar archivo temporal
            os.unlink(screenshot_path)
            
            return {
                'success': True,
                'action': 'screenshot',
                'url': page.url,
                'image_data': image_data,
                'image_format': 'png',
                'full_page': full_page,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Screenshot failed: {str(e)}'
            }
    
    async def _extract_text(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer texto de la página"""
        try:
            selector = parameters.get('selector')
            
            if selector:
                # Extraer texto de elemento específico
                elements = await page.query_selector_all(selector)
                texts = []
                
                for element in elements:
                    text = await element.text_content()
                    if text:
                        texts.append(text.strip())
                
                return {
                    'success': True,
                    'action': 'extract_text',
                    'selector': selector,
                    'texts': texts,
                    'count': len(texts),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Extraer todo el texto de la página
                text = await page.text_content('body')
                
                return {
                    'success': True,
                    'action': 'extract_text',
                    'text': text.strip() if text else '',
                    'length': len(text) if text else 0,
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Text extraction failed: {str(e)}'
            }
    
    async def _extract_links(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer enlaces de la página"""
        try:
            # Obtener todos los enlaces
            links = await page.evaluate('''
                () => {
                    const links = [];
                    const anchors = document.querySelectorAll('a[href]');
                    
                    anchors.forEach(anchor => {
                        links.push({
                            href: anchor.href,
                            text: anchor.textContent.trim(),
                            title: anchor.title || '',
                            target: anchor.target || ''
                        });
                    });
                    
                    return links;
                }
            ''')
            
            # Filtrar enlaces válidos
            valid_links = []
            for link in links:
                if link['href'] and link['href'].startswith(('http://', 'https://')):
                    valid_links.append(link)
            
            return {
                'success': True,
                'action': 'extract_links',
                'links': valid_links,
                'count': len(valid_links),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Link extraction failed: {str(e)}'
            }
    
    async def _fill_form(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Rellenar formulario"""
        try:
            selector = parameters.get('selector')
            text = parameters.get('text')
            
            if not selector or not text:
                return {
                    'success': False,
                    'error': 'Both selector and text are required for fill_form'
                }
            
            # Esperar elemento
            await page.wait_for_selector(selector)
            
            # Rellenar campo
            await page.fill(selector, text)
            
            return {
                'success': True,
                'action': 'fill_form',
                'selector': selector,
                'text': text,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Form filling failed: {str(e)}'
            }
    
    async def _click_element(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Hacer clic en elemento"""
        try:
            selector = parameters.get('selector')
            
            if not selector:
                return {
                    'success': False,
                    'error': 'Selector is required for click_element'
                }
            
            # Esperar elemento
            await page.wait_for_selector(selector)
            
            # Hacer clic
            await page.click(selector)
            
            return {
                'success': True,
                'action': 'click_element',
                'selector': selector,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Click failed: {str(e)}'
            }
    
    async def _scroll_page(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Hacer scroll en la página"""
        try:
            # Scroll hasta el final de la página
            await page.evaluate('''
                () => {
                    window.scrollTo(0, document.body.scrollHeight);
                }
            ''')
            
            # Esperar un poco para que se cargue contenido dinámico
            await page.wait_for_timeout(2000)
            
            return {
                'success': True,
                'action': 'scroll_page',
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Scroll failed: {str(e)}'
            }
    
    async def _wait_for_element(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Esperar elemento"""
        try:
            selector = parameters.get('selector')
            
            if not selector:
                return {
                    'success': False,
                    'error': 'Selector is required for wait_for_element'
                }
            
            # Esperar elemento
            await page.wait_for_selector(selector)
            
            return {
                'success': True,
                'action': 'wait_for_element',
                'selector': selector,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Wait failed: {str(e)}'
            }
    
    async def _execute_script(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar JavaScript"""
        try:
            script = parameters.get('script')
            
            if not script:
                return {
                    'success': False,
                    'error': 'Script is required for execute_script'
                }
            
            # Ejecutar script
            result = await page.evaluate(script)
            
            return {
                'success': True,
                'action': 'execute_script',
                'script': script,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Script execution failed: {str(e)}'
            }
    
    async def _get_page_info(self, page, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener información de la página"""
        try:
            # Obtener información básica
            title = await page.title()
            url = page.url
            
            # Obtener metadatos
            metadata = await page.evaluate('''
                () => {
                    const metas = {};
                    const metaTags = document.querySelectorAll('meta');
                    
                    metaTags.forEach(meta => {
                        if (meta.name) {
                            metas[meta.name] = meta.content;
                        } else if (meta.property) {
                            metas[meta.property] = meta.content;
                        }
                    });
                    
                    return metas;
                }
            ''')
            
            # Obtener estadísticas
            stats = await page.evaluate('''
                () => {
                    return {
                        links: document.querySelectorAll('a[href]').length,
                        images: document.querySelectorAll('img').length,
                        forms: document.querySelectorAll('form').length,
                        inputs: document.querySelectorAll('input').length,
                        buttons: document.querySelectorAll('button').length,
                        textLength: document.body.textContent.length
                    };
                }
            ''')
            
            return {
                'success': True,
                'action': 'get_page_info',
                'title': title,
                'url': url,
                'metadata': metadata,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Page info extraction failed: {str(e)}'
            }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros de entrada"""
        errors = []
        
        # Validar acción
        action = parameters.get('action')
        if not action:
            errors.append("action is required")
        elif action not in ['navigate', 'screenshot', 'extract_text', 'extract_links', 'fill_form', 'click_element', 'scroll_page', 'wait_for_element', 'execute_script', 'get_page_info']:
            errors.append("Invalid action")
        
        # Validar URL
        url = parameters.get('url')
        if not url:
            errors.append("URL is required")
        elif not isinstance(url, str):
            errors.append("URL must be a string")
        
        # Validaciones específicas por acción
        if action in ['fill_form']:
            if not parameters.get('selector'):
                errors.append("selector is required for fill_form")
            if not parameters.get('text'):
                errors.append("text is required for fill_form")
        
        if action in ['click_element', 'wait_for_element']:
            if not parameters.get('selector'):
                errors.append("selector is required for this action")
        
        if action == 'execute_script':
            if not parameters.get('script'):
                errors.append("script is required for execute_script")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información adicional de la herramienta"""
        return {
            'category': 'web_automation',
            'version': '1.0.0',
            'capabilities': [
                'Browser automation',
                'Dynamic content scraping',
                'Form filling',
                'Screenshot capture',
                'JavaScript execution',
                'Element interaction'
            ],
            'advantages': [
                'Handles JavaScript-rendered content',
                'Real browser environment',
                'Advanced interaction capabilities',
                'Screenshot and visual testing',
                'Modern web standards support'
            ],
            'playwright_status': 'available' if self.playwright_available else 'not_installed'
        }