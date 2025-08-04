#!/usr/bin/env python3
"""
Script de debug para probar browser-use independientemente
"""

import asyncio
import logging
import sys
import os

# Agregar path del backend
sys.path.insert(0, '/app/backend')

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_browser_use():
    """Test simple de browser-use para identificar el problema"""
    
    try:
        print("🧪 Iniciando test de browser-use...")
        
        # Importar browser-use
        from browser_use import Agent
        from browser_use.browser.session import BrowserSession
        from browser_use.browser.profile import BrowserProfile
        
        print("✅ Importaciones exitosas")
        
        # Importar adaptador de Mitosis
        from src.adapters.mitosis_ollama_chat import MitosisOllamaChatModel
        from src.services.ollama_service import OllamaService
        
        print("✅ Adaptador Mitosis importado correctamente")
        
        # Crear modelo LLM
        ollama_service = OllamaService(base_url="https://66bd0d09b557.ngrok-free.app")
        llm_model = MitosisOllamaChatModel.create_from_mitosis_config(
            ollama_service=ollama_service,
            model="llama3.1:8b"
        )
        
        print("✅ Modelo LLM creado exitosamente")
        
        # Crear sesión de browser primero
        browser_session = BrowserSession(
            headless=True,
            browser_profile=BrowserProfile(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        )
        
        print("✅ Sesión de browser creada")
        
        print("🧪 Probando con modelo de prueba simple...")
        
        # Crear un modelo simple de prueba
        class SimpleLLM:
            def __init__(self):
                self.name = "simple-test"
                self.provider = "test"
                self.model_name = "test"
                
            async def ainvoke(self, messages, output_format=None):
                from browser_use.llm.views import ChatInvokeCompletion
                return ChatInvokeCompletion(response="Test response")
        
        simple_llm = SimpleLLM()
        print("✅ Modelo simple creado")
        
        # Probar con modelo simple
        simple_agent = Agent(
            task="Test básico",
            llm=simple_llm,
            browser_session=browser_session,
            use_vision=False,
            max_failures=1
        )
        print("✅ Agent simple creado")
        
        try:
            simple_result = await simple_agent.run("Say hello")
            print(f"✅ Test con modelo simple exitoso: {simple_result}")
        except Exception as e:
            print(f"❌ Error con modelo simple también: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Ahora probar con nuestro modelo
        
        # Crear sesión de browser
        browser_session = BrowserSession(
            headless=True,
            browser_profile=BrowserProfile(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        )
        
        print("✅ Sesión de browser creada")
        
        # Crear Agent - con parámetros más específicos
        print("🔧 Creando Agent con configuración detallada...")
        
        # Crear directorio para conversaciones si no existe
        os.makedirs("/tmp/browser_conversations", exist_ok=True)
        
        agent = Agent(
            task="Navegación web básica",
            llm=llm_model,
            browser_session=browser_session,
            use_vision=False,  # Probar sin vision primero
            max_failures=1,    # Reducir failures para debug
            save_conversation_path=None  # Sin guardar conversación por ahora
        )
        
        print("✅ Agent de browser-use creado exitosamente")
        
        # Test simple - navegar a una página
        print("🚀 Probando navegación a Google...")
        
        try:
            result = await agent.run("Navigate to https://www.google.com")
            print(f"✅ Test completado exitosamente: {result}")
            return True
        except Exception as e:
            print(f"❌ Error específico en agent.run(): {str(e)}")
            print(f"❌ Tipo de error: {type(e)}")
            import traceback
            traceback.print_exc()
            
            # Intentar llamada más simple
            print("🔄 Probando tarea más simple...")
            try:
                simple_result = await agent.run("Say hello")
                print(f"✅ Tarea simple exitosa: {simple_result}")
            except Exception as e2:
                print(f"❌ Error en tarea simple también: {str(e2)}")
            
            return False
        
    except Exception as e:
        print(f"❌ Error durante test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            if 'agent' in locals():
                await agent.close()
        except:
            pass

if __name__ == "__main__":
    result = asyncio.run(test_browser_use())
    if result:
        print("🎉 Test exitoso - browser-use está funcionando")
    else:
        print("💥 Test falló - hay problemas con browser-use")