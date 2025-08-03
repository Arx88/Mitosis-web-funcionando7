#!/usr/bin/env python3
"""
MITOSIS BACKEND AUTOMATIC EXECUTION TESTING
Test the specific issue where backend creates plans but doesn't execute them automatically.

SPECIFIC TESTING REQUEST:
Testea específicamente el endpoint /api/agent/chat con el backend de Mitosis para verificar si:

1. **Crear tarea desde frontend**: Enviar un POST a /api/agent/chat con mensaje "Crear un análisis de mercado para software en 2025" 
2. **Verificar respuesta**: Confirmar que el backend devuelve un plan con steps
3. **Verificar ejecución automática**: Buscar en logs si aparecen mensajes de:
   - "🚀 STARTING execute_task_steps_sequentially"
   - "⚡ EXECUTING STEP 1/4" (o similar)
   - "emit_step_event called" (eventos WebSocket)
4. **Monitorear logs durante 30 segundos** después del request para ver si la ejecución automática se inicia
5. **Verificar WebSocket Manager**: Confirmar que existe y está inicializado

**URL Backend**: https://c4f5be8b-db00-42e6-8dcc-7c4a057ac882.preview.emergentagent.com

**PROBLEMA ESPECÍFICO A DEBUGGEAR**: El backend debería crear el plan Y luego ejecutarlo automáticamente con emit_step_event, pero según el usuario el frontend se queda en paso 1. Necesito confirmar si la ejecución automática se está iniciando o no.
"""

