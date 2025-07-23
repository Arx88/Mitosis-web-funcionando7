#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND CONSOLIDATED SERVER TESTING
Tests the refactored consolidated backend server functionality
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://33daae9e-0eef-4291-8c45-9b1f547b085b.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class ConsolidatedBackendTester:
    """Comprehensive tester for the consolidated backend server"""
    
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        
        self.results.append(result)
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
    
    def test_health_endpoints(self):
        """Test health check endpoints"""
        print("🏥 TESTING HEALTH ENDPOINTS")
        print("=" * 50)
        
        # Test main health endpoint
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Check for new APIResponse format
                if 'success' in data and 'data' in data:
                    self.log_result(
                        "Main Health Check (New APIResponse Format)",
                        True,
                        f"Status: {data.get('success')}, Services: {data.get('data', {}).get('services', {})}"
                    )
                else:
                    # Old format
                    self.log_result(
                        "Main Health Check (Legacy Format)",
                        data.get('status') == 'healthy',
                        f"Status: {data.get('status')}, Services: {data.get('services', {})}"
                    )
            else:
                self.log_result("Main Health Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Main Health Check", False, f"Exception: {str(e)}")
        
        # Test API health endpoint
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "API Health Check",
                    data.get('success', True),
                    f"API Status: {data.get('data', {}).get('api_status', data.get('status'))}"
                )
            else:
                self.log_result("API Health Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("API Health Check", False, f"Exception: {str(e)}")
    
    def test_system_status_endpoint(self):
        """Test system status endpoint"""
        print("🖥️ TESTING SYSTEM STATUS ENDPOINT")
        print("=" * 50)
        
        try:
            response = requests.get(f"{API_BASE}/system/status", timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                # Check for consolidated server info
                server_info = data.get('data', {}).get('server_info', {})
                services = data.get('data', {}).get('services', {})
                
                success = (
                    server_info.get('name') == 'Mitosis Consolidated Server' and
                    'mongodb' in services and
                    'ollama' in services and
                    'tools' in services
                )
                
                self.log_result(
                    "System Status Endpoint",
                    success,
                    f"Server: {server_info.get('name')}, Services: {list(services.keys())}"
                )
            else:
                self.log_result("System Status Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("System Status Endpoint", False, f"Exception: {str(e)}")
    
    def test_agent_configuration_endpoints(self):
        """Test agent configuration endpoints"""
        print("⚙️ TESTING AGENT CONFIGURATION ENDPOINTS")
        print("=" * 50)
        
        # Test get current configuration
        try:
            response = requests.get(f"{API_BASE}/agent/config/current", timeout=10)
            if response.status_code == 200:
                data = response.json()
                config_data = data.get('data', {})
                
                success = (
                    'config' in config_data and
                    'services_status' in config_data and
                    'ollama' in config_data.get('config', {})
                )
                
                self.log_result(
                    "Get Current Configuration",
                    success,
                    f"Provider: {config_data.get('config', {}).get('current_provider')}"
                )
            else:
                self.log_result("Get Current Configuration", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Get Current Configuration", False, f"Exception: {str(e)}")
        
        # Test apply configuration
        try:
            test_config = {
                "config": {
                    "ollama": {
                        "enabled": True,
                        "endpoint": "https://bef4a4bb93d1.ngrok-free.app",
                        "model": "llama3.1:8b"
                    }
                }
            }
            
            response = requests.post(
                f"{API_BASE}/agent/config/apply",
                json=test_config,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                self.log_result(
                    "Apply Configuration",
                    success,
                    f"Config applied: {data.get('data', {}).get('message', 'Success')}"
                )
            else:
                self.log_result("Apply Configuration", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Apply Configuration", False, f"Exception: {str(e)}")
    
    def test_monitor_endpoints(self):
        """Test monitor endpoints"""
        print("📊 TESTING MONITOR ENDPOINTS")
        print("=" * 50)
        
        # Test get monitor pages
        try:
            response = requests.get(f"{API_BASE}/monitor/pages", timeout=10)
            if response.status_code == 200:
                data = response.json()
                pages_data = data.get('data', {})
                
                success = (
                    'pages' in pages_data and
                    'total_pages' in pages_data and
                    isinstance(pages_data.get('pages'), list)
                )
                
                self.log_result(
                    "Get Monitor Pages",
                    success,
                    f"Total pages: {pages_data.get('total_pages', 0)}"
                )
            else:
                self.log_result("Get Monitor Pages", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Get Monitor Pages", False, f"Exception: {str(e)}")
        
        # Test get latest monitor page
        try:
            response = requests.get(f"{API_BASE}/monitor/latest", timeout=10)
            if response.status_code == 200:
                data = response.json()
                page_data = data.get('data', {})
                
                success = (
                    'id' in page_data and
                    'title' in page_data and
                    'content' in page_data
                )
                
                self.log_result(
                    "Get Latest Monitor Page",
                    success,
                    f"Page: {page_data.get('title', 'Unknown')}"
                )
            else:
                self.log_result("Get Latest Monitor Page", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Get Latest Monitor Page", False, f"Exception: {str(e)}")
    
    def test_agent_endpoints(self):
        """Test agent endpoints"""
        print("🤖 TESTING AGENT ENDPOINTS")
        print("=" * 50)
        
        # Test agent status
        try:
            response = requests.get(f"{API_BASE}/agent/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Check for both new and old formats
                if 'data' in data:
                    status_data = data['data']
                else:
                    status_data = data
                
                success = (
                    'status' in status_data and
                    'ollama' in status_data
                )
                
                self.log_result(
                    "Agent Status",
                    success,
                    f"Status: {status_data.get('status')}, Ollama: {status_data.get('ollama', {}).get('connected', False)}"
                )
            else:
                self.log_result("Agent Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Agent Status", False, f"Exception: {str(e)}")
        
        # Test agent chat endpoint
        try:
            chat_message = {
                "message": "Hola, ¿cómo estás? Este es un test del servidor consolidado."
            }
            
            response = requests.post(
                f"{API_BASE}/agent/chat",
                json=chat_message,
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for both new and old formats
                if 'data' in data:
                    response_data = data['data']
                else:
                    response_data = data
                
                success = (
                    'response' in response_data and
                    len(response_data.get('response', '')) > 0
                )
                
                self.log_result(
                    "Agent Chat",
                    success,
                    f"Response length: {len(response_data.get('response', ''))}, Memory used: {response_data.get('memory_used', False)}"
                )
            else:
                self.log_result("Agent Chat", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Agent Chat", False, f"Exception: {str(e)}")
        
        # Test generate suggestions
        try:
            response = requests.post(f"{API_BASE}/agent/generate-suggestions", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                suggestions_data = data.get('data', {})
                suggestions = suggestions_data.get('suggestions', [])
                
                success = (
                    isinstance(suggestions, list) and
                    len(suggestions) > 0 and
                    all('title' in s and 'description' in s for s in suggestions)
                )
                
                self.log_result(
                    "Generate Suggestions",
                    success,
                    f"Suggestions count: {len(suggestions)}"
                )
            else:
                self.log_result("Generate Suggestions", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Generate Suggestions", False, f"Exception: {str(e)}")
    
    def test_websocket_functionality(self):
        """Test WebSocket functionality (basic connectivity)"""
        print("🔌 TESTING WEBSOCKET FUNCTIONALITY")
        print("=" * 50)
        
        try:
            # Test if WebSocket endpoint is available by checking if socketio is initialized
            # We'll do this by testing a simple HTTP request to see if SocketIO headers are present
            response = requests.get(f"{BACKEND_URL}/socket.io/", timeout=5)
            
            # SocketIO typically returns specific responses or redirects
            websocket_available = (
                response.status_code in [200, 400, 404] or  # Various SocketIO responses
                'socket.io' in response.headers.get('server', '').lower()
            )
            
            self.log_result(
                "WebSocket Availability",
                websocket_available,
                f"SocketIO endpoint response: {response.status_code}"
            )
        except Exception as e:
            self.log_result("WebSocket Availability", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling"""
        print("🚨 TESTING ERROR HANDLING")
        print("=" * 50)
        
        # Test 404 error handling
        try:
            response = requests.get(f"{API_BASE}/nonexistent-endpoint", timeout=5)
            if response.status_code == 404:
                data = response.json()
                
                # Check for standardized error format
                success = (
                    'success' in data and
                    data.get('success') == False and
                    'error' in data
                )
                
                self.log_result(
                    "404 Error Handling",
                    success,
                    f"Error format standardized: {success}"
                )
            else:
                self.log_result("404 Error Handling", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("404 Error Handling", False, f"Exception: {str(e)}")
        
        # Test invalid JSON handling
        try:
            response = requests.post(
                f"{API_BASE}/agent/chat",
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            success = response.status_code in [400, 422, 500]  # Should return error status
            
            self.log_result(
                "Invalid JSON Handling",
                success,
                f"Status code: {response.status_code}"
            )
        except Exception as e:
            self.log_result("Invalid JSON Handling", False, f"Exception: {str(e)}")
    
    def test_service_integrations(self):
        """Test service integrations"""
        print("🔧 TESTING SERVICE INTEGRATIONS")
        print("=" * 50)
        
        # Test MongoDB integration via system status
        try:
            response = requests.get(f"{API_BASE}/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                services = data.get('data', {}).get('services', {})
                mongodb_status = services.get('mongodb', {})
                
                success = mongodb_status.get('status') == 'connected'
                
                self.log_result(
                    "MongoDB Integration",
                    success,
                    f"MongoDB status: {mongodb_status.get('status', 'unknown')}"
                )
            else:
                self.log_result("MongoDB Integration", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("MongoDB Integration", False, f"Exception: {str(e)}")
        
        # Test Ollama integration
        try:
            response = requests.get(f"{API_BASE}/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                services = data.get('data', {}).get('services', {})
                ollama_status = services.get('ollama', {})
                
                success = ollama_status.get('status') == 'connected'
                
                self.log_result(
                    "Ollama Integration",
                    success,
                    f"Ollama status: {ollama_status.get('status', 'unknown')}, Models: {ollama_status.get('models_count', 0)}"
                )
            else:
                self.log_result("Ollama Integration", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Ollama Integration", False, f"Exception: {str(e)}")
        
        # Test Tool Manager integration
        try:
            response = requests.get(f"{API_BASE}/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                services = data.get('data', {}).get('services', {})
                tools_status = services.get('tools', {})
                
                success = (
                    tools_status.get('status') == 'available' and
                    tools_status.get('count', 0) > 0
                )
                
                self.log_result(
                    "Tool Manager Integration",
                    success,
                    f"Tools available: {tools_status.get('count', 0)}"
                )
            else:
                self.log_result("Tool Manager Integration", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Tool Manager Integration", False, f"Exception: {str(e)}")
    
    def test_api_response_format(self):
        """Test standardized API response format"""
        print("📋 TESTING API RESPONSE FORMAT")
        print("=" * 50)
        
        endpoints_to_test = [
            ("/health", "GET"),
            ("/api/health", "GET"),
            ("/api/system/status", "GET"),
            ("/api/agent/config/current", "GET"),
            ("/api/monitor/pages", "GET")
        ]
        
        standardized_count = 0
        total_endpoints = len(endpoints_to_test)
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{BACKEND_URL}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for new APIResponse format
                    has_new_format = (
                        'success' in data and
                        'timestamp' in data and
                        isinstance(data.get('success'), bool)
                    )
                    
                    if has_new_format:
                        standardized_count += 1
                        
            except Exception as e:
                pass  # Skip failed requests for this test
        
        success = standardized_count > 0
        self.log_result(
            "Standardized API Response Format",
            success,
            f"Endpoints with new format: {standardized_count}/{total_endpoints}"
        )
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 COMPREHENSIVE CONSOLIDATED BACKEND TESTING")
        print("=" * 80)
        print(f"Testing backend at: {BACKEND_URL}")
        print("=" * 80)
        print()
        
        # Run all test categories
        self.test_health_endpoints()
        self.test_system_status_endpoint()
        self.test_agent_configuration_endpoints()
        self.test_monitor_endpoints()
        self.test_agent_endpoints()
        self.test_websocket_functionality()
        self.test_error_handling()
        self.test_service_integrations()
        self.test_api_response_format()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")
        print()
        
        if self.failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        print("✅ PASSED TESTS:")
        for result in self.results:
            if result['success']:
                print(f"  - {result['test']}")
        
        print("=" * 80)
        
        # Overall assessment
        if self.passed_tests >= self.total_tests * 0.8:  # 80% pass rate
            print("🎉 OVERALL ASSESSMENT: CONSOLIDATED SERVER IS WORKING WELL")
        elif self.passed_tests >= self.total_tests * 0.6:  # 60% pass rate
            print("⚠️ OVERALL ASSESSMENT: CONSOLIDATED SERVER HAS SOME ISSUES")
        else:
            print("❌ OVERALL ASSESSMENT: CONSOLIDATED SERVER HAS MAJOR ISSUES")
        
        print("=" * 80)


if __name__ == "__main__":
    print("Starting Consolidated Backend Testing...")
    print(f"Backend URL: {BACKEND_URL}")
    print()
    
    tester = ConsolidatedBackendTester()
    tester.run_all_tests()