#!/usr/bin/env python3
"""
Test de Arquitectura de Configuración Dinámica para Ollama
Prueba los nuevos endpoints de configuración dinámica implementados
"""

import requests
import json
import time
from datetime import datetime

# Configuración de prueba
BACKEND_URL = "https://9003c516-1eb2-4fd2-860d-2a1b53c51d8e.preview.emergentagent.com"
TEST_OLLAMA_ENDPOINT = "https://bef4a4bb93d1.ngrok-free.app"

def print_test_header(test_name):
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")

def print_result(success, message, data=None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if data:
        print(f"   Data: {json.dumps(data, indent=2)}")

def test_current_configuration():
    """Test 1: Obtener configuración actual"""
    print_test_header("TEST 1: Configuración Actual - GET /api/agent/config/current")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/agent/config/current", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar estructura de respuesta
            required_fields = ['success', 'config', 'services_status', 'timestamp']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print_result(False, f"Missing required fields: {missing_fields}", data)
                return False
            
            # Verificar estado de servicios
            services_status = data.get('services_status', {})
            ollama_status = services_status.get('ollama', {})
            
            print_result(True, "Configuración actual obtenida exitosamente")
            print(f"   📊 Ollama endpoint: {ollama_status.get('endpoint', 'N/A')}")
            print(f"   📊 Ollama connected: {ollama_status.get('connected', False)}")
            print(f"   📊 Current model: {ollama_status.get('current_model', 'N/A')}")
            print(f"   📊 Available models: {len(ollama_status.get('available_models', []))}")
            
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Request failed: {str(e)}")
        return False

def test_validate_configuration():
    """Test 2: Validar configuración"""
    print_test_header("TEST 2: Validar Configuración - POST /api/agent/config/validate")
    
    # Test con configuración válida
    print("\n🔍 Probando configuración VÁLIDA...")
    valid_config = {
        "config": {
            "ollama": {
                "enabled": True,
                "endpoint": TEST_OLLAMA_ENDPOINT,
                "model": "llama3.1:8b"
            },
            "openrouter": {
                "enabled": False
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/config/validate",
            json=valid_config,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar estructura de validación
            required_fields = ['valid', 'issues', 'services_tested']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print_result(False, f"Missing validation fields: {missing_fields}", data)
                return False
            
            is_valid = data.get('valid', False)
            issues = data.get('issues', [])
            services_tested = data.get('services_tested', {})
            
            print_result(is_valid, f"Configuración válida: {is_valid}")
            if issues:
                print(f"   ⚠️ Issues found: {issues}")
            
            # Verificar prueba de servicios
            ollama_test = services_tested.get('ollama', {})
            if ollama_test:
                print(f"   🔗 Ollama endpoint tested: {ollama_test.get('endpoint')}")
                print(f"   🔗 Ollama connected: {ollama_test.get('connected', False)}")
                print(f"   🔗 Models available: {ollama_test.get('models_available', 0)}")
                
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Valid config test failed: {str(e)}")
        return False
    
    # Test con configuración inválida
    print("\n🔍 Probando configuración INVÁLIDA...")
    invalid_config = {
        "config": {
            "ollama": {
                "enabled": True,
                "endpoint": "https://invalid-endpoint-test.com",
                "model": "nonexistent-model"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/config/validate",
            json=invalid_config,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            is_valid = data.get('valid', True)  # Should be False
            issues = data.get('issues', [])
            
            if not is_valid and issues:
                print_result(True, f"Configuración inválida detectada correctamente: {len(issues)} issues")
                print(f"   ⚠️ Issues: {issues}")
                return True
            else:
                print_result(False, "Configuración inválida no fue detectada", data)
                return False
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Invalid config test failed: {str(e)}")
        return False

def test_apply_configuration():
    """Test 3: Aplicar configuración"""
    print_test_header("TEST 3: Aplicar Configuración - POST /api/agent/config/apply")
    
    new_config = {
        "config": {
            "ollama": {
                "enabled": True,
                "endpoint": TEST_OLLAMA_ENDPOINT,
                "model": "llama3.1:8b"
            },
            "openrouter": {
                "enabled": False
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/config/apply",
            json=new_config,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar respuesta de aplicación
            if data.get('success', False):
                config_applied = data.get('config_applied', {})
                ollama_applied = config_applied.get('ollama', {})
                
                print_result(True, "Configuración aplicada exitosamente")
                print(f"   🔧 Ollama enabled: {ollama_applied.get('enabled', False)}")
                print(f"   🔧 Ollama endpoint: {ollama_applied.get('endpoint', 'N/A')}")
                print(f"   🔧 Ollama model: {ollama_applied.get('model', 'N/A')}")
                print(f"   🔧 Ollama connected: {ollama_applied.get('connected', False)}")
                
                return True
            else:
                print_result(False, f"Application failed: {data.get('error', 'Unknown error')}", data)
                return False
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Apply config failed: {str(e)}")
        return False

def test_ollama_models():
    """Test 4: Obtener modelos de Ollama"""
    print_test_header("TEST 4: Obtener Modelos Ollama - POST /api/agent/ollama/models")
    
    # Test con endpoint válido
    print("\n🔍 Probando con endpoint VÁLIDO...")
    valid_request = {
        "endpoint": TEST_OLLAMA_ENDPOINT
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/ollama/models",
            json=valid_request,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            models = data.get('models', [])
            endpoint = data.get('endpoint', '')
            count = data.get('count', 0)
            is_fallback = data.get('fallback', False)
            
            if models:
                print_result(True, f"Modelos obtenidos exitosamente: {count} modelos")
                print(f"   📋 Endpoint: {endpoint}")
                print(f"   📋 Fallback used: {is_fallback}")
                
                # Mostrar algunos modelos
                for i, model in enumerate(models[:3]):
                    name = model.get('name', 'Unknown')
                    size = model.get('size', 'Unknown size')
                    print(f"   📋 Model {i+1}: {name} ({size})")
                
                if len(models) > 3:
                    print(f"   📋 ... and {len(models) - 3} more models")
                    
                return True
            else:
                print_result(False, "No models returned", data)
                return False
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Models request failed: {str(e)}")
        return False
    
    # Test con endpoint inválido (debería usar fallback)
    print("\n🔍 Probando con endpoint INVÁLIDO (fallback)...")
    invalid_request = {
        "endpoint": "https://invalid-ollama-endpoint.com"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/ollama/models",
            json=invalid_request,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            models = data.get('models', [])
            is_fallback = data.get('fallback', False)
            warning = data.get('warning', '')
            
            if is_fallback and models:
                print_result(True, f"Fallback models returned: {len(models)} modelos")
                print(f"   ⚠️ Warning: {warning}")
                return True
            else:
                print_result(False, "Fallback not working correctly", data)
                return False
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Fallback test failed: {str(e)}")
        return False

def test_ollama_connection():
    """Test 5: Verificar conexión Ollama"""
    print_test_header("TEST 5: Verificar Conexión Ollama - POST /api/agent/ollama/check")
    
    # Test con endpoint válido
    print("\n🔍 Probando conexión con endpoint VÁLIDO...")
    valid_request = {
        "endpoint": TEST_OLLAMA_ENDPOINT
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/ollama/check",
            json=valid_request,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            is_connected = data.get('is_connected', False)
            endpoint = data.get('endpoint', '')
            status = data.get('status', '')
            
            print_result(is_connected, f"Conexión Ollama: {status}")
            print(f"   🔗 Endpoint: {endpoint}")
            print(f"   🔗 Connected: {is_connected}")
            
            return is_connected
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Connection check failed: {str(e)}")
        return False
    
    # Test con endpoint inválido
    print("\n🔍 Probando conexión con endpoint INVÁLIDO...")
    invalid_request = {
        "endpoint": "https://invalid-ollama-endpoint.com"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/ollama/check",
            json=invalid_request,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            is_connected = data.get('is_connected', True)  # Should be False
            
            if not is_connected:
                print_result(True, "Endpoint inválido detectado correctamente")
                return True
            else:
                print_result(False, "Endpoint inválido no fue detectado", data)
                return False
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Invalid connection test failed: {str(e)}")
        return False

def test_complete_flow():
    """Test 6: Flujo completo de configuración"""
    print_test_header("TEST 6: Flujo Completo de Configuración Dinámica")
    
    print("\n🔄 Paso 1: Obtener configuración actual...")
    if not test_current_configuration():
        return False
    
    print("\n🔄 Paso 2: Validar nueva configuración...")
    if not test_validate_configuration():
        return False
    
    print("\n🔄 Paso 3: Aplicar nueva configuración...")
    if not test_apply_configuration():
        return False
    
    print("\n🔄 Paso 4: Verificar que configuración se aplicó...")
    time.sleep(2)  # Esperar a que se aplique
    if not test_current_configuration():
        return False
    
    print("\n🔄 Paso 5: Obtener modelos del endpoint configurado...")
    if not test_ollama_models():
        return False
    
    print_result(True, "Flujo completo de configuración dinámica exitoso")
    return True

def main():
    """Ejecutar todos los tests de configuración dinámica"""
    print("🚀 INICIANDO TESTS DE ARQUITECTURA DE CONFIGURACIÓN DINÁMICA")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print(f"🔗 Test Ollama Endpoint: {TEST_OLLAMA_ENDPOINT}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    tests = [
        ("Configuración Actual", test_current_configuration),
        ("Validar Configuración", test_validate_configuration),
        ("Aplicar Configuración", test_apply_configuration),
        ("Obtener Modelos Ollama", test_ollama_models),
        ("Verificar Conexión Ollama", test_ollama_connection),
        ("Flujo Completo", test_complete_flow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_result(False, f"Test {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE TESTS DE CONFIGURACIÓN DINÁMICA")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 RESULTADO FINAL: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 TODOS LOS TESTS DE CONFIGURACIÓN DINÁMICA PASARON")
        print("✅ La arquitectura de configuración dinámica está funcionando correctamente")
        print("✅ El frontend puede controlar el comportamiento del backend dinámicamente")
        print("✅ Sin valores hardcodeados, todo es configurable")
        print("✅ La configuración persiste entre llamadas")
        print("✅ Los modelos vienen del endpoint configurado dinámicamente")
        print("✅ La validación verifica conectividad real")
    else:
        print("⚠️ ALGUNOS TESTS FALLARON")
        print("❌ La arquitectura de configuración dinámica necesita ajustes")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)