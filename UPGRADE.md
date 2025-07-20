Introducción

Este informe aborda los problemas críticos identificados en el agente Mitosis, específicamente su incapacidad para concretar tareas de manera efectiva y la generación de planes de acción genéricos. El objetivo es proporcionar un diagnóstico exhaustivo, explicar las causas raíz y proponer soluciones claras y accionables para el equipo de desarrollo. Se detallará el flujo funcional deseado del agente, cómo se integrarán las nuevas funcionalidades en la interfaz de usuario (UI) existente, y se ofrecerán recomendaciones para una implementación robusta y sin conflictos.

La problemática actual del agente Mitosis se resume en dos puntos principales:

1.
Planes Genéricos: Los planes de acción generados por el agente carecen de especificidad y adaptabilidad a la tarea solicitada, recurriendo a una estructura predefinida que no refleja un análisis profundo ni una estrategia personalizada.

2.
Falta de Concreción en la Ejecución: El agente "dice" que realiza las tareas y avanza en sus fases, pero no ejecuta acciones reales ni produce resultados tangibles, lo que lleva a una experiencia de usuario frustrante y a la percepción de que el agente no es funcional.

Estos problemas no solo afectan la eficacia del agente, sino que también socavan la confianza del usuario en el sistema. La solución propuesta se centra en mejorar la inteligencia del agente en la planificación, establecer un mecanismo robusto para la ejecución real de tareas mediante la invocación de herramientas, y asegurar una retroalimentación clara y verificable en la UI.

El informe se estructura de la siguiente manera:

•
Sección 1: Diagnóstico y Soluciones Detalladas por Problema

•
Problema 1: Generación de Planes Genéricos

•
Problema 2: Falta de Concreción en la Ejecución de Tareas

•
Problema 3: Integración Limitada con Herramientas

•
Problema 4: Dependencia Excesiva en la Generación de Texto del LLM para el Control de Flujo



•
Sección 2: Flujo Funcional Deseado y Experiencia de Usuario

•
Visión General del Flujo

•
Integración con la UI Actual



•
Sección 3: Recomendaciones de Implementación y Consideraciones Finales

•
Arquitectura y Componentes Clave

•
Estrategias de Pruebas

•
Consideraciones de Rendimiento y Escalabilidad

•
Mantenimiento y Evolución Futura



Se espera que este documento sirva como una guía clara para el equipo de desarrollo, permitiendo una comprensión profunda de los desafíos actuales y un camino bien definido hacia una solución efectiva y sostenible.

Sección 1: Diagnóstico y Soluciones Detalladas por Problema

Esta sección profundiza en cada uno de los problemas identificados, explicando su causa raíz y proponiendo soluciones técnicas específicas. Se hará referencia al código existente para ilustrar los puntos clave y se delinearán los cambios necesarios.

Problema 1: Generación de Planes Genéricos

Descripción del Problema:

El agente Mitosis, al recibir una solicitud de tarea, a menudo genera un plan de acción que es idéntico o muy similar a un plan predefinido, en lugar de crear uno específico y adaptado a la complejidad y los requisitos únicos de la tarea. Esto se manifiesta en la UI como una secuencia de pasos genéricos como "Análisis", "Ejecución" y "Entrega", independientemente de si la tarea es "Analizar tendencias de IA" o "Crear un script de automatización".

Razón del Problema (Análisis de agent_core.py y enhanced_prompts.py):

La causa principal de este comportamiento reside en la lógica de manejo de errores y respaldo dentro de la función create_and_execute_task en agent_core.py [1]. Cuando el modelo de lenguaje (LLM) encargado de la planificación no produce una respuesta en formato JSON válido o el JSON generado no contiene la estructura esperada (específicamente la clave phases), el sistema recurre a un plan de respaldo codificado. Este plan de respaldo es, por diseño, genérico:

Python


            try:
                # Extraer JSON del response si está envuelto en texto
                start_idx = plan_response.find("{")
                end_idx = plan_response.rfind("}") + 1
                if start_idx != -1 and end_idx != 0:
                    plan_json = plan_response[start_idx:end_idx]
                    plan_data = json.loads(plan_json)
                else:
                    # Si no hay JSON, crear plan básico
                    plan_data = {
                        "goal": goal,
                        "phases": [
                            {"id": 1, "title": "Análisis", "description": description, "required_capabilities": ["analysis"]},
                            {"id": 2, "title": "Ejecución", "description": "Ejecutar la tarea", "required_capabilities": ["general"]},
                            {"id": 3, "title": "Entrega", "description": "Entregar resultados", "required_capabilities": ["communication"]}
                        ]
                    }
            except json.JSONDecodeError:
                # Plan de respaldo
                plan_data = {
                    "goal": goal,
                    "phases": [
                        {"id": 1, "title": "Análisis", "description": description, "required_capabilities": ["analysis"]},
                        {"id": 2, "title": "Ejecución", "description": "Ejecutar la tarea", "required_capabilities": ["general"]},
                        {"id": 3, "title": "Entrega", "description": "Entregar resultados", "required_capabilities": ["communication"]}
                    ]
                }


