#!/usr/bin/env python3
"""
Specific Chat Endpoint Memory Integration Test - REVIEW REQUEST

This script tests the specific issues mentioned in the review request:
- Chat endpoint at /app/backend/src/routes/agent_routes.py lines 253-330
- Memory manager initialization status
- Enhanced agent availability
- Automatic memory usage in chat
- Error 500 identification

Focus: Investigate why the memory system is NOT working correctly in the chat endpoint.
"""

import requests
import json
import uuid
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"

print(f"🔍 SPECIFIC CHAT ENDPOINT MEMORY INTEGRATION TEST")
print(f"Backend URL: {BASE_URL}")
print(f"Test Time: {datetime.now().isoformat()}")
print("="*80)

def test_chat_endpoint_memory_integration():
    """Test the specific chat endpoint memory integration mentioned in the review"""
    
    print(f"\n🧪 TESTING CHAT ENDPOINT MEMORY INTEGRATION")
    print(f"Endpoint: {BASE_URL}{API_PREFIX}/chat")
    print(f"Lines: 253-330 in agent_routes.py")
    
    # Test data
    test_message = "Hello, I'm testing the memory integration system. Can you remember this conversation?"
    task_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    user_id = "memory_test_user"
    
    chat_data = {
        "message": test_message,
        "context": {
            "task_id": task_id,
            "session_id": session_id,
            "user_id": user_id
        }
    }
    
    print(f"Request Data: {json.dumps(chat_data, indent=2)}")
    
    try:
        # Send chat request
        response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", json=chat_data, timeout=30)
        status_code = response.status_code
        
        print(f"\n📊 RESPONSE ANALYSIS:")
        print(f"Status Code: {status_code}")
        
        if status_code == 500:
            print(f"❌ ERROR 500 DETECTED - This is the issue mentioned in the review!")
            try:
                error_data = response.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error Text: {response.text}")
            return False, {"error": "500 Internal Server Error", "details": response.text}
        
        elif status_code != 200:
            print(f"❌ Unexpected status code: {status_code}")
            try:
                error_data = response.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error Text: {response.text}")
            return False, {"error": f"Status {status_code}", "details": response.text}
        
        # Parse successful response
        try:
            response_data = response.json()
            print(f"Response Keys: {list(response_data.keys())}")
            
            # Check memory usage flag
            memory_used = response_data.get('memory_used', False)
            print(f"Memory Used: {memory_used}")
            
            # Check if enhanced processing was used
            enhanced_processing = response_data.get('enhanced_processing', False)
            print(f"Enhanced Processing: {enhanced_processing}")
            
            # Check response content
            response_text = response_data.get('response', '')
            print(f"Response Length: {len(response_text)} characters")
            print(f"Response Preview: {response_text[:200]}...")
            
            # Check task ID
            returned_task_id = response_data.get('task_id')
            print(f"Task ID Returned: {returned_task_id}")
            print(f"Task ID Matches: {returned_task_id == task_id}")
            
            # Check model used
            model = response_data.get('model', 'unknown')
            print(f"Model Used: {model}")
            
            # Check execution status
            execution_status = response_data.get('execution_status', 'unknown')
            print(f"Execution Status: {execution_status}")
            
            # Analyze if memory integration is working
            memory_integration_working = memory_used or enhanced_processing
            
            print(f"\n🧠 MEMORY INTEGRATION ANALYSIS:")
            print(f"Memory Integration Working: {memory_integration_working}")
            
            if memory_integration_working:
                print(f"✅ Memory system is being used in chat endpoint")
            else:
                print(f"❌ Memory system is NOT being used in chat endpoint")
                print(f"   This could be the issue mentioned in the review!")
            
            return memory_integration_working, {
                "status_code": status_code,
                "memory_used": memory_used,
                "enhanced_processing": enhanced_processing,
                "response_length": len(response_text),
                "task_id_matches": returned_task_id == task_id,
                "model": model,
                "execution_status": execution_status,
                "memory_integration_working": memory_integration_working
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Decode Error: {e}")
            print(f"Raw Response: {response.text}")
            return False, {"error": "Invalid JSON response", "raw_response": response.text}
            
    except Exception as e:
        print(f"❌ Request Exception: {e}")
        return False, {"error": str(e)}

def test_memory_manager_status():
    """Test if memory_manager.is_initialized is True"""
    
    print(f"\n🧪 TESTING MEMORY MANAGER STATUS")
    print(f"Checking if memory_manager.is_initialized is True")
    
    try:
        # Check memory analytics to see initialization status
        response = requests.get(f"{BASE_URL}/api/memory/analytics", timeout=10)
        status_code = response.status_code
        
        print(f"Memory Analytics Status: {status_code}")
        
        if status_code != 200:
            print(f"❌ Memory analytics endpoint failed: {status_code}")
            return False, {"error": f"Status {status_code}"}
        
        data = response.json()
        system_info = data.get('system_info', {})
        is_initialized = system_info.get('initialized', False)
        
        print(f"Memory Manager Initialized: {is_initialized}")
        
        if is_initialized:
            print(f"✅ memory_manager.is_initialized is True")
        else:
            print(f"❌ memory_manager.is_initialized is False - This is the issue!")
        
        return is_initialized, {
            "initialized": is_initialized,
            "system_info": system_info
        }
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, {"error": str(e)}

def test_enhanced_agent_availability():
    """Test if enhanced_agent is available in current_app.enhanced_agent"""
    
    print(f"\n🧪 TESTING ENHANCED AGENT AVAILABILITY")
    print(f"Checking if enhanced_agent is available in current_app.enhanced_agent")
    
    try:
        # Check agent health to see enhanced components
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health", timeout=10)
        status_code = response.status_code
        
        print(f"Agent Health Status: {status_code}")
        
        if status_code != 200:
            print(f"❌ Agent health endpoint failed: {status_code}")
            return False, {"error": f"Status {status_code}"}
        
        data = response.json()
        services = data.get('services', {})
        
        # Look for orchestration service (indicates enhanced components)
        orchestration = services.get('orchestration', {})
        enhanced_available = bool(orchestration)
        
        print(f"Enhanced Components Available: {enhanced_available}")
        
        if enhanced_available:
            print(f"✅ Enhanced agent components are available")
            print(f"   Active Tasks: {orchestration.get('active_tasks', 0)}")
            print(f"   Total Tasks: {orchestration.get('total_tasks', 0)}")
            print(f"   Success Rate: {orchestration.get('success_rate', 0):.2f}")
        else:
            print(f"❌ Enhanced agent components are NOT available")
            print(f"   This could explain why memory integration is failing!")
        
        return enhanced_available, {
            "enhanced_available": enhanced_available,
            "orchestration": orchestration,
            "services": services
        }
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, {"error": str(e)}

def test_multiple_chat_conversations():
    """Test multiple conversations to see if memory persists"""
    
    print(f"\n🧪 TESTING MULTIPLE CHAT CONVERSATIONS FOR MEMORY PERSISTENCE")
    
    session_id = str(uuid.uuid4())
    user_id = "memory_persistence_test"
    
    conversations = [
        "My name is Alice and I work as a data scientist.",
        "I'm working on a machine learning project about image recognition.",
        "What do you remember about my work?",
        "Can you recall my name and profession?"
    ]
    
    results = []
    
    for i, message in enumerate(conversations, 1):
        print(f"\n💬 Conversation {i}: {message}")
        
        chat_data = {
            "message": message,
            "context": {
                "task_id": str(uuid.uuid4()),
                "session_id": session_id,
                "user_id": user_id
            }
        }
        
        try:
            response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", json=chat_data, timeout=30)
            status_code = response.status_code
            
            if status_code == 200:
                response_data = response.json()
                memory_used = response_data.get('memory_used', False)
                response_text = response_data.get('response', '')
                
                print(f"   Status: ✅ Success")
                print(f"   Memory Used: {memory_used}")
                print(f"   Response Preview: {response_text[:100]}...")
                
                # For the last two conversations, check if context is remembered
                if i >= 3:
                    context_indicators = ['Alice', 'data scientist', 'machine learning', 'image recognition']
                    context_found = any(indicator.lower() in response_text.lower() for indicator in context_indicators)
                    print(f"   Context Found: {context_found}")
                    results.append({
                        "conversation": i,
                        "memory_used": memory_used,
                        "context_found": context_found if i >= 3 else None
                    })
                else:
                    results.append({
                        "conversation": i,
                        "memory_used": memory_used,
                        "context_found": None
                    })
                    
            else:
                print(f"   Status: ❌ Failed ({status_code})")
                results.append({
                    "conversation": i,
                    "error": f"Status {status_code}"
                })
                
        except Exception as e:
            print(f"   Status: ❌ Exception ({e})")
            results.append({
                "conversation": i,
                "error": str(e)
            })
        
        time.sleep(1)  # Brief pause between conversations
    
    # Analyze results
    successful_conversations = [r for r in results if 'error' not in r]
    memory_used_count = sum(1 for r in successful_conversations if r.get('memory_used', False))
    context_found_count = sum(1 for r in successful_conversations if r.get('context_found', False))
    
    print(f"\n📊 CONVERSATION ANALYSIS:")
    print(f"Successful Conversations: {len(successful_conversations)}/{len(conversations)}")
    print(f"Memory Used: {memory_used_count}/{len(successful_conversations)}")
    print(f"Context Found: {context_found_count}/2 (last 2 conversations)")
    
    memory_persistence_working = memory_used_count > 0 and context_found_count > 0
    
    if memory_persistence_working:
        print(f"✅ Memory persistence is working across conversations")
    else:
        print(f"❌ Memory persistence is NOT working across conversations")
        print(f"   This indicates the memory integration issue mentioned in the review!")
    
    return memory_persistence_working, {
        "successful_conversations": len(successful_conversations),
        "total_conversations": len(conversations),
        "memory_used_count": memory_used_count,
        "context_found_count": context_found_count,
        "memory_persistence_working": memory_persistence_working,
        "results": results
    }

def main():
    """Main test execution"""
    
    print("🚀 Starting Specific Chat Endpoint Memory Integration Tests...")
    
    # Run tests
    tests = [
        ("Memory Manager Status", test_memory_manager_status),
        ("Enhanced Agent Availability", test_enhanced_agent_availability),
        ("Chat Endpoint Memory Integration", test_chat_endpoint_memory_integration),
        ("Multiple Chat Conversations", test_multiple_chat_conversations)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"🧪 {test_name}")
        print(f"{'='*80}")
        
        try:
            start_time = time.time()
            passed, details = test_func()
            end_time = time.time()
            execution_time = end_time - start_time
            
            results[test_name] = {
                "passed": passed,
                "execution_time": f"{execution_time:.2f}s",
                "details": details
            }
            
            if passed:
                print(f"\n✅ RESULT: PASSED ({execution_time:.2f}s)")
            else:
                print(f"\n❌ RESULT: FAILED ({execution_time:.2f}s)")
                
        except Exception as e:
            results[test_name] = {
                "passed": False,
                "error": str(e),
                "execution_time": "N/A"
            }
            print(f"\n❌ RESULT: FAILED (Exception: {e})")
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"🔍 SPECIFIC CHAT ENDPOINT MEMORY INTEGRATION TEST SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r.get("passed", False))
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result.get("passed", False) else "❌ FAILED"
        execution_time = result.get("execution_time", "N/A")
        print(f"   {status} - {test_name} ({execution_time})")
        
        if not result.get("passed", False):
            if "error" in result:
                print(f"      Error: {result['error']}")
            elif "details" in result and isinstance(result["details"], dict) and "error" in result["details"]:
                print(f"      Error: {result['details']['error']}")
    
    # Root cause analysis
    print(f"\n🔍 ROOT CAUSE ANALYSIS:")
    
    memory_manager_working = results.get("Memory Manager Status", {}).get("passed", False)
    enhanced_agent_available = results.get("Enhanced Agent Availability", {}).get("passed", False)
    chat_integration_working = results.get("Chat Endpoint Memory Integration", {}).get("passed", False)
    memory_persistence_working = results.get("Multiple Chat Conversations", {}).get("passed", False)
    
    if memory_manager_working and enhanced_agent_available and chat_integration_working and memory_persistence_working:
        print(f"✅ CONCLUSION: Memory system is working correctly in the chat endpoint")
        print(f"   The issue mentioned in the review may have been resolved.")
    else:
        print(f"❌ CONCLUSION: Memory system has issues in the chat endpoint")
        print(f"   Issues identified:")
        
        if not memory_manager_working:
            print(f"   - Memory manager is not properly initialized")
        if not enhanced_agent_available:
            print(f"   - Enhanced agent components are not available")
        if not chat_integration_working:
            print(f"   - Chat endpoint is not using memory integration")
        if not memory_persistence_working:
            print(f"   - Memory persistence across conversations is not working")
    
    print(f"{'='*80}")

if __name__ == "__main__":
    main()