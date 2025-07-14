import { useEffect, useRef, useState } from 'react';

interface ScrollRevealProps {
  children: string;
  scrollContainerRef?: React.RefObject<HTMLElement>;
  enableBlur?: boolean;
  baseOpacity?: number;
  baseRotation?: number;
  blurStrength?: number;
  containerClassName?: string;
  textClassName?: string;
  rotationEnd?: string;
  wordAnimationEnd?: string;
  autoScroll?: boolean;
  index?: number;
  onAnimationComplete?: () => void;
  streamingMode?: boolean;
}

const ScrollReveal: React.FC<ScrollRevealProps> = ({
  children,
  scrollContainerRef,
  enableBlur = true,
  baseOpacity = 0,
  baseRotation = 0,
  blurStrength = 4,
  containerClassName = "",
  textClassName = "",
  autoScroll = true,
  index = 0,
  onAnimationComplete,
  streamingMode = false
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [animationPhase, setAnimationPhase] = useState<'entering' | 'visible' | 'exiting'>('entering');

  useEffect(() => {
    if (!autoScroll) return;

    // Para modo streaming, animación más fluida y continua
    if (streamingMode) {
      const enterDelay = index * 200; // Más rápido para fluidez
      
      const enterTimer = setTimeout(() => {
        setIsVisible(true);
        setAnimationPhase('visible');
        onAnimationComplete?.();
      }, enterDelay);

      // Transición más larga para fadeout continuo
      const exitTimer = setTimeout(() => {
        setAnimationPhase('exiting');
        setTimeout(() => {
          setIsVisible(false);
        }, 1200); // Transición más larga para fadeout suave
      }, enterDelay + 4000); // Más tiempo visible

      return () => {
        clearTimeout(enterTimer);
        clearTimeout(exitTimer);
      };
    } else {
      // Modo normal (existente)
      const enterDelay = index * 300;
      
      const enterTimer = setTimeout(() => {
        setIsVisible(true);
        setAnimationPhase('visible');
        onAnimationComplete?.();
      }, enterDelay);

      const exitTimer = setTimeout(() => {
        setAnimationPhase('exiting');
        setTimeout(() => {
          setIsVisible(false);
        }, 800);
      }, enterDelay + 3000);

      return () => {
        clearTimeout(enterTimer);
        clearTimeout(exitTimer);
      };
    }
  }, [autoScroll, index, onAnimationComplete, streamingMode]);

  const getAnimationStyles = () => {
    const baseStyles = {
      transition: streamingMode 
        ? 'all 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94)' // Más suave para streaming
        : 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
      transformOrigin: '0% 50%',
    };

    switch (animationPhase) {
      case 'entering':
        return {
          ...baseStyles,
          opacity: 0,
          transform: streamingMode 
            ? `translateY(30px) scale(0.92)` // Más sutil para streaming
            : `translateY(20px) scale(0.95)`,
          filter: enableBlur ? `blur(${blurStrength}px)` : 'none',
        };
      case 'visible':
        return {
          ...baseStyles,
          opacity: 1,
          transform: 'translateY(0px) scale(1)',
          filter: 'blur(0px)',
        };
      case 'exiting':
        return {
          ...baseStyles,
          opacity: 0,
          transform: streamingMode
            ? 'translateY(-30px) scale(0.98)' // Fadeout más suave hacia arriba
            : 'translateY(-20px) scale(1)',
          filter: enableBlur ? `blur(${blurStrength/2}px)` : 'none',
        };
      default:
        return baseStyles;
    }
  };

  if (!isVisible && animationPhase !== 'entering') return null;

  return (
    <div 
      ref={containerRef} 
      className={`${containerClassName} ${streamingMode ? 'streaming-text' : ''}`}
      style={getAnimationStyles()}
    >
      <p className={`leading-relaxed ${textClassName}`}>
        {children}
      </p>
    </div>
  );
};

export default ScrollReveal;