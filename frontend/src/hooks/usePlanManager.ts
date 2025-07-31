/**
 * HOOK SIMPLIFICADO PARA PLAN DE ACCIÓN
 * Refactorización completa - UN SOLO lugar para manejar el estado del plan
 * Elimina duplicación y race conditions
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

interface PlanState {
  steps: TaskStep[];
  currentActiveStepId: string | null;
  progress: number;
  isCompleted: boolean;
}

export const usePlanManager = ({
  taskId,
  initialPlan = [],
  onPlanUpdate,
  onStepComplete,
  onTaskComplete
}: PlanManagerProps) => {
  
  // Estado consolidado del plan
  const [planState, setPlanState] = useState<PlanState>({
    steps: initialPlan,
    currentActiveStepId: null,
    progress: 0,
    isCompleted: false
  });

  // WebSocket connection
  const { socket, isConnected, joinTaskRoom, leaveTaskRoom } = useWebSocket();
  
  // Ref para evitar loops en effects
  const isUpdatingRef = useRef(false);
  const lastUpdateRef = useRef<string>('');

  // ========================================================================
  // FUNCIÓN PRINCIPAL: ACTUALIZAR ESTADO DEL PLAN
  // ========================================================================
  
  const updatePlanState = useCallback((newSteps: TaskStep[], source: string = 'internal') => {
    // Evitar updates redundantes
    const stepsString = JSON.stringify(newSteps.map(s => ({ id: s.id, active: s.active, completed: s.completed })));
    if (lastUpdateRef.current === stepsString) {
      return;
    }
    lastUpdateRef.current = stepsString;

    if (isUpdatingRef.current) {
      console.log(`🔄 [PLAN-${taskId}] Update skipped (already updating) from: ${source}`);
      return;
    }

    isUpdatingRef.current = true;
    console.log(`🎯 [PLAN-${taskId}] Updating plan state from: ${source}`, {
      totalSteps: newSteps.length,
      activeSteps: newSteps.filter(s => s.active).length,
      completedSteps: newSteps.filter(s => s.completed).length
    });

    // Validar que solo hay un step activo
    const activeSteps = newSteps.filter(s => s.active);
    if (activeSteps.length > 1) {
      console.warn(`⚠️ [PLAN-${taskId}] Multiple active steps detected, fixing...`, 
        activeSteps.map(s => s.id));
      
      // Mantener solo el primer step activo
      newSteps = newSteps.map((step, index) => ({
        ...step,
        active: index === newSteps.findIndex(s => s.active)
      }));
    }

    // Calcular progreso
    const completedSteps = newSteps.filter(s => s.completed).length;
    const totalSteps = newSteps.length;
    const progress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
    const isCompleted = completedSteps === totalSteps && totalSteps > 0;
    const currentActiveStepId = newSteps.find(s => s.active)?.id || null;

    // Actualizar estado
    setPlanState({
      steps: newSteps,
      currentActiveStepId,
      progress,
      isCompleted
    });

    // Callbacks
    onPlanUpdate?.(newSteps);
    if (isCompleted && !planState.isCompleted) {
      console.log(`🎉 [PLAN-${taskId}] Task completed!`);
      onTaskComplete?.();
    }

    isUpdatingRef.current = false;
  }, [taskId, onPlanUpdate, onTaskComplete, planState.isCompleted]);

  // ========================================================================
  // FUNCIONES DE CONTROL DEL PLAN
  // ========================================================================

  const startStep = useCallback((stepId: string) => {
    console.log(`▶️ [PLAN-${taskId}] Starting step: ${stepId}`);
    
    setPlanState(prev => {
      const newSteps = prev.steps.map(step => ({
        ...step,
        active: step.id === stepId,
        start_time: step.id === stepId ? new Date() : step.start_time
      }));
      
      updatePlanState(newSteps, 'startStep');
      return prev;
    });
  }, [taskId, updatePlanState]);

  const completeStep = useCallback((stepId: string) => {
    console.log(`✅ [PLAN-${taskId}] Completing step: ${stepId}`);
    
    setPlanState(prev => {
      const stepIndex = prev.steps.findIndex(s => s.id === stepId);
      if (stepIndex === -1) {
        console.warn(`⚠️ [PLAN-${taskId}] Step not found: ${stepId}`);
        return prev;
      }

      const newSteps = [...prev.steps];
      
      // Completar el step actual
      newSteps[stepIndex] = {
        ...newSteps[stepIndex],
        active: false,
        completed: true,
        status: 'completed'
      };

      // Activar el siguiente step automáticamente
      const nextStepIndex = stepIndex + 1;
      if (nextStepIndex < newSteps.length && !newSteps[nextStepIndex].completed) {
        console.log(`▶️ [PLAN-${taskId}] Auto-activating next step: ${newSteps[nextStepIndex].id}`);
        newSteps[nextStepIndex] = {
          ...newSteps[nextStepIndex],
          active: true,
          start_time: new Date()
        };
      }

      updatePlanState(newSteps, 'completeStep');
      onStepComplete?.(stepId);
      
      return prev;
    });
  }, [taskId, updatePlanState, onStepComplete]);

  const setPlan = useCallback((newPlan: TaskStep[]) => {
    console.log(`📋 [PLAN-${taskId}] Setting new plan with ${newPlan.length} steps`);
    updatePlanState(newPlan, 'setPlan');
  }, [taskId, updatePlanState]);

  // ========================================================================
  // WEBSOCKET EVENTS
  // ========================================================================

  useEffect(() => {
    if (!socket || !taskId) return;

    console.log(`🔌 [PLAN-${taskId}] Setting up WebSocket listeners`);
    joinTaskRoom(taskId);

    const handlePlanUpdated = (data: any) => {
      console.log(`📡 [PLAN-${taskId}] WebSocket plan_updated:`, data);
      if (data.plan?.steps && Array.isArray(data.plan.steps)) {
        const newSteps = data.plan.steps.map((step: any) => ({
          id: step.id,
          title: step.title,
          description: step.description,
          tool: step.tool,
          status: step.status,
          estimated_time: step.estimated_time,
          completed: step.completed || false,
          active: step.active || false,
          start_time: step.start_time ? new Date(step.start_time) : undefined
        }));
        updatePlanState(newSteps, 'websocket-plan_updated');
      }
    };

    const handleStepStarted = (data: any) => {
      console.log(`📡 [PLAN-${taskId}] WebSocket step_started:`, data);
      if (data.step_id) {
        startStep(data.step_id);
      }
    };

    const handleStepCompleted = (data: any) => {
      console.log(`📡 [PLAN-${taskId}] WebSocket step_completed:`, data);
      if (data.step_id) {
        completeStep(data.step_id);
      }
    };

    const handleTaskProgress = (data: any) => {
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
  }, [socket, taskId, joinTaskRoom, leaveTaskRoom, startStep, completeStep, updatePlanState]);

  // ========================================================================
  // INICIALIZACIÓN CON PLAN INICIAL
  // ========================================================================

  useEffect(() => {
    if (initialPlan.length > 0 && planState.steps.length === 0) {
      console.log(`🚀 [PLAN-${taskId}] Initializing with plan:`, initialPlan.length, 'steps');
      updatePlanState(initialPlan, 'initialization');
    }
  }, [initialPlan, planState.steps.length, taskId, updatePlanState]);

  // ========================================================================
  // API PÚBLICA
  // ========================================================================

  return {
    // Estado del plan
    plan: planState.steps,
    currentActiveStepId: planState.currentActiveStepId,
    progress: planState.progress,
    isCompleted: planState.isCompleted,
    isConnected,
    
    // Funciones de control
    setPlan,
    startStep,
    completeStep,
    
    // Estado computado
    totalSteps: planState.steps.length,
    completedSteps: planState.steps.filter(s => s.completed).length,
    currentActiveStep: planState.steps.find(s => s.active) || null
  };
};