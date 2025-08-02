/**
 * HOOKS DE GESTIÓN DE TAREAS REFACTORIZADOS - AISLAMIENTO COMPLETO Y SIMPLIFICADO
 * Dividido en hooks específicos para mejorar mantenibilidad y rendimiento
 * Usa completamente el Context API para persistencia aislada por tarea
 */

import { useCallback } from 'react';
import { useAppContext } from '../context/AppContext';
import { useWebSocket } from './useWebSocket';
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
  
  // ✅ WEBSOCKET HOOK - PARA UNIRSE A ROOMS INMEDIATAMENTE  
  const { joinTaskRoom } = useWebSocket();
  
  // ========================================================================
  // CREAR TAREA CON MENSAJE INICIAL - SIMPLIFICADO Y ROBUSTO
  // ========================================================================
  
  const createTaskWithMessage = useCallback(async (messageContent: string) => {
    console.log('🎯 [TASK-MANAGEMENT] Creating task with message:', messageContent);
    
    dispatch({ type: 'SET_THINKING', payload: false });
    dispatch({ type: 'SET_TASK_CREATING', payload: true });
    
    // ✅ PASO 1: CREAR TAREA LIMPIA CON ID TEMPORAL
    const tempTaskId = `temp-task-${Date.now()}`;
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      content: messageContent,
      sender: 'user',
      timestamp: new Date()
    };
    
    const newTask: Task = {
      id: tempTaskId,
      title: messageContent.slice(0, 50) + (messageContent.length > 50 ? '...' : ''),
      createdAt: new Date(),
      status: 'pending',
      messages: [userMessage],
      terminalCommands: [],
      isFavorite: false,
      progress: 0,
      iconType: undefined
    };
    
    console.log('🎯 [TASK-MANAGEMENT] Creating task with temp ID:', tempTaskId);
    
    // ✅ PASO 2: AGREGAR AL CONTEXT - SE INICIALIZA AUTOMÁTICAMENTE AISLADO
    dispatch({ type: 'ADD_TASK', payload: newTask });
    dispatch({ type: 'SET_ACTIVE_TASK', payload: tempTaskId });
    
    console.log('🎯 [TASK-MANAGEMENT] Task added to context and activated:', tempTaskId);
    console.log('🎯 [TASK-MANAGEMENT] Current tasks after add:', state.tasks.length + 1);
    
    try {
      // ✅ PASO 3: ENVIAR AL BACKEND PARA GENERAR PLAN Y TÍTULO MEJORADO
      console.log('🎯 [TASK-MANAGEMENT] Sending to backend for plan generation...');
      console.log('🎯 [TASK-MANAGEMENT] API URL:', `${API_CONFIG.backend.url}/api/agent/chat`);
      console.log('🎯 [TASK-MANAGEMENT] Request payload:', {
        message: messageContent.trim(),
        task_id: tempTaskId
      });
      
      const response = await fetch(`${API_CONFIG.backend.url}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageContent.trim(),
          task_id: tempTaskId
        })
      });
      
      console.log('🎯 [TASK-MANAGEMENT] Response received:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ [TASK-MANAGEMENT] Backend response received:', data);
        
        // ✅ PASO 4: OBTENER ID REAL DEL BACKEND
        const backendTaskId = data.task_id || tempTaskId;
        
        // ✅ PASO 5: PREPARAR TAREA ACTUALIZADA
        let updatedTask: Task = { 
          ...newTask,
          id: backendTaskId,
          title: data.enhanced_title || newTask.title,
          status: 'active'
        };
        
        // ✅ PASO 6: PROCESAR PLAN SI EXISTE
        if (data.plan && Array.isArray(data.plan)) {
          console.log('📋 [TASK-MANAGEMENT] Processing plan with', data.plan.length, 'steps');
          
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
          
          // ✅ PASO 7: ACTUALIZAR PLAN EN CONTEXT AISLADO
          updateTaskPlan(backendTaskId, frontendPlan);
        }
        
        // ✅ PASO 8: MIGRAR ESTADO COMPLETO SI ID CAMBIÓ
        if (backendTaskId !== tempTaskId) {
          console.log('🔄 [TASK-MANAGEMENT] Migrating state from', tempTaskId, 'to', backendTaskId);
          migrateTaskState(tempTaskId, backendTaskId);
          
          dispatch({ 
            type: 'UPDATE_TASK_ID', 
            payload: { 
              oldId: tempTaskId, 
              newId: backendTaskId, 
              updatedTask 
            } 
          });
          // ✅ UPDATE_TASK_ID ya actualiza activeTaskId automáticamente
          console.log('🎯 [TASK-MANAGEMENT] Task ID migrated and activated:', backendTaskId);
        } else {
          // Solo actualizar la tarea si el ID no cambió
          dispatch({ type: 'UPDATE_TASK', payload: updatedTask });
          // En este caso sí necesitamos establecer activeTaskId manualmente
          dispatch({ type: 'SET_ACTIVE_TASK', payload: backendTaskId });
          console.log('🎯 [TASK-MANAGEMENT] Task updated and activated:', backendTaskId);
        }
        
        // 🚀 CRÍTICO: UNIRSE A LA ROOM DE WEBSOCKET INMEDIATAMENTE
        console.log('🔌 [TASK-MANAGEMENT] Joining WebSocket room for real-time updates:', backendTaskId);
        joinTaskRoom(backendTaskId);
        
        // ✅ PASO 10: AUTO-INICIAR EJECUCIÓN SI HAY PLAN
        if (data.plan && data.plan.length > 0) {
          console.log('🚀 [TASK-MANAGEMENT] Auto-starting task execution...');
          setTimeout(async () => {
            try {
              await startTaskExecution(backendTaskId);
            } catch (error) {
              console.error('❌ [TASK-MANAGEMENT] Error starting execution:', error);
            }
          }, 1000);
        }
        
        console.log('✅ [TASK-MANAGEMENT] Task creation completed successfully');
        
      } else {
        const errorText = await response.text();
        console.error('❌ [TASK-MANAGEMENT] Backend error:', {
          status: response.status,
          statusText: response.statusText,
          errorText: errorText
        });
        
        // Mantener la tarea pero marcarla como fallida
        updateTask((task: Task) => {
          if (task.id !== tempTaskId) return task;
          return { ...task, status: 'failed' };
        });
      }
      
    } catch (error) {
      console.error('❌ [TASK-MANAGEMENT] Network error:', {
        error: error,
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : 'No stack trace'
      });
      
      // Mantener la tarea pero marcarla como fallida
      updateTask((task: Task) => {
        if (task.id !== tempTaskId) return task;
        return { ...task, status: 'failed' };
      });
    } finally {
      dispatch({ type: 'SET_TASK_CREATING', payload: false });
    }
    
    return newTask;
  }, [dispatch, updateTask, updateTaskPlan, migrateTaskState]);
  
  // ========================================================================
  // OPERACIONES BÁSICAS SIMPLIFICADAS
  // ========================================================================
  
  const startTaskExecution = useCallback(async (taskId: string) => {
    try {
      console.log('🚀 [TASK-MANAGEMENT] Starting execution for task:', taskId);
      
      const response = await fetch(`${API_CONFIG.backend.url}/api/agent/start-task-execution/${taskId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        console.log('✅ [TASK-MANAGEMENT] Task execution started successfully');
      } else {
        console.error('❌ [TASK-MANAGEMENT] Failed to start execution:', response.status);
      }
    } catch (error) {
      console.error('❌ [TASK-MANAGEMENT] Error starting execution:', error);
    }
  }, []);
  
  return {
    // Estado básico
    tasks: state.tasks,
    activeTaskId: state.activeTaskId,
    isTaskCreating: state.isTaskCreating,
    
    // Operaciones CRUD
    createTask,
    createTaskWithMessage,
    updateTask,
    deleteTask,
    setActiveTask,
    updateTaskProgress,
    
    // Operaciones especiales
    startTaskExecution
  };
};

