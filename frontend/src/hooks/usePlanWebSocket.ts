/**
 * WebSocket Hook Específico para Plan de Acción
 * REFACTORIZADO: Maneja ÚNICAMENTE eventos relacionados al plan
 * Elimina duplicación y usa el nuevo usePlanReducer
 */

import { useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import { usePlanReducer } from './usePlanReducer';
import { TaskStep } from '../types';

interface PlanWebSocketHookProps {
  taskId: string;
  initialPlan?: TaskStep[];
  onPlanUpdate?: (plan: TaskStep[]) => void;
  onStepComplete?: (stepId: string) => void;
  onTaskComplete?: () => void;
}

export const usePlanWebSocket = ({
  taskId,
  initialPlan = [],
  onPlanUpdate,
  onStepComplete,
  onTaskComplete
}: PlanWebSocketHookProps) => {
  
  const {
    socket,
    isConnected,
    joinTaskRoom,
    leaveTaskRoom,
    addEventListeners,
    removeEventListeners
  } = useWebSocket();

  const {
    plan,
    progress,
    setPlan,
    startStep,
    completeStep,
    updateStep,
    isCompleted
  } = usePlanReducer(initialPlan);

  // ========================================================================
  // EFECTOS PARA WEBSOCKET
  // ========================================================================

  // Configurar WebSocket cuando el taskId cambia
  useEffect(() => {
    if (!taskId || !socket) return;

    joinTaskRoom(taskId);

    // UN SOLO SET DE EVENT HANDLERS - SIN DUPLICACIÓN
    const eventHandlers = {
      // Evento: Nuevo plan recibido del backend
      'plan_updated': (data: any) => {
        if (data.plan?.steps && Array.isArray(data.plan.steps)) {
          const newSteps = data.plan.steps.map((step: any) => ({
            id: step.id,
            title: step.title,
            description: step.description,
            tool: step.tool,
            status: step.status,
            estimated_time: step.estimated_time,
            completed: step.completed || false,
            active: step.active || false
          }));
          
          setPlan(newSteps);
          onPlanUpdate?.(newSteps);
        }
      },

      // Evento: Paso iniciado
      'step_started': (data: any) => {
        if (data.step_id) {
          startStep(data.step_id, data.timestamp);
        }
      },

      // Evento: Paso completado
      'step_completed': (data: any) => {
        if (data.step_id) {
          completeStep(data.step_id, data.result, data.timestamp);
          onStepComplete?.(data.step_id);
        }
      },

      // Evento: Progreso general de la tarea
      'task_progress': (data: any) => {
        if (data.step_id) {
          // Solo actualizar el step específico mencionado
          if (data.status === 'started' || data.activity) {
            startStep(data.step_id, data.timestamp);
          } else if (data.status === 'completed') {
            completeStep(data.step_id, data.result, data.timestamp);
            onStepComplete?.(data.step_id);
          }
        }
      },

      // Evento: Tarea completada
      'task_completed': (data: any) => {
        onTaskComplete?.();
      }
    };

    addEventListeners(eventHandlers);

    return () => {
      removeEventListeners();
      leaveTaskRoom(taskId);
    };
  }, [taskId, socket, joinTaskRoom, leaveTaskRoom, addEventListeners, removeEventListeners, setPlan, startStep, completeStep, onPlanUpdate, onStepComplete, onTaskComplete]);

  // Efecto para notificar cuando el plan se completa
  useEffect(() => {
    if (isCompleted()) {
      onTaskComplete?.();
    }
  }, [isCompleted, onTaskComplete]);

  // ========================================================================
  // FUNCIONES PÚBLICAS
  // ========================================================================

  const updatePlanFromTask = useCallback((taskPlan: TaskStep[]) => {
    setPlan(taskPlan);
  }, [setPlan]);

  return {
    // Estado del plan
    plan,
    progress,
    isConnected,
    
    // Funciones para control manual
    updatePlanFromTask,
    startStep,
    completeStep,
    updateStep
  };
};