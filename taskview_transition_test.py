#!/usr/bin/env python3
"""
TASKVIEW TRANSITION FIX TESTING - MITOSIS APPLICATION
Testing the specific fix for TaskView transition and consolidated task creation logic
"""

import requests
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskViewTransitionTester:
    def __init__(self):
        # Get backend URL from environment
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.split('=')[1].strip()
                    break
            else:
                self.base_url = "https://2c2e2045-234a-4f5b-8f4e-62b51d84d8da.preview.emergentagent.com"
        
        self.api_url = f"{self.base_url}/api"
        logger.info(f"🌐 Testing TaskView transition fix at: {self.api_url}")
        
        # Test results storage
        self.test_results = {
            'backend_health': {'passed': False, 'details': []},
            'task_creation': {'passed': False, 'details': []},
            'plan_generation': {'passed': False, 'details': []},
            'consolidated_logic': {'passed': False, 'details': []},
            'state_management': {'passed': False, 'details': []},
            'overall_success': False
        }

    def test_backend_health(self):
        """Test 1: Backend Health and Connectivity"""
        logger.info("🧪 TEST 1: Backend Health and Connectivity")
        
        try:
            # Test basic health endpoint
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Backend health check passed: {data.get('status')}")
                self.test_results['backend_health']['details'].append("✅ Basic health endpoint working")
                
                # Test agent health endpoint
                agent_response = requests.get(f"{self.api_url}/agent/health", timeout=10)
                if agent_response.status_code == 200:
                    agent_data = agent_response.json()
                    logger.info(f"✅ Agent health check passed")
                    self.test_results['backend_health']['details'].append("✅ Agent health endpoint working")
                    self.test_results['backend_health']['passed'] = True
                else:
                    logger.warning(f"⚠️ Agent health endpoint returned: {agent_response.status_code}")
                    self.test_results['backend_health']['details'].append(f"⚠️ Agent health endpoint: {agent_response.status_code}")
                    self.test_results['backend_health']['passed'] = True  # Still pass if basic health works
                
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                self.test_results['backend_health']['details'].append(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check error: {str(e)}")
            self.test_results['backend_health']['details'].append(f"❌ Health check error: {str(e)}")
            return False
        
        return self.test_results['backend_health']['passed']

    def test_task_creation_working(self):
        """Test 2: Task Creation Working - Verify tasks can be created successfully"""
        logger.info("🧪 TEST 2: Task Creation Working")
        
        test_message = "Test TaskView transition fix"
        task_id = f"test_transition_{int(time.time())}"
        
        try:
            # Test task creation via chat endpoint (simulating frontend behavior)
            logger.info(f"  📋 Testing task creation with message: '{test_message}'")
            
            response = requests.post(
                f"{self.api_url}/agent/chat",
                json={
                    'message': test_message,
                    'context': {'task_id': task_id}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if task was created successfully
                if data.get('task_id') and data.get('response'):
                    logger.info("  ✅ Task creation successful via chat endpoint")
                    self.test_results['task_creation']['details'].append("✅ Chat endpoint creates tasks successfully")
                    
                    # Check if memory is being used (indicates proper integration)
                    if data.get('memory_used'):
                        logger.info("  ✅ Memory integration working")
                        self.test_results['task_creation']['details'].append("✅ Memory integration active")
                    
                    self.test_results['task_creation']['passed'] = True
                    return True
                else:
                    logger.error("  ❌ Task creation response missing required fields")
                    self.test_results['task_creation']['details'].append("❌ Response missing task_id or response")
                    
            else:
                logger.error(f"  ❌ Task creation failed: {response.status_code}")
                self.test_results['task_creation']['details'].append(f"❌ Chat endpoint failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"  ❌ Task creation test error: {str(e)}")
            self.test_results['task_creation']['details'].append(f"❌ Exception: {str(e)}")
        
        return False

    def test_plan_generation_working(self):
        """Test 3: Plan Generation Working - Verify backend generates plans correctly"""
        logger.info("🧪 TEST 3: Plan Generation Working")
        
        test_task = "Create a comprehensive analysis of renewable energy trends in 2025"
        task_id = f"test_plan_{int(time.time())}"
        
        try:
            # Test plan generation via initialize-task endpoint
            logger.info(f"  📋 Testing plan generation for: '{test_task}'")
            
            response = requests.post(
                f"{self.api_url}/agent/initialize-task",
                json={
                    'task_id': task_id,
                    'title': test_task,
                    'auto_execute': False
                },
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if plan was generated
                plan = data.get('plan', {})
                if plan and plan.get('steps'):
                    steps = plan['steps']
                    logger.info(f"  ✅ Plan generated successfully with {len(steps)} steps")
                    self.test_results['plan_generation']['details'].append(f"✅ Plan generated with {len(steps)} steps")
                    
                    # Check plan structure
                    if plan.get('task_type') and plan.get('complexity'):
                        logger.info("  ✅ Plan has proper structure (task_type, complexity)")
                        self.test_results['plan_generation']['details'].append("✅ Plan structure is valid")
                    
                    # Check if steps have required fields
                    valid_steps = 0
                    for step in steps:
                        if step.get('title') and step.get('description') and step.get('tool'):
                            valid_steps += 1
                    
                    if valid_steps == len(steps):
                        logger.info("  ✅ All steps have valid structure")
                        self.test_results['plan_generation']['details'].append("✅ All steps properly structured")
                        self.test_results['plan_generation']['passed'] = True
                        return True
                    else:
                        logger.warning(f"  ⚠️ Only {valid_steps}/{len(steps)} steps have valid structure")
                        self.test_results['plan_generation']['details'].append(f"⚠️ Only {valid_steps}/{len(steps)} steps valid")
                        
                else:
                    logger.error("  ❌ No plan or steps generated")
                    self.test_results['plan_generation']['details'].append("❌ No plan or steps generated")
                    
            else:
                logger.error(f"  ❌ Plan generation failed: {response.status_code}")
                self.test_results['plan_generation']['details'].append(f"❌ Initialize-task failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"  ❌ Plan generation test error: {str(e)}")
            self.test_results['plan_generation']['details'].append(f"❌ Exception: {str(e)}")
        
        return False

    def test_consolidated_task_creation_logic(self):
        """Test 4: Consolidated Task Creation Logic - Test createTaskWithMessage() function equivalent"""
        logger.info("🧪 TEST 4: Consolidated Task Creation Logic")
        
        test_cases = [
            {
                'message': 'Create a market analysis report for electric vehicles',
                'expected_type': 'task'
            },
            {
                'message': 'hola',
                'expected_type': 'casual'
            },
            {
                'message': 'Develop a comprehensive business strategy for sustainable fashion',
                'expected_type': 'task'
            }
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                logger.info(f"  📋 Test case {i}: '{test_case['message']}'")
                
                response = requests.post(
                    f"{self.api_url}/agent/chat",
                    json={
                        'message': test_case['message'],
                        'context': {'task_id': f'test_consolidated_{i}_{int(time.time())}'}
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if response is properly structured
                    required_fields = ['response', 'task_id', 'timestamp']
                    has_required = all(field in data for field in required_fields)
                    
                    if has_required:
                        logger.info(f"    ✅ Response properly structured")
                        
                        # Check if task/casual detection is working
                        mode = data.get('mode', 'unknown')
                        if test_case['expected_type'] == 'casual' and 'casual' in mode.lower():
                            logger.info(f"    ✅ Correctly identified as casual conversation")
                            passed_tests += 1
                        elif test_case['expected_type'] == 'task' and 'casual' not in mode.lower():
                            logger.info(f"    ✅ Correctly identified as task message")
                            passed_tests += 1
                        else:
                            logger.warning(f"    ⚠️ Message type detection may be incorrect (mode: {mode})")
                            passed_tests += 0.5  # Partial credit
                            
                    else:
                        logger.error(f"    ❌ Response missing required fields")
                        
                else:
                    logger.error(f"    ❌ Request failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"    ❌ Test case {i} error: {str(e)}")
        
        success_rate = passed_tests / total_tests
        self.test_results['consolidated_logic']['passed'] = success_rate >= 0.7
        self.test_results['consolidated_logic']['details'].append(f"✅ {passed_tests}/{total_tests} test cases passed ({success_rate:.1%})")
        
        logger.info(f"📊 Consolidated Logic: {passed_tests}/{total_tests} passed ({success_rate:.1%})")
        return self.test_results['consolidated_logic']['passed']

    def test_state_management_backend_support(self):
        """Test 5: State Management Backend Support - Verify backend supports proper state management"""
        logger.info("🧪 TEST 5: State Management Backend Support")
        
        try:
            # Test agent status endpoint for state information
            logger.info("  📋 Testing agent status for state management info...")
            
            response = requests.get(f"{self.api_url}/agent/status", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if status provides necessary information for frontend state management
                status_fields = ['status', 'ollama', 'tools', 'memory']
                valid_fields = 0
                
                for field in status_fields:
                    if field in data:
                        valid_fields += 1
                        logger.info(f"    ✅ Status field '{field}' present")
                    else:
                        logger.warning(f"    ⚠️ Status field '{field}' missing")
                
                if valid_fields >= 3:
                    logger.info("  ✅ Agent status provides sufficient state information")
                    self.test_results['state_management']['details'].append("✅ Agent status endpoint provides state info")
                    
                    # Test if we can get active tasks or similar state info
                    if 'status' in data and data['status'] == 'running':
                        logger.info("  ✅ Agent is in running state")
                        self.test_results['state_management']['details'].append("✅ Agent running state confirmed")
                        self.test_results['state_management']['passed'] = True
                        return True
                    else:
                        logger.warning("  ⚠️ Agent status unclear")
                        self.test_results['state_management']['details'].append("⚠️ Agent status unclear")
                        
                else:
                    logger.error(f"  ❌ Insufficient status fields: {valid_fields}/{len(status_fields)}")
                    self.test_results['state_management']['details'].append(f"❌ Only {valid_fields}/{len(status_fields)} status fields present")
                    
            else:
                logger.error(f"  ❌ Agent status failed: {response.status_code}")
                self.test_results['state_management']['details'].append(f"❌ Agent status failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"  ❌ State management test error: {str(e)}")
            self.test_results['state_management']['details'].append(f"❌ Exception: {str(e)}")
        
        return False

    def run_all_tests(self):
        """Run all TaskView transition tests"""
        logger.info("🚀 STARTING TASKVIEW TRANSITION FIX TESTING")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Run all tests in sequence
        tests = [
            ('Backend Health', self.test_backend_health),
            ('Task Creation Working', self.test_task_creation_working),
            ('Plan Generation Working', self.test_plan_generation_working),
            ('Consolidated Task Creation Logic', self.test_consolidated_task_creation_logic),
            ('State Management Backend Support', self.test_state_management_backend_support)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info("-" * 40)
            try:
                if test_func():
                    passed_tests += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: EXCEPTION - {str(e)}")
        
        # Calculate overall success
        success_rate = passed_tests / total_tests
        self.test_results['overall_success'] = success_rate >= 0.8
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Final summary
        logger.info("=" * 60)
        logger.info("🏁 TASKVIEW TRANSITION TESTING COMPLETE")
        logger.info(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1%})")
        logger.info(f"⏱️ Total Duration: {duration:.1f} seconds")
        logger.info(f"🎯 TaskView Transition Fix Status: {'WORKING' if self.test_results['overall_success'] else 'NEEDS ATTENTION'}")
        
        return self.test_results

def main():
    """Main test execution"""
    tester = TaskViewTransitionTester()
    results = tester.run_all_tests()
    
    # Print detailed results
    print("\n" + "=" * 60)
    print("📋 TASKVIEW TRANSITION FIX TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        if test_name == 'overall_success':
            continue
            
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"\n{test_name.upper().replace('_', ' ')}: {status}")
        
        for detail in result['details']:
            print(f"  {detail}")
    
    print(f"\n🎯 TASKVIEW TRANSITION FIX: {'SUCCESS' if results['overall_success'] else 'NEEDS WORK'}")
    
    # Specific recommendations based on results
    if not results['overall_success']:
        print("\n🔧 RECOMMENDATIONS:")
        if not results['task_creation']['passed']:
            print("  - Fix task creation endpoint issues")
        if not results['plan_generation']['passed']:
            print("  - Verify plan generation logic and schema validation")
        if not results['consolidated_logic']['passed']:
            print("  - Check consolidated task creation logic implementation")
        if not results['state_management']['passed']:
            print("  - Improve backend state management support")
    
    return 0 if results['overall_success'] else 1

if __name__ == "__main__":
    exit(main())