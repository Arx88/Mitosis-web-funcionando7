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

# Importaciones de base tool system
from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

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

@register_tool
class AINavigationTool(BaseTool):
    """🤖 Herramienta de navegación inteligente con browser-use"""
    
    def __init__(self):
        super().__init__(
            name="ai_navigation",
            description="🤖 Navegación web inteligente usando AI con browser-use Agent. Permite ejecutar tareas de navegación usando lenguaje natural.",
            parameters=[
                ParameterDefinition(
                    name="task_description",
                    type="string",
                    description="Descripción en lenguaje natural de la tarea de navegación (ej: 'buscar información sobre IA en Google')",
                    required=True
                ),
                ParameterDefinition(
                    name="url",
                    type="string", 
                    description="URL inicial opcional (si no se especifica, la IA decidirá dónde navegar)",
                    required=False
                ),
                ParameterDefinition(
                    name="extract_data",
                    type="boolean",
                    description="Si extraer datos estructurados de las páginas visitadas",
                    required=False,
                    default=False
                )
            ]
        )
        self.browser_manager = None
        self.websocket_manager = None
        
    def _emit_progress(self, message: str, level: str = "info"):
        """Emitir progreso via WebSocket"""
        try:
            if self.websocket_manager and hasattr(self, 'task_id'):
                self.websocket_manager.send_log_message(self.task_id, level, message)
            logger.info(f"[AI-NAV] {message}")
        except Exception as e:
            logger.warning(f"Error emitiendo progreso: {e}")
    
    async def execute(self, task_description: str, url: Optional[str] = None, 
                     extract_data: bool = False, **kwargs) -> ToolExecutionResult:
        """
        🤖 Ejecutar navegación inteligente usando browser-use
        """
        
        # Obtener task_id del contexto si está disponible
        self.task_id = kwargs.get('task_id', f"ai-nav-{int(time.time())}")
        
        if not BROWSER_USE_AVAILABLE:
            return ToolExecutionResult(
                success=False,
                error="Browser-use integration no disponible",
                data={
                    "message": "La funcionalidad de navegación AI requiere browser-use",
                    "browser_use_available": False
                }
            )
        
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
            
            result_data = {
                "task_description": task_description,
                "initial_url": url,
                "navigation_result": task_result,
                "extracted_data": extracted_data,
                "execution_time": execution_time,
                "agent_type": "browser-use",
                "llm_model": self.browser_manager.llm_model.name if self.browser_manager.llm_model else None,
                "browser_use_available": True
            }
            
            self._emit_progress(f"🎉 Navegación inteligente completada exitosamente en {execution_time:.2f}s")
            
            return ToolExecutionResult(
                success=True,
                data=result_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            error_msg = f"❌ Error en navegación inteligente: {str(e)}"
            self._emit_progress(error_msg, "error")
            
            import traceback
            logger.error(f"AI Navigation error: {traceback.format_exc()}")
            
            return ToolExecutionResult(
                success=False,
                error=str(e),
                data={
                    "task_description": task_description,
                    "execution_time": time.time() - start_time,
                    "browser_use_available": BROWSER_USE_AVAILABLE
                }
            )
            
        finally:
            # Cleanup
            if self.browser_manager:
                try:
                    await self.browser_manager.close()
                    self._emit_progress("🔒 Browser-use Agent cerrado correctamente")
                except Exception as e:
                    logger.warning(f"Error cerrando browser manager: {e}")

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validar parámetros de la herramienta"""
        try:
            # Validar task_description requerido
            if 'task_description' not in parameters or not parameters['task_description']:
                return False
                
            # Validar tipos opcionales
            if 'url' in parameters and parameters['url'] and not isinstance(parameters['url'], str):
                return False
                
            if 'extract_data' in parameters and not isinstance(parameters['extract_data'], bool):
                return False
                
            return True
            
        except Exception:
            return False

# Para testing directo
if __name__ == "__main__":
    async def test_ai_navigation():
        """Test de navegación inteligente"""
        tool = AINavigationTool()
        result = await tool.execute(
            task_description="Search for information about artificial intelligence and summarize the key points",
            url="https://www.google.com",
            extract_data=True
        )
        print(f"Result: {result}")
    
    asyncio.run(test_ai_navigation())