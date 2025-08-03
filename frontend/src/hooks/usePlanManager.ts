/**
 * HOOK ÚNICO Y SIMPLIFICADO PARA PLAN DE ACCIÓN - REFACTORIZADO
 * Usa completamente el Context API para aislamiento de tareas
 * Eliminada duplicación y loops infinitos
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { useWebSocket } from './useWebSocket';
import { TaskStep } from '../types';
import { useAppContext } from '../context/AppContext';
import { API_CONFIG } from '../config/api';

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
  // USAR CONTEXT PARA ESTADO AISLADO - NO MÁS ESTADO LOCAL
  // ========================================================================
  
  const { 
    getTaskPlanState, 
    updateTaskPlan,
    getTaskWebSocketState,
    setTaskWebSocketState
  } = useAppContext();
  
  // WebSocket connection
  const { socket, isConnected, joinTaskRoom, leaveTaskRoom } = useWebSocket();
  
  // Refs para evitar loops infinitos
  const isUpdatingRef = useRef(false);
  const lastStepsHashRef = useRef<string>('');
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // ========================================================================
  // OBTENER ESTADO AISLADO DESDE CONTEXT
  // ========================================================================
  
  const taskPlanState = useMemo(() => getTaskPlanState(taskId), [getTaskPlanState, taskId]);
  const plan = taskPlanState.plan;
  const progress = taskPlanState.progress;
  const currentActiveStep = taskPlanState.currentActiveStep;
  const lastUpdateTime = taskPlanState.lastUpdateTime;

  // ========================================================================
  // FUNCIÓN PRINCIPAL: ACTUALIZAR PLAN - USANDO CONTEXT AISLADO
  // ========================================================================
  
  const updatePlan = useCallback((newSteps: TaskStep[], source: string = 'internal') => {
    // Crear hash de los pasos para detectar cambios reales
    const stepsHash = JSON.stringify(newSteps.map(s => ({ 
      id: s.id, 
      completed: s.completed, 
      active: s.active,
      status: s.status 
    })));
    
    // ✅ PROTECCIÓN 1: Evitar actualizaciones redundantes
    if (stepsHash === lastStepsHashRef.current) {
      console.log(`🛡️ [PLAN-${taskId}] Update skipped - no changes detected from: ${source}`);
      return;
    }
    
    // ✅ PROTECCIÓN 2: Evitar múltiples updates simultáneos
    if (isUpdatingRef.current) {
      console.log(`🛡️ [PLAN-${taskId}] Update skipped - already updating from: ${source}`);
      return;
    }

    // ✅ ACTUALIZACIÓN INMEDIATA SIN DEBOUNCE PARA EVITAR REINICIOS
    isUpdatingRef.current = true;
    lastStepsHashRef.current = stepsHash;
    
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
        console.warn(`⚠️ [PLAN-${taskId}] Deactivating invalid active step: ${step.id}`);
        return { ...step, active: false };
      }
      return step;
    });

    // ✅ ACTUALIZAR EN CONTEXT AISLADO
    updateTaskPlan(taskId, validatedSteps);
    
    // Callbacks con protección
    try {
      onPlanUpdate?.(validatedSteps);
      
      // Verificar si la tarea está completa
      const completedSteps = validatedSteps.filter(s => s.completed).length;
      const totalSteps = validatedSteps.length;
      
      if (completedSteps === totalSteps && totalSteps > 0) {
        console.log(`🎉 [PLAN-${taskId}] Task completed! All ${totalSteps} steps are done`);
        onTaskComplete?.();
      }
    } catch (error) {
      console.error(`❌ [PLAN-${taskId}] Error in callbacks:`, error);
    } finally {
      isUpdatingRef.current = false;
    }
  }, [taskId, updateTaskPlan, onPlanUpdate, onTaskComplete]);

  const setPlan = useCallback((newSteps: TaskStep[]) => {
    console.log(`🔄 [PLAN-${taskId}] setPlan called with ${newSteps.length} steps`);
    
    // UPGRADE AI: Limpieza inmediata para evitar mostrar datos de tarea anterior
    if (newSteps.length === 0) {
      console.log(`🧹 [PLAN-${taskId}] Setting empty plan - clearing previous task state`);
      // Actualizar inmediatamente en el Context para limpiar estado anterior
      updateTaskPlan(taskId, []);
      onPlanUpdate?.([]);
    } else {
      console.log(`📋 [PLAN-${taskId}] Setting plan with ${newSteps.length} steps`);
    }
    
    updatePlan(newSteps, 'setPlan');
  }, [taskId, updatePlan, updateTaskPlan, onPlanUpdate]);

  // ========================================================================
  // FUNCIONES DE CONTROL DE STEPS
  // ========================================================================
  
  const startStep = useCallback((stepId: string, timestamp?: Date) => {
    const currentPlan = getTaskPlanState(taskId).plan;
    const updatedSteps = currentPlan.map(step => ({
      ...step,
      active: step.id === stepId && !step.completed,
      start_time: step.id === stepId ? (timestamp || new Date()) : step.start_time
    }));
    
    updatePlan(updatedSteps, 'startStep');
  }, [taskId, getTaskPlanState, updatePlan]);

  const completeStep = useCallback((stepId: string, result?: any, timestamp?: Date) => {
    const currentPlan = getTaskPlanState(taskId).plan;
    const updatedSteps = currentPlan.map(step => ({
      ...step,
      completed: step.id === stepId ? true : step.completed,
      active: step.id === stepId ? false : step.active,
      status: step.id === stepId ? 'completed' : step.status
    }));
    
    updatePlan(updatedSteps, 'completeStep');
    
    if (onStepComplete) {
      onStepComplete(stepId);
    }
  }, [taskId, getTaskPlanState, updatePlan, onStepComplete]);

  const updateStep = useCallback((stepId: string, updates: Partial<TaskStep>) => {
    const currentPlan = getTaskPlanState(taskId).plan;
    const updatedSteps = currentPlan.map(step =>
      step.id === stepId ? { ...step, ...updates } : step
    );
    
    updatePlan(updatedSteps, 'updateStep');
  }, [taskId, getTaskPlanState, updatePlan]);

  // ========================================================================
  // WEBSOCKET INTEGRATION - USANDO CONTEXT AISLADO
  // ========================================================================

  useEffect(() => {
    if (!taskId || !socket) {
      console.log(`⚠️ [PLAN-${taskId || 'NO-ID'}] Missing requirements - taskId:`, !!taskId, 'socket:', !!socket);
      return;
    }

    console.log(`🌐 [PLAN-${taskId}] Setting up WebSocket connection and polling`);
    let isJoined = false;

    const setupConnection = () => {
      if (!socket || !taskId || isJoined) return;
      
      console.log(`🔗 [PLAN-${taskId}] Setting up connection`);
      joinTaskRoom(taskId);
      isJoined = true;
    };

    // ✅ CRITICAL FIX: Add HTTP polling as backup
    const startPolling = () => {
      const pollInterval = setInterval(async () => {
        try {
          console.log(`🔄 [PLAN-${taskId}] Polling for updates...`);
          const response = await fetch(`${API_CONFIG.backend.url}/api/agent/get-all-tasks`);
          if (response.ok) {
            const data = await response.json();
            const currentTask = data.tasks?.find((t: any) => t.id === taskId);
            
            if (currentTask?.plan && Array.isArray(currentTask.plan)) {
              console.log(`📊 [PLAN-${taskId}] Polling found plan with ${currentTask.plan.length} steps`);
              
              const newSteps = currentTask.plan.map((step: any) => ({
                id: step.id,
                title: step.title,
                description: step.description,
                tool: step.tool,
                status: step.status,
                estimated_time: step.estimated_time,
                completed: step.completed || false,
                active: step.active || false,
                result: step.result
              }));
              
              updatePlan(newSteps, 'http-polling');
            }
          }
        } catch (error) {
          console.error(`❌ [PLAN-${taskId}] Polling error:`, error);
        }
      }, 3000); // Poll every 3 seconds

      return () => {
        console.log(`🛑 [PLAN-${taskId}] Stopping polling`);
        clearInterval(pollInterval);
      };
    };

    // Listen for connection events
    const onConnect = () => {
      console.log(`✅ [PLAN-${taskId}] WebSocket connected, joining room`);
      setupConnection();
    };

    const onDisconnect = () => {
      console.log(`❌ [PLAN-${taskId}] WebSocket disconnected`);
      isJoined = false;
    };

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);

    const handlePlanUpdated = (data: any) => {
      if (data.plan?.steps && Array.isArray(data.plan.steps)) {
        console.log(`📡 [PLAN-${taskId}] Plan update received via WebSocket:`, data.plan.steps.length, 'steps');
        
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
        
        updatePlan(newSteps, 'websocket-plan_updated');
      }
    };

    const handleStepStarted = (data: any) => {
      if (data.step_id) {
        console.log(`🚀 [PLAN-${taskId}] Step started via WebSocket:`, data.step_id);
        startStep(data.step_id, data.timestamp ? new Date(data.timestamp) : undefined);
      }
    };

    const handleStepCompleted = (data: any) => {
      if (data.step_id) {
        console.log(`✅ [PLAN-${taskId}] Step completed via WebSocket:`, data.step_id);
        completeStep(data.step_id, data.result, data.timestamp ? new Date(data.timestamp) : undefined);
      }
    };

    const handleTaskProgress = (data: any) => {
      if (data.step_id) {
        if (data.status === 'started' || data.activity) {
          startStep(data.step_id, data.timestamp ? new Date(data.timestamp) : undefined);
        } else if (data.status === 'completed') {
          completeStep(data.step_id, data.result, data.timestamp ? new Date(data.timestamp) : undefined);
        }
      }
    };

    const handleTaskCompleted = (data: any) => {
      console.log(`🎉 [PLAN-${taskId}] Task completed via WebSocket`);
      onTaskComplete?.();
    };

    // Registrar listeners
    socket.on('plan_updated', handlePlanUpdated);
    socket.on('step_started', handleStepStarted);
    socket.on('step_completed', handleStepCompleted);
    socket.on('task_progress', handleTaskProgress);
    socket.on('task_completed', handleTaskCompleted);

    // Start HTTP polling as backup
    const stopPolling = startPolling();

    return () => {
      console.log(`🧹 [PLAN-${taskId}] Cleaning up WebSocket listeners and polling`);
      
      // Stop polling
      stopPolling();
      
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('plan_updated', handlePlanUpdated);
      socket.off('step_started', handleStepStarted);
      socket.off('step_completed', handleStepCompleted);
      socket.off('task_progress', handleTaskProgress);
      socket.off('task_completed', handleTaskCompleted);
      
      // ✅ CRITICAL FIX: Only leave room if we actually joined
      if (isJoined) {
        console.log(`🚪 [PLAN-${taskId}] Leaving WebSocket room`);
        leaveTaskRoom(taskId);
        isJoined = false;
      }
    };
  }, [taskId, socket]); // ✅ CRITICAL FIX: Remove dependencies that cause re-renders

  // ========================================================================
  // INICIALIZACIÓN DEL PLAN - CON CONTEXT AISLADO
  // ========================================================================

  useEffect(() => {
    if (initialPlan && initialPlan.length > 0) {
      const currentPlan = getTaskPlanState(taskId).plan;
      
      // Solo inicializar si no hay plan existente
      if (currentPlan.length === 0) {
        console.log(`📋 [PLAN-${taskId}] Initializing plan with ${initialPlan.length} steps`);
        updatePlan(initialPlan, 'initialization');
      }
    }
  }, [taskId, initialPlan, getTaskPlanState, updatePlan]);

  // ========================================================================
  // COMPUTED VALUES - USANDO CONTEXT AISLADO
  // ========================================================================

  const currentActiveStepId = useMemo(() => {
    return currentActiveStep?.id || null;
  }, [currentActiveStep]);

  const isCompleted = useMemo(() => {
    return taskPlanState.isCompleted;
  }, [taskPlanState.isCompleted]);

  // ========================================================================
  // CLEANUP
  // ========================================================================

  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  // ========================================================================
  // RETURN - USANDO DATOS AISLADOS DEL CONTEXT
  // ========================================================================

  return {
    // Estado del plan desde Context aislado
    plan,
    progress,
    lastUpdateTime,
    currentActiveStep,
    currentActiveStepId,
    isCompleted,
    
    // Estado de conexión
    isConnected,
    
    // Funciones de control
    setPlan,
    updatePlan,
    startStep,
    completeStep,
    updateStep
  };
};