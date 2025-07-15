import React, { useState, useEffect } from 'react';
import { ExecutionPlan, ExecutionStatus, agentAPI } from '../../services/api';
import { Play, Pause, Square, RotateCcw, CheckCircle, Clock, AlertCircle, Zap } from 'lucide-react';

interface ExecutionControlPanelProps {
  taskId: string;
  taskTitle: string;
  taskDescription?: string;
  onExecutionStart?: (plan: ExecutionPlan) => void;
  onExecutionComplete?: (status: ExecutionStatus) => void;
  onStatusUpdate?: (status: ExecutionStatus) => void;
}

export const ExecutionControlPanel: React.FC<ExecutionControlPanelProps> = ({
  taskId,
  taskTitle,
  taskDescription = '',
  onExecutionStart,
  onExecutionComplete,
  onStatusUpdate
}) => {
  const [plan, setPlan] = useState<ExecutionPlan | null>(null);
  const [status, setStatus] = useState<ExecutionStatus | null>(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusInterval, setStatusInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    generatePlan();
  }, [taskId, taskTitle, taskDescription]);

  useEffect(() => {
    return () => {
      if (statusInterval) {
        clearInterval(statusInterval);
      }
    };
  }, [statusInterval]);

  const generatePlan = async () => {
    if (!taskId || !taskTitle) return;
    
    setIsGeneratingPlan(true);
    setError(null);
    
    try {
      const result = await agentAPI.generateExecutionPlan(taskId, taskTitle, taskDescription);
      setPlan(result);
      onExecutionStart?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error generating plan');
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const executeTask = async () => {
    if (!taskId || !taskTitle) return;
    
    setIsExecuting(true);
    setError(null);
    
    try {
      await agentAPI.executeTask(taskId, taskTitle, taskDescription);
      startStatusPolling();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error executing task');
      setIsExecuting(false);
    }
  };

  const stopExecution = async () => {
    try {
      await agentAPI.stopTaskExecution(taskId);
      setIsExecuting(false);
      if (statusInterval) {
        clearInterval(statusInterval);
        setStatusInterval(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error stopping execution');
    }
  };

  const startStatusPolling = () => {
    const interval = setInterval(async () => {
      try {
        const newStatus = await agentAPI.getExecutionStatus(taskId);
        setStatus(newStatus);
        onStatusUpdate?.(newStatus);
        
        if (newStatus.status === 'completed' || newStatus.status === 'failed') {
          setIsExecuting(false);
          clearInterval(interval);
          setStatusInterval(null);
          onExecutionComplete?.(newStatus);
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 1000);
    
    setStatusInterval(interval);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'failed': return 'text-red-400';
      case 'running': return 'text-blue-400';
      case 'pending': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'failed': return <AlertCircle className="w-4 h-4" />;
      case 'running': return <Clock className="w-4 h-4 animate-spin" />;
      case 'pending': return <Clock className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (isGeneratingPlan) {
    return (
      <div className="bg-[#383739] rounded-lg p-4 border border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-blue-400 animate-pulse" />
          <h3 className="text-sm font-semibold text-[#DADADA]">Generating Execution Plan...</h3>
        </div>
        <div className="space-y-2">
          <div className="h-4 bg-[#4A4A4C] rounded animate-pulse"></div>
          <div className="h-4 bg-[#4A4A4C] rounded animate-pulse w-3/4"></div>
          <div className="h-4 bg-[#4A4A4C] rounded animate-pulse w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#383739] rounded-lg p-4 border border-red-500/20">
        <div className="flex items-center gap-2 mb-2">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <h3 className="text-sm font-semibold text-red-400">Execution Error</h3>
        </div>
        <p className="text-xs text-red-300 mb-3">{error}</p>
        <button
          onClick={generatePlan}
          className="px-3 py-1 bg-red-500/20 text-red-400 rounded text-xs hover:bg-red-500/30 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!plan) {
    return null;
  }

  return (
    <div className="bg-[#383739] rounded-lg p-4 border border-[rgba(255,255,255,0.08)]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-[#DADADA]">Execution Engine</h3>
        </div>
        <div className="flex items-center gap-2">
          {!isExecuting ? (
            <button
              onClick={executeTask}
              className="flex items-center gap-1 px-3 py-1 bg-green-500/20 text-green-400 rounded text-xs hover:bg-green-500/30 transition-colors"
            >
              <Play className="w-3 h-3" />
              Execute
            </button>
          ) : (
            <button
              onClick={stopExecution}
              className="flex items-center gap-1 px-3 py-1 bg-red-500/20 text-red-400 rounded text-xs hover:bg-red-500/30 transition-colors"
            >
              <Square className="w-3 h-3" />
              Stop
            </button>
          )}
          <button
            onClick={generatePlan}
            disabled={isExecuting}
            className="flex items-center gap-1 px-3 py-1 bg-blue-500/20 text-blue-400 rounded text-xs hover:bg-blue-500/30 transition-colors disabled:opacity-50"
          >
            <RotateCcw className="w-3 h-3" />
            Regenerate
          </button>
        </div>
      </div>

      {/* Plan Overview */}
      <div className="mb-4 p-3 bg-[#4A4A4C] rounded">
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-[#ACACAC]">Steps:</span>
            <span className="text-[#DADADA] ml-2">{plan.steps.length}</span>
          </div>
          <div>
            <span className="text-[#ACACAC]">Estimated Duration:</span>
            <span className="text-[#DADADA] ml-2">{formatDuration(plan.total_estimated_duration)}</span>
          </div>
          <div>
            <span className="text-[#ACACAC]">Success Rate:</span>
            <span className="text-green-400 ml-2">{Math.round(plan.success_probability * 100)}%</span>
          </div>
          <div>
            <span className="text-[#ACACAC]">Complexity:</span>
            <span className="text-yellow-400 ml-2">{plan.complexity_score}/10</span>
          </div>
        </div>
      </div>

      {/* Execution Status */}
      {status && (
        <div className="mb-4 p-3 bg-[#4A4A4C] rounded">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className={getStatusColor(status.status)}>
                {getStatusIcon(status.status)}
              </span>
              <span className="text-xs font-medium text-[#DADADA]">
                Status: <span className={getStatusColor(status.status)}>{status.status}</span>
              </span>
            </div>
            <span className="text-xs text-[#ACACAC]">
              {formatDuration(status.execution_time)}
            </span>
          </div>
          <div className="mb-2">
            <div className="flex justify-between text-xs text-[#ACACAC] mb-1">
              <span>Progress: {status.current_step}/{status.total_steps}</span>
              <span>{Math.round(status.progress * 100)}%</span>
            </div>
            <div className="w-full bg-[#2A2A2A] rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${status.progress * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Steps List */}
      <div className="space-y-2">
        <h4 className="text-xs font-medium text-[#DADADA] mb-2">Execution Steps:</h4>
        <div className="max-h-48 overflow-y-auto space-y-1">
          {plan.steps.map((step, index) => {
            const stepStatus = status?.steps.find(s => s.id === step.id);
            return (
              <div
                key={step.id}
                className={`p-2 rounded text-xs border ${
                  stepStatus?.status === 'completed' ? 'bg-green-500/10 border-green-500/20' :
                  stepStatus?.status === 'running' ? 'bg-blue-500/10 border-blue-500/20' :
                  stepStatus?.status === 'failed' ? 'bg-red-500/10 border-red-500/20' :
                  'bg-[#4A4A4C] border-[rgba(255,255,255,0.08)]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[#ACACAC]">{index + 1}.</span>
                    <span className="text-[#DADADA]">{step.title}</span>
                    {stepStatus && (
                      <span className={getStatusColor(stepStatus.status)}>
                        {getStatusIcon(stepStatus.status)}
                      </span>
                    )}
                  </div>
                  <div className="text-[#ACACAC] text-xs">
                    {formatDuration(step.estimated_duration)}
                  </div>
                </div>
                <div className="text-[#ACACAC] mt-1 text-xs">
                  {step.description}
                </div>
                <div className="flex items-center gap-1 mt-1">
                  <span className="px-1 py-0.5 bg-[#5A5A5C] text-[#DADADA] rounded text-xs">
                    {step.tool}
                  </span>
                  {stepStatus && stepStatus.retry_count > 0 && (
                    <span className="text-yellow-400 text-xs">
                      (Retry #{stepStatus.retry_count})
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Required Tools */}
      <div className="mt-4 pt-3 border-t border-[rgba(255,255,255,0.08)]">
        <h4 className="text-xs font-medium text-[#DADADA] mb-2">Required Tools:</h4>
        <div className="flex flex-wrap gap-1">
          {plan.required_tools.map((tool, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-[#4A4A4C] text-xs text-[#DADADA] rounded"
            >
              {tool}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};