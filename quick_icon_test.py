#!/usr/bin/env python3
"""
Quick test to see icon assignment improvements
"""

import requests
import json

# Backend URL
BACKEND_URL = "http://localhost:8001"

def quick_test():
    """Quick test of 3 key scenarios"""
    
    test_cases = [
        {"task": "Crear una aplicación web", "expected": "code"},
        {"task": "Analizar datos de ventas", "expected": "chart"},
        {"task": "Buscar restaurantes en Valencia", "expected": "map"}
    ]
    
    print("🧪 Quick Icon Test")
    print("=" * 30)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Task: {test['task']}")
        print(f"   Expected: {test['expected']}")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/agent/chat",
                json={"message": test["task"]},
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                icon = data.get('plan', {}).get('suggested_icon', 'NOT_FOUND')
                match = "✅" if icon == test['expected'] else "❌"
                print(f"   Assigned: {icon} {match}")
            else:
                print(f"   Error: {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {str(e)}")

if __name__ == "__main__":
    quick_test()