# 📋 MITOSIS AGENT - COMPREHENSIVE CODE ANALYSIS PLAN

## 1. RESUMEN EJECUTIVO

### Descripción de la Aplicación
Mitosis es una aplicación de agente general inteligente que combina un backend FastAPI con un frontend React para proporcionar un sistema completo de automatización de tareas. La aplicación permite a los usuarios crear tareas, generar planes de acción automáticos, y ejecutar herramientas de forma autónoma con retroalimentación en tiempo real.

### Stack Tecnológico Detallado
- **Backend**: FastAPI (Python 3.9+) con MongoDB como base de datos
- **Frontend**: React 18 con TypeScript, Vite como bundler
- **Comunicación en Tiempo Real**: HTTP Polling (WebSocket reemplazado por problemas de "server error")
- **Integración IA**: Ollama para modelos LLM locales (llama3.1, qwen2.5, gemma2)
- **Herramientas**: Sistema extensible de 15+ herramientas especializadas
- **Persistencia**: MongoDB para tareas y archivos
- **Monitoreo**: Sistema de logs y métricas detallado
- **Automatización Web**: Playwright para navegación y scraping
- **Búsqueda Web**: Tavily, Bing Search, Firecrawl para investigación
- **Memoria Avanzada**: Sistema de memoria episódica, semántica y procedimental

### Estado Actual - Análisis Post-Refactorización
La aplicación ha pasado por múltiples refactorizaciones exitosas, reduciendo significativamente la duplicación de código (de 120+ archivos a ~30 archivos esenciales) y mejorando la estabilidad. El sistema está funcionalmente completo con capacidades autónomas verificadas, pero presenta problemas críticos de arquitectura que requieren atención inmediata.

## 2. ARQUITECTURA Y FLUJO DE DATOS - ANÁLISIS COMPLETO

### Arquitectura General - Estructura Detallada

#### Backend (FastAPI) - Estructura Completa
```
/app/backend/
├── server.py                    # Servidor principal WSGI
├── src/
│   ├── routes/                  # Rutas de la API (2 archivos)
│   │   ├── agent_routes.py      # 30+ endpoints principales
│   │   └── memory_routes.py     # Rutas de memoria avanzada
│   ├── services/                # Servicios de negocio (4 archivos)
│   │   ├── ollama_service.py    # Integración con Ollama LLM
│   │   ├── task_manager.py      # Gestión de tareas y persistencia
│   │   ├── database.py          # Servicios de MongoDB
│   │   └── automatic_execution_orchestrator.py # Orquestación
│   ├── core/                    # Lógica central (1 archivo)
│   │   └── agent_unified.py     # Agente unificado (1,200+ líneas)
│   ├── tools/                   # Herramientas especializadas (20+ archivos)
│   │   ├── tool_manager.py      # Gestor central de herramientas
│   │   ├── web_search_tool.py   # Búsqueda web con Playwright
│   │   ├── file_manager_tool.py # Gestión de archivos completa
│   │   ├── tavily_search_tool.py # Búsqueda con Tavily API
│   │   ├── deep_research_tool.py # Investigación profunda
│   │   ├── comprehensive_research_tool.py # Investigación multi-fuente
│   │   ├── firecrawl_tool.py    # Web scraping avanzado
│   │   ├── playwright_tool.py   # Automatización de navegadores
│   │   ├── shell_tool.py        # Comandos de terminal
│   │   ├── task_planner.py      # Planificación inteligente
│   │   ├── execution_engine.py  # Motor de ejecución (1,000+ líneas)
│   │   └── [15+ herramientas más]
│   ├── websocket/               # Comunicación en tiempo real (DESHABILITADO)
│   │   └── websocket_manager.py # Manager WebSocket (NO USADO)
│   ├── memory/                  # Sistema de memoria avanzado (8 archivos)
│   │   ├── advanced_memory_manager.py # Gestor principal (1,400+ líneas)
│   │   ├── working_memory_store.py # Memoria de trabajo
│   │   ├── episodic_memory_store.py # Memoria episódica
│   │   ├── semantic_memory_store.py # Memoria semántica
│   │   ├── procedural_memory_store.py # Memoria procedimental
│   │   ├── embedding_service.py # Embeddings para búsqueda
│   │   └── semantic_indexer.py  # Indexación semántica
│   ├── orchestration/           # Orquestación de tareas (8 archivos)
│   │   ├── task_orchestrator.py # Orquestador principal
│   │   ├── planning_algorithms.py # Algoritmos de planificación
│   │   ├── hierarchical_planning_engine.py # Planificación jerárquica
│   │   ├── adaptive_execution_engine.py # Ejecución adaptativa
│   │   ├── resource_manager.py  # Gestión de recursos
│   │   └── dependency_resolver.py # Resolución de dependencias
│   ├── context/                 # Gestión de contexto (6 archivos)
│   │   ├── intelligent_context_manager.py # Gestor inteligente
│   │   └── strategies/          # Estrategias de contexto
│   ├── validation/              # Validación de resultados (1 archivo)
│   │   └── result_validators.py # Validadores de pasos
│   ├── analysis/                # Análisis de errores (1 archivo)
│   │   └── error_analyzer.py    # Análisis de errores
│   ├── agents/                  # Agentes especializados (2 archivos)
│   │   ├── self_reflection_engine.py # Auto-reflexión
│   │   └── replanning_engine.py # Re-planificación
│   ├── planning/                # Planificación dinámica (1 archivo)
│   │   └── dynamic_task_planner.py # Planificador dinámico
│   └── utils/                   # Utilidades (3 archivos)
│       ├── json_encoder.py      # Codificador JSON
│       └── json_encoder_fixed.py # Codificador JSON corregido
├── static/generated_files/      # Archivos generados dinámicamente
└── [15+ archivos de configuración y testing]
```

