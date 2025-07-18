#!/usr/bin/env python3
"""
Comprehensive Backend Test Script for Mitosis Application - Memory System Integration Focus

This script tests the Mitosis backend application comprehensively focusing on:
1. Backend Health and Status - Test the /health endpoint and verify all services are running correctly
2. Memory System Integration - Test the memory system integration in the chat endpoint
3. Chat Functionality - Test the /api/agent/chat endpoint with various messages
4. Memory Persistence - Test multiple consecutive conversations to verify memory persistence
5. WebSearch Integration - Test chat with WebSearch functionality
6. Agent Status - Test agent status and Ollama configuration endpoints
7. Error Handling - Test error handling for edge cases

Key expectations:
- Chat endpoint should return memory_used: true in all responses
- Multiple conversations should show improved context awareness
- Backend should be stable without crashes
- All memory components should be initialized and working
- Response times should be reasonable (< 30 seconds for most operations)
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime

# Configuration
BASE_URL = "https://e3950462-a256-4767-a06d-3f34f86d4494.preview.emergentagent.com"
API_PREFIX = "/api/agent"
MEMORY_PREFIX = "/api/memory"

print(f"🧪 COMPREHENSIVE BACKEND TESTING - MEMORY SYSTEM INTEGRATION FOCUS")
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
    url = f"{BASE_URL}{endpoint}"
    test_results["summary"]["total"] += 1
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {name}")
    print(f"🔗 URL: {url}")
    print(f"📋 METHOD: {method}")
    if data:
        print(f"📤 DATA: {json.dumps(data, indent=2)}")
    
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        status_code = response.status_code
        print(f"⏱️  RESPONSE TIME: {response_time:.2f}s")
        print(f"📊 STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"📥 RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"📥 RESPONSE: {response_data}")
        
        # Check status code
        status_ok = status_code == expected_status
        
        # Determine test result
        passed = status_ok
        
        # Update test results
        test_results["tests"].append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "expected_status": expected_status,
            "response_time": response_time,
            "passed": passed,
            "response_data": response_data if passed else None
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"✅ RESULT: PASSED")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ RESULT: FAILED")
            print(f"   Expected status {expected_status}, got {status_code}")
        
        return passed, response_data
    
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "error": str(e),
            "response_time": response_time,
            "passed": False
        })
        print(f"❌ ERROR: {str(e)}")
        print(f"❌ RESULT: FAILED (Exception)")
        return False, None

def test_memory_integration_comprehensive():
    """Test comprehensive memory system integration as requested in review"""
    print(f"\n{'='*100}")
    print(f"🧠 COMPREHENSIVE MEMORY SYSTEM INTEGRATION TEST")
    print(f"{'='*100}")
    
    memory_tests_passed = 0
    memory_tests_total = 0
    
    # Test 1: Memory Analytics (using correct endpoint)
    print(f"\n🔍 TEST 1: Memory Analytics")
    memory_tests_total += 1
    
    passed, response_data = run_test(
        "Memory Analytics",
        f"{MEMORY_PREFIX}/memory-analytics",
        "GET",
        timeout=20
    )
    
    if passed and response_data:
        # Check if analytics has expected structure
        if isinstance(response_data, dict):
            expected_sections = ['overview', 'memory_efficiency', 'learning_insights']
            has_all_sections = all(section in response_data for section in expected_sections)
            if has_all_sections:
                print("✅ Memory analytics has all expected sections")
                memory_tests_passed += 1
            else:
                print("❌ Memory analytics missing expected sections")
                print(f"   Available sections: {list(response_data.keys())}")
        else:
            print("⚠️  Memory analytics format unexpected")
    
    # Test 2: Episode Storage (using correct format)
    print(f"\n🔍 TEST 2: Episode Storage")
    memory_tests_total += 1
    
    episode_data = {
        "user_query": "What is artificial intelligence?",
        "agent_response": "Artificial intelligence is a field of computer science focused on creating systems that can perform tasks that typically require human intelligence.",
        "success": True,
        "context": {
            "task_id": f"test-{uuid.uuid4()}",
            "user_id": "test-user",
            "timestamp": datetime.now().isoformat()
        },
        "tools_used": ["web_search"],
        "importance": 0.8,
        "metadata": {
            "tags": ["ai", "ml", "test"]
        }
    }
    
    passed, response_data = run_test(
        "Episode Storage",
        f"{MEMORY_PREFIX}/store-episode",
        "POST",
        episode_data,
        timeout=10
    )
    
    if passed and response_data:
        if isinstance(response_data, dict) and response_data.get('success'):
            episode_id = response_data.get('episode_id')
            if episode_id:
                print(f"✅ Episode stored successfully with ID: {episode_id}")
                memory_tests_passed += 1
            else:
                print("❌ Episode storage succeeded but no ID returned")
        else:
            print("❌ Episode storage failed")
    
    # Test 3: Knowledge Storage
    print(f"\n🔍 TEST 3: Knowledge Storage")
    memory_tests_total += 1
    
    knowledge_data = {
        "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
        "type": "fact",
        "subject": "Machine Learning",
        "predicate": "is a subset of",
        "object": "Artificial Intelligence",
        "confidence": 0.9,
        "context": {
            "source": "test",
            "domain": "computer_science"
        }
    }
    
    passed, response_data = run_test(
        "Knowledge Storage",
        f"{MEMORY_PREFIX}/store-knowledge",
        "POST",
        knowledge_data,
        timeout=10
    )
    
    if passed and response_data:
        if isinstance(response_data, dict) and response_data.get('success'):
            knowledge_id = response_data.get('knowledge_id')
            if knowledge_id:
                print(f"✅ Knowledge stored successfully with ID: {knowledge_id}")
                memory_tests_passed += 1
            else:
                print("❌ Knowledge storage succeeded but no ID returned")
        else:
            print("❌ Knowledge storage failed")
    
    # Test 4: Context Retrieval (using correct endpoint)
    print(f"\n🔍 TEST 4: Memory Context Retrieval")
    memory_tests_total += 1
    
    context_data = {
        "query": "artificial intelligence machine learning",
        "context_type": "all",
        "max_results": 5
    }
    
    passed, response_data = run_test(
        "Memory Context Retrieval",
        f"{MEMORY_PREFIX}/retrieve-context",
        "POST",
        context_data,
        timeout=10
    )
    
    if passed and response_data:
        if isinstance(response_data, dict) and 'context' in response_data:
            context = response_data['context']
            if context:
                print("✅ Memory context retrieval working with context data")
                memory_tests_passed += 1
            else:
                print("⚠️  Memory context retrieval returned empty context")
        else:
            print("⚠️  Memory context retrieval format unexpected")
    
    # Test 5: Semantic Search
    print(f"\n🔍 TEST 5: Semantic Search")
    memory_tests_total += 1
    
    search_data = {
        "query": "artificial intelligence applications",
        "max_results": 5,
        "memory_types": ["all"]
    }
    
    passed, response_data = run_test(
        "Semantic Search",
        f"{MEMORY_PREFIX}/semantic-search",
        "POST",
        search_data,
        timeout=15
    )
    
    if passed and response_data:
        if isinstance(response_data, dict) and 'results' in response_data:
            results = response_data['results']
            total_results = response_data.get('total_results', 0)
            print(f"✅ Semantic search working with {total_results} results")
            memory_tests_passed += 1
        else:
            print("❌ Semantic search missing expected results structure")
    
    # Test 5: Chat Integration with Memory
    print(f"\n🔍 TEST 5: Chat Integration with Memory (KEY TEST)")
    memory_tests_total += 1
    
    chat_data = {
        "message": "Explain the benefits of artificial intelligence in healthcare",
        "context": {
            "task_id": f"test-chat-{uuid.uuid4()}",
            "user_id": "test-user"
        }
    }
    
    passed, response_data = run_test(
        "Chat Integration with Memory",
        f"{API_PREFIX}/chat",
        "POST",
        chat_data,
        timeout=30
    )
    
    if passed and response_data:
        if isinstance(response_data, dict):
            # KEY CHECK: memory_used should be true
            memory_used = response_data.get('memory_used', False)
            if memory_used:
                print("✅ Chat endpoint using memory (memory_used: true)")
                memory_tests_passed += 1
            else:
                print("❌ Chat endpoint NOT using memory (memory_used: false or missing)")
                print(f"   Response keys: {list(response_data.keys())}")
        else:
            print("⚠️  Chat response format unexpected")
    
    # Test 6: Multiple Conversations Memory Persistence
    print(f"\n🔍 TEST 6: Multiple Conversations Memory Persistence")
    memory_tests_total += 1
    
    task_id = f"test-persistence-{uuid.uuid4()}"
    conversations = [
        "What is artificial intelligence?",
        "How does machine learning relate to what we just discussed?",
        "Can you give me examples of AI applications in the field we talked about?",
        "What are the future trends in this area?"
    ]
    
    conversation_results = []
    memory_usage_count = 0
    
    for i, message in enumerate(conversations):
        print(f"\n   Conversation {i+1}: {message}")
        
        conv_data = {
            "message": message,
            "context": {
                "task_id": task_id,
                "user_id": "test-user",
                "conversation_step": i + 1
            }
        }
        
        passed, response_data = run_test(
            f"Conversation {i+1}",
            f"{API_PREFIX}/chat",
            "POST",
            conv_data,
            timeout=30
        )
        
        if passed and response_data:
            memory_used = response_data.get('memory_used', False)
            if memory_used:
                memory_usage_count += 1
                print(f"   ✅ Memory used in conversation {i+1}")
            else:
                print(f"   ❌ Memory NOT used in conversation {i+1}")
            
            conversation_results.append({
                "step": i + 1,
                "memory_used": memory_used,
                "response_length": len(str(response_data.get('response', '')))
            })
        else:
            conversation_results.append({
                "step": i + 1,
                "memory_used": False,
                "failed": True
            })
    
    # Check if memory was used consistently
    if memory_usage_count == len(conversations):
        print(f"✅ Memory used in ALL {len(conversations)} conversations")
        memory_tests_passed += 1
    else:
        print(f"❌ Memory used in only {memory_usage_count}/{len(conversations)} conversations")
    
    # Print memory integration test summary
    print(f"\n{'='*80}")
    print(f"🧠 MEMORY INTEGRATION TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Memory Tests Passed: {memory_tests_passed}/{memory_tests_total}")
    print(f"Memory Success Rate: {memory_tests_passed/memory_tests_total*100:.1f}%")
    
    return memory_tests_passed, memory_tests_total

def test_websearch_integration():
    """Test WebSearch integration with memory"""
    print(f"\n🔍 WEBSEARCH INTEGRATION TEST")
    
    websearch_data = {
        "message": "[WebSearch] latest developments in artificial intelligence 2025",
        "search_mode": "websearch",
        "context": {
            "task_id": f"test-websearch-{uuid.uuid4()}",
            "user_id": "test-user"
        }
    }
    
    passed, response_data = run_test(
        "WebSearch Integration with Memory",
        f"{API_PREFIX}/chat",
        "POST",
        websearch_data,
        timeout=45
    )
    
    if passed and response_data:
        memory_used = response_data.get('memory_used', False)
        search_mode = response_data.get('search_mode')
        search_data = response_data.get('search_data', {})
        
        print(f"   Memory Used: {memory_used}")
        print(f"   Search Mode: {search_mode}")
        print(f"   Search Results: {len(search_data.get('sources', []))} sources")
        
        if memory_used and search_mode == 'websearch':
            print("✅ WebSearch working with memory integration")
            return True
        else:
            print("❌ WebSearch not properly integrated with memory")
            return False
    
    return False

def print_final_summary():
    """Print comprehensive test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*100)
    print(f"🎯 COMPREHENSIVE BACKEND TEST SUMMARY")
    print("="*100)
    print(f"📅 Timestamp: {test_results['timestamp']}")
    print(f"📊 Total tests: {total}")
    print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
    
    # Calculate average response time
    response_times = [test.get('response_time', 0) for test in test_results['tests'] if 'response_time' in test]
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        print(f"⏱️  Average response time: {avg_response_time:.2f}s")
    
    print("="*100)
    
    # Print failed tests
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"   - {test['name']} ({test['endpoint']})")
                if "error" in test:
                    print(f"     Error: {test['error']}")
                elif "status_code" in test and "expected_status" in test:
                    print(f"     Expected status {test['expected_status']}, got {test['status_code']}")
    
    # Print passed tests summary
    print(f"\n✅ PASSED TESTS:")
    for test in test_results["tests"]:
        if test["passed"]:
            response_time = test.get('response_time', 0)
            print(f"   - {test['name']} ({response_time:.2f}s)")

