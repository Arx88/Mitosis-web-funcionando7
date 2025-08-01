# Informe de Análisis y Recomendaciones para MitosisV5

## 1. Introducción

El objetivo de este informe es analizar el código proporcionado de MitosisV5, específicamente el backend (`server.py`, `agent_routes.py`, `websocket_manager.py`) y el frontend (`TerminalView.tsx`), para identificar las funcionalidades existentes y las ausencias que impiden la visualización en tiempo real de la navegación web, los datos recolectados y el proceso de armado de informes en el terminal de TaskView, sin modificar la UI existente. Se prestará especial atención a la integración de **Playwright con Selenium** para la captura de eventos de navegación.

## 2. Arquitectura General

El proyecto MitosisV5 sigue una arquitectura cliente-servidor con un backend en Flask y un frontend en React. La comunicación en tiempo real se gestiona a través de WebSockets (SocketIO).

*   **Backend:**
    *   `server.py`: Punto de entrada principal, configura Flask, CORS, MongoDB, inicializa `WebSocketManager`, `OllamaService` y `ToolManager`. Registra las rutas del agente.
    *   `websocket_manager.py`: Gestiona las conexiones WebSocket y la emisión de eventos en tiempo real a los clientes. Define varios tipos de actualización (`UpdateType`) como `TASK_STARTED`, `TASK_PROGRESS`, `STEP_STARTED`, `STEP_COMPLETED`, etc.
    *   `agent_routes.py`: Contiene las rutas API para la interacción del agente, incluyendo la ejecución de pasos (`execute_single_step_detailed`) y la obtención del estado de la tarea (`get_task_status`). Utiliza `emit_step_event` para enviar actualizaciones a través del WebSocket.
    *   `web_browser_manager.py`: **Este módulo es crucial para la interacción con el navegador web y donde se integraría Playwright/Selenium.**

*   **Frontend:**
    *   `TerminalView.tsx`: Componente principal que muestra el estado de la ejecución de la tarea, el plan, los resultados de las herramientas y los logs. Utiliza un `AppContext` para gestionar los `monitorPages` (páginas del monitor) y el `currentPageIndex` (índice de la página actual).

## 3. Análisis de la Implementación Actual

### 3.1. Backend (server.py, agent_routes.py, websocket_manager.py)

El `WebSocketManager` está bien estructurado para enviar actualizaciones de tareas y pasos. Métodos como `send_task_progress`, `send_step_started`, `send_step_completed` y `emit_to_task` son fundamentales para la comunicación en tiempo real. El `agent_routes.py` ya emite eventos de `step_started` y `step_completed`.

**Puntos fuertes:**
*   Infraestructura WebSocket ya establecida y funcional.
*   Manejo de `task_id` y `session_id` para actualizaciones específicas de tareas.
*   Tipos de actualización (`UpdateType`) bien definidos para diferentes eventos de la tarea.

**Ausencias clave para la visualización en tiempo real:**
*   **Navegación Web en Tiempo Real:** No se observa en el código revisado (`server.py`, `agent_routes.py`) que los eventos de navegación web (cambios de URL, contenido de la página, interacciones) sean capturados por `web_browser_manager.py` y luego enviados a través del WebSocket. Para mostrar la navegación en tiempo real, se necesita un mecanismo que envíe estas actualizaciones al frontend a medida que ocurren. **La integración de Playwright/Selenium es clave aquí.**
*   **Datos Recolectados en Tiempo Real:** Similar a la navegación, la recolección de datos (ej. resultados de búsquedas, scraping) no parece estar siendo enviada de forma granular y en tiempo real al frontend. Los `ToolResult` se envían al final de la ejecución de una herramienta, pero no durante el proceso de recolección.
*   **Armado de Informes en Tiempo Real:** El informe final se genera y carga al completar la tarea (`loadFinalReport` en el frontend). No hay un mecanismo para enviar actualizaciones incrementales del informe a medida que se va construyendo en el backend.

### 3.2. Frontend (TerminalView.tsx)

El componente `TerminalView` es robusto y ya maneja la visualización de planes, resultados de herramientas y logs. Utiliza `monitorPages` para gestionar diferentes páginas de contenido (plan, ejecución de herramientas, informe). La integración con `AppContext` para `monitorPages` es un buen enfoque para el manejo de estado.

