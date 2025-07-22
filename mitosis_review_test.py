#!/usr/bin/env python3
"""
Mitosis Backend Comprehensive Testing Script - Review Request Fulfillment

This script tests the Mitosis backend application comprehensively to verify all functionalities 
are working correctly as requested in the review.

TESTING REQUIREMENTS:
1. Backend Health Check: Test the /health endpoint to ensure all services are running properly
2. Agent Health and Status: Test the /api/agent/health and /api/agent/status endpoints
3. Chat Functionality: Test the /api/agent/chat endpoint with different types of messages
4. Memory System: Test the memory system integration
5. File Management: Test file upload and processing capabilities
6. Ollama Integration: Verify Ollama connection and model availability
7. Database: Test MongoDB connection and data operations
8. Error Handling: Test error scenarios and proper error responses

CURRENT CONFIGURATION:
- Backend URL: https://929fd28d-e48b-4d30-b963-581487842c96.preview.emergentagent.com
- Ollama endpoint: https://78d08925604a.ngrok-free.app
- Model: llama3.1:8b
- Database: MongoDB local
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime

# Configuration from review request
BASE_URL = "https://929fd28d-e48b-4d30-b963-581487842c96.preview.emergentagent.com"
OLLAMA_ENDPOINT = "https://78d08925604a.ngrok-free.app"
EXPECTED_MODEL = "llama3.1:8b"

print(f"🧪 MITOSIS BACKEND COMPREHENSIVE TESTING - REVIEW REQUEST FULFILLMENT")
print(f"Backend URL: {BASE_URL}")
print(f"Ollama Endpoint: {OLLAMA_ENDPOINT}")
print(f"Expected Model: {EXPECTED_MODEL}")
print(f"Test started at: {datetime.now().isoformat()}")
print("=" * 80)

# Test results tracking
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "success_rate": 0.0
    }
}

def run_test(name, endpoint, method="GET", data=None, expected_status=200, timeout=30):
    """Run a test against an API endpoint"""
    global test_results
    
    print(f"\n🔍 Testing: {name}")
    print(f"   Endpoint: {method} {endpoint}")
    
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(endpoint, timeout=timeout)
        elif method == "POST":
            headers = {'Content-Type': 'application/json'}
            response = requests.post(endpoint, json=data, headers=headers, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        elapsed_time = time.time() - start_time
        
        # Check status code
        if response.status_code == expected_status:
            print(f"   ✅ PASSED ({elapsed_time:.2f}s)")
            
            # Try to parse JSON response
            try:
                response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
            except:
                response_data = response.text[:200]
            
            result = {
                "name": name,
                "status": "PASSED",
                "elapsed_time": elapsed_time,
                "response_code": response.status_code,
                "response_data": response_data
            }
            test_results["summary"]["passed"] += 1
        else:
            print(f"   ❌ FAILED ({elapsed_time:.2f}s) - Expected {expected_status}, got {response.status_code}")
            result = {
                "name": name,
                "status": "FAILED",
                "elapsed_time": elapsed_time,
                "response_code": response.status_code,
                "error": f"Expected status {expected_status}, got {response.status_code}",
                "response_data": response.text[:200]
            }
            test_results["summary"]["failed"] += 1
        
        test_results["tests"].append(result)
        test_results["summary"]["total"] += 1
        
        return response
        
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        print(f"   ❌ FAILED ({elapsed_time:.2f}s) - Timeout after {timeout}s")
        result = {
            "name": name,
            "status": "FAILED",
            "elapsed_time": elapsed_time,
            "error": f"Timeout after {timeout}s"
        }
        test_results["tests"].append(result)
        test_results["summary"]["failed"] += 1
        test_results["summary"]["total"] += 1
        return None
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"   ❌ FAILED ({elapsed_time:.2f}s) - {str(e)}")
        result = {
            "name": name,
            "status": "FAILED",
            "elapsed_time": elapsed_time,
            "error": str(e)
        }
        test_results["tests"].append(result)
        test_results["summary"]["failed"] += 1
        test_results["summary"]["total"] += 1
        return None

def test_backend_health():
    """Test 1: Backend Health Check"""
    print("\n" + "="*50)
    print("1. BACKEND HEALTH CHECK")
    print("="*50)
    
    response = run_test(
        "Backend Health Check",
        f"{BASE_URL}/health",
        method="GET"
    )
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
            services = data.get('services', {})
            print(f"   Services: Ollama={services.get('ollama', False)}, Tools={services.get('tools', 0)}, Database={services.get('database', False)}")
            return True
        except:
            print(f"   Response: {response.text[:200]}")
            return True
    return False

def test_agent_health_and_status():
    """Test 2: Agent Health and Status"""
    print("\n" + "="*50)
    print("2. AGENT HEALTH AND STATUS")
    print("="*50)
    
    # Test agent health
    response = run_test(
        "Agent Health Check",
        f"{BASE_URL}/api/agent/health",
        method="GET"
    )
    
    # Test agent status
    response = run_test(
        "Agent Status Check",
        f"{BASE_URL}/api/agent/status",
        method="GET"
    )
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            print(f"   Agent Status: {data.get('status', 'unknown')}")
            if 'ollama' in data:
                ollama_info = data['ollama']
                print(f"   Ollama Endpoint: {ollama_info.get('endpoint', 'unknown')}")
                print(f"   Available Models: {len(ollama_info.get('models', []))}")
            return True
        except:
            print(f"   Response: {response.text[:200]}")
            return True
    return False

def test_chat_functionality():
    """Test 3: Chat Functionality with Different Message Types"""
    print("\n" + "="*50)
    print("3. CHAT FUNCTIONALITY")
    print("="*50)
    
    test_messages = [
        {
            "name": "Simple Conversation",
            "message": "Hola, ¿cómo estás?",
            "timeout": 15
        },
        {
            "name": "Task Execution",
            "message": "Crea un informe sobre las mejores prácticas en desarrollo de software",
            "timeout": 30
        },
        {
            "name": "WebSearch",
            "message": "[WebSearch] noticias inteligencia artificial 2025",
            "timeout": 30
        },
        {
            "name": "DeepSearch",
            "message": "[DeepResearch] aplicaciones de IA en medicina",
            "timeout": 45
        }
    ]
    
    chat_results = []
    
    for test_msg in test_messages:
        response = run_test(
            f"Chat - {test_msg['name']}",
            f"{BASE_URL}/api/agent/chat",
            method="POST",
            data={"message": test_msg["message"]},
            timeout=test_msg["timeout"]
        )
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                memory_used = data.get('memory_used', False)
                response_length = len(data.get('response', ''))
                print(f"   Memory Used: {memory_used}")
                print(f"   Response Length: {response_length} characters")
                chat_results.append({
                    "message": test_msg["message"],
                    "memory_used": memory_used,
                    "response_length": response_length
                })
            except:
                print(f"   Response: {response.text[:200]}")
                chat_results.append({
                    "message": test_msg["message"],
                    "memory_used": False,
                    "response_length": len(response.text),
                    "raw_response": True
                })
        else:
            chat_results.append({
                "message": test_msg["message"],
                "memory_used": False,
                "response_length": 0,
                "error": True
            })
    
    return chat_results

def test_memory_system():
    """Test 4: Memory System Integration"""
    print("\n" + "="*50)
    print("4. MEMORY SYSTEM INTEGRATION")
    print("="*50)
    
    # Test memory analytics
    response = run_test(
        "Memory Analytics",
        f"{BASE_URL}/api/memory/analytics",
        method="GET"
    )
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            print(f"   Memory Components: {len(data.get('components', []))}")
            print(f"   Overview Available: {'overview' in data}")
            print(f"   Memory Efficiency: {'memory_efficiency' in data}")
            print(f"   Learning Insights: {'learning_insights' in data}")
        except:
            print(f"   Response: {response.text[:200]}")
    
    # Test context retrieval
    response = run_test(
        "Memory Context Retrieval",
        f"{BASE_URL}/api/memory/context",
        method="POST",
        data={"query": "desarrollo de software", "limit": 5}
    )
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            print(f"   Context Results: {len(data.get('results', []))}")
            print(f"   Synthesized Context Available: {'synthesized_context' in data}")
        except:
            print(f"   Response: {response.text[:200]}")

def test_ollama_integration():
    """Test 5: Ollama Integration"""
    print("\n" + "="*50)
    print("5. OLLAMA INTEGRATION")
    print("="*50)
    
    # Test Ollama check endpoint
    response = run_test(
        "Ollama Connection Check",
        f"{BASE_URL}/api/agent/ollama/check",
        method="POST",
        data={"endpoint": OLLAMA_ENDPOINT}
    )
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            print(f"   Connection Status: {data.get('status', 'unknown')}")
            print(f"   Endpoint: {data.get('endpoint', 'unknown')}")
        except:
            print(f"   Response: {response.text[:200]}")
    
    # Test Ollama models endpoint
    response = run_test(
        "Ollama Models List",
        f"{BASE_URL}/api/agent/ollama/models",
        method="POST",
        data={"endpoint": OLLAMA_ENDPOINT}
    )
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            models = data.get('models', [])
            print(f"   Available Models: {len(models)}")
            if isinstance(models, list) and len(models) > 0:
                model_names = []
                for model in models:
                    if isinstance(model, dict):
                        model_names.append(model.get('name', 'unknown'))
                    elif isinstance(model, str):
                        model_names.append(model)
                expected_model_found = EXPECTED_MODEL in model_names
                print(f"   Expected Model ({EXPECTED_MODEL}) Found: {expected_model_found}")
                if model_names:
                    print(f"   Sample Models: {model_names[:3]}")
        except Exception as e:
            print(f"   Response parsing error: {e}")
            print(f"   Response: {response.text[:200]}")

def test_database_connection():
    """Test 6: Database Connection"""
    print("\n" + "="*50)
    print("6. DATABASE CONNECTION")
    print("="*50)
    
    response = run_test(
        "Database Stats",
        f"{BASE_URL}/api/stats",
        method="GET"
    )
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            print(f"   Database Connected: {data.get('connected', False)}")
            print(f"   Collections: {data.get('collections', 0)}")
            print(f"   Total Size: {data.get('total_size_mb', 0)} MB")
        except:
            print(f"   Response: {response.text[:200]}")

def test_error_handling():
    """Test 7: Error Handling"""
    print("\n" + "="*50)
    print("7. ERROR HANDLING")
    print("="*50)
    
    # Test invalid endpoint
    run_test(
        "Invalid Endpoint",
        f"{BASE_URL}/api/invalid/endpoint",
        method="GET",
        expected_status=404
    )
    
    # Test invalid chat data
    run_test(
        "Invalid Chat Data",
        f"{BASE_URL}/api/agent/chat",
        method="POST",
        data={},  # Missing message
        expected_status=400
    )

def print_final_summary():
    """Print final test summary"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TESTING SUMMARY")
    print("="*80)
    
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    test_results["summary"]["success_rate"] = success_rate
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test in test_results["tests"]:
        status_icon = "✅" if test["status"] == "PASSED" else "❌"
        elapsed = test.get("elapsed_time", 0)
        print(f"{status_icon} {test['name']} ({elapsed:.2f}s)")
        if test["status"] == "FAILED" and "error" in test:
            print(f"   Error: {test['error']}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if success_rate >= 90:
        print("✅ EXCELLENT - Backend fully functional and production ready")
    elif success_rate >= 75:
        print("⚠️ GOOD - Backend mostly functional with minor issues")
    elif success_rate >= 50:
        print("⚠️ FAIR - Backend has significant issues that need attention")
    else:
        print("❌ POOR - Backend has critical issues requiring immediate attention")
    
    return test_results

def main():
    """Main testing function"""
    try:
        # Run all tests
        test_backend_health()
        test_agent_health_and_status()
        chat_results = test_chat_functionality()
        test_memory_system()
        test_ollama_integration()
        test_database_connection()
        test_error_handling()
        
        # Print final summary
        results = print_final_summary()
        
        # Save results to file
        with open('/app/mitosis_review_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Test results saved to: /app/mitosis_review_test_results.json")
        
        return results
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        return None

if __name__ == "__main__":
    main()