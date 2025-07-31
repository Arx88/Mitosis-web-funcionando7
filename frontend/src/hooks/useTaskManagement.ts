/**
 * HOOKS DE GESTIÓN DE TAREAS REFACTORIZADOS - AISLAMIENTO COMPLETO Y SIMPLIFICADO
 * Dividido en hooks específicos para mejorar mantenibilidad y rendimiento
 * Usa completamente el Context API para persistencia aislada por tarea
 */

import { useCallback } from 'react';
import { useAppContext } from '../context/AppContext';
import { API_CONFIG } from '../config/api';
import { Task, Message } from '../types';

// ========================================================================
// HOOK PRINCIPAL: OPERACIONES CRUD DE TAREAS - SIMPLIFICADO
// ========================================================================

export const useTaskManagement = () => {
  const { 
    state, 
    dispatch, 
    createTask, 
    updateTask, 
    deleteTask, 
    setActiveTask, 
    updateTaskProgress,
    addTaskMessage,
    updateTaskPlan,
    resetTaskState,
    migrateTaskState
  } = useAppContext();
  
  // ========================================================================
  // CREAR TAREA CON MENSAJE INICIAL - TOTALMENTE AISLADO
  // ========================================================================
  
  const createTaskWithMessage = useCallback(async (messageContent: string) => {
    dispatch({ type: 'SET_THINKING', payload: false });
    
    // Crear mensaje de usuario
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      content: messageContent,
      sender: 'user',
      timestamp: new Date()
    };
    
    // Crear tarea completamente aislada
    const newTask: Task = {
      id: `task-${Date.now()}`,
      title: messageContent,
      createdAt: new Date(),
      status: 'active',
      messages: [userMessage], // Mensaje incluido directamente
      terminalCommands: [],
      isFavorite: false,
      progress: 0,
      iconType: undefined
    };
    
    // ✅ USAR CONTEXT COMPLETAMENTE - El Context se encarga del aislamiento
    dispatch({ type: 'ADD_TASK', payload: newTask });
    dispatch({ type: 'SET_ACTIVE_TASK', payload: newTask.id });
    
    // Set loading state AFTER task creation but BEFORE API call
    dispatch({ type: 'SET_TASK_CREATING', payload: true });
    
    // Usar chat endpoint que incluye generación de plan
    try {
      const response = await fetch(`${API_CONFIG.backend.url}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageContent.trim(),
          task_id: newTask.id
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // CRÍTICO: Actualizar tarea con título mejorado, plan Y el task_id real del backend
        const backendTaskId = data.task_id; // ID real generado por el backend
        
        // Crear la tarea actualizada con el nuevo ID
        let updatedTask: Task = { 
          ...newTask,
          id: backendTaskId // CRÍTICO: Usar el ID real del backend
        };
        
        // Update title from enhanced_title
        if (data.enhanced_title) {
          updatedTask.title = data.enhanced_title;
        }
        
        // Update plan from response
        if (data.plan && Array.isArray(data.plan)) {
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

          // ✅ USAR CONTEXT PARA ACTUALIZAR PLAN DE FORMA AISLADA
          updateTaskPlan(backendTaskId, frontendPlan);
        }
        
        // ✅ MIGRAR ESTADO COMPLETO DE ID VIEJO A NUEVO (AISLAMIENTO COMPLETO)
        migrateTaskState(newTask.id, backendTaskId);
        
        // CRÍTICO: Usar la nueva acción para actualizar el ID y migrar todos los estados
        dispatch({ 
          type: 'UPDATE_TASK_ID', 
          payload: { 
            oldId: newTask.id, 
            newId: backendTaskId, 
            updatedTask 
          } 
        });
        
        // Auto-iniciar ejecución si hay plan
        if (data.plan && data.plan.length > 0) {
          setTimeout(async () => {
            try {
              await startTaskExecution(backendTaskId); // Usar el ID del backend
            } catch (error) {
              console.error('Error starting task execution:', error);
            }
          }, 1000);
        }
      } else {
        const errorText = await response.text();
        console.error('Backend response error:', response.status, errorText);
      }
    } catch (error) {
      console.error('Error generating plan:', error);
    }
    
    dispatch({ type: 'SET_TASK_CREATING', payload: false });
    
    return newTask;
  }, [dispatch, updateTask, updateTaskPlan, migrateTaskState]);
  
  // ========================================================================
  // INICIAR EJECUCIÓN DE TAREA
  // ========================================================================
  
  const startTaskExecution = useCallback(async (taskId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.backend.url}/api/agent/start-task-execution/${taskId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        console.log('✅ Task execution started successfully');
      }
    } catch (error) {
      console.error('❌ Error starting execution:', error);
    }
  }, []);
  
  // ========================================================================
  // SUBIR ARCHIVOS PARA UNA TAREA - CON AISLAMIENTO COMPLETO
  // ========================================================================
  
  const uploadFilesForTask = useCallback(async (files: FileList, taskId?: string) => {
    try {
      let targetTask = state.tasks.find(t => t.id === taskId);
      
      if (!targetTask) {
        // Crear nueva tarea para archivos con aislamiento completo
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
        
        // ✅ USAR CONTEXT PARA GESTIÓN AISLADA DE ARCHIVOS
        const { setTaskFiles } = useAppContext();
        setTaskFiles(targetTask.id, uploadData.files);
        
        // Crear mensajes usando el Context aislado
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
        
        // ✅ USAR CONTEXT PARA MENSAJES AISLADOS POR TAREA
        addTaskMessage(targetTask.id, userMessage);
        addTaskMessage(targetTask.id, assistantMessage);
        
        // Actualizar tarea
        updateTask((task: Task) => {
          if (task.id !== targetTask!.id) return task;
          
          return {
            ...task,
            status: 'completed',
            progress: 100
          };
        });
        
        setActiveTask(targetTask.id);
      }
    } catch (error) {
      console.error('❌ Error uploading files:', error);
    }
  }, [state.tasks, createTask, updateTask, setActiveTask, addTaskMessage]);
  
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
    closeShareModal
  };
};

// ========================================================================
// HOOK PARA GESTIÓN DE ARCHIVOS CON AISLAMIENTO COMPLETO
// ========================================================================

export const useFileManagement = () => {
  const { 
    state, 
    getTaskFiles,
    setTaskFiles
  } = useAppContext();
  
  const getFiles = useCallback((taskId: string) => {
    return getTaskFiles(taskId);
  }, [getTaskFiles]);
  
  const setFiles = useCallback((taskId: string, files: any[]) => {
    setTaskFiles(taskId, files);
  }, [setTaskFiles]);
  
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
    getFiles,
    setFiles,
    downloadFile,
    downloadAllFiles
  };
};

// ========================================================================
// HOOK PARA GESTIÓN DE TERMINAL CON AISLAMIENTO COMPLETO
// ========================================================================

export const useTerminalManagement = () => {
  const { 
    state, 
    getTerminalLogs,
    addTerminalLog,
    getTaskTerminalCommands,
    setTaskTerminalCommands,
    addTaskTerminalCommand,
    setTaskTyping,
    getTaskMonitorPages,
    setTaskMonitorPages,
    addTaskMonitorPage,
    getTaskCurrentPageIndex,
    setTaskCurrentPageIndex
  } = useAppContext();
  
  const clearLogs = useCallback((taskId: string) => {
    dispatch({ type: 'CLEAR_TERMINAL_LOGS', payload: taskId });
  }, []);
  
  const logToTerminal = useCallback((taskId: string, message: string, type: 'info' | 'success' | 'error' = 'info') => {
    addTerminalLog(taskId, message, type);
  }, [addTerminalLog]);
  
  const setTyping = useCallback((taskId: string, isTyping: boolean) => {
    setTaskTyping(taskId, isTyping);
  }, [setTaskTyping]);

  const getTerminalCommands = useCallback((taskId: string) => {
    return getTaskTerminalCommands(taskId);
  }, [getTaskTerminalCommands]);

  const setTerminalCommands = useCallback((taskId: string, commands: any[]) => {
    setTaskTerminalCommands(taskId, commands);
  }, [setTaskTerminalCommands]);

  const addTerminalCommand = useCallback((taskId: string, command: any) => {
    addTaskTerminalCommand(taskId, command);
  }, [addTaskTerminalCommand]);

  const getMonitorPages = useCallback((taskId: string) => {
    return getTaskMonitorPages(taskId);
  }, [getTaskMonitorPages]);

  const setMonitorPages = useCallback((taskId: string, pages: any[]) => {
    setTaskMonitorPages(taskId, pages);
  }, [setTaskMonitorPages]);

  const addMonitorPage = useCallback((taskId: string, page: any) => {
    addTaskMonitorPage(taskId, page);
  }, [addTaskMonitorPage]);

  const getCurrentPageIndex = useCallback((taskId: string) => {
    return getTaskCurrentPageIndex(taskId);
  }, [getTaskCurrentPageIndex]);

  const setCurrentPageIndex = useCallback((taskId: string, pageIndex: number) => {
    setTaskCurrentPageIndex(taskId, pageIndex);
  }, [setTaskCurrentPageIndex]);
  
  return {
    terminalLogs: state.terminalLogs,
    initializingTaskId: state.initializingTaskId,
    initializationLogs: state.initializationLogs,
    clearLogs,
    logToTerminal,
    setTyping,
    getTerminalLogs,
    getTerminalCommands,
    setTerminalCommands,
    addTerminalCommand,
    getMonitorPages,
    setMonitorPages,
    addMonitorPage,
    getCurrentPageIndex,
    setCurrentPageIndex
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

// ========================================================================
// HOOK PARA GESTIÓN DE MENSAJES CON AISLAMIENTO COMPLETO
// ========================================================================

export const useMessagesManagement = () => {
  const { 
    getTaskMessages,
    setTaskMessages,
    addTaskMessage,
    updateTaskMessages
  } = useAppContext();
  
  const getMessages = useCallback((taskId: string) => {
    return getTaskMessages(taskId);
  }, [getTaskMessages]);
  
  const setMessages = useCallback((taskId: string, messages: Message[]) => {
    setTaskMessages(taskId, messages);
  }, [setTaskMessages]);
  
  const addMessage = useCallback((taskId: string, message: Message) => {
    addTaskMessage(taskId, message);
  }, [addTaskMessage]);
  
  const updateMessages = useCallback((taskId: string, updater: (messages: Message[]) => Message[]) => {
    updateTaskMessages(taskId, updater);
  }, [updateTaskMessages]);
  
  return {
    getMessages,
    setMessages,
    addMessage,
    updateMessages
  };
};