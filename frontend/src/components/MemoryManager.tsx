import React, { useState } from 'react';
import { 
  Brain, 
  Trash2, 
  Eye, 
  ArrowUp, 
  ArrowDown, 
  Minus,
  FileText,
  Search,
  Filter,
  X,
  BarChart3,
  AlertCircle,
  Settings
} from 'lucide-react';
import { MemoryFile } from '../hooks/useMemoryManager';
import { MemoryIndicator } from './MemoryIndicator';

interface MemoryManagerProps {
  memoryFiles: MemoryFile[];
  onRemoveFile: (fileId: string) => void;
  onToggleFile: (fileId: string) => void;
  onUpdatePriority: (fileId: string, priority: 'low' | 'medium' | 'high') => void;
  onClearAll: () => void;
  className?: string;
}

export const MemoryManager: React.FC<MemoryManagerProps> = ({
  memoryFiles,
  onRemoveFile,
  onToggleFile,
  onUpdatePriority,
  onClearAll,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'research_report' | 'uploaded_file' | 'agent_file'>('all');
  const [filterPriority, setFilterPriority] = useState<'all' | 'low' | 'medium' | 'high'>('all');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [showPreview, setShowPreview] = useState<string | null>(null);

  // Filter files based on search and filters
  const filteredFiles = memoryFiles.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         file.content.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'all' || file.type === filterType;
    const matchesPriority = filterPriority === 'all' || file.priority === filterPriority;
    
    return matchesSearch && matchesType && matchesPriority;
  });

  // Statistics
  const stats = {
    total: memoryFiles.length,
    active: memoryFiles.filter(f => f.isActive).length,
    totalSize: memoryFiles.reduce((sum, file) => sum + file.metadata.size, 0),
    byType: {
      research_report: memoryFiles.filter(f => f.type === 'research_report').length,
      uploaded_file: memoryFiles.filter(f => f.type === 'uploaded_file').length,
      agent_file: memoryFiles.filter(f => f.type === 'agent_file').length
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getTypeIcon = (type: MemoryFile['type']) => {
    switch (type) {
      case 'research_report':
        return <BarChart3 className="w-4 h-4 text-blue-400" />;
      case 'uploaded_file':
        return <FileText className="w-4 h-4 text-green-400" />;
      case 'agent_file':
        return <Settings className="w-4 h-4 text-purple-400" />;
    }
  };

  const getTypeLabel = (type: MemoryFile['type']) => {
    switch (type) {
      case 'research_report':
        return 'Informe de Investigación';
      case 'uploaded_file':
        return 'Archivo Subido';
      case 'agent_file':
        return 'Archivo del Agente';
    }
  };

  return (
    <div className={`bg-[#1a1a1b] border border-[rgba(255,255,255,0.12)] rounded-lg ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#DADADA]">Memoria RAG</h3>
            <p className="text-sm text-[#ACACAC]">
              {activeFiles.length} archivo{activeFiles.length !== 1 ? 's' : ''} activo{activeFiles.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-[#ACACAC] hover:text-[#DADADA] transition-colors"
        >
          {isExpanded ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
        </button>
      </div>

      {/* Memory Status */}
      <div className="p-4 border-b border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${activeFiles.length > 0 ? 'bg-green-400' : 'bg-gray-400'}`} />
            <span className="text-sm font-medium text-[#DADADA]">
              {activeFiles.length > 0 ? 'Memoria Activa' : 'Sin Memoria'}
            </span>
          </div>
          <span className="text-xs text-[#ACACAC]">
            {formatFileSize(totalMemorySize)}
          </span>
        </div>

        {activeFiles.length > 0 && (
          <div className="bg-[rgba(34,197,94,0.1)] border border-[rgba(34,197,94,0.2)] rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-4 h-4 text-green-400" />
              <span className="text-sm font-medium text-green-400">
                El agente consultará {activeFiles.length} archivo{activeFiles.length !== 1 ? 's' : ''} como conocimiento base
              </span>
            </div>
            <div className="text-xs text-[#ACACAC]">
              Solo activo durante esta sesión
            </div>
          </div>
        )}
      </div>

      {/* Expandible Content */}
      {isExpanded && (
        <div className="p-4">
          {memoryFiles.length === 0 ? (
            <div className="text-center py-8">
              <Brain className="w-16 h-16 text-[#7f7f7f] mx-auto mb-4" />
              <p className="text-[#ACACAC] text-lg mb-2">No hay archivos en memoria</p>
              <p className="text-[#7f7f7f] text-sm">
                Usa el botón "Memoria" en cualquier archivo para agregarlo como conocimiento base
              </p>
            </div>
          ) : (
            <>
              {/* Actions */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-[#ACACAC]">
                  {memoryFiles.length} archivo{memoryFiles.length !== 1 ? 's' : ''} en memoria
                </span>
                {memoryFiles.length > 0 && (
                  <button
                    onClick={onClearAllMemory}
                    className="flex items-center gap-2 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 rounded-lg text-sm text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    Limpiar Todo
                  </button>
                )}
              </div>

              {/* Files List */}
              <div className="space-y-2">
                {memoryFiles.map((file) => (
                  <div
                    key={file.id}
                    className={`p-3 rounded-lg border transition-all ${
                      file.isActive 
                        ? 'bg-[rgba(34,197,94,0.1)] border-[rgba(34,197,94,0.2)]' 
                        : 'bg-[rgba(255,255,255,0.04)] border-[rgba(255,255,255,0.08)]'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="text-lg">{getFileIcon(file.type)}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-sm font-medium text-[#DADADA] truncate">
                              {file.name}
                            </h4>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${getSourceColor(file.source)}`}>
                              {getSourceLabel(file.source)}
                            </span>
                          </div>
                          <p className="text-xs text-[#ACACAC] mb-2 line-clamp-2">
                            {file.summary}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-[#7f7f7f]">
                            <Clock className="w-3 h-3" />
                            <span>{file.addedAt.toLocaleString()}</span>
                            <span>•</span>
                            <span>{formatFileSize(file.size)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 ml-2">
                        <button
                          onClick={() => onToggleMemoryFile(file.id)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                            file.isActive
                              ? 'bg-red-600/20 hover:bg-red-600/30 text-red-400'
                              : 'bg-green-600/20 hover:bg-green-600/30 text-green-400'
                          }`}
                        >
                          {file.isActive ? 'Desactivar' : 'Activar'}
                        </button>
                        <button
                          onClick={() => onRemoveMemoryFile(file.id)}
                          className="p-1.5 hover:bg-red-600/20 rounded-lg text-red-400 transition-colors"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

// Hook para manejar el sistema de memoria
export const useMemoryManager = () => {
  const [memoryFiles, setMemoryFiles] = useState<MemoryFile[]>([]);

  const addMemoryFile = (file: MemoryFile) => {
    setMemoryFiles(prev => {
      // Evitar duplicados
      const exists = prev.some(f => f.id === file.id);
      if (exists) return prev;
      
      return [...prev, file];
    });
  };

  const removeMemoryFile = (id: string) => {
    setMemoryFiles(prev => prev.filter(f => f.id !== id));
  };

  const toggleMemoryFile = (id: string) => {
    setMemoryFiles(prev => prev.map(f => 
      f.id === id ? { ...f, isActive: !f.isActive } : f
    ));
  };

  const clearAllMemory = () => {
    setMemoryFiles([]);
  };

  const getActiveMemoryContext = () => {
    const activeFiles = memoryFiles.filter(f => f.isActive);
    if (activeFiles.length === 0) return '';
    
    return activeFiles.map(f => `
==== MEMORIA: ${f.name} ====
${f.content}
========================
`).join('\n');
  };

  return {
    memoryFiles,
    addMemoryFile,
    removeMemoryFile,
    toggleMemoryFile,
    clearAllMemory,
    getActiveMemoryContext,
    hasActiveMemory: memoryFiles.some(f => f.isActive)
  };
};