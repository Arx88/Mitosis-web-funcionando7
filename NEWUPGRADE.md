## Introducción
Este documento técnico detalla un plan de mejora integral para el agente general actual, abordando las inconsistencias y problemas de funcionalidad identificados. El objetivo es transformar el agente en una entidad autónoma y potente, capaz de procesar tareas de manera eficiente, ejecutar planes de acción de forma autónoma y comunicar el progreso y los resultados de manera clara y técnica al usuario. Se hará especial énfasis en el *porqué* de cada solución y se proporcionarán ejemplos de código concretos para facilitar la implementación por parte del equipo de desarrollo, **sin modificar la interfaz de usuario existente ni duplicar funcionalidades**.

## Problemas Identificados y Análisis Técnico
Durante la revisión del código fuente (`Mitosis-Beta2-main`) y el análisis del comportamiento del agente, se identificaron los siguientes problemas clave:

### 1. Tareas creadas desde el input de bienvenida no se procesan
**Descripción del Problema:** El usuario reporta que las tareas iniciadas desde el campo de entrada de texto en la página de bienvenida no son procesadas por el agente, mientras que las tareas creadas a través del botón "TAREA NUEVA" sí lo son.

**Análisis Técnico:** Este comportamiento sugiere una disparidad en la forma en que el frontend inicia la comunicación con el backend para cada método. Es probable que el input de bienvenida no esté enviando la solicitud al endpoint correcto, o que el formato de los datos enviados sea inconsistente. Dada la estructura del `backend/server.py` y `backend/src/routes/agent_routes.py`, el endpoint principal para la interacción con el agente es `/api/agent/chat` o potencialmente `/api/agent/initialize-task`.

El `server.py` configura las rutas del agente a través de `agent_bp` y las registra bajo `/api/agent/`. La función `chat()` en `agent_routes.py` es el punto de entrada principal para procesar mensajes y generar planes. Si el input de bienvenida no invoca correctamente esta ruta o no proporciona los parámetros esperados (ej. `message` y `context`), la tarea no se iniciará.

**Hipótesis de Causa Raíz:** El frontend asociado al input de bienvenida probablemente utiliza una lógica de envío de datos diferente o un endpoint obsoleto/incorrecto en comparación con el botón "TAREA NUEVA". Esto podría manifestarse como:
*   Un evento JavaScript incorrecto o ausente en el input de bienvenida.
*   Un `fetch` o `XMLHttpRequest` apuntando a una URL incorrecta.
*   Un objeto JSON mal formado o incompleto enviado al backend.

### 2. El agente no ejecuta los pasos del plan de forma autónoma
**Descripción del Problema:** A pesar de que el agente genera un plan de acción detallado, no procede a ejecutar automáticamente cada paso. El usuario debe intervenir manualmente para avanzar en el plan.

**Análisis Técnico:** La revisión de `backend/src/routes/agent_routes.py` revela la intención de implementar la ejecución autónoma. Específicamente, en la función `chat()`, después de la generación del plan (`structured_plan = generate_dynamic_plan_with_ai(message, task_id)`), se encuentra el siguiente bloque de código:

```python
# MODIFICACIÓN: NO ejecutar automáticamente - dejar que el usuario controle la ejecución paso a paso
# execute_plan_with_real_tools(task_id, structured_plan["steps"], message)

# ... (código intermedio)

# 🎯 INICIAR EJECUCIÓN AUTOMÁTICA DESPUÉS DE GENERAR EL PLAN
logger.info(f"🚀 Starting automatic execution for task {task_id}")
try:
    # Llamar internamente al endpoint de ejecución automática
    import threading
    app = current_app._get_current_object()
    
    def auto_execute_with_context():
        with app.app_context():
            logger.info(f"🔄 Auto-executing task {task_id} with {len(structured_plan.get(\'steps\', []))} steps")
            execute_task_steps_sequentially(task_id, structured_plan.get(\'steps\', []))
            logger.info(f"✅ Auto-execution completed for task {task_id}")
    
    execution_thread = threading.Thread(target=auto_execute_with_context)
    execution_thread.daemon = True
    execution_thread.start()
    
    logger.info(f"🎯 Auto-execution thread started for task {task_id}")
    execution_status = \'executing\'  # Estado: ejecutándose automáticamente
    
except Exception as e:
    logger.error(f"❌ Error starting auto-execution for task {task_id}: {e}")
    execution_status = \'plan_ready\'  # Fallback al estado anterior
```

