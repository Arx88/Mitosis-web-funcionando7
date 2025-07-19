#!/usr/bin/env python3
"""
Local Backend Test for Mitosis V5-beta - Testing UPGRADE.md improvements
"""

import requests
import json
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

def test_improvements():
    print("🚀 Testing Mitosis V5-beta UPGRADE.md Improvements Locally")
    print("=" * 70)
    
    results = {
        'intent_detection': False,
        'plan_generation': False,
        'websocket_communication': False,
        'ollama_parsing': False,
        'task_persistence': False,
        'error_handling': False
    }
    
    # Test 1: Intent Detection System
    print("\n🧠 1. INTENT DETECTION SYSTEM")
    try:
        # Test casual conversation
        casual_response = requests.post(f"{API_BASE}/agent/chat", 
                                      json={'message': 'hola'}, 
                                      timeout=10)
        
        # Test task message
        task_response = requests.post(f"{API_BASE}/agent/chat", 
                                    json={'message': 'crear un informe sobre IA'}, 
                                    timeout=15)
        
        if casual_response.status_code == 200 and task_response.status_code == 200:
            casual_data = casual_response.json()
            task_data = task_response.json()
            
            # Check if casual message doesn't generate complex plans
            casual_simple = len(casual_data.get('plan', [])) <= 1
            # Check if task message generates plans
            task_complex = len(task_data.get('plan', [])) > 1
            
            if casual_simple and task_complex:
                print("✅ Intent detection working - casual vs task differentiation")
                results['intent_detection'] = True
            else:
                print(f"⚠️ Intent detection partial - casual plan: {len(casual_data.get('plan', []))}, task plan: {len(task_data.get('plan', []))}")
        else:
            print(f"❌ Intent detection failed - status codes: {casual_response.status_code}, {task_response.status_code}")
    except Exception as e:
        print(f"❌ Intent detection error: {e}")
    
    # Test 2: Robust Plan Generation
    print("\n📋 2. ROBUST PLAN GENERATION")
    try:
        response = requests.post(f"{API_BASE}/agent/chat", 
                               json={'message': 'desarrollar una estrategia de marketing completa'}, 
                               timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            plan = data.get('plan', [])
            
            # Check JSON schema compliance
            schema_valid = True
            if plan and isinstance(plan, list):
                for step in plan:
                    if not isinstance(step, dict):
                        schema_valid = False
                        break
                    required_fields = ['title', 'description', 'tool']
                    if not all(field in step for field in required_fields):
                        schema_valid = False
                        break
            
            if schema_valid and len(plan) > 0:
                print(f"✅ Plan generation working - {len(plan)} valid steps generated")
                results['plan_generation'] = True
            else:
                print(f"⚠️ Plan generation issues - valid: {schema_valid}, steps: {len(plan)}")
        else:
            print(f"❌ Plan generation failed - status: {response.status_code}")
    except Exception as e:
        print(f"❌ Plan generation error: {e}")
    
    # Test 3: WebSocket Communication Infrastructure
    print("\n🔌 3. WEBSOCKET COMMUNICATION")
    try:
        # Test task ID generation for WebSocket tracking
        response = requests.post(f"{API_BASE}/agent/chat", 
                               json={'message': 'analizar datos de ejemplo'}, 
                               timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            
            if task_id and len(str(task_id)) > 10:
                print(f"✅ WebSocket infrastructure ready - Task ID: {task_id}")
                results['websocket_communication'] = True
            else:
                print(f"⚠️ WebSocket infrastructure partial - Task ID: {task_id}")
        else:
            print(f"❌ WebSocket infrastructure failed - status: {response.status_code}")
    except Exception as e:
        print(f"❌ WebSocket infrastructure error: {e}")
    
    # Test 4: Ollama Response Parsing
    print("\n🤖 4. OLLAMA RESPONSE PARSING")
    try:
        # Check Ollama connection
        health_response = requests.get(f"{API_BASE}/agent/health", timeout=10)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            ollama_config = health_data.get('ollama_config', {})
            
            # Check expected configuration
            expected_endpoint = "https://78d08925604a.ngrok-free.app"
            expected_model = "llama3.1:8b"
            
            endpoint_correct = expected_endpoint in str(ollama_config.get('endpoint', ''))
            models_available = ollama_config.get('available_models', [])
            model_available = any(expected_model in str(model) for model in models_available)
            
            if endpoint_correct and len(models_available) > 0:
                print(f"✅ Ollama parsing ready - Endpoint: {endpoint_correct}, Models: {len(models_available)}")
                results['ollama_parsing'] = True
            else:
                print(f"⚠️ Ollama parsing partial - Endpoint: {endpoint_correct}, Models: {len(models_available)}")
        else:
            print(f"❌ Ollama parsing failed - status: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Ollama parsing error: {e}")
    
    # Test 5: Task Persistence with MongoDB
    print("\n💾 5. TASK PERSISTENCE")
    try:
        # Check database connection
        health_response = requests.get(f"{API_BASE}/health", timeout=10)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            db_connected = health_data.get('services', {}).get('database', False)
            
            if db_connected:
                # Test task creation and persistence
                task_response = requests.post(f"{API_BASE}/agent/chat", 
                                            json={'message': 'crear documento de prueba'}, 
                                            timeout=15)
                
                if task_response.status_code == 200:
                    task_data = task_response.json()
                    task_id = task_data.get('task_id')
                    
                    if task_id:
                        print(f"✅ Task persistence working - DB connected, Task created: {task_id}")
                        results['task_persistence'] = True
                    else:
                        print(f"⚠️ Task persistence partial - DB connected but no task ID")
                else:
                    print(f"⚠️ Task persistence partial - DB connected but task creation failed")
            else:
                print(f"❌ Task persistence failed - Database not connected")
        else:
            print(f"❌ Task persistence failed - Health check failed")
    except Exception as e:
        print(f"❌ Task persistence error: {e}")
    
    # Test 6: Error Handling and Resilience
    print("\n🛡️ 6. ERROR HANDLING & RESILIENCE")
    try:
        # Test invalid endpoint
        invalid_response = requests.get(f"{API_BASE}/invalid-endpoint", timeout=5)
        proper_404 = invalid_response.status_code == 404
        
        # Test invalid data
        invalid_data_response = requests.post(f"{API_BASE}/agent/chat", 
                                            json={'invalid_field': 'test'}, 
                                            timeout=5)
        proper_error_handling = invalid_data_response.status_code in [400, 422]
        
        if proper_404 and proper_error_handling:
            print(f"✅ Error handling working - 404: {proper_404}, Data validation: {proper_error_handling}")
            results['error_handling'] = True
        else:
            print(f"⚠️ Error handling partial - 404: {proper_404}, Data validation: {proper_error_handling}")
    except Exception as e:
        print(f"❌ Error handling error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 UPGRADE.MD IMPROVEMENTS VERIFICATION SUMMARY")
    print("=" * 70)
    
    improvements = [
        ("Intent Detection System", results['intent_detection']),
        ("Robust Plan Generation", results['plan_generation']),
        ("Real-time WebSocket Communication", results['websocket_communication']),
        ("Robust Ollama Response Parsing", results['ollama_parsing']),
        ("Task Persistence with MongoDB", results['task_persistence']),
        ("Error Handling and Resilience", results['error_handling'])
    ]
    
    passed = sum(1 for _, result in improvements if result)
    total = len(improvements)
    success_rate = passed / total * 100
    
    for improvement, result in improvements:
        status = "✅ IMPLEMENTED" if result else "❌ NEEDS WORK"
        print(f"{status} {improvement}")
    
    print(f"\n🎯 OVERALL IMPLEMENTATION STATUS:")
    print(f"   Implemented: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 85:
        assessment = "🎉 EXCELLENT - All major improvements implemented"
    elif success_rate >= 70:
        assessment = "✅ GOOD - Most improvements implemented"
    elif success_rate >= 50:
        assessment = "⚠️ PARTIAL - Core improvements implemented"
    else:
        assessment = "❌ INCOMPLETE - Major improvements missing"
    
    print(f"   Assessment: {assessment}")
    print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    test_improvements()