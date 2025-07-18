#!/usr/bin/env python3
"""
Focused Mitosis Agent Testing - Based on Actual Available Endpoints

This script tests the actual available endpoints and focuses on the key issues
mentioned in the review request:
1. Agent not creating proper plans
2. Not solving real tasks  
3. Showing generic success messages instead of real results
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"

def test_agent_real_vs_generic():
    """Test the core issue: Real results vs generic messages"""
    print("🔍 TESTING CORE ISSUE: Real Results vs Generic Messages")
    print("="*80)
    
    # Test 1: Simple conversation (should be simple response)
    print("\n1️⃣ Testing Simple Conversation:")
    simple_response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", 
                                  json={"message": "Hola, ¿cómo estás?"}, 
                                  timeout=30)
    
    if simple_response.status_code == 200:
        simple_data = simple_response.json()
        print(f"✅ Status: {simple_response.status_code}")
        print(f"📝 Response: {simple_data.get('response', '')[:200]}...")
        print(f"🧠 Memory used: {simple_data.get('memory_used', False)}")
        print(f"🆔 Task ID: {simple_data.get('task_id', 'None')}")
        print(f"📋 Mode: {simple_data.get('mode', 'None')}")
        
        # Check if it's generic
        response_text = simple_data.get('response', '')
        is_generic = "Tarea completada exitosamente" in response_text
        print(f"⚠️  Generic response detected: {is_generic}")
    else:
        print(f"❌ Failed: {simple_response.status_code}")
    
    # Test 2: Complex task that should trigger planning
    print("\n2️⃣ Testing Complex Task (Should Create Real Plan):")
    complex_response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", 
                                   json={"message": "Crea un informe detallado sobre las tendencias de inteligencia artificial en 2025"}, 
                                   timeout=60)
    
    if complex_response.status_code == 200:
        complex_data = complex_response.json()
        print(f"✅ Status: {complex_response.status_code}")
        print(f"📝 Response length: {len(complex_data.get('response', ''))}")
        print(f"📝 Response preview: {complex_data.get('response', '')[:300]}...")
        print(f"🧠 Memory used: {complex_data.get('memory_used', False)}")
        print(f"🆔 Task ID: {complex_data.get('task_id', 'None')}")
        print(f"📋 Mode: {complex_data.get('mode', 'None')}")
        
        # Check for plan
        if 'plan' in complex_data:
            plan = complex_data['plan']
            print(f"📋 Plan detected: {type(plan)} with {len(plan) if isinstance(plan, (list, dict)) else 'unknown'} items")
            if isinstance(plan, list):
                print("📋 Plan steps:")
                for i, step in enumerate(plan[:3]):  # Show first 3 steps
                    print(f"   {i+1}. {step}")
            elif isinstance(plan, dict):
                print(f"📋 Plan keys: {list(plan.keys())}")
        
        # Check if it's generic
        response_text = complex_data.get('response', '')
        is_generic = "Tarea completada exitosamente" in response_text
        print(f"⚠️  Generic response detected: {is_generic}")
        
        # Check for real content
        has_real_content = len(response_text) > 500 and any(
            keyword in response_text.lower() 
            for keyword in ['inteligencia artificial', 'tendencias', '2025', 'análisis', 'tecnología']
        )
        print(f"✅ Real content detected: {has_real_content}")
    else:
        print(f"❌ Failed: {complex_response.status_code}")
    
    # Test 3: WebSearch task
    print("\n3️⃣ Testing WebSearch Task:")
    websearch_response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", 
                                     json={
                                         "message": "Busca información sobre las últimas innovaciones en inteligencia artificial",
                                         "search_mode": "websearch"
                                     }, 
                                     timeout=60)
    
    if websearch_response.status_code == 200:
        websearch_data = websearch_response.json()
        print(f"✅ Status: {websearch_response.status_code}")
        print(f"📝 Response length: {len(websearch_data.get('response', ''))}")
        print(f"🔍 Search mode: {websearch_data.get('search_mode', 'None')}")
        print(f"🔍 Search data: {bool(websearch_data.get('search_data'))}")
        
        if 'search_data' in websearch_data:
            search_data = websearch_data['search_data']
            print(f"🔍 Search data keys: {list(search_data.keys()) if isinstance(search_data, dict) else 'Not a dict'}")
            if isinstance(search_data, dict) and 'sources' in search_data:
                print(f"🔍 Sources found: {len(search_data['sources'])}")
        
        # Check if it's actually using web search
        response_text = websearch_data.get('response', '')
        has_search_results = any(
            keyword in response_text.lower() 
            for keyword in ['fuente', 'según', 'información', 'datos', 'resultados']
        )
        print(f"✅ Search results in response: {has_search_results}")
    else:
        print(f"❌ Failed: {websearch_response.status_code}")

def test_planning_system():
    """Test the planning system specifically"""
    print("\n🔍 TESTING PLANNING SYSTEM")
    print("="*80)
    
    # Test generate-plan endpoint
    plan_response = requests.post(f"{BASE_URL}{API_PREFIX}/generate-plan", 
                                json={
                                    "task": "Crear una aplicación web simple con HTML, CSS y JavaScript",
                                    "context": {"user_preferences": {"framework": "vanilla"}}
                                }, 
                                timeout=30)
    
    if plan_response.status_code == 200:
        plan_data = plan_response.json()
        print(f"✅ Generate Plan Status: {plan_response.status_code}")
        print(f"📋 Response keys: {list(plan_data.keys())}")
        
        if 'plan' in plan_data:
            plan = plan_data['plan']
            print(f"📋 Plan type: {type(plan)}")
            if isinstance(plan, list):
                print(f"📋 Plan has {len(plan)} steps:")
                for i, step in enumerate(plan):
                    print(f"   {i+1}. {step}")
            elif isinstance(plan, dict):
                print(f"📋 Plan structure: {list(plan.keys())}")
                if 'steps' in plan:
                    steps = plan['steps']
                    print(f"📋 Steps: {len(steps) if isinstance(steps, list) else 'Not a list'}")
        
        # Check for complexity and time estimates
        if 'complexity' in plan_data:
            print(f"🎯 Complexity: {plan_data['complexity']}")
        if 'estimated_time' in plan_data:
            print(f"⏱️  Estimated time: {plan_data['estimated_time']}")
    else:
        print(f"❌ Generate Plan Failed: {plan_response.status_code}")
        try:
            error_data = plan_response.json()
            print(f"❌ Error: {error_data}")
        except:
            print(f"❌ Error text: {plan_response.text}")

def test_available_endpoints():
    """Test all available endpoints"""
    print("\n🔍 TESTING AVAILABLE ENDPOINTS")
    print("="*80)
    
    endpoints = [
        ('/health', 'GET'),
        ('/status', 'GET'),
        ('/generate-suggestions', 'POST'),
        ('/ollama/check', 'POST'),
        ('/ollama/models', 'POST')
    ]
    
    for endpoint, method in endpoints:
        print(f"\n🔗 Testing {method} {endpoint}")
        try:
            if method == 'GET':
                response = requests.get(f"{BASE_URL}{API_PREFIX}{endpoint}", timeout=10)
            else:
                # POST with minimal data
                test_data = {}
                if endpoint == '/generate-suggestions':
                    test_data = {"context": "test"}
                elif endpoint == '/ollama/check':
                    test_data = {"endpoint": "http://localhost:11434"}
                elif endpoint == '/ollama/models':
                    test_data = {"endpoint": "http://localhost:11434"}
                
                response = requests.post(f"{BASE_URL}{API_PREFIX}{endpoint}", json=test_data, timeout=10)
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"   Error: {response.text[:100]}...")
        except Exception as e:
            print(f"   Exception: {str(e)}")

def test_memory_integration():
    """Test memory integration in chat responses"""
    print("\n🔍 TESTING MEMORY INTEGRATION")
    print("="*80)
    
    # Send multiple messages to test memory persistence
    messages = [
        "Mi nombre es Juan y trabajo en tecnología",
        "¿Recuerdas mi nombre?",
        "¿En qué trabajo?"
    ]
    
    for i, message in enumerate(messages):
        print(f"\n{i+1}️⃣ Message: {message}")
        response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", 
                               json={"message": message}, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Memory used: {data.get('memory_used', False)}")
            print(f"   Response: {data.get('response', '')[:150]}...")
            
            # Check if memory is actually working
            if i > 0:  # For follow-up questions
                response_text = data.get('response', '').lower()
                if i == 1:  # Should remember name
                    remembers_name = 'juan' in response_text
                    print(f"   Remembers name: {remembers_name}")
                elif i == 2:  # Should remember job
                    remembers_job = 'tecnología' in response_text or 'technology' in response_text
                    print(f"   Remembers job: {remembers_job}")
        else:
            print(f"   Failed: {response.status_code}")

def main():
    """Run focused tests"""
    print("🚀 FOCUSED MITOSIS AGENT TESTING")
    print("Focus: Real results vs generic messages, planning, memory")
    print("="*80)
    
    # Core functionality tests
    test_agent_real_vs_generic()
    test_planning_system()
    test_available_endpoints()
    test_memory_integration()
    
    print("\n🎯 TESTING COMPLETE")
    print("="*80)
    print("Key findings will help determine if the agent is working correctly")
    print("or still showing generic success messages instead of real results.")

if __name__ == "__main__":
    main()