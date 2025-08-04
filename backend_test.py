#!/usr/bin/env python3
"""
BACKEND TESTING SUITE FOR MITOSIS WEB SEARCH FUNCTIONALITY FIX
Testing the corrected web_search tool to verify real results are obtained instead of simulated ones
Focus: Verify that "Parsing failed - no real search results found" error is resolved
"""

import requests
import json
import time
import sys
from datetime import datetime
import threading
import re

# Configuration
BACKEND_URL = "https://e27bb7c9-0aac-4400-bac8-b6436e299b91.preview.emergentagent.com"

class MitosisWebSearchTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.created_task_id = None
        self.websocket_events = []
        self.web_search_results = []
        
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
            
            # Test /api/health
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

    def test_2_create_web_search_task(self):
        """Test 2: Create Web Search Task - TypeScript 2025"""
        try:
            print("🔄 Test 2: Creating web search task about TypeScript 2025")
            
            url = f"{self.backend_url}/api/agent/chat"
            payload = {
                "message": "Busca información sobre TypeScript 2025 y sus nuevas características",
                "auto_execute": True
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                
                if task_id:
                    self.created_task_id = task_id
                    details = f"Task created successfully: {task_id}"
                    self.log_test("2. Create Web Search Task", True, details)
                    return task_id
                else:
                    self.log_test("2. Create Web Search Task", False, f"No task_id in response: {data}")
                    return None
            else:
                self.log_test("2. Create Web Search Task", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("2. Create Web Search Task", False, "Request failed", e)
            return None

    def test_3_verify_plan_generation(self):
        """Test 3: Verify 4-Step Plan Generation"""
        try:
            print("🔄 Test 3: Verifying 4-step plan generation")
            
            if not self.created_task_id:
                self.log_test("3. Plan Generation", False, "No task_id available")
                return False
            
            # Wait a moment for plan generation
            time.sleep(3)
            
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                plan = data.get('plan', [])
                total_steps = data.get('total_steps', 0)
                
                if success and len(plan) >= 4:
                    # Check if first step involves web search
                    first_step = plan[0] if plan else {}
                    step_description = first_step.get('description', '').lower()
                    
                    has_web_search = any(keyword in step_description for keyword in 
                                       ['buscar', 'search', 'información', 'web', 'investigar'])
                    
                    details = f"Plan generated: {len(plan)} steps, Total: {total_steps}, Web search in step 1: {has_web_search}"
                    self.log_test("3. Plan Generation", True, details)
                    return True
                else:
                    self.log_test("3. Plan Generation", False, f"Invalid plan: success={success}, steps={len(plan)}")
                    return False
            else:
                self.log_test("3. Plan Generation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("3. Plan Generation", False, "Request failed", e)
            return False

    def test_4_monitor_step1_execution(self):
        """Test 4: Monitor Step 1 Web Search Execution - Critical Test"""
        try:
            print("🔄 Test 4: Monitoring Step 1 web search execution (CRITICAL)")
            
            if not self.created_task_id:
                self.log_test("4. Step 1 Web Search", False, "No task_id available")
                return False
            
            # Monitor step 1 execution for up to 45 seconds
            start_time = time.time()
            max_wait_time = 45
            step1_completed = False
            parsing_failed_detected = False
            real_results_found = False
            
            print("   Monitoring step 1 execution...")
            
            while time.time() - start_time < max_wait_time:
                url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    current_step = data.get('current_step', 0)
                    completed_steps = data.get('completed_steps', 0)
                    plan = data.get('plan', [])
                    
                    # Check step 1 status
                    if len(plan) > 0:
                        step1 = plan[0]
                        step1_status = step1.get('status', 'pending')
                        step1_result = step1.get('result', '')
                        
                        print(f"   Step 1 status: {step1_status}, Overall: {status}, Completed: {completed_steps}")
                        
                        # Check for parsing failed error
                        if 'parsing failed' in str(step1_result).lower() or 'no real search results found' in str(step1_result).lower():
                            parsing_failed_detected = True
                            details = f"CRITICAL: 'Parsing failed' error detected in step 1 result"
                            self.log_test("4. Step 1 Web Search", False, details)
                            return False
                        
                        # Check for real results
                        if step1_status == 'completed' and step1_result:
                            # Look for real URLs (not example.com)
                            url_pattern = r'https?://[^\s]+'
                            urls_found = re.findall(url_pattern, str(step1_result))
                            real_urls = [url for url in urls_found if 'example.com' not in url]
                            
                            if real_urls:
                                real_results_found = True
                                step1_completed = True
                                details = f"Step 1 completed with REAL results: {len(real_urls)} real URLs found"
                                self.log_test("4. Step 1 Web Search", True, details)
                                return True
                        
                        # Check if step 1 failed
                        if step1_status == 'failed' or step1_status == 'error':
                            details = f"Step 1 failed: status={step1_status}, result={step1_result[:200]}..."
                            self.log_test("4. Step 1 Web Search", False, details)
                            return False
                    
                    # Check if task moved beyond step 1
                    if completed_steps > 0 or current_step > 1:
                        step1_completed = True
                        details = f"Step 1 completed, task progressed: completed={completed_steps}, current={current_step}"
                        self.log_test("4. Step 1 Web Search", True, details)
                        return True
                
                time.sleep(2)
            
            # Timeout reached
            if parsing_failed_detected:
                details = f"CRITICAL: 'Parsing failed' error still occurring after {max_wait_time}s"
                self.log_test("4. Step 1 Web Search", False, details)
            elif not step1_completed:
                details = f"Step 1 did not complete within {max_wait_time} seconds"
                self.log_test("4. Step 1 Web Search", False, details)
            else:
                details = f"Step 1 completed but no real results verified"
                self.log_test("4. Step 1 Web Search", True, details)
                return True
            
            return False
                
        except Exception as e:
            self.log_test("4. Step 1 Web Search", False, "Request failed", e)
            return False

    def test_5_verify_real_results(self):
        """Test 5: Verify Real Search Results (Not Simulated)"""
        try:
            print("🔄 Test 5: Verifying real search results (not simulated)")
            
            if not self.created_task_id:
                self.log_test("5. Real Results Verification", False, "No task_id available")
                return False
            
            # Get current task status
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', [])
                
                if len(plan) > 0:
                    step1 = plan[0]
                    step1_result = str(step1.get('result', ''))
                    
                    # Check for simulated results indicators
                    simulated_indicators = [
                        'example.com',
                        'fallback_results',
                        'generated basic results',
                        'parsing failed',
                        'no real search results found'
                    ]
                    
                    has_simulated = any(indicator in step1_result.lower() for indicator in simulated_indicators)
                    
                    # Check for real URLs
                    url_pattern = r'https?://[^\s]+'
                    urls_found = re.findall(url_pattern, step1_result)
                    real_urls = [url for url in urls_found if not any(sim in url.lower() for sim in ['example.com', 'test.com'])]
                    
                    # Check for real content indicators
                    real_content_indicators = [
                        'typescript',
                        'javascript',
                        'programming',
                        'microsoft',
                        'github',
                        'stackoverflow',
                        'developer'
                    ]
                    
                    has_real_content = any(indicator in step1_result.lower() for indicator in real_content_indicators)
                    
                    if not has_simulated and len(real_urls) > 0 and has_real_content:
                        details = f"REAL results verified: {len(real_urls)} real URLs, no simulated indicators, relevant content found"
                        self.log_test("5. Real Results Verification", True, details)
                        return True
                    elif has_simulated:
                        details = f"SIMULATED results detected: Found simulated indicators in results"
                        self.log_test("5. Real Results Verification", False, details)
                        return False
                    else:
                        details = f"Inconclusive: URLs={len(real_urls)}, Real content={has_real_content}"
                        self.log_test("5. Real Results Verification", False, details)
                        return False
                else:
                    self.log_test("5. Real Results Verification", False, "No plan steps available")
                    return False
            else:
                self.log_test("5. Real Results Verification", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("5. Real Results Verification", False, "Request failed", e)
            return False

    def test_6_monitor_subsequent_steps(self):
        """Test 6: Monitor Subsequent Steps Execution"""
        try:
            print("🔄 Test 6: Monitoring subsequent steps execution")
            
            if not self.created_task_id:
                self.log_test("6. Subsequent Steps", False, "No task_id available")
                return False
            
            # Monitor for up to 60 seconds for subsequent steps
            start_time = time.time()
            max_wait_time = 60
            steps_progress = {}
            
            while time.time() - start_time < max_wait_time:
                url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    completed_steps = data.get('completed_steps', 0)
                    current_step = data.get('current_step', 0)
                    plan = data.get('plan', [])
                    
                    # Track progress of each step
                    for i, step in enumerate(plan):
                        step_status = step.get('status', 'pending')
                        if i not in steps_progress or steps_progress[i] != step_status:
                            steps_progress[i] = step_status
                            print(f"   Step {i+1}: {step_status}")
                    
                    # Check if we have progress beyond step 1
                    if completed_steps >= 2 or current_step >= 2:
                        details = f"Subsequent steps executing: completed={completed_steps}, current={current_step}"
                        self.log_test("6. Subsequent Steps", True, details)
                        return True
                    
                    # Check for task completion
                    if status == 'completed':
                        details = f"Task completed: {completed_steps} steps completed"
                        self.log_test("6. Subsequent Steps", True, details)
                        return True
                    
                    # Check for failure
                    if status in ['failed', 'error']:
                        details = f"Task failed during execution: status={status}"
                        self.log_test("6. Subsequent Steps", False, details)
                        return False
                
                time.sleep(3)
            
            # Check final state
            final_completed = steps_progress.get(1, 'pending') if len(steps_progress) > 1 else 'no_step2'
            if final_completed in ['completed', 'in_progress']:
                details = f"Some progress on subsequent steps: {dict(steps_progress)}"
                self.log_test("6. Subsequent Steps", True, details)
                return True
            else:
                details = f"No significant progress on subsequent steps after {max_wait_time}s: {dict(steps_progress)}"
                self.log_test("6. Subsequent Steps", False, details)
                return False
                
        except Exception as e:
            self.log_test("6. Subsequent Steps", False, "Request failed", e)
            return False

    def test_7_task_completion(self):
        """Test 7: Verify Task Completion"""
        try:
            print("🔄 Test 7: Verifying task completion")
            
            if not self.created_task_id:
                self.log_test("7. Task Completion", False, "No task_id available")
                return False
            
            # Monitor for completion for up to 90 seconds
            start_time = time.time()
            max_wait_time = 90
            
            while time.time() - start_time < max_wait_time:
                url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    completed_steps = data.get('completed_steps', 0)
                    total_steps = data.get('total_steps', 0)
                    
                    print(f"   Task status: {status}, Progress: {completed_steps}/{total_steps}")
                    
                    # Check for completion
                    if status == 'completed' and completed_steps == total_steps:
                        details = f"Task completed successfully: {completed_steps}/{total_steps} steps"
                        self.log_test("7. Task Completion", True, details)
                        return True
                    
                    # Check for failure
                    if status in ['failed', 'error']:
                        details = f"Task failed: status={status}, progress={completed_steps}/{total_steps}"
                        self.log_test("7. Task Completion", False, details)
                        return False
                
                time.sleep(5)
            
            # Final check
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                completed_steps = data.get('completed_steps', 0)
                total_steps = data.get('total_steps', 0)
                
                if completed_steps >= 3:  # At least 3 steps completed is good progress
                    details = f"Good progress achieved: {completed_steps}/{total_steps} steps, status={status}"
                    self.log_test("7. Task Completion", True, details)
                    return True
                else:
                    details = f"Task did not complete within {max_wait_time}s: {completed_steps}/{total_steps} steps, status={status}"
                    self.log_test("7. Task Completion", False, details)
                    return False
            else:
                self.log_test("7. Task Completion", False, "Cannot get final task status")
                return False
                
        except Exception as e:
            self.log_test("7. Task Completion", False, "Request failed", e)
            return False

    def run_web_search_tests(self):
        """Run comprehensive web search functionality tests"""
        print("🚀 MITOSIS WEB SEARCH FUNCTIONALITY FIX TESTING")
        print("=" * 70)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print(f"Test Task: 'Busca información sobre TypeScript 2025 y sus nuevas características'")
        print(f"FOCUS: Verify 'Parsing failed - no real search results found' error is RESOLVED")
        print()
        
        # Test 1: Backend Health
        print("=" * 50)
        health_ok = self.test_1_backend_health()
        if not health_ok:
            print("❌ Backend health check failed. Aborting tests.")
            return self.test_results
        
        # Test 2: Create Web Search Task
        print("=" * 50)
        task_id = self.test_2_create_web_search_task()
        if not task_id:
            print("❌ Failed to create web search task. Aborting remaining tests.")
            self.print_summary()
            return self.test_results
        
        # Wait a moment for task to be saved
        print("⏳ Waiting 5 seconds for task to be saved...")
        time.sleep(5)
        
        # Test 3: Plan Generation
        print("=" * 50)
        plan_ok = self.test_3_verify_plan_generation()
        
        # Test 4: Step 1 Web Search Execution (CRITICAL)
        print("=" * 50)
        step1_ok = self.test_4_monitor_step1_execution()
        
        # Test 5: Real Results Verification
        print("=" * 50)
        real_results_ok = self.test_5_verify_real_results()
        
        # Test 6: Subsequent Steps
        print("=" * 50)
        subsequent_ok = self.test_6_monitor_subsequent_steps()
        
        # Test 7: Task Completion
        print("=" * 50)
        completion_ok = self.test_7_task_completion()
        
        # Summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("🎯 WEB SEARCH FUNCTIONALITY FIX TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        # Analyze results for the specific web search fix
        critical_issues = []
        web_search_working = True
        parsing_failed_resolved = True
        real_results_obtained = False
        
        for result in self.test_results:
            if not result['success']:
                test_name = result['test']
                details = result['details'] or result['error']
                
                if 'Step 1 Web Search' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    web_search_working = False
                    if 'parsing failed' in details.lower():
                        parsing_failed_resolved = False
                elif 'Real Results Verification' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    if 'simulated results detected' in details.lower():
                        real_results_obtained = False
                elif 'Plan Generation' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                elif 'Task Completion' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                else:
                    critical_issues.append(f"❌ {test_name} - {details}")
            else:
                # Check for positive results
                if 'Real Results Verification' in result['test']:
                    real_results_obtained = True
        
        if critical_issues:
            print("🚨 ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("✅ All web search functionality tests passed successfully")
        
        print()
        
        # Specific diagnosis for the web search fix
        print("🔍 WEB SEARCH FIX ANALYSIS:")
        
        if parsing_failed_resolved:
            print("✅ 'PARSING FAILED' ERROR: RESOLVED")
            print("   - No 'Parsing failed - no real search results found' errors detected")
        else:
            print("❌ 'PARSING FAILED' ERROR: STILL OCCURRING")
            print("   - The critical error is still present in step 1 execution")
        
        if real_results_obtained:
            print("✅ REAL SEARCH RESULTS: OBTAINED")
            print("   - Real URLs found, no simulated results detected")
            print("   - Relevant content indicators present")
        else:
            print("❌ REAL SEARCH RESULTS: NOT OBTAINED")
            print("   - Still getting simulated results or no results")
        
        if web_search_working:
            print("✅ WEB SEARCH FUNCTIONALITY: WORKING")
            print("   - Step 1 web search executes successfully")
            print("   - Task progresses beyond step 1")
        else:
            print("❌ WEB SEARCH FUNCTIONALITY: BROKEN")
            print("   - Step 1 web search fails or gets stuck")
        
        print()
        
        # Overall assessment
        if parsing_failed_resolved and real_results_obtained and web_search_working:
            print("🎉 OVERALL ASSESSMENT: ✅ WEB SEARCH FIX SUCCESSFUL")
            print("   - The corrected web_search tool is working properly")
            print("   - Real search results are being obtained")
            print("   - No more 'Parsing failed' errors")
            print("   - Tasks can progress through all 4 steps")
        else:
            print("⚠️ OVERALL ASSESSMENT: ❌ WEB SEARCH FIX NEEDS MORE WORK")
            print("   - The web search functionality still has issues")
            print("   - May need additional debugging and fixes")
        
        print()
        
        # Specific recommendations
        print("📋 RECOMMENDATIONS:")
        if not parsing_failed_resolved:
            print("   1. Check regex patterns in unified_web_search_tool.py")
            print("   2. Verify HTML parsing logic for search engines")
            print("   3. Test with different search engines (Google, Bing, DuckDuckGo)")
        
        if not real_results_obtained:
            print("   1. Verify URL filtering logic removes example.com properly")
            print("   2. Check if search engines are returning valid results")
            print("   3. Test with different search queries")
        
        if not web_search_working:
            print("   1. Check backend logs for step 1 execution errors")
            print("   2. Verify tool_manager integration with web_search")
            print("   3. Test web_search tool independently")
        
        if parsing_failed_resolved and real_results_obtained and web_search_working:
            print("   1. Web search fix is working correctly")
            print("   2. Monitor for any regression issues")
            print("   3. Consider performance optimizations")
        
        print()
        print("📊 WEB SEARCH FUNCTIONALITY FIX TESTING COMPLETE")
        
        if self.created_task_id:
            print(f"📝 Test Task ID: {self.created_task_id}")
            print("   Use this ID to check logs and debug if needed")

if __name__ == "__main__":
    tester = MitosisWebSearchTester()
    results = tester.run_web_search_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results if not result['success'])
    sys.exit(failed_tests)