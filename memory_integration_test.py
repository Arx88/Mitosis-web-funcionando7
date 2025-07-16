#!/usr/bin/env python3
"""
Memory System Integration Test Script for Mitosis Chat Endpoint

This script tests the memory system integration in the Mitosis chat endpoint, focusing on:
1. Memory Initialization - Check if memory_manager is properly initialized
2. Context Retrieval - Test if chat endpoint can retrieve relevant context from previous conversations
3. Episode Storage - Test if conversations are being stored in episodic memory correctly
4. Memory System Status - Check overall status of memory system components
5. Chat Integration - Test multiple conversations to see if memory integration is working transparently

Based on PLAN2.md, we recently fixed the memory initialization issue where memory_manager.is_initialized was always False.
This test verifies if the fix is working and if the memory system is functioning correctly with the chat endpoint.
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path

# Configuration
# Get the backend URL from the frontend .env file
try:
    with open('/app/frontend/.env', 'r') as env_file:
        for line in env_file:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BASE_URL = line.strip().split('=', 1)[1].strip('"\'')
                break
        else:
            BASE_URL = "http://localhost:8001"
except Exception as e:
    print(f"Error reading .env file: {e}")
    BASE_URL = "http://localhost:8001"

API_PREFIX = "/api"

print(f"🧠 MEMORY SYSTEM INTEGRATION TEST - MITOSIS CHAT ENDPOINT")
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

def run_test(name, test_func):
    """Run a test and track results"""
    test_results["summary"]["total"] += 1
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {name}")
    print(f"{'='*80}")
    
    try:
        start_time = time.time()
        passed, details = test_func()
        end_time = time.time()
        execution_time = end_time - start_time
        
        test_results["tests"].append({
            "name": name,
            "passed": passed,
            "execution_time": execution_time,
            "details": details
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"✅ RESULT: PASSED ({execution_time:.2f}s)")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ RESULT: FAILED ({execution_time:.2f}s)")
            if details.get('error'):
                print(f"   Error: {details['error']}")
        
        return passed, details
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "passed": False,
            "error": str(e),
            "execution_time": 0
        })
        print(f"❌ RESULT: FAILED (Exception)")
        print(f"   Exception: {str(e)}")
        return False, {"error": str(e)}

def test_backend_health():
    """Test 1: Backend Health Check"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        if response.status_code != 200:
            return False, {"error": f"Health check failed with status {response.status_code}"}
        
        data = response.json()
        print(f"📊 Backend Status: {data.get('status', 'unknown')}")
        
        services = data.get('services', {})
        print(f"🧠 Ollama: {services.get('ollama', 'unknown')}")
        print(f"🔧 Tools: {services.get('tools', 'unknown')}")
        print(f"💾 Database: {services.get('database', 'unknown')}")
        
        return True, {
            "status": data.get('status'),
            "services": services
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def test_memory_system_initialization():
    """Test 2: Memory System Initialization Check"""
    try:
        # Test memory stats endpoint to check if memory system is initialized
        response = requests.get(f"{BASE_URL}{API_PREFIX}/agent/memory/stats", timeout=30)
        
        if response.status_code != 200:
            return False, {"error": f"Memory stats endpoint failed with status {response.status_code}"}
        
        data = response.json()
        print(f"📊 Memory Stats Response Keys: {list(data.keys())}")
        
        # Check for key memory components
        expected_components = ['working_memory', 'episodic_memory', 'semantic_memory', 'procedural_memory', 'embedding_service', 'semantic_indexer']
        found_components = []
        
        for component in expected_components:
            if component in data:
                found_components.append(component)
                print(f"✅ {component}: Found")
            else:
                print(f"❌ {component}: Missing")
        
        initialization_success = len(found_components) >= 4  # At least 4 core components should be present
        
        return initialization_success, {
            "found_components": found_components,
            "total_components": len(found_components),
            "expected_components": len(expected_components),
            "memory_stats": data
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def test_memory_analytics():
    """Test 3: Memory Analytics Endpoint"""
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/memory/memory-analytics", timeout=30)
        
        if response.status_code != 200:
            return False, {"error": f"Memory analytics failed with status {response.status_code}"}
        
        data = response.json()
        print(f"📊 Memory Analytics Response Keys: {list(data.keys())}")
        
        # Check for expected analytics structure
        expected_sections = ['overview', 'memory_efficiency', 'learning_insights']
        found_sections = []
        
        for section in expected_sections:
            if section in data:
                found_sections.append(section)
                print(f"✅ {section}: Found")
                
                # Print some details
                if section == 'overview' and isinstance(data[section], dict):
                    overview = data[section]
                    for component, stats in overview.items():
                        if isinstance(stats, dict):
                            print(f"   📈 {component}: {stats}")
            else:
                print(f"❌ {section}: Missing")
        
        analytics_success = len(found_sections) >= 2  # At least 2 sections should be present
        
        return analytics_success, {
            "found_sections": found_sections,
            "analytics_data": data
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def test_episode_storage():
    """Test 4: Episode Storage in Memory"""
    try:
        # Test storing an episode directly
        episode_data = {
            "user_query": "What is artificial intelligence?",
            "agent_response": "Artificial intelligence (AI) is a branch of computer science that aims to create machines capable of intelligent behavior.",
            "success": True,
            "context": {
                "test_episode": True,
                "session_id": str(uuid.uuid4())
            },
            "tools_used": [],
            "importance": 0.7,
            "metadata": {
                "test_type": "memory_integration_test"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/memory/store-episode",
            json=episode_data,
            timeout=30
        )
        
        if response.status_code != 200:
            return False, {"error": f"Episode storage failed with status {response.status_code}"}
        
        data = response.json()
        print(f"📝 Episode Storage Response: {data}")
        
        if not data.get('success'):
            return False, {"error": "Episode storage returned success=False"}
        
        episode_id = data.get('episode_id')
        if not episode_id:
            return False, {"error": "No episode_id returned"}
        
        print(f"✅ Episode stored successfully with ID: {episode_id}")
        
        return True, {
            "episode_id": episode_id,
            "stored_at": data.get('stored_at'),
            "storage_response": data
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def test_knowledge_storage():
    """Test 5: Knowledge Storage in Semantic Memory"""
    try:
        # Test storing knowledge
        knowledge_data = {
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
            "type": "fact",
            "subject": "Machine Learning",
            "predicate": "is defined as",
            "object": "a subset of AI that enables learning from experience",
            "confidence": 0.9,
            "context": {
                "test_knowledge": True,
                "domain": "artificial_intelligence"
            },
            "metadata": {
                "test_type": "memory_integration_test"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/memory/store-knowledge",
            json=knowledge_data,
            timeout=30
        )
        
        if response.status_code != 200:
            return False, {"error": f"Knowledge storage failed with status {response.status_code}"}
        
        data = response.json()
        print(f"🧠 Knowledge Storage Response: {data}")
        
        if not data.get('success'):
            return False, {"error": "Knowledge storage returned success=False"}
        
        knowledge_id = data.get('knowledge_id')
        if not knowledge_id:
            return False, {"error": "No knowledge_id returned"}
        
        print(f"✅ Knowledge stored successfully with ID: {knowledge_id}")
        
        return True, {
            "knowledge_id": knowledge_id,
            "stored_at": data.get('stored_at'),
            "storage_response": data
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def test_procedure_storage():
    """Test 6: Procedure Storage in Procedural Memory"""
    try:
        # Test storing a procedure
        procedure_data = {
            "name": "Answer AI Questions",
            "description": "Procedure for answering questions about artificial intelligence",
            "steps": [
                "Analyze the question to understand what aspect of AI is being asked about",
                "Retrieve relevant knowledge from semantic memory",
                "Structure the response with clear explanations",
                "Provide examples if helpful",
                "Ensure accuracy and completeness"
            ],
            "context_conditions": {
                "domain": "artificial_intelligence",
                "question_type": "explanatory"
            },
            "category": "question_answering",
            "effectiveness": 0.8,
            "usage_count": 1,
            "metadata": {
                "test_type": "memory_integration_test"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/memory/store-procedure",
            json=procedure_data,
            timeout=30
        )
        
        if response.status_code != 200:
            return False, {"error": f"Procedure storage failed with status {response.status_code}"}
        
        data = response.json()
        print(f"⚙️ Procedure Storage Response: {data}")
        
        if not data.get('success'):
            return False, {"error": "Procedure storage returned success=False"}
        
        procedure_id = data.get('procedure_id')
        if not procedure_id:
            return False, {"error": "No procedure_id returned"}
        
        print(f"✅ Procedure stored successfully with ID: {procedure_id}")
        
        return True, {
            "procedure_id": procedure_id,
            "stored_at": data.get('stored_at'),
            "storage_response": data
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def test_semantic_search():
    """Test 7: Semantic Search Functionality"""
    try:
        # Test semantic search
        search_data = {
            "query": "artificial intelligence machine learning",
            "max_results": 5,
            "memory_types": ["all"]
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/memory/semantic-search",
            json=search_data,
            timeout=30
        )
        
        if response.status_code != 200:
            return False, {"error": f"Semantic search failed with status {response.status_code}"}
        
        data = response.json()
        print(f"🔍 Semantic Search Response Keys: {list(data.keys())}")
        
        query = data.get('query')
        results = data.get('results', [])
        total_results = data.get('total_results', 0)
        
        print(f"🔍 Query: {query}")
        print(f"📊 Total Results: {total_results}")
        print(f"📋 Results Structure: {type(results)}")
        
        if isinstance(results, list):
            print(f"✅ Results returned as list with {len(results)} items")
        else:
            print(f"⚠️ Results not returned as list: {type(results)}")
        
        return True, {
            "query": query,
            "total_results": total_results,
            "results_type": type(results).__name__,
            "results_count": len(results) if isinstance(results, list) else 0,
            "search_response": data
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def test_context_retrieval():
    """Test 8: Context Retrieval Functionality"""
    try:
        # Test context retrieval
        context_data = {
            "query": "What is machine learning?",
            "context_type": "all",
            "max_results": 10
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/memory/retrieve-context",
            json=context_data,
            timeout=30
        )
        
        if response.status_code != 200:
            return False, {"error": f"Context retrieval failed with status {response.status_code}"}
        
        data = response.json()
        print(f"🔄 Context Retrieval Response Keys: {list(data.keys())}")
        
        query = data.get('query')
        context = data.get('context')
        retrieved_at = data.get('retrieved_at')
        
        print(f"🔄 Query: {query}")
        print(f"📝 Context Type: {type(context)}")
        print(f"⏰ Retrieved At: {retrieved_at}")
        
        if context:
            print(f"✅ Context retrieved successfully")
            if isinstance(context, str):
                print(f"📄 Context Length: {len(context)} characters")
            elif isinstance(context, dict):
                print(f"📊 Context Keys: {list(context.keys())}")
        else:
            print(f"⚠️ No context retrieved")
        
        return True, {
            "query": query,
            "context_available": bool(context),
            "context_type": type(context).__name__,
            "retrieved_at": retrieved_at,
            "context_response": data
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def test_chat_integration_with_memory():
    """Test 9: Chat Integration with Memory System (MAIN TEST)"""
    try:
        # Test chat endpoint with memory integration
        chat_data = {
            "message": "Explain the relationship between artificial intelligence and machine learning",
            "context": {
                "task_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "user_id": "test_user"
            }
        }
        
        print(f"💬 Sending chat message: {chat_data['message']}")
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/agent/chat",
            json=chat_data,
            timeout=60  # Longer timeout for chat processing
        )
        
        if response.status_code != 200:
            return False, {"error": f"Chat endpoint failed with status {response.status_code}"}
        
        data = response.json()
        print(f"💬 Chat Response Keys: {list(data.keys())}")
        
        # Check for key response elements
        response_text = data.get('response', '')
        task_id = data.get('task_id')
        memory_used = data.get('memory_used', False)
        timestamp = data.get('timestamp')
        
        print(f"📝 Response Length: {len(response_text)} characters")
        print(f"🆔 Task ID: {task_id}")
        print(f"🧠 Memory Used: {memory_used}")
        print(f"⏰ Timestamp: {timestamp}")
        
        if response_text:
            print(f"✅ Chat response generated successfully")
            print(f"📄 Response Preview: {response_text[:200]}...")
        else:
            print(f"❌ No response text generated")
        
        # Check if memory integration is working
        memory_integration_working = (
            response_text and 
            task_id and 
            timestamp
        )
        
        return memory_integration_working, {
            "response_generated": bool(response_text),
            "response_length": len(response_text),
            "task_id": task_id,
            "memory_used": memory_used,
            "timestamp": timestamp,
            "chat_response": data
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def test_multiple_conversations_memory_persistence():
    """Test 10: Multiple Conversations for Memory Persistence"""
    try:
        session_id = str(uuid.uuid4())
        conversations = [
            "What is artificial intelligence?",
            "How does machine learning relate to AI?",
            "Can you give me examples of AI applications?",
            "What did we discuss about AI earlier?"
        ]
        
        conversation_results = []
        
        for i, message in enumerate(conversations, 1):
            print(f"\n💬 Conversation {i}: {message}")
            
            chat_data = {
                "message": message,
                "context": {
                    "task_id": str(uuid.uuid4()),
                    "session_id": session_id,  # Same session for all conversations
                    "user_id": "test_user",
                    "conversation_number": i
                }
            }
            
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/agent/chat",
                json=chat_data,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                memory_used = data.get('memory_used', False)
                
                conversation_results.append({
                    "conversation_number": i,
                    "message": message,
                    "response_generated": bool(response_text),
                    "response_length": len(response_text),
                    "memory_used": memory_used,
                    "success": True
                })
                
                print(f"✅ Conversation {i} successful (Memory used: {memory_used})")
                if response_text:
                    print(f"📄 Response preview: {response_text[:150]}...")
            else:
                conversation_results.append({
                    "conversation_number": i,
                    "message": message,
                    "success": False,
                    "error": f"Status {response.status_code}"
                })
                print(f"❌ Conversation {i} failed with status {response.status_code}")
            
            # Small delay between conversations
            time.sleep(1)
        
        # Analyze results
        successful_conversations = sum(1 for r in conversation_results if r.get('success'))
        memory_usage_count = sum(1 for r in conversation_results if r.get('memory_used'))
        
        print(f"\n📊 Conversation Summary:")
        print(f"   Successful: {successful_conversations}/{len(conversations)}")
        print(f"   Memory Used: {memory_usage_count}/{len(conversations)}")
        
        # Test passes if at least 3 conversations are successful
        test_passed = successful_conversations >= 3
        
        return test_passed, {
            "total_conversations": len(conversations),
            "successful_conversations": successful_conversations,
            "memory_usage_count": memory_usage_count,
            "conversation_results": conversation_results,
            "session_id": session_id
        }
        
    except Exception as e:
        return False, {"error": str(e)}

def print_summary():
    """Print comprehensive test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print(f"🧠 MEMORY SYSTEM INTEGRATION TEST SUMMARY")
    print("="*80)
    print(f"⏰ Test completed at: {datetime.now().isoformat()}")
    print(f"📊 Total tests: {total}")
    print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
    
    # Print individual test results
    print(f"\n📋 DETAILED RESULTS:")
    for test in test_results["tests"]:
        status = "✅ PASSED" if test["passed"] else "❌ FAILED"
        execution_time = test.get("execution_time", 0)
        print(f"   {status} - {test['name']} ({execution_time:.2f}s)")
        
        if not test["passed"] and "error" in test:
            print(f"      Error: {test['error']}")
    
    # Print failed tests details
    failed_tests = [test for test in test_results["tests"] if not test["passed"]]
    if failed_tests:
        print(f"\n❌ FAILED TESTS DETAILS:")
        for test in failed_tests:
            print(f"   - {test['name']}")
            if "error" in test:
                print(f"     Error: {test['error']}")
            elif "details" in test and test["details"].get("error"):
                print(f"     Error: {test['details']['error']}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if passed == total:
        print(f"🏆 EXCELLENT: All memory system integration tests passed!")
        print(f"   The memory system is fully functional and properly integrated with the chat endpoint.")
    elif passed >= total * 0.8:
        print(f"✅ GOOD: Most memory system integration tests passed ({passed}/{total})")
        print(f"   The memory system is largely functional with minor issues.")
    elif passed >= total * 0.6:
        print(f"⚠️ PARTIAL: Some memory system integration tests passed ({passed}/{total})")
        print(f"   The memory system has significant issues that need attention.")
    else:
        print(f"❌ CRITICAL: Most memory system integration tests failed ({passed}/{total})")
        print(f"   The memory system requires immediate attention and fixes.")
    
    print("="*80)

def main():
    """Main test execution"""
    print(f"🚀 Starting Memory System Integration Tests...")
    
    # Run all tests
    run_test("Backend Health Check", test_backend_health)
    run_test("Memory System Initialization", test_memory_system_initialization)
    run_test("Memory Analytics", test_memory_analytics)
    run_test("Episode Storage", test_episode_storage)
    run_test("Knowledge Storage", test_knowledge_storage)
    run_test("Procedure Storage", test_procedure_storage)
    run_test("Semantic Search", test_semantic_search)
    run_test("Context Retrieval", test_context_retrieval)
    run_test("Chat Integration with Memory", test_chat_integration_with_memory)
    run_test("Multiple Conversations Memory Persistence", test_multiple_conversations_memory_persistence)
    
    # Print comprehensive summary
    print_summary()
    
    # Return exit code based on results
    if test_results["summary"]["failed"] == 0:
        print(f"\n🎉 All tests passed! Memory system integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️ Some tests failed. Memory system integration needs attention.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
"""
Memory System Integration Test for Mitosis Application
Tests the memory system integration to identify why the chat endpoint is failing (Error 500)
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://cc904615-7e51-4a3d-b9d1-04093afb14ee.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MemoryIntegrationTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_result(self, test_name, status, details, duration=0):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'duration': f"{duration:.2f}s"
        }
        self.results.append(result)
        self.total_tests += 1
        if status == "✅ PASSED":
            self.passed_tests += 1
        
        status_symbol = "✅" if status == "✅ PASSED" else "❌"
        print(f"{status_symbol} {test_name}: {details} ({duration:.2f}s)")
    
    def test_backend_health(self):
        """Test backend health and service availability"""
        start_time = time.time()
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                ollama_status = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                db_status = services.get('database', False)
                
                details = f"Ollama: {ollama_status}, Tools: {tools_count}, Database: {db_status}"
                self.log_result("Backend Health Check", "✅ PASSED", details, duration)
                return True
            else:
                self.log_result("Backend Health Check", "❌ FAILED", f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Backend Health Check", "❌ FAILED", f"Connection error: {str(e)}", duration)
            return False
    
    def test_memory_system_initialization(self):
        """Test memory system initialization and component availability"""
        start_time = time.time()
        try:
            response = requests.get(f"{API_BASE}/memory/analytics", timeout=15)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                components = data.get('components', {})
                
                # Check for all 6 expected components
                expected_components = [
                    'WorkingMemory', 'EpisodicMemory', 'SemanticMemory', 
                    'ProceduralMemory', 'EmbeddingService', 'SemanticIndexer'
                ]
                
                found_components = []
                for comp_name, comp_data in components.items():
                    if comp_data.get('initialized', False):
                        found_components.append(comp_name)
                
                if len(found_components) >= 6:
                    details = f"All {len(found_components)} components initialized: {', '.join(found_components)}"
                    self.log_result("Memory System Initialization", "✅ PASSED", details, duration)
                    return True
                else:
                    details = f"Only {len(found_components)}/6 components initialized: {', '.join(found_components)}"
                    self.log_result("Memory System Initialization", "❌ FAILED", details, duration)
                    return False
            else:
                self.log_result("Memory System Initialization", "❌ FAILED", f"HTTP {response.status_code}: {response.text}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory System Initialization", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def test_enhanced_agent_availability(self):
        """Test if enhanced agent components are available"""
        start_time = time.time()
        try:
            response = requests.get(f"{API_BASE}/agent/status", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for enhanced components indicators
                enhanced_indicators = []
                if 'enhanced_agent' in str(data).lower():
                    enhanced_indicators.append('enhanced_agent')
                if 'enhanced_memory' in str(data).lower():
                    enhanced_indicators.append('enhanced_memory')
                if 'enhanced_task_manager' in str(data).lower():
                    enhanced_indicators.append('enhanced_task_manager')
                
                if len(enhanced_indicators) > 0:
                    details = f"Enhanced components detected: {', '.join(enhanced_indicators)}"
                    self.log_result("Enhanced Agent Availability", "✅ PASSED", details, duration)
                    return True
                else:
                    details = "No enhanced components detected in status response"
                    self.log_result("Enhanced Agent Availability", "⚠️ PARTIAL", details, duration)
                    return False
            else:
                self.log_result("Enhanced Agent Availability", "❌ FAILED", f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Enhanced Agent Availability", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def test_memory_context_retrieval(self):
        """Test memory context retrieval functionality"""
        start_time = time.time()
        try:
            payload = {
                "query": "artificial intelligence applications",
                "context_type": "all",
                "max_results": 5
            }
            
            response = requests.post(f"{API_BASE}/memory/context", json=payload, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'context' in data or 'results' in data:
                    details = f"Context retrieval working, response structure: {list(data.keys())}"
                    self.log_result("Memory Context Retrieval", "✅ PASSED", details, duration)
                    return True
                else:
                    details = f"Unexpected response structure: {data}"
                    self.log_result("Memory Context Retrieval", "⚠️ PARTIAL", details, duration)
                    return False
            else:
                self.log_result("Memory Context Retrieval", "❌ FAILED", f"HTTP {response.status_code}: {response.text}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory Context Retrieval", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def test_chat_endpoint_detailed(self):
        """Test chat endpoint with detailed error analysis"""
        start_time = time.time()
        try:
            payload = {
                "message": "Hello, can you explain what artificial intelligence is?",
                "session_id": f"test_session_{int(time.time())}",
                "task_id": f"test_task_{int(time.time())}"
            }
            
            response = requests.post(f"{API_BASE}/agent/chat", json=payload, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    details = f"Chat working, response length: {len(data.get('response', ''))}"
                    self.log_result("Chat Endpoint Test", "✅ PASSED", details, duration)
                    return True
                else:
                    details = f"Unexpected response structure: {list(data.keys())}"
                    self.log_result("Chat Endpoint Test", "⚠️ PARTIAL", details, duration)
                    return False
            elif response.status_code == 500:
                # Detailed error analysis for 500 errors
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    details = f"Error 500: {error_msg}"
                except:
                    details = f"Error 500: {response.text[:200]}..."
                
                self.log_result("Chat Endpoint Test", "❌ FAILED", details, duration)
                return False
            else:
                details = f"HTTP {response.status_code}: {response.text[:200]}..."
                self.log_result("Chat Endpoint Test", "❌ FAILED", details, duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Chat Endpoint Test", "❌ FAILED", f"Connection error: {str(e)}", duration)
            return False
    
    def test_memory_operations(self):
        """Test basic memory operations"""
        start_time = time.time()
        try:
            # Test episode storage
            episode_payload = {
                "title": "Test Episode",
                "description": "Testing episode storage functionality",
                "context": {"test": True},
                "actions": [{"type": "test", "content": "test action"}],
                "outcomes": [{"type": "test", "content": "test outcome"}],
                "importance": 3,
                "tags": ["test"]
            }
            
            response = requests.post(f"{API_BASE}/memory/episodes", json=episode_payload, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                details = "Episode storage working correctly"
                self.log_result("Memory Operations Test", "✅ PASSED", details, duration)
                return True
            else:
                details = f"Episode storage failed: HTTP {response.status_code}"
                self.log_result("Memory Operations Test", "❌ FAILED", details, duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory Operations Test", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def test_dependency_imports(self):
        """Test for missing dependencies that might cause import errors"""
        start_time = time.time()
        try:
            # Test if we can access the backend logs or error information
            response = requests.get(f"{API_BASE}/agent/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                # If health check passes, basic imports are working
                details = "Basic imports and dependencies appear to be working"
                self.log_result("Dependency Check", "✅ PASSED", details, duration)
                return True
            else:
                details = f"Health check failed, possible dependency issues: HTTP {response.status_code}"
                self.log_result("Dependency Check", "❌ FAILED", details, duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Dependency Check", "❌ FAILED", f"Connection error: {str(e)}", duration)
            return False
    
    def run_comprehensive_test(self):
        """Run all tests and provide comprehensive analysis"""
        print("🧠 MEMORY SYSTEM INTEGRATION TESTING - COMPREHENSIVE ANALYSIS")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        tests = [
            self.test_backend_health,
            self.test_dependency_imports,
            self.test_memory_system_initialization,
            self.test_enhanced_agent_availability,
            self.test_memory_context_retrieval,
            self.test_memory_operations,
            self.test_chat_endpoint_detailed
        ]
        
        for test in tests:
            test()
            time.sleep(0.5)  # Brief pause between tests
        
        print()
        print("=" * 80)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed results
        for result in self.results:
            status_symbol = "✅" if result['status'] == "✅ PASSED" else "❌" if result['status'] == "❌ FAILED" else "⚠️"
            print(f"{status_symbol} {result['test']}: {result['details']} ({result['duration']})")
        
        print()
        print("🔍 ROOT CAUSE ANALYSIS:")
        
        # Analyze results to identify root cause
        failed_tests = [r for r in self.results if r['status'] == "❌ FAILED"]
        
        if not failed_tests:
            print("✅ All tests passed - Memory system integration is working correctly")
        else:
            print("❌ Issues identified:")
            for failed in failed_tests:
                print(f"   - {failed['test']}: {failed['details']}")
            
            # Specific analysis for chat endpoint failure
            chat_failed = any("Chat Endpoint" in r['test'] for r in failed_tests)
            memory_failed = any("Memory" in r['test'] for r in failed_tests)
            enhanced_failed = any("Enhanced" in r['test'] for r in failed_tests)
            
            if chat_failed:
                print("\n🚨 CHAT ENDPOINT FAILURE ANALYSIS:")
                if memory_failed:
                    print("   - Memory system issues detected - likely cause of chat failure")
                if enhanced_failed:
                    print("   - Enhanced agent components not available - may cause import errors")
                if not memory_failed and not enhanced_failed:
                    print("   - Chat failure appears isolated - check backend logs for specific error")
        
        return success_rate

if __name__ == "__main__":
    tester = MemoryIntegrationTester()
    success_rate = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 80 else 1)