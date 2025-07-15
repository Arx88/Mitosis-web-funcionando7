#!/usr/bin/env python3
"""
Execution Engine Comprehensive Testing Script
Tests the Execution Engine functionality as requested in the review:

1. Task Analysis Testing - /api/agent/task/analyze
2. Plan Generation Testing - /api/agent/task/plan  
3. Execution Engine Testing - /api/agent/task/execute
4. Tool Coordination Testing - verify execution engine coordination
5. Error Handling Testing - test error scenarios
6. Templates Testing - /api/agent/plans/templates
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"

print(f"🚀 EXECUTION ENGINE COMPREHENSIVE TESTING")
print(f"Using backend URL: {BASE_URL}")
print(f"Testing Phase 3.2 - Execution Engine Integration")

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
    print(f"TEST: {name}")
    print(f"URL: {url}")
    print(f"METHOD: {method}")
    if data:
        print(f"DATA: {json.dumps(data, indent=2)}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
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
            "missing_keys": missing_keys if not keys_ok else None,
            "response_data": response_data if passed else None
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
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
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_task_analysis():
    """Test the /api/agent/task/analyze endpoint with different types of tasks"""
    print(f"\n🔍 TESTING TASK ANALYSIS FUNCTIONALITY")
    
    # Test cases for different task types
    test_cases = [
        {
            "name": "Web Development Task Analysis",
            "task_title": "Build a responsive portfolio website",
            "task_description": "Create a modern portfolio website with HTML, CSS, JavaScript, and responsive design",
            "expected_type": "web_development"
        },
        {
            "name": "Data Analysis Task Analysis", 
            "task_title": "Analyze sales data and create visualization",
            "task_description": "Process CSV sales data, perform statistical analysis, and create charts",
            "expected_type": "data_analysis"
        },
        {
            "name": "File Processing Task Analysis",
            "task_title": "Convert and organize image files",
            "task_description": "Batch convert images from PNG to JPEG and organize by date",
            "expected_type": "file_processing"
        }
    ]
    
    analysis_results = []
    
    for test_case in test_cases:
        data = {
            "task_title": test_case["task_title"],
            "task_description": test_case["task_description"]
        }
        
        passed, response_data = run_test(
            test_case["name"],
            f"{API_PREFIX}/task/analyze",
            method="POST",
            data=data,
            expected_keys=["success", "analysis"]
        )
        
        if passed and response_data:
            analysis = response_data.get("analysis", {})
            print(f"📊 Analysis Results:")
            print(f"   Task Type: {analysis.get('task_type', 'Unknown')}")
            print(f"   Complexity: {analysis.get('complexity', 'Unknown')}")
            print(f"   Required Tools: {analysis.get('required_tools', [])}")
            print(f"   Estimated Duration: {analysis.get('estimated_duration', 'Unknown')} seconds")
            
            analysis_results.append({
                "test_case": test_case["name"],
                "analysis": analysis,
                "passed": passed
            })
    
    return analysis_results

def test_plan_generation():
    """Test the /api/agent/task/plan endpoint to verify proper execution plans"""
    print(f"\n📋 TESTING PLAN GENERATION FUNCTIONALITY")
    
    # Test plan generation for different task types
    test_cases = [
        {
            "name": "Web Development Plan Generation",
            "task_id": f"web-dev-{uuid.uuid4()}",
            "task_title": "Create a landing page with contact form",
            "task_description": "Build a responsive landing page with HTML, CSS, JavaScript and a working contact form"
        },
        {
            "name": "Data Analysis Plan Generation",
            "task_id": f"data-analysis-{uuid.uuid4()}",
            "task_title": "Analyze customer behavior data",
            "task_description": "Process customer data, identify patterns, and generate insights report"
        }
    ]
    
    plan_results = []
    
    for test_case in test_cases:
        data = {
            "task_id": test_case["task_id"],
            "task_title": test_case["task_title"],
            "task_description": test_case["task_description"]
        }
        
        passed, response_data = run_test(
            test_case["name"],
            f"{API_PREFIX}/task/plan",
            method="POST",
            data=data,
            expected_keys=["success", "execution_plan"]
        )
        
        if passed and response_data:
            execution_plan = response_data.get("execution_plan", {})
            steps = execution_plan.get("steps", [])
            
            print(f"📋 Execution Plan Results:")
            print(f"   Task ID: {execution_plan.get('task_id')}")
            print(f"   Title: {execution_plan.get('title')}")
            print(f"   Total Steps: {len(steps)}")
            print(f"   Estimated Duration: {execution_plan.get('total_estimated_duration')} seconds")
            print(f"   Complexity Score: {execution_plan.get('complexity_score')}")
            print(f"   Required Tools: {execution_plan.get('required_tools', [])}")
            print(f"   Success Probability: {execution_plan.get('success_probability', 0)}")
            
            # Validate step structure
            print(f"   📝 Steps Analysis:")
            for i, step in enumerate(steps):
                print(f"      Step {i+1}: {step.get('title', 'No title')}")
                print(f"         Tool: {step.get('tool', 'No tool')}")
                print(f"         Dependencies: {step.get('dependencies', [])}")
                print(f"         Duration: {step.get('estimated_duration', 0)} seconds")
                print(f"         Complexity: {step.get('complexity', 'Unknown')}")
            
            plan_results.append({
                "test_case": test_case["name"],
                "task_id": test_case["task_id"],
                "execution_plan": execution_plan,
                "passed": passed
            })
    
    return plan_results

def test_execution_engine():
    """Test the /api/agent/task/execute endpoint with a simple task"""
    print(f"\n⚙️ TESTING EXECUTION ENGINE FUNCTIONALITY")
    
    # Create a simple task for execution testing
    task_id = f"exec-test-{uuid.uuid4()}"
    task_title = "Simple file processing task"
    task_description = "Create a text file with system information"
    
    data = {
        "task_id": task_id,
        "task_title": task_title,
        "task_description": task_description,
        "config": {
            "max_retries": 2,
            "timeout_per_step": 60,
            "fail_fast": True
        }
    }
    
    # Start task execution
    passed, response_data = run_test(
        "Task Execution Start",
        f"{API_PREFIX}/task/execute",
        method="POST",
        data=data,
        expected_keys=["success", "message", "task_id", "status"]
    )
    
    if not passed:
        return {"execution_started": False, "task_id": task_id}
    
    print(f"✅ Task execution started successfully")
    print(f"   Task ID: {task_id}")
    print(f"   Status: {response_data.get('status', 'Unknown')}")
    
    # Wait a moment for execution to start
    time.sleep(2)
    
    # Test execution status tracking
    status_results = test_execution_status(task_id)
    
    return {
        "execution_started": True,
        "task_id": task_id,
        "start_response": response_data,
        "status_results": status_results
    }

def test_execution_status(task_id):
    """Test the /api/agent/task/execution-status/{task_id} endpoint"""
    print(f"\n📊 TESTING EXECUTION STATUS TRACKING")
    
    status_checks = []
    
    # Check status multiple times to track progress
    for i in range(3):
        passed, response_data = run_test(
            f"Execution Status Check {i+1}",
            f"{API_PREFIX}/task/execution-status/{task_id}",
            method="GET",
            expected_keys=["success", "execution_status"]
        )
        
        if passed and response_data:
            execution_status = response_data.get("execution_status", {})
            print(f"📊 Status Check {i+1}:")
            print(f"   Status: {execution_status.get('status', 'Unknown')}")
            print(f"   Current Step: {execution_status.get('current_step_index', 0)}")
            print(f"   Progress: {execution_status.get('success_rate', 0)*100:.1f}%")
            print(f"   Execution Time: {execution_status.get('total_execution_time', 0):.2f}s")
            
            status_checks.append({
                "check_number": i+1,
                "status": execution_status,
                "passed": passed
            })
        
        # Wait between status checks
        if i < 2:
            time.sleep(3)
    
    return status_checks

def test_tool_coordination():
    """Test that the execution engine can coordinate tools properly"""
    print(f"\n🔧 TESTING TOOL COORDINATION")
    
    # First, get available tools
    passed, response_data = run_test(
        "Available Tools Check",
        f"{API_PREFIX}/tools",
        method="GET",
        expected_keys=["tools", "count"]
    )
    
    if not passed:
        return {"tools_available": False}
    
    tools = response_data.get("tools", [])
    tool_names = [tool.get("name") for tool in tools]
    
    print(f"🔧 Available Tools ({len(tools)}):")
    for tool in tools:
        print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
    
    # Test a task that requires multiple tools
    task_id = f"coordination-test-{uuid.uuid4()}"
    task_title = "Multi-tool coordination test"
    task_description = "Create files and search for information using multiple tools"
    
    data = {
        "task_id": task_id,
        "task_title": task_title,
        "task_description": task_description,
        "config": {
            "max_retries": 1,
            "timeout_per_step": 30
        }
    }
    
    # Start execution
    passed, response_data = run_test(
        "Multi-tool Task Execution",
        f"{API_PREFIX}/task/execute",
        method="POST",
        data=data,
        expected_keys=["success", "task_id"]
    )
    
    coordination_result = {
        "tools_available": True,
        "tool_count": len(tools),
        "tool_names": tool_names,
        "execution_started": passed,
        "task_id": task_id if passed else None
    }
    
    if passed:
        # Wait and check status
        time.sleep(5)
        status_passed, status_data = run_test(
            "Coordination Status Check",
            f"{API_PREFIX}/task/execution-status/{task_id}",
            method="GET"
        )
        
        if status_passed:
            coordination_result["final_status"] = status_data.get("execution_status", {})
    
    return coordination_result

def test_error_handling():
    """Test error scenarios and retry mechanisms"""
    print(f"\n❌ TESTING ERROR HANDLING AND RETRY MECHANISMS")
    
    error_test_results = []
    
    # Test 1: Invalid tool parameters
    print(f"\n🧪 Test 1: Invalid Task Parameters")
    invalid_data = {
        "task_id": "",  # Invalid empty task_id
        "task_title": "",  # Invalid empty title
        "task_description": "This should fail"
    }
    
    passed, response_data = run_test(
        "Invalid Parameters Test",
        f"{API_PREFIX}/task/execute",
        method="POST",
        data=invalid_data,
        expected_status=400  # Expecting error
    )
    
    error_test_results.append({
        "test": "Invalid Parameters",
        "expected_error": True,
        "got_error": not passed,
        "passed": not passed  # We expect this to fail
    })
    
    # Test 2: Non-existent task status
    print(f"\n🧪 Test 2: Non-existent Task Status")
    fake_task_id = f"non-existent-{uuid.uuid4()}"
    
    passed, response_data = run_test(
        "Non-existent Task Status",
        f"{API_PREFIX}/task/execution-status/{fake_task_id}",
        method="GET"
    )
    
    error_test_results.append({
        "test": "Non-existent Task Status",
        "expected_error": False,  # Should return empty status, not error
        "got_error": not passed,
        "passed": True  # Any response is acceptable
    })
    
    # Test 3: Task analysis with missing data
    print(f"\n🧪 Test 3: Task Analysis Missing Data")
    missing_data = {
        "task_description": "Description without title"
        # Missing task_title
    }
    
    passed, response_data = run_test(
        "Missing Task Title Test",
        f"{API_PREFIX}/task/analyze",
        method="POST",
        data=missing_data,
        expected_status=400
    )
    
    error_test_results.append({
        "test": "Missing Task Title",
        "expected_error": True,
        "got_error": not passed,
        "passed": not passed
    })
    
    return error_test_results

def test_templates():
    """Test the /api/agent/plans/templates endpoint"""
    print(f"\n📋 TESTING PLAN TEMPLATES")
    
    passed, response_data = run_test(
        "Plan Templates Retrieval",
        f"{API_PREFIX}/plans/templates",
        method="GET",
        expected_keys=["success", "templates"]
    )
    
    if not passed:
        return {"templates_available": False}
    
    templates = response_data.get("templates", {})
    
    print(f"📋 Available Templates ({len(templates)}):")
    
    template_analysis = {}
    expected_templates = [
        "web_development", "data_analysis", "file_processing", 
        "system_administration", "research", "automation", "general"
    ]
    
    for template_key, template_data in templates.items():
        print(f"   🏷️  {template_key}:")
        print(f"      Name: {template_data.get('name', 'Unknown')}")
        print(f"      Description: {template_data.get('description', 'No description')}")
        print(f"      Steps: {template_data.get('steps', 0)}")
        print(f"      Duration: {template_data.get('estimated_duration', 0)} seconds")
        print(f"      Complexity: {template_data.get('complexity', 'Unknown')}")
        print(f"      Required Tools: {template_data.get('required_tools', [])}")
        
        template_analysis[template_key] = {
            "name": template_data.get('name'),
            "steps": template_data.get('steps', 0),
            "duration": template_data.get('estimated_duration', 0),
            "complexity": template_data.get('complexity'),
            "tools": template_data.get('required_tools', [])
        }
    
    # Check if all expected templates are present
    missing_templates = [t for t in expected_templates if t not in templates]
    extra_templates = [t for t in templates if t not in expected_templates]
    
    print(f"\n📊 Template Analysis:")
    print(f"   Expected Templates: {len(expected_templates)}")
    print(f"   Found Templates: {len(templates)}")
    print(f"   Missing Templates: {missing_templates}")
    print(f"   Extra Templates: {extra_templates}")
    
    return {
        "templates_available": True,
        "template_count": len(templates),
        "templates": template_analysis,
        "missing_templates": missing_templates,
        "extra_templates": extra_templates,
        "all_expected_present": len(missing_templates) == 0
    }

def print_comprehensive_summary():
    """Print comprehensive test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print(f"🎯 EXECUTION ENGINE COMPREHENSIVE TEST SUMMARY")
    print(f"Timestamp: {test_results['timestamp']}")
    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print("="*80)
    
    # Categorize results by functionality
    categories = {
        "Task Analysis": [],
        "Plan Generation": [],
        "Execution Engine": [],
        "Tool Coordination": [],
        "Error Handling": [],
        "Templates": []
    }
    
    for test in test_results["tests"]:
        test_name = test["name"]
        if "Analysis" in test_name:
            categories["Task Analysis"].append(test)
        elif "Plan" in test_name:
            categories["Plan Generation"].append(test)
        elif "Execution" in test_name or "Status" in test_name:
            categories["Execution Engine"].append(test)
        elif "Coordination" in test_name or "Tools" in test_name:
            categories["Tool Coordination"].append(test)
        elif "Error" in test_name or "Invalid" in test_name or "Missing" in test_name:
            categories["Error Handling"].append(test)
        elif "Template" in test_name:
            categories["Templates"].append(test)
    
    print(f"\n📊 RESULTS BY FUNCTIONALITY:")
    for category, tests in categories.items():
        if tests:
            passed_count = sum(1 for t in tests if t["passed"])
            total_count = len(tests)
            print(f"\n🔹 {category}: {passed_count}/{total_count} passed")
            for test in tests:
                status = "✅" if test["passed"] else "❌"
                print(f"   {status} {test['name']}")
    
    # Print failed tests details
    if failed > 0:
        print(f"\n❌ FAILED TESTS DETAILS:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"\n🔸 {test['name']} ({test['endpoint']})")
                if "error" in test:
                    print(f"   Error: {test['error']}")
                elif "status_code" in test and "expected_status" in test:
                    print(f"   Expected status {test['expected_status']}, got {test['status_code']}")
                if "missing_keys" in test and test["missing_keys"]:
                    print(f"   Missing keys: {', '.join(test['missing_keys'])}")

def main():
    """Main test execution function"""
    print(f"🚀 Starting Execution Engine Comprehensive Testing")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Task Analysis Testing
        print(f"\n" + "="*80)
        print(f"🔍 PHASE 1: TASK ANALYSIS TESTING")
        print(f"="*80)
        analysis_results = test_task_analysis()
        
        # 2. Plan Generation Testing
        print(f"\n" + "="*80)
        print(f"📋 PHASE 2: PLAN GENERATION TESTING")
        print(f"="*80)
        plan_results = test_plan_generation()
        
        # 3. Execution Engine Testing
        print(f"\n" + "="*80)
        print(f"⚙️ PHASE 3: EXECUTION ENGINE TESTING")
        print(f"="*80)
        execution_results = test_execution_engine()
        
        # 4. Tool Coordination Testing
        print(f"\n" + "="*80)
        print(f"🔧 PHASE 4: TOOL COORDINATION TESTING")
        print(f"="*80)
        coordination_results = test_tool_coordination()
        
        # 5. Error Handling Testing
        print(f"\n" + "="*80)
        print(f"❌ PHASE 5: ERROR HANDLING TESTING")
        print(f"="*80)
        error_results = test_error_handling()
        
        # 6. Templates Testing
        print(f"\n" + "="*80)
        print(f"📋 PHASE 6: TEMPLATES TESTING")
        print(f"="*80)
        template_results = test_templates()
        
        # Print comprehensive summary
        print_comprehensive_summary()
        
        # Final assessment
        success_rate = test_results["summary"]["passed"] / test_results["summary"]["total"] * 100
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        print(f"Overall Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"✅ EXECUTION ENGINE INTEGRATION: EXCELLENT")
        elif success_rate >= 60:
            print(f"⚠️ EXECUTION ENGINE INTEGRATION: GOOD (needs minor improvements)")
        else:
            print(f"❌ EXECUTION ENGINE INTEGRATION: NEEDS SIGNIFICANT WORK")
        
        print(f"\n📋 EXECUTION ENGINE PHASE 3.2 TESTING COMPLETED")
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Testing interrupted by user")
        print_comprehensive_summary()
    except Exception as e:
        print(f"\n❌ Testing failed with exception: {str(e)}")
        print_comprehensive_summary()

if __name__ == "__main__":
    main()