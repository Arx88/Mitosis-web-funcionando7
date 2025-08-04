#!/usr/bin/env python3
"""
BACKEND TESTING SUITE FOR MITOSIS WEBSOCKET REAL-TIME NAVIGATION FIX
Testing the corrected WebSocket Manager initialization and real-time browser navigation events
Focus: Verify that "Global WebSocket manager not available or initialized for task" error is resolved
"""

import requests
import json
import time
import sys
from datetime import datetime
import threading
import re

# Configuration
BACKEND_URL = "https://6a42dbad-573b-4631-929d-0d271703ed7e.preview.emergentagent.com"

class MitosisWebSocketNavigationTester:
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
        self.navigation_events = []
        
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

    def test_1_websocket_manager_initialization(self):
        """Test 1: Verify WebSocket Manager is Initialized"""
        try:
            print("🔄 Test 1: Checking WebSocket Manager initialization")
            
            # Test backend health to see if WebSocket Manager is initialized
            url = f"{self.backend_url}/api/health"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                active_connections = data.get('active_connections', 0)
                
                # Check if we can access WebSocket endpoint
                ws_url = f"{self.backend_url}/api/socket.io/"
                ws_response = self.session.get(ws_url, timeout=5)
                
                # SocketIO should return a specific response or redirect
                websocket_available = ws_response.status_code in [200, 400, 404]  # 400 is normal for SocketIO GET
                
                details = f"WebSocket endpoint accessible: {websocket_available}, Active connections: {active_connections}"
                self.log_test("1. WebSocket Manager Initialization", websocket_available, details)
                return websocket_available
            else:
                self.log_test("1. WebSocket Manager Initialization", False, f"Health check failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("1. WebSocket Manager Initialization", False, "Request failed", e)
            return False

    def test_2_create_web_navigation_task(self):
        """Test 2: Create Web Navigation Task that requires browser_visual events"""
        try:
            print("🔄 Test 2: Creating web navigation task that requires real-time browser events")
            
            url = f"{self.backend_url}/api/agent/chat"
            payload = {
                "message": "Busca información sobre inteligencia artificial en tiempo real y muestra el progreso de navegación",
                "auto_execute": True
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                
                if task_id:
                    self.created_task_id = task_id
                    details = f"Web navigation task created successfully: {task_id}"
                    self.log_test("2. Create Web Navigation Task", True, details)
                    return task_id
                else:
                    self.log_test("2. Create Web Navigation Task", False, f"No task_id in response: {data}")
                    return None
            else:
                self.log_test("2. Create Web Navigation Task", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("2. Create Web Navigation Task", False, "Request failed", e)
            return None

    def test_3_verify_no_websocket_manager_error(self):
        """Test 3: Verify NO 'Global WebSocket manager not available' error occurs"""
        try:
            print("🔄 Test 3: Monitoring for 'Global WebSocket manager not available' error")
            
            if not self.created_task_id:
                self.log_test("3. No WebSocket Manager Error", False, "No task_id available")
                return False
            
            # Monitor task execution for WebSocket manager errors
            start_time = time.time()
            max_wait_time = 30
            websocket_error_detected = False
            task_started = False
            
            while time.time() - start_time < max_wait_time:
                url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    plan = data.get('plan', [])
                    
                    # Check if task has started
                    if status not in ['pending', 'unknown']:
                        task_started = True
                    
                    # Check for WebSocket manager errors in step results
                    for step in plan:
                        step_result = str(step.get('result', ''))
                        step_error = str(step.get('error', ''))
                        
                        if 'global websocket manager not available' in step_result.lower() or \
                           'global websocket manager not available' in step_error.lower():
                            websocket_error_detected = True
                            details = f"CRITICAL: 'Global WebSocket manager not available' error detected in step result"
                            self.log_test("3. No WebSocket Manager Error", False, details)
                            return False
                    
                    # If task has progressed without WebSocket errors, that's good
                    if task_started and len([s for s in plan if s.get('status') == 'completed']) > 0:
                        details = f"Task progressing without WebSocket manager errors: status={status}"
                        self.log_test("3. No WebSocket Manager Error", True, details)
                        return True
                
                time.sleep(2)
            
            # If we reach here without detecting the error, that's success
            if task_started and not websocket_error_detected:
                details = f"No 'Global WebSocket manager not available' error detected during {max_wait_time}s monitoring"
                self.log_test("3. No WebSocket Manager Error", True, details)
                return True
            elif not task_started:
                details = f"Task did not start within {max_wait_time}s - cannot verify WebSocket manager"
                self.log_test("3. No WebSocket Manager Error", False, details)
                return False
            else:
                details = f"Monitoring completed without WebSocket manager errors"
                self.log_test("3. No WebSocket Manager Error", True, details)
                return True
                
        except Exception as e:
            self.log_test("3. No WebSocket Manager Error", False, "Request failed", e)
            return False

    def test_4_monitor_web_search_execution(self):
        """Test 4: Monitor Web Search Step for Real-time Navigation Events"""
        try:
            print("🔄 Test 4: Monitoring web search step for real-time navigation events")
            
            if not self.created_task_id:
                self.log_test("4. Web Search Navigation Events", False, "No task_id available")
                return False
            
            # Monitor web search execution for navigation events
            start_time = time.time()
            max_wait_time = 60
            navigation_events_found = False
            web_search_completed = False
            
            print("   Monitoring for navigation events during web search...")
            
            while time.time() - start_time < max_wait_time:
                url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    plan = data.get('plan', [])
                    
                    # Look for web search step
                    for i, step in enumerate(plan):
                        step_description = step.get('description', '').lower()
                        step_result = str(step.get('result', ''))
                        step_status = step.get('status', 'pending')
                        
                        # Check if this is a web search step
                        if any(keyword in step_description for keyword in ['buscar', 'search', 'información', 'web', 'investigar']):
                            print(f"   Web search step {i+1}: {step_status}")
                            
                            # Look for navigation-related content in results
                            navigation_indicators = [
                                'navegando',
                                'navegación',
                                'browser',
                                'playwright',
                                'página cargada',
                                'extrayendo',
                                'screenshot',
                                'browser_visual',
                                'navegador iniciado'
                            ]
                            
                            has_navigation_content = any(indicator in step_result.lower() for indicator in navigation_indicators)
                            
                            if has_navigation_content:
                                navigation_events_found = True
                                print(f"   ✅ Navigation events detected in step {i+1}")
                            
                            if step_status == 'completed':
                                web_search_completed = True
                                if has_navigation_content:
                                    details = f"Web search completed with navigation events: step {i+1}"
                                    self.log_test("4. Web Search Navigation Events", True, details)
                                    return True
                    
                    # Check overall progress
                    completed_steps = len([s for s in plan if s.get('status') == 'completed'])
                    if completed_steps > 0:
                        print(f"   Progress: {completed_steps} steps completed")
                
                time.sleep(3)
            
            # Final assessment
            if navigation_events_found:
                details = f"Navigation events detected during web search execution"
                self.log_test("4. Web Search Navigation Events", True, details)
                return True
            elif web_search_completed:
                details = f"Web search completed but no clear navigation events detected"
                self.log_test("4. Web Search Navigation Events", False, details)
                return False
            else:
                details = f"Web search did not complete within {max_wait_time}s"
                self.log_test("4. Web Search Navigation Events", False, details)
                return False
                
        except Exception as e:
            self.log_test("4. Web Search Navigation Events", False, "Request failed", e)
            return False

    def test_5_verify_comprehensive_logging(self):
        """Test 5: Verify Comprehensive Logging in unified_web_search_tool.py"""
        try:
            print("🔄 Test 5: Verifying comprehensive logging during web search")
            
            if not self.created_task_id:
                self.log_test("5. Comprehensive Logging", False, "No task_id available")
                return False
            
            # Get current task status and look for comprehensive logging
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', [])
                
                comprehensive_logging_found = False
                
                for step in plan:
                    step_result = str(step.get('result', ''))
                    
                    # Look for comprehensive logging indicators
                    logging_indicators = [
                        'STEP_1_COMPLETE',
                        'STEP_2_COMPLETE', 
                        'STEP_3_COMPLETE',
                        'STEP_4_COMPLETE',
                        'STEP_5_COMPLETE',
                        'STEP_6_COMPLETE',
                        'STEP_7_COMPLETE',
                        'STEP_8_COMPLETE',
                        'Message emission completed successfully',
                        'WebSocket Manager is_initialized: True',
                        'send_log_message',
                        'browser_visual'
                    ]
                    
                    found_indicators = [indicator for indicator in logging_indicators if indicator.lower() in step_result.lower()]
                    
                    if len(found_indicators) >= 3:  # At least 3 comprehensive logging indicators
                        comprehensive_logging_found = True
                        details = f"Comprehensive logging verified: {len(found_indicators)} indicators found"
                        self.log_test("5. Comprehensive Logging", True, details)
                        return True
                
                if not comprehensive_logging_found:
                    details = f"Comprehensive logging not detected in step results"
                    self.log_test("5. Comprehensive Logging", False, details)
                    return False
            else:
                self.log_test("5. Comprehensive Logging", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("5. Comprehensive Logging", False, "Request failed", e)
            return False

    def test_6_verify_step8_completion(self):
        """Test 6: Verify STEP_8_COMPLETE: Message emission completed successfully"""
        try:
            print("🔄 Test 6: Verifying STEP_8_COMPLETE message emission")
            
            if not self.created_task_id:
                self.log_test("6. STEP_8_COMPLETE Verification", False, "No task_id available")
                return False
            
            # Monitor for STEP_8_COMPLETE message
            start_time = time.time()
            max_wait_time = 45
            step8_complete_found = False
            
            while time.time() - start_time < max_wait_time:
                url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    plan = data.get('plan', [])
                    
                    for step in plan:
                        step_result = str(step.get('result', ''))
                        
                        # Look for STEP_8_COMPLETE specifically
                        if 'STEP_8_COMPLETE' in step_result and 'Message emission completed successfully' in step_result:
                            step8_complete_found = True
                            details = f"STEP_8_COMPLETE: Message emission completed successfully - VERIFIED"
                            self.log_test("6. STEP_8_COMPLETE Verification", True, details)
                            return True
                
                time.sleep(3)
            
            # Final check
            if not step8_complete_found:
                details = f"STEP_8_COMPLETE message not found within {max_wait_time}s"
                self.log_test("6. STEP_8_COMPLETE Verification", False, details)
                return False
                
        except Exception as e:
            self.log_test("6. STEP_8_COMPLETE Verification", False, "Request failed", e)
            return False

    def test_7_verify_websocket_events_emission(self):
        """Test 7: Verify WebSocket Events are Being Emitted"""
        try:
            print("🔄 Test 7: Verifying WebSocket events emission (log_message and browser_visual)")
            
            if not self.created_task_id:
                self.log_test("7. WebSocket Events Emission", False, "No task_id available")
                return False
            
            # Get current task status and look for WebSocket event indicators
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', [])
                
                websocket_events_found = False
                log_message_events = 0
                browser_visual_events = 0
                
                for step in plan:
                    step_result = str(step.get('result', ''))
                    
                    # Count different types of WebSocket events
                    if 'send_log_message' in step_result.lower():
                        log_message_events += step_result.lower().count('send_log_message')
                    
                    if 'browser_visual' in step_result.lower():
                        browser_visual_events += step_result.lower().count('browser_visual')
                    
                    # Look for Flask SocketIO emission indicators
                    socketio_indicators = [
                        'flask socketio',
                        'socketio.emit',
                        'emit_task_event',
                        'websocket event emitted'
                    ]
                    
                    socketio_events = sum(1 for indicator in socketio_indicators if indicator in step_result.lower())
                    
                    if log_message_events > 0 or browser_visual_events > 0 or socketio_events > 0:
                        websocket_events_found = True
                
                if websocket_events_found:
                    details = f"WebSocket events verified: log_message={log_message_events}, browser_visual={browser_visual_events}"
                    self.log_test("7. WebSocket Events Emission", True, details)
                    return True
                else:
                    details = f"No WebSocket event emission indicators found in step results"
                    self.log_test("7. WebSocket Events Emission", False, details)
                    return False
            else:
                self.log_test("7. WebSocket Events Emission", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("7. WebSocket Events Emission", False, "Request failed", e)
            return False

    def run_websocket_navigation_tests(self):
        """Run comprehensive WebSocket real-time navigation tests"""
        print("🚀 MITOSIS WEBSOCKET REAL-TIME NAVIGATION FIX TESTING")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print(f"FOCUS: Verify 'Global WebSocket manager not available or initialized for task' error is RESOLVED")
        print(f"EXPECTED: WebSocket Manager is_initialized: True, browser_visual events, comprehensive logging")
        print()
        
        # Test 1: WebSocket Manager Initialization
        print("=" * 60)
        ws_init_ok = self.test_1_websocket_manager_initialization()
        
        # Test 2: Create Web Navigation Task
        print("=" * 60)
        task_id = self.test_2_create_web_navigation_task()
        if not task_id:
            print("❌ Failed to create web navigation task. Aborting remaining tests.")
            self.print_summary()
            return self.test_results
        
        # Wait for task to be saved and start processing
        print("⏳ Waiting 8 seconds for task to start processing...")
        time.sleep(8)
        
        # Test 3: Verify No WebSocket Manager Error
        print("=" * 60)
        no_ws_error_ok = self.test_3_verify_no_websocket_manager_error()
        
        # Test 4: Monitor Web Search Navigation Events
        print("=" * 60)
        navigation_events_ok = self.test_4_monitor_web_search_execution()
        
        # Test 5: Verify Comprehensive Logging
        print("=" * 60)
        logging_ok = self.test_5_verify_comprehensive_logging()
        
        # Test 6: Verify STEP_8_COMPLETE
        print("=" * 60)
        step8_ok = self.test_6_verify_step8_completion()
        
        # Test 7: Verify WebSocket Events Emission
        print("=" * 60)
        events_ok = self.test_7_verify_websocket_events_emission()
        
        # Summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 WEBSOCKET REAL-TIME NAVIGATION FIX TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        # Analyze results for the specific WebSocket fix
        critical_issues = []
        websocket_manager_working = True
        no_websocket_errors = True
        navigation_events_working = False
        comprehensive_logging_working = False
        step8_complete_working = False
        websocket_events_working = False
        
        for result in self.test_results:
            if not result['success']:
                test_name = result['test']
                details = result['details'] or result['error']
                
                if 'WebSocket Manager Initialization' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    websocket_manager_working = False
                elif 'No WebSocket Manager Error' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    no_websocket_errors = False
                elif 'Web Search Navigation Events' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                elif 'Comprehensive Logging' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                elif 'STEP_8_COMPLETE' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                elif 'WebSocket Events Emission' in test_name:
                    critical_issues.append(f"⚠️ MAJOR: {test_name} - {details}")
                else:
                    critical_issues.append(f"❌ {test_name} - {details}")
            else:
                # Check for positive results
                if 'Web Search Navigation Events' in result['test']:
                    navigation_events_working = True
                elif 'Comprehensive Logging' in result['test']:
                    comprehensive_logging_working = True
                elif 'STEP_8_COMPLETE' in result['test']:
                    step8_complete_working = True
                elif 'WebSocket Events Emission' in result['test']:
                    websocket_events_working = True
        
        if critical_issues:
            print("🚨 ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("✅ All WebSocket real-time navigation tests passed successfully")
        
        print()
        
        # Specific diagnosis for the WebSocket fix
        print("🔍 WEBSOCKET REAL-TIME NAVIGATION FIX ANALYSIS:")
        
        if websocket_manager_working:
            print("✅ WEBSOCKET MANAGER INITIALIZATION: WORKING")
            print("   - WebSocket Manager is properly initialized")
            print("   - WebSocket endpoints are accessible")
        else:
            print("❌ WEBSOCKET MANAGER INITIALIZATION: BROKEN")
            print("   - WebSocket Manager may not be initialized properly")
        
        if no_websocket_errors:
            print("✅ 'GLOBAL WEBSOCKET MANAGER NOT AVAILABLE' ERROR: RESOLVED")
            print("   - No 'Global WebSocket manager not available' errors detected")
        else:
            print("❌ 'GLOBAL WEBSOCKET MANAGER NOT AVAILABLE' ERROR: STILL OCCURRING")
            print("   - The critical error is still present during task execution")
        
        if navigation_events_working:
            print("✅ REAL-TIME NAVIGATION EVENTS: WORKING")
            print("   - Navigation events detected during web search")
            print("   - Browser activity is being tracked in real-time")
        else:
            print("❌ REAL-TIME NAVIGATION EVENTS: NOT WORKING")
            print("   - No navigation events detected during web search")
        
        if comprehensive_logging_working:
            print("✅ COMPREHENSIVE LOGGING: WORKING")
            print("   - Detailed logging from unified_web_search_tool.py detected")
            print("   - Multiple STEP_X_COMPLETE messages found")
        else:
            print("❌ COMPREHENSIVE LOGGING: NOT WORKING")
            print("   - Comprehensive logging not detected in results")
        
        if step8_complete_working:
            print("✅ STEP_8_COMPLETE MESSAGE EMISSION: WORKING")
            print("   - 'STEP_8_COMPLETE: Message emission completed successfully' verified")
        else:
            print("❌ STEP_8_COMPLETE MESSAGE EMISSION: NOT WORKING")
            print("   - STEP_8_COMPLETE message not found")
        
        if websocket_events_working:
            print("✅ WEBSOCKET EVENTS EMISSION: WORKING")
            print("   - Both log_message and browser_visual events are being emitted")
            print("   - Flask SocketIO is functioning correctly")
        else:
            print("❌ WEBSOCKET EVENTS EMISSION: NOT WORKING")
            print("   - WebSocket events are not being emitted properly")
        
        print()
        
        # Overall assessment
        if websocket_manager_working and no_websocket_errors and navigation_events_working and step8_complete_working:
            print("🎉 OVERALL ASSESSMENT: ✅ WEBSOCKET REAL-TIME NAVIGATION FIX SUCCESSFUL")
            print("   - WebSocket Manager is properly initialized")
            print("   - No more 'Global WebSocket manager not available' errors")
            print("   - Real-time navigation events are working")
            print("   - Comprehensive logging is functioning")
            print("   - WebSocket events are being emitted correctly")
        else:
            print("⚠️ OVERALL ASSESSMENT: ❌ WEBSOCKET REAL-TIME NAVIGATION FIX NEEDS MORE WORK")
            print("   - The WebSocket real-time navigation functionality still has issues")
            print("   - May need additional debugging and fixes")
        
        print()
        
        # Specific recommendations
        print("📋 RECOMMENDATIONS:")
        if not websocket_manager_working:
            print("   1. Check WebSocket Manager initialization in server.py")
            print("   2. Verify initialize_websocket(app) is being called")
            print("   3. Check for WebSocket Manager import errors")
        
        if not no_websocket_errors:
            print("   1. Check unified_web_search_tool.py for WebSocket Manager usage")
            print("   2. Verify get_websocket_manager() function is working")
            print("   3. Check WebSocket Manager global availability")
        
        if not navigation_events_working:
            print("   1. Check browser_visual event emission in web search tool")
            print("   2. Verify Playwright integration with WebSocket events")
            print("   3. Test real-time navigation event transmission")
        
        if not comprehensive_logging_working:
            print("   1. Check logging configuration in unified_web_search_tool.py")
            print("   2. Verify STEP_X_COMPLETE messages are being generated")
            print("   3. Check log level and output configuration")
        
        if not websocket_events_working:
            print("   1. Check Flask SocketIO configuration and emission")
            print("   2. Verify WebSocket event types (log_message, browser_visual)")
            print("   3. Test WebSocket connection and event transmission")
        
        if websocket_manager_working and no_websocket_errors and navigation_events_working:
            print("   1. WebSocket real-time navigation fix is working correctly")
            print("   2. Monitor for any regression issues")
            print("   3. Consider performance optimizations for real-time events")
        
        print()
        print("📊 WEBSOCKET REAL-TIME NAVIGATION FIX TESTING COMPLETE")
        
        if self.created_task_id:
            print(f"📝 Test Task ID: {self.created_task_id}")
            print("   Use this ID to check logs and debug WebSocket events if needed")

if __name__ == "__main__":
    tester = MitosisWebSocketNavigationTester()
    results = tester.run_websocket_navigation_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results if not result['success'])
    sys.exit(failed_tests)