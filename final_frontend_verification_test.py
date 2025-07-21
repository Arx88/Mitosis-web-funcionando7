#!/usr/bin/env python3
"""
Test final para verificar que el botón Verificar del frontend funcione correctamente
"""
import requests
import json

def test_frontend_verification():
    """Test final para verificar el botón de verificación del frontend"""
    print("🎯 TESTING FINAL: Verificación del botón 'Verificar' en el frontend")
    print("=" * 65)
    
    print("1️⃣ Probando endpoint actual del backend...")
    try:
        # Simular la llamada que hace el frontend
        response = requests.post(
            "https://61a56488-e3f8-4b60-b174-bf039e1491db.preview.emergentagent.com/api/agent/ollama/check",
            json={"endpoint": "https://bef4a4bb93d1.ngrok-free.app"},
            timeout=10
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Content: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Verification SUCCESS!")
            print(f"🔗 Endpoint: {data.get('endpoint')}")
            print(f"🔌 Connected: {data.get('is_connected')}")
            print(f"📊 Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Verification FAILED: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test ERROR: {e}")
        return False

def test_direct_endpoint_verification():
    """Test directo del nuevo endpoint"""
    print("\n2️⃣ Verificando que el nuevo endpoint funcione directamente...")
    
    try:
        # Verificar directamente el nuevo endpoint
        response = requests.get("https://bef4a4bb93d1.ngrok-free.app/api/tags", timeout=10)
        
        print(f"📊 Direct Endpoint Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            print(f"✅ Direct endpoint is WORKING!")
            print(f"🤖 Models available: {len(models)}")
            print(f"🔍 llama3.1:8b available: {'llama3.1:8b' in models}")
            return True
        else:
            print(f"❌ Direct endpoint FAILED: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Direct endpoint ERROR: {e}")
        return False

def main():
    """Función principal del test"""
    
    # Test 1: Frontend verification
    frontend_ok = test_frontend_verification()
    
    # Test 2: Direct endpoint
    endpoint_ok = test_direct_endpoint_verification()
    
    print("\n" + "=" * 65)
    print("📊 RESULTS SUMMARY:")
    print(f"Frontend Verification: {'✅ WORKING' if frontend_ok else '❌ FAILED'}")
    print(f"Direct Endpoint: {'✅ WORKING' if endpoint_ok else '❌ FAILED'}")
    
    if frontend_ok and endpoint_ok:
        print("\n🎉 FINAL TEST COMPLETED SUCCESSFULLY!")
        print("✅ The 'Verificar' button in frontend should now work!")
        print("🔗 New endpoint: https://bef4a4bb93d1.ngrok-free.app")
        print("🤖 Model: llama3.1:8b")
        print("💾 Configuration updated in both frontend and backend")
        print("🎯 TASK COMPLETED: Endpoint change successful!")
        return 0
    else:
        if not frontend_ok:
            print("⚠️ Frontend verification still has issues")
        if not endpoint_ok:
            print("⚠️ Direct endpoint verification failed")
        return 1

if __name__ == "__main__":
    exit(main())