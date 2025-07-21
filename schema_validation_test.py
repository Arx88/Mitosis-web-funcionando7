#!/usr/bin/env python3
"""
Schema Validation and Plan Generation Testing Script
Tests the Mitosis backend focusing on schema validation fixes and plan generation improvements
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Backend URL from environment - try local first, then external
LOCAL_BACKEND_URL = "http://localhost:8001"
EXTERNAL_BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://bc6fef3a-4731-4ece-b5a8-f725fb26e620.preview.emergentagent.com')

# Test local first
try:
    test_response = requests.get(f"{LOCAL_BACKEND_URL}/api/health", timeout=5)
    if test_response.status_code == 200:
        BACKEND_URL = LOCAL_BACKEND_URL
        print(f"✅ Using local backend: {BACKEND_URL}")
    else:
        BACKEND_URL = EXTERNAL_BACKEND_URL
        print(f"⚠️ Local backend not available, using external: {BACKEND_URL}")
except:
    BACKEND_URL = EXTERNAL_BACKEND_URL
    print(f"⚠️ Local backend not available, using external: {BACKEND_URL}")

API_BASE = f"{BACKEND_URL}/api"

class SchemaValidationTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        
        print(f"{status} {test_name} ({response_time:.2f}s)")
        print(f"   Details: {details}")
        print()
        
    def test_backend_health(self):
        """Test backend health and service status"""
        print("🏥 Testing Backend Health...")
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                ollama_status = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                database_status = services.get('database', False)
                
                details = f"Services: Ollama={ollama_status}, Tools={tools_count}, Database={database_status}"
                self.log_result("Backend Health Check", True, details, response_time)
                return True
            else:
                self.log_result("Backend Health Check", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Backend Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_agent_status(self):
        """Test agent status endpoint for Ollama configuration"""
        print("🤖 Testing Agent Status...")
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/agent/status", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                ollama_config = data.get('ollama', {})
                endpoint = ollama_config.get('endpoint', '')
                model = ollama_config.get('current_model', '')
                
                # Check if endpoint matches expected
                expected_endpoint = "https://78d08925604a.ngrok-free.app"
                endpoint_match = expected_endpoint in endpoint
                
                details = f"Endpoint: {endpoint}, Model: {model}, Endpoint Match: {endpoint_match}"
                self.log_result("Agent Status Check", endpoint_match, details, response_time)
                return endpoint_match
            else:
                self.log_result("Agent Status Check", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Agent Status Check", False, f"Error: {str(e)}")
            return False
    
    def test_schema_validation_investigacion(self):
        """Test schema validation with investigación task"""
        print("🔍 Testing Schema Validation - Investigación...")
        message = "Buscar información sobre inteligencia artificial"
        
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE}/agent/chat", 
                                   json={"message": message}, 
                                   timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for schema validation success indicators
                has_task_id = 'task_id' in data
                has_response = 'response' in data and len(data['response']) > 0
                no_schema_errors = 'schema' not in data.get('response', '').lower() or 'validation' not in data.get('response', '').lower()
                
                # Check if plan was generated (for task messages)
                plan_generated = 'plan' in data or 'PLAN' in data.get('response', '')
                
                success = has_task_id and has_response and no_schema_errors
                details = f"Task ID: {has_task_id}, Response: {has_response}, No Schema Errors: {no_schema_errors}, Plan Generated: {plan_generated}"
                
                self.log_result("Schema Validation - Investigación", success, details, response_time)
                return success, data
            else:
                self.log_result("Schema Validation - Investigación", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Schema Validation - Investigación", False, f"Error: {str(e)}")
            return False, None
    
    def test_schema_validation_creacion(self):
        """Test schema validation with creación task"""
        print("📝 Testing Schema Validation - Creación...")
        message = "Crear un documento técnico sobre Python"
        
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE}/agent/chat", 
                                   json={"message": message}, 
                                   timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for valid response structure
                has_task_id = 'task_id' in data
                has_response = 'response' in data and len(data['response']) > 0
                no_schema_errors = 'error' not in data.get('response', '').lower() or 'schema' not in data.get('response', '').lower()
                
                success = has_task_id and has_response and no_schema_errors
                details = f"Task ID: {has_task_id}, Response Length: {len(data.get('response', ''))}, No Schema Errors: {no_schema_errors}"
                
                self.log_result("Schema Validation - Creación", success, details, response_time)
                return success, data
            else:
                self.log_result("Schema Validation - Creación", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Schema Validation - Creación", False, f"Error: {str(e)}")
            return False, None
    
    def test_schema_validation_analisis(self):
        """Test schema validation with análisis task"""
        print("📊 Testing Schema Validation - Análisis...")
        message = "Analizar los beneficios de la automatización"
        
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE}/agent/chat", 
                                   json={"message": message}, 
                                   timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for valid response structure
                has_task_id = 'task_id' in data
                has_response = 'response' in data and len(data['response']) > 0
                memory_used = data.get('memory_used', False)
                
                success = has_task_id and has_response and memory_used
                details = f"Task ID: {has_task_id}, Response: {has_response}, Memory Used: {memory_used}"
                
                self.log_result("Schema Validation - Análisis", success, details, response_time)
                return success, data
            else:
                self.log_result("Schema Validation - Análisis", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Schema Validation - Análisis", False, f"Error: {str(e)}")
            return False, None
    
    def test_schema_validation_general(self):
        """Test schema validation with general processing task"""
        print("⚙️ Testing Schema Validation - General Processing...")
        message = "Ayúdame con mi proyecto"
        
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE}/agent/chat", 
                                   json={"message": message}, 
                                   timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for valid response structure
                has_task_id = 'task_id' in data
                has_response = 'response' in data and len(data['response']) > 0
                execution_status = data.get('execution_status', '')
                
                success = has_task_id and has_response
                details = f"Task ID: {has_task_id}, Response: {has_response}, Status: {execution_status}"
                
                self.log_result("Schema Validation - General Processing", success, details, response_time)
                return success, data
            else:
                self.log_result("Schema Validation - General Processing", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Schema Validation - General Processing", False, f"Error: {str(e)}")
            return False, None
    
    def test_plan_generation_robustness(self):
        """Test plan generation robustness and retry mechanisms"""
        print("🔄 Testing Plan Generation Robustness...")
        
        # Test with a complex task that should trigger plan generation
        message = "Crear un análisis completo del mercado de tecnología blockchain en 2025"
        
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE}/agent/chat", 
                                   json={"message": message}, 
                                   timeout=45)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for plan generation indicators
                has_task_id = 'task_id' in data
                has_response = 'response' in data
                response_text = data.get('response', '')
                
                # Look for plan indicators in response
                has_plan_structure = any(keyword in response_text.upper() for keyword in ['PLAN', 'PASO', 'ETAPA', 'FASE'])
                no_error_messages = not any(error in response_text.lower() for error in ['error', 'failed', 'falló'])
                
                success = has_task_id and has_response and has_plan_structure and no_error_messages
                details = f"Task ID: {has_task_id}, Plan Structure: {has_plan_structure}, No Errors: {no_error_messages}, Response Length: {len(response_text)}"
                
                self.log_result("Plan Generation Robustness", success, details, response_time)
                return success, data
            else:
                self.log_result("Plan Generation Robustness", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Plan Generation Robustness", False, f"Error: {str(e)}")
            return False, None
    
    def test_tool_consistency(self):
        """Test that tools used match PLAN_SCHEMA enum values"""
        print("🔧 Testing Tool Consistency...")
        
        # Valid tools according to PLAN_SCHEMA
        valid_tools = [
            "web_search", "analysis", "creation", "planning", "delivery", 
            "processing", "synthesis", "search_definition", "data_analysis", 
            "shell", "research", "investigation", "web_scraping", "search", 
            "mind_map", "spreadsheets", "database"
        ]
        
        # Test with a task that should use multiple tools
        message = "Investigar y crear un informe sobre las tendencias de IA en 2025"
        
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE}/agent/chat", 
                                   json={"message": message}, 
                                   timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Check if response mentions any invalid tool combinations
                invalid_tool_patterns = ['web_search|analysis', 'analysis|creation', 'search|investigation']
                has_invalid_tools = any(pattern in response_text for pattern in invalid_tool_patterns)
                
                # Check for valid tool mentions
                mentioned_tools = [tool for tool in valid_tools if tool in response_text.lower()]
                
                success = not has_invalid_tools and len(mentioned_tools) > 0
                details = f"No Invalid Tools: {not has_invalid_tools}, Valid Tools Mentioned: {len(mentioned_tools)}, Tools: {mentioned_tools[:3]}"
                
                self.log_result("Tool Consistency Check", success, details, response_time)
                return success, data
            else:
                self.log_result("Tool Consistency Check", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Tool Consistency Check", False, f"Error: {str(e)}")
            return False, None
    
    def test_emergency_plan_generation(self):
        """Test emergency plan generation when Ollama fails"""
        print("🆘 Testing Emergency Plan Generation...")
        
        # This test checks if the system can handle failures gracefully
        message = "Crear un documento muy complejo con múltiples secciones técnicas"
        
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE}/agent/chat", 
                                   json={"message": message}, 
                                   timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check that we get a response even if there are issues
                has_response = 'response' in data and len(data.get('response', '')) > 0
                has_task_id = 'task_id' in data
                
                # Check if emergency plan was used (look for fallback indicators)
                response_text = data.get('response', '')
                has_fallback_indicators = any(word in response_text.lower() for word in ['emergency', 'fallback', 'backup'])
                
                success = has_response and has_task_id
                details = f"Has Response: {has_response}, Task ID: {has_task_id}, Fallback Used: {has_fallback_indicators}"
                
                self.log_result("Emergency Plan Generation", success, details, response_time)
                return success, data
            else:
                self.log_result("Emergency Plan Generation", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Emergency Plan Generation", False, f"Error: {str(e)}")
            return False, None
    
    def test_casual_vs_task_detection(self):
        """Test that casual messages don't trigger plan generation"""
        print("💬 Testing Casual vs Task Detection...")
        
        # Test casual message
        casual_message = "hola"
        
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE}/agent/chat", 
                                   json={"message": casual_message}, 
                                   timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Casual messages should NOT generate plans
                has_plan_structure = any(keyword in response_text.upper() for keyword in ['PLAN DE ACCIÓN', 'PASO 1', 'ETAPA'])
                is_casual_response = len(response_text) < 200  # Casual responses should be shorter
                has_greeting = any(word in response_text.lower() for word in ['hola', 'saludos', 'buenos'])
                
                success = not has_plan_structure and (is_casual_response or has_greeting)
                details = f"No Plan Structure: {not has_plan_structure}, Casual Response: {is_casual_response}, Has Greeting: {has_greeting}"
                
                self.log_result("Casual vs Task Detection", success, details, response_time)
                return success, data
            else:
                self.log_result("Casual vs Task Detection", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Casual vs Task Detection", False, f"Error: {str(e)}")
            return False, None
    
    def run_all_tests(self):
        """Run all schema validation and plan generation tests"""
        print("🧪 Starting Schema Validation and Plan Generation Testing...")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Test 1: Backend Health
        health_ok = self.test_backend_health()
        if not health_ok:
            print("❌ Backend health check failed. Stopping tests.")
            return self.generate_summary()
        
        # Test 2: Agent Status
        self.test_agent_status()
        
        # Test 3-6: Schema Validation Tests
        self.test_schema_validation_investigacion()
        self.test_schema_validation_creacion()
        self.test_schema_validation_analisis()
        self.test_schema_validation_general()
        
        # Test 7: Plan Generation Robustness
        self.test_plan_generation_robustness()
        
        # Test 8: Tool Consistency
        self.test_tool_consistency()
        
        # Test 9: Emergency Plan Generation
        self.test_emergency_plan_generation()
        
        # Test 10: Casual vs Task Detection
        self.test_casual_vs_task_detection()
        
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("=" * 80)
        print("📊 SCHEMA VALIDATION AND PLAN GENERATION TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Show failed tests
        if self.failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"   - {result['test_name']}: {result['details']}")
            print()
        
        # Show passed tests
        print("✅ PASSED TESTS:")
        for result in self.results:
            if result['success']:
                print(f"   - {result['test_name']}: {result['details']}")
        
        print()
        print("🎯 KEY FINDINGS:")
        
        # Analyze results for key findings
        schema_tests = [r for r in self.results if 'Schema Validation' in r['test_name']]
        schema_success_rate = (sum(1 for r in schema_tests if r['success']) / len(schema_tests) * 100) if schema_tests else 0
        
        plan_tests = [r for r in self.results if 'Plan Generation' in r['test_name'] or 'Tool Consistency' in r['test_name']]
        plan_success_rate = (sum(1 for r in plan_tests if r['success']) / len(plan_tests) * 100) if plan_tests else 0
        
        print(f"   - Schema Validation Success Rate: {schema_success_rate:.1f}%")
        print(f"   - Plan Generation Success Rate: {plan_success_rate:.1f}%")
        
        if success_rate >= 80:
            print("   - ✅ Overall system performance is EXCELLENT")
        elif success_rate >= 60:
            print("   - ⚠️ Overall system performance is GOOD with minor issues")
        else:
            print("   - ❌ Overall system performance needs IMPROVEMENT")
        
        return {
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': success_rate,
            'results': self.results
        }

def main():
    """Main test execution"""
    tester = SchemaValidationTester()
    summary = tester.run_all_tests()
    
    # Save results to file
    with open('/app/schema_validation_test_results.json', 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Test results saved to: /app/schema_validation_test_results.json")
    
    # Return appropriate exit code
    if summary['success_rate'] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()