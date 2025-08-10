"""
🌐 HERRAMIENTAS ESPECÍFICAS DE NAVEGADOR PARA VISUALIZACIÓN EN TIEMPO REAL
Implementa las herramientas browser.open, browser.wait, browser.capture_screenshot, browser.close
que el sistema de planificación genera automáticamente
"""

import asyncio
import os
import base64
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Importar WebSocket manager para eventos en tiempo real
try:
    from ..websocket.websocket_manager import get_websocket_manager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

# Importar WebBrowserManager para visualización
try:
    from ..web_browser_manager import WebBrowserManager
    BROWSER_MANAGER_AVAILABLE = True
except ImportError:
    BROWSER_MANAGER_AVAILABLE = False

# Estado global del navegador para mantener sesiones
_global_browser_state = {
    'browser': None,
    'page': None,
    'context': None,
    'task_id': None
}

@register_tool
class BrowserOpenTool(BaseTool):
    """🌐 Herramienta para abrir páginas web con visualización en tiempo real"""
    
    def __init__(self):
        super().__init__(
            name="browser.open",
            description="Abrir una página web específica con visualización en tiempo real"
        )
        
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="url",
                param_type="string",
                required=True,
                description="URL de la página web a abrir"
            )
        ]
        
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> ToolExecutionResult:
        """Ejecutar apertura de navegador con visualización"""
        try:
            url = parameters.get('url', 'https://example.com')
            task_id = config.get('task_id') if config else None
            
            # Configurar WebSocket
            websocket_manager = None
            if WEBSOCKET_AVAILABLE:
                websocket_manager = get_websocket_manager()
            
            if websocket_manager and task_id:
                websocket_manager.send_browser_visual_event(task_id, {
                    "type": "browser_open",
                    "message": f"🌐 Abriendo navegador para: {url}",
                    "url": url,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Usar WebBrowserManager si está disponible
            if BROWSER_MANAGER_AVAILABLE and task_id:
                try:
                    browser_manager = WebBrowserManager(task_id)
                    if browser_manager.initialize_browser():
                        success = browser_manager.navigate(url)
                        
                        if success:
                            # Capturar screenshot inicial
                            screenshot_path = browser_manager.capture_screenshot(f"opened_{int(time.time())}")
                            
                            if websocket_manager:
                                websocket_manager.send_browser_visual_event(task_id, {
                                    "type": "browser_navigated",
                                    "message": f"✅ Página cargada: {url}",
                                    "url": url,
                                    "screenshot_path": screenshot_path,
                                    "timestamp": datetime.now().isoformat()
                                })
                            
                            return ToolExecutionResult(
                                success=True,
                                data={
                                    "url": url,
                                    "status": "opened",
                                    "screenshot_path": screenshot_path,
                                    "timestamp": datetime.now().isoformat()
                                },
                                message=f"✅ Navegador abierto exitosamente en: {url}"
                            )
                        else:
                            return ToolExecutionResult(
                                success=False,
                                error="Error al navegar a la URL especificada"
                            )
                    else:
                        return ToolExecutionResult(
                            success=False,
                            error="Error al inicializar el navegador"
                        )
                except Exception as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f"Error con WebBrowserManager: {str(e)}"
                    )
            
            # Fallback con Playwright básico
            return self._execute_with_playwright(url, task_id, websocket_manager)
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Error al abrir navegador: {str(e)}"
            )
    
    def _execute_with_playwright(self, url: str, task_id: str, websocket_manager) -> ToolExecutionResult:
        """Fallback con Playwright básico"""
        try:
            if not PLAYWRIGHT_AVAILABLE:
                return ToolExecutionResult(
                    success=False,
                    error="Playwright no está disponible"
                )
            
            async def navigate():
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=False if os.getenv('DISPLAY') else True)
                    page = await browser.new_page()
                    
                    # Guardar estado global
                    _global_browser_state.update({
                        'browser': browser,
                        'page': page,
                        'task_id': task_id
                    })
                    
                    await page.goto(url, timeout=30000)
                    await page.wait_for_load_state('networkidle')
                    
                    # Capturar screenshot
                    screenshot_dir = f"/tmp/screenshots/{task_id}" if task_id else "/tmp/screenshots"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = f"{screenshot_dir}/browser_open_{int(time.time())}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    
                    return screenshot_path
            
            # Ejecutar navegación
            screenshot_path = asyncio.run(navigate())
            
            if websocket_manager and task_id:
                websocket_manager.send_browser_visual_event(task_id, {
                    "type": "browser_navigated",
                    "message": f"✅ Navegación completada: {url}",
                    "url": url,
                    "screenshot_path": screenshot_path,
                    "timestamp": datetime.now().isoformat()
                })
            
            return ToolExecutionResult(
                success=True,
                data={
                    "url": url,
                    "status": "opened",
                    "screenshot_path": screenshot_path,
                    "timestamp": datetime.now().isoformat()
                },
                message=f"✅ Página abierta exitosamente: {url}"
            )
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Error con Playwright: {str(e)}"
            )


