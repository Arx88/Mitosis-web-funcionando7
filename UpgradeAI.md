# Informe de Integración Específico: Browser-Use en el Proyecto Mitosis

## 1. Introducción y Contexto del Proyecto Mitosis

El presente informe técnico tiene como objetivo principal proporcionar una guía detallada y específica para la integración de la biblioteca `browser-use` en el proyecto `Mitosis`. El requerimiento fundamental es transformar la visualización actual de la actividad de navegación web del agente, que se limita a logs de texto y capturas de pantalla estáticas, hacia una experiencia de monitoreo en tiempo real más interactiva y visualmente rica. Esta refactorización busca no solo mejorar la depuración y el entendimiento del comportamiento del agente, sino también alinear la infraestructura de navegación con las capacidades avanzadas que `browser-use` ofrece para la interacción de agentes de IA con entornos web.

El proyecto `Mitosis`, según el análisis de su estructura, ya ha establecido una base robusta para la automatización del navegador, utilizando `Playwright` para la orquestación de las interacciones web. Los archivos clave identificados en esta funcionalidad son `backend/web_browser_manager.py`, que encapsula la lógica de control del navegador, y `backend/unified_api.py`, que actúa como el punto central de comunicación entre el backend y el frontend, incluyendo la gestión de eventos en tiempo real a través de `SocketIO`. La implementación actual ya envía eventos de actividad del navegador (como `navigation_completed`, `click_completed`, `typing_completed`) y rutas de capturas de pantalla al frontend. Sin embargo, la integración de `browser-use` permitirá una abstracción de más alto nivel y, potencialmente, una representación más semántica de las acciones del agente en el navegador, superando las limitaciones de una simple transmisión de logs y capturas de pantalla.

## 2. Análisis Detallado de la Implementación Actual en Mitosis

Para comprender la integración propuesta, es crucial un análisis profundo de los componentes existentes en `Mitosis` que gestionan la navegación web y la comunicación en tiempo real.

### 2.1. `backend/web_browser_manager.py`

Este módulo es el corazón de la interacción de `Mitosis` con el navegador. Su clase principal, `WebBrowserManager`, se encarga de:

*   **Inicialización de Playwright:** Lanza instancias de navegadores (`Chromium`, `Firefox`, `WebKit`) y gestiona contextos de navegador para operaciones concurrentes.
*   **Operaciones de Navegación:** Implementa métodos como `navigate`, `click_element`, `type_text`, y `extract_data` que interactúan directamente con la API de `Playwright`.
*   **Captura de Pantallas:** El método `_take_screenshot` genera capturas de pantalla en formato PNG y las guarda en un directorio temporal (`/tmp/screenshots/{task_id}`). La ruta de estas capturas se convierte en una URL accesible desde el frontend (`/api/files/screenshots/{task_id}/{screenshot_name}`).
*   **Integración con WebSocket:** Utiliza una instancia de `websocket_manager` (pasada en el constructor) para enviar eventos de actividad del navegador en tiempo real al frontend. Estos eventos incluyen el tipo de actividad (ej. `navigation_completed`), la URL, el título de la página y la ruta de la captura de pantalla. También envía mensajes de log (`send_log_message`) para depuración.

**Puntos Clave para la Integración:**

*   El `WebBrowserManager` ya es asíncrono, lo cual es compatible con `browser-use`.
*   La dependencia de `Playwright` es explícita y bien manejada.
*   La lógica de envío de eventos vía `websocket_manager` es un punto de extensión ideal para transmitir la información más rica que `browser-use` puede proporcionar.

### 2.2. `backend/unified_api.py`

Este módulo expone la API RESTful y la funcionalidad de `SocketIO` para la comunicación con el frontend. La clase `UnifiedMitosisAPI` es responsable de:

*   **Gestión de Sesiones:** Mantiene un mapeo de `session_id` a `room_id` para la comunicación `SocketIO`.
*   **Páginas de Monitoreo (`MonitorPage`):** Define una estructura de datos para las páginas de monitoreo que se envían al frontend. Estas páginas contienen `id`, `title`, `content`, `type` (ej. `plan`, `tool-execution`, `report`, `file`, `error`), `timestamp` y `metadata`.
*   **Eventos SocketIO:** Maneja conexiones (`connect`), desconexiones (`disconnect`) y la unión a salas de monitoreo (`join_monitoring`). Emite eventos como `new_monitor_page` para actualizar el frontend.
*   **Integración con `MitosisRealAgent`:** Interactúa con la instancia de `MitosisRealAgent` para procesar mensajes de usuario y gestionar tareas.

**Puntos Clave para la Integración:**

*   El `websocket_manager` utilizado en `WebBrowserManager` probablemente es una instancia o un proxy del `SocketIO` de `UnifiedMitosisAPI`.
*   La estructura `MonitorPage` es genérica y puede adaptarse para incluir nuevos tipos de eventos o metadatos provenientes de `browser-use`.
*   La emisión de eventos `new_monitor_page` es el mecanismo actual para la visualización en el frontend.

## 3. Capacidades Relevantes de `browser-use` para Mitosis

`browser-use` es una biblioteca de Python que simplifica la interacción de agentes de IA con navegadores web, construyendo sobre `Playwright`. Sus características más relevantes para `Mitosis` son:

