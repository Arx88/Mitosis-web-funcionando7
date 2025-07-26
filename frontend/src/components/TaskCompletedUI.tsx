import React from 'react';
import { CheckCircle } from 'lucide-react';

interface TaskCompletedUIProps {
  className?: string;
}

export const TaskCompletedUI: React.FC<TaskCompletedUIProps> = ({ className = "" }) => {
  return (
    <div className={`mt-3 ${className}`}>
      {/* ✨ FIXED: Smaller completion UI that matches collapsed panel size */}
      <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-400/20 rounded-xl overflow-hidden shadow-lg backdrop-blur-sm">
        <div className="px-4 py-4 flex items-center justify-center text-center">
          {/* ✨ FIXED: Smaller animated check icon */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center shadow-lg animate-pulse">
              <CheckCircle className="w-4 h-4 text-white animate-bounce" style={{ animationDuration: '2s' }} />
            </div>
            
            {/* ✨ FIXED: Compact completion message */}
            <div>
              <h3 className="text-sm font-bold text-green-400 animate-fade-in">
                Tarea Completada
              </h3>
              <p className="text-xs text-green-300/80 animate-fade-in" style={{ animationDelay: '0.5s' }}>
                Todas las etapas ejecutadas exitosamente
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};