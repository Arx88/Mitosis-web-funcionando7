# Plan Detallado de Mejoras para el Agente MitosisV6

Este documento proporciona un plan exhaustivo y paso a paso para transformar el agente MitosisV6 en un sistema autónomo altamente capaz, similar a los agentes de propósito general más avanzados. El enfoque principal estará en las mejoras del backend, asegurando que la interfaz de usuario existente pueda seguir funcionando sin cambios significativos, o con adaptaciones mínimas.

Cada sección detalla el objetivo de la mejora, los cambios de diseño propuestos y las instrucciones de implementación específicas para el equipo de desarrollo.

## Fase 1: Preparación del Entorno y Definición de la Interfaz de Herramientas

### Objetivo de la Fase

El objetivo de esta fase es establecer una base sólida para la integración de herramientas y asegurar que el equipo de desarrollo tenga un entorno de trabajo consistente y eficiente. Esto incluye definir una interfaz unificada para todas las herramientas que el agente podrá utilizar, lo que es crucial para la modularidad y la escalabilidad del sistema.

### 1.1. Configuración del Entorno de Desarrollo

**Objetivo:** Asegurar que todos los miembros del equipo tengan un entorno de desarrollo idéntico y que las dependencias del proyecto estén claramente definidas y gestionadas.

**Instrucciones de Implementación:**

1.  **Creación de un `requirements.txt`:**
    *   **Acción:** Generar un archivo `requirements.txt` que liste todas las bibliotecas de Python necesarias para el proyecto MitosisV6. Esto debe incluir las dependencias actuales (como `sqlite3`, `json`, `logging`, `ollama`, `openrouter`, etc.) y cualquier nueva dependencia que se introduzca (por ejemplo, para validación de JSON, embeddings, bases de datos vectoriales, etc.).
    *   **Comando Sugerido:** Ejecutar `pip freeze > requirements.txt` en un entorno virtual limpio después de instalar todas las dependencias del proyecto.
    *   **Ubicación:** `mitosisv6_root/requirements.txt`

2.  **Uso de Entornos Virtuales:**
    *   **Acción:** Instruir a todos los desarrolladores para que utilicen entornos virtuales (por ejemplo, `venv` o `conda`) para aislar las dependencias del proyecto del sistema global de Python.
    *   **Comandos Sugeridos:**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        ```

3.  **Configuración de Linter y Formateador (Opcional pero Recomendado):**
    *   **Acción:** Configurar herramientas como `flake8` (linter) y `black` (formateador) para mantener la consistencia del código en todo el equipo. Esto reduce los conflictos de estilo y mejora la legibilidad.
    *   **Comandos Sugeridos:**
        ```bash
        pip install flake8 black
        # Añadir a pre-commit hooks si se usa Git
        ```

### 1.2. Definición de la Interfaz Unificada de Herramientas

**Objetivo:** Crear una interfaz estándar para todas las herramientas que el agente podrá invocar. Esto permitirá que el agente interactúe con diversas funcionalidades externas de manera consistente, sin necesidad de conocer los detalles de implementación de cada herramienta.

**Diseño Propuesto:**

Se propone una clase base `Tool` y un registro centralizado de herramientas. Cada herramienta será una clase que herede de `Tool` y que implemente un método `run`.

**Instrucciones de Implementación:**

1.  **Crear un Nuevo Módulo para Herramientas:**
    *   **Acción:** Crear un nuevo directorio `tools/` dentro de `backend/` para organizar todas las definiciones de herramientas.
    *   **Ubicación:** `mitosisv6_root/backend/tools/`

2.  **Definir la Clase Base `Tool`:**
    *   **Acción:** Crear un archivo `base_tool.py` dentro de `backend/tools/` con la siguiente estructura:
    *   **Código (`backend/tools/base_tool.py`):**
        ```python
        from abc import ABC, abstractmethod
        from typing import Dict, Any, List

        class Tool(ABC):
            """Clase base abstracta para todas las herramientas del agente.
            Cada herramienta debe heredar de esta clase e implementar los métodos abstractos.
            """
            def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
                self._name = name
                self._description = description
                self._parameters = parameters

            @property
            def name(self) -> str:
                """Nombre único de la herramienta (ej. 'shell_exec', 'file_read')."""
                return self._name

            @property
            def description(self) -> str:
                """Descripción concisa de la herramienta para que el LLM entienda su propósito.
                Debe ser lo suficientemente detallada para que el LLM sepa cuándo y cómo usarla.
                """
                return self._description

            @property
            def parameters(self) -> Dict[str, Any]:
                """Esquema JSON de los parámetros de entrada que la herramienta espera.
                Debe seguir el formato de JSON Schema para describir tipos, descripciones, etc.
                Ejemplo: {'type': 'object', 'properties': {'command': {'type': 'string', 'description': 'Comando a ejecutar'}}, 'required': ['command']}
                """
                return self._parameters

            @abstractmethod
            def run(self, **kwargs) -> Dict[str, Any]:
                """Ejecuta la lógica de la herramienta con los parámetros proporcionados.
                Debe devolver un diccionario con el resultado de la operación.
                """
                pass

            def to_json_schema(self) -> Dict[str, Any]:
                """Genera el esquema JSON completo de la herramienta para el LLM.
                """
                return {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.parameters
                }
        ```

3.  **Crear un Registro de Herramientas (`tool_registry.py`):**
    *   **Acción:** Crear un archivo `tool_registry.py` dentro de `backend/tools/` que actuará como un registro central para todas las herramientas disponibles. Este registro será utilizado por el `agent_core` para descubrir e invocar herramientas.
    *   **Código (`backend/tools/tool_registry.py`):**
        ```python
        from typing import Dict, Type
        from backend.tools.base_tool import Tool

        class ToolRegistry:
            """Registro centralizado para todas las herramientas disponibles del agente.
            Permite registrar y recuperar herramientas por su nombre.
            """
            _tools: Dict[str, Tool] = {}

            @classmethod
            def register_tool(cls, tool_instance: Tool):
                """Registra una instancia de herramienta en el registro.
                Args:
                    tool_instance: Una instancia de una clase que hereda de Tool.
                """
                if not isinstance(tool_instance, Tool):
                    raise TypeError("Solo se pueden registrar instancias de Tool.")
                if tool_instance.name in cls._tools:
                    raise ValueError(f"La herramienta '{tool_instance.name}' ya está registrada.")
                cls._tools[tool_instance.name] = tool_instance
                print(f"Herramienta '{tool_instance.name}' registrada exitosamente.")

            @classmethod
            def get_tool(cls, name: str) -> Tool:
                """Recupera una herramienta registrada por su nombre.
                Args:
                    name: El nombre de la herramienta a recuperar.
                Returns:
                    La instancia de la herramienta.
                Raises:
                    ValueError: Si la herramienta no está registrada.
                """
                tool = cls._tools.get(name)
                if not tool:
                    raise ValueError(f"La herramienta '{name}' no está registrada.")
                return tool

            @classmethod
            def list_tools(cls) -> List[Tool]:
                """Lista todas las herramientas registradas.
                Returns:
                    Una lista de instancias de Tool.
                """
                return list(cls._tools.values())

            @classmethod
            def get_tool_json_schemas(cls) -> List[Dict[str, Any]]:
                """Obtiene los esquemas JSON de todas las herramientas registradas.
                Esto es útil para proporcionar al LLM una descripción de las herramientas disponibles.
                """
                return [tool.to_json_schema() for tool in cls._tools.values()]

            @classmethod
            def clear_registry(cls):
                """Limpia el registro de herramientas (útil para pruebas).
                """
                cls._tools.clear()
        ```

4.  **Actualizar `agent_core.py` para Usar el Registro de Herramientas:**
    *   **Acción:** Modificar la inicialización de `MitosisAgent` para incluir una instancia del `ToolRegistry` y registrar las herramientas iniciales (aunque las herramientas concretas se implementarán en la Fase 2).
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...
        from backend.tools.tool_registry import ToolRegistry
        # ... otras clases y dataclasses ...

        class MitosisAgent:
            # ... __init__ existente ...
            def __init__(self, config: Optional[AgentConfig] = None):
                # ... código existente ...
                self.tool_registry = ToolRegistry()
                self._register_initial_tools() # Nuevo método para registrar herramientas
                # ... código existente ...

            def _register_initial_tools(self):
                """Registra las herramientas básicas del agente.
                Estas herramientas se implementarán en detalle en la Fase 2.
                """
                # Ejemplo de registro (las implementaciones reales vendrán después)
                # from backend.tools.shell_tool import ShellTool
                # self.tool_registry.register_tool(ShellTool())
                # ... otras herramientas ...
                pass # Por ahora, no se registran herramientas concretas

            # ... resto de la clase ...
        ```

### 1.3. Preparación para la Integración de LLM con Herramientas

**Objetivo:** Asegurar que el LLM pueda recibir y comprender las descripciones de las herramientas, y que pueda generar llamadas a herramientas en un formato parseable.

**Diseño Propuesto:**

El `EnhancedPromptManager` necesitará ser capaz de incluir las descripciones de las herramientas en el prompt del LLM. El LLM, a su vez, deberá ser instruido para generar una respuesta que incluya una llamada a una herramienta en un formato específico (por ejemplo, JSON o un formato de función).

**Instrucciones de Implementación:**

1.  **Modificar `EnhancedPromptManager` para Incluir Herramientas:**
    *   **Acción:** Añadir un método a `EnhancedPromptManager` que pueda generar un prompt incluyendo las descripciones de las herramientas disponibles. Esto se utilizará en el bucle de ejecución de fases.
    *   **Cambios en `backend/enhanced_prompts.py` (fragmento):**
        ```python
        # ... imports existentes ...
        from backend.tools.tool_registry import ToolRegistry # Importar el registro
        # ... otras clases y dataclasses ...

        class EnhancedPromptManager:
            def __init__(self, memory_manager, task_manager):
                # ... código existente ...
                self.tool_registry = ToolRegistry() # Acceso al registro de herramientas
                # ... código existente ...

            def generate_tool_use_prompt(self, task, phase, current_context: str) -> str:
                """Genera un prompt para que el LLM decida qué herramienta usar.
                Incluye la descripción de la tarea, la fase actual, el contexto y las herramientas disponibles.
                """
                tool_schemas = self.tool_registry.get_tool_json_schemas()
                tools_description = json.dumps(tool_schemas, indent=2)

                prompt = f"""Eres un agente autónomo. Tu objetivo es completar la fase actual de la tarea.

Tarea: {task.title}
Descripción de la Tarea: {task.description}
Objetivo de la Tarea: {task.goal}

Fase Actual: {phase.title}
Descripción de la Fase: {phase.description}
Capacidades Requeridas para la Fase: {', '.join(phase.required_capabilities)}

Contexto Actual de la Ejecución de la Fase:
{current_context}

Herramientas Disponibles (en formato JSON Schema):
```json
{tools_description}
```

Basándote en la tarea, la fase actual y el contexto, decide la siguiente acción. Puedes:
1. Usar una de las herramientas disponibles. Si usas una herramienta, tu respuesta DEBE ser un objeto JSON con la siguiente estructura:
   ```json
   {{"tool_name": "nombre_de_la_herramienta", "tool_args": {{ "param1": "valor1", "param2": "valor2"}}}}
   ```
   Asegúrate de que los parámetros (`tool_args`) coincidan con el esquema de la herramienta.
2. Indicar que la fase ha sido completada. Si la fase está completamente terminada y no se necesitan más acciones o herramientas, tu respuesta DEBE ser un objeto JSON con la siguiente estructura:
   ```json
   {{"action": "finish_phase", "result": "Descripción del resultado final de la fase."}}
   ```
3. Indicar que necesitas más información o que no puedes proceder. Si no puedes avanzar, tu respuesta DEBE ser un objeto JSON con la siguiente estructura:
   ```json
   {{"action": "request_info", "reason": "Explicación de por qué no puedes avanzar y qué información necesitas."}}
   ```

Tu respuesta debe ser SOLO el objeto JSON. No incluyas texto adicional antes o después del JSON.
"""
                return prompt

            # ... resto de la clase ...
        ```

