# REFACTOR STRATEGY - Mitosis Agent 
## Estrategia de Refactorización Detallada (2025-01-26)

### 🎯 OBJETIVOS PRINCIPALES

1. **Restaurar WebSocket Real**: Eliminar HTTP Polling y restaurar comunicación en tiempo real
2. **Centralizar Estado**: Implementar Context API para single source of truth
3. **Eliminar Duplicación**: Consolidar lógica duplicada (URLs, validación, etc.)
4. **Optimizar Performance**: Reducir re-renders y bundle size
5. **Abstraer Herramientas**: Unificar API de 15+ herramientas backend
6. **Implementar Testing**: Cobertura de tests comprehensiva

### 📊 ANÁLISIS DE IMPACTO

#### Problemas Críticos Identificados:
- **HTTP Polling**: 🔴 CRÍTICO - Latencia 2s, alta carga CPU
- **URLs Duplicadas**: 🔴 CRÍTICO - 8+ archivos con misma lógica
- **Estado Fragmentado**: 🔴 CRÍTICO - Race conditions en TaskView/ChatInterface
- **WebSocket Roto**: 🔴 CRÍTICO - "server error" no diagnosticado
- **Sin Error Boundaries**: 🟡 ALTO - Crashes no controlados
- **Bundle Size**: 🟡 MEDIO - Imports no optimizados

### 🔧 PLAN DE EJECUCIÓN DETALLADO

---

## FASE 1: ANÁLISIS Y BACKUP COMPLETO ✅

### ✅ Completado:
- [x] Backup completo (264MB, 18,598 archivos)
- [x] Análisis de estructura frontend
- [x] Análisis de estructura backend  
- [x] Identificación de patterns duplicados
- [x] Mapeo de dependencias críticas

### ⏭️ Próximas Acciones:
1. **Verificar Funcionalidad Actual**
   - Probar creación de tareas
   - Verificar ejecución de steps  
   - Comprobar chat interface
   - Validar terminal updates

2. **Actualizar ANALYSIS_PLAN.md**
   - Agregar nuevos hallazgos específicos
   - Actualizar métricas de deuda técnica
   - Documentar estado actual vs objetivo

---

## FASE 2: ESTABILIZACIÓN DE COMUNICACIÓN 🔄

### 🎯 Objetivo: Restaurar WebSocket y eliminar HTTP Polling

#### 2.1 Diagnóstico WebSocket (Estimado: 4 horas)
**Archivos a Analizar**:
- `/app/backend/src/websocket/websocket_manager.py` (417 líneas)
- `/app/backend/server.py` (configuración SocketIO)
- `/app/frontend/src/hooks/useWebSocket.ts` (150 líneas)

**Acciones Específicas**:
```bash
# Verificar logs de WebSocket
tail -f /var/log/supervisor/backend.*.log | grep -i websocket

# Probar conexión WebSocket directa
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" \
     http://localhost:8001/socket.io/

# Diagnosticar CORS y middleware
grep -r "CORS\|cors" /app/backend/
```

**Problemas Esperados**:
- CORS configuration incorrecta
- SocketIO version mismatch
- Event handler registration issues
- Room management problems

#### 2.2 Crear Nueva Implementación WebSocket (Estimado: 6 horas)
**Archivo Nuevo**: `/app/frontend/src/config/websocket.ts`
```typescript
// Configuración centralizada WebSocket
export const WEBSOCKET_CONFIG = {
  url: API_CONFIG.getWebSocketUrl(),
  options: {
    transports: ['websocket', 'polling'], // Fallback automático
    upgrade: true,
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5,
    timeout: 20000
  }
};
```

**Modificar**: `/app/frontend/src/hooks/useWebSocket.ts`
```typescript
// ANTES: HTTP Polling simulation
const useWebSocket = (): UseWebSocketReturn => {
  pollingIntervalRef.current = setInterval(async () => {
    const response = await fetch(`${backendUrl}/api/agent/get-task-status/${taskId}`);
  }, 2000);
};

// DESPUÉS: WebSocket real con fallback
const useWebSocket = (): UseWebSocketReturn => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const newSocket = io(WEBSOCKET_CONFIG.url, WEBSOCKET_CONFIG.options);
    
    newSocket.on('connect', () => {
      setIsConnected(true);
      console.log('✅ WebSocket connected');
    });
    
    newSocket.on('connect_error', (error) => {
      console.error('❌ WebSocket error:', error);
      // Fallback automático a HTTP polling si falla
      if (!pollingFallback) {
        initializeHttpPollingFallback();
      }
    });
    
    setSocket(newSocket);
    return () => newSocket.close();
  }, []);
};
```

#### 2.3 Unificar Configuración URLs (Estimado: 3 horas)
**Archivo Nuevo**: `/app/frontend/src/config/api.ts`
```typescript
// Configuración centralizada de API
interface ApiConfig {
  backend: {
    url: string;
    wsUrl: string;
  };
  endpoints: {
    chat: string;
    generatePlan: string;
    executeStep: string;
    taskStatus: string;
    health: string;
  };
}

export const API_CONFIG: ApiConfig = {
  backend: {
    url: getBackendUrl(),
    wsUrl: getWebSocketUrl()
  },
  endpoints: {
    chat: '/api/agent/chat',
    generatePlan: '/api/agent/generate-plan',
    executeStep: '/api/agent/execute-step-detailed',
    taskStatus: '/api/agent/get-task-status',
    health: '/api/agent/health'
  }
};

function getBackendUrl(): string {
  const url = import.meta.env.VITE_BACKEND_URL || 
              import.meta.env.REACT_APP_BACKEND_URL || 
              process.env.REACT_APP_BACKEND_URL;
  
  if (!url) {
    throw new Error('Backend URL not configured');
  }
  
  return url;
}
```

**Archivos a Refactorizar** (eliminar duplicación):
- `/app/frontend/src/services/api.ts` (líneas 2-6)
- `/app/frontend/src/hooks/useWebSocket.ts` (líneas 37-40)
- `/app/frontend/src/components/ChatInterface/ChatInterface.tsx`
- `/app/frontend/src/components/TaskView.tsx`
- `/app/frontend/src/App.tsx`
- +3 archivos más

#### 2.4 Implementar Error Boundaries (Estimado: 2 horas)
**Archivo Nuevo**: `/app/frontend/src/components/ErrorBoundary.tsx`
```typescript
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

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    
    // Enviar error a servicio de monitoreo
    console.error('[ErrorBoundary]', error, errorInfo);
    
    // Opcional: Enviar a backend para logging
    if (window.navigator.sendBeacon) {
      window.navigator.sendBeacon('/api/agent/log-error', JSON.stringify({
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      }));
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary bg-red-500/10 border border-red-500/20 rounded-lg p-6 m-4">
          <h2 className="text-red-400 text-lg font-semibold mb-2">
            ⚠️ Something went wrong
          </h2>
          <p className="text-red-300 mb-4">
            The application encountered an unexpected error. Please try refreshing the page.
          </p>
          <details className="text-sm text-red-200">
            <summary className="cursor-pointer hover:text-red-100">
              Error details (click to expand)
            </summary>
            <pre className="mt-2 p-2 bg-black/20 rounded text-xs overflow-auto">
              {this.state.error?.message}
              {this.state.errorInfo?.componentStack}
            </pre>
          </details>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition-colors"
          >
            🔄 Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Integración en App.tsx**:
```typescript
// Envolver componentes críticos
<ErrorBoundary>
  <Sidebar />
