#!/usr/bin/env python3
"""
Enhanced Mitosis Backend Comprehensive Test Script
Testing the enhanced Mitosis backend with autonomous capabilities

This script tests:
1. Autonomous Functions - new endpoints like /api/agent/initialize-task, /api/agent/chat, /api/agent/status, /api/health
2. Autonomous Execution - testing that messages like "Crear un plan de marketing" trigger autonomous execution
3. Terminal Output - verify output appears in backend logs with clear formatting
4. Compatibility - existing endpoints still work
5. WebSocket - verify WebSocket connections are available
"""

import requests
import json
import sys
import uuid
import time
import os
from datetime import datetime
from pathlib import Path

# Configuration - Use external URL from frontend .env
backend_url = "http://localhost:8001"
try:
    with open('/app/frontend/.env', 'r') as env_file:
        for line in env_file:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.strip().split('=', 1)[1].strip('"\'')
                break
except Exception as e:
    print(f"Error reading .env file: {e}")

BASE_URL = backend_url
print(f"🔗 Testing Enhanced Mitosis Backend at: {BASE_URL}")

# Test results tracking
test_results = {
    "timestamp": datetime.now().isoformat(),
    "backend_url": BASE_URL,
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
}

def run_test(name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, timeout=30):
    """Run a test against an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    test_results["summary"]["total"] += 1
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {name}")
    print(f"🔗 URL: {url}")
    print(f"📋 METHOD: {method}")
    if data:
        print(f"📤 DATA: {json.dumps(data, indent=2)}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        status_code = response.status_code
        print(f"📊 STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"📥 RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"📥 RESPONSE: {response_data}")
        
        # Check status code
        status_ok = status_code == expected_status
        
        # Check expected keys
        keys_ok = True
        missing_keys = []
        if expected_keys and status_ok and isinstance(response_data, dict):
            for key in expected_keys:
                if key not in response_data:
                    keys_ok = False
                    missing_keys.append(key)
        
        # Determine test result
        passed = status_ok and keys_ok
        
        # Update test results
        test_results["tests"].append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "expected_status": expected_status,
            "passed": passed,
            "missing_keys": missing_keys if not keys_ok else None,
            "response_data": response_data if passed else None
        })
        
        if passed:
            test_results["summary"]["passed"] += 1
            print(f"✅ RESULT: PASSED")
        else:
            test_results["summary"]["failed"] += 1
            print(f"❌ RESULT: FAILED")
            if not status_ok:
                print(f"  - Expected status {expected_status}, got {status_code}")
            if not keys_ok:
                print(f"  - Missing expected keys: {', '.join(missing_keys)}")
        
        return passed, response_data
    
    except Exception as e:
        test_results["summary"]["failed"] += 1
        test_results["tests"].append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "error": str(e),
            "passed": False
        })
        print(f"💥 ERROR: {str(e)}")
        print(f"❌ RESULT: FAILED (Exception)")
        return False, None

def test_autonomous_functions():
    """Test the new autonomous function endpoints"""
    print(f"\n🤖 TESTING AUTONOMOUS FUNCTIONS")
    
    # Test 1: Enhanced Health Check
    passed, health_data = run_test(
        "Enhanced Health Check (/api/health)",
        "/api/health",
        expected_keys=["status", "timestamp", "services"]
    )
    
    # Check if enhanced: true is present
    if passed and isinstance(health_data, dict):
        enhanced = health_data.get("enhanced", False)
        if enhanced:
            print("✅ Enhanced backend detected (enhanced: true)")
        else:
            print("⚠️ Enhanced flag not found in health response")
    
    # Test 2: Agent Status Endpoint
    passed, status_data = run_test(
        "Agent Status (/api/agent/status)",
        "/api/agent/status",
        expected_keys=["status", "capabilities"]
    )
    
    # Test 3: Agent Health Endpoint
    passed, agent_health_data = run_test(
        "Agent Health (/api/agent/health)",
        "/api/agent/health",
        expected_keys=["status"]
    )
    
    # Test 4: Initialize Task Endpoint (if available)
    task_id = f"test-autonomous-{uuid.uuid4()}"
    init_data = {
        "task_id": task_id,
        "message": "Crear un plan de marketing digital",
        "autonomous": True
    }
    
    passed, init_response = run_test(
        "Initialize Autonomous Task (/api/agent/initialize-task)",
        "/api/agent/initialize-task",
        method="POST",
        data=init_data,
        expected_status=200
    )
    
    return task_id

def test_autonomous_execution(task_id):
    """Test autonomous execution with marketing plan creation"""
    print(f"\n🚀 TESTING AUTONOMOUS EXECUTION")
    
    # Test autonomous chat with plan generation trigger
    autonomous_message = "Crear un plan de marketing digital completo para una startup de tecnología"
    
    chat_data = {
        "message": autonomous_message,
        "context": {
            "task_id": task_id,
            "autonomous": True,
            "previous_messages": []
        }
    }
    
    print(f"🎯 Testing autonomous execution with message: '{autonomous_message}'")
    
    passed, chat_response = run_test(
        "Autonomous Chat Execution (/api/agent/chat)",
        "/api/agent/chat",
        method="POST",
        data=chat_data,
        expected_keys=["response", "task_id"],
        timeout=60  # Longer timeout for autonomous execution
    )
    
    if passed and isinstance(chat_response, dict):
        # Check for autonomous execution indicators
        response_text = chat_response.get("response", "")
        task_id_response = chat_response.get("task_id", "")
        
        # Look for plan generation indicators
        plan_indicators = ["plan", "paso", "estrategia", "marketing", "acción"]
        plan_detected = any(indicator.lower() in response_text.lower() for indicator in plan_indicators)
        
        if plan_detected:
            print("✅ Plan generation detected in response")
        else:
            print("⚠️ No clear plan generation detected")
        
        if task_id_response:
            print(f"✅ Task ID returned: {task_id_response}")
        else:
            print("⚠️ No task ID in response")
        
        # Check for memory usage
        memory_used = chat_response.get("memory_used", False)
        if memory_used:
            print("✅ Memory system integration detected")
        else:
            print("⚠️ Memory system not detected")
    
    return passed, chat_response

def test_websocket_availability():
    """Test WebSocket endpoint availability"""
    print(f"\n🔌 TESTING WEBSOCKET AVAILABILITY")
    
    # Test WebSocket endpoint (usually socket.io)
    websocket_endpoints = [
        "/socket.io/",
        "/ws",
        "/websocket"
    ]
    
    websocket_available = False
    
    for endpoint in websocket_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code in [200, 400, 426]:  # 426 = Upgrade Required (WebSocket)
                print(f"✅ WebSocket endpoint found: {endpoint} (Status: {response.status_code})")
                websocket_available = True
                break
            else:
                print(f"⚠️ Endpoint {endpoint} returned status: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Endpoint {endpoint} not accessible: {str(e)}")
    
    if not websocket_available:
        print("❌ No WebSocket endpoints found")
    
    return websocket_available

def test_compatibility():
    """Test that existing endpoints still work"""
    print(f"\n🔄 TESTING BACKWARD COMPATIBILITY")
    
    # Test existing endpoints
    compatibility_tests = [
        ("Tools List", "/api/agent/tools", "GET", None, ["tools"]),
        ("Models List", "/api/agent/models", "GET", None, ["models"]),
    ]
    
    compatibility_passed = 0
    total_compatibility_tests = len(compatibility_tests)
    
    for test_name, endpoint, method, data, expected_keys in compatibility_tests:
        passed, _ = run_test(test_name, endpoint, method, data, expected_keys=expected_keys)
        if passed:
            compatibility_passed += 1
    
    compatibility_rate = (compatibility_passed / total_compatibility_tests) * 100
    print(f"📊 Compatibility Rate: {compatibility_rate:.1f}% ({compatibility_passed}/{total_compatibility_tests})")
    
    return compatibility_rate >= 75  # 75% compatibility threshold

def test_terminal_output_monitoring():
    """Test that backend produces terminal output"""
    print(f"\n📺 TESTING TERMINAL OUTPUT MONITORING")
    
    # This test checks if the backend is configured to produce terminal output
    # We'll look for log files or check if the backend responds with execution details
    
    test_message = "Realizar análisis de mercado"
    
    chat_data = {
        "message": test_message,
        "context": {
            "task_id": f"terminal-test-{uuid.uuid4()}",
            "monitor_output": True
        }
    }
    
    passed, response = run_test(
        "Terminal Output Test",
        "/api/agent/chat",
        method="POST",
        data=chat_data,
        timeout=30
    )
    
    if passed and isinstance(response, dict):
        # Check for execution details that would appear in terminal
        execution_indicators = [
            "ejecutando", "procesando", "iniciando", "completado",
            "step", "paso", "progress", "progreso"
        ]
        
        response_text = str(response).lower()
        terminal_output_detected = any(indicator in response_text for indicator in execution_indicators)
        
        if terminal_output_detected:
            print("✅ Terminal output indicators detected in response")
        else:
            print("⚠️ No clear terminal output indicators found")
        
        return terminal_output_detected
    
    return False

def print_comprehensive_summary():
    """Print comprehensive test summary"""
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    
    print("\n" + "="*80)
    print(f"🎯 ENHANCED MITOSIS BACKEND TEST SUMMARY")
    print(f"⏰ Timestamp: {test_results['timestamp']}")
    print(f"🔗 Backend URL: {test_results['backend_url']}")
    print(f"📊 Total tests: {total}")
    print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
    print("="*80)
    
    # Categorize results
    autonomous_tests = []
    compatibility_tests = []
    websocket_tests = []
    other_tests = []
    
    for test in test_results["tests"]:
        test_name = test["name"].lower()
        if "autonomous" in test_name or "initialize" in test_name:
            autonomous_tests.append(test)
        elif "compatibility" in test_name or "tools" in test_name or "models" in test_name:
            compatibility_tests.append(test)
        elif "websocket" in test_name or "socket" in test_name:
            websocket_tests.append(test)
        else:
            other_tests.append(test)
    
    # Print categorized results
    categories = [
        ("🤖 AUTONOMOUS FUNCTIONS", autonomous_tests),
        ("🔄 COMPATIBILITY", compatibility_tests),
        ("🔌 WEBSOCKET", websocket_tests),
        ("🔧 OTHER TESTS", other_tests)
    ]
    
    for category_name, category_tests in categories:
        if category_tests:
            print(f"\n{category_name}:")
            for test in category_tests:
                status = "✅" if test["passed"] else "❌"
                print(f"  {status} {test['name']}")
                if not test["passed"] and "error" in test:
                    print(f"      Error: {test['error']}")
    
    # Print failed tests details
    if failed > 0:
        print(f"\n❌ FAILED TESTS DETAILS:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"- {test['name']} ({test['endpoint']})")
                if "error" in test:
                    print(f"  Error: {test['error']}")
                elif "status_code" in test and "expected_status" in test:
                    if test["status_code"] != test["expected_status"]:
                        print(f"  Expected status {test['expected_status']}, got {test['status_code']}")
                if "missing_keys" in test and test["missing_keys"]:
                    print(f"  Missing keys: {', '.join(test['missing_keys'])}")
    
    # Overall assessment
    success_rate = (passed / total) * 100
    print(f"\n🎯 OVERALL ASSESSMENT:")
    
    if success_rate >= 90:
        print(f"🟢 EXCELLENT: {success_rate:.1f}% success rate - Enhanced backend is working excellently")
    elif success_rate >= 75:
        print(f"🟡 GOOD: {success_rate:.1f}% success rate - Enhanced backend is mostly functional")
    elif success_rate >= 50:
        print(f"🟠 FAIR: {success_rate:.1f}% success rate - Enhanced backend has some issues")
    else:
        print(f"🔴 POOR: {success_rate:.1f}% success rate - Enhanced backend needs significant fixes")
    
    return success_rate

def main():
    """Main test execution"""
    print("🚀 Starting Enhanced Mitosis Backend Comprehensive Testing")
    print(f"🔗 Backend URL: {BASE_URL}")
    print(f"⏰ Test started at: {datetime.now().isoformat()}")
    
    try:
        # Test 1: Autonomous Functions
        print("\n" + "="*80)
        print("🤖 PHASE 1: TESTING AUTONOMOUS FUNCTIONS")
        print("="*80)
        task_id = test_autonomous_functions()
        
        # Test 2: Autonomous Execution
        print("\n" + "="*80)
        print("🚀 PHASE 2: TESTING AUTONOMOUS EXECUTION")
        print("="*80)
        execution_passed, execution_response = test_autonomous_execution(task_id)
        
        # Test 3: WebSocket Availability
        print("\n" + "="*80)
        print("🔌 PHASE 3: TESTING WEBSOCKET AVAILABILITY")
        print("="*80)
        websocket_available = test_websocket_availability()
        
        # Test 4: Compatibility
        print("\n" + "="*80)
        print("🔄 PHASE 4: TESTING BACKWARD COMPATIBILITY")
        print("="*80)
        compatibility_ok = test_compatibility()
        
        # Test 5: Terminal Output
        print("\n" + "="*80)
        print("📺 PHASE 5: TESTING TERMINAL OUTPUT")
        print("="*80)
        terminal_output_ok = test_terminal_output_monitoring()
        
        # Final Summary
        success_rate = print_comprehensive_summary()
        
        # Specific findings for the review request
        print(f"\n🎯 SPECIFIC REVIEW REQUEST FINDINGS:")
        print(f"✅ Autonomous Functions: {'WORKING' if any(t['passed'] and 'autonomous' in t['name'].lower() for t in test_results['tests']) else 'NEEDS WORK'}")
        print(f"✅ Autonomous Execution: {'WORKING' if execution_passed else 'NEEDS WORK'}")
        print(f"✅ Terminal Output: {'DETECTED' if terminal_output_ok else 'NOT DETECTED'}")
        print(f"✅ Compatibility: {'GOOD' if compatibility_ok else 'ISSUES FOUND'}")
        print(f"✅ WebSocket: {'AVAILABLE' if websocket_available else 'NOT FOUND'}")
        
        # Save results to file
        results_file = "/app/enhanced_mitosis_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        print(f"\n💾 Test results saved to: {results_file}")
        
        return success_rate >= 75
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)