import requests
import json
import time
import os
import sys
import threading
import subprocess
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://c4f5be8b-db00-42e6-8dcc-7c4a057ac882.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisAutomaticExecutionTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://c4f5be8b-db00-42e6-8dcc-7c4a057ac882.preview.emergentagent.com'
        })
        self.test_results = []
        self.task_id = None
        self.log_monitoring_active = False
        self.captured_logs = []
        
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
    
    def monitor_backend_logs(self, duration_seconds: int = 30):
        """Monitor backend logs for automatic execution indicators"""
        print(f"\n🔍 Starting log monitoring for {duration_seconds} seconds...")
        self.log_monitoring_active = True
        self.captured_logs = []
        
        def log_monitor():
            try:
                # Monitor supervisor logs for backend
                cmd = ["tail", "-f", "/var/log/supervisor/backend.*.log"]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                start_time = time.time()
                while self.log_monitoring_active and (time.time() - start_time) < duration_seconds:
                    line = process.stdout.readline()
                    if line:
                        self.captured_logs.append(line.strip())
                        # Print important log lines in real-time
                        if any(keyword in line for keyword in [
                            "🚀 STARTING execute_task_steps_sequentially",
                            "⚡ EXECUTING STEP",
                            "emit_step_event called",
                            "WebSocket event emitted",
                            "Task execution started",
                            "Step completed"
                        ]):
                            print(f"   📋 LOG: {line.strip()}")
                    time.sleep(0.1)
                
                process.terminate()
            except Exception as e:
                print(f"   ⚠️ Log monitoring error: {e}")
        
        # Start log monitoring in background thread
        log_thread = threading.Thread(target=log_monitor)
        log_thread.daemon = True
        log_thread.start()
        
        return log_thread
    
    def stop_log_monitoring(self):
        """Stop log monitoring"""
        self.log_monitoring_active = False
        time.sleep(1)  # Give thread time to stop
    
    def test_task_creation_with_specific_message(self) -> bool:
        """Test 1: Create task with specific message from review request"""
        try:
            # Exact message from review request
            test_message = "Crear un análisis de mercado para software en 2025"
            
            payload = {
                "message": test_message
            }
            
            print(f"\n🎯 Testing task creation with: {test_message}")
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required response fields
                response_text = data.get('response', '')
                task_id = data.get('task_id', '')
                memory_used = data.get('memory_used', False)
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                
                # Store task_id for later tests
                if task_id:
                    self.task_id = task_id
                    print(f"   📋 Task ID created: {task_id}")
                
                # Verify plan structure and content
                if plan and len(plan) >= 3:  # At least 3 steps
                    # Check if plan has proper structure
                    valid_plan = True
                    step_details = []
                    for i, step in enumerate(plan):
                        if not all(key in step for key in ['title', 'description']):
                            valid_plan = False
                            break
                        step_details.append(f"Step {i+1}: {step.get('title', 'No title')}")
                    
                    if valid_plan and response_text and task_id:
                        self.log_test("Task Creation with Specific Message", True, 
                                    f"Task created successfully - {len(plan)} steps, Task ID: {task_id}")
                        print(f"   📋 Plan steps: {'; '.join(step_details[:3])}...")
                        return True
                    else:
                        self.log_test("Task Creation with Specific Message", False, 
                                    f"Plan structure invalid - Valid plan: {valid_plan}, Response: {bool(response_text)}, Task ID: {bool(task_id)}", data)
                        return False
                else:
                    self.log_test("Task Creation with Specific Message", False, 
                                f"Plan not generated or insufficient steps - Plan length: {len(plan) if plan else 0}", data)
                    return False
            else:
                self.log_test("Task Creation with Specific Message", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Task Creation with Specific Message", False, f"Exception: {str(e)}")
            return False
    
    def test_automatic_execution_monitoring(self) -> bool:
        """Test 2: Monitor for automatic execution after task creation"""
        if not self.task_id:
            self.log_test("Automatic Execution Monitoring", False, "No task ID available for monitoring")
            return False
        
        try:
            print(f"\n🔍 Monitoring automatic execution for task: {self.task_id}")
            
            # Start log monitoring
            log_thread = self.monitor_backend_logs(30)
            
            # Wait for potential automatic execution
            print("   ⏳ Waiting 30 seconds for automatic execution to start...")
            time.sleep(30)
            
            # Stop log monitoring
            self.stop_log_monitoring()
            
            # Analyze captured logs for execution indicators
            execution_indicators = [
                "🚀 STARTING execute_task_steps_sequentially",
                "⚡ EXECUTING STEP 1/4",
                "⚡ EXECUTING STEP",
                "emit_step_event called",
                "WebSocket event emitted",
                "Task execution started",
                "Step completed"
            ]
            
            found_indicators = []
            for log_line in self.captured_logs:
                for indicator in execution_indicators:
                    if indicator in log_line:
                        found_indicators.append(indicator)
                        break
            
            if found_indicators:
                self.log_test("Automatic Execution Monitoring", True, 
                            f"Automatic execution detected - Found indicators: {', '.join(set(found_indicators))}")
                return True
            else:
                self.log_test("Automatic Execution Monitoring", False, 
                            f"No automatic execution detected - Monitored {len(self.captured_logs)} log lines, no execution indicators found")
                return False
                
        except Exception as e:
            self.log_test("Automatic Execution Monitoring", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_manager_initialization(self) -> bool:
        """Test 3: Verify WebSocket Manager exists and is initialized"""
        try:
            # Check backend status for WebSocket information
            response = self.session.get(f"{API_BASE}/agent/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if backend is running and has memory enabled (indicates WebSocket support)
                backend_running = data.get('status', '') == 'running'
                memory_enabled = data.get('memory', {}).get('enabled', False)
                memory_initialized = data.get('memory', {}).get('initialized', False)
                
                # Also test WebSocket endpoint accessibility
                socketio_url = f"{BACKEND_URL}/socket.io/"
                socketio_response = self.session.get(socketio_url, timeout=10)
                websocket_accessible = socketio_response.status_code in [200, 400]  # 400 is OK for socket.io
                
                if backend_running and memory_enabled and memory_initialized and websocket_accessible:
                    self.log_test("WebSocket Manager Initialization", True, 
                                f"WebSocket Manager initialized - Backend running: {backend_running}, Memory enabled: {memory_enabled}, Initialized: {memory_initialized}, Endpoint accessible: {websocket_accessible}")
                    return True
                else:
                    self.log_test("WebSocket Manager Initialization", False, 
                                f"WebSocket Manager issues - Running: {backend_running}, Memory enabled: {memory_enabled}, Initialized: {memory_initialized}, Accessible: {websocket_accessible}")
                    return False
            else:
                self.log_test("WebSocket Manager Initialization", False, 
                            f"Cannot verify WebSocket Manager - Status endpoint error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Manager Initialization", False, f"Exception: {str(e)}")
            return False
    
    def test_task_execution_endpoints(self) -> bool:
        """Test 4: Check if task execution endpoints exist"""
        if not self.task_id:
            self.log_test("Task Execution Endpoints", False, "No task ID available for testing")
            return False
        
        try:
            # Test various potential execution endpoints
            execution_endpoints = [
                f"/api/agent/start-task-execution/{self.task_id}",
                f"/api/agent/execute-task/{self.task_id}",
                f"/api/agent/run-task/{self.task_id}",
                f"/api/agent/task/{self.task_id}/execute"
            ]
            
            endpoint_results = []
            for endpoint in execution_endpoints:
                try:
                    response = self.session.post(f"{BACKEND_URL}{endpoint}", timeout=10)
                    endpoint_results.append({
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'accessible': response.status_code != 404
                    })
                except Exception as e:
                    endpoint_results.append({
                        'endpoint': endpoint,
                        'status_code': 'error',
                        'accessible': False,
                        'error': str(e)
                    })
            
            # Check if any execution endpoints are accessible
            accessible_endpoints = [r for r in endpoint_results if r['accessible']]
            
            if accessible_endpoints:
                self.log_test("Task Execution Endpoints", True, 
                            f"Task execution endpoints found - {len(accessible_endpoints)} accessible endpoints")
                for endpoint in accessible_endpoints:
                    print(f"   📋 Accessible: {endpoint['endpoint']} (Status: {endpoint['status_code']})")
                return True
            else:
                self.log_test("Task Execution Endpoints", False, 
                            f"No task execution endpoints found - All {len(execution_endpoints)} endpoints returned 404 or error")
                for endpoint in endpoint_results:
                    print(f"   ❌ Not accessible: {endpoint['endpoint']} (Status: {endpoint['status_code']})")
                return False
                
        except Exception as e:
            self.log_test("Task Execution Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_event_emission_capability(self) -> bool:
        """Test 5: Test if backend can emit WebSocket events"""
        if not self.task_id:
            self.log_test("WebSocket Event Emission Capability", False, "No task ID available for testing")
            return False
        
        try:
            # Test if there's a force emit endpoint for testing
            force_emit_url = f"{API_BASE}/agent/force-websocket-emit/{self.task_id}"
            
            payload = {
                "message": "Test WebSocket emission for automatic execution debugging"
            }
            
            response = self.session.post(force_emit_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                active_connections = data.get('active_connections', 0)
                
                if success:
                    self.log_test("WebSocket Event Emission Capability", True, 
                                f"WebSocket emission working - Success: {success}, Active connections: {active_connections}")
                    return True
                else:
                    self.log_test("WebSocket Event Emission Capability", False, 
                                f"WebSocket emission failed - Success: {success}, Active connections: {active_connections}")
                    return False
            else:
                self.log_test("WebSocket Event Emission Capability", False, 
                            f"WebSocket emission endpoint not available - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Event Emission Capability", False, f"Exception: {str(e)}")
            return False
    
    def test_task_status_after_creation(self) -> bool:
        """Test 6: Check task status after creation to see if execution started"""
        if not self.task_id:
            self.log_test("Task Status After Creation", False, "No task ID available for testing")
            return False
        
        try:
            # Wait a bit after task creation
            time.sleep(5)
            
            # Check task status
            status_url = f"{API_BASE}/agent/get-task-status/{self.task_id}"
            response = self.session.get(status_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for execution indicators in task status
                status = data.get('status', 'unknown')
                current_step = data.get('current_step', 0)
                completed_steps = data.get('completed_steps', 0)
                is_executing = data.get('is_executing', False)
                
                # Check if task has progressed beyond initial creation
                execution_started = (
                    current_step > 0 or 
                    completed_steps > 0 or 
                    is_executing or 
                    status in ['executing', 'in_progress', 'running']
                )
                
                if execution_started:
                    self.log_test("Task Status After Creation", True, 
                                f"Task execution started - Status: {status}, Current step: {current_step}, Completed: {completed_steps}, Executing: {is_executing}")
                    return True
                else:
                    self.log_test("Task Status After Creation", False, 
                                f"Task execution not started - Status: {status}, Current step: {current_step}, Completed: {completed_steps}, Executing: {is_executing}")
                    return False
            else:
                self.log_test("Task Status After Creation", False, 
                            f"Cannot get task status - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Task Status After Creation", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all automatic execution tests"""
        print("🧪 STARTING MITOSIS BACKEND AUTOMATIC EXECUTION TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing automatic execution after plan creation")
        print("📋 TESTING: Task creation, plan generation, automatic execution, WebSocket events")
        print("🔍 MESSAGE: 'Crear un análisis de mercado para software en 2025'")
        print("=" * 80)
        
        # Test sequence focused on automatic execution
        tests = [
            ("Task Creation with Specific Message", self.test_task_creation_with_specific_message),
            ("Automatic Execution Monitoring", self.test_automatic_execution_monitoring),
            ("WebSocket Manager Initialization", self.test_websocket_manager_initialization),
            ("Task Execution Endpoints", self.test_task_execution_endpoints),
            ("WebSocket Event Emission Capability", self.test_websocket_event_emission_capability),
            ("Task Status After Creation", self.test_task_status_after_creation)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 80)
        print("🎯 MITOSIS BACKEND AUTOMATIC EXECUTION TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ AUTOMATIC EXECUTION WORKING PERFECTLY"
        elif success_rate >= 70:
            overall_status = "⚠️ AUTOMATIC EXECUTION MOSTLY WORKING - Minor issues detected"
        elif success_rate >= 50:
            overall_status = "⚠️ AUTOMATIC EXECUTION PARTIAL - Significant issues found"
        else:
            overall_status = "❌ AUTOMATIC EXECUTION CRITICAL - Major issues preventing functionality"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for automatic execution
        critical_tests = ["Task Creation with Specific Message", "Automatic Execution Monitoring", "WebSocket Manager Initialization"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL AUTOMATIC EXECUTION FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical automatic execution functionality is working")
            print("   🎯 CONCLUSION: Backend automatic execution is working correctly")
        else:
            print("   ❌ Some critical automatic execution functionality is not working")
            print("   🎯 CONCLUSION: Backend has automatic execution issues that need to be fixed")
        
        # Specific findings
        print(f"\n🔍 SPECIFIC FINDINGS:")
        
        task_creation_result = next((r for r in self.test_results if r['test_name'] == 'Task Creation with Specific Message'), None)
        if task_creation_result and task_creation_result['success']:
            print("   ✅ Task creation with plan generation is working correctly")
        elif task_creation_result:
            print("   ❌ Task creation or plan generation issues detected")
        
        execution_result = next((r for r in self.test_results if r['test_name'] == 'Automatic Execution Monitoring'), None)
        if execution_result and execution_result['success']:
            print("   ✅ Automatic execution is working - execution indicators found in logs")
        elif execution_result:
            print("   ❌ Automatic execution NOT working - no execution indicators found in logs")
        
        websocket_result = next((r for r in self.test_results if r['test_name'] == 'WebSocket Manager Initialization'), None)
        if websocket_result and websocket_result['success']:
            print("   ✅ WebSocket Manager is initialized and working")
        elif websocket_result:
            print("   ❌ WebSocket Manager initialization issues detected")
        
        endpoints_result = next((r for r in self.test_results if r['test_name'] == 'Task Execution Endpoints'), None)
        if endpoints_result and endpoints_result['success']:
            print("   ✅ Task execution endpoints are available")
        elif endpoints_result:
            print("   ❌ Task execution endpoints are missing (404 errors)")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id,
            'automatic_execution_working': execution_result and execution_result['success'] if execution_result else False,
            'task_creation_working': task_creation_result and task_creation_result['success'] if task_creation_result else False,
            'websocket_working': websocket_result and websocket_result['success'] if websocket_result else False
        }

def main():
    """Main testing function"""
    tester = MitosisAutomaticExecutionTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/mitosis_execution_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR MAIN AGENT")
    print("=" * 80)
    
    if results['automatic_execution_working']:
        print("✅ AUTOMATIC EXECUTION DIAGNOSIS: Backend automatic execution is working correctly")
        print("📋 RECOMMENDATION: Backend creates plans AND executes them automatically")
        print("🔧 NEXT STEPS: Frontend should receive WebSocket events during execution")
    else:
        print("❌ AUTOMATIC EXECUTION DIAGNOSIS: Backend does NOT execute plans automatically")
        print("📋 RECOMMENDATION: Fix backend automatic execution after plan creation")
        print("🔧 NEXT STEPS: Implement automatic task execution with WebSocket event emission")
    
    if results['task_creation_working']:
        print("✅ TASK CREATION STATUS: Task creation and plan generation working correctly")
    else:
        print("❌ TASK CREATION STATUS: Task creation or plan generation issues detected")
    
    if results['websocket_working']:
        print("✅ WEBSOCKET STATUS: WebSocket Manager is initialized and working")
    else:
        print("❌ WEBSOCKET STATUS: WebSocket Manager initialization issues detected")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 AUTOMATIC EXECUTION TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ AUTOMATIC EXECUTION TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)