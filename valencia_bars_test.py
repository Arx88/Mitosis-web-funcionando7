#!/usr/bin/env python3
"""
COMPREHENSIVE MITOSIS SYSTEM TEST FOR VALENCIA BARS REPORT
Testing the complete system to execute: "Genera informe sobre los mejores bares de Valencia en 2025"

This test verifies:
1. Chat endpoint with specific task message
2. Plan generation for Valencia bars research
3. Autonomous execution capabilities
4. File generation and deliverables
5. Complete task workflow
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path

# Configuration - Use local URL for testing
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"

print(f"🧪 COMPREHENSIVE MITOSIS VALENCIA BARS REPORT TEST")
print(f"Using backend URL: {BASE_URL}")
print(f"Target task: 'Genera informe sobre los mejores bares de Valencia en 2025'")

# Test results tracking
test_results = {
    "timestamp": datetime.now().isoformat(),
    "task_message": "Genera informe sobre los mejores bares de Valencia en 2025",
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
}

def log_test_result(name, passed, details=None, error=None):
    """Log test result"""
    test_results["summary"]["total"] += 1
    if passed:
        test_results["summary"]["passed"] += 1
        print(f"✅ {name}: PASSED")
    else:
        test_results["summary"]["failed"] += 1
        print(f"❌ {name}: FAILED")
        if error:
            print(f"   Error: {error}")
    
    test_results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details,
        "error": error,
        "timestamp": datetime.now().isoformat()
    })

def test_chat_endpoint_valencia_task():
    """Test 1: Chat endpoint with Valencia bars task"""
    print(f"\n{'='*80}")
    print(f"TEST 1: CHAT ENDPOINT - Valencia Bars Task")
    print(f"{'='*80}")
    
    try:
        url = f"{BASE_URL}{API_PREFIX}/chat"
        data = {
            "message": "Genera informe sobre los mejores bares de Valencia en 2025",
            "context": {
                "task_id": f"valencia-bars-{uuid.uuid4()}",
                "previous_messages": []
            }
        }
        
        print(f"URL: {url}")
        print(f"DATA: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        if status_code == 200:
            response_data = response.json()
            print(f"RESPONSE KEYS: {list(response_data.keys())}")
            
            # Check for expected keys
            expected_keys = ["response", "task_id", "memory_used"]
            missing_keys = [key for key in expected_keys if key not in response_data]
            
            if not missing_keys:
                task_id = response_data.get("task_id")
                memory_used = response_data.get("memory_used")
                response_text = response_data.get("response", "")
                
                print(f"Task ID: {task_id}")
                print(f"Memory Used: {memory_used}")
                print(f"Response: {response_text[:200]}...")
                
                # Check if response is relevant to Valencia bars
                valencia_indicators = ["valencia", "bares", "bar", "informe", "2025"]
                relevant = any(indicator.lower() in response_text.lower() for indicator in valencia_indicators)
                
                log_test_result(
                    "Chat Endpoint - Valencia Task",
                    True,
                    {
                        "task_id": task_id,
                        "memory_used": memory_used,
                        "response_relevant": relevant,
                        "response_length": len(response_text)
                    }
                )
                return True, response_data
            else:
                log_test_result(
                    "Chat Endpoint - Valencia Task",
                    False,
                    error=f"Missing keys: {missing_keys}"
                )
                return False, None
        else:
            log_test_result(
                "Chat Endpoint - Valencia Task",
                False,
                error=f"HTTP {status_code}"
            )
            return False, None
            
    except Exception as e:
        log_test_result(
            "Chat Endpoint - Valencia Task",
            False,
            error=str(e)
        )
        return False, None

def test_plan_generation(task_id):
    """Test 2: Plan generation for Valencia bars task"""
    print(f"\n{'='*80}")
    print(f"TEST 2: PLAN GENERATION - Valencia Bars Research Plan")
    print(f"{'='*80}")
    
    try:
        # Test get-task-plan endpoint
        url = f"{BASE_URL}{API_PREFIX}/get-task-plan/{task_id}"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        if status_code == 200:
            plan_data = response.json()
            print(f"PLAN RESPONSE KEYS: {list(plan_data.keys())}")
            
            # Check for plan structure
            if "plan" in plan_data:
                plan = plan_data["plan"]
                steps = plan.get("steps", [])
                
                print(f"Plan Title: {plan.get('title', 'N/A')}")
                print(f"Plan Description: {plan.get('description', 'N/A')}")
                print(f"Number of Steps: {len(steps)}")
                
                # Verify steps are relevant to Valencia bars research
                relevant_steps = 0
                for i, step in enumerate(steps):
                    step_description = step.get("description", "")
                    print(f"Step {i+1}: {step_description}")
                    
                    # Check if step is relevant to Valencia bars research
                    valencia_keywords = ["valencia", "bares", "bar", "búsqueda", "search", "web", "informe", "report"]
                    if any(keyword.lower() in step_description.lower() for keyword in valencia_keywords):
                        relevant_steps += 1
                
                plan_quality = relevant_steps >= len(steps) * 0.5  # At least 50% relevant steps
                
                log_test_result(
                    "Plan Generation - Valencia Bars",
                    True,
                    {
                        "total_steps": len(steps),
                        "relevant_steps": relevant_steps,
                        "plan_quality": plan_quality,
                        "plan_title": plan.get('title', 'N/A')
                    }
                )
                return True, plan_data
            else:
                log_test_result(
                    "Plan Generation - Valencia Bars",
                    False,
                    error="No plan found in response"
                )
                return False, None
        else:
            log_test_result(
                "Plan Generation - Valencia Bars",
                False,
                error=f"HTTP {status_code}"
            )
            return False, None
            
    except Exception as e:
        log_test_result(
            "Plan Generation - Valencia Bars",
            False,
            error=str(e)
        )
        return False, None

def test_task_execution(task_id):
    """Test 3: Task execution capabilities"""
    print(f"\n{'='*80}")
    print(f"TEST 3: TASK EXECUTION - Autonomous Execution")
    print(f"{'='*80}")
    
    try:
        # Test start-task-execution endpoint
        url = f"{BASE_URL}{API_PREFIX}/start-task-execution/{task_id}"
        print(f"URL: {url}")
        
        response = requests.post(url, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        if status_code == 200:
            execution_data = response.json()
            print(f"EXECUTION RESPONSE: {json.dumps(execution_data, indent=2)}")
            
            # Check execution status
            execution_started = execution_data.get("execution_started", False)
            message = execution_data.get("message", "")
            
            log_test_result(
                "Task Execution - Start",
                execution_started,
                {
                    "execution_started": execution_started,
                    "message": message
                }
            )
            return execution_started, execution_data
        else:
            log_test_result(
                "Task Execution - Start",
                False,
                error=f"HTTP {status_code}"
            )
            return False, None
            
    except Exception as e:
        log_test_result(
            "Task Execution - Start",
            False,
            error=str(e)
        )
        return False, None

def test_step_execution(task_id, step_id="step_1"):
    """Test 4: Individual step execution"""
    print(f"\n{'='*80}")
    print(f"TEST 4: STEP EXECUTION - Execute Individual Step")
    print(f"{'='*80}")
    
    try:
        # Test execute-step endpoint
        url = f"{BASE_URL}{API_PREFIX}/execute-step/{task_id}/{step_id}"
        print(f"URL: {url}")
        
        response = requests.post(url, timeout=60)  # Longer timeout for step execution
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        if status_code == 200:
            step_data = response.json()
            print(f"STEP EXECUTION KEYS: {list(step_data.keys())}")
            
            # Check step execution results
            step_completed = step_data.get("step_completed", False)
            step_result = step_data.get("step_result", {})
            
            print(f"Step Completed: {step_completed}")
            print(f"Step Result: {json.dumps(step_result, indent=2)}")
            
            log_test_result(
                "Step Execution - Individual Step",
                step_completed,
                {
                    "step_completed": step_completed,
                    "step_result_keys": list(step_result.keys()) if step_result else []
                }
            )
            return step_completed, step_data
        else:
            log_test_result(
                "Step Execution - Individual Step",
                False,
                error=f"HTTP {status_code}"
            )
            return False, None
            
    except Exception as e:
        log_test_result(
            "Step Execution - Individual Step",
            False,
            error=str(e)
        )
        return False, None

def test_file_generation(task_id):
    """Test 5: File generation and deliverables"""
    print(f"\n{'='*80}")
    print(f"TEST 5: FILE GENERATION - Valencia Bars Report Files")
    print(f"{'='*80}")
    
    try:
        # Test get-task-files endpoint
        url = f"{BASE_URL}{API_PREFIX}/get-task-files/{task_id}"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        if status_code == 200:
            files_data = response.json()
            print(f"FILES RESPONSE KEYS: {list(files_data.keys())}")
            
            files = files_data.get("files", [])
            print(f"Number of files: {len(files)}")
            
            # Check for relevant files
            relevant_files = 0
            for file_info in files:
                file_name = file_info.get("name", "")
                file_size = file_info.get("size", 0)
                file_type = file_info.get("mime_type", "")
                
                print(f"File: {file_name} ({file_size} bytes, {file_type})")
                
                # Check if file is relevant to Valencia bars
                valencia_keywords = ["valencia", "bares", "bar", "informe", "report"]
                if any(keyword.lower() in file_name.lower() for keyword in valencia_keywords):
                    relevant_files += 1
            
            files_generated = len(files) > 0
            
            log_test_result(
                "File Generation - Valencia Report",
                files_generated,
                {
                    "total_files": len(files),
                    "relevant_files": relevant_files,
                    "files_list": [f.get("name", "unnamed") for f in files]
                }
            )
            return files_generated, files_data
        else:
            log_test_result(
                "File Generation - Valencia Report",
                False,
                error=f"HTTP {status_code}"
            )
            return False, None
            
    except Exception as e:
        log_test_result(
            "File Generation - Valencia Report",
            False,
            error=str(e)
        )
        return False, None

def test_agent_status():
    """Test 6: Agent status and health"""
    print(f"\n{'='*80}")
    print(f"TEST 6: AGENT STATUS - System Health Check")
    print(f"{'='*80}")
    
    try:
        # Test agent status endpoint
        url = f"{BASE_URL}{API_PREFIX}/status"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        if status_code == 200:
            status_data = response.json()
            print(f"STATUS RESPONSE KEYS: {list(status_data.keys())}")
            
            # Check key status indicators
            ollama_status = status_data.get("ollama", {})
            tools_count = status_data.get("tools_count", 0)
            memory_enabled = status_data.get("memory", {}).get("enabled", False)
            
            print(f"Ollama Connected: {ollama_status.get('connected', False)}")
            print(f"Ollama Endpoint: {ollama_status.get('endpoint', 'N/A')}")
            print(f"Tools Available: {tools_count}")
            print(f"Memory Enabled: {memory_enabled}")
            
            system_healthy = (
                ollama_status.get('connected', False) and
                tools_count > 0 and
                memory_enabled
            )
            
            log_test_result(
                "Agent Status - System Health",
                system_healthy,
                {
                    "ollama_connected": ollama_status.get('connected', False),
                    "tools_count": tools_count,
                    "memory_enabled": memory_enabled,
                    "ollama_endpoint": ollama_status.get('endpoint', 'N/A')
                }
            )
            return system_healthy, status_data
        else:
            log_test_result(
                "Agent Status - System Health",
                False,
                error=f"HTTP {status_code}"
            )
            return False, None
            
    except Exception as e:
        log_test_result(
            "Agent Status - System Health",
            False,
            error=str(e)
        )
        return False, None

def test_initialize_task():
    """Test 7: Initialize task endpoint for autonomous execution"""
    print(f"\n{'='*80}")
    print(f"TEST 7: INITIALIZE TASK - Autonomous Plan Generation")
    print(f"{'='*80}")
    
    try:
        # Test initialize-task endpoint
        url = f"{BASE_URL}{API_PREFIX}/initialize-task"
        data = {
            "message": "Genera informe sobre los mejores bares de Valencia en 2025",
            "auto_execute": True
        }
        
        print(f"URL: {url}")
        print(f"DATA: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=60)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        if status_code == 200:
            init_data = response.json()
            print(f"INITIALIZE RESPONSE KEYS: {list(init_data.keys())}")
            
            # Check initialization results
            task_id = init_data.get("task_id")
            plan_generated = init_data.get("plan_generated", False)
            execution_started = init_data.get("execution_started", False)
            
            print(f"Task ID: {task_id}")
            print(f"Plan Generated: {plan_generated}")
            print(f"Execution Started: {execution_started}")
            
            initialization_success = task_id is not None and plan_generated
            
            log_test_result(
                "Initialize Task - Autonomous",
                initialization_success,
                {
                    "task_id": task_id,
                    "plan_generated": plan_generated,
                    "execution_started": execution_started
                }
            )
            return initialization_success, init_data
        else:
            log_test_result(
                "Initialize Task - Autonomous",
                False,
                error=f"HTTP {status_code}"
            )
            return False, None
            
    except Exception as e:
        log_test_result(
            "Initialize Task - Autonomous",
            False,
            error=str(e)
        )
        return False, None

def print_final_summary():
    """Print comprehensive test summary"""
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE VALENCIA BARS REPORT TEST SUMMARY")
    print(f"{'='*80}")
    
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print(f"Test Target: {test_results['task_message']}")
    print(f"Test Timestamp: {test_results['timestamp']}")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    print(f"\nDETAILED RESULTS:")
    for test in test_results["tests"]:
        status = "✅ PASSED" if test["passed"] else "❌ FAILED"
        print(f"  {status}: {test['name']}")
        if not test["passed"] and test.get("error"):
            print(f"    Error: {test['error']}")
    
    print(f"\n{'='*80}")
    
    # Determine overall system status
    if passed == total:
        print(f"🎉 SYSTEM STATUS: FULLY OPERATIONAL")
        print(f"✅ Mitosis can successfully execute Valencia bars report task")
    elif passed >= total * 0.75:
        print(f"⚠️ SYSTEM STATUS: MOSTLY OPERATIONAL")
        print(f"✅ Mitosis can execute Valencia bars report with minor issues")
    elif passed >= total * 0.5:
        print(f"⚠️ SYSTEM STATUS: PARTIALLY OPERATIONAL")
        print(f"❌ Mitosis has significant issues executing Valencia bars report")
    else:
        print(f"❌ SYSTEM STATUS: NOT OPERATIONAL")
        print(f"❌ Mitosis cannot execute Valencia bars report task")
    
    print(f"{'='*80}")

def main():
    """Run comprehensive Valencia bars report test"""
    print(f"🚀 Starting comprehensive Mitosis system test...")
    print(f"Target: Generate Valencia bars report for 2025")
    
    # Test 1: Chat endpoint with Valencia task
    chat_success, chat_data = test_chat_endpoint_valencia_task()
    task_id = None
    if chat_success and chat_data:
        task_id = chat_data.get("task_id")
    
    # Test 2: Plan generation (if we have a task_id)
    if task_id:
        test_plan_generation(task_id)
        test_task_execution(task_id)
        test_step_execution(task_id)
        test_file_generation(task_id)
    
    # Test 3: Agent status
    test_agent_status()
    
    # Test 4: Initialize task for autonomous execution
    test_initialize_task()
    
    # Print final summary
    print_final_summary()
    
    # Return overall success
    return test_results["summary"]["passed"] >= test_results["summary"]["total"] * 0.75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)