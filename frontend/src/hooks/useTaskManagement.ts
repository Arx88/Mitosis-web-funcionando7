/**
 * Custom Hooks Especializados - Fase 3
 * Hooks que usan el Context API para funcionalidades específicas
 * Eliminan props drilling y centralizan lógica de negocio
 */

import { useCallback } from 'react';
import { useAppContext } from '../context/AppContext';
import { API_CONFIG } from '../config/api';
import { Task, Message } from '../types';

// ========================================================================
// HOOK PARA GESTIÓN DE TAREAS
// ========================================================================

export const useTaskManagement = () => {
  const { state, dispatch, createTask, updateTask, deleteTask, setActiveTask, updateTaskProgress } = useAppContext();
  
  // Crear tarea con mensaje inicial (consolidado)
  const createTaskWithMessage = useCallback(async (messageContent: string) => {
    dispatch({ type: 'SET_TASK_CREATING', payload: true });
    dispatch({ type: 'SET_THINKING', payload: false });
    
    // Crear mensaje de usuario
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      content: messageContent,
      sender: 'user',
      timestamp: new Date()
    };
    
    // Crear tarea con mensaje incluido
    const newTask: Task = {
      id: `task-${Date.now()}`,
      title: messageContent,
      createdAt: new Date(),
      status: 'active',
      messages: [userMessage],
      terminalCommands: [],
      isFavorite: false,
      progress: 0,
      iconType: undefined
    };
    
    // Agregar tarea y activarla
    dispatch({ type: 'ADD_TASK', payload: newTask });
    dispatch({ type: 'SET_ACTIVE_TASK', payload: newTask.id });
    
    // Generar plan mejorado y título
    try {
      console.log('📝 Hook: Generating enhanced title and plan');
      const response = await fetch(`${API_CONFIG.backend.url}/api/agent/generate-plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_title: messageContent.trim(),
          task_id: newTask.id
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Actualizar tarea con título mejorado y plan
        updateTask((task: Task) => {
          if (task.id !== newTask.id) return task;
          
          let updatedTask = { ...task };
          
          if (data.enhanced_title) {
            updatedTask.title = data.enhanced_title;
          }
          
          if (data.plan) {
            const frontendPlan = data.plan.map((step: any) => ({
              id: step.id,
              title: step.title,
              description: step.description,
              tool: step.tool,
              status: step.status,
              estimated_time: step.estimated_time,
              completed: step.completed || false,
              active: step.active || false
            }));
            
            updatedTask = {
              ...updatedTask,
              plan: frontendPlan,
              status: 'in-progress',
              progress: 0
            };
          }
          
          return updatedTask;
        });
        
        // Auto-iniciar ejecución si hay plan
        if (data.plan && data.plan.length > 0) {
          setTimeout(async () => {
            await startTaskExecution(newTask.id);
          }, 1000);
        }
      }
    } catch (error) {
      console.error('❌ Error generating plan:', error);
    }
    
    dispatch({ type: 'SET_TASK_CREATING', payload: false });
    return newTask;
  }, [dispatch, updateTask]);
  
  // Iniciar ejecución de tarea
  const startTaskExecution = useCallback(async (taskId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.backend.url}/api/agent/start-task-execution/${taskId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        console.log('✅ Task execution started:', taskId);
      }
    } catch (error) {
      console.error('❌ Error starting execution:', error);
    }
  }, []);
  
  // Subir archivos para una tarea
  const uploadFilesForTask = useCallback(async (files: FileList, taskId?: string) => {
    try {
      let targetTask = state.tasks.find(t => t.id === taskId);
      
      if (!targetTask) {
        // Crear nueva tarea para archivos
        targetTask = createTask("Archivos adjuntos");
      }
      
      const formData = new FormData();
      formData.append('task_id', targetTask.id);
      
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      
      const response = await fetch(`${API_CONFIG.backend.url}/api/agent/upload-files`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const uploadData = await response.json();
        
        // Actualizar tarea con archivos subidos
        const filesList = uploadData.files.map((file: any) => 
          `• **${file.name}** (${Math.round(file.size / 1024)} KB)`
        ).join('\n');
        
        const userMessage: Message = {
          id: `msg-${Date.now()}`,
          content: `He adjuntado ${files.length} archivo(s):\n\n${filesList}\n\nPor favor, procesa estos archivos.`,
          sender: 'user',
          timestamp: new Date(),
          attachments: uploadData.files.map((file: any) => ({
            id: file.id,
            name: file.name,
            size: String(file.size),
            type: file.mime_type,
            url: `${API_CONFIG.backend.url}/api/agent/download/${file.id}`
          }))
        };
        
        const assistantMessage: Message = {
          id: `msg-${Date.now() + 1}`,
          content: 'file_upload_success',
          sender: 'assistant',
          timestamp: new Date(),
          attachments: uploadData.files.map((file: any) => ({
            id: file.id,
            name: file.name,
            size: String(file.size),
            type: file.mime_type,
            url: `${API_CONFIG.backend.url}/api/agent/download/${file.id}`
          })),
          status: {
            type: 'success',
            message: `${uploadData.files.length} archivo${uploadData.files.length !== 1 ? 's' : ''} listo${uploadData.files.length !== 1 ? 's' : ''} para usar`
          }
        };
        
        updateTask((task: Task) => {
          if (task.id !== targetTask!.id) return task;
          
          return {
            ...task,
            messages: [...task.messages, userMessage, assistantMessage],
            status: 'completed',
            progress: 100
          };
        });
        
        setActiveTask(targetTask.id);
        
        // Actualizar archivos de la tarea
        dispatch({ 
          type: 'SET_TASK_FILES', 
          payload: { taskId: targetTask.id, files: uploadData.files } 
        });
      }
    } catch (error) {
      console.error('❌ Error uploading files:', error);
    }
  }, [state.tasks, createTask, updateTask, setActiveTask, dispatch]);
  
  return {
    tasks: state.tasks,
    activeTaskId: state.activeTaskId,
    isTaskCreating: state.isTaskCreating,
    createTask,
    createTaskWithMessage,
    updateTask,
    deleteTask,
    setActiveTask,
    updateTaskProgress,
    startTaskExecution,
    uploadFilesForTask
  };
};

// ========================================================================
// HOOK PARA GESTIÓN DE UI Y MODALS
// ========================================================================

export const useUIState = () => {
  const { state, dispatch } = useAppContext();
  
  const toggleSidebar = useCallback((collapsed?: boolean) => {
    dispatch({ type: 'TOGGLE_SIDEBAR', payload: collapsed });
  }, [dispatch]);
  
  const setTerminalSize = useCallback((size: number) => {
    dispatch({ type: 'SET_TERMINAL_SIZE', payload: size });
  }, [dispatch]);
  
  const setThinking = useCallback((thinking: boolean) => {
    dispatch({ type: 'SET_THINKING', payload: thinking });
  }, [dispatch]);
  
  const openFilesModal = useCallback(() => {
    dispatch({ type: 'SET_MODALS', payload: { filesModal: true } });
  }, [dispatch]);
  
  const closeFilesModal = useCallback(() => {
    dispatch({ type: 'SET_MODALS', payload: { filesModal: false } });
  }, [dispatch]);
  
  const openShareModal = useCallback(() => {
    dispatch({ type: 'SET_MODALS', payload: { shareModal: true } });
  }, [dispatch]);
  
  const closeShareModal = useCallback(() => {
    dispatch({ type: 'SET_MODALS', payload: { shareModal: false } });
  }, [dispatch]);
  
  const openConfigPanel = useCallback(() => {
    dispatch({ type: 'SET_CONFIG', payload: state.config }); // Trigger config open
  }, [dispatch, state.config]);
  
  return {
    sidebarCollapsed: state.sidebarCollapsed,
    terminalSize: state.terminalSize,
    isThinking: state.isThinking,
    showFilesModal: state.showFilesModal,
    showShareModal: state.showShareModal,
    isConfigOpen: state.isConfigOpen,
    toggleSidebar,
    setTerminalSize,
    setThinking,
    openFilesModal,
    closeFilesModal,
    openShareModal,
    closeShareModal,
    openConfigPanel
  };
};

// ========================================================================
// HOOK PARA GESTIÓN DE ARCHIVOS
// ========================================================================

export const useFileManagement = () => {
  const { state, dispatch, getTaskFiles } = useAppContext();
  
  const setTaskFiles = useCallback((taskId: string, files: any[]) => {
    dispatch({ type: 'SET_TASK_FILES', payload: { taskId, files } });
  }, [dispatch]);
  
  const getFiles = useCallback((taskId: string) => {
    return getTaskFiles(taskId);
  }, [getTaskFiles]);
  
  const downloadFile = useCallback(async (fileId: string, fileName: string) => {
    try {
      const response = await fetch(`${API_CONFIG.backend.url}/api/agent/download/${fileId}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('❌ Error downloading file:', error);
    }
  }, []);
  
  const downloadAllFiles = useCallback(async (taskId: string, taskTitle: string) => {
    try {
      const response = await fetch(`${API_CONFIG.backend.url}/api/agent/download-all-files/${taskId}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${taskTitle}-files.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('❌ Error downloading all files:', error);
    }
  }, []);
  
  return {
    taskFiles: state.taskFiles,
    setTaskFiles,
    getFiles,
    downloadFile,
    downloadAllFiles
  };
};

// ========================================================================
// HOOK PARA GESTIÓN DE TERMINAL
// ========================================================================

export const useTerminalManagement = () => {
  const { state, dispatch, addTerminalLog, getTerminalLogs } = useAppContext();
  
  const clearLogs = useCallback((taskId: string) => {
    dispatch({ type: 'CLEAR_TERMINAL_LOGS', payload: taskId });
  }, [dispatch]);
  
  const logToTerminal = useCallback((taskId: string, message: string, type: 'info' | 'success' | 'error' = 'info') => {
    addTerminalLog(taskId, message, type);
  }, [addTerminalLog]);
  
  const setTyping = useCallback((taskId: string, isTyping: boolean) => {
    dispatch({ type: 'SET_TYPING', payload: { taskId, isTyping } });
  }, [dispatch]);
  
  return {
    terminalLogs: state.terminalLogs,
    initializingTaskId: state.initializingTaskId,
    initializationLogs: state.initializationLogs,
    typingState: state.typingState,
    clearLogs,
    logToTerminal,
    setTyping,
    getTerminalLogs
  };
};

// ========================================================================
// HOOK PARA GESTIÓN DE CONFIGURACIÓN
// ========================================================================

export const useConfigManagement = () => {
  const { state, dispatch } = useAppContext();
  
  const updateConfig = useCallback((newConfig: any) => {
    dispatch({ type: 'SET_CONFIG', payload: newConfig });
  }, [dispatch]);
  
  return {
    config: state.config,
    updateConfig
  };
};