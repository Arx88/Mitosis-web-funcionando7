#!/usr/bin/env python3
"""
Comprehensive Memory Integration Test Script for Mitosis Backend System

This script tests the complete Mitosis backend system comprehensively after memory integration fixes, focusing on:

1. Backend Health and Status: Test all health endpoints to ensure services are running correctly
2. Memory System Complete Integration: Test all memory endpoints including the newly fixed methods
3. Chat Functionality with Memory: Test the chat endpoint with memory integration working automatically
4. Memory Persistence: Test multiple conversations to verify memory persistence works
5. Ollama Integration: Test that Ollama integration is working with the memory system
6. API Endpoints: Test all agent endpoints to ensure they work properly
7. Fixed Methods: Test specifically the compress_old_memory and export_memory_data methods
8. Error Handling: Test error handling for various scenarios

The goal is to confirm that the complete system is working at production level after fixing 
the memory integration issues and completing the missing methods.
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime

# Configuration - Use the frontend URL from .env
BASE_URL = "https://c9d7ec55-c6f2-484b-a23c-ac8914c6abc9.preview.emergentagent.com"
API_PREFIX = "/api/agent"
MEMORY_PREFIX = "/api/memory"

print(f"🧪 COMPREHENSIVE MEMORY INTEGRATION TESTING - PRODUCTION LEVEL VERIFICATION")
print(f"Using backend URL: {BASE_URL}")
print(f"Test started at: {datetime.now().isoformat()}")

# Test results tracking
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
}

def run_test(name, endpoint, method="GET", data=None, expected_status=200, timeout=30):
    """Run a test against an API endpoint"""
    start_time = time.time()
    
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, timeout=timeout)
        
        duration = time.time() - start_time
        
        # Check status code
        status_ok = response.status_code == expected_status
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except:
            response_data = {"raw_response": response.text}
        
        result = {
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "duration": round(duration, 2),
            "passed": status_ok,
            "response": response_data,
            "data_sent": data
        }
        
        test_results["tests"].append(result)
        test_results["summary"]["total"] += 1
        
        if status_ok:
            test_results["summary"]["passed"] += 1
            print(f"✅ {name}: PASSED ({duration:.2f}s)")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ {name}: FAILED ({duration:.2f}s) - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        result = {
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "status_code": None,
            "expected_status": expected_status,
            "duration": round(duration, 2),
            "passed": False,
            "error": str(e),
            "data_sent": data
        }
        
        test_results["tests"].append(result)
        test_results["summary"]["total"] += 1
        test_results["summary"]["failed"] += 1
        
        print(f"❌ {name}: ERROR ({duration:.2f}s) - {str(e)}")
        return result

def test_memory_integration_specific(test_name, message, expected_memory_used=True):
    """Test chat endpoint specifically for memory integration"""
    data = {
        "message": message,
        "task_id": str(uuid.uuid4())
    }
    
    result = run_test(test_name, f"{API_PREFIX}/chat", "POST", data, timeout=45)
    
    if result["passed"] and "response" in result:
        response = result["response"]
        memory_used = response.get("memory_used", False)
        
        if expected_memory_used and memory_used:
            print(f"   ✅ Memory integration working: memory_used = {memory_used}")
        elif not expected_memory_used and not memory_used:
            print(f"   ✅ Memory not used as expected: memory_used = {memory_used}")
        elif expected_memory_used and not memory_used:
            print(f"   ⚠️  Memory not used when expected: memory_used = {memory_used}")
        else:
            print(f"   ⚠️  Unexpected memory usage: memory_used = {memory_used}")
        
        # Check for task_id in response
        if "task_id" in response:
            print(f"   ✅ Task ID generated: {response['task_id']}")
        
        # Check response length
        if "response" in response and len(response["response"]) > 100:
            print(f"   ✅ Comprehensive response generated ({len(response['response'])} chars)")
    
    return result

print("\n" + "="*80)
print("1. BACKEND HEALTH AND STATUS TESTING")
print("="*80)

# Test basic health endpoint
run_test("Backend Health Check", "/health")

# Test agent health endpoint
run_test("Agent Health Check", f"{API_PREFIX}/health")

# Test agent status endpoint
run_test("Agent Status Check", f"{API_PREFIX}/status")

print("\n" + "="*80)
print("2. OLLAMA INTEGRATION TESTING")
print("="*80)

# Test Ollama connection check
ollama_check_data = {
    "endpoint": "https://78d08925604a.ngrok-free.app",
    "model": "llama3.1:8b"
}
run_test("Ollama Connection Check", f"{API_PREFIX}/ollama/check", "POST", ollama_check_data)

# Test Ollama models list
run_test("Ollama Models List", f"{API_PREFIX}/ollama/models", "POST", ollama_check_data)

print("\n" + "="*80)
print("3. MEMORY SYSTEM COMPLETE INTEGRATION TESTING")
print("="*80)

# Test memory analytics
run_test("Memory Analytics", f"{MEMORY_PREFIX}/memory-analytics")

# Test episode storage
episode_data = {
    "user_query": "What are the applications of AI in healthcare?",
    "agent_response": "AI in healthcare has many applications including diagnostic imaging, drug discovery, and personalized treatment plans.",
    "success": True,
    "context": {"topic": "healthcare", "type": "question"},
    "tools_used": ["web_search"],
    "importance": 0.8,
    "metadata": {"source": "user_conversation"}
}
run_test("Episode Storage", f"{MEMORY_PREFIX}/store-episode", "POST", episode_data)

# Test knowledge storage
knowledge_data = {
    "content": "AI in healthcare can improve diagnosis accuracy by up to 95%",
    "type": "fact",
    "subject": "AI in healthcare",
    "predicate": "improves",
    "object": "diagnosis accuracy by up to 95%",
    "confidence": 0.9,
    "context": {"domain": "healthcare"},
    "metadata": {"source": "medical_research"}
}
run_test("Knowledge Storage", f"{MEMORY_PREFIX}/store-knowledge", "POST", knowledge_data)

# Test procedure storage
procedure_data = {
    "name": "Healthcare AI Analysis",
    "description": "Process for analyzing healthcare data using AI",
    "steps": ["Analyze patient data", "Apply AI models", "Generate recommendations"],
    "category": "healthcare",
    "context_conditions": {"domain": "healthcare"},
    "effectiveness": 0.85,
    "metadata": {"complexity": "medium", "duration": "30min"}
}
run_test("Procedure Storage", f"{MEMORY_PREFIX}/store-procedure", "POST", procedure_data)

# Test semantic search
search_data = {
    "query": "artificial intelligence healthcare applications",
    "max_results": 5,
    "memory_types": ["all"]
}
run_test("Semantic Search", f"{MEMORY_PREFIX}/semantic-search", "POST", search_data)

# Test context retrieval
context_data = {
    "query": "healthcare AI discussion",
    "context_type": "all",
    "max_results": 10
}
run_test("Memory Context Retrieval", f"{MEMORY_PREFIX}/retrieve-context", "POST", context_data)

print("\n" + "="*80)
print("4. FIXED METHODS TESTING (compress_old_memory and export_memory_data)")
print("="*80)

# Test compress_old_memory method
compress_data = {
    "config": {
        "days_threshold": 30,
        "compression_ratio": 0.5
    }
}
run_test("Memory Compression", f"{MEMORY_PREFIX}/compress-memory", "POST", compress_data)

# Test export_memory_data method
run_test("Memory Export", f"{MEMORY_PREFIX}/export-memory")

print("\n" + "="*80)
print("5. CHAT FUNCTIONALITY WITH MEMORY INTEGRATION")
print("="*80)

# Test chat with memory integration - various scenarios
test_memory_integration_specific(
    "Chat Integration with Memory - Healthcare Query",
    "What are the latest applications of AI in healthcare?",
    expected_memory_used=True
)

test_memory_integration_specific(
    "Chat Integration with Memory - Follow-up Question",
    "Can you elaborate on the diagnostic accuracy improvements?",
    expected_memory_used=True
)

test_memory_integration_specific(
    "Chat Integration with Memory - Technical Question",
    "How do machine learning algorithms improve medical imaging?",
    expected_memory_used=True
)

print("\n" + "="*80)
print("6. MEMORY PERSISTENCE TESTING")
print("="*80)

# Test multiple conversations to verify memory persistence
conversations = [
    "I'm interested in learning about renewable energy technologies",
    "What are the most promising solar energy innovations?",
    "How do wind turbines compare to solar panels in efficiency?",
    "What role does energy storage play in renewable systems?"
]

print("Testing memory persistence across multiple conversations...")
for i, message in enumerate(conversations, 1):
    test_memory_integration_specific(
        f"Memory Persistence Test {i}/4",
        message,
        expected_memory_used=True
    )
    time.sleep(2)  # Brief pause between conversations

print("\n" + "="*80)
print("7. WEBSEARCH INTEGRATION WITH MEMORY")
print("="*80)

# Test WebSearch with memory integration
websearch_data = {
    "message": "[WebSearch] Latest developments in quantum computing 2025",
    "task_id": str(uuid.uuid4())
}
run_test("WebSearch Integration", f"{API_PREFIX}/chat", "POST", websearch_data, timeout=60)

print("\n" + "="*80)
print("8. ERROR HANDLING TESTING")
print("="*80)

# Test invalid endpoint
run_test("Invalid Endpoint", "/api/invalid/endpoint", "GET", expected_status=404)

# Test invalid chat data
invalid_chat_data = {"invalid_field": "test"}
run_test("Invalid Chat Data", f"{API_PREFIX}/chat", "POST", invalid_chat_data, expected_status=400)

# Test invalid memory data
invalid_memory_data = {"invalid": "data"}
run_test("Invalid Memory Data", f"{MEMORY_PREFIX}/store-episode", "POST", invalid_memory_data, expected_status=400)

print("\n" + "="*80)
print("COMPREHENSIVE TESTING RESULTS SUMMARY")
print("="*80)

# Calculate success rate
total_tests = test_results["summary"]["total"]
passed_tests = test_results["summary"]["passed"]
failed_tests = test_results["summary"]["failed"]
success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

print(f"📊 TESTING STATISTICS:")
print(f"   Total Tests: {total_tests}")
print(f"   Passed: {passed_tests}")
print(f"   Failed: {failed_tests}")
print(f"   Success Rate: {success_rate:.1f}%")

print(f"\n🎯 MEMORY INTEGRATION ANALYSIS:")
memory_tests = [t for t in test_results["tests"] if "memory" in t["name"].lower() or "chat" in t["name"].lower()]
memory_passed = len([t for t in memory_tests if t["passed"]])
memory_total = len(memory_tests)
memory_success_rate = (memory_passed / memory_total * 100) if memory_total > 0 else 0

print(f"   Memory-related Tests: {memory_total}")
print(f"   Memory Tests Passed: {memory_passed}")
print(f"   Memory Success Rate: {memory_success_rate:.1f}%")

# Check for memory_used in chat responses
chat_tests = [t for t in test_results["tests"] if "chat" in t["endpoint"].lower()]
memory_used_count = 0
for test in chat_tests:
    if test["passed"] and "response" in test and isinstance(test["response"], dict):
        if test["response"].get("memory_used", False):
            memory_used_count += 1

if chat_tests:
    memory_usage_rate = (memory_used_count / len(chat_tests) * 100)
    print(f"   Chat Tests with Memory Used: {memory_used_count}/{len(chat_tests)} ({memory_usage_rate:.1f}%)")

print(f"\n⏱️  PERFORMANCE ANALYSIS:")
response_times = [t["duration"] for t in test_results["tests"] if t["passed"]]
if response_times:
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    min_response_time = min(response_times)
    print(f"   Average Response Time: {avg_response_time:.2f}s")
    print(f"   Max Response Time: {max_response_time:.2f}s")
    print(f"   Min Response Time: {min_response_time:.2f}s")

print(f"\n🔍 CRITICAL ISSUES:")
critical_failures = []
for test in test_results["tests"]:
    if not test["passed"]:
        if "health" in test["name"].lower():
            critical_failures.append(f"❌ CRITICAL: {test['name']} - Backend health issue")
        elif "memory" in test["name"].lower() and "chat" in test["name"].lower():
            critical_failures.append(f"❌ CRITICAL: {test['name']} - Memory integration failure")
        elif test["expected_status"] == 200:
            critical_failures.append(f"⚠️  {test['name']} - Functionality issue")

if critical_failures:
    for failure in critical_failures:
        print(f"   {failure}")
else:
    print("   ✅ No critical issues detected")

print(f"\n🎉 FINAL VERDICT:")
if success_rate >= 90:
    print("   ✅ EXCELLENT - System is production ready")
elif success_rate >= 80:
    print("   ✅ GOOD - System is functional with minor issues")
elif success_rate >= 70:
    print("   ⚠️  ACCEPTABLE - System works but needs improvements")
else:
    print("   ❌ POOR - System has significant issues requiring fixes")

# Memory integration specific verdict
if memory_success_rate >= 90 and memory_usage_rate >= 80:
    print("   ✅ MEMORY INTEGRATION: Excellent - Working as expected")
elif memory_success_rate >= 80:
    print("   ⚠️  MEMORY INTEGRATION: Good - Minor issues detected")
else:
    print("   ❌ MEMORY INTEGRATION: Poor - Significant issues detected")

print(f"\n📝 DETAILED RESULTS:")
print("   Results saved to test_results variable for further analysis")

# Save results to file
try:
    with open('/app/memory_integration_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    print("   ✅ Detailed results saved to memory_integration_test_results.json")
except Exception as e:
    print(f"   ⚠️  Could not save results to file: {e}")

print(f"\n🏁 Testing completed at: {datetime.now().isoformat()}")