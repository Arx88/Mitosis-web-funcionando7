# Informe Detallado de Mejoras para el Backend del Agente Mitosis V5-beta

## Introducción

Este informe se centra en proporcionar un análisis técnico y recomendaciones precisas para fortalecer el backend del agente Mitosis V5-beta, con el objetivo de mejorar su robustez, transparencia y capacidad para manejar tareas complejas de manera autónoma, acercándolo a las capacidades de un agente general como Manus. Las observaciones se basan en la interacción directa con la aplicación proporcionada y en la comprensión de su arquitectura subyacente. Se evitará la referencia directa a documentos previos, enfocándose en soluciones concretas para los problemas identificados en el funcionamiento del agente.

El análisis se estructura en torno a los componentes clave del backend, identificando las áreas donde la lógica actual presenta fragilidades o limitaciones, y proponiendo modificaciones específicas para optimizar el rendimiento y la experiencia del usuario final. La meta es transformar el agente Mitosis V5-beta en una plataforma más fiable y eficiente, capaz de ejecutar flujos de trabajo complejos con mayor autonomía y ofrecer una retroalimentación clara y en tiempo real.

## 1. Detección de Intención y Gestión de Flujos

El agente Mitosis V5-beta actualmente utiliza una lógica heurística para diferenciar entre conversaciones casuales y solicitudes de tareas. Esta aproximación, basada en la longitud del mensaje y la coincidencia de patrones, es propensa a errores, llevando a que interacciones simples activen flujos de trabajo complejos y innecesarios. Para un agente robusto, la clasificación de intención debe ser precisa y adaptable.

### Problema Identificado:

La función encargada de determinar si una conversación es casual o una tarea (ubicada en `backend/src/routes/agent_routes.py`) se basa en reglas rígidas. Por ejemplo, un saludo corto puede ser interpretado como una tarea, lo que resulta en la generación de un plan de acción y la activación del monitor de ejecución, elementos que no son pertinentes para una interacción casual. Esto no solo consume recursos innecesariamente, sino que también confunde al usuario, quien espera una respuesta conversacional simple y no un proceso de tarea.

### Solución Propuesta: Clasificación de Intención Basada en LLM

Para mejorar la precisión y la flexibilidad, se recomienda reemplazar la lógica heurística por un clasificador de intención impulsado por el propio modelo de lenguaje (LLM) que el agente ya utiliza (Ollama). Esto permitirá una interpretación más matizada de la intención del usuario.

**Implementación en `backend/src/routes/agent_routes.py`:**

1.  **Modificación de `is_casual_conversation`:**
    *   Esta función debería ser reescrita para interactuar con el `ollama_service`.
    *   Se enviaría el mensaje del usuario a Ollama con un prompt específico que le pida clasificar la intención. El prompt debe ser claro y solicitar una respuesta en un formato estructurado (ej., JSON) para facilitar el parseo.

    ```python
    # Ejemplo de prompt para Ollama (conceptual)
    intent_prompt = f"""
    Clasifica la siguiente frase del usuario en una de las siguientes categorías: 'casual', 'tarea_investigacion', 'tarea_creacion', 'tarea_analisis', 'otro'.
    Responde SOLO con un objeto JSON con la clave 'intent'.

    Frase: "{message}"

    Ejemplo de respuesta casual: {{"intent": "casual"}}
    Ejemplo de respuesta tarea: {{"intent": "tarea_investigacion"}}
    """
    # ... (llamada a ollama_service.generate_response con este prompt)
    ```

2.  **Manejo de la Respuesta de Ollama:**
    *   El backend debe parsear la respuesta JSON de Ollama para extraer la intención. Es crucial implementar un manejo robusto de errores para el parseo JSON, incluyendo reintentos si el formato inicial es incorrecto.
    *   Basado en la intención clasificada, el agente puede entonces decidir si procede con un flujo de conversación casual o inicia un proceso de planificación y ejecución de tareas.