Este fragmento indica que la ejecución autónoma se intenta iniciar en un hilo separado (`threading.Thread`) llamando a `execute_task_steps_sequentially`. Sin embargo, si la ejecución no se percibe como autónoma, las posibles causas son:
*   **Problemas en `execute_task_steps_sequentially`:** La lógica dentro de esta función (ubicada más abajo en `agent_routes.py`) podría no estar ejecutando las herramientas reales o podría estar bloqueada/fallando silenciosamente.
*   **Falta de persistencia del estado de ejecución:** Si el estado de la tarea (`active_task_plans` o la base de datos MongoDB) no se actualiza correctamente durante la ejecución de los pasos, el frontend no reflejará el progreso.
*   **Errores en la inicialización del hilo:** El hilo podría no estar iniciándose correctamente o el `app.app_context()` podría no estar manejando las dependencias de Flask como se espera en un entorno de hilo.

La función `execute_step_real` dentro de `execute_task_steps_sequentially` es la encargada de invocar las herramientas reales. Es crucial que esta función mapee correctamente los tipos de herramientas del plan (`web_search`, `analysis`, `creation`, etc.) a las funciones de `tool_manager.execute_tool()` y que estas herramientas estén correctamente inicializadas y operativas.

### 3. El progreso de la tarea no se muestra en el chat/terminal
**Descripción del Problema:** El usuario no recibe actualizaciones en tiempo real sobre el progreso de la tarea, ni se visualizan los pasos completados o en curso.

**Análisis Técnico:** El código ya incorpora un `websocket_manager` (inicializado en `server.py` y utilizado en `agent_routes.py`) para emitir eventos de progreso. Las funciones `send_websocket_update` y `emit_step_event` son las responsables de esta comunicación. Los tipos de actualización (`UpdateType`) como `STEP_STARTED`, `STEP_COMPLETED`, `TASK_PROGRESS`, `TOOL_EXECUTION_DETAIL`, `TASK_COMPLETED`, y `TASK_FAILED` están definidos y se intentan emitir.

Si el progreso no se muestra, las causas pueden ser:
*   **Conexión WebSocket del Frontend:** El frontend podría no estar estableciendo o manteniendo una conexión WebSocket activa con el backend. Esto podría deberse a problemas de CORS, configuración del cliente WebSocket, o reconexión automática.
*   **Manejo de Eventos en el Frontend:** El código JavaScript del frontend podría no estar escuchando correctamente los eventos emitidos por el backend, o no estar actualizando la interfaz de usuario de manera reactiva a estos eventos.
*   **Frecuencia o Contenido de las Actualizaciones:** Aunque se emiten eventos, la frecuencia o el contenido de los datos enviados podrían no ser suficientes o estar mal formateados para una visualización efectiva en el frontend.

### 4. Los resultados finales no se entregan al usuario de forma clara
**Descripción del Problema:** La entrega de los resultados finales de una tarea completada no es clara o prominente en la interfaz del usuario.

**Análisis Técnico:** La función `generate_clean_response` en `agent_routes.py` es la encargada de construir la respuesta final que se envía al usuario. Esta función ya intenta ser dinámica y considerar la presencia de archivos generados (`files_created`). Sin embargo, la forma en que esta cadena de texto se presenta en el frontend puede no ser óptima.

El problema no reside tanto en la generación del contenido del mensaje (que ya es bastante detallado), sino en cómo el frontend lo renderiza y lo hace accesible. Por ejemplo, si se generan archivos, los enlaces de descarga deben ser clicables y visibles. Si el resultado es un texto largo, debe presentarse de manera legible y no como un bloque de texto plano.

**Hipótesis de Causa Raíz:** La presentación final en el frontend no está capitalizando la información estructurada que `generate_clean_response` ya proporciona. Esto incluye la falta de:
*   Renderizado de Markdown o HTML en el chat para mejorar la legibilidad.
*   Componentes UI específicos para mostrar archivos adjuntos o enlaces de descarga de manera destacada.
*   Un mecanismo para notificar al usuario sobre la finalización de la tarea y la disponibilidad de resultados tangibles.

## Soluciones Propuestas con Ejemplos de Código
Para abordar los problemas identificados, se proponen las siguientes soluciones técnicas, enfocadas en el backend y la comunicación, sin requerir cambios en la UI más allá de la interpretación de los datos recibidos.

### 1. Unificación y Robustecimiento del Flujo de Inicialización de Tareas
**Objetivo:** Asegurar que todas las solicitudes de tareas inicien el mismo flujo de procesamiento en el backend, independientemente de su origen en el frontend.

