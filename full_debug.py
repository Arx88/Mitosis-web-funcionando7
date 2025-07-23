#!/usr/bin/env python3
"""
Full debug test to see the complete process
"""

import requests
import json

BACKEND_URL = "http://localhost:8001"

def full_debug():
    """Full debugging with detailed response analysis"""
    
    task = "Buscar restaurantes en Valencia"
    print(f"🔍 Full Debug: {task}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/chat",
            json={"message": task},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("=" * 60)
            print("📄 FULL RESPONSE:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=" * 60)
            
            # Extract specific info
            if 'plan' in data:
                plan = data['plan']
                print(f"📋 Plan exists: {plan is not None}")
                if plan:
                    print(f"🎯 Suggested icon in plan: {plan.get('suggested_icon', 'NOT_FOUND')}")
                    print(f"📝 Plan keys: {list(plan.keys())}")
            else:
                print("❌ No 'plan' key in response")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    full_debug()