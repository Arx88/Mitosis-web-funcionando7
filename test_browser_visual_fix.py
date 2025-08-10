#!/usr/bin/env python3
"""
🧪 TEST DE NAVEGACIÓN VISUAL - VERIFICAR CORRECCIÓN DE BROWSER_VISUAL EVENTS
Prueba específica para validar que los eventos browser_visual se emiten correctamente
"""

import requests
import time
import json
from datetime import datetime

def test_browser_visual_functionality():
    """Test específico para eventos browser_visual"""
    
    print("🧪 INICIANDO TEST DE NAVEGACIÓN VISUAL...")
    print("=" * 60)
    
    # Crear task_id único para el test
    test_task_id = f"test-browser-visual-fix-{int(time.time())}"
    print(f"📋 Test Task ID: {test_task_id}")
    
    # Preparar datos para búsqueda web que debería generar eventos browser_visual
    search_data = {
        "message": "busca información sobre Python programming 2025",
        "task_id": test_task_id
    }
    
    print(f"🔍 Enviando búsqueda web para generar eventos browser_visual...")
    print(f"   Query: {search_data['message']}")
    print(f"   Task ID: {search_data['task_id']}")
    
    try:
        # Realizar petición de búsqueda
        response = requests.post(
            'http://localhost:8001/api/agent/chat',
            json=search_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Petición enviada exitosamente")
            print(f"   Response task_id: {result.get('task_id')}")
            print(f"   Plan steps: {len(result.get('plan', []))}")
            
            # Esperar un momento para que se procese
            print(f"⏳ Esperando 10 segundos para procesamiento...")
            time.sleep(10)
            
            # Verificar logs de WebSocket para eventos browser_visual
            print(f"🔍 Verificando logs de WebSocket...")
            
            try:
                with open('/tmp/websocket_debug.log', 'r') as f:
                    logs = f.read()
                    
                # Buscar evidencia de eventos browser_visual en logs
                visual_events_found = 0
                for line in logs.split('\n'):
                    if test_task_id in line and ('browser_visual' in line.lower() or 'navegación visual' in line.lower()):
                        visual_events_found += 1
                        print(f"   📸 BROWSER_VISUAL event encontrado: {line.strip()}")
                
                if visual_events_found > 0:
                    print(f"✅ BROWSER_VISUAL EVENTS DETECTADOS: {visual_events_found} eventos encontrados")
                    print(f"✅ CORRECCIÓN EXITOSA: Los eventos browser_visual se están generando")
                    return True
                else:
                    print(f"❌ NO SE ENCONTRARON EVENTOS BROWSER_VISUAL")
                    print(f"⚠️ Los eventos pueden estar funcionando pero no aparecer en logs")
                    
                    # Verificar si al menos hay actividad de búsqueda web
                    search_activity = sum(1 for line in logs.split('\n') if test_task_id in line and 'WEB SEARCH' in line)
                    if search_activity > 0:
                        print(f"✅ BÚSQUEDA WEB ACTIVA: {search_activity} eventos de búsqueda detectados")
                        print(f"⚠️ La funcionalidad base funciona, puede ser problema de logging de browser_visual")
                        return False
                    else:
                        print(f"❌ NO HAY ACTIVIDAD DE BÚSQUEDA WEB DETECTADA")
                        return False
                        
            except FileNotFoundError:
                print(f"⚠️ Archivo de log no encontrado: /tmp/websocket_debug.log")
                return False
                
        else:
            print(f"❌ Error en petición: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante test: {str(e)}")
        return False

def verify_websocket_functionality():
    """Verificar que WebSocket esté funcionando"""
    print(f"\n🔌 VERIFICANDO FUNCIONALIDAD WEBSOCKET...")
    
    try:
        # Test básico de health endpoint
        response = requests.get('http://localhost:8001/api/health', timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend funcionando: {health_data}")
            return True
        else:
            print(f"❌ Backend no responde correctamente: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error verificando backend: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"🧪 TEST DE CORRECCIÓN BROWSER_VISUAL")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Objetivo: Verificar que eventos browser_visual funcionen correctamente")
    print()
    
    # Verificar que el backend esté funcionando
    if not verify_websocket_functionality():
        print(f"❌ Backend no está funcionando correctamente")
        exit(1)
    
    # Ejecutar test principal
    success = test_browser_visual_functionality()
    
    print()
    print("=" * 60)
    if success:
        print(f"✅ TEST EXITOSO: Los eventos browser_visual están funcionando")
        print(f"🎉 CORRECCIÓN CONFIRMADA: La navegación visual en tiempo real funciona")
    else:
        print(f"❌ TEST FALLIDO: Los eventos browser_visual necesitan más corrección")
        print(f"🔧 PRÓXIMOS PASOS: Revisar la implementación del WebSocket en _emit_browser_visual")
    
    print(f"📝 Log completo disponible en: /tmp/websocket_debug.log")