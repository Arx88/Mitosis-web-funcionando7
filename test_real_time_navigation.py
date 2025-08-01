#!/usr/bin/env python3
"""
🔍 TEST DE NAVEGACIÓN EN TIEMPO REAL - Diagnóstico del problema
Verifica si la visualización en tiempo real funciona correctamente

Usuario reporta: "la visualización en tiempo real de la navegación web del agente en la terminal del taskview NO ESTÁ FUNCIONANDO"
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"
TEST_TASK_ID = f"test-real-time-{int(time.time())}"

def test_websocket_manager_available():
    """Test 1: Verificar que WebSocket Manager esté disponible"""
    print("🔍 TEST 1: Verificar WebSocket Manager...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/agent/status")
        if response.status_code == 200:
            print("✅ Backend disponible")
            return True
        else:
            print(f"❌ Backend no disponible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al backend: {e}")
        return False

def test_unified_web_search_tool():
    """Test 2: Ejecutar búsqueda web unificada para verificar logs en tiempo real"""
    print(f"🔍 TEST 2: Ejecutar búsqueda web unificada con task_id: {TEST_TASK_ID}")
    
    try:
        # Crear mensaje de chat que debería usar web_search
        chat_data = {
            "message": "Buscar información sobre inteligencia artificial 2025",
            "task_id": TEST_TASK_ID
        }
        
        print(f"📤 Enviando request de chat...")
        response = requests.post(
            f"{BACKEND_URL}/api/agent/chat", 
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat response exitoso: {result.get('success', False)}")
            print(f"📊 Plan generado: {len(result.get('plan', []))} pasos")
            
            # Verificar si se menciona web_search en el plan
            plan = result.get('plan', [])
            web_search_steps = [step for step in plan if 'web_search' in step.get('tool', '').lower() or 'buscar' in step.get('title', '').lower()]
            print(f"🔍 Pasos de búsqueda web detectados: {len(web_search_steps)}")
            
            for i, step in enumerate(web_search_steps):
                print(f"   Paso {i+1}: {step.get('title', 'Sin título')} - Herramienta: {step.get('tool', 'Sin herramienta')}")
            
            return True
        else:
            print(f"❌ Error en chat: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de búsqueda: {e}")
        return False

def test_task_execution():
    """Test 3: Verificar que la tarea se ejecute y genere logs de navegación"""
    print(f"🔍 TEST 3: Verificar ejecución de tarea {TEST_TASK_ID}")
    
    try:
        # Intentar obtener el estado de la tarea
        response = requests.get(f"{BACKEND_URL}/api/agent/get-task-status/{TEST_TASK_ID}")
        
        if response.status_code == 200:
            task_status = response.json()
            print(f"✅ Tarea encontrada - Estado: {task_status.get('status', 'unknown')}")
            print(f"📊 Progreso: {task_status.get('progress', 0)}%")
            print(f"🎯 Paso actual: {task_status.get('current_step', 'N/A')}")
            print(f"📝 Total pasos: {task_status.get('total_steps', 0)}")
            
            return True
        else:
            print(f"❌ Tarea no encontrada: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando ejecución: {e}")
        return False

def test_websocket_debug_logs():
    """Test 4: Verificar logs de debug de WebSocket"""
    print("🔍 TEST 4: Verificar logs de debug de WebSocket...")
    
    try:
        import os
        debug_log_path = "/tmp/websocket_debug.log"
        
        if os.path.exists(debug_log_path):
            with open(debug_log_path, 'r') as f:
                logs = f.read()
                recent_logs = logs.split('\n')[-20:]  # Últimas 20 líneas
                
                print(f"✅ Archivo de debug encontrado. Últimos logs:")
                for log_line in recent_logs:
                    if log_line.strip():
                        print(f"   {log_line}")
                
                # Buscar evidencia de nuestro test
                test_evidence = [line for line in recent_logs if TEST_TASK_ID in line]
                if test_evidence:
                    print(f"🎯 Evidencia de nuestro test encontrada: {len(test_evidence)} líneas")
                else:
                    print("⚠️ No se encontró evidencia de nuestro test en los logs")
                
                return True
        else:
            print("❌ Archivo de debug de WebSocket no encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Error leyendo logs de debug: {e}")
        return False

def test_web_search_tool_direct():
    """Test 5: Ejecutar herramienta web_search directamente"""
    print("🔍 TEST 5: Ejecutar herramienta web_search directamente...")
    
    try:
        # Test del endpoint de navegación en tiempo real
        test_data = {
            "task_id": TEST_TASK_ID,
            "url": "https://www.bing.com/search?q=inteligencia+artificial",
            "actions": ["navigate", "screenshot", "extract_links"]
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/test-real-time-browser",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test directo exitoso: {result.get('success', False)}")
            print(f"📊 Acciones completadas: {len(result.get('actions_completed', []))}")
            
            for action in result.get('actions_completed', []):
                print(f"   - {action.get('action', 'unknown')}: {action.get('status', 'unknown')}")
            
            return True
        else:
            print(f"❌ Error en test directo: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test directo: {e}")
        return False

def main():
    """Ejecutar todos los tests de diagnóstico"""
    print("🚀 DIAGNÓSTICO DE NAVEGACIÓN EN TIEMPO REAL")
    print("=" * 60)
    print(f"Task ID de prueba: {TEST_TASK_ID}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 60)
    
    tests = [
        test_websocket_manager_available,
        test_unified_web_search_tool,
        test_task_execution,
        test_web_search_tool_direct,
        test_websocket_debug_logs
    ]
    
    results = []
    
    for i, test_func in enumerate(tests, 1):
        print(f"\n📋 Ejecutando Test {i}/{len(tests)}: {test_func.__name__}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_func.__name__, result))
            
            if result:
                print(f"✅ Test {i} EXITOSO")
            else:
                print(f"❌ Test {i} FALLÓ")
                
        except Exception as e:
            print(f"💥 Test {i} EXCEPCIÓN: {e}")
            results.append((test_func.__name__, False))
        
        print("-" * 40)
        time.sleep(2)  # Pausa entre tests
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    successful_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("-" * 60)
    print(f"📈 ÉXITO: {successful_tests}/{total_tests} tests ({successful_tests/total_tests*100:.1f}%)")
    
    if successful_tests == total_tests:
        print("🎉 TODOS LOS TESTS PASARON - La navegación en tiempo real debería funcionar")
    elif successful_tests >= total_tests * 0.6:
        print("⚠️ ALGUNOS TESTS FALLARON - Revisar los logs para identificar el problema específico")
    else:
        print("🚨 MÚLTIPLES TESTS FALLARON - Hay problemas significativos con la navegación en tiempo real")
    
    print("=" * 60)
    print("💡 PRÓXIMOS PASOS:")
    print("1. Revisar los logs de WebSocket en /tmp/websocket_debug.log")
    print("2. Verificar conexión WebSocket desde el frontend")
    print("3. Comprobar que los eventos lleguen al TerminalView")
    print("4. Revisar configuración de CORS y rutas /api/socket.io/")

if __name__ == "__main__":
    main()