#### Frontend (React) - Estructura Completa
```
/app/frontend/src/
├── App.tsx                      # Componente principal (500+ líneas)
├── index.tsx                    # Punto de entrada
├── components/                  # Componentes UI (55+ archivos)
│   ├── TaskView.tsx            # Vista de tareas principal (800+ líneas)
│   ├── Sidebar.tsx             # Barra lateral (400+ líneas)
│   ├── ChatInterface/          # Interfaz de chat
│   │   ├── ChatInterface.tsx   # Componente principal (1,150+ líneas)
│   │   └── index.tsx           # Exportación
│   ├── TerminalView/           # Vista de terminal
│   │   ├── TerminalView.tsx    # Terminal principal (600+ líneas)
│   │   └── index.tsx           # Exportación
│   ├── VanishInput.tsx         # Input animado personalizado
│   ├── ThinkingAnimation.tsx   # Animación de pensamiento
│   ├── TaskCompletedUI.tsx     # UI de tarea completada
│   ├── AgentStatusBar.tsx      # Barra de estado del agente
│   ├── ConfigPanel.tsx         # Panel de configuración
│   ├── MemoryManager.tsx       # Gestor de memoria
│   ├── MemoryTab.tsx           # Tab de memoria
│   ├── ToolExecutionDetails.tsx # Detalles de ejecución
│   ├── SearchResults.tsx       # Resultados de búsqueda
│   ├── FileAttachment.tsx      # Archivos adjuntos
│   ├── FileUploadModal.tsx     # Modal de subida de archivos
│   ├── DeepResearchReport.tsx  # Reportes de investigación
│   ├── ExecutionEngine/        # Motor de ejecución
│   │   ├── TaskAnalysisPanel.tsx # Panel de análisis
│   │   └── ExecutionControlPanel.tsx # Control de ejecución
│   ├── ContextManager/         # Gestión de contexto
│   │   ├── ContextVariablesPanel.tsx # Variables de contexto
│   │   └── ContextCheckpointsPanel.tsx # Checkpoints
│   ├── ui/                     # Componentes UI base
│   │   ├── CustomSelect.tsx    # Select personalizado
│   │   ├── NumberInput.tsx     # Input numérico
│   │   ├── ConnectionStatus.tsx # Estado de conexión
│   │   ├── link-preview.tsx    # Preview de enlaces
│   │   ├── hover-border-gradient.tsx # Gradiente hover
│   │   └── moving-border.tsx   # Borde animado
│   └── [40+ componentes más]
├── services/                   # Servicios del frontend (1 archivo)
│   └── api.ts                  # Cliente de API (870+ líneas)
├── hooks/                      # Hooks personalizados (5 archivos)
│   ├── useWebSocket.ts         # Hook WebSocket (150+ líneas)
│   ├── useMemoryManager.ts     # Hook de memoria (225+ líneas)
│   ├── useThinkingTimer.ts     # Hook de timer de pensamiento
│   ├── useOllamaConnection.ts  # Hook de conexión Ollama
│   └── useConsoleReportFormatter.ts # Hook de formato de consola
├── utils/                      # Utilidades (4 archivos)
│   ├── pdfGenerator.ts         # Generador de PDF
│   ├── academicReportUtils.ts  # Utilidades de reportes
│   └── markdownConsoleFormatter.ts # Formateador Markdown
├── lib/                        # Librerías (1 archivo)
│   └── utils.ts                # Utilidades generales
└── types.ts                    # Tipos TypeScript (50+ interfaces)
```

### Flujo de Datos Principal - Análisis Detallado

#### 1. **Creación de Tarea** (Flujo Completo)
```
Usuario → VanishInput → ChatInterface.tsx → TaskView.tsx → 
Backend /api/agent/generate-plan → Ollama LLM → Plan estructurado → 
MongoDB persistencia → Frontend actualización
```

#### 2. **Generación de Plan** (Proceso Inteligente)
```
Backend → TaskPlanner.analyze_task() → Ollama prompt específico → 
JSON Schema validation → Plan steps creation → 
MongoDB storage → Frontend plan display
```

#### 3. **Ejecución Autónoma** (Sistema Complejo)
```
Backend → TaskOrchestrator → ExecutionEngine → ToolManager → 
Herramientas específicas → HTTP Polling updates → 
TerminalView updates → Progress tracking
```

#### 4. **Retroalimentación** (Comunicación Bidireccional)
```
Terminal/Chat → HTTP Polling (NO WebSocket) → 
Frontend useWebSocket hook → TaskView updates → 
Real-time progress display
```

### Gestión del Estado - Análisis Profundo

#### Frontend State Management (Problemas Identificados)
- **React State**: Manejo local disperso en 55+ componentes
- **Custom Hooks**: `useWebSocket` (simulado), `useMemoryManager` (localStorage)
- **No Context API**: Ausencia de estado global centralizado
- **Props Drilling**: Comunicación excesiva entre componentes (6+ niveles)
- **State Inconsistencies**: Estados duplicados entre TaskView y ChatInterface

#### Backend State Management (Arquitectura Compleja)
- **MongoDB**: Persistencia principal con 5+ colecciones
- **Memory Cache**: Caché en memoria no persistente
- **Task Manager**: Gestión centralizada con active_cache
- **HTTP Polling**: Reemplazo de WebSocket para estado en tiempo real
- **Context Manager**: Gestión de contexto de ejecución
- **Orchestration State**: Estado de orquestación distribuido

### Problemas Críticos de Arquitectura Identificados

#### 1. **Comunicación en Tiempo Real Deteriorada**
- WebSocket reemplazado por HTTP Polling debido a "server error"
- useWebSocket hook simula conexión WebSocket pero usa HTTP
- Latencia aumentada y uso excesivo de recursos

#### 2. **Inconsistencia en URLs y Configuración**
- Múltiples formas de obtener backend URL
- Hardcoded URLs en varios lugares
- Configuración de entorno fragmentada

#### 3. **Gestión de Estado Fragmentada**
- Estado duplicado entre componentes
- Falta de single source of truth
- Props drilling excesivo

#### 4. **Complejidad de Herramientas**
- 20+ herramientas con APIs inconsistentes
- Falta de abstracción común
- Manejo de errores heterogéneo

## 3. AUDITORÍA DE CÓDIGO DETALLADA - ANÁLISIS EXHAUSTIVO

### A. Inconsistencias y Malas Prácticas Críticas

#### A1. **Comunicación en Tiempo Real Deteriorada**
**Problema Crítico**: WebSocket reemplazado por HTTP Polling
```typescript
// useWebSocket.ts - Hook que simula WebSocket pero usa HTTP
export const useWebSocket = (): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  // ... pero realmente hace HTTP polling cada 2 segundos
  pollingIntervalRef.current = setInterval(async () => {
    const response = await fetch(`${backendUrl}/api/agent/get-task-status/${taskId}`);
  }, 2000);
};
```

**Problema**: Latencia aumentada, uso excesivo de recursos, UX deteriorada
**Ubicación**: `/app/frontend/src/hooks/useWebSocket.ts`

#### A2. **Gestión de URLs Fragmentada y Inconsistente**
**Problema**: Múltiples formas de obtener la URL del backend
```typescript
// En api.ts
const API_BASE_URL = `${getBackendUrl()}/api/agent`;
const getBackendUrl = () => {
  return import.meta.env.VITE_BACKEND_URL || 
         import.meta.env.REACT_APP_BACKEND_URL || 
         process.env.REACT_APP_BACKEND_URL;
};

// En ChatInterface.tsx
const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                  import.meta.env.REACT_APP_BACKEND_URL || 
                  process.env.REACT_APP_BACKEND_URL ||
                  'http://localhost:8001';

// En useWebSocket.ts
const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                  import.meta.env.REACT_APP_BACKEND_URL || 
                  process.env.REACT_APP_BACKEND_URL ||
                  'http://localhost:8001';
```

**Problema**: Duplicación de lógica, inconsistencia en fallbacks, hardcoded URLs
**Ubicación**: 8+ archivos diferentes

#### A3. **Gestión de Estado Fragmentada**
**Problema**: Estado duplicado entre TaskView y ChatInterface
```typescript
// TaskView.tsx
const [messages, setMessages] = useState<Message[]>([]);
const [plan, setPlan] = useState<any>(null);
const [isExecuting, setIsExecuting] = useState(false);

// ChatInterface.tsx
const [messages, setMessages] = useState<Message[]>([]);
const [isLoading, setIsLoading] = useState(false);
const [showQuickActions, setShowQuickActions] = useState(false);
```

