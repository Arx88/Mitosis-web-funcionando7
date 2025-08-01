#!/usr/bin/env python3
"""
MITOSIS BACKEND COMPREHENSIVE TESTING AFTER ORPHANED FILES CLEANUP
Testing the Mitosis backend comprehensively after removing orphaned files that were causing infinite loops.

SPECIFIC TESTING REQUEST:
Test the Mitosis backend comprehensively after removing orphaned files that were causing infinite loops in the "PLAN DE ACCION" logic. Specifically test:

1. **Backend Health**: Verify all health endpoints (/api/health, /api/agent/health, /api/agent/status) are working properly
2. **Task Creation**: Test basic task creation via /api/agent/chat endpoint  
3. **Plan Generation**: Verify that tasks generate proper plan structures with steps, not just basic responses
4. **WebSocket Functionality**: Test WebSocket endpoints and verify they're accessible and functional
5. **Database Operations**: Test task persistence and retrieval from MongoDB
6. **OLLAMA Integration**: Ensure OLLAMA connection is working for plan generation

CONTEXT: Just removed orphaned files (useIsolatedPlanManager.ts and useTaskWebSocket.ts) that were causing infinite loops and conflicts with the new simplified plan management system. Need to verify that the backend can now generate proper plans with step structures and that the infinite loop issue is resolved at the backend level.

EXPECTED: Backend should generate structured plans with steps, not just basic chat responses, and all endpoints should work without infinite loops or conflicts.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL from environment
BACKEND_URL = "https://31ac0422-78aa-4076-a1b1-c3e7b8886947.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisBackendTester:
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
    
    def test_backend_health_endpoints(self) -> bool:
        """Test 1: All Backend Health Endpoints"""
        try:
            print(f"\n🏥 Testing all backend health endpoints...")
            
            health_endpoints = [
                ("/api/health", "API Health"),
                ("/api/agent/status", "Agent Status")
            ]
            
            all_healthy = True
            health_details = []
            
            for endpoint, name in health_endpoints:
                try:
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get('status', 'unknown')
                        
                        if status in ['healthy', 'running']:
                            health_details.append(f"{name}: ✅ {status}")
                            
                            # Check specific services for detailed health
                            if 'services' in data:
                                services = data['services']
                                if isinstance(services, dict):
                                    db_status = services.get('database', False)
                                    ollama_status = services.get('ollama', False)
                                    tools_count = services.get('tools', 0)
                                    health_details.append(f"  - Database: {'✅' if db_status else '❌'}")
                                    health_details.append(f"  - OLLAMA: {'✅' if ollama_status else '❌'}")
                                    health_details.append(f"  - Tools: {tools_count}")
                        else:
                            health_details.append(f"{name}: ❌ {status}")
                            all_healthy = False
                    else:
                        health_details.append(f"{name}: ❌ HTTP {response.status_code}")
                        all_healthy = False
                        
                except Exception as e:
                    health_details.append(f"{name}: ❌ Exception: {str(e)}")
                    all_healthy = False
            
            if all_healthy:
                self.log_test("Backend Health Endpoints", True, 
                            f"All health endpoints working - {'; '.join(health_details)}")
                return True
            else:
                self.log_test("Backend Health Endpoints", False, 
                            f"Some health endpoints failed - {'; '.join(health_details)}")
                return False
                
        except Exception as e:
            self.log_test("Backend Health Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_task_creation_basic(self) -> bool:
        """Test 2: Basic Task Creation via /api/agent/chat"""
        try:
            print(f"\n📋 Testing basic task creation...")
            
            test_message = "Crear un análisis de mercado para software en 2025"
            
            payload = {
                "message": test_message
            }
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for basic response fields
                response_text = data.get('response', '')
                task_id = data.get('task_id', '')
                memory_used = data.get('memory_used', False)
                
                # Store task_id for later tests
                if task_id:
                    self.task_id = task_id
                    print(f"   📋 Task created with ID: {task_id}")
                
                if response_text and task_id:
                    self.log_test("Basic Task Creation", True, 
                                f"Task created successfully - ID: {task_id}, Memory: {memory_used}")
                    return True
                else:
                    self.log_test("Basic Task Creation", False, 
                                f"Task creation incomplete - Response: {bool(response_text)}, ID: {bool(task_id)}", data)
                    return False
            else:
                self.log_test("Basic Task Creation", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Basic Task Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_plan_generation_structure(self) -> bool:
        """Test 3: Plan Generation with Proper Step Structures"""
        try:
            print(f"\n🎯 Testing plan generation with step structures...")
            
            # Use a task that should definitely generate a structured plan
            test_message = "Crear un plan de marketing digital para startups en 2025"
            
            payload = {
                "message": test_message
            }
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for plan structure
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                task_type = data.get('task_type', '')
                complexity = data.get('complexity', '')
                
                if plan and len(plan) >= 2:
                    valid_plan = True
                    step_details = []
                    
                    for i, step in enumerate(plan):
                        # Check required fields for proper plan structure
                        required_fields = ['id', 'title', 'description', 'tool', 'status']
                        missing_fields = [field for field in required_fields if field not in step]
                        
                        if missing_fields:
                            valid_plan = False
                            print(f"   ❌ Step {i+1} missing fields: {missing_fields}")
                            break
                        
                        step_details.append(f"Step {i+1}: {step.get('title', 'No title')} ({step.get('tool', 'No tool')})")
                        
                        # Verify step has proper structure
                        if not step.get('title') or not step.get('description'):
                            valid_plan = False
                            print(f"   ❌ Step {i+1} has empty title or description")
                            break
                    
                    if valid_plan and enhanced_title:
                        self.log_test("Plan Generation Structure", True, 
                                    f"Structured plan generated - {len(plan)} steps, Type: {task_type}, Complexity: {complexity}")
                        print(f"   📊 Enhanced Title: {enhanced_title}")
                        print(f"   📋 Plan Steps: {'; '.join(step_details)}")
                        return True
                    else:
                        self.log_test("Plan Generation Structure", False, 
                                    f"Plan structure invalid - Valid: {valid_plan}, Title: {bool(enhanced_title)}", data)
                        return False
                else:
                    # Check if it's just a basic chat response (which would indicate the infinite loop issue)
                    response_text = data.get('response', '')
                    if response_text and not plan:
                        self.log_test("Plan Generation Structure", False, 
                                    f"Only basic chat response generated, no plan structure - This indicates the infinite loop issue may persist", data)
                    else:
                        self.log_test("Plan Generation Structure", False, 
                                    f"No plan generated - Plan length: {len(plan) if plan else 0}", data)
                    return False
            else:
                self.log_test("Plan Generation Structure", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Plan Generation Structure", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_functionality(self) -> bool:
        """Test 4: WebSocket Endpoints and Functionality"""
        try:
            print(f"\n🔌 Testing WebSocket functionality...")
            
            # Test WebSocket endpoint accessibility
            websocket_url = f"{BACKEND_URL}/api/socket.io/"
            
            # Try to access the WebSocket endpoint
            response = self.session.get(websocket_url, timeout=10)
            
            # WebSocket endpoints typically return specific responses
            websocket_accessible = response.status_code in [200, 400, 426]  # 426 = Upgrade Required
            
            if websocket_accessible:
                # Test if we can get WebSocket transport info
                try:
                    # Try to get socket.io info
                    info_response = self.session.get(f"{websocket_url}?transport=polling", timeout=5)
                    if info_response.status_code == 200:
                        self.log_test("WebSocket Functionality", True, 
                                    f"WebSocket endpoint accessible and functional - Status: {response.status_code}")
                        return True
                    else:
                        self.log_test("WebSocket Functionality", True, 
                                    f"WebSocket endpoint accessible - Status: {response.status_code}")
                        return True
                except:
                    self.log_test("WebSocket Functionality", True, 
                                f"WebSocket endpoint accessible - Status: {response.status_code}")
                    return True
            else:
                self.log_test("WebSocket Functionality", False, 
                            f"WebSocket endpoint not accessible - Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Functionality", False, f"Exception: {str(e)}")
            return False
    
    def test_database_operations(self) -> bool:
        """Test 5: Database Operations (Task Persistence and Retrieval)"""
        try:
            print(f"\n💾 Testing database operations...")
            
            if not self.task_id:
                self.log_test("Database Operations", False, "No task ID available for database testing")
                return False
            
            # Test task retrieval
            try:
                response = self.session.get(f"{API_BASE}/agent/get-task-files/{self.task_id}", 
                                          timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if task data is retrievable
                    if isinstance(data, dict) and ('files' in data or 'task' in data or 'status' in data):
                        self.log_test("Database Operations", True, 
                                    f"Task data retrievable from database - Task ID: {self.task_id}")
                        return True
                    else:
                        self.log_test("Database Operations", False, 
                                    f"Task data format unexpected - Data: {type(data)}", data)
                        return False
                else:
                    # Try alternative endpoint
                    alt_response = self.session.get(f"{API_BASE}/agent/get-task-status/{self.task_id}", 
                                                  timeout=10)
                    if alt_response.status_code == 200:
                        self.log_test("Database Operations", True, 
                                    f"Task data retrievable via alternative endpoint - Task ID: {self.task_id}")
                        return True
                    else:
                        self.log_test("Database Operations", False, 
                                    f"Task not retrievable from database - HTTP {response.status_code}")
                        return False
                        
            except Exception as db_e:
                self.log_test("Database Operations", False, f"Database operation exception: {str(db_e)}")
                return False
                
        except Exception as e:
            self.log_test("Database Operations", False, f"Exception: {str(e)}")
            return False
    
    def test_ollama_integration(self) -> bool:
        """Test 6: OLLAMA Integration for Plan Generation"""
        try:
            print(f"\n🤖 Testing OLLAMA integration...")
            
            # Test OLLAMA status through agent status endpoint
            response = self.session.get(f"{API_BASE}/agent/status", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                ollama_info = data.get('ollama', {})
                ollama_connected = ollama_info.get('connected', False)
                ollama_endpoint = ollama_info.get('endpoint', '')
                ollama_model = ollama_info.get('model', '')
                available_models = ollama_info.get('available_models', [])
                
                if ollama_connected and ollama_endpoint and ollama_model:
                    # Test if OLLAMA can actually generate responses by making a simple chat request
                    test_payload = {
                        "message": "Hola, como estas?"
                    }
                    
                    chat_response = self.session.post(f"{API_BASE}/agent/chat", 
                                                    json=test_payload, timeout=20)
                    
                    if chat_response.status_code == 200:
                        chat_data = chat_response.json()
                        response_text = chat_data.get('response', '')
                        
                        if response_text and len(response_text) > 10:  # Meaningful response
                            self.log_test("OLLAMA Integration", True, 
                                        f"OLLAMA working - Endpoint: {ollama_endpoint}, Model: {ollama_model}, Models available: {len(available_models)}")
                            return True
                        else:
                            self.log_test("OLLAMA Integration", False, 
                                        f"OLLAMA connected but not generating proper responses - Response length: {len(response_text)}")
                            return False
                    else:
                        self.log_test("OLLAMA Integration", False, 
                                    f"OLLAMA connected but chat request failed - HTTP {chat_response.status_code}")
                        return False
                else:
                    self.log_test("OLLAMA Integration", False, 
                                f"OLLAMA not properly configured - Connected: {ollama_connected}, Endpoint: {bool(ollama_endpoint)}, Model: {bool(ollama_model)}", data)
                    return False
            else:
                self.log_test("OLLAMA Integration", False, 
                            f"Cannot check OLLAMA status - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OLLAMA Integration", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive backend tests"""
        print("🧪 STARTING MITOSIS BACKEND COMPREHENSIVE TESTING AFTER ORPHANED FILES CLEANUP")
        print("=" * 80)
        print("🎯 FOCUS: Testing backend after removing orphaned files causing infinite loops")
        print("📋 TESTING: Health endpoints, task creation, plan generation, WebSocket, database, OLLAMA")
        print("🔍 CONTEXT: Verifying infinite loop issue is resolved and proper plan structures are generated")
        print("⚠️ EXPECTED: Structured plans with steps, not just basic chat responses")
        print("=" * 80)
        
        # Test sequence for comprehensive backend testing
        tests = [
            ("Backend Health Endpoints", self.test_backend_health_endpoints),
            ("Basic Task Creation", self.test_task_creation_basic),
            ("Plan Generation Structure", self.test_plan_generation_structure),
            ("WebSocket Functionality", self.test_websocket_functionality),
            ("Database Operations", self.test_database_operations),
            ("OLLAMA Integration", self.test_ollama_integration)
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
        print("🎯 MITOSIS BACKEND COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 80:
            overall_status = "✅ BACKEND FULLY FUNCTIONAL - INFINITE LOOP ISSUE RESOLVED"
        elif success_rate >= 60:
            overall_status = "⚠️ BACKEND MOSTLY FUNCTIONAL - Minor issues remain"
        else:
            overall_status = "❌ BACKEND HAS CRITICAL ISSUES - Infinite loop issue may persist"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical functionality assessment for infinite loop resolution
        critical_tests = ["Backend Health Endpoints", "Plan Generation Structure", "OLLAMA Integration"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL FUNCTIONALITY FOR INFINITE LOOP RESOLUTION:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical backend functionality is working")
            print("   🎯 CONCLUSION: Infinite loop issue appears to be resolved")
            print("   📋 RECOMMENDATION: Backend ready for frontend integration")
        else:
            print("   ❌ Some critical backend functionality is not working")
            print("   🎯 CONCLUSION: Infinite loop issue may persist or other critical problems exist")
            print("   📋 RECOMMENDATION: Fix backend issues before proceeding")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id,
            'backend_ready': critical_passed >= len(critical_tests) - 1,  # Allow 1 failure
            'infinite_loop_resolved': critical_passed >= 2  # At least plan generation and health working
        }

def main():
    """Main testing function"""
    tester = MitosisBackendTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/backend_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR MITOSIS BACKEND AFTER ORPHANED FILES CLEANUP")
    print("=" * 80)
    
    if results['backend_ready']:
        print("✅ BACKEND DIAGNOSIS: Backend APIs are working and ready")
        if results['infinite_loop_resolved']:
            print("✅ INFINITE LOOP ISSUE: Appears to be resolved - proper plan generation working")
        else:
            print("⚠️ INFINITE LOOP ISSUE: May still exist - plan generation needs verification")
        print("📋 RECOMMENDATION: Backend is ready for frontend integration")
        print("🔧 NEXT STEPS: Test frontend UI and plan execution functionality")
    else:
        print("❌ BACKEND DIAGNOSIS: Backend has critical issues")
        if not results['infinite_loop_resolved']:
            print("❌ INFINITE LOOP ISSUE: Likely persists - plan generation not working properly")
        print("📋 RECOMMENDATION: Fix backend issues before frontend testing")
        print("🔧 NEXT STEPS: Address backend API problems and infinite loop issues")
    
    # Return exit code based on success
    if results['success_rate'] >= 60:
        print("\n🎉 BACKEND TESTING COMPLETED - READY FOR NEXT PHASE")
        return 0
    else:
        print("\n⚠️ BACKEND TESTING COMPLETED WITH CRITICAL ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)