**Puntos fuertes:**
*   Diseño modular con `MonitorPage` para diferentes tipos de contenido.
*   Manejo de estados de inicialización y timers para pasos.
*   Uso de `AppContext` para centralizar el estado de las páginas del monitor.
*   Capacidad para mostrar `ToolExecutionDetails`.

**Ausencias clave para la visualización en tiempo real:**
*   **Consumo de Eventos de Navegación Web:** `TerminalView` no tiene lógica explícita para escuchar y renderizar eventos de navegación web en tiempo real (ej. URL actual, capturas de pantalla, interacciones del navegador). Aunque `executionData` se pasa, no se observa cómo se utiliza para este propósito específico.
*   **Consumo de Datos Recolectados Granulares:** Similar al backend, el frontend no está configurado para recibir y mostrar actualizaciones granulares de datos recolectados. Se espera `ToolResult[]` que son resultados finales, no intermedios.
*   **Consumo de Actualizaciones de Informe en Tiempo Real:** `TerminalView` carga el informe final una vez que la tarea está completada. No hay un mecanismo para recibir y mostrar el informe a medida que se construye.
*   **Manejo de `terminalOutput`:** Aunque existe un estado `terminalOutput`, no se observa cómo se alimenta dinámicamente con logs o actividades en tiempo real del agente más allá de la inicialización.

## 4. Identificación de lo que falta para mostrar datos en tiempo real

Para lograr la visualización en tiempo real de la navegación web, los datos recolectados y el armado de informes, se necesita:

### 4.1. Para Navegación Web en Tiempo Real (con Playwright/Selenium):

