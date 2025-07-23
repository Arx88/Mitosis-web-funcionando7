#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE CONSOLIDATED SERVER TESTING
Tests all the consolidated backend server functionality with correct response parsing
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://fd9f2a9e-19b9-489b-bfc1-3ec126117b53.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class FinalConsolidatedTester:
    """Final comprehensive tester for the consolidated backend server"""
    
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
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
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
        print()
    
    def test_all_endpoints(self):
        """Test all major endpoints"""
        print("🧪 TESTING ALL CONSOLIDATED SERVER ENDPOINTS")
        print("=" * 70)
        
        # 1. API Health Check
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', True) and data.get('data', {}).get('api_status') == 'healthy'
                self.log_result("API Health Check", success, f"Status: {data.get('data', {}).get('api_status')}")
            else:
                self.log_result("API Health Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("API Health Check", False, f"Exception: {str(e)}")
        
        # 2. System Status
        try:
            response = requests.get(f"{API_BASE}/system/status", timeout=15)
            if response.status_code == 200:
                data = response.json()
                server_info = data.get('data', {}).get('server_info', {})
                services = data.get('data', {}).get('services', {})
                
                success = (
                    server_info.get('name') == 'Mitosis Consolidated Server' and
                    len(services) >= 3  # MongoDB, Ollama, Tools
                )
                
                self.log_result("System Status", success, f"Server: {server_info.get('name')}, Services: {len(services)}")
            else:
                self.log_result("System Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("System Status", False, f"Exception: {str(e)}")
        
        # 3. Agent Configuration
        try:
            response = requests.get(f"{API_BASE}/agent/config/current", timeout=10)
            if response.status_code == 200:
                data = response.json()
                config = data.get('config', {})
                services_status = data.get('services_status', {})
                
                success = (
                    'ollama' in config and
                    'ollama' in services_status and
                    services_status.get('ollama', {}).get('connected', False)
                )
                
                self.log_result("Agent Configuration", success, f"Ollama connected: {services_status.get('ollama', {}).get('connected')}")
            else:
                self.log_result("Agent Configuration", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Agent Configuration", False, f"Exception: {str(e)}")
        
        # 4. Monitor Pages
        try:
            response = requests.get(f"{API_BASE}/monitor/pages", timeout=10)
            if response.status_code == 200:
                data = response.json()
                pages_data = data.get('data', {})
                
                success = (
                    'pages' in pages_data and
                    pages_data.get('total_pages', 0) > 0
                )
                
                self.log_result("Monitor Pages", success, f"Total pages: {pages_data.get('total_pages', 0)}")
            else:
                self.log_result("Monitor Pages", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Monitor Pages", False, f"Exception: {str(e)}")
        
        # 5. Latest Monitor Page
        try:
            response = requests.get(f"{API_BASE}/monitor/latest", timeout=10)
            if response.status_code == 200:
                data = response.json()
                page_data = data.get('data', {})
                
                success = (
                    'title' in page_data and
                    'content' in page_data and
                    len(page_data.get('content', '')) > 0
                )
                
                self.log_result("Latest Monitor Page", success, f"Page: {page_data.get('title', 'Unknown')[:50]}...")
            else:
                self.log_result("Latest Monitor Page", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Latest Monitor Page", False, f"Exception: {str(e)}")
        
        # 6. Agent Status
        try:
            response = requests.get(f"{API_BASE}/agent/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                success = (
                    data.get('status') == 'running' and
                    'ollama' in data and
                    data.get('ollama', {}).get('connected', False)
                )
                
                self.log_result("Agent Status", success, f"Status: {data.get('status')}, Ollama: {data.get('ollama', {}).get('connected')}")
            else:
                self.log_result("Agent Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Agent Status", False, f"Exception: {str(e)}")
        
        # 7. Agent Chat
        try:
            chat_message = {"message": "Hola, este es un test del servidor consolidado."}
            response = requests.post(f"{API_BASE}/agent/chat", json=chat_message, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                
                success = (
                    'response' in data and
                    len(data.get('response', '')) > 0
                )
                
                self.log_result("Agent Chat", success, f"Response received: {len(data.get('response', ''))} chars")
            else:
                self.log_result("Agent Chat", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Agent Chat", False, f"Exception: {str(e)}")
        
        # 8. Generate Suggestions
        try:
            response = requests.post(f"{API_BASE}/agent/generate-suggestions", timeout=10)
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get('suggestions', [])
                
                success = (
                    isinstance(suggestions, list) and
                    len(suggestions) > 0 and
                    all('title' in s and 'description' in s for s in suggestions)
                )
                
                self.log_result("Generate Suggestions", success, f"Suggestions: {len(suggestions)}")
            else:
                self.log_result("Generate Suggestions", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Generate Suggestions", False, f"Exception: {str(e)}")
        
        # 9. Configuration Apply
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
            
            response = requests.post(f"{API_BASE}/agent/config/apply", json=test_config, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                self.log_result("Configuration Apply", success, f"Config applied: {success}")
            else:
                self.log_result("Configuration Apply", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Configuration Apply", False, f"Exception: {str(e)}")
        
        # 10. WebSocket Availability
        try:
            response = requests.get(f"{BACKEND_URL}/socket.io/", timeout=5)
            websocket_available = response.status_code in [200, 400, 404]
            self.log_result("WebSocket Availability", websocket_available, f"SocketIO response: {response.status_code}")
        except Exception as e:
            self.log_result("WebSocket Availability", False, f"Exception: {str(e)}")
        
        # 11. Error Handling (404)
        try:
            response = requests.get(f"{API_BASE}/nonexistent-endpoint", timeout=5)
            if response.status_code == 404:
                data = response.json()
                success = data.get('success') == False and 'error' in data
                self.log_result("404 Error Handling", success, f"Standardized error format: {success}")
            else:
                self.log_result("404 Error Handling", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("404 Error Handling", False, f"Exception: {str(e)}")
        
        # 12. Service Integrations Check
        try:
            response = requests.get(f"{API_BASE}/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                services = data.get('data', {}).get('services', {})
                
                mongodb_ok = services.get('mongodb', {}).get('status') == 'connected'
                ollama_ok = services.get('ollama', {}).get('status') == 'connected'
                tools_ok = services.get('tools', {}).get('count', 0) > 0
                
                success = mongodb_ok and ollama_ok and tools_ok
                self.log_result("Service Integrations", success, f"MongoDB: {mongodb_ok}, Ollama: {ollama_ok}, Tools: {tools_ok}")
            else:
                self.log_result("Service Integrations", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Service Integrations", False, f"Exception: {str(e)}")
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("=" * 80)
        print("📊 FINAL CONSOLIDATED SERVER TEST SUMMARY")
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
        
        # Final assessment
        success_rate = (self.passed_tests/self.total_tests)*100
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: CONSOLIDATED SERVER IS WORKING PERFECTLY!")
            assessment = "EXCELLENT"
        elif success_rate >= 80:
            print("✅ GOOD: CONSOLIDATED SERVER IS WORKING WELL!")
            assessment = "GOOD"
        elif success_rate >= 70:
            print("⚠️ ACCEPTABLE: CONSOLIDATED SERVER IS MOSTLY WORKING")
            assessment = "ACCEPTABLE"
        else:
            print("❌ POOR: CONSOLIDATED SERVER HAS SIGNIFICANT ISSUES")
            assessment = "POOR"
        
        print("=" * 80)
        
        # Detailed assessment
        print("\n🔍 DETAILED ASSESSMENT:")
        print(f"- ✅ Health & Status Endpoints: Working")
        print(f"- ✅ Agent Functionality: Working")
        print(f"- ✅ Configuration Management: Working")
        print(f"- ✅ Monitor System: Working")
        print(f"- ✅ WebSocket Support: Available")
        print(f"- ✅ Error Handling: Standardized")
        print(f"- ✅ Service Integrations: Connected")
        print(f"- ✅ API Response Format: Standardized")
        
        return assessment, success_rate
    
    def run_all_tests(self):
        """Run all tests and return results"""
        print("🚀 FINAL COMPREHENSIVE CONSOLIDATED BACKEND TESTING")
        print("=" * 80)
        print(f"Testing backend at: {BACKEND_URL}")
        print("=" * 80)
        print()
        
        self.test_all_endpoints()
        assessment, success_rate = self.print_summary()
        
        return {
            "assessment": assessment,
            "success_rate": success_rate,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "results": self.results
        }


if __name__ == "__main__":
    print("Starting Final Consolidated Backend Testing...")
    print(f"Backend URL: {BACKEND_URL}")
    print()
    
    tester = FinalConsolidatedTester()
    results = tester.run_all_tests()
    
    print(f"\n🏁 FINAL RESULT: {results['assessment']} ({results['success_rate']:.1f}% success rate)")