#!/usr/bin/env python3
"""
Mitosis Backend Connectivity Test Script - Review Request Focused Testing

This script tests the Mitosis backend application to verify that backend connectivity 
issues have been resolved after adding the mpmath dependency and restarting the service.

Focus Areas (as per review request):
1. Backend Health Check - Test the /health endpoint to ensure all services are healthy
2. Chat Functionality - Test the /api/agent/chat endpoint with a simple message
3. Memory Integration - Verify memory system integration is working (memory_used: true)
4. Ollama Integration - Test Ollama connection to https://78d08925604a.ngrok-free.app
5. API Response Times - Check that responses are reasonable (under 10 seconds)
6. Error Handling - Verify proper error responses
7. WebSearch Integration - Test WebSearch functionality with a simple query
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration - Use localhost for internal testing
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"
MEMORY_PREFIX = "/api/memory"

print(f"🧪 MITOSIS BACKEND CONNECTIVITY TEST - REVIEW REQUEST FOCUSED")
print(f"📅 Test Date: {datetime.now().isoformat()}")
print(f"🔗 Backend URL: {BASE_URL}")
print("="*80)

# Test results tracking
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "success_rate": 0
    }
}

def run_test(name, test_func):
    """Run a test and track results"""
    test_results["summary"]["total"] += 1
    
    print(f"\n🧪 TEST: {name}")
    print("-" * 60)
    
    start_time = time.time()
    try:
        passed, details = test_func()
        end_time = time.time()
        response_time = end_time - start_time
        
        test_results["tests"].append({
            "name": name,
            "passed": passed,
            "response_time": round(response_time, 2),
            "details": details
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"✅ PASSED ({response_time:.2f}s)")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ FAILED ({response_time:.2f}s)")
            if details:
                print(f"   Details: {details}")
        
        return passed, response_time
    
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "passed": False,
            "response_time": round(response_time, 2),
            "error": str(e)
        })
        
        print(f"❌ FAILED ({response_time:.2f}s) - Exception: {str(e)}")
        return False, response_time

def test_backend_health():
    """Test 1: Backend Health Check"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            
            services = data.get('services', {})
            print(f"   Services:")
            print(f"     - Ollama: {services.get('ollama')}")
            print(f"     - Database: {services.get('database')}")
            print(f"     - Tools: {services.get('tools')}")
            
            # Check if all services are healthy
            all_healthy = (
                data.get('status') == 'healthy' and
                services.get('ollama') == True and
                services.get('database') == True and
                services.get('tools', 0) > 0
            )
            
            return all_healthy, f"Status: {data.get('status')}, Services: {services}"
        else:
            return False, f"HTTP {response.status_code}"
    
    except Exception as e:
        return False, str(e)

def test_agent_health():
    """Test 2: Agent Health Check"""
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Agent Status: {data.get('status')}")
            
            # Check Ollama configuration
            ollama_config = data.get('ollama_config', {})
            print(f"   Ollama Config:")
            print(f"     - Endpoint: {ollama_config.get('endpoint')}")
            print(f"     - Model: {ollama_config.get('model')}")
            print(f"     - Connected: {ollama_config.get('connected')}")
            
            # Check if agent is healthy
            agent_healthy = (
                data.get('status') == 'healthy' and
                ollama_config.get('connected') == True
            )
            
            return agent_healthy, f"Agent: {data.get('status')}, Ollama: {ollama_config.get('connected')}"
        else:
            return False, f"HTTP {response.status_code}"
    
    except Exception as e:
        return False, str(e)

