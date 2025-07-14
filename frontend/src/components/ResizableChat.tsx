import React, { useState, useCallback, useRef, useEffect } from 'react';

interface ResizableChatProps {
  children: React.ReactNode;
  initialWidth?: string;
  minWidth?: number;
  maxWidth?: number;
  onResize?: (width: number) => void;
}

export const ResizableChat: React.FC<ResizableChatProps> = ({
  children,
  initialWidth = '50%',
  minWidth = 300,
  maxWidth = 800,
  onResize
}) => {
  const [width, setWidth] = useState(initialWidth);
  const [isResizing, setIsResizing] = useState(false);
  const startX = useRef<number>(0);
  const startWidth = useRef<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsResizing(true);
    startX.current = e.clientX;
    
    if (containerRef.current) {
      startWidth.current = containerRef.current.offsetWidth;
    }
    
    // Prevent text selection during resize
    e.preventDefault();
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return;
    
    const deltaX = e.clientX - startX.current;
    const newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth.current + deltaX));
    
    setWidth(`${newWidth}px`);
    onResize?.(newWidth);
  }, [isResizing, minWidth, maxWidth, onResize]);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isResizing, handleMouseMove, handleMouseUp]);

  return (
    <div className="flex h-full">
      <div
        ref={containerRef}
        className="flex flex-col overflow-hidden"
        style={{ width }}
      >
        {children}
      </div>
      
      {/* Resize Handle */}
      <div
        className={`w-1 bg-[rgba(255,255,255,0.08)] cursor-ew-resize hover:bg-[rgba(255,255,255,0.16)] transition-colors ${
          isResizing ? 'bg-blue-400' : ''
        }`}
        onMouseDown={handleMouseDown}
      >
        <div className="h-full flex items-center justify-center">
          <div className="h-8 w-0.5 bg-[rgba(255,255,255,0.3)] rounded-full"></div>
        </div>
      </div>
    </div>
  );
};