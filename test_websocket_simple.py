#!/usr/bin/env python3
"""
Test simple de conectividad WebSocket
"""
import socketio
import time
import sys

def test_websocket_connection():
    try:
        print("🔌 Testing WebSocket connection...")
        
        # Create client
        sio = socketio.Client(logger=False, engineio_logger=False)
        
        @sio.event
        def connect():
            print("✅ WebSocket connected successfully!")
            return True
        
        @sio.event
        def disconnect():
            print("❌ WebSocket disconnected")
        
        @sio.event
        def connect_error(data):
            print(f"❌ WebSocket connection error: {data}")
        
        # Try to connect
        try:
            sio.connect('http://localhost:8001', socketio_path='/api/socket.io/')
            print("✅ Connection successful!")
            
            # Test join room
            sio.emit('join_task', {'task_id': 'test-connection-123'})
            print("✅ Join task emitted successfully!")
            
            # Wait a bit
            time.sleep(2)
            
            # Leave room
            sio.emit('leave_task', {'task_id': 'test-connection-123'})
            print("✅ Leave task emitted successfully!")
            
            # Disconnect
            sio.disconnect()
            print("✅ Disconnected cleanly")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_websocket_connection()
    sys.exit(0 if success else 1)