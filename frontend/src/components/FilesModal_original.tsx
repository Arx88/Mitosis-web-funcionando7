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

  // Reset selection when files change or modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedFiles(new Set());
      setIsAllSelected(false);
    }
  }, [isOpen, files]);

  // Filter files based on active tab
  const filteredFiles = files.filter(file => {
    if (activeTab === 'agent') {
      return !file.source || file.source === 'agent';
    } else if (activeTab === 'uploaded') {
      return file.source === 'uploaded';
    }
    return false; // Memory tab doesn't filter regular files
  });

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

  const handleDownloadSelected = () => {
    if (selectedFiles.size === 0) return;
    
    const selectedFileObjects = filteredFiles.filter(f => selectedFiles.has(f.id));
    
    if (selectedFiles.size === 1) {
      // Si solo hay un archivo seleccionado, descargarlo directamente
      onDownload(selectedFileObjects[0]);
    } else {
      // Si hay múltiples archivos, usar la función de descarga múltiple
      if (onDownloadSelected) {
        onDownloadSelected(selectedFileObjects);
      } else {
        // Fallback: descargar cada archivo individualmente
        selectedFileObjects.forEach(file => onDownload(file));
      }
    }
  };

  const clearSelection = () => {
    setSelectedFiles(new Set());
  };

  const getFileIcon = (file: FileItem) => {
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
    } else {
      return <FileText className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getTotalSelectedSize = () => {
    const selectedFileObjects = filteredFiles.filter(f => selectedFiles.has(f.id));
    return selectedFileObjects.reduce((total, file) => total + file.size, 0);
  };

  const agentFiles = files.filter(f => !f.source || f.source === 'agent');
  const uploadedFiles = files.filter(f => f.source === 'uploaded');
  const memoryCount = memoryFiles.length;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#272728] rounded-xl border border-[rgba(255,255,255,0.08)] w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[rgba(255,255,255,0.08)]">
          <div>
            <h2 className="text-lg font-bold text-[#DADADA]">Archivos de la Tarea</h2>
            <p className="text-sm text-[#7f7f7f]">{taskTitle}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#383739] rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-[#DADADA]" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-[rgba(255,255,255,0.08)]">
          <div className="flex">
            <button
              onClick={() => {
                setActiveTab('agent');
                setSelectedFiles(new Set());
              }}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === 'agent'
                  ? 'border-blue-500 text-blue-400 bg-[rgba(59,130,246,0.1)]'
                  : 'border-transparent text-[#ACACAC] hover:text-[#DADADA] hover:bg-[rgba(255,255,255,0.05)]'
              }`}
            >
              <Bot className="w-4 h-4" />
              Agente ({agentFiles.length})
            </button>
            <button
              onClick={() => {
                setActiveTab('uploaded');
                setSelectedFiles(new Set());
              }}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === 'uploaded'
                  ? 'border-green-500 text-green-400 bg-[rgba(34,197,94,0.1)]'
                  : 'border-transparent text-[#ACACAC] hover:text-[#DADADA] hover:bg-[rgba(255,255,255,0.05)]'
              }`}
            >
              <Upload className="w-4 h-4" />
              Uploaded ({uploadedFiles.length})
            </button>
            <button
              onClick={() => {
                setActiveTab('memory');
                setSelectedFiles(new Set());
              }}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === 'memory'
                  ? 'border-purple-500 text-purple-400 bg-[rgba(168,85,247,0.1)]'
                  : 'border-transparent text-[#ACACAC] hover:text-[#DADADA] hover:bg-[rgba(255,255,255,0.05)]'
              }`}
            >
              <Brain className="w-4 h-4" />
              Memoria ({memoryCount})
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {activeTab === 'memory' ? (
            /* Memory Tab Content */
            <MemoryTab
              memoryFiles={memoryFiles}
              onAddMemoryFile={onAddMemoryFile}
              onRemoveMemoryFile={onRemoveMemoryFile}
              onToggleMemoryFile={onToggleMemoryFile}
              onClearAllMemory={onClearAllMemory}
              className="border-0 bg-transparent"
            />
          ) : filteredFiles.length === 0 ? (
            <div className="text-center py-12">
              {activeTab === 'agent' ? (
                <>
                  <Bot className="w-16 h-16 text-[#7f7f7f] mx-auto mb-4" />
                  <p className="text-[#ACACAC] text-lg mb-2">No hay archivos del agente</p>
                  <p className="text-[#7f7f7f] text-sm">
                    Los archivos creados por el agente durante esta tarea aparecerán aquí
                  </p>
                </>
              ) : (
                <>
                  <Upload className="w-16 h-16 text-[#7f7f7f] mx-auto mb-4" />
                  <p className="text-[#ACACAC] text-lg mb-2">No hay archivos subidos</p>
                  <p className="text-[#7f7f7f] text-sm">
                    Los archivos que subas usando el botón de adjuntar aparecerán aquí
                  </p>
                </>
              )}
            </div>
          ) : (
            <>
              {/* Selection Controls */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <button
                    onClick={toggleSelectAll}
                    className="flex items-center gap-2 px-3 py-1.5 bg-[#383739] hover:bg-[#404142] 
                      rounded-lg text-sm text-[#DADADA] transition-colors"
                  >
                    {isAllSelected ? (
                      <CheckSquare className="w-4 h-4 text-blue-400" />
                    ) : (
                      <Square className="w-4 h-4" />
                    )}
                    {isAllSelected ? 'Deseleccionar Todo' : 'Seleccionar Todo'}
                  </button>
                  
                  {selectedFiles.size > 0 && (
                    <button
                      onClick={clearSelection}
                      className="flex items-center gap-2 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 
                        rounded-lg text-sm text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      Limpiar
                    </button>
                  )}
                </div>

                <div className="text-sm text-[#ACACAC]">
                  {selectedFiles.size > 0 ? (
                    <>
                      {selectedFiles.size} de {filteredFiles.length} seleccionados
                      {selectedFiles.size > 1 && (
                        <span className="text-[#7f7f7f]">
                          {' '}• {formatFileSize(getTotalSelectedSize())}
                        </span>
                      )}
                    </>
                  ) : (
                    `${filteredFiles.length} archivo${filteredFiles.length !== 1 ? 's' : ''} ${activeTab === 'agent' ? 'del agente' : 'subidos'}`
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 mb-4">
                {selectedFiles.size > 0 && (
                  <button
                    onClick={handleDownloadSelected}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 
                      rounded-lg text-sm text-white transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Descargar Seleccionados ({selectedFiles.size})
                  </button>
                )}
                
                <button
                  onClick={onDownloadAll}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 
                    rounded-lg text-sm text-white transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Descargar Todo como ZIP
                </button>
              </div>

              {/* Files List */}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredFiles.map((file) => (
                  <div
                    key={file.id}
                    className={`flex items-center p-3 rounded-lg transition-colors cursor-pointer
                      ${selectedFiles.has(file.id) 
                        ? 'bg-blue-600/20 border border-blue-500/30' 
                        : 'bg-[#383739] hover:bg-[#404142] border border-transparent'
                      }`}
                    onClick={() => toggleFileSelection(file.id)}
                  >
                    {/* Selection Checkbox */}
                    <div className="mr-3 flex-shrink-0">
                      {selectedFiles.has(file.id) ? (
                        <CheckSquare className="w-5 h-5 text-blue-400" />
                      ) : (
                        <Square className="w-5 h-5 text-[#7f7f7f]" />
                      )}
                    </div>

                    {/* File Info */}
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {getFileIcon(file)}
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-[#DADADA] truncate">
                          {file.name}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-[#7f7f7f]">
                          <span>{formatFileSize(file.size)}</span>
                          <span>•</span>
                          <span>{new Date(file.created_at).toLocaleString()}</span>
                          {file.source && (
                            <>
                              <span>•</span>
                              <span className={`flex items-center gap-1 ${
                                file.source === 'agent' ? 'text-blue-400' : 'text-green-400'
                              }`}>
                                {file.source === 'agent' ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />}
                                {file.source === 'agent' ? 'Agente' : 'Usuario'}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Individual Download Button */}
                    <div className="flex items-center gap-2">
                      {onAddFileToMemory && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onAddFileToMemory(file);
                          }}
                          className="flex items-center gap-1 px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 
                            rounded text-xs text-purple-400 transition-colors flex-shrink-0"
                        >
                          <Brain className="w-3 h-3" />
                          Memoria
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDownload(file);
                        }}
                        className="flex items-center gap-1 px-3 py-1.5 bg-[#4A4A4C] hover:bg-[#5A5A5C] 
                          rounded text-xs text-[#DADADA] transition-colors flex-shrink-0"
                      >
                        <Download className="w-3 h-3" />
                        Descargar
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};