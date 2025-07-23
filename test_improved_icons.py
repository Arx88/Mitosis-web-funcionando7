#!/usr/bin/env python3
"""
Test script to verify the improved icon assignment coherence in Mitosis
"""

import requests
import json
import time

# Backend URL
BACKEND_URL = "http://localhost:8001"

def test_improved_icon_coherence():
    """Test the improved icon assignment system"""
    
    test_cases = [
        {
            "task": "Crear una aplicación web con React y backend en Python",
            "expected_icon": "code",
            "category": "Development"
        },
        {
            "task": "Desarrollar una base de datos para usuarios",
            "expected_icon": "database", 
            "category": "Development/Database"
        },
        {
            "task": "Analizar datos de ventas del último trimestre",
            "expected_icon": "chart",
            "category": "Data Analysis"
        },
        {
            "task": "Crear un diseño gráfico para una campaña publicitaria",
            "expected_icon": "image",
            "category": "Creative/Design"
        },
        {
            "task": "Buscar información sobre restaurantes en Valencia",
            "expected_icon": "map",
            "category": "Location/Search"
        },
        {
            "task": "Escribir un informe de marketing digital",
            "expected_icon": "file",
            "category": "Documents"
        },
        {
            "task": "Crear estrategia de negocio para empresa",
            "expected_icon": "briefcase",
            "category": "Business"
        },
        {
            "task": "Hacer un video promocional",
            "expected_icon": "video",
            "category": "Multimedia"
        },
        {
            "task": "Investigar sobre inteligencia artificial",
            "expected_icon": "search",
            "category": "Research"
        },
        {
            "task": "Enviar correos a clientes potenciales",
            "expected_icon": "mail",
            "category": "Communication"
        }
    ]
    
    print("🔧 Testing IMPROVED Icon Assignment System")
    print("=" * 60)
    
    results = []
    correct_assignments = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['task']}")
        print(f"   Category: {test_case['category']}")
        print(f"   Expected: {test_case['expected_icon']}")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/agent/chat",
                json={"message": test_case["task"]},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                assigned_icon = "NOT_FOUND"
                
                if 'plan' in data and data['plan']:
                    assigned_icon = data['plan'].get('suggested_icon', 'NOT_FOUND')
                
                is_correct = assigned_icon == test_case['expected_icon']
                if is_correct:
                    correct_assignments += 1
                
                print(f"   ✅ Assigned: {assigned_icon}")
                print(f"   🎯 Correct: {'✅ YES' if is_correct else '❌ NO'}")
                
                results.append({
                    "task": test_case["task"],
                    "category": test_case["category"],
                    "expected_icon": test_case["expected_icon"],
                    "assigned_icon": assigned_icon,
                    "correct": is_correct
                })
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
        time.sleep(1)
    
    # Final analysis
    total_tests = len(test_cases)
    coherence_rate = (correct_assignments / total_tests) * 100
    
    print("\n" + "=" * 60)
    print("📊 IMPROVED ICON ASSIGNMENT RESULTS")
    print("=" * 60)
    
    print(f"\n🎯 ACCURACY RATE: {coherence_rate:.1f}% ({correct_assignments}/{total_tests})")
    
    if coherence_rate >= 90:
        print("🎉 EXCELLENT! Icon assignment is highly coherent!")
    elif coherence_rate >= 70:
        print("✅ GOOD! Icon assignment is mostly coherent")
    elif coherence_rate >= 50:
        print("⚠️  FAIR - Some improvements still needed")
    else:
        print("❌ POOR - Major issues remain")
    
    # Show incorrect assignments
    incorrect = [r for r in results if not r['correct']]
    if incorrect:
        print(f"\n❌ INCORRECT ASSIGNMENTS ({len(incorrect)}):")
        for inc in incorrect:
            print(f"   - {inc['task'][:40]}...")
            print(f"     Expected: {inc['expected_icon']}, Got: {inc['assigned_icon']}")
    else:
        print("\n🎉 ALL ASSIGNMENTS WERE CORRECT!")
    
    # Save results
    with open("/app/improved_icon_test_results.json", "w") as f:
        json.dump({
            "coherence_rate": coherence_rate,
            "correct_assignments": correct_assignments,
            "total_tests": total_tests,
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: /app/improved_icon_test_results.json")
    return coherence_rate

if __name__ == "__main__":
    rate = test_improved_icon_coherence()
    
    if rate >= 80:
        print("\n🎉 SUCCESS: Icon coherence problem has been RESOLVED!")
    else:
        print(f"\n⚠️  PARTIAL SUCCESS: Coherence improved but still needs work (current: {rate:.1f}%)")