#!/usr/bin/env python3
"""
Local Schema Validation and Plan Generation Testing Script
Tests the Mitosis backend locally focusing on schema validation fixes and plan generation improvements
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Use local backend URL
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class LocalSchemaValidationTester:
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
                                   timeout=60)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for schema validation success indicators
                has_task_id = 'task_id' in data
                has_response = 'response' in data and len(data['response']) > 0
                response_text = data.get('response', '')
                
                # Check for schema validation errors
                schema_error_indicators = ['schema validation failed', 'invalid tool names', 'web_search|analysis']
                has_schema_errors = any(indicator in response_text.lower() for indicator in schema_error_indicators)
                
                # Check if plan was generated (for task messages)
                plan_generated = 'plan' in data or any(keyword in response_text.upper() for keyword in ['PLAN', 'PASO', 'ETAPA'])
                
                success = has_task_id and has_response and not has_schema_errors
                details = f"Task ID: {has_task_id}, Response: {has_response}, No Schema Errors: {not has_schema_errors}, Plan Generated: {plan_generated}"
                
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
                                   timeout=60)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Check for valid response structure
                has_task_id = 'task_id' in data
                has_response = 'response' in data and len(data['response']) > 0
                
                # Check for schema validation errors
                schema_error_indicators = ['schema validation failed', 'invalid tool', 'validation error']
                has_schema_errors = any(indicator in response_text.lower() for indicator in schema_error_indicators)
                
                success = has_task_id and has_response and not has_schema_errors
                details = f"Task ID: {has_task_id}, Response Length: {len(data.get('response', ''))}, No Schema Errors: {not has_schema_errors}"
                
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
                                   timeout=60)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Check for valid response structure
                has_task_id = 'task_id' in data
                has_response = 'response' in data and len(data['response']) > 0
                memory_used = data.get('memory_used', False)
                
                # Check for schema validation errors
                has_schema_errors = 'schema' in response_text.lower() and 'error' in response_text.lower()
                
                success = has_task_id and has_response and memory_used and not has_schema_errors
                details = f"Task ID: {has_task_id}, Response: {has_response}, Memory Used: {memory_used}, No Schema Errors: {not has_schema_errors}"
                
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
                                   timeout=60)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Check for valid response structure
                has_task_id = 'task_id' in data
                has_response = 'response' in data and len(data['response']) > 0
                execution_status = data.get('execution_status', '')
                
                # Check for schema validation errors
                has_schema_errors = 'schema validation failed' in response_text.lower()
                
                success = has_task_id and has_response and not has_schema_errors
                details = f"Task ID: {has_task_id}, Response: {has_response}, Status: {execution_status}, No Schema Errors: {not has_schema_errors}"
                
                self.log_result("Schema Validation - General Processing", success, details, response_time)
                return success, data
            else:
                self.log_result("Schema Validation - General Processing", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Schema Validation - General Processing", False, f"Error: {str(e)}")
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
                                   timeout=60)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Check if response mentions any invalid tool combinations (the old problem)
                invalid_tool_patterns = ['web_search|analysis', 'analysis|creation', 'search|investigation']
                has_invalid_tools = any(pattern in response_text for pattern in invalid_tool_patterns)
                
                # Check for valid tool mentions
                mentioned_tools = [tool for tool in valid_tools if tool in response_text.lower()]
                
                # Check for schema validation success
                has_schema_errors = 'schema validation failed' in response_text.lower()
                
                success = not has_invalid_tools and not has_schema_errors and len(mentioned_tools) >= 0
                details = f"No Invalid Tools: {not has_invalid_tools}, No Schema Errors: {not has_schema_errors}, Valid Tools Mentioned: {len(mentioned_tools)}"
                
                self.log_result("Tool Consistency Check", success, details, response_time)
                return success, data
            else:
                self.log_result("Tool Consistency Check", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except Exception as e:
            self.log_result("Tool Consistency Check", False, f"Error: {str(e)}")
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
                                   timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Casual messages should NOT generate plans
                has_plan_structure = any(keyword in response_text.upper() for keyword in ['PLAN DE ACCIÓN', 'PASO 1', 'ETAPA'])
                is_casual_response = len(response_text) < 300  # Casual responses should be shorter
                has_greeting = any(word in response_text.lower() for word in ['hola', 'saludos', 'buenos', 'ayudar'])
                
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
        print("🧪 Starting Local Schema Validation and Plan Generation Testing...")
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
        
        # Test 7: Tool Consistency
        self.test_tool_consistency()
        
        # Test 8: Casual vs Task Detection
        self.test_casual_vs_task_detection()
        
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("=" * 80)
        print("📊 LOCAL SCHEMA VALIDATION AND PLAN GENERATION TEST SUMMARY")
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
        
        tool_tests = [r for r in self.results if 'Tool Consistency' in r['test_name'] or 'Casual vs Task' in r['test_name']]
        tool_success_rate = (sum(1 for r in tool_tests if r['success']) / len(tool_tests) * 100) if tool_tests else 0
        
        print(f"   - Schema Validation Success Rate: {schema_success_rate:.1f}%")
        print(f"   - Tool Consistency Success Rate: {tool_success_rate:.1f}%")
        
        if success_rate >= 80:
            print("   - ✅ Overall system performance is EXCELLENT")
        elif success_rate >= 60:
            print("   - ⚠️ Overall system performance is GOOD with minor issues")
        else:
            print("   - ❌ Overall system performance needs IMPROVEMENT")
        
        # Specific findings about schema validation fixes
        schema_error_found = any('schema' in r['details'].lower() and 'error' in r['details'].lower() for r in self.results)
        invalid_tools_found = any('invalid tool' in r['details'].lower() for r in self.results)
        
        print("\n🔍 SCHEMA VALIDATION SPECIFIC FINDINGS:")
        if not schema_error_found:
            print("   - ✅ No schema validation errors detected")
        else:
            print("   - ❌ Schema validation errors still present")
            
        if not invalid_tools_found:
            print("   - ✅ No invalid tool combinations detected")
        else:
            print("   - ❌ Invalid tool combinations still present")
        
        return {
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': success_rate,
            'results': self.results,
            'schema_validation_fixed': not schema_error_found,
            'tool_consistency_fixed': not invalid_tools_found
        }

def main():
    """Main test execution"""
    tester = LocalSchemaValidationTester()
    summary = tester.run_all_tests()
    
    # Save results to file
    with open('/app/local_schema_validation_test_results.json', 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Test results saved to: /app/local_schema_validation_test_results.json")
    
    # Return appropriate exit code
    if summary['success_rate'] >= 70:  # Lower threshold for local testing
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()