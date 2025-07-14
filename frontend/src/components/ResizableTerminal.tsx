import React, { useState, useCallback, useRef, useEffect } from 'react';

interface ResizableTerminalProps {
  children: React.ReactNode;
  initialHeight?: number;
  minHeight?: number;
  maxHeight?: number;
  onResize?: (height: number) => void;
}

export const ResizableTerminal: React.FC<ResizableTerminalProps> = ({
  children,
  initialHeight = 300,
  minHeight = 200,
  maxHeight = 600,
  onResize
}) => {
  const [height, setHeight] = useState(initialHeight);
  const [isResizing, setIsResizing] = useState(false);
  const startY = useRef<number>(0);
  const startHeight = useRef<number>(0);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsResizing(true);
    startY.current = e.clientY;
    startHeight.current = height;
    
    // Prevent text selection during resize
    e.preventDefault();
  }, [height]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return;
    
    const deltaY = e.clientY - startY.current;
    const newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight.current + deltaY));
    
    setHeight(newHeight);
    onResize?.(newHeight);
  }, [isResizing, minHeight, maxHeight, onResize]);

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
    <div className="flex flex-col">
      <div
        className="relative border-l border-[rgba(255,255,255,0.08)]"
        style={{ height: `${height}px` }}
      >
        {children}
      </div>
      
      {/* Resize Handle */}
      <div
        className={`h-1 bg-[rgba(255,255,255,0.08)] cursor-ns-resize hover:bg-[rgba(255,255,255,0.16)] transition-colors ${
          isResizing ? 'bg-blue-400' : ''
        }`}
        onMouseDown={handleMouseDown}
      >
        <div className="h-full flex items-center justify-center">
          <div className="w-8 h-0.5 bg-[rgba(255,255,255,0.3)] rounded-full"></div>
        </div>
      </div>
    </div>
  );
};