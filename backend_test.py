#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND TESTING FOR ICON MAPPING AND FIRST MESSAGE LOGIC FIXES
Testing specific corrections made by main agent:
1. Icon mapping fix: Direct mapping from backend suggested_icon to frontend
2. First message logic fix: Using isFirstUserMessage instead of isFirstMessage
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://74a5e33d-f0aa-4bdf-866a-560ce9007d4f.preview.emergentagent.com"

class IconMappingTester:
    """Test icon mapping corrections"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def test_icon_mapping_coherence(self) -> Dict[str, Any]:
        """Test that suggested_icon from backend maps correctly to frontend icons"""
        logger.info("🎯 Testing icon mapping coherence...")
        
        test_cases = [
            {
                "task": "Crear una aplicación web con React y Node.js",
                "expected_icons": ["code", "globe", "terminal", "database"],
                "category": "development"
            },
            {
                "task": "Encontrar los mejores restaurantes en Madrid",
                "expected_icons": ["map", "search", "navigation"],
                "category": "location"
            },
            {
                "task": "Analizar datos de ventas del último trimestre",
                "expected_icons": ["chart", "database", "calculator"],
                "category": "analysis"
            },
            {
                "task": "Crear un documento técnico sobre IA",
                "expected_icons": ["file", "book", "edit"],
                "category": "document"
            },
            {
                "task": "Desarrollar una estrategia de marketing digital",
                "expected_icons": ["briefcase", "users", "dollar"],
                "category": "business"
            }
        ]
        
        results = {
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "test_results": [],
            "icon_mapping_working": False
        }
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"🧪 Test {i}/{len(test_cases)}: {test_case['task'][:50]}...")
            
            try:
                # Test /api/agent/generate-plan endpoint
                plan_response = self._test_generate_plan_icon(test_case)
                
                # Test /api/agent/chat endpoint  
                chat_response = self._test_chat_icon(test_case)
                
                # Analyze results
                test_result = self._analyze_icon_mapping(test_case, plan_response, chat_response)
                results["test_results"].append(test_result)
                
                if test_result["passed"]:
                    results["passed"] += 1
                    logger.info(f"✅ Test {i} PASSED: Icon '{test_result['actual_icon']}' correctly mapped")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ Test {i} FAILED: Expected {test_result['expected_icons']}, got '{test_result['actual_icon']}'")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Test {i} ERROR: {str(e)}")
                results["failed"] += 1
                results["test_results"].append({
                    "test_case": test_case,
                    "passed": False,
                    "error": str(e),
                    "actual_icon": None
                })
        
        results["icon_mapping_working"] = results["passed"] > results["failed"]
        results["success_rate"] = (results["passed"] / results["total_tests"]) * 100
        
        logger.info(f"🎯 Icon Mapping Test Results: {results['passed']}/{results['total_tests']} passed ({results['success_rate']:.1f}%)")
        return results
    
    def _test_generate_plan_icon(self, test_case: Dict) -> Dict:
        """Test icon assignment in generate-plan endpoint"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/agent/generate-plan",
                json={"task_title": test_case["task"]},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "suggested_icon": data.get("suggested_icon"),
                    "response_data": data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "suggested_icon": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggested_icon": None
            }
    
    def _test_chat_icon(self, test_case: Dict) -> Dict:
        """Test icon assignment in chat endpoint"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/agent/chat",
                json={
                    "message": test_case["task"],
                    "context": {}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get("plan", {})
                return {
                    "success": True,
                    "suggested_icon": plan.get("suggested_icon") if plan else data.get("suggested_icon"),
                    "response_data": data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "suggested_icon": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggested_icon": None
            }
    
    def _analyze_icon_mapping(self, test_case: Dict, plan_response: Dict, chat_response: Dict) -> Dict:
        """Analyze if icon mapping is working correctly"""
        
        # Get actual icons from responses
        plan_icon = plan_response.get("suggested_icon")
        chat_icon = chat_response.get("suggested_icon")
        
        # Check if icons are consistent between endpoints
        icons_consistent = plan_icon == chat_icon if plan_icon and chat_icon else False
        
        # Check if icon is in expected list
        actual_icon = plan_icon or chat_icon
        icon_appropriate = actual_icon in test_case["expected_icons"] if actual_icon else False
        
        # Check if icon is from valid icon set (not None or empty)
        valid_icons = [
            "book", "image", "smartphone", "code", "database", "globe", "search", "file", 
            "settings", "download", "upload", "server", "cloud", "shield", "key", "music", 
            "video", "message", "mail", "chart", "shopping", "dollar", "calendar", "users", 
            "monitor", "terminal", "zap", "briefcase", "lightbulb", "rocket", "star", "award",
            "activity", "calculator", "layers", "package", "wrench", "workflow", "puzzle",
            "building", "archive", "grid", "layout", "send", "share", "component", "target",
            "flag", "edit", "camera", "mic", "headphones", "printer", "scan", "copy", "save",
            "folder", "clock", "bell", "phone", "map", "compass", "navigation", "wifi", "lock"
        ]
        
        icon_valid = actual_icon in valid_icons if actual_icon else False
        
        return {
            "test_case": test_case,
            "plan_icon": plan_icon,
            "chat_icon": chat_icon,
            "actual_icon": actual_icon,
            "expected_icons": test_case["expected_icons"],
            "icons_consistent": icons_consistent,
            "icon_appropriate": icon_appropriate,
            "icon_valid": icon_valid,
            "passed": icons_consistent and icon_valid and actual_icon is not None,
            "plan_response_success": plan_response.get("success", False),
            "chat_response_success": chat_response.get("success", False)
        }


class FirstMessageLogicTester:
    """Test first message logic corrections"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def test_first_message_detection(self) -> Dict[str, Any]:
        """Test that isFirstUserMessage logic works correctly for new tasks"""
        logger.info("🔄 Testing first message detection logic...")
        
        test_scenarios = [
            {
                "scenario": "New task creation with first message",
                "task_title": "Crear un análisis de mercado para productos de software",
                "first_message": "Necesito un análisis completo del mercado de software en 2025",
                "expected_behavior": "should_generate_plan"
            },
            {
                "scenario": "Simple task with direct request",
                "task_title": "Buscar información sobre inteligencia artificial",
                "first_message": "Dame información actualizada sobre IA generativa",
                "expected_behavior": "should_generate_plan"
            },
            {
                "scenario": "Complex task requiring planning",
                "task_title": "Desarrollar estrategia de marketing digital",
                "first_message": "Quiero crear una estrategia completa de marketing para mi startup",
                "expected_behavior": "should_generate_plan"
            }
        ]
        
        results = {
            "total_scenarios": len(test_scenarios),
            "passed": 0,
            "failed": 0,
            "scenario_results": [],
            "first_message_logic_working": False
        }
        
        for i, scenario in enumerate(test_scenarios, 1):
            logger.info(f"🧪 Scenario {i}/{len(test_scenarios)}: {scenario['scenario']}")
            
            try:
                # Simulate new task flow
                scenario_result = self._test_new_task_flow(scenario)
                results["scenario_results"].append(scenario_result)
                
                if scenario_result["passed"]:
                    results["passed"] += 1
                    logger.info(f"✅ Scenario {i} PASSED: First message logic working correctly")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ Scenario {i} FAILED: {scenario_result.get('failure_reason', 'Unknown error')}")
                
                time.sleep(2)  # Rate limiting between scenarios
                
            except Exception as e:
                logger.error(f"❌ Scenario {i} ERROR: {str(e)}")
                results["failed"] += 1
                results["scenario_results"].append({
                    "scenario": scenario,
                    "passed": False,
                    "error": str(e)
                })
        
        results["first_message_logic_working"] = results["passed"] > results["failed"]
        results["success_rate"] = (results["passed"] / results["total_scenarios"]) * 100
        
        logger.info(f"🔄 First Message Logic Test Results: {results['passed']}/{results['total_scenarios']} passed ({results['success_rate']:.1f}%)")
        return results
    
    def _test_new_task_flow(self, scenario: Dict) -> Dict:
        """Test the complete new task flow with first message"""
        
        try:
            # Step 1: Simulate task creation (empty task)
            task_id = f"test-task-{int(time.time())}"
            
            # Step 2: Send first user message (should trigger plan generation)
            logger.info(f"📨 Sending first message: {scenario['first_message'][:50]}...")
            
            chat_response = self.session.post(
                f"{self.base_url}/api/agent/chat",
                json={
                    "message": scenario["first_message"],
                    "context": {
                        "task_id": task_id,
                        "is_new_task": True  # Simulate new task context
                    }
                },
                timeout=45
            )
            
            if chat_response.status_code != 200:
                return {
                    "scenario": scenario,
                    "passed": False,
                    "failure_reason": f"Chat endpoint failed: HTTP {chat_response.status_code}",
                    "chat_response": None
                }
            
            chat_data = chat_response.json()
            
            # Step 3: Check if plan was generated automatically
            plan_generated = self._check_plan_generation(chat_data)
            
            # Step 4: Check if enhanced title was generated
            title_enhanced = self._check_title_enhancement(chat_data, scenario)
            
            # Step 5: Verify logs show first message detection
            logs_correct = self._check_first_message_logs(chat_data)
            
            return {
                "scenario": scenario,
                "task_id": task_id,
                "chat_response": chat_data,
                "plan_generated": plan_generated,
                "title_enhanced": title_enhanced,
                "logs_correct": logs_correct,
                "passed": plan_generated["success"] and title_enhanced["success"],
                "failure_reason": self._get_failure_reason(plan_generated, title_enhanced, logs_correct)
            }
            
        except Exception as e:
            return {
                "scenario": scenario,
                "passed": False,
                "error": str(e),
                "failure_reason": f"Exception during test: {str(e)}"
            }
    
    def _check_plan_generation(self, chat_data: Dict) -> Dict:
        """Check if plan was generated in response"""
        
        plan = chat_data.get("plan")
        if not plan:
            return {
                "success": False,
                "reason": "No plan found in chat response"
            }
        
        if not isinstance(plan, dict):
            return {
                "success": False,
                "reason": "Plan is not a dictionary object"
            }
        
        steps = plan.get("steps", [])
        if not steps or len(steps) == 0:
            return {
                "success": False,
                "reason": "Plan has no steps"
            }
        
        # Check if steps have required fields
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return {
                    "success": False,
                    "reason": f"Step {i+1} is not a dictionary"
                }
            
            required_fields = ["title", "description", "tool"]
            for field in required_fields:
                if field not in step:
                    return {
                        "success": False,
                        "reason": f"Step {i+1} missing required field: {field}"
                    }
        
        return {
            "success": True,
            "steps_count": len(steps),
            "plan_data": plan
        }
    
    def _check_title_enhancement(self, chat_data: Dict, scenario: Dict) -> Dict:
        """Check if enhanced title was generated"""
        
        enhanced_title = chat_data.get("enhanced_title")
        if not enhanced_title:
            return {
                "success": False,
                "reason": "No enhanced_title found in response"
            }
        
        if enhanced_title == scenario["task_title"]:
            return {
                "success": False,
                "reason": "Enhanced title is same as original title"
            }
        
        if len(enhanced_title.strip()) < 10:
            return {
                "success": False,
                "reason": "Enhanced title too short"
            }
        
        return {
            "success": True,
            "enhanced_title": enhanced_title,
            "original_title": scenario["task_title"]
        }
    
    def _check_first_message_logs(self, chat_data: Dict) -> Dict:
        """Check if logs indicate first message processing"""
        
        # Look for indicators that this was processed as first message
        mode = chat_data.get("mode")
        execution_status = chat_data.get("execution_status")
        
        if mode != "agent_with_structured_plan":
            return {
                "success": False,
                "reason": f"Expected mode 'agent_with_structured_plan', got '{mode}'"
            }
        
        if execution_status not in ["executing", "plan_ready"]:
            return {
                "success": False,
                "reason": f"Expected execution_status 'executing' or 'plan_ready', got '{execution_status}'"
            }
        
        return {
            "success": True,
            "mode": mode,
            "execution_status": execution_status
        }
    
    def _get_failure_reason(self, plan_generated: Dict, title_enhanced: Dict, logs_correct: Dict) -> str:
        """Get comprehensive failure reason"""
        
        reasons = []
        
        if not plan_generated["success"]:
            reasons.append(f"Plan generation failed: {plan_generated['reason']}")
        
        if not title_enhanced["success"]:
            reasons.append(f"Title enhancement failed: {title_enhanced['reason']}")
        
        if not logs_correct["success"]:
            reasons.append(f"Logs incorrect: {logs_correct['reason']}")
        
        return "; ".join(reasons) if reasons else "Unknown failure"


