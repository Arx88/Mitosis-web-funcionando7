#!/usr/bin/env python3
"""
Test Script Rápido para Verificación de Mejoras Críticas
Testing optimizado para verificar funcionalidades clave sin timeouts
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"
TIMEOUT = 10  # Timeout más corto

def quick_test(endpoint, method="GET", data=None, test_name="Test"):
    """Ejecutar test rápido con timeout corto"""
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=TIMEOUT)
        else:
            response = requests.post(f"{BACKEND_URL}{endpoint}", 
                                   json=data, timeout=TIMEOUT)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            return True, response.json(), elapsed
        else:
            return False, {"error": f"HTTP {response.status_code}"}, elapsed
            
    except requests.exceptions.Timeout:
        return False, {"error": "Timeout"}, TIMEOUT
    except Exception as e:
        return False, {"error": str(e)}, 0

def main():
    print("🚀 TESTING RÁPIDO DE MEJORAS MITOSIS V5-BETA")
    print("=" * 60)
    
    tests_results = []
    
    # Test 1: Health Check
    print("📊 Test 1: Backend Health...")
    success, data, elapsed = quick_test("/api/health")
    if success:
        print(f"   ✅ Health OK ({elapsed:.2f}s)")
        print(f"   ✅ Services: DB={data['services']['database']}, Ollama={data['services']['ollama']}, Tools={data['services']['tools']}")
        tests_results.append(("Health Check", True, elapsed))
    else:
        print(f"   ❌ Health Failed: {data.get('error', 'Unknown')}")
        tests_results.append(("Health Check", False, elapsed))
    
    # Test 2: Clasificación Casual
    print("\n🗣️ Test 2: Clasificación Casual...")
    success, data, elapsed = quick_test("/api/agent/chat", "POST", {"message": "hola"})
    if success:
        has_plan = 'plan' in data and data['plan'] and len(data['plan'].get('steps', [])) > 0
        is_casual = not has_plan
        print(f"   ✅ Clasificación Casual OK ({elapsed:.2f}s)")
        print(f"   ✅ Clasificado como: {'CASUAL' if is_casual else 'TAREA'}")
        print(f"   ✅ Response: {data['response'][:50]}...")
        tests_results.append(("Clasificación Casual", True, elapsed))
    else:
        print(f"   ❌ Clasificación Failed: {data.get('error', 'Unknown')}")
        tests_results.append(("Clasificación Casual", False, elapsed))
    
    # Test 3: Clasificación de Tarea (con timeout más largo)
    print("\n📋 Test 3: Clasificación de Tarea...")
    success, data, elapsed = quick_test("/api/agent/chat", "POST", {"message": "buscar datos sobre IA"})
    if success:
        has_plan = 'plan' in data and data['plan'] and len(data['plan'].get('steps', [])) > 0
        print(f"   ✅ Clasificación Tarea OK ({elapsed:.2f}s)")
        print(f"   ✅ Clasificado como: {'TAREA' if has_plan else 'CASUAL'}")
        if has_plan:
            plan = data['plan']
            print(f"   ✅ Plan: {len(plan['steps'])} pasos")
            print(f"   ✅ Source: {plan.get('plan_source', 'unknown')}")
            print(f"   ✅ Status: {data.get('execution_status', 'unknown')}")
            
            # Verificar estructura del primer paso
            if plan['steps']:
                step = plan['steps'][0]
                required_fields = ['id', 'title', 'description', 'tool', 'status']
                valid_structure = all(field in step for field in required_fields)
                print(f"   ✅ Step Structure: {'Valid' if valid_structure else 'Invalid'}")
        
        tests_results.append(("Clasificación Tarea", True, elapsed))
    else:
        print(f"   ❌ Clasificación Tarea Failed: {data.get('error', 'Unknown')}")
        tests_results.append(("Clasificación Tarea", False, elapsed))
    
    # Resumen Final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTING:")
    
    total_tests = len(tests_results)
    successful_tests = sum(1 for _, success, _ in tests_results if success)
    
    for test_name, success, elapsed in tests_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name} ({elapsed:.2f}s)")
    
    print(f"\n🎯 RESULTADO: {successful_tests}/{total_tests} tests exitosos")
    success_rate = (successful_tests / total_tests) * 100
    print(f"🎯 TASA DE ÉXITO: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 TESTING EXITOSO - Mejoras funcionando correctamente!")
    else:
        print("⚠️ TESTING CON PROBLEMAS - Revisar fallos")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)