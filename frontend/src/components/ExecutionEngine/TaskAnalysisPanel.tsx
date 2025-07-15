import React, { useState, useEffect } from 'react';
import { TaskAnalysis, agentAPI } from '../../services/api';
import { Brain, Clock, Zap, AlertTriangle, CheckCircle, Target } from 'lucide-react';

interface TaskAnalysisPanelProps {
  taskTitle: string;
  taskDescription?: string;
  onAnalysisComplete?: (analysis: TaskAnalysis) => void;
}

export const TaskAnalysisPanel: React.FC<TaskAnalysisPanelProps> = ({
  taskTitle,
  taskDescription = '',
  onAnalysisComplete
}) => {
  const [analysis, setAnalysis] = useState<TaskAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (taskTitle) {
      analyzeTask();
    }
  }, [taskTitle, taskDescription]);

  const analyzeTask = async () => {
    if (!taskTitle) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await agentAPI.analyzeTask(taskTitle, taskDescription);
      setAnalysis(result);
      onAnalysisComplete?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error analyzing task');
    } finally {
      setLoading(false);
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'low': return 'text-green-400';
      case 'medium': return 'text-yellow-400';
      case 'high': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getSuccessColor = (probability: number) => {
    if (probability >= 0.8) return 'text-green-400';
    if (probability >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (loading) {
    return (
      <div className="bg-[#383739] rounded-lg p-4 border border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-blue-400 animate-pulse" />
          <h3 className="text-sm font-semibold text-[#DADADA]">Analyzing Task...</h3>
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
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <h3 className="text-sm font-semibold text-red-400">Analysis Error</h3>
        </div>
        <p className="text-xs text-red-300">{error}</p>
        <button
          onClick={analyzeTask}
          className="mt-2 px-3 py-1 bg-red-500/20 text-red-400 rounded text-xs hover:bg-red-500/30 transition-colors"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  if (!analysis) {
    return null;
  }

  return (
    <div className="bg-[#383739] rounded-lg p-4 border border-[rgba(255,255,255,0.08)]">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-5 h-5 text-blue-400" />
        <h3 className="text-sm font-semibold text-[#DADADA]">Task Analysis</h3>
        <span className="text-xs text-[#7f7f7f]">
          {new Date(analysis.analysis_timestamp).toLocaleTimeString()}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-medium text-[#DADADA]">Type:</span>
            <span className="text-xs text-purple-400 capitalize">{analysis.task_type}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Zap className={`w-4 h-4 ${getComplexityColor(analysis.complexity)}`} />
            <span className="text-xs font-medium text-[#DADADA]">Complexity:</span>
            <span className={`text-xs capitalize ${getComplexityColor(analysis.complexity)}`}>
              {analysis.complexity}
            </span>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            <span className="text-xs font-medium text-[#DADADA]">Duration:</span>
            <span className="text-xs text-blue-400">{formatDuration(analysis.estimated_duration)}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <CheckCircle className={`w-4 h-4 ${getSuccessColor(analysis.success_probability)}`} />
            <span className="text-xs font-medium text-[#DADADA]">Success:</span>
            <span className={`text-xs ${getSuccessColor(analysis.success_probability)}`}>
              {Math.round(analysis.success_probability * 100)}%
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <h4 className="text-xs font-medium text-[#DADADA] mb-1">Required Tools:</h4>
          <div className="flex flex-wrap gap-1">
            {analysis.required_tools.map((tool, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-[#4A4A4C] text-xs text-[#DADADA] rounded"
              >
                {tool}
              </span>
            ))}
          </div>
        </div>

        {analysis.risk_factors && analysis.risk_factors.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-[#DADADA] mb-1">Risk Factors:</h4>
            <div className="space-y-1">
              {analysis.risk_factors.map((risk, index) => (
                <div key={index} className="flex items-start gap-2">
                  <AlertTriangle className="w-3 h-3 text-yellow-400 mt-0.5 flex-shrink-0" />
                  <span className="text-xs text-yellow-300">{risk}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};