#!/usr/bin/env python3
"""
Memory Integration Test Script for Mitosis Backend - REVIEW REQUEST FULFILLMENT

This script tests the updated memory integration in the chat endpoint, focusing on:
1. Memory Initialization - verify memory_manager initializes correctly
2. Context Retrieval - test that chat endpoint retrieves relevant context automatically
3. Memory Storage - test that conversations are stored in episodic memory
4. Enhanced Agent - test if enhanced agent is enabled and working
5. Memory Usage Flag - verify memory_used flag is set correctly
6. Memory Persistence - test multiple conversations for memory persistence

Test endpoints:
- POST /api/agent/chat (main chat endpoint)
- POST /api/memory/retrieve_context (memory retrieval)
- POST /api/memory/store_episode (memory storage)
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"
MEMORY_PREFIX = "/api/memory"

print(f"🧠 MEMORY INTEGRATION TESTING - REVIEW REQUEST FULFILLMENT")
print(f"Using backend URL: {BASE_URL}")
print(f"Testing memory integration in chat endpoint as requested in review")

# Test results
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
}

def run_test(name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, timeout=30):
    """Run a test against an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    test_results["summary"]["total"] += 1
    
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"URL: {url}")
    print(f"METHOD: {method}")
    if data:
        print(f"DATA: {json.dumps(data, indent=2)}")
    
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        elapsed_time = time.time() - start_time
        status_code = response.status_code
        print(f"STATUS: {status_code} (took {elapsed_time:.2f}s)")
        
        try:
            response_data = response.json()
            print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data}")
        
        # Check status code
        status_ok = status_code == expected_status
        
        # Check expected keys
        keys_ok = True
        missing_keys = []
        if expected_keys and status_ok and isinstance(response_data, dict):
            for key in expected_keys:
                if key not in response_data:
                    keys_ok = False
                    missing_keys.append(key)
        
        # Determine test result
        passed = status_ok and keys_ok
        
        # Update test results
        test_results["tests"].append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "expected_status": expected_status,
            "passed": passed,
            "elapsed_time": elapsed_time,
            "missing_keys": missing_keys if not keys_ok else None,
            "response_data": response_data if passed else None
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED ({elapsed_time:.2f}s)")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED ({elapsed_time:.2f}s)")
            if not status_ok:
                print(f"  - Expected status {expected_status}, got {status_code}")
            if not keys_ok:
                print(f"  - Missing expected keys: {', '.join(missing_keys)}")
        
        return passed, response_data
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "error": str(e),
            "passed": False,
            "elapsed_time": elapsed_time
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception after {elapsed_time:.2f}s)")
        return False, None

def test_memory_system_initialization():
    """Test 1: Memory Initialization - verify memory_manager initializes correctly"""
    print(f"\n🧠 MEMORY INTEGRATION TEST 1: Memory System Initialization")
    
    # Test memory system status
    passed, response_data = run_test(
        "Memory System Status Check",
        f"{MEMORY_PREFIX}/status",
        method="GET",
        expected_keys=["is_initialized", "components", "system_info"]
    )
    
    if passed and response_data:
        is_initialized = response_data.get("is_initialized", False)
        components = response_data.get("components", {})
        system_info = response_data.get("system_info", {})
        
        print(f"\n📊 MEMORY SYSTEM ANALYSIS:")
        print(f"   Initialized: {is_initialized}")
        print(f"   Components: {len(components)} components")
        
        # Check for expected components
        expected_components = [
            "working_memory", "episodic_memory", "semantic_memory", 
            "procedural_memory", "embedding_service", "semantic_indexer"
        ]
        
        for component in expected_components:
            status = components.get(component, "NOT FOUND")
            print(f"   - {component}: {status}")
        
        print(f"   System Info: {json.dumps(system_info, indent=4)}")
        
        if is_initialized and len(components) >= 6:
            print(f"✅ Memory system is properly initialized with all components")
            return True
        else:
            print(f"❌ Memory system initialization incomplete")
            return False
    
    return False

