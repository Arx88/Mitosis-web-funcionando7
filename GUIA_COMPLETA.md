# 🤖 Agente General - Sistema Completo

## 🎯 Estado del Proyecto
✅ **COMPLETADO AL 100%** - El sistema está listo para usar

### ✅ Funcionalidades Implementadas
- **Backend Flask completo** con integración a Ollama
- **Sistema de herramientas extensible** (shell, web search, file manager)
- **API RESTful** con todos los endpoints necesarios
- **Frontend React** completamente funcional
- **Interfaz de chat** con visualización de resultados en tiempo real
- **Terminal integrado** que muestra la ejecución de comandos
- **Gestión de tareas** con planes de acción
- **Seguridad implementada** con validaciones y restricciones

## 🚀 Instrucciones de Uso

### Paso 1: Iniciar Ollama en tu ordenador
```bash
# Asegúrate de que Ollama esté ejecutándose
ollama serve

# Verificar que está disponible
curl http://localhost:11434/api/tags
```

### Paso 2: Iniciar el Backend
```bash
cd /app/agent_backend
./start.sh
```

### Paso 3: Iniciar el Frontend
```bash
cd /app/agent_project
yarn dev
```

### Paso 4: Acceder a la aplicación
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/health

## 🔧 Herramientas Disponibles

### 1. **Shell Tool**
Ejecuta comandos de terminal de forma segura
- **Parámetros**: `{"command": "ls -la"}`
- **Restricciones**: Comandos peligrosos bloqueados
- **Timeout**: 30 segundos

### 2. **Web Search Tool**
Busca información en internet y extrae contenido
- **Búsqueda**: `{"query": "Python tutorial"}`
- **Extracción**: `{"action": "extract", "url": "https://example.com"}`
- **Límite**: 10 resultados máximo

### 3. **File Manager Tool**
Gestiona archivos y directorios de forma segura
- **Acciones**: read, write, create, delete, list, copy, move, mkdir
- **Ejemplo**: `{"action": "read", "path": "/tmp/file.txt"}`
- **Seguridad**: Rutas restringidas para proteger el sistema

## 📱 Uso de la Interfaz

### Crear una Nueva Tarea
1. Haz clic en "Crear tarea" en la barra lateral
2. Escribe el título de tu tarea
3. Comienza a chatear con el agente

### Interactuar con el Agente
- **Escribe tu solicitud** en el chat
- **El agente analizará** tu petición
- **Ejecutará herramientas** si es necesario
- **Verás los resultados** en tiempo real en el terminal

### Ejemplos de Peticiones
```
"Ejecuta ls -la para ver los archivos del directorio actual"
"Busca información sobre Python en internet"
"Crea un archivo llamado test.txt con contenido 'Hola mundo'"
"Lista los archivos en el directorio /tmp"
"Busca en Google información sobre machine learning"
```

## 🛡️ Características de Seguridad

### Comandos Shell Bloqueados
- `rm -rf /`, `mkfs`, `dd if=`, `format`
- `shutdown`, `reboot`, `halt`, `poweroff`
- Y otros comandos peligrosos

### Rutas de Archivos Restringidas
- **Permitidas**: `/tmp`, `/var/tmp`, `/app`, `/home`
- **Bloqueadas**: `/etc`, `/bin`, `/sbin`, `/usr/bin`

### Timeouts y Límites
- **Shell**: 30 segundos máximo
- **Web Search**: 15 segundos máximo
- **Resultados**: 10 resultados máximo

## 🔄 API Endpoints

### Chat
```bash
POST /api/agent/chat
{
  "message": "Tu mensaje aquí",
  "context": {"task_id": "optional"}
}
```

### Estado del Sistema
```bash
GET /api/agent/status
```

### Herramientas Disponibles
```bash
GET /api/agent/tools
```

### Modelos de Ollama
```bash
GET /api/agent/models
POST /api/agent/models
{"model": "llama3.2"}
```

## 🧠 Integración con Ollama

El sistema está configurado para usar Ollama en `localhost:11434`. Los modelos recomendados son:
- `llama3.2` (por defecto)
- `llama3.1`
- `mixtral`
- `codellama`

### Instalar un Modelo
```bash
ollama pull llama3.2
```

## 🎮 Ejemplos de Uso

### Ejemplo 1: Análisis de Sistema
```
Usuario: "Analiza el sistema y muéstrame información del disco"
Agente: [Ejecuta comandos como df -h, du -sh, etc.]
```

### Ejemplo 2: Búsqueda e Investigación
```
Usuario: "Busca información sobre las últimas tendencias en IA"
Agente: [Busca en internet y extrae contenido relevante]
```

### Ejemplo 3: Gestión de Archivos
```
Usuario: "Crea un script Python que imprima 'Hola mundo'"
Agente: [Crea archivo .py con el código correspondiente]
```

## 🔧 Resolución de Problemas

### Ollama no conecta
- Verificar que Ollama esté ejecutándose: `ollama serve`
- Comprobar el puerto: `curl localhost:11434/api/tags`

### Backend no inicia
- Verificar dependencias: `pip install -r requirements.txt`
- Revisar logs: `cat backend.log`

### Frontend no conecta
- Verificar que el backend esté en puerto 5000
- Comprobar CORS en la configuración

## 📊 Monitoreo

### Logs del Sistema
- **Backend**: `/app/agent_backend/backend.log`
- **Frontend**: `/app/agent_project/frontend.log`

### Health Check
```bash
curl http://localhost:5000/health
```

## 🚀 Próximos Pasos Sugeridos

1. **Añadir más herramientas** (calculadora, generador de código, etc.)
2. **Implementar persistencia** de conversaciones
3. **Añadir autenticación** de usuarios
4. **Mejorar la interfaz** con más funcionalidades
5. **Implementar WebSockets** para comunicación en tiempo real

---

## 🎉 ¡El sistema está listo para usar!

El Agente General está completamente funcional y listo para ayudarte con cualquier tarea que necesites. Solo asegúrate de que Ollama esté ejecutándose en tu ordenador y podrás comenzar a interactuar con el agente inmediatamente.