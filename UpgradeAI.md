# Informe Profesional: Análisis y Mejoras para la Aplicación Mitosis

**Fecha:** 8 de marzo de 2025
**Autor:** Manus AI

## 1. Introducción

El presente informe detalla un análisis exhaustivo de la arquitectura y el comportamiento de la aplicación Mitosis, con el objetivo de identificar las causas raíz de las inconsistencias reportadas por el usuario. Estas incluyen la falta de aislamiento entre tareas, la contaminación de contenido, la visualización incorrecta del estado del agente ("PENSANDO" en todas las tareas), y problemas con la gestión del ciclo de vida de las tareas, como la imposibilidad de eliminarlas. El análisis se ha centrado en el backend de la aplicación, revisando la estructura del proyecto, los módulos de orquestación, gestión de memoria, servicios de base de datos y comunicación en tiempo real.

El objetivo principal es proporcionar un conjunto de instrucciones de mejora completas y detalladas, diseñadas para rectificar estos problemas sin comprometer la interfaz de usuario (UI) o la experiencia de usuario (UX) existente. Cada propuesta de mejora ha sido concebida con una perspectiva de desarrollo senior, asegurando la robustez, escalabilidad y mantenibilidad del sistema, y verificando su impacto de extremo a extremo.

## 2. Estructura del Proyecto y Análisis de Componentes Clave

La aplicación Mitosis presenta una estructura modular en su backend, organizada de la siguiente manera:

*   `backend/server.py`: Punto de entrada principal de la aplicación Flask.
*   `backend/src/`: Contiene la lógica de negocio y los módulos principales.
    *   `agents/`: Módulos relacionados con la lógica de los agentes.
    *   `core/`: Componentes centrales.
    *   `orchestration/`: Lógica de orquestación de tareas.
        *   `task_orchestrator.py`: Orquestador principal de tareas.
        *   `hierarchical_planning_engine.py`: Motor de planificación jerárquica.
        *   `adaptive_execution_engine.py`: Motor de ejecución adaptativa.
        *   `dependency_resolver.py`: Resolución de dependencias.
        *   `resource_manager.py`: Gestión de recursos.
        *   `planning_algorithms.py`: Algoritmos de planificación.
    *   `memory/`: Gestión de la memoria del agente.
        *   `advanced_memory_manager.py`: Gestor unificado de memoria.
        *   `working_memory_store.py`: Memoria de trabajo (contexto inmediato).
        *   `episodic_memory_store.py`: Memoria episódica (experiencias pasadas).
        *   `semantic_memory_store.py`: Memoria semántica (conocimiento general).
        *   `procedural_memory_store.py`: Memoria procedimental (procedimientos y estrategias).
        *   `semantic_indexer.py`: Indexador semántico.
        *   `embedding_service.py`: Servicio de embeddings.
    *   `routes/`: Definición de las rutas API.
        *   `agent_routes.py`: Rutas relacionadas con las operaciones del agente y tareas.
    *   `services/`: Servicios de soporte.
        *   `database.py`: Servicio de conexión y operaciones con MongoDB.
        *   `ollama_service.py`: Servicio de interacción con Ollama.
        *   `task_manager.py`: (Antiguo) Gestor de tareas, ahora subsumido por `task_orchestrator` y `database.py`.
        *   `websocket/websocket_manager.py`: Gestión de la comunicación en tiempo real.
    *   `validation/`: Lógica de validación.
    *   `tools/`: Herramientas utilizadas por el agente.

Esta estructura es, en general, adecuada para una aplicación de agente. Sin embargo, el análisis ha revelado varios puntos de mejora críticos relacionados con el aislamiento de tareas, la gestión del estado y la comunicación en tiempo real, que se detallan en las siguientes secciones.



## 3. Problemas de Arquitectura y Aislamiento

Durante la fase de análisis, se identificaron varias áreas donde la arquitectura actual de Mitosis presenta desafíos significativos en cuanto al aislamiento de tareas y la prevención de la contaminación de contenido. Estos problemas se manifiestan en el comportamiento observado por el usuario, como la visualización del agente "PENSANDO" en todas las tareas simultáneamente y la mezcla de información entre ellas.

### 3.1. Aislamiento de Tareas Concurrentes

El `TaskOrchestrator` (`backend/src/orchestration/task_orchestrator.py`) es el componente central para la gestión de tareas. Si bien implementa un mecanismo para `active_orchestrations` [1], la forma en que se manejan los contextos y los recursos compartidos puede llevar a una falta de aislamiento efectivo. La concurrencia se gestiona a nivel de orquestación, pero no se garantiza que los componentes internos (como los servicios de memoria o las herramientas) operen con un contexto de tarea estrictamente aislado. Si un servicio subyacente no es consciente del `task_id` o `session_id` actual, podría procesar o almacenar datos de múltiples tareas de forma indistinta, causando la "contaminación" observada.

**Problema Identificado:**

