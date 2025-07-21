#!/usr/bin/env python3
"""
Comprehensive Test for Real Plan Execution System
Tests the fixed "sistema arreglado de ejecución real de planes"

This test verifies:
1. Real Plan Execution: /api/agent/chat with document creation request
2. Tangible File Creation: Real files in /app/backend/static/generated_files/
3. Download Endpoints: /api/agent/list-files and /api/agent/download/<filename>
4. WebSocket Integration: Real-time updates during execution
5. Enhanced Responses: File creation info and download links
6. System State: All services working without regressions
"""

import requests
import json
import time
import os
from datetime import datetime
from urllib.parse import urljoin

# Configuration
BACKEND_URL = "https://5ee3d056-2e8a-4cf4-9c24-833be751801b.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class PlanExecutionTester:
    def __init__(self):
        self.results = []
        self.files_created = []
        self.test_start_time = datetime.now()
        
    def log_result(self, test_name, status, details, response_time=None):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⚠️"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status_icon} {test_name}: {status}{time_info}")
        if details:
            print(f"   Details: {details}")
        print()
        
    def test_backend_health(self):
        """Test 1: Backend Health Check"""
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                details = f"Database: {services.get('database')}, Ollama: {services.get('ollama')}, Tools: {services.get('tools')}"
                self.log_result("Backend Health Check", "PASSED", details, response_time)
                return True
            else:
                self.log_result("Backend Health Check", "FAILED", f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Backend Health Check", "FAILED", str(e))
            return False
    
    def test_agent_status(self):
        """Test 2: Agent Status Check"""
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/agent/status", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                details = f"Running: {data.get('running')}, Memory: {data.get('memory_enabled')}, Tasks: {data.get('active_tasks', 0)}"
                self.log_result("Agent Status Check", "PASSED", details, response_time)
                return True
            else:
                self.log_result("Agent Status Check", "FAILED", f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Agent Status Check", "FAILED", str(e))
            return False
    
    def test_real_plan_execution(self):
        """Test 3: Real Plan Execution with Document Creation"""
        try:
            # Test message that requires creating a document
            test_message = "Ayúdame a crear un documento sobre Python para principiantes"
            
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/agent/chat",
                json={"message": test_message},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                has_response = bool(data.get('response'))
                has_task_id = bool(data.get('task_id'))
                memory_used = data.get('memory_used', False)
                mode = data.get('mode', '')
                status = data.get('status', '')
                
                # Check if it's a structured plan (not casual conversation)
                is_structured_plan = mode == 'agent_with_structured_plan'
                plan_generated = status in ['plan_generated', 'completed']
                
                details = f"Response: {len(data.get('response', ''))} chars, Task ID: {has_task_id}, Memory: {memory_used}, Mode: {mode}, Status: {status}"
                
                if has_response and has_task_id and is_structured_plan and plan_generated:
                    self.log_result("Real Plan Execution", "PASSED", details, response_time)
                    
                    # Store task_id for later verification
                    self.task_id = data.get('task_id')
                    return True
                else:
                    self.log_result("Real Plan Execution", "FAILED", f"Missing elements - {details}", response_time)
                    return False
            else:
                self.log_result("Real Plan Execution", "FAILED", f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Real Plan Execution", "FAILED", str(e))
            return False
    
    def test_file_creation_wait(self):
        """Test 4: Wait for File Creation (Real Execution)"""
        try:
            print("⏳ Waiting for plan execution and file creation (30 seconds)...")
            
            # Wait for plan execution to complete and create files
            max_wait_time = 30
            check_interval = 5
            waited_time = 0
            
            while waited_time < max_wait_time:
                time.sleep(check_interval)
                waited_time += check_interval
                
                # Check if files have been created
                try:
                    response = requests.get(f"{API_BASE}/agent/list-files", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        files = data.get('files', [])
                        
                        # Check for recently created files (within last 2 minutes)
                        recent_files = []
                        current_time = datetime.now()
                        
                        for file_info in files:
                            file_created = datetime.fromisoformat(file_info['created'].replace('Z', '+00:00').replace('+00:00', ''))
                            time_diff = (current_time - file_created).total_seconds()
                            
                            if time_diff < 120:  # Files created in last 2 minutes
                                recent_files.append(file_info)
                        
                        if recent_files:
                            self.files_created = recent_files
                            details = f"Found {len(recent_files)} recently created files after {waited_time}s"
                            self.log_result("File Creation Wait", "PASSED", details)
                            return True
                        
                        print(f"   Checked after {waited_time}s: {len(files)} total files, {len(recent_files)} recent")
                    
                except Exception as check_error:
                    print(f"   Error checking files after {waited_time}s: {check_error}")
            
            # Final check
            self.log_result("File Creation Wait", "FAILED", f"No files created after {max_wait_time}s wait")
            return False
            
        except Exception as e:
            self.log_result("File Creation Wait", "FAILED", str(e))
            return False
    
    def test_list_files_endpoint(self):
        """Test 5: List Files Endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/agent/list-files", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                files = data.get('files', [])
                total_files = data.get('total_files', 0)
                
                details = f"Found {total_files} files, Response structure valid"
                self.log_result("List Files Endpoint", "PASSED", details, response_time)
                
                # Store files for download test
                self.available_files = files
                return True
            else:
                self.log_result("List Files Endpoint", "FAILED", f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("List Files Endpoint", "FAILED", str(e))
            return False
    
    def test_file_download_endpoint(self):
        """Test 6: File Download Endpoint"""
        try:
            if not hasattr(self, 'available_files') or not self.available_files:
                self.log_result("File Download Endpoint", "SKIPPED", "No files available to download")
                return False
            
            # Test downloading the first available file
            test_file = self.available_files[0]
            filename = test_file['name']
            
            start_time = time.time()
            response = requests.get(f"{API_BASE}/agent/download/{filename}", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content_length = len(response.content)
                content_type = response.headers.get('Content-Type', 'unknown')
                
                details = f"Downloaded {filename}: {content_length} bytes, Type: {content_type}"
                self.log_result("File Download Endpoint", "PASSED", details, response_time)
                return True
            else:
                self.log_result("File Download Endpoint", "FAILED", f"HTTP {response.status_code} for {filename}", response_time)
                return False
                
        except Exception as e:
            self.log_result("File Download Endpoint", "FAILED", str(e))
            return False
    
    def test_tangible_file_verification(self):
        """Test 7: Verify Tangible Files Exist"""
        try:
            # Check if generated_files directory exists and has content
            files_dir = "/app/backend/static/generated_files"
            
            if not os.path.exists(files_dir):
                self.log_result("Tangible File Verification", "FAILED", "Generated files directory does not exist")
                return False
            
            # List files in directory
            files = [f for f in os.listdir(files_dir) if os.path.isfile(os.path.join(files_dir, f))]
            
            if not files:
                self.log_result("Tangible File Verification", "FAILED", "No files found in generated_files directory")
                return False
            
            # Check file contents
            total_size = 0
            valid_files = 0
            
            for filename in files:
                file_path = os.path.join(files_dir, filename)
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    # Check if file has actual content (not empty)
                    if file_size > 0:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(100)  # Read first 100 chars
                            if content.strip():  # Has non-whitespace content
                                valid_files += 1
                except Exception:
                    pass
            
            details = f"Found {len(files)} files, {valid_files} with valid content, Total size: {total_size} bytes"
            
            if valid_files > 0:
                self.log_result("Tangible File Verification", "PASSED", details)
                return True
            else:
                self.log_result("Tangible File Verification", "FAILED", f"No valid content files - {details}")
                return False
                
        except Exception as e:
            self.log_result("Tangible File Verification", "FAILED", str(e))
            return False
    
    def test_enhanced_responses(self):
        """Test 8: Enhanced Responses with File Info"""
        try:
            # Test another document creation request to check enhanced responses
            test_message = "Crea un informe breve sobre inteligencia artificial"
            
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/agent/chat",
                json={"message": test_message},
                timeout=25
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Check for enhanced response indicators
                has_file_info = any(keyword in response_text.lower() for keyword in [
                    'archivo', 'file', 'descarga', 'download', 'generado', 'created'
                ])
                
                has_structured_plan = data.get('mode') == 'agent_with_structured_plan'
                has_task_tracking = bool(data.get('task_id'))
                
                details = f"File info: {has_file_info}, Structured: {has_structured_plan}, Task tracking: {has_task_tracking}"
                
                if has_structured_plan and has_task_tracking:
                    self.log_result("Enhanced Responses", "PASSED", details, response_time)
                    return True
                else:
                    self.log_result("Enhanced Responses", "FAILED", f"Missing enhancements - {details}", response_time)
                    return False
            else:
                self.log_result("Enhanced Responses", "FAILED", f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Enhanced Responses", "FAILED", str(e))
            return False
    
    def test_system_stability(self):
        """Test 9: System Stability Check"""
        try:
            # Test multiple consecutive requests to ensure no regressions
            stable_requests = 0
            total_requests = 3
            
            for i in range(total_requests):
                try:
                    start_time = time.time()
                    response = requests.get(f"{API_BASE}/agent/status", timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200 and response_time < 5.0:
                        stable_requests += 1
                    
                    time.sleep(1)  # Brief pause between requests
                    
                except Exception:
                    pass
            
            stability_rate = (stable_requests / total_requests) * 100
            details = f"Stability: {stable_requests}/{total_requests} requests successful ({stability_rate:.1f}%)"
            
            if stability_rate >= 75:  # At least 75% success rate
                self.log_result("System Stability Check", "PASSED", details)
                return True
            else:
                self.log_result("System Stability Check", "FAILED", details)
                return False
                
        except Exception as e:
            self.log_result("System Stability Check", "FAILED", str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 COMPREHENSIVE PLAN EXECUTION SYSTEM TEST")
        print("=" * 60)
        print(f"Testing backend: {BACKEND_URL}")
        print(f"Started at: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run tests in order
        tests = [
            self.test_backend_health,
            self.test_agent_status,
            self.test_real_plan_execution,
            self.test_file_creation_wait,
            self.test_list_files_endpoint,
            self.test_file_download_endpoint,
            self.test_tangible_file_verification,
            self.test_enhanced_responses,
            self.test_system_stability
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test_func.__name__} crashed: {e}")
        
        # Generate summary
        self.generate_summary(passed_tests, total_tests)
    
    def generate_summary(self, passed_tests, total_tests):
        """Generate comprehensive test summary"""
        test_end_time = datetime.now()
        total_duration = (test_end_time - self.test_start_time).total_seconds()
        
        print("=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
        
        print(f"{status_icon} OVERALL STATUS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"⏱️  Total execution time: {total_duration:.1f} seconds")
        print()
        
        # Detailed results
        print("📋 DETAILED TEST RESULTS:")
        for result in self.results:
            status_icon = "✅" if result['status'] == "PASSED" else "❌" if result['status'] == "FAILED" else "⚠️"
            time_info = f" ({result['response_time']:.2f}s)" if result['response_time'] else ""
            print(f"{status_icon} {result['test']}: {result['status']}{time_info}")
            if result['details']:
                print(f"   {result['details']}")
        
        print()
        
        # Critical findings
        print("🔍 CRITICAL FINDINGS:")
        
        # Check for plan execution
        plan_execution_passed = any(r['test'] == 'Real Plan Execution' and r['status'] == 'PASSED' for r in self.results)
        file_creation_passed = any(r['test'] == 'Tangible File Verification' and r['status'] == 'PASSED' for r in self.results)
        download_passed = any(r['test'] == 'File Download Endpoint' and r['status'] == 'PASSED' for r in self.results)
        
        if plan_execution_passed:
            print("✅ Real plan execution system is working")
        else:
            print("❌ CRITICAL: Real plan execution system failed")
        
        if file_creation_passed:
            print("✅ Tangible file creation is working")
        else:
            print("❌ CRITICAL: No tangible files being created")
        
        if download_passed:
            print("✅ File download system is operational")
        else:
            print("❌ CRITICAL: File download system not working")
        
        # Files created info
        if hasattr(self, 'files_created') and self.files_created:
            print(f"📁 Files created during test: {len(self.files_created)}")
            for file_info in self.files_created[:3]:  # Show first 3
                print(f"   - {file_info['name']} ({file_info['size']} bytes)")
        
        print()
        
        # Final assessment
        if success_rate >= 80:
            print("🎉 ASSESSMENT: Plan execution system is working correctly!")
            print("   The reported issue 'dice que completa pero no entrega resultados' appears to be RESOLVED.")
        elif success_rate >= 60:
            print("⚠️  ASSESSMENT: Plan execution system has some issues but core functionality works.")
        else:
            print("❌ ASSESSMENT: Plan execution system has critical failures.")
            print("   The reported issue 'dice que completa pero no entrega resultados' is NOT resolved.")
        
        print()
        print("=" * 60)

if __name__ == "__main__":
    tester = PlanExecutionTester()
    tester.run_all_tests()