import React, { useState, useEffect } from 'react';
import { CheckCircle, Loader2, Settings, Cloud, Package, Play, Terminal } from 'lucide-react';

interface InitializationStep {
  id: string;
  title: string;
  duration: number; // milliseconds
  status: 'pending' | 'running' | 'completed';
  icon: React.ComponentType<any>;
}

interface MinimalTaskInitializerProps {
  taskId: string;
  taskTitle: string;
  taskType?: 'web-development' | 'data-processing' | 'system-administration' | 'general';
  onComplete?: () => void;
  onLogUpdate?: (message: string, type: 'info' | 'success' | 'error') => void;
}

export const MinimalTaskInitializer: React.FC<MinimalTaskInitializerProps> = ({
  taskId,
  taskTitle,
  taskType = 'general',
  onComplete,
  onLogUpdate
}) => {
  const [steps, setSteps] = useState<InitializationStep[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  // Definir pasos de inicialización minimalista
  const initializeSteps = (): InitializationStep[] => {
    const baseSteps: InitializationStep[] = [
      {
        id: 'environment',
        title: 'Setting up environment',
        duration: 1500, // Incrementado para ser más visible
        status: 'pending',
        icon: Settings
      },
      {
        id: 'dependencies',
        title: 'Installing dependencies',
        duration: 2000, // Incrementado para ser más visible
        status: 'pending',
        icon: Package
      },
      {
        id: 'agent',
        title: 'Initializing agent',
        duration: 1000, // Incrementado para ser más visible
        status: 'pending',
        icon: Play
      }
    ];

    // Personalizar según tipo de tarea
    if (taskType === 'web-development') {
      baseSteps[1].title = 'Installing web dev tools';
      baseSteps[1].duration = 2500;
    } else if (taskType === 'data-processing') {
      baseSteps[1].title = 'Installing data libraries';
      baseSteps[1].duration = 3000;
    }

    return baseSteps;
  };

  // Inicializar pasos
  useEffect(() => {
    const initialSteps = initializeSteps();
    setSteps(initialSteps);
    
    // Log inicial
    if (onLogUpdate) {
      onLogUpdate(`🚀 Initializing task: ${taskTitle}`, 'info');
    }
  }, [taskTitle, taskType, onLogUpdate]);

  // Ejecutar pasos secuencialmente
  useEffect(() => {
    if (steps.length === 0) return;

    const currentStep = steps[currentStepIndex];
    if (!currentStep) {
      // Todos los pasos completados
      if (onLogUpdate) {
        onLogUpdate(`✅ Task environment ready for: ${taskTitle}`, 'success');
      }
      
      setTimeout(() => {
        setIsVisible(false);
        if (onComplete) {
          onComplete();
        }
      }, 500);
      return;
    }

    // Marcar paso como running
    setSteps(prev => prev.map(step => 
      step.id === currentStep.id 
        ? { ...step, status: 'running' }
        : step
    ));

    // Log del paso actual
    if (onLogUpdate) {
      onLogUpdate(`⚙️  ${currentStep.title}...`, 'info');
    }

    // Simular ejecución del paso
    const timer = setTimeout(() => {
      setSteps(prev => prev.map(step => 
        step.id === currentStep.id 
          ? { ...step, status: 'completed' }
          : step
      ));

      // Log de completado
      if (onLogUpdate) {
        onLogUpdate(`✓ ${currentStep.title} completed`, 'success');
      }

      // Avanzar al siguiente paso
      setCurrentStepIndex(prev => prev + 1);
    }, currentStep.duration);

    return () => clearTimeout(timer);
  }, [currentStepIndex, steps, taskTitle, onLogUpdate, onComplete]);

  // Si no es visible, no renderizar nada
  if (!isVisible) return null;

  return (
    <div className="flex items-center gap-2 text-xs text-[#ACACAC] bg-[#2A2A2B] rounded-lg px-3 py-2 border border-[rgba(255,255,255,0.05)]">
      <Terminal className="w-3 h-3 text-blue-400" />
      <div className="flex items-center gap-2">
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={step.id} className="flex items-center gap-1">
              {step.status === 'completed' ? (
                <CheckCircle className="w-3 h-3 text-green-400" />
              ) : step.status === 'running' ? (
                <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
              ) : (
                <Icon className="w-3 h-3 text-[#7F7F7F]" />
              )}
              
              {step.status === 'running' && (
                <span className="text-blue-400 text-xs font-medium">
                  {step.title}
                </span>
              )}
              
              {index < steps.length - 1 && step.status === 'completed' && (
                <span className="text-[#7F7F7F] mx-1">→</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};