*   **Falta de Contexto Propagado:** No todos los componentes o funciones parecen recibir explícitamente el `task_id` o `session_id` como parte de su contexto de operación. Esto es crucial para que las operaciones de logging, memoria y comunicación WebSocket se atribuyan correctamente a una tarea específica.
*   **Recursos Compartidos sin Segmentación:** Si bien existe un `ResourceManager`, no está claro si los recursos (como conexiones a bases de datos o servicios externos) se segmentan o se utilizan de manera que eviten el cruce de datos entre tareas. Por ejemplo, si un servicio de herramientas no limpia su estado entre ejecuciones de diferentes tareas, podría haber fugas de información.

**Mejoras Propuestas:**

1.  **Inyección de Contexto Global (Thread-Local/Async-Local):** Implementar un mecanismo para propagar el `OrchestrationContext` (que incluye `task_id`, `user_id`, `session_id`) a través de toda la pila de ejecución de una tarea. Esto se puede lograr utilizando `contextvars` en Python (para código asíncrono) o `threading.local` (para código síncrono). Cada función o método que opere dentro del contexto de una tarea debe poder acceder a estos identificadores de forma transparente. Esto asegura que los logs, las operaciones de memoria y las comunicaciones se asocien siempre a la tarea correcta.
    *   **Implementación:** Crear un `TaskContextHolder` que almacene el contexto actual de la tarea. Antes de iniciar la orquestación de una tarea, establecer este contexto. Asegurarse de que los servicios de memoria, los servicios de herramientas y el `WebSocketManager` accedan a este contexto para filtrar o etiquetar sus operaciones.
    *   **Ejemplo de `TaskContextHolder` (Conceptual):**
        ```python
        import contextvars

        current_task_context = contextvars.ContextVar('current_task_context', default=None)

        def set_current_task_context(context: Dict):
            current_task_context.set(context)

        def get_current_task_context():
            return current_task_context.get()
        ```
        Luego, en `TaskOrchestrator.orchestrate_task`:
        ```python
        import contextvars
        # ...
        async def orchestrate_task(self, context: OrchestrationContext) -> OrchestrationResult:
            token = current_task_context.set(context) # Establecer el contexto
            try:
                # ... lógica de orquestación ...
            finally:
                current_task_context.reset(token) # Restablecer el contexto al finalizar
        ```
        Y en otros módulos, para acceder al `task_id`:
        ```python
        from your_module.task_context import get_current_task_context

        def some_function_in_memory_manager():
            context = get_current_task_context()
            task_id = context.task_id if context else "unknown"
            logger.info(f"Operando para tarea: {task_id}")
            # ... usar task_id para segmentar datos ...
        ```
2.  **Refactorización de Servicios para Contexto de Tarea:** Revisar cada servicio (especialmente `AdvancedMemoryManager`, `WorkingMemoryStore`, `EpisodicMemoryStore`, `SemanticMemoryStore`, `ProceduralMemoryStore`, y cualquier servicio de herramientas) para asegurar que todas las operaciones de lectura/escritura de datos incluyan el `task_id` como un parámetro explícito o lo obtengan del `TaskContextHolder`. Esto permitirá que los datos se almacenen y recuperen de forma segmentada por tarea.
    *   **Impacto:** Garantizará que la memoria de trabajo, episódica y semántica no mezclen datos entre diferentes tareas, y que los logs se puedan filtrar por tarea, resolviendo la "contaminación" de contenido.

### 3.2. Persistencia de Datos y Aislamiento (MongoDB)

El `DatabaseService` (`backend/src/services/database.py`) utiliza MongoDB para la persistencia de datos. Se observó que las colecciones `tasks`, `conversations`, `files`, `shares` y `tool_results` están indexadas por `task_id`, lo cual es una buena práctica para el aislamiento a nivel de base de datos. Sin embargo, la lógica de `save_task` utiliza `replace_one` con `upsert=True` [2]. Si bien esto previene duplicados, es fundamental que el `task_id` sea verdaderamente único y se genere de forma robusta para cada nueva tarea. Si el `task_id` no es único o se reutiliza accidentalmente, podría haber sobrescritura de datos de tareas diferentes.

**Problema Identificado:**

*   **Generación de `task_id`:** Es crucial asegurar que el `task_id` generado para cada tarea sea globalmente único y no colisione. El uso de `uuid.uuid4()` es una buena práctica para esto, y se observa que `agent_routes.py` lo utiliza [3]. Sin embargo, es importante verificar que este `task_id` se propague consistentemente a todos los subsistemas que interactúan con la base de datos.
*   **Limpieza de Tareas:** La función `delete_task` en `DatabaseService` elimina correctamente la tarea y sus conversaciones y archivos asociados [4]. Sin embargo, si una tarea no se elimina explícitamente (por ejemplo, debido a un fallo en el flujo de trabajo), sus datos residuales podrían permanecer en la base de datos, contribuyendo a la percepción de "tareas que no se pueden borrar" o a un crecimiento descontrolado de la base de datos.

**Mejoras Propuestas:**

