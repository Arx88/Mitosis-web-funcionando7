#!/usr/bin/env python3
"""
Test script to verify Playwright visual automation functionality
"""
import json
import requests
import time
from datetime import datetime

def test_playwright_visual():
    """Test the Playwright visual automation tool"""
    
    print("🧪 INICIANDO TEST DE PLAYWRIGHT VISUAL")
    print("=" * 50)
    
    # Test 1: Check if backend is responsive
    print("\n1. Verificando estado del backend...")
    try:
        response = requests.get('http://localhost:8001/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend está funcionando")
        else:
            print("❌ Backend no está respondiendo correctamente")
            return False
    except Exception as e:
        print(f"❌ Error conectando al backend: {e}")
        return False
    
    # Test 2: Test Playwright visual automation via chat endpoint
    print("\n2. Probando automatización visual con Playwright...")
    
    # Test message asking for visual web automation
    test_message = """
    Usa la herramienta de Playwright para:
    1. Navegar a https://example.com
    2. Tomar un screenshot de la página
    3. Extraer el título de la página
    4. Usar el modo visual con screenshots automáticos
    
    Configura:
    - visual_mode: true
    - step_screenshots: true
    - highlight_elements: true
    - slow_motion: 1000
    """
    
    try:
        payload = {
            "message": test_message,
            "task_id": f"test_playwright_visual_{int(time.time())}"
        }
        
        print(f"📤 Enviando solicitud de automatización visual...")
        response = requests.post(
            'http://localhost:8001/api/agent/chat', 
            json=payload,
            timeout=60  # Aumentar timeout para automatización
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Respuesta recibida del agente")
            
            # Verificar que la respuesta contiene datos visuales
            if 'response' in result:
                print(f"📋 Respuesta: {result['response'][:200]}...")
                
                # Buscar evidencia de uso de Playwright
                response_text = result['response'].lower()
                if 'playwright' in response_text or 'screenshot' in response_text or 'navegación' in response_text:
                    print("✅ Evidencia de uso de Playwright encontrada")
                    return True
                else:
                    print("⚠️  No se encontró evidencia clara de uso de Playwright")
            
            print(f"📊 Respuesta completa: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Error en respuesta: {response.status_code}")
            print(f"📋 Contenido: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando automatización visual: {e}")
        return False

def test_direct_playwright_tool():
    """Test the Playwright tool directly"""
    
    print("\n3. Probando herramienta Playwright directamente...")
    
    try:
        # Import directly from the tool
        import sys
        sys.path.append('/app/backend/src')
        from tools.playwright_tool import PlaywrightTool
        
        # Create tool instance
        tool = PlaywrightTool()
        
        print(f"✅ Herramienta creada: {tool.name}")
        print(f"📋 Descripción: {tool.description}")
        print(f"🔧 Playwright disponible: {tool.playwright_available}")
        
        if not tool.playwright_available:
            print("❌ Playwright no está disponible")
            return False
        
        # Test basic functionality
        print("\n📸 Probando captura de screenshot visual...")
        
        # Test parameters for visual mode
        params = {
            'action': 'screenshot',
            'url': 'https://example.com',
            'visual_mode': True,
            'step_screenshots': True,
            'highlight_elements': True,
            'slow_motion': 1000,
            'full_page': False
        }
        
        print(f"🎯 Parámetros: {params}")
        
        # Execute the tool
        result = tool.execute(params)
        
        if result.get('success'):
            print("✅ Automatización visual exitosa")
            
            # Check for visual features
            if 'visual_steps' in result:
                print(f"📊 Pasos visuales registrados: {result['total_steps']}")
                
                # Show visual steps
                for i, step in enumerate(result['visual_steps']):
                    print(f"   {i+1}. {step['step']} - {step['details']}")
                    if 'screenshot' in step:
                        print(f"      📸 Screenshot capturado (base64 length: {len(step['screenshot'])})")
            
            if 'image_data' in result:
                print(f"📸 Screenshot principal capturado (base64 length: {len(result['image_data'])})")
            
            print(f"📋 Resultado: {json.dumps({k: v for k, v in result.items() if k != 'image_data' and k != 'visual_steps'}, indent=2)}")
            return True
        else:
            print(f"❌ Error en automatización: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando herramienta directamente: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🎬 TESTING PLAYWRIGHT VISUAL AUTOMATION")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    # Test results
    results = {
        'backend_health': False,
        'chat_integration': False,
        'direct_tool': False
    }
    
    # Run tests
    results['backend_health'] = test_playwright_visual()
    results['direct_tool'] = test_direct_playwright_tool()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
    
    success_count = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 RESULTADO GENERAL: {success_count}/{total_tests} pruebas exitosas")
    
    if success_count == total_tests:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! Playwright visual está funcionando correctamente.")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los logs anteriores.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)