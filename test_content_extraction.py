#!/usr/bin/env python3
"""
🔍 TEST DE EXTRACCIÓN DE CONTENIDO
Script para diagnosticar por qué no se está extrayendo contenido real
"""

import sys
import os
sys.path.append('/app/backend')

import asyncio
import json
from datetime import datetime
from backend.src.tools.tool_manager import ToolManager

async def test_content_extraction():
    """Test directo de extracción de contenido web"""
    
    print("🔍 INICIANDO TEST DE EXTRACCIÓN DE CONTENIDO")
    print("=" * 60)
    
    # Inicializar tool manager
    tool_manager = ToolManager()
    
    # Obtener herramienta web_search
    web_search_tool = tool_manager.get_tool('web_search')
    if not web_search_tool:
        print("❌ Error: Herramienta web_search no encontrada")
        return
    
    print("✅ Herramienta web_search encontrada")
    
    # Parámetros de prueba específicos para Javier Milei
    test_params = {
        'query': 'Javier Milei presidente Argentina 2024 biografía política',
        'max_results': 3,
        'search_engine': 'bing',
        'extract_content': True
    }
    
    # Configuración con task_id para testing
    test_config = {
        'task_id': 'test-extraction-' + str(int(datetime.now().timestamp()))
    }
    
    print(f"🚀 Ejecutando búsqueda con parámetros:")
    print(f"   Query: {test_params['query']}")
    print(f"   Max results: {test_params['max_results']}")
    print(f"   Extract content: {test_params['extract_content']}")
    print(f"   Task ID: {test_config['task_id']}")
    print()
    
    try:
        # Ejecutar herramienta
        print("⏳ Ejecutando herramienta web_search...")
        result = web_search_tool._execute_tool(test_params, test_config)
        
        print("✅ Ejecución completada")
        print(f"🎯 Éxito: {result.success}")
        print()
        
        if result.success and result.data:
            data = result.data
            results = data.get('results', []) or data.get('search_results', [])
            
            print(f"📊 RESULTADOS OBTENIDOS: {len(results)} resultados")
            print("=" * 50)
            
            for i, res in enumerate(results):
                print(f"\n🔍 RESULTADO {i+1}:")
                print(f"   Título: {res.get('title', 'Sin título')[:80]}...")
                print(f"   URL: {res.get('url', 'Sin URL')}")
                print(f"   Source: {res.get('source', 'Unknown')}")
                print(f"   Method: {res.get('method', 'Unknown')}")
                
                # ⚠️ ANÁLISIS CRÍTICO DEL CONTENIDO
                content_extracted = res.get('content_extracted', False)
                content_length = res.get('content_length', 0)
                content_preview = res.get('content_preview', '')
                
                print(f"   📄 Contenido extraído: {content_extracted}")
                print(f"   📏 Longitud contenido: {content_length}")
                
                if content_preview:
                    print(f"   🔍 Preview contenido: {content_preview[:100]}...")
                else:
                    print(f"   ❌ Sin preview de contenido")
                
                # Verificar navigation_data si existe
                nav_data = res.get('navigation_data', {})
                if nav_data:
                    print(f"   🌐 Navegación: páginas={nav_data.get('pages_visited', 0)}, screenshots={nav_data.get('screenshots_taken', 0)}")
                    print(f"   💾 Contenido real: {nav_data.get('has_real_content', False)}")
                
                print(f"   📝 Snippet: {res.get('snippet', 'Sin snippet')[:100]}...")
        else:
            print("❌ ERROR EN LA EJECUCIÓN")
            if hasattr(result, 'error'):
                print(f"   Error: {result.error}")
    
    except Exception as e:
        print(f"❌ EXCEPCIÓN DURANTE LA PRUEBA: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 DIAGNÓSTICO DE EXTRACCIÓN DE CONTENIDO WEB")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    asyncio.run(test_content_extraction())