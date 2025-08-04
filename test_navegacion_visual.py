#!/usr/bin/env python3
"""
🧪 TEST DE NAVEGACIÓN VISUAL - Verificar si browser_visual eventos aparecen
Documentar todo el proceso para registro completo
"""

import requests
import json
import time
from datetime import datetime

def test_navegacion_visual():
    """Probar búsqueda web y verificar eventos browser_visual"""
    
    print("\n🧪 INICIANDO TEST DE NAVEGACIÓN VISUAL")
    print("=" * 50)
    print(f"⏰ Hora inicio: {datetime.now().strftime('%H:%M:%S')}")
    
    # PASO 1: Hacer una búsqueda web simple
    print("\n📝 PASO 1: Ejecutar búsqueda web con browser-use")
    
    backend_url = "http://localhost:8001"
    test_query = "navegación web browser-use test"
    
    try:
        # Crear task_id único para el test
        task_id = f"test-navegacion-{int(time.time())}"
        print(f"🆔 Task ID: {task_id}")
        
        # Hacer request al endpoint de chat/búsqueda
        chat_data = {
            "message": f"web_search query='{test_query}' max_results=3",
            "task_id": task_id
        }
        
        print(f"📤 Enviando request: {chat_data}")
        
        response = requests.post(
            f"{backend_url}/api/agent/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response recibida:")
            print(json.dumps(result, indent=2)[:500] + "...")
            
            print(f"\n⏳ Esperando 10 segundos para que se procesen los eventos WebSocket...")
            time.sleep(10)
            
            # PASO 2: Verificar logs para eventos browser_visual
            print("\n📝 PASO 2: Verificar logs para eventos browser_visual")
            
            # Buscar en archivos de log temporales
            import os
            log_files = [
                "/tmp/websocket_debug.log",
                "/var/log/supervisor/backend.out.log"
            ]
            
            browser_visual_found = False
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    print(f"\n🔍 Buscando en: {log_file}")
                    try:
                        with open(log_file, 'r') as f:
                            content = f.read()
                            if "browser_visual" in content:
                                print(f"✅ ¡ENCONTRADO! browser_visual eventos en {log_file}")
                                browser_visual_found = True
                                
                                # Mostrar líneas relevantes
                                lines = content.split('\n')
                                for i, line in enumerate(lines):
                                    if "browser_visual" in line:
                                        print(f"   📄 Línea {i+1}: {line}")
                            else:
                                print(f"❌ No se encontró 'browser_visual' en {log_file}")
                    except Exception as e:
                        print(f"⚠️ Error leyendo {log_file}: {e}")
                else:
                    print(f"⚠️ Log file no existe: {log_file}")
            
            # PASO 3: Resultados del test
            print(f"\n📝 PASO 3: RESULTADOS DEL TEST")
            print("=" * 30)
            
            if browser_visual_found:
                print("✅ EVENTOS BROWSER_VISUAL: ENCONTRADOS")
                print("   ✅ El backend SÍ está emitiendo eventos browser_visual")
                print("   🔍 PROBLEMA POSIBLE: Frontend no recibe o no procesa correctamente")
            else:
                print("❌ EVENTOS BROWSER_VISUAL: NO ENCONTRADOS")
                print("   ❌ El backend NO está emitiendo eventos browser_visual")
                print("   🔍 PROBLEMA: La generación de screenshots no está funcionando")
            
            # Información adicional para debugging
            print(f"\n📊 INFORMACIÓN ADICIONAL:")
            print(f"   🆔 Task ID usado: {task_id}")
            print(f"   🔍 Query de búsqueda: {test_query}")
            print(f"   📡 Backend URL: {backend_url}")
            print(f"   ⏰ Hora finalización: {datetime.now().strftime('%H:%M:%S')}")
            
            return browser_visual_found
            
        else:
            print(f"❌ Error en request: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante test: {e}")
        return False

if __name__ == "__main__":
    success = test_navegacion_visual()
    
    print(f"\n🏁 RESULTADO FINAL:")
    if success:
        print("✅ Eventos browser_visual encontrados - Problema posiblemente en frontend")
    else:
        print("❌ Eventos browser_visual NO encontrados - Problema en backend")
        
    print("\n📝 PARA CONTINUAR INVESTIGACIÓN:")
    print("1. Revisar logs más detallados")
    print("2. Verificar configuración WebSocket en backend")
    print("3. Confirmar si screenshots se están generando en subprocess")
    print("4. Verificar si task_id se está pasando correctamente")