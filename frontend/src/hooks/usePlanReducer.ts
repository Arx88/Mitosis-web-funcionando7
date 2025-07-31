/**
 * Plan State Management Hook using useReducer
 * REFACTORIZADO: Centraliza TODA la lógica del plan de acción
 * Elimina duplicación y sobrecomplicación en TaskView.tsx
 */

import { useReducer, useCallback } from 'react';
import { TaskStep } from '../types';

// ========================================================================
// TIPOS PARA EL PLAN REDUCER
// ========================================================================

interface PlanState {
  steps: TaskStep[];
  currentActiveStepId: string | null;
  completedStepsCount: number;
  totalSteps: number;
  progress: number;
}

type PlanAction = 
  | { type: 'SET_PLAN'; payload: TaskStep[] }
  | { type: 'START_STEP'; payload: { stepId: string; timestamp?: string } }
  | { type: 'COMPLETE_STEP'; payload: { stepId: string; result?: any; timestamp?: string } }
  | { type: 'UPDATE_STEP'; payload: { stepId: string; updates: Partial<TaskStep> } }
  | { type: 'RESET_PLAN' };

// Estado inicial
const initialPlanState: PlanState = {
  steps: [],
  currentActiveStepId: null,
  completedStepsCount: 0,
  totalSteps: 0,
  progress: 0
};

// ========================================================================
// PLAN REDUCER - LÓGICA CENTRALIZADA Y SIMPLE
// ========================================================================

function planReducer(state: PlanState, action: PlanAction): PlanState {
  switch (action.type) {
    case 'SET_PLAN':
      const newSteps = action.payload;
      const completed = newSteps.filter(s => s.completed).length;
      const total = newSteps.length;
      
      return {
        ...state,
        steps: newSteps,
        currentActiveStepId: newSteps.find(s => s.active)?.id || null,
        completedStepsCount: completed,
        totalSteps: total,
        progress: total > 0 ? Math.round((completed / total) * 100) : 0
      };

    case 'START_STEP': {
      const { stepId, timestamp } = action.payload;
      
      const updatedSteps = state.steps.map(step => {
        if (step.id === stepId) {
          // Activar el paso actual
          return {
            ...step,
            active: true,
            status: 'in-progress',
            completed: false,
            start_time: timestamp ? new Date(timestamp) : new Date()
          };
        } else {
          // Desactivar todos los demás pasos
          return {
            ...step,
            active: false
          };
        }
      });

      return {
        ...state,
        steps: updatedSteps,
        currentActiveStepId: stepId
      };
    }

    case 'COMPLETE_STEP': {
      const { stepId, result, timestamp } = action.payload;
      
      const updatedSteps = state.steps.map(step => {
        if (step.id === stepId) {
          // Completar el paso actual
          return {
            ...step,
            active: false,
            status: 'completed',
            completed: true,
            result: result || step.result
          };
        }
        return step;
      });

      // Activar automáticamente el siguiente paso
      const currentIndex = state.steps.findIndex(s => s.id === stepId);
      const nextStepIndex = currentIndex + 1;
      
      if (nextStepIndex < state.steps.length) {
        updatedSteps[nextStepIndex] = {
          ...updatedSteps[nextStepIndex],
          active: true,
          status: 'in-progress',
          start_time: new Date()
        };
      }

      const completed = updatedSteps.filter(s => s.completed).length;
      const nextActiveStepId = nextStepIndex < state.steps.length 
        ? updatedSteps[nextStepIndex].id 
        : null;

      return {
        ...state,
        steps: updatedSteps,
        currentActiveStepId: nextActiveStepId,
        completedStepsCount: completed,
        progress: Math.round((completed / state.totalSteps) * 100)
      };
    }

    case 'UPDATE_STEP': {
      const { stepId, updates } = action.payload;
      
      const updatedSteps = state.steps.map(step => 
        step.id === stepId ? { ...step, ...updates } : step
      );

      const completed = updatedSteps.filter(s => s.completed).length;

      return {
        ...state,
        steps: updatedSteps,
        completedStepsCount: completed,
        progress: Math.round((completed / state.totalSteps) * 100)
      };
    }

    case 'RESET_PLAN':
      return initialPlanState;

    default:
      return state;
  }
}

// ========================================================================
// HOOK PERSONALIZADO
// ========================================================================

export const usePlanReducer = (initialPlan: TaskStep[] = []) => {
  const [planState, dispatch] = useReducer(planReducer, {
    ...initialPlanState,
    steps: initialPlan,
    totalSteps: initialPlan.length,
    completedStepsCount: initialPlan.filter(s => s.completed).length,
    progress: initialPlan.length > 0 ? 
      Math.round((initialPlan.filter(s => s.completed).length / initialPlan.length) * 100) : 0
  });

  // ========================================================================
  // HANDLERS PÚBLICOS SIMPLES
  // ========================================================================

  const setPlan = useCallback((steps: TaskStep[]) => {
    dispatch({ type: 'SET_PLAN', payload: steps });
  }, []);

  const startStep = useCallback((stepId: string, timestamp?: string) => {
    dispatch({ type: 'START_STEP', payload: { stepId, timestamp } });
  }, []);

  const completeStep = useCallback((stepId: string, result?: any, timestamp?: string) => {
    dispatch({ type: 'COMPLETE_STEP', payload: { stepId, result, timestamp } });
  }, []);

  const updateStep = useCallback((stepId: string, updates: Partial<TaskStep>) => {
    dispatch({ type: 'UPDATE_STEP', payload: { stepId, updates } });
  }, []);

  const resetPlan = useCallback(() => {
    dispatch({ type: 'RESET_PLAN' });
  }, []);

  // ========================================================================
  // HELPER FUNCTIONS
  // ========================================================================

  const getCurrentActiveStep = useCallback(() => {
    return planState.steps.find(step => step.active) || null;
  }, [planState.steps]);

  const getNextStep = useCallback(() => {
    const currentIndex = planState.steps.findIndex(step => step.active);
    const nextIndex = currentIndex + 1;
    return nextIndex < planState.steps.length ? planState.steps[nextIndex] : null;
  }, [planState.steps]);

  const isCompleted = useCallback(() => {
    return planState.totalSteps > 0 && planState.completedStepsCount === planState.totalSteps;
  }, [planState.completedStepsCount, planState.totalSteps]);

  return {
    // Estado
    plan: planState.steps,
    currentActiveStepId: planState.currentActiveStepId,
    completedStepsCount: planState.completedStepsCount,
    totalSteps: planState.totalSteps,
    progress: planState.progress,
    
    // Acciones
    setPlan,
    startStep,
    completeStep,
    updateStep,
    resetPlan,
    
    // Helpers
    getCurrentActiveStep,
    getNextStep,
    isCompleted
  };
};