def test_memory_analytics():
    """Test memory analytics endpoint"""
    print(f"\n🧠 MEMORY INTEGRATION TEST: Memory Analytics")
    
    passed, response_data = run_test(
        "Memory Analytics",
        f"{MEMORY_PREFIX}/analytics",
        method="GET",
        expected_keys=["overview", "memory_efficiency", "learning_insights"]
    )
    
    if passed and response_data:
        overview = response_data.get("overview", {})
        memory_efficiency = response_data.get("memory_efficiency", {})
        learning_insights = response_data.get("learning_insights", {})
        
        print(f"\n📊 MEMORY ANALYTICS:")
        print(f"   Overview: {json.dumps(overview, indent=4)}")
        print(f"   Memory Efficiency: {json.dumps(memory_efficiency, indent=4)}")
        print(f"   Learning Insights: {json.dumps(learning_insights, indent=4)}")
        
        return True
    
    return False

def test_memory_operations():
    """Test memory storage operations"""
    print(f"\n🧠 MEMORY INTEGRATION TEST: Memory Storage Operations")
    
    # Test episode storage
    episode_data = {
        "content": "Test conversation about artificial intelligence and machine learning",
        "context": {
            "task_id": f"test-{uuid.uuid4()}",
            "user_id": "test-user",
            "session_id": f"session-{uuid.uuid4()}"
        },
        "metadata": {
            "topic": "AI/ML discussion",
            "importance": 0.8,
            "tags": ["artificial intelligence", "machine learning", "test"]
        }
    }
    
    passed1, response1 = run_test(
        "Episode Storage",
        f"{MEMORY_PREFIX}/store_episode",
        method="POST",
        data=episode_data,
        expected_keys=["success", "episode_id"]
    )
    
    # Test knowledge storage
    knowledge_data = {
        "fact": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data",
        "category": "AI/ML",
        "confidence": 0.9,
        "source": "test_conversation",
        "context": {
            "domain": "technology",
            "relevance": "high"
        }
    }
    
    passed2, response2 = run_test(
        "Knowledge Storage",
        f"{MEMORY_PREFIX}/store_knowledge",
        method="POST",
        data=knowledge_data,
        expected_keys=["success", "fact_id"]
    )
    
    # Test procedure storage
    procedure_data = {
        "name": "AI Research Process",
        "steps": [
            "Define research question",
            "Gather relevant data",
            "Apply machine learning algorithms",
            "Evaluate results",
            "Draw conclusions"
        ],
        "category": "research",
        "context": {
            "domain": "AI research",
            "complexity": "medium"
        }
    }
    
    passed3, response3 = run_test(
        "Procedure Storage",
        f"{MEMORY_PREFIX}/store_procedure",
        method="POST",
        data=procedure_data,
        expected_keys=["success", "procedure_id"]
    )
    
    return passed1 and passed2 and passed3

def test_memory_retrieval():
    """Test memory context retrieval"""
    print(f"\n🧠 MEMORY INTEGRATION TEST: Memory Context Retrieval")
    
    # Test context retrieval
    context_data = {
        "query": "artificial intelligence machine learning",
        "context": {
            "task_id": f"test-{uuid.uuid4()}",
            "user_id": "test-user"
        },
        "max_results": 5
    }
    
    passed, response_data = run_test(
        "Memory Context Retrieval",
        f"{MEMORY_PREFIX}/retrieve_context",
        method="POST",
        data=context_data,
        expected_keys=["episodic_memory", "procedural_memory", "semantic_memory", "working_memory", "synthesized_context"]
    )
    
    if passed and response_data:
        episodic = response_data.get("episodic_memory", [])
        procedural = response_data.get("procedural_memory", [])
        semantic = response_data.get("semantic_memory", [])
        working = response_data.get("working_memory", [])
        synthesized = response_data.get("synthesized_context", "")
        
        print(f"\n📊 MEMORY RETRIEVAL ANALYSIS:")
        print(f"   Episodic Memory: {len(episodic)} items")
        print(f"   Procedural Memory: {len(procedural)} items")
        print(f"   Semantic Memory: {len(semantic)} items")
        print(f"   Working Memory: {len(working)} items")
        print(f"   Synthesized Context: {len(synthesized)} characters")
        
        return True
    
    return False

def test_semantic_search():
    """Test semantic search functionality"""
    print(f"\n🧠 MEMORY INTEGRATION TEST: Semantic Search")
    
    search_data = {
        "query": "machine learning algorithms",
        "max_results": 3,
        "threshold": 0.5
    }
    
    passed, response_data = run_test(
        "Semantic Search",
        f"{MEMORY_PREFIX}/search",
        method="POST",
        data=search_data,
        expected_keys=["results", "query", "search_stats"]
    )
    
    if passed and response_data:
        results = response_data.get("results", [])
        query = response_data.get("query", "")
        stats = response_data.get("search_stats", {})
        
        print(f"\n📊 SEMANTIC SEARCH ANALYSIS:")
        print(f"   Query: {query}")
        print(f"   Results: {len(results)} items found")
        print(f"   Search Stats: {json.dumps(stats, indent=4)}")
        
        return True
    
    return False

