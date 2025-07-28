import React, { useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { VanishInput } from './components/VanishInput';
import { TaskView } from './components/TaskView';
import { ConfigPanel } from './components/ConfigPanel';
import { FileUploadModal } from './components/FileUploadModal';
import { LoadingPlaceholder } from './components/LoadingPlaceholder';
import { generateRandomIcon } from './components/TaskIcon';
import { Globe, FileText, Presentation, Smartphone, Search, Gamepad2 } from 'lucide-react';
import { useTaskManagement, useUIState, useConfigManagement } from './hooks/useTaskManagement';
import { useAppContext } from './context/AppContext';

// Función para generar ideas dinámicas basadas en contexto
const generateDynamicIdeas = async () => {
  try {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'https://frontend-fix-9.preview.emergentagent.com';
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
  // Context hooks - elimina props drilling
  const { getActiveTask } = useAppContext();
  const {
    tasks,
    activeTaskId,
    isTaskCreating,
    createTask,
    createTaskWithMessage,
    updateTask,
    deleteTask,
    setActiveTask,
    updateTaskProgress,
    uploadFilesForTask
  } = useTaskManagement();
  
  const {
    sidebarCollapsed,
    isThinking,
    showFilesModal,
    toggleSidebar,
    setThinking,
    openFilesModal,
    closeFilesModal
  } = useUIState();
  
  const { config, updateConfig } = useConfigManagement();
  
  // Estado local únicamente para cosas que NO necesitan ser compartidas
  const [dynamicIdeas, setDynamicIdeas] = React.useState<any[]>([]);
  const [isInitialLoading, setIsInitialLoading] = React.useState(false); // Removido delay artificial
  const [showFileUpload, setShowFileUpload] = React.useState(false);
  const [isConfigOpen, setIsConfigOpen] = React.useState(false);
  const [initializingTaskId, setInitializingTaskId] = React.useState<string | null>(null);
  const [initializationLogs, setInitializationLogs] = React.useState<Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>>([]);

  // Cargar ideas dinámicas solo cuando no hay tareas activas
  useEffect(() => {
    if (!activeTaskId && dynamicIdeas.length === 0) {
      generateDynamicIdeas().then(ideas => {
        setDynamicIdeas(ideas.slice(0, 3));
      });
    }
  }, [activeTaskId, dynamicIdeas.length]);

  // Función para completar la inicialización
  const handleInitializationComplete = React.useCallback(() => {
    console.log('✅ Task initialization completed');
    setInitializingTaskId(null);
    
    // Agregar log final de inicialización completada
    const logEntry = {
      message: '🎉 Environment ready! You can start working now.',
      type: 'success' as const,
      timestamp: new Date()
    };
    setInitializationLogs(prev => [...prev, logEntry]);
    
    // Limpiar logs después de un tiempo
    setTimeout(() => {
      setInitializationLogs([]);
    }, 10000);
  }, []);

  // Función para manejar logs de inicialización
  const handleInitializationLog = React.useCallback((message: string, type: 'info' | 'success' | 'error') => {
    const logEntry = {
      message,
      type,
      timestamp: new Date()
    };
    
    setInitializationLogs(prev => [...prev, logEntry]);
    console.log(`📝 Initialization log (${type}):`, message);
  }, []);

  const handleConfigChange = (newConfig: any) => {
    updateConfig(newConfig);
    console.log('Configuración actualizada:', newConfig);
  };

  const handleDynamicIdea = (idea: any) => {
    createTaskWithMessage(idea.title);
  };

  const handleAttachFiles = () => {
    console.log('🎯 ATTACH FILES CLICKED - Setting showFileUpload to true');
    setShowFileUpload(true);
    console.log('✅ showFileUpload state set to true');
  };

  const handleFilesUploaded = async (files: FileList) => {
    console.log('📎 Files uploaded:', files);
    await uploadFilesForTask(files);
    setShowFileUpload(false);
  };

  // Optimized keyboard shortcuts
  useEffect(() => {
    const handleKeyboard = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isConfigOpen) {
        setIsConfigOpen(false);
      }
    };

    if (isConfigOpen) {
      window.addEventListener('keydown', handleKeyboard);
      return () => window.removeEventListener('keydown', handleKeyboard);
    }
  }, [isConfigOpen]);

  const activeTask = getActiveTask();

  // 🐛 DEBUG: Logging critical render state - usando Context
  console.log('🔍 RENDER DEBUG - App.tsx (Context version):', {
    activeTaskId,
    tasksLength: tasks.length,
    activeTask: activeTask ? `Found: ${activeTask.id} - "${activeTask.title}"` : 'Not found',
    condition: `activeTask=${!!activeTask}, activeTaskId=${!!activeTaskId}`,
    renderResult: activeTask && activeTaskId ? 'TaskView' : 'Homepage',
    contextEnabled: true
  });

  return (
    <div className="flex h-screen w-full bg-[#272728] text-[#DADADA]" style={{ fontFamily: "'Segoe UI Variable Display', 'Segoe UI', system-ui, -apple-system, sans-serif", fontWeight: 400 }}>
      {isInitialLoading ? (
        // Loading placeholder (simplificado)
        <div className="flex w-full">
          <div className="w-80 bg-[#212122] border-r border-[rgba(255,255,255,0.08)] p-4">
            <LoadingPlaceholder type="card" className="mb-4" />
          </div>
          <div className="flex-1 flex items-center justify-center p-8">
            <LoadingPlaceholder type="text" lines={1} height="h-12" className="mb-4" />
          </div>
        </div>
      ) : (
        <>
          <Sidebar 
            tasks={tasks} 
            activeTaskId={activeTaskId} 
            onTaskSelect={setActiveTask} 
            onCreateTask={createTask}
            onDeleteTask={deleteTask}
            onUpdateTask={updateTask}
            onConfigOpen={() => setIsConfigOpen(true)}
            isCollapsed={sidebarCollapsed}
            onToggleCollapse={toggleSidebar}
          />
          
          <div className="flex-1 flex flex-col overflow-hidden">
            {activeTask && activeTaskId ? (
              <TaskView 
                task={activeTask} 
                onUpdateTask={updateTask}
                onUpdateTaskProgress={updateTaskProgress}
                isThinking={isThinking}
                externalLogs={initializationLogs}
                isInitializing={initializingTaskId === activeTask.id}
                onInitializationComplete={handleInitializationComplete}
                onInitializationLog={handleInitializationLog}
              />
            ) : (
              <div className="flex flex-1 items-center justify-center bg-[#272728] p-8">
                <div className="text-left max-w-4xl w-full">
                  {/* Título unificado */}
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
                          console.log('🎯 Homepage: Creating task with initial message (Context)');
                          if (message.trim()) {
                            const newTask = await createTaskWithMessage(message.trim());
                            console.log('✅ Task created with Context:', newTask.id);
                          }
                        }}
                        placeholder="Escribe tu tarea aquí..."
                        className="w-full text-lg"
                        showInternalButtons={true}
                        onAttachFiles={handleAttachFiles}
                        onWebSearch={async (searchQuery) => {
                          console.log('🌐 WebSearch: Creating task with Context');
                          if (searchQuery && searchQuery.trim().length > 0) {
                            const newTask = await createTaskWithMessage(searchQuery);
                            console.log('✅ WebSearch task created with Context:', newTask.id);
                          }
                        }}
                        onDeepSearch={async (searchQuery) => {
                          console.log('🔬 DeepSearch: Creating task with Context');
                          if (searchQuery && searchQuery.trim().length > 0) {
                            const newTask = await createTaskWithMessage(searchQuery);
                            console.log('✅ DeepSearch task created with Context:', newTask.id);
                          }
                        }}
                        onVoiceInput={() => console.log('Voice input clicked')}
                      />
                    )}
                  </div>
                  
                  {/* Ideas dinámicas */}
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
            config={config}
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