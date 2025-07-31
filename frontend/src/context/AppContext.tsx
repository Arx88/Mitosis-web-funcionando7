/**
 * Context API Global - REFACTORIZADO PARA AISLAMIENTO COMPLETO DE TAREAS
 * FASE FINAL: Sistema robusto de aislamiento donde cada tarea mantiene su estado independiente
 * Single source of truth con gestión avanzada de persistencia por tarea
 */

import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';
import { Task, Message, AgentConfig, TaskStep } from '../types';

// ========================================================================
// TIPOS EXPANDIDOS PARA AISLAMIENTO COMPLETO
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
  
  // ========================================================================
  // AISLAMIENTO COMPLETO POR TAREA - NUEVAS ESTRUCTURAS
  // ========================================================================
  
  // Archivos por tarea (ya existía, mejorado)
  taskFiles: Record<string, any[]>; // taskId -> files[]
  
  // Terminal logs por tarea (ya existía, mejorado)
  terminalLogs: Record<string, Array<{
    message: string;
    type: 'info' | 'success' | 'error';
    timestamp: Date;
    taskId: string;
  }>>;
  
  // Chat messages por tarea (NUEVO - aislamiento de chat)
  taskMessages: Record<string, Message[]>; // taskId -> messages[]
  
  // Plan states por tarea (NUEVO - aislamiento de plan)
  taskPlanStates: Record<string, {
    plan: TaskStep[];
    currentActiveStep: TaskStep | null;
    progress: number;
    lastUpdateTime: Date;
    isCompleted: boolean;
  }>;
  
  // Terminal commands por tarea (NUEVO - aislamiento de comandos)
  taskTerminalCommands: Record<string, Array<{
    id: string;
    command: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    output?: string;
    timestamp: Date;
  }>>;
  
  // WebSocket connection states por tarea (NUEVO)
  taskWebSocketStates: Record<string, {
    isConnected: boolean;
    joinedRoom: boolean;
    lastEvent: Date | null;
  }>;
  
  // Estado de typing por tarea (ya existía, mejorado)
  typingState: Record<string, boolean>; // taskId -> isTyping
  
  // Monitor pages por tarea (NUEVO - aislamiento de terminal view)
  taskMonitorPages: Record<string, Array<{
    id: string;
    title: string;
    content: string;  
    type: 'plan' | 'tool-execution' | 'report' | 'file' | 'error';
    timestamp: Date;
    toolName?: string;
    metadata?: any;
  }>>;
  
  // Current page index por tarea (NUEVO)
  taskCurrentPageIndex: Record<string, number>;
  
  // Estado de inicialización
  initializingTaskId: string | null;
  initializationLogs: Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>;
  
  // Estado de modals
  showFilesModal: boolean;
  showShareModal: boolean;
}

// Acciones expandidas del reducer
type AppAction = 
  | { type: 'SET_TASKS'; payload: Task[] }
  | { type: 'ADD_TASK'; payload: Task }
  | { type: 'UPDATE_TASK'; payload: Task }
  | { type: 'UPDATE_TASK_FUNCTIONAL'; payload: (task: Task) => Task }
  | { type: 'UPDATE_TASK_ID'; payload: { oldId: string; newId: string; updatedTask: Task } }
  | { type: 'DELETE_TASK'; payload: string }
  | { type: 'SET_ACTIVE_TASK'; payload: string | null }
  | { type: 'TOGGLE_SIDEBAR'; payload?: boolean }
  | { type: 'SET_TERMINAL_SIZE'; payload: number }
  | { type: 'SET_THINKING'; payload: boolean }
  | { type: 'SET_TASK_CREATING'; payload: boolean }
  | { type: 'SET_CONFIG'; payload: AgentConfig }
  
  // ========================================================================
  // ACCIONES PARA AISLAMIENTO COMPLETO POR TAREA
  // ========================================================================
  
  | { type: 'SET_TASK_FILES'; payload: { taskId: string; files: any[] } }
  | { type: 'ADD_TERMINAL_LOG'; payload: { taskId: string; log: {message: string, type: 'info' | 'success' | 'error', timestamp: Date} } }
  | { type: 'CLEAR_TERMINAL_LOGS'; payload: string }
  | { type: 'SET_TASK_MESSAGES'; payload: { taskId: string; messages: Message[] } }
  | { type: 'ADD_TASK_MESSAGE'; payload: { taskId: string; message: Message } }
  | { type: 'UPDATE_TASK_MESSAGES'; payload: { taskId: string; updater: (messages: Message[]) => Message[] } }
  | { type: 'SET_TASK_PLAN_STATE'; payload: { taskId: string; planState: any } }
  | { type: 'UPDATE_TASK_PLAN'; payload: { taskId: string; plan: TaskStep[] } }
  | { type: 'SET_TASK_TERMINAL_COMMANDS'; payload: { taskId: string; commands: any[] } }
  | { type: 'ADD_TASK_TERMINAL_COMMAND'; payload: { taskId: string; command: any } }
  | { type: 'SET_TASK_WEBSOCKET_STATE'; payload: { taskId: string; state: any } }
  | { type: 'SET_TASK_MONITOR_PAGES'; payload: { taskId: string; pages: any[] } }
  | { type: 'ADD_TASK_MONITOR_PAGE'; payload: { taskId: string; page: any } }
  | { type: 'SET_TASK_CURRENT_PAGE'; payload: { taskId: string; pageIndex: number } }
  | { type: 'RESET_TASK_STATE'; payload: string }
  | { type: 'MIGRATE_TASK_STATE'; payload: { oldId: string; newId: string } }
  | { type: 'INITIALIZE_TASK_DATA'; payload: { taskId: string } }
  
  | { type: 'SET_INITIALIZATION'; payload: { taskId: string | null; logs?: Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}> } }
  | { type: 'SET_MODALS'; payload: { filesModal?: boolean; shareModal?: boolean } }
  | { type: 'SET_TYPING'; payload: { taskId: string; isTyping: boolean } };

