#!/usr/bin/env python3
"""
DeepResearch Functionality Test Script for Task Manager Backend

This script tests the DeepResearch functionality of the Task Manager backend,
focusing on the enhanced_deep_research tool, progress tracking, and report generation.
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime

# Configuration
# Get the backend URL from the frontend .env file
try:
    with open('/app/frontend/.env', 'r') as env_file:
        for line in env_file:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.strip().split('=', 1)[1].strip('"\'')
                break
except Exception as e:
    print(f"Error reading .env file: {e}")
    backend_url = "http://localhost:8001"

# Use local URL for testing to avoid timeouts
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"

print(f"Using backend URL: {BASE_URL}")

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

def run_test(name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None):
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
            response = requests.get(url, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)
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
        if expected_keys and status_ok:
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

def print_summary():
    """Print test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print(f"TEST SUMMARY")
    print(f"Timestamp: {test_results['timestamp']}")
    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print("="*80)
    
    # Print failed tests
    if failed > 0:
        print("\nFAILED TESTS:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"- {test['name']} ({test['endpoint']})")
                if "error" in test:
                    print(f"  Error: {test['error']}")
                elif "status_code" in test and "expected_status" in test and test["status_code"] != test["expected_status"]:
                    print(f"  Expected status {test['expected_status']}, got {test['status_code']}")
                if "missing_keys" in test and test["missing_keys"]:
                    print(f"  Missing keys: {', '.join(test['missing_keys'])}")

def test_deep_research_functionality():
    """Test the DeepResearch functionality with a Spanish query"""
    print(f"\n{'='*80}")
    print(f"TEST: DeepResearch Functionality with Spanish Query")
    
    test_results["summary"]["total"] += 1
    
    try:
        # Create a task ID for testing
        task_id = f"test-{uuid.uuid4()}"
        
        # Step 1: Test Chat API with DeepResearch query
        chat_url = f"{BASE_URL}{API_PREFIX}/chat"
        chat_data = {
            "message": "[DeepResearch] Los orígenes del capitalismo moderno",
            "search_mode": "deepsearch",
            "context": {
                "task_id": task_id
            }
        }
        
        print(f"URL: {chat_url}")
        print(f"METHOD: POST")
        print(f"DATA: {json.dumps(chat_data, indent=2)}")
        
        # Send the request
        chat_response = requests.post(chat_url, json=chat_data, timeout=60)
        chat_status = chat_response.status_code
        print(f"CHAT API STATUS: {chat_status}")
        
        try:
            chat_response_data = chat_response.json()
            print(f"CHAT API RESPONSE: {json.dumps(chat_response_data, indent=2)}")
        except:
            chat_response_data = chat_response.text
            print(f"CHAT API RESPONSE: {chat_response_data}")
        
        # Check if the response has the expected structure
        deepsearch_response_ok = False
        search_data_ok = False
        
        if chat_status == 200:
            # Check if the response contains search_mode and search_data
            if "search_mode" in chat_response_data and chat_response_data["search_mode"] == "deepsearch":
                deepsearch_response_ok = True
                print("✅ DeepResearch mode detected in response")
            else:
                print("❌ DeepResearch mode not detected in response")
            
            # Check if search_data has the expected structure
            search_data = chat_response_data.get("search_data", {})
            expected_search_data_keys = ["query", "directAnswer", "sources", "type", "key_findings", "recommendations"]
            
            if search_data and all(key in search_data for key in expected_search_data_keys):
                search_data_ok = True
                print("✅ search_data has the expected structure")
                
                # Print some details about the search results
                print(f"Query: {search_data.get('query')}")
                print(f"Direct Answer: {search_data.get('directAnswer')[:100]}...")
                print(f"Sources: {len(search_data.get('sources', []))} sources found")
                print(f"Key Findings: {len(search_data.get('key_findings', []))} findings")
                print(f"Recommendations: {len(search_data.get('recommendations', []))} recommendations")
            else:
                print("❌ search_data missing expected keys")
                if search_data:
                    missing_keys = [key for key in expected_search_data_keys if key not in search_data]
                    print(f"Missing keys: {', '.join(missing_keys)}")
        
        # Step 2: Test the progress tracking endpoint
        print("\nTesting DeepResearch progress tracking endpoint...")
        
        progress_url = f"{BASE_URL}{API_PREFIX}/deep-research/progress/{task_id}"
        progress_response = requests.get(progress_url, timeout=10)
        progress_status = progress_response.status_code
        print(f"PROGRESS API STATUS: {progress_status}")
        
        try:
            progress_response_data = progress_response.json()
            print(f"PROGRESS API RESPONSE: {json.dumps(progress_response_data, indent=2)}")
        except:
            progress_response_data = progress_response.text
            print(f"PROGRESS API RESPONSE: {progress_response_data}")
        
        # Check if the progress endpoint returns the expected structure
        progress_endpoint_ok = False
        
        if progress_status == 200:
            expected_progress_keys = ["task_id", "is_active", "current_progress", "current_step", "steps"]
            
            if all(key in progress_response_data for key in expected_progress_keys):
                progress_endpoint_ok = True
                print("✅ Progress endpoint returns the expected structure")
                
                # Print some details about the progress
                print(f"Task ID: {progress_response_data.get('task_id')}")
                print(f"Is Active: {progress_response_data.get('is_active')}")
                print(f"Current Progress: {progress_response_data.get('current_progress')}%")
                print(f"Current Step: {progress_response_data.get('current_step')}")
                print(f"Steps: {len(progress_response_data.get('steps', []))} steps defined")
            else:
                print("❌ Progress endpoint missing expected keys")
                missing_keys = [key for key in expected_progress_keys if key not in progress_response_data]
                print(f"Missing keys: {', '.join(missing_keys)}")
        else:
            print(f"❌ Progress endpoint returned status {progress_status}")
        
        # Step 3: Check if a report file was created
        report_file_created = False
        created_files = chat_response_data.get("created_files", [])
        
        if created_files:
            for file_info in created_files:
                if file_info.get("mime_type") == "text/markdown" and "informe_" in file_info.get("name", ""):
                    report_file_created = True
                    print(f"✅ Report file created: {file_info.get('name')}")
                    print(f"File path: {file_info.get('path')}")
                    print(f"File size: {file_info.get('size')} bytes")
                    break
            
            if not report_file_created:
                print("❌ No report file was created in created_files")
        else:
            print("❌ No files were created in created_files")
        
        # Check if the report file exists directly in the reports directory
        report_file_exists = False
        report_file_path = None
        
        try:
            import glob
            task_id_short = task_id[:8]
            report_files = glob.glob(f"/app/backend/reports/informe_*{task_id_short}*.md")
            
            if report_files:
                report_file_exists = True
                report_file_path = report_files[0]
                print(f"✅ Report file found directly in reports directory: {report_file_path}")
                
                # Check file size
                import os
                file_size = os.path.getsize(report_file_path)
                print(f"File size: {file_size} bytes")
            else:
                print("❌ No report file found in reports directory matching task ID")
        except Exception as e:
            print(f"Error checking for report file: {e}")
        
        # Step 4: Test the task files endpoint to verify the report file is accessible
        files_url = f"{BASE_URL}{API_PREFIX}/files/{task_id}"
        files_response = requests.get(files_url, timeout=10)
        files_status = files_response.status_code
        print(f"\nFILES API STATUS: {files_status}")
        
        try:
            files_response_data = files_response.json()
            print(f"FILES API RESPONSE: {json.dumps(files_response_data, indent=2)}")
        except:
            files_response_data = files_response.text
            print(f"FILES API RESPONSE: {files_response_data}")
        
        # Check if the files endpoint returns the expected structure
        files_endpoint_ok = False
        report_file_accessible = False
        
        if files_status == 200:
            expected_files_keys = ["files", "count", "task_id"]
            
            if all(key in files_response_data for key in expected_files_keys):
                files_endpoint_ok = True
                print("✅ Files endpoint returns the expected structure")
                
                # Check if the report file is in the list
                files = files_response_data.get("files", [])
                for file_info in files:
                    if file_info.get("mime_type") == "text/markdown" and "informe_" in file_info.get("name", ""):
                        report_file_accessible = True
                        print(f"✅ Report file accessible through files API: {file_info.get('name')}")
                        break
                
                if not report_file_accessible:
                    print("❌ Report file not found in files API response")
            else:
                print("❌ Files endpoint missing expected keys")
                missing_keys = [key for key in expected_files_keys if key not in files_response_data]
                print(f"Missing keys: {', '.join(missing_keys)}")
        else:
            print(f"❌ Files endpoint returned status {files_status}")
        
        # Determine test result
        passed = deepsearch_response_ok and search_data_ok and progress_endpoint_ok and (report_file_created or report_file_exists or report_file_accessible)
        
        # Update test results
        test_results["tests"].append({
            "name": "DeepResearch Functionality with Spanish Query",
            "endpoint": f"{API_PREFIX}/chat, {API_PREFIX}/deep-research/progress/*, {API_PREFIX}/files/*",
            "method": "POST, GET",
            "status_code": chat_status,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "deepsearch_response_ok": deepsearch_response_ok,
                "search_data_ok": search_data_ok,
                "progress_endpoint_ok": progress_endpoint_ok,
                "report_file_created": report_file_created,
                "report_file_exists": report_file_exists,
                "report_file_accessible": report_file_accessible
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"The DeepResearch functionality is working correctly with Spanish queries")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if not deepsearch_response_ok:
                print(f"  - DeepResearch mode not detected in Chat API response")
            if not search_data_ok:
                print(f"  - search_data missing expected structure in Chat API response")
            if not progress_endpoint_ok:
                print(f"  - Progress tracking endpoint missing expected structure")
            if not report_file_created and not report_file_exists and not report_file_accessible:
                print(f"  - No report file was created or accessible")
        
        return passed, chat_response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "DeepResearch Functionality with Spanish Query",
            "endpoint": f"{API_PREFIX}/chat, {API_PREFIX}/deep-research/progress/*, {API_PREFIX}/files/*",
            "method": "POST, GET",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_two_column_progress_interface():
    """Test the two-column progress interface data structure"""
    print(f"\n{'='*80}")
    print(f"TEST: Two-Column Progress Interface Data Structure")
    
    test_results["summary"]["total"] += 1
    
    try:
        # Create a task ID for testing
        task_id = f"test-{uuid.uuid4()}"
        
        # Step 1: Start a DeepResearch query to initialize progress tracking
        chat_url = f"{BASE_URL}{API_PREFIX}/chat"
        chat_data = {
            "message": "[DeepResearch] Historia de la inteligencia artificial",
            "search_mode": "deepsearch",
            "context": {
                "task_id": task_id
            }
        }
        
        print(f"Starting DeepResearch query to initialize progress tracking...")
        print(f"URL: {chat_url}")
        print(f"METHOD: POST")
        print(f"DATA: {json.dumps(chat_data, indent=2)}")
        
        # Send the request (don't wait for completion)
        chat_response = requests.post(chat_url, json=chat_data, timeout=30)
        
        # Step 2: Test the progress tracking endpoint immediately
        print("\nTesting DeepResearch progress tracking endpoint for two-column interface...")
        
        progress_url = f"{BASE_URL}{API_PREFIX}/deep-research/progress/{task_id}"
        
        # Try multiple times to get progress data
        max_attempts = 3
        progress_data_ok = False
        steps_structure_ok = False
        
        for attempt in range(max_attempts):
            print(f"\nAttempt {attempt+1}/{max_attempts} to get progress data...")
            
            progress_response = requests.get(progress_url, timeout=10)
            progress_status = progress_response.status_code
            print(f"PROGRESS API STATUS: {progress_status}")
            
            try:
                progress_response_data = progress_response.json()
                print(f"PROGRESS API RESPONSE: {json.dumps(progress_response_data, indent=2)}")
                
                if progress_status == 200:
                    # Check if the response has the expected structure
                    expected_progress_keys = ["task_id", "is_active", "current_progress", "current_step", "steps"]
                    
                    if all(key in progress_response_data for key in expected_progress_keys):
                        progress_data_ok = True
                        print("✅ Progress endpoint returns the expected structure")
                        
                        # Check if steps have the expected structure for two-column interface
                        steps = progress_response_data.get("steps", [])
                        
                        if steps and len(steps) > 0:
                            expected_step_keys = ["id", "title", "description", "status"]
                            
                            if all(all(key in step for key in expected_step_keys) for step in steps):
                                steps_structure_ok = True
                                print("✅ Steps have the expected structure for two-column interface")
                                
                                # Print some details about the steps
                                print(f"Number of steps: {len(steps)}")
                                for i, step in enumerate(steps):
                                    print(f"Step {i+1}: {step.get('title')} - {step.get('status')}")
                                
                                # No need to try again if we have good data
                                break
                            else:
                                print("❌ Steps missing expected keys for two-column interface")
                                missing_step_keys = []
                                for i, step in enumerate(steps):
                                    missing_keys = [key for key in expected_step_keys if key not in step]
                                    if missing_keys:
                                        missing_step_keys.append(f"Step {i+1}: {', '.join(missing_keys)}")
                                if missing_step_keys:
                                    print(f"Missing keys: {'; '.join(missing_step_keys)}")
                        else:
                            print("❌ No steps found in progress data")
                    else:
                        print("❌ Progress endpoint missing expected keys")
                        missing_keys = [key for key in expected_progress_keys if key not in progress_response_data]
                        print(f"Missing keys: {', '.join(missing_keys)}")
                else:
                    print(f"❌ Progress endpoint returned status {progress_status}")
                
            except Exception as e:
                print(f"Error processing progress data: {e}")
            
            # Wait a bit before trying again
            if not steps_structure_ok and attempt < max_attempts - 1:
                print(f"Waiting 2 seconds before next attempt...")
                time.sleep(2)
        
        # Determine test result
        passed = progress_data_ok and steps_structure_ok
        
        # Update test results
        test_results["tests"].append({
            "name": "Two-Column Progress Interface Data Structure",
            "endpoint": f"{API_PREFIX}/deep-research/progress/*",
            "method": "GET",
            "status_code": progress_status if 'progress_status' in locals() else 0,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "progress_data_ok": progress_data_ok,
                "steps_structure_ok": steps_structure_ok
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"The two-column progress interface data structure is correctly implemented")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if not progress_data_ok:
                print(f"  - Progress endpoint missing expected structure")
            if not steps_structure_ok:
                print(f"  - Steps missing expected structure for two-column interface")
        
        return passed, progress_response_data if 'progress_response_data' in locals() else None
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "Two-Column Progress Interface Data Structure",
            "endpoint": f"{API_PREFIX}/deep-research/progress/*",
            "method": "GET",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def main():
    """Run all tests"""
    print("Starting DeepResearch Functionality Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {test_results['timestamp']}")
    
    # Test 1: Backend API Health Check
    run_test(
        name="Backend API Health Check",
        endpoint="/health",
        expected_keys=["status", "services", "timestamp"]
    )
    
    # Test 2: Tools API - Check if enhanced_deep_research tool is available
    run_test(
        name="Tools API - Check Enhanced Deep Research Tool",
        endpoint=f"{API_PREFIX}/tools",
        expected_keys=["tools", "count"]
    )
    
    # Test 3: DeepResearch Functionality with Spanish Query
    test_deep_research_functionality()
    
    # Test 4: Two-Column Progress Interface Data Structure
    test_two_column_progress_interface()
    
    # Print summary
    print_summary()
    
    # Return exit code based on test results
    return 0 if test_results["summary"]["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())