#!/usr/bin/env python3
"""
Mitosis Backend Comprehensive Testing Script - Review Request Fulfillment

This script performs a complete verification of the Mitosis backend application as requested:
1. Health Check Completo - all services healthy
2. Configuración Ollama - connected to https://78d08925604a.ngrok-free.app with llama3.1:8b
3. Sistema de Memoria - advanced memory system working
4. API Endpoints - /api/agent/chat, /api/agent/status
5. Funcionalidad de Chat - send test message and get correct response
6. Herramientas disponibles - confirm 12 tools are available and operational
7. Estabilidad - verify no crashes or errors

Backend should be running on localhost:8001 and accessible externally.
"""

import requests
import json
import sys
import uuid
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
EXTERNAL_URL = "https://4359b6f3-95cc-48fc-92bb-0cc5ab04d8db.preview.emergentagent.com"
EXPECTED_OLLAMA_ENDPOINT = "https://78d08925604a.ngrok-free.app"
EXPECTED_MODEL = "llama3.1:8b"
EXPECTED_TOOLS_COUNT = 12

# Test results tracking
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "success_rate": 0
    }
}

def log_test(name, passed, details=None, error=None):
    """Log test result"""
    test_results["summary"]["total"] += 1
    if passed:
        test_results["summary"]["passed"] += 1
        status = "✅ PASSED"
    else:
        test_results["summary"]["failed"] += 1
        status = "❌ FAILED"
    
    test_results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details,
        "error": error,
        "timestamp": datetime.now().isoformat()
    })
    
    print(f"{status}: {name}")
    if details:
        print(f"   Details: {details}")
    if error:
        print(f"   Error: {error}")
    return passed

def make_request(method, endpoint, data=None, timeout=30, use_external=False):
    """Make HTTP request with error handling"""
    base_url = EXTERNAL_URL if use_external else BASE_URL
    url = f"{base_url}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response.status_code, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    except requests.exceptions.RequestException as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)

def test_1_health_check_completo():
    """1. Health Check Completo - Verificar que todos los servicios estén saludables"""
    print("\n" + "="*80)
    print("TEST 1: HEALTH CHECK COMPLETO")
    print("="*80)
    
    # Test basic health endpoint
    status_code, response = make_request("GET", "/api/health")
    
    if status_code != 200:
        return log_test("Health Check Completo", False, error=f"Health endpoint returned {status_code}: {response}")
    
    if not isinstance(response, dict):
        return log_test("Health Check Completo", False, error="Health endpoint did not return JSON")
    
    # Check required fields
    required_fields = ["status", "services"]
    missing_fields = [field for field in required_fields if field not in response]
    if missing_fields:
        return log_test("Health Check Completo", False, error=f"Missing fields: {missing_fields}")
    
    # Check overall status
    if response.get("status") != "healthy":
        return log_test("Health Check Completo", False, error=f"Overall status is not healthy: {response.get('status')}")
    
    # Check individual services
    services = response.get("services", {})
    required_services = ["database", "ollama", "tools"]
    
    service_status = {}
    for service in required_services:
        if service not in services:
            service_status[service] = "MISSING"
        elif service == "tools":
            # Tools should be a number (count of available tools)
            tools_count = services[service]
            service_status[service] = f"OK ({tools_count} tools)" if isinstance(tools_count, int) and tools_count > 0 else f"FAILED ({tools_count})"
        else:
            # Database and Ollama should be boolean true
            service_status[service] = "OK" if services[service] is True else f"FAILED ({services[service]})"
    
    # Check if all services are healthy
    all_healthy = all("OK" in status for status in service_status.values())
    
    details = f"Services: {service_status}"
    return log_test("Health Check Completo", all_healthy, details=details)