// ========================================================================
// CONFIGURACIÓN INICIAL MEJORADA
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
  
  // ========================================================================
  // AISLAMIENTO COMPLETO INICIALIZADO
  // ========================================================================
  taskFiles: {},
  terminalLogs: {},
  taskMessages: {},
  taskPlanStates: {},
  taskTerminalCommands: {},
  taskWebSocketStates: {},
  taskMonitorPages: {},
  taskCurrentPageIndex: {},
  typingState: {},
  
  initializingTaskId: null,
  initializationLogs: [],
  showFilesModal: false,
  showShareModal: false
};

// ========================================================================
// REDUCER EXPANDIDO - LÓGICA DE AISLAMIENTO COMPLETO
// ========================================================================

function appReducer(state: GlobalAppState, action: AppAction): GlobalAppState {
  switch (action.type) {
    case 'SET_TASKS':
      return {
        ...state,
        tasks: action.payload
      };
      
    case 'ADD_TASK':
      const newTask = action.payload;
      
      // ✅ GARANTIZAR INICIALIZACIÓN COMPLETA DE DATOS AISLADOS
      console.log('🎯 [CONTEXT] ADD_TASK: Initializing isolated data for task:', newTask.id);
      
      return {
        ...state,
        tasks: [newTask, ...state.tasks],
        
        // ✅ INICIALIZAR ESTADO AISLADO COMPLETO PARA NUEVA TAREA
        taskMessages: { 
          ...state.taskMessages, 
          [newTask.id]: newTask.messages || [] 
        },
        taskFiles: { 
          ...state.taskFiles, 
          [newTask.id]: [] 
        },
        terminalLogs: { 
          ...state.terminalLogs, 
          [newTask.id]: [] 
        },
        taskPlanStates: { 
          ...state.taskPlanStates, 
          [newTask.id]: {
            plan: newTask.plan || [],
            currentActiveStep: null,
            progress: 0,
            lastUpdateTime: new Date(),
            isCompleted: false
          }
        },
        taskTerminalCommands: { 
          ...state.taskTerminalCommands, 
          [newTask.id]: newTask.terminalCommands || [] 
        },
        taskWebSocketStates: { 
          ...state.taskWebSocketStates, 
          [newTask.id]: { isConnected: false, joinedRoom: false, lastEvent: null }
        },
        taskMonitorPages: { 
          ...state.taskMonitorPages, 
          [newTask.id]: [] 
        },
        taskCurrentPageIndex: { 
          ...state.taskCurrentPageIndex, 
          [newTask.id]: 0 
        },
        typingState: { 
          ...state.typingState, 
          [newTask.id]: false 
        }
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
            if (!action.payload || typeof action.payload !== 'function') {
              console.error('❌ UPDATE_TASK_FUNCTIONAL payload is not a valid function');
              return task;
            }
            
            const updatedTask = action.payload(task);
            
            if (!updatedTask || typeof updatedTask !== 'object' || !updatedTask.id) {
              console.error('❌ UPDATE_TASK_FUNCTIONAL returned invalid task');
              return task;
            }
            
            return updatedTask;
          } catch (error) {
            console.error('❌ Error in functional update:', error);
            return task;
          }
        })
      };
      
    case 'UPDATE_TASK_ID':
      const { oldId, newId, updatedTask } = action.payload;
      return {
        ...state,
        tasks: state.tasks.map(task => 
          task.id === oldId ? updatedTask : task
        ),
        activeTaskId: state.activeTaskId === oldId ? newId : state.activeTaskId,
        // ✅ MIGRAR TODOS LOS ESTADOS AISLADOS AL NUEVO ID
        taskFiles: {
          ...Object.fromEntries(Object.entries(state.taskFiles).filter(([taskId]) => taskId !== oldId)),
          [newId]: state.taskFiles[oldId] || []
        },
        terminalLogs: {
          ...Object.fromEntries(Object.entries(state.terminalLogs).filter(([taskId]) => taskId !== oldId)),
          [newId]: state.terminalLogs[oldId] || []
        },
        taskMessages: {
          ...Object.fromEntries(Object.entries(state.taskMessages).filter(([taskId]) => taskId !== oldId)),
          [newId]: state.taskMessages[oldId] || []
        },
        taskPlanStates: {
          ...Object.fromEntries(Object.entries(state.taskPlanStates).filter(([taskId]) => taskId !== oldId)),
          [newId]: state.taskPlanStates[oldId] || {
            plan: [], currentActiveStep: null, progress: 0, lastUpdateTime: new Date(), isCompleted: false
          }
        },
        taskTerminalCommands: {
          ...Object.fromEntries(Object.entries(state.taskTerminalCommands).filter(([taskId]) => taskId !== oldId)),
          [newId]: state.taskTerminalCommands[oldId] || []
        },
        taskWebSocketStates: {
          ...Object.fromEntries(Object.entries(state.taskWebSocketStates).filter(([taskId]) => taskId !== oldId)),
          [newId]: state.taskWebSocketStates[oldId] || { isConnected: false, joinedRoom: false, lastEvent: null }
        },
        taskMonitorPages: {
          ...Object.fromEntries(Object.entries(state.taskMonitorPages).filter(([taskId]) => taskId !== oldId)),
          [newId]: state.taskMonitorPages[oldId] || []
        },
        taskCurrentPageIndex: {
          ...Object.fromEntries(Object.entries(state.taskCurrentPageIndex).filter(([taskId]) => taskId !== oldId)),
          [newId]: state.taskCurrentPageIndex[oldId] || 0
        },
        typingState: {
          ...Object.fromEntries(Object.entries(state.typingState).filter(([taskId]) => taskId !== oldId)),
          [newId]: state.typingState[oldId] || false
        },
        initializingTaskId: state.initializingTaskId === oldId ? newId : state.initializingTaskId
      };
      
    case 'DELETE_TASK':
      const taskToDelete = action.payload;
      const newTasks = state.tasks.filter(task => task.id !== taskToDelete);
      const newActiveTaskId = state.activeTaskId === taskToDelete 
        ? (newTasks.length > 0 ? newTasks[0].id : null)
        : state.activeTaskId;
        
      return {
        ...state,
        tasks: newTasks,
        activeTaskId: newActiveTaskId,
        // ✅ LIMPIAR COMPLETAMENTE TODO EL ESTADO AISLADO DE LA TAREA ELIMINADA
        taskFiles: Object.fromEntries(Object.entries(state.taskFiles).filter(([taskId]) => taskId !== taskToDelete)),
        terminalLogs: Object.fromEntries(Object.entries(state.terminalLogs).filter(([taskId]) => taskId !== taskToDelete)),
        taskMessages: Object.fromEntries(Object.entries(state.taskMessages).filter(([taskId]) => taskId !== taskToDelete)),
        taskPlanStates: Object.fromEntries(Object.entries(state.taskPlanStates).filter(([taskId]) => taskId !== taskToDelete)),
        taskTerminalCommands: Object.fromEntries(Object.entries(state.taskTerminalCommands).filter(([taskId]) => taskId !== taskToDelete)),
        taskWebSocketStates: Object.fromEntries(Object.entries(state.taskWebSocketStates).filter(([taskId]) => taskId !== taskToDelete)),
        taskMonitorPages: Object.fromEntries(Object.entries(state.taskMonitorPages).filter(([taskId]) => taskId !== taskToDelete)),
        taskCurrentPageIndex: Object.fromEntries(Object.entries(state.taskCurrentPageIndex).filter(([taskId]) => taskId !== taskToDelete)),
        typingState: Object.fromEntries(Object.entries(state.typingState).filter(([taskId]) => taskId !== taskToDelete))
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

    // ========================================================================
    // ACCIONES PARA AISLAMIENTO COMPLETO POR TAREA
    // ========================================================================
      
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
          [action.payload.taskId]: [...currentLogs, { ...action.payload.log, taskId: action.payload.taskId }]
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

    case 'SET_TASK_MESSAGES':
      return {
        ...state,
        taskMessages: {
          ...state.taskMessages,
          [action.payload.taskId]: action.payload.messages
        }
      };

    case 'ADD_TASK_MESSAGE':
      const currentMessages = state.taskMessages[action.payload.taskId] || [];
      return {
        ...state,
        taskMessages: {
          ...state.taskMessages,
          [action.payload.taskId]: [...currentMessages, action.payload.message]
        }
      };

    case 'UPDATE_TASK_MESSAGES':
      const existingMessages = state.taskMessages[action.payload.taskId] || [];
      return {
        ...state,
        taskMessages: {
          ...state.taskMessages,
          [action.payload.taskId]: action.payload.updater(existingMessages)
        }
      };

    case 'SET_TASK_PLAN_STATE':
      return {
        ...state,
        taskPlanStates: {
          ...state.taskPlanStates,
          [action.payload.taskId]: action.payload.planState
        }
      };

    case 'UPDATE_TASK_PLAN':
      const currentPlanState = state.taskPlanStates[action.payload.taskId] || {
        plan: [], currentActiveStep: null, progress: 0, lastUpdateTime: new Date(), isCompleted: false
      };
      
      const completedSteps = action.payload.plan.filter(s => s.completed).length;
      const totalSteps = action.payload.plan.length;
      const progress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
      const currentActiveStep = action.payload.plan.find(s => s.active) || null;
      
      return {
        ...state,
        taskPlanStates: {
          ...state.taskPlanStates,
          [action.payload.taskId]: {
            ...currentPlanState,
            plan: action.payload.plan,
            currentActiveStep,
            progress,
            lastUpdateTime: new Date(),
            isCompleted: completedSteps === totalSteps && totalSteps > 0
          }
        }
      };

    case 'SET_TASK_TERMINAL_COMMANDS':
      return {
        ...state,
        taskTerminalCommands: {
          ...state.taskTerminalCommands,
          [action.payload.taskId]: action.payload.commands
        }
      };

    case 'ADD_TASK_TERMINAL_COMMAND':
      const currentCommands = state.taskTerminalCommands[action.payload.taskId] || [];
      return {
        ...state,
        taskTerminalCommands: {
          ...state.taskTerminalCommands,
          [action.payload.taskId]: [...currentCommands, action.payload.command]
        }
      };

    case 'SET_TASK_WEBSOCKET_STATE':
      return {
        ...state,
        taskWebSocketStates: {
          ...state.taskWebSocketStates,
          [action.payload.taskId]: action.payload.state
        }
      };

    case 'SET_TASK_MONITOR_PAGES':
      return {
        ...state,
        taskMonitorPages: {
          ...state.taskMonitorPages,
          [action.payload.taskId]: action.payload.pages
        }
      };

    case 'ADD_TASK_MONITOR_PAGE':
      const currentPages = state.taskMonitorPages[action.payload.taskId] || [];
      return {
        ...state,
        taskMonitorPages: {
          ...state.taskMonitorPages,
          [action.payload.taskId]: [...currentPages, action.payload.page]
        }
      };

    case 'SET_TASK_CURRENT_PAGE':
      return {
        ...state,
        taskCurrentPageIndex: {
          ...state.taskCurrentPageIndex,
          [action.payload.taskId]: action.payload.pageIndex
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
      const taskIdToReset = action.payload;
      return {
        ...state,
        taskFiles: { ...state.taskFiles, [taskIdToReset]: [] },
        terminalLogs: { ...state.terminalLogs, [taskIdToReset]: [] },
        taskMessages: { ...state.taskMessages, [taskIdToReset]: [] },
        taskPlanStates: { 
          ...state.taskPlanStates, 
          [taskIdToReset]: {
            plan: [], currentActiveStep: null, progress: 0, lastUpdateTime: new Date(), isCompleted: false
          }
        },
        taskTerminalCommands: { ...state.taskTerminalCommands, [taskIdToReset]: [] },
        taskWebSocketStates: { 
          ...state.taskWebSocketStates, 
          [taskIdToReset]: { isConnected: false, joinedRoom: false, lastEvent: null }
        },
        taskMonitorPages: { ...state.taskMonitorPages, [taskIdToReset]: [] },
        taskCurrentPageIndex: { ...state.taskCurrentPageIndex, [taskIdToReset]: 0 },
        typingState: { ...state.typingState, [taskIdToReset]: false }
      };

    case 'MIGRATE_TASK_STATE':
      // Migra estado de una tarea ID antigua a una nueva
      const { oldId: migrateOldId, newId: migrateNewId } = action.payload;
      return {
        ...state,
        taskFiles: {
          ...Object.fromEntries(Object.entries(state.taskFiles).filter(([taskId]) => taskId !== migrateOldId)),
          [migrateNewId]: state.taskFiles[migrateOldId] || []
        },
        terminalLogs: {
          ...Object.fromEntries(Object.entries(state.terminalLogs).filter(([taskId]) => taskId !== migrateOldId)),
          [migrateNewId]: state.terminalLogs[migrateOldId] || []
        },
        taskMessages: {
          ...Object.fromEntries(Object.entries(state.taskMessages).filter(([taskId]) => taskId !== migrateOldId)),
          [migrateNewId]: state.taskMessages[migrateOldId] || []
        },
        taskPlanStates: {
          ...Object.fromEntries(Object.entries(state.taskPlanStates).filter(([taskId]) => taskId !== migrateOldId)),
          [migrateNewId]: state.taskPlanStates[migrateOldId] || {
            plan: [], currentActiveStep: null, progress: 0, lastUpdateTime: new Date(), isCompleted: false
          }
        },
        taskTerminalCommands: {
          ...Object.fromEntries(Object.entries(state.taskTerminalCommands).filter(([taskId]) => taskId !== migrateOldId)),
          [migrateNewId]: state.taskTerminalCommands[migrateOldId] || []
        },
        taskWebSocketStates: {
          ...Object.fromEntries(Object.entries(state.taskWebSocketStates).filter(([taskId]) => taskId !== migrateOldId)),
          [migrateNewId]: state.taskWebSocketStates[migrateOldId] || { isConnected: false, joinedRoom: false, lastEvent: null }
        },
        taskMonitorPages: {
          ...Object.fromEntries(Object.entries(state.taskMonitorPages).filter(([taskId]) => taskId !== migrateOldId)),
          [migrateNewId]: state.taskMonitorPages[migrateOldId] || []
        },
        taskCurrentPageIndex: {
          ...Object.fromEntries(Object.entries(state.taskCurrentPageIndex).filter(([taskId]) => taskId !== migrateOldId)),
          [migrateNewId]: state.taskCurrentPageIndex[migrateOldId] || 0
        },
        typingState: {
          ...Object.fromEntries(Object.entries(state.typingState).filter(([taskId]) => taskId !== migrateOldId)),
          [migrateNewId]: state.typingState[migrateOldId] || false
        }
      };
      
    case 'INITIALIZE_TASK_DATA':
      // ✅ GARANTIZAR QUE UNA TAREA TENGA TODOS SUS DATOS AISLADOS INICIALIZADOS
      const taskToInitialize = action.payload.taskId;
      console.log('🔧 [CONTEXT] INITIALIZE_TASK_DATA: Ensuring complete data isolation for task:', taskToInitialize);
      
      return {
        ...state,
        taskMessages: state.taskMessages[taskToInitialize] ? state.taskMessages : { 
          ...state.taskMessages, 
          [taskToInitialize]: [] 
        },
        taskFiles: state.taskFiles[taskToInitialize] ? state.taskFiles : { 
          ...state.taskFiles, 
          [taskToInitialize]: [] 
        },
        terminalLogs: state.terminalLogs[taskToInitialize] ? state.terminalLogs : { 
          ...state.terminalLogs, 
          [taskToInitialize]: [] 
        },
        taskPlanStates: state.taskPlanStates[taskToInitialize] ? state.taskPlanStates : { 
          ...state.taskPlanStates, 
          [taskToInitialize]: {
            plan: [], currentActiveStep: null, progress: 0, lastUpdateTime: new Date(), isCompleted: false
          }
        },
        taskTerminalCommands: state.taskTerminalCommands[taskToInitialize] ? state.taskTerminalCommands : { 
          ...state.taskTerminalCommands, 
          [taskToInitialize]: [] 
        },
        taskWebSocketStates: state.taskWebSocketStates[taskToInitialize] ? state.taskWebSocketStates : { 
          ...state.taskWebSocketStates, 
          [taskToInitialize]: { isConnected: false, joinedRoom: false, lastEvent: null }
        },
        taskMonitorPages: state.taskMonitorPages[taskToInitialize] ? state.taskMonitorPages : { 
          ...state.taskMonitorPages, 
          [taskToInitialize]: [] 
        },
        taskCurrentPageIndex: state.taskCurrentPageIndex[taskToInitialize] !== undefined ? state.taskCurrentPageIndex : { 
          ...state.taskCurrentPageIndex, 
          [taskToInitialize]: 0 
        },
        typingState: state.typingState[taskToInitialize] !== undefined ? state.typingState : { 
          ...state.typingState, 
          [taskToInitialize]: false 
        }
      };
      
    default:
      return state;
  }
}

// ========================================================================
// CONTEXT Y PROVIDER EXPANDIDOS
// ========================================================================

interface AppContextType {
  state: GlobalAppState;
  dispatch: React.Dispatch<AppAction>;
  
  // Helper functions para operaciones comunes
  createTask: (title: string, iconType?: string) => Task;
  updateTask: (task: Task | ((currentTask: Task) => Task)) => void;
  deleteTask: (taskId: string) => void;
  setActiveTask: (taskId: string | null) => void;
  updateTaskProgress: (taskId: string) => void;
  
  // ========================================================================
  // GETTERS EXPANDIDOS PARA AISLAMIENTO COMPLETO
  // ========================================================================
  getActiveTask: () => Task | undefined;
  getTaskFiles: (taskId: string) => any[];
  getTerminalLogs: (taskId: string) => Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date, taskId: string}>;
  getTaskMessages: (taskId: string) => Message[];
  getTaskPlanState: (taskId: string) => any;
  getTaskTerminalCommands: (taskId: string) => any[];
  getTaskWebSocketState: (taskId: string) => any;
  getTaskMonitorPages: (taskId: string) => any[];
  getTaskCurrentPageIndex: (taskId: string) => number;
  isTaskTyping: (taskId: string) => boolean;
  
  // ========================================================================
  // SETTERS EXPANDIDOS PARA AISLAMIENTO COMPLETO
  // ========================================================================
  setTaskMessages: (taskId: string, messages: Message[]) => void;
  addTaskMessage: (taskId: string, message: Message) => void;
  updateTaskMessages: (taskId: string, updater: (messages: Message[]) => Message[]) => void;
  updateTaskPlan: (taskId: string, plan: TaskStep[]) => void;
  setTaskFiles: (taskId: string, files: any[]) => void;
  addTerminalLog: (taskId: string, message: string, type: 'info' | 'success' | 'error') => void;
  setTaskTerminalCommands: (taskId: string, commands: any[]) => void;
  addTaskTerminalCommand: (taskId: string, command: any) => void;
  setTaskWebSocketState: (taskId: string, state: any) => void;
  setTaskMonitorPages: (taskId: string, pages: any[]) => void;
  addTaskMonitorPage: (taskId: string, page: any) => void;
  setTaskCurrentPageIndex: (taskId: string, pageIndex: number) => void;
  setTaskTyping: (taskId: string, isTyping: boolean) => void;
  
  // ========================================================================
  // UTILIDADES DE GESTIÓN DE ESTADO
  // ========================================================================
  resetTaskState: (taskId: string) => void;
  migrateTaskState: (oldId: string, newId: string) => void;
  initializeTaskData: (taskId: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// ========================================================================
// PROVIDER COMPONENT EXPANDIDO
// ========================================================================

interface AppContextProviderProps {
  children: ReactNode;
}

export const AppContextProvider: React.FC<AppContextProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  // Helper functions
  const createTask = useCallback((title: string, iconType?: string): Task => {
    console.log('🎯 CONTEXT: createTask called with:', { title, iconType });
    
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
    
    console.log('🎯 CONTEXT: Created task object:', newTask.id);
    console.log('🎯 CONTEXT: Dispatching ADD_TASK...');
    
    dispatch({ type: 'ADD_TASK', payload: newTask });
    dispatch({ type: 'SET_ACTIVE_TASK', payload: newTask.id });
    
    console.log('🎯 CONTEXT: Task creation completed, returning:', newTask.id);
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
  
  const updateTaskProgress = useCallback((taskId: string) => {
    dispatch({ 
      type: 'UPDATE_TASK_FUNCTIONAL', 
      payload: (task: Task) => {
        if (task.id !== taskId) return task;
        
        const planState = state.taskPlanStates[taskId];
        if (!planState || !planState.plan || planState.plan.length === 0) {
          return task;
        }
        
        const completedSteps = planState.plan.filter(step => step.completed).length;
        const totalSteps = planState.plan.length;
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
  }, [state.taskPlanStates]);
  
  // ========================================================================
  // GETTERS EXPANDIDOS
  // ========================================================================
  
  const getActiveTask = useCallback(() => {
    return state.tasks.find(task => task.id === state.activeTaskId);
  }, [state.tasks, state.activeTaskId]);
  
  const getTaskFiles = useCallback((taskId: string) => {
    return state.taskFiles[taskId] || [];
  }, [state.taskFiles]);
  
  const getTerminalLogs = useCallback((taskId: string) => {
    const logs = state.terminalLogs[taskId] || [];
    console.log(`📥 [CONTEXT-GET] getTerminalLogs(${taskId}): ${logs.length} logs`);
    return logs;
  }, [state.terminalLogs]);

  const getTaskMessages = useCallback((taskId: string) => {
    const messages = state.taskMessages[taskId] || [];
    console.log(`📥 [CONTEXT-GET] getTaskMessages(${taskId}): ${messages.length} messages`);
    return messages;
  }, [state.taskMessages]);

  const getTaskPlanState = useCallback((taskId: string) => {
    return state.taskPlanStates[taskId] || {
      plan: [], currentActiveStep: null, progress: 0, lastUpdateTime: new Date(), isCompleted: false
    };
  }, [state.taskPlanStates]);

  const getTaskTerminalCommands = useCallback((taskId: string) => {
    return state.taskTerminalCommands[taskId] || [];
  }, [state.taskTerminalCommands]);

  const getTaskWebSocketState = useCallback((taskId: string) => {
    return state.taskWebSocketStates[taskId] || { isConnected: false, joinedRoom: false, lastEvent: null };
  }, [state.taskWebSocketStates]);

  const getTaskMonitorPages = useCallback((taskId: string) => {
    const pages = state.taskMonitorPages[taskId] || [];
    console.log(`📥 [CONTEXT-GET] getTaskMonitorPages(${taskId}): ${pages.length} pages`);
    return pages;
  }, [state.taskMonitorPages]);

  const getTaskCurrentPageIndex = useCallback((taskId: string) => {
    return state.taskCurrentPageIndex[taskId] || 0;
  }, [state.taskCurrentPageIndex]);
  
  const isTaskTyping = useCallback((taskId: string) => {
    return state.typingState[taskId] || false;
  }, [state.typingState]);

  // ========================================================================
  // SETTERS EXPANDIDOS
  // ========================================================================

  const setTaskMessages = useCallback((taskId: string, messages: Message[]) => {
    console.log(`📤 [CONTEXT-SET] setTaskMessages(${taskId}): Setting ${messages.length} messages`);
    dispatch({ type: 'SET_TASK_MESSAGES', payload: { taskId, messages } });
  }, []);

  const addTaskMessage = useCallback((taskId: string, message: Message) => {
    dispatch({ type: 'ADD_TASK_MESSAGE', payload: { taskId, message } });
  }, []);

  const updateTaskMessages = useCallback((taskId: string, updater: (messages: Message[]) => Message[]) => {
    dispatch({ type: 'UPDATE_TASK_MESSAGES', payload: { taskId, updater } });
  }, []);

  const updateTaskPlan = useCallback((taskId: string, plan: TaskStep[]) => {
    dispatch({ type: 'UPDATE_TASK_PLAN', payload: { taskId, plan } });
  }, []);

  const setTaskFiles = useCallback((taskId: string, files: any[]) => {
    dispatch({ type: 'SET_TASK_FILES', payload: { taskId, files } });
  }, []);

  const addTerminalLog = useCallback((taskId: string, message: string, type: 'info' | 'success' | 'error') => {
    const log = { message, type, timestamp: new Date() };
    dispatch({ type: 'ADD_TERMINAL_LOG', payload: { taskId, log } });
  }, []);

  const setTaskTerminalCommands = useCallback((taskId: string, commands: any[]) => {
    dispatch({ type: 'SET_TASK_TERMINAL_COMMANDS', payload: { taskId, commands } });
  }, []);

  const addTaskTerminalCommand = useCallback((taskId: string, command: any) => {
    dispatch({ type: 'ADD_TASK_TERMINAL_COMMAND', payload: { taskId, command } });
  }, []);

  const setTaskWebSocketState = useCallback((taskId: string, state: any) => {
    dispatch({ type: 'SET_TASK_WEBSOCKET_STATE', payload: { taskId, state } });
  }, []);

  const setTaskMonitorPages = useCallback((taskId: string, pages: any[]) => {
    console.log(`📤 [CONTEXT-SET] setTaskMonitorPages(${taskId}): Setting ${pages.length} pages`);
    dispatch({ type: 'SET_TASK_MONITOR_PAGES', payload: { taskId, pages } });
  }, []);

  const addTaskMonitorPage = useCallback((taskId: string, page: any) => {
    dispatch({ type: 'ADD_TASK_MONITOR_PAGE', payload: { taskId, page } });
  }, []);

  const setTaskCurrentPageIndex = useCallback((taskId: string, pageIndex: number) => {
    dispatch({ type: 'SET_TASK_CURRENT_PAGE', payload: { taskId, pageIndex } });
  }, []);

  const setTaskTyping = useCallback((taskId: string, isTyping: boolean) => {
    dispatch({ type: 'SET_TYPING', payload: { taskId, isTyping } });
  }, []);

  // ========================================================================
  // UTILIDADES DE GESTIÓN DE ESTADO
  // ========================================================================

  const resetTaskState = useCallback((taskId: string) => {
    console.log('🧹 [CONTEXT] Resetting task state for:', taskId);
    dispatch({ type: 'RESET_TASK_STATE', payload: taskId });
  }, []);

  const migrateTaskState = useCallback((oldId: string, newId: string) => {
    console.log('🔄 [CONTEXT] Migrating task state from', oldId, 'to', newId);
    dispatch({ type: 'MIGRATE_TASK_STATE', payload: { oldId, newId } });
  }, []);
  
  const initializeTaskData = useCallback((taskId: string) => {
    console.log('🔧 [CONTEXT] Initializing task data for:', taskId);
    dispatch({ type: 'INITIALIZE_TASK_DATA', payload: { taskId } });
  }, []);
  
  // Crear el valor del contexto de forma memoizada para evitar re-renders
  const contextValue = React.useMemo<AppContextType>(() => {
    return {
      state,
      dispatch,
      createTask,
      updateTask,
      deleteTask,
      setActiveTask,
      updateTaskProgress,
      getActiveTask,
      getTaskFiles,
      getTerminalLogs,
      getTaskMessages,
      getTaskPlanState,
      getTaskTerminalCommands,
      getTaskWebSocketState,
      getTaskMonitorPages,
      getTaskCurrentPageIndex,
      isTaskTyping,
      setTaskMessages,
      addTaskMessage,
      updateTaskMessages,
      updateTaskPlan,
      setTaskFiles,
      addTerminalLog,
      setTaskTerminalCommands,
      addTaskTerminalCommand,
      setTaskWebSocketState,
      setTaskMonitorPages,
      addTaskMonitorPage,
      setTaskCurrentPageIndex,
      setTaskTyping,
      resetTaskState,
      migrateTaskState
    };
  }, [
    state,
    dispatch,
    createTask,
    updateTask,
    deleteTask,
    setActiveTask,
    updateTaskProgress,
    getActiveTask,
    getTaskFiles,
    getTerminalLogs,
    getTaskMessages,
    getTaskPlanState,
    getTaskTerminalCommands,
    getTaskWebSocketState,
    getTaskMonitorPages,
    getTaskCurrentPageIndex,
    isTaskTyping,
    setTaskMessages,
    addTaskMessage,
    updateTaskMessages,
    updateTaskPlan,
    setTaskFiles,
    addTerminalLog,
    setTaskTerminalCommands,
    addTaskTerminalCommand,
    setTaskWebSocketState,
    setTaskMonitorPages,
    addTaskMonitorPage,
    setTaskCurrentPageIndex,
    setTaskTyping,
    resetTaskState,
    migrateTaskState
  ]);
  
  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

// ========================================================================
// HOOK PERSONALIZADO EXPANDIDO
// ========================================================================

export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (context === undefined) {
    console.error('useAppContext must be used within an AppContextProvider');
    
    // Return a safe default context instead of throwing to prevent app crashes
    return {
      state: initialState,
      dispatch: () => console.warn('dispatch called with default context'),
      createTask: (title: string) => {
        return {
          id: `default-${Date.now()}`,
          title,
          createdAt: new Date(),
          status: 'pending',
          messages: [],
          terminalCommands: [],
          isFavorite: false,
          progress: 0
        };
      },
      updateTask: () => {},
      deleteTask: () => {},
      setActiveTask: () => {},
      updateTaskProgress: () => {},
      getActiveTask: () => undefined,
      getTaskFiles: () => [],
      getTerminalLogs: () => [],
      getTaskMessages: () => [],
      getTaskPlanState: () => ({ plan: [], currentActiveStep: null, progress: 0, lastUpdateTime: new Date(), isCompleted: false }),
      getTaskTerminalCommands: () => [],
      getTaskWebSocketState: () => ({ isConnected: false, joinedRoom: false, lastEvent: null }),
      getTaskMonitorPages: () => [],
      getTaskCurrentPageIndex: () => 0,
      isTaskTyping: () => false,
      setTaskMessages: () => {},
      addTaskMessage: () => {},
      updateTaskMessages: () => {},
      updateTaskPlan: () => {},
      setTaskFiles: () => {},
      addTerminalLog: () => {},
      setTaskTerminalCommands: () => {},
      addTaskTerminalCommand: () => {},
      setTaskWebSocketState: () => {},
      setTaskMonitorPages: () => {},
      addTaskMonitorPage: () => {},
      setTaskCurrentPageIndex: () => {},
      setTaskTyping: () => {},
      resetTaskState: () => {},
      migrateTaskState: () => {}
    };
  }
  
  return context;
};

// Export types
export type { GlobalAppState, AppAction };