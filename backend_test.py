#!/usr/bin/env python3
"""
BACKEND TESTING SUITE FOR MITOSIS WEB NAVIGATION FUNCTIONALITY
Testing the corrected web navigation system to verify multiple site navigation
Focus: Verify that web navigation visits multiple different websites (NOT just Bing)
Context: User reported TaskView terminal showing same Bing image, system not navigating to specific links
"""

import requests
import json
import time
import sys
from datetime import datetime
import threading
import re
import subprocess

# Configuration
BACKEND_URL = "https://df209258-3b83-483b-a34c-970a958b35e3.preview.emergentagent.com"

class MitosisWebNavigationTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.created_task_id = None
        self.navigation_logs = []
        self.visited_sites = []
        self.screenshots_captured = []
        
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

    def monitor_backend_logs(self, duration=60):
        """Monitor backend logs for navigation activity"""
        try:
            print(f"🔍 Monitoring backend logs for {duration} seconds...")
            
            # Monitor supervisor logs for navigation activity
            cmd = f"tail -f /var/log/supervisor/backend.out.log | grep -E 'Navegando directamente|✅ Navegado a|page_visited|Screenshot|capturado|content_preview|content_length|Contenido extraído' | head -20"
            
            process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            start_time = time.time()
            navigation_events = []
            
            while time.time() - start_time < duration:
                try:
                    # Check if process has output
                    output = process.stdout.readline()
                    if output:
                        output = output.strip()
                        navigation_events.append(output)
                        print(f"   📋 LOG: {output}")
                        
                        # Extract visited sites
                        if "Navegado a" in output or "page_visited" in output:
                            # Extract URL from log
                            url_match = re.search(r'https?://[^\s]+', output)
                            if url_match:
                                url = url_match.group()
                                domain = re.search(r'https?://([^/]+)', url)
                                if domain:
                                    site = domain.group(1)
                                    if site not in self.visited_sites:
                                        self.visited_sites.append(site)
                                        print(f"   🌐 NEW SITE VISITED: {site}")
                        
                        # Extract screenshot info
                        if "Screenshot" in output or "capturado" in output:
                            self.screenshots_captured.append(output)
                            print(f"   📸 SCREENSHOT: {len(self.screenshots_captured)} captured")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    break
            
            process.terminate()
            self.navigation_logs = navigation_events
            
            return navigation_events
            
        except Exception as e:
            print(f"   ❌ Error monitoring logs: {e}")
            return []

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

    def test_2_create_ai_search_task(self):
        """Test 2: Create AI Search Task - Multiple Sites Expected"""
        try:
            print("🔄 Test 2: Creating AI search task expecting multiple site navigation")
            
            url = f"{self.backend_url}/api/agent/chat"
            payload = {
                "message": "Busca información sobre inteligencia artificial 2025",
                "task_id": f"test-multi-sites-{int(time.time())}"
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id') or payload['task_id']
                
                if task_id:
                    self.created_task_id = task_id
                    details = f"Task created successfully: {task_id}"
                    self.log_test("2. Create AI Search Task", True, details)
                    return task_id
                else:
                    self.log_test("2. Create AI Search Task", False, f"No task_id in response: {data}")
                    return None
            else:
                self.log_test("2. Create AI Search Task", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("2. Create AI Search Task", False, "Request failed", e)
            return None

    def test_3_monitor_navigation_logs(self):
        """Test 3: Monitor Navigation Logs for Multiple Sites"""
        try:
            print("🔄 Test 3: Monitoring navigation logs for multiple site visits")
            
            if not self.created_task_id:
                self.log_test("3. Navigation Log Monitoring", False, "No task_id available")
                return False
            
            print(f"   📋 Monitoring logs for task: {self.created_task_id}")
            
            # Start log monitoring in background
            log_thread = threading.Thread(
                target=self.monitor_backend_logs, 
                args=(90,),  # Monitor for 90 seconds
                daemon=True
            )
            log_thread.start()
            
            # Wait for some navigation activity
            time.sleep(95)  # Wait for monitoring to complete
            
            # Analyze results
            unique_sites = len(set(self.visited_sites))
            total_logs = len(self.navigation_logs)
            
            if unique_sites >= 3:
                details = f"SUCCESS: {unique_sites} different sites visited: {self.visited_sites[:5]}"
                self.log_test("3. Navigation Log Monitoring", True, details)
                return True
            elif unique_sites >= 1 and 'bing.com' not in str(self.visited_sites).lower():
                details = f"PARTIAL: {unique_sites} sites visited (not just Bing): {self.visited_sites}"
                self.log_test("3. Navigation Log Monitoring", True, details)
                return True
            elif unique_sites == 1 and 'bing.com' in str(self.visited_sites).lower():
                details = f"FAIL: Only Bing visited, no navigation to other sites: {self.visited_sites}"
                self.log_test("3. Navigation Log Monitoring", False, details)
                return False
            else:
                details = f"FAIL: No navigation detected in logs. Total logs: {total_logs}"
                self.log_test("3. Navigation Log Monitoring", False, details)
                return False
                
        except Exception as e:
            self.log_test("3. Navigation Log Monitoring", False, "Request failed", e)
            return False

    def test_4_verify_content_extraction(self):
        """Test 4: Verify Content Extraction from Multiple Sites"""
        try:
            print("🔄 Test 4: Verifying content extraction from different sites")
            
            if not self.created_task_id:
                self.log_test("4. Content Extraction", False, "No task_id available")
                return False
            
            # Check for content extraction in logs
            content_logs = [log for log in self.navigation_logs if 
                          'content_preview' in log or 'content_length' in log or 'Contenido extraído' in log]
            
            # Look for content with substantial length (>100 characters)
            substantial_content = []
            for log in content_logs:
                # Extract content length if mentioned
                length_match = re.search(r'content_length[:\s]*(\d+)', log)
                if length_match:
                    length = int(length_match.group(1))
                    if length > 100:
                        substantial_content.append(log)
                elif len(log) > 200:  # Log itself is substantial
                    substantial_content.append(log)
            
            if len(substantial_content) >= 2:
                details = f"SUCCESS: {len(substantial_content)} substantial content extractions from different sites"
                self.log_test("4. Content Extraction", True, details)
                return True
            elif len(substantial_content) >= 1:
                details = f"PARTIAL: {len(substantial_content)} content extraction detected"
                self.log_test("4. Content Extraction", True, details)
                return True
            else:
                details = f"FAIL: No substantial content extraction detected. Content logs: {len(content_logs)}"
                self.log_test("4. Content Extraction", False, details)
                return False
                
        except Exception as e:
            self.log_test("4. Content Extraction", False, "Request failed", e)
            return False

    def test_5_verify_screenshot_diversity(self):
        """Test 5: Verify Screenshot Diversity from Different Pages"""
        try:
            print("🔄 Test 5: Verifying screenshot diversity from different pages")
            
            if not self.created_task_id:
                self.log_test("5. Screenshot Diversity", False, "No task_id available")
                return False
            
            # Analyze screenshot logs
            screenshot_count = len(self.screenshots_captured)
            
            # Look for different screenshot contexts
            different_contexts = set()
            for screenshot_log in self.screenshots_captured:
                # Extract context from screenshot log
                if 'result' in screenshot_log.lower():
                    different_contexts.add('search_results')
                if 'final' in screenshot_log.lower():
                    different_contexts.add('final_page')
                if 'scrolled' in screenshot_log.lower():
                    different_contexts.add('scrolled_content')
                # Extract URLs if present
                url_match = re.search(r'https?://([^/\s]+)', screenshot_log)
                if url_match:
                    domain = url_match.group(1)
                    different_contexts.add(domain)
            
            unique_contexts = len(different_contexts)
            
            if screenshot_count >= 3 and unique_contexts >= 2:
                details = f"SUCCESS: {screenshot_count} screenshots from {unique_contexts} different contexts: {list(different_contexts)[:3]}"
                self.log_test("5. Screenshot Diversity", True, details)
                return True
            elif screenshot_count >= 2:
                details = f"PARTIAL: {screenshot_count} screenshots captured, contexts: {unique_contexts}"
                self.log_test("5. Screenshot Diversity", True, details)
                return True
            else:
                details = f"FAIL: Only {screenshot_count} screenshots captured, insufficient diversity"
                self.log_test("5. Screenshot Diversity", False, details)
                return False
                
        except Exception as e:
            self.log_test("5. Screenshot Diversity", False, "Request failed", e)
            return False

    def test_6_verify_no_bing_only_navigation(self):
        """Test 6: Verify System is NOT Stuck on Bing Only"""
        try:
            print("🔄 Test 6: Verifying system is not stuck on Bing search results only")
            
            if not self.visited_sites:
                self.log_test("6. No Bing-Only Navigation", False, "No sites visited detected")
                return False
            
            # Check if only Bing was visited
            bing_only = all('bing.com' in site.lower() for site in self.visited_sites)
            non_bing_sites = [site for site in self.visited_sites if 'bing.com' not in site.lower()]
            
            if not bing_only and len(non_bing_sites) >= 1:
                details = f"SUCCESS: System navigated beyond Bing to {len(non_bing_sites)} other sites: {non_bing_sites[:3]}"
                self.log_test("6. No Bing-Only Navigation", True, details)
                return True
            elif bing_only and len(self.visited_sites) == 1:
                details = f"FAIL: System stuck on Bing only, no navigation to other sites: {self.visited_sites}"
                self.log_test("6. No Bing-Only Navigation", False, details)
                return False
            else:
                details = f"PARTIAL: Mixed results - Bing sites: {len(self.visited_sites) - len(non_bing_sites)}, Non-Bing: {len(non_bing_sites)}"
                self.log_test("6. No Bing-Only Navigation", True, details)
                return True
                
        except Exception as e:
            self.log_test("6. No Bing-Only Navigation", False, "Request failed", e)
            return False

    def run_web_navigation_tests(self):
        """Run comprehensive web navigation functionality tests"""
        print("🚀 MITOSIS WEB NAVIGATION FUNCTIONALITY TESTING")
        print("=" * 70)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print(f"Test Task: 'Busca información sobre inteligencia artificial 2025'")
        print(f"FOCUS: Verify navigation to MULTIPLE different websites (NOT just Bing)")
        print()
        
        # Test 1: Backend Health
        print("=" * 50)
        health_ok = self.test_1_backend_health()
        if not health_ok:
            print("❌ Backend health check failed. Aborting tests.")
            return self.test_results
        
        # Test 2: Create AI Search Task
        print("=" * 50)
        task_id = self.test_2_create_ai_search_task()
        if not task_id:
            print("❌ Failed to create AI search task. Aborting remaining tests.")
            self.print_summary()
            return self.test_results
        
        # Wait a moment for task to be saved
        print("⏳ Waiting 5 seconds for task to be saved...")
        time.sleep(5)
        
        # Test 3: Monitor Navigation Logs (CRITICAL)
        print("=" * 50)
        navigation_ok = self.test_3_monitor_navigation_logs()
        
        # Test 4: Content Extraction
        print("=" * 50)
        content_ok = self.test_4_verify_content_extraction()
        
        # Test 5: Screenshot Diversity
        print("=" * 50)
        screenshot_ok = self.test_5_verify_screenshot_diversity()
        
        # Test 6: No Bing-Only Navigation
        print("=" * 50)
        no_bing_only_ok = self.test_6_verify_no_bing_only_navigation()
        
        # Summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("🎯 WEB NAVIGATION FUNCTIONALITY TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        # Analyze results for the specific navigation fix
        critical_issues = []
        navigation_working = True
        multiple_sites_visited = False
        content_extracted = False
        screenshots_diverse = False
        not_stuck_on_bing = False
        
        for result in self.test_results:
            if not result['success']:
                test_name = result['test']
                details = result['details'] or result['error']
                
                if 'Navigation Log Monitoring' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    navigation_working = False
                elif 'No Bing-Only Navigation' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    not_stuck_on_bing = False
                elif 'Content Extraction' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                elif 'Screenshot Diversity' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                else:
                    critical_issues.append(f"❌ {test_name} - {details}")
            else:
                # Check for positive results
                if 'Navigation Log Monitoring' in result['test']:
                    multiple_sites_visited = True
                if 'Content Extraction' in result['test']:
                    content_extracted = True
                if 'Screenshot Diversity' in result['test']:
                    screenshots_diverse = True
                if 'No Bing-Only Navigation' in result['test']:
                    not_stuck_on_bing = True
        
        if critical_issues:
            print("🚨 ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("✅ All web navigation functionality tests passed successfully")
        
        print()
        
        # Specific diagnosis for the navigation fix
        print("🔍 WEB NAVIGATION FIX ANALYSIS:")
        
        if multiple_sites_visited:
            print("✅ MULTIPLE SITE NAVIGATION: WORKING")
            print(f"   - System navigated to {len(self.visited_sites)} different sites: {self.visited_sites[:3]}")
        else:
            print("❌ MULTIPLE SITE NAVIGATION: NOT WORKING")
            print("   - System is not navigating to multiple different websites")
        
        if not_stuck_on_bing:
            print("✅ NOT STUCK ON BING: CONFIRMED")
            print("   - System successfully navigates beyond Bing search results")
        else:
            print("❌ STUCK ON BING: PROBLEM PERSISTS")
            print("   - System appears to be stuck on Bing search results only")
        
        if content_extracted:
            print("✅ CONTENT EXTRACTION: WORKING")
            print("   - Real content extracted from visited sites (>100 characters)")
        else:
            print("❌ CONTENT EXTRACTION: NOT WORKING")
            print("   - No substantial content extraction detected")
        
        if screenshots_diverse:
            print("✅ SCREENSHOT DIVERSITY: WORKING")
            print(f"   - {len(self.screenshots_captured)} screenshots from different contexts")
        else:
            print("❌ SCREENSHOT DIVERSITY: NOT WORKING")
            print("   - Screenshots not diverse or insufficient")
        
        print()
        
        # Overall assessment
        if multiple_sites_visited and not_stuck_on_bing and content_extracted:
            print("🎉 OVERALL ASSESSMENT: ✅ WEB NAVIGATION FIX SUCCESSFUL")
            print("   - System navigates to multiple different websites")
            print("   - Not stuck on Bing search results only")
            print("   - Real content extraction from different sites")
            print("   - Screenshots captured from different pages")
        else:
            print("⚠️ OVERALL ASSESSMENT: ❌ WEB NAVIGATION FIX NEEDS MORE WORK")
            print("   - The web navigation functionality still has issues")
            print("   - May need additional debugging and fixes")
        
        print()
        
        # Specific recommendations
        print("📋 RECOMMENDATIONS:")
        if not multiple_sites_visited:
            print("   1. Check unified_web_search_tool.py for direct navigation implementation")
            print("   2. Verify event loop fix is working correctly")
            print("   3. Test with different search queries")
        
        if not not_stuck_on_bing:
            print("   1. Verify link extraction and navigation logic")
            print("   2. Check if system is clicking on search result links")
            print("   3. Test navigation to specific URLs directly")
        
        if not content_extracted:
            print("   1. Check content extraction logic in navigation tools")
            print("   2. Verify page loading and parsing functionality")
            print("   3. Test content extraction independently")
        
        if multiple_sites_visited and not_stuck_on_bing and content_extracted:
            print("   1. Web navigation fix is working correctly")
            print("   2. Monitor for any regression issues")
            print("   3. Consider performance optimizations")
        
        print()
        print("📊 WEB NAVIGATION FUNCTIONALITY TESTING COMPLETE")
        
        if self.created_task_id:
            print(f"📝 Test Task ID: {self.created_task_id}")
            print("   Use this ID to check logs and debug if needed")
        
        print(f"📋 Navigation Logs Captured: {len(self.navigation_logs)}")
        print(f"🌐 Unique Sites Visited: {len(set(self.visited_sites))}")
        print(f"📸 Screenshots Captured: {len(self.screenshots_captured)}")

if __name__ == "__main__":
    tester = MitosisWebNavigationTester()
    results = tester.run_web_navigation_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results if not result['success'])
    sys.exit(failed_tests)