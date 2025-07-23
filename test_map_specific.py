#!/usr/bin/env python3
"""
Test very specific map-related queries
"""

import requests
import json

BACKEND_URL = "http://localhost:8001"

def test_map_specific():
    """Test very specific map queries"""
    
    test_cases = [
        "Buscar restaurantes en Valencia",
        "Encontrar comida en Madrid", 
        "Localizar bares en Barcelona",
        "Ubicar lugares de valencia"
    ]
    
    print("🗺️ Testing Map-Specific Cases")
    print("=" * 40)
    
    for i, task in enumerate(test_cases, 1):
        print(f"\n{i}. {task}")
        
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
                result = "✅" if icon == "map" else "❌"
                print(f"   Icon: {icon} {result}")
            else:
                print(f"   Error: {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {str(e)}")

if __name__ == "__main__":
    test_map_specific()