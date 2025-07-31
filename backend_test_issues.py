#!/usr/bin/env python3
"""
MITOSIS BACKEND TESTING FOR SPECIFIC REPORTED ISSUES
Testing the two critical issues reported in the review request:

CRITICAL ISSUES TO TEST:
1. **File Fetching SyntaxError**: Test the `/api/agent/get-task-files/{task_id}` endpoint 
   to see if it's returning HTML instead of JSON, causing the `SyntaxError: Unexpected token '<'` on the frontend.

2. **Missing Auto-Execution Endpoint**: Test the `/api/agent/start-task-execution/{task_id}` endpoint 
   to check if it returns 404 or if there's another routing issue.

ADDITIONAL TESTS:
3. Backend health and basic endpoints
4. CORS or routing issues
5. Response formats (JSON vs HTML)

BACKEND URL: https://7ac24ada-9a56-4ac5-8359-affff70362b6.preview.emergentagent.com
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://7ac24ada-9a56-4ac5-8359-affff70362b6.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisBackendIssuesTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://7ac24ada-9a56-4ac5-8359-affff70362b6.preview.emergentagent.com'
        })
        self.test_results = []
        self.task_id = None
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)[:500]}...")
    
    def test_backend_health(self) -> bool:
        """Test 1: Backend Health Check"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                database_ok = services.get('database', False)
                ollama_ok = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                
                if database_ok and ollama_ok and tools_count > 0:
                    self.log_test("Backend Health", True, 
                                f"Backend healthy - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}")
                    return True
                else:
                    self.log_test("Backend Health", False, 
                                f"Some services unhealthy - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}", data)
                    return False
            else:
                self.log_test("Backend Health", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Backend Health", False, f"Exception: {str(e)}")
            return False
    
    def create_test_task(self) -> str:
        """Create a test task and return task_id"""
        try:
            payload = {"message": "Create a test task for file testing"}
            response = self.session.post(f"{API_BASE}/agent/chat", json=payload, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id', '')
                if task_id:
                    print(f"   Created test task with ID: {task_id}")
                    return task_id
            
            # Fallback to a generic task ID
            return "test-task-123"
            
        except Exception as e:
            print(f"   Failed to create test task: {e}")
            return "test-task-123"
    
    def test_file_fetching_endpoint(self) -> bool:
        """Test 2: File Fetching Endpoint - Check for HTML vs JSON issue"""
        try:
            # Create a test task first
            if not self.task_id:
                self.task_id = self.create_test_task()
            
            # Test the specific endpoint mentioned in the issue
            file_endpoint = f"{API_BASE}/agent/get-task-files/{self.task_id}"
            
            print(f"\n🎯 Testing file fetching endpoint: {file_endpoint}")
            
            response = self.session.get(file_endpoint, timeout=15)
            
            # Check response content type
            content_type = response.headers.get('Content-Type', '').lower()
            is_json_content_type = 'application/json' in content_type
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Content-Type: {content_type}")
            print(f"   Response Length: {len(response.text)} chars")
            
            # Check if response starts with HTML
            response_text = response.text.strip()
            is_html_response = response_text.startswith('<!DOCTYPE html>') or response_text.startswith('<html')
            
            # Try to parse as JSON
            is_valid_json = False
            json_data = None
            try:
                json_data = response.json()
                is_valid_json = True
            except:
                is_valid_json = False
            
            # Log detailed findings
            print(f"   Is HTML Response: {is_html_response}")
            print(f"   Is Valid JSON: {is_valid_json}")
            print(f"   JSON Content-Type: {is_json_content_type}")
            
            if response.status_code == 200:
                if is_valid_json and not is_html_response:
                    self.log_test("File Fetching Endpoint", True, 
                                f"Endpoint returns valid JSON - Status: {response.status_code}, JSON: {is_valid_json}, HTML: {is_html_response}")
                    return True
                elif is_html_response:
                    self.log_test("File Fetching Endpoint", False, 
                                f"CRITICAL: Endpoint returns HTML instead of JSON - This causes SyntaxError on frontend", 
                                {"response_preview": response_text[:200], "content_type": content_type})
                    return False
                else:
                    self.log_test("File Fetching Endpoint", False, 
                                f"Endpoint returns invalid JSON - Status: {response.status_code}, JSON: {is_valid_json}", 
                                {"response_preview": response_text[:200], "content_type": content_type})
                    return False
            elif response.status_code == 404:
                # 404 is acceptable if no files exist yet, but should still be JSON
                if is_valid_json and not is_html_response:
                    self.log_test("File Fetching Endpoint", True, 
                                f"Endpoint returns proper 404 JSON response - No files found but format is correct")
                    return True
                else:
                    self.log_test("File Fetching Endpoint", False, 
                                f"404 response is HTML instead of JSON - This causes SyntaxError on frontend", 
                                {"response_preview": response_text[:200], "content_type": content_type})
                    return False
            else:
                self.log_test("File Fetching Endpoint", False, 
                            f"Unexpected status code: {response.status_code}", 
                            {"response_preview": response_text[:200], "content_type": content_type})
                return False
                
        except Exception as e:
            self.log_test("File Fetching Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_auto_execution_endpoint(self) -> bool:
        """Test 3: Auto-Execution Endpoint - Check for 404 or routing issues"""
        try:
            # Create a test task first
            if not self.task_id:
                self.task_id = self.create_test_task()
            
            # Test the specific endpoint mentioned in the issue
            execution_endpoint = f"{API_BASE}/agent/start-task-execution/{self.task_id}"
            
            print(f"\n🎯 Testing auto-execution endpoint: {execution_endpoint}")
            
            # Test with POST method (most likely for starting execution)
            response = self.session.post(execution_endpoint, json={}, timeout=15)
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"   Response Length: {len(response.text)} chars")
            
            # Check if it's a 404 (endpoint not found)
            if response.status_code == 404:
                # Check if it's returning HTML 404 page or JSON 404
                try:
                    json_data = response.json()
                    self.log_test("Auto-Execution Endpoint", False, 
                                f"Endpoint returns 404 - Route not implemented or incorrect path", 
                                {"json_response": json_data})
                    return False
                except:
                    # HTML 404 page
                    self.log_test("Auto-Execution Endpoint", False, 
                                f"Endpoint returns HTML 404 - Route definitely not found", 
                                {"response_preview": response.text[:200]})
                    return False
            
            elif response.status_code in [200, 201, 202]:
                # Success responses
                try:
                    json_data = response.json()
                    self.log_test("Auto-Execution Endpoint", True, 
                                f"Endpoint working - Status: {response.status_code}, returns valid JSON")
                    return True
                except:
                    self.log_test("Auto-Execution Endpoint", False, 
                                f"Endpoint returns {response.status_code} but invalid JSON", 
                                {"response_preview": response.text[:200]})
                    return False
            
            elif response.status_code == 400:
                # Bad request - endpoint exists but may need different parameters
                try:
                    json_data = response.json()
                    self.log_test("Auto-Execution Endpoint", True, 
                                f"Endpoint exists but needs different parameters - Status: 400, JSON response")
                    return True
                except:
                    self.log_test("Auto-Execution Endpoint", False, 
                                f"Endpoint returns 400 but invalid JSON", 
                                {"response_preview": response.text[:200]})
                    return False
            
            elif response.status_code == 405:
                # Method not allowed - try GET method
                get_response = self.session.get(execution_endpoint, timeout=15)
                print(f"   GET Response Status: {get_response.status_code}")
                
                if get_response.status_code in [200, 400]:
                    self.log_test("Auto-Execution Endpoint", True, 
                                f"Endpoint exists but requires GET method - POST: 405, GET: {get_response.status_code}")
                    return True
                else:
                    self.log_test("Auto-Execution Endpoint", False, 
                                f"Method not allowed and GET also fails - POST: 405, GET: {get_response.status_code}")
                    return False
            
            else:
                # Other status codes
                try:
                    json_data = response.json()
                    self.log_test("Auto-Execution Endpoint", False, 
                                f"Unexpected status code: {response.status_code}", 
                                {"json_response": json_data})
                    return False
                except:
                    self.log_test("Auto-Execution Endpoint", False, 
                                f"Unexpected status code with invalid JSON: {response.status_code}", 
                                {"response_preview": response.text[:200]})
                    return False
                
        except Exception as e:
            self.log_test("Auto-Execution Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_basic_endpoints(self) -> bool:
        """Test 4: Basic Endpoints Functionality"""
        try:
            # Test multiple basic endpoints
            endpoints_to_test = [
                ("/agent/status", "GET"),
                ("/agent/health", "GET"),
                ("/health", "GET")
            ]
            
            working_endpoints = 0
            total_endpoints = len(endpoints_to_test)
            
            for endpoint, method in endpoints_to_test:
                try:
                    if method == "GET":
                        response = self.session.get(f"{API_BASE}{endpoint}", timeout=10)
                    else:
                        response = self.session.post(f"{API_BASE}{endpoint}", json={}, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            response.json()  # Verify it's valid JSON
                            working_endpoints += 1
                            print(f"   ✅ {endpoint} - Status: {response.status_code}, JSON: ✓")
                        except:
                            print(f"   ⚠️ {endpoint} - Status: {response.status_code}, JSON: ✗")
                    else:
                        print(f"   ❌ {endpoint} - Status: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ {endpoint} - Exception: {str(e)}")
            
            success_rate = (working_endpoints / total_endpoints) * 100
            
            if success_rate >= 80:
                self.log_test("Basic Endpoints", True, 
                            f"Basic endpoints working - {working_endpoints}/{total_endpoints} ({success_rate:.0f}%)")
                return True
            else:
                self.log_test("Basic Endpoints", False, 
                            f"Basic endpoints issues - {working_endpoints}/{total_endpoints} ({success_rate:.0f}%)")
                return False
                
        except Exception as e:
            self.log_test("Basic Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_cors_and_routing(self) -> bool:
        """Test 5: CORS and Routing Issues"""
        try:
            # Test CORS headers on critical endpoints
            test_endpoints = [
                f"{API_BASE}/agent/chat",
                f"{API_BASE}/agent/get-task-files/test-task",
                f"{API_BASE}/agent/start-task-execution/test-task"
            ]
            
            cors_working = 0
            total_tests = len(test_endpoints)
            
            for endpoint in test_endpoints:
                try:
                    # Test OPTIONS request for CORS preflight
                    options_response = self.session.options(endpoint, timeout=10)
                    
                    # Check for CORS headers
                    cors_origin = options_response.headers.get('Access-Control-Allow-Origin')
                    cors_methods = options_response.headers.get('Access-Control-Allow-Methods')
                    cors_headers = options_response.headers.get('Access-Control-Allow-Headers')
                    
                    has_cors = any([cors_origin, cors_methods, cors_headers])
                    
                    if has_cors:
                        cors_working += 1
                        print(f"   ✅ CORS OK for {endpoint.split('/')[-2:]}")
                    else:
                        print(f"   ❌ No CORS headers for {endpoint.split('/')[-2:]}")
                        
                except Exception as e:
                    print(f"   ❌ CORS test failed for {endpoint.split('/')[-2:]}: {str(e)}")
            
            success_rate = (cors_working / total_tests) * 100
            
            if success_rate >= 70:
                self.log_test("CORS and Routing", True, 
                            f"CORS working - {cors_working}/{total_tests} ({success_rate:.0f}%)")
                return True
            else:
                self.log_test("CORS and Routing", False, 
                            f"CORS issues detected - {cors_working}/{total_tests} ({success_rate:.0f}%)")
                return False
                
        except Exception as e:
            self.log_test("CORS and Routing", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests focused on the reported issues"""
        print("🧪 STARTING MITOSIS BACKEND ISSUES TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing specific reported issues")
        print("📋 CRITICAL ISSUES:")
        print("   1. File Fetching SyntaxError (HTML vs JSON)")
        print("   2. Missing Auto-Execution Endpoint (404 errors)")
        print("🔍 BACKEND URL:", BACKEND_URL)
        print("=" * 80)
        
        # Test sequence focused on reported issues
        tests = [
            ("Backend Health", self.test_backend_health),
            ("File Fetching Endpoint", self.test_file_fetching_endpoint),
            ("Auto-Execution Endpoint", self.test_auto_execution_endpoint),
            ("Basic Endpoints", self.test_basic_endpoints),
            ("CORS and Routing", self.test_cors_and_routing)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 80)
        print("🎯 MITOSIS BACKEND ISSUES TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ BACKEND WORKING PERFECTLY"
        elif success_rate >= 70:
            overall_status = "⚠️ BACKEND MOSTLY WORKING - Minor issues detected"
        elif success_rate >= 50:
            overall_status = "⚠️ BACKEND PARTIAL - Significant issues found"
        else:
            overall_status = "❌ BACKEND CRITICAL - Major issues preventing functionality"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for the reported issues
        critical_tests = ["File Fetching Endpoint", "Auto-Execution Endpoint"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL REPORTED ISSUES:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ Both reported issues are resolved")
            print("   🎯 CONCLUSION: Backend endpoints are working correctly")
        else:
            print("   ❌ One or both reported issues are still present")
            print("   🎯 CONCLUSION: Backend has issues that need to be fixed")
        
        # Specific findings for each reported issue
        print(f"\n🔍 SPECIFIC ISSUE ANALYSIS:")
        
        file_result = next((r for r in self.test_results if r['test_name'] == 'File Fetching Endpoint'), None)
        if file_result and file_result['success']:
            print("   ✅ ISSUE 1 RESOLVED: File fetching endpoint returns proper JSON (no SyntaxError)")
        elif file_result:
            print("   ❌ ISSUE 1 PRESENT: File fetching endpoint returns HTML instead of JSON (causes SyntaxError)")
        
        execution_result = next((r for r in self.test_results if r['test_name'] == 'Auto-Execution Endpoint'), None)
        if execution_result and execution_result['success']:
            print("   ✅ ISSUE 2 RESOLVED: Auto-execution endpoint is available and working")
        elif execution_result:
            print("   ❌ ISSUE 2 PRESENT: Auto-execution endpoint returns 404 or has routing issues")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id,
            'backend_working': critical_passed >= 1,  # If at least 1 critical test passes
            'file_fetching_working': file_result and file_result['success'] if file_result else False,
            'auto_execution_working': execution_result and execution_result['success'] if execution_result else False
        }

def main():
    """Main testing function"""
    tester = MitosisBackendIssuesTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/backend_issues_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR MAIN AGENT")
    print("=" * 80)
    
    if results['file_fetching_working'] and results['auto_execution_working']:
        print("✅ DIAGNOSIS: Both reported issues are resolved")
        print("📋 RECOMMENDATION: Backend endpoints are working correctly")
        print("🔧 NEXT STEPS: Frontend should be able to communicate with backend without issues")
    elif results['file_fetching_working']:
        print("⚠️ DIAGNOSIS: File fetching issue resolved, but auto-execution endpoint still has problems")
        print("📋 RECOMMENDATION: Fix the auto-execution endpoint routing")
        print("🔧 NEXT STEPS: Implement or fix the /api/agent/start-task-execution/{task_id} endpoint")
    elif results['auto_execution_working']:
        print("⚠️ DIAGNOSIS: Auto-execution endpoint working, but file fetching returns HTML instead of JSON")
        print("📋 RECOMMENDATION: Fix the file fetching endpoint to return proper JSON")
        print("🔧 NEXT STEPS: Ensure /api/agent/get-task-files/{task_id} returns JSON, not HTML")
    else:
        print("❌ DIAGNOSIS: Both reported issues are still present")
        print("📋 RECOMMENDATION: Fix both endpoints - file fetching and auto-execution")
        print("🔧 NEXT STEPS: Address both routing and response format issues")
    
    # Specific issue details
    print(f"\n🔍 ISSUE-SPECIFIC FINDINGS:")
    
    if results.get('file_fetching_working'):
        print("✅ ISSUE 1 STATUS: File fetching endpoint returns proper JSON format")
    else:
        print("❌ ISSUE 1 STATUS: File fetching endpoint returns HTML instead of JSON (causes SyntaxError)")
    
    if results.get('auto_execution_working'):
        print("✅ ISSUE 2 STATUS: Auto-execution endpoint is available and accessible")
    else:
        print("❌ ISSUE 2 STATUS: Auto-execution endpoint returns 404 or has routing issues")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 BACKEND ISSUES TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ BACKEND ISSUES TESTING COMPLETED WITH PROBLEMS")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)