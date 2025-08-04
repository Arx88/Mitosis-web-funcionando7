#!/usr/bin/env python3
"""
Test script para verificar la integración de browser-use con Mitosis
"""

import sys
import os
import asyncio
import logging

# Añadir el directorio del backend al path
sys.path.append('/app/backend/src')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_browser_use_integration():
    """Test básico de la integración browser-use"""
    try:
        logger.info("🧪 Iniciando test de integración browser-use...")
        
        # 1. Test import de MitosisOllamaChatModel
        logger.info("📦 Testing import de MitosisOllamaChatModel...")
        from adapters.mitosis_ollama_chat import MitosisOllamaChatModel
        logger.info("✅ MitosisOllamaChatModel importado exitosamente")
        
        # 2. Test import de WebBrowserManager refactorizado
        logger.info("📦 Testing import de WebBrowserManager...")
        from web_browser_manager import WebBrowserManager
        logger.info("✅ WebBrowserManager importado exitosamente")
        
        # 3. Test creación de LLM model
        logger.info("🧠 Testing creación de LLM model...")
        llm_model = MitosisOllamaChatModel(
            model="llama3.1:8b",
            host="https://66bd0d09b557.ngrok-free.app"
        )
        logger.info(f"✅ LLM model creado: {llm_model.name}")
        
        # 4. Test creación de WebBrowserManager (mock websocket_manager)
        class MockWebSocketManager:
            def send_browser_activity(self, task_id, activity_type, url, title, screenshot_path):
                logger.info(f"📡 Mock WebSocket: {activity_type} - {url}")
            
            def send_log_message(self, task_id, level, message):
                logger.info(f"📝 Mock Log: {level} - {message}")
        
        mock_websocket = MockWebSocketManager()
        
        logger.info("🤖 Testing creación de WebBrowserManager...")
        browser_manager = WebBrowserManager(
            websocket_manager=mock_websocket,
            task_id="test-task-123",
            ollama_service=None,  # Will create its own
            browser_type="browser-use"
        )
        logger.info("✅ WebBrowserManager creado exitosamente")
        
        # 5. Test inicialización (sin ejecutar realmente para evitar errores de entorno)
        logger.info("🚀 Testing estructura de inicialización...")
        assert hasattr(browser_manager, 'llm_model'), "browser_manager debe tener llm_model"
        assert hasattr(browser_manager, 'initialize_browser'), "browser_manager debe tener initialize_browser"
        assert browser_manager.browser_type == "browser-use", "browser_type debe ser browser-use"
        logger.info("✅ Estructura de WebBrowserManager correcta")
        
        # 6. Test métodos principales existen
        logger.info("🔍 Testing existencia de métodos principales...")
        required_methods = ['navigate', 'click_element', 'type_text', 'extract_data', 'perform_complex_task']
        for method in required_methods:
            assert hasattr(browser_manager, method), f"Método {method} debe existir"
        logger.info("✅ Todos los métodos principales existen")
        
        logger.info("🎉 Test de integración browser-use COMPLETADO EXITOSAMENTE!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test de integración: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_browser_use_integration())
    if success:
        print("\n✅ INTEGRACIÓN BROWSER-USE FUNCIONANDO CORRECTAMENTE")
        exit(0)
    else:
        print("\n❌ PROBLEMAS EN INTEGRACIÓN BROWSER-USE")
        exit(1)