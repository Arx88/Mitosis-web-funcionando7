# Índice Funcional - Mitosis

## 🎯 REGLA CRÍTICA
**ANTES DE CREAR CUALQUIER NUEVA FUNCIÓN**: Buscar en este índice si ya existe funcionalidad similar para evitar duplicaciones.

---

## 📱 FRONTEND - React + TypeScript

### Componente Principal
**App.tsx** (`/app/frontend/src/App.tsx`)
- `App()` - Componente raíz principal
- `generateDynamicIdeas()` - Genera sugerencias dinámicas desde backend
- Estado: `dynamicIdeas`, `isConfigModalOpen`, `isInitialLoading`
- Maneja: routing, configuración, tareas, archivos, WebSocket

### Componentes UI (32+ componentes)
**Ubicación**: `/app/frontend/src/components/`

#### Componentes Core
- `Sidebar.tsx` - Navegación lateral, lista de tareas
- `TaskView.tsx` - Vista principal de tareas y ejecución  
- `VanishInput.tsx` - Input principal con animaciones
- `ConfigPanel.tsx` - Panel de configuración del agente
- `TerminalView.tsx` - Terminal en tiempo real para logs

#### Componentes de Visualización
- `TaskSummary.tsx` - Resumen de tareas completadas
- `SearchResults.tsx` - Resultados de búsquedas web
- `DeepResearchReport.tsx` - Reportes de investigación
- `DeepResearchResult.tsx` - Resultados individuales
- `ErrorAnalysisPanel.tsx` - Panel de análisis de errores
- `EnhancedMonitoringDashboard.tsx` - Dashboard de monitoreo

#### Componentes de Sistema
- `LoadingPlaceholder.tsx` - Placeholders para carga
- `Loader.tsx` - Componente de carga genérico
- `ErrorBoundary.tsx` - Manejo global de errores
- `LazyComponents.tsx` - Componentes con lazy loading
- `MovingBorder.tsx` - Efectos visuales animados

#### Componentes de Archivos
- `FileUploadModal.tsx` - Modal para subir archivos
- `FilesModal.tsx` - Modal para gestión de archivos
- `FileInlineDisplay.tsx` - Visualización inline de archivos
- `ShareModal.tsx` - Modal para compartir contenido

#### Componentes Especializados
- `TaskIcon.tsx` - Iconos dinámicos para tareas
- `EnvironmentSetupLoader.tsx` - Cargador de entorno
- `BrowserVisualFeedback.tsx` - Feedback visual de navegador

### Gestión de Estado
**AppContext.tsx** (`/app/frontend/src/context/AppContext.tsx`)
- Context API principal con useReducer
- Estados: tasks, activeTaskId, UI state, config
- Acciones: CREATE_TASK, UPDATE_TASK, SET_ACTIVE_TASK, etc.

### Custom Hooks
**Ubicación**: `/app/frontend/src/hooks/`
- `useTaskManagement.ts` - Gestión completa de tareas
- `useWebSocket.ts` - Comunicación WebSocket real-time
- `useMemoryManager.ts` - Sistema de memoria
- `useUIState.ts` - Estado de interfaz
- `useConfigManagement.ts` - Configuración del agente
- `useFileManagement.ts` - Gestión de archivos

### Servicios Frontend
**Ubicación**: `/app/frontend/src/services/`
- API client para comunicación con backend
- WebSocket client para tiempo real
- File upload service
- Configuration service

### Configuración
**api.ts** (`/app/frontend/src/config/api.ts`)
- URLs centralizadas del backend
- Configuración de endpoints
- Variables de entorno

---

## 🖥️ BACKEND - Flask + Python

### Servidor Principal
**server.py** (`/app/backend/server.py`)
- `Flask app` - Servidor principal con SocketIO
- `get_dynamic_cors_origins()` - CORS dinámico para múltiples entornos
- `health_check()` - Health check completo
- `initialize_ollama_queue()` - Sistema de cola Ollama
- WebSocket handlers: connect, disconnect, join_task, leave_task
- Función global: `emit_task_event()`, `emit_browser_visual_safe()`

### Rutas del Agente
**agent_routes.py** (`/app/backend/src/routes/agent_routes.py`)

#### Endpoints Principales
- `POST /api/agent/chat` - Chat principal con el agente
- `POST /api/agent/generate-plan` - Generación de planes
- `POST /api/agent/start-task-execution/<task_id>` - Ejecutar tarea
- `GET /api/agent/get-all-tasks` - Obtener todas las tareas
- `GET /api/agent/status` - Estado del agente
- `GET /api/agent/get-task-status/<task_id>` - Estado de tarea específica

#### Configuración y Gestión
- `GET /api/agent/config/current` - Configuración actual
- `POST /api/agent/config/apply` - Aplicar configuración
- `POST /api/agent/ollama/models` - Modelos Ollama disponibles
- `POST /api/agent/ollama/check` - Verificar conexión Ollama
- `GET /api/agent/model-info` - Información modelo actual