1.  **Auditoría de Generación y Propagación de `task_id`:** Realizar una auditoría completa para asegurar que cada nueva tarea genere un `task_id` único (usando `uuid.uuid4()`) en el punto de entrada de la creación de la tarea, y que este `task_id` se propague sin modificaciones a todos los componentes que interactúan con la base de datos o con el `WebSocketManager`. Cualquier operación de lectura o escritura de datos relacionada con una tarea debe usar este `task_id` como clave principal para el aislamiento.
2.  **Implementación de Políticas de Retención de Datos:** Complementar la función `cleanup_old_data` [5] con políticas de retención más explícitas y automatizadas. Esto podría incluir:
    *   **Tareas Completadas/Fallidas:** Un proceso en segundo plano que elimine automáticamente tareas que han finalizado (completadas o fallidas) después de un período configurable (e.g., 7 o 30 días). Esto abordaría el problema de las "tareas que no se pueden borrar" si el usuario espera una limpieza automática.
    *   **Archivos Temporales:** Implementar una limpieza más agresiva de archivos temporales o resultados intermedios que no sean necesarios una vez que la tarea ha finalizado o ha sido marcada para eliminación.

### 3.3. Uso de WebSockets y Contaminación de Contenido

El `WebSocketManager` (`backend/src/websocket/websocket_manager.py`) es fundamental para la comunicación en tiempo real con el frontend. Se observó que el manager utiliza "rooms" (`join_room(task_id)`) para segmentar las actualizaciones por `task_id` [6], lo cual es una buena práctica. Además, se implementa un almacenamiento de mensajes (`stored_messages`) para clientes que se unen tarde a una tarea [7]. Sin embargo, la descripción del problema sugiere que el contenido se "mezcla" o el agente se ve "PENSANDO" en todas las tareas.

**Problema Identificado:**

*   **Emisión Global Inadvertida:** Aunque la mayoría de las emisiones son a una `room=task_id`, se observa una "Strategy 2: Broadcast to all connected clients for critical messages" para `UpdateType.LOG_MESSAGE`, `UpdateType.BROWSER_ACTIVITY`, `UpdateType.TASK_PROGRESS` [8]. Esta emisión global es la causa directa de que el agente se vea "PENSANDO" en todas las tareas y de la contaminación de logs, ya que estos mensajes se envían a *todos* los clientes conectados, independientemente de la tarea a la que estén suscritos.
*   **Falta de Filtrado en el Frontend:** Si el frontend no filtra correctamente los mensajes recibidos por `task_id` (incluso si se emiten a una sala específica), podría mostrar información de tareas no seleccionadas. Aunque el backend emite a salas, el frontend debe ser robusto en su manejo de los datos recibidos.

**Mejoras Propuestas:**

1.  **Eliminar Emisiones Globales de Logs y Progreso:** La "Strategy 2" en `WebSocketManager.send_update` [8] debe ser eliminada o modificada para que estos tipos de mensajes (LOG_MESSAGE, BROWSER_ACTIVITY, TASK_PROGRESS) se emitan *únicamente* a la `room=task_id` correspondiente. Esto es crítico para asegurar el aislamiento visual y de contenido en el frontend. Si se necesita una vista global de la actividad del sistema, se debe implementar un canal de comunicación separado y explícito para ello, al que el frontend se suscriba solo si es necesario.
    *   **Impacto:** Resolverá directamente el problema de que el agente se vea "PENSANDO" en todas las tareas y la mezcla de contenido en la terminal.
2.  **Reforzar el Filtrado en el Frontend:** Aunque la modificación anterior es la más importante, es una buena práctica asegurar que el frontend siempre filtre los mensajes recibidos por `task_id` antes de mostrarlos. Esto añade una capa de robustez y previene problemas si futuras emisiones globales se introducen accidentalmente o si el frontend se suscribe a múltiples tareas.

### 3.4. Gestión de la Memoria y Fugas de Información

Los módulos de memoria (`working_memory_store.py`, `advanced_memory_manager.py`, etc.) son cruciales para el comportamiento del agente. `WorkingMemoryStore` implementa un mecanismo de TTL (Time-To-Live) y LRU (Least Recently Used) para limpiar contextos expirados [9]. `AdvancedMemoryManager` orquesta el almacenamiento y recuperación de experiencias en diferentes tipos de memoria [10].

**Problema Identificado:**

*   **Contexto de Tarea en Memoria:** Si bien `AdvancedMemoryManager.store_experience` recibe un `task_context` [11], no se observa un mecanismo explícito para que las búsquedas (`retrieve_relevant_context`, `semantic_search`) filtren los resultados por `task_id` por defecto. Esto significa que una tarea podría recuperar información de la memoria que pertenece a otra tarea, lo que contribuye a la contaminación de contenido.
*   **Fugas de Memoria Lógicas:** Aunque `WorkingMemoryStore` tiene mecanismos de limpieza, si los otros tipos de memoria (episódica, semántica, procedimental) no tienen límites de capacidad o mecanismos de limpieza basados en la relevancia o el tiempo, podrían crecer indefinidamente, almacenando información de tareas antiguas que ya no son relevantes, lo que podría llevar a un rendimiento degradado y a la recuperación de contexto obsoleto o irrelevante.

**Mejoras Propuestas:**

