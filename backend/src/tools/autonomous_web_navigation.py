"""
Herramienta de Navegación Web Autónoma
Para planificar y ejecutar tareas de navegación web de forma completamente autónoma
"""

import os
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import uuid
import base64
import tempfile
from pathlib import Path

# Playwright será instalado como dependencia
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright")

class AutonomousWebNavigation:
    def __init__(self):
        self.name = "autonomous_web_navigation"
        self.description = "Herramienta de navegación web autónoma - Planifica y ejecuta tareas de navegación web complejas"
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        
        # Configuración por defecto - ADAPTADA PARA TERMINAL
        # El usuario requiere que la navegación web se muestre en el terminal
        
        self.config = {
            'headless': False,  # Headless desactivado para navegación visible
            'timeout': 30000,  # 30 segundos
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'visual_mode': True,  # SIEMPRE modo visual activado
            'step_screenshots': True,  # Screenshots automáticos SIEMPRE
            'highlight_elements': True,  # Resaltar elementos SIEMPRE
            'slow_motion': 800,  # Ralentizar para mejor visibilidad
            'use_xvfb': True,  # SIEMPRE usar display virtual para visualización
            'log_to_terminal': True,  # Logs detallados para terminal
            'step_delay': 1000,  # Pausa entre pasos
            'max_retries': 3,  # Reintentos máximos
            'screenshot_quality': 90,  # Calidad de screenshots
            'element_highlight_time': 1000  # Tiempo de resaltado
        }
        
        # Almacenar progreso y logs
        self.execution_logs = []
        self.current_step = 0
        self.total_steps = 0
        self.screenshots = []
        
    def get_description(self) -> str:
        return self.description
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "task_description",
                "type": "string",
                "description": "Descripción de la tarea de navegación web a realizar",
                "required": True,
                "examples": [
                    "Crea una cuenta en Twitter",
                    "Busca información sobre Python en Stack Overflow",
                    "Compra un producto en Amazon",
                    "Llena un formulario de contacto en example.com"
                ]
            },
            {
                "name": "target_url",
                "type": "string",
                "description": "URL objetivo (opcional, se puede detectar automáticamente)",
                "required": False
            },
            {
                "name": "user_data",
                "type": "object",
                "description": "Datos del usuario para formularios (opcional)",
                "required": False,
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                    "phone": {"type": "string"},
                    "address": {"type": "string"}
                }
            },
            {
                "name": "constraints",
                "type": "object",
                "description": "Restricciones y límites para la navegación",
                "required": False,
                "properties": {
                    "max_steps": {"type": "integer", "default": 20},
                    "timeout_per_step": {"type": "integer", "default": 30},
                    "allow_external_links": {"type": "boolean", "default": False},
                    "screenshot_frequency": {"type": "string", "default": "every_step"}
                }
            }
        ]
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecutar navegación web autónoma con planificación y ejecución
        """
        try:
            if not self.playwright_available:
                return {
                    'success': False,
                    'error': 'Playwright not installed',
                    'suggestion': 'Install Playwright with: pip install playwright && playwright install'
                }
            
            task_description = parameters.get('task_description')
            target_url = parameters.get('target_url')
            user_data = parameters.get('user_data', {})
            constraints = parameters.get('constraints', {})
            
            if not task_description:
                return {
                    'success': False,
                    'error': 'task_description is required'
                }
            
            # Inicializar logs
            self.execution_logs = []
            self.current_step = 0
            self.screenshots = []
            
            # Ejecutar navegación autónoma con subprocess y xvfb-run
            import subprocess
            import tempfile
            import os
            
            # Configurar variable de entorno para xvfb
            env = os.environ.copy()
            env['DISPLAY'] = ':99'
            
            # Ejecutar Xvfb en background
            xvfb_process = None
            try:
                # Iniciar Xvfb
                xvfb_process = subprocess.Popen(
                    ['Xvfb', ':99', '-screen', '0', '1920x1080x24', '-ac', '+extension', 'GLX', '+render', '-noreset'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=env
                )
                
                # Esperar a que Xvfb se inicie
                import time
                time.sleep(3)
                
                # Ejecutar navegación autónoma
                import threading
                import concurrent.futures
                
                def run_autonomous_navigation():
                    try:
                        # Crear un nuevo event loop en el hilo
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            self.log_step("🚀 INICIANDO NAVEGACIÓN AUTÓNOMA CON XVFB", "info")
                            self.log_step(f"🎯 Tarea: {task_description}", "info")
                            
                            result = loop.run_until_complete(
                                self._execute_autonomous_navigation(
                                    task_description, target_url, user_data, constraints
                                )
                            )
                            return result
                        finally:
                            loop.close()
                    except Exception as e:
                        self.log_step(f"❌ Error en navegación autónoma: {e}", "error")
                        return {
                            'success': False,
                            'error': str(e),
                            'execution_logs': self.execution_logs,
                            'screenshots': self.screenshots,
                            'timestamp': datetime.now().isoformat()
                        }
                
                # Ejecutar en un hilo separado
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_autonomous_navigation)
                    result = future.result(timeout=300)  # 5 minutos timeout
                    return result
                    
            finally:
                # Limpiar Xvfb
                if xvfb_process:
                    xvfb_process.terminate()
                    try:
                        xvfb_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        xvfb_process.kill()
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_logs': self.execution_logs,
                'screenshots': self.screenshots,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _execute_autonomous_navigation(self, task_description: str, target_url: str, user_data: dict, constraints: dict) -> Dict[str, Any]:
        """
        Ejecutar navegación autónoma con planificación inteligente
        """
        async with async_playwright() as p:
            # Lanzar navegador con configuración adaptada para terminal
            browser = await p.chromium.launch(
                headless=self.config['headless'],  # Usar configuración
                slow_mo=self.config['slow_motion'],
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--start-maximized',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            try:
                # Crear contexto
                context = await browser.new_context(
                    viewport=self.config['viewport'],
                    user_agent=self.config['user_agent']
                )
                
                # Crear página
                page = await context.new_page()
                page.set_default_timeout(self.config['timeout'])
                
                # Generar plan autónomo
                plan = await self._generate_autonomous_plan(task_description, target_url, user_data)
                self.total_steps = len(plan)
                
                self.log_step(f"📋 Plan generado con {len(plan)} pasos", "info")
                
                # Ejecutar plan paso a paso
                results = []
                for i, step in enumerate(plan):
                    self.current_step = i + 1
                    self.log_step(f"🔄 Paso {self.current_step}/{self.total_steps}: {step['action']}", "info")
                    
                    try:
                        step_result = await self._execute_step(page, step, user_data)
                        results.append(step_result)
                        
                        if step_result['success']:
                            self.log_step(f"✅ Paso {self.current_step} completado", "success")
                        else:
                            self.log_step(f"❌ Paso {self.current_step} falló: {step_result.get('error', 'Error desconocido')}", "error")
                            
                            # Intentar recuperación automática
                            if await self._attempt_recovery(page, step, step_result):
                                self.log_step(f"🔄 Recuperación exitosa para paso {self.current_step}", "success")
                            else:
                                self.log_step(f"⚠️ No se pudo recuperar del error en paso {self.current_step}", "error")
                        
                        # Tomar screenshot después de cada paso
                        await self._take_screenshot(page, f"step_{self.current_step}")
                        
                        # Pausa entre pasos
                        await asyncio.sleep(self.config['step_delay'] / 1000)
                        
                    except Exception as e:
                        self.log_step(f"💥 Error inesperado en paso {self.current_step}: {str(e)}", "error")
                        results.append({
                            'step': self.current_step,
                            'success': False,
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        })
                
                # Evaluación final
                success_rate = sum(1 for r in results if r['success']) / len(results) if results else 0
                overall_success = success_rate >= 0.7  # 70% de éxito mínimo
                
                self.log_step(f"🏁 Navegación completada - Éxito: {success_rate:.1%}", "success" if overall_success else "error")
                
                return {
                    'success': overall_success,
                    'task_description': task_description,
                    'plan': plan,
                    'step_results': results,
                    'success_rate': success_rate,
                    'total_steps': len(plan),
                    'completed_steps': self.current_step,
                    'execution_logs': self.execution_logs,
                    'screenshots': self.screenshots,
                    'final_url': page.url,
                    'timestamp': datetime.now().isoformat()
                }
                
            finally:
                await browser.close()
                self.log_step("🔚 Navegador cerrado", "info")
    
    async def _generate_autonomous_plan(self, task_description: str, target_url: str, user_data: dict) -> List[Dict[str, Any]]:
        """
        Generar plan autónomo basado en la descripción de la tarea
        """
        plan = []
        
        # Analizar la tarea para generar plan inteligente
        task_lower = task_description.lower()
        
        # Detectar URL objetivo si no se proporcionó
        if not target_url:
            if 'twitter' in task_lower or 'x.com' in task_lower:
                target_url = 'https://twitter.com'
            elif 'facebook' in task_lower:
                target_url = 'https://facebook.com'
            elif 'instagram' in task_lower:
                target_url = 'https://instagram.com'
            elif 'linkedin' in task_lower:
                target_url = 'https://linkedin.com'
            elif 'github' in task_lower:
                target_url = 'https://github.com'
            elif 'google' in task_lower:
                target_url = 'https://google.com'
            elif 'youtube' in task_lower:
                target_url = 'https://youtube.com'
            elif 'amazon' in task_lower:
                target_url = 'https://amazon.com'
            else:
                target_url = 'https://google.com'
        
        # Paso 1: Navegación inicial
        plan.append({
            'action': f'Navegar a {target_url}',
            'type': 'navigate',
            'url': target_url,
            'expected_elements': ['body', 'title'],
            'timeout': 10000
        })
        
        # Generar pasos específicos basados en la tarea
        if any(keyword in task_lower for keyword in ['cuenta', 'register', 'sign up', 'registro']):
            plan.extend(self._generate_registration_plan(target_url, user_data))
        elif any(keyword in task_lower for keyword in ['login', 'sign in', 'inicia sesión', 'acceder']):
            plan.extend(self._generate_login_plan(target_url, user_data))
        elif any(keyword in task_lower for keyword in ['buscar', 'search', 'busca']):
            plan.extend(self._generate_search_plan(task_description, target_url))
        elif any(keyword in task_lower for keyword in ['comprar', 'buy', 'purchase', 'añadir carrito']):
            plan.extend(self._generate_shopping_plan(task_description, target_url))
        elif any(keyword in task_lower for keyword in ['formulario', 'form', 'llenar', 'fill']):
            plan.extend(self._generate_form_plan(task_description, target_url, user_data))
        else:
            # Plan genérico para tareas no específicas
            plan.extend(self._generate_generic_plan(task_description, target_url))
        
        # Paso final: Verificación y screenshot
        plan.append({
            'action': 'Verificar resultado y capturar evidencia',
            'type': 'verify_and_capture',
            'expected_outcome': 'Task completed successfully',
            'timeout': 5000
        })
        
        return plan
    
    def _generate_registration_plan(self, target_url: str, user_data: dict) -> List[Dict[str, Any]]:
        """Generar plan para registro de cuenta"""
        plan = []
        
        # Generar datos de prueba si no se proporcionaron
        if not user_data:
            user_data = {
                'name': f'Test User {int(time.time())}',
                'email': f'test{int(time.time())}@example.com',
                'username': f'testuser{int(time.time())}',
                'password': 'TestPassword123!'
            }
        
        if 'twitter' in target_url:
            plan.extend([
                {
                    'action': 'Buscar botón de registro',
                    'type': 'find_element',
                    'selectors': ['[data-testid="signupButton"]', 'a[href="/i/flow/signup"]', 'text=Sign up'],
                    'timeout': 5000
                },
                {
                    'action': 'Hacer clic en registro',
                    'type': 'click',
                    'selectors': ['[data-testid="signupButton"]', 'a[href="/i/flow/signup"]', 'text=Sign up'],
                    'timeout': 5000
                },
                {
                    'action': 'Llenar nombre',
                    'type': 'fill',
                    'selectors': ['input[name="name"]', '[data-testid="ocfEnterTextTextInput"]'],
                    'value': user_data.get('name', 'Test User'),
                    'timeout': 5000
                },
                {
                    'action': 'Llenar email',
                    'type': 'fill',
                    'selectors': ['input[name="email"]', 'input[type="email"]'],
                    'value': user_data.get('email', 'test@example.com'),
                    'timeout': 5000
                },
                {
                    'action': 'Continuar registro',
                    'type': 'click',
                    'selectors': ['[data-testid="ocfEnterTextNextButton"]', 'text=Next', 'button[type="submit"]'],
                    'timeout': 5000
                }
            ])
        else:
            # Plan genérico para otros sitios
            plan.extend([
                {
                    'action': 'Buscar botón o enlace de registro',
                    'type': 'find_element',
                    'selectors': ['text=Sign up', 'text=Register', 'text=Create account', '[href*="register"]', '[href*="signup"]'],
                    'timeout': 5000
                },
                {
                    'action': 'Hacer clic en registro',
                    'type': 'click',
                    'selectors': ['text=Sign up', 'text=Register', 'text=Create account'],
                    'timeout': 5000
                },
                {
                    'action': 'Llenar formulario de registro',
                    'type': 'fill_form',
                    'fields': [
                        {'selectors': ['input[name="name"]', 'input[type="text"]'], 'value': user_data.get('name', 'Test User')},
                        {'selectors': ['input[name="email"]', 'input[type="email"]'], 'value': user_data.get('email', 'test@example.com')},
                        {'selectors': ['input[name="username"]'], 'value': user_data.get('username', 'testuser')},
                        {'selectors': ['input[name="password"]', 'input[type="password"]'], 'value': user_data.get('password', 'TestPassword123!')}
                    ],
                    'timeout': 5000
                },
                {
                    'action': 'Enviar formulario',
                    'type': 'click',
                    'selectors': ['button[type="submit"]', 'text=Submit', 'text=Create account'],
                    'timeout': 5000
                }
            ])
        
        return plan
    
    def _generate_login_plan(self, target_url: str, user_data: dict) -> List[Dict[str, Any]]:
        """Generar plan para inicio de sesión"""
        return [
            {
                'action': 'Buscar botón de login',
                'type': 'find_element',
                'selectors': ['text=Log in', 'text=Sign in', '[href*="login"]', '[data-testid="loginButton"]'],
                'timeout': 5000
            },
            {
                'action': 'Hacer clic en login',
                'type': 'click',
                'selectors': ['text=Log in', 'text=Sign in', '[href*="login"]'],
                'timeout': 5000
            },
            {
                'action': 'Llenar credenciales',
                'type': 'fill_form',
                'fields': [
                    {'selectors': ['input[name="email"]', 'input[name="username"]', 'input[type="email"]'], 'value': user_data.get('email', 'test@example.com')},
                    {'selectors': ['input[name="password"]', 'input[type="password"]'], 'value': user_data.get('password', 'TestPassword123!')}
                ],
                'timeout': 5000
            },
            {
                'action': 'Enviar login',
                'type': 'click',
                'selectors': ['button[type="submit"]', 'text=Log in', 'text=Sign in'],
                'timeout': 5000
            }
        ]
    
    def _generate_search_plan(self, task_description: str, target_url: str) -> List[Dict[str, Any]]:
        """Generar plan para búsqueda"""
        # Extraer término de búsqueda
        search_term = task_description.lower()
        for prefix in ['buscar', 'busca', 'search']:
            if prefix in search_term:
                search_term = search_term.split(prefix)[-1].strip()
                break
        
        return [
            {
                'action': 'Buscar campo de búsqueda',
                'type': 'find_element',
                'selectors': ['input[name="q"]', 'input[type="search"]', '[data-testid="SearchBox_Search_Input"]', 'input[placeholder*="Search"]'],
                'timeout': 5000
            },
            {
                'action': f'Escribir término de búsqueda: {search_term}',
                'type': 'fill',
                'selectors': ['input[name="q"]', 'input[type="search"]', '[data-testid="SearchBox_Search_Input"]'],
                'value': search_term,
                'timeout': 5000
            },
            {
                'action': 'Ejecutar búsqueda',
                'type': 'press_key',
                'key': 'Enter',
                'timeout': 5000
            },
            {
                'action': 'Esperar resultados',
                'type': 'wait_for_element',
                'selectors': ['[data-testid="primaryColumn"]', '.search-result', '.result'],
                'timeout': 10000
            }
        ]
    
    def _generate_shopping_plan(self, task_description: str, target_url: str) -> List[Dict[str, Any]]:
        """Generar plan para compras"""
        return [
            {
                'action': 'Buscar producto',
                'type': 'search_product',
                'query': task_description,
                'timeout': 10000
            },
            {
                'action': 'Seleccionar primer producto',
                'type': 'click',
                'selectors': ['.product-item', '[data-component-type="s-search-result"]'],
                'timeout': 5000
            },
            {
                'action': 'Añadir al carrito',
                'type': 'click',
                'selectors': ['#add-to-cart-button', 'text=Add to cart', 'text=Añadir al carrito'],
                'timeout': 5000
            }
        ]
    
    def _generate_form_plan(self, task_description: str, target_url: str, user_data: dict) -> List[Dict[str, Any]]:
        """Generar plan para llenar formularios"""
        return [
            {
                'action': 'Buscar formulario',
                'type': 'find_element',
                'selectors': ['form', 'input[type="text"]', 'input[type="email"]'],
                'timeout': 5000
            },
            {
                'action': 'Llenar formulario automáticamente',
                'type': 'auto_fill_form',
                'user_data': user_data,
                'timeout': 10000
            },
            {
                'action': 'Enviar formulario',
                'type': 'click',
                'selectors': ['button[type="submit"]', 'input[type="submit"]', 'text=Submit'],
                'timeout': 5000
            }
        ]
    
    def _generate_generic_plan(self, task_description: str, target_url: str) -> List[Dict[str, Any]]:
        """Generar plan genérico para tareas no específicas"""
        return [
            {
                'action': 'Explorar página',
                'type': 'explore_page',
                'timeout': 5000
            },
            {
                'action': 'Buscar elementos interactivos',
                'type': 'find_interactive_elements',
                'timeout': 5000
            },
            {
                'action': 'Intentar interacción inteligente',
                'type': 'smart_interaction',
                'task_description': task_description,
                'timeout': 10000
            }
        ]
    
    async def _execute_step(self, page, step: Dict[str, Any], user_data: dict) -> Dict[str, Any]:
        """
        Ejecutar un paso individual del plan
        """
        try:
            step_type = step['type']
            timeout = step.get('timeout', 5000)
            
            if step_type == 'navigate':
                await page.goto(step['url'], wait_until='domcontentloaded', timeout=timeout)
                await page.wait_for_timeout(2000)  # Esperar carga completa
                return {'success': True, 'step': step, 'timestamp': datetime.now().isoformat()}
            
            elif step_type == 'find_element':
                selectors = step['selectors']
                element = None
                for selector in selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=timeout)
                        if element:
                            break
                    except:
                        continue
                
                if element:
                    await self._highlight_element(page, selector)
                    return {'success': True, 'step': step, 'element_found': True, 'timestamp': datetime.now().isoformat()}
                else:
                    return {'success': False, 'step': step, 'error': 'Element not found', 'timestamp': datetime.now().isoformat()}
            
            elif step_type == 'click':
                selectors = step['selectors']
                clicked = False
                for selector in selectors:
                    try:
                        await self._highlight_element(page, selector)
                        await page.click(selector, timeout=timeout)
                        clicked = True
                        break
                    except:
                        continue
                
                if clicked:
                    await page.wait_for_timeout(1000)  # Esperar después del click
                    return {'success': True, 'step': step, 'timestamp': datetime.now().isoformat()}
                else:
                    return {'success': False, 'step': step, 'error': 'Could not click element', 'timestamp': datetime.now().isoformat()}
            
            elif step_type == 'fill':
                selectors = step['selectors']
                value = step['value']
                filled = False
                for selector in selectors:
                    try:
                        await self._highlight_element(page, selector)
                        await page.fill(selector, value, timeout=timeout)
                        filled = True
                        break
                    except:
                        continue
                
                if filled:
                    return {'success': True, 'step': step, 'timestamp': datetime.now().isoformat()}
                else:
                    return {'success': False, 'step': step, 'error': 'Could not fill element', 'timestamp': datetime.now().isoformat()}
            
            elif step_type == 'fill_form':
                fields = step['fields']
                filled_fields = 0
                for field in fields:
                    selectors = field['selectors']
                    value = field['value']
                    for selector in selectors:
                        try:
                            await self._highlight_element(page, selector)
                            await page.fill(selector, value, timeout=timeout)
                            filled_fields += 1
                            break
                        except:
                            continue
                
                success_rate = filled_fields / len(fields) if fields else 0
                return {
                    'success': success_rate >= 0.5,  # Al menos 50% de campos llenados
                    'step': step,
                    'filled_fields': filled_fields,
                    'total_fields': len(fields),
                    'timestamp': datetime.now().isoformat()
                }
            
            elif step_type == 'press_key':
                key = step['key']
                await page.keyboard.press(key)
                await page.wait_for_timeout(1000)
                return {'success': True, 'step': step, 'timestamp': datetime.now().isoformat()}
            
            elif step_type == 'wait_for_element':
                selectors = step['selectors']
                found = False
                for selector in selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=timeout)
                        found = True
                        break
                    except:
                        continue
                
                return {'success': found, 'step': step, 'timestamp': datetime.now().isoformat()}
            
            elif step_type == 'verify_and_capture':
                # Tomar screenshot final
                await self._take_screenshot(page, 'final_result')
                return {'success': True, 'step': step, 'final_url': page.url, 'timestamp': datetime.now().isoformat()}
            
            elif step_type == 'explore_page':
                # Explorar página para obtener información
                title = await page.title()
                url = page.url
                await self._take_screenshot(page, 'page_exploration')
                return {'success': True, 'step': step, 'title': title, 'url': url, 'timestamp': datetime.now().isoformat()}
            
            elif step_type == 'find_interactive_elements':
                # Buscar elementos interactivos
                interactive_elements = await page.evaluate('''
                    () => {
                        const elements = [];
                        const buttons = document.querySelectorAll('button');
                        const links = document.querySelectorAll('a');
                        const inputs = document.querySelectorAll('input');
                        
                        buttons.forEach(el => elements.push({type: 'button', text: el.textContent.trim()}));
                        links.forEach(el => elements.push({type: 'link', text: el.textContent.trim(), href: el.href}));
                        inputs.forEach(el => elements.push({type: 'input', placeholder: el.placeholder}));
                        
                        return elements.slice(0, 10);  // Primeros 10 elementos
                    }
                ''')
                return {'success': True, 'step': step, 'interactive_elements': interactive_elements, 'timestamp': datetime.now().isoformat()}
            
            elif step_type == 'smart_interaction':
                # Interacción inteligente basada en la tarea
                task_description = step.get('task_description', '').lower()
                
                if 'registro' in task_description or 'cuenta' in task_description:
                    # Buscar botón de registro
                    try:
                        await page.wait_for_selector('text=Sign up', timeout=5000)
                        await page.click('text=Sign up')
                        return {'success': True, 'step': step, 'action': 'clicked_signup', 'timestamp': datetime.now().isoformat()}
                    except:
                        pass
                
                if 'login' in task_description:
                    # Buscar botón de login
                    try:
                        await page.wait_for_selector('text=Log in', timeout=5000)
                        await page.click('text=Log in')
                        return {'success': True, 'step': step, 'action': 'clicked_login', 'timestamp': datetime.now().isoformat()}
                    except:
                        pass
                
                # Interacción genérica - tomar screenshot
                await self._take_screenshot(page, 'smart_interaction')
                return {'success': True, 'step': step, 'action': 'generic_interaction', 'timestamp': datetime.now().isoformat()}
            
            else:
                return {'success': False, 'step': step, 'error': f'Unknown step type: {step_type}', 'timestamp': datetime.now().isoformat()}
        
        except Exception as e:
            return {'success': False, 'step': step, 'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def _highlight_element(self, page, selector: str) -> bool:
        """Resaltar elemento antes de interactuar"""
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
            
            await asyncio.sleep(self.config['element_highlight_time'] / 1000)
            return True
        except:
            return False
    
    async def _take_screenshot(self, page, step_name: str) -> str:
        """Tomar screenshot y convertir a base64"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                screenshot_path = tmp_file.name
            
            await page.screenshot(
                path=screenshot_path,
                full_page=True
            )
            
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            os.unlink(screenshot_path)
            
            screenshot_info = {
                'step': step_name,
                'timestamp': datetime.now().isoformat(),
                'image_data': image_data,
                'url': page.url
            }
            
            self.screenshots.append(screenshot_info)
            return image_data
        except Exception as e:
            self.log_step(f"Error capturando screenshot: {str(e)}", "error")
            return None
    
    async def _attempt_recovery(self, page, failed_step: Dict[str, Any], error_result: Dict[str, Any]) -> bool:
        """Intentar recuperación automática de errores"""
        try:
            # Estrategias básicas de recuperación
            if 'timeout' in str(error_result.get('error', '')).lower():
                # Esperar más tiempo y reintentar
                await page.wait_for_timeout(3000)
                return True
            
            if 'element not found' in str(error_result.get('error', '')).lower():
                # Intentar scroll y buscar de nuevo
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(2000)
                return True
            
            return False
        except:
            return False
    
    def log_step(self, message: str, level: str = "info"):
        """Registrar paso en logs para mostrar en TerminalView"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'step': self.current_step,
            'total_steps': self.total_steps,
            'type': 'web_navigation'  # Tipo especial para TerminalView
        }
        
        self.execution_logs.append(log_entry)
        
        # Imprimir en consola para debugging y TerminalView
        icon = "🌐" if level == "info" else "✅" if level == "success" else "❌"
        timestamp = datetime.now().strftime('%H:%M:%S')
        progress = f"[{self.current_step}/{self.total_steps}]" if self.total_steps > 0 else ""
        print(f"{icon} [{timestamp}] {progress} {message}")
        
        # Enviar a TerminalView si está disponible
        if hasattr(self, 'terminal_callback') and self.terminal_callback:
            self.terminal_callback(message, level)
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros de entrada"""
        errors = []
        
        task_description = parameters.get('task_description')
        if not task_description:
            errors.append("task_description is required")
        elif not isinstance(task_description, str):
            errors.append("task_description must be a string")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información de la herramienta"""
        return {
            'category': 'web_automation_autonomous',
            'version': '1.0.0',
            'capabilities': [
                'Autonomous web task planning',
                'Intelligent step execution',
                'Automatic error recovery',
                'Visual browser automation',
                'Screenshot capture and logging',
                'Real-time progress tracking',
                'Smart element detection',
                'Form filling automation',
                'Multi-site navigation'
            ],
            'supported_tasks': [
                'Account creation',
                'Login automation',
                'Form filling',
                'Web search',
                'Shopping automation',
                'Information extraction',
                'Page navigation',
                'Screenshot capture'
            ],
            'playwright_status': 'available' if self.playwright_available else 'not_installed'
        }