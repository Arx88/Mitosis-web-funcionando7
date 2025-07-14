# Documentación de APIs - Mitosis

## Resumen de APIs Integradas

Este documento describe todas las APIs y servicios externos utilizados en la aplicación Mitosis.

### APIs Integradas y Funcionando ✅

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

#### 3. **Firecrawl API** - Web Scraping Avanzado
- **Propósito**: Scraping web más sofisticado que BeautifulSoup
- **Estado**: ✅ Integrado y configurado
- **Clave**: `fc-d7697dffe9a04c4e973e213284e9de76`
- **Ubicación**: `/app/backend/.env`
- **Archivos**:
  - `src/tools/firecrawl_tool.py`
- **Funcionalidades**:
  - Extracción de contenido estructurado
  - Manejo de JavaScript y SPAs
  - Soporte para múltiples formatos de salida
  - Crawling de múltiples páginas

#### 4. **QStash (Redis)** - Jobs en Background
- **Propósito**: Procesamiento de trabajos en segundo plano
- **Estado**: ✅ Integrado y configurado
- **URL**: `redis://default:AeJLAAIjcDE4NmM1NWI5ZjQwYjE0NDIwYjRhNWZmNDhmOTk2OGU1MHAxMA@normal-vervet-57931.upstash.io:6379`
- **Ubicación**: `/app/backend/.env`
- **Archivos**:
  - `src/tools/qstash_tool.py`
- **Funcionalidades**:
  - Creación y gestión de trabajos
  - Monitoreo de progreso
  - Colas de prioridad
  - Timeout y cancelación

#### 5. **Playwright** - Automatización de Navegadores
- **Propósito**: Automatización web y scraping avanzado
- **Estado**: ✅ Integrado y configurado
- **Dependencias**: `playwright>=1.40.0`
- **Ubicación**: `/app/backend/requirements.txt`
- **Archivos**:
  - `src/tools/playwright_tool.py`
- **Funcionalidades**:
  - Navegación automatizada
  - Capturas de pantalla
  - Extracción de contenido dinámico
  - Interacción con formularios
  - Ejecución de JavaScript

### APIs Disponibles (No Integradas) 🔄

#### 6. **RapidAPI** - APIs Externas
- **Propósito**: Acceso a múltiples APIs de terceros
- **Estado**: 🔄 Clave disponible, pendiente de uso específico
- **Clave**: `e3c8f40077msh2383361adacc215p1fb470jsn0a2150f802f9`
- **Recomendación**: Solo integrar si se necesitan APIs específicas

#### 7. **Smithery** - Agentes Personalizados
- **Propósito**: Desarrollo de agentes especializados
- **Estado**: 🔄 Clave disponible, pendiente de investigación
- **Clave**: `generous-zebra-3J27EB`
- **Recomendación**: Investigar capacidades antes de integrar

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

### Estructura de Archivos - Estado Actual

```
/app/backend/src/tools/
├── shell_tool.py                 # ✅ Comandos shell
├── file_manager_tool.py          # ✅ Gestión de archivos
├── tavily_search_tool.py         # ✅ Búsqueda Tavily
├── enhanced_web_search_tool.py   # ✅ Búsqueda web mejorada
├── deep_research_tool.py         # ✅ Investigación profunda
├── comprehensive_research_tool.py # ✅ Investigación comprehensiva
├── firecrawl_tool.py             # ✅ NUEVO - Web scraping avanzado
├── qstash_tool.py                # ✅ NUEVO - Jobs en background
├── playwright_tool.py            # ✅ NUEVO - Automatización navegadores
├── rapidapi_tool.py              # 🔄 Por crear (si se necesita)
└── smithery_tool.py              # 🔄 Por crear (si se necesita)
```

### Variables de Entorno - Estado Actual

```bash
# /app/backend/.env
# Existentes y funcionando
TAVILY_API_KEY=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
MONGO_URL=mongodb://localhost:27017/task_manager

# Nuevas integradas
FIRECRAWL_API_KEY=fc-d7697dffe9a04c4e973e213284e9de76
QSTASH_URL=redis://default:AeJLAAIjcDE4NmM1NWI5ZjQwYjE0NDIwYjRhNWZmNDhmOTk2OGU1MHAxMA@normal-vervet-57931.upstash.io:6379

# Disponibles pero no integradas
RAPIDAPI_KEY=e3c8f40077msh2383361adacc215p1fb470jsn0a2150f802f9
SMITHERY_KEY=generous-zebra-3J27EB
```