**Solución Técnica:**
La clave es que el frontend, tanto desde el input de bienvenida como desde el botón "TAREA NUEVA", envíe una solicitud `POST` al mismo endpoint, preferiblemente `/api/agent/chat`, con un cuerpo JSON consistente que contenga la clave `message` (la descripción de la tarea). Si el input de bienvenida no está haciendo esto, la corrección debe hacerse en el código JavaScript del frontend.

**Ejemplo de Código (Frontend - Conceptual, para el equipo de desarrollo):**

```javascript
// Ejemplo conceptual de cómo el frontend debería enviar la tarea
// Esto asume que el input de bienvenida tiene un ID 'welcome-input' y el botón 'new-task-button'

// Función genérica para enviar la tarea
async function sendTaskToAgent(taskMessage) {
    try {
        const response = await fetch('/api/agent/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: taskMessage })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Task initiated:', data);
        // Aquí el frontend debería manejar la respuesta, por ejemplo, mostrando el plan
        // y activando la escucha de WebSockets para el task_id recibido.
    } catch (error) {
        console.error('Error initiating task:', error);
        // Manejo de errores en la UI
    }
}

// Event Listener para el input de bienvenida (ejemplo)
const welcomeInput = document.getElementById('welcome-input');
if (welcomeInput) {
    welcomeInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            const message = welcomeInput.value.trim();
            if (message) {
                sendTaskToAgent(message);
                welcomeInput.value = ''; // Limpiar input
            }
        }
    });
}

// Event Listener para el botón 'TAREA NUEVA' (ejemplo)
const newTaskButton = document.getElementById('new-task-button');
if (newTaskButton) {
    newTaskButton.addEventListener('click', function() {
        // Asumiendo que hay un modal o algún otro input para la nueva tarea
        const taskMessage = prompt('Introduce la descripción de la nueva tarea:');
        if (taskMessage) {
            sendTaskToAgent(taskMessage);
        }
    });
}
```

**Acción en Backend (Verificación/Refuerzo):**
El `agent_routes.py` ya tiene el endpoint `/chat` que maneja el `message`. La clave es asegurar que este endpoint sea el único punto de entrada para iniciar tareas y que la lógica de `generate_unified_ai_plan` se active siempre. No se requiere cambio de código en el backend si el frontend ya está enviando al endpoint correcto con el formato esperado.

### 2. Activación y Mejora de la Ejecución Autónoma del Plan
**Objetivo:** Lograr que el agente ejecute automáticamente los pasos del plan de acción una vez generado, sin intervención manual del usuario.

**Solución Técnica:**
El código ya contiene la infraestructura para la ejecución autónoma mediante un hilo (`threading.Thread`) que llama a `execute_task_steps_sequentially`. El problema es que esta ejecución no se percibe o no se completa. La línea comentada `execute_plan_with_real_tools` en `chat()` es un vestigio de una implementación anterior. La implementación actual utiliza `execute_task_steps_sequentially`.

La función `execute_task_steps_sequentially` es la que debe ser robustecida. Actualmente, esta función llama a `execute_step_internal`, que a su vez llama a `execute_step_real`. La clave es asegurar que `execute_step_real` mapee correctamente las herramientas del plan a las herramientas reales del `tool_manager` y que estas herramientas funcionen sin errores.

**Modificaciones Propuestas (Backend - `backend/src/routes/agent_routes.py`):**

**a) Asegurar la Invocación Correcta de `execute_task_steps_sequentially`:**
Verificar que el hilo se inicie inmediatamente después de la generación del plan en la función `chat()`:

```python
# En agent_routes.py, dentro de la función chat():

# ... (código de generación de plan y respuesta inicial)

# 🎯 INICIAR EJECUCIÓN AUTOMÁTICA DESPUÉS DE GENERAR EL PLAN
logger.info(f"🚀 Starting automatic execution for task {task_id}")
try:
    # Llamar internamente al endpoint de ejecución automática
    import threading
    app = current_app._get_current_object()
    
    def auto_execute_with_context():
        with app.app_context():
            logger.info(f"🔄 Auto-executing task {task_id} with {len(structured_plan.get(\'steps\', []))} steps")
            # Asegurarse de que structured_plan.get('steps', []) contenga los pasos correctos
            execute_task_steps_sequentially(task_id, structured_plan.get(\'steps\', []))
            logger.info(f"✅ Auto-execution completed for task {task_id}")
    
    execution_thread = threading.Thread(target=auto_execute_with_context)
    execution_thread.daemon = True # Permite que el hilo termine con la aplicación principal
    execution_thread.start()
    
    logger.info(f"🎯 Auto-execution thread started for task {task_id}")
    execution_status = \'executing\'  # Estado: ejecutándose automáticamente
    
except Exception as e:
    logger.error(f"❌ Error starting auto-execution for task {task_id}: {e}")
    execution_status = \'plan_ready\'  # Fallback al estado anterior

# ... (resto de la función chat)
```

