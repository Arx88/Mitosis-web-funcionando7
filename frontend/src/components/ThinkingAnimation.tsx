import React, { useEffect, useState } from 'react';
import { Bot, Zap, Brain, Search, Cpu, Eye, BookOpen, Sparkles, Lightbulb } from 'lucide-react';

export interface ThinkingAnimationProps {
  isVisible: boolean;
  message?: string;
  className?: string;
}

const thinkingPhrases = [
  "Analizando pregunta",
  "Procesando información",
  "Generando respuesta",
  "Buscando conexiones",
  "Evaluando contexto",
  "Organizando ideas",
  "Refinando respuesta",
  "Validando información",
  "Sintetizando datos",
  "Estructurando contenido",
  "Revisando coherencia",
  "Optimizando respuesta",
  "Comprendiendo matices",
  "Explorando posibilidades",
  "Conectando conceptos",
  "Analizando implicaciones",
  "Formulando respuesta",
  "Verificando precisión",
  "Elaborando detalles",
  "Completando análisis"
];

const thinkingIcons = [
  { icon: Brain, color: 'text-purple-400' },
  { icon: Search, color: 'text-blue-400' },
  { icon: Cpu, color: 'text-green-400' },
  { icon: Eye, color: 'text-yellow-400' },
  { icon: BookOpen, color: 'text-indigo-400' },
  { icon: Sparkles, color: 'text-pink-400' },
  { icon: Lightbulb, color: 'text-orange-400' },
  { icon: Zap, color: 'text-cyan-400' }
];

export const ThinkingAnimation: React.FC<ThinkingAnimationProps> = ({
  isVisible,
  message,
  className = ''
}) => {
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [currentIconIndex, setCurrentIconIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (!isVisible) return;

    const interval = setInterval(() => {
      setIsAnimating(true);
      
      setTimeout(() => {
        setCurrentPhraseIndex((prev) => (prev + 1) % thinkingPhrases.length);
        setCurrentIconIndex((prev) => (prev + 1) % thinkingIcons.length);
        setIsAnimating(false);
      }, 150);
    }, 2000);

    return () => clearInterval(interval);
  }, [isVisible]);

  if (!isVisible) return null;

  const currentIcon = thinkingIcons[currentIconIndex];
  const IconComponent = currentIcon.icon;

  return (
    <div className={`flex items-start gap-3 py-2 px-4 ${className}`}>
      <div className="flex-shrink-0">
        {/* Mismo robot que en Agente - sin círculo */}
        <div className="w-8 h-8 bg-[#404142] rounded-full flex items-center justify-center">
          <svg className="w-4 h-4 text-[#DADADA]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
          </svg>
        </div>
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium text-[#DADADA]">Agente</span>
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Thinking Icon - más sutil */}
          <div className="relative">
            <div className={`w-4 h-4 rounded-full flex items-center justify-center transition-all duration-300 ${isAnimating ? 'scale-75 opacity-50' : 'scale-100 opacity-100'}`}>
              <IconComponent className={`w-3 h-3 ${currentIcon.color} animate-pulse`} />
            </div>
          </div>

          {/* Thinking Text - más minimalista, lighter font */}
          <div className={`text-sm font-light text-[#ACACAC] transition-all duration-300 ${isAnimating ? 'opacity-50 transform scale-95' : 'opacity-100 transform scale-100'}`}>
            {message || thinkingPhrases[currentPhraseIndex]}
          </div>
          
          {/* Animated dots - más sutiles, properly centered */}
          <div className="flex items-center gap-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-1 h-1 bg-blue-400 rounded-full animate-bounce opacity-60"
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};