import React, { useState } from 'react';
import { ExternalLink, Globe, Link as LinkIcon } from 'lucide-react';

interface LinkPreviewProps {
  url: string;
  title?: string;
  description?: string;
  className?: string;
}

export const LinkPreview: React.FC<LinkPreviewProps> = ({
  url,
  title,
  description,
  className = ''
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch {
      return url;
    }
  };

  const getDomain = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname.replace('www.', '');
    } catch {
      return 'web';
    }
  };

  const truncateText = (text: string, maxLength: number = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <div 
      className={`group relative ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className={`
          block p-4 rounded-xl border transition-all duration-200 
          bg-gradient-to-r from-[#1E1E1F] to-[#252526]
          border-blue-500/20 hover:border-blue-500/40
          hover:shadow-lg hover:scale-[1.02]
          text-decoration-none
          ${isHovered ? 'shadow-blue-500/10' : ''}
        `}
      >
        <div className="flex items-start gap-3">
          {/* Link Icon */}
          <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
            <Globe className="w-5 h-5 text-white" />
          </div>

          {/* Link Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-semibold text-[#DADADA] truncate group-hover:text-blue-400 transition-colors">
                {title || getDomain(url)}
              </h4>
              <ExternalLink className="w-3 h-3 text-blue-400 opacity-60 group-hover:opacity-100 transition-opacity" />
            </div>
            
            {description && (
              <p className="text-sm text-[#ACACAC] leading-relaxed mb-2">
                {truncateText(description)}
              </p>
            )}
            
            <div className="flex items-center gap-2 text-xs">
              <LinkIcon className="w-3 h-3 text-blue-400" />
              <span className="text-blue-400 hover:text-blue-300 transition-colors truncate">
                {formatUrl(url)}
              </span>
            </div>
          </div>
        </div>
      </a>
    </div>
  );
};

interface MultiLinkDisplayProps {
  links: Array<{
    url: string;
    title?: string;
    description?: string;
  }>;
  className?: string;
}

export const MultiLinkDisplay: React.FC<MultiLinkDisplayProps> = ({
  links,
  className = ''
}) => {
  if (links.length === 0) return null;

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center gap-2 text-sm text-blue-400 font-medium">
        <LinkIcon className="w-4 h-4" />
        <span>Enlaces encontrados ({links.length})</span>
      </div>
      
      <div className="space-y-2">
        {links.map((link, index) => (
          <LinkPreview
            key={index}
            url={link.url}
            title={link.title}
            description={link.description}
          />
        ))}
      </div>
    </div>
  );
};