def test_chat_with_memory_integration():
    """Test 2: Chat Integration with Memory - verify memory_used flag and context usage"""
    print(f"\n🧠 MEMORY INTEGRATION TEST 2: Chat Integration with Memory")
    
    # Test chat with memory integration
    chat_data = {
        "message": "Tell me about artificial intelligence and its applications in healthcare",
        "context": {
            "task_id": f"memory-test-{uuid.uuid4()}",
            "user_id": "test-user",
            "session_id": f"session-{uuid.uuid4()}"
        }
    }
    
    passed, response_data = run_test(
        "Chat Integration with Memory",
        f"{API_PREFIX}/chat",
        method="POST",
        data=chat_data,
        expected_keys=["response", "memory_used", "task_id"],
        timeout=60
    )
    
    if passed and response_data:
        memory_used = response_data.get("memory_used", False)
        response_text = response_data.get("response", "")
        task_id = response_data.get("task_id", "")
        
        print(f"\n📊 CHAT MEMORY INTEGRATION ANALYSIS:")
        print(f"   Memory Used: {memory_used}")
        print(f"   Response Length: {len(response_text)} characters")
        print(f"   Task ID: {task_id}")
        print(f"   Response Preview: {response_text[:200]}...")
        
        if memory_used:
            print(f"✅ Chat endpoint is using memory integration (memory_used: true)")
            return True
        else:
            print(f"❌ Chat endpoint is not using memory integration (memory_used: false)")
            return False
    
    return False

def test_multiple_conversations_memory_persistence():
    """Test 6: Memory Persistence - test multiple conversations for memory persistence"""
    print(f"\n🧠 MEMORY INTEGRATION TEST 6: Multiple Conversations Memory Persistence")
    
    session_id = f"persistence-test-{uuid.uuid4()}"
    user_id = "test-user-persistence"
    
    conversations = [
        "What is machine learning and how does it work?",
        "Can you explain neural networks in simple terms?",
        "How is deep learning different from traditional machine learning?",
        "What are some practical applications of AI in business?"
    ]
    
    memory_usage_results = []
    
    for i, message in enumerate(conversations):
        print(f"\n--- Conversation {i+1}/4 ---")
        
        chat_data = {
            "message": message,
            "context": {
                "task_id": f"persistence-test-{i+1}-{uuid.uuid4()}",
                "user_id": user_id,
                "session_id": session_id
            }
        }
        
        passed, response_data = run_test(
            f"Conversation {i+1} Memory Persistence",
            f"{API_PREFIX}/chat",
            method="POST",
            data=chat_data,
            expected_keys=["response", "memory_used", "task_id"],
            timeout=60
        )
        
        if passed and response_data:
            memory_used = response_data.get("memory_used", False)
            response_text = response_data.get("response", "")
            task_id = response_data.get("task_id", "")
            
            memory_usage_results.append({
                "conversation": i+1,
                "memory_used": memory_used,
                "response_length": len(response_text),
                "task_id": task_id
            })
            
            print(f"   Memory Used: {memory_used}")
            print(f"   Response Length: {len(response_text)} characters")
            print(f"   Task ID: {task_id}")
        else:
            memory_usage_results.append({
                "conversation": i+1,
                "memory_used": False,
                "error": "Request failed"
            })
        
        # Small delay between conversations
        time.sleep(1)
    
    # Analyze memory persistence results
    successful_conversations = len([r for r in memory_usage_results if r.get("memory_used")])
    total_conversations = len(conversations)
    
    print(f"\n📊 MEMORY PERSISTENCE ANALYSIS:")
    print(f"   Total Conversations: {total_conversations}")
    print(f"   Conversations with Memory: {successful_conversations}")
    print(f"   Memory Usage Rate: {successful_conversations}/{total_conversations} ({successful_conversations/total_conversations*100:.1f}%)")
    
    for result in memory_usage_results:
        conv_num = result["conversation"]
        memory_used = result.get("memory_used", False)
        status = "✅" if memory_used else "❌"
        print(f"   Conversation {conv_num}: {status} Memory Used: {memory_used}")
    
    # Consider test passed if at least 75% of conversations used memory
    success_rate = successful_conversations / total_conversations
    if success_rate >= 0.75:
        print(f"✅ Memory persistence test PASSED ({success_rate*100:.1f}% success rate)")
        return True
    else:
        print(f"❌ Memory persistence test FAILED ({success_rate*100:.1f}% success rate)")
        return False

