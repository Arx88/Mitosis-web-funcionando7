#!/usr/bin/env python3
"""
MITOSIS BACKEND TESTING - SOLAR ENERGY REPORT META-CONTENT ISSUE
Test the specific "meta-informes" problem reported by the user.

SPECIFIC TESTING REQUEST FROM USER:
Test if the corrections to the "meta-informes" problem in Mitosis work correctly.

ORIGINAL PROBLEM REPORTED:
When user asks "Escribe un informe sobre los beneficios de la energía solar", 
the agent returns a meta-report saying "Este informe analizará los beneficios de la energía solar..." 
instead of the REAL report with specific content about solar energy.

CORRECTIONS MADE:
Modified functions in /app/backend/src/routes/agent_routes.py:
1. generate_professional_final_report (lines 1289-1320) 
2. execute_analysis_step (lines 997-1015)
3. execute_processing_step (lines 1814-1836) 
4. generate_unified_ai_plan (lines 4251-4302)

SPECIFIC TEST REQUIRED:
1. Go to https://38146bbb-fcab-42f6-9cbd-f49422f98546.preview.emergentagent.com
2. Send the EXACT task: "Escribe un informe sobre los beneficios de la energía solar"
3. Wait full time for execution (up to 5-10 minutes if necessary)
4. Verify the final generated content

EXPECTED RESULT (CORRECT):
- Content saying "Los beneficios de la energía solar incluyen..."
- Specific information about economic, environmental, technical advantages
- Concrete data about efficiency, costs, impact
- Useful and specific content about solar energy

PROBLEMATIC RESULT (TO BE AVOIDED):
- "Este informe analizará los beneficios de la energía solar"
- "Se procederá a estudiar los aspectos de la energía solar"
- "Los objetivos de este documento son..."
- Any meta-content describing what will be done

**URL Backend**: https://38146bbb-fcab-42f6-9cbd-f49422f98546.preview.emergentagent.com
**WebSocket URL**: /api/socket.io/
**Test Task**: "Escribe un informe sobre los beneficios de la energía solar"
"""

