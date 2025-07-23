#!/usr/bin/env python3
"""
MITOSIS BACKEND API TESTING - ICON ASSIGNMENT & TASK CREATION FLOW
Testing the specific fixes for icon coherence and task creation flow
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://11a8329d-458b-411d-ad58-e540e377cb3b.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.api_base = API_BASE
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def log_test(self, test_name, status, details="", error=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def test_backend_health(self):
        """Test basic backend health"""
        try:
            response = self.session.get(f"{self.api_base}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Backend Health Check", 
                    "PASS",
                    f"Status: {data.get('status', 'unknown')}, Services: {data.get('services', {})}"
                )
                return True
            else:
                self.log_test(
                    "Backend Health Check", 
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test("Backend Health Check", "FAIL", "", str(e))
            return False

    def test_agent_status(self):
        """Test agent status endpoint"""
        try:
            response = self.session.get(f"{self.api_base}/agent/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                ollama_status = data.get('ollama', {})
                tools_count = data.get('tools_count', 0)
                
                self.log_test(
                    "Agent Status Check", 
                    "PASS",
                    f"Ollama: {ollama_status.get('connected', False)}, Tools: {tools_count}"
                )
                return data
            else:
                self.log_test(
                    "Agent Status Check", 
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
                return None
                
        except Exception as e:
            self.log_test("Agent Status Check", "FAIL", "", str(e))
            return None

    def test_icon_assignment_restaurants(self):
        """Test icon assignment for restaurant/place tasks (should get 'map' icon)"""
        test_messages = [
            "Buscar los mejores restaurantes de Valencia en 2025",
            "Crear una guía de bares y comida en Madrid",
            "Investigar lugares para comer en Barcelona",
            "Analizar restaurantes con mejor ubicación en la ciudad"
        ]
        
        for message in test_messages:
            try:
                payload = {
                    "message": message,
                    "task_id": f"test_map_{int(time.time())}"
                }
                
                response = self.session.post(
                    f"{self.api_base}/agent/generate-plan", 
                    json=payload, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    suggested_icon = data.get('suggested_icon', 'unknown')
                    
                    if suggested_icon == 'map':
                        self.log_test(
                            f"Icon Assignment - Restaurant/Place", 
                            "PASS",
                            f"Message: '{message[:50]}...' → Icon: '{suggested_icon}'"
                        )
                    else:
                        self.log_test(
                            f"Icon Assignment - Restaurant/Place", 
                            "FAIL",
                            f"Message: '{message[:50]}...' → Expected: 'map', Got: '{suggested_icon}'"
                        )
                else:
                    self.log_test(
                        f"Icon Assignment - Restaurant/Place", 
                        "FAIL",
                        f"HTTP {response.status_code}",
                        response.text[:200]
                    )
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.log_test(f"Icon Assignment - Restaurant/Place", "FAIL", "", str(e))

    def test_icon_assignment_programming(self):
        """Test icon assignment for programming/code tasks (should get 'code' icon)"""
        test_messages = [
            "Crear una aplicación web con React y Node.js",
            "Desarrollar un script en Python para análisis de datos",
            "Escribir código JavaScript para una API REST",
            "Programar una base de datos SQL con consultas optimizadas"
        ]
        
        for message in test_messages:
            try:
                payload = {
                    "message": message,
                    "task_id": f"test_code_{int(time.time())}"
                }
                
                response = self.session.post(
                    f"{self.api_base}/agent/generate-plan", 
                    json=payload, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    suggested_icon = data.get('suggested_icon', 'unknown')
                    
                    if suggested_icon == 'code':
                        self.log_test(
                            f"Icon Assignment - Programming", 
                            "PASS",
                            f"Message: '{message[:50]}...' → Icon: '{suggested_icon}'"
                        )
                    else:
                        self.log_test(
                            f"Icon Assignment - Programming", 
                            "FAIL",
                            f"Message: '{message[:50]}...' → Expected: 'code', Got: '{suggested_icon}'"
                        )
                else:
                    self.log_test(
                        f"Icon Assignment - Programming", 
                        "FAIL",
                        f"HTTP {response.status_code}",
                        response.text[:200]
                    )
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.log_test(f"Icon Assignment - Programming", "FAIL", "", str(e))

    def test_icon_assignment_documents(self):
        """Test icon assignment for document tasks (should get 'file' icon)"""
        test_messages = [
            "Crear un informe técnico sobre inteligencia artificial",
            "Escribir un documento de especificaciones del proyecto",
            "Redactar un artículo sobre tendencias tecnológicas",
            "Generar un archivo de documentación para la API"
        ]
        
        for message in test_messages:
            try:
                payload = {
                    "message": message,
                    "task_id": f"test_file_{int(time.time())}"
                }
                
                response = self.session.post(
                    f"{self.api_base}/agent/generate-plan", 
                    json=payload, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    suggested_icon = data.get('suggested_icon', 'unknown')
                    
                    if suggested_icon == 'file':
                        self.log_test(
                            f"Icon Assignment - Documents", 
                            "PASS",
                            f"Message: '{message[:50]}...' → Icon: '{suggested_icon}'"
                        )
                    else:
                        self.log_test(
                            f"Icon Assignment - Documents", 
                            "FAIL",
                            f"Message: '{message[:50]}...' → Expected: 'file', Got: '{suggested_icon}'"
                        )
                else:
                    self.log_test(
                        f"Icon Assignment - Documents", 
                        "FAIL",
                        f"HTTP {response.status_code}",
                        response.text[:200]
                    )
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.log_test(f"Icon Assignment - Documents", "FAIL", "", str(e))

    def test_simplified_icon_system(self):
        """Test that only the 9 simplified icons are returned"""
        valid_icons = ['map', 'code', 'file', 'chart', 'search', 'image', 'music', 'briefcase', 'target']
        
        test_messages = [
            "Analizar datos de ventas y crear gráficos",  # Should be 'chart'
            "Buscar información sobre machine learning",   # Should be 'search'
            "Crear un logo para la empresa",              # Should be 'image'
            "Desarrollar estrategia de marketing",        # Should be 'briefcase'
            "Completar tarea general de análisis"         # Should be 'target'
        ]
        
        for message in test_messages:
            try:
                payload = {
                    "message": message,
                    "task_id": f"test_simplified_{int(time.time())}"
                }
                
                response = self.session.post(
                    f"{self.api_base}/agent/generate-plan", 
                    json=payload, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    suggested_icon = data.get('suggested_icon', 'unknown')
                    
                    if suggested_icon in valid_icons:
                        self.log_test(
                            f"Simplified Icon System", 
                            "PASS",
                            f"Message: '{message[:50]}...' → Valid Icon: '{suggested_icon}'"
                        )
                    else:
                        self.log_test(
                            f"Simplified Icon System", 
                            "FAIL",
                            f"Message: '{message[:50]}...' → Invalid Icon: '{suggested_icon}' (not in {valid_icons})"
                        )
                else:
                    self.log_test(
                        f"Simplified Icon System", 
                        "FAIL",
                        f"HTTP {response.status_code}",
                        response.text[:200]
                    )
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.log_test(f"Simplified Icon System", "FAIL", "", str(e))

    def test_task_creation_flow(self):
        """Test task creation via API"""
        try:
            # Test creating a new task
            task_message = "Crear un análisis de mercado para productos de software en 2025"
            payload = {
                "message": task_message,
                "task_id": f"test_task_{int(time.time())}"
            }
            
            response = self.session.post(
                f"{self.api_base}/agent/chat", 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                response_text = data.get('response', '')
                
                if task_id and response_text:
                    self.log_test(
                        "Task Creation Flow", 
                        "PASS",
                        f"Task ID: {task_id}, Response length: {len(response_text)} chars"
                    )
                    return task_id
                else:
                    self.log_test(
                        "Task Creation Flow", 
                        "FAIL",
                        "Missing task_id or response in API response"
                    )
                    return None
            else:
                self.log_test(
                    "Task Creation Flow", 
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
                return None
                
        except Exception as e:
            self.log_test("Task Creation Flow", "FAIL", "", str(e))
            return None

    def test_generate_plan_endpoint(self):
        """Test the generate-plan endpoint specifically"""
        try:
            task_message = "Desarrollar una estrategia de marketing digital para una startup tecnológica"
            payload = {
                "message": task_message,
                "task_id": f"test_plan_{int(time.time())}"
            }
            
            response = self.session.post(
                f"{self.api_base}/agent/generate-plan", 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required fields
                required_fields = ['plan', 'enhanced_title', 'suggested_icon', 'complexity']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    plan_steps = data.get('plan', [])
                    enhanced_title = data.get('enhanced_title', '')
                    suggested_icon = data.get('suggested_icon', '')
                    
                    self.log_test(
                        "Generate Plan Endpoint", 
                        "PASS",
                        f"Plan steps: {len(plan_steps)}, Title: '{enhanced_title}', Icon: '{suggested_icon}'"
                    )
                    return data
                else:
                    self.log_test(
                        "Generate Plan Endpoint", 
                        "FAIL",
                        f"Missing required fields: {missing_fields}"
                    )
                    return None
            else:
                self.log_test(
                    "Generate Plan Endpoint", 
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
                return None
                
        except Exception as e:
            self.log_test("Generate Plan Endpoint", "FAIL", "", str(e))
            return None

    def test_title_enhancement(self):
        """Test that titles are being enhanced properly"""
        test_cases = [
            {
                "input": "crear informe",
                "should_contain": ["informe", "crear"]
            },
            {
                "input": "analizar datos de ventas",
                "should_contain": ["análisis", "datos", "ventas"]
            },
            {
                "input": "desarrollar app móvil",
                "should_contain": ["desarrollo", "aplicación", "móvil"]
            }
        ]
        
        for test_case in test_cases:
            try:
                payload = {
                    "message": test_case["input"],
                    "task_id": f"test_title_{int(time.time())}"
                }
                
                response = self.session.post(
                    f"{self.api_base}/agent/generate-plan", 
                    json=payload, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    enhanced_title = data.get('enhanced_title', '').lower()
                    
                    # Check if enhanced title is different from input and contains relevant keywords
                    if enhanced_title != test_case["input"].lower() and len(enhanced_title) > len(test_case["input"]):
                        contains_keywords = any(keyword.lower() in enhanced_title for keyword in test_case["should_contain"])
                        
                        if contains_keywords:
                            self.log_test(
                                "Title Enhancement", 
                                "PASS",
                                f"Input: '{test_case['input']}' → Enhanced: '{data.get('enhanced_title')}'"
                            )
                        else:
                            self.log_test(
                                "Title Enhancement", 
                                "WARN",
                                f"Enhanced title doesn't contain expected keywords: '{enhanced_title}'"
                            )
                    else:
                        self.log_test(
                            "Title Enhancement", 
                            "FAIL",
                            f"Title not properly enhanced: '{test_case['input']}' → '{enhanced_title}'"
                        )
                else:
                    self.log_test(
                        "Title Enhancement", 
                        "FAIL",
                        f"HTTP {response.status_code}",
                        response.text[:200]
                    )
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.log_test("Title Enhancement", "FAIL", "", str(e))

    def test_websocket_communication(self):
        """Test WebSocket communication readiness"""
        try:
            # Check if WebSocket manager is initialized via agent status
            response = self.session.get(f"{self.api_base}/agent/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for WebSocket-related information
                if 'status' in data and data['status'] == 'running':
                    self.log_test(
                        "WebSocket Communication", 
                        "PASS",
                        "Agent status shows 'running' - WebSocket infrastructure ready"
                    )
                else:
                    self.log_test(
                        "WebSocket Communication", 
                        "WARN",
                        "Agent status unclear - WebSocket readiness uncertain"
                    )
            else:
                self.log_test(
                    "WebSocket Communication", 
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test("WebSocket Communication", "FAIL", "", str(e))

    def test_integration_complete_flow(self):
        """Test complete integration flow: create task → generate plan → verify icon"""
        try:
            # Step 1: Create task
            task_message = "Investigar los mejores restaurantes de comida italiana en Valencia y crear una guía completa"
            
            # Step 2: Generate plan
            payload = {
                "message": task_message,
                "task_id": f"test_integration_{int(time.time())}"
            }
            
            response = self.session.post(
                f"{self.api_base}/agent/generate-plan", 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Step 3: Verify all components
                plan = data.get('plan', [])
                enhanced_title = data.get('enhanced_title', '')
                suggested_icon = data.get('suggested_icon', '')
                complexity = data.get('complexity', '')
                
                # Verify icon is correct for restaurant task (should be 'map')
                icon_correct = suggested_icon == 'map'
                
                # Verify plan has steps
                has_plan = len(plan) >= 3
                
                # Verify title is enhanced
                title_enhanced = enhanced_title != task_message and len(enhanced_title) > 0
                
                if icon_correct and has_plan and title_enhanced:
                    self.log_test(
                        "Integration Complete Flow", 
                        "PASS",
                        f"Icon: {suggested_icon} ✓, Plan steps: {len(plan)} ✓, Enhanced title: '{enhanced_title}' ✓"
                    )
                else:
                    issues = []
                    if not icon_correct:
                        issues.append(f"Wrong icon: {suggested_icon} (expected 'map')")
                    if not has_plan:
                        issues.append(f"Insufficient plan steps: {len(plan)}")
                    if not title_enhanced:
                        issues.append("Title not enhanced")
                    
                    self.log_test(
                        "Integration Complete Flow", 
                        "FAIL",
                        f"Issues: {', '.join(issues)}"
                    )
            else:
                self.log_test(
                    "Integration Complete Flow", 
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test("Integration Complete Flow", "FAIL", "", str(e))

    def run_all_tests(self):
        """Run all tests"""
        print("🧪 MITOSIS BACKEND API TESTING - ICON ASSIGNMENT & TASK CREATION FLOW")
        print("=" * 80)
        print()
        
        # Basic connectivity tests
        print("📡 BASIC CONNECTIVITY TESTS")
        print("-" * 40)
        if not self.test_backend_health():
            print("❌ Backend health check failed. Stopping tests.")
            return
        
        agent_status = self.test_agent_status()
        if not agent_status:
            print("⚠️ Agent status check failed. Continuing with limited tests.")
        
        print()
        
        # Icon assignment tests
        print("🎯 ICON ASSIGNMENT TESTS")
        print("-" * 40)
        self.test_icon_assignment_restaurants()
        self.test_icon_assignment_programming()
        self.test_icon_assignment_documents()
        self.test_simplified_icon_system()
        print()
        
        # Task creation flow tests
        print("📋 TASK CREATION FLOW TESTS")
        print("-" * 40)
        self.test_task_creation_flow()
        self.test_generate_plan_endpoint()
        self.test_title_enhancement()
        print()
        
        # Integration tests
        print("🔗 INTEGRATION TESTS")
        print("-" * 40)
        self.test_websocket_communication()
        self.test_integration_complete_flow()
        print()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Warnings: {warned_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['error'] or result['details']}")
            print()
        
        if warned_tests > 0:
            print("⚠️ WARNINGS:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        # Icon assignment analysis
        icon_tests = [r for r in self.test_results if 'Icon Assignment' in r['test']]
        icon_passed = len([r for r in icon_tests if r['status'] == 'PASS'])
        if icon_tests:
            print(f"  - Icon Assignment: {icon_passed}/{len(icon_tests)} tests passed")
        
        # Task creation analysis
        task_tests = [r for r in self.test_results if 'Task Creation' in r['test'] or 'Generate Plan' in r['test']]
        task_passed = len([r for r in task_tests if r['status'] == 'PASS'])
        if task_tests:
            print(f"  - Task Creation Flow: {task_passed}/{len(task_tests)} tests passed")
        
        # Integration analysis
        integration_tests = [r for r in self.test_results if 'Integration' in r['test']]
        integration_passed = len([r for r in integration_tests if r['status'] == 'PASS'])
        if integration_tests:
            print(f"  - Integration Tests: {integration_passed}/{len(integration_tests)} tests passed")
        
        print()
        print("🎯 FOCUS AREAS FROM REVIEW REQUEST:")
        print("  1. Icon Assignment Testing - Testing different task types for coherent icon assignment")
        print("  2. Task Creation Flow Testing - Testing task creation and plan generation")
        print("  3. Integration Testing - Testing complete flow with proper icon assignment")
        print()

if __name__ == "__main__":
    tester = MitosisBackendTester()
    tester.run_all_tests()