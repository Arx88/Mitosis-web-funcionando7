import React, { useState, useEffect } from 'react';
import { CheckCircle, Circle, Loader2, Clock, Settings, Cloud, Package, Play } from 'lucide-react';

interface EnvironmentSetupStep {
  id: string;
  title: string;
  description: string;
  duration: number; // segundos
  status: 'pending' | 'in-progress' | 'completed' | 'error';
  icon: React.ComponentType<any>;
}

interface EnvironmentSetupLoaderProps {
  isVisible: boolean;
  onComplete: () => void;
  taskTitle: string;
  taskType?: 'web-development' | 'data-processing' | 'system-administration' | 'general';
}

export const EnvironmentSetupLoader: React.FC<EnvironmentSetupLoaderProps> = ({
  isVisible,
  onComplete,
  taskTitle,
  taskType = 'general'
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [steps, setSteps] = useState<EnvironmentSetupStep[]>([]);
  const [totalProgress, setTotalProgress] = useState(0);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState(0);
  const [startTime, setStartTime] = useState<Date | null>(null);

  // Definir pasos según el tipo de tarea
  const getStepsForTaskType = (type: string): EnvironmentSetupStep[] => {
    const baseSteps: EnvironmentSetupStep[] = [
      {
        id: 'safe-environment',
        title: 'Setting Up Safe Environment',
        description: 'Creating isolated container environment...',
        duration: 20,
        status: 'pending',
        icon: Settings
      },
      {
        id: 'cloud-init',
        title: 'Initializing Cloud Environment',
        description: 'Connecting to cloud resources and allocating compute...',
        duration: 30,
        status: 'pending',
        icon: Cloud
      },
      {
        id: 'resources',
        title: 'Provisioning Resources',
        description: 'Installing required dependencies and tools...',
        duration: 40,
        status: 'pending',
        icon: Package
      },
      {
        id: 'configuration',
        title: 'Configuring Environment',
        description: 'Setting up environment variables and configurations...',
        duration: 20,
        status: 'pending',
        icon: Settings
      },
      {
        id: 'agent-start',
        title: 'Starting the Agent',
        description: 'Initializing AI agent and loading task context...',
        duration: 10,
        status: 'pending',
        icon: Play
      }
    ];

    // Personalizar pasos según el tipo de tarea
    if (type === 'web-development') {
      baseSteps[2].description = 'Installing Node.js, npm, frameworks and build tools...';
      baseSteps[2].duration = 50;
    } else if (type === 'data-processing') {
      baseSteps[2].description = 'Installing Python, pandas, numpy, jupyter and ML libraries...';
      baseSteps[2].duration = 60;
    } else if (type === 'system-administration') {
      baseSteps[2].description = 'Installing system tools, monitoring and security utilities...';
      baseSteps[2].duration = 45;
    }

    return baseSteps;
  };

  // Inicializar pasos cuando el componente se muestra
  useEffect(() => {
    if (isVisible && steps.length === 0) {
      const initialSteps = getStepsForTaskType(taskType);
      setSteps(initialSteps);
      setStartTime(new Date());
      
      // Calcular tiempo total estimado
      const totalTime = initialSteps.reduce((acc, step) => acc + step.duration, 0);
      setEstimatedTimeRemaining(totalTime);
    }
  }, [isVisible, taskType]);

  // Simular progreso de pasos
  useEffect(() => {
    if (!isVisible || steps.length === 0) return;

    const currentStep = steps[currentStepIndex];
    if (!currentStep || currentStep.status === 'completed') {
      if (currentStepIndex < steps.length - 1) {
        setCurrentStepIndex(prev => prev + 1);
      } else {
        // Todos los pasos completados
        setTimeout(() => {
          onComplete();
        }, 1000);
      }
      return;
    }

    // Marcar paso actual como en progreso
    if (currentStep.status === 'pending') {
      setSteps(prevSteps => prevSteps.map(step => 
        step.id === currentStep.id 
          ? { ...step, status: 'in-progress' }
          : step
      ));
    }

    // Simular progreso del paso actual
    const stepTimer = setTimeout(() => {
      setSteps(prevSteps => prevSteps.map(step => 
        step.id === currentStep.id 
          ? { ...step, status: 'completed' }
          : step
      ));
    }, currentStep.duration * 1000);

    return () => clearTimeout(stepTimer);
  }, [currentStepIndex, steps, isVisible, onComplete]);

  // Actualizar progreso total y tiempo restante
  useEffect(() => {
    const completedSteps = steps.filter(step => step.status === 'completed').length;
    const progress = Math.round((completedSteps / steps.length) * 100);
    setTotalProgress(progress);

    // Calcular tiempo restante
    const remainingSteps = steps.slice(currentStepIndex);
    const timeRemaining = remainingSteps.reduce((acc, step) => acc + step.duration, 0);
    setEstimatedTimeRemaining(timeRemaining);
  }, [steps, currentStepIndex]);

  // Formatear tiempo restante
  const formatTimeRemaining = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  // Obtener tiempo transcurrido
  const getElapsedTime = (): string => {
    if (!startTime) return '0s';
    const elapsed = Math.floor((new Date().getTime() - startTime.getTime()) / 1000);
    return formatTimeRemaining(elapsed);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-[#272728] rounded-2xl p-8 max-w-2xl w-full mx-4 border border-[rgba(255,255,255,0.08)]">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Settings className="w-8 h-8 text-blue-400 animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Preparing Your Environment</h2>
          <p className="text-[#ACACAC] mb-1">Setting up everything needed for:</p>
          <p className="text-blue-400 font-medium">{taskTitle}</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-[#ACACAC]">Overall Progress</span>
            <span className="text-sm text-white font-medium">{totalProgress}%</span>
          </div>
          <div className="w-full bg-[#383739] rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${totalProgress}%` }}
            />
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-4 mb-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div 
                key={step.id}
                className={`flex items-center gap-4 p-4 rounded-lg transition-all duration-300 ${
                  step.status === 'in-progress' 
                    ? 'bg-blue-500/10 border border-blue-500/20' 
                    : step.status === 'completed'
                    ? 'bg-green-500/10 border border-green-500/20'
                    : 'bg-[#383739] border border-transparent'
                }`}
              >
                {/* Icon/Status */}
                <div className="flex-shrink-0">
                  {step.status === 'completed' ? (
                    <CheckCircle className="w-6 h-6 text-green-400" />
                  ) : step.status === 'in-progress' ? (
                    <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
                  ) : (
                    <Circle className="w-6 h-6 text-[#7F7F7F]" />
                  )}
                </div>

                {/* Step Icon */}
                <div className={`flex-shrink-0 p-2 rounded-lg ${
                  step.status === 'completed' 
                    ? 'bg-green-500/20' 
                    : step.status === 'in-progress'
                    ? 'bg-blue-500/20'
                    : 'bg-[#4A4A4C]'
                }`}>
                  <Icon className={`w-4 h-4 ${
                    step.status === 'completed' 
                      ? 'text-green-400' 
                      : step.status === 'in-progress'
                      ? 'text-blue-400'
                      : 'text-[#ACACAC]'
                  }`} />
                </div>

                {/* Step Content */}
                <div className="flex-1 min-w-0">
                  <h3 className={`font-medium ${
                    step.status === 'completed' 
                      ? 'text-green-400' 
                      : step.status === 'in-progress'
                      ? 'text-blue-400'
                      : 'text-[#DADADA]'
                  }`}>
                    {step.title}
                  </h3>
                  <p className="text-sm text-[#ACACAC] truncate">{step.description}</p>
                </div>

                {/* Duration */}
                <div className="flex-shrink-0 text-xs text-[#7F7F7F]">
                  {step.duration}s
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Info */}
        <div className="flex justify-between items-center text-sm text-[#ACACAC] bg-[#383739] rounded-lg p-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span>Est. remaining: {formatTimeRemaining(estimatedTimeRemaining)}</span>
          </div>
          <div>
            Elapsed: {getElapsedTime()}
          </div>
        </div>

        {/* Note */}
        <div className="mt-4 text-center">
          <p className="text-xs text-[#7F7F7F]">
            This usually takes around 1-2 minutes • Setting up isolated environment
          </p>
        </div>
      </div>
    </div>
  );
};