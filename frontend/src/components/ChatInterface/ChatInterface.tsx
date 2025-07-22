import React, { useEffect, useState, useRef } from 'react';
import { Paperclip, Mic, Send, Terminal, Globe, FileText, Plus, Zap, X, Search, Layers } from 'lucide-react';
import { agentAPI, ChatResponse, ToolResult, SearchData, UploadData } from '../../services/api';
import { VanishInput } from '../VanishInput';
import { FileUploadModal } from '../FileUploadModal';
import { FileAttachment } from '../FileAttachment';
import { ToolExecutionDetails } from '../ToolExecutionDetails';
import { SearchResults } from '../SearchResults';
import { FileUploadSuccess } from '../FileUploadSuccess';
import { TaskSummary } from '../TaskSummary';
import { LinkPreview, MultiLinkDisplay } from '../LinkPreview';

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
  onTaskPlanGenerated?: (plan: any) => void;
  onTitleGenerated?: (title: string) => void; // ✨ NUEVO: Callback para título generado
  hasExistingPlan?: boolean; // ✨ NUEVO: Indica si la tarea ya tiene plan generado
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
  onTaskPlanGenerated,
  onTitleGenerated, // ✨ NUEVO: Callback para título generado
  hasExistingPlan = false // ✨ NUEVO: Indica si ya hay plan
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [activeQuickAction, setActiveQuickAction] = useState<string | null>(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Helper function for formatting file sizes
  const formatFileSize = (bytes: number): string => {
    if (!bytes) return 'Tamaño desconocido';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
    if (message.trim() && !isLoading) {
      setIsLoading(true);
      setActiveQuickAction(null);

      // Crear mensaje del usuario
      const userMessage: Message = {
        id: `msg-${Date.now()}-user`,
        content: message,
        sender: 'user',
        timestamp: new Date()
      };

      // Llamar al callback original
      onSendMessage(message);

      try {
        // 🚀 LÓGICA MEJORADA: Si es el primer mensaje de la tarea, usar generate-plan para generar plan específico
        const isFirstMessage = messages.length === 0;
        
        // 🐛 DEBUG: Log critical values for debugging title generation issue
        console.log('🐛 DEBUG - Title Generation Check:', {
          isFirstMessage,
          hasExistingPlan,
          messagesLength: messages.length,
          dataId,
          condition: isFirstMessage && !hasExistingPlan
        });
        
        if (isFirstMessage && !hasExistingPlan) {
          console.log('🎯 FIRST MESSAGE - Calling generate-plan for specific plan generation');
          
          // 🐛 DEBUG: Log backend URL and request details
          const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
          console.log('🐛 DEBUG - Backend URL:', backendUrl);
          console.log('🐛 DEBUG - Request details:', {
            url: `${backendUrl}/api/agent/generate-plan`,
            method: 'POST',
            taskTitle: message.trim(),
            taskId: dataId
          });
          
          try {
            const initResponse = await fetch(`${backendUrl}/api/agent/generate-plan`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                task_title: message.trim(),
                task_id: dataId
              })
            });
            
            console.log('🐛 DEBUG - Response status:', initResponse.status);
            console.log('🐛 DEBUG - Response ok:', initResponse.ok);
          
            if (initResponse.ok) {
              const initData = await initResponse.json();
              console.log('✅ Plan generated with specific AI planning:', initData);
              
              // Crear respuesta del agente indicando que el plan fue generado
              const agentMessage: Message = {
                id: `msg-${Date.now()}-agent`,
                content: `✅ Plan de acción específico generado. Ejecutando ${initData.plan?.length || initData.total_steps || 0} pasos personalizados para completar tu tarea.`,
                sender: 'agent',
                timestamp: new Date()
              };
              
              // ✅ FIXED: Update messages FIRST before title to avoid race condition
              if (onUpdateMessages) {
                const updatedMessages = [...messages, userMessage, agentMessage];
                onUpdateMessages(updatedMessages);
              }
              
              // ✨ FIXED: Update title AFTER messages to ensure it doesn't get overwritten
              if (onTitleGenerated && initData.enhanced_title) {
                console.log('📝 Updating task title with enhanced title (AFTER messages):', initData.enhanced_title);
                onTitleGenerated(initData.enhanced_title);
              }
              
              // ✅ CRITICAL FIX: Call onTaskPlanGenerated callback for plan display in TerminalView
              if (onTaskPlanGenerated && initData.plan) {
                console.log('📋 Calling onTaskPlanGenerated with specific AI plan:', initData);
                onTaskPlanGenerated({
                  steps: initData.plan,
                  total_steps: initData.total_steps,
                  estimated_total_time: initData.estimated_total_time,
                task_type: initData.task_type,
                complexity: initData.complexity
              });
            }
            
          } else {
            console.error('❌ Generate plan failed:', initResponse.status);
            console.error('❌ Response details:', await initResponse.text());
            // Fallback al chat normal si falla
            await sendRegularChatMessage(message, userMessage);
          }
          
          } catch (fetchError) {
            console.error('🐛 DEBUG - Fetch error:', fetchError);
            console.error('🐛 DEBUG - Error type:', fetchError.name);
            console.error('🐛 DEBUG - Error message:', fetchError.message);
            // Fallback al chat normal si hay error de red
            await sendRegularChatMessage(message, userMessage);
          }
          
        } else if (isFirstMessage && hasExistingPlan) {
          console.log('🎯 FIRST MESSAGE - Task already has plan, using regular chat');
          // Si ya hay plan, solo agregar mensaje y usar chat regular
          await sendRegularChatMessage(message, userMessage);
          
        } else {
          // Para mensajes posteriores, usar el chat normal
          await sendRegularChatMessage(message, userMessage);
        }
        
      } catch (error) {
        console.error('❌ Error:', error);
      } finally {
        setIsLoading(false);
      }
    }
  };
  
  // Función helper para el chat normal
  const sendRegularChatMessage = async (processedMessage: string, userMessage: Message) => {
    try {
      // Enviar mensaje al backend usando el endpoint chat normal
      const response: ChatResponse = await agentAPI.sendMessage(processedMessage, {
        task_id: dataId,
        previous_messages: messages.slice(-5), // Enviar últimos 5 mensajes como contexto
      });

      // Parse links from response
      const parseLinksFromText = (text: string) => {
        const urlRegex = /https?:\/\/[^\s\)]+/g;
        const matches = text.match(urlRegex) || [];
        return matches.map(url => ({
          url,
          title: url,
          description: ''
        }));
      };

      const parseStructuredLinks = (text: string) => {
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
        const matches = [...text.matchAll(linkRegex)];
        return matches.map(match => ({
          url: match[2],
          title: match[1],
          description: ''
        }));
      };

      const responseLinks = parseLinksFromText(response.response);
      const structuredLinks = parseStructuredLinks(response.response);
      const allLinks = [...responseLinks, ...structuredLinks];
      
      const uniqueLinks = allLinks.filter((link, index, self) => 
        index === self.findIndex(l => l.url === link.url)
      );

      const agentMessage: Message = {
        id: `msg-${Date.now()}`,
        content: response.response,
        sender: 'assistant',
        timestamp: new Date(response.timestamp),
        toolResults: response.tool_results || [],
        searchData: response.search_data,
        uploadData: response.upload_data,
        links: uniqueLinks.length > 0 ? uniqueLinks : undefined,
        status: response.tool_results && response.tool_results.length > 0 ? {
          type: 'success',
          message: `Ejecuté ${response.tool_results.length} herramienta(s)`
        } : undefined
      };

      if (onUpdateMessages) {
        if (response.plan && response.plan.steps) {
          const planNotificationMessage: Message = {
            id: `plan-${Date.now()}`,
            content: `📋 **Plan generado**\n\nCreé un plan de ${response.plan.total_steps} pasos. Ver progreso en "Plan de Acción".`,
            sender: 'assistant',
            timestamp: new Date(response.timestamp),
            status: {
              type: 'success',
              message: `Plan de ${response.plan.total_steps} pasos generado`
            }
          };
          const messagesWithPlan = [...messages, userMessage, planNotificationMessage];
          onUpdateMessages(messagesWithPlan);
          
          if (onTaskPlanGenerated) {
            onTaskPlanGenerated(response.plan);
          }
        } else {
          const updatedMessages = [...messages, userMessage, agentMessage];
          onUpdateMessages(updatedMessages);
        }
      }

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
        
        onLogToTerminal(`📈 RESUMEN: ${response.tool_results.length} herramienta(s) ejecutada(s) correctamente`, 'info');
      }

    } catch (error) {
      console.error('Error sending message:', error);
      
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
        const currentMessages = [...messages, userMessage];
        const updatedMessages = [...currentMessages, errorMessage];
        onUpdateMessages(updatedMessages);
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
                     process.env.REACT_APP_BACKEND_URL || 
                     'http://localhost:8001';
      
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
          size: f.size,
          type: f.mime_type || f.type || 'application/octet-stream',
          url: `${backendUrl}/api/agent/download/${f.id}`,
          uploadedAt: new Date(),
          preview: f.preview || undefined
        }));

        // Crear mensaje informativo mejorado con archivos subidos
        const uploadMessage: Message = {
          id: `msg-${Date.now()}`,
          content: 'file_upload_success', // Special marker for file upload success
          sender: 'assistant',
          timestamp: new Date(),
          attachments: uploadedFiles,
          status: {
            type: 'success',
            message: `${result.files.length} archivo${result.files.length !== 1 ? 's' : ''} cargado${result.files.length !== 1 ? 's' : ''} y listo${result.files.length !== 1 ? 's' : ''} para usar`
          }
        };

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
    setShowFileUpload(true);
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
          directAnswer: directAnswer || 'Información encontrada en las fuentes listadas',
          sources,
          type: content.includes('🔍') || content.includes('Búsqueda Web') ? 'websearch' : 'deepsearch'
        };
      }
    } catch (error) {
      console.error('Error parsing message as search results:', error);
    }
    return null;
  };

  // Helper function to get file type from extension
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

  const parseMessageAsFileUpload = (content: string) => {
    try {
      // Check if it's a file upload success message with different patterns
      if (content.includes('📎 **Archivos cargados exitosamente**') || 
          content.includes('Archivos cargados exitosamente') ||
          content.includes('archivos** que ahora están disponibles')) {
        
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
            url: undefined
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
            url: undefined
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
  
  // Component's main return statement
  return (
    <div className="flex flex-col h-full bg-[#272728] text-[#DADADA] w-full" data-id={dataId}>
      {/* Sticky Processing Activity Indicator */}
      {(isTyping || isLoading) && (
        <div className="sticky top-0 z-10 bg-[#272728] border-b border-[rgba(255,255,255,0.08)] px-4 py-2 flex-shrink-0">
          <div className="flex items-center gap-2 text-sm text-[#ACACAC]">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
            {assistantName} está {isLoading ? 'procesando' : 'escribiendo'}...
          </div>
        </div>
      )}

      {/* Messages Container - Fixed height with proper scrolling */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <div className="h-full overflow-y-auto p-4 space-y-4 custom-scrollbar" style={{
          scrollbarWidth: 'thin',
          scrollbarColor: '#7f7f7f #383739'
        }}>
          {messages.map(message => (
            <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[90%] ${message.sender === 'user' ? 'bg-[rgba(255,255,255,0.06)]' : 'bg-[#383739]'} rounded-xl p-4`}>
                {/* Special handling for file upload success */}
                {message.content === 'file_upload_success' && message.attachments ? (
                  <FileUploadSuccess
                    files={message.attachments.map(att => ({
                      id: att.id || `file-${Date.now()}`,
                      name: att.name,
                      size: att.size ? parseInt(att.size) : 0,
                      type: att.type,
                      url: att.url
                    }))}
                    onFileView={(file) => {
                      // Mostrar información del archivo en el terminal
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
                      
                      // También abrir el archivo si tiene URL
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
                  />
                ) : (() => {
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
                      />
                    );
                  }
                  
                  // Priority 3: Check if message content contains search results (fallback)
                  if (message.content.includes('🔍') || 
                      message.content.includes('🔬') || 
                      message.content.includes('Búsqueda Web con Tavily') || 
                      message.content.includes('Investigación Profunda')) {
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
                  
                  // Priority 4: Check if message content contains file upload success (fallback)
                  if (message.content.includes('📎') || 
                      message.content.includes('Archivos cargados') || 
                      message.content.includes('archivos** que ahora están disponibles')) {
                    // Parse file upload results from message content
                    const fileUploadResults = parseMessageAsFileUpload(message.content);
                    if (fileUploadResults && fileUploadResults.files.length > 0) {
                      return (
                        <FileUploadSuccess
                          files={fileUploadResults.files}
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
                        />
                      );
                    }
                  }
                  
                  // Priority 5: Render message content with enhanced formatting
                  return (
                    <div className="space-y-3">
                      {/* Main message content */}
                      <div className="text-base whitespace-pre-wrap break-words">
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
                    </div>
                  );
                })()}
                
                
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
                {message.attachments && message.content !== 'file_upload_success' && (
                  <div className="mt-4">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-lg">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-base text-[#DADADA] font-semibold">
                          Archivos adjuntos
                        </h4>
                        <p className="text-sm text-[#ACACAC]">
                          {message.attachments.length} archivo{message.attachments.length !== 1 ? 's' : ''} disponible{message.attachments.length !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                    
                    {/* Professional file grid with enhanced design */}
                    <div className="grid grid-cols-1 gap-3">
                      {message.attachments.map((attachment, index) => (
                        <div
                          key={index}
                          className="group relative"
                        >
                          <FileAttachment
                            file={{
                              id: attachment.id || `att-${index}`,
                              name: attachment.name,
                              size: attachment.size ? parseInt(attachment.size) : undefined,
                              type: attachment.type,
                              preview: attachment.preview,
                              url: attachment.url
                            }}
                            onView={(file) => {
                              // Mostrar información del archivo en el terminal
                              const fileInfo = `📄 VISTA PREVIA DEL ARCHIVO
────────────────────────────────────────
📝 Nombre: ${file.name}
📊 Tamaño: ${file.size ? formatFileSize(file.size) : 'Desconocido'}
🏷️  Tipo: ${file.type || 'Desconocido'}
🆔 ID: ${file.id}
🔗 URL: ${file.url || 'No disponible'}
📅 Cargado: ${attachment.uploadedAt ? new Date(attachment.uploadedAt).toLocaleString() : 'Desconocido'}
────────────────────────────────────────`;
                              
                              if (onLogToTerminal) {
                                onLogToTerminal(fileInfo, 'info');
                              }
                              
                              // También abrir el archivo si tiene URL
                              if (file.url) {
                                window.open(file.url, '_blank');
                              }
                            }}
                            onDownload={(file) => {
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
                            size="medium"
                            showActions={true}
                          />
                        </div>
                      ))}
                    </div>
                    
                    {/* Enhanced summary and bulk actions */}
                    <div className="mt-4 p-4 bg-gradient-to-r from-[#1E1E1F] to-[#252526] rounded-xl border border-[rgba(255,255,255,0.08)]">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                            <span className="text-sm text-green-400 font-medium">
                              {message.attachments.length} archivo{message.attachments.length !== 1 ? 's' : ''} listo{message.attachments.length !== 1 ? 's' : ''}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => {
                              // Mostrar todos los archivos en el terminal
                              const allFilesInfo = message.attachments?.map(att => `📄 ${att.name} (${att.size ? formatFileSize(parseInt(att.size)) : 'Tamaño desconocido'})`).join('\n');
                              if (onLogToTerminal && allFilesInfo) {
                                onLogToTerminal(`📋 ARCHIVOS DISPONIBLES:\n${allFilesInfo}`, 'info');
                              }
                            }}
                            className="px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            Ver todos
                          </button>
                          <button 
                            onClick={() => {
                              message.attachments?.forEach(attachment => {
                                if (attachment.url) {
                                  const link = document.createElement('a');
                                  link.href = attachment.url;
                                  link.download = attachment.name;
                                  link.click();
                                }
                              });
                              if (onLogToTerminal) {
                                onLogToTerminal(`⬇️ Descargando ${message.attachments?.length} archivo${message.attachments?.length !== 1 ? 's' : ''}`, 'success');
                              }
                            }}
                            className="px-3 py-1.5 bg-gradient-to-r from-purple-500/20 to-pink-500/20 hover:from-purple-500/30 hover:to-pink-500/30 text-purple-400 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Descargar todos
                          </button>
                        </div>
                      </div>
                    </div>
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
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>
      </div>

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
        onClose={() => setShowFileUpload(false)}
        onFilesUploaded={handleFilesUploaded}
        maxFiles={10}
        maxFileSize={50}
        acceptedTypes={['.txt', '.pdf', '.doc', '.docx', '.json', '.csv', '.py', '.js', '.html', '.css', '.md', '.png', '.jpg', '.jpeg', '.gif']}
      />
    </div>
  );
};