3.  **Transición de Flujo Condicional:**
    *   Si la intención es `casual`, el agente debería generar una respuesta conversacional simple y no activar el "PLAN DE ACCIÓN" ni el "COMPUTADOR".
    *   Si la intención es una `tarea`, entonces se procede con la generación del plan y la activación de los monitores. Esto asegura que la UI solo muestre elementos de tarea cuando sean relevantes.

### Beneficios:

*   **Precisión Mejorada:** El LLM es mucho más capaz de entender el contexto y la semántica de la intención del usuario que las reglas heurísticas.
*   **Experiencia de Usuario Coherente:** El agente responderá de manera apropiada a cada tipo de interacción, evitando la activación innecesaria de flujos complejos.
*   **Optimización de Recursos:** Se evita la ejecución de lógica de planificación y monitoreo para conversaciones casuales, reduciendo la carga del sistema.



## 2. Generación de Plan y Robustez

La generación de un plan de acción es el corazón de la capacidad de un agente para abordar tareas complejas. En Mitosis V5-beta, este proceso depende críticamente de la capacidad del modelo de lenguaje (Ollama) para producir una salida JSON perfectamente formateada. Cualquier desviación de este formato ideal conduce a un fallo en la planificación y a la activación de un plan de contingencia genérico, lo que degrada significativamente la inteligencia del agente.

### Problema Identificado:

La función `generate_dynamic_plan_with_ai` (en `backend/src/routes/agent_routes.py`) es vulnerable a errores de formato JSON en la respuesta de Ollama. Si la respuesta no es un JSON válido, el sistema recurre a `generate_fallback_plan`. Además, la respuesta inicial del endpoint `/api/agent/chat` incluye un `execution_status: 'completed'` y el `structured_plan` inmediatamente después de la generación del plan, lo cual es engañoso, ya que la ejecución real de los pasos aún no ha comenzado o está en sus primeras etapas. Esta falta de transparencia en el estado del plan afecta la credibilidad del agente.

### Solución Propuesta: Robustecer el Parseo JSON y la Comunicación del Estado del Plan

Para asegurar que el agente siempre opere con planes de alta calidad y comunique su estado de manera precisa, se deben implementar las siguientes mejoras:

**Implementación en `backend/src/routes/agent_routes.py` y `ollama_service.py`:**

1.  **Bucle de Reintento para la Generación de JSON:**
    *   Modificar `generate_dynamic_plan_with_ai` para incluir un mecanismo de reintento. Si el primer intento de Ollama no produce un JSON válido, se debe enviar un prompt de seguimiento a Ollama pidiéndole que corrija el formato. Esto puede implicar un prompt como: "El JSON anterior no fue válido. Por favor, corrige el formato y asegúrate de que sea un JSON válido según el esquema proporcionado."
    *   Se pueden establecer un número máximo de reintentos (ej., 2-3) antes de recurrir al `fallback_plan`.

2.  **Validación de Esquemas JSON:**
    *   Utilizar una librería de validación de esquemas JSON (como `jsonschema`) para validar la estructura del plan generado por Ollama. Esto va más allá de la simple validez sintáctica del JSON; asegura que el JSON cumpla con el esquema esperado (ej., que contenga las claves `task_type`, `complexity`, `steps`, y que cada paso tenga `id`, `title`, `description`, `tool`, etc.).
    *   Si la validación falla, se puede retroalimentar a Ollama con el error específico del esquema, lo que le permite corregir la estructura del plan de manera más efectiva.

3.  **Manejo Explícito de Fallback y Notificación:**
    *   Cuando `generate_fallback_plan` sea invocado, el backend debe registrar explícitamente esta situación (ej., en los logs) y, crucialmente, notificar al frontend. Esto se puede hacer añadiendo un campo al JSON de respuesta del endpoint `/api/agent/chat` (ej., `"plan_source": "fallback"` o `"warning": "Plan generado por contingencia"`).
    *   El frontend, al recibir esta información, puede mostrar un indicador discreto al usuario (ej., un pequeño icono de advertencia junto al "PLAN DE ACCIÓN" o un mensaje en cursiva) que indique que el plan actual es un plan de contingencia y que la precisión o el detalle pueden variar.