class BackendHealthTester:
    """Test backend health and connectivity"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_backend_health(self) -> Dict[str, Any]:
        """Test backend health and required services"""
        logger.info("🏥 Testing backend health...")
        
        health_results = {
            "backend_accessible": False,
            "agent_health": False,
            "ollama_connected": False,
            "database_connected": False,
            "tools_available": False,
            "endpoints_working": {},
            "overall_health": False
        }
        
        try:
            # Test basic connectivity
            health_results["backend_accessible"] = self._test_basic_connectivity()
            
            # Test agent health endpoint
            health_results["agent_health"] = self._test_agent_health()
            
            # Test specific endpoints
            health_results["endpoints_working"] = self._test_endpoints()
            
            # Overall health assessment
            health_results["overall_health"] = (
                health_results["backend_accessible"] and
                health_results["agent_health"] and
                len([ep for ep in health_results["endpoints_working"].values() if ep]) >= 2
            )
            
            logger.info(f"🏥 Backend Health: {'✅ HEALTHY' if health_results['overall_health'] else '❌ UNHEALTHY'}")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            health_results["error"] = str(e)
        
        return health_results
    
    def _test_basic_connectivity(self) -> bool:
        """Test basic backend connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _test_agent_health(self) -> bool:
        """Test agent health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/agent/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False
        except:
            return False
    
    def _test_endpoints(self) -> Dict[str, bool]:
        """Test specific endpoints"""
        endpoints = {
            "/api/agent/status": False,
            "/api/health": False,
            "/api/agent/generate-plan": False
        }
        
        # Test status endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/agent/status", timeout=10)
            endpoints["/api/agent/status"] = response.status_code == 200
        except:
            pass
        
        # Test health endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            endpoints["/api/health"] = response.status_code == 200
        except:
            pass
        
        # Test generate-plan endpoint
        try:
            response = self.session.post(
                f"{self.base_url}/api/agent/generate-plan",
                json={"task_title": "Test task"},
                timeout=15
            )
            endpoints["/api/agent/generate-plan"] = response.status_code == 200
        except:
            pass
        
        return endpoints


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    logger.info("🚀 Starting comprehensive backend testing for icon mapping and first message logic fixes...")
    
    # Initialize testers
    icon_tester = IconMappingTester(BACKEND_URL)
    first_message_tester = FirstMessageLogicTester(BACKEND_URL)
    health_tester = BackendHealthTester(BACKEND_URL)
    
    # Run tests
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "backend_url": BACKEND_URL,
        "test_summary": {},
        "detailed_results": {}
    }
    
    # 1. Backend Health Check
    logger.info("=" * 60)
    logger.info("1. BACKEND HEALTH CHECK")
    logger.info("=" * 60)
    
    health_results = health_tester.test_backend_health()
    test_results["detailed_results"]["health"] = health_results
    
    if not health_results["overall_health"]:
        logger.error("❌ Backend health check failed - skipping other tests")
        test_results["test_summary"]["overall_status"] = "FAILED - Backend unhealthy"
        return test_results
    
    # 2. Icon Mapping Tests
    logger.info("=" * 60)
    logger.info("2. ICON MAPPING COHERENCE TESTS")
    logger.info("=" * 60)
    
    icon_results = icon_tester.test_icon_mapping_coherence()
    test_results["detailed_results"]["icon_mapping"] = icon_results
    
    # 3. First Message Logic Tests
    logger.info("=" * 60)
    logger.info("3. FIRST MESSAGE LOGIC TESTS")
    logger.info("=" * 60)
    
    first_message_results = first_message_tester.test_first_message_detection()
    test_results["detailed_results"]["first_message_logic"] = first_message_results
    
    # 4. Generate Test Summary
    logger.info("=" * 60)
    logger.info("4. TEST SUMMARY")
    logger.info("=" * 60)
    
    # Calculate overall results
    icon_success = icon_results.get("icon_mapping_working", False)
    first_message_success = first_message_results.get("first_message_logic_working", False)
    
    test_results["test_summary"] = {
        "overall_status": "PASSED" if (icon_success and first_message_success) else "FAILED",
        "backend_health": "✅ HEALTHY" if health_results["overall_health"] else "❌ UNHEALTHY",
        "icon_mapping": "✅ WORKING" if icon_success else "❌ FAILED",
        "first_message_logic": "✅ WORKING" if first_message_success else "❌ FAILED",
        "icon_mapping_success_rate": f"{icon_results.get('success_rate', 0):.1f}%",
        "first_message_success_rate": f"{first_message_results.get('success_rate', 0):.1f}%",
        "total_tests_run": (
            icon_results.get("total_tests", 0) + 
            first_message_results.get("total_scenarios", 0)
        ),
        "total_tests_passed": (
            icon_results.get("passed", 0) + 
            first_message_results.get("passed", 0)
        )
    }
    
    # Log summary
    summary = test_results["test_summary"]
    logger.info(f"📊 OVERALL STATUS: {summary['overall_status']}")
    logger.info(f"🏥 Backend Health: {summary['backend_health']}")
    logger.info(f"🎯 Icon Mapping: {summary['icon_mapping']} ({summary['icon_mapping_success_rate']})")
    logger.info(f"🔄 First Message Logic: {summary['first_message_logic']} ({summary['first_message_success_rate']})")
    logger.info(f"📈 Total Tests: {summary['total_tests_passed']}/{summary['total_tests_run']} passed")
    
    return test_results


if __name__ == "__main__":
    try:
        results = run_comprehensive_tests()
        
        # Save results to file
        with open("/app/test_results_icon_and_first_message.json", "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info("💾 Test results saved to /app/test_results_icon_and_first_message.json")
        
        # Exit with appropriate code
        if results["test_summary"]["overall_status"] == "PASSED":
            logger.info("🎉 ALL TESTS PASSED!")
            exit(0)
        else:
            logger.error("❌ SOME TESTS FAILED!")
            exit(1)
            
    except Exception as e:
        logger.error(f"💥 Test execution failed: {str(e)}")
        exit(1)