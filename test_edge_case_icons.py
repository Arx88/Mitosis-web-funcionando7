#!/usr/bin/env python3
"""
Advanced test script to find incoherent icon assignments in Mitosis
"""

import requests
import json
import time

# Backend URL
BACKEND_URL = "http://localhost:8001"

def test_edge_cases():
    """Test edge cases that might reveal incoherent icon assignments"""
    
    edge_test_cases = [
        {
            "task": "Crea algo increíble hoy",
            "description": "Very generic task - should get generic icon",
            "expected_patterns": ["target", "lightbulb", "star"]
        },
        {
            "task": "Ayúdame con mi proyecto",
            "description": "Vague request - icon assignment might be random",
            "expected_patterns": ["target", "lightbulb", "briefcase"]
        },
        {
            "task": "Haz análisis de mercado para restaurantes en Valencia con datos",
            "description": "Mixed keywords - chart vs map confusion possible",
            "expected_patterns": ["chart", "map", "activity"]
        },
        {
            "task": "Necesito programar una web que analice imágenes",
            "description": "Multiple categories - code vs image confusion",
            "expected_patterns": ["code", "image", "terminal"]
        },
        {
            "task": "Construir aplicación móvil para buscar música",
            "description": "Multiple contexts - smartphone vs music confusion",
            "expected_patterns": ["smartphone", "music", "code"]
        },
        {
            "task": "Escribir código para crear documentos automáticamente",
            "description": "Code + document - potential confusion",
            "expected_patterns": ["code", "file", "terminal"]
        },
        {
            "task": "Investiga y desarrolla una solución de base de datos",
            "description": "Research + database - potential confusion", 
            "expected_patterns": ["database", "search", "server"]
        },
        {
            "task": "Hola, ¿puedes ayudarme?",
            "description": "Casual greeting - should get fallback",
            "expected_patterns": ["target", "message", "lightbulb"]
        },
        {
            "task": "🚀 Crear dashboard web para visualizar datos de ventas con gráficos interactivos",
            "description": "Complex task with emojis",
            "expected_patterns": ["chart", "code", "activity"]
        },
        {
            "task": "hacer algo random lol",
            "description": "Very informal and vague",
            "expected_patterns": ["target", "lightbulb"]
        }
    ]
    
    print("🔍 Testing Edge Cases for Icon Assignment")
    print("=" * 60)
    
    results = []
    inconsistent_assignments = []
    
    for i, test_case in enumerate(edge_test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['task']}")
        print(f"   Expected patterns: {test_case['expected_patterns']}")
        print(f"   Description: {test_case['description']}")
        
        # Run the same task multiple times to check for consistency
        icons_received = []
        
        for run in range(3):  # Run each test 3 times
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/agent/chat",
                    json={"message": test_case["task"]},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    suggested_icon = "NOT_FOUND"
                    if 'plan' in data and data['plan']:
                        suggested_icon = data['plan'].get('suggested_icon', 'NOT_FOUND')
                    
                    icons_received.append(suggested_icon)
                    print(f"   Run {run + 1}: {suggested_icon}")
                
                time.sleep(1)  # Short wait between runs
                
            except Exception as e:
                print(f"   Run {run + 1}: ERROR - {str(e)}")
                icons_received.append("ERROR")
        
        # Analyze consistency
        unique_icons = list(set(icons_received))
        is_consistent = len(unique_icons) == 1
        is_coherent = any(icon in test_case['expected_patterns'] for icon in icons_received if icon not in ['ERROR', 'NOT_FOUND'])
        
        result = {
            "task": test_case["task"],
            "description": test_case["description"],
            "expected_patterns": test_case["expected_patterns"],
            "icons_received": icons_received,
            "unique_icons": unique_icons,
            "is_consistent": is_consistent,
            "is_coherent": is_coherent
        }
        
        results.append(result)
        
        print(f"   📊 Consistency: {'✅ YES' if is_consistent else '❌ NO'}")
        print(f"   🎯 Coherence: {'✅ YES' if is_coherent else '❌ NO'}")
        
        if not is_consistent or not is_coherent:
            inconsistent_assignments.append(result)
    
    # Final analysis
    print("\n" + "=" * 60)
    print("📊 EDGE CASE ANALYSIS RESULTS")
    print("=" * 60)
    
    consistent_count = sum(1 for r in results if r['is_consistent'])
    coherent_count = sum(1 for r in results if r['is_coherent'])
    total_tests = len(results)
    
    print(f"\n🎯 CONSISTENCY RATE: {(consistent_count/total_tests)*100:.1f}% ({consistent_count}/{total_tests})")
    print(f"🎯 COHERENCE RATE: {(coherent_count/total_tests)*100:.1f}% ({coherent_count}/{total_tests})")
    
    if inconsistent_assignments:
        print(f"\n⚠️  PROBLEMATIC ASSIGNMENTS FOUND: {len(inconsistent_assignments)}")
        for prob in inconsistent_assignments:
            print(f"\n❌ Task: {prob['task'][:50]}...")
            print(f"   Expected: {prob['expected_patterns']}")
            print(f"   Received: {prob['icons_received']}")
            print(f"   Issues: {'Inconsistent' if not prob['is_consistent'] else ''} {'Incoherent' if not prob['is_coherent'] else ''}")
    else:
        print("\n✅ No problematic assignments found in edge cases")
    
    # Save detailed results
    with open("/app/edge_case_icon_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: /app/edge_case_icon_test_results.json")
    
    return inconsistent_assignments

if __name__ == "__main__":
    problems = test_edge_cases()
    
    if problems:
        print("\n🔧 RECOMMENDATION: Icon assignment needs improvement for:")
        for prob in problems:
            print(f"   - {prob['task'][:60]}...")
    else:
        print("\n✅ Icon assignment appears to be working correctly!")