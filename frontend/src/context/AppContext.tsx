/**
 * Context API Global - Consolidación de Estado 
 * FASE 3: Elimina estado duplicado y race conditions
 * Single source of truth para toda la aplicación
 */

import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';
import { Task, Message, AgentConfig, AppState } from '../types';

// ========================================================================
// TIPOS PARA EL CONTEXTO GLOBAL
// ========================================================================

interface GlobalAppState {
  // Estado de tareas consolidado
  tasks: Task[];
  activeTaskId: string | null;
  
  // Estado de UI consolidado
  sidebarCollapsed: boolean;
  terminalSize: number;
  isThinking: boolean;
  isTaskCreating: boolean;
  showFileUpload: boolean;
  isConfigOpen: boolean;
  
  // Estado de configuración
  config: AgentConfig;
  
  // Estado de archivos consolidado
  taskFiles: Record<string, any[]>; // taskId -> files[]
  
  // Estado de logs de terminal consolidado
  terminalLogs: Record<string, Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>>;
  
  // Estado de inicialización
  initializingTaskId: string | null;
  initializationLogs: Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>;
  
  // Estado de modals
  showFilesModal: boolean;
  showShareModal: boolean;
  
  // Estado de typing
  typingState: Record<string, boolean>; // taskId -> isTyping
}

// Acciones del reducer
type AppAction = 
  | { type: 'SET_TASKS'; payload: Task[] }
  | { type: 'ADD_TASK'; payload: Task }
  | { type: 'UPDATE_TASK'; payload: Task }
  | { type: 'UPDATE_TASK_FUNCTIONAL'; payload: (task: Task) => Task }
  | { type: 'DELETE_TASK'; payload: string }
  | { type: 'SET_ACTIVE_TASK'; payload: string | null }
  | { type: 'TOGGLE_SIDEBAR'; payload?: boolean }
  | { type: 'SET_TERMINAL_SIZE'; payload: number }
  | { type: 'SET_THINKING'; payload: boolean }
  | { type: 'SET_TASK_CREATING'; payload: boolean }
  | { type: 'SET_CONFIG'; payload: AgentConfig }
  | { type: 'SET_TASK_FILES'; payload: { taskId: string; files: any[] } }
  | { type: 'ADD_TERMINAL_LOG'; payload: { taskId: string; log: {message: string, type: 'info' | 'success' | 'error', timestamp: Date} } }
  | { type: 'CLEAR_TERMINAL_LOGS'; payload: string }
  | { type: 'SET_INITIALIZATION'; payload: { taskId: string | null; logs?: Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}> } }
  | { type: 'SET_MODALS'; payload: { filesModal?: boolean; shareModal?: boolean } }
  | { type: 'SET_TYPING'; payload: { taskId: string; isTyping: boolean } }
  | { type: 'RESET_TASK_STATE'; payload: string };

// ========================================================================
// CONFIGURACIÓN INICIAL
// ========================================================================

const defaultConfig: AgentConfig = {
  systemPrompt: `Eres un agente general altamente inteligente y útil. Tu objetivo es ayudar a los usuarios a completar sus tareas de manera eficiente y precisa.

Características:
- Analiza cuidadosamente cada solicitud
- Planifica los pasos necesarios para resolver la tarea
- Utiliza las herramientas disponibles cuando sea necesario
- Proporciona respuestas claras y detalladas
- Mantén un tono profesional pero amigable

Herramientas disponibles:
- Shell: Para ejecutar comandos del sistema
- Web Search: Para buscar información en internet
- File Manager: Para gestionar archivos y directorios

Siempre explica lo que estás haciendo y por qué, para que el usuario pueda entender tu proceso de pensamiento.`,
  memory: {
    enabled: true,
    maxMessages: 20,
    contextWindow: 4096
  },
  ollama: {
    enabled: true,
    model: "llama3.1:8b",
    temperature: 0.7,
    maxTokens: 2048,
    endpoint: "https://bef4a4bb93d1.ngrok-free.app"
  },
  openrouter: {
    enabled: false,
    model: "openai/gpt-4o-mini",
    apiKey: "",
    temperature: 0.7,
    maxTokens: 2048,
    endpoint: "https://openrouter.ai/api/v1"
  },
  tools: {
    shell: {
      enabled: true,
      allowedCommands: ["ls", "pwd", "cat", "grep", "find", "curl"],
      timeout: 30
    },
    webSearch: {
      enabled: true,
      maxResults: 5,
      timeout: 15
    },
    fileManager: {
      enabled: true,
      allowedPaths: ["/tmp", "/home", "/var/log"],
      maxFileSize: 10
    }
  }
};

const initialState: GlobalAppState = {
  tasks: [],
  activeTaskId: null,
  sidebarCollapsed: false,
  terminalSize: 300,
  isThinking: false,
  isTaskCreating: false,
  showFileUpload: false,
  isConfigOpen: false,
  config: defaultConfig,
  taskFiles: {},
  terminalLogs: {},
  initializingTaskId: null,
  initializationLogs: [],
  showFilesModal: false,
  showShareModal: false,
  typingState: {}
};

