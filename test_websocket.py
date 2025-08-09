#!/usr/bin/env python3
"""
Test WebSocket Connection for Real-time Navigation
"""

import time
import json
import requests
from datetime import datetime

def test_websocket_connection():
    print("🔌 Testing WebSocket Connection...")
    
    # Test 1: Check if WebSocket endpoint is responding
    try:
        response = requests.get("http://localhost:8001/api/socket.io/?EIO=4&transport=polling")
        if response.status_code == 200:
            print("✅ WebSocket endpoint is responsive")
            print(f"Response: {response.text[:100]}...")
        else:
            print(f"❌ WebSocket endpoint error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to WebSocket endpoint: {e}")
        return False
    
    # Test 2: Test basic agent health
    try:
        response = requests.get("http://localhost:8001/api/agent/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Agent health OK")
            print(f"MongoDB: {data.get('mongodb', {}).get('connected', 'unknown')}")
            print(f"Ollama: {data.get('ollama', {}).get('connected', 'unknown')}")
        else:
            print(f"❌ Agent health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Agent health check error: {e}")
    
    # Test 3: Try to emit a test browser_visual event
    try:
        # Import the WebSocket manager from backend
        import sys
        sys.path.append('/app/backend')
        
        from src.websocket.websocket_manager import get_websocket_manager
        
        ws_manager = get_websocket_manager()
        if ws_manager and ws_manager.is_initialized:
            print("✅ WebSocket manager is initialized")
            
            # Try to emit a test event
            test_event = {
                'type': 'test_navigation',
                'task_id': 'test-123',
                'message': 'Test browser visual event',
                'timestamp': time.time(),
                'url': 'https://test.com'
            }
            
            ws_manager.emit_update('test-123', 'browser_visual', test_event)
            print("✅ Test browser_visual event emitted")
            
        else:
            print("❌ WebSocket manager not initialized")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket event test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 MITOSIS WEBSOCKET DIAGNOSTIC TEST")
    print("=====================================")
    success = test_websocket_connection()
    
    if success:
        print("\n✅ ALL TESTS PASSED - WebSocket should be working")
    else:
        print("\n❌ SOME TESTS FAILED - WebSocket needs fixing")