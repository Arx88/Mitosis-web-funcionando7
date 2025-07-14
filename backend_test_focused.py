#!/usr/bin/env python3
"""
Focused Backend API Test Script for Task Manager Application

This script specifically tests the backend API endpoints mentioned in the review request:
1. Chat API Testing: Test sending a WebSearch message to see if search results are properly formatted and returned
2. File Upload Testing: Test uploading a sample file to verify the file display improvements are working
3. Search Results Testing: Verify that Tavily search is working and returning properly formatted results
4. Tool Integration Testing: Test that tool executions are logged correctly to the terminal
"""

import requests
import json
import sys
import uuid
import os
import tempfile
import mimetypes
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

def run_test(name, endpoint, method="GET", data=None, files=None, expected_status=200, expected_keys=None, validation_func=None):
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
            if files:
                response = requests.post(url, data=data, files=files, timeout=30)
            else:
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
        
        # Run custom validation function if provided
        validation_ok = True
        validation_message = None
        if validation_func and status_ok and keys_ok:
            validation_ok, validation_message = validation_func(response_data)
        
        # Determine test result
        passed = status_ok and keys_ok and validation_ok
        
        # Update test results
        test_results["tests"].append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "expected_status": expected_status,
            "passed": passed,
            "missing_keys": missing_keys if not keys_ok else None,
            "validation_message": validation_message,
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
            if not validation_ok and validation_message:
                print(f"  - Validation failed: {validation_message}")
        
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
                elif test["status_code"] != test["expected_status"]:
                    print(f"  Expected status {test['expected_status']}, got {test['status_code']}")
                if test.get("missing_keys"):
                    print(f"  Missing keys: {', '.join(test['missing_keys'])}")
                if test.get("validation_message"):
                    print(f"  Validation: {test['validation_message']}")

def test_websearch_chat():
    """Test 1: Chat API with WebSearch mode"""
    print(f"\n{'='*80}")
    print(f"TEST 1: Chat API with WebSearch Mode")
    
    # Define validation function for WebSearch response
    def validate_websearch_response(response_data):
        # Check if the response is properly formatted
        response_text = response_data.get("response", "")
        
        # Check for expected sections in the response
        expected_sections = [
            "**Búsqueda Web con Tavily**",
            "**Pregunta:**",
            "**Respuesta Directa:**",
            "**Fuentes encontradas:**"
        ]
        
        for section in expected_sections:
            if section not in response_text:
                return False, f"Missing section '{section}' in response"
        
        # Check if tool_results contains the expected structure
        tool_results = response_data.get("tool_results", [])
        if not tool_results:
            return False, "No tool_results found in response"
        
        # Check if search_mode is set correctly
        if response_data.get("search_mode") != "websearch":
            return False, f"Expected search_mode 'websearch', got '{response_data.get('search_mode')}'"
        
        return True, None
    
    # Run the test
    query = "Search for information about artificial intelligence"
    data = {
        "message": f"[WebSearch] {query}",
        "search_mode": "websearch"
    }
    
    return run_test(
        name="Chat API with WebSearch Mode",
        endpoint=f"{API_PREFIX}/chat",
        method="POST",
        data=data,
        expected_keys=["response", "tool_results", "search_mode"],
        validation_func=validate_websearch_response
    )

def test_file_upload():
    """Test 2: File Upload API"""
    print(f"\n{'='*80}")
    print(f"TEST 2: File Upload API")
    
    # Define validation function for file upload response
    def validate_file_upload_response(response_data):
        # Check if the response indicates success
        if not response_data.get("success", False):
            return False, "Upload not successful"
        
        # Check if files were uploaded
        files = response_data.get("files", [])
        if not files:
            return False, "No files in response"
        
        # Check if each file has the required attributes
        for file_info in files:
            required_attrs = ['id', 'name', 'path', 'size', 'mime_type', 'created_at', 'source']
            missing_attrs = [attr for attr in required_attrs if attr not in file_info]
            if missing_attrs:
                return False, f"File {file_info.get('name')} missing attributes: {', '.join(missing_attrs)}"
            
            # Check if source is set correctly
            if file_info.get('source') != 'uploaded':
                return False, f"File {file_info.get('name')} has incorrect source: {file_info.get('source')}"
        
        return True, None
    
    # Create a test task ID
    task_id = f"test-upload-{uuid.uuid4()}"
    
    # Create a test file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
        temp_file.write(b"This is a test file for upload testing.\nIt contains some text content.")
        temp_file_path = temp_file.name
    
    try:
        # Prepare the multipart/form-data request
        files = {
            'files': ('test_upload.txt', open(temp_file_path, 'rb'), 'text/plain')
        }
        data = {
            'task_id': task_id
        }
        
        # Run the test
        result, response_data = run_test(
            name="File Upload API",
            endpoint=f"{API_PREFIX}/upload-files",
            method="POST",
            data=data,
            files=files,
            expected_keys=["success", "files"],
            validation_func=validate_file_upload_response
        )
        
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
            print(f"Cleaned up test file: {temp_file_path}")
        except Exception as e:
            print(f"Error cleaning up file {temp_file_path}: {e}")
        
        return result, response_data
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
            print(f"Cleaned up test file: {temp_file_path}")
        except:
            pass
        
        return False, None

