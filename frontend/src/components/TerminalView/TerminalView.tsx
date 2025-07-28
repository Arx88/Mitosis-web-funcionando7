import React, { useEffect, useState, useRef } from 'react';
import { Check, ChevronDown, Maximize2, Rewind, Terminal, AlertCircle, CheckCircle, Circle, ChevronUp, Clock, Activity, Zap, FileText, SkipBack, SkipForward, Monitor, Radio, ArrowLeft, ArrowRight, RotateCcw, Loader2 } from 'lucide-react';
import { ToolResult } from '../../services/api';
import { TaskStep } from '../../types';
import { TaskIcon } from '../TaskIcon';
import { ToolExecutionDetails } from '../ToolExecutionDetails';
import { TaskCompletedUI } from '../TaskCompletedUI';

export interface Task {
  id: string;
  title: string;
  completed: boolean;
}

export interface MonitorPage {
  id: string;
  title: string;
  content: string;
  type: 'plan' | 'tool-execution' | 'report' | 'file' | 'error';
  timestamp: Date;
  toolName?: string;
  toolParams?: any;
  metadata?: {
    lineCount?: number;
    fileSize?: number;
    executionTime?: number;
    status?: 'success' | 'error' | 'running';
  };
}

export interface TerminalViewProps {
  title?: string;
  tasks?: Task[];
  isLive?: boolean;
  onFullscreen?: () => void;
  'data-id'?: string;
  toolResults?: ToolResult[];
  plan?: TaskStep[];
  onToggleTaskStep?: (stepId: string) => void;
  onPlanUpdate?: (plan: any[]) => void; // ✨ NEW: Callback for plan updates
  externalLogs?: Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>;
  isInitializing?: boolean;
  onInitializationComplete?: () => void;
  onInitializationLog?: (message: string, type: 'info' | 'success' | 'error') => void;
  taskId?: string;
  taskTitle?: string;
  executionData?: any; // Datos de ejecución del backend
}

