#!/usr/bin/env python3
"""
Script de demostración completa para X.com con registro de cuenta
"""

import asyncio
import os
import subprocess
import time
import random
import string
from datetime import datetime
from playwright.async_api import async_playwright

async def demo_x_com_registration():
    """
    Demostración completa del proceso de registro en X.com
    """
    print("🎯 === DEMOSTRACIÓN X.COM REGISTRO DE CUENTA ===")
    print("🕐 Iniciando demostración:", datetime.now().strftime("%H:%M:%S"))
    
    # Configurar display virtual
    display_num = 99
    xvfb_cmd = f"Xvfb :{display_num} -screen 0 1920x1080x24 -ac +extension GLX +render -noreset"
    
    print(f"🖥️ Configurando display virtual :{display_num}")
    xvfb_process = subprocess.Popen(xvfb_cmd.split(), 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
    
    time.sleep(3)
    os.environ['DISPLAY'] = f":{display_num}"
    
    # Iniciar window manager
    wm_process = None
    try:
        wm_process = subprocess.Popen(['fluxbox'], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
        time.sleep(2)
        print("✅ Window manager iniciado")
    except FileNotFoundError:
        print("⚠️ Window manager no encontrado")
    
    # Generar datos de demostración
    demo_username = f"demo_user_{random.randint(1000, 9999)}"
    demo_email = f"demo{random.randint(100, 999)}@example.com"
    demo_password = "DemoPassword123!"
    
    print(f"👤 Usuario demo: {demo_username}")
    print(f"📧 Email demo: {demo_email}")
    
    try:
        async with async_playwright() as p:
            print("🌐 Lanzando navegador Chrome...")
            
            # Lanzar navegador en modo visible con configuración optimizada
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=1500,  # 1.5 segundos entre acciones
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            try:
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                page = await context.new_page()
                page.set_default_timeout(30000)
                
                # Paso 1: Navegar a X.com
                print("📍 PASO 1: Navegando a X.com...")
                await page.goto('https://x.com')
                await page.wait_for_timeout(3000)
                
                # Tomar screenshot inicial
                await page.screenshot(path='/tmp/x_com_step1_home.png')
                print("📸 Screenshot 1: Página inicial capturada")
                
                # Paso 2: Buscar botón de registro
                print("🔍 PASO 2: Buscando botón de registro...")
                
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
                        print(f"✅ Botón de registro encontrado: {selector}")
                        
                        # Resaltar el botón
                        await page.evaluate(f'''
                            document.querySelector('{selector}').style.outline = '3px solid #ff6b6b';
                            document.querySelector('{selector}').style.backgroundColor = 'rgba(255, 107, 107, 0.1)';
                        ''')
                        
                        await page.wait_for_timeout(2000)
                        
                        # Hacer clic en el botón
                        await page.click(selector)
                        print("👆 Clic en botón de registro realizado")
                        
                        signup_found = True
                        break
                        
                    except Exception as e:
                        print(f"⚠️ Selector {selector} no encontrado: {e}")
                        continue
                
                if not signup_found:
                    print("🔍 Explorando página para encontrar registro...")
                    
                    # Buscar enlaces que contengan palabras clave
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
                    
                    print(f"🔍 Encontrados {len(links)} enlaces visibles")
                    
                    # Buscar enlace de registro
                    for link in links:
                        if any(keyword in link['text'].lower() for keyword in ['sign up', 'create', 'register', 'join']):
                            print(f"📍 Navegando a enlace: {link['text']}")
                            await page.goto(link['href'])
                            signup_found = True
                            break
                
                # Paso 3: Capturar pantalla de formulario
                await page.wait_for_timeout(3000)
                await page.screenshot(path='/tmp/x_com_step2_signup.png')
                print("📸 Screenshot 2: Página de registro capturada")
                
                # Paso 4: Intentar llenar formulario
                print("📝 PASO 3: Intentando llenar formulario...")
                
                form_fields = [
                    {'name': 'name', 'selectors': ['input[name="name"]', 'input[autocomplete="name"]', 'input[placeholder*="name"]'], 'value': f"Demo User {demo_username}"},
                    {'name': 'email', 'selectors': ['input[name="email"]', 'input[type="email"]', 'input[autocomplete="email"]'], 'value': demo_email},
                    {'name': 'username', 'selectors': ['input[name="username"]', 'input[placeholder*="username"]'], 'value': demo_username},
                ]
                
                for field in form_fields:
                    print(f"🔍 Buscando campo: {field['name']}")
                    
                    for selector in field['selectors']:
                        try:
                            await page.wait_for_selector(selector, timeout=3000)
                            
                            # Resaltar campo
                            await page.evaluate(f'''
                                document.querySelector('{selector}').style.outline = '3px solid #4a9eff';
                                document.querySelector('{selector}').style.backgroundColor = 'rgba(74, 158, 255, 0.1)';
                            ''')
                            
                            await page.wait_for_timeout(1000)
                            
                            print(f"✍️ Escribiendo en campo {field['name']}: {field['value']}")
                            await page.fill(selector, field['value'])
                            await page.wait_for_timeout(1500)
                            
                            # Quitar resaltado
                            await page.evaluate(f'''
                                document.querySelector('{selector}').style.outline = '';
                                document.querySelector('{selector}').style.backgroundColor = '';
                            ''')
                            
                            break
                            
                        except Exception as e:
                            print(f"⚠️ Campo {field['name']} con selector {selector} no encontrado")
                            continue
                
                # Paso 5: Capturar formulario llenado
                await page.screenshot(path='/tmp/x_com_step3_form_filled.png')
                print("📸 Screenshot 3: Formulario llenado capturado")
                
                # Paso 6: Buscar botón de envío
                print("🔍 PASO 4: Buscando botón de envío...")
                
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
                        
                        # Resaltar botón
                        await page.evaluate(f'''
                            document.querySelector('{selector}').style.outline = '3px solid #4ade80';
                            document.querySelector('{selector}').style.backgroundColor = 'rgba(74, 222, 128, 0.1)';
                        ''')
                        
                        await page.wait_for_timeout(2000)
                        
                        print(f"✅ Botón de envío encontrado: {selector}")
                        print("🎯 SIMULANDO clic en botón de envío (SIN ENVIAR)")
                        
                        # Solo hacer hover, no enviar realmente
                        await page.hover(selector)
                        await page.wait_for_timeout(2000)
                        
                        break
                        
                    except Exception as e:
                        print(f"⚠️ Botón {selector} no encontrado: {e}")
                        continue
                
                # Paso 7: Screenshot final
                await page.screenshot(path='/tmp/x_com_step4_final.png')
                print("📸 Screenshot 4: Demostración completada")
                
                # Paso 8: Mostrar mensaje de éxito
                print("🎉 DEMOSTRACIÓN COMPLETADA EXITOSAMENTE!")
                print("📊 Resumen:")
                print(f"   👤 Usuario: {demo_username}")
                print(f"   📧 Email: {demo_email}")
                print(f"   🕐 Tiempo: {datetime.now().strftime('%H:%M:%S')}")
                print("   📸 Screenshots guardados en:")
                print("      - /tmp/x_com_step1_home.png")
                print("      - /tmp/x_com_step2_signup.png")
                print("      - /tmp/x_com_step3_form_filled.png")
                print("      - /tmp/x_com_step4_final.png")
                
                # Esperar para mostrar resultado
                await page.wait_for_timeout(5000)
                
            finally:
                await browser.close()
                print("🔚 Navegador cerrado")
                
    except Exception as e:
        print(f"❌ Error en demostración: {e}")
        
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

if __name__ == "__main__":
    asyncio.run(demo_x_com_registration())