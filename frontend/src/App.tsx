import React, { useEffect, useState, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { VanishInput } from './components/VanishInput';
import { TaskView } from './components/TaskView';
import { ConfigPanel } from './components/ConfigPanel';
import { FileUploadModal } from './components/FileUploadModal';
import { LoadingPlaceholder } from './components/LoadingPlaceholder';
import { generateRandomIcon } from './components/TaskIcon';
import { Globe, FileText, Presentation, Smartphone, Search, Gamepad2 } from 'lucide-react';
import { API_CONFIG } from './config/api';
import { useAppContext } from './context/AppContext';
import { useTaskManagement, useUIState, useConfigManagement, useFileManagement } from './hooks/useTaskManagement';

// ========================================================================
// APP PRINCIPAL - REFACTORIZADO PARA AISLAMIENTO COMPLETO
// Usa completamente el Context API expandido para gestión de estado aislado
// ========================================================================

// Función para generar ideas dinámicas basadas en contexto
const generateDynamicIdeas = async () => {
  try {
    const response = await fetch(`${API_CONFIG.backend.url}/api/agent/generate-suggestions`, {
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
  // ========================================================================
  // USAR CONTEXT COMPLETAMENTE - NO MÁS ESTADO LOCAL
  // ========================================================================
  
  const {
    tasks,
    activeTaskId,
    isTaskCreating,
    createTask, // ✅ FUNCIÓN YA DISPONIBLE EN EL HOOK REFACTORIZADO
    createTaskWithMessage,
    updateTask,
    deleteTask,
    setActiveTask
  } = useTaskManagement();
  
  const { uploadFilesForTask } = useFileManagement(); // ✅ USAR HOOK ESPECÍFICO
  
  const {
    sidebarCollapsed,
    isThinking,
    showFilesModal,
    isConfigOpen,
    toggleSidebar,
    setThinking,
    openFilesModal,
    closeFilesModal
  } = useUIState();
  
  const { config, updateConfig } = useConfigManagement();
  
  // ========================================================================
  // ESTADO LOCAL MÍNIMO - SOLO PARA UI NO PERSISTENTE
  // ========================================================================
  
  const [dynamicIdeas, setDynamicIdeas] = useState<any[]>([]);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [initializingTaskId, setInitializingTaskId] = useState<string | null>(null);
  const [initializationLogs, setInitializationLogs] = useState<Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>>([]);

  // ========================================================================
  // EFECTOS PARA CARGA INICIAL Y GESTIÓN
  // ========================================================================

  // Cargar ideas dinámicas solo cuando no hay tareas activas
  useEffect(() => {
    if (!activeTaskId && dynamicIdeas.length === 0) {
      generateDynamicIdeas().then(ideas => {
        setDynamicIdeas(ideas.slice(0, 3)); // Mostrar solo 3 ideas
      });
    }
  }, [activeTaskId, dynamicIdeas.length]);

  // Quitar loading inmediatamente
  useEffect(() => {
    setIsInitialLoading(false);
  }, []);

  // ========================================================================
  // HANDLERS - USANDO HOOKS DEL CONTEXT
  // ========================================================================

  const handleDynamicIdea = useCallback((idea: any) => {
    createTaskWithMessage(idea.title);
  }, [createTaskWithMessage]);

  const handleAttachFiles = useCallback(() => {
    console.log('🎯 ATTACH FILES CLICKED - Opening file upload modal');
    openFilesModal();
  }, [openFilesModal]);

  const handleFilesUploaded = useCallback(async (files: FileList) => {
    console.log('📎 Files uploaded:', files);
    
    try {
      await uploadFilesForTask(files);
    } catch (error) {
      console.error('💥 Error uploading files:', error);
    }
    
    closeFilesModal();
  }, [uploadFilesForTask, closeFilesModal]);

  const handleConfigChange = useCallback((newConfig: any) => {
    updateConfig(newConfig);
    console.log('Configuración actualizada:', newConfig);
  }, [updateConfig]);

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
  }, [handleInitializationLog]);

  // ========================================================================
  // OPTIMIZACIÓN DE RENDERS
  // ========================================================================

  // Optimized keyboard shortcuts
  useEffect(() => {
    const handleKeyboard = (e: KeyboardEvent) => {
      // Escape para cerrar configuración
      if (e.key === 'Escape' && isConfigModalOpen) {
        setIsConfigModalOpen(false);
      }
    };

    if (isConfigModalOpen) { // Solo agregar listener si está abierto
      window.addEventListener('keydown', handleKeyboard);
      return () => window.removeEventListener('keydown', handleKeyboard);
    }
  }, [isConfigModalOpen]);

  // ========================================================================
  // GETTERS MEMOIZADOS USANDO CONTEXT
  // ========================================================================

  const activeTask = tasks.find(task => task.id === activeTaskId);

  // Debug logging
  console.log('🔍 RENDER DEBUG - App.tsx render:', {
    activeTaskId,
    tasksLength: tasks.length,
    activeTask: activeTask ? `Found: ${activeTask.id} - "${activeTask.title}"` : 'Not found',
    condition: `activeTask=${!!activeTask}, activeTaskId=${!!activeTaskId}`,
    renderResult: activeTask && activeTaskId ? 'TaskView' : 'Homepage'
  });

  // ========================================================================
  // RENDER PRINCIPAL
  // ========================================================================

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
            tasks={tasks} // ✅ DESDE CONTEXT
            activeTaskId={activeTaskId} // ✅ DESDE CONTEXT
            onTaskSelect={setActiveTask} // ✅ HOOK DEL CONTEXT
            onCreateTask={async (title, iconType) => {
              console.log('🎯 APP: Creating task:', title);
              try {
                // Si es solo "Nueva tarea" (placeholder), no llamar al backend todavía
                if (title === 'Nueva tarea' || title.trim() === '') {
                  console.log('🎯 APP: Creating placeholder task (no backend call)');
                  const placeholderTask = createTask(title || 'Nueva tarea', iconType);
                  return placeholderTask;
                } else {
                  // Solo llamar al backend cuando hay contenido real del usuario
                  console.log('🎯 APP: Creating task with backend integration:', title);
                  const newTask = await createTaskWithMessage(title, iconType);
                  console.log('🎯 APP: Nueva tarea creada con backend correctamente:', newTask.id);
                  return newTask;
                }
              } catch (error) {
                console.error('❌ Error creating task:', error);
                // Fallback to context-only creation
                const fallbackTask = createTask(title, iconType);
                console.log('🎯 APP: Fallback task created:', fallbackTask.id);
                return fallbackTask;
              }
            }}
            onDeleteTask={deleteTask} // ✅ HOOK DEL CONTEXT
            onUpdateTask={updateTask} // ✅ HOOK DEL CONTEXT
            onConfigOpen={() => setIsConfigModalOpen(true)}
            isCollapsed={sidebarCollapsed} // ✅ DESDE CONTEXT
            onToggleCollapse={toggleSidebar} // ✅ HOOK DEL CONTEXT
          />
          
          <div className="flex-1 flex flex-col overflow-hidden">
            {activeTask && activeTaskId ? (
              <TaskView 
                task={activeTask} // ✅ TAREA ACTIVA DESDE CONTEXT
                onUpdateTask={updateTask} // ✅ HOOK DEL CONTEXT
                onUpdateTaskProgress={(taskId) => {
                  // Progress update se maneja automáticamente en el Context
                  console.log(`🔄 Progress update request for task: ${taskId}`);
                }}
                isThinking={isThinking} // ✅ DESDE CONTEXT
                onTerminalResize={(height) => {
                  // Terminal resize se maneja en UI state
                  console.log(`📏 Terminal resized to: ${height}px`);
                }}
                externalLogs={initializationLogs} // Logs locales de inicialización
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
                            // ✅ USAR HOOK DEL CONTEXT
                            await createTaskWithMessage(message.trim());
                          }
                        }}
                        placeholder="Escribe tu tarea aquí..."
                        className="w-full text-lg"
                        showInternalButtons={true}
                        onAttachFiles={handleAttachFiles}
                        onWebSearch={async (searchQuery) => {
                          console.log('🌐 WebSearch: Creating task with message');
                          if (searchQuery && searchQuery.trim().length > 0) {
                            // ✅ USAR HOOK DEL CONTEXT
                            await createTaskWithMessage(searchQuery);
                          }
                        }}
                        onDeepSearch={async (searchQuery) => {
                          console.log('🔬 DeepSearch: Creating task with message');
                          if (searchQuery && searchQuery.trim().length > 0) {
                            // ✅ USAR HOOK DEL CONTEXT
                            await createTaskWithMessage(searchQuery);
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
            config={config} // ✅ DESDE CONTEXT
            onConfigChange={handleConfigChange}
            onClose={() => setIsConfigModalOpen(false)}
            isOpen={isConfigModalOpen}
          />

          {/* File Upload Modal */}
          <FileUploadModal
            isOpen={showFilesModal} // ✅ DESDE CONTEXT
            onClose={closeFilesModal} // ✅ HOOK DEL CONTEXT
            onFilesUploaded={handleFilesUploaded}
          />
        </>
      )}
    </div>
  );
}