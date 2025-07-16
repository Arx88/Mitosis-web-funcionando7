import React from 'react';
import { Bot } from 'lucide-react';

export type AgentStatus = 
  | 'idle'
  | 'task_received'
  | 'analyzing_task'
  | 'executing_step'
  | 'waiting_user_input'
  | 'task_completed'
  | 'task_failed'
  | 'orchestrating'
  | 'planning'
  | 'executing_plan';

interface AgentStatusBarProps {
  status: AgentStatus;
  currentStep?: string;
  className?: string;
}

export const AgentStatusBar: React.FC<AgentStatusBarProps> = ({
  status,
  currentStep,
  className = ''
}) => {
  const getStatusText = () => {
    switch (status) {
      case 'task_received':
        return 'Tarea Recibida';
      case 'analyzing_task':
        return 'Analizando Tarea';
      case 'executing_step':
        return currentStep ? `Ejecutando Paso: ${currentStep}` : 'Ejecutando Paso';
      case 'waiting_user_input':
        return 'Esperando Entrada del Usuario';
      case 'task_completed':
        return 'Tarea Completada';
      case 'task_failed':
        return 'Tarea Fallida';
      default:
        return '';
    }
  };

  if (status === 'idle') {
    return (
      <div className={`w-full px-4 py-2 bg-[#2A2A2C] border-t border-[rgba(255,255,255,0.08)] overflow-x-hidden ${className}`} style={{ fontFamily: "'Open Sans', sans-serif" }}>
        <div className="flex items-center gap-3">
          <Bot className="w-4 h-4 text-gray-500 flex-shrink-0" />
          <span className="text-xs font-light text-gray-500">
            Agente en espera...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`w-full px-4 py-3 bg-[#2A2A2C] border-t border-[rgba(255,255,255,0.08)] overflow-x-hidden ${className}`} style={{ fontFamily: "'Open Sans', sans-serif" }}>
      <div className="flex items-center gap-3">
        {/* Robot Icon - sin círculo, 20% más grande */}
        <Bot className="w-5 h-5 text-white flex-shrink-0" />
        
        {/* Status Text - White color, Open Sans font, lighter weight */}
        <span className="text-sm font-light text-white truncate">
          {getStatusText()}
        </span>
        
        {/* Activity Indicator - White color, properly centered */}
        {(status === 'analyzing_task' || status === 'executing_step') && (
          <div className="flex items-center gap-1 ml-2 flex-shrink-0">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-1 h-1 bg-white rounded-full animate-bounce opacity-60"
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};