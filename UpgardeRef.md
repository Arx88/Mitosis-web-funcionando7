
# Informe de Análisis del Agente General

## 1. Arquitectura General del Sistema

El sistema del agente general está compuesto por dos componentes principales: un **Backend** desarrollado con Flask y un **Frontend** desarrollado con React. La comunicación entre estos dos componentes se realiza a través de APIs REST y WebSockets para actualizaciones en tiempo real. La persistencia de datos se gestiona mediante una base de datos MongoDB.

### 1.1. Componentes del Backend

El backend, implementado en Python con el framework Flask, es el cerebro del agente. Sus componentes clave incluyen:

*   **`server.py`**: Este es el archivo principal del servidor Flask. Se encarga de:
    *   Inicializar la aplicación Flask y configurar CORS para permitir la comunicación con el frontend.
    *   Configurar el logging para el sistema y la terminal.
    *   Establecer la conexión con MongoDB (`pymongo`).
    *   Inicializar el `WebSocketManager` para manejar las comunicaciones en tiempo real.
    *   Inicializar el `OllamaService` para interactuar con modelos de lenguaje.
    *   Inicializar el `ToolManager` para gestionar las herramientas disponibles para el agente.
    *   Registrar los `Blueprints` de las rutas del agente (definidas en `agent_routes.py`).
    *   Proveer endpoints para la configuración dinámica del agente y checks de salud (`/health`).

*   **`src/routes/agent_routes.py`**: Este módulo define las rutas API específicas para la lógica del agente. Incluye endpoints para:
    *   `health`: Un endpoint de salud que verifica la conexión a MongoDB, el estado de Ollama y el `TaskManager`.
    *   `execute-step-detailed/<task_id>/<step_id>`: Permite la ejecución controlada y secuencial de un paso específico de un plan de tarea. Este endpoint es crítico para la orquestación de las tareas.
    *   `get-task-status/<task_id>`: Proporciona el estado actual de una tarea, incluyendo el plan de ejecución y las herramientas ejecutadas. Es utilizado por el frontend para el polling.
    *   `get-task-plan/<task_id>`: Retorna el plan de ejecución de una tarea específica.
    *   Contiene la lógica para la generación de planes de acción utilizando Ollama y la validación de estos planes contra un `PLAN_SCHEMA`.
    *   Emite eventos de WebSocket (`emit_step_event`) para notificar al frontend sobre el progreso de los pasos y la tarea.

*   **`src/websocket/websocket_manager.py`**: Gestiona las conexiones WebSocket y las actualizaciones en tiempo real. Sus funciones principales son:
    *   Inicializar `SocketIO` con la aplicación Flask.
    *   Manejar eventos de conexión (`connect`), desconexión (`disconnect`), unión a tareas (`join_task`) y salida de tareas (`leave_task`).
    *   Mantener un registro de las conexiones activas por `task_id` y `session_id`.
    *   Proveer el método `send_update` para enviar actualizaciones a todos los clientes suscritos a una tarea específica.
    *   **Punto clave para la persistencia del chat y la terminal**: Este módulo almacena los últimos 10 eventos por tarea (`stored_events`) para clientes que se unen tarde, lo que sugiere un intento de persistencia a corto plazo para la UI.

*   **`src/services/task_manager.py`**: Este módulo es fundamental para la persistencia del estado de las tareas. Se encarga de:
    *   Interactuar con la base de datos MongoDB a través de `DatabaseService`.
    *   `create_task`: Crea y persiste una nueva tarea en MongoDB.
    *   `get_task`: Recupera una tarea por su ID, utilizando un caché en memoria (`active_cache`) para reducir la latencia.
    *   `update_task`: Actualiza los datos de una tarea en MongoDB y en el caché.
    *   `update_task_step_status`: Actualiza el estado de un paso específico dentro de una tarea.
    *   `get_all_tasks`, `get_incomplete_tasks`, `delete_task`, `get_task_history`, `cleanup_old_tasks`, `recover_incomplete_tasks_on_startup`: Funciones para la gestión completa del ciclo de vida de las tareas.
    *   Implementa un patrón Singleton (`get_task_manager`) para asegurar una única instancia del gestor de tareas.

*   **`src/services/database.py`**: (Asumo su existencia y funcionalidad basándome en `task_manager.py`) Este módulo abstrae la interacción con MongoDB, proporcionando métodos para guardar, obtener, actualizar y eliminar documentos de tareas.

*   **`src/context/intelligent_context_manager.py`**: Gestiona la construcción de contexto optimizado para el modelo de lenguaje. Utiliza diferentes estrategias (`ChatContextStrategy`, `TaskPlanningContextStrategy`, etc.) para adaptar el contexto según el tipo de interacción. También implementa un caché de contexto.

*   **`src/services/ollama_service.py`**: Proporciona una interfaz para interactuar con el servicio Ollama, permitiendo la generación de texto y la gestión de modelos.

*   **`src/tools/tool_manager.py`**: Gestiona la disponibilidad y ejecución de las herramientas que el agente puede utilizar (e.g., `web_search`, `shell`, `analysis`).

### 1.2. Componentes del Frontend

El frontend, desarrollado con React, es la interfaz de usuario que interactúa con el backend. Los archivos clave que se relacionan con la gestión de tareas, chat y persistencia son:

*   **`frontend/src/App.tsx`**: El componente raíz de la aplicación React, que probablemente orquesta la visualización de las diferentes secciones (barra lateral, chat, terminal, plan de acción).

*   **`frontend/src/context/AppContext.tsx`**: Es probable que este archivo defina el contexto global de React, donde se almacenan estados compartidos como la tarea activa, el historial del chat, el plan de acción, etc. Este es un punto crítico para entender cómo se maneja el estado a nivel de la UI.

*   **`frontend/src/hooks/useTaskManagement.ts`**: Un hook personalizado que encapsula la lógica para interactuar con el `TaskManager` del backend, incluyendo la creación, actualización y recuperación de tareas. Es probable que maneje la lógica de cambio de tareas y la carga de su estado.

*   **`frontend/src/hooks/usePlanManager.ts`**: Probablemente gestiona el estado y las interacciones relacionadas con el plan de acción de la tarea actual.

*   **`frontend/src/hooks/useWebSocket.ts`**: Este hook se encarga de establecer y mantener la conexión WebSocket con el backend, así como de procesar los eventos recibidos en tiempo real. Es crucial para las actualizaciones del chat y la terminal.

*   **`frontend/src/components/ChatInterface`**: Componentes relacionados con la visualización y gestión del chat.

*   **`frontend/src/components/TerminalView`**: Componentes relacionados con la visualización de la terminal y la salida de comandos.

*   **`frontend/src/components/TaskView.tsx`**: Este componente es central, ya que agrupa la visualización del chat, el plan de acción y la terminal. Es donde se manifiestan los problemas de aislamiento.

### 1.3. Comunicación entre Backend y Frontend

La comunicación se establece principalmente a través de:

*   **APIs REST**: Para operaciones como la creación de tareas, la obtención del estado inicial de una tarea, la aplicación de configuraciones, etc. (ej. `/api/agent/create-task`, `/api/agent/get-task-status`).
*   **WebSockets (Socket.IO)**: Para actualizaciones en tiempo real. El backend emite eventos (`task_update`, `step_started`, `step_completed`, etc.) que el frontend escucha para actualizar dinámicamente la UI (chat, progreso del plan, salida de la terminal). El `WebSocketManager` en el backend y `useWebSocket.ts` en el frontend son los encargados de esta comunicación.

### 1.4. Estructura de Datos para Tareas y su Estado

El estado de una tarea se persiste en MongoDB y se gestiona a través del `TaskManager`. Una tarea (`task_document`) típicamente incluye los siguientes campos:

*   `task_id`: Identificador único de la tarea.
*   `status`: Estado actual de la tarea (e.g., `created`, `pending`, `executing`, `completed`, `failed`).
*   `plan`: Una lista de pasos (`steps`) que componen el plan de acción. Cada paso tiene su propio `id`, `title`, `description`, `tool`, `status` (e.g., `in-progress`, `completed`), `result`, `start_time`, `completed_time`, etc.
*   `current_step`: Índice o ID del paso actual en ejecución.
*   `message`: El mensaje inicial o la descripción de la tarea.
*   `task_type`, `complexity`, `ai_generated`, `plan_source`.
*   `created_at`, `updated_at`, `start_time`, `completed_at`.
*   `final_result`, `error`, `fallback_reason`, `warning`.
*   `metadata`: Un diccionario para almacenar información adicional.