// ========================================================================
// REDUCER - LÓGICA DE ESTADO CONSOLIDADA
// ========================================================================

function appReducer(state: GlobalAppState, action: AppAction): GlobalAppState {
  console.log('🔄 AppContext Reducer:', action.type, action.payload);
  
  switch (action.type) {
    case 'SET_TASKS':
      return {
        ...state,
        tasks: action.payload
      };
      
    case 'ADD_TASK':
      return {
        ...state,
        tasks: [action.payload, ...state.tasks]
      };
      
    case 'UPDATE_TASK':
      return {
        ...state,
        tasks: state.tasks.map(task => 
          task.id === action.payload.id ? action.payload : task
        )
      };
      
    case 'UPDATE_TASK_FUNCTIONAL':
      return {
        ...state,
        tasks: state.tasks.map(task => {
          try {
            const updatedTask = action.payload(task);
            if (updatedTask !== task) {
              console.log('🚀 CONTEXT FUNCTIONAL UPDATE:', {
                taskId: task.id,
                oldTitle: task.title,
                newTitle: updatedTask.title,
                oldMessagesCount: task.messages?.length || 0,
                newMessagesCount: updatedTask.messages?.length || 0
              });
            }
            return updatedTask;
          } catch (error) {
            console.error('❌ Error in functional update:', error);
            return task;
          }
        })
      };
      
    case 'DELETE_TASK':
      const newTasks = state.tasks.filter(task => task.id !== action.payload);
      const newActiveTaskId = state.activeTaskId === action.payload 
        ? (newTasks.length > 0 ? newTasks[0].id : null)
        : state.activeTaskId;
        
      return {
        ...state,
        tasks: newTasks,
        activeTaskId: newActiveTaskId,
        // Limpiar estado relacionado con la tarea eliminada
        taskFiles: Object.fromEntries(
          Object.entries(state.taskFiles).filter(([taskId]) => taskId !== action.payload)
        ),
        terminalLogs: Object.fromEntries(
          Object.entries(state.terminalLogs).filter(([taskId]) => taskId !== action.payload)
        ),
        typingState: Object.fromEntries(
          Object.entries(state.typingState).filter(([taskId]) => taskId !== action.payload)
        )
      };
      
    case 'SET_ACTIVE_TASK':
      return {
        ...state,
        activeTaskId: action.payload
      };
      
    case 'TOGGLE_SIDEBAR':
      return {
        ...state,
        sidebarCollapsed: action.payload !== undefined ? action.payload : !state.sidebarCollapsed
      };
      
    case 'SET_TERMINAL_SIZE':
      return {
        ...state,
        terminalSize: action.payload
      };
      
    case 'SET_THINKING':
      return {
        ...state,
        isThinking: action.payload
      };
      
    case 'SET_TASK_CREATING':
      return {
        ...state,
        isTaskCreating: action.payload
      };
      
    case 'SET_CONFIG':
      return {
        ...state,
        config: action.payload
      };
      
    case 'SET_TASK_FILES':
      return {
        ...state,
        taskFiles: {
          ...state.taskFiles,
          [action.payload.taskId]: action.payload.files
        }
      };
      
    case 'ADD_TERMINAL_LOG':
      const currentLogs = state.terminalLogs[action.payload.taskId] || [];
      return {
        ...state,
        terminalLogs: {
          ...state.terminalLogs,
          [action.payload.taskId]: [...currentLogs, action.payload.log]
        }
      };
      
    case 'CLEAR_TERMINAL_LOGS':
      return {
        ...state,
        terminalLogs: {
          ...state.terminalLogs,
          [action.payload]: []
        }
      };
      
    case 'SET_INITIALIZATION':
      return {
        ...state,
        initializingTaskId: action.payload.taskId,
        initializationLogs: action.payload.logs || state.initializationLogs
      };
      
    case 'SET_MODALS':
      return {
        ...state,
        showFilesModal: action.payload.filesModal !== undefined ? action.payload.filesModal : state.showFilesModal,
        showShareModal: action.payload.shareModal !== undefined ? action.payload.shareModal : state.showShareModal
      };
      
    case 'SET_TYPING':
      return {
        ...state,
        typingState: {
          ...state.typingState,
          [action.payload.taskId]: action.payload.isTyping
        }
      };
      
    case 'RESET_TASK_STATE':
      return {
        ...state,
        terminalLogs: {
          ...state.terminalLogs,
          [action.payload]: []
        },
        taskFiles: {
          ...state.taskFiles,
          [action.payload]: []
        },
        typingState: {
          ...state.typingState,
          [action.payload]: false
        }
      };
      
    default:
      return state;
  }
}

// ========================================================================
// CONTEXT Y PROVIDER
// ========================================================================

interface AppContextType {
  state: GlobalAppState;
  dispatch: React.Dispatch<AppAction>;
  