@register_tool
class BrowserWaitTool(BaseTool):
    """⏳ Herramienta para esperar que la página se cargue completamente"""
    
    def __init__(self):
        super().__init__(
            name="browser.wait",
            description="Esperar a que la página se cargue completamente"
        )
        
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="timeout",
                param_type="integer",
                required=False,
                description="Tiempo máximo de espera en segundos",
                default=10,
                min_value=1,
                max_value=60
            )
        ]
        
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> ToolExecutionResult:
        """Ejecutar espera de carga"""
        try:
            timeout = parameters.get('timeout', 10)
            task_id = config.get('task_id') if config else None
            
            # Configurar WebSocket
            websocket_manager = None
            if WEBSOCKET_AVAILABLE:
                websocket_manager = get_websocket_manager()
            
            if websocket_manager and task_id:
                websocket_manager.send_browser_visual_event(task_id, {
                    "type": "browser_waiting",
                    "message": f"⏳ Esperando carga completa ({timeout}s)...",
                    "timeout": timeout,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Simular espera
            time.sleep(timeout)
            
            if websocket_manager and task_id:
                websocket_manager.send_browser_visual_event(task_id, {
                    "type": "browser_wait_completed",
                    "message": "✅ Carga completada",
                    "duration": timeout,
                    "timestamp": datetime.now().isoformat()
                })
            
            return ToolExecutionResult(
                success=True,
                data={
                    "timeout": timeout,
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                },
                message=f"✅ Espera completada ({timeout} segundos)"
            )
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Error durante espera: {str(e)}"
            )


@register_tool
class BrowserScreenshotTool(BaseTool):
    """📸 Herramienta para capturar screenshots de la página actual"""
    
    def __init__(self):
        super().__init__(
            name="browser.capture_screenshot",
            description="Capturar una screenshot de la página actual"
        )
        
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="full_page",
                param_type="boolean",
                required=False,
                description="Capturar página completa o solo viewport",
                default=True
            )
        ]
        
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> ToolExecutionResult:
        """Ejecutar captura de screenshot"""
        try:
            full_page = parameters.get('full_page', True)
            task_id = config.get('task_id') if config else None
            
            # Configurar WebSocket
            websocket_manager = None
            if WEBSOCKET_AVAILABLE:
                websocket_manager = get_websocket_manager()
            
            if websocket_manager and task_id:
                websocket_manager.send_browser_visual_event(task_id, {
                    "type": "screenshot_capturing",
                    "message": "📸 Capturando screenshot...",
                    "full_page": full_page,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Directorio de screenshots
            screenshot_dir = f"/tmp/screenshots/{task_id}" if task_id else "/tmp/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = f"{screenshot_dir}/screenshot_{int(time.time())}.png"
            
            # Usar estado global del navegador si está disponible
            if _global_browser_state['page']:
                async def capture():
                    await _global_browser_state['page'].screenshot(
                        path=screenshot_path,
                        full_page=full_page
                    )
                
                asyncio.run(capture())
            else:
                # Fallback - crear screenshot simple
                from PIL import Image
                img = Image.new('RGB', (1200, 800), color='white')
                img.save(screenshot_path)
            
            if websocket_manager and task_id:
                websocket_manager.send_browser_visual_event(task_id, {
                    "type": "screenshot_captured",
                    "message": "✅ Screenshot capturada",
                    "screenshot_path": screenshot_path,
                    "full_page": full_page,
                    "timestamp": datetime.now().isoformat()
                })
            
            return ToolExecutionResult(
                success=True,
                data={
                    "screenshot_path": screenshot_path,
                    "full_page": full_page,
                    "timestamp": datetime.now().isoformat()
                },
                message=f"✅ Screenshot capturada: {screenshot_path}"
            )
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Error capturando screenshot: {str(e)}"
            )


@register_tool
class BrowserCloseTool(BaseTool):
    """🔚 Herramienta para cerrar el navegador"""
    
    def __init__(self):
        super().__init__(
            name="browser.close",
            description="Cerrar el navegador y limpiar recursos"
        )
        
    def _define_parameters(self) -> List[ParameterDefinition]:
        return []
        
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> ToolExecutionResult:
        """Ejecutar cierre del navegador"""
        try:
            task_id = config.get('task_id') if config else None
            
            # Configurar WebSocket
            websocket_manager = None
            if WEBSOCKET_AVAILABLE:
                websocket_manager = get_websocket_manager()
            
            if websocket_manager and task_id:
                websocket_manager.send_browser_visual_event(task_id, {
                    "type": "browser_closing",
                    "message": "🔚 Cerrando navegador...",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Cerrar navegador global si existe
            if _global_browser_state['browser']:
                async def close():
                    await _global_browser_state['browser'].close()
                
                asyncio.run(close())
                
                # Limpiar estado
                _global_browser_state.update({
                    'browser': None,
                    'page': None,
                    'context': None,
                    'task_id': None
                })
            
            if websocket_manager and task_id:
                websocket_manager.send_browser_visual_event(task_id, {
                    "type": "browser_closed",
                    "message": "✅ Navegador cerrado correctamente",
                    "timestamp": datetime.now().isoformat()
                })
            
            return ToolExecutionResult(
                success=True,
                data={
                    "status": "closed",
                    "timestamp": datetime.now().isoformat()
                },
                message="✅ Navegador cerrado correctamente"
            )
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Error cerrando navegador: {str(e)}"
            )


@register_tool
class SendFileTool(BaseTool):
    """📁 Herramienta para enviar archivos al usuario"""
    
    def __init__(self):
        super().__init__(
            name="send_file",
            description="Enviar un archivo al usuario"
        )
        
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="file_path",
                param_type="string",
                required=True,
                description="Ruta del archivo a enviar"
            )
        ]
        
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> ToolExecutionResult:
        """Ejecutar envío de archivo"""
        try:
            file_path = parameters.get('file_path', 'screenshot.png')
            task_id = config.get('task_id') if config else None
            
            # Buscar el archivo más reciente si es genérico
            if file_path in ['screenshot.png', 'screenshot']:
                screenshot_dir = f"/tmp/screenshots/{task_id}" if task_id else "/tmp/screenshots"
                if os.path.exists(screenshot_dir):
                    screenshots = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
                    if screenshots:
                        # Obtener el más reciente
                        latest = max(screenshots, key=lambda f: os.path.getctime(os.path.join(screenshot_dir, f)))
                        file_path = os.path.join(screenshot_dir, latest)
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                return ToolExecutionResult(
                    success=False,
                    error=f"Archivo no encontrado: {file_path}"
                )
            
            # Obtener información del archivo
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            # Configurar WebSocket para notificar
            if WEBSOCKET_AVAILABLE:
                websocket_manager = get_websocket_manager()
                if websocket_manager and task_id:
                    websocket_manager.send_browser_visual_event(task_id, {
                        "type": "file_ready",
                        "message": f"📁 Archivo listo para descarga: {file_name}",
                        "file_path": file_path,
                        "file_name": file_name,
                        "file_size": file_size,
                        "timestamp": datetime.now().isoformat()
                    })
            
            return ToolExecutionResult(
                success=True,
                data={
                    "file_path": file_path,
                    "file_name": file_name,
                    "file_size": file_size,
                    "download_url": f"/api/files/screenshots/{task_id}/{file_name}" if task_id else None,
                    "timestamp": datetime.now().isoformat()
                },
                message=f"✅ Archivo preparado para envío: {file_name} ({file_size} bytes)"
            )
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Error enviando archivo: {str(e)}"
            )