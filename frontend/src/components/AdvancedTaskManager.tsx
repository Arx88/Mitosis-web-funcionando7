import React, { useState, useEffect } from 'react';
import { TaskAnalysisPanel } from './ExecutionEngine/TaskAnalysisPanel';
import { ExecutionControlPanel } from './ExecutionEngine/ExecutionControlPanel';
import { ContextVariablesPanel } from './ContextManager/ContextVariablesPanel';
import { ContextCheckpointsPanel } from './ContextManager/ContextCheckpointsPanel';
import { TaskAnalysis, ExecutionPlan, ExecutionStatus } from '../services/api';
import { Zap, Database, Settings, ChevronDown, ChevronUp } from 'lucide-react';

interface AdvancedTaskManagerProps {
  taskId: string;
  taskTitle: string;
  taskDescription?: string;
  isVisible?: boolean;
  onTaskUpdate?: (taskData: any) => void;
}

export const AdvancedTaskManager: React.FC<AdvancedTaskManagerProps> = ({
  taskId,
  taskTitle,
  taskDescription = '',
  isVisible = true,
  onTaskUpdate
}) => {
  const [activeTab, setActiveTab] = useState<'analysis' | 'execution' | 'variables' | 'checkpoints'>('analysis');
  const [isExpanded, setIsExpanded] = useState(false);
  const [taskAnalysis, setTaskAnalysis] = useState<TaskAnalysis | null>(null);
  const [executionPlan, setExecutionPlan] = useState<ExecutionPlan | null>(null);
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus | null>(null);
  const [contextVariables, setContextVariables] = useState<Record<string, any>>({});

  useEffect(() => {
    if (taskId && taskTitle) {
      // Reset state when task changes
      setTaskAnalysis(null);
      setExecutionPlan(null);
      setExecutionStatus(null);
      setContextVariables({});
    }
  }, [taskId, taskTitle]);

  const handleAnalysisComplete = (analysis: TaskAnalysis) => {
    setTaskAnalysis(analysis);
    onTaskUpdate?.({ analysis });
  };

  const handleExecutionStart = (plan: ExecutionPlan) => {
    setExecutionPlan(plan);
    setActiveTab('execution');
    onTaskUpdate?.({ plan });
  };

  const handleExecutionComplete = (status: ExecutionStatus) => {
    setExecutionStatus(status);
    onTaskUpdate?.({ status });
  };

  const handleStatusUpdate = (status: ExecutionStatus) => {
    setExecutionStatus(status);
    onTaskUpdate?.({ status });
  };

  const handleVariableUpdate = (variables: Record<string, any>) => {
    setContextVariables(variables);
    onTaskUpdate?.({ variables });
  };

  const handleCheckpointRestore = (checkpointId: string) => {
    // Refresh variables and status when checkpoint is restored
    onTaskUpdate?.({ checkpointRestored: checkpointId });
  };

  const handleCheckpointCreate = (checkpointId: string) => {
    onTaskUpdate?.({ checkpointCreated: checkpointId });
  };

  if (!isVisible) {
    return null;
  }

  const tabs = [
    { id: 'analysis', label: 'Analysis', icon: Settings },
    { id: 'execution', label: 'Execution', icon: Zap },
    { id: 'variables', label: 'Variables', icon: Database },
    { id: 'checkpoints', label: 'Checkpoints', icon: Database }
  ];

  return (
    <div className="bg-[#272728] border border-[rgba(255,255,255,0.08)] rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-3 bg-[#383739] border-b border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-blue-400" />
          <h2 className="text-sm font-semibold text-[#DADADA]">Advanced Task Manager</h2>
          <span className="text-xs text-[#ACACAC] font-mono">
            {taskId.slice(-8)}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Status Indicators */}
          <div className="flex items-center gap-2 text-xs">
            {taskAnalysis && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-[#ACACAC]">Analyzed</span>
              </div>
            )}
            {executionPlan && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span className="text-[#ACACAC]">Planned</span>
              </div>
            )}
            {executionStatus && (
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${
                  executionStatus.status === 'completed' ? 'bg-green-400' :
                  executionStatus.status === 'failed' ? 'bg-red-400' :
                  executionStatus.status === 'running' ? 'bg-yellow-400' :
                  'bg-gray-400'
                }`}></div>
                <span className="text-[#ACACAC]">
                  {executionStatus.status}
                </span>
              </div>
            )}
          </div>
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-[#ACACAC] hover:text-[#DADADA] transition-colors"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <>
          {/* Tab Navigation */}
          <div className="flex border-b border-[rgba(255,255,255,0.08)] bg-[#383739]">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 text-xs font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'text-blue-400 border-b-2 border-blue-400 bg-[#4A4A4C]'
                    : 'text-[#ACACAC] hover:text-[#DADADA] hover:bg-[#4A4A4C]'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="p-4">
            {activeTab === 'analysis' && (
              <TaskAnalysisPanel
                taskTitle={taskTitle}
                taskDescription={taskDescription}
                onAnalysisComplete={handleAnalysisComplete}
              />
            )}

            {activeTab === 'execution' && (
              <ExecutionControlPanel
                taskId={taskId}
                taskTitle={taskTitle}
                taskDescription={taskDescription}
                onExecutionStart={handleExecutionStart}
                onExecutionComplete={handleExecutionComplete}
                onStatusUpdate={handleStatusUpdate}
              />
            )}

            {activeTab === 'variables' && (
              <ContextVariablesPanel
                taskId={taskId}
                onVariableUpdate={handleVariableUpdate}
              />
            )}

            {activeTab === 'checkpoints' && (
              <ContextCheckpointsPanel
                taskId={taskId}
                onCheckpointRestore={handleCheckpointRestore}
                onCheckpointCreate={handleCheckpointCreate}
              />
            )}
          </div>
        </>
      )}

      {/* Collapsed Summary */}
      {!isExpanded && (
        <div className="p-3 bg-[#383739]">
          <div className="grid grid-cols-4 gap-4 text-xs">
            <div className="text-center">
              <div className="text-[#ACACAC]">Status</div>
              <div className="text-[#DADADA]">
                {executionStatus ? executionStatus.status : 'Ready'}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[#ACACAC]">Progress</div>
              <div className="text-[#DADADA]">
                {executionStatus ? `${Math.round(executionStatus.progress * 100)}%` : '0%'}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[#ACACAC]">Variables</div>
              <div className="text-[#DADADA]">
                {Object.keys(contextVariables).length}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[#ACACAC]">Success Rate</div>
              <div className="text-[#DADADA]">
                {taskAnalysis ? `${Math.round(taskAnalysis.success_probability * 100)}%` : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};