  // Helper functions para operaciones comunes
  createTask: (title: string, iconType?: string) => Task;
  updateTask: (task: Task | ((currentTask: Task) => Task)) => void;
  deleteTask: (taskId: string) => void;
  setActiveTask: (taskId: string | null) => void;
  addTerminalLog: (taskId: string, message: string, type: 'info' | 'success' | 'error') => void;
  updateTaskProgress: (taskId: string) => void;
  
  // Getters para datos computados
  getActiveTask: () => Task | undefined;
  getTaskFiles: (taskId: string) => any[];
  getTerminalLogs: (taskId: string) => Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>;
  isTaskTyping: (taskId: string) => boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// ========================================================================
// PROVIDER COMPONENT
// ========================================================================

interface AppContextProviderProps {
  children: ReactNode;
}

export const AppContextProvider: React.FC<AppContextProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  // Helper functions
  const createTask = useCallback((title: string, iconType?: string): Task => {
    const newTask: Task = {
      id: `task-${Date.now()}`,
      title,
      createdAt: new Date(),
      status: 'pending',
      messages: [],
      terminalCommands: [],
      isFavorite: false,
      progress: 0,
      iconType
    };
    
    dispatch({ type: 'ADD_TASK', payload: newTask });
    dispatch({ type: 'SET_ACTIVE_TASK', payload: newTask.id });
    
    console.log('🆕 Context: Task created:', newTask.id);
    return newTask;
  }, []);
  
  const updateTask = useCallback((taskOrFunction: Task | ((currentTask: Task) => Task)) => {
    if (typeof taskOrFunction === 'function') {
      dispatch({ type: 'UPDATE_TASK_FUNCTIONAL', payload: taskOrFunction });
    } else {
      dispatch({ type: 'UPDATE_TASK', payload: taskOrFunction });
    }
  }, []);
  
  const deleteTask = useCallback((taskId: string) => {
    dispatch({ type: 'DELETE_TASK', payload: taskId });
  }, []);
  
  const setActiveTask = useCallback((taskId: string | null) => {
    dispatch({ type: 'SET_ACTIVE_TASK', payload: taskId });
  }, []);
  
  const addTerminalLog = useCallback((taskId: string, message: string, type: 'info' | 'success' | 'error') => {
    const log = {
      message,
      type,
      timestamp: new Date()
    };
    dispatch({ type: 'ADD_TERMINAL_LOG', payload: { taskId, log } });
  }, []);
  
  const updateTaskProgress = useCallback((taskId: string) => {
    dispatch({ 
      type: 'UPDATE_TASK_FUNCTIONAL', 
      payload: (task: Task) => {
        if (task.id !== taskId || !task.plan || task.plan.length === 0) {
          return task;
        }
        
        const completedSteps = task.plan.filter(step => step.completed).length;
        const totalSteps = task.plan.length;
        const planProgress = Math.round((completedSteps / totalSteps) * 100);
        
        let newStatus = task.status;
        if (planProgress === 100 && task.status !== 'completed') {
          newStatus = 'completed';
        } else if (planProgress > 0 && task.status === 'pending') {
          newStatus = 'in-progress';
        }
        
        return {
          ...task,
          progress: planProgress,
          status: newStatus
        };
      }
    });
  }, []);
  
  // Getters
  const getActiveTask = useCallback(() => {
    return state.tasks.find(task => task.id === state.activeTaskId);
  }, [state.tasks, state.activeTaskId]);
  
  const getTaskFiles = useCallback((taskId: string) => {
    return state.taskFiles[taskId] || [];
  }, [state.taskFiles]);
  
  const getTerminalLogs = useCallback((taskId: string) => {
    return state.terminalLogs[taskId] || [];
  }, [state.terminalLogs]);
  
  const isTaskTyping = useCallback((taskId: string) => {
    return state.typingState[taskId] || false;
  }, [state.typingState]);
  
  const contextValue: AppContextType = {
    state,
    dispatch,
    createTask,
    updateTask,
    deleteTask,
    setActiveTask,
    addTerminalLog,
    updateTaskProgress,
    getActiveTask,
    getTaskFiles,
    getTerminalLogs,
    isTaskTyping
  };
  
  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

// ========================================================================
// HOOK PERSONALIZADO
// ========================================================================

export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (context === undefined) {
    console.error('❌ useAppContext called outside of AppContextProvider');
    // Return a default context to prevent crashes during development
    return {
      state: initialState,
      dispatch: () => {},
      createTask: () => ({ id: '', title: '', createdAt: new Date(), status: 'pending', messages: [], terminalCommands: [], isFavorite: false, progress: 0 }),
      updateTask: () => {},
      deleteTask: () => {},
      setActiveTask: () => {},
      addTerminalLog: () => {},
      updateTaskProgress: () => {},
      getActiveTask: () => undefined,
      getTaskFiles: () => [],
      getTerminalLogs: () => [],
      isTaskTyping: () => false
    };
  }
  return context;
};

// Export types
export type { GlobalAppState, AppAction };