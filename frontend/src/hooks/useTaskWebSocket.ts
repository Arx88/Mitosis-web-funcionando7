/**
 * WEBSOCKET AISLADO POR TAREA
 * Cada TaskView tiene su propia conexión WebSocket completamente aislada
 * SOLUCIÓN AL PROBLEMA DE CONTAMINACIÓN ENTRE TAREAS
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { API_CONFIG, getWebSocketConfig } from '../config/api';

interface TaskWebSocketProps {
  taskId: string;
  onTaskProgress?: (data: any) => void;
  onStepStarted?: (data: any) => void;
  onStepCompleted?: (data: any) => void;
  onPlanUpdated?: (data: any) => void;
  onToolResult?: (data: any) => void;
  onError?: (data: any) => void;
}

interface UseTaskWebSocketReturn {
  isConnected: boolean;
  connectionType: 'websocket' | 'polling' | 'disconnected';
  sendMessage: (event: string, data: any) => void;
  disconnect: () => void;
}

export const useTaskWebSocket = ({
  taskId,
  onTaskProgress,
  onStepStarted,
  onStepCompleted,
  onPlanUpdated,
  onToolResult,
  onError
}: TaskWebSocketProps): UseTaskWebSocketReturn => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionType, setConnectionType] = useState<'websocket' | 'polling' | 'disconnected'>('disconnected');
  
  // Refs para mantener referencias estables
  const taskIdRef = useRef(taskId);
  const cleanupRef = useRef<(() => void) | null>(null);

  // ========================================================================
  // INICIALIZACIÓN DE WEBSOCKET ESPECÍFICO PARA ESTA TAREA
  // ========================================================================

  useEffect(() => {
    taskIdRef.current = taskId;
    
    if (!taskId) {
      console.warn(`⚠️ [WS-${taskId}] Cannot initialize WebSocket without taskId`);
      return;
    }

    console.log(`🔌 [WS-${taskId}] Initializing WebSocket connection`);
    
    const wsConfig = getWebSocketConfig();
    
    // Crear socket específico para esta tarea
    const taskSocket = io(wsConfig.url, {
      ...wsConfig.options,
      forceNew: true,
      query: { task_id: taskId } // Importante: incluir taskId en la conexión
    });

    // ========================================================================
    // EVENT HANDLERS DE CONEXIÓN
    // ========================================================================

    taskSocket.on('connect', () => {
      console.log(`✅ [WS-${taskId}] Connected to WebSocket`);
      setIsConnected(true);
      setConnectionType(taskSocket.io.engine.transport.name as 'websocket' | 'polling');
      
      // Unirse al room específico de esta tarea
      taskSocket.emit('join_task', { task_id: taskId });
      console.log(`🏠 [WS-${taskId}] Joined task room`);
    });

    taskSocket.on('disconnect', () => {
      console.log(`❌ [WS-${taskId}] Disconnected from WebSocket`);
      setIsConnected(false);
      setConnectionType('disconnected');
    });

    taskSocket.on('connect_error', (error) => {
      console.error(`💥 [WS-${taskId}] Connection error:`, error);
      setIsConnected(false);
      setConnectionType('disconnected');
      onError?.({ type: 'connection_error', error: error.message });
    });

    // ========================================================================
    // EVENT HANDLERS ESPECÍFICOS DE TAREA - CON FILTRO DE SEGURIDAD
    // ========================================================================

    const handleTaskProgress = (data: any) => {
      // FILTRO CRÍTICO: Solo procesar si es para ESTA tarea
      if (data.task_id && data.task_id !== taskIdRef.current) {
        console.warn(`🛡️ [WS-${taskId}] Ignoring task_progress for different task: ${data.task_id}`);
        return;
      }
      
      console.log(`📈 [WS-${taskId}] Task progress received:`, data);
      onTaskProgress?.(data);
    };

    const handleStepStarted = (data: any) => {
      // FILTRO CRÍTICO: Solo procesar si es para ESTA tarea
      if (data.task_id && data.task_id !== taskIdRef.current) {
        console.warn(`🛡️ [WS-${taskId}] Ignoring step_started for different task: ${data.task_id}`);
        return;
      }
      
      console.log(`▶️ [WS-${taskId}] Step started:`, data);
      onStepStarted?.(data);
    };

    const handleStepCompleted = (data: any) => {
      // FILTRO CRÍTICO: Solo procesar si es para ESTA tarea
      if (data.task_id && data.task_id !== taskIdRef.current) {
        console.warn(`🛡️ [WS-${taskId}] Ignoring step_completed for different task: ${data.task_id}`);
        return;
      }
      
      console.log(`✅ [WS-${taskId}] Step completed:`, data);
      onStepCompleted?.(data);
    };

    const handlePlanUpdated = (data: any) => {
      // FILTRO CRÍTICO: Solo procesar si es para ESTA tarea
      if (data.task_id && data.task_id !== taskIdRef.current) {
        console.warn(`🛡️ [WS-${taskId}] Ignoring plan_updated for different task: ${data.task_id}`);
        return;
      }
      
      console.log(`📋 [WS-${taskId}] Plan updated:`, data);
      onPlanUpdated?.(data);
    };

    const handleToolResult = (data: any) => {
      // FILTRO CRÍTICO: Solo procesar si es para ESTA tarea
      if (data.task_id && data.task_id !== taskIdRef.current) {
        console.warn(`🛡️ [WS-${taskId}] Ignoring tool_result for different task: ${data.task_id}`);
        return;
      }
      
      console.log(`🔧 [WS-${taskId}] Tool result:`, data);
      onToolResult?.(data);
    };

    const handleError = (data: any) => {
      // FILTRO CRÍTICO: Solo procesar si es para ESTA tarea
      if (data.task_id && data.task_id !== taskIdRef.current) {
        console.warn(`🛡️ [WS-${taskId}] Ignoring error for different task: ${data.task_id}`);
        return;
      }
      
      console.error(`❌ [WS-${taskId}] WebSocket error:`, data);
      onError?.(data);
    };

    // ========================================================================
    // REGISTRAR EVENT LISTENERS
    // ========================================================================

    taskSocket.on('task_progress', handleTaskProgress);
    taskSocket.on('step_started', handleStepStarted);
    taskSocket.on('step_completed', handleStepCompleted);
    taskSocket.on('plan_updated', handlePlanUpdated);
    taskSocket.on('tool_result', handleToolResult);
    taskSocket.on('error', handleError);

    setSocket(taskSocket);

    // ========================================================================
    // CLEANUP FUNCTION
    // ========================================================================

    const cleanup = () => {
      console.log(`🧹 [WS-${taskId}] Cleaning up WebSocket connection`);
      
      // Remover todos los event listeners
      taskSocket.off('task_progress', handleTaskProgress);
      taskSocket.off('step_started', handleStepStarted);
      taskSocket.off('step_completed', handleStepCompleted);
      taskSocket.off('plan_updated', handlePlanUpdated);
      taskSocket.off('tool_result', handleToolResult);
      taskSocket.off('error', handleError);
      
      // Salir del room
      taskSocket.emit('leave_task', { task_id: taskId });
      
      // Desconectar socket
      taskSocket.close();
      
      setSocket(null);
      setIsConnected(false);
      setConnectionType('disconnected');
    };

    cleanupRef.current = cleanup;

    // Cleanup cuando el componente se desmonta
    return cleanup;
  }, [taskId, onTaskProgress, onStepStarted, onStepCompleted, onPlanUpdated, onToolResult, onError]);

  // ========================================================================
  // API PÚBLICA
  // ========================================================================

  const sendMessage = useCallback((event: string, data: any) => {
    if (socket && isConnected) {
      const messageData = {
        ...data,
        task_id: taskIdRef.current // Siempre incluir el taskId
      };
      
      console.log(`📤 [WS-${taskIdRef.current}] Sending message:`, event, messageData);
      socket.emit(event, messageData);
    } else {
      console.warn(`⚠️ [WS-${taskIdRef.current}] Cannot send message - not connected`);
    }
  }, [socket, isConnected]);

  const disconnect = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current();
    }
  }, []);

  return {
    isConnected,
    connectionType,
    sendMessage,
    disconnect
  };
};