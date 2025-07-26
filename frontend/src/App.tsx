import React, { useEffect, useMemo, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { VanishInput } from './components/VanishInput';
import { TaskView } from './components/TaskView';
import { LoadingPlaceholder } from './components/LoadingPlaceholder';
import { generateRandomIcon } from './components/TaskIcon';
import { Globe, FileText, Presentation, Smartphone, Search, Gamepad2 } from 'lucide-react';
import { useTaskManagement, useUIState, useConfigManagement } from './hooks/useTaskManagement';
import { useAppContext } from './context/AppContext';
import { 
  LazyWrapper, 
  ConfigPanel, 
  FilesModal, 
  FileUploadModal, 
  ModalLoadingFallback,
  preloadCriticalComponents 
} from './components/LazyComponents';

// ========================================================================
// OPTIMIZACIONES DE PERFORMANCE - FASE 5
// ========================================================================

// Memoizar generación de ideas dinámicas
const generateDynamicIdeas = async () => {
  try {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
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

// Componente de idea memoizado para evitar re-renders
const DynamicIdeaButton = React.memo<{
  idea: any;
  isLoading: boolean;
  onClick: (idea: any) => void;
}>(({ idea, isLoading, onClick }) => {
  const handleClick = useCallback(() => {
    onClick(idea);
  }, [idea, onClick]);

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className="flex items-center gap-2 px-4 py-2 bg-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.1)] rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <Search className="w-4 h-4 text-blue-400" />
      <span className="text-sm text-[#DADADA]">{idea.title}</span>
    </button>
  );
});

DynamicIdeaButton.displayName = 'DynamicIdeaButton';

// ========================================================================
// COMPONENTE PRINCIPAL OPTIMIZADO
// ========================================================================

export function App() {
  // Context hooks - eliminan props drilling
  try {
    const appContext = useAppContext();
    const { getActiveTask } = appContext;
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
  } catch (error) {
    console.error('❌ CRITICAL APP ERROR:', error);
    return (
      <div className="flex h-screen w-full bg-red-900 text-white items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Error de Aplicación</h1>
          <p className="mb-4">Ha ocurrido un error crítico en la aplicación:</p>
          <pre className="bg-black p-4 rounded text-left text-sm overflow-auto max-w-2xl">
            {error instanceof Error ? error.message : String(error)}
          </pre>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
          >
            Recargar Página
          </button>
        </div>
      </div>
    );
  }
  
  // Estado local mínimo - solo para datos que NO se comparten
  const [dynamicIdeas, setDynamicIdeas] = React.useState<any[]>([]);
  const [isInitialLoading, setIsInitialLoading] = React.useState(false);
  const [showFileUpload, setShowFileUpload] = React.useState(false);
  const [isConfigOpen, setIsConfigOpen] = React.useState(false);
  const [initializingTaskId, setInitializingTaskId] = React.useState<string | null>(null);
  const [initializationLogs, setInitializationLogs] = React.useState<Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>>([]);

  // ========================================================================
  // MEMOIZED VALUES - PREVENIR CÁLCULOS INNECESARIOS
  // ========================================================================

  const activeTask = useMemo(() => getActiveTask(), [getActiveTask]);

  // Memoizar condición de renderizado principal
  const shouldShowTaskView = useMemo(() => {
    return activeTask && activeTaskId;
  }, [activeTask, activeTaskId]);

  // ========================================================================
  // CALLBACKS MEMOIZADOS - PREVENIR RE-RENDERS
  // ========================================================================

  const handleInitializationComplete = useCallback(() => {
    console.log('✅ Task initialization completed');
    setInitializingTaskId(null);
    
    const logEntry = {
      message: '🎉 Environment ready! You can start working now.',
      type: 'success' as const,
      timestamp: new Date()
    };
    setInitializationLogs(prev => [...prev, logEntry]);
    
    setTimeout(() => {
      setInitializationLogs([]);
    }, 10000);
  }, []);

  const handleInitializationLog = useCallback((message: string, type: 'info' | 'success' | 'error') => {
    const logEntry = {
      message,
      type,
      timestamp: new Date()
    };
    
    setInitializationLogs(prev => [...prev, logEntry]);
    console.log(`📝 Initialization log (${type}):`, message);
  }, []);

  const handleConfigChange = useCallback((newConfig: any) => {
    updateConfig(newConfig);
    console.log('Configuración actualizada:', newConfig);
  }, [updateConfig]);

  const handleDynamicIdea = useCallback((idea: any) => {
    createTaskWithMessage(idea.title);
  }, [createTaskWithMessage]);

  const handleAttachFiles = useCallback(() => {
    console.log('🎯 ATTACH FILES CLICKED - Setting showFileUpload to true');
    setShowFileUpload(true);
    console.log('✅ showFileUpload state set to true');
  }, []);

  const handleFilesUploaded = useCallback(async (files: FileList) => {
    console.log('📎 Files uploaded:', files);
    await uploadFilesForTask(files);
    setShowFileUpload(false);
  }, [uploadFilesForTask]);

  const handleCreateTaskWithMessage = useCallback(async (message: string) => {
    console.log('🎯 Homepage: Creating task with initial message (Optimized)');
    if (message.trim()) {
      const newTask = await createTaskWithMessage(message.trim());
      console.log('✅ Task created optimized:', newTask.id);
    }
  }, [createTaskWithMessage]);

  // ========================================================================
  // EFFECTS OPTIMIZADOS
  // ========================================================================

  // Cargar ideas dinámicas solo cuando es necesario
  useEffect(() => {
    if (!activeTaskId && dynamicIdeas.length === 0) {
      generateDynamicIdeas().then(ideas => {
        setDynamicIdeas(ideas.slice(0, 3));
      });
    }
  }, [activeTaskId, dynamicIdeas.length]);

  // Preload componentes críticos
  useEffect(() => {
    preloadCriticalComponents();
  }, []);

  // Keyboard shortcuts optimizados
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

  // ========================================================================
  // MEMOIZED COMPONENTS - PREVENIR RE-RENDERS INNECESARIOS
  // ========================================================================

  const sidebar = useMemo(() => (
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
  ), [tasks, activeTaskId, setActiveTask, createTask, deleteTask, updateTask, sidebarCollapsed, toggleSidebar]);

  const taskView = useMemo(() => {
    if (!shouldShowTaskView) return null;
    
    return (
      <TaskView 
        task={activeTask!} 
        onUpdateTask={updateTask}
        onUpdateTaskProgress={updateTaskProgress}
        isThinking={isThinking}
        externalLogs={initializationLogs}
        isInitializing={initializingTaskId === activeTask!.id}
        onInitializationComplete={handleInitializationComplete}
        onInitializationLog={handleInitializationLog}
      />
    );
  }, [shouldShowTaskView, activeTask, updateTask, updateTaskProgress, isThinking, initializationLogs, initializingTaskId, handleInitializationComplete, handleInitializationLog]);

  const dynamicIdeasSection = useMemo(() => {
    if (dynamicIdeas.length === 0) return null;
    
    return (
      <div className="mb-12">
        <div className="flex items-center justify-center gap-3">
          {dynamicIdeas.map((idea, index) => (
            <DynamicIdeaButton
              key={index}
              idea={idea}
              isLoading={isTaskCreating}
              onClick={handleDynamicIdea}
            />
          ))}
        </div>
      </div>
    );
  }, [dynamicIdeas, isTaskCreating, handleDynamicIdea]);

  const homepage = useMemo(() => {
    if (shouldShowTaskView) return null;
    
    return (
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
          
          {/* Caja de texto optimizada */}
          <div className="mb-8 max-w-4xl mx-auto">
            {isTaskCreating ? (
              <div className="w-full p-4 bg-[rgba(255,255,255,0.06)] rounded-lg border border-[rgba(255,255,255,0.08)]">
                <LoadingPlaceholder type="text" lines={1} height="h-6" className="mb-2" />
                <div className="text-sm text-[#ACACAC]">Creando nueva tarea...</div>
              </div>
            ) : (
              <VanishInput
                onSendMessage={handleCreateTaskWithMessage}
                placeholder="Escribe tu tarea aquí..."
                className="w-full text-lg"
                showInternalButtons={true}
                onAttachFiles={handleAttachFiles}
                onWebSearch={handleCreateTaskWithMessage}
                onDeepSearch={handleCreateTaskWithMessage}
                onVoiceInput={() => console.log('Voice input clicked')}
              />
            )}
          </div>
          
          {/* Ideas dinámicas memoizadas */}
          {dynamicIdeasSection}
        </div>
      </div>
    );
  }, [shouldShowTaskView, isTaskCreating, handleCreateTaskWithMessage, handleAttachFiles, dynamicIdeasSection]);

  // ========================================================================
  // RENDER OPTIMIZADO CON LAZY LOADING
  // ========================================================================

  return (
    <div className="flex h-screen w-full bg-[#272728] text-[#DADADA]" style={{ fontFamily: "'Segoe UI Variable Display', 'Segoe UI', system-ui, -apple-system, sans-serif", fontWeight: 400 }}>
      {isInitialLoading ? (
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
          {sidebar}
          
          <div className="flex-1 flex flex-col overflow-hidden">
            {taskView || homepage}
          </div>

          {/* Lazy loaded modals con Suspense optimizado */}
          <LazyWrapper fallback={<ModalLoadingFallback />}>
            <ConfigPanel
              config={config}
              onConfigChange={handleConfigChange}
              onClose={() => setIsConfigOpen(false)}
              isOpen={isConfigOpen}
            />
          </LazyWrapper>

          <LazyWrapper fallback={<ModalLoadingFallback />}>
            <FileUploadModal
              isOpen={showFileUpload}
              onClose={() => setShowFileUpload(false)}
              onFilesUploaded={handleFilesUploaded}
            />
          </LazyWrapper>
        </>
      )}
    </div>
  );
}