1.  **Filtrado de Memoria por `task_id`:** Modificar los métodos de búsqueda en `AdvancedMemoryManager` (`retrieve_relevant_context`, `semantic_search`) y en los `*MemoryStore` subyacentes para que acepten un `task_id` opcional. Cuando se proporciona, la búsqueda debe limitarse a los datos asociados con ese `task_id`. Esto requiere que, al almacenar datos en cada `*MemoryStore`, el `task_id` se guarde como un atributo explícito del registro.
    *   **Impacto:** Asegurará que el agente solo acceda a la memoria relevante para la tarea actual, mejorando el aislamiento y la coherencia del comportamiento.
2.  **Políticas de Retención para Memorias a Largo Plazo:** Implementar o reforzar las políticas de retención para `EpisodicMemoryStore`, `SemanticMemoryStore` y `ProceduralMemoryStore`. Esto podría incluir:
    *   **Límites de Capacidad:** Asegurar que estas memorias tengan límites de capacidad razonables, y que cuando se excedan, se utilicen estrategias de reemplazo (e.g., LRU, LFU - Least Frequently Used, o basadas en la importancia/relevancia).
    *   **Limpieza Basada en Tareas:** Desarrollar un proceso que, al eliminar una tarea (a través de `DatabaseService.delete_task`), también elimine los registros asociados en todas las memorias. Esto requiere que cada registro en las memorias tenga una referencia al `task_id` original.

[1] `backend/src/orchestration/task_orchestrator.py` - `self.active_orchestrations`
[2] `backend/src/services/database.py` - `save_task` method
[3] `backend/src/routes/agent_routes.py` - `uuid.uuid4()` usage
[4] `backend/src/services/database.py` - `delete_task` method
[5] `backend/src/services/database.py` - `cleanup_old_data` method
[6] `backend/src/websocket/websocket_manager.py` - `join_room(task_id)`
[7] `backend/src/websocket/websocket_manager.py` - `self.stored_messages`
[8] `backend/src/websocket/websocket_manager.py` - `send_update` method, "Strategy 2"
[9] `backend/src/memory/working_memory_store.py` - `_cleanup_expired` and LRU logic
[10] `backend/src/memory/advanced_memory_manager.py` - `store_experience` and `retrieve_relevant_context`
[11] `backend/src/memory/advanced_memory_manager.py` - `store_experience` method, `task_context` parameter




## 4. Revisión de la Implementación del Plan de Acción y Terminal

La visualización del plan de acción y la terminal son elementos cruciales para la interacción del usuario con el agente, proporcionando transparencia sobre su progreso y actividad. El análisis de los componentes relacionados (`agent_routes.py` y `websocket_manager.py`) ha revelado las causas de las inconsistencias reportadas, particularmente la percepción de que el agente está "PENSANDO" en todas las tareas simultáneamente.

### 4.1. Visualización del Plan de Acción en la UI

El plan de acción se genera y se persiste en la base de datos como parte de los datos de la tarea. La ruta `/execute-step-detailed/<task_id>/<step_id>` en `agent_routes.py` es responsable de ejecutar pasos individuales del plan [12]. La UI probablemente consume estos datos para renderizar el plan de acción y actualizar el estado de cada paso. La actualización del progreso en tiempo real se maneja a través de WebSockets.

**Problema Identificado:**

*   **Dependencia Implícita en el Frontend:** Si bien el backend envía actualizaciones segmentadas por `task_id` (excepto por las emisiones globales ya identificadas), la UI debe estar diseñada para consumir y mostrar estas actualizaciones de manera que cada tarea tenga su propia vista aislada del plan de acción. Si el frontend no maneja correctamente los `task_id` al recibir las actualizaciones, podría haber una superposición visual de estados o planes.

**Mejoras Propuestas:**

1.  **Validación Rigurosa en el Frontend:** Asegurar que el componente de la UI responsable de mostrar el plan de acción solo procese y muestre actualizaciones que correspondan al `task_id` de la tarea actualmente seleccionada por el usuario. Esto implica un filtrado explícito de los mensajes WebSocket recibidos en el lado del cliente, utilizando el `task_id` como clave de filtrado.
2.  **Diseño de Estado de UI por Tarea:** El estado global de la UI no debe contener información de progreso o actividad que no esté directamente asociada a la tarea activa. Cada vista de tarea debe inicializar su propio estado de plan de acción y terminal, y actualizarlo únicamente con los mensajes de WebSocket que contengan su `task_id` correspondiente.

### 4.2. Actualización del Progreso en Tiempo Real y Visualización de Logs

El `WebSocketManager` es el encargado de enviar actualizaciones de progreso y logs al frontend. Métodos como `send_task_progress`, `send_step_started`, `send_step_completed`, `send_step_failed`, y `emit_activity` son utilizados para comunicar el estado de la ejecución [13].

**Problema Identificado:**

*   **Emisiones Globales de Actividad (`emit_activity`):** Como se mencionó en la sección 3.3, la función `emit_activity` en `websocket_manager.py` utiliza `emit_update` con `UpdateType.TASK_PROGRESS` [14]. Aunque `emit_update` intenta emitir a la `room=task_id`, también contiene una "Strategy 2" que emite `UpdateType.TASK_PROGRESS` globalmente [8]. Esta es la causa principal de que el agente se vea "PENSANDO" en todas las tareas, ya que los mensajes de progreso y actividad se transmiten a todos los clientes conectados, independientemente de la tarea que estén visualizando.
*   **Logs Genéricos sin Contexto:** Si los logs generados por el backend no incluyen consistentemente el `task_id` en su formato, o si el `WebSocketManager` no los etiqueta adecuadamente antes de enviarlos, se mezclan en la terminal del frontend, haciendo imposible discernir a qué tarea pertenece cada entrada de log.

