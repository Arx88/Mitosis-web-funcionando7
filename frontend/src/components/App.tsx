import React, { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TaskView } from './components/TaskView';
import { ConfigPanel } from './components/ConfigPanel';
import { VanishInput } from './components/VanishInput';
import { Task, AgentConfig, AppState } from './types';
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

// Ideas sugeridas para el usuario - Más pequeñas y elegantes
const suggestedIdeas = [
  {
    icon: Globe,
    title: "Página web",
    color: "text-blue-400",
    taskIconType: "web"
  },
  {
    icon: Presentation,
    title: "Presentación",
    color: "text-green-400",
    taskIconType: "presentacion"
  },
  {
    icon: Smartphone,
    title: "App",
    color: "text-purple-400",
    taskIconType: "app"
  },
  {
    icon: Search,
    title: "Investigación",
    color: "text-orange-400",
    taskIconType: "investigacion"
  },
  {
    icon: Gamepad2,
    title: "Juego",
    color: "text-red-400",
    taskIconType: "juego"
  }
];

export function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [appState, setAppState] = useState<AppState>({
    sidebarCollapsed: false,
    terminalSize: 300,
    isThinking: false,
    config: defaultConfig
  });
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  
  const createTask = async (title: string, iconType?: string) => {
    const newTask: Task = {
      id: `task-${Date.now()}`,
      title,
      createdAt: new Date(),
      status: 'pending',
      messages: [],
      terminalCommands: [],
      plan: [], // Initialize with empty plan
      isFavorite: false,
      iconType: iconType // Agregar el tipo de icono
    };
    setTasks(prev => [...prev, newTask]);
    setActiveTaskId(newTask.id);
    
    // Generate plan automatically for the new task
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                     import.meta.env.REACT_APP_BACKEND_URL || 
                     process.env.REACT_APP_BACKEND_URL || 
                     'http://localhost:8001';
      
      console.log('🎯 Generating plan for task:', title);
      const planResponse = await fetch(`${backendUrl}/api/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: title
        })
      });

      if (planResponse.ok) {
        const planData = await planResponse.json();
        console.log('✅ Plan generated:', planData);
        
        // CRÍTICO: Usar el task_id que devuelve el backend
        const backendTaskId = planData.task_id;
        console.log('🆔 Using backend task ID:', backendTaskId);
        
        // Update the newTask with backend ID and plan
        const updatedTask: Task = {
          ...newTask,
          id: backendTaskId, // USAR ID DEL BACKEND
          title: planData.enhanced_title || title,
          plan: planData.plan || [],
          status: 'ready' as const
        };
        
        setTasks(prev => prev.map(task => 
          task.id === newTask.id ? updatedTask : task
        ));

        // Start automatic execution using BACKEND ID
        console.log('🚀 Starting automatic execution for task:', backendTaskId);
        const executionResponse = await fetch(`${backendUrl}/api/agent/start-task-execution/${backendTaskId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            plan: planData.plan,
            task_title: title
          })
        });

        if (executionResponse.ok) {
          console.log('✅ Task execution started successfully');
          // Update task status to in-progress
          setTasks(prev => prev.map(task => 
            task.id === newTask.id ? { ...task, status: 'in-progress' as const } : task
          ));
        } else {
          console.error('❌ Failed to start task execution:', executionResponse.status);
        }
      } else {
        console.error('❌ Failed to generate plan:', planResponse.status);
      }
    } catch (error) {
      console.error('❌ Error in automatic plan generation and execution:', error);
    }
    
    // Crear archivos automáticamente para la nueva tarea
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                     import.meta.env.REACT_APP_BACKEND_URL || 
                     process.env.REACT_APP_BACKEND_URL || 
                     'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/agent/create-test-files/${newTask.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        console.log(`Archivos creados automáticamente para la tarea: ${newTask.title}`);
      }
    } catch (error) {
      console.error('Error creating files for new task:', error);
    }
    
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

  const handleConfigChange = async (newConfig: AgentConfig) => {
    // Aplicar configuración al estado local
    setAppState(prev => ({
      ...prev,
      config: newConfig
    }));
    
    // Enviar configuración al backend para aplicar dinámicamente
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                     import.meta.env.REACT_APP_BACKEND_URL || 
                     process.env.REACT_APP_BACKEND_URL;
                     
      console.log('🔧 Enviando nueva configuración al backend...');
      
      const response = await fetch(`${backendUrl}/api/agent/config/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          config: newConfig
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Configuración aplicada exitosamente:', result);
      } else {
        console.error('❌ Error aplicando configuración:', await response.text());
      }
    } catch (error) {
      console.error('❌ Error enviando configuración al backend:', error);
    }
    
    console.log('🔧 Configuración actualizada:', newConfig);
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
    
    // Simular pensamiento del agente
    if (updatedTask.status === 'in-progress') {
      setAppState(prev => ({ ...prev, isThinking: true }));
      
      // Quitar el estado de pensamiento después de un tiempo
      setTimeout(() => {
        setAppState(prev => ({ ...prev, isThinking: false }));
      }, 2000);
    }
  };

  const handleSuggestedIdea = (idea: typeof suggestedIdeas[0]) => {
    createTask(idea.title, idea.taskIconType);
  };

  const activeTask = tasks.find(task => task.id === activeTaskId);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyboard = (e: KeyboardEvent) => {
      // Ctrl/Cmd + B para toggle sidebar
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        toggleSidebar();
      }
      
      // Ctrl/Cmd + , para abrir configuración
      if ((e.ctrlKey || e.metaKey) && e.key === ',') {
        e.preventDefault();
        setIsConfigOpen(true);
      }
      
      // Escape para cerrar configuración
      if (e.key === 'Escape' && isConfigOpen) {
        setIsConfigOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyboard);
    return () => window.removeEventListener('keydown', handleKeyboard);
  }, [isConfigOpen]);

  return (
    <div className="flex h-screen w-full bg-[#272728] text-[#DADADA] font-sans">
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
            isThinking={appState.isThinking}
            onTerminalResize={handleTerminalResize}
          />
        ) : (
          <div className="flex flex-1 items-center justify-center bg-[#272728] p-8">
            <div className="text-left max-w-4xl w-full">
              {/* Título unificado - mismo tamaño y fuente */}
              <div className="mb-12 text-left">
                <h2 className="text-5xl font-bold text-white leading-tight mb-2" 
                    style={{ fontFamily: "'Libre Baskerville', serif" }}>
                  Bienvenido a Mitosis
                </h2>
                <p className="text-5xl font-bold text-[#ACACAC] leading-tight" 
                   style={{ fontFamily: "'Libre Baskerville', serif" }}>
                  ¿Qué puedo hacer por ti?
                </p>
              </div>
              
              {/* Caja de texto con botones internos */}
              <div className="mb-8 max-w-4xl mx-auto">
                <VanishInput
                  onSendMessage={async (message) => {
                    if (message.trim()) {
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
                          
                          const updatedTask = {
                            ...newTask,
                            messages: [userMessage],
                            status: 'in-progress' as const
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
                  onAttachFiles={() => console.log('Attach files clicked')}
                  onWebSearch={() => console.log('Web search clicked')}
                  onDeepSearch={() => console.log('Deep search clicked')}
                  onVoiceInput={() => console.log('Voice input clicked')}
                />
              </div>
              
              {/* Ideas sugeridas - pequeñas y en una fila */}
              <div className="mb-12">
                <div className="flex items-center justify-center gap-3">
                  {suggestedIdeas.map((idea, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestedIdea(idea)}
                      className="flex items-center gap-2 px-4 py-2 bg-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.1)] rounded-lg border border-[rgba(255,255,255,0.08)] hover:border-[rgba(255,255,255,0.15)] transition-all duration-200"
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
    </div>
  );
}