Este mecanismo de respaldo, aunque previene fallos completos, enmascara el problema subyacente de que el LLM no está generando el JSON de plan de manera consistente o correcta. Las razones por las que el LLM podría fallar en esto incluyen:

•
Calidad del Modelo de Lenguaje: El planning_model seleccionado (self.model_manager.select_best_model(task_type="analysis", ...)) podría no ser lo suficientemente capaz o estar mal ajustado para la tarea de generación de JSON estructurado. Algunos LLMs son mejores que otros en seguir instrucciones de formato precisas.

•
Robustez del Prompt de Planificación: Aunque enhanced_prompts.py define un prompt task_planning con un formato JSON detallado, el LLM podría ignorar o desviarse de este formato si el prompt no es lo suficientemente coercitivo o si el modelo no ha sido entrenado con suficientes ejemplos de generación de JSON [2]. Pequeñas variaciones en la salida del LLM (por ejemplo, comas faltantes, llaves extra, comentarios inesperados) pueden romper el parseo JSON.

•
Contexto Insuficiente o Ruido: Si el context proporcionado al prompt de planificación es demasiado vago, ruidoso o no relevante, el LLM podría tener dificultades para generar un plan específico.

Solución Propuesta: Mejora de la Generación de Planes Específicos

La solución a este problema implica un enfoque multifacético que mejore la fiabilidad de la generación de JSON por parte del LLM y refine la lógica de planificación:

1.
Reforzar el Prompt de Planificación (enhanced_prompts.py):

•
Instrucciones Más Coercitivas: Modificar el prompt task_planning para incluir frases más imperativas y claras sobre la necesidad de adherirse estrictamente al formato JSON. Por ejemplo, añadir una advertencia como: "¡ADVERTENCIA! La respuesta DEBE ser un JSON válido y nada más. No incluyas texto explicativo antes o después del JSON." [3]

•
Ejemplos en Contexto (Few-shot learning): Incluir uno o dos ejemplos de pares de task_title y el JSON de plan esperado directamente en el prompt. Esto guía al LLM sobre el formato y la especificidad deseada. Los ejemplos deben ser variados para mostrar cómo el plan se adapta a diferentes tipos de tareas.

•
Validación de Esquema JSON: En lugar de solo pedir un JSON, se podría incluir un esquema JSON simplificado o una descripción de los campos requeridos y sus tipos, para que el LLM tenga una referencia más formal.



2.
Validación y Reintento Robusto (agent_core.py):

•
Validación de Esquema Post-Generación: Después de recibir la plan_response del LLM, implementar una validación más estricta del JSON. Utilizar una librería de validación de esquemas JSON (como jsonschema en Python) para verificar que la estructura del plan (phases, id, title, description, required_capabilities, etc.) cumple con un esquema predefinido. Esto es más robusto que solo verificar la existencia de phases.

•
Mecanismo de Reintento con Retroalimentación: Si la validación del JSON falla, en lugar de recurrir inmediatamente al plan genérico, el agente debería:

•
Registrar el Error: Guardar la plan_response fallida y el error de validación en la memoria para análisis futuro (aprendizaje).

•
Generar un Prompt de Corrección: Enviar un nuevo prompt al LLM, incluyendo la plan_response original y el error de validación, pidiéndole que corrija el JSON. Por ejemplo: "El JSON generado no es válido. Error: [mensaje de error]. Por favor, corrige el JSON y asegúrate de que cumpla con el esquema." [4]

•
Límite de Reintentos: Establecer un número máximo de reintentos (ej. 2-3). Solo después de agotar los reintentos y si el LLM sigue sin producir un JSON válido, se debería recurrir al plan de respaldo genérico. Esto asegura que el agente haga un esfuerzo significativo para generar un plan específico antes de rendirse.





3.
Selección de Modelo de LLM (model_manager.py):

•
Modelos Optimizados para JSON: Si es posible, configurar ModelManager para priorizar modelos de LLM que se sabe que son más fiables en la generación de JSON estructurado para la tarea de planificación. Algunos modelos están específicamente ajustados para la generación de código o datos estructurados.

•
Monitoreo de Rendimiento: Utilizar las métricas de PromptPerformance en enhanced_prompts.py para monitorear la tasa de éxito de la generación de JSON para el prompt task_planning. Si la tasa de éxito es consistentemente baja, esto indicaría la necesidad de ajustar el prompt, el modelo o la estrategia de reintento.