</ErrorBoundary>

<ErrorBoundary>
  <TaskView />
</ErrorBoundary>
```

### 📊 Métricas de Éxito Fase 2:
- [ ] WebSocket conectando sin "server error"
- [ ] Latencia < 100ms (vs 2000ms HTTP polling)
- [ ] URLs centralizadas (1 archivo vs 8+)
- [ ] Error boundaries capturando errores
- [ ] 0 crashes no controlados

---

## FASE 3: CONSOLIDACIÓN DE ESTADO 🔄

### 🎯 Objetivo: Crear Single Source of Truth con Context API

#### 3.1 Crear Context API Global (Estimado: 8 horas)
**Archivo Nuevo**: `/app/frontend/src/context/AppContext.tsx`
```typescript
// Estado global centralizado
interface AppState {
  // Tasks
  tasks: Task[];
  activeTaskId: string | null;
  isTaskCreating: boolean;
  
  // Messages  
  messages: Message[];
  isMessageLoading: boolean;
  
  // UI State
  sidebarCollapsed: boolean;
  terminalSize: number;
  isThinking: boolean;
  
  // Configuration
  agentConfig: AgentConfig;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
  
  // Application State
  currentView: 'home' | 'task' | 'config';
  initializingTaskId: string | null;
}

// Actions centralizadas
interface AppActions {
  // Task Actions
  createTask: (message: string) => Promise<Task>;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  deleteTask: (taskId: string) => void;
  setActiveTask: (taskId: string | null) => void;
  
  // Message Actions
  addMessage: (message: Message) => void;
  updateMessages: (taskId: string, messages: Message[]) => void;
  
  // UI Actions
  toggleSidebar: () => void;
  setTerminalSize: (size: number) => void;
  setThinking: (thinking: boolean) => void;
  
  // Config Actions
  updateConfig: (config: Partial<AgentConfig>) => void;
  setConnectionStatus: (status: 'connected' | 'disconnected' | 'connecting') => void;
}

const AppContext = createContext<{
  state: AppState;
  actions: AppActions;
} | null>(null);

// Reducer para estado complejo
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'CREATE_TASK':
      return {
        ...state,
        tasks: [action.payload, ...state.tasks],
        activeTaskId: action.payload.id,
        currentView: 'task'
      };
      
    case 'UPDATE_TASK':
      return {
        ...state,
        tasks: state.tasks.map(task => 
          task.id === action.payload.taskId 
            ? { ...task, ...action.payload.updates }
            : task
        )
      };
      
    case 'DELETE_TASK':
      const remainingTasks = state.tasks.filter(t => t.id !== action.payload);
      return {
        ...state,
        tasks: remainingTasks,
        activeTaskId: state.activeTaskId === action.payload 
          ? (remainingTasks[0]?.id || null)
          : state.activeTaskId
      };
      
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload]
      };
      
    case 'TOGGLE_SIDEBAR':
      return {
        ...state,
        sidebarCollapsed: !state.sidebarCollapsed
      };
      
    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        connectionStatus: action.payload
      };
      
    default:
      return state;
  }
}

