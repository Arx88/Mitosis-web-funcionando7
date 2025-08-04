#!/usr/bin/env python3
"""
🧪 TEST DIRECTO DE BROWSER-USE CON NAVEGACIÓN VISUAL
Verificar si la corrección implementada está funcionando
"""

import asyncio
import os
import sys
sys.path.insert(0, '/app/backend')

from src.tools.unified_web_search_tool import UnifiedWebSearchTool

async def test_browser_use_visual():
    """Test directo de navegación visual"""
    print("🚀 INICIANDO TEST DE NAVEGACIÓN VISUAL BROWSER-USE")
    print("="*60)
    
    # Crear instancia de la herramienta
    tool = UnifiedWebSearchTool()
    
    # Parámetros de prueba
    test_params = {
        'query': 'robótica avanzada 2025',
        'max_results': 3,
        'search_engine': 'bing',
        'extract_content': True
    }
    
    # Config con task_id para WebSocket
    test_config = {
        'task_id': 'test-visual-navigation-1234'
    }
    
    print(f"📝 Query: {test_params['query']}")
    print(f"📝 Task ID: {test_config['task_id']}")
    print(f"📝 Motor: {test_params['search_engine']}")
    print("="*60)
    
    try:
        # Ejecutar la herramienta con navegación visual
        print("🔍 Ejecutando herramienta con navegación visual...")
        result = tool._execute_tool(test_params, test_config)
        
        print("="*60)
        print("📊 RESULTADOS DEL TEST:")
        print(f"✅ Éxito: {result.success}")
        
        if result.success and result.data:
            print(f"📈 Resultados encontrados: {result.data.get('results_count', 0)}")
            print(f"🎭 Visualización habilitada: {result.data.get('visualization_enabled', False)}")
            print(f"📸 Screenshots generados: {result.data.get('screenshots_generated', False)}")
            print(f"🔧 Motor usado: {result.data.get('search_engine')}")
            
            # Mostrar algunos resultados
            if result.data.get('results'):
                print("\n🔍 MUESTRA DE RESULTADOS:")
                for i, res in enumerate(result.data['results'][:2]):
                    print(f"  {i+1}. {res.get('title', 'Sin título')[:60]}...")
                    print(f"     URL: {res.get('url', 'Sin URL')}")
                    print(f"     Método: {res.get('method', 'desconocido')}")
                    print()
        
        else:
            print(f"❌ Error: {result.error}")
        
    except Exception as e:
        print(f"❌ EXCEPCIÓN DURANTE TEST: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("="*60)
    print("🏁 TEST COMPLETADO")

if __name__ == "__main__":
    # Ejecutar test async
    asyncio.run(test_browser_use_visual())