4.  **Comunicación Precisa del Estado de Ejecución Inicial:**
    *   Modificar la respuesta del endpoint `/api/agent/chat` para que el `execution_status` refleje el estado real. En lugar de `"completed"`, debería ser `"plan_generated"` o `"execution_pending"`.
    *   La UI debe interpretar este estado para mostrar un mensaje apropiado (ej., "Plan de acción generado. El agente está preparando la ejecución...") en lugar de dar la impresión de que la tarea ya está finalizada.

### Beneficios:

*   **Planes de Mayor Calidad:** El agente generará planes más precisos y útiles, incluso frente a respuestas imperfectas de Ollama.
*   **Transparencia Mejorada:** El usuario siempre sabrá si el plan es generado por IA o por contingencia, y el estado real de la tarea será comunicado desde el inicio.
*   **Reducción de Frustración:** Se evitan las expectativas erróneas sobre la finalización de la tarea, mejorando la experiencia general del usuario.



## 3. Ejecución del Plan y Retroalimentación en Tiempo Real

Uno de los aspectos más críticos para la experiencia de usuario en un agente autónomo es la visibilidad del progreso de la tarea. Actualmente, el agente Mitosis V5-beta ejecuta los planes en segundo plano, pero la retroalimentación en la interfaz de usuario es limitada, creando una "caja negra" donde el usuario no puede seguir el avance de la tarea ni identificar posibles problemas.

### Problema Identificado:

La función `execute_plan_with_real_tools` (en `backend/src/routes/agent_routes.py`) se ejecuta en un hilo separado, lo cual es una buena práctica para no bloquear la API. Sin embargo, la comunicación del progreso y los resultados de la ejecución al frontend es deficiente. El "COMPUTADOR" (Monitor de Ejecución) no muestra logs detallados ni el progreso de las herramientas en tiempo real. Los estados de los pasos en el "PLAN DE ACCIÓN" no se actualizan dinámicamente sin un polling constante por parte del frontend, lo que genera latencia y una experiencia de usuario estática. Si un paso falla, la información del error no se transmite de manera prominente al usuario.

### Solución Propuesta: Implementación de WebSockets para Comunicación en Tiempo Real

La solución fundamental para transformar la experiencia de usuario y la transparencia del agente es la implementación de WebSockets para la comunicación en tiempo real entre el backend y el frontend. El proyecto ya incluye un módulo `websocket.websocket_manager`, lo que facilita esta integración.

**Implementación en `backend/src/routes/agent_routes.py` (dentro de `execute_plan_with_real_tools`):**

1.  **Actualizaciones de Estado de Pasos en Tiempo Real:**
    *   Cada vez que el estado de un paso cambia (inicia, progresa, completa, falla), se debe enviar un mensaje WebSocket al frontend. Esto permitirá que la sección "PLAN DE ACCIÓN" de la UI se actualice dinámicamente, mostrando el progreso real de cada paso.

    ```python
    # En execute_plan_with_real_tools, dentro del bucle de pasos, después de actualizar el estado:
    from websocket.websocket_manager import WebSocketManager
    ws_manager = WebSocketManager.get_instance()
    ws_manager.send_message(task_id, {
        'type': 'step_update',
        'step_id': step['id'],
        'status': step['status'], # 'in-progress', 'completed', 'failed'
        'title': step['title'],
        'description': step['description'],
        'result_summary': step_result.get('summary') if step_result else None, # Resumen conciso del resultado del paso
        'error': step.get('error') # Mensaje de error si el paso falló
    })
    ```