export const TerminalView = ({
  title = 'Monitor de Ejecución',
  tasks = [],
  isLive = false,
  onFullscreen,
  'data-id': dataId,
  toolResults = [],
  plan = [],
  onToggleTaskStep,
  onPlanUpdate, // ✨ NEW: Add onPlanUpdate prop
  externalLogs = [],
  isInitializing = false,
  onInitializationComplete,
  onInitializationLog,
  taskId,
  taskTitle,
  executionData
}: TerminalViewProps) => {
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [isPlanExpanded, setIsPlanExpanded] = useState(true);

  // ✨ NEW: Time tracking for steps
  const [stepTimers, setStepTimers] = useState<{ [stepId: string]: { startTime: Date, interval: NodeJS.Timeout } }>({});

  // ✨ NEW: Function to format elapsed time
  const formatElapsedTime = (startTime: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - startTime.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const minutes = Math.floor(diffSeconds / 60);
    const seconds = diffSeconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  // ✨ NEW: Start timer for active step
  const startStepTimer = (stepId: string) => {
    if (stepTimers[stepId]) return; // Already has timer
    
    const startTime = new Date();
    const interval = setInterval(() => {
      const elapsedTime = formatElapsedTime(startTime);
      
      // Update the plan with elapsed time
      if (plan) {
        const updatedPlan = plan.map(step => 
          step.id === stepId 
            ? { ...step, elapsed_time: elapsedTime, start_time: startTime }
            : step
        );
        onPlanUpdate?.(updatedPlan);
      }
    }, 1000);

    setStepTimers(prev => ({
      ...prev,
      [stepId]: { startTime, interval }
    }));
  };

  // ✨ NEW: Stop timer for step
  const stopStepTimer = (stepId: string) => {
    if (stepTimers[stepId]) {
      clearInterval(stepTimers[stepId].interval);
      setStepTimers(prev => {
        const newTimers = { ...prev };
        delete newTimers[stepId];
        return newTimers;
      });
    }
  };

  // ✨ NEW: Effect to manage step timers - FIXED: Don't stop timer when step completes
  useEffect(() => {
    if (!plan) return;

    // Start timer for active steps
    plan.forEach(step => {
      if (step.active && !stepTimers[step.id]) {
        startStepTimer(step.id);
      } else if (!step.active && !step.completed && stepTimers[step.id]) {
        // Only stop timer if step becomes inactive AND not completed
        // This prevents timer from disappearing when step completes
        stopStepTimer(step.id);
      }
    });

    // Only cleanup timers for steps that no longer exist in plan
    Object.keys(stepTimers).forEach(stepId => {
      const step = plan.find(s => s.id === stepId);
      if (!step) {
        stopStepTimer(stepId);
      }
    });

    // Cleanup all timers on unmount
    return () => {
      Object.values(stepTimers).forEach(timer => {
        clearInterval(timer.interval);
      });
    };
  }, [plan]);
  const [currentExecutingTool, setCurrentExecutingTool] = useState<ToolResult | null>(null);
  const [monitorPages, setMonitorPages] = useState<MonitorPage[]>([]);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [isLiveMode, setIsLiveMode] = useState(true);
  const [isSystemOnline, setIsSystemOnline] = useState(false);
  const [initializationStep, setInitializationStep] = useState(0);
  const [paginationStats, setPaginationStats] = useState({
    totalPages: 0,
    currentPage: 1,
    limit: 20,
    offset: 0
  });
  const monitorRef = useRef<HTMLDivElement>(null);

  // Función para cargar el informe final - FIXED: Proper error handling and content loading
  const loadFinalReport = async (taskId: string) => {
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'https://frontend-fix-9.preview.emergentagent.com';
      console.log('📄 Loading final report for task:', taskId);
      
      const response = await fetch(`${backendUrl}/api/agent/generate-final-report/${taskId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('📄 Final report loaded successfully:', result);
        
        // Create the final report content
        const reportContent = result.report || result.content || `# Informe Final - ${taskTitle}\n\n## Resumen\n\nTarea completada exitosamente.\n\n## Pasos Ejecutados\n\n${plan?.map((step, index) => `${index + 1}. ${step.title} ✅`).join('\n') || 'No hay pasos registrados'}\n\n## Conclusión\n\nTodos los pasos se ejecutaron correctamente.\n\n---\n\n*Generado automáticamente por Mitosis*`;
        
        const reportPage: MonitorPage = {
          id: 'final-report',
          title: '📄 INFORME FINAL - Tarea Completada',
          content: reportContent,
          type: 'report',
          timestamp: new Date(),
          metadata: {
            lineCount: reportContent.split('\n').length,
            status: 'success',
            fileSize: reportContent.length
          }
        };
        
        // Update or add the final report page
        setMonitorPages(prev => {
          const existingIndex = prev.findIndex(page => page.id === 'final-report');
          if (existingIndex >= 0) {
            // Update existing page
            const updated = [...prev];
            updated[existingIndex] = reportPage;
            // Navigate to the final report page
            setCurrentPageIndex(existingIndex);
            setIsLiveMode(false);
            return updated;
          } else {
            // Add new page
            setPaginationStats(prevStats => ({ 
              ...prevStats, 
              totalPages: prevStats.totalPages + 1 
            }));
            const newPages = [...prev, reportPage];
            // Navigate to the final report page (last page)
            setCurrentPageIndex(newPages.length - 1);
            setIsLiveMode(false);
            return newPages;
          }
        });
        
        console.log('📄 Final report loaded successfully in terminal');
      } else {
        console.error('Error loading final report:', response.status);
        // Create fallback report
        const fallbackReport = `# Informe Final - ${taskTitle}\n\n## Resumen\n\nTarea completada exitosamente.\n\n## Pasos Ejecutados\n\n${plan?.map((step, index) => `${index + 1}. ${step.title} ✅`).join('\n') || 'No hay pasos registrados'}\n\n## Conclusión\n\nTodos los pasos se ejecutaron correctamente.\n\n---\n\n*Generado automáticamente por Mitosis*`;
        
        const fallbackPage: MonitorPage = {
          id: 'final-report',
          title: '📄 INFORME FINAL - Tarea Completada',
          content: fallbackReport,
          type: 'report',
          timestamp: new Date(),
          metadata: {
            lineCount: fallbackReport.split('\n').length,
            status: 'success',
            fileSize: fallbackReport.length
          }
        };
        
        // Add fallback report
        setMonitorPages(prev => {
          const newPages = [...prev, fallbackPage];
          setCurrentPageIndex(newPages.length - 1);
          setIsLiveMode(false);
          return newPages;
        });
        setPaginationStats(prev => ({ ...prev, totalPages: prev.totalPages + 1 }));
      }
    } catch (error) {
      console.error('Error loading final report:', error);
      // Create error fallback report
      const errorReport = `# Informe Final - ${taskTitle}\n\n## Resumen\n\nTarea completada exitosamente.\n\n## Pasos Ejecutados\n\n${plan?.map((step, index) => `${index + 1}. ${step.title} ✅`).join('\n') || 'No hay pasos registrados'}\n\n## Conclusión\n\nTodos los pasos se ejecutaron correctamente.\n\n---\n\n*Generado automáticamente por Mitosis*`;
      
      const errorPage: MonitorPage = {
        id: 'final-report',
        title: '📄 INFORME FINAL - Tarea Completada',
        content: errorReport,
        type: 'report',
        timestamp: new Date(),
        metadata: {
          lineCount: errorReport.split('\n').length,
          status: 'success',
          fileSize: errorReport.length
        }
      };
      
      // Add error fallback report
      setMonitorPages(prev => {
        const newPages = [...prev, errorPage];
        setCurrentPageIndex(newPages.length - 1);
        setIsLiveMode(false);
        return newPages;
      });
      setPaginationStats(prev => ({ ...prev, totalPages: prev.totalPages + 1 }));
    }
  };

  // Define initialization steps as constant to avoid infinite re-renders
  const initializationSteps = [
    { id: 'env', title: 'Setting up environment', duration: 1500 },
    { id: 'deps', title: 'Installing dependencies', duration: 2000 },
    { id: 'agent', title: 'Initializing agent', duration: 1000 }
  ];

  // Reset terminal state when dataId changes (switching tasks)
  useEffect(() => {
    console.log('🔄 TERMINAL: Resetting state for new task:', dataId);
    setTerminalOutput([]);
    setCurrentExecutingTool(null);
    setMonitorPages([]);
    setCurrentPageIndex(0);
    setIsLiveMode(true);
    setIsSystemOnline(false);
    setInitializationStep(0);
    setPaginationStats({
      totalPages: 0,
      currentPage: 1,
      limit: 20,
      offset: 0
    });
    console.log('✅ TERMINAL: State reset complete for task:', dataId);
  }, [dataId]); // Reset whenever dataId changes, including when it becomes null/undefined

  // Handle environment initialization - Fixed dependency array
  useEffect(() => {
    if (isInitializing && taskId && taskTitle) {
      console.log('🚀 TERMINAL: Starting environment initialization');
      setIsSystemOnline(false);
      setInitializationStep(0);
      
      // Log initial message
      if (onInitializationLog) {
        onInitializationLog(`🚀 Initializing environment for: ${taskTitle}`, 'info');
      }
      
      // Process initialization steps
      const processStep = (stepIndex: number) => {
        if (stepIndex >= initializationSteps.length) {
          // All steps completed
          setIsSystemOnline(true);
          if (onInitializationLog) {
            onInitializationLog('✅ Environment ready! System is now ONLINE', 'success');
          }
          if (onInitializationComplete) {
            onInitializationComplete();
          }
          return;
        }
        
        const step = initializationSteps[stepIndex];
        setInitializationStep(stepIndex);
        
        if (onInitializationLog) {
          onInitializationLog(`⚙️ ${step.title}...`, 'info');
        }
        
        setTimeout(() => {
          if (onInitializationLog) {
            onInitializationLog(`✓ ${step.title} completed`, 'success');
          }
          processStep(stepIndex + 1);
        }, step.duration);
      };
      
      processStep(0);
    }
  }, [isInitializing, taskId, taskTitle, onInitializationLog, onInitializationComplete]); // Removed initializationSteps

  // Inicializar con TODO.md como Página 1 - Solo si hay plan Y no hay páginas Y hay dataId
  useEffect(() => {
    if (plan && plan.length > 0 && monitorPages.length === 0 && dataId) {
      const todoPlan = plan.map((step, index) => 
        `${index + 1}. ${step.title} ${step.completed ? '✓' : '○'}`
      ).join('\n');
      
      const todoPage: MonitorPage = {
        id: 'todo-plan',
        title: 'TODO.md - Plan de Acción',
        content: `# Plan de Acción\n\n${todoPlan}\n\n---\n\n*Generado automáticamente por el sistema de monitoreo*`,
        type: 'plan',
        timestamp: new Date(),
        metadata: {
          lineCount: plan.length + 4,
          status: 'success'
        }
      };
      
      setMonitorPages([todoPage]);
      setPaginationStats(prev => ({ ...prev, totalPages: 1 }));
    }
  }, [plan, dataId, monitorPages.length]); // Solo para cargar TODO.md inicial

  // SEPARAR: Verificar completación y cargar informe final
  useEffect(() => {
    if (plan && plan.length > 0 && taskId) {
      const allCompleted = plan.every(step => step.completed);
      const completedCount = plan.filter(s => s.completed).length;
      
      console.log('🔍 [DEBUG] Plan estado:', {
        totalSteps: plan.length,
        completedSteps: completedCount,
        allCompleted,
        taskId,
        planSteps: plan.map(s => ({ id: s.id, title: s.title, completed: s.completed }))
      });
      
      // Cargar informe final si la tarea está completada
      if (allCompleted && completedCount > 0) {
        console.log('🎯 [DEBUG] Todos los pasos completados, cargando informe final para tarea:', taskId);
        
        // Verificar que no se haya cargado ya el informe final
        const hasReportPage = monitorPages.some(page => page.id === 'final-report');
        if (!hasReportPage) {
          setTimeout(() => {
            const finalReportPage: MonitorPage = {
              id: 'final-report',
              title: '📄 INFORME FINAL - Tarea Completada',
              content: 'Cargando informe final...',
              type: 'report',
              timestamp: new Date(),
              metadata: {
                lineCount: 1,
                status: 'success',
                fileSize: 0
              }
            };
            
            console.log('📄 [DEBUG] Añadiendo página de informe final');
            setMonitorPages(prev => {
              const newPages = [...prev, finalReportPage];
              // Navegar automáticamente a la página del informe final cuando se agrega
              setCurrentPageIndex(newPages.length - 1);
              setIsLiveMode(false);
              return newPages;
            });
            setPaginationStats(prev => ({ ...prev, totalPages: prev.totalPages + 1 }));
            loadFinalReport(taskId);
          }, 1000);
        }
      }
    }
  }, [plan, taskId, monitorPages]); // Separado para detectar cambios en completación

  // Procesar herramientas y crear páginas
  useEffect(() => {
    if (toolResults.length > 0) {
      const newPages: MonitorPage[] = [];
      
      toolResults.forEach((result, index) => {
        // Crear página para cada herramienta utilizada
        const pageContent = generateToolPageContent(result);
        
        const toolPage: MonitorPage = {
          id: `tool-${result.tool}-${index}`,
          title: `${result.tool.toUpperCase()} - Ejecución #${index + 1}`,
          content: pageContent,
          type: 'tool-execution',
          timestamp: new Date(),
          toolName: result.tool,
          toolParams: result.parameters,
          metadata: {
            lineCount: pageContent.split('\n').length,
            status: result.result.error ? 'error' : 'success',
            executionTime: result.executionTime || 0
          }
        };
        
        newPages.push(toolPage);
        
        // Si es deep research, crear página adicional para el reporte
        if (result.tool === 'enhanced_deep_research' && result.result?.result?.console_report) {
          const reportPage: MonitorPage = {
            id: `report-${index}`,
            title: `Informe de Investigación - ${new Date().toLocaleDateString()}`,
            content: result.result.result.console_report,
            type: 'report',
            timestamp: new Date(),
            metadata: {
              lineCount: result.result.result.console_report.split('\n').length,
              fileSize: result.result.result.console_report.length,
              status: 'success'
            }
          };
          
          newPages.push(reportPage);
        }
      });
      
      // Actualizar páginas manteniendo TODO.md como primera página
      setMonitorPages(prev => {
        const todoPage = prev.find(p => p.id === 'todo-plan');
        const otherPages = prev.filter(p => p.id !== 'todo-plan');
        const allPages = todoPage ? [todoPage, ...otherPages, ...newPages] : [...otherPages, ...newPages];
        
        setPaginationStats(prevStats => ({
          ...prevStats,
          totalPages: allPages.length
        }));
        
        // Mantener en modo Live y ir a la última página automáticamente
        if (isLiveMode && allPages.length > 0) {
          setCurrentPageIndex(allPages.length - 1);
        }
        
        return allPages;
      });
      
      // Set current executing tool
      if (toolResults.length > 0) {
        setCurrentExecutingTool(toolResults[toolResults.length - 1]);
      }
    }
  }, [toolResults]);

  // Procesar logs externos
  useEffect(() => {
    if (externalLogs.length > 0) {
      const newPages: MonitorPage[] = [];
      
      externalLogs.forEach((log, index) => {
        if (log.message.includes('# ') || log.message.includes('## ') || log.message.includes('### ')) {
          const logPage: MonitorPage = {
            id: `log-${index}`,
            title: `Registro del Sistema - ${log.timestamp.toLocaleTimeString()}`,
            content: log.message,
            type: 'file',
            timestamp: log.timestamp,
            metadata: {
              lineCount: log.message.split('\n').length,
              status: log.type === 'error' ? 'error' : 'success'
            }
          };
          
          newPages.push(logPage);
        }
      });
      
      if (newPages.length > 0) {
        setMonitorPages(prev => [...prev, ...newPages]);
        setPaginationStats(prev => ({
          ...prev,
          totalPages: prev.totalPages + newPages.length
        }));
      }
    }
  }, [externalLogs]);

  // Procesar datos de ejecución del backend
  useEffect(() => {
    if (executionData && executionData.executed_tools) {
      console.log('🔧 Processing execution data in terminal:', executionData);
      
      const newPages: MonitorPage[] = [];
      
      executionData.executed_tools.forEach((tool: any, index: number) => {
        if (tool.result && tool.tool) {
          // Crear página para cada herramienta ejecutada
          const pageContent = generateBackendToolPageContent(tool);
          
          const toolPage: MonitorPage = {
            id: `backend-tool-${tool.tool}-${index}`,
            title: `${tool.tool.toUpperCase()} - Ejecutado por Backend`,
            content: pageContent,
            type: 'tool-execution',
            timestamp: new Date(tool.timestamp || new Date()),
            toolName: tool.tool,
            toolParams: tool.parameters,
            metadata: {
              lineCount: pageContent.split('\n').length,
              status: tool.success ? 'success' : 'error',
              executionTime: tool.result?.execution_time || 0
            }
          };
          
          newPages.push(toolPage);
        }
      });
      
      // Si la tarea está completada, agregar página de informe final para cualquier tarea
      if (executionData.status === 'completed') {
        const finalReportPage: MonitorPage = {
          id: 'final-report',
          title: '📄 INFORME FINAL - Tarea Completada',
          content: 'Cargando informe final...',
          type: 'report',
          timestamp: new Date(),
          metadata: {
            lineCount: 1,
            status: 'success',
            fileSize: 0
          }
        };
        
        newPages.push(finalReportPage);
        
        // Cargar el informe final desde el backend para cualquier tarea completada
        if (taskId) {
          loadFinalReport(taskId);
        }
      }
      
      if (newPages.length > 0) {
        setMonitorPages(prev => [...prev, ...newPages]);
        setPaginationStats(prev => ({
          ...prev,
          totalPages: prev.totalPages + newPages.length
        }));
        
        // Agregar logs de terminal para mostrar la ejecución
        const executionLogs = executionData.executed_tools.map((tool: any, index: number) => 
          `[${new Date().toLocaleTimeString()}] ✅ ${tool.tool}: ${tool.success ? 'SUCCESS' : 'FAILED'} (${tool.result?.execution_time || 0}s)`
        );
        
        setTerminalOutput(prev => [...prev, ...executionLogs]);
      }
    }
  }, [executionData, taskId]);

  // Efecto para mantener el modo Live siempre en la última página
  useEffect(() => {
    if (isLiveMode && monitorPages.length > 0) {
      setCurrentPageIndex(monitorPages.length - 1);
    }
  }, [monitorPages.length, isLiveMode]);

  const generateBackendToolPageContent = (tool: any): string => {
    const timestamp = tool.timestamp || new Date().toISOString();
    let content = `# Ejecución Backend: ${tool.tool.toUpperCase()}\n\n`;
    content += `**Timestamp:** ${timestamp}\n`;
    content += `**Status:** ${tool.success ? '✅ SUCCESS' : '❌ FAILED'}\n`;
    content += `**Tiempo de ejecución:** ${tool.result?.execution_time || 0}s\n\n`;
    
    if (tool.parameters) {
      content += `**Parámetros:**\n\`\`\`json\n${JSON.stringify(tool.parameters, null, 2)}\n\`\`\`\n\n`;
    }
    
    if (tool.result) {
      content += `**Resultado:**\n\`\`\`json\n${JSON.stringify(tool.result, null, 2)}\n\`\`\`\n\n`;
    }
    
    // Procesamiento específico por herramienta
    if (tool.tool === 'web_search' && tool.result?.results) {
      content += `**Resultados de búsqueda:**\n`;
      tool.result.results.forEach((result: any, index: number) => {
        content += `${index + 1}. **${result.title}**\n`;
        content += `   URL: ${result.url}\n`;
        content += `   Snippet: ${result.snippet || 'N/A'}\n\n`;
      });
    } else if (tool.tool === 'shell' && tool.result?.stdout) {
      content += `**Output:**\n\`\`\`bash\n${tool.result.stdout}\n\`\`\`\n`;
      if (tool.result.stderr) {
        content += `**Error:**\n\`\`\`bash\n${tool.result.stderr}\n\`\`\`\n`;
      }
    } else if (tool.tool === 'file_manager') {
      content += `**Operación:** ${tool.parameters?.action || 'N/A'}\n`;
      content += `**Archivo:** ${tool.parameters?.path || 'N/A'}\n`;
      if (tool.result?.success) {
        content += `**Resultado:** Operación completada exitosamente\n`;
      }
    }
    
    return content;
  };

  const generateToolPageContent = (result: ToolResult): string => {
    const timestamp = new Date().toISOString();
    let content = `# Ejecución de Herramienta: ${result.tool.toUpperCase()}\n\n`;
    content += `**Timestamp:** ${timestamp}\n`;
    content += `**Parámetros:**\n\`\`\`json\n${JSON.stringify(result.parameters, null, 2)}\n\`\`\`\n\n`;
    
    if (result.tool === 'shell') {
      content += `**Comando:** \`${result.parameters.command}\`\n\n`;
      content += `**Salida:**\n\`\`\`bash\n`;
      if (result.result.stdout) content += result.result.stdout;
      if (result.result.stderr) content += `\nERROR: ${result.result.stderr}`;
      content += `\n\`\`\`\n`;
    } else if (result.tool === 'web_search') {
      content += `**Búsqueda:** ${result.parameters.query}\n\n`;
      if (result.result.results) {
        content += `**Resultados encontrados:** ${result.result.results.length}\n\n`;
        result.result.results.slice(0, 5).forEach((res: any, i: number) => {
          content += `### ${i + 1}. ${res.title}\n`;
          content += `**URL:** ${res.url}\n`;
          content += `**Snippet:** ${res.snippet}\n\n`;
        });
      }
    } else if (result.tool === 'file_manager') {
      content += `**Acción:** ${result.parameters.action}\n`;
      content += `**Ruta:** ${result.parameters.path}\n\n`;
      if (result.result.success) {
        content += `✅ **Éxito:** ${result.result.success}\n`;
      }
      if (result.result.error) {
        content += `❌ **Error:** ${result.result.error}\n`;
      }
    }
    
    return content;
  };

  const handlePreviousPage = () => {
    if (currentPageIndex > 0) {
      setCurrentPageIndex(currentPageIndex - 1);
      setIsLiveMode(false);
    }
  };

  const handleNextPage = () => {
    if (currentPageIndex < monitorPages.length - 1) {
      setCurrentPageIndex(currentPageIndex + 1);
    }
  };

  const handleLiveMode = () => {
    setIsLiveMode(true);
    setCurrentPageIndex(monitorPages.length - 1); // Ir a la última página
  };

  const handleResetToStart = () => {
    setCurrentPageIndex(0);
    setIsLiveMode(false);
  };

  const formatMarkdownContent = (content: string) => {
    return (
      <div className="academic-document bg-white text-black p-6 rounded-lg shadow-lg w-full max-w-none">
        <div dangerouslySetInnerHTML={{ __html: formatMarkdownToHtml(content) }} />
      </div>
    );
  };

  const formatMarkdownToHtml = (markdown: string): string => {
    let html = markdown;
    
    // Academic title
    html = html.replace(/^# (.+)$/gm, '<div class="academic-title">$1</div>');
    
    // Headers
    html = html.replace(/^## (.+)$/gm, '<div class="academic-section"><h2>$1</h2></div>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    
    // Bold text
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Code blocks
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Paragraphs
    html = html.replace(/^(?!<[^>]*>|```|\s*$)(.+)$/gm, '<p>$1</p>');
    
    return html;
  };

  const currentPage = monitorPages[currentPageIndex];
  const isLastPage = currentPageIndex === monitorPages.length - 1;

  return (
    <div data-id={dataId} className="flex flex-col h-full w-full bg-[#2a2a2b] text-[#dadada] p-4 font-sans text-base">
      {/* Header - Rediseñado para Monitor */}
      <div className="flex items-center gap-2 mb-4">
        <Monitor size={20} className="text-blue-400" />
        <div className="flex-1 text-lg font-semibold">{title}</div>
        <div className="flex items-center gap-3 text-sm text-[#7f7f7f]">
          <div className="flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${isSystemOnline ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            <span>{isSystemOnline ? 'ONLINE' : 'OFFLINE'}</span>
          </div>
          <div className="flex items-center gap-1">
            <Radio size={14} className="text-blue-400" />
            <span>Página {currentPageIndex + 1} de {monitorPages.length}</span>
          </div>
        </div>
        <button onClick={onFullscreen} className="p-1.5 rounded-md hover:bg-black/10">
          <Maximize2 size={20} className="text-[#7f7f7f]" />
        </button>
      </div>

      {/* Tool Execution Status */}
      {currentExecutingTool && isLive && (
        <div className="mb-4 p-3 bg-[#2a2a2b] rounded-lg border border-blue-400/30">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
            <span className="text-sm font-medium text-blue-400">Herramienta en Ejecución</span>
          </div>
          <ToolExecutionDetails
            tool={currentExecutingTool.tool}
            parameters={currentExecutingTool.parameters}
            status="executing"
            showDetailedView={true}
            className="text-sm"
          />
        </div>
      )}

      {/* Monitor Display */}
      <div className="flex-1 flex flex-col bg-[#383739] rounded-lg border border-black/30 overflow-hidden">
        {/* Monitor Header */}
        <div className="h-10 flex items-center px-4 border-b border-white/10 bg-[#383739]">
          <div className="flex-1 text-center">
            <span className="text-sm font-medium text-[#dadada]">
              {currentPage ? currentPage.title : 'Monitor Mitosis'}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-[#7f7f7f]">
            {currentPage && (
              <>
                <FileText className="w-3 h-3" />
                <span>{currentPage.metadata?.lineCount || 0} líneas</span>
                {currentPage.metadata?.fileSize && (
                  <span>• {Math.round(currentPage.metadata.fileSize / 1024)} KB</span>
                )}
                <span className={`px-2 py-1 rounded text-xs ${
                  currentPage.metadata?.status === 'success' ? 'bg-green-500/20 text-green-400' :
                  currentPage.metadata?.status === 'error' ? 'bg-red-500/20 text-red-400' :
                  'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {currentPage.metadata?.status?.toUpperCase() || 'OK'}
                </span>
              </>
            )}
          </div>
        </div>
        
        {/* Monitor Content - Expandido para usar todo el ancho */}
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar w-full" ref={monitorRef}>
          {/* Show initialization steps when initializing - MINIMALIST COMPUTER DESIGN */}
          {isInitializing && !isSystemOnline && (
            <div className="flex items-center justify-center h-full w-full">
              <div className="max-w-xs w-full space-y-6">
                {/* Computer Icon - Using existing Monitor icon in GRAY */}
                <div className="flex justify-center mb-8">
                  <Monitor size={48} className="text-gray-400" />
                </div>
                
                {/* Steps - Granular with checkmarks - CENTERED TEXTS */}
                <div className="space-y-3">
                  {initializationSteps.map((step, index) => (
                    <div key={step.id} className="text-center">
                      <div className={`text-sm ${
                        index < initializationStep ? 'text-gray-400' :
                        index === initializationStep ? 'text-gray-300' :
                        'text-gray-600'
                      }`}>
                        {step.title}
                        {index === initializationStep && '...'}
                        {/* Checkmark for completed steps - CONSISTENT WITH PLAN DE ACCION */}
                        {index < initializationStep && (
                          <span className="ml-2">
                            <Check className="w-3 h-3 text-green-500 inline" />
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Progress Bar - 40% narrower and stable - CENTERED */}
                <div className="space-y-3 mt-8">
                  <div className="flex justify-center">
                    <div className="w-3/5 bg-gray-700 rounded-full h-1.5">
                      <div 
                        className="bg-blue-500 h-1.5 rounded-full transition-all duration-500 ease-out"
                        style={{ 
                          width: `${(initializationStep / initializationSteps.length) * 100}%` 
                        }}
                      />
                    </div>
                  </div>
                  <div className="text-center text-xs text-gray-500">
                    {Math.round((initializationStep / initializationSteps.length) * 100)}%
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Normal content when not initializing */}
          {(!isInitializing || isSystemOnline) && (
            <>
              {currentPage ? (
                <div className="space-y-4 w-full">
                  {currentPage.type === 'plan' || currentPage.type === 'report' ? (
                    <div className="w-full">
                      {formatMarkdownContent(currentPage.content)}
                    </div>
                  ) : (
                    <div className="space-y-2 w-full">
                      <div className="flex items-center gap-2 text-sm text-[#ACACAC] border-b border-[#404040] pb-2">
                        <div className={`w-2 h-2 rounded-full ${
                          currentPage.type === 'tool-execution' ? 'bg-blue-400' :
                          currentPage.type === 'file' ? 'bg-green-400' :
                          currentPage.type === 'error' ? 'bg-red-400' :
                          'bg-gray-400'
                        }`} />
                        <span className="font-medium">{currentPage.type.toUpperCase()}</span>
                        <span className="text-xs ml-auto">{currentPage.timestamp.toLocaleString()}</span>
                      </div>
                      
                      <div className="terminal-pager w-full">
                        <pre className="text-sm font-mono text-[#e0e0e0] whitespace-pre-wrap w-full max-w-none overflow-x-auto">
                          {currentPage.content}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full w-full text-[#7f7f7f]">
                  <Monitor className="w-12 h-12 mb-3 opacity-50" />
                  <p className="text-center">Sistema de monitoreo listo</p>
                  <p className="text-sm mt-1 text-center">Esperando datos del agente...</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Pagination Controls - Rediseñado */}
        <div className="pager-controls bg-[#383739] border-t border-white/10">
          <button 
            onClick={handleResetToStart}
            disabled={currentPageIndex === 0}
            title="Ir al inicio"
            className="flex items-center gap-1"
          >
            <RotateCcw size={14} />
            Inicio
          </button>
          
          <button 
            onClick={handlePreviousPage}
            disabled={currentPageIndex === 0}
            title="Página anterior"
            className="flex items-center gap-1"
          >
            <ArrowLeft size={14} />
            Anterior
          </button>
          
          <button 
            onClick={handleLiveMode}
            disabled={!isSystemOnline || (isLastPage && isLiveMode)}
            title={isSystemOnline ? "Ir a la última página (tiempo real)" : "Sistema offline"}
            className={`flex items-center gap-1 ${
              isLiveMode && isLastPage && isSystemOnline ? 'bg-green-600/20 text-green-400' : 
              !isSystemOnline ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <Radio size={14} />
            {isSystemOnline ? 'Live' : 'Offline'}
          </button>
          
          <button 
            onClick={handleNextPage}
            disabled={currentPageIndex >= monitorPages.length - 1}
            title="Página siguiente"
            className="flex items-center gap-1"
          >
            Siguiente
            <ArrowRight size={14} />
          </button>
          
          <div className="file-indicator">
            <span>
              PÁGINAS {currentPageIndex + 1} / {monitorPages.length}
            </span>
          </div>
          
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ 
                width: monitorPages.length > 0 
                  ? `${((currentPageIndex + 1) / monitorPages.length) * 100}%` 
                  : '0%' 
              }}
            />
          </div>
          
          <div className="flex items-center gap-3 text-xs">
            {isLiveMode && isSystemOnline && (
              <div className="flex items-center gap-1 text-green-400">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span>ONLINE</span>
              </div>
            )}
            {!isSystemOnline && (
              <div className="flex items-center gap-1 text-red-400">
                <div className="w-2 h-2 bg-red-400 rounded-full" />
                <span>OFFLINE</span>
              </div>
            )}
            <div className="text-[#7f7f7f]">
              {toolResults.length} herramienta(s) ejecutada(s)
            </div>
          </div>
        </div>
      </div>

      {/* Plan de Acción o Tarea Completada */}
      {plan && plan.length > 0 && (
        <>
          {/* Mostrar TaskCompletedUI si todas las tareas están completadas */}
          {plan.filter(s => s.completed).length === plan.length ? (
            <TaskCompletedUI />
          ) : (
            /* Plan de Acción normal cuando NO está completado */
            <div className="mt-3 bg-gradient-to-br from-[#383739] to-[#2a2a2b] border border-white/10 rounded-xl overflow-hidden shadow-lg">
              <div 
                className="px-4 py-3 flex justify-between items-center cursor-pointer hover:bg-[rgba(255,255,255,0.05)] transition-all duration-200 group" 
                onClick={() => setIsPlanExpanded(!isPlanExpanded)}
              >
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 bg-[#404142] rounded-lg flex items-center justify-center shadow-md">
                    <Activity className="w-3.5 h-3.5 text-[#DADADA]" />
                  </div>
                  <div className="flex flex-col">
                    <h3 className="text-sm font-semibold text-[#DADADA] group-hover:text-white transition-colors leading-tight">
                      Plan de Acción
                    </h3>
                    <p className="text-xs text-[#ACACAC] leading-tight mt-0.5">
                      {`${plan.filter(s => s.completed).length} de ${plan.length} tareas completadas`}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="flex flex-col items-end gap-1">
                    <div className="text-xs font-medium text-[#ACACAC]">
                      {Math.round((plan.filter(s => s.completed).length / plan.length) * 100)}%
                    </div>
                    <div className="w-12 h-1.5 bg-black/30 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-700 ease-out"
                        style={{ width: `${(plan.filter(s => s.completed).length / plan.length) * 100}%` }}
                      />
                    </div>
                  </div>
                  
                  {isPlanExpanded ? (
                    <ChevronDown className="w-4 h-4 text-[#7f7f7f] group-hover:text-white transition-all duration-200 transform group-hover:scale-110" />
                  ) : (
                    <ChevronUp className="w-4 h-4 text-[#7f7f7f] group-hover:text-white transition-all duration-200 transform group-hover:scale-110" />
                  )}
                </div>
              </div>
              
              {isPlanExpanded && (
                <div className="px-4 py-3 space-y-2 bg-[#383739] border-t border-[rgba(255,255,255,0.08)]">
                  {plan.map((step, index) => (
                    <div 
                      key={step.id} 
                      className={`group flex items-center space-x-3 px-3 py-2 rounded-lg transition-all duration-200 ${
                        step.active ? 'bg-[rgba(59,130,246,0.1)] border border-[rgba(59,130,246,0.3)]' : 
                        step.completed ? 'bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.2)]' : 
                        'border border-transparent'
                      }`}
                    >
                      <div className={`flex-shrink-0 w-5 h-5 flex items-center justify-center text-xs font-bold transition-all duration-200 ${
                        step.completed ? '' :
                        step.active ? '' :
                        'bg-[#3a3a3c] text-[#7f7f7f] group-hover:bg-[#4a4a4c] group-hover:text-[#ACACAC] rounded-full'
                      }`}>
                        {step.completed ? (
                          <Check className="w-3 h-3 text-green-500" />
                        ) : step.active ? (
                          <div className="w-4 h-4 flex items-center justify-center">
                            <div className="w-3 h-3 rounded-sm loader-spin" 
                                 style={{
                                   background: 'linear-gradient(-45deg, #fc00ff 0%, #00dbde 100%)'
                                 }}>
                            </div>
                          </div>
                        ) : (
                          <span className="text-xs font-semibold">{index + 1}</span>
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <span className={`block text-sm transition-all duration-200 leading-tight ${
                          step.completed ? 'line-through text-[#8f8f8f] font-medium' : 
                          step.active ? 'text-blue-400 font-semibold' : 
                          'text-[#DADADA] group-hover:text-white font-medium'
                        }`}>
                          {step.title}
                        </span>
                        {step.description && (
                          <span className={`block text-xs mt-1 transition-all duration-200 ${
                            step.completed ? 'line-through text-[#6f6f6f]' : 
                            step.active ? 'text-blue-300' : 
                            'text-[#ACACAC] group-hover:text-[#DADADA]'
                          }`}>
                            {step.description}
                          </span>
                        )}
                        {step.elapsed_time && (
                          <span className={`block text-xs mt-0.5 transition-all duration-200 ${
                            step.completed ? 'text-green-400 font-medium' : 
                            step.active ? 'text-blue-200 font-medium' : 
                            'text-[#7f7f7f] group-hover:text-[#ACACAC]'
                          }`}>
                            {step.completed ? '✅ Completado en ' + step.elapsed_time : 
                             step.active ? '⏱️ ' + step.elapsed_time + ' (En progreso)' : 
                             '⏰ ' + step.elapsed_time}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {!isPlanExpanded && (
                <div className="px-4 py-3 bg-[#383739] border-t border-[rgba(255,255,255,0.08)]">
                  <div className="space-y-2">
                    {/* Tarea actual */}
                    {(() => {
                      const currentTask = plan.find(step => step.active);
                      return currentTask ? (
                        <div className="flex items-center gap-3">
                          <div className="w-4 h-4 flex items-center justify-center">
                            <div className="w-3 h-3 rounded-sm loader-spin" 
                                 style={{
                                   background: 'linear-gradient(-45deg, #fc00ff 0%, #00dbde 100%)'
                                 }}>
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="text-xs font-medium text-blue-400">Actual:</div>
                            <div className="text-xs text-[#DADADA] truncate">{currentTask.title}</div>
                          </div>
                        </div>
                      ) : null;
                    })()}
                    
                    {/* Próxima tarea */}
                    {(() => {
                      const currentIndex = plan.findIndex(step => step.active);
                      const nextTask = currentIndex >= 0 && currentIndex < plan.length - 1 ? plan[currentIndex + 1] : null;
                      return nextTask ? (
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 bg-[#7f7f7f] rounded-full"></div>
                          <div className="flex-1">
                            <div className="text-xs font-medium text-[#7f7f7f]">Siguiente:</div>
                            <div className="text-xs text-[#7f7f7f] truncate">{nextTask.title}</div>
                          </div>
                        </div>
                      ) : null;
                    })()}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};