/**
 * HOOK ÚNICO Y SIMPLIFICADO PARA PLAN DE ACCIÓN
 * Refactorización completa - elimina duplicación y complejidad
 * UN SOLO lugar para manejar el estado del plan
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { TaskStep } from '../types';

interface PlanManagerProps {
  taskId: string;
  initialPlan?: TaskStep[];
  onPlanUpdate?: (plan: TaskStep[]) => void;
  onStepComplete?: (stepId: string) => void;
  onTaskComplete?: () => void;
}

export const usePlanManager = ({
  taskId,
  initialPlan = [],
  onPlanUpdate,
  onStepComplete,
  onTaskComplete
}: PlanManagerProps) => {
  
  // ========================================================================
  // ESTADO ÚNICO Y SIMPLE
  // ========================================================================
  
  const [steps, setSteps] = useState<TaskStep[]>(initialPlan);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date());
  
  // WebSocket connection
  const { socket, isConnected, joinTaskRoom, leaveTaskRoom } = useWebSocket();
  
  // Ref para evitar loops
  const isUpdatingRef = useRef(false);

  // ========================================================================
  // FUNCIÓN PRINCIPAL: ACTUALIZAR PLAN - SIMPLE Y DIRECTO
  // ========================================================================
  
  const updatePlan = useCallback((newSteps: TaskStep[], source: string = 'internal') => {
    if (isUpdatingRef.current) {
      console.log(`🔄 [PLAN-${taskId}] Update skipped (already updating) from: ${source}`);
      return;
    }

    isUpdatingRef.current = true;
    
    console.log(`🎯 [PLAN-${taskId}] Updating plan from: ${source}`, {
      totalSteps: newSteps.length,
      activeSteps: newSteps.filter(s => s.active).length,
      completedSteps: newSteps.filter(s => s.completed).length
    });

    // VALIDACIÓN CRÍTICA: Solo un step puede estar activo
    let activeStepFound = false;
    const validatedSteps = newSteps.map(step => {
      if (step.active && !activeStepFound && !step.completed) {
        activeStepFound = true;
        return step; // Este es el único activo válido
      } else if (step.active) {
        // Desactivar steps duplicados o completados que estén activos
        return { ...step, active: false };
      }
      return step;
    });

    // Actualizar estado
    setSteps(validatedSteps);
    setLastUpdateTime(new Date());
    
    // Callbacks
    onPlanUpdate?.(validatedSteps);
    
    // Verificar si la tarea está completa
    const completedSteps = validatedSteps.filter(s => s.completed).length;
    const totalSteps = validatedSteps.length;
    
    if (totalSteps > 0 && completedSteps === totalSteps) {
      console.log(`🎉 [PLAN-${taskId}] Task completed!`);
      onTaskComplete?.();
    }

    isUpdatingRef.current = false;
  }, [taskId, onPlanUpdate, onTaskComplete]);

  // ========================================================================
  // LÓGICA SIMPLE: COMPLETAR PASO Y ACTIVAR EL SIGUIENTE
  // ========================================================================

  const completeStep = useCallback((stepId: string) => {
    console.log(`✅ [PLAN-${taskId}] Completing step: ${stepId}`);
    
    setSteps(prevSteps => {
      const stepIndex = prevSteps.findIndex(s => s.id === stepId);
      if (stepIndex === -1) {
        console.warn(`⚠️ [PLAN-${taskId}] Step not found: ${stepId}`);
        return prevSteps;
      }

      const newSteps = [...prevSteps];
      
      // 1. Completar el step actual
      newSteps[stepIndex] = {
        ...newSteps[stepIndex],
        active: false,
        completed: true,
        status: 'completed'
      };

      // 2. Activar el siguiente step automáticamente (LÓGICA SIMPLE)
      const nextStepIndex = stepIndex + 1;
      if (nextStepIndex < newSteps.length && !newSteps[nextStepIndex].completed) {
        console.log(`▶️ [PLAN-${taskId}] Auto-activating next step: ${newSteps[nextStepIndex].id}`);
        newSteps[nextStepIndex] = {
          ...newSteps[nextStepIndex],
          active: true,
          start_time: new Date()
        };
      }

      // Actualizar usando la función principal
      setTimeout(() => {
        updatePlan(newSteps, 'completeStep');
        onStepComplete?.(stepId);
      }, 0);
      
      return newSteps;
    });
  }, [taskId, updatePlan, onStepComplete]);

  const startStep = useCallback((stepId: string) => {
    console.log(`▶️ [PLAN-${taskId}] Starting step: ${stepId}`);
    
    setSteps(prevSteps => {
      const newSteps = prevSteps.map(step => ({
        ...step,
        active: step.id === stepId && !step.completed,
        start_time: step.id === stepId ? new Date() : step.start_time
      }));
      
      setTimeout(() => {
        updatePlan(newSteps, 'startStep');
      }, 0);
      
      return newSteps;
    });
  }, [taskId, updatePlan]);

  const setPlan = useCallback((newPlan: TaskStep[]) => {
    console.log(`📋 [PLAN-${taskId}] Setting new plan with ${newPlan.length} steps`);
    updatePlan(newPlan, 'setPlan');
  }, [taskId, updatePlan]);

  // ========================================================================
  // WEBSOCKET EVENTS - SIMPLIFICADO
  // ========================================================================

  useEffect(() => {
    if (!socket || !taskId) return;

    console.log(`🔌 [PLAN-${taskId}] Setting up WebSocket listeners`);
    joinTaskRoom(taskId);

    const handlePlanUpdated = (data: any) => {
      if (data.task_id !== taskId) return; // Filtro de seguridad
      
      console.log(`📡 [PLAN-${taskId}] WebSocket plan_updated:`, data);
      if (data.plan?.steps && Array.isArray(data.plan.steps)) {
        const newSteps = data.plan.steps.map((step: any) => ({
          id: step.id,
          title: step.title,
          description: step.description,
          tool: step.tool,
          status: step.status,
          estimated_time: step.estimated_time,
          completed: Boolean(step.completed),
          active: Boolean(step.active),
          start_time: step.start_time ? new Date(step.start_time) : undefined
        }));
        updatePlan(newSteps, 'websocket-plan_updated');
      }
    };

    const handleStepStarted = (data: any) => {
      if (data.task_id !== taskId) return; // Filtro de seguridad
      
      console.log(`📡 [PLAN-${taskId}] WebSocket step_started:`, data);
      if (data.step_id) {
        startStep(data.step_id);
      }
    };

    const handleStepCompleted = (data: any) => {
      if (data.task_id !== taskId) return; // Filtro de seguridad
      
      console.log(`📡 [PLAN-${taskId}] WebSocket step_completed:`, data);
      if (data.step_id) {
        completeStep(data.step_id);
      }
    };

    const handleTaskProgress = (data: any) => {
      if (data.task_id !== taskId) return; // Filtro de seguridad
      
      console.log(`📡 [PLAN-${taskId}] WebSocket task_progress:`, data);
      if (data.step_id) {
        if (data.status === 'started') {
          startStep(data.step_id);
        } else if (data.status === 'completed') {
          completeStep(data.step_id);
        }
      }
    };

    // Registrar event listeners
    socket.on('plan_updated', handlePlanUpdated);
    socket.on('step_started', handleStepStarted);
    socket.on('step_completed', handleStepCompleted);
    socket.on('task_progress', handleTaskProgress);

    return () => {
      console.log(`🔌 [PLAN-${taskId}] Cleaning up WebSocket listeners`);
      socket.off('plan_updated', handlePlanUpdated);
      socket.off('step_started', handleStepStarted);
      socket.off('step_completed', handleStepCompleted);
      socket.off('task_progress', handleTaskProgress);
      leaveTaskRoom(taskId);
    };
  }, [socket, taskId, joinTaskRoom, leaveTaskRoom, startStep, completeStep, updatePlan]);

  // ========================================================================
  // INICIALIZACIÓN CON PLAN INICIAL
  // ========================================================================

  useEffect(() => {
    if (initialPlan.length > 0 && steps.length === 0) {
      console.log(`🚀 [PLAN-${taskId}] Initializing with plan:`, initialPlan.length, 'steps');
      setPlan(initialPlan);
    }
  }, [initialPlan, steps.length, taskId, setPlan]);

  // ========================================================================
  // API PÚBLICA SIMPLE
  // ========================================================================

  // Valores computados
  const currentActiveStep = steps.find(s => s.active) || null;
  const currentActiveStepId = currentActiveStep?.id || null;
  const completedSteps = steps.filter(s => s.completed).length;
  const totalSteps = steps.length;
  const progress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
  const isCompleted = completedSteps === totalSteps && totalSteps > 0;

  return {
    // Estado del plan
    plan: steps,
    currentActiveStep,
    currentActiveStepId,
    progress,
    isCompleted,
    isConnected,
    lastUpdateTime,
    
    // Funciones de control
    setPlan,
    startStep,
    completeStep,
    
    // Estado computado
    totalSteps,
    completedSteps
  };
};