**Problema**: Sincronización compleja, bugs de estado, props drilling excesivo
**Ubicación**: `/app/frontend/src/components/TaskView.tsx`, `/app/frontend/src/components/ChatInterface/ChatInterface.tsx`

#### A4. **Validación de Datos Inconsistente**
**Problema**: Validación implementada de forma diferente en cada herramienta
```python
# En web_search_tool.py
def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(parameters, dict):
        return {'valid': False, 'error': 'Parameters must be a dictionary'}
    if 'query' not in parameters:
        return {'valid': False, 'error': 'query parameter is required'}

# En file_manager_tool.py
def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(parameters, dict):
        return {'valid': False, 'error': 'Parameters must be a dictionary'}
    if 'action' not in parameters:
        return {'valid': False, 'error': 'action parameter is required'}
```

**Problema**: Código duplicado, inconsistencia en mensajes de error, falta de abstracción
**Ubicación**: 15+ archivos de herramientas

### B. Duplicación de Código (Oportunidades DRY) - Análisis Detallado

#### B1. **Lógica de Configuración de Backend URL**
**Duplicación**: Aparece en 8+ archivos
```typescript
// Patrón duplicado en múltiples archivos
const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                  import.meta.env.REACT_APP_BACKEND_URL || 
                  process.env.REACT_APP_BACKEND_URL ||
                  'http://localhost:8001';
```

**Oportunidad**: Crear función utilitaria centralizada
**Archivos Afectados**: 
- `/app/frontend/src/services/api.ts`
- `/app/frontend/src/hooks/useWebSocket.ts`
- `/app/frontend/src/components/ChatInterface/ChatInterface.tsx`
- `/app/frontend/src/components/TaskView.tsx`
- [4+ archivos más]

#### B2. **Validación de Parámetros en Herramientas**
**Duplicación**: Lógica similar en 15+ herramientas
```python
# Patrón repetido en todas las herramientas
def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(parameters, dict):
        return {'valid': False, 'error': 'Parameters must be a dictionary'}
    # ... validaciones específicas
```

**Oportunidad**: Clase base abstracta para herramientas
**Archivos Afectados**: Todas las herramientas en `/app/backend/src/tools/`

#### B3. **Formateo de Fechas y Timestamps**
**Duplicación**: Múltiples formas de formatear timestamps
```typescript
// Patrón 1
timestamp: new Date().toISOString()

// Patrón 2
timestamp: new Date().toLocaleString()

// Patrón 3
timestamp: datetime.now().isoformat()  // Python
```

**Oportunidad**: Utilidades de fecha centralizadas
**Archivos Afectados**: 20+ archivos en frontend y backend

#### B4. **Manejo de Errores en Componentes React**
**Duplicación**: Try-catch patterns similares
```typescript
// Patrón repetido en múltiples componentes
try {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  const data = await response.json();
  // ... procesamiento
} catch (error) {
  console.error('Error:', error);
  // ... manejo de error
}
```

**Oportunidad**: Hook personalizado para API calls
**Archivos Afectados**: 10+ componentes React

### C. Posibles Errores y Code Smells - Análisis Profundo

#### C1. **Race Conditions Críticas**
**Problema**: Updates concurrentes de estado en TaskView
```typescript
// TaskView.tsx - Potencial race condition
const handleSendMessage = async (message: string) => {
  setIsExecuting(true);
  // ... operación asíncrona
  setMessages(prev => [...prev, newMessage]);
  setIsExecuting(false);
};

// Si se llama rápidamente, puede causar estado inconsistente
```

**Ubicación**: `/app/frontend/src/components/TaskView.tsx:350-400`
**Impacto**: Estado inconsistente, mensajes perdidos, bugs de UI

#### C2. **Memory Leaks en HTTP Polling**
**Problema**: Event listeners y timers no limpiados
```typescript
// useWebSocket.ts - Potential memory leak
useEffect(() => {
  pollingIntervalRef.current = setInterval(async () => {
    // ... polling logic
  }, 2000);
  
  // Cleanup solo en unmount, no en cambios de dependencias
  return () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
  };
}, []); // Dependencies array vacío - problema
```

**Ubicación**: `/app/frontend/src/hooks/useWebSocket.ts:42-118`
**Impacto**: Memory leaks, degradación de performance

#### C3. **Hardcoded Values y Magic Numbers**
**Problema**: Valores mágicos dispersos por el código
```python
# backend/src/tools/playwright_tool.py
'timeout': 30000,  # 30 segundos
'viewport': {'width': 1920, 'height': 1080},

# backend/src/orchestration/task_orchestrator.py
ping_timeout=60,
ping_interval=25,
max_file_size=100 * 1024 * 1024  # 100MB
```

**Ubicación**: 25+ archivos
**Impacto**: Mantenimiento difícil, configuración inflexible

#### C4. **Inconsistent Error Boundaries**
**Problema**: Falta de error boundaries en React
```typescript
// App.tsx - Sin error boundary
<div className="flex h-screen bg-gradient-to-br from-gray-900 to-gray-800">
  <Sidebar />
  <div className="flex-1 flex flex-col">
    <TaskView /> {/* Puede fallar sin captura */}
  </div>
</div>
```

**Ubicación**: Componentes principales
**Impacto**: Crashes no controlados, mala UX

#### C5. **Async/Await Inconsistencias**
**Problema**: Mezcla de patrones async
```python
# agent_unified.py - Inconsistent async patterns
async def _execute_task_async(self, task_id: str):
    # Código async
    await self._execute_step_async(step, task)
    # Pero también llamadas síncronas
    self._update_task_progress(task)  # Debería ser await
```

**Ubicación**: `/app/backend/src/core/agent_unified.py`
**Impacto**: Bloqueo del event loop, performance degradada

### D. Manejo de Asincronía y Efectos Secundarios - Análisis Específico

#### D1. **Promises Sin Manejo de Errores**
**Problema**: Unhandled promise rejections
```typescript
// ChatInterface.tsx - Promises sin catch
const handleSendMessage = async (message: string) => {
  onSendMessage(message); // No await, no catch
  
  // Más adelante...
  createTaskWithMessage(message.trim()); // Unhandled promise
};
```

**Ubicación**: `/app/frontend/src/components/ChatInterface/ChatInterface.tsx:158-206`
**Impacto**: Errores silenciosos, debugging difícil

#### D2. **useEffect Dependencies Incorrectas**
**Problema**: Dependencias que causan loops infinitos
```typescript
// TaskView.tsx - Dependencia problemática
useEffect(() => {
  tasks.forEach(task => {
    if (task.plan && task.plan.length > 0) {
      updateTaskProgress(task.id);
    }
  });
}, [tasks.map(t => t.plan?.map(step => step.completed).join(',') || '').join('|')]);
```

**Ubicación**: `/app/frontend/src/components/TaskView.tsx:120-135`
**Impacto**: Re-renders excesivos, performance degradada

#### D3. **Concurrent Operations Sin Sincronización**
**Problema**: Operaciones concurrentes en backend
```python
# task_manager.py - Concurrent access without locks
def execute_task(self, task_id: str):
    task = self.get_task(task_id)  # Read
    task.status = 'executing'      # Write
    self.save_task(task)           # Save
    # Si otra operación modifica task entre read y save, se pierde
```