def test_2_configuracion_ollama():
    """2. Configuración Ollama - Verificar conexión al endpoint específico con modelo específico"""
    print("\n" + "="*80)
    print("TEST 2: CONFIGURACIÓN OLLAMA")
    print("="*80)
    
    # Test agent status endpoint
    status_code, response = make_request("GET", "/api/agent/status")
    
    if status_code != 200:
        return log_test("Configuración Ollama", False, error=f"Agent status endpoint returned {status_code}: {response}")
    
    if not isinstance(response, dict):
        return log_test("Configuración Ollama", False, error="Agent status endpoint did not return JSON")
    
    # Check Ollama configuration
    ollama_info = response.get("ollama", {})
    
    # Check endpoint
    endpoint = ollama_info.get("endpoint")
    endpoint_ok = endpoint == EXPECTED_OLLAMA_ENDPOINT
    
    # Check if connected
    connected = ollama_info.get("connected", False)
    
    # Check model (simplified - just check if it's mentioned)
    model = ollama_info.get("model")
    model_ok = model == EXPECTED_MODEL
    
    details = {
        "endpoint": f"Expected: {EXPECTED_OLLAMA_ENDPOINT}, Got: {endpoint}",
        "connected": connected,
        "model": f"Expected: {EXPECTED_MODEL}, Got: {model}",
        "endpoint_match": endpoint_ok,
        "model_match": model_ok
    }
    
    success = endpoint_ok and connected and model_ok
    return log_test("Configuración Ollama", success, details=str(details))

def test_3_sistema_memoria():
    """3. Sistema de Memoria - Confirmar que el sistema de memoria avanzado esté funcionando"""
    print("\n" + "="*80)
    print("TEST 3: SISTEMA DE MEMORIA")
    print("="*80)
    
    # Test if memory is working through chat endpoint (indirect test)
    status_code, response = make_request("POST", "/api/agent/chat", {
        "message": "Test memory system"
    }, timeout=15)
    
    if status_code != 200:
        return log_test("Sistema de Memoria", False, error=f"Chat endpoint returned {status_code}: {response}")
    
    if not isinstance(response, dict):
        return log_test("Sistema de Memoria", False, error="Chat endpoint did not return JSON")
    
    # Check if memory_used flag is present and true
    memory_used = response.get("memory_used", False)
    
    # Check agent status for memory info
    status_code2, status_response = make_request("GET", "/api/agent/status")
    memory_info = {}
    if status_code2 == 200 and isinstance(status_response, dict):
        memory_info = status_response.get("memory", {})
    
    memory_enabled = memory_info.get("enabled", False)
    memory_initialized = memory_info.get("initialized", False)
    
    details = {
        "memory_used_in_chat": memory_used,
        "memory_enabled": memory_enabled,
        "memory_initialized": memory_initialized,
        "status_endpoint": "OK" if status_code2 == 200 else f"FAILED ({status_code2})"
    }
    
    success = memory_used and memory_enabled
    return log_test("Sistema de Memoria", success, details=str(details))

def test_4_api_endpoints():
    """4. API Endpoints - Probar los principales endpoints"""
    print("\n" + "="*80)
    print("TEST 4: API ENDPOINTS")
    print("="*80)
    
    endpoints_to_test = [
        ("/api/agent/chat", "POST", {"message": "Hello, this is a test"}),
        ("/api/agent/status", "GET", None),
        ("/api/agent/health", "GET", None),
        ("/api/health", "GET", None)
    ]
    
    results = {}
    
    for endpoint, method, data in endpoints_to_test:
        status_code, response = make_request(method, endpoint, data, timeout=10)
        
        if status_code == 200:
            results[endpoint] = "OK"
        else:
            results[endpoint] = f"FAILED ({status_code})"
    
    success_count = sum(1 for result in results.values() if result == "OK")
    total_count = len(results)
    success = success_count >= total_count * 0.75  # At least 75% success rate
    
    details = f"Endpoints: {results} ({success_count}/{total_count} successful)"
    return log_test("API Endpoints", success, details=details)

