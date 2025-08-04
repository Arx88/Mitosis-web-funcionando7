#!/usr/bin/env python3
"""
BACKEND TESTING SUITE FOR MITOSIS TASK DELETION FUNCTIONALITY
Testing complete task deletion functionality as requested by user
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://8573597c-1997-460c-b77a-6b973a0414e3.preview.emergentagent.com"

class MitosisTaskDeletionTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.created_task_id = None
        
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

    def test_1_create_test_task(self):
        """Step 1: Create a test task using POST /api/agent/chat"""
        try:
            print("🔄 Step 1: Creating test task with message 'Crear análisis de prueba para eliminar'")
            
            url = f"{self.backend_url}/api/agent/chat"
            payload = {
                "message": "Crear análisis de prueba para eliminar",
                "memory_used": True
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                
                if task_id:
                    self.created_task_id = task_id
                    details = f"Test task created successfully: {task_id}"
                    self.log_test("1. Create Test Task", True, details)
                    return task_id
                else:
                    self.log_test("1. Create Test Task", False, "No task_id in response")
                    return None
            else:
                self.log_test("1. Create Test Task", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("1. Create Test Task", False, "Request failed", e)
            return None

    def test_2_verify_task_created(self):
        """Step 2: Verify task was created using GET /api/agent/get-all-tasks"""
        try:
            print("🔄 Step 2: Verifying task appears in task list")
            
            url = f"{self.backend_url}/api/agent/get-all-tasks"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('tasks', [])
                
                # Look for our created task
                task_found = False
                for task in tasks:
                    # Check both task_id and id fields
                    task_id = task.get('task_id') or task.get('id')
                    if task_id == self.created_task_id:
                        task_found = True
                        task_title = task.get('title', 'No title')
                        task_status = task.get('status', 'unknown')
                        break
                
                if task_found:
                    details = f"Task found in list: {self.created_task_id} - Title: '{task_title}', Status: {task_status}"
                    self.log_test("2. Verify Task in List", True, details)
                    return True
                else:
                    available_tasks = [t.get('task_id') or t.get('id', 'no-id') for t in tasks]
                    details = f"Task {self.created_task_id} NOT found in list. Available tasks: {available_tasks[:5]}"
                    self.log_test("2. Verify Task in List", False, details)
                    return False
            else:
                self.log_test("2. Verify Task in List", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("2. Verify Task in List", False, "Request failed", e)
            return False

    def test_3_delete_task(self):
        """Step 3: Test DELETE /api/agent/delete-task/{task_id}"""
        try:
            print(f"🔄 Step 3: Deleting task {self.created_task_id}")
            
            url = f"{self.backend_url}/api/agent/delete-task/{self.created_task_id}"
            response = self.session.delete(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                message = data.get('message', 'No message')
                
                if success:
                    details = f"Task deleted successfully: {message}"
                    self.log_test("3. Delete Task", True, details)
                    return True
                else:
                    details = f"Delete request returned success=false: {message}"
                    self.log_test("3. Delete Task", False, details)
                    return False
            elif response.status_code == 404:
                self.log_test("3. Delete Task", False, "Delete endpoint not found (404)")
                return False
            else:
                self.log_test("3. Delete Task", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("3. Delete Task", False, "Request failed", e)
            return False

    def test_4_verify_task_deleted(self):
        """Step 4: Verify task was deleted using GET /api/agent/get-all-tasks"""
        try:
            print("🔄 Step 4: Verifying task no longer appears in task list")
            
            url = f"{self.backend_url}/api/agent/get-all-tasks"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('tasks', [])
                
                # Look for our deleted task
                task_found = False
                for task in tasks:
                    # Check both task_id and id fields
                    task_id = task.get('task_id') or task.get('id')
                    if task_id == self.created_task_id:
                        task_found = True
                        break
                
                if not task_found:
                    details = f"Task {self.created_task_id} successfully removed from list"
                    self.log_test("4. Verify Task Deleted", True, details)
                    return True
                else:
                    details = f"Task {self.created_task_id} STILL FOUND in list after deletion - This is the reported bug!"
                    self.log_test("4. Verify Task Deleted", False, details)
                    return False
            else:
                self.log_test("4. Verify Task Deleted", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("4. Verify Task Deleted", False, "Request failed", e)
            return False

    def test_5_delete_nonexistent_task(self):
        """Step 5: Test edge case - delete non-existent task"""
        try:
            print("🔄 Step 5: Testing edge case - deleting non-existent task")
            
            fake_task_id = "nonexistent-task-12345"
            url = f"{self.backend_url}/api/agent/delete-task/{fake_task_id}"
            response = self.session.delete(url, timeout=10)
            
            if response.status_code == 404:
                details = f"Correctly returned 404 for non-existent task: {fake_task_id}"
                self.log_test("5. Delete Non-existent Task", True, details)
                return True
            elif response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                if not success:
                    details = f"Correctly returned success=false for non-existent task"
                    self.log_test("5. Delete Non-existent Task", True, details)
                    return True
                else:
                    details = f"Incorrectly returned success=true for non-existent task"
                    self.log_test("5. Delete Non-existent Task", False, details)
                    return False
            else:
                details = f"Unexpected response for non-existent task: HTTP {response.status_code}"
                self.log_test("5. Delete Non-existent Task", False, details)
                return False
                
        except Exception as e:
            self.log_test("5. Delete Non-existent Task", False, "Request failed", e)
            return False

    def test_backend_health(self):
        """Test backend health before running deletion tests"""
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

    def run_task_deletion_tests(self):
        """Run comprehensive task deletion functionality tests"""
        print("🗑️ MITOSIS TASK DELETION FUNCTIONALITY TEST")
        print("=" * 60)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Pre-test: Backend Health
        print("0. Testing Backend Health...")
        health_ok = self.test_backend_health()
        if not health_ok:
            print("❌ Backend health check failed. Aborting tests.")
            return self.test_results
        
        # Test 1: Create test task
        print("\n" + "="*50)
        task_id = self.test_1_create_test_task()
        if not task_id:
            print("❌ Failed to create test task. Aborting remaining tests.")
            self.print_summary()
            return self.test_results
        
        # Wait a moment for task to be processed
        print("⏳ Waiting 3 seconds for task to be processed...")
        time.sleep(3)
        
        # Test 2: Verify task was created
        print("\n" + "="*50)
        task_verified = self.test_2_verify_task_created()
        if not task_verified:
            print("⚠️ Task not found in list, but continuing with deletion test...")
        
        # Test 3: Delete the task
        print("\n" + "="*50)
        delete_success = self.test_3_delete_task()
        if not delete_success:
            print("❌ Failed to delete task. This indicates the deletion endpoint issue.")
        
        # Wait a moment for deletion to be processed
        print("⏳ Waiting 2 seconds for deletion to be processed...")
        time.sleep(2)
        
        # Test 4: Verify task was deleted
        print("\n" + "="*50)
        self.test_4_verify_task_deleted()
        
        # Test 5: Edge case - delete non-existent task
        print("\n" + "="*50)
        self.test_5_delete_nonexistent_task()
        
        # Summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 TASK DELETION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        # Analyze results for the specific user issue
        deletion_working = True
        critical_issues = []
        
        for result in self.test_results:
            if not result['success']:
                if 'Delete Task' in result['test']:
                    critical_issues.append(f"❌ {result['test']}: {result['details'] or result['error']}")
                    deletion_working = False
                elif 'Verify Task Deleted' in result['test']:
                    critical_issues.append(f"🚨 CRITICAL: {result['test']}: {result['details'] or result['error']}")
                    deletion_working = False
                elif 'Create Test Task' in result['test']:
                    critical_issues.append(f"❌ {result['test']}: {result['details'] or result['error']}")
        
        if critical_issues:
            print("🚨 ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("✅ All task deletion tests passed successfully")
        
        print()
        
        # Specific analysis for user's reported issue
        if deletion_working:
            print("✅ TASK DELETION FUNCTIONALITY: WORKING CORRECTLY")
            print("   - Tasks can be deleted via DELETE /api/agent/delete-task/{task_id}")
            print("   - Deleted tasks are properly removed from the task list")
            print("   - The reported issue (tasks reappearing after reload) appears to be RESOLVED")
        else:
            print("❌ TASK DELETION FUNCTIONALITY: ISSUES DETECTED")
            print("   - This confirms the user's reported issue")
            print("   - Tasks may not be properly deleted or may reappear after reload")
        
        print()
        print("📊 TASK DELETION DIAGNOSIS COMPLETE")

if __name__ == "__main__":
    tester = MitosisTaskDeletionTester()
    results = tester.run_task_deletion_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results if not result['success'])
    sys.exit(failed_tests)