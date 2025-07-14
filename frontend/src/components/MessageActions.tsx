import React, { useState } from 'react';
import { Copy, RefreshCw, Check } from 'lucide-react';

interface MessageActionsProps {
  messageContent: string;
  onRegenerate?: () => void;
  className?: string;
}

export const MessageActions: React.FC<MessageActionsProps> = ({
  messageContent,
  onRegenerate,
  className = ''
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(messageContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Error copying to clipboard:', error);
    }
  };

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      <button
        onClick={handleCopy}
        className="p-1.5 text-[#7F7F7F] hover:text-[#DADADA] hover:bg-[rgba(255,255,255,0.05)] 
          rounded transition-all duration-200 opacity-70 group-hover:opacity-100"
        title="Copiar respuesta"
      >
        {copied ? (
          <Check className="w-3.5 h-3.5 text-green-400" />
        ) : (
          <Copy className="w-3.5 h-3.5" />
        )}
      </button>
      
      {onRegenerate && (
        <button
          onClick={onRegenerate}
          className="p-1.5 text-[#7F7F7F] hover:text-[#DADADA] hover:bg-[rgba(255,255,255,0.05)] 
            rounded transition-all duration-200 opacity-70 group-hover:opacity-100"
          title="Regenerar respuesta"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};