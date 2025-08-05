"""
📡 EVENTOS VISUALES DE NAVEGACIÓN PARA WEBSOCKET
Maneja la emisión de eventos browser_visual al frontend durante navegación en tiempo real

FUNCIONALIDADES:
- ✅ Eventos browser_visual específicos para navegación
- ✅ Screenshots reales enviados como data URLs
- ✅ Progreso paso a paso visible en terminal
- ✅ Integración completa con WebSocket Manager
"""

import time
import base64
from typing import Dict, Any, Optional
from datetime import datetime

class BrowserVisualEventManager:
    """
    📡 GESTOR DE EVENTOS VISUALES DE NAVEGACIÓN
    
    Maneja todos los eventos browser_visual que se envían al frontend
    durante la navegación web en tiempo real
    """
    
    def __init__(self, websocket_manager, task_id: str):
        self.websocket_manager = websocket_manager
        self.task_id = task_id
        self.event_counter = 0
    
    def emit_navigation_start(self, task_description: str, start_url: str):
        """🚀 EVENTO: Inicio de navegación"""
        self._emit_browser_visual({
            'type': 'navigation_start',
            'message': f'🚀 NAVEGACIÓN REAL INICIADA: {task_description}',
            'task_description': task_description,
            'start_url': start_url,
            'step': 'Iniciando navegación web en tiempo real',
            'progress': 0
        })
    
    def emit_x11_server_ready(self, display: str, resolution: str):
        """🖥️ EVENTO: Servidor X11 listo"""
        self._emit_browser_visual({
            'type': 'x11_server_ready',
            'message': f'🖥️ Servidor X11 virtual activo - Display {display}',
            'display': display,
            'resolution': resolution,
            'step': 'Servidor de visualización configurado',
            'progress': 20
        })
    
    def emit_browser_launch(self, browser_type: str = "Chromium"):
        """🌐 EVENTO: Browser lanzado"""
        self._emit_browser_visual({
            'type': 'browser_launched', 
            'message': f'🌐 Navegador {browser_type} lanzado en modo visible',
            'browser_type': browser_type,
            'step': 'Navegador listo para navegación visible',
            'progress': 40
        })
    
    def emit_page_navigation(self, url: str, title: str = ""):
        """📄 EVENTO: Navegación a página"""
        self._emit_browser_visual({
            'type': 'page_navigation',
            'message': f'📄 Navegando a: {title or url}',
            'url': url,
            'title': title,
            'step': f'Cargando página: {url}',
            'progress': 60
        })
    
    def emit_screenshot_captured(self, screenshot_path: str, screenshot_index: int, 
                               current_url: str, screenshot_base64: str = None):
        """📸 EVENTO: Screenshot capturado (con imagen real)"""
        
        event_data = {
            'type': 'screenshot_captured',
            'message': f'📸 Screenshot #{screenshot_index + 1} capturado',
            'screenshot_url': screenshot_path,  # URL para acceso vía Flask
            'screenshot_index': screenshot_index,
            'current_url': current_url,
            'step': f'Captura #{screenshot_index + 1} - {current_url}',
            'progress': min(80 + (screenshot_index * 2), 95)
        }
        
        # Añadir screenshot como data URL si está disponible
        if screenshot_base64:
            event_data['screenshot_data'] = f'data:image/png;base64,{screenshot_base64}'
        
        self._emit_browser_visual(event_data)
    
    def emit_user_action(self, action_type: str, description: str, target: str = ""):
        """🖱️ EVENTO: Acción del usuario simulada"""
        action_messages = {
            'click': f'🖱️ Haciendo clic en: {target}',
            'type': f'⌨️ Escribiendo: {description}',
            'scroll': f'📜 Desplazando página: {description}',
            'search': f'🔍 Buscando: {description}'
        }
        
        self._emit_browser_visual({
            'type': 'user_action',
            'action_type': action_type,
            'message': action_messages.get(action_type, f'⚡ Acción: {action_type}'),
            'description': description,
            'target': target,
            'step': f'Ejecutando: {action_type}'
        })
    
    def emit_page_loaded(self, url: str, title: str, load_time: float):
        """✅ EVENTO: Página cargada completamente"""
        self._emit_browser_visual({
            'type': 'page_loaded',
            'message': f'✅ Página cargada: {title}',
            'url': url,
            'title': title,
            'load_time': load_time,
            'step': f'Página lista: {title}',
            'progress': 70
        })
    
    def emit_navigation_complete(self, total_screenshots: int, total_pages: int, 
                               total_duration: float):
        """🎉 EVENTO: Navegación completada"""
        self._emit_browser_visual({
            'type': 'navigation_complete',
            'message': f'🎉 NAVEGACIÓN COMPLETADA - {total_screenshots} capturas realizadas',
            'total_screenshots': total_screenshots,
            'total_pages': total_pages,
            'total_duration': total_duration,
            'step': 'Navegación finalizada exitosamente',
            'progress': 100
        })
    
    def emit_navigation_error(self, error_message: str, context: str = ""):
        """❌ EVENTO: Error durante navegación"""
        self._emit_browser_visual({
            'type': 'navigation_error',
            'message': f'❌ Error en navegación: {error_message}',
            'error': error_message,
            'context': context,
            'step': 'Error durante navegación'
        })
    
    def emit_custom_progress(self, message: str, step: str, progress: int):
        """📊 EVENTO: Progreso personalizado"""
        self._emit_browser_visual({
            'type': 'custom_progress',
            'message': message,
            'step': step,
            'progress': max(0, min(100, progress))
        })
    
    def _emit_browser_visual(self, data: Dict[str, Any]):
        """📡 EMITIR EVENTO BROWSER_VISUAL AL WEBSOCKET"""
        
        # Añadir metadatos estándar
        enhanced_data = {
            'task_id': self.task_id,
            'event_id': self.event_counter,
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            **data
        }
        
        self.event_counter += 1
        
        try:
            # Emitir evento browser_visual principal
            self.websocket_manager.emit_to_task(self.task_id, 'browser_visual', enhanced_data)
            
            # También emitir como terminal_activity para visibilidad en terminal
            terminal_data = {
                'message': data.get('message', 'Navegación en tiempo real'),
                'timestamp': enhanced_data['timestamp']
            }
            self.websocket_manager.emit_to_task(self.task_id, 'terminal_activity', terminal_data)
            
            print(f"📡 [BROWSER_VISUAL] {data.get('message', 'Evento emitido')}")
            
        except Exception as e:
            print(f"⚠️ Error emitiendo browser_visual: {str(e)}")

def create_browser_visual_manager(websocket_manager, task_id: str) -> BrowserVisualEventManager:
    """🏭 FACTORY: Crear gestor de eventos visuales"""
    return BrowserVisualEventManager(websocket_manager, task_id)