*   **Abstracción de Alto Nivel:** Permite a los agentes realizar acciones complejas (navegar, hacer clic, escribir, extraer información) con instrucciones más semánticas, reduciendo la verbosidad del código `Playwright` directo.
*   **Integración con LLMs:** Está diseñado para ser utilizado por LLMs, lo que significa que puede interpretar instrucciones en lenguaje natural y traducirlas en acciones del navegador. Esto es fundamental para un agente como `Mitosis`.
*   **Observabilidad Mejorada:** `browser-use` puede proporcionar una representación más rica del estado del navegador, incluyendo el DOM simplificado, elementos interactivos y el contexto visual, lo que va más allá de una simple captura de pantalla.
*   **Manejo de Eventos:** Aunque no se detalla explícitamente en la documentación pública, `browser-use` por su naturaleza de interacción con LLMs, debe tener mecanismos internos para observar y reportar la actividad del navegador de una manera más estructurada.

La principal ventaja de `browser-use` sobre la implementación actual de `Playwright` en `Mitosis` radica en su capacidad para elevar el nivel de abstracción de la interacción. En lugar de que el agente de `Mitosis` tenga que especificar selectores CSS o XPath directamente para cada acción, `browser-use` puede permitirle operar con conceptos más cercanos al lenguaje natural, como "hacer clic en el botón de enviar" o "leer el precio del producto". Esto no solo simplifica el código del agente, sino que también abre la puerta a una visualización de la actividad más significativa en el frontend.

## 4. Diseño de la Arquitectura de Integración Específica

La integración de `browser-use` en `Mitosis` se centrará en refactorizar `web_browser_manager.py` para que `browser-use` sea la capa principal de interacción con el navegador, mientras se mantiene la infraestructura de `SocketIO` existente para la comunicación en tiempo real con el frontend. Se propone un enfoque de reemplazo gradual y mejora de la observabilidad.

### 4.1. Modificaciones en `backend/web_browser_manager.py`

El objetivo es reemplazar las llamadas directas a `Playwright` para las acciones de alto nivel con las de `browser-use`, manteniendo la capacidad de captura de pantalla y el envío de eventos al `websocket_manager`.

**Paso 1: Importar e Inicializar `browser-use.Agent`**

Se debe importar `Agent` de `browser_use` y una clase de LLM compatible (como `ChatOpenAI` o la que `Mitosis` ya esté utilizando para sus operaciones principales). La instancia de `browser_use.Agent` se inicializará en el constructor o en el método `initialize` de `WebBrowserManager`.