Impacto Esperado:

Al implementar estas mejoras, el agente Mitosis será capaz de generar planes de acción mucho más específicos y adaptados a cada tarea. Esto no solo mejorará la precisión de la planificación, sino que también proporcionará una experiencia de usuario más satisfactoria al ver planes de acción relevantes en la UI del módulo de Plan de Acción.

Problema 2: Falta de Concreción en la Ejecución de Tareas

Descripción del Problema:

El agente Mitosis "dice" que completa las fases de una tarea, pero en realidad no realiza ninguna acción externa o produce resultados tangibles. La "ejecución" es una simulación textual generada por el LLM, lo que lleva a la percepción de que el agente no es funcional y no entrega valor real.

Razón del Problema (Análisis de agent_core.py):

El núcleo de este problema se encuentra en la función execute_current_phase en agent_core.py [1]. Como se mencionó en el diagnóstico inicial, el código contiene un comentario explícito que revela la naturaleza simulada de la ejecución:

Python


            # Simular resultados de la fase (en una implementación real, aquí se ejecutarían herramientas)
            phase_results = {
                "execution_response": execution_response,
                "model_used": execution_model.name,
                "completed_at": time.time()
            }


Actualmente, execution_response es simplemente la salida textual del LLM en respuesta al execution_prompt. El agente luego verifica si esta respuesta contiene palabras como "completado" o "finalizado" para decidir si avanza a la siguiente fase. No hay un mecanismo para invocar herramientas externas, ejecutar código, interactuar con APIs o manipular archivos como parte de la ejecución de la fase.

Esto significa que, aunque el LLM pueda "pensar" en los pasos correctos y generar texto que suene como una ejecución exitosa, el sistema subyacente no realiza ninguna de esas acciones. La falta de una capa de "acción" real es la deficiencia más crítica del agente.

Solución Propuesta: Implementación de un Despachador de Herramientas (Tool Dispatcher)

Para resolver este problema, es fundamental introducir un mecanismo que permita al agente invocar y ejecutar herramientas externas de manera programática. Esto transformará la "simulación" en una "ejecución" real. La solución implica:

1.
Definición de Herramientas y sus Capacidades:

•
Cada herramienta disponible para el agente (ej. búsqueda web, ejecución de shell, manipulación de archivos, generación de imágenes, etc.) debe tener una definición clara de su propósito, sus parámetros de entrada y su formato de salida esperado.

•
Estas definiciones pueden residir en un ToolManager (si ya existe) o en un nuevo módulo tools.py.



2.
Invocación de Herramientas Basada en la Intención del LLM (agent_core.py):

•
La execution_response del LLM ya no debe ser solo texto libre. En su lugar, el LLM debe ser instruido para generar una llamada a herramienta estructurada (ej. en formato JSON) que el agente pueda parsear y ejecutar.

•
Modificación del Prompt de Ejecución de Fase (enhanced_prompts.py): El prompt phase_execution debe ser modificado para instruir al LLM a generar un JSON que contenga:

•
action_type: El tipo de acción a realizar (ej. tool_call, reflection, report).

•
Si action_type es tool_call:

•
tool_name: El nombre de la herramienta a invocar (ej. web_search, shell_exec, file_write_text).

•
tool_parameters: Un diccionario de parámetros para la herramienta, siguiendo su esquema.



•
thought: Un breve pensamiento del LLM sobre por qué está realizando esta acción.

•
status_update: Un mensaje de progreso para el usuario.



•
Ejemplo de Salida Esperada del LLM para phase_execution:



3.
Despachador de Herramientas (agent_core.py o nuevo tool_dispatcher.py):

•
Dentro de execute_current_phase, después de obtener la execution_response del LLM, se debe intentar parsearla como JSON.

•
Si es un JSON válido y contiene una tool_call:

•
Validar los tool_parameters contra el esquema de la herramienta.

•
Invocar la herramienta correspondiente utilizando los parámetros proporcionados. Esto implicaría llamar a las funciones de las herramientas disponibles (ej. default_api.info_search_web, default_api.shell_exec, etc.).

•
Capturar el resultado de la ejecución de la herramienta.

•
Registrar el resultado de la herramienta en la memoria del agente y en el contexto de la fase.



•
Si el LLM no genera una tool_call o si la herramienta falla, el agente debe tener una estrategia de manejo de errores (ver Problema 4).



4.
Actualización del Progreso Basada en Resultados Reales:

•
El avance de la fase ya no dependerá de palabras clave en la execution_response. En su lugar, se basará en el éxito de la tool_call y en la evaluación de los resultados de la herramienta.

•
Si una herramienta se ejecuta con éxito y produce los resultados esperados, la fase puede considerarse completada o se puede generar un nuevo prompt para el LLM para que evalúe los resultados y decida el siguiente paso.