**Ubicación**: `/app/backend/src/services/task_manager.py`
**Impacto**: Condiciones de carrera, datos inconsistentes

#### D4. **Event Listeners Acumulativos**
**Problema**: Event listeners no removidos correctamente
```typescript
// useWebSocket.ts - Listeners acumulativos
const addEventListeners = (events: Partial<HttpPollingEvents>) => {
  eventListenersRef.current = events; // Sobrescribe, no limpia anteriores
};
```

**Ubicación**: `/app/frontend/src/hooks/useWebSocket.ts:132-140`
**Impacto**: Memory leaks, comportamiento impredecible

### E. Problemas de Performance Identificados

#### E1. **Excessive Re-renders**
**Problema**: Components re-rendering innecesariamente
```typescript
// TaskView.tsx - Re-renders excesivos
const TaskView = ({ task }: TaskViewProps) => {
  // Sin React.memo, re-renderiza con cada cambio del padre
  
  const [messages, setMessages] = useState<Message[]>([]);
  // Estado que cambia frecuentemente dispara re-renders
};
```

**Impacto**: Performance degradada, UI lenta

#### E2. **Large Bundle Size**
**Problema**: Bundle size grande por imports innecesarios
```typescript
// Imports completos en lugar de específicos
import * as React from 'react';
import { agentAPI } from '../../services/api'; // Import completo
```

**Impacto**: Carga inicial lenta, más ancho de banda

#### E3. **Memory Usage Excesivo**
**Problema**: Objetos grandes en memoria
```python
# advanced_memory_manager.py - Objetos grandes en memoria
self.episodic_memory.episodes = {}  # Puede crecer indefinidamente
self.semantic_memory.concepts = {}   # Sin límite de tamaño
```

**Impacto**: Uso de memoria creciente, degradación de performance

### F. Problemas de Seguridad Identificados

#### F1. **Exposure de Información Sensible**
**Problema**: API keys y configuración expuesta
```typescript
// Configuración expuesta en frontend
const API_BASE_URL = `${getBackendUrl()}/api/agent`;
// Backend URL expuesta en bundle
```

**Impacto**: Información sensible visible al cliente

#### F2. **Falta de Validación de Input**
**Problema**: Inputs no validados en frontend
```typescript
// VanishInput.tsx - Input sin validación
const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault();
  if (value.trim()) {
    onSubmit(value.trim()); // No hay validación adicional
  }
};
```

**Impacto**: Posibles ataques de injection, datos corruptos

#### F3. **CORS Configuration Insegura**
**Problema**: Configuración CORS permisiva
```python
# server.py - CORS muy permisivo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Muy permisivo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Impacto**: Vulnerabilidades de seguridad, ataques CSRF

## 4. PLAN DE REFACTORIZACIÓN PROPUESTO - ESTRATEGIA COMPREHENSIVA

### ESTRATEGIA GENERAL: REFACTORIZACIÓN INCREMENTAL CON IMPACTO MÍNIMO

La refactorización se realizará en 6 fases principales, cada una con objetivos específicos y métricas de éxito claras. El enfoque será incremental para mantener la funcionalidad existente mientras se mejora la arquitectura.

### FASE 1: ESTABILIZACIÓN DE COMUNICACIÓN (Semanas 1-2)

#### Objetivo Principal: Restablecer WebSocket y eliminar HTTP Polling

#### 1.1 Restaurar WebSocket Functionality
**Problema**: HTTP Polling reemplazó WebSocket por "server error"
```typescript
// Actual: useWebSocket.ts simula conexión pero usa HTTP
const useWebSocket = (): UseWebSocketReturn => {
  // HTTP polling cada 2 segundos
  setInterval(async () => {
    const response = await fetch(`${backendUrl}/api/agent/get-task-status/${taskId}`);
  }, 2000);
};

// Objetivo: Verdadera conexión WebSocket
const useWebSocket = (): UseWebSocketReturn => {
  const [socket, setSocket] = useState<Socket | null>(null);
  
  useEffect(() => {
    const newSocket = io(backendUrl, {
      transports: ['websocket'],
      upgrade: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });
    
    setSocket(newSocket);
    return () => newSocket.close();
  }, [backendUrl]);
};
```

**Tareas Específicas**:
- [ ] Diagnosticar y corregir "server error" en WebSocket
- [ ] Reimplementar useWebSocket con Socket.IO real
- [ ] Crear fallback mechanism a HTTP polling
- [ ] Implementar reconnection logic robusto
- [ ] Testing exhaustivo de comunicación en tiempo real

#### 1.2 Unificar Configuración de URLs
**Problema**: URLs duplicadas en 8+ archivos
```typescript
// Crear: src/config/api.ts
export const API_CONFIG = {
  getBackendUrl: () => {
    const url = import.meta.env.VITE_BACKEND_URL || 
                import.meta.env.REACT_APP_BACKEND_URL || 
                process.env.REACT_APP_BACKEND_URL || 
                'http://localhost:8001';
    return url;
  },
  
  getWebSocketUrl: () => {
    const baseUrl = API_CONFIG.getBackendUrl();
    return baseUrl.replace('http', 'ws');
  },
  
  API_ENDPOINTS: {
    CHAT: '/api/agent/chat',
    GENERATE_PLAN: '/api/agent/generate-plan',
    EXECUTE_STEP: '/api/agent/execute-step-detailed',
    TASK_STATUS: '/api/agent/get-task-status'
  }
};
```

**Tareas Específicas**:
- [ ] Crear configuración centralizada de API
- [ ] Refactorizar todos los archivos para usar configuración central
- [ ] Implementar validación de configuración
- [ ] Crear environment-specific configs

#### 1.3 Implementar Error Boundaries
**Problema**: Falta de error boundaries en React
```typescript
// Crear: src/components/ErrorBoundary.tsx
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });
    
    // Log error to monitoring service
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong.</h2>
          <details>
            <summary>Error details</summary>
            <pre>{this.state.error?.message}</pre>
            <pre>{this.state.errorInfo?.componentStack}</pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Tareas Específicas**:
- [ ] Crear ErrorBoundary component
- [ ] Implementar en componentes críticos
- [ ] Agregar logging de errores
- [ ] Crear UI de error user-friendly

### FASE 2: CONSOLIDACIÓN DE ESTADO (Semanas 3-4)

#### Objetivo Principal: Crear Single Source of Truth para Estado

#### 2.1 Implementar Context API Global
**Problema**: Estado duplicado entre TaskView y ChatInterface
```typescript
// Crear: src/context/AppContext.tsx
interface AppState {
  tasks: Task[];
  activeTaskId: string | null;
  messages: Message[];
  isExecuting: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
  agentConfig: AgentConfig;
}

interface AppActions {
  createTask: (message: string) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  addMessage: (message: Message) => void;
  setExecutionStatus: (status: boolean) => void;
  updateConfig: (config: Partial<AgentConfig>) => void;
}

const AppContext = createContext<{
  state: AppState;
  actions: AppActions;
} | null>(null);

export const AppProvider: React.FC<React.PropsWithChildren<{}>> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  const actions = useMemo<AppActions>(() => ({
    createTask: (message: string) => dispatch({ type: 'CREATE_TASK', payload: message }),
    updateTask: (taskId: string, updates: Partial<Task>) => 
      dispatch({ type: 'UPDATE_TASK', payload: { taskId, updates } }),
    addMessage: (message: Message) => dispatch({ type: 'ADD_MESSAGE', payload: message }),
    setExecutionStatus: (status: boolean) => 
      dispatch({ type: 'SET_EXECUTION_STATUS', payload: status }),
    updateConfig: (config: Partial<AgentConfig>) => 
      dispatch({ type: 'UPDATE_CONFIG', payload: config })
  }), []);
  
  return (
    <AppContext.Provider value={{ state, actions }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};
```

