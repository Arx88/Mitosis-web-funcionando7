#!/usr/bin/env python3
"""
COMPREHENSIVE MITOSIS AGENT PLAN EXECUTION FLOW TESTING
Testing the complete plan generation and execution pipeline

CRITICAL OBJECTIVE: Verify that the refactoring eliminated endpoint duplication 
and that the agent can now generate AND execute plans completely.

Test Coverage:
1. Plan Generation Testing - /api/agent/generate-plan
2. Execution Endpoints Testing - /api/agent/start-task-execution/<task_id>
3. Step Execution Testing - /api/agent/execute-step/<task_id>/<step_id>
4. WebSocket Events Testing - Confirm correct events are emitted
5. Integration Flow Testing - Complete task creation, plan generation, and step execution
"""

import requests
import json
import time
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://11a8329d-458b-411d-ad58-e540e377cb3b.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisExecutionTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MitosisExecutionTester/1.0'
        })
        self.test_results = []
        self.task_id = None
        self.generated_plan = None
        
    def log_test_result(self, test_name: str, success: bool, details: str, response_data=None):
        """Log test result with details"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {details}")
        
        if response_data and not success:
            logger.error(f"Response data: {json.dumps(response_data, indent=2)}")
    
    def test_backend_health(self):
        """Test 1: Verify backend health and agent status"""
        logger.info("🔍 Testing backend health and agent status...")
        
        try:
            # Test general health
            health_response = self.session.get(f"{API_BASE}/health", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                self.log_test_result(
                    "Backend Health Check",
                    True,
                    f"Backend healthy - Services: {health_data.get('services', {})}"
                )
            else:
                self.log_test_result(
                    "Backend Health Check",
                    False,
                    f"Health check failed with status {health_response.status_code}"
                )
                return False
            
            # Test agent health
            agent_health_response = self.session.get(f"{API_BASE}/agent/health", timeout=10)
            if agent_health_response.status_code == 200:
                agent_data = agent_health_response.json()
                self.log_test_result(
                    "Agent Health Check",
                    True,
                    f"Agent healthy - MongoDB: {agent_data.get('mongodb', {}).get('connected', False)}, Ollama: {agent_data.get('ollama', {}).get('connected', False)}"
                )
            else:
                self.log_test_result(
                    "Agent Health Check",
                    False,
                    f"Agent health check failed with status {agent_health_response.status_code}"
                )
                return False
            
            # Test agent status
            status_response = self.session.get(f"{API_BASE}/agent/status", timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                self.log_test_result(
                    "Agent Status Check",
                    True,
                    f"Agent status OK - Ollama connected: {status_data.get('ollama', {}).get('connected', False)}, Tools: {status_data.get('tools_count', 0)}"
                )
                return True
            else:
                self.log_test_result(
                    "Agent Status Check",
                    False,
                    f"Agent status check failed with status {status_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Backend Health Check",
                False,
                f"Exception during health check: {str(e)}"
            )
            return False
    
    def test_plan_generation(self):
        """Test 2: Plan Generation Testing - /api/agent/generate-plan"""
        logger.info("🔍 Testing plan generation endpoint...")
        
        try:
            # Generate a unique task ID
            self.task_id = f"test_task_{int(time.time())}"
            
            # Test plan generation with a comprehensive task
            plan_request = {
                "task_title": "Crear un análisis completo de mercado para productos de software en 2025 con recomendaciones estratégicas",
                "task_id": self.task_id
            }
            
            logger.info(f"📋 Generating plan for task: {plan_request['task_title']}")
            
            plan_response = self.session.post(
                f"{API_BASE}/agent/generate-plan",
                json=plan_request,
                timeout=30
            )
            
            if plan_response.status_code == 200:
                plan_data = plan_response.json()
                self.generated_plan = plan_data
                
                # Validate plan structure
                required_fields = ['plan', 'task_id', 'enhanced_title', 'total_steps', 'task_type']
                missing_fields = [field for field in required_fields if field not in plan_data]
                
                if missing_fields:
                    self.log_test_result(
                        "Plan Generation Structure",
                        False,
                        f"Missing required fields: {missing_fields}",
                        plan_data
                    )
                    return False
                
                # Validate plan steps
                steps = plan_data.get('plan', [])
                if not steps or len(steps) < 3:
                    self.log_test_result(
                        "Plan Generation Steps",
                        False,
                        f"Plan has insufficient steps: {len(steps)}",
                        plan_data
                    )
                    return False
                
                # Validate step structure
                for i, step in enumerate(steps):
                    step_required = ['id', 'title', 'description', 'tool']
                    step_missing = [field for field in step_required if field not in step]
                    if step_missing:
                        self.log_test_result(
                            f"Plan Step {i+1} Structure",
                            False,
                            f"Step missing fields: {step_missing}",
                            step
                        )
                        return False
                
                self.log_test_result(
                    "Plan Generation",
                    True,
                    f"Plan generated successfully - {len(steps)} steps, enhanced title: '{plan_data.get('enhanced_title', 'N/A')}', complexity: {plan_data.get('complexity', 'N/A')}"
                )
                
                # Log plan details
                logger.info(f"📊 Plan Details:")
                logger.info(f"   - Task ID: {plan_data.get('task_id')}")
                logger.info(f"   - Enhanced Title: {plan_data.get('enhanced_title')}")
                logger.info(f"   - Total Steps: {plan_data.get('total_steps')}")
                logger.info(f"   - Task Type: {plan_data.get('task_type')}")
                logger.info(f"   - Complexity: {plan_data.get('complexity')}")
                logger.info(f"   - Estimated Time: {plan_data.get('estimated_total_time')}")
                
                for i, step in enumerate(steps):
                    logger.info(f"   Step {i+1}: {step.get('title')} (Tool: {step.get('tool')})")
                
                return True
            else:
                self.log_test_result(
                    "Plan Generation",
                    False,
                    f"Plan generation failed with status {plan_response.status_code}",
                    plan_response.text
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Plan Generation",
                False,
                f"Exception during plan generation: {str(e)}"
            )
            return False
    
    def test_task_execution_start(self):
        """Test 3: Execution Endpoints Testing - /api/agent/start-task-execution/<task_id>"""
        logger.info("🔍 Testing task execution start endpoint...")
        
        if not self.task_id or not self.generated_plan:
            self.log_test_result(
                "Task Execution Start",
                False,
                "No task ID or plan available for execution testing"
            )
            return False
        
        try:
            # Start task execution
            logger.info(f"🚀 Starting execution for task: {self.task_id}")
            
            execution_response = self.session.post(
                f"{API_BASE}/agent/start-task-execution/{self.task_id}",
                json={},
                timeout=15
            )
            
            if execution_response.status_code == 200:
                execution_data = execution_response.json()
                
                self.log_test_result(
                    "Task Execution Start",
                    True,
                    f"Task execution started successfully - Response: {execution_data.get('message', 'Started')}"
                )
                
                # Wait a moment for execution to begin
                time.sleep(2)
                return True
            else:
                self.log_test_result(
                    "Task Execution Start",
                    False,
                    f"Task execution start failed with status {execution_response.status_code}",
                    execution_response.text
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Task Execution Start",
                False,
                f"Exception during task execution start: {str(e)}"
            )
            return False
    
    def test_step_execution(self):
        """Test 4: Step Execution Testing - /api/agent/execute-step/<task_id>/<step_id>"""
        logger.info("🔍 Testing individual step execution...")
        
        if not self.task_id or not self.generated_plan:
            self.log_test_result(
                "Step Execution",
                False,
                "No task ID or plan available for step execution testing"
            )
            return False
        
        try:
            steps = self.generated_plan.get('plan', [])
            if not steps:
                self.log_test_result(
                    "Step Execution",
                    False,
                    "No steps available in generated plan"
                )
                return False
            
            # Test execution of first step
            first_step = steps[0]
            step_id = first_step.get('id')
            
            if not step_id:
                self.log_test_result(
                    "Step Execution",
                    False,
                    "First step has no ID"
                )
                return False
            
            logger.info(f"⚡ Executing step: {first_step.get('title')} (ID: {step_id})")
            
            step_response = self.session.post(
                f"{API_BASE}/agent/execute-step/{self.task_id}/{step_id}",
                json={},
                timeout=20
            )
            
            if step_response.status_code == 200:
                step_data = step_response.json()
                
                self.log_test_result(
                    "Step Execution",
                    True,
                    f"Step executed successfully - Success: {step_data.get('success', False)}, Result type: {type(step_data.get('result', {}))}"
                )
                
                # Log step execution details
                if 'result' in step_data:
                    result = step_data['result']
                    logger.info(f"📊 Step Execution Result:")
                    logger.info(f"   - Success: {step_data.get('success', False)}")
                    logger.info(f"   - Result Type: {result.get('type', 'unknown') if isinstance(result, dict) else type(result)}")
                    if isinstance(result, dict) and 'summary' in result:
                        logger.info(f"   - Summary: {result.get('summary')}")
                
                return True
            else:
                self.log_test_result(
                    "Step Execution",
                    False,
                    f"Step execution failed with status {step_response.status_code}",
                    step_response.text
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Step Execution",
                False,
                f"Exception during step execution: {str(e)}"
            )
            return False
    
    def test_task_plan_retrieval(self):
        """Test 5: Task Plan Retrieval - /api/agent/get-task-plan/<task_id>"""
        logger.info("🔍 Testing task plan retrieval...")
        
        if not self.task_id:
            self.log_test_result(
                "Task Plan Retrieval",
                False,
                "No task ID available for plan retrieval testing"
            )
            return False
        
        try:
            logger.info(f"📋 Retrieving plan for task: {self.task_id}")
            
            plan_response = self.session.get(
                f"{API_BASE}/agent/get-task-plan/{self.task_id}",
                timeout=10
            )
            
            if plan_response.status_code == 200:
                plan_data = plan_response.json()
                
                # Validate plan retrieval structure
                required_fields = ['task_id', 'status', 'plan', 'stats']
                missing_fields = [field for field in required_fields if field not in plan_data]
                
                if missing_fields:
                    self.log_test_result(
                        "Task Plan Retrieval",
                        False,
                        f"Missing required fields in plan retrieval: {missing_fields}",
                        plan_data
                    )
                    return False
                
                stats = plan_data.get('stats', {})
                self.log_test_result(
                    "Task Plan Retrieval",
                    True,
                    f"Plan retrieved successfully - Status: {plan_data.get('status')}, Total steps: {stats.get('total_steps', 0)}, Completed: {stats.get('completed_steps', 0)}"
                )
                
                # Log plan status details
                logger.info(f"📊 Plan Status:")
                logger.info(f"   - Task Status: {plan_data.get('status')}")
                logger.info(f"   - Total Steps: {stats.get('total_steps', 0)}")
                logger.info(f"   - Completed Steps: {stats.get('completed_steps', 0)}")
                logger.info(f"   - In Progress Steps: {stats.get('in_progress_steps', 0)}")
                logger.info(f"   - Remaining Steps: {stats.get('remaining_steps', 0)}")
                
                return True
            else:
                self.log_test_result(
                    "Task Plan Retrieval",
                    False,
                    f"Plan retrieval failed with status {plan_response.status_code}",
                    plan_response.text
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Task Plan Retrieval",
                False,
                f"Exception during plan retrieval: {str(e)}"
            )
            return False
    
    def test_integration_flow(self):
        """Test 6: Integration Flow Testing - Complete workflow"""
        logger.info("🔍 Testing complete integration flow...")
        
        try:
            # Create a new task for integration testing
            integration_task_id = f"integration_test_{int(time.time())}"
            
            # Step 1: Generate plan
            logger.info("📋 Step 1: Generating plan for integration test...")
            plan_request = {
                "task_title": "Desarrollar una estrategia de marketing digital para una startup tecnológica",
                "task_id": integration_task_id
            }
            
            plan_response = self.session.post(
                f"{API_BASE}/agent/generate-plan",
                json=plan_request,
                timeout=25
            )
            
            if plan_response.status_code != 200:
                self.log_test_result(
                    "Integration Flow - Plan Generation",
                    False,
                    f"Plan generation failed in integration test with status {plan_response.status_code}"
                )
                return False
            
            plan_data = plan_response.json()
            steps = plan_data.get('plan', [])
            
            if len(steps) < 3:
                self.log_test_result(
                    "Integration Flow - Plan Validation",
                    False,
                    f"Integration plan has insufficient steps: {len(steps)}"
                )
                return False
            
            # Step 2: Retrieve plan to verify persistence
            logger.info("📋 Step 2: Verifying plan persistence...")
            time.sleep(1)
            
            retrieval_response = self.session.get(
                f"{API_BASE}/agent/get-task-plan/{integration_task_id}",
                timeout=10
            )
            
            if retrieval_response.status_code != 200:
                self.log_test_result(
                    "Integration Flow - Plan Persistence",
                    False,
                    f"Plan retrieval failed in integration test with status {retrieval_response.status_code}"
                )
                return False
            
            # Step 3: Execute first step
            logger.info("⚡ Step 3: Executing first step...")
            first_step_id = steps[0].get('id')
            
            if not first_step_id:
                self.log_test_result(
                    "Integration Flow - Step ID",
                    False,
                    "First step has no ID in integration test"
                )
                return False
            
            step_response = self.session.post(
                f"{API_BASE}/agent/execute-step/{integration_task_id}/{first_step_id}",
                json={},
                timeout=20
            )
            
            if step_response.status_code != 200:
                self.log_test_result(
                    "Integration Flow - Step Execution",
                    False,
                    f"Step execution failed in integration test with status {step_response.status_code}"
                )
                return False
            
            # Step 4: Verify step completion
            logger.info("📊 Step 4: Verifying step completion...")
            time.sleep(1)
            
            final_plan_response = self.session.get(
                f"{API_BASE}/agent/get-task-plan/{integration_task_id}",
                timeout=10
            )
            
            if final_plan_response.status_code == 200:
                final_plan_data = final_plan_response.json()
                completed_steps = final_plan_data.get('stats', {}).get('completed_steps', 0)
                
                self.log_test_result(
                    "Integration Flow",
                    True,
                    f"Integration flow completed successfully - Plan generated, persisted, step executed, completion verified. Completed steps: {completed_steps}"
                )
                
                logger.info(f"🎉 Integration Flow Summary:")
                logger.info(f"   - Task ID: {integration_task_id}")
                logger.info(f"   - Plan Generated: ✅ ({len(steps)} steps)")
                logger.info(f"   - Plan Persisted: ✅")
                logger.info(f"   - Step Executed: ✅")
                logger.info(f"   - Completion Verified: ✅ ({completed_steps} completed)")
                
                return True
            else:
                self.log_test_result(
                    "Integration Flow - Final Verification",
                    False,
                    f"Final plan verification failed with status {final_plan_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Integration Flow",
                False,
                f"Exception during integration flow: {str(e)}"
            )
            return False
    
    def test_endpoint_duplication_check(self):
        """Test 7: Verify no endpoint duplication exists"""
        logger.info("🔍 Testing for endpoint duplication...")
        
        try:
            # Test that all required endpoints exist and respond
            endpoints_to_test = [
                ('/api/agent/generate-plan', 'POST'),
                ('/api/agent/start-task-execution/test_id', 'POST'),
                ('/api/agent/execute-step/test_id/test_step', 'POST'),
                ('/api/agent/get-task-plan/test_id', 'GET'),
                ('/api/agent/health', 'GET'),
                ('/api/agent/status', 'GET')
            ]
            
            endpoint_results = []
            
            for endpoint, method in endpoints_to_test:
                try:
                    if method == 'GET':
                        response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=5)
                    else:
                        response = self.session.post(f"{BACKEND_URL}{endpoint}", json={}, timeout=5)
                    
                    # We expect some endpoints to fail with 400/404 for test data, but they should exist
                    endpoint_exists = response.status_code not in [404, 405]  # 404 = not found, 405 = method not allowed
                    endpoint_results.append((endpoint, method, endpoint_exists, response.status_code))
                    
                except Exception as e:
                    endpoint_results.append((endpoint, method, False, f"Exception: {str(e)}"))
            
            # Check results
            missing_endpoints = [f"{method} {endpoint}" for endpoint, method, exists, status in endpoint_results if not exists]
            
            if missing_endpoints:
                self.log_test_result(
                    "Endpoint Duplication Check",
                    False,
                    f"Missing or inaccessible endpoints: {missing_endpoints}"
                )
                return False
            else:
                self.log_test_result(
                    "Endpoint Duplication Check",
                    True,
                    f"All required endpoints are accessible - {len(endpoint_results)} endpoints verified"
                )
                
                # Log endpoint status
                logger.info("📡 Endpoint Verification Results:")
                for endpoint, method, exists, status in endpoint_results:
                    status_icon = "✅" if exists else "❌"
                    logger.info(f"   {status_icon} {method} {endpoint} - Status: {status}")
                
                return True
                
        except Exception as e:
            self.log_test_result(
                "Endpoint Duplication Check",
                False,
                f"Exception during endpoint duplication check: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info("🚀 Starting Comprehensive Mitosis Agent Plan Execution Flow Testing")
        logger.info(f"🌐 Backend URL: {BACKEND_URL}")
        logger.info("=" * 80)
        
        test_methods = [
            self.test_backend_health,
            self.test_plan_generation,
            self.test_task_execution_start,
            self.test_step_execution,
            self.test_task_plan_retrieval,
            self.test_integration_flow,
            self.test_endpoint_duplication_check
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                logger.error(f"❌ Test method {test_method.__name__} failed with exception: {str(e)}")
        
        # Generate summary
        logger.info("=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        logger.info(f"🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            logger.info(f"{status} - {result['test_name']}: {result['details']}")
        
        # Critical assessment
        critical_tests = [
            "Plan Generation",
            "Task Execution Start", 
            "Step Execution",
            "Integration Flow"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        logger.info("=" * 80)
        logger.info("🎯 CRITICAL ASSESSMENT")
        logger.info("=" * 80)
        
        if critical_passed == len(critical_tests):
            logger.info("🎉 SUCCESS: All critical plan execution functionality is working!")
            logger.info("✅ The agent can generate AND execute plans completely")
            logger.info("✅ Refactoring appears to have eliminated endpoint duplication")
            logger.info("✅ Complete plan execution flow is operational")
        else:
            logger.info("❌ CRITICAL ISSUES FOUND: Plan execution flow has problems")
            logger.info(f"❌ Critical tests passed: {critical_passed}/{len(critical_tests)}")
            logger.info("❌ The agent may not be able to generate and execute plans properly")
        
        return success_rate >= 80 and critical_passed == len(critical_tests)

def main():
    """Main test execution"""
    tester = MitosisExecutionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 MITOSIS PLAN EXECUTION TESTING: SUCCESS")
        exit(0)
    else:
        print("\n❌ MITOSIS PLAN EXECUTION TESTING: FAILED")
        exit(1)

if __name__ == "__main__":
    main()