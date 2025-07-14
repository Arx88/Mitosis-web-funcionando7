import React, { useState } from 'react';
import { FileText, Image, Video, Music, Archive, File, Download, Eye, X } from 'lucide-react';

interface FileAttachmentProps {
  file: {
    id: string;
    name: string;
    size?: number;
    type?: string;
    url?: string;
    preview?: string;
  };
  onView?: (file: any) => void;
  onDownload?: (file: any) => void;
  onRemove?: (file: any) => void;
  showActions?: boolean;
  size?: 'small' | 'medium' | 'large';
}

export const FileAttachment: React.FC<FileAttachmentProps> = ({
  file,
  onView,
  onDownload,
  onRemove,
  showActions = true,
  size = 'medium'
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Tamaño desconocido';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (fileName: string, mimeType?: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    const iconProps = {
      className: size === 'small' ? 'w-4 h-4' : size === 'large' ? 'w-8 h-8' : 'w-6 h-6'
    };

    if (mimeType?.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension || '')) {
      return <Image {...iconProps} className={`${iconProps.className} text-green-400`} />;
    }
    if (mimeType?.startsWith('video/') || ['mp4', 'avi', 'mov', 'wmv', 'flv'].includes(extension || '')) {
      return <Video {...iconProps} className={`${iconProps.className} text-red-400`} />;
    }
    if (mimeType?.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac'].includes(extension || '')) {
      return <Music {...iconProps} className={`${iconProps.className} text-purple-400`} />;
    }
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(extension || '')) {
      return <Archive {...iconProps} className={`${iconProps.className} text-yellow-400`} />;
    }
    if (['txt', 'md', 'doc', 'docx', 'pdf'].includes(extension || '')) {
      return <FileText {...iconProps} className={`${iconProps.className} text-blue-400`} />;
    }
    return <File {...iconProps} className={`${iconProps.className} text-gray-400`} />;
  };

  const getFileTypeColor = (fileName: string, mimeType?: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    if (mimeType?.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension || '')) {
      return 'border-green-500/20 bg-green-500/10';
    }
    if (mimeType?.startsWith('video/') || ['mp4', 'avi', 'mov', 'wmv', 'flv'].includes(extension || '')) {
      return 'border-red-500/20 bg-red-500/10';
    }
    if (mimeType?.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac'].includes(extension || '')) {
      return 'border-purple-500/20 bg-purple-500/10';
    }
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(extension || '')) {
      return 'border-yellow-500/20 bg-yellow-500/10';
    }
    if (['txt', 'md', 'doc', 'docx', 'pdf'].includes(extension || '')) {
      return 'border-blue-500/20 bg-blue-500/10';
    }
    return 'border-gray-500/20 bg-gray-500/10';
  };

  const sizeClasses = {
    small: 'p-2 text-xs',
    medium: 'p-3 text-sm',
    large: 'p-4 text-base'
  };

  return (
    <div 
      className={`
        relative rounded-lg border transition-all duration-200 cursor-pointer
        ${getFileTypeColor(file.name, file.type)}
        ${sizeClasses[size]}
        ${isHovered ? 'scale-105 shadow-lg' : ''}
        hover:border-opacity-40
      `}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onView?.(file)}
    >
      {/* File Icon and Info */}
      <div className="flex items-center gap-3">
        {/* File Icon */}
        <div className="flex-shrink-0">
          {getFileIcon(file.name, file.type)}
        </div>
        
        {/* File Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className={`font-medium text-[#DADADA] truncate ${
              size === 'small' ? 'text-xs' : size === 'large' ? 'text-base' : 'text-sm'
            }`}>
              {file.name}
            </p>
            {/* File extension badge */}
            <span className={`
              px-1.5 py-0.5 rounded text-xs font-mono uppercase
              ${getFileTypeColor(file.name, file.type).replace('border-', 'bg-').replace('/20', '/30').replace(' bg-', ' text-white bg-')}
              opacity-75
            `}>
              {file.name.split('.').pop() || 'file'}
            </span>
          </div>
          {file.size && (
            <p className={`text-[#7f7f7f] ${
              size === 'small' ? 'text-xs' : 'text-xs'
            }`}>
              {formatFileSize(file.size)}
            </p>
          )}
        </div>

        {/* Action Buttons */}
        {showActions && (
          <div className="flex-shrink-0 flex items-center gap-1">
            {onView && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onView(file);
                }}
                className="p-1.5 rounded-full bg-blue-500/20 hover:bg-blue-500/30 transition-colors group"
                title="Vista previa"
              >
                <Eye className="w-3 h-3 text-blue-400" />
              </button>
            )}
            {onDownload && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDownload(file);
                }}
                className="p-1.5 rounded-full bg-green-500/20 hover:bg-green-500/30 transition-colors"
                title="Descargar archivo"
              >
                <Download className="w-3 h-3 text-green-400" />
              </button>
            )}
            {onRemove && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(file);
                }}
                className="p-1.5 rounded-full bg-red-500/20 hover:bg-red-500/30 transition-colors"
                title="Eliminar archivo"
              >
                <X className="w-3 h-3 text-red-400" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Preview overlay for images */}
      {file.preview && isHovered && (
        <div className="absolute -top-2 -left-2 w-16 h-16 rounded-lg overflow-hidden border-2 border-white shadow-lg z-10">
          <img 
            src={file.preview} 
            alt={file.name}
            className="w-full h-full object-cover"
          />
        </div>
      )}
    </div>
  );
};