#### Utilidades
- `POST /api/agent/cleanup-completed-tasks` - Limpiar tareas antiguas
- `POST /api/agent/force-stop-task/<task_id>` - Detener tarea forzadamente
- `POST /api/agent/generate-final-report/<task_id>` - Generar informe final

### Servicios Core

#### OllamaService
**ollama_service.py** (`/app/backend/src/services/ollama_service.py`)
- `generate_completion()` - Generar completions con Ollama
- `is_healthy()` - Verificar salud del servicio
- `get_available_models()` - Modelos disponibles
- `set_model()` - Cambiar modelo activo
- `update_endpoint()` - Actualizar endpoint

#### TaskManager  
**task_manager.py** (`/app/backend/task_manager.py`)
- `create_task()` - Crear nueva tarea
- `get_task()` - Obtener tarea por ID
- `update_task()` - Actualizar tarea
- `execute_task()` - Ejecutar plan de tarea
- `get_all_tasks()` - Obtener todas las tareas
- `cleanup_completed_tasks()` - Limpiar tareas completadas

#### MemoryManager
**memory_manager.py** (`/app/backend/memory_manager.py`)
- `store_memory()` - Almacenar en memoria
- `retrieve_memory()` - Recuperar de memoria  
- `get_context()` - Obtener contexto actual
- `update_context()` - Actualizar contexto

### Sistema de Herramientas (12+ Tools)
**Ubicación**: `/app/backend/src/tools/`

#### Herramientas Base
- `base_tool.py` - **BaseTool** clase abstracta para todas las herramientas
- `tool_manager.py` - **ToolManager** para gestión y registro
- `tool_registry.py` - Auto-discovery y lazy loading

#### Herramientas Disponibles
1. **shell_tool.py** - Ejecución de comandos shell
   - `execute_shell_command()` - Ejecutar comando
   - `get_system_info()` - Información del sistema

2. **unified_web_search_tool.py** - Búsqueda web unificada
   - `search_web()` - Búsqueda con múltiples proveedores
   - `deep_search()` - Búsqueda profunda

3. **file_manager_tool.py** - Gestión de archivos
   - `create_file()` - Crear archivo
   - `read_file()` - Leer archivo
   - `delete_file()` - Eliminar archivo
   - `list_directory()` - Listar directorio

4. **real_time_browser_tool.py** - Navegación web en tiempo real *(MEJORADO 2025-01-26)*
   - `navigate_to_url()` - Navegar a URL
   - `take_screenshot()` - Capturar pantalla
   - `extract_data()` - Extraer datos de página
   - `_extract_search_terms()` - *(MEJORADO)* Extracción inteligente de términos de búsqueda
   - `_perform_search_task()` - *(REFACTORIZADO)* Búsqueda robusta con múltiples estrategias  
   - `_explore_search_results()` - *(NUEVO)* Exploración inteligente de resultados
   - `_perform_link_based_search()` - *(NUEVO)* Búsqueda basada en enlaces relevantes
   - `_clean_search_terms()` - *(NUEVO)* Limpieza de términos extraídos

5. **playwright_tool.py** - Automatización web avanzada
   - `launch_browser()` - Lanzar navegador
   - `perform_action()` - Ejecutar acciones
   - `wait_for_element()` - Esperar elementos

6. **ollama_processing_tool.py** - Procesamiento con IA
   - `process_text()` - Procesar texto
   - `analyze_content()` - Analizar contenido

7. **ollama_analysis_tool.py** - Análisis avanzado con IA
   - `analyze_data()` - Analizar datos
   - `generate_insights()` - Generar insights

8. **execution_engine.py** - Motor de ejecución
   - `execute_plan()` - Ejecutar plan completo
   - `execute_step()` - Ejecutar paso individual

9. **visual_browser_events.py** - Eventos visuales de navegador
   - `emit_browser_event()` - Emitir evento visual
   - `capture_browser_state()` - Capturar estado

### WebSocket Manager
**websocket_manager.py** (`/app/backend/src/websocket/websocket_manager.py`)
- `WebSocketManager` clase principal
- `send_task_update()` - Enviar actualización de tarea
- `send_log_message()` - Enviar mensaje de log
- `join_task_room()` - Unirse a room de tarea
- `cleanup_task_connections()` - Limpiar conexiones

### Configuración
**ollama_config.py** (`/app/backend/src/config/ollama_config.py`)
- `get_ollama_config()` - Configuración Ollama
- `get_ollama_endpoint()` - Endpoint Ollama
- `get_ollama_model()` - Modelo por defecto

---

## 🗄️ BASE DE DATOS - MongoDB

### Colecciones Principales
**Database**: `mitosis`

#### tasks
- `task_id` (string) - ID único de tarea
- `title` (string) - Título de la tarea  
- `status` (string) - Estado: pending, running, completed, failed
- `plan` (array) - Plan de ejecución con pasos
- `progress` (number) - Progreso 0-100
- `created_at` (datetime) - Fecha de creación
- `updated_at` (datetime) - Última actualización
- `result` (object) - Resultado de ejecución