Impacto Esperado:

Esta es la mejora más crítica. Al implementar un despachador de herramientas, el agente Mitosis pasará de ser un "simulador" a un "ejecutor" real. Cada fase del plan se traducirá en acciones concretas, como realizar búsquedas web, escribir archivos, ejecutar comandos de shell, etc. Esto permitirá al agente producir resultados tangibles y entregar el trabajo final de la tarea de forma efectiva, resolviendo directamente la queja del usuario sobre la falta de concreción.

Problema 3: Integración Limitada con Herramientas

Descripción del Problema:

Aunque el sistema parece tener un ToolManager y pruebas para herramientas como web_search y deep_research (evidenciado por mitosis_comprehensive_diagnostic.py), la función execute_current_phase en agent_core.py no muestra una integración explícita o un mecanismo para invocar estas herramientas durante la ejecución de las fases. Esto crea una desconexión entre la capacidad de las herramientas y la capacidad del agente para utilizarlas en el contexto de una tarea.

Razón del Problema:

La razón es una consecuencia directa del Problema 2. Dado que execute_current_phase actualmente solo genera una respuesta textual del LLM y busca palabras clave para avanzar, no hay un punto de integración donde las herramientas puedan ser llamadas. El execution_prompt actual no instruye al LLM a generar llamadas a herramientas, y no hay una capa de interpretación de la respuesta del LLM para traducir la intención en una invocación de herramienta.

Solución Propuesta: Formalización del Despachador de Herramientas y Definición de Interfaz

Esta solución es una extensión y formalización de la propuesta para el Problema 2. Se necesita un sistema claro y bien definido para que el LLM pueda "decidir" qué herramienta usar y cómo, y para que el agente pueda ejecutar esa decisión.

1.
Centralización de la Definición de Herramientas:

•
Crear un registro central de todas las herramientas disponibles, sus nombres, descripciones, y un esquema JSON para sus parámetros. Esto podría ser un diccionario o una clase en tool_manager.py o un nuevo tools_registry.py.

•
Ejemplo de registro:



2.
Generación de Llamadas a Herramientas por el LLM (enhanced_prompts.py):

•
El prompt phase_execution debe incluir las descripciones de las herramientas disponibles y sus esquemas de parámetros. Esto se conoce como "Function Calling" o "Tool Use" en el contexto de los LLMs [5].

•
El prompt instruirá al LLM a generar una respuesta en un formato específico (ej. JSON) que contenga la tool_name y tool_parameters si decide usar una herramienta. Si no se necesita una herramienta, el LLM puede generar una respuesta textual o un JSON indicando que la fase está completa.

•
Ejemplo de instrucción en el prompt:



3.
Lógica de Despacho en execute_current_phase (agent_core.py):

•
Después de recibir la respuesta del LLM, el agente debe:

•
Intentar parsear la respuesta como JSON.

•
Si es un JSON y action_type es tool_call:

•
Obtener tool_name y tool_parameters.

•
Buscar la herramienta en TOOLS_REGISTRY.

•
Validar los parámetros recibidos contra el esquema de la herramienta.

•
Invocar la función de la herramienta (TOOLS_REGISTRY[tool_name]["function"](**tool_parameters)).

•
Manejar el resultado de la herramienta (éxito/fallo, salida).



•
Si action_type es reflection o report, invocar las funciones correspondientes del agente.

•
Si el JSON no es válido o no se reconoce el action_type, o si la herramienta falla, activar el mecanismo de manejo de errores (ver Problema 4).





Impacto Esperado:

Esta formalización de la integración de herramientas permitirá al agente Mitosis utilizar activamente sus capacidades para realizar acciones concretas. El LLM actuará como un "cerebro" que decide qué herramienta usar, y el despachador de herramientas será el "brazo" que ejecuta esa decisión. Esto es fundamental para que el agente pueda producir resultados reales, como archivos generados, datos recopilados o scripts ejecutados.

Problema 4: Dependencia Excesiva en la Generación de Texto del LLM para el Control de Flujo

Descripción del Problema:

El avance de las fases de la tarea y la determinación de su finalización dependen de la detección de palabras clave como "completado" o "finalizado" en la respuesta textual del LLM. Este método es inherentemente frágil, ya que el LLM puede generar estas palabras sin haber logrado realmente el objetivo, o puede no generarlas incluso si la acción fue exitosa, lo que lleva a bucles, estancamientos o falsos positivos en el progreso.

Razón del Problema:

La razón es la falta de un mecanismo de retroalimentación estructurado y verificable desde la capa de ejecución de la tarea. Al no haber una invocación real de herramientas (Problema 2 y 3), el agente no tiene una forma objetiva de saber si una fase ha sido completada con éxito. Por lo tanto, se ve obligado a depender de la interpretación del lenguaje natural del LLM, que es propenso a la ambigüedad y a la "alucinación" de éxito.

