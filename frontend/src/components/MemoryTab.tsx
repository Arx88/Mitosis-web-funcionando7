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
  Settings,
  Clock,
  Plus
} from 'lucide-react';
import { MemoryFile } from '../hooks/useMemoryManager';

interface MemoryTabProps {
  memoryFiles: MemoryFile[];
  onAddMemoryFile?: (file: MemoryFile) => void;
  onRemoveMemoryFile?: (id: string) => void;
  onToggleMemoryFile?: (id: string) => void;
  onClearAllMemory?: () => void;
  className?: string;
}

export const MemoryTab: React.FC<MemoryTabProps> = ({
  memoryFiles,
  onAddMemoryFile,
  onRemoveMemoryFile,
  onToggleMemoryFile,
  onClearAllMemory,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'research_report' | 'uploaded_file' | 'agent_file'>('all');
  const [isExpanded, setIsExpanded] = useState(true);

  // Filter files based on search and filters
  const filteredFiles = memoryFiles.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         file.content.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'all' || file.type === filterType;
    
    return matchesSearch && matchesType;
  });

  // Statistics
  const activeFiles = memoryFiles.filter(f => f.isActive);
  const totalMemorySize = memoryFiles.reduce((sum, file) => sum + file.metadata.size, 0);

  const stats = {
    total: memoryFiles.length,
    active: activeFiles.length,
    totalSize: totalMemorySize,
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

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'deep_research':
        return 'bg-blue-500/20 text-blue-300';
      case 'file_upload':
        return 'bg-green-500/20 text-green-300';
      case 'agent_generated':
        return 'bg-purple-500/20 text-purple-300';
      default:
        return 'bg-gray-500/20 text-gray-300';
    }
  };

  const getSourceLabel = (source: string) => {
    switch (source) {
      case 'deep_research':
        return 'Deep Research';
      case 'file_upload':
        return 'Archivo Subido';
      case 'agent_generated':
        return 'Generado por Agente';
      default:
        return 'Desconocido';
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
              {/* Search and Filters */}
              <div className="flex items-center gap-3 mb-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#7f7f7f]" />
                  <input
                    type="text"
                    placeholder="Buscar en memoria..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-[#272728] rounded-lg pl-10 pr-4 py-2 text-sm text-[#DADADA] placeholder-[#7f7f7f] focus:outline-none focus:ring-2 focus:ring-green-500/50"
                  />
                </div>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value as any)}
                  className="bg-[#272728] rounded-lg px-3 py-2 text-sm text-[#DADADA] focus:outline-none focus:ring-2 focus:ring-green-500/50"
                >
                  <option value="all">Todos los tipos</option>
                  <option value="research_report">Informes</option>
                  <option value="uploaded_file">Archivos subidos</option>
                  <option value="agent_file">Archivos del agente</option>
                </select>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-[#ACACAC]">
                  {filteredFiles.length} de {memoryFiles.length} archivo{memoryFiles.length !== 1 ? 's' : ''} en memoria
                </span>
                {memoryFiles.length > 0 && (
                  <button
                    onClick={() => onClearAllMemory?.()}
                    className="flex items-center gap-2 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 rounded-lg text-sm text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    Limpiar Todo
                  </button>
                )}
              </div>

              {/* Files List */}
              <div className="space-y-2">
                {filteredFiles.map((file) => (
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
                        <div className="text-lg">{getTypeIcon(file.type)}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-sm font-medium text-[#DADADA] truncate">
                              {file.name}
                            </h4>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${getSourceColor(file.metadata.source)}`}>
                              {getSourceLabel(file.metadata.source)}
                            </span>
                          </div>
                          <p className="text-xs text-[#ACACAC] mb-2 line-clamp-2">
                            {file.metadata.summary || file.content.substring(0, 100) + '...'}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-[#7f7f7f]">
                            <Clock className="w-3 h-3" />
                            <span>{formatDate(file.metadata.createdAt)}</span>
                            <span>•</span>
                            <span>{formatFileSize(file.metadata.size)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 ml-2">
                        <button
                          onClick={() => onToggleMemoryFile?.(file.id)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                            file.isActive
                              ? 'bg-red-600/20 hover:bg-red-600/30 text-red-400'
                              : 'bg-green-600/20 hover:bg-green-600/30 text-green-400'
                          }`}
                        >
                          {file.isActive ? 'Desactivar' : 'Activar'}
                        </button>
                        <button
                          onClick={() => onRemoveMemoryFile?.(file.id)}
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