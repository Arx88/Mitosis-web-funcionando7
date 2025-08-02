#!/usr/bin/env python3
"""
Prueba directa de conexión WebSocket para diagnosticar el problema
"""

import socketio
import time
import requests

def test_websocket_connection():
    print("🔌 Testing WebSocket connection to Mitosis backend...")
    
    # URL del backend
    backend_url = "https://0e9acadc-c511-44ef-9913-029260092624.preview.emergentagent.com"
    
    # 1. Probar HTTP polling primero
    print("\n1. Testing HTTP polling...")
    try:
        response = requests.get(f"{backend_url}/api/socket.io/?EIO=4&transport=polling")
        if response.status_code == 200:
            print(f"✅ HTTP polling works: {response.text[:100]}...")
        else:
            print(f"❌ HTTP polling failed: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTP polling error: {e}")
    
    # 2. Probar conexión SocketIO
    print("\n2. Testing SocketIO connection...")
    try:
        sio = socketio.Client(
            logger=True,
            engineio_logger=True
        )
        
        @sio.event
        def connect():
            print("✅ SocketIO connected successfully!")
            
        @sio.event 
        def disconnect():
            print("❌ SocketIO disconnected")
            
        @sio.event
        def connect_error(data):
            print(f"❌ SocketIO connection error: {data}")
            
        @sio.event
        def task_update(data):
            print(f"📡 Received task_update: {data}")
            
        @sio.event
        def log_message(data):
            print(f"📝 Received log_message: {data}")
            
        @sio.event
        def browser_activity(data):
            print(f"🌐 Received browser_activity: {data}")
        
        # Conectar usando la configuración correcta
        print(f"Connecting to: {backend_url}")
        sio.connect(
            backend_url,
            socketio_path='/api/socket.io/',
            transports=['polling', 'websocket']
        )
        
        # Unirse a una sala de prueba
        print("Joining test task room...")
        test_task_id = "websocket-test-" + str(int(time.time()))
        sio.emit('join_task', {'task_id': test_task_id})
        
        # Esperar por eventos
        print(f"Listening for events for task: {test_task_id}")
        print("Waiting 10 seconds for any events...")
        time.sleep(10)
        
        # Limpiar
        sio.emit('leave_task', {'task_id': test_task_id})
        sio.disconnect()
        
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ SocketIO test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_websocket_connection()