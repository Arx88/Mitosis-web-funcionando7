#!/usr/bin/env python3
"""
BACKEND TESTING SUITE FOR MITOSIS SYNCHRONIZATION ISSUE
Testing specific task synchronization between frontend and backend
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://7d400244-56cf-4207-9df0-dc8711a7609e.preview.emergentagent.com"
SPECIFIC_TASK_ID = "task-1754249098561-1-241"

class MitosisBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        
    def log_test(self, test_name, success, details, error=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'error': str(error) if error else None,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def test_specific_task_status(self):
        """Test the specific task status endpoint for the reported task"""
        try:
            url = f"{self.backend_url}/api/agent/get-task-status/{SPECIFIC_TASK_ID}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    task_status = data.get('status', 'unknown')
                    progress = data.get('progress', 0)
                    current_step = data.get('current_step')
                    completed_steps = data.get('completed_steps', 0)
                    total_steps = data.get('total_steps', 0)
                    
                    details = f"Status: {task_status}, Progress: {progress}%, Current Step: {current_step}, Completed: {completed_steps}/{total_steps}"
                    
                    # Check if this matches the reported issue
                    if completed_steps == 2 and total_steps == 4:
                        details += " - MATCHES REPORTED ISSUE: 2/4 steps completed"
                    
                    self.log_test("Specific Task Status Check", True, details)
                    return data
                else:
                    self.log_test("Specific Task Status Check", False, f"API returned success=false: {data}")
                    return None
            else:
                self.log_test("Specific Task Status Check", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Specific Task Status Check", False, "Request failed", e)
            return None

    def test_websocket_endpoint_availability(self):
        """Test if WebSocket endpoint is available"""
        try:
            # Test the WebSocket endpoint availability via HTTP
            url = f"{self.backend_url}/api/socket.io/"
            response = self.session.get(url, timeout=10)
            
            # SocketIO typically returns specific responses
            if response.status_code in [200, 400]:  # 400 is normal for HTTP requests to WebSocket endpoints
                self.log_test("WebSocket Endpoint Availability", True, f"WebSocket endpoint accessible (HTTP {response.status_code})")
                return True
            else:
                self.log_test("WebSocket Endpoint Availability", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Endpoint Availability", False, "Request failed", e)
            return False

    def test_task_execution_endpoint(self):
        """Test if task execution can be triggered"""
        try:
            url = f"{self.backend_url}/api/agent/start-task-execution/{SPECIFIC_TASK_ID}"
            response = self.session.post(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Task Execution Endpoint", True, f"Execution triggered: {data}")
                return data
            elif response.status_code == 404:
                self.log_test("Task Execution Endpoint", False, "Endpoint not found - this could be the synchronization issue")
                return None
            else:
                self.log_test("Task Execution Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Task Execution Endpoint", False, "Request failed", e)
            return None

    def test_step_progress_events(self):
        """Test if step progress events can be emitted"""
        try:
            # Try to trigger a step completion event
            url = f"{self.backend_url}/api/agent/emit-step-event"
            payload = {
                "task_id": SPECIFIC_TASK_ID,
                "event_type": "step_started",
                "step_data": {
                    "step": "step-3",
                    "status": "in_progress"
                }
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Step Progress Events", True, f"Event emission successful: {data}")
                return True
            elif response.status_code == 404:
                self.log_test("Step Progress Events", False, "Step event endpoint not found")
                return False
            else:
                self.log_test("Step Progress Events", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Step Progress Events", False, "Request failed", e)
            return False

    def test_backend_health(self):
        """Test backend health and service status"""
        try:
            url = f"{self.backend_url}/api/health"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                database = services.get('database', False)
                ollama = services.get('ollama', False)
                tools = services.get('tools', 0)
                
                details = f"Database: {database}, Ollama: {ollama}, Tools: {tools}"
                self.log_test("Backend Health Check", True, details)
                return data
            else:
                self.log_test("Backend Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Backend Health Check", False, "Request failed", e)
            return None

    def test_agent_status(self):
        """Test agent status endpoint"""
        try:
            url = f"{self.backend_url}/api/agent/status"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                ollama_info = data.get('ollama', {})
                tools_count = data.get('tools_count', 0)
                memory_info = data.get('memory', {})
                
                details = f"Ollama connected: {ollama_info.get('connected')}, Tools: {tools_count}, Memory enabled: {memory_info.get('enabled')}"
                self.log_test("Agent Status Check", True, details)
                return data
            else:
                self.log_test("Agent Status Check", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Agent Status Check", False, "Request failed", e)
            return None

    def test_create_test_task(self):
        """Create a test task to verify task creation and progress tracking"""
        try:
            url = f"{self.backend_url}/api/agent/chat"
            payload = {
                "message": "Test de sincronización frontend-backend",
                "memory_used": True
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                
                if task_id:
                    details = f"Test task created: {task_id}"
                    self.log_test("Test Task Creation", True, details)
                    
                    # Wait a moment and check task status
                    time.sleep(2)
                    return self.test_created_task_status(task_id)
                else:
                    self.log_test("Test Task Creation", False, "No task_id in response")
                    return None
            else:
                self.log_test("Test Task Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Test Task Creation", False, "Request failed", e)
            return None

    def test_created_task_status(self, task_id):
        """Test status of newly created task"""
        try:
            url = f"{self.backend_url}/api/agent/get-task-status/{task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    status = data.get('status', 'unknown')
                    progress = data.get('progress', 0)
                    
                    details = f"New task {task_id}: Status={status}, Progress={progress}%"
                    self.log_test("Created Task Status Check", True, details)
                    return data
                else:
                    self.log_test("Created Task Status Check", False, f"API returned success=false for new task")
                    return None
            else:
                self.log_test("Created Task Status Check", False, f"HTTP {response.status_code} for new task")
                return None
                
        except Exception as e:
            self.log_test("Created Task Status Check", False, "Request failed for new task", e)
            return None

    def run_synchronization_diagnosis(self):
        """Run comprehensive synchronization diagnosis"""
        print("🔍 MITOSIS BACKEND SYNCHRONIZATION DIAGNOSIS")
        print("=" * 60)
        print(f"Backend URL: {self.backend_url}")
        print(f"Specific Task ID: {SPECIFIC_TASK_ID}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Test 1: Backend Health
        print("1. Testing Backend Health...")
        self.test_backend_health()
        
        # Test 2: Agent Status
        print("2. Testing Agent Status...")
        self.test_agent_status()
        
        # Test 3: Specific Task Status (the reported issue)
        print("3. Testing Specific Task Status...")
        task_data = self.test_specific_task_status()
        
        # Test 4: WebSocket Availability
        print("4. Testing WebSocket Endpoint...")
        self.test_websocket_endpoint_availability()
        
        # Test 5: Task Execution Endpoint
        print("5. Testing Task Execution Endpoint...")
        self.test_task_execution_endpoint()
        
        # Test 6: Step Progress Events
        print("6. Testing Step Progress Events...")
        self.test_step_progress_events()
        
        # Test 7: Create Test Task
        print("7. Creating Test Task...")
        self.test_create_test_task()
        
        # Summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 SYNCHRONIZATION DIAGNOSIS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        # Critical issues
        critical_issues = []
        for result in self.test_results:
            if not result['success']:
                if 'Task Status Check' in result['test']:
                    critical_issues.append(f"❌ {result['test']}: {result['details'] or result['error']}")
                elif 'WebSocket' in result['test']:
                    critical_issues.append(f"⚠️ {result['test']}: {result['details'] or result['error']}")
                elif 'Task Execution' in result['test']:
                    critical_issues.append(f"❌ {result['test']}: {result['details'] or result['error']}")
        
        if critical_issues:
            print("🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("✅ No critical synchronization issues detected")
        
        print()
        print("📊 DIAGNOSIS COMPLETE")

if __name__ == "__main__":
    tester = MitosisBackendTester()
    results = tester.run_synchronization_diagnosis()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results if not result['success'])
    sys.exit(failed_tests)