**Tareas Específicas**:
- [ ] Crear AppContext con useReducer
- [ ] Definir actions y reducers
- [ ] Migrar estado de TaskView a Context
- [ ] Migrar estado de ChatInterface a Context
- [ ] Eliminar props drilling

#### 2.2 Crear Custom Hooks Especializados
**Problema**: Lógica compleja dispersa en componentes
```typescript
// Crear: src/hooks/useTaskManagement.ts
export const useTaskManagement = () => {
  const { state, actions } = useAppContext();
  
  const createTaskWithMessage = useCallback(async (message: string) => {
    actions.setExecutionStatus(true);
    
    try {
      const response = await agentAPI.generatePlan(message);
      const newTask = {
        id: generateId(),
        message,
        plan: response.plan,
        status: 'ready',
        createdAt: new Date().toISOString()
      };
      
      actions.createTask(newTask);
      return newTask;
    } catch (error) {
      console.error('Error creating task:', error);
      throw error;
    } finally {
      actions.setExecutionStatus(false);
    }
  }, [actions]);
  
  const executeTaskStep = useCallback(async (taskId: string, stepId: string) => {
    try {
      const response = await agentAPI.executeStep(taskId, stepId);
      actions.updateTask(taskId, { 
        plan: response.updatedPlan,
        status: response.taskStatus
      });
      return response;
    } catch (error) {
      console.error('Error executing step:', error);
      throw error;
    }
  }, [actions]);
  
  return {
    tasks: state.tasks,
    activeTask: state.tasks.find(t => t.id === state.activeTaskId),
    isExecuting: state.isExecuting,
    createTaskWithMessage,
    executeTaskStep
  };
};
```

**Tareas Específicas**:
- [ ] Crear useTaskManagement hook
- [ ] Crear useMessageManagement hook
- [ ] Crear useAgentConfig hook
- [ ] Refactorizar componentes para usar hooks

#### 2.3 Implementar Estado Persistente
**Problema**: Estado se pierde en refresh
```typescript
// Crear: src/hooks/usePersistedState.ts
export const usePersistedState = <T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void] => {
  const [state, setState] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error loading ${key} from localStorage:`, error);
      return initialValue;
    }
  });

  const setPersistedState = useCallback((value: T | ((prev: T) => T)) => {
    setState(currentState => {
      const newState = typeof value === 'function' 
        ? (value as (prev: T) => T)(currentState)
        : value;
      
      try {
        window.localStorage.setItem(key, JSON.stringify(newState));
      } catch (error) {
        console.error(`Error saving ${key} to localStorage:`, error);
      }
      
      return newState;
    });
  }, [key]);

  return [state, setPersistedState];
};
```

**Tareas Específicas**:
- [ ] Crear usePersistedState hook
- [ ] Implementar persistencia de tareas
- [ ] Implementar persistencia de configuración
- [ ] Agregar migración de datos

### FASE 3: ABSTRACCIÓN DE HERRAMIENTAS (Semanas 5-6)

#### Objetivo Principal: Unificar API de Herramientas

#### 3.1 Crear Clase Base para Herramientas
**Problema**: Validación duplicada en 15+ herramientas
```python
# Crear: src/tools/base_tool.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

class BaseTool(ABC):
    """Clase base abstracta para todas las herramientas"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre único de la herramienta"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción de la herramienta"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[Dict[str, Any]]:
        """Obtener parámetros esperados"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validación base común a todas las herramientas"""
        if not isinstance(parameters, dict):
            return {'valid': False, 'error': 'Parameters must be a dictionary'}
        
        # Validar parámetros requeridos
        required_params = [p for p in self.get_parameters() if p.get('required', False)]
        for param in required_params:
            if param['name'] not in parameters:
                return {
                    'valid': False, 
                    'error': f"Required parameter '{param['name']}' is missing"
                }
        
        # Validar tipos de parámetros
        for param in self.get_parameters():
            param_name = param['name']
            if param_name in parameters:
                expected_type = param.get('type', 'string')
                if not self._validate_type(parameters[param_name], expected_type):
                    return {
                        'valid': False,
                        'error': f"Parameter '{param_name}' must be of type {expected_type}"
                    }
        
        return {'valid': True}
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validar tipo de parámetro"""
        type_validators = {
            'string': lambda x: isinstance(x, str),
            'integer': lambda x: isinstance(x, int),
            'boolean': lambda x: isinstance(x, bool),
            'array': lambda x: isinstance(x, list),
            'object': lambda x: isinstance(x, dict)
        }
        
        validator = type_validators.get(expected_type, lambda x: True)
        return validator(value)
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar la herramienta"""
        pass
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Obtener información completa de la herramienta"""
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.get_parameters(),
            'category': getattr(self, 'category', 'general'),
            'version': getattr(self, 'version', '1.0.0')
        }
```

**Tareas Específicas**:
- [ ] Crear BaseTool abstract class
- [ ] Migrar todas las herramientas a BaseTool
- [ ] Implementar validación común
- [ ] Crear factory pattern para herramientas

#### 3.2 Implementar Tool Registry
**Problema**: Gestión manual de herramientas
```python
# Crear: src/tools/tool_registry.py
class ToolRegistry:
    """Registry central para todas las herramientas"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool: BaseTool):
        """Registrar una herramienta"""
        self._tools[tool.name] = tool
        
        # Agregar a categoría
        category = getattr(tool, 'category', 'general')
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool.name)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Obtener herramienta por nombre"""
        return self._tools.get(name)
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Obtener herramientas por categoría"""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names]
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Obtener todas las herramientas"""
        return self._tools.copy()
    
    def execute_tool(self, name: str, parameters: Dict[str, Any], 
                    config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar herramienta por nombre"""
        tool = self.get_tool(name)
        if not tool:
            return {'error': f'Tool {name} not found', 'success': False}
        
        # Validar parámetros
        validation = tool.validate_parameters(parameters)
        if not validation['valid']:
            return {'error': validation['error'], 'success': False}
        
        # Ejecutar
        try:
            return tool.execute(parameters, config)
        except Exception as e:
            return {'error': str(e), 'success': False}