// ========================================================================
// HOOK ESPECÍFICO: GESTIÓN DE ARCHIVOS - AISLAMIENTO COMPLETO
// ========================================================================

export const useFileManagement = () => {
  const { 
    state,
    getTaskFiles,
    setTaskFiles,
    addTaskMessage,
    createTask,
    updateTask,
    setActiveTask
  } = useAppContext();
  
  const uploadFilesForTask = useCallback(async (files: FileList, taskId?: string) => {
    try {
      console.log('📎 [FILE-MANAGEMENT] Uploading', files.length, 'files for task:', taskId);
      
      let targetTask = state.tasks.find(t => t.id === taskId);
      
      if (!targetTask) {
        // Crear nueva tarea para archivos con aislamiento completo
        console.log('📎 [FILE-MANAGEMENT] Creating new task for files');
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
        console.log('✅ [FILE-MANAGEMENT] Files uploaded successfully');
        
        // ✅ USAR CONTEXT PARA GESTIÓN AISLADA DE ARCHIVOS
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
        
      } else {
        console.error('❌ [FILE-MANAGEMENT] Upload failed:', response.status);
      }
    } catch (error) {
      console.error('❌ [FILE-MANAGEMENT] Error uploading files:', error);
    }
  }, [state.tasks, createTask, updateTask, setActiveTask, addTaskMessage, setTaskFiles]);
  
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
      console.error('❌ [FILE-MANAGEMENT] Error downloading file:', error);
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
      console.error('❌ [FILE-MANAGEMENT] Error downloading all files:', error);
    }
  }, []);
  
  return {
    uploadFilesForTask,
    getFiles,
    setFiles,
    downloadFile,
    downloadAllFiles
  };
};