Solución Propuesta: Control de Flujo Basado en Eventos y Resultados Estructurados

Para un control de flujo robusto, el agente debe basarse en señales claras y estructuradas, no en la interpretación de texto libre. Esto implica:

1.
Resultados Estructurados de Herramientas:

•
Cada herramienta invocada por el despachador de herramientas debe devolver un resultado estructurado (ej. JSON) que indique claramente el éxito o fracaso de la operación, junto con cualquier salida relevante (ej. ruta del archivo creado, resultados de búsqueda, etc.).

•
Ejemplo de resultado de herramienta:



2.
Lógica de Avance de Fase en agent_core.py:

•
La función execute_current_phase debe evaluar el status del resultado de la herramienta. Si el status es success, la fase puede considerarse completada. Si es failure, se activa el mecanismo de manejo de errores.

•
El LLM aún puede ser consultado para una "reflexión" sobre el resultado de la herramienta o para decidir la siguiente acción, pero la decisión de avanzar de fase no debe depender de su texto libre.



3.
Manejo de Errores y Reintentos Inteligentes (agent_core.py):

•
Cuando una herramienta falla, el agente debe invocar su función handle_error (que ya existe). Esta función debería generar un prompt al LLM con el mensaje de error y el contexto, pidiéndole una estrategia de recuperación. La respuesta del LLM debe ser una nueva tool_call o una instrucción para el agente (ej. "pedir ayuda al usuario").

•
Implementar un contador de reintentos por fase. Si una fase falla repetidamente, el agente debe escalar el problema (ej. notificar al usuario, marcar la tarea como fallida).



4.
Actualización de la UI con Progreso Verificable:

•
La UI debe reflejar el progreso de la tarea basándose en el estado real de las fases y los resultados de las herramientas, no solo en las respuestas textuales del LLM.

•
Cuando una herramienta crea un archivo, la UI debería mostrar el nombre del archivo y, idealmente, un enlace para descargarlo o previsualizarlo. Cuando una búsqueda web se completa, la UI debería mostrar los enlaces relevantes.



Impacto Esperado:

Este cambio fundamental hará que el control de flujo del agente sea mucho más robusto y fiable. El progreso de la tarea se basará en hechos verificables (ejecución exitosa de herramientas) en lugar de en la interpretación subjetiva del texto del LLM. Esto no solo mejorará la precisión del estado del agente, sino que también permitirá una retroalimentación más significativa y útil para el usuario en la UI, mostrando resultados tangibles a medida que la tarea avanza.

Sección 2: Flujo Funcional Deseado y Experiencia de Usuario

Esta sección describe cómo debería funcionar el agente Mitosis una vez implementadas las soluciones propuestas, enfocándose en el flujo de trabajo desde la perspectiva del usuario y cómo la UI actual se adaptará para reflejar estas mejoras.

Visión General del Flujo Funcional Deseado

El flujo funcional deseado para el agente Mitosis se puede describir en los siguientes pasos, que se ejecutarán de manera iterativa y reflexiva:

1.
Recepción de la Tarea (Input del Usuario):

•
El usuario introduce una solicitud de tarea en el campo de entrada de texto de la UI (ej. "Crea un informe sobre las tendencias de IA en 2025").

•
La UI envía esta solicitud al backend del agente.



2.
Análisis y Planificación de la Tarea (Backend - agent_core.py):

•
El agente recibe la solicitud.

•
Invoca al LLM (a través de model_manager y enhanced_prompts) para generar un plan de acción específico y detallado en formato JSON. Este plan incluirá fases, descripciones, capacidades requeridas y, opcionalmente, herramientas sugeridas para cada fase.

•
Si el JSON no es válido o el plan no es específico, el agente reintentará con el LLM, proporcionando retroalimentación sobre el error de formato o la falta de especificidad.

•
Una vez que se obtiene un plan válido y específico, el task_manager lo registra y lo marca como la tarea activa.



3.
Visualización del Plan de Acción (UI - Módulo de Plan de Acción):

•
El backend envía el plan de acción generado a la UI.

•
El módulo de Plan de Acción en la UI (que ya es funcional) mostrará este plan detallado, con sus fases y descripciones específicas. Ya no se verán planes genéricos.

•
La UI indicará claramente la fase actual activa.



4.
Ejecución Iterativa de Fases (Backend - agent_core.py):

•
El agente selecciona la fase actual del plan.

•
Genera un prompt para el LLM (phase_execution) instruyéndole a decidir la siguiente acción concreta para esa fase. Esta acción será una tool_call (ej. web_search, file_write_text, shell_exec) o una indicación de que la fase está completa.

