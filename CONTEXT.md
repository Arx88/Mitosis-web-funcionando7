# CONTEXT.md - Análisis Completo del Proyecto Mitosis

## 📋 RESUMEN EJECUTIVO

**ESTADO GENERAL**: Aplicación de agente general con múltiples refactorings, backend funcional pero con problemas de integración frontend.

**TECNOLOGÍAS**: FastAPI + React + MongoDB + Ollama + WebSocket

**PROBLEMA REPORTADO**: App inestable, necesita revisión completa del workflow y limpieza de código.

---

## 🏗️ ARQUITECTURA ACTUAL

### Backend (/app/backend/)
- **Server Principal**: `server.py` (526 líneas)
- **Framework**: Flask + SocketIO (no FastAPI como esperado)
- **Puerto**: 8001 (0.0.0.0)
- **Base de Datos**: MongoDB (localhost:27017)
- **LLM**: Ollama (https://bef4a4bb93d1.ngrok-free.app)

### Frontend (/app/frontend/)
- **Framework**: React + TypeScript (Vite)
- **Puerto**: 3000
- **Estado**: App.tsx (829 líneas) - MUY COMPLEJO
- **Backend URL**: Variables de entorno configuradas

---

## 🔍 ANÁLISIS DETALLADO DEL CÓDIGO

### Backend Analysis - ACTUALIZADO

#### server.py - Servidor Principal (526 líneas)
```python
# CARACTERÍSTICAS ENCONTRADAS:
- Flask + SocketIO (NO FastAPI como esperado)
- Logging intensivo configurado (/var/log/mitosis_debug.log)
- WebSocket Manager incluido
- Ollama Service integrado
- Tool Manager con 12 herramientas
- Sistema de configuración dinámica
- Health checks implementados
- Fallback routes por si fallan las rutas principales
```

**PROBLEMAS IDENTIFICADOS**:
1. **Importación Compleja**: Líneas 122-155 intentan importar rutas del agente con fallback
2. **ACTUALIZACIÓN**: `src/routes/agent_routes.py` SÍ EXISTE - problema era en path de búsqueda
3. **Inconsistencia**: Se menciona FastAPI pero usa Flask
4. **Código Defensivo**: Múltiples try/catch por importaciones fallidas

#### agent_routes.py - RUTAS PRINCIPALES DEL AGENTE (1658 líneas!)
```python
# ARCHIVO MASIVO CON TODA LA LÓGICA DEL AGENTE:
- Sistema de clasificación LLM para casual vs tareas
- Generación de planes con schema JSON validation
- Ejecución de pasos individuales con herramientas
- TaskManager con persistencia MongoDB
- Plan execution pipeline completo
- Sistema de archivos y carpetas compartidas
- 12 tipos de herramientas (web_search, analysis, creation, etc.)
```

**FUNCIONALIDADES CRÍTICAS ENCONTRADAS**:
1. **is_casual_conversation()**: Clasifica mensajes con Ollama + fallback heurístico
2. **generate_dynamic_plan_with_ai()**: Genera planes JSON validados
3. **execute_plan_with_real_tools()**: Ejecuta pasos con herramientas reales
4. **get_task_data()**: Persistencia MongoDB + fallback memoria
5. **determine_unified_icon()**: Sistema de iconos inteligente
6. **PLAN_SCHEMA**: Validación JSON estricta para planes

#### requirements.txt - Dependencias
- **Total**: 123+ dependencias
- **Categorías**: Flask, MongoDB, AI/ML, WebSocket, Tools
- **Estado**: Muy pesado, posible over-engineering
- **Crítico**: `rpds-py==0.26.0` (mencionado en tests como fix)

#### .env Backend
```bash
# CONFIGURACIÓN ENCONTRADA:
OLLAMA_BASE_URL=https://bef4a4bb93d1.ngrok-free.app
OLLAMA_DEFAULT_MODEL=llama3.1:8b
AGENT_LLM_PROVIDER=ollama
MONGO_URL=mongodb://localhost:27017/task_manager
```

### Frontend Analysis - ACTUALIZADO

#### App.tsx - Componente Principal (829 líneas) - ANÁLISIS COMPLETO
**COMPLEJIDAD EXTREMA**: Archivo demasiado grande con múltiples responsabilidades

**FUNCIONALIDADES IDENTIFICADAS**:
1. **Task Management**: Crear, actualizar, eliminar tareas
2. **Chat Interface**: Mensajes y comunicación
3. **Plan Generation**: Generación automática de planes
4. **File Upload**: Sistema de archivos adjuntos
5. **Dynamic Ideas**: Sugerencias dinámicas
6. **WebSocket**: Comunicación tiempo real
7. **Configuration**: Panel de configuración
8. **NUEVA**: Dual task creation: `createTask()` vs `createTaskWithMessage()`

**PROBLEMAS CRÍTICOS ENCONTRADOS**:
```typescript
// LÍNEAS 174-302: createTaskWithMessage() - Lógica compleja con enhanced title
// LÍNEAS 305-326: startTaskExecutionFromApp() - Auto-execution pipeline
// LÍNEAS 387-458: updateTask() - Sistema con race conditions Y functional updates
// LÍNEAS 122-172: createTask() vs createTaskWithMessage() - DUPLICACIÓN CONTROLADA
```

#### TaskView.tsx - Vista Principal de Tarea (1030 líneas!)
**ARCHIVO MASIVO**: Maneja toda la interfaz de tarea activa

**CARACTERÍSTICAS PRINCIPALES**:
1. **Dual Panel**: Chat (w-1/2) + Terminal (w-1/2) - CSS FIJO aplicado
2. **ChatInterface Integration**: Manejo completo de mensajes
3. **Plan Generation**: Integración con backend para planes
4. **Race Condition Fixes**: Functional updates para prevenir pérdida de mensajes
5. **Auto-execution**: Pipeline automático después de generar plan
6. **File Management**: Sistema de archivos y modals
7. **Terminal Integration**: TerminalView para ejecución en tiempo real

**FIXES CRÍTICOS IMPLEMENTADOS**:
- CSS fix: `md:w-1/2` → `w-1/2` para paneles siempre visibles
- Functional updates para prevenir race conditions
- Message persistence durante plan generation

#### Sidebar.tsx - Navegación Principal (342 líneas)
**FUNCIONALIDADES**:
1. **Task Creation**: Botón "Nueva tarea" 
2. **Search**: Búsqueda por título y contenido
3. **Favorites**: Sistema de favoritos
4. **Task Management**: Editar, eliminar, seleccionar
5. **Collapsed Mode**: Interfaz compacta

#### package.json Frontend
- **Dependencias**: React 19.1.0, Socket.io, Tailwind, etc.
- **Scripts**: Desarrollo y producción configurados
- **Estado**: Dependencias actualizadas

---

## 🚨 PROBLEMAS IDENTIFICADOS - ACTUALIZADO

### 1. Over-Engineering Confirmado
- **Backend**: agent_routes.py tiene 1658 líneas en un solo archivo
- **Frontend**: App.tsx (829 líneas), TaskView.tsx (1030 líneas)
- **Múltiples responsabilidades**: Archivos gigantes con lógica mezclada
- **Duplicación**: Múltiples formas de hacer lo mismo (createTask vs createTaskWithMessage)

### 2. Arquitectura Inconsistente
- **Framework Mixing**: Se menciona FastAPI pero usa Flask + SocketIO
- **Import Strategy**: Sistema defensivo con múltiples fallbacks
- **Error Handling**: Over-defensive programming con try/catch masivo

### 3. Race Conditions - PARCIALMENTE RESUELTO
- **Message Loss**: Durante plan generation - FIXED con functional updates
- **State Updates**: Múltiples updates simultáneos pueden causar inconsistencias
- **Title Overwriting**: Enhanced title podía ser sobrescrito - FIXED

### 4. CSS/UI Issues - RESUELTO
- **ChatInterface Invisible**: `md:w-1/2` → `w-1/2` - FIXED
- **Panel Layout**: Ahora siempre visible independiente del screen size

### 5. Dependencias Excesivas - CONFIRMADO
- **123+ dependencias** en backend (requirements.txt)
- **Paquetes AI/ML**: torch, transformers, sentence-transformers
- **Vector DBs**: chromadb, faiss-cpu
- **Over-kill**: Para un agente simple tiene demasiadas dependencias

### 6. Código Legacy y Fallbacks
- **TaskManager**: Sistema híbrido con MongoDB + memoria legacy
- **Active Task Plans**: Diccionario en memoria como fallback
- **Import Fallbacks**: Múltiples niveles de fallback por servicios no disponibles

---

## 📊 WORKFLOW ACTUAL - COMPLETAMENTE ANALIZADO

### Flujo de Creación de Tareas - REAL:

#### DESDE HOMEPAGE:
1. **Usuario**: Escribe en VanishInput (homepage)
2. **Frontend**: `createTaskWithMessage()` se ejecuta (App.tsx:174-302)
3. **Backend**: Llamada a `/api/agent/generate-plan` (agent_routes.py:945+)
4. **LLM Classification**: `is_casual_conversation()` determina si es casual o tarea
5. **Plan Generation**: `generate_dynamic_plan_with_ai()` crea plan validado JSON
6. **Frontend**: Enhanced title + plan actualiza task
7. **Auto-execution**: `startTaskExecutionFromApp()` inicia pipeline automático

#### DESDE SIDEBAR "NUEVA TAREA":
1. **Usuario**: Click "Nueva tarea" en sidebar
2. **Frontend**: `handleCreateTask()` ejecuta `createTask()` (Sidebar.tsx:43-59)
3. **Task Creation**: Tarea vacía "Tarea X" se crea
4. **TaskView**: Se activa automáticamente (`setActiveTaskId`)
5. **Usuario**: Escribe primer mensaje en ChatInterface
6. **Backend**: Similar pipeline que homepage pero en TaskView

### Pipeline de Ejecución - REAL:
1. **Plan Generated**: JSON schema validado (PLAN_SCHEMA)
2. **Step Execution**: `execute_single_step_logic()` procesa cada paso
3. **Tool Integration**: 12 herramientas disponibles (web_search, analysis, creation, etc.)
4. **Real Files**: Se crean archivos reales en `/app/backend/static/generated_files/`
5. **WebSocket Updates**: Tiempo real via WebSocketManager
6. **MongoDB Persistence**: TaskManager guarda estado completo

### Problemas en el Workflow - ACTUALIZADOS:
- **CSS Issue**: Era `md:w-1/2` causing ChatInterface invisible - FIXED
- **Race Conditions**: Functional updates implementados para message persistence
- **Message Loss**: Durante plan generation - FIXED con functional updates
- **Auto-execution**: Pipeline funcionando correctamente

---

## 🧠 ANÁLISIS PROFUNDO DE SERVICIOS

### OllamaService - SERVICIO COMPLEJO (702 líneas)
**CARACTERÍSTICAS**:
- **Endpoint Dinámico**: Puede cambiar endpoint en runtime
- **Multi-Model Support**: Configuraciones específicas por modelo
- **Robust JSON Parsing**: 4 estrategias diferentes para parsear respuestas
- **Request Optimization**: Parámetros optimizados por modelo específico
- **Casual vs Task Mode**: Diferentes system prompts
- **Error Recovery**: Múltiples niveles de fallback

**MODELOS CONFIGURADOS**:
- `llama3.1:8b` (temperatura 0.15, timeout 180s)
- `qwen3:32b` (temperatura 0.1, timeout 480s) 
- `deepseek-r1:32b` (temperatura 0.12, timeout 420s)

### TaskManager - PERSISTENCIA HÍBRIDA (424 líneas)
**ARQUITECTURA**:
- **MongoDB Primary**: Base de datos principal
- **Memory Cache**: Cache activo para acceso rápido
- **Recovery System**: Recuperación de tareas incompletas al startup
- **Cleanup System**: Limpieza automática de tareas viejas
- **Statistics**: Sistema completo de estadísticas

**MÉTODOS CRÍTICOS**:
1. `create_task()`: Persistencia completa en MongoDB
2. `get_task()`: Cache-first, fallback a MongoDB
3. `update_task_step_status()`: Actualizaciones granulares
4. `recover_incomplete_tasks_on_startup()`: Recovery automático

### ToolManager - ECOSISTEMA DE HERRAMIENTAS (502 líneas) 
**12 HERRAMIENTAS DISPONIBLES**:
1. **shell**: ShellTool - Comandos del sistema
2. **web_search**: WebSearchTool - Búsqueda web real
3. **file_manager**: FileManagerTool - Gestión de archivos
4. **tavily_search**: TavilySearchTool - API Tavily
5. **comprehensive_research**: ComprehensiveResearchTool
6. **deep_research**: DeepResearchTool (opcional)
7. **enhanced_web_search**: EnhancedWebSearchTool (opcional)
8. **firecrawl**: FirecrawlTool (opcional)
9. **qstash**: QStashTool (opcional) 
10. **playwright**: PlaywrightTool (opcional)
11. **autonomous_web_navigation**: AutonomousWebNavigation (opcional)
12. **basic_web_search**: BasicWebSearchTool (opcional)

**SEGURIDAD IMPLEMENTADA**:
- Comandos bloqueados en shell
- Paths permitidos/bloqueados para archivos
- Timeouts por herramienta
- Rate limiting y size limits
- Container isolation (opcional)

---

## 📋 WORKFLOW COMPLETO DETALLADO - ANÁLISIS FINAL

### ESTADO ACTUAL - VERDADERAMENTE FUNCIONAL:

**EVIDENCIA DESDE EL CÓDIGO**:
1. ✅ **Backend Robusto**: `agent_routes.py` tiene todo el pipeline implementado
2. ✅ **LLM Integration**: OllamaService con 4 estrategias de parsing
3. ✅ **Plan Generation**: Schema JSON validation completa
4. ✅ **Step Execution**: Ejecución real con 12 herramientas
5. ✅ **File Generation**: Archivos reales en `/app/backend/static/generated_files/`
6. ✅ **MongoDB Persistence**: TaskManager híbrido con recovery
7. ✅ **Frontend Integration**: TaskView con chat + terminal
8. ✅ **Race condition fixes**: Functional updates implementados

### WORKFLOW TÉCNICO REAL:

#### 1. TASK CREATION:
- **Homepage**: `createTaskWithMessage()` → plan generation inmediato
- **Sidebar**: `createTask()` → task vacía → user input → plan generation

#### 2. PLAN GENERATION: 
- `is_casual_conversation()` → Clasifica mensaje (LLM + fallback)
- `generate_dynamic_plan_with_ai()` → Genera plan JSON validado
- **PLAN_SCHEMA validation** → 3-6 pasos, herramientas específicas
- `determine_unified_icon()` → Icono inteligente basado en contenido

#### 3. PLAN EXECUTION:
- `execute_plan_with_real_tools()` → Pipeline completo de ejecución
- `execute_single_step_logic()` → Cada paso con herramienta específica
- **Real tool execution** → WebSearch, Analysis, Creation, etc.
- **File generation** → Archivos reales con contenido generado
- **MongoDB persistence** → Estado guardado paso a paso

#### 4. FRONTEND INTEGRATION:
- **TaskView** → Chat (w-1/2) + Terminal (w-1/2)
- **Message persistence** → Functional updates previenen race conditions
- **Real-time updates** → TerminalView muestra progreso
- **Auto-execution** → Pipeline automático después de plan generation

---

## 📝 NOTAS DE ANÁLISIS

**TIMESTAMP**: Enero 2025
**ANÁLISIS**: 20% completado
**ESTADO**: Backend parcialmente analizado, frontend estructura identificada
**CRÍTICO**: Necesito encontrar los archivos src/ reales para continuar

---

*Este archivo se actualiza conforme avanzo en el análisis del código*