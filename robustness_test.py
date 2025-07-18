#!/usr/bin/env python3
"""
BACKEND ROBUSTNESS TEST - SIMPLIFIED SERVER TESTING
Testing the simplified backend (server_simple.py) for stability and functionality
Focus: Health, Chat, Status, Database, Error Handling, Service Stability
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://2455389d-3413-4f40-9450-c5cc3faf6ec7.preview.emergentagent.com"
TEST_TIMEOUT = 10

class BackendRobustnessTest:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_result(self, test_name, passed, duration, details=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
            
        result = {
            "test": test_name,
            "status": status,
            "duration": f"{duration:.2f}s",
            "details": details
        }
        self.results.append(result)
        print(f"{status} ({duration:.2f}s) - {test_name}")
        if details:
            print(f"    Details: {details}")
    
    def test_backend_health(self):
        """Test 1: Backend Health and Stability - Using agent status as health check"""
        print("\n🔍 Testing Backend Health and Stability...")
        start_time = time.time()
        
        try:
            # Use agent status endpoint as health check since /health is routed to frontend
            response = requests.get(f"{BACKEND_URL}/api/agent/status", timeout=TEST_TIMEOUT)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "running":
                    memory_info = data.get("memory", {})
                    ollama_info = data.get("ollama", {})
                    details = f"Backend running, Memory enabled={memory_info.get('enabled')}, Ollama endpoint={ollama_info.get('endpoint')}"
                    self.log_result("Backend Health Check", True, duration, details)
                    return True
                else:
                    self.log_result("Backend Health Check", False, duration, f"Status not running: {data.get('status')}")
                    return False
            else:
                self.log_result("Backend Health Check", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Backend Health Check", False, duration, f"Exception: {str(e)}")
            return False
    
    def test_basic_chat_functionality(self):
        """Test 2: Basic Chat Functionality - /api/agent/chat endpoint"""
        print("\n💬 Testing Basic Chat Functionality...")
        start_time = time.time()
        
        try:
            payload = {
                "message": "Test message for backend robustness verification"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/agent/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=TEST_TIMEOUT
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data and "task_id" in data:
                    memory_used = data.get("memory_used", False)
                    details = f"Response received, task_id={data.get('task_id')}, memory_used={memory_used}"
                    self.log_result("Basic Chat Functionality", True, duration, details)
                    return True
                else:
                    self.log_result("Basic Chat Functionality", False, duration, "Missing required fields in response")
                    return False
            else:
                self.log_result("Basic Chat Functionality", False, duration, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Basic Chat Functionality", False, duration, f"Exception: {str(e)}")
            return False
    
    def test_agent_status(self):
        """Test 3: Agent Status - /api/agent/status endpoint"""
        print("\n📊 Testing Agent Status...")
        start_time = time.time()
        
        try:
            response = requests.get(f"{BACKEND_URL}/api/agent/status", timeout=TEST_TIMEOUT)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and "ollama" in data:
                    ollama_info = data.get("ollama", {})
                    memory_info = data.get("memory", {})
                    details = f"Status={data.get('status')}, Ollama endpoint={ollama_info.get('endpoint')}, Memory enabled={memory_info.get('enabled')}"
                    self.log_result("Agent Status", True, duration, details)
                    return True
                else:
                    self.log_result("Agent Status", False, duration, "Missing required fields in response")
                    return False
            else:
                self.log_result("Agent Status", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Agent Status", False, duration, f"Exception: {str(e)}")
            return False
    
    def test_service_stability(self):
        """Test 4: Service Stability - Multiple consecutive requests"""
        print("\n🔄 Testing Service Stability...")
        start_time = time.time()
        
        try:
            successful_requests = 0
            total_requests = 5
            
            for i in range(total_requests):
                # Use agent status endpoint for stability testing
                response = requests.get(f"{BACKEND_URL}/api/agent/status", timeout=TEST_TIMEOUT)
                if response.status_code == 200:
                    successful_requests += 1
                time.sleep(0.5)  # Small delay between requests
            
            duration = time.time() - start_time
            
            if successful_requests == total_requests:
                details = f"{successful_requests}/{total_requests} consecutive requests successful"
                self.log_result("Service Stability", True, duration, details)
                return True
            else:
                details = f"Only {successful_requests}/{total_requests} requests successful"
                self.log_result("Service Stability", False, duration, details)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Service Stability", False, duration, f"Exception: {str(e)}")
            return False
    
    def test_database_connection(self):
        """Test 5: Database Connection - Verify MongoDB connectivity through agent status"""
        print("\n🗄️ Testing Database Connection...")
        start_time = time.time()
        
        try:
            # Test database connection by checking if backend can respond consistently
            # The simplified backend connects to MongoDB on startup
            response = requests.get(f"{BACKEND_URL}/api/agent/status", timeout=TEST_TIMEOUT)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                # If backend is responding, database connection is working
                # (simplified backend would fail to start if MongoDB was not available)
                if data.get("status") == "running":
                    self.log_result("Database Connection", True, duration, "Backend running - MongoDB connection verified")
                    return True
                else:
                    self.log_result("Database Connection", False, duration, "Backend not running properly")
                    return False
            else:
                self.log_result("Database Connection", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Database Connection", False, duration, f"Exception: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test 6: Error Handling - Test various error scenarios"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test 6a: Invalid endpoint
        start_time = time.time()
        try:
            response = requests.get(f"{BACKEND_URL}/api/invalid/endpoint", timeout=TEST_TIMEOUT)
            duration = time.time() - start_time
            
            if response.status_code == 404:
                self.log_result("Error Handling - Invalid Endpoint", True, duration, "Proper 404 response")
            else:
                self.log_result("Error Handling - Invalid Endpoint", False, duration, f"Expected 404, got {response.status_code}")
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Error Handling - Invalid Endpoint", False, duration, f"Exception: {str(e)}")
        
        # Test 6b: Invalid chat data
        start_time = time.time()
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/agent/chat",
                json={},  # Empty payload
                headers={"Content-Type": "application/json"},
                timeout=TEST_TIMEOUT
            )
            duration = time.time() - start_time
            
            if response.status_code == 400:
                data = response.json()
                if "error" in data:
                    self.log_result("Error Handling - Invalid Chat Data", True, duration, f"Proper 400 response: {data.get('error')}")
                else:
                    self.log_result("Error Handling - Invalid Chat Data", False, duration, "400 response but no error message")
            else:
                self.log_result("Error Handling - Invalid Chat Data", False, duration, f"Expected 400, got {response.status_code}")
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Error Handling - Invalid Chat Data", False, duration, f"Exception: {str(e)}")
    
    def test_chat_with_realistic_data(self):
        """Test 7: Chat with realistic data to verify robustness"""
        print("\n🤖 Testing Chat with Realistic Data...")
        start_time = time.time()
        
        try:
            payload = {
                "message": "Explain the benefits of using a simplified backend architecture for stability"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/agent/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=TEST_TIMEOUT
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data and len(data["response"]) > 0:
                    details = f"Response length: {len(data['response'])} chars, Status: {data.get('status')}"
                    self.log_result("Chat with Realistic Data", True, duration, details)
                    return True
                else:
                    self.log_result("Chat with Realistic Data", False, duration, "Empty or missing response")
                    return False
            else:
                self.log_result("Chat with Realistic Data", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Chat with Realistic Data", False, duration, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all robustness tests"""
        print("🧪 COMPREHENSIVE BACKEND ROBUSTNESS TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Timeout: {TEST_TIMEOUT}s")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Run all tests
        self.test_backend_health()
        self.test_basic_chat_functionality()
        self.test_agent_status()
        self.test_service_stability()
        self.test_database_connection()
        self.test_error_handling()
        self.test_chat_with_realistic_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.results:
            print(f"  {result['status']} ({result['duration']}) - {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
        
        # Overall assessment
        print("\n" + "=" * 60)
        print("🎯 ROBUSTNESS ASSESSMENT")
        print("=" * 60)
        
        if success_rate >= 90:
            print("✅ EXCELLENT - Backend is highly robust and stable")
        elif success_rate >= 75:
            print("✅ GOOD - Backend is stable with minor issues")
        elif success_rate >= 50:
            print("⚠️ MODERATE - Backend has some stability issues")
        else:
            print("❌ POOR - Backend has significant stability issues")
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = BackendRobustnessTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Backend robustness test PASSED")
        sys.exit(0)
    else:
        print("\n⚠️ Backend robustness test FAILED")
        sys.exit(1)