# Instancia global
tool_registry = ToolRegistry()
```

**Tareas Específicas**:
- [ ] Crear ToolRegistry
- [ ] Auto-registrar herramientas
- [ ] Implementar lazy loading
- [ ] Crear herramientas plugin system

### FASE 4: OPTIMIZACIÓN DE PERFORMANCE (Semanas 7-8)

#### Objetivo Principal: Mejorar Rendimiento y Reducir Bundle Size

#### 4.1 Implementar React.memo y useMemo
**Problema**: Re-renders excesivos
```typescript
// Optimizar: TaskView.tsx
const TaskView = React.memo(({ task, onUpdateTask }: TaskViewProps) => {
  const memoizedPlan = useMemo(() => {
    if (!task.plan) return null;
    
    return task.plan.map(step => ({
      ...step,
      formattedTime: formatEstimatedTime(step.estimated_time),
      isCompleted: step.status === 'completed',
      isActive: step.status === 'in-progress'
    }));
  }, [task.plan]);

  const memoizedMessages = useMemo(() => {
    return task.messages.map(msg => ({
      ...msg,
      formattedTime: formatMessageTime(msg.timestamp),
      isFromAgent: msg.sender === 'agent'
    }));
  }, [task.messages]);

  const handleUpdateTask = useCallback((updates: Partial<Task>) => {
    onUpdateTask(task.id, updates);
  }, [task.id, onUpdateTask]);

  return (
    <div className="task-view">
      <TaskHeader task={task} />
      <TaskPlan 
        plan={memoizedPlan} 
        onStepExecute={handleStepExecute}
      />
      <MessageList messages={memoizedMessages} />
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function
  return (
    prevProps.task.id === nextProps.task.id &&
    prevProps.task.status === nextProps.task.status &&
    prevProps.task.plan === nextProps.task.plan &&
    prevProps.task.messages === nextProps.task.messages
  );
});
```

**Tareas Específicas**:
- [ ] Implementar React.memo en componentes pesados
- [ ] Optimizar con useMemo y useCallback
- [ ] Crear custom comparison functions
- [ ] Implementar virtualization para listas largas

#### 4.2 Implementar Code Splitting
**Problema**: Bundle size grande
```typescript
// Implementar lazy loading
const TaskView = React.lazy(() => import('./components/TaskView'));
const ConfigPanel = React.lazy(() => import('./components/ConfigPanel'));
const MemoryManager = React.lazy(() => import('./components/MemoryManager'));

// En App.tsx
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/task/:id" element={<TaskView />} />
    <Route path="/config" element={<ConfigPanel />} />
    <Route path="/memory" element={<MemoryManager />} />
  </Routes>
</Suspense>
```

**Tareas Específicas**:
- [ ] Implementar route-based code splitting
- [ ] Crear component-based lazy loading
- [ ] Optimizar imports
- [ ] Implementar preloading strategies

#### 4.3 Optimizar Backend Performance
**Problema**: Queries ineficientes y memory usage alto
```python
# Optimizar: task_manager.py
from functools import lru_cache
import asyncio

class TaskManager:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutos
    
    @lru_cache(maxsize=128)
    def get_task_cached(self, task_id: str) -> Optional[Task]:
        """Obtener tarea con cache"""
        cache_key = f"task_{task_id}"
        cached = self._cache.get(cache_key)
        
        if cached and time.time() - cached['timestamp'] < self._cache_ttl:
            return cached['data']
        
        # Cargar de DB
        task = self.db_service.get_task(task_id)
        if task:
            self._cache[cache_key] = {
                'data': task,
                'timestamp': time.time()
            }
        
        return task
    
    async def execute_task_async(self, task_id: str):
        """Ejecución asíncrona mejorada"""
        task = await self.get_task_async(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Ejecutar pasos en paralelo cuando sea posible
        parallel_steps = self._identify_parallel_steps(task.plan)
        
        for step_group in parallel_steps:
            if len(step_group) == 1:
                await self._execute_step_async(step_group[0])
            else:
                await asyncio.gather(*[
                    self._execute_step_async(step) for step in step_group
                ])
```

**Tareas Específicas**:
- [ ] Implementar caching inteligente
- [ ] Optimizar queries de MongoDB
- [ ] Implementar ejecución paralela
- [ ] Crear connection pooling

### FASE 5: TESTING Y CALIDAD (Semanas 9-10)

#### Objetivo Principal: Cobertura de Tests Comprehensiva

#### 5.1 Implementar Testing Frontend
**Problema**: Falta de tests unitarios
```typescript
// Crear: src/components/__tests__/TaskView.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TaskView } from '../TaskView';
import { AppProvider } from '../../context/AppContext';

const mockTask = {
  id: 'test-task-1',
  message: 'Test task',
  plan: [
    {
      id: 'step-1',
      title: 'Test Step',
      description: 'Test step description',
      status: 'pending',
      tool: 'web_search'
    }
  ],
  status: 'ready',
  messages: [],
  createdAt: new Date().toISOString()
};

const renderTaskView = (task = mockTask) => {
  return render(
    <AppProvider>
      <TaskView task={task} onUpdateTask={jest.fn()} />
    </AppProvider>
  );
};

describe('TaskView', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render task information correctly', () => {
    renderTaskView();
    
    expect(screen.getByText('Test task')).toBeInTheDocument();
    expect(screen.getByText('Test Step')).toBeInTheDocument();
    expect(screen.getByText('Test step description')).toBeInTheDocument();
  });

  it('should handle step execution', async () => {
    const mockOnUpdateTask = jest.fn();
    renderTaskView();
    
    const executeButton = screen.getByText('Execute Step');
    fireEvent.click(executeButton);
    
    await waitFor(() => {
      expect(mockOnUpdateTask).toHaveBeenCalledWith('test-task-1', {
        plan: expect.arrayContaining([
          expect.objectContaining({
            id: 'step-1',
            status: 'in-progress'
          })
        ])
      });
    });
  });

  it('should display error state correctly', () => {
    const errorTask = {
      ...mockTask,
      status: 'error',
      error: 'Test error message'
    };
    
    renderTaskView(errorTask);
    
    expect(screen.getByText('Test error message')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('should handle plan updates', () => {
    const { rerender } = renderTaskView();
    
    const updatedTask = {
      ...mockTask,
      plan: [
        {
          ...mockTask.plan[0],
          status: 'completed'
        }
      ]
    };
    
    rerender(
      <AppProvider>
        <TaskView task={updatedTask} onUpdateTask={jest.fn()} />
      </AppProvider>
    );
    
    expect(screen.getByText('✓')).toBeInTheDocument();
  });
});
```

**Tareas Específicas**:
- [ ] Configurar Jest y Testing Library
- [ ] Crear tests unitarios para componentes
- [ ] Implementar integration tests
- [ ] Crear tests E2E con Playwright

#### 5.2 Implementar Testing Backend
**Problema**: Falta de tests para API
```python
# Crear: tests/test_agent_routes.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.main import app

client = TestClient(app)

class TestAgentRoutes:
    def setup_method(self):
        """Setup para cada test"""
        self.mock_task_data = {
            'id': 'test-task-1',
            'message': 'Test task',
            'plan': [
                {
                    'id': 'step-1',
                    'title': 'Test Step',
                    'description': 'Test description',
                    'tool': 'web_search',
                    'status': 'pending'
                }
            ],
            'status': 'ready'
        }

    @patch('src.routes.agent_routes.get_task_data')
    def test_get_task_status_existing_task(self, mock_get_task_data):
        """Test obtener status de tarea existente"""
        mock_get_task_data.return_value = self.mock_task_data
        
        response = client.get('/api/agent/get-task-status/test-task-1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['task_id'] == 'test-task-1'
        assert data['status'] == 'plan_generated'
        assert len(data['plan']) == 1

    @patch('src.routes.agent_routes.get_task_data')
    def test_get_task_status_nonexistent_task(self, mock_get_task_data):
        """Test obtener status de tarea inexistente"""
        mock_get_task_data.return_value = None
        
        response = client.get('/api/agent/get-task-status/nonexistent')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'not found' in data['error']

    @patch('src.routes.agent_routes.execute_single_step_logic')
    @patch('src.routes.agent_routes.get_task_data')
    def test_execute_step_detailed(self, mock_get_task_data, mock_execute_step):
        """Test ejecutar paso específico"""
        mock_get_task_data.return_value = self.mock_task_data
        mock_execute_step.return_value = {
            'success': True,
            'type': 'web_search',
            'summary': 'Search completed'
        }
        
        response = client.post('/api/agent/execute-step-detailed/test-task-1/step-1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['step_completed'] is True
        assert 'step_result' in data

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get('/api/agent/health')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'mongodb' in data
        assert 'ollama' in data

    @patch('src.routes.agent_routes.get_ollama_service')
    def test_generate_plan_with_ollama(self, mock_get_ollama_service):
        """Test generar plan con Ollama"""
        mock_ollama_service = Mock()
        mock_ollama_service.generate_text.return_value = '''
        {
            "steps": [
                {
                    "title": "Generated Step",
                    "description": "Generated description",
                    "tool": "web_search",
                    "estimated_time": "2 minutes"
                }
            ],
            "task_type": "research",
            "complexity": "medium"
        }
        '''
        mock_get_ollama_service.return_value = mock_ollama_service
        
        response = client.post('/api/agent/generate-plan', json={
            'task_title': 'Test research task',
            'task_id': 'test-task-1'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'plan' in data
        assert len(data['plan']) == 1
        assert data['plan'][0]['title'] == 'Generated Step'
```

**Tareas Específicas**:
- [ ] Configurar pytest y fixtures
- [ ] Crear tests unitarios para routes
- [ ] Implementar tests para herramientas
- [ ] Crear tests de integración con MongoDB

#### 5.3 Implementar CI/CD Pipeline
**Problema**: Falta de automatización
```yaml
# Crear: .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'yarn'
          cache-dependency-path: frontend/yarn.lock
      
      - name: Install dependencies
        run: |
          cd frontend
          yarn install --frozen-lockfile
      
      - name: Run tests
        run: |
          cd frontend
          yarn test --coverage --watchAll=false
      
      - name: Run lint
        run: |
          cd frontend
          yarn lint
      
      - name: Build
        run: |
          cd frontend
          yarn build
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/lcov.info
          flags: frontend

  test-backend:
    runs-on: ubuntu-latest
    services:
      mongodb:
        image: mongo:6.0
        ports:
          - 27017:27017
        options: >-
          --health-cmd="echo 'db.runCommand(\"ping\").ok' | mongosh localhost:27017/test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: |
          cd backend
          pytest --cov=src --cov-report=xml
        env:
          MONGO_URL: mongodb://localhost:27017/test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [test-frontend, test-backend]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install Playwright
        run: |
          npm install -g @playwright/test
          playwright install
      
      - name: Run E2E tests
        run: |
          cd e2e
          playwright test
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: e2e/playwright-report/
```

**Tareas Específicas**:
- [ ] Configurar GitHub Actions
- [ ] Implementar tests automatizados
- [ ] Configurar coverage reporting
- [ ] Implementar quality gates

### FASE 6: DOCUMENTACIÓN Y FINALIZACIÓN (Semanas 11-12)

#### Objetivo Principal: Documentación Completa y Deployment

#### 6.1 Crear Documentación Técnica
**Problema**: Falta de documentación
```markdown
# Crear: docs/ARCHITECTURE.md
# Mitosis Agent - Arquitectura Técnica

## Visión General
Mitosis es una aplicación de agente general que combina FastAPI (backend) con React (frontend) para proporcionar automatización inteligente de tareas.

## Arquitectura del Sistema

### Backend Architecture
```
Backend (FastAPI)
├── API Layer (FastAPI routes)
├── Business Logic (Services)
├── Tool System (Pluggable tools)
├── Memory System (Multi-type memory)
├── Database Layer (MongoDB)
└── AI Integration (Ollama)
```

### Frontend Architecture
```
Frontend (React + TypeScript)
├── UI Components (React components)
├── State Management (Context API)
├── API Client (Axios/Fetch)
├── Real-time Communication (WebSocket)
└── Local Storage (Persistence)
```

## Flujo de Datos

### 1. Task Creation Flow
1. User inputs task in VanishInput
2. ChatInterface processes input
3. Backend generates plan using Ollama
4. Plan stored in MongoDB
5. Frontend displays plan
6. User can execute steps

### 2. Step Execution Flow
1. User clicks execute step
2. Frontend calls execute-step-detailed API
3. Backend uses appropriate tool
4. Results stored in database
5. Progress updated via WebSocket
6. Frontend displays results

## Componentes Clave

### Backend Services
- **TaskManager**: Gestión de tareas y persistencia
- **OllamaService**: Integración con LLM
- **ToolManager**: Gestión de herramientas
- **DatabaseService**: Interacciones con MongoDB
- **MemoryManager**: Sistema de memoria avanzado

### Frontend Components
- **TaskView**: Vista principal de tareas
- **ChatInterface**: Interfaz de chat
- **TerminalView**: Terminal de ejecución
- **Sidebar**: Navegación y configuración
- **MemoryManager**: Gestión de memoria

## Configuración y Deployment

### Desarrollo
```bash
# Backend
cd backend
pip install -r requirements.txt
python server.py

# Frontend
cd frontend
yarn install
yarn dev
```

### Producción
```bash
# Docker
docker-compose up -d

# O manual
python -m uvicorn server:app --host 0.0.0.0 --port 8001
```

## Testing

### Frontend Tests
```bash
cd frontend
yarn test
```

### Backend Tests
```bash
cd backend
pytest
```

### E2E Tests
```bash
cd e2e
playwright test
```
```

**Tareas Específicas**:
- [ ] Crear documentación de arquitectura
- [ ] Documentar API endpoints
- [ ] Crear guías de deployment
- [ ] Documentar configuración

#### 6.2 Optimizar para Producción
**Problema**: Configuración de desarrollo
```python
# Crear: backend/config/production.py
import os
from typing import Optional

class ProductionConfig:
    # Database
    MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017/mitosis')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Performance
    WORKER_COUNT = int(os.getenv('WORKER_COUNT', '4'))
    MAX_CONNECTIONS = int(os.getenv('MAX_CONNECTIONS', '100'))
    
    # Features
    ENABLE_WEBSOCKET = os.getenv('ENABLE_WEBSOCKET', 'true').lower() == 'true'
    ENABLE_MEMORY_SYSTEM = os.getenv('ENABLE_MEMORY_SYSTEM', 'true').lower() == 'true'
    
    # Ollama
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1')
    
    # Tools
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')
    
    @classmethod
    def validate(cls):
        """Validar configuración"""
        errors = []
        
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'your-secret-key-here':
            errors.append('SECRET_KEY must be set')
        
        if not cls.MONGO_URL:
            errors.append('MONGO_URL must be set')
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
```

**Tareas Específicas**:
- [ ] Crear configuración de producción
- [ ] Implementar health checks
- [ ] Configurar logging
- [ ] Optimizar performance

### Métricas de Éxito - KPIs Específicos

#### Métricas Técnicas
- **Reducción de Código**: 40% menos líneas de código duplicado
- **Cobertura de Tests**: 85% mínimo (actualmente 0%)
- **Performance**: 50% mejora en time-to-interactive
- **Bundle Size**: 35% reducción en tamaño de bundle
- **Memory Usage**: 30% reducción en uso de memoria
- **WebSocket Latency**: <100ms para actualizaciones en tiempo real

#### Métricas de Calidad
- **Duplicación de Código**: <3% (actualmente ~20%)
- **Complejidad Ciclomática**: <8 por función (actualmente >15)
- **ESLint Errors**: 0 errores (actualmente 50+)
- **TypeScript Coverage**: 90% (actualmente 60%)
- **Error Rate**: <0.05% en producción
- **MTTR**: <5 minutos para errores críticos

#### Métricas de Experiencia
- **Time to Task Creation**: <2 segundos
- **Step Execution Time**: <5 segundos promedio
- **UI Responsiveness**: <16ms frame time
- **Error Recovery**: <1 segundo para reconexión

### Hoja de Ruta Detallada de Implementación

#### Semana 1: Análisis y Preparación
- [ ] **Día 1-2**: Auditoría completa del código existente
- [ ] **Día 3-4**: Configuración del entorno de desarrollo
- [ ] **Día 5-7**: Preparación de herramientas y dependencies

#### Semana 2: Estabilización de Comunicación
- [ ] **Día 8-10**: Diagnóstico y corrección de WebSocket
- [ ] **Día 11-12**: Implementación de configuración centralizada
- [ ] **Día 13-14**: Error boundaries y manejo de errores

#### Semana 3: Consolidación de Estado
- [ ] **Día 15-17**: Implementación de Context API
- [ ] **Día 18-19**: Migración de componentes a Context
- [ ] **Día 20-21**: Custom hooks especializados

#### Semana 4: Finalización de Estado
- [ ] **Día 22-24**: Estado persistente y migración
- [ ] **Día 25-26**: Testing de gestión de estado
- [ ] **Día 27-28**: Refinamiento y optimización

#### Semana 5: Abstracción de Herramientas
- [ ] **Día 29-31**: Clase base para herramientas
- [ ] **Día 32-33**: Migración de herramientas existentes
- [ ] **Día 34-35**: Tool registry y factory pattern

#### Semana 6: Finalización de Herramientas
- [ ] **Día 36-38**: Testing de herramientas
- [ ] **Día 39-40**: Plugin system
- [ ] **Día 41-42**: Documentación de herramientas

#### Semana 7: Optimización de Performance
- [ ] **Día 43-45**: React.memo y optimizaciones
- [ ] **Día 46-47**: Code splitting y lazy loading
- [ ] **Día 48-49**: Bundle optimization

#### Semana 8: Finalización de Performance
- [ ] **Día 50-52**: Backend optimization
- [ ] **Día 53-54**: Caching y database optimization
- [ ] **Día 55-56**: Performance testing

#### Semana 9: Testing Frontend
- [ ] **Día 57-59**: Unit tests para componentes
- [ ] **Día 60-61**: Integration tests
- [ ] **Día 62-63**: Testing utilities

#### Semana 10: Testing Backend
- [ ] **Día 64-66**: Unit tests para APIs
- [ ] **Día 67-68**: Integration tests con MongoDB
- [ ] **Día 69-70**: E2E tests con Playwright

#### Semana 11: Documentación
- [ ] **Día 71-73**: Documentación técnica
- [ ] **Día 74-75**: API documentation
- [ ] **Día 76-77**: Deployment guides

#### Semana 12: Finalización y Deployment
- [ ] **Día 78-80**: Configuración de producción
- [ ] **Día 81-82**: CI/CD pipeline
- [ ] **Día 83-84**: Final testing y deployment

### Consideraciones de Implementación

#### Riesgos Potenciales y Mitigaciones
1. **WebSocket Restoration Risk**: Posible interrupción del servicio
   - **Mitigación**: Implementar fallback a HTTP polling
   - **Timeline**: Máximo 2 días de downtime

2. **Context Migration Risk**: Posible breaking changes
   - **Mitigación**: Migración gradual por componente
   - **Timeline**: Testing exhaustivo en cada paso

3. **Performance Regression Risk**: Optimizaciones pueden introducir bugs
   - **Mitigación**: Benchmarking antes y después
   - **Timeline**: Rollback plan preparado

4. **Tool Migration Risk**: Herramientas pueden fallar
   - **Mitigación**: Migración una por una con fallback
   - **Timeline**: Testing individual por herramienta

#### Estrategias de Mitigación Específicas
1. **Feature Flags**: Implementar feature flags para cambios críticos
2. **Canary Deployment**: Despliegue gradual en producción
3. **Monitoring**: Monitoreo exhaustivo de métricas
4. **Rollback Strategy**: Plan de rollback para cada fase

#### Recursos Necesarios
- **Desarrollador Senior Full-Stack**: 1 FTE por 12 semanas
- **QA Engineer**: 0.5 FTE por 6 semanas (semanas 7-12)
- **DevOps Engineer**: 0.25 FTE por 4 semanas (semanas 9-12)
- **Herramientas**: Testing frameworks, monitoring tools, CI/CD

### Beneficios Esperados Post-Refactorización

#### Mejoras Técnicas
1. **Arquitectura Más Robusta**: Single source of truth, estado centralizado
2. **Comunicación Mejorada**: WebSocket real, latencia reducida
3. **Código Más Limpio**: Menos duplicación, mejor organización
4. **Testing Comprehensivo**: Confianza en cambios, menos bugs
5. **Performance Optimizada**: Carga más rápida, mejor UX

#### Mejoras de Desarrollo
1. **Desarrollo Más Rápido**: Menos tiempo en debugging
2. **Onboarding Mejorado**: Código más fácil de entender
3. **Mantenimiento Simplificado**: Cambios más fáciles de implementar
4. **Escalabilidad Mejorada**: Arquitectura soporta crecimiento

#### Mejoras de Producto
1. **UX Mejorada**: Interacciones más fluidas
2. **Confiabilidad Aumentada**: Menos errores en producción
3. **Performance Mejor**: Aplicación más responsiva
4. **Funcionalidad Expandida**: Más fácil agregar features

### Conclusión

Este plan de refactorización comprehensivo transformará Mitosis de una aplicación con deuda técnica significativa en un sistema robusto, escalable y mantenible. La implementación gradual y las métricas de éxito claras garantizan que el proceso sea controlado, medible y exitoso.

El enfoque en comunicación real-time, gestión de estado centralizada, abstracción de herramientas y optimización de performance asegura que el sistema resultante será significativamente superior en términos de arquitectura, performance y experiencia de usuario.

La inversión en refactorización pagará dividendos inmediatos en términos de velocidad de desarrollo, estabilidad del sistema y capacidad de agregar nuevas funcionalidades de manera eficiente y confiable.