// ========================================================================
// HOOK ESPECÍFICO: GESTIÓN DE UI Y MODALS - SIMPLIFICADO
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
// HOOK ESPECÍFICO: GESTIÓN DE TERMINAL CON AISLAMIENTO COMPLETO
// ========================================================================

export const useTerminalManagement = () => {
  const { 
    state, 
    dispatch,
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
  }, [dispatch]);
  
  const logToTerminal = useCallback((taskId: string, message: string, type: 'info' | 'success' | 'error' = 'info') => {
    console.log(`📋 [TERMINAL-MANAGEMENT] Logging to task ${taskId}:`, message, `(${type})`);
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
    console.log(`📺 [TERMINAL-MANAGEMENT] Setting ${pages.length} monitor pages for task ${taskId}`);
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
    // Estado básico
    terminalLogs: state.terminalLogs,
    initializingTaskId: state.initializingTaskId,
    initializationLogs: state.initializationLogs,
    
    // Operaciones básicas
    clearLogs,
    logToTerminal,
    setTyping,
    getTerminalLogs,
    
    // Comandos de terminal
    getTerminalCommands,
    setTerminalCommands,
    addTerminalCommand,
    
    // Monitor pages
    getMonitorPages,
    setMonitorPages,
    addMonitorPage,
    getCurrentPageIndex,
    setCurrentPageIndex
  };
};

// ========================================================================
// HOOK ESPECÍFICO: GESTIÓN DE MENSAJES CON AISLAMIENTO COMPLETO
// ========================================================================

export const useMessagesManagement = () => {
  const { 
    getTaskMessages,
    setTaskMessages,
    addTaskMessage,
    updateTaskMessages
  } = useAppContext();
  
  const getMessages = useCallback((taskId: string) => {
    const messages = getTaskMessages(taskId);
    console.log(`💬 [MESSAGE-MANAGEMENT] Getting ${messages.length} messages for task ${taskId}`);
    return messages;
  }, [getTaskMessages]);
  
  const setMessages = useCallback((taskId: string, messages: Message[]) => {
    console.log(`💬 [MESSAGE-MANAGEMENT] Setting ${messages.length} messages for task ${taskId}`);
    setTaskMessages(taskId, messages);
  }, [setTaskMessages]);
  
  const addMessage = useCallback((taskId: string, message: Message) => {
    console.log(`💬 [MESSAGE-MANAGEMENT] Adding message to task ${taskId}:`, message.content.slice(0, 50) + '...');
    addTaskMessage(taskId, message);
  }, [addTaskMessage]);
  
  const updateMessages = useCallback((taskId: string, updater: (messages: Message[]) => Message[]) => {
    console.log(`💬 [MESSAGE-MANAGEMENT] Updating messages for task ${taskId}`);
    updateTaskMessages(taskId, updater);
  }, [updateTaskMessages]);
  
  return {
    getMessages,
    setMessages,
    addMessage,
    updateMessages
  };
};

// ========================================================================
// HOOK ESPECÍFICO: GESTIÓN DE CONFIGURACIÓN - SIMPLIFICADO
// ========================================================================

export const useConfigManagement = () => {
  const { state, dispatch } = useAppContext();
  
  const updateConfig = useCallback((newConfig: any) => {
    console.log('⚙️ [CONFIG-MANAGEMENT] Updating configuration');
    dispatch({ type: 'SET_CONFIG', payload: newConfig });
  }, [dispatch]);
  
  return {
    config: state.config,
    updateConfig
  };
};