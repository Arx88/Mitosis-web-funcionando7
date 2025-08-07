# Índice Funcional - Proyecto Mitosis

## 📊 Estado: EN CONSTRUCCIÓN
**Última Actualización**: 2025-01-24 (Inicio de sesión)

---

## 🏗️ Estructura del Sistema (Basada en test_result.md)

### BACKEND (`/app/backend/`)
```
server.py                    # Servidor principal FastAPI
src/
├── routes/
│   └── agent_routes.py     # Rutas principales del agente
├── services/               # Servicios de negocio
├── tools/                  # Herramientas del agente
│   ├── tool_manager.py     # Gestor de herramientas
│   └── unified_web_search_tool.py # 🔍 BÚSQUEDA WEB
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

### ✅ NAVEGACIÓN WEB EN TIEMPO REAL
- **X11 Virtual**: Display :99 (Xvfb PID 2036)
- **RealTimeBrowserTool**: Implementada
- **Browser Visual Events**: WebSocket configurado
- **Screenshots**: Directorio `/tmp/screenshots/`
- **Playwright**: Chromium instalado y funcional

### ✅ INTELIGENCIA ARTIFICIAL  
- **Ollama**: Endpoint configurado (gpt-oss:20b)
- **Modelos**: gpt-oss:20b disponible
- **API Integration**: Endpoints `/api/agent/ollama/`

### ✅ HERRAMIENTAS DEL AGENTE
- **web_search**: Búsqueda web con Tavily API
- **browser_use**: Navegación automatizada  
- **analysis**: Análisis de datos
- **creation**: Creación de contenido
- **file_manager**: Gestión de archivos
- **unified_web_search**: 🔍 **PROBLEMA REPORTADO AQUÍ**

---

## 🔴 PROBLEMAS IDENTIFICADOS

### ❌ BÚSQUEDA WEB - PROBLEMA CRÍTICO
**Archivo**: `unified_web_search_tool.py`
**Síntoma**: "abre el navegador pero no se queda en el home y no lo usa para buscar"
**Estado**: REQUIERE INVESTIGACIÓN INMEDIATA

### ⚠️ PROBLEMAS PREVIOS RESUELTOS (según test_result.md)
- **Botones deshabilitados**: ✅ CORREGIDO
- **Duplicación de tareas**: ✅ CORREGIDO  
- **WebSocket conexión**: ✅ FUNCIONANDO
- **Tool mapping errors**: ✅ CORREGIDO

---

## 📋 FUNCIONALIDADES POR VERIFICAR

### 🔄 PENDIENTE DE MAPEAR
- [ ] **Rutas API Completas**: Mapear todos los endpoints
- [ ] **Componentes React**: Catalogar componentes frontend
- [ ] **Servicios Backend**: Documentar servicios individuales
- [ ] **Configuración WebSocket**: Detallar eventos disponibles
- [ ] **Herramientas Completas**: Lista exhaustiva de tools

### 🔍 ANÁLISIS REQUERIDO
- [ ] **Pipeline de Navegación**: Flujo completo de búsqueda web
- [ ] **Gestión de Tareas**: Cómo se procesan las tareas del usuario
- [ ] **Eventos Tiempo Real**: Mapeo completo de eventos WebSocket
- [ ] **Integración IA**: Flujo completo Ollama → Agente → Usuario

---

## 🎯 PRÓXIMOS PASOS PARA COMPLETAR ÍNDICE

1. **Explorar Backend Completo**
   ```bash
   view_bulk [todos los archivos .py de backend]
   ```

2. **Mapear Frontend Detallado**
   ```bash
   view_bulk [componentes React principales]
   ```

3. **Analizar Herramientas**
   ```bash
   grep_tool "class.*Tool" --include="*.py" /app/backend/src/tools/
   ```

4. **Documentar APIs**
   ```bash
   grep_tool "@app\\..*route" --include="*.py" /app/backend/
   ```

---

## 🚨 NOTA IMPORTANTE
Este índice está en construcción. La prioridad actual es resolver el problema de búsqueda web antes de completar el mapeo completo del sistema.

**ARCHIVO CRÍTICO A INVESTIGAR**: `/app/backend/src/tools/unified_web_search_tool.py`