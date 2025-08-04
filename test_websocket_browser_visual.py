#!/usr/bin/env python3
"""
🧪 TEST ESPECÍFICO - WEBSOCKET BROWSER_VISUAL EVENTS
Simula un cliente frontend y verifica si los eventos browser_visual llegan correctamente
"""

import socketio
import requests
import time
import json
import threading
from datetime import datetime

class WebSocketTester:
    def __init__(self):
        self.sio = socketio.Client()
        self.received_events = []
        self.connected = False
        self.task_id = f"websocket-browser-visual-test-{int(time.time())}"
        
        # 🔥 Setup event handlers
        self.setup_handlers()
        
    def setup_handlers(self):
        @self.sio.event
        def connect():
            print(f"✅ [WEBSOCKET] Connected to server")
            self.connected = True
            
            # 🎯 Join the task room immediately
            print(f"🔗 [WEBSOCKET] Joining room: {self.task_id}")
            self.sio.emit('join_task', {'task_id': self.task_id})
            
        @self.sio.event  
        def disconnect():
            print(f"❌ [WEBSOCKET] Disconnected from server")
            self.connected = False
            
        @self.sio.on('browser_visual')
        def on_browser_visual(data):
            timestamp = datetime.now().isoformat()
            print(f"🎉 [SUCCESS] browser_visual event received at {timestamp}!")
            print(f"📸 [BROWSER_VISUAL] Data: {json.dumps(data, indent=2)}")
            self.received_events.append({
                'event': 'browser_visual',
                'data': data,
                'timestamp': timestamp
            })
            
        @self.sio.on('task_progress')
        def on_task_progress(data):
            print(f"📊 [TASK_PROGRESS] {data}")
            
        @self.sio.on('task_update')
        def on_task_update(data):
            print(f"🔄 [TASK_UPDATE] {data}")
            
        @self.sio.event
        def connect_error(data):
            print(f"❌ [ERROR] Connection failed: {data}")

    def test_websocket_browser_visual(self):
        """Test completo de navegación visual via WebSocket"""
        
        print(f"🚀 INICIANDO TEST WEBSOCKET BROWSER_VISUAL")
        print(f"🎯 Task ID: {self.task_id}")
        print("=" * 60)
        
        try:
            # 1. Connect to WebSocket
            print(f"🔌 [STEP 1] Connecting to WebSocket...")
            self.sio.connect('http://localhost:8001', 
                           socketio_path='/api/socket.io')
            
            # Wait for connection
            time.sleep(2)
            
            if not self.connected:
                print(f"❌ [FAIL] Could not connect to WebSocket")
                return False
                
            # 2. Create task via API
            print(f"📝 [STEP 2] Creating task via REST API...")
            task_payload = {
                "message": "Buscar información sobre Python FastAPI para navegación visual",
                "task_id": self.task_id
            }
            
            response = requests.post('http://localhost:8001/api/agent/chat',
                                   json=task_payload,
                                   headers={'Content-Type': 'application/json'})
            
            if response.status_code != 200:
                print(f"❌ [FAIL] Task creation failed: {response.status_code}")
                return False
                
            print(f"✅ [SUCCESS] Task created successfully")
            
            # 3. Execute step with web search (should trigger browser_visual)
            print(f"🌐 [STEP 3] Executing web search step...")
            execute_url = f'http://localhost:8001/api/agent/execute-step-detailed/{self.task_id}/step-1'
            
            # Start execution in background
            def execute_step():
                try:
                    resp = requests.post(execute_url, timeout=30)
                    print(f"📊 [EXECUTION] Step completed with status: {resp.status_code}")
                except Exception as e:
                    print(f"⚠️ [EXECUTION] Step execution error: {e}")
            
            execution_thread = threading.Thread(target=execute_step)
            execution_thread.start()
            
            # 4. Monitor for browser_visual events for 25 seconds
            print(f"👀 [STEP 4] Monitoring for browser_visual events (25 seconds)...")
            monitor_start = time.time()
            
            while time.time() - monitor_start < 25:
                time.sleep(1)
                elapsed = int(time.time() - monitor_start)
                if elapsed % 5 == 0:
                    print(f"⏱️ [MONITOR] {elapsed}s - Events received: {len(self.received_events)}")
            
            # 5. Final results
            print("=" * 60)
            print(f"🏁 TEST COMPLETED")
            print(f"📊 RESULTS:")
            print(f"   - WebSocket Connected: {'✅' if self.connected else '❌'}")
            print(f"   - Task Created: ✅")
            print(f"   - browser_visual Events Received: {len(self.received_events)}")
            
            if self.received_events:
                print(f"   - ✅ SUCCESS: browser_visual events are working!")
                print(f"   - First Event Timestamp: {self.received_events[0]['timestamp']}")
                print(f"   - Event Types: {[e['data'].get('type', 'unknown') for e in self.received_events]}")
                return True
            else:
                print(f"   - ❌ FAIL: No browser_visual events received")
                return False
                
        except Exception as e:
            print(f"❌ [CRITICAL ERROR] Test failed: {e}")
            return False
            
        finally:
            if self.connected:
                self.sio.disconnect()

if __name__ == "__main__":
    tester = WebSocketTester()
    success = tester.test_websocket_browser_visual()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 NAVEGACIÓN VISUAL BROWSER_VISUAL: FUNCIONANDO CORRECTAMENTE ✅")
    else:
        print("❌ NAVEGACIÓN VISUAL BROWSER_VISUAL: NO FUNCIONA - REQUIERE MÁS DEBUGGING")
    print("=" * 60)