**b) Robustecer `execute_step_real` y el mapeo de herramientas:**
La función `execute_step_real` es crítica. Debe asegurarse de que cada `tool` definido en el plan (`web_search`, `analysis`, `creation`, etc.) se mapee a una herramienta real y funcional del `tool_manager`. El código actual ya tiene un mapeo, pero es vital que las herramientas (`valencia_bars_tool`, `comprehensive_research`, `file_manager`) estén correctamente implementadas y accesibles.

**Revisión y Mejora de `execute_step_real` (Backend - `backend/src/routes/agent_routes.py`):**

```python
# Dentro de execute_step_real(task_id: str, step_id: str, step: dict):

    tool = step.get(\'tool\', \'general\')
    title = step.get(\'title\', \'Ejecutando paso\')
    description = step.get(\'description\', \'\')
    
    logger.info(f"🔧 Ejecutando REAL TOOL: {tool} para paso: {title}")
    
    # Emitir progreso inicial
    emit_step_event(task_id, \'task_progress\', {
        \'step_id\': step_id,
        \'activity\': f"Iniciando {tool}...",
        \'progress_percentage\': 25,
        \'timestamp\': datetime.now().isoformat()
    })
    
    try:
        tool_manager = get_tool_manager()
        
        if tool_manager and hasattr(tool_manager, \'execute_tool\'):
            tool_params = {}
            mapped_tool = tool # Por defecto, la herramienta es la misma

            # Lógica de mapeo de herramientas (asegurarse de que estas herramientas existan y funcionen)
            if tool == \'web_search\':
                mapped_tool = \'web_search\'
                search_query = extract_search_query_from_message(f"{title} {description}", title) # Usar LLM para query
                tool_params = {
                    \'query\': search_query,
                    \'num_results\': 5
                }
            elif tool == \'analysis\' or tool == \'data_analysis\' or tool == \'synthesis\':
                mapped_tool = \'comprehensive_research\' # Herramienta unificada para investigación/análisis
                tool_params = {
                    \'query\': f"{title}: {description}",
                    \'max_results\': 5,
                    \'include_analysis\': True
                }
            elif tool == \'creation\':
                mapped_tool = \'file_manager\' # Usar file_manager para crear archivos
                filename = f"generated_content_{task_id}_{step_id}.md"
                content_to_create = f"# {title}\n\n## Descripción\n{description}\n\n*Contenido generado por el agente para la tarea: {task_id} - Paso: {step_id}*\n\n"\
                                  f"{{{{GENERATED_CONTENT_PLACEHOLDER}}}}" # Placeholder para contenido real de LLM
                tool_params = {
                    \'action\': \'create\',
                    \'path\': f"/app/backend/static/generated_files/{filename}",
                    \'content\': content_to_create
                }
                # Aquí se necesitaría una llamada a Ollama para generar el contenido real
                # y luego actualizar el archivo. Esto es un punto de mejora clave.
                # Por ahora, el placeholder indica que el contenido es estático.

            elif tool == \'planning\':
                mapped_tool = \'file_manager\'
                filename = f"plan_output_{task_id}_{step_id}.md"
                tool_params = {
                    \'action\': \'create\',
                    \'path\': f"/app/backend/static/generated_files/{filename}",
                    \'content\': f"# Planificación: {title}\n\nDescripción: {description}\n\n*Este es un plan generado automáticamente.*\n"
                }
            elif tool == \'delivery\':
                mapped_tool = \'file_manager\'
                filename = f"delivery_report_{task_id}_{step_id}.md"
                tool_params = {
                    \'action\': \'create\',
                    \'path\': f"/app/backend/static/generated_files/{filename}",
                    \'content\': f"# Informe de Entrega: {title}\n\nDescripción: {description}\n\n*Este es el informe de entrega final.*\n"
                }
            elif tool == \'processing\':
                mapped_tool = \'comprehensive_research\'
                tool_params = {
                    \'query\': f"Process and summarize: {title} {description}",
                    \'max_results\': 3,
                    \'include_analysis\': True
                }
            # Añadir más mapeos según las herramientas disponibles en tool_manager
            # y los tipos de 'tool' que el LLM puede generar en el plan.

            # Manejo especial para la herramienta de bares de Valencia (si existe y es relevante)
            if (\'valencia\' in f"{title} {description}".lower() and 
                any(word in f"{title} {description}".lower() for word in [\'bar\', \'bares\', \'restaurant\', \'local\', \'sitio\'])):
                try:
                    # Asegurarse de que valencia_bars_tool.py esté en src/tools y sea importable
                    import sys
                    sys.path.append(\'/app/backend/src/tools\')
                    from valencia_bars_tool import valencia_bars_tool
                    mapped_tool = \'valencia_bars_tool\'
                    tool_params = {
                        \'query\': f"{title} {description}",
                        \'max_results\': 8
                    }
                    logger.info(f"🍻 VALENCIA BARS DETECTED: Using specialized Valencia bars tool")
                except ImportError:
                    logger.warning("Valencia bars tool not found, falling back to web_search.")
                    mapped_tool = \'web_search\'
                    tool_params = {
                        \'query\': f"{title} {description}",
                        \'max_results\': 5
                    }

            # Ejecutar herramienta real
            logger.info(f"🚀 Executing MAPPED tool: original=\'{tool}\' -> mapped=\'{mapped_tool}\' with params: {tool_params}")
            
            available_tools = list(tool_manager.tools.keys()) if hasattr(tool_manager, \'tools\') else []
            if mapped_tool not in available_tools:
                logger.error(f"❌ TOOL MAPPING ERROR: Tool \'{mapped_tool}\' not found in available tools: {available_tools}")
                raise Exception(f"Tool \'{mapped_tool}\' not available. Available tools: {available_tools}")
            
            tool_result = tool_manager.execute_tool(mapped_tool, tool_params, task_id=task_id)
            
            # Emitir progreso avanzado
            emit_step_event(task_id, \'task_progress\', {
                \'step_id\': step_id,
                \'activity\': f"Procesando resultados de {mapped_tool}...",
                \'progress_percentage\': 90,
                \'timestamp\': datetime.now().isoformat()
            })
            
            logger.info(f"✅ Tool {mapped_tool} executed successfully, result: {str(tool_result)[:200]}...")
            
            emit_step_event(task_id, \'tool_result\', {
                \'step_id\': step_id,
                \'tool\': mapped_tool,
                \'result\': tool_result,
                \'timestamp\': datetime.now().isoformat()
            })
            
        else:
            logger.warning(f"⚠️ Tool manager not available, falling back to simulation for {tool}")
            time.sleep(3)
            emit_step_event(task_id, \'task_progress\', {
                \'step_id\': step_id,
                \'activity\': f"Simulación de {tool} completada (herramientas no disponibles)",
                \'progress_percentage\': 90,
                \'timestamp\': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"❌ Error executing real tool {tool}: {e}")
        emit_step_event(task_id, \'task_progress\', {
            \'step_id\': step_id,
            \'activity\': f"Error en {tool}: {str(e)}, continuando...",
            \'progress_percentage\': 75,
            \'timestamp\': datetime.now().isoformat()
        })
```

