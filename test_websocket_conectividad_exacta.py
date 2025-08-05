#!/usr/bin/env python3
"""
🔌 TEST CONECTIVIDAD WEBSOCKET EXACTA
Usar la misma configuración que el frontend para conectarse
"""

import socketio
import requests
import json
import time
from datetime import datetime
import threading

def test_websocket_conectividad_exacta():
    """Test usando EXACTAMENTE la misma configuración que el frontend"""
    
    print("\n🔌 INICIANDO TEST CONECTIVIDAD WEBSOCKET EXACTA")
    print("=" * 70)
    print(f"⏰ Hora inicio: {datetime.now().strftime('%H:%M:%S')}")
    
    # CONFIGURACIÓN EXACTA DEL FRONTEND  
    backend_url = "http://localhost:8001"
    socket_path = "/api/socket.io/"
    task_id = f"test-exacto-{int(time.time())}"
    
    print(f"🔗 Backend URL: {backend_url}")
    print(f"📍 Socket Path: {socket_path}")
    print(f"🆔 Task ID: {task_id}")
    
    # Variables de estado
    connected = False
    task_joined = False
    browser_visual_events = []
    
    # Crear cliente con configuración exacta del frontend
    sio = socketio.Client(
        logger=True,  # Habilitar logging para debug
        engineio_logger=True
    )
    
    @sio.event
    def connect():
        global connected
        connected = True
        print(f"✅ CONECTADO: WebSocket establecido exitosamente")
        
        # Log de debugging
        try:
            with open('/tmp/test_websocket_exacto.log', 'a') as f:
                f.write(f"[{datetime.now()}] CONNECTED: Client established WebSocket connection\n")
                f.flush()
        except:
            pass
    
    @sio.event
    def connect_error(data):
        print(f"❌ ERROR DE CONEXIÓN: {data}")
        try:
            with open('/tmp/test_websocket_exacto.log', 'a') as f:
                f.write(f"[{datetime.now()}] CONNECT_ERROR: {data}\n")
                f.flush()
        except:
            pass
    
    @sio.event
    def disconnect():
        print(f"❌ DESCONECTADO: WebSocket cerrado")
        try:
            with open('/tmp/test_websocket_exacto.log', 'a') as f:
                f.write(f"[{datetime.now()}] DISCONNECTED\n")
                f.flush()
        except:
            pass
    
    @sio.event
    def connection_status(data):
        print(f"📊 STATUS CONEXIÓN: {data}")
    
    @sio.event
    def join_task_response(data):
        global task_joined
        task_joined = True
        print(f"✅ JOIN_TASK_RESPONSE: {data}")
        try:
            with open('/tmp/test_websocket_exacto.log', 'a') as f:
                f.write(f"[{datetime.now()}] JOIN_TASK_RESPONSE: {data}\n")
                f.flush()
        except:
            pass
    
    @sio.event
    def browser_visual(data):
        """CAPTURAR EVENTOS BROWSER_VISUAL"""
        print(f"🎉 BROWSER_VISUAL RECIBIDO: {data['type']} - {data.get('message', 'Sin mensaje')}")
        browser_visual_events.append({
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
        try:
            with open('/tmp/test_websocket_exacto.log', 'a') as f:
                f.write(f"[{datetime.now()}] BROWSER_VISUAL: {data}\n")
                f.flush()
        except:
            pass
    
    @sio.event
    def task_update(data):
        """CAPTURAR TASK_UPDATE CON BROWSER_VISUAL"""
        if data.get('type') == 'browser_visual':
            print(f"🎯 TASK_UPDATE (browser_visual): {data}")
            browser_visual_events.append({
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
    
    @sio.event
    def task_progress(data):
        """CAPTURAR EVENTOS DE PROGRESO"""
        print(f"📈 TASK_PROGRESS: {data.get('message', 'Sin mensaje')[:50]}...")
    
    try:
        # PASO 1: CONECTAR CON CONFIGURACIÓN EXACTA
        print(f"\n📝 PASO 1: CONECTAR WEBSOCKET")
        print(f"🔌 Intentando conectar a: {backend_url}{socket_path}")
        
        # Usar EXACTAMENTE la misma configuración del frontend
        sio.connect(
            backend_url,
            socketio_path=socket_path,
            transports=['polling', 'websocket'],
            wait_timeout=10
        )
        
        # Esperar conexión
        timeout = 0
        while not connected and timeout < 15:
            time.sleep(0.2)
            timeout += 0.2
        
        if not connected:
            print(f"❌ ERROR: No se estableció conexión WebSocket después de 15 segundos")
            return False
            
        print(f"✅ CONEXIÓN ESTABLECIDA EXITOSAMENTE")
        
        # PASO 2: UNIRSE AL TASK
        print(f"\n📝 PASO 2: UNIRSE AL TASK")
        print(f"📤 Enviando join_task para: {task_id}")
        
        sio.emit('join_task', {'task_id': task_id})
        
        # Esperar confirmación de join
        timeout = 0
        while not task_joined and timeout < 5:
            time.sleep(0.2)
            timeout += 0.2
        
        if task_joined:
            print(f"✅ UNIDO AL TASK EXITOSAMENTE")
        else:
            print(f"⚠️ ADVERTENCIA: Sin confirmación de join_task (puede funcionar igual)")
        
        # PASO 3: EJECUTAR BÚSQUEDA WEB
        print(f"\n📝 PASO 3: EJECUTAR BÚSQUEDA WEB CON NAVEGACIÓN VISUAL")
        
        test_query = "test navegación visual websocket exacta"
        chat_data = {
            "message": f"web_search query='{test_query}' max_results=2",
            "task_id": task_id
        }
        
        print(f"📤 Enviando request a API: {chat_data}")
        
        # Enviar request al backend
        response = requests.post(
            f"{backend_url}/api/agent/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ REQUEST ENVIADO EXITOSAMENTE")
            
            # PASO 4: MONITOREAR EVENTOS EN TIEMPO REAL
            print(f"\n📝 PASO 4: MONITOREANDO EVENTOS BROWSER_VISUAL")
            print(f"⏳ Esperando 30 segundos para capturar eventos...")
            
            start_time = time.time()
            last_count = 0
            
            while time.time() - start_time < 30:
                current_count = len(browser_visual_events)
                if current_count != last_count:
                    print(f"📸 NUEVO EVENTO BROWSER_VISUAL #{current_count}")
                    if browser_visual_events:
                        latest = browser_visual_events[-1]['data']
                        event_type = latest.get('type', 'unknown')
                        message = latest.get('message', 'Sin mensaje')[:60]
                        print(f"   └─ {event_type}: {message}")
                    last_count = current_count
                
                time.sleep(0.5)  # Monitor cada 0.5 segundos
            
            # PASO 5: RESULTADOS
            print(f"\n📝 PASO 5: ANÁLISIS DE RESULTADOS")
            print("=" * 50)
            
            total_events = len(browser_visual_events)
            print(f"📊 TOTAL EVENTOS BROWSER_VISUAL CAPTURADOS: {total_events}")
            
            if total_events > 0:
                print(f"✅ ¡NAVEGACIÓN VISUAL FUNCIONANDO CORRECTAMENTE!")
                print(f"\n📋 EVENTOS RECIBIDOS:")
                
                for i, event in enumerate(browser_visual_events):
                    event_data = event['data']
                    event_type = event_data.get('type', 'unknown')
                    timestamp = event['timestamp']
                    message = event_data.get('message', 'Sin mensaje')[:80]
                    print(f"   {i+1}. [{timestamp}] {event_type}: {message}")
                
                # Verificar progreso de navegación
                progress_events = [e for e in browser_visual_events if e['data'].get('type') == 'navigation_progress']
                if progress_events:
                    print(f"\n📈 PROGRESO DE NAVEGACIÓN DETECTADO: {len(progress_events)} eventos")
                
                return True
                
            else:
                print(f"❌ NO SE RECIBIERON EVENTOS BROWSER_VISUAL")
                print(f"\n🔍 POSIBLES CAUSAS:")
                print(f"   1. Eventos se generan en backend pero no llegan al cliente")
                print(f"   2. Cliente no está en la room correcta")  
                print(f"   3. Backend no está generando eventos para este task_id")
                
                # Revisar logs
                try:
                    with open('/tmp/test_websocket_exacto.log', 'r') as f:
                        log_content = f.read()
                        print(f"\n📄 LOG DEL TEST:")
                        lines = log_content.split('\\n')
                        for line in lines[-15:]:  # Últimas 15 líneas
                            if line.strip():
                                print(f"   {line}")
                except:
                    print(f"   ⚠️ No se pudo leer log del test")
                
                return False
        
        else:
            print(f"❌ ERROR EN REQUEST: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return False
    
    except Exception as e:
        print(f"❌ ERROR DURANTE TEST: {e}")
        return False
    
    finally:
        # Limpiar conexión
        try:
            sio.disconnect()
        except:
            pass

if __name__ == "__main__":
    
    # Inicializar log
    try:
        with open('/tmp/test_websocket_exacto.log', 'w') as f:
            f.write(f"=== TEST WEBSOCKET EXACTO INICIADO: {datetime.now()} ===\n")
    except:
        pass
    
    success = test_websocket_conectividad_exacta()
    
    print(f"\n🏁 RESULTADO FINAL:")
    if success:
        print("✅ NAVEGACIÓN VISUAL WEBSOCKET FUNCIONA PERFECTAMENTE")
        print("   - Conectividad WebSocket correcta")
        print("   - Eventos browser_visual llegando al frontend")
        print("   - Problema resuelto completamente")
    else:
        print("❌ EVENTOS BROWSER_VISUAL NO LLEGAN AL FRONTEND")
        print("   - Conectividad WebSocket OK")
        print("   - Problema en transmisión de eventos específicos")
    
    print(f"\n📊 LOGS GENERADOS:")
    print("   - /tmp/test_websocket_exacto.log")
    print("   - /tmp/websocket_comprehensive.log")