import React, { useState, useEffect } from 'react';
import { CheckCircle, Circle, AlertCircle, Clock, Zap, Activity, Cpu, Timer, Target, TrendingUp } from 'lucide-react';
import { OrchestrationStatus, OrchestrationResult, agentAPI } from '../services/api';

interface OrchestrationProgressProps {
  taskId: string;
  initialStatus?: OrchestrationStatus;
  onComplete?: (result: OrchestrationResult) => void;
  onError?: (error: string) => void;
}

export const OrchestrationProgress: React.FC<OrchestrationProgressProps> = ({
  taskId,
  initialStatus,
  onComplete,
  onError
}) => {
  const [status, setStatus] = useState<OrchestrationStatus | null>(initialStatus || null);
  const [isPolling, setIsPolling] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startTime] = useState(Date.now());

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (isPolling && taskId) {
      intervalId = setInterval(async () => {
        try {
          const currentStatus = await agentAPI.getOrchestrationStatus(taskId);
          setStatus(currentStatus);

          // Stop polling if task is completed or failed
          if (currentStatus.status === 'completed' || currentStatus.status === 'failed') {
            setIsPolling(false);
            if (currentStatus.status === 'completed' && onComplete) {
              // Get final result
              try {
                const result = await agentAPI.getTaskStatus(taskId);
                onComplete(result);
              } catch (err) {
                console.error('Error getting final result:', err);
              }
            }
          }
        } catch (err) {
          console.error('Error polling orchestration status:', err);
          setError(err instanceof Error ? err.message : 'Unknown error');
          setIsPolling(false);
          if (onError) {
            onError(err instanceof Error ? err.message : 'Unknown error');
          }
        }
      }, 1000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [taskId, isPolling, onComplete, onError]);

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-4">
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span className="font-medium">Error en Orquestación</span>
        </div>
        <p className="text-red-300 mt-2">{error}</p>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mb-4">
        <div className="flex items-center gap-2 text-blue-400">
          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
          <span>Iniciando orquestación...</span>
        </div>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'planning':
        return <Activity className="w-5 h-5 text-yellow-400 animate-pulse" />;
      case 'executing':
        return <Zap className="w-5 h-5 text-blue-400 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      case 'cancelled':
        return <Circle className="w-5 h-5 text-gray-400" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planning':
        return 'yellow';
      case 'executing':
        return 'blue';
      case 'completed':
        return 'green';
      case 'failed':
        return 'red';
      case 'cancelled':
        return 'gray';
      default:
        return 'gray';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'planning':
        return 'Planificando Tarea';
      case 'executing':
        return 'Ejecutando Plan';
      case 'completed':
        return 'Completado';
      case 'failed':
        return 'Falló';
      case 'cancelled':
        return 'Cancelado';
      default:
        return 'Estado Desconocido';
    }
  };

  const formatTime = (milliseconds: number) => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const color = getStatusColor(status.status);
  const elapsedTime = Date.now() - startTime;

  return (
    <div className={`bg-${color}-500/10 border border-${color}-500/20 rounded-lg p-4 mb-4`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {getStatusIcon(status.status)}
          <span className={`text-${color}-400 font-medium`}>
            {getStatusText(status.status)}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Timer className="w-4 h-4" />
          {formatTime(elapsedTime)}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm text-gray-300">Progreso</span>
          <span className="text-sm text-gray-300">{Math.round(status.progress)}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className={`bg-${color}-500 h-2 rounded-full transition-all duration-300`}
            style={{ width: `${status.progress}%` }}
          />
        </div>
      </div>

      {/* Current Step */}
      {status.current_step && (
        <div className="mb-3">
          <div className="flex items-center gap-2 text-sm">
            <Target className="w-4 h-4 text-gray-400" />
            <span className="text-gray-300">Paso Actual:</span>
            <span className={`text-${color}-400`}>{status.current_step}</span>
          </div>
          {status.total_steps && (
            <div className="flex items-center gap-2 text-sm mt-1">
              <TrendingUp className="w-4 h-4 text-gray-400" />
              <span className="text-gray-300">
                Paso {status.total_steps - Math.floor((1 - status.progress / 100) * status.total_steps)} de {status.total_steps}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Task ID */}
      <div className="text-xs text-gray-500 border-t border-gray-600 pt-2">
        Task ID: {taskId}
      </div>
    </div>
  );
};