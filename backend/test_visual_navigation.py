#!/usr/bin/env python3
"""
Script de prueba para verificar que la navegación visual funciona
"""

import asyncio
import os
import subprocess
import time
from playwright.async_api import async_playwright

async def test_visual_navigation():
    """
    Prueba básica de navegación visual con Playwright
    """
    print("🚀 Iniciando prueba de navegación visual...")
    
    # Configurar display virtual
    display_num = 99
    xvfb_cmd = f"Xvfb :{display_num} -screen 0 1920x1080x24 -ac +extension GLX +render -noreset"
    
    print(f"🖥️ Iniciando display virtual :{display_num}")
    xvfb_process = subprocess.Popen(xvfb_cmd.split(), 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
    
    # Esperar a que se inicie
    time.sleep(3)
    
    # Configurar variable de entorno
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
    
    try:
        async with async_playwright() as p:
            print("🌐 Lanzando navegador...")
            
            # Lanzar navegador en modo visible
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=1000,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--start-maximized'
                ]
            )
            
            try:
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                
                print("📍 Navegando a X.com...")
                await page.goto('https://x.com')
                
                print("⏳ Esperando 5 segundos...")
                await page.wait_for_timeout(5000)
                
                print("📄 Título de la página:", await page.title())
                
                # Tomar screenshot
                await page.screenshot(path='/tmp/x_com_test.png')
                print("📸 Screenshot guardado en /tmp/x_com_test.png")
                
                print("✅ Navegación visual exitosa!")
                
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        
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
        
        print("🧹 Limpieza completada")

if __name__ == "__main__":
    asyncio.run(test_visual_navigation())