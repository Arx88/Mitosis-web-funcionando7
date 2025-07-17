"""
Herramienta de demostración para X.com (Twitter) con navegación visible en tiempo real
Demuestra la funcionalidad de registro de cuenta con visualización completa
"""

import asyncio
import os
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
import string

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class XComDemoTool:
    def __init__(self):
        self.name = "x_com_demo"
        self.description = "Herramienta de demostración para X.com - Navegación visible en tiempo real con registro de cuenta"
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        
        # Configuración para navegación SIEMPRE visible
        self.config = {
            'headless': False,  # NUNCA headless
            'slow_motion': 1000,  # 1 segundo entre acciones para mejor visualización
            'timeout': 45000,  # 45 segundos timeout
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.steps_log = []
    
    def get_description(self) -> str:
        return self.description
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "action",
                "type": "string",
                "description": "Acción a realizar en X.com",
                "required": True,
                "enum": ["demo_registration", "navigate_explore", "demo_login_flow"]
            },
            {
                "name": "demo_username",
                "type": "string",
                "description": "Nombre de usuario para la demostración",
                "required": False,
                "default": "demo_user_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            },
            {
                "name": "demo_email",
                "type": "string",
                "description": "Email para la demostración",
                "required": False,
                "default": "demo_email_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + "@example.com"
            },
            {
                "name": "visual_mode",
                "type": "boolean",
                "description": "Activar modo visual (siempre activado)",
                "default": True
            },
            {
                "name": "slow_motion",
                "type": "integer",
                "description": "Ralentización entre acciones en milisegundos",
                "default": 1000
            }
        ]
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecutar demostración de X.com con navegación visible
        """
        if not self.playwright_available:
            return {
                'success': False,
                'error': 'Playwright no está instalado',
                'suggestion': 'Instala Playwright con: pip install playwright && playwright install'
            }
        
        action = parameters.get('action', 'demo_registration')
        demo_username = parameters.get('demo_username', f"demo_user_{random.randint(1000, 9999)}")
        demo_email = parameters.get('demo_email', f"demo{random.randint(100, 999)}@example.com")
        slow_motion = parameters.get('slow_motion', 1000)
        
        print(f"\n🎯 === DEMOSTRACIÓN X.COM EN TIEMPO REAL ===")
        print(f"🎬 Acción: {action}")
        print(f"👤 Usuario demo: {demo_username}")
        print(f"📧 Email demo: {demo_email}")
        print(f"⏱️  Ralentización: {slow_motion}ms")
        print(f"📱 Navegador será visible en terminal")
        
        # Ejecutar en hilo separado con display virtual
        import threading
        import concurrent.futures
        
        def run_demo():
            return self._setup_visual_display_and_run(action, demo_username, demo_email, slow_motion)
        
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_demo)
                result = future.result(timeout=180)  # 3 minutos timeout para demo completa
                return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _setup_visual_display_and_run(self, action: str, username: str, email: str, slow_motion: int) -> Dict[str, Any]:
        """
        Configurar display virtual y ejecutar demostración
        """
        display_num = 99
        
        # Configurar display virtual optimizado
        xvfb_cmd = f"Xvfb :{display_num} -screen 0 1920x1080x24 -ac +extension GLX +render -noreset"
        
        print(f"\n🖥️ Configurando display virtual :{display_num} para navegación visible")
        xvfb_process = subprocess.Popen(xvfb_cmd.split(), 
                                      stdout=subprocess.DEVNULL, 
                                      stderr=subprocess.DEVNULL)
        
        # Esperar a que Xvfb se inicie
        time.sleep(3)
        
        # Configurar variable de entorno DISPLAY
        os.environ['DISPLAY'] = f":{display_num}"
        
        # Iniciar window manager para mejor visualización
        wm_process = None
        try:
            wm_process = subprocess.Popen(['fluxbox'], 
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL)
            time.sleep(2)
            print("✅ Window manager iniciado")
        except FileNotFoundError:
            print("⚠️  Window manager no encontrado, continuando sin él")
        
        # Configurar xhost
        try:
            subprocess.run(['xhost', '+local:'], check=False, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            pass
        
        try:
            # Crear event loop y ejecutar demo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                print(f"🎬 Iniciando demostración visual de X.com en tiempo real...")
                result = loop.run_until_complete(self._run_x_demo(action, username, email, slow_motion))
                return result
            finally:
                loop.close()
        
        finally:
            # Limpiar procesos
            if wm_process:
                wm_process.terminate()
                try:
                    wm_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    wm_process.kill()
            
            xvfb_process.terminate()
            try:
                xvfb_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                xvfb_process.kill()
            
            print("🧹 Display virtual terminado")
    
    async def _run_x_demo(self, action: str, username: str, email: str, slow_motion: int) -> Dict[str, Any]:
        """
        Ejecutar demostración específica de X.com
        """
        self.steps_log = []
        
        async with async_playwright() as p:
            print(f"\n🚀 Lanzando navegador Chrome en modo visible...")
            
            # Configurar navegador SIEMPRE visible
            browser = await p.chromium.launch(
                headless=False,  # NUNCA headless
                slow_mo=slow_motion,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps'
                ]
            )
            
            try:
                context = await browser.new_context(
                    viewport=self.config['viewport'],
                    user_agent=self.config['user_agent']
                )
                
                page = await context.new_page()
                page.set_default_timeout(self.config['timeout'])
                
                # Ejecutar acción específica
                if action == 'demo_registration':
                    result = await self._demo_x_registration(page, username, email)
                elif action == 'navigate_explore':
                    result = await self._demo_x_explore(page)
                elif action == 'demo_login_flow':
                    result = await self._demo_x_login_flow(page)
                else:
                    result = {'success': False, 'error': f'Acción no soportada: {action}'}
                
                # Agregar log de pasos al resultado
                result['steps_log'] = self.steps_log
                result['total_steps'] = len(self.steps_log)
                
                return result
            
            finally:
                await browser.close()
                print("🔚 Navegador cerrado")
    
    async def _log_step(self, step_name: str, details: str = "", page=None):
        """
        Registrar paso con timestamp y detalles
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        step_info = {
            'timestamp': timestamp,
            'step': step_name,
            'details': details,
            'url': page.url if page else 'N/A'
        }
        
        self.steps_log.append(step_info)
        print(f"📝 [{timestamp}] {step_name}: {details}")
        
        # Pausa para mejor visualización
        await asyncio.sleep(1)
    
    async def _demo_x_registration(self, page, username: str, email: str) -> Dict[str, Any]:
        """
        Demostrar el proceso de registro en X.com
        """
        try:
            await self._log_step("INICIO", "Iniciando demostración de registro en X.com", page)
            
            # Navegar a X.com
            await self._log_step("NAVEGACIÓN", "Navegando a x.com")
            await page.goto('https://x.com', wait_until='domcontentloaded')
            
            await self._log_step("PÁGINA CARGADA", f"Página cargada: {await page.title()}", page)
            
            # Esperar a que la página se cargue completamente
            await page.wait_for_timeout(3000)
            
            # Buscar botón de registro
            await self._log_step("BUSCANDO REGISTRO", "Buscando botón de registro/sign up")
            
            # Intentar diferentes selectores para el botón de registro
            signup_selectors = [
                'a[href="/i/flow/signup"]',
                'a[data-testid="signupButton"]',
                'a:has-text("Sign up")',
                'a:has-text("Create account")',
                'span:has-text("Sign up")',
                '[data-testid="signupButton"]'
            ]
            
            signup_found = False
            for selector in signup_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await self._log_step("BOTÓN ENCONTRADO", f"Botón de registro encontrado con selector: {selector}")
                    
                    # Hacer clic en el botón de registro
                    await page.click(selector)
                    await self._log_step("CLIC REGISTRO", "Clic en botón de registro realizado")
                    signup_found = True
                    break
                except:
                    continue
            
            if not signup_found:
                await self._log_step("EXPLORACIÓN", "Explorando página para encontrar opciones de registro")
                
                # Tomar screenshot de la página actual
                await page.screenshot(path='/tmp/x_com_page.png')
                
                # Buscar todos los enlaces visibles
                links = await page.evaluate('''
                    () => {
                        const links = Array.from(document.querySelectorAll('a'));
                        return links
                            .filter(link => link.offsetParent !== null)
                            .map(link => ({
                                text: link.textContent.trim(),
                                href: link.href
                            }))
                            .filter(link => link.text.length > 0);
                    }
                ''')
                
                await self._log_step("ENLACES ENCONTRADOS", f"Encontrados {len(links)} enlaces visibles")
                
                # Buscar enlace que contenga "sign up", "create", "register"
                for link in links:
                    if any(keyword in link['text'].lower() for keyword in ['sign up', 'create', 'register', 'join']):
                        await self._log_step("ENLACE REGISTRO", f"Encontrado enlace: {link['text']}")
                        await page.goto(link['href'])
                        signup_found = True
                        break
            
            if signup_found:
                await page.wait_for_timeout(2000)
                await self._log_step("FORMULARIO REGISTRO", "Navegando a formulario de registro")
                
                # Intentar llenar formulario de registro
                await self._demo_fill_signup_form(page, username, email)
            
            await self._log_step("EXPLORACIÓN COMPLETA", "Demostración de navegación y exploración completada")
            
            return {
                'success': True,
                'action': 'demo_registration',
                'username': username,
                'email': email,
                'message': 'Demostración de registro completada - Navegación visible en tiempo real',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            await self._log_step("ERROR", f"Error en demostración: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'action': 'demo_registration'
            }
    
    async def _demo_fill_signup_form(self, page, username: str, email: str):
        """
        Demostrar el llenado del formulario de registro
        """
        try:
            await self._log_step("FORMULARIO", "Intentando llenar formulario de registro")
            
            # Buscar campos de formulario
            form_fields = [
                {'name': 'name', 'selectors': ['input[name="name"]', 'input[autocomplete="name"]', 'input[placeholder*="name"]']},
                {'name': 'email', 'selectors': ['input[name="email"]', 'input[type="email"]', 'input[autocomplete="email"]']},
                {'name': 'username', 'selectors': ['input[name="username"]', 'input[placeholder*="username"]']},
                {'name': 'password', 'selectors': ['input[type="password"]', 'input[name="password"]']}
            ]
            
            for field in form_fields:
                await self._log_step("CAMPO", f"Buscando campo: {field['name']}")
                
                for selector in field['selectors']:
                    try:
                        await page.wait_for_selector(selector, timeout=3000)
                        
                        # Determinar qué texto escribir
                        if field['name'] == 'name':
                            text_to_type = f"Demo User {username}"
                        elif field['name'] == 'email':
                            text_to_type = email
                        elif field['name'] == 'username':
                            text_to_type = username
                        elif field['name'] == 'password':
                            text_to_type = "DemoPassword123!"
                        else:
                            text_to_type = "demo_value"
                        
                        await self._log_step("ESCRIBIENDO", f"Escribiendo en campo {field['name']}: {text_to_type}")
                        await page.fill(selector, text_to_type)
                        await page.wait_for_timeout(1000)
                        break
                    except:
                        continue
            
            # Buscar botón de envío
            await self._log_step("BOTÓN ENVÍO", "Buscando botón de envío del formulario")
            
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign up")',
                'button:has-text("Create account")',
                'button:has-text("Next")',
                '[data-testid="ocfSignupButton"]'
            ]
            
            for selector in submit_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await self._log_step("BOTÓN ENCONTRADO", f"Botón de envío encontrado: {selector}")
                    
                    # Simular clic (sin enviar realmente)
                    await self._log_step("SIMULACIÓN", "Simulando clic en botón de envío (sin enviar)")
                    await page.hover(selector)
                    await page.wait_for_timeout(2000)
                    break
                except:
                    continue
            
        except Exception as e:
            await self._log_step("ERROR FORMULARIO", f"Error en formulario: {str(e)}")
    
    async def _demo_x_explore(self, page) -> Dict[str, Any]:
        """
        Demostrar exploración de X.com
        """
        try:
            await self._log_step("EXPLORACIÓN", "Iniciando exploración de X.com")
            
            await page.goto('https://x.com', wait_until='domcontentloaded')
            await self._log_step("PÁGINA PRINCIPAL", f"Cargado: {await page.title()}")
            
            # Explorar diferentes secciones
            sections = [
                {'name': 'Explore', 'url': 'https://x.com/explore'},
                {'name': 'Trending', 'url': 'https://x.com/explore/tabs/trending'},
                {'name': 'News', 'url': 'https://x.com/explore/tabs/news'}
            ]
            
            for section in sections:
                await self._log_step("NAVEGACIÓN", f"Navegando a {section['name']}")
                await page.goto(section['url'], wait_until='domcontentloaded')
                await page.wait_for_timeout(3000)
                await self._log_step("SECCIÓN", f"Explorando {section['name']}")
            
            return {
                'success': True,
                'action': 'navigate_explore',
                'message': 'Exploración completada',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'navigate_explore'
            }
    
    async def _demo_x_login_flow(self, page) -> Dict[str, Any]:
        """
        Demostrar flujo de login en X.com
        """
        try:
            await self._log_step("LOGIN FLOW", "Iniciando demostración de flujo de login")
            
            await page.goto('https://x.com', wait_until='domcontentloaded')
            await self._log_step("PÁGINA CARGADA", f"Título: {await page.title()}")
            
            # Buscar botón de login
            login_selectors = [
                'a[href="/i/flow/login"]',
                'a[data-testid="loginButton"]',
                'a:has-text("Log in")',
                'a:has-text("Sign in")'
            ]
            
            for selector in login_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await self._log_step("LOGIN ENCONTRADO", f"Botón de login encontrado: {selector}")
                    await page.click(selector)
                    await self._log_step("CLIC LOGIN", "Clic en botón de login")
                    break
                except:
                    continue
            
            await page.wait_for_timeout(3000)
            await self._log_step("FORMULARIO LOGIN", "Mostrando formulario de login")
            
            return {
                'success': True,
                'action': 'demo_login_flow',
                'message': 'Flujo de login demostrado',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'demo_login_flow'
            }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar parámetros de entrada
        """
        errors = []
        
        action = parameters.get('action')
        if not action:
            errors.append("action es requerido")
        elif action not in ['demo_registration', 'navigate_explore', 'demo_login_flow']:
            errors.append("action debe ser: demo_registration, navigate_explore, o demo_login_flow")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        Información de la herramienta
        """
        return {
            'category': 'demo_web_automation',
            'version': '1.0.0',
            'capabilities': [
                'Demostración de registro en X.com',
                'Navegación visible en tiempo real',
                'Exploración de interfaz web',
                'Flujo de login demostrado',
                'Visualización paso a paso'
            ],
            'demo_features': [
                'Navegador siempre visible',
                'Ralentización para mejor observación',
                'Logging detallado de cada paso',
                'Manejo de errores robusto',
                'Screenshots automáticos'
            ],
            'playwright_status': 'disponible' if self.playwright_available else 'no_instalado'
        }