•
Despacho de Herramientas: Si el LLM decide invocar una herramienta, el agente parsea la llamada a la herramienta y la ejecuta utilizando las funciones reales de las herramientas (ej. default_api.info_search_web).

•
Monitoreo de Consola (Backend): Durante la ejecución de la herramienta, el agente registrará en su consola interna (logs) las acciones que está realizando y los archivos que está generando o modificando. Esta información será crucial para la retroalimentación a la UI.



5.
Retroalimentación de Progreso y Resultados (Backend a UI):

•
El resultado de la ejecución de la herramienta (éxito/fallo, salida) se envía de vuelta al agente.

•
El agente actualiza el estado de la fase en el task_manager (completada, en progreso, fallida).

•
Actualización de la UI: El backend enviará actualizaciones en tiempo real a la UI, indicando:

•
La fase actual y su estado.

•
Los resultados de las herramientas (ej. "Búsqueda web completada, se encontraron 10 resultados", "Archivo 'informe.md' creado").

•
Archivos Generados: Si se genera un archivo, la UI mostrará un enlace o una previsualización del archivo. Esto es clave para la "entrega del archivo o trabajo final de la tarea de forma efectiva".

•
Mensajes de la consola interna del agente, mostrando los archivos en los que está trabajando.





6.
Reflexión y Manejo de Errores (Backend - agent_core.py):

•
Después de cada acción (especialmente si una herramienta falla), el agente puede invocar su función de reflection para analizar el resultado y aprender.

•
Si una herramienta falla, el agente utiliza su función handle_error para intentar una estrategia de recuperación (ej. reintentar con diferentes parámetros, usar una herramienta alternativa, pedir aclaración al usuario).

•
La UI reflejará estos estados de error y recuperación, proporcionando transparencia al usuario.



7.
Finalización de la Tarea (Backend a UI):

•
Una vez que todas las fases del plan se completan con éxito, el task_manager marca la tarea como finalizada.

•
El backend notifica a la UI, que mostrará un mensaje de finalización y presentará el resultado final de la tarea (ej. el informe completo, el script funcional, etc.).



Integración con la UI Actual

La UI actual ya cuenta con un módulo de Plan de Acción y una consola. La clave es cómo alimentar estos componentes con datos más ricos y precisos del backend sin duplicar funcionalidad o romper lo existente.

1. Módulo de Plan de Acción (UI):

•
Cambio Necesario: La UI actualmente recibe un plan (genérico) y lo muestra. El cambio principal es que el backend ahora enviará un plan específico y detallado generado por el LLM (después de la validación y reintentos). La lógica de renderizado de la UI para las fases y sus descripciones debería ser capaz de manejar esta mayor especificidad.

•
Implementación:

•
Backend: Asegurarse de que el endpoint que sirve el plan de acción (/api/agent/generate-plan o similar) devuelva el JSON del plan generado por el LLM (con las mejoras del Problema 1).

•
Frontend: El componente de la UI que renderiza el plan (PlanActionComponent o similar) no debería necesitar cambios drásticos si ya itera sobre una lista de fases y muestra sus title y description. La mejora será en el contenido de esos campos, no en la estructura de datos.

•
Actualización de Progreso: La UI ya debe tener un mecanismo para marcar la fase activa. El backend deberá enviar actualizaciones de estado (ej. a través de WebSockets o polling) para indicar qué fase está active o completed. Esto se integraría con la lógica de task_manager.advance_phase.



2. Consola de Actividad (UI):

•
Cambio Necesario: La consola actual probablemente muestra mensajes de log o de chat. Para mostrar los archivos generados y el progreso de las herramientas, la consola necesita recibir mensajes estructurados del backend que incluyan información sobre las acciones de las herramientas y los resultados de los archivos.

•
Implementación:

•
Backend (agent_core.py, tool_dispatcher.py):

•
Cuando una herramienta se invoca, el tool_dispatcher (o la lógica dentro de execute_current_phase) debe generar un mensaje de log estructurado que incluya el nombre de la herramienta, los parámetros, y el resultado (ej. ruta del archivo, URL de búsqueda). Este mensaje no es solo para el log interno, sino para ser enviado a la UI.

•
Estos mensajes estructurados se pueden enviar a la UI a través de un canal de comunicación en tiempo real (ej. WebSockets). Si ya existe un endpoint de chat o de log, se puede extender para manejar estos mensajes de "actividad de herramienta".



•
Frontend:

•
El componente de la UI que renderiza la consola (ConsoleComponent o similar) necesitará lógica para interpretar estos mensajes estructurados.