```python
# backend/web_browser_manager.py

import logging
import asyncio
import json
import time
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import re
from urllib.parse import urljoin, urlparse

# Playwright imports (se mantienen porque browser-use los usa internamente y para posibles usos de bajo nivel)
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.error("Playwright no está instalado. Ejecutar: pip install playwright && playwright install")

# ✅ Importar browser-use
try:
    from browser_use import Agent
    # Asumiendo que Mitosis ya tiene un LLM configurado, se usará ese. Si no, se puede usar ChatOpenAI.
    # from browser_use.llm import ChatOpenAI # Descomentar si se necesita un LLM específico para browser-use
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logging.error("browser-use no está instalado. Ejecutar: pip install browser-use")

# ... (otras clases y dataclasses existentes)

class WebBrowserManager:
    """Gestor unificado de navegación web con Playwright y visualización en tiempo real"""
    
    def __init__(self, config: Optional[BrowserConfig] = None, websocket_manager=None, task_id: str = None):
        self.config = config or BrowserConfig()
        self.logger = logging.getLogger(__name__)
        self.websocket_manager = websocket_manager
        self.task_id = task_id
        
        # Estado del navegador (se mantienen para compatibilidad y posible uso directo de Playwright)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.active_pages: Dict[str, Page] = {}
        
        # ✅ Instancia de browser-use Agent
        self.browser_use_agent: Optional[Agent] = None
        
        # ... (resto del constructor existente)
        
        if not BROWSER_USE_AVAILABLE:
            self.logger.error("⚠️ browser-use no disponible - funcionalidad de alto nivel limitada")

    async def initialize(self) -> bool:
        """Inicializa el navegador y contextos"""
        if not PLAYWRIGHT_AVAILABLE or not BROWSER_USE_AVAILABLE:
            self.logger.error("Cannot initialize browser - Playwright or browser-use not available")
            return False
        
        try:
            # Inicializar Playwright (browser-use lo usará internamente, pero podemos mantenerlo para control directo si es necesario)
            self.playwright = await async_playwright().start()
            
            # Lanzar navegador (browser-use puede lanzar su propio navegador, o podemos pasárselo)
            # Para una integración más limpia, dejaremos que browser-use maneje el lanzamiento del navegador.
            # Si se necesita control sobre el navegador lanzado por browser-use, se puede explorar su API.
            
            # ✅ Inicializar browser-use Agent
            # Aquí se asume que Mitosis ya tiene un LLM configurado (ej. self.agent.llm en unified_api.py)
            # Se necesitará pasar una instancia de LLM compatible con browser-use.
            # Para este ejemplo, usaremos un placeholder. En Mitosis, esto debería ser el LLM real del agente.
            
            # Ejemplo de cómo obtener el LLM del agente Mitosis (esto requeriría pasar el agente o el LLM aquí)
            # from agent_core_real import MitosisRealAgent # Importar donde sea necesario
            # llm_instance = MitosisRealAgent.get_llm_instance() # Pseudocódigo para obtener el LLM
            
            # Por simplicidad, usaremos un LLM de ejemplo. En un entorno real, se pasaría el LLM de Mitosis.
            # from browser_use.llm import ChatOpenAI
            # llm_for_browser_use = ChatOpenAI(model="gpt-4o") # Asegúrate de que el modelo sea accesible
            
            # Si el LLM de Mitosis no es directamente compatible, se necesitará un wrapper.
            # Para este informe, asumimos que se puede adaptar o que Mitosis usa un LLM compatible.
            
            self.browser_use_agent = Agent(
                task="Navegación web para el agente Mitosis", # Tarea genérica o dinámica
                llm=None, # ✅ Sustituir con la instancia de LLM real de Mitosis
                # Otras configuraciones de browser-use, como el modo headless, user_agent, etc.
                # browser_config=self.config # Si browser-use acepta un objeto de configuración similar
            )
            
            # Opcional: Si browser-use permite adjuntar a un navegador existente de Playwright:
            # self.browser = await self.playwright.chromium.launch(headless=self.config.headless)
            # self.context = await self.browser.new_context(...)
            # self.browser_use_agent = Agent(..., page=self.context.new_page())
            
            self.logger.info("browser-use Agent inicializado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando browser-use Agent: {e}")
            return False

    # ✅ MÉTODOS PARA NAVEGACIÓN EN TIEMPO REAL - REFRACTORIZADOS CON BROWSER-USE

    async def navigate(self, url: str):
        """Navegar a URL con eventos de tiempo real usando browser-use"""
        try:
            if not self.browser_use_agent:
                self.logger.error("❌ browser-use Agent no inicializado para navegar")
                return
            
            self.logger.info(f"🌐 Navegando a {url} usando browser-use...")
            
            # browser-use maneja la navegación internamente. El método `go_to` es un ejemplo.
            # La API exacta puede variar, consultar la documentación de browser-use.
            await self.browser_use_agent.go_to(url)
            
            # browser-use puede no exponer directamente la 'page' de Playwright para tomar screenshots.
            # Si se necesita una captura de pantalla, se podría necesitar una forma de acceder a la página interna
            # o que browser-use proporcione un método para tomar capturas.
            # Por ahora, asumimos que browser-use tiene un método para obtener el título y que la captura
            # de pantalla se manejará de forma adaptada o se delegará a browser-use si lo soporta.
            
            # Intentar obtener el título de la página a través de browser-use
            page_title = "" # Placeholder
            try:
                # Esto es pseudocódigo, la API real de browser-use puede variar
                page_title = await self.browser_use_agent.get_current_page_title() 
            except AttributeError:
                self.logger.warning("browser-use Agent no expone método para obtener título de página directamente.")
            
            # La captura de pantalla es un punto crítico. Si browser-use no la expone, se necesitará
            # una instancia de Playwright separada o un mecanismo para acceder a la página actual.
            # Para este informe, asumimos que _take_screenshot se adaptará o se usará una alternativa.
            screenshot_path = "" # Placeholder
            # if self.browser_use_agent.current_page: # Pseudocódigo si browser-use expone la página
            #    screenshot_path = await self._take_screenshot(self.browser_use_agent.current_page, url)
            
            # Enviar evento de navegación completa al frontend
            if self.websocket_manager and self.task_id:
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "navigation_completed",
                    url,
                    page_title,
                    screenshot_path
                )
                self.websocket_manager.send_log_message(
                    self.task_id,
                    "info",
                    f"🌐 Navegación completada a: {url} (Título: {page_title})"
                )
            
        except Exception as e:
            self.logger.error(f"❌ Error navegando a {url} con browser-use: {e}")
            if self.websocket_manager and self.task_id:
                self.websocket_manager.send_log_message(
                    self.task_id,
                    "error",
                    f"Error navegando a {url} con browser-use: {str(e)}"
                )

    async def click_element(self, selector: str):
        """Hacer click en elemento con tracking en tiempo real usando browser-use"""
        try:
            if not self.browser_use_agent:
                self.logger.error("❌ browser-use Agent no inicializado para click")
                return
            
            self.logger.info(f"🖱️ Intentando click en: {selector} usando browser-use...")
            
            # browser-use maneja el click internamente. El método `click` es un ejemplo.
            await self.browser_use_agent.click(selector)
            
            # Obtener URL y título actuales después del click
            current_url = "" # Placeholder
            current_title = "" # Placeholder
            try:
                current_url = await self.browser_use_agent.get_current_url() # Pseudocódigo
                current_title = await self.browser_use_agent.get_current_page_title() # Pseudocódigo
            except AttributeError:
                pass # Manejar si los métodos no existen
            
            screenshot_path = "" # Placeholder
            # if self.browser_use_agent.current_page: # Pseudocódigo
            #    screenshot_path = await self._take_screenshot(self.browser_use_agent.current_page, current_url)
            
            if self.websocket_manager and self.task_id:
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "click_completed",
                    current_url,
                    current_title,
                    screenshot_path
                )
                self.websocket_manager.send_log_message(
                    self.task_id,
                    "info",
                    f"🖱️ Click completado en: {selector} (URL: {current_url})"
                )
            
        except Exception as e:
            self.logger.error(f"❌ Error haciendo click en {selector} con browser-use: {e}")
            if self.websocket_manager and self.task_id:
                self.websocket_manager.send_log_message(
                    self.task_id,
                    "error",
                    f"Error haciendo click en {selector} con browser-use: {str(e)}"
                )

    async def type_text(self, selector: str, text: str):
        """Escribir texto en elemento con tracking en tiempo real usando browser-use"""
        try:
            if not self.browser_use_agent:
                self.logger.error("❌ browser-use Agent no inicializado para escribir texto")
                return
            
            self.logger.info(f"⌨️ Intentando escribir en {selector}: {text[:50]}... usando browser-use...")
            
            # browser-use maneja la escritura de texto internamente. El método `type` o `fill` es un ejemplo.
            await self.browser_use_agent.type(selector, text)
            
            # Obtener URL y título actuales después de escribir
            current_url = "" # Placeholder
            current_title = "" # Placeholder
            try:
                current_url = await self.browser_use_agent.get_current_url() # Pseudocódigo
                current_title = await self.browser_use_agent.get_current_page_title() # Pseudocódigo
            except AttributeError:
                pass # Manejar si los métodos no existen
            
            screenshot_path = "" # Placeholder
            # if self.browser_use_agent.current_page: # Pseudocódigo
            #    screenshot_path = await self._take_screenshot(self.browser_use_agent.current_page, current_url)
            
            if self.websocket_manager and self.task_id:
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "typing_completed",
                    current_url,
                    current_title,
                    screenshot_path
                )
                self.websocket_manager.send_log_message(
                    self.task_id,
                    "info",
                    f"⌨️ Texto escrito en {selector}: {text[:50]}... (URL: {current_url})"
                )
            
        except Exception as e:
            self.logger.error(f"❌ Error escribiendo en {selector} con browser-use: {e}")
            if self.websocket_manager and self.task_id:
                self.websocket_manager.send_log_message(
                    self.task_id,
                    "error",
                    f"Error escribiendo en {selector} con browser-use: {str(e)}"
                )

    async def extract_data(self, selector: str) -> dict:
        """Extraer datos de la página con tracking en tiempo real usando browser-use"""
        try:
            if not self.browser_use_agent:
                self.logger.error("❌ browser-use Agent no inicializado para extracción de datos")
                return {"count": 0, "data": []}
            
            self.logger.info(f"🔍 Intentando extraer datos con selector: {selector} usando browser-use...")
            
            # browser-use puede tener un método para extraer datos o se puede usar su capacidad de ejecutar JS.
            # La API exacta de browser-use para extracción puede variar. Se asume un método como `extract_elements`.
            extracted_elements_raw = await self.browser_use_agent.extract_elements(selector) # Pseudocódigo
            
            data = []
            for element in extracted_elements_raw:
                # Adaptar la estructura de datos según lo que devuelva browser-use.
                # Esto es un ejemplo basado en la estructura actual de Mitosis.
                text_content = element.get("text", "").strip()
                href_attr = element.get("href", None)
                data.append({
                    "text": text_content,
                    "href": href_attr,
                    "type": "link" if href_attr else "text"
                })
            
            result = {
                "count": len(data),
                "data": data,
                "selector": selector,
                "timestamp": time.time()
            }
            
            if self.websocket_manager and self.task_id:
                self.websocket_manager.send_data_collection_update(
                    self.task_id,
                    f"extraction-{selector}",
                    f"Datos extraídos: {len(data)} elementos encontrados",
                    data[:3]  # Enviar muestra de 3 elementos
                )
                self.websocket_manager.send_log_message(
                    self.task_id,
                    "info",
                    f"🔍 Datos extraídos con selector: {selector} (Elementos: {len(data)})"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo datos con {selector} con browser-use: {e}")
            if self.websocket_manager and self.task_id:
                self.websocket_manager.send_log_message(
                    self.task_id,
                    "error",
                    f"Error extrayendo datos con {selector} con browser-use: {str(e)}"
                )
            return {"count": 0, "data": [], "error": str(e)}

    async def _take_screenshot(self, page: Page, url: str) -> str:
        """Tomar screenshot de la página actual. Adaptado para trabajar con browser-use si es posible.
        Este método podría necesitar ser refactorizado si browser-use no expone la página de Playwright directamente.
        Una alternativa es que browser-use tenga su propio método de captura de pantalla o que se use una instancia
        separada de Playwright solo para capturas, adjuntándose al navegador de browser-use.
        """
        # ... (código existente de _take_screenshot, con posibles adaptaciones)
        # Si browser-use expone la página de Playwright, se puede usar directamente:
        # await page.screenshot(path=screenshot_path, quality=20, full_page=False)
        # Si no, browser-use podría tener un método como: await self.browser_use_agent.take_screenshot(path=...)
        # O se podría mantener una instancia de Playwright para este propósito, adjuntándose al navegador.
        
        # Por ahora, se mantiene el código original asumiendo que 'page' es accesible o se adaptará.
        try:
            if not self.task_id:
                return ""
            
            import os
            import time
            
            timestamp = int(time.time() * 1000)
            hostname = url.replace("https://", "").replace("http://", "").split("/")[0]
            safe_hostname = "".join(c for c in hostname if c.isalnum() or c in ".-_")[:20]
            screenshot_name = f"screenshot_{safe_hostname}_{timestamp}.png"
            screenshot_path = os.path.join(self.screenshot_dir, screenshot_name)
            
            # ✅ Adaptación: Si browser-use no expone la página directamente, se necesitará un mecanismo alternativo.
            # Una opción es que browser-use tenga un método para tomar capturas, o usar una instancia de Playwright
            # que se adjunte al navegador de browser-use.
            # Por simplicidad en este ejemplo, asumimos que 'page' es la página activa de browser-use o se puede obtener.
            # Si no, este método necesitará una refactorización más profunda.
            
            # Pseudocódigo para tomar screenshot si browser-use no expone la página directamente:
            # if self.browser_use_agent and hasattr(self.browser_use_agent, 'get_current_playwright_page'):
            #     current_playwright_page = await self.browser_use_agent.get_current_playwright_page()
            #     if current_playwright_page:
            #         await current_playwright_page.screenshot(path=screenshot_path, quality=20, full_page=False)
            # else:
            #     self.logger.warning("No se pudo obtener la página de Playwright de browser-use para screenshot.")
            #     return ""
            
            # Para mantener la compatibilidad con el código existente, se asume que 'page' es válida.
            # Si 'page' proviene de browser-use, asegúrate de que sea un objeto Page de Playwright.
            await page.screenshot(path=screenshot_path, quality=20, full_page=False)
            
            screenshot_url = f"/api/files/screenshots/{self.task_id}/{screenshot_name}"
            
            self.logger.info(f"📸 Screenshot guardado: {screenshot_path}")
            return screenshot_url
            
        except Exception as e:
            self.logger.error(f"❌ Error tomando screenshot: {e}")
            return ""

    async def close_browser(self):
        """Cerrar navegador y limpiar recursos, incluyendo browser-use Agent"""
        try:
            if self.browser_use_agent:
                await self.browser_use_agent.close() # Asumiendo que browser-use tiene un método close
                self.logger.info("browser-use Agent cerrado.")
            # ... (resto del código de cierre de navegador existente)
            if self.browser:
                await self.browser.close()
                self.logger.info("Navegador Playwright cerrado.")
            if self.playwright:
                await self.playwright.stop()
                self.logger.info("Playwright detenido.")
        except Exception as e:
            self.logger.error(f"Error cerrando navegador/browser-use Agent: {e}")

```

