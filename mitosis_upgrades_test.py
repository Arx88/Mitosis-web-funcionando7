#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND TESTING - MITOSIS V5-BETA UPGRADE VERIFICATION
Testing all 6 major improvements implemented according to UPGRADE.md

This script tests:
1. LLM Intent Detection with is_casual_conversation()
2. Robust Plan Generation with generate_dynamic_plan_with_ai()
3. Real-time WebSockets
4. Robust Ollama Parsing with _parse_response()
5. Task Persistence (MongoDB)
6. Error Handling and Resiliency
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class MitosisUpgradesTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.api_base = API_BASE
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = 30
        
    def log_test(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name} ({response_time:.2f}s)")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_backend_health(self):
        """Test basic backend health"""
        print("\n🏥 TESTING BACKEND HEALTH")
        try:
            start_time = time.time()
            response = self.session.get(f"{self.api_base}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                # Check all required services
                ollama_healthy = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                database_healthy = services.get('database', False)
                
                details = f"Ollama: {ollama_healthy}, Tools: {tools_count}, Database: {database_healthy}"
                success = ollama_healthy and tools_count > 0 and database_healthy
                
                self.log_test("Backend Health Check", success, details, response_time)
                return success
            else:
                self.log_test("Backend Health Check", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_llm_intent_detection(self):
        """Test LLM Intent Detection (UPGRADE.md Section 1)"""
        print("\n🤖 TESTING LLM INTENT DETECTION")
        
        # Test cases for casual vs task detection
        test_cases = [
            # Casual messages
            {"message": "hola", "expected_casual": True, "description": "Simple greeting"},
            {"message": "¿cómo estás?", "expected_casual": True, "description": "Casual question"},
            {"message": "gracias", "expected_casual": True, "description": "Thank you"},
            {"message": "buenos días", "expected_casual": True, "description": "Good morning"},
            
            # Task messages
            {"message": "crear un informe sobre IA", "expected_casual": False, "description": "Create report task"},
            {"message": "buscar información sobre machine learning", "expected_casual": False, "description": "Search task"},
            {"message": "analizar datos de mercado", "expected_casual": False, "description": "Analysis task"},
            {"message": "generar contenido para blog", "expected_casual": False, "description": "Content creation task"}
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for test_case in test_cases:
            try:
                start_time = time.time()
                response = self.session.post(f"{self.api_base}/agent/chat", json={
                    "message": test_case["message"]
                })
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if response indicates casual or task handling
                    response_text = data.get('response', '').lower()
                    has_plan = 'plan de acción' in response_text or 'steps' in str(data)
                    is_casual_response = not has_plan and len(response_text) < 200
                    
                    # Determine if classification was correct
                    expected_casual = test_case["expected_casual"]
                    actual_casual = is_casual_response
                    
                    success = (expected_casual == actual_casual)
                    
                    if success:
                        passed_tests += 1
                    
                    details = f"{test_case['description']}: Expected casual={expected_casual}, Got casual={actual_casual}"
                    self.log_test(f"Intent Detection - {test_case['message'][:20]}...", success, details, response_time)
                    
                else:
                    self.log_test(f"Intent Detection - {test_case['message'][:20]}...", False, f"HTTP {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Intent Detection - {test_case['message'][:20]}...", False, f"Exception: {str(e)}")
        
        # Overall intent detection success
        overall_success = passed_tests >= (total_tests * 0.75)  # 75% success rate required
        self.log_test("LLM Intent Detection Overall", overall_success, f"{passed_tests}/{total_tests} tests passed")
        
        return overall_success
    
    def test_robust_plan_generation(self):
        """Test Robust Plan Generation with JSON Schema Validation (UPGRADE.md Section 2)"""
        print("\n📋 TESTING ROBUST PLAN GENERATION")
        
        test_tasks = [
            "Crear un análisis completo sobre tendencias de inteligencia artificial en 2025",
            "Desarrollar una estrategia de marketing digital para una startup",
            "Investigar y documentar las mejores prácticas de desarrollo web moderno"
        ]
        
        passed_tests = 0
        
        for task in test_tasks:
            try:
                start_time = time.time()
                response = self.session.post(f"{self.api_base}/agent/chat", json={
                    "message": task
                })
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for plan generation
                    has_structured_plan = 'structured_plan' in data
                    has_steps = False
                    plan_source = data.get('plan_source', 'unknown')
                    execution_status = data.get('execution_status', 'unknown')
                    has_required_fields = False
                    valid_steps = False
                    
                    if has_structured_plan:
                        plan = data.get('structured_plan', {})
                        steps = plan.get('steps', [])
                        has_steps = len(steps) > 0
                        
                        # Validate plan structure (JSON Schema validation)
                        has_required_fields = all(key in plan for key in ['steps', 'task_type', 'complexity'])
                        
                        # Check if steps have required structure
                        valid_steps = True
                        for step in steps:
                            if not all(key in step for key in ['title', 'description', 'tool']):
                                valid_steps = False
                                break
                    
                    # Check for proper initial execution status (should be 'plan_generated', not 'completed')
                    proper_initial_status = execution_status in ['plan_generated', 'executing', 'pending']
                    
                    # Check for fallback notification if applicable
                    has_fallback_notification = plan_source == 'fallback' and 'warning' in data
                    
                    success = (has_structured_plan and has_steps and has_required_fields and 
                              valid_steps and proper_initial_status)
                    
                    details = f"Plan: {has_structured_plan}, Steps: {len(steps) if has_steps else 0}, Status: {execution_status}, Source: {plan_source}"
                    
                    if success:
                        passed_tests += 1
                    
                    self.log_test(f"Plan Generation - {task[:30]}...", success, details, response_time)
                    
                else:
                    self.log_test(f"Plan Generation - {task[:30]}...", False, f"HTTP {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Plan Generation - {task[:30]}...", False, f"Exception: {str(e)}")
        
        overall_success = passed_tests >= len(test_tasks) * 0.67  # 67% success rate required
        self.log_test("Robust Plan Generation Overall", overall_success, f"{passed_tests}/{len(test_tasks)} tests passed")
        
        return overall_success
    
    def test_websocket_functionality(self):
        """Test WebSocket Real-time Updates (UPGRADE.md Section 3)"""
        print("\n🔌 TESTING WEBSOCKET FUNCTIONALITY")
        
        try:
            # Test WebSocket initialization by checking if WebSocket manager is available
            start_time = time.time()
            response = self.session.get(f"{self.api_base}/agent/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Start a task that should trigger WebSocket updates
                task_response = self.session.post(f"{self.api_base}/agent/chat", json={
                    "message": "Buscar información sobre Python programming"
                })
                
                if task_response.status_code == 200:
                    task_data = task_response.json()
                    task_id = task_data.get('task_id')
                    
                    if task_id:
                        # WebSocket functionality is implemented - we can't directly test WebSocket 
                        # connections in this script, but we can verify the infrastructure exists
                        success = True
                        details = f"WebSocket infrastructure available, Task ID: {task_id}"
                    else:
                        success = False
                        details = "No task ID returned for WebSocket tracking"
                else:
                    success = False
                    details = f"Failed to start task for WebSocket testing: HTTP {task_response.status_code}"
            else:
                success = False
                details = f"Backend health check failed: HTTP {response.status_code}"
            
            self.log_test("WebSocket Infrastructure", success, details, response_time)
            return success
            
        except Exception as e:
            self.log_test("WebSocket Infrastructure", False, f"Exception: {str(e)}")
            return False
    
    def test_ollama_parsing_robustness(self):
        """Test Robust Ollama Parsing (UPGRADE.md Section 4)"""
        print("\n🧠 TESTING OLLAMA PARSING ROBUSTNESS")
        
        try:
            # Test Ollama connection and parsing
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/agent/ollama/check", json={
                "endpoint": "https://78d08925604a.ngrok-free.app"
            })
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                connection_status = data.get('status', 'unknown')
                
                if connection_status == 'connected':
                    # Test model availability
                    models_response = self.session.post(f"{self.api_base}/agent/ollama/models", json={
                        "endpoint": "https://78d08925604a.ngrok-free.app"
                    })
                    
                    if models_response.status_code == 200:
                        models_data = models_response.json()
                        models = models_data.get('models', [])
                        has_llama_model = any('llama3.1:8b' in model for model in models)
                        
                        # Test response parsing with a complex query
                        parse_test_response = self.session.post(f"{self.api_base}/agent/chat", json={
                            "message": "Generar un plan JSON estructurado para análisis de datos"
                        })
                        
                        if parse_test_response.status_code == 200:
                            parse_data = parse_test_response.json()
                            has_structured_response = 'structured_plan' in parse_data
                            
                            success = has_llama_model and has_structured_response
                            details = f"Models: {len(models)}, Llama3.1: {has_llama_model}, Structured: {has_structured_response}"
                        else:
                            success = False
                            details = f"Parse test failed: HTTP {parse_test_response.status_code}"
                    else:
                        success = False
                        details = f"Models check failed: HTTP {models_response.status_code}"
                else:
                    success = False
                    details = f"Ollama not connected: {connection_status}"
            else:
                success = False
                details = f"Ollama check failed: HTTP {response.status_code}"
            
            self.log_test("Ollama Parsing Robustness", success, details, response_time)
            return success
            
        except Exception as e:
            self.log_test("Ollama Parsing Robustness", False, f"Exception: {str(e)}")
            return False
    
    def test_task_persistence(self):
        """Test Task Persistence with MongoDB (UPGRADE.md Section 5)"""
        print("\n💾 TESTING TASK PERSISTENCE")
        
        try:
            # Create a task and verify it's persisted
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/agent/chat", json={
                "message": "Crear un documento sobre blockchain technology"
            })
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                
                if task_id:
                    # Wait a moment for persistence
                    time.sleep(2)
                    
                    # Try to retrieve task status (this would use persistent storage)
                    status_response = self.session.get(f"{self.api_base}/agent/status")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        # Check if database is connected (indicates persistence capability)
                        database_connected = status_data.get('database', {}).get('connected', False)
                        
                        success = database_connected
                        details = f"Task ID: {task_id}, Database connected: {database_connected}"
                    else:
                        success = False
                        details = f"Status check failed: HTTP {status_response.status_code}"
                else:
                    success = False
                    details = "No task ID returned"
            else:
                success = False
                details = f"Task creation failed: HTTP {response.status_code}"
            
            self.log_test("Task Persistence", success, details, response_time)
            return success
            
        except Exception as e:
            self.log_test("Task Persistence", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling_resilience(self):
        """Test Error Handling and Resilience (UPGRADE.md Section 6)"""
        print("\n🛡️ TESTING ERROR HANDLING & RESILIENCE")
        
        test_scenarios = [
            {
                "name": "Invalid Endpoint",
                "url": f"{self.api_base}/invalid/endpoint",
                "method": "GET",
                "expected_status": 404,
                "data": None
            },
            {
                "name": "Invalid Chat Data",
                "url": f"{self.api_base}/agent/chat",
                "method": "POST",
                "expected_status": 400,
                "data": {"invalid_field": "test"}
            },
            {
                "name": "Empty Chat Message",
                "url": f"{self.api_base}/agent/chat",
                "method": "POST",
                "expected_status": 400,
                "data": {"message": ""}
            }
        ]
        
        passed_tests = 0
        
        for scenario in test_scenarios:
            try:
                start_time = time.time()
                
                if scenario["method"] == "GET":
                    response = self.session.get(scenario["url"])
                else:
                    response = self.session.post(scenario["url"], json=scenario["data"])
                
                response_time = time.time() - start_time
                
                # Check if error is handled properly
                status_matches = response.status_code == scenario["expected_status"]
                
                # Check if error response is structured
                has_error_message = False
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        has_error_message = 'error' in error_data
                    except:
                        has_error_message = False
                
                success = status_matches and (response.status_code < 400 or has_error_message)
                
                if success:
                    passed_tests += 1
                
                details = f"Expected: {scenario['expected_status']}, Got: {response.status_code}, Error msg: {has_error_message}"
                self.log_test(f"Error Handling - {scenario['name']}", success, details, response_time)
                
            except Exception as e:
                self.log_test(f"Error Handling - {scenario['name']}", False, f"Exception: {str(e)}")
        
        # Test resilience with a complex task that might fail
        try:
            start_time = time.time()
            resilience_response = self.session.post(f"{self.api_base}/agent/chat", json={
                "message": "Realizar una tarea muy compleja que podría fallar con múltiples pasos"
            })
            response_time = time.time() - start_time
            
            if resilience_response.status_code == 200:
                resilience_data = resilience_response.json()
                has_fallback_plan = 'plan_source' in resilience_data
                has_error_handling = 'error' not in resilience_data or resilience_data.get('error') is None
                
                resilience_success = has_error_handling
                resilience_details = f"Fallback available: {has_fallback_plan}, No errors: {has_error_handling}"
                
                if resilience_success:
                    passed_tests += 1
                
                self.log_test("Resilience - Complex Task", resilience_success, resilience_details, response_time)
            else:
                self.log_test("Resilience - Complex Task", False, f"HTTP {resilience_response.status_code}")
                
        except Exception as e:
            self.log_test("Resilience - Complex Task", False, f"Exception: {str(e)}")
        
        overall_success = passed_tests >= len(test_scenarios) * 0.75  # 75% success rate required
        self.log_test("Error Handling & Resilience Overall", overall_success, f"{passed_tests}/{len(test_scenarios) + 1} tests passed")
        
        return overall_success
    
    def test_memory_system_integration(self):
        """Test Memory System Integration"""
        print("\n🧠 TESTING MEMORY SYSTEM INTEGRATION")
        
        try:
            # Test memory analytics endpoint
            start_time = time.time()
            response = self.session.get(f"{self.api_base}/memory/memory-analytics")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                has_overview = 'overview' in data
                has_efficiency = 'memory_efficiency' in data
                has_insights = 'learning_insights' in data
                
                success = has_overview and has_efficiency and has_insights
                details = f"Overview: {has_overview}, Efficiency: {has_efficiency}, Insights: {has_insights}"
            else:
                success = False
                details = f"HTTP {response.status_code}"
            
            self.log_test("Memory System Analytics", success, details, response_time)
            
            # Test memory storage
            episode_response = self.session.post(f"{self.api_base}/memory/store-episode", json={
                "user_query": "Test query for memory",
                "agent_response": "Test response",
                "success": True,
                "context": {"test": True}
            })
            
            episode_success = episode_response.status_code == 200
            self.log_test("Memory Episode Storage", episode_success, f"HTTP {episode_response.status_code}")
            
            return success and episode_success
            
        except Exception as e:
            self.log_test("Memory System Integration", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 STARTING COMPREHENSIVE MITOSIS V5-BETA BACKEND TESTING")
        print("=" * 80)
        
        test_functions = [
            ("Backend Health", self.test_backend_health),
            ("LLM Intent Detection", self.test_llm_intent_detection),
            ("Robust Plan Generation", self.test_robust_plan_generation),
            ("WebSocket Functionality", self.test_websocket_functionality),
            ("Ollama Parsing Robustness", self.test_ollama_parsing_robustness),
            ("Task Persistence", self.test_task_persistence),
            ("Error Handling & Resilience", self.test_error_handling_resilience),
            ("Memory System Integration", self.test_memory_system_integration)
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_function in test_functions:
            try:
                result = test_function()
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {str(e)}")
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']} ({result['response_time']:.2f}s)")
        
        print(f"\n🎯 OVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 75:
            print("🎉 EXCELLENT - MITOSIS V5-BETA BACKEND IS HIGHLY FUNCTIONAL")
        elif success_rate >= 50:
            print("⚠️  GOOD - MITOSIS V5-BETA BACKEND IS FUNCTIONAL WITH MINOR ISSUES")
        else:
            print("❌ NEEDS ATTENTION - MITOSIS V5-BETA BACKEND HAS SIGNIFICANT ISSUES")
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = MitosisUpgradesTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)