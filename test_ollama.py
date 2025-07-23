#!/usr/bin/env python3
"""
Test Ollama service directly
"""

import requests
import json

def test_ollama():
    """Test if Ollama is working"""
    
    print("🔍 Testing Ollama Service")
    print("=" * 30)
    
    # Test if backend reports Ollama as healthy
    try:
        response = requests.get("http://localhost:8001/api/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Backend health: {health_data}")
            
            if 'ollama' in health_data:
                print(f"Ollama status: {health_data['ollama']}")
        else:
            print(f"Health check failed: {response.status_code}")
    except Exception as e:
        print(f"Health check error: {e}")
    
    # Test Ollama directly
    try:
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b-instruct-q4_K_M",
                "prompt": "Test message",
                "stream": False
            },
            timeout=10
        )
        
        if ollama_response.status_code == 200:
            print("✅ Ollama is responding directly")
        else:
            print(f"❌ Ollama direct test failed: {ollama_response.status_code}")
            
    except Exception as e:
        print(f"❌ Ollama direct test error: {e}")

if __name__ == "__main__":
    test_ollama()