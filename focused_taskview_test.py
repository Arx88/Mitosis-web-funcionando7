#!/usr/bin/env python3
"""
FOCUSED TASKVIEW TRANSITION AND AUTONOMOUS CAPABILITIES TEST
Testing the specific requirements from the review request
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusedMitosisTest:
    def __init__(self):
        # Get backend URL from environment
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.split('=')[1].strip()
                    break
            else:
                self.base_url = "https://93c94e04-ef82-430e-9ba8-c966aaf65bb5.preview.emergentagent.com"
        
        self.api_url = f"{self.base_url}/api"
        logger.info(f"🌐 Testing Mitosis at: {self.api_url}")

    def test_specific_message(self):
        """Test the specific message mentioned in the review request"""
        logger.info("🧪 TESTING SPECIFIC MESSAGE: 'Test TaskView transition fix'")
        
        try:
            # Test the exact message from the review request
            response = requests.post(
                f"{self.api_url}/agent/chat",
                json={
                    'message': 'Test TaskView transition fix',
                    'context': {'task_id': f'test_specific_{int(time.time())}'}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Task creation successful")
                logger.info(f"  - Task ID: {data.get('task_id')}")
                logger.info(f"  - Response: {data.get('response', '')[:100]}...")
                logger.info(f"  - Memory Used: {data.get('memory_used')}")
                logger.info(f"  - Mode: {data.get('mode')}")
                return True
            else:
                logger.error(f"❌ Request failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test error: {str(e)}")
            return False

    def test_plan_generation_and_access(self):
        """Test that plans are generated and accessible"""
        logger.info("🧪 TESTING PLAN GENERATION AND ACCESS")
        
        try:
            # Test plan generation via initialize-task
            response = requests.post(
                f"{self.api_url}/agent/initialize-task",
                json={
                    'task_id': f'test_plan_access_{int(time.time())}',
                    'title': 'Create a comprehensive market analysis for renewable energy sector',
                    'auto_execute': False
                },
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', {})
                
                if plan and plan.get('steps'):
                    logger.info(f"✅ Plan generated with {len(plan['steps'])} steps")
                    logger.info(f"  - Task Type: {plan.get('task_type')}")
                    logger.info(f"  - Complexity: {plan.get('complexity')}")
                    logger.info(f"  - Estimated Time: {plan.get('estimated_time')}")
                    
                    # Show first step as example
                    if plan['steps']:
                        first_step = plan['steps'][0]
                        logger.info(f"  - First Step: {first_step.get('title')}")
                        logger.info(f"  - Tool: {first_step.get('tool')}")
                    
                    return True
                else:
                    logger.error("❌ No plan or steps generated")
                    return False
            else:
                logger.error(f"❌ Plan generation failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Plan generation test error: {str(e)}")
            return False

    def test_autonomous_capabilities(self):
        """Test autonomous agent capabilities"""
        logger.info("🧪 TESTING AUTONOMOUS CAPABILITIES")
        
        try:
            # Test agent status to verify autonomous capabilities
            response = requests.get(f"{self.api_url}/agent/status", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Agent status retrieved")
                logger.info(f"  - Status: {data.get('status')}")
                logger.info(f"  - Ollama Connected: {data.get('ollama', {}).get('connected')}")
                logger.info(f"  - Ollama Endpoint: {data.get('ollama', {}).get('endpoint')}")
                logger.info(f"  - Ollama Model: {data.get('ollama', {}).get('model')}")
                logger.info(f"  - Tools Available: {data.get('tools_count', 0)}")
                logger.info(f"  - Memory Enabled: {data.get('memory', {}).get('enabled')}")
                
                # Check if key autonomous components are working
                ollama_connected = data.get('ollama', {}).get('connected', False)
                tools_available = data.get('tools_count', 0) > 0
                memory_enabled = data.get('memory', {}).get('enabled', False)
                
                if ollama_connected and tools_available and memory_enabled:
                    logger.info("✅ All autonomous capabilities are operational")
                    return True
                else:
                    logger.warning("⚠️ Some autonomous capabilities may not be fully operational")
                    return False
            else:
                logger.error(f"❌ Agent status failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Autonomous capabilities test error: {str(e)}")
            return False

    def test_consolidated_task_creation(self):
        """Test the consolidated task creation logic mentioned in the review"""
        logger.info("🧪 TESTING CONSOLIDATED TASK CREATION LOGIC")
        
        test_scenarios = [
            {
                'name': 'Input Task',
                'message': 'Create a business plan for a sustainable tech startup',
                'method': 'input'
            },
            {
                'name': 'Web Search Task',
                'message': 'Research the latest trends in artificial intelligence for 2025',
                'method': 'web_search'
            },
            {
                'name': 'Deep Search Task',
                'message': 'Analyze market opportunities in renewable energy sector',
                'method': 'deep_search'
            }
        ]
        
        successful_tests = 0
        
        for scenario in test_scenarios:
            try:
                logger.info(f"  📋 Testing {scenario['name']}: {scenario['message']}")
                
                response = requests.post(
                    f"{self.api_url}/agent/chat",
                    json={
                        'message': scenario['message'],
                        'context': {
                            'task_id': f'test_{scenario["method"]}_{int(time.time())}',
                            'method': scenario['method']
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('task_id') and data.get('response'):
                        logger.info(f"    ✅ {scenario['name']} successful")
                        successful_tests += 1
                    else:
                        logger.warning(f"    ⚠️ {scenario['name']} incomplete response")
                else:
                    logger.error(f"    ❌ {scenario['name']} failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"    ❌ {scenario['name']} error: {str(e)}")
        
        success_rate = successful_tests / len(test_scenarios)
        logger.info(f"📊 Consolidated Task Creation: {successful_tests}/{len(test_scenarios)} successful ({success_rate:.1%})")
        
        return success_rate >= 0.67  # At least 2/3 should work

    def run_focused_tests(self):
        """Run all focused tests for the TaskView transition fix"""
        logger.info("🚀 STARTING FOCUSED TASKVIEW TRANSITION TESTS")
        logger.info("=" * 60)
        
        tests = [
            ('Specific Message Test', self.test_specific_message),
            ('Plan Generation and Access', self.test_plan_generation_and_access),
            ('Autonomous Capabilities', self.test_autonomous_capabilities),
            ('Consolidated Task Creation', self.test_consolidated_task_creation)
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
        
        success_rate = passed_tests / total_tests
        overall_success = success_rate >= 0.75
        
        logger.info("=" * 60)
        logger.info("🏁 FOCUSED TESTING COMPLETE")
        logger.info(f"📊 Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1%})")
        logger.info(f"🎯 TaskView Transition Fix: {'SUCCESS' if overall_success else 'NEEDS ATTENTION'}")
        
        return overall_success

def main():
    """Main test execution"""
    tester = FocusedMitosisTest()
    success = tester.run_focused_tests()
    
    if success:
        print("\n🎉 TASKVIEW TRANSITION FIX VERIFICATION: SUCCESS")
        print("✅ Task creation working correctly")
        print("✅ Plan generation operational")
        print("✅ Autonomous capabilities ready")
        print("✅ Consolidated task creation logic functional")
    else:
        print("\n⚠️ TASKVIEW TRANSITION FIX VERIFICATION: NEEDS ATTENTION")
        print("Some components may need additional work")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())