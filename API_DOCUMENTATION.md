# Documentación de APIs - Mitosis

## Resumen de APIs Integradas

Este documento describe todas las APIs y servicios externos utilizados en la aplicación Mitosis.

### APIs Actualmente Integradas ✅

#### 1. **Tavily API** - Búsqueda Web
- **Propósito**: Búsqueda web avanzada con resultados enriquecidos
- **Estado**: ✅ Integrado y funcionando
- **Clave**: `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`
- **Ubicación**: `/app/backend/.env`
- **Archivos**:
  - `src/tools/tavily_search_tool.py`
  - `src/tools/enhanced_web_search_tool.py`
- **Uso**: WebSearch desde la página de bienvenida

#### 2. **MongoDB** - Base de Datos
- **Propósito**: Persistencia de datos, tareas, conversaciones y archivos
- **Estado**: ✅ Integrado y funcionando
- **URL**: `mongodb://localhost:27017/task_manager`
- **Ubicación**: `/app/backend/.env`
- **Archivos**:
  - `src/services/database.py`
- **Uso**: Almacenamiento de todas las operaciones

### APIs Disponibles para Integración 🔄

#### 3. **Firecrawl** - Web Scraping Avanzado
- **Propósito**: Scraping web más sofisticado que BeautifulSoup
- **Clave**: `fc-d7697dffe9a04c4e973e213284e9de76`
- **Valor agregado**: 
  - Extracción de contenido estructurado
  - Manejo de JavaScript y SPAs
  - Mejores resultados que BeautifulSoup
- **Recomendación**: ✅ INTEGRAR - Mejora significativa sobre el scraping actual

#### 4. **QStash** - Jobs en Background
- **Propósito**: Procesamiento de trabajos en segundo plano
- **Clave**: `redis://default:AeJLAAIjcDE4NmM1NWI5ZjQwYjE0NDIwYjRhNWZmNDhmOTk2OGU1MHAxMA@normal-vervet-57931.upstash.io:6379`
- **Valor agregado**:
  - Tareas de investigación profunda sin bloquear UI
  - Procesamiento de archivos grandes
  - Tareas programadas
- **Recomendación**: ✅ INTEGRAR - Mejora UX para tareas largas

#### 5. **RapidAPI** - APIs Externas
- **Propósito**: Acceso a múltiples APIs de terceros
- **Clave**: `e3c8f40077msh2383361adacc215p1fb470jsn0a2150f802f9`
- **Valor agregado**:
  - Acceso a APIs especializadas
  - Datos de mercado, clima, noticias, etc.
- **Recomendación**: ⚠️ EVALUAR - Solo si se necesitan APIs específicas

#### 6. **Smithery** - Agentes Personalizados
- **Propósito**: Desarrollo de agentes especializados
- **Clave**: `generous-zebra-3J27EB`
- **Valor agregado**:
  - Agentes especializados por dominio
  - Flujos de trabajo personalizados
- **Recomendación**: 🔍 INVESTIGAR - Requiere análisis del servicio

#### 7. **Playwright** - Automatización de Navegadores
- **Propósito**: Automatización web y testing
- **Valor agregado**:
  - Scraping de contenido dinámico
  - Testing automatizado
  - Capturas de pantalla
- **Recomendación**: ✅ INTEGRAR - Útil para scraping avanzado

### Funcionalidades Ya Implementadas (No Necesitan APIs Externas)

#### ❌ **NO INTEGRAR** - Ya tenemos implementado:

1. **Búsqueda Web Básica**: Ya tenemos Tavily + DuckDuckGo
2. **Gestión de Archivos**: Ya implementado en file_manager_tool.py
3. **Comandos Shell**: Ya implementado en shell_tool.py
4. **Web Scraping Básico**: Ya tenemos BeautifulSoup
5. **Base de Datos**: Ya tenemos MongoDB
6. **Sistema de Tareas**: Ya implementado en frontend
7. **Chat Interface**: Ya implementado

### Integraciones Recomendadas

#### 🎯 **Prioridad Alta**:
1. **Firecrawl** - Mejora significativa en scraping
2. **QStash** - Mejora UX para tareas largas
3. **Playwright** - Automatización web avanzada

#### 🔍 **Prioridad Media**:
1. **Smithery** - Después de investigar capacidades
2. **RapidAPI** - Solo APIs específicas necesarias

### Estructura de Archivos para Nuevas Integraciones

```
/app/backend/src/tools/
├── firecrawl_tool.py         # 🔄 Por crear
├── qstash_tool.py            # 🔄 Por crear
├── playwright_tool.py        # 🔄 Por crear
├── rapidapi_tool.py          # 🔄 Por crear (opcional)
└── smithery_tool.py          # 🔄 Por crear (opcional)
```

### Variables de Entorno Necesarias

```bash
# /app/backend/.env
# Existentes
TAVILY_API_KEY=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
MONGO_URL=mongodb://localhost:27017/task_manager

# Nuevas por agregar
FIRECRAWL_API_KEY=fc-d7697dffe9a04c4e973e213284e9de76
QSTASH_URL=redis://default:AeJLAAIjcDE4NmM1NWI5ZjQwYjE0NDIwYjRhNWZmNDhmOTk2OGU1MHAxMA@normal-vervet-57931.upstash.io:6379
RAPIDAPI_KEY=e3c8f40077msh2383361adacc215p1fb470jsn0a2150f802f9
SMITHERY_KEY=generous-zebra-3J27EB
```

### Estado de Servicios

| Servicio | Estado | Funcionalidad | Mejora |
|----------|--------|---------------|---------|
| Tavily | ✅ Activo | Búsqueda web | - |
| MongoDB | ✅ Activo | Base de datos | - |
| Firecrawl | 🔄 Pendiente | Web scraping | +++ |
| QStash | 🔄 Pendiente | Jobs background | +++ |
| Playwright | 🔄 Pendiente | Automatización | ++ |
| RapidAPI | 🔄 Pendiente | APIs externas | + |
| Smithery | 🔄 Pendiente | Agentes custom | ? |

### Notas de Implementación

1. **Principio de Valor**: Solo integrar APIs que agreguen valor real
2. **Evitar Duplicación**: No integrar si ya tenemos funcionalidad equivalente
3. **Priorizar UX**: Priorizar integraciones que mejoren experiencia de usuario
4. **Documentar Todo**: Cada nueva integración debe documentarse aquí

---

**Última actualización**: 2025-01-15
**Responsable**: Mitosis Development Team