1.  **Backend (`web_browser_manager.py` y `agent_routes.py`):**
    *   **Instrumentación de Playwright/Selenium:** El módulo `web_browser_manager.py` (o donde se gestione la instancia del navegador) debe ser instrumentado para capturar eventos del navegador. Esto implica usar los listeners de eventos de Playwright o Selenium.
        *   **Playwright:** Puedes usar `page.on('urlchanged')`, `page.on('load')`, `page.on('domcontentloaded')`, `page.on('request')`, `page.on('response')`. Para interacciones, puedes interceptar métodos como `page.click()`, `page.fill()`, etc., o usar `page.evaluate()` para inyectar JavaScript que capture eventos del DOM.
        *   **Selenium:** Puedes usar `driver.current_url` para cambios de URL, y para eventos más detallados, necesitarías inyectar JavaScript en la página usando `driver.execute_script()` para monitorear eventos del DOM (clicks, inputs, etc.) y luego pasar esa información de vuelta a Python.
    *   **Captura de Contenido y Capturas de Pantalla:** En cada evento relevante (cambio de URL, carga de página), se debe capturar la URL actual, el título de la página y, crucialmente, una captura de pantalla. Las capturas de pantalla pueden guardarse temporalmente en el backend y su URL (o base64 si son pequeñas) enviarse al frontend.
    *   **Emisión de Eventos WebSocket:** Estos eventos capturados deben ser enviados al frontend a través del `WebSocketManager`. Se podría definir un nuevo `UpdateType` (ej. `BROWSER_ACTIVITY`) o extender `STEP_UPDATE` con un subtipo específico.
    *   **Ejemplo de Integración (Pseudocódigo para `web_browser_manager.py`):**

        ```python
        # backend/src/web_browser_manager.py (ejemplo conceptual)
        from playwright.sync_api import sync_playwright
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager
        import base64
        import os
        import time

        class WebBrowserManager:
            def __init__(self, websocket_manager, task_id):
                self.websocket_manager = websocket_manager
                self.task_id = task_id
                self.browser = None
                self.page = None # Para Playwright
                self.driver = None # Para Selenium
                self.browser_type = "playwright" # o "selenium"

            def initialize_browser(self):
                if self.browser_type == "playwright":
                    self.playwright_instance = sync_playwright().start()
                    self.browser = self.playwright_instance.chromium.launch(headless=True)
                    self.page = self.browser.new_page()
                    self._setup_playwright_listeners()
                elif self.browser_type == "selenium":
                    service = ChromeService(ChromeDriverManager().install())
                    options = webdriver.ChromeOptions()
                    options.add_argument('--headless')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    self.driver = webdriver.Chrome(service=service, options=options)
                    self._setup_selenium_listeners()
                self.websocket_manager.send_log_message(self.task_id, "info", f"Navegador {self.browser_type} inicializado.")

            def _setup_playwright_listeners(self):
                self.page.on("urlchanged", lambda url: self._on_url_changed(url))
                self.page.on("load", lambda: self._on_page_loaded())
                # Puedes añadir más listeners para clicks, inputs, etc.
                # self.page.on("request", lambda request: self._on_request(request))
                # self.page.on("response", lambda response: self._on_response(response))

            def _on_url_changed(self, url):
                self.websocket_manager.send_browser_activity(self.task_id, "url_changed", url, "", "")

            def _on_page_loaded(self):
                current_url = self.page.url
                title = self.page.title()
                screenshot_path = self._take_screenshot()
                self.websocket_manager.send_browser_activity(self.task_id, "page_loaded", current_url, title, screenshot_path)
                self.websocket_manager.send_log_message(self.task_id, "info", f"Página cargada: {title} ({current_url})")

            def _setup_selenium_listeners(self):
                # Selenium no tiene listeners nativos tan robustos como Playwright.
                # Se requiere polling o inyección de JS para eventos de DOM.
                # Para URL, se puede hacer polling en el bucle principal de la herramienta.
                pass

            def _take_screenshot(self) -> str:
                screenshot_dir = f"/tmp/screenshots/{self.task_id}"
                os.makedirs(screenshot_dir, exist_ok=True)
                timestamp = int(time.time() * 1000)
                screenshot_name = f"screenshot_{timestamp}.png"
                screenshot_path = os.path.join(screenshot_dir, screenshot_name)
                if self.browser_type == "playwright":
                    self.page.screenshot(path=screenshot_path)
                elif self.browser_type == "selenium":
                    self.driver.save_screenshot(screenshot_path)
                # Retornar una URL accesible para el frontend (ej. a través de un endpoint de Flask)
                return f"/files/screenshots/{self.task_id}/{screenshot_name}"

            def navigate(self, url):
                if self.browser_type == "playwright":
                    self.page.goto(url)
                elif self.browser_type == "selenium":
                    self.driver.get(url)
                self.websocket_manager.send_log_message(self.task_id, "info", f"Navegando a: {url}")
                # For Selenium, manually trigger page loaded event after navigation
                if self.browser_type == "selenium":
                    time.sleep(1) # Give it a moment to load
                    current_url = self.driver.current_url
                    title = self.driver.title
                    screenshot_path = self._take_screenshot()
                    self.websocket_manager.send_browser_activity(self.task_id, "page_loaded", current_url, title, screenshot_path)
                    self.websocket_manager.send_log_message(self.task_id, "info", f"Página cargada (Selenium): {title} ({current_url})")

            def close_browser(self):
                if self.browser_type == "playwright" and self.browser:
                    self.browser.close()
                    self.playwright_instance.stop()
                elif self.browser_type == "selenium" and self.driver:
                    self.driver.quit()
                self.websocket_manager.send_log_message(self.task_id, "info", f"Navegador {self.browser_type} cerrado.")

        # En agent_routes.py, al ejecutar un paso de navegación o búsqueda:
        # from ..web_browser_manager import WebBrowserManager
        # ...
        # ws_manager = get_websocket_manager()
        # browser_manager = WebBrowserManager(ws_manager, task_id)
        # browser_manager.initialize_browser()
        # browser_manager.navigate("https://www.ejemplo.com")
        # ...
        # browser_manager.close_browser()
        ```