**Mejoras Propuestas:**

1.  **Eliminación de Emisiones Globales de Progreso y Logs:** Es imperativo eliminar la "Strategy 2" dentro de `WebSocketManager.send_update` para los tipos `UpdateType.LOG_MESSAGE`, `UpdateType.BROWSER_ACTIVITY`, y `UpdateType.TASK_PROGRESS`. Todas las actualizaciones de progreso y logs deben ser emitidas *únicamente* a la `room` específica del `task_id`. Esto asegurará que solo los clientes suscritos a esa tarea reciban sus actualizaciones de progreso y logs, resolviendo el problema de la "contaminación" visual.
    *   **Acción Específica:** Modificar la línea en `send_update` que dice `if update_type in [UpdateType.LOG_MESSAGE, UpdateType.BROWSER_ACTIVITY, UpdateType.TASK_PROGRESS]: self.socketio.emit('global_task_update', update_data)` para que esta condición sea eliminada o para que la emisión se realice solo a la `room=task_id`.
2.  **Enriquecimiento de Logs con `task_id`:** Asegurar que todos los mensajes de log generados por el sistema incluyan el `task_id` relevante. Esto se puede lograr utilizando un `logging.Filter` personalizado o asegurando que el `TaskContextHolder` (propuesto en la sección 3.1) se utilice para inyectar el `task_id` en los registros de log. De esta manera, incluso si un log se emite globalmente (lo cual se debe evitar), el frontend podría filtrarlo si fuera necesario.
3.  **Gestión de la Terminal en el Frontend:** El componente de la terminal en el frontend debe ser rediseñado para mantener un historial de logs separado para cada `task_id`. Cuando el usuario cambia de tarea, la terminal debe mostrar solo los logs correspondientes a la tarea seleccionada. Esto requiere que el frontend almacene los logs recibidos por `task_id` y los cargue dinámicamente al cambiar de vista.

### 4.3. Causa de que el Agente se vea "PENSANDO" en Todas las Tareas

La causa principal de este comportamiento es la emisión global de mensajes de progreso y actividad a través de WebSockets, como se detalló en la sección anterior. Cuando el `WebSocketManager` emite un `UpdateType.TASK_PROGRESS` o `LOG_MESSAGE` utilizando la "Strategy 2" (emisión global), todos los clientes conectados reciben esta actualización. Si el frontend interpreta cualquier mensaje de progreso o log como una señal de que "el agente está pensando", y no filtra estos mensajes por `task_id`, entonces la UI mostrará erróneamente que todas las tareas están activas o "pensando".

**Mejoras Propuestas:**

1.  **Aplicar las Soluciones de Aislamiento de WebSockets:** La eliminación de las emisiones globales en `WebSocketManager.send_update` (Sección 4.2, Mejora 1) es la solución directa a este problema. Al asegurar que los mensajes de progreso y actividad solo se envíen a la `room` específica de la tarea, cada cliente solo recibirá actualizaciones para la tarea a la que está suscrito, eliminando la contaminación visual.
2.  **Refinar la Lógica de "Pensando" en el Frontend:** El frontend debe tener una lógica clara para determinar cuándo una tarea está "pensando" o activa. Esta lógica debe basarse *únicamente* en los mensajes de progreso y estado recibidos para el `task_id` actualmente seleccionado. Si no se reciben mensajes de progreso para una tarea específica, o si su estado final es `completed` o `failed`, no debe mostrarse como "pensando".

[12] `backend/src/routes/agent_routes.py` - `@agent_bp.route('/execute-step-detailed/<task_id>/<step_id>', methods=['POST'])`
[13] `backend/src/websocket/websocket_manager.py` - `send_task_progress`, `send_step_started`, `send_step_completed`, `send_step_failed`, `emit_activity`
[14] `backend/src/websocket/websocket_manager.py` - `emit_activity` method calling `emit_update` with `UpdateType.TASK_PROGRESS`




## 5. Conclusiones y Recomendaciones Finales

El análisis de la aplicación Mitosis ha revelado que los problemas de aislamiento de tareas, contaminación de contenido y visualización errónea del estado del agente ("PENSANDO" en todas las tareas) se derivan principalmente de una combinación de factores:

1.  **Falta de Propagación Consistente del Contexto de Tarea:** No todos los componentes del backend reciben o utilizan el `task_id` de manera uniforme para segmentar operaciones, especialmente en los módulos de memoria y logging.
2.  **Emisiones Globales de WebSocket:** La emisión de mensajes de progreso y logs a *todos* los clientes conectados, en lugar de solo a la sala específica de la tarea, es la causa directa de la contaminación visual en el frontend.
3.  **Gestión de Memoria y Persistencia:** Aunque existen mecanismos de aislamiento, la falta de filtrado explícito por `task_id` en las operaciones de memoria y la ausencia de políticas de retención de datos más agresivas contribuyen a la acumulación de información y posibles fugas lógicas.