// Provider con lógica completa
export const AppProvider: React.FC<React.PropsWithChildren<{}>> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  // Actions memoizadas para performance
  const actions = useMemo<AppActions>(() => ({
    createTask: async (message: string) => {
      dispatch({ type: 'SET_TASK_CREATING', payload: true });
      
      try {
        const newTask: Task = {
          id: `task-${Date.now()}`,
          title: message,
          createdAt: new Date(),
          status: 'pending',
          messages: [{
            id: `msg-${Date.now()}`,
            content: message,
            sender: 'user',
            timestamp: new Date()
          }],
          terminalCommands: [],
          isFavorite: false,
          progress: 0
        };
        
        dispatch({ type: 'CREATE_TASK', payload: newTask });
        
        // Generate plan and enhance title
        const backendUrl = API_CONFIG.backend.url;
        const response = await fetch(`${backendUrl}${API_CONFIG.endpoints.generatePlan}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task_title: message.trim(),
            task_id: newTask.id
          })
        });
        
        if (response.ok) {
          const planData = await response.json();
          
          dispatch({ type: 'UPDATE_TASK', payload: {
            taskId: newTask.id,
            updates: {
              title: planData.enhanced_title || message,
              plan: planData.plan,
              status: 'in-progress',
              iconType: planData.suggested_icon
            }
          }});
        }
        
        return newTask;
      } catch (error) {
        console.error('Error creating task:', error);
        throw error;
      } finally {
        dispatch({ type: 'SET_TASK_CREATING', payload: false });
      }
    },
    
    updateTask: (taskId: string, updates: Partial<Task>) => {
      dispatch({ type: 'UPDATE_TASK', payload: { taskId, updates } });
    },
    
    deleteTask: (taskId: string) => {
      dispatch({ type: 'DELETE_TASK', payload: taskId });
    },
    
    setActiveTask: (taskId: string | null) => {
      dispatch({ type: 'SET_ACTIVE_TASK', payload: taskId });
    },
    
    addMessage: (message: Message) => {
      dispatch({ type: 'ADD_MESSAGE', payload: message });
    },
    
    updateMessages: (taskId: string, messages: Message[]) => {
      dispatch({ type: 'UPDATE_TASK', payload: {
        taskId,
        updates: { messages }
      }});
    },
    
    toggleSidebar: () => {
      dispatch({ type: 'TOGGLE_SIDEBAR' });
    },
    
    setTerminalSize: (size: number) => {
      dispatch({ type: 'SET_TERMINAL_SIZE', payload: size });
    },
    
    setThinking: (thinking: boolean) => {
      dispatch({ type: 'SET_THINKING', payload: thinking });
    },
    
    updateConfig: (config: Partial<AgentConfig>) => {
      dispatch({ type: 'UPDATE_CONFIG', payload: config });
    },
    
    setConnectionStatus: (status: 'connected' | 'disconnected' | 'connecting') => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: status });
    }
  }), []);
  
  return (
    <AppContext.Provider value={{ state, actions }}>
      {children}
    </AppContext.Provider>
  );
};

// Hook personalizado para usar el contexto
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};
```

#### 3.2 Migrar Estado de Componentes (Estimado: 6 horas)
**Modificar TaskView.tsx**:
```typescript
// ANTES: Estado local
const TaskView: React.FC<TaskViewProps> = ({ task, onUpdateTask }) => {
  const [isTyping, setIsTyping] = useState(false);
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [taskFiles, setTaskFiles] = useState<FileItem[]>([]);
  
// DESPUÉS: Context API
const TaskView: React.FC<TaskViewProps> = () => {
  const { state, actions } = useAppContext();
  const { tasks, activeTaskId, messages, isThinking } = state;
  const activeTask = tasks.find(t => t.id === activeTaskId);
  
  // Estado local solo para UI específica del componente
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [taskFiles, setTaskFiles] = useState<FileItem[]>([]);
```

**Modificar ChatInterface.tsx**:
```typescript
// ANTES: Props drilling
interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  // ... 10+ props más
}

// DESPUÉS: Context API  
interface ChatInterfaceProps {
  // Solo props específicas del componente
  placeholder?: string;
  disabled?: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ placeholder, disabled }) => {
  const { state, actions } = useAppContext();
  const { messages, isMessageLoading } = state;
  
  const handleSendMessage = (message: string) => {
    actions.addMessage({
      id: `msg-${Date.now()}`,
      content: message,
      sender: 'user',
      timestamp: new Date()
    });
  };
```

#### 3.3 Crear Custom Hooks Especializados (Estimado: 4 horas)
**Archivo Nuevo**: `/app/frontend/src/hooks/useTaskManagement.ts`
```typescript
export const useTaskManagement = () => {
  const { state, actions } = useAppContext();
  
  const createTaskWithMessage = useCallback(async (message: string) => {
    try {
      const task = await actions.createTask(message);
      return task;
    } catch (error) {
      console.error('Error creating task with message:', error);
      throw error;
    }
  }, [actions]);
  
  const executeTaskStep = useCallback(async (taskId: string, stepId: string) => {
    try {
      const response = await fetch(
        `${API_CONFIG.backend.url}${API_CONFIG.endpoints.executeStep}/${taskId}/${stepId}`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' } }
      );
      
      if (response.ok) {
        const result = await response.json();
        
        // Actualizar task con resultado
        actions.updateTask(taskId, {
          plan: result.updatedPlan,
          status: result.taskStatus
        });
        
        return result;
      }
    } catch (error) {
      console.error('Error executing step:', error);
      throw error;
    }
  }, [actions]);
  
  const getActiveTask = useCallback(() => {
    return state.tasks.find(t => t.id === state.activeTaskId);
  }, [state.tasks, state.activeTaskId]);
  
  const getTaskProgress = useCallback((taskId: string) => {
    const task = state.tasks.find(t => t.id === taskId);
    if (!task?.plan) return 0;
    
    const completedSteps = task.plan.filter(step => step.completed).length;
    return Math.round((completedSteps / task.plan.length) * 100);
  }, [state.tasks]);
  
  return {
    tasks: state.tasks,
    activeTask: getActiveTask(),
    isTaskCreating: state.isTaskCreating,
    createTaskWithMessage,
    executeTaskStep,
    getTaskProgress,
    updateTask: actions.updateTask,
    deleteTask: actions.deleteTask
  };
};
```

**Archivo Nuevo**: `/app/frontend/src/hooks/useMessageManagement.ts`
```typescript
export const useMessageManagement = () => {
  const { state, actions } = useAppContext();
  
  const sendMessage = useCallback(async (content: string, taskId?: string) => {
    const message: Message = {
      id: `msg-${Date.now()}`,
      content,
      sender: 'user',
      timestamp: new Date()
    };
    
    actions.addMessage(message);
    
    if (taskId) {
      // Enviar mensaje al backend para procesamiento
      try {
        const response = await fetch(
          `${API_CONFIG.backend.url}${API_CONFIG.endpoints.chat}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: content,
              task_id: taskId,
              context: { user_input: true }
            })
          }
        );
        
        if (response.ok) {
          const result = await response.json();
          
          // Agregar respuesta del agente
          actions.addMessage({
            id: `msg-${Date.now() + 1}`,
            content: result.response,
            sender: 'assistant',
            timestamp: new Date()
          });
        }
      } catch (error) {
        console.error('Error sending message:', error);
      }
    }
    
    return message;
  }, [actions]);
  
  const getMessagesForTask = useCallback((taskId: string) => {
    const task = state.tasks.find(t => t.id === taskId);
    return task?.messages || [];
  }, [state.tasks]);
  
  return {
    messages: state.messages,
    isLoading: state.isMessageLoading,
    sendMessage,
    getMessagesForTask,
    addMessage: actions.addMessage
  };
};
```

#### 3.4 Implementar Estado Persistente (Estimado: 3 horas)
**Archivo Nuevo**: `/app/frontend/src/hooks/usePersistedState.ts`
```typescript
export const usePersistedState = <T>(
  key: string,
  initialValue: T,
  options: {
    storage?: 'localStorage' | 'sessionStorage';
    serializer?: {
      stringify: (value: T) => string;
      parse: (value: string) => T;
    };
  } = {}
): [T, (value: T | ((prev: T) => T)) => void] => {
  const { 
    storage = 'localStorage',
    serializer = JSON
  } = options;
  
  const storageObject = storage === 'localStorage' ? localStorage : sessionStorage;
  
  const [state, setState] = useState<T>(() => {
    try {
      const item = storageObject.getItem(key);
      return item ? serializer.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error loading ${key} from ${storage}:`, error);
      return initialValue;
    }
  });

  const setPersistedState = useCallback((value: T | ((prev: T) => T)) => {
    setState(currentState => {
      const newState = typeof value === 'function' 
        ? (value as (prev: T) => T)(currentState)
        : value;
      
      try {
        storageObject.setItem(key, serializer.stringify(newState));
      } catch (error) {
        console.error(`Error saving ${key} to ${storage}:`, error);
      }
      
      return newState;
    });
  }, [key, storage, serializer, storageObject]);

  // Sync con otros tabs
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        try {
          const newValue = serializer.parse(e.newValue);
          setState(newValue);
        } catch (error) {
          console.error(`Error syncing ${key} from storage:`, error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, serializer]);

  return [state, setPersistedState];
};
```

### 📊 Métricas de Éxito Fase 3:
- [ ] Estado centralizado (0 props drilling)
- [ ] Context API implementado
- [ ] Custom hooks funcionales
- [ ] Estado persistente configurado
- [ ] Componentes sin estado local duplicado

---

## FASE 4: ABSTRACCIÓN DE HERRAMIENTAS 🔄

### 🎯 Objetivo: Unificar API de 15+ herramientas backend

#### 4.1 Crear Clase Base BaseTool (Estimado: 6 horas)
**Archivo Nuevo**: `/app/backend/src/tools/base_tool.py`
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime
import json

class ToolValidationError(Exception):
    """Custom exception for tool validation errors"""
    pass

class BaseTool(ABC):
    """Clase base abstracta para todas las herramientas del sistema"""
    
    def __init__(self, name: str = None, version: str = "1.0.0"):
        self.name = name or self.__class__.__name__.replace('Tool', '').lower()
        self.version = version
        self.logger = logging.getLogger(f"tools.{self.name}")
        self._execution_history: List[Dict[str, Any]] = []
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción de la funcionalidad de la herramienta"""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """Categoría de la herramienta (search, analysis, creation, etc.)"""
        pass
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Esquema JSON de parámetros esperados"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validación común de parámetros"""
        if not isinstance(parameters, dict):
            return {
                'valid': False, 
                'error': 'Parameters must be a dictionary',
                'error_code': 'INVALID_TYPE'
            }
        
        schema = self.get_parameters_schema()
        required_params = schema.get('required', [])
        properties = schema.get('properties', {})
        
        # Validar parámetros requeridos
        for param in required_params:
            if param not in parameters:
                return {
                    'valid': False,
                    'error': f"Required parameter '{param}' is missing",
                    'error_code': 'MISSING_REQUIRED_PARAM',
                    'missing_param': param
                }
        
        # Validar tipos de parámetros
        for param_name, param_value in parameters.items():
            if param_name in properties:
                prop_schema = properties[param_name]
                expected_type = prop_schema.get('type')
                
                if not self._validate_parameter_type(param_value, expected_type):
                    return {
                        'valid': False,
                        'error': f"Parameter '{param_name}' must be of type {expected_type}",
                        'error_code': 'INVALID_PARAM_TYPE',
                        'param_name': param_name,
                        'expected_type': expected_type,
                        'actual_type': type(param_value).__name__
                    }
        
        return {'valid': True}
    
    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validar tipo específico de parámetro"""
        type_validators = {
            'string': lambda x: isinstance(x, str),
            'integer': lambda x: isinstance(x, int),
            'number': lambda x: isinstance(x, (int, float)),
            'boolean': lambda x: isinstance(x, bool),
            'array': lambda x: isinstance(x, list),
            'object': lambda x: isinstance(x, dict),
            'null': lambda x: x is None
        }
        
        validator = type_validators.get(expected_type)
        return validator(value) if validator else True
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar la herramienta con parámetros dados"""
        pass
    
    def safe_execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecución segura con validación y manejo de errores"""
        execution_id = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        start_time = datetime.now()
        self.logger.info(f"[{execution_id}] Starting execution with parameters: {parameters}")
        
        try:
            # Validar parámetros
            validation_result = self.validate_parameters(parameters)
            if not validation_result['valid']:
                error_result = {
                    'success': False,
                    'error': validation_result['error'],
                    'error_code': validation_result.get('error_code', 'VALIDATION_ERROR'),
                    'tool': self.name,
                    'execution_id': execution_id,
                    'execution_time': 0
                }
                self.logger.error(f"[{execution_id}] Validation failed: {validation_result['error']}")
                return error_result
            
            # Ejecutar herramienta
            result = self.execute(parameters, context or {})
            
            # Calcular tiempo de ejecución
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Agregar metadatos estándar
            standard_result = {
                'success': result.get('success', True),
                'tool': self.name,
                'execution_id': execution_id,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat(),
                **result
            }
            
            # Registrar en historial
            self._execution_history.append({
                'execution_id': execution_id,
                'parameters': parameters,
                'result': standard_result,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"[{execution_id}] Execution completed successfully in {execution_time:.2f}s")
            return standard_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_result = {
                'success': False,
                'error': str(e),
                'error_code': 'EXECUTION_ERROR',
                'tool': self.name,
                'execution_id': execution_id,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.error(f"[{execution_id}] Execution failed after {execution_time:.2f}s: {str(e)}")
            return error_result
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información completa de la herramienta"""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'version': self.version,
            'parameters_schema': self.get_parameters_schema(),
            'execution_count': len(self._execution_history),
            'last_execution': self._execution_history[-1]['timestamp'] if self._execution_history else None
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener historial de ejecuciones"""
        return self._execution_history[-limit:] if limit > 0 else self._execution_history
    
    def clear_history(self):
        """Limpiar historial de ejecuciones"""
        self._execution_history.clear()
        self.logger.info(f"Execution history cleared for tool: {self.name}")
```

#### 4.2 Migrar Herramientas Existentes (Estimado: 12 horas)
**Ejemplo: Migrar web_search_tool.py**
```python
# ANTES: Herramienta independiente
class WebSearchTool:
    def __init__(self):
        self.name = "web_search"
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(parameters, dict):
            return {'valid': False, 'error': 'Parameters must be a dictionary'}
        if 'query' not in parameters:
            return {'valid': False, 'error': 'query parameter is required'}
        # ... más validaciones duplicadas

# DESPUÉS: Herramienta que hereda de BaseTool
class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__(name="web_search", version="2.0.0")
    
    @property
    def description(self) -> str:
        return "Perform web searches using Playwright with multiple search engines"
    
    @property
    def category(self) -> str:
        return "search"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to execute",
                    "minLength": 1,
                    "maxLength": 500
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5
                },
                "search_engine": {
                    "type": "string",
                    "description": "Search engine to use",
                    "enum": ["google", "bing", "duckduckgo"],
                    "default": "bing"
                },
                "extract_content": {
                    "type": "boolean",
                    "description": "Whether to extract page content",
                    "default": True
                }
            }
        }
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar búsqueda web"""
        query = parameters['query']
        max_results = parameters.get('max_results', 5)
        search_engine = parameters.get('search_engine', 'bing')
        extract_content = parameters.get('extract_content', True)
        
        try:
            # Lógica específica de búsqueda web
            results = self._perform_web_search(
                query=query,
                max_results=max_results,
                search_engine=search_engine,
                extract_content=extract_content
            )
            
            return {
                'query': query,
                'search_engine': search_engine,
                'results_count': len(results),
                'results': results,
                'summary': f"Found {len(results)} results for '{query}'"
            }
            
        except Exception as e:
            raise ToolValidationError(f"Web search failed: {str(e)}")
    
    def _perform_web_search(self, query: str, max_results: int, 
                           search_engine: str, extract_content: bool) -> List[Dict[str, Any]]:
        """Implementación específica de búsqueda"""
        # ... lógica de búsqueda existente
        pass
```

**Herramientas a migrar** (prioridad por uso):
1. **web_search_tool.py** → WebSearchTool(BaseTool)
2. **file_manager_tool.py** → FileManagerTool(BaseTool)  
3. **tavily_search_tool.py** → TavilySearchTool(BaseTool)
4. **playwright_tool.py** → PlaywrightTool(BaseTool)
5. **shell_tool.py** → ShellTool(BaseTool)
6. **task_planner.py** → TaskPlannerTool(BaseTool)
7. +9 herramientas más

#### 4.3 Crear Tool Registry (Estimado: 4 horas)
**Archivo Nuevo**: `/app/backend/src/tools/tool_registry.py`
```python
from typing import Dict, List, Optional, Type, Any
import importlib
import inspect
from pathlib import Path
from .base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry central para gestión de herramientas"""
    
    def __init__(self, auto_discover: bool = True):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._categories: Dict[str, List[str]] = {}
        
        if auto_discover:
            self.discover_tools()
    
    def discover_tools(self):
        """Auto-descubrir herramientas en el directorio"""
        tools_dir = Path(__file__).parent
        
        for py_file in tools_dir.glob("*_tool.py"):
            if py_file.name == "base_tool.py":
                continue
                
            try:
                module_name = py_file.stem
                module = importlib.import_module(f".{module_name}", package=__package__)
                
                # Buscar clases que hereden de BaseTool
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseTool) and 
                        obj != BaseTool and 
                        not name.startswith('_')):
                        
                        self.register_tool_class(obj)
                        logger.info(f"Discovered tool class: {name}")
                        
            except Exception as e:
                logger.error(f"Error discovering tools in {py_file}: {e}")
    
    def register_tool_class(self, tool_class: Type[BaseTool]):
        """Registrar clase de herramienta"""
        # Crear instancia para obtener metadatos
        try:
            instance = tool_class()
            self._tool_classes[instance.name] = tool_class
            logger.info(f"Registered tool class: {instance.name}")
        except Exception as e:
            logger.error(f"Error registering tool class {tool_class.__name__}: {e}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Obtener instancia de herramienta (lazy loading)"""
        if name in self._tools:
            return self._tools[name]
        
        if name in self._tool_classes:
            try:
                tool_instance = self._tool_classes[name]()
                self._tools[name] = tool_instance
                
                # Actualizar categorías
                category = tool_instance.category
                if category not in self._categories:
                    self._categories[category] = []
                if name not in self._categories[category]:
                    self._categories[category].append(name)
                
                logger.info(f"Instantiated tool: {name}")
                return tool_instance
                
            except Exception as e:
                logger.error(f"Error instantiating tool {name}: {e}")
                return None
        
        logger.warning(f"Tool not found: {name}")
        return None
    
    def execute_tool(self, name: str, parameters: Dict[str, Any], 
                    context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar herramienta por nombre"""
        tool = self.get_tool(name)
        
        if not tool:
            return {
                'success': False,
                'error': f'Tool "{name}" not found',
                'error_code': 'TOOL_NOT_FOUND',
                'available_tools': list(self._tool_classes.keys())
            }
        
        return tool.safe_execute(parameters, context)
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Obtener herramientas por categoría"""
        if category not in self._categories:
            return []
        
        tools = []
        for tool_name in self._categories[category]:
            tool = self.get_tool(tool_name)
            if tool:
                tools.append(tool)
        
        return tools
    
    def get_all_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """Obtener información de todas las herramientas"""
        tools_info = {}
        
        for tool_name in self._tool_classes.keys():
            tool = self.get_tool(tool_name)
            if tool:
                tools_info[tool_name] = tool.get_tool_info()
        
        return tools_info
    
    def get_categories(self) -> Dict[str, List[str]]:
        """Obtener todas las categorías y sus herramientas"""
        # Asegurar que todas las herramientas estén categorizadas
        for tool_name in self._tool_classes.keys():
            self.get_tool(tool_name)  # Trigger lazy loading
        
        return self._categories.copy()
    
    def validate_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros sin ejecutar la herramienta"""
        tool = self.get_tool(tool_name)
        
        if not tool:
            return {
                'valid': False,
                'error': f'Tool "{tool_name}" not found',
                'error_code': 'TOOL_NOT_FOUND'
            }
        
        return tool.validate_parameters(parameters)
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Obtener esquema de parámetros de una herramienta"""
        tool = self.get_tool(tool_name)
        return tool.get_parameters_schema() if tool else None
    
    def reload_tool(self, tool_name: str) -> bool:
        """Recargar herramienta (útil para desarrollo)"""
        if tool_name in self._tools:
            del self._tools[tool_name]
        
        tool = self.get_tool(tool_name)
        return tool is not None
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de ejecución"""
        stats = {
            'total_tools': len(self._tool_classes),
            'instantiated_tools': len(self._tools),
            'categories': len(self._categories),
            'tools_by_category': {},
            'execution_counts': {}
        }
        
        for category, tool_names in self._categories.items():
            stats['tools_by_category'][category] = len(tool_names)
        
        for tool_name, tool in self._tools.items():
            stats['execution_counts'][tool_name] = len(tool.get_execution_history(limit=0))
        
        return stats

# Instancia global del registry
tool_registry = ToolRegistry()

def get_tool_registry() -> ToolRegistry:
    """Obtener instancia global del registry"""
    return tool_registry
```

#### 4.4 Integrar con Sistemas Existentes (Estimado: 3 horas)
**Modificar**: `/app/backend/src/services/tool_manager.py`
```python
# ANTES: Gestión manual de herramientas
class ToolManager:
    def __init__(self):
        self.tools = {
            'web_search': WebSearchTool(),
            'file_manager': FileManagerTool(),
            # ... manual registration
        }

# DESPUÉS: Usar Tool Registry
from ..tools.tool_registry import get_tool_registry

class ToolManager:
    def __init__(self):
        self.registry = get_tool_registry()
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], 
                    task_id: str = None) -> Dict[str, Any]:
        """Ejecutar herramienta usando registry"""
        context = {'task_id': task_id} if task_id else {}
        return self.registry.execute_tool(tool_name, parameters, context)
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Obtener herramientas disponibles"""
        return self.registry.get_all_tools_info()
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Obtener herramientas por categoría"""
        tools = self.registry.get_tools_by_category(category)
        return [tool.get_tool_info() for tool in tools]
```

### 📊 Métricas de Éxito Fase 4:
- [ ] BaseTool implementado
- [ ] 15+ herramientas migradas
- [ ] Tool Registry funcional
- [ ] Código duplicado eliminado (<3%)
- [ ] API unificada para todas las herramientas

---

## FASE 5: OPTIMIZACIÓN DE PERFORMANCE 🔄

### 🎯 Objetivo: Mejorar rendimiento y reducir bundle size

#### 5.1 Implementar React Optimizations (Estimado: 6 horas)
**Modificar componentes críticos con React.memo**:
```typescript
// TaskView.tsx - Optimizado
const TaskView = React.memo<TaskViewProps>(({ 
  taskId 
}) => {
  const { state, actions } = useAppContext();
  const task = useMemo(() => 
    state.tasks.find(t => t.id === taskId), 
    [state.tasks, taskId]
  );
  
  const memoizedPlan = useMemo(() => {
    if (!task?.plan) return null;
    
    return task.plan.map(step => ({
      ...step,
      formattedTime: formatEstimatedTime(step.estimated_time),
      isCompleted: step.status === 'completed',
      isActive: step.status === 'in-progress'
    }));
  }, [task?.plan]);

  const handleStepExecute = useCallback(async (stepId: string) => {
    if (!task) return;
    
    try {
      await actions.executeTaskStep(task.id, stepId);
    } catch (error) {
      console.error('Error executing step:', error);
    }
  }, [task, actions]);

  const handleSendMessage = useCallback(async (message: string) => {
    if (!task) return;
    
    try {
      await actions.sendMessage(message, task.id);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  }, [task, actions]);

  // Early return si no hay task
  if (!task) {
    return <div className="flex-1 flex items-center justify-center">
      <div className="text-gray-400">Task not found</div>
    </div>;
  }

  return (
    <div className="flex-1 flex">
      <div className="w-1/2 flex flex-col">
        <TaskHeader task={task} />
        <ChatInterface 
          onSendMessage={handleSendMessage}
          disabled={state.isMessageLoading}
        />
      </div>
      
      <div className="w-1/2 flex flex-col">
        <PlanView 
          plan={memoizedPlan}
          onStepExecute={handleStepExecute}
        />
        <TerminalView taskId={task.id} />
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison para evitar re-renders innecesarios
  return prevProps.taskId === nextProps.taskId;
});
```

**Implementar React.Suspense y lazy loading**:
```typescript
// App.tsx - Code splitting
const TaskView = React.lazy(() => import('./components/TaskView'));
const ConfigPanel = React.lazy(() => import('./components/ConfigPanel'));
const MemoryManager = React.lazy(() => import('./components/MemoryManager'));

// Loading component optimizado
const LoadingSpinner = React.memo(() => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
  </div>
));

export function App() {
  return (
    <AppProvider>
      <ErrorBoundary>
        <div className="flex h-screen w-full bg-[#272728]">
          <Sidebar />
          
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/" element={<Homepage />} />
              <Route path="/task/:id" element={<TaskView />} />
              <Route path="/config" element={<ConfigPanel />} />
              <Route path="/memory" element={<MemoryManager />} />
            </Routes>
          </Suspense>
        </div>
      </ErrorBoundary>
    </AppProvider>
  );
}
```

#### 5.2 Optimizar Bundle Size (Estimado: 4 horas)
**Configurar Vite para tree shaking**:
```typescript
// vite.config.ts - Optimizado
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['lucide-react'],
          utils: ['date-fns', 'uuid']
        }
      }
    },
    chunkSizeWarningLimit: 600,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'lucide-react'],
    exclude: ['@vite/client', '@vite/env']
  }
});
```

**Optimizar imports**:
```typescript
// ANTES: Import completo
import * as React from 'react';
import { agentAPI } from '../../services/api';

// DESPUÉS: Imports específicos
import { useState, useEffect, useCallback, useMemo } from 'react';
import { sendMessage, getTaskStatus } from '../../services/api';
```

#### 5.3 Implementar Virtualization (Estimado: 3 horas)
**Para listas largas de tareas y mensajes**:
```typescript
// Instalar: yarn add react-window react-window-infinite-loader
import { FixedSizeList as List } from 'react-window';

const MessageList = React.memo<{ messages: Message[] }>(({ messages }) => {
  const itemHeight = 60; // Altura estimada por mensaje
  const containerHeight = 400; // Altura del contenedor

  const renderMessage = useCallback(({ index, style }: any) => {
    const message = messages[index];
    
    return (
      <div style={style} key={message.id}>
        <MessageItem message={message} />
      </div>
    );
  }, [messages]);

  return (
    <List
      height={containerHeight}
      itemCount={messages.length}
      itemSize={itemHeight}
      itemData={messages}
    >
      {renderMessage}
    </List>
  );
});
```

#### 5.4 Optimizar Backend Performance (Estimado: 4 horas)
**Implementar caching en TaskManager**:
```python
# task_manager.py - Con caching
from functools import lru_cache
from typing import Optional, Dict, Any
import time

class TaskManager:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutos
    
    @lru_cache(maxsize=128)
    def get_task_cached(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener tarea con cache LRU"""
        cache_key = f"task_{task_id}"
        cached_entry = self._cache.get(cache_key)
        
        if cached_entry and time.time() - cached_entry['timestamp'] < self._cache_ttl:
            return cached_entry['data']
        
        # Cargar de DB si no está en cache
        task = self.db_service.get_task(task_id)
        if task:
            self._cache[cache_key] = {
                'data': task,
                'timestamp': time.time()
            }
        
        return task
    
    def update_task_cached(self, task_id: str, updates: Dict[str, Any]):
        """Actualizar tarea y invalidar cache"""
        # Actualizar en DB
        self.db_service.update_task(task_id, updates)
        
        # Invalidar cache
        cache_key = f"task_{task_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        # Invalidar LRU cache
        self.get_task_cached.cache_clear()
```

**Optimizar queries MongoDB**:
```python
# database.py - Queries optimizadas
class DatabaseService:
    def __init__(self):
        self.tasks_collection = db.tasks
        # Crear índices para performance
        self.tasks_collection.create_index([("id", 1)])
        self.tasks_collection.create_index([("status", 1)])
        self.tasks_collection.create_index([("created_at", -1)])
    
    def get_tasks_paginated(self, page: int = 1, limit: int = 20, 
                           status: str = None) -> Dict[str, Any]:
        """Obtener tareas con paginación"""
        skip = (page - 1) * limit
        
        query = {}
        if status:
            query['status'] = status
        
        # Usar projection para limitar datos
        projection = {
            'id': 1, 'title': 1, 'status': 1, 'progress': 1, 
            'created_at': 1, 'updated_at': 1
        }
        
        tasks = list(self.tasks_collection
                    .find(query, projection)
                    .sort('created_at', -1)
                    .skip(skip)
                    .limit(limit))
        
        total = self.tasks_collection.count_documents(query)
        
        return {
            'tasks': tasks,
            'total': total,
            'page': page,
            'limit': limit,
            'has_more': skip + limit < total
        }
```

### 📊 Métricas de Éxito Fase 5:
- [ ] Bundle size reducido 35%
- [ ] Time-to-interactive mejorado 50%
- [ ] Memory usage reducido 30%
- [ ] React.memo implementado en componentes críticos
- [ ] Lazy loading configurado
- [ ] Caching backend implementado

---

## FASE 6: TESTING Y DOCUMENTACIÓN 🔄

### 🎯 Objetivo: Cobertura de tests comprehensiva y documentación

#### 6.1 Setup Testing Framework (Estimado: 4 horas)
**Configurar Jest + Testing Library**:
```json
// package.json - Testing setup
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --watchAll=false"
  },
  "devDependencies": {
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/user-event": "^14.4.3",
    "jest": "^29.3.1",
    "jest-environment-jsdom": "^29.3.1"
  }
}
```

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

#### 6.2 Implementar Unit Tests (Estimado: 8 hours)
**Context API Tests**:
```typescript
// __tests__/context/AppContext.test.tsx
import { renderHook, act } from '@testing-library/react';
import { AppProvider, useAppContext } from '../../src/context/AppContext';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AppProvider>{children}</AppProvider>
);

describe('AppContext', () => {
  it('should create task successfully', async () => {
    const { result } = renderHook(() => useAppContext(), { wrapper });
    
    expect(result.current.state.tasks).toHaveLength(0);
    
    await act(async () => {
      await result.current.actions.createTask('Test task');
    });
    
    expect(result.current.state.tasks).toHaveLength(1);
    expect(result.current.state.tasks[0].title).toBe('Test task');
    expect(result.current.state.activeTaskId).toBe(result.current.state.tasks[0].id);
  });

  it('should update task correctly', () => {
    const { result } = renderHook(() => useAppContext(), { wrapper });
    
    // Create task first
    act(() => {
      result.current.actions.createTask('Test task');
    });
    
    const taskId = result.current.state.tasks[0].id;
    
    // Update task
    act(() => {
      result.current.actions.updateTask(taskId, { 
        title: 'Updated task',
        status: 'completed' 
      });
    });
    
    const updatedTask = result.current.state.tasks.find(t => t.id === taskId);
    expect(updatedTask?.title).toBe('Updated task');
    expect(updatedTask?.status).toBe('completed');
  });

  it('should delete task correctly', () => {
    const { result } = renderHook(() => useAppContext(), { wrapper });
    
    // Create task
    act(() => {
      result.current.actions.createTask('Test task');
    });
    
    const taskId = result.current.state.tasks[0].id;
    expect(result.current.state.tasks).toHaveLength(1);
    
    // Delete task
    act(() => {
      result.current.actions.deleteTask(taskId);
    });
    
    expect(result.current.state.tasks).toHaveLength(0);
    expect(result.current.state.activeTaskId).toBeNull();
  });
});
```

**Custom Hooks Tests**:
```typescript
// __tests__/hooks/useTaskManagement.test.tsx
import { renderHook, act } from '@testing-library/react';
import { useTaskManagement } from '../../src/hooks/useTaskManagement';
import { AppProvider } from '../../src/context/AppContext';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AppProvider>{children}</AppProvider>
);

// Mock fetch para APIs
global.fetch = jest.fn();

describe('useTaskManagement', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  it('should create task with message successfully', async () => {
    // Mock successful API response
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        enhanced_title: 'Enhanced Test Task',
        plan: [
          { id: 'step-1', title: 'Step 1', completed: false },
          { id: 'step-2', title: 'Step 2', completed: false }
        ]
      })
    });

    const { result } = renderHook(() => useTaskManagement(), { wrapper });
    
    let createdTask: any;
    await act(async () => {
      createdTask = await result.current.createTaskWithMessage('Test task message');
    });
    
    expect(createdTask).toBeDefined();
    expect(result.current.tasks).toHaveLength(1);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/agent/generate-plan'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: expect.stringContaining('Test task message')
      })
    );
  });

  it('should calculate task progress correctly', () => {
    const { result } = renderHook(() => useTaskManagement(), { wrapper });
    
    // Create task with plan
    act(() => {
      result.current.actions.createTask('Test task');
    });
    
    const task = result.current.tasks[0];
    
    // Update task with plan
    act(() => {
      result.current.actions.updateTask(task.id, {
        plan: [
          { id: 'step-1', title: 'Step 1', completed: true },
          { id: 'step-2', title: 'Step 2', completed: false },
          { id: 'step-3', title: 'Step 3', completed: false }
        ]
      });
    });
    
    const progress = result.current.getTaskProgress(task.id);
    expect(progress).toBe(33); // 1/3 = 33%
  });
});
```

#### 6.3 Integration Tests (Estimado: 6 horas)
**API Integration Tests**:
```typescript
// __tests__/integration/api.test.ts
import { agentAPI } from '../../src/services/api';

