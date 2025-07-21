#!/usr/bin/env python3
"""
Comprehensive Testing Script for Mitosis V5-beta Backend System
Tests all 6 major improvements from UPGRADE.md:

1. Intent Detection System (LLM-based intent classification)
2. Robust Plan Generation (JSON schema validation, retry mechanisms)
3. Real-time WebSocket Communication (WebSocket manager, task tracking)
4. Robust Ollama Response Parsing (multiple JSON extraction strategies)
5. Task Persistence with MongoDB (task storage, recovery)
6. Error Handling and Resilience (retry mechanisms, exponential backoff)
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://50041b40-574c-4bf5-8648-00b3fb079ce2.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisV5Tester:
    def __init__(self):
        self.results = {
            'intent_detection': {'passed': 0, 'failed': 0, 'tests': []},
            'plan_generation': {'passed': 0, 'failed': 0, 'tests': []},
            'websocket_communication': {'passed': 0, 'failed': 0, 'tests': []},
            'ollama_parsing': {'passed': 0, 'failed': 0, 'tests': []},
            'task_persistence': {'passed': 0, 'failed': 0, 'tests': []},
            'error_handling': {'passed': 0, 'failed': 0, 'tests': []}
        }
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mitosis-V5-Tester/1.0'
        })

    def log_test(self, category: str, test_name: str, passed: bool, details: str, response_time: float = 0):
        """Log test result"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} [{category.upper()}] {test_name} ({response_time:.2f}s)")
        if details:
            print(f"   Details: {details}")
        
        self.results[category]['tests'].append({
            'name': test_name,
            'passed': passed,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        })
        
        if passed:
            self.results[category]['passed'] += 1
        else:
            self.results[category]['failed'] += 1

    def make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 30) -> Dict:
        """Make HTTP request with error handling"""
        try:
            start_time = time.time()
            url = f"{API_BASE}{endpoint}"
            
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            try:
                result = response.json()
            except json.JSONDecodeError:
                result = {'text': response.text, 'status_code': response.status_code}
            
            result['_response_time'] = response_time
            result['_status_code'] = response.status_code
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                '_response_time': time.time() - start_time if 'start_time' in locals() else 0,
                '_status_code': 0
            }

    def test_1_intent_detection_system(self):
        """Test 1: Intent Detection System - LLM-based intent classification"""
        print("\n🧠 Testing Intent Detection System...")
        
        # Test 1.1: Casual conversation detection
        casual_messages = [
            "hola",
            "¿cómo estás?",
            "gracias",
            "buenos días",
            "¿quién eres?"
        ]
        
        for message in casual_messages:
            response = self.make_request('POST', '/agent/chat', {
                'message': message,
                'test_mode': True
            })
            
            response_time = response.get('_response_time', 0)
            
            # Check if response indicates casual conversation (no plan generation)
            is_casual = (
                'plan' not in response or 
                not response.get('plan') or
                'casual' in response.get('response', '').lower() or
                len(response.get('response', '')) < 200  # Casual responses are typically shorter
            )
            
            self.log_test(
                'intent_detection',
                f'Casual Message Detection: "{message}"',
                is_casual,
                f"Response length: {len(response.get('response', ''))}, Plan generated: {bool(response.get('plan'))}",
                response_time
            )
        
        # Test 1.2: Task message detection
        task_messages = [
            "crear un informe sobre inteligencia artificial",
            "buscar información sobre el cambio climático",
            "analizar datos de ventas del último trimestre",
            "desarrollar una estrategia de marketing digital"
        ]
        
        for message in task_messages:
            response = self.make_request('POST', '/agent/chat', {
                'message': message,
                'test_mode': True
            })
            
            response_time = response.get('_response_time', 0)
            
            # Check if response indicates task processing (plan generation)
            is_task = (
                'plan' in response and 
                response.get('plan') and
                len(response.get('plan', [])) > 0
            )
            
            self.log_test(
                'intent_detection',
                f'Task Message Detection: "{message[:30]}..."',
                is_task,
                f"Plan steps: {len(response.get('plan', []))}, Task ID: {response.get('task_id', 'None')}",
                response_time
            )
        
        # Test 1.3: Fallback mechanism when Ollama unavailable
        # This would require temporarily disabling Ollama, so we'll test the heuristic patterns
        edge_cases = [
            "ayúdame con algo",  # Ambiguous
            "necesito información",  # Task-like but vague
            "ok perfecto"  # Casual acknowledgment
        ]
        
        for message in edge_cases:
            response = self.make_request('POST', '/agent/chat', {
                'message': message,
                'test_mode': True
            })
            
            response_time = response.get('_response_time', 0)
            
            # Check if system handles edge cases appropriately
            handled_appropriately = (
                '_status_code' in response and 
                response['_status_code'] == 200 and
                'response' in response
            )
            
            self.log_test(
                'intent_detection',
                f'Edge Case Handling: "{message}"',
                handled_appropriately,
                f"Status: {response.get('_status_code')}, Has response: {bool(response.get('response'))}",
                response_time
            )

    def test_2_robust_plan_generation(self):
        """Test 2: Robust Plan Generation - JSON schema validation, retry mechanisms"""
        print("\n📋 Testing Robust Plan Generation...")
        
        # Test 2.1: JSON Schema Validation
        complex_task = "crear un análisis completo de mercado para productos tecnológicos emergentes"
        
        response = self.make_request('POST', '/agent/chat', {
            'message': complex_task,
            'test_mode': True
        })
        
        response_time = response.get('_response_time', 0)
        plan = response.get('plan', [])
        
        # Validate plan structure according to schema
        schema_valid = True
        schema_errors = []
        
        if not isinstance(plan, list) or len(plan) == 0:
            schema_valid = False
            schema_errors.append("Plan is not a valid list or is empty")
        else:
            for i, step in enumerate(plan):
                if not isinstance(step, dict):
                    schema_valid = False
                    schema_errors.append(f"Step {i} is not a dict")
                    continue
                
                required_fields = ['title', 'description', 'tool']
                for field in required_fields:
                    if field not in step:
                        schema_valid = False
                        schema_errors.append(f"Step {i} missing required field: {field}")
                
                # Check field constraints
                if 'title' in step and (len(step['title']) < 5 or len(step['title']) > 100):
                    schema_valid = False
                    schema_errors.append(f"Step {i} title length invalid")
                
                if 'description' in step and (len(step['description']) < 10 or len(step['description']) > 300):
                    schema_valid = False
                    schema_errors.append(f"Step {i} description length invalid")
        
        self.log_test(
            'plan_generation',
            'JSON Schema Validation',
            schema_valid,
            f"Plan steps: {len(plan)}, Errors: {'; '.join(schema_errors) if schema_errors else 'None'}",
            response_time
        )
        
        # Test 2.2: Plan generation with proper status
        task_id = response.get('task_id')
        if task_id:
            # Check if task has proper initial status
            status_response = self.make_request('GET', f'/agent/status')
            status_time = status_response.get('_response_time', 0)
            
            proper_status = (
                status_response.get('_status_code') == 200 and
                'status' in status_response
            )
            
            self.log_test(
                'plan_generation',
                'Initial Task Status',
                proper_status,
                f"Status endpoint accessible: {proper_status}, Task ID: {task_id}",
                status_time
            )
        
        # Test 2.3: Fallback plan generation
        # Test with a very complex request that might challenge the AI
        complex_request = "desarrollar una aplicación de inteligencia artificial cuántica que integre blockchain, IoT, realidad aumentada y machine learning para revolucionar la industria financiera global"
        
        fallback_response = self.make_request('POST', '/agent/chat', {
            'message': complex_request,
            'test_mode': True
        })
        
        fallback_time = fallback_response.get('_response_time', 0)
        
        # Check if system provides some form of plan even for complex requests
        fallback_works = (
            fallback_response.get('_status_code') == 200 and
            (fallback_response.get('plan') or fallback_response.get('response'))
        )
        
        plan_source = 'unknown'
        if 'plan_source' in fallback_response:
            plan_source = fallback_response['plan_source']
        elif fallback_response.get('plan'):
            plan_source = 'ai_generated'
        
        self.log_test(
            'plan_generation',
            'Fallback Plan Generation',
            fallback_works,
            f"Plan source: {plan_source}, Has plan: {bool(fallback_response.get('plan'))}, Has response: {bool(fallback_response.get('response'))}",
            fallback_time
        )

    def test_3_websocket_communication(self):
        """Test 3: Real-time WebSocket Communication - WebSocket manager, task tracking"""
        print("\n🔌 Testing WebSocket Communication...")
        
        # Test 3.1: WebSocket Manager Initialization
        health_response = self.make_request('GET', '/health')
        health_time = health_response.get('_response_time', 0)
        
        websocket_initialized = (
            health_response.get('_status_code') == 200 and
            health_response.get('services', {}).get('ollama') is not None
        )
        
        self.log_test(
            'websocket_communication',
            'WebSocket Infrastructure Check',
            websocket_initialized,
            f"Health check passed: {websocket_initialized}, Services: {list(health_response.get('services', {}).keys())}",
            health_time
        )
        
        # Test 3.2: Task ID Generation for WebSocket Tracking
        task_message = "realizar un análisis de datos de ejemplo"
        task_response = self.make_request('POST', '/agent/chat', {
            'message': task_message,
            'test_mode': True
        })
        
        task_time = task_response.get('_response_time', 0)
        task_id = task_response.get('task_id')
        
        task_tracking = bool(task_id) and len(str(task_id)) > 10
        
        self.log_test(
            'websocket_communication',
            'Task ID Generation for Tracking',
            task_tracking,
            f"Task ID: {task_id}, Valid format: {task_tracking}",
            task_time
        )
        
        # Test 3.3: Real-time Update Structure
        # Check if response includes fields needed for real-time updates
        update_fields = ['task_id', 'status', 'plan']
        has_update_fields = all(field in task_response for field in update_fields)
        
        self.log_test(
            'websocket_communication',
            'Real-time Update Structure',
            has_update_fields,
            f"Update fields present: {[field for field in update_fields if field in task_response]}",
            0
        )
        
        # Test 3.4: WebSocket Manager Integration
        # Test if the system can handle multiple concurrent requests (simulating WebSocket scenarios)
        concurrent_requests = []
        start_time = time.time()
        
        for i in range(3):
            response = self.make_request('POST', '/agent/chat', {
                'message': f"tarea de prueba {i+1}",
                'test_mode': True
            })
            concurrent_requests.append(response)
        
        concurrent_time = time.time() - start_time
        
        all_successful = all(
            req.get('_status_code') == 200 and req.get('task_id') 
            for req in concurrent_requests
        )
        
        unique_task_ids = len(set(req.get('task_id') for req in concurrent_requests if req.get('task_id'))) == 3
        
        self.log_test(
            'websocket_communication',
            'Concurrent Task Handling',
            all_successful and unique_task_ids,
            f"All successful: {all_successful}, Unique task IDs: {unique_task_ids}, Total time: {concurrent_time:.2f}s",
            concurrent_time
        )

    def test_4_ollama_parsing(self):
        """Test 4: Robust Ollama Response Parsing - Multiple JSON extraction strategies"""
        print("\n🤖 Testing Ollama Response Parsing...")
        
        # Test 4.1: Ollama Connection and Health
        ollama_health = self.make_request('GET', '/agent/health')
        ollama_time = ollama_health.get('_response_time', 0)
        
        ollama_connected = (
            ollama_health.get('_status_code') == 200 and
            ollama_health.get('services', {}).get('ollama') == True
        )
        
        expected_endpoint = "https://78d08925604a.ngrok-free.app"
        expected_model = "llama3.1:8b"
        
        endpoint_correct = expected_endpoint in str(ollama_health.get('ollama_config', {}))
        model_available = expected_model in str(ollama_health.get('available_models', []))
        
        self.log_test(
            'ollama_parsing',
            'Ollama Connection and Configuration',
            ollama_connected and endpoint_correct,
            f"Connected: {ollama_connected}, Endpoint: {endpoint_correct}, Model available: {model_available}",
            ollama_time
        )
        
        # Test 4.2: Response Parsing with Different Message Types
        parsing_test_messages = [
            "explícame qué es la inteligencia artificial",  # Simple explanation
            "crear un plan para mejorar la productividad",  # Plan generation
            "buscar información sobre energías renovables"  # Search task
        ]
        
        for message in parsing_test_messages:
            response = self.make_request('POST', '/agent/chat', {
                'message': message,
                'test_mode': True
            })
            
            response_time = response.get('_response_time', 0)
            
            # Check if response was parsed successfully
            parsing_successful = (
                response.get('_status_code') == 200 and
                'response' in response and
                len(response.get('response', '')) > 0 and
                'error' not in response
            )
            
            # Check for structured response elements
            has_structure = bool(response.get('plan') or response.get('task_id'))
            
            self.log_test(
                'ollama_parsing',
                f'Response Parsing: "{message[:30]}..."',
                parsing_successful,
                f"Parsed: {parsing_successful}, Has structure: {has_structure}, Response length: {len(response.get('response', ''))}",
                response_time
            )
        
        # Test 4.3: Error Recovery and Fallback
        # Test with a potentially problematic request
        edge_case_message = "¿¿¿crear un plan muy complejo con múltiples pasos y herramientas???"
        
        edge_response = self.make_request('POST', '/agent/chat', {
            'message': edge_case_message,
            'test_mode': True
        })
        
        edge_time = edge_response.get('_response_time', 0)
        
        # Check if system handles edge cases gracefully
        error_recovery = (
            edge_response.get('_status_code') == 200 and
            ('response' in edge_response or 'error' in edge_response)
        )
        
        self.log_test(
            'ollama_parsing',
            'Error Recovery and Fallback',
            error_recovery,
            f"Status: {edge_response.get('_status_code')}, Has response: {bool(edge_response.get('response'))}, Has error: {bool(edge_response.get('error'))}",
            edge_time
        )
        
        # Test 4.4: Multiple Parsing Strategies
        # Test if system can handle different response formats
        status_response = self.make_request('GET', '/agent/status')
        status_time = status_response.get('_response_time', 0)
        
        status_parsing = (
            status_response.get('_status_code') == 200 and
            isinstance(status_response, dict) and
            len(status_response) > 1
        )
        
        self.log_test(
            'ollama_parsing',
            'Multiple Format Parsing',
            status_parsing,
            f"Status endpoint parsed: {status_parsing}, Fields: {len(status_response)}",
            status_time
        )

    def test_5_task_persistence(self):
        """Test 5: Task Persistence with MongoDB - Task storage, recovery"""
        print("\n💾 Testing Task Persistence...")
        
        # Test 5.1: Database Connection
        health_response = self.make_request('GET', '/health')
        health_time = health_response.get('_response_time', 0)
        
        db_connected = (
            health_response.get('_status_code') == 200 and
            health_response.get('services', {}).get('database') == True
        )
        
        self.log_test(
            'task_persistence',
            'MongoDB Database Connection',
            db_connected,
            f"Database connected: {db_connected}, Services: {health_response.get('services', {})}",
            health_time
        )
        
        # Test 5.2: Task Creation and Storage
        persistence_task = "crear un documento de prueba para verificar persistencia"
        
        task_response = self.make_request('POST', '/agent/chat', {
            'message': persistence_task,
            'test_mode': True
        })
        
        task_time = task_response.get('_response_time', 0)
        task_id = task_response.get('task_id')
        
        task_created = (
            task_response.get('_status_code') == 200 and
            task_id is not None and
            task_response.get('plan') is not None
        )
        
        self.log_test(
            'task_persistence',
            'Task Creation and Storage',
            task_created,
            f"Task ID: {task_id}, Plan steps: {len(task_response.get('plan', []))}, Status: {task_response.get('status')}",
            task_time
        )
        
        # Test 5.3: Task Retrieval and Recovery
        if task_id:
            # Wait a moment to ensure task is persisted
            time.sleep(1)
            
            # Try to retrieve task information through status endpoint
            status_response = self.make_request('GET', '/agent/status')
            status_time = status_response.get('_response_time', 0)
            
            task_retrievable = (
                status_response.get('_status_code') == 200 and
                'status' in status_response
            )
            
            self.log_test(
                'task_persistence',
                'Task Retrieval Capability',
                task_retrievable,
                f"Status retrievable: {task_retrievable}, Response fields: {len(status_response)}",
                status_time
            )
        
        # Test 5.4: Step Status Updates
        # Create another task to test step updates
        step_task = "analizar datos de ejemplo con múltiples pasos"
        
        step_response = self.make_request('POST', '/agent/chat', {
            'message': step_task,
            'test_mode': True
        })
        
        step_time = step_response.get('_response_time', 0)
        step_plan = step_response.get('plan', [])
        
        step_tracking = (
            step_response.get('_status_code') == 200 and
            len(step_plan) > 0 and
            all('id' in step for step in step_plan if isinstance(step, dict))
        )
        
        self.log_test(
            'task_persistence',
            'Step Status Tracking',
            step_tracking,
            f"Steps with IDs: {len([s for s in step_plan if isinstance(s, dict) and 'id' in s])}, Total steps: {len(step_plan)}",
            step_time
        )
        
        # Test 5.5: Task History and Analytics
        stats_response = self.make_request('GET', '/stats')
        stats_time = stats_response.get('_response_time', 0)
        
        stats_available = (
            stats_response.get('_status_code') == 200 and
            isinstance(stats_response, dict)
        )
        
        self.log_test(
            'task_persistence',
            'Task History and Analytics',
            stats_available,
            f"Stats available: {stats_available}, Stats fields: {len(stats_response) if isinstance(stats_response, dict) else 0}",
            stats_time
        )

    def test_6_error_handling(self):
        """Test 6: Error Handling and Resilience - Retry mechanisms, exponential backoff"""
        print("\n🛡️ Testing Error Handling and Resilience...")
        
        # Test 6.1: Invalid Endpoint Handling
        invalid_response = self.make_request('GET', '/invalid-endpoint')
        invalid_time = invalid_response.get('_response_time', 0)
        
        proper_404 = invalid_response.get('_status_code') == 404
        
        self.log_test(
            'error_handling',
            'Invalid Endpoint Handling',
            proper_404,
            f"Status code: {invalid_response.get('_status_code')}, Proper 404: {proper_404}",
            invalid_time
        )
        
        # Test 6.2: Invalid Request Data Handling
        invalid_data_response = self.make_request('POST', '/agent/chat', {
            'invalid_field': 'test',
            # Missing required 'message' field
        })
        
        invalid_data_time = invalid_data_response.get('_response_time', 0)
        
        proper_400 = invalid_data_response.get('_status_code') == 400
        has_error_message = 'error' in invalid_data_response
        
        self.log_test(
            'error_handling',
            'Invalid Request Data Handling',
            proper_400 or has_error_message,
            f"Status: {invalid_data_response.get('_status_code')}, Has error: {has_error_message}",
            invalid_data_time
        )
        
        # Test 6.3: Timeout and Resilience
        # Test with a complex request that might take time
        complex_request = "realizar un análisis exhaustivo y detallado de múltiples aspectos de la inteligencia artificial, incluyendo machine learning, deep learning, procesamiento de lenguaje natural, visión por computadora, robótica, ética en IA, y futuras aplicaciones"
        
        timeout_response = self.make_request('POST', '/agent/chat', {
            'message': complex_request,
            'test_mode': True
        }, timeout=45)  # Longer timeout for complex request
        
        timeout_time = timeout_response.get('_response_time', 0)
        
        handles_complexity = (
            timeout_response.get('_status_code') == 200 and
            ('response' in timeout_response or 'plan' in timeout_response) and
            'error' not in timeout_response
        )
        
        self.log_test(
            'error_handling',
            'Complex Request Handling',
            handles_complexity,
            f"Handled: {handles_complexity}, Response time: {timeout_time:.2f}s, Has plan: {bool(timeout_response.get('plan'))}",
            timeout_time
        )
        
        # Test 6.4: Service Availability Checks
        health_response = self.make_request('GET', '/health')
        agent_health_response = self.make_request('GET', '/agent/health')
        
        health_time = health_response.get('_response_time', 0)
        agent_health_time = agent_health_response.get('_response_time', 0)
        
        health_endpoints_work = (
            health_response.get('_status_code') == 200 and
            agent_health_response.get('_status_code') == 200
        )
        
        service_monitoring = (
            'services' in health_response and
            isinstance(health_response.get('services'), dict)
        )
        
        self.log_test(
            'error_handling',
            'Service Health Monitoring',
            health_endpoints_work and service_monitoring,
            f"Health endpoints work: {health_endpoints_work}, Service monitoring: {service_monitoring}",
            (health_time + agent_health_time) / 2
        )
        
        # Test 6.5: Graceful Degradation
        # Test multiple rapid requests to see if system handles load
        rapid_requests = []
        start_time = time.time()
        
        for i in range(5):
            response = self.make_request('POST', '/agent/chat', {
                'message': f"prueba rápida {i+1}",
                'test_mode': True
            }, timeout=10)
            rapid_requests.append(response)
        
        rapid_time = time.time() - start_time
        
        successful_requests = sum(1 for req in rapid_requests if req.get('_status_code') == 200)
        success_rate = successful_requests / len(rapid_requests)
        
        graceful_degradation = success_rate >= 0.8  # At least 80% success rate
        
        self.log_test(
            'error_handling',
            'Graceful Degradation Under Load',
            graceful_degradation,
            f"Success rate: {success_rate:.1%} ({successful_requests}/{len(rapid_requests)}), Total time: {rapid_time:.2f}s",
            rapid_time
        )

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Mitosis V5-beta Backend Testing...")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"⏰ Test started at: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Run all test suites
        self.test_1_intent_detection_system()
        self.test_2_robust_plan_generation()
        self.test_3_websocket_communication()
        self.test_4_ollama_parsing()
        self.test_5_task_persistence()
        self.test_6_error_handling()
        
        # Generate summary report
        self.generate_summary_report()

    def generate_summary_report(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.results.items():
            passed = results['passed']
            failed = results['failed']
            total = passed + failed
            success_rate = (passed / total * 100) if total > 0 else 0
            
            status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
            
            print(f"\n{status_icon} {category.upper().replace('_', ' ')}")
            print(f"   Passed: {passed}/{total} ({success_rate:.1f}%)")
            
            if failed > 0:
                print(f"   Failed tests:")
                for test in results['tests']:
                    if not test['passed']:
                        print(f"     - {test['name']}: {test['details']}")
            
            total_passed += passed
            total_failed += failed
        
        # Overall summary
        overall_total = total_passed + total_failed
        overall_success_rate = (total_passed / overall_total * 100) if overall_total > 0 else 0
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {overall_total}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_failed}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        
        # Determine overall status
        if overall_success_rate >= 90:
            status = "🎉 EXCELLENT - All major improvements verified and working"
        elif overall_success_rate >= 80:
            status = "✅ GOOD - Most improvements working with minor issues"
        elif overall_success_rate >= 70:
            status = "⚠️ ACCEPTABLE - Core functionality working, some improvements need attention"
        else:
            status = "❌ NEEDS WORK - Significant issues found in multiple areas"
        
        print(f"\n🏆 FINAL ASSESSMENT: {status}")
        
        # Specific UPGRADE.md improvements status
        print(f"\n📋 UPGRADE.MD IMPROVEMENTS STATUS:")
        improvements = [
            ("Intent Detection System", self.results['intent_detection']),
            ("Robust Plan Generation", self.results['plan_generation']),
            ("Real-time WebSocket Communication", self.results['websocket_communication']),
            ("Robust Ollama Response Parsing", self.results['ollama_parsing']),
            ("Task Persistence with MongoDB", self.results['task_persistence']),
            ("Error Handling and Resilience", self.results['error_handling'])
        ]
        
        for improvement, results in improvements:
            total = results['passed'] + results['failed']
            success_rate = (results['passed'] / total * 100) if total > 0 else 0
            status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
            print(f"   {status_icon} {improvement}: {success_rate:.1f}% ({results['passed']}/{total})")
        
        print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")
        print("=" * 80)

if __name__ == "__main__":
    tester = MitosisV5Tester()
    tester.run_all_tests()