Para abordar estos problemas de manera integral y mantener la UI/UX existente, se proponen las siguientes mejoras, que deben ser implementadas con un enfoque de desarrollo senior, asegurando la robustez y la escalabilidad de la solución:

### 5.1. Instrucciones de Mejora Completas (De Extremo a Extremo)

#### 5.1.1. Aislamiento de Tareas y Propagación de Contexto

**Objetivo:** Asegurar que cada operación en el backend esté intrínsecamente ligada a un `task_id` específico, previniendo la mezcla de datos y logs entre tareas.

1.  **Implementar `TaskContextHolder`:**
    *   **Acción:** Crear un módulo `task_context.py` (o similar) que utilice `contextvars` para almacenar y recuperar el contexto de la tarea actual (`task_id`, `user_id`, `session_id`).
    *   **Ubicación:** `backend/src/utils/task_context.py` (nueva carpeta `utils`).
    *   **Código (Ejemplo):**
        ```python
        # backend/src/utils/task_context.py
        import contextvars
        from typing import Dict, Any

        class OrchestrationContext:
            def __init__(self, task_id: str, user_id: str, session_id: str, **kwargs):
                self.task_id = task_id
                self.user_id = user_id
                self.session_id = session_id
                self.metadata = kwargs

            def to_dict(self):
                return {
                    "task_id": self.task_id,
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    **self.metadata
                }

        current_task_context_var = contextvars.ContextVar(
            'current_task_context', default=None
        )

        def set_current_task_context(context: OrchestrationContext):
            return current_task_context_var.set(context)

        def get_current_task_context() -> OrchestrationContext:
            return current_task_context_var.get()

        def reset_current_task_context(token: contextvars.Token):
            current_task_context_var.reset(token)
        ```
    *   **Integración:**
        *   En `TaskOrchestrator.orchestrate_task` (o donde se inicia la ejecución de una tarea), obtener el `task_id` y crear una instancia de `OrchestrationContext`. Usar `set_current_task_context` al inicio y `reset_current_task_context` en un bloque `finally`.
        *   **Ejemplo en `TaskOrchestrator`:**
            ```python
            # backend/src/orchestration/task_orchestrator.py
            from src.utils.task_context import set_current_task_context, reset_current_task_context, OrchestrationContext
            # ...

            async def orchestrate_task(self, task_id: str, user_id: str, session_id: str, initial_message: str) -> OrchestrationResult:
                # ... (obtener/crear plan)
                context = OrchestrationContext(task_id=task_id, user_id=user_id, session_id=session_id)
                token = set_current_task_context(context)
                try:
                    # ... lógica existente de orquestación ...
                finally:
                    reset_current_task_context(token)
            ```
2.  **Refactorizar Servicios de Memoria:**
    *   **Acción:** Modificar `AdvancedMemoryManager` y todos los `*MemoryStore` (Working, Episodic, Semantic, Procedural) para que todas las operaciones de almacenamiento y recuperación de datos acepten y utilicen el `task_id` (obtenido de `get_current_task_context()`) como un filtro o clave de segmentación.
    *   **Impacto:** Asegurará que las búsquedas de memoria solo devuelvan información relevante para la tarea actual, eliminando la contaminación de contenido entre tareas.
    *   **Ejemplo en `AdvancedMemoryManager`:**
        ```python
        # backend/src/memory/advanced_memory_manager.py
        from src.utils.task_context import get_current_task_context
        # ...

        def store_experience(self, experience: Dict[str, Any]):
            context = get_current_task_context()
            if context: # Asegurarse de que el contexto exista
                experience["task_id"] = context.task_id
            # ... lógica existente para almacenar en los diferentes stores ...
            self.working_memory.add_entry(experience)
            self.episodic_memory.add_entry(experience)
            # ...

        def retrieve_relevant_context(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
            context = get_current_task_context()
            task_id_filter = context.task_id if context else None
            
            # Modificar las llamadas a los stores para incluir el filtro de task_id
            working_mem_results = self.working_memory.get_relevant_entries(query, k, task_id=task_id_filter)
            episodic_mem_results = self.episodic_memory.get_relevant_entries(query, k, task_id=task_id_filter)
            # ... combinar y devolver resultados ...
        ```
    *   **Modificación en `*MemoryStore` (ej. `WorkingMemoryStore`):**
        ```python
        # backend/src/memory/working_memory_store.py
        # ...
        def add_entry(self, entry: Dict[str, Any]):
            # Asegurarse de que el task_id se almacene con la entrada
            if "task_id" not in entry:
                from src.utils.task_context import get_current_task_context
                context = get_current_task_context()
                if context: entry["task_id"] = context.task_id
                else: entry["task_id"] = "global" # Fallback para entradas sin contexto
            self.store[entry["id"]] = {"data": entry, "timestamp": datetime.now(), "access_time": datetime.now()}
            self._cleanup_expired()

        def get_relevant_entries(self, query: str, k: int = 5, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
            relevant_entries = []
            for entry_id, entry_data in self.store.items():
                # Aplicar filtro por task_id si se proporciona
                if task_id and entry_data["data"].get("task_id") != task_id:
                    continue
                # ... lógica existente de relevancia ...
                relevant_entries.append(entry_data["data"])
            return relevant_entries[:k]
        ```