2.  **Frontend (`TerminalView.tsx` y `AppContext.tsx`):**
    *   **Suscripción a Eventos de Navegación:** `TerminalView` (o un componente padre que gestione la conexión WebSocket) debe suscribirse a los nuevos eventos de navegación (`BROWSER_ACTIVITY`).
    *   **Actualización de `monitorPages`:** Cada evento de navegación debe traducirse en una nueva `MonitorPage` de tipo `web-browsing` o similar, que contenga la URL, el título y la captura de pantalla. Estas páginas deben agregarse a `monitorPages` y el `currentPageIndex` debe actualizarse para mostrar la última actividad.
    *   **Servir Capturas de Pantalla:** Necesitarás un endpoint en Flask (`server.py`) para servir las capturas de pantalla guardadas en `/tmp/screenshots/`. Por ejemplo:

        ```python
        # server.py
        from flask import send_from_directory

        @app.route("/files/screenshots/<task_id>/<filename>")
        def serve_screenshot(task_id, filename):
            return send_from_directory(f"/tmp/screenshots/{task_id}", filename)
        ```

    *   **Renderizado Específico:** Dentro de `TerminalView`, se necesitará una lógica de renderizado para las páginas de navegación, mostrando la URL, el título y la imagen de la captura de pantalla.

### 4.2. Para Datos Recolectados en Tiempo Real:

1.  **Backend (`agent_routes.py` y módulos de herramientas):**
    *   **Emisión de Eventos Intermedios:** Cuando una herramienta (ej. `web_search`, `data_analysis`) recolecta datos, debe enviar actualizaciones intermedias a través del WebSocket, no solo el resultado final. Esto podría ser un `STEP_UPDATE` con un payload específico para datos.
    *   **Ejemplo de Payload:**
        ```json
        {
            "task_id": "task_xyz",
            "type": "step_update",
            "timestamp": "...",
            "data": {
                "step_id": "step_123",
                "update_type": "data_collected",
                "data_summary": "Se encontraron 10 resultados de búsqueda",
                "partial_data": [...] // Pequeña muestra o resumen
            }
        }
        ```

2.  **Frontend (`TerminalView.tsx`):**
    *   **Consumo de Actualizaciones de Datos:** `TerminalView` debe escuchar estos eventos `step_update` y, si el `update_type` es `data_collected`, actualizar la `MonitorPage` correspondiente al paso actual o crear una nueva página de tipo `data-collection`.
    *   **Visualización de Datos Parciales:** La `MonitorPage` debe ser capaz de mostrar estos datos parciales o un resumen, quizás en un formato de tabla o lista.

### 4.3. Para Armado de Informes en Tiempo Real:

1.  **Backend (Módulo de Generación de Informes):**
    *   **Generación Incremental:** Si el informe se construye en varias etapas, cada etapa debe generar una porción del informe y enviarla al frontend.
    *   **Emisión de Eventos de Informe:** Se podría usar un `UpdateType` como `REPORT_PROGRESS` o `REPORT_SECTION_COMPLETED`.
    *   **Ejemplo de Payload:**
        ```json
        {
            "task_id": "task_xyz",
            "type": "report_progress",
            "timestamp": "...",
            "data": {
                "section_title": "Introducción",
                "content_delta": "Contenido de la introducción...",
                "full_report_so_far": "..." // Opcional, para reconstruir
            }
        }
        ```

2.  **Frontend (`TerminalView.tsx`):**
    *   **Actualización de Página de Informe:** `TerminalView` debe tener una `MonitorPage` dedicada al informe. A medida que llegan los eventos `REPORT_PROGRESS`, el contenido de esta página se debe actualizar incrementalmente. Esto podría implicar concatenar `content_delta` o reemplazar el `full_report_so_far`.
    *   **Renderizado de Markdown:** Dado que el informe es Markdown, el componente ya tiene la capacidad de renderizarlo. Solo necesita actualizar el contenido de la página del monitor.

### 4.4. Consolidación y Mejora de Logs en TerminalView:

*   **Backend (`websocket_manager.py` y `agent_routes.py`):**
    *   **Eventos de Log Genéricos:** Además de los eventos estructurados, se podría emitir un evento `LOG_MESSAGE` para cualquier log relevante que deba aparecer en el terminal, incluyendo mensajes de depuración, errores, o información general del agente.
    *   **Ejemplo de Payload:**
        ```json
        {
            "task_id": "task_xyz",
            "type": "log_message",
            "timestamp": "...",
            "data": {
                "level": "info", // info, warn, error
                "message": "Agente iniciando búsqueda web para 'inteligencia artificial'"
            }
        }
        ```