2.  **Logs Detallados en Tiempo Real para el Monitor ("COMPUTADOR"):**
    *   Cualquier mensaje de log relevante (INFO, ERROR) generado durante la ejecución de `execute_plan_with_real_tools` o las herramientas invocadas, debe ser enviado al frontend a través de WebSockets. Esto convertirá el "COMPUTADOR" en una consola de depuración y monitoreo en vivo.

    ```python
    # En execute_plan_with_real_tools, después de cada logger.info/error:
    ws_manager.send_message(task_id, {
        'type': 'log_message',
        'level': 'info' if level == logging.INFO else 'error',
        'message': 'Mensaje del log aquí',
        'timestamp': datetime.now().isoformat()
    })
    ```

3.  **Detalles de Ejecución de Herramientas:**
    *   Cuando una herramienta específica (ej., `web_search`, `analysis`, `creation`) es invocada y finaliza, se debe enviar un mensaje WebSocket con detalles sobre su ejecución, incluyendo los parámetros de entrada y un resumen de los resultados o errores.

    ```python
    # En execute_plan_with_real_tools, después de la ejecución de una herramienta:
    ws_manager.send_message(task_id, {
        'type': 'tool_execution_detail',
        'tool_name': tool_name,
        'input_params': tool_input_params, # Parámetros con los que se llamó a la herramienta
        'output_summary': tool_output_summary, # Resumen conciso del resultado de la herramienta
        'error': tool_error_message # Mensaje de error si la herramienta falló
    })
    ```

4.  **Notificación de Finalización del Plan:**
    *   Una vez que `execute_plan_with_real_tools` ha terminado completamente (ya sea con éxito o con un fallo general de la tarea), debe enviar un mensaje final al frontend indicando la conclusión de la tarea y el resultado final.

    ```python
    # Al final de execute_plan_with_real_tools:
    ws_manager.send_message(task_id, {
        'type': 'task_completed',
        'task_id': task_id,
        'status': 'success' if final_result else 'failed',
        'final_result': final_result, # El resultado consolidado de la tarea
        'overall_error': overall_error # Error general de la tarea si falló
    })
    ```

### Beneficios:

*   **Transparencia Total:** El usuario tendrá visibilidad completa del proceso interno del agente, desde la planificación hasta la ejecución de cada herramienta.
*   **Experiencia de Usuario Dinámica:** La UI se actualizará en tiempo real, proporcionando una sensación de interactividad y progreso constante.
*   **Depuración Simplificada:** Los logs detallados y los mensajes de error en tiempo real facilitarán la identificación y resolución de problemas, tanto para el usuario como para los desarrolladores.
*   **Confianza del Usuario:** La capacidad de ver lo que el agente está haciendo en cada momento aumenta la confianza en su funcionamiento y en su capacidad para completar tareas complejas.



## 4. Servicio Ollama y Extracción de Query

El servicio Ollama es el motor de inteligencia del agente Mitosis V5-beta, responsable de la generación de planes, análisis y creación de contenido. La fiabilidad de este servicio y la calidad de las interacciones con él son cruciales para el rendimiento general del agente. Actualmente, existen oportunidades para mejorar el parseo de sus respuestas y la eficacia de las consultas generadas para las herramientas.

### Problema Identificado:

La función `_parse_response` en `ollama_service.py` busca bloques JSON específicos (````json { ... } ````). Si Ollama se desvía ligeramente de este formato, el parseo fallará, incluso si la intención de la respuesta es correcta. Esto puede llevar a que el agente no pueda interpretar correctamente las instrucciones o datos proporcionados por el LLM. Además, la función `extract_search_query_from_message` utilizada para herramientas como `web_search` es muy básica, lo que puede resultar en consultas de búsqueda ineficaces y, consecuentemente, en resultados de baja calidad para el usuario.

### Solución Propuesta: Robustecer el Parseo de Ollama y Optimizar la Generación de Consultas

Para asegurar que el agente aproveche al máximo la inteligencia de Ollama y realice búsquedas más precisas, se deben implementar las siguientes mejoras:

**Implementación en `backend/src/services/ollama_service.py` y `backend/src/routes/agent_routes.py`:**

1.  **Parseo Robusto de Respuestas de Ollama:**
    *   Modificar la función `_parse_response` para que sea más tolerante a variaciones en el formato de salida de Ollama. En lugar de depender estrictamente de los bloques ````json ````, se pueden utilizar librerías más avanzadas para la extracción de JSON de texto no estructurado (ej., `json5` o enfoques basados en expresiones regulares más flexibles que busquen el primer objeto JSON válido en la respuesta).
    *   Implementar un mecanismo de reintento o corrección automática. Si el parseo inicial falla, se podría intentar una segunda pasada con una lógica de extracción más permisiva, o incluso enviar un prompt de seguimiento a Ollama pidiéndole que "limpie" su respuesta o la reformatee.

2.  **Extracción de Query Mejorada para Herramientas (LLM-driven):**
    *   La función `extract_search_query_from_message` debe ser reemplazada o mejorada para utilizar el LLM de Ollama. En lugar de extraer palabras clave heurísticamente, el LLM puede analizar el mensaje original del usuario y el contexto del paso del plan para generar consultas de búsqueda optimizadas.
    *   Se puede diseñar un prompt específico para Ollama que le pida generar 3-5 palabras clave o frases de búsqueda relevantes, o incluso una consulta de búsqueda completa, basándose en la descripción del paso de la tarea.

    ```python
    # Ejemplo de prompt para Ollama para generar consultas de búsqueda (conceptual)
    search_query_prompt = f"""
    Genera 3-5 palabras clave de búsqueda para la siguiente tarea, enfocándote en obtener información relevante y actualizada.
    Responde SOLO con una lista de palabras clave separadas por comas.

    Tarea: "{task_step_description}"

    Ejemplo: "inteligencia artificial, avances recientes, IA 2024, machine learning, deep learning"
    """
    # ... (llamada a ollama_service.generate_response con este prompt y uso de las palabras clave generadas)
    ```

### Beneficios:

*   **Mayor Fiabilidad:** El agente será más resistente a las variaciones en la salida de Ollama, asegurando que la información crítica sea siempre procesada correctamente.
*   **Resultados Más Precisos:** Las consultas de búsqueda generadas por el LLM serán más inteligentes y contextualmente relevantes, lo que conducirá a mejores resultados de las herramientas y, en última instancia, a una mayor calidad en los resúmenes o soluciones entregadas al usuario.
*   **Optimización del Rendimiento:** Al obtener información más precisa desde el principio, se reduce la necesidad de pasos de refinamiento o reintentos, mejorando la eficiencia general del agente.



## 5. Persistencia del Estado de Tareas

La gestión del estado de las tareas es fundamental para la fiabilidad y la experiencia de usuario de un agente autónomo. Si el estado de una tarea se pierde debido a un reinicio del backend o a un fallo inesperado, el usuario pierde todo el progreso, lo que resulta en una experiencia frustrante y una pérdida de confianza en el sistema.

### Problema Identificado:

Actualmente, el agente Mitosis V5-beta utiliza un diccionario en memoria (`active_task_plans`) para almacenar el estado de las tareas en curso. Esta aproximación es volátil: cualquier reinicio del servidor (ya sea intencional para una actualización o no intencional debido a un fallo) resulta en la pérdida completa del progreso de todas las tareas activas. Esto impide que el agente pueda retomar una tarea donde la dejó y limita su capacidad para manejar flujos de trabajo de larga duración o para ofrecer un historial de tareas fiable.

### Solución Propuesta: Migración a Persistencia en Base de Datos

Para garantizar la resiliencia y la capacidad de recuperación de las tareas, el estado de las tareas debe ser persistido en una base de datos. Dado que el proyecto ya utiliza MongoDB, esta es la solución más lógica y eficiente.

**Implementación en `backend/src/routes/agent_routes.py` y `backend/src/services/mongodb_service.py`:**