#### 5.1.2. Gestión de WebSockets y Comunicación en Tiempo Real

**Objetivo:** Eliminar la contaminación de contenido en el frontend asegurando que las actualizaciones de progreso y logs sean específicas de la tarea.

1.  **Eliminar Emisiones Globales en `WebSocketManager`:**
    *   **Acción:** Modificar el método `send_update` en `backend/src/websocket/websocket_manager.py` para eliminar la "Strategy 2" que emite mensajes globalmente para `LOG_MESSAGE`, `BROWSER_ACTIVITY`, y `TASK_PROGRESS`.
    *   **Código (Modificación):**
        ```python
        # backend/src/websocket/websocket_manager.py - dentro de send_update
        # ...
        try:
            # Send to all clients in the task room
            self.socketio.emit("task_update", update_data, room=task_id)
            
            # 🔧 ADDITIONAL EMIT STRATEGIES for maximum compatibility (REVISAR Y ELIMINAR/MODIFICAR)
            # Strategy 1: Emit to individual sessions if room fails (mantener si es necesario para compatibilidad)
            if task_id in self.active_connections:
                for session_id in self.active_connections[task_id]:
                    self.socketio.emit("task_update", update_data, room=session_id)
                    logger.info(f"📡 Sent to individual session: {session_id}")
            
            # Strategy 2: Broadcast to all connected clients for critical messages (ELIMINAR ESTE BLOQUE)
            # if update_type in [UpdateType.LOG_MESSAGE, UpdateType.BROWSER_ACTIVITY, UpdateType.TASK_PROGRESS]:
            #     self.socketio.emit("global_task_update", update_data)
            #     logger.info(f"📡 Broadcasted {update_type.value} globally for task {task_id}")
            
            # Strategy 3: Store in session storage for retrieval (mantener si es necesario)
            # ...
        ```
    *   **Impacto:** Esto resolverá directamente el problema de que el agente se vea "PENSANDO" en todas las tareas y la mezcla de logs en la terminal, ya que solo los clientes suscritos a la `room` de la tarea recibirán estas actualizaciones.
2.  **Enriquecimiento de Logs del Backend:**
    *   **Acción:** Implementar un `logging.Filter` personalizado que inyecte el `task_id` (obtenido de `get_current_task_context()`) en cada registro de log. Esto permitirá que, incluso si por alguna razón un log se escapa del aislamiento de WebSocket, el frontend pueda filtrarlo por `task_id`.
    *   **Ubicación:** `backend/src/utils/log_filters.py` (nueva carpeta `utils`).
    *   **Código (Ejemplo):**
        ```python
        # backend/src/utils/log_filters.py
        import logging
        from src.utils.task_context import get_current_task_context

        class TaskContextFilter(logging.Filter):
            def filter(self, record):
                context = get_current_task_context()
                if context:
                    record.task_id = context.task_id
                    record.user_id = context.user_id
                    record.session_id = context.session_id
                else:
                    record.task_id = "N/A"
                    record.user_id = "N/A"
                    record.session_id = "N/A"
                return True
        ```
    *   **Integración:** Añadir este filtro a los handlers de logging en `server.py` o en la configuración de logging.
        ```python
        # backend/server.py (o archivo de configuración de logging)
        import logging
        from src.utils.log_filters import TaskContextFilter

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Añadir el filtro a todos los handlers
        for handler in logger.handlers:
            handler.addFilter(TaskContextFilter())
        ```

#### 5.1.3. Gestión del Ciclo de Vida de Tareas y Consistencia del Estado

**Objetivo:** Mejorar la gestión de tareas, permitiendo una eliminación efectiva y una limpieza automática de datos obsoletos.

1.  **Auditoría de Generación y Propagación de `task_id`:**
    *   **Acción:** Realizar una revisión exhaustiva de todos los puntos donde se crea o se utiliza un `task_id` para asegurar que siempre se genere un `uuid.uuid4()` único al inicio de una nueva tarea y que este se propague consistentemente a todas las funciones y servicios que lo requieran (base de datos, memoria, WebSockets).
    *   **Verificación:** Asegurarse de que no haya lógica que pueda reutilizar `task_id`s antiguos o generar duplicados.
2.  **Implementar Políticas de Retención de Datos Automatizadas:**
    *   **Acción:** Extender la función `cleanup_old_data` en `backend/src/services/database.py` o crear un nuevo servicio de limpieza en segundo plano.
    *   **Funcionalidad:**
        *   Eliminar tareas completadas o fallidas (y sus datos asociados en `conversations`, `files`, `tool_results`, y **todas las memorias**) después de un período configurable (e.g., 30 días). Esto puede ser un cron job o un hilo de limpieza que se ejecute periódicamente.
        *   Asegurarse de que la eliminación de una tarea en `DatabaseService.delete_task` también active la limpieza de los datos asociados en *todas* las memorias (Working, Episodic, Semantic, Procedural). Esto requiere que los registros en las memorias tengan una referencia al `task_id`.
    *   **Impacto:** Reducirá el tamaño de la base de datos, mejorará el rendimiento de las consultas y resolverá la percepción de "tareas que no se pueden borrar" al automatizar su limpieza.

