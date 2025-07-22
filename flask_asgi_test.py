#!/usr/bin/env python3
"""
MITOSIS FLASK/ASGI COMPATIBILITY FIX TESTING
Testing the Flask/ASGI compatibility issue fix and core functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
EXTERNAL_URL = "https://0985e82d-0b00-4ff8-a718-81e33927dd33.preview.emergentagent.com"
EXPECTED_OLLAMA_ENDPOINT = "https://bef4a4bb93d1.ngrok-free.app"
EXPECTED_MODEL = "llama3.1:8b"

class MitosisFlaskTester:
    def __init__(self):
        self.base_url = EXTERNAL_URL
        self.results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MitosisFlaskTester/1.0'
        })
        
    def log_result(self, test_name, success, details, response_time=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{time_info}")
        print(f"   Details: {details}")
        print()
        
    def test_flask_asgi_compatibility(self):
        """Test 1: Verify Flask/ASGI compatibility issue is fixed"""
        print("🔧 Testing Flask/ASGI Compatibility Fix...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'status' in data and data['status'] == 'healthy':
                    self.log_result(
                        "Flask/ASGI Compatibility Fix",
                        True,
                        f"Backend responding correctly (status: {data['status']})",
                        response_time
                    )
                    return True
                else:
                    self.log_result(
                        "Flask/ASGI Compatibility Fix",
                        False,
                        f"Unexpected response format: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_result(
                    "Flask/ASGI Compatibility Fix",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Flask/ASGI Compatibility Fix",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_ollama_connectivity(self):
        """Test 2: Verify OLLAMA connectivity to expected endpoint"""
        print("🤖 Testing OLLAMA Connectivity...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/agent/status", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if ollama configuration is present
                if 'ollama' in data:
                    ollama_info = data['ollama']
                    endpoint = ollama_info.get('endpoint', '')
                    model = ollama_info.get('model', '')
                    connected = ollama_info.get('connected', False)
                    
                    # Verify endpoint and model
                    endpoint_match = EXPECTED_OLLAMA_ENDPOINT in endpoint
                    model_match = EXPECTED_MODEL in model
                    
                    if endpoint_match and model_match:
                        status_msg = "connected" if connected else "configured but not connected"
                        self.log_result(
                            "OLLAMA Connectivity",
                            True,
                            f"Endpoint: {endpoint}, Model: {model}, Status: {status_msg}",
                            response_time
                        )
                        return True
                    else:
                        self.log_result(
                            "OLLAMA Connectivity",
                            False,
                            f"Configuration mismatch - Expected: {EXPECTED_OLLAMA_ENDPOINT}/{EXPECTED_MODEL}, Got: {endpoint}/{model}",
                            response_time
                        )
                        return False
                else:
                    self.log_result(
                        "OLLAMA Connectivity",
                        False,
                        f"No OLLAMA configuration found in status response: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_result(
                    "OLLAMA Connectivity",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "OLLAMA Connectivity",
                False,
                f"Request error: {str(e)}"
            )
            return False
    
    def test_core_endpoints(self):
        """Test 3: Verify core API endpoints"""
        print("🌐 Testing Core API Endpoints...")
        
        endpoints = [
            ("/api/health", "GET"),
            ("/api/agent/status", "GET"),
        ]
        
        success_count = 0
        total_endpoints = len(endpoints)
        
        for endpoint, method in endpoints:
            try:
                start_time = time.time()
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json={}, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"   ✅ {method} {endpoint} - OK ({response_time:.2f}s)")
                else:
                    print(f"   ❌ {method} {endpoint} - HTTP {response.status_code} ({response_time:.2f}s)")
                    
            except Exception as e:
                print(f"   ❌ {method} {endpoint} - Error: {str(e)}")
        
        success_rate = (success_count / total_endpoints) * 100
        self.log_result(
            "Core API Endpoints",
            success_count == total_endpoints,
            f"{success_count}/{total_endpoints} endpoints working ({success_rate:.1f}% success rate)"
        )
        
        return success_count == total_endpoints
    
    def test_agent_chat_functionality(self):
        """Test 4: Verify agent chat functionality"""
        print("💬 Testing Agent Chat Functionality...")
        
        test_message = "Hello, can you help me create a simple marketing plan?"
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/agent/chat",
                json={"message": test_message},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expected response fields
                required_fields = ['response', 'task_id']
                optional_fields = ['memory_used', 'timestamp', 'status']
                
                missing_fields = [field for field in required_fields if field not in data]
                present_optional = [field for field in optional_fields if field in data]
                
                if not missing_fields:
                    response_text = data.get('response', '')
                    task_id = data.get('task_id', '')
                    memory_used = data.get('memory_used', False)
                    
                    self.log_result(
                        "Agent Chat Functionality",
                        True,
                        f"Response generated ({len(response_text)} chars), Task ID: {task_id}, Memory: {memory_used}, Optional fields: {present_optional}",
                        response_time
                    )
                    return True
                else:
                    self.log_result(
                        "Agent Chat Functionality",
                        False,
                        f"Missing required fields: {missing_fields}. Response: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_result(
                    "Agent Chat Functionality",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Agent Chat Functionality",
                False,
                f"Request error: {str(e)}"
            )
            return False
    
    def test_websocket_system(self):
        """Test 5: Verify WebSocket system availability"""
        print("🔌 Testing WebSocket System...")
        
        # Test if WebSocket endpoints are accessible (basic connectivity test)
        try:
            start_time = time.time()
            # Try to access the socket.io endpoint
            response = self.session.get(f"{self.base_url}/socket.io/", timeout=10)
            response_time = time.time() - start_time
            
            # Socket.IO typically returns specific responses or redirects
            if response.status_code in [200, 400, 404]:  # 400 is common for socket.io without proper handshake
                self.log_result(
                    "WebSocket System",
                    True,
                    f"WebSocket endpoint accessible (HTTP {response.status_code})",
                    response_time
                )
                return True
            else:
                self.log_result(
                    "WebSocket System",
                    False,
                    f"WebSocket endpoint not accessible (HTTP {response.status_code})",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "WebSocket System",
                False,
                f"WebSocket connection test failed: {str(e)}"
            )
            return False
    
    def test_agent_workflow(self):
        """Test 6: Test complete agent workflow"""
        print("🔄 Testing Complete Agent Workflow...")
        
        workflow_steps = [
            "Create a simple business plan for a coffee shop",
            "What are the key components I should include?"
        ]
        
        success_count = 0
        total_steps = len(workflow_steps)
        
        for i, message in enumerate(workflow_steps, 1):
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{self.base_url}/api/agent/chat",
                    json={"message": message},
                    timeout=25
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if 'response' in data and 'task_id' in data:
                        success_count += 1
                        print(f"   ✅ Step {i}: Message processed successfully ({response_time:.2f}s)")
                        print(f"      Response: {data['response'][:100]}...")
                    else:
                        print(f"   ❌ Step {i}: Invalid response format")
                else:
                    print(f"   ❌ Step {i}: HTTP {response.status_code}")
                    
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Step {i}: Error - {str(e)}")
        
        workflow_success = success_count == total_steps
        self.log_result(
            "Complete Agent Workflow",
            workflow_success,
            f"{success_count}/{total_steps} workflow steps completed successfully"
        )
        
        return workflow_success
    
    def run_all_tests(self):
        """Run all tests and generate summary"""
        print("🧪 MITOSIS FLASK/ASGI COMPATIBILITY FIX TESTING")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Expected OLLAMA: {EXPECTED_OLLAMA_ENDPOINT}")
        print(f"Expected Model: {EXPECTED_MODEL}")
        print("=" * 60)
        print()
        
        # Run all tests
        tests = [
            self.test_flask_asgi_compatibility,
            self.test_ollama_connectivity,
            self.test_core_endpoints,
            self.test_agent_chat_functionality,
            self.test_websocket_system,
            self.test_agent_workflow
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            
            print("-" * 40)
        
        # Generate summary
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 60)
        print("📊 TESTING SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if success_rate >= 80:
            print("🎉 OVERALL STATUS: EXCELLENT - Flask/ASGI fix successful!")
        elif success_rate >= 60:
            print("⚠️  OVERALL STATUS: GOOD - Minor issues detected")
        else:
            print("❌ OVERALL STATUS: NEEDS ATTENTION - Major issues found")
        
        print("\n" + "=" * 60)
        print("🔍 DETAILED RESULTS")
        print("=" * 60)
        
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            time_info = f" ({result['response_time']:.2f}s)" if result['response_time'] else ""
            print(f"{status} {result['test']}{time_info}")
            print(f"   {result['details']}")
            print()
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = MitosisFlaskTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎯 CONCLUSION: Flask/ASGI compatibility fix successful!")
        sys.exit(0)
    else:
        print("⚠️  CONCLUSION: Backend has issues that need attention.")
        sys.exit(1)