El `TaskManager` utiliza un caché en memoria (`active_cache`) para las tareas accedidas recientemente, lo que es una optimización de rendimiento. Sin embargo, la fuente de verdad principal es MongoDB.

En el frontend, el estado de la tarea activa, el historial del chat y la salida de la terminal se gestionan a través del contexto de React (probablemente `AppContext.tsx`) y varios hooks (`useTaskManagement.ts`, `usePlanManager.ts`, `useWebSocket.ts`). La clave aquí es cómo este estado se carga y se descarga al cambiar de tarea, y cómo se asegura que los datos sean específicos de cada `task_id`.



### 1.2. Componentes del Frontend

El frontend, desarrollado con React, es la interfaz de usuario que interactúa con el backend. Los archivos clave que se relacionan con la gestión de tareas, chat y persistencia son:

*   **`frontend/src/App.tsx`**: El componente raíz de la aplicación React, que probablemente orquesta la visualización de las diferentes secciones (barra lateral, chat, terminal, plan de acción).

*   **`frontend/src/context/AppContext.tsx`**: Este archivo define el contexto global de React, donde se almacenan estados compartidos como la tarea activa, el historial del chat, el plan de acción, etc. **Es un punto crítico para entender cómo se maneja el estado a nivel de la UI.** Se observa que ya se han implementado estructuras `Record<string, ...>` para aislar el estado por `taskId` para `taskFiles`, `terminalLogs`, `taskMessages`, `taskPlanStates`, `taskTerminalCommands`, `taskWebSocketStates`, `taskMonitorPages`, y `taskCurrentPageIndex`. Esto indica un esfuerzo por lograr el aislamiento a nivel del frontend.

*   **`frontend/src/hooks/useTaskManagement.ts`**: Un hook personalizado que encapsula la lógica para interactuar con el `TaskManager` del backend, incluyendo la creación, actualización y recuperación de tareas. Maneja la lógica de cambio de tareas y la carga de su estado. Se observa que utiliza IDs temporales para las tareas y luego las migra a IDs reales del backend, lo cual es fundamental para la persistencia.

*   **`frontend/src/hooks/usePlanManager.ts`**: Probablemente gestiona el estado y las interacciones relacionadas con el plan de acción de la tarea actual.

*   **`frontend/src/hooks/useWebSocket.ts`**: Este hook se encarga de establecer y mantener la conexión WebSocket con el backend, así como de procesar los eventos recibidos en tiempo real. Es crucial para las actualizaciones del chat y la terminal.

*   **`frontend/src/components/ChatInterface`**: Componentes relacionados con la visualización y gestión del chat.

*   **`frontend/src/components/TerminalView`**: Componentes relacionados con la visualización de la terminal y la salida de comandos.

*   **`frontend/src/components/TaskView.tsx`**: Este componente es central, ya que agrupa la visualización del chat, el plan de acción y la terminal. Es donde se manifiestan los problemas de aislamiento.

### 1.3. Comunicación entre Backend y Frontend

La comunicación se establece principalmente a través de:

*   **APIs REST**: Para operaciones como la creación de tareas, la obtención del estado inicial de una tarea, la aplicación de configuraciones, etc. (ej. `/api/agent/create-task`, `/api/agent/get-task-status`).
*   **WebSockets (Socket.IO)**: Para actualizaciones en tiempo real. El backend emite eventos (`task_update`, `step_started`, `step_completed`, etc.) que el frontend escucha para actualizar dinámicamente la UI (chat, progreso del plan, salida de la terminal). El `WebSocketManager` en el backend y `useWebSocket.ts` en el frontend son los encargados de esta comunicación.

### 1.4. Estructura de Datos para Tareas y su Estado

El estado de una tarea se persiste en MongoDB y se gestiona a través del `TaskManager`. Una tarea (`task_document`) típicamente incluye los siguientes campos:

*   `task_id`: Identificador único de la tarea.
*   `status`: Estado actual de la tarea (e.g., `created`, `pending`, `executing`, `completed`, `failed`).
*   `plan`: Una lista de pasos (`steps`) que componen el plan de acción. Cada paso tiene su propio `id`, `title`, `description`, `tool`, `status` (e.g., `in-progress`, `completed`), `result`, `start_time`, `completed_time`, etc.
*   `current_step`: Índice o ID del paso actual en ejecución.
*   `message`: El mensaje inicial o la descripción de la tarea.
*   `task_type`, `complexity`, `ai_generated`, `plan_source`.
*   `created_at`, `updated_at`, `start_time`, `completed_at`.
*   `final_result`, `error`, `fallback_reason`, `warning`.
*   `metadata`: Un diccionario para almacenar información adicional.

El `TaskManager` utiliza un caché en memoria (`active_cache`) para las tareas accedidas recientemente, lo que es una optimización de rendimiento. Sin embargo, la fuente de verdad principal es MongoDB.

En el frontend, el estado de la tarea activa, el historial del chat y la salida de la terminal se gestionan a través del contexto de React (probablemente `AppContext.tsx`) y varios hooks (`useTaskManagement.ts`, `usePlanManager.ts`, `useWebSocket.ts`). La clave aquí es cómo este estado se carga y se descarga al cambiar de tarea, y cómo se asegura que los datos sean específicos de cada `task_id`.



## 2. Identificación de Problemas de Persistencia y Aislamiento

El problema central radica en la falta de coherencia y aislamiento del estado entre las diferentes tareas, manifestándose en la UI (chat, plan de acción, terminal) y en la persistencia de datos. Aunque se han implementado mecanismos para el aislamiento, existen fallas que provocan la mezcla y duplicación de información.

### 2.1. Problemas de Aislamiento en el Frontend

El frontend, a través de `AppContext.tsx`, ya implementa estructuras `Record<string, ...>` para almacenar el estado de elementos como `taskFiles`, `terminalLogs`, `taskMessages`, y `taskPlanStates` por `taskId`. Esto es un paso correcto hacia el aislamiento. Sin embargo, los problemas reportados sugieren que la *utilización* o *sincronización* de estos estados aislados no es perfecta.

**Síntomas reportados:**

*   **El plan de acción no persiste correctamente y se muestra duplicado en todas las tareas.**
*   **El chat también se duplica.**
*   **La terminal no muestra los resultados correspondientes a ninguna tarea.**

**Posibles causas y ejemplos de código (Frontend):**

1.  **Falta de carga/descarga explícita del estado al cambiar de tarea:** Aunque `AppContext.tsx` almacena el estado por `taskId`, los componentes que consumen este contexto (ej. `TaskView.tsx`, `ChatInterface`, `TerminalView`) podrían no estar actualizando su visualización de forma reactiva al cambio de `activeTaskId`. Si un componente no se suscribe correctamente al `activeTaskId` y al estado asociado a ese ID, podría seguir mostrando datos de la tarea anterior o datos globales no aislados.

    *   **Ejemplo (hipotético):** Si `TaskView.tsx` o sus subcomponentes leen directamente de un estado global no indexado por `taskId` o no reaccionan a los cambios de `activeTaskId`:

    ```typescript
    // frontend/src/components/TaskView.tsx (ejemplo simplificado)
    // PROBLEMA: Si `messages` no se obtiene del `taskMessages[activeTaskId]`
    // y en su lugar se usa una variable global o un estado local no reseteado.
    const { activeTaskId, messages } = useAppContext(); // `messages` aquí podría ser global
    // ... renderiza `messages`
    ```

2.  **Manejo incorrecto de eventos WebSocket en el frontend:** El `useWebSocket.ts` recibe actualizaciones del backend. Si estas actualizaciones no se dirigen correctamente al `taskId` activo o si se aplican a un estado global en lugar del estado aislado por tarea, se produciría la duplicación. El `websocket_manager.py` del backend ya emite eventos con `task_id` (`self.socketio.emit(event, enhanced_data, room=task_id)`), lo que sugiere que el problema podría estar en cómo el frontend consume estos eventos.

    *   **Ejemplo (frontend/src/hooks/useWebSocket.ts):**

    ```typescript
    // frontend/src/hooks/useWebSocket.ts (ejemplo simplificado)
    socket.on("task_update", (data) => {
      const { task_id, type, data: updateData } = data;
      // PROBLEMA: Si `dispatch` no usa `task_id` para actualizar el estado aislado
      // o si se actualiza un estado global en lugar de `taskMessages[task_id]`
      if (type === "new_message") {
        dispatch({ type: "ADD_MESSAGE_TO_GLOBAL_CHAT", payload: updateData.message }); // Incorrecto
        // Debería ser:
        // dispatch({ type: "ADD_TASK_MESSAGE", payload: { taskId: task_id, message: updateData.message } });
      }
    });
    ```