#### files
- `id` (string) - ID único del archivo
- `task_id` (string) - ID de tarea asociada
- `name` (string) - Nombre del archivo
- `content` (string) - Contenido del archivo
- `type` (string) - Tipo MIME
- `size` (number) - Tamaño en bytes
- `source` (string) - Origen: user, agent, tool
- `created_at` (datetime) - Fecha de creación

#### memory
- `id` (string) - ID único
- `task_id` (string) - Tarea asociada (opcional)
- `type` (string) - Tipo: short_term, long_term, context
- `content` (object) - Contenido de memoria
- `created_at` (datetime) - Fecha de creación
- `expires_at` (datetime) - Fecha de expiración (opcional)

---

## 🌐 API ENDPOINTS COMPLETOS

### Agente Principal (`/api/agent/`)
- `GET /health` - Health check
- `POST /chat` - Chat con el agente
- `POST /generate-plan` - Generar plan
- `POST /start-task-execution/<id>` - Ejecutar tarea
- `GET /get-all-tasks` - Todas las tareas
- `GET /status` - Estado completo
- `GET /get-task-status/<id>` - Estado de tarea

### Configuración (`/api/agent/config/`)
- `GET /current` - Configuración actual
- `POST /apply` - Aplicar configuración

### Ollama (`/api/agent/ollama/`)
- `POST /models` - Modelos disponibles
- `POST /check` - Verificar conexión
- `GET /model-info` - Información del modelo

### Herramientas (`/api/tools/`)
- `GET /available` - Herramientas disponibles
- `POST /{tool_name}` - Ejecutar herramienta

### Archivos (`/api/files/`)
- `GET /screenshots/<task_id>/<filename>` - Servir capturas
- `POST /upload` - Subir archivo
- `GET /<task_id>` - Archivos de tarea

### Gestión (`/api/agent/`)
- `POST /cleanup-completed-tasks` - Limpiar tareas
- `POST /force-stop-task/<id>` - Detener tarea
- `POST /generate-final-report/<id>` - Informe final
- `POST /generate-suggestions` - Sugerencias dinámicas

---

## 🔗 WEBSOCKET EVENTS

### Cliente → Servidor
- `connect` - Conectar cliente
- `join_task` - Unirse a tarea
- `leave_task` - Salir de tarea
- `disconnect` - Desconectar

### Servidor → Cliente  
- `connection_status` - Estado de conexión
- `joined_task` - Confirmación de unión
- `task_progress` - Progreso de tarea
- `step_completed` - Paso completado
- `tool_execution` - Ejecución de herramienta
- `task_completed` - Tarea terminada
- `browser_visual` - Evento visual de navegador
- `log_message` - Mensaje de log
- `error` - Error del sistema

---

## 🛠️ PATRONES DE DESARROLLO

### Patrón Tool
```python
class NewTool(BaseTool):
    name = "tool_name"
    description = "Tool description"
    
    async def execute(self, **kwargs):
        # Implementation
        return result
```

### Patrón Hook React
```typescript
export function useNewFeature() {
    const [state, setState] = useState();
    
    const action = useCallback(() => {
        // Implementation
    }, []);
    
    return { state, action };
}
```

### Patrón API Endpoint
```python
@agent_bp.route('/new-endpoint', methods=['POST'])
def new_endpoint():
    try:
        data = request.get_json()
        result = process_data(data)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

---

## ⚠️ FUNCIONES CRÍTICAS - NO DUPLICAR

### Gestión de Tareas
- ✅ **Creación**: `createTask()`, `createTaskWithMessage()` (frontend) + `create_task()` (backend)
- ✅ **Ejecución**: `execute_task()` (TaskManager)
- ✅ **WebSocket**: `emit_task_event()`, `send_task_update()`

### Comunicación IA
- ✅ **Ollama**: `generate_completion()` (OllamaService)
- ✅ **Planificación**: `generate_plan()` (agent_routes.py)

### Navegación Web
- ✅ **Real-time**: `real_time_browser_tool.py`
- ✅ **Playwright**: `playwright_tool.py`
- ✅ **Búsqueda**: `unified_web_search_tool.py`

### Gestión de Estado
- ✅ **Global**: Context API (AppContext.tsx)
- ✅ **WebSocket**: useWebSocket hook
- ✅ **UI**: useUIState hook

---

## 📝 NOTAS PARA FUTURAS MEJORAS

### AL AGREGAR NUEVA FUNCIONALIDAD
1. Verificar este índice para evitar duplicación
2. Seguir patrones existentes
3. Actualizar este documento
4. Mantener consistencia con arquitectura actual

### UBICACIONES RECOMENDADAS
- **Nuevas herramientas**: `/app/backend/src/tools/`
- **Nuevos componentes**: `/app/frontend/src/components/`
- **Nuevos hooks**: `/app/frontend/src/hooks/`
- **Nuevos endpoints**: Agregar a `agent_routes.py`
- **Nuevos servicios**: `/app/backend/src/services/`