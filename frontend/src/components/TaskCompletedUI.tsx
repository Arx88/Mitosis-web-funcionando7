import React from 'react';
import { CheckCircle } from 'lucide-react';

interface TaskCompletedUIProps {
  className?: string;
}

export const TaskCompletedUI: React.FC<TaskCompletedUIProps> = ({ className = "" }) => {
  return (
    <div className={`mt-3 ${className}`}>
      <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-400/20 rounded-xl overflow-hidden shadow-lg backdrop-blur-sm">
        <div className="px-6 py-8 flex flex-col items-center justify-center text-center">
          {/* Animated Check Icon */}
          <div className="mb-4 relative">
            <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center shadow-lg animate-pulse">
              <CheckCircle className="w-8 h-8 text-white animate-bounce" style={{ animationDuration: '2s' }} />
            </div>
            {/* Subtle ring animation */}
            <div className="absolute inset-0 w-16 h-16 border-2 border-green-400/30 rounded-full animate-ping" style={{ animationDuration: '3s' }}></div>
          </div>
          
          {/* Completion Message */}
          <h3 className="text-xl font-bold text-green-400 mb-2 animate-fade-in">
            Tarea Completada
          </h3>
          
          <p className="text-sm text-green-300/80 animate-fade-in" style={{ animationDelay: '0.5s' }}>
            Todas las etapas han sido ejecutadas exitosamente
          </p>
        </div>
      </div>
    </div>
  );
};