3.  **Inicialización o reseteo incompleto del estado al crear una nueva tarea:** Aunque `ADD_TASK` en `AppContext.tsx` inicializa los `Record` con objetos vacíos para la nueva tarea, es crucial que todos los componentes de la UI que muestran datos de la tarea se reinicien o se re-rendericen correctamente cuando se selecciona una nueva tarea o se crea una. Si hay estados locales en los componentes que no se limpian, podrían persistir datos visuales de la tarea anterior.

    *   **Ejemplo (frontend/src/context/AppContext.tsx - `ADD_TASK` reducer):**

    ```typescript
    // Ya se inicializa correctamente:
    // taskMessages: { ...state.taskMessages, [newTask.id]: newTask.messages || [] },
    // terminalLogs: { ...state.terminalLogs, [newTask.id]: [] },
    // taskPlanStates: { ...state.taskPlanStates, [newTask.id]: { plan: newTask.plan || [], ... } },
    ```
    El problema no parece estar en la inicialización en el reducer, sino en cómo los componentes reaccionan a `activeTaskId`.

### 2.2. Problemas de Persistencia en el Backend

El backend utiliza MongoDB y el `TaskManager` para la persistencia de tareas, lo cual es una buena práctica. El `TaskManager` ya maneja la creación, obtención y actualización de tareas, incluyendo sus planes y pasos. El `websocket_manager.py` también intenta almacenar los últimos eventos (`stored_events`) para clientes que se unen tarde.

**Síntomas reportados:**

*   **El plan de acción no persiste correctamente.** (Contradice la implementación de `TaskManager` que sí persiste el plan).
*   **Al actualizarlo, se muestra duplicado en todas las tareas.** (Esto apunta más a un problema de frontend o de cómo se recupera el plan).
*   **La terminal no muestra los resultados correspondientes a ninguna tarea.**

**Posibles causas y ejemplos de código (Backend):**

1.  **Sincronización inconsistente entre `TaskManager` y `agent_routes.py`:** Aunque `TaskManager` persiste los datos, si las funciones en `agent_routes.py` (como `execute_single_step_detailed` o `get_task_status`) no utilizan consistentemente los métodos de `TaskManager` para leer y escribir el estado de la tarea, o si manipulan el estado de la tarea en memoria sin persistirlo, podría haber inconsistencias.

    *   **Ejemplo (backend/src/routes/agent_routes.py - `execute_single_step_detailed`):**

    ```python
    # backend/src/routes/agent_routes.py
    # ...
    # Actualizar en persistencia ANTES de emitir evento
    update_task_data(task_id, {"plan": steps}) # Esto usa TaskManager.update_task
    # ...
    ```
    La función `update_task_data` (que se asume es un wrapper para `task_manager.update_task`) parece estar en su lugar. El problema podría ser que el frontend no siempre *solicita* el estado actualizado del backend, o que el backend no siempre *envía* el estado completo y correcto a través de WebSockets.

2.  **Manejo de `stored_events` en `websocket_manager.py`:** El `websocket_manager.py` almacena los últimos 10 eventos por tarea. Si un cliente se desconecta y se reconecta, o cambia de tarea, debería recibir estos eventos almacenados para reconstruir el estado de la terminal y el chat. Si esta lógica de recuperación no se activa correctamente en el frontend, o si los eventos almacenados no son suficientes para reconstruir el estado completo, se vería una terminal vacía o un chat incompleto.

    *   **Ejemplo (backend/src/websocket/websocket_manager.py - `emit_to_task`):**

    ```python
    # CRITICAL FIX: Store the event for later retrieval even if no connections
    if not hasattr(self, 'stored_events'):
        self.stored_events = {}
    if task_id not in self.stored_events:
        self.stored_events[task_id] = []
    
    # Store last 10 events per task for late-joining clients
    self.stored_events[task_id].append(enhanced_data)
    if len(self.stored_events[task_id]) > 10:
        self.stored_events[task_id] = self.stored_events[task_id][-10:]
    ```
    Esta lógica es correcta para almacenar eventos. El problema es si el frontend realmente los solicita y los usa para reconstruir el estado al cambiar de tarea.

3.  **Recuperación de tareas incompletas al inicio del backend:** El `TaskManager` tiene una función `recover_incomplete_tasks_on_startup`. Si esta función no carga todos los datos necesarios (chat, terminal logs, plan completo) en el caché o si el frontend no tiene un mecanismo para solicitar el estado completo de las tareas recuperadas al iniciar la aplicación, se verían inconsistencias.

    *   **Ejemplo (backend/src/services/task_manager.py - `recover_incomplete_tasks_on_startup`):**

    ```python
    # backend/src/services/task_manager.py
    # ...
    for task in incomplete_tasks:
        task_id = task.get("task_id")
        if task_id:
            # Cargar en caché para acceso rápido
            self.active_cache[task_id] = task
            recovered_task_ids.append(task_id)
    ```
    Aquí se carga la tarea completa en el caché. El problema es cómo el frontend utiliza esta información al iniciar o al cambiar de tarea.

### 2.3. Resumen de los Problemas Identificados

Los problemas de persistencia y aislamiento no parecen ser una falla fundamental en la arquitectura de almacenamiento (MongoDB + TaskManager), sino más bien en la **sincronización y el flujo de datos entre el backend y el frontend, y cómo el frontend gestiona y renderiza el estado aislado por tarea.**

*   **Duplicación de chat y plan de acción:** Sugiere que el frontend no está limpiando o cargando el estado correcto al cambiar de tarea, o que los eventos de WebSocket se están aplicando a un estado global en lugar de al estado específico de la tarea activa.
*   **Terminal no muestra resultados:** Indica que la salida de la terminal no se está asociando correctamente con la tarea activa, o que no se está recuperando el historial de comandos/salidas al cambiar de tarea.

El `AppContext.tsx` ya tiene la estructura para el aislamiento, lo que es una ventaja. La clave será asegurar que los `useCallbacks` y `useEffects` en los hooks del frontend (ej. `useTaskManagement`, `useWebSocket`, `useTerminalManagement`, `usePlanManager`) estén correctamente vinculados al `activeTaskId` y que actualicen los estados aislados de forma granular. Además, la lógica de recuperación de estado al cambiar de tarea en el frontend debe ser robusta, posiblemente solicitando el estado completo de la tarea al backend si no está disponible en el caché del frontend.



### 2.4. Detalles de Persistencia y Aislamiento por Componente

#### 2.4.1. Chat

**Problema Reportado:** El chat se duplica.

**Análisis:**

*   **Frontend (`AppContext.tsx` y `useTaskManagement.ts`):**
    *   `AppContext.tsx` tiene `taskMessages: Record<string, Message[]>;` que es la estructura correcta para aislar los mensajes por tarea. Cuando se añade una nueva tarea (`ADD_TASK`), se inicializa `taskMessages[newTask.id]` con `newTask.messages || []`. Cuando se migra un `taskId` (`UPDATE_TASK_ID`), el estado de `taskMessages` se mueve al nuevo ID. Cuando se elimina una tarea (`DELETE_TASK`), el estado de `taskMessages` para esa tarea se limpia.
    *   `useTaskManagement.ts` utiliza `addTaskMessage` (que es un `dispatch` a `ADD_TASK_MESSAGE` en `AppContext.tsx`) para añadir mensajes. Esta acción también está diseñada para ser aislada por `taskId`.

    **Ejemplo de `AppContext.tsx` (Reducer `ADD_TASK_MESSAGE`):**
    ```typescript
    case 'ADD_TASK_MESSAGE':
      return {
        ...state,
        taskMessages: {
          ...state.taskMessages,
          [action.payload.taskId]: [
            ...(state.taskMessages[action.payload.taskId] || []),
            action.payload.message
          ]
        }
      };
    ```
    Esta implementación del reducer es correcta para el aislamiento. El problema de duplicación sugiere que:
    1.  **Múltiples componentes están escuchando y añadiendo mensajes al mismo tiempo, o**
    2.  **Los mensajes se están añadiendo a un `taskId` incorrecto, o**
    3.  **El `useWebSocket.ts` está procesando eventos de chat y añadiéndolos sin verificar si ya existen o si el `activeTaskId` es el correcto para la visualización.**