// Mock para tests de integración
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('Agent API Integration', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('sendMessage', () => {
    it('should send message and return response', async () => {
      const mockResponse = {
        response: 'Test response',
        tool_calls: [],
        tool_results: [],
        timestamp: new Date().toISOString()
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await agentAPI.sendMessage('Test message');
      
      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/agent/chat'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: 'Test message',
            context: {}
          })
        })
      );
    });

    it('should handle API errors gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      await expect(agentAPI.sendMessage('Test message'))
        .rejects.toThrow('HTTP error! status: 500');
    });
  });

  describe('getStatus', () => {
    it('should return agent status', async () => {
      const mockStatus = {
        status: 'healthy',
        ollama_status: 'connected',
        available_models: ['llama3.1:8b'],
        current_model: 'llama3.1:8b',
        tools_count: 15
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus
      });

      const result = await agentAPI.getStatus();
      
      expect(result).toEqual(mockStatus);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/agent/status')
      );
    });
  });
});
```

#### 6.4 Backend Tests (Estimado: 6 horas)
**Tool Registry Tests**:
```python
# tests/test_tool_registry.py
import pytest
from unittest.mock import Mock, patch
from src.tools.tool_registry import ToolRegistry
from src.tools.base_tool import BaseTool

class MockTool(BaseTool):
    def __init__(self):
        super().__init__(name="mock_tool", version="1.0.0")
    
    @property
    def description(self) -> str:
        return "Mock tool for testing"
    
    @property
    def category(self) -> str:
        return "testing"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["test_param"],
            "properties": {
                "test_param": {"type": "string"}
            }
        }
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "success": True,
            "result": f"Mock result with {parameters['test_param']}"
        }

