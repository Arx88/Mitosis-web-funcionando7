# Índice Funcional - Proyecto Mitosis

## 📊 Estado: EN CONSTRUCCIÓN (Diagnóstico Crítico Completado)
**Última Actualización**: 2025-01-24 - Problema Crítico Identificado

---

## 🚨 PROBLEMA CRÍTICO IDENTIFICADO

### ❌ BÚSQUEDA WEB - FUNCIONALIDAD CORE ROTA
**Archivo**: `/app/backend/src/tools/unified_web_search_tool.py`
**Error**: `Cannot run the event loop while another loop is running`
**Síntoma Exact Match**: "abre el navegador pero no se queda en el home y no lo usa para buscar"

**DIAGNÓSTICO TÉCNICO**:
1. ✅ X11 Server funcional (Display :99, PID 2054)
2. ✅ RealTimeBrowserTool se carga correctamente 
3. ✅ WebSocket se inicializa exitosamente
4. ❌ **FALLA EN EJECUCIÓN**: Conflicto asyncio vs eventlet
5. ❌ **FALLBACK FALLA**: Mismo problema event loop
6. ❌ **RESULTADO**: Sin resultados reales de búsqueda

---

## 🏗️ Estructura del Sistema (Verificada)

### BACKEND (`/app/backend/`)
```
server.py                    # Servidor principal FastAPI
src/
├── routes/
│   └── agent_routes.py     # Rutas principales del agente
├── services/               # Servicios de negocio
├── tools/                  # Herramientas del agente
│   ├── tool_manager.py     # Gestor de herramientas
│   └── unified_web_search_tool.py # 🔴 PROBLEMA CRÍTICO AQUÍ
├── websocket/              # Gestión WebSocket
└── core/
    └── agent_unified.py    # Agente principal consolidado
```

### FRONTEND (`/app/frontend/`)
```
src/
├── App.js                  # Componente principal React
├── App.css                # Estilos del componente
├── index.js               # Punto de entrada
└── index.css              # Estilos globales
public/                     # Assets estáticos
dist/                       # Build de producción
```

---

## 🛠️ Funcionalidades Implementadas

### ✅ SISTEMA CORE
- **Servidor FastAPI**: Puerto 8001, modo producción
- **Frontend React**: Puerto 3000, build optimizado  
- **Base de Datos**: MongoDB operacional
- **WebSocket**: Eventos en tiempo real funcionando
- **CORS**: Configuración dinámica
- **URL Externa**: https://45dfeaa6-7eaf-4101-bc6c-20901a318336.preview.emergentagent.com

### ⚠️ NAVEGACIÓN WEB - PROBLEMÁTICA
- **X11 Virtual**: ✅ Display :99 (Xvfb PID 2054) - FUNCIONANDO
- **RealTimeBrowserTool**: ⚠️ Importa pero falla en ejecución
- **Browser Visual Events**: ⚠️ WebSocket OK, pero sin datos por fallo ejecución
- **Screenshots**: ❌ Directorio `/tmp/screenshots/` pero sin capturas por fallo
- **Playwright**: ❌ Falla por conflicto event loop asyncio vs eventlet

### ✅ INTELIGENCIA ARTIFICIAL  
- **Ollama**: Endpoint configurado (gpt-oss:20b)
- **Modelos**: gpt-oss:20b disponible
- **API Integration**: Endpoints `/api/agent/ollama/` funcionando

### ⚠️ HERRAMIENTAS DEL AGENTE
- **web_search**: ❌ **ROTA** - Conflicto event loop crítico
- **browser_use**: ❌ **PROBLEMÁTICA** - Misma base asyncio
- **analysis**: ✅ Funcionando
- **creation**: ✅ Funcionando  
- **file_manager**: ✅ Funcionando
- **processing**: ✅ Funcionando

---

## 🔴 ANÁLISIS DETALLADO DEL PROBLEMA

### 📊 TESTING EJECUTADO Y RESULTADOS

#### 1. **Test API Chat**
```bash
curl -X POST "http://localhost:8001/api/agent/chat" \
  -d '{"message": "Busca información sobre inteligencia artificial"}'
```
**Resultado**: ✅ Plan generado correctamente con tool="web_search"

#### 2. **Test Ejecución Búsqueda**
```bash
curl -X POST "http://localhost:8001/api/agent/execute-step-detailed/chat-1754553686/step-1"
```
**Resultado**: ❌ "Los resultados de las búsquedas realizadas no arrojaron ninguna fuente"

#### 3. **Análisis de Logs**
```
[REAL_TIME_BROWSER] 🔌 WebSocket inicializado para navegación en tiempo real
🌐 NAVEGACIÓN WEB: ⚠️ Error en navegación en tiempo real: Cannot run the event loop while another loop is running  
🌐 NAVEGACIÓN WEB: ❌ Error ejecutando Playwright fallback: Cannot run the event loop while another loop is running
🌐 NAVEGACIÓN WEB: ⚠️ Búsqueda completada sin resultados reales
```

### 🔬 CAUSA RAÍZ CONFIRMADA
**PROBLEMA ARQUITECTURAL**: 
- Backend usa **Flask + Eventlet** (event loop principal)
- `unified_web_search_tool.py` ejecuta **Playwright (asyncio)**
- Python **no permite** múltiples event loops asyncio concurrentes
- **Resultado**: Navegación se inicializa pero **falla en ejecución**

---

## 📋 FUNCIONALIDADES POR REPARAR

### 🚨 CRÍTICAS - REQUIEREN SOLUCIÓN INMEDIATA
- [ ] **unified_web_search_tool.py**: Implementar subprocess/thread para asyncio
- [ ] **RealTimeBrowserTool**: Verificar compatibilidad después de fix
- [ ] **Browser Visual Events**: Re-testing después de solución
- [ ] **Screenshot Pipeline**: Verificar captura en tiempo real funciona

### 🔄 PENDIENTE DE VERIFICAR POST-FIX
- [ ] **Pipeline de Navegación**: Flujo completo de búsqueda web
- [ ] **Gestión de Tareas**: Verificar que web_search ejecuta correctamente  
- [ ] **Eventos Tiempo Real**: Confirmar browser_visual events llegando
- [ ] **Integración IA**: Flujo completo query → web_search → resultados → análisis

---

## 🎯 PLAN DE ACCIÓN INMEDIATO

### FASE 1: SOLUCIÓN TÉCNICA (CRÍTICA)
1. **Modificar unified_web_search_tool.py**
   - Implementar subprocess para operaciones Playwright
   - Aislar asyncio del event loop principal eventlet
   - Mantener funcionalidad de screenshots en tiempo real

2. **Testing de Validación**
   - Probar búsqueda con query real
   - Verificar screenshots se generan
   - Confirmar resultados no simulados

### FASE 2: COMPLETAR MAPEO FUNCIONAL
1. **Explorar Backend Completo**
2. **Mapear Frontend Detallado** 
3. **Documentar APIs Completas**

---

## 🚨 ESTADO CRÍTICO
**BÚSQUEDA WEB NO FUNCIONAL**: La funcionalidad core del sistema (búsqueda e investigación web) está completamente rota debido al conflicto de event loops. 

**IMPACTO EN USUARIO**: El sistema genera planes correctos pero NO puede ejecutar búsquedas reales, por lo que las tareas fallan sin resultados útiles.

**PRIORIDAD MÁXIMA**: Solucionar conflicto asyncio/eventlet en unified_web_search_tool.py