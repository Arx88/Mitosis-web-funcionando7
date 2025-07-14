import React, { useState } from 'react';
import { FileText, Image, Video, Music, Archive, File, Code, Eye, Download, X, MoreHorizontal, Brain } from 'lucide-react';

interface EnhancedFileDisplayProps {
  files: Array<{
    id: string;
    name: string;
    size?: number | string;
    type?: string;
    url?: string;
    preview?: string;
  }>;
  onFileView?: (file: any) => void;
  onFileDownload?: (file: any) => void;
  onFileRemove?: (file: any) => void;
  onAddToMemory?: (file: any) => void;
  className?: string;
}

export const EnhancedFileDisplay: React.FC<EnhancedFileDisplayProps> = ({
  files,
  onFileView,
  onFileDownload,
  onFileRemove,
  onAddToMemory,
  className = ''
}) => {
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);

  const getFileIcon = (fileName: string, mimeType?: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    if (mimeType?.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension || '')) {
      return { icon: Image, color: 'text-emerald-400', bgColor: 'bg-emerald-500/15 border-emerald-500/25' };
    }
    if (mimeType?.startsWith('video/') || ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'].includes(extension || '')) {
      return { icon: Video, color: 'text-rose-400', bgColor: 'bg-rose-500/15 border-rose-500/25' };
    }
    if (mimeType?.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac', 'ogg'].includes(extension || '')) {
      return { icon: Music, color: 'text-violet-400', bgColor: 'bg-violet-500/15 border-violet-500/25' };
    }
    if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(extension || '')) {
      return { icon: Archive, color: 'text-amber-400', bgColor: 'bg-amber-500/15 border-amber-500/25' };
    }
    if (['txt', 'md', 'doc', 'docx', 'pdf', 'rtf'].includes(extension || '')) {
      return { icon: FileText, color: 'text-sky-400', bgColor: 'bg-sky-500/15 border-sky-500/25' };
    }
    if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'css', 'html', 'xml', 'json', 'yaml', 'yml'].includes(extension || '')) {
      return { icon: Code, color: 'text-cyan-400', bgColor: 'bg-cyan-500/15 border-cyan-500/25' };
    }
    return { icon: File, color: 'text-slate-400', bgColor: 'bg-slate-500/15 border-slate-500/25' };
  };

  const formatFileSize = (bytes?: number | string) => {
    if (!bytes) return '';
    const size = typeof bytes === 'string' ? parseInt(bytes) : bytes;
    if (size < 1024) return `${size}B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)}KB`;
    if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)}MB`;
    return `${(size / (1024 * 1024 * 1024)).toFixed(1)}GB`;
  };

  const handleDropdownToggle = (fileId: string) => {
    setOpenDropdownId(openDropdownId === fileId ? null : fileId);
  };

  const handleAction = (action: () => void, fileId: string) => {
    action();
    setOpenDropdownId(null);
  };

  if (!files || files.length === 0) return null;

  return (
    <div className={`space-y-3 ${className}`}>
      {files.map((file) => {
        const { icon: IconComponent, color, bgColor } = getFileIcon(file.name, file.type);
        const isDropdownOpen = openDropdownId === file.id;
        
        return (
          <div
            key={file.id}
            className={`relative flex items-center gap-3 p-3 rounded-xl border transition-all duration-200 hover:scale-[1.02] ${bgColor}`}
          >
            {/* File Icon - left side */}
            <div className="flex-shrink-0">
              <div className={`w-10 h-10 rounded-lg ${bgColor} flex items-center justify-center`}>
                <IconComponent className={`w-5 h-5 ${color}`} />
              </div>
            </div>
            
            {/* File Info - center */}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-[#DADADA] truncate">
                {file.name}
              </div>
              {file.size && (
                <div className="text-xs text-[#ACACAC] opacity-75 mt-0.5">
                  {formatFileSize(file.size)}
                </div>
              )}
            </div>
            
            {/* Dropdown Arrow - right side */}
            <div className="flex-shrink-0 relative">
              <button
                onClick={() => handleDropdownToggle(file.id)}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                title="Opciones del archivo"
              >
                <MoreHorizontal className="w-4 h-4 text-[#ACACAC] hover:text-[#DADADA]" />
              </button>
              
              {/* Dropdown Menu */}
              {isDropdownOpen && (
                <div className="absolute right-0 top-full mt-1 w-40 bg-[#2A2A2B] border border-[rgba(255,255,255,0.1)] rounded-lg shadow-lg z-50">
                  {onFileView && (
                    <button
                      onClick={() => handleAction(() => onFileView(file), file.id)}
                      className="w-full px-3 py-2 text-left text-sm text-[#DADADA] hover:bg-[rgba(255,255,255,0.08)] transition-colors flex items-center gap-2 rounded-t-lg"
                    >
                      <Eye className="w-4 h-4 text-blue-400" />
                      Ver archivo
                    </button>
                  )}
                  {onFileDownload && (
                    <button
                      onClick={() => handleAction(() => onFileDownload(file), file.id)}
                      className="w-full px-3 py-2 text-left text-sm text-[#DADADA] hover:bg-[rgba(255,255,255,0.08)] transition-colors flex items-center gap-2"
                    >
                      <Download className="w-4 h-4 text-green-400" />
                      Descargar
                    </button>
                  )}
                  {onFileRemove && (
                    <button
                      onClick={() => handleAction(() => onFileRemove(file), file.id)}
                      className="w-full px-3 py-2 text-left text-sm text-[#DADADA] hover:bg-[rgba(255,255,255,0.08)] transition-colors flex items-center gap-2"
                    >
                      <X className="w-4 h-4 text-red-400" />
                      Eliminar
                    </button>
                  )}
                  {onAddToMemory && (
                    <button
                      onClick={() => handleAction(() => onAddToMemory(file), file.id)}
                      className="w-full px-3 py-2 text-left text-sm text-[#DADADA] hover:bg-[rgba(255,255,255,0.08)] transition-colors flex items-center gap-2 rounded-b-lg"
                    >
                      <Brain className="w-4 h-4 text-purple-400" />
                      Memoria
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
      
      {/* Click outside to close dropdown */}
      {openDropdownId && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setOpenDropdownId(null)}
        />
      )}
    </div>
  );
};