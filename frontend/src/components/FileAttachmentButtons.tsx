import React from 'react';
import { FileText, Image, Video, Music, Archive, File, Code, Eye, Download, X } from 'lucide-react';

interface FileAttachmentButtonsProps {
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
  showActions?: boolean;
  className?: string;
}

export const FileAttachmentButtons: React.FC<FileAttachmentButtonsProps> = ({
  files,
  onFileView,
  onFileDownload,
  onFileRemove,
  showActions = true,
  className = ''
}) => {
  
  const getFileIcon = (fileName: string, mimeType?: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    if (mimeType?.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension || '')) {
      return { icon: Image, color: 'text-emerald-400', bgColor: 'bg-emerald-500/15 border-emerald-500/25 hover:bg-emerald-500/25' };
    }
    if (mimeType?.startsWith('video/') || ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'].includes(extension || '')) {
      return { icon: Video, color: 'text-rose-400', bgColor: 'bg-rose-500/15 border-rose-500/25 hover:bg-rose-500/25' };
    }
    if (mimeType?.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac', 'ogg'].includes(extension || '')) {
      return { icon: Music, color: 'text-violet-400', bgColor: 'bg-violet-500/15 border-violet-500/25 hover:bg-violet-500/25' };
    }
    if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(extension || '')) {
      return { icon: Archive, color: 'text-amber-400', bgColor: 'bg-amber-500/15 border-amber-500/25 hover:bg-amber-500/25' };
    }
    if (['txt', 'md', 'doc', 'docx', 'pdf', 'rtf'].includes(extension || '')) {
      return { icon: FileText, color: 'text-sky-400', bgColor: 'bg-sky-500/15 border-sky-500/25 hover:bg-sky-500/25' };
    }
    if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'css', 'html', 'xml', 'json', 'yaml', 'yml'].includes(extension || '')) {
      return { icon: Code, color: 'text-cyan-400', bgColor: 'bg-cyan-500/15 border-cyan-500/25 hover:bg-cyan-500/25' };
    }
    return { icon: File, color: 'text-slate-400', bgColor: 'bg-slate-500/15 border-slate-500/25 hover:bg-slate-500/25' };
  };

  const formatFileSize = (bytes?: number | string) => {
    if (!bytes) return '';
    const size = typeof bytes === 'string' ? parseInt(bytes) : bytes;
    if (size < 1024) return `${size}B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)}KB`;
    if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)}MB`;
    return `${(size / (1024 * 1024 * 1024)).toFixed(1)}GB`;
  };

  if (!files || files.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {files.map((file) => {
        const { icon: IconComponent, color, bgColor } = getFileIcon(file.name, file.type);
        
        return (
          <div
            key={file.id}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all duration-200 hover:scale-105 ${bgColor}`}
          >
            {/* File Icon */}
            <div className="flex-shrink-0">
              <IconComponent className={`w-4 h-4 ${color}`} />
            </div>
            
            {/* File Name and Size */}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-[#DADADA] truncate max-w-[120px]">
                {file.name}
              </div>
              {file.size && (
                <div className="text-xs text-[#ACACAC] opacity-75">
                  {formatFileSize(file.size)}
                </div>
              )}
            </div>
            
            {/* View Button (Eye Icon) */}
            {showActions && onFileView && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onFileView(file);
                }}
                className="flex-shrink-0 p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                title="Ver archivo"
              >
                <Eye className="w-3.5 h-3.5 text-white" />
              </button>
            )}
            
            {/* Additional Actions (Download, Remove) */}
            {showActions && (
              <div className="flex items-center gap-1">
                {onFileDownload && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onFileDownload(file);
                    }}
                    className="p-1 rounded-full bg-green-500/20 hover:bg-green-500/30 transition-colors"
                    title="Descargar archivo"
                  >
                    <Download className="w-3 h-3 text-green-400" />
                  </button>
                )}
                {onFileRemove && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onFileRemove(file);
                    }}
                    className="p-1 rounded-full bg-red-500/20 hover:bg-red-500/30 transition-colors"
                    title="Eliminar archivo"
                  >
                    <X className="w-3 h-3 text-red-400" />
                  </button>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};