**Consideraciones Adicionales para `web_browser_manager.py`:**

*   **Instancia de LLM para `browser-use`:** La inicialización de `browser_use.Agent` requiere una instancia de LLM. En `Mitosis`, esta instancia debería ser la misma que utiliza el `MitosisRealAgent` para sus operaciones principales. Esto podría requerir pasar el LLM al constructor de `WebBrowserManager` o tener un método para obtenerlo del agente principal.
*   **Manejo de `_take_screenshot`:** Este es el punto más delicado. Si `browser-use` no expone directamente el objeto `Page` de `Playwright` que está utilizando, el método `_take_screenshot` necesitará una refactorización. Las opciones incluyen:
    *   Que `browser-use` tenga su propio método para tomar capturas de pantalla.
    *   Mantener una instancia separada de `Playwright` en `WebBrowserManager` que se adjunte al navegador lanzado por `browser-use` para tomar capturas. Esto podría ser complejo.
    *   Modificar `browser-use` (si es posible) para que exponga la `Page` actual.
*   **Eventos de Observabilidad de `browser-use`:** `browser-use` está diseñado para que los LLMs interpreten el contenido del navegador. Esto significa que internamente, `browser-use` puede estar generando representaciones del DOM o eventos de alto nivel (ej. "elemento interactivo encontrado", "información clave extraída"). Si `browser-use` expone estos eventos, se pueden mapear a los mensajes del `websocket_manager` para proporcionar una visualización más rica en el frontend. Esto requeriría explorar la API de `browser-use` en detalle.

