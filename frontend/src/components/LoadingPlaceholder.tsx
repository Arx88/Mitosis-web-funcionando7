import React from 'react';

interface LoadingPlaceholderProps {
  type?: 'text' | 'image' | 'card' | 'inline' | 'message' | 'file';
  lines?: number;
  className?: string;
  width?: string;
  height?: string;
  rounded?: boolean;
}

export const LoadingPlaceholder: React.FC<LoadingPlaceholderProps> = ({
  type = 'text',
  lines = 3,
  className = '',
  width = 'w-full',
  height = 'h-4',
  rounded = true
}) => {
  const baseClasses = `loading-shimmer ${rounded ? 'rounded' : ''} ${className}`;

  if (type === 'text') {
    return (
      <div className="space-y-2 animate-optimized">
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={`${baseClasses} ${height} ${
              index === lines - 1 ? 'w-3/4' : width
            }`}
            style={{
              animationDelay: `${index * 0.1}s`,
            }}
          />
        ))}
      </div>
    );
  }

  if (type === 'image') {
    return (
      <div className={`${baseClasses} ${width} ${height || 'h-32'} rounded-lg relative overflow-hidden`}>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex items-center gap-2 text-[#ACACAC] z-10">
            <div className="w-5 h-5 rounded-full border-2 border-[#ACACAC] border-t-transparent animate-spin" />
            <span className="text-sm">Cargando imagen...</span>
          </div>
        </div>
      </div>
    );
  }

  if (type === 'card') {
    return (
      <div className="space-y-3 p-4 bg-[#383739] rounded-xl">
        <LoadingPlaceholder type="text" lines={1} width="w-1/2" height="h-5" />
        <LoadingPlaceholder type="text" lines={2} />
      </div>
    );
  }

  if (type === 'message') {
    return (
      <div className="flex items-start gap-3 max-w-[90%] fade-in">
        {/* Robot icon placeholder */}
        <div className="w-9 h-9 bg-[#404142] rounded-full flex items-center justify-center flex-shrink-0 mt-1">
          <div className="w-6 h-6 bg-[#3a3a3b] rounded loading-shimmer" />
        </div>
        
        {/* Message content placeholder */}
        <div className="bg-[#383739] rounded-xl p-4 flex-1 chat-container">
          <LoadingPlaceholder type="text" lines={3} />
        </div>
      </div>
    );
  }

  if (type === 'file') {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, index) => (
          <div key={index} className="flex items-center gap-3 p-3 bg-[#383739] rounded-lg file-attachment-wrapper">
            <LoadingPlaceholder type="image" width="w-8" height="h-8" />
            <div className="flex-1">
              <LoadingPlaceholder type="text" lines={1} width="w-32" />
              <LoadingPlaceholder type="text" lines={1} width="w-16" height="h-3" />
            </div>
            <LoadingPlaceholder type="image" width="w-6" height="h-6" />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'inline') {
    return (
      <span className={`${baseClasses} inline-block ${width} ${height} rounded`} />
    );
  }

  return <div className={`${baseClasses} ${width} ${height}`} />;
};

// Pre-built components for common use cases
export const MessageLoadingPlaceholder: React.FC = () => {
  return <LoadingPlaceholder type="message" />;
};

export const ImageLoadingPlaceholder: React.FC<{ className?: string }> = ({ 
  className = '' 
}) => {
  return <LoadingPlaceholder type="image" className={className} />;
};

export const FileLoadingPlaceholder: React.FC<{ count?: number }> = ({ 
  count = 1 
}) => {
  return <LoadingPlaceholder type="file" lines={count} />;
};

export const CardLoadingPlaceholder: React.FC<{ className?: string }> = ({ 
  className = '' 
}) => {
  return <LoadingPlaceholder type="card" className={className} />;
};

// Typing indicator component for chat
export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-start gap-3 max-w-[90%] fade-in">
      <div className="w-9 h-9 bg-[#404142] rounded-full flex items-center justify-center flex-shrink-0 mt-1">
        <div className="w-6 h-6 text-[#DADADA]">
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
      </div>
      
      <div className="bg-[#383739] rounded-xl p-4 flex-1">
        <div className="flex items-center gap-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-[#ACACAC] rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-[#ACACAC] rounded-full animate-pulse" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-[#ACACAC] rounded-full animate-pulse" style={{ animationDelay: '300ms' }}></div>
          </div>
          <span className="text-sm text-[#ACACAC]">Pensando...</span>
        </div>
      </div>
    </div>
  );
};