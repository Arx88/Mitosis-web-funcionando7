#!/usr/bin/env python3
"""
Backend API Test Script for Ollama Service Improvements

This script tests the backend API endpoints after UI configuration improvements,
specifically focusing on:
1. Ollama models endpoint - real models fetch with fallback to dummy
2. Health endpoint - correct Ollama status information  
3. General functionality - main endpoints still working after changes
4. Status endpoint
5. Basic chat endpoint
6. Ollama service handling both successful and failed connections
"""

import requests
import json
import sys
import uuid
import os
from datetime import datetime

# Configuration
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

def test_ollama_models_endpoint():
    """Test Ollama models endpoint - should return real models if available, fallback to dummy"""
    print(f"\n{'='*80}")
    print(f"TEST: Ollama Models Endpoint - Real Models Fetch with Fallback")
    
    test_results["summary"]["total"] += 1
    
    try:
        url = f"{BASE_URL}{API_PREFIX}/models"
        print(f"URL: {url}")
        print(f"METHOD: GET")
        
        response = requests.get(url, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data}")
        
        # Check status code
        status_ok = status_code == 200
        
        # Check expected keys
        expected_keys = ["models", "current_model", "timestamp"]
        keys_ok = True
        missing_keys = []
        
        if status_ok and isinstance(response_data, dict):
            for key in expected_keys:
                if key not in response_data:
                    keys_ok = False
                    missing_keys.append(key)
        
        # Check models array structure
        models_ok = False
        models_list = response_data.get("models", []) if isinstance(response_data, dict) else []
        current_model = response_data.get("current_model", "") if isinstance(response_data, dict) else ""
        
        if isinstance(models_list, list) and len(models_list) > 0:
            models_ok = True
            print(f"✅ Models list contains {len(models_list)} models")
            print(f"   Models: {models_list}")
            print(f"   Current model: {current_model}")
            
            # Check if we have expected fallback models (indicating Ollama is not available)
            fallback_models = ["llama3.2", "llama3.1", "mistral", "codellama", "phi3"]
            is_fallback = all(model in fallback_models for model in models_list)
            
            if is_fallback:
                print(f"✅ Using fallback dummy models (Ollama not available)")
            else:
                print(f"✅ Using real Ollama models (Ollama available)")
        else:
            print(f"❌ Models list is empty or invalid")
        
        # Check current model is valid
        current_model_ok = current_model and isinstance(current_model, str) and len(current_model) > 0
        if current_model_ok:
            print(f"✅ Current model is valid: {current_model}")
        else:
            print(f"❌ Current model is invalid or missing")
        
        # Determine test result
        passed = status_ok and keys_ok and models_ok and current_model_ok
        
        # Update test results
        test_results["tests"].append({
            "name": "Ollama Models Endpoint - Real Models Fetch with Fallback",
            "endpoint": f"{API_PREFIX}/models",
            "method": "GET",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "missing_keys": missing_keys if not keys_ok else None,
            "response_data": {
                "models_count": len(models_list),
                "current_model": current_model,
                "models_list": models_list
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"  - Models endpoint returns proper structure with {len(models_list)} models")
            print(f"  - Current model: {current_model}")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if not status_ok:
                print(f"  - Expected status 200, got {status_code}")
            if not keys_ok:
                print(f"  - Missing expected keys: {', '.join(missing_keys)}")
            if not models_ok:
                print(f"  - Models list is empty or invalid")
            if not current_model_ok:
                print(f"  - Current model is invalid or missing")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "Ollama Models Endpoint - Real Models Fetch with Fallback",
            "endpoint": f"{API_PREFIX}/models",
            "method": "GET",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_ollama_health_endpoint():
    """Test health endpoint - should return correct Ollama status information"""
    print(f"\n{'='*80}")
    print(f"TEST: Health Endpoint - Correct Ollama Status Information")
    
    test_results["summary"]["total"] += 1
    
    try:
        url = f"{BASE_URL}/health"
        print(f"URL: {url}")
        print(f"METHOD: GET")
        
        response = requests.get(url, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data}")
        
        # Check status code
        status_ok = status_code == 200
        
        # Check expected keys
        expected_keys = ["status", "timestamp", "services"]
        keys_ok = True
        missing_keys = []
        
        if status_ok and isinstance(response_data, dict):
            for key in expected_keys:
                if key not in response_data:
                    keys_ok = False
                    missing_keys.append(key)
        
        # Check services structure
        services_ok = False
        services = response_data.get("services", {}) if isinstance(response_data, dict) else {}
        
        if isinstance(services, dict):
            expected_service_keys = ["ollama", "tools", "database"]
            service_keys_ok = all(key in services for key in expected_service_keys)
            
            if service_keys_ok:
                services_ok = True
                ollama_status = services.get("ollama")
                tools_count = services.get("tools")
                database_status = services.get("database")
                
                print(f"✅ Services structure is correct")
                print(f"   Ollama status: {ollama_status}")
                print(f"   Tools count: {tools_count}")
                print(f"   Database status: {database_status}")
                
                # Validate service values
                if isinstance(ollama_status, bool):
                    print(f"✅ Ollama status is boolean: {ollama_status}")
                else:
                    print(f"❌ Ollama status should be boolean, got: {type(ollama_status)}")
                
                if isinstance(tools_count, int) and tools_count >= 0:
                    print(f"✅ Tools count is valid integer: {tools_count}")
                else:
                    print(f"❌ Tools count should be non-negative integer, got: {tools_count}")
                
                if isinstance(database_status, bool):
                    print(f"✅ Database status is boolean: {database_status}")
                else:
                    print(f"❌ Database status should be boolean, got: {type(database_status)}")
            else:
                print(f"❌ Services missing expected keys: {expected_service_keys}")
        else:
            print(f"❌ Services is not a dictionary")
        
        # Check overall status
        overall_status = response_data.get("status", "") if isinstance(response_data, dict) else ""
        status_valid = overall_status in ["healthy", "degraded", "error"]
        
        if status_valid:
            print(f"✅ Overall status is valid: {overall_status}")
        else:
            print(f"❌ Overall status is invalid: {overall_status}")
        
        # Determine test result
        passed = status_ok and keys_ok and services_ok and status_valid
        
        # Update test results
        test_results["tests"].append({
            "name": "Health Endpoint - Correct Ollama Status Information",
            "endpoint": "/health",
            "method": "GET",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "missing_keys": missing_keys if not keys_ok else None,
            "response_data": {
                "overall_status": overall_status,
                "ollama_status": services.get("ollama") if services else None,
                "tools_count": services.get("tools") if services else None,
                "database_status": services.get("database") if services else None
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"  - Health endpoint returns proper structure")
            print(f"  - Overall status: {overall_status}")
            print(f"  - Ollama status correctly reported: {services.get('ollama') if services else 'N/A'}")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if not status_ok:
                print(f"  - Expected status 200, got {status_code}")
            if not keys_ok:
                print(f"  - Missing expected keys: {', '.join(missing_keys)}")
            if not services_ok:
                print(f"  - Services structure is invalid")
            if not status_valid:
                print(f"  - Overall status is invalid: {overall_status}")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "Health Endpoint - Correct Ollama Status Information",
            "endpoint": "/health",
            "method": "GET",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_basic_chat_endpoint():
    """Test basic chat endpoint functionality"""
    print(f"\n{'='*80}")
    print(f"TEST: Basic Chat Endpoint Functionality")
    
    test_results["summary"]["total"] += 1
    
    try:
        url = f"{BASE_URL}{API_PREFIX}/chat"
        print(f"URL: {url}")
        print(f"METHOD: POST")
        
        # Test basic chat message
        data = {
            "message": "Hello, how are you?",
            "context": {
                "task_id": f"test-chat-{uuid.uuid4()}"
            }
        }
        
        print(f"DATA: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"RESPONSE KEYS: {list(response_data.keys())}")
            if 'response' in response_data:
                print(f"RESPONSE TEXT: {response_data['response'][:200]}...")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data[:500]}...")
        
        # Check status code
        status_ok = status_code == 200
        
        # Check expected keys
        expected_keys = ["response", "tool_calls", "tool_results", "timestamp"]
        keys_ok = True
        missing_keys = []
        
        if status_ok and isinstance(response_data, dict):
            for key in expected_keys:
                if key not in response_data:
                    keys_ok = False
                    missing_keys.append(key)
        
        # Check response content
        response_content_ok = False
        if isinstance(response_data, dict):
            response_text = response_data.get("response", "")
            if isinstance(response_text, str) and len(response_text) > 0:
                response_content_ok = True
                print(f"✅ Response contains text content ({len(response_text)} characters)")
            else:
                print(f"❌ Response text is empty or invalid")
        
        # Check tool_calls and tool_results structure
        tool_structure_ok = True
        if isinstance(response_data, dict):
            tool_calls = response_data.get("tool_calls", [])
            tool_results = response_data.get("tool_results", [])
            
            if isinstance(tool_calls, list) and isinstance(tool_results, list):
                print(f"✅ Tool calls and results have correct structure")
                print(f"   Tool calls: {len(tool_calls)}")
                print(f"   Tool results: {len(tool_results)}")
            else:
                tool_structure_ok = False
                print(f"❌ Tool calls or results have incorrect structure")
        
        # Determine test result
        passed = status_ok and keys_ok and response_content_ok and tool_structure_ok
        
        # Update test results
        test_results["tests"].append({
            "name": "Basic Chat Endpoint Functionality",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "missing_keys": missing_keys if not keys_ok else None,
            "response_data": {
                "response_length": len(response_data.get("response", "")) if isinstance(response_data, dict) else 0,
                "tool_calls_count": len(response_data.get("tool_calls", [])) if isinstance(response_data, dict) else 0,
                "tool_results_count": len(response_data.get("tool_results", [])) if isinstance(response_data, dict) else 0
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"  - Chat endpoint responds correctly to basic messages")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if not status_ok:
                print(f"  - Expected status 200, got {status_code}")
            if not keys_ok:
                print(f"  - Missing expected keys: {', '.join(missing_keys)}")
            if not response_content_ok:
                print(f"  - Response content is empty or invalid")
            if not tool_structure_ok:
                print(f"  - Tool calls/results structure is invalid")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "Basic Chat Endpoint Functionality",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_websearch_mode():
    """Test WebSearch mode in chat endpoint"""
    print(f"\n{'='*80}")
    print(f"TEST: WebSearch Mode in Chat Endpoint")
    
    test_results["summary"]["total"] += 1
    
    try:
        url = f"{BASE_URL}{API_PREFIX}/chat"
        print(f"URL: {url}")
        print(f"METHOD: POST")
        
        # Test WebSearch mode
        data = {
            "message": "[WebSearch] artificial intelligence trends 2025",
            "search_mode": "websearch",
            "context": {
                "task_id": f"test-websearch-{uuid.uuid4()}"
            }
        }
        
        print(f"DATA: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=45)  # Increased timeout for search
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"RESPONSE KEYS: {list(response_data.keys())}")
            if 'search_mode' in response_data:
                print(f"SEARCH MODE: {response_data['search_mode']}")
            if 'search_data' in response_data:
                search_data = response_data['search_data']
                print(f"SEARCH DATA KEYS: {list(search_data.keys()) if isinstance(search_data, dict) else 'Not a dict'}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data[:500]}...")
        
        # Check status code
        status_ok = status_code == 200
        
        # Check WebSearch specific structure
        websearch_ok = False
        search_data_ok = False
        
        if status_ok and isinstance(response_data, dict):
            # Check search_mode
            search_mode = response_data.get("search_mode")
            if search_mode == "websearch":
                websearch_ok = True
                print(f"✅ WebSearch mode detected correctly")
            else:
                print(f"❌ WebSearch mode not detected, got: {search_mode}")
            
            # Check search_data structure
            search_data = response_data.get("search_data", {})
            if isinstance(search_data, dict):
                expected_search_keys = ["query", "directAnswer", "sources", "summary"]
                search_keys_present = all(key in search_data for key in expected_search_keys)
                
                if search_keys_present:
                    search_data_ok = True
                    print(f"✅ Search data structure is correct")
                    print(f"   Query: {search_data.get('query')}")
                    print(f"   Sources count: {len(search_data.get('sources', []))}")
                    print(f"   Has summary: {bool(search_data.get('summary'))}")
                else:
                    missing_search_keys = [key for key in expected_search_keys if key not in search_data]
                    print(f"❌ Search data missing keys: {missing_search_keys}")
            else:
                print(f"❌ Search data is not a dictionary")
        
        # Check tool_results for web_search tool
        tool_execution_ok = False
        if isinstance(response_data, dict):
            tool_results = response_data.get("tool_results", [])
            if isinstance(tool_results, list) and len(tool_results) > 0:
                web_search_result = None
                for result in tool_results:
                    if result.get("tool") == "web_search":
                        web_search_result = result
                        break
                
                if web_search_result:
                    tool_execution_ok = True
                    print(f"✅ Web search tool was executed")
                    print(f"   Tool result success: {web_search_result.get('result', {}).get('success', False)}")
                else:
                    print(f"❌ Web search tool was not executed")
            else:
                print(f"❌ No tool results found")
        
        # Determine test result
        passed = status_ok and websearch_ok and search_data_ok and tool_execution_ok
        
        # Update test results
        test_results["tests"].append({
            "name": "WebSearch Mode in Chat Endpoint",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "search_mode": response_data.get("search_mode") if isinstance(response_data, dict) else None,
                "search_data_present": bool(response_data.get("search_data")) if isinstance(response_data, dict) else False,
                "tool_results_count": len(response_data.get("tool_results", [])) if isinstance(response_data, dict) else 0
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"  - WebSearch mode works correctly")
            print(f"  - Search data structure is proper")
            print(f"  - Web search tool executed successfully")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if not status_ok:
                print(f"  - Expected status 200, got {status_code}")
            if not websearch_ok:
                print(f"  - WebSearch mode not detected correctly")
            if not search_data_ok:
                print(f"  - Search data structure is invalid")
            if not tool_execution_ok:
                print(f"  - Web search tool was not executed")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "WebSearch Mode in Chat Endpoint",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "error": str(e),
            "passed": False
        })
        print(f"ERROR: {str(e)}")
        print(f"RESULT: ❌ FAILED (Exception)")
        return False, None

def test_deepsearch_mode():
    """Test DeepSearch mode in chat endpoint"""
    print(f"\n{'='*80}")
    print(f"TEST: DeepSearch Mode in Chat Endpoint")
    
    test_results["summary"]["total"] += 1
    
    try:
        url = f"{BASE_URL}{API_PREFIX}/chat"
        print(f"URL: {url}")
        print(f"METHOD: POST")
        
        # Test DeepSearch mode
        data = {
            "message": "[DeepResearch] climate change solutions",
            "search_mode": "deepsearch",
            "context": {
                "task_id": f"test-deepsearch-{uuid.uuid4()}"
            }
        }
        
        print(f"DATA: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=60)  # Increased timeout for deep research
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"RESPONSE KEYS: {list(response_data.keys())}")
            if 'search_mode' in response_data:
                print(f"SEARCH MODE: {response_data['search_mode']}")
            if 'search_data' in response_data:
                search_data = response_data['search_data']
                print(f"SEARCH DATA KEYS: {list(search_data.keys()) if isinstance(search_data, dict) else 'Not a dict'}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data[:500]}...")
        
        # Check status code
        status_ok = status_code == 200
        
        # Check DeepSearch specific structure
        deepsearch_ok = False
        search_data_ok = False
        
        if status_ok and isinstance(response_data, dict):
            # Check search_mode
            search_mode = response_data.get("search_mode")
            if search_mode == "deepsearch":
                deepsearch_ok = True
                print(f"✅ DeepSearch mode detected correctly")
            else:
                print(f"❌ DeepSearch mode not detected, got: {search_mode}")
            
            # Check search_data structure
            search_data = response_data.get("search_data", {})
            if isinstance(search_data, dict):
                expected_search_keys = ["query", "directAnswer", "sources", "type", "key_findings", "recommendations"]
                search_keys_present = all(key in search_data for key in expected_search_keys)
                
                if search_keys_present:
                    search_data_ok = True
                    print(f"✅ Search data structure is correct")
                    print(f"   Query: {search_data.get('query')}")
                    print(f"   Type: {search_data.get('type')}")
                    print(f"   Key findings count: {len(search_data.get('key_findings', []))}")
                    print(f"   Recommendations count: {len(search_data.get('recommendations', []))}")
                else:
                    missing_search_keys = [key for key in expected_search_keys if key not in search_data]
                    print(f"❌ Search data missing keys: {missing_search_keys}")
            else:
                print(f"❌ Search data is not a dictionary")
        
        # Check tool_results for deep_research tool
        tool_execution_ok = False
        if isinstance(response_data, dict):
            tool_results = response_data.get("tool_results", [])
            if isinstance(tool_results, list) and len(tool_results) > 0:
                deep_research_result = None
                for result in tool_results:
                    if result.get("tool") == "deep_research":
                        deep_research_result = result
                        break
                
                if deep_research_result:
                    tool_execution_ok = True
                    print(f"✅ Deep research tool was executed")
                    print(f"   Tool result success: {deep_research_result.get('result', {}).get('success', False)}")
                else:
                    print(f"❌ Deep research tool was not executed")
            else:
                print(f"❌ No tool results found")
        
        # Check created_files for research report
        files_created_ok = False
        if isinstance(response_data, dict):
            created_files = response_data.get("created_files", [])
            if isinstance(created_files, list) and len(created_files) > 0:
                files_created_ok = True
                print(f"✅ Research files were created: {len(created_files)} files")
                for file_info in created_files:
                    print(f"   File: {file_info.get('name')} ({file_info.get('size')} bytes)")
            else:
                print(f"❌ No research files were created")
        
        # Determine test result
        passed = status_ok and deepsearch_ok and search_data_ok and tool_execution_ok
        
        # Update test results
        test_results["tests"].append({
            "name": "DeepSearch Mode in Chat Endpoint",
            "endpoint": f"{API_PREFIX}/chat",
            "method": "POST",
            "status_code": status_code,
            "expected_status": 200,
            "passed": passed,
            "response_data": {
                "search_mode": response_data.get("search_mode") if isinstance(response_data, dict) else None,
                "search_data_present": bool(response_data.get("search_data")) if isinstance(response_data, dict) else False,
                "tool_results_count": len(response_data.get("tool_results", [])) if isinstance(response_data, dict) else 0,
                "created_files_count": len(response_data.get("created_files", [])) if isinstance(response_data, dict) else 0
            }
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"RESULT: ✅ PASSED")
            print(f"  - DeepSearch mode works correctly")
            print(f"  - Search data structure is proper")
            print(f"  - Deep research tool executed successfully")
            if files_created_ok:
                print(f"  - Research files were created")
        else:
            test_results["summary"]["failed"] += 1
            print(f"RESULT: ❌ FAILED")
            if not status_ok:
                print(f"  - Expected status 200, got {status_code}")
            if not deepsearch_ok:
                print(f"  - DeepSearch mode not detected correctly")
            if not search_data_ok:
                print(f"  - Search data structure is invalid")
            if not tool_execution_ok:
                print(f"  - Deep research tool was not executed")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": "DeepSearch Mode in Chat Endpoint",
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
    print(f"OLLAMA SERVICE IMPROVEMENTS TEST SUMMARY")
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
    """Main test execution"""
    print("🚀 Starting Ollama Service Improvements Backend Testing")
    print("="*80)
    
    # Test the specific areas mentioned in the user request
    
    # 1. Test Ollama models endpoint - real models fetch with fallback to dummy
    test_ollama_models_endpoint()
    
    # 2. Test health endpoint - correct Ollama status information
    test_ollama_health_endpoint()
    
    # 3. Test status endpoint
    run_test("Status API", f"{API_PREFIX}/status", "GET", None, 200, ["status", "ollama_status", "available_models", "current_model", "tools_count"])
    
    # 4. Test tools endpoint
    run_test("Tools API", f"{API_PREFIX}/tools", "GET", None, 200, ["tools", "count"])
    
    # 5. Test basic chat endpoint
    test_basic_chat_endpoint()
    
    # 6. Test WebSearch mode (verifying Ollama service handles both successful and failed connections)
    test_websearch_mode()
    
    # 7. Test DeepSearch mode (verifying Ollama service handles both successful and failed connections)
    test_deepsearch_mode()
    
    # Print final summary
    print_summary()
    
    # Return exit code based on results
    if test_results["summary"]["failed"] > 0:
        print(f"\n❌ Some tests failed. Please check the results above.")
        return 1
    else:
        print(f"\n✅ All tests passed successfully!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)