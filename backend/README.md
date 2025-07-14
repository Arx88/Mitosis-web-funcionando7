# Agente Mitosis Mejorado

Un agente de IA general autónomo con integración avanzada de Ollama y OpenRouter, gestión inteligente de memoria y tareas, y sistema de prompts optimizados.

## 🚀 Características Principales

### Integración de Modelos
- **Ollama**: Detección automática de modelos locales instalados
- **OpenRouter**: Acceso a múltiples modelos de lenguaje en la nube
- **Selección Inteligente**: Algoritmo que selecciona el mejor modelo según la tarea y presupuesto
- **Fallback Automático**: Cambio automático entre proveedores en caso de fallos

### Gestión de Memoria
- **Memoria a Corto Plazo**: Contexto de conversación en memoria RAM
- **Memoria a Largo Plazo**: Base de conocimientos persistente en SQLite
- **Búsqueda Inteligente**: Sistema de búsqueda y recuperación de información relevante
- **Limpieza Automática**: Gestión automática de datos antiguos

### Administración de Tareas
- **Planificación Automática**: Descomposición inteligente de tareas complejas
- **Ejecución por Fases**: Seguimiento detallado del progreso
- **Monitoreo Continuo**: Detección de tareas estancadas o problemáticas
- **Adaptación Dinámica**: Ajuste de estrategias basado en resultados

### Sistema de Prompts
- **Prompts Contextuales**: Generación dinámica basada en contexto
- **Plantillas Optimizadas**: Prompts especializados para diferentes tipos de tareas
- **Optimización Automática**: Ajuste de longitud para límites de tokens
- **Reflexión y Aprendizaje**: Capacidad de autoevaluación y mejora

## 📁 Estructura del Proyecto

```
Mitosis_Enhanced/
├── agent_core.py           # Núcleo principal del agente
├── model_manager.py        # Gestor unificado de modelos
├── ollama_service.py       # Servicio de integración con Ollama
├── openrouter_service.py   # Servicio de integración con OpenRouter
├── memory_manager.py       # Sistema de gestión de memoria
├── task_manager.py         # Administrador de tareas
├── enhanced_prompts.py     # Sistema de prompts optimizados
├── test_suite.py          # Suite completa de pruebas
├── fixes.py               # Correcciones y utilidades
├── requirements.txt       # Dependencias del proyecto
└── README.md             # Esta documentación
```

## 🛠️ Instalación y Configuración

### Requisitos Previos
- Python 3.11 o superior
- Ollama instalado y ejecutándose (opcional)
- API key de OpenRouter (opcional)

### Instalación
```bash
# Clonar o descargar los archivos del proyecto
cd Mitosis_Enhanced

# Instalar dependencias (la mayoría son módulos estándar de Python)
pip install requests

# Configurar variables de entorno (opcional)
export OPENROUTER_API_KEY="tu_api_key_aqui"
```

### Configuración de Ollama
```bash
# Instalar Ollama (si no está instalado)
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar algunos modelos
ollama pull llama2
ollama pull codellama
ollama pull mistral

# Verificar que Ollama esté ejecutándose
ollama list
```

## 🚀 Uso Básico

### Crear y Usar el Agente

```python
from agent_core import create_mitosis_agent

# Crear agente con configuración básica
agent = create_mitosis_agent(
    ollama_url="http://localhost:11434",
    openrouter_api_key="tu_api_key",  # opcional
    prefer_local=True
)

# Iniciar sesión
session_id = agent.start_session()
print(f"Sesión iniciada: {session_id}")

# Procesar mensaje del usuario
response = agent.process_user_message("Hola, ¿puedes ayudarme con Python?")
print(f"Respuesta: {response}")

# Crear y ejecutar una tarea
task_result = agent.create_and_execute_task(
    title="Crear script de análisis",
    description="Desarrollar un script para analizar datos CSV",
    goal="Crear un script funcional y documentado"
)
print(f"Resultado: {task_result}")

# Obtener estado del agente
status = agent.get_status()
print(f"Estado: {status}")

# Cerrar agente
agent.shutdown()
```

### Configuración Avanzada

```python
from agent_core import MitosisAgent, AgentConfig

# Configuración personalizada
config = AgentConfig(
    ollama_url="http://localhost:11434",
    openrouter_api_key="tu_api_key",
    prefer_local_models=True,
    max_cost_per_1k_tokens=0.01,
    memory_db_path="mi_agente.db",
    max_short_term_messages=100,
    max_concurrent_tasks=2,
    debug_mode=True
)

# Crear agente con configuración personalizada
agent = MitosisAgent(config)
```

## 🧪 Pruebas

### Ejecutar Suite de Pruebas
```bash
cd Mitosis_Enhanced
python test_suite.py
```

