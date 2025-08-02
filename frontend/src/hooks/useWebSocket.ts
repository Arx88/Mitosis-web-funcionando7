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
  // ✅ NUEVOS EVENTOS PARA VISUALIZACIÓN EN TIEMPO REAL - SEGÚN UpgardeRef.md SECCIÓN 5.3
  browser_activity: (data: any) => void;
  data_collection_update: (data: any) => void;
  report_progress: (data: any) => void;
  log_message: (data: any) => void;
  // Eventos genéricos que el backend podría emitir
  task_update: (data: any) => void;
  progress_update: (data: any) => void;
  agent_activity: (data: any) => void;
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
    const wsConfig = getWebSocketConfig();
    
    console.log('🔌 Initializing WebSocket connection:', wsConfig);
    
    const newSocket = io(wsConfig.url, {
      ...wsConfig.options
    });
    
    newSocket.on('connect', () => {
      console.log('✅ WebSocket connected successfully');
      setIsConnected(true);
      setConnectionType(newSocket.io.engine.transport.name as 'websocket' | 'polling');
      setIsPollingFallback(false);
    });
    
    newSocket.on('disconnect', (reason) => {
      console.log('❌ WebSocket disconnected:', reason);
      setIsConnected(false);
      setConnectionType('disconnected');
    });
    
    newSocket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error);
      setIsConnected(false);
      setConnectionType('disconnected');
      
      // Activar HTTP polling automáticamente cuando WebSocket falla
      setIsPollingFallback(true);
      
      if (currentTaskId) {
        startHttpPollingFallback(currentTaskId);
      }
    });
    
    setSocket(newSocket);
    
    // Cleanup on unmount
    return () => {
      console.log('🔌 Cleaning up WebSocket connection');
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
    
    console.log(`🔄 Starting HTTP polling fallback for task: ${taskId}`);
    
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`${API_CONFIG.backend.url}/api/agent/get-task-status/${taskId}`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        });

        if (response.ok) {
          const data = await response.json();
          
          // ✅ CRITICAL FIX: Stop polling for completed/failed tasks
          if (data.status === 'completed' || data.status === 'failed') {
            console.log(`🏁 Task ${taskId} is ${data.status}, stopping HTTP polling`);
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            setIsPollingFallback(false);
            
            // Send final event and stop
            if (eventListenersRef.current) {
              if (data.status === 'completed') {
                eventListenersRef.current.task_completed?.(data);
              } else {
                eventListenersRef.current.task_failed?.(data);
              }
            }
            return; // Exit interval
          }
          
          // Only process active task status updates
          if (data.status && eventListenersRef.current) {
            switch (data.status) {
              case 'plan_generated':
                eventListenersRef.current.task_started?.(data);
                break;
              case 'executing':
              case 'in_progress':
                eventListenersRef.current.task_progress?.(data);
                break;
            }
          }

          // Handle step progress only for active tasks
          if (data.plan && Array.isArray(data.plan)) {
            data.plan.forEach((step: any) => {
              if (step.status === 'completed' && eventListenersRef.current.step_completed) {
                eventListenersRef.current.step_completed(step);
              } else if (step.status === 'in_progress' && eventListenersRef.current.step_started) {
                eventListenersRef.current.step_started(step);
              }
            });
          }
        } else {
          console.warn(`HTTP Polling: Failed to fetch task ${taskId} status`);
        }
      } catch (error) {
        console.error('HTTP Polling fallback error:', error);
        // Stop polling on persistent errors
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        setIsPollingFallback(false);
      }
    }, 5000); // ✅ Increased interval to 5 seconds to reduce server load
  }, []);

  const joinTaskRoom = useCallback((taskId: string) => {
    // ✅ CRITICAL FIX: Prevent multiple polling for the same task
    if (currentTaskId === taskId) {
      console.log(`⚠️ Already connected to task: ${taskId}, skipping join`);
      return;
    }
    
    // Clean up previous task connection
    if (currentTaskId) {
      console.log(`🔄 Switching from task ${currentTaskId} to ${taskId}`);
      // Stop previous polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
    
    setCurrentTaskId(taskId);
    
    console.log(`🎯 Joining task room: ${taskId}`);
    
    if (socket && isConnected) {
      socket.emit('join_task', { task_id: taskId });
      console.log(`✅ WebSocket join_task emitted for: ${taskId}`);
    } else {
      // Start polling fallback if WebSocket not available
      console.log(`🔄 WebSocket not available, starting HTTP polling for: ${taskId}`);
      startHttpPollingFallback(taskId);
      setIsPollingFallback(true);
    }
  }, [socket, isConnected, startHttpPollingFallback, currentTaskId]);

  const leaveTaskRoom = useCallback((taskId: string) => {
    setCurrentTaskId(null);
    
    console.log(`🚪 Leaving task room: ${taskId}`);
    
    if (socket) {
      socket.emit('leave_task', { task_id: taskId });
    }
    
    // ✅ CRITICAL FIX: Always stop HTTP Polling when leaving task
    if (pollingIntervalRef.current) {
      console.log(`🛑 Stopping HTTP polling for task: ${taskId}`);
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
    setIsPollingFallback(false);
  }, [socket]);

  const addEventListeners = useCallback((events: Partial<WebSocketEvents>) => {
    eventListenersRef.current = { ...eventListenersRef.current, ...events };
    
    // Agregar los listeners al socket si está conectado
    if (socket && isConnected) {
      Object.entries(events).forEach(([eventName, handler]) => {
        if (handler) {
          socket.on(eventName, handler);
        }
      });
    }
  }, [socket, isConnected]);

  const removeEventListeners = useCallback(() => {
    if (socket) {
      // Remover todos los listeners actuales
      Object.keys(eventListenersRef.current).forEach((eventName) => {
        socket.off(eventName);
      });
    }
    eventListenersRef.current = {};
  }, [socket]);

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