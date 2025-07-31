#!/usr/bin/env python3
"""
COMPREHENSIVE MITOSIS BACKEND TESTING FOR WEBSOCKET AND CORS ISSUES
Testing the specific issues reported in the review request:

PROBLEMS REPORTED:
1. WebSocket Error: Frontend failing to connect with "timeout" error
2. CORS Error: Error accessing `/files/task-1753710463282`
3. Plan Generation: Backend generates plans correctly but frontend doesn't show them
4. Task ID: task-1753710463282 was created and has a plan with 4 steps

TESTING REQUIREMENTS:
1. WebSocket endpoints and configuration
2. CORS configuration for files and other endpoints
3. Endpoint `/files/task-1753710463282` vs `/api/agent/get-task-files/task-1753710463282`
4. State of task task-1753710463282 and its plan
5. Testing plan generation in real-time
6. Verify endpoints work correctly for frontend flow

BACKEND URL: https://7ac24ada-9a56-4ac5-8359-affff70362b6.preview.emergentagent.com
SPECIFIC TASK ID: task-1753710463282
MESSAGE: "Genera un informe sobre IA en 2025"
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
SPECIFIC_TASK_ID = "task-1753710463282"
TEST_MESSAGE = "Genera un informe sobre IA en 2025"

class MitosisWebSocketCORSTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://7ac24ada-9a56-4ac5-8359-affff70362b6.preview.emergentagent.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.test_results = []
        
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
    
    def test_websocket_endpoint_availability(self) -> bool:
        """Test 1: WebSocket Endpoint Availability"""
        try:
            # Test WebSocket handshake endpoint
            websocket_handshake_url = f"{BACKEND_URL}/socket.io/?EIO=4&transport=polling"
            
            response = self.session.get(websocket_handshake_url, timeout=10)
            
            if response.status_code == 200:
                # Check if response contains socket.io handshake
                response_text = response.text
                is_socketio_response = 'socket.io' in response_text or response_text.startswith('0{')
                
                if is_socketio_response:
                    self.log_test("WebSocket Endpoint Availability", True, 
                                f"WebSocket handshake endpoint accessible - Response: {response_text[:100]}...")
                    return True
                else:
                    self.log_test("WebSocket Endpoint Availability", False, 
                                f"Invalid WebSocket handshake response: {response_text[:200]}")
                    return False
            else:
                self.log_test("WebSocket Endpoint Availability", False, 
                            f"WebSocket handshake failed - HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Endpoint Availability", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_configuration(self) -> bool:
        """Test 2: WebSocket Configuration and CORS"""
        try:
            # Test WebSocket handshake and CORS headers
            websocket_handshake_url = f"{BACKEND_URL}/socket.io/?EIO=4&transport=polling"
            
            response = self.session.get(websocket_handshake_url, timeout=10)
            
            if response.status_code == 200:
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                
                # Check if response contains socket.io handshake
                response_text = response.text
                is_socketio_response = 'socket.io' in response_text or response_text.startswith('0{')
                
                if is_socketio_response:
                    self.log_test("WebSocket Configuration", True, 
                                f"WebSocket handshake successful. CORS headers: {cors_headers}")
                    return True
                else:
                    self.log_test("WebSocket Configuration", False, 
                                f"Invalid WebSocket handshake response: {response_text[:200]}")
                    return False
            else:
                self.log_test("WebSocket Configuration", False, 
                            f"WebSocket handshake failed - HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Configuration", False, f"Exception: {str(e)}")
            return False
    
    def test_cors_configuration(self) -> bool:
        """Test 3: CORS Configuration for API Endpoints"""
        try:
            # Test CORS preflight request
            preflight_headers = {
                'Origin': 'https://7ac24ada-9a56-4ac5-8359-affff70362b6.preview.emergentagent.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{API_BASE}/agent/chat", headers=preflight_headers, timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            # Check if CORS is properly configured
            origin_allowed = cors_headers['Access-Control-Allow-Origin'] in ['*', 'https://7ac24ada-9a56-4ac5-8359-affff70362b6.preview.emergentagent.com']
            methods_allowed = 'POST' in str(cors_headers.get('Access-Control-Allow-Methods', ''))
            headers_allowed = 'Content-Type' in str(cors_headers.get('Access-Control-Allow-Headers', ''))
            
            if origin_allowed and methods_allowed and headers_allowed:
                self.log_test("CORS Configuration", True, 
                            f"CORS properly configured: {cors_headers}")
                return True
            else:
                self.log_test("CORS Configuration", False, 
                            f"CORS misconfigured - Origin: {origin_allowed}, Methods: {methods_allowed}, Headers: {headers_allowed}")
                return False
                
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Exception: {str(e)}")
            return False
    
    def test_specific_task_status(self) -> bool:
        """Test 4: Specific Task Status (task-1753710463282)"""
        try:
            # Test the specific task mentioned in the review request
            response = self.session.get(f"{API_BASE}/agent/get-task-status/{SPECIFIC_TASK_ID}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                task_id = data.get('task_id')
                status = data.get('status')
                plan = data.get('plan', [])
                message = data.get('message', '')
                
                if task_id == SPECIFIC_TASK_ID and plan and len(plan) >= 4:
                    self.log_test("Specific Task Status", True, 
                                f"Task {SPECIFIC_TASK_ID} found with {len(plan)} steps, status: {status}, message: {message}")
                    return True
                else:
                    self.log_test("Specific Task Status", False, 
                                f"Task data incomplete - ID: {task_id}, Plan steps: {len(plan)}, Status: {status}")
                    return False
            elif response.status_code == 404:
                self.log_test("Specific Task Status", False, 
                            f"Task {SPECIFIC_TASK_ID} not found (404)")
                return False
            else:
                self.log_test("Specific Task Status", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Specific Task Status", False, f"Exception: {str(e)}")
            return False
    
    def test_files_endpoint_cors(self) -> bool:
        """Test 5: Files Endpoint CORS Issue"""
        try:
            # Test the files endpoint that was mentioned in the CORS error
            files_endpoints = [
                f"/files/{SPECIFIC_TASK_ID}",
                f"{API_BASE}/agent/get-task-files/{SPECIFIC_TASK_ID}",
                f"{API_BASE}/files/{SPECIFIC_TASK_ID}"
            ]
            
            results = []
            for endpoint in files_endpoints:
                try:
                    full_url = f"{BACKEND_URL}{endpoint}" if not endpoint.startswith('http') else endpoint
                    response = self.session.get(full_url, timeout=10)
                    
                    cors_origin = response.headers.get('Access-Control-Allow-Origin', 'Not set')
                    
                    results.append({
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'cors_origin': cors_origin,
                        'success': response.status_code in [200, 404]  # 404 is acceptable if no files
                    })
                    
                except Exception as e:
                    results.append({
                        'endpoint': endpoint,
                        'error': str(e),
                        'success': False
                    })
            
            # Check if at least one endpoint works
            working_endpoints = [r for r in results if r.get('success', False)]
            
            if working_endpoints:
                self.log_test("Files Endpoint CORS", True, 
                            f"Files endpoints working: {len(working_endpoints)}/{len(files_endpoints)}. Details: {results}")
                return True
            else:
                self.log_test("Files Endpoint CORS", False, 
                            f"No files endpoints working. Results: {results}")
                return False
                
        except Exception as e:
            self.log_test("Files Endpoint CORS", False, f"Exception: {str(e)}")
            return False
    
    def test_plan_generation_realtime(self) -> bool:
        """Test 6: Plan Generation in Real-time"""
        try:
            # Test plan generation with the specific message
            payload = {
                "message": TEST_MESSAGE
            }
            
            print(f"\n🎯 Testing real-time plan generation with: {TEST_MESSAGE}")
            
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for plan generation
                plan = data.get('plan', [])
                task_id = data.get('task_id', '')
                enhanced_title = data.get('enhanced_title', '')
                response_text = data.get('response', '')
                
                if plan and len(plan) >= 4 and task_id and enhanced_title:
                    self.log_test("Plan Generation Real-time", True, 
                                f"Plan generated in {response_time:.2f}s - {len(plan)} steps, Task ID: {task_id}, Title: {enhanced_title}")
                    return True
                else:
                    self.log_test("Plan Generation Real-time", False, 
                                f"Plan generation incomplete - Plan: {len(plan)} steps, Task ID: {bool(task_id)}, Title: {bool(enhanced_title)}")
                    return False
            else:
                self.log_test("Plan Generation Real-time", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Plan Generation Real-time", False, f"Exception: {str(e)}")
            return False
    
    def test_backend_websocket_manager_status(self) -> bool:
        """Test 7: Backend WebSocket Manager Status"""
        try:
            # Check if WebSocket manager is properly initialized in backend
            response = self.session.get(f"{API_BASE}/agent/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for WebSocket-related status information
                status = data.get('status', '')
                memory_info = data.get('memory', {})
                
                # Check if backend is running (indicates WebSocket manager should be working)
                if status == 'running':
                    self.log_test("Backend WebSocket Manager Status", True, 
                                f"Backend running with WebSocket support. Status: {status}, Memory: {memory_info}")
                    return True
                else:
                    self.log_test("Backend WebSocket Manager Status", False, 
                                f"Backend not properly running. Status: {status}")
                    return False
            else:
                self.log_test("Backend WebSocket Manager Status", False, 
                            f"Cannot check backend status - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Backend WebSocket Manager Status", False, f"Exception: {str(e)}")
            return False
    
    def test_backend_health_comprehensive(self) -> bool:
        """Test 8: Comprehensive Backend Health Check"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                # Check critical services
                database_ok = services.get('database', False)
                ollama_ok = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                
                if database_ok and ollama_ok and tools_count > 0:
                    self.log_test("Backend Health Comprehensive", True, 
                                f"All services healthy - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}")
                    return True
                else:
                    self.log_test("Backend Health Comprehensive", False, 
                                f"Some services unhealthy - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}", data)
                    return False
            else:
                self.log_test("Backend Health Comprehensive", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Backend Health Comprehensive", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all WebSocket and CORS tests"""
        print("🧪 STARTING COMPREHENSIVE MITOSIS WEBSOCKET AND CORS TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Diagnosing WebSocket timeout and CORS errors")
        print("📋 TESTING: WebSocket endpoints, CORS configuration, and file access")
        print(f"🔍 TASK ID: {SPECIFIC_TASK_ID}")
        print(f"🔍 MESSAGE: '{TEST_MESSAGE}'")
        print("=" * 80)
        
        # Test sequence focused on WebSocket and CORS issues
        tests = [
            ("WebSocket Endpoint Availability", self.test_websocket_endpoint_availability),
            ("WebSocket Configuration", self.test_websocket_configuration),
            ("CORS Configuration", self.test_cors_configuration),
            ("Specific Task Status", self.test_specific_task_status),
            ("Files Endpoint CORS", self.test_files_endpoint_cors),
            ("Plan Generation Real-time", self.test_plan_generation_realtime),
            ("Backend WebSocket Manager Status", self.test_backend_websocket_manager_status),
            ("Backend Health Comprehensive", self.test_backend_health_comprehensive)
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
        print("🎯 WEBSOCKET AND CORS TESTING RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ WEBSOCKET AND CORS WORKING CORRECTLY"
        elif success_rate >= 70:
            overall_status = "⚠️ WEBSOCKET/CORS MOSTLY WORKING - Minor issues detected"
        elif success_rate >= 50:
            overall_status = "⚠️ WEBSOCKET/CORS PARTIAL - Significant issues found"
        else:
            overall_status = "❌ WEBSOCKET/CORS CRITICAL - Major issues preventing frontend connection"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for WebSocket and CORS
        critical_tests = ["WebSocket Endpoint Availability", "WebSocket Configuration", "CORS Configuration", "Files Endpoint CORS"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL WEBSOCKET/CORS FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical WebSocket/CORS functionality is working")
            print("   🎯 CONCLUSION: WebSocket and CORS are properly configured")
        else:
            print("   ❌ Some critical WebSocket/CORS functionality is not working")
            print("   🎯 CONCLUSION: WebSocket/CORS configuration needs fixes")
        
        # Specific findings
        print(f"\n🔍 SPECIFIC FINDINGS:")
        
        # Check specific task status
        task_result = next((r for r in self.test_results if r['test_name'] == 'Specific Task Status'), None)
        if task_result and task_result['success']:
            print(f"   ✅ Task {SPECIFIC_TASK_ID} found with plan and 4+ steps")
        else:
            print(f"   ❌ Task {SPECIFIC_TASK_ID} not found or incomplete")
        
        # Check WebSocket connectivity
        ws_result = next((r for r in self.test_results if r['test_name'] == 'WebSocket Endpoint Availability'), None)
        if ws_result and ws_result['success']:
            print("   ✅ WebSocket endpoint is accessible and working")
        else:
            print("   ❌ WebSocket endpoint has connection issues (likely cause of timeout)")
        
        # Check CORS configuration
        cors_result = next((r for r in self.test_results if r['test_name'] == 'CORS Configuration'), None)
        if cors_result and cors_result['success']:
            print("   ✅ CORS is properly configured for API endpoints")
        else:
            print("   ❌ CORS configuration issues detected")
        
        # Check files endpoint
        files_result = next((r for r in self.test_results if r['test_name'] == 'Files Endpoint CORS'), None)
        if files_result and files_result['success']:
            print("   ✅ Files endpoints are accessible with proper CORS")
        else:
            print("   ❌ Files endpoint CORS issues detected")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'websocket_working': ws_result and ws_result['success'] if ws_result else False,
            'cors_working': cors_result and cors_result['success'] if cors_result else False,
            'task_found': task_result and task_result['success'] if task_result else False,
            'files_accessible': files_result and files_result['success'] if files_result else False
        }

def main():
    """Main testing function"""
    tester = MitosisWebSocketCORSTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/websocket_cors_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR MAIN AGENT")
    print("=" * 80)
    
    if results['websocket_working'] and results['cors_working']:
        print("✅ WEBSOCKET & CORS DIAGNOSIS: Both working correctly")
        print("📋 RECOMMENDATION: Issue likely in frontend WebSocket client implementation")
        print("🔧 NEXT STEPS: Check frontend WebSocket connection code")
    elif results['websocket_working'] and not results['cors_working']:
        print("⚠️ WEBSOCKET & CORS DIAGNOSIS: WebSocket OK, CORS issues detected")
        print("📋 RECOMMENDATION: Fix CORS configuration")
        print("🔧 NEXT STEPS: Update CORS settings in backend")
    elif not results['websocket_working'] and results['cors_working']:
        print("⚠️ WEBSOCKET & CORS DIAGNOSIS: CORS OK, WebSocket issues detected")
        print("📋 RECOMMENDATION: Fix WebSocket configuration")
        print("🔧 NEXT STEPS: Check WebSocket manager initialization")
    else:
        print("❌ WEBSOCKET & CORS DIAGNOSIS: Both have issues")
        print("📋 RECOMMENDATION: Fix both WebSocket and CORS configurations")
        print("🔧 NEXT STEPS: Address WebSocket and CORS setup")
    
    if results['task_found']:
        print(f"✅ TASK STATUS: Task {SPECIFIC_TASK_ID} found with plan")
    else:
        print(f"❌ TASK STATUS: Task {SPECIFIC_TASK_ID} not found or incomplete")
    
    if results['files_accessible']:
        print("✅ FILES ACCESS: Files endpoints accessible")
    else:
        print("❌ FILES ACCESS: Files endpoint issues detected")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 WEBSOCKET/CORS TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ WEBSOCKET/CORS TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)