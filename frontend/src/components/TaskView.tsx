import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Task, Message, TerminalCommand } from '../types';
import { TerminalView } from './TerminalView';
import { ChatInterface } from './ChatInterface';
import { ThinkingAnimation } from './ThinkingAnimation';
import { FilesModal } from './FilesModal';
import { ShareModal } from './ShareModal';
import { agentAPI, FileItem } from '../services/api';
import { useMemoryManager } from '../hooks/useMemoryManager';
import { usePlanManager } from '../hooks/usePlanManager';
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
// COMPONENTE REFACTORIZADO - USANDO usePlanWebSocket
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
  const [isTyping, setIsTyping] = useState(false);
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [taskFiles, setTaskFiles] = useState<FileItem[]>([]);
  const [terminalLogs, setTerminalLogs] = useState<Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>>([]);
  const monitorRef = useRef<HTMLDivElement>(null);
  
  // Memory manager
  const { memory } = useMemoryManager();

  // ========================================================================
  // NUEVO: PLAN MANAGER SIMPLIFICADO - REEMPLAZA LA LÓGICA ANTERIOR
  // ========================================================================

  const {
    plan,
    progress,
    isConnected,
    currentActiveStep,
    setPlan: updatePlanFromTask
  } = usePlanManager({
    taskId: task.id,
    initialPlan: task.plan || [],
    onPlanUpdate: (updatedPlan) => {
      console.log(`🔄 [TASK-${task.id}] Plan updated:`, updatedPlan.length, 'steps');
      // Actualizar la tarea con el nuevo plan
      onUpdateTask((currentTask: Task) => ({
        ...currentTask,
        plan: updatedPlan,
        progress: Math.round((updatedPlan.filter(s => s.completed).length / updatedPlan.length) * 100)
      }));
    },
    onStepComplete: (stepId) => {
      console.log(`✅ [TASK-${task.id}] Step completed:`, stepId);
      // Log cuando un paso se completa
      const step = plan.find(s => s.id === stepId);
      if (step) {
        setTerminalLogs(prev => [...prev, {
          message: `✅ Completado: ${step.title}`,
          type: 'success',
          timestamp: new Date()
        }]);
      }
      
      // Notificar progreso
      if (onUpdateTaskProgress) {
        onUpdateTaskProgress(task.id);
      }
    },
    onTaskComplete: () => {
      console.log(`🎉 [TASK-${task.id}] Task completed!`);
      // Log cuando toda la tarea se completa
      setTerminalLogs(prev => [...prev, {
        message: '🎉 ¡Tarea completada exitosamente!',
        type: 'success',
        timestamp: new Date()
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
  // SINCRONIZACIÓN CON PLAN DE LA TAREA
  // ========================================================================

  // Sincronizar el plan del WebSocket con el plan de la tarea
  useEffect(() => {
    if (task.plan && task.plan.length > 0) {
      updatePlanFromTask(task.plan);
    }
  }, [task.plan, updatePlanFromTask]);

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

  const combinedLogs = useMemo(() => {
    return [...terminalLogs, ...externalLogs].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [terminalLogs, externalLogs]);

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
  // EFFECTS
  // ========================================================================

  // Cargar archivos de tarea
  useEffect(() => {
    let mounted = true;
    
    const loadTaskFiles = async () => {
      try {
        const files = await agentAPI.getTaskFiles(task.id);
        if (mounted) {
          setTaskFiles(files);
        }
      } catch (error) {
        console.error('Error loading task files:', error);
      }
    };

    if (task.id) {
      loadTaskFiles();
    }

    return () => {
      mounted = false;
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
      plan={plan} // Usar el plan del hook WebSocket
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
            </div>
            
            {/* Stats */}
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span>{taskStats.messageCount} mensajes</span>
              <span>{taskStats.commandCount} comandos</span>
              {plan.length > 0 && <span>{taskStats.planProgress}% completado</span>}
              {isConnected && (
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-xs text-green-400">Live</span>
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