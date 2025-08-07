# Memoria de Largo Plazo - Proyecto Mitosis

## Fecha de Registro: 2025-01-24

## Arquitectura del Sistema
### Stack Tecnológico
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI + Flask-SocketIO + Eventlet + Gunicorn (Modo Producción)
- **Base de Datos**: MongoDB
- **IA**: Ollama (gpt-oss:20b) - https://e8da53409283.ngrok-free.app
- **Navegación Web**: Playwright + Browser-use + Selenium + X11 Virtual
- **X11 Virtual**: Xvfb para navegación visible en tiempo real (Display :99)
- **Modo Despliegue**: Producción optimizada con archivos estáticos

### Componentes Principales
```
/app/
├── backend/                     # FastAPI backend
│   ├── server.py               # Servidor principal
│   ├── production_wsgi.py      # Servidor WSGI modo producción
│   ├── src/                    # Código fuente
│   │   ├── routes/            # Rutas API (todas con prefijo /api/)
│   │   ├── services/          # Servicios de negocio  
│   │   ├── tools/             # 7 herramientas del agente
│   │   └── websocket/         # WebSocket manager + eventos tiempo real
├── frontend/                   # React frontend
│   ├── src/                   # Código fuente React
│   ├── public/                # Assets estáticos
│   └── dist/                  # Build de producción (OPTIMIZADO)
├── docs/                      # Documentación del sistema completa
└── start_mitosis.sh           # Script de inicialización modo producción
```

## Convenciones de Desarrollo
- **Idioma**: Código en inglés, comentarios en español
- **Funciones**: Pequeñas, puras y bien documentadas
- **Base de datos**: Usar UUIDs en lugar de ObjectID de MongoDB
- **APIs**: Todas las rutas backend deben tener prefijo `/api/` (CRÍTICO para Kubernetes)
- **WebSocket**: Eventos en tiempo real para progreso de tareas + browser_visual
- **Navegación**: Screenshots en `/tmp/screenshots/{task_id}/` cada 2 segundos
- **Modo Producción**: Frontend como archivos estáticos + backend gunicorn + eventlet

## Reglas para el Agente Autónomo
- Siempre actualizar los archivos de memoria después de cambios
- Consultar el índice funcional antes de crear código nuevo
- Registrar todos los cambios en el changelog
- Evitar duplicaciones de código y funcionalidad
- Usar `view_bulk` para ver múltiples archivos simultáneamente
- Mantener trazabilidad completa de modificaciones
- **NUNCA** modificar URLs o puertos en archivos .env
- Usar variables de entorno SIEMPRE para configuración

## Sistema Jerárquico Robusto (IMPLEMENTADO)
### Fase 1: Web Search Jerárquico
- **Estado**: ✅ IMPLEMENTADO en execute_web_search_step()
- **8 funciones auxiliares**: Sub-planificador, ejecutor, evaluador, re-planificador
- **IA integrada**: Ollama genera sub-planes específicos automáticamente
- **Auto-evaluación**: Sistema evalúa completitud y re-planifica si necesario
- **Robustez**: De 1 búsqueda → 3-7 búsquedas específicas
- **Transparencia**: Progreso interno visible al usuario

### Fase 2: Enhanced Analysis Jerárquico  
- **Estado**: ✅ IMPLEMENTADO en execute_enhanced_analysis_step()
- **Múltiples análisis**: contextual, data, trend, comparative
- **Auto-evaluación**: Criteria ≥2 análisis + ≥300 chars + ≥70% confianza
- **Re-análisis adaptivo**: Síntesis adicional si insuficiente

## Integración de IA y Navegación en Tiempo Real
- **Navegación Visual**: Sistema completamente implementado con X11 virtual (Display :99)
- **Browser Visual Events**: Eventos WebSocket para mostrar progreso real
- **Screenshots Reales**: Capturados cada 2 segundos durante navegación web
- **RealTimeBrowserTool**: Integrado con sistema jerárquico
- **Herramientas**: web_search (jerárquico), enhanced_analysis (jerárquico), creation, processing

## Variables de Entorno Críticas (NO MODIFICAR)
- `REACT_APP_BACKEND_URL`: URL del backend para frontend (AUTO-DETECTADA)
- `MONGO_URL`: Conexión a MongoDB (configurada internamente)
- `OLLAMA_ENDPOINT`: https://e8da53409283.ngrok-free.app
- `TAVILY_API_KEY`: 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
- `DISPLAY`: :99 (X11 virtual server para navegación)

## Arquitectura de Servicios (Modo Producción)
### Backend
- **Proceso**: Gunicorn + Eventlet worker 
- **Puerto interno**: 8001 (mapeado externamente por Kubernetes)
- **WebSocket**: SocketIO con eventlet para eventos en tiempo real
- **APIs**: 7 herramientas + endpoints de salud + Ollama integration

### Frontend  
- **Proceso**: Serve (archivos estáticos optimizados)
- **Puerto interno**: 3000 (mapeado externamente por Kubernetes)
- **Build**: Optimizado para producción sin hot-reload
- **Performance**: Máxima con archivos estáticos

### Infraestructura
- **MongoDB**: Persistencia de tareas y resultados
- **X11 Virtual**: Display :99 (PID 2085) para navegación visible
- **Supervisor**: Gestión automática de todos los servicios
- **CORS**: Configuración ultra-dinámica para múltiples dominios

## Sistema de Testing y Validación
- **Playwright**: Navegación web automatizada en tiempo real
- **Selenium**: Backup para navegación web
- **Chrome/Chromium**: Navegadores disponibles para testing
- **X11 Virtual**: Navegación visible para debugging
- **WebSocket Testing**: Eventos en tiempo real verificados

## Estado del Sistema (2025-01-24)
✅ **COMPLETAMENTE OPERATIVO EN MODO PRODUCCIÓN**
- Sistema jerárquico Fase 1 y 2 implementados
- Navegación web en tiempo real funcionando  
- Todos los servicios corriendo correctamente
- URL externa accesible globalmente
- Testing tools completamente instalados
- IA integration verificada y funcional