import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Task, Message, TerminalCommand } from '../types';
import { TerminalView } from './TerminalView';
import { ChatInterface } from './ChatInterface';
import { ThinkingAnimation } from './ThinkingAnimation';
import { FilesModal } from './FilesModal';
import { ShareModal } from './ShareModal';
import { agentAPI, FileItem } from '../services/api';
import { useIsolatedMemoryManager } from '../hooks/useIsolatedMemoryManager';
import { usePlanManager } from '../hooks/usePlanManager';
import { useMessagesManagement, useTerminalManagement, useFileManagement } from '../hooks/useTaskManagement';
import { useAppContext } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { API_CONFIG } from '../config/api';
import { Star, Files, Share2, GripVertical } from 'lucide-react';

interface TaskViewProps {
  task: Task;
  onUpdateTask: (task: Task | ((currentTask: Task) => Task)) => void;
  onUpdateTaskProgress?: (taskId: string) => void;
  isThinking: boolean;
  onTerminalResize?: (height: number) => void;
  externalLogs?: Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>;
  isInitializing?: boolean;
  onInitializationComplete?: () => void;
  onInitializationLog?: (message: string, type: 'info' | 'success' | 'error') => void;
}

// ========================================================================
// TASKVIEW REFACTORIZADO - AISLAMIENTO COMPLETO POR TAREA
// ========================================================================

