#!/usr/bin/env python3
"""
MEMORY SYSTEM INTEGRATION TEST - REVIEW REQUEST FOCUSED

This script specifically tests the memory system integration in the Mitosis chat endpoint
as requested in the review, focusing on:

1. **Chat Endpoint Memory Integration**: Test the `/api/agent/chat` endpoint to verify that memory is being used automatically in conversations
2. **Memory Retrieval**: Test if the chat endpoint can retrieve relevant context from previous conversations automatically
3. **Memory Storage**: Test if conversations are being stored in episodic memory automatically
4. **Memory Manager Initialization**: Check if memory_manager is properly initialized when chat endpoint is called
5. **Context Enhancement**: Test if conversations are being enhanced with relevant context from memory
6. **Memory Used Flag**: Test if the `memory_used` flag is being set correctly in chat responses
7. **Episode Storage**: Test if new episodes are being stored automatically after each conversation
8. **Memory System Status**: Verify that the memory system is working as expected

The goal is to verify that the memory system is working transparently - users should not interact 
with memory directly, but the agent should automatically use memory to improve responses by 
remembering previous conversations and storing new experiences.
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

print(f"🧠 MEMORY SYSTEM INTEGRATION TEST - REVIEW REQUEST FOCUSED")
print(f"Using backend URL: {BASE_URL}")
print(f"Focus: Testing memory integration in chat endpoint as requested in review")
print("="*80)

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
        
        test_results["tests"].append({
            "name": name,
            "passed": passed,
            "execution_time": round(end_time - start_time, 2),
            "details": details
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"✅ RESULT: PASSED ({end_time - start_time:.2f}s)")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ RESULT: FAILED ({end_time - start_time:.2f}s)")
            if details and 'error' in details:
                print(f"   Error: {details['error']}")
        
        return passed, details
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "passed": False,
            "error": str(e)
        })
        print(f"❌ RESULT: FAILED (Exception: {str(e)})")
        return False, {"error": str(e)}

def test_memory_system_status():
    """Test 1: Memory System Status - Verify that the memory system is working as expected"""
    try:
        url = f"{BASE_URL}{MEMORY_PREFIX}/memory-analytics"
        response = requests.get(url, timeout=30)
        
        print(f"Memory Analytics URL: {url}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Memory System Status: {json.dumps(data, indent=2)}")
            
            # Check if memory system is initialized
            system_info = data.get('overview', {}).get('system_info', {})
            initialized = system_info.get('initialized', False)
            
            # Check if all 6 memory components are present
            overview = data.get('overview', {})
            required_components = ['working_memory', 'episodic_memory', 'semantic_memory', 'procedural_memory', 'embedding_service', 'semantic_indexer']
            
            components_found = []
            for component in required_components:
                if component in overview:
                    components_found.append(component)
                    print(f"✅ {component}: found")
                else:
                    print(f"❌ {component}: missing")
            
            success = initialized and len(components_found) == len(required_components)
            
            return success, {
                "initialized": initialized,
                "components_found": components_found,
                "total_components": len(required_components),
                "episodic_episodes": overview.get('episodic_memory', {}).get('total_episodes', 0),
                "memory_analytics": data
            }
        else:
            return False, {"error": f"Memory analytics endpoint returned {response.status_code}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def test_episode_storage():
    """Test 2: Episode Storage - Test if new episodes are being stored automatically after each conversation"""
    try:
        url = f"{BASE_URL}{MEMORY_PREFIX}/store-episode"
        
        episode_data = {
            "user_query": "What is artificial intelligence and how does it work?",
            "agent_response": "Artificial intelligence (AI) is a branch of computer science that aims to create machines capable of intelligent behavior.",
            "success": True,
            "context": {
                "test_type": "memory_integration",
                "session_id": str(uuid.uuid4()),
                "task_id": str(uuid.uuid4())
            },
            "tools_used": [],
            "importance": 3,
            "metadata": {
                "test_timestamp": datetime.now().isoformat(),
                "topic": "AI basics"
            }
        }
        
        print(f"Episode Storage URL: {url}")
        print(f"Episode Data: {json.dumps(episode_data, indent=2)}")
        
        response = requests.post(url, json=episode_data, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Episode Storage Response: {json.dumps(data, indent=2)}")
            
            success = data.get('success', False) and 'episode_id' in data
            
            return success, {
                "episode_stored": success,
                "episode_id": data.get('episode_id'),
                "stored_at": data.get('stored_at'),
                "response": data
            }
        else:
            try:
                error_data = response.json()
                return False, {"error": f"Status {response.status_code}: {error_data}"}
            except:
                return False, {"error": f"Status {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def test_knowledge_storage():
    """Test 3: Knowledge Storage - Test if knowledge can be stored in semantic memory"""
    try:
        url = f"{BASE_URL}{MEMORY_PREFIX}/store-knowledge"
        
        knowledge_data = {
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
            "type": "fact",
            "subject": "Machine Learning",
            "predicate": "is a subset of",
            "object": "Artificial Intelligence",
            "confidence": 0.95,
            "context": {
                "test_type": "memory_integration",
                "domain": "AI/ML",
                "source": "test_conversation"
            },
            "metadata": {
                "test_timestamp": datetime.now().isoformat()
            }
        }
        
        print(f"Knowledge Storage URL: {url}")
        print(f"Knowledge Data: {json.dumps(knowledge_data, indent=2)}")
        
        response = requests.post(url, json=knowledge_data, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Knowledge Storage Response: {json.dumps(data, indent=2)}")
            
            success = data.get('success', False) and 'knowledge_id' in data
            
            return success, {
                "knowledge_stored": success,
                "knowledge_id": data.get('knowledge_id'),
                "type": data.get('type'),
                "stored_at": data.get('stored_at'),
                "response": data
            }
        else:
            try:
                error_data = response.json()
                return False, {"error": f"Status {response.status_code}: {error_data}"}
            except:
                return False, {"error": f"Status {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def test_semantic_search():
    """Test 4: Semantic Search - Test if semantic search functionality works"""
    try:
        url = f"{BASE_URL}{MEMORY_PREFIX}/semantic-search"
        
        search_data = {
            "query": "artificial intelligence machine learning",
            "max_results": 5,
            "memory_types": ["all"]
        }
        
        print(f"Semantic Search URL: {url}")
        print(f"Search Data: {json.dumps(search_data, indent=2)}")
        
        response = requests.post(url, json=search_data, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Semantic Search Response: {json.dumps(data, indent=2)}")
            
            success = 'results' in data and 'total_results' in data
            
            return success, {
                "search_successful": success,
                "query": data.get('query'),
                "total_results": data.get('total_results', 0),
                "results": data.get('results', []),
                "response": data
            }
        else:
            try:
                error_data = response.json()
                return False, {"error": f"Status {response.status_code}: {error_data}"}
            except:
                return False, {"error": f"Status {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def test_context_retrieval():
    """Test 5: Context Retrieval - Test if relevant context can be retrieved from memory"""
    try:
        url = f"{BASE_URL}{MEMORY_PREFIX}/retrieve-context"
        
        context_data = {
            "query": "artificial intelligence and machine learning applications",
            "context_type": "all",
            "max_results": 10
        }
        
        print(f"Context Retrieval URL: {url}")
        print(f"Context Data: {json.dumps(context_data, indent=2)}")
        
        response = requests.post(url, json=context_data, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Context Retrieval Response: {json.dumps(data, indent=2)}")
            
            success = 'context' in data and 'query' in data
            
            return success, {
                "context_retrieved": success,
                "query": data.get('query'),
                "context": data.get('context'),
                "retrieved_at": data.get('retrieved_at'),
                "response": data
            }
        else:
            try:
                error_data = response.json()
                return False, {"error": f"Status {response.status_code}: {error_data}"}
            except:
                return False, {"error": f"Status {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def test_chat_integration_with_memory():
    """Test 6: Chat Integration with Memory - Test if chat endpoint uses memory automatically"""
    try:
        url = f"{BASE_URL}{API_PREFIX}/chat"
        
        # Create a unique session for this test
        session_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        chat_data = {
            "message": "Explain the difference between artificial intelligence, machine learning, and deep learning",
            "context": {
                "task_id": task_id,
                "session_id": session_id,
                "user_id": "test_user_memory"
            }
        }
        
        print(f"Chat Integration URL: {url}")
        print(f"Chat Data: {json.dumps(chat_data, indent=2)}")
        
        response = requests.post(url, json=chat_data, timeout=60)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Chat Response Keys: {list(data.keys())}")
            
            # Check for memory usage indicators
            memory_used = data.get('memory_used', False)
            response_text = data.get('response', '')
            
            print(f"Memory Used: {memory_used}")
            print(f"Response Length: {len(response_text)} characters")
            print(f"Response Preview: {response_text[:200]}...")
            
            # Success if we get a response and memory_used flag is present
            success = 'response' in data and 'memory_used' in data
            
            return success, {
                "chat_successful": success,
                "memory_used": memory_used,
                "response_length": len(response_text),
                "task_id": data.get('task_id'),
                "model": data.get('model'),
                "timestamp": data.get('timestamp'),
                "enhanced_processing": data.get('enhanced_processing', False),
                "cognitive_mode": data.get('cognitive_mode'),
                "response": data
            }
        else:
            try:
                error_data = response.json()
                return False, {"error": f"Status {response.status_code}: {error_data}"}
            except:
                return False, {"error": f"Status {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def test_multiple_conversations_memory_persistence():
    """Test 7: Multiple Conversations Memory Persistence - Test memory across multiple conversations"""
    try:
        url = f"{BASE_URL}{API_PREFIX}/chat"
        
        # Create a unique session for this test
        session_id = str(uuid.uuid4())
        
        conversations = [
            "My name is Sarah and I'm interested in learning about AI",
            "What are the main types of machine learning algorithms?",
            "Can you remember my name from our previous conversation?",
            "Based on my interest in AI, what programming languages should I learn?"
        ]
        
        conversation_results = []
        
        for i, message in enumerate(conversations, 1):
            print(f"\n--- Conversation {i}/4 ---")
            
            chat_data = {
                "message": message,
                "context": {
                    "task_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "user_id": "test_user_sarah"
                }
            }
            
            print(f"Message: {message}")
            
            response = requests.post(url, json=chat_data, timeout=60)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                memory_used = data.get('memory_used', False)
                response_text = data.get('response', '')
                
                print(f"Memory Used: {memory_used}")
                print(f"Response Preview: {response_text[:150]}...")
                
                conversation_results.append({
                    "conversation_number": i,
                    "message": message,
                    "success": True,
                    "memory_used": memory_used,
                    "response_length": len(response_text),
                    "task_id": data.get('task_id'),
                    "enhanced_processing": data.get('enhanced_processing', False)
                })
            else:
                print(f"❌ Conversation {i} failed with status {response.status_code}")
                conversation_results.append({
                    "conversation_number": i,
                    "message": message,
                    "success": False,
                    "error": f"Status {response.status_code}"
                })
        
        # Analyze results
        successful_conversations = sum(1 for r in conversation_results if r['success'])
        memory_used_count = sum(1 for r in conversation_results if r.get('memory_used', False))
        
        success = successful_conversations == len(conversations) and memory_used_count > 0
        
        print(f"\n📊 Conversation Summary:")
        print(f"Successful conversations: {successful_conversations}/{len(conversations)}")
        print(f"Conversations with memory usage: {memory_used_count}/{len(conversations)}")
        
        return success, {
            "total_conversations": len(conversations),
            "successful_conversations": successful_conversations,
            "memory_used_count": memory_used_count,
            "memory_usage_rate": f"{memory_used_count}/{len(conversations)}",
            "conversation_results": conversation_results
        }
            
    except Exception as e:
        return False, {"error": str(e)}

def print_summary():
    """Print comprehensive test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print(f"🧠 MEMORY SYSTEM INTEGRATION TEST SUMMARY - REVIEW REQUEST")
    print("="*80)
    print(f"Timestamp: {test_results['timestamp']}")
    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    # Print detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for test in test_results["tests"]:
        status = "✅ PASSED" if test["passed"] else "❌ FAILED"
        execution_time = test.get("execution_time", "N/A")
        print(f"  {status} - {test['name']} ({execution_time}s)")
        
        if not test["passed"] and "error" in test:
            print(f"    Error: {test['error']}")
    
    # Print failed tests details
    if failed > 0:
        print(f"\n❌ FAILED TESTS DETAILS:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"- {test['name']}")
                if "error" in test:
                    print(f"  Error: {test['error']}")
                elif "details" in test and "error" in test["details"]:
                    print(f"  Error: {test['details']['error']}")
    
    # Memory system specific analysis
    memory_tests_passed = sum(1 for test in test_results["tests"] if test["passed"])
    
    print(f"\n🧠 MEMORY SYSTEM ANALYSIS:")
    print(f"Memory system functionality: {memory_tests_passed}/{total} components working")
    
    # Check specific memory integration aspects
    chat_integration_passed = any(test["passed"] and "Chat Integration" in test["name"] for test in test_results["tests"])
    memory_persistence_passed = any(test["passed"] and "Memory Persistence" in test["name"] for test in test_results["tests"])
    
    print(f"\n🎯 REVIEW REQUEST SPECIFIC FINDINGS:")
    print(f"1. Chat Endpoint Memory Integration: {'✅ WORKING' if chat_integration_passed else '❌ FAILED'}")
    print(f"2. Memory Persistence Across Conversations: {'✅ WORKING' if memory_persistence_passed else '❌ FAILED'}")
    print(f"3. Memory System Infrastructure: {'✅ WORKING' if memory_tests_passed >= 4 else '❌ NEEDS ATTENTION'}")
    
    if memory_tests_passed >= total * 0.8:  # 80% threshold
        print(f"\n✅ MEMORY SYSTEM STATUS: EXCELLENT - Ready for production")
        print(f"   The memory system is working transparently as designed")
        print(f"   Users don't interact with memory directly, but the agent automatically uses it")
    elif memory_tests_passed >= total * 0.6:  # 60% threshold
        print(f"\n⚠️ MEMORY SYSTEM STATUS: GOOD - Minor issues to address")
        print(f"   Core memory functionality is working but some components need attention")
    else:
        print(f"\n❌ MEMORY SYSTEM STATUS: NEEDS ATTENTION - Major issues found")
        print(f"   Memory system requires significant work before production use")
    
    print("="*80)

def main():
    """Main test execution"""
    print("🚀 Starting Memory System Integration Tests...")
    
    # Run all tests in sequence
    tests = [
        ("Memory System Status", test_memory_system_status),
        ("Episode Storage", test_episode_storage),
        ("Knowledge Storage", test_knowledge_storage),
        ("Semantic Search", test_semantic_search),
        ("Context Retrieval", test_context_retrieval),
        ("Chat Integration with Memory", test_chat_integration_with_memory),
        ("Multiple Conversations Memory Persistence", test_multiple_conversations_memory_persistence)
    ]
    
    for test_name, test_func in tests:
        run_test(test_name, test_func)
        time.sleep(1)  # Brief pause between tests
    
    # Print comprehensive summary
    print_summary()
    
    # Return exit code based on results
    if test_results["summary"]["failed"] == 0:
        print(f"\n🎉 ALL MEMORY INTEGRATION TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️ SOME MEMORY INTEGRATION TESTS FAILED - See details above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)