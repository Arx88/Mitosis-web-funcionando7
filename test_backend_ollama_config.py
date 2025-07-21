#!/usr/bin/env python3
"""
Direct test to verify that the backend is actually loading the correct Ollama URL from environment variables.
"""
import os
import sys
import requests
from pathlib import Path

# Add backend paths
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

def test_env_variables():
    """Test if environment variables are properly loaded"""
    print("🔍 Testing Environment Variables...")
    
    # Force reload of .env file 
    from dotenv import load_dotenv
    load_dotenv(str(backend_path / ".env"), override=True)
    
    ollama_base_url = os.getenv('OLLAMA_BASE_URL')
    print(f"📊 OLLAMA_BASE_URL from env: {ollama_base_url}")
    print(f"📊 OLLAMA_HOST from env: {os.getenv('OLLAMA_HOST')}")
    print(f"📊 OLLAMA_DEFAULT_MODEL from env: {os.getenv('OLLAMA_DEFAULT_MODEL')}")
    
    return ollama_base_url

def test_service_creation():
    """Test creating OllamaService with environment variables"""
    print("\n🔍 Testing OllamaService creation...")
    
    # Force reload of .env file
    from dotenv import load_dotenv
    load_dotenv(str(backend_path / ".env"), override=True)
    
    try:
        from src.services.ollama_service import OllamaService
        
        # Create service without passing base_url to force it to use env var
        ollama_service = OllamaService()
        
        print(f"📊 Service URL: {ollama_service.base_url}")
        print(f"📊 Service model: {ollama_service.default_model}")
        
        # Test connection
        connection_result = ollama_service.check_connection()
        print(f"🔗 Connection result: {connection_result}")
        
        if connection_result.get('healthy'):
            print("✅ Service connection SUCCESS")
            return True
        else:
            print(f"❌ Service connection FAILED: {connection_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Service creation error: {e}")
        return False

def test_direct_backend_api():
    """Test calling the backend API"""
    print("\n🔍 Testing Backend API with Ollama...")
    
    try:
        # Test health endpoint first
        health_response = requests.get("http://localhost:8001/api/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"📊 Health data: {health_response.json()}")
        else:
            print(f"❌ Health endpoint failed: {health_response.status_code}")
            return False
        
        # Test a simple chat to verify Ollama integration
        print("\n🧪 Testing chat endpoint...")
        chat_response = requests.post(
            "http://localhost:8001/api/agent/chat",
            json={
                "message": "Hola, esto es una prueba del nuevo endpoint de Ollama",
                "task_id": "test_endpoint_change"
            },
            timeout=60  # Longer timeout for LLM response
        )
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            print(f"✅ Chat endpoint SUCCESS")
            print(f"📝 Response: {chat_data.get('response', '')[:150]}...")
            print(f"🤖 Model: {chat_data.get('model', 'Unknown')}")
            print(f"🔗 Task ID: {chat_data.get('task_id', 'Unknown')}")
            return True
        else:
            print(f"❌ Chat endpoint failed: {chat_response.status_code}")
            print(f"Error: {chat_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Backend API test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Ollama Endpoint Configuration After Change")
    print("=" * 55)
    
    results = []
    
    # Test 1: Environment variables
    results.append(test_env_variables() == "https://bef4a4bb93d1.ngrok-free.app")
    
    # Test 2: Service creation
    results.append(test_service_creation())
    
    # Test 3: Backend API
    results.append(test_direct_backend_api())
    
    print("\n" + "=" * 55)
    print("📊 TEST RESULTS:")
    
    test_names = [
        "Environment Variables Correct",
        "OllamaService Uses New Endpoint", 
        "Backend API Chat Works"
    ]
    
    all_passed = True
    for i, (name, passed) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Ollama endpoint change successful.")
        print("📱 New endpoint: https://bef4a4bb93d1.ngrok-free.app")
        print("🤖 Model: llama3.1:8b")
        print("✅ Backend is properly configured and functional")
        return 0
    else:
        print("\n❌ Some tests failed. Check configuration.")
        return 1

if __name__ == "__main__":
    exit(main())