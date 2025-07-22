#!/usr/bin/env python3
"""
TARGETED MITOSIS VALENCIA BARS TEST - SPECIFIC ENDPOINTS
Testing the specific endpoints mentioned in the review request
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

print(f"🎯 TARGETED MITOSIS VALENCIA BARS ENDPOINT TEST")
print(f"Testing specific endpoints from review request")

def test_specific_endpoints():
    """Test the specific endpoints mentioned in the review request"""
    
    # 1. POST /api/agent/chat (para iniciar la tarea)
    print(f"\n{'='*60}")
    print(f"1. Testing POST /api/agent/chat")
    print(f"{'='*60}")
    
    chat_url = f"{BASE_URL}{API_PREFIX}/chat"
    chat_data = {
        "message": "Genera informe sobre los mejores bares de Valencia en 2025"
    }
    
    try:
        response = requests.post(chat_url, json=chat_data, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id")
            print(f"✅ Chat endpoint working - Task ID: {task_id}")
            print(f"Response contains plan: {'plan' in data}")
            print(f"Memory used: {data.get('memory_used', False)}")
            
            # 2. GET /api/agent/get-task-plan/<task_id>
            if task_id:
                print(f"\n{'='*60}")
                print(f"2. Testing GET /api/agent/get-task-plan/{task_id}")
                print(f"{'='*60}")
                
                plan_url = f"{BASE_URL}{API_PREFIX}/get-task-plan/{task_id}"
                plan_response = requests.get(plan_url, timeout=30)
                print(f"Status: {plan_response.status_code}")
                if plan_response.status_code == 200:
                    plan_data = plan_response.json()
                    print(f"✅ Plan endpoint working")
                    print(f"Plan has steps: {'plan' in plan_data and 'steps' in plan_data.get('plan', {})}")
                    if 'plan' in plan_data and 'steps' in plan_data['plan']:
                        steps = plan_data['plan']['steps']
                        print(f"Number of steps: {len(steps)}")
                else:
                    print(f"❌ Plan endpoint failed: {plan_response.status_code}")
                
                # 3. POST /api/agent/start-task-execution/<task_id>
                print(f"\n{'='*60}")
                print(f"3. Testing POST /api/agent/start-task-execution/{task_id}")
                print(f"{'='*60}")
                
                exec_url = f"{BASE_URL}{API_PREFIX}/start-task-execution/{task_id}"
                exec_response = requests.post(exec_url, timeout=30)
                print(f"Status: {exec_response.status_code}")
                if exec_response.status_code == 200:
                    exec_data = exec_response.json()
                    print(f"✅ Execution start endpoint working")
                    print(f"Execution started: {exec_data.get('success', False)}")
                else:
                    print(f"❌ Execution start failed: {exec_response.status_code}")
                
                # Wait a bit for execution to progress
                time.sleep(3)
                
                # 4. POST /api/agent/execute-step/<task_id>/<step_id>
                print(f"\n{'='*60}")
                print(f"4. Testing POST /api/agent/execute-step/{task_id}/step_1")
                print(f"{'='*60}")
                
                step_url = f"{BASE_URL}{API_PREFIX}/execute-step/{task_id}/step_1"
                step_response = requests.post(step_url, timeout=60)
                print(f"Status: {step_response.status_code}")
                if step_response.status_code == 200:
                    step_data = step_response.json()
                    print(f"✅ Step execution endpoint working")
                    print(f"Step completed: {step_data.get('step_completed', False)}")
                else:
                    print(f"❌ Step execution failed: {step_response.status_code}")
                
                # Wait for file generation
                time.sleep(2)
                
                # 5. GET /api/agent/get-task-files/<task_id>
                print(f"\n{'='*60}")
                print(f"5. Testing GET /api/agent/get-task-files/{task_id}")
                print(f"{'='*60}")
                
                files_url = f"{BASE_URL}{API_PREFIX}/get-task-files/{task_id}"
                files_response = requests.get(files_url, timeout=30)
                print(f"Status: {files_response.status_code}")
                if files_response.status_code == 200:
                    files_data = files_response.json()
                    print(f"✅ Files endpoint working")
                    files = files_data.get('files', [])
                    print(f"Number of files: {len(files)}")
                    for file_info in files:
                        print(f"  - {file_info.get('name', 'unnamed')} ({file_info.get('size', 0)} bytes)")
                else:
                    print(f"❌ Files endpoint failed: {files_response.status_code}")
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error testing chat endpoint: {e}")
        return
    
    # 6. GET /api/agent/status
    print(f"\n{'='*60}")
    print(f"6. Testing GET /api/agent/status")
    print(f"{'='*60}")
    
    status_url = f"{BASE_URL}{API_PREFIX}/status"
    try:
        status_response = requests.get(status_url, timeout=30)
        print(f"Status: {status_response.status_code}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"✅ Status endpoint working")
            print(f"Ollama connected: {status_data.get('ollama', {}).get('connected', False)}")
            print(f"Tools available: {status_data.get('tools', [])}")
            print(f"Memory enabled: {status_data.get('memory', {}).get('enabled', False)}")
        else:
            print(f"❌ Status endpoint failed: {status_response.status_code}")
    except Exception as e:
        print(f"❌ Error testing status endpoint: {e}")

def test_success_criteria():
    """Test the success criteria from the review request"""
    print(f"\n{'='*60}")
    print(f"TESTING SUCCESS CRITERIA")
    print(f"{'='*60}")
    
    criteria_results = {
        "plan_generated": False,
        "steps_executed": False,
        "files_generated": False,
        "task_completed": False,
        "relevant_content": False
    }
    
    # Test plan generation
    chat_url = f"{BASE_URL}{API_PREFIX}/chat"
    chat_data = {"message": "Genera informe sobre los mejores bares de Valencia en 2025"}
    
    try:
        response = requests.post(chat_url, json=chat_data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id")
            
            # Check if plan was generated
            if 'plan' in data and data['plan']:
                criteria_results["plan_generated"] = True
                print(f"✅ Plan generated correctly")
                
                plan = data['plan']
                if 'steps' in plan and len(plan['steps']) > 0:
                    print(f"   - Plan has {len(plan['steps'])} steps")
                    
                    # Check if steps are relevant to Valencia bars
                    valencia_keywords = ['valencia', 'bares', 'bar', 'informe', 'búsqueda', 'search']
                    relevant_steps = 0
                    for step in plan['steps']:
                        step_text = (step.get('description', '') + ' ' + step.get('title', '')).lower()
                        if any(keyword in step_text for keyword in valencia_keywords):
                            relevant_steps += 1
                    
                    if relevant_steps > 0:
                        criteria_results["relevant_content"] = True
                        print(f"   - {relevant_steps} steps are relevant to Valencia bars")
            else:
                print(f"❌ No plan generated")
            
            # Check for file generation after some time
            if task_id:
                time.sleep(5)  # Wait for execution
                
                files_url = f"{BASE_URL}{API_PREFIX}/get-task-files/{task_id}"
                files_response = requests.get(files_url, timeout=30)
                if files_response.status_code == 200:
                    files_data = files_response.json()
                    files = files_data.get('files', [])
                    if len(files) > 0:
                        criteria_results["files_generated"] = True
                        print(f"✅ Files generated: {len(files)} files")
                        
                        # Check if files contain Valencia bars content
                        for file_info in files:
                            file_name = file_info.get('name', '').lower()
                            if 'valencia' in file_name or 'bar' in file_name:
                                criteria_results["relevant_content"] = True
                                print(f"   - Relevant file: {file_info.get('name')}")
                    else:
                        print(f"❌ No files generated")
                
                # Check if steps were executed
                plan_url = f"{BASE_URL}{API_PREFIX}/get-task-plan/{task_id}"
                plan_response = requests.get(plan_url, timeout=30)
                if plan_response.status_code == 200:
                    plan_data = plan_response.json()
                    if 'stats' in plan_data:
                        stats = plan_data['stats']
                        completed_steps = stats.get('completed_steps', 0)
                        if completed_steps > 0:
                            criteria_results["steps_executed"] = True
                            print(f"✅ Steps executed: {completed_steps} completed")
                        
                        if stats.get('status') == 'completed':
                            criteria_results["task_completed"] = True
                            print(f"✅ Task completed successfully")
    
    except Exception as e:
        print(f"❌ Error testing success criteria: {e}")
    
    # Print final criteria assessment
    print(f"\n{'='*60}")
    print(f"SUCCESS CRITERIA ASSESSMENT")
    print(f"{'='*60}")
    
    total_criteria = len(criteria_results)
    passed_criteria = sum(criteria_results.values())
    
    for criterion, passed in criteria_results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {criterion.replace('_', ' ').title()}: {'PASSED' if passed else 'FAILED'}")
    
    print(f"\nOverall Success Rate: {passed_criteria}/{total_criteria} ({passed_criteria/total_criteria*100:.1f}%)")
    
    if passed_criteria >= total_criteria * 0.8:
        print(f"🎉 SYSTEM IS WORKING CORRECTLY FOR VALENCIA BARS TASK")
    elif passed_criteria >= total_criteria * 0.6:
        print(f"⚠️ SYSTEM IS MOSTLY WORKING WITH MINOR ISSUES")
    else:
        print(f"❌ SYSTEM HAS SIGNIFICANT ISSUES")

if __name__ == "__main__":
    test_specific_endpoints()
    test_success_criteria()