import React, { useState, useEffect } from 'react';
import { ContextCheckpoint, agentAPI } from '../../services/api';
import { Save, RotateCcw, Plus, Clock, User, Bot, Trash2, RefreshCw } from 'lucide-react';

interface ContextCheckpointsPanelProps {
  taskId: string;
  onCheckpointRestore?: (checkpointId: string) => void;
  onCheckpointCreate?: (checkpointId: string) => void;
}

export const ContextCheckpointsPanel: React.FC<ContextCheckpointsPanelProps> = ({
  taskId,
  onCheckpointRestore,
  onCheckpointCreate
}) => {
  const [checkpoints, setCheckpoints] = useState<ContextCheckpoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCheckpointDescription, setNewCheckpointDescription] = useState('');
  const [creatingCheckpoint, setCreatingCheckpoint] = useState(false);
  const [restoringCheckpoint, setRestoringCheckpoint] = useState<string | null>(null);

  useEffect(() => {
    if (taskId) {
      loadCheckpoints();
    }
  }, [taskId]);

  const loadCheckpoints = async () => {
    if (!taskId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await agentAPI.getContextCheckpoints(taskId);
      setCheckpoints(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading checkpoints');
    } finally {
      setLoading(false);
    }
  };

  const createCheckpoint = async () => {
    if (!newCheckpointDescription.trim()) return;
    
    setCreatingCheckpoint(true);
    setError(null);
    
    try {
      const result = await agentAPI.createCheckpoint(taskId, newCheckpointDescription);
      setNewCheckpointDescription('');
      setShowCreateForm(false);
      loadCheckpoints();
      onCheckpointCreate?.(result.checkpoint_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creating checkpoint');
    } finally {
      setCreatingCheckpoint(false);
    }
  };

  const restoreCheckpoint = async (checkpointId: string) => {
    setRestoringCheckpoint(checkpointId);
    setError(null);
    
    try {
      await agentAPI.restoreCheckpoint(taskId, checkpointId);
      onCheckpointRestore?.(checkpointId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error restoring checkpoint');
    } finally {
      setRestoringCheckpoint(null);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getRelativeTime = (timestamp: string) => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  const getCheckpointIcon = (checkpoint: ContextCheckpoint) => {
    if (checkpoint.auto_created) {
      return <Bot className="w-4 h-4 text-blue-400" />;
    } else {
      return <User className="w-4 h-4 text-green-400" />;
    }
  };

  return (
    <div className="bg-[#383739] rounded-lg p-4 border border-[rgba(255,255,255,0.08)]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Save className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-[#DADADA]">Context Checkpoints</h3>
          <span className="text-xs text-[#ACACAC]">
            ({checkpoints.length} checkpoints)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadCheckpoints}
            disabled={loading}
            className="p-1 text-[#ACACAC] hover:text-[#DADADA] transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowCreateForm(true)}
            className="p-1 text-[#ACACAC] hover:text-[#DADADA] transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Create Checkpoint Form */}
      {showCreateForm && (
        <div className="mb-4 p-3 bg-[#4A4A4C] rounded border border-[rgba(255,255,255,0.08)]">
          <h4 className="text-xs font-medium text-[#DADADA] mb-2">Create New Checkpoint</h4>
          <div className="space-y-2">
            <textarea
              placeholder="Checkpoint description (optional)"
              value={newCheckpointDescription}
              onChange={(e) => setNewCheckpointDescription(e.target.value)}
              className="w-full text-xs bg-[#5A5A5C] text-[#DADADA] border border-[rgba(255,255,255,0.08)] rounded px-2 py-1 h-20 resize-none"
            />
            <div className="flex gap-2">
              <button
                onClick={createCheckpoint}
                disabled={creatingCheckpoint}
                className="px-3 py-1 bg-green-500/20 text-green-400 rounded text-xs hover:bg-green-500/30 transition-colors disabled:opacity-50"
              >
                {creatingCheckpoint ? 'Creating...' : 'Create'}
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                className="px-3 py-1 bg-red-500/20 text-red-400 rounded text-xs hover:bg-red-500/30 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-2 bg-red-500/10 border border-red-500/20 rounded">
          <p className="text-red-400 text-xs">{error}</p>
        </div>
      )}

      {/* Checkpoints List */}
      <div className="space-y-2">
        {loading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-[#4A4A4C] rounded animate-pulse" />
            ))}
          </div>
        ) : checkpoints.length === 0 ? (
          <div className="text-[#ACACAC] text-xs p-4 text-center">
            No checkpoints found. Create your first checkpoint to save the current state.
          </div>
        ) : (
          <div className="max-h-80 overflow-y-auto space-y-2">
            {checkpoints.map((checkpoint) => (
              <div
                key={checkpoint.checkpoint_id}
                className="p-3 bg-[#4A4A4C] rounded border border-[rgba(255,255,255,0.08)] hover:border-[rgba(255,255,255,0.12)] transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {getCheckpointIcon(checkpoint)}
                      <span className="text-xs font-medium text-[#DADADA]">
                        {checkpoint.step_id}
                      </span>
                      <span className="text-xs text-[#ACACAC]">
                        {checkpoint.auto_created ? 'Auto' : 'Manual'}
                      </span>
                    </div>
                    
                    {checkpoint.description && (
                      <p className="text-xs text-[#ACACAC] mb-2">
                        {checkpoint.description}
                      </p>
                    )}
                    
                    <div className="flex items-center gap-4 text-xs text-[#7f7f7f]">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{getRelativeTime(checkpoint.timestamp)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span>{checkpoint.variables_count} variables</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-1 ml-2">
                    <button
                      onClick={() => restoreCheckpoint(checkpoint.checkpoint_id)}
                      disabled={restoringCheckpoint === checkpoint.checkpoint_id}
                      className="p-1 text-[#ACACAC] hover:text-blue-400 transition-colors disabled:opacity-50"
                      title="Restore checkpoint"
                    >
                      <RotateCcw className={`w-3 h-3 ${
                        restoringCheckpoint === checkpoint.checkpoint_id ? 'animate-spin' : ''
                      }`} />
                    </button>
                  </div>
                </div>
                
                <div className="mt-2 text-xs text-[#7f7f7f]">
                  <span className="font-mono">
                    {checkpoint.checkpoint_id.slice(-12)}
                  </span>
                  <span className="mx-2">•</span>
                  <span>{formatTimestamp(checkpoint.timestamp)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Quick Actions */}
      <div className="mt-4 pt-3 border-t border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center justify-between">
          <span className="text-xs text-[#ACACAC]">
            Checkpoints are automatically created during task execution
          </span>
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center gap-1 px-3 py-1 bg-blue-500/20 text-blue-400 rounded text-xs hover:bg-blue-500/30 transition-colors"
          >
            <Plus className="w-3 h-3" />
            Create Manual
          </button>
        </div>
      </div>
    </div>
  );
};