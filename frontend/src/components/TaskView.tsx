import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  onUpdateTask: (task: Task | ((currentTask: Task) => Task)) => void; // 🚀 Support functional updates
  onUpdateTaskProgress?: (taskId: string) => void;
  isThinking: boolean;
  onTerminalResize?: (height: number) => void;
  externalLogs?: Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>;
  isInitializing?: boolean;
  onInitializationComplete?: () => void;
  onInitializationLog?: (message: string, type: 'info' | 'success' | 'error') => void;
}

export const TaskView: React.FC<TaskViewProps> = ({
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
  
  // 🚀 WebSocket integration para updates en tiempo real
  const {
    socket,
    isConnected,
    joinTaskRoom,
    leaveTaskRoom,
    addEventListeners,
    removeEventListeners,
  } = useWebSocket();

  
  // 🚀 WebSocket Effects - Gestión de conexión y eventos
  useEffect(() => {
    if (isConnected && task.id) {
      console.log('🏠 Joining task room for:', task.id);
      joinTaskRoom(task.id);

      // Configurar event listeners
      addEventListeners({
        task_started: (data) => {
          console.log('🚀 Task started:', data);
          logToTerminal('🚀 Ejecución de tarea iniciada', 'info');
        },

        task_progress: (data) => {
          console.log('⏳ Task progress:', data);
          if (data.activity) {
            logToTerminal(`⏳ ${data.activity}`, 'info');
          }
        },

        task_completed: (data) => {
          console.log('✅ Task completed:', data);
          logToTerminal('✅ Tarea completada exitosamente', 'success');
          
          // ✨ NEW: Add success completion message to chat
          const completionMessage = {
            id: `msg-${Date.now()}-completion`,
            content: `🎉 **¡Tarea completada exitosamente!**\n\nTu tarea "${task.title}" ha sido finalizada. Todos los pasos se ejecutaron correctamente.\n\n¿Te gustaría que te ayude con alguna otra cosa?`,
            sender: 'assistant' as const,
            timestamp: new Date(),
            status: {
              type: 'success' as const,
              message: 'Tarea finalizada exitosamente'
            }
          };

          // Add completion message to chat
          onUpdateTask((currentTask) => ({
            ...currentTask,
            messages: [...(currentTask.messages || []), completionMessage],
            status: 'completed' as const
          }));

          // Reload task data to get final results
          if (onTaskUpdate) {
            onTaskUpdate();
          }
        },

        task_failed: (data) => {
          console.log('❌ Task failed:', data);
          logToTerminal(`❌ Error en la tarea: ${data.error || 'Error desconocido'}`, 'error');
        },

        step_started: (data) => {
          console.log('🔄 Step started:', data);
          logToTerminal(`🔄 Iniciando: ${data.title || 'Paso'}`, 'info');
          
          // Actualizar estado del paso en el plan
          updateStepStatus(data.step_id, 'in-progress', true);
        },

        step_completed: (data) => {
          console.log('✅ Step completed:', data);
          logToTerminal(`✅ Completado: ${data.title || 'Paso'}`, 'success');
          
          // Actualizar estado del paso
          updateStepStatus(data.step_id, 'completed', false, true);
          
          // Ejecutar siguiente paso después de 1 segundo
          setTimeout(() => {
            executeNextStep();
          }, 1000);
        },

        step_failed: (data) => {
          console.log('❌ Step failed:', data);
          logToTerminal(`❌ Error en paso: ${data.title || data.data?.title || 'Paso'} - ${data.error || 'Error desconocido'}`, 'error');
          
          // Update step status in the plan
          if (task.plan && Array.isArray(task.plan)) {
            const updatedPlan = task.plan.map(step => ({
              ...step,
              status: step.id === data.step_id ? 'failed' : step.status,
              active: false,
              error: step.id === data.step_id ? data.error : step.error
            }));
            
            // Update task with new plan state
            if (onTaskUpdate) {
              onTaskUpdate();
            }
          }
        },

        plan_updated: (data) => {
          console.log('📋 Plan updated:', data);
          logToTerminal('📋 Plan de acción generado', 'info');
          
          if (data.plan && data.plan.steps) {
            const updatedTask = {
              ...task,
              plan: data.plan.steps.map((step: any, index: number) => ({
                id: step.id || `step-${index}`,
                title: step.title,
                description: step.description,
                completed: false,
                active: false,
                tool: step.tool,
                estimated_time: step.estimated_time,
                priority: step.priority,
                status: 'pending'
              }))
            };
            onUpdateTask(updatedTask);
            
            // Mostrar resumen en terminal
            logToTerminal(`📊 Plan generado: ${data.plan.steps.length} pasos`, 'info');
            logToTerminal(`⏱️ Tiempo estimado: ${data.plan.estimated_total_time || 'No especificado'}`, 'info');
            
            // NUEVA FUNCIONALIDAD: Auto-iniciar ejecución
            setTimeout(() => {
              startTaskExecution(task.id);
            }, 500); // Esperar 500ms antes de iniciar - respuesta más rápida
          }
        },

        // Duplicated event handlers removed - keeping only the first set at lines 61-125

        context_changed: (data) => {
          console.log('🔄 Context changed:', data);
          logToTerminal('🔄 Contexto de ejecución actualizado', 'info');
        },

        error: (data) => {
          console.log('❌ WebSocket error:', data);
          logToTerminal(`❌ Error: ${data.message || 'Error desconocido'}`, 'error');
        },
      });

      // Cleanup al cambiar de tarea
      return () => {
        if (task.id) {
          leaveTaskRoom(task.id);
        }
        removeEventListeners();
      };
    }
  }, [isConnected, task.id, joinTaskRoom, leaveTaskRoom, addEventListeners, removeEventListeners]);

  // Nueva función para iniciar ejecución
  const startTaskExecution = async (taskId: string) => {
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
      
      const response = await fetch(`${backendUrl}/api/agent/start-task-execution/${taskId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        logToTerminal('🚀 Iniciando ejecución automática...', 'info');
      }
    } catch (error) {
      console.error('Error starting task execution:', error);
      logToTerminal('❌ Error iniciando ejecución', 'error');
    }
  };

  // 🚀 Función de ejecución automática de pasos
  const executeNextStep = async (specificStepId?: string) => {
    if (!task.plan || task.plan.length === 0) return;
    
    // Encontrar el siguiente paso a ejecutar
    let nextStep;
    if (specificStepId) {
      nextStep = task.plan.find(step => step.id === specificStepId);
    } else {
      nextStep = task.plan.find(step => !step.completed && !step.active);
    }
    
    if (!nextStep) {
      logToTerminal('🎉 Todos los pasos completados', 'success');
      return;
    }
    
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
      
      logToTerminal(`🚀 Ejecutando: ${nextStep.title}`, 'info');
      
      const response = await fetch(`${backendUrl}/api/agent/execute-step/${task.id}/${nextStep.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          step: nextStep,
          context: {
            task_id: task.id,
            previous_steps: task.plan.filter(s => s.completed)
          }
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      logToTerminal(`📊 Resultado: ${result.summary || 'Ejecutado'}`, 'info');
      
    } catch (error) {
      console.error('Error executing step:', error);
      logToTerminal(`❌ Error ejecutando paso: ${error.message}`, 'error');
    }
  };

  const updateStepStatus = (stepId: string, status: string, active: boolean, completed?: boolean) => {
    const updatedTask = {
      ...task,
      plan: task.plan?.map(step => ({
        ...step,
        status: step.id === stepId ? status : step.status,
        active: step.id === stepId ? active : false,
        completed: completed !== undefined && step.id === stepId ? completed : step.completed
      }))
    };
    onUpdateTask(updatedTask);
    
    // Actualizar progreso
    if (onUpdateTaskProgress) {
      onUpdateTaskProgress(task.id);
    }
  };

  // Debug effects for modal states
  useEffect(() => {
    console.log('🗂️ FilesModal state changed:', showFilesModal);
  }, [showFilesModal]);

  useEffect(() => {
    console.log('🔗 ShareModal state changed:', showShareModal);
  }, [showShareModal]);

  // Memory Manager
  const {
    memoryFiles,
    addMemoryFile,
    removeMemoryFile,
    toggleMemoryFile,
    clearAllMemory
  } = useMemoryManager();
  // Función para agregar archivo a memoria
  const addFileToMemory = (file: FileItem) => {
    const memoryFile = {
      name: file.name,
      type: file.source === 'uploaded' ? 'uploaded_file' as const : 'agent_file' as const,
      content: `Archivo: ${file.name}\nTipo: ${file.mime_type}\nTamaño: ${file.size} bytes\nFecha: ${file.created_at}`,
      metadata: {
        size: file.size,
        createdAt: new Date(file.created_at),
        source: file.source || 'agent_generated',
        summary: `Archivo ${file.name} (${file.mime_type})`,
        tags: [file.mime_type?.split('/')[0] || 'unknown']
      }
    };
    
    addMemoryFile(memoryFile);
    logToTerminal(`🧠 Archivo "${file.name}" agregado a la memoria`, 'success');
  };
  const logToTerminal = useCallback((message: string, type: 'info' | 'success' | 'error' | 'warning' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
      message,
      type,
      timestamp: new Date()
    };
    
    setTerminalLogs(prev => [...prev, logEntry]);
    
    // Auto-scroll al final
    setTimeout(() => {
      if (monitorRef.current) {
        monitorRef.current.scrollTop = monitorRef.current.scrollHeight;
      }
    }, 100);
    
    console.log(`📝 Terminal log (${type}):`, message);
  }, []);

  // Función para generar enlace de compartir
  const generateShareLink = async (taskId: string): Promise<string> => {
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
      console.log('Backend URL:', backendUrl); // Debug log
      const response = await fetch(`${backendUrl}/api/agent/share`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: taskId,
          task_title: task.title,
          messages: task.messages
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.share_link;
    } catch (error) {
      console.error('Error generating share link:', error);
      throw error;
    }
  };

  // Función para obtener archivos de la tarea
  const getTaskFiles = async () => {
    try {
      const files = await agentAPI.getTaskFiles(task.id);
      setTaskFiles(files);
    } catch (error) {
      console.error('Error fetching files:', error);
      setTaskFiles([]);
    }
  };

  // Función para descargar un archivo
  const downloadFile = async (file: FileItem) => {
    try {
      const blob = await agentAPI.downloadFile(file.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  // Función para descargar todos los archivos como ZIP
  const downloadAllFiles = async () => {
    try {
      const blob = await agentAPI.downloadAllFiles(task.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${task.title}-files.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading files:', error);
    }
  };

  // Función para descargar archivos seleccionados
  const downloadSelectedFiles = async (files: FileItem[]) => {
    try {
      if (files.length === 1) {
        // Si solo hay un archivo, descargarlo directamente
        downloadFile(files[0]);
      } else {
        // Si hay múltiples archivos, crear un ZIP
        const fileIds = files.map(f => f.id);
        const blob = await agentAPI.downloadSelectedFiles(fileIds);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${task.title}-selected-files.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Error downloading selected files:', error);
      // Fallback: descargar cada archivo individualmente
      for (const file of files) {
        await downloadFile(file);
      }
    }
  };

  // Función para crear archivos de prueba
  const createTestFiles = async () => {
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/agent/create-test-files/${task.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Actualizar la lista de archivos
      setTaskFiles(data.files || []);
      
      // Mostrar mensaje de éxito
      console.log(`Se crearon ${data.files?.length || 0} archivos de prueba`);
    } catch (error) {
      console.error('Error creating test files:', error);
    }
  };

  // Cargar archivos cuando se abre el modal
  React.useEffect(() => {
    if (showFilesModal) {
      getTaskFiles();
    }
  }, [showFilesModal]);

  // Optimized: Moderate polling only when needed - FIXED browser saturation issue
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    // Solo hacer polling si la tarea tiene un plan y no está completada
    // Reducido la frecuencia del polling para evitar saturar el navegador
    if (task.plan && task.plan.length > 0 && task.status !== 'completed') {
      // Polling menos agresivo - cada 10 segundos en lugar de 1-3 segundos
      intervalId = setInterval(async () => {
        try {
          const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
          const response = await fetch(`${backendUrl}/api/agent/get-task-plan/${task.id}`);
          
          if (response.ok) {
            const planData = await response.json();
            
            // Actualizar tarea con progreso del plan
            const updatedTask = {
              ...task,
              plan: planData.plan,
              progress: planData.progress,
              status: planData.status === 'completed' ? 'completed' as const : 'in-progress' as const
            };
            
            onUpdateTask(updatedTask);
            
            // Log progreso al terminal solo si hay cambios
            if (logToTerminal && planData.progress !== task.progress) {
              logToTerminal(`📊 Progreso: ${planData.completed_steps}/${planData.total_steps} pasos (${Math.round(planData.progress)}%)`, 'info');
            }
            
            // Parar polling si está completado
            if (planData.status === 'completed') {
              clearInterval(intervalId);
              logToTerminal('✅ Plan completado exitosamente', 'success');
            }
          }
        } catch (error) {
          console.error('Error fetching plan progress:', error);
          // Stop polling on persistent errors to avoid spamming
          clearInterval(intervalId);
        }
      }, 10000); // Polling cada 10 segundos - menos agresivo
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [task.id, task.plan, task.status, task.progress, onUpdateTask, logToTerminal]);

  // Let ChatInterface handle messages and API calls directly
  // Remove the TaskView's custom handleSendMessage that blocks API calls

  // Function to generate dynamic plan from backend
  const generateDynamicPlan = async (taskContent: string) => {
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
      
      const response = await fetch(`${backendUrl}/api/agent/generate-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_title: taskContent,
          context: { dynamic_planning: true }
        })
      });

      if (response.ok) {
        const planData = await response.json();
        return planData.plan || [];
      } else {
        console.warn('Failed to generate dynamic plan from backend');
        return [];
      }
    } catch (error) {
      console.error('Error generating dynamic plan:', error);
      return [];
    }
  };

  const toggleTaskStep = (stepId: string) => {
    if (!task.plan) return;

    const currentIndex = task.plan.findIndex(s => s.id === stepId);
    const step = task.plan[currentIndex];
    
    if (!step) return;

    const updatedPlan = task.plan.map((s, index) => {
      if (index === currentIndex) {
        // Si el paso se completa, desactivarlo
        if (!s.completed) {
          return { ...s, completed: true, active: false };
        } else {
          // Si se descompleta, activarlo y desactivar todos los demás
          return { ...s, completed: false, active: true };
        }
      }
      
      // Lógica para manejar otros pasos
      if (!step.completed) {
        // Si estamos completando el paso actual
        if (index === currentIndex + 1) {
          // Activar el siguiente paso solo si no hay pasos incompletos anteriores
          const hasIncompleteStepsBefore = task.plan.slice(0, index).some(prevStep => !prevStep.completed && prevStep.id !== stepId);
          return { ...s, active: !hasIncompleteStepsBefore, completed: false };
        } else if (index > currentIndex) {
          // Desactivar todos los pasos posteriores
          return { ...s, active: false, completed: false };
        } else {
          // Mantener pasos anteriores como están
          return s;
        }
      } else {
        // Si estamos descompletando el paso actual
        if (index > currentIndex) {
          // Desactivar y descompletar todos los pasos siguientes
          return { ...s, active: false, completed: false };
        } else if (index < currentIndex) {
          // Mantener pasos anteriores completados
          return s;
        } else {
          // Desactivar todos los otros pasos activos
          return { ...s, active: false };
        }
      }
    });

    // Asegurar que solo hay un paso activo a la vez
    let hasActiveStep = false;
    const finalPlan = updatedPlan.map(s => {
      if (s.active && !hasActiveStep) {
        hasActiveStep = true;
        return s;
      } else if (s.active && hasActiveStep) {
        return { ...s, active: false };
      }
      return s;
    });

    // Calculate progress based on completed steps
    const completedSteps = finalPlan.filter(step => step.completed).length;
    const totalSteps = finalPlan.length;
    const planProgress = Math.round((completedSteps / totalSteps) * 100);
    
    // Determine status based on progress
    let newStatus = task.status;
    if (planProgress === 100 && task.status !== 'completed') {
      newStatus = 'completed';
    } else if (planProgress > 0 && task.status === 'pending') {
      newStatus = 'in-progress';
    }

    onUpdateTask({
      ...task,
      plan: finalPlan,
      progress: planProgress,
      status: newStatus
    });

    // Llamar a la función de actualización de progreso si está disponible
    if (onUpdateTaskProgress) {
      setTimeout(() => onUpdateTaskProgress(task.id), 100);
    }
  };

  return (
    <div className="flex h-full bg-[#272728] overflow-hidden relative">
      {/* Chat Section with Header - FIXED: Always visible with proper width */}
      <div className="w-1/2 flex flex-col min-h-0" style={{minWidth: '50%', maxWidth: '50%'}}>
        {/* Header de la tarea - solo para el chat */}
        <div className="border-b border-[rgba(255,255,255,0.08)] px-4 py-2.5 bg-[#383739] flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-[#DADADA]">{task.title}</h2>
              <div className="text-xs text-[#7f7f7f]">
                Creado el {new Date(task.createdAt).toLocaleString()}
              </div>
            </div>
            <div className="flex items-center gap-2">

              <button
                onClick={(e) => {
                  console.log('🗂️ Files button clicked');
                  e.preventDefault();
                  e.stopPropagation();
                  setShowFilesModal(true);
                }}
                className="flex items-center gap-1 px-3 py-1.5 bg-[#4A4A4C] hover:bg-[#5A5A5C] rounded-lg text-xs text-[#DADADA] transition-colors"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Archivos
              </button>
              <button
                onClick={(e) => {
                  console.log('🔗 Share button clicked');
                  e.preventDefault();
                  e.stopPropagation();
                  setShowShareModal(true);
                }}
                className="flex items-center gap-1 px-3 py-1.5 bg-[#4A4A4C] hover:bg-[#5A5A5C] rounded-lg text-xs text-[#DADADA] transition-colors"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                </svg>
                Compartir
              </button>
              <button
                onClick={(e) => {
                  console.log('⭐ Favorite button clicked');
                  e.preventDefault();
                  e.stopPropagation();
                  const updatedTask = {
                    ...task,
                    isFavorite: !task.isFavorite
                  };
                  onUpdateTask(updatedTask);
                }}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                  task.isFavorite 
                    ? 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400' 
                    : 'bg-[#4A4A4C] hover:bg-[#5A5A5C] text-[#DADADA]'
                }`}
                title={task.isFavorite ? 'Quitar de favoritos' : 'Agregar a favoritos'}
              >
                <Star className={`w-3 h-3 ${task.isFavorite ? 'fill-yellow-400 text-yellow-400' : ''}`} />
                {task.isFavorite ? 'Favorito' : 'Favorito'}
              </button>
            </div>
          </div>
        </div>
        
        {/* 🚀 Agent Status - mostrar estado del agente en tiempo real */}
        
        {/* Chat Interface - con altura completa disponible */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 min-h-0">
            <ChatInterface 
              messages={task.messages.map(msg => ({
                id: msg.id,
                content: msg.content,
                sender: msg.sender === 'agent' ? 'assistant' : msg.sender,
                timestamp: msg.timestamp,
                attachments: msg.attachments,
                status: msg.status,
                toolResults: msg.toolResults,
                searchData: msg.searchData,
                uploadData: msg.uploadData,
                links: msg.links
              }))} 
              onSendMessage={async (message) => {
                console.log('🔥 TASKVIEW DEBUG: onSendMessage called with:', message);
                console.log('🔥 TASKVIEW DEBUG: Current task state:', {
                  taskId: task.id,
                  title: task.title,
                  messagesCount: task.messages?.length || 0,
                  hasPlan: !!(task.plan && task.plan.length > 0)
                });
                
                // 🔧 CRITICAL FIX: Actually process the message instead of just logging
                try {
                  console.log('🔥 TASKVIEW DEBUG: Starting message processing...');
                  
                  // Call the backend to process the message
                  const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
                  console.log('🔥 TASKVIEW DEBUG: Backend URL:', backendUrl);
                  
                  const response = await fetch(`${backendUrl}/api/agent/generate-plan`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                      message: message,
                      task_id: task.id,
                      context: 'nueva_tarea'
                    })
                  });
                  
                  console.log('🔥 TASKVIEW DEBUG: Backend response status:', response.status);
                  
                  if (response.ok) {
                    const result = await response.json();
                    console.log('🔥 TASKVIEW DEBUG: Backend result:', result);
                    
                    // Update the task with the generated plan
                    if (result.plan) {
                      console.log('🔥 TASKVIEW DEBUG: Updating task with plan:', result.plan);
                      onUpdateTask((currentTask: Task) => ({
                        ...currentTask,
                        plan: result.plan,
                        title: result.enhanced_title || `${currentTask.title}`,
                        messages: [...(currentTask.messages || []), {
                          id: `msg-${Date.now()}`,
                          content: message,
                          sender: 'user',
                          timestamp: new Date()
                        }]
                      }));
                    }
                  } else {
                    console.error('🔥 TASKVIEW ERROR: Backend response failed:', response.status);
                  }
                  
                } catch (error) {
                  console.error('🔥 TASKVIEW ERROR: Message processing failed:', error);
                }
              }}
              isTyping={isTyping} 
              assistantName="Agente" 
              placeholder="Describe tu tarea..." 
              data-id={task.id}
              hasExistingPlan={!!(task.plan && task.plan.length > 0 && task.plan.some(step => step.id && step.title))}
              onLogToTerminal={logToTerminal}
              onUpdateMessages={(messages) => {
                console.log('📨 TaskView: onUpdateMessages called with:', {
                  messagesCount: messages.length,
                  messages: messages.map(m => ({ 
                    id: m.id, 
                    sender: m.sender, 
                    content: m.content.substring(0, 50) + '...' 
                  }))
                });
                
                // 🚀 CRITICAL FIX: Use functional update to prevent race conditions
                // This ensures we always get the most current task state
                onUpdateTask((currentTask: Task) => {
                  // Only update the task that matches our current task ID
                  if (currentTask.id !== task.id) {
                    return currentTask; // Return unchanged for other tasks
                  }
                  
                  console.log('📨 RACE CONDITION FIX - Using functional update for messages:', {
                    taskId: currentTask.id,
                    currentTitle: currentTask.title,
                    currentMessagesCount: currentTask.messages?.length || 0,
                    newMessagesCount: messages.length,
                    currentPlan: currentTask.plan?.length || 0,
                    fixApplied: 'Functional update prevents message loss during plan generation'
                  });
                  
                  const updatedTask = {
                    ...currentTask, // Use MOST CURRENT task state (preserves title, plan, etc.)
                    messages: messages.map(msg => ({
                      id: msg.id,
                      content: msg.content,
                      sender: msg.sender === 'assistant' ? 'agent' : msg.sender,
                      timestamp: msg.timestamp,
                      attachments: msg.attachments,
                      status: msg.status,
                      toolResults: msg.toolResults,
                      searchData: msg.searchData,
                      uploadData: msg.uploadData,
                      links: msg.links
                    }))
                  };
                  
                  console.log('📨 TaskView: Updated task with messages (PRESERVING ALL CURRENT STATE):', {
                    taskId: updatedTask.id,
                    preservedTitle: updatedTask.title,
                    preservedPlan: updatedTask.plan?.length || 0,
                    newMessagesCount: updatedTask.messages.length,
                    BEFORE_UPDATE: currentTask.messages?.length || 0,
                    AFTER_UPDATE: updatedTask.messages.length,
                    raceconditionFixed: true
                  });
                  
                  return updatedTask;
                });
                
                console.log('📨 TaskView: onUpdateTask called successfully with functional update');
              }}
              onTaskPlanGenerated={(plan) => {
                console.log('📋 TaskView: Plan received from ChatInterface:', plan);
                
                // 🚀 CRITICAL FIX: Use functional update to get most current task state
                // This prevents the race condition where plan generation overwrites enhanced title AND MESSAGES
                onUpdateTask((currentTask: Task) => {
                  // Only update the task that matches our current task ID
                  if (currentTask.id !== task.id) {
                    return currentTask; // Return unchanged for other tasks
                  }
                  
                  console.log('📋 RACE CONDITION FIX - Using functional update to preserve enhanced title AND MESSAGES:', {
                    taskId: currentTask.id,
                    currentTitle: currentTask.title,
                    currentMessagesCount: currentTask.messages?.length || 0,
                    planSteps: plan.steps?.length,
                    fixApplied: 'Functional update preserves latest state INCLUDING messages'
                  });
                  
                  // Convertir el plan del backend al formato del frontend
                  const frontendPlan = plan.steps.map((step: any) => ({
                    id: step.id,
                    title: step.title,
                    description: step.description,
                    tool: step.tool,
                    status: step.status,
                    estimated_time: step.estimated_time,
                    completed: step.completed,
                    active: step.active
                  }));
                  
                  // Actualizar la tarea con el plan generado, preservando el título más actual Y MENSAJES
                  const updatedTask = {
                    ...currentTask, // Use MOST CURRENT task state (includes enhanced title AND messages)
                    plan: frontendPlan,
                    planGenerated: true,
                    status: 'in-progress' as const,
                    totalSteps: plan.total_steps,
                    estimatedTime: plan.estimated_total_time,
                    taskType: plan.task_type,
                    complexity: plan.complexity,
                    progress: 0 // Iniciar con 0% ya que los pasos no están completados
                  };
                  
                  console.log('📋 TaskView: Updated task with plan (ENHANCED TITLE AND MESSAGES PRESERVED):', {
                    taskId: updatedTask.id,
                    preservedTitle: updatedTask.title,
                    preservedMessagesCount: updatedTask.messages?.length || 0,
                    preservedMessages: updatedTask.messages?.map(m => ({ sender: m.sender, content: m.content.substring(0, 50) + '...' })) || [],
                    planSteps: updatedTask.plan?.length,
                    raceconditionFixed: true
                  });
                  
                  return updatedTask;
                });
                
                // Log al terminal
                if (logToTerminal && plan.steps?.length) {
                  logToTerminal(`📋 Plan generado: ${plan.steps.length} pasos definidos`, 'success');
                  
                  // 🚀 CRITICAL FIX: Auto-start execution after plan generation
                  console.log('🚀 Auto-starting task execution after plan generation in TaskView');
                  setTimeout(() => {
                    startTaskExecution(task.id);
                  }, 500); // Wait 500ms for UI to update - faster response
                }
              }}
              onTitleGenerated={(enhancedTitle) => {
                console.log('📝 NUEVA TAREA FIX - TaskView: Enhanced title received from ChatInterface:', enhancedTitle);
                console.log('📝 NUEVA TAREA FIX - TaskView: Current task:', task);
                
                // Actualizar el título de la tarea con el título mejorado
                const updatedTask = {
                  ...task,
                  title: enhancedTitle
                };
                
                console.log('📝 NUEVA TAREA FIX - TaskView: Updating task with enhanced title:', updatedTask);
                console.log('📝 NUEVA TAREA FIX - TaskView: About to call onUpdateTask...');
                onUpdateTask(updatedTask);
                console.log('📝 NUEVA TAREA FIX - TaskView: onUpdateTask called successfully');
                
                // Log al terminal
                if (logToTerminal) {
                  logToTerminal(`📝 Título mejorado generado: "${enhancedTitle}"`, 'success');
                }
              }}
              onIconGenerated={(suggestedIcon) => {
                console.log('🎯 TaskView: Icon suggestion received from ChatInterface:', suggestedIcon);
                
                // Actualizar el icono de la tarea con el icono sugerido por LLM
                onUpdateTask((currentTask) => {
                  if (currentTask.id !== task.id) {
                    return currentTask;
                  }
                  
                  const updatedTask = {
                    ...currentTask,
                    iconType: suggestedIcon // 🎯 ACTUALIZAR ICONO CON SUGERENCIA DEL LLM
                  };
                  
                  console.log('🎯 TaskView: Updated task with LLM-suggested icon:', {
                    taskId: updatedTask.id,
                    newIcon: suggestedIcon,
                    previousIcon: currentTask.iconType || 'none'
                  });
                  
                  return updatedTask;
                });
                
                // Log al terminal
                if (logToTerminal) {
                  logToTerminal(`🎯 Icono inteligente seleccionado: "${suggestedIcon}"`, 'success');
                }
              }}
              onTaskReset={() => {
                // Reset task-specific state when switching tasks - MORE COMPREHENSIVE RESET
                console.log('🔄 Task reset triggered for task:', task.id);
                
                // Clear terminal logs for new task
                setTerminalLogs([]);
                
                // Reset any file-related state
                setTaskFiles([]);
                
                // Reset any typing state
                setIsTyping(false);
                
                // Reset modal states
                setShowFilesModal(false);
                setShowShareModal(false);
                
                console.log('🖥️ Terminal/computer state fully reset for task:', task.id);
              }}
              isNewTask={task.messages.length === 0}
            />
          </div>
        </div>
      </div>

      {/* Terminal Section - FIXED: Always visible with proper width */}
      <div className="w-1/2 flex flex-col min-h-0" style={{minWidth: '50%', maxWidth: '50%'}}>
        <div className="flex-1 min-h-0">
          <TerminalView 
            title="Ejecución de comandos" 
            isLive={task.status === 'in-progress'}
            plan={task.plan}
            onToggleTaskStep={toggleTaskStep}
            onPlanUpdate={(updatedPlan) => {
              // Update the task with the updated plan
              onUpdateTask((currentTask) => ({
                ...currentTask,
                plan: updatedPlan
              }));
            }}
            externalLogs={[...terminalLogs, ...externalLogs]}
            isInitializing={isInitializing}
            onInitializationComplete={onInitializationComplete}
            onInitializationLog={onInitializationLog}
            taskId={task.id}
            taskTitle={task.title}
            data-id={task.id}
            executionData={task.executionData}
          />
        </div>
      </div>

      {/* Files Modal */}
      <FilesModal
        isOpen={showFilesModal}
        onClose={() => setShowFilesModal(false)}
        files={taskFiles}
        onDownload={downloadFile}
        onDownloadAll={downloadAllFiles}
        onDownloadSelected={downloadSelectedFiles}
        taskTitle={task.title}
        memoryFiles={memoryFiles}
        onAddMemoryFile={addMemoryFile}
        onRemoveMemoryFile={removeMemoryFile}
        onToggleMemoryFile={toggleMemoryFile}
        onClearAllMemory={clearAllMemory}
        onAddFileToMemory={addFileToMemory}
      />

      {/* Share Modal */}
      <ShareModal
        isOpen={showShareModal}
        onClose={() => setShowShareModal(false)}
        taskTitle={task.title}
        taskId={task.id}
        onGenerateLink={generateShareLink}
      />


    </div>
  );
};