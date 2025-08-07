#!/usr/bin/env python3
"""
🧪 SCRIPT DE TESTING PARA VERIFICAR LA EXTRACCIÓN INTELIGENTE DE QUERIES

Prueba la función mejorada de extracción de keywords para validar que
ahora genera queries inteligentes en lugar de "BUSCAR INFORMACIÓN" genéricos.
"""

import sys
import os

# Agregar el path del backend
sys.path.insert(0, '/app/backend/src')

from tools.unified_web_search_tool import UnifiedWebSearchTool

def test_query_extraction():
    """🧪 Test cases para verificar la extracción mejorada"""
    
    # Crear instancia de la herramienta
    web_search_tool = UnifiedWebSearchTool()
    
    # Casos de prueba que representan el problema original
    test_cases = [
        {
            'name': 'Problema Original - Selección Argentina',
            'input': 'Buscar información sobre la selección argentina de fútbol 2025 jugadores convocados',
            'expected_keywords': ['selección', 'argentina', 'fútbol', 'jugadores', '2025']
        },
        {
            'name': 'Problema Original - Inflación',
            'input': 'Investigar sobre la inflación en Argentina durante el año 2024',
            'expected_keywords': ['inflación', 'argentina', '2025']
        },
        {
            'name': 'Problema Original - Tecnología IA',
            'input': 'Obtener información específica sobre inteligencia artificial y machine learning',
            'expected_keywords': ['inteligencia', 'artificial', 'machine', 'learning']
        },
        {
            'name': 'Query Genérico Malo',
            'input': 'Buscar información sobre datos específicos necesarios para completar',
            'expected_keywords': ['noticias', 'actualidad', '2025']  # Debería usar fallback
        },
        {
            'name': 'Nombres Propios',
            'input': 'Investigar sobre Lionel Messi y el Inter Miami en 2025',
            'expected_keywords': ['lionel', 'messi', 'inter', 'miami', '2025']
        }
    ]
    
    print("🧪 TESTING EXTRACCIÓN INTELIGENTE DE QUERIES")
    print("=" * 60)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"  📝 Input Original: '{test_case['input']}'")
        
        # Extraer query inteligente
        smart_query = web_search_tool._extract_clean_keywords_static(test_case['input'])
        
        print(f"  🎯 Query Inteligente: '{smart_query}'")
        print(f"  📋 Keywords Esperados: {test_case['expected_keywords']}")
        
        # Analizar si mejora significativamente
        original_words = test_case['input'].lower().split()
        smart_words = smart_query.lower().split()
        
        # Verificar que eliminó palabras genéricas
        generic_removed = not any(word in smart_query.lower() for word in ['buscar', 'información', 'sobre', 'investigar', 'obtener', 'específica'])
        
        # Verificar que contiene algunos keywords esperados
        found_keywords = []
        for keyword in test_case['expected_keywords']:
            if keyword.lower() in smart_query.lower():
                found_keywords.append(keyword)
        
        print(f"  ✅ Eliminó palabras genéricas: {generic_removed}")
        print(f"  📊 Keywords encontrados: {found_keywords} ({len(found_keywords)}/{len(test_case['expected_keywords'])})")
        
        # Evaluar mejora
        if len(smart_query) < len(test_case['input']) * 0.7 and generic_removed:
            print(f"  🎉 MEJORADO: Query más específico y sin palabras genéricas")
        else:
            print(f"  ⚠️  REVISAR: Posible mejora adicional necesaria")
        
        print()

def compare_before_after():
    """🔄 Comparar método anterior vs nuevo"""
    
    print("\n🔄 COMPARACIÓN MÉTODO ANTERIOR vs NUEVO")
    print("=" * 60)
    
    test_queries = [
        "Buscar información sobre la selección argentina 2025",
        "Investigar sobre inteligencia artificial",
        "Obtener datos específicos sobre la inflación en Argentina"
    ]
    
    web_search_tool = UnifiedWebSearchTool()
    
    for query in test_queries:
        print(f"\n📝 Query Original: '{query}'")
        
        # Método anterior (simulado)
        old_method = query.replace('Buscar información sobre:', '').replace('Investigar:', '').strip()
        print(f"   🗑️  Método Anterior: '{old_method}'")
        
        # Nuevo método inteligente
        new_method = web_search_tool._extract_clean_keywords_static(query)
        print(f"   🧠 Método Nuevo: '{new_method}'")
        
        # Evaluar mejora
        if len(new_method) < len(old_method) and 'información' not in new_method:
            print("   ✅ MEJORA: Más específico y limpio")
        else:
            print("   ⚠️  Revisar: Posible mejora adicional")

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE EXTRACCIÓN DE QUERIES...")
    print()
    
    try:
        test_query_extraction()
        compare_before_after()
        
        print("\n" + "="*60)
        print("✅ TESTS COMPLETADOS")
        print("🎯 Si ves mejoras en la especificidad y eliminación de palabras genéricas,")
        print("   la implementación está funcionando correctamente.")
        
    except Exception as e:
        print(f"❌ Error durante testing: {str(e)}")
        import traceback
        traceback.print_exc()