#!/usr/bin/env python3
"""
MITOSIS BACKEND REAL-TIME WEBSOCKET STEP PROGRESSION TESTING
Test the specific WebSocket step progression issue reported by the user.

SPECIFIC TESTING REQUEST FROM USER:
Test the Mitosis backend comprehensively focusing on the REAL-TIME WebSocket step progression issue:

1. **Create a task** with a complex plan that will take some time to execute
2. **Monitor WebSocket events** in real-time to verify step progression is sent correctly 
3. **Verify step sequence** - ensure steps execute 1→2→3→4 without jumping back
4. **Check step completion logic** - verify steps are only marked complete when they actually finish
5. **Monitor execution logs** - verify actual vs reported step progression
6. **Test frontend sync** - ensure frontend receives accurate real-time updates

SPECIFIC ISSUES TO INVESTIGATE:
- User reports agent jumps from step 3 back to step 2
- Steps being marked as "HECHO" (done) prematurely  
- Frontend may not be showing real agent action vs cached data
- Agent incorrectly determining task completion

**URL Backend**: https://6fdadea9-df4d-44a4-adc8-feca2d77c031.preview.emergentagent.com
**WebSocket URL**: /api/socket.io/
**Test Task**: "Crear análisis detallado sobre blockchain en 2025"
"""

