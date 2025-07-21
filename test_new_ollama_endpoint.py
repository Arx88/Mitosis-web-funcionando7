#!/usr/bin/env python3
"""
Test script to verify the new Ollama endpoint configuration
"""
import requests
import json
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

def test_ollama_direct():
    """Test direct connection to the new Ollama endpoint"""
    print("🔍 Testing direct Ollama endpoint connection...")
    
    endpoint = "https://bef4a4bb93d1.ngrok-free.app"
    
    try:
        # Test /api/tags endpoint
        response = requests.get(f"{endpoint}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            print(f"✅ Direct Ollama connection SUCCESS")
            print(f"📊 Endpoint: {endpoint}")
            print(f"🤖 Available models: {len(models)}")
            for model in models:
                print(f"   - {model}")
            
            # Check if llama3.1:8b is available
            if "llama3.1:8b" in models:
                print("✅ Required model llama3.1:8b is available")
                return True
            else:
                print("⚠️ Warning: llama3.1:8b model not found")
                return False
        else:
            print(f"❌ Direct connection failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Direct connection error: {e}")
        return False

def test_ollama_service():
    """Test backend OllamaService with new endpoint"""
    print("\n🔍 Testing backend OllamaService...")
    
    try:
        # Import the service
        from src.services.ollama_service import OllamaService
        
        # Create service with new endpoint
        ollama_service = OllamaService()
        
        print(f"📊 Service URL: {ollama_service.base_url}")
        print(f"🤖 Default model: {ollama_service.default_model}")
        
        # Test health check
        health_check = ollama_service.check_connection()
        print(f"🏥 Health check: {health_check}")
        
        if health_check.get('healthy'):
            print("✅ Backend OllamaService connection SUCCESS")
            
            # Test getting available models
            models = ollama_service.get_available_models()
            print(f"🤖 Available models from service: {len(models)}")
            for model in models:
                print(f"   - {model}")
            
            # Test simple generation
            print("\n🧪 Testing response generation...")
            response = ollama_service.generate_casual_response("Hello, test message")
            
            if response and not response.get('error'):
                print(f"✅ Response generation SUCCESS")
                print(f"📝 Response: {response.get('response', '')[:100]}...")
                return True
            else:
                print(f"❌ Response generation failed: {response.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Backend service connection failed: {health_check.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Backend service error: {e}")
        return False

def test_backend_api():
    """Test backend API endpoints"""
    print("\n🔍 Testing backend API endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8001/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend health endpoint SUCCESS")
            print(f"📊 Health data: {json.dumps(health_data, indent=2)}")
        else:
            print(f"❌ Health endpoint failed: HTTP {response.status_code}")
            return False
        
        # Test a simple chat request to verify Ollama integration
        print("\n🧪 Testing chat endpoint with Ollama...")
        chat_response = requests.post(
            "http://localhost:8001/api/agent/chat",
            json={
                "message": "Hello, this is a test message",
                "task_id": "test_ollama_endpoint"
            },
            timeout=30
        )
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            print(f"✅ Chat endpoint SUCCESS")
            print(f"📝 Response: {chat_data.get('response', '')[:100]}...")
            print(f"🤖 Model used: {chat_data.get('model', 'Unknown')}")
            return True
        else:
            print(f"❌ Chat endpoint failed: HTTP {chat_response.status_code}")
            print(f"Error response: {chat_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Backend API error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing New Ollama Endpoint Configuration")
    print("=" * 50)
    
    results = []
    
    # Test 1: Direct Ollama connection
    results.append(test_ollama_direct())
    
    # Test 2: Backend OllamaService
    results.append(test_ollama_service())
    
    # Test 3: Backend API endpoints
    results.append(test_backend_api())
    
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS:")
    
    test_names = [
        "Direct Ollama Connection",
        "Backend OllamaService", 
        "Backend API Endpoints"
    ]
    
    all_passed = True
    for i, (name, passed) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! New Ollama endpoint is working correctly.")
        print(f"🔗 Endpoint: https://bef4a4bb93d1.ngrok-free.app")
        print(f"🤖 Model: llama3.1:8b")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())