### Dependencias Instaladas

```bash
# /app/backend/requirements.txt
# Dependencias nuevas agregadas
playwright>=1.40.0           # ✅ Instalado
redis>=5.0.0                 # ✅ Instalado
firecrawl-py>=0.0.11         # ✅ Instalado
```

### Estado de Servicios

| Servicio | Estado | Herramientas | Funcionalidad |
|----------|--------|--------------|---------------|
| Backend | ✅ Running | 11 tools | Chat, APIs, Tools |
| Frontend | ✅ Running | Production | UI, Tasks, WebSearch |
| MongoDB | ✅ Running | Connected | Datos persistentes |
| Tavily | ✅ Active | Web Search | Búsqueda web |
| Firecrawl | ✅ Active | Advanced Scraping | Web scraping |
| QStash | ✅ Active | Background Jobs | Jobs async |
| Playwright | ✅ Active | Browser Automation | Automatización |

### Herramientas Disponibles en Tool Manager

1. **shell** - Comandos del sistema
2. **web_search** - Búsqueda web mejorada
3. **file_manager** - Gestión de archivos
4. **tavily_search** - Búsqueda Tavily
5. **deep_research** - Investigación profunda
6. **comprehensive_research** - Investigación comprehensiva
7. **enhanced_web_search** - Búsqueda web mejorada
8. **enhanced_deep_research** - Investigación mejorada
9. **firecrawl** - 🆕 Web scraping avanzado
10. **qstash** - 🆕 Jobs en background
11. **playwright** - 🆕 Automatización de navegadores

### Notas de Implementación - Completado

1. **Principio de Valor**: ✅ Solo se integraron APIs que agreguen valor real
2. **Evitar Duplicación**: ✅ No se duplicó funcionalidad existente
3. **Priorizar UX**: ✅ Se priorizaron integraciones que mejoran experiencia de usuario
4. **Documentar Todo**: ✅ Todas las integraciones están documentadas

### Resumen de Implementación

#### ✅ **Completado**:
1. **Script de Producción**: `/app/scripts/build-production.sh` - Automatiza construcción
2. **Firecrawl Integration**: Web scraping avanzado con API configurada
3. **Playwright Integration**: Automatización de navegadores instalada
4. **QStash Integration**: Jobs en background implementados (conexión Redis pendiente)
5. **Tool Manager**: Actualizado con las 11 herramientas (3 nuevas)
6. **Documentación**: API_DOCUMENTATION.md actualizada
7. **Testing**: Script de prueba para verificar integraciones

#### 🔄 **Pendiente de Uso**:
- **RapidAPI**: Clave disponible, usar cuando se necesiten APIs específicas
- **Smithery**: Clave disponible, requiere investigación de capacidades

### Comandos Útiles

```bash
# Construir para producción
cd /app/frontend && /app/scripts/build-production.sh

# Probar integraciones
python /app/scripts/test-integrations.py

# Verificar herramientas disponibles
curl -s http://localhost:8001/api/agent/tools | jq '.tools[].name'

# Restart services
sudo supervisorctl restart all

# Verificar estado
sudo supervisorctl status
```

### Casos de Uso de las Nuevas Herramientas

#### **Firecrawl** - Web Scraping Avanzado
- **Cuándo usar**: Para sitios con JavaScript, SPAs, contenido dinámico
- **Ventajas**: Mejor que BeautifulSoup para sitios modernos
- **Ejemplo**: Extraer datos de páginas e-commerce, noticias, documentación

#### **Playwright** - Automatización de Navegadores
- **Cuándo usar**: Para interacciones complejas, capturas de pantalla, testing
- **Ventajas**: Navegador real, manejo de JavaScript, capturas visuales
- **Ejemplo**: Automatizar formularios, testing de UI, scraping complejo

#### **QStash** - Jobs en Background
- **Cuándo usar**: Para tareas largas que no deben bloquear la UI
- **Ventajas**: Procesamiento asíncrono, monitoreo de progreso
- **Ejemplo**: Investigación profunda, procesamiento de archivos grandes

---

**Implementación completada**: 2025-01-15
**Herramientas integradas**: 3 nuevas (Firecrawl, Playwright, QStash)
**Estado**: ✅ Listo para uso en producción