import requests
import json
import time
import os
import sys
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Backend URL from environment - test both internal and external URLs
BACKEND_URL = "https://6fdadea9-df4d-44a4-adc8-feca2d77c031.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisWebSocketStepProgressionTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://6fdadea9-df4d-44a4-adc8-feca2d77c031.preview.emergentagent.com'
        })
        self.test_results = []
        self.task_id = None
        self.websocket_events = []
        self.step_progression = []
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
                
                # Track step progression
                if 'current_step' in data:
                    step_info = {
                        'step': data['current_step'],
                        'total_steps': data.get('total_steps', 4),
                        'status': data.get('status', 'unknown'),
                        'timestamp': datetime.now().isoformat()
                    }
                    self.step_progression.append(step_info)
                    print(f"   📈 Step progression: {step_info['step']}/{step_info['total_steps']} - {step_info['status']}")
            
            @self.sio.event
            def step_completed(data):
                print(f"✅ WebSocket Event - step_completed: {data}")
                self.websocket_events.append({
                    'event': 'step_completed',
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                })
                
                # Track step completion
                if 'step' in data:
                    step_info = {
                        'step': data['step'],
                        'completed': True,
                        'result': data.get('result', 'No result'),
                        'timestamp': datetime.now().isoformat()
                    }
                    self.step_progression.append(step_info)
                    print(f"   ✅ Step {data['step']} completed: {step_info['result'][:100]}...")
            
            @self.sio.event
            def task_completed(data):
                print(f"🎉 WebSocket Event - task_completed: {data}")
                self.websocket_events.append({
                    'event': 'task_completed',
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                })
            
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
    
    def test_create_complex_task(self) -> bool:
        """Test 1: Create a complex task that will take time to execute"""
        try:
            # Use the exact test task from the review request
            test_message = "Crear análisis detallado sobre blockchain en 2025"
            
            payload = {
                "message": test_message
            }
            
            print(f"\n🎯 Creating complex task: {test_message}")
            
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
                
                # Verify plan structure for complex task
                if plan and len(plan) >= 4:
                    # Check if plan has proper structure for blockchain analysis
                    valid_plan = True
                    step_details = []
                    tools_used = set()
                    
                    for i, step in enumerate(plan):
                        if not all(key in step for key in ['title', 'description', 'tool']):
                            valid_plan = False
                            break
                        step_details.append(f"Step {i+1}: {step.get('title', 'No title')}")
                        tools_used.add(step.get('tool', 'unknown'))
                    
                    # Check if it's actually a complex blockchain analysis task
                    blockchain_keywords = ['blockchain', 'análisis', 'detallado', '2025', 'mercado', 'tecnología']
                    plan_text = json.dumps(plan).lower()
                    has_blockchain_content = any(keyword in plan_text for keyword in blockchain_keywords)
                    
                    if valid_plan and response_text and task_id and enhanced_title and has_blockchain_content:
                        self.log_test("Create Complex Task", True, 
                                    f"Complex blockchain task created - {len(plan)} steps, {len(tools_used)} tools, Task ID: {task_id}")
                        print(f"   📊 Plan steps: {'; '.join(step_details[:2])}...")
                        print(f"   🛠️ Tools to be used: {', '.join(list(tools_used)[:3])}...")
                        return True
                    else:
                        self.log_test("Create Complex Task", False, 
                                    f"Task not complex enough - Valid plan: {valid_plan}, Blockchain content: {has_blockchain_content}", data)
                        return False
                else:
                    self.log_test("Create Complex Task", False, 
                                f"Plan not generated or insufficient steps - Plan length: {len(plan) if plan else 0}", data)
                    return False
            else:
                self.log_test("Create Complex Task", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Create Complex Task", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_connection_and_monitoring(self) -> bool:
        """Test 2: WebSocket Connection and Real-time Monitoring Setup"""
        try:
            print(f"\n🔌 Setting up WebSocket connection for real-time monitoring...")
            
            # Setup WebSocket client
            if not self.setup_websocket_client():
                self.log_test("WebSocket Connection", False, "Failed to setup WebSocket client")
                return False
            
            # Connect to WebSocket
            if not self.connect_websocket():
                self.log_test("WebSocket Connection", False, "Failed to connect to WebSocket server")
                return False
            
            # Join task room if we have a task ID
            if self.task_id:
                if not self.join_task_room(self.task_id):
                    self.log_test("WebSocket Connection", False, "Failed to join task room")
                    return False
            
            # Test WebSocket is ready for monitoring
            if self.websocket_connected and self.sio:
                self.log_test("WebSocket Connection", True, 
                            f"WebSocket connected and ready for monitoring - Task room: {self.task_id}")
                return True
            else:
                self.log_test("WebSocket Connection", False, "WebSocket not properly connected")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Exception: {str(e)}")
            return False
    
    def test_task_execution_trigger(self) -> bool:
        """Test 3: Task Execution Trigger and Initial Step Monitoring"""
        try:
            if not self.task_id:
                self.log_test("Task Execution Trigger", False, "No task ID available for execution")
                return False
            
            print(f"\n🚀 Triggering task execution for: {self.task_id}")
            
            # Try to trigger task execution
            execution_payload = {
                "task_id": self.task_id
            }
            
            # Test different execution endpoints
            execution_endpoints = [
                f"{API_BASE}/agent/start-task-execution/{self.task_id}",
                f"{API_BASE}/agent/execute-task",
                f"{API_BASE}/agent/execute/{self.task_id}"
            ]
            
            execution_triggered = False
            execution_response = None
            
            for endpoint in execution_endpoints:
                try:
                    print(f"   🔍 Trying execution endpoint: {endpoint}")
                    response = self.session.post(endpoint, json=execution_payload, timeout=15)
                    
                    if response.status_code == 200:
                        execution_response = response.json()
                        execution_triggered = True
                        print(f"   ✅ Execution triggered via: {endpoint}")
                        break
                    elif response.status_code == 404:
                        print(f"   ❌ Endpoint not found: {endpoint}")
                    else:
                        print(f"   ⚠️ Endpoint returned {response.status_code}: {endpoint}")
                        
                except Exception as e:
                    print(f"   ❌ Error with endpoint {endpoint}: {e}")
                    continue
            
            # Monitor for initial WebSocket events (first 10 seconds)
            print(f"   ⏱️ Monitoring for initial WebSocket events (10 seconds)...")
            initial_events_count = len(self.websocket_events)
            
            start_time = time.time()
            while (time.time() - start_time) < 10:
                time.sleep(0.5)
                
                # Check if we received any task progress events
                new_events = len(self.websocket_events) - initial_events_count
                if new_events > 0:
                    print(f"   📊 Received {new_events} WebSocket events during monitoring")
                    break
            
            # Analyze results
            final_events_count = len(self.websocket_events) - initial_events_count
            has_progress_events = any(event['event'] in ['task_progress', 'step_completed', 'terminal_output'] 
                                    for event in self.websocket_events[-final_events_count:])
            
            if execution_triggered and has_progress_events:
                self.log_test("Task Execution Trigger", True, 
                            f"Task execution triggered and WebSocket events received - {final_events_count} events")
                return True
            elif execution_triggered:
                self.log_test("Task Execution Trigger", False, 
                            f"Task execution triggered but no WebSocket events - {final_events_count} events")
                return False
            else:
                self.log_test("Task Execution Trigger", False, 
                            f"Task execution not triggered - No working execution endpoints found")
                return False
                
        except Exception as e:
            self.log_test("Task Execution Trigger", False, f"Exception: {str(e)}")
            return False
    
    def test_step_sequence_monitoring(self) -> bool:
        """Test 4: Step Sequence Monitoring (1→2→3→4 without jumping back)"""
        try:
            print(f"\n📈 Monitoring step sequence progression for 60 seconds...")
            
            # Clear previous step progression data
            self.step_progression = []
            initial_events = len(self.websocket_events)
            
            # Monitor for 60 seconds to catch step progression
            monitoring_duration = 60
            start_time = time.time()
            last_step = 0
            step_sequence_valid = True
            step_jumps_detected = []
            
            while (time.time() - start_time) < monitoring_duration:
                time.sleep(1)
                
                # Analyze step progression from WebSocket events
                for event in self.websocket_events[initial_events:]:
                    if event['event'] in ['task_progress', 'step_completed']:
                        data = event['data']
                        if isinstance(data, dict):
                            current_step = data.get('current_step') or data.get('step', 0)
                            
                            if isinstance(current_step, int) and current_step > 0:
                                # Check for step sequence violations
                                if current_step < last_step:
                                    step_jumps_detected.append({
                                        'from_step': last_step,
                                        'to_step': current_step,
                                        'timestamp': event['timestamp'],
                                        'event_type': event['event']
                                    })
                                    step_sequence_valid = False
                                    print(f"   ⚠️ STEP JUMP DETECTED: Step {last_step} → Step {current_step} at {event['timestamp']}")
                                
                                last_step = max(last_step, current_step)
                                print(f"   📊 Step progression: {current_step} (highest: {last_step})")
                
                # Check if we've reached step 4 or task completion
                if last_step >= 4:
                    print(f"   ✅ Reached final step: {last_step}")
                    break
                
                # Check for task completion events
                completion_events = [e for e in self.websocket_events[initial_events:] 
                                   if e['event'] == 'task_completed']
                if completion_events:
                    print(f"   🎉 Task completion detected")
                    break
            
            # Analyze results
            total_events = len(self.websocket_events) - initial_events
            progress_events = [e for e in self.websocket_events[initial_events:] 
                             if e['event'] in ['task_progress', 'step_completed']]
            
            if step_sequence_valid and len(progress_events) > 0 and last_step > 1:
                self.log_test("Step Sequence Monitoring", True, 
                            f"Step sequence valid - No jumps detected, reached step {last_step}, {len(progress_events)} progress events")
                return True
            elif not step_sequence_valid:
                self.log_test("Step Sequence Monitoring", False, 
                            f"Step sequence INVALID - {len(step_jumps_detected)} jumps detected: {step_jumps_detected}")
                return False
            elif len(progress_events) == 0:
                self.log_test("Step Sequence Monitoring", False, 
                            f"No step progression events received - {total_events} total events")
                return False
            else:
                self.log_test("Step Sequence Monitoring", False, 
                            f"Insufficient step progression - Only reached step {last_step}")
                return False
                
        except Exception as e:
            self.log_test("Step Sequence Monitoring", False, f"Exception: {str(e)}")
            return False
    
    def test_step_completion_logic(self) -> bool:
        """Test 5: Step Completion Logic (steps only marked complete when actually finished)"""
        try:
            print(f"\n✅ Analyzing step completion logic...")
            
            # Analyze step completion events
            completion_events = [e for e in self.websocket_events 
                               if e['event'] == 'step_completed']
            progress_events = [e for e in self.websocket_events 
                             if e['event'] == 'task_progress']
            
            if not completion_events:
                self.log_test("Step Completion Logic", False, 
                            "No step completion events received")
                return False
            
            # Check if completion events have proper data
            valid_completions = []
            premature_completions = []
            
            for event in completion_events:
                data = event['data']
                if isinstance(data, dict):
                    step = data.get('step', 0)
                    result = data.get('result', '')
                    status = data.get('status', '')
                    
                    # Check if completion has actual results
                    has_result = bool(result and len(str(result)) > 10)
                    has_proper_status = status in ['completed', 'success', 'done']
                    
                    completion_info = {
                        'step': step,
                        'has_result': has_result,
                        'has_proper_status': has_proper_status,
                        'result_length': len(str(result)),
                        'timestamp': event['timestamp']
                    }
                    
                    if has_result and (has_proper_status or result != 'No result'):
                        valid_completions.append(completion_info)
                        print(f"   ✅ Valid completion - Step {step}: {str(result)[:50]}...")
                    else:
                        premature_completions.append(completion_info)
                        print(f"   ⚠️ Premature completion - Step {step}: {result}")
            
            # Analyze completion quality
            total_completions = len(completion_events)
            valid_completion_rate = len(valid_completions) / total_completions if total_completions > 0 else 0
            
            if valid_completion_rate >= 0.8 and len(valid_completions) > 0:
                self.log_test("Step Completion Logic", True, 
                            f"Step completion logic working - {len(valid_completions)}/{total_completions} valid completions ({valid_completion_rate:.1%})")
                return True
            elif len(premature_completions) > 0:
                self.log_test("Step Completion Logic", False, 
                            f"Premature completions detected - {len(premature_completions)} premature, {len(valid_completions)} valid")
                return False
            else:
                self.log_test("Step Completion Logic", False, 
                            f"Insufficient completion data - {total_completions} completions, {valid_completion_rate:.1%} valid")
                return False
                
        except Exception as e:
            self.log_test("Step Completion Logic", False, f"Exception: {str(e)}")
            return False
    
    def test_frontend_sync_verification(self) -> bool:
        """Test 6: Frontend Sync Verification (ensure frontend receives accurate real-time updates)"""
        try:
            print(f"\n🔄 Verifying frontend sync with real-time updates...")
            
            # Check if we have sufficient WebSocket events for frontend sync
            total_events = len(self.websocket_events)
            
            if total_events < 3:
                self.log_test("Frontend Sync Verification", False, 
                            f"Insufficient WebSocket events for frontend sync - Only {total_events} events")
                return False
            
            # Analyze event types and timing
            event_types = defaultdict(int)
            event_timeline = []
            
            for event in self.websocket_events:
                event_types[event['event']] += 1
                event_timeline.append({
                    'event': event['event'],
                    'timestamp': event['timestamp'],
                    'has_data': bool(event['data'])
                })
            
            # Check for essential frontend sync events
            has_progress_events = event_types.get('task_progress', 0) > 0
            has_completion_events = event_types.get('step_completed', 0) > 0
            has_terminal_output = event_types.get('terminal_output', 0) > 0
            
            # Check event timing (should be spread over time, not all at once)
            if len(event_timeline) >= 2:
                first_event_time = datetime.fromisoformat(event_timeline[0]['timestamp'])
                last_event_time = datetime.fromisoformat(event_timeline[-1]['timestamp'])
                time_span = (last_event_time - first_event_time).total_seconds()
                
                events_spread_over_time = time_span > 5  # Events should span more than 5 seconds
            else:
                events_spread_over_time = False
            
            # Verify data quality in events
            events_with_data = sum(1 for event in self.websocket_events if event['data'])
            data_quality_rate = events_with_data / total_events if total_events > 0 else 0
            
            # Overall frontend sync assessment
            sync_score = 0
            if has_progress_events: sync_score += 1
            if has_completion_events: sync_score += 1
            if has_terminal_output: sync_score += 1
            if events_spread_over_time: sync_score += 1
            if data_quality_rate >= 0.7: sync_score += 1
            
            if sync_score >= 4:
                self.log_test("Frontend Sync Verification", True, 
                            f"Frontend sync working - {total_events} events, {sync_score}/5 sync criteria met")
                print(f"   📊 Event types: {dict(event_types)}")
                print(f"   ⏱️ Time span: {time_span:.1f}s, Data quality: {data_quality_rate:.1%}")
                return True
            else:
                self.log_test("Frontend Sync Verification", False, 
                            f"Frontend sync issues - {sync_score}/5 sync criteria met, {total_events} events")
                print(f"   📊 Event types: {dict(event_types)}")
                print(f"   ⚠️ Missing: Progress={has_progress_events}, Completion={has_completion_events}, Terminal={has_terminal_output}")
                return False
                
        except Exception as e:
            self.log_test("Frontend Sync Verification", False, f"Exception: {str(e)}")
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
        """Run all WebSocket step progression tests"""
        print("🧪 STARTING MITOSIS BACKEND WEBSOCKET STEP PROGRESSION TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing real-time WebSocket step progression issues")
        print("📋 TESTING: Complex task creation, WebSocket monitoring, step sequence, completion logic")
        print("🔍 TEST TASK: 'Crear análisis detallado sobre blockchain en 2025'")
        print("⚠️ INVESTIGATING: Step jumps (3→2), premature completion, frontend sync issues")
        print("=" * 80)
        
        # Test sequence focused on WebSocket step progression
        tests = [
            ("Create Complex Task", self.test_create_complex_task),
            ("WebSocket Connection", self.test_websocket_connection_and_monitoring),
            ("Task Execution Trigger", self.test_task_execution_trigger),
            ("Step Sequence Monitoring", self.test_step_sequence_monitoring),
            ("Step Completion Logic", self.test_step_completion_logic),
            ("Frontend Sync Verification", self.test_frontend_sync_verification)
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
        print("🎯 MITOSIS BACKEND WEBSOCKET STEP PROGRESSION TEST RESULTS")
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
            event_types = defaultdict(int)
            for event in self.websocket_events:
                event_types[event['event']] += 1
            
            for event_type, count in event_types.items():
                print(f"   - {event_type}: {count} events")
        
        # Step Progression Summary
        print(f"\n📈 STEP PROGRESSION SUMMARY:")
        print(f"   Step Progression Events: {len(self.step_progression)}")
        
        if self.step_progression:
            max_step = max(step.get('step', 0) for step in self.step_progression if isinstance(step.get('step'), int))
            print(f"   Maximum Step Reached: {max_step}")
            
            # Check for step jumps
            step_jumps = []
            last_step = 0
            for step_info in self.step_progression:
                current_step = step_info.get('step', 0)
                if isinstance(current_step, int) and current_step < last_step:
                    step_jumps.append(f"{last_step}→{current_step}")
                last_step = max(last_step, current_step) if isinstance(current_step, int) else last_step
            
            if step_jumps:
                print(f"   ⚠️ Step Jumps Detected: {', '.join(step_jumps)}")
            else:
                print(f"   ✅ No Step Jumps Detected")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ WEBSOCKET STEP PROGRESSION WORKING PERFECTLY"
        elif success_rate >= 70:
            overall_status = "⚠️ WEBSOCKET MOSTLY WORKING - Minor step progression issues"
        elif success_rate >= 50:
            overall_status = "⚠️ WEBSOCKET PARTIAL - Significant step progression issues"
        else:
            overall_status = "❌ WEBSOCKET CRITICAL - Major step progression failures"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for step progression
        critical_tests = ["Create Complex Task", "WebSocket Connection", "Step Sequence Monitoring", "Step Completion Logic"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL STEP PROGRESSION FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical step progression functionality is working")
            print("   🎯 CONCLUSION: WebSocket step progression issues are RESOLVED")
        else:
            print("   ❌ Some critical step progression functionality is not working")
            print("   🎯 CONCLUSION: WebSocket step progression issues PERSIST")
        
        # Specific findings for user's reported issues
        print(f"\n🔍 SPECIFIC ISSUE ANALYSIS:")
        
        # Issue 1: Agent jumps from step 3 back to step 2
        step_sequence_result = next((r for r in self.test_results if r['test_name'] == 'Step Sequence Monitoring'), None)
        if step_sequence_result and step_sequence_result['success']:
            print("   ✅ STEP JUMPING: No step jumps detected (3→2 issue resolved)")
        elif step_sequence_result:
            print("   ❌ STEP JUMPING: Step sequence violations detected (3→2 issue persists)")
        else:
            print("   ⚠️ STEP JUMPING: Could not verify step sequence")
        
        # Issue 2: Steps being marked as "HECHO" (done) prematurely
        completion_result = next((r for r in self.test_results if r['test_name'] == 'Step Completion Logic'), None)
        if completion_result and completion_result['success']:
            print("   ✅ PREMATURE COMPLETION: Steps completed properly with valid results")
        elif completion_result:
            print("   ❌ PREMATURE COMPLETION: Steps marked done prematurely (HECHO issue persists)")
        else:
            print("   ⚠️ PREMATURE COMPLETION: Could not verify completion logic")
        
        # Issue 3: Frontend sync issues
        sync_result = next((r for r in self.test_results if r['test_name'] == 'Frontend Sync Verification'), None)
        if sync_result and sync_result['success']:
            print("   ✅ FRONTEND SYNC: Real-time updates working correctly")
        elif sync_result:
            print("   ❌ FRONTEND SYNC: Frontend not receiving accurate real-time updates")
        else:
            print("   ⚠️ FRONTEND SYNC: Could not verify frontend synchronization")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id,
            'websocket_events': self.websocket_events,
            'step_progression': self.step_progression,
            'websocket_working': critical_passed >= 3,
            'step_progression_working': step_sequence_result and step_sequence_result['success'] if step_sequence_result else False,
            'completion_logic_working': completion_result and completion_result['success'] if completion_result else False,
            'frontend_sync_working': sync_result and sync_result['success'] if sync_result else False
        }

def main():
    """Main testing function"""
    tester = MitosisWebSocketStepProgressionTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/backend_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR MAIN AGENT")
    print("=" * 80)
    
    if results['websocket_working']:
        print("✅ WEBSOCKET DIAGNOSIS: WebSocket step progression is working correctly")
        print("📋 RECOMMENDATION: Real-time step progression issues are resolved")
        print("🔧 NEXT STEPS: Frontend should receive accurate real-time updates")
    else:
        print("❌ WEBSOCKET DIAGNOSIS: WebSocket step progression has critical issues")
        print("📋 RECOMMENDATION: Fix WebSocket step progression issues first")
        print("🔧 NEXT STEPS: Address WebSocket event emission and step sequence problems")
    
    if results.get('step_progression_working'):
        print("✅ STEP SEQUENCE STATUS: Step progression working correctly (no jumps detected)")
    else:
        print("❌ STEP SEQUENCE STATUS: Step sequence issues detected (jumps or insufficient progression)")
    
    if results.get('completion_logic_working'):
        print("✅ COMPLETION LOGIC STATUS: Steps completed properly with valid results")
    else:
        print("❌ COMPLETION LOGIC STATUS: Premature completion issues detected")
    
    if results.get('frontend_sync_working'):
        print("✅ FRONTEND SYNC STATUS: Real-time updates working correctly")
    else:
        print("❌ FRONTEND SYNC STATUS: Frontend sync issues detected")
    
    # Specific user issue analysis
    print(f"\n🔍 USER REPORTED ISSUES ANALYSIS:")
    
    if results.get('step_progression_working'):
        print("   ✅ ISSUE 1 RESOLVED: Agent no longer jumps from step 3 back to step 2")
    else:
        print("   ❌ ISSUE 1 PERSISTS: Agent still has step jumping issues (3→2)")
    
    if results.get('completion_logic_working'):
        print("   ✅ ISSUE 2 RESOLVED: Steps no longer marked as 'HECHO' prematurely")
    else:
        print("   ❌ ISSUE 2 PERSISTS: Steps still being marked as done prematurely")
    
    if results.get('frontend_sync_working'):
        print("   ✅ ISSUE 3 RESOLVED: Frontend showing real agent action vs cached data correctly")
    else:
        print("   ❌ ISSUE 3 PERSISTS: Frontend may still be showing cached data instead of real action")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 WEBSOCKET STEP PROGRESSION TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ WEBSOCKET STEP PROGRESSION TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)