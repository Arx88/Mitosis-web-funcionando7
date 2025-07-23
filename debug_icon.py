#!/usr/bin/env python3
"""
Debug test to see what icon is assigned and why
"""

import requests
import json

# Backend URL
BACKEND_URL = "http://localhost:8001"

def debug_icon_assignment():
    """Debug single test case"""
    
    task = "Buscar restaurantes en Valencia"
    print(f"🔍 Debugging: {task}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/chat",
            json={"message": task},
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            icon = data.get('plan', {}).get('suggested_icon', 'NOT_FOUND')
            print(f"✅ Response received")
            print(f"🎯 Assigned icon: {icon}")
            
            # Print full plan data for debugging
            plan = data.get('plan', {})
            print(f"📋 Plan title: {plan.get('title', 'N/A')}")
            print(f"📝 Plan description: {plan.get('description', 'N/A')[:100]}...")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    debug_icon_assignment()