1.  **Centralización de la Gestión de Tareas:**
    *   Crear una clase o módulo específico (ej., `task_manager.py`) que encapsule toda la lógica de creación, actualización y recuperación de tareas. Este módulo interactuaría directamente con `mongodb_service`.
    *   La variable global `active_task_plans` debe ser eliminada o, en su lugar, utilizada como un caché de corta duración para reducir la latencia de las operaciones de base de datos, pero la fuente de verdad siempre debe ser la base de datos.

2.  **Actualización de Operaciones CRUD para Tareas:**
    *   Todas las operaciones que actualmente modifican `active_task_plans` (ej., la creación de un nuevo plan, la actualización del estado de un paso, el registro de resultados intermedios, el registro de errores) deben ser reescritas para interactuar con MongoDB.
    *   Esto implica modificar las funciones dentro de `agent_routes.py` (como `execute_plan_with_real_tools`, `update_task_progress`, `update_task_time`) para que persistan los cambios en la base de datos.

    ```python
    # Ejemplo conceptual de cómo se actualizaría un paso en la base de datos
    # en lugar de en active_task_plans en memoria
    # En execute_plan_with_real_tools, después de actualizar el estado del paso:
    from services.mongodb_service import MongoDBService
    db_service = MongoDBService.get_instance()
    db_service.update_task_step_status(task_id, step_id, new_status, result_summary=result, error=error)
    ```

3.  **Recuperación de Tareas al Inicio:**
    *   Al iniciar el backend, el sistema debería consultar la base de datos para identificar tareas que quedaron incompletas (ej., con estado `in-progress` o `pending`) y ofrecer la opción de retomarlas. Esto puede ser útil para tareas de larga duración.

4.  **Historial de Tareas:**
    *   La persistencia en la base de datos permitirá construir un historial completo de todas las tareas ejecutadas por el agente, incluyendo sus planes, resultados y cualquier error. Esto es invaluable para el análisis de rendimiento, la depuración y para que el usuario pueda revisar trabajos anteriores.
    *   Se pueden crear nuevos endpoints en `agent_routes.py` (ej., `/api/agent/tasks/history`, `/api/agent/tasks/<task_id>`) para que el frontend pueda acceder a este historial.

### Beneficios:

*   **Resiliencia:** Las tareas no se perderán si el backend se reinicia, lo que mejora drásticamente la fiabilidad del agente.
*   **Capacidad de Recuperación:** El agente podrá retomar tareas incompletas, lo que es crucial para flujos de trabajo de larga duración.
*   **Historial Completo:** Se dispondrá de un registro detallado de todas las interacciones y tareas, facilitando la depuración, el análisis y la mejora continua del agente.
*   **Mejora de la UX:** El usuario tendrá la confianza de que su trabajo no se perderá y podrá acceder a un historial completo de sus interacciones con el agente.



## 6. Manejo de Errores y Resiliencia

Un agente robusto no solo ejecuta tareas, sino que también maneja los errores de manera elegante, se recupera de fallos y proporciona retroalimentación clara al usuario cuando surgen problemas. El agente Mitosis V5-beta tiene oportunidades significativas para mejorar su resiliencia y la forma en que comunica los errores.

### Problema Identificado:

Actualmente, cuando una herramienta falla durante la ejecución de un paso del plan, el error se registra internamente y el paso se marca como `failed`. Sin embargo, esta información no se transmite de manera prominente al usuario en la interfaz. La falta de un mecanismo de reintento o de una estrategia de fallback clara para las herramientas que fallan puede llevar a que la tarea completa se detenga o produzca resultados incompletos sin una explicación adecuada al usuario. Además, la respuesta final del agente puede ser genérica, incluso si la tarea ha fallado, lo que confunde al usuario sobre el éxito o fracaso real de su solicitud.

### Solución Propuesta: Estrategias de Reintento, Fallback y Comunicación de Errores

