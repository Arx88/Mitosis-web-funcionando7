import React, { useEffect, useState, useCallback } from 'react';
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
    endpoint: "https://bef4a4bb93d1.ngrok-free.app"
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
    const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
    
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
  
  const createTask = async (title: string, iconType?: string): Promise<Task> => {
    console.log('🔥 APP.TSX: createTask called with title:', title, 'iconType:', iconType);
    console.log('🔥 APP.TSX: current tasks length:', tasks.length);
    
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
      progress: 0, // Initialize progress at 0
      iconType: iconType // 🎯 SET ICON TYPE FROM PARAMETER
    };
    
    // ✅ FIXED: Set activeTaskId immediately without setTimeout to prevent race conditions
    setTasks(prev => {
      const updatedTasks = [newTask, ...prev];
      console.log('🎯 TASK CREATION - Tasks updated:', updatedTasks.length);
      return updatedTasks;
    });
    
    // Set activeTaskId immediately after updating tasks
    setActiveTaskId(newTask.id);
    console.log('🚀 CRITICAL FIX: ActiveTaskId set immediately:', newTask.id);
    
    setIsTaskCreating(false);
    
    // 🐛 DEBUG: Logging task creation state
    console.log('🎯 TASK CREATION DEBUG:', {
      newTaskId: newTask.id,
      setActiveTaskIdCalled: true,
      tasksUpdate: 'Added to beginning of array'
    });
    
    // Inicializar el proceso de inicialización
    setInitializingTaskId(newTask.id);
    setInitializationLogs([]);
    console.log('✅ Task created, starting initialization:', newTask.id);
    
    return newTask;
  };
  // ✅ FIXED: Consolidated task creation with message to avoid race conditions AND generate enhanced title
  const createTaskWithMessage = async (messageContent: string) => {
    setIsTaskCreating(true);
    
    // Reset any thinking state
    setAppState(prev => ({
      ...prev,
      isThinking: false
    }));
    
    // Create user message
    const userMessage = {
      id: `msg-${Date.now()}`,
      content: messageContent,
      sender: 'user' as const,
      timestamp: new Date()
    };
    
    // Create task with temporary title (will be enhanced)
    const newTask: Task = {
      id: `task-${Date.now()}`,
      title: messageContent, // Temporary title, will be enhanced
      createdAt: new Date(),
      status: 'active', // Set as active since it has a message
      messages: [userMessage], // Include message immediately
      terminalCommands: [],
      isFavorite: false,
      progress: 0
    };
    
    // ✅ ATOMIC OPERATION: Update tasks and activeTaskId together
    setTasks(prev => [newTask, ...prev]);
    setActiveTaskId(newTask.id);
    
    // Initialize task process
    setInitializingTaskId(newTask.id);
    setInitializationLogs([]);
    
    // 🚀 NEW: Generate enhanced title AND plan with backend API
    try {
      console.log('📝 Generating enhanced title and plan for task:', newTask.id);
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
      const initResponse = await fetch(`${backendUrl}/api/agent/generate-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_title: messageContent.trim(),
          task_id: newTask.id
        })
      });
      
      if (initResponse.ok) {
        const initData = await initResponse.json();
        console.log('✅ Backend response received:', initData);
        
        // ✨ Process complete response: enhanced_title AND plan
        let updatedTask = { ...newTask };
        
        // Update title if available
        if (initData.enhanced_title) {
          console.log('📝 Updating task with enhanced title:', initData.enhanced_title);
          updatedTask.title = initData.enhanced_title;
          newTask.title = initData.enhanced_title; // Update return object
        }
        
        // 🚀 NEW: Process plan if available (same logic as ChatInterface)
        if (initData.plan) {
          console.log('📋 Processing plan for homepage task:', initData.plan);
          
          // Convert backend plan to frontend format (same as TaskView)
          const frontendPlan = initData.plan.map((step: any) => ({
            id: step.id,
            title: step.title,
            description: step.description,
            tool: step.tool,
            status: step.status,
            estimated_time: step.estimated_time,
            completed: step.completed || false,
            active: step.active || false
          }));
          
          // Update task with plan and set to in-progress
          updatedTask = {
            ...updatedTask,
            plan: frontendPlan,
            status: 'in-progress',
            progress: 0
          };
          
          console.log('✅ Plan processed for homepage task, steps:', frontendPlan.length);
        }
        
        // Update tasks state with complete data
        setTasks(prev => prev.map(task => 
          task.id === newTask.id ? updatedTask : task
        ));
        
        console.log('✅ Task updated with enhanced title and plan');
      } else {
        console.warn('⚠️ Failed to generate enhanced title and plan, using original message');
      }
    } catch (error) {
      console.error('❌ Error generating enhanced title and plan:', error);
    }
    
    setIsTaskCreating(false);
    
    console.log('🚀 CONSOLIDATED TASK CREATION:', {
      taskId: newTask.id,
      hasMessage: true,
      status: 'in-progress',
      activeTaskIdSet: true,
      titleGenerated: true,
      planGenerated: true,
      finalTitle: newTask.title
    });
    
    return newTask;
  };

  // Función para manejar logs de inicialización
  const handleInitializationLog = useCallback((message: string, type: 'info' | 'success' | 'error') => {
    const logEntry = {
      message,
      type,
      timestamp: new Date()
    };
    
    setInitializationLogs(prev => [...prev, logEntry]);
    console.log(`📝 Initialization log (${type}):`, message);
  }, []);

  // Función para completar la inicialización
  const handleInitializationComplete = useCallback(() => {
    console.log('✅ Task initialization completed');
    setInitializingTaskId(null);
    
    // Agregar log final de inicialización completada
    handleInitializationLog('🎉 Environment ready! You can start working now.', 'success');
    
    // Opcional: Limpiar logs después de un tiempo
    setTimeout(() => {
      setInitializationLogs([]);
    }, 10000); // Limpiar logs después de 10 segundos
  }, []);

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

  const updateTask = (updatedTaskOrFunction: Task | ((currentTask: Task) => Task)) => {
    // 🚀 RACE CONDITION FIX: Support functional updates to prevent stale state issues
    if (typeof updatedTaskOrFunction === 'function') {
      console.log('🚀 RACE CONDITION FIX - App.tsx updateTask called with FUNCTION (prevents stale state)');
      
      setTasks(prev => {
        const taskToUpdate = prev.find(t => t.id === (prev.find(task => task.id) as Task)?.id);
        if (!taskToUpdate) {
          console.error('❌ Task not found for functional update');
          return prev;
        }
        
        // Find the task to update by checking which task is being modified
        let updatedTaskId: string | null = null;
        const newTasks = prev.map(task => {
          try {
            const potentialUpdate = updatedTaskOrFunction(task);
            if (potentialUpdate !== task) {
              updatedTaskId = task.id;
              console.log('🚀 FUNCTIONAL UPDATE - Task updated:', {
                taskId: task.id,
                oldTitle: task.title,
                newTitle: potentialUpdate.title,
                functionalUpdateApplied: true
              });
              return potentialUpdate;
            }
            return task;
          } catch (error) {
            return task; // Skip this task if update function doesn't apply
          }
        });
        
        return newTasks;
      });
      return;
    }
    
    // Original behavior for direct Task objects
    const updatedTask = updatedTaskOrFunction as Task;
    console.log('🐛 NUEVA TAREA FIX - App.tsx updateTask called with:', updatedTask.id, updatedTask.title);
    
    // 🔍 STACK TRACE - Para encontrar qué está sobrescribiendo el título
    console.trace('🕵️ WHO IS CALLING updateTask? Stack trace:');
    
    setTasks(prev => {
      const newTasks = prev.map(task => 
        task.id === updatedTask.id ? updatedTask : task
      );
      
      // Debug: Check if the task was actually updated
      const originalTask = prev.find(t => t.id === updatedTask.id);
      const updatedTaskInArray = newTasks.find(t => t.id === updatedTask.id);
      
      console.log('🐛 NUEVA TAREA FIX - Task update comparison:', {
        taskId: updatedTask.id,
        originalTitle: originalTask?.title,
        newTitle: updatedTaskInArray?.title,
        titleChanged: originalTask?.title !== updatedTaskInArray?.title,
        updateSource: 'updateTask function'
      });
      
      return newTasks;
    });
    
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

  const handleDynamicIdea = (idea: any) => {
    // ✅ FIXED: Use consolidated function for task creation
    createTaskWithMessage(idea.title);
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
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
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
        
        // Generar plan completado para archivos adjuntos (simple)
        const completedFileAttachmentPlan = [
          {
            id: 'file-step-1',
            title: 'Archivos procesados',
            description: 'Archivos adjuntos listos para usar',
            completed: true,
            active: false,
            tool: 'file_manager'
          }
        ];
        
        // Actualizar progreso simplificado
        const updateFileAttachmentProgress = async () => {
          // Simplificado - ya no hay múltiples pasos que actualizar
          console.log('✅ File attachment progress completed');
        };
        
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
        
        // ✅ CRITICAL FIX: Set activeTaskId to transition to TaskView
        setActiveTaskId(newTask.id);
        console.log('✅ File upload completed, TaskView activated:', newTask.id);
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
      
      // ✅ CRITICAL FIX: Set activeTaskId even on error to show error state
      setActiveTaskId(newTask.id);
      console.log('⚠️ File upload failed, but TaskView activated to show error:', newTask.id);
    }
    
    setShowFileUpload(false);
  };

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

  // Remove artificial loading delay - set loading to false immediately
  useEffect(() => {
    setIsInitialLoading(false);
  }, []);

  const activeTask = tasks.find(task => task.id === activeTaskId);

  // 🐛 DEBUG: Logging critical render state
  console.log('🔍 RENDER DEBUG - App.tsx render:', {
    activeTaskId,
    tasksLength: tasks.length,
    activeTask: activeTask ? `Found: ${activeTask.id} - "${activeTask.title}"` : 'Not found',
    condition: `activeTask=${!!activeTask}, activeTaskId=${!!activeTaskId}`,
    renderResult: activeTask && activeTaskId ? 'TaskView' : 'Homepage'
  });

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
            {activeTask && activeTaskId ? (
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
                          console.log('🎯 Homepage: Creating task with initial message');
                          if (message.trim()) {
                            // ✅ FIXED: Create task with message in one atomic operation
                            const newTask = await createTaskWithMessage(message.trim());
                            console.log('✅ Task created with initial message:', newTask.id);
                          }
                        }}
                        placeholder="Escribe tu tarea aquí..."
                        className="w-full text-lg"
                        showInternalButtons={true}
                        onAttachFiles={handleAttachFiles}
                        onWebSearch={async (searchQuery) => {
                          console.log('🌐 WebSearch: Creating task with message');
                          if (searchQuery && searchQuery.trim().length > 0) {
                            // ✅ FIXED: Use consolidated function
                            const newTask = await createTaskWithMessage(searchQuery);
                            console.log('✅ WebSearch task created:', newTask.id);
                          }
                        }}
                        onDeepSearch={async (searchQuery) => {
                          console.log('🔬 DeepSearch: Creating task with message');
                          if (searchQuery && searchQuery.trim().length > 0) {
                            // ✅ FIXED: Use consolidated function
                            const newTask = await createTaskWithMessage(searchQuery);
                            console.log('✅ DeepSearch task created:', newTask.id);
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