#### 5.1.4. Mejoras en el Frontend (Sin Cambios en UI/UX)

**Objetivo:** Asegurar que el frontend maneje las actualizaciones de manera aislada por tarea, complementando las mejoras del backend.

1.  **Filtrado Riguroso de Mensajes WebSocket:**
    *   **Acción:** En el cliente (JavaScript/TypeScript), modificar el listener de mensajes WebSocket (`socket.on('task_update', ...)`) para que solo procese y actualice la UI si el `task_id` del mensaje recibido coincide con el `task_id` de la tarea actualmente seleccionada en la interfaz de usuario.
    *   **Código (Ejemplo Conceptual en Frontend):**
        ```javascript
        // En el componente de la UI que muestra la tarea activa
        let currentActiveTaskId = null; // Se actualiza cuando el usuario selecciona una tarea

        socket.on('task_update', (message) => {
            if (message.task_id === currentActiveTaskId) {
                // Procesar y actualizar la UI para esta tarea
                // ... (lógica existente para actualizar plan, terminal, etc.)
            } else {
                // Ignorar o loggear para depuración si es necesario
                console.log(`Mensaje para tarea no activa (${message.task_id}), ignorado.`);
            }
        });
        ```
2.  **Gestión de Estado de Terminal por Tarea:**
    *   **Acción:** Implementar un almacenamiento local (e.g., un objeto JavaScript o un store de Redux/Zustand) en el frontend que mantenga un historial de logs y actividades *separado* para cada `task_id`. Cuando el usuario cambia de tarea, la terminal debe cargar y mostrar el historial correspondiente a la tarea seleccionada.
    *   **Impacto:** La terminal mostrará solo los logs relevantes para la tarea activa, eliminando la mezcla de logs de diferentes tareas.

### 5.2. Verificación de Cambios (De Extremo a Extremo)

Después de implementar las mejoras, se recomienda un proceso de verificación riguroso:

1.  **Pruebas Unitarias y de Integración:** Ampliar la cobertura de pruebas para los módulos modificados, especialmente `TaskContextHolder`, `AdvancedMemoryManager`, `*MemoryStore` y `WebSocketManager`. Asegurar que las pruebas de integración validen el flujo completo de una tarea, desde su creación hasta su finalización, verificando el aislamiento de datos y logs.
2.  **Pruebas de Carga y Concurrencia:** Ejecutar múltiples tareas concurrentemente para verificar que el aislamiento se mantiene bajo carga y que no hay regresiones en el rendimiento o la estabilidad.
3.  **Monitoreo de Logs y Base de Datos:** Observar los logs del backend para asegurar que el `task_id` se propaga correctamente y que no hay mensajes de log que se mezclen. Monitorear el tamaño de las colecciones de MongoDB para verificar que las políticas de retención de datos funcionan como se espera.
4.  **Pruebas de Usuario (UAT):** Realizar pruebas con usuarios reales para confirmar que la percepción de "PENSANDO" en todas las tareas ha desaparecido y que la experiencia de usuario es fluida y sin contaminación de contenido.

Al seguir estas instrucciones detalladas, la aplicación Mitosis mejorará significativamente su robustez, escalabilidad y la experiencia del usuario, resolviendo las inconsistencias reportadas sin necesidad de cambios en la UI/UX. Este enfoque prolijo y de extremo a extremo asegura una base sólida para futuras evoluciones del sistema.

---

### Referencias

[1] `backend/src/orchestration/task_orchestrator.py` - `self.active_orchestrations`
[2] `backend/src/services/database.py` - `save_task` method
[3] `backend/src/routes/agent_routes.py` - `uuid.uuid4()` usage
[4] `backend/src/services/database.py` - `delete_task` method
[5] `backend/src/services/database.py` - `cleanup_old_data` method
[6] `backend/src/websocket/websocket_manager.py` - `join_room(task_id)`
[7] `backend/src/websocket/websocket_manager.py` - `self.stored_messages`
[8] `backend/src/websocket/websocket_manager.py` - `send_update` method, "Strategy 2"
[9] `backend/src/memory/working_memory_store.py` - `_cleanup_expired` and LRU logic
[10] `backend/src/memory/advanced_memory_manager.py` - `store_experience` and `retrieve_relevant_context`
[11] `backend/src/memory/advanced_memory_manager.py` - `store_experience` method, `task_context` parameter
[12] `backend/src/routes/agent_routes.py` - `@agent_bp.route(\'/execute-step-detailed/<task_id>/<step_id>\', methods=[\'POST\'])`
[13] `backend/src/websocket/websocket_manager.py` - `send_task_progress`, `send_step_started`, `send_step_completed`, `send_step_failed`, `emit_activity`
[14] `backend/src/websocket/websocket_manager.py` - `emit_activity` method calling `emit_update` with `UpdateType.TASK_PROGRESS`


