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
    model: "llama3.2",
    temperature: 0.7,
    maxTokens: 2048,
    endpoint: "http://localhost:11434"
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

// Ideas sugeridas para el usuario - Más pequeñas y elegantes
const suggestedIdeas = [
  {
    icon: Globe,
    title: "Página web",
    color: "text-blue-400"
  },
  {
    icon: Presentation,
    title: "Presentación",
    color: "text-green-400"
  },
  {
    icon: Smartphone,
    title: "App",
    color: "text-purple-400"
  },
  {
    icon: Search,
    title: "Investigación",
    color: "text-orange-400"
  },
  {
    icon: Gamepad2,
    title: "Juego",
    color: "text-red-400"
  }
];

export function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [hasCreatedExampleTasks, setHasCreatedExampleTasks] = useState(false);
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
  
  const createTask = async (title: string) => {
    // Reset any previous task state before creating new task
    setActiveTaskId(null);
    setIsTaskCreating(true);
    
    // Reset terminal/computer state for new task - MORE COMPREHENSIVE RESET
    console.log('🔄 Resetting terminal and computer state for new task');
    
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
    
    // Removed automatic test file creation to prevent mockup files from appearing
    console.log('✅ Task created without automatic file generation:', newTask.id);
    console.log('🖥️ Terminal/computer state reset for new task');
    setIsTaskCreating(false);
    
    return newTask;
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

  // Función para generar planes específicos según el tipo de tarea
  const generateTaskPlan = (taskTitle: string) => {
    if (taskTitle.includes('[WebSearch]')) {
      return [
        { id: 'ws-1', title: 'Inicializar búsqueda web', completed: true, active: false },
        { id: 'ws-2', title: 'Analizar consulta del usuario', completed: true, active: false },
        { id: 'ws-3', title: 'Realizar búsqueda en fuentes web', completed: true, active: false },
        { id: 'ws-4', title: 'Procesar resultados encontrados', completed: true, active: false },
        { id: 'ws-5', title: 'Generar resumen de resultados', completed: true, active: false }
      ];
    } else if (taskTitle.includes('[DeepResearch]')) {
      return [
        { id: 'dr-1', title: 'Preparar investigación profunda', completed: true, active: false },
        { id: 'dr-2', title: 'Recopilar fuentes múltiples', completed: false, active: true },
        { id: 'dr-3', title: 'Analizar contenido de fuentes', completed: false, active: false },
        { id: 'dr-4', title: 'Sintetizar hallazgos clave', completed: false, active: false },
        { id: 'dr-5', title: 'Generar reporte académico', completed: false, active: false }
      ];
    } else if (taskTitle.includes('Archivos adjuntos')) {
      return [
        { id: 'fa-1', title: 'Recibir archivos del usuario', completed: true, active: false },
        { id: 'fa-2', title: 'Validar formato de archivos', completed: true, active: false },
        { id: 'fa-3', title: 'Procesar contenido de archivos', completed: true, active: false },
        { id: 'fa-4', title: 'Organizar archivos en sistema', completed: true, active: false },
        { id: 'fa-5', title: 'Confirmar disponibilidad', completed: true, active: false }
      ];
    } else {
      // Plan genérico para otras tareas
      return [
        { id: 'gen-1', title: 'Analizar la tarea', completed: false, active: true },
        { id: 'gen-2', title: 'Investigar soluciones', completed: false, active: false },
        { id: 'gen-3', title: 'Implementar solución', completed: false, active: false },
        { id: 'gen-4', title: 'Verificar resultados', completed: false, active: false },
        { id: 'gen-5', title: 'Presentar informe', completed: false, active: false }
      ];
    }
  };

  const handleSuggestedIdea = (idea: typeof suggestedIdeas[0]) => {
    // Reset any previous task state before creating new task
    setActiveTaskId(null);
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
        const fileAttachmentPlan = generateTaskPlan('Archivos adjuntos');
        
        const updatedTask = {
          ...newTask,
          messages: [userMessage, assistantMessage],
          plan: fileAttachmentPlan, // Asignar plan específico
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

  // Remove example tasks - no longer needed
  // useEffect(() => {
  //   if (!hasCreatedExampleTasks && tasks.length === 0) {
  //     const exampleTasks = [
  //       'Tarea Estilo Clásico - Bordes suaves y colores tradicionales',
  //       'Tarea Estilo Moderno - Líneas limpias y efectos de sombra',
  //       'Tarea Estilo Neon - Efectos brillantes y colores vibrantes',
  //       'Tarea Estilo Minimal - Limpio y minimalista',
  //       'Tarea Estilo Elegante - Gradientes suaves y tipografía refinada',
  //       'Tarea Estilo Colorido - Múltiples colores y efectos alegres',
  //       'Tarea Estilo Profesional - Sobrio y empresarial',
  //       'Tarea Estilo Futurista - Formas geométricas y efectos tech',
  //       'Tarea Estilo Vintage - Colores cálidos y efectos retro',
  //       'Tarea Estilo Gaming - Efectos dinámicos y colores vibrantes'
  //     ];

  //     const newTasks = exampleTasks.map((title, index) => ({
  //       id: `example-task-${index + 1}`,
  //       title,
  //       createdAt: new Date(),
  //       status: 'pending' as const,
  //       messages: [],
  //       terminalCommands: [],
  //       isFavorite: false
  //     }));

  //     setTasks(newTasks);
  //     setHasCreatedExampleTasks(true);
  //   }
  // }, [hasCreatedExampleTasks, tasks.length]);

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
                            // Reset any previous task state before creating new task
                            setActiveTaskId(null);
                            
                            // Crear la tarea con el texto exacto del usuario
                            const newTask = await createTask(message.trim());
                            // Inmediatamente enviar el mensaje del usuario a la tarea creada
                            setTimeout(() => {
                              if (newTask) {
                                const userMessage = {
                                  id: `msg-${Date.now()}`,
                                  content: message.trim(),
                                  sender: 'user' as const,
                                  timestamp: new Date()
                                };
                                
                                // Generar plan genérico para tareas normales
                                const genericPlan = generateTaskPlan(message.trim());
                                
                                const updatedTask = {
                                  ...newTask,
                                  messages: [userMessage],
                                  plan: genericPlan, // Asignar plan genérico
                                  status: 'in-progress' as const,
                                  progress: 0 // Start at 0, progress will be based on plan completion
                                };
                                
                                setTasks(prev => prev.map(task => 
                                  task.id === newTask.id ? updatedTask : task
                                ));
                              }
                            }, 100);
                          }
                        }}
                        placeholder="Escribe tu tarea aquí..."
                        className="w-full text-lg"
                        showInternalButtons={true}
                        onAttachFiles={handleAttachFiles}
                        onWebSearch={async (inputText) => {
                          console.log('🌐 Web search clicked with text:', inputText);
                          if (inputText && inputText.trim().length > 0) {
                            // Create task with WebSearch prefix
                            const newTask = await createTask(`[WebSearch] ${inputText.trim()}`);
                            
                            // Send the message to the backend API
                            try {
                              const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
                              console.log('🔗 Backend URL for WebSearch:', backendUrl);
                              console.log('📤 Sending WebSearch request to backend');
                              
                              const response = await fetch(`${backendUrl}/api/agent/chat`, {
                                method: 'POST',
                                headers: {
                                  'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                  message: `[WebSearch] ${inputText.trim()}`,
                                  context: { task_id: newTask.id }
                                })
                              });

                              console.log('📡 WebSearch response status:', response.status);

                              if (response.ok) {
                                const chatResponse = await response.json();
                                console.log('✅ WebSearch response received:', chatResponse);
                                
                                // Generar plan específico para WebSearch
                                const webSearchPlan = generateTaskPlan(`[WebSearch] ${inputText.trim()}`);
                                
                                const userMessage = {
                                  id: `msg-${Date.now()}`,
                                  content: `[WebSearch] ${inputText.trim()}`,
                                  sender: 'user' as const,
                                  timestamp: new Date()
                                };
                                
                                const agentMessage = {
                                  id: `msg-${Date.now() + 1}`,
                                  content: chatResponse.response || 'Realizando búsqueda web...',
                                  sender: 'agent' as const,
                                  timestamp: new Date(),
                                  searchData: chatResponse.search_data
                                };
                                
                                const updatedTask = {
                                  ...newTask,
                                  messages: [userMessage, agentMessage],
                                  plan: webSearchPlan, // Asignar plan específico
                                  status: 'completed' as const, // WebSearch se completa inmediatamente
                                  progress: 100 // 100% porque todas las etapas del plan están completadas
                                };
                                
                                setTasks(prev => prev.map(task => 
                                  task.id === newTask.id ? updatedTask : task
                                ));
                              } else {
                                console.error('❌ WebSearch error response:', response.status, response.statusText);
                              }
                            } catch (error) {
                              console.error('💥 Error executing web search:', error);
                              // Fallback to basic task creation
                              const userMessage = {
                                id: `msg-${Date.now()}`,
                                content: `[WebSearch] ${inputText.trim()}`,
                                sender: 'user' as const,
                                timestamp: new Date()
                              };
                              
                              const updatedTask = {
                                ...newTask,
                                messages: [userMessage],
                                status: 'in-progress' as const,
                                progress: 10
                              };
                              
                              setTasks(prev => prev.map(task => 
                                task.id === newTask.id ? updatedTask : task
                              ));
                            }
                          }
                        }}
                        onDeepSearch={async (inputText) => {
                          console.log('🔬 Deep search clicked with text:', inputText);
                          if (inputText && inputText.trim().length > 0) {
                            // Create task with DeepResearch prefix
                            const newTask = await createTask(`[DeepResearch] ${inputText.trim()}`);
                            
                            // Send the message to the backend API
                            try {
                              const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
                              console.log('🔗 Backend URL for DeepSearch:', backendUrl);
                              console.log('📤 Sending DeepSearch request to backend');
                              
                              const response = await fetch(`${backendUrl}/api/agent/chat`, {
                                method: 'POST',
                                headers: {
                                  'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                  message: `[DeepResearch] ${inputText.trim()}`,
                                  context: { task_id: newTask.id }
                                })
                              });

                              console.log('📡 DeepSearch response status:', response.status);

                              if (response.ok) {
                                const chatResponse = await response.json();
                                console.log('✅ DeepSearch response received:', chatResponse);
                                
                                // Generar plan específico para DeepResearch
                                const deepResearchPlan = generateTaskPlan(`[DeepResearch] ${inputText.trim()}`);
                                
                                const userMessage = {
                                  id: `msg-${Date.now()}`,
                                  content: `[DeepResearch] ${inputText.trim()}`,
                                  sender: 'user' as const,
                                  timestamp: new Date()
                                };
                                
                                const agentMessage = {
                                  id: `msg-${Date.now() + 1}`,
                                  content: chatResponse.response || 'Iniciando investigación profunda...',
                                  sender: 'agent' as const,
                                  timestamp: new Date(),
                                  searchData: chatResponse.search_data
                                };
                                
                                const updatedTask = {
                                  ...newTask,
                                  messages: [userMessage, agentMessage],
                                  plan: deepResearchPlan.map(step => ({ ...step, completed: true, active: false })), // Marcar como completado
                                  status: 'completed' as const, // DeepSearch se completa inmediatamente
                                  progress: 100 // 100% porque el backend ya devolvió el resultado completo
                                };
                                
                                setTasks(prev => prev.map(task => 
                                  task.id === newTask.id ? updatedTask : task
                                ));
                              } else {
                                console.error('❌ DeepSearch error response:', response.status, response.statusText);
                              }
                            } catch (error) {
                              console.error('💥 Error executing deep search:', error);
                              // Fallback to basic task creation
                              const userMessage = {
                                id: `msg-${Date.now()}`,
                                content: `[DeepResearch] ${inputText.trim()}`,
                                sender: 'user' as const,
                                timestamp: new Date()
                              };
                              
                              const updatedTask = {
                                ...newTask,
                                messages: [userMessage],
                                status: 'in-progress' as const,
                                progress: 10
                              };
                              
                              setTasks(prev => prev.map(task => 
                                task.id === newTask.id ? updatedTask : task
                              ));
                            }
                          }
                        }}
                        onVoiceInput={() => console.log('Voice input clicked')}
                      />
                    )}
                  </div>
                  
                  {/* Ideas sugeridas - pequeñas y en una fila */}
                  <div className="mb-12">
                    <div className="flex items-center justify-center gap-3">
                      {suggestedIdeas.map((idea, index) => (
                        <button
                          key={index}
                          onClick={() => handleSuggestedIdea(idea)}
                          disabled={isTaskCreating}
                          className="flex items-center gap-2 px-4 py-2 bg-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.1)] rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <idea.icon className={`w-4 h-4 ${idea.color}`} />
                          <span className="text-sm text-[#DADADA]">{idea.title}</span>
                        </button>
                      ))}
                    </div>
                  </div>
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