import React, { useState, useEffect } from 'react';
import { Task, Message, TerminalCommand } from '../types';
import { TerminalView } from './TerminalView';
import { ChatInterface } from './ChatInterface';
import { ThinkingAnimation } from './ThinkingAnimation';
import { FilesModal } from './FilesModal';
import { ShareModal } from './ShareModal';
import { AdvancedTaskManager } from './AdvancedTaskManager';
import { agentAPI, FileItem } from '../services/api';
import { useMemoryManager } from '../hooks/useMemoryManager';
import { Star, Zap } from 'lucide-react';

interface TaskViewProps {
  task: Task;
  onUpdateTask: (task: Task) => void;
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
  const logToTerminal = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
    setTerminalLogs(prev => [...prev, {
      message,
      type,
      timestamp: new Date()
    }]);
  };

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

  const handleSendMessage = (content: string) => {
    // Check if this is the first message
    const isFirstMessage = task.messages.length === 0;
    
    // Add user message
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      content,
      sender: 'user',
      timestamp: new Date()
    };

    const updatedTask = {
      ...task,
      messages: [...task.messages, userMessage],
      status: 'in-progress' as const
    };
    onUpdateTask(updatedTask);

    // If this is the first message, start environment initialization in terminal
    if (isFirstMessage) {
      // Log environment initialization steps to terminal
      logToTerminal('🚀 Initializing task environment...', 'info');
      
      setTimeout(() => {
        logToTerminal('⚙️  Setting up environment...', 'info');
      }, 500);
      
      setTimeout(() => {
        logToTerminal('📦 Installing dependencies...', 'info');
      }, 1500);
      
      setTimeout(() => {
        logToTerminal('🤖 Initializing agent...', 'info');
      }, 2500);
      
      setTimeout(() => {
        logToTerminal('✅ Environment ready! Starting task execution...', 'success');
      }, 3500);
    }

    // Simulate agent typing
    setIsTyping(true);

    // Simulate agent response after a delay
    setTimeout(() => {
      // If this is the first message, generate a plan
      if (isFirstMessage) {
        const plan = generatePlan();
        
        // Add terminal command
        const terminalCommand: TerminalCommand = {
          id: `cmd-${Date.now()}`,
          command: `analyze "${content.replace(/"/g, '\\"')}"`,
          status: 'completed'
        };

        // Add agent response
        const agentMessage: Message = {
          id: `msg-${Date.now() + 1}`,
          content: `He analizado tu tarea y he creado un plan para resolverla. Voy a comenzar a trabajar en ella ahora.`,
          sender: 'agent',
          timestamp: new Date()
        };

        onUpdateTask({
          ...updatedTask,
          plan,
          terminalCommands: [...updatedTask.terminalCommands, terminalCommand],
          messages: [...updatedTask.messages, agentMessage]
        });
      } else {
        // Add terminal command for subsequent messages
        const terminalCommand: TerminalCommand = {
          id: `cmd-${Date.now()}`,
          command: `process "${content.replace(/"/g, '\\"')}"`,
          status: 'completed'
        };

        // Add agent response
        const agentMessage: Message = {
          id: `msg-${Date.now() + 1}`,
          content: `Estoy trabajando en tu solicitud. Déjame procesar esta información.`,
          sender: 'agent',
          timestamp: new Date()
        };

        onUpdateTask({
          ...updatedTask,
          terminalCommands: [...updatedTask.terminalCommands, terminalCommand],
          messages: [...updatedTask.messages, agentMessage]
        });
      }
      setIsTyping(false);
    }, 1500);
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

  // Helper function to generate a plan based on the task description
  const generatePlan = () => {
    // This is a simplified example - in a real app, this would be generated by an AI
    return [
      {
        id: 'step-1',
        title: 'Analizar la tarea',
        completed: false,
        active: true
      },
      {
        id: 'step-2',
        title: 'Investigar soluciones',
        completed: false,
        active: false
      },
      {
        id: 'step-3',
        title: 'Implementar solución',
        completed: false,
        active: false
      },
      {
        id: 'step-4',
        title: 'Verificar resultados',
        completed: false,
        active: false
      },
      {
        id: 'step-5',
        title: 'Presentar informe',
        completed: false,
        active: false
      }
    ];
  };

  return (
    <div className="flex h-full bg-[#272728] overflow-hidden">
      {/* Chat Section with Header */}
      <div className="md:w-1/2 flex flex-col min-h-0">
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
        
        {/* Chat Interface - con altura completa disponible */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 min-h-0">
            <ChatInterface 
              messages={task.messages.map(msg => ({
                id: msg.id,
                content: msg.content,
                sender: msg.sender === 'agent' ? 'assistant' : msg.sender,
                timestamp: msg.timestamp
              }))} 
              onSendMessage={handleSendMessage} 
              isTyping={isTyping} 
              assistantName="Agente" 
              placeholder="Describe tu tarea..." 
              data-id={task.id}
              onLogToTerminal={logToTerminal}
              onUpdateMessages={(messages) => {
                const updatedTask = {
                  ...task,
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
                onUpdateTask(updatedTask);
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

      {/* Terminal Section - llega hasta arriba */}
      <div className="md:w-1/2 flex flex-col min-h-0">
        <div className="flex-1 min-h-0">
          <TerminalView 
            title="Ejecución de comandos" 
            isLive={task.status === 'in-progress'}
            plan={task.plan}
            onToggleTaskStep={toggleTaskStep}
            externalLogs={[...terminalLogs, ...externalLogs]}
            isInitializing={isInitializing}
            onInitializationComplete={onInitializationComplete}
            onInitializationLog={onInitializationLog}
            taskId={task.id}
            taskTitle={task.title}
            data-id={task.id}
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