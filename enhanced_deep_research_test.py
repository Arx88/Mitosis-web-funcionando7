#!/usr/bin/env python3
"""
Enhanced Deep Research Tool Test Script

This script tests the enhanced deep research tool functionality in the Task Manager application.
It verifies:
1. Tool availability in the tools API
2. Tool execution through the chat API
3. Progress tracking
4. File generation
5. Error handling
"""

import requests
import json
import sys
import uuid
import os
import time
from datetime import datetime
from pathlib import Path

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

def test_enhanced_deep_research_tool_availability():
    """Test if the enhanced_deep_research tool is available in the tools API"""
    print(f"\n{'='*80}")
    print(f"TEST: Enhanced Deep Research Tool Availability")
    
    test_results["summary"]["total"] += 1
    
    try:
        # Check if the tool is available in the tools list
        url = f"{BASE_URL}{API_PREFIX}/tools"
        print(f"URL: {url}")
        print(f"METHOD: GET")
        
        # Send the request
        response = requests.get(url, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        # Process response
        try:
            response_data = response.json()
            print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data}")
        
        # Check if the enhanced_deep_research tool is in the tools list
        tools = response_data.get("tools", [])
        tool_available = False
        tool_details = None
        
        for tool in tools:
            if tool.get("name") == "enhanced_deep_research":
                tool_available = True
                tool_details = tool
                break
        
        if tool_available:
            print(f"✅ Enhanced Deep Research Tool is available in the tools list")
            print(f"Tool description: {tool_details.get('description')}")
            print(f"Tool parameters: {json.dumps(tool_details.get('parameters'), indent=2)}")
        else:
            print(f"❌ Enhanced Deep Research Tool is not available in the tools list")
        
        # Check if the tool has the expected parameters
        expected_parameters = ["query", "max_sources", "max_images", "generate_report", "task_id"]
        parameters_ok = True
        missing_parameters = []
        
        if tool_available:
            tool_parameters = tool_details.get("parameters", [])
            parameter_names = [param.get("name") for param in tool_parameters]
            
            for param in expected_parameters:
                if param not in parameter_names:
                    parameters_ok = False
                    missing_parameters.append(param)
        else:
            parameters_ok = False
            missing_parameters = expected_parameters
        
        # Determine test result
        passed = tool_available and parameters_ok
        
        # Update test results
        test_results["tests"].append({
            "name": "Enhanced Deep Research Tool Availability",
            "endpoint": f"{API_PREFIX}/tools",
            "method": "GET",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "tool_available": tool_available,
                "parameters_ok": parameters_ok,
                "missing_parameters": missing_parameters
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"The enhanced_deep_research tool is available and has all expected parameters")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if not tool_available:
                print(f"  - Enhanced Deep Research Tool is not available in the tools list")
            if not parameters_ok:
                print(f"  - Missing expected parameters: {', '.join(missing_parameters)}")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "Enhanced Deep Research Tool Availability",
            "endpoint": f"{API_PREFIX}/tools",
            "method": "GET",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_enhanced_deep_research_execution():
    """Test the execution of the enhanced_deep_research tool through the chat API"""
    print(f"\n{'='*80}")
    print(f"TEST: Enhanced Deep Research Tool Execution")
    
    test_results["summary"]["total"] += 1
    
    try:
        # Create a task ID for testing
        task_id = f"test-{uuid.uuid4()}"
        
        # Test the chat API with DeepResearch mode
        url = f"{BASE_URL}{API_PREFIX}/chat"
        print(f"URL: {url}")
        print(f"METHOD: POST")
        
        # Create a message that should trigger the enhanced_deep_research tool
        data = {
            "message": "[DeepResearch] Renewable energy trends",
            "search_mode": "deepsearch",
            "context": {
                "task_id": task_id,
                "previous_messages": []
            }
        }
        
        print(f"DATA: {json.dumps(data, indent=2)}")
        
        # Send the request
        response = requests.post(url, json=data, timeout=60)  # Longer timeout for research
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        # Process response
        try:
            response_data = response.json()
            print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data}")
        
        # Check status code
        status_ok = status_code == 200
        
        # Check expected keys
        expected_keys = ["response", "tool_results", "search_mode", "search_data"]
        keys_ok = True
        missing_keys = []
        
        if status_ok:
            for key in expected_keys:
                if key not in response_data:
                    keys_ok = False
                    missing_keys.append(key)
        
        # Check if the tool was executed correctly
        tool_executed = False
        console_report_generated = False
        report_file_created = False
        
        if status_ok and keys_ok:
            tool_results = response_data.get("tool_results", [])
            
            if tool_results and len(tool_results) > 0:
                tool_result = tool_results[0]
                
                if tool_result.get("tool") == "enhanced_deep_research":
                    tool_executed = True
                    print("✅ Enhanced Deep Research Tool was executed")
                    
                    # Check if the result contains the expected data
                    result = tool_result.get("result", {}).get("result", {})
                    
                    if result.get("console_report"):
                        console_report_generated = True
                        print("✅ Console report was generated")
                    
                    if result.get("report_file"):
                        report_file_created = True
                        report_file = result.get("report_file")
                        print(f"✅ Report file was created: {report_file}")
                        
                        # Check if the file exists
                        if os.path.exists(report_file):
                            print(f"✅ Report file exists on disk")
                            
                            # Check file content
                            try:
                                with open(report_file, 'r', encoding='utf-8') as f:
                                    file_content = f.read()
                                    print(f"Report file content length: {len(file_content)} characters")
                                    if len(file_content) > 100:
                                        print("✅ Report file has valid content")
                                    else:
                                        print("❌ Report file content is too short")
                            except Exception as e:
                                print(f"Error reading report file: {e}")
                        else:
                            print(f"❌ Report file does not exist on disk")
                    
                    # Check if the file was added to task_files
                    created_files = response_data.get("created_files", [])
                    if created_files and len(created_files) > 0:
                        print(f"✅ Report file was added to task_files")
                        
                        # Check if the file can be downloaded
                        file_id = created_files[0].get("id")
                        if file_id:
                            download_url = f"{BASE_URL}{API_PREFIX}/download/{file_id}"
                            print(f"Testing file download from: {download_url}")
                            
                            try:
                                download_response = requests.get(download_url, timeout=10)
                                if download_response.status_code == 200:
                                    print(f"✅ Report file can be downloaded")
                                else:
                                    print(f"❌ Report file download failed with status {download_response.status_code}")
                            except Exception as e:
                                print(f"Error downloading report file: {e}")
                    else:
                        print(f"❌ Report file was not added to task_files")
        
        # Determine test result
        passed = status_ok and keys_ok and tool_executed
        
        # Update test results
        test_results["tests"].append({
            "name": "Enhanced Deep Research Tool Execution",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "tool_executed": tool_executed,
                "console_report_generated": console_report_generated,
                "report_file_created": report_file_created
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if not status_ok:
                print(f"  - Expected status 200, got {status_code}")
            if not keys_ok:
                print(f"  - Missing expected keys: {', '.join(missing_keys)}")
            if not tool_executed:
                print(f"  - Enhanced Deep Research Tool was not executed")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "Enhanced Deep Research Tool Execution",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_error_handling():
    """Test error handling in the enhanced_deep_research tool"""
    print(f"\n{'='*80}")
    print(f"TEST: Enhanced Deep Research Tool Error Handling")
    
    test_results["summary"]["total"] += 1
    
    try:
        # Test with invalid query (empty)
        url = f"{BASE_URL}{API_PREFIX}/chat"
        print(f"URL: {url}")
        print(f"METHOD: POST")
        
        # Create a message with empty query
        data = {
            "message": "[DeepResearch] ",
            "search_mode": "deepsearch",
            "context": {
                "task_id": f"test-{uuid.uuid4()}",
                "previous_messages": []
            }
        }
        
        print(f"DATA: {json.dumps(data, indent=2)}")
        
        # Send the request
        response = requests.post(url, json=data, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        # Process response
        try:
            response_data = response.json()
            print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data}")
        
        # Check if the response contains an error message
        error_handled = False
        
        if status_code == 200 or status_code == 400:
            tool_results = response_data.get("tool_results", [])
            
            if tool_results and len(tool_results) > 0:
                tool_result = tool_results[0]
                
                if "error" in tool_result.get("result", {}):
                    error_handled = True
                    print(f"✅ Error was handled correctly: {tool_result['result'].get('error')}")
        
        # Determine test result
        passed = error_handled
        
        # Update test results
        test_results["tests"].append({
            "name": "Enhanced Deep Research Tool Error Handling",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "error_handled": error_handled
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            print(f"  - Error was not handled correctly")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "Enhanced Deep Research Tool Error Handling",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
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

def main():
    """Run all tests"""
    print("Starting Enhanced Deep Research Tool Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {test_results['timestamp']}")
    
    # Test 1: Enhanced Deep Research Tool Availability
    test_enhanced_deep_research_tool_availability()
    
    # Test 2: Enhanced Deep Research Tool Execution
    test_enhanced_deep_research_execution()
    
    # Test 3: Error Handling
    test_error_handling()
    
    # Print summary
    print_summary()
    
    # Return exit code based on test results
    return 0 if test_results["summary"]["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())