class TestToolRegistry:
    def setup_method(self):
        self.registry = ToolRegistry(auto_discover=False)
    
    def test_register_tool_class(self):
        """Test tool class registration"""
        self.registry.register_tool_class(MockTool)
        
        assert "mock_tool" in self.registry._tool_classes
        assert MockTool == self.registry._tool_classes["mock_tool"]
    
    def test_get_tool_lazy_loading(self):
        """Test lazy loading of tools"""
        self.registry.register_tool_class(MockTool)
        
        # Tool should not be instantiated yet
        assert "mock_tool" not in self.registry._tools
        
        # Get tool triggers lazy loading
        tool = self.registry.get_tool("mock_tool")
        
        assert tool is not None
        assert isinstance(tool, MockTool)
        assert "mock_tool" in self.registry._tools
    
    def test_execute_tool(self):
        """Test tool execution through registry"""
        self.registry.register_tool_class(MockTool)
        
        result = self.registry.execute_tool("mock_tool", {
            "test_param": "test_value"
        })
        
        assert result["success"] is True
        assert "Mock result with test_value" in result["result"]
        assert result["tool"] == "mock_tool"
        assert "execution_id" in result
        assert "execution_time" in result
    
    def test_execute_nonexistent_tool(self):
        """Test execution of non-existent tool"""
        result = self.registry.execute_tool("nonexistent_tool", {})
        
        assert result["success"] is False
        assert result["error_code"] == "TOOL_NOT_FOUND"
        assert "nonexistent_tool" in result["error"]
    
    def test_validate_parameters(self):
        """Test parameter validation"""
        self.registry.register_tool_class(MockTool)
        
        # Valid parameters
        result = self.registry.validate_tool_parameters("mock_tool", {
            "test_param": "valid_value"
        })
        assert result["valid"] is True
        
        # Invalid parameters (missing required)
        result = self.registry.validate_tool_parameters("mock_tool", {})
        assert result["valid"] is False
        assert "test_param" in result["error"]
    
    def test_get_tools_by_category(self):
        """Test getting tools by category"""
        self.registry.register_tool_class(MockTool)
        
        tools = self.registry.get_tools_by_category("testing")
        assert len(tools) == 1
        assert tools[0].name == "mock_tool"
        
        # Non-existent category
        tools = self.registry.get_tools_by_category("nonexistent")
        assert len(tools) == 0
