import React, { useState, useEffect } from 'react';
import { ContextInfo, ContextVariable, agentAPI } from '../../services/api';
import { Database, Eye, EyeOff, Plus, Edit, Trash2, RefreshCw, Settings, Code, Hash, Type, List } from 'lucide-react';

interface ContextVariablesPanelProps {
  taskId: string;
  onVariableUpdate?: (variables: Record<string, any>) => void;
}

export const ContextVariablesPanel: React.FC<ContextVariablesPanelProps> = ({
  taskId,
  onVariableUpdate
}) => {
  const [contextInfo, setContextInfo] = useState<ContextInfo | null>(null);
  const [variables, setVariables] = useState<Record<string, any>>({});
  const [selectedScope, setSelectedScope] = useState<string>('all');
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newVariable, setNewVariable] = useState({
    key: '',
    value: '',
    type: 'string',
    scope: 'task'
  });

  useEffect(() => {
    if (taskId) {
      loadContextInfo();
      loadVariables();
    }
  }, [taskId]);

  const loadContextInfo = async () => {
    try {
      const info = await agentAPI.getContextInfo(taskId);
      setContextInfo(info);
    } catch (err) {
      console.error('Error loading context info:', err);
    }
  };

  const loadVariables = async () => {
    if (!taskId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const scope = selectedScope === 'all' ? undefined : selectedScope;
      const result = await agentAPI.getContextVariables(taskId, scope);
      setVariables(result);
      onVariableUpdate?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading variables');
    } finally {
      setLoading(false);
    }
  };

  const addVariable = async () => {
    if (!newVariable.key || !newVariable.value) return;
    
    try {
      let parsedValue = newVariable.value;
      
      // Parse value based on type
      if (newVariable.type === 'number') {
        parsedValue = parseFloat(newVariable.value);
      } else if (newVariable.type === 'boolean') {
        parsedValue = newVariable.value.toLowerCase() === 'true';
      } else if (newVariable.type === 'object' || newVariable.type === 'list') {
        parsedValue = JSON.parse(newVariable.value);
      }
      
      await agentAPI.setContextVariable(
        taskId,
        newVariable.key,
        parsedValue,
        newVariable.type,
        newVariable.scope
      );
      
      setNewVariable({ key: '', value: '', type: 'string', scope: 'task' });
      setShowAddForm(false);
      loadVariables();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error adding variable');
    }
  };

  const formatValue = (value: any, type: string) => {
    if (value === null || value === undefined) return 'null';
    if (type === 'object' || type === 'list') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'string': return <Type className="w-4 h-4 text-green-400" />;
      case 'number': return <Hash className="w-4 h-4 text-blue-400" />;
      case 'boolean': return <Settings className="w-4 h-4 text-yellow-400" />;
      case 'object': return <Code className="w-4 h-4 text-purple-400" />;
      case 'list': return <List className="w-4 h-4 text-orange-400" />;
      default: return <Database className="w-4 h-4 text-gray-400" />;
    }
  };

  const getScopeColor = (scope: string) => {
    switch (scope) {
      case 'task': return 'text-blue-400';
      case 'step': return 'text-green-400';
      case 'global': return 'text-purple-400';
      case 'temporary': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  if (!contextInfo && !loading) {
    return (
      <div className="bg-[#383739] rounded-lg p-4 border border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center gap-2 text-[#ACACAC]">
          <Database className="w-5 h-5" />
          <span className="text-sm">No context available</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#383739] rounded-lg p-4 border border-[rgba(255,255,255,0.08)]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-[#DADADA]">Context Variables</h3>
          {contextInfo && (
            <span className="text-xs text-[#ACACAC]">
              ({contextInfo.variables_count} variables)
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-[#ACACAC] hover:text-[#DADADA] transition-colors"
          >
            {isExpanded ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
          <button
            onClick={loadVariables}
            disabled={loading}
            className="p-1 text-[#ACACAC] hover:text-[#DADADA] transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowAddForm(true)}
            className="p-1 text-[#ACACAC] hover:text-[#DADADA] transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Context Info Summary */}
      {contextInfo && (
        <div className="mb-4 p-3 bg-[#4A4A4C] rounded">
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-[#ACACAC]">Session ID:</span>
              <span className="text-[#DADADA] ml-2 font-mono text-xs">
                {contextInfo.session_id.slice(-8)}
              </span>
            </div>
            <div>
              <span className="text-[#ACACAC]">Status:</span>
              <span className={`ml-2 ${contextInfo.is_active ? 'text-green-400' : 'text-red-400'}`}>
                {contextInfo.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div>
              <span className="text-[#ACACAC]">Checkpoints:</span>
              <span className="text-[#DADADA] ml-2">{contextInfo.checkpoints_count}</span>
            </div>
            <div>
              <span className="text-[#ACACAC]">Last Access:</span>
              <span className="text-[#DADADA] ml-2">
                {new Date(contextInfo.last_accessed).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Scope Filter */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs text-[#ACACAC]">Scope:</span>
          <select
            value={selectedScope}
            onChange={(e) => {
              setSelectedScope(e.target.value);
              setTimeout(loadVariables, 100);
            }}
            className="text-xs bg-[#4A4A4C] text-[#DADADA] border border-[rgba(255,255,255,0.08)] rounded px-2 py-1"
          >
            <option value="all">All Scopes</option>
            <option value="task">Task</option>
            <option value="step">Step</option>
            <option value="global">Global</option>
            <option value="temporary">Temporary</option>
          </select>
        </div>
      </div>

      {/* Add Variable Form */}
      {showAddForm && (
        <div className="mb-4 p-3 bg-[#4A4A4C] rounded border border-[rgba(255,255,255,0.08)]">
          <h4 className="text-xs font-medium text-[#DADADA] mb-2">Add New Variable</h4>
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <input
                type="text"
                placeholder="Key"
                value={newVariable.key}
                onChange={(e) => setNewVariable({...newVariable, key: e.target.value})}
                className="text-xs bg-[#5A5A5C] text-[#DADADA] border border-[rgba(255,255,255,0.08)] rounded px-2 py-1"
              />
              <select
                value={newVariable.type}
                onChange={(e) => setNewVariable({...newVariable, type: e.target.value})}
                className="text-xs bg-[#5A5A5C] text-[#DADADA] border border-[rgba(255,255,255,0.08)] rounded px-2 py-1"
              >
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="boolean">Boolean</option>
                <option value="object">Object</option>
                <option value="list">List</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <textarea
                placeholder="Value"
                value={newVariable.value}
                onChange={(e) => setNewVariable({...newVariable, value: e.target.value})}
                className="text-xs bg-[#5A5A5C] text-[#DADADA] border border-[rgba(255,255,255,0.08)] rounded px-2 py-1 h-20 resize-none"
              />
              <select
                value={newVariable.scope}
                onChange={(e) => setNewVariable({...newVariable, scope: e.target.value})}
                className="text-xs bg-[#5A5A5C] text-[#DADADA] border border-[rgba(255,255,255,0.08)] rounded px-2 py-1"
              >
                <option value="task">Task</option>
                <option value="step">Step</option>
                <option value="global">Global</option>
                <option value="temporary">Temporary</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button
                onClick={addVariable}
                className="px-3 py-1 bg-green-500/20 text-green-400 rounded text-xs hover:bg-green-500/30 transition-colors"
              >
                Add
              </button>
              <button
                onClick={() => setShowAddForm(false)}
                className="px-3 py-1 bg-red-500/20 text-red-400 rounded text-xs hover:bg-red-500/30 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Variables List */}
      {isExpanded && (
        <div className="space-y-2">
          {loading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 bg-[#4A4A4C] rounded animate-pulse" />
              ))}
            </div>
          ) : error ? (
            <div className="text-red-400 text-xs p-2 bg-red-500/10 rounded">
              {error}
            </div>
          ) : Object.keys(variables).length === 0 ? (
            <div className="text-[#ACACAC] text-xs p-2 text-center">
              No variables found in selected scope
            </div>
          ) : (
            <div className="max-h-64 overflow-y-auto space-y-2">
              {Object.entries(variables).map(([key, value]) => (
                <div key={key} className="p-2 bg-[#4A4A4C] rounded border border-[rgba(255,255,255,0.08)]">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      {getTypeIcon(typeof value)}
                      <span className="text-xs font-medium text-[#DADADA]">{key}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-[#ACACAC]">
                        {typeof value}
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-[#ACACAC] font-mono bg-[#2A2A2A] p-2 rounded max-h-20 overflow-y-auto">
                    {formatValue(value, typeof value)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};