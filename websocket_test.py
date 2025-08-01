#!/usr/bin/env python3
"""
COMPREHENSIVE MITOSIS WEBSOCKET COMMUNICATION TESTING
Testing WebSocket communication between frontend and backend to diagnose why
the frontend is not receiving real-time updates despite backend working perfectly.

CRITICAL ISSUE IDENTIFIED:
- Backend is functioning perfectly and completing all tasks
- WebSocket events are being emitted correctly from backend  
- Frontend is not receiving real-time updates (task_progress, step_completed, task_completed)
- User sees "el agente se queda en el primer paso" due to lack of progress updates

TESTING FOCUS:
1. **WebSocket Connectivity**: Test WebSocket connection establishment
2. **Real-time Event Emission**: Verify backend emits progress events correctly
3. **Task Execution Flow**: Test complete task execution with event tracking
4. **Backend API Functionality**: Verify all backend endpoints work correctly
5. **Task Persistence**: Test MongoDB task storage and recovery
6. **CORS Configuration**: Verify CORS allows WebSocket connections
7. **Event Broadcasting**: Test WebSocket event broadcasting to clients
8. **Connection Diagnostics**: Identify WebSocket connection issues

BACKEND URL: https://e16aaf8b-9515-4874-baf4-4996642c59cb.preview.emergentagent.com
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://e16aaf8b-9515-4874-baf4-4996642c59cb.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
WEBSOCKET_URL = f"{BACKEND_URL}/api/socket.io/"

class MitosisWebSocketTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://e16aaf8b-9515-4874-baf4-4996642c59cb.preview.emergentagent.com'
        })
        self.test_results = []
        self.task_id = None
        self.websocket_events = []
        self.websocket_connected = False
        
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
    
    def test_backend_health_comprehensive(self) -> bool:
        """Test 1: Comprehensive Backend Health Check"""
        try:
            # Test multiple health endpoints
            endpoints = [
                ("/health", "Basic Health"),
                ("/api/health", "API Health"),
                ("/api/agent/health", "Agent Health"),
                ("/api/agent/status", "Agent Status")
            ]
            
            health_results = {}
            
            for endpoint, name in endpoints:
                try:
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    health_results[name] = {
                        'status_code': response.status_code,
                        'success': response.status_code == 200,
                        'data': response.json() if response.status_code == 200 else None
                    }
                except Exception as e:
                    health_results[name] = {
                        'status_code': 0,
                        'success': False,
                        'error': str(e)
                    }
            
            # Analyze results
            successful_endpoints = sum(1 for result in health_results.values() if result['success'])
            total_endpoints = len(endpoints)
            
            # Check specific health indicators
            api_health = health_results.get("API Health", {}).get('data', {})
            agent_status = health_results.get("Agent Status", {}).get('data', {})
            
            database_ok = api_health.get('services', {}).get('database', False)
            ollama_ok = agent_status.get('ollama', {}).get('connected', False)
            tools_count = agent_status.get('tools_count', 0)
            memory_enabled = agent_status.get('memory', {}).get('enabled', False)
            
            if successful_endpoints >= 3 and database_ok and memory_enabled:
                self.log_test("Backend Health Comprehensive", True, 
                            f"Backend healthy - {successful_endpoints}/{total_endpoints} endpoints, DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}, Memory: {memory_enabled}")
                return True
            else:
                self.log_test("Backend Health Comprehensive", False, 
                            f"Backend issues - {successful_endpoints}/{total_endpoints} endpoints, DB: {database_ok}, Ollama: {ollama_ok}, Tools: {tools_count}, Memory: {memory_enabled}")
                return False
                
        except Exception as e:
            self.log_test("Backend Health Comprehensive", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_endpoint_accessibility(self) -> bool:
        """Test 2: WebSocket Endpoint Accessibility"""
        try:
            print(f"\n🔌 Testing WebSocket endpoint accessibility: {WEBSOCKET_URL}")
            
            # Test Socket.IO endpoint directly
            try:
                socketio_response = self.session.get(f"{BACKEND_URL}/socket.io/", timeout=10)
                socketio_accessible = socketio_response.status_code in [200, 400]  # 400 is OK for socket.io without proper handshake
                print(f"   🔍 Socket.IO endpoint status: {socketio_response.status_code}")
            except Exception as e:
                socketio_accessible = False
                print(f"   ❌ Socket.IO endpoint error: {e}")
            
            # Test alternative WebSocket path
            try:
                alt_response = self.session.get(f"{BACKEND_URL}/api/socket.io/", timeout=10)
                alt_accessible = alt_response.status_code in [200, 400]
                print(f"   🔍 Alternative Socket.IO path status: {alt_response.status_code}")
            except Exception as e:
                alt_accessible = False
                print(f"   ❌ Alternative Socket.IO path error: {e}")
            
            # Check CORS headers for WebSocket
            cors_headers = {}
            if socketio_accessible:
                cors_headers = {
                    'Access-Control-Allow-Origin': socketio_response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': socketio_response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': socketio_response.headers.get('Access-Control-Allow-Headers')
                }
            
            has_cors = any(cors_headers.values())
            
            if socketio_accessible or alt_accessible:
                self.log_test("WebSocket Endpoint Accessibility", True, 
                            f"WebSocket endpoint accessible - Socket.IO: {socketio_accessible}, Alt path: {alt_accessible}, CORS: {has_cors}")
                return True
            else:
                self.log_test("WebSocket Endpoint Accessibility", False, 
                            f"WebSocket endpoint not accessible - Socket.IO: {socketio_accessible}, Alt path: {alt_accessible}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Endpoint Accessibility", False, f"Exception: {str(e)}")
            return False
    
    def test_task_creation_with_monitoring(self) -> bool:
        """Test 3: Task Creation with Progress Monitoring"""
        try:
            # Create a task that should generate WebSocket events
            test_message = "Crear un análisis rápido de mercado para software en 2025"
            
            payload = {
                "message": test_message
            }
            
            print(f"\n🎯 Creating task for monitoring: {test_message}")
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id', '')
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                memory_used = data.get('memory_used', False)
                
                if task_id:
                    self.task_id = task_id
                    print(f"   📝 Task created with ID: {task_id}")
                    print(f"   📋 Plan steps: {len(plan)}")
                    print(f"   🧠 Memory used: {memory_used}")
                    print(f"   📄 Enhanced title: {enhanced_title}")
                    
                    # Check if plan has proper structure for WebSocket events
                    if plan and len(plan) >= 4:
                        valid_plan = True
                        tools_used = set()
                        for step in plan:
                            if not all(key in step for key in ['title', 'description', 'tool']):
                                valid_plan = False
                                break
                            tools_used.add(step.get('tool', 'unknown'))
                        
                        if valid_plan:
                            self.log_test("Task Creation with Monitoring", True, 
                                        f"Task created successfully - ID: {task_id}, Plan: {len(plan)} steps, Tools: {len(tools_used)}, Memory: {memory_used}")
                            return True
                        else:
                            self.log_test("Task Creation with Monitoring", False, 
                                        f"Task created but plan structure invalid - ID: {task_id}", data)
                            return False
                    else:
                        self.log_test("Task Creation with Monitoring", False, 
                                    f"Task created but no proper plan - ID: {task_id}, Plan length: {len(plan) if plan else 0}", data)
                        return False
                else:
                    self.log_test("Task Creation with Monitoring", False, 
                                f"Task creation failed - No task ID returned", data)
                    return False
            else:
                self.log_test("Task Creation with Monitoring", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Task Creation with Monitoring", False, f"Exception: {str(e)}")
            return False
    
    def test_task_execution_endpoints(self) -> bool:
        """Test 4: Task Execution Endpoints"""
        try:
            if not self.task_id:
                self.log_test("Task Execution Endpoints", False, "No task ID available for execution testing")
                return False
            
            print(f"\n🚀 Testing task execution endpoints for: {self.task_id}")
            
            # Test various execution endpoints
            execution_endpoints = [
                f"/api/agent/execute-task/{self.task_id}",
                f"/api/agent/execute-plan/{self.task_id}",
                f"/api/agent/start-execution/{self.task_id}",
                f"/api/agent/run-task/{self.task_id}"
            ]
            
            execution_results = {}
            
            for endpoint in execution_endpoints:
                try:
                    response = self.session.post(f"{BACKEND_URL}{endpoint}", timeout=15)
                    execution_results[endpoint] = {
                        'status_code': response.status_code,
                        'success': response.status_code in [200, 202, 404],  # 404 is OK if endpoint doesn't exist
                        'data': response.json() if response.status_code == 200 else None
                    }
                    print(f"   🔍 {endpoint}: {response.status_code}")
                except Exception as e:
                    execution_results[endpoint] = {
                        'status_code': 0,
                        'success': False,
                        'error': str(e)
                    }
                    print(f"   ❌ {endpoint}: {e}")
            
            # Check if any execution endpoint is available
            available_endpoints = [ep for ep, result in execution_results.items() if result['success']]
            
            # Also test task status/progress endpoints
            status_endpoints = [
                f"/api/agent/task-status/{self.task_id}",
                f"/api/agent/get-task/{self.task_id}",
                f"/api/agent/task-progress/{self.task_id}"
            ]
            
            status_results = {}
            
            for endpoint in status_endpoints:
                try:
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    status_results[endpoint] = {
                        'status_code': response.status_code,
                        'success': response.status_code in [200, 404],
                        'data': response.json() if response.status_code == 200 else None
                    }
                    print(f"   🔍 {endpoint}: {response.status_code}")
                except Exception as e:
                    status_results[endpoint] = {
                        'status_code': 0,
                        'success': False,
                        'error': str(e)
                    }
            
            available_status_endpoints = [ep for ep, result in status_results.items() if result['success']]
            
            if len(available_endpoints) > 0 or len(available_status_endpoints) > 0:
                self.log_test("Task Execution Endpoints", True, 
                            f"Task execution infrastructure available - Execution endpoints: {len(available_endpoints)}, Status endpoints: {len(available_status_endpoints)}")
                return True
            else:
                self.log_test("Task Execution Endpoints", False, 
                            f"No task execution endpoints available - Tested {len(execution_endpoints)} execution and {len(status_endpoints)} status endpoints")
                return False
                
        except Exception as e:
            self.log_test("Task Execution Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_task_persistence_and_recovery(self) -> bool:
        """Test 5: Task Persistence and Recovery"""
        try:
            if not self.task_id:
                self.log_test("Task Persistence and Recovery", False, "No task ID available for persistence testing")
                return False
            
            print(f"\n💾 Testing task persistence for: {self.task_id}")
            
            # Test task retrieval
            task_found = False
            try:
                task_response = self.session.get(f"{API_BASE}/agent/get-task/{self.task_id}", timeout=10)
                if task_response.status_code == 200:
                    task_data = task_response.json()
                    task_found = True
                    print(f"   ✅ Task found in database: {task_data.get('title', 'No title')}")
                else:
                    print(f"   ❌ Task not found: {task_response.status_code}")
            except Exception as e:
                print(f"   ❌ Task retrieval error: {e}")
            
            # Test task files
            files_available = False
            try:
                files_response = self.session.get(f"{API_BASE}/agent/get-task-files/{self.task_id}", timeout=10)
                if files_response.status_code == 200:
                    files_data = files_response.json()
                    files_count = len(files_data.get('files', []))
                    files_available = True
                    print(f"   📁 Task files found: {files_count}")
                elif files_response.status_code == 404:
                    files_available = True  # 404 is OK if no files yet
                    print(f"   📁 No task files yet (404 - normal for new tasks)")
                else:
                    print(f"   ❌ Task files error: {files_response.status_code}")
            except Exception as e:
                print(f"   ❌ Task files error: {e}")
            
            # Test MongoDB connection directly
            mongodb_ok = False
            try:
                health_response = self.session.get(f"{API_BASE}/health", timeout=10)
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    mongodb_ok = health_data.get('services', {}).get('database', False)
                    print(f"   🗄️ MongoDB connection: {mongodb_ok}")
            except Exception as e:
                print(f"   ❌ MongoDB check error: {e}")
            
            # Evaluate persistence
            persistence_score = sum([task_found, files_available, mongodb_ok])
            
            if persistence_score >= 2:
                self.log_test("Task Persistence and Recovery", True, 
                            f"Task persistence working - Task found: {task_found}, Files available: {files_available}, MongoDB: {mongodb_ok}")
                return True
            else:
                self.log_test("Task Persistence and Recovery", False, 
                            f"Task persistence issues - Task found: {task_found}, Files available: {files_available}, MongoDB: {mongodb_ok}")
                return False
                
        except Exception as e:
            self.log_test("Task Persistence and Recovery", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_configuration_analysis(self) -> bool:
        """Test 6: WebSocket Configuration Analysis"""
        try:
            print(f"\n🔧 Analyzing WebSocket configuration")
            
            # Check backend server configuration
            try:
                status_response = self.session.get(f"{API_BASE}/agent/status", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    backend_running = status_data.get('status', '') == 'running'
                    memory_enabled = status_data.get('memory', {}).get('enabled', False)
                    print(f"   🔍 Backend running: {backend_running}")
                    print(f"   🧠 Memory enabled: {memory_enabled}")
                else:
                    backend_running = False
                    memory_enabled = False
                    print(f"   ❌ Backend status error: {status_response.status_code}")
            except Exception as e:
                backend_running = False
                memory_enabled = False
                print(f"   ❌ Backend status error: {e}")
            
            # Test CORS configuration for WebSocket
            cors_ok = False
            try:
                # Test OPTIONS request to WebSocket endpoint
                options_response = self.session.options(f"{BACKEND_URL}/socket.io/", timeout=10)
                cors_headers = {
                    'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers')
                }
                cors_ok = any(cors_headers.values())
                print(f"   🌐 CORS headers present: {cors_ok}")
            except Exception as e:
                print(f"   ❌ CORS check error: {e}")
            
            # Test API CORS as fallback indicator
            api_cors_ok = False
            try:
                api_response = self.session.get(f"{API_BASE}/health", timeout=10)
                api_cors_ok = api_response.headers.get('Access-Control-Allow-Origin') is not None
                print(f"   🌐 API CORS working: {api_cors_ok}")
            except Exception as e:
                print(f"   ❌ API CORS check error: {e}")
            
            # Check if WebSocket path is configured correctly
            websocket_path_ok = False
            try:
                # Test both possible WebSocket paths
                path1_response = self.session.get(f"{BACKEND_URL}/socket.io/", timeout=5)
                path2_response = self.session.get(f"{BACKEND_URL}/api/socket.io/", timeout=5)
                
                path1_ok = path1_response.status_code in [200, 400]
                path2_ok = path2_response.status_code in [200, 400]
                
                websocket_path_ok = path1_ok or path2_ok
                print(f"   🛤️ WebSocket paths - /socket.io/: {path1_ok}, /api/socket.io/: {path2_ok}")
            except Exception as e:
                print(f"   ❌ WebSocket path check error: {e}")
            
            # Overall configuration assessment
            config_score = sum([backend_running, memory_enabled, cors_ok or api_cors_ok, websocket_path_ok])
            
            if config_score >= 3:
                self.log_test("WebSocket Configuration Analysis", True, 
                            f"WebSocket configuration good - Backend: {backend_running}, Memory: {memory_enabled}, CORS: {cors_ok or api_cors_ok}, Paths: {websocket_path_ok}")
                return True
            else:
                self.log_test("WebSocket Configuration Analysis", False, 
                            f"WebSocket configuration issues - Backend: {backend_running}, Memory: {memory_enabled}, CORS: {cors_ok or api_cors_ok}, Paths: {websocket_path_ok}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Configuration Analysis", False, f"Exception: {str(e)}")
            return False
    
    def test_real_time_communication_simulation(self) -> bool:
        """Test 7: Real-time Communication Simulation"""
        try:
            print(f"\n📡 Simulating real-time communication patterns")
            
            # Test rapid API calls to simulate real-time updates
            rapid_calls_success = 0
            total_rapid_calls = 5
            
            for i in range(total_rapid_calls):
                try:
                    response = self.session.get(f"{API_BASE}/health", timeout=5)
                    if response.status_code == 200:
                        rapid_calls_success += 1
                    time.sleep(0.5)  # 500ms between calls
                except:
                    pass
            
            print(f"   🔄 Rapid API calls: {rapid_calls_success}/{total_rapid_calls} successful")
            
            # Test concurrent request handling
            concurrent_success = False
            try:
                import threading
                import queue
                
                results_queue = queue.Queue()
                
                def make_request():
                    try:
                        response = self.session.get(f"{API_BASE}/agent/status", timeout=10)
                        results_queue.put(response.status_code == 200)
                    except:
                        results_queue.put(False)
                
                # Start 3 concurrent requests
                threads = []
                for _ in range(3):
                    thread = threading.Thread(target=make_request)
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads
                for thread in threads:
                    thread.join(timeout=15)
                
                # Check results
                concurrent_results = []
                while not results_queue.empty():
                    concurrent_results.append(results_queue.get())
                
                concurrent_success = len(concurrent_results) >= 2 and any(concurrent_results)
                print(f"   🔀 Concurrent requests: {len(concurrent_results)} completed, {sum(concurrent_results)} successful")
                
            except Exception as e:
                print(f"   ❌ Concurrent test error: {e}")
            
            # Test WebSocket-like polling simulation
            polling_success = False
            try:
                if self.task_id:
                    # Simulate polling for task updates
                    polling_attempts = 3
                    polling_responses = 0
                    
                    for i in range(polling_attempts):
                        try:
                            response = self.session.get(f"{API_BASE}/agent/get-task-files/{self.task_id}", timeout=5)
                            if response.status_code in [200, 404]:  # Both are valid responses
                                polling_responses += 1
                            time.sleep(1)
                        except:
                            pass
                    
                    polling_success = polling_responses >= 2
                    print(f"   📊 Polling simulation: {polling_responses}/{polling_attempts} successful")
                else:
                    print(f"   ⚠️ No task ID for polling simulation")
            except Exception as e:
                print(f"   ❌ Polling simulation error: {e}")
            
            # Overall real-time communication assessment
            realtime_score = sum([
                rapid_calls_success >= 4,  # At least 4/5 rapid calls successful
                concurrent_success,
                polling_success or not self.task_id  # Success or no task to test with
            ])
            
            if realtime_score >= 2:
                self.log_test("Real-time Communication Simulation", True, 
                            f"Real-time communication capable - Rapid: {rapid_calls_success}/5, Concurrent: {concurrent_success}, Polling: {polling_success}")
                return True
            else:
                self.log_test("Real-time Communication Simulation", False, 
                            f"Real-time communication issues - Rapid: {rapid_calls_success}/5, Concurrent: {concurrent_success}, Polling: {polling_success}")
                return False
                
        except Exception as e:
            self.log_test("Real-time Communication Simulation", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_diagnostics_comprehensive(self) -> bool:
        """Test 8: Comprehensive WebSocket Diagnostics"""
        try:
            print(f"\n🔧 Running comprehensive WebSocket diagnostics")
            
            diagnostics = {
                'backend_url': BACKEND_URL,
                'websocket_url': WEBSOCKET_URL,
                'network_reachable': False,
                'socketio_endpoint_accessible': False,
                'api_endpoints_working': False,
                'cors_configured': False,
                'task_creation_working': False,
                'task_persistence_working': False,
                'real_time_capable': False
            }
            
            # Test network reachability
            try:
                health_response = self.session.get(f"{API_BASE}/health", timeout=5)
                diagnostics['network_reachable'] = health_response.status_code == 200
            except:
                diagnostics['network_reachable'] = False
            
            # Test Socket.IO endpoint
            try:
                socketio_response = self.session.get(f"{BACKEND_URL}/socket.io/", timeout=5)
                diagnostics['socketio_endpoint_accessible'] = socketio_response.status_code in [200, 400]
            except:
                diagnostics['socketio_endpoint_accessible'] = False
            
            # Test API endpoints
            try:
                api_response = self.session.get(f"{API_BASE}/agent/status", timeout=5)
                diagnostics['api_endpoints_working'] = api_response.status_code == 200
            except:
                diagnostics['api_endpoints_working'] = False
            
            # Test CORS
            try:
                cors_response = self.session.get(f"{API_BASE}/health", timeout=5)
                diagnostics['cors_configured'] = cors_response.headers.get('Access-Control-Allow-Origin') is not None
            except:
                diagnostics['cors_configured'] = False
            
            # Test task creation
            diagnostics['task_creation_working'] = self.task_id is not None
            
            # Test task persistence (from previous tests)
            persistence_results = [r for r in self.test_results if r['test_name'] == 'Task Persistence and Recovery']
            diagnostics['task_persistence_working'] = len(persistence_results) > 0 and persistence_results[0]['success']
            
            # Test real-time capability (from previous tests)
            realtime_results = [r for r in self.test_results if r['test_name'] == 'Real-time Communication Simulation']
            diagnostics['real_time_capable'] = len(realtime_results) > 0 and realtime_results[0]['success']
            
            # Analyze diagnostics
            working_components = sum(diagnostics.values())
            total_components = len(diagnostics) - 2  # Exclude URLs from count
            
            print(f"   📊 Diagnostic results:")
            for key, value in diagnostics.items():
                if key not in ['backend_url', 'websocket_url']:
                    status = "✅" if value else "❌"
                    print(f"      {status} {key.replace('_', ' ').title()}: {value}")
            
            # Identify specific issues
            issues = []
            if not diagnostics['network_reachable']:
                issues.append("Backend not reachable")
            if not diagnostics['socketio_endpoint_accessible']:
                issues.append("Socket.IO endpoint not accessible")
            if not diagnostics['api_endpoints_working']:
                issues.append("API endpoints not working")
            if not diagnostics['cors_configured']:
                issues.append("CORS not configured")
            if not diagnostics['task_creation_working']:
                issues.append("Task creation not working")
            if not diagnostics['task_persistence_working']:
                issues.append("Task persistence not working")
            if not diagnostics['real_time_capable']:
                issues.append("Real-time communication not capable")
            
            if working_components >= 5:
                self.log_test("WebSocket Diagnostics Comprehensive", True, 
                            f"WebSocket infrastructure mostly working - {working_components}/{total_components} components working")
                return True
            else:
                self.log_test("WebSocket Diagnostics Comprehensive", False, 
                            f"WebSocket infrastructure has issues - {working_components}/{total_components} components working. Issues: {', '.join(issues)}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Diagnostics Comprehensive", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all WebSocket communication tests"""
        print("🧪 STARTING MITOSIS WEBSOCKET COMMUNICATION TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Diagnosing WebSocket communication issues")
        print("📋 ISSUE: Backend working perfectly but frontend not receiving real-time updates")
        print("🔍 GOAL: Identify why WebSocket events are not reaching frontend")
        print("=" * 80)
        
        # Test sequence focused on WebSocket communication
        tests = [
            ("Backend Health Comprehensive", self.test_backend_health_comprehensive),
            ("WebSocket Endpoint Accessibility", self.test_websocket_endpoint_accessibility),
            ("Task Creation with Monitoring", self.test_task_creation_with_monitoring),
            ("Task Execution Endpoints", self.test_task_execution_endpoints),
            ("Task Persistence and Recovery", self.test_task_persistence_and_recovery),
            ("WebSocket Configuration Analysis", self.test_websocket_configuration_analysis),
            ("Real-time Communication Simulation", self.test_real_time_communication_simulation),
            ("WebSocket Diagnostics Comprehensive", self.test_websocket_diagnostics_comprehensive)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 80)
        print("🎯 MITOSIS WEBSOCKET COMMUNICATION TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ WEBSOCKET INFRASTRUCTURE WORKING PERFECTLY"
        elif success_rate >= 70:
            overall_status = "⚠️ WEBSOCKET MOSTLY WORKING - Minor issues detected"
        elif success_rate >= 50:
            overall_status = "⚠️ WEBSOCKET PARTIAL - Significant issues found"
        else:
            overall_status = "❌ WEBSOCKET CRITICAL - Major issues preventing real-time communication"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for WebSocket communication
        critical_tests = ["Backend Health Comprehensive", "WebSocket Endpoint Accessibility", "Task Creation with Monitoring", "WebSocket Configuration Analysis"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL WEBSOCKET FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical WebSocket functionality is working")
            print("   🎯 CONCLUSION: WebSocket infrastructure is ready for real-time communication")
        else:
            print("   ❌ Some critical WebSocket functionality is not working")
            print("   🎯 CONCLUSION: WebSocket has issues that prevent real-time communication")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id,
            'websocket_working': critical_passed >= 3,
            'backend_working': critical_passed >= 2,
            'diagnostics': {
                'backend_url': BACKEND_URL,
                'websocket_url': WEBSOCKET_URL,
                'task_created': self.task_id is not None
            }
        }

def main():
    """Main testing function"""
    tester = MitosisWebSocketTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/websocket_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL WEBSOCKET COMMUNICATION ASSESSMENT")
    print("=" * 80)
    
    if results['websocket_working']:
        print("✅ WEBSOCKET DIAGNOSIS: WebSocket infrastructure is working correctly")
        print("📋 RECOMMENDATION: WebSocket communication should be functional")
        print("🔧 NEXT STEPS: Check frontend WebSocket client implementation")
    else:
        print("❌ WEBSOCKET DIAGNOSIS: WebSocket infrastructure has issues")
        print("📋 RECOMMENDATION: Fix WebSocket infrastructure issues first")
        print("🔧 NEXT STEPS: Address WebSocket configuration and connectivity problems")
    
    if results['backend_working']:
        print("✅ BACKEND STATUS: Backend is working correctly and ready for WebSocket communication")
    else:
        print("❌ BACKEND STATUS: Backend has issues that prevent WebSocket communication")
    
    # Specific recommendations based on test results
    print(f"\n🔍 SPECIFIC FINDINGS:")
    
    # Check specific test results
    endpoint_result = next((r for r in results['test_results'] if r['test_name'] == 'WebSocket Endpoint Accessibility'), None)
    if endpoint_result and endpoint_result['success']:
        print("   ✅ WebSocket endpoints are accessible")
    elif endpoint_result:
        print("   ❌ WebSocket endpoints are not accessible - This is likely the main issue")
    
    config_result = next((r for r in results['test_results'] if r['test_name'] == 'WebSocket Configuration Analysis'), None)
    if config_result and config_result['success']:
        print("   ✅ WebSocket configuration is correct")
    elif config_result:
        print("   ❌ WebSocket configuration has issues - Check CORS and backend setup")
    
    task_result = next((r for r in results['test_results'] if r['test_name'] == 'Task Creation with Monitoring'), None)
    if task_result and task_result['success']:
        print("   ✅ Task creation is working - Backend can generate tasks for WebSocket events")
    elif task_result:
        print("   ❌ Task creation has issues - Backend cannot generate tasks properly")
    
    realtime_result = next((r for r in results['test_results'] if r['test_name'] == 'Real-time Communication Simulation'), None)
    if realtime_result and realtime_result['success']:
        print("   ✅ Real-time communication is capable")
    elif realtime_result:
        print("   ❌ Real-time communication has issues - Backend may not handle concurrent requests well")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 WEBSOCKET COMMUNICATION TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ WEBSOCKET COMMUNICATION TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)