*   **Frontend (`TerminalView.tsx`):**
    *   **Consumo de `LOG_MESSAGE`:** El `TerminalView` debe escuchar estos eventos y agregarlos a su estado `terminalOutput` para mostrarlos en la sección de logs. Esto proporcionaría una visión más detallada de lo que el agente está haciendo en tiempo real.

## 5. Soluciones Específicas para el Código

Aquí se detallan las modificaciones necesarias en los archivos clave para implementar las funcionalidades descritas.

### 5.1. `backend/src/websocket/websocket_manager.py`

**1. Añadir nuevos `UpdateType`:**

```python
# ... (imports existentes)

class UpdateType(Enum):
    # ... (tipos existentes)
    BROWSER_ACTIVITY = "browser_activity" # Para eventos de navegación web
    DATA_COLLECTION_UPDATE = "data_collection_update" # Para datos recolectados incrementalmente
    REPORT_PROGRESS = "report_progress" # Para actualizaciones incrementales del informe
    LOG_MESSAGE = "log_message" # Para mensajes de log genéricos

class WebSocketManager:
    # ... (métodos existentes)

    def send_browser_activity(self, task_id: str, activity_type: str, url: str, title: str = "", screenshot_url: str = ""):
        """Send browser activity notification"""
        self.send_update(task_id, UpdateType.BROWSER_ACTIVITY, {
            'activity_type': activity_type,
            'url': url,
            'title': title,
            'screenshot_url': screenshot_url,
            'message': f'Navegando a: {url}' if activity_type == 'page_loaded' else f'Actividad en navegador: {activity_type}'
        })

    def send_data_collection_update(self, task_id: str, step_id: str, data_summary: str, partial_data: Any = None):
        """Send incremental data collection update"""
        self.send_update(task_id, UpdateType.DATA_COLLECTION_UPDATE, {
            'step_id': step_id,
            'data_summary': data_summary,
            'partial_data': partial_data,
            'message': f'Datos recolectados: {data_summary}'
        })

    def send_report_progress(self, task_id: str, section_title: str, content_delta: str, full_report_so_far: str = ""):
        """Send incremental report progress update"""
        self.send_update(task_id, UpdateType.REPORT_PROGRESS, {
            'section_title': section_title,
            'content_delta': content_delta,
            'full_report_so_far': full_report_so_far,
            'message': f'Generando informe: {section_title}'
        })

    def send_log_message(self, task_id: str, level: str, message: str):
        """Send generic log message to terminal"""
        self.send_update(task_id, UpdateType.LOG_MESSAGE, {
            'level': level,
            'message': message
        })

```

### 5.2. `backend/src/routes/agent_routes.py`

**1. Integrar llamadas a `WebSocketManager` para eventos de navegación y datos:**

Deberás identificar los puntos en tu lógica de ejecución de herramientas (especialmente las relacionadas con `web_search`, `web_scraping`, `research`) donde ocurren estos eventos y llamar a los nuevos métodos del `websocket_manager`.

Por ejemplo, si tienes una función `execute_web_search`:

