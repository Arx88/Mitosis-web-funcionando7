"""
🤖 HERRAMIENTA DE NAVEGACIÓN INTELIGENTE CON BROWSER-USE
Implementa navegación web usando AI con browser-use Agent integrado

CARACTERÍSTICAS:
- Navegación usando lenguaje natural
- AI comprende estructura de páginas automáticamente
- Visualización en tiempo real via WebSocket
- Integración completa con Mitosis LLM stack
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Importaciones de Mitosis
try:
    from ..web_browser_manager import WebBrowserManager
    from ..services.ollama_service import OllamaService
    from ..utils.websocket_manager import get_websocket_manager
    BROWSER_USE_AVAILABLE = True
except ImportError as e:
    BROWSER_USE_AVAILABLE = False
    logging.warning(f"⚠️ Browser-use integration no disponible: {e}")

logger = logging.getLogger(__name__)

class AINavigationTool:
    """🤖 Herramienta de navegación inteligente con browser-use"""
    
    def __init__(self, task_id: str = None):
        self.task_id = task_id or f"nav-{int(time.time())}"
        self.browser_manager = None
        self.websocket_manager = None
        
    def get_tool_info(self) -> Dict[str, Any]:
        """Información de la herramienta para registro"""
        return {
            "name": "ai_navigation",
            "description": "🤖 Navegación web inteligente usando AI con browser-use",
            "parameters": {
                "task_description": {
                    "type": "string",
                    "description": "Descripción en lenguaje natural de la tarea de navegación",
                    "required": True
                },
                "url": {
                    "type": "string", 
                    "description": "URL inicial (opcional - la IA puede navegar automáticamente)",
                    "required": False
                },
                "extract_data": {
                    "type": "boolean",
                    "description": "Si extraer datos de las páginas visitadas",
                    "default": False
                }
            },
            "browser_use_enabled": BROWSER_USE_AVAILABLE
        }
    
    def _emit_progress(self, message: str, level: str = "info"):
        """Emitir progreso via WebSocket"""
        try:
            if self.websocket_manager:
                self.websocket_manager.send_log_message(self.task_id, level, message)
            logger.info(f"[AI-NAV] {message}")
        except Exception as e:
            logger.warning(f"Error emitiendo progreso: {e}")
    
    async def execute(self, task_description: str, url: Optional[str] = None, 
                     extract_data: bool = False) -> Dict[str, Any]:
        """
        🤖 Ejecutar navegación inteligente usando browser-use
        
        Args:
            task_description: Descripción en lenguaje natural de la tarea
            url: URL inicial opcional
            extract_data: Si extraer datos de páginas
            
        Returns:
            Dict con resultados de la navegación
        """
        
        if not BROWSER_USE_AVAILABLE:
            return {
                "success": False,
                "error": "Browser-use integration no disponible",
                "message": "La funcionalidad de navegación AI requiere browser-use",
                "timestamp": datetime.now().isoformat()
            }
        
        start_time = time.time()
        
        try:
            # Inicializar WebSocket manager
            self.websocket_manager = get_websocket_manager()
            
            self._emit_progress("🤖 Iniciando navegación inteligente con browser-use Agent...")
            self._emit_progress(f"📝 Tarea: {task_description}")
            
            # Crear WebBrowserManager con browser-use
            ollama_service = OllamaService()
            self.browser_manager = WebBrowserManager(
                websocket_manager=self.websocket_manager,
                task_id=self.task_id,
                ollama_service=ollama_service,
                browser_type="browser-use"
            )
            
            self._emit_progress("🚀 Inicializando browser-use Agent...")
            
            # Inicializar browser
            await self.browser_manager.initialize_browser()
            
            self._emit_progress("✅ Browser-use Agent listo para navegación inteligente")
            
            # Construir tarea completa
            if url:
                full_task = f"Navigate to {url} and then {task_description}"
                self._emit_progress(f"🎯 Navegando a {url} y ejecutando: {task_description}")
            else:
                full_task = task_description
                self._emit_progress(f"🎯 Ejecutando tarea: {task_description}")
            
            # Ejecutar navegación inteligente
            self._emit_progress("🧠 IA analizando tarea y planificando navegación...")
            
            if url:
                # Navegar primero a URL específica
                navigation_result = await self.browser_manager.navigate(url, task_description)
                self._emit_progress(f"✅ Navegación a {url} completada")
                
                # Luego ejecutar tarea compleja
                if task_description and "navigate to" not in task_description.lower():
                    self._emit_progress("🎯 Ejecutando tarea compleja en la página...")
                    task_result = await self.browser_manager.perform_complex_task(task_description)
                else:
                    task_result = navigation_result
            else:
                # Ejecutar tarea compleja directamente (la IA decidirá dónde navegar)
                self._emit_progress("🤖 IA decidiendo automáticamente sitios a visitar...")
                task_result = await self.browser_manager.perform_complex_task(full_task)
            
            # Extraer datos si se solicita
            extracted_data = None
            if extract_data:
                self._emit_progress("🔍 Extrayendo datos de páginas visitadas...")
                extracted_data = await self.browser_manager.extract_data(
                    f"Extract relevant data related to: {task_description}"
                )
                self._emit_progress("✅ Extracción de datos completada")
            
            # Preparar resultado final
            execution_time = time.time() - start_time
            
            result = {
                "success": True,
                "task_description": task_description,
                "initial_url": url,
                "navigation_result": task_result,
                "extracted_data": extracted_data,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "agent_type": "browser-use",
                "llm_model": self.browser_manager.llm_model.name if self.browser_manager.llm_model else None
            }
            
            self._emit_progress(f"🎉 Navegación inteligente completada exitosamente en {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Error en navegación inteligente: {str(e)}"
            self._emit_progress(error_msg, "error")
            
            return {
                "success": False,
                "error": str(e),
                "task_description": task_description,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            # Cleanup
            if self.browser_manager:
                try:
                    await self.browser_manager.close()
                    self._emit_progress("🔒 Browser-use Agent cerrado correctamente")
                except Exception as e:
                    logger.warning(f"Error cerrando browser manager: {e}")

# Función de ejecución compatible con el sistema de herramientas de Mitosis
async def execute_ai_navigation(task_description: str, url: str = None, 
                               extract_data: bool = False, task_id: str = None) -> Dict[str, Any]:
    """
    🤖 Función de ejecución para navegación inteligente
    Compatible con el sistema de herramientas de Mitosis
    """
    tool = AINavigationTool(task_id=task_id)
    return await tool.execute(task_description, url, extract_data)

# Registro de herramienta para el sistema de Mitosis
def register_ai_navigation_tool():
    """Registra la herramienta en el sistema de Mitosis"""
    return {
        "ai_navigation": {
            "function": execute_ai_navigation,
            "description": "🤖 Navegación web inteligente usando AI con browser-use",
            "parameters": {
                "task_description": "string (required) - Descripción en lenguaje natural de la tarea",
                "url": "string (optional) - URL inicial",
                "extract_data": "boolean (optional, default: false) - Extraer datos de páginas",
                "task_id": "string (optional) - ID de tarea para tracking"
            },
            "ai_powered": True,
            "browser_use_enabled": BROWSER_USE_AVAILABLE
        }
    }

# Para testing directo
if __name__ == "__main__":
    async def test_ai_navigation():
        """Test de navegación inteligente"""
        tool = AINavigationTool("test-nav-123")
        result = await tool.execute(
            task_description="Search for information about artificial intelligence and summarize the key points",
            url="https://www.google.com",
            extract_data=True
        )
        print(f"Result: {result}")
    
    asyncio.run(test_ai_navigation())