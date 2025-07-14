import React from 'react';
import { CheckCircle } from 'lucide-react';
import { EnhancedFileDisplay } from './EnhancedFileDisplay';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
}

interface FileUploadSuccessProps {
  files: UploadedFile[];
  onFileView?: (file: UploadedFile) => void;
  onFileDownload?: (file: UploadedFile) => void;
  onFileRemove?: (file: UploadedFile) => void;
  onAddToMemory?: (file: UploadedFile) => void;
}

export const FileUploadSuccess: React.FC<FileUploadSuccessProps> = ({
  files,
  onFileView,
  onFileDownload,
  onFileRemove,
  onAddToMemory
}) => {
  
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)}GB`;
  };

  return (
    <div className="space-y-3">
      {/* Success Message Header */}
      <div className="flex items-center gap-3 p-4 bg-green-500/10 border border-green-500/25 rounded-xl">
        <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
        <div>
          <div className="text-sm font-medium text-green-400">
            ✅ {files.length} archivo{files.length !== 1 ? 's' : ''} cargado{files.length !== 1 ? 's' : ''} exitosamente
          </div>
          <div className="text-xs text-green-300/70 mt-1">
            Los siguientes archivos están ahora disponibles:
          </div>
        </div>
      </div>

      {/* Enhanced Files Display */}
      <EnhancedFileDisplay
        files={files}
        onFileView={onFileView}
        onFileDownload={onFileDownload}
        onFileRemove={onFileRemove}
        onAddToMemory={onAddToMemory}
        className=""
      />

      {/* Additional Context */}
      <div className="text-xs text-[#ACACAC] opacity-75 mt-2">
        Puedes hacer clic en los botones para ver o descargar cada archivo.
      </div>
    </div>
  );
};