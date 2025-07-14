import React from 'react';
import { Eye, FileText, Image, Video, Music, Archive, File, Code, Download } from 'lucide-react';

interface FileInlineButtonProps {
  file: {
    id?: string;
    name: string;
    type?: string;
    size?: string | number;
    url?: string;
  };
  onView?: (file: any) => void;
  onDownload?: (file: any) => void;
}

export const FileInlineButton: React.FC<FileInlineButtonProps> = ({
  file,
  onView,
  onDownload
}) => {
  const getFileIcon = (fileName: string, mimeType?: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    const iconProps = { className: 'w-4 h-4' };

    if (mimeType?.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'ico'].includes(extension || '')) {
      return <Image {...iconProps} className="w-4 h-4 text-green-400" />;
    }
    if (mimeType?.startsWith('video/') || ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(extension || '')) {
      return <Video {...iconProps} className="w-4 h-4 text-red-400" />;
    }
    if (mimeType?.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'].includes(extension || '')) {
      return <Music {...iconProps} className="w-4 h-4 text-purple-400" />;
    }
    if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'].includes(extension || '')) {
      return <Archive {...iconProps} className="w-4 h-4 text-yellow-400" />;
    }
    if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'html', 'css', 'php', 'rb', 'go', 'rs', 'swift'].includes(extension || '')) {
      return <Code {...iconProps} className="w-4 h-4 text-cyan-400" />;
    }
    if (['txt', 'md', 'doc', 'docx', 'pdf', 'rtf', 'odt'].includes(extension || '')) {
      return <FileText {...iconProps} className="w-4 h-4 text-blue-400" />;
    }
    return <File {...iconProps} className="w-4 h-4 text-gray-400" />;
  };

  const getFileColor = (fileName: string, mimeType?: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    if (mimeType?.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'ico'].includes(extension || '')) {
      return 'border-green-400/40 bg-green-400/10 hover:bg-green-400/20';
    }
    if (mimeType?.startsWith('video/') || ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(extension || '')) {
      return 'border-red-400/40 bg-red-400/10 hover:bg-red-400/20';
    }
    if (mimeType?.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'].includes(extension || '')) {
      return 'border-purple-400/40 bg-purple-400/10 hover:bg-purple-400/20';
    }
    if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'].includes(extension || '')) {
      return 'border-yellow-400/40 bg-yellow-400/10 hover:bg-yellow-400/20';
    }
    if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'html', 'css', 'php', 'rb', 'go', 'rs', 'swift'].includes(extension || '')) {
      return 'border-cyan-400/40 bg-cyan-400/10 hover:bg-cyan-400/20';
    }
    if (['txt', 'md', 'doc', 'docx', 'pdf', 'rtf', 'odt'].includes(extension || '')) {
      return 'border-blue-400/40 bg-blue-400/10 hover:bg-blue-400/20';
    }
    return 'border-gray-400/40 bg-gray-400/10 hover:bg-gray-400/20';
  };

  const formatFileSize = (size?: string | number) => {
    if (!size) return '';
    const bytes = typeof size === 'string' ? parseInt(size) : size;
    if (isNaN(bytes)) return '';
    
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const displayName = file.name.length > 20 ? file.name.substring(0, 17) + '...' : file.name;
  const sizeText = formatFileSize(file.size);

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg border transition-all duration-200 cursor-pointer ${getFileColor(file.name, file.type)}`}>
      {/* File Icon */}
      <div className="flex-shrink-0">
        {getFileIcon(file.name, file.type)}
      </div>
      
      {/* File Name and Size */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-[#DADADA] truncate" title={file.name}>
            {displayName}
          </span>
          {sizeText && (
            <span className="text-xs text-[#ACACAC] flex-shrink-0">
              {sizeText}
            </span>
          )}
        </div>
      </div>
      
      {/* View Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onView?.(file);
        }}
        className="flex-shrink-0 p-1 rounded-md bg-blue-500/20 hover:bg-blue-500/30 transition-colors"
        title="Ver archivo"
      >
        <Eye className="w-3 h-3 text-blue-400" />
      </button>
    </div>
  );
};

interface FileInlineDisplayProps {
  files: Array<{
    id?: string;
    name: string;
    type?: string;
    size?: string | number;
    url?: string;
  }>;
  onFileView?: (file: any) => void;
  onFileDownload?: (file: any) => void;
}

export const FileInlineDisplay: React.FC<FileInlineDisplayProps> = ({
  files,
  onFileView,
  onFileDownload
}) => {
  if (!files || files.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {files.map((file, index) => (
        <FileInlineButton
          key={file.id || `file-${index}`}
          file={file}
          onView={onFileView}
          onDownload={onFileDownload}
        />
      ))}
    </div>
  );
};