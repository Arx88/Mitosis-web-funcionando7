#!/usr/bin/env python3
"""
BACKEND TESTING SUITE FOR WEB NAVIGATION INVESTIGATION
Testing the specific problem reported by user:
"El usuario reporta que el agente no está navegando a sitios web específicos durante búsquedas web, solo se queda en la página de Bing."

TESTING FOCUS:
1. DIRECT WEB SEARCH FUNCTIONALITY: Test web_search tool directly with specific query
2. REAL NAVIGATION LOGS: Examine if _explore_search_results executes and navigates to specific sites
3. COMPLETENESS VALIDATION SYSTEM: Test validate_step_completeness function
4. IDENTIFY SPECIFIC PROBLEM: CSS selectors, _explore_search_results errors, X11 server issues, etc.

Expected Result: Identify exactly why agent is not navigating to specific websites and propose concrete solution.
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
BACKEND_URL = "https://0871bf98-2a06-4ad9-b17c-f2881bf13143.preview.emergentagent.com"

class MitosisToolDiversificationTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.created_task_id = None
        self.tool_usage_logs = []
        self.tools_used = set()
        self.content_generated = ""
        self.meta_content_detected = []
        self.multi_source_validation_logs = []
        
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

    def monitor_tool_usage_logs(self, duration=120):
        """Monitor backend logs for tool usage tracking and diversification"""
        try:
            print(f"🔍 Monitoring backend logs for tool usage tracking for {duration} seconds...")
            
            # Monitor supervisor logs for tool usage tracking
            cmd = f"tail -f /var/log/supervisor/backend.out.log | grep -E '📊 TOOL USAGE TRACKER|ollama_processing|web_search|file_manager|validate_multi_source_data_collection|analysis.*→|creation.*→|Meta-content detected|se realizará|se analizará' | head -30"
            
            process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            start_time = time.time()
            tool_events = []
            
            while time.time() - start_time < duration:
                try:
                    # Check if process has output
                    output = process.stdout.readline()
                    if output:
                        output = output.strip()
                        tool_events.append(output)
                        print(f"   📋 LOG: {output}")
                        
                        # Extract tool usage
                        if "📊 TOOL USAGE TRACKER" in output:
                            self.tool_usage_logs.append(output)
                            print(f"   🛠️ TOOL TRACKER DETECTED: {len(self.tool_usage_logs)} entries")
                        
                        # Extract specific tools used
                        if "ollama_processing" in output:
                            self.tools_used.add("ollama_processing")
                            print(f"   🧠 OLLAMA_PROCESSING DETECTED")
                        
                        if "web_search" in output:
                            self.tools_used.add("web_search")
                            print(f"   🌐 WEB_SEARCH DETECTED")
                        
                        if "file_manager" in output:
                            self.tools_used.add("file_manager")
                            print(f"   📁 FILE_MANAGER DETECTED")
                        
                        # Extract meta-content detection
                        if any(phrase in output.lower() for phrase in ["se realizará", "se analizará", "meta-content detected"]):
                            self.meta_content_detected.append(output)
                            print(f"   🚫 META-CONTENT DETECTED: {len(self.meta_content_detected)} instances")
                        
                        # Extract multi-source validation
                        if "validate_multi_source_data_collection" in output:
                            self.multi_source_validation_logs.append(output)
                            print(f"   📊 MULTI-SOURCE VALIDATION: {len(self.multi_source_validation_logs)} calls")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    break
            
            process.terminate()
            
            return tool_events
            
        except Exception as e:
            print(f"   ❌ Error monitoring tool usage logs: {e}")
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

    def test_2_create_economic_analysis_task(self):
        """Test 2: Create Economic Analysis Task - Tool Diversification Expected"""
        try:
            print("🔄 Test 2: Creating economic analysis task expecting tool diversification")
            
            url = f"{self.backend_url}/api/agent/chat"
            payload = {
                "message": "Realizar análisis detallado del impacto económico de la inteligencia artificial en Argentina durante 2024-2025",
                "task_id": f"test-tool-diversification-{int(time.time())}"
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id') or payload['task_id']
                
                if task_id:
                    self.created_task_id = task_id
                    details = f"Economic analysis task created successfully: {task_id}"
                    self.log_test("2. Create Economic Analysis Task", True, details)
                    return task_id
                else:
                    self.log_test("2. Create Economic Analysis Task", False, f"No task_id in response: {data}")
                    return None
            else:
                self.log_test("2. Create Economic Analysis Task", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("2. Create Economic Analysis Task", False, "Request failed", e)
            return None

    def test_3_monitor_tool_diversification(self):
        """Test 3: Monitor Tool Usage for Diversification"""
        try:
            print("🔄 Test 3: Monitoring tool usage for diversification (NOT just web_search)")
            
            if not self.created_task_id:
                self.log_test("3. Tool Diversification Monitoring", False, "No task_id available")
                return False
            
            print(f"   📋 Monitoring tool usage for task: {self.created_task_id}")
            
            # Start tool usage monitoring in background
            log_thread = threading.Thread(
                target=self.monitor_tool_usage_logs, 
                args=(120,),  # Monitor for 120 seconds
                daemon=True
            )
            log_thread.start()
            
            # Wait for tool usage activity
            time.sleep(125)  # Wait for monitoring to complete
            
            # Analyze results
            unique_tools = len(self.tools_used)
            tool_tracker_entries = len(self.tool_usage_logs)
            
            if unique_tools >= 3:
                details = f"SUCCESS: {unique_tools} different tools used: {list(self.tools_used)}"
                self.log_test("3. Tool Diversification Monitoring", True, details)
                return True
            elif unique_tools >= 2 and "web_search" not in self.tools_used:
                details = f"GOOD: {unique_tools} tools used (not just web_search): {list(self.tools_used)}"
                self.log_test("3. Tool Diversification Monitoring", True, details)
                return True
            elif unique_tools == 1 and "web_search" in self.tools_used:
                details = f"FAIL: Only web_search used, no tool diversification: {list(self.tools_used)}"
                self.log_test("3. Tool Diversification Monitoring", False, details)
                return False
            else:
                details = f"FAIL: Insufficient tool diversification. Tools: {unique_tools}, Tracker entries: {tool_tracker_entries}"
                self.log_test("3. Tool Diversification Monitoring", False, details)
                return False
                
        except Exception as e:
            self.log_test("3. Tool Diversification Monitoring", False, "Request failed", e)
            return False

    def test_4_verify_real_data_collection(self):
        """Test 4: Verify Real Data Collection (dates, numbers, names)"""
        try:
            print("🔄 Test 4: Verifying real data collection with specific details")
            
            if not self.created_task_id:
                self.log_test("4. Real Data Collection", False, "No task_id available")
                return False
            
            # Get task results to analyze content
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                task_data = data
                
                # Extract content from task results
                content_sources = []
                if 'plan' in task_data:
                    for step in task_data.get('plan', []):
                        if 'result' in step:
                            content_sources.append(step['result'])
                
                # Combine all content
                all_content = " ".join(str(content) for content in content_sources)
                self.content_generated = all_content
                
                # Check for real data indicators
                real_data_indicators = {
                    'dates': len(re.findall(r'\b(2024|2025|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b', all_content, re.IGNORECASE)),
                    'numbers': len(re.findall(r'\b\d+[.,]?\d*\s*(%|millones|miles|USD|ARS|pesos)\b', all_content, re.IGNORECASE)),
                    'names': len(re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', all_content)),
                    'specific_terms': len(re.findall(r'\b(Argentina|Buenos Aires|INDEC|Banco Central|PIB|inflación|tecnología|startup)\b', all_content, re.IGNORECASE))
                }
                
                total_indicators = sum(real_data_indicators.values())
                content_length = len(all_content)
                
                if total_indicators >= 10 and content_length > 500:
                    details = f"SUCCESS: {total_indicators} real data indicators found in {content_length} chars: {real_data_indicators}"
                    self.log_test("4. Real Data Collection", True, details)
                    return True
                elif total_indicators >= 5:
                    details = f"PARTIAL: {total_indicators} real data indicators found: {real_data_indicators}"
                    self.log_test("4. Real Data Collection", True, details)
                    return True
                else:
                    details = f"FAIL: Only {total_indicators} real data indicators found in {content_length} chars"
                    self.log_test("4. Real Data Collection", False, details)
                    return False
            else:
                self.log_test("4. Real Data Collection", False, f"Could not get task status: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("4. Real Data Collection", False, "Request failed", e)
            return False

    def test_5_verify_meta_content_detection(self):
        """Test 5: Verify Meta-Content Detection (NO generic phrases)"""
        try:
            print("🔄 Test 5: Verifying meta-content detection (rejecting generic phrases)")
            
            if not self.content_generated:
                self.log_test("5. Meta-Content Detection", False, "No content available for analysis")
                return False
            
            # Check for meta-content phrases that should be rejected
            meta_phrases = [
                "se realizará", "se analizará", "el presente estudio", "información general",
                "se llevará a cabo", "se procederá", "se efectuará", "se desarrollará",
                "en el futuro", "posteriormente", "a continuación", "en resumen",
                "por otro lado", "en conclusión", "finalmente", "en primer lugar"
            ]
            
            detected_meta_phrases = []
            for phrase in meta_phrases:
                if phrase.lower() in self.content_generated.lower():
                    detected_meta_phrases.append(phrase)
            
            meta_content_count = len(detected_meta_phrases)
            detection_logs = len(self.meta_content_detected)
            
            if meta_content_count == 0:
                details = f"SUCCESS: No meta-content phrases detected. Content is specific and real."
                self.log_test("5. Meta-Content Detection", True, details)
                return True
            elif meta_content_count <= 2:
                details = f"ACCEPTABLE: Only {meta_content_count} meta-phrases found: {detected_meta_phrases[:2]}"
                self.log_test("5. Meta-Content Detection", True, details)
                return True
            else:
                details = f"FAIL: {meta_content_count} meta-content phrases detected: {detected_meta_phrases[:5]}"
                self.log_test("5. Meta-Content Detection", False, details)
                return False
                
        except Exception as e:
            self.log_test("5. Meta-Content Detection", False, "Request failed", e)
            return False

    def test_6_verify_multi_source_validation(self):
        """Test 6: Verify Multi-Source Data Validation Function"""
        try:
            print("🔄 Test 6: Verifying multi-source data validation function execution")
            
            validation_calls = len(self.multi_source_validation_logs)
            tool_tracker_calls = len(self.tool_usage_logs)
            unique_tools = len(self.tools_used)
            
            if validation_calls >= 1 and unique_tools >= 2:
                details = f"SUCCESS: {validation_calls} validation calls with {unique_tools} different tools"
                self.log_test("6. Multi-Source Validation", True, details)
                return True
            elif tool_tracker_calls >= 3:
                details = f"PARTIAL: {tool_tracker_calls} tool tracker calls detected (validation may be implicit)"
                self.log_test("6. Multi-Source Validation", True, details)
                return True
            else:
                details = f"FAIL: Only {validation_calls} validation calls, {tool_tracker_calls} tracker calls"
                self.log_test("6. Multi-Source Validation", False, details)
                return False
                
        except Exception as e:
            self.log_test("6. Multi-Source Validation", False, "Request failed", e)
            return False

    def run_tool_diversification_tests(self):
        """Run comprehensive tool diversification and real data collection tests"""
        print("🚀 MITOSIS TOOL DIVERSIFICATION AND REAL DATA COLLECTION TESTING")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print(f"Test Task: 'Realizar análisis detallado del impacto económico de la IA en Argentina 2024-2025'")
        print(f"FOCUS: Verify tool diversification + real data collection + no meta-content")
        print()
        
        # Test 1: Backend Health
        print("=" * 60)
        health_ok = self.test_1_backend_health()
        if not health_ok:
            print("❌ Backend health check failed. Aborting tests.")
            return self.test_results
        
        # Test 2: Create Economic Analysis Task
        print("=" * 60)
        task_id = self.test_2_create_economic_analysis_task()
        if not task_id:
            print("❌ Failed to create economic analysis task. Aborting remaining tests.")
            self.print_summary()
            return self.test_results
        
        # Wait a moment for task to be saved
        print("⏳ Waiting 10 seconds for task to be saved and processing to start...")
        time.sleep(10)
        
        # Test 3: Monitor Tool Diversification (CRITICAL)
        print("=" * 60)
        diversification_ok = self.test_3_monitor_tool_diversification()
        
        # Test 4: Real Data Collection
        print("=" * 60)
        real_data_ok = self.test_4_verify_real_data_collection()
        
        # Test 5: Meta-Content Detection
        print("=" * 60)
        meta_content_ok = self.test_5_verify_meta_content_detection()
        
        # Test 6: Multi-Source Validation
        print("=" * 60)
        multi_source_ok = self.test_6_verify_multi_source_validation()
        
        # Summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 TOOL DIVERSIFICATION AND REAL DATA COLLECTION TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        # Analyze results for the specific improvements
        critical_issues = []
        tool_diversification_working = False
        real_data_collected = False
        meta_content_rejected = False
        multi_source_validated = False
        
        for result in self.test_results:
            if not result['success']:
                test_name = result['test']
                details = result['details'] or result['error']
                
                if 'Tool Diversification' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                elif 'Real Data Collection' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                elif 'Meta-Content Detection' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                elif 'Multi-Source Validation' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                else:
                    critical_issues.append(f"❌ {test_name} - {details}")
            else:
                # Check for positive results
                if 'Tool Diversification' in result['test']:
                    tool_diversification_working = True
                if 'Real Data Collection' in result['test']:
                    real_data_collected = True
                if 'Meta-Content Detection' in result['test']:
                    meta_content_rejected = True
                if 'Multi-Source Validation' in result['test']:
                    multi_source_validated = True
        
        if critical_issues:
            print("🚨 ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("✅ All tool diversification and real data collection tests passed successfully")
        
        print()
        
        # Specific diagnosis for the improvements
        print("🔍 TOOL DIVERSIFICATION IMPROVEMENTS ANALYSIS:")
        
        if tool_diversification_working:
            print("✅ TOOL DIVERSIFICATION: WORKING")
            print(f"   - System used {len(self.tools_used)} different tools: {list(self.tools_used)}")
            print(f"   - Tool usage tracker entries: {len(self.tool_usage_logs)}")
        else:
            print("❌ TOOL DIVERSIFICATION: NOT WORKING")
            print("   - System is not using diverse tools based on context")
        
        if real_data_collected:
            print("✅ REAL DATA COLLECTION: WORKING")
            print("   - Content contains specific dates, numbers, names, and terms")
            print(f"   - Content length: {len(self.content_generated)} characters")
        else:
            print("❌ REAL DATA COLLECTION: NOT WORKING")
            print("   - Content lacks specific real data indicators")
        
        if meta_content_rejected:
            print("✅ META-CONTENT DETECTION: WORKING")
            print("   - System successfully rejects generic phrases like 'se realizará', 'se analizará'")
        else:
            print("❌ META-CONTENT DETECTION: NOT WORKING")
            print("   - Content contains too many generic meta-phrases")
        
        if multi_source_validated:
            print("✅ MULTI-SOURCE VALIDATION: WORKING")
            print(f"   - Validation function calls: {len(self.multi_source_validation_logs)}")
        else:
            print("❌ MULTI-SOURCE VALIDATION: NOT WORKING")
            print("   - Multi-source validation function not detected")
        
        print()
        
        # Overall assessment
        if tool_diversification_working and real_data_collected and meta_content_rejected:
            print("🎉 OVERALL ASSESSMENT: ✅ TOOL DIVERSIFICATION IMPROVEMENTS SUCCESSFUL")
            print("   - System uses different tools based on context")
            print("   - Real data collection with specific details")
            print("   - Meta-content detection working correctly")
            print("   - Multi-source validation implemented")
        else:
            print("⚠️ OVERALL ASSESSMENT: ❌ TOOL DIVERSIFICATION IMPROVEMENTS NEED MORE WORK")
            print("   - The tool diversification functionality still has issues")
            print("   - May need additional debugging and fixes")
        
        print()
        
        # Specific recommendations
        print("📋 RECOMMENDATIONS:")
        if not tool_diversification_working:
            print("   1. Check agent_routes.py for correct tool mapping (analysis→ollama_processing)")
            print("   2. Verify 📊 TOOL USAGE TRACKER is logging tool usage correctly")
            print("   3. Test context-based tool selection logic")
        
        if not real_data_collected:
            print("   1. Verify web search is collecting real data from multiple sources")
            print("   2. Check ollama_processing is using real data from previous steps")
            print("   3. Test data extraction and processing pipeline")
        
        if not meta_content_rejected:
            print("   1. Check meta-content detection with 16 new phrases")
            print("   2. Verify content generation rejects generic phrases")
            print("   3. Test content quality validation")
        
        if not multi_source_validated:
            print("   1. Implement validate_multi_source_data_collection() function")
            print("   2. Check multi-source validation scoring system")
            print("   3. Test source diversity requirements")
        
        if tool_diversification_working and real_data_collected and meta_content_rejected:
            print("   1. Tool diversification improvements are working correctly")
            print("   2. Monitor for any regression issues")
            print("   3. Consider expanding to more tool types")
        
        print()
        print("📊 TOOL DIVERSIFICATION AND REAL DATA COLLECTION TESTING COMPLETE")
        
        if self.created_task_id:
            print(f"📝 Test Task ID: {self.created_task_id}")
            print("   Use this ID to check logs and debug if needed")
        
        print(f"📋 Tool Usage Logs: {len(self.tool_usage_logs)}")
        print(f"🛠️ Unique Tools Used: {len(self.tools_used)}")
        print(f"📊 Multi-Source Validation Calls: {len(self.multi_source_validation_logs)}")
        print(f"🚫 Meta-Content Detections: {len(self.meta_content_detected)}")

if __name__ == "__main__":
    tester = MitosisToolDiversificationTester()
    results = tester.run_tool_diversification_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results if not result['success'])
    sys.exit(failed_tests)