*   **Backend (`agent_routes.py` y `websocket_manager.py`):**
    *   El backend envía mensajes de chat a través de WebSockets. En `agent_routes.py`, la función `emit_step_event` (que a su vez usa `websocket_manager.emit_to_task`) es la encargada de enviar actualizaciones al frontend. Estos eventos incluyen el `task_id`.

    **Ejemplo de `websocket_manager.py` (`emit_to_task`):**
    ```python
    def emit_to_task(self, task_id: str, event: str, data: Dict[str, Any]):
        # ...
        enhanced_data = {
            **data,
            'task_id': task_id,
            'event': event,
            'server_timestamp': datetime.now().isoformat()
        }
        # ...
        self.socketio.emit(event, enhanced_data, room=task_id)
        # ...
    ```
    La lógica del backend para emitir eventos de chat parece correcta en cuanto al aislamiento por `task_id`. El problema de duplicación en el chat es casi seguro un problema del frontend, donde los mensajes se están renderizando o añadiendo al estado de forma incorrecta.

#### 2.4.2. Plan de Acción

**Problema Reportado:** El plan de acción no persiste correctamente. Al actualizarlo, se muestra duplicado en todas las tareas.

**Análisis:**

*   **Frontend (`AppContext.tsx` y `usePlanManager.ts`):**
    *   `AppContext.tsx` tiene `taskPlanStates: Record<string, { plan: TaskStep[]; ... }>;` para aislar el estado del plan por tarea. La acción `UPDATE_TASK_PLAN` está diseñada para actualizar el plan de una tarea específica.

    **Ejemplo de `AppContext.tsx` (Reducer `UPDATE_TASK_PLAN`):**
    ```typescript
    case 'UPDATE_TASK_PLAN':
      return {
        ...state,
        taskPlanStates: {
          ...state.taskPlanStates,
          [action.payload.taskId]: {
            ...(state.taskPlanStates[action.payload.taskId] || {}),
            plan: action.payload.plan,
            lastUpdateTime: new Date()
          }
        }
      };
    ```
    Similar al chat, la estructura de datos y la acción del reducer son correctas para el aislamiento. La duplicación sugiere que:
    1.  **El componente que muestra el plan de acción no está leyendo del `taskPlanStates[activeTaskId]` o no se está re-renderizando correctamente al cambiar `activeTaskId`.**
    2.  **El backend está enviando actualizaciones de plan que el frontend aplica a todas las tareas o a un estado global.**

*   **Backend (`agent_routes.py` y `task_manager.py`):**
    *   El `TaskManager` (`src/services/task_manager.py`) es la fuente de verdad para la persistencia del plan. Los planes se guardan en MongoDB como parte del documento de la tarea.

    **Ejemplo de `task_manager.py` (`update_task`):**
    ```python
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        # ...
        success = self.db_service.update_task(task_id, updates)
        if success:
            if task_id in self.active_cache:
                self.active_cache[task_id].update(updates)
        # ...
    ```
    Cuando el backend genera un plan (en `agent_routes.py` dentro de la ruta `/api/agent/chat`), este plan se persiste usando `update_task_data` (que llama a `task_manager.update_task`).

    **Ejemplo de `agent_routes.py` (en la ruta `/api/agent/chat`):**
    ```python
    # ... después de generar el plan ...
    update_task_data(task_id, {
        'plan': frontend_plan, # El plan se guarda aquí
        'status': 'plan_generated',
        'task_type': data.get('task_type', 'general'),
        'complexity': data.get('complexity', 'media'),
        'ai_generated': True,
        'plan_source': 'ollama'
    })
    # ...
    ```
    La persistencia del plan en el backend es robusta. El problema de duplicación y no persistencia en la UI es casi seguro un problema del frontend, donde el estado del plan no se está cargando o visualizando correctamente al cambiar de tarea.

#### 2.4.3. Terminal

**Problema Reportado:** La terminal no muestra los resultados correspondientes a ninguna tarea.

**Análisis:**

*   **Frontend (`AppContext.tsx` y `useTerminalManagement.ts`):**
    *   `AppContext.tsx` tiene `terminalLogs: Record<string, Array<{ message: string; ... }>>;` y `taskTerminalCommands: Record<string, Array<{ id: string; command: string; ... }>>;` para aislar los logs y comandos de la terminal por tarea.
    *   `useTerminalManagement.ts` utiliza `addTerminalLog` y `addTaskTerminalCommand` para añadir entradas a estos estados aislados.

    **Ejemplo de `AppContext.tsx` (Reducer `ADD_TERMINAL_LOG`):**
    ```typescript
    case 'ADD_TERMINAL_LOG':
      return {
        ...state,
        terminalLogs: {
          ...state.terminalLogs,
          [action.payload.taskId]: [
            ...(state.terminalLogs[action.payload.taskId] || []),
            { ...action.payload.log, timestamp: new Date(action.payload.log.timestamp) }
          ]
        }
      };
    ```
    La estructura de datos y las acciones del reducer son correctas para el aislamiento.

*   **Backend (`agent_routes.py` y `websocket_manager.py`):**
    *   La salida de la terminal se envía a través de WebSockets. El `agent_routes.py` emite eventos de `step_completed` que incluyen el `result` de la ejecución de la herramienta, que a menudo contiene la salida de la terminal.
    *   El `websocket_manager.py` almacena los últimos 10 eventos en `stored_events` por `task_id`. Estos eventos deberían ser utilizados por el frontend para reconstruir el historial de la terminal cuando un usuario cambia a una tarea existente.

    **Ejemplo de `agent_routes.py` (en `execute_single_step_detailed`):**
    ```python
    # ...
    emit_step_event(task_id, 'step_completed', {
        'step_id': current_step.get('id'),
        'step_index': step_index,
        'title': current_step.get('title', 'Paso completado'),
        'result': step_result, # Aquí se incluye la salida de la herramienta/terminal
        'activity': f"Completado paso {step_index + 1}: {current_step.get('title', 'Sin título')}",
        'progress_percentage': int(((step_index + 1) / len(steps)) * 100),
        'timestamp': datetime.now().isoformat()
    })
    # ...
    ```
    El problema de la terminal que no muestra los resultados es probablemente una combinación de:
    1.  **El frontend no está solicitando o procesando correctamente los `stored_events` del `websocket_manager` al cambiar de tarea.**
    2.  **El componente `TerminalView` no está leyendo del `terminalLogs[activeTaskId]` o no se está re-renderizando correctamente.**
    3.  **La forma en que la salida de la herramienta se mapea a los `terminalLogs` en el frontend podría ser incorrecta o incompleta.**

En resumen, la arquitectura de persistencia del backend (MongoDB + `TaskManager`) parece sólida. El problema principal reside en la capa del frontend, específicamente en cómo se gestiona el estado global de la aplicación (a través de `AppContext`) y cómo los componentes de la UI consumen y reaccionan a los cambios en el `activeTaskId` para mostrar los datos aislados de cada tarea. La lógica de recuperación de estado al cambiar de tarea y al reconectar WebSockets necesita ser revisada y fortalecida en el frontend.



## 3. Análisis de Duplicaciones y su Impacto

Los problemas reportados de "duplicación" en el chat y el plan de acción no parecen ser el resultado de una duplicación literal de datos en la persistencia del backend (MongoDB), sino más bien una **duplicación percibida en la interfaz de usuario (UI)**. Esto ocurre cuando el frontend no gestiona correctamente el estado de las tareas al cambiar entre ellas, mostrando información de una tarea en el contexto de otra, o acumulando información que debería ser específica de una sola tarea.

### 3.1. Duplicación Percibida en el Frontend

La arquitectura del frontend, especialmente en `AppContext.tsx`, ya ha implementado un modelo de datos que aísla el estado por `taskId` (e.g., `taskMessages: Record<string, Message[]>`, `taskPlanStates: Record<string, { plan: TaskStep[]; ... }>`). Esto significa que, a nivel de almacenamiento en el frontend, los datos no están intrínsecamente duplicados para diferentes tareas; cada tarea tiene su propio conjunto de mensajes, planes, logs, etc.

La duplicación se manifiesta visualmente debido a:

*   **Falta de reseteo o carga adecuada del estado al cambiar de tarea:** Si un componente de la UI (como `ChatInterface` o `TaskView`) no se re-renderiza completamente o no actualiza sus datos internos para reflejar el `activeTaskId` actual, podría seguir mostrando datos de la tarea previamente activa. Esto da la impresión de que el chat o el plan se han "duplicado" en la nueva tarea, cuando en realidad es el componente el que no ha cambiado su fuente de datos.

    *   **Impacto:** Confusión para el usuario, experiencia de usuario inconsistente, dificultad para seguir el progreso de tareas individuales, y una percepción de inestabilidad del sistema.

