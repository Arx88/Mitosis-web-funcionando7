/**
 * Componente para mostrar el estado del agente en tiempo real
 * Muestra progreso de ejecución, pasos completados y planificación dinámica
 */

import React, { useState, useEffect } from 'react';
import { Bot, CheckCircle, Clock, AlertCircle, RefreshCw, Zap } from 'lucide-react';

interface AgentStep {
  id: string;
  title: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress?: number;
  execution_time?: number;
  retry_count?: number;
  error?: string;
}

interface AgentStatusProps {
  taskId: string;
  isExecuting: boolean;
  currentStep?: string;
  totalSteps?: number;
  completedSteps?: number;
  executionTime?: number;
  successRate?: number;
  steps?: AgentStep[];
  planUpdates?: any[];
  onStepClick?: (stepId: string) => void;
}

export const AgentStatus: React.FC<AgentStatusProps> = ({
  taskId,
  isExecuting,
  currentStep,
  totalSteps = 0,
  completedSteps = 0,
  executionTime = 0,
  successRate = 0,
  steps = [],
  planUpdates = [],
  onStepClick,
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [showPlanHistory, setShowPlanHistory] = useState(false);

  const progress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  const toggleStepExpansion = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'running':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'skipped':
        return <Clock className="w-4 h-4 text-gray-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStepStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 border-green-500/30 text-green-400';
      case 'running':
        return 'bg-blue-500/20 border-blue-500/30 text-blue-400';
      case 'failed':
        return 'bg-red-500/20 border-red-500/30 text-red-400';
      case 'skipped':
        return 'bg-gray-500/20 border-gray-500/30 text-gray-400';
      default:
        return 'bg-gray-600/20 border-gray-600/30 text-gray-400';
    }
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="bg-[#1A1A1A] border border-[rgba(255,255,255,0.08)] rounded-lg p-6 mb-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Bot className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-[#DADADA]">
            {isExecuting ? 'Ejecutando Tarea' : 'Agente Listo'}
          </h3>
          {planUpdates.length > 0 && (
            <div className="flex items-center space-x-1">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-yellow-400">
                {planUpdates.length} actualizaciones
              </span>
            </div>
          )}
        </div>
        <div className="text-sm text-gray-400">
          ID: {taskId.substring(0, 8)}...
        </div>
      </div>

      {/* Progress Bar */}
      {isExecuting && (
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-400">
              Progreso: {completedSteps}/{totalSteps} pasos
            </span>
            <span className="text-sm text-gray-400">
              {formatTime(executionTime)}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Current Step */}
      {currentStep && isExecuting && (
        <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
            <span className="text-sm font-medium text-blue-400">
              Ejecutando: {currentStep}
            </span>
          </div>
        </div>
      )}

      {/* Steps List */}
      {steps.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-[#DADADA]">Pasos de Ejecución</h4>
            <span className="text-xs text-gray-400">
              Tasa de éxito: {Math.round(successRate * 100)}%
            </span>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {steps.map((step) => (
              <div
                key={step.id}
                className={`p-3 rounded-lg border transition-all cursor-pointer ${getStepStatusColor(step.status)}`}
                onClick={() => {
                  toggleStepExpansion(step.id);
                  onStepClick?.(step.id);
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStepIcon(step.status)}
                    <div>
                      <div className="font-medium text-sm">{step.title}</div>
                      <div className="text-xs opacity-70">
                        {step.status === 'running' && step.progress && (
                          <span>Progreso: {Math.round(step.progress * 100)}%</span>
                        )}
                        {step.execution_time && (
                          <span>Tiempo: {formatTime(step.execution_time)}</span>
                        )}
                        {step.retry_count && step.retry_count > 0 && (
                          <span className="ml-2">Reintentos: {step.retry_count}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs opacity-50">
                    {(step.status || 'pending').toUpperCase()}
                  </div>
                </div>
                
                {/* Expanded Details */}
                {expandedSteps.has(step.id) && (
                  <div className="mt-2 pt-2 border-t border-current/20">
                    <div className="text-xs opacity-70">
                      <div>ID: {step.id}</div>
                      {step.error && (
                        <div className="mt-1 text-red-400">
                          Error: {step.error}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Plan Updates */}
      {planUpdates.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-[#DADADA]">Actualizaciones del Plan</h4>
            <button
              onClick={() => setShowPlanHistory(!showPlanHistory)}
              className="text-xs text-yellow-400 hover:text-yellow-300"
            >
              {showPlanHistory ? 'Ocultar' : 'Mostrar'} historial
            </button>
          </div>
          
          {showPlanHistory && (
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {planUpdates.map((update, index) => (
                <div
                  key={index}
                  className="p-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-xs"
                >
                  <div className="flex items-center space-x-2">
                    <Zap className="w-3 h-3 text-yellow-400" />
                    <span className="font-medium text-yellow-400">
                      {update.reason || 'Plan actualizado'}
                    </span>
                  </div>
                  <div className="text-gray-400 mt-1">
                    {update.description || 'Sin descripción'}
                  </div>
                  <div className="text-gray-500 mt-1">
                    {new Date(update.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Status Summary */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="bg-gray-800/50 p-3 rounded-lg">
          <div className="text-gray-400">Estado</div>
          <div className="font-medium text-[#DADADA]">
            {isExecuting ? 'Ejecutando' : 'Listo'}
          </div>
        </div>
        <div className="bg-gray-800/50 p-3 rounded-lg">
          <div className="text-gray-400">Progreso</div>
          <div className="font-medium text-[#DADADA]">
            {Math.round(progress)}%
          </div>
        </div>
      </div>
    </div>
  );
};