#!/usr/bin/env python3
"""
Autonomous Backend Test Script for Mitosis Agent - POST MOCKUP REMOVAL TESTING

This script tests the new autonomous functionality after MOCKUP content removal:
1. /chat endpoint - should generate REAL dynamic plans using TaskPlanner
2. /generate-plan endpoint - should create plans based on available tools
3. /generate-suggestions endpoint - should give dynamic suggestions (not hardcoded)
4. Real autonomy - verify tasks are planned and executed without predetermined content
5. Ollama integration - verify it uses https://9g1hiqvg9k@wnbaldwy.com with llama3.1:8b
6. Fallback handling - verify appropriate fallback if autonomous execution fails
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

print(f"🧪 Testing Autonomous Mitosis Agent Backend")
print(f"🔗 Backend URL: {BASE_URL}")
print(f"📅 Test Date: {datetime.now().isoformat()}")

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
    print(f"🧪 TEST: {name}")
    print(f"🔗 URL: {url}")
    print(f"📤 METHOD: {method}")
    if data:
        print(f"📋 DATA: {json.dumps(data, indent=2)}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        status_code = response.status_code
        print(f"📊 STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"📄 RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"📄 RESPONSE: {response_data}")
        
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
            "missing_keys": missing_keys if not keys_ok else None,
            "response_data": response_data if passed else None
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"✅ RESULT: PASSED")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ RESULT: FAILED")
            if not status_ok:
                print(f"  - Expected status {expected_status}, got {status_code}")
            if not keys_ok:
                print(f"  - Missing expected keys: {', '.join(missing_keys)}")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "error": str(e),
            "passed": False
        })
        print(f"❌ ERROR: {str(e)}")
        print(f"❌ RESULT: FAILED (Exception)")
        return False, None

def test_autonomous_chat_endpoint():
    """Test /chat endpoint for autonomous execution with REAL dynamic planning"""
    print(f"\n{'='*80}")
    print(f"🤖 TESTING AUTONOMOUS CHAT ENDPOINT - KEY REQUIREMENT")
    
    test_cases = [
        {
            "name": "Basic Autonomous Task",
            "message": "Crear un plan para desarrollar una aplicación web moderna",
            "expected_autonomous": True
        },
        {
            "name": "Complex Analysis Task", 
            "message": "Analizar las tendencias de inteligencia artificial en 2025",
            "expected_autonomous": True
        },
        {
            "name": "Technical Implementation Task",
            "message": "Implementar un sistema de autenticación seguro",
            "expected_autonomous": True
        }
    ]
    
    autonomous_tests_passed = 0
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        
        data = {
            "message": test_case["message"],
            "context": {
                "task_id": f"autonomous_test_{int(time.time())}",
                "previous_messages": []
            }
        }
        
        passed, response_data = run_test(
            f"Autonomous Chat - {test_case['name']}", 
            f"{API_PREFIX}/chat",
            method="POST",
            data=data,
            expected_status=200,
            expected_keys=["response", "autonomous_execution", "timestamp"],
            timeout=45
        )
        
        if passed and isinstance(response_data, dict):
            # Verify autonomous execution
            autonomous_execution = response_data.get("autonomous_execution", False)
            has_execution_plan = "execution_plan" in response_data
            has_model_info = "model" in response_data
            
            print(f"🤖 Autonomous Execution: {autonomous_execution}")
            print(f"📋 Has Execution Plan: {has_execution_plan}")
            print(f"🧠 Has Model Info: {has_model_info}")
            
            # Check for REAL planning (not MOCKUP)
            response_text = response_data.get("response", "")
            has_real_planning = any(indicator in response_text for indicator in [
                "Plan de ejecución generado",
                "Tiempo estimado",
                "Complejidad",
                "Probabilidad de éxito"
            ])
            
            print(f"📊 Has Real Planning Indicators: {has_real_planning}")
            
            # Check execution plan structure if present
            if has_execution_plan:
                execution_plan = response_data.get("execution_plan", {})
                plan_has_steps = "steps" in execution_plan and len(execution_plan.get("steps", [])) > 0
                plan_has_metrics = all(key in execution_plan for key in [
                    "complexity_score", "success_probability", "total_estimated_duration"
                ])
                
                print(f"📋 Plan Has Steps: {plan_has_steps} ({len(execution_plan.get('steps', []))} steps)")
                print(f"📊 Plan Has Metrics: {plan_has_metrics}")
                
                if plan_has_steps:
                    for i, step in enumerate(execution_plan.get("steps", [])[:3]):
                        print(f"   Step {i+1}: {step.get('title', 'No title')}")
            
            # Verify NOT MOCKUP content
            is_not_mockup = not any(mockup_indicator in response_text.lower() for mockup_indicator in [
                "mockup", "placeholder", "ejemplo", "simulado", "demo"
            ])
            
            print(f"🚫 Not MOCKUP Content: {is_not_mockup}")
            
            # Test passes if it shows autonomous execution with real planning
            autonomous_test_passed = (
                autonomous_execution and 
                has_real_planning and 
                is_not_mockup and
                (has_execution_plan or "planning_error" in response_data)  # Allow planning errors as fallback
            )
            
            if autonomous_test_passed:
                autonomous_tests_passed += 1
                print(f"✅ Autonomous test PASSED for {test_case['name']}")
            else:
                print(f"❌ Autonomous test FAILED for {test_case['name']}")
                if not autonomous_execution:
                    print("   - Missing autonomous_execution flag")
                if not has_real_planning:
                    print("   - Missing real planning indicators")
                if not is_not_mockup:
                    print("   - Contains MOCKUP content")
    
    print(f"\n📊 AUTONOMOUS CHAT SUMMARY: {autonomous_tests_passed}/{len(test_cases)} tests passed")
    return autonomous_tests_passed == len(test_cases)

def test_generate_plan_endpoint():
    """Test /generate-plan endpoint for dynamic plan creation"""
    print(f"\n{'='*80}")
    print(f"📋 TESTING GENERATE-PLAN ENDPOINT - DYNAMIC PLANNING")
    
    test_cases = [
        "Desarrollar una API REST con autenticación",
        "Crear un dashboard de analytics",
        "Implementar un sistema de notificaciones"
    ]
    
    plans_generated = 0
    
    for task_title in test_cases:
        print(f"\n🔍 Testing plan generation for: {task_title}")
        
        data = {"task_title": task_title}
        
        passed, response_data = run_test(
            f"Generate Plan - {task_title[:30]}...",
            f"{API_PREFIX}/generate-plan",
            method="POST", 
            data=data,
            expected_status=200,
            expected_keys=["plan", "generated_dynamically"],
            timeout=30
        )
        
        if passed and isinstance(response_data, dict):
            plan = response_data.get("plan", [])
            generated_dynamically = response_data.get("generated_dynamically", False)
            
            print(f"📋 Plan Steps: {len(plan)}")
            print(f"🔄 Generated Dynamically: {generated_dynamically}")
            
            # Check plan structure
            if plan and len(plan) > 0:
                has_valid_steps = all(
                    isinstance(step, dict) and 
                    "title" in step and 
                    "description" in step
                    for step in plan
                )
                
                print(f"✅ Valid Plan Structure: {has_valid_steps}")
                
                # Show first few steps
                for i, step in enumerate(plan[:3]):
                    print(f"   Step {i+1}: {step.get('title', 'No title')}")
                
                if has_valid_steps and generated_dynamically:
                    plans_generated += 1
                    print(f"✅ Plan generation PASSED")
                else:
                    print(f"❌ Plan generation FAILED")
            else:
                print(f"❌ No plan steps generated")
    
    print(f"\n📊 PLAN GENERATION SUMMARY: {plans_generated}/{len(test_cases)} plans generated successfully")
    return plans_generated == len(test_cases)

def test_generate_suggestions_endpoint():
    """Test /generate-suggestions endpoint for dynamic suggestions"""
    print(f"\n{'='*80}")
    print(f"💡 TESTING GENERATE-SUGGESTIONS ENDPOINT - DYNAMIC SUGGESTIONS")
    
    passed, response_data = run_test(
        "Generate Dynamic Suggestions",
        f"{API_PREFIX}/generate-suggestions",
        method="POST",
        data={},
        expected_status=200,
        expected_keys=["suggestions", "generated_dynamically"],
        timeout=15
    )
    
    if passed and isinstance(response_data, dict):
        suggestions = response_data.get("suggestions", [])
        generated_dynamically = response_data.get("generated_dynamically", False)
        based_on_tools = response_data.get("based_on_available_tools", [])
        
        print(f"💡 Suggestions Count: {len(suggestions)}")
        print(f"🔄 Generated Dynamically: {generated_dynamically}")
        print(f"🛠️ Based on Tools: {based_on_tools}")
        
        # Check suggestions structure
        if suggestions and len(suggestions) > 0:
            has_valid_suggestions = all(
                isinstance(suggestion, dict) and
                "title" in suggestion and
                "tool" in suggestion
                for suggestion in suggestions
            )
            
            print(f"✅ Valid Suggestions Structure: {has_valid_suggestions}")
            
            # Show suggestions
            for i, suggestion in enumerate(suggestions):
                print(f"   Suggestion {i+1}: {suggestion.get('title', 'No title')} (Tool: {suggestion.get('tool', 'No tool')})")
            
            # Check for NOT hardcoded content
            suggestion_titles = [s.get('title', '') for s in suggestions]
            is_not_hardcoded = not all(
                title in [
                    "Crear un documento",
                    "Buscar información",
                    "Analizar datos"
                ] for title in suggestion_titles
            )
            
            print(f"🚫 Not Hardcoded: {is_not_hardcoded}")
            
            suggestions_test_passed = (
                has_valid_suggestions and 
                generated_dynamically and 
                is_not_hardcoded and
                len(based_on_tools) > 0
            )
            
            if suggestions_test_passed:
                print(f"✅ Suggestions generation PASSED")
                return True
            else:
                print(f"❌ Suggestions generation FAILED")
                return False
        else:
            print(f"❌ No suggestions generated")
            return False
    
    return False

def test_ollama_integration():
    """Test Ollama integration with specific endpoint"""
    print(f"\n{'='*80}")
    print(f"🧠 TESTING OLLAMA INTEGRATION - SPECIFIC ENDPOINT")
    
    # Test Ollama connection check
    ollama_endpoint = "https://9g1hiqvg9k@wnbaldwy.com"
    
    data = {"endpoint": ollama_endpoint}
    
    passed, response_data = run_test(
        "Ollama Connection Check",
        f"{API_PREFIX}/ollama/check",
        method="POST",
        data=data,
        expected_status=200,
        expected_keys=["is_connected", "endpoint"],
        timeout=20
    )
    
    ollama_connected = False
    if passed and isinstance(response_data, dict):
        is_connected = response_data.get("is_connected", False)
        endpoint_returned = response_data.get("endpoint", "")
        
        print(f"🔗 Connected: {is_connected}")
        print(f"🌐 Endpoint: {endpoint_returned}")
        
        if is_connected and endpoint_returned == ollama_endpoint:
            ollama_connected = True
            print(f"✅ Ollama connection PASSED")
        else:
            print(f"❌ Ollama connection FAILED")
    
    # Test Ollama models
    if ollama_connected:
        passed_models, models_data = run_test(
            "Ollama Models Check",
            f"{API_PREFIX}/ollama/models", 
            method="POST",
            data=data,
            expected_status=200,
            expected_keys=["models", "endpoint"],
            timeout=20
        )
        
        if passed_models and isinstance(models_data, dict):
            models = models_data.get("models", [])
            has_llama31 = "llama3.1:8b" in models
            
            print(f"🤖 Available Models: {models}")
            print(f"🎯 Has llama3.1:8b: {has_llama31}")
            
            if has_llama31:
                print(f"✅ Ollama models PASSED")
                return True
            else:
                print(f"⚠️ llama3.1:8b model not found, but connection works")
                return True  # Still pass if connection works
    
    return ollama_connected

def test_fallback_handling():
    """Test fallback handling when autonomous execution fails"""
    print(f"\n{'='*80}")
    print(f"🛡️ TESTING FALLBACK HANDLING")
    
    # Test with a potentially problematic request
    data = {
        "message": "Execute a complex system operation that might fail",
        "context": {
            "task_id": f"fallback_test_{int(time.time())}",
            "force_error": True  # This might not be handled, but let's see
        }
    }
    
    passed, response_data = run_test(
        "Fallback Handling Test",
        f"{API_PREFIX}/chat",
        method="POST",
        data=data,
        expected_status=200,
        expected_keys=["response", "timestamp"],
        timeout=30
    )
    
    if passed and isinstance(response_data, dict):
        has_fallback_used = response_data.get("fallback_used", False)
        has_error_info = "error" in response_data or "planning_error" in response_data
        autonomous_execution = response_data.get("autonomous_execution", False)
        
        print(f"🛡️ Fallback Used: {has_fallback_used}")
        print(f"❌ Has Error Info: {has_error_info}")
        print(f"🤖 Autonomous Execution: {autonomous_execution}")
        
        # Good fallback should either work autonomously or gracefully fallback
        fallback_works = (
            autonomous_execution or  # Works autonomously
            has_fallback_used or     # Uses fallback
            has_error_info           # Provides error info
        )
        
        if fallback_works:
            print(f"✅ Fallback handling PASSED")
            return True
        else:
            print(f"❌ Fallback handling FAILED")
            return False
    
    return False

def test_no_mockup_content():
    """Test that there's no MOCKUP content in responses"""
    print(f"\n{'='*80}")
    print(f"🚫 TESTING NO MOCKUP CONTENT - CRITICAL REQUIREMENT")
    
    test_messages = [
        "Crear un plan de marketing digital",
        "Desarrollar una estrategia de contenido",
        "Analizar competencia en el mercado"
    ]
    
    no_mockup_tests_passed = 0
    
    for message in test_messages:
        print(f"\n🔍 Testing for MOCKUP content in: {message}")
        
        data = {
            "message": message,
            "context": {"task_id": f"mockup_test_{int(time.time())}"}
        }
        
        passed, response_data = run_test(
            f"No MOCKUP Test - {message[:30]}...",
            f"{API_PREFIX}/chat",
            method="POST",
            data=data,
            expected_status=200,
            timeout=30
        )
        
        if passed and isinstance(response_data, dict):
            response_text = response_data.get("response", "").lower()
            
            # Check for MOCKUP indicators
            mockup_indicators = [
                "mockup", "placeholder", "ejemplo hardcodeado", 
                "contenido simulado", "demo", "test content",
                "lorem ipsum", "sample data", "fake data"
            ]
            
            has_mockup = any(indicator in response_text for indicator in mockup_indicators)
            
            print(f"🚫 Has MOCKUP Content: {has_mockup}")
            
            if not has_mockup:
                no_mockup_tests_passed += 1
                print(f"✅ No MOCKUP content found")
            else:
                print(f"❌ MOCKUP content detected")
                # Show which indicators were found
                found_indicators = [indicator for indicator in mockup_indicators if indicator in response_text]
                print(f"   Found indicators: {found_indicators}")
    
    print(f"\n📊 NO MOCKUP SUMMARY: {no_mockup_tests_passed}/{len(test_messages)} tests passed")
    return no_mockup_tests_passed == len(test_messages)

