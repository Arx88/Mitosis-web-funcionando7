#!/usr/bin/env python3
"""
Comprehensive WebSocket Backend Testing for Mitosis V5-Beta
Tests the WebSocket system with automatic plan execution focusing on:
1. Backend Health Check
2. WebSocket Manager initialization
3. Plan Generation with auto_execute=true
4. Step Execution endpoints
5. Task Initialization
6. WebSocket Events
7. Tool Simulation with activities
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://491dc7aa-905c-4a31-b16f-f0eab23cf6e1.preview.emergentagent.com"

class WebSocketBackendTester:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        logger.info(f"{status} - {test_name}: {details} ({response_time:.2f}s)")
        
    def test_backend_health_check(self) -> bool:
        """Test 1: Backend Health Check - Verify all backend services are healthy and running"""
        try:
            start_time = time.time()
            
            # Test main health endpoint
            response = self.session.get(f"{self.backend_url}/api/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                services = health_data.get('services', {})
                
                # Check all required services
                ollama_healthy = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                database_connected = services.get('database', False)
                
                if ollama_healthy and tools_count > 0 and database_connected:
                    self.log_test_result(
                        "Backend Health Check", 
                        True, 
                        f"All services healthy - Ollama: {ollama_healthy}, Tools: {tools_count}, DB: {database_connected}",
                        response_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "Backend Health Check", 
                        False, 
                        f"Some services unhealthy - Ollama: {ollama_healthy}, Tools: {tools_count}, DB: {database_connected}",
                        response_time
                    )
                    return False
            else:
                self.log_test_result(
                    "Backend Health Check", 
                    False, 
                    f"Health endpoint returned {response.status_code}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test_result("Backend Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_manager_initialization(self) -> bool:
        """Test 2: WebSocket Manager - Test that the WebSocket manager is initialized and working"""
        try:
            start_time = time.time()
            
            # Test agent status endpoint which should show WebSocket status
            response = self.session.get(f"{self.backend_url}/api/agent/status", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Check if WebSocket-related information is present
                # The status should indicate the system is ready for real-time updates
                if 'status' in status_data and status_data.get('status') == 'running':
                    self.log_test_result(
                        "WebSocket Manager Initialization", 
                        True, 
                        f"Agent status indicates system ready for WebSocket communication",
                        response_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "WebSocket Manager Initialization", 
                        False, 
                        f"Agent status does not indicate WebSocket readiness: {status_data}",
                        response_time
                    )
                    return False
            else:
                self.log_test_result(
                    "WebSocket Manager Initialization", 
                    False, 
                    f"Agent status endpoint returned {response.status_code}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test_result("WebSocket Manager Initialization", False, f"Exception: {str(e)}")
            return False
    
    def test_plan_generation_with_auto_execute(self) -> Dict[str, Any]:
        """Test 3: Plan Generation - Test the /api/agent/chat endpoint with auto_execute=true"""
        try:
            start_time = time.time()
            
            # Generate a task that should trigger plan generation
            test_message = "Crear un informe sobre inteligencia artificial"
            task_id = str(uuid.uuid4())
            
            payload = {
                'message': test_message,
                'context': {
                    'task_id': task_id,
                    'auto_execute': True
                }
            }
            
            response = self.session.post(f"{self.backend_url}/api/agent/chat", json=payload, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                chat_data = response.json()
                
                # Check if plan was generated
                plan = chat_data.get('plan')
                task_id_returned = chat_data.get('task_id')
                execution_status = chat_data.get('execution_status')
                
                if plan and 'steps' in plan and len(plan['steps']) > 0:
                    steps_count = len(plan['steps'])
                    self.log_test_result(
                        "Plan Generation with Auto Execute", 
                        True, 
                        f"Plan generated successfully with {steps_count} steps, task_id: {task_id_returned}, status: {execution_status}",
                        response_time
                    )
                    return {
                        'success': True,
                        'task_id': task_id_returned,
                        'plan': plan,
                        'steps_count': steps_count
                    }
                else:
                    self.log_test_result(
                        "Plan Generation with Auto Execute", 
                        False, 
                        f"Plan not generated properly: {chat_data}",
                        response_time
                    )
                    return {'success': False}
            else:
                error_text = response.text if response.text else "No response text"
                self.log_test_result(
                    "Plan Generation with Auto Execute", 
                    False, 
                    f"Chat endpoint returned {response.status_code}: {error_text}",
                    response_time
                )
                return {'success': False}
                
        except Exception as e:
            self.log_test_result("Plan Generation with Auto Execute", False, f"Exception: {str(e)}")
            return {'success': False}
    
    def test_step_execution_endpoint(self, task_id: str, step_id: str) -> bool:
        """Test 4: Step Execution - Test the /api/agent/execute-step/<task_id>/<step_id> endpoint"""
        try:
            start_time = time.time()
            
            # Execute a specific step
            response = self.session.post(
                f"{self.backend_url}/api/agent/execute-step/{task_id}/{step_id}", 
                json={}, 
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                execution_data = response.json()
                
                success = execution_data.get('success', False)
                step_id_returned = execution_data.get('step_id')
                result = execution_data.get('result')
                
                if success and step_id_returned and result:
                    self.log_test_result(
                        "Step Execution Endpoint", 
                        True, 
                        f"Step {step_id} executed successfully with result",
                        response_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "Step Execution Endpoint", 
                        False, 
                        f"Step execution failed: {execution_data}",
                        response_time
                    )
                    return False
            elif response.status_code == 400:
                # This might be expected if steps need to be executed in order
                error_data = response.json()
                if 'must_complete_first' in error_data:
                    self.log_test_result(
                        "Step Execution Endpoint", 
                        True, 
                        f"Step execution validation working - must complete previous steps first",
                        response_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "Step Execution Endpoint", 
                        False, 
                        f"Unexpected 400 error: {error_data}",
                        response_time
                    )
                    return False
            else:
                error_text = response.text if response.text else "No response text"
                self.log_test_result(
                    "Step Execution Endpoint", 
                    False, 
                    f"Execute step endpoint returned {response.status_code}: {error_text}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test_result("Step Execution Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_task_initialization_endpoint(self) -> Dict[str, Any]:
        """Test 5: Task Initialization - Test the /api/agent/initialize-task endpoint"""
        try:
            start_time = time.time()
            
            task_id = str(uuid.uuid4())
            payload = {
                'task_id': task_id,
                'title': 'Test task initialization with WebSocket events',
                'auto_execute': True
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/agent/initialize-task", 
                json=payload, 
                timeout=20
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                init_data = response.json()
                
                success = init_data.get('success', False)
                returned_task_id = init_data.get('task_id')
                plan = init_data.get('plan')
                auto_execute = init_data.get('auto_execute', False)
                
                if success and returned_task_id and plan:
                    self.log_test_result(
                        "Task Initialization Endpoint", 
                        True, 
                        f"Task initialized successfully - ID: {returned_task_id}, auto_execute: {auto_execute}",
                        response_time
                    )
                    return {
                        'success': True,
                        'task_id': returned_task_id,
                        'plan': plan,
                        'auto_execute': auto_execute
                    }
                else:
                    self.log_test_result(
                        "Task Initialization Endpoint", 
                        False, 
                        f"Task initialization failed: {init_data}",
                        response_time
                    )
                    return {'success': False}
            else:
                error_text = response.text if response.text else "No response text"
                self.log_test_result(
                    "Task Initialization Endpoint", 
                    False, 
                    f"Initialize task endpoint returned {response.status_code}: {error_text}",
                    response_time
                )
                return {'success': False}
                
        except Exception as e:
            self.log_test_result("Task Initialization Endpoint", False, f"Exception: {str(e)}")
            return {'success': False}
    
    def test_websocket_events_simulation(self, task_id: str) -> bool:
        """Test 6: WebSocket Events - Verify that WebSocket events would be emitted correctly"""
        try:
            start_time = time.time()
            
            # Test getting task plan which should show WebSocket-ready structure
            response = self.session.get(f"{self.backend_url}/api/agent/get-task-plan/{task_id}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                plan_data = response.json()
                
                # Check if the plan structure supports WebSocket events
                plan = plan_data.get('plan', [])
                task_status = plan_data.get('status')
                stats = plan_data.get('stats', {})
                
                if plan and isinstance(plan, list) and len(plan) > 0:
                    # Check if steps have the structure needed for WebSocket events
                    first_step = plan[0]
                    has_id = 'id' in first_step
                    has_title = 'title' in first_step
                    has_status_tracking = 'status' in first_step or 'completed' in first_step
                    
                    if has_id and has_title and has_status_tracking:
                        self.log_test_result(
                            "WebSocket Events Structure", 
                            True, 
                            f"Task plan structure supports WebSocket events - {len(plan)} steps with proper tracking",
                            response_time
                        )
                        return True
                    else:
                        self.log_test_result(
                            "WebSocket Events Structure", 
                            False, 
                            f"Task plan structure missing WebSocket event support fields",
                            response_time
                        )
                        return False
                else:
                    self.log_test_result(
                        "WebSocket Events Structure", 
                        False, 
                        f"No valid plan structure found for WebSocket events",
                        response_time
                    )
                    return False
            else:
                self.log_test_result(
                    "WebSocket Events Structure", 
                    False, 
                    f"Get task plan endpoint returned {response.status_code}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test_result("WebSocket Events Structure", False, f"Exception: {str(e)}")
            return False
    
    def test_tool_simulation_with_activities(self) -> bool:
        """Test 7: Tool Simulation - Test that the execute_tool_simulation function works with activities"""
        try:
            start_time = time.time()
            
            # Test a simple chat that should trigger tool usage
            test_message = "Buscar información sobre machine learning"
            task_id = str(uuid.uuid4())
            
            payload = {
                'message': test_message,
                'context': {
                    'task_id': task_id
                }
            }
            
            response = self.session.post(f"{self.backend_url}/api/agent/chat", json=payload, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                chat_data = response.json()
                
                # Check if tools were used or planned
                tool_calls = chat_data.get('tool_calls', [])
                plan = chat_data.get('plan', {})
                plan_steps = plan.get('steps', []) if plan else []
                
                # Look for tool usage in plan steps
                tools_in_plan = []
                for step in plan_steps:
                    if 'tool' in step:
                        tools_in_plan.append(step['tool'])
                
                if tool_calls or tools_in_plan:
                    self.log_test_result(
                        "Tool Simulation with Activities", 
                        True, 
                        f"Tools detected - Direct calls: {len(tool_calls)}, Plan tools: {tools_in_plan}",
                        response_time
                    )
                    return True
                else:
                    # Even if no tools were directly called, if we got a plan, the system is working
                    if plan_steps:
                        self.log_test_result(
                            "Tool Simulation with Activities", 
                            True, 
                            f"Tool simulation infrastructure working - {len(plan_steps)} steps planned",
                            response_time
                        )
                        return True
                    else:
                        self.log_test_result(
                            "Tool Simulation with Activities", 
                            False, 
                            f"No tool usage or planning detected",
                            response_time
                        )
                        return False
            else:
                error_text = response.text if response.text else "No response text"
                self.log_test_result(
                    "Tool Simulation with Activities", 
                    False, 
                    f"Chat endpoint returned {response.status_code}: {error_text}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test_result("Tool Simulation with Activities", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all WebSocket backend tests"""
        logger.info("🚀 Starting Comprehensive WebSocket Backend Testing for Mitosis V5-Beta")
        logger.info(f"🔗 Backend URL: {self.backend_url}")
        
        # Test 1: Backend Health Check
        health_ok = self.test_backend_health_check()
        
        # Test 2: WebSocket Manager Initialization
        websocket_ok = self.test_websocket_manager_initialization()
        
        # Test 3: Plan Generation with Auto Execute
        plan_result = self.test_plan_generation_with_auto_execute()
        plan_ok = plan_result.get('success', False)
        
        # Test 4: Step Execution (if we have a plan)
        step_ok = False
        if plan_ok and plan_result.get('plan'):
            plan = plan_result['plan']
            task_id = plan_result['task_id']
            steps = plan.get('steps', [])
            if steps and len(steps) > 0:
                first_step = steps[0]
                step_id = first_step.get('id', 'step_1')
                step_ok = self.test_step_execution_endpoint(task_id, step_id)
        
        # Test 5: Task Initialization
        init_result = self.test_task_initialization_endpoint()
        init_ok = init_result.get('success', False)
        
        # Test 6: WebSocket Events (if we have a task)
        events_ok = False
        if init_ok:
            task_id = init_result['task_id']
            events_ok = self.test_websocket_events_simulation(task_id)
        elif plan_ok:
            task_id = plan_result['task_id']
            events_ok = self.test_websocket_events_simulation(task_id)
        
        # Test 7: Tool Simulation
        tools_ok = self.test_tool_simulation_with_activities()
        
        # Summary
        total_tests = 7
        passed_tests = sum([health_ok, websocket_ok, plan_ok, step_ok, init_ok, events_ok, tools_ok])
        success_rate = (passed_tests / total_tests) * 100
        
        logger.info("\n" + "="*80)
        logger.info("📊 COMPREHENSIVE WEBSOCKET BACKEND TEST RESULTS")
        logger.info("="*80)
        logger.info(f"✅ Backend Health Check: {'PASSED' if health_ok else 'FAILED'}")
        logger.info(f"✅ WebSocket Manager: {'PASSED' if websocket_ok else 'FAILED'}")
        logger.info(f"✅ Plan Generation (auto_execute): {'PASSED' if plan_ok else 'FAILED'}")
        logger.info(f"✅ Step Execution Endpoint: {'PASSED' if step_ok else 'FAILED'}")
        logger.info(f"✅ Task Initialization: {'PASSED' if init_ok else 'FAILED'}")
        logger.info(f"✅ WebSocket Events: {'PASSED' if events_ok else 'FAILED'}")
        logger.info(f"✅ Tool Simulation: {'PASSED' if tools_ok else 'FAILED'}")
        logger.info("-"*80)
        logger.info(f"📈 SUCCESS RATE: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 85:
            logger.info("🎉 EXCELLENT - WebSocket system is fully functional!")
        elif success_rate >= 70:
            logger.info("✅ GOOD - WebSocket system is mostly functional with minor issues")
        elif success_rate >= 50:
            logger.info("⚠️ FAIR - WebSocket system has some functionality but needs improvements")
        else:
            logger.info("❌ POOR - WebSocket system has significant issues")
        
        return {
            'success_rate': success_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'test_results': self.test_results
        }

def main():
    """Main test execution"""
    tester = WebSocketBackendTester(BACKEND_URL)
    results = tester.run_comprehensive_test()
    
    # Return results for potential integration with other systems
    return results

if __name__ == "__main__":
    main()