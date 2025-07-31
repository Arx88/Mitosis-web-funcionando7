/**
 * PLAN MANAGER COMPLETAMENTE AISLADO POR TAREA
 * Cada TaskView tiene su propio plan manager sin interferencias
 * SOLUCIÓN DEFINITIVA AL PROBLEMA DE CONTAMINACIÓN
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useTaskWebSocket } from './useTaskWebSocket';
import { TaskStep } from '../types';

interface IsolatedPlanManagerProps {
  taskId: string;
  initialPlan?: TaskStep[];
  onPlanUpdate?: (plan: TaskStep[]) => void;
  onStepComplete?: (stepId: string) => void;
  onTaskComplete?: () => void;
}

interface IsolatedPlanState {
  steps: TaskStep[];
  currentActiveStepId: string | null;
  progress: number;
  isCompleted: boolean;
  lastUpdateTime: Date;
}

export const useIsolatedPlanManager = ({
  taskId,
  initialPlan = [],
  onPlanUpdate,
  onStepComplete,
  onTaskComplete
}: IsolatedPlanManagerProps) => {
  
  // ========================================================================
  // ESTADO COMPLETAMENTE AISLADO POR TAREA
  // ========================================================================
  
  const [planState, setPlanState] = useState<IsolatedPlanState>(() => ({
    steps: [...initialPlan], // Crear copia para evitar referencias compartidas
    currentActiveStepId: initialPlan.find(s => s.active)?.id || null,
    progress: initialPlan.length > 0 ? Math.round((initialPlan.filter(s => s.completed).length / initialPlan.length) * 100) : 0,
    isCompleted: initialPlan.length > 0 && initialPlan.every(s => s.completed),
    lastUpdateTime: new Date()
  }));

  // Refs para control interno
  const isUpdatingRef = useRef(false);
  const taskIdRef = useRef(taskId);
  const mountedRef = useRef(true);

  // ========================================================================
  // WEBSOCKET ESPECÍFICO PARA ESTA TAREA
  // ========================================================================

  const { isConnected, sendMessage } = useTaskWebSocket({
    taskId,
    onPlanUpdated: useCallback((data: any) => {
      if (!mountedRef.current || data.task_id !== taskIdRef.current) return;
      
      console.log(`📋 [PLAN-${taskId}] WebSocket plan update:`, data);
      
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
        
        updatePlanStateInternal(newSteps, 'websocket-plan');
      }
    }, [taskId]),
    
    onStepStarted: useCallback((data: any) => {
      if (!mountedRef.current || data.task_id !== taskIdRef.current) return;
      
      console.log(`▶️ [PLAN-${taskId}] WebSocket step started:`, data);
      
      if (data.step_id) {
        startStepInternal(data.step_id, 'websocket-start');
      }
    }, [taskId]),
    
    onStepCompleted: useCallback((data: any) => {
      if (!mountedRef.current || data.task_id !== taskIdRef.current) return;
      
      console.log(`✅ [PLAN-${taskId}] WebSocket step completed:`, data);
      
      if (data.step_id) {
        completeStepInternal(data.step_id, 'websocket-complete');
      }
    }, [taskId]),
    
    onTaskProgress: useCallback((data: any) => {
      if (!mountedRef.current || data.task_id !== taskIdRef.current) return;
      
      console.log(`📈 [PLAN-${taskId}] WebSocket task progress:`, data);
      
      if (data.step_id) {
        if (data.status === 'started') {
          startStepInternal(data.step_id, 'websocket-progress-start');
        } else if (data.status === 'completed') {
          completeStepInternal(data.step_id, 'websocket-progress-complete');
        }
      }
    }, [taskId])
  });

  // ========================================================================
  // FUNCIONES INTERNAS DE ACTUALIZACIÓN
  // ========================================================================

  const updatePlanStateInternal = useCallback((newSteps: TaskStep[], source: string = 'internal') => {
    if (!mountedRef.current || isUpdatingRef.current) {
      return;
    }

    isUpdatingRef.current = true;
    
    console.log(`🔄 [PLAN-${taskId}] Updating plan from: ${source}`, {
      totalSteps: newSteps.length,
      activeSteps: newSteps.filter(s => s.active).length,
      completedSteps: newSteps.filter(s => s.completed).length
    });

    // Validar que solo hay un step activo
    const activeSteps = newSteps.filter(s => s.active);
    if (activeSteps.length > 1) {
      console.warn(`⚠️ [PLAN-${taskId}] Multiple active steps detected, fixing...`);
      
      // Mantener solo el primer step activo
      let firstActiveFound = false;
      newSteps = newSteps.map(step => ({
        ...step,
        active: step.active && !firstActiveFound ? (firstActiveFound = true, true) : false
      }));
    }

    // Calcular estado
    const completedSteps = newSteps.filter(s => s.completed).length;
    const totalSteps = newSteps.length;
    const progress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
    const isCompleted = completedSteps === totalSteps && totalSteps > 0;
    const currentActiveStepId = newSteps.find(s => s.active)?.id || null;

    // Actualizar estado
    setPlanState(prev => {
      const wasCompleted = prev.isCompleted;
      const newState = {
        steps: newSteps,
        currentActiveStepId,
        progress,
        isCompleted,
        lastUpdateTime: new Date()
      };
      
      // Callbacks
      setTimeout(() => {
        if (mountedRef.current) {
          onPlanUpdate?.(newSteps);
          
          if (isCompleted && !wasCompleted) {
            console.log(`🎉 [PLAN-${taskId}] Task completed!`);
            onTaskComplete?.();
          }
        }
      }, 0);
      
      return newState;
    });

    isUpdatingRef.current = false;
  }, [taskId, onPlanUpdate, onTaskComplete]);

  const startStepInternal = useCallback((stepId: string, source: string = 'internal') => {
    if (!mountedRef.current) return;
    
    console.log(`▶️ [PLAN-${taskId}] Starting step: ${stepId} (${source})`);
    
    setPlanState(prev => {
      const newSteps = prev.steps.map(step => ({
        ...step,
        active: step.id === stepId,
        start_time: step.id === stepId ? new Date() : step.start_time
      }));
      
      updatePlanStateInternal(newSteps, `startStep-${source}`);
      return prev; // updatePlanStateInternal se encarga de la actualización real
    });
  }, [taskId, updatePlanStateInternal]);

  const completeStepInternal = useCallback((stepId: string, source: string = 'internal') => {
    if (!mountedRef.current) return;
    
    console.log(`✅ [PLAN-${taskId}] Completing step: ${stepId} (${source})`);
    
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

      updatePlanStateInternal(newSteps, `completeStep-${source}`);
      
      // Callback de step completado
      setTimeout(() => {
        if (mountedRef.current) {
          onStepComplete?.(stepId);
        }
      }, 0);
      
      return prev; // updatePlanStateInternal se encarga de la actualización real
    });
  }, [taskId, updatePlanStateInternal, onStepComplete]);

  // ========================================================================
  // API PÚBLICA
  // ========================================================================

  const setPlan = useCallback((newPlan: TaskStep[]) => {
    console.log(`📋 [PLAN-${taskId}] Setting new plan with ${newPlan.length} steps`);
    
    // Crear copia profunda para evitar referencias compartidas
    const planCopy = newPlan.map(step => ({ ...step }));
    updatePlanStateInternal(planCopy, 'setPlan');
  }, [taskId, updatePlanStateInternal]);

  const startStep = useCallback((stepId: string) => {
    startStepInternal(stepId, 'manual');
  }, [startStepInternal]);

  const completeStep = useCallback((stepId: string) => {
    completeStepInternal(stepId, 'manual');
  }, [completeStepInternal]);

  // ========================================================================
  // EFECTOS DE LIFECYCLE
  // ========================================================================

  // Actualizar taskIdRef cuando cambie
  useEffect(() => {
    taskIdRef.current = taskId;
  }, [taskId]);

  // Inicializar con plan inicial
  useEffect(() => {
    if (initialPlan.length > 0 && planState.steps.length === 0) {
      console.log(`🚀 [PLAN-${taskId}] Initializing with plan:`, initialPlan.length, 'steps');
      const planCopy = initialPlan.map(step => ({ ...step }));
      updatePlanStateInternal(planCopy, 'initialization');
    }
  }, [initialPlan, planState.steps.length, taskId, updatePlanStateInternal]);

  // Cleanup al desmontar
  useEffect(() => {
    mountedRef.current = true;
    
    return () => {
      console.log(`🧹 [PLAN-${taskId}] Plan manager cleanup`);
      mountedRef.current = false;
      isUpdatingRef.current = false;
    };
  }, [taskId]);

  // ========================================================================
  // VALORES DE RETORNO AISLADOS
  // ========================================================================

  return {
    // Estado del plan
    plan: planState.steps,
    currentActiveStepId: planState.currentActiveStepId,
    progress: planState.progress,
    isCompleted: planState.isCompleted,
    isConnected,
    lastUpdateTime: planState.lastUpdateTime,
    
    // Funciones de control
    setPlan,
    startStep,
    completeStep,
    
    // Estado computado
    totalSteps: planState.steps.length,
    completedSteps: planState.steps.filter(s => s.completed).length,
    currentActiveStep: planState.steps.find(s => s.active) || null,
    
    // Funciones WebSocket
    sendMessage
  };
};