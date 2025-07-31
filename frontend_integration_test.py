#!/usr/bin/env python3
"""
MITOSIS FRONTEND INTEGRATION TESTING
Testing specific issues mentioned in the review request:

CURRENT ISSUES TO TEST:
- Tasks are created but show generic title "Tarea 1" instead of enhanced titles from the backend
- No "PLAN DE ACCIÓN" appears in the frontend - the plan is not being generated
- WebSocket shows OFFLINE status consistently
- Frontend logs show "No initial plan found" and "Setting new plan with 0 steps"

BACKEND URLs TO TEST:
- Backend URL: https://4bb53208-212c-440f-9581-7b02cf7ebdd3.preview.emergentagent.com
- Main chat endpoint: /api/agent/chat (POST)

TEST REQUIREMENTS:
1. Chat Endpoint Test: Send POST to /api/agent/chat with message "Crear una presentación sobre sostenibilidad"
2. WebSocket Status Check: Test WebSocket endpoints
3. Plan Generation Flow: Verify complete flow from chat request to plan generation
4. Enhanced Title Generation: Test if generate_task_title_with_llm function is working

EXPECTED RESPONSE FORMAT: The frontend expects responses with fields like:
- enhanced_title: string
- plan: array of step objects
- task_id: string
- response: string
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL from environment
BACKEND_URL = "https://4bb53208-212c-440f-9581-7b02cf7ebdd3.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class FrontendIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': BACKEND_URL
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
    
    def test_chat_endpoint_specific_message(self) -> bool:
        """Test 1: Chat Endpoint with Specific Message from Review Request"""
        try:
            print(f"\n📋 Testing chat endpoint with specific message: 'Crear una presentación sobre sostenibilidad'")
            
            # Use the exact message from the review request
            test_message = "Crear una presentación sobre sostenibilidad"
            
            payload = {
                "message": test_message
            }
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for all expected fields from frontend
                enhanced_title = data.get('enhanced_title', '')
                plan = data.get('plan', [])
                task_id = data.get('task_id', '')
                response_text = data.get('response', '')
                
                print(f"   📊 Enhanced Title: '{enhanced_title}'")
                print(f"   📋 Plan Steps: {len(plan) if plan else 0}")
                print(f"   🆔 Task ID: {task_id}")
                print(f"   💬 Response Length: {len(response_text) if response_text else 0}")
                
                # Detailed plan analysis
                if plan and len(plan) > 0:
                    print(f"   📝 Plan Details:")
                    for i, step in enumerate(plan[:3]):  # Show first 3 steps
                        step_title = step.get('title', 'No title')
                        step_tool = step.get('tool', 'No tool')
                        print(f"      Step {i+1}: {step_title} (Tool: {step_tool})")
                
                # Check if response matches frontend expectations
                has_enhanced_title = bool(enhanced_title and enhanced_title != "Tarea 1")
                has_plan = bool(plan and len(plan) > 0)
                has_task_id = bool(task_id)
                has_response = bool(response_text)
                
                if has_enhanced_title and has_plan and has_task_id and has_response:
                    self.log_test("Chat Endpoint - Specific Message", True, 
                                f"All expected fields present - Title: '{enhanced_title}', Plan: {len(plan)} steps, ID: {task_id}")
                    return True
                else:
                    missing_fields = []
                    if not has_enhanced_title:
                        missing_fields.append("enhanced_title")
                    if not has_plan:
                        missing_fields.append("plan")
                    if not has_task_id:
                        missing_fields.append("task_id")
                    if not has_response:
                        missing_fields.append("response")
                    
                    self.log_test("Chat Endpoint - Specific Message", False, 
                                f"Missing expected fields: {', '.join(missing_fields)}", data)
                    return False
            else:
                self.log_test("Chat Endpoint - Specific Message", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Chat Endpoint - Specific Message", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_connection_status(self) -> bool:
        """Test 2: WebSocket Connection Status Check"""
        try:
            print(f"\n🔌 Testing WebSocket connection status...")
            
            # Test multiple WebSocket endpoints
            websocket_endpoints = [
                "/api/socket.io/",
                "/socket.io/",
                "/api/socket.io/?transport=polling",
                "/api/socket.io/?transport=websocket"
            ]
            
            websocket_results = []
            
            for endpoint in websocket_endpoints:
                try:
                    url = f"{BACKEND_URL}{endpoint}"
                    response = self.session.get(url, timeout=10)
                    
                    # WebSocket endpoints can return various status codes
                    if response.status_code in [200, 400, 426]:  # 426 = Upgrade Required
                        websocket_results.append(f"{endpoint}: ✅ {response.status_code}")
                        
                        # Try to get more info from response
                        if response.status_code == 200:
                            try:
                                # Check if it's a socket.io response
                                content = response.text[:100]
                                if 'socket.io' in content.lower() or 'polling' in content.lower():
                                    websocket_results.append(f"  - Content indicates Socket.IO server")
                            except:
                                pass
                    else:
                        websocket_results.append(f"{endpoint}: ❌ {response.status_code}")
                        
                except Exception as e:
                    websocket_results.append(f"{endpoint}: ❌ Exception: {str(e)[:50]}")
            
            # Check if any WebSocket endpoint is working
            working_endpoints = [result for result in websocket_results if "✅" in result]
            
            if working_endpoints:
                self.log_test("WebSocket Connection Status", True, 
                            f"WebSocket endpoints accessible - {len(working_endpoints)} working")
                for result in websocket_results:
                    print(f"   {result}")
                return True
            else:
                self.log_test("WebSocket Connection Status", False, 
                            f"No WebSocket endpoints accessible")
                for result in websocket_results:
                    print(f"   {result}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Connection Status", False, f"Exception: {str(e)}")
            return False
    
    def test_plan_generation_flow(self) -> bool:
        """Test 3: Complete Plan Generation Flow"""
        try:
            print(f"\n🎯 Testing complete plan generation flow...")
            
            # Test with a task that should definitely generate a plan
            test_message = "Crear un análisis completo del mercado de inteligencia artificial en 2025"
            
            payload = {
                "message": test_message
            }
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Analyze the complete flow
                enhanced_title = data.get('enhanced_title', '')
                plan = data.get('plan', [])
                task_type = data.get('task_type', '')
                complexity = data.get('complexity', '')
                task_id = data.get('task_id', '')
                memory_used = data.get('memory_used', False)
                
                print(f"   📊 Enhanced Title: '{enhanced_title}'")
                print(f"   📋 Plan Steps: {len(plan) if plan else 0}")
                print(f"   🏷️ Task Type: {task_type}")
                print(f"   ⚡ Complexity: {complexity}")
                print(f"   🧠 Memory Used: {memory_used}")
                
                # Detailed plan validation
                if plan and len(plan) > 0:
                    valid_steps = 0
                    for i, step in enumerate(plan):
                        required_fields = ['id', 'title', 'description', 'tool', 'status']
                        has_all_fields = all(field in step for field in required_fields)
                        
                        if has_all_fields:
                            valid_steps += 1
                            print(f"   ✅ Step {i+1}: {step.get('title', 'No title')} ({step.get('tool', 'No tool')})")
                        else:
                            missing = [field for field in required_fields if field not in step]
                            print(f"   ❌ Step {i+1}: Missing fields: {missing}")
                    
                    # Check if plan generation is complete and valid
                    plan_complete = (
                        enhanced_title and enhanced_title != "Tarea 1" and
                        len(plan) >= 3 and  # At least 3 steps for a complete plan
                        valid_steps == len(plan) and  # All steps are valid
                        task_type and complexity
                    )
                    
                    if plan_complete:
                        self.log_test("Plan Generation Flow", True, 
                                    f"Complete plan generated - Title: '{enhanced_title}', {len(plan)} valid steps, Type: {task_type}")
                        return True
                    else:
                        issues = []
                        if not enhanced_title or enhanced_title == "Tarea 1":
                            issues.append("No enhanced title")
                        if len(plan) < 3:
                            issues.append(f"Only {len(plan)} steps")
                        if valid_steps != len(plan):
                            issues.append(f"Only {valid_steps}/{len(plan)} valid steps")
                        if not task_type:
                            issues.append("No task type")
                        if not complexity:
                            issues.append("No complexity")
                        
                        self.log_test("Plan Generation Flow", False, 
                                    f"Incomplete plan generation - Issues: {', '.join(issues)}", data)
                        return False
                else:
                    self.log_test("Plan Generation Flow", False, 
                                f"No plan generated - Only basic response returned", data)
                    return False
            else:
                self.log_test("Plan Generation Flow", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Plan Generation Flow", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_title_generation(self) -> bool:
        """Test 4: Enhanced Title Generation Function"""
        try:
            print(f"\n🏷️ Testing enhanced title generation...")
            
            # Test multiple messages to verify title generation consistency
            test_messages = [
                "Crear una presentación sobre sostenibilidad",
                "Analizar el mercado de criptomonedas en 2025",
                "Desarrollar una estrategia de marketing digital",
                "Investigar tendencias de inteligencia artificial"
            ]
            
            title_results = []
            
            for i, message in enumerate(test_messages):
                try:
                    payload = {"message": message}
                    response = self.session.post(f"{API_BASE}/agent/chat", 
                                               json=payload, timeout=20)
                    
                    if response.status_code == 200:
                        data = response.json()
                        enhanced_title = data.get('enhanced_title', '')
                        
                        # Check if title is enhanced (not generic)
                        is_enhanced = (
                            enhanced_title and 
                            enhanced_title != "Tarea 1" and 
                            enhanced_title != f"Tarea {i+1}" and
                            len(enhanced_title) > 10 and
                            enhanced_title.lower() != message.lower()
                        )
                        
                        if is_enhanced:
                            title_results.append(f"✅ '{message[:30]}...' → '{enhanced_title}'")
                        else:
                            title_results.append(f"❌ '{message[:30]}...' → '{enhanced_title}' (Generic/Invalid)")
                    else:
                        title_results.append(f"❌ '{message[:30]}...' → HTTP {response.status_code}")
                        
                    time.sleep(1)  # Brief pause between requests
                    
                except Exception as e:
                    title_results.append(f"❌ '{message[:30]}...' → Exception: {str(e)[:30]}")
            
            # Analyze results
            successful_titles = [result for result in title_results if "✅" in result]
            success_rate = len(successful_titles) / len(test_messages) * 100
            
            print(f"   📊 Title Generation Results:")
            for result in title_results:
                print(f"      {result}")
            
            if success_rate >= 75:  # At least 75% success rate
                self.log_test("Enhanced Title Generation", True, 
                            f"Title generation working - {len(successful_titles)}/{len(test_messages)} successful ({success_rate:.1f}%)")
                return True
            else:
                self.log_test("Enhanced Title Generation", False, 
                            f"Title generation inconsistent - {len(successful_titles)}/{len(test_messages)} successful ({success_rate:.1f}%)")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Title Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_frontend_expected_response_format(self) -> bool:
        """Test 5: Frontend Expected Response Format Validation"""
        try:
            print(f"\n📋 Testing frontend expected response format...")
            
            test_message = "Crear una presentación sobre sostenibilidad"
            payload = {"message": test_message}
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check all expected fields for frontend
                expected_fields = {
                    'enhanced_title': str,
                    'plan': list,
                    'task_id': str,
                    'response': str,
                    'memory_used': bool,
                    'task_type': str,
                    'complexity': str
                }
                
                field_results = []
                all_fields_valid = True
                
                for field, expected_type in expected_fields.items():
                    value = data.get(field)
                    
                    if value is not None:
                        if isinstance(value, expected_type):
                            if field == 'plan' and len(value) > 0:
                                # Validate plan structure
                                first_step = value[0]
                                step_fields = ['id', 'title', 'description', 'tool', 'status']
                                missing_step_fields = [f for f in step_fields if f not in first_step]
                                
                                if not missing_step_fields:
                                    field_results.append(f"✅ {field}: {expected_type.__name__} with {len(value)} valid steps")
                                else:
                                    field_results.append(f"⚠️ {field}: {expected_type.__name__} with {len(value)} steps, but missing step fields: {missing_step_fields}")
                                    all_fields_valid = False
                            elif field == 'enhanced_title' and value == "Tarea 1":
                                field_results.append(f"⚠️ {field}: Generic title '{value}' (should be enhanced)")
                                all_fields_valid = False
                            else:
                                field_results.append(f"✅ {field}: {expected_type.__name__} = '{str(value)[:50]}{'...' if len(str(value)) > 50 else ''}'")
                        else:
                            field_results.append(f"❌ {field}: Expected {expected_type.__name__}, got {type(value).__name__}")
                            all_fields_valid = False
                    else:
                        field_results.append(f"❌ {field}: Missing")
                        all_fields_valid = False
                
                print(f"   📊 Response Format Validation:")
                for result in field_results:
                    print(f"      {result}")
                
                if all_fields_valid:
                    self.log_test("Frontend Expected Response Format", True, 
                                f"All expected fields present and valid")
                    return True
                else:
                    invalid_fields = [result for result in field_results if "❌" in result or "⚠️" in result]
                    self.log_test("Frontend Expected Response Format", False, 
                                f"Some fields invalid - {len(invalid_fields)} issues found", data)
                    return False
            else:
                self.log_test("Frontend Expected Response Format", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Frontend Expected Response Format", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all frontend integration tests"""
        print("🧪 STARTING MITOSIS FRONTEND INTEGRATION TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing specific issues mentioned in review request")
        print("📋 ISSUES: Generic titles, missing plans, WebSocket OFFLINE, no plan generation")
        print("🔍 TESTING: Chat endpoint, WebSocket status, plan generation, enhanced titles")
        print("⚠️ EXPECTED: Enhanced titles, structured plans, working WebSocket, proper response format")
        print("=" * 80)
        
        # Test sequence for frontend integration issues
        tests = [
            ("Chat Endpoint - Specific Message", self.test_chat_endpoint_specific_message),
            ("WebSocket Connection Status", self.test_websocket_connection_status),
            ("Plan Generation Flow", self.test_plan_generation_flow),
            ("Enhanced Title Generation", self.test_enhanced_title_generation),
            ("Frontend Expected Response Format", self.test_frontend_expected_response_format)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(2)  # Pause between tests to avoid rate limiting
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 80)
        print("🎯 MITOSIS FRONTEND INTEGRATION TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 80:
            overall_status = "✅ BACKEND READY FOR FRONTEND INTEGRATION"
        elif success_rate >= 60:
            overall_status = "⚠️ BACKEND MOSTLY READY - Some integration issues remain"
        else:
            overall_status = "❌ BACKEND HAS CRITICAL INTEGRATION ISSUES"
        
        print(f"   Overall Status: {overall_status}")
        
        # Specific assessment for reported issues
        critical_tests = ["Chat Endpoint - Specific Message", "Plan Generation Flow", "Enhanced Title Generation"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL TESTS FOR REPORTED ISSUES:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical functionality is working")
            print("   🎯 CONCLUSION: Backend is generating enhanced titles and plans correctly")
            print("   📋 RECOMMENDATION: Issue may be in frontend integration or WebSocket communication")
        else:
            print("   ❌ Some critical functionality is not working")
            print("   🎯 CONCLUSION: Backend has issues with plan generation or title enhancement")
            print("   📋 RECOMMENDATION: Fix backend issues before investigating frontend")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'backend_ready': critical_passed >= len(critical_tests) - 1,
            'issues_resolved': critical_passed == len(critical_tests)
        }

def main():
    """Main testing function"""
    tester = FrontendIntegrationTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/frontend_integration_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment for the specific issues mentioned
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR REPORTED FRONTEND INTEGRATION ISSUES")
    print("=" * 80)
    
    if results['issues_resolved']:
        print("✅ BACKEND DIAGNOSIS: Backend is working correctly")
        print("✅ ENHANCED TITLES: Backend generates proper enhanced titles (not 'Tarea 1')")
        print("✅ PLAN GENERATION: Backend generates structured plans with steps")
        print("✅ RESPONSE FORMAT: Backend returns all expected fields for frontend")
        print("📋 CONCLUSION: The issues are likely in frontend integration or WebSocket communication")
        print("🔧 RECOMMENDATION: Investigate frontend WebSocket connection and plan display logic")
    else:
        print("❌ BACKEND DIAGNOSIS: Backend has issues with core functionality")
        failed_tests = [result for result in results['test_results'] if not result['success']]
        for failed in failed_tests:
            print(f"   ❌ {failed['test_name']}: {failed['details']}")
        print("📋 CONCLUSION: Backend needs fixes before frontend integration can work")
        print("🔧 RECOMMENDATION: Fix backend issues first, then test frontend integration")
    
    # Specific recommendations for each reported issue
    print(f"\n🔍 SPECIFIC ISSUE ANALYSIS:")
    
    # Check enhanced title issue
    title_test = next((r for r in results['test_results'] if 'Enhanced Title' in r['test_name']), None)
    if title_test and title_test['success']:
        print("   ✅ Enhanced Titles: Backend generates proper titles - frontend display issue")
    else:
        print("   ❌ Enhanced Titles: Backend not generating enhanced titles properly")
    
    # Check plan generation issue
    plan_test = next((r for r in results['test_results'] if 'Plan Generation' in r['test_name']), None)
    if plan_test and plan_test['success']:
        print("   ✅ Plan Generation: Backend generates structured plans - frontend not receiving/displaying")
    else:
        print("   ❌ Plan Generation: Backend not generating proper plan structures")
    
    # Check WebSocket issue
    websocket_test = next((r for r in results['test_results'] if 'WebSocket' in r['test_name']), None)
    if websocket_test and websocket_test['success']:
        print("   ✅ WebSocket Endpoints: Backend WebSocket accessible - frontend connection issue")
    else:
        print("   ❌ WebSocket Endpoints: Backend WebSocket not accessible")
    
    # Return exit code based on success
    if results['success_rate'] >= 60:
        print("\n🎉 FRONTEND INTEGRATION TESTING COMPLETED")
        return 0
    else:
        print("\n⚠️ FRONTEND INTEGRATION TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)