def test_tavily_search():
    """Test 3: Tavily Search Tool"""
    print(f"\n{'='*80}")
    print(f"TEST 3: Tavily Search Tool")
    
    # Define validation function for Tavily search response
    def validate_tavily_search_response(response_data):
        # Check if the response contains the expected structure
        tool_results = response_data.get("tool_results", [])
        if not tool_results:
            return False, "No tool_results found in response"
        
        # Check if the first tool result is for tavily_search
        if not tool_results[0].get("tool") == "tavily_search":
            return False, f"Expected tool 'tavily_search', got '{tool_results[0].get('tool')}''"
        
        # Check if the response is properly formatted
        response_text = response_data.get("response", "")
        
        # Check for expected sections in the response
        expected_sections = [
            "**Búsqueda Web con Tavily**",
            "**Pregunta:**",
            "**Respuesta Directa:**",
            "**Fuentes encontradas:**"
        ]
        
        for section in expected_sections:
            if section not in response_text:
                return False, f"Missing section '{section}' in response"
        
        return True, None
    
    # Run the test
    query = "What are the latest advancements in artificial intelligence?"
    data = {
        "message": f"[WebSearch] {query}",
        "search_mode": "websearch"
    }
    
    return run_test(
        name="Tavily Search Tool",
        endpoint=f"{API_PREFIX}/chat",
        method="POST",
        data=data,
        expected_keys=["response", "tool_results", "search_mode"],
        validation_func=validate_tavily_search_response
    )

def test_tool_execution_logging():
    """Test 4: Tool Execution Logging"""
    print(f"\n{'='*80}")
    print(f"TEST 4: Tool Execution Logging")
    
    # Define validation function for tool execution logging
    def validate_tool_execution_logging(response_data):
        # Check if tool_results contains the expected structure
        tool_results = response_data.get("tool_results", [])
        if not tool_results:
            return False, "No tool_results found in response"
        
        # Check if the tool result contains the expected fields
        tool_result = tool_results[0]
        required_fields = ['tool', 'parameters', 'result']
        missing_fields = [field for field in required_fields if field not in tool_result]
        if missing_fields:
            return False, f"Tool result missing fields: {', '.join(missing_fields)}"
        
        # Check if the result contains success status
        result = tool_result.get("result", {})
        if "success" not in result:
            return False, "Tool result missing 'success' status"
        
        # Check if the result contains timestamp
        if "timestamp" not in result:
            return False, "Tool result missing 'timestamp'"
        
        return True, None
    
    # Run the test with WebSearch which will execute the tavily_search tool
    query = "What is the capital of France?"
    data = {
        "message": f"[WebSearch] {query}",
        "search_mode": "websearch"
    }
    
    return run_test(
        name="Tool Execution Logging",
        endpoint=f"{API_PREFIX}/chat",
        method="POST",
        data=data,
        expected_keys=["response", "tool_results"],
        validation_func=validate_tool_execution_logging
    )

def main():
    """Run all tests"""
    print("Starting Focused Backend API Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {test_results['timestamp']}")
    
    # Test 1: Chat API with WebSearch mode
    test_websearch_chat()
    
    # Test 2: File Upload API
    test_file_upload()
    
    # Test 3: Tavily Search Tool
    test_tavily_search()
    
    # Test 4: Tool Execution Logging
    test_tool_execution_logging()
    
    # Print summary
    print_summary()
    
    # Return exit code based on test results
    return 0 if test_results["summary"]["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())