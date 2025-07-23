#!/usr/bin/env python3
"""
NUEVA TAREA FLOW BACKEND TESTING
Testing the backend functionality for the Nueva Tarea flow fixes:

1. User Message Processing: Backend should properly process user messages and reflect them in plans
2. Plan Generation Process: Backend should generate plans correctly with enhanced message processing logic
3. Chat Flow Verification: Backend should maintain proper message flow and responses

Focus: Backend API endpoints and their responses for Nueva Tarea flow
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
BACKEND_URL = "https://c98456b8-1d6f-431b-a23f-52aa625cdad4.preview.emergentagent.com"

class NuevaTareaBackendTester:
    """Test Nueva Tarea flow backend functionality"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def test_nueva_tarea_flow(self) -> Dict[str, Any]:
        """Test complete Nueva Tarea flow from backend perspective"""
        logger.info("🆕 Testing Nueva Tarea flow backend functionality...")
        
        test_scenarios = [
            {
                "name": "Market Analysis Task",
                "message": "Crear un análisis de mercado para productos de software en 2025",
                "expected_plan_steps": 4,
                "expected_enhanced_title": True
            },
            {
                "name": "AI Presentation Task", 
                "message": "Crear una presentación sobre inteligencia artificial",
                "expected_plan_steps": 4,
                "expected_enhanced_title": True
            },
            {
                "name": "Marketing Strategy Task",
                "message": "Desarrollar una estrategia de marketing digital para una startup",
                "expected_plan_steps": 4,
                "expected_enhanced_title": True
            }
        ]
        
        results = {
            "total_scenarios": len(test_scenarios),
            "passed": 0,
            "failed": 0,
            "scenario_results": [],
            "nueva_tarea_backend_working": False
        }
        
        for i, scenario in enumerate(test_scenarios, 1):
            logger.info(f"🧪 Testing scenario {i}/{len(test_scenarios)}: {scenario['name']}")
            
            try:
                # Test the complete Nueva Tarea backend flow
                scenario_result = self._test_scenario_backend_flow(scenario)
                results["scenario_results"].append(scenario_result)
                
                if scenario_result["passed"]:
                    results["passed"] += 1
                    logger.info(f"✅ Scenario {i} PASSED: {scenario['name']}")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ Scenario {i} FAILED: {scenario_result.get('failure_reason', 'Unknown error')}")
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Scenario {i} ERROR: {str(e)}")
                results["failed"] += 1
                results["scenario_results"].append({
                    "scenario": scenario,
                    "passed": False,
                    "error": str(e)
                })
        
        results["nueva_tarea_backend_working"] = results["passed"] > results["failed"]
        results["success_rate"] = (results["passed"] / results["total_scenarios"]) * 100
        
        logger.info(f"🆕 Nueva Tarea Backend Test Results: {results['passed']}/{results['total_scenarios']} passed ({results['success_rate']:.1f}%)")
        return results
    
    def _test_scenario_backend_flow(self, scenario: Dict) -> Dict:
        """Test complete backend flow for a Nueva Tarea scenario"""
        
        try:
            # Step 1: Test chat endpoint (simulates Nueva Tarea message submission)
            logger.info(f"📨 Testing chat endpoint with message: {scenario['message'][:50]}...")
            
            chat_response = self.session.post(
                f"{self.base_url}/api/agent/chat",
                json={
                    "message": scenario["message"],
                    "context": {
                        "is_nueva_tarea": True,  # Simulate Nueva Tarea context
                        "task_id": f"nueva-tarea-{int(time.time())}"
                    }
                },
                timeout=45
            )
            
            if chat_response.status_code != 200:
                return {
                    "scenario": scenario,
                    "passed": False,
                    "failure_reason": f"Chat endpoint failed: HTTP {chat_response.status_code} - {chat_response.text}",
                    "chat_response": None
                }
            
            chat_data = chat_response.json()
            
            # Step 2: Verify user message processing
            message_processing = self._verify_message_processing(chat_data, scenario)
            
            # Step 3: Verify plan generation
            plan_generation = self._verify_plan_generation(chat_data, scenario)
            
            # Step 4: Verify enhanced title generation
            title_enhancement = self._verify_title_enhancement(chat_data, scenario)
            
            # Step 5: Verify response structure for frontend
            response_structure = self._verify_response_structure(chat_data)
            
            # Step 6: Test generate-plan endpoint separately
            plan_endpoint_test = self._test_generate_plan_endpoint(scenario)
            
            return {
                "scenario": scenario,
                "chat_response": chat_data,
                "message_processing": message_processing,
                "plan_generation": plan_generation,
                "title_enhancement": title_enhancement,
                "response_structure": response_structure,
                "plan_endpoint_test": plan_endpoint_test,
                "passed": (
                    message_processing["success"] and
                    plan_generation["success"] and
                    title_enhancement["success"] and
                    response_structure["success"]
                ),
                "failure_reason": self._get_failure_reason(
                    message_processing, plan_generation, title_enhancement, response_structure
                )
            }
            
        except Exception as e:
            return {
                "scenario": scenario,
                "passed": False,
                "error": str(e),
                "failure_reason": f"Exception during backend test: {str(e)}"
            }
    
    def _verify_message_processing(self, chat_data: Dict, scenario: Dict) -> Dict:
        """Verify that user message was properly processed by backend"""
        
        user_message = scenario["message"]
        
        # Check if the backend processed the message correctly by looking at the generated plan
        plan = chat_data.get("plan", {})
        if not isinstance(plan, dict):
            return {
                "success": False,
                "reason": "No plan generated - message not processed"
            }
        
        # Check if enhanced title reflects the user's request
        enhanced_title = chat_data.get("enhanced_title", "")
        title_reflects_request = False
        
        # Extract key words from user message
        user_keywords = user_message.lower().split()
        title_keywords = enhanced_title.lower().split()
        
        # Check if at least 1 key word from user message appears in enhanced title
        matching_keywords = [word for word in user_keywords if word in title_keywords and len(word) > 3]
        if len(matching_keywords) >= 1:
            title_reflects_request = True
        
        # Check if plan steps are relevant to user request
        steps = plan.get("steps", [])
        steps_relevant = False
        if steps:
            # Check if step descriptions contain relevant keywords
            all_step_text = " ".join([step.get("description", "") + " " + step.get("title", "") for step in steps]).lower()
            relevant_keywords = [word for word in user_keywords if word in all_step_text and len(word) > 3]
            if len(relevant_keywords) >= 2:
                steps_relevant = True
        
        # Check if task_type matches user intent
        task_type = plan.get("task_type", "").lower()
        task_type_relevant = any(word in task_type for word in user_keywords if len(word) > 3)
        
        message_processed = title_reflects_request and steps_relevant
        
        return {
            "success": message_processed,
            "title_reflects_request": title_reflects_request,
            "steps_relevant": steps_relevant,
            "task_type_relevant": task_type_relevant,
            "matching_keywords": matching_keywords,
            "enhanced_title": enhanced_title,
            "reason": "User message properly processed and reflected in plan" if message_processed else "User message not properly reflected in generated plan"
        }
    
    def _verify_plan_generation(self, chat_data: Dict, scenario: Dict) -> Dict:
        """Verify that plan is generated correctly"""
        
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
        
        # Verify minimum expected steps
        expected_steps = scenario.get("expected_plan_steps", 3)
        if len(steps) < expected_steps:
            return {
                "success": False,
                "reason": f"Plan has {len(steps)} steps, expected at least {expected_steps}"
            }
        
        # Verify step structure
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return {
                    "success": False,
                    "reason": f"Step {i+1} is not a dictionary"
                }
            
            required_fields = ["title", "description"]
            for field in required_fields:
                if field not in step or not step[field]:
                    return {
                        "success": False,
                        "reason": f"Step {i+1} missing or empty required field: {field}"
                    }
        
        return {
            "success": True,
            "steps_count": len(steps),
            "plan_title": plan.get("title", ""),
            "plan_description": plan.get("description", "")
        }
    
    def _verify_title_enhancement(self, chat_data: Dict, scenario: Dict) -> Dict:
        """Verify that enhanced title is generated"""
        
        enhanced_title = chat_data.get("enhanced_title")
        if not enhanced_title:
            # Check in plan object
            plan = chat_data.get("plan", {})
            enhanced_title = plan.get("title") if isinstance(plan, dict) else None
        
        if not enhanced_title:
            return {
                "success": False,
                "reason": "No enhanced title found in response"
            }
        
        if len(enhanced_title.strip()) < 10:
            return {
                "success": False,
                "reason": "Enhanced title too short"
            }
        
        # Check if title is actually enhanced (different from generic "Tarea 1")
        if enhanced_title.lower() in ["tarea 1", "nueva tarea", "task 1"]:
            return {
                "success": False,
                "reason": "Title not properly enhanced (still generic)"
            }
        
        return {
            "success": True,
            "enhanced_title": enhanced_title,
            "title_length": len(enhanced_title)
        }
    
    def _verify_response_structure(self, chat_data: Dict) -> Dict:
        """Verify that response has proper structure for frontend"""
        
        required_fields = ["response", "timestamp"]
        optional_fields = ["plan", "enhanced_title", "suggested_icon", "task_id", "memory_used"]
        
        missing_required = []
        for field in required_fields:
            if field not in chat_data:
                missing_required.append(field)
        
        if missing_required:
            return {
                "success": False,
                "reason": f"Missing required fields: {', '.join(missing_required)}"
            }
        
        # Check optional fields presence
        present_optional = []
        for field in optional_fields:
            if field in chat_data:
                present_optional.append(field)
        
        return {
            "success": True,
            "required_fields_present": required_fields,
            "optional_fields_present": present_optional,
            "response_keys": list(chat_data.keys())
        }
    
    def _test_generate_plan_endpoint(self, scenario: Dict) -> Dict:
        """Test the generate-plan endpoint separately"""
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/agent/generate-plan",
                json={"task_title": scenario["message"]},
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "reason": f"Generate-plan endpoint failed: HTTP {response.status_code}",
                    "response_data": None
                }
            
            data = response.json()
            
            # Check if plan is in the response (could be direct array or nested)
            plan_data = data.get("plan", data)  # Sometimes plan is direct, sometimes nested
            
            if isinstance(plan_data, list):
                steps = plan_data
            elif isinstance(plan_data, dict):
                steps = plan_data.get("steps", [])
            else:
                return {
                    "success": False,
                    "reason": "No valid plan structure in generate-plan response",
                    "response_data": data
                }
            
            if len(steps) < 3:
                return {
                    "success": False,
                    "reason": f"Generate-plan returned {len(steps)} steps, expected at least 3",
                    "response_data": data
                }
            
            return {
                "success": True,
                "steps_count": len(steps),
                "has_enhanced_title": "enhanced_title" in data,
                "has_suggested_icon": "suggested_icon" in data,
                "response_data": data
            }
            
        except Exception as e:
            return {
                "success": False,
                "reason": f"Exception testing generate-plan endpoint: {str(e)}",
                "error": str(e)
            }
    
    def _get_failure_reason(self, message_processing: Dict, plan_generation: Dict, 
                           title_enhancement: Dict, response_structure: Dict) -> str:
        """Get comprehensive failure reason"""
        
        reasons = []
        
        if not message_processing["success"]:
            reasons.append(f"Message processing: {message_processing['reason']}")
        
        if not plan_generation["success"]:
            reasons.append(f"Plan generation: {plan_generation['reason']}")
        
        if not title_enhancement["success"]:
            reasons.append(f"Title enhancement: {title_enhancement['reason']}")
        
        if not response_structure["success"]:
            reasons.append(f"Response structure: {response_structure['reason']}")
        
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
            working_endpoints = len([ep for ep in health_results["endpoints_working"].values() if ep])
            health_results["overall_health"] = (
                health_results["backend_accessible"] and
                working_endpoints >= 2
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
            "/api/agent/chat": False,
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
        
        # Test chat endpoint
        try:
            response = self.session.post(
                f"{self.base_url}/api/agent/chat",
                json={"message": "Test message"},
                timeout=15
            )
            endpoints["/api/agent/chat"] = response.status_code == 200
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


def run_nueva_tarea_tests():
    """Run Nueva Tarea backend tests"""
    logger.info("🚀 Starting Nueva Tarea backend testing...")
    
    # Initialize testers
    nueva_tarea_tester = NuevaTareaBackendTester(BACKEND_URL)
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
        logger.error("❌ Backend health check failed - skipping Nueva Tarea tests")
        test_results["test_summary"]["overall_status"] = "FAILED - Backend unhealthy"
        return test_results
    
    # 2. Nueva Tarea Flow Tests
    logger.info("=" * 60)
    logger.info("2. NUEVA TAREA FLOW BACKEND TESTS")
    logger.info("=" * 60)
    
    nueva_tarea_results = nueva_tarea_tester.test_nueva_tarea_flow()
    test_results["detailed_results"]["nueva_tarea_flow"] = nueva_tarea_results
    
    # 3. Generate Test Summary
    logger.info("=" * 60)
    logger.info("3. TEST SUMMARY")
    logger.info("=" * 60)
    
    # Calculate overall results
    nueva_tarea_success = nueva_tarea_results.get("nueva_tarea_backend_working", False)
    
    test_results["test_summary"] = {
        "overall_status": "PASSED" if nueva_tarea_success else "FAILED",
        "backend_health": "✅ HEALTHY" if health_results["overall_health"] else "❌ UNHEALTHY",
        "nueva_tarea_flow": "✅ WORKING" if nueva_tarea_success else "❌ FAILED",
        "nueva_tarea_success_rate": f"{nueva_tarea_results.get('success_rate', 0):.1f}%",
        "total_scenarios_run": nueva_tarea_results.get("total_scenarios", 0),
        "total_scenarios_passed": nueva_tarea_results.get("passed", 0)
    }
    
    # Log summary
    summary = test_results["test_summary"]
    logger.info(f"📊 OVERALL STATUS: {summary['overall_status']}")
    logger.info(f"🏥 Backend Health: {summary['backend_health']}")
    logger.info(f"🆕 Nueva Tarea Flow: {summary['nueva_tarea_flow']} ({summary['nueva_tarea_success_rate']})")
    logger.info(f"📈 Total Scenarios: {summary['total_scenarios_passed']}/{summary['total_scenarios_run']} passed")
    
    return test_results


if __name__ == "__main__":
    try:
        results = run_nueva_tarea_tests()
        
        # Save results to file
        with open("/app/nueva_tarea_test_results.json", "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info("💾 Test results saved to /app/nueva_tarea_test_results.json")
        
        # Exit with appropriate code
        if results["test_summary"]["overall_status"] == "PASSED":
            logger.info("🎉 NUEVA TAREA BACKEND TESTS PASSED!")
            exit(0)
        else:
            logger.error("❌ NUEVA TAREA BACKEND TESTS FAILED!")
            exit(1)
            
    except Exception as e:
        logger.error(f"💥 Test execution failed: {str(e)}")
        exit(1)