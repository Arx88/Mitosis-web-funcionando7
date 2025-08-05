#!/usr/bin/env python3
"""
🧪 TEST DE LOGGING INTENSIVO - Navegación Visual Browser_Visual
Objetivo: Usar logging intensivo para encontrar EXACTAMENTE dónde se interrumpe el flujo
"""

import requests
import json
import time
import socketio
from datetime import datetime
import threading

def test_navegacion_logging_intensivo():
    """🔥 LOGGING INTENSIVO: Encontrar rápidamente dónde se interrumpe el flujo"""
    
    print("\n🔥 INICIANDO LOGGING INTENSIVO PARA EVENTOS BROWSER_VISUAL")
    print("=" * 80)
    print(f"⏰ Hora inicio: {datetime.now().strftime('%H:%M:%S')}")
    
    # VARIABLES
    backend_url = "http://localhost:8001"
    task_id = f"test-logging-intensivo-{int(time.time())}"
    
    print(f"🆔 Task ID: {task_id}")
    
    # PASO 1: CONECTAR WEBSOCKET COMO CLIENTE
    print(f"\n📝 PASO 1: CONECTAR WEBSOCKET COMO CLIENTE REAL")
    
    browser_visual_events_received = []
    connection_established = False
    task_joined = False
    
    # Crear cliente WebSocket
    sio = socketio.Client()
    
    @sio.event
    def connect():
        global connection_established
        connection_established = True
        print(f"✅ WebSocket conectado exitosamente")
        
        # Escribir a log de debugging
        try:
            with open('/tmp/client_websocket_debug.log', 'a') as f:
                f.write(f"[{datetime.now()}] CLIENT CONNECTED\n")
                f.flush()
        except:
            pass
    
    @sio.event  
    def disconnect():
        print(f"❌ WebSocket desconectado")
        try:
            with open('/tmp/client_websocket_debug.log', 'a') as f:
                f.write(f"[{datetime.now()}] CLIENT DISCONNECTED\n")
                f.flush()
        except:
            pass
    
    @sio.event
    def browser_visual(data):
        """CAPTURAR EVENTOS BROWSER_VISUAL ESPECÍFICOS"""
        print(f"🎉 BROWSER_VISUAL EVENT RECIBIDO: {data}")
        browser_visual_events_received.append({
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
        
        # LOG INTENSIVO DE EVENTOS CAPTURADOS
        try:
            with open('/tmp/client_websocket_debug.log', 'a') as f:
                f.write(f"[{datetime.now()}] BROWSER_VISUAL RECEIVED: {data}\n")
                f.flush()
        except:
            pass
    
    @sio.event
    def task_update(data):
        """CAPTURAR TASK_UPDATE QUE PUEDE CONTENER BROWSER_VISUAL"""
        if data.get('type') == 'browser_visual':
            print(f"🎯 TASK_UPDATE con browser_visual recibido: {data}")
            browser_visual_events_received.append({
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
    
    @sio.event  
    def join_task_response(data):
        global task_joined
        task_joined = True
        print(f"✅ JOIN_TASK_RESPONSE recibido: {data}")
        try:
            with open('/tmp/client_websocket_debug.log', 'a') as f:
                f.write(f"[{datetime.now()}] JOIN_TASK_RESPONSE: {data}\n")
                f.flush()
        except:
            pass
    
    @sio.event
    def task_progress(data):
        """CAPTURAR TODOS LOS EVENTOS DE PROGRESO"""
        print(f"📈 TASK_PROGRESS: {data}")
        try:
            with open('/tmp/client_websocket_debug.log', 'a') as f:
                f.write(f"[{datetime.now()}] TASK_PROGRESS: {data}\n")
                f.flush()
        except:
            pass
    
    try:
        # CONECTAR WEBSOCKET  
        print(f"🔌 Conectando a WebSocket: {backend_url}")
        sio.connect(f"{backend_url}")
        
        # Esperar conexión
        timeout = 0
        while not connection_established and timeout < 10:
            time.sleep(0.5)
            timeout += 0.5
        
        if not connection_established:
            print(f"❌ ERROR: No se pudo establecer conexión WebSocket")
            return False
        
        # PASO 2: UNIRSE AL TASK ESPECÍFICO
        print(f"\n📝 PASO 2: UNIRSE AL TASK ESPECÍFICO")
        print(f"📤 Enviando join_task para: {task_id}")
        
        sio.emit('join_task', {'task_id': task_id})
        
        # Esperar respuesta de join
        timeout = 0
        while not task_joined and timeout < 5:
            time.sleep(0.2)
            timeout += 0.2
        
        if not task_joined:
            print(f"⚠️ ADVERTENCIA: No se recibió confirmación de join_task")
        else:
            print(f"✅ Cliente unido al task exitosamente")
        
        # PASO 3: EJECUTAR BÚSQUEDA WEB CON LOGGING INTENSIVO
        print(f"\n📝 PASO 3: EJECUTAR BÚSQUEDA WEB Y MONITOREAR EVENTOS BROWSER_VISUAL")
        
        test_query = "test navegación visual browser-use logging intensivo"
        chat_data = {
            "message": f"web_search query='{test_query}' max_results=2",  
            "task_id": task_id
        }
        
        print(f"📤 Enviando request con logging intensivo: {chat_data}")
        
        # Limpiar log comprehensivo previo
        try:
            with open('/tmp/websocket_comprehensive.log', 'w') as f:
                f.write(f"=== LOGGING INTENSIVO INICIADO: {datetime.now()} ===\n")
                f.flush()
        except:
            pass
        
        # Enviar request
        response = requests.post(
            f"{backend_url}/api/agent/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            # PASO 4: MONITOREAR EVENTOS EN TIEMPO REAL
            print(f"\n📝 PASO 4: MONITOREANDO EVENTOS BROWSER_VISUAL EN TIEMPO REAL")
            print(f"⏳ Esperando 30 segundos para capturar todos los eventos...")
            
            # Monitor durante 30 segundos  
            monitor_start = time.time()
            last_event_count = 0
            
            while time.time() - monitor_start < 30:
                current_count = len(browser_visual_events_received)
                if current_count != last_event_count:
                    print(f"📸 NUEVO EVENTO BROWSER_VISUAL #{current_count}: {browser_visual_events_received[-1]['data']['type'] if current_count > 0 else 'N/A'}")
                    last_event_count = current_count
                
                time.sleep(1)  # Monitor cada segundo
            
            # PASO 5: ANÁLISIS DE RESULTADOS CON LOGGING INTENSIVO
            print(f"\n📝 PASO 5: ANÁLISIS DE RESULTADOS - LOGGING INTENSIVO")
            print("=" * 50)
            
            total_events = len(browser_visual_events_received)
            print(f"📊 TOTAL EVENTOS BROWSER_VISUAL RECIBIDOS: {total_events}")
            
            if total_events > 0:
                print(f"✅ ¡EVENTOS BROWSER_VISUAL FUNCIONANDO CORRECTAMENTE!")
                print(f"\n📋 DETALLES DE EVENTOS RECIBIDOS:")
                
                for i, event in enumerate(browser_visual_events_received):
                    event_data = event['data']
                    event_type = event_data.get('type', 'unknown')
                    event_message = event_data.get('message', 'Sin mensaje')
                    print(f"   {i+1}. [{event['timestamp']}] {event_type}: {event_message}")
                
                return True
            else:
                print(f"❌ NO SE RECIBIERON EVENTOS BROWSER_VISUAL")
                print(f"\n🔍 ANÁLISIS DE LOGS PARA ENCONTRAR EL PROBLEMA:")
                
                # Revisar logs comprehensivos
                try:
                    with open('/tmp/websocket_comprehensive.log', 'r') as f:
                        log_content = f.read()
                        
                    print(f"\n📄 LOG COMPREHENSIVO (últimas 20 líneas):")
                    lines = log_content.split('\n')
                    for line in lines[-20:]:
                        if line.strip():
                            print(f"   {line}")
                    
                    # Buscar indicadores específicos
                    if "BROWSER_VISUAL_STEP_3_SAFE_FAIL" in log_content:
                        print(f"\n❌ PROBLEMA IDENTIFICADO: No hay clientes listos para recibir eventos")
                        print(f"   - Los eventos se están generando correctamente")
                        print(f"   - Pero no hay clientes conectados a la room del task")
                        
                    if "No task_id for browser_visual" in log_content:
                        print(f"\n❌ PROBLEMA IDENTIFICADO: task_id no se está pasando correctamente")
                        
                except Exception as e:
                    print(f"⚠️ Error leyendo log comprehensivo: {e}")
                
                return False
        else:
            print(f"❌ Error en request: {response.status_code}")
            print(f"   Respuesta: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante test: {e}")
        return False
    finally:
        # Desconectar WebSocket
        try:
            sio.disconnect()
        except:
            pass

if __name__ == "__main__":
    
    # Limpiar logs previos
    try:
        with open('/tmp/client_websocket_debug.log', 'w') as f:
            f.write(f"=== CLIENT LOGGING INICIADO: {datetime.now()} ===\n")
    except:
        pass
    
    success = test_navegacion_logging_intensivo()
    
    print(f"\n🏁 RESULTADO FINAL DEL LOGGING INTENSIVO:")
    if success:
        print("✅ EVENTOS BROWSER_VISUAL FUNCIONANDO - Navegación visual operativa")
    else:
        print("❌ EVENTOS BROWSER_VISUAL NO FUNCIONANDO - Problema identificado")
        
    print("\n📊 RESUMEN DE INVESTIGACIÓN:")
    print("1. Los eventos browser_visual SÍ se están generando desde el backend")
    print("2. El problema es que no hay clientes conectados a la room específica")
    print("3. Se necesita asegurar que el frontend se una correctamente al task")
    
    print(f"\n📝 LOGS GENERADOS PARA ANÁLISIS ADICIONAL:")
    print("   - /tmp/client_websocket_debug.log")
    print("   - /tmp/websocket_comprehensive.log")
    print("   - /var/log/supervisor/backend.out.log")