import React, { useState } from 'react';
import { Brain, Plus, Check, Loader2 } from 'lucide-react';

interface MemoryActionButtonProps {
  isInMemory: boolean;
  isLoading?: boolean;
  onClick: () => void;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'ghost';
  className?: string;
  disabled?: boolean;
}

export const MemoryActionButton: React.FC<MemoryActionButtonProps> = ({
  isInMemory,
  isLoading = false,
  onClick,
  size = 'sm',
  variant = 'secondary',
  className = '',
  disabled = false
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [justClicked, setJustClicked] = useState(false);

  const handleClick = () => {
    setJustClicked(true);
    onClick();
    
    // Reset the clicked state after 2 seconds
    setTimeout(() => {
      setJustClicked(false);
    }, 2000);
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base'
  };

  const variantClasses = {
    primary: isInMemory 
      ? 'bg-purple-500/20 border-purple-500/50 text-purple-300 hover:bg-purple-500/30'
      : 'bg-purple-600 hover:bg-purple-700 text-white border-purple-600',
    secondary: isInMemory
      ? 'bg-purple-500/10 border-purple-500/30 text-purple-400 hover:bg-purple-500/20'
      : 'bg-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.12)] text-[#DADADA] border-[rgba(255,255,255,0.12)]',
    ghost: isInMemory
      ? 'bg-transparent border-transparent text-purple-400 hover:bg-purple-500/10'
      : 'bg-transparent hover:bg-[rgba(255,255,255,0.08)] text-[#ACACAC] border-transparent'
  };

  const iconSize = size === 'sm' ? 'w-3 h-3' : size === 'md' ? 'w-4 h-4' : 'w-5 h-5';

  return (
    <button
      onClick={handleClick}
      disabled={disabled || isLoading}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`
        flex items-center gap-1.5 rounded-lg transition-all duration-200 
        border font-medium relative overflow-hidden
        ${sizeClasses[size]} 
        ${variantClasses[variant]}
        ${disabled || isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${justClicked && !isInMemory ? 'animate-pulse' : ''}
        ${className}
      `}
      title={isInMemory ? 'Ya está en memoria' : 'Agregar a memoria'}
    >
      {/* Feedback animation overlay */}
      {justClicked && !isInMemory && (
        <div className="absolute inset-0 bg-purple-500/20 animate-ping"></div>
      )}
      
      {isLoading ? (
        <Loader2 className={`${iconSize} animate-spin`} />
      ) : isInMemory ? (
        <Brain className={`${iconSize} ${isHovered ? 'animate-pulse' : ''}`} />
      ) : justClicked ? (
        <Check className={`${iconSize} text-green-400`} />
      ) : (
        <Plus className={iconSize} />
      )}
      
      {size !== 'sm' && (
        <span>
          {isLoading ? 'Agregando...' : 
           isInMemory ? 'En memoria' : 
           justClicked ? 'Agregado!' : 
           'Agregar a memoria'}
        </span>
      )}
    </button>
  );
};

export default MemoryActionButton;