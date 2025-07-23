/**
 * Hook personalizado para manejar conexiones WebSocket con el backend
 * Gestiona eventos de tareas en tiempo real del ExecutionEngine
 */

import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface WebSocketEvents {
  task_started: (data: any) => void;
  task_progress: (data: any) => void;
  task_completed: (data: any) => void;
  task_failed: (data: any) => void;
  step_started: (data: any) => void;
  step_completed: (data: any) => void;
  step_failed: (data: any) => void;
  plan_updated: (data: any) => void;
  context_changed: (data: any) => void;
  error: (data: any) => void;
}

interface UseWebSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  joinTaskRoom: (taskId: string) => void;
  leaveTaskRoom: (taskId: string) => void;
  addEventListeners: (events: Partial<WebSocketEvents>) => void;
  removeEventListeners: () => void;
}

export const useWebSocket = (): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  const eventListenersRef = useRef<Partial<WebSocketEvents>>({});

  useEffect(() => {
    // Obtener URL del backend
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                      import.meta.env.REACT_APP_BACKEND_URL || 
                      process.env.REACT_APP_BACKEND_URL ||
                      'http://localhost:8001';

    console.log('🔌 Connecting to WebSocket:', backendUrl);

    // Crear conexión WebSocket
    socketRef.current = io(backendUrl, {
      transports: ['websocket', 'polling'],
      timeout: 10000,
      forceNew: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    const socket = socketRef.current;

    // Event listeners de conexión
    socket.on('connect', () => {
      console.log('✅ WebSocket connected:', socket.id);
      setIsConnected(true);
    });

    socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket disconnected:', reason);
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error);
      setIsConnected(false);
    });

    socket.on('reconnect', (attemptNumber) => {
      console.log('🔄 WebSocket reconnected after', attemptNumber, 'attempts');
      setIsConnected(true);
    });

    socket.on('reconnect_error', (error) => {
      console.error('❌ WebSocket reconnection error:', error);
    });

    // Cleanup al desmontar
    return () => {
      console.log('🧹 Cleaning up WebSocket connection');
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
      setIsConnected(false);
    };
  }, []);

  const joinTaskRoom = (taskId: string) => {
    if (socketRef.current && isConnected) {
      console.log('🏠 Joining task room:', taskId);
      socketRef.current.emit('join_task', { task_id: taskId });
    }
  };

  const leaveTaskRoom = (taskId: string) => {
    if (socketRef.current && isConnected) {
      console.log('🚪 Leaving task room:', taskId);
      socketRef.current.emit('leave_task', { task_id: taskId });
    }
  };

  const addEventListeners = (events: Partial<WebSocketEvents>) => {
    if (!socketRef.current) return;

    const socket = socketRef.current;
    eventListenersRef.current = events;

    // Agregar listeners para eventos de tareas
    if (events.task_started) {
      socket.on('task_started', (data) => {
        console.log('📋 Task started:', data);
        events.task_started?.(data);
      });
    }

    if (events.task_progress) {
      socket.on('task_progress', (data) => {
        console.log('⏳ Task progress:', data);
        events.task_progress?.(data);
      });
    }

    if (events.task_completed) {
      socket.on('task_completed', (data) => {
        console.log('✅ Task completed:', data);
        events.task_completed?.(data);
      });
    }

    if (events.task_failed) {
      socket.on('task_failed', (data) => {
        console.log('❌ Task failed:', data);
        events.task_failed?.(data);
      });
    }

    if (events.step_started) {
      socket.on('step_started', (data) => {
        console.log('🔧 Step started:', data);
        events.step_started?.(data);
      });
    }

    if (events.step_completed) {
      socket.on('step_completed', (data) => {
        console.log('✅ Step completed:', data);
        events.step_completed?.(data);
      });
    }

    if (events.step_failed) {
      socket.on('step_failed', (data) => {
        console.log('❌ Step failed:', data);
        events.step_failed?.(data);
      });
    }

    if (events.plan_updated) {
      socket.on('plan_updated', (data) => {
        console.log('📋 Plan updated:', data);
        events.plan_updated?.(data);
      });
    }

    if (events.context_changed) {
      socket.on('context_changed', (data) => {
        console.log('🔄 Context changed:', data);
        events.context_changed?.(data);
      });
    }
  };

  const removeEventListeners = () => {
    if (!socketRef.current) return;

    const socket = socketRef.current;
    const events = eventListenersRef.current;

    // Remover listeners
    if (events.task_started) socket.off('task_started');
    if (events.task_progress) socket.off('task_progress');
    if (events.task_completed) socket.off('task_completed');
    if (events.task_failed) socket.off('task_failed');
    if (events.plan_updated) socket.off('plan_updated');
    if (events.context_changed) socket.off('context_changed');

    eventListenersRef.current = {};
  };

  return {
    socket: socketRef.current,
    isConnected,
    joinTaskRoom,
    leaveTaskRoom,
    addEventListeners,
    removeEventListeners,
  };
};