#!/usr/bin/env python3
"""
MITOSIS BACKEND HEALTH AND FUNCTIONALITY TESTING
Testing backend health and functionality to resolve React Error #306 and frontend blank page issue:

1. Test all /api/agent/ endpoints are working correctly
2. Verify the /api/health endpoint returns correct status
3. Test that CORS is configured correctly for the frontend domain
4. Verify that WebSocket endpoint /socket.io/ is accessible
5. Test a simple chat request to /api/agent/chat to ensure backend processing is working

CRITICAL OBJECTIVE: Identify and resolve backend communication issues preventing React from completing its render cycle.
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://e5264aee-8866-49fb-a2eb-7a4c7b869c9e.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisBackendHealthTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://e5264aee-8866-49fb-a2eb-7a4c7b869c9e.preview.emergentagent.com'
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
    
    def test_backend_health_endpoint(self) -> bool:
        """Test 1: Backend Health Endpoint (/api/health)"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                # Check critical services
                database_ok = services.get('database', False)
                ollama_ok = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                if database_ok and ollama_ok and tools_count > 0:
                    self.log_test("Backend Health Endpoint", True, 
                                f"Health endpoint working - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}, CORS: {bool(cors_headers['Access-Control-Allow-Origin'])}")
                    return True
                else:
                    self.log_test("Backend Health Endpoint", False, 
                                f"Some services unhealthy - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}", data)
                    return False
            else:
                self.log_test("Backend Health Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Backend Health Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_cors_configuration(self) -> bool:
        """Test 2: CORS Configuration for Frontend Domain"""
        try:
            # Test OPTIONS request (preflight)
            options_response = self.session.options(f"{API_BASE}/agent/status", timeout=10)
            
            # Test GET request with Origin header
            get_response = self.session.get(f"{API_BASE}/agent/status", timeout=10)
            
            # Check CORS headers in both responses
            cors_checks = []
            
            for response, req_type in [(options_response, "OPTIONS"), (get_response, "GET")]:
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                cors_methods = response.headers.get('Access-Control-Allow-Methods')
                cors_headers = response.headers.get('Access-Control-Allow-Headers')
                
                cors_checks.append({
                    'type': req_type,
                    'status': response.status_code,
                    'origin': cors_origin,
                    'methods': cors_methods,
                    'headers': cors_headers
                })
            
            # Evaluate CORS configuration
            cors_working = True
            cors_details = []
            
            for check in cors_checks:
                if check['status'] not in [200, 204]:
                    cors_working = False
                    cors_details.append(f"{check['type']} failed with {check['status']}")
                elif not check['origin'] or check['origin'] not in ['*', BACKEND_URL]:
                    cors_working = False
                    cors_details.append(f"{check['type']} missing/invalid CORS origin: {check['origin']}")
                else:
                    cors_details.append(f"{check['type']} CORS OK")
            
            if cors_working:
                self.log_test("CORS Configuration", True, 
                            f"CORS properly configured - {', '.join(cors_details)}")
                return True
            else:
                self.log_test("CORS Configuration", False, 
                            f"CORS issues detected - {', '.join(cors_details)}", cors_checks)
                return False
                
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_endpoint_accessibility(self) -> bool:
        """Test 3: WebSocket Endpoint Accessibility (/socket.io/)"""
        try:
            # Test if the WebSocket endpoint is accessible
            # We can't test actual WebSocket connection with requests, but we can test the HTTP endpoint
            websocket_url = f"{BACKEND_URL}/socket.io/"
            
            response = self.session.get(websocket_url, timeout=10, params={'transport': 'polling'})
            
            # Socket.IO typically returns specific responses for polling transport
            if response.status_code in [200, 400]:  # 400 is also acceptable for Socket.IO
                # Check if response contains Socket.IO indicators
                response_text = response.text.lower()
                socketio_indicators = ['socket.io', 'transport', 'polling', 'websocket']
                
                indicators_found = sum(1 for indicator in socketio_indicators if indicator in response_text)
                
                if indicators_found >= 2 or 'socket.io' in response_text:
                    self.log_test("WebSocket Endpoint Accessibility", True, 
                                f"WebSocket endpoint accessible - HTTP {response.status_code}, Socket.IO indicators found")
                    return True
                else:
                    self.log_test("WebSocket Endpoint Accessibility", False, 
                                f"WebSocket endpoint responds but no Socket.IO indicators - HTTP {response.status_code}")
                    return False
            else:
                self.log_test("WebSocket Endpoint Accessibility", False, 
                            f"WebSocket endpoint not accessible - HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Endpoint Accessibility", False, f"Exception: {str(e)}")
            return False
    
    def test_agent_endpoints_functionality(self) -> bool:
        """Test 4: All /api/agent/ Endpoints Functionality"""
        try:
            endpoints_to_test = [
                ('/api/agent/status', 'GET'),
                ('/api/agent/config/current', 'GET'),
                ('/api/agent/generate-suggestions', 'POST')
            ]
            
            endpoint_results = []
            
            for endpoint, method in endpoints_to_test:
                try:
                    if method == 'GET':
                        response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    else:  # POST
                        response = self.session.post(f"{BACKEND_URL}{endpoint}", json={}, timeout=10)
                    
                    endpoint_results.append({
                        'endpoint': endpoint,
                        'method': method,
                        'status': response.status_code,
                        'success': response.status_code == 200,
                        'response_size': len(response.text) if response.text else 0
                    })
                    
                except Exception as e:
                    endpoint_results.append({
                        'endpoint': endpoint,
                        'method': method,
                        'status': 'ERROR',
                        'success': False,
                        'error': str(e)
                    })
            
            # Evaluate results
            successful_endpoints = sum(1 for result in endpoint_results if result['success'])
            total_endpoints = len(endpoint_results)
            
            if successful_endpoints >= total_endpoints * 0.75:  # At least 75% working
                self.log_test("Agent Endpoints Functionality", True, 
                            f"Agent endpoints working - {successful_endpoints}/{total_endpoints} endpoints successful")
                return True
            else:
                failed_endpoints = [r['endpoint'] for r in endpoint_results if not r['success']]
                self.log_test("Agent Endpoints Functionality", False, 
                            f"Multiple agent endpoints failing - {successful_endpoints}/{total_endpoints} successful, failed: {failed_endpoints}", endpoint_results)
                return False
                
        except Exception as e:
            self.log_test("Agent Endpoints Functionality", False, f"Exception: {str(e)}")
            return False
    
    def test_chat_endpoint_processing(self) -> bool:
        """Test 5: Chat Endpoint Processing (/api/agent/chat)"""
        try:
            # Test simple chat request to ensure backend processing is working
            test_message = "Hello, can you help me with a simple task?"
            
            payload = {
                "message": test_message
            }
            
            print(f"\n🎯 Testing chat endpoint processing with: {test_message}")
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required response fields that indicate proper processing
                response_text = data.get('response', '')
                task_id = data.get('task_id', '')
                memory_used = data.get('memory_used', False)
                timestamp = data.get('timestamp', '')
                
                # Store task_id for potential later use
                if task_id:
                    self.task_id = task_id
                
                # Check response quality
                processing_indicators = [
                    bool(response_text and len(response_text) > 10),  # Meaningful response
                    bool(task_id),  # Task ID generated
                    bool(timestamp),  # Timestamp present
                    memory_used is True  # Memory system working
                ]
                
                successful_indicators = sum(processing_indicators)
                
                if successful_indicators >= 3:  # At least 3 out of 4 indicators
                    self.log_test("Chat Endpoint Processing", True, 
                                f"Chat processing working - Response: {len(response_text)} chars, Task ID: {bool(task_id)}, Memory: {memory_used}")
                    return True
                else:
                    self.log_test("Chat Endpoint Processing", False, 
                                f"Chat processing incomplete - Response: {bool(response_text)}, Task ID: {bool(task_id)}, Memory: {memory_used}, Timestamp: {bool(timestamp)}", data)
                    return False
            else:
                self.log_test("Chat Endpoint Processing", False, 
                            f"Chat endpoint failed - HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Chat Endpoint Processing", False, f"Exception: {str(e)}")
            return False
    
    def test_backend_response_format(self) -> bool:
        """Test 6: Backend Response Format Compatibility"""
        try:
            # Test multiple endpoints to ensure consistent JSON response format
            test_endpoints = [
                ('/api/health', 'GET', {}),
                ('/api/agent/status', 'GET', {}),
                ('/api/agent/chat', 'POST', {"message": "Test response format"})
            ]
            
            format_results = []
            
            for endpoint, method, payload in test_endpoints:
                try:
                    if method == 'GET':
                        response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=15)
                    else:
                        response = self.session.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=15)
                    
                    # Check response format
                    format_check = {
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'content_type': response.headers.get('Content-Type', ''),
                        'is_json': False,
                        'has_timestamp': False,
                        'has_status': False
                    }
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            format_check['is_json'] = True
                            format_check['has_timestamp'] = 'timestamp' in data
                            format_check['has_status'] = 'status' in data or 'response' in data
                        except:
                            pass
                    
                    format_results.append(format_check)
                    
                except Exception as e:
                    format_results.append({
                        'endpoint': endpoint,
                        'error': str(e),
                        'is_json': False
                    })
            
            # Evaluate format consistency
            json_responses = sum(1 for r in format_results if r.get('is_json', False))
            total_responses = len([r for r in format_results if r.get('status_code') == 200])
            
            if total_responses > 0 and json_responses == total_responses:
                self.log_test("Backend Response Format", True, 
                            f"Response format consistent - {json_responses}/{total_responses} endpoints return valid JSON")
                return True
            else:
                self.log_test("Backend Response Format", False, 
                            f"Response format inconsistent - {json_responses}/{total_responses} endpoints return valid JSON", format_results)
                return False
                
        except Exception as e:
            self.log_test("Backend Response Format", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling_and_status_codes(self) -> bool:
        """Test 7: Error Handling and HTTP Status Codes"""
        try:
            # Test various error scenarios
            error_tests = [
                # Invalid endpoint
                ('/api/agent/nonexistent', 'GET', {}, [404]),
                # Invalid method
                ('/api/agent/status', 'DELETE', {}, [405, 404]),
                # Missing required fields
                ('/api/agent/chat', 'POST', {}, [400, 422])
            ]
            
            error_handling_results = []
            
            for endpoint, method, payload, expected_codes in error_tests:
                try:
                    if method == 'GET':
                        response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    elif method == 'POST':
                        response = self.session.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=10)
                    else:  # DELETE or other methods
                        response = self.session.request(method, f"{BACKEND_URL}{endpoint}", timeout=10)
                    
                    error_handling_results.append({
                        'test': f"{method} {endpoint}",
                        'status_code': response.status_code,
                        'expected': expected_codes,
                        'correct': response.status_code in expected_codes,
                        'has_error_message': 'error' in response.text.lower() if response.text else False
                    })
                    
                except Exception as e:
                    error_handling_results.append({
                        'test': f"{method} {endpoint}",
                        'error': str(e),
                        'correct': False
                    })
            
            # Evaluate error handling
            correct_responses = sum(1 for r in error_handling_results if r.get('correct', False))
            total_tests = len(error_handling_results)
            
            if correct_responses >= total_tests * 0.75:  # At least 75% correct
                self.log_test("Error Handling and Status Codes", True, 
                            f"Error handling working - {correct_responses}/{total_tests} error scenarios handled correctly")
                return True
            else:
                self.log_test("Error Handling and Status Codes", False, 
                            f"Error handling issues - {correct_responses}/{total_tests} error scenarios handled correctly", error_handling_results)
                return False
                
        except Exception as e:
            self.log_test("Error Handling and Status Codes", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend health and functionality tests"""
        print("🧪 STARTING MITOSIS BACKEND HEALTH AND FUNCTIONALITY TESTING")
        print("🎯 OBJECTIVE: Resolve React Error #306 and frontend blank page issue")
        print("=" * 80)
        
        # Test sequence focused on backend communication issues
        tests = [
            ("Backend Health Endpoint", self.test_backend_health_endpoint),
            ("CORS Configuration", self.test_cors_configuration),
            ("WebSocket Endpoint Accessibility", self.test_websocket_endpoint_accessibility),
            ("Agent Endpoints Functionality", self.test_agent_endpoints_functionality),
            ("Chat Endpoint Processing", self.test_chat_endpoint_processing),
            ("Backend Response Format", self.test_backend_response_format),
            ("Error Handling and Status Codes", self.test_error_handling_and_status_codes)
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
        print("🎯 BACKEND HEALTH AND FUNCTIONALITY TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ EXCELLENT - Backend is fully operational for frontend communication"
        elif success_rate >= 70:
            overall_status = "⚠️ GOOD - Backend mostly working with minor communication issues"
        elif success_rate >= 50:
            overall_status = "⚠️ PARTIAL - Backend has significant issues affecting frontend communication"
        else:
            overall_status = "❌ CRITICAL - Backend has major issues preventing frontend communication"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for React Error #306 resolution
        critical_tests = ["Backend Health Endpoint", "CORS Configuration", "Chat Endpoint Processing", "Backend Response Format"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL BACKEND COMMUNICATION FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical backend communication functionality is working")
            print("   ✅ Backend should support proper React rendering")
        else:
            print("   ❌ Some critical backend communication functionality is failing")
            print("   ❌ This may be causing React Error #306 and blank page issue")
        
        # Specific recommendations for React Error #306
        print(f"\n🩺 REACT ERROR #306 DIAGNOSIS:")
        if critical_passed == len(critical_tests):
            print("   ✅ Backend communication appears healthy")
            print("   ➡️ React Error #306 likely caused by frontend issues, not backend")
            print("   ➡️ Check frontend error boundaries, component lifecycle, or state management")
        else:
            failed_critical = [result['test_name'] for result in self.test_results 
                             if result['test_name'] in critical_tests and not result['success']]
            print("   ❌ Backend communication issues detected:")
            for failed_test in failed_critical:
                print(f"      - {failed_test}")
            print("   ➡️ Fix these backend issues to resolve React Error #306")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id,
            'react_error_diagnosis': {
                'backend_healthy': critical_passed == len(critical_tests),
                'likely_cause': 'frontend' if critical_passed == len(critical_tests) else 'backend',
                'failed_critical_tests': [r['test_name'] for r in self.test_results 
                                        if r['test_name'] in critical_tests and not r['success']]
            }
        }

def main():
    """Main testing function"""
    tester = MitosisBackendHealthTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/backend_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 BACKEND HEALTH TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ BACKEND HEALTH TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)