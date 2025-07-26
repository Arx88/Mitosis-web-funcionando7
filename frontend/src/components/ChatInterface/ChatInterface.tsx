import React, { useEffect, useState, useRef, useMemo, useCallback } from 'react';
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
  onFilesClick?: () => void;
  onShareClick?: () => void;
  disabled?: boolean;
  task?: any;
  onUpdateTask?: (updater: (task: any) => any) => void;
}

// ========================================================================
// COMPONENTES MEMOIZADOS PARA EVITAR RE-RENDERS
// ========================================================================

const MessageComponent = React.memo<{
  message: Message;
  assistantName: string;
  onLogToTerminal?: (message: string, type?: 'info' | 'success' | 'error') => void;
}>(({ message, assistantName, onLogToTerminal }) => {
  // Memoizar contenido del mensaje
  const messageContent = useMemo(() => {
    if (message.content === 'search_results' && message.searchData) {
      return <SearchResults searchData={message.searchData} />;
    }
    
    if (message.content === 'file_upload_success' && message.uploadData) {
      return <FileUploadSuccess uploadData={message.uploadData} />;
    }
    
    if (message.content === 'task_summary' && message.status?.type === 'success') {
      return <TaskSummary message={message.status.message} />;
    }
    
    return <div className="whitespace-pre-wrap">{message.content}</div>;
  }, [message.content, message.searchData, message.uploadData, message.status]);

  // Memoizar attachments
  const attachments = useMemo(() => {
    if (!message.attachments || message.attachments.length === 0) return null;
    
    return (
      <div className="mt-3 space-y-2">
        {message.attachments.map((attachment, index) => (
          <FileAttachment key={`${message.id}-${index}`} file={attachment} />
        ))}
      </div>
    );
  }, [message.attachments, message.id]);

  // Memoizar tool results
  const toolResults = useMemo(() => {
    if (!message.toolResults || message.toolResults.length === 0) return null;
    
    return (
      <div className="mt-3 space-y-2">
        {message.toolResults.map((result, index) => (
          <ToolExecutionDetails 
            key={`${message.id}-tool-${index}`} 
            result={result} 
            onLogToTerminal={onLogToTerminal}
          />
        ))}
      </div>
    );
  }, [message.toolResults, message.id, onLogToTerminal]);

  // Memoizar links
  const links = useMemo(() => {
    if (!message.links || message.links.length === 0) return null;
    
    return (
      <div className="mt-3">
        <MultiLinkDisplay links={message.links} />
      </div>
    );
  }, [message.links]);

  return (
    <div className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
        message.sender === 'user'
          ? 'bg-blue-600 text-white'
          : 'bg-[rgba(255,255,255,0.06)] text-[#DADADA] border border-[rgba(255,255,255,0.08)]'
      }`}>
        {message.sender === 'assistant' && (
          <div className="text-xs text-gray-400 mb-2">{assistantName}</div>
        )}
        
        {messageContent}
        {attachments}
        {toolResults}
        {links}
        
        {message.status && (
          <div className={`mt-2 text-xs p-2 rounded ${
            message.status.type === 'success'
              ? 'bg-green-900/20 text-green-400'
              : message.status.type === 'error'
              ? 'bg-red-900/20 text-red-400'
              : 'bg-blue-900/20 text-blue-400'
          }`}>
            {message.status.message}
          </div>
        )}
        
        <div className="text-xs text-gray-400 mt-2">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  return prevProps.message.id === nextProps.message.id &&
         prevProps.message.content === nextProps.message.content &&
         prevProps.assistantName === nextProps.assistantName;
});

MessageComponent.displayName = 'MessageComponent';

// ========================================================================
// COMPONENTE PRINCIPAL OPTIMIZADO
// ========================================================================

const ChatInterfaceComponent: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  onAttachFiles,
  isTyping = false,
  assistantName = "Agente",
  placeholder = "Escribe tu mensaje...",
  className = "",
  onUpdateMessages,
  onLogToTerminal,
  onTaskPlanGenerated,
  onFilesClick,
  onShareClick,
  disabled = false,
  task,
  onUpdateTask
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // ========================================================================
  // CALLBACKS MEMOIZADOS
  // ========================================================================

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const handleSendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      content: message.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    // Actualizar mensajes inmediatamente para UI responsive
    if (onUpdateMessages) {
      onUpdateMessages([...messages, userMessage]);
    }

    setInputValue('');
    setIsLoading(true);

    try {
      const response = await agentAPI.sendMessage(message, task?.id);
      
      if (response.success) {
        const assistantMessage: Message = {
          id: `msg-${Date.now() + 1}`,
          content: response.message,
          sender: 'assistant',
          timestamp: new Date(),
          toolResults: response.toolResults,
          searchData: response.searchData,
          uploadData: response.uploadData,
          links: response.links
        };

        if (onUpdateMessages) {
          onUpdateMessages([...messages, userMessage, assistantMessage]);
        }

        // Si hay un plan generado, actualizar la tarea
        if (response.plan && onUpdateTask) {
          onUpdateTask((currentTask: any) => ({
            ...currentTask,
            plan: response.plan,
            status: 'in-progress'
          }));

          if (onTaskPlanGenerated) {
            onTaskPlanGenerated(response.plan);
          }
        }

        // Log de herramientas al terminal
        if (response.toolResults && onLogToTerminal) {
          response.toolResults.forEach((result: ToolResult) => {
            onLogToTerminal(
              `Tool: ${result.tool_name} - ${result.success ? 'Success' : 'Failed'}`,
              result.success ? 'success' : 'error'
            );
          });
        }
      } else {
        const errorMessage: Message = {
          id: `msg-${Date.now() + 1}`,
          content: 'Error al procesar el mensaje',
          sender: 'assistant',
          timestamp: new Date(),
          status: {
            type: 'error',
            message: response.error || 'Error desconocido'
          }
        };

        if (onUpdateMessages) {
          onUpdateMessages([...messages, userMessage, errorMessage]);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        content: 'Error de conexión',
        sender: 'assistant',
        timestamp: new Date(),
        status: {
          type: 'error',
          message: 'No se pudo conectar con el servidor'
        }
      };

      if (onUpdateMessages) {
        onUpdateMessages([...messages, userMessage, errorMessage]);
      }
    } finally {
      setIsLoading(false);
    }
  }, [messages, onUpdateMessages, isLoading, task?.id, onUpdateTask, onTaskPlanGenerated, onLogToTerminal]);

  const handleFileUpload = useCallback(async (files: FileList) => {
    if (onAttachFiles) {
      onAttachFiles(files);
    }
    setShowFileUpload(false);
  }, [onAttachFiles]);

  const handleAttachClick = useCallback(() => {
    setShowFileUpload(true);
  }, []);

  const handleCloseFileUpload = useCallback(() => {
    setShowFileUpload(false);
  }, []);

  // ========================================================================
  // EFFECTS OPTIMIZADOS
  // ========================================================================

  useEffect(() => {
    scrollToBottom();
  }, [messages.length, scrollToBottom]);

  // ========================================================================
  // MEMOIZED VALUES
  // ========================================================================

  const renderedMessages = useMemo(() => {
    return messages.map((message) => (
      <MessageComponent
        key={message.id}
        message={message}
        assistantName={assistantName}
        onLogToTerminal={onLogToTerminal}
      />
    ));
  }, [messages, assistantName, onLogToTerminal]);

  const typingIndicator = useMemo(() => {
    if (!isTyping && !isLoading) return null;
    
    return (
      <div className="flex justify-start mb-4">
        <div className="bg-[rgba(255,255,255,0.06)] rounded-2xl px-4 py-3 border border-[rgba(255,255,255,0.08)]">
          <div className="text-xs text-gray-400 mb-1">{assistantName}</div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <span className="ml-2 text-gray-400 text-sm">
              {isLoading ? 'Procesando...' : 'Escribiendo...'}
            </span>
          </div>
        </div>
      </div>
    );
  }, [isTyping, isLoading, assistantName]);

  const fileUploadModal = useMemo(() => (
    <FileUploadModal
      isOpen={showFileUpload}
      onClose={handleCloseFileUpload}
      onFilesUploaded={handleFileUpload}
    />
  ), [showFileUpload, handleCloseFileUpload, handleFileUpload]);

  // ========================================================================
  // RENDER OPTIMIZADO
  // ========================================================================

  return (
    <div className={`flex flex-col h-full bg-[#272728] ${className}`}>
      {/* Messages container */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {renderedMessages}
        {typingIndicator}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-[rgba(255,255,255,0.08)] p-4">
        <VanishInput
          onSendMessage={handleSendMessage}
          placeholder={disabled ? "Esperando inicialización..." : placeholder}
          disabled={disabled || isLoading}
          showInternalButtons={true}
          onAttachFiles={handleAttachClick}
          onFilesClick={onFilesClick}
          onShareClick={onShareClick}
        />
      </div>

      {/* File upload modal */}
      {fileUploadModal}
    </div>
  );
};

// ========================================================================
// EXPORT CON REACT.MEMO
// ========================================================================

export const ChatInterface = React.memo(ChatInterfaceComponent, (prevProps, nextProps) => {
  return (
    prevProps.messages.length === nextProps.messages.length &&
    prevProps.isTyping === nextProps.isTyping &&
    prevProps.disabled === nextProps.disabled &&
    prevProps.task?.id === nextProps.task?.id
  );
});