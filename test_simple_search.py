#!/usr/bin/env python3
"""
🧪 TEST SIMPLE: Verificar que web search funcione con logs en tiempo real
"""

import requests
import json
import time

def test_direct_web_search():
    """Test directo de búsqueda web sin timeout"""
    
    BACKEND_URL = "http://localhost:8001"
    
    print("🧪 PRUEBA SIMPLE: Búsqueda web con visualización en tiempo real")
    print("=" * 60)
    
    try:
        # Test muy simple con timeout corto
        chat_data = {
            "message": "Busca información sobre IA",
            "task_id": f"simple-test-{int(time.time())}"
        }
        
        print(f"📤 Enviando mensaje: {chat_data['message']}")
        print(f"🆔 Task ID: {chat_data['task_id']}")
        
        response = requests.post(
            f"{BACKEND_URL}/api/agent/chat", 
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=15  # Timeout más corto
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response exitoso!")
            print(f"📊 Success: {result.get('success', False)}")
            
            if result.get('plan'):
                print(f"📋 Plan generado: {len(result.get('plan', []))} pasos")
                for i, step in enumerate(result.get('plan', [])[:3]):  # Primeros 3 pasos
                    print(f"   {i+1}. {step.get('title', 'Sin título')}")
                    print(f"      Herramienta: {step.get('tool', 'Sin herramienta')}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📝 Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_websocket_logs():
    """Verificar logs de WebSocket recientes"""
    print("\n🔍 VERIFICANDO LOGS DE WEBSOCKET:")
    print("-" * 40)
    
    try:
        with open('/tmp/websocket_debug.log', 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-10:]  # Últimas 10 líneas
            
            print("📋 Últimos logs:")
            for line in recent_lines:
                if line.strip():
                    print(f"   {line.strip()}")
            
            # Buscar logs de EVENTLET
            eventlet_logs = [line for line in recent_lines if 'EVENTLET' in line]
            if eventlet_logs:
                print(f"\n✅ Logs de EVENTLET encontrados: {len(eventlet_logs)}")
            else:
                print(f"\n⚠️ No se encontraron logs de EVENTLET")
                
    except Exception as e:
        print(f"❌ Error leyendo logs: {e}")

if __name__ == "__main__":
    success = test_direct_web_search()
    check_websocket_logs()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST SIMPLE EXITOSO - La herramienta de búsqueda responde")
    else:
        print("❌ TEST SIMPLE FALLÓ - Revisar configuración")
    print("=" * 60)