2.  **Preparación para el Parseo de Llamadas a Herramientas:**
    *   **Acción:** En `agent_core.py`, se necesitará un nuevo método para parsear la respuesta del LLM y extraer el nombre de la herramienta y sus argumentos, o la indicación de que la fase ha terminado.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...
        import json
        # ... otras clases y dataclasses ...

        class MitosisAgent:
            # ... __init__ y otros métodos ...

            def _parse_tool_call(self, llm_response: str) -> Dict[str, Any]:
                """Parsea la respuesta del LLM para extraer la llamada a la herramienta o la acción.
                Asume que la respuesta es un JSON válido.
                """
                try:
                    response_data = json.loads(llm_response)
                    return response_data
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error al parsear la respuesta del LLM como JSON: {e}. Respuesta: {llm_response}")
                    # Podrías intentar una recuperación aquí o lanzar una excepción
                    return {"action": "error", "reason": f"JSON inválido: {e}"}

            # ... resto de la clase ...
        ```

Esta fase sienta las bases para la integración de herramientas. En la siguiente fase, se implementarán las herramientas esenciales y se comenzará a modificar el bucle de ejecución para utilizarlas.



## Fase 2: Implementación de Herramientas Esenciales (Shell, Archivos, Web)

### Objetivo de la Fase

El objetivo de esta fase es implementar un conjunto inicial de herramientas esenciales que permitirán al agente interactuar con el sistema operativo, el sistema de archivos y la web. Estas herramientas son los "sentidos" y "manos" del agente, habilitando la ejecución de acciones reales en el entorno. Cada herramienta se implementará como una clase que hereda de la clase `Tool` definida en la Fase 1.

### 2.1. Herramienta de Ejecución de Comandos de Shell (`ShellTool`)

**Objetivo:** Permitir que el agente ejecute comandos de shell directamente en el entorno del sistema operativo, lo que es fundamental para tareas como la instalación de paquetes, la ejecución de scripts, la gestión de procesos, etc.

**Diseño Propuesto:**

La `ShellTool` encapsulará la ejecución de comandos de shell y la captura de su salida. Se utilizará el módulo `subprocess` de Python para ejecutar los comandos de forma segura.

**Instrucciones de Implementación:**

1.  **Crear el Archivo de la Herramienta:**
    *   **Acción:** Crear un archivo `shell_tool.py` dentro de `backend/tools/`.
    *   **Código (`backend/tools/shell_tool.py`):**
        ```python
        import subprocess
        from typing import Dict, Any
        from backend.tools.base_tool import Tool

        class ShellTool(Tool):
            """Herramienta para ejecutar comandos de shell.
            Permite al agente interactuar directamente con el sistema operativo.
            """
            def __init__(self):
                super().__init__(
                    name="shell_exec",
                    description="Ejecuta un comando de shell y devuelve su salida. Útil para instalar paquetes, ejecutar scripts, etc.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "El comando de shell a ejecutar."
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Tiempo máximo en segundos para la ejecución del comando. Por defecto es 60.",
                                "default": 60
                            }
                        },
                        "required": ["command"]
                    }
                )

            def run(self, command: str, timeout: int = 60) -> Dict[str, Any]:
                """Ejecuta el comando de shell especificado.
                Args:
                    command: El comando de shell a ejecutar.
                    timeout: Tiempo máximo en segundos para la ejecución del comando.
                Returns:
                    Un diccionario con la salida estándar, la salida de error y el código de retorno.
                """
                try:
                    # Usar subprocess.run para ejecutar el comando de forma segura
                    # capture_output=True captura stdout y stderr
                    # text=True decodifica stdout/stderr como texto
                    # check=True lanzará una CalledProcessError si el comando devuelve un código de salida distinto de cero
                    result = subprocess.run(
                        command, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        timeout=timeout,
                        check=True
                    )
                    return {
                        "status": "success",
                        "stdout": result.stdout.strip(),
                        "stderr": result.stderr.strip(),
                        "returncode": result.returncode
                    }
                except subprocess.CalledProcessError as e:
                    return {
                        "status": "error",
                        "stdout": e.stdout.strip(),
                        "stderr": e.stderr.strip(),
                        "returncode": e.returncode,
                        "message": f"El comando falló con código de retorno {e.returncode}"
                    }
                except subprocess.TimeoutExpired:
                    return {
                        "status": "error",
                        "stdout": "",
                        "stderr": "",
                        "returncode": 1,
                        "message": f"El comando excedió el tiempo de espera de {timeout} segundos."
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "stdout": "",
                        "stderr": str(e),
                        "returncode": 1,
                        "message": f"Error inesperado al ejecutar el comando: {str(e)}"
                    }
        ```

2.  **Registrar la Herramienta en `agent_core.py`:**
    *   **Acción:** Importar `ShellTool` en `agent_core.py` y registrar una instancia en el `ToolRegistry` durante la inicialización del agente.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...
        from backend.tools.shell_tool import ShellTool # Nuevo import

        class MitosisAgent:
            # ... __init__ existente ...

            def _register_initial_tools(self):
                """Registra las herramientas básicas del agente.
                """
                self.tool_registry.register_tool(ShellTool())
                # ... se añadirán más herramientas aquí ...
        ```

### 2.2. Herramientas de Gestión de Archivos (`FileReadTool`, `FileWriteTool`, `FileAppendTool`, `FileDeleteTool`)

**Objetivo:** Proporcionar al agente la capacidad de interactuar con el sistema de archivos, lo que es esencial para leer configuraciones, guardar resultados, manipular datos, etc.

**Diseño Propuesto:**

Se crearán herramientas separadas para leer, escribir, añadir y eliminar archivos, siguiendo el principio de responsabilidad única. Esto hace que las herramientas sean más específicas y fáciles de usar para el LLM.

**Instrucciones de Implementación:**

1.  **Crear el Archivo de la Herramienta:**
    *   **Acción:** Crear un archivo `file_tools.py` dentro de `backend/tools/`.
    *   **Código (`backend/tools/file_tools.py`):**
        ```python
        import os
        from typing import Dict, Any
        from backend.tools.base_tool import Tool

        class FileReadTool(Tool):
            """Herramienta para leer el contenido de un archivo de texto.
            Útil para inspeccionar código, leer configuraciones o datos.
            """
            def __init__(self):
                super().__init__(
                    name="file_read",
                    description="Lee el contenido de un archivo de texto. Devuelve el contenido del archivo.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "La ruta absoluta o relativa al archivo a leer."
                            }
                        },
                        "required": ["path"]
                    }
                )

            def run(self, path: str) -> Dict[str, Any]:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    return {"status": "success", "content": content}
                except FileNotFoundError:
                    return {"status": "error", "message": f"Archivo no encontrado: {path}"}
                except Exception as e:
                    return {"status": "error", "message": f"Error al leer el archivo {path}: {str(e)}"}

        class FileWriteTool(Tool):
            """Herramienta para escribir (sobrescribir) contenido en un archivo de texto.
            Útil para crear o actualizar archivos.
            """
            def __init__(self):
                super().__init__(
                    name="file_write",
                    description="Escribe (sobrescribe) contenido en un archivo de texto. Crea el archivo si no existe.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "La ruta absoluta o relativa al archivo a escribir."
                            },
                            "content": {
                                "type": "string",
                                "description": "El contenido a escribir en el archivo."
                            }
                        },
                        "required": ["path", "content"]
                    }
                )

            def run(self, path: str, content: str) -> Dict[str, Any]:
                try:
                    # Asegurarse de que el directorio exista
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    return {"status": "success", "message": f"Archivo {path} escrito exitosamente."}
                except Exception as e:
                    return {"status": "error", "message": f"Error al escribir en el archivo {path}: {str(e)}"}

        class FileAppendTool(Tool):
            """Herramienta para añadir contenido al final de un archivo de texto.
            Útil para añadir logs o resultados incrementales.
            """
            def __init__(self):
                super().__init__(
                    name="file_append",
                    description="Añade contenido al final de un archivo de texto. Crea el archivo si no existe.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "La ruta absoluta o relativa al archivo."
                            },
                            "content": {
                                "type": "string",
                                "description": "El contenido a añadir al archivo."
                            }
                        },
                        "required": ["path", "content"]
                    }
                )

            def run(self, path: str, content: str) -> Dict[str, Any]:
                try:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "a", encoding="utf-8") as f:
                        f.write(content)
                    return {"status": "success", "message": f"Contenido añadido a {path} exitosamente."}
                except Exception as e:
                    return {"status": "error", "message": f"Error al añadir contenido a {path}: {str(e)}"}

        class FileDeleteTool(Tool):
            """Herramienta para eliminar un archivo.
            Útil para limpiar archivos temporales o no deseados.
            """
            def __init__(self):
                super().__init__(
                    name="file_delete",
                    description="Elimina un archivo del sistema de archivos.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "La ruta absoluta o relativa al archivo a eliminar."
                            }
                        },
                        "required": ["path"]
                    }
                )

            def run(self, path: str) -> Dict[str, Any]:
                try:
                    os.remove(path)
                    return {"status": "success", "message": f"Archivo {path} eliminado exitosamente."}
                except FileNotFoundError:
                    return {"status": "error", "message": f"Archivo no encontrado: {path}"}
                except Exception as e:
                    return {"status": "error", "message": f"Error al eliminar el archivo {path}: {str(e)}"}
        ```

2.  **Registrar las Herramientas en `agent_core.py`:**
    *   **Acción:** Importar las nuevas herramientas de archivo en `agent_core.py` y registrar sus instancias en el `ToolRegistry`.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...
        from backend.tools.file_tools import FileReadTool, FileWriteTool, FileAppendTool, FileDeleteTool # Nuevo import

        class MitosisAgent:
            # ... __init__ existente ...

            def _register_initial_tools(self):
                """Registra las herramientas básicas del agente.
                """
                self.tool_registry.register_tool(ShellTool())
                self.tool_registry.register_tool(FileReadTool())
                self.tool_registry.register_tool(FileWriteTool())
                self.tool_registry.register_tool(FileAppendTool())
                self.tool_registry.register_tool(FileDeleteTool())
                # ... se añadirán más herramientas aquí ...
        ```

### 2.3. Herramientas de Interacción Web (`WebSearchTool`, `WebBrowseTool`)

**Objetivo:** Dotar al agente de la capacidad de buscar información en la web y de navegar por páginas web para extraer contenido. Esto es crucial para la investigación, la recopilación de datos y la interacción con servicios en línea.

**Diseño Propuesto:**

Se utilizará una biblioteca de búsqueda web (como `requests` para peticiones HTTP y `BeautifulSoup` para parsear HTML) para `WebBrowseTool`. Para `WebSearchTool`, se puede integrar con una API de búsqueda (como Google Search API o una alternativa gratuita si es posible).

**Instrucciones de Implementación:**

1.  **Instalar Dependencias Adicionales:**
    *   **Acción:** Añadir `requests` y `beautifulsoup4` al `requirements.txt` y asegurarse de que estén instaladas.
    *   **Comando Sugerido:** `pip install requests beautifulsoup4`

2.  **Crear el Archivo de la Herramienta:**
    *   **Acción:** Crear un archivo `web_tools.py` dentro de `backend/tools/`.
    *   **Código (`backend/tools/web_tools.py`):**
        ```python
        import requests
        from bs4 import BeautifulSoup
        from typing import Dict, Any
        from backend.tools.base_tool import Tool

        class WebSearchTool(Tool):
            """Herramienta para realizar búsquedas en la web.
            Requiere una API de búsqueda (ej. Google Custom Search API, SerpApi, etc.).
            Para simplificar, aquí se muestra un placeholder. En una implementación real, se integraría con una API.
            """
            def __init__(self):
                super().__init__(
                    name="web_search",
                    description="Realiza una búsqueda en la web y devuelve los títulos y URLs de los primeros resultados. Útil para investigar y encontrar información.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "La consulta de búsqueda."
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Número máximo de resultados a devolver. Por defecto es 5.",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                )

            def run(self, query: str, num_results: int = 5) -> Dict[str, Any]:
                # ESTO ES UN PLACEHOLDER. EN UNA IMPLEMENTACIÓN REAL, SE USARÍA UNA API DE BÚSQUEDA.
                # Ejemplo con una búsqueda simulada o una API gratuita limitada:
                try:
                    # Simulación de búsqueda (reemplazar con una API real)
                    print(f"DEBUG: Realizando búsqueda web para: {query}")
                    results = [
                        {"title": f"Resultado 1 para {query}", "url": "https://example.com/result1"},
                        {"title": f"Resultado 2 para {query}", "url": "https://example.com/result2"},
                        {"title": f"Resultado 3 para {query}", "url": "https://example.com/result3"},
                    ]
                    return {"status": "success", "results": results[:num_results]}
                except Exception as e:
                    return {"status": "error", "message": f"Error al realizar la búsqueda web: {str(e)}"}

        class WebBrowseTool(Tool):
            """Herramienta para navegar a una URL y extraer su contenido principal.
            Útil para leer artículos, documentación o extraer datos de páginas web.
            """
            def __init__(self):
                super().__init__(
                    name="web_browse",
                    description="Navega a una URL y extrae el contenido principal de la página (texto visible). Útil para leer el contenido de un enlace.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "La URL de la página web a navegar."
                            }
                        },
                        "required": ["url"]
                    }
                )

            def run(self, url: str) -> Dict[str, Any]:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP erróneos

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Eliminar scripts y estilos
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Obtener texto de la página
                    text = soup.get_text()

                    # Limpiar espacios en blanco excesivos
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)

                    return {"status": "success", "content": text[:4000]} # Limitar a 4000 caracteres para evitar sobrecarga
                except requests.exceptions.RequestException as e:
                    return {"status": "error", "message": f"Error de red o HTTP al navegar a {url}: {str(e)}"}
                except Exception as e:
                    return {"status": "error", "message": f"Error al procesar la página {url}: {str(e)}"}
        ```

3.  **Registrar las Herramientas en `agent_core.py`:**
    *   **Acción:** Importar las nuevas herramientas web en `agent_core.py` y registrar sus instancias en el `ToolRegistry`.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...
        from backend.tools.web_tools import WebSearchTool, WebBrowseTool # Nuevo import

        class MitosisAgent:
            # ... __init__ existente ...

            def _register_initial_tools(self):
                """Registra las herramientas básicas del agente.
                """
                self.tool_registry.register_tool(ShellTool())
                self.tool_registry.register_tool(FileReadTool())
                self.tool_registry.register_tool(FileWriteTool())
                self.tool_registry.register_tool(FileAppendTool())
                self.tool_registry.register_tool(FileDeleteTool())
                self.tool_registry.register_tool(WebSearchTool())
                self.tool_registry.register_tool(WebBrowseTool())
                # ... se añadirán más herramientas aquí ...
        ```

Al completar esta fase, el agente MitosisV6 tendrá la capacidad de ejecutar comandos de shell, manipular archivos y realizar búsquedas/navegación web. Estas herramientas son la base para que el agente pueda interactuar con el mundo real y dejar de "simular" la ejecución de tareas. La siguiente fase se centrará en integrar estas herramientas en el bucle de ejecución de fases del agente.



## Fase 3: Rediseño del Bucle de Ejecución de Fases con Tool-Use

### Objetivo de la Fase

El objetivo más crítico de esta fase es transformar la ejecución de las fases de una "simulación" basada en LLM a una interacción real con el entorno a través de las herramientas implementadas en la Fase 2. Esto implica un rediseño fundamental del método `execute_current_phase` en `agent_core.py` para implementar un bucle iterativo de razonamiento-acción-observación (ReAct).

### 3.1. Modificación del Bucle de Ejecución de Fases

**Objetivo:** Implementar un bucle ReAct dentro de cada fase de la tarea, permitiendo al agente pensar, usar herramientas, observar los resultados y repetir hasta que la fase se complete o se encuentre un obstáculo insuperable.

**Diseño Propuesto:**

El método `execute_current_phase` dejará de ser una simple llamada al LLM para generar una respuesta de texto. En su lugar, se convertirá en un orquestador que:

1.  **Genera un prompt** para el LLM que incluye la descripción de la fase, el contexto actual y las herramientas disponibles (con sus esquemas JSON).
2.  **Obtiene una respuesta del LLM** que debe ser una llamada a una herramienta, una indicación de finalización de fase o una solicitud de información.
3.  **Parsea la respuesta** para determinar la acción a tomar.
4.  **Ejecuta la herramienta** si es una llamada a herramienta.
5.  **Registra el resultado** de la herramienta en el contexto de la fase.
6.  **Repite** el proceso hasta que la fase se complete o se agoten los intentos.

**Instrucciones de Implementación:**