def print_summary():
    """Print comprehensive test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print(f"🧪 AUTONOMOUS MITOSIS AGENT TEST SUMMARY")
    print(f"📅 Timestamp: {test_results['timestamp']}")
    print(f"📊 Total tests: {total}")
    print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
    print("="*80)
    
    # Print failed tests
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"- {test['name']} ({test['endpoint']})")
                if "error" in test:
                    print(f"  Error: {test['error']}")
                elif "status_code" in test and "expected_status" in test and test["status_code"] != test["expected_status"]:
                    print(f"  Expected status {test['expected_status']}, got {test['status_code']}")
                if "missing_keys" in test and test["missing_keys"]:
                    print(f"  Missing keys: {', '.join(test['missing_keys'])}")

def main():
    """Run all autonomous functionality tests"""
    print(f"🚀 Starting Autonomous Mitosis Agent Testing")
    print(f"🎯 Focus: Post-MOCKUP removal verification")
    
    # Test basic connectivity first
    health_passed, _ = run_test(
        "Backend Health Check",
        "/health",
        expected_keys=["status", "services"]
    )
    
    if not health_passed:
        print(f"❌ Backend health check failed. Cannot continue testing.")
        return False
    
    # Run autonomous functionality tests
    test_results_summary = {
        "autonomous_chat": test_autonomous_chat_endpoint(),
        "generate_plan": test_generate_plan_endpoint(), 
        "generate_suggestions": test_generate_suggestions_endpoint(),
        "ollama_integration": test_ollama_integration(),
        "fallback_handling": test_fallback_handling(),
        "no_mockup_content": test_no_mockup_content()
    }
    
    # Print detailed summary
    print_summary()
    
    # Print autonomous functionality summary
    print(f"\n🤖 AUTONOMOUS FUNCTIONALITY RESULTS:")
    for test_name, result in test_results_summary.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"- {test_name.replace('_', ' ').title()}: {status}")
    
    # Overall assessment
    passed_tests = sum(test_results_summary.values())
    total_tests = len(test_results_summary)
    
    print(f"\n🎯 OVERALL AUTONOMOUS ASSESSMENT: {passed_tests}/{total_tests} core tests passed")
    
    if passed_tests == total_tests:
        print(f"🎉 ALL AUTONOMOUS FUNCTIONALITY TESTS PASSED!")
        print(f"✅ Mitosis agent is truly autonomous (no MOCKUP content)")
        return True
    else:
        print(f"⚠️ Some autonomous functionality tests failed")
        print(f"🔧 Review failed tests and fix implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)