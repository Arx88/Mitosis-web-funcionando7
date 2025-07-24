/**
 * Hook personalizado para manejar comunicación en tiempo real con el backend
 * SOLUCIÓN HTTP POLLING - Reemplaza WebSocket completamente para evitar "server error"
 */

import { useEffect, useRef, useState } from 'react';

interface HttpPollingEvents {
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
  socket: null; // No socket - usar HTTP polling
  isConnected: boolean;
  joinTaskRoom: (taskId: string) => void;
  leaveTaskRoom: (taskId: string) => void;
  addEventListeners: (events: Partial<HttpPollingEvents>) => void;
  removeEventListeners: () => void;
}

export const useWebSocket = (): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const eventListenersRef = useRef<Partial<HttpPollingEvents>>({});
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Obtener URL del backend
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                    import.meta.env.REACT_APP_BACKEND_URL || 
                    process.env.REACT_APP_BACKEND_URL ||
                    'http://localhost:8001';

  const startPolling = (taskId: string) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    console.log('🔄 Starting HTTP polling for task:', taskId);
    setIsConnected(true);

    pollingIntervalRef.current = setInterval(async () => {
      try {
        // Polling endpoint para obtener actualizaciones de tarea
        const response = await fetch(`${backendUrl}/api/agent/get-task-status/${taskId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          
          // Simular eventos WebSocket basados en el status de la tarea
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

          // Polling de progreso de steps
          if (data.plan && Array.isArray(data.plan)) {
            data.plan.forEach((step: any) => {
              if (step.status === 'completed' && eventListenersRef.current.step_completed) {
                console.log('✅ Step completed:', step);
                eventListenersRef.current.step_completed(step);
              } else if (step.status === 'in_progress' && eventListenersRef.current.step_started) {
                console.log('🔧 Step started:', step);
                eventListenersRef.current.step_started(step);
              }
            });
          }
        }
      } catch (error) {
        console.error('❌ HTTP Polling error:', error);
        // No desconectar por un error, seguir intentando
      }
    }, 2000); // Polling cada 2 segundos
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsConnected(false);
    console.log('⏹️ HTTP polling stopped');
  };

  useEffect(() => {
    // Simular conexión exitosa
    console.log('✅ HTTP Polling connection established (no WebSocket)');
    
    // Cleanup al desmontar
    return () => {
      stopPolling();
    };
  }, []);

  const joinTaskRoom = (taskId: string) => {
    console.log('🏠 Joining task room (HTTP Polling):', taskId);
    setCurrentTaskId(taskId);
    startPolling(taskId);
  };

  const leaveTaskRoom = (taskId: string) => {
    console.log('🚪 Leaving task room (HTTP Polling):', taskId);
    setCurrentTaskId(null);
    stopPolling();
  };

  const addEventListeners = (events: Partial<HttpPollingEvents>) => {
    console.log('📡 Adding HTTP polling event listeners');
    eventListenersRef.current = events;
  };

  const removeEventListeners = () => {
    console.log('🗑️ Removing HTTP polling event listeners');
    eventListenersRef.current = {};
  };

  return {
    socket: null, // No socket - usando HTTP polling
    isConnected,
    joinTaskRoom,
    leaveTaskRoom,
    addEventListeners,
    removeEventListeners,
  };
};