```python
# ... (imports existentes)

# Obtener websocket_manager de current_app
def get_websocket_manager():
    return current_app.websocket_manager

# ... (otras funciones)

def execute_single_step_logic(step: Dict[str, Any], user_message: str, task_id: str) -> Dict[str, Any]:
    # ... (lógica existente)
    ws_manager = get_websocket_manager()

    if step["tool"] == "web_search":
        query = step["description"] # O algún otro campo que contenga la consulta
        ws_manager.send_log_message(task_id, "info", f"Realizando búsqueda web para: {query}")
        
        # --- INTEGRACIÓN PLAYWRIGHT/SELENIUM --- 
        # Aquí se instanciaría y usaría el WebBrowserManager
        from src.web_browser_manager import WebBrowserManager # Asegúrate de que la ruta sea correcta
        browser_manager = WebBrowserManager(ws_manager, task_id)
        try:
            browser_manager.initialize_browser()
            browser_manager.navigate(f"https://www.google.com/search?q={query}")
            
            # Simular recolección de datos después de la navegación
            # En un escenario real, aquí harías el scraping de los resultados
            results = [{"title": "Resultado 1", "url": "https://ejemplo.com/1"}, {"title": "Resultado 2", "url": "https://ejemplo.com/2"}]
            ws_manager.send_data_collection_update(task_id, step["id"], f"Se encontraron {len(results)} resultados de búsqueda", results[:2]) # Enviar solo una muestra
            
            # Puedes añadir más interacciones y emitir eventos de actividad del navegador
            # browser_manager.click_element("selector_del_enlace")
            # browser_manager.type_text("selector_del_input", "texto")

            return {"success": True, "summary": "Búsqueda web completada", "content": json.dumps(results)}
        except Exception as e:
            ws_manager.send_log_message(task_id, "error", f"Error en la búsqueda web: {str(e)}")
            return {"success": False, "summary": f"Error en búsqueda web: {str(e)}", "content": ""}
        finally:
            browser_manager.close_browser()

    # ... (otros tipos de herramientas)

    elif step["tool"] == "creation":
        # Si la creación implica generar un informe, puedes enviar progreso
        ws_manager.send_log_message(task_id, "info", "Iniciando generación de informe...")
        ws_manager.send_report_progress(task_id, "Introducción", "Este es el inicio del informe.")
        # ... (lógica de generación de informe)
        ws_manager.send_report_progress(task_id, "Conclusiones", "Aquí las conclusiones.", "Contenido completo del informe hasta ahora...")
        return {"success": True, "summary": "Informe generado"}

    # ... (resto de la función)

```

**2. Asegurar que `websocket_manager` esté disponible:**

En `agent_routes.py`, asegúrate de que `current_app.websocket_manager` esté accesible. Esto ya debería estar configurado en `server.py`.

### 5.3. `frontend/src/components/TerminalView/TerminalView.tsx`

**1. Actualizar `MonitorPage` interface:**

```typescript
// ... (imports existentes)

export interface MonitorPage {
  id: string;
  title: string;
  content: string;
  type: 'plan' | 'tool-execution' | 'report' | 'file' | 'error' | 'web-browsing' | 'data-collection' | 'log'; // Añadir nuevos tipos
  timestamp: Date;
  toolName?: string;
  toolParams?: any;
  metadata?: {
    lineCount?: number;
    fileSize?: number;
    executionTime?: number;
    status?: 'success' | 'error' | 'running';
    // Nuevos campos para navegación web
    url?: string;
    screenshotUrl?: string; // URL accesible para la imagen
    // Nuevos campos para recolección de datos
    dataSummary?: string;
    partialData?: any;
    // Nuevos campos para logs
    logLevel?: 'info' | 'warn' | 'error';
  };
}

// ... (resto del archivo)
```

**2. Suscribirse a los nuevos eventos WebSocket:**

En el `useEffect` donde ya te suscribes a eventos WebSocket (probablemente en un componente padre o en `AppContext`), añade la lógica para los nuevos tipos de eventos.

