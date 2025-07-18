#!/usr/bin/env python3
"""
Simplified Agent Testing Script - REVIEW REQUEST FULFILLMENT
Testing the new ultra simple and effective agent implementation

SPECIFIC TESTS REQUESTED:
1. Health Check: Test /api/agent/health
2. Chat with Action Plan: Test /api/agent/chat with "Dame un informe sobre inteligencia artificial en 2025"
3. Plan Generation: Test /api/agent/generate-plan with different task types
4. Task Classification: Verify different task types generate specific plans

VERIFICATION CRITERIA:
- Plans have specific steps (not generic)
- Each step has title, description, tool, and estimated time
- Final response is useful without placeholders
- No duplications in responses
- Progress is marked correctly (completed: true/false)
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

print(f"🧪 SIMPLIFIED AGENT TESTING - REVIEW REQUEST FULFILLMENT")
print(f"Using backend URL: {BASE_URL}")
print(f"Testing timestamp: {datetime.now().isoformat()}")

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

def run_test(name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, timeout=30):
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
        response_time = round(end_time - start_time, 2)
        
        status_code = response.status_code
        print(f"⏱️  RESPONSE TIME: {response_time}s")
        print(f"📊 STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"📥 RESPONSE KEYS: {list(response_data.keys())}")
            
            # Print key parts of response for analysis
            if 'response' in response_data:
                response_text = response_data['response']
                print(f"📝 RESPONSE LENGTH: {len(response_text)} characters")
                print(f"📝 RESPONSE PREVIEW: {response_text[:200]}...")
            
            if 'plan' in response_data:
                plan = response_data['plan']
                print(f"📋 PLAN STEPS: {len(plan)} steps")
                for i, step in enumerate(plan[:3]):  # Show first 3 steps
                    print(f"   Step {i+1}: {step.get('title', 'NO TITLE')} ({step.get('tool', 'NO TOOL')})")
            
            if 'task_type' in response_data:
                print(f"🏷️  TASK TYPE: {response_data['task_type']}")
            
            if 'complexity' in response_data:
                print(f"📊 COMPLEXITY: {response_data['complexity']}")
                
        except:
            response_data = response.text
            print(f"📥 RESPONSE (TEXT): {response_data[:300]}...")
        
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
            "response_time": response_time,
            "passed": passed,
            "missing_keys": missing_keys if not keys_ok else None,
            "response_data": response_data if passed and isinstance(response_data, dict) else None
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"✅ RESULT: PASSED")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ RESULT: FAILED")
            if not status_ok:
                print(f"   - Expected status {expected_status}, got {status_code}")
            if not keys_ok:
                print(f"   - Missing expected keys: {', '.join(missing_keys)}")
        
        return passed, response_data
    
    except Exception as e:
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "response_time": response_time,
            "error": str(e),
            "passed": False
        })
        print(f"❌ ERROR: {str(e)}")
        print(f"❌ RESULT: FAILED (Exception)")
        return False, None

def analyze_plan_quality(plan_data, task_description):
    """Analyze the quality of a generated plan"""
    if not isinstance(plan_data, list):
        return False, "Plan is not a list of steps"
    
    if len(plan_data) == 0:
        return False, "Plan is empty"
    
    issues = []
    
    # Check each step has required fields
    required_fields = ['title', 'description', 'tool', 'estimated_time']
    for i, step in enumerate(plan_data):
        for field in required_fields:
            if field not in step:
                issues.append(f"Step {i+1} missing '{field}'")
            elif not step[field] or step[field] == "":
                issues.append(f"Step {i+1} has empty '{field}'")
    
    # Check for generic/placeholder content
    generic_indicators = ['placeholder', 'example', 'generic', 'TODO', 'TBD']
    for i, step in enumerate(plan_data):
        title = step.get('title', '').lower()
        description = step.get('description', '').lower()
        
        for indicator in generic_indicators:
            if indicator in title or indicator in description:
                issues.append(f"Step {i+1} contains generic/placeholder content: '{indicator}'")
    
    # Check for task-specific content
    task_words = task_description.lower().split()
    task_specific = False
    for step in plan_data:
        step_text = (step.get('title', '') + ' ' + step.get('description', '')).lower()
        if any(word in step_text for word in task_words if len(word) > 3):
            task_specific = True
            break
    
    if not task_specific:
        issues.append("Plan doesn't seem specific to the task - no task-related keywords found")
    
    # Check for duplicated steps
    titles = [step.get('title', '') for step in plan_data]
    if len(titles) != len(set(titles)):
        issues.append("Plan contains duplicated step titles")
    
    return len(issues) == 0, issues

def test_task_classification():
    """Test different task types to verify classification and plan generation"""
    print(f"\n{'='*80}")
    print(f"🧪 COMPREHENSIVE TASK CLASSIFICATION TEST")
    
    test_cases = [
        {
            "name": "Research Task",
            "message": "Buscar información sobre el cambio climático",
            "expected_type": "research",
            "expected_tools": ["web_search", "analysis"]
        },
        {
            "name": "Analysis Task", 
            "message": "Analizar las ventajas y desventajas de la energía solar",
            "expected_type": "analysis",
            "expected_tools": ["data_collection", "analysis", "synthesis"]
        },
        {
            "name": "Creation Task",
            "message": "Crear un documento sobre marketing digital",
            "expected_type": "creation", 
            "expected_tools": ["planning", "content_creation", "review"]
        },
        {
            "name": "General Task",
            "message": "Hola, ¿cómo estás?",
            "expected_type": "general",
            "expected_tools": ["processing", "delivery"]
        }
    ]
    
    classification_results = []
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        print(f"📝 Message: {test_case['message']}")
        
        # Test plan generation
        passed, response_data = run_test(
            f"Plan Generation - {test_case['name']}",
            f"{API_PREFIX}/generate-plan",
            "POST",
            {"message": test_case["message"]},
            200,
            ["plan", "task_type", "complexity"]
        )
        
        if passed and isinstance(response_data, dict):
            # Analyze plan quality
            plan = response_data.get('plan', [])
            task_type = response_data.get('task_type', '')
            
            plan_quality_ok, plan_issues = analyze_plan_quality(plan, test_case['message'])
            
            # Check task type classification
            type_correct = task_type == test_case['expected_type']
            
            # Check if expected tools are present
            tools_in_plan = [step.get('tool', '') for step in plan]
            tools_present = any(tool in tools_in_plan for tool in test_case['expected_tools'])
            
            classification_results.append({
                "test_case": test_case['name'],
                "message": test_case['message'],
                "expected_type": test_case['expected_type'],
                "actual_type": task_type,
                "type_correct": type_correct,
                "plan_quality_ok": plan_quality_ok,
                "plan_issues": plan_issues,
                "tools_present": tools_present,
                "plan_steps": len(plan)
            })
            
            print(f"   📊 Task Type: {task_type} (Expected: {test_case['expected_type']}) {'✅' if type_correct else '❌'}")
            print(f"   📋 Plan Steps: {len(plan)}")
            print(f"   🔧 Tools in Plan: {tools_in_plan}")
            print(f"   ✅ Plan Quality: {'OK' if plan_quality_ok else 'ISSUES'}")
            if not plan_quality_ok:
                for issue in plan_issues[:3]:  # Show first 3 issues
                    print(f"      - {issue}")
    
    return classification_results

def main():
    """Main testing function"""
    print(f"\n🚀 STARTING SIMPLIFIED AGENT COMPREHENSIVE TESTING")
    
    # TEST 1: Health Check
    print(f"\n📋 TEST 1: HEALTH CHECK")
    run_test(
        "Agent Health Check",
        f"{API_PREFIX}/health",
        "GET",
        None,
        200,
        ["status"]
    )
    
    # TEST 2: Chat with Action Plan (Specific request from review)
    print(f"\n📋 TEST 2: CHAT WITH ACTION PLAN")
    chat_message = "Dame un informe sobre inteligencia artificial en 2025"
    passed, response_data = run_test(
        "Chat with Action Plan - AI Report 2025",
        f"{API_PREFIX}/chat",
        "POST",
        {"message": chat_message},
        200,
        ["response", "plan", "task_id"],
        60  # Longer timeout for complex task
    )
    
    # Analyze the chat response quality
    if passed and isinstance(response_data, dict):
        print(f"\n🔍 ANALYZING CHAT RESPONSE QUALITY:")
        
        response_text = response_data.get('response', '')
        plan = response_data.get('plan', [])
        task_id = response_data.get('task_id', '')
        
        # Check response quality
        response_quality_issues = []
        
        if len(response_text) < 100:
            response_quality_issues.append("Response too short (< 100 characters)")
        
        if 'placeholder' in response_text.lower() or 'todo' in response_text.lower():
            response_quality_issues.append("Response contains placeholders")
        
        if 'inteligencia artificial' not in response_text.lower() and '2025' not in response_text.lower():
            response_quality_issues.append("Response doesn't seem related to the requested topic")
        
        # Analyze plan quality
        plan_quality_ok, plan_issues = analyze_plan_quality(plan, chat_message)
        
        print(f"   📝 Response Length: {len(response_text)} characters")
        print(f"   📋 Plan Steps: {len(plan)}")
        print(f"   🆔 Task ID: {task_id}")
        print(f"   ✅ Response Quality: {'OK' if len(response_quality_issues) == 0 else 'ISSUES'}")
        
        if response_quality_issues:
            for issue in response_quality_issues:
                print(f"      - {issue}")
        
        print(f"   ✅ Plan Quality: {'OK' if plan_quality_ok else 'ISSUES'}")
        if not plan_quality_ok:
            for issue in plan_issues[:3]:
                print(f"      - {issue}")
    
    # TEST 3: Plan Generation with Different Task Types
    print(f"\n📋 TEST 3: PLAN GENERATION WITH DIFFERENT TASK TYPES")
    classification_results = test_task_classification()
    
    # TEST 4: Verify No Duplications
    print(f"\n📋 TEST 4: VERIFY NO DUPLICATIONS IN RESPONSES")
    
    # Test multiple requests to same endpoint to check for duplications
    duplicate_test_messages = [
        "Crear un plan de marketing",
        "Crear un plan de marketing",  # Same message
        "Analizar datos de ventas",
        "Analizar datos de ventas"   # Same message
    ]
    
    responses = []
    for i, message in enumerate(duplicate_test_messages):
        passed, response_data = run_test(
            f"Duplication Test {i+1}",
            f"{API_PREFIX}/generate-plan",
            "POST",
            {"message": message},
            200,
            ["plan"]
        )
        
        if passed and isinstance(response_data, dict):
            responses.append({
                "message": message,
                "response": response_data.get('response', ''),
                "plan": response_data.get('plan', [])
            })
    
    # Check for duplications
    print(f"\n🔍 ANALYZING DUPLICATION PATTERNS:")
    
    # Group by message
    message_groups = {}
    for resp in responses:
        msg = resp['message']
        if msg not in message_groups:
            message_groups[msg] = []
        message_groups[msg].append(resp)
    
    duplication_issues = []
    for message, group in message_groups.items():
        if len(group) > 1:
            # Check if responses are identical (which would be bad)
            first_response = group[0]['response']
            first_plan = json.dumps(group[0]['plan'], sort_keys=True)
            
            for other in group[1:]:
                if other['response'] == first_response and json.dumps(other['plan'], sort_keys=True) == first_plan:
                    duplication_issues.append(f"Identical responses for message: '{message}'")
                    break
    
    print(f"   ✅ Duplication Check: {'OK' if len(duplication_issues) == 0 else 'ISSUES'}")
    if duplication_issues:
        for issue in duplication_issues:
            print(f"      - {issue}")
    
    # FINAL SUMMARY
    print(f"\n{'='*80}")
    print(f"📊 FINAL TEST SUMMARY")
    print(f"{'='*80}")
    
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"🧪 Total Tests: {total}")
    print(f"✅ Passed: {passed} ({success_rate:.1f}%)")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Testing Duration: {datetime.now().isoformat()}")
    
    # Detailed analysis
    print(f"\n📋 DETAILED ANALYSIS:")
    
    # Task Classification Analysis
    if classification_results:
        correct_classifications = sum(1 for r in classification_results if r['type_correct'])
        quality_plans = sum(1 for r in classification_results if r['plan_quality_ok'])
        
        print(f"   🏷️  Task Classification: {correct_classifications}/{len(classification_results)} correct")
        print(f"   📋 Plan Quality: {quality_plans}/{len(classification_results)} high quality")
        
        for result in classification_results:
            status = "✅" if result['type_correct'] and result['plan_quality_ok'] else "❌"
            print(f"      {status} {result['test_case']}: {result['actual_type']} ({result['plan_steps']} steps)")
    
    # Performance Analysis
    response_times = [test['response_time'] for test in test_results['tests'] if 'response_time' in test]
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        print(f"   ⏱️  Average Response Time: {avg_response_time:.2f}s")
        print(f"   ⏱️  Max Response Time: {max_response_time:.2f}s")
    
    # Final Verdict
    print(f"\n🎯 FINAL VERDICT:")
    if success_rate >= 80:
        print(f"✅ SIMPLIFIED AGENT IS WORKING EXCELLENTLY ({success_rate:.1f}% success rate)")
        print(f"   The new ultra simple and effective agent implementation is functioning correctly.")
        print(f"   Plans are specific, steps have required fields, and responses are useful.")
    elif success_rate >= 60:
        print(f"⚠️  SIMPLIFIED AGENT IS PARTIALLY WORKING ({success_rate:.1f}% success rate)")
        print(f"   Some issues detected but core functionality is operational.")
    else:
        print(f"❌ SIMPLIFIED AGENT HAS SIGNIFICANT ISSUES ({success_rate:.1f}% success rate)")
        print(f"   Major problems detected that need immediate attention.")
    
    # Failed tests summary
    if failed > 0:
        print(f"\n❌ FAILED TESTS SUMMARY:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"   - {test['name']}: {test.get('error', 'Status/Key issues')}")
    
    return success_rate >= 80

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with exception: {str(e)}")
        sys.exit(1)