1.  **Actualizar `MitosisAgent` en `backend/agent_core.py`:**
    *   **Acción:** Modificar el método `execute_current_phase` para implementar el bucle ReAct. Se añadirán métodos auxiliares para la ejecución de herramientas y el manejo de los resultados.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...
        from backend.tools.tool_registry import ToolRegistry
        from backend.tools.base_tool import Tool # Asegurarse de importar Tool
        import json
        # ... otras clases y dataclasses ...

        class MitosisAgent:
            # ... __init__ y otros métodos ...

            async def execute_current_phase(self, task_id: Optional[str] = None) -> str:
                """Ejecuta la fase actual de una tarea utilizando un bucle de razonamiento-acción-observación (ReAct)."""
                try:
                    self.state = AgentState.EXECUTING

                    if task_id:
                        task = self.task_manager.get_task(task_id)
                    else:
                        task = self.task_manager.get_current_task()

                    if not task:
                        return "Error: No hay tarea activa para ejecutar."

                    current_phase = self.task_manager.get_current_phase(task.id)
                    if not current_phase:
                        return "Error: No hay fase activa en la tarea."

                    self.logger.info(f"Iniciando ejecución de fase {current_phase.id}: {current_phase.title} para tarea {task.id}")

                    # Inicializar el historial de la fase para el contexto del LLM
                    if "execution_history" not in current_phase.results:
                        current_phase.results["execution_history"] = []

                    max_tool_iterations = 10 # Límite para evitar bucles infinitos
                    iteration_count = 0
                    phase_completed = False
                    last_tool_result = ""

                    while iteration_count < max_tool_iterations and not phase_completed:
                        iteration_count += 1
                        self.logger.info(f"Fase {current_phase.id}, Iteración {iteration_count}")

                        # 1. Razonamiento: Generar prompt para que el LLM decida la siguiente acción
                        # El contexto actual incluirá el historial de herramientas usadas y sus resultados
                        current_context_for_llm = self._format_execution_history(current_phase.results["execution_history"])
                        if last_tool_result:
                            current_context_for_llm += f"\nÚltimo resultado de herramienta: {last_tool_result}"

                        tool_use_prompt = self.prompt_manager.generate_tool_use_prompt(
                            task, current_phase, current_context_for_llm
                        )

                        # Seleccionar modelo para la toma de decisiones (puede ser el mismo que para planificación)
                        decision_model = self.model_manager.select_best_model(
                            task_type="analysis",
                            max_cost=self.config.max_cost_per_1k_tokens
                        )

                        if not decision_model:
                            return "Error: No hay modelos disponibles para la toma de decisiones de herramientas."

                        # Obtener la respuesta del LLM (debe ser una llamada a herramienta o una acción)
                        llm_response = self.model_manager.generate_response(
                            tool_use_prompt,
                            model=decision_model,
                            max_tokens=1000, # Suficientes tokens para la llamada a herramienta JSON
                            temperature=0.2 # Baja temperatura para respuestas más deterministas
                        )

                        if not llm_response:
                            self.logger.error("El LLM no generó una respuesta para la decisión de herramienta.")
                            break # Salir del bucle de la fase

                        # 2. Parseo de la Acción: Extraer la herramienta y los argumentos
                        action_data = self._parse_tool_call(llm_response)

                        action_type = action_data.get("action")
                        tool_name = action_data.get("tool_name")
                        tool_args = action_data.get("tool_args", {})

                        if action_type == "finish_phase":
                            phase_completed = True
                            final_result = action_data.get("result", "Fase completada por decisión del agente.")
                            current_phase.results["final_phase_result"] = final_result
                            self.logger.info(f"Agente decidió completar la fase: {final_result}")
                            break
                        elif action_type == "request_info":
                            reason = action_data.get("reason", "El agente necesita más información.")
                            self.logger.warning(f"Agente solicitó más información: {reason}")
                            self.state = AgentState.WAITING_USER
                            return f"Fase {current_phase.id} pausada. El agente necesita más información: {reason}"
                        elif tool_name:
                            # 3. Acción: Ejecutar la herramienta
                            self.logger.info(f"Ejecutando herramienta: {tool_name} con argumentos: {tool_args}")
                            tool_result_data = self._execute_tool(tool_name, tool_args)
                            last_tool_result = json.dumps(tool_result_data) # Para el siguiente prompt

                            # 4. Observación: Registrar el resultado de la herramienta
                            current_phase.results["execution_history"].append({
                                "iteration": iteration_count,
                                "thought": llm_response, # La respuesta del LLM que llevó a la acción
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "tool_result": tool_result_data,
                                "timestamp": time.time()
                            })
                            self.logger.info(f"Resultado de herramienta: {tool_result_data.get("status")}")

                            if tool_result_data.get("status") == "error":
                                self.logger.error(f"Error en herramienta {tool_name}: {tool_result_data.get("message")}")
                                # Aquí se podría invocar el manejo de errores o reintentar
                                # Por ahora, simplemente se registra y se continúa o se falla la fase
                                # break # Opcional: salir del bucle si hay un error crítico
                        else:
                            self.logger.error(f"Respuesta del LLM no reconocida: {llm_response}")
                            break # Salir del bucle si la respuesta no es válida

                    # Después del bucle de iteraciones de herramientas
                    if phase_completed:
                        # Avanzar a la siguiente fase
                        next_phase_id = current_phase.id + 1
                        if next_phase_id <= len(task.phases):
                            self.task_manager.advance_phase(task.id, current_phase.id, next_phase_id, current_phase.results)
                            self.state = AgentState.IDLE
                            return f"Fase {current_phase.id} completada. Avanzando a fase {next_phase_id}."
                        else:
                            # Completar tarea
                            self.task_manager.complete_task(task.id, current_phase.results)
                            self.stats["tasks_completed"] += 1
                            self.state = AgentState.IDLE
                            return f"Tarea \'{task.title}\' completada exitosamente."
                    else:
                        # Si el bucle terminó sin completar la fase (ej. max_tool_iterations alcanzado)
                        self.task_manager.fail_task(task.id, f"Fase {current_phase.id} no completada después de {max_tool_iterations} iteraciones de herramientas.")
                        self.state = AgentState.ERROR
                        return f"Fase {current_phase.id} no completada. Revise los logs para más detalles."

                except Exception as e:
                    self.logger.error(f"Error al ejecutar fase: {e}", exc_info=True)
                    self.state = AgentState.ERROR
                    self.task_manager.fail_task(task.id, f"Error inesperado durante la ejecución de la fase: {str(e)}")
                    return f"Error al ejecutar fase: {str(e)}"

            def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
                """Ejecuta una herramienta registrada y devuelve su resultado."""
                try:
                    tool = self.tool_registry.get_tool(tool_name)
                    result = tool.run(**tool_args)
                    return result
                except ValueError as e:
                    self.logger.error(f"Error al obtener la herramienta {tool_name}: {e}")
                    return {"status": "error", "message": f"Herramienta no encontrada o inválida: {tool_name}"}
                except Exception as e:
                    self.logger.error(f"Error al ejecutar la herramienta {tool_name}: {e}", exc_info=True)
                    return {"status": "error", "message": f"Error durante la ejecución de la herramienta {tool_name}: {str(e)}"}

            def _format_execution_history(self, history: List[Dict[str, Any]]) -> str:
                """Formatea el historial de ejecución de herramientas para incluirlo en el prompt del LLM."""
                formatted_history = []
                for entry in history:
                    formatted_history.append(f"Iteración {entry['iteration']}:\n")
                    formatted_history.append(f"  Pensamiento del LLM: {entry['thought']}\n")
                    formatted_history.append(f"  Herramienta Usada: {entry['tool_name']}({json.dumps(entry['tool_args'])})\n")
                    formatted_history.append(f"  Resultado: {json.dumps(entry['tool_result'])}\n")
                return "\n".join(formatted_history)

            # ... resto de la clase ...
        ```

### 3.2. Actualización de `TaskManager` y `TaskPhase`

**Objetivo:** Asegurar que el `TaskManager` pueda almacenar el historial de ejecución de herramientas dentro de cada fase y que la estructura de `TaskPhase` sea adecuada para este nuevo contexto.

**Diseño Propuesto:**

La clase `TaskPhase` ya tiene un campo `results` que es un diccionario, lo cual es adecuado para almacenar el `execution_history`. No se requieren cambios estructurales importantes, pero es importante entender cómo se utilizará.

**Instrucciones de Implementación:**

1.  **Verificar `TaskPhase` en `backend/task_manager.py`:**
    *   **Acción:** Confirmar que `TaskPhase` puede almacenar un diccionario en su campo `results`. El campo `execution_history` se almacenará dentro de este diccionario.
    *   **Código (`backend/task_manager.py` - verificar):**
        ```python
        @dataclass
        class TaskPhase:
            # ... campos existentes ...
            results: Dict[str, Any] = None # Asegurarse de que sea un diccionario
            # ...
            def __post_init__(self):
                if self.results is None:
                    self.results = {}
        ```

### 3.3. Refinamiento del `EnhancedPromptManager`

**Objetivo:** Asegurar que el `EnhancedPromptManager` genere prompts claros y efectivos para el bucle de tool-use, incluyendo las descripciones de las herramientas y el historial de ejecución.

**Diseño Propuesto:**

El método `generate_tool_use_prompt` ya fue esbozado en la Fase 1. Ahora se debe asegurar que el formato de las herramientas sea el más adecuado para el LLM que se esté utilizando (por ejemplo, OpenAI Function Calling format si se usa un modelo compatible, o un formato JSON personalizado como el propuesto).

**Instrucciones de Implementación:**

1.  **Revisar `generate_tool_use_prompt` en `backend/enhanced_prompts.py`:**
    *   **Acción:** Asegurarse de que el prompt sea lo suficientemente claro para guiar al LLM a generar la respuesta en el formato JSON esperado para la llamada a herramientas o las acciones de control (`finish_phase`, `request_info`). Es crucial que el LLM entienda que **solo debe responder con el JSON**.
    *   **Consideraciones:**
        *   **Claridad en el Formato de Salida:** Enfatizar que la respuesta debe ser *solo* el JSON. Los LLMs a veces añaden texto explicativo. Se puede usar `json.loads` con un manejo de errores robusto en `_parse_tool_call` para intentar extraer el JSON incluso si hay texto extra.
        *   **Ejemplos en el Prompt:** Considerar añadir ejemplos de llamadas a herramientas y de las acciones `finish_phase` y `request_info` directamente en el prompt para guiar al LLM.

### 3.4. Pruebas Unitarias y de Integración para el Bucle de Ejecución

**Objetivo:** Validar que el nuevo bucle de ejecución de fases funciona correctamente, que las herramientas se invocan y que los resultados se procesan adecuadamente.

**Instrucciones de Implementación:**

1.  **Crear Mocks para Herramientas y LLM:**
    *   **Acción:** Para las pruebas unitarias, crear versiones "mock" de las herramientas y del `ModelManager` que devuelvan resultados predefinidos. Esto permite probar la lógica del bucle sin depender de la ejecución real de comandos o llamadas a APIs externas.

2.  **Escribir Pruebas para `execute_current_phase`:**
    *   **Acción:** Crear un nuevo archivo de prueba (ej. `test_phase_execution.py` en `tests/`) que:
        *   Inicialice `MitosisAgent` con mocks.
        *   Cree una tarea con una o más fases.
        *   Simule respuestas del LLM que incluyan llamadas a herramientas.
        *   Verifique que las herramientas mock se invocan con los argumentos correctos.
        *   Verifique que el historial de ejecución se registra correctamente.
        *   Verifique que la fase avanza o se completa según lo esperado.
        *   Pruebe escenarios de error (ej. LLM genera JSON inválido, herramienta falla).

Al finalizar esta fase, el agente MitosisV6 tendrá un "cuerpo" funcional capaz de interactuar con el mundo exterior a través de herramientas. Este es un hito crucial para su autonomía. La siguiente fase se centrará en hacer que la planificación de tareas sea más robusta y menos dependiente de la perfección del LLM.



## Fase 4: Mejora de la Robustez de la Planificación de Tareas

### Objetivo de la Fase

El objetivo de esta fase es hacer que el proceso de planificación de tareas sea significativamente más robusto y menos propenso a fallar debido a la generación de JSON inválido o incompleto por parte del LLM. Esto es crucial para la fiabilidad del agente, ya que un plan defectuoso puede llevar a una ejecución fallida o ineficiente. Se implementarán mecanismos de validación y reintento con retroalimentación para guiar al LLM hacia la generación de planes de alta calidad.

### 4.1. Definición y Validación del Esquema JSON para Planes de Tarea

**Objetivo:** Establecer un esquema formal para la estructura de los planes de tarea generados por el LLM y utilizarlo para validar la salida del LLM. Esto asegura que los planes sean siempre parseables y contengan la información necesaria.

**Diseño Propuesto:**

Se definirá un esquema JSON utilizando la especificación JSON Schema. Se utilizará una biblioteca de Python (`jsonschema`) para realizar la validación. Este esquema se incluirá en el prompt del LLM para guiar su generación.

**Instrucciones de Implementación:**

1.  **Instalar Dependencia:**
    *   **Acción:** Añadir `jsonschema` al `requirements.txt` e instalarlo.
    *   **Comando Sugerido:** `pip install jsonschema`

2.  **Definir el Esquema JSON del Plan de Tarea:**
    *   **Acción:** Crear un nuevo archivo `task_plan_schema.py` dentro de `backend/` que contenga la definición del esquema JSON. Este esquema debe reflejar la estructura esperada por las clases `Task` y `TaskPhase` en `task_manager.py`.
    *   **Código (`backend/task_plan_schema.py`):**
        ```python
        TASK_PLAN_SCHEMA = {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "El objetivo reformulado de la tarea."},
                "phases": {
                    "type": "array",
                    "description": "Lista ordenada de fases para completar la tarea.",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer", "description": "ID único de la fase (debe ser secuencial, empezando por 1)."},
                            "title": {"type": "string", "description": "Título conciso de la fase."},
                            "description": {"type": "string", "description": "Descripción detallada de lo que se debe lograr en esta fase."},
                            "required_capabilities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de capacidades o habilidades requeridas para esta fase (ej. 'coding', 'research', 'file_io')."
                            },
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Lista de IDs de fases de las que esta fase depende (opcional)."
                            },
                            "estimated_duration": {"type": "string", "description": "Estimación de tiempo para completar la fase (ej. '2 horas', '1 día')."},
                            "success_criteria": {"type": "string", "description": "Criterios claros y verificables para determinar el éxito de la fase."}
                        },
                        "required": ["id", "title", "description", "required_capabilities", "success_criteria"]
                    }
                }
            },
            "required": ["goal", "phases"]
        }
        ```

3.  **Integrar la Validación en `agent_core.py`:**
    *   **Acción:** Modificar la función `create_and_execute_task` para utilizar el esquema JSON y validar la respuesta del LLM. Se importará `jsonschema` y el esquema definido.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...
        import jsonschema
        from backend.task_plan_schema import TASK_PLAN_SCHEMA # Nuevo import

        class MitosisAgent:
            # ... __init__ y otros métodos ...

            def create_and_execute_task(self, title: str, description: str, goal: str,
                                       auto_execute: bool = True) -> str:
                try:
                    self.state = AgentState.PLANNING

                    # Bucle de reintento para la planificación
                    max_planning_retries = 3
                    plan_data = None
                    validation_error_message = None

                    for attempt in range(max_planning_retries):
                        # Generar prompt del sistema con contexto y esquema JSON
                        planning_prompt = self.prompt_manager.generate_task_planning_prompt(
                            goal=goal,
                            description=description,
                            context=f"Título: {title}",
                            json_schema=TASK_PLAN_SCHEMA, # Pasar el esquema al prompt manager
                            validation_error=validation_error_message # Pasar el error de validación si existe
                        )

                        # Seleccionar modelo para planificación
                        planning_model = self.model_manager.select_best_model(
                            task_type="analysis",
                            max_cost=self.config.max_cost_per_1k_tokens
                        )

                        if not planning_model:
                            return "Error: No hay modelos disponibles para planificación."

                        # Generar plan
                        plan_response = self.model_manager.generate_response(
                            planning_prompt,
                            model=planning_model,
                            max_tokens=1500,
                            temperature=0.3
                        )

                        if not plan_response:
                            validation_error_message = "El LLM no generó ninguna respuesta para el plan."
                            self.logger.warning(f"Intento {attempt+1}: {validation_error_message}")
                            continue

                        try:
                            # Extraer JSON del response si está envuelto en texto
                            start_idx = plan_response.find("{")
                            end_idx = plan_response.rfind("}") + 1
                            if start_idx != -1 and end_idx != 0:
                                plan_json_str = plan_response[start_idx:end_idx]
                                plan_data = json.loads(plan_json_str)
                            else:
                                raise json.JSONDecodeError("No se encontró JSON válido en la respuesta.", plan_response, 0)

                            # Validar el JSON contra el esquema
                            jsonschema.validate(instance=plan_data, schema=TASK_PLAN_SCHEMA)
                            self.logger.info(f"Plan de tarea generado y validado exitosamente en el intento {attempt+1}.")
                            break # Salir del bucle si el plan es válido

                        except (json.JSONDecodeError, jsonschema.ValidationError) as e:
                            validation_error_message = f"El plan generado no es un JSON válido o no cumple con el esquema: {e}. Por favor, corrige el formato y la estructura."
                            self.logger.warning(f"Intento {attempt+1}: {validation_error_message}")
                            plan_data = None # Resetear plan_data para el siguiente intento

                    if plan_data is None:
                        self.logger.error("Todos los intentos de planificación fallaron. Recurriendo al plan de respaldo.")
                        # Plan de respaldo si todos los intentos fallan
                        plan_data = {
                            "goal": goal,
                            "phases": [
                                {"id": 1, "title": "Análisis Inicial", "description": description, "required_capabilities": ["analysis"], "success_criteria": "Análisis completado."},
                                {"id": 2, "title": "Ejecución General", "description": "Ejecutar la tarea principal", "required_capabilities": ["general"], "success_criteria": "Tarea ejecutada."},
                                {"id": 3, "title": "Entrega de Resultados", "description": "Entregar los resultados al usuario", "required_capabilities": ["communication"], "success_criteria": "Resultados entregados."}
                            ]
                        }

                    # Crear tarea (el resto del código es similar al existente)
                    task_id = self.task_manager.create_task(
                        title=title,
                        description=description,
                        goal=goal,
                        phases=plan_data.get("phases", []),
                        context={"plan_response": plan_response if plan_response else "Plan de respaldo usado"}
                    )

                    # ... resto de la función ...

                except Exception as e:
                    self.logger.error(f"Error al crear/ejecutar tarea: {e}", exc_info=True)
                    self.state = AgentState.ERROR
                    return f"Error al crear tarea: {str(e)}"
        ```