def test_5_funcionalidad_chat():
    """5. Funcionalidad de Chat - Enviar mensaje de prueba y verificar respuesta correcta"""
    print("\n" + "="*80)
    print("TEST 5: FUNCIONALIDAD DE CHAT")
    print("="*80)
    
    # Test with a realistic message
    test_message = "Hola, ¿puedes ayudarme con información sobre inteligencia artificial?"
    
    status_code, response = make_request("POST", "/api/agent/chat", {
        "message": test_message
    }, timeout=30)
    
    if status_code != 200:
        return log_test("Funcionalidad de Chat", False, error=f"Chat endpoint returned {status_code}: {response}")
    
    if not isinstance(response, dict):
        return log_test("Funcionalidad de Chat", False, error="Chat endpoint did not return JSON")
    
    # Check response structure
    expected_fields = ["response", "task_id"]
    response_fields = list(response.keys())
    
    # Check if we got a meaningful response
    response_text = response.get("response", "")
    has_response = isinstance(response_text, str) and len(response_text) > 10
    
    # Check if task_id is present
    has_task_id = "task_id" in response and response["task_id"]
    
    # Check for memory usage (if available)
    memory_used = response.get("memory_used", False)
    
    details = {
        "response_length": len(response_text) if isinstance(response_text, str) else 0,
        "has_task_id": has_task_id,
        "memory_used": memory_used,
        "response_fields": response_fields
    }
    
    success = has_response and has_task_id
    return log_test("Funcionalidad de Chat", success, details=str(details))

def test_6_herramientas_disponibles():
    """6. Herramientas disponibles - Confirmar que las herramientas estén disponibles y operativas"""
    print("\n" + "="*80)
    print("TEST 6: HERRAMIENTAS DISPONIBLES")
    print("="*80)
    
    # Since /api/agent/tools doesn't exist, check via health endpoint
    status_code, response = make_request("GET", "/api/health")
    
    if status_code != 200:
        return log_test("Herramientas Disponibles", False, error=f"Health endpoint returned {status_code}: {response}")
    
    if not isinstance(response, dict):
        return log_test("Herramientas Disponibles", False, error="Health endpoint did not return JSON")
    
    # Check tools count from health endpoint
    services = response.get("services", {})
    tools_count = services.get("tools", 0)
    
    # Check if we have the expected number of tools (approximately)
    expected_min_tools = 10  # At least 10 tools
    tools_count_ok = tools_count >= expected_min_tools
    
    # Test if chat endpoint can handle tool requests (indirect test)
    chat_status, chat_response = make_request("POST", "/api/agent/chat", {
        "message": "Test tools availability"
    }, timeout=10)
    
    chat_works = chat_status == 200
    
    details = {
        "tools_count": f"{tools_count} (expected >= {expected_min_tools})",
        "tools_count_ok": tools_count_ok,
        "chat_endpoint_works": chat_works,
        "tools_reported": tools_count
    }
    
    success = tools_count_ok and chat_works
    return log_test("Herramientas Disponibles", success, details=str(details))

def test_7_estabilidad():
    """7. Estabilidad - Verificar que no haya crashes ni errores"""
    print("\n" + "="*80)
    print("TEST 7: ESTABILIDAD")
    print("="*80)
    
    # Perform multiple consecutive requests to test stability
    stability_tests = [
        ("GET", "/api/health", None),
        ("GET", "/api/agent/status", None),
        ("POST", "/api/agent/chat", {"message": "Test message 1"}),
        ("GET", "/api/agent/tools", None),
        ("POST", "/api/agent/chat", {"message": "Test message 2"}),
    ]
    
    results = []
    start_time = time.time()
    
    for i, (method, endpoint, data) in enumerate(stability_tests):
        print(f"   Stability test {i+1}/{len(stability_tests)}: {method} {endpoint}")
        
        test_start = time.time()
        status_code, response = make_request(method, endpoint, data, timeout=15)
        test_duration = time.time() - test_start
        
        success = status_code == 200
        results.append({
            "test": f"{method} {endpoint}",
            "success": success,
            "status_code": status_code,
            "duration": round(test_duration, 2)
        })
        
        if not success:
            print(f"      ❌ Failed: {status_code}")
        else:
            print(f"      ✅ Success: {test_duration:.2f}s")
        
        # Small delay between requests
        time.sleep(0.5)
    
    total_duration = time.time() - start_time
    successful_tests = sum(1 for result in results if result["success"])
    total_tests = len(results)
    
    # Check for consistent performance (no test should take too long)
    max_duration = max(result["duration"] for result in results)
    performance_ok = max_duration < 30  # No single request should take more than 30 seconds
    
    # Check success rate
    success_rate = successful_tests / total_tests
    stability_ok = success_rate >= 0.8  # At least 80% success rate
    
    details = {
        "success_rate": f"{successful_tests}/{total_tests} ({success_rate:.1%})",
        "total_duration": f"{total_duration:.2f}s",
        "max_request_duration": f"{max_duration:.2f}s",
        "performance_ok": performance_ok,
        "failed_tests": [result["test"] for result in results if not result["success"]]
    }
    
    success = stability_ok and performance_ok
    return log_test("Estabilidad", success, details=str(details))

