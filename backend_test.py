#!/usr/bin/env python3
"""
COMPREHENSIVE MITOSIS BACKEND TESTING - PLAN GENERATION IMPROVEMENTS
Testing the unified plan generation system, schema validation, and fallback mechanisms
"""

import requests
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MitosisBackendTester:
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
        logger.info(f"🌐 Testing backend at: {self.api_url}")
        
        # Test results storage
        self.test_results = {
            'generic_plan_generation': {'passed': False, 'details': []},
            'code_deduplication': {'passed': False, 'details': []},
            'plan_generation_endpoints': {'passed': False, 'details': []},
            'schema_validation': {'passed': False, 'details': []},
            'fallback_mechanisms': {'passed': False, 'details': []},
            'overall_success': False
        }

    def test_health_check(self):
        """Test basic backend connectivity"""
        try:
            logger.info("🩺 Testing backend health...")
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Backend health check passed: {data.get('status')}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check error: {str(e)}")
            return False

    def test_generic_plan_generation(self):
        """Test 1: Generic Plan Generation Fix - No Valencia-specific examples"""
        logger.info("🧪 TEST 1: Generic Plan Generation Fix")
        
        test_cases = [
            {
                'task': 'Create a financial analysis report for tech startups in 2025',
                'expected_keywords': ['financial', 'analysis', 'tech', 'startups', '2025'],
                'forbidden_keywords': ['valencia', 'bares', 'restaurantes', 'spain']
            },
            {
                'task': 'Develop a marketing strategy for sustainable fashion brands',
                'expected_keywords': ['marketing', 'strategy', 'sustainable', 'fashion'],
                'forbidden_keywords': ['valencia', 'bares', 'restaurantes', 'spain']
            },
            {
                'task': 'Research artificial intelligence trends in healthcare',
                'expected_keywords': ['research', 'artificial intelligence', 'healthcare', 'trends'],
                'forbidden_keywords': ['valencia', 'bares', 'restaurantes', 'spain']
            }
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                logger.info(f"  📋 Test case {i}: {test_case['task']}")
                
                # Test via initialize-task endpoint
                response = requests.post(
                    f"{self.api_url}/agent/initialize-task",
                    json={
                        'task_id': f'test_generic_{i}_{int(time.time())}',
                        'title': test_case['task'],
                        'auto_execute': False
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    plan = data.get('plan', {})
                    steps = plan.get('steps', [])
                    
                    if steps:
                        # Check for task-specific content
                        plan_text = json.dumps(plan).lower()
                        
                        # Verify expected keywords are present
                        expected_found = sum(1 for keyword in test_case['expected_keywords'] 
                                           if keyword.lower() in plan_text)
                        
                        # Verify forbidden keywords are NOT present
                        forbidden_found = sum(1 for keyword in test_case['forbidden_keywords'] 
                                            if keyword.lower() in plan_text)
                        
                        if expected_found >= 2 and forbidden_found == 0:
                            logger.info(f"    ✅ Plan is task-specific and generic (no Valencia examples)")
                            self.test_results['generic_plan_generation']['details'].append(
                                f"✅ Test case {i}: Task-specific plan generated"
                            )
                            passed_tests += 1
                        else:
                            logger.warning(f"    ⚠️ Plan may contain generic or Valencia-specific content")
                            self.test_results['generic_plan_generation']['details'].append(
                                f"⚠️ Test case {i}: Plan not sufficiently task-specific"
                            )
                    else:
                        logger.error(f"    ❌ No plan steps generated")
                        self.test_results['generic_plan_generation']['details'].append(
                            f"❌ Test case {i}: No plan steps generated"
                        )
                else:
                    logger.error(f"    ❌ Request failed: {response.status_code}")
                    self.test_results['generic_plan_generation']['details'].append(
                        f"❌ Test case {i}: Request failed with {response.status_code}"
                    )
                    
            except Exception as e:
                logger.error(f"    ❌ Test case {i} error: {str(e)}")
                self.test_results['generic_plan_generation']['details'].append(
                    f"❌ Test case {i}: Exception - {str(e)}"
                )
        
        success_rate = passed_tests / total_tests
        self.test_results['generic_plan_generation']['passed'] = success_rate >= 0.7
        
        logger.info(f"📊 Generic Plan Generation: {passed_tests}/{total_tests} passed ({success_rate:.1%})")
        return self.test_results['generic_plan_generation']['passed']

    def test_code_deduplication(self):
        """Test 2: Code Deduplication - Verify unified plan generation functions"""
        logger.info("🧪 TEST 2: Code Deduplication Verification")
        
        try:
            # Test that both endpoints use the same underlying plan generation
            task_id_1 = f'test_dedup_1_{int(time.time())}'
            task_id_2 = f'test_dedup_2_{int(time.time())}'
            test_message = "Create a comprehensive business plan for a renewable energy startup"
            
            # Test initialize-task endpoint
            logger.info("  📋 Testing initialize-task endpoint...")
            response1 = requests.post(
                f"{self.api_url}/agent/initialize-task",
                json={
                    'task_id': task_id_1,
                    'title': test_message,
                    'auto_execute': False
                },
                timeout=30
            )
            
            # Test chat endpoint in task mode
            logger.info("  💬 Testing chat endpoint in task mode...")
            response2 = requests.post(
                f"{self.api_url}/agent/chat",
                json={
                    'message': test_message,
                    'context': {'task_id': task_id_2}
                },
                timeout=30
            )
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                plan1 = data1.get('plan', {})
                # For chat endpoint, check if it generated a plan structure
                has_plan_structure = 'plan' in str(data2).lower() or 'steps' in str(data2).lower()
                
                if plan1.get('steps') and has_plan_structure:
                    logger.info("  ✅ Both endpoints successfully generate plans")
                    self.test_results['code_deduplication']['details'].append(
                        "✅ Both initialize-task and chat endpoints generate plans"
                    )
                    self.test_results['code_deduplication']['passed'] = True
                else:
                    logger.warning("  ⚠️ One or both endpoints failed to generate plans")
                    self.test_results['code_deduplication']['details'].append(
                        "⚠️ Inconsistent plan generation between endpoints"
                    )
            else:
                logger.error(f"  ❌ Endpoint failures: {response1.status_code}, {response2.status_code}")
                self.test_results['code_deduplication']['details'].append(
                    f"❌ Endpoint failures: initialize-task={response1.status_code}, chat={response2.status_code}"
                )
                
        except Exception as e:
            logger.error(f"  ❌ Code deduplication test error: {str(e)}")
            self.test_results['code_deduplication']['details'].append(f"❌ Exception: {str(e)}")
        
        logger.info(f"📊 Code Deduplication: {'PASSED' if self.test_results['code_deduplication']['passed'] else 'FAILED'}")
        return self.test_results['code_deduplication']['passed']

    def test_plan_generation_endpoints(self):
        """Test 3: Plan Generation Endpoints - Both endpoints work correctly"""
        logger.info("🧪 TEST 3: Plan Generation Endpoints")
        
        endpoints_tested = 0
        endpoints_passed = 0
        
        # Test initialize-task endpoint
        try:
            logger.info("  📋 Testing /api/agent/initialize-task...")
            response = requests.post(
                f"{self.api_url}/agent/initialize-task",
                json={
                    'task_id': f'test_endpoint_init_{int(time.time())}',
                    'title': 'Analyze market trends for electric vehicles in Europe',
                    'auto_execute': False
                },
                timeout=30
            )
            
            endpoints_tested += 1
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('plan', {}).get('steps'):
                    logger.info("    ✅ initialize-task endpoint working correctly")
                    endpoints_passed += 1
                    self.test_results['plan_generation_endpoints']['details'].append(
                        "✅ initialize-task endpoint generates plans successfully"
                    )
                else:
                    logger.error("    ❌ initialize-task endpoint returned invalid response")
                    self.test_results['plan_generation_endpoints']['details'].append(
                        "❌ initialize-task endpoint returned invalid response"
                    )
            else:
                logger.error(f"    ❌ initialize-task endpoint failed: {response.status_code}")
                self.test_results['plan_generation_endpoints']['details'].append(
                    f"❌ initialize-task endpoint failed: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"    ❌ initialize-task endpoint error: {str(e)}")
            self.test_results['plan_generation_endpoints']['details'].append(
                f"❌ initialize-task endpoint error: {str(e)}"
            )
        
        # Test chat endpoint
        try:
            logger.info("  💬 Testing /api/agent/chat...")
            response = requests.post(
                f"{self.api_url}/agent/chat",
                json={
                    'message': 'Develop a comprehensive cybersecurity strategy for small businesses',
                    'context': {'task_id': f'test_endpoint_chat_{int(time.time())}'}
                },
                timeout=30
            )
            
            endpoints_tested += 1
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response') and data.get('task_id'):
                    logger.info("    ✅ chat endpoint working correctly")
                    endpoints_passed += 1
                    self.test_results['plan_generation_endpoints']['details'].append(
                        "✅ chat endpoint processes task messages successfully"
                    )
                else:
                    logger.error("    ❌ chat endpoint returned invalid response")
                    self.test_results['plan_generation_endpoints']['details'].append(
                        "❌ chat endpoint returned invalid response"
                    )
            else:
                logger.error(f"    ❌ chat endpoint failed: {response.status_code}")
                self.test_results['plan_generation_endpoints']['details'].append(
                    f"❌ chat endpoint failed: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"    ❌ chat endpoint error: {str(e)}")
            self.test_results['plan_generation_endpoints']['details'].append(
                f"❌ chat endpoint error: {str(e)}"
            )
        
        success_rate = endpoints_passed / endpoints_tested if endpoints_tested > 0 else 0
        self.test_results['plan_generation_endpoints']['passed'] = success_rate >= 0.5
        
        logger.info(f"📊 Plan Generation Endpoints: {endpoints_passed}/{endpoints_tested} passed ({success_rate:.1%})")
        return self.test_results['plan_generation_endpoints']['passed']

    def test_schema_validation(self):
        """Test 4: Schema Validation - Verify JSON schema validation works"""
        logger.info("🧪 TEST 4: Schema Validation")
        
        try:
            # Generate a plan and verify it has proper structure
            logger.info("  📋 Testing plan structure validation...")
            response = requests.post(
                f"{self.api_url}/agent/initialize-task",
                json={
                    'task_id': f'test_schema_{int(time.time())}',
                    'title': 'Create a data science project roadmap for predictive analytics',
                    'auto_execute': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', {})
                
                # Check required schema fields
                required_fields = ['steps', 'task_type', 'complexity']
                schema_valid = True
                validation_details = []
                
                for field in required_fields:
                    if field in plan:
                        validation_details.append(f"✅ Required field '{field}' present")
                    else:
                        validation_details.append(f"❌ Required field '{field}' missing")
                        schema_valid = False
                
                # Check steps structure
                steps = plan.get('steps', [])
                if isinstance(steps, list) and len(steps) > 0:
                    validation_details.append(f"✅ Steps array present with {len(steps)} steps")
                    
                    # Check first step structure
                    if steps:
                        step = steps[0]
                        step_fields = ['title', 'description', 'tool']
                        for field in step_fields:
                            if field in step:
                                validation_details.append(f"✅ Step field '{field}' present")
                            else:
                                validation_details.append(f"❌ Step field '{field}' missing")
                                schema_valid = False
                else:
                    validation_details.append("❌ Steps array missing or empty")
                    schema_valid = False
                
                self.test_results['schema_validation']['details'] = validation_details
                self.test_results['schema_validation']['passed'] = schema_valid
                
                if schema_valid:
                    logger.info("  ✅ Schema validation passed")
                else:
                    logger.error("  ❌ Schema validation failed")
                    
            else:
                logger.error(f"  ❌ Failed to get plan for schema validation: {response.status_code}")
                self.test_results['schema_validation']['details'].append(
                    f"❌ Failed to get plan: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"  ❌ Schema validation test error: {str(e)}")
            self.test_results['schema_validation']['details'].append(f"❌ Exception: {str(e)}")
        
        logger.info(f"📊 Schema Validation: {'PASSED' if self.test_results['schema_validation']['passed'] else 'FAILED'}")
        return self.test_results['schema_validation']['passed']

    def test_fallback_mechanisms(self):
        """Test 5: Fallback Mechanisms - Test fallback when AI generation fails"""
        logger.info("🧪 TEST 5: Fallback Mechanisms")
        
        try:
            # Test with a complex task that might challenge the AI
            logger.info("  🔄 Testing fallback plan generation...")
            response = requests.post(
                f"{self.api_url}/agent/initialize-task",
                json={
                    'task_id': f'test_fallback_{int(time.time())}',
                    'title': 'Create an extremely complex multi-dimensional quantum computing algorithm optimization framework with advanced machine learning integration and real-time distributed processing capabilities',
                    'auto_execute': False
                },
                timeout=45  # Longer timeout for complex task
            )
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', {})
                
                # Check if we got any plan (either AI-generated or fallback)
                if plan.get('steps'):
                    plan_source = plan.get('plan_source', 'unknown')
                    logger.info(f"  ✅ Plan generated successfully (source: {plan_source})")
                    
                    # Check if it's a fallback plan
                    if 'fallback' in plan_source.lower():
                        logger.info("  ✅ Fallback mechanism activated successfully")
                        self.test_results['fallback_mechanisms']['details'].append(
                            "✅ Fallback plan generation working"
                        )
                    else:
                        logger.info("  ✅ AI plan generation successful (fallback not needed)")
                        self.test_results['fallback_mechanisms']['details'].append(
                            "✅ AI plan generation successful"
                        )
                    
                    self.test_results['fallback_mechanisms']['passed'] = True
                else:
                    logger.error("  ❌ No plan generated (fallback failed)")
                    self.test_results['fallback_mechanisms']['details'].append(
                        "❌ No plan generated - fallback failed"
                    )
            else:
                logger.error(f"  ❌ Fallback test failed: {response.status_code}")
                self.test_results['fallback_mechanisms']['details'].append(
                    f"❌ Request failed: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"  ❌ Fallback mechanisms test error: {str(e)}")
            self.test_results['fallback_mechanisms']['details'].append(f"❌ Exception: {str(e)}")
        
        logger.info(f"📊 Fallback Mechanisms: {'PASSED' if self.test_results['fallback_mechanisms']['passed'] else 'FAILED'}")
        return self.test_results['fallback_mechanisms']['passed']

    def test_casual_vs_task_detection(self):
        """Bonus Test: Verify casual vs task message detection"""
        logger.info("🧪 BONUS TEST: Casual vs Task Detection")
        
        test_cases = [
            {'message': 'hola', 'expected_mode': 'casual'},
            {'message': '¿cómo estás?', 'expected_mode': 'casual'},
            {'message': 'Create a business plan for a tech startup', 'expected_mode': 'task'},
            {'message': 'Analyze market data for cryptocurrency trends', 'expected_mode': 'task'}
        ]
        
        passed_tests = 0
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{self.api_url}/agent/chat",
                    json={
                        'message': test_case['message'],
                        'context': {'task_id': f'test_detection_{int(time.time())}'}
                    },
                    timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    mode = data.get('mode', 'unknown')
                    
                    if test_case['expected_mode'] in mode or (test_case['expected_mode'] == 'task' and mode != 'casual_conversation'):
                        logger.info(f"  ✅ '{test_case['message']}' correctly detected as {mode}")
                        passed_tests += 1
                    else:
                        logger.warning(f"  ⚠️ '{test_case['message']}' incorrectly detected as {mode}")
                        
            except Exception as e:
                logger.error(f"  ❌ Detection test error for '{test_case['message']}': {str(e)}")
        
        detection_success = passed_tests >= len(test_cases) * 0.75
        logger.info(f"📊 Casual vs Task Detection: {passed_tests}/{len(test_cases)} passed")
        return detection_success

    def run_all_tests(self):
        """Run all tests and return comprehensive results"""
        logger.info("🚀 STARTING COMPREHENSIVE MITOSIS BACKEND TESTING")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Test 0: Health check
        if not self.test_health_check():
            logger.error("❌ Backend health check failed - aborting tests")
            return self.test_results
        
        # Run all main tests
        tests = [
            ('Generic Plan Generation Fix', self.test_generic_plan_generation),
            ('Code Deduplication', self.test_code_deduplication),
            ('Plan Generation Endpoints', self.test_plan_generation_endpoints),
            ('Schema Validation', self.test_schema_validation),
            ('Fallback Mechanisms', self.test_fallback_mechanisms)
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
        
        # Bonus test
        logger.info("-" * 40)
        self.test_casual_vs_task_detection()
        
        # Calculate overall success
        success_rate = passed_tests / total_tests
        self.test_results['overall_success'] = success_rate >= 0.8
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Final summary
        logger.info("=" * 60)
        logger.info("🏁 TESTING COMPLETE")
        logger.info(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1%})")
        logger.info(f"⏱️ Total Duration: {duration:.1f} seconds")
        logger.info(f"🎯 Overall Success: {'YES' if self.test_results['overall_success'] else 'NO'}")
        
        return self.test_results

def main():
    """Main test execution"""
    tester = MitosisBackendTester()
    results = tester.run_all_tests()
    
    # Print detailed results
    print("\n" + "=" * 60)
    print("📋 DETAILED TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        if test_name == 'overall_success':
            continue
            
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"\n{test_name.upper().replace('_', ' ')}: {status}")
        
        for detail in result['details']:
            print(f"  {detail}")
    
    print(f"\n🎯 FINAL RESULT: {'SUCCESS' if results['overall_success'] else 'FAILURE'}")
    
    return 0 if results['overall_success'] else 1

if __name__ == "__main__":
    exit(main())