### 4.2. Refinamiento del Prompt de Planificación

**Objetivo:** Mejorar el prompt de planificación para que el LLM sea más propenso a generar planes válidos y de alta calidad, especialmente cuando se le proporciona retroalimentación sobre errores de validación.

**Diseño Propuesto:**

El `EnhancedPromptManager` se actualizará para aceptar el esquema JSON y cualquier mensaje de error de validación, incorporándolos directamente en el prompt para guiar al LLM.

**Instrucciones de Implementación:**

1.  **Modificar `generate_task_planning_prompt` en `backend/enhanced_prompts.py`:**
    *   **Acción:** Añadir parámetros para el esquema JSON y el mensaje de error de validación. Incluir estos en el prompt de manera clara.
    *   **Cambios en `backend/enhanced_prompts.py` (fragmento):**
        ```python
        # ... imports existentes ...
        import json
        # ... otras clases y dataclasses ...

        class EnhancedPromptManager:
            # ... __init__ existente ...

            def generate_task_planning_prompt(self, goal: str, description: str = "", 
                                            context: str = "", resources: str = "",
                                            json_schema: Optional[Dict[str, Any]] = None,
                                            validation_error: Optional[str] = None) -> str:
                """Genera un prompt optimizado para planificación de tareas.
                Incluye el esquema JSON esperado y retroalimentación de errores de validación.
                """
                template = self.prompt_templates.get("task_planning", "")
                optimized_template = self._apply_optimizations("task_planning", template)

                schema_str = ""
                if json_schema:
                    schema_str = f"\n\nEl plan DEBE seguir estrictamente el siguiente esquema JSON:\n```json\n{json.dumps(json_schema, indent=2)}\n```\n"

                error_feedback = ""
                if validation_error:
                    error_feedback = f"\n\nATENCIÓN: El plan generado anteriormente no fue válido. Error: {validation_error}\nPor favor, genera un nuevo plan que cumpla estrictamente con el formato JSON y el esquema proporcionados. No incluyas texto adicional fuera del bloque JSON.\n"

                # Asegurarse de que el prompt original tenga un placeholder para el esquema y el error
                # Si no lo tiene, añadirlo al final o en un lugar lógico.
                # Para este ejemplo, asumimos que el template base ya puede manejarlo o lo añadimos.
                full_prompt = f"""{optimized_template}
{schema_str}
{error_feedback}"""

                return full_prompt.format(
                    goal=goal,
                    description=description,
                    context=context,
                    resources=resources
                )

            # ... resto de la clase ...
        ```

### 4.3. Mejora del Plan de Respaldo

**Objetivo:** Asegurar que, incluso si el LLM falla repetidamente en generar un plan válido, el agente pueda recurrir a un plan de respaldo más útil y estructurado que el genérico actual.

**Diseño Propuesto:**

El plan de respaldo se hará más detallado y adaptable, incluyendo fases más significativas y criterios de éxito básicos. Se podría incluso considerar un pequeño LLM local para generar un plan de respaldo más inteligente si el principal falla.

**Instrucciones de Implementación:**

1.  **Actualizar el Plan de Respaldo en `agent_core.py`:**
    *   **Acción:** Modificar la sección del plan de respaldo en `create_and_execute_task` para que sea más útil. Las fases deben ser lo suficientemente genéricas como para aplicarse a una amplia gama de tareas, pero lo suficientemente específicas como para guiar la ejecución.
    *   **Cambios en `backend/agent_core.py` (fragmento - dentro de `create_and_execute_task`):**
        ```python
        # ... código existente ...

                    if plan_data is None:
                        self.logger.error("Todos los intentos de planificación fallaron. Recurriendo al plan de respaldo.")
                        # Plan de respaldo mejorado
                        plan_data = {
                            "goal": goal,
                            "phases": [
                                {"id": 1, "title": "Análisis y Comprensión del Problema", 
                                 "description": "Investigar y comprender a fondo el problema o la solicitud del usuario, identificando los requisitos clave y los posibles enfoques.", 
                                 "required_capabilities": ["research", "analysis"], 
                                 "success_criteria": "Documento de requisitos y enfoque inicial definido."},
                                {"id": 2, "title": "Diseño de la Solución", 
                                 "description": "Diseñar una solución detallada para el problema, incluyendo la identificación de herramientas necesarias y la estructura de los pasos a seguir.", 
                                 "required_capabilities": ["design", "planning"], 
                                 "success_criteria": "Diseño de solución y lista de herramientas requeridas."},
                                {"id": 3, "title": "Implementación y Ejecución", 
                                 "description": "Llevar a cabo la implementación de la solución utilizando las herramientas disponibles y ejecutando los pasos definidos en el diseño.", 
                                 "required_capabilities": ["general", "tool_use"], 
                                 "success_criteria": "Solución implementada y resultados preliminares obtenidos."},
                                {"id": 4, "title": "Verificación y Refinamiento", 
                                 "description": "Verificar los resultados obtenidos, identificar posibles errores o áreas de mejora, y refinar la solución hasta que cumpla con los criterios de éxito.", 
                                 "required_capabilities": ["testing", "analysis"], 
                                 "success_criteria": "Resultados verificados y solución finalizada."},
                                {"id": 5, "title": "Entrega y Documentación", 
                                 "description": "Preparar y entregar los resultados finales al usuario, incluyendo cualquier documentación relevante o explicación del proceso.", 
                                 "required_capabilities": ["communication", "documentation"], 
                                 "success_criteria": "Resultados entregados y documentación completa."}
                            ]
                        }

                    # ... resto de la función ...
        ```

### 4.4. Pruebas de Robustez de la Planificación

**Objetivo:** Validar que los mecanismos de validación y reintento funcionan correctamente y que el agente puede recuperarse de la generación de planes inválidos.

**Instrucciones de Implementación:**

1.  **Crear Escenarios de Prueba:**
    *   **Acción:** En el módulo de pruebas, crear casos de prueba que simulen las siguientes situaciones:
        *   El LLM genera un JSON perfectamente válido en el primer intento.
        *   El LLM genera un JSON inválido (ej. sintaxis incorrecta) en el primer intento, pero lo corrige en un reintento.
        *   El LLM genera un JSON válido sintácticamente pero que no cumple con el esquema (ej. falta un campo requerido) en el primer intento, y lo corrige en un reintento.
        *   El LLM falla repetidamente en generar un JSON válido, y el agente recurre al plan de respaldo.

2.  **Mocks para `ModelManager`:**
    *   **Acción:** Utilizar mocks para el `ModelManager` que puedan simular las respuestas del LLM, incluyendo respuestas inválidas en los primeros intentos y respuestas válidas en los posteriores, o respuestas consistentemente inválidas.

Al completar esta fase, el agente MitosisV6 será mucho más resiliente a las imperfecciones en la generación de texto por parte del LLM durante la planificación, asegurando que siempre opere con un plan estructurado y válido. La siguiente fase se centrará en la evolución del sistema de memoria para permitir búsquedas semánticas y una extracción de conocimiento más inteligente.



## Fase 5: Evolución del Sistema de Memoria (Búsqueda Semántica y Extracción de Conocimiento)

### Objetivo de la Fase

El objetivo de esta fase es transformar el sistema de memoria del agente MitosisV6 de una base de datos de conocimiento basada en palabras clave a una que soporte la búsqueda semántica y la extracción de conocimiento más inteligente. Esto permitirá al agente recuperar información relevante basándose en el significado, no solo en la coincidencia exacta de términos, y aprender de manera más efectiva de sus interacciones y experiencias. Una memoria más potente es fundamental para un razonamiento más profundo y una toma de decisiones informada.

### 5.1. Implementación de Búsqueda Semántica

**Objetivo:** Reemplazar la búsqueda de conocimiento basada en `LIKE` en `MemoryManager` por una búsqueda semántica utilizando embeddings y una base de datos vectorial. Esto permitirá al agente encontrar conocimiento relevante incluso si la consulta no contiene las palabras exactas del conocimiento almacenado.

**Diseño Propuesto:**

Se utilizará un modelo de embeddings para convertir el contenido textual (consultas y elementos de conocimiento) en vectores numéricos de alta dimensión (embeddings). Estos embeddings se almacenarán en una base de datos vectorial, que permitirá realizar búsquedas de similitud (vecinos más cercanos) de manera eficiente. Para este plan, se propone `ChromaDB` como base de datos vectorial por su facilidad de uso y capacidad de ejecutarse localmente, junto con la biblioteca `sentence-transformers` para generar embeddings.

**Instrucciones de Implementación:**

1.  **Instalar Dependencias:**
    *   **Acción:** Añadir `chromadb` y `sentence-transformers` al `requirements.txt` e instalarlos.
    *   **Comando Sugerido:** `pip install chromadb sentence-transformers`

2.  **Crear un Módulo para el Generador de Embeddings:**
    *   **Acción:** Crear un nuevo archivo `embedding_generator.py` dentro de `backend/`.
    *   **Código (`backend/embedding_generator.py`):**
        ```python
        from sentence_transformers import SentenceTransformer
        from typing import List
        import logging

        class EmbeddingGenerator:
            """Genera embeddings vectoriales para texto utilizando un modelo pre-entrenado.
            """
            def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
                self.logger = logging.getLogger(__name__)
                try:
                    self.model = SentenceTransformer(model_name)
                    self.logger.info(f"Modelo de embeddings cargado: {model_name}")
                except Exception as e:
                    self.logger.error(f"Error al cargar el modelo de embeddings {model_name}: {e}")
                    self.model = None

            def generate_embedding(self, text: str) -> List[float]:
                """Genera un embedding para un texto dado.
                Args:
                    text: El texto de entrada.
                Returns:
                    Una lista de flotantes que representa el embedding del texto.
                Raises:
                    RuntimeError: Si el modelo de embeddings no está cargado.
                """
                if self.model is None:
                    raise RuntimeError("El modelo de embeddings no está cargado.")
                return self.model.encode(text).tolist()

            def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
                """Genera embeddings para una lista de textos.
                Args:
                    texts: Una lista de textos de entrada.
                Returns:
                    Una lista de listas de flotantes, donde cada sublista es el embedding de un texto.
                Raises:
                    RuntimeError: Si el modelo de embeddings no está cargado.
                """
                if self.model is None:
                    raise RuntimeError("El modelo de embeddings no está cargado.")
                return self.model.encode(texts).tolist()
        ```