### Pruebas Individuales
```python
# Probar gestor de modelos
from model_manager import ModelManager
manager = ModelManager()
manager.refresh_models()
print(f"Modelos disponibles: {len(manager.get_available_models())}")

# Probar memoria
from memory_manager import MemoryManager
memory = MemoryManager()
memory.add_message("user", "Hola")
print(f"Mensajes: {len(memory.get_recent_messages())}")

# Probar tareas
from task_manager import TaskManager
task_manager = TaskManager(memory)
task_id = task_manager.create_task("Test", "Prueba", "Objetivo", [])
print(f"Tarea creada: {task_id}")
```

## 📊 Monitoreo y Estadísticas

### Obtener Estado del Agente
```python
status = agent.get_status()
print(f"""
Estado del Agente:
- Estado actual: {status['state']}
- Tiempo activo: {status['uptime_seconds']:.1f}s
- Mensajes procesados: {status['statistics']['messages_processed']}
- Tareas completadas: {status['statistics']['tasks_completed']}
- Modelos disponibles: {status['available_models']}
""")
```

### Estadísticas de Memoria
```python
memory_stats = agent.memory_manager.get_memory_stats()
print(f"""
Estadísticas de Memoria:
- Mensajes a corto plazo: {memory_stats['short_term_memory']['current_messages']}
- Total de conocimiento: {memory_stats['long_term_memory']['total_knowledge']}
- Total de tareas: {memory_stats['long_term_memory']['total_tasks']}
""")
```

## 🔧 Personalización

### Añadir Plantillas de Prompts Personalizadas
```python
from enhanced_prompts import PromptTemplate, PromptType

# Crear plantilla personalizada
custom_template = PromptTemplate(
    name="mi_plantilla",
    type=PromptType.TOOL_SELECTION,
    template="Mi prompt personalizado: {variable1} {variable2}",
    variables=["variable1", "variable2"],
    description="Plantilla para mi caso de uso específico"
)

# Añadir al gestor de prompts
agent.prompt_manager.add_custom_template(custom_template)
```

### Configurar Callbacks de Herramientas
```python
def mi_callback(resultado):
    print(f"Herramienta ejecutada: {resultado}")

# Registrar callback
agent.task_manager.tool_callbacks["mi_herramienta"] = mi_callback
```

## 🐛 Solución de Problemas

### Problemas Comunes

1. **Ollama no disponible**
   ```bash
   # Verificar que Ollama esté ejecutándose
   curl http://localhost:11434/api/tags
   
   # Reiniciar Ollama si es necesario
   ollama serve
   ```

2. **Error de API key de OpenRouter**
   ```python
   # Verificar configuración
   import os
   print(f"API Key configurada: {bool(os.getenv('OPENROUTER_API_KEY'))}")
   ```

3. **Problemas de memoria**
   ```python
   # Limpiar memoria antigua
   agent.memory_manager.cleanup_old_data(days_old=7)
   
   # Verificar estadísticas
   stats = agent.memory_manager.get_memory_stats()
   print(stats)
   ```

### Logs de Depuración
```python
import logging

# Habilitar logs detallados
logging.basicConfig(level=logging.DEBUG)

# Crear agente en modo debug
config = AgentConfig(debug_mode=True, log_level="DEBUG")
agent = MitosisAgent(config)
```

## 🤝 Contribución

### Estructura de Desarrollo
1. Cada componente es independiente y testeable
2. Usar type hints en todas las funciones
3. Documentar funciones complejas
4. Añadir pruebas para nuevas funcionalidades

### Añadir Nuevas Funcionalidades
1. Crear el módulo en un archivo separado
2. Añadir pruebas en `test_suite.py`
3. Integrar en `agent_core.py`
4. Actualizar documentación

## 📈 Rendimiento

### Benchmarks Típicos
- Inserción de 1000 mensajes: ~1.7s
- 100 búsquedas en conocimiento: ~0.2s
- Inicialización del agente: ~0.5s
- Procesamiento de mensaje: ~2-5s (dependiendo del modelo)

### Optimizaciones
- Base de datos SQLite con índices optimizados
- Cache en memoria para búsquedas frecuentes
- Limpieza automática de datos antiguos
- Optimización de prompts para límites de tokens

## 📄 Licencia

Este proyecto está diseñado como una mejora del agente Mitosis original, incorporando las mejores prácticas de MANUS AI para crear un agente general más robusto y eficiente.

## 🔗 Referencias

- [Ollama Documentation](https://ollama.ai/docs)
- [OpenRouter API](https://openrouter.ai/docs)
- [SQLite Documentation](https://sqlite.org/docs.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

**Desarrollado con ❤️ para la comunidad de IA**

