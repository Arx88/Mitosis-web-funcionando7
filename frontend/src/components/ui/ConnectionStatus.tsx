import React from 'react';
import { Wifi, WifiOff, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface ConnectionStatusProps {
  isConnected: boolean;
  isLoading?: boolean;
  label: string;
  errorMessage?: string;
  className?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  isLoading = false,
  label,
  errorMessage,
  className = ''
}) => {
  const getStatusIcon = () => {
    if (isLoading) {
      return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
    }
    
    if (isConnected) {
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    }
    
    return <AlertCircle className="w-4 h-4 text-red-400" />;
  };

  const getStatusText = () => {
    if (isLoading) return 'Conectando...';
    if (isConnected) return 'Conectado';
    return 'Desconectado';
  };

  const getStatusColor = () => {
    if (isLoading) return 'text-blue-400';
    if (isConnected) return 'text-green-400';
    return 'text-red-400';
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {getStatusIcon()}
      <div className="flex flex-col">
        <span className="text-[#DADADA] text-sm font-medium">{label}</span>
        <span className={`text-xs ${getStatusColor()}`}>
          {getStatusText()}
        </span>
        {errorMessage && !isConnected && !isLoading && (
          <span className="text-xs text-red-400 mt-1">{errorMessage}</span>
        )}
      </div>
    </div>
  );
};