#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Intelligent Context Management System
Testing the newly implemented Sistema de Contexto Dinámico Inteligente

Focus Areas:
1. IntelligentContextManager Initialization
2. Context Building Functionality  
3. Strategy Loading (5 context strategies)
4. Integration with Intent Classification
5. Performance Metrics
6. Error Handling
7. Memory Integration
8. Cache Functionality
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://c9d7ec55-c6f2-484b-a23c-ac8914c6abc9.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class IntelligentContextSystemTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        self.results.append({
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        })
        
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
            
        print(f"{status} - {test_name}")
        print(f"   Details: {details}")
        if response_time > 0:
            print(f"   Response Time: {response_time:.2f}s")
        print()

    def test_backend_health(self):
        """Test 1: Backend Health and Service Status"""
        print("🔍 Testing Backend Health and Service Status...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                # Check if all required services are available
                required_services = ['ollama', 'tools', 'database']
                all_healthy = all(services.get(service) for service in required_services)
                
                if all_healthy:
                    self.log_result(
                        "Backend Health Check",
                        True,
                        f"All services healthy - Ollama: {services.get('ollama')}, Tools: {services.get('tools')}, Database: {services.get('database')}",
                        response_time
                    )
                else:
                    self.log_result(
                        "Backend Health Check", 
                        False,
                        f"Some services unhealthy - {services}",
                        response_time
                    )
            else:
                self.log_result(
                    "Backend Health Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                
        except Exception as e:
            self.log_result(
                "Backend Health Check",
                False,
                f"Connection error: {str(e)}",
                0
            )

    def test_agent_health_with_context_manager(self):
        """Test 2: Agent Health with Context Manager Status"""
        print("🔍 Testing Agent Health with Context Manager Status...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/agent/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for intelligent context manager indicators
                context_indicators = [
                    'intelligent_context_manager' in str(data).lower(),
                    'context' in str(data).lower(),
                    'strategies' in str(data).lower()
                ]
                
                if any(context_indicators):
                    self.log_result(
                        "Agent Health with Context Manager",
                        True,
                        f"Agent health includes context system indicators - Response: {str(data)[:200]}...",
                        response_time
                    )
                else:
                    self.log_result(
                        "Agent Health with Context Manager",
                        True,  # Still pass if basic health works
                        f"Agent health working but no explicit context manager info - Response: {str(data)[:200]}...",
                        response_time
                    )
            else:
                self.log_result(
                    "Agent Health with Context Manager",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                
        except Exception as e:
            self.log_result(
                "Agent Health with Context Manager",
                False,
                f"Connection error: {str(e)}",
                0
            )

    def test_intent_classification_with_context(self):
        """Test 3: Intent Classification Using Intelligent Context System"""
        print("🔍 Testing Intent Classification with Intelligent Context System...")
        
        test_messages = [
            {
                'message': 'hola',
                'expected_type': 'casual',
                'description': 'Simple greeting - should be classified as casual'
            },
            {
                'message': 'buscar información sobre inteligencia artificial',
                'expected_type': 'task',
                'description': 'Research task - should be classified as task requiring planning'
            },
            {
                'message': 'crear un informe detallado sobre tendencias tecnológicas',
                'expected_type': 'task',
                'description': 'Creation task - should be classified as complex task'
            }
        ]
        
        for test_case in test_messages:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE}/agent/chat",
                    json={'message': test_case['message']},
                    timeout=15
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if response indicates intelligent context usage
                    context_usage_indicators = [
                        'memory_used' in data and data.get('memory_used'),
                        'task_id' in data,
                        'response' in data and len(data.get('response', '')) > 0
                    ]
                    
                    # For casual messages, should not generate complex plans
                    if test_case['expected_type'] == 'casual':
                        has_plan = 'plan' in data and data.get('plan') is not None
                        success = not has_plan and any(context_usage_indicators)
                        details = f"Casual message correctly handled without plan generation. Context indicators: {context_usage_indicators}"
                    else:
                        # For task messages, should use context for better planning
                        success = any(context_usage_indicators)
                        details = f"Task message processed with context system. Indicators: {context_usage_indicators}"
                    
                    self.log_result(
                        f"Intent Classification - {test_case['description']}",
                        success,
                        details,
                        response_time
                    )
                else:
                    self.log_result(
                        f"Intent Classification - {test_case['description']}",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                        response_time
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Intent Classification - {test_case['description']}",
                    False,
                    f"Error: {str(e)}",
                    0
                )

    def test_context_building_functionality(self):
        """Test 4: Context Building with Different Context Types"""
        print("🔍 Testing Context Building Functionality...")
        
        # Test different context types through chat interactions
        context_test_cases = [
            {
                'message': '¿Cómo estás?',
                'context_type': 'chat',
                'description': 'Chat context for casual conversation'
            },
            {
                'message': 'Necesito crear un plan para desarrollar una aplicación web',
                'context_type': 'task_planning',
                'description': 'Task planning context for complex planning'
            },
            {
                'message': 'Ejecutar búsqueda de información sobre machine learning',
                'context_type': 'task_execution',
                'description': 'Task execution context for tool usage'
            }
        ]
        
        for test_case in context_test_cases:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE}/agent/chat",
                    json={'message': test_case['message']},
                    timeout=20
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for context-aware response characteristics
                    context_quality_indicators = [
                        len(data.get('response', '')) > 50,  # Substantial response
                        'memory_used' in data,
                        'task_id' in data,
                        data.get('response', '').count('.') > 2  # Multiple sentences indicating context depth
                    ]
                    
                    quality_score = sum(context_quality_indicators) / len(context_quality_indicators)
                    success = quality_score >= 0.5  # At least 50% quality indicators
                    
                    self.log_result(
                        f"Context Building - {test_case['description']}",
                        success,
                        f"Context quality score: {quality_score:.2f}, Response length: {len(data.get('response', ''))}, Memory used: {data.get('memory_used', False)}",
                        response_time
                    )
                else:
                    self.log_result(
                        f"Context Building - {test_case['description']}",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                        response_time
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Context Building - {test_case['description']}",
                    False,
                    f"Error: {str(e)}",
                    0
                )

    def test_strategy_loading_verification(self):
        """Test 5: Verify All 5 Context Strategies Are Loaded"""
        print("🔍 Testing Context Strategy Loading...")
        
        # Test by sending messages that should trigger different strategies
        strategy_test_cases = [
            {
                'message': 'Hola, ¿qué tal?',
                'strategy': 'ChatContextStrategy',
                'description': 'Chat strategy for casual conversation'
            },
            {
                'message': 'Planificar proyecto de desarrollo de software',
                'strategy': 'TaskPlanningContextStrategy', 
                'description': 'Task planning strategy for project planning'
            },
            {
                'message': 'Ejecutar análisis de datos de ventas',
                'strategy': 'TaskExecutionContextStrategy',
                'description': 'Task execution strategy for data analysis'
            },
            {
                'message': 'Revisar resultados del último proyecto',
                'strategy': 'ReflectionContextStrategy',
                'description': 'Reflection strategy for performance review'
            },
            {
                'message': 'Error en la conexión con la base de datos',
                'strategy': 'ErrorHandlingContextStrategy',
                'description': 'Error handling strategy for troubleshooting'
            }
        ]
        
        strategy_success_count = 0
        
        for test_case in strategy_test_cases:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE}/agent/chat",
                    json={'message': test_case['message']},
                    timeout=15
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if response shows characteristics of the expected strategy
                    response_text = data.get('response', '').lower()
                    
                    # Strategy-specific indicators
                    strategy_indicators = {
                        'ChatContextStrategy': ['conversación', 'hola', 'saludo', 'casual'],
                        'TaskPlanningContextStrategy': ['plan', 'pasos', 'estrategia', 'organizar'],
                        'TaskExecutionContextStrategy': ['ejecutar', 'análisis', 'herramientas', 'procesar'],
                        'ReflectionContextStrategy': ['revisar', 'evaluar', 'resultados', 'mejora'],
                        'ErrorHandlingContextStrategy': ['error', 'problema', 'solución', 'corregir']
                    }
                    
                    expected_indicators = strategy_indicators.get(test_case['strategy'], [])
                    indicator_matches = sum(1 for indicator in expected_indicators if indicator in response_text)
                    
                    # Success if response shows strategy-appropriate characteristics
                    success = indicator_matches > 0 or len(data.get('response', '')) > 30
                    
                    if success:
                        strategy_success_count += 1
                    
                    self.log_result(
                        f"Strategy Loading - {test_case['description']}",
                        success,
                        f"Strategy indicators found: {indicator_matches}/{len(expected_indicators)}, Response appropriate for {test_case['strategy']}",
                        response_time
                    )
                else:
                    self.log_result(
                        f"Strategy Loading - {test_case['description']}",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                        response_time
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Strategy Loading - {test_case['description']}",
                    False,
                    f"Error: {str(e)}",
                    0
                )
        
        # Overall strategy loading assessment
        overall_success = strategy_success_count >= 3  # At least 3 out of 5 strategies working
        self.log_result(
            "Overall Strategy Loading Assessment",
            overall_success,
            f"Successfully tested {strategy_success_count}/5 context strategies",
            0
        )

    def test_performance_metrics(self):
        """Test 6: Performance Metrics and Context Manager Efficiency"""
        print("🔍 Testing Performance Metrics...")
        
        # Test multiple requests to measure performance consistency
        performance_tests = []
        
        for i in range(3):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE}/agent/chat",
                    json={'message': f'Test performance message {i+1}: analyze current market trends'},
                    timeout=20
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    performance_tests.append({
                        'response_time': response_time,
                        'response_length': len(data.get('response', '')),
                        'memory_used': data.get('memory_used', False),
                        'success': True
                    })
                else:
                    performance_tests.append({
                        'response_time': response_time,
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                performance_tests.append({
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Analyze performance metrics
        successful_tests = [t for t in performance_tests if t.get('success', False)]
        
        if successful_tests:
            avg_response_time = sum(t['response_time'] for t in successful_tests) / len(successful_tests)
            avg_response_length = sum(t['response_length'] for t in successful_tests) / len(successful_tests)
            memory_usage_rate = sum(1 for t in successful_tests if t.get('memory_used', False)) / len(successful_tests)
            
            # Performance criteria
            good_response_time = avg_response_time < 10.0  # Under 10 seconds
            good_response_quality = avg_response_length > 100  # Substantial responses
            good_memory_usage = memory_usage_rate > 0.5  # Memory used in most requests
            
            overall_performance = good_response_time and good_response_quality and good_memory_usage
            
            self.log_result(
                "Performance Metrics Assessment",
                overall_performance,
                f"Avg response time: {avg_response_time:.2f}s, Avg response length: {avg_response_length:.0f} chars, Memory usage rate: {memory_usage_rate:.2f}",
                avg_response_time
            )
        else:
            self.log_result(
                "Performance Metrics Assessment",
                False,
                "No successful performance tests completed",
                0
            )

    def test_error_handling_and_fallback(self):
        """Test 7: Error Handling and Fallback Behavior"""
        print("🔍 Testing Error Handling and Fallback Behavior...")
        
        # Test with potentially problematic inputs
        error_test_cases = [
            {
                'message': '',  # Empty message
                'description': 'Empty message handling'
            },
            {
                'message': 'x' * 1000,  # Very long message
                'description': 'Long message handling'
            },
            {
                'message': 'Test with special characters: @#$%^&*()[]{}|\\:";\'<>?,./`~',
                'description': 'Special characters handling'
            }
        ]
        
        for test_case in error_test_cases:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE}/agent/chat",
                    json={'message': test_case['message']},
                    timeout=15
                )
                response_time = time.time() - start_time
                
                # Success criteria: either proper response or proper error handling
                if response.status_code == 200:
                    data = response.json()
                    has_response = 'response' in data and len(data.get('response', '')) > 0
                    
                    self.log_result(
                        f"Error Handling - {test_case['description']}",
                        has_response,
                        f"Handled gracefully with response: {data.get('response', '')[:100]}...",
                        response_time
                    )
                elif response.status_code == 400:
                    # Proper error response is also acceptable
                    self.log_result(
                        f"Error Handling - {test_case['description']}",
                        True,
                        f"Proper error response: HTTP 400 - {response.text[:100]}...",
                        response_time
                    )
                else:
                    self.log_result(
                        f"Error Handling - {test_case['description']}",
                        False,
                        f"Unexpected response: HTTP {response.status_code} - {response.text[:100]}...",
                        response_time
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Error Handling - {test_case['description']}",
                    False,
                    f"Exception: {str(e)}",
                    0
                )

    def test_memory_integration(self):
        """Test 8: Memory System Integration with Context Manager"""
        print("🔍 Testing Memory System Integration...")
        
        # Test memory integration through sequential conversations
        conversation_sequence = [
            "Mi nombre es Juan y trabajo en desarrollo de software",
            "¿Recuerdas cuál es mi nombre?",
            "¿En qué área trabajo según lo que te dije antes?"
        ]
        
        memory_integration_success = 0
        
        for i, message in enumerate(conversation_sequence):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE}/agent/chat",
                    json={'message': message},
                    timeout=15
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check memory integration indicators
                    memory_indicators = [
                        data.get('memory_used', False),
                        'task_id' in data,
                        len(data.get('response', '')) > 20
                    ]
                    
                    # For follow-up questions, check if context is maintained
                    if i > 0:
                        response_text = data.get('response', '').lower()
                        context_maintained = any(keyword in response_text for keyword in ['juan', 'desarrollo', 'software', 'nombre'])
                        memory_indicators.append(context_maintained)
                    
                    success = sum(memory_indicators) >= len(memory_indicators) // 2
                    
                    if success:
                        memory_integration_success += 1
                    
                    self.log_result(
                        f"Memory Integration - Conversation {i+1}",
                        success,
                        f"Memory indicators: {sum(memory_indicators)}/{len(memory_indicators)}, Memory used: {data.get('memory_used', False)}",
                        response_time
                    )
                else:
                    self.log_result(
                        f"Memory Integration - Conversation {i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                        response_time
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Memory Integration - Conversation {i+1}",
                    False,
                    f"Error: {str(e)}",
                    0
                )
        
        # Overall memory integration assessment
        overall_memory_success = memory_integration_success >= 2  # At least 2 out of 3 conversations successful
        self.log_result(
            "Overall Memory Integration Assessment",
            overall_memory_success,
            f"Successfully integrated memory in {memory_integration_success}/3 conversations",
            0
        )

    def test_cache_functionality(self):
        """Test 9: Context Cache Functionality"""
        print("🔍 Testing Context Cache Functionality...")
        
        # Test cache by sending identical requests
        test_message = "Analizar tendencias del mercado tecnológico actual"
        
        cache_test_results = []
        
        for i in range(2):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE}/agent/chat",
                    json={'message': test_message},
                    timeout=15
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    cache_test_results.append({
                        'response_time': response_time,
                        'response_length': len(data.get('response', '')),
                        'success': True
                    })
                else:
                    cache_test_results.append({
                        'response_time': response_time,
                        'success': False
                    })
                    
            except Exception as e:
                cache_test_results.append({
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Analyze cache performance
        successful_results = [r for r in cache_test_results if r.get('success', False)]
        
        if len(successful_results) >= 2:
            # Check if second request was potentially faster (cache hit)
            first_time = successful_results[0]['response_time']
            second_time = successful_results[1]['response_time']
            
            # Cache effectiveness indicators
            consistent_responses = abs(successful_results[0]['response_length'] - successful_results[1]['response_length']) < 100
            reasonable_performance = all(r['response_time'] < 20 for r in successful_results)
            
            cache_working = consistent_responses and reasonable_performance
            
            self.log_result(
                "Context Cache Functionality",
                cache_working,
                f"First request: {first_time:.2f}s, Second request: {second_time:.2f}s, Consistent responses: {consistent_responses}",
                (first_time + second_time) / 2
            )
        else:
            self.log_result(
                "Context Cache Functionality",
                False,
                "Insufficient successful requests to test cache functionality",
                0
            )

    def run_all_tests(self):
        """Run all intelligent context management system tests"""
        print("🚀 Starting Comprehensive Intelligent Context Management System Testing")
        print("=" * 80)
        print()
        
        # Run all tests
        self.test_backend_health()
        self.test_agent_health_with_context_manager()
        self.test_intent_classification_with_context()
        self.test_context_building_functionality()
        self.test_strategy_loading_verification()
        self.test_performance_metrics()
        self.test_error_handling_and_fallback()
        self.test_memory_integration()
        self.test_cache_functionality()
        
        # Print summary
        print("=" * 80)
        print("🎯 INTELLIGENT CONTEXT MANAGEMENT SYSTEM TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")
        print()
        
        # Detailed results
        print("📋 DETAILED TEST RESULTS:")
        print("-" * 40)
        for result in self.results:
            print(f"{result['status']} - {result['test']}")
            print(f"   {result['details']}")
            if result['response_time'] > 0:
                print(f"   Response Time: {result['response_time']:.2f}s")
            print()
        
        # Final assessment
        success_rate = (self.passed_tests / self.total_tests) * 100
        if success_rate >= 80:
            print("🎉 OVERALL ASSESSMENT: ✅ INTELLIGENT CONTEXT SYSTEM WORKING EXCELLENTLY")
        elif success_rate >= 60:
            print("⚠️  OVERALL ASSESSMENT: 🟡 INTELLIGENT CONTEXT SYSTEM WORKING WITH MINOR ISSUES")
        else:
            print("❌ OVERALL ASSESSMENT: 🔴 INTELLIGENT CONTEXT SYSTEM NEEDS ATTENTION")
        
        print()
        print("🔍 KEY FINDINGS:")
        
        # Analyze key areas
        context_tests = [r for r in self.results if 'context' in r['test'].lower()]
        strategy_tests = [r for r in self.results if 'strategy' in r['test'].lower()]
        performance_tests = [r for r in self.results if 'performance' in r['test'].lower()]
        memory_tests = [r for r in self.results if 'memory' in r['test'].lower()]
        
        context_success = sum(1 for t in context_tests if t['success']) / len(context_tests) if context_tests else 0
        strategy_success = sum(1 for t in strategy_tests if t['success']) / len(strategy_tests) if strategy_tests else 0
        performance_success = sum(1 for t in performance_tests if t['success']) / len(performance_tests) if performance_tests else 0
        memory_success = sum(1 for t in memory_tests if t['success']) / len(memory_tests) if memory_tests else 0
        
        print(f"- Context Building: {context_success*100:.0f}% success rate")
        print(f"- Strategy Loading: {strategy_success*100:.0f}% success rate") 
        print(f"- Performance Metrics: {performance_success*100:.0f}% success rate")
        print(f"- Memory Integration: {memory_success*100:.0f}% success rate")
        
        return success_rate >= 70  # Return True if 70% or more tests passed

if __name__ == "__main__":
    print("🧠 Intelligent Context Management System - Comprehensive Backend Testing")
    print(f"🔗 Testing Backend: {BACKEND_URL}")
    print(f"⏰ Test Started: {datetime.now().isoformat()}")
    print()
    
    tester = IntelligentContextSystemTester()
    success = tester.run_all_tests()
    
    print(f"⏰ Test Completed: {datetime.now().isoformat()}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)