•
Si un mensaje indica que se ha generado un archivo, la UI debería renderizar un enlace clicable al archivo (ej. <a href="/path/to/file.md" target="_blank">informe.md</a>). Esto requerirá que el backend exponga un endpoint para servir los archivos generados.

•
Si un mensaje indica una búsqueda web, podría mostrar los enlaces relevantes directamente en la consola o un resumen.





3. Entrega del Archivo o Trabajo Final (UI):

•
Cambio Necesario: Actualmente, el agente no entrega un "trabajo final". Con las mejoras, cuando una tarea se completa (ej. se genera un informe), el agente debe notificar a la UI y proporcionar la ubicación del archivo final.

•
Implementación:

•
Backend (task_manager.py, agent_core.py): Cuando task_manager.complete_task es llamado, debe incluir en su notificación a la UI la ruta del archivo o los archivos resultantes de la tarea. Esto puede ser parte del task_status o un evento separado.

•
Frontend: La UI, al recibir la notificación de tarea completada, debería mostrar prominentemente un enlace al archivo final. Esto podría ser un botón "Descargar Informe" o una sección "Resultados Finales" en el módulo de Plan de Acción.



Consideraciones Clave para la UI:

•
API de Backend: Asegurarse de que el backend exponga los endpoints necesarios para que la UI pueda:

•
Obtener el plan de acción detallado.

•
Recibir actualizaciones de progreso en tiempo real (WebSockets son ideales para esto).

•
Servir los archivos generados por el agente (ej. un endpoint /api/files/{task_id}/{filename}).



•
Reutilización de Componentes: La filosofía debe ser reutilizar los componentes existentes de la UI (módulo de Plan de Acción, consola) y simplemente enriquecer los datos que reciben del backend. Esto minimiza el riesgo de duplicación y rotura.

•
Estado de la UI: La UI debe ser capaz de reflejar los diferentes estados del agente (pensando, planificando, ejecutando, reflexionando, error) para proporcionar transparencia al usuario.

Sección 3: Recomendaciones de Implementación y Consideraciones Finales

Esta sección ofrece recomendaciones prácticas para el equipo de desarrollo, abarcando aspectos de arquitectura, pruebas, rendimiento y mantenimiento, para asegurar una implementación exitosa y sostenible de las soluciones propuestas.

Arquitectura y Componentes Clave

La arquitectura actual del agente Mitosis, con sus módulos model_manager, memory_manager, task_manager y enhanced_prompts, es una base sólida. Las mejoras propuestas se centran en fortalecer la interacción entre estos componentes y añadir una capa de ejecución de herramientas robusta.

1.
Refactorización de execute_current_phase: Esta función en agent_core.py se convertirá en el corazón de la ejecución real. Deberá ser capaz de:

•
Parsear la salida estructurada del LLM (llamadas a herramientas).

•
Validar las llamadas a herramientas contra un registro centralizado.

•
Invocar dinámicamente las funciones de las herramientas.

•
Manejar los resultados de las herramientas (éxito/fallo).

•
Actualizar el estado de la tarea y la memoria con los resultados de la ejecución.



2.
Módulo ToolDispatcher (Nuevo): Se recomienda crear un nuevo módulo tool_dispatcher.py o una clase ToolDispatcher dentro de agent_core.py para encapsular la lógica de invocación y manejo de herramientas. Esto mantendrá agent_core.py más limpio y facilitará la adición de nuevas herramientas en el futuro. Este despachador interactuaría con un TOOLS_REGISTRY centralizado.

3.
TOOLS_REGISTRY Centralizado: Como se mencionó, un diccionario o clase que mapee nombres de herramientas a sus funciones reales y esquemas de parámetros es crucial. Esto permite al LLM "conocer" las herramientas disponibles y al despachador invocarlas de forma segura.

4.
Mecanismo de Comunicación Backend-Frontend (WebSockets): Para una retroalimentación en tiempo real fluida en la UI (progreso de fases, logs de herramientas, archivos generados), se recomienda encarecidamente el uso de WebSockets. Esto permitirá al backend "empujar" actualizaciones a la UI tan pronto como ocurran, en lugar de que la UI tenga que "tirar" (polling) constantemente. Si ya existe un sistema de WebSockets para el chat, se puede extender para mensajes de progreso y actividad.

5.
Persistencia de Tareas y Resultados: Asegurarse de que el task_manager persista el estado completo de las tareas (incluyendo los resultados de las fases y los archivos generados) en la base de datos de memoria. Esto es vital para la recuperación de fallos y para que el usuario pueda revisar el historial de tareas.

Estrategias de Pruebas

La implementación de estas soluciones requiere un enfoque de pruebas riguroso para garantizar la fiabilidad y evitar regresiones.

1.
Pruebas Unitarias:

•
Generación de Prompts: Probar que enhanced_prompts.py genera prompts correctamente estructurados, incluyendo los ejemplos y las instrucciones coercitivas para JSON.