**Consideraciones Adicionales para la Ejecución Autónoma:**
*   **Manejo de Errores y Reintentos:** El código ya utiliza `tenacity` en `execute_plan_with_real_tools` (aunque esa función no se usa directamente para la ejecución autónoma). Es crucial que la lógica de reintentos y manejo de excepciones se aplique a nivel de `execute_step_real` para cada invocación de herramienta. Esto significa que las llamadas a `tool_manager.execute_tool` deben estar envueltas en bloques `try-except` robustos.
*   **Validación de Resultados de Pasos:** Después de cada `tool_manager.execute_tool`, se debe validar el `tool_result`. Si el resultado no es el esperado (ej. búsqueda vacía, análisis sin contenido), el agente debe poder decidir si reintentar, usar una estrategia alternativa, o marcar el paso como fallido. La función `validate_step_result` ya existe y debe ser utilizada activamente para esto.

### 3. Implementación de Comunicación en Tiempo Real (WebSockets) para el Progreso
**Objetivo:** Proporcionar actualizaciones en tiempo real del progreso de la tarea al frontend, incluyendo el estado de cada paso y logs detallados.

**Solución Técnica:**
El backend ya emite eventos de WebSocket. El problema es que el frontend no los está consumiendo o renderizando adecuadamente. La solución principal reside en el frontend, pero se puede asegurar que el backend envíe la información más completa posible.

