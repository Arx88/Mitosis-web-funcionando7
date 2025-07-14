import React, { useEffect, useState, useRef } from 'react';
import { Check, ChevronDown, Maximize2, Rewind, Terminal, AlertCircle, CheckCircle, Circle, ChevronUp, Clock, Activity, Zap, FileText, SkipBack, SkipForward, Monitor, Radio, ArrowLeft, ArrowRight, RotateCcw } from 'lucide-react';
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
  externalLogs?: Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>;
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
  externalLogs = []
}: TerminalViewProps) => {
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [isPlanExpanded, setIsPlanExpanded] = useState(true);
  const [currentExecutingTool, setCurrentExecutingTool] = useState<ToolResult | null>(null);
  const [monitorPages, setMonitorPages] = useState<MonitorPage[]>([]);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [isLiveMode, setIsLiveMode] = useState(true);
  const [paginationStats, setPaginationStats] = useState({
    totalPages: 0,
    currentPage: 1,
    limit: 20,
    offset: 0
  });
  const monitorRef = useRef<HTMLDivElement>(null);

  // Inicializar con TODO.md como Página 1
  useEffect(() => {
    if (plan && plan.length > 0 && monitorPages.length === 0) {
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
  }, [plan]);

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
            <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-400 animate-pulse' : 'bg-[#7f7f7f]'}`} />
            <span>{isLive ? 'En vivo' : 'Offline'}</span>
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
            <div className="text-center text-[#7f7f7f] py-8 w-full">
              <Monitor className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Inicializando sistema de monitoreo...</p>
              <p className="text-sm mt-1">Esperando datos del agente...</p>
            </div>
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
            disabled={isLastPage && isLiveMode}
            title="Ir a la última página (tiempo real)"
            className={`flex items-center gap-1 ${isLiveMode && isLastPage ? 'bg-green-600/20 text-green-400' : ''}`}
          >
            <Radio size={14} />
            Live
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
            {isLiveMode && (
              <div className="flex items-center gap-1 text-green-400">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span>MODO LIVE</span>
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
                      className={`group flex items-center space-x-3 cursor-pointer hover:bg-[rgba(255,255,255,0.05)] px-3 py-2 rounded-lg transition-all duration-200 ${
                        step.active ? 'bg-[rgba(59,130,246,0.1)] border border-[rgba(59,130,246,0.3)]' : 
                        step.completed ? 'bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.2)]' : 
                        'border border-transparent hover:border-[rgba(255,255,255,0.1)]'
                      }`}
                      onClick={() => onToggleTaskStep?.(step.id)}
                    >
                      <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-200 ${
                        step.completed ? 'bg-green-500 text-white shadow-md' :
                        step.active ? 'bg-blue-500 text-white animate-pulse shadow-md' :
                        'bg-[#3a3a3c] text-[#7f7f7f] group-hover:bg-[#4a4a4c] group-hover:text-[#ACACAC]'
                      }`}>
                        {step.completed ? (
                          <CheckCircle className="w-3 h-3" />
                        ) : (
                          <span className="text-xs font-semibold">{index + 1}</span>
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <span className={`block text-sm transition-all duration-200 leading-tight ${
                          step.completed ? 'line-through text-[#8f8f8f] font-normal' : 
                          step.active ? 'text-blue-400 font-semibold' : 
                          'text-[#DADADA] group-hover:text-white font-normal'
                        }`}>
                          {step.title}
                        </span>
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
                          <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
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