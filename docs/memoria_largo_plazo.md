# Memoria de Largo Plazo - Mitosis

## Arquitectura General
**Mitosis** es un Agente General Autónomo de IA con arquitectura full-stack moderna:

### Stack Tecnológico
- **Frontend**: React + TypeScript + Tailwind CSS + Vite
- **Backend**: Flask + FastAPI + Python + SocketIO
- **Base de datos**: MongoDB
- **IA/LLM**: Ollama local + OpenRouter como alternativa
- **Comunicación**: WebSocket real-time + HTTP REST API
- **Gestión de procesos**: Supervisor (backend y frontend)

### Puertos y URLs
- **Backend interno**: 0.0.0.0:8001 (mapeado externamente)
- **Frontend**: Puerto 3000/5173 (desarrollo)
- **URL externa**: https://fbccc99e-1d40-4797-ac97-f134f2410c0b.preview.emergentagent.com
- **API base**: `/api/` (todos los endpoints backend usan este prefijo)

### Base de Datos MongoDB
- **URL**: `mongodb://localhost:27017/mitosis`
- **Colecciones principales**: 
  - `tasks` - Almacena todas las tareas del agente
  - `files` - Archivos generados por las tareas
  - `memory` - Sistema de memoria del agente
  - `plans` - Planes de acción generados

## Convenciones de Desarrollo

### Nomenclatura
- **Archivos**: snake_case para Python, camelCase para TypeScript
- **Componentes React**: PascalCase
- **Funciones**: camelCase en TS, snake_case en Python
- **Constantes**: UPPER_SNAKE_CASE
- **URLs**: kebab-case

### Estructura de Endpoints
- Todos los endpoints backend usan prefijo `/api/`
- Estructura: `/api/{módulo}/{acción}`
- Ejemplos: `/api/agent/chat`, `/api/agent/status`, `/api/tools/shell`

### Gestión de Estado
- **Frontend**: Context API + useReducer (no Redux)
- **Backend**: Flask application context + MongoDB
- **WebSocket**: SocketIO con rooms por task_id

## Decisiones Arquitectónicas Importantes

### 1. Sistema de Herramientas (Tools)
- **Patrón**: BaseTool clase abstracta
- **Registry**: Auto-discovery con lazy loading
- **Ubicación**: `/backend/src/tools/`
- **12+ herramientas**: shell, web_search, file_manager, análisis, etc.

### 2. WebSocket vs HTTP
- **WebSocket**: Para comunicación en tiempo real (progress, logs, browser visual)
- **HTTP**: Para operaciones CRUD y configuración
- **Rooms**: Cada tarea tiene su propia room (`task_{task_id}`)

### 3. Sistema de Memoria
- **Tipos**: Corto plazo (buffer), largo plazo (persistente)
- **Almacenamiento**: MongoDB + archivos locales
- **Contexto**: Cada tarea mantiene su propio contexto

### 4. Manejo de Errores
- **Frontend**: ErrorBoundary + try-catch
- **Backend**: Logging centralizado + respuestas JSON consistentes
- **WebSocket**: Eventos de error específicos

## Reglas para el Agente de Mantenimiento

### Antes de Modificar Código
1. **SIEMPRE** consultar `index_funcional.md` para evitar duplicaciones
2. Verificar en `memoria_corto_plazo.md` si hay trabajo en progreso relacionado
3. Revisar `tareas_pendientes.md` para context adicional

### Después de Cada Cambio
1. Actualizar `cambios.md` con descripción detallada del cambio
2. Actualizar `index_funcional.md` si se agregaron/modificaron funciones
3. Agregar a `tareas_pendientes.md` si algo quedó pendiente
4. Resumir en `memoria_corto_plazo.md` para reference inmediata

### Prioridades de Trabajo
1. **Funcionalidad core** del agente (planificación, ejecución)
2. **Herramientas** (tools) - agregar/mejorar capacidades
3. **UI/UX** - mejorar interfaz y experiencia
4. **Performance** - optimizaciones
5. **Testing** - cobertura y calidad

### Patrones a Mantener
- **Error handling**: Siempre usar try-catch con logging
- **Async operations**: Usar async/await consistentemente
- **State management**: Single source of truth
- **Component structure**: Separar lógica de presentación
- **API responses**: Formato consistente con success/error flags

## Configuración de Entorno
- **Variables críticas**: MONGO_URL, OLLAMA_BASE_URL, REACT_APP_BACKEND_URL
- **Secretos**: OPENROUTER_API_KEY, SECRET_KEY
- **Debug**: Logging configurado en múltiples niveles