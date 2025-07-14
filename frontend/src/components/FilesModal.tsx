import React, { useState, useEffect } from 'react';
import { X, Download, FileText, Image, Video, Music, Archive, CheckSquare, Square, Trash2, Bot, User, Upload, Brain } from 'lucide-react';
import { MemoryTab } from './MemoryTab';
import { MemoryFile } from '../hooks/useMemoryManager';

interface FileItem {
  id: string;
  name: string;
  path: string;
  size: number;
  type: 'file' | 'directory';
  mime_type?: string;
  created_at: string;
  source?: 'agent' | 'uploaded'; // Nuevo campo para diferenciar origen
}

interface FilesModalProps {
  isOpen: boolean;
  onClose: () => void;
  files: FileItem[];
  onDownload: (file: FileItem) => void;
  onDownloadAll: () => void;
  onDownloadSelected?: (files: FileItem[]) => void;
  taskTitle: string;
  memoryFiles?: MemoryFile[];
  onAddMemoryFile?: (file: MemoryFile) => void;
  onRemoveMemoryFile?: (id: string) => void;
  onToggleMemoryFile?: (id: string) => void;
  onClearAllMemory?: () => void;
  onAddFileToMemory?: (file: FileItem) => void;
}

export const FilesModal: React.FC<FilesModalProps> = ({
  isOpen,
  onClose,
  files,
  onDownload,
  onDownloadAll,
  onDownloadSelected,
  taskTitle,
  memoryFiles = [],
  onAddMemoryFile,
  onRemoveMemoryFile,
  onToggleMemoryFile,
  onClearAllMemory,
  onAddFileToMemory
}) => {
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [isAllSelected, setIsAllSelected] = useState(false);
  const [activeTab, setActiveTab] = useState<'agent' | 'uploaded' | 'memory'>('agent');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset selection when files change or modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedFiles(new Set());
      setIsAllSelected(false);
      setError(null);
    }
  }, [isOpen, files]);

  // Filter files based on active tab with better error handling
  const filteredFiles = React.useMemo(() => {
    if (!Array.isArray(files)) {
      console.warn('Files prop is not an array:', files);
      return [];
    }

    return files.filter(file => {
      if (!file || typeof file !== 'object') {
        console.warn('Invalid file object:', file);
        return false;
      }

      if (activeTab === 'agent') {
        return !file.source || file.source === 'agent';
      } else if (activeTab === 'uploaded') {
        return file.source === 'uploaded';
      }
      return false; // Memory tab doesn't filter regular files
    });
  }, [files, activeTab]);

  // Update "select all" state when individual selections change
  useEffect(() => {
    setIsAllSelected(selectedFiles.size === filteredFiles.length && filteredFiles.length > 0);
  }, [selectedFiles, filteredFiles]);

  if (!isOpen) return null;

  const toggleFileSelection = (fileId: string) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId);
    } else {
      newSelected.add(fileId);
    }
    setSelectedFiles(newSelected);
  };

  const toggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(filteredFiles.map(f => f.id)));
    }
  };

  const handleDownloadSelected = async () => {
    if (selectedFiles.size === 0) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const selectedFileObjects = filteredFiles.filter(f => selectedFiles.has(f.id));
      
      if (selectedFiles.size === 1) {
        // Si solo hay un archivo seleccionado, descargarlo directamente
        await onDownload(selectedFileObjects[0]);
      } else {
        // Si hay múltiples archivos, usar la función de descarga múltiple
        if (onDownloadSelected) {
          await onDownloadSelected(selectedFileObjects);
        } else {
          // Fallback: descargar cada archivo individualmente
          for (const file of selectedFileObjects) {
            await onDownload(file);
          }
        }
      }
    } catch (err) {
      console.error('Error downloading files:', err);
      setError('Error al descargar archivos. Por favor, inténtalo de nuevo.');
    } finally {
      setIsLoading(false);
    }
  };

  const clearSelection = () => {
    setSelectedFiles(new Set());
  };

  const getFileIcon = (file: FileItem) => {
    if (!file) return <FileText className="w-4 h-4 text-gray-400" />;
    
    if (file.type === 'directory') {
      return <Archive className="w-4 h-4 text-yellow-500" />;
    }
    
    const mimeType = file.mime_type || '';
    
    if (mimeType.startsWith('image/')) {
      return <Image className="w-4 h-4 text-green-500" />;
    } else if (mimeType.startsWith('video/')) {
      return <Video className="w-4 h-4 text-blue-500" />;
    } else if (mimeType.startsWith('audio/')) {
      return <Music className="w-4 h-4 text-purple-500" />;
    } else if (mimeType.includes('pdf')) {
      return <FileText className="w-4 h-4 text-red-500" />;
    } else if (mimeType.includes('text') || mimeType.includes('json')) {
      return <FileText className="w-4 h-4 text-blue-400" />;
    } else {
      return <FileText className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getTotalSelectedSize = () => {
    const selectedFileObjects = filteredFiles.filter(f => selectedFiles.has(f.id));
    return selectedFileObjects.reduce((total, file) => total + (file.size || 0), 0);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (err) {
      return 'Fecha inválida';
    }
  };

  const agentFiles = files.filter(f => !f.source || f.source === 'agent');
  const uploadedFiles = files.filter(f => f.source === 'uploaded');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#272728] rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col border border-[rgba(255,255,255,0.08)]">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[rgba(255,255,255,0.08)]">
          <div>
            <h2 className="text-xl font-semibold text-[#DADADA]">Archivos Generados</h2>
            <p className="text-sm text-[#ACACAC] mt-1">{taskTitle}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[rgba(255,255,255,0.08)] rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-[#ACACAC]" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[rgba(255,255,255,0.08)]">
          <button
            onClick={() => setActiveTab('agent')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'agent'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-[#ACACAC] hover:text-[#DADADA]'
            }`}
          >
            <Bot className="w-4 h-4" />
            Generados por Agente ({agentFiles.length})
          </button>
          <button
            onClick={() => setActiveTab('uploaded')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'uploaded'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-[#ACACAC] hover:text-[#DADADA]'
            }`}
          >
            <Upload className="w-4 h-4" />
            Subidos ({uploadedFiles.length})
          </button>
          <button
            onClick={() => setActiveTab('memory')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'memory'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-[#ACACAC] hover:text-[#DADADA]'
            }`}
          >
            <Brain className="w-4 h-4" />
            Memoria ({memoryFiles.length})
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'memory' ? (
            <MemoryTab
              memoryFiles={memoryFiles}
              onAddMemoryFile={onAddMemoryFile}
              onRemoveMemoryFile={onRemoveMemoryFile}
              onToggleMemoryFile={onToggleMemoryFile}
              onClearAllMemory={onClearAllMemory}
            />
          ) : (
            <>
              {/* Selection Controls */}
              {filteredFiles.length > 0 && (
                <div className="flex items-center justify-between p-4 bg-[#383739] border-b border-[rgba(255,255,255,0.08)]">
                  <div className="flex items-center gap-4">
                    <button
                      onClick={toggleSelectAll}
                      className="flex items-center gap-2 text-sm text-[#ACACAC] hover:text-[#DADADA]"
                    >
                      {isAllSelected ? (
                        <CheckSquare className="w-4 h-4" />
                      ) : (
                        <Square className="w-4 h-4" />
                      )}
                      {isAllSelected ? 'Deseleccionar todo' : 'Seleccionar todo'}
                    </button>
                    
                    {selectedFiles.size > 0 && (
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-[#ACACAC]">
                          {selectedFiles.size} archivo{selectedFiles.size !== 1 ? 's' : ''} seleccionado{selectedFiles.size !== 1 ? 's' : ''} 
                          ({formatFileSize(getTotalSelectedSize())})
                        </span>
                        <button
                          onClick={clearSelection}
                          className="text-sm text-[#7f7f7f] hover:text-[#ACACAC]"
                        >
                          Limpiar selección
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {selectedFiles.size > 0 && (
                      <button
                        onClick={handleDownloadSelected}
                        disabled={isLoading}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm"
                      >
                        <Download className="w-4 h-4" />
                        {isLoading ? 'Descargando...' : `Descargar seleccionados (${selectedFiles.size})`}
                      </button>
                    )}
                    
                    <button
                      onClick={onDownloadAll}
                      disabled={isLoading || filteredFiles.length === 0}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm"
                    >
                      <Download className="w-4 h-4" />
                      Descargar todos
                    </button>
                  </div>
                </div>
              )}

              {/* Files List */}
              <div className="flex-1 overflow-y-auto">
                {filteredFiles.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-64 text-[#7f7f7f]">
                    <FileText className="w-12 h-12 mb-4 text-[#4A4A4C]" />
                    <p className="text-lg font-medium">No hay archivos</p>
                    <p className="text-sm">
                      {activeTab === 'agent' 
                        ? 'El agente no ha generado archivos aún'
                        : 'No se han subido archivos'
                      }
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-[rgba(255,255,255,0.08)]">
                    {filteredFiles.map((file) => (
                      <div
                        key={file.id}
                        className={`flex items-center gap-4 p-4 hover:bg-[#383739] transition-colors ${
                          selectedFiles.has(file.id) ? 'bg-blue-500/10' : ''
                        }`}
                      >
                        <button
                          onClick={() => toggleFileSelection(file.id)}
                          className="flex-shrink-0"
                        >
                          {selectedFiles.has(file.id) ? (
                            <CheckSquare className="w-5 h-5 text-blue-400" />
                          ) : (
                            <Square className="w-5 h-5 text-[#7f7f7f]" />
                          )}
                        </button>

                        <div className="flex-shrink-0">
                          {getFileIcon(file)}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-medium text-[#DADADA] truncate">
                              {file.name}
                            </p>
                            {file.source === 'uploaded' && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400">
                                Subido
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-4 mt-1">
                            <p className="text-xs text-[#ACACAC]">
                              {formatFileSize(file.size)}
                            </p>
                            <p className="text-xs text-[#ACACAC]">
                              {formatDate(file.created_at)}
                            </p>
                            {file.mime_type && (
                              <p className="text-xs text-[#7f7f7f]">
                                {file.mime_type}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {onAddFileToMemory && (
                            <button
                              onClick={() => onAddFileToMemory(file)}
                              className="p-2 text-[#7f7f7f] hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                              title="Añadir a memoria"
                            >
                              <Brain className="w-4 h-4" />
                            </button>
                          )}
                          
                          <button
                            onClick={() => onDownload(file)}
                            disabled={isLoading}
                            className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
                            title="Descargar archivo"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-500">
            {activeTab !== 'memory' && (
              <>
                Total: {filteredFiles.length} archivo{filteredFiles.length !== 1 ? 's' : ''} 
                ({formatFileSize(filteredFiles.reduce((total, file) => total + (file.size || 0), 0))})
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

