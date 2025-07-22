import React, { useEffect, useState, useRef } from 'react';
import { Send, Paperclip, Mic } from 'lucide-react';
import { agentAPI, ChatResponse } from '../../services/api';
import { VanishInput } from '../VanishInput';

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
  toolResults?: any[];
  searchData?: any;
  links?: Array<{
    url: string;
    title?: string;
    description?: string;
  }>;
}

export interface SimpleChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  onUpdateMessages?: (messages: Message[]) => void;
  onTaskPlanGenerated?: (plan: any) => void;
  onLogToTerminal?: (message: string, type?: 'info' | 'success' | 'error') => void;
  isTyping?: boolean;
  assistantName?: string;
  placeholder?: string;
  className?: string;
  'data-id'?: string;
  onTaskReset?: () => void;
  isNewTask?: boolean;
}

export const SimpleChatInterface: React.FC<SimpleChatInterfaceProps> = ({
  messages,
  onSendMessage,
  onUpdateMessages,
  onTaskPlanGenerated,
  onLogToTerminal,
  isTyping = false,
  assistantName = 'Agente',
  placeholder = 'Describe tu tarea...',
  className = '',
  'data-id': dataId,
  onTaskReset,
  isNewTask = false
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll al final
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // SIMPLIFICADO: Solo una función para enviar mensajes
  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;
    
    setIsLoading(true);
    
    try {
      // 1. Crear mensaje del usuario
      const userMessage: Message = {
        id: `msg-${Date.now()}-user`,
        content: message.trim(),
        sender: 'user',
        timestamp: new Date()
      };

      // 2. Agregar mensaje del usuario AL ESTADO LOCAL INMEDIATAMENTE
      if (onUpdateMessages) {
        const updatedMessages = [...messages, userMessage];
        onUpdateMessages(updatedMessages);
      }

      // 3. Llamar callback para TaskView (importante para preservar la funcionalidad)
      onSendMessage(message.trim());

      // 4. Si es el primer mensaje, generar plan específico
      const isFirstMessage = messages.length === 0;
      
      if (isFirstMessage) {
        // Generar plan específico
        const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
        const planResponse = await fetch(`${backendUrl}/api/agent/generate-plan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task_title: message.trim(),
            task_id: dataId
          })
        });

        if (planResponse.ok) {
          const planData = await planResponse.json();
          
          // Crear respuesta del agente
          const agentMessage: Message = {
            id: `msg-${Date.now()}-agent`,
            content: `✅ Plan de acción generado. Ejecutando ${planData.total_steps || planData.plan?.length || 0} pasos para completar tu tarea.`,
            sender: 'assistant',
            timestamp: new Date(),
          };

          // Actualizar mensajes con la respuesta del agente
          if (onUpdateMessages) {
            const finalMessages = [...messages, userMessage, agentMessage];
            onUpdateMessages(finalMessages);
          }

          // Notificar plan generado para mostrar en TerminalView
          if (onTaskPlanGenerated && planData.plan) {
            onTaskPlanGenerated({
              steps: planData.plan,
              total_steps: planData.total_steps || planData.plan.length,
              estimated_total_time: planData.estimated_total_time,
              task_type: planData.task_type,
              complexity: planData.complexity
            });
          }

          if (onLogToTerminal) {
            onLogToTerminal(`📋 Plan generado: ${planData.total_steps || planData.plan?.length} pasos`, 'success');
          }
        } else {
          throw new Error('Failed to generate plan');
        }
      } else {
        // Para mensajes posteriores, usar chat normal
        const chatResponse: ChatResponse = await agentAPI.sendMessage(message.trim(), {
          task_id: dataId,
          previous_messages: messages.slice(-3) // Últimos 3 mensajes como contexto
        });

        const agentMessage: Message = {
          id: `msg-${Date.now()}-agent`,
          content: chatResponse.response,
          sender: 'assistant',
          timestamp: new Date(chatResponse.timestamp),
          toolResults: chatResponse.tool_results || [],
          searchData: chatResponse.search_data,
          links: chatResponse.links
        };

        // Actualizar mensajes
        if (onUpdateMessages) {
          const finalMessages = [...messages, userMessage, agentMessage];
          onUpdateMessages(finalMessages);
        }

        // Log tool executions
        if (chatResponse.tool_results && onLogToTerminal) {
          chatResponse.tool_results.forEach(tool => {
            onLogToTerminal(`🔧 ${tool.tool}: ${JSON.stringify(tool.parameters)}`, 'info');
          });
        }
      }

    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: `msg-${Date.now()}-error`,
        content: 'Error al procesar el mensaje. Por favor, intenta de nuevo.',
        sender: 'assistant',
        timestamp: new Date(),
        status: { type: 'error', message: 'Error de conexión' }
      };

      if (onUpdateMessages) {
        const errorMessages = [...messages, errorMessage];
        onUpdateMessages(errorMessages);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#272728] text-[#DADADA]" data-id={dataId}>
      {/* Estado de carga */}
      {(isTyping || isLoading) && (
        <div className="px-4 py-2 border-b border-[rgba(255,255,255,0.08)] bg-[#272728]">
          <div className="flex items-center gap-2 text-sm text-[#ACACAC]">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
            {assistantName} está {isLoading ? 'procesando' : 'escribiendo'}...
          </div>
        </div>
      )}

      {/* Mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-xl p-4 ${
              message.sender === 'user' 
                ? 'bg-[rgba(255,255,255,0.06)] text-[#DADADA]' 
                : 'bg-[#383739] text-[#DADADA]'
            }`}>
              {/* Contenido del mensaje */}
              <div className="whitespace-pre-wrap break-words text-base">
                {message.content}
              </div>

              {/* Status */}
              {message.status && (
                <div className={`mt-2 text-sm px-2 py-1 rounded ${
                  message.status.type === 'success' ? 'bg-green-500/20 text-green-400' :
                  message.status.type === 'error' ? 'bg-red-500/20 text-red-400' :
                  'bg-blue-500/20 text-blue-400'
                }`}>
                  {message.status.message}
                </div>
              )}

              {/* Tool Results - Simplificado */}
              {message.toolResults && message.toolResults.length > 0 && (
                <div className="mt-3 space-y-2">
                  <div className="text-xs text-[#ACACAC]">
                    🔧 {message.toolResults.length} herramienta(s) ejecutada(s)
                  </div>
                  {message.toolResults.slice(0, 2).map((tool, idx) => (
                    <div key={idx} className="text-xs bg-[#1E1E1F] p-2 rounded border border-[rgba(255,255,255,0.05)]">
                      <strong>{tool.tool}</strong>: {JSON.stringify(tool.parameters).substring(0, 100)}...
                    </div>
                  ))}
                </div>
              )}

              {/* Links - Simplificado */}
              {message.links && message.links.length > 0 && (
                <div className="mt-3 space-y-1">
                  {message.links.slice(0, 3).map((link, idx) => (
                    <a key={idx} href={link.url} target="_blank" rel="noopener noreferrer" 
                       className="block text-blue-400 hover:text-blue-300 text-sm truncate">
                      🔗 {link.title || link.url}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input simplificado */}
      <div className="border-t border-[rgba(255,255,255,0.08)] p-4 bg-[#272728]">
        <VanishInput
          onSendMessage={handleSendMessage}
          placeholder={placeholder}
          disabled={isLoading}
          className="w-full"
        />
      </div>
    </div>
  );
};