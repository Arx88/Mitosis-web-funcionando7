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
import { Star, Files, Share2 } from 'lucide-react';

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
  
  const monitorRef = useRef<HTMLDivElement>(null);
  
  // Memory manager aislado por tarea (conservado)
  const { hasActiveMemory, getMemoryStats } = useIsolatedMemoryManager({ taskId: task.id });

  // ========================================================================
  // PLAN MANAGER SIMPLIFICADO - USANDO CONTEXT AISLADO
  // ========================================================================

  const {
    plan,
    progress,
    isConnected,
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
  
  const currentPageIndex = useMemo(() => {
    const index = getCurrentPageIndex(task.id);
    console.log(`📍 [PAGE-INDEX] Task ${task.id} current page index: ${index}`);
    return index;
  }, [getCurrentPageIndex, task.id]);

  // ========================================================================
  // EFECTOS DE INICIALIZACIÓN Y RESETEO POR TAREA
  // ========================================================================

  // RESET COMPLETO cuando cambia la tarea ID - SIN RESETEAR CONTEXT (ya está aislado)
  const lastTaskIdRef = useRef<string>('');
  useEffect(() => {
    if (task.id !== lastTaskIdRef.current) {
      console.log(`🔄 [TASKVIEW-SWITCH] ${lastTaskIdRef.current} → ${task.id}`);
      console.log(`🔄 [TASKVIEW-SWITCH] Task title: "${task.title}"`);
      console.log(`🔄 [TASKVIEW-SWITCH] Task status: ${task.status}`);
      console.log(`🔄 [TASKVIEW-SWITCH] Task messages: ${task.messages?.length || 0}`);
      console.log(`🔄 [TASKVIEW-SWITCH] Task plan: ${task.plan?.length || 0} steps`);
      
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
      
      // NO RESETEAR CONTEXT - Ya está aislado por taskId
      // Solo resetear estado UI local
      setShowFilesModal(false);
      setShowShareModal(false);
      
      // Si hay un plan inicial, establecerlo
      if (task.plan && task.plan.length > 0) {
        console.log(`📋 [PLAN-INIT] Loading existing plan with ${task.plan.length} steps`);
        setPlan(task.plan);
      } else {
        console.log(`📋 [PLAN-INIT] No plan found for task ${task.id}`);
      }
      
      console.log(`✅ [TASKVIEW-SWITCH] Switch complete - data isolated`);
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
      disabled={false} // ✅ TEMPORALMENTE DESHABILITAR isInitializing HASTA QUE LA INICIALIZACIÓN FUNCIONE CORRECTAMENTE
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
    <div className="flex h-full">
      {/* Panel izquierdo - Chat */}
      <div className="flex-1 flex flex-col bg-[#272728] border-r border-[rgba(255,255,255,0.08)]">
        {/* Header del task */}
        <div className="p-4 border-b border-[rgba(255,255,255,0.08)] bg-[#212122]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold text-white truncate max-w-md">
                {task.title}
              </h2>
              {plan.length > 0 && (
                <div className="flex items-center gap-2">
                  <div className="w-20 bg-[#3a3a3c] rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${taskStats.planProgress}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400">{taskStats.planProgress}%</span>
                </div>
              )}
            </div>
            
            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleToggleFavorite}
                className={`p-2 rounded-lg transition-all duration-200 ${
                  task.isFavorite
                    ? 'text-yellow-400 bg-yellow-400/10 hover:bg-yellow-400/20'
                    : 'text-gray-400 hover:text-yellow-400 hover:bg-yellow-400/10'
                }`}
                title={task.isFavorite ? 'Quitar de favoritos' : 'Agregar a favoritos'}
              >
                <Star className={`w-5 h-5 ${task.isFavorite ? 'fill-current' : ''}`} />
              </button>
              
              <button
                onClick={handleFilesModal}
                className="p-2 rounded-lg text-gray-400 hover:text-blue-400 hover:bg-blue-400/10 transition-all duration-200"
                title="Ver archivos generados"
              >
                <Files className="w-5 h-5" />
              </button>
              
              <button
                onClick={handleShareModal}
                className="p-2 rounded-lg text-gray-400 hover:text-green-400 hover:bg-green-400/10 transition-all duration-200"
                title="Compartir conversación"
              >
                <Share2 className="w-5 h-5" />
              </button>
              
              {isConnected && (
                <div className="flex items-center gap-2 ml-2 px-3 py-1 bg-green-500/10 rounded-full">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-xs text-green-400 font-medium">En vivo</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden">
          {chatInterface}
        </div>
      </div>

      {/* Panel derecho - Terminal */}     
      <div className="w-1/2 bg-[#1e1e1e] border-l border-[rgba(255,255,255,0.08)]" ref={monitorRef}>
        {terminalView}
      </div>

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