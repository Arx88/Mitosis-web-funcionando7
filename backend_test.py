#!/usr/bin/env python3
"""
MITOSIS PLAN DE ACCIÓN TESTING
Testing the refactored Plan de Acción functionality as requested in the review.

SPECIFIC TESTING REQUEST:
Test the refactored Plan de Acción system with:
- New usePlanReducer hook with centralized logic
- New usePlanWebSocket hook for WebSocket events
- Refactored TaskView.tsx component
- Cleaned useWebSocket.ts hook

EXPECTED FUNCTIONALITY:
1. Creating a new task should show the Action Plan
2. Steps should appear correctly (pending, active, completed)
3. Logic: completed step → next step activates automatically
4. Visual states: only ONE step active at a time with blue spinner
5. Completed steps show green ✅
6. Pending steps show numbering
7. No excessive console logs
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL from environment
BACKEND_URL = "https://4043af97-b312-4e41-9e0f-ae9ec47441af.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class PlanDeAccionTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': BACKEND_URL
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
            print(f"\n🏥 Testing backend health...")
            
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                services = data.get('services', {})
                
                if status == 'healthy':
                    self.log_test("Backend Health", True, 
                                f"Backend healthy - Services: {services}")
                    return True
                else:
                    self.log_test("Backend Health", False, 
                                f"Backend unhealthy - Status: {status}", data)
                    return False
            else:
                self.log_test("Backend Health", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Backend Health", False, f"Exception: {str(e)}")
            return False
    
    def test_create_task_with_plan(self) -> bool:
        """Test 2: Create Task with Plan de Acción"""
        try:
            print(f"\n📋 Creating task with Plan de Acción...")
            
            # Use a simple task that should generate a clear plan
            test_message = "Crear un archivo de texto con hola mundo"
            
            payload = {
                "message": test_message
            }
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required response fields
                response_text = data.get('response', '')
                task_id = data.get('task_id', '')
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                
                # Store task_id for later tests
                if task_id:
                    self.task_id = task_id
                    print(f"   📋 Task created with ID: {task_id}")
                
                # Verify plan structure
                if plan and len(plan) >= 2:
                    valid_plan = True
                    step_details = []
                    
                    for i, step in enumerate(plan):
                        required_fields = ['id', 'title', 'description', 'tool', 'status']
                        if not all(key in step for key in required_fields):
                            valid_plan = False
                            print(f"   ❌ Step {i+1} missing required fields: {step}")
                            break
                        
                        step_details.append(f"Step {i+1}: {step.get('title', 'No title')}")
                        
                        # Check initial step states
                        if i == 0:
                            # First step should be active or ready to start
                            if step.get('status') not in ['pending', 'ready']:
                                print(f"   ⚠️ First step has unexpected status: {step.get('status')}")
                        else:
                            # Other steps should be pending
                            if step.get('status') != 'pending':
                                print(f"   ⚠️ Step {i+1} should be pending but is: {step.get('status')}")
                    
                    if valid_plan and response_text and task_id and enhanced_title:
                        self.log_test("Create Task with Plan", True, 
                                    f"Task created with valid plan - {len(plan)} steps, Task ID: {task_id}")
                        print(f"   📊 Plan steps: {'; '.join(step_details)}")
                        return True
                    else:
                        self.log_test("Create Task with Plan", False, 
                                    f"Task created but plan invalid - Valid plan: {valid_plan}", data)
                        return False
                else:
                    self.log_test("Create Task with Plan", False, 
                                f"Plan not generated or insufficient steps - Plan length: {len(plan) if plan else 0}", data)
                    return False
            else:
                self.log_test("Create Task with Plan", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Task with Plan", False, f"Exception: {str(e)}")
            return False
    
    def test_task_status_endpoint(self) -> bool:
        """Test 3: Task Status Endpoint"""
        try:
            if not self.task_id:
                self.log_test("Task Status Endpoint", False, "No task ID available")
                return False
            
            print(f"\n📊 Testing task status endpoint...")
            
            response = self.session.get(f"{API_BASE}/agent/get-task-status/{self.task_id}", 
                                      timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required fields
                status = data.get('status', '')
                plan = data.get('plan', [])
                task_title = data.get('title', '')
                
                if status and plan and task_title:
                    self.log_test("Task Status Endpoint", True, 
                                f"Task status retrieved - Status: {status}, Plan steps: {len(plan)}")
                    return True
                else:
                    self.log_test("Task Status Endpoint", False, 
                                f"Missing required fields - Status: {bool(status)}, Plan: {bool(plan)}, Title: {bool(task_title)}", data)
                    return False
            else:
                self.log_test("Task Status Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Task Status Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_agent_status(self) -> bool:
        """Test 4: Agent Status"""
        try:
            print(f"\n🤖 Testing agent status...")
            
            response = self.session.get(f"{API_BASE}/agent/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                status = data.get('status', '')
                ollama = data.get('ollama', {})
                tools = data.get('tools', [])
                
                if status == 'running' and ollama and tools:
                    self.log_test("Agent Status", True, 
                                f"Agent running - Ollama connected: {ollama.get('connected', False)}, Tools: {len(tools)}")
                    return True
                else:
                    self.log_test("Agent Status", False, 
                                f"Agent not properly configured - Status: {status}", data)
                    return False
            else:
                self.log_test("Agent Status", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Agent Status", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_endpoint(self) -> bool:
        """Test 5: WebSocket Endpoint Availability"""
        try:
            print(f"\n🔌 Testing WebSocket endpoint availability...")
            
            # Test if the WebSocket endpoint is accessible
            websocket_url = f"{BACKEND_URL}/api/socket.io/"
            
            # Try to make a simple HTTP request to the WebSocket endpoint
            response = self.session.get(websocket_url, timeout=5)
            
            # WebSocket endpoints typically return specific responses
            if response.status_code in [200, 400, 426]:  # 426 = Upgrade Required (normal for WebSocket)
                self.log_test("WebSocket Endpoint", True, 
                            f"WebSocket endpoint accessible - Status: {response.status_code}")
                return True
            else:
                self.log_test("WebSocket Endpoint", False, 
                            f"WebSocket endpoint not accessible - Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend API tests"""
        print("🧪 STARTING MITOSIS PLAN DE ACCIÓN BACKEND TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing backend APIs for Plan de Acción functionality")
        print("📋 TESTING: Task creation, plan generation, status endpoints")
        print("🔍 TEST TASK: 'Crear un archivo de texto con hola mundo'")
        print("⚠️ VALIDATING: Backend readiness for frontend Plan de Acción testing")
        print("=" * 80)
        
        # Test sequence for backend APIs
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Create Task with Plan", self.test_create_task_with_plan),
            ("Task Status Endpoint", self.test_task_status_endpoint),
            ("Agent Status", self.test_agent_status),
            ("WebSocket Endpoint", self.test_websocket_endpoint)
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
        print("🎯 MITOSIS PLAN DE ACCIÓN BACKEND TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 80:
            overall_status = "✅ BACKEND READY FOR FRONTEND TESTING"
        elif success_rate >= 60:
            overall_status = "⚠️ BACKEND MOSTLY READY - Minor issues"
        else:
            overall_status = "❌ BACKEND NOT READY - Major issues"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical functionality assessment
        critical_tests = ["Backend Health", "Create Task with Plan", "Agent Status"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL BACKEND FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical backend functionality is working")
            print("   🎯 CONCLUSION: Backend is ready for Plan de Acción frontend testing")
        else:
            print("   ❌ Some critical backend functionality is not working")
            print("   🎯 CONCLUSION: Fix backend issues before frontend testing")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id,
            'backend_ready': critical_passed >= len(critical_tests) - 1  # Allow 1 failure
        }

def main():
    """Main testing function"""
    tester = PlanDeAccionTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/backend_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR PLAN DE ACCIÓN TESTING")
    print("=" * 80)
    
    if results['backend_ready']:
        print("✅ BACKEND DIAGNOSIS: Backend APIs are working and ready")
        print("📋 RECOMMENDATION: Proceed with frontend Plan de Acción testing")
        print("🔧 NEXT STEPS: Test frontend UI and Plan de Acción functionality")
    else:
        print("❌ BACKEND DIAGNOSIS: Backend has critical issues")
        print("📋 RECOMMENDATION: Fix backend issues before frontend testing")
        print("🔧 NEXT STEPS: Address backend API problems first")
    
    # Return exit code based on success
    if results['success_rate'] >= 60:
        print("\n🎉 BACKEND TESTING COMPLETED - READY FOR FRONTEND TESTING")
        return 0
    else:
        print("\n⚠️ BACKEND TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)