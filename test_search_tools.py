#!/usr/bin/env python3
"""
Test específico de herramientas de búsqueda REAL
"""

import sys
sys.path.insert(0, '/app/backend')

def test_search_tools():
    print("🔍 TESTING HERRAMIENTAS DE BÚSQUEDA REAL")
    print("=" * 50)
    
    # Importar ToolManager directamente
    from src.tools.tool_manager import ToolManager
    
    tool_manager = ToolManager()
    
    # Listar herramientas disponibles
    available_tools = tool_manager.get_available_tools()
    print(f"📊 Herramientas disponibles: {len(available_tools)}")
    
    for tool in available_tools:
        name = tool['name']
        enabled = tool['enabled']
        print(f"   - {name}: {'✅ HABILITADO' if enabled else '❌ DESHABILITADO'}")
    
    # Test específico Tavily
    print(f"\n🧪 Test directo de Tavily:")
    if tool_manager.is_tool_enabled('tavily_search'):
        result = tool_manager.execute_tool(
            tool_name='tavily_search',
            parameters={
                'query': 'Python programming',
                'max_results': 3,
                'include_answer': True
            },
            config={'timeout': 30}
        )
        print(f"   Resultado Tavily: {result}")
    else:
        print("   ❌ Tavily no habilitado")
    
    # Test específico WebSearch
    print(f"\n🧪 Test directo de WebSearch:")
    if tool_manager.is_tool_enabled('web_search'):
        result = tool_manager.execute_tool(
            tool_name='web_search', 
            parameters={
                'query': 'Python programming',
                'max_results': 3
            },
            config={'timeout': 30}
        )
        print(f"   Resultado WebSearch: {result}")
    else:
        print("   ❌ WebSearch no habilitado")

if __name__ == "__main__":
    test_search_tools()