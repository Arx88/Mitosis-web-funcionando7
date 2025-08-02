#!/usr/bin/env python3
"""
COMPREHENSIVE MITOSIS PLAN GENERATION FLOW TESTING
Testing the complete flow from frontend to backend focusing on the reported issue:

PROBLEM REPORTED:
- User creates task from frontend but action plan is not generated or visible
- Backend works perfectly - logs show plan generated correctly with 4 steps
- Endpoints /api/agent/chat and /api/agent/generate-plan return correct responses when tested directly
- Plan is saved successfully in MongoDB
- Problem seems to be in frontend-backend communication or frontend rendering logic

TESTING OBJECTIVES:
1. Test complete flow from frontend to backend comprehensively
2. Verify specifically the /api/agent/generate-plan endpoint with different payloads
3. Simulate exact flow that frontend makes when user creates a task
4. Verify response that frontend is receiving matches expectations
5. Identify specifically where disconnection is between backend (working) and frontend (not showing plans)
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://f9748e49-9c96-49dd-bee2-60b8cfdb3f15.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisPlanGenerationFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://f9748e49-9c96-49dd-bee2-60b8cfdb3f15.preview.emergentagent.com'
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
    
    def test_exact_user_scenario(self) -> bool:
        """Test 1: Exact User Scenario - 'Genera un informe sobre la IA en 2025'"""
        try:
            # Test the exact message mentioned in the review request
            test_message = "Genera un informe sobre la IA en 2025"
            
            payload = {
                "message": test_message
            }
            
            print(f"\n🎯 Testing exact user scenario: {test_message}")
            
            # Test /api/agent/chat endpoint first (as frontend would do)
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required response fields that frontend expects
                response_text = data.get('response', '')
                task_id = data.get('task_id', '')
                memory_used = data.get('memory_used', False)
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                
                # Store task_id for later tests
                if task_id:
                    self.task_id = task_id
                
                # Verify plan structure matches what frontend expects
                plan_valid = False
                if isinstance(plan, list) and len(plan) >= 4:  # Review mentioned 4 steps
                    plan_valid = True
                    for step in plan:
                        if not isinstance(step, dict) or not all(key in step for key in ['title', 'description', 'tool']):
                            plan_valid = False
                            break
                
                if response_text and task_id and memory_used and plan_valid:
                    self.log_test("Exact User Scenario - Chat Endpoint", True, 
                                f"Chat successful - Task ID: {task_id}, Plan steps: {len(plan)}, Enhanced title: {enhanced_title}")
                    return True
                else:
                    self.log_test("Exact User Scenario - Chat Endpoint", False, 
                                f"Incomplete response - Response: {bool(response_text)}, Task ID: {bool(task_id)}, Memory: {memory_used}, Plan valid: {plan_valid}", data)
                    return False
            else:
                self.log_test("Exact User Scenario - Chat Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Exact User Scenario - Chat Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_generate_plan_endpoint_directly(self) -> bool:
        """Test 2: Direct Generate Plan Endpoint Testing"""
        try:
            # Test the /api/agent/generate-plan endpoint directly
            test_message = "Genera un informe sobre la IA en 2025"
            
            # CRITICAL FIX: Use task_title instead of message for generate-plan endpoint
            payload = {
                "task_title": test_message  # Changed from "message" to "task_title"
            }
            
            print(f"\n🔍 Testing generate-plan endpoint directly: {test_message}")
            print(f"   Using payload: {payload}")
            
            response = self.session.post(f"{API_BASE}/agent/generate-plan", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check plan structure
                plan = data.get('plan', [])
                task_id = data.get('task_id', '')
                enhanced_title = data.get('enhanced_title', '')
                task_type = data.get('task_type', '')
                complexity = data.get('complexity', '')
                estimated_time = data.get('estimated_total_time', '')
                success = data.get('success', False)
                
                # Verify plan has exactly 4 steps as mentioned in review
                if isinstance(plan, list) and len(plan) >= 4:
                    # Validate each step structure
                    valid_steps = True
                    for i, step in enumerate(plan):
                        if not isinstance(step, dict):
                            valid_steps = False
                            break
                        required_fields = ['title', 'description', 'tool']
                        if not all(field in step for field in required_fields):
                            valid_steps = False
                            break
                    
                    if valid_steps and enhanced_title and success:
                        self.log_test("Generate Plan Endpoint Direct", True, 
                                    f"Plan generated correctly - {len(plan)} steps, type: {task_type}, complexity: {complexity}, success: {success}")
                        
                        # Store task_id for later tests
                        if not self.task_id:
                            self.task_id = task_id or f"plan-{int(time.time())}"
                        return True
                    else:
                        self.log_test("Generate Plan Endpoint Direct", False, 
                                    f"Invalid plan structure - valid_steps: {valid_steps}, title: {bool(enhanced_title)}, success: {success}", data)
                        return False
                else:
                    self.log_test("Generate Plan Endpoint Direct", False, 
                                f"Plan is not a list or has wrong number of steps - type: {type(plan)}, length: {len(plan) if isinstance(plan, list) else 'N/A'}", data)
                    return False
            else:
                self.log_test("Generate Plan Endpoint Direct", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Generate Plan Endpoint Direct", False, f"Exception: {str(e)}")
            return False
    
    def test_frontend_payload_variations(self) -> bool:
        """Test 3: Frontend Payload Variations"""
        try:
            # Test different payload formats that frontend might send
            test_scenarios = [
                {
                    "name": "Standard Frontend Payload (task_title)",
                    "payload": {"task_title": "Genera un informe sobre la IA en 2025"}
                },
                {
                    "name": "Frontend with Additional Fields",
                    "payload": {
                        "task_title": "Genera un informe sobre la IA en 2025",
                        "user_id": "test_user",
                        "session_id": "test_session"
                    }
                },
                {
                    "name": "Frontend Nueva Tarea Flow",
                    "payload": {
                        "task_title": "Genera un informe sobre la IA en 2025",
                        "task_type": "nueva_tarea"
                    }
                },
                {
                    "name": "WRONG: Frontend using 'message' field",
                    "payload": {"message": "Genera un informe sobre la IA en 2025"}
                }
            ]
            
            successful_scenarios = 0
            
            for scenario in test_scenarios:
                print(f"\n   Testing: {scenario['name']}")
                
                response = self.session.post(f"{API_BASE}/agent/generate-plan", 
                                           json=scenario['payload'], timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    plan = data.get('plan', [])
                    
                    if isinstance(plan, list) and len(plan) >= 4:
                        successful_scenarios += 1
                        print(f"      ✅ Success - {len(plan)} steps generated")
                    else:
                        print(f"      ❌ Failed - Invalid plan: {type(plan)}, length: {len(plan) if isinstance(plan, list) else 'N/A'}")
                else:
                    print(f"      ❌ Failed - HTTP {response.status_code}: {response.text[:100]}")
            
            # We expect 3/4 to succeed (the 'message' field one should fail)
            expected_success = 3
            if successful_scenarios >= expected_success:
                self.log_test("Frontend Payload Variations", True, 
                            f"Expected scenarios successful: {successful_scenarios}/{len(test_scenarios)} (expected {expected_success}+)")
                return True
            else:
                self.log_test("Frontend Payload Variations", False, 
                            f"Only {successful_scenarios}/{len(test_scenarios)} payload variations successful (expected {expected_success}+)")
                return False
                
        except Exception as e:
            self.log_test("Frontend Payload Variations", False, f"Exception: {str(e)}")
            return False
    
    def test_mongodb_plan_persistence(self) -> bool:
        """Test 4: MongoDB Plan Persistence Verification"""
        if not self.task_id:
            self.log_test("MongoDB Plan Persistence", False, "No task_id available for persistence test")
            return False
            
        try:
            # Wait a moment for plan to be saved
            time.sleep(2)
            
            # Try to retrieve the task from backend to verify it was saved
            # We'll use a backend endpoint that should retrieve from MongoDB
            response = self.session.get(f"{API_BASE}/agent/task/{self.task_id}/status", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                task_id = data.get('task_id', '')
                status = data.get('status', '')
                steps = data.get('steps', [])
                metadata = data.get('metadata', {})
                
                if task_id == self.task_id and steps and len(steps) >= 4:
                    self.log_test("MongoDB Plan Persistence", True, 
                                f"Plan persisted correctly - Task ID: {task_id}, Status: {status}, Steps: {len(steps)}")
                    return True
                else:
                    self.log_test("MongoDB Plan Persistence", False, 
                                f"Plan not properly persisted - Task ID match: {task_id == self.task_id}, Steps: {len(steps)}", data)
                    return False
            else:
                # Try alternative endpoint to check persistence
                response = self.session.get(f"{API_BASE}/agent/get-task-plan/{self.task_id}", timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    plan = data.get('plan', [])
                    
                    if plan and len(plan) >= 4:
                        self.log_test("MongoDB Plan Persistence", True, 
                                    f"Plan persisted correctly (alternative check) - Steps: {len(plan)}")
                        return True
                    else:
                        self.log_test("MongoDB Plan Persistence", False, 
                                    f"Plan not properly persisted - Steps: {len(plan)}", data)
                        return False
                else:
                    self.log_test("MongoDB Plan Persistence", False, 
                                f"Cannot verify persistence - HTTP {response.status_code}")
                    return False
                
        except Exception as e:
            self.log_test("MongoDB Plan Persistence", False, f"Exception: {str(e)}")
            return False
    
    def test_response_format_compatibility(self) -> bool:
        """Test 5: Response Format Compatibility with Frontend"""
        try:
            # Test that response format matches exactly what frontend expects
            test_message = "Genera un informe sobre la IA en 2025"
            
            payload = {
                "message": test_message
            }
            
            print(f"\n🔍 Testing response format compatibility")
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check all fields that frontend expects
                expected_fields = {
                    'response': str,
                    'task_id': str,
                    'memory_used': bool,
                    'plan': list,
                    'enhanced_title': str,
                    'timestamp': str
                }
                
                missing_fields = []
                wrong_types = []
                
                for field, expected_type in expected_fields.items():
                    if field not in data:
                        missing_fields.append(field)
                    elif not isinstance(data[field], expected_type):
                        wrong_types.append(f"{field} (expected {expected_type.__name__}, got {type(data[field]).__name__})")
                
                # Check plan structure specifically
                plan = data.get('plan', [])
                plan_structure_valid = True
                if isinstance(plan, list) and len(plan) > 0:
                    for step in plan:
                        if not isinstance(step, dict):
                            plan_structure_valid = False
                            break
                        required_step_fields = ['title', 'description', 'tool']
                        if not all(field in step for field in required_step_fields):
                            plan_structure_valid = False
                            break
                else:
                    plan_structure_valid = False
                
                if not missing_fields and not wrong_types and plan_structure_valid:
                    self.log_test("Response Format Compatibility", True, 
                                f"Response format fully compatible - All fields present with correct types, plan structure valid")
                    return True
                else:
                    issues = []
                    if missing_fields:
                        issues.append(f"Missing fields: {missing_fields}")
                    if wrong_types:
                        issues.append(f"Wrong types: {wrong_types}")
                    if not plan_structure_valid:
                        issues.append("Invalid plan structure")
                    
                    self.log_test("Response Format Compatibility", False, 
                                f"Response format issues - {'; '.join(issues)}", data)
                    return False
            else:
                self.log_test("Response Format Compatibility", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Response Format Compatibility", False, f"Exception: {str(e)}")
            return False
    
    def test_cors_and_headers(self) -> bool:
        """Test 6: CORS and Headers Configuration"""
        try:
            # Test CORS configuration with frontend origin
            test_message = "Genera un informe sobre la IA en 2025"
            
            payload = {
                "task_title": test_message  # Use correct field for generate-plan endpoint
            }
            
            print(f"\n🔍 Testing CORS and headers configuration")
            
            # Test with Origin header (as frontend would send)
            response = self.session.post(f"{API_BASE}/agent/generate-plan", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                # Check CORS headers in response
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                # Check if CORS is properly configured
                cors_configured = (
                    cors_headers['Access-Control-Allow-Origin'] in ['*', 'https://f9748e49-9c96-49dd-bee2-60b8cfdb3f15.preview.emergentagent.com'] or
                    cors_headers['Access-Control-Allow-Origin'] is not None
                )
                
                if cors_configured:
                    self.log_test("CORS and Headers", True, 
                                f"CORS properly configured - Origin: {cors_headers['Access-Control-Allow-Origin']}")
                    return True
                else:
                    self.log_test("CORS and Headers", False, 
                                f"CORS not properly configured - Headers: {cors_headers}")
                    return False
            else:
                self.log_test("CORS and Headers", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("CORS and Headers", False, f"Exception: {str(e)}")
            return False
    
    def test_api_consistency_issue(self) -> bool:
        """Test 8: API Consistency Issue - Different field requirements"""
        try:
            print(f"\n🔍 Testing API consistency between chat and generate-plan endpoints")
            
            test_message = "Genera un informe sobre la IA en 2025"
            
            # Test 1: Chat endpoint with 'message' field (should work)
            chat_payload = {"message": test_message}
            chat_response = self.session.post(f"{API_BASE}/agent/chat", 
                                            json=chat_payload, timeout=30)
            
            chat_works = chat_response.status_code == 200
            
            # Test 2: Generate-plan endpoint with 'message' field (should fail)
            plan_payload_wrong = {"message": test_message}
            plan_response_wrong = self.session.post(f"{API_BASE}/agent/generate-plan", 
                                                  json=plan_payload_wrong, timeout=30)
            
            plan_fails_with_message = plan_response_wrong.status_code == 400
            
            # Test 3: Generate-plan endpoint with 'task_title' field (should work)
            plan_payload_correct = {"task_title": test_message}
            plan_response_correct = self.session.post(f"{API_BASE}/agent/generate-plan", 
                                                    json=plan_payload_correct, timeout=30)
            
            plan_works_with_task_title = plan_response_correct.status_code == 200
            
            # Analyze the inconsistency
            inconsistency_detected = chat_works and plan_fails_with_message and plan_works_with_task_title
            
            if inconsistency_detected:
                self.log_test("API Consistency Issue", False, 
                            f"CRITICAL API INCONSISTENCY DETECTED: Chat endpoint uses 'message' field, Generate-plan endpoint uses 'task_title' field. This causes frontend-backend communication issues.")
                
                # Log detailed findings
                print(f"   📊 DETAILED ANALYSIS:")
                print(f"      ✅ /api/agent/chat with 'message': {chat_works}")
                print(f"      ❌ /api/agent/generate-plan with 'message': {plan_fails_with_message} (returns 400)")
                print(f"      ✅ /api/agent/generate-plan with 'task_title': {plan_works_with_task_title}")
                print(f"   🎯 ROOT CAUSE: Frontend likely sends 'message' to generate-plan endpoint but it expects 'task_title'")
                
                return False
            else:
                self.log_test("API Consistency Issue", True, 
                            f"API endpoints are consistent - no field requirement mismatch detected")
                return True
                
        except Exception as e:
            self.log_test("API Consistency Issue", False, f"Exception: {str(e)}")
            return False
    def test_complete_frontend_simulation(self) -> bool:
        """Test 9: Complete Frontend Flow Simulation"""
        try:
            print(f"\n🔄 Simulating complete frontend flow")
            
            # Simulate the exact sequence frontend would follow
            test_message = "Genera un informe sobre la IA en 2025"
            
            # Step 1: User creates task (frontend calls chat endpoint)
            chat_payload = {"message": test_message}
            chat_response = self.session.post(f"{API_BASE}/agent/chat", 
                                            json=chat_payload, timeout=45)
            
            if chat_response.status_code != 200:
                self.log_test("Complete Frontend Simulation", False, 
                            f"Step 1 failed - Chat endpoint returned HTTP {chat_response.status_code}")
                return False
            
            chat_data = chat_response.json()
            simulation_task_id = chat_data.get('task_id', '')
            plan = chat_data.get('plan', [])
            
            if not simulation_task_id or not plan:
                self.log_test("Complete Frontend Simulation", False, 
                            f"Step 1 failed - No task_id or plan returned")
                return False
            
            # Step 2: Frontend would display the plan (check if plan is displayable)
            plan_displayable = True
            if not isinstance(plan, list) or len(plan) < 4:
                plan_displayable = False
            else:
                for step in plan:
                    if not isinstance(step, dict) or not all(key in step for key in ['title', 'description']):
                        plan_displayable = False
                        break
            
            if not plan_displayable:
                self.log_test("Complete Frontend Simulation", False, 
                            f"Step 2 failed - Plan not displayable: {type(plan)}, length: {len(plan) if isinstance(plan, list) else 'N/A'}")
                return False
            
            # Step 3: Frontend would monitor task progress
            time.sleep(2)
            status_response = self.session.get(f"{API_BASE}/agent/task/{simulation_task_id}/status", timeout=15)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                task_status = status_data.get('status', '')
                
                # Step 4: Check if plan steps are accessible
                steps = status_data.get('steps', [])
                steps_accessible = len(steps) >= 4
                
                if steps_accessible:
                    self.log_test("Complete Frontend Simulation", True, 
                                f"Complete frontend flow successful - Task: {simulation_task_id}, Status: {task_status}, Steps: {len(steps)}")
                    return True
                else:
                    self.log_test("Complete Frontend Simulation", False, 
                                f"Step 4 failed - Steps not accessible: {len(steps)}")
                    return False
            else:
                self.log_test("Complete Frontend Simulation", False, 
                            f"Step 3 failed - Status check returned HTTP {status_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Complete Frontend Simulation", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all plan generation flow tests"""
        print("🧪 STARTING COMPREHENSIVE MITOSIS PLAN GENERATION FLOW TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Identifying disconnection between backend (working) and frontend (not showing plans)")
        print("=" * 80)
        
        # Test sequence focused on plan generation flow
        tests = [
            ("Exact User Scenario", self.test_exact_user_scenario),
            ("Generate Plan Endpoint Direct", self.test_generate_plan_endpoint_directly),
            ("Frontend Payload Variations", self.test_frontend_payload_variations),
            ("MongoDB Plan Persistence", self.test_mongodb_plan_persistence),
            ("Response Format Compatibility", self.test_response_format_compatibility),
            ("CORS and Headers", self.test_cors_and_headers),
            ("API Consistency Issue", self.test_api_consistency_issue),
            ("Complete Frontend Simulation", self.test_complete_frontend_simulation)
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
        print("🎯 PLAN GENERATION FLOW TEST RESULTS SUMMARY")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ EXCELLENT - Plan generation flow working correctly"
        elif success_rate >= 70:
            overall_status = "⚠️ GOOD - Plan generation mostly working with minor issues"
        elif success_rate >= 50:
            overall_status = "⚠️ PARTIAL - Plan generation has significant issues"
        else:
            overall_status = "❌ CRITICAL - Major issues with plan generation flow"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for plan generation
        critical_tests = ["Exact User Scenario", "Generate Plan Endpoint Direct", "Response Format Compatibility", "API Consistency Issue", "Complete Frontend Simulation"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL PLAN GENERATION FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical plan generation functionality is working")
        else:
            print("   ❌ Some critical plan generation functionality is not working")
        
        # Specific analysis for the reported issue
        print(f"\n🔍 SPECIFIC ISSUE ANALYSIS:")
        
        # Check if backend is generating plans correctly
        backend_plan_generation = any(result['success'] for result in self.test_results 
                                    if result['test_name'] in ["Exact User Scenario", "Generate Plan Endpoint Direct"])
        
        # Check if response format is compatible with frontend
        frontend_compatibility = any(result['success'] for result in self.test_results 
                                   if result['test_name'] == "Response Format Compatibility")
        
        # Check if MongoDB persistence is working
        mongodb_persistence = any(result['success'] for result in self.test_results 
                                if result['test_name'] == "MongoDB Plan Persistence")
        
        print(f"   Backend Plan Generation: {'✅ WORKING' if backend_plan_generation else '❌ FAILING'}")
        print(f"   Frontend Compatibility: {'✅ WORKING' if frontend_compatibility else '❌ FAILING'}")
        print(f"   MongoDB Persistence: {'✅ WORKING' if mongodb_persistence else '❌ FAILING'}")
        
        # Provide specific diagnosis
        if backend_plan_generation and frontend_compatibility and mongodb_persistence:
            diagnosis = "✅ BACKEND IS WORKING CORRECTLY - Issue likely in frontend rendering or state management"
        elif backend_plan_generation and not frontend_compatibility:
            diagnosis = "⚠️ BACKEND WORKING BUT RESPONSE FORMAT INCOMPATIBLE - Frontend expecting different format"
        elif not backend_plan_generation:
            diagnosis = "❌ BACKEND PLAN GENERATION FAILING - Core functionality broken"
        else:
            diagnosis = "⚠️ MIXED RESULTS - Partial functionality working"
        
        print(f"   Diagnosis: {diagnosis}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id,
            'backend_plan_generation': backend_plan_generation,
            'frontend_compatibility': frontend_compatibility,
            'mongodb_persistence': mongodb_persistence,
            'diagnosis': diagnosis
        }

def main():
    """Main testing function"""
    tester = MitosisPlanGenerationFlowTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/backend_plan_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 PLAN GENERATION FLOW TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ PLAN GENERATION FLOW TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)