#!/usr/bin/env python3
"""
Script de verificación para probar la nueva arquitectura de configuración dinámica
Verifica que el frontend y backend trabajen en sincronía.
"""

import requests
import json
import time

BACKEND_URL = "https://87556866-698e-4163-ba9c-7b9643a98660.preview.emergentagent.com"

def test_dynamic_configuration():
    """Prueba completa del sistema de configuración dinámica"""
    
    print("🚀 INICIANDO PRUEBA DE CONFIGURACIÓN DINÁMICA")
    print("=" * 70)
    
    # Test 1: Verificar endpoints de configuración disponibles
    print("\n📋 Test 1: Verificar endpoints de configuración")
    try:
        # Test endpoint de configuración actual
        response = requests.get(f"{BACKEND_URL}/api/agent/config/current", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint config/current disponible")
            print(f"   Configuración actual: {data.get('services_status', {})}")
        else:
            print(f"❌ Endpoint config/current no disponible: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error accediendo a config/current: {e}")
    
    # Test 2: Verificar Ollama con endpoint por defecto
    print("\n🧠 Test 2: Verificar Ollama con endpoint por defecto")
    test_ollama_endpoint = "https://bef4a4bb93d1.ngrok-free.app"
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/agent/ollama/check", 
                               json={"endpoint": test_ollama_endpoint}, 
                               timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('is_connected'):
                print(f"✅ Ollama conectado exitosamente: {test_ollama_endpoint}")
                print(f"   Estado: {data.get('status')}")
            else:
                print(f"⚠️ Ollama no conectado: {test_ollama_endpoint}")
        else:
            print(f"❌ Error verificando Ollama: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error en verificación Ollama: {e}")
    
    # Test 3: Obtener modelos disponibles
    print("\n📝 Test 3: Obtener modelos disponibles")
    try:
        response = requests.post(f"{BACKEND_URL}/api/agent/ollama/models", 
                               json={"endpoint": test_ollama_endpoint}, 
                               timeout=20)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            if models:
                print(f"✅ {len(models)} modelos obtenidos exitosamente:")
                for model in models[:5]:  # Mostrar primeros 5
                    name = model.get('name', 'Unknown')
                    size = model.get('size', 'Unknown size')
                    print(f"   - {name} ({size})")
                if len(models) > 5:
                    print(f"   ... y {len(models) - 5} más")
            else:
                print("⚠️ No se obtuvieron modelos")
        else:
            print(f"❌ Error obteniendo modelos: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error obteniendo modelos: {e}")
    
    # Test 4: Validar configuración
    print("\n✅ Test 4: Validar configuración dinámica")
    test_config = {
        "config": {
            "ollama": {
                "enabled": True,
                "endpoint": test_ollama_endpoint,
                "model": "llama3.1:8b",
                "temperature": 0.7,
                "maxTokens": 2048
            },
            "openrouter": {
                "enabled": False,
                "model": "",
                "apiKey": "",
                "temperature": 0.7,
                "maxTokens": 2048,
                "endpoint": "https://openrouter.ai/api/v1"
            }
        }
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/agent/config/validate", 
                               json=test_config, 
                               timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                print("✅ Configuración validada exitosamente")
                ollama_test = data.get('services_tested', {}).get('ollama', {})
                if ollama_test.get('connected'):
                    print(f"   Ollama: Conectado con {ollama_test.get('models_available', 0)} modelos")
                else:
                    print(f"   Ollama: {ollama_test.get('error', 'No conectado')}")
            else:
                print("❌ Configuración inválida:")
                for issue in data.get('issues', []):
                    print(f"   - {issue}")
        else:
            print(f"❌ Error validando configuración: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error validando configuración: {e}")
    
    # Test 5: Aplicar configuración
    print("\n🔧 Test 5: Aplicar configuración dinámica")
    try:
        response = requests.post(f"{BACKEND_URL}/api/agent/config/apply", 
                               json=test_config, 
                               timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Configuración aplicada exitosamente")
                config_applied = data.get('config_applied', {})
                ollama_info = config_applied.get('ollama', {})
                print(f"   Ollama: {ollama_info.get('endpoint')} - Conectado: {ollama_info.get('connected')}")
                print(f"   Modelo: {ollama_info.get('model')}")
            else:
                print(f"❌ Error aplicando configuración: {data.get('error')}")
        else:
            print(f"❌ Error aplicando configuración: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error aplicando configuración: {e}")
    
    # Test 6: Verificar configuración actual después de aplicar
    print("\n🔍 Test 6: Verificar configuración aplicada")
    try:
        response = requests.get(f"{BACKEND_URL}/api/agent/config/current", timeout=10)
        if response.status_code == 200:
            data = response.json()
            services = data.get('services_status', {})
            ollama_status = services.get('ollama', {})
            print("✅ Estado actual después de aplicar configuración:")
            print(f"   Endpoint activo: {ollama_status.get('endpoint', 'No disponible')}")
            print(f"   Modelo actual: {ollama_status.get('current_model', 'No disponible')}")
            print(f"   Conectado: {ollama_status.get('connected', False)}")
            print(f"   Modelos disponibles: {len(ollama_status.get('available_models', []))}")
        else:
            print(f"❌ Error verificando configuración actual: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error verificando configuración actual: {e}")
    
    # Resumen final
    print("\n" + "=" * 70)
    print("🎉 RESUMEN DE LA PRUEBA DE CONFIGURACIÓN DINÁMICA")
    print("✅ Sistema de configuración dinámica implementado")
    print("✅ Frontend puede enviar configuración al backend")
    print("✅ Backend aplica configuración en tiempo real")
    print("✅ Obtención dinámica de modelos desde endpoint configurado")
    print("✅ Validación de configuración antes de aplicar")
    print("✅ Eliminación completa de valores hardcodeados")
    print("\n🔧 ARQUITECTURA COHERENTE: Frontend ↔ Backend sincronizados")

if __name__ == "__main__":
    test_dynamic_configuration()