```typescript
// En AppContext.tsx o un componente que maneje la conexión WebSocket

useEffect(() => {
  if (!socket || !currentTaskId) return;

  const handleTaskUpdate = (update: any) => {
    if (update.task_id !== currentTaskId) return; // Asegurarse de que sea para la tarea actual

    const updateType = update.type;
    const data = update.data;

    switch (updateType) {
      case 'browser_activity':
        addTaskMonitorPage(currentTaskId, {
          id: `browser-${Date.now()}`,
          title: `🌐 Navegando: ${data.title || data.url}`,
          content: `URL: ${data.url}`,
          type: 'web-browsing',
          timestamp: new Date(update.timestamp),
          metadata: {
            url: data.url,
            screenshotUrl: data.screenshot_url,
          },
        });
        break;
      case 'data_collection_update':
        addTaskMonitorPage(currentTaskId, {
          id: `data-${Date.now()}`,
          title: `📊 Datos Recolectados: ${data.data_summary}`,
          content: JSON.stringify(data.partial_data, null, 2),
          type: 'data-collection',
          timestamp: new Date(update.timestamp),
          metadata: {
            dataSummary: data.data_summary,
            partialData: data.partial_data,
          },
        });
        break;
      case 'report_progress':
        // Encontrar o crear la página del informe
        let reportPage = getTaskMonitorPages(currentTaskId).find(p => p.id === 'final-report');
        if (!reportPage) {
          reportPage = {
            id: 'final-report',
            title: '📄 Informe en Construcción',
            content: '',
            type: 'report',
            timestamp: new Date(),
            metadata: { status: 'running' },
          };
          addTaskMonitorPage(currentTaskId, reportPage); // Añadir si no existe
        }
        
        // Actualizar contenido del informe (concatenar o reemplazar)
        const newContent = reportPage.content + (data.content_delta || '');
        // O si `full_report_so_far` está disponible:
        // const newContent = data.full_report_so_far || reportPage.content;

        setTaskMonitorPages(currentTaskId, getTaskMonitorPages(currentTaskId).map(p => 
          p.id === 'final-report' ? { ...p, content: newContent, timestamp: new Date(update.timestamp) } : p
        ));
        break;
      case 'log_message':
        // Esto se puede añadir directamente a terminalOutput o a una nueva MonitorPage de tipo 'log'
        // Para mantenerlo simple y similar a tu `externalLogs` existente:
        setTerminalOutput(prev => [...prev, `[${data.level.toUpperCase()}] ${data.message}`]);
        // O si quieres una página de monitor para logs:
        addTaskMonitorPage(currentTaskId, {
          id: `log-${Date.now()}`,
          title: `Log: ${data.level.toUpperCase()}`,
          content: data.message,
          type: 'log',
          timestamp: new Date(update.timestamp),
          metadata: { logLevel: data.level },
        });
        break;
      // ... (otros casos existentes como step_started, step_completed)
    }
  };

  socket.on('task_update', handleTaskUpdate); // Asumiendo que todos los updates vienen bajo 'task_update'
  // O si emites eventos separados:
  // socket.on('browser_activity', handleBrowserActivity);
  // socket.on('data_collection_update', handleDataCollectionUpdate);
  // socket.on('report_progress', handleReportProgress);
  // socket.on('log_message', handleLogMessage);

  return () => {
    socket.off('task_update', handleTaskUpdate);
    // socket.off('browser_activity', handleBrowserActivity);
    // ...
  };
}, [socket, currentTaskId, addTaskMonitorPage, getTaskMonitorPages, setTaskMonitorPages]);

```

**3. Renderizar los nuevos tipos de `MonitorPage` en `TerminalView.tsx`:**

Modifica la sección de renderizado de `monitorPages` para manejar los nuevos tipos.