**Verificación y Refuerzo en Backend (`backend/src/routes/agent_routes.py`):**

**a) Asegurar la Emisión de Eventos Completos:**
Revisar todas las llamadas a `emit_step_event` y `send_websocket_update` para asegurarse de que los diccionarios `data` contengan toda la información relevante para el frontend (ej. `step_id`, `title`, `description`, `status`, `progress`, `result_summary`, `error`, `file_created`, `download_url`).

**Ejemplo de Emisión Mejorada (dentro de `execute_plan_with_real_tools` o `execute_task_steps_sequentially`):**

```python
# Cuando un paso inicia:
send_websocket_update(\'step_update\', {
    \'type\': \'step_update\',
    \'step_id\': step[\'id\'],
    \'status\': \'in-progress\',
    \'title\': step[\'title\'],
    \'description\': step[\'description\'],
    \'progress\': (i / len(steps)) * 100, # Progreso general de la tarea
    \'current_step\': i + 1,
    \'total_steps\': len(steps),
    \'timestamp\': datetime.now().isoformat()
})

# Cuando una herramienta se ejecuta (detalle):
send_websocket_update(\'tool_execution_detail\', {
    \'type\': \'tool_execution_detail\',
    \'tool_name\': mapped_tool,
    \'input_params\': tool_params, # Parámetros con los que se llamó la herramienta
    \'message\': f\'🔍 Ejecutando {mapped_tool} para: {title}\',
    \'timestamp\': datetime.now().isoformat()
})

# Cuando un paso finaliza (éxito/falla/advertencia):
send_websocket_update(\'step_update\', {
    \'type\': \'step_update\',
    \'step_id\': step[\'id\'],
    \'status\': websocket_status, # 'completed_success', 'completed_with_warnings', 'failed'
    \'title\': step[\'title\'],
    \'description\': step[\'description\'],
    \'result_summary\': validation_message, # Mensaje de validación o resumen del resultado
    \'execution_time\': step_execution_time,
    \'progress\': ((i + 1) / len(steps)) * 100,
    \'validation_status\': validation_status,
    \'error\': step.get(\'error\', None) # Si hay un error
})

# Cuando la tarea completa:
send_websocket_update(\'task_completed\', {
    \'type\': \'task_completed\',
    \'task_id\': task_id,
    \'status\': \'success\' if final_task_status == "completed_success" else \'completed_with_warnings\',
    \'final_result\': final_dynamic_response, # El mensaje final para el usuario
    \'final_task_status\': final_task_status,
    \'total_steps\': total_steps,
    \'completed_steps\': completed_steps,
    \'failed_steps\': failed_steps,
    \'execution_time\': (datetime.now() - active_task_plans[task_id].get(\'start_time\', datetime.now())).total_seconds(),
    \'message\': f\'🎉 Tarea completada: {completed_steps}/{total_steps} pasos exitosos\',
    \'timestamp\': datetime.now().isoformat()
})
```

**Acción en Frontend (Conceptual, para el equipo de desarrollo):**
El equipo de frontend debe implementar un cliente WebSocket que escuche estos eventos y actualice la UI. Esto implica:
*   **Conexión WebSocket:** Utilizar una librería como `socket.io-client` para establecer y gestionar la conexión.
*   **Manejo de Eventos:** Implementar `socket.on('plan_updated', ...)` , `socket.on('step_update', ...)` , `socket.on('tool_execution_detail', ...)` y `socket.on('task_completed', ...)` para actualizar el estado de la UI.
*   **Renderizado Dinámico:** Utilizar frameworks reactivos (React, Vue, Angular) para renderizar dinámicamente el plan de pasos, el progreso general y los logs detallados.

**Ejemplo de Código (Frontend - Cliente WebSocket conceptual):**