const TaskViewComponent: React.FC<TaskViewProps> = ({
  task,
  onUpdateTask,
  onUpdateTaskProgress,
  isThinking,
  externalLogs = [],
  isInitializing = false,
  onInitializationComplete,
  onInitializationLog
}) => {
  // ========================================================================
  // CONTEXT Y HOOKS AISLADOS POR TAREA
  // ========================================================================
  
  const { 
    getTaskPlanState, 
    updateTaskPlan,
    getTaskWebSocketState,
    setTaskWebSocketState
  } = useAppContext();
  
  // ✅ USAR HOOKS COMPLETAMENTE AISLADOS POR TAREA
  const { getMessages, setMessages, addMessage, updateMessages } = useMessagesManagement();
  const { 
    getTerminalLogs, 
    logToTerminal, 
    getMonitorPages, 
    setMonitorPages, 
    addMonitorPage,
    getCurrentPageIndex,
    setCurrentPageIndex 
  } = useTerminalManagement();
  const { getFiles, setFiles } = useFileManagement();

  // ========================================================================
  // ESTADO LOCAL MÍNIMO - SOLO UI, NO DATOS
  // ========================================================================
  
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  
  // ========================================================================
  // ESTADO PARA REDIMENSIONAMIENTO RESPONSIVO
  // ========================================================================
  const [chatWidthPercent, setChatWidthPercent] = useState(40); // 40% por defecto (más pequeño)
  const [isResizing, setIsResizing] = useState(false);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  
  const monitorRef = useRef<HTMLDivElement>(null);
  const resizeRef = useRef<HTMLDivElement>(null);
  
  // Detectar tamaño de ventana para responsiveness
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Lógica responsive para colapsar elementos según el espacio
  const getResponsiveLayout = () => {
    const isMobile = windowWidth < 768;
    const isTablet = windowWidth < 1024;
    const isSmallDesktop = windowWidth < 1200;
    
    if (isMobile) {
      return {
        shouldCollapseChat: true,
        shouldCollapseSidebar: true,
        minChatWidth: 300,
        maxChatWidth: windowWidth - 100,
        defaultChatWidth: windowWidth > 600 ? 35 : 30
      };
    } else if (isTablet) {
      return {
        shouldCollapseChat: false,
        shouldCollapseSidebar: windowWidth < 900,
        minChatWidth: 350,
        maxChatWidth: windowWidth * 0.7,
        defaultChatWidth: 35
      };
    } else if (isSmallDesktop) {
      return {
        shouldCollapseChat: false,
        shouldCollapseSidebar: false,
        minChatWidth: 400,
        maxChatWidth: windowWidth * 0.65,
        defaultChatWidth: 40
      };
    } else {
      return {
        shouldCollapseChat: false,
        shouldCollapseSidebar: false,
        minChatWidth: 450,
        maxChatWidth: windowWidth * 0.6,
        defaultChatWidth: 40
      };
    }
  };
  
  const responsiveLayout = getResponsiveLayout();
  
  // Memory manager aislado por tarea (conservado)
  const { hasActiveMemory, getMemoryStats } = useIsolatedMemoryManager({ taskId: task.id });

  // ========================================================================
  // WEBSOCKET SETUP PARA BROWSER_VISUAL EVENTS - CRÍTICO
  // ========================================================================
  
  const { socket, isConnected, joinTaskRoom, addEventListeners } = useWebSocket();
  
  // Configurar event listeners para browser_visual con reconexión automática
  useEffect(() => {
    console.log(`🔌 [WEBSOCKET-DEBUG] useEffect triggered:`, { 
      hasSocket: !!socket, 
      isConnected, 
      taskId: task.id 
    });
    
    if (socket && task.id) {  // No requiere isConnected para intentar conectar
      console.log(`🔌 [WEBSOCKET] Setting up browser_visual listeners for task ${task.id}`);
      
      // Join task room even if not connected yet
      joinTaskRoom(task.id);
      
      // Add browser_visual event listener  
      addEventListeners({
        browser_visual: (data) => {
          console.log(`📸 [BROWSER_VISUAL] Event received for task ${task.id}:`, data);
          
          // ✅ VALIDACIÓN: Filtrar eventos mal formados o vacíos
          if (!data || typeof data !== 'object') {
            console.log(`📸 [BROWSER_VISUAL] Invalid data received, skipping:`, data);
            return;
          }
          
          // ✅ VALIDACIÓN: Verificar que tenga datos mínimos requeridos
          if (!data.task_id && !data.url && !data.step && !data.message && !data.screenshot_url && !data.screenshot) {
            console.log(`📸 [BROWSER_VISUAL] Empty or incomplete data received, skipping:`, data);
            return;
          }
          
          // ✅ VALIDACIÓN: Verificar timestamp válido (evitar fechas como 1970)
          const eventTimestamp = data.timestamp ? new Date(data.timestamp * 1000) : new Date();
          if (eventTimestamp.getFullYear() < 2020) {
            console.log(`📸 [BROWSER_VISUAL] Invalid timestamp detected (${eventTimestamp}), using current time`);
            // Usar timestamp actual en lugar del inválido
          }
          
          if (data.task_id === task.id) {
            // ✅ VALIDACIÓN: Solo procesar si hay información útil
            const hasUsefulInfo = data.url || data.step || data.message || data.screenshot_url || data.screenshot;
            if (!hasUsefulInfo) {
              console.log(`📸 [BROWSER_VISUAL] No useful information in event, skipping`);
              return;
            }
            
            const visualMessage = `# 🌐 Navegación Web en Tiempo Real

## ${data.step || 'Navegación activa'}

**Timestamp:** ${eventTimestamp.getFullYear() > 2020 ? eventTimestamp.toLocaleTimeString() : new Date().toLocaleTimeString()}
**URL:** ${data.url || 'N/A'}

![Screenshot](${data.screenshot_url || data.screenshot || '/api/placeholder-screenshot.png'})

*${data.message || 'Captura automática de navegación browser-use'}*

---`;
            
            // Add visual message to terminal
            logToTerminal(visualMessage, 'info');
            
            // También crear una página de monitor específica
            addMonitorPage({
              id: `browser_visual_${Date.now()}`,
              title: data.step || 'Navegación Visual',
              content: visualMessage,
              timestamp: eventTimestamp.getFullYear() > 2020 ? eventTimestamp : new Date(),
              type: 'browser_visual'
            });
            
            console.log(`📸 [BROWSER_VISUAL] Valid visual message added to terminal`);
          } else {
            console.log(`📸 [BROWSER_VISUAL] Event for different task (${data.task_id}), ignoring`);
          }
        },
        
        // También escuchar browser_activity como fallback y eventos generales
        browser_activity: (data) => {
          console.log(`🌐 [BROWSER_ACTIVITY] Event received:`, data);
          if (data.task_id === task.id) {
            logToTerminal(`🌐 Browser Activity: ${data.description || 'Navigation event'}`, 'info');
          }
        },
        
        // También escuchar task_update para browser_visual events
        task_update: (data) => {
          console.log(`📋 [TASK_UPDATE] Event received:`, data);
          if (data.type === 'browser_visual' && data.data && data.data.task_id === task.id) {
            console.log(`📸 [BROWSER_VISUAL via task_update] Processing:`, data.data);
            
            const visualData = data.data;
            
            // ✅ VALIDACIÓN: Verificar que tenga datos mínimos requeridos
            if (!visualData.url && !visualData.step && !visualData.message && !visualData.screenshot_url && !visualData.screenshot) {
              console.log(`📸 [BROWSER_VISUAL via task_update] Empty or incomplete data, skipping:`, visualData);
              return;
            }
            
            // ✅ VALIDACIÓN: Verificar timestamp válido
            const eventTimestamp = visualData.timestamp ? new Date(visualData.timestamp * 1000) : new Date();
            if (eventTimestamp.getFullYear() < 2020) {
              console.log(`📸 [BROWSER_VISUAL via task_update] Invalid timestamp detected, using current time`);
            }
            
            // Procesar como browser_visual normal
            const visualMessage = `# 🌐 Navegación Web en Tiempo Real

## ${visualData.step || 'Navegación activa'}

**Timestamp:** ${eventTimestamp.getFullYear() > 2020 ? eventTimestamp.toLocaleTimeString() : new Date().toLocaleTimeString()}
**URL:** ${visualData.url || 'N/A'}

![Screenshot](${visualData.screenshot_url || visualData.screenshot || '/api/placeholder-screenshot.png'})

*${visualData.message || 'Captura automática de navegación browser-use'}*

---`;
            
            logToTerminal(visualMessage, 'info');
            
            addMonitorPage({
              id: `browser_visual_${Date.now()}`,
              title: visualData.step || 'Navegación Visual',
              content: visualMessage,
              timestamp: eventTimestamp.getFullYear() > 2020 ? eventTimestamp : new Date(),
              type: 'browser_visual'
            });
          }
        }
      });
      
      console.log(`✅ [WEBSOCKET] browser_visual listeners configured for task ${task.id}`);
      
      // RETRY CONNECTION cada 5 segundos si no está conectado
      const retryInterval = setInterval(() => {
        if (!isConnected && socket) {
          console.log(`🔄 [WEBSOCKET] Retry connection for task ${task.id}`);
          joinTaskRoom(task.id);
        } else if (isConnected) {
          clearInterval(retryInterval);
          console.log(`✅ [WEBSOCKET] Connection stable for task ${task.id}`);
        }
      }, 5000);
      
      return () => {
        clearInterval(retryInterval);
      };
    } // <-- Cerrar el if (socket && task.id)
  }, [socket, isConnected, task.id, joinTaskRoom, addEventListeners, logToTerminal, addMonitorPage]);
  
  // ========================================================================
  // PLAN MANAGER SIMPLIFICADO - USANDO CONTEXT AISLADO
  // ========================================================================

  const {
    plan,
    progress,
    isConnected: planConnected,
    currentActiveStep,
    currentActiveStepId,
    setPlan,
    lastUpdateTime,
    completeStep
  } = usePlanManager({
    taskId: task.id,
    initialPlan: task.plan || [],
    onPlanUpdate: (updatedPlan) => {
      console.log(`🔄 [TASK-${task.id}] Plan updated (ISOLATED):`, updatedPlan.length, 'steps');
      
      // ✅ USAR CONTEXT PARA PERSISTENCIA AISLADA
      updateTaskPlan(task.id, updatedPlan);
      
      // ✅ ACTUALIZAR TAREA SOLO SI HAY CAMBIOS REALES
      onUpdateTask((currentTask: Task) => {
        const currentProgress = Math.round((updatedPlan.filter(s => s.completed).length / updatedPlan.length) * 100);
        
        // No actualizar si no hay cambios reales en el progreso
        if (currentTask.progress === currentProgress && 
            currentTask.plan?.length === updatedPlan.length) {
          console.log(`🛡️ [TASK-${task.id}] Skipping unnecessary task update`);
          return currentTask;
        }
        
        return {
          ...currentTask,
          plan: updatedPlan,
          progress: currentProgress
        };
      });
    },
    onStepComplete: (stepId) => {
      console.log(`✅ [TASK-${task.id}] Step completed (ISOLATED):`, stepId);
      
      // ✅ LOG USANDO CONTEXT AISLADO
      const step = plan.find(s => s.id === stepId);
      if (step) {
        logToTerminal(task.id, `✅ Completado: ${step.title}`, 'success');
      }
      
      // Notificar progreso
      if (onUpdateTaskProgress) {
        onUpdateTaskProgress(task.id);
      }
    },
    onTaskComplete: () => {
      console.log(`🎉 [TASK-${task.id}] Task completed (ISOLATED)!`);
      
      // ✅ LOG USANDO CONTEXT AISLADO
      logToTerminal(task.id, '🎉 ¡Tarea completada exitosamente!', 'success');

      // Actualizar estado de la tarea
      onUpdateTask((currentTask: Task) => ({
        ...currentTask,
        status: 'completed',
        progress: 100
      }));
    }
  });

  // ========================================================================
  // SINCRONIZACIÓN CON DATOS AISLADOS DEL CONTEXT
  // ========================================================================

  // Obtener datos aislados de la tarea desde el Context
  const taskMessages = useMemo(() => {
    const messages = getMessages(task.id);
    console.log(`💬 [TASK-MESSAGES] Task ${task.id} has ${messages.length} messages in context`);
    return messages;
  }, [getMessages, task.id]);
  
  const taskTerminalLogs = useMemo(() => {
    const logs = getTerminalLogs(task.id);
    console.log(`📋 [TERMINAL-LOGS] Task ${task.id} has ${logs.length} terminal logs in context`);
    return logs;
  }, [getTerminalLogs, task.id]);
  
  const taskFiles = useMemo(() => {
    const files = getFiles(task.id);
    console.log(`📁 [TASK-FILES] Task ${task.id} has ${files.length} files in context`);
    return files;
  }, [getFiles, task.id]);
  
  const taskMonitorPages = useMemo(() => {
    const pages = getMonitorPages(task.id);
    console.log(`📺 [MONITOR-PAGES] Task ${task.id} has ${pages.length} monitor pages in context`);
    return pages;
  }, [getMonitorPages, task.id]);
  
  // ========================================================================
  // HANDLERS DE REDIMENSIONAMIENTO RESPONSIVO
  // ========================================================================
  
  // Handler para iniciar el redimensionamiento
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    
    const startX = e.clientX;
    const startWidth = (chatWidthPercent / 100) * windowWidth;
    
    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - startX;
      const newWidth = startWidth + deltaX;
      const newWidthPercent = Math.min(Math.max((newWidth / windowWidth) * 100, 
        (responsiveLayout.minChatWidth / windowWidth) * 100), 
        (responsiveLayout.maxChatWidth / windowWidth) * 100);
      
      setChatWidthPercent(newWidthPercent);
    };
    
    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [chatWidthPercent, windowWidth, responsiveLayout]);
  
  // Ajustar el ancho cuando cambia el tamaño de ventana
  useEffect(() => {
    if (chatWidthPercent === 40 || chatWidthPercent === 35 || chatWidthPercent === 30) {
      setChatWidthPercent(responsiveLayout.defaultChatWidth);
    }
  }, [windowWidth, responsiveLayout]);
  
  const currentPageIndex = useMemo(() => {
    const index = getCurrentPageIndex(task.id);
    console.log(`📍 [PAGE-INDEX] Task ${task.id} current page index: ${index}`);
    return index;
  }, [getCurrentPageIndex, task.id]);

  // ========================================================================
  // EFECTOS DE INICIALIZACIÓN Y RESETEO POR TAREA
  // ========================================================================

  // RESET COMPLETO cuando cambia la tarea ID - UPGRADE AI: LIMPIEZA INMEDIATA
  const lastTaskIdRef = useRef<string>('');
  useEffect(() => {
    if (task.id !== lastTaskIdRef.current) {
      console.log(`🔄 [TASKVIEW-SWITCH] ${lastTaskIdRef.current} → ${task.id}`);
      console.log(`🔄 [TASKVIEW-SWITCH] Task title: "${task.title}"`);
      console.log(`🔄 [TASKVIEW-SWITCH] Task status: ${task.status}`);
      console.log(`🔄 [TASKVIEW-SWITCH] Task messages: ${task.messages?.length || 0}`);
      console.log(`🔄 [TASKVIEW-SWITCH] Task plan: ${task.plan?.length || 0} steps`);
      
      // UPGRADE AI: LIMPIEZA INMEDIATA DEL ESTADO ANTERIOR
      console.log(`🧹 [TASKVIEW-SWITCH] CLEARING PREVIOUS TASK STATE IMMEDIATELY`);
      
      // Limpiar plan inmediatamente para evitar mostrar plan anterior
      setPlan([]);
      
      // Limpiar estado UI local
      setShowFilesModal(false);
      setShowShareModal(false);
      
      // Log estado del Context aislado
      const contextMessages = getMessages(task.id);
      const contextLogs = getTerminalLogs(task.id);
      const contextPages = getMonitorPages(task.id);
      const contextFiles = getFiles(task.id);
      
      console.log(`🔍 [CONTEXT-STATE] Task ${task.id}:`);
      console.log(`  - Messages in context: ${contextMessages.length}`);
      console.log(`  - Terminal logs in context: ${contextLogs.length}`);
      console.log(`  - Monitor pages in context: ${contextPages.length}`);
      console.log(`  - Files in context: ${contextFiles.length}`);
      
      lastTaskIdRef.current = task.id;
      
      // UPGRADE AI: ESTABLECER PLAN DE LA NUEVA TAREA INMEDIATAMENTE O MOSTRAR VACÍO
      if (task.plan && task.plan.length > 0) {
        console.log(`📋 [PLAN-INIT] Loading existing plan with ${task.plan.length} steps`);
        console.log(`📋 [PLAN-INIT] Plan details:`, task.plan.map(step => ({
          id: step.id,
          title: step.title,
          active: step.active,
          completed: step.completed,
          status: step.status
        })));
        setPlan(task.plan);
        
        console.log(`📋 [PLAN-INIT] Plan set immediately, forcing plan manager update`);
      } else {
        console.log(`📋 [PLAN-INIT] No plan found for task ${task.id}, showing empty state while checking backend...`);
        
        // UPGRADE AI: Mantener plan vacío mientras se busca en backend
        // No mostrar información de la tarea anterior
        setPlan([]);
        
        // FALLBACK: If no plan in task, try to fetch from backend
        const fetchTaskPlan = async () => {
          try {
            const response = await fetch(`${API_CONFIG.backend.url}/api/agent/get-all-tasks`);
            if (response.ok) {
              const data = await response.json();
              const backendTask = data.tasks?.find(t => t.id === task.id);
              if (backendTask?.plan && backendTask.plan.length > 0) {
                console.log(`📋 [PLAN-FALLBACK] Found plan in backend with ${backendTask.plan.length} steps`);
                setPlan(backendTask.plan);
                
                // Also update the task in context
                onUpdateTask((currentTask: Task) => ({
                  ...currentTask,
                  plan: backendTask.plan
                }));
              } else {
                console.log(`📋 [PLAN-FALLBACK] No plan found in backend for task ${task.id}`);
                // Mantener plan vacío
                setPlan([]);
              }
            }
          } catch (error) {
            console.error(`❌ [PLAN-FALLBACK] Error fetching task plan from backend:`, error);
            // En caso de error, mantener plan vacío 
            setPlan([]);
          }
        };
        
        fetchTaskPlan();
      }
      
      console.log(`✅ [TASKVIEW-SWITCH] Switch complete - data isolated, previous state cleared`);
    }
  }, [task.id, task.plan, setPlan, getMessages, getTerminalLogs, getMonitorPages, getFiles]);

  // Sincronizar mensajes con Context aislado
  useEffect(() => {
    if (task.messages && task.messages.length > 0) {
      const currentContextMessages = getMessages(task.id);
      
      console.log(`💬 [MESSAGE-SYNC] Task ${task.id}:`);
      console.log(`  - Task.messages: ${task.messages.length}`);
      console.log(`  - Context messages: ${currentContextMessages.length}`);
      
      // Solo actualizar si hay diferencias
      if (currentContextMessages.length !== task.messages.length) {
        console.log(`💬 [MESSAGE-SYNC] Syncing ${task.messages.length} messages to isolated context`);
        setMessages(task.id, task.messages);
      } else {
        console.log(`💬 [MESSAGE-SYNC] Messages already in sync`);
      }
    } else {
      console.log(`💬 [MESSAGE-SYNC] Task ${task.id} has no messages`);
    }
  }, [task.messages, task.id, getMessages, setMessages]);

  // Cargar archivos de tarea específicos (aislados)
  useEffect(() => {
    let mounted = true;
    
    const loadTaskFiles = async () => {
      try {
        console.log(`📁 [FILE-LOAD] Loading files for task ${task.id}`);
        const files = await agentAPI.getTaskFiles(task.id);
        if (mounted) {
          console.log(`📁 [FILE-LOAD] Loaded ${files.length} files, setting in context`);
          setFiles(task.id, files); // ✅ USAR CONTEXT AISLADO
          console.log(`✅ [FILE-LOAD] Files set in isolated context for task ${task.id}`);
        } else {
          console.log(`📁 [FILE-LOAD] Component unmounted, skipping file set`);
        }
      } catch (error) {
        console.error(`❌ [FILE-LOAD] Error loading files for task ${task.id}:`, error);
      }
    };

    if (task.id) {
      loadTaskFiles();
    }

    return () => {
      mounted = false;
      console.log(`🧹 [FILE-LOAD] Cleanup for task ${task.id} - isolated data preserved`);
    };
  }, [task.id, setFiles]);

  // ========================================================================
  // MEMOIZED VALUES - USANDO DATOS AISLADOS
  // ========================================================================

  const taskStats = useMemo(() => ({
    messageCount: taskMessages.length,
    commandCount: 0, // Todo: usar taskTerminalCommands cuando esté implementado
    planProgress: progress,
    hasFiles: taskFiles.length > 0,
    isCompleted: task.status === 'completed'
  }), [taskMessages.length, progress, task.status, taskFiles.length]);

  // Combinar logs con filtro de seguridad por tarea (ya están aislados)
  const combinedLogs = useMemo(() => {
    const filteredExternalLogs = externalLogs.filter(log => 
      log && log.message && log.timestamp
    );
    
    const combined = [...taskTerminalLogs, ...filteredExternalLogs].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
    
    console.log(`📋 [TASK-${task.id}] Combined isolated logs: ${combined.length} total (${taskTerminalLogs.length} terminal + ${filteredExternalLogs.length} external)`);
    
    return combined;
  }, [taskTerminalLogs, externalLogs, task.id]);

  // ========================================================================
  // CALLBACKS MEMOIZADOS - USANDO DATOS AISLADOS
  // ========================================================================

  const handleUpdateTask = useCallback((updatedTask: Task | ((current: Task) => Task)) => {
    if (typeof updatedTask === 'function') {
      onUpdateTask(updatedTask);
    } else {
      onUpdateTask(updatedTask);
    }
  }, [onUpdateTask]);

  const handleUpdateMessages = useCallback((updater: (messages: Message[]) => Message[]) => {
    if (typeof updater !== 'function') {
      console.error('❌ handleUpdateMessages: updater is not a function');
      return;
    }
    
    // ✅ USAR CONTEXT AISLADO PARA MENSAJES
    updateMessages(task.id, updater);
    
    // También actualizar la tarea principal
    handleUpdateTask((currentTask: Task) => ({
      ...currentTask,
      messages: updater(currentTask.messages || [])
    }));
  }, [handleUpdateTask, task.id, updateMessages]);

  const handleUpdateMessagesWrapper = useCallback((messages: Message[]) => {
    // ✅ USAR CONTEXT AISLADO
    setMessages(task.id, messages);
    
    handleUpdateTask((currentTask: Task) => ({
      ...currentTask,
      messages: messages
    }));
  }, [handleUpdateTask, task.id, setMessages]);

  const handleToggleFavorite = useCallback(() => {
    handleUpdateTask((currentTask: Task) => ({
      ...currentTask,
      isFavorite: !currentTask.isFavorite
    }));
  }, [handleUpdateTask]);

  const handleFilesModal = useCallback(() => {
    setShowFilesModal(true);
  }, []);

  const handleCloseFilesModal = useCallback(() => {
    setShowFilesModal(false);
  }, []);

  const handleShareModal = useCallback(() => {
    setShowShareModal(true);
  }, []);

  const handleDownloadFile = useCallback(async (file: FileItem) => {
    try {
      const blob = await agentAPI.downloadFile(file.id);
      
      // Crear enlace de descarga
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = file.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  }, []);

  const handleDownloadAllFiles = useCallback(async () => {
    try {
      const blob = await agentAPI.downloadAllFiles(task.id);
      
      // Crear enlace de descarga
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${task.title}-archivos.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading all files:', error);
    }
  }, [task.id, task.title]);

  const handleGenerateShareLink = useCallback(async (taskId: string): Promise<string> => {
    try {
      // Aquí se llamaría a la API para generar el enlace
      const response = await agentAPI.generateShareLink(taskId);
      return response.link;
    } catch (error) {
      console.error('Error generating share link:', error);
      throw error;
    }
  }, []);

  const handleCloseShareModal = useCallback(() => {
    setShowShareModal(false);
  }, []);

  const handleInitializationLog = useCallback((message: string, type: 'info' | 'success' | 'error') => {
    onInitializationLog?.(message, type);
  }, [onInitializationLog]);

  const handleInitializationComplete = useCallback(() => {
    onInitializationComplete?.();
  }, [onInitializationComplete]);

  // ========================================================================
  // MEMOIZED COMPONENTS - USANDO DATOS AISLADOS
  // ========================================================================

  const chatInterface = useMemo(() => (
    <ChatInterface
      messages={taskMessages} // ✅ USAR DATOS AISLADOS
      onUpdateMessages={handleUpdateMessagesWrapper}
      isTyping={isThinking}
      onFilesClick={handleFilesModal}
      onShareClick={handleShareModal}
      disabled={false} // ✅ CORRECCIÓN CRÍTICA: HABILITAR PERMANENTEMENTE EL INPUT - PROBLEMA DE KEYWORDS SOLUCIONADO
      task={task}
      onUpdateTask={handleUpdateTask}
    />
  ), [taskMessages, task, handleUpdateMessagesWrapper, isThinking, handleFilesModal, handleShareModal, isInitializing, handleUpdateTask]);

  const terminalView = useMemo(() => (
    <TerminalView
      commands={task.terminalCommands || []}
      logs={combinedLogs} // ✅ USAR LOGS COMBINADOS AISLADOS
      isInitializing={isInitializing}
      onInitializationComplete={handleInitializationComplete}
      onInitializationLog={handleInitializationLog}
      task={task}
      plan={plan} // ✅ USAR PLAN DEL HOOK AISLADO
      taskId={task.id}
      taskTitle={task.title}
    />
  ), [task.terminalCommands, task, combinedLogs, isInitializing, handleInitializationComplete, handleInitializationLog, plan]);

  const filesModal = useMemo(() => (
    showFilesModal && (
      <FilesModal
        isOpen={showFilesModal}
        onClose={handleCloseFilesModal}
        files={taskFiles} // ✅ USAR ARCHIVOS AISLADOS
        onDownload={handleDownloadFile}
        onDownloadAll={handleDownloadAllFiles}
        taskTitle={task.title}
      />
    )
  ), [showFilesModal, handleCloseFilesModal, taskFiles, task.title, handleDownloadFile, handleDownloadAllFiles]);

  const shareModal = useMemo(() => (
    showShareModal && (
      <ShareModal
        isOpen={showShareModal}
        onClose={handleCloseShareModal}
        taskTitle={task.title}
        taskId={task.id}
        onGenerateLink={handleGenerateShareLink}
      />
    )
  ), [showShareModal, handleCloseShareModal, task.title, task.id, handleGenerateShareLink]);

  // ========================================================================
  // RENDER
  // ========================================================================

  return (
    <div className="flex h-full overflow-hidden relative">
      {/* Panel izquierdo - Chat - Redimensionable */}
      <div 
        className="min-w-0 flex flex-col bg-[#272728] border-r border-[rgba(255,255,255,0.08)] overflow-hidden transition-all duration-200"
        style={{ 
          width: responsiveLayout.shouldCollapseChat 
            ? '100%' 
            : `${chatWidthPercent}%`,
          minWidth: `${Math.min(responsiveLayout.minChatWidth, windowWidth * 0.3)}px`,
          maxWidth: `${responsiveLayout.maxChatWidth}px`
        }}
      >
        {/* Header del task - Responsive Header */}
        <div className="p-2 sm:p-4 border-b border-[rgba(255,255,255,0.08)] bg-[#212122]">
          <div className="flex items-center justify-between flex-wrap sm:flex-nowrap gap-2">
            <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
              <h2 className="text-base sm:text-xl font-semibold text-white truncate max-w-[200px] sm:max-w-md">
                {task.title}
              </h2>
              {plan.length > 0 && (
                <div className="flex items-center gap-1 sm:gap-2">
                  <div className="w-12 sm:w-20 bg-[#3a3a3c] rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${taskStats.planProgress}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400 whitespace-nowrap">{taskStats.planProgress}%</span>
                </div>
              )}
            </div>
            
            {/* Action Buttons - Responsive Stack */}
            <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
              {!responsiveLayout.shouldCollapseChat && (
                <div className="text-xs text-gray-500 px-2 py-1 bg-gray-800 rounded">
                  Chat: {Math.round(chatWidthPercent)}%
                </div>
              )}
              
              <button
                onClick={handleToggleFavorite}
                className={`p-1 sm:p-2 rounded-lg transition-all duration-200 ${
                  task.isFavorite
                    ? 'text-yellow-400 bg-yellow-400/10 hover:bg-yellow-400/20'
                    : 'text-gray-400 hover:text-yellow-400 hover:bg-yellow-400/10'
                }`}
                title={task.isFavorite ? 'Quitar de favoritos' : 'Agregar a favoritos'}
              >
                <Star className={`w-4 h-4 sm:w-5 sm:h-5 ${task.isFavorite ? 'fill-current' : ''}`} />
              </button>
              
              <button
                onClick={handleFilesModal}
                className="p-1 sm:p-2 rounded-lg text-gray-400 hover:text-blue-400 hover:bg-blue-400/10 transition-all duration-200"
                title="Ver archivos generados"
              >
                <Files className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
              
              <button
                onClick={handleShareModal}
                className="p-1 sm:p-2 rounded-lg text-gray-400 hover:text-green-400 hover:bg-green-400/10 transition-all duration-200"
                title="Compartir conversación"
              >
                <Share2 className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
              
              {isConnected && (
                <div className="flex items-center gap-1 sm:gap-2 ml-1 sm:ml-2 px-2 sm:px-3 py-1 bg-green-500/10 rounded-full">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-xs text-green-400 font-medium hidden sm:inline">En vivo</span>
                  <span className="text-xs text-green-400 font-medium sm:hidden">●</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Chat Interface - Responsive Container */}
        <div className="flex-1 overflow-hidden min-h-0">
          {chatInterface}
        </div>
      </div>

      {/* Barra de redimensionamiento - Solo visible en desktop */}
      {!responsiveLayout.shouldCollapseChat && (
        <div
          className="w-1 bg-[rgba(255,255,255,0.05)] hover:bg-blue-500/30 cursor-col-resize transition-colors duration-200 group flex-shrink-0 relative"
          onMouseDown={handleMouseDown}
          ref={resizeRef}
        >
          <div className="absolute inset-y-0 left-1/2 transform -translate-x-1/2 w-3 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <GripVertical className="w-4 h-4 text-gray-400" />
          </div>
          {isResizing && (
            <div className="absolute inset-0 w-1 bg-blue-500" />
          )}
        </div>
      )}

      {/* Panel derecho - Monitor de Ejecución - Responsive Width */}     
      <div 
        className={`
          min-w-0 bg-[#1e1e1e] border-l border-[rgba(255,255,255,0.08)] flex-shrink-0 transition-all duration-200
          ${responsiveLayout.shouldCollapseChat ? 'hidden' : 'flex'}
        `}
        style={{ 
          width: responsiveLayout.shouldCollapseChat 
            ? '0%' 
            : `${100 - chatWidthPercent}%`,
          minWidth: responsiveLayout.shouldCollapseSidebar ? '250px' : '300px'
        }}
        ref={monitorRef}
      >
        {/* Header del Monitor con indicador de tamaño */}
        <div className="flex flex-col h-full">
          <div className="px-3 py-2 bg-[#1a1a1a] border-b border-[rgba(255,255,255,0.08)]">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-300">Monitor de Ejecución</h3>
              <div className="text-xs text-gray-500">
                {Math.round(100 - chatWidthPercent)}%
              </div>
            </div>
          </div>
          <div className="flex-1 min-h-0">
            {terminalView}
          </div>
        </div>
      </div>

      {/* Overlay de redimensionamiento */}
      {isResizing && (
        <div className="fixed inset-0 bg-transparent cursor-col-resize z-50" />
      )}

      {/* Modals */}
      {filesModal}
      {shareModal}
    </div>
  );
};

// ========================================================================
// EXPORT CON REACT.MEMO MEJORADO
// ========================================================================

export const TaskView = React.memo(TaskViewComponent, (prevProps, nextProps) => {
  return (
    prevProps.task.id === nextProps.task.id &&
    prevProps.task.title === nextProps.task.title &&
    prevProps.task.status === nextProps.task.status &&
    prevProps.task.progress === nextProps.task.progress &&
    prevProps.isThinking === nextProps.isThinking &&
    prevProps.isInitializing === nextProps.isInitializing &&
    prevProps.externalLogs?.length === nextProps.externalLogs?.length
  );
});