3.  **Modificar `MemoryManager` para Integrar ChromaDB y Embeddings:**
    *   **Acción:** Reestructurar `MemoryManager` para inicializar una colección ChromaDB y utilizar el `EmbeddingGenerator` para almacenar embeddings junto con el contenido del conocimiento. La función `search_knowledge` se adaptará para realizar búsquedas vectoriales.
    *   **Cambios en `backend/memory_manager.py` (fragmento):**
        ```python
        # ... imports existentes ...
        import chromadb
        from chromadb.utils import embedding_functions
        from backend.embedding_generator import EmbeddingGenerator # Nuevo import

        # ... clases Message, TaskMemory, KnowledgeItem existentes ...

        class MemoryManager:
            def __init__(self, db_path: str = "mitosis_memory.db", max_short_term_messages: int = 50):
                self.db_path = db_path
                self.max_short_term_messages = max_short_term_messages
                self.logger = logging.getLogger(__name__)

                self.short_term_memory: List[Message] = []
                self.current_session_id = self._generate_session_id()

                # Inicializar generador de embeddings
                self.embedding_generator = EmbeddingGenerator()

                # Inicializar ChromaDB
                self.chroma_client = chromadb.PersistentClient(path=f"{self.db_path}_chroma")
                # Usar un embedding function que coincida con nuestro generador
                # Nota: ChromaDB puede usar su propio SentenceTransformer, pero para consistencia
                # usaremos nuestro EmbeddingGenerator.
                # Si el modelo de embeddings es grande, se puede considerar cargarlo una sola vez.
                self.knowledge_collection = self.chroma_client.get_or_create_collection(
                    name="knowledge_base_collection",
                    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name="paraphrase-multilingual-MiniLM-L12-v2"
                    ) # Asegurarse de que este modelo coincida con EmbeddingGenerator
                )

                self._init_database() # La base de datos SQLite seguirá almacenando metadatos

                self._knowledge_cache: Dict[str, KnowledgeItem] = {}
                self._cache_max_size = 100

                self.logger.info(f"Gestor de memoria inicializado con ChromaDB en {self.db_path}_chroma")

            # ... _init_database (mantener la tabla knowledge_base para metadatos) ...
            # La tabla knowledge_base en SQLite ahora almacenará el ID de ChromaDB y metadatos, no el embedding en sí.
            # Se podría añadir una columna para el ID de ChromaDB si es diferente del ID de conocimiento.

            def add_knowledge(self, content: str, category: str, source: str,
                             confidence: float = 1.0, tags: Optional[List[str]] = None) -> str:
                """Añade un elemento de conocimiento a la base de datos y a ChromaDB."""
                knowledge_id = hashlib.md5(f"{content}{category}{source}{time.time()}".encode()).hexdigest() # Añadir timestamp para unicidad

                knowledge_item = KnowledgeItem(
                    id=knowledge_id,
                    content=content,
                    category=category,
                    source=source,
                    confidence=confidence,
                    created_at=time.time(),
                    tags=tags or []
                )

                try:
                    # Añadir a ChromaDB
                    self.knowledge_collection.add(
                        documents=[content],
                        metadatas=[asdict(knowledge_item)], # Almacenar metadatos completos
                        ids=[knowledge_id]
                    )

                    # Añadir metadatos a la base de datos SQLite (sin el contenido completo ni el embedding)
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT OR REPLACE INTO knowledge_base
                        (id, category, source, confidence, created_at, accessed_count, last_accessed, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        knowledge_item.id,
                        knowledge_item.category,
                        knowledge_item.source,
                        knowledge_item.confidence,
                        knowledge_item.created_at,
                        knowledge_item.accessed_count,
                        knowledge_item.last_accessed,
                        json.dumps(knowledge_item.tags)
                    ))

                    conn.commit()
                    conn.close()

                    # Actualizar cache
                    self._knowledge_cache[knowledge_id] = knowledge_item
                    self._manage_cache_size()

                    self.logger.info(f"Conocimiento añadido: {knowledge_id}")
                    return knowledge_id

                except Exception as e:
                    self.logger.error(f"Error al añadir conocimiento: {e}")
                    return ""

            def search_knowledge(self, query: str, category: Optional[str] = None,
                                limit: int = 10, min_confidence: float = 0.5) -> List[KnowledgeItem]:
                """Busca elementos de conocimiento relevantes utilizando búsqueda semántica."""
                try:
                    # Realizar búsqueda vectorial en ChromaDB
                    results = self.knowledge_collection.query(
                        query_texts=[query],
                        n_results=limit,
                        where={
                            "category": category
                        } if category else {}
                        # ChromaDB también permite filtrar por metadatos, lo que es útil para la confianza y tags
                        # Sin embargo, el filtrado por confianza en ChromaDB requeriría almacenar la confianza como metadato numérico
                    )

                    knowledge_items = []
                    if results and results["ids"]:
                        for i, doc_id in enumerate(results["ids"][0]):
                            metadata = results["metadatas"][0][i]
                            # Reconstruir KnowledgeItem desde los metadatos de ChromaDB
                            item = KnowledgeItem(
                                id=doc_id,
                                content=results["documents"][0][i], # El contenido también se almacena en ChromaDB
                                category=metadata.get("category"),
                                source=metadata.get("source"),
                                confidence=metadata.get("confidence"),
                                created_at=metadata.get("created_at"),
                                accessed_count=metadata.get("accessed_count", 0), # Obtener de metadatos o default
                                last_accessed=metadata.get("last_accessed", 0), # Obtener de metadatos o default
                                tags=metadata.get("tags", [])
                            )
                            # Filtrar por confianza si es necesario (ChromaDB no filtra por score de similitud directamente)
                            if item.confidence >= min_confidence:
                                knowledge_items.append(item)
                                self._update_access_count(item.id) # Actualizar el contador de acceso en SQLite

                    return knowledge_items

                except Exception as e:
                    self.logger.error(f"Error al buscar conocimiento semántico: {e}")
                    return []

            # ... _update_access_count (mantenerlo para actualizar SQLite) ...
            # ... cleanup_old_data (modificar para limpiar también ChromaDB) ...
            def cleanup_old_data(self, days_old: int = 30):
                """Limpia datos antiguos de la base de datos SQLite y ChromaDB."""
                cutoff_time = time.time() - (days_old * 24 * 60 * 60)

                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    # Limpiar conversaciones antiguas (SQLite)
                    cursor.execute("DELETE FROM conversation_history WHERE timestamp < ?", (cutoff_time,))
                    deleted_messages = cursor.rowcount

                    # Limpiar tareas completadas antiguas (SQLite)
                    cursor.execute("""
                        DELETE FROM task_memory
                        WHERE status = 'completed' AND updated_at < ?
                    """, (cutoff_time,))
                    deleted_tasks = cursor.rowcount

                    # Limpiar conocimiento con baja confianza y poco acceso (SQLite)
                    # Obtener IDs de conocimiento a eliminar de SQLite
                    cursor.execute("SELECT id FROM knowledge_base WHERE confidence < 0.3 AND accessed_count < 2 AND created_at < ?", (cutoff_time,))
                    ids_to_delete_from_chroma = [row[0] for row in cursor.fetchall()]
                    deleted_knowledge_sqlite = cursor.rowcount

                    # Eliminar de SQLite
                    cursor.execute("""
                        DELETE FROM knowledge_base
                        WHERE confidence < 0.3 AND accessed_count < 2 AND created_at < ?
                    """, (cutoff_time,))

                    conn.commit()
                    conn.close()

                    # Eliminar de ChromaDB usando los IDs obtenidos
                    if ids_to_delete_from_chroma:
                        self.knowledge_collection.delete(ids=ids_to_delete_from_chroma)
                        self.logger.info(f"Eliminados {len(ids_to_delete_from_chroma)} elementos de conocimiento de ChromaDB.")

                    self.logger.info(f"Limpieza completada: {deleted_messages} mensajes, {deleted_tasks} tareas, {deleted_knowledge_sqlite} elementos de conocimiento eliminados de SQLite.")

                except Exception as e:
                    self.logger.error(f"Error durante la limpieza: {e}")
        ```

### 5.2. Extracción de Conocimiento Mejorada

**Objetivo:** Utilizar un LLM para extraer conocimiento estructurado y de alta calidad de las interacciones del agente (mensajes de usuario, respuestas del agente, resultados de herramientas, reflexiones). Este conocimiento estructurado será más útil para la base de conocimiento y para futuras decisiones del agente.

**Diseño Propuesto:**

Se creará una nueva función en `agent_core.py` (o un módulo dedicado si la lógica se vuelve compleja) que, después de cada interacción significativa, invocará un LLM para identificar y extraer entidades, relaciones, hechos clave o lecciones aprendidas. Este LLM será instruido para generar la información en un formato estructurado (ej. JSON) que luego se añadirá a la `knowledge_base`.

**Instrucciones de Implementación:**

