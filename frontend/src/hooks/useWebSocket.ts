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
    
    const newSocket = io(wsConfig.url, wsConfig.options);
    
    // Connection event handlers
    newSocket.on('connect', () => {
      console.log('✅ WebSocket connected successfully');
      console.log('🔗 Transport:', newSocket.io.engine.transport.name);
      setIsConnected(true);
      setConnectionType(newSocket.io.engine.transport.name as 'websocket' | 'polling');
      setIsPollingFallback(false);
      
      // Stop HTTP polling fallback if it was running
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    });
    
    newSocket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error);
      setIsConnected(false);
      setConnectionType('disconnected');
      
      // Start HTTP Polling fallback after 3 failed attempts
      if (!isPollingFallback && currentTaskId) {
        console.log('🔄 Starting HTTP Polling fallback...');
        setIsPollingFallback(true);
        startHttpPollingFallback(currentTaskId);
      }
    });
    
    newSocket.on('disconnect', (reason) => {
      console.log('📡 WebSocket disconnected:', reason);
      setIsConnected(false);
      setConnectionType('disconnected');
      
      // Auto-reconnect unless manually disconnected
      if (reason === 'io server disconnect') {
        newSocket.connect();
      }
    });
    
    // Transport upgrade events
    newSocket.io.on('upgrade', () => {
      console.log('🚀 Transport upgraded to:', newSocket.io.engine.transport.name);
      setConnectionType(newSocket.io.engine.transport.name as 'websocket' | 'polling');
    });
    
    newSocket.io.on('upgradeError', (error) => {
      console.warn('⚠️ Transport upgrade failed:', error);
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
    console.log('🏠 Joining task room:', taskId);
    setCurrentTaskId(taskId);
    
    if (socket && isConnected) {
      socket.emit('join_task', { task_id: taskId });
      
      // Setup DIRECT WebSocket event listeners for backend events
      console.log('📡 Setting up direct WebSocket event listeners...');
      
      // Listen to specific events that backend emits
      socket.on('plan_updated', (data) => {
        console.log('📋 WebSocket plan_updated received:', data);
        if (eventListenersRef.current.plan_updated) {
          eventListenersRef.current.plan_updated(data);
        }
      });
      
      socket.on('step_started', (data) => {
        console.log('🚀 WebSocket step_started received:', data);
        if (eventListenersRef.current.step_started) {
          eventListenersRef.current.step_started(data);
        }
      });
      
      socket.on('task_progress', (data) => {
        console.log('🔄 WebSocket task_progress received:', data);
        if (eventListenersRef.current.task_progress) {
          eventListenersRef.current.task_progress(data);
        }
      });
      
      socket.on('tool_result', (data) => {
        console.log('🔧 WebSocket tool_result received:', data);
        if (eventListenersRef.current.tool_result) {
          eventListenersRef.current.tool_result(data);
        }
      });
      
      socket.on('step_needs_more_work', (data) => {
        console.log('⚠️ WebSocket step_needs_more_work received:', data);
        if (eventListenersRef.current.step_needs_more_work) {
          eventListenersRef.current.step_needs_more_work(data);
        }
      });
      
      socket.on('task_completed', (data) => {
        console.log('🎉 WebSocket task_completed received:', data);
        if (eventListenersRef.current.task_completed) {
          eventListenersRef.current.task_completed(data);
        }
      });
      
      socket.on('task_failed', (data) => {
        console.log('❌ WebSocket task_failed received:', data);
        if (eventListenersRef.current.task_failed) {
          eventListenersRef.current.task_failed(data);
        }
      });
      
    } else if (isPollingFallback) {
      // Use HTTP Polling fallback
      startHttpPollingFallback(taskId);
    }
  }, [socket, isConnected, isPollingFallback, startHttpPollingFallback]);

  const leaveTaskRoom = useCallback((taskId: string) => {
    console.log('🚪 Leaving task room:', taskId);
    setCurrentTaskId(null);
    
    if (socket) {
      socket.emit('leave_task', { task_id: taskId });
      
      // Remove ALL WebSocket event listeners
      socket.off('plan_updated');
      socket.off('step_started');
      socket.off('task_progress');
      socket.off('tool_result');
      socket.off('step_needs_more_work');
      socket.off('task_completed');
      socket.off('task_failed');
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