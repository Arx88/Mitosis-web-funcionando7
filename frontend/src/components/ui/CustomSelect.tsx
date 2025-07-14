import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, Wifi, WifiOff } from 'lucide-react';

interface Option {
  value: string;
  label: string;
  disabled?: boolean;
}

interface CustomSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: Option[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  loading?: boolean;
  showConnectionStatus?: boolean;
  isConnected?: boolean;
  onRefresh?: () => void;
}

export const CustomSelect: React.FC<CustomSelectProps> = ({
  value,
  onChange,
  options,
  placeholder = "Seleccionar...",
  disabled = false,
  className = '',
  loading = false,
  showConnectionStatus = false,
  isConnected = false,
  onRefresh
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedOption = options.find(opt => opt.value === value);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleOptionClick = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleToggle = () => {
    if (disabled) return;
    setIsOpen(!isOpen);
  };

  const handleRefresh = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onRefresh) {
      onRefresh();
    }
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Main button */}
      <button
        type="button"
        onClick={handleToggle}
        disabled={disabled}
        className={`
          w-full bg-[#2A2A2B] rounded-lg p-3 text-left text-[#DADADA]
          border border-[rgba(255,255,255,0.08)]
          focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-all duration-200
          flex items-center justify-between
          ${isOpen ? 'border-[rgba(255,255,255,0.16)]' : ''}
        `}
      >
        <div className="flex items-center gap-2 flex-1">
          {showConnectionStatus && (
            <div className="flex items-center gap-1">
              {isConnected ? (
                <Wifi className="w-4 h-4 text-green-400" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-400" />
              )}
            </div>
          )}
          
          <span className={selectedOption ? 'text-[#DADADA]' : 'text-[#ACACAC]'}>
            {loading ? 'Cargando...' : (selectedOption?.label || placeholder)}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {onRefresh && (
            <button
              type="button"
              onClick={handleRefresh}
              className="p-1 hover:bg-[rgba(255,255,255,0.08)] rounded transition-colors"
            >
              <svg className="w-4 h-4 text-[#ACACAC]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          )}
          
          <ChevronDown className={`w-4 h-4 text-[#ACACAC] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-[#2A2A2B] border border-[rgba(255,255,255,0.08)] rounded-lg shadow-lg z-50 max-h-60 overflow-hidden">
          {/* Search input */}
          {options.length > 5 && (
            <div className="p-2 border-b border-[rgba(255,255,255,0.08)]">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar..."
                className="w-full bg-[#383739] rounded p-2 text-[#DADADA] text-sm focus:outline-none focus:ring-1 focus:ring-[rgba(255,255,255,0.16)]"
              />
            </div>
          )}
          
          {/* Options */}
          <div className="max-h-48 overflow-y-auto custom-scrollbar">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-[#ACACAC] text-sm">
                {loading ? 'Cargando opciones...' : 'No se encontraron opciones'}
              </div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleOptionClick(option.value)}
                  disabled={option.disabled}
                  className={`
                    w-full px-3 py-2 text-left text-sm transition-colors
                    flex items-center justify-between
                    ${option.disabled ? 'text-[#606060] cursor-not-allowed' : 'text-[#DADADA] hover:bg-[rgba(255,255,255,0.08)]'}
                    ${option.value === value ? 'bg-[rgba(255,255,255,0.06)]' : ''}
                  `}
                >
                  <span>{option.label}</span>
                  {option.value === value && (
                    <Check className="w-4 h-4 text-blue-400" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};