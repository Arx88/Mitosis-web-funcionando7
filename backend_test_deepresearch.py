#!/usr/bin/env python3
"""
DeepResearch Functionality Test Script for Task Manager Application

This script tests the DeepResearch functionality in the Task Manager application,
focusing on:
1. Enhanced DeepResearch Tool availability
2. DeepResearch Progress Tracking
3. DeepResearch Report Generation
4. DeepResearch Chat API Integration
"""

import requests
import json
import sys
import uuid
import os
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

def test_enhanced_deep_research_tool():
    """Test the enhanced_deep_research tool availability"""
    print(f"\n{'='*80}")
    print(f"TEST: Enhanced Deep Research Tool Availability")
    
    test_results["summary"]["total"] += 1
    
    try:
        # First, check if the tool is available in the tools list
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
        enhanced_deep_research_available = False
        enhanced_deep_research_details = None
        
        for tool in tools:
            if tool.get("name") == "enhanced_deep_research":
                enhanced_deep_research_available = True
                enhanced_deep_research_details = tool
                break
        
        if enhanced_deep_research_available:
            print(f"✅ Enhanced Deep Research Tool is available in the tools list")
            print(f"Tool description: {enhanced_deep_research_details.get('description')}")
            print(f"Tool parameters: {json.dumps(enhanced_deep_research_details.get('parameters'), indent=2)}")
        else:
            print(f"❌ Enhanced Deep Research Tool is not available in the tools list")
        
        # Check if the tool has the expected parameters
        expected_parameters = ["query", "max_sources", "max_images", "generate_report", "task_id"]
        parameters_ok = True
        missing_parameters = []
        
        if enhanced_deep_research_available:
            tool_parameters = enhanced_deep_research_details.get("parameters", [])
            parameter_names = [param.get("name") for param in tool_parameters]
            
            for param in expected_parameters:
                if param not in parameter_names:
                    parameters_ok = False
                    missing_parameters.append(param)
        else:
            parameters_ok = False
            missing_parameters = expected_parameters
        
        # Determine test result
        passed = enhanced_deep_research_available and parameters_ok
        
        # Update test results
        test_results["tests"].append({
            "name": "Enhanced Deep Research Tool Availability",
            "endpoint": f"{API_PREFIX}/tools",
            "method": "GET",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "tool_available": enhanced_deep_research_available,
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
            if not enhanced_deep_research_available:
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

def test_deep_research_progress_tracking():
    """Test the DeepResearch progress tracking endpoint"""
    print(f"\n{'='*80}")
    print(f"TEST: DeepResearch Progress Tracking")
    
    test_results["summary"]["total"] += 1
    
    try:
        # Create a task ID for testing
        task_id = f"test-{uuid.uuid4()}"
        
        # Test the progress tracking endpoint
        url = f"{BASE_URL}{API_PREFIX}/deep-research/progress/{task_id}"
        print(f"URL: {url}")
        print(f"METHOD: GET")
        
        # Send the request
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        # Process response
        try:
            response_data = response.json()
            print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data}")
        
        # Check if the progress endpoint returns the expected structure
        expected_progress_keys = ["task_id", "is_active", "current_progress", "current_step", "steps"]
        
        # Check if all expected keys are present
        keys_ok = True
        missing_keys = []
        
        if status_code == 200:
            for key in expected_progress_keys:
                if key not in response_data:
                    keys_ok = False
                    missing_keys.append(key)
        
        # Check if steps have the expected structure
        steps_ok = False
        if keys_ok and "steps" in response_data and isinstance(response_data["steps"], list):
            steps = response_data["steps"]
            if len(steps) > 0:
                expected_step_keys = ["id", "title", "description", "status"]
                step_keys_ok = True
                
                for step in steps:
                    for key in expected_step_keys:
                        if key not in step:
                            step_keys_ok = False
                            break
                
                steps_ok = step_keys_ok
        
        # Determine test result
        passed = status_code == 200 and keys_ok and steps_ok
        
        # Update test results
        test_results["tests"].append({
            "name": "DeepResearch Progress Tracking",
            "endpoint": f"{API_PREFIX}/deep-research/progress/{task_id}",
            "method": "GET",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "keys_ok": keys_ok,
                "missing_keys": missing_keys,
                "steps_ok": steps_ok
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"The DeepResearch progress tracking endpoint returns the expected structure")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if status_code != 200:
                print(f"  - Expected status 200, got {status_code}")
            if not keys_ok:
                print(f"  - Missing expected keys: {', '.join(missing_keys)}")
            if not steps_ok:
                print(f"  - Steps do not have the expected structure")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "DeepResearch Progress Tracking",
            "endpoint": f"{API_PREFIX}/deep-research/progress/{task_id}",
            "method": "GET",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_deep_research_chat_integration():
    """Test the DeepResearch mode in the Chat API"""
    print(f"\n{'='*80}")
    print(f"TEST: DeepResearch Chat API Integration")
    
    test_results["summary"]["total"] += 1
    
    try:
        # Create a task ID for testing
        task_id = f"test-{uuid.uuid4()}"
        
        # Test the DeepResearch mode in the Chat API
        url = f"{BASE_URL}{API_PREFIX}/chat"
        print(f"URL: {url}")
        print(f"METHOD: POST")
        
        # Create a message with [DeepResearch] prefix
        data = {
            "message": "[DeepResearch] renewable energy trends",
            "search_mode": "deepsearch",
            "context": {
                "task_id": task_id
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
        
        # Check if the response has the expected structure
        expected_keys = ["response", "search_mode", "search_data", "tool_calls", "tool_results"]
        
        # Check if all expected keys are present
        keys_ok = True
        missing_keys = []
        
        if status_code == 200:
            for key in expected_keys:
                if key not in response_data:
                    keys_ok = False
                    missing_keys.append(key)
        
        # Check if search_mode is deepsearch
        search_mode_ok = False
        if keys_ok and "search_mode" in response_data:
            search_mode_ok = response_data["search_mode"] == "deepsearch"
        
        # Check if search_data has the expected structure
        search_data_ok = False
        if keys_ok and "search_data" in response_data:
            search_data = response_data["search_data"]
            expected_search_data_keys = ["query", "directAnswer", "sources", "type", "key_findings", "recommendations"]
            
            search_data_keys_ok = True
            for key in expected_search_data_keys:
                if key not in search_data:
                    search_data_keys_ok = False
                    break
            
            search_data_ok = search_data_keys_ok
        
        # Check if a report file was created
        report_file_created = False
        created_files = response_data.get("created_files", [])
        
        if created_files:
            for file_info in created_files:
                if file_info.get("mime_type") == "text/markdown" and "informe_" in file_info.get("name", ""):
                    report_file_created = True
                    print(f"✅ Report file created: {file_info.get('name')}")
                    print(f"File path: {file_info.get('path')}")
                    print(f"File size: {file_info.get('size')} bytes")
                    break
        
        # Determine test result
        passed = status_code == 200 and keys_ok and search_mode_ok and search_data_ok
        
        # Update test results
        test_results["tests"].append({
            "name": "DeepResearch Chat API Integration",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "keys_ok": keys_ok,
                "missing_keys": missing_keys,
                "search_mode_ok": search_mode_ok,
                "search_data_ok": search_data_ok,
                "report_file_created": report_file_created
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"The DeepResearch mode in the Chat API works correctly")
            if report_file_created:
                print(f"A report file was successfully created")
            else:
                print(f"No report file was created, but this might be expected if generate_report is false")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if status_code != 200:
                print(f"  - Expected status 200, got {status_code}")
            if not keys_ok:
                print(f"  - Missing expected keys: {', '.join(missing_keys)}")
            if not search_mode_ok:
                print(f"  - search_mode is not 'deepsearch'")
            if not search_data_ok:
                print(f"  - search_data does not have the expected structure")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "DeepResearch Chat API Integration",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_deep_research_report_generation():
    """Test the DeepResearch report generation"""
    print(f"\n{'='*80}")
    print(f"TEST: DeepResearch Report Generation")
    
    test_results["summary"]["total"] += 1
    
    try:
        # Create a task ID for testing
        task_id = f"test-{uuid.uuid4()}"
        
        # Test the DeepResearch mode in the Chat API with report generation
        url = f"{BASE_URL}{API_PREFIX}/chat"
        print(f"URL: {url}")
        print(f"METHOD: POST")
        
        # Create a message with [DeepResearch] prefix and explicit generate_report parameter
        data = {
            "message": "[DeepResearch] artificial intelligence ethics",
            "search_mode": "deepsearch",
            "context": {
                "task_id": task_id
            },
            "parameters": {
                "generate_report": True
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
        
        # Check if a report file was created
        report_file_created = False
        report_file_path = None
        created_files = response_data.get("created_files", [])
        
        if created_files:
            for file_info in created_files:
                if file_info.get("mime_type") == "text/markdown" and "informe_" in file_info.get("name", ""):
                    report_file_created = True
                    report_file_path = file_info.get("path")
                    print(f"✅ Report file created: {file_info.get('name')}")
                    print(f"File path: {report_file_path}")
                    print(f"File size: {file_info.get('size')} bytes")
                    break
        
        # Check if the report file exists and has the expected format
        report_content_ok = False
        
        # First, check if the report file path is in the response
        if "report_file" in response_data.get("search_data", {}) or "report_file" in response_data.get("tool_results", [{}])[0].get("result", {}).get("result", {}):
            report_file_path = response_data.get("search_data", {}).get("report_file")
            
            if not report_file_path and response_data.get("tool_results"):
                report_file_path = response_data.get("tool_results", [{}])[0].get("result", {}).get("result", {}).get("report_file")
            
            if report_file_path and os.path.exists(report_file_path):
                report_file_created = True
                try:
                    with open(report_file_path, 'r', encoding='utf-8') as f:
                        report_content = f.read()
                    
                    # Check if the report has the expected sections
                    expected_sections = [
                        "INFORME DE INVESTIGACIÓN PROFUNDA",
                        "RESUMEN EJECUTIVO",
                        "HALLAZGOS CLAVE",
                        "RECOMENDACIONES",
                        "FUENTES CONSULTADAS"
                    ]
                    
                    sections_ok = True
                    for section in expected_sections:
                        if section not in report_content:
                            sections_ok = False
                            print(f"❌ Missing section in report: {section}")
                    
                    report_content_ok = sections_ok
                    
                    if report_content_ok:
                        print(f"✅ Report file has the expected format with all required sections")
                        print(f"Report file path: {report_file_path}")
                        print(f"Report length: {len(report_content)} characters")
                    else:
                        print(f"❌ Report file does not have the expected format")
                except Exception as e:
                    print(f"Error reading report file: {e}")
        else:
            # Check if any report files were created in the reports directory
            reports_dir = "/app/backend/reports"
            if os.path.exists(reports_dir):
                report_files = [f for f in os.listdir(reports_dir) if f.startswith("informe_") and f.endswith(".md")]
                if report_files:
                    # Get the most recent report file
                    report_files.sort(key=lambda x: os.path.getmtime(os.path.join(reports_dir, x)), reverse=True)
                    most_recent_report = os.path.join(reports_dir, report_files[0])
                    
                    # Check if the report was created in the last minute
                    if time.time() - os.path.getmtime(most_recent_report) < 60:
                        report_file_created = True
                        report_file_path = most_recent_report
                        
                        try:
                            with open(report_file_path, 'r', encoding='utf-8') as f:
                                report_content = f.read()
                            
                            # Check if the report has the expected sections
                            expected_sections = [
                                "INFORME DE INVESTIGACIÓN PROFUNDA",
                                "RESUMEN EJECUTIVO",
                                "HALLAZGOS CLAVE",
                                "RECOMENDACIONES",
                                "FUENTES CONSULTADAS"
                            ]
                            
                            sections_ok = True
                            for section in expected_sections:
                                if section not in report_content:
                                    sections_ok = False
                                    print(f"❌ Missing section in report: {section}")
                            
                            report_content_ok = sections_ok
                            
                            if report_content_ok:
                                print(f"✅ Report file has the expected format with all required sections")
                                print(f"Report file path: {report_file_path}")
                                print(f"Report length: {len(report_content)} characters")
                            else:
                                print(f"❌ Report file does not have the expected format")
                        except Exception as e:
                            print(f"Error reading report file: {e}")
        
        # Determine test result
        passed = status_code == 200 and (report_file_created or "console_report" in response_data.get("search_data", {}))
        
        # Update test results
        test_results["tests"].append({
            "name": "DeepResearch Report Generation",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "report_file_created": report_file_created,
                "report_content_ok": report_content_ok
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"The DeepResearch report generation works correctly")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if status_code != 200:
                print(f"  - Expected status 200, got {status_code}")
            if not report_file_created:
                print(f"  - No report file was created")
            if not report_content_ok:
                print(f"  - Report file does not have the expected format")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "DeepResearch Report Generation",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

if __name__ == "__main__":
    print("Starting DeepResearch Functionality Tests...")
    
    # Test 1: Enhanced DeepResearch Tool Availability
    test_enhanced_deep_research_tool()
    
    # Test 2: DeepResearch Progress Tracking
    test_deep_research_progress_tracking()
    
    # Test 3: DeepResearch Chat API Integration
    test_deep_research_chat_integration()
    
    # Test 4: DeepResearch Report Generation
    test_deep_research_report_generation()
    
    # Print summary
    print_summary()