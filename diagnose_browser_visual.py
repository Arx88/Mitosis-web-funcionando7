#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO COMPLETO DE NAVEGACIÓN WEB EN TIEMPO REAL
Analiza por qué a veces funciona y otras no la visualización de screenshots
"""

import os
import sys
import time
import json
import requests
import subprocess
from datetime import datetime

def check_xvfb_status():
    """Verificar estado del servidor X11 virtual"""
    print("🖥️ VERIFICANDO SERVIDOR X11 VIRTUAL...")
    print("=" * 60)
    
    try:
        # Verificar procesos Xvfb
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        xvfb_processes = [line for line in result.stdout.split('\n') if 'Xvfb' in line]
        
        if xvfb_processes:
            for proc in xvfb_processes:
                print(f"✅ Xvfb encontrado: {proc}")
        else:
            print("❌ No se encontraron procesos Xvfb")
            return False
        
        # Verificar variable DISPLAY
        display = os.environ.get('DISPLAY', 'no configurada')
        print(f"🖥️ Variable DISPLAY: {display}")
        
        # Verificar conectividad al display
        try:
            result = subprocess.run(['xset', '-display', ':99', 'q'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Display :99 es accesible")
                return True
            else:
                print(f"❌ Display :99 no accesible: {result.stderr}")
                return False
        except Exception as e:
            print(f"⚠️ No se pudo verificar display: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando Xvfb: {e}")
        return False

def check_screenshot_directory():
    """Verificar directorio de screenshots"""
    print("\n📸 VERIFICANDO DIRECTORIO DE SCREENSHOTS...")
    print("=" * 60)
    
    screenshot_dirs = ['/tmp/screenshots', '/app/screenshots', '/var/tmp/screenshots']
    
    for dir_path in screenshot_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directorio existe: {dir_path}")
            try:
                files = os.listdir(dir_path)
                if files:
                    print(f"📁 Archivos encontrados: {len(files)}")
                    for f in files[:5]:  # Mostrar primeros 5
                        print(f"   - {f}")
                else:
                    print("📁 Directorio vacío")
            except Exception as e:
                print(f"❌ Error leyendo directorio: {e}")
        else:
            print(f"❌ Directorio no existe: {dir_path}")
    
    # Crear directorio si no existe
    main_dir = '/tmp/screenshots'
    if not os.path.exists(main_dir):
        try:
            os.makedirs(main_dir, exist_ok=True)
            print(f"✅ Directorio creado: {main_dir}")
        except Exception as e:
            print(f"❌ Error creando directorio: {e}")
    
    return True

def check_browser_processes():
    """Verificar procesos de navegador activos"""
    print("\n🌐 VERIFICANDO PROCESOS DE NAVEGADOR...")
    print("=" * 60)
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        browser_processes = [line for line in result.stdout.split('\n') 
                            if any(browser in line.lower() for browser in ['chrome', 'chromium', 'firefox'])]
        
        if browser_processes:
            print(f"✅ Procesos de navegador encontrados: {len(browser_processes)}")
            for i, proc in enumerate(browser_processes[:3]):  # Primeros 3
                print(f"   🌐 {i+1}: {proc[:100]}...")
        else:
            print("❌ No se encontraron procesos de navegador activos")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando navegador: {e}")
        return False

def check_backend_status():
    """Verificar estado del backend"""
    print("\n🔧 VERIFICANDO ESTADO DEL BACKEND...")
    print("=" * 60)
    
    backend_url = "http://localhost:8001"
    
    try:
        # Health check
        response = requests.get(f"{backend_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend responde correctamente")
            data = response.json()
            print(f"   📊 Status: {data.get('status', 'unknown')}")
            print(f"   🕒 Timestamp: {data.get('timestamp', 'unknown')}")
        else:
            print(f"⚠️ Backend responde con código: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al backend")
        return False
    except Exception as e:
        print(f"❌ Error verificando backend: {e}")
        return False
    
    # Verificar endpoint de agente
    try:
        response = requests.get(f"{backend_url}/api/agent/status", timeout=10)
        if response.status_code == 200:
            print("✅ Endpoint del agente funciona")
            data = response.json()
            print(f"   🤖 Ollama conectado: {data.get('ollama', {}).get('connected', False)}")
            print(f"   🛠️ Herramientas: {data.get('tools_count', 0)}")
        else:
            print(f"⚠️ Endpoint del agente código: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verificando endpoint del agente: {e}")
    
    return True

def test_screenshot_capture():
    """Probar captura de screenshot básica"""
    print("\n📷 PROBANDO CAPTURA DE SCREENSHOT...")
    print("=" * 60)
    
    try:
        # Verificar si scrot está disponible
        result = subprocess.run(['which', 'scrot'], capture_output=True)
        if result.returncode != 0:
            # Instalar scrot si no está
            print("📦 Instalando scrot...")
            subprocess.run(['apt-get', 'update', '-qq'], capture_output=True)
            subprocess.run(['apt-get', 'install', '-y', 'scrot'], capture_output=True)
        
        # Capturar screenshot de prueba
        test_screenshot = '/tmp/test_screenshot.png'
        result = subprocess.run([
            'scrot', '-z', test_screenshot
        ], env={'DISPLAY': ':99'}, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(test_screenshot):
            file_size = os.path.getsize(test_screenshot)
            print(f"✅ Screenshot capturado exitosamente")
            print(f"   📄 Archivo: {test_screenshot}")
            print(f"   💾 Tamaño: {file_size} bytes")
            
            # Limpiar archivo de prueba
            os.remove(test_screenshot)
            return True
        else:
            print(f"❌ Error capturando screenshot: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de captura: {e}")
        return False

def check_websocket_status():
    """Verificar estado de WebSocket"""
    print("\n🔌 VERIFICANDO WEBSOCKET...")
    print("=" * 60)
    
    try:
        # Verificar logs del supervisor para WebSocket
        log_files = [
            '/var/log/supervisor/backend.err.log',
            '/var/log/supervisor/backend.out.log',
            '/var/log/mitosis_debug.log'
        ]
        
        websocket_mentions = 0
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        if 'websocket' in content.lower() or 'socket.io' in content.lower():
                            websocket_mentions += 1
                            print(f"✅ WebSocket mencionado en: {log_file}")
                except Exception as e:
                    print(f"⚠️ Error leyendo {log_file}: {e}")
        
        if websocket_mentions > 0:
            print(f"✅ WebSocket configurado en {websocket_mentions} archivos de log")
        else:
            print("⚠️ No se encontraron menciones de WebSocket en logs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando WebSocket: {e}")
        return False

def analyze_issue_patterns():
    """Analizar patrones del problema"""
    print("\n🔍 ANÁLISIS DE PATRONES DEL PROBLEMA...")
    print("=" * 60)
    
    print("📋 POSIBLES CAUSAS DE INCONSISTENCIA:")
    print("")
    print("1. 🔄 CONCURRENCIA:")
    print("   - Múltiples tareas ejecutándose simultáneamente")
    print("   - Race conditions en captura de screenshots")
    print("   - Conflictos en acceso al display :99")
    print("")
    print("2. 💾 RECURSOS:")
    print("   - Memoria insuficiente para navegador + captura")
    print("   - CPU sobrecargado durante navegación")
    print("   - Espacio en disco limitado para screenshots")
    print("")
    print("3. ⏱️ TIMING:")
    print("   - Timeouts muy cortos para cargar páginas")
    print("   - Capturas antes de que la página cargue completamente")
    print("   - Sincronización entre navegación y captura")
    print("")
    print("4. 🔌 WEBSOCKET:")
    print("   - Conexión WebSocket intermitente")
    print("   - Eventos browser_visual perdidos en transmisión")
    print("   - Buffer de eventos saturado")
    print("")
    print("5. 🖥️ DISPLAY:")
    print("   - Servidor X11 se reinicia ocasionalmente")
    print("   - Pérdida de conexión al display virtual")
    print("   - Conflictos con otros procesos gráficos")
    
    return True

def provide_solutions():
    """Proporcionar soluciones"""
    print("\n💡 SOLUCIONES RECOMENDADAS...")
    print("=" * 60)
    
    print("🔧 CORRECCIONES INMEDIATAS:")
    print("")
    print("1. 🔒 SEMÁFORO DE NAVEGACIÓN:")
    print("   - Implementar lock para una sola navegación a la vez")
    print("   - Cola de tareas de navegación")
    print("")
    print("2. ⏱️ TIMEOUTS ROBUSTOS:")
    print("   - Aumentar timeouts de carga de páginas")
    print("   - Retry automático en caso de fallo")
    print("")
    print("3. 📸 CAPTURA REDUNDANTE:")
    print("   - Múltiples intentos de screenshot por evento")
    print("   - Validación de archivo antes de enviar evento")
    print("")
    print("4. 🔌 WEBSOCKET ROBUSTO:")
    print("   - Queue de eventos con retry")
    print("   - Verificación de entrega de eventos")
    print("")
    print("5. 📊 MONITOREO:")
    print("   - Logging detallado de cada paso")
    print("   - Métricas de éxito/fallo por tarea")

def main():
    """Función principal de diagnóstico"""
    print("🔍 DIAGNÓSTICO COMPLETO - NAVEGACIÓN WEB EN TIEMPO REAL")
    print("=" * 80)
    print(f"🕒 Fecha: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Ejecutar verificaciones
    results = {
        'xvfb': check_xvfb_status(),
        'screenshots': check_screenshot_directory(), 
        'browser': check_browser_processes(),
        'backend': check_backend_status(),
        'screenshot_test': test_screenshot_capture(),
        'websocket': check_websocket_status()
    }
    
    # Análisis y soluciones
    analyze_issue_patterns()
    provide_solutions()
    
    # Resumen final
    print("\n📊 RESUMEN DIAGNÓSTICO...")
    print("=" * 60)
    
    total_checks = len(results)
    passed_checks = sum(results.values())
    
    print(f"✅ Verificaciones exitosas: {passed_checks}/{total_checks}")
    print(f"📊 Porcentaje de éxito: {(passed_checks/total_checks)*100:.1f}%")
    
    if passed_checks == total_checks:
        print("🎉 SISTEMA COMPLETAMENTE FUNCIONAL")
        print("💡 El problema podría ser intermitente - monitorear próximas ejecuciones")
    elif passed_checks >= total_checks * 0.7:
        print("⚠️ SISTEMA MAYORMENTE FUNCIONAL")
        print("💡 Algunos componentes necesitan atención")
    else:
        print("❌ SISTEMA CON PROBLEMAS SERIOS")
        print("💡 Requiere correcciones antes de funcionar correctamente")
    
    print("\n" + "=" * 80)
    print("🔚 DIAGNÓSTICO COMPLETADO")

if __name__ == '__main__':
    main()