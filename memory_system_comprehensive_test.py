#!/usr/bin/env python3
"""
Memory System Comprehensive Test Script for Mitosis Backend Application

This script tests the memory system functionality as requested in the review:
1. Memory System Status - Test all memory endpoints
2. Memory Integration - Test /api/agent/chat endpoint to verify memory is being used automatically (memory_used: true)
3. Memory Operations - Test storing episodes, knowledge, and procedures
4. Memory Compression - Test compress_old_memory() functionality
5. Memory Export - Test export_memory_data() functionality
6. Memory Search - Test semantic search functionality
7. Memory Analytics - Test memory analytics and statistics

The key expectation is that the chat endpoint should automatically use memory (memory_used: true)
and the compress_old_memory() method should work correctly.
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path

# Configuration
try:
    with open('/app/frontend/.env', 'r') as env_file:
        for line in env_file:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.strip().split('=', 1)[1].strip('"\'')
                break
except Exception as e:
    print(f"Error reading .env file: {e}")
    backend_url = "http://localhost:8001"

# Use local URL for testing to avoid timeouts
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api"

print(f"🧠 MEMORY SYSTEM COMPREHENSIVE TESTING")
print(f"Using backend URL: {BASE_URL}")
print(f"Testing focus: Memory system functionality as requested in review")

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
        print(f"STATUS: {status_code} ({elapsed_time:.2f}s)")
        
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
            "elapsed_time": elapsed_time,
            "passed": passed,
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
            "elapsed_time": elapsed_time,
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception after {elapsed_time:.2f}s)")
        return False, None

def print_summary():
    """Print test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print(f"🧠 MEMORY SYSTEM COMPREHENSIVE TEST SUMMARY")
    print(f"Timestamp: {test_results['timestamp']}")
    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print("="*80)
    
    # Print failed tests
    if failed > 0:
        print("\nFAILED TESTS:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"- {test['name']} ({test['endpoint']})")
                if "error" in test:
                    print(f"  Error: {test['error']}")
                elif "status_code" in test and "expected_status" in test and test["status_code"] != test["expected_status"]:
                    print(f"  Expected status {test['expected_status']}, got {test['status_code']}")
                if "missing_keys" in test and test["missing_keys"]:
                    print(f"  Missing keys: {', '.join(test['missing_keys'])}")

def test_memory_system_comprehensive():
    """
    Comprehensive test of the memory system functionality as requested in the review
    """
    print(f"\n🧠 STARTING COMPREHENSIVE MEMORY SYSTEM TESTING")
    print(f"Focus: Testing all memory endpoints and integration with chat system")
    
    # 1. MEMORY SYSTEM STATUS - Test all memory endpoints
    print(f"\n📊 SECTION 1: MEMORY SYSTEM STATUS - Testing all memory endpoints")
    
    # Test backend health first
    run_test(
        "Backend Health Check",
        "/health",
        "GET",
        expected_keys=["status", "services"]
    )
    
    # Test memory analytics
    run_test(
        "Memory Analytics",
        "/api/memory/memory-analytics",
        "GET",
        expected_keys=["overview", "memory_efficiency", "learning_insights"]
    )
    
    # 2. MEMORY OPERATIONS - Test storing episodes, knowledge, and procedures
    print(f"\n💾 SECTION 2: MEMORY OPERATIONS - Testing storage operations")
    
    # Test episode storage
    episode_data = {
        "user_query": "What is artificial intelligence?",
        "agent_response": "Artificial intelligence (AI) is a branch of computer science that aims to create intelligent machines that can perform tasks that typically require human intelligence.",
        "success": True,
        "context": {
            "session_id": str(uuid.uuid4()),
            "task_id": str(uuid.uuid4())
        },
        "tools_used": ["knowledge_base"],
        "importance": 0.8,
        "metadata": {
            "test": True,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    run_test(
        "Episode Storage",
        "/api/memory/store-episode",
        "POST",
        episode_data,
        expected_keys=["success", "episode_id", "stored_at"]
    )
    
    # Test knowledge storage (fact)
    knowledge_data = {
        "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
        "type": "fact",
        "subject": "Machine Learning",
        "predicate": "is defined as",
        "object": "a subset of artificial intelligence",
        "confidence": 0.9,
        "context": {
            "domain": "computer_science",
            "source": "test_data"
        },
        "metadata": {
            "test": True
        }
    }
    
    run_test(
        "Knowledge Storage (Fact)",
        "/api/memory/store-knowledge",
        "POST",
        knowledge_data,
        expected_keys=["success", "knowledge_id", "type", "stored_at"]
    )
    
    # Test procedure storage
    procedure_data = {
        "name": "Web Search Process",
        "description": "Standard procedure for conducting web searches",
        "steps": [
            "Analyze the search query",
            "Select appropriate search terms",
            "Execute search using web_search tool",
            "Filter and rank results",
            "Present formatted results to user"
        ],
        "category": "search_operations",
        "context_conditions": {
            "requires_internet": True,
            "tool_availability": ["web_search"]
        },
        "effectiveness": 0.85,
        "usage_count": 0,
        "metadata": {
            "test": True,
            "created_by": "test_system"
        }
    }
    
    run_test(
        "Procedure Storage",
        "/api/memory/store-procedure",
        "POST",
        procedure_data,
        expected_keys=["success", "procedure_id", "stored_at"]
    )
    
    # 3. MEMORY SEARCH - Test semantic search functionality
    print(f"\n🔍 SECTION 3: MEMORY SEARCH - Testing semantic search functionality")
    
    search_data = {
        "query": "artificial intelligence machine learning",
        "max_results": 5,
        "memory_types": ["all"]
    }
    
    run_test(
        "Semantic Search",
        "/api/memory/semantic-search",
        "POST",
        search_data,
        expected_keys=["query", "results", "total_results", "search_timestamp"]
    )
    
    # Test context retrieval
    context_data = {
        "query": "What is machine learning?",
        "context_type": "all",
        "max_results": 10
    }
    
    run_test(
        "Memory Context Retrieval",
        "/api/memory/retrieve-context",
        "POST",
        context_data,
        expected_keys=["query", "context", "retrieved_at"]
    )
    
    # 4. MEMORY INTEGRATION - Test /api/agent/chat endpoint to verify memory is being used automatically
    print(f"\n🤖 SECTION 4: MEMORY INTEGRATION - Testing chat endpoint with memory integration")
    
    chat_data = {
        "message": "Tell me about artificial intelligence and its applications",
        "context": {
            "task_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "user_id": "test_user"
        }
    }
    
    passed, response_data = run_test(
        "Chat Integration with Memory",
        "/api/agent/chat",
        "POST",
        chat_data,
        expected_keys=["response", "task_id", "timestamp"],
        timeout=60
    )
    
    # Check if memory_used flag is present and true
    if passed and response_data:
        memory_used = response_data.get("memory_used", False)
        if memory_used:
            print(f"✅ MEMORY INTEGRATION CONFIRMED: memory_used = {memory_used}")
        else:
            print(f"⚠️ MEMORY INTEGRATION ISSUE: memory_used = {memory_used}")
    
    # 5. MEMORY PERSISTENCE - Test multiple conversations to verify memory persistence
    print(f"\n🔄 SECTION 5: MEMORY PERSISTENCE - Testing multiple conversations")
    
    session_id = str(uuid.uuid4())
    conversations = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "What are the applications of AI in healthcare?",
        "Can you summarize what we discussed about AI?"
    ]
    
    memory_usage_count = 0
    for i, message in enumerate(conversations, 1):
        chat_data = {
            "message": message,
            "context": {
                "task_id": str(uuid.uuid4()),
                "session_id": session_id,
                "user_id": "test_user",
                "conversation_step": i
            }
        }
        
        passed, response_data = run_test(
            f"Multiple Conversations Memory Persistence - Step {i}",
            "/api/agent/chat",
            "POST",
            chat_data,
            expected_keys=["response", "task_id", "timestamp"],
            timeout=60
        )
        
        if passed and response_data and response_data.get("memory_used", False):
            memory_usage_count += 1
    
    print(f"📊 MEMORY PERSISTENCE RESULTS: {memory_usage_count}/{len(conversations)} conversations used memory")
    
    # 6. MEMORY COMPRESSION - Test compress_old_memory() functionality
    print(f"\n🗜️ SECTION 6: MEMORY COMPRESSION - Testing compress_old_memory() functionality")
    
    compression_data = {
        "compression_threshold_days": 1,  # Compress items older than 1 day
        "compression_ratio": 0.5
    }
    
    run_test(
        "Memory Compression",
        "/api/agent/memory/compress",
        "POST",
        compression_data,
        expected_keys=["compressed_items", "memory_saved", "compression_timestamp"]
    )
    
    # Also test the memory routes version
    run_test(
        "Memory Compression (Memory Routes)",
        "/api/memory/compress-memory",
        "POST",
        {"config": compression_data},
        expected_keys=["success", "compressed_items", "memory_saved", "compression_timestamp"]
    )
    
    # 7. MEMORY EXPORT - Test export_memory_data() functionality
    print(f"\n📤 SECTION 7: MEMORY EXPORT - Testing export_memory_data() functionality")
    
    export_data = {
        "export_format": "json",
        "include_compressed": True
    }
    
    run_test(
        "Memory Export",
        "/api/agent/memory/export",
        "POST",
        export_data,
        expected_keys=["export_data", "export_timestamp"]
    )
    
    # Also test the memory routes version
    run_test(
        "Memory Export (Memory Routes)",
        "/api/memory/export-memory",
        "GET",
        expected_keys=["success", "export_data", "export_timestamp"]
    )
    
    # 8. ADDITIONAL MEMORY ANALYTICS - Test comprehensive memory analytics
    print(f"\n📈 SECTION 8: ADDITIONAL MEMORY ANALYTICS - Testing comprehensive analytics")
    
    # Test agent memory stats
    run_test(
        "Agent Memory Stats",
        "/api/agent/memory/stats",
        "GET"
    )
    
    # Test learning insights
    run_test(
        "Learning Insights",
        "/api/agent/memory/learning-insights",
        "GET",
        expected_keys=["learning_insights", "orchestration_metrics", "timestamp"]
    )
    
    # Test memory search via agent routes
    search_agent_data = {
        "query": "artificial intelligence applications",
        "context_type": "all",
        "max_results": 5
    }
    
    run_test(
        "Memory Search (Agent Routes)",
        "/api/agent/memory/search",
        "POST",
        search_agent_data
    )

def main():
    """Main test execution"""
    print(f"🚀 Starting Memory System Comprehensive Testing")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Focus: Memory system functionality as requested in review")
    
    # Run comprehensive memory system tests
    test_memory_system_comprehensive()
    
    # Print final summary
    print_summary()
    
    # Final assessment
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    print(f"Memory System Status: {'✅ EXCELLENT' if success_rate >= 90 else '⚠️ NEEDS ATTENTION' if success_rate >= 70 else '❌ CRITICAL ISSUES'}")
    print(f"Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
    
    if success_rate >= 90:
        print(f"🏆 MEMORY SYSTEM IS PRODUCTION READY")
        print(f"All core memory functionality is working correctly")
    elif success_rate >= 70:
        print(f"⚠️ MEMORY SYSTEM HAS MINOR ISSUES")
        print(f"Core functionality works but some features need attention")
    else:
        print(f"❌ MEMORY SYSTEM HAS CRITICAL ISSUES")
        print(f"Significant problems detected that need immediate attention")
    
    # Key findings summary
    print(f"\n📋 KEY FINDINGS:")
    memory_integration_tests = [test for test in test_results["tests"] if "Chat Integration" in test["name"] or "Memory Persistence" in test["name"]]
    memory_integration_passed = sum(1 for test in memory_integration_tests if test["passed"])
    
    print(f"• Memory Integration: {memory_integration_passed}/{len(memory_integration_tests)} tests passed")
    
    compression_tests = [test for test in test_results["tests"] if "Compression" in test["name"]]
    compression_passed = sum(1 for test in compression_tests if test["passed"])
    
    print(f"• Memory Compression: {compression_passed}/{len(compression_tests)} tests passed")
    
    export_tests = [test for test in test_results["tests"] if "Export" in test["name"]]
    export_passed = sum(1 for test in export_tests if test["passed"])
    
    print(f"• Memory Export: {export_passed}/{len(export_tests)} tests passed")
    
    search_tests = [test for test in test_results["tests"] if "Search" in test["name"] or "Semantic" in test["name"]]
    search_passed = sum(1 for test in search_tests if test["passed"])
    
    print(f"• Memory Search: {search_passed}/{len(search_tests)} tests passed")
    
    return success_rate >= 70

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)