### 4.2. Modificaciones en `backend/unified_api.py`

Las modificaciones en `unified_api.py` serán mínimas, ya que la interfaz de comunicación a través del `websocket_manager` se mantendrá. El `UnifiedMitosisAPI` seguirá recibiendo los mismos tipos de eventos y datos, pero la información contenida en ellos será más rica si `browser-use` proporciona más detalles.

**Paso 1: Asegurar que `websocket_manager` esté disponible para `WebBrowserManager`**

El `WebBrowserManager` ya recibe `websocket_manager` en su constructor. Es crucial asegurarse de que la instancia de `WebBrowserManager` que se pasa al `MitosisRealAgent` (y que este a su vez usa) tenga el `websocket_manager` correctamente configurado para emitir eventos a través de `SocketIO`.

```python
# backend/unified_api.py

# ... (importaciones existentes)

# Importar WebBrowserManager
from web_browser_manager import WebBrowserManager, BrowserConfig # Asegúrate de que la ruta sea correcta

class UnifiedMitosisAPI:
    # ... (constructor existente)
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.app = Flask(__name__)
        CORS(self.app, origins="*")
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        if config is None:
            config = AgentConfig(
                ollama_url="http://localhost:11434",
                openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
                prefer_local_models=True,
                max_cost_per_1k_tokens=0.01,
                memory_db_path="unified_agent.db",
                max_short_term_messages=100,
                max_concurrent_tasks=2,
                debug_mode=True
            )
        
        # ✅ Pasar el websocket_manager al MitosisRealAgent para que lo use el WebBrowserManager
        # Esto asume que MitosisRealAgent acepta un websocket_manager o que WebBrowserManager
        # se inicializa dentro de MitosisRealAgent y se le pasa el manager.
        # Si MitosisRealAgent inicializa WebBrowserManager internamente, se debe modificar
        # la inicialización dentro de MitosisRealAgent para pasar self.websocket_manager.
        
        # Ejemplo (pseudocódigo) si MitosisRealAgent necesita el websocket_manager:
        # self.agent = MitosisRealAgent(config, websocket_manager=self) # 'self' es la instancia de UnifiedMitosisAPI
        
        # Asumiendo que MitosisRealAgent ya tiene un mecanismo para pasar el websocket_manager
        # al WebBrowserManager, o que WebBrowserManager puede acceder a él globalmente.
        # Si no, se necesitará una refactorización en MitosisRealAgent.
        
        # Para este ejemplo, se asume que el websocket_manager se pasa correctamente.
        # Si MitosisRealAgent inicializa WebBrowserManager, la modificación iría allí.
        # Por ejemplo, en agent_core_real.py, en la inicialización de MitosisRealAgent:
        # self.web_browser_manager = WebBrowserManager(config.browser_config, websocket_manager=self.websocket_manager, task_id=self.task_id)
        
        self.agent = MitosisRealAgent(config) # Mantener como está si el websocket_manager se inyecta de otra forma
        self.start_time = time.time()
        self.monitor_pages: List[MonitorPage] = []
        self.active_sessions: Dict[str, str] = {}
        
        self._create_initial_todo_page()
        self._setup_routes()
        self._setup_socketio_events()
        
        logger.info("Unified Mitosis API initialized successfully")

    # ... (resto de la clase UnifiedMitosisAPI existente)

    def send_browser_activity(self, task_id: str, activity_type: str, url: str, title: str, screenshot_path: str):
        """Método para enviar actividad del navegador al frontend via SocketIO.
        Este método será llamado por WebBrowserManager.
        """
        # Crear una MonitorPage o un evento SocketIO específico para la actividad del navegador
        # Se puede adaptar la estructura de MonitorPage o crear un nuevo tipo de evento.
        
        # Ejemplo de adaptación de MonitorPage:
        content = f"**Actividad:** {activity_type}\n**URL:** {url}\n**Título:** {title}"
        if screenshot_path:
            content += f"\n**Screenshot:** ![Screenshot]({screenshot_path})"
            
        self._add_monitor_page(
            title=f"Actividad Navegador: {activity_type}",
            content=content,
            page_type="browser-activity",
            metadata={
                "task_id": task_id,
                "activity_type": activity_type,
                "url": url,
                "title": title,
                "screenshot_url": screenshot_path
            }
        )
        
        # Además de _add_monitor_page, se puede emitir un evento SocketIO más específico
        # para que el frontend lo maneje de forma diferenciada para la visualización en tiempo real.
        self.socketio.emit(
            'browser_activity_update',
            {
                "task_id": task_id,
                "activity_type": activity_type,
                "url": url,
                "title": title,
                "screenshot_url": screenshot_path,
                "timestamp": datetime.now().isoformat()
            },
            room=f"monitor_{task_id}" # Emitir a la sala específica de la tarea si existe
        )

    def send_log_message(self, task_id: str, level: str, message: str):
        """Método para enviar mensajes de log al frontend via SocketIO.
        Este método será llamado por WebBrowserManager.
        """
        self._add_monitor_page(
            title=f"Log ({level.upper()}): {task_id}",
            content=f"**Nivel:** {level.upper()}\n**Mensaje:** {message}",
            page_type="log-message",
            metadata={
                "task_id": task_id,
                "level": level,
                "message": message
            }
        )
        
        self.socketio.emit(
            'log_message_update',
            {
                "task_id": task_id,
                "level": level,
                "message": message,
                "timestamp": datetime.now().isoformat()
            },
            room=f"monitor_{task_id}"
        )

    def send_data_collection_update(self, task_id: str, update_id: str, message: str, data: List[Dict]):
        """Método para enviar actualizaciones de recolección de datos al frontend via SocketIO.
        Este método será llamado por WebBrowserManager.
        """
        content = f"**Actualización de Datos:** {message}\n**ID de Actualización:** {update_id}\n**Datos (muestra):** {json.dumps(data, indent=2)}"
        self._add_monitor_page(
            title=f"Recolección de Datos: {update_id}",
            content=content,
            page_type="data-collection",
            metadata={
                "task_id": task_id,
                "update_id": update_id,
                "message": message,
                "data_sample": data
            }
        )
        
        self.socketio.emit(
            'data_collection_update',
            {
                "task_id": task_id,
                "update_id": update_id,
                "message": message,
                "data_sample": data,
                "timestamp": datetime.now().isoformat()
            },
            room=f"monitor_{task_id}"
        )

```

