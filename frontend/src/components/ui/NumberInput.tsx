import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

interface NumberInputProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  className?: string;
  placeholder?: string;
}

export const NumberInput: React.FC<NumberInputProps> = ({
  value,
  onChange,
  min = 0,
  max = Infinity,
  step = 1,
  disabled = false,
  className = '',
  placeholder
}) => {
  const [isFocused, setIsFocused] = useState(false);

  const handleIncrement = () => {
    if (disabled) return;
    const newValue = Math.min(value + step, max);
    onChange(newValue);
  };

  const handleDecrement = () => {
    if (disabled) return;
    const newValue = Math.max(value - step, min);
    onChange(newValue);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    const newValue = parseFloat(e.target.value) || 0;
    if (newValue >= min && newValue <= max) {
      onChange(newValue);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      handleIncrement();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      handleDecrement();
    }
  };

  return (
    <div className={`relative ${className}`}>
      <input
        type="number"
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        disabled={disabled}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        className={`
          w-full bg-[#2A2A2B] rounded-lg p-3 pr-12 text-[#DADADA] 
          border border-[rgba(255,255,255,0.08)] 
          focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-all duration-200
          ${isFocused ? 'border-[rgba(255,255,255,0.16)]' : ''}
          [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none
        `}
      />
      
      {/* Custom increment/decrement buttons */}
      <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex flex-col">
        <button
          type="button"
          onClick={handleIncrement}
          disabled={disabled || value >= max}
          className={`
            p-1 hover:bg-[rgba(255,255,255,0.08)] rounded transition-colors
            disabled:opacity-40 disabled:cursor-not-allowed
            ${!disabled && value < max ? 'text-[#ACACAC] hover:text-[#DADADA]' : 'text-[#606060]'}
          `}
        >
          <ChevronUp className="w-3 h-3" />
        </button>
        
        <button
          type="button"
          onClick={handleDecrement}
          disabled={disabled || value <= min}
          className={`
            p-1 hover:bg-[rgba(255,255,255,0.08)] rounded transition-colors
            disabled:opacity-40 disabled:cursor-not-allowed
            ${!disabled && value > min ? 'text-[#ACACAC] hover:text-[#DADADA]' : 'text-[#606060]'}
          `}
        >
          <ChevronDown className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};