# Memoria de Largo Plazo - Proyecto Mitosis

## Fecha de Registro: 2025-01-24

## Arquitectura del Sistema
### Stack Tecnológico
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI + Flask-SocketIO + Eventlet
- **Base de Datos**: MongoDB
- **IA**: Ollama (gpt-oss:20b)
- **Navegación Web**: Playwright + Browser-use + Selenium
- **X11 Virtual**: Xvfb para navegación visible en tiempo real

### Componentes Principales
```
/app/
├── backend/                     # FastAPI backend
│   ├── server.py               # Servidor principal
│   ├── src/                    # Código fuente
│   │   ├── routes/            # Rutas API
│   │   ├── services/          # Servicios de negocio  
│   │   ├── tools/             # Herramientas del agente
│   │   └── websocket/         # WebSocket manager
├── frontend/                   # React frontend
│   ├── src/                   # Código fuente React
│   ├── public/                # Assets estáticos
│   └── dist/                  # Build de producción
├── docs/                      # Documentación del sistema
└── start_mitosis.sh           # Script de inicialización
```

## Convenciones de Desarrollo
- **Idioma**: Código en inglés, comentarios en español
- **Funciones**: Pequeñas, puras y bien documentadas
- **Base de datos**: Usar UUIDs en lugar de ObjectID de MongoDB
- **APIs**: Todas las rutas backend deben tener prefijo `/api/`
- **WebSocket**: Eventos en tiempo real para progreso de tareas
- **Navegación**: Screenshots en `/tmp/screenshots/{task_id}/`

## Reglas para el Agente Autónomo
- Siempre actualizar los archivos de memoria después de cambios
- Consultar el índice funcional antes de crear código nuevo
- Registrar todos los cambios en el changelog
- Evitar duplicaciones de código y funcionalidad
- Usar `view_bulk` para ver múltiples archivos simultáneamente
- Mantener trazabilidad completa de modificaciones

## Integración de IA y Navegación
- **Navegación en Tiempo Real**: Sistema implementado con X11 virtual
- **Browser Visual**: Eventos WebSocket para mostrar progreso
- **Screenshots**: Capturados cada 2 segundos durante navegación
- **Herramientas Principales**: web_search, browser_use, analysis, creation

## Variables de Entorno Críticas
- `REACT_APP_BACKEND_URL`: URL del backend para frontend
- `MONGO_URL`: Conexión a MongoDB
- `OLLAMA_ENDPOINT`: Endpoint de Ollama para IA
- `TAVILY_API_KEY`: Clave API para búsqueda web