*   **Manejo incorrecto de eventos de WebSocket:** Si el `useWebSocket.ts` o los componentes que consumen sus datos no filtran los eventos por el `activeTaskId` actual, o si aplican los eventos a un estado global en lugar del estado específico de la tarea, los mensajes o actualizaciones del plan de una tarea podrían aparecer en la UI de otra tarea.

    *   **Impacto:** Mezcla de información entre tareas, lo que invalida el concepto de aislamiento de tareas y hace que el agente sea ineficaz para manejar múltiples contextos simultáneamente.

*   **Inicialización incompleta de componentes:** Aunque `AppContext.tsx` inicializa correctamente los estados aislados para una nueva tarea, si los componentes hijos no se montan/desmontan o no se reinicializan correctamente al cambiar de tarea, podrían retener estados internos que no corresponden a la tarea actual.

    *   **Impacto:** Datos residuales de tareas anteriores, lo que contribuye a la percepción de duplicación y a un comportamiento impredecible de la UI.

### 3.2. Ausencia de Duplicación Crítica en el Backend

Basado en la revisión de `server.py`, `agent_routes.py`, `websocket_manager.py`, y `task_manager.py`, no se encontraron evidencias de duplicación de lógica o datos a nivel de persistencia en el backend que causen los problemas reportados. El `TaskManager` utiliza MongoDB como fuente de verdad única para cada tarea, y el `websocket_manager` almacena eventos por `task_id`.

*   **`TaskManager`:** Cada tarea se guarda como un documento único en MongoDB, y el caché en memoria (`active_cache`) también es un mapeo de `task_id` a `task_data`. No hay duplicación de la tarea completa.

*   **`agent_routes.py`:** Las operaciones de actualización (`update_task_data`) se realizan sobre un `task_id` específico, asegurando que los cambios se apliquen al documento de tarea correcto.

*   **`websocket_manager.py`:** Los eventos se emiten y se almacenan con un `task_id` asociado, lo que permite un direccionamiento preciso de las actualizaciones.

La única "duplicación" en el backend podría ser la lógica de fallback en `server.py` si las rutas reales del agente no se cargan, pero esto es un mecanismo de seguridad y no una causa de los problemas de persistencia/aislamiento en un entorno de producción funcional.

### 3.3. Impacto General de la Duplicación Percibida

La duplicación percibida en la UI, aunque no sea una duplicación de datos subyacente, tiene un impacto significativo en la **usabilidad y fiabilidad** del agente:

*   **Inconsistencia del Estado:** El usuario ve un estado que no corresponde a la tarea activa, lo que rompe la coherencia entre la UI y el backend.
*   **Experiencia de Usuario Degradada:** La dificultad para gestionar múltiples tareas y la confusión generada por la mezcla de información hacen que el agente sea menos útil y frustrante de usar.
*   **Dificultad en la Depuración:** Los desarrolladores pueden tener dificultades para identificar la causa raíz de los problemas, ya que la UI muestra un comportamiento que no se alinea con el estado real del backend.
*   **Falta de Confianza:** El comportamiento errático del agente erosiona la confianza del usuario en su capacidad para manejar tareas complejas de manera fiable.

En resumen, el problema de duplicación es principalmente un problema de **sincronización y gestión del estado en el frontend**, donde los componentes no están reaccionando adecuadamente a los cambios de `activeTaskId` o no están consumiendo los datos aislados de manera correcta. La solución requerirá un enfoque cuidadoso en la lógica de renderizado y actualización de los componentes de React, asegurando que siempre reflejen el estado de la tarea actualmente activa.



## 4. Diseño de Soluciones Específicas para Aislamiento de Contextos por Tarea

El análisis previo ha revelado que la arquitectura del backend para la persistencia de tareas es robusta, utilizando MongoDB y un `TaskManager` que ya aísla los datos por `task_id`. El problema principal radica en la capa del frontend, específicamente en cómo se gestiona el estado global de la aplicación (a través de `AppContext`) y cómo los componentes de la UI consumen y reaccionan a los cambios en el `activeTaskId` para mostrar los datos aislados de cada tarea. La lógica de recuperación de estado al cambiar de tarea y al reconectar WebSockets en el frontend necesita ser revisada y fortalecida.

### 4.1. Modelo de Datos para Estados de Tareas Aislados (Frontend)

El `AppContext.tsx` ya implementa un modelo de datos adecuado para el aislamiento de tareas, utilizando objetos `Record<string, ...>` donde la clave es el `taskId`. Esto es fundamental y debe mantenerse. Las estructuras existentes son:

