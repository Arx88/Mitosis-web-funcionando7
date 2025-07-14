import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Send, Terminal, Bot, Zap, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { unifiedAPI, ChatResponse, MonitorPage, AgentStatus } from '../../services/unified_api';
import { VanishInput } from '../VanishInput';
import { ThinkingAnimation } from '../ThinkingAnimation';
import { MessageActions } from '../MessageActions';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  isStreaming?: boolean;
}

interface UnifiedChatInterfaceProps {
  onMonitorPageUpdate?: (page: MonitorPage) => void;
  onStatusUpdate?: (status: AgentStatus) => void;
}

export const UnifiedChatInterface: React.FC<UnifiedChatInterfaceProps> = ({
  onMonitorPageUpdate,
  onStatusUpdate
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Initialize WebSocket connection and event listeners
  useEffect(() => {
    // Socket event listeners
    const handleSocketConnected = () => {
      setConnectionStatus('connected');
      console.log('Socket connected');
    };

    const handleSocketDisconnected = () => {
      setConnectionStatus('disconnected');
      console.log('Socket disconnected');
    };

    const handleNewMonitorPage = (page: MonitorPage) => {
      console.log('New monitor page received:', page);
      onMonitorPageUpdate?.(page);
    };

    const handleMonitoringReady = () => {
      console.log('Monitoring ready');
      loadInitialStatus();
    };

    // Register event listeners
    unifiedAPI.on('socket_connected', handleSocketConnected);
    unifiedAPI.on('socket_disconnected', handleSocketDisconnected);
    unifiedAPI.on('new_monitor_page', handleNewMonitorPage);
    unifiedAPI.on('monitoring_ready', handleMonitoringReady);

    // Initial status load
    loadInitialStatus();

    // Cleanup
    return () => {
      unifiedAPI.off('socket_connected', handleSocketConnected);
      unifiedAPI.off('socket_disconnected', handleSocketDisconnected);
      unifiedAPI.off('new_monitor_page', handleNewMonitorPage);
      unifiedAPI.off('monitoring_ready', handleMonitoringReady);
    };
  }, [onMonitorPageUpdate]);

  const loadInitialStatus = async () => {
    try {
      const status = await unifiedAPI.getStatus();
      setAgentStatus(status);
      onStatusUpdate?.(status);
    } catch (error) {
      console.error('Error loading initial status:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setIsThinking(true);

    try {
      const response: ChatResponse = await unifiedAPI.sendMessage(userMessage.content, sessionId);
      
      // Update session ID if provided
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }

      // Create agent response message
      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        sender: 'agent',
        timestamp: new Date(response.timestamp)
      };

      setMessages(prev => [...prev, agentMessage]);

      // Update status
      const updatedStatus = await unifiedAPI.getStatus();
      setAgentStatus(updatedStatus);
      onStatusUpdate?.(updatedStatus);

    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        sender: 'agent',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsThinking(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'disconnected':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Conectado';
      case 'disconnected':
        return 'Desconectado';
      default:
        return 'Conectando...';
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header with status */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Bot className="w-6 h-6 text-blue-400" />
            <h1 className="text-xl font-bold text-white">Mitosis Unificado</h1>
          </div>
          <div className="flex items-center space-x-2 text-sm">
            {getConnectionStatusIcon()}
            <span className="text-gray-300">{getConnectionStatusText()}</span>
          </div>
        </div>
        
        {agentStatus && (
          <div className="flex items-center space-x-4 text-sm text-gray-300">
            <div className="flex items-center space-x-1">
              <Terminal className="w-4 h-4" />
              <span>Estado: {agentStatus.state}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Zap className="w-4 h-4" />
              <span>Modelos: {agentStatus.available_models.length}</span>
            </div>
          </div>
        )}
      </div>

      {/* Chat messages */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 && (
          <div className="text-center py-12">
            <Bot className="w-16 h-16 text-blue-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">¡Bienvenido a Mitosis Unificado!</h2>
            <p className="text-gray-400 max-w-md mx-auto">
              Un agente de IA general con capacidades avanzadas de procesamiento, memoria y ejecución de tareas.
              Escribe tu mensaje para comenzar.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                message.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-100'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.sender === 'agent' && (
                  <Bot className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
                )}
                <div className="flex-1">
                  <div className="whitespace-pre-wrap break-words">
                    {message.content}
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs opacity-70">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.sender === 'agent' && (
                      <MessageActions 
                        content={message.content}
                        onCopy={() => navigator.clipboard.writeText(message.content)}
                      />
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}

        {isThinking && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg p-4 bg-gray-700">
              <div className="flex items-center space-x-2">
                <Bot className="w-5 h-5 text-blue-400" />
                <ThinkingAnimation />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-4 border-t border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="flex items-center space-x-2">
          <div className="flex-1">
            <VanishInput
              value={inputValue}
              onChange={setInputValue}
              onKeyPress={handleKeyPress}
              placeholder="Escribe tu mensaje aquí..."
              disabled={isLoading || connectionStatus === 'disconnected'}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading || connectionStatus === 'disconnected'}
            className={`p-3 rounded-lg transition-all duration-200 ${
              !inputValue.trim() || isLoading || connectionStatus === 'disconnected'
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 hover:scale-105'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        
        {connectionStatus === 'disconnected' && (
          <div className="mt-2 text-center text-sm text-red-400">
            Conexión perdida. Intentando reconectar...
          </div>
        )}
      </div>
    </div>
  );
};

export default UnifiedChatInterface;

