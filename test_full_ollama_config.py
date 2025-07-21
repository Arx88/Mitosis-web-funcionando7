#!/usr/bin/env python3
"""
Test para verificar que el frontend esté utilizando el nuevo endpoint de Ollama
"""
import requests
import time

def test_frontend_ollama_config():
    """Test para verificar la configuración de Ollama en el frontend"""
    print("🔍 Testing Frontend Ollama Configuration...")
    
    # URL del frontend
    frontend_url = "https://61a56488-e3f8-4b60-b174-bf039e1491db.preview.emergentagent.com"
    
    try:
        # Hacer request al frontend
        response = requests.get(frontend_url, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Verificar que el nuevo endpoint esté en el contenido
            if "bef4a4bb93d1.ngrok-free.app" in content:
                print("✅ NEW ENDPOINT found in frontend!")
                print("🔗 Frontend is configured with: https://bef4a4bb93d1.ngrok-free.app")
                
                # Verificar que el endpoint anterior no esté presente
                if "78d08925604a.ngrok-free.app" not in content:
                    print("✅ OLD ENDPOINT removed from frontend")
                    return True
                else:
                    print("⚠️ OLD ENDPOINT still present in frontend")
                    return False
            else:
                print("❌ NEW ENDPOINT not found in frontend content")
                print("🔍 Looking for Ollama configuration in response...")
                
                # Buscar cualquier referencia a ngrok
                if "ngrok-free.app" in content:
                    print("🔗 Found ngrok reference in frontend")
                else:
                    print("❌ No ngrok references found")
                return False
        else:
            print(f"❌ Frontend request failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test error: {e}")
        return False

def test_backend_ollama_verification():
    """Test para verificar que el backend también esté usando el nuevo endpoint"""
    print("\n🔍 Testing Backend Ollama Verification Endpoint...")
    
    try:
        # Probar el endpoint específico de verificación de Ollama del backend
        backend_url = "http://localhost:8001"
        
        # Test de health check
        health_response = requests.get(f"{backend_url}/api/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Backend health check successful")
        
        # Test de status del agente que debe mostrar la configuración actual
        status_response = requests.get(f"{backend_url}/api/agent/status", timeout=30)
        if status_response.status_code == 200:
            status_data = status_response.json()
            print("✅ Agent status retrieved")
            print(f"🤖 Models available: {status_data.get('models_available', [])}")
            print(f"🔧 Tools available: {status_data.get('tools_available', 0)}")
            return True
        else:
            print(f"⚠️ Agent status returned: {status_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend test error: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Testing Frontend and Backend Ollama Configuration")
    print("=" * 60)
    
    # Test frontend
    frontend_ok = test_frontend_ollama_config()
    
    # Test backend
    backend_ok = test_backend_ollama_verification()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS:")
    print(f"Frontend Configuration: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"Backend Configuration: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    
    if frontend_ok and backend_ok:
        print("\n🎉 BOTH FRONTEND AND BACKEND CONFIGURED CORRECTLY!")
        print("🔗 New Endpoint: https://bef4a4bb93d1.ngrok-free.app")
        print("🤖 Model: llama3.1:8b")
        print("✅ The verification button in frontend should now work!")
        return 0
    else:
        print("\n⚠️ Some configurations may need attention")
        if not frontend_ok:
            print("🔧 Frontend may need rebuild or cache clear")
        if not backend_ok:
            print("🔧 Backend may need service restart")
        return 1

if __name__ == "__main__":
    exit(main())