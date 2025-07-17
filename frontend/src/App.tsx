import React, { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { VanishInput } from './components/VanishInput';
import { TaskView } from './components/TaskView';
import { ConfigPanel } from './components/ConfigPanel';
import { FileUploadModal } from './components/FileUploadModal';
import { LoadingPlaceholder, MessageLoadingPlaceholder } from './components/LoadingPlaceholder';
import { Task, Message, AppState, AgentConfig } from './types';
import { generateRandomIcon } from './components/TaskIcon';
import { Globe, FileText, Presentation, Smartphone, Search, Gamepad2 } from 'lucide-react';

// Configuración por defecto del agente
const defaultConfig: AgentConfig = {
  systemPrompt: `Eres un agente general altamente inteligente y útil. Tu objetivo es ayudar a los usuarios a completar sus tareas de manera eficiente y precisa.

Características:
- Analiza cuidadosamente cada solicitud
- Planifica los pasos necesarios para resolver la tarea
- Utiliza las herramientas disponibles cuando sea necesario
- Proporciona respuestas claras y detalladas
- Mantén un tono profesional pero amigable

Herramientas disponibles:
- Shell: Para ejecutar comandos del sistema
- Web Search: Para buscar información en internet
- File Manager: Para gestionar archivos y directorios

Siempre explica lo que estás haciendo y por qué, para que el usuario pueda entender tu proceso de pensamiento.`,
  memory: {
    enabled: true,
    maxMessages: 20,
    contextWindow: 4096
  },
  ollama: {
    enabled: true,
    model: "llama3.1:8b",
    temperature: 0.7,
    maxTokens: 2048,
    endpoint: "https://78d08925604a.ngrok-free.app"
  },
  openrouter: {
    enabled: false,
    model: "openai/gpt-4o-mini",
    apiKey: "",
    temperature: 0.7,
    maxTokens: 2048,
    endpoint: "https://openrouter.ai/api/v1"
  },
  tools: {
    shell: {
      enabled: true,
      allowedCommands: ["ls", "pwd", "cat", "grep", "find", "curl"],
      timeout: 30
    },
    webSearch: {
      enabled: true,
      maxResults: 5,
      timeout: 15
    },
    fileManager: {
      enabled: true,
      allowedPaths: ["/tmp", "/home", "/var/log"],
      maxFileSize: 10
    }
  }
};

// Función para generar ideas dinámicas basadas en contexto
const generateDynamicIdeas = async () => {
  try {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
    
    const response = await fetch(`${backendUrl}/api/agent/generate-suggestions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        context: { user_context: true, generate_dynamic_suggestions: true }
      })
    });

    if (response.ok) {
      const suggestionsData = await response.json();
      return suggestionsData.suggestions || [];
    } else {
      console.warn('Failed to generate dynamic suggestions, using empty array');
      return [];
    }
  } catch (error) {
    console.error('Error generating dynamic suggestions:', error);
    return [];
  }
};

export function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [dynamicIdeas, setDynamicIdeas] = useState<any[]>([]);
  const [appState, setAppState] = useState<AppState>({
    sidebarCollapsed: false,
    terminalSize: 300,
    isThinking: false,
    config: defaultConfig
  });
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isTaskCreating, setIsTaskCreating] = useState(false);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [initializingTaskId, setInitializingTaskId] = useState<string | null>(null);
  const [initializationLogs, setInitializationLogs] = useState<Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>>([]);

  // Cargar ideas dinámicas solo cuando no hay tareas activas
  useEffect(() => {
    if (!activeTaskId && dynamicIdeas.length === 0) {
      generateDynamicIdeas().then(ideas => {
        setDynamicIdeas(ideas.slice(0, 3)); // Mostrar solo 3 ideas
      });
    }
  }, [activeTaskId, dynamicIdeas.length]);
  
  const createTask = async (title: string) => {
    setIsTaskCreating(true);
    
    // Reset any thinking state
    setAppState(prev => ({
      ...prev,
      isThinking: false
    }));
    
    const newTask: Task = {
      id: `task-${Date.now()}`,
      title,
      createdAt: new Date(),
      status: 'pending',
      messages: [],
      terminalCommands: [], // Start with empty terminal commands for each task
      isFavorite: false,
      progress: 0 // Initialize progress at 0
    };
    setTasks(prev => [newTask, ...prev]);
    setActiveTaskId(newTask.id);
    setIsTaskCreating(false);
    
    // Inicializar el proceso de inicialización
    setInitializingTaskId(newTask.id);
    setInitializationLogs([]);
    console.log('✅ Task created, starting initialization:', newTask.id);
    
    return newTask;
  };

  // Función para manejar logs de inicialización
  const handleInitializationLog = (message: string, type: 'info' | 'success' | 'error') => {
    const logEntry = {
      message,
      type,
      timestamp: new Date()
    };
    
    setInitializationLogs(prev => [...prev, logEntry]);
    console.log(`📝 Initialization log (${type}):`, message);
  };

  // Función para completar la inicialización
  const handleInitializationComplete = () => {
    console.log('✅ Task initialization completed');
    setInitializingTaskId(null);
    
    // Agregar log final de inicialización completada
    handleInitializationLog('🎉 Environment ready! You can start working now.', 'success');
    
    // Opcional: Limpiar logs después de un tiempo
    setTimeout(() => {
      setInitializationLogs([]);
    }, 10000); // Limpiar logs después de 10 segundos
  };

  const deleteTask = (taskId: string) => {
    setTasks(prev => prev.filter(task => task.id !== taskId));
    
    // Si la tarea eliminada era la activa, seleccionar otra o ninguna
    if (activeTaskId === taskId) {
      const remainingTasks = tasks.filter(task => task.id !== taskId);
      setActiveTaskId(remainingTasks.length > 0 ? remainingTasks[0].id : null);
    }
  };

  const toggleSidebar = () => {
    setAppState(prev => ({
      ...prev,
      sidebarCollapsed: !prev.sidebarCollapsed
    }));
  };

  const handleConfigChange = (newConfig: AgentConfig) => {
    setAppState(prev => ({
      ...prev,
      config: newConfig
    }));
    
    // Aquí podrías enviar la configuración al backend
    console.log('Configuración actualizada:', newConfig);
  };

  const handleTerminalResize = (height: number) => {
    setAppState(prev => ({
      ...prev,
      terminalSize: height
    }));
  };

  const updateTask = (updatedTask: Task) => {
    setTasks(prev => prev.map(task => 
      task.id === updatedTask.id ? updatedTask : task
    ));
    
    // Simular pensamiento del agente solo si hay cambios de estado importantes
    if (updatedTask.status === 'in-progress' && updatedTask.messages.length > 0) {
      setAppState(prev => ({ ...prev, isThinking: true }));
      
      // Quitar el estado de pensamiento después de un tiempo
      setTimeout(() => {
        setAppState(prev => ({ ...prev, isThinking: false }));
      }, 2000);
    }
  };

  // Nueva función específica para actualizar el progreso basado en el plan
  const updateTaskProgress = (taskId: string) => {
    setTasks(prev => prev.map(task => {
      if (task.id !== taskId || !task.plan || task.plan.length === 0) {
        return task;
      }
      
      const completedSteps = task.plan.filter(step => step.completed).length;
      const totalSteps = task.plan.length;
      const planProgress = Math.round((completedSteps / totalSteps) * 100);
      
      // Determinar el status basado en el progreso
      let newStatus = task.status;
      if (planProgress === 100 && task.status !== 'completed') {
        newStatus = 'completed';
      } else if (planProgress > 0 && task.status === 'pending') {
        newStatus = 'in-progress';
      }
      
      return {
        ...task,
        progress: planProgress,
        status: newStatus
      };
    }));
  };

// Función para generar planes dinámicos usando IA
const generateDynamicTaskPlan = async (taskTitle: string) => {
  try {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
    
    // Solicitar al backend generar un plan específico para esta tarea
    const response = await fetch(`${backendUrl}/api/agent/generate-plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_title: taskTitle,
        context: { dynamic_planning: true }
      })
    });

    if (response.ok) {
      const planData = await response.json();
      return planData.plan || [];
    } else {
      console.warn('Failed to generate dynamic plan, creating minimal plan');
      return [];
    }
  } catch (error) {
    console.error('Error generating dynamic plan:', error);
    return [];
  }
};

  const handleDynamicIdea = (idea: any) => {
    createTask(idea.title);
  };

  const handleAttachFiles = () => {
    console.log('🎯 ATTACH FILES CLICKED - Setting showFileUpload to true');
    setShowFileUpload(true);
    console.log('✅ showFileUpload state set to true');
  };

  const handleFilesUploaded = async (files: FileList) => {
    console.log('📎 Files uploaded:', files);
    
    // Create a new task for the uploaded files
    const newTask = await createTask("Archivos adjuntos");
    
    // Upload files to the backend and get file information
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
      console.log('🔗 Backend URL for file upload:', backendUrl);
      console.log('📤 Uploading files to backend');
      
      const formData = new FormData();
      formData.append('task_id', newTask.id);
      
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
        console.log(`📄 Adding file ${i + 1}: ${files[i].name}`);
      }

      const response = await fetch(`${backendUrl}/api/agent/upload-files`, {
        method: 'POST',
        body: formData
      });

      console.log('📡 File upload response status:', response.status);

      if (response.ok) {
        const uploadData = await response.json();
        console.log('✅ Files uploaded successfully:', uploadData);
        
        // Create user message with file attachment info showing the files
        const filesList = uploadData.files.map((file: any) => 
          `• **${file.name}** (${Math.round(file.size / 1024)} KB)`
        ).join('\n');
        
        const userMessage = {
          id: `msg-${Date.now()}`,
          content: `He adjuntado ${files.length} archivo(s):\n\n${filesList}\n\nPor favor, procesa estos archivos.`,
          sender: 'user' as const,
          timestamp: new Date(),
          attachments: uploadData.files.map((file: any) => ({
            id: file.id,
            name: file.name,
            size: String(file.size),
            type: file.mime_type,
            url: `${backendUrl}/api/agent/download/${file.id}`
          }))
        };
        
        // Create assistant response message to show files were processed
        const assistantMessage = {
          id: `msg-${Date.now() + 1}`,
          content: 'file_upload_success', // Special marker to trigger file display
          sender: 'assistant' as const,
          timestamp: new Date(),
          attachments: uploadData.files.map((file: any) => ({
            id: file.id,
            name: file.name,
            size: String(file.size),
            type: file.mime_type,
            url: `${backendUrl}/api/agent/download/${file.id}`
          })),
          status: {
            type: 'success' as const,
            message: `${uploadData.files.length} archivo${uploadData.files.length !== 1 ? 's' : ''} listo${uploadData.files.length !== 1 ? 's' : ''} para usar`
          }
        };
        
        // Generar plan específico para archivos adjuntos
        const fileAttachmentPlan = await generateDynamicTaskPlan('Archivos adjuntos');
        
        // Marcar pasos como completados para archivos adjuntos
        const completedFileAttachmentPlan = fileAttachmentPlan.map((step, index) => ({
          ...step,
          completed: true,
          active: false
        }));
        
        // Actualizar progreso en el backend
        const updateFileAttachmentProgress = async () => {
          try {
            const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
            for (let i = 0; i < fileAttachmentPlan.length; i++) {
              const step = fileAttachmentPlan[i];
              await fetch(`${backendUrl}/api/agent/update-task-progress`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  task_id: newTask.id,
                  step_id: step.id,
                  completed: true
                })
              });
            }
          } catch (error) {
            console.error('Error updating file attachment progress:', error);
          }
        };
        
        // Actualizar progreso
        updateFileAttachmentProgress();
        
        const updatedTask = {
          ...newTask,
          messages: [userMessage, assistantMessage],
          plan: completedFileAttachmentPlan, // Usar plan completado
          status: 'completed' as const, // Mark as completed since files are uploaded
          progress: 100 // Set to 100% when files are uploaded and ready
        };
        
        setTasks(prev => prev.map(task => 
          task.id === newTask.id ? updatedTask : task
        ));
      } else {
        console.error('❌ File upload error response:', response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('💥 Error uploading files:', error);
      
      // Create error message if upload fails
      const errorMessage = {
        id: `msg-${Date.now()}`,
        content: 'Hubo un error al subir los archivos. Por favor, intenta de nuevo.',
        sender: 'assistant' as const,
        timestamp: new Date(),
        status: {
          type: 'error' as const,
          message: 'Error de upload'
        }
      };
      
      const updatedTask = {
        ...newTask,
        messages: [errorMessage],
        status: 'failed' as const,
        progress: 0
      };
      
      setTasks(prev => prev.map(task => 
        task.id === newTask.id ? updatedTask : task
      ));
    }
    
    setShowFileUpload(false);
  };

  const activeTask = tasks.find(task => task.id === activeTaskId);

  // Optimized keyboard shortcuts
  useEffect(() => {
    const handleKeyboard = (e: KeyboardEvent) => {
      // Escape para cerrar configuración
      if (e.key === 'Escape' && isConfigOpen) {
        setIsConfigOpen(false);
      }
    };

    if (isConfigOpen) { // Solo agregar listener si está abierto
      window.addEventListener('keydown', handleKeyboard);
      return () => window.removeEventListener('keydown', handleKeyboard);
    }
  }, [isConfigOpen]);

  // Optimized initial loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitialLoading(false);
    }, 1000); // 1 second loading simulation

    return () => clearTimeout(timer);
  }, []); // Sin dependencias innecesarias

  return (
    <div className="flex h-screen w-full bg-[#272728] text-[#DADADA]" style={{ fontFamily: "'Segoe UI Variable Display', 'Segoe UI', system-ui, -apple-system, sans-serif", fontWeight: 400 }}>
      {isInitialLoading ? (
        // Loading placeholder for initial app load
        <div className="flex w-full">
          {/* Sidebar placeholder */}
          <div className="w-80 bg-[#212122] border-r border-[rgba(255,255,255,0.08)] p-4">
            <LoadingPlaceholder type="card" className="mb-4" />
            <LoadingPlaceholder type="text" lines={1} className="mb-4" />
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <LoadingPlaceholder key={i} type="text" lines={2} height="h-12" />
              ))}
            </div>
          </div>
          
          {/* Main content placeholder */}
          <div className="flex-1 flex flex-col">
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="text-center max-w-2xl w-full space-y-8">
                {/* Placeholder para "Bienvenido a Mitosis" */}
                <LoadingPlaceholder type="text" lines={1} height="h-12" className="mb-4" />
                
                {/* Placeholder para "¿Qué puedo hacer por ti?" */}
                <LoadingPlaceholder type="text" lines={1} height="h-12" className="mb-6" />
                
                {/* Placeholder para la caja de chat */}
                <LoadingPlaceholder type="card" className="mb-6" />
                
                {/* Placeholder para TODOS los botones juntos */}
                <LoadingPlaceholder type="card" height="h-12" className="w-full" />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          <Sidebar 
            tasks={tasks} 
            activeTaskId={activeTaskId} 
            onTaskSelect={setActiveTaskId} 
            onCreateTask={createTask}
            onDeleteTask={deleteTask}
            onUpdateTask={updateTask}
            onConfigOpen={() => setIsConfigOpen(true)}
            isCollapsed={appState.sidebarCollapsed}
            onToggleCollapse={toggleSidebar}
          />
          
          <div className="flex-1 flex flex-col overflow-hidden">
            {activeTask ? (
              <TaskView 
                task={activeTask} 
                onUpdateTask={updateTask}
                onUpdateTaskProgress={updateTaskProgress}
                isThinking={appState.isThinking}
                onTerminalResize={handleTerminalResize}
                externalLogs={initializationLogs}
                isInitializing={initializingTaskId === activeTask.id}
                onInitializationComplete={handleInitializationComplete}
                onInitializationLog={handleInitializationLog}
              />
            ) : (
              <div className="flex flex-1 items-center justify-center bg-[#272728] p-8">
                <div className="text-left max-w-4xl w-full">
                  {/* Título unificado - separado 15% hacia arriba del input */}
                  <div className="mb-12 text-left">
                    <h2 className="text-5xl font-bold text-white leading-none mb-2" 
                        style={{ fontFamily: "'Libre Baskerville', serif" }}>
                      Bienvenido a Mitosis
                    </h2>
                    <p className="text-5xl font-bold text-[#ACACAC] leading-none" 
                       style={{ fontFamily: "'Libre Baskerville', serif" }}>
                      ¿Qué puedo hacer por ti?
                    </p>
                  </div>
                  
                  {/* Caja de texto con botones internos */}
                  <div className="mb-8 max-w-4xl mx-auto">
                    {isTaskCreating ? (
                      <div className="w-full p-4 bg-[rgba(255,255,255,0.06)] rounded-lg border border-[rgba(255,255,255,0.08)]">
                        <LoadingPlaceholder type="text" lines={1} height="h-6" className="mb-2" />
                        <div className="text-sm text-[#ACACAC]">Creando nueva tarea...</div>
                      </div>
                    ) : (
                      <VanishInput
                        onSendMessage={async (message) => {
                          if (message.trim()) {
                            console.log('🚀 Creating task with message:', message.trim());
                            
                            // PASO 1: Crear la tarea INMEDIATAMENTE y actualizarla en el estado
                            const newTask = await createTask(message.trim());
                            console.log('✅ Task created successfully:', newTask.id);
                            
                            // PASO 2: Crear mensaje del usuario INMEDIATAMENTE
                            const userMessage = {
                              id: `msg-${Date.now()}`,
                              content: message.trim(),
                              sender: 'user' as const,
                              timestamp: new Date()
                            };
                            
                            // PASO 3: Actualizar la tarea CON el mensaje del usuario INMEDIATAMENTE
                            const basicTaskUpdate = {
                              ...newTask,
                              messages: [userMessage],
                              status: 'in-progress' as const,
                              progress: 10
                            };
                            
                            setTasks(prev => prev.map(task => 
                              task.id === newTask.id ? basicTaskUpdate : task
                            ));
                            
                            console.log('✅ Task updated in sidebar with user message');
                            
                            // PASO 4: Procesar backend de manera asíncrona (sin bloquear la UI)
                            try {
                              const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
                              
                              const response = await fetch(`${backendUrl}/api/agent/chat`, {
                                method: 'POST',
                                headers: {
                                  'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                  message: message.trim(),
                                  context: { task_id: newTask.id }
                                })
                              });

                              if (response.ok) {
                                const chatResponse = await response.json();
                                console.log('✅ Backend response received:', chatResponse);
                                
                                // Crear mensaje del agente
                                const agentMessage = {
                                  id: `msg-${Date.now() + 1}`,
                                  content: chatResponse.response || "Tarea completada exitosamente.",
                                  sender: 'agent' as const,
                                  timestamp: new Date()
                                };
                                
                                // Actualizar tarea con respuesta del agente
                                const finalTaskUpdate = {
                                  ...basicTaskUpdate,
                                  messages: [userMessage, agentMessage],
                                  status: 'completed' as const,
                                  progress: 100
                                };
                                
                                setTasks(prev => prev.map(task => 
                                  task.id === newTask.id ? finalTaskUpdate : task
                                ));
                                
                                console.log('✅ Task completed and updated in sidebar');
                                
                              } else {
                                console.error('❌ Backend error response:', response.status);
                                // Mantener tarea con solo el mensaje del usuario
                                const errorTaskUpdate = {
                                  ...basicTaskUpdate,
                                  status: 'failed' as const,
                                  progress: 0
                                };
                                
                                setTasks(prev => prev.map(task => 
                                  task.id === newTask.id ? errorTaskUpdate : task
                                ));
                              }
                            } catch (error) {
                              console.error('💥 Error processing backend:', error);
                              // Mantener tarea con solo el mensaje del usuario  
                              const errorTaskUpdate = {
                                ...basicTaskUpdate,
                                status: 'failed' as const,
                                progress: 0
                              };
                              
                              setTasks(prev => prev.map(task => 
                                task.id === newTask.id ? errorTaskUpdate : task
                              ));
                            }
                          }
                        }}
                        placeholder="Escribe tu tarea aquí..."
                        className="w-full text-lg"
                        showInternalButtons={true}
                        onAttachFiles={handleAttachFiles}
                        onWebSearch={async (searchQuery) => {
                          console.log('🌐 WebSearch received query:', searchQuery);
                          if (searchQuery && searchQuery.trim().length > 0) {
                            console.log('🌐 Creating WebSearch task with query:', searchQuery);
                            
                            // PASO 1: Crear la tarea INMEDIATAMENTE con prefijo WebSearch (ya incluido en searchQuery)
                            const newTask = await createTask(searchQuery);
                            console.log('✅ WebSearch task created:', newTask.id);
                            
                            // PASO 2: Crear mensaje del usuario INMEDIATAMENTE
                            const userMessage = {
                              id: `msg-${Date.now()}`,
                              content: searchQuery,
                              sender: 'user' as const,
                              timestamp: new Date()
                            };
                            
                            // PASO 3: Actualizar la tarea CON el mensaje del usuario INMEDIATAMENTE
                            const basicTaskUpdate = {
                              ...newTask,
                              messages: [userMessage],
                              status: 'in-progress' as const,
                              progress: 10
                            };
                            
                            setTasks(prev => prev.map(task => 
                              task.id === newTask.id ? basicTaskUpdate : task
                            ));
                            
                            console.log('✅ WebSearch task updated in sidebar');
                            
                            // PASO 4: Procesar backend de manera asíncrona
                            try {
                              const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
                              
                              const response = await fetch(`${backendUrl}/api/agent/chat`, {
                                method: 'POST',
                                headers: {
                                  'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                  message: searchQuery,
                                  context: { task_id: newTask.id }
                                })
                              });

                              if (response.ok) {
                                const chatResponse = await response.json();
                                console.log('✅ WebSearch backend response received:', chatResponse);
                                
                                // Crear mensaje del agente
                                const agentMessage = {
                                  id: `msg-${Date.now() + 1}`,
                                  content: chatResponse.response || "Búsqueda web completada exitosamente.",
                                  sender: 'agent' as const,
                                  timestamp: new Date(),
                                  searchData: chatResponse.search_data
                                };
                                
                                // Actualizar tarea con respuesta del agente
                                const finalTaskUpdate = {
                                  ...basicTaskUpdate,
                                  messages: [userMessage, agentMessage],
                                  status: 'completed' as const,
                                  progress: 100
                                };
                                
                                setTasks(prev => prev.map(task => 
                                  task.id === newTask.id ? finalTaskUpdate : task
                                ));
                                
                                console.log('✅ WebSearch task completed and updated in sidebar');
                                
                              } else {
                                console.error('❌ WebSearch backend error:', response.status);
                                const errorTaskUpdate = {
                                  ...basicTaskUpdate,
                                  status: 'failed' as const,
                                  progress: 0
                                };
                                
                                setTasks(prev => prev.map(task => 
                                  task.id === newTask.id ? errorTaskUpdate : task
                                ));
                              }
                            } catch (error) {
                              console.error('💥 Error in WebSearch:', error);
                              const errorTaskUpdate = {
                                ...basicTaskUpdate,
                                status: 'failed' as const,
                                progress: 0
                              };
                              
                              setTasks(prev => prev.map(task => 
                                task.id === newTask.id ? errorTaskUpdate : task
                              ));
                            }
                          }
                        }}
                        onDeepSearch={async (searchQuery) => {
                          console.log('🔬 DeepSearch received query:', searchQuery);
                          if (searchQuery && searchQuery.trim().length > 0) {
                            console.log('🔬 Creating DeepSearch task with query:', searchQuery);
                            
                            // PASO 1: Crear la tarea INMEDIATAMENTE con prefijo DeepResearch (ya incluido en searchQuery)
                            const newTask = await createTask(searchQuery);
                            console.log('✅ DeepSearch task created:', newTask.id);
                            
                            // PASO 2: Crear mensaje del usuario INMEDIATAMENTE
                            const userMessage = {
                              id: `msg-${Date.now()}`,
                              content: searchQuery,
                              sender: 'user' as const,
                              timestamp: new Date()
                            };
                            
                            // PASO 3: Actualizar la tarea CON el mensaje del usuario INMEDIATAMENTE
                            const basicTaskUpdate = {
                              ...newTask,
                              messages: [userMessage],
                              status: 'in-progress' as const,
                              progress: 10
                            };
                            
                            setTasks(prev => prev.map(task => 
                              task.id === newTask.id ? basicTaskUpdate : task
                            ));
                            
                            console.log('✅ DeepSearch task updated in sidebar');
                            
                            // PASO 4: Procesar backend de manera asíncrona
                            try {
                              const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
                              
                              const response = await fetch(`${backendUrl}/api/agent/chat`, {
                                method: 'POST',
                                headers: {
                                  'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                  message: searchQuery,
                                  context: { task_id: newTask.id }
                                })
                              });

                              if (response.ok) {
                                const chatResponse = await response.json();
                                console.log('✅ DeepSearch backend response received:', chatResponse);
                                
                                // Crear mensaje del agente
                                const agentMessage = {
                                  id: `msg-${Date.now() + 1}`,
                                  content: chatResponse.response || "Investigación profunda completada exitosamente.",
                                  sender: 'agent' as const,
                                  timestamp: new Date(),
                                  searchData: chatResponse.search_data
                                };
                                
                                // Actualizar tarea con respuesta del agente
                                const finalTaskUpdate = {
                                  ...basicTaskUpdate,
                                  messages: [userMessage, agentMessage],
                                  status: 'completed' as const,
                                  progress: 100
                                };
                                
                                setTasks(prev => prev.map(task => 
                                  task.id === newTask.id ? finalTaskUpdate : task
                                ));
                                
                                console.log('✅ DeepSearch task completed and updated in sidebar');
                                
                              } else {
                                console.error('❌ DeepSearch backend error:', response.status);
                                const errorTaskUpdate = {
                                  ...basicTaskUpdate,
                                  status: 'failed' as const,
                                  progress: 0
                                };
                                
                                setTasks(prev => prev.map(task => 
                                  task.id === newTask.id ? errorTaskUpdate : task
                                ));
                              }
                            } catch (error) {
                              console.error('💥 Error in DeepSearch:', error);
                              const errorTaskUpdate = {
                                ...basicTaskUpdate,
                                status: 'failed' as const,
                                progress: 0
                              };
                              
                              setTasks(prev => prev.map(task => 
                                task.id === newTask.id ? errorTaskUpdate : task
                              ));
                            }
                          }
                        }}
                        onVoiceInput={() => console.log('Voice input clicked')}
                      />
                    )}
                  </div>
                  
                  {/* Ideas dinámicas - solo si hay ideas cargadas */}
                  {dynamicIdeas.length > 0 && (
                    <div className="mb-12">
                      <div className="flex items-center justify-center gap-3">
                        {dynamicIdeas.map((idea, index) => (
                          <button
                            key={index}
                            onClick={() => handleDynamicIdea(idea)}
                            disabled={isTaskCreating}
                            className="flex items-center gap-2 px-4 py-2 bg-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.1)] rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <Search className={`w-4 h-4 text-blue-400`} />
                            <span className="text-sm text-[#DADADA]">{idea.title}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Panel de Configuración */}
          <ConfigPanel
            config={appState.config}
            onConfigChange={handleConfigChange}
            onClose={() => setIsConfigOpen(false)}
            isOpen={isConfigOpen}
          />

          {/* File Upload Modal */}
          <FileUploadModal
            isOpen={showFileUpload}
            onClose={() => setShowFileUpload(false)}
            onFilesUploaded={handleFilesUploaded}
          />
        </>
      )}
    </div>
  );
}