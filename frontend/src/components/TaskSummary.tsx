import React from 'react';
import { CheckCircle, Clock, Target, Award, Zap, TrendingUp } from 'lucide-react';

interface TaskSummaryProps {
  title?: string;
  completedSteps?: string[];
  executionTime?: string;
  toolsUsed?: string[];
  outcome?: string;
  type?: 'success' | 'partial' | 'info';
}

export const TaskSummary: React.FC<TaskSummaryProps> = ({
  title = "Tarea completada exitosamente",
  completedSteps = [],
  executionTime,
  toolsUsed = [],
  outcome,
  type = 'success'
}) => {
  const getStatusColor = () => {
    switch (type) {
      case 'success':
        return {
          gradient: 'from-green-500/10 to-emerald-500/10',
          border: 'border-green-500/20',
          icon: 'text-green-400',
          accent: 'text-green-400'
        };
      case 'partial':
        return {
          gradient: 'from-yellow-500/10 to-orange-500/10',
          border: 'border-yellow-500/20',
          icon: 'text-yellow-400',
          accent: 'text-yellow-400'
        };
      default:
        return {
          gradient: 'from-blue-500/10 to-cyan-500/10',
          border: 'border-blue-500/20',
          icon: 'text-blue-400',
          accent: 'text-blue-400'
        };
    }
  };

  const colors = getStatusColor();

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className={`flex items-center gap-3 p-4 bg-gradient-to-r ${colors.gradient} rounded-xl border ${colors.border}`}>
        <div className={`flex items-center justify-center w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-lg`}>
          <CheckCircle className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className={`text-lg font-semibold ${colors.accent}`}>
            ✨ {title}
          </h3>
          <p className="text-sm text-[#ACACAC]">
            Se ha completado el procesamiento de tu solicitud con éxito
          </p>
        </div>
      </div>

      {/* Task Outcome */}
      {outcome && (
        <div className="bg-gradient-to-r from-[#1E1E1F] to-[#252526] rounded-xl p-5 border border-[rgba(255,255,255,0.08)]">
          <div className="flex items-center gap-2 mb-3">
            <Target className={`w-5 h-5 ${colors.accent}`} />
            <h4 className={`text-base font-semibold ${colors.accent}`}>Resultado:</h4>
          </div>
          <div className="text-[#DADADA] leading-relaxed">
            {outcome.split('\n').map((paragraph, index) => (
              paragraph.trim() && (
                <p key={index} className="mb-2 last:mb-0">
                  {paragraph}
                </p>
              )
            ))}
          </div>
        </div>
      )}

      {/* Completed Steps */}
      {completedSteps.length > 0 && (
        <div className="bg-[#1E1E1F] rounded-xl p-4 border border-[rgba(255,255,255,0.08)]">
          <div className="flex items-center gap-2 mb-3">
            <Zap className={`w-5 h-5 ${colors.accent}`} />
            <h4 className={`text-base font-semibold ${colors.accent}`}>
              Pasos completados:
            </h4>
          </div>
          
          <div className="space-y-2">
            {completedSteps.map((step, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className={`flex-shrink-0 w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center text-green-400 text-xs font-bold mt-0.5`}>
                  ✓
                </div>
                <p className="text-sm text-[#DADADA] leading-relaxed">
                  {step}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tools Used and Execution Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Tools Used */}
        {toolsUsed.length > 0 && (
          <div className="bg-[#1E1E1F] rounded-xl p-4 border border-[rgba(255,255,255,0.08)]">
            <div className="flex items-center gap-2 mb-3">
              <Award className={`w-5 h-5 ${colors.accent}`} />
              <h4 className={`text-base font-semibold ${colors.accent}`}>
                Herramientas utilizadas:
              </h4>
            </div>
            
            <div className="flex flex-wrap gap-2">
              {toolsUsed.map((tool, index) => (
                <span
                  key={index}
                  className={`px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r ${colors.gradient} ${colors.border} border`}
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Execution Time */}
        {executionTime && (
          <div className="bg-[#1E1E1F] rounded-xl p-4 border border-[rgba(255,255,255,0.08)]">
            <div className="flex items-center gap-2 mb-3">
              <Clock className={`w-5 h-5 ${colors.accent}`} />
              <h4 className={`text-base font-semibold ${colors.accent}`}>
                Tiempo de ejecución:
              </h4>
            </div>
            
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-[#ACACAC]" />
              <span className="text-sm text-[#DADADA]">
                {executionTime}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className={`p-4 bg-gradient-to-r ${colors.gradient} rounded-xl border ${colors.border}`}>
        <div className="flex items-center gap-2 justify-center">
          <div className={`w-2 h-2 ${colors.accent.replace('text-', 'bg-')} rounded-full animate-pulse`}></div>
          <span className={`text-sm font-medium ${colors.accent}`}>
            Tarea finalizada • Puedes continuar con nuevas solicitudes
          </span>
        </div>
      </div>
    </div>
  );
};