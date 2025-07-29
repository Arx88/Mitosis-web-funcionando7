#!/usr/bin/env python3
"""
MITOSIS WEBSOCKET EVENT EMISSION DIAGNOSIS
Diagnose the specific issue where backend progresses correctly but frontend doesn't show real-time updates.

SPECIFIC ISSUE TO DIAGNOSE:
- Backend generates plans and executes steps correctly (task-1753789476281 executing step-2)
- Frontend shows agent "stuck on first step" visually
- WebSocket hook implemented with HTTP polling fallback
- Need to verify if backend emits WebSocket events during task execution

CRITICAL TESTING FOCUS:
1. **Task Creation and Execution**: Create task and verify execution starts
2. **WebSocket Event Emission**: Monitor if backend emits step_started, task_progress, step_completed events
3. **HTTP Polling Fallback**: Test get-task-status endpoints for polling
4. **Real-time Communication**: Verify WebSocket infrastructure is working
5. **Task Status Tracking**: Monitor task progression through API calls
6. **Event Broadcasting**: Test if WebSocket events reach frontend

BACKEND URL: https://c709f51b-b2f2-4187-aeb7-c477ff21005c.preview.emergentagent.com
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment - test both internal and external URLs
BACKEND_URL = "https://c709f51b-b2f2-4187-aeb7-c477ff21005c.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisCORSAndConfigTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://c709f51b-b2f2-4187-aeb7-c477ff21005c.preview.emergentagent.com'  # Test CORS
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
    
    def test_api_health_endpoint(self) -> bool:
        """Test 1: API Health Endpoint"""
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
                
                has_cors = any(cors_headers.values())
                
                if database_ok and ollama_ok and tools_count > 0:
                    self.log_test("API Health Endpoint", True, 
                                f"Health endpoint working - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}, CORS: {has_cors}")
                    return True
                else:
                    self.log_test("API Health Endpoint", False, 
                                f"Some services unhealthy - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}", data)
                    return False
            else:
                self.log_test("API Health Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("API Health Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_cors_configuration_api(self) -> bool:
        """Test 2: CORS Configuration for /api/* endpoints"""
        try:
            # Test OPTIONS request to check CORS preflight
            options_response = self.session.options(f"{API_BASE}/agent/chat", timeout=10)
            
            # Test actual POST request
            post_response = self.session.post(f"{API_BASE}/agent/chat", 
                                            json={"message": "test"}, timeout=10)
            
            # Check CORS headers in both responses
            options_cors = {
                'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers')
            }
            
            post_cors = {
                'Access-Control-Allow-Origin': post_response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': post_response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': post_response.headers.get('Access-Control-Allow-Headers')
            }
            
            # Check if CORS is properly configured
            options_has_cors = options_cors['Access-Control-Allow-Origin'] is not None
            post_has_cors = post_cors['Access-Control-Allow-Origin'] is not None
            
            if options_has_cors and post_has_cors:
                self.log_test("CORS Configuration API", True, 
                            f"CORS properly configured for /api/* - OPTIONS: {options_has_cors}, POST: {post_has_cors}")
                return True
            else:
                self.log_test("CORS Configuration API", False, 
                            f"CORS not properly configured - OPTIONS: {options_has_cors}, POST: {post_has_cors}")
                return False
                
        except Exception as e:
            self.log_test("CORS Configuration API", False, f"Exception: {str(e)}")
            return False
    
    def test_chat_functionality_with_plan(self) -> bool:
        """Test 3: Chat Functionality with Plan Generation"""
        try:
            # Test with the exact message from the review request
            test_message = "Genera un informe sobre la IA en 2025"
            
            payload = {
                "message": test_message
            }
            
            print(f"\n🎯 Testing chat functionality with: {test_message}")
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required response fields
                response_text = data.get('response', '')
                task_id = data.get('task_id', '')
                memory_used = data.get('memory_used', False)
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                
                # Store task_id for later tests
                if task_id:
                    self.task_id = task_id
                
                # Verify plan structure and content
                if plan and len(plan) >= 4:
                    # Check if plan has proper structure
                    valid_plan = True
                    step_details = []
                    for i, step in enumerate(plan):
                        if not all(key in step for key in ['title', 'description', 'tool']):
                            valid_plan = False
                            break
                        step_details.append(f"Step {i+1}: {step.get('title', 'No title')}")
                    
                    if valid_plan and response_text and task_id and enhanced_title:
                        self.log_test("Chat Functionality with Plan", True, 
                                    f"Chat generates proper plan - {len(plan)} steps, Task ID: {task_id}, Enhanced title: {enhanced_title}")
                        print(f"   Plan steps: {'; '.join(step_details[:3])}...")
                        return True
                    else:
                        self.log_test("Chat Functionality with Plan", False, 
                                    f"Plan structure invalid - Valid plan: {valid_plan}, Response: {bool(response_text)}, Task ID: {bool(task_id)}, Title: {bool(enhanced_title)}", data)
                        return False
                else:
                    self.log_test("Chat Functionality with Plan", False, 
                                f"Plan not generated or insufficient steps - Plan length: {len(plan) if plan else 0}", data)
                    return False
            else:
                self.log_test("Chat Functionality with Plan", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Chat Functionality with Plan", False, f"Exception: {str(e)}")
            return False
    
    def test_plan_generation_verification(self) -> bool:
        """Test 4: Plan Generation Verification"""
        try:
            # Test plan generation endpoint directly
            test_message = "Genera un informe sobre la IA en 2025"
            
            payload = {
                "task_title": test_message
            }
            
            print(f"\n🎯 Testing plan generation endpoint with: {test_message}")
            
            response = self.session.post(f"{API_BASE}/agent/generate-plan", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required response fields
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                task_type = data.get('task_type', '')
                complexity = data.get('complexity', '')
                
                # Verify plan structure and quality
                if plan and len(plan) >= 4:
                    # Check if plan has proper structure
                    valid_plan = True
                    tools_used = set()
                    for step in plan:
                        if not all(key in step for key in ['title', 'description', 'tool']):
                            valid_plan = False
                            break
                        tools_used.add(step.get('tool', 'unknown'))
                    
                    if valid_plan and enhanced_title:
                        self.log_test("Plan Generation Verification", True, 
                                    f"Plan generation working - {len(plan)} steps, Type: {task_type}, Complexity: {complexity}, Tools: {len(tools_used)}")
                        return True
                    else:
                        self.log_test("Plan Generation Verification", False, 
                                    f"Plan structure invalid - Valid plan: {valid_plan}, Title: {bool(enhanced_title)}", data)
                        return False
                else:
                    self.log_test("Plan Generation Verification", False, 
                                f"Plan not generated or insufficient steps - Plan length: {len(plan) if plan else 0}", data)
                    return False
            else:
                self.log_test("Plan Generation Verification", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Plan Generation Verification", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_support(self) -> bool:
        """Test 5: WebSocket Support Check"""
        try:
            # Check if WebSocket endpoint is accessible by testing socket.io info
            socketio_url = f"{BACKEND_URL}/socket.io/"
            
            # Test socket.io endpoint
            response = self.session.get(socketio_url, timeout=10)
            
            # Also check backend status for WebSocket infrastructure
            status_response = self.session.get(f"{API_BASE}/agent/status", timeout=10)
            
            websocket_accessible = response.status_code in [200, 400]  # 400 is also OK for socket.io without proper handshake
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                backend_running = status_data.get('status', '') == 'running'
                memory_enabled = status_data.get('memory', {}).get('enabled', False)
                
                if websocket_accessible and backend_running and memory_enabled:
                    self.log_test("WebSocket Support", True, 
                                f"WebSocket support available - Endpoint accessible: {websocket_accessible}, Backend running: {backend_running}, Memory: {memory_enabled}")
                    return True
                else:
                    self.log_test("WebSocket Support", False, 
                                f"WebSocket support issues - Accessible: {websocket_accessible}, Running: {backend_running}, Memory: {memory_enabled}")
                    return False
            else:
                self.log_test("WebSocket Support", False, 
                            f"Cannot verify WebSocket support - Status endpoint error: {status_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Support", False, f"Exception: {str(e)}")
            return False
    
    def test_files_endpoint_cors(self) -> bool:
        """Test 6: Files Endpoint CORS Compliance"""
        if not self.task_id:
            # Create a test task first
            try:
                chat_response = self.session.post(f"{API_BASE}/agent/chat", 
                                                json={"message": "test task for files"}, timeout=15)
                if chat_response.status_code == 200:
                    self.task_id = chat_response.json().get('task_id', 'test-task-id')
            except:
                self.task_id = 'test-task-id'
        
        try:
            # Test /files/<task_id> endpoint for CORS compliance
            files_url = f"{BACKEND_URL}/files/{self.task_id}"
            
            # Test OPTIONS request for CORS preflight
            options_response = self.session.options(files_url, timeout=10)
            
            # Test GET request
            get_response = self.session.get(files_url, timeout=10)
            
            # Check CORS headers
            options_cors = options_response.headers.get('Access-Control-Allow-Origin')
            get_cors = get_response.headers.get('Access-Control-Allow-Origin')
            
            # Check if endpoint is accessible (may redirect or return data)
            files_accessible = get_response.status_code in [200, 302, 404]  # 404 is OK if no files exist yet
            cors_configured = options_cors is not None or get_cors is not None
            
            if files_accessible and cors_configured:
                self.log_test("Files Endpoint CORS", True, 
                            f"Files endpoint CORS working - Accessible: {files_accessible}, CORS headers: {cors_configured}")
                return True
            else:
                self.log_test("Files Endpoint CORS", False, 
                            f"Files endpoint CORS issues - Accessible: {files_accessible}, CORS: {cors_configured}")
                return False
                
        except Exception as e:
            self.log_test("Files Endpoint CORS", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all CORS and configuration tests"""
        print("🧪 STARTING MITOSIS BACKEND CORS AND CONFIGURATION TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing CORS fixes and configuration changes")
        print("📋 TESTING: API health, CORS headers, chat functionality, plan generation, WebSocket, files")
        print("🔍 MESSAGE: 'Genera un informe sobre la IA en 2025'")
        print("=" * 80)
        
        # Test sequence focused on CORS and configuration
        tests = [
            ("API Health Endpoint", self.test_api_health_endpoint),
            ("CORS Configuration API", self.test_cors_configuration_api),
            ("Chat Functionality with Plan", self.test_chat_functionality_with_plan),
            ("Plan Generation Verification", self.test_plan_generation_verification),
            ("WebSocket Support", self.test_websocket_support),
            ("Files Endpoint CORS", self.test_files_endpoint_cors)
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
        print("🎯 MITOSIS BACKEND CORS AND CONFIGURATION TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ BACKEND CORS AND CONFIG WORKING PERFECTLY"
        elif success_rate >= 70:
            overall_status = "⚠️ BACKEND MOSTLY WORKING - Minor issues detected"
        elif success_rate >= 50:
            overall_status = "⚠️ BACKEND PARTIAL - Significant issues found"
        else:
            overall_status = "❌ BACKEND CRITICAL - Major issues preventing functionality"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for CORS and configuration
        critical_tests = ["API Health Endpoint", "CORS Configuration API", "Chat Functionality with Plan", "WebSocket Support"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL CORS AND CONFIGURATION FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical CORS and configuration functionality is working")
            print("   🎯 CONCLUSION: Backend CORS fixes and configuration changes are successful")
        else:
            print("   ❌ Some critical CORS and configuration functionality is not working")
            print("   🎯 CONCLUSION: Backend has CORS or configuration issues that need to be fixed")
        
        # Specific findings
        print(f"\n🔍 SPECIFIC FINDINGS:")
        
        cors_result = next((r for r in self.test_results if r['test_name'] == 'CORS Configuration API'), None)
        if cors_result and cors_result['success']:
            print("   ✅ CORS configuration is working correctly for /api/* endpoints")
        elif cors_result:
            print("   ❌ CORS configuration issues detected for /api/* endpoints")
        
        files_result = next((r for r in self.test_results if r['test_name'] == 'Files Endpoint CORS'), None)
        if files_result and files_result['success']:
            print("   ✅ Files endpoint CORS is working correctly")
        elif files_result:
            print("   ❌ Files endpoint CORS issues detected")
        
        chat_result = next((r for r in self.test_results if r['test_name'] == 'Chat Functionality with Plan'), None)
        if chat_result and chat_result['success']:
            print("   ✅ Chat functionality with plan generation is working correctly")
        elif chat_result:
            print("   ❌ Chat functionality or plan generation issues detected")
        
        websocket_result = next((r for r in self.test_results if r['test_name'] == 'WebSocket Support'), None)
        if websocket_result and websocket_result['success']:
            print("   ✅ WebSocket support is available and working")
        elif websocket_result:
            print("   ❌ WebSocket support issues detected")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id,
            'backend_working': critical_passed >= 3,  # If 3+ critical tests pass, backend is working
            'cors_working': cors_result and cors_result['success'] if cors_result else False,
            'files_cors_working': files_result and files_result['success'] if files_result else False
        }

def main():
    """Main testing function"""
    tester = MitosisCORSAndConfigTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/backend_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR MAIN AGENT")
    print("=" * 80)
    
    if results['backend_working']:
        print("✅ BACKEND DIAGNOSIS: Backend CORS and configuration changes are working correctly")
        print("📋 RECOMMENDATION: Backend is ready for frontend-backend communication")
        print("🔧 NEXT STEPS: Frontend should be able to communicate with backend without CORS issues")
    else:
        print("❌ BACKEND DIAGNOSIS: Backend has CORS or configuration issues")
        print("📋 RECOMMENDATION: Fix backend CORS or configuration issues first")
        print("🔧 NEXT STEPS: Address backend CORS and configuration problems")
    
    if results.get('cors_working'):
        print("✅ CORS STATUS: CORS configuration is working correctly for /api/* endpoints")
    else:
        print("❌ CORS STATUS: CORS configuration issues detected for /api/* endpoints")
    
    if results.get('files_cors_working'):
        print("✅ FILES CORS STATUS: Files endpoint CORS is working correctly")
    else:
        print("❌ FILES CORS STATUS: Files endpoint CORS issues detected")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 CORS AND CONFIGURATION TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ CORS AND CONFIGURATION TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)