**Consideraciones Adicionales para `unified_api.py`:**

*   **Inyección de Dependencias:** Es fundamental que la instancia de `WebBrowserManager` dentro de `MitosisRealAgent` reciba la instancia correcta de `websocket_manager` (que es `self` de `UnifiedMitosisAPI`). Esto probablemente requerirá modificar el constructor de `MitosisRealAgent` en `agent_core_real.py` para aceptar `websocket_manager` y pasarlo a `WebBrowserManager`.
*   **Eventos Específicos para Frontend:** Se han añadido métodos `send_browser_activity`, `send_log_message`, y `send_data_collection_update` a `UnifiedMitosisAPI`. Estos métodos serán llamados por `WebBrowserManager` y emitirán eventos `SocketIO` específicos (`browser_activity_update`, `log_message_update`, `data_collection_update`) que el frontend puede escuchar para una visualización más granular y en tiempo real, además de la creación de `MonitorPage`s genéricas.

### 4.3. Impacto en `agent_core_real.py`

El archivo `agent_core_real.py` (donde reside `MitosisRealAgent`) necesitará una pequeña modificación para asegurar que el `WebBrowserManager` se inicialice con la instancia correcta del `websocket_manager`.

```python
# backend/agent_core_real.py (Ejemplo de modificación)

# ... (importaciones existentes)
from web_browser_manager import WebBrowserManager, BrowserConfig

class MitosisRealAgent:
    def __init__(self, config: AgentConfig, websocket_manager=None):
        self.config = config
        self.memory_manager = MemoryManager(config.memory_db_path)
        self.task_manager = TaskManager(self.memory_manager)
        self.model_manager = ModelManager(config.ollama_url, config.openrouter_api_key, config.prefer_local_models)
        self.prompt_manager = EnhancedPromptManager()
        
        # ✅ Pasar el websocket_manager al WebBrowserManager
        self.web_browser_manager = WebBrowserManager(
            config=BrowserConfig(), # Usar la configuración de navegador de Mitosis si existe
            websocket_manager=websocket_manager, # Aquí se inyecta el manager
            task_id=None # El task_id se puede establecer cuando se inicia una tarea específica
        )
        
        # ✅ Inicializar el WebBrowserManager de forma asíncrona
        asyncio.create_task(self.web_browser_manager.initialize())
        
        # ... (resto del constructor)

    # ... (otros métodos del agente)

    async def process_web_action(self, action_type: str, *args, **kwargs):
        """Método para que el agente ejecute acciones web a través del WebBrowserManager.
        Este método sería llamado por la lógica del agente cuando necesite interactuar con el navegador.
        """
        if action_type == "navigate":
            await self.web_browser_manager.navigate(args[0])
        elif action_type == "click":
            await self.web_browser_manager.click_element(args[0])
        elif action_type == "type":
            await self.web_browser_manager.type_text(args[0], args[1])
        elif action_type == "extract":
            return await self.web_browser_manager.extract_data(args[0])
        # ... (otros tipos de acciones web)

```

