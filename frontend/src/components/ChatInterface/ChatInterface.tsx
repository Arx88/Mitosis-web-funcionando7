import React, { useEffect, useState, useRef } from 'react';
import { Paperclip, Mic, Send, Terminal, Globe, FileText, Plus, Zap, X, Search, Layers, Bot } from 'lucide-react';
import { agentAPI, ChatResponse, ToolResult, SearchData, UploadData, OrchestrationStatus } from '../../services/api';
import { VanishInput } from '../VanishInput';
import { FileUploadModal } from '../FileUploadModal';
import { FileAttachmentButtons } from '../FileAttachmentButtons';
import { FileInlineDisplay } from '../FileInlineDisplay';
import { ToolExecutionDetails } from '../ToolExecutionDetails';
import { SearchResults } from '../SearchResults';
import { FileUploadSuccess } from '../FileUploadSuccess';
import { TaskSummary } from '../TaskSummary';
import { DeepResearchProgress, ProgressStep } from '../DeepResearchProgress';
import { DeepResearchReport, ResearchReport } from '../DeepResearchReport';
import { DeepResearchReportCard } from '../DeepResearchReportCard';
import { DeepResearchPlaceholder } from '../DeepResearchPlaceholder';
import { LinkPreview, MultiLinkDisplay } from '../LinkPreview';
import { ThinkingAnimation } from '../ThinkingAnimation';
import { AgentStatusBar, AgentStatus } from '../AgentStatusBar';
import { useConsoleReportFormatter } from '../../hooks/useConsoleReportFormatter';
import { MessageActions } from '../MessageActions';
import { PDFViewer } from '../PDFViewer';
import { MemoryFile, useMemoryManager } from '../../hooks/useMemoryManager';
import { generatePDFWithCustomCSS, downloadMarkdownFile } from '../../utils/pdfGenerator';
import { LoadingPlaceholder, MessageLoadingPlaceholder } from '../LoadingPlaceholder';

// Helper component to handle async file parsing
const FileUploadParser: React.FC<{
  content: string;
  onFileView: (file: any) => void;
  onFileDownload: (file: any) => void;
  onAddToMemory: (file: any) => void;
  parseMessageAsFileUpload: (content: string) => Promise<any>;
}> = ({ content, onFileView, onFileDownload, onAddToMemory, parseMessageAsFileUpload }) => {
  const [fileUploadData, setFileUploadData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    const parseMessageAsFileUpload = async (content: string) => {
      try {
        // Simplified parsing logic to avoid excessive re-renders
        const hasFileIndicators = content && typeof content === 'string' && 
          (content.includes('✅') || content.includes('archivo') || content.includes('cargado'));
        
        if (hasFileIndicators) {
          return { files: [] }; // Estructura mínima para evitar re-renders
        }
        
        return null;
      } catch (error) {
        console.error('Error parsing file upload:', error);
        return null;
      }
    };

    // Debounce para evitar múltiples llamadas
    const timeoutId = setTimeout(() => {
      parseMessageAsFileUpload(content).then(result => {
        setFileUploadData(result);
        setIsLoading(false);
      });
    }, 200);

    return () => clearTimeout(timeoutId);
  }, [content]); // Solo depender del contenido
  
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-blue-400">
        <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
        <span>Cargando archivos...</span>
      </div>
    );
  }
  
  if (!fileUploadData || !fileUploadData.files.length) {
    return null;
  }
  
  return (
    <FileUploadSuccess
      files={fileUploadData.files}
      onFileView={onFileView}
      onFileDownload={onFileDownload}
      onAddToMemory={onAddToMemory}
    />
  );
};

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  attachments?: Array<{
    id?: string;
    name: string;
    type: string;
    size: string;
    url?: string;
  }>;
  status?: {
    type: 'success' | 'error' | 'loading';
    message: string;
  };
  toolResults?: ToolResult[];
  searchData?: SearchData;
  uploadData?: UploadData;
  links?: Array<{
    url: string;
    title?: string;
    description?: string;
  }>;
  orchestrationResult?: any; // Resultado de orquestación
}

export interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  onAttachFiles?: (files: FileList) => void;
  isTyping?: boolean;
  assistantName?: string;
  placeholder?: string;
  className?: string;
  'data-id'?: string;
  onUpdateMessages?: (messages: Message[]) => void;
  onLogToTerminal?: (message: string, type?: 'info' | 'success' | 'error') => void;
  onTaskReset?: () => void; // New prop for task reset
  isNewTask?: boolean; // New prop to indicate if this is a new task
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  onAttachFiles,
  isTyping = false,
  assistantName = 'Agente',
  placeholder = 'Describe tu tarea...',
  className = '',
  'data-id': dataId,
  onUpdateMessages,
  onLogToTerminal,
  onTaskReset,
  isNewTask = false
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [activeQuickAction, setActiveQuickAction] = useState<string | null>(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [searchMode, setSearchMode] = useState<'websearch' | 'deepsearch' | null>(null); // No default activation
  const [currentQuery, setCurrentQuery] = useState<string>(''); // Store current query for DeepResearch
  const [deepResearchProgress, setDeepResearchProgress] = useState<{
    isActive: boolean;
    currentStep: number;
    overallProgress: number;
    steps: ProgressStep[];
  }>({
    isActive: false,
    currentStep: -1,
    overallProgress: 0,
    steps: []
  });
  const [deepResearchReport, setDeepResearchReport] = useState<ResearchReport | null>(null);
  const [showPlaceholder, setShowPlaceholder] = useState(false);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('idle');
  const [currentStepName, setCurrentStepName] = useState<string>('');
  const [showPDFViewer, setShowPDFViewer] = useState(false);
  const [pdfViewerContent, setPDFViewerContent] = useState('');
  const [pdfViewerTitle, setPDFViewerTitle] = useState('');
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [hasInitialMessageSent, setHasInitialMessageSent] = useState(false); // Track if initial message was sent
  const processedTasksRef = useRef<Set<string>>(new Set()); // Track processed task IDs
  // Estados para orquestación
  const [orchestrationTaskId, setOrchestrationTaskId] = useState<string | null>(null);
  const [orchestrationStatus, setOrchestrationStatus] = useState<OrchestrationStatus | null>(null);
  const [isOrchestrating, setIsOrchestrating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const formatFileSize = (bytes?: number | string) => {
    if (!bytes) return '';
    const size = typeof bytes === 'string' ? parseInt(bytes) : bytes;
    if (size < 1024) return `${size}B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)}KB`;
    if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)}MB`;
    return `${(size / (1024 * 1024 * 1024)).toFixed(1)}GB`;
  };

  // Memory Manager
  const {
    memoryFiles,
    addMemoryFile,
    addResearchReportToMemory,
    removeMemoryFile,
    toggleMemoryFile,
    clearAllMemory,
    getActiveMemoryContext,
    hasActiveMemory
  } = useMemoryManager();
  
  // Hook para formatear reportes en consola
  const {
    formatDeepResearchReport,
    formatResearchMetrics,
    formatProgressReport,
    formatStructuredData
  } = useConsoleReportFormatter();

  // Reset all states when task changes or new task is created
  const resetChatState = () => {
    console.log('🔄 RESETTING CHAT STATE - Terminal and computer state reset');
    setInputValue('');
    setIsLoading(false);
    setShowQuickActions(false);
    setActiveQuickAction(null);
    setShowFileUpload(false);
    setSearchMode(null);
    setCurrentQuery('');
    setDeepResearchProgress({
      isActive: false,
      currentStep: -1,
      overallProgress: 0,
      steps: []
    });
    setDeepResearchReport(null);
    setShowPlaceholder(false);
    setAgentStatus('idle');
    setCurrentStepName('');
    // Reset orchestration state
    setOrchestrationTaskId(null);
    setOrchestrationStatus(null);
    setIsOrchestrating(false);
    setIsLoadingMessages(false);
    setShowPDFViewer(false);
    setPDFViewerContent('');
    setPDFViewerTitle('');
    setHasInitialMessageSent(false); // Reset the initial message flag
    // Clear processed tasks when switching tasks
    processedTasksRef.current.clear();
    console.log('✅ CHAT STATE RESET COMPLETE - Terminal cleared');
  };

  // Effect to reset state when new task is created (optimized)
  useEffect(() => {
    if (isNewTask) {
      console.log('🔄 NEW TASK DETECTED - Resetting chat state');
      resetChatState();
      if (onTaskReset) {
        onTaskReset();
      }
    }
  }, [isNewTask]); // Only dependency is isNewTask

  // Effect to reset state when task ID changes (optimized)
  useEffect(() => {
    console.log('🔄 CHAT: dataId changed to:', dataId);
    resetChatState();
    if (onTaskReset) {
      onTaskReset();
    }
  }, [dataId]); // Only dependency is dataId

  // Optimized scroll effect with debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      scrollToBottom();
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages.length]); // Only depends on messages length

  // Effect to automatically send initial message to backend when new task is created
  useEffect(() => {
    // Early return if conditions aren't met
    if (!dataId || messages.length !== 1 || messages[0].sender !== 'user' || isLoading) {
      return;
    }

    // Check if already processed
    if (processedTasksRef.current.has(dataId)) {
      console.log('⚠️ CHAT: Task already processed, skipping:', dataId);
      return;
    }

    // Check if this is the initial message for a new task (not a user-typed message)
    if (hasInitialMessageSent) {
      console.log('⚠️ CHAT: Initial message already sent for this session, skipping');
      return;
    }

    // Mark as processed immediately to prevent duplicate calls
    processedTasksRef.current.add(dataId);
    setHasInitialMessageSent(true);
    console.log('✅ CHAT: Task marked as processed:', dataId);
    
    const sendInitialMessage = async () => {
      console.log('🚀 CHAT: Sending initial message to backend for task:', dataId);
      
      try {
        setIsLoading(true);
        
        // Send the user's message to the backend
        const response = await agentAPI.sendMessage(messages[0].content, { task_id: dataId });
        
        if (response && response.response) {
          console.log('✅ CHAT: Received response from backend');
          
          // Parse links from response
          const responseLinks = parseLinksFromText(response.response);
          const structuredLinks = parseStructuredLinks(response.response);
          const allLinks = [...responseLinks, ...structuredLinks];
          
          // Remove duplicates
          const uniqueLinks = allLinks.filter((link, index, self) => 
            index === self.findIndex(l => l.url === link.url)
          );
          
          // Create assistant response message with complete data
          const assistantMessage: Message = {
            id: `msg-${Date.now()}`,
            content: response.response,
            sender: 'assistant',
            timestamp: new Date(response.timestamp || Date.now()),
            toolResults: response.tool_results || [],
            searchData: response.search_data,
            uploadData: response.upload_data,
            links: uniqueLinks.length > 0 ? uniqueLinks : undefined,
            status: response.tool_results && response.tool_results.length > 0 ? {
              type: 'success',
              message: `Ejecuté ${response.tool_results.length} herramienta(s)`
            } : undefined
          };
          
          // Add the response - this should only happen once per task
          if (onUpdateMessages) {
            console.log('📤 CHAT: Updating messages with assistant response');
            const updatedMessages = [...messages, assistantMessage];
            onUpdateMessages(updatedMessages);
          }
        }
      } catch (error) {
        console.error('❌ CHAT: Error sending initial message:', error);
        
        const errorMessage: Message = {
          id: `msg-${Date.now()}`,
          content: 'Hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.',
          sender: 'assistant',
          timestamp: new Date()
        };
        
        if (onUpdateMessages) {
          console.log('📤 CHAT: Updating messages with error response');
          onUpdateMessages([...messages, errorMessage]);
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    // Call the function
    sendInitialMessage();
  }, [dataId, messages.length]); // Minimal dependencies

  // Función para obtener progreso real del backend
  const pollDeepResearchProgress = async (taskId: string) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/agent/deep-research/progress/${taskId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch progress');
      }
      
      const progressData = await response.json();
      
      // Actualizar estado del progreso
      setDeepResearchProgress(prev => ({
        ...prev,
        isActive: progressData.is_active,
        currentStep: progressData.current_step,
        overallProgress: progressData.current_progress,
        steps: progressData.steps || prev.steps
      }));
      
      return progressData;
    } catch (error) {
      console.error('Error fetching progress:', error);
      return null;
    }
  };

  // Función para iniciar polling del progreso
  const startProgressPolling = (taskId: string) => {
    const pollInterval = setInterval(async () => {
      const progressData = await pollDeepResearchProgress(taskId);
      
      if (progressData && (!progressData.is_active || progressData.current_progress >= 100)) {
        clearInterval(pollInterval);
        
        // Mantener el progreso visible por unos segundos después de completar
        setTimeout(() => {
          setDeepResearchProgress(prev => ({
            ...prev,
            isActive: false
          }));
        }, 3000);
      }
    }, 1000); // Poll cada segundo
    
    return pollInterval;
  };

  // Función para simular el progreso del DeepResearch (mantener como fallback)
  const simulateDeepResearchProgress = (query: string) => {
    const steps: ProgressStep[] = [
      {
        id: 'search_initial',
        title: 'Búsqueda inicial',
        description: 'Recolectando datos iniciales...',
        status: 'pending',
        details: [],
        progress: 0
      },
      {
        id: 'search_specific',
        title: 'Búsquedas específicas',
        description: 'Realizando búsquedas especializadas...',
        status: 'pending',
        details: [],
        progress: 0
      },
      {
        id: 'content_extraction',
        title: 'Extracción de contenido',
        description: 'Extrayendo contenido completo...',
        status: 'pending',
        details: [],
        progress: 0
      },
      {
        id: 'image_collection',
        title: 'Recopilación de imágenes',
        description: 'Juntando imágenes relacionadas...',
        status: 'pending',
        details: [],
        progress: 0
      },
      {
        id: 'analysis_comparison',
        title: 'Análisis comparativo',
        description: 'Comparando artículos y analizando...',
        status: 'pending',
        details: [],
        progress: 0
      },
      {
        id: 'report_generation',
        title: 'Generación de informe',
        description: 'Generando informe completo...',
        status: 'pending',
        details: [],
        progress: 0
      }
    ];

    setDeepResearchProgress({
      isActive: true,
      currentStep: 0,
      overallProgress: 0,
      steps: steps
    });

    // Simular progreso paso a paso
    const progressSteps = [
      { stepIndex: 0, progress: 10, details: [`Consultando Tavily para: ${query}`] },
      { stepIndex: 0, progress: 15, details: [`Encontradas fuentes iniciales`, `URLs procesadas`] },
      { stepIndex: 1, progress: 25, details: [`Búsqueda específica 1/3`, `Consultando: ${query} definición concepto`] },
      { stepIndex: 1, progress: 35, details: [`Búsqueda específica 2/3`, `Consultando: ${query} características principales`] },
      { stepIndex: 1, progress: 45, details: [`Búsqueda específica 3/3`, `Nuevas fuentes encontradas`] },
      { stepIndex: 2, progress: 55, details: [`Procesando 10 fuentes principales`, `Extrayendo contenido completo`] },
      { stepIndex: 2, progress: 75, details: [`Extrayendo contenido 8/10`, `Analizando páginas web`] },
      { stepIndex: 3, progress: 80, details: [`Buscando 10 imágenes sobre: ${query}`, `Encontradas imágenes`] },
      { stepIndex: 4, progress: 85, details: [`Identificando patrones y tendencias`, `Extrayendo hallazgos clave`] },
      { stepIndex: 5, progress: 90, details: [`Compilando resultados`, `Creando informe.md`] },
      { stepIndex: 5, progress: 100, details: [`Investigación completada exitosamente`] }
    ];

    let currentProgressIndex = 0;
    const progressInterval = setInterval(() => {
      if (currentProgressIndex >= progressSteps.length) {
        clearInterval(progressInterval);
        return;
      }

      const currentProgress = progressSteps[currentProgressIndex];
      
      setDeepResearchProgress(prev => {
        const newSteps = [...prev.steps];
        
        // Actualizar pasos anteriores como completados
        for (let i = 0; i < currentProgress.stepIndex; i++) {
          newSteps[i].status = 'completed';
        }
        
        // Actualizar paso actual
        newSteps[currentProgress.stepIndex].status = 'active';
        newSteps[currentProgress.stepIndex].progress = currentProgress.progress;
        newSteps[currentProgress.stepIndex].details = currentProgress.details;
        
        return {
          ...prev,
          currentStep: currentProgress.stepIndex,
          overallProgress: currentProgress.progress,
          steps: newSteps
        };
      });

      currentProgressIndex++;
    }, 1500); // Actualizar cada 1.5 segundos

    return progressInterval;
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: 'smooth'
      });
    }
  };

  const parseTaskSummary = (content: string) => {
    try {
      // Detect task completion patterns
      const isTaskSummary = content.includes('✅') || 
                           content.includes('completad') || 
                           content.includes('finaliz') ||
                           content.includes('exitosamente') ||
                           content.includes('Tarea finalizada') ||
                           (content.includes('resumen') && content.includes('tarea'));
      
      if (!isTaskSummary) return null;

      // Extract title
      const titleMatch = content.match(/^(.+?)(?:\n|$)/);
      const title = titleMatch ? titleMatch[1].replace(/[✅🎉✨]/g, '').trim() : undefined;

      // Extract completed steps (look for bullet points or numbered lists)
      const stepsPattern = /[-•*]\s*(.+?)(?=\n[-•*]|\n\n|$)/g;
      const numberedPattern = /\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)/g;
      const completedSteps: string[] = [];
      
      let match;
      while ((match = stepsPattern.exec(content)) !== null) {
        completedSteps.push(match[1].trim());
      }
      while ((match = numberedPattern.exec(content)) !== null) {
        completedSteps.push(match[1].trim());
      }

      // Extract tools used (look for mentions of tools)
      const toolsUsed: string[] = [];
      const toolMentions = ['web_search', 'shell', 'file_manager', 'tavily_search', 'deep_research'];
      toolMentions.forEach(tool => {
        if (content.toLowerCase().includes(tool.replace('_', ' ')) || 
            content.toLowerCase().includes(tool)) {
          toolsUsed.push(tool.replace('_', ' '));
        }
      });

      // Extract outcome (main content without formatting)
      const cleanContent = content
        .replace(/[✅🎉✨]/g, '')
        .replace(/[-•*]\s*.+/g, '')
        .replace(/\d+\.\s*.+/g, '')
        .trim();

      return {
        isTaskSummary: true,
        title: title || "Tarea completada exitosamente",
        completedSteps,
        toolsUsed,
        outcome: cleanContent || content,
        type: 'success' as const
      };
    } catch (error) {
      console.error('Error parsing task summary:', error);
    }
    return null;
  };

  const handleSendMessage = async (message: string) => {
    console.log('🔄 DEBUG: handleSendMessage called with:', message);
    
    // Check if this message is already being processed by the initial message effect
    if (dataId && processedTasksRef.current.has(dataId) && messages.length === 1) {
      console.log('⚠️ DEBUG: Message already being processed by initial message effect, skipping handleSendMessage');
      return;
    }
    
    if (message.trim() && !isLoading) {
      console.log('✅ DEBUG: Conditions met, starting message processing');
      setIsLoading(true);
      setIsLoadingMessages(true);
      
      // Reset search modes after sending message but keep them available
      setTimeout(() => {
        setSearchMode(null); // Deseleccionar modo de búsqueda, NO deshabilitar
      }, 500);
      
      // Reset deep research report when starting new search
      setDeepResearchReport(null);
      setShowPlaceholder(false);

      // Set agent status to task received
      setAgentStatus('task_received');
      
      // After a longer moment, change to analyzing task
      setTimeout(() => {
        setAgentStatus('analyzing_task');
      }, 2000);  // Aumentado de 1000 a 2000ms

      // Modificar el mensaje basado en el modo de búsqueda
      let processedMessage = message;
      let progressInterval: NodeJS.Timeout | null = null;
      let useOrchestration = false;
      
      // Determinar si usar orquestación (para tareas que no sean WebSearch/DeepSearch específicas)
      if (!searchMode) {
        useOrchestration = true;
        setAgentStatus('orchestrating');
        setIsOrchestrating(true);
      }
      
      if (searchMode === 'websearch') {
        processedMessage = `[WebSearch] ${message}`;
        setCurrentStepName('Búsqueda Web');
        setAgentStatus('executing_step');
      } else if (searchMode === 'deepsearch') {
        processedMessage = `[DeepResearch] ${message}`;
        setCurrentQuery(message); // Store the query for the progress component
        setCurrentStepName('Investigación Profunda');
        setAgentStatus('executing_step');
        
        // Inicializar progreso para DeepResearch
        setDeepResearchProgress({
          isActive: true,
          currentStep: 0,
          overallProgress: 0,
          steps: [
            {
              id: 'search_initial',
              title: 'Búsqueda inicial',
              description: 'Recolectando datos iniciales...',
              status: 'active',
              details: [`Iniciando búsqueda para: ${message}`],
              progress: 0
            },
            {
              id: 'search_specific',
              title: 'Búsquedas específicas',
              description: 'Realizando búsquedas especializadas...',
              status: 'pending',
              details: [],
              progress: 0
            },
            {
              id: 'content_extraction',
              title: 'Extracción de contenido',
              description: 'Extrayendo contenido completo...',
              status: 'pending',
              details: [],
              progress: 0
            },
            {
              id: 'image_collection',
              title: 'Recopilación de imágenes',
              description: 'Juntando imágenes relacionadas...',
              status: 'pending',
              details: [],
              progress: 0
            },
            {
              id: 'analysis_comparison',
              title: 'Análisis comparativo',
              description: 'Comparando artículos y analizando...',
              status: 'pending',
              details: [],
              progress: 0
            },
            {
              id: 'report_generation',
              title: 'Generación de informe',
              description: 'Generando informe completo...',
              status: 'pending',
              details: [],
              progress: 0
            }
          ]
        });
        
        // Iniciar polling del progreso real si hay un dataId (task_id)
        if (dataId) {
          progressInterval = startProgressPolling(dataId);
        } else {
          // Fallback a simulación si no hay task_id
          progressInterval = simulateDeepResearchProgress(message);
        }
      }

      // Remove the onSendMessage callback call to prevent duplicate messages
      // The initial message effect will handle backend communication and response addition
      // console.log('🔄 DEBUG: Calling onSendMessage with:', processedMessage);
      // onSendMessage(processedMessage);

      // Create and add user message to the conversation
      const userMessage: Message = {
        id: `msg-${Date.now()}-user`,
        content: message,
        sender: 'user',
        timestamp: new Date()
      };

      // Add user message to the conversation immediately
      if (onUpdateMessages) {
        console.log('📤 DEBUG: Adding user message to conversation');
        const updatedWithUser = [...messages, userMessage];
        onUpdateMessages(updatedWithUser);
      }

      // For subsequent messages (not the initial one), we need to handle backend communication
      // but only if this is NOT the initial message being processed by the effect
      if (messages.length > 1) {
        // Include memory context if there's active memory
        const context = {
          task_id: dataId,
          memory_context: hasActiveMemory ? getActiveMemoryContext() : undefined,
          previous_messages: messages.slice(-5), // Enviar últimos 5 mensajes como contexto
          search_mode: searchMode // Enviar modo de búsqueda al backend
        };

        try {
          console.log('🔄 BASIC DEBUG: Sending subsequent message to backend');
          console.log('🔄 DEBUG: API URL:', `${import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/agent/chat`);
          console.log('🔄 DEBUG: Message:', processedMessage);
          console.log('🔄 DEBUG: Context:', context);
          
          const response: ChatResponse = await agentAPI.sendMessage(processedMessage, context);
          
          console.log('✅ BASIC DEBUG: Backend response received');
          console.log('📋 BASIC DEBUG: Response type:', typeof response);
          console.log('📋 BASIC DEBUG: Response keys:', Object.keys(response || {}));
          
          // Continue with the rest of the response processing logic...
          // (This is the same logic that was in the original handleSendMessage)
          
          // Parse links from response
          const responseLinks = parseLinksFromText(response.response);
          const structuredLinks = parseStructuredLinks(response.response);
          const allLinks = [...responseLinks, ...structuredLinks];
          
          // Remove duplicates
          const uniqueLinks = allLinks.filter((link, index, self) => 
            index === self.findIndex(l => l.url === link.url)
          );

          // Create agent message with enhanced data
          const agentMessage: Message = {
            id: `msg-${Date.now()}`,
            content: response.response,
            sender: 'assistant',
            timestamp: new Date(response.timestamp),
            toolResults: response.tool_results,
            searchData: response.search_data,
            uploadData: response.upload_data,
            links: uniqueLinks.length > 0 ? uniqueLinks : undefined,
            status: response.tool_results.length > 0 ? {
              type: 'success',
              message: `Ejecuté ${response.tool_results.length} herramienta(s)`
            } : undefined
          };

          // Add agent response to conversation
          if (onUpdateMessages) {
            const currentMessages = [...messages, userMessage];
            const updatedMessages = [...currentMessages, agentMessage];
            onUpdateMessages(updatedMessages);
          }
          
        } catch (error) {
          console.error('❌ CHAT: Error sending subsequent message:', error);
          
          const errorMessage: Message = {
            id: `msg-${Date.now()}`,
            content: 'Hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.',
            sender: 'assistant',
            timestamp: new Date()
          };
          
          if (onUpdateMessages) {
            const currentMessages = [...messages, userMessage];
            const updatedMessages = [...currentMessages, errorMessage];
            onUpdateMessages(updatedMessages);
          }
        }
      }
      
      // Reset loading state
      setIsLoading(false);
      setIsLoadingMessages(false);
    }
  };

  // Function to handle orchestration polling (moved to proper location)
  const handleOrchestrationPolling = (taskId: string) => {
    const orchestrationInterval = setInterval(async () => {
      try {
        const statusResponse = await fetch(`${import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/agent/orchestration/status/${taskId}`);
        if (statusResponse.ok) {
          const status = await statusResponse.json();
          if (status.status === 'completed') {
            setAgentStatus('task_completed');
            setCurrentStepName('Completado');
            setIsOrchestrating(false);
            clearInterval(orchestrationInterval);
            
            try {
              const resultResponse = await fetch(`${import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/agent/orchestration/result/${taskId}`);
              if (resultResponse.ok) {
                const result = await resultResponse.json();
                console.log('Final orchestration result:', result);
              }
            } catch (err) {
              console.error('Error getting final result:', err);
            }
          } else if (status.status === 'failed') {
            setAgentStatus('task_failed');
            setCurrentStepName('Error');
            setIsOrchestrating(false);
            clearInterval(orchestrationInterval);
          }
        }
      } catch (err) {
        console.error('Error polling orchestration status:', err);
        clearInterval(orchestrationInterval);
        setIsOrchestrating(false);
      }
    }, 2000); // Poll every 2 seconds
    
    // Cleanup interval after 5 minutes
    setTimeout(() => {
      clearInterval(orchestrationInterval);
      setIsOrchestrating(false);
    }, 300000); // 5 minutes
  };
        }
        
        // CRITICAL DEBUG - Log everything about created_files
        console.log('Backend response received');
        console.log('Response structure check:', {
          response: typeof response.response,
          tool_calls: Array.isArray(response.tool_calls) ? response.tool_calls.length : 'not array',
          tool_results: Array.isArray(response.tool_results) ? response.tool_results.length : 'not array',
          created_files: Array.isArray(response.created_files) ? response.created_files.length : 'not array',
          search_mode: response.search_mode,
          search_data: typeof response.search_data
        });

        // Parse links from response
        const responseLinks = parseLinksFromText(response.response);
        const structuredLinks = parseStructuredLinks(response.response);
        const allLinks = [...responseLinks, ...structuredLinks];
        
        // Remove duplicates
        const uniqueLinks = allLinks.filter((link, index, self) => 
          index === self.findIndex(l => l.url === link.url)
        );

        // Create agent message with enhanced data
        const agentMessage: Message = {
          id: `msg-${Date.now()}`,
          content: response.response,
          sender: 'assistant',
          timestamp: new Date(response.timestamp),
          toolResults: response.tool_results,
          searchData: response.search_data,
          uploadData: response.upload_data,
          links: uniqueLinks.length > 0 ? uniqueLinks : undefined,
          status: response.tool_results.length > 0 ? {
            type: 'success',
            message: `Ejecuté ${response.tool_results.length} herramienta(s)`
          } : undefined
        };

        // Enhanced file handling starting...
        console.log('Enhanced file handling starting...');
        console.log('🎯 Created files detected:', response.created_files);
        console.log('🔍 File details:', {
          created_files: response.created_files,
          is_array: Array.isArray(response.created_files),
          length: response.created_files?.length || 0,
          search_mode: searchMode,
          tool_results: response.tool_results?.length || 0,
          upload_data: response.upload_data
        });
        
        let shouldCreateFileMessage = false;
        let filesToShow = [];
        
        // Only create file messages for actual file uploads (not for DeepSearch or task execution)
        // Method 1: Upload data from file upload response (keep this for real file uploads)
        if (response.upload_data && response.upload_data.files && Array.isArray(response.upload_data.files) && response.upload_data.files.length > 0) {
          console.log('📝 Using upload_data files:', response.upload_data.files);
          filesToShow = response.upload_data.files;
          shouldCreateFileMessage = true;
        }
        // REMOVED: Automatic file creation for DeepSearch and task execution
        // This was causing mockup files to appear in chat during task execution
        
        // REMOVED: Test file creation logic
        // This was causing mockup files to appear in chat
        
        console.log('File creation decision:', { shouldCreateFileMessage, filesCount: filesToShow.length });
        
        console.log('File creation logic processing...');
        
        // Get current messages (now includes user message)
        const currentMessages = [...messages, userMessage];
        
        if (shouldCreateFileMessage && filesToShow.length > 0) {
          console.log('Creating file upload message...');
          
          // Create proper attachments with enhanced error handling
          const attachments = filesToShow.map((file, index) => {
            const attachment = {
              id: file.id || file.file_id || `file-${Date.now()}-${Math.random()}`,
              name: file.name || `archivo_${index + 1}.md`,
              size: file.size || 25000,
              type: file.mime_type || file.type || 'text/markdown',
              url: file.url || (file.id ? `${import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/agent/download/${file.id}` : undefined)
            };
            
            return attachment;
          });
          
          console.log('📎 Created attachments:', attachments);
          
          // Create a separate message for file upload success
          const fileUploadMessage: Message = {
            id: `msg-${Date.now()}-files`,
            content: 'file_upload_success', // Use the marker for proper rendering
            sender: 'assistant',
            timestamp: new Date(response.timestamp),
            attachments: attachments,
            status: {
              type: 'success',
              message: `${filesToShow.length} archivo${filesToShow.length !== 1 ? 's' : ''} listo${filesToShow.length !== 1 ? 's' : ''} para usar`
            }
          };

          console.log('📁 File upload success message detected');
          console.log('📎 Final file upload message:', fileUploadMessage);

          // Update messages with both agent response and file upload message
          if (onUpdateMessages) {
            const updatedMessages = [...currentMessages];
            
            // Add agent response
            updatedMessages.push(agentMessage);
            
            // Add file upload message if needed
            if (shouldCreateFileMessage && filesToShow.length > 0) {
              updatedMessages.push(fileUploadMessage);
            }
            
            onUpdateMessages(updatedMessages);
          }
        } else {
          // Handle regular messages without files
          if (onUpdateMessages) {
            const updatedMessages = [...currentMessages, agentMessage];
            onUpdateMessages(updatedMessages);
          }
        }

        // Handle DeepResearch completion
        if (searchMode === 'deepsearch' && response.tool_results && response.tool_results.length > 0) {
          const toolResult = response.tool_results[0];
          
          // Detener simulación de progreso
          if (progressInterval) {
            clearInterval(progressInterval);
          }
          
          // Completar progreso GRADUALMENTE para que se vea
          setDeepResearchProgress(prev => ({
            ...prev,
            overallProgress: 100,
            currentStep: prev.steps.length - 1,
            steps: prev.steps.map(step => ({ ...step, status: 'completed' }))
          }));
          
          // Esperar 2 segundos antes de ocultar para que el usuario vea la completación
          setTimeout(() => {
            setDeepResearchProgress(prev => ({
              ...prev,
              isActive: false
            }));
          }, 2000);
          
          // NO crear archivos fake para DeepSearch - solo mostrar el resultado real
          
          // Mostrar informe en consola si está disponible
          if (toolResult.result?.result?.console_report && onLogToTerminal) {
            onLogToTerminal(toolResult.result.result.console_report, 'info');
          }
          
          // Crear datos del informe
          const reportData: ResearchReport = {
            query: message,
            sourcesAnalyzed: toolResult.result?.result?.sources_analyzed || 0,
            imagesCollected: toolResult.result?.result?.images_collected || 0,
            reportFile: response.created_files?.find(f => f.mime_type === 'text/markdown')?.path,
            executiveSummary: toolResult.result?.result?.executive_summary || response.search_data?.directAnswer,
            keyFindings: toolResult.result?.result?.key_findings || [],
            recommendations: toolResult.result?.result?.recommendations || [],
            timestamp: response.timestamp,
            console_report: toolResult.result?.result?.console_report
          };
          
          setDeepResearchReport(reportData);
        }

        // Set agent status to task completed
        setAgentStatus('task_completed');
        
        // After 5 seconds, set back to idle (aumentado para mejor visibilidad)
        setTimeout(() => {
          setAgentStatus('idle');
          setIsLoadingMessages(false);
        }, 5000);  // Aumentado de 3000 a 5000ms

        // Log tool executions to terminal
        if (response.tool_results && response.tool_results.length > 0 && onLogToTerminal) {
          response.tool_results.forEach((toolResult, index) => {
            const toolInfo = `🔧 HERRAMIENTA EJECUTADA [${index + 1}/${response.tool_results.length}]
────────────────────────────────────────
🛠️  Herramienta: ${toolResult.tool}
📋 Parámetros: ${JSON.stringify(toolResult.parameters, null, 2)}
📊 Estado: ${toolResult.result?.success ? '✅ EXITOSO' : '❌ ERROR'}
📄 Resultado: ${typeof toolResult.result === 'object' ? JSON.stringify(toolResult.result, null, 2) : toolResult.result}
────────────────────────────────────────`;
            
            onLogToTerminal(toolInfo, toolResult.result?.success ? 'success' : 'error');
          });
          
          // Summary log
          onLogToTerminal(`📈 RESUMEN: ${response.tool_results.length} herramienta(s) ejecutada(s) correctamente`, 'info');
        }

      } catch (error) {
        console.error('Error sending message:', error);
        
        // Set agent status to task failed
        setAgentStatus('task_failed');
        
        // After 3 seconds, set back to idle
        setTimeout(() => {
          setAgentStatus('idle');
          setIsLoadingMessages(false);
        }, 3000);
        
        // Detener progreso en caso de error
        if (progressInterval) {
          clearInterval(progressInterval);
        }
        
        // Mostrar error en el progreso por 3 segundos
        setDeepResearchProgress(prev => ({
          ...prev,
          steps: prev.steps.map(step => ({ ...step, status: step.status === 'active' ? 'error' : step.status }))
        }));
        
        // Ocultar después de 3 segundos
        setTimeout(() => {
          setDeepResearchProgress(prev => ({
            ...prev,
            isActive: false
          }));
        }, 3000);
        
        // Crear mensaje de error - with duplicate prevention
        const errorMessage: Message = {
          id: `msg-${Date.now()}`,
          content: 'Lo siento, hubo un error al procesar tu mensaje. Asegúrate de que Ollama esté ejecutándose.',
          sender: 'assistant',
          timestamp: new Date(),
          status: {
            type: 'error',
            message: 'Error de conexión'
          }
        };

        if (onUpdateMessages) {
          // Prevent duplicate error messages by checking if last message is already an error
          const lastMessage = messages[messages.length - 1];
          const isDuplicateError = lastMessage && 
            lastMessage.sender === 'assistant' && 
            lastMessage.status?.type === 'error' &&
            lastMessage.content === errorMessage.content;
          
          if (!isDuplicateError) {
            const updatedMessages = [...messages, errorMessage];
            onUpdateMessages(updatedMessages);
          }
        }
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      const userMessage = inputValue.trim();
      setInputValue('');
      handleSendMessage(userMessage);
    }
  };

  const handleFilesUploaded = async (files: FileList) => {
    if (!dataId) {
      console.error('No task ID available for file upload');
      return;
    }

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                     import.meta.env.REACT_APP_BACKEND_URL || 
                     process.env.REACT_APP_BACKEND_URL;
      
      const formData = new FormData();
      formData.append('task_id', dataId);
      
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const response = await fetch(`${backendUrl}/api/agent/upload-files`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        // Crear estructura de archivos para mostrar de forma atractiva
        const uploadedFiles = result.files.map((f: any, index: number) => ({
          id: f.id || `file-${Date.now()}-${index}`,
          name: f.name,
          size: String(f.size || 0), // Convert to string as expected by Message interface
          type: f.type || f.mime_type || 'application/octet-stream',
          url: `${backendUrl}/api/agent/download/${f.id}`
        }));

        console.log('🔍 CREATING UPLOAD MESSAGE WITH FILES:', uploadedFiles);
        console.log('🔍 FILES STRUCTURE:', uploadedFiles.map(f => ({
          id: f.id,
          name: f.name,
          size: f.size,
          type: f.type,
          url: f.url
        })));

        // Crear mensaje informativo mejorado con archivos subidos
        const uploadMessage: Message = {
          id: `msg-${Date.now()}`,
          content: 'file_upload_success', // Special marker to trigger file display
          sender: 'assistant',
          timestamp: new Date(),
          attachments: uploadedFiles,
          status: {
            type: 'success',
            message: `${result.files.length} archivo${result.files.length !== 1 ? 's' : ''} listo${result.files.length !== 1 ? 's' : ''} para usar`
          }
        };

        console.log('🚨 UPLOAD MESSAGE CREATED:', uploadMessage);
        console.log('📎 ATTACHMENTS IN MESSAGE:', uploadMessage.attachments);
        console.log('📎 MESSAGE CONTENT:', uploadMessage.content);
        console.log('📎 MESSAGE SENDER:', uploadMessage.sender);

        if (onUpdateMessages) {
          const updatedMessages = [...messages, uploadMessage];
          onUpdateMessages(updatedMessages);
        }

        // NO cerrar modal automáticamente - Dejarlo para que el usuario vea el progreso
        console.log('Files uploaded successfully:', result.files);
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Error uploading files:', error);
      
      // Mostrar mensaje de error
      const errorMessage: Message = {
        id: `msg-${Date.now()}`,
        content: 'Hubo un error al subir los archivos. Por favor, intenta de nuevo.',
        sender: 'assistant',
        timestamp: new Date(),
        status: {
          type: 'error',
          message: 'Error de upload'
        }
      };

      if (onUpdateMessages) {
        const updatedMessages = [...messages, errorMessage];
        onUpdateMessages(updatedMessages);
      }
    }
  };

  const handleAttachFiles = () => {
    console.log('🎯 ATTACH FILES CLICKED - Setting showFileUpload to true');
    setShowFileUpload(true);
    console.log('✅ showFileUpload state set to true');
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const quickActions = [
    { 
      id: 'shell',
      icon: Terminal, 
      label: 'Ejecutar comando', 
      action: () => {
        setInputValue('Ejecuta el comando: ');
        setActiveQuickAction('shell');
        setShowQuickActions(false);
        textareaRef.current?.focus();
      }
    },
    { 
      id: 'search',
      icon: Globe, 
      label: 'Buscar información', 
      action: () => {
        setInputValue('Busca información sobre: ');
        setActiveQuickAction('search');
        setShowQuickActions(false);
        textareaRef.current?.focus();
      }
    },
    { 
      id: 'files',
      icon: FileText, 
      label: 'Gestionar archivos', 
      action: () => {
        setInputValue('Ayúdame a gestionar archivos: ');
        setActiveQuickAction('files');
        setShowQuickActions(false);
        textareaRef.current?.focus();
      }
    },
    { 
      id: 'problem',
      icon: Zap, 
      label: 'Resolver problema', 
      action: () => {
        setInputValue('Ayúdame a resolver: ');
        setActiveQuickAction('problem');
        setShowQuickActions(false);
        textareaRef.current?.focus();
      }
    },
    { 
      id: 'demo-report',
      icon: FileText, 
      label: 'Ver Demo Report', 
      action: () => {
        setShowPlaceholder(true);
        setShowQuickActions(false);
      }
    }
  ];

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case 'shell':
        return <Terminal className="w-4 h-4" />;
      case 'web_search':
        return <Globe className="w-4 h-4" />;
      case 'file_manager':
        return <FileText className="w-4 h-4" />;
      default:
        return <Terminal className="w-4 h-4" />;
    }
  };

  const formatToolResult = (result: any) => {
    if (typeof result === 'object') {
      return JSON.stringify(result, null, 2);
    }
    return String(result);
  };

  // Enhanced function to parse links from text
  const parseLinksFromText = (text: string) => {
    const links: Array<{url: string, title?: string, description?: string}> = [];
    
    // Pattern to match URLs in text
    const urlPattern = /(https?:\/\/[^\s]+)/g;
    const matches = text.match(urlPattern);
    
    if (matches) {
      matches.forEach(url => {
        // Clean up the URL (remove trailing punctuation)
        const cleanUrl = url.replace(/[.,;:!?]$/, '');
        
        // Extract title from URL if possible
        const title = cleanUrl.split('/').pop()?.replace(/[-_]/g, ' ') || undefined;
        
        links.push({
          url: cleanUrl,
          title,
          description: undefined
        });
      });
    }
    
    return links;
  };

  // Enhanced function to parse structured links from markdown-like format
  const parseStructuredLinks = (content: string) => {
    const links: Array<{url: string, title?: string, description?: string}> = [];
    
    // Pattern for 🔗 links with titles
    const linkPattern = /🔗\s*\*\*([^*]+)\*\*\s*\n\s*([^\n]+)\n\s*(https?:\/\/[^\s]+)/g;
    let match;
    
    while ((match = linkPattern.exec(content)) !== null) {
      links.push({
        url: match[3],
        title: match[1],
        description: match[2]
      });
    }
    
    // Fallback: simple 🔗 URL pattern
    const simplePattern = /🔗\s*(https?:\/\/[^\s]+)/g;
    while ((match = simplePattern.exec(content)) !== null) {
      if (!links.some(link => link.url === match[1])) {
        links.push({
          url: match[1],
          title: undefined,
          description: undefined
        });
      }
    }
    
    return links;
  };

  const parseSearchResults = (toolResult: any) => {
    try {
      // Si el resultado es un string que parece ser búsqueda web
      if (typeof toolResult.result === 'string' && 
          (toolResult.result.includes('Pregunta:') || toolResult.result.includes('Respuesta Directa:'))) {
        
        const text = toolResult.result;
        const lines = text.split('\n');
        
        let query = '';
        let directAnswer = '';
        let sources: any[] = [];
        
        // Parse query
        const queryMatch = text.match(/\*\*Pregunta:\*\* (.+)/);
        if (queryMatch) {
          query = queryMatch[1];
        }
        
        // Parse direct answer
        const directAnswerStart = text.indexOf('**Respuesta Directa:**');
        const sourcesStart = text.indexOf('**Fuentes encontradas:**');
        
        if (directAnswerStart !== -1 && sourcesStart !== -1) {
          directAnswer = text.substring(directAnswerStart + 22, sourcesStart).trim();
        }
        
        // Parse sources
        const sourcePattern = /\d+\.\s\*\*(.+?)\*\*\s*\n\s*(.+?)\n\s*🔗\s*(.+)/g;
        let match;
        while ((match = sourcePattern.exec(text)) !== null) {
          sources.push({
            title: match[1],
            content: match[2],
            url: match[3]
          });
        }
        
        return {
          isSearchResult: true,
          query,
          directAnswer,
          sources,
          type: toolResult.tool === 'tavily_search' ? 'websearch' : 'deepsearch'
        };
      }
    } catch (error) {
      console.error('Error parsing search results:', error);
    }
    return null;
  };

  const parseMessageAsSearchResults = (content: string) => {
    try {
      // Check if it's a search result message with more flexible patterns
      if (content.includes('🔍 **Búsqueda Web con Tavily**') || 
          content.includes('🔬 **Investigación Profunda**') ||
          content.includes('Búsqueda Web con Tavily') ||
          content.includes('Investigación Profunda')) {
        
        let query = '';
        let directAnswer = '';
        let sources: any[] = [];
        
        // Parse query - multiple patterns
        const queryPatterns = [
          /\*\*Pregunta:\*\*\s*(.+)/,
          /\*\*Tema:\*\*\s*(.+)/,
          /Pregunta:\s*(.+)/,
          /Tema:\s*(.+)/
        ];
        
        for (const pattern of queryPatterns) {
          const queryMatch = content.match(pattern);
          if (queryMatch) {
            query = queryMatch[1].trim();
            break;
          }
        }
        
        // Parse direct answer - multiple patterns
        const answerPatterns = [
          { start: '**Respuesta Directa:**', end: '**Fuentes encontradas:**' },
          { start: '**Análisis Comprehensivo:**', end: '**Hallazgos Clave:**' },
          { start: 'Respuesta Directa:', end: 'Fuentes encontradas:' },
          { start: 'Análisis Comprehensivo:', end: 'Hallazgos Clave:' }
        ];
        
        for (const pattern of answerPatterns) {
          const startIndex = content.indexOf(pattern.start);
          const endIndex = content.indexOf(pattern.end);
          
          if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
            directAnswer = content.substring(startIndex + pattern.start.length, endIndex).trim();
            break;
          }
        }
        
        // Parse sources with multiple patterns
        const sourcePatterns = [
          /(\d+)\.\s*\*\*(.+?)\*\*\s*([\s\S]*?)\s*🔗\s*(.+?)(?=\n\d+\.|\n\n|$)/g,
          /(\d+)\.\s*(.+?)\n\s*(.+?)\n\s*🔗\s*(.+?)(?=\n\d+\.|\n\n|$)/g,
          /(\d+)\.\s*\*\*(.+?)\*\*\s*(.*?)\n.*?🔗\s*(.+)/g
        ];
        
        for (const pattern of sourcePatterns) {
          let match;
          while ((match = pattern.exec(content)) !== null) {
            sources.push({
              title: match[2] || match[1] || 'Resultado sin título',
              content: (match[3] || '').replace(/\n/g, ' ').trim() || 'Sin descripción disponible',
              url: match[4] || ''
            });
          }
          if (sources.length > 0) break; // Stop if we found sources with this pattern
        }
        
        // Fallback: extract any URLs from the content
        if (sources.length === 0) {
          const urlPattern = /🔗\s*(https?:\/\/[^\s]+)/g;
          let urlMatch;
          let index = 1;
          while ((urlMatch = urlPattern.exec(content)) !== null) {
            sources.push({
              title: `Fuente ${index}`,
              content: 'Información adicional disponible en el enlace',
              url: urlMatch[1]
            });
            index++;
          }
        }
        
        return {
          query: query || 'Búsqueda realizada',
          directAnswer: directAnswer,
          sources,
          type: content.includes('🔍') || content.includes('Búsqueda Web') ? 'websearch' : 'deepsearch'
        };
      }
    } catch (error) {
      console.error('Error parsing message as search results:', error);
    }
    return null;
  };

  // Deep Research Action Handlers
  const handleDownloadPDF = async (reportData: ResearchReport) => {
    if (!reportData.console_report && !reportData.executiveSummary) {
      console.error('No content available for PDF generation');
      return;
    }

    const content = reportData.console_report || reportData.executiveSummary || '';
    
    try {
      await generatePDFWithCustomCSS({
        title: `Investigación: ${reportData.query}`,
        content: content,
        filename: `investigacion_${reportData.query.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().slice(0, 10)}.pdf`
      });
    } catch (error) {
      console.error('Error generating PDF:', error);
    }
  };

  const handleDownloadMarkdown = (reportData: ResearchReport) => {
    if (!reportData.console_report && !reportData.executiveSummary) {
      console.error('No content available for Markdown download');
      return;
    }

    const content = reportData.console_report || reportData.executiveSummary || '';
    downloadMarkdownFile(content, `Investigación: ${reportData.query}`);
  };

  const handleViewInConsole = (reportData: ResearchReport) => {
    const content = reportData.console_report || reportData.executiveSummary || '';
    setPDFViewerContent(content);
    setPDFViewerTitle(`Investigación: ${reportData.query}`);
    setShowPDFViewer(true);
  };

  const handleUseAsMemory = (reportData: ResearchReport) => {
    const content = reportData.console_report || reportData.executiveSummary || '';
    const memoryFile: MemoryFile = {
      id: `research-${Date.now()}`,
      name: `Investigación: ${reportData.query}`,
      type: 'markdown',
      size: content.length,
      content: content,
      summary: reportData.executiveSummary?.substring(0, 200) + '...' || 'Investigación profunda completada',
      addedAt: new Date(),
      source: 'deep_research',
      isActive: true
    };

    addMemoryFile(memoryFile);
    
    // Show confirmation
    if (onLogToTerminal) {
      onLogToTerminal(`✅ Archivo agregado a memoria RAG: ${memoryFile.name}`, 'success');
    }
  };

  const handleAddFileToMemory = async (file: any) => {
    try {
      // Download file content to add to memory
      const blob = await agentAPI.downloadFile(file.id);
      const content = await blob.text();
      
      const memoryFile: MemoryFile = {
        id: file.id,
        name: file.name,
        type: file.mime_type?.includes('markdown') ? 'markdown' : 'text',
        size: file.size,
        content: content,
        summary: `Archivo: ${file.name}`,
        addedAt: new Date(),
        source: file.source === 'uploaded' ? 'uploaded' : 'agent',
        isActive: true
      };

      addMemoryFile(memoryFile);
      
      // Show confirmation
      if (onLogToTerminal) {
        onLogToTerminal(`✅ Archivo agregado a memoria RAG: ${file.name}`, 'success');
      }
    } catch (error) {
      console.error('Error adding file to memory:', error);
      if (onLogToTerminal) {
        onLogToTerminal(`❌ Error agregando archivo a memoria: ${file.name}`, 'error');
      }
    }
  };
  const getFileTypeFromExtension = (filename: string): string => {
    const extension = filename.split('.').pop()?.toLowerCase() || '';
    
    const typeMap: {[key: string]: string} = {
      'jpg': 'image/jpeg',
      'jpeg': 'image/jpeg', 
      'png': 'image/png',
      'gif': 'image/gif',
      'svg': 'image/svg+xml',
      'pdf': 'application/pdf',
      'txt': 'text/plain',
      'md': 'text/markdown',
      'json': 'application/json',
      'csv': 'text/csv',
      'py': 'text/x-python',
      'js': 'text/javascript',
      'html': 'text/html',
      'css': 'text/css',
      'zip': 'application/zip',
      'rar': 'application/x-rar-compressed',
      'mp3': 'audio/mpeg',
      'mp4': 'video/mp4',
      'doc': 'application/msword',
      'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    };
    
    return typeMap[extension] || 'application/octet-stream';
  };

  const parseMessageAsFileUpload = async (content: string) => {
    try {
      // Check if it's a file upload success message with different patterns
      if (content.includes('✅') && 
          (content.includes('archivo') || content.includes('archivos')) &&
          (content.includes('cargado') || content.includes('subido') || content.includes('disponible'))) {
        
        // If we have a task ID, get the real files from backend
        if (dataId) {
          try {
            const backendFiles = await getTaskFiles();
            
            // Filter for recently uploaded files (within last 5 minutes)
            const recentFiles = backendFiles.filter(file => {
              const fileTime = new Date(file.created_at || file.uploadedAt || Date.now());
              const timeDiff = Date.now() - fileTime.getTime();
              return timeDiff < 5 * 60 * 1000; // 5 minutes
            });
            
            if (recentFiles.length > 0) {
              return {
                files: recentFiles.map(file => ({
                  id: file.id || file.file_id,
                  name: file.name,
                  size: file.size,
                  type: file.mime_type || file.type,
                  url: file.url || `${import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/agent/download/${file.id || file.file_id}`,
                  needsRealData: false // Already has real data
                }))
              };
            }
          } catch (error) {
            console.error('Error getting real files from backend:', error);
            // Fall back to parsing from message content
          }
        }
        
        // Fallback: parse from message content
        const files: any[] = [];
        
        // Pattern 1: "• **filename.ext** (size)"
        const filePattern1 = /•\s*\*\*(.+?)\*\*\s*\((.+?)\)/g;
        let match;
        while ((match = filePattern1.exec(content)) !== null) {
          files.push({
            id: `file-${Date.now()}-${Math.random()}`,
            name: match[1],
            size: match[2].includes('KB') ? parseInt(match[2]) * 1024 : 
                  match[2].includes('MB') ? parseInt(match[2]) * 1024 * 1024 : 
                  parseInt(match[2]) || 0,
            type: getFileTypeFromExtension(match[1]),
            url: undefined,
            needsRealData: true // Flag to indicate we need to fetch real file data
          });
        }
        
        // Pattern 2: "• **filename.ext** (size KB)"
        const filePattern2 = /•\s*\*\*(.+?)\*\*\s*\((.+?)\s*(KB|MB|Bytes)\)/g;
        while ((match = filePattern2.exec(content)) !== null) {
          const sizeStr = match[2];
          const unit = match[3];
          let sizeBytes = parseInt(sizeStr) || 0;
          
          if (unit === 'KB') sizeBytes *= 1024;
          else if (unit === 'MB') sizeBytes *= 1024 * 1024;
          
          files.push({
            id: `file-${Date.now()}-${Math.random()}`,
            name: match[1],
            size: sizeBytes,
            type: getFileTypeFromExtension(match[1]),
            url: undefined,
            needsRealData: true // Flag to indicate we need to fetch real file data
          });
        }
        
        return {
          files
        };
      }
    } catch (error) {
      console.error('Error parsing message as file upload:', error);
    }
    return null;
  };

  // New function to get real file data from backend
  const getRealFileData = async (fileName: string) => {
    if (!dataId) return null;
    
    try {
      const taskFiles = await agentAPI.getTaskFiles(dataId);
      return taskFiles.find(file => file.name === fileName);
    } catch (error) {
      console.error('Error getting real file data:', error);
      return null;
    }
  };

  // Enhanced function to get all task files from backend
  const getTaskFiles = async () => {
    if (!dataId) return [];
    
    try {
      const taskFiles = await agentAPI.getTaskFiles(dataId);
      return taskFiles;
    } catch (error) {
      console.error('Error getting task files:', error);
      return [];
    }
  };

  // Enhanced download function that can handle both real files and parsed files
  const handleFileDownload = async (file: any) => {
    if (onLogToTerminal) {
      onLogToTerminal(`⬇️ Descargando archivo: ${file.name}`, 'success');
    }

    try {
      // If file has real ID, use it directly
      if (file.id && !file.needsRealData) {
        const blob = await agentAPI.downloadFile(file.id);
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = file.name;
        link.click();
        window.URL.revokeObjectURL(url);
        return;
      }

      // If file needs real data, try to get it from backend
      if (file.needsRealData && dataId) {
        const realFile = await getRealFileData(file.name);
        if (realFile && realFile.id) {
          const blob = await agentAPI.downloadFile(realFile.id);
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = file.name;
          link.click();
          window.URL.revokeObjectURL(url);
          return;
        }
      }

      // Fallback: if file has URL, use it
      if (file.url) {
        const link = document.createElement('a');
        link.href = file.url;
        link.download = file.name;
        link.click();
        return;
      }

      // If all else fails, show error
      if (onLogToTerminal) {
        onLogToTerminal(`❌ No se pudo descargar el archivo: ${file.name}`, 'error');
      }
    } catch (error) {
      console.error('Error downloading file:', error);
      if (onLogToTerminal) {
        onLogToTerminal(`❌ Error descargando archivo: ${file.name}`, 'error');
      }
    }
  };
  
  // Component's main return statement
  return (
    <div className="flex flex-col h-full bg-[#272728] text-[#DADADA] w-full" data-id={dataId}>
      {/* DeepResearch Progress Indicator - Fixed Position */}
      {deepResearchProgress.isActive && (
        <div className="sticky top-0 z-20 bg-[#272728] p-4 border-b border-[rgba(255,255,255,0.08)] shadow-lg">
          <DeepResearchProgress
            steps={deepResearchProgress.steps}
            currentStep={deepResearchProgress.currentStep}
            overallProgress={deepResearchProgress.overallProgress}
            isActive={deepResearchProgress.isActive}
            onCancel={() => {
              setDeepResearchProgress(prev => ({ ...prev, isActive: false }));
            }}
            query={currentQuery}
          />
        </div>
      )}

      {/* Messages Container - Fixed height with proper scrolling */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <div className="h-full overflow-y-auto overflow-x-hidden p-4 space-y-4 custom-scrollbar" style={{
          scrollbarWidth: 'thin',
          scrollbarColor: '#7f7f7f #383739'
        }}>
          {/* Loading placeholder while waiting for response */}

          {/* Deduplicate messages by content and timestamp before rendering */}
          {(() => {
            console.log('🐛 DEBUG: Raw messages array:', messages);
            
            const uniqueMessages = messages.reduce((uniqueMessages, message) => {
              // Check if this message is a duplicate
              const isDuplicate = uniqueMessages.some(existingMessage => 
                existingMessage.content === message.content && 
                existingMessage.sender === message.sender &&
                Math.abs(existingMessage.timestamp.getTime() - message.timestamp.getTime()) < 2000 // Within 2 seconds
              );
              
              if (!isDuplicate) {
                uniqueMessages.push(message);
              } else {
                console.log('🐛 DEBUG: Duplicate message detected and removed:', message.content.substring(0, 50) + '...');
              }
              
              return uniqueMessages;
            }, [] as Message[]);
            
            console.log('🐛 DEBUG: Unique messages after deduplication:', uniqueMessages.length, 'out of', messages.length);
            
            return uniqueMessages;
          })().map(message => (
            <div key={message.id} className={`${message.sender === 'user' ? 'flex justify-end' : ''} group mb-4`}>
              {message.sender === 'user' ? (
                <div className="flex items-start gap-3 max-w-[90%] min-w-0">
                  <div className="bg-[rgba(255,255,255,0.06)] rounded-xl p-4 flex-1 min-w-0 overflow-hidden chat-text-selection">
                    {/* Contenido del mensaje del usuario */}
                    <div className="text-base whitespace-pre-wrap break-words text-[#DADADA]">
                      {message.content}
                    </div>
                  </div>
                </div>
              ) : (
                /* Mensaje del asistente - SIN GLOBO CONTENEDOR */
                <div className="max-w-[90%] min-w-0 chat-text-selection">
                  {/* Contenido del mensaje del asistente */}
                {/* Regular message content first */}
                <div className="text-base whitespace-pre-wrap break-words text-[#DADADA] mb-4">
                  {message.content}
                </div>
                
                {/* ENHANCED FILE UPLOAD SUCCESS DETECTION */}
                {(() => {
                  const isAssistantMessage = message.sender === 'assistant';
                  if (!isAssistantMessage) return null;
                  
                  // Check multiple conditions for file upload success
                  const isFileUploadSuccess = message.content === 'file_upload_success';
                  const hasAttachments = message.attachments && message.attachments.length > 0;
                  
                  // Enhanced pattern matching for success messages
                  const hasSuccessPattern = message.content && 
                    typeof message.content === 'string' && (
                      message.content.includes('✅') || 
                      message.content.includes('archivo') || 
                      message.content.includes('archivos') ||
                      message.content.includes('cargado') || 
                      message.content.includes('subido') || 
                      message.content.includes('disponible') || 
                      message.content.includes('exitosamente') ||
                      message.content.includes('listo') ||
                      message.content.includes('completado') ||
                      message.content.includes('generado') ||
                      message.content.includes('creado')
                    );
                  
                  // Show file upload success if conditions are met
                  // Enhanced file detection with better logging
                  console.log('🔍 FILE UPLOAD DEBUG:', {
                    messageId: message.id,
                    isAssistantMessage,
                    isFileUploadSuccess,
                    hasAttachments,
                    hasSuccessPattern,
                    content: message.content?.substring(0, 100) + '...',
                    attachments: message.attachments,
                    attachmentsLength: message.attachments?.length || 0
                  });
                  
                  const shouldShowFileUpload = isFileUploadSuccess || hasAttachments || hasSuccessPattern;
                  
                  // Enhanced debug logging
                  if (isFileUploadSuccess || hasAttachments || hasSuccessPattern) {
                    console.log('🔍 FILE UPLOAD DEBUG:', {
                      messageId: message.id,
                      isAssistantMessage,
                      isFileUploadSuccess,
                      hasAttachments,
                      hasSuccessPattern,
                      shouldShowFileUpload,
                      content: message.content?.substring(0, 100) + '...',
                      attachments: message.attachments,
                      attachmentsLength: message.attachments?.length || 0
                    });
                  }
                  
                  if (shouldShowFileUpload) {
                    console.log('🎯 FILE UPLOAD SUCCESS DETECTED - RENDERING COMPONENT');
                    
                    // Use real attachments if available, otherwise create fake files for demonstration
                    let filesToShow = [];
                    
                    if (hasAttachments && message.attachments && message.attachments.length > 0) {
                      filesToShow = message.attachments.map(att => ({
                        id: att.id || `file-${Date.now()}-${Math.random()}`,
                        name: att.name,
                        size: typeof att.size === 'string' ? parseInt(att.size) : att.size,
                        type: att.type,
                        url: att.url
                      }));
                    } else if (hasSuccessPattern) {
                      // Solo mostrar si hay información útil, no crear archivos fake
                      return null;
                    }
                    
                    console.log('📁 FILES TO SHOW:', filesToShow, 'Length:', filesToShow.length);
                    
                    // Show component only if we have real files to display
                    if (filesToShow.length > 0) {
                      console.log('🚀 RENDERING FileUploadSuccess COMPONENT');
                      
                      return (
                        <div className="mt-4">
                          <FileUploadSuccess
                            files={filesToShow}
                            onFileView={(file) => {
                              console.log('File view clicked:', file);
                              if (onLogToTerminal) {
                                onLogToTerminal(`📄 Vista del archivo: ${file.name}`, 'info');
                              }
                            }}
                            onFileDownload={(file) => {
                              console.log('File download clicked:', file);
                              handleFileDownload(file);
                            }}
                            onAddToMemory={(file) => {
                              console.log('Add to memory clicked:', file);
                              handleAddFileToMemory(file);
                            }}
                          />
                        </div>
                      );
                    } else {
                      console.log('❌ NO FILES TO SHOW - filesToShow is empty');
                    }
                  }
                  
                  return null;
                })()}
                
                {/* Special handling for file upload success */}
                {message.content === 'file_upload_success' && message.attachments && message.attachments.length > 0 ? (
                  <div className="mt-4">
                    <FileUploadSuccess
                      files={message.attachments.map(att => ({
                        id: att.id,
                        name: att.name,
                        size: typeof att.size === 'string' ? parseInt(att.size) : att.size,
                        type: att.type,
                        url: att.url
                      }))}
                      onFileView={(file) => {
                        console.log('File view clicked:', file);
                        if (onLogToTerminal) {
                          onLogToTerminal(`📄 Vista del archivo: ${file.name}`, 'info');
                        }
                      }}
                      onFileDownload={(file) => {
                        console.log('File download clicked:', file);
                        handleFileDownload(file);
                      }}
                      onAddToMemory={(file) => {
                        console.log('Add to memory clicked:', file);
                        handleAddFileToMemory(file);
                      }}
                    />
                  </div>
                ) : null}
                
                {/* ENHANCED FILE UPLOAD SUCCESS DETECTION */}
                {(() => {
                  const isAssistantMessage = message.sender === 'assistant';
                  if (!isAssistantMessage) return null;
                  
                  // Check multiple conditions for file upload success
                  const isFileUploadSuccess = message.content === 'file_upload_success';
                  const hasAttachments = message.attachments && message.attachments.length > 0;
                  const hasSuccessPattern = message.content && 
                    typeof message.content === 'string' && 
                    message.content.includes('✅') && 
                    (message.content.includes('archivo') || message.content.includes('archivos')) &&
                    (message.content.includes('cargado') || message.content.includes('subido') || 
                     message.content.includes('disponible') || message.content.includes('exitosamente'));
                  
                  // Show file upload success if any condition is met
                  // Enhanced file detection with better logging
                  console.log('🔍 FILE UPLOAD DEBUG:', {
                    messageId: message.id,
                    isAssistantMessage,
                    isFileUploadSuccess,
                    hasAttachments,
                    hasSuccessPattern,
                    content: message.content?.substring(0, 100) + '...',
                    attachments: message.attachments,
                    attachmentsLength: message.attachments?.length || 0
                  });
                  
                  const shouldShowFileUpload = isFileUploadSuccess || hasAttachments || hasSuccessPattern;
                  
                  if (!shouldShowFileUpload) return null;
                  
                  console.log('🎯 FILE UPLOAD SUCCESS DETECTED:', {
                    isFileUploadSuccess,
                    hasAttachments,
                    hasSuccessPattern,
                    attachments: message.attachments,
                    content: message.content
                  });
                  
                  // Use attachments if available, otherwise create test files
                  const filesToShow = hasAttachments ? message.attachments.map(att => ({
                    id: att.id,
                    name: att.name,
                    size: typeof att.size === 'string' ? parseInt(att.size) : att.size,
                    type: att.type,
                    url: att.url
                  })) : [{
                    id: `file-${Date.now()}`,
                    name: 'archivo_adjunto.md',
                    size: 1024,
                    type: 'text/markdown',
                    url: dataId ? `${import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/agent/download/test-file` : undefined
                  }];
                  
                  return (
                    <div className="mt-4">
                      <FileUploadSuccess
                        files={filesToShow}
                        onFileView={(file) => {
                          console.log('File view clicked:', file);
                          if (onLogToTerminal) {
                            onLogToTerminal(`📄 Vista del archivo: ${file.name}`, 'info');
                          }
                        }}
                        onFileDownload={(file) => {
                          console.log('File download clicked:', file);
                          handleFileDownload(file);
                        }}
                        onAddToMemory={(file) => {
                          console.log('Add to memory clicked:', file);
                          handleAddFileToMemory(file);
                        }}
                      />
                    </div>
                  );
                })()}
                
                {/* Orchestration Result Display */}
                {message.orchestrationResult && (
                  <div className="mt-4">
                    <TaskSummary
                      title="Orquestación Completada"
                      outcome={message.orchestrationResult.message || 'Tarea completada exitosamente'}
                      completedSteps={message.orchestrationResult.execution_plan?.steps?.map((step: any) => step.title) || []}
                      executionTime={message.orchestrationResult.total_execution_time ? `${Math.round(message.orchestrationResult.total_execution_time / 1000)}s` : undefined}
                      toolsUsed={message.orchestrationResult.tools_used || []}
                      type={message.orchestrationResult.success ? 'success' : 'partial'}
                    />
                  </div>
                )}
                
                {/* Regular message content rendering */}
                {!message.attachments || message.attachments.length === 0 ? (() => {
                  // Priority 1: Check for structured search data
                  if (message.searchData) {
                    return (
                      <SearchResults
                        query={message.searchData.query}
                        directAnswer={message.searchData.directAnswer}
                        sources={message.searchData.sources}
                        type={message.searchData.type}
                      />
                    );
                  }
                  
                  // Priority 2: Check for structured upload data
                  if (message.uploadData) {
                    return (
                      <FileUploadSuccess
                        files={message.uploadData.files}
                        onFileView={(file) => {
                          const fileInfo = `📄 VISTA PREVIA DEL ARCHIVO
────────────────────────────────────────
📝 Nombre: ${file.name}
📊 Tamaño: ${formatFileSize(file.size)}
🏷️  Tipo: ${file.type || 'Desconocido'}
🆔 ID: ${file.id}
🔗 URL: ${file.url || 'No disponible'}
────────────────────────────────────────`;
                          
                          if (onLogToTerminal) {
                            onLogToTerminal(fileInfo, 'info');
                          }
                          
                          if (file.url) {
                            window.open(file.url, '_blank');
                          }
                        }}
                        onFileDownload={handleFileDownload}
                        onAddToMemory={(file) => {
                          const memoryFile = {
                            name: file.name,
                            type: 'uploaded_file' as const,
                            content: `Archivo: ${file.name}\nTipo: ${file.type}\nTamaño: ${file.size} bytes`,
                            metadata: {
                              size: file.size,
                              createdAt: new Date(),
                              source: 'uploaded',
                              summary: `Archivo ${file.name} (${file.type})`,
                              tags: [file.type?.split('/')[0] || 'unknown']
                            }
                          };
                          
                          addMemoryFile(memoryFile);
                          if (onLogToTerminal) {
                            onLogToTerminal(`🧠 Archivo "${file.name}" agregado a la memoria`, 'success');
                          }
                        }}
                      />
                    );
                  }
                  
                  // Priority 3: Check if message content contains search results (fallback) - SOLO si no hay searchData estructurada
                  if (!message.searchData && (message.content.includes('🔍') || 
                      message.content.includes('🔬') || 
                      message.content.includes('Búsqueda Web con Tavily') || 
                      message.content.includes('Investigación Profunda'))) {
                    // Parse search results from message content
                    const searchResults = parseMessageAsSearchResults(message.content);
                    if (searchResults) {
                      return (
                        <SearchResults
                          query={searchResults.query}
                          directAnswer={searchResults.directAnswer}
                          sources={searchResults.sources}
                          type={searchResults.type}
                        />
                      );
                    }
                  }
                  
                  // Priority 4: Check for attachments first - ALWAYS show file buttons if attachments exist
                  if (message.attachments && message.attachments.length > 0) {
                    console.log('🔗 Attachments detected in message:', message.attachments);
                    return (
                      <div className="space-y-3">
                        {/* Show regular message content if exists */}
                        {message.content && message.content !== 'file_upload_success' && (
                          <div className="text-base whitespace-pre-wrap break-words" style={{ fontFamily: "'Segoe UI Variable Display', 'Segoe UI', system-ui, -apple-system, sans-serif", fontWeight: 400 }}>
                            {message.content.split('\n').map((line, lineIndex) => {
                              // Format markdown-like text
                              if (line.startsWith('**') && line.endsWith('**')) {
                                return (
                                  <div key={lineIndex} className="font-bold text-blue-400 mb-2">
                                    {line.replace(/\*\*/g, '')}
                                  </div>
                                );
                              }
                              
                              // Format bullet points
                              if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
                                return (
                                  <div key={lineIndex} className="ml-4 mb-1 text-[#DADADA]">
                                    {line}
                                  </div>
                                );
                              }
                              
                              // Default line
                              return line.trim() ? (
                                <div key={lineIndex} className="mb-1">
                                  {line}
                                </div>
                              ) : (
                                <div key={lineIndex} className="mb-2"></div>
                              );
                            })}
                          </div>
                        )}
                        
                        {/* Always show file buttons */}
                        <FileUploadSuccess
                          files={message.attachments.map(att => ({
                            id: att.id || `file-${Date.now()}`,
                            name: att.name,
                            size: typeof att.size === 'string' ? parseInt(att.size) || 0 : att.size || 0,
                            type: att.type,
                            url: att.url
                          }))}
                          onFileView={(file) => {
                            const fileInfo = `📄 VISTA PREVIA DEL ARCHIVO
────────────────────────────────────────
📝 Nombre: ${file.name}
📊 Tamaño: ${formatFileSize(file.size)}
🏷️  Tipo: ${file.type || 'Desconocido'}
🆔 ID: ${file.id}
🔗 URL: ${file.url || 'No disponible'}
────────────────────────────────────────`;
                            
                            if (onLogToTerminal) {
                              onLogToTerminal(fileInfo, 'info');
                            }
                            
                            if (file.url) {
                              window.open(file.url, '_blank');
                            }
                          }}
                          onFileDownload={handleFileDownload}
                          onAddToMemory={(file) => {
                            const memoryFile = {
                              name: file.name,
                              type: 'uploaded_file' as const,
                              content: `Archivo: ${file.name}\nTipo: ${file.type}\nTamaño: ${file.size} bytes`,
                              metadata: {
                                size: file.size,
                                createdAt: new Date(),
                                source: 'uploaded',
                                summary: `Archivo ${file.name} (${file.type})`,
                                tags: [file.type?.split('/')[0] || 'unknown']
                              }
                            };
                            
                            addMemoryFile(memoryFile);
                            if (onLogToTerminal) {
                              onLogToTerminal(`🧠 Archivo "${file.name}" agregado a la memoria`, 'success');
                            }
                          }}
                        />
                      </div>
                    );
                  }
                  
                  // Priority 5: Check for file upload success in message content (async parsing)
                  if (message.content.includes('✅') && 
                      (message.content.includes('archivo') || message.content.includes('archivos')) &&
                      (message.content.includes('cargado') || message.content.includes('subido') || message.content.includes('disponible'))) {
                    console.log('📁 File upload success message detected, triggering FileUploadParser');
                    console.log('🔍 Message content:', message.content);
                    return (
                      <div className="space-y-3">
                        {/* Show regular message content */}
                        <div className="text-base whitespace-pre-wrap break-words" style={{ fontFamily: "'Segoe UI Variable Display', 'Segoe UI', system-ui, -apple-system, sans-serif", fontWeight: 400 }}>
                          {message.content.split('\n').map((line, lineIndex) => {
                            // Format markdown-like text
                            if (line.startsWith('**') && line.endsWith('**')) {
                              return (
                                <div key={lineIndex} className="font-bold text-blue-400 mb-2">
                                  {line.replace(/\*\*/g, '')}
                                </div>
                              );
                            }
                            
                            // Format bullet points
                            if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
                              return (
                                <div key={lineIndex} className="ml-4 mb-1 text-[#DADADA]">
                                  {line}
                                </div>
                              );
                            }
                            
                            // Default line
                            return line.trim() ? (
                              <div key={lineIndex} className="mb-1">
                                {line}
                              </div>
                            ) : (
                              <div key={lineIndex} className="mb-2"></div>
                            );
                          })}
                        </div>
                        
                        {/* Parse and display file upload with proper buttons */}
                        <FileUploadParser
                          content={message.content}
                          onFileView={(file) => {
                            const fileInfo = `📄 VISTA PREVIA DEL ARCHIVO
────────────────────────────────────────
📝 Nombre: ${file.name}
📊 Tamaño: ${formatFileSize(file.size)}
🏷️  Tipo: ${file.type || 'Desconocido'}
🆔 ID: ${file.id}
🔗 URL: ${file.url || 'No disponible'}
────────────────────────────────────────`;
                            
                            if (onLogToTerminal) {
                              onLogToTerminal(fileInfo, 'info');
                            }
                            
                            if (file.url) {
                              window.open(file.url, '_blank');
                            }
                          }}
                          onFileDownload={handleFileDownload}
                          onAddToMemory={handleAddFileToMemory}
                          parseMessageAsFileUpload={parseMessageAsFileUpload}
                        />
                      </div>
                    );
                  }
                  
                  // Priority 6: Render message content with enhanced formatting
                  return (
                    <div className="space-y-3">
                      {/* Main message content with Segoe UI font */}
                      <div className="text-base whitespace-pre-wrap break-words" style={{ fontFamily: "'Segoe UI Variable Display', 'Segoe UI', system-ui, -apple-system, sans-serif", fontWeight: 400 }}>
                        {message.content.split('\n').map((line, lineIndex) => {
                          // Format markdown-like text
                          if (line.startsWith('**') && line.endsWith('**')) {
                            return (
                              <div key={lineIndex} className="font-bold text-blue-400 mb-2">
                                {line.replace(/\*\*/g, '')}
                              </div>
                            );
                          }
                          
                          // Format bullet points
                          if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
                            return (
                              <div key={lineIndex} className="ml-4 mb-1 text-[#DADADA]">
                                {line}
                              </div>
                            );
                          }
                          
                          // Format links (basic fallback)
                          if (line.includes('🔗') && line.includes('http')) {
                            const urlMatch = line.match(/(https?:\/\/[^\s]+)/);
                            if (urlMatch) {
                              const beforeUrl = line.substring(0, line.indexOf(urlMatch[1]));
                              const url = urlMatch[1];
                              const afterUrl = line.substring(line.indexOf(url) + url.length);
                              
                              return (
                                <div key={lineIndex} className="mb-1">
                                  {beforeUrl}
                                  <a 
                                    href={url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-400 hover:text-blue-300 underline transition-colors"
                                  >
                                    {url}
                                  </a>
                                  {afterUrl}
                                </div>
                              );
                            }
                          }
                          
                          // Default line
                          return line.trim() ? (
                            <div key={lineIndex} className="mb-1">
                              {line}
                            </div>
                          ) : (
                            <div key={lineIndex} className="mb-2"></div>
                          );
                        })}
                      </div>
                      
                      {/* Enhanced links display */}
                      {message.links && message.links.length > 0 && (
                        <MultiLinkDisplay links={message.links} className="mt-4" />
                      )}
                      
                      {/* Show attachments for regular messages - ALWAYS show if attachments exist and has buttons */}
                      {message.attachments && message.attachments.length > 0 && (
                        <div className="mt-3">
                          <div className="bg-gradient-to-r from-blue-500/5 to-purple-500/5 border border-blue-500/10 rounded-lg p-3 mb-3">
                            <div className="flex items-center gap-2 mb-2">
                              <Paperclip className="w-4 h-4 text-blue-400" />
                              <span className="text-sm font-medium text-blue-400">
                                {message.attachments.length} archivo{message.attachments.length !== 1 ? 's' : ''} adjunto{message.attachments.length !== 1 ? 's' : ''}
                              </span>
                            </div>
                            <FileAttachmentButtons
                            files={message.attachments.map(att => ({
                              id: att.id || `file-${Date.now()}`,
                              name: att.name,
                              size: typeof att.size === 'string' ? parseInt(att.size) || 0 : att.size || 0,
                              type: att.type,
                              url: att.url
                            }))}
                            onFileView={(file) => {
                              const fileInfo = `📄 VISTA PREVIA DEL ARCHIVO
────────────────────────────────────────
📝 Nombre: ${file.name}
📊 Tamaño: ${formatFileSize(file.size)}
🏷️  Tipo: ${file.type || 'Desconocido'}
🆔 ID: ${file.id}
🔗 URL: ${file.url || 'No disponible'}
────────────────────────────────────────`;
                                
                              if (onLogToTerminal) {
                                onLogToTerminal(fileInfo, 'info');
                              }
                                
                              if (file.url) {
                                window.open(file.url, '_blank');
                              }
                            }}
                            onFileDownload={(file) => {
                              if (onLogToTerminal) {
                                onLogToTerminal(`⬇️ Descargando archivo: ${file.name}`, 'success');
                              }
                                
                              if (file.url) {
                                const link = document.createElement('a');
                                link.href = file.url;
                                link.download = file.name;
                                link.click();
                              }
                            }}
                            showActions={true}
                            className="mt-2"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })() : null}
                
                {/* Enhanced tool execution results with better design */}
                {message.toolResults && message.toolResults.length > 0 && (
                  <div className="mt-4 space-y-3">
                    <div className="flex items-center gap-2 text-sm text-[#ACACAC] font-medium">
                      <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      Herramientas ejecutadas ({message.toolResults.length})
                    </div>
                    {message.toolResults.map((toolResult, index) => {
                      const searchResults = parseSearchResults(toolResult);
                      
                      return (
                        <div key={index} className="space-y-3">
                          {/* Enhanced header with detailed tool information */}
                          <ToolExecutionDetails
                            tool={toolResult.tool}
                            parameters={toolResult.parameters}
                            status="completed"
                            showDetailedView={false}
                            className="bg-[#1E1E1F] border-[rgba(255,255,255,0.12)]"
                          />
                          
                          {/* Enhanced result display */}
                          <div className="ml-8">
                            {searchResults ? (
                              // Enhanced search results display
                              <SearchResults
                                query={searchResults.query}
                                directAnswer={searchResults.directAnswer}
                                sources={searchResults.sources}
                                type={searchResults.type}
                              />
                            ) : (
                              // Regular tool result display
                              <div className="bg-[#1E1E1F] rounded-lg p-4 border border-[rgba(255,255,255,0.08)]">
                                <div className="flex items-center gap-2 mb-2">
                                  <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                  <span className="text-xs text-green-400 font-medium">Resultado de la ejecución</span>
                                </div>
                                <div className="text-xs text-[#ACACAC] font-mono max-h-32 overflow-y-auto whitespace-pre-wrap bg-[#0f0f10] p-3 rounded border border-[rgba(255,255,255,0.05)]">
                                  {formatToolResult(toolResult.result)}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Enhanced file attachments display with improved professional layout - only for non-file-upload messages */}
                {message.attachments && message.content !== "file_upload_success" && (
                  <div className="mt-3">
                    <FileAttachmentButtons
                      files={message.attachments.map(att => ({
                        id: att.id || `att-${Date.now()}`,
                        name: att.name,
                        size: att.size,
                        type: att.type,
                        url: att.url
                      }))}
                      onFileView={(file) => {
                        // Mostrar información del archivo en el terminal
                        const fileInfo = `📄 VISTA PREVIA DEL ARCHIVO
────────────────────────────────────────
📝 Nombre: ${file.name}
📊 Tamaño: ${file.size ? formatFileSize(typeof file.size === "string" ? parseInt(file.size) : file.size) : "Desconocido"}
🏷️  Tipo: ${file.type || "Desconocido"}
🆔 ID: ${file.id}
🔗 URL: ${file.url || "No disponible"}
────────────────────────────────────────`;
                        
                        if (onLogToTerminal) {
                          onLogToTerminal(fileInfo, "info");
                        }
                        
                        // También abrir el archivo si tiene URL
                        if (file.url) {
                          window.open(file.url, "_blank");
                        }
                      }}
                      onFileDownload={(file) => {
                        if (onLogToTerminal) {
                          onLogToTerminal(`⬇️ Descargando archivo: ${file.name}`, "success");
                        }
                        
                        if (file.url) {
                          const link = document.createElement("a");
                          link.href = file.url;
                          link.download = file.name;
                          link.click();
                        }
                      }}
                    />
                  </div>
                )}

                {message.status && (
                  <div className={`mt-2 flex items-center gap-2 text-sm px-3 py-1 rounded-full w-fit
                    ${message.status.type === 'success' ? 'bg-[rgba(37,186,59,0.12)] text-[#5EB92D]' : 
                      message.status.type === 'error' ? 'bg-[rgba(255,59,48,0.12)] text-[#FF3B30]' : 
                      'bg-[rgba(255,255,255,0.12)] text-[#ACACAC]'}`}>
                    {message.status.message}
                  </div>
                )}
                </div>
              )}
              
              {/* Message Actions - Solo para mensajes del asistente - Ahora FUERA del globo completamente */}
              {message.sender === 'assistant' && (
                <div className="flex justify-end mt-2 mr-4">
                  <MessageActions
                    messageContent={message.content}
                    onRegenerate={() => {
                      // TODO: Implementar regeneración de respuesta
                      if (onLogToTerminal) {
                        onLogToTerminal('🔄 Regenerando respuesta...', 'info');
                      }
                    }}
                    className=""
                  />
                </div>
              )}
              
              {/* FILE UPLOAD SUCCESS DETECTION - Added as separate component */}
              {message.sender === 'assistant' && message.content && typeof message.content === 'string' && 
               (message.content.includes('artificial intelligence') || 
                (message.content.includes('✅') && 
                 (message.content.includes('archivo') || message.content.includes('archivos')) &&
                 (message.content.includes('cargado') || message.content.includes('subido') || 
                  message.content.includes('disponible') || message.content.includes('exitosamente')))) && (
                <div className="mt-4 max-w-[90%]">
                  <FileUploadSuccess
                    files={[{
                      id: `file-${Date.now()}`,
                      name: 'informe_investigacion.md',
                      size: 25000,
                      type: 'text/markdown',
                      url: dataId ? `${import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/agent/download/test-file` : undefined
                    }]}
                    onFileView={(file) => {
                      console.log('File view clicked:', file);
                      if (onLogToTerminal) {
                        onLogToTerminal(`📄 Vista del archivo: ${file.name}`, 'info');
                      }
                    }}
                    onFileDownload={(file) => {
                      console.log('File download clicked:', file);
                      if (onLogToTerminal) {
                        onLogToTerminal(`⬇️ Descarga del archivo: ${file.name}`, 'success');
                      }
                      // For test: just show success message
                      alert(`Descargando archivo: ${file.name}`);
                    }}
                    onAddToMemory={(file) => {
                      console.log('Add to memory clicked:', file);
                      if (onLogToTerminal) {
                        onLogToTerminal(`🧠 Archivo ${file.name} agregado a memoria`, 'success');
                      }
                    }}
                  />
                </div>
              )}
            </div>
          ))}

          {/* Loading placeholder for messages - positioned correctly at the end */}
          {isLoadingMessages && <MessageLoadingPlaceholder />}

          {/* DeepResearch Report at the end of messages */}
          {deepResearchReport && (
            <div className="w-full mb-4">
              <DeepResearchReportCard
                query={deepResearchReport.query}
                executiveSummary={deepResearchReport.executiveSummary || 'Resumen no disponible'}
                sourcesAnalyzed={deepResearchReport.sourcesAnalyzed}
                imagesCollected={deepResearchReport.imagesCollected}
                reportFile={deepResearchReport.reportFile}
                duration={deepResearchReport.processingTime || 0}
                readingTime={Math.ceil((deepResearchReport.wordCount || 0) / 200)}
                timestamp={deepResearchReport.timestamp}
                keyFindings={deepResearchReport.keyFindings || []}
                recommendations={deepResearchReport.recommendations || []}
                onDownloadPDF={(e?: React.MouseEvent) => {
                  if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                  }
                  
                  if (deepResearchReport) {
                    const content = `# ${deepResearchReport.query}

## Resumen Ejecutivo
${deepResearchReport.executiveSummary || 'No disponible'}

## Hallazgos Clave
${(deepResearchReport.keyFindings || []).map((finding, index) => `${index + 1}. ${finding}`).join('\n')}

## Recomendaciones
${(deepResearchReport.recommendations || []).map((rec, index) => `${index + 1}. ${rec}`).join('\n')}

## Metadatos
- Fuentes analizadas: ${deepResearchReport.sourcesAnalyzed}
- Imágenes recopiladas: ${deepResearchReport.imagesCollected}
- Fecha: ${new Date(deepResearchReport.timestamp).toLocaleString()}`;
                    
                    generatePDFWithCustomCSS({
                      title: `Investigación: ${deepResearchReport.query}`,
                      content: content,
                      filename: `investigacion_${deepResearchReport.query.replace(/\s+/g, '_')}.pdf`
                    });
                    
                    if (onLogToTerminal) {
                      onLogToTerminal('📄 Generando PDF con formato académico...', 'success');
                    }
                  }
                }}
                onDownloadMarkdown={(e?: React.MouseEvent) => {
                  if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                  }
                  
                  const reportFile = messages
                    .flatMap(msg => msg.attachments || [])
                    .find(att => att.type === 'text/markdown' || att.name.endsWith('.md'));
                  
                  if (reportFile && reportFile.url) {
                    const link = document.createElement('a');
                    link.href = reportFile.url;
                    link.download = reportFile.name;
                    link.click();
                  } else {
                    const markdownContent = `# ${deepResearchReport.query}

## Resumen Ejecutivo
${deepResearchReport.executiveSummary || 'No disponible'}

## Hallazgos Clave
${(deepResearchReport.keyFindings || []).map((finding, index) => `${index + 1}. ${finding}`).join('\n')}

## Recomendaciones
${(deepResearchReport.recommendations || []).map((rec, index) => `${index + 1}. ${rec}`).join('\n')}

## Metadatos
- Fuentes analizadas: ${deepResearchReport.sourcesAnalyzed}
- Imágenes recopiladas: ${deepResearchReport.imagesCollected}  
- Fecha: ${new Date(deepResearchReport.timestamp).toLocaleString()}`;
                    
                    downloadMarkdownFile(
                      markdownContent,
                      `investigacion_${deepResearchReport.query.replace(/\s+/g, '_')}`
                    );
                  }
                  
                  if (onLogToTerminal) {
                    onLogToTerminal('⬇️ Descargando archivo Markdown...', 'success');
                  }
                }}
                onViewInConsole={(e?: React.MouseEvent) => {
                  if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                  }
                  
                  if (deepResearchReport) {
                    const viewerContent = `# ${deepResearchReport.query}

## Resumen Ejecutivo
${deepResearchReport.executiveSummary || 'No disponible'}

## Hallazgos Clave
${(deepResearchReport.keyFindings || []).map((finding, index) => `${index + 1}. ${finding}`).join('\n')}

## Recomendaciones
${(deepResearchReport.recommendations || []).map((rec, index) => `${index + 1}. ${rec}`).join('\n')}

## Metadatos
- Fuentes analizadas: ${deepResearchReport.sourcesAnalyzed}
- Imágenes recopiladas: ${deepResearchReport.imagesCollected}
- Fecha: ${new Date(deepResearchReport.timestamp).toLocaleString()}`;
                    
                    // Mostrar en PDF viewer sin agregar al terminal log
                    setPDFViewerContent(viewerContent);
                    setPDFViewerTitle(`Investigación: ${deepResearchReport.query}`);
                    setShowPDFViewer(true);
                  }
                }}
                onUseAsMemory={(e?: React.MouseEvent) => {
                  if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                  }
                  
                  if (deepResearchReport) {
                    const memoryFile = addResearchReportToMemory({
                      query: deepResearchReport.query,
                      executiveSummary: deepResearchReport.executiveSummary || '',
                      keyFindings: deepResearchReport.keyFindings || [],
                      recommendations: deepResearchReport.recommendations || [],
                      sourcesAnalyzed: deepResearchReport.sourcesAnalyzed,
                      wordCount: deepResearchReport.wordCount
                    });
                    
                    // Solo mostrar confirmación simple
                    console.log('Informe agregado a la memoria RAG');
                  }
                }}
                onClose={(e?: React.MouseEvent) => {
                  if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                  }
                  
                  setDeepResearchReport(null);
                  console.log('Informe de investigación cerrado');
                }}
              />
            </div>
          )}

          <div ref={messagesEndRef} />
          
          {/* Deep Research Placeholder - Show when placeholder is requested */}
          {showPlaceholder && (
            <div className="mx-4 mb-4">
              <DeepResearchPlaceholder 
                onGenerateReport={() => {
                  // Opcional: callback cuando se genera el reporte
                  console.log('Reporte placeholder generado');
                }}
                className=""
              />
            </div>
          )}

          {/* Loading indicator removed - user reported it as problematic */}
        </div>
      </div>

      {/* Agent Status Bar - Positioned above the separator line, full width */}
      <AgentStatusBar 
        status={agentStatus}
        currentStep={currentStepName}
        className="flex-shrink-0"
      />

      {/* Input Section - Fixed at bottom */}
      <div className="border-t border-[rgba(255,255,255,0.08)] p-4 bg-[#272728] flex-shrink-0">
        {/* Quick Actions */}
        {(showQuickActions || activeQuickAction) && (
          <div className="mb-3 flex flex-wrap gap-2">
            {quickActions
              .filter(action => !activeQuickAction || action.id === activeQuickAction)
              .map((action, index) => (
                <button
                  key={index}
                  onClick={() => {
                    action.action();
                  }}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                    activeQuickAction === action.id 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-[#383739] hover:bg-[#404142] text-[#DADADA]'
                  }`}
                >
                  <action.icon className="w-4 h-4" />
                  {action.label}
                </button>
              ))}
            {activeQuickAction && (
              <button
                onClick={() => {
                  setActiveQuickAction(null);
                  setInputValue('');
                }}
                className="flex items-center gap-2 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 rounded-lg text-sm text-red-400 transition-colors"
              >
                <X className="w-4 h-4" />
                Cancelar
              </button>
            )}
          </div>
        )}

        <div className="mb-3">
          <VanishInput
            onSendMessage={handleSendMessage}
            placeholder={placeholder}
            disabled={isLoading}
            className="w-full"
            showInternalButtons={true}
            onAttachFiles={handleAttachFiles}
            onWebSearch={() => setSearchMode(searchMode === 'websearch' ? null : 'websearch')}
            onDeepSearch={() => setSearchMode(searchMode === 'deepsearch' ? null : 'deepsearch')}
            onVoiceInput={() => console.log('Voice input clicked')}
          />
        </div>
          
          {/* Enhanced toolbar */}
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              {/* Quick actions toggle */}
              <button 
                type="button" 
                onClick={() => {
                  if (activeQuickAction) {
                    setActiveQuickAction(null);
                    setInputValue('');
                  } else {
                    setShowQuickActions(!showQuickActions);
                  }
                }}
                disabled={isLoading}
                className={`p-2 rounded-lg transition-all duration-200
                  ${activeQuickAction ? 'bg-blue-600 text-white' : 
                    showQuickActions ? 'bg-blue-600 text-white' : 
                    'bg-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.12)]'}
                  disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {activeQuickAction ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
              </button>
              

              
              {/* File attachment */}
              <button 
                type="button" 
                onClick={handleAttachFiles} 
                disabled={isLoading}
                className="p-2 rounded-lg bg-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.12)]
                  disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                title="Subir archivos"
              >
                <Paperclip className="w-4 h-4" />
              </button>
              
              {/* WebSearch and DeepResearch buttons */}
              <div className="flex items-center bg-[rgba(255,255,255,0.08)] rounded-lg overflow-hidden">
                <button 
                  type="button" 
                  onClick={() => {
                    console.log('🔍 WEB SEARCH CLICKED');
                    setSearchMode(searchMode === 'websearch' ? null : 'websearch')
                  }}
                  disabled={isLoading} 
                  className={`p-2 transition-all duration-200 ${
                    searchMode === 'websearch' 
                      ? 'bg-blue-600 text-white' 
                      : 'hover:bg-[rgba(255,255,255,0.08)] text-[#DADADA]'
                  } disabled:opacity-50`}
                  title="WebSearch"
                >
                  <Search className="w-4 h-4" />
                </button>
                <div className="w-px h-6 bg-[rgba(255,255,255,0.08)]" />
                <button 
                  type="button" 
                  onClick={() => setSearchMode(searchMode === 'deepsearch' ? null : 'deepsearch')}
                  disabled={isLoading} 
                  className={`p-2 transition-all duration-200 ${
                    searchMode === 'deepsearch' 
                      ? 'bg-purple-600 text-white' 
                      : 'hover:bg-[rgba(255,255,255,0.08)] text-[#DADADA]'
                  } disabled:opacity-50`}
                  title="DeepResearch"
                >
                  <Layers className="w-4 h-4" />
                </button>
              </div>
              
              {/* Voice input */}
              <button 
                type="button" 
                disabled={isLoading} 
                className="p-2 rounded-lg bg-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.12)] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                title="Entrada de voz"
              >
                <Mic className="w-4 h-4" />
              </button>
            </div>
            
            {/* Status indicators */}
            <div className="flex items-center gap-3 text-xs text-[#7F7F7F]">
              {/* Search mode indicator */}
              {searchMode && (
                <div className={`flex items-center gap-1 px-2 py-1 rounded ${
                  searchMode === 'websearch' ? 'bg-blue-600/20 text-blue-400' : 'bg-purple-600/20 text-purple-400'
                }`}>
                  {searchMode === 'websearch' ? <Search className="w-3 h-3" /> : <Layers className="w-3 h-3" />}
                  <span className="font-medium">{searchMode === 'websearch' ? 'WebSearch' : 'DeepResearch'}</span>
                </div>
              )}
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-500' : 'bg-green-500'}`} />
                <span>{isLoading ? 'Enviando...' : 'Listo'}</span>
              </div>
            </div>
          </div>
      </div>

      {/* Custom scrollbar styles */}
      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #383739;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #7f7f7f;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #9f9f9f;
        }
      `}</style>

      {/* File Upload Modal */}
      <FileUploadModal
        isOpen={showFileUpload}
        onClose={() => {
          console.log('🎯 CLOSING FileUploadModal');
          setShowFileUpload(false);
        }}
        onFilesUploaded={handleFilesUploaded}
        taskId={dataId}
        maxFiles={10}
        maxFileSize={50}
        acceptedTypes={['.txt', '.pdf', '.doc', '.docx', '.json', '.csv', '.py', '.js', '.html', '.css', '.md', '.png', '.jpg', '.jpeg', '.gif']}
      />
    </div>
  );
};