1.  **Modificar `agent_core.py` para la Extracción de Conocimiento:**
    *   **Acción:** Reemplazar o mejorar la función `_extract_knowledge_from_conversation` y extenderla para procesar también los resultados de las herramientas y las reflexiones.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...
        # ... otras clases y dataclasses ...

        class MitosisAgent:
            # ... __init__ y otros métodos ...

            async def _extract_and_store_knowledge(self, text_to_analyze: str, context_type: str, source_id: str):
                """Extrae conocimiento estructurado de un texto usando un LLM y lo almacena.
                Args:
                    text_to_analyze: El texto del cual extraer conocimiento.
                    context_type: Tipo de contexto (ej. 'conversation', 'tool_result', 'reflection').
                    source_id: ID de la fuente original (ej. ID de mensaje, ID de tarea, ID de reflexión).
                """
                try:
                    # Prompt para el LLM para extraer conocimiento
                    extraction_prompt = self.prompt_manager.generate_knowledge_extraction_prompt(
                        text=text_to_analyze,
                        context_type=context_type
                    )

                    extraction_model = self.model_manager.select_best_model(
                        task_type="analysis", # O un tipo específico para extracción de conocimiento
                        max_cost=self.config.max_cost_per_1k_tokens
                    )

                    if not extraction_model:
                        self.logger.warning("No hay modelo disponible para extracción de conocimiento.")
                        return

                    llm_response = self.model_manager.generate_response(
                        extraction_prompt,
                        model=extraction_model,
                        max_tokens=1000,
                        temperature=0.1 # Baja temperatura para extracción precisa
                    )

                    if not llm_response:
                        self.logger.warning("LLM no generó respuesta para extracción de conocimiento.")
                        return

                    # Asumir que el LLM devuelve un JSON con el conocimiento extraído
                    # Ejemplo de formato esperado: {"facts": [], "concepts": [], "summary": ""}
                    extracted_data = json.loads(llm_response)

                    # Almacenar cada pieza de conocimiento extraída
                    if "facts" in extracted_data and isinstance(extracted_data["facts"], list):
                        for fact in extracted_data["facts"]:
                            self.memory_manager.add_knowledge(
                                content=fact.get("statement", str(fact)),
                                category=fact.get("category", "extracted_fact"),
                                source=f"{context_type}:{source_id}",
                                confidence=fact.get("confidence", 0.7),
                                tags=fact.get("tags", [])
                            )
                    if "summary" in extracted_data and extracted_data["summary"]:
                         self.memory_manager.add_knowledge(
                            content=extracted_data["summary"],
                            category="summary",
                            source=f"{context_type}:{source_id}",
                            confidence=0.8,
                            tags=["summary", context_type]
                        )

                except Exception as e:
                    self.logger.error(f"Error al extraer y almacenar conocimiento: {e}", exc_info=True)

            # Modificar process_user_message para llamar a _extract_and_store_knowledge
            def process_user_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
                # ... código existente ...
                response = self.model_manager.chat_completion(
                    messages=messages,
                    model=best_model,
                    max_tokens=1000,
                    temperature=0.7
                )
                # ... código existente ...

                # Llamar a la nueva función de extracción de conocimiento
                full_conversation_text = f"Usuario: {message}\nAgente: {response}"
                self._extract_and_store_knowledge(full_conversation_text, "conversation", self.current_session_id)

                self.state = AgentState.IDLE
                return response

            # Modificar execute_current_phase para llamar a _extract_and_store_knowledge
            async def execute_current_phase(self, task_id: Optional[str] = None) -> str:
                # ... código existente ...
                # Dentro del bucle de herramientas, después de cada tool_result_data:
                # self._extract_and_store_knowledge(json.dumps(tool_result_data), "tool_result", f"{task.id}-{current_phase.id}-{iteration_count}")
                # Y al finalizar la fase:
                # self._extract_and_store_knowledge(current_phase.results["final_phase_result"], "phase_completion", f"{task.id}-{current_phase.id}")
                # ... código existente ...

            # Modificar reflect_on_action para llamar a _extract_and_store_knowledge
            def reflect_on_action(self, action: str, result: str, expected: str) -> str:
                # ... código existente ...
                if reflection_response:
                    # Ya se añade una reflexión general, pero se podría extraer conocimiento más granular
                    reflection_id = self.memory_manager.add_knowledge(
                        content=f"Reflexión sobre acción: {action} -> {reflection_response}",
                        category="reflection",
                        source="agent_reflection",
                        confidence=0.8,
                        tags=["reflection", "learning"]
                    )
                    # Extraer conocimiento más profundo de la reflexión
                    self._extract_and_store_knowledge(reflection_response, "reflection", reflection_id)
                    return reflection_response
                # ... código existente ...
        ```

2.  **Añadir Prompt de Extracción de Conocimiento en `enhanced_prompts.py`:**
    *   **Acción:** Crear una nueva plantilla de prompt para la extracción de conocimiento estructurado.
    *   **Cambios en `backend/enhanced_prompts.py` (fragmento):**
        ```python
        # ... imports existentes ...

        class EnhancedPromptManager:
            # ... __init__ existente ...

            def _initialize_base_templates(self):
                # ... plantillas existentes ...
                base_templates["knowledge_extraction"] = """Analiza el siguiente texto y extrae cualquier hecho, concepto clave o lección aprendida. 
                El texto proviene de un contexto de {context_type}. 
                Formato de salida en JSON, incluyendo una lista de 'facts' (cada uno con 'statement', 'category', 'confidence', 'tags') y un 'summary' general.

                Texto a analizar:
                {text}

                Ejemplo de formato JSON:
                ```json
                {{
                  "facts": [
                    {{"statement": "El lenguaje Python es interpretado.", "category": "programming_fact", "confidence": 0.9, "tags": ["python", "lenguaje"]}},
                    {{"statement": "La herramienta ShellTool permite ejecutar comandos de sistema.", "category": "tool_capability", "confidence": 0.8, "tags": ["shell", "herramienta"]}}
                  ],
                  "summary": "Resumen conciso de los puntos clave extraídos del texto."
                }}
                ```
                Tu respuesta debe ser SOLO el objeto JSON. No incluyas texto adicional antes o después del JSON.
                """
                # ... resto de la función ...

            def generate_knowledge_extraction_prompt(self, text: str, context_type: str) -> str:
                """Genera un prompt para la extracción de conocimiento estructurado."""
                template = self.prompt_templates.get("knowledge_extraction", "")
                optimized_template = self._apply_optimizations("knowledge_extraction", template)

                return optimized_template.format(
                    text=text,
                    context_type=context_type
                )

            # ... resto de la clase ...
        ```

### 5.3. Pruebas para el Sistema de Memoria Mejorado

**Objetivo:** Validar que la búsqueda semántica funciona correctamente y que la extracción de conocimiento es efectiva.

**Instrucciones de Implementación:**

1.  **Pruebas Unitarias para `EmbeddingGenerator`:**
    *   **Acción:** Verificar que el generador de embeddings carga el modelo correctamente y produce embeddings para textos de entrada.

2.  **Pruebas Unitarias para `MemoryManager` (Búsqueda Semántica):**
    *   **Acción:** Escribir pruebas que:
        *   Añadan varios elementos de conocimiento con contenido semánticamente similar pero con palabras clave diferentes.
        *   Realicen búsquedas utilizando consultas que no contengan las palabras clave exactas pero sí el significado.
        *   Verifiquen que los resultados de la búsqueda son los esperados (los elementos semánticamente más cercanos).
        *   Prueben el filtrado por categoría y confianza.

3.  **Pruebas de Integración para Extracción de Conocimiento:**
    *   **Acción:** Simular interacciones completas (mensajes de usuario, resultados de herramientas) y verificar que el `_extract_and_store_knowledge` se invoca y que el conocimiento extraído se almacena correctamente en la base de datos de conocimiento (ChromaDB y SQLite).
    *   **Mocks:** Utilizar mocks para el `ModelManager` que simulen la respuesta JSON de extracción de conocimiento del LLM.

Al completar esta fase, el agente MitosisV6 tendrá una memoria mucho más sofisticada, capaz de comprender y recuperar información basada en el significado, lo que mejorará drásticamente su capacidad de razonamiento y aprendizaje. La siguiente fase se centrará en refinar la reflexión y el aprendizaje proactivo, utilizando esta memoria mejorada.



## Fase 6: Refinamiento de la Reflexión y el Aprendizaje Proactivo

### Objetivo de la Fase

El objetivo de esta fase es transformar el mecanismo de reflexión del agente de un proceso pasivo de registro a un componente activo de aprendizaje proactivo. Utilizando la memoria semántica mejorada de la Fase 5, el agente será capaz de extraer lecciones más profundas de sus experiencias (éxitos y fracasos) y aplicar activamente esos aprendizajes para mejorar su rendimiento en tareas futuras. Esto es fundamental para la evolución y la inteligencia a largo plazo del agente.

### 6.1. Reflexión Post-Tarea y Post-Fallo

**Objetivo:** Implementar un proceso de reflexión más estructurado y profundo que se active automáticamente después de la finalización de una tarea (exitosa o fallida) o de una fase que haya encontrado dificultades. La reflexión debe ir más allá de una acción individual y analizar el proceso completo.

**Diseño Propuesto:**

Se creará un nuevo método en `agent_core.py` que orquestará el proceso de reflexión. Este método:

1.  Recuperará el historial completo de la tarea o fase (plan, acciones, resultados de herramientas, pensamientos del LLM).
2.  Generará un prompt detallado para un LLM de reflexión, pidiéndole que analice el historial e identifique:
    *   Qué funcionó bien y por qué.
    *   Qué salió mal y por qué (causas raíz).
    *   Patrones recurrentes (éxitos o errores).
    *   Lecciones aprendidas clave.
    *   Recomendaciones concretas para mejorar el rendimiento futuro.
3.  Almacenará estas lecciones aprendidas en la base de conocimiento semántica (`MemoryManager`) con una alta confianza y etiquetas específicas (ej. `lesson_learned`, `best_practice`, `failure_mode`).

**Instrucciones de Implementación:**

1.  **Modificar `agent_core.py` para Orquestar la Reflexión:**
    *   **Acción:** Añadir un nuevo método `_initiate_post_mortem_reflection` que será llamado por `task_manager` cuando una tarea o fase termine.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...

        class MitosisAgent:
            # ... __init__ y otros métodos ...

            async def _initiate_post_mortem_reflection(self, task_id: str, phase_id: Optional[int] = None):
                """Inicia un proceso de reflexión post-mortem sobre una tarea o fase.
                Analiza el historial para extraer lecciones aprendidas.
                """
                self.state = AgentState.REFLECTING
                task = self.task_manager.get_task(task_id)
                if not task:
                    self.logger.error(f"No se encontró la tarea {task_id} para la reflexión.")
                    return

                reflection_target_description = f"Tarea: {task.title} (ID: {task.id})"
                reflection_history = []
                reflection_category = "task_reflection"
                reflection_source = f"task_completion:{task.id}"

                if phase_id is not None:
                    phase = next((p for p in task.phases if p.id == phase_id), None)
                    if not phase:
                        self.logger.error(f"No se encontró la fase {phase_id} para la reflexión en la tarea {task_id}.")
                        return
                    reflection_target_description = f"Fase: {phase.title} (ID: {phase.id}) de Tarea: {task.title} (ID: {task.id})"
                    reflection_history = phase.results.get("execution_history", [])
                    reflection_category = "phase_reflection"
                    reflection_source = f"phase_completion:{task.id}-{phase.id}"
                else:
                    # Recopilar historial de todas las fases para la reflexión de la tarea completa
                    for p in task.phases:
                        reflection_history.extend(p.results.get("execution_history", []))

                # Formatear el historial para el LLM
                formatted_history = self._format_execution_history(reflection_history)

                reflection_prompt = self.prompt_manager.generate_post_mortem_reflection_prompt(
                    target_description=reflection_target_description,
                    history=formatted_history,
                    task_goal=task.goal,
                    task_status=task.status.value
                )

                reflection_model = self.model_manager.select_best_model(
                    task_type="analysis",
                    max_cost=self.config.max_cost_per_1k_tokens
                )

                if not reflection_model:
                    self.logger.warning("No hay modelo disponible para la reflexión post-mortem.")
                    return

                llm_reflection = self.model_manager.generate_response(
                    reflection_prompt,
                    model=reflection_model,
                    max_tokens=2000,
                    temperature=0.5
                )

                if llm_reflection:
                    # Almacenar la reflexión en la base de conocimiento
                    reflection_id = self.memory_manager.add_knowledge(
                        content=llm_reflection,
                        category=reflection_category,
                        source=reflection_source,
                        confidence=0.9,
                        tags=["reflection", "learning", task.status.value]
                    )
                    self.logger.info(f"Reflexión post-mortem almacenada para {reflection_target_description}: {reflection_id}")
                    # Opcional: Extraer conocimiento más granular de esta reflexión
                    await self._extract_and_store_knowledge(llm_reflection, reflection_category, reflection_id)
                else:
                    self.logger.warning(f"LLM no generó reflexión para {reflection_target_description}.")
                self.state = AgentState.IDLE

            # Modificar complete_task y fail_task en TaskManager para llamar a esta función
            # Esto se hará en la sección 6.2

            # Mantener la función reflect_on_action para reflexiones a nivel de acción individual si se desea
            # o consolidarla completamente en la reflexión post-mortem.
            # Por ahora, se puede mantener, pero su uso podría ser menos frecuente.
        ```

2.  **Añadir Prompt de Reflexión Post-Mortem en `enhanced_prompts.py`:**
    *   **Acción:** Crear una nueva plantilla de prompt que guíe al LLM para realizar un análisis post-mortem detallado.
    *   **Cambios en `backend/enhanced_prompts.py` (fragmento):**
        ```python
        # ... imports existentes ...

        class EnhancedPromptManager:
            # ... __init__ existente ...

            def _initialize_base_templates(self):
                # ... plantillas existentes ...
                base_templates["post_mortem_reflection"] = """Realiza un análisis post-mortem detallado de la siguiente ejecución.

                **Objetivo de la Ejecución:** {target_description}
                **Estado Final de la Tarea:** {task_status}
                **Objetivo General de la Tarea:** {task_goal}

                **Historial de Ejecución (Pensamientos, Acciones, Resultados de Herramientas):**
                {history}

                **Análisis Requerido:**
                1.  **Evaluación General:** ¿Se logró el objetivo? ¿Por qué sí o por qué no?
                2.  **Puntos Fuertes:** ¿Qué estrategias, acciones o herramientas funcionaron excepcionalmente bien?
                3.  **Puntos Débiles/Errores:** ¿Qué falló? ¿Cuál fue la causa raíz de los problemas? ¿Hubo errores en la planificación, ejecución, uso de herramientas o interpretación de resultados?
                4.  **Patrones Identificados:** ¿Se observaron patrones recurrentes de éxito o fracaso?
                5.  **Lecciones Aprendidas Clave:** Resume los aprendizajes más importantes de esta experiencia.
                6.  **Recomendaciones para el Futuro:** ¿Cómo se podría mejorar el rendimiento en situaciones similares en el futuro? (Ej. ajustar prompts, usar diferentes herramientas, modificar el plan, etc.)

                Proporciona un análisis exhaustivo y constructivo. Tu respuesta debe ser un texto bien estructurado, no un JSON.
                """
                # ... resto de la función ...

            def generate_post_mortem_reflection_prompt(self, target_description: str, history: str,
                                                    task_goal: str, task_status: str) -> str:
                """Genera un prompt para la reflexión post-mortem."""
                template = self.prompt_templates.get("post_mortem_reflection", "")
                optimized_template = self._apply_optimizations("post_mortem_reflection", template)

                return optimized_template.format(
                    target_description=target_description,
                    history=history,
                    task_goal=task_goal,
                    task_status=task_status
                )

            # ... resto de la clase ...
        ```

### 6.2. Integración de la Reflexión en el `TaskManager`

**Objetivo:** Asegurar que el `TaskManager` active el proceso de reflexión post-mortem en los momentos adecuados (finalización de tarea o fallo de fase/tarea).

**Diseño Propuesto:**

El `TaskManager` llamará al nuevo método de reflexión del `agent_core` cuando una tarea se complete (`complete_task`) o falle (`fail_task`). También se podría considerar una reflexión a nivel de fase si una fase falla repetidamente.

**Instrucciones de Implementación:**

1.  **Modificar `TaskManager` en `backend/task_manager.py`:**
    *   **Acción:** Añadir un callback al `agent_core` para iniciar la reflexión.
    *   **Cambios en `backend/task_manager.py` (fragmento):**
        ```python
        # ... imports existentes ...
        from typing import List, Dict, Optional, Any, Callable, TYPE_CHECKING
        import threading

        if TYPE_CHECKING:
            from backend.agent_core import MitosisAgent # Importación para type hinting, evita circular imports

        class TaskManager:
            def __init__(self, memory_manager: MemoryManager):
                self.memory_manager = memory_manager
                self.logger = logging.getLogger(__name__)
                self.agent_core_ref: Optional["MitosisAgent"] = None # Referencia al agente principal
                # ... resto del __init__ ...

            def set_agent_core_ref(self, agent_core_instance: "MitosisAgent"):
                """Establece la referencia al agente principal para callbacks."""
                self.agent_core_ref = agent_core_instance

            def complete_task(self, task_id: str, results: Optional[Dict[str, Any]] = None) -> bool:
                # ... código existente ...
                self._save_task_to_memory(task)

                # Iniciar reflexión post-mortem para la tarea completada
                if self.agent_core_ref:
                    # Ejecutar en un hilo separado o como una tarea asíncrona para no bloquear
                    threading.Thread(target=lambda: self.agent_core_ref._initiate_post_mortem_reflection(task_id)).start()

                self._process_next_task()
                self.logger.info(f"Tarea completada: {task_id}")
                return True

            def fail_task(self, task_id: str, error_message: str) -> bool:
                # ... código existente ...
                self._save_task_to_memory(task)

                # Iniciar reflexión post-mortem para la tarea fallida
                if self.agent_core_ref:
                    threading.Thread(target=lambda: self.agent_core_ref._initiate_post_mortem_reflection(task_id)).start()

                self._process_next_task()
                self.logger.error(f"Tarea fallida: {task_id} - {error_message}")
                return True

            # Opcional: Añadir llamada a reflexión en execute_current_phase de agent_core
            # si una fase individual falla después de varios reintentos de herramientas.
            # Esto ya está parcialmente cubierto por el fail_task de la tarea completa.
        ```

2.  **Establecer la Referencia en `agent_core.py`:**
    *   **Acción:** En el `__init__` de `MitosisAgent`, pasar una referencia de sí mismo al `TaskManager`.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        class MitosisAgent:
            def __init__(self, config: Optional[AgentConfig] = None):
                # ... código existente ...
                self._initialize_components()
                self.task_manager.set_agent_core_ref(self) # Establecer la referencia
                # ... código existente ...
        ```

### 6.3. Integración de la Reflexión en la Planificación

**Objetivo:** Utilizar activamente las lecciones aprendidas de las reflexiones pasadas para informar y mejorar la planificación de nuevas tareas. Esto cierra el bucle de aprendizaje del agente.

**Diseño Propuesto:**

Antes de generar un nuevo plan de tarea, el agente consultará su base de conocimiento semántica en busca de lecciones aprendidas relevantes para el objetivo de la nueva tarea. Estas lecciones se incluirán en el prompt de planificación para guiar al LLM.

**Instrucciones de Implementación:**

1.  **Modificar `create_and_execute_task` en `agent_core.py`:**
    *   **Acción:** Antes de generar el prompt de planificación, realizar una búsqueda semántica en la base de conocimiento para encontrar reflexiones relevantes.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...

        class MitosisAgent:
            # ... __init__ y otros métodos ...

            def create_and_execute_task(self, title: str, description: str, goal: str,
                                       auto_execute: bool = True) -> str:
                try:
                    self.state = AgentState.PLANNING

                    # 1. Buscar lecciones aprendidas relevantes
                    relevant_lessons = self.memory_manager.search_knowledge(
                        query=f"Cómo abordar la tarea: {goal}",
                        category="task_reflection", # Buscar reflexiones de tareas
                        limit=3 # Limitar el número de lecciones a incluir
                    )
                    # También buscar lecciones de fallos si la tarea es similar a una que falló
                    failed_lessons = self.memory_manager.search_knowledge(
                        query=f"Errores comunes al intentar: {goal}",
                        category="task_reflection",
                        limit=2,
                        min_confidence=0.7 # Solo las más relevantes
                    )

                    contextual_lessons = ""
                    if relevant_lessons or failed_lessons:
                        contextual_lessons = "\n\nLecciones aprendidas de experiencias pasadas:\n"
                        for lesson in relevant_lessons:
                            contextual_lessons += f"- {lesson.content}\n"
                        for lesson in failed_lessons:
                            contextual_lessons += f"- Evitar: {lesson.content}\n"

                    max_planning_retries = 3
                    plan_data = None
                    validation_error_message = None

                    for attempt in range(max_planning_retries):
                        # Generar prompt del sistema con contexto, esquema JSON y lecciones aprendidas
                        planning_prompt = self.prompt_manager.generate_task_planning_prompt(
                            goal=goal,
                            description=description,
                            context=f"Título: {title}{contextual_lessons}", # Incluir lecciones aquí
                            json_schema=TASK_PLAN_SCHEMA,
                            validation_error=validation_error_message
                        )

                        # ... resto del código de planificación ...
        ```