def test_ollama_integration():
    """Test 3: Ollama Integration"""
    try:
        # Test Ollama check endpoint
        response = requests.post(f"{BASE_URL}{API_PREFIX}/ollama/check", 
                               json={"endpoint": "https://78d08925604a.ngrok-free.app"}, 
                               timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Connection Status: {data.get('status')}")
            print(f"   Endpoint: {data.get('endpoint')}")
            print(f"   Connected: {data.get('connected')}")
            
            # Test models endpoint
            models_response = requests.post(f"{BASE_URL}{API_PREFIX}/ollama/models", 
                                          json={"endpoint": "https://78d08925604a.ngrok-free.app"}, 
                                          timeout=15)
            
            if models_response.status_code == 200:
                models_data = models_response.json()
                models = models_data.get('models', [])
                print(f"   Available Models: {len(models)}")
                
                # Check if llama3.1:8b is available
                llama_available = any(model.get('name') == 'llama3.1:8b' for model in models)
                print(f"   llama3.1:8b Available: {llama_available}")
                
                return data.get('connected') and llama_available, f"Connected: {data.get('connected')}, Models: {len(models)}"
            else:
                return False, f"Models endpoint failed: HTTP {models_response.status_code}"
        else:
            return False, f"HTTP {response.status_code}"
    
    except Exception as e:
        return False, str(e)

def test_memory_system():
    """Test 4: Memory System Integration"""
    try:
        # Test memory analytics
        response = requests.get(f"{BASE_URL}{MEMORY_PREFIX}/analytics", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Memory System Status: Initialized")
            
            # Check memory components
            components = data.get('components', {})
            print(f"   Components:")
            for component, status in components.items():
                print(f"     - {component}: {status}")
            
            # Test episode storage
            episode_data = {
                "content": "Test episode for connectivity verification",
                "context": {"test": True},
                "importance": 0.5
            }
            
            episode_response = requests.post(f"{BASE_URL}{MEMORY_PREFIX}/store-episode", 
                                           json=episode_data, timeout=10)
            
            episode_success = episode_response.status_code == 200
            print(f"   Episode Storage: {'✅' if episode_success else '❌'}")
            
            # Test context retrieval
            context_response = requests.post(f"{BASE_URL}{MEMORY_PREFIX}/get-context", 
                                           json={"query": "test"}, timeout=10)
            
            context_success = context_response.status_code == 200
            print(f"   Context Retrieval: {'✅' if context_success else '❌'}")
            
            return episode_success and context_success, f"Components: {len(components)}, Storage: {episode_success}, Retrieval: {context_success}"
        else:
            return False, f"HTTP {response.status_code}"
    
    except Exception as e:
        return False, str(e)

def test_chat_functionality():
    """Test 5: Chat Functionality with Memory Integration"""
    try:
        chat_data = {
            "message": "Hello, please explain AI briefly"
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", 
                               json=chat_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Length: {len(data.get('response', ''))}")
            print(f"   Memory Used: {data.get('memory_used', False)}")
            print(f"   Task ID: {data.get('task_id', 'None')}")
            
            # Check if memory is being used
            memory_used = data.get('memory_used', False)
            has_response = len(data.get('response', '')) > 0
            
            return memory_used and has_response, f"Memory: {memory_used}, Response: {has_response}"
        else:
            return False, f"HTTP {response.status_code}"
    
    except Exception as e:
        return False, str(e)

def test_websearch_integration():
    """Test 6: WebSearch Integration"""
    try:
        websearch_data = {
            "message": "[WebSearch] AI news 2025"
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", 
                               json=websearch_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Search Mode: {data.get('search_mode', 'None')}")
            print(f"   Response Length: {len(data.get('response', ''))}")
            
            # Check search data
            search_data = data.get('search_data', {})
            if search_data:
                print(f"   Sources Found: {len(search_data.get('sources', []))}")
                print(f"   Query: {search_data.get('query', 'None')}")
            
            # Check if WebSearch worked
            is_websearch = data.get('search_mode') == 'websearch'
            has_sources = len(search_data.get('sources', [])) > 0
            
            return is_websearch and has_sources, f"Mode: {data.get('search_mode')}, Sources: {len(search_data.get('sources', []))}"
        else:
            return False, f"HTTP {response.status_code}"
    
    except Exception as e:
        return False, str(e)

def test_error_handling():
    """Test 7: Error Handling"""
    try:
        # Test invalid endpoint
        response1 = requests.get(f"{BASE_URL}/invalid-endpoint", timeout=5)
        invalid_endpoint_ok = response1.status_code == 404
        
        # Test invalid chat data
        response2 = requests.post(f"{BASE_URL}{API_PREFIX}/chat", 
                                json={}, timeout=5)
        invalid_data_ok = response2.status_code == 400
        
        print(f"   Invalid Endpoint (404): {'✅' if invalid_endpoint_ok else '❌'}")
        print(f"   Invalid Data (400): {'✅' if invalid_data_ok else '❌'}")
        
        return invalid_endpoint_ok and invalid_data_ok, f"404: {invalid_endpoint_ok}, 400: {invalid_data_ok}"
    
    except Exception as e:
        return False, str(e)

def test_memory_persistence():
    """Test 8: Memory Persistence Across Conversations"""
    try:
        # First conversation
        conv1_data = {
            "message": "My name is John and I work as a software engineer"
        }
        
        response1 = requests.post(f"{BASE_URL}{API_PREFIX}/chat", 
                                json=conv1_data, timeout=30)
        
        if response1.status_code != 200:
            return False, f"First conversation failed: HTTP {response1.status_code}"
        
        data1 = response1.json()
        memory_used_1 = data1.get('memory_used', False)
        
        # Wait a moment for memory to be stored
        time.sleep(1)
        
        # Second conversation referencing the first
        conv2_data = {
            "message": "What do you remember about my profession?"
        }
        
        response2 = requests.post(f"{BASE_URL}{API_PREFIX}/chat", 
                                json=conv2_data, timeout=30)
        
        if response2.status_code != 200:
            return False, f"Second conversation failed: HTTP {response2.status_code}"
        
        data2 = response2.json()
        memory_used_2 = data2.get('memory_used', False)
        
        print(f"   Conversation 1 Memory: {memory_used_1}")
        print(f"   Conversation 2 Memory: {memory_used_2}")
        
        # Check if both conversations used memory
        both_used_memory = memory_used_1 and memory_used_2
        
        return both_used_memory, f"Conv1: {memory_used_1}, Conv2: {memory_used_2}"
    
    except Exception as e:
        return False, str(e)

def print_final_summary():
    """Print final test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    test_results["summary"]["success_rate"] = round(success_rate, 1)
    
    print("\n" + "="*80)
    print("🎯 FINAL TEST SUMMARY - MITOSIS BACKEND CONNECTIVITY")
    print("="*80)
    print(f"📊 Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    # Calculate average response time
    response_times = [test.get('response_time', 0) for test in test_results["tests"]]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    print(f"⏱️  Average Response Time: {avg_response_time:.2f}s")
    
    print("\n📋 DETAILED RESULTS:")
    for test in test_results["tests"]:
        status = "✅ PASSED" if test["passed"] else "❌ FAILED"
        print(f"   {test['name']}: {status} ({test['response_time']}s)")
        if not test["passed"] and "error" in test:
            print(f"      Error: {test['error']}")
        elif "details" in test:
            print(f"      Details: {test['details']}")
    
    print("\n🎯 REVIEW REQUEST ASSESSMENT:")
    
    # Check specific requirements from review request
    health_passed = any(test["name"] == "Backend Health Check" and test["passed"] for test in test_results["tests"])
    chat_passed = any(test["name"] == "Chat Functionality with Memory Integration" and test["passed"] for test in test_results["tests"])
    memory_passed = any(test["name"] == "Memory System Integration" and test["passed"] for test in test_results["tests"])
    ollama_passed = any(test["name"] == "Ollama Integration" and test["passed"] for test in test_results["tests"])
    websearch_passed = any(test["name"] == "WebSearch Integration" and test["passed"] for test in test_results["tests"])
    error_handling_passed = any(test["name"] == "Error Handling" and test["passed"] for test in test_results["tests"])
    
    print(f"   1. Backend Health Check: {'✅' if health_passed else '❌'}")
    print(f"   2. Chat Functionality: {'✅' if chat_passed else '❌'}")
    print(f"   3. Memory Integration: {'✅' if memory_passed else '❌'}")
    print(f"   4. Ollama Integration: {'✅' if ollama_passed else '❌'}")
    print(f"   5. API Response Times: {'✅' if avg_response_time < 10 else '❌'} (avg: {avg_response_time:.2f}s)")
    print(f"   6. Error Handling: {'✅' if error_handling_passed else '❌'}")
    print(f"   7. WebSearch Integration: {'✅' if websearch_passed else '❌'}")
    
    # Overall assessment
    critical_tests_passed = health_passed and chat_passed and memory_passed and ollama_passed
    
    print(f"\n🏆 OVERALL ASSESSMENT:")
    if success_rate >= 85 and critical_tests_passed:
        print("   ✅ EXCELLENT - Backend connectivity issues have been resolved")
        print("   ✅ All critical systems are operational")
        print("   ✅ Memory integration is working correctly")
        print("   ✅ Response times are acceptable")
    elif success_rate >= 70:
        print("   ⚠️  GOOD - Most systems working but some issues remain")
        print("   ⚠️  Minor connectivity issues may still exist")
    else:
        print("   ❌ POOR - Significant connectivity issues remain")
        print("   ❌ Backend requires further investigation")
    
    return success_rate >= 85 and critical_tests_passed

def main():
    """Main test execution"""
    print("🚀 Starting Mitosis Backend Connectivity Tests...")
    
    # Run all tests
    tests = [
        ("Backend Health Check", test_backend_health),
        ("Agent Health Check", test_agent_health),
        ("Ollama Integration", test_ollama_integration),
        ("Memory System Integration", test_memory_system),
        ("Chat Functionality with Memory Integration", test_chat_functionality),
        ("WebSearch Integration", test_websearch_integration),
        ("Error Handling", test_error_handling),
        ("Memory Persistence Across Conversations", test_memory_persistence)
    ]
    
    for test_name, test_func in tests:
        run_test(test_name, test_func)
    
    # Print final summary
    overall_success = print_final_summary()
    
    # Save results to file
    with open('/app/mitosis_connectivity_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Test results saved to: /app/mitosis_connectivity_test_results.json")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)