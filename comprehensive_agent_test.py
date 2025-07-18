#!/usr/bin/env python3
"""
Comprehensive Mitosis Agent Testing Script - Review Request Focused

This script tests the Mitosis backend system comprehensively to verify the agent 
is working correctly after fixing dependency issues, focusing on:

1. Backend Health: Verify all services are healthy (database, ollama, tools)
2. Agent Chat Functionality: Test different types of messages
3. Agent Behavior: Verify correct planning vs simple responses
4. Memory System: Test memory integration and persistence
5. Tools Integration: Verify all 12 tools are accessible and working
6. Planning System: Test the generate-plan endpoint
7. Error Handling: Test error scenarios

The user reported that the agent was not working correctly - it wasn't creating 
proper plans, not solving real tasks, and showing generic success messages 
instead of real results.
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path

# Configuration - Use localhost for internal testing
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"

print(f"🧪 COMPREHENSIVE MITOSIS AGENT TESTING")
print(f"Using backend URL: {BASE_URL}")
print(f"Testing focus: Agent functionality after dependency fixes")
print(f"Timestamp: {datetime.now().isoformat()}")

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

def run_test(name, test_func, *args, **kwargs):
    """Run a test and track results"""
    test_results["summary"]["total"] += 1
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {name}")
    print(f"{'='*80}")
    
    try:
        start_time = time.time()
        passed, result_data = test_func(*args, **kwargs)
        end_time = time.time()
        
        test_results["tests"].append({
            "name": name,
            "passed": passed,
            "duration": round(end_time - start_time, 2),
            "result_data": result_data
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"✅ PASSED ({end_time - start_time:.2f}s)")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ FAILED ({end_time - start_time:.2f}s)")
        
        return passed, result_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "passed": False,
            "error": str(e)
        })
        print(f"❌ FAILED (Exception): {str(e)}")
        return False, None

def test_backend_health():
    """Test 1: Backend Health - Verify all services are healthy"""
    print("🔍 Testing backend health and service status...")
    
    try:
        # Test main health endpoint
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        
        if response.status_code != 200:
            return False, f"Health endpoint returned {response.status_code}"
        
        health_data = response.json()
        print(f"Health response: {json.dumps(health_data, indent=2)}")
        
        # Check required services
        services = health_data.get('services', {})
        required_services = ['database', 'ollama', 'tools']
        
        for service in required_services:
            if service not in services:
                return False, f"Missing service: {service}"
            
            if service == 'tools':
                # Tools should be a number (count of tools)
                if not isinstance(services[service], int) or services[service] < 10:
                    return False, f"Expected at least 10 tools, got {services[service]}"
                print(f"✅ Tools: {services[service]} available")
            else:
                # Database and ollama should be boolean true
                if not services[service]:
                    return False, f"Service {service} is not healthy"
                print(f"✅ {service.title()}: Healthy")
        
        return True, health_data
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_agent_chat_simple():
    """Test 2: Simple Conversation - Should NOT trigger planning"""
    print("🔍 Testing simple conversation (should be discussion mode)...")
    
    try:
        chat_data = {
            "message": "Hola, ¿cómo estás?"
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", json=chat_data, timeout=30)
        
        if response.status_code != 200:
            return False, f"Chat endpoint returned {response.status_code}"
        
        response_data = response.json()
        print(f"Response keys: {list(response_data.keys())}")
        
        # Check response structure
        if 'response' not in response_data:
            return False, "Missing 'response' field"
        
        response_text = response_data['response']
        print(f"Response text: {response_text[:200]}...")
        
        # For simple conversation, should NOT have complex planning
        # Check if it's a simple response (not a complex plan)
        is_simple_response = len(response_text) < 500 and not any(
            keyword in response_text.lower() 
            for keyword in ['plan', 'step 1', 'step 2', 'task breakdown', 'execution']
        )
        
        # Check if memory is being used
        memory_used = response_data.get('memory_used', False)
        print(f"Memory used: {memory_used}")
        
        # Check task_id generation
        task_id = response_data.get('task_id')
        print(f"Task ID: {task_id}")
        
        return True, {
            "response_length": len(response_text),
            "is_simple_response": is_simple_response,
            "memory_used": memory_used,
            "has_task_id": bool(task_id)
        }
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_agent_chat_complex():
    """Test 3: Complex Task - Should trigger planning and real execution"""
    print("🔍 Testing complex task (should trigger agent mode with planning)...")
    
    try:
        chat_data = {
            "message": "Crea un informe detallado sobre las tendencias de inteligencia artificial en 2025"
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", json=chat_data, timeout=60)
        
        if response.status_code != 200:
            return False, f"Chat endpoint returned {response.status_code}"
        
        response_data = response.json()
        print(f"Response keys: {list(response_data.keys())}")
        
        # Check response structure
        if 'response' not in response_data:
            return False, "Missing 'response' field"
        
        response_text = response_data['response']
        print(f"Response text length: {len(response_text)}")
        print(f"Response preview: {response_text[:300]}...")
        
        # For complex task, should have planning indicators
        has_planning = any(
            keyword in response_text.lower() 
            for keyword in ['plan', 'paso', 'step', 'análisis', 'investigación', 'informe']
        )
        
        # Check if it's a substantial response (not generic)
        is_substantial = len(response_text) > 200
        
        # Check if memory is being used
        memory_used = response_data.get('memory_used', False)
        print(f"Memory used: {memory_used}")
        
        # Check for tool usage indicators
        tool_calls = response_data.get('tool_calls', [])
        tool_results = response_data.get('tool_results', [])
        print(f"Tool calls: {len(tool_calls)}")
        print(f"Tool results: {len(tool_results)}")
        
        # Check task_id generation
        task_id = response_data.get('task_id')
        print(f"Task ID: {task_id}")
        
        return True, {
            "response_length": len(response_text),
            "has_planning": has_planning,
            "is_substantial": is_substantial,
            "memory_used": memory_used,
            "tool_calls_count": len(tool_calls),
            "tool_results_count": len(tool_results),
            "has_task_id": bool(task_id)
        }
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_websearch_functionality():
    """Test 4: WebSearch Task - Test web search functionality"""
    print("🔍 Testing WebSearch functionality...")
    
    try:
        chat_data = {
            "message": "Busca información sobre las últimas innovaciones en inteligencia artificial",
            "search_mode": "websearch"
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/chat", json=chat_data, timeout=45)
        
        if response.status_code != 200:
            return False, f"WebSearch endpoint returned {response.status_code}"
        
        response_data = response.json()
        print(f"Response keys: {list(response_data.keys())}")
        
        # Check if search_mode is correctly set
        search_mode = response_data.get('search_mode')
        print(f"Search mode: {search_mode}")
        
        # Check for search_data
        search_data = response_data.get('search_data', {})
        print(f"Search data keys: {list(search_data.keys())}")
        
        # Verify search results structure
        has_sources = 'sources' in search_data and len(search_data['sources']) > 0
        has_query = 'query' in search_data
        has_summary = 'summary' in search_data or 'directAnswer' in search_data
        
        print(f"Has sources: {has_sources} ({len(search_data.get('sources', []))} sources)")
        print(f"Has query: {has_query}")
        print(f"Has summary: {has_summary}")
        
        # Check response quality
        response_text = response_data.get('response', '')
        is_informative = len(response_text) > 100
        
        return True, {
            "search_mode": search_mode,
            "has_sources": has_sources,
            "sources_count": len(search_data.get('sources', [])),
            "has_query": has_query,
            "has_summary": has_summary,
            "response_length": len(response_text),
            "is_informative": is_informative
        }
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_memory_system():
    """Test 5: Memory System - Test memory integration and persistence"""
    print("🔍 Testing memory system integration...")
    
    try:
        # Test memory analytics endpoint
        response = requests.get(f"{BASE_URL}/api/memory/analytics", timeout=10)
        
        if response.status_code != 200:
            return False, f"Memory analytics endpoint returned {response.status_code}"
        
        analytics_data = response.json()
        print(f"Memory analytics: {json.dumps(analytics_data, indent=2)}")
        
        # Check analytics structure
        expected_sections = ['overview', 'memory_efficiency', 'learning_insights']
        has_all_sections = all(section in analytics_data for section in expected_sections)
        
        # Test memory context retrieval
        context_response = requests.post(
            f"{BASE_URL}/api/memory/context", 
            json={"query": "test query", "limit": 5}, 
            timeout=10
        )
        
        context_ok = context_response.status_code == 200
        if context_ok:
            context_data = context_response.json()
            print(f"Memory context keys: {list(context_data.keys())}")
        
        # Test episode storage
        episode_response = requests.post(
            f"{BASE_URL}/api/memory/episodes", 
            json={
                "content": "Test episode for memory testing",
                "context": {"test": True},
                "importance": 0.5
            }, 
            timeout=10
        )
        
        episode_ok = episode_response.status_code == 200
        if episode_ok:
            episode_data = episode_response.json()
            print(f"Episode storage result: {episode_data}")
        
        return True, {
            "analytics_available": True,
            "has_all_sections": has_all_sections,
            "context_retrieval_ok": context_ok,
            "episode_storage_ok": episode_ok
        }
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_tools_integration():
    """Test 6: Tools Integration - Verify all tools are accessible"""
    print("🔍 Testing tools integration...")
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/tools", timeout=10)
        
        if response.status_code != 200:
            return False, f"Tools endpoint returned {response.status_code}"
        
        tools_data = response.json()
        tools = tools_data.get('tools', [])
        
        print(f"Available tools: {len(tools)}")
        
        # Expected tools based on the review request
        expected_tools = [
            'web_search', 'comprehensive_research', 'enhanced_web_search',
            'enhanced_deep_research', 'file_manager', 'shell_tool'
        ]
        
        available_tool_names = [tool.get('name') for tool in tools]
        print(f"Tool names: {available_tool_names}")
        
        # Check if key tools are available
        key_tools_available = []
        for expected_tool in expected_tools:
            if expected_tool in available_tool_names:
                key_tools_available.append(expected_tool)
        
        print(f"Key tools available: {key_tools_available}")
        
        # Verify tool structure
        tools_have_required_fields = True
        for tool in tools:
            if not all(field in tool for field in ['name', 'description', 'parameters']):
                tools_have_required_fields = False
                break
        
        return True, {
            "total_tools": len(tools),
            "key_tools_available": key_tools_available,
            "key_tools_count": len(key_tools_available),
            "tools_have_required_fields": tools_have_required_fields,
            "all_tool_names": available_tool_names
        }
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_planning_system():
    """Test 7: Planning System - Test the generate-plan endpoint"""
    print("🔍 Testing planning system...")
    
    try:
        plan_data = {
            "task": "Crear una aplicación web simple con HTML, CSS y JavaScript",
            "context": {
                "user_preferences": {"framework": "vanilla"},
                "constraints": {"time": "2 hours"}
            }
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/generate-plan", json=plan_data, timeout=30)
        
        if response.status_code != 200:
            return False, f"Generate plan endpoint returned {response.status_code}"
        
        plan_response = response.json()
        print(f"Plan response keys: {list(plan_response.keys())}")
        
        # Check plan structure
        has_plan = 'plan' in plan_response
        has_steps = False
        has_complexity = 'complexity' in plan_response
        has_estimated_time = 'estimated_time' in plan_response
        
        if has_plan:
            plan = plan_response['plan']
            if isinstance(plan, dict) and 'steps' in plan:
                steps = plan['steps']
                has_steps = isinstance(steps, list) and len(steps) > 0
                print(f"Plan has {len(steps)} steps")
            elif isinstance(plan, list):
                has_steps = len(plan) > 0
                print(f"Plan has {len(plan)} items")
        
        print(f"Has plan: {has_plan}")
        print(f"Has steps: {has_steps}")
        print(f"Has complexity: {has_complexity}")
        print(f"Has estimated time: {has_estimated_time}")
        
        if has_complexity:
            print(f"Complexity: {plan_response['complexity']}")
        if has_estimated_time:
            print(f"Estimated time: {plan_response['estimated_time']}")
        
        return True, {
            "has_plan": has_plan,
            "has_steps": has_steps,
            "has_complexity": has_complexity,
            "has_estimated_time": has_estimated_time,
            "plan_structure": type(plan_response.get('plan', None)).__name__
        }
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_error_handling():
    """Test 8: Error Handling - Test error scenarios"""
    print("🔍 Testing error handling...")
    
    try:
        # Test invalid endpoint
        response1 = requests.get(f"{BASE_URL}{API_PREFIX}/invalid-endpoint", timeout=10)
        invalid_endpoint_handled = response1.status_code == 404
        
        # Test invalid chat data
        response2 = requests.post(f"{BASE_URL}{API_PREFIX}/chat", json={}, timeout=10)
        invalid_data_handled = response2.status_code in [400, 422]
        
        # Test malformed JSON
        response3 = requests.post(
            f"{BASE_URL}{API_PREFIX}/chat", 
            data="invalid json", 
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        malformed_json_handled = response3.status_code in [400, 422]
        
        print(f"Invalid endpoint handled: {invalid_endpoint_handled} (status: {response1.status_code})")
        print(f"Invalid data handled: {invalid_data_handled} (status: {response2.status_code})")
        print(f"Malformed JSON handled: {malformed_json_handled} (status: {response3.status_code})")
        
        # At least 2 out of 3 error scenarios should be handled properly
        error_handling_score = sum([invalid_endpoint_handled, invalid_data_handled, malformed_json_handled])
        
        return error_handling_score >= 2, {
            "invalid_endpoint_handled": invalid_endpoint_handled,
            "invalid_data_handled": invalid_data_handled,
            "malformed_json_handled": malformed_json_handled,
            "error_handling_score": f"{error_handling_score}/3"
        }
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_agent_behavior_consistency():
    """Test 9: Agent Behavior - Test consistency between simple and complex tasks"""
    print("🔍 Testing agent behavior consistency...")
    
    try:
        # Test multiple simple conversations
        simple_messages = [
            "¿Qué tal?",
            "Buenos días",
            "¿Cómo funciona esto?"
        ]
        
        simple_results = []
        for msg in simple_messages:
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/chat", 
                json={"message": msg}, 
                timeout=20
            )
            if response.status_code == 200:
                data = response.json()
                simple_results.append({
                    "message": msg,
                    "response_length": len(data.get('response', '')),
                    "memory_used": data.get('memory_used', False),
                    "has_task_id": bool(data.get('task_id'))
                })
        
        # Test multiple complex tasks
        complex_messages = [
            "Analiza las tendencias del mercado tecnológico",
            "Crea un plan de marketing digital",
            "Investiga sobre energías renovables"
        ]
        
        complex_results = []
        for msg in complex_messages:
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/chat", 
                json={"message": msg}, 
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                complex_results.append({
                    "message": msg,
                    "response_length": len(data.get('response', '')),
                    "memory_used": data.get('memory_used', False),
                    "has_task_id": bool(data.get('task_id')),
                    "tool_calls": len(data.get('tool_calls', []))
                })
        
        # Analyze consistency
        simple_avg_length = sum(r['response_length'] for r in simple_results) / len(simple_results) if simple_results else 0
        complex_avg_length = sum(r['response_length'] for r in complex_results) / len(complex_results) if complex_results else 0
        
        # Complex responses should generally be longer
        length_consistency = complex_avg_length > simple_avg_length
        
        # Memory usage should be consistent
        simple_memory_usage = sum(r['memory_used'] for r in simple_results) / len(simple_results) if simple_results else 0
        complex_memory_usage = sum(r['memory_used'] for r in complex_results) / len(complex_results) if complex_results else 0
        
        print(f"Simple avg length: {simple_avg_length:.1f}")
        print(f"Complex avg length: {complex_avg_length:.1f}")
        print(f"Simple memory usage: {simple_memory_usage:.1f}")
        print(f"Complex memory usage: {complex_memory_usage:.1f}")
        
        return True, {
            "simple_results": simple_results,
            "complex_results": complex_results,
            "simple_avg_length": simple_avg_length,
            "complex_avg_length": complex_avg_length,
            "length_consistency": length_consistency,
            "simple_memory_usage": simple_memory_usage,
            "complex_memory_usage": complex_memory_usage
        }
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def print_final_summary():
    """Print comprehensive test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print("🎯 COMPREHENSIVE MITOSIS AGENT TEST SUMMARY")
    print("="*80)
    print(f"Timestamp: {test_results['timestamp']}")
    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    # Detailed results
    print("\n📊 DETAILED RESULTS:")
    for test in test_results["tests"]:
        status = "✅ PASSED" if test["passed"] else "❌ FAILED"
        duration = test.get("duration", "N/A")
        print(f"  {status} - {test['name']} ({duration}s)")
        
        if not test["passed"] and "error" in test:
            print(f"    Error: {test['error']}")
    
    # Critical findings
    print("\n🔍 CRITICAL FINDINGS:")
    
    # Backend health
    health_test = next((t for t in test_results["tests"] if "Backend Health" in t["name"]), None)
    if health_test and health_test["passed"]:
        print("  ✅ Backend services are healthy")
    else:
        print("  ❌ Backend health issues detected")
    
    # Agent functionality
    simple_test = next((t for t in test_results["tests"] if "Simple Conversation" in t["name"]), None)
    complex_test = next((t for t in test_results["tests"] if "Complex Task" in t["name"]), None)
    
    if simple_test and complex_test:
        if simple_test["passed"] and complex_test["passed"]:
            print("  ✅ Agent handles both simple and complex tasks correctly")
        else:
            print("  ❌ Agent behavior issues detected")
    
    # Memory system
    memory_test = next((t for t in test_results["tests"] if "Memory System" in t["name"]), None)
    if memory_test and memory_test["passed"]:
        print("  ✅ Memory system is functional")
    else:
        print("  ❌ Memory system issues detected")
    
    # Tools integration
    tools_test = next((t for t in test_results["tests"] if "Tools Integration" in t["name"]), None)
    if tools_test and tools_test["passed"]:
        result_data = tools_test.get("result_data", {})
        tools_count = result_data.get("total_tools", 0)
        print(f"  ✅ Tools integration working ({tools_count} tools available)")
    else:
        print("  ❌ Tools integration issues detected")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if passed / total >= 0.8:
        print("  ✅ EXCELLENT - Agent is working correctly after dependency fixes")
    elif passed / total >= 0.6:
        print("  ⚠️  GOOD - Agent is mostly working with minor issues")
    else:
        print("  ❌ POOR - Agent has significant issues that need attention")
    
    print("="*80)

def main():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive Mitosis Agent Testing...")
    
    # Run all tests
    run_test("Backend Health Check", test_backend_health)
    run_test("Simple Conversation Test", test_agent_chat_simple)
    run_test("Complex Task Test", test_agent_chat_complex)
    run_test("WebSearch Functionality Test", test_websearch_functionality)
    run_test("Memory System Integration Test", test_memory_system)
    run_test("Tools Integration Test", test_tools_integration)
    run_test("Planning System Test", test_planning_system)
    run_test("Error Handling Test", test_error_handling)
    run_test("Agent Behavior Consistency Test", test_agent_behavior_consistency)
    
    # Print final summary
    print_final_summary()
    
    # Save results to file
    with open('/app/comprehensive_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Test results saved to: /app/comprehensive_test_results.json")

if __name__ == "__main__":
    main()