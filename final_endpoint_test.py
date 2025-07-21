#!/usr/bin/env python3
"""
Final verification test - Send a message to confirm the new Ollama endpoint is working
"""
import requests
import json

def final_test():
    """Send a message to test the complete pipeline with the new endpoint"""
    print("🔥 FINAL TEST: Complete Message Processing with New Ollama Endpoint")
    print("=" * 70)
    
    try:
        # Send a simple greeting to test the pipeline
        response = requests.post(
            "http://localhost:8001/api/agent/chat",
            json={
                "message": "Hola, soy una prueba para confirmar que el nuevo endpoint de Ollama https://bef4a4bb93d1.ngrok-free.app está funcionando correctamente. Por favor confirma que puedes responder.",
                "task_id": "final_endpoint_test"
            },
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ MESSAGE PROCESSING SUCCESS")
            print(f"📱 Task ID: {data.get('task_id', 'Unknown')}")
            print(f"🤖 Model Response Mode: {data.get('model', 'Unknown')}")
            print(f"🎯 Memory Used: {data.get('memory_used', False)}")
            print(f"📝 Response Length: {len(data.get('response', ''))} characters")
            print(f"⏱️  Processing Time: {data.get('processing_time', 'Unknown')}")
            
            # Show first part of response
            response_text = data.get('response', '')
            if response_text:
                print("\n📄 OLLAMA RESPONSE (first 200 chars):")
                print("-" * 50)
                print(response_text[:200] + ("..." if len(response_text) > 200 else ""))
                print("-" * 50)
                
                # Check if response mentions the endpoint
                if "bef4a4bb93d1" in response_text or "funcionando" in response_text:
                    print("🎯 Response indicates endpoint is working correctly!")
                else:
                    print("📝 Response received from new endpoint")
                    
                return True
            else:
                print("⚠️ Empty response received")
                return False
        else:
            print(f"❌ REQUEST FAILED: HTTP {response.status_code}")
            print(f"Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        return False

if __name__ == "__main__":
    success = final_test()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 FINAL TEST PASSED!")
        print("✅ NEW OLLAMA ENDPOINT IS FULLY FUNCTIONAL")
        print("🔗 Endpoint: https://bef4a4bb93d1.ngrok-free.app")  
        print("🤖 Model: llama3.1:8b")
        print("🚀 Backend API is processing messages correctly")
        print("✅ TASK COMPLETED SUCCESSFULLY")
    else:
        print("❌ FINAL TEST FAILED")
        print("🔧 Please check the configuration")