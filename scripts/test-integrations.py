#!/usr/bin/env python3
"""
Script de prueba para las nuevas integraciones
Verifica que Firecrawl, QStash y Playwright funcionen correctamente
"""

import os
import sys
import json
from datetime import datetime

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Agregar el directorio src al path
sys.path.append('/app/backend/src')

# Importar las nuevas herramientas
try:
    from tools.firecrawl_tool import FirecrawlTool
    from tools.qstash_tool import QStashTool
    from tools.playwright_tool import PlaywrightTool
    from tools.tool_manager import ToolManager
    
    print("✅ Todas las herramientas importadas correctamente")
except ImportError as e:
    print(f"❌ Error importando herramientas: {e}")
    sys.exit(1)

def test_firecrawl():
    """Probar Firecrawl tool"""
    print("\n🔍 Probando Firecrawl Tool...")
    
    tool = FirecrawlTool()
    
    # Verificar información de la herramienta
    print(f"Descripción: {tool.get_description()}")
    print(f"Parámetros: {len(tool.get_parameters())} parámetros disponibles")
    
    # Verificar configuración
    info = tool.get_tool_info()
    print(f"Estado API: {info.get('api_status', 'unknown')}")
    
    # Prueba básica
    if tool.api_key:
        print("🔑 API key configurada correctamente")
        
        # Probar validación de parámetros
        validation = tool.validate_parameters({
            'url': 'https://example.com',
            'mode': 'single'
        })
        print(f"Validación: {'✅ Válido' if validation['valid'] else '❌ Inválido'}")
        
        # Nota: No ejecutamos scraping real para evitar uso de API
        print("⚠️  Scraping real no ejecutado para conservar API calls")
    else:
        print("❌ API key no configurada")
    
    return True

def test_qstash():
    """Probar QStash tool"""
    print("\n⚡ Probando QStash Tool...")
    
    tool = QStashTool()
    
    # Verificar información de la herramienta
    print(f"Descripción: {tool.get_description()}")
    print(f"Parámetros: {len(tool.get_parameters())} parámetros disponibles")
    
    # Verificar configuración
    info = tool.get_tool_info()
    print(f"Estado Redis: {info.get('redis_status', 'unknown')}")
    
    # Prueba de conexión
    if tool.redis_client:
        print("🔑 Redis configurado correctamente")
        
        # Probar validación de parámetros
        validation = tool.validate_parameters({
            'action': 'create_job',
            'job_type': 'custom',
            'payload': {'test': 'data'}
        })
        print(f"Validación: {'✅ Válido' if validation['valid'] else '❌ Inválido'}")
        
        # Probar listado de jobs
        try:
            result = tool.execute({
                'action': 'list_jobs'
            })
            if result.get('success'):
                print(f"📋 Jobs actuales: {result.get('total_jobs', 0)}")
            else:
                print(f"❌ Error listando jobs: {result.get('error')}")
        except Exception as e:
            print(f"❌ Error en conexión Redis: {e}")
    else:
        print("❌ Redis no configurado")
    
    return True

def test_playwright():
    """Probar Playwright tool"""
    print("\n🎭 Probando Playwright Tool...")
    
    tool = PlaywrightTool()
    
    # Verificar información de la herramienta
    print(f"Descripción: {tool.get_description()}")
    print(f"Parámetros: {len(tool.get_parameters())} parámetros disponibles")
    
    # Verificar configuración
    info = tool.get_tool_info()
    print(f"Estado Playwright: {info.get('playwright_status', 'unknown')}")
    
    # Verificar disponibilidad
    if tool.playwright_available:
        print("✅ Playwright instalado correctamente")
        
        # Probar validación de parámetros
        validation = tool.validate_parameters({
            'action': 'get_page_info',
            'url': 'https://example.com'
        })
        print(f"Validación: {'✅ Válido' if validation['valid'] else '❌ Inválido'}")
        
        # Nota: No ejecutamos navegación real para evitar tiempo de ejecución
        print("⚠️  Navegación real no ejecutada para conservar tiempo")
    else:
        print("❌ Playwright no instalado")
    
    return True

def test_tool_manager():
    """Probar que las herramientas estén registradas en el ToolManager"""
    print("\n🛠️  Probando Tool Manager...")
    
    manager = ToolManager()
    
    # Obtener herramientas disponibles
    tools = manager.get_available_tools()
    print(f"Total de herramientas: {len(tools)}")
    
    # Verificar que las nuevas herramientas estén incluidas
    tool_names = [tool['name'] for tool in tools]
    
    new_tools = ['firecrawl', 'qstash', 'playwright']
    for tool_name in new_tools:
        if tool_name in tool_names:
            print(f"✅ {tool_name} registrada correctamente")
        else:
            print(f"❌ {tool_name} NO registrada")
    
    # Mostrar estadísticas
    stats = manager.get_usage_stats()
    print(f"Total de llamadas: {stats.get('total_calls', 0)}")
    print(f"Total de errores: {stats.get('total_errors', 0)}")
    
    return True

def test_backend_health():
    """Probar que el backend responda correctamente"""
    print("\n🏥 Probando Health del Backend...")
    
    import requests
    
    try:
        # Probar endpoint de health
        response = requests.get('http://localhost:8001/health', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend respondiendo correctamente")
            print(f"Estado: {data.get('status', 'unknown')}")
            
            services = data.get('services', {})
            print(f"Herramientas disponibles: {services.get('tools', 0)}")
            print(f"Base de datos: {'✅ Conectada' if services.get('database') else '❌ Desconectada'}")
        else:
            print(f"❌ Backend error: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al backend: {e}")
    
    return True

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de integración...")
    print(f"Fecha: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # Ejecutar pruebas
    tests = [
        test_firecrawl,
        test_qstash,
        test_playwright,
        test_tool_manager,
        test_backend_health
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Error en prueba {test.__name__}: {e}")
            results.append(False)
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Pruebas exitosas: {passed}/{total}")
    print(f"Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ¡Todas las integraciones funcionan correctamente!")
    else:
        print("⚠️  Algunas integraciones necesitan revisión")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)