```typescript
// ... (dentro de TerminalView.tsx, en la sección de renderizado de la página actual)

const renderCurrentPageContent = () => {
  if (!currentPage) return null;

  switch (currentPage.type) {
    case 'plan':
      return (
        <div className="markdown-content">
          <h3>Plan de Ejecución</h3>
          <pre className="whitespace-pre-wrap text-sm">{currentPage.content}</pre>
        </div>
      );
    case 'tool-execution':
      return (
        <div className="markdown-content">
          <h3>Detalles de Ejecución de Herramienta: {currentPage.toolName}</h3>
          <p>{currentPage.content}</p>
          {currentPage.metadata?.status === 'error' && (
            <div className="text-red-500">Error: {currentPage.metadata.status}</div>
          )}
          {currentPage.toolParams && (
            <pre className="bg-gray-700 p-2 rounded text-xs">{JSON.stringify(currentPage.toolParams, null, 2)}</pre>
          )}
        </div>
      );
    case 'report':
      return (
        <div className="markdown-content">
          <AcademicMarkdownRenderer markdown={currentPage.content} />
        </div>
      );
    case 'file':
      return (
        <div className="markdown-content">
          <h3>Contenido del Archivo: {currentPage.title}</h3>
          <pre className="whitespace-pre-wrap text-sm">{currentPage.content}</pre>
        </div>
      );
    case 'error':
      return (
        <div className="markdown-content text-red-500">
          <h3>Error: {currentPage.title}</h3>
          <pre className="whitespace-pre-wrap text-sm">{currentPage.content}</pre>
        </div>
      );
    case 'web-browsing':
      return (
        <div className="markdown-content">
          <h3>🌐 Navegación Web: {currentPage.title}</h3>
          <p>URL: <a href={currentPage.metadata?.url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">{currentPage.metadata?.url}</a></p>
          {currentPage.metadata?.screenshotUrl && (
            <img src={currentPage.metadata.screenshotUrl} alt="Captura de pantalla de la navegación" className="mt-2 rounded-lg max-w-full h-auto" />
          )}
          <p className="text-sm mt-2">{currentPage.content}</p>
        </div>
      );
    case 'data-collection':
      return (
        <div className="markdown-content">
          <h3>📊 Datos Recolectados: {currentPage.title}</h3>
          <p>{currentPage.metadata?.dataSummary}</p>
          {currentPage.metadata?.partialData && (
            <pre className="bg-gray-700 p-2 rounded text-xs">{JSON.stringify(currentPage.metadata.partialData, null, 2)}</pre>
          )}
          <p className="text-sm mt-2">{currentPage.content}</p>
        </div>
      );
    case 'log':
      return (
        <div className="markdown-content">
          <h3 className={currentPage.metadata?.logLevel === 'error' ? 'text-red-500' : currentPage.metadata?.logLevel === 'warn' ? 'text-yellow-500' : ''}>Log: {currentPage.title}</h3>
          <pre className="whitespace-pre-wrap text-sm">{currentPage.content}</pre>
        </div>
      );
    default:
      return (
        <div className="markdown-content">
          <h3>Contenido Desconocido</h3>
          <pre className="whitespace-pre-wrap text-sm">{currentPage.content}</pre>
        </div>
      );
  }
};

// ... (resto del archivo)
```

**4. Actualizar la sección de logs del terminal:**

Para mostrar los `LOG_MESSAGE` en el `terminalOutput`:

```typescript
// ... (dentro de TerminalView.tsx, en la sección de renderizado del terminal)

<div className="flex-1 overflow-y-auto p-2 text-xs font-mono bg-gray-800 text-gray-200 rounded-b-lg">
  {terminalOutput.map((line, index) => (
    <div key={index} className="py-0.5">{line}</div>
  ))}
  {externalLogs.map((log, index) => (
    <div key={`ext-${index}`} className={`py-0.5 ${log.type === 'error' ? 'text-red-400' : log.type === 'success' ? 'text-green-400' : 'text-gray-300'}`}>
      <span className="text-gray-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span> {log.message}
    </div>
  ))}
  {/* ... (otros elementos de UI) */}
</div>
```

### 5.4. Consideraciones Adicionales

*   **Instalación de Playwright/Selenium:** Asegúrate de que las dependencias de Playwright (`pip install playwright` y `playwright install`) o Selenium (`pip install selenium` y el WebDriver correspondiente) estén instaladas en tu entorno de backend.
*   **Manejo de `executionData`:** El `executionData` que ya se pasa al `TerminalView` desde `get_task_status` en `agent_routes.py` es útil para el estado general y los `executed_tools`. Sin embargo, para la visualización en tiempo real, la estrategia de eventos WebSocket es más adecuada.
*   **Optimización de WebSocket:** Asegúrate de que los payloads de WebSocket no sean excesivamente grandes, especialmente para las capturas de pantalla o datos masivos. Considera enviar URLs a recursos grandes en lugar de los datos directamente. Para las capturas de pantalla, guardarlas en el servidor y servir su URL es la mejor práctica.
*   **Manejo de Errores:** Implementa un manejo robusto de errores tanto en el backend (para la captura y emisión de eventos) como en el frontend (para el consumo y renderizado).
*   **Pruebas:** Realiza pruebas exhaustivas de cada nueva funcionalidad para asegurar que los eventos se emiten y consumen correctamente, y que la UI se actualiza como se espera.

Este informe proporciona un camino claro para implementar las funcionalidades de visualización en tiempo real que deseas, incorporando la integración de Playwright/Selenium para la navegación web, manteniendo la separación entre el backend y el frontend y sin requerir cambios drásticos en la UI existente, sino extendiendo sus capacidades.

