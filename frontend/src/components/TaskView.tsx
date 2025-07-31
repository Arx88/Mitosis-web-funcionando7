import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Task, Message, TerminalCommand } from '../types';
import { TerminalView } from './TerminalView';
import { ChatInterface } from './ChatInterface';
import { ThinkingAnimation } from './ThinkingAnimation';
import { FilesModal } from './FilesModal';
import { ShareModal } from './ShareModal';
import { agentAPI, FileItem } from '../services/api';
import { useIsolatedMemoryManager } from '../hooks/useIsolatedMemoryManager';
import { usePlanManager } from '../hooks/usePlanManager'; // ✅ Usar el hook simplificado
import { Star } from 'lucide-react';

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
// COMPONENTE REFACTORIZADO - ARREGLANDO LOOP INFINITO
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
  // ESTADO LOCAL SIMPLE
  // ========================================================================
  
  const [isTyping, setIsTyping] = useState(false);
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [taskFiles, setTaskFiles] = useState<FileItem[]>([]);
  
  // LOGS TERMINALES AISLADOS
  const [terminalLogs, setTerminalLogs] = useState<Array<{
    message: string, 
    type: 'info' | 'success' | 'error', 
    timestamp: Date,
    taskId: string
  }>>([]);
  
  const monitorRef = useRef<HTMLDivElement>(null);
  
  // Memory manager aislado por tarea
  const { hasActiveMemory, getMemoryStats } = useIsolatedMemoryManager({ taskId: task.id });

  // ========================================================================
  // PLAN MANAGER SIMPLIFICADO - CON PROTECCIÓN CONTRA LOOPS
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
      console.log(`🔄 [TASK-${task.id}] Plan updated (SAFE):`, updatedPlan.length, 'steps');
      // ✅ ARREGLO: Solo actualizar si hay cambios reales
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
      console.log(`✅ [TASK-${task.id}] Step completed (SAFE):`, stepId);
      // Log cuando un paso se completa
      const step = plan.find(s => s.id === stepId);
      if (step) {
        setTerminalLogs(prev => [...prev, {
          message: `✅ Completado: ${step.title}`,
          type: 'success',
          timestamp: new Date(),
          taskId: task.id
        }]);
      }
      
      // Notificar progreso
      if (onUpdateTaskProgress) {
        onUpdateTaskProgress(task.id);
      }
    },
    onTaskComplete: () => {
      console.log(`🎉 [TASK-${task.id}] Task completed (SAFE)!`);
      // Log cuando toda la tarea se completa
      setTerminalLogs(prev => [...prev, {
        message: '🎉 ¡Tarea completada exitosamente!',
        type: 'success',
        timestamp: new Date(),
        taskId: task.id
      }]);

      // Actualizar estado de la tarea
      onUpdateTask((currentTask: Task) => ({
        ...currentTask,
        status: 'completed',
        progress: 100
      }));
    }
  });

  // ========================================================================
  // SINCRONIZACIÓN SEGURA CON PLAN DE LA TAREA - ARREGLO DEL LOOP
  // ========================================================================

  // REF para evitar loops infinitos
  const lastPlanRef = useRef<string>('');
  const lastTaskIdRef = useRef<string>('');

  // ✅ ARREGLO CRÍTICO: Reset completo cuando cambia la tarea ID
  useEffect(() => {
    if (task.id !== lastTaskIdRef.current) {
      console.log(`🔄 [TASK-${task.id}] Task changed from ${lastTaskIdRef.current} to ${task.id} - COMPLETE RESET`);
      
      // Resetear completamente el estado del plan manager
      lastPlanRef.current = '';
      lastTaskIdRef.current = task.id;
      
      // Si hay un plan inicial, establecerlo
      if (task.plan && task.plan.length > 0) {
        console.log(`📋 [TASK-${task.id}] Setting initial plan with ${task.plan.length} steps`);
        setPlan(task.plan);
      } else {
        // Limpiar plan si no hay plan inicial
        setPlan([]);
      }
    }
  }, [task.id, task.plan, setPlan]);

  // ✅ ARREGLO: Sincronizar solo cuando hay cambios reales del plan (NO basado en task.id)
  useEffect(() => {
    if (task.plan && task.plan.length > 0) {
      // Crear hash del plan para detectar cambios reales
      const planHash = JSON.stringify(task.plan.map(s => ({ 
        id: s.id, 
        completed: s.completed, 
        active: s.active 
      })));
      
      // Solo actualizar si el plan realmente cambió
      if (planHash !== lastPlanRef.current) {
        console.log(`🔄 [TASK-${task.id}] Plan sync - real change detected`);
        lastPlanRef.current = planHash;
        setPlan(task.plan);
      } else {
        console.log(`🛡️ [TASK-${task.id}] Plan sync - no changes, skipping`);
      }
    }
  }, [task.plan, setPlan]); // ✅ ARREGLO CRÍTICO: Dependencia en task.plan, NO en task.id

  // ========================================================================
  // MEMOIZED VALUES
  // ========================================================================

  const taskStats = useMemo(() => ({
    messageCount: task.messages?.length || 0,
    commandCount: task.terminalCommands?.length || 0,
    planProgress: progress,
    hasFiles: taskFiles.length > 0,
    isCompleted: task.status === 'completed'
  }), [task.messages?.length, task.terminalCommands?.length, progress, task.status, taskFiles.length]);

  // Combinar logs con filtro de seguridad por tarea
  const combinedLogs = useMemo(() => {
    const filteredTerminalLogs = terminalLogs.filter(log => 
      !log.taskId || log.taskId === task.id
    );
    
    const filteredExternalLogs = externalLogs.filter(log => 
      log && log.message && log.timestamp
    );
    
    const combined = [...filteredTerminalLogs, ...filteredExternalLogs].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
    
    console.log(`📋 [TASK-${task.id}] Combined logs: ${combined.length} total (${filteredTerminalLogs.length} terminal + ${filteredExternalLogs.length} external)`);
    
    return combined;
  }, [terminalLogs, externalLogs, task.id]);

  // ========================================================================
  // CALLBACKS MEMOIZADOS
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
    
    handleUpdateTask((currentTask: Task) => ({
      ...currentTask,
      messages: updater(currentTask.messages || [])
    }));
  }, [handleUpdateTask]);

  const handleUpdateMessagesWrapper = useCallback((messages: Message[]) => {
    handleUpdateTask((currentTask: Task) => ({
      ...currentTask,
      messages: messages
    }));
  }, [handleUpdateTask]);

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
  // EFFECTS - AISLAMIENTO Y LIMPIEZA
  // ========================================================================

  // RESET COMPLETO cuando cambia la tarea
  useEffect(() => {
    console.log(`🔄 [TASK-${task.id}] TaskView initialized - clearing state`);
    
    // Limpiar estado local aislado
    setTerminalLogs([]);
    setTaskFiles([]);
    setIsTyping(false);
    setShowFilesModal(false);
    setShowShareModal(false);
    
    // Reset plan hash
    lastPlanRef.current = '';
    
    console.log(`✅ [TASK-${task.id}] TaskView state reset complete`);
  }, [task.id]);

  // Cargar archivos de tarea específicos
  useEffect(() => {
    let mounted = true;
    
    const loadTaskFiles = async () => {
      try {
        console.log(`📁 [TASK-${task.id}] Loading task files`);
        const files = await agentAPI.getTaskFiles(task.id);
        if (mounted) {
          setTaskFiles(files);
          console.log(`✅ [TASK-${task.id}] Loaded ${files.length} files`);
        }
      } catch (error) {
        console.error(`❌ [TASK-${task.id}] Error loading task files:`, error);
      }
    };

    if (task.id) {
      loadTaskFiles();
    }

    return () => {
      mounted = false;
      console.log(`🧹 [TASK-${task.id}] TaskView cleanup`);
    };
  }, [task.id]);

  // ========================================================================
  // MEMOIZED COMPONENTS
  // ========================================================================

  const chatInterface = useMemo(() => (
    <ChatInterface
      messages={task.messages || []}
      onUpdateMessages={handleUpdateMessagesWrapper}
      isTyping={isTyping || isThinking}
      onFilesClick={handleFilesModal}
      onShareClick={handleShareModal}
      disabled={isInitializing}
      task={task}
      onUpdateTask={handleUpdateTask}
    />
  ), [task.messages, task, handleUpdateMessagesWrapper, isTyping, isThinking, handleFilesModal, handleShareModal, isInitializing, handleUpdateTask]);

  const terminalView = useMemo(() => (
    <TerminalView
      commands={task.terminalCommands || []}
      logs={combinedLogs}
      isInitializing={isInitializing}
      onInitializationComplete={handleInitializationComplete}
      onInitializationLog={handleInitializationLog}
      task={task}
      plan={plan} // ✅ Usar el plan del hook simplificado
      taskId={task.id}
      taskTitle={task.title}
    />
  ), [task.terminalCommands, task, combinedLogs, isInitializing, handleInitializationComplete, handleInitializationLog, plan]);

  const filesModal = useMemo(() => (
    showFilesModal && (
      <FilesModal
        isOpen={showFilesModal}
        onClose={handleCloseFilesModal}
        files={taskFiles}
        taskTitle={task.title}
        taskId={task.id}
      />
    )
  ), [showFilesModal, handleCloseFilesModal, taskFiles, task.title, task.id]);

  const shareModal = useMemo(() => (
    showShareModal && (
      <ShareModal
        isOpen={showShareModal}
        onClose={handleCloseShareModal}
        task={task}
      />
    )
  ), [showShareModal, handleCloseShareModal, task]);

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
              <button
                onClick={handleToggleFavorite}
                className={`p-1 rounded-md transition-colors ${
                  task.isFavorite
                    ? 'text-yellow-400 hover:text-yellow-300'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
                title={task.isFavorite ? 'Remove from favorites' : 'Add to favorites'}
              >
                <Star className={`w-5 h-5 ${task.isFavorite ? 'fill-current' : ''}`} />
              </button>
              {/* ID DE LA TAREA PARA DEBUGGING */}
              <span className="text-xs text-gray-500 bg-[#3a3a3c] px-2 py-1 rounded font-mono">
                ID: {task.id.substring(0, 8)}...
              </span>
            </div>
            
            {/* Stats */}
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span>{taskStats.messageCount} mensajes</span>
              <span>{taskStats.commandCount} comandos</span>
              {plan.length > 0 && <span>{taskStats.planProgress}% completado</span>}
              {isConnected && (
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-xs text-green-400">Live-{task.id.substring(0, 4)}</span>
                </div>
              )}
              {/* Timestamp de última actualización */}
              {lastUpdateTime && (
                <span className="text-xs text-blue-400" title={`Última actualización: ${lastUpdateTime.toLocaleTimeString()}`}>
                  🔄 {lastUpdateTime.toLocaleTimeString()}
                </span>
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
// EXPORT CON REACT.MEMO
// ========================================================================

export const TaskView = React.memo(TaskViewComponent, (prevProps, nextProps) => {
  return (
    prevProps.task.id === nextProps.task.id &&
    prevProps.task.title === nextProps.task.title &&
    prevProps.task.status === nextProps.task.status &&
    prevProps.task.messages?.length === nextProps.task.messages?.length &&
    prevProps.task.terminalCommands?.length === nextProps.task.terminalCommands?.length &&
    prevProps.task.progress === nextProps.task.progress &&
    prevProps.isThinking === nextProps.isThinking &&
    prevProps.isInitializing === nextProps.isInitializing &&
    prevProps.externalLogs?.length === nextProps.externalLogs?.length
  );
});