•
Parseo de JSON del Plan: Probar la lógica de parseo y validación del JSON del plan en agent_core.py con casos de éxito, JSONs inválidos, JSONs incompletos y JSONs con estructura incorrecta.

•
Despachador de Herramientas: Probar que el ToolDispatcher puede parsear correctamente las llamadas a herramientas del LLM, validar los parámetros e invocar las funciones correctas. Mockear las funciones de las herramientas para estas pruebas.

•
Manejo de Errores: Probar la función handle_error con diferentes tipos de errores y verificar que genera estrategias de recuperación adecuadas.



2.
Pruebas de Integración:

•
Flujo de Planificación: Probar el flujo completo de create_and_execute_task, asegurando que el LLM genera planes específicos y que el sistema los acepta y los registra correctamente.

•
Flujo de Ejecución de Fase: Probar execute_current_phase con diferentes tipos de fases que requieran diferentes herramientas (ej. una fase que requiera web_search, otra file_write_text). Verificar que las herramientas se invocan y que los resultados se procesan correctamente.

•
Integración con Memoria: Asegurar que los resultados de las herramientas y las reflexiones se almacenan correctamente en el memory_manager.



3.
Pruebas End-to-End (E2E):

•
Simulación de Tareas Completas: Crear pruebas E2E que simulen una tarea completa desde la entrada del usuario hasta la entrega del resultado final. Esto implicaría la interacción con el backend y la verificación de los resultados en el sistema de archivos o en la base de datos.

•
Integración UI-Backend: Utilizar herramientas de prueba de UI (ej. Playwright, Selenium) para simular la interacción del usuario con la UI y verificar que el plan de acción se muestra correctamente, la consola se actualiza en tiempo real y los archivos finales son accesibles.



4.
Pruebas de Rendimiento y Escalabilidad:

•
Monitorear el tiempo de respuesta de la generación de planes y la ejecución de fases. Identificar cuellos de botella, especialmente en las interacciones con el LLM y las herramientas externas.

•
Realizar pruebas de carga para asegurar que el agente puede manejar múltiples tareas concurrentes (si max_concurrent_tasks lo permite) sin degradación significativa del rendimiento.



Consideraciones de Rendimiento y Escalabilidad

•
Llamadas al LLM: Las llamadas al LLM son costosas en tiempo y recursos. Optimizar los prompts para obtener la información necesaria en una sola llamada, y utilizar modelos más pequeños y rápidos para tareas menos complejas cuando sea posible.

•
Asincronía: Utilizar asyncio en Python para manejar operaciones I/O intensivas (llamadas a LLM, invocación de herramientas externas, operaciones de red/disco) de manera asíncrona. Esto permitirá que el agente maneje múltiples solicitudes o fases de tareas de manera más eficiente sin bloquear el hilo principal.

•
Manejo de Errores Robusto: Los errores en las herramientas externas pueden ralentizar o detener el agente. Implementar timeouts, reintentos con backoff exponencial y mecanismos de circuit breaker para manejar fallos de herramientas de manera elegante.

•
Optimización de Memoria: Monitorear el uso de memoria, especialmente en el memory_manager. Asegurarse de que la limpieza de datos antiguos (cleanup_old_data) funcione correctamente para evitar el crecimiento descontrolado de la base de datos.

Mantenimiento y Evolución Futura

•
Logging Detallado: Mantener un sistema de logging exhaustivo que registre las decisiones del LLM, las invocaciones de herramientas, los resultados de las herramientas, los errores y el progreso de las tareas. Esto será invaluable para la depuración y el monitoreo del comportamiento del agente.

•
Monitoreo de Métricas: Implementar un sistema de monitoreo para las métricas clave del agente (ej. tasa de éxito de planificación, tasa de éxito de ejecución de herramientas, tiempo promedio por fase, uso de recursos). Esto permitirá identificar problemas de rendimiento o comportamiento anómalo de manera proactiva.

•
Aprendizaje Continuo: El sistema de PromptPerformance en enhanced_prompts.py es un excelente punto de partida para el aprendizaje continuo. Utilizar los datos de rendimiento para refinar automáticamente los prompts o para sugerir ajustes manuales a los desarrolladores.

•
Extensibilidad de Herramientas: Diseñar el ToolDispatcher y el TOOLS_REGISTRY de manera que sea fácil añadir nuevas herramientas en el futuro sin modificar el núcleo del agente.

•
Feedback del Usuario: Establecer un mecanismo para que los usuarios puedan proporcionar retroalimentación sobre la calidad de los planes y los resultados de las tareas. Esta retroalimentación puede ser utilizada para mejorar el agente a través de un ciclo de aprendizaje humano-en-el-bucle.