def print_summary():
    """Print test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print(f"🧠 MEMORY INTEGRATION TEST SUMMARY - REVIEW REQUEST FULFILLMENT")
    print(f"Timestamp: {test_results['timestamp']}")
    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print("="*80)
    
    # Print detailed results
    print(f"\n📊 DETAILED TEST RESULTS:")
    for test in test_results["tests"]:
        status = "✅ PASSED" if test["passed"] else "❌ FAILED"
        elapsed = test.get("elapsed_time", 0)
        print(f"   {status} - {test['name']} ({elapsed:.2f}s)")
        
        if not test["passed"]:
            if "error" in test:
                print(f"      Error: {test['error']}")
            elif "status_code" in test and "expected_status" in test:
                print(f"      Expected status {test['expected_status']}, got {test['status_code']}")
            if "missing_keys" in test and test["missing_keys"]:
                print(f"      Missing keys: {', '.join(test['missing_keys'])}")
    
    # Print failed tests summary
    if failed > 0:
        print(f"\n❌ FAILED TESTS SUMMARY:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"   - {test['name']} ({test['endpoint']})")
    
    # Final assessment
    success_rate = passed / total if total > 0 else 0
    print(f"\n🎯 FINAL ASSESSMENT:")
    if success_rate >= 0.9:
        print(f"   ✅ EXCELLENT - Memory integration is working perfectly ({success_rate*100:.1f}% success rate)")
    elif success_rate >= 0.75:
        print(f"   ✅ GOOD - Memory integration is working well ({success_rate*100:.1f}% success rate)")
    elif success_rate >= 0.5:
        print(f"   ⚠️ PARTIAL - Memory integration has some issues ({success_rate*100:.1f}% success rate)")
    else:
        print(f"   ❌ POOR - Memory integration needs significant work ({success_rate*100:.1f}% success rate)")

def main():
    """Main test execution"""
    print(f"🚀 Starting Memory Integration Testing...")
    print(f"Focus: Testing updated memory integration in chat endpoint as requested in review")
    
    # Test 1: Memory System Initialization
    memory_init_ok = test_memory_system_initialization()
    
    # Test Memory Analytics
    test_memory_analytics()
    
    # Test Memory Operations
    test_memory_operations()
    
    # Test Memory Retrieval
    test_memory_retrieval()
    
    # Test Semantic Search
    test_semantic_search()
    
    # Test 2: Chat Integration with Memory
    chat_memory_ok = test_chat_with_memory_integration()
    
    # Test 6: Memory Persistence
    memory_persistence_ok = test_multiple_conversations_memory_persistence()
    
    # Print comprehensive summary
    print_summary()
    
    # Final verdict
    print(f"\n🎯 MEMORY INTEGRATION REVIEW REQUEST VERDICT:")
    print(f"   1. Memory Initialization: {'✅ WORKING' if memory_init_ok else '❌ FAILED'}")
    print(f"   2. Chat Memory Integration: {'✅ WORKING' if chat_memory_ok else '❌ FAILED'}")
    print(f"   3. Memory Persistence: {'✅ WORKING' if memory_persistence_ok else '❌ FAILED'}")
    
    if memory_init_ok and chat_memory_ok and memory_persistence_ok:
        print(f"\n🎉 REVIEW REQUEST FULFILLED: Memory integration is working as expected!")
        print(f"   - Memory system initializes correctly")
        print(f"   - Chat endpoint uses memory automatically (memory_used: true)")
        print(f"   - Memory persistence across conversations is working")
    else:
        print(f"\n⚠️ REVIEW REQUEST ISSUES FOUND: Memory integration needs attention")
        if not memory_init_ok:
            print(f"   - Memory system initialization issues")
        if not chat_memory_ok:
            print(f"   - Chat endpoint not using memory properly")
        if not memory_persistence_ok:
            print(f"   - Memory persistence across conversations failing")

if __name__ == "__main__":
    main()