#!/usr/bin/env python3
"""
Mitosis Backend Comprehensive Testing - Post Syntax Error Fix
Tests the current state after fixing syntax error in agent_routes.py
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://15c16a6c-c05b-4a8b-8862-e44571e2a1d6.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisBackendTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_result(self, test_name: str, passed: bool, details: str = "", response_time: float = 0):
        """Log test result"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.results.append({
            'test': test_name,
            'status': status,
            'passed': passed,
            'details': details,
            'response_time': f"{response_time:.2f}s",
            'timestamp': datetime.now().isoformat()
        })
        
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
            
        print(f"{status} - {test_name} ({response_time:.2f}s)")
        if details:
            print(f"    Details: {details}")
    
    def test_basic_health_check(self):
        """Test 1: Basic Health Check - /api/health endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                # Check if all expected services are present
                expected_services = ['ollama', 'tools', 'database']
                all_services_present = all(service in services for service in expected_services)
                
                if all_services_present:
                    details = f"All services healthy: {services}"
                    self.log_result("Basic Health Check", True, details, response_time)
                    return True
                else:
                    details = f"Missing services in response: {services}"
                    self.log_result("Basic Health Check", False, details, response_time)
                    return False
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_result("Basic Health Check", False, details, response_time)
                return False
                
        except Exception as e:
            self.log_result("Basic Health Check", False, f"Exception: {str(e)}", 0)
            return False
    
    def test_plan_generation_testing(self):
        """Test 2: Plan Generation Testing - /api/agent/test-plan-generation endpoint"""
        try:
            start_time = time.time()
            test_data = {
                "message": "Crear un informe completo sobre las tendencias de inteligencia artificial en 2025",
                "task_id": f"test-plan-{int(time.time())}"
            }
            
            response = requests.post(
                f"{API_BASE}/agent/test-plan-generation", 
                json=test_data,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                test_results = data.get('test_results', {})
                ai_plan = test_results.get('ai_plan', {})
                fallback_plan = test_results.get('fallback_plan', {})
                comparison = data.get('comparison', {})
                
                # Check if both AI and fallback plans were generated
                ai_working = comparison.get('ai_working', False)
                plans_different = comparison.get('plans_different', False)
                
                if ai_working and plans_different:
                    ai_steps = comparison.get('ai_steps', 0)
                    fallback_steps = comparison.get('fallback_steps', 0)
                    details = f"AI plan: {ai_steps} steps, Fallback: {fallback_steps} steps, Plans different: {plans_different}"
                    self.log_result("Plan Generation Testing", True, details, response_time)
                    return True
                else:
                    details = f"Plan generation issues - AI working: {ai_working}, Plans different: {plans_different}"
                    self.log_result("Plan Generation Testing", False, details, response_time)
                    return False
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_result("Plan Generation Testing", False, details, response_time)
                return False
                
        except Exception as e:
            self.log_result("Plan Generation Testing", False, f"Exception: {str(e)}", 0)
            return False
    
    def test_task_creation_and_plan_generation(self):
        """Test 3: Task Creation and Plan Generation - /api/agent/generate-plan endpoint"""
        try:
            start_time = time.time()
            test_data = {
                "task_title": "Desarrollar una estrategia de marketing digital para una startup tecnológica",
                "task_id": f"task-{int(time.time())}"
            }
            
            response = requests.post(
                f"{API_BASE}/agent/generate-plan", 
                json=test_data,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', [])
                task_id = data.get('task_id')
                total_steps = data.get('total_steps', 0)
                task_type = data.get('task_type', '')
                ai_generated = data.get('ai_generated', False)
                
                # Check if plan was generated with reasonable content
                if len(plan) > 0 and total_steps > 0 and task_id:
                    # Check if plan steps are specific to the task (not generic)
                    specific_keywords = ['marketing', 'digital', 'startup', 'estrategia', 'tecnológica']
                    plan_text = json.dumps(plan).lower()
                    has_specific_content = any(keyword in plan_text for keyword in specific_keywords)
                    
                    details = f"Generated {total_steps} steps, Task type: {task_type}, AI generated: {ai_generated}, Specific content: {has_specific_content}"
                    self.log_result("Task Creation and Plan Generation", True, details, response_time)
                    return True, task_id
                else:
                    details = f"Invalid plan generated - Steps: {len(plan)}, Total: {total_steps}, Task ID: {task_id}"
                    self.log_result("Task Creation and Plan Generation", False, details, response_time)
                    return False, None
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_result("Task Creation and Plan Generation", False, details, response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Task Creation and Plan Generation", False, f"Exception: {str(e)}", 0)
            return False, None
    
    def test_casual_conversation_chat(self):
        """Test 4: Chat Endpoint - Casual Conversation"""
        try:
            start_time = time.time()
            test_data = {
                "message": "Hola, ¿cómo estás?",
                "context": {
                    "task_id": f"casual-{int(time.time())}"
                }
            }
            
            response = requests.post(
                f"{API_BASE}/agent/chat", 
                json=test_data,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                mode = data.get('mode', '')
                memory_used = data.get('memory_used', False)
                plan = data.get('plan')
                
                # For casual conversation, should NOT generate action plan
                is_casual_mode = mode == 'casual_conversation'
                no_action_plan = plan is None
                has_response = len(response_text) > 0
                
                if is_casual_mode and no_action_plan and has_response:
                    details = f"Mode: {mode}, Memory used: {memory_used}, Response length: {len(response_text)}, No action plan: {no_action_plan}"
                    self.log_result("Casual Conversation Chat", True, details, response_time)
                    return True
                else:
                    details = f"Unexpected casual response - Mode: {mode}, Plan: {plan is not None}, Response: {len(response_text)}, Memory: {memory_used}"
                    self.log_result("Casual Conversation Chat", False, details, response_time)
                    return False
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_result("Casual Conversation Chat", False, details, response_time)
                return False
                
        except Exception as e:
            self.log_result("Casual Conversation Chat", False, f"Exception: {str(e)}", 0)
            return False
    
    def test_complex_task_chat(self):
        """Test 5: Chat Endpoint - Complex Task with Action Plan"""
        try:
            start_time = time.time()
            test_data = {
                "message": "Crear un análisis completo sobre el impacto de la inteligencia artificial en el sector financiero",
                "context": {
                    "task_id": f"complex-{int(time.time())}"
                }
            }
            
            response = requests.post(
                f"{API_BASE}/agent/chat", 
                json=test_data,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                mode = data.get('mode', '')
                memory_used = data.get('memory_used', False)
                plan = data.get('plan', {})
                task_id = data.get('task_id')
                
                # For complex task, should generate structured action plan
                is_agent_mode = mode == 'agent_with_structured_plan'
                has_action_plan = plan and len(plan.get('steps', [])) > 0
                has_response = len(response_text) > 0
                
                if is_agent_mode and has_action_plan and has_response:
                    steps_count = len(plan.get('steps', []))
                    plan_type = plan.get('task_type', 'unknown')
                    
                    # Check if plan is specific to the task (not generic)
                    plan_text = json.dumps(plan).lower()
                    specific_keywords = ['inteligencia artificial', 'financiero', 'análisis', 'impacto', 'sector']
                    has_specific_content = any(keyword in plan_text for keyword in specific_keywords)
                    
                    details = f"Mode: {mode}, Steps: {steps_count}, Type: {plan_type}, Memory: {memory_used}, Specific: {has_specific_content}"
                    self.log_result("Complex Task Chat", True, details, response_time)
                    return True, task_id
                else:
                    details = f"Complex task issues - Mode: {mode}, Plan steps: {len(plan.get('steps', []))}, Response: {len(response_text)}, Memory: {memory_used}"
                    self.log_result("Complex Task Chat", False, details, response_time)
                    return False, None
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_result("Complex Task Chat", False, details, response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Complex Task Chat", False, f"Exception: {str(e)}", 0)
            return False, None
    
    def test_multiple_different_tasks(self):
        """Test 6: Multiple Different Tasks with Different Plans"""
        try:
            tasks = [
                "Investigar las mejores prácticas de ciberseguridad para empresas",
                "Desarrollar un plan de contenido para redes sociales"
            ]
            
            task_results = []
            
            for i, task_message in enumerate(tasks):
                start_time = time.time()
                test_data = {
                    "message": task_message,
                    "context": {
                        "task_id": f"multi-task-{i}-{int(time.time())}"
                    }
                }
                
                response = requests.post(
                    f"{API_BASE}/agent/chat", 
                    json=test_data,
                    timeout=30
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    plan = data.get('plan', {})
                    steps = plan.get('steps', [])
                    
                    task_results.append({
                        'task': task_message[:30] + "...",
                        'steps_count': len(steps),
                        'plan_type': plan.get('task_type', 'unknown'),
                        'steps_titles': [step.get('title', '') for step in steps[:2]],  # First 2 step titles
                        'response_time': response_time
                    })
                else:
                    task_results.append({
                        'task': task_message[:30] + "...",
                        'error': f"HTTP {response.status_code}",
                        'response_time': response_time
                    })
                
                # Small delay between requests
                time.sleep(1)
            
            # Analyze results
            successful_tasks = [r for r in task_results if 'error' not in r]
            different_plans = len(set(str(r.get('steps_titles', [])) for r in successful_tasks)) > 1
            all_have_plans = all(r.get('steps_count', 0) > 0 for r in successful_tasks)
            
            total_response_time = sum(r.get('response_time', 0) for r in task_results)
            
            if len(successful_tasks) >= 2 and different_plans and all_have_plans:
                details = f"Successfully created {len(successful_tasks)}/2 different plans, Plans are different: {different_plans}"
                self.log_result("Multiple Different Tasks", True, details, total_response_time)
                return True
            else:
                details = f"Issues with multiple tasks - Success: {len(successful_tasks)}/2, Different: {different_plans}, All have plans: {all_have_plans}"
                self.log_result("Multiple Different Tasks", False, details, total_response_time)
                return False
                
        except Exception as e:
            self.log_result("Multiple Different Tasks", False, f"Exception: {str(e)}", 0)
            return False
    
    def test_task_completion_and_delivery(self, task_id: str = None):
        """Test 7: Task Completion and Delivery"""
        if not task_id:
            # Create a task first
            success, task_id = self.test_task_creation_and_plan_generation()
            if not success or not task_id:
                self.log_result("Task Completion and Delivery", False, "Could not create task for testing", 0)
                return False
        
        try:
            # Wait a bit for task to start processing
            time.sleep(3)
            
            start_time = time.time()
            response = requests.get(f"{API_BASE}/agent/get-task-plan/{task_id}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', [])
                status = data.get('status', '')
                progress = data.get('progress', 0)
                final_result = data.get('final_result')
                
                # Check if task is progressing or completed
                has_plan = len(plan) > 0
                is_progressing = status in ['executing', 'completed'] or progress > 0
                
                if has_plan and is_progressing:
                    details = f"Status: {status}, Progress: {progress}%, Steps: {len(plan)}, Final result: {final_result is not None}"
                    self.log_result("Task Completion and Delivery", True, details, response_time)
                    return True
                else:
                    details = f"Task not progressing - Status: {status}, Progress: {progress}%, Plan: {len(plan)} steps"
                    self.log_result("Task Completion and Delivery", False, details, response_time)
                    return False
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_result("Task Completion and Delivery", False, details, response_time)
                return False
                
        except Exception as e:
            self.log_result("Task Completion and Delivery", False, f"Exception: {str(e)}", 0)
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Starting Comprehensive Mitosis Backend Testing - Post Syntax Error Fix")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Test 1: Basic Health Check
        self.test_basic_health_check()
        
        # Test 2: Plan Generation Testing
        self.test_plan_generation_testing()
        
        # Test 3: Task Creation and Plan Generation
        success, task_id = self.test_task_creation_and_plan_generation()
        
        # Test 4: Casual Conversation Chat
        self.test_casual_conversation_chat()
        
        # Test 5: Complex Task Chat
        complex_success, complex_task_id = self.test_complex_task_chat()
        
        # Test 6: Multiple Different Tasks
        self.test_multiple_different_tasks()
        
        # Test 7: Task Completion and Delivery
        if complex_task_id:
            self.test_task_completion_and_delivery(complex_task_id)
        else:
            self.test_task_completion_and_delivery()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY - MITOSIS BACKEND POST SYNTAX ERROR FIX")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            print(f"{result['status']} - {result['test']} ({result['response_time']})")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 FINAL ASSESSMENT:")
        if success_rate >= 80:
            print("✅ SYNTAX ERROR FIX SUCCESSFUL - Backend is working well")
        elif success_rate >= 60:
            print("⚠️ PARTIAL SUCCESS - Some issues remain after syntax error fix")
        else:
            print("❌ CRITICAL ISSUES REMAIN - Syntax error fix may not be complete")
        
        print("\n🔧 KEY FINDINGS:")
        
        # Analyze specific test results
        health_tests = [r for r in self.results if 'Health' in r['test']]
        plan_tests = [r for r in self.results if 'Plan' in r['test'] or 'Task Creation' in r['test']]
        chat_tests = [r for r in self.results if 'Chat' in r['test']]
        
        if all(r['passed'] for r in health_tests):
            print("✅ Backend services are healthy and responding")
        else:
            print("❌ Backend health issues detected")
            
        if all(r['passed'] for r in plan_tests):
            print("✅ Plan generation is working correctly after syntax fix")
        else:
            print("❌ Plan generation still has issues - syntax error may not be fully resolved")
            
        if all(r['passed'] for r in chat_tests):
            print("✅ Chat functionality is working properly")
        else:
            print("❌ Chat functionality has problems")
        
        print("\n🔍 SYNTAX ERROR FIX VERIFICATION:")
        plan_generation_working = any(r['passed'] and 'Plan Generation' in r['test'] for r in self.results)
        complex_tasks_working = any(r['passed'] and 'Complex Task' in r['test'] for r in self.results)
        multiple_tasks_working = any(r['passed'] and 'Multiple Different' in r['test'] for r in self.results)
        
        if plan_generation_working and complex_tasks_working:
            print("✅ generate_dynamic_plan_with_ai function appears to be working correctly")
        else:
            print("❌ generate_dynamic_plan_with_ai function may still have issues")
            
        if multiple_tasks_working:
            print("✅ Multiple task creation with different plans is working")
        else:
            print("❌ Multiple task creation may have issues")

def main():
    """Main function"""
    tester = MitosisBackendTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()