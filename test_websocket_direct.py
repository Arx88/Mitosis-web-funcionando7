#!/usr/bin/env python3
"""
🔌 TEST WEBSOCKET: Conectar directamente para verificar eventos en tiempo real
"""

import socketio
import time
import requests
import json
from threading import Thread

class WebSocketTester:
    def __init__(self, backend_url="http://localhost:8001"):
        self.backend_url = backend_url
        self.sio = socketio.Client()
        self.task_id = None
        self.received_events = []
        
        # Configurar event handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.sio.event
        def connect():
            print("✅ WebSocket conectado!")
            if self.task_id:
                print(f"🔌 Uniéndose a sala: {self.task_id}")
                self.sio.emit('join_task', {'task_id': self.task_id})
        
        @self.sio.event  
        def disconnect():
            print("❌ WebSocket desconectado")
        
        @self.sio.event
        def log_message(data):
            print(f"📝 LOG MESSAGE: {data}")
            self.received_events.append(('log_message', data))
        
        @self.sio.event
        def terminal_activity(data):
            print(f"💻 TERMINAL ACTIVITY: {data}")
            self.received_events.append(('terminal_activity', data))
        
        @self.sio.event
        def browser_activity(data):
            print(f"🌐 BROWSER ACTIVITY: {data}")
            self.received_events.append(('browser_activity', data))
        
        @self.sio.event
        def task_progress(data):
            print(f"📊 TASK PROGRESS: {data}")
            self.received_events.append(('task_progress', data))
    
    def connect_websocket(self):
        """Conectar al WebSocket"""
        try:
            self.sio.connect(self.backend_url, transports=['websocket'])
            return True
        except Exception as e:
            print(f"❌ Error conectando WebSocket: {e}")
            return False
    
    def trigger_web_search(self):
        """Disparar una búsqueda web para generar eventos"""
        try:
            self.task_id = f"websocket-test-{int(time.time())}"
            
            # IMPORTANTE: Unirse a la sala ANTES de disparar la búsqueda
            if self.sio.connected:
                print(f"🔌 Uniéndose a sala: {self.task_id}")
                self.sio.emit('join_task', {'task_id': self.task_id})
                time.sleep(1)  # Dar tiempo a que se una
            
            print(f"🚀 Disparando búsqueda web con ID: {self.task_id}")
            
            chat_data = {
                "message": "Busca información sobre Python 2025",
                "task_id": self.task_id
            }
            
            response = requests.post(
                f"{self.backend_url}/api/agent/chat",
                json=chat_data,
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Chat request exitoso: {result.get('success')}")
                return True
            else:
                print(f"❌ Error en chat: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error disparando búsqueda: {e}")
            return False
    
    def wait_for_events(self, timeout=30):
        """Esperar eventos durante timeout segundos"""
        print(f"⏳ Esperando eventos durante {timeout} segundos...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            self.sio.sleep(1)
            
            # Mostrar eventos recibidos en tiempo real
            if len(self.received_events) > 0:
                for event_type, data in self.received_events[-3:]:  # Últimos 3 eventos
                    print(f"   🔴 EVENTO: {event_type} - {str(data)[:100]}...")
        
        print(f"📊 Total eventos recibidos: {len(self.received_events)}")
        
        # Mostrar resumen
        event_types = {}
        for event_type, _ in self.received_events:
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print("📋 Resumen de eventos:")
        for event_type, count in event_types.items():
            print(f"   - {event_type}: {count}")

def main():
    print("🧪 TEST WEBSOCKET DIRECTO")
    print("=" * 60)
    
    tester = WebSocketTester()
    
    # PASO 1: Conectar WebSocket
    if not tester.connect_websocket():
        print("❌ No se pudo conectar al WebSocket")
        return
    
    time.sleep(2)  # Dar tiempo a la conexión
    
    # PASO 2: Disparar búsqueda web
    if not tester.trigger_web_search():
        print("❌ No se pudo disparar la búsqueda")
        return
    
    # PASO 3: Esperar eventos
    tester.wait_for_events(25)
    
    # RESULTADO
    print("\n" + "=" * 60)
    if len(tester.received_events) > 0:
        print("🎉 SUCCESS: Eventos WebSocket recibidos!")
        print("✅ La visualización en tiempo real está funcionando")
    else:
        print("❌ FAIL: No se recibieron eventos WebSocket")
        print("⚠️ La visualización en tiempo real NO está funcionando")
    
    print("=" * 60)
    
    # Desconectar
    tester.sio.disconnect()

if __name__ == "__main__":
    main()