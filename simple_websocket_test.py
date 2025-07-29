#!/usr/bin/env python3
"""
SIMPLE WEBSOCKET COMMUNICATION TEST
Focus on the core WebSocket communication issue between frontend and backend.
"""

import requests
import json
import time
from datetime import datetime

# Backend URL
BACKEND_URL = "https://cca0017e-8b5f-4b34-8012-a22ce8188d1a.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_backend_health():
    """Test backend health"""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            services = data.get('services', {})
            print(f"   ✅ Backend healthy - DB: {services.get('database', False)}, Ollama: {services.get('ollama', False)}")
            return True
        else:
            print(f"   ❌ Backend unhealthy - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend error: {e}")
        return False

def test_websocket_endpoints():
    """Test WebSocket endpoint accessibility"""
    print("🔍 Testing WebSocket endpoints...")
    try:
        # Test Socket.IO endpoint
        response = requests.get(f"{BACKEND_URL}/socket.io/", timeout=10)
        socketio_ok = response.status_code in [200, 400]  # 400 is OK for socket.io
        print(f"   🔌 Socket.IO endpoint (/socket.io/): {response.status_code} - {'✅ OK' if socketio_ok else '❌ FAIL'}")
        
        # Test alternative path
        response2 = requests.get(f"{BACKEND_URL}/api/socket.io/", timeout=10)
        alt_ok = response2.status_code in [200, 400]
        print(f"   🔌 Alt Socket.IO endpoint (/api/socket.io/): {response2.status_code} - {'✅ OK' if alt_ok else '❌ FAIL'}")
        
        return socketio_ok or alt_ok
    except Exception as e:
        print(f"   ❌ WebSocket endpoint error: {e}")
        return False

def test_task_creation():
    """Test task creation"""
    print("🔍 Testing task creation...")
    try:
        payload = {
            "message": "Crear un análisis rápido de mercado para software en 2025"
        }
        
        response = requests.post(f"{API_BASE}/agent/chat", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id', '')
            plan = data.get('plan', [])
            memory_used = data.get('memory_used', False)
            
            print(f"   ✅ Task created - ID: {task_id}")
            print(f"   📋 Plan steps: {len(plan)}")
            print(f"   🧠 Memory used: {memory_used}")
            
            return True, task_id
        else:
            print(f"   ❌ Task creation failed - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False, None
    except Exception as e:
        print(f"   ❌ Task creation error: {e}")
        return False, None

def test_cors_configuration():
    """Test CORS configuration"""
    print("🔍 Testing CORS configuration...")
    try:
        headers = {
            'Origin': 'https://cca0017e-8b5f-4b34-8012-a22ce8188d1a.preview.emergentagent.com',
            'Content-Type': 'application/json'
        }
        
        # Test OPTIONS request
        options_response = requests.options(f"{API_BASE}/agent/chat", headers=headers, timeout=10)
        options_cors = options_response.headers.get('Access-Control-Allow-Origin')
        
        # Test GET request
        get_response = requests.get(f"{API_BASE}/health", headers=headers, timeout=10)
        get_cors = get_response.headers.get('Access-Control-Allow-Origin')
        
        print(f"   🌐 OPTIONS CORS: {options_cors}")
        print(f"   🌐 GET CORS: {get_cors}")
        
        cors_ok = options_cors is not None or get_cors is not None
        print(f"   {'✅ CORS configured' if cors_ok else '❌ CORS not configured'}")
        
        return cors_ok
    except Exception as e:
        print(f"   ❌ CORS test error: {e}")
        return False

def test_agent_status():
    """Test agent status"""
    print("🔍 Testing agent status...")
    try:
        response = requests.get(f"{API_BASE}/agent/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', '')
            ollama = data.get('ollama', {})
            memory = data.get('memory', {})
            tools_count = data.get('tools_count', 0)
            
            print(f"   📊 Agent status: {status}")
            print(f"   🤖 Ollama connected: {ollama.get('connected', False)}")
            print(f"   🧠 Memory enabled: {memory.get('enabled', False)}")
            print(f"   🛠️ Tools available: {tools_count}")
            
            return status == 'running'
        else:
            print(f"   ❌ Agent status error - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Agent status error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 SIMPLE WEBSOCKET COMMUNICATION TEST")
    print("=" * 60)
    print("🎯 Diagnosing WebSocket communication issues")
    print("=" * 60)
    
    results = {}
    
    # Run tests
    results['backend_health'] = test_backend_health()
    results['websocket_endpoints'] = test_websocket_endpoints()
    results['task_creation'], task_id = test_task_creation()
    results['cors_configuration'] = test_cors_configuration()
    results['agent_status'] = test_agent_status()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
    
    # Diagnosis
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSIS")
    print("=" * 60)
    
    if results['backend_health'] and results['websocket_endpoints']:
        print("✅ Backend and WebSocket infrastructure are working")
        
        if results['task_creation']:
            print("✅ Task creation is working - Backend can generate tasks")
            
            if results['cors_configuration']:
                print("✅ CORS is configured - Frontend should be able to connect")
                print("\n🎯 CONCLUSION: WebSocket infrastructure appears to be working correctly")
                print("💡 RECOMMENDATION: The issue may be in the frontend WebSocket client implementation")
                print("🔧 NEXT STEPS: Check frontend WebSocket connection code and event listeners")
            else:
                print("❌ CORS is not configured properly")
                print("\n🎯 CONCLUSION: CORS issues may prevent WebSocket connections")
                print("💡 RECOMMENDATION: Fix CORS configuration for WebSocket endpoints")
        else:
            print("❌ Task creation is not working")
            print("\n🎯 CONCLUSION: Backend cannot create tasks properly")
            print("💡 RECOMMENDATION: Fix task creation before testing WebSocket events")
    else:
        print("❌ Backend or WebSocket infrastructure has issues")
        print("\n🎯 CONCLUSION: Basic infrastructure problems prevent WebSocket communication")
        print("💡 RECOMMENDATION: Fix backend health and WebSocket endpoint accessibility first")
    
    # Specific findings
    print("\n🔍 SPECIFIC FINDINGS:")
    
    if results['websocket_endpoints']:
        print("   ✅ WebSocket endpoints are accessible - Socket.IO server is running")
    else:
        print("   ❌ WebSocket endpoints are not accessible - Socket.IO server may not be running")
    
    if results['agent_status']:
        print("   ✅ Agent is running and ready for WebSocket communication")
    else:
        print("   ❌ Agent is not running properly")
    
    if task_id:
        print(f"   ✅ Task created successfully with ID: {task_id}")
        print("   💡 This task should generate WebSocket events when executed")
    else:
        print("   ❌ No task was created - Cannot test WebSocket events")
    
    return 0 if passed_tests >= 4 else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)