```javascript
// En el componente principal del frontend que maneja las tareas
import { io } from 'socket.io-client';

// ... (estado del componente para el plan, logs, etc.)

useEffect(() => {
    const socket = io('http://localhost:8001'); // Asegurarse que la URL sea correcta

    socket.on('connect', () => {
        console.log('WebSocket connected');
    });

    socket.on('plan_updated', (data) => {
        console.log('Plan Updated:', data);
        // Actualizar el estado del plan en la UI
        setTaskPlan(data.plan.steps);
        setTaskId(data.task_id);
        // ... iniciar visualización del progreso
    });

    socket.on('step_update', (data) => {
        console.log('Step Update:', data);
        // Actualizar el estado de un paso específico en la UI (ej. cambiar color, texto)
        // Actualizar la barra de progreso general
        updateStepStatus(data.step_id, data.status, data.result_summary);
        updateOverallProgress(data.progress);
    });

    socket.on('tool_execution_detail', (data) => {
        console.log('Tool Execution Detail:', data);
        // Añadir este detalle a un panel de logs en la UI
        addLogEntry(data.message, data.level || 'info');
        if (data.file_created && data.download_url) {
            // Mostrar notificación de archivo creado y enlace de descarga
            showFileNotification(data.file_created, data.download_url);
        }
    });

    socket.on('task_completed', (data) => {
        console.log('Task Completed:', data);
        // Mostrar mensaje de tarea completada y el resultado final
        displayFinalResult(data.final_result);
        // Limpiar o resetear el estado de la tarea
    });

    socket.on('task_failed', (data) => {
        console.log('Task Failed:', data);
        // Mostrar mensaje de error y detalles
        displayErrorMessage(data.overall_error || data.message);
    });

    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
    });

    return () => {
        socket.disconnect();
    };
}, []); // Se ejecuta una vez al montar el componente

// Funciones auxiliares para actualizar el estado (ejemplo)
function updateStepStatus(stepId, status, summary) {
    // Lógica para encontrar el paso por stepId y actualizar su estado y resumen
}

function updateOverallProgress(progress) {
    // Lógica para actualizar una barra de progreso global
}

function addLogEntry(message, level) {
    // Lógica para añadir mensajes a un array de logs y renderizarlos
}

function showFileNotification(filename, downloadUrl) {
    // Lógica para mostrar un toast o notificación con el archivo y su enlace
}

function displayFinalResult(result) {
    // Lógica para mostrar el resultado final en un área designada
}

function displayErrorMessage(error) {
    // Lógica para mostrar mensajes de error prominentes
}
```

### 4. Mejora de la Presentación de Resultados Finales y Archivos Generados
**Objetivo:** Presentar los resultados finales de la tarea, incluyendo los archivos generados, de manera clara, accesible y visualmente atractiva para el usuario.

**Solución Técnica:**
La función `generate_clean_response` en `agent_routes.py` ya construye un mensaje final con información sobre archivos. La mejora principal aquí es asegurar que el frontend interprete y renderice este mensaje de manera efectiva, especialmente si contiene Markdown o enlaces.

**Modificaciones Propuestas (Backend - `backend/src/routes/agent_routes.py`):**

**a) Formato de Salida de `generate_clean_response`:**
Aunque el Markdown ya se usa, se puede asegurar que los enlaces de descarga sean explícitos y que la estructura del mensaje sea consistente para que el frontend pueda parsearlo. Se recomienda que `generate_clean_response` devuelva un objeto estructurado (JSON) en lugar de una cadena de texto plana, para que el frontend tenga más control sobre la renderización.

```python
# En agent_routes.py, modificar generate_clean_response para devolver un dict/JSON

def generate_clean_response(ollama_response: str, tool_results: list, task_status: str = "success", 
                          failed_step_title: str = None, error_message: str = None, warnings: list = None) -> dict:
    # ... (lógica existente para determinar clean_response y files_created)

    response_data = {
        "status": task_status,
        "message": clean_response, # El mensaje principal en Markdown
        "files_generated": [],
        "warnings": warnings or [],
        "error": error_message
    }

    for file_info in files_created:
        response_data["files_generated"].append({
            "name": file_info["name"],
            "size": file_info["size"],
            "download_url": file_info["download_url"],
            "type": file_info["type"]
        })
    
    return response_data # Devolver un diccionario
```

**b) Persistencia de Resultados Finales:**
El código ya utiliza `update_task_data` para guardar el `final_result`. Es crucial que este `final_result` contenga el objeto estructurado devuelto por `generate_clean_response` para que pueda ser recuperado y mostrado incluso después de que la sesión de WebSocket termine.

```python
# En agent_routes.py, dentro de execute_plan_with_real_tools, al finalizar la tarea:

# ... (código para generar final_dynamic_response)

# Marcar tarea como completada en persistencia y memoria
task_completion_updates = {
    \'status\': \'completed\',
    \'completed_at\': datetime.now().isoformat(),
    \'final_result\': final_dynamic_response,  # Ahora es un diccionario estructurado
    \'final_task_status\': final_task_status,
    \'completed_steps\': completed_steps,
    \'failed_steps\': failed_steps,
    \'total_steps\': total_steps
}

# Actualizar con TaskManager (persistencia)
update_task_data(task_id, task_completion_updates)
```