import requests
import json
import time
import os
import sys
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL from environment - test both internal and external URLs
BACKEND_URL = "https://38146bbb-fcab-42f6-9cbd-f49422f98546.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisSolarEnergyReportTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://38146bbb-fcab-42f6-9cbd-f49422f98546.preview.emergentagent.com'
        })
        self.test_results = []
        self.task_id = None
        self.websocket_events = []
        self.final_report_content = ""
        self.websocket_connected = False
        self.sio = None
        self.monitoring_active = False
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)[:500]}...")
    
    def setup_websocket_client(self) -> bool:
        """Setup WebSocket client for real-time monitoring"""
        try:
            # Try to import socketio, if not available, skip WebSocket tests
            try:
                import socketio
            except ImportError:
                print("⚠️ python-socketio not available, installing...")
                os.system("pip install python-socketio[client]")
                import socketio
            
            self.sio = socketio.Client(
                logger=False,
                engineio_logger=False,
                reconnection=True,
                reconnection_attempts=3,
                reconnection_delay=1
            )
            
            @self.sio.event
            def connect():
                self.websocket_connected = True
                print("🔌 WebSocket connected successfully")
                self.websocket_events.append({
                    'event': 'connect',
                    'timestamp': datetime.now().isoformat(),
                    'data': None
                })
            
            @self.sio.event
            def disconnect():
                self.websocket_connected = False
                print("🔌 WebSocket disconnected")
                self.websocket_events.append({
                    'event': 'disconnect',
                    'timestamp': datetime.now().isoformat(),
                    'data': None
                })
            
            @self.sio.event
            def task_progress(data):
                print(f"📊 WebSocket Event - task_progress: {data}")
                self.websocket_events.append({
                    'event': 'task_progress',
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                })
            
            @self.sio.event
            def step_completed(data):
                print(f"✅ WebSocket Event - step_completed: {data}")
                self.websocket_events.append({
                    'event': 'step_completed',
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                })
                
                # Capture final report content if available
                if isinstance(data, dict) and 'result' in data:
                    result = data['result']
                    if isinstance(result, str) and len(result) > 100:
                        self.final_report_content = result
                        print(f"   📄 Captured report content: {len(result)} characters")
            
            @self.sio.event
            def task_completed(data):
                print(f"🎉 WebSocket Event - task_completed: {data}")
                self.websocket_events.append({
                    'event': 'task_completed',
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                })
                
                # Capture final report content if available
                if isinstance(data, dict) and 'result' in data:
                    result = data['result']
                    if isinstance(result, str) and len(result) > 100:
                        self.final_report_content = result
                        print(f"   📄 Captured final report: {len(result)} characters")
            
            @self.sio.event
            def terminal_output(data):
                print(f"💻 WebSocket Event - terminal_output: {data}")
                self.websocket_events.append({
                    'event': 'terminal_output',
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                })
            
            @self.sio.event
            def error(data):
                print(f"❌ WebSocket Event - error: {data}")
                self.websocket_events.append({
                    'event': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                })
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup WebSocket client: {e}")
            return False
    
    def connect_websocket(self) -> bool:
        """Connect to WebSocket server"""
        try:
            websocket_url = f"{BACKEND_URL}/api/socket.io/"
            print(f"🔌 Connecting to WebSocket: {websocket_url}")
            
            self.sio.connect(websocket_url, transports=['polling', 'websocket'])
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.websocket_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.websocket_connected:
                print("✅ WebSocket connection established")
                return True
            else:
                print("❌ WebSocket connection timeout")
                return False
                
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False
    
    def join_task_room(self, task_id: str) -> bool:
        """Join task-specific WebSocket room"""
        try:
            if self.sio and self.websocket_connected:
                self.sio.emit('join_task', {'task_id': task_id})
                print(f"🏠 Joined task room: {task_id}")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to join task room: {e}")
            return False
    
    def test_create_solar_energy_task(self) -> bool:
        """Test 1: Create the exact solar energy report task"""
        try:
            # Use the EXACT test task from the review request
            test_message = "Escribe un informe sobre los beneficios de la energía solar"
            
            payload = {
                "message": test_message
            }
            
            print(f"\n🌞 Creating solar energy report task: {test_message}")
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required response fields
                response_text = data.get('response', '')
                task_id = data.get('task_id', '')
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                
                # Store task_id for later tests
                if task_id:
                    self.task_id = task_id
                    print(f"   📋 Task created with ID: {task_id}")
                
                # Verify plan structure for solar energy task
                if plan and len(plan) >= 2:
                    # Check if plan has proper structure for solar energy report
                    valid_plan = True
                    step_details = []
                    tools_used = set()
                    
                    for i, step in enumerate(plan):
                        if not all(key in step for key in ['title', 'description', 'tool']):
                            valid_plan = False
                            break
                        step_details.append(f"Step {i+1}: {step.get('title', 'No title')}")
                        tools_used.add(step.get('tool', 'unknown'))
                    
                    # Check if it's actually a solar energy report task
                    solar_keywords = ['solar', 'energía', 'informe', 'beneficios', 'renovable', 'sostenible']
                    plan_text = json.dumps(plan).lower()
                    has_solar_content = any(keyword in plan_text for keyword in solar_keywords)
                    
                    if valid_plan and response_text and task_id and enhanced_title and has_solar_content:
                        self.log_test("Create Solar Energy Task", True, 
                                    f"Solar energy task created - {len(plan)} steps, {len(tools_used)} tools, Task ID: {task_id}")
                        print(f"   📊 Plan steps: {'; '.join(step_details[:2])}...")
                        print(f"   🛠️ Tools to be used: {', '.join(list(tools_used)[:3])}...")
                        return True
                    else:
                        self.log_test("Create Solar Energy Task", False, 
                                    f"Task not properly structured - Valid plan: {valid_plan}, Solar content: {has_solar_content}", data)
                        return False
                else:
                    self.log_test("Create Solar Energy Task", False, 
                                f"Plan not generated or insufficient steps - Plan length: {len(plan) if plan else 0}", data)
                    return False
            else:
                self.log_test("Create Solar Energy Task", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Create Solar Energy Task", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_monitoring_setup(self) -> bool:
        """Test 2: WebSocket Connection and Real-time Monitoring Setup"""
        try:
            print(f"\n🔌 Setting up WebSocket connection for real-time monitoring...")
            
            # Setup WebSocket client
            if not self.setup_websocket_client():
                self.log_test("WebSocket Monitoring Setup", False, "Failed to setup WebSocket client")
                return False
            
            # Connect to WebSocket
            if not self.connect_websocket():
                self.log_test("WebSocket Monitoring Setup", False, "Failed to connect to WebSocket server")
                return False
            
            # Join task room if we have a task ID
            if self.task_id:
                if not self.join_task_room(self.task_id):
                    self.log_test("WebSocket Monitoring Setup", False, "Failed to join task room")
                    return False
            
            # Test WebSocket is ready for monitoring
            if self.websocket_connected and self.sio:
                self.log_test("WebSocket Monitoring Setup", True, 
                            f"WebSocket connected and ready for monitoring - Task room: {self.task_id}")
                return True
            else:
                self.log_test("WebSocket Monitoring Setup", False, "WebSocket not properly connected")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Monitoring Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_task_execution_and_monitoring(self) -> bool:
        """Test 3: Task Execution and Long-term Monitoring (up to 10 minutes)"""
        try:
            if not self.task_id:
                self.log_test("Task Execution and Monitoring", False, "No task ID available for execution")
                return False
            
            print(f"\n🚀 Starting task execution and monitoring for: {self.task_id}")
            print("⏱️ This will monitor for up to 10 minutes to capture the full execution...")
            
            # Monitor for up to 10 minutes (600 seconds) to capture full execution
            monitoring_duration = 600  # 10 minutes
            start_time = time.time()
            initial_events = len(self.websocket_events)
            
            task_completed = False
            execution_started = False
            
            while (time.time() - start_time) < monitoring_duration:
                time.sleep(2)  # Check every 2 seconds
                
                # Check for task progress events
                new_events = self.websocket_events[initial_events:]
                
                # Look for execution start
                if not execution_started:
                    progress_events = [e for e in new_events if e['event'] in ['task_progress', 'step_completed']]
                    if progress_events:
                        execution_started = True
                        print(f"   🎯 Task execution started - {len(progress_events)} progress events detected")
                
                # Look for task completion
                completion_events = [e for e in new_events if e['event'] == 'task_completed']
                if completion_events:
                    task_completed = True
                    print(f"   🎉 Task completion detected after {time.time() - start_time:.1f} seconds")
                    break
                
                # Print periodic updates
                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0:  # Every 30 seconds
                    total_new_events = len(new_events)
                    print(f"   ⏱️ Monitoring: {elapsed:.0f}s elapsed, {total_new_events} events captured")
            
            # Analyze results
            final_events = self.websocket_events[initial_events:]
            total_events = len(final_events)
            progress_events = [e for e in final_events if e['event'] in ['task_progress', 'step_completed']]
            completion_events = [e for e in final_events if e['event'] == 'task_completed']
            
            elapsed_time = time.time() - start_time
            
            if task_completed and len(progress_events) > 0:
                self.log_test("Task Execution and Monitoring", True, 
                            f"Task completed successfully - {elapsed_time:.1f}s, {total_events} events, {len(progress_events)} progress events")
                return True
            elif execution_started and len(progress_events) > 0:
                self.log_test("Task Execution and Monitoring", True, 
                            f"Task execution in progress - {elapsed_time:.1f}s, {total_events} events, {len(progress_events)} progress events")
                return True
            elif total_events > 0:
                self.log_test("Task Execution and Monitoring", False, 
                            f"Task execution unclear - {elapsed_time:.1f}s, {total_events} events, {len(progress_events)} progress events")
                return False
            else:
                self.log_test("Task Execution and Monitoring", False, 
                            f"No task execution detected - {elapsed_time:.1f}s, no events received")
                return False
                
        except Exception as e:
            self.log_test("Task Execution and Monitoring", False, f"Exception: {str(e)}")
            return False
    
    def test_final_report_content_analysis(self) -> bool:
        """Test 4: Final Report Content Analysis (Meta vs Real Content)"""
        try:
            print(f"\n📄 Analyzing final report content for meta vs real content...")
            
            # Try to get final report content from multiple sources
            report_content = ""
            
            # Source 1: From WebSocket events
            if self.final_report_content:
                report_content = self.final_report_content
                print(f"   📡 Using report from WebSocket events: {len(report_content)} characters")
            
            # Source 2: Try to fetch final report via API
            if not report_content and self.task_id:
                try:
                    report_response = self.session.get(f"{API_BASE}/agent/generate-final-report/{self.task_id}", timeout=30)
                    if report_response.status_code == 200:
                        report_data = report_response.json()
                        if 'report' in report_data:
                            report_content = report_data['report']
                            print(f"   🌐 Using report from API endpoint: {len(report_content)} characters")
                except Exception as e:
                    print(f"   ⚠️ Could not fetch report via API: {e}")
            
            # Source 3: Check WebSocket events for any content
            if not report_content:
                for event in reversed(self.websocket_events):
                    if event['event'] in ['step_completed', 'task_completed'] and event['data']:
                        data = event['data']
                        if isinstance(data, dict) and 'result' in data:
                            result = data['result']
                            if isinstance(result, str) and len(result) > 200:
                                report_content = result
                                print(f"   🔍 Using report from WebSocket event: {len(report_content)} characters")
                                break
            
            if not report_content:
                self.log_test("Final Report Content Analysis", False, 
                            "No final report content found to analyze")
                return False
            
            # Analyze content for meta vs real content
            print(f"   📊 Analyzing report content: {len(report_content)} characters")
            
            # Meta-content indicators (PROBLEMATIC)
            meta_indicators = [
                "este informe analizará",
                "se procederá a estudiar",
                "los objetivos de este documento",
                "el presente documento tiene como objetivo",
                "a continuación se analizará",
                "en este informe se estudiará",
                "el propósito de este análisis",
                "este documento pretende",
                "se realizará un análisis",
                "el objetivo principal es analizar"
            ]
            
            # Real content indicators (EXPECTED)
            real_content_indicators = [
                "los beneficios de la energía solar incluyen",
                "la energía solar ofrece",
                "ventajas económicas",
                "ventajas ambientales",
                "eficiencia energética",
                "reducción de costos",
                "impacto ambiental",
                "tecnología fotovoltaica",
                "paneles solares",
                "energía renovable",
                "sostenibilidad",
                "ahorro energético"
            ]
            
            # Check for meta-content (bad)
            meta_count = 0
            found_meta_indicators = []
            report_lower = report_content.lower()
            
            for indicator in meta_indicators:
                if indicator in report_lower:
                    meta_count += 1
                    found_meta_indicators.append(indicator)
            
            # Check for real content (good)
            real_count = 0
            found_real_indicators = []
            
            for indicator in real_content_indicators:
                if indicator in report_lower:
                    real_count += 1
                    found_real_indicators.append(indicator)
            
            # Analyze content quality
            has_specific_data = bool(re.search(r'\d+%|\d+\s*(kwh|mw|gw|euros?|dólares?)', report_lower))
            has_technical_terms = len([term for term in ['fotovoltaica', 'inversor', 'batería', 'red eléctrica'] if term in report_lower]) > 0
            content_length_adequate = len(report_content) > 500
            
            print(f"   🔍 Content Analysis Results:")
            print(f"      Meta indicators found: {meta_count} - {found_meta_indicators[:3]}")
            print(f"      Real content indicators: {real_count} - {found_real_indicators[:3]}")
            print(f"      Has specific data: {has_specific_data}")
            print(f"      Has technical terms: {has_technical_terms}")
            print(f"      Content length adequate: {content_length_adequate} ({len(report_content)} chars)")
            
            # Sample of the content for manual review
            content_sample = report_content[:300] + "..." if len(report_content) > 300 else report_content
            print(f"   📝 Content sample: {content_sample}")
            
            # Determine if this is real content vs meta-content
            is_real_content = (
                real_count >= 3 and  # At least 3 real content indicators
                meta_count <= 1 and  # At most 1 meta indicator
                content_length_adequate and  # Adequate length
                (has_specific_data or has_technical_terms)  # Has specific data or technical terms
            )
            
            is_meta_content = (
                meta_count >= 2 or  # 2 or more meta indicators
                (meta_count >= 1 and real_count <= 1)  # Meta indicators with little real content
            )
            
            if is_real_content and not is_meta_content:
                self.log_test("Final Report Content Analysis", True, 
                            f"REAL CONTENT DETECTED - {real_count} real indicators, {meta_count} meta indicators, {len(report_content)} chars")
                print("   ✅ SUCCESS: Agent generated REAL content about solar energy benefits")
                print("   🎯 CONCLUSION: Meta-informes problem appears to be RESOLVED")
                return True
            elif is_meta_content:
                self.log_test("Final Report Content Analysis", False, 
                            f"META-CONTENT DETECTED - {meta_count} meta indicators, {real_count} real indicators")
                print("   ❌ PROBLEM: Agent generated META-CONTENT instead of real information")
                print("   🎯 CONCLUSION: Meta-informes problem PERSISTS")
                return False
            else:
                self.log_test("Final Report Content Analysis", False, 
                            f"UNCLEAR CONTENT - {real_count} real indicators, {meta_count} meta indicators, needs manual review")
                print("   ⚠️ UNCLEAR: Content quality unclear, manual review needed")
                return False
                
        except Exception as e:
            self.log_test("Final Report Content Analysis", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_websocket(self):
        """Cleanup WebSocket connection"""
        try:
            if self.sio and self.websocket_connected:
                self.sio.disconnect()
                print("🔌 WebSocket disconnected")
        except Exception as e:
            print(f"⚠️ Error during WebSocket cleanup: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all solar energy report tests"""
        print("🧪 STARTING MITOSIS SOLAR ENERGY REPORT META-CONTENT TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing if meta-informes problem is resolved")
        print("📋 TESTING: Solar energy report generation, content analysis")
        print("🔍 TEST TASK: 'Escribe un informe sobre los beneficios de la energía solar'")
        print("⚠️ INVESTIGATING: Meta-content vs real content generation")
        print("=" * 80)
        
        # Test sequence focused on solar energy report content
        tests = [
            ("Create Solar Energy Task", self.test_create_solar_energy_task),
            ("WebSocket Monitoring Setup", self.test_websocket_monitoring_setup),
            ("Task Execution and Monitoring", self.test_task_execution_and_monitoring),
            ("Final Report Content Analysis", self.test_final_report_content_analysis)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        try:
            for test_name, test_func in tests:
                print(f"\n🔍 Running: {test_name}")
                try:
                    result = test_func()
                    if result:
                        passed_tests += 1
                    time.sleep(2)  # Brief pause between tests
                except Exception as e:
                    self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        finally:
            # Always cleanup WebSocket connection
            self.cleanup_websocket()
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 80)
        print("🎯 MITOSIS SOLAR ENERGY REPORT TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # WebSocket Events Summary
        print(f"\n📡 WEBSOCKET EVENTS SUMMARY:")
        print(f"   Total Events Captured: {len(self.websocket_events)}")
        
        if self.websocket_events:
            from collections import defaultdict
            event_types = defaultdict(int)
            for event in self.websocket_events:
                event_types[event['event']] += 1
            
            for event_type, count in event_types.items():
                print(f"   - {event_type}: {count} events")
        
        # Final Report Summary
        print(f"\n📄 FINAL REPORT SUMMARY:")
        if self.final_report_content:
            print(f"   Report Content Captured: {len(self.final_report_content)} characters")
            print(f"   Report Sample: {self.final_report_content[:150]}...")
        else:
            print("   No final report content captured")
        
        # Determine overall status
        content_analysis_result = next((r for r in self.test_results if r['test_name'] == 'Final Report Content Analysis'), None)
        
        if content_analysis_result and content_analysis_result['success']:
            overall_status = "✅ META-INFORMES PROBLEM RESOLVED - Real content generated"
        elif content_analysis_result and not content_analysis_result['success']:
            overall_status = "❌ META-INFORMES PROBLEM PERSISTS - Meta-content still generated"
        elif success_rate >= 75:
            overall_status = "⚠️ TESTING MOSTLY SUCCESSFUL - Content analysis needed"
        else:
            overall_status = "❌ TESTING FAILED - Could not complete analysis"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for meta-informes issue
        print(f"\n🔥 CRITICAL META-INFORMES ANALYSIS:")
        
        if content_analysis_result:
            if content_analysis_result['success']:
                print("   ✅ REAL CONTENT GENERATED: Agent produced specific solar energy information")
                print("   🎯 CONCLUSION: Meta-informes corrections are WORKING")
                print("   📋 RECOMMENDATION: The fixes appear to be successful")
            else:
                print("   ❌ META-CONTENT DETECTED: Agent still producing meta-descriptions")
                print("   🎯 CONCLUSION: Meta-informes corrections are NOT WORKING")
                print("   📋 RECOMMENDATION: Further fixes needed in report generation functions")
        else:
            print("   ⚠️ CONTENT ANALYSIS INCOMPLETE: Could not analyze final report content")
            print("   🎯 CONCLUSION: Unable to determine if meta-informes issue is resolved")
            print("   📋 RECOMMENDATION: Manual testing required")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'test_results': self.test_results,
            'task_id': self.task_id,
            'websocket_events': self.websocket_events,
            'final_report_content': self.final_report_content,
            'meta_informes_resolved': content_analysis_result and content_analysis_result['success'] if content_analysis_result else False,
            'content_analysis_completed': content_analysis_result is not None
        }

def main():
    """Main testing function"""
    tester = MitosisSolarEnergyReportTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/solar_energy_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR MAIN AGENT")
    print("=" * 80)
    
    if results.get('meta_informes_resolved'):
        print("✅ META-INFORMES DIAGNOSIS: The corrections are working correctly")
        print("📋 RECOMMENDATION: Agent now generates REAL content instead of meta-descriptions")
        print("🔧 NEXT STEPS: The solar energy report issue appears to be resolved")
        print("🎉 SUCCESS: User should now receive actual solar energy benefits information")
    elif results.get('content_analysis_completed'):
        print("❌ META-INFORMES DIAGNOSIS: The corrections are NOT working")
        print("📋 RECOMMENDATION: Agent still generates meta-content instead of real information")
        print("🔧 NEXT STEPS: Further fixes needed in report generation functions")
        print("⚠️ ISSUE PERSISTS: User will still receive meta-descriptions instead of real content")
    else:
        print("⚠️ META-INFORMES DIAGNOSIS: Could not complete content analysis")
        print("📋 RECOMMENDATION: Manual testing required to verify corrections")
        print("🔧 NEXT STEPS: Test the exact task manually in the frontend")
        print("❓ UNCLEAR: Unable to determine if the issue is resolved")
    
    # Specific user issue analysis
    print(f"\n🔍 SPECIFIC SOLAR ENERGY REPORT ANALYSIS:")
    
    if results.get('meta_informes_resolved'):
        print("   ✅ ISSUE RESOLVED: 'Escribe un informe sobre los beneficios de la energía solar' now generates real content")
        print("   📄 EXPECTED RESULT: Content includes specific benefits, data, and technical information")
        print("   🚫 AVOIDED RESULT: No more 'Este informe analizará...' meta-descriptions")
    elif results.get('content_analysis_completed'):
        print("   ❌ ISSUE PERSISTS: 'Escribe un informe sobre los beneficios de la energía solar' still generates meta-content")
        print("   📄 PROBLEMATIC RESULT: Still receiving 'Este informe analizará...' descriptions")
        print("   🚫 MISSING RESULT: Not getting real solar energy benefits information")
    else:
        print("   ⚠️ ISSUE STATUS UNCLEAR: Could not analyze the solar energy report content")
        print("   📄 RECOMMENDATION: Test manually with the exact task")
        print("   🔍 MANUAL TEST: Go to the frontend and submit 'Escribe un informe sobre los beneficios de la energía solar'")
    
    # Return exit code based on success
    if results.get('meta_informes_resolved'):
        print("\n🎉 SOLAR ENERGY REPORT TESTING COMPLETED SUCCESSFULLY - ISSUE RESOLVED")
        return 0
    elif results.get('content_analysis_completed'):
        print("\n❌ SOLAR ENERGY REPORT TESTING COMPLETED - ISSUE PERSISTS")
        return 1
    else:
        print("\n⚠️ SOLAR ENERGY REPORT TESTING INCOMPLETE - MANUAL VERIFICATION NEEDED")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)