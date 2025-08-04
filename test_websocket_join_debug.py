#!/usr/bin/env python3
"""
🔍 DEBUGGING ESPECÍFICO - WebSocket join_task functionality
Verifica que el join_task funcione correctamente y se registren las conexiones
"""

import socketio
import time
import json
from datetime import datetime

class WebSocketJoinTester:
    def __init__(self):
        self.sio = socketio.Client()
        self.connected = False
        self.joined_task = False
        self.task_id = f"debug-join-test-{int(time.time())}"
        
        self.setup_handlers()
        
    def setup_handlers(self):
        @self.sio.event
        def connect():
            print(f"✅ [WEBSOCKET] Connected to server")
            print(f"🔗 [DEBUG] Session ID: {self.sio.sid}")
            self.connected = True
            
        @self.sio.event  
        def disconnect():
            print(f"❌ [WEBSOCKET] Disconnected from server")
            self.connected = False
            
        @self.sio.on('joined_task')
        def on_joined_task(data):
            print(f"🎯 [JOINED_TASK] Response: {json.dumps(data, indent=2)}")
            self.joined_task = True
            
        @self.sio.on('error')
        def on_error(data):
            print(f"❌ [ERROR] {data}")
            
        @self.sio.event
        def connect_error(data):
            print(f"❌ [CONNECT_ERROR] {data}")

    def test_join_task(self):
        """Test específico del join_task functionality"""
        
        print(f"🔍 DEBUGGING WEBSOCKET JOIN_TASK FUNCTIONALITY")
        print(f"🎯 Task ID: {self.task_id}")
        print("=" * 60)
        
        try:
            # 1. Connect to WebSocket
            print(f"🔌 [STEP 1] Connecting to WebSocket...")
            self.sio.connect('http://localhost:8001', 
                           socketio_path='/api/socket.io')
            
            time.sleep(2)
            
            if not self.connected:
                print(f"❌ [FAIL] Could not connect to WebSocket")
                return False
                
            print(f"✅ [SUCCESS] Connected with Session ID: {self.sio.sid}")
            
            # 2. Join task room
            print(f"🔗 [STEP 2] Joining task room...")
            self.sio.emit('join_task', {'task_id': self.task_id})
            
            # Wait for join confirmation
            print(f"⏳ [WAITING] For join_task confirmation...")
            time.sleep(3)
            
            if self.joined_task:
                print(f"✅ [SUCCESS] Successfully joined task room")
            else:
                print(f"❌ [FAIL] Did not receive join_task confirmation")
                
            # 3. Keep connection alive for a bit to see other events
            print(f"👀 [STEP 3] Monitoring for additional events (10 seconds)...")
            time.sleep(10)
            
            return self.joined_task
                
        except Exception as e:
            print(f"❌ [CRITICAL ERROR] Test failed: {e}")
            return False
            
        finally:
            if self.connected:
                self.sio.disconnect()
                
        return False

if __name__ == "__main__":
    print("🚀 STARTING WEBSOCKET JOIN DEBUG TEST")
    print("=" * 60)
    
    tester = WebSocketJoinTester()
    success = tester.test_join_task()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 WEBSOCKET JOIN_TASK: FUNCIONANDO CORRECTAMENTE ✅")
        print("   El problema no está en join_task")
    else:
        print("❌ WEBSOCKET JOIN_TASK: PROBLEMA ENCONTRADO")
        print("   El problema SÍ está en join_task")
    print("=" * 60)