def main():
    """Main test execution"""
    print(f"\n🚀 STARTING COMPREHENSIVE BACKEND TESTING")
    
    # 1. Backend Health and Status
    print(f"\n{'='*80}")
    print(f"1️⃣  BACKEND HEALTH AND STATUS TESTS")
    print(f"{'='*80}")
    
    run_test("Backend Health Check", "/health", "GET")
    run_test("Agent Health Check", f"{API_PREFIX}/health", "GET")
    run_test("Agent Status Check", f"{API_PREFIX}/status", "GET")
    
    # 2. Ollama Configuration Tests
    print(f"\n{'='*80}")
    print(f"2️⃣  OLLAMA CONFIGURATION TESTS")
    print(f"{'='*80}")
    
    ollama_check_data = {
        "endpoint": "https://78d08925604a.ngrok-free.app",
        "model": "llama3.1:8b"
    }
    
    run_test("Ollama Connection Check", f"{API_PREFIX}/ollama/check", "POST", ollama_check_data)
    run_test("Ollama Models List", f"{API_PREFIX}/ollama/models", "POST", ollama_check_data)
    
    # 3. Memory System Integration (COMPREHENSIVE)
    print(f"\n{'='*80}")
    print(f"3️⃣  MEMORY SYSTEM INTEGRATION TESTS (COMPREHENSIVE)")
    print(f"{'='*80}")
    
    memory_passed, memory_total = test_memory_integration_comprehensive()
    
    # 4. WebSearch Integration
    print(f"\n{'='*80}")
    print(f"4️⃣  WEBSEARCH INTEGRATION TEST")
    print(f"{'='*80}")
    
    websearch_success = test_websearch_integration()
    
    # 5. Error Handling Tests
    print(f"\n{'='*80}")
    print(f"5️⃣  ERROR HANDLING TESTS")
    print(f"{'='*80}")
    
    # Test invalid endpoint
    run_test("Invalid Endpoint", "/api/invalid", "GET", expected_status=404)
    
    # Test invalid chat data
    invalid_chat_data = {"invalid": "data"}
    run_test("Invalid Chat Data", f"{API_PREFIX}/chat", "POST", invalid_chat_data, expected_status=400)
    
    # Final Summary
    print_final_summary()
    
    # Memory-specific summary
    print(f"\n🧠 MEMORY SYSTEM ASSESSMENT:")
    print(f"   Memory Integration Success Rate: {memory_passed}/{memory_total} ({memory_passed/memory_total*100:.1f}%)")
    print(f"   WebSearch with Memory: {'✅ Working' if websearch_success else '❌ Failed'}")
    
    # Overall assessment
    total_success_rate = test_results["summary"]["passed"] / test_results["summary"]["total"] * 100
    
    if total_success_rate >= 90:
        print(f"\n🎉 OVERALL ASSESSMENT: ✅ EXCELLENT ({total_success_rate:.1f}% success rate)")
        print(f"   Backend is stable and memory integration is working well")
    elif total_success_rate >= 75:
        print(f"\n⚠️  OVERALL ASSESSMENT: 🟡 GOOD ({total_success_rate:.1f}% success rate)")
        print(f"   Backend is mostly working with some minor issues")
    else:
        print(f"\n❌ OVERALL ASSESSMENT: 🔴 NEEDS ATTENTION ({total_success_rate:.1f}% success rate)")
        print(f"   Backend has significant issues that need to be addressed")
    
    print(f"\n🏁 COMPREHENSIVE BACKEND TESTING COMPLETED")
    print(f"📊 Final Score: {test_results['summary']['passed']}/{test_results['summary']['total']} tests passed")

if __name__ == "__main__":
    main()