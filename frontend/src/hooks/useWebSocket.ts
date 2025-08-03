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
  const eventListenersRef = useRef<Partial<WebSocketEvents>>({});
  const pendingRoomsRef = useRef<Set<string>>(new Set()); // ✅ TRACK PENDING ROOMS

  useEffect(() => {
    const wsConfig = getWebSocketConfig();
    
    console.log('🔌 Initializing WebSocket connection:', wsConfig);
    
    const newSocket = io(wsConfig.url, wsConfig.options);
    
    newSocket.on('connect', () => {
      console.log('✅ WebSocket connected successfully');
      setIsConnected(true);
      setConnectionType(newSocket.io.engine.transport.name as 'websocket' | 'polling');
      
      // ✅ AUTO-JOIN PENDING ROOMS
      const pendingRooms = Array.from(pendingRoomsRef.current);
      if (pendingRooms.length > 0) {
        console.log('🎯 Auto-joining pending rooms:', pendingRooms);
        pendingRooms.forEach(taskId => {
          newSocket.emit('join_task', { task_id: taskId });
          console.log('🔗 Auto-joined room:', taskId);
        });
      }
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
    });
    
    newSocket.on('connection_status', (data) => {
      console.log('📡 Connection status received:', data);
    });
    
    newSocket.on('joined_task', (data) => {
      console.log('✅ Successfully joined task room:', data);
      // Remove from pending once joined
      if (data.task_id) {
        pendingRoomsRef.current.delete(data.task_id);
      }
    });
    
    setSocket(newSocket);
    
    return () => {
      console.log('🧹 Cleaning up WebSocket connection');
      newSocket.disconnect();
    };
  }, []);

  const joinTaskRoom = useCallback((taskId: string) => {
    // ✅ ALWAYS ADD TO PENDING ROOMS FIRST
    pendingRoomsRef.current.add(taskId);
    
    if (socket && isConnected) {
      console.log('🔗 Joining task room immediately:', taskId);
      socket.emit('join_task', { task_id: taskId });
    } else {
      console.warn('⚠️ Socket not ready, added to pending rooms:', taskId);
    }
  }, [socket, isConnected]);

  const leaveTaskRoom = useCallback((taskId: string) => {
    if (socket && isConnected) {
      console.log('🔗 Leaving task room:', taskId);
      socket.emit('leave_task', { task_id: taskId });
    }
  }, [socket, isConnected]);

  const addEventListeners = useCallback((events: Partial<WebSocketEvents>) => {
    if (!socket) return;
    
    console.log('📝 Adding event listeners:', Object.keys(events));
    eventListenersRef.current = { ...eventListenersRef.current, ...events };
    
    Object.entries(events).forEach(([eventName, handler]) => {
      if (handler) {
        socket.on(eventName, handler);
      }
    });
  }, [socket]);

  const removeEventListeners = useCallback(() => {
    if (!socket) return;
    
    console.log('🧹 Removing event listeners');
    Object.keys(eventListenersRef.current).forEach(eventName => {
      socket.off(eventName);
    });
    eventListenersRef.current = {};
  }, [socket]);

  return {
    socket,
    isConnected,
    connectionType,
    joinTaskRoom,
    leaveTaskRoom,
    addEventListeners,
    removeEventListeners
  };
};