```

#### 6.5 E2E Tests (Estimado: 4 horas)
**Playwright E2E Tests**:
```typescript
// e2e/task-creation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Task Creation Flow', () => {
  test('should create task and display plan', async ({ page }) => {
    await page.goto('/');
    
    // Should show homepage
    await expect(page.getByText('Bienvenido a Mitosis')).toBeVisible();
    
    // Create new task
    const input = page.getByPlaceholder('Escribe tu tarea aquí...');
    await input.fill('Crear un análisis de mercado para productos de software');
    await input.press('Enter');
    
    // Should navigate to task view
    await expect(page.getByText('Tarea 1')).toBeVisible();
    
    // Should show plan generation
    await expect(page.getByText('Plan de Acción')).toBeVisible();
    
    // Wait for plan to be generated
    await page.waitForSelector('[data-testid="plan-step"]', { timeout: 10000 });
    
    // Should have multiple steps
    const steps = page.locator('[data-testid="plan-step"]');
    await expect(steps).toHaveCountGreaterThan(2);
    
    // Should show enhanced title
    await expect(page.getByText('Análisis de Mercado de Software')).toBeVisible();
  });

  test('should execute task steps', async ({ page }) => {
    await page.goto('/');
    
    // Create task
    const input = page.getByPlaceholder('Escribe tu tarea aquí...');
    await input.fill('Buscar información sobre inteligencia artificial');
    await input.press('Enter');
    
    // Wait for plan generation
    await page.waitForSelector('[data-testid="plan-step"]');
    
    // Click on first step execute button
    const firstStep = page.locator('[data-testid="plan-step"]').first();
    await firstStep.getByRole('button', { name: /ejecutar/i }).click();
    
    // Should show step execution
    await expect(page.getByText(/ejecutando/i)).toBeVisible();
    
    // Wait for step completion
    await page.waitForSelector('[data-testid="step-completed"]', { timeout: 30000 });
    
    // Should show completed step
    await expect(page.getByText(/completado/i)).toBeVisible();
  });

  test('should handle WebSocket connection', async ({ page }) => {
    await page.goto('/');
    
    // Check connection status
    await expect(page.getByTestId('connection-status')).toHaveText(/conectado|online/i);
    
    // Create task to test real-time updates
    const input = page.getByPlaceholder('Escribe tu tarea aquí...');
    await input.fill('Test WebSocket communication');
    await input.press('Enter');
    
    // Should receive real-time updates
    await expect(page.getByText(/iniciando/i)).toBeVisible({ timeout: 5000 });
  });
});
```

### 📊 Métricas de Éxito Fase 6:
- [ ] Jest + Testing Library configurado
- [ ] Unit tests 85% cobertura
- [ ] Integration tests implementados
- [ ] E2E tests con Playwright
- [ ] CI/CD pipeline configurado
- [ ] Documentación completa

---

## 📊 MÉTRICAS FINALES ESPERADAS

### Performance Improvements:
- **Bundle Size**: -35% (de ~2MB a ~1.3MB)
- **Time-to-Interactive**: -50% (de 4s a 2s)
- **Memory Usage**: -30% (de 150MB a 105MB)
- **WebSocket Latency**: -95% (de 2000ms a <100ms)

### Quality Improvements:
- **Code Duplication**: -90% (de ~20% a <3%)
- **Cyclomatic Complexity**: -40% (de >15 a <8 por función)
- **Test Coverage**: +85% (de 0% a 85%)
- **Error Rate**: -80% (objetivo <0.05%)

### Architecture Improvements:
- **Single Source of Truth**: Context API implementado
- **Centralized Configuration**: URLs unificadas
- **Unified Tool API**: 15+ herramientas abstraídas
- **Error Boundaries**: Crashes controlados
- **WebSocket Real**: Comunicación en tiempo real restaurada

---

## 🚀 CRONOGRAMA DE EJECUCIÓN

### Semana 1-2: Fases 1-2 (Comunicación)
- **Días 1-3**: Fase 1 completa
- **Días 4-10**: Fase 2 (WebSocket + URLs + Error Boundaries)
- **Días 11-14**: Testing y refinamiento Fase 2

### Semana 3-4: Fase 3 (Estado)
- **Días 15-22**: Context API + Migración de estado
- **Días 23-28**: Custom hooks + Estado persistente

### Semana 5-6: Fase 4 (Herramientas)
- **Días 29-35**: BaseTool + Migración herramientas
- **Días 36-42**: Tool Registry + Integración

### Semana 7-8: Fase 5 (Performance)
- **Días 43-49**: React optimizations + Bundle size
- **Días 50-56**: Backend optimization + Caching

### Semana 9-10: Fase 6 (Testing)
- **Días 57-63**: Framework setup + Unit tests
- **Días 64-70**: Integration + E2E tests

### Semana 11-12: Finalización
- **Días 71-77**: Documentación completa
- **Días 78-84**: Deployment + CI/CD

---

## ⚠️ RIESGOS Y MITIGACIONES

### Riesgos Críticos:
1. **WebSocket "server error"**: Diagnóstico y solución pueden tomar más tiempo
   - **Mitigación**: Mantener HTTP Polling como fallback
2. **Breaking changes en Context API**: Migración compleja
   - **Mitigación**: Migración gradual por componente
3. **Tool migration complexity**: 15+ herramientas
   - **Mitigación**: Una herramienta a la vez con testing

### Estrategias de Rollback:
- Backup completo disponible
- Commits atómicos por cambio
- Feature flags para nuevas funcionalidades
- Fallback mechanisms implementados

---

## 🎯 CRITERIOS DE ÉXITO

La refactorización será considerada exitosa cuando:

✅ **WebSocket funcionando** sin "server error"  
✅ **Estado centralizado** con Context API  
✅ **URLs unificadas** en 1 archivo  
✅ **Herramientas abstraídas** con API común  
✅ **Tests implementados** con 85% cobertura  
✅ **Performance mejorada** según métricas  
✅ **Funcionalidad preservada** 100%  

---

## 📝 CONCLUSIÓN

Esta estrategia de refactorización transformará Mitosis de una aplicación con deuda técnica significativa en un sistema robusto, escalable y mantenible. El enfoque incremental y las métricas claras garantizan el éxito del proceso.

**Próxima Acción**: Comenzar Fase 2 - Diagnóstico de WebSocket y creación de nueva implementación.