**Acción en Frontend (Conceptual, para el equipo de desarrollo):**
El frontend debe ser capaz de interpretar el objeto JSON devuelto por `generate_clean_response` y renderizarlo adecuadamente.

*   **Renderizado de Markdown:** Utilizar una librería de renderizado de Markdown (ej. `marked.js` para React) para mostrar el `response_data.message` de manera legible.
*   **Componentes de Archivos:** Crear componentes UI específicos para listar y permitir la descarga de los archivos en `response_data.files_generated`.
*   **Notificaciones:** Implementar un sistema de notificación (toast, modal) que se active al recibir el evento `task_completed` y muestre un resumen y enlaces directos a los resultados.

**Ejemplo de Código (Frontend - Renderizado de Resultados conceptual):**

```javascript
// En el componente de chat o resultados
import ReactMarkdown from 'react-markdown'; // Ejemplo con React

function TaskResultDisplay({ resultData }) {
    if (!resultData) return null;

    return (
        <div className="task-result-container">
            <div className={`status-badge ${resultData.status}`}>
                {resultData.status === 'completed_success' && '✅ Completado'
                 || resultData.status === 'completed_with_warnings' && '⚠️ Con Advertencias'
                 || resultData.status === 'failed' && '❌ Fallido'}
            </div>
            
            <div className="result-message">
                <ReactMarkdown>{resultData.message}</ReactMarkdown>
            </div>

            {resultData.files_generated && resultData.files_generated.length > 0 && (
                <div className="generated-files">
                    <h3>Archivos Generados:</h3>
                    <ul>
                        {resultData.files_generated.map(file => (
                            <li key={file.name}>
                                <a href={file.download_url} target="_blank" rel="noopener noreferrer">
                                    📁 {file.name} ({file.size} bytes)
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {resultData.warnings && resultData.warnings.length > 0 && (
                <div className="result-warnings">
                    <h4>Advertencias:</h4>
                    <ul>
                        {resultData.warnings.map((warning, index) => (
                            <li key={index}>⚠️ {warning}</li>
                        ))}
                    </ul>
                </div>
            )}

            {resultData.error && (
                <div className="result-error">
                    <h4>Error:</h4>
                    <p>🚨 {resultData.error}</p>
                </div>
            )}
        </div>
    );
}
```

## Resumen de Cambios Clave y Justificación

| Problema Identificado | Solución Propuesta | Justificación Técnica | Impacto Esperado |
| :-------------------- | :----------------- | :-------------------- | :--------------- |
| Tareas desde input de bienvenida no procesadas | Unificación del flujo de inicialización en frontend | Asegura que todas las solicitudes de tarea lleguen al mismo endpoint del backend con formato consistente, eliminando puntos de falla por disparidad de entrada. | Todas las tareas se inician correctamente. |
| Agente no ejecuta pasos autónomamente | Activación y robustecimiento de `execute_task_steps_sequentially` y `execute_step_real` | Habilita la ejecución en segundo plano de los planes generados, utilizando las herramientas reales del `tool_manager` y mejorando el manejo de errores. | El agente procesa tareas de forma completamente autónoma. |
| Progreso no visible en chat/terminal | Verificación de emisión de eventos WebSocket y mejora de datos enviados | Asegura que el backend envíe información granular y completa sobre el estado de la tarea y los pasos, permitiendo al frontend una visualización detallada. | El usuario ve el progreso en tiempo real, incluyendo logs de herramientas y estado de pasos. |
| Resultados finales no claros | `generate_clean_response` devuelve JSON estructurado; frontend renderiza Markdown y componentes de archivos | Proporciona al frontend datos estructurados para una presentación rica y accesible de los resultados, incluyendo enlaces de descarga explícitos y notificaciones. | Los resultados son claros, accesibles y los archivos generados son fáciles de encontrar y descargar. |

## Conclusión
La implementación de este plan de mejora transformará el agente general en una herramienta significativamente más potente, autónoma y fácil de usar. Al abordar los problemas de inicialización de tareas, ejecución autónoma, comunicación de progreso y presentación de resultados, se logrará un flujo de trabajo más eficiente y una experiencia de usuario superior, alineada con las capacidades de un agente de IA avanzado. Las soluciones propuestas se centran en optimizar el backend y la comunicación, sin requerir cambios fundamentales en la estructura de la UI, sino mejorando cómo la UI consume y presenta la información ya disponible o fácilmente generable. Este enfoque garantiza una mejora sustancial con una inversión de desarrollo eficiente.

**Autor:** Manus AI
**Fecha:** 22 de Julio de 2025


