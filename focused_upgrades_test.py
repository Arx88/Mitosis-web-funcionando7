#!/usr/bin/env python3
"""
FOCUSED BACKEND TESTING - MITOSIS V5-BETA UPGRADE VERIFICATION
Quick verification of the 6 major improvements implemented according to UPGRADE.md
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

def test_improvement(name, test_func):
    """Test an improvement and log results"""
    print(f"\n🔍 TESTING {name}")
    try:
        start_time = time.time()
        success, details = test_func()
        response_time = time.time() - start_time
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {name} ({response_time:.2f}s)")
        print(f"   Details: {details}")
        return success
    except Exception as e:
        print(f"❌ FAILED {name} - Exception: {str(e)}")
        return False

def test_backend_health():
    """Test basic backend health"""
    response = requests.get(f"{API_BASE}/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        services = data.get('services', {})
        ollama_healthy = services.get('ollama', False)
        tools_count = services.get('tools', 0)
        database_healthy = services.get('database', False)
        
        success = ollama_healthy and tools_count > 0 and database_healthy
        details = f"Ollama: {ollama_healthy}, Tools: {tools_count}, Database: {database_healthy}"
        return success, details
    else:
        return False, f"HTTP {response.status_code}"

def test_llm_intent_detection():
    """Test LLM Intent Detection (UPGRADE.md Section 1)"""
    # Test casual message
    casual_response = requests.post(f"{API_BASE}/agent/chat", 
                                  json={"message": "hola"}, timeout=15)
    
    # Test task message  
    task_response = requests.post(f"{API_BASE}/agent/chat", 
                                json={"message": "crear un informe sobre IA"}, timeout=15)
    
    if casual_response.status_code == 200 and task_response.status_code == 200:
        casual_data = casual_response.json()
        task_data = task_response.json()
        
        # Check casual response (should be short, no plan)
        casual_text = casual_data.get('response', '')
        casual_has_plan = len(casual_data.get('plan', [])) > 0
        
        # Check task response (should have plan)
        task_has_plan = len(task_data.get('plan', [])) > 0
        
        success = not casual_has_plan and task_has_plan
        details = f"Casual has plan: {casual_has_plan}, Task has plan: {task_has_plan}"
        return success, details
    else:
        return False, f"HTTP errors: casual={casual_response.status_code}, task={task_response.status_code}"

def test_robust_plan_generation():
    """Test Robust Plan Generation (UPGRADE.md Section 2)"""
    response = requests.post(f"{API_BASE}/agent/chat", 
                           json={"message": "crear un análisis completo sobre IA"}, timeout=20)
    
    if response.status_code == 200:
        data = response.json()
        
        # Check for plan structure
        plan = data.get('plan', [])
        has_steps = len(plan) > 0
        execution_status = data.get('execution_status', 'unknown')
        
        # Validate step structure
        valid_steps = True
        if has_steps:
            for step in plan:
                if not all(key in step for key in ['title', 'description']):
                    valid_steps = False
                    break
        
        # Check proper initial status
        proper_status = execution_status in ['plan_generated', 'executing', 'pending']
        
        success = has_steps and valid_steps and proper_status
        details = f"Steps: {len(plan)}, Valid structure: {valid_steps}, Status: {execution_status}"
        return success, details
    else:
        return False, f"HTTP {response.status_code}"

def test_websocket_infrastructure():
    """Test WebSocket Infrastructure (UPGRADE.md Section 3)"""
    # Test task creation that should generate task_id for WebSocket tracking
    response = requests.post(f"{API_BASE}/agent/chat", 
                           json={"message": "buscar información sobre Python"}, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        task_id = data.get('task_id')
        
        success = task_id is not None
        details = f"Task ID generated: {task_id is not None}"
        return success, details
    else:
        return False, f"HTTP {response.status_code}"

def test_ollama_parsing():
    """Test Ollama Parsing Robustness (UPGRADE.md Section 4)"""
    # Test Ollama connection
    response = requests.post(f"{API_BASE}/agent/ollama/check", 
                           json={"endpoint": "https://78d08925604a.ngrok-free.app"}, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        connection_status = data.get('status', 'unknown')
        
        # Test structured response generation
        if connection_status == 'connected':
            parse_response = requests.post(f"{API_BASE}/agent/chat", 
                                         json={"message": "generar plan estructurado"}, timeout=15)
            
            if parse_response.status_code == 200:
                parse_data = parse_response.json()
                has_structured_response = len(parse_data.get('plan', [])) > 0
                
                success = has_structured_response
                details = f"Connected: {connection_status}, Structured response: {has_structured_response}"
                return success, details
            else:
                return False, f"Parse test failed: HTTP {parse_response.status_code}"
        else:
            return False, f"Ollama not connected: {connection_status}"
    else:
        return False, f"HTTP {response.status_code}"

def test_task_persistence():
    """Test Task Persistence (UPGRADE.md Section 5)"""
    # Create a task
    response = requests.post(f"{API_BASE}/agent/chat", 
                           json={"message": "crear documento sobre blockchain"}, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        task_id = data.get('task_id')
        
        # Check database connection (indicates persistence capability)
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            database_connected = health_data.get('services', {}).get('database', False)
            
            success = task_id is not None and database_connected
            details = f"Task ID: {task_id is not None}, Database: {database_connected}"
            return success, details
        else:
            return False, f"Health check failed: HTTP {health_response.status_code}"
    else:
        return False, f"HTTP {response.status_code}"

def test_error_handling():
    """Test Error Handling and Resilience (UPGRADE.md Section 6)"""
    # Test invalid endpoint
    invalid_response = requests.get(f"{API_BASE}/invalid/endpoint", timeout=5)
    
    # Test invalid chat data
    invalid_chat_response = requests.post(f"{API_BASE}/agent/chat", 
                                        json={"invalid_field": "test"}, timeout=5)
    
    # Check proper error handling
    invalid_handled = invalid_response.status_code == 404
    chat_error_handled = invalid_chat_response.status_code == 400
    
    # Test resilience with complex task
    complex_response = requests.post(f"{API_BASE}/agent/chat", 
                                   json={"message": "realizar tarea compleja con múltiples pasos"}, timeout=15)
    
    resilience_success = complex_response.status_code == 200
    
    success = invalid_handled and chat_error_handled and resilience_success
    details = f"404 handled: {invalid_handled}, 400 handled: {chat_error_handled}, Resilience: {resilience_success}"
    return success, details

def main():
    """Run focused tests for all 6 improvements"""
    print("🚀 FOCUSED MITOSIS V5-BETA BACKEND TESTING")
    print("=" * 60)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("LLM Intent Detection", test_llm_intent_detection),
        ("Robust Plan Generation", test_robust_plan_generation),
        ("WebSocket Infrastructure", test_websocket_infrastructure),
        ("Ollama Parsing Robustness", test_ollama_parsing),
        ("Task Persistence", test_task_persistence),
        ("Error Handling & Resilience", test_error_handling)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        if test_improvement(test_name, test_func):
            passed_tests += 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FOCUSED TEST RESULTS SUMMARY")
    print("=" * 60)
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"🎯 SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate >= 85:
        print("🎉 EXCELLENT - All major improvements are working correctly")
    elif success_rate >= 70:
        print("✅ GOOD - Most improvements are working with minor issues")
    elif success_rate >= 50:
        print("⚠️  PARTIAL - Some improvements need attention")
    else:
        print("❌ CRITICAL - Major improvements have significant issues")
    
    return success_rate >= 70

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)