### 6.4. Pruebas para el Sistema de Reflexión y Aprendizaje

**Objetivo:** Validar que el proceso de reflexión se activa correctamente, que las lecciones aprendidas se almacenan y que estas lecciones influyen en la planificación futura.

**Instrucciones de Implementación:**

1.  **Pruebas de Activación de Reflexión:**
    *   **Acción:** Escribir pruebas que simulen la finalización exitosa y fallida de tareas y fases, y verifiquen que el método `_initiate_post_mortem_reflection` se llama. Utilizar mocks para el `ModelManager` y el `MemoryManager` para verificar las llamadas.

2.  **Pruebas de Contenido de Reflexión:**
    *   **Acción:** Simular un historial de ejecución de tarea (con éxitos y fallos simulados de herramientas) y verificar que el LLM de reflexión (mockeado) genera una reflexión que contenga los puntos clave esperados (ej. identificación de un error específico, una lección aprendida).

3.  **Pruebas de Influencia en la Planificación:**
    *   **Acción:** Crear un escenario donde una tarea similar haya fallado previamente y se haya generado una reflexión. Luego, iniciar una nueva tarea con un objetivo similar y verificar que el prompt de planificación incluye las lecciones aprendidas de la reflexión anterior. Esto requerirá un mock sofisticado para `MemoryManager.search_knowledge`.

Al completar esta fase, el agente MitosisV6 no solo será capaz de ejecutar tareas, sino que también aprenderá activamente de cada experiencia, mejorando su inteligencia y eficiencia con el tiempo. La siguiente fase se centrará en hacer que el manejo de errores sea más inteligente y proactivo.



## Fase 7: Mejora del Manejo de Errores y Estrategias de Recuperación

### Objetivo de la Fase

El objetivo de esta fase es dotar al agente MitosisV6 de un sistema de manejo de errores más sofisticado y de estrategias de recuperación proactivas. Un agente autónomo debe ser capaz de identificar, diagnosticar y, en la medida de lo posible, recuperarse de los errores sin intervención humana. Esto aumentará significativamente la robustez y fiabilidad del agente, permitiéndole manejar situaciones inesperadas de manera más elegante.

### 7.1. Detección y Clasificación de Errores

**Objetivo:** Implementar mecanismos para detectar errores de manera más granular y clasificarlos según su tipo y gravedad. Esto permitirá al agente aplicar estrategias de recuperación específicas para cada tipo de error.

**Diseño Propuesto:**

Se centralizará la gestión de errores en un nuevo módulo o clase `ErrorHandler`. Las herramientas y otros componentes del agente reportarán errores a este manejador, que los clasificará y registrará. Se definirán tipos de errores comunes (ej. `ToolExecutionError`, `LLMResponseError`, `PlanningError`, `EnvironmentError`).

**Instrucciones de Implementación:**

1.  **Crear un Módulo `error_handler.py`:**
    *   **Acción:** Crear un nuevo archivo `error_handler.py` dentro de `backend/`.
    *   **Código (`backend/error_handler.py`):**
        ```python
        import logging
        from typing import Dict, Any, Optional

        class ErrorType:
            TOOL_EXECUTION = "tool_execution_error"
            LLM_RESPONSE = "llm_response_error"
            PLANNING = "planning_error"
            ENVIRONMENT = "environment_error"
            UNKNOWN = "unknown_error"
            # Añadir más tipos según sea necesario

        class ErrorHandler:
            """Maneja la detección, clasificación y registro de errores del agente.
            """
            def __init__(self):
                self.logger = logging.getLogger(__name__)

            def handle_error(self, error: Exception, error_type: str = ErrorType.UNKNOWN,
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                """Procesa un error, lo clasifica y lo registra.
                Args:
                    error: La excepción Python que ocurrió.
                    error_type: Tipo predefinido del error (ver ErrorType).
                    context: Diccionario con información adicional relevante para el error.
                Returns:
                    Un diccionario con los detalles del error procesado.
                """
                error_details = {
                    "type": error_type,
                    "message": str(error),
                    "class": error.__class__.__name__,
                    "context": context if context is not None else {},
                    "timestamp": logging.Formatter().formatTime(logging.LogRecord(name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None))
                }
                self.logger.error(f"Error detectado: Tipo={error_type}, Mensaje=\"{str(error)}\", Contexto={context}", exc_info=True)
                # Aquí se podría añadir lógica para enviar alertas, notificaciones, etc.
                return error_details

            def classify_exception(self, e: Exception) -> str:
                """Intenta clasificar una excepción Python en un tipo de error conocido.
                """
                if isinstance(e, (subprocess.CalledProcessError, subprocess.TimeoutExpired)):
                    return ErrorType.TOOL_EXECUTION
                elif isinstance(e, (json.JSONDecodeError, ValueError)) and "LLM" in str(e):
                    return ErrorType.LLM_RESPONSE
                elif isinstance(e, jsonschema.ValidationError):
                    return ErrorType.PLANNING
                elif isinstance(e, (requests.exceptions.RequestException, FileNotFoundError)):
                    return ErrorType.ENVIRONMENT
                # Añadir más reglas de clasificación según se identifiquen patrones de error
                return ErrorType.UNKNOWN
        ```

2.  **Integrar `ErrorHandler` en `agent_core.py` y Herramientas:**
    *   **Acción:** Instanciar `ErrorHandler` en `MitosisAgent` y utilizarlo en los bloques `try-except` de `execute_current_phase`, `_execute_tool`, `create_and_execute_task` y en las herramientas individuales.
    *   **Cambios en `backend/agent_core.py` (fragmento):**
        ```python
        # ... imports existentes ...
        from backend.error_handler import ErrorHandler, ErrorType # Nuevo import

        class MitosisAgent:
            def __init__(self, config: Optional[AgentConfig] = None):
                # ... código existente ...
                self.error_handler = ErrorHandler() # Instanciar ErrorHandler
                # ... código existente ...

            async def execute_current_phase(self, task_id: Optional[str] = None) -> str:
                try:
                    # ... código existente ...
                except Exception as e:
                    error_details = self.error_handler.handle_error(
                        e, error_type=self.error_handler.classify_exception(e),
                        context={"phase_id": current_phase.id, "task_id": task.id}
                    )
                    self.state = AgentState.ERROR
                    self.task_manager.fail_task(task.id, f"Error inesperado durante la ejecución de la fase: {error_details['message']}")
                    return f"Error al ejecutar fase: {error_details['message']}"

            def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
                try:
                    # ... código existente ...
                except Exception as e:
                    error_details = self.error_handler.handle_error(
                        e, error_type=ErrorType.TOOL_EXECUTION,
                        context={"tool_name": tool_name, "tool_args": tool_args}
                    )
                    return {"status": "error", "message": f"Error durante la ejecución de la herramienta {tool_name}: {error_details['message']}"}

            def create_and_execute_task(self, title: str, description: str, goal: str,
                                       auto_execute: bool = True) -> str:
                try:
                    # ... código existente ...
                except Exception as e:
                    error_details = self.error_handler.handle_error(
                        e, error_type=ErrorType.PLANNING,
                        context={"goal": goal, "description": description}
                    )
                    self.state = AgentState.ERROR
                    return f"Error al crear tarea: {error_details['message']}"
        ```
    *   **Cambios en `backend/tools/*.py` (ej. `shell_tool.py`):**
        ```python
        # ... imports existentes ...
        # No es necesario pasar el ErrorHandler a cada herramienta, ya que _execute_tool lo captura.
        # Sin embargo, si una herramienta necesita lógica de reintento interna o manejo específico,
        # podría recibir una instancia de ErrorHandler.
        # Por ahora, el manejo centralizado en _execute_tool es suficiente.
        ```

### 7.2. Estrategias de Recuperación Automática

**Objetivo:** Implementar lógica para que el agente intente recuperarse de ciertos tipos de errores de forma autónoma, reduciendo la necesidad de intervención humana.

**Diseño Propuesto:**

Las estrategias de recuperación se implementarán en `agent_core.py` y se activarán en función del tipo de error detectado. Esto podría incluir reintentos, ajuste de prompts, selección de herramientas alternativas o incluso la re-planificación de una fase.

**Instrucciones de Implementación:**

1.  **Modificar `execute_current_phase` en `backend/agent_core.py` para Reintentos y Ajustes:**
    *   **Acción:** Añadir lógica de reintento con retroalimentación al LLM para errores de `LLM_RESPONSE` y `TOOL_EXECUTION`.
    *   **Cambios en `backend/agent_core.py` (fragmento - dentro de `execute_current_phase`):**
        ```python
        # ... código existente ...

                    max_tool_iterations = 10
                    max_error_retries = 3 # Número de reintentos para errores dentro de una iteración
                    iteration_count = 0
                    phase_completed = False
                    last_tool_result = ""
                    error_feedback_for_llm = ""

                    while iteration_count < max_tool_iterations and not phase_completed:
                        iteration_count += 1
                        self.logger.info(f"Fase {current_phase.id}, Iteración {iteration_count}")

                        current_context_for_llm = self._format_execution_history(current_phase.results["execution_history"])
                        if last_tool_result:
                            current_context_for_llm += f"\nÚltimo resultado de herramienta: {last_tool_result}"
                        if error_feedback_for_llm:
                            current_context_for_llm += f"\nRetroalimentación de error: {error_feedback_for_llm}\nPor favor, corrige tu enfoque.\n"

                        tool_use_prompt = self.prompt_manager.generate_tool_use_prompt(
                            task, current_phase, current_context_for_llm
                        )

                        # ... selección de modelo y generación de respuesta del LLM ...

                        action_data = self._parse_tool_call(llm_response)
                        action_type = action_data.get("action")
                        tool_name = action_data.get("tool_name")
                        tool_args = action_data.get("tool_args", {})

                        if action_type == "finish_phase" or action_type == "request_info":
                            # ... lógica existente ...
                            break
                        elif tool_name:
                            tool_result_data = self._execute_tool(tool_name, tool_args)
                            last_tool_result = json.dumps(tool_result_data)

                            current_phase.results["execution_history"].append({
                                "iteration": iteration_count,
                                "thought": llm_response,
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "tool_result": tool_result_data,
                                "timestamp": time.time()
                            })

                            if tool_result_data.get("status") == "error":
                                error_message = tool_result_data.get("message", "Error desconocido en la herramienta.")
                                self.logger.error(f"Error en herramienta {tool_name}: {error_message}")
                                error_feedback_for_llm = f"La herramienta {tool_name} falló con el siguiente mensaje: {error_message}. Revisa tus argumentos o intenta una estrategia diferente."
                                # Aquí se podría incrementar un contador de errores para la iteración
                                # y si excede un límite, considerar fallar la fase o re-planificar.
                                # Por ahora, el LLM recibirá la retroalimentación y reintentará.
                            else:
                                error_feedback_for_llm = "" # Limpiar el feedback de error si la herramienta tuvo éxito
                        else:
                            # Error de parseo o respuesta no reconocida del LLM
                            error_message = f"Respuesta del LLM no reconocida o JSON inválido: {llm_response}"
                            self.logger.error(error_message)
                            error_feedback_for_llm = f"Tu respuesta no pudo ser parseada o no siguió el formato esperado. Error: {error_message}. Por favor, asegúrate de que tu respuesta sea SOLO un JSON válido con 'tool_name' y 'tool_args', o 'action' y 'result'/'reason'."
                            # Si el LLM falla en generar JSON válido repetidamente, se podría forzar un reintento
                            # o incluso una re-planificación de la fase.
                            # Por ahora, se le da feedback y se espera que se corrija.

                        # Lógica para reintentos de errores específicos
                        if error_feedback_for_llm and iteration_count < max_tool_iterations:
                            # Si hay un error y aún quedan iteraciones, el bucle continuará
                            # y el LLM recibirá el error_feedback_for_llm.
                            pass
                        elif error_feedback_for_llm and iteration_count >= max_tool_iterations:
                            # Si hay un error y se acabaron las iteraciones, la fase falla.
                            self.logger.error(f"Fase {current_phase.id} falló debido a errores persistentes después de {max_tool_iterations} iteraciones.")
                            break # Salir del bucle de la fase

                    # ... resto del código de finalización de fase ...
        ```

### 7.3. Notificación y Registro de Errores

**Objetivo:** Asegurar que los errores importantes sean registrados de manera persistente y que se notifique a los operadores o desarrolladores cuando ocurran fallos críticos que el agente no pueda resolver por sí mismo.

**Diseño Propuesto:**

El `ErrorHandler` registrará los errores en un sistema de logs persistente (ej. un archivo de log rotativo o una base de datos de logs). Para errores críticos, se podría integrar con un sistema de notificación (ej. Slack, correo electrónico, PagerDuty).

**Instrucciones de Implementación:**

1.  **Configurar Logging Avanzado:**
    *   **Acción:** Configurar el módulo `logging` de Python para que los logs se guarden en un archivo, con rotación diaria y niveles de log adecuados (INFO, WARNING, ERROR, CRITICAL).
    *   **Cambios en `main.py` o un nuevo `logging_config.py`:**
        ```python
        import logging
        from logging.handlers import TimedRotatingFileHandler
        import os

        def setup_logging(log_dir="logs", log_file="agent.log"):
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            log_path = os.path.join(log_dir, log_file)

            # Configuración del logger raíz
            logger = logging.getLogger()
            logger.setLevel(logging.INFO) # Nivel mínimo para el logger raíz

            # Handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # Handler para archivo con rotación diaria
            file_handler = TimedRotatingFileHandler(
                log_path, when="midnight", interval=1, backupCount=7
            ) # Rotar a medianoche, mantener 7 archivos de respaldo
            file_handler.setLevel(logging.DEBUG) # Nivel más detallado para el archivo
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # Configurar loggers específicos si es necesario
            logging.getLogger('chromadb').setLevel(logging.WARNING)
            logging.getLogger('httpx').setLevel(logging.WARNING)
            # etc.

        # Llamar a setup_logging() al inicio de la aplicación
        # Ejemplo: en main.py, al principio del script
        ```

