#!/usr/bin/env python3
"""
🔍 TEST DE EXTRACCIÓN DE CONTENIDO - VERSIÓN DIRECTA
Script para diagnosticar por qué no se está extrayendo contenido real
"""

import sys
import os
sys.path.append('/app/backend')

import asyncio
import json
from datetime import datetime

async def test_content_extraction_direct():
    """Test directo de extracción de contenido web"""
    
    print("🔍 INICIANDO TEST DIRECTO DE EXTRACCIÓN DE CONTENIDO")
    print("=" * 60)
    
    try:
        # Importar directamente la herramienta
        from backend.src.tools.unified_web_search_tool import UnifiedWebSearchTool
        
        # Crear instancia de la herramienta
        web_search_tool = UnifiedWebSearchTool()
        print("✅ Herramienta UnifiedWebSearchTool creada")
        
        # Parámetros de prueba específicos para Javier Milei FORZANDO SITIOS REALES
        test_params = {
            'query': 'Javier Milei presidente Argentina biografía site:wikipedia.org OR site:clarin.com OR site:infobae.com',
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
        print(f"   Task ID: {test_config['task_id']}")
        print()
        
        # Ejecutar herramienta
        print("⏳ Ejecutando herramienta web_search...")
        result = web_search_tool._execute_tool(test_params, test_config)
        
        print("✅ Ejecución completada")
        print(f"🎯 Éxito: {result.success}")
        
        if not result.success:
            print(f"❌ Error: {result.error if hasattr(result, 'error') else 'Error desconocido'}")
            return
        
        print()
        
        if result.success and result.data:
            data = result.data
            results = data.get('results', []) or data.get('search_results', [])
            
            print(f"📊 RESULTADOS OBTENIDOS: {len(results)} resultados")
            print("=" * 50)
            
            for i, res in enumerate(results):
                print(f"\n🔍 RESULTADO {i+1}:")
                print(f"   Título: {res.get('title', 'Sin título')}")
                print(f"   URL: {res.get('url', 'Sin URL')}")
                print(f"   Method: {res.get('method', 'Unknown')}")
                
                # ⚠️ ANÁLISIS CRÍTICO DEL CONTENIDO
                content_extracted = res.get('content_extracted', False)
                content_length = res.get('content_length', 0)
                content_preview = res.get('content_preview', '')
                
                print(f"   📄 Contenido extraído: {content_extracted}")
                print(f"   📏 Longitud contenido: {content_length}")
                
                if content_preview and len(content_preview) > 10:
                    print(f"   🔍 Preview contenido ({len(content_preview)} chars):")
                    print(f"       {content_preview[:150]}...")
                    print("   ✅ CONTENIDO REAL ENCONTRADO!")
                else:
                    print(f"   ❌ SIN CONTENIDO REAL - Solo metadatos")
                
                # Verificar navigation_data si existe
                nav_data = res.get('navigation_data', {})
                if nav_data:
                    print(f"   🌐 Navegación: páginas={nav_data.get('pages_visited', 0)}, screenshots={nav_data.get('screenshots_taken', 0)}")
                    print(f"   💾 Contenido real: {nav_data.get('has_real_content', False)}")
                
                snippet = res.get('snippet', '')
                if snippet and len(snippet) > 50:
                    print(f"   📝 Snippet ({len(snippet)} chars): {snippet[:100]}...")
                else:
                    print(f"   📝 Snippet muy corto o vacío")
                
                # Diagnóstico específico
                if not content_extracted or content_length == 0:
                    print(f"   🚨 PROBLEMA: No se extrajo contenido real de esta página")
                    
                if 'real_time_navigation' in res:
                    print(f"   ⏱️ Navegación tiempo real: {res['real_time_navigation']}")
                    
                if 'screenshot_captured' in res:
                    print(f"   📸 Screenshot capturado: {res['screenshot_captured']}")
    
    except Exception as e:
        print(f"❌ EXCEPCIÓN DURANTE LA PRUEBA: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 DIAGNÓSTICO DIRECTO DE EXTRACCIÓN DE CONTENIDO WEB")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    asyncio.run(test_content_extraction_direct())