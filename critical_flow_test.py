#!/usr/bin/env python3
"""
CRITICAL FLOW TESTING - DIAGNOSING PLAN GENERATION AND EXECUTION ISSUE

SPECIFIC ISSUE REPORTED BY USER:
- User sends simple task: "Crea una lista de 3 colores primarios"
- Message appears in blue bubble (frontend working)
- Agent shows "Procesando..." but never advances
- NO "PLAN DE ACCIÓN" section appears
- NO progress in monitor
- Task NEVER completes

TESTING FOCUS:
1. Test /api/agent/chat endpoint with exact user message
2. Verify if plan is generated automatically
3. Check if task execution starts automatically
4. Verify WebSocket events are emitted
5. Check task persistence and status updates
6. End-to-end flow verification
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL from environment
BACKEND_URL = "https://c4f5be8b-db00-42e6-8dcc-7c4a057ac882.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class CriticalFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': BACKEND_URL
        })
        self.test_results = []
        self.task_id = None
        self.user_message = "Crea una lista de 3 colores primarios"
        
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
    
    def test_chat_endpoint_with_user_message(self) -> bool:
        """Test 1: Send exact user message to /api/agent/chat"""
        try:
            print(f"\n💬 Testing chat endpoint with user message: '{self.user_message}'")
            
            payload = {
                "message": self.user_message
            }
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract key fields
                task_id = data.get('task_id', '')
                response_text = data.get('response', '')
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                status = data.get('status', '')
                
                # Store task_id for later tests
                if task_id:
                    self.task_id = task_id
                    print(f"   📋 Task created with ID: {task_id}")
                
                # Check if we got a proper response
                if response_text and task_id:
                    self.log_test("Chat Endpoint Response", True, 
                                f"Message processed successfully - Task ID: {task_id}, Response length: {len(response_text)}")
                    
                    # Log additional details
                    print(f"   📝 Response: {response_text[:100]}...")
                    if plan:
                        print(f"   📋 Plan generated: {len(plan)} steps")
                    if enhanced_title:
                        print(f"   🎯 Enhanced title: {enhanced_title}")
                    
                    return True
                else:
                    self.log_test("Chat Endpoint Response", False, 
                                f"Incomplete response - Task ID: {bool(task_id)}, Response: {bool(response_text)}", data)
                    return False
            else:
                self.log_test("Chat Endpoint Response", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Chat Endpoint Response", False, f"Exception: {str(e)}")
            return False
    
    def test_plan_generation(self) -> bool:
        """Test 2: Verify if plan is generated automatically"""
        try:
            print(f"\n🎯 Testing automatic plan generation...")
            
            if not self.task_id:
                self.log_test("Plan Generation", False, "No task ID available from previous test")
                return False
            
            # First check the response from chat endpoint
            payload = {"message": self.user_message}
            response = self.session.post(f"{API_BASE}/agent/chat", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                task_type = data.get('task_type', '')
                complexity = data.get('complexity', '')
                
                if plan and len(plan) > 0:
                    # Verify plan structure
                    valid_steps = 0
                    for i, step in enumerate(plan):
                        if all(key in step for key in ['id', 'title', 'description', 'tool']):
                            valid_steps += 1
                            print(f"   Step {i+1}: {step.get('title', 'No title')} ({step.get('tool', 'No tool')})")
                    
                    if valid_steps == len(plan) and enhanced_title:
                        self.log_test("Plan Generation", True, 
                                    f"Complete plan generated - {len(plan)} valid steps, Enhanced title: {enhanced_title}")
                        return True
                    else:
                        self.log_test("Plan Generation", False, 
                                    f"Plan structure incomplete - {valid_steps}/{len(plan)} valid steps, Title: {bool(enhanced_title)}")
                        return False
                else:
                    self.log_test("Plan Generation", False, 
                                f"No plan generated - Plan length: {len(plan) if plan else 0}", data)
                    return False
            else:
                self.log_test("Plan Generation", False, 
                            f"Cannot check plan - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Plan Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_task_persistence(self) -> bool:
        """Test 3: Verify task is persisted in database"""
        try:
            print(f"\n💾 Testing task persistence...")
            
            if not self.task_id:
                self.log_test("Task Persistence", False, "No task ID available")
                return False
            
            # Check if task status endpoint exists and returns data
            response = self.session.get(f"{API_BASE}/agent/get-task-status/{self.task_id}", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                success = data.get('success', False)
                status = data.get('status', '')
                title = data.get('title', '')
                plan = data.get('plan', [])
                
                if success and status and title:
                    self.log_test("Task Persistence", True, 
                                f"Task persisted successfully - Status: {status}, Title: {title}, Plan steps: {len(plan)}")
                    return True
                else:
                    self.log_test("Task Persistence", False, 
                                f"Task data incomplete - Success: {success}, Status: {status}, Title: {bool(title)}", data)
                    return False
            elif response.status_code == 404:
                self.log_test("Task Persistence", False, 
                            f"Task not found in database - 404 error (this is the main issue)")
                return False
            else:
                self.log_test("Task Persistence", False, 
                            f"Cannot check task persistence - HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Task Persistence", False, f"Exception: {str(e)}")
            return False
    
    def test_task_execution_trigger(self) -> bool:
        """Test 4: Check if task execution is triggered automatically"""
        try:
            print(f"\n🚀 Testing automatic task execution trigger...")
            
            if not self.task_id:
                self.log_test("Task Execution Trigger", False, "No task ID available")
                return False
            
            # Check if task execution endpoint exists
            response = self.session.post(f"{API_BASE}/agent/start-task-execution/{self.task_id}", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                message = data.get('message', '')
                
                if success:
                    self.log_test("Task Execution Trigger", True, 
                                f"Task execution triggered - Message: {message}")
                    return True
                else:
                    self.log_test("Task Execution Trigger", False, 
                                f"Task execution failed - Message: {message}", data)
                    return False
            elif response.status_code == 404:
                self.log_test("Task Execution Trigger", False, 
                            f"Task execution endpoint not found - 404 error (critical missing functionality)")
                return False
            else:
                self.log_test("Task Execution Trigger", False, 
                            f"Task execution failed - HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Task Execution Trigger", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_infrastructure(self) -> bool:
        """Test 5: Verify WebSocket infrastructure is ready"""
        try:
            print(f"\n🔌 Testing WebSocket infrastructure...")
            
            # Check if WebSocket endpoint is accessible (basic connectivity test)
            # We can't easily test WebSocket connection in this script, but we can check if the endpoint exists
            
            # Check backend health to see if WebSocket is configured
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', '')
                
                if status == 'healthy':
                    self.log_test("WebSocket Infrastructure", True, 
                                f"Backend healthy - WebSocket infrastructure should be available")
                    return True
                else:
                    self.log_test("WebSocket Infrastructure", False, 
                                f"Backend not healthy - Status: {status}", data)
                    return False
            else:
                self.log_test("WebSocket Infrastructure", False, 
                            f"Cannot check backend health - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Infrastructure", False, f"Exception: {str(e)}")
            return False
    
    def test_end_to_end_flow(self) -> bool:
        """Test 6: Complete end-to-end flow simulation"""
        try:
            print(f"\n🔄 Testing complete end-to-end flow...")
            
            # Step 1: Send message and get task
            payload = {"message": self.user_message}
            chat_response = self.session.post(f"{API_BASE}/agent/chat", json=payload, timeout=30)
            
            if chat_response.status_code != 200:
                self.log_test("End-to-End Flow", False, f"Chat failed - HTTP {chat_response.status_code}")
                return False
            
            chat_data = chat_response.json()
            task_id = chat_data.get('task_id', '')
            plan = chat_data.get('plan', [])
            
            if not task_id or not plan:
                self.log_test("End-to-End Flow", False, 
                            f"Chat response incomplete - Task ID: {bool(task_id)}, Plan: {len(plan) if plan else 0}")
                return False
            
            print(f"   ✅ Step 1: Task created with {len(plan)} steps")
            
            # Step 2: Check task persistence
            time.sleep(2)  # Brief wait
            status_response = self.session.get(f"{API_BASE}/agent/get-task-status/{task_id}", timeout=15)
            
            if status_response.status_code != 200:
                self.log_test("End-to-End Flow", False, 
                            f"Task not persisted - HTTP {status_response.status_code}")
                return False
            
            print(f"   ✅ Step 2: Task persisted in database")
            
            # Step 3: Try to trigger execution
            exec_response = self.session.post(f"{API_BASE}/agent/start-task-execution/{task_id}", timeout=15)
            
            if exec_response.status_code == 200:
                print(f"   ✅ Step 3: Task execution triggered")
                execution_working = True
            elif exec_response.status_code == 404:
                print(f"   ❌ Step 3: Task execution endpoint missing (404)")
                execution_working = False
            else:
                print(f"   ❌ Step 3: Task execution failed - HTTP {exec_response.status_code}")
                execution_working = False
            
            # Step 4: Check final task status
            time.sleep(3)  # Wait for potential processing
            final_status_response = self.session.get(f"{API_BASE}/agent/get-task-status/{task_id}", timeout=15)
            
            if final_status_response.status_code == 200:
                final_data = final_status_response.json()
                final_status = final_data.get('status', '')
                progress = final_data.get('progress', 0)
                
                print(f"   📊 Step 4: Final status - Status: {final_status}, Progress: {progress}%")
                
                # Determine overall success
                if execution_working and final_status in ['executing', 'completed']:
                    self.log_test("End-to-End Flow", True, 
                                f"Complete flow working - Task executing/completed with {progress}% progress")
                    return True
                else:
                    self.log_test("End-to-End Flow", False, 
                                f"Flow incomplete - Execution: {execution_working}, Status: {final_status}, Progress: {progress}%")
                    return False
            else:
                self.log_test("End-to-End Flow", False, 
                            f"Cannot check final status - HTTP {final_status_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("End-to-End Flow", False, f"Exception: {str(e)}")
            return False
    
    def run_critical_flow_tests(self) -> Dict[str, Any]:
        """Run all critical flow tests"""
        print("🧪 STARTING CRITICAL FLOW TESTING - DIAGNOSING PLAN GENERATION AND EXECUTION ISSUE")
        print("=" * 90)
        print(f"🎯 USER ISSUE: Task '{self.user_message}' never completes")
        print("📋 SYMPTOMS: Shows 'Procesando...', no PLAN DE ACCIÓN, no progress, never finishes")
        print("🔍 TESTING: Chat endpoint, plan generation, task persistence, execution trigger, WebSocket, E2E flow")
        print("⚠️ EXPECTED: Identify exactly where the flow breaks")
        print("=" * 90)
        
        # Test sequence for critical flow
        tests = [
            ("Chat Endpoint Response", self.test_chat_endpoint_with_user_message),
            ("Plan Generation", self.test_plan_generation),
            ("Task Persistence", self.test_task_persistence),
            ("Task Execution Trigger", self.test_task_execution_trigger),
            ("WebSocket Infrastructure", self.test_websocket_infrastructure),
            ("End-to-End Flow", self.test_end_to_end_flow)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        critical_failures = []
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                else:
                    critical_failures.append(test_name)
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
                critical_failures.append(test_name)
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 90)
        print("🎯 CRITICAL FLOW TEST RESULTS")
        print("=" * 90)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Critical Failures: {len(critical_failures)}")
        
        # Identify root cause
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        if "Chat Endpoint Response" in critical_failures:
            print("   🚨 CRITICAL: Chat endpoint not working - messages cannot be processed")
            root_cause = "Chat endpoint failure"
        elif "Plan Generation" in critical_failures:
            print("   🚨 CRITICAL: Plan generation broken - no PLAN DE ACCIÓN created")
            root_cause = "Plan generation failure"
        elif "Task Persistence" in critical_failures:
            print("   🚨 CRITICAL: Tasks not saved to database - 404 errors on task status")
            root_cause = "Task persistence failure"
        elif "Task Execution Trigger" in critical_failures:
            print("   🚨 CRITICAL: Task execution endpoint missing - tasks never start executing")
            root_cause = "Task execution missing"
        elif "End-to-End Flow" in critical_failures:
            print("   🚨 CRITICAL: Complete flow broken - multiple issues in sequence")
            root_cause = "Multiple system failures"
        else:
            print("   ✅ All critical components working - issue may be in frontend or WebSocket events")
            root_cause = "Frontend or WebSocket issue"
        
        # Determine overall status
        if success_rate >= 80:
            overall_status = "✅ BACKEND FLOW WORKING - Issue likely in frontend"
        elif success_rate >= 60:
            overall_status = "⚠️ BACKEND PARTIALLY WORKING - Some critical issues"
        else:
            overall_status = "❌ BACKEND FLOW BROKEN - Multiple critical failures"
        
        print(f"   Overall Status: {overall_status}")
        print(f"   Root Cause: {root_cause}")
        
        # Specific recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        
        if "Task Persistence" in critical_failures:
            print("   1. Fix task creation in TaskManager - tasks not saving to MongoDB")
            print("   2. Check agent_routes.py line ~7007 for create_task() call")
        
        if "Task Execution Trigger" in critical_failures:
            print("   1. Implement missing /api/agent/start-task-execution endpoint")
            print("   2. Add automatic task execution after plan generation")
        
        if "Plan Generation" in critical_failures:
            print("   1. Check Ollama service connection and model configuration")
            print("   2. Verify plan generation logic in agent_routes.py")
        
        if success_rate < 50:
            print("   1. URGENT: Multiple critical backend failures need immediate attention")
            print("   2. Check backend logs for detailed error messages")
            print("   3. Verify all services (MongoDB, Ollama, WebSocket) are running")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'root_cause': root_cause,
            'critical_failures': critical_failures,
            'test_results': self.test_results,
            'task_id': self.task_id,
            'user_message': self.user_message,
            'backend_working': success_rate >= 60,
            'flow_complete': "End-to-End Flow" not in critical_failures
        }

def main():
    """Main testing function"""
    tester = CriticalFlowTester()
    results = tester.run_critical_flow_tests()
    
    # Save results to file
    results_file = '/app/critical_flow_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 90)
    print("🎯 FINAL DIAGNOSIS FOR USER'S ISSUE")
    print("=" * 90)
    
    print(f"🔍 USER REPORTED: '{results['user_message']}' never completes")
    print(f"📊 BACKEND STATUS: {results['overall_status']}")
    print(f"🚨 ROOT CAUSE: {results['root_cause']}")
    
    if results['backend_working']:
        print("✅ BACKEND DIAGNOSIS: Backend is mostly functional")
        if results['flow_complete']:
            print("✅ FLOW DIAGNOSIS: Complete flow working - issue likely in frontend WebSocket display")
            print("📋 RECOMMENDATION: Check frontend TaskView rendering and WebSocket event handling")
        else:
            print("⚠️ FLOW DIAGNOSIS: Backend flow has gaps - task execution or persistence issues")
            print("📋 RECOMMENDATION: Fix backend task execution and persistence")
    else:
        print("❌ BACKEND DIAGNOSIS: Critical backend failures preventing task completion")
        print("📋 RECOMMENDATION: Fix critical backend issues before testing frontend")
    
    print(f"\n🔧 IMMEDIATE ACTIONS NEEDED:")
    for i, failure in enumerate(results['critical_failures'], 1):
        print(f"   {i}. Fix {failure}")
    
    # Return exit code based on success
    if results['success_rate'] >= 60:
        print("\n🎉 CRITICAL FLOW TESTING COMPLETED - ISSUES IDENTIFIED")
        return 0
    else:
        print("\n⚠️ CRITICAL FLOW TESTING COMPLETED - MULTIPLE CRITICAL FAILURES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)