2.  **Integración con Sistema de Notificación (Opcional, Avanzado):**
    *   **Acción:** Para errores `CRITICAL` o `ERROR` que persisten después de los reintentos, el `ErrorHandler` podría invocar un servicio externo para enviar una notificación. Esto requeriría una nueva herramienta o una integración directa en `ErrorHandler`.
    *   **Ejemplo (en `ErrorHandler.handle_error`):**
        ```python
        # ... dentro de handle_error ...
        if error_type in [ErrorType.PLANNING, ErrorType.ENVIRONMENT] or "persistente" in error_details["message"]:
            self.logger.critical(f"ERROR CRÍTICO DETECTADO: {error_details['message']}. Requiere intervención humana.")
            # Aquí se podría llamar a una función para enviar un correo electrónico o un mensaje a Slack
            # send_notification_to_ops(error_details)
        # ...
        ```

### 7.4. Pruebas de Manejo de Errores y Recuperación

**Objetivo:** Validar que el sistema de manejo de errores detecta, clasifica y responde a los errores de manera adecuada, y que las estrategias de recuperación funcionan como se espera.

**Instrucciones de Implementación:**

1.  **Pruebas Unitarias para `ErrorHandler`:**
    *   **Acción:** Probar la clasificación de diferentes tipos de excepciones y verificar que los detalles del error se registran correctamente.

2.  **Pruebas de Integración para Recuperación de Errores:**
    *   **Acción:** Crear escenarios de prueba que simulen fallos en las herramientas (ej. `ShellTool` devuelve un error, `WebBrowseTool` falla al conectar) o respuestas inválidas del LLM. Verificar que el agente intenta recuperarse (reintenta, ajusta el prompt) y que, si la recuperación falla, el error se registra y notifica adecuadamente.
    *   **Mocks:** Utilizar mocks para las herramientas y el `ModelManager` para simular los fallos y las respuestas del LLM.

Al completar esta fase, el agente MitosisV6 será significativamente más robusto y capaz de operar de forma autónoma durante períodos más largos, incluso frente a desafíos inesperados. La siguiente fase se centrará en la documentación y las pruebas exhaustivas para asegurar la calidad y el mantenimiento del sistema.



## Fase 8: Documentación y Pruebas Exhaustivas

### Objetivo de la Fase

El objetivo de esta fase es asegurar la calidad, mantenibilidad y usabilidad del agente MitosisV6 mediante la creación de documentación completa y la implementación de un régimen de pruebas exhaustivo. Una buena documentación facilita la comprensión y el mantenimiento del código por parte del equipo de desarrollo, mientras que las pruebas garantizan que el agente funcione como se espera y que los cambios futuros no introduzcan regresiones. Esto es fundamental para la sostenibilidad a largo plazo del proyecto.

### 8.1. Documentación del Código y la Arquitectura

**Objetivo:** Crear documentación clara y concisa para el código fuente, la arquitectura del sistema y los componentes clave del agente. Esto incluye docstrings, comentarios en línea y un documento de diseño de alto nivel.

**Diseño Propuesto:**

Se utilizarán docstrings de Python (formato Google o Sphinx) para documentar clases, métodos y funciones. Los comentarios en línea se usarán para explicar lógica compleja o decisiones de diseño específicas. Se creará un documento Markdown (`architecture_design.md`) que describa la arquitectura general, el flujo de datos y la interacción entre los módulos.

**Instrucciones de Implementación:**

1.  **Docstrings y Comentarios en Línea:**
    *   **Acción:** Revisar todo el código fuente (`agent_core.py`, `model_manager.py`, `memory_manager.py`, `task_manager.py`, `enhanced_prompts.py`, `error_handler.py`, `embedding_generator.py`, y todos los archivos en `backend/tools/`).
    *   **Estándar:** Asegurarse de que cada clase, método y función tenga un docstring que describa su propósito, argumentos, valores de retorno y cualquier excepción que pueda lanzar. Añadir comentarios en línea para explicar secciones de código no obvias o algoritmos complejos.
    *   **Ejemplo de Docstring (Google Style):**
        ```python
        def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
            """Calcula la similitud coseno entre dos embeddings vectoriales.

            Args:
                embedding1: El primer vector de embedding.
                embedding2: El segundo vector de embedding.

            Returns:
                Un flotante que representa la similitud coseno (entre -1 y 1).
            """
            # ... implementación ...
        ```

2.  **Documento de Diseño de Arquitectura:**
    *   **Acción:** Crear un archivo `architecture_design.md` en el directorio raíz del proyecto (`mitosisv6_root/`).
    *   **Contenido:** Este documento debe incluir:
        *   **Visión General:** Una descripción de alto nivel del propósito del agente y sus capacidades.
        *   **Componentes Principales:** Descripción de cada módulo principal (`agent_core`, `model_manager`, `memory_manager`, `task_manager`, `enhanced_prompts`, `error_handler`, `tools/`) y sus responsabilidades.
        *   **Flujo de Datos:** Diagramas (si es posible, usando Mermaid o PlantUML en Markdown) que ilustren cómo fluye la información entre los componentes (ej. desde la entrada del usuario, a través del LLM, a la ejecución de herramientas, y de vuelta).
        *   **Interacción con Herramientas:** Explicación de cómo el `ToolRegistry` y las herramientas individuales se integran con el bucle ReAct.
        *   **Sistema de Memoria:** Detalle de cómo `MemoryManager` utiliza SQLite y ChromaDB, y cómo se gestionan los embeddings y la búsqueda semántica.
        *   **Manejo de Errores:** Descripción del `ErrorHandler` y las estrategias de recuperación.
        *   **Consideraciones de Despliegue:** Notas sobre dependencias, configuración del entorno y posibles escenarios de despliegue.

### 8.2. Estrategia de Pruebas y Cobertura

**Objetivo:** Establecer una estrategia de pruebas clara que incluya pruebas unitarias, de integración y, si es posible, de extremo a extremo, para garantizar la funcionalidad y la robustez del agente. Se buscará una alta cobertura de código.

**Diseño Propuesto:**

Se utilizará `pytest` como framework de pruebas. Se organizarán las pruebas en un directorio `tests/` con subdirectorios para pruebas unitarias (`unit/`), de integración (`integration/`) y de extremo a extremo (`e2e/`). Se utilizará `pytest-cov` para medir la cobertura de código.

**Instrucciones de Implementación:**

1.  **Instalar Dependencias de Pruebas:**
    *   **Acción:** Añadir `pytest` y `pytest-cov` al `requirements.txt` e instalarlos.
    *   **Comando Sugerido:** `pip install pytest pytest-cov`

2.  **Organización de Pruebas:**
    *   **Acción:** Crear la siguiente estructura de directorios en la raíz del proyecto:
        ```
        mitosisv6_root/
        ├── backend/
        ├── tests/
        │   ├── unit/
        │   ├── integration/
        │   └── e2e/
        └── ...
        ```

3.  **Pruebas Unitarias:**
    *   **Objetivo:** Probar componentes individuales de forma aislada (ej. una función específica en `MemoryManager`, un método en `ShellTool`).
    *   **Acción:** Escribir pruebas unitarias para cada clase y función importante. Utilizar mocks para aislar las dependencias externas (ej. mockear llamadas a LLM, operaciones de base de datos, llamadas a `subprocess`).
    *   **Ubicación:** `tests/unit/`
    *   **Ejemplo:** Probar que `ShellTool.run` devuelve el `stdout` correcto para un comando simple.

4.  **Pruebas de Integración:**
    *   **Objetivo:** Probar la interacción entre múltiples componentes (ej. `agent_core` y `ToolRegistry`, `MemoryManager` y ChromaDB).
    *   **Acción:** Escribir pruebas que verifiquen el flujo de datos y la lógica a través de varias unidades. Se pueden usar bases de datos reales (pero temporales) para ChromaDB y SQLite para estas pruebas.
    *   **Ubicación:** `tests/integration/`
    *   **Ejemplo:** Probar que `agent_core.execute_current_phase` puede invocar una `FileReadTool` y procesar su resultado.

5.  **Pruebas de Extremo a Extremo (E2E):**
    *   **Objetivo:** Simular escenarios de uso reales, probando el agente completo desde la entrada del usuario hasta la finalización de la tarea.
    *   **Acción:** Escribir pruebas que inicien una tarea completa y verifiquen que el agente la completa correctamente, utilizando todas las herramientas y componentes. Estas pruebas serán más lentas y pueden requerir modelos LLM reales (o mocks muy sofisticados).
    *   **Ubicación:** `tests/e2e/`
    *   **Ejemplo:** Probar que el agente puede investigar un tema en la web, escribir un resumen en un archivo y reportar el éxito al usuario.

6.  **Medición de Cobertura de Código:**
    *   **Acción:** Configurar `pytest-cov` para generar informes de cobertura de código. Esto ayudará a identificar áreas del código que no están siendo probadas.
    *   **Comando Sugerido:** `pytest --cov=backend --cov-report=html tests/` (genera un informe HTML en `htmlcov/`).
    *   **Objetivo:** Apuntar a una cobertura de código alta (ej. >80%) para las partes críticas del backend.

### 8.3. Integración Continua (CI)

**Objetivo:** Automatizar la ejecución de pruebas y la verificación de la calidad del código cada vez que se realice un cambio en el repositorio. Esto asegura que los errores se detecten temprano y que el código base se mantenga saludable.

**Diseño Propuesto:**

Se configurará un pipeline de CI utilizando una herramienta como GitHub Actions, GitLab CI o Jenkins. El pipeline ejecutará los linters, formateadores y todas las pruebas (unitarias, integración, E2E) en cada push o pull request.

**Instrucciones de Implementación (Ejemplo con GitHub Actions):**

1.  **Crear Archivo de Workflow:**
    *   **Acción:** Crear un archivo `.github/workflows/ci.yml` en la raíz del repositorio.
    *   **Código (`.github/workflows/ci.yml`):**
        ```yaml
        name: CI/CD MitosisV6 Agent

        on: [push, pull_request]

        jobs:
          build-and-test:
            runs-on: ubuntu-latest

            steps:
            - uses: actions/checkout@v3

            - name: Set up Python
              uses: actions/setup-python@v4
              with:
                python-version: '3.11' # O la versión de Python que uses

            - name: Install dependencies
              run: |
                python -m pip install --upgrade pip
                pip install -r requirements.txt
                pip install pytest pytest-cov flake8 black

            - name: Run linters and formatters
              run: |
                flake8 backend/
                black --check backend/

            - name: Run tests with coverage
              run: |
                pytest --cov=backend --cov-report=xml tests/

            - name: Upload coverage to Codecov
              uses: codecov/codecov-action@v3
              with:
                token: ${{ secrets.CODECOV_TOKEN }} # Configurar como secreto en GitHub
                file: ./coverage.xml
                flags: unittests # Opcional: añadir flags para diferenciar tipos de cobertura
                name: codecov-mitosisv6
        ```

Al completar esta fase, el agente MitosisV6 no solo será funcional y robusto, sino que también será un proyecto bien documentado y mantenible, listo para futuras expansiones y mejoras. La fase final se centrará en la entrega de este plan detallado al usuario.



## Confirmación de Ajuste del Plan Basado en la Revisión del Código Existente

Durante la fase inicial de análisis, se realizó una revisión exhaustiva del código fuente proporcionado en `MitosisV6.zip`. Esta revisión abarcó los módulos clave como `agent_core.py`, `model_manager.py`, `memory_manager.py`, `task_manager.py`, y `enhanced_prompts.py`.

**Hallazgos Clave de la Revisión:**

*   **Estructura Modular Existente:** Se confirmó que el agente MitosisV6 ya posee una arquitectura modular bien definida, con componentes separados para la gestión de modelos, memoria, tareas y prompts. Esto es una base excelente y se ha aprovechado en el plan propuesto.
*   **Simulación de Ejecución de Fases:** Se identificó que la ejecución de las fases de las tareas se basa actualmente en una "simulación" de resultados generados por el LLM, en lugar de una interacción real con el entorno a través de herramientas. Este fue el punto principal de divergencia y la razón fundamental para la inclusión de las Fases 2 y 3 (Implementación de Herramientas Esenciales y Rediseño del Bucle de Ejecución con Tool-Use).
*   **Gestión de Memoria Básica:** El `MemoryManager` existente maneja la memoria a corto plazo y una base de conocimiento basada en SQLite, pero carece de capacidades de búsqueda semántica. Esto justificó la Fase 5 (Evolución del Sistema de Memoria).
*   **Manejo de Errores y Reflexión Incipientes:** Existen métodos para el manejo de errores y la reflexión, pero son básicos y no incluyen estrategias de recuperación automática o un aprendizaje proactivo profundo. Esto validó la necesidad de las Fases 6 y 7 (Refinamiento de la Reflexión y Mejora del Manejo de Errores).
*   **Ausencia de Validación de Esquemas en Planificación:** La planificación de tareas, aunque presente, no incluye mecanismos robustos de validación de esquemas JSON para la salida del LLM, lo que puede llevar a planes inválidos. Esto fundamentó la Fase 4 (Mejora de la Robustez de la Planificación).

**Ajuste del Plan:**

El plan detallado presentado previamente (`detailed_improvement_plan.md`) fue diseñado específicamente para complementar y construir sobre la base existente de MitosisV6, evitando la duplicación de componentes ya funcionales. Las fases propuestas se centran en:

1.  **Introducir el uso real de herramientas:** Creando una interfaz unificada y herramientas esenciales (Shell, Archivos, Web) que tu agente actualmente simula.
2.  **Transformar el bucle de ejecución:** Pasando de una simulación a un ciclo de razonamiento-acción-observación (ReAct) que utiliza las herramientas.
3.  **Fortalecer la planificación:** Añadiendo validación de esquemas y mecanismos de reintento para asegurar planes de tarea robustos.
4.  **Mejorar la memoria:** Implementando búsqueda semántica y extracción de conocimiento para una memoria más inteligente y útil.
5.  **Profundizar la reflexión y el aprendizaje:** Convirtiendo la reflexión en un proceso proactivo que aprende de éxitos y fracasos.
6.  **Robustecer el manejo de errores:** Con detección, clasificación y estrategias de recuperación automática.
7.  **Asegurar la calidad:** Con documentación exhaustiva y un régimen de pruebas completo.

En resumen, el plan no duplica funcionalidades existentes, sino que las mejora y las extiende para alcanzar el nivel de un agente autónomo y potente. Los componentes existentes de `ModelManager`, `TaskManager`, `MemoryManager` (en su estructura básica) y `EnhancedPromptManager` (en su capacidad de generar prompts) se mantienen como la base sobre la cual se construyen las nuevas capacidades.

