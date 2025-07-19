#!/usr/bin/env python3
"""
MITOSIS BACKEND DIAGNOSTIC - FOCUSED ON ACTUAL ENDPOINTS
========================================================

This script tests the actual available endpoints and diagnoses the real system state.
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"
print(f"🔍 MITOSIS BACKEND DIAGNOSTIC")
print(f"🌐 Using backend URL: {BASE_URL}")
print(f"📅 Diagnostic started at: {datetime.now().isoformat()}")
print("="*80)

def test_endpoint(name, endpoint, method="GET", data=None, timeout=30):
    """Test an endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {name}")
    print(f"   URL: {url}")
    print(f"   Method: {method}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        
        status = response.status_code
        print(f"   Status: {status}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=4)}")
        else:
            result = response.text
            print(f"   Response: {result[:200]}...")
        
        success = status == 200
        print(f"   Result: {'✅ PASSED' if success else '❌ FAILED'}")
        
        return success, result
        
    except Exception as e:
        print(f"   Error: {e}")
        print(f"   Result: ❌ FAILED")
        return False, str(e)

def main():
    """Run the diagnostic"""
    
    results = {}
    
    # Test 1: Basic Health
    print("\n" + "="*50)
    print("SECTION 1: BASIC HEALTH CHECKS")
    print("="*50)
    
    success, result = test_endpoint("Main Health", "/api/health")
    results["main_health"] = {"success": success, "result": result}
    
    success, result = test_endpoint("Agent Health", "/api/agent/health")
    results["agent_health"] = {"success": success, "result": result}
    
    success, result = test_endpoint("Agent Status", "/api/agent/status")
    results["agent_status"] = {"success": success, "result": result}
    
    # Test 2: Chat Functionality
    print("\n" + "="*50)
    print("SECTION 2: CHAT FUNCTIONALITY")
    print("="*50)
    
    # Test simple greeting
    chat_data = {"message": "Hola"}
    success, result = test_endpoint("Simple Chat", "/api/agent/chat", "POST", chat_data, 30)
    results["simple_chat"] = {"success": success, "result": result}
    
    if success and isinstance(result, dict):
        print(f"   📊 Chat Analysis:")
        print(f"      Response length: {len(result.get('response', ''))}")
        print(f"      Memory used: {result.get('memory_used', 'N/A')}")
        print(f"      Task ID: {result.get('task_id', 'N/A')}")
        print(f"      Mode: {result.get('mode', 'N/A')}")
        print(f"      Status: {result.get('execution_status', 'N/A')}")
    
    # Test task request
    task_data = {"message": "Ayúdame a crear un documento sobre Python"}
    success, result = test_endpoint("Task Request", "/api/agent/chat", "POST", task_data, 45)
    results["task_request"] = {"success": success, "result": result}
    
    if success and isinstance(result, dict):
        print(f"   📊 Task Analysis:")
        print(f"      Response length: {len(result.get('response', ''))}")
        print(f"      Memory used: {result.get('memory_used', 'N/A')}")
        print(f"      Task ID: {result.get('task_id', 'N/A')}")
        print(f"      Mode: {result.get('mode', 'N/A')}")
        print(f"      Status: {result.get('execution_status', 'N/A')}")
        print(f"      Created files: {len(result.get('created_files', []))}")
        print(f"      Tool results: {len(result.get('tool_results', []))}")
    
    # Test 3: Ollama Integration
    print("\n" + "="*50)
    print("SECTION 3: OLLAMA INTEGRATION")
    print("="*50)
    
    ollama_check_data = {"endpoint": "https://78d08925604a.ngrok-free.app"}
    success, result = test_endpoint("Ollama Check", "/api/agent/ollama/check", "POST", ollama_check_data)
    results["ollama_check"] = {"success": success, "result": result}
    
    ollama_models_data = {"endpoint": "https://78d08925604a.ngrok-free.app"}
    success, result = test_endpoint("Ollama Models", "/api/agent/ollama/models", "POST", ollama_models_data)
    results["ollama_models"] = {"success": success, "result": result}
    
    # Test 4: Memory System (if available)
    print("\n" + "="*50)
    print("SECTION 4: MEMORY SYSTEM")
    print("="*50)
    
    # Check if memory endpoints exist
    success, result = test_endpoint("Memory Analytics", "/api/memory/analytics")
    results["memory_analytics"] = {"success": success, "result": result}
    
    # Test 5: WebSearch Integration
    print("\n" + "="*50)
    print("SECTION 5: WEBSEARCH INTEGRATION")
    print("="*50)
    
    websearch_data = {
        "message": "[WebSearch] inteligencia artificial 2025",
        "search_mode": "websearch"
    }
    success, result = test_endpoint("WebSearch", "/api/agent/chat", "POST", websearch_data, 60)
    results["websearch"] = {"success": success, "result": result}
    
    if success and isinstance(result, dict):
        print(f"   📊 WebSearch Analysis:")
        print(f"      Search mode: {result.get('search_mode', 'N/A')}")
        print(f"      Search data: {'Yes' if result.get('search_data') else 'No'}")
        if result.get('search_data'):
            search_data = result['search_data']
            print(f"      Sources found: {len(search_data.get('sources', []))}")
            print(f"      Images found: {len(search_data.get('images', []))}")
    
    # Test 6: Plan Generation
    print("\n" + "="*50)
    print("SECTION 6: PLAN GENERATION")
    print("="*50)
    
    plan_data = {"message": "Crear un informe sobre tendencias tecnológicas"}
    success, result = test_endpoint("Plan Generation", "/api/agent/generate-plan", "POST", plan_data)
    results["plan_generation"] = {"success": success, "result": result}
    
    # Generate Summary
    print("\n" + "="*80)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"📈 OVERALL RESULTS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"   Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, test_result in results.items():
        status = "✅ PASSED" if test_result["success"] else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    # Critical Analysis
    print(f"\n🔍 CRITICAL ANALYSIS:")
    
    # Check if basic health is working
    if results.get("main_health", {}).get("success") and results.get("agent_health", {}).get("success"):
        print("   ✅ Backend services are running correctly")
    else:
        print("   ❌ Backend services have issues")
    
    # Check if chat is working
    if results.get("simple_chat", {}).get("success"):
        print("   ✅ Basic chat functionality is working")
        
        # Check memory integration
        simple_result = results.get("simple_chat", {}).get("result", {})
        if isinstance(simple_result, dict) and simple_result.get("memory_used"):
            print("   ✅ Memory integration is working")
        else:
            print("   ⚠️  Memory integration may not be working")
    else:
        print("   ❌ Basic chat functionality is not working")
    
    # Check if task processing is working
    if results.get("task_request", {}).get("success"):
        task_result = results.get("task_request", {}).get("result", {})
        if isinstance(task_result, dict):
            created_files = len(task_result.get("created_files", []))
            tool_results = len(task_result.get("tool_results", []))
            
            if created_files > 0 or tool_results > 0:
                print("   ✅ Task processing delivers actual results")
            else:
                print("   ⚠️  Task processing may not deliver actual results")
                print("       This could be the 'says it completes but doesn't deliver' issue")
    
    # Check Ollama integration
    if results.get("ollama_check", {}).get("success"):
        print("   ✅ Ollama integration is working")
    else:
        print("   ⚠️  Ollama integration may have issues")
    
    # Check WebSearch
    if results.get("websearch", {}).get("success"):
        websearch_result = results.get("websearch", {}).get("result", {})
        if isinstance(websearch_result, dict) and websearch_result.get("search_data"):
            print("   ✅ WebSearch functionality is working")
        else:
            print("   ⚠️  WebSearch may not be returning search data")
    else:
        print("   ❌ WebSearch functionality is not working")
    
    print(f"\n💡 RECOMMENDATIONS:")
    
    if failed_tests == 0:
        print("   ✅ System appears to be functioning correctly")
        print("   ✅ Ready to continue with improvements")
    elif failed_tests <= 2:
        print("   ⚠️  Minor issues detected but system is generally functional")
        print("   📈 Can proceed with improvements while monitoring issues")
    else:
        print("   🔧 Multiple issues detected - focus on fixing problems first")
    
    # Specific issue analysis
    if results.get("task_request", {}).get("success"):
        task_result = results.get("task_request", {}).get("result", {})
        if isinstance(task_result, dict):
            created_files = len(task_result.get("created_files", []))
            tool_results = len(task_result.get("tool_results", []))
            response_length = len(task_result.get("response", ""))
            
            if response_length > 100 and (created_files == 0 and tool_results == 0):
                print("   🚨 IDENTIFIED ISSUE: Agent provides detailed responses but doesn't create actual deliverables")
                print("      This matches the reported 'says it completes but doesn't deliver results' problem")
                print("      Recommendation: Check file creation and tool execution logic")
    
    print(f"\n📅 Diagnostic completed at: {datetime.now().isoformat()}")
    print("="*80)

if __name__ == "__main__":
    main()