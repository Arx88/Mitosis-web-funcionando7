import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Task, Message, TerminalCommand } from '../types';
import { TerminalView } from './TerminalView';
import { ChatInterface } from './ChatInterface';
import { ThinkingAnimation } from './ThinkingAnimation';
import { FilesModal } from './FilesModal';
import { ShareModal } from './ShareModal';
import { agentAPI, FileItem } from '../services/api';
import { useMemoryManager } from '../hooks/useMemoryManager';
import { useWebSocket } from '../hooks/useWebSocket';
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
// COMPONENTE OPTIMIZADO CON REACT.MEMO Y MEMOIZATION
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
  
  // WebSocket integration optimizado con useMemo
  const {
    socket,
    isConnected,
    joinTaskRoom,
    leaveTaskRoom,
    addEventListeners,
    removeEventListeners,
  } = useWebSocket();

  // Memory manager optimizado
  const { memory } = useMemoryManager();

  // ========================================================================
  // MEMOIZED VALUES - PREVENIR RE-CÁLCULOS INNECESARIOS
  // ========================================================================

  // Memoizar cálculos pesados del task
  const taskStats = useMemo(() => ({
    messageCount: task.messages?.length || 0,
    commandCount: task.terminalCommands?.length || 0,
    planProgress: task.plan ? Math.round((task.plan.filter(s => s.completed).length / task.plan.length) * 100) : 0,
    hasFiles: taskFiles.length > 0,
    isCompleted: task.status === 'completed'
  }), [task.messages?.length, task.terminalCommands?.length, task.plan, task.status, taskFiles.length]);

  // Memoizar configuración de WebSocket
  const socketConfig = useMemo(() => ({
    taskId: task.id,
    roomName: `task-${task.id}`
  }), [task.id]);

  // Memoizar logs combinados para evitar re-creación en cada render
  const combinedLogs = useMemo(() => {
    return [...terminalLogs, ...externalLogs].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [terminalLogs, externalLogs]);

  // ========================================================================
  // CALLBACKS MEMOIZADOS - PREVENIR RE-RENDERS DE COMPONENTES HIJOS
  // ========================================================================

  const handleUpdateTask = useCallback((updatedTask: Task | ((current: Task) => Task)) => {
    if (typeof updatedTask === 'function') {
      onUpdateTask(updatedTask);
    } else {
      onUpdateTask(updatedTask);
    }
  }, [onUpdateTask]);

  const handleUpdateMessages = useCallback((updater: (messages: Message[]) => Message[]) => {
    // Validate that updater is actually a function
    if (typeof updater !== 'function') {
      console.error('❌ handleUpdateMessages: updater is not a function:', {
        updaterType: typeof updater,
        updater: updater,
        taskId: task.id
      });
      return;
    }
    
    handleUpdateTask((currentTask: Task) => ({
      ...currentTask,
      messages: updater(currentTask.messages || [])
    }));
  }, [handleUpdateTask, task.id]);

  // Create a wrapper function that adapts to ChatInterface's expected signature
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
  // EFFECTS OPTIMIZADOS
  // ========================================================================

  // WebSocket setup optimizado
  useEffect(() => {
    if (!socket || !isConnected || !task.id) return;

    joinTaskRoom(socketConfig.roomName);

    const eventHandlers = {
      'task_progress': (data: any) => {
        if (data.task_id === task.id) {
          handleUpdateTask((currentTask: Task) => ({
            ...currentTask,
            progress: data.progress,
            status: data.status || currentTask.status
          }));
          
          if (onUpdateTaskProgress) {
            onUpdateTaskProgress(task.id);
          }
        }
      },
      
      'task_message': (data: any) => {
        if (data.task_id === task.id) {
          const newMessage: Message = {
            id: data.id || `msg-${Date.now()}`,
            content: data.content,
            sender: data.sender || 'assistant',
            timestamp: new Date(data.timestamp || Date.now()),
            attachments: data.attachments
          };
          
          handleUpdateMessages((messages: Message[]) => [...messages, newMessage]);
        }
      },
      
      'terminal_output': (data: any) => {
        if (data.task_id === task.id) {
          const logEntry = {
            message: data.output,
            type: data.type || 'info' as const,
            timestamp: new Date(data.timestamp || Date.now())
          };
          
          setTerminalLogs(prev => [...prev, logEntry]);
        }
      },
      
      'typing_status': (data: any) => {
        if (data.task_id === task.id) {
          setIsTyping(data.typing);
        }
      }
    };

    addEventListeners(eventHandlers);

    return () => {
      removeEventListeners(Object.keys(eventHandlers));
      leaveTaskRoom(socketConfig.roomName);
    };
  }, [socket, isConnected, task.id, socketConfig.roomName, joinTaskRoom, leaveTaskRoom, addEventListeners, removeEventListeners, handleUpdateTask, handleUpdateMessages, onUpdateTaskProgress]);

  // Cargar archivos de tarea optimizado
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
  // MEMOIZED COMPONENTS - PREVENIR RE-RENDERS INNECESARIOS
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
      plan={task.plan || []}
      taskId={task.id}
      taskTitle={task.title}
    />
  ), [task.terminalCommands, task, combinedLogs, isInitializing, handleInitializationComplete, handleInitializationLog]);

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
  // RENDER OPTIMIZADO
  // ========================================================================

  return (
    <div className="flex h-full">
      {/* Panel izquierdo - Chat */}
      <div className="flex-1 flex flex-col bg-[#272728] border-r border-[rgba(255,255,255,0.08)]">
        {/* Header del task optimizado */}
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
            
            {/* Stats optimizados */}
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span>{taskStats.messageCount} mensajes</span>
              <span>{taskStats.commandCount} comandos</span>
              {task.plan && <span>{taskStats.planProgress}% completado</span>}
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

      {/* Modals memoizados */}
      {filesModal}
      {shareModal}
    </div>
  );
};

// ========================================================================
// EXPORT CON REACT.MEMO Y COMPARACIÓN OPTIMIZADA
// ========================================================================

export const TaskView = React.memo(TaskViewComponent, (prevProps, nextProps) => {
  // Comparación personalizada para evitar re-renders innecesarios
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