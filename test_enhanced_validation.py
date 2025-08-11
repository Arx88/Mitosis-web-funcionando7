#!/usr/bin/env python3
"""
FOCUSED TEST FOR ENHANCED STEP VALIDATION SYSTEM
Testing the specific issue reported: Enhanced Step Validator not working (0% functionality)
"""

import requests
import json
import time
import sys
import subprocess
from datetime import datetime

# Configuration
BACKEND_URL = "https://b9e4a7d6-6664-404f-9a00-f2c8ca5f31cd.preview.emergentagent.com"

class EnhancedValidationTester:
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

    def test_1_backend_health(self):
        """Test 1: Backend Health Check"""
        try:
            print("🔄 Test 1: Checking backend health endpoints")
            
            url = f"{self.backend_url}/api/health"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                database = services.get('database', False)
                ollama = services.get('ollama', False)
                tools = services.get('tools', 0)
                
                details = f"Database: {database}, Ollama: {ollama}, Tools: {tools}"
                self.log_test("1. Backend Health Check", True, details)
                return True
            else:
                self.log_test("1. Backend Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("1. Backend Health Check", False, "Request failed", e)
            return False

    def test_2_create_political_research_task(self):
        """Test 2: Create Political Research Task - Should Trigger Enhanced Validation"""
        try:
            print("🔄 Test 2: Creating political research task to trigger enhanced validation")
            
            url = f"{self.backend_url}/api/agent/chat"
            payload = {
                "message": "Realizar búsquedas en fuentes confiables sobre biografía, trayectoria política, ideología y declaraciones públicas de Javier Milei",
                "task_id": f"test-enhanced-validation-{int(time.time())}"
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id') or payload['task_id']
                
                if task_id:
                    self.created_task_id = task_id
                    details = f"Political research task created successfully: {task_id}"
                    self.log_test("2. Create Political Research Task", True, details)
                    return task_id
                else:
                    self.log_test("2. Create Political Research Task", False, f"No task_id in response: {data}")
                    return None
            else:
                self.log_test("2. Create Political Research Task", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("2. Create Political Research Task", False, "Request failed", e)
            return None

    def test_3_execute_step_1(self):
        """Test 3: Execute Step 1 to trigger enhanced validation"""
        try:
            print("🔄 Test 3: Executing Step 1 to trigger enhanced validation")
            
            if not self.created_task_id:
                self.log_test("3. Execute Step 1", False, "No task_id available")
                return False
            
            # First get the task plan to find step 1
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                self.log_test("3. Execute Step 1", False, f"Could not get task status: HTTP {response.status_code}")
                return False
            
            task_data = response.json()
            plan = task_data.get('plan', [])
            
            if not plan:
                self.log_test("3. Execute Step 1", False, "No plan found in task")
                return False
            
            step_1 = plan[0]  # First step
            step_1_id = step_1.get('id')
            
            if not step_1_id:
                self.log_test("3. Execute Step 1", False, "Step 1 has no ID")
                return False
            
            # Execute step 1
            url = f"{self.backend_url}/api/agent/execute-step-detailed/{self.created_task_id}/{step_1_id}"
            response = self.session.post(url, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                
                if success:
                    details = f"Step 1 executed successfully: {step_1.get('title', 'Unknown step')}"
                    self.log_test("3. Execute Step 1", True, details)
                    return True
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_test("3. Execute Step 1", False, f"Step execution failed: {error_msg}")
                    return False
            else:
                self.log_test("3. Execute Step 1", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("3. Execute Step 1", False, "Request failed", e)
            return False

    def test_4_check_enhanced_validation_logs(self):
        """Test 4: Check backend logs for enhanced validation activity"""
        try:
            print("🔄 Test 4: Checking backend logs for enhanced validation activity")
            
            # Check supervisor logs for enhanced validation patterns
            cmd = "tail -n 100 /var/log/supervisor/backend.out.log | grep -E 'DETECTADO PASO 1 DE INVESTIGACIÓN|enhanced_step_validator|EnhancedStepValidator|VALIDACIÓN SUPER ESTRICTA|validate_step_1_with_enhanced_validator'"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                log_lines = result.stdout.strip().split('\n')
                enhanced_validator_calls = len([line for line in log_lines if 'enhanced_step_validator' in line or 'EnhancedStepValidator' in line])
                political_research_detected = any('DETECTADO PASO 1 DE INVESTIGACIÓN' in line for line in log_lines)
                strict_validation_applied = any('VALIDACIÓN SUPER ESTRICTA' in line for line in log_lines)
                
                details = f"Enhanced validator calls: {enhanced_validator_calls}, Political research detected: {political_research_detected}, Strict validation: {strict_validation_applied}"
                
                if enhanced_validator_calls > 0 or political_research_detected or strict_validation_applied:
                    self.log_test("4. Enhanced Validation Logs", True, details)
                    return True
                else:
                    self.log_test("4. Enhanced Validation Logs", False, f"No enhanced validation activity found. Lines checked: {len(log_lines)}")
                    return False
            else:
                self.log_test("4. Enhanced Validation Logs", False, "No enhanced validation logs found")
                return False
                
        except Exception as e:
            self.log_test("4. Enhanced Validation Logs", False, "Log check failed", e)
            return False

    def test_5_verify_task_completion_status(self):
        """Test 5: Verify task completion and validation results"""
        try:
            print("🔄 Test 5: Verifying task completion and validation results")
            
            if not self.created_task_id:
                self.log_test("5. Task Completion Status", False, "No task_id available")
                return False
            
            # Wait a bit for task to complete
            time.sleep(10)
            
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                plan = data.get('plan', [])
                
                if plan:
                    step_1 = plan[0]
                    step_1_completed = step_1.get('completed', False)
                    step_1_status = step_1.get('status', 'unknown')
                    step_1_result = step_1.get('result', {})
                    
                    # Check if enhanced validation was applied
                    validation_type = step_1_result.get('validation_type', 'unknown')
                    is_step_1_research = step_1_result.get('is_step_1_research', False)
                    
                    details = f"Step 1 completed: {step_1_completed}, Status: {step_1_status}, Validation type: {validation_type}, Is research: {is_step_1_research}"
                    
                    if is_step_1_research and validation_type == 'enhanced_political':
                        self.log_test("5. Task Completion Status", True, details)
                        return True
                    else:
                        self.log_test("5. Task Completion Status", False, f"Enhanced validation not applied. {details}")
                        return False
                else:
                    self.log_test("5. Task Completion Status", False, "No plan found in task")
                    return False
            else:
                self.log_test("5. Task Completion Status", False, f"Could not get task status: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("5. Task Completion Status", False, "Request failed", e)
            return False

    def run_focused_tests(self):
        """Run focused enhanced validation tests"""
        print("🚀 ENHANCED STEP VALIDATION SYSTEM TESTING")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print(f"FOCUS: Verify enhanced step validation system for Paso 1")
        print()
        
        # Test 1: Backend Health
        print("=" * 60)
        health_ok = self.test_1_backend_health()
        if not health_ok:
            print("❌ Backend health check failed. Aborting tests.")
            return self.test_results
        
        # Test 2: Create Political Research Task
        print("=" * 60)
        task_id = self.test_2_create_political_research_task()
        if not task_id:
            print("❌ Failed to create political research task. Aborting remaining tests.")
            self.print_summary()
            return self.test_results
        
        # Wait for task to be processed
        print("⏳ Waiting 5 seconds for task to be processed...")
        time.sleep(5)
        
        # Test 3: Execute Step 1
        print("=" * 60)
        step_executed = self.test_3_execute_step_1()
        
        # Wait for execution to complete
        print("⏳ Waiting 15 seconds for step execution to complete...")
        time.sleep(15)
        
        # Test 4: Check Enhanced Validation Logs
        print("=" * 60)
        logs_ok = self.test_4_check_enhanced_validation_logs()
        
        # Test 5: Verify Task Completion Status
        print("=" * 60)
        completion_ok = self.test_5_verify_task_completion_status()
        
        # Summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 ENHANCED STEP VALIDATION SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        # Analyze results for the enhanced validation system
        enhanced_validator_working = False
        automatic_detection_working = False
        integration_working = False
        
        for result in self.test_results:
            if result['success']:
                if 'Enhanced Validation Logs' in result['test']:
                    enhanced_validator_working = True
                if 'Task Completion Status' in result['test'] and 'enhanced_political' in result.get('details', ''):
                    automatic_detection_working = True
                    integration_working = True
        
        print("🔍 ENHANCED STEP VALIDATION SYSTEM ANALYSIS:")
        
        if enhanced_validator_working:
            print("✅ ENHANCED STEP VALIDATOR: WORKING")
            print("   - Enhanced validator calls detected in logs")
        else:
            print("❌ ENHANCED STEP VALIDATOR: NOT WORKING")
            print("   - No enhanced validator calls detected in logs")
        
        if automatic_detection_working:
            print("✅ AUTOMATIC DETECTION: WORKING")
            print("   - Political research patterns detected automatically")
        else:
            print("❌ AUTOMATIC DETECTION: NOT WORKING")
            print("   - Political research patterns not detected")
        
        if integration_working:
            print("✅ INTEGRATION FLOW: WORKING")
            print("   - agent_routes.py → enhanced_step_validator.py integration working")
        else:
            print("❌ INTEGRATION FLOW: NOT WORKING")
            print("   - Integration between components not working properly")
        
        print()
        
        # Overall assessment
        if enhanced_validator_working and automatic_detection_working and integration_working:
            print("🎉 OVERALL ASSESSMENT: ✅ ENHANCED STEP VALIDATION SYSTEM WORKING")
        else:
            print("⚠️ OVERALL ASSESSMENT: ❌ ENHANCED STEP VALIDATION SYSTEM NEEDS WORK")
        
        print()
        
        if self.created_task_id:
            print(f"📝 Test Task ID: {self.created_task_id}")
            print("   Use this ID to check logs and debug if needed")

if __name__ == "__main__":
    tester = EnhancedValidationTester()
    results = tester.run_focused_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results if not result['success'])
    sys.exit(failed_tests)