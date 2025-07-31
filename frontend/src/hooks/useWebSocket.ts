/**
 * Hook personalizado para manejar comunicación WebSocket real en tiempo real
 * SOLUCIÓN WEBSOCKET REAL - Reemplaza HTTP Polling con conexión WebSocket auténtica
 * Incluye fallback automático a HTTP Polling si WebSocket falla
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { API_CONFIG, getWebSocketConfig } from '../config/api';

interface WebSocketEvents {
  task_started: (data: any) => void;
  task_progress: (data: any) => void;
  task_completed: (data: any) => void;
  task_failed: (data: any) => void;
  step_started: (data: any) => void;
  step_completed: (data: any) => void;
  step_failed: (data: any) => void;
  step_needs_more_work: (data: any) => void;
  plan_updated: (data: any) => void;
  tool_result: (data: any) => void;
  context_changed: (data: any) => void;
  error: (data: any) => void;
}

interface UseWebSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  connectionType: 'websocket' | 'polling' | 'disconnected';
  joinTaskRoom: (taskId: string) => void;
  leaveTaskRoom: (taskId: string) => void;
  addEventListeners: (events: Partial<WebSocketEvents>) => void;
  removeEventListeners: () => void;
}

export const useWebSocket = (): UseWebSocketReturn => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionType, setConnectionType] = useState<'websocket' | 'polling' | 'disconnected'>('disconnected');
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const eventListenersRef = useRef<Partial<WebSocketEvents>>({});
  
  // Fallback HTTP Polling (mantener por si WebSocket falla)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [isPollingFallback, setIsPollingFallback] = useState(false);

  useEffect(() => {
    console.log('🔌 Initializing WebSocket connection...');
    const wsConfig = getWebSocketConfig();
    
    console.log('🔧 WebSocket URL:', wsConfig.url);
    console.log('🔧 WebSocket Options:', wsConfig.options);
    
    const newSocket = io(wsConfig.url, {
      ...wsConfig.options,
      forceNew: true
    });
    
    newSocket.on('connect', () => {
      console.log('✅ WebSocket connected successfully!');
      console.log('🔧 Transport:', newSocket.io.engine.transport.name);
      console.log('🆔 Session ID:', newSocket.id);
      setIsConnected(true);
      setConnectionType(newSocket.io.engine.transport.name as 'websocket' | 'polling');
      setIsPollingFallback(false);
    });
    
    newSocket.on('disconnect', () => {
      console.log('🔌 WebSocket disconnected');
      setIsConnected(false);
      setConnectionType('disconnected');
    });
    
    newSocket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error);
      console.error('❌ Error details:', error.message, error.type);
      setIsConnected(false);
      setConnectionType('disconnected');
      
      // CRÍTICO: Activar HTTP polling automáticamente cuando WebSocket falla
      console.log('🔄 WebSocket failed, activating HTTP polling fallback...');
      setIsPollingFallback(true);
      
      // Si hay una tarea activa, iniciar polling inmediatamente
      if (currentTaskId) {
        console.log('🔄 Starting HTTP polling for current task:', currentTaskId);
        startHttpPollingFallback(currentTaskId);
      }
    });
    
    // Listen for backend connection confirmation
    newSocket.on('connection_established', (data) => {
      console.log('🎉 Backend confirmed connection:', data);
    });
    
    setSocket(newSocket);
    
    // Cleanup on unmount
    return () => {
      console.log('🧹 Cleaning up WebSocket connection');
      newSocket.close();
      
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);

  // HTTP Polling fallback implementation
  const startHttpPollingFallback = useCallback((taskId: string) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    console.log('🔄 HTTP Polling fallback active for task:', taskId);
    
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`${API_CONFIG.backend.url}/api/agent/get-task-status/${taskId}`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        });

        if (response.ok) {
          const data = await response.json();
          
          // Simulate WebSocket events based on task status
          if (data.status && eventListenersRef.current) {
            switch (data.status) {
              case 'plan_generated':
                eventListenersRef.current.task_started?.(data);
                break;
              case 'executing':
                eventListenersRef.current.task_progress?.(data);
                break;
              case 'completed':
                eventListenersRef.current.task_completed?.(data);
                break;
              case 'failed':
                eventListenersRef.current.task_failed?.(data);
                break;
            }
          }

          // Handle step progress
          if (data.plan && Array.isArray(data.plan)) {
            data.plan.forEach((step: any) => {
              if (step.status === 'completed' && eventListenersRef.current.step_completed) {
                eventListenersRef.current.step_completed(step);
              } else if (step.status === 'in_progress' && eventListenersRef.current.step_started) {
                eventListenersRef.current.step_started(step);
              }
            });
          }
        }
      } catch (error) {
        console.error('❌ HTTP Polling fallback error:', error);
      }
    }, 3000); // Poll every 3 seconds (slower than original 2s to reduce load)
  }, [eventListenersRef.current]);

  const joinTaskRoom = useCallback((taskId: string) => {
    setCurrentTaskId(taskId);
    
    if (socket && isConnected) {
      socket.emit('join_task', { task_id: taskId });
    } else {
      // Start polling fallback if WebSocket not available
      startHttpPollingFallback(taskId);
      setIsPollingFallback(true);
    }
  }, [socket, isConnected, startHttpPollingFallback]);

  const leaveTaskRoom = useCallback((taskId: string) => {
    setCurrentTaskId(null);
    
    if (socket) {
      socket.emit('leave_task', { task_id: taskId });
    }
    
    // Stop HTTP Polling fallback
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
    setIsPollingFallback(false);
  }, [socket]);

  const addEventListeners = useCallback((events: Partial<WebSocketEvents>) => {
    console.log('📡 Adding WebSocket/Polling event listeners');
    eventListenersRef.current = { ...eventListenersRef.current, ...events };
  }, []);

  const removeEventListeners = useCallback(() => {
    console.log('🗑️ Removing WebSocket/Polling event listeners');
    eventListenersRef.current = {};
  }, []);

  return {
    socket,
    isConnected,
    connectionType,
    joinTaskRoom,
    leaveTaskRoom,
    addEventListeners,
    removeEventListeners,
  };
};