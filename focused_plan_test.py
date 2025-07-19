#!/usr/bin/env python3
"""
Focused Plan Execution Test - Direct Backend Testing
Tests the real plan execution system directly on the local backend
"""

import requests
import json
import time
import os
from datetime import datetime

# Test local backend directly
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class FocusedPlanTester:
    def __init__(self):
        self.results = []
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
        """Test Backend Health"""
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                details = f"Database: {services.get('database')}, Ollama: {services.get('ollama')}, Tools: {services.get('tools')}"
                self.log_result("Backend Health", "PASSED", details, response_time)
                return True
            else:
                self.log_result("Backend Health", "FAILED", f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Backend Health", "FAILED", str(e))
            return False
    
    def test_document_creation_request(self):
        """Test Document Creation Request"""
        try:
            # Test message that should trigger document creation
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
                response_text = data.get('response', '')
                task_id = data.get('task_id')
                memory_used = data.get('memory_used', False)
                mode = data.get('mode', '')
                status = data.get('status', '')
                
                # Check if it's a structured plan (not casual conversation)
                is_structured_plan = mode == 'agent_with_structured_plan'
                plan_generated = status in ['plan_generated', 'completed']
                
                details = f"Response: {len(response_text)} chars, Task ID: {bool(task_id)}, Memory: {memory_used}, Mode: {mode}, Status: {status}"
                
                if is_structured_plan and plan_generated and task_id:
                    self.log_result("Document Creation Request", "PASSED", details, response_time)
                    self.task_id = task_id
                    return True
                else:
                    self.log_result("Document Creation Request", "FAILED", f"Not structured plan - {details}", response_time)
                    return False
            else:
                self.log_result("Document Creation Request", "FAILED", f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Document Creation Request", "FAILED", str(e))
            return False
    
    def test_file_creation_monitoring(self):
        """Test File Creation Monitoring"""
        try:
            print("⏳ Monitoring file creation for 45 seconds...")
            
            # Create generated_files directory if it doesn't exist
            files_dir = "/app/backend/static/generated_files"
            os.makedirs(files_dir, exist_ok=True)
            
            # Monitor for file creation
            max_wait_time = 45
            check_interval = 5
            waited_time = 0
            initial_files = set()
            
            # Get initial file list
            if os.path.exists(files_dir):
                initial_files = set(os.listdir(files_dir))
            
            while waited_time < max_wait_time:
                time.sleep(check_interval)
                waited_time += check_interval
                
                # Check for new files
                if os.path.exists(files_dir):
                    current_files = set(os.listdir(files_dir))
                    new_files = current_files - initial_files
                    
                    if new_files:
                        # Check file contents
                        valid_files = []
                        for filename in new_files:
                            file_path = os.path.join(files_dir, filename)
                            try:
                                if os.path.getsize(file_path) > 0:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read(100)
                                        if content.strip():
                                            valid_files.append(filename)
                            except Exception:
                                pass
                        
                        if valid_files:
                            details = f"Found {len(valid_files)} new files with content after {waited_time}s: {', '.join(valid_files[:3])}"
                            self.log_result("File Creation Monitoring", "PASSED", details)
                            self.created_files = valid_files
                            return True
                    
                    print(f"   Checked after {waited_time}s: {len(current_files)} total files, {len(new_files)} new files")
                else:
                    print(f"   Checked after {waited_time}s: Directory doesn't exist yet")
            
            self.log_result("File Creation Monitoring", "FAILED", f"No new files created after {max_wait_time}s")
            return False
            
        except Exception as e:
            self.log_result("File Creation Monitoring", "FAILED", str(e))
            return False
    
    def test_list_files_api(self):
        """Test List Files API"""
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/agent/list-files", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                files = data.get('files', [])
                total_files = data.get('total_files', 0)
                
                details = f"API returned {total_files} files"
                self.log_result("List Files API", "PASSED", details, response_time)
                self.api_files = files
                return True
            else:
                self.log_result("List Files API", "FAILED", f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("List Files API", "FAILED", str(e))
            return False
    
    def test_download_functionality(self):
        """Test Download Functionality"""
        try:
            if not hasattr(self, 'api_files') or not self.api_files:
                self.log_result("Download Functionality", "SKIPPED", "No files available from API")
                return False
            
            # Test downloading the first file
            test_file = self.api_files[0]
            filename = test_file['name']
            
            start_time = time.time()
            response = requests.get(f"{API_BASE}/agent/download/{filename}", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content_length = len(response.content)
                content_type = response.headers.get('Content-Type', 'unknown')
                
                details = f"Downloaded {filename}: {content_length} bytes, Type: {content_type}"
                self.log_result("Download Functionality", "PASSED", details, response_time)
                return True
            else:
                self.log_result("Download Functionality", "FAILED", f"HTTP {response.status_code} for {filename}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Download Functionality", "FAILED", str(e))
            return False
    
    def test_websocket_integration(self):
        """Test WebSocket Integration (Basic Check)"""
        try:
            # Check if WebSocket manager is initialized by looking at logs
            import subprocess
            
            # Check recent backend logs for WebSocket activity
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            websocket_indicators = [
                "WebSocket initialized",
                "WebSocket manager",
                "send_update",
                "task_id",
                "real-time"
            ]
            
            log_content = result.stdout.lower()
            websocket_activity = sum(1 for indicator in websocket_indicators if indicator.lower() in log_content)
            
            if websocket_activity >= 2:
                details = f"Found {websocket_activity} WebSocket indicators in logs"
                self.log_result("WebSocket Integration", "PASSED", details)
                return True
            else:
                details = f"Only {websocket_activity} WebSocket indicators found"
                self.log_result("WebSocket Integration", "FAILED", details)
                return False
                
        except Exception as e:
            self.log_result("WebSocket Integration", "FAILED", str(e))
            return False
    
    def run_focused_tests(self):
        """Run focused tests"""
        print("🎯 FOCUSED PLAN EXECUTION SYSTEM TEST")
        print("=" * 50)
        print(f"Testing local backend: {BACKEND_URL}")
        print(f"Started at: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run tests in order
        tests = [
            self.test_backend_health,
            self.test_document_creation_request,
            self.test_file_creation_monitoring,
            self.test_list_files_api,
            self.test_download_functionality,
            self.test_websocket_integration
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
        """Generate test summary"""
        test_end_time = datetime.now()
        total_duration = (test_end_time - self.test_start_time).total_seconds()
        
        print("=" * 50)
        print("📊 FOCUSED TEST RESULTS")
        print("=" * 50)
        
        success_rate = (passed_tests / total_tests) * 100
        status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
        
        print(f"{status_icon} OVERALL: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"⏱️  Duration: {total_duration:.1f} seconds")
        print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        # Check critical components
        backend_healthy = any(r['test'] == 'Backend Health' and r['status'] == 'PASSED' for r in self.results)
        plan_execution = any(r['test'] == 'Document Creation Request' and r['status'] == 'PASSED' for r in self.results)
        file_creation = any(r['test'] == 'File Creation Monitoring' and r['status'] == 'PASSED' for r in self.results)
        api_working = any(r['test'] == 'List Files API' and r['status'] == 'PASSED' for r in self.results)
        download_working = any(r['test'] == 'Download Functionality' and r['status'] == 'PASSED' for r in self.results)
        
        print(f"✅ Backend Health: {'WORKING' if backend_healthy else 'FAILED'}")
        print(f"✅ Plan Execution: {'WORKING' if plan_execution else 'FAILED'}")
        print(f"✅ File Creation: {'WORKING' if file_creation else 'FAILED'}")
        print(f"✅ List Files API: {'WORKING' if api_working else 'FAILED'}")
        print(f"✅ Download API: {'WORKING' if download_working else 'FAILED'}")
        
        print()
        
        # Assessment
        critical_working = sum([backend_healthy, plan_execution, file_creation])
        
        if critical_working >= 3:
            print("🎉 ASSESSMENT: Real plan execution system is WORKING!")
            print("   The system can generate plans, execute them, and create tangible files.")
        elif critical_working >= 2:
            print("⚠️  ASSESSMENT: Plan execution system partially working.")
            print("   Some components work but there are issues with file creation or execution.")
        else:
            print("❌ ASSESSMENT: Plan execution system has critical failures.")
        
        print()
        print("=" * 50)

if __name__ == "__main__":
    tester = FocusedPlanTester()
    tester.run_focused_tests()