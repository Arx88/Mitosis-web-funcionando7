#!/usr/bin/env python3
"""
Test script to check icon assignment behavior in Mitosis
"""

import requests
import json
import time

# Backend URL
BACKEND_URL = "http://localhost:8001"

def is_icon_coherent(expected_category, assigned_icon):
    """Check if the assigned icon is coherent with the expected category"""
    
    category_mappings = {
        "code/development": ["code", "terminal", "database", "server", "smartphone", "monitor"],
        "document/writing": ["book", "file", "edit", "folder", "archive"],
        "search/location": ["search", "globe", "map", "compass", "navigation"],
        "analysis/data": ["chart", "calculator", "activity", "layers", "grid"],
        "creative/design": ["image", "lightbulb", "star", "camera", "video"],
        "research": ["search", "globe", "activity", "target", "compass"]
    }
    
    expected_icons = category_mappings.get(expected_category, [])
    return assigned_icon in expected_icons

def test_icon_assignment():
    """Test different types of tasks to see what icons are assigned"""
    
    test_cases = [
        {
            "task": "Crear una aplicación web con React",
            "expected_category": "code/development",
            "description": "Should get a code-related icon"
        },
        {
            "task": "Escribir un informe sobre marketing digital",
            "expected_category": "document/writing", 
            "description": "Should get a file/document icon"
        },
        {
            "task": "Buscar los mejores restaurantes en Valencia",
            "expected_category": "search/location",
            "description": "Should get a search or map icon"
        },
        {
            "task": "Analizar datos de ventas del último trimestre",
            "expected_category": "analysis/data",
            "description": "Should get a chart/analysis icon"
        },
        {
            "task": "Crear un diseño gráfico para una campaña",
            "expected_category": "creative/design",
            "description": "Should get an image/design icon"
        },
        {
            "task": "Hacer una investigación sobre inteligencia artificial",
            "expected_category": "research",
            "description": "Should get a search/research icon"
        }
    ]
    
    print("🧪 Testing Icon Assignment in Mitosis")
    print("=" * 50)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['task']}")
        print(f"   Expected: {test_case['expected_category']}")
        print(f"   Description: {test_case['description']}")
        
        try:
            # Send request to chat endpoint
            response = requests.post(
                f"{BACKEND_URL}/api/agent/chat",
                json={"message": test_case["task"]},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for icon information in the response
                suggested_icon = "NOT_FOUND"
                plan_data = None
                
                # Check if there's a plan with an icon
                if 'plan' in data and data['plan']:
                    plan_data = data['plan']
                    suggested_icon = plan_data.get('suggested_icon', 'NOT_FOUND')
                
                print(f"   ✅ Response received")
                print(f"   🎯 Assigned Icon: {suggested_icon}")
                
                # Store result
                results.append({
                    "task": test_case["task"],
                    "expected_category": test_case["expected_category"],
                    "assigned_icon": suggested_icon,
                    "full_plan": plan_data,
                    "coherent": is_icon_coherent(test_case["expected_category"], suggested_icon)
                })
                
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                results.append({
                    "task": test_case["task"],
                    "expected_category": test_case["expected_category"],
                    "assigned_icon": "ERROR",
                    "error": f"HTTP {response.status_code}"
                })
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                "task": test_case["task"],
                "expected_category": test_case["expected_category"],
                "assigned_icon": "ERROR",
                "error": str(e)
            })
        
        # Wait between requests
        time.sleep(2)
    
    # Analyze results
    print("\n" + "=" * 50)
    print("📊 ICON ASSIGNMENT ANALYSIS")
    print("=" * 50)
    
    coherent_count = 0
    total_successful = 0
    
    for result in results:
        if result["assigned_icon"] not in ["ERROR", "NOT_FOUND"]:
            total_successful += 1
            coherence = is_icon_coherent(result["expected_category"], result["assigned_icon"])
            if coherence:
                coherent_count += 1
            
            print(f"\n📝 Task: {result['task'][:50]}...")
            print(f"   Expected: {result['expected_category']}")
            print(f"   Assigned: {result['assigned_icon']}")
            print(f"   Coherent: {'✅ YES' if coherence else '❌ NO'}")
    
    if total_successful > 0:
        coherence_rate = (coherent_count / total_successful) * 100
        print(f"\n🎯 COHERENCE RATE: {coherence_rate:.1f}% ({coherent_count}/{total_successful})")
        
        if coherence_rate < 70:
            print("⚠️  LOW COHERENCE DETECTED - Icons are not being assigned coherently!")
        else:
            print("✅ Good coherence rate")
    else:
        print("❌ No successful icon assignments detected")
    
    # Save results to file
    with open("/app/icon_assignment_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: /app/icon_assignment_test_results.json")

if __name__ == "__main__":
    test_icon_assignment()