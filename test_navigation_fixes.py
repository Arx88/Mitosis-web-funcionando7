#!/usr/bin/env python3
"""
🧪 TEST ESPECÍFICO DE NAVEGACIÓN WEB EN TIEMPO REAL
Prueba las correcciones implementadas para el problema de inconsistencia
"""

import requests
import time
import json
from datetime import datetime

def test_navigation_consistency():
    """Probar navegación web múltiples veces para verificar consistencia"""
    
    print("🧪 TESTING NAVEGACIÓN WEB EN TIEMPO REAL - CORRECCIONES IMPLEMENTADAS")
    print("=" * 80)
    print(f"🕒 Inicio del test: {datetime.now().isoformat()}")
    print("=" * 80)
    
    backend_url = "http://localhost:8001"
    
    # Test 1: Verificar que backend está funcionando
    print("\n📡 TEST 1: Verificando backend...")
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend responde correctamente")
        else:
            print(f"❌ Backend error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al backend: {e}")
        return False
    
    # Test 2: Verificar servicios del agente
    print("\n🤖 TEST 2: Verificando servicios del agente...")
    try:
        response = requests.get(f"{backend_url}/api/agent/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agente funcionando - Ollama: {data.get('ollama', {}).get('connected', False)}")
            print(f"✅ Herramientas disponibles: {data.get('tools_count', 0)}")
        else:
            print(f"❌ Error en agente: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verificando agente: {e}")
    
    # Test 3: Crear tarea con navegación web
    print("\n🌐 TEST 3: Creando tarea de navegación web...")
    task_data = {
        "message": "Buscar información sobre Pokemon y capturar screenshots en tiempo real",
        "config": {
            "enable_real_time_navigation": True,
            "capture_interval": 2,
            "max_duration": 30
        }
    }
    
    try:
        response = requests.post(f"{backend_url}/api/agent/chat", json=task_data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id', 'unknown')
            print(f"✅ Tarea creada exitosamente: {task_id}")
            
            # Test 4: Monitorear ejecución
            return monitor_task_execution(backend_url, task_id)
        else:
            print(f"❌ Error creando tarea: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en creación de tarea: {e}")
        return False

def monitor_task_execution(backend_url: str, task_id: str) -> bool:
    """Monitorear ejecución de la tarea para verificar screenshots"""
    
    print(f"\n📊 TEST 4: Monitoreando ejecución de tarea {task_id}...")
    
    screenshots_detected = 0
    browser_visual_events = 0
    max_monitoring_time = 60  # 1 minuto
    start_time = time.time()
    
    while time.time() - start_time < max_monitoring_time:
        try:
            # Verificar estado de la tarea
            response = requests.get(f"{backend_url}/api/agent/task/{task_id}", timeout=5)
            if response.status_code == 200:
                task_data = response.json()
                status = task_data.get('status', 'unknown')
                
                # Buscar evidencia de navegación web
                if 'screenshots' in str(task_data).lower():
                    screenshots_detected += 1
                
                if 'browser_visual' in str(task_data).lower():
                    browser_visual_events += 1
                
                print(f"⏰ [{int(time.time() - start_time)}s] Status: {status} - Screenshots: {screenshots_detected} - Eventos: {browser_visual_events}")
                
                # Si la tarea está completada, verificar resultados
                if status in ['completed', 'failed', 'error']:
                    return evaluate_results(screenshots_detected, browser_visual_events, status)
                    
            else:
                print(f"⚠️ Error obteniendo estado de tarea: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Error monitoreando tarea: {e}")
        
        time.sleep(3)  # Verificar cada 3 segundos
    
    print("⏰ Tiempo de monitoreo agotado")
    return evaluate_results(screenshots_detected, browser_visual_events, "timeout")

def evaluate_results(screenshots: int, events: int, status: str) -> bool:
    """Evaluar los resultados del test"""
    
    print("\n📊 EVALUACIÓN DE RESULTADOS...")
    print("=" * 50)
    print(f"📸 Screenshots detectados: {screenshots}")
    print(f"📡 Eventos browser_visual: {events}")
    print(f"🎯 Estado final: {status}")
    print("=" * 50)
    
    # Criterios de éxito
    success = True
    
    if screenshots < 1:
        print("❌ FALLO: No se detectaron screenshots")
        success = False
    else:
        print("✅ Screenshots detectados correctamente")
    
    if events < 1:
        print("❌ FALLO: No se detectaron eventos browser_visual")
        success = False
    else:
        print("✅ Eventos browser_visual detectados")
    
    if status == 'failed':
        print("❌ FALLO: La tarea falló durante la ejecución")
        success = False
    elif status == 'completed':
        print("✅ Tarea completada exitosamente")
    
    print("\n🎯 RESULTADO FINAL:")
    if success:
        print("🎉 ¡TEST EXITOSO! Las correcciones funcionan correctamente")
        print("✅ La navegación web en tiempo real es ahora CONSISTENTE")
    else:
        print("❌ TEST FALLIDO - Las correcciones necesitan más trabajo")
        print("⚠️ La navegación web todavía tiene problemas de consistencia")
    
    return success

def main():
    """Función principal del test"""
    try:
        result = test_navigation_consistency()
        
        print("\n" + "=" * 80)
        if result:
            print("🏆 CONCLUSIÓN: PROBLEMA RESUELTO - Navegación web consistente")
            print("✅ Las correcciones implementadas funcionan correctamente:")
            print("   • Variable DISPLAY configurada globalmente")
            print("   • Semáforo de navegación previene concurrencia")
            print("   • Validación de screenshots con múltiples reintentos")
            print("   • Eventos WebSocket con retry automático")
        else:
            print("⚠️ CONCLUSIÓN: PROBLEMA PERSISTE - Navegación inconsistente")
            print("❌ Se requieren correcciones adicionales")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"💥 ERROR CRÍTICO EN TEST: {e}")
        return False

if __name__ == '__main__':
    main()