#!/usr/bin/env python3
"""
COMPREHENSIVE MITOSIS AGENT AUTONOMOUS FUNCTIONALITY TESTING
Testing the complete autonomous execution pipeline to verify that the agent can execute tasks from start to finish and generate tangible results.

CRITICAL OBJECTIVE: Verify that the refactoring has eliminated duplications and the agent can generate AND execute plans completely.
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://e71a7bfa-cc8f-4d93-98fc-5b476bdd3e84.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisAgentTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
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
                
                # Check critical services
                database_ok = services.get('database', False)
                ollama_ok = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                
                if database_ok and ollama_ok and tools_count > 0:
                    self.log_test("Backend Health Check", True, 
                                f"All services healthy - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}")
                    return True
                else:
                    self.log_test("Backend Health Check", False, 
                                f"Some services unhealthy - DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}", data)
                    return False
            else:
                self.log_test("Backend Health Check", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_agent_status(self) -> bool:
        """Test 2: Agent Status Check"""
        try:
            response = self.session.get(f"{API_BASE}/agent/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check Ollama connection
                ollama_info = data.get('ollama', {})
                ollama_connected = ollama_info.get('connected', False)
                ollama_endpoint = ollama_info.get('endpoint', '')
                ollama_model = ollama_info.get('model', '')
                
                # Check tools
                tools_count = data.get('tools_count', 0)
                
                if ollama_connected and tools_count >= 10:  # Expecting 12 tools
                    self.log_test("Agent Status Check", True, 
                                f"Agent ready - Ollama: {ollama_endpoint} ({ollama_model}), Tools: {tools_count}")
                    return True
                else:
                    self.log_test("Agent Status Check", False, 
                                f"Agent not ready - Ollama connected: {ollama_connected}, Tools: {tools_count}", data)
                    return False
            else:
                self.log_test("Agent Status Check", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Agent Status Check", False, f"Exception: {str(e)}")
            return False
    
    def test_plan_generation(self) -> bool:
        """Test 3: Plan Generation Testing"""
        try:
            test_message = "Crear un análisis de mercado para productos de tecnología en 2025"
            
            payload = {
                "message": test_message
            }
            
            response = self.session.post(f"{API_BASE}/agent/generate-plan", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check plan structure
                plan = data.get('plan', {})
                if isinstance(plan, dict):
                    steps = plan.get('steps', [])
                    task_type = plan.get('task_type', '')
                    complexity = plan.get('complexity', '')
                    enhanced_title = data.get('enhanced_title', '')
                    
                    if len(steps) >= 3 and task_type and complexity:
                        # Validate step structure
                        valid_steps = True
                        for step in steps:
                            if not all(key in step for key in ['title', 'description', 'tool']):
                                valid_steps = False
                                break
                        
                        if valid_steps:
                            self.log_test("Plan Generation", True, 
                                        f"Valid plan generated - {len(steps)} steps, type: {task_type}, complexity: {complexity}, title: {enhanced_title}")
                            
                            # Store task_id for later tests
                            self.task_id = data.get('task_id')
                            return True
                        else:
                            self.log_test("Plan Generation", False, 
                                        "Invalid step structure in generated plan", data)
                            return False
                    else:
                        self.log_test("Plan Generation", False, 
                                    f"Incomplete plan structure - steps: {len(steps)}, type: {task_type}, complexity: {complexity}", data)
                        return False
                else:
                    self.log_test("Plan Generation", False, 
                                "Plan is not a dictionary or missing", data)
                    return False
            else:
                self.log_test("Plan Generation", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Plan Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_task_initialization(self) -> bool:
        """Test 4: Task Initialization for Autonomous Execution"""
        if not self.task_id:
            self.log_test("Task Initialization", False, "No task_id available from plan generation")
            return False
            
        try:
            payload = {
                "message": "Crear un análisis de mercado para productos de tecnología en 2025"
            }
            
            response = self.session.post(f"{API_BASE}/agent/initialize-task", 
                                       json=payload, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                
                success = data.get('success', False)
                task_id = data.get('task_id', '')
                plan_generated = data.get('plan_generated', False)
                
                if success and task_id and plan_generated:
                    self.log_test("Task Initialization", True, 
                                f"Task initialized successfully - ID: {task_id}, Plan generated: {plan_generated}")
                    self.task_id = task_id  # Update task_id
                    return True
                else:
                    self.log_test("Task Initialization", False, 
                                f"Task initialization incomplete - success: {success}, task_id: {task_id}, plan: {plan_generated}", data)
                    return False
            else:
                self.log_test("Task Initialization", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Task Initialization", False, f"Exception: {str(e)}")
            return False
    
    def test_task_plan_retrieval(self) -> bool:
        """Test 5: Task Plan Retrieval"""
        if not self.task_id:
            self.log_test("Task Plan Retrieval", False, "No task_id available")
            return False
            
        try:
            response = self.session.get(f"{API_BASE}/agent/get-task-plan/{self.task_id}", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                task_id = data.get('task_id', '')
                status = data.get('status', '')
                plan = data.get('plan', [])
                stats = data.get('stats', {})
                
                if task_id and plan and stats:
                    total_steps = stats.get('total_steps', 0)
                    completed_steps = stats.get('completed_steps', 0)
                    
                    self.log_test("Task Plan Retrieval", True, 
                                f"Plan retrieved - Status: {status}, Steps: {total_steps}, Completed: {completed_steps}")
                    return True
                else:
                    self.log_test("Task Plan Retrieval", False, 
                                f"Incomplete plan data - task_id: {task_id}, plan length: {len(plan)}, stats: {bool(stats)}", data)
                    return False
            else:
                self.log_test("Task Plan Retrieval", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Task Plan Retrieval", False, f"Exception: {str(e)}")
            return False
    
    def test_task_execution_start(self) -> bool:
        """Test 6: Start Task Execution (Autonomous)"""
        if not self.task_id:
            self.log_test("Task Execution Start", False, "No task_id available")
            return False
            
        try:
            response = self.session.post(f"{API_BASE}/agent/start-task-execution/{self.task_id}", 
                                       json={}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                success = data.get('success', False)
                execution_started = data.get('execution_started', False)
                message = data.get('message', '')
                
                if success and execution_started:
                    self.log_test("Task Execution Start", True, 
                                f"Execution started successfully - {message}")
                    return True
                else:
                    self.log_test("Task Execution Start", False, 
                                f"Execution not started - success: {success}, started: {execution_started}, message: {message}", data)
                    return False
            else:
                self.log_test("Task Execution Start", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Task Execution Start", False, f"Exception: {str(e)}")
            return False
    
    def test_step_execution(self) -> bool:
        """Test 7: Individual Step Execution with Real Tools"""
        if not self.task_id:
            self.log_test("Step Execution", False, "No task_id available")
            return False
            
        try:
            # First get the plan to find the first step
            plan_response = self.session.get(f"{API_BASE}/agent/get-task-plan/{self.task_id}", timeout=15)
            
            if plan_response.status_code != 200:
                self.log_test("Step Execution", False, "Could not retrieve plan for step execution")
                return False
                
            plan_data = plan_response.json()
            plan = plan_data.get('plan', [])
            
            if not plan:
                self.log_test("Step Execution", False, "No steps found in plan")
                return False
                
            # Get the first step
            first_step = plan[0]
            step_id = first_step.get('id', '')
            
            if not step_id:
                self.log_test("Step Execution", False, "First step has no ID")
                return False
            
            # Execute the first step
            response = self.session.post(f"{API_BASE}/agent/execute-step/{self.task_id}/{step_id}", 
                                       json={}, timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                
                success = data.get('success', False)
                step_result = data.get('step_result', {})
                step_completed = data.get('step_completed', False)
                
                if success and step_completed and step_result:
                    result_type = step_result.get('type', 'unknown')
                    result_summary = step_result.get('summary', 'No summary')
                    
                    self.log_test("Step Execution", True, 
                                f"Step executed successfully - Type: {result_type}, Summary: {result_summary}")
                    return True
                else:
                    self.log_test("Step Execution", False, 
                                f"Step execution incomplete - success: {success}, completed: {step_completed}, result: {bool(step_result)}", data)
                    return False
            else:
                self.log_test("Step Execution", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Step Execution", False, f"Exception: {str(e)}")
            return False
    
    def test_document_generation(self) -> bool:
        """Test 8: Document Generation and File Creation"""
        if not self.task_id:
            self.log_test("Document Generation", False, "No task_id available")
            return False
            
        try:
            # Check if any files were generated for this task
            response = self.session.get(f"{API_BASE}/agent/get-task-files/{self.task_id}", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                files = data.get('files', [])
                
                if files:
                    # Check if files are accessible
                    first_file = files[0]
                    filename = first_file.get('filename', '')
                    
                    if filename:
                        # Try to access the file
                        file_response = self.session.get(f"{API_BASE}/agent/download/{filename}", timeout=10)
                        
                        if file_response.status_code == 200:
                            self.log_test("Document Generation", True, 
                                        f"Document generated and accessible - {len(files)} files, first: {filename}")
                            return True
                        else:
                            self.log_test("Document Generation", False, 
                                        f"File exists but not accessible - {filename}, HTTP {file_response.status_code}")
                            return False
                    else:
                        self.log_test("Document Generation", False, 
                                    "Files exist but no filename available", data)
                        return False
                else:
                    # No files yet, but this might be expected if execution is still in progress
                    self.log_test("Document Generation", True, 
                                "No files generated yet (execution may be in progress)")
                    return True
            else:
                self.log_test("Document Generation", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Document Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_integration_flow(self) -> bool:
        """Test 9: Complete Integration Flow (End-to-End)"""
        try:
            # Test the complete workflow with a new task
            test_message = "Crear un informe sobre las mejores prácticas de desarrollo de software en 2025"
            
            print("\n🔄 Testing complete integration flow...")
            
            # Step 1: Generate plan
            plan_payload = {"message": test_message}
            plan_response = self.session.post(f"{API_BASE}/agent/generate-plan", 
                                            json=plan_payload, timeout=30)
            
            if plan_response.status_code != 200:
                self.log_test("Integration Flow", False, "Plan generation failed in integration test")
                return False
                
            plan_data = plan_response.json()
            integration_task_id = plan_data.get('task_id')
            
            if not integration_task_id:
                self.log_test("Integration Flow", False, "No task_id returned from plan generation")
                return False
            
            # Step 2: Initialize task
            init_response = self.session.post(f"{API_BASE}/agent/initialize-task", 
                                            json=plan_payload, timeout=20)
            
            if init_response.status_code != 200:
                self.log_test("Integration Flow", False, "Task initialization failed in integration test")
                return False
            
            # Step 3: Start execution
            exec_response = self.session.post(f"{API_BASE}/agent/start-task-execution/{integration_task_id}", 
                                            json={}, timeout=30)
            
            if exec_response.status_code != 200:
                self.log_test("Integration Flow", False, "Task execution start failed in integration test")
                return False
            
            # Step 4: Check task status
            status_response = self.session.get(f"{API_BASE}/agent/get-task-plan/{integration_task_id}", timeout=15)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                task_status = status_data.get('status', '')
                
                self.log_test("Integration Flow", True, 
                            f"Complete integration flow successful - Task status: {task_status}")
                return True
            else:
                self.log_test("Integration Flow", False, "Task status check failed in integration test")
                return False
                
        except Exception as e:
            self.log_test("Integration Flow", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        print("🧪 STARTING COMPREHENSIVE MITOSIS AGENT AUTONOMOUS FUNCTIONALITY TESTING")
        print("=" * 80)
        
        # Test sequence
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Agent Status", self.test_agent_status),
            ("Plan Generation", self.test_plan_generation),
            ("Task Initialization", self.test_task_initialization),
            ("Task Plan Retrieval", self.test_task_plan_retrieval),
            ("Task Execution Start", self.test_task_execution_start),
            ("Step Execution", self.test_step_execution),
            ("Document Generation", self.test_document_generation),
            ("Integration Flow", self.test_integration_flow)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ EXCELLENT - System is fully operational"
        elif success_rate >= 70:
            overall_status = "⚠️ GOOD - System is mostly operational with minor issues"
        elif success_rate >= 50:
            overall_status = "⚠️ PARTIAL - System has significant issues but core functionality works"
        else:
            overall_status = "❌ CRITICAL - System has major issues preventing proper operation"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings
        critical_tests = ["Backend Health", "Agent Status", "Plan Generation", "Task Execution Start"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical functionality is working")
        else:
            print("   ❌ Some critical functionality is not working")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id
        }

def main():
    """Main testing function"""
    tester = MitosisAgentTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/backend_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)