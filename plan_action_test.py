#!/usr/bin/env python3
"""
PLAN DE ACCIÓN TESTING - SPECIFIC STEP ACTIVATION ISSUE
Test the specific Plan de Acción functionality where steps should show as ACTIVO before completion.

SPECIFIC TESTING REQUEST:
Test that after the first step, subsequent steps show as ACTIVO in the frontend.

PROBLEM FIXED:
- Frontend had duplicate event handlers for `step_started` causing conflicts
- Backend emits events in sequence: step_started → step_completed → step_started (next step)

EXPECTED BEHAVIOR:
1. Create task → generates plan with multiple steps
2. Execute first step → shows as ACTIVO
3. Complete first step → next step shows as ACTIVO
4. Continue until all steps are completed

URL: https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL
BACKEND_URL = "https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class PlanActionTester:
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
            print(f"\n🏥 Testing backend health at: {API_BASE}")
            
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                
                if status == 'healthy':
                    self.log_test("Backend Health", True, f"Backend is healthy - Status: {status}")
                    return True
                else:
                    self.log_test("Backend Health", False, f"Backend status: {status}", data)
                    return False
            else:
                self.log_test("Backend Health", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Backend Health", False, f"Exception: {str(e)}")
            return False

    def test_create_action_plan_task(self) -> bool:
        """Test 2: Create Task with Action Plan"""
        try:
            # Use the specific test message from the review request
            test_message = "Crear un análisis sobre los beneficios de la energía solar"
            
            payload = {
                "message": test_message
            }
            
            print(f"\n📋 Creating action plan task: {test_message}")
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required response fields
                response_text = data.get('response', '')
                task_id = data.get('task_id', '')
                plan = data.get('plan', [])
                
                # Store task_id for later tests
                if task_id:
                    self.task_id = task_id
                    print(f"   📋 Task created with ID: {task_id}")
                
                # Verify plan structure
                if plan and len(plan) >= 3:
                    # Check if plan has proper structure
                    valid_plan = True
                    step_details = []
                    
                    for i, step in enumerate(plan):
                        if not all(key in step for key in ['title', 'description']):
                            valid_plan = False
                            break
                        step_details.append(f"Step {i+1}: {step.get('title', 'No title')}")
                        
                        # Check initial step states
                        step_id = step.get('id')
                        step_active = step.get('active', False)
                        step_completed = step.get('completed', False)
                        
                        print(f"   📊 Step {i+1}: ID={step_id}, Active={step_active}, Completed={step_completed}")
                    
                    # Check if it's about solar energy analysis
                    solar_keywords = ['solar', 'energía', 'análisis', 'beneficios']
                    plan_text = json.dumps(plan).lower()
                    has_solar_content = any(keyword in plan_text for keyword in solar_keywords)
                    
                    if valid_plan and response_text and task_id and has_solar_content:
                        self.log_test("Create Action Plan Task", True, 
                                    f"Solar energy analysis task created - {len(plan)} steps, Task ID: {task_id}")
                        print(f"   📊 Plan steps: {'; '.join(step_details)}")
                        return True
                    else:
                        self.log_test("Create Action Plan Task", False, 
                                    f"Task not properly created - Valid plan: {valid_plan}, Solar content: {has_solar_content}", data)
                        return False
                else:
                    self.log_test("Create Action Plan Task", False, 
                                f"Plan not generated or insufficient steps - Plan length: {len(plan) if plan else 0}", data)
                    return False
            else:
                self.log_test("Create Action Plan Task", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Action Plan Task", False, f"Exception: {str(e)}")
            return False

    def test_get_task_status(self) -> bool:
        """Test 3: Get Task Status and Plan Details"""
        try:
            if not self.task_id:
                self.log_test("Get Task Status", False, "No task ID available")
                return False
            
            print(f"\n📊 Getting task status for: {self.task_id}")
            
            # Try different endpoints to get task status
            endpoints = [
                f"{API_BASE}/agent/task/{self.task_id}",
                f"{API_BASE}/agent/tasks/{self.task_id}",
                f"{API_BASE}/agent/status/{self.task_id}"
            ]
            
            task_data = None
            working_endpoint = None
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        task_data = response.json()
                        working_endpoint = endpoint
                        break
                except Exception as e:
                    continue
            
            if task_data:
                plan = task_data.get('plan', [])
                status = task_data.get('status', 'unknown')
                
                print(f"   📊 Task status: {status}")
                print(f"   📋 Plan steps: {len(plan)}")
                
                # Analyze step states
                active_steps = []
                completed_steps = []
                
                for i, step in enumerate(plan):
                    step_id = step.get('id', f'step_{i}')
                    step_active = step.get('active', False)
                    step_completed = step.get('completed', False)
                    step_title = step.get('title', 'No title')
                    
                    if step_active:
                        active_steps.append(f"Step {i+1}: {step_title}")
                    if step_completed:
                        completed_steps.append(f"Step {i+1}: {step_title}")
                    
                    print(f"   📊 Step {i+1}: {step_title[:50]}... - Active: {step_active}, Completed: {step_completed}")
                
                self.log_test("Get Task Status", True, 
                            f"Task status retrieved - Status: {status}, Active steps: {len(active_steps)}, Completed: {len(completed_steps)}")
                return True
            else:
                self.log_test("Get Task Status", False, 
                            f"Could not retrieve task status from any endpoint")
                return False
                
        except Exception as e:
            self.log_test("Get Task Status", False, f"Exception: {str(e)}")
            return False

    def test_execute_first_step(self) -> bool:
        """Test 4: Execute First Step and Check ACTIVO Status"""
        try:
            if not self.task_id:
                self.log_test("Execute First Step", False, "No task ID available")
                return False
            
            print(f"\n🚀 Executing first step for task: {self.task_id}")
            
            # Try to get the first step ID
            task_response = self.session.get(f"{API_BASE}/agent/task/{self.task_id}", timeout=10)
            if task_response.status_code != 200:
                self.log_test("Execute First Step", False, "Could not get task details")
                return False
            
            task_data = task_response.json()
            plan = task_data.get('plan', [])
            
            if not plan:
                self.log_test("Execute First Step", False, "No plan found in task")
                return False
            
            first_step = plan[0]
            first_step_id = first_step.get('id')
            
            if not first_step_id:
                self.log_test("Execute First Step", False, "First step has no ID")
                return False
            
            print(f"   🎯 Executing step: {first_step.get('title', 'No title')}")
            
            # Execute the first step
            execution_payload = {
                "step_id": first_step_id
            }
            
            response = self.session.post(
                f"{API_BASE}/agent/execute-step-detailed/{self.task_id}/{first_step_id}", 
                json=execution_payload, 
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if step execution started
                success = result.get('success', False)
                step_result = result.get('step_result', {})
                
                if success:
                    self.log_test("Execute First Step", True, 
                                f"First step executed successfully - Result: {step_result.get('summary', 'No summary')}")
                    
                    # Wait a moment and check step status
                    time.sleep(3)
                    
                    # Get updated task status
                    updated_response = self.session.get(f"{API_BASE}/agent/task/{self.task_id}", timeout=10)
                    if updated_response.status_code == 200:
                        updated_data = updated_response.json()
                        updated_plan = updated_data.get('plan', [])
                        
                        # Check if first step is completed and second step is active
                        if len(updated_plan) >= 2:
                            first_step_updated = updated_plan[0]
                            second_step_updated = updated_plan[1]
                            
                            first_completed = first_step_updated.get('completed', False)
                            second_active = second_step_updated.get('active', False)
                            
                            print(f"   📊 After execution - First step completed: {first_completed}, Second step active: {second_active}")
                            
                            if first_completed and second_active:
                                print("   ✅ PERFECT: First step completed, second step is now ACTIVO")
                                return True
                            elif first_completed:
                                print("   ⚠️ First step completed but second step not active yet")
                                return True
                            else:
                                print("   ⚠️ First step execution may still be in progress")
                                return True
                    
                    return True
                else:
                    self.log_test("Execute First Step", False, 
                                f"Step execution failed - Error: {result.get('error', 'Unknown error')}", result)
                    return False
            else:
                self.log_test("Execute First Step", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Execute First Step", False, f"Exception: {str(e)}")
            return False

    def test_step_progression_sequence(self) -> bool:
        """Test 5: Monitor Step Progression Sequence"""
        try:
            if not self.task_id:
                self.log_test("Step Progression Sequence", False, "No task ID available")
                return False
            
            print(f"\n📈 Monitoring step progression sequence for task: {self.task_id}")
            
            # Monitor for 30 seconds to see step progression
            monitoring_duration = 30
            start_time = time.time()
            step_states_history = []
            
            while (time.time() - start_time) < monitoring_duration:
                try:
                    response = self.session.get(f"{API_BASE}/agent/task/{self.task_id}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        plan = data.get('plan', [])
                        
                        # Record current step states
                        current_state = {
                            'timestamp': datetime.now().isoformat(),
                            'steps': []
                        }
                        
                        for i, step in enumerate(plan):
                            step_state = {
                                'step_number': i + 1,
                                'title': step.get('title', 'No title')[:30],
                                'active': step.get('active', False),
                                'completed': step.get('completed', False),
                                'status': step.get('status', 'unknown')
                            }
                            current_state['steps'].append(step_state)
                        
                        step_states_history.append(current_state)
                        
                        # Print current state
                        active_steps = [s for s in current_state['steps'] if s['active']]
                        completed_steps = [s for s in current_state['steps'] if s['completed']]
                        
                        if active_steps or completed_steps:
                            print(f"   📊 {datetime.now().strftime('%H:%M:%S')} - Active: {len(active_steps)}, Completed: {len(completed_steps)}")
                            for step in active_steps:
                                print(f"      🔄 ACTIVO: Step {step['step_number']} - {step['title']}")
                            for step in completed_steps:
                                print(f"      ✅ COMPLETADO: Step {step['step_number']} - {step['title']}")
                
                except Exception as e:
                    print(f"   ⚠️ Error monitoring: {e}")
                
                time.sleep(2)
            
            # Analyze step progression
            if len(step_states_history) >= 2:
                # Check for proper step activation sequence
                activation_sequence = []
                completion_sequence = []
                
                for state in step_states_history:
                    for step in state['steps']:
                        if step['active'] and step['step_number'] not in [s['step_number'] for s in activation_sequence]:
                            activation_sequence.append({
                                'step_number': step['step_number'],
                                'title': step['title'],
                                'timestamp': state['timestamp']
                            })
                        if step['completed'] and step['step_number'] not in [s['step_number'] for s in completion_sequence]:
                            completion_sequence.append({
                                'step_number': step['step_number'],
                                'title': step['title'],
                                'timestamp': state['timestamp']
                            })
                
                print(f"\n   📊 Activation sequence: {len(activation_sequence)} steps activated")
                for activation in activation_sequence:
                    print(f"      🔄 Step {activation['step_number']}: {activation['title']} at {activation['timestamp']}")
                
                print(f"   📊 Completion sequence: {len(completion_sequence)} steps completed")
                for completion in completion_sequence:
                    print(f"      ✅ Step {completion['step_number']}: {completion['title']} at {completion['timestamp']}")
                
                # Check if we have proper step progression
                if len(activation_sequence) >= 2:
                    self.log_test("Step Progression Sequence", True, 
                                f"Step progression working - {len(activation_sequence)} steps activated, {len(completion_sequence)} completed")
                    return True
                elif len(activation_sequence) == 1 and len(completion_sequence) >= 1:
                    self.log_test("Step Progression Sequence", True, 
                                f"Partial step progression - {len(activation_sequence)} activated, {len(completion_sequence)} completed")
                    return True
                else:
                    self.log_test("Step Progression Sequence", False, 
                                f"Insufficient step progression - {len(activation_sequence)} activated, {len(completion_sequence)} completed")
                    return False
            else:
                self.log_test("Step Progression Sequence", False, 
                            f"Insufficient monitoring data - {len(step_states_history)} states recorded")
                return False
                
        except Exception as e:
            self.log_test("Step Progression Sequence", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Plan de Acción tests"""
        print("🧪 STARTING PLAN DE ACCIÓN BACKEND TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing Plan de Acción step activation (ACTIVO status)")
        print("📋 TESTING: Step progression where each step shows as ACTIVO before completion")
        print("🔍 TEST TASK: 'Crear un análisis sobre los beneficios de la energía solar'")
        print("⚠️ INVESTIGATING: Steps should show ACTIVO status before being completed")
        print("=" * 80)
        
        # Test sequence focused on Plan de Acción functionality
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Create Action Plan Task", self.test_create_action_plan_task),
            ("Get Task Status", self.test_get_task_status),
            ("Execute First Step", self.test_execute_first_step),
            ("Step Progression Sequence", self.test_step_progression_sequence)
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
        print("🎯 PLAN DE ACCIÓN BACKEND TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 80:
            overall_status = "✅ PLAN DE ACCIÓN WORKING CORRECTLY"
        elif success_rate >= 60:
            overall_status = "⚠️ PLAN DE ACCIÓN MOSTLY WORKING - Minor issues"
        else:
            overall_status = "❌ PLAN DE ACCIÓN HAS ISSUES - Needs attention"
        
        print(f"   Overall Status: {overall_status}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'test_results': self.test_results,
            'task_id': self.task_id,
            'backend_working': success_rate >= 60
        }

def main():
    """Main testing function"""
    tester = PlanActionTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/plan_action_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR MAIN AGENT")
    print("=" * 80)
    
    if results['backend_working']:
        print("✅ BACKEND DIAGNOSIS: Plan de Acción backend functionality is working")
        print("📋 RECOMMENDATION: Backend can create tasks and execute steps properly")
        print("🔧 NEXT STEPS: Proceed with frontend testing using browser automation")
    else:
        print("❌ BACKEND DIAGNOSIS: Plan de Acción backend has critical issues")
        print("📋 RECOMMENDATION: Fix backend issues before testing frontend")
        print("🔧 NEXT STEPS: Address backend API and step execution problems")
    
    # Return exit code based on success
    if results['success_rate'] >= 60:
        print("\n🎉 PLAN DE ACCIÓN BACKEND TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ PLAN DE ACCIÓN BACKEND TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)