### 4.4. Impacto en el Frontend

El frontend de `Mitosis` (ubicado en `frontend/`) necesitará ser actualizado para consumir los nuevos eventos `SocketIO` y renderizar la información de la actividad del navegador de una manera más visual e interactiva. Actualmente, el frontend ya maneja `MonitorPage`s, pero para una visualización en tiempo real de la navegación, se recomienda:

*   **Escuchar Eventos Específicos:** El frontend debe escuchar los eventos `browser_activity_update`, `log_message_update` y `data_collection_update` emitidos por el backend.
*   **Componente de Visualización de Navegación:** Desarrollar un nuevo componente en el frontend (ej. en React/TypeScript) que reciba estos eventos y muestre la actividad del navegador. Esto podría incluir:
    *   Una línea de tiempo de eventos de navegación.
    *   Una galería de capturas de pantalla interactivas.
    *   Una representación simplificada del DOM o de los elementos interactivos.
    *   Animaciones o indicadores visuales para clics y escritura.
*   **Actualización de la Interfaz de Logs:** La terminal de logs actual puede seguir mostrando los mensajes de `log_message_update`, pero con la información adicional de `browser_activity_update` se puede crear una vista dedicada a la actividad del navegador.

## 5. Plan de Implementación Detallado

El siguiente plan de implementación se desglosa en fases para una integración controlada y eficiente.

### Fase 1: Preparación y Configuración de `browser-use`

*   **Objetivo:** Asegurar que `browser-use` esté correctamente instalado y que el LLM de `Mitosis` pueda ser utilizado por `browser-use`.
*   **Acciones:**
    1.  **Instalación de `browser-use`:**
        ```bash
        pip install browser-use
        uv run playwright install # Si no se ha hecho ya
        ```
    2.  **Verificación de LLM:** Confirmar que el LLM que `Mitosis` utiliza (`agent_core_real.py`) es compatible con `browser-use` o crear un *wrapper* si es necesario. `browser-use` soporta `OpenAI`, `Anthropic`, etc. Si `Mitosis` usa un LLM personalizado, se deberá integrar su API con `browser-use`.

### Fase 2: Refactorización de `backend/web_browser_manager.py`

*   **Objetivo:** Reemplazar las interacciones directas con `Playwright` por las de `browser-use` y adaptar el envío de eventos.
*   **Acciones:**
    1.  **Modificar `WebBrowserManager.__init__`:** Añadir `self.browser_use_agent = None`.
    2.  **Modificar `WebBrowserManager.initialize`:**
        *   Eliminar el lanzamiento directo del navegador y la creación de contextos de `Playwright` (a menos que se necesiten para observación paralela).
        *   Instanciar `self.browser_use_agent = Agent(task="...", llm=your_mitosis_llm_instance)`.
        *   Asegurarse de que el `LLM` de `Mitosis` se pase correctamente a `browser-use.Agent`.
    3.  **Refactorizar `navigate`:** Reemplazar `await page.goto(url)` con `await self.browser_use_agent.go_to(url)`. Adaptar la obtención del título y la captura de pantalla.
    4.  **Refactorizar `click_element`:** Reemplazar `await page.click(selector)` con `await self.browser_use_agent.click(selector)`. Adaptar la obtención de URL/título y la captura de pantalla.
    5.  **Refactorizar `type_text`:** Reemplazar `await page.fill(selector, text)` con `await self.browser_use_agent.type(selector, text)`. Adaptar la obtención de URL/título y la captura de pantalla.
    6.  **Refactorizar `extract_data`:** Reemplazar `await page.query_selector_all(selector)` con el método equivalente de `browser-use` (ej. `await self.browser_use_agent.extract_elements(selector)`). Adaptar el procesamiento de los datos extraídos.
    7.  **Adaptar `_take_screenshot`:** Este es el paso más crítico. Si `browser-use` no expone la `Page` de `Playwright` o un método de captura, se deberá implementar una solución alternativa. Una opción es que `WebBrowserManager` mantenga una instancia de `Playwright` solo para capturas, que se adjunte al navegador de `browser-use`.
    8.  **Asegurar el `websocket_manager`:** Verificar que todas las llamadas a `self.websocket_manager.send_browser_activity`, `send_log_message`, etc., sigan funcionando correctamente con la nueva lógica.

### Fase 3: Refactorización de `backend/unified_api.py` y `backend/agent_core_real.py`

*   **Objetivo:** Asegurar la correcta inyección del `websocket_manager` y la invocación de las acciones web del agente.
*   **Acciones:**
    1.  **Modificar `UnifiedMitosisAPI.__init__`:** Asegurarse de que la instancia de `MitosisRealAgent` se inicialice con `websocket_manager=self` (la instancia de `UnifiedMitosisAPI`).
    2.  **Modificar `MitosisRealAgent.__init__`:** Aceptar `websocket_manager` como argumento y pasarlo al constructor de `WebBrowserManager`.
    3.  **Crear `process_web_action` en `MitosisRealAgent`:** Este método centralizará las llamadas a `WebBrowserManager` desde la lógica del agente, permitiendo que el agente decida qué acción web realizar.