*   `taskFiles: Record<string, any[]>;`
*   `terminalLogs: Record<string, Array<{ message: string; type: 'info' | 'success' | 'error'; timestamp: Date; taskId: string; }>>;
*   `taskMessages: Record<string, Message[]>;`
*   `taskPlanStates: Record<string, { plan: TaskStep[]; currentActiveStep: TaskStep | null; progress: number; lastUpdateTime: Date; isCompleted: boolean; }>;`
*   `taskTerminalCommands: Record<string, Array<{ id: string; command: string; status: 'pending' | 'running' | 'completed' | 'failed'; output?: string; timestamp: Date; }>>;
*   `taskWebSocketStates: Record<string, { isConnected: boolean; joinedRoom: boolean; lastEvent: Date | null; }>;`
*   `taskMonitorPages: Record<string, Array<{ id: string; title: string; content: string; type: 'plan' | 'tool-execution' | 'report' | 'file' | 'error'; timestamp: Date; toolName?: string; metadata?: any; }>>;
*   `taskCurrentPageIndex: Record<string, number>;`
*   `typingState: Record<string, boolean>;`

Este modelo es correcto y no requiere cambios estructurales importantes. La solución se centrará en asegurar que los componentes de React accedan y actualicen estos estados de manera consistente y reactiva al `activeTaskId`.

### 4.2. Soluciones para el Manejo del Chat por Tarea

El problema de duplicación del chat se debe a que los componentes de la UI no están leyendo o actualizando el estado de los mensajes de forma exclusiva para la tarea activa. La solución implica asegurar que `ChatInterface` y `useWebSocket.ts` siempre operen sobre `state.taskMessages[state.activeTaskId]`.

**Modificaciones Sugeridas (Frontend):**

1.  **`ChatInterface` Component:**
    *   Asegurarse de que el componente `ChatInterface` (y cualquier subcomponente que muestre mensajes) obtenga los mensajes directamente de `state.taskMessages[state.activeTaskId]` a través del `useAppContext`.
    *   Utilizar `useEffect` para reaccionar a los cambios en `activeTaskId` y forzar una re-renderización o un reseteo de cualquier estado interno relacionado con los mensajes.

    ```typescript
    // frontend/src/components/ChatInterface/ChatInterface.tsx (ejemplo conceptual)
    import { useAppContext } from '../../context/AppContext';
    import React, { useEffect, useRef } from 'react';

    const ChatInterface: React.FC = () => {
      const { state } = useAppContext();
      const messages = state.activeTaskId ? state.taskMessages[state.activeTaskId] || [] : [];
      const messagesEndRef = useRef<HTMLDivElement>(null);

      useEffect(() => {
        // Scroll to bottom on activeTaskId change or new messages
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, [state.activeTaskId, messages]); // Dependencia clave: activeTaskId

      return (
        <div className="chat-container">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              {msg.content}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      );
    };
    ```

2.  **`useWebSocket.ts` Hook:**
    *   Este hook es crucial. Debe asegurarse de que cuando reciba un evento de WebSocket, el `dispatch` para añadir un mensaje (`ADD_TASK_MESSAGE`) siempre use el `task_id` proporcionado en el payload del evento, y no asuma que es para la tarea actualmente activa en la UI.
    *   Además, al conectar o unirse a una tarea, el frontend debe solicitar el historial de mensajes (y logs de terminal) almacenados en el backend (`websocket_manager.stored_events`) para esa `task_id` y cargarlos en el `AppContext`.

    ```typescript
    // frontend/src/hooks/useWebSocket.ts (modificación conceptual)
    import { useEffect, useCallback } from 'react';
    import { io } from 'socket.io-client';
    import { useAppContext } from '../context/AppContext';
    import { API_CONFIG } from '../config/api';

    export const useWebSocket = () => {
      const { dispatch, state } = useAppContext();
      const socket = io(API_CONFIG.backend.url, { path: '/api/socket.io/' });

      useEffect(() => {
        socket.on('connect', () => {
          console.log('WebSocket connected');
          // Al conectar, si hay una tarea activa, unirse a su sala
          if (state.activeTaskId) {
            socket.emit('join_task', { task_id: state.activeTaskId });
          }
        });

        socket.on('task_update', (data) => {
          const { task_id, type, data: updateData } = data;
          // Asegurarse de que el update sea para la tarea correcta
          if (task_id) {
            if (type === 'new_message') {
              dispatch({ type: 'ADD_TASK_MESSAGE', payload: { taskId: task_id, message: updateData.message } });
            } else if (type === 'step_completed' || type === 'step_started') {
              // Procesar actualizaciones de plan y terminal aquí
              // Esto se detalla en las secciones siguientes
            }
            // ... otros tipos de actualizaciones
          }
        });

        // Manejar eventos de historial al unirse a una sala (si el backend los envía)
        socket.on('task_history', (data) => {
          const { task_id, messages, terminalLogs, planState } = data;
          if (task_id === state.activeTaskId) { // Solo si es la tarea activa
            dispatch({ type: 'SET_TASK_MESSAGES', payload: { taskId: task_id, messages } });
            dispatch({ type: 'SET_TERMINAL_LOGS', payload: { taskId: task_id, logs: terminalLogs } });
            dispatch({ type: 'SET_TASK_PLAN_STATE', payload: { taskId: task_id, planState } });
          }
        });

        return () => {
          socket.disconnect();
        };
      }, [dispatch, state.activeTaskId]); // Re-ejecutar si activeTaskId cambia

      const joinTaskRoom = useCallback((taskId: string) => {
        socket.emit('join_task', { task_id: taskId });
      }, [socket]);

      const leaveTaskRoom = useCallback((taskId: string) => {
        socket.emit('leave_task', { task_id: taskId });
      }, [socket]);

      return { joinTaskRoom, leaveTaskRoom };
    };
    ```

### 4.3. Soluciones para el Manejo del Plan de Acción por Tarea

El problema de duplicación del plan de acción es similar al del chat: el componente de la UI no está mostrando el plan correcto para la tarea activa.

**Modificaciones Sugeridas (Frontend):**

1.  **Componente de Visualización del Plan (ej. en `TaskView.tsx` o un subcomponente):**
    *   Asegurarse de que el componente que renderiza el plan de acción (la lista de pasos) siempre obtenga los datos de `state.taskPlanStates[state.activeTaskId].plan`.
    *   Implementar un `useEffect` para reaccionar a los cambios en `activeTaskId` y asegurarse de que el plan correcto se cargue y se muestre.

    ```typescript
    // frontend/src/components/TaskView.tsx (ejemplo conceptual)
    import { useAppContext } from '../../context/AppContext';
    import React, { useEffect } from 'react';

    const TaskView: React.FC = () => {
      const { state } = useAppContext();
      const activeTaskPlanState = state.activeTaskId ? state.taskPlanStates[state.activeTaskId] : null;
      const planSteps = activeTaskPlanState ? activeTaskPlanState.plan : [];

      useEffect(() => {
        // Lógica para asegurar que el plan se muestre correctamente al cambiar de tarea
        console.log(`Cargando plan para tarea: ${state.activeTaskId}`);
      }, [state.activeTaskId, planSteps]);

      return (
        <div className="plan-container">
          {planSteps.length > 0 ? (
            planSteps.map((step, index) => (
              <div key={step.id} className={`step ${step.status}`}>
                {step.title}
              </div>
            ))
          ) : (
            <p>No hay plan de acción para esta tarea.</p>
          )}
        </div>
      );
    };
    ```

2.  **`usePlanManager.ts` Hook:**
    *   Este hook debe asegurarse de que todas las operaciones (obtener plan, actualizar paso, etc.) se realicen sobre el `task_id` activo. Las funciones de `AppContext` ya están diseñadas para esto.

### 4.4. Soluciones para el Manejo de la Terminal por Tarea

La terminal que no muestra los resultados correctos es un problema de carga de estado y de cómo se procesan los eventos de la terminal.

**Modificaciones Sugeridas (Frontend):**

1.  **`TerminalView` Component:**
    *   Asegurarse de que `TerminalView` (y sus subcomponentes) obtenga los logs y comandos de `state.terminalLogs[state.activeTaskId]` y `state.taskTerminalCommands[state.activeTaskId]`.
    *   Utilizar `useEffect` para reaccionar a los cambios en `activeTaskId` y asegurar que la terminal se limpie y cargue los logs y comandos correctos para la nueva tarea.

    ```typescript
    // frontend/src/components/TerminalView/TerminalView.tsx (ejemplo conceptual)
    import { useAppContext } from '../../context/AppContext';
    import React, { useEffect, useRef } from 'react';

    const TerminalView: React.FC = () => {
      const { state } = useAppContext();
      const terminalLogs = state.activeTaskId ? state.terminalLogs[state.activeTaskId] || [] : [];
      const terminalCommands = state.activeTaskId ? state.taskTerminalCommands[state.activeTaskId] || [] : [];
      const terminalEndRef = useRef<HTMLDivElement>(null);

      useEffect(() => {
        // Scroll to bottom on activeTaskId change or new logs/commands
        terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, [state.activeTaskId, terminalLogs, terminalCommands]);

      return (
        <div className="terminal-container">
          {terminalLogs.map((log, index) => (
            <div key={index} className={`terminal-log ${log.type}`}>
              {log.message}
            </div>
          ))}
          {/* Render commands as well */}
          <div ref={terminalEndRef} />
        </div>
      );
    };
    ```

2.  **`useWebSocket.ts` Hook (continuación):**
    *   Cuando se recibe un evento `step_completed` o `tool_execution_detail` del backend, el `useWebSocket.ts` debe extraer la información relevante (salida de la herramienta, logs) y despacharla a `ADD_TERMINAL_LOG` o `ADD_TASK_TERMINAL_COMMAND` utilizando el `task_id` del evento.
    *   Es crucial que el backend envíe suficiente información en el `step_result` para que el frontend pueda reconstruir la salida de la terminal de manera significativa.

3.  **Backend (`agent_routes.py` y `websocket_manager.py`):**
    *   Asegurarse de que el `step_result` enviado en los eventos de WebSocket (`step_completed`) contenga toda la información necesaria para la terminal, incluyendo la salida de comandos shell, resultados de búsqueda web, etc. El `get_task_status` en `agent_routes.py` ya incluye `executionData` con `executed_tools`, lo cual es un buen punto de partida.
    *   El `websocket_manager.py` ya almacena los últimos 10 eventos. El frontend debe solicitar estos eventos al unirse a una tarea para reconstruir el historial de la terminal.

### 4.5. Gestión General del Estado en el Frontend

Para garantizar un aislamiento completo y una experiencia de usuario coherente, se deben seguir las siguientes prácticas:

1.  **Single Source of Truth:** El `AppContext` debe ser la única fuente de verdad para el estado de la aplicación. Los componentes deben obtener su estado de `AppContext` y no mantener estados locales duplicados que no se sincronicen con el contexto.

2.  **Reactividad a `activeTaskId`:** Todos los componentes que muestran información específica de la tarea (chat, plan, terminal, archivos) deben tener un `useEffect` que reaccione a los cambios en `state.activeTaskId`. Cuando `activeTaskId` cambia, el componente debe:
    *   Limpiar cualquier estado interno temporal.
    *   Cargar los datos correspondientes al nuevo `activeTaskId` desde `AppContext`.
    *   Asegurarse de que los datos se rendericen correctamente.

3.  **Manejo de la Migración de `taskId`:** El `UPDATE_TASK_ID` en `AppContext.tsx` ya maneja la migración de todos los estados aislados del `oldId` al `newId`. Esto es crítico y debe ser invocado correctamente por `useTaskManagement.ts` cuando el backend devuelve un `task_id` real después de la creación de una tarea temporal.

4.  **Recuperación de Estado al Cambiar de Tarea:**
    *   Cuando el usuario cambia de tarea en el frontend, el `useTaskManagement.ts` o un hook similar debe:
        *   Actualizar `activeTaskId` en `AppContext`.
        *   Si la tarea a la que se cambia no tiene su estado completamente cargado en el `AppContext` (ej. si es la primera vez que se selecciona desde que se inició la aplicación o si el caché del frontend se limpió), debe realizar una llamada REST al backend (`/api/agent/get-task-status/<task_id>`) para obtener el estado completo de la tarea (plan, mensajes, `executionData` para la terminal) y luego despachar las acciones correspondientes (`SET_TASK_MESSAGES`, `SET_TASK_PLAN_STATE`, `ADD_TERMINAL_LOG` para logs históricos) para poblar el `AppContext`.
        *   Unirse a la sala de WebSocket de la nueva tarea (`socket.emit('join_task', { task_id: newTaskId })`) para recibir actualizaciones en tiempo real.

5.  **Manejo de Desconexiones y Reconexiones de WebSocket:**
    *   Cuando el `useWebSocket.ts` se reconecta, debe re-unirse a la sala de la `activeTaskId` actual.
    *   El backend (`websocket_manager.py`) ya almacena los últimos 10 eventos. Al unirse a una sala, el backend podría enviar estos eventos almacenados al cliente para ayudar a reconstruir el estado de la UI. El frontend debe tener una lógica para procesar estos eventos históricos y aplicarlos al estado aislado de la tarea.

### 4.6. Consideraciones Adicionales

*   **Optimización de Rendimiento:** Aunque el aislamiento es clave, se debe monitorear el rendimiento, especialmente con muchas tareas activas. El uso de `useMemo` y `useCallback` en los hooks y componentes de React puede ayudar a prevenir re-renderizaciones innecesarias.
*   **Manejo de Errores:** Asegurar que cualquier error en la comunicación o en el procesamiento de datos se maneje de forma elegante y se muestre al usuario sin romper la aplicación.
*   **Pruebas Unitarias y de Integración:** Implementar pruebas exhaustivas para cada una de estas soluciones, especialmente para los casos de cambio de tarea, creación de tareas y manejo de eventos de WebSocket, para garantizar que el aislamiento funcione como se espera. Los casos de prueba obligatorios mencionados en el prompt (dos tareas activas al mismo tiempo) serán cruciales para validar estas soluciones.

Al implementar estas soluciones, se logrará que cada tarea tenga su propio contexto completamente aislado y persistente, resolviendo los problemas de duplicación y coherencia entre la UI y el backend.



## 5. Resumen de los Problemas Encontrados

El análisis exhaustivo del código fuente del agente general ha revelado que los problemas de coherencia entre la UI y el backend, y la falta de persistencia y aislamiento de tareas, se manifiestan principalmente en la capa del frontend. Aunque el backend utiliza MongoDB y un `TaskManager` robusto para la persistencia de datos aislados por `task_id`, la interfaz de usuario no siempre refleja este aislamiento de manera consistente.

Los problemas clave identificados son:

*   **Duplicación Percibida en la UI (Chat y Plan de Acción):** Los mensajes de chat y los pasos del plan de acción aparecen mezclados o duplicados al cambiar entre tareas. Esto no se debe a una duplicación de datos en el backend, sino a que los componentes del frontend no están actualizando su visualización de forma reactiva al `activeTaskId` o están procesando eventos de WebSocket de manera incorrecta, aplicando actualizaciones a un estado global en lugar del estado específico de la tarea.

*   **Terminal sin Resultados Correspondientes:** La terminal no muestra los logs y comandos asociados a la tarea activa. Esto sugiere una falla en la carga del historial de la terminal al cambiar de tarea y/o un procesamiento incorrecto de los eventos de la terminal enviados por WebSocket.

*   **Sincronización Inconsistente Frontend-Backend:** Aunque el backend persiste correctamente el estado de la tarea, el frontend no siempre solicita o procesa el estado completo de la tarea al cambiar entre ellas o al reconectar, lo que lleva a una UI desactualizada o inconsistente.

En esencia, la arquitectura de datos del frontend (`AppContext.tsx` con `Record<string, ...>`) es adecuada para el aislamiento, pero la implementación de los componentes y hooks de React no siempre aprovecha esta estructura de manera óptima, lo que resulta en una experiencia de usuario confusa y una percepción de falta de aislamiento.



## 6. Soluciones Propuestas

Las soluciones se centran en fortalecer la gestión del estado en el frontend y asegurar una sincronización impecable con el backend, sin requerir cambios significativos en la lógica de persistencia del backend, que ya es robusta.

### 6.1. Refuerzo del Aislamiento en el Frontend

El `AppContext.tsx` ya proporciona la estructura de datos necesaria para el aislamiento por `task_id`. La clave es asegurar que todos los componentes y hooks que interactúan con el estado de la tarea lo hagan de forma consciente del `activeTaskId`.

**Recomendaciones Clave:**

1.  **Centralizar el Acceso al Estado de la Tarea Activa:** Crear un selector o una función de utilidad en `AppContext` o en un hook dedicado (`useActiveTaskState`) que siempre devuelva el sub-estado correspondiente al `activeTaskId` actual. Esto reduce la probabilidad de errores al acceder a los datos.

    ```typescript
    // frontend/src/context/AppContext.tsx (ejemplo de selector)
    // ... dentro de useAppContext
    const getActiveTaskMessages = useCallback(() => {
      return state.activeTaskId ? state.taskMessages[state.activeTaskId] || [] : [];
    }, [state.activeTaskId, state.taskMessages]);

    const getActiveTaskPlanState = useCallback(() => {
      return state.activeTaskId ? state.taskPlanStates[state.activeTaskId] : null;
    }, [state.activeTaskId, state.taskPlanStates]);

    // ... y así para todos los estados aislados
    return { state, dispatch, getActiveTaskMessages, getActiveTaskPlanState, ... };
    ```

2.  **Uso Consistente de `useEffect` en Componentes:** Todos los componentes que visualizan datos específicos de la tarea (ej. `ChatInterface`, `TerminalView`, componentes del plan) deben usar `useEffect` con `state.activeTaskId` como dependencia para reaccionar a los cambios de tarea. Dentro de este `useEffect`, se debe asegurar que el componente se reinicialice o cargue los datos correctos.

    ```typescript
    // Ejemplo conceptual para cualquier componente de TaskView
    useEffect(() => {
      // Lógica para asegurar que el componente se actualice al cambiar de tarea
      // Por ejemplo, si hay un estado local para el scroll, resetearlo.
      // Si hay suscripciones a eventos, re-suscribirse con el nuevo taskId.
      console.log(`Componente ${componentName} actualizado para tarea: ${state.activeTaskId}`);
    }, [state.activeTaskId]);
    ```

### 6.2. Sincronización Mejorada con el Backend

La comunicación entre el frontend y el backend debe ser más robusta para asegurar que el estado de la UI siempre refleje la fuente de verdad en MongoDB.

1.  **Recuperación Completa del Estado de la Tarea al Cambiar:**
    *   Cuando el usuario selecciona una tarea existente (o al cargar la aplicación si hay una tarea activa guardada), el frontend debe realizar una llamada REST al endpoint `/api/agent/get-task-status/<task_id>` para obtener el estado completo de esa tarea desde el backend.
    *   Esta llamada debe recuperar no solo el plan, sino también el historial de mensajes y los datos de ejecución de la terminal (`executionData`).
    *   Una vez recibidos los datos, el frontend debe despachar las acciones correspondientes (`SET_TASK_MESSAGES`, `SET_TASK_PLAN_STATE`, `ADD_TERMINAL_LOG` para logs históricos) para poblar el `AppContext` para esa `task_id`.

    ```typescript
    // frontend/src/hooks/useTaskManagement.ts (modificación conceptual en setActiveTask)
    const setActiveTask = useCallback(async (taskId: string | null) => {
      dispatch({ type: 'SET_ACTIVE_TASK', payload: taskId });
      if (taskId) {
        // Fetch full task state from backend
        try {
          const response = await fetch(`${API_CONFIG.backend.url}/api/agent/get-task-status/${taskId}`);
          if (response.ok) {
            const taskData = await response.json();
            // Actualizar mensajes
            dispatch({ type: 'SET_TASK_MESSAGES', payload: { taskId, messages: taskData.messages || [] } });
            // Actualizar plan
            dispatch({ type: 'SET_TASK_PLAN_STATE', payload: { taskId, planState: { plan: taskData.plan || [], /* ...otros campos del plan */ } } });
            // Actualizar logs de terminal (convertir executionData a logs)
            const terminalLogs = convertExecutionDataToTerminalLogs(taskData.executionData);
            dispatch({ type: 'SET_TERMINAL_LOGS', payload: { taskId, logs: terminalLogs } });
            // ... y otros estados aislados
          } else {
            console.error(`Failed to fetch task status for ${taskId}`);
          }
        } catch (error) {
          console.error(`Error fetching task status for ${taskId}:`, error);
        }
      }
    }, [dispatch]);
    ```
    *Nota: Se necesitará una función `convertExecutionDataToTerminalLogs` para transformar los `executed_tools` del backend en el formato de `terminalLogs` del frontend.*

2.  **Manejo de Eventos WebSocket en `useWebSocket.ts`:**
    *   Asegurarse de que el `useWebSocket.ts` siempre procese los eventos de `task_update` (y otros eventos relevantes) utilizando el `task_id` incluido en el payload del evento.
    *   Al recibir un evento, el `dispatch` debe dirigirse al estado aislado de la tarea correspondiente, no a un estado global.
    *   Implementar una lógica para que, al unirse a una sala de WebSocket (`join_task`), el backend envíe el historial de eventos almacenados (`stored_events`) para esa tarea. El frontend debe procesar estos eventos históricos y añadirlos al estado de la tarea en `AppContext`.

    ```typescript
    // backend/src/websocket/websocket_manager.py (modificación conceptual en handle_join_task)
    @self.socketio.on("join_task")
    def handle_join_task(data):
        task_id = data.get("task_id")
        session_id = request.sid
        # ... (lógica existente para unirse a la sala y trackear conexiones)

        # Enviar eventos históricos al cliente que se une
        stored_events = self.get_stored_events(task_id)
        for event_data in stored_events:
            emit(event_data["event"], event_data, room=session_id) # Emitir a la sesión específica
        logger.info(f"Sent {len(stored_events)} historical events to new client {session_id} for task {task_id}")
    ```

    ```typescript
    // frontend/src/hooks/useWebSocket.ts (modificación conceptual para manejar historial)
    useEffect(() => {
      // ... (código existente de conexión y task_update)

      socket.on("historical_event", (data) => { // Nuevo evento para historial
        const { task_id, event, data: eventData } = data;
        // Procesar eventos históricos como si fueran eventos en tiempo real
        if (task_id) {
          if (event === 'new_message') {
            dispatch({ type: 'ADD_TASK_MESSAGE', payload: { taskId: task_id, message: eventData.message } });
          } else if (event === 'step_completed' || event === 'step_started') {
            // Procesar actualizaciones de plan y terminal
            // ... (lógica para añadir logs de terminal y actualizar plan)
          }
          // ... otros tipos de eventos históricos
        }
      });

      return () => {
        socket.disconnect();
      };
    }, [dispatch, state.activeTaskId]);
    ```

### 6.3. Plan de Implementación Paso a Paso

Este plan se enfoca en el frontend, ya que el backend parece estar bien estructurado para el aislamiento.

**Fase 1: Preparación y Refactorización de Componentes (Frontend)**

1.  **Auditoría de Componentes:** Identificar todos los componentes de React que muestran o interactúan con el chat, el plan de acción y la terminal (`ChatInterface`, `TerminalView`, `TaskView`, etc.).
2.  **Centralización del Acceso al Estado:**
    *   Modificar `AppContext.tsx` para exponer selectores (`getActiveTaskMessages`, `getActiveTaskPlanState`, etc.) que devuelvan el estado de la tarea activa.
    *   Actualizar los componentes para que utilicen estos selectores en lugar de acceder directamente a `state.taskMessages[state.activeTaskId]` (aunque la diferencia es sutil, el selector puede añadir memoización y claridad).
3.  **Implementación de `useEffect` para `activeTaskId`:** En cada componente relevante, añadir un `useEffect` que dependa de `state.activeTaskId`. Dentro de este `useEffect`:
    *   Asegurarse de que cualquier estado local que pueda retener información de la tarea anterior se reinicie.
    *   Forzar una re-renderización si es necesario (aunque React debería manejar esto automáticamente si las dependencias son correctas).

**Fase 2: Mejora de la Sincronización y Recuperación (Frontend)**

1.  **Función de Conversión de `executionData`:** Crear una función de utilidad (`convertExecutionDataToTerminalLogs`) que tome el `executionData` del backend (obtenido de `/api/agent/get-task-status`) y lo transforme en el formato de `terminalLogs` y `taskTerminalCommands` esperado por el frontend.
2.  **Implementación de `setActiveTask` Mejorado:** Modificar el `setActiveTask` en `useTaskManagement.ts` para que, al cambiar de tarea, realice una llamada REST a `/api/agent/get-task-status/<task_id>`. Luego, despachar las acciones (`SET_TASK_MESSAGES`, `SET_TASK_PLAN_STATE`, `SET_TERMINAL_LOGS`, etc.) para poblar el `AppContext` con el estado completo de la tarea recuperada.
3.  **Manejo de Historial de WebSocket:**
    *   Modificar `websocket_manager.py` en el backend para que, al recibir un evento `join_task`, envíe los `stored_events` (historial de los últimos eventos) al cliente que se une, utilizando un nuevo tipo de evento (ej. `historical_event`).
    *   Modificar `useWebSocket.ts` en el frontend para escuchar el evento `historical_event` y procesar estos eventos, añadiéndolos al estado aislado de la tarea en `AppContext`.

**Fase 3: Pruebas Exhaustivas**

1.  **Pruebas Unitarias:** Escribir pruebas unitarias para los selectores de `AppContext` y para la función `convertExecutionDataToTerminalLogs`.
2.  **Pruebas de Integración (Frontend):**
    *   **Caso de Prueba 1: Creación de Múltiples Tareas:** Crear dos o más tareas nuevas y verificar que el chat, el plan de acción y la terminal de cada tarea estén completamente vacíos al inicio y que no se mezclen los datos a medida que se interactúa con ellas.
    *   **Caso de Prueba 2: Cambio entre Tareas Activas:** Iniciar una tarea, interactuar con ella (enviar mensajes, ejecutar pasos del plan, ver salida de terminal). Luego, cambiar a una segunda tarea, interactuar con ella. Volver a la primera tarea y verificar que su estado (chat, plan, terminal) se haya restaurado correctamente y no contenga información de la segunda tarea.
    *   **Caso de Prueba 3: Recarga de Página:** Iniciar una tarea, interactuar con ella. Recargar la página del navegador y verificar que el estado de la tarea activa se restaure correctamente (si la aplicación tiene un mecanismo para recordar la última tarea activa).
    *   **Caso de Prueba 4: Desconexión/Reconexión de WebSocket:** Simular una desconexión y reconexión del WebSocket (ej. reiniciando el backend) y verificar que el frontend pueda recuperar el estado de la tarea activa y su historial de eventos.
3.  **Pruebas de Rendimiento:** Monitorear el rendimiento de la aplicación con múltiples tareas activas para asegurar que las mejoras no introduzcan latencia excesiva.

### 6.4. Casos de Prueba Obligatorios (Reiteración y Detalle)

Para validar las soluciones, se deben ejecutar los siguientes casos de prueba, prestando especial atención a la coherencia y el aislamiento del `TaskView` (chat, plan de acción, terminal):

1.  **Test con al menos dos tareas activas al mismo tiempo:**
    *   **Paso 1:** Crear `Tarea A`. Enviar 3-4 mensajes en el chat. Iniciar la ejecución de un paso del plan. Ejecutar un comando en la terminal y observar la salida.
    *   **Paso 2:** Crear `Tarea B`. Verificar que el chat, el plan de acción y la terminal de `Tarea B` estén completamente vacíos. Enviar 3-4 mensajes diferentes en el chat de `Tarea B`. Iniciar la ejecución de un paso diferente del plan. Ejecutar un comando diferente en la terminal y observar la salida.
    *   **Paso 3:** Cambiar de `Tarea B` a `Tarea A`. Verificar que el chat de `Tarea A` muestre solo los mensajes de `Tarea A`, que el plan de acción de `Tarea A` muestre su estado original, y que la terminal de `Tarea A` muestre solo los logs y comandos de `Tarea A`.
    *   **Paso 4:** Cambiar de `Tarea A` a `Tarea B`. Verificar que el chat de `Tarea B` muestre solo los mensajes de `Tarea B`, que el plan de acción de `Tarea B` muestre su estado original, y que la terminal de `Tarea B` muestre solo los logs y comandos de `Tarea B`.

2.  **Verificación de Persistencia y Carga:**
    *   Después de realizar el Test 1, recargar la página del navegador (simulando un cierre y reapertura de la aplicación). Si la aplicación tiene un mecanismo para recordar la última tarea activa, verificar que al cargar, el estado de esa tarea se restaure correctamente. Si no, seleccionar manualmente una de las tareas y verificar su estado.

3.  **Verificación de Eventos Históricos de WebSocket:**
    *   Con una tarea activa y con historial de chat y terminal, reiniciar el backend (simulando una desconexión de WebSocket). Una vez que el backend se reinicie y el frontend se reconecte, verificar que el historial de chat y terminal se reconstruya correctamente a través de los eventos históricos enviados por el `websocket_manager`.

Al completar estas pruebas con éxito, se podrá confirmar que el sistema se comporta como un agente general bien diseñado, con tareas completamente independientes y persistentes, y que los problemas de inconsistencia y duplicación han sido resueltos.