Para mejorar la robustez y la transparencia del agente, se deben implementar estrategias proactivas de manejo de errores y una comunicación clara de los mismos.

**Implementación en `backend/src/routes/agent_routes.py` y `backend/src/services/ollama_service.py`:**

1.  **Reintentos con Retroceso Exponencial para Llamadas a Herramientas:**
    *   Modificar la lógica de ejecución de herramientas dentro de `execute_plan_with_real_tools` para incluir reintentos automáticos cuando una herramienta falla. Utilizar una estrategia de retroceso exponencial (ej., esperar 1 segundo, luego 2, luego 4, etc.) para evitar sobrecargar el servicio que está fallando.
    *   Establecer un número máximo de reintentos (ej., 3-5). Si la herramienta sigue fallando después de los reintentos, entonces se considera un fallo definitivo para ese paso.

    ```python
    # Ejemplo conceptual de reintento para la ejecución de una herramienta
    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def execute_tool_with_retries(tool_name, tool_params):
        # Lógica actual de ejecución de la herramienta
        # Si hay un error, lanzar una excepción
        pass

    # Dentro de execute_plan_with_real_tools:
    try:
        step_result = execute_tool_with_retries(step["tool"], tool_input)
        step["status"] = "completed"
        # ... enviar actualización WebSocket ...
    except Exception as e:
        step["status"] = "failed"
        step["error"] = str(e)
        # ... enviar actualización WebSocket con el error ...
    ```

2.  **Estrategias de Fallback para Herramientas Críticas:**
    *   Para herramientas críticas (ej., `web_search`), si la herramienta principal falla persistentemente, el agente debería intentar una herramienta alternativa si está disponible (ej., si `tavily-python` falla, intentar `duckduckgo-search`).
    *   Esta lógica de fallback debe ser configurable y, si se utiliza, debe ser comunicada al usuario a través del monitor de ejecución.

3.  **Comunicación de Errores Detallada al Frontend:**
    *   Cuando un paso falla, el mensaje WebSocket enviado al frontend (`step_update`) debe incluir el mensaje de error completo y, si es posible, una sugerencia sobre la causa o cómo el usuario podría reformular la solicitud.
    *   El "COMPUTADOR" en la UI debe ser capaz de mostrar estos mensajes de error de manera prominente (ej., en texto rojo, con un icono de advertencia), no solo como un log discreto.

4.  **Respuesta Final Condicional y Dinámica:**
    *   La función `generate_clean_response` (o la lógica que genera la respuesta final al usuario) debe ser modificada para reflejar el resultado real de la tarea. Si la tarea falló (ej., porque un paso crítico no pudo completarse incluso después de reintentos), la respuesta final debe explicar claramente el fallo, los pasos que se intentaron y, si es posible, sugerir al usuario cómo proceder.
    *   Si la tarea se completó con advertencias (ej., algunos pasos secundarios fallaron pero la tarea principal se logró), la respuesta final debe mencionarlo.

    ```python
    # Ejemplo conceptual de respuesta final basada en el estado de la tarea
    if task_status == "completed_success":
        final_message = f"¡Tarea completada con éxito! Aquí tienes el resumen: {final_result}"
    elif task_status == "completed_with_warnings":
        final_message = f"Tarea completada con algunas advertencias. {final_result}. Detalles en el monitor."
    elif task_status == "failed":
        final_message = f"Lo siento, la tarea no pudo completarse debido a un error en el paso '{failed_step_title}': {error_message}. Por favor, revisa el monitor para más detalles o intenta reformular tu solicitud."
    ```

### Beneficios:

*   **Mayor Robustez:** El agente será más capaz de superar fallos temporales o problemas con herramientas externas.
*   **Transparencia en Errores:** El usuario será informado de manera clara y oportuna sobre cualquier problema, lo que reduce la frustración y permite una intervención informada.
*   **Mejora de la UX:** Una experiencia más fiable y con retroalimentación clara, incluso en caso de fallo, aumenta la confianza del usuario en el agente.