### Fase 4: Actualización del Frontend para Visualización Avanzada

*   **Objetivo:** Mejorar la interfaz de usuario para una visualización interactiva de la actividad del navegador.
*   **Acciones:**
    1.  **Actualizar `frontend/src/hooks/useWebSocket.ts` (o similar):** Añadir listeners para los nuevos eventos `SocketIO`: `browser_activity_update`, `log_message_update`, `data_collection_update`.
    2.  **Crear un nuevo componente de React (ej. `BrowserActivityMonitor.tsx`):** Este componente será responsable de renderizar la actividad del navegador. Podría incluir:
        *   Una línea de tiempo de eventos de navegación.
        *   Un carrusel o galería de capturas de pantalla.
        *   Una representación visual de los elementos interactuados (ej. resaltando el selector en la captura de pantalla).
    3.  **Integrar el nuevo componente:** Añadir `BrowserActivityMonitor.tsx` a la interfaz principal de `Mitosis`.
    4.  **Mejorar la visualización de logs:** Adaptar el componente de logs existente para diferenciar los mensajes de actividad del navegador y, quizás, vincularlos a la nueva vista interactiva.

## 6. Consideraciones Técnicas y Mejores Prácticas

### 6.1. Manejo de Errores y Robustez

*   **Captura de Excepciones:** Mantener y mejorar la captura de excepciones en `WebBrowserManager` y `unified_api.py` para manejar fallos de `browser-use` y `Playwright`.
*   **Logging Detallado:** Asegurar que los logs (`self.logger.error`, `self.logger.info`) proporcionen suficiente contexto para depurar problemas relacionados con `browser-use`.
*   **Reintentos y Timeouts:** Implementar lógicas de reintento con retroceso exponencial para operaciones de red o de navegador que puedan fallar temporalmente.

### 6.2. Rendimiento y Recursos

*   **Uso de Headless:** Mantener el modo `headless` para `Playwright` (y por extensión, `browser-use`) en entornos de producción para optimizar el rendimiento y el uso de recursos.
*   **Gestión de Contextos:** `WebBrowserManager` ya tiene un pool de contextos. Asegurarse de que `browser-use` se integre eficientemente con esta gestión o que su propio manejo de recursos sea óptimo.
*   **Optimización de Capturas de Pantalla:** Las capturas de pantalla pueden ser intensivas en recursos. Considerar:
    *   Reducir la calidad de la imagen (`quality=20` ya está en uso).
    *   Tomar capturas solo en eventos clave o a intervalos definidos.
    *   Implementar un sistema de limpieza para `/tmp/screenshots`.

### 6.3. Seguridad

*   **Validación de Entradas:** Validar todas las entradas de usuario y de agente antes de pasarlas a `browser-use` o `Playwright` para prevenir inyecciones o comportamientos inesperados.
*   **Aislamiento:** Si es posible, ejecutar las operaciones del navegador en un entorno aislado (ej. Docker) para contener cualquier riesgo de seguridad.

### 6.4. Mantenimiento y Escalabilidad

*   **Documentación Interna:** Documentar claramente los cambios realizados y las decisiones de diseño, especialmente en relación con la interacción entre `Mitosis`, `browser-use` y `Playwright`.
*   **Pruebas Automatizadas:** Ampliar la suite de pruebas unitarias y de integración para cubrir la nueva funcionalidad de `browser-use` y asegurar que los cambios no introduzcan regresiones.
*   **Monitoreo:** Utilizar las capacidades de monitoreo en tiempo real para observar el rendimiento y la estabilidad de la integración en producción.

## 7. Conclusión y Próximos Pasos

La integración de `browser-use` en el proyecto `Mitosis` es una evolución lógica que permitirá una interacción más sofisticada y una visualización más rica de la actividad de navegación del agente. El informe ha detallado las modificaciones específicas necesarias en `backend/web_browser_manager.py`, `backend/unified_api.py` y `backend/agent_core_real.py`, junto con las consideraciones para la actualización del frontend.

Se recomienda proceder con la implementación siguiendo el plan detallado, prestando especial atención a la inyección de la instancia de LLM en `browser-use.Agent` y la adaptación del mecanismo de captura de pantalla. La mejora en la observabilidad y la experiencia de depuración justificará el esfuerzo de refactorización, posicionando a `Mitosis` con una capacidad de monitoreo de agentes de IA de vanguardia.

**Próximos Pasos Sugeridos:**

1.  **Confirmar la compatibilidad del LLM de Mitosis con `browser-use`:** Antes de cualquier refactorización de código, verificar si el LLM actual de `Mitosis` puede ser directamente utilizado por `browser-use`. Si no, desarrollar un *wrapper* o una estrategia de adaptación.
2.  **Prototipo de `_take_screenshot`:** Dada la criticidad de las capturas de pantalla para la visualización, desarrollar un pequeño prototipo que demuestre cómo `_take_screenshot` funcionará con `browser-use` (ya sea a través de un método de `browser-use` o adjuntando una instancia de `Playwright` al navegador de `browser-use`).
3.  **Implementación de la Fase 1:** Proceder con la refactorización de `WebBrowserManager` para usar `browser-use` para las operaciones básicas, realizando pruebas exhaustivas.
4.  **Desarrollo del Frontend:** En paralelo, comenzar el desarrollo del componente de visualización de actividad del navegador en el frontend, basándose en los nuevos eventos `SocketIO`.