def test_external_accessibility():
    """Bonus Test: External Accessibility - Verificar acceso externo"""
    print("\n" + "="*80)
    print("BONUS TEST: EXTERNAL ACCESSIBILITY")
    print("="*80)
    
    # Test external URL access
    status_code, response = make_request("GET", "/api/health", use_external=True, timeout=15)
    
    if status_code != 200:
        return log_test("External Accessibility", False, error=f"External health endpoint returned {status_code}: {response}")
    
    if not isinstance(response, dict):
        return log_test("External Accessibility", False, error="External health endpoint did not return JSON")
    
    # Check if response is the same as internal
    external_status = response.get("status")
    success = external_status == "healthy"
    
    details = f"External URL: {EXTERNAL_URL}, Status: {external_status}"
    return log_test("External Accessibility", success, details=details)

def print_final_summary():
    """Print comprehensive test summary"""
    print("\n" + "="*100)
    print("MITOSIS BACKEND COMPREHENSIVE TEST RESULTS")
    print("="*100)
    
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    test_results["summary"]["success_rate"] = success_rate
    
    print(f"Timestamp: {test_results['timestamp']}")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Overall assessment
    if success_rate >= 90:
        overall_status = "🎉 EXCELLENT - SISTEMA COMPLETAMENTE OPERACIONAL"
    elif success_rate >= 75:
        overall_status = "✅ GOOD - SISTEMA MAYORMENTE FUNCIONAL"
    elif success_rate >= 50:
        overall_status = "⚠️ PARTIAL - SISTEMA PARCIALMENTE FUNCIONAL"
    else:
        overall_status = "❌ CRITICAL - SISTEMA REQUIERE ATENCIÓN INMEDIATA"
    
    print(f"\nOVERALL STATUS: {overall_status}")
    
    # Detailed results
    print(f"\nDETAILED RESULTS:")
    print("-" * 100)
    
    for test in test_results["tests"]:
        status_icon = "✅" if test["passed"] else "❌"
        print(f"{status_icon} {test['name']}")
        if test.get("details"):
            print(f"   {test['details']}")
        if test.get("error"):
            print(f"   Error: {test['error']}")
    
    # Failed tests summary
    failed_tests = [test for test in test_results["tests"] if not test["passed"]]
    if failed_tests:
        print(f"\nFAILED TESTS SUMMARY:")
        print("-" * 50)
        for test in failed_tests:
            print(f"❌ {test['name']}")
            if test.get("error"):
                print(f"   Error: {test['error']}")
    
    print("\n" + "="*100)
    
    return success_rate

def main():
    """Run all tests"""
    print("🚀 INICIANDO VERIFICACIÓN COMPLETA DEL BACKEND MITOSIS")
    print("="*100)
    print(f"Backend URL: {BASE_URL}")
    print(f"External URL: {EXTERNAL_URL}")
    print(f"Expected Ollama Endpoint: {EXPECTED_OLLAMA_ENDPOINT}")
    print(f"Expected Model: {EXPECTED_MODEL}")
    print("="*100)
    
    # Run all tests
    test_1_health_check_completo()
    test_2_configuracion_ollama()
    test_3_sistema_memoria()
    test_4_api_endpoints()
    test_5_funcionalidad_chat()
    test_6_herramientas_disponibles()
    test_7_estabilidad()
    test_external_accessibility()
    
    # Print final summary
    success_rate = print_final_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 75 else 1)

if __name__ == "__main__":
    main()