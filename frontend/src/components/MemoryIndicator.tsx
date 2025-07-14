import React from 'react';
import { Brain, Database, Zap } from 'lucide-react';

interface MemoryIndicatorProps {
  isInMemory: boolean;
  priority?: 'low' | 'medium' | 'high';
  size?: 'xs' | 'sm' | 'md';
  showLabel?: boolean;
  className?: string;
}

export const MemoryIndicator: React.FC<MemoryIndicatorProps> = ({
  isInMemory,
  priority = 'medium',
  size = 'sm',
  showLabel = false,
  className = ''
}) => {
  if (!isInMemory) return null;

  const sizeClasses = {
    xs: 'w-2 h-2',
    sm: 'w-3 h-3',
    md: 'w-4 h-4'
  };

  const priorityConfig = {
    low: {
      color: 'text-gray-400',
      bg: 'bg-gray-500/20',
      border: 'border-gray-500/30',
      icon: Database,
      label: 'Memoria (Baja)'
    },
    medium: {
      color: 'text-purple-400',
      bg: 'bg-purple-500/20',
      border: 'border-purple-500/30',
      icon: Brain,
      label: 'Memoria (Media)'
    },
    high: {
      color: 'text-amber-400',
      bg: 'bg-amber-500/20',
      border: 'border-amber-500/30',
      icon: Zap,
      label: 'Memoria (Alta)'
    }
  };

  const config = priorityConfig[priority];
  const IconComponent = config.icon;

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      <div
        className={`
          flex items-center justify-center rounded-full border
          ${config.bg} ${config.border} ${sizeClasses[size]}
        `}
        title={config.label}
      >
        <IconComponent className={`${sizeClasses[size]} ${config.color}`} />
      </div>
      
      {showLabel && (
        <span className={`text-xs ${config.color} font-medium`}>
          {config.label}
        </span>
      )}
    </div>
  );
};

export default MemoryIndicator;