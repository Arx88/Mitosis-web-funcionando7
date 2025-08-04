#!/usr/bin/env python3
"""
🧪 TEST WEBSOCKET DIRECTO - Conectar directamente al WebSocket para verificar eventos browser_visual
"""

import socketio
import requests
import time
import threading
from datetime import datetime

def test_websocket_browser_visual():
    """Conectar al WebSocket y verificar si llegan eventos browser_visual"""
    
    print("\n🧪 INICIANDO TEST WEBSOCKET DIRECTO")
    print("=" * 50)
    print(f"⏰ Hora inicio: {datetime.now().strftime('%H:%M:%S')}")
    
    # Variables para capturar eventos
    browser_visual_events = []
    task_update_events = []
    all_events = []
    
    # Crear cliente SocketIO
    sio = socketio.Client(logger=False, engineio_logger=False)
    
    @sio.event
    def connect():
        print("✅ Conectado al WebSocket")
    
    @sio.event
    def disconnect():
        print("❌ Desconectado del WebSocket")
    
    @sio.event
    def browser_visual(data):
        print(f"📸 ¡EVENTO BROWSER_VISUAL RECIBIDO! {data}")
        browser_visual_events.append(data)
        all_events.append(('browser_visual', data))
    
    @sio.event
    def task_update(data):
        if 'browser_visual' in str(data).lower():
            print(f"📋 Task update con browser_visual: {data}")
        task_update_events.append(data)
        all_events.append(('task_update', data))
    
    @sio.event
    def task_progress(data):
        if 'visual' in str(data).lower():
            print(f"📈 Task progress con visual: {data}")
        all_events.append(('task_progress', data))
        
    @sio.event  
    def connect_error(data):
        print(f"❌ Error de conexión: {data}")
    
    try:
        # Conectar al WebSocket
        print("🔌 Conectando al WebSocket...")
        sio.connect('http://localhost:8001')
        
        # Crear task_id único
        task_id = f"test-websocket-{int(time.time())}"
        print(f"🆔 Task ID: {task_id}")
        
        # Unirse a la room de la task
        print("🔗 Uniéndose a task room...")
        sio.emit('join_task', {'task_id': task_id})
        time.sleep(1)  # Esperar confirmación
        
        # Iniciar navegación en thread separado
        def hacer_navegacion():
            try:
                print("📤 Enviando request de navegación...")
                response = requests.post(
                    "http://localhost:8001/api/agent/chat",
                    json={
                        "message": f"web_search query='test websocket browser visual' max_results=2",
                        "task_id": task_id
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                print(f"📥 Response status: {response.status_code}")
            except Exception as e:
                print(f"❌ Error en request: {e}")
        
        # Ejecutar navegación en background
        nav_thread = threading.Thread(target=hacer_navegacion)
        nav_thread.daemon = True
        nav_thread.start()
        
        # Escuchar eventos por 20 segundos
        print("👂 Escuchando eventos por 20 segundos...")
        time.sleep(20)
        
        # Resultados
        print(f"\n📊 RESULTADOS DEL TEST:")
        print("=" * 30)
        print(f"🎯 Eventos browser_visual capturados: {len(browser_visual_events)}")
        print(f"📋 Eventos task_update capturados: {len(task_update_events)}")
        print(f"📈 Total eventos capturados: {len(all_events)}")
        
        if browser_visual_events:
            print(f"\n✅ ¡ÉXITO! Eventos browser_visual encontrados:")
            for i, event in enumerate(browser_visual_events):
                print(f"   📸 Evento {i+1}: {event}")
        else:
            print(f"\n❌ NO se encontraron eventos browser_visual directos")
            
        # Mostrar algunos eventos para debugging
        print(f"\n📋 Últimos 3 eventos capturados:")
        for event_type, event_data in all_events[-3:]:
            print(f"   🔔 {event_type}: {str(event_data)[:100]}...")
            
        return len(browser_visual_events) > 0
        
    except Exception as e:
        print(f"❌ Error durante test WebSocket: {e}")
        return False
        
    finally:
        try:
            sio.disconnect()
        except:
            pass

if __name__ == "__main__":
    success = test_websocket_browser_visual()
    
    print(f"\n🏁 RESULTADO FINAL:")
    if success:
        print("✅ Eventos browser_visual confirmados - NAVEGACIÓN VISUAL FUNCIONANDO")
    else:
        print("❌ Eventos browser_visual no confirmados - Continuar investigación")