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
    roomName: task.id  // ✅ FIX: Usar task.id directamente, no task-${task.id}
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
      // Eventos reales que emite el backend - ACTUALIZAR PLAN EN TIEMPO REAL
      'task_progress': (data: any) => {
        console.log('🔄 WebSocket task_progress received:', data);
        
        const logEntry = {
          message: `[${data.step_id || 'task'}] ${data.activity || data.message || 'Progress update'}`,
          type: 'info' as const,
          timestamp: new Date(data.timestamp || Date.now())
        };
        
        setTerminalLogs(prev => [...prev, logEntry]);
        
        // CRÍTICO: Actualizar progreso del plan si hay información de step
        if (data.step_id) {
          handleUpdateTask((currentTask: Task) => {
            if (!currentTask.plan) return currentTask;
            
            const updatedPlan = currentTask.plan.map(step => {
              if (step.id === data.step_id) {
                return {
                  ...step,
                  active: true,
                  status: 'in-progress'
                };
              } else {
                return {
                  ...step,
                  active: false
                };
              }
            });
            
            return {
              ...currentTask,
              plan: updatedPlan,
              status: 'in-progress'
            };
          });
        }
        
        if (onUpdateTaskProgress) {
          onUpdateTaskProgress(task.id);
        }
      },
      
      'step_started': (data: any) => {
        console.log('🚀 WebSocket step_started received:', data);
        
        const logEntry = {
          message: `▶️ Iniciando: ${data.title || data.step_title || 'Step'}`,
          type: 'success' as const,
          timestamp: new Date(data.timestamp || Date.now())
        };
        
        setTerminalLogs(prev => [...prev, logEntry]);
        
        // CRÍTICO: Actualizar el plan para mostrar el step activo
        handleUpdateTask((currentTask: Task) => {
          if (!currentTask.plan) return currentTask;
          
          const updatedPlan = currentTask.plan.map(step => {
            if (step.id === data.step_id) {
              return {
                ...step,
                active: true,
                status: 'in-progress',
                completed: false
              };
            } else {
              return {
                ...step,
                active: false
              };
            }
          });
          
          console.log('🔄 Plan updated after step_started:', {
            stepId: data.step_id,
            stepTitle: data.title,
            planLength: updatedPlan.length,
            activeStep: updatedPlan.find(s => s.active)?.title
          });
          
          return {
            ...currentTask,
            plan: updatedPlan,
            status: 'in-progress'
          };
        });
      },
      
      'step_completed': (data: any) => {
        console.log('✅ WebSocket step_completed received:', data);
        
        const logEntry = {
          message: `✅ Completado: ${data.title || data.step_title || 'Step'}`,
          type: 'success' as const,
          timestamp: new Date(data.timestamp || Date.now())
        };
        
        setTerminalLogs(prev => [...prev, logEntry]);
        
        // CRÍTICO: Marcar el step como completado y activar el siguiente
        handleUpdateTask((currentTask: Task) => {
          if (!currentTask.plan) return currentTask;
          
          const currentStepIndex = currentTask.plan.findIndex(step => step.id === data.step_id);
          const nextStepIndex = currentStepIndex + 1;
          
          const updatedPlan = currentTask.plan.map((step, index) => {
            if (step.id === data.step_id) {
              // Marcar el step actual como completado
              return {
                ...step,
                active: false,
                status: 'completed',
                completed: true
              };
            } else if (index === nextStepIndex && nextStepIndex < currentTask.plan.length) {
              // Activar el siguiente step si existe
              return {
                ...step,
                active: true,
                status: 'in-progress',
                completed: false
              };
            } else {
              return {
                ...step,
                active: false
              };
            }
          });
          
          // Calcular progreso total
          const completedSteps = updatedPlan.filter(s => s.completed).length;
          const totalSteps = updatedPlan.length;
          const progress = Math.round((completedSteps / totalSteps) * 100);
          
          console.log('🔄 Plan updated after step_completed:', {
            stepId: data.step_id,
            completedSteps,
            totalSteps,
            progress,
            nextActiveStep: updatedPlan.find(s => s.active)?.title
          });
          
          return {
            ...currentTask,
            plan: updatedPlan,
            progress,
            status: progress === 100 ? 'completed' : 'in-progress'
          };
        });
      },
      
      'step_needs_more_work': (data: any) => {
        console.log('⚠️ WebSocket step_needs_more_work received:', data);
        
        const logEntry = {
          message: `⚠️ Paso ${data.title} requiere más trabajo: ${data.feedback}`,
          type: 'warning' as const,
          timestamp: new Date(data.timestamp || Date.now())
        };
        
        setTerminalLogs(prev => [...prev, logEntry]);
      },
      
      'task_completed': (data: any) => {
        console.log('🎉 WebSocket task_completed received:', data);
        
        const logEntry = {
          message: '🎉 ¡Tarea completada exitosamente!',
          type: 'success' as const,
          timestamp: new Date(data.timestamp || Date.now())
        };
        
        setTerminalLogs(prev => [...prev, logEntry]);
        
        // Actualizar el estado de la tarea a completada
        handleUpdateTask((currentTask: Task) => ({
          ...currentTask,
          status: 'completed'
        }));
      },
      
      'plan_updated': (data: any) => {
        console.log('📋 WebSocket plan_updated received:', data);
        
        const logEntry = {
          message: `📋 Plan actualizado para: ${data.plan?.task_type || 'tarea'}`,
          type: 'info' as const,
          timestamp: new Date(data.timestamp || Date.now())
        };
        
        setTerminalLogs(prev => [...prev, logEntry]);
        
        // CRÍTICO: Actualizar el plan completo de la tarea
        if (data.plan && data.plan.steps && Array.isArray(data.plan.steps)) {
          handleUpdateTask((currentTask: Task) => {
            const updatedPlan = data.plan.steps.map((step: any, index: number) => {
              // Buscar el paso existente para preservar estado local
              const existingStep = currentTask.plan?.find(s => s.id === step.id);
              
              return {
                id: step.id,
                title: step.title,
                description: step.description,
                tool: step.tool,
                status: step.status,
                estimated_time: step.estimated_time,
                completed: step.completed || false,
                // CRÍTICO: Preservar estado activo local si no viene explícito del backend
                active: step.active !== undefined ? step.active : (existingStep?.active || false)
              };
            });
            
            console.log('📋 Updating task plan from plan_updated:', {
              taskId: currentTask.id,
              stepsCount: updatedPlan.length,
              activeStep: updatedPlan.find(s => s.active)?.title
            });
            
            return {
              ...currentTask,
              plan: updatedPlan,
              status: 'in-progress'
            };
          });
        }
      },
      
      'progress_update': (data: any) => {
        console.log('🔄 WebSocket progress_update received:', data);
        
        // Manejar diferentes tipos de progress_update
        if (data.type === 'step_completed' && data.data?.step_id) {
          const stepData = data.data;
          
          const logEntry = {
            message: `✅ Paso completado: ${stepData.title}`,
            type: 'success' as const,
            timestamp: new Date(data.timestamp || Date.now())
          };
          
          setTerminalLogs(prev => [...prev, logEntry]);
          
          // Actualizar el plan igual que en step_completed
          handleUpdateTask((currentTask: Task) => {
            if (!currentTask.plan) return currentTask;
            
            const currentStepIndex = currentTask.plan.findIndex(step => step.id === stepData.step_id);
            const nextStepIndex = currentStepIndex + 1;
            
            const updatedPlan = currentTask.plan.map((step, index) => {
              if (step.id === stepData.step_id) {
                return {
                  ...step,
                  active: false,
                  status: 'completed',
                  completed: true
                };
              } else if (index === nextStepIndex && nextStepIndex < currentTask.plan.length) {
                return {
                  ...step,
                  active: true,
                  status: 'in-progress'
                };
              } else {
                return {
                  ...step,
                  active: false
                };
              }
            });
            
            const completedSteps = updatedPlan.filter(s => s.completed).length;
            const totalSteps = updatedPlan.length;
            const progress = Math.round((completedSteps / totalSteps) * 100);
            
            console.log('📈 Progress updated from progress_update event:', {
              stepId: stepData.step_id,
              progress,
              completedSteps,
              totalSteps
            });
            
            return {
              ...currentTask,
              plan: updatedPlan,
              progress,
              status: progress === 100 ? 'completed' : 'in-progress'
            };
          });
        } else if (data.plan) {
          // Actualizar plan completo si viene en los datos
          handleUpdateTask((currentTask: Task) => {
            if (!data.plan.steps) return currentTask;
            
            const updatedPlan = data.plan.steps.map((step: any) => ({
              id: step.id,
              title: step.title,
              description: step.description,
              tool: step.tool,
              status: step.status,
              estimated_time: step.estimated_time,
              completed: step.completed || false,
              active: step.active || false
            }));
            
            return {
              ...currentTask,
              plan: updatedPlan
            };
          });
        }
      },
      
      'agent_activity': (data: any) => {
        console.log('🤖 WebSocket agent_activity received:', data);
        
        // Manejar actividad del agente similar a progress_update
        if (data.type === 'step_completed' && data.data?.step_id) {
          const stepData = data.data;
          
          const logEntry = {
            message: `🤖 Agente completó: ${stepData.title}`,
            type: 'success' as const,
            timestamp: new Date(data.timestamp || Date.now())
          };
          
          setTerminalLogs(prev => [...prev, logEntry]);
          
          // Mismo manejo que progress_update para step_completed
          handleUpdateTask((currentTask: Task) => {
            if (!currentTask.plan) return currentTask;
            
            const currentStepIndex = currentTask.plan.findIndex(step => step.id === stepData.step_id);
            const nextStepIndex = currentStepIndex + 1;
            
            const updatedPlan = currentTask.plan.map((step, index) => {
              if (step.id === stepData.step_id) {
                return {
                  ...step,
                  active: false,
                  status: 'completed',
                  completed: true
                };
              } else if (index === nextStepIndex && nextStepIndex < currentTask.plan.length) {
                return {
                  ...step,
                  active: true,
                  status: 'in-progress',
                  completed: false
                };
              } else {
                return {
                  ...step,
                  active: false
                };
              }
            });
            
            const completedSteps = updatedPlan.filter(s => s.completed).length;
            const totalSteps = updatedPlan.length;
            const progress = Math.round((completedSteps / totalSteps) * 100);
            
            console.log('🤖 Agent activity updated plan:', {
              stepId: stepData.step_id,
              progress,
              completedSteps,
              totalSteps,
              nextActiveStep: updatedPlan.find(s => s.active)?.title
            });
            
            return {
              ...currentTask,
              plan: updatedPlan,
              progress,
              status: progress === 100 ? 'completed' : 'in-progress'
            };
          });
        }
      },
      
      'task_update': (data: any) => {
        console.log('📝 WebSocket task_update received:', data);
        
        // Actualizar el plan si viene en task_update
        if (data.plan && data.plan.steps && Array.isArray(data.plan.steps)) {
          handleUpdateTask((currentTask: Task) => {
            const updatedPlan = data.plan.steps.map((step: any, index: number) => {
              // Buscar el paso existente para preservar estado local
              const existingStep = currentTask.plan?.find(s => s.id === step.id);
              
              return {
                id: step.id,
                title: step.title,
                description: step.description,
                tool: step.tool,
                status: step.status,
                estimated_time: step.estimated_time,
                completed: step.completed || false,
                // CRÍTICO: Preservar estado activo local si no viene explícito del backend
                active: step.active !== undefined ? step.active : (existingStep?.active || false)
              };
            });
            
            console.log('📝 Task updated from task_update:', {
              taskId: currentTask.id,
              stepsCount: updatedPlan.length,
              activeStep: updatedPlan.find(s => s.active)?.title
            });
            
            return {
              ...currentTask,
              plan: updatedPlan,
              status: data.status || currentTask.status
            };
          });
        }
      },
      
      'tool_result': (data: any) => {
        console.log('🔧 WebSocket tool_result received:', data);
        
        const status = data.result?.success ? '✅' : '❌';
        const logEntry = {
          message: `${status} Herramienta ${data.tool}: ${data.result?.success ? 'Éxito' : data.result?.error || 'Error'}`,
          type: data.result?.success ? 'success' as const : 'error' as const,
          timestamp: new Date(data.timestamp || Date.now())
        };
        
        setTerminalLogs(prev => [...prev, logEntry]);
      },
      
      // Mantener eventos legacy para compatibilidad
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