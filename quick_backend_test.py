#!/usr/bin/env python3
"""
Quick Backend Verification Test for Mitosis V5-beta
"""

import requests
import json
import time
from datetime import datetime

BACKEND_URL = "https://15c16a6c-c05b-4a8b-8862-e44571e2a1d6.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def quick_test():
    print("🚀 Quick Backend Verification Test")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Health Check...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Health: {data.get('status')}")
            print(f"   Database: {data.get('services', {}).get('database')}")
            print(f"   Ollama: {data.get('services', {}).get('ollama')}")
            print(f"   Tools: {data.get('services', {}).get('tools')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Agent Health
    print("\n2. Agent Health...")
    try:
        response = requests.get(f"{API_BASE}/agent/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agent Status: {data.get('status')}")
            ollama_config = data.get('ollama_config', {})
            if ollama_config:
                print(f"   Ollama Endpoint: {ollama_config.get('endpoint')}")
                print(f"   Model: {ollama_config.get('current_model')}")
        else:
            print(f"❌ Agent health failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Agent health error: {e}")
    
    # Test 3: Simple Chat
    print("\n3. Simple Chat Test...")
    try:
        response = requests.post(f"{API_BASE}/agent/chat", 
                               json={'message': 'hola'}, 
                               timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat Response: {len(data.get('response', ''))} chars")
            print(f"   Memory Used: {data.get('memory_used')}")
            print(f"   Task ID: {data.get('task_id')}")
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Chat error: {e}")
    
    # Test 4: Task Chat
    print("\n4. Task Processing Test...")
    try:
        response = requests.post(f"{API_BASE}/agent/chat", 
                               json={'message': 'crear un análisis breve'}, 
                               timeout=20)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Task Response: {len(data.get('response', ''))} chars")
            print(f"   Memory Used: {data.get('memory_used')}")
            print(f"   Plan Steps: {len(data.get('plan', []))}")
            print(f"   Status: {data.get('status')}")
        else:
            print(f"❌ Task processing failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Task processing error: {e}")
    
    # Test 5: Agent Status
    print("\n5. Agent Status...")
    try:
        response = requests.get(f"{API_BASE}/agent/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status Available")
            print(f"   Running: {data.get('status')}")
            print(f"   Memory: {data.get('memory_enabled')}")
        else:
            print(f"❌ Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status error: {e}")
    
    print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    quick_test()