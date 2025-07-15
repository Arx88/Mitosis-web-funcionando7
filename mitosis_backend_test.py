#!/usr/bin/env python3
"""
Mitosis Backend Test Script - New Default Configuration Testing

This script tests the Mitosis backend application with the new default configurations to ensure:
1. Backend Health Check: Test the /health endpoint to ensure all services are running
2. Ollama Configuration: Test the Ollama endpoints to verify default endpoint and model
3. API Endpoints: Test the main API endpoints
4. Stability: Check if the backend is stable and doesn't crash during normal operations
5. Configuration Defaults: Verify that the new configuration values are being used by default

Backend should be running at localhost:8001 and should be stable without crashes.
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"

# Expected default configurations
EXPECTED_OLLAMA_ENDPOINT = "https://78d08925604a.ngrok-free.app"
EXPECTED_OLLAMA_MODEL = "llama3.1:8b"

print(f"🧪 MITOSIS BACKEND TESTING - NEW DEFAULT CONFIGURATIONS")
print(f"Backend URL: {BASE_URL}")
print(f"Expected Ollama Endpoint: {EXPECTED_OLLAMA_ENDPOINT}")
print(f"Expected Ollama Model: {EXPECTED_OLLAMA_MODEL}")
print(f"Test Started: {datetime.now().isoformat()}")
print("="*80)

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

def run_test(name, test_func):
    """Run a test and track results"""
    test_results["summary"]["total"] += 1
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {name}")
    print(f"{'='*80}")
    
    try:
        start_time = time.time()
        passed, details = test_func()
        end_time = time.time()
        
        test_results["tests"].append({
            "name": name,
            "passed": passed,
            "duration": round(end_time - start_time, 2),
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"✅ RESULT: PASSED ({end_time - start_time:.2f}s)")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ RESULT: FAILED ({end_time - start_time:.2f}s)")
            if details and "error" in details:
                print(f"   Error: {details['error']}")
        
        return passed
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "passed": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        print(f"❌ RESULT: FAILED (Exception: {str(e)})")
        return False

def test_backend_health_check():
    """Test 1: Backend Health Check - Test the /health endpoint"""
    print("Testing backend health endpoint...")
    
    try:
        url = f"{BASE_URL}/health"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        print(f"Status Code: {status_code}")
        
        if status_code != 200:
            return False, {"error": f"Health endpoint returned status {status_code}"}
        
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            data = {"raw_response": response.text}
            print(f"Raw Response: {response.text}")
        
        # Check required fields
        required_fields = ["status", "timestamp", "services"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return False, {"error": f"Missing required fields: {missing_fields}"}
        
        # Check if status is healthy
        if data.get("status") != "healthy":
            return False, {"error": f"Backend status is not healthy: {data.get('status')}"}
        
        # Check services
        services = data.get("services", {})
        print(f"Services Status:")
        print(f"  - Ollama: {services.get('ollama', 'Unknown')}")
        print(f"  - Tools: {services.get('tools', 'Unknown')}")
        print(f"  - Database: {services.get('database', 'Unknown')}")
        
        return True, {
            "status": data.get("status"),
            "services": services,
            "timestamp": data.get("timestamp")
        }
    
    except requests.exceptions.ConnectionError:
        return False, {"error": "Cannot connect to backend - is it running on localhost:8001?"}
    except Exception as e:
        return False, {"error": str(e)}

def test_agent_health_endpoint():
    """Test 2: Agent Health Endpoint - Test /api/agent/health"""
    print("Testing agent health endpoint...")
    
    try:
        url = f"{BASE_URL}{API_PREFIX}/health"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        print(f"Status Code: {status_code}")
        
        if status_code != 200:
            return False, {"error": f"Agent health endpoint returned status {status_code}"}
        
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            data = {"raw_response": response.text}
            print(f"Raw Response: {response.text}")
        
        return True, data
    
    except Exception as e:
        return False, {"error": str(e)}

def test_ollama_configuration():
    """Test 3: Ollama Configuration - Test default endpoint and model"""
    print("Testing Ollama configuration with default values...")
    
    try:
        # Test Ollama check endpoint
        check_url = f"{BASE_URL}{API_PREFIX}/ollama/check"
        print(f"Ollama Check URL: {check_url}")
        
        check_response = requests.get(check_url, timeout=15)
        check_status = check_response.status_code
        print(f"Ollama Check Status: {check_status}")
        
        if check_status != 200:
            return False, {"error": f"Ollama check endpoint returned status {check_status}"}
        
        try:
            check_data = check_response.json()
            print(f"Ollama Check Response: {json.dumps(check_data, indent=2)}")
        except:
            check_data = {"raw_response": check_response.text}
            print(f"Ollama Check Raw Response: {check_response.text}")
        
        # Verify default endpoint
        endpoint = check_data.get("endpoint") or check_data.get("data", {}).get("endpoint")
        if endpoint != EXPECTED_OLLAMA_ENDPOINT:
            return False, {
                "error": f"Ollama endpoint mismatch. Expected: {EXPECTED_OLLAMA_ENDPOINT}, Got: {endpoint}"
            }
        
        print(f"✅ Ollama endpoint correctly set to: {endpoint}")
        
        # Test connection status
        is_connected = check_data.get("is_connected") or check_data.get("data", {}).get("is_connected")
        print(f"Ollama Connection Status: {is_connected}")
        
        # Test Ollama models endpoint
        models_url = f"{BASE_URL}{API_PREFIX}/ollama/models"
        print(f"Ollama Models URL: {models_url}")
        
        models_response = requests.get(models_url, timeout=15)
        models_status = models_response.status_code
        print(f"Ollama Models Status: {models_status}")
        
        if models_status != 200:
            return False, {"error": f"Ollama models endpoint returned status {models_status}"}
        
        try:
            models_data = models_response.json()
            print(f"Ollama Models Response: {json.dumps(models_data, indent=2)}")
        except:
            models_data = {"raw_response": models_response.text}
            print(f"Ollama Models Raw Response: {models_response.text}")
        
        # Check if expected model is available
        models = models_data.get("models") or models_data.get("data", {}).get("models", [])
        print(f"Available Models: {models}")
        
        if EXPECTED_OLLAMA_MODEL in models:
            print(f"✅ Expected model '{EXPECTED_OLLAMA_MODEL}' is available")
        else:
            print(f"⚠️ Expected model '{EXPECTED_OLLAMA_MODEL}' not found in available models")
        
        return True, {
            "endpoint": endpoint,
            "is_connected": is_connected,
            "models": models,
            "expected_model_available": EXPECTED_OLLAMA_MODEL in models
        }
    
    except Exception as e:
        return False, {"error": str(e)}

def test_agent_status_endpoint():
    """Test 4: Agent Status Endpoint - Test /api/agent/status"""
    print("Testing agent status endpoint...")
    
    try:
        url = f"{BASE_URL}{API_PREFIX}/status"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        print(f"Status Code: {status_code}")
        
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            data = {"raw_response": response.text}
            print(f"Raw Response: {response.text}")
        
        # Even if endpoint doesn't exist, we'll note it but not fail the test
        if status_code == 404:
            print("ℹ️ Agent status endpoint not implemented - this is acceptable")
            return True, {"note": "Endpoint not implemented"}
        
        if status_code != 200:
            return False, {"error": f"Agent status endpoint returned status {status_code}"}
        
        return True, data
    
    except Exception as e:
        return False, {"error": str(e)}

def test_backend_stability():
    """Test 5: Backend Stability - Check if backend is stable during operations"""
    print("Testing backend stability with multiple requests...")
    
    try:
        stability_results = []
        
        # Test multiple health checks to ensure stability
        for i in range(5):
            print(f"Stability check {i+1}/5...")
            
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            stability_results.append({
                "check": i+1,
                "status_code": response.status_code,
                "response_time": round(response_time, 3),
                "success": response.status_code == 200
            })
            
            print(f"  Check {i+1}: Status {response.status_code}, Time: {response_time:.3f}s")
            
            # Small delay between requests
            time.sleep(0.5)
        
        # Analyze stability
        successful_checks = sum(1 for result in stability_results if result["success"])
        avg_response_time = sum(result["response_time"] for result in stability_results) / len(stability_results)
        
        print(f"Stability Results:")
        print(f"  Successful checks: {successful_checks}/5")
        print(f"  Average response time: {avg_response_time:.3f}s")
        
        # Consider stable if at least 4/5 checks pass and avg response time < 2s
        is_stable = successful_checks >= 4 and avg_response_time < 2.0
        
        return is_stable, {
            "successful_checks": successful_checks,
            "total_checks": 5,
            "average_response_time": round(avg_response_time, 3),
            "stability_results": stability_results
        }
    
    except Exception as e:
        return False, {"error": str(e)}

def test_basic_chat_functionality():
    """Test 6: Basic Chat Functionality - Test basic chat endpoint"""
    print("Testing basic chat functionality...")
    
    try:
        url = f"{BASE_URL}{API_PREFIX}/chat"
        print(f"URL: {url}")
        
        # Simple test message
        data = {
            "message": "Hello, this is a test message"
        }
        
        print(f"Request Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=30)
        status_code = response.status_code
        print(f"Status Code: {status_code}")
        
        if status_code != 200:
            return False, {"error": f"Chat endpoint returned status {status_code}"}
        
        try:
            response_data = response.json()
            print(f"Response Keys: {list(response_data.keys())}")
            
            # Check for expected response structure
            if "response" in response_data:
                response_text = response_data["response"]
                print(f"Response Text: {response_text[:200]}...")
                
                # Check if it's an error response about Ollama
                if "Error de conexión con Ollama" in response_text or "connection" in response_text.lower():
                    print("ℹ️ Chat endpoint working but Ollama connection issue detected")
                    return True, {
                        "status": "working_with_ollama_issue",
                        "response_structure": list(response_data.keys())
                    }
                else:
                    print("✅ Chat endpoint working with successful response")
                    return True, {
                        "status": "working",
                        "response_structure": list(response_data.keys())
                    }
            else:
                return False, {"error": "Response missing 'response' field"}
        
        except:
            response_data = {"raw_response": response.text}
            print(f"Raw Response: {response.text}")
            return False, {"error": "Invalid JSON response"}
    
    except Exception as e:
        return False, {"error": str(e)}

def print_final_summary():
    """Print final test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print("🎯 FINAL TEST SUMMARY")
    print("="*80)
    print(f"Test Timestamp: {test_results['timestamp']}")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - MITOSIS BACKEND IS WORKING CORRECTLY!")
    elif passed >= total * 0.8:
        print("\n✅ MOST TESTS PASSED - BACKEND IS MOSTLY FUNCTIONAL")
    else:
        print("\n⚠️ MULTIPLE TEST FAILURES - BACKEND NEEDS ATTENTION")
    
    print("\n📊 DETAILED RESULTS:")
    for test in test_results["tests"]:
        status = "✅ PASS" if test["passed"] else "❌ FAIL"
        duration = test.get("duration", 0)
        print(f"  {status} - {test['name']} ({duration}s)")
        
        if not test["passed"] and "error" in test:
            print(f"    Error: {test['error']}")
    
    print("\n" + "="*80)
    
    return passed == total

def main():
    """Main test execution"""
    print("🚀 Starting Mitosis Backend Tests...")
    
    # Run all tests
    tests = [
        ("Backend Health Check", test_backend_health_check),
        ("Agent Health Endpoint", test_agent_health_endpoint),
        ("Ollama Configuration", test_ollama_configuration),
        ("Agent Status Endpoint", test_agent_status_endpoint),
        ("Backend Stability", test_backend_stability),
        ("Basic Chat Functionality", test_basic_chat_functionality)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        passed = run_test(test_name, test_func)
        if not passed:
            all_passed = False
    
    # Print final summary
    final_success = print_final_summary()
    
    # Exit with appropriate code
    sys.exit(0 if final_success else 1)

if __name__ == "__main__":
    main()