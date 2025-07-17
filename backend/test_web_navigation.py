#!/usr/bin/env python3
"""
Test para verificar que la navegación web autónoma funcione correctamente
"""

import sys
import os
sys.path.append('/app/backend/src')

from tools.autonomous_web_navigation import AutonomousWebNavigation
from tools.tool_manager import ToolManager

def test_autonomous_web_navigation():
    """
    Test básico para verificar que la navegación web autónoma funcione
    """
    print("🧪 === TEST NAVEGACIÓN WEB AUTÓNOMA ===")
    
    # Inicializar herramienta
    nav_tool = AutonomousWebNavigation()
    
    # Verificar que la herramienta esté disponible
    print(f"✅ Herramienta inicializada: {nav_tool.name}")
    print(f"📝 Descripción: {nav_tool.get_description()}")
    
    # Verificar parámetros
    params = nav_tool.get_parameters()
    print(f"🔧 Parámetros disponibles: {len(params)}")
    
    # Test con tarea simple
    test_parameters = {
        'task_description': 'Navegar a google.com y tomar un screenshot',
        'constraints': {
            'max_steps': 5,
            'timeout_per_step': 10,
            'screenshot_frequency': 'every_step'
        }
    }
    
    print(f"🎯 Ejecutando test con parámetros: {test_parameters}")
    
    try:
        # Ejecutar navegación
        result = nav_tool.execute(test_parameters)
        
        if result.get('success'):
            print(f"✅ Test exitoso!")
            print(f"📊 Pasos completados: {result.get('completed_steps', 'N/A')}")
            print(f"📈 Tasa de éxito: {result.get('success_rate', 'N/A')}")
            print(f"🖼️ Screenshots: {len(result.get('screenshots', []))}")
        else:
            print(f"❌ Test falló: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Error ejecutando test: {e}")
    
    return result

def test_tool_manager_integration():
    """
    Test para verificar que ToolManager tenga la herramienta registrada
    """
    print("\n🧪 === TEST INTEGRACIÓN TOOL MANAGER ===")
    
    tool_manager = ToolManager()
    
    # Verificar herramientas disponibles
    available_tools = tool_manager.get_available_tools()
    print(f"🔧 Herramientas disponibles: {len(available_tools)}")
    
    # Buscar herramienta de navegación web
    nav_tool_found = False
    for tool in available_tools:
        if tool['name'] == 'autonomous_web_navigation':
            nav_tool_found = True
            print(f"✅ Herramienta encontrada: {tool['name']}")
            print(f"📝 Descripción: {tool['description']}")
            print(f"🟢 Habilitada: {tool['enabled']}")
            break
    
    if not nav_tool_found:
        print("❌ Herramienta de navegación web no encontrada en ToolManager")
        return False
    
    # Test de ejecución a través de ToolManager
    print("\n🎯 Ejecutando a través de ToolManager...")
    
    test_parameters = {
        'task_description': 'Navegar a example.com',
        'constraints': {
            'max_steps': 3,
            'timeout_per_step': 5
        }
    }
    
    try:
        result = tool_manager.execute_tool(
            'autonomous_web_navigation', 
            test_parameters,
            config={'timeout': 30}
        )
        
        if result.get('success'):
            print("✅ Ejecución a través de ToolManager exitosa")
            return True
        else:
            print(f"❌ Fallo en ejecución: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"💥 Error en ejecución: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando tests de navegación web autónoma...")
    
    # Test 1: Herramienta directa
    test_autonomous_web_navigation()
    
    # Test 2: Integración con ToolManager
    test_tool_manager_integration()
    
    print("\n✅ Tests completados")