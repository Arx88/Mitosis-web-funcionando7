import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Download, Globe, FileText, Image, BarChart3, CheckCircle, AlertCircle, X, Activity, Zap, Database, Eye, Cpu } from 'lucide-react';
import ScrollReveal from './ScrollReveal';

export interface ProgressStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  details?: string[];
  progress?: number;
  startTime?: Date;
  endTime?: Date;
  sourcesFound?: number;
  imagesFound?: number;
}

export interface StreamingData {
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  details?: any;
  id?: string;
}

export interface DeepResearchProgressProps {
  steps: ProgressStep[];
  currentStep: number;
  overallProgress: number;
  isActive: boolean;
  onCancel?: () => void;
  className?: string;
  query?: string;
  taskId?: string;
  onComplete?: (report: any) => void;
}

export const DeepResearchProgress: React.FC<DeepResearchProgressProps> = ({
  steps,
  currentStep,
  overallProgress,
  isActive,
  onCancel,
  className = '',
  query = '',
  taskId,
  onComplete
}) => {
  const [streamingData, setStreamingData] = useState<StreamingData[]>([]);
  const [realTimeProgress, setRealTimeProgress] = useState<any>(null);
  const [statistics, setStatistics] = useState({
    totalSources: 0,
    totalImages: 0,
    elapsedTime: 0
  });
  const streamingRef = useRef<HTMLDivElement>(null);
  const startTimeRef = useRef<Date>(new Date());
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const streamingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Real-time progress polling from backend
  const pollProgress = useCallback(async () => {
    if (!taskId || !isActive) return;
    
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                        import.meta.env.REACT_APP_BACKEND_URL || 
                        process.env.REACT_APP_BACKEND_URL;
      
      const response = await fetch(`${backendUrl}/api/agent/deep-research/progress/${taskId}`);
      
      if (response.ok) {
        const progressData = await response.json();
        setRealTimeProgress(progressData);
        
        // Add streaming data if there's an update
        if (progressData.latest_update) {
          const newStreamingData = {
            timestamp: new Date().toISOString(),
            message: progressData.latest_update.action || 'Procesando...',
            type: 'info' as const,
            details: progressData.latest_update.details,
            id: `stream-${Date.now()}-${Math.random()}`
          };
          
          setStreamingData(prev => [...prev, newStreamingData]);
        }
        
        // Update statistics
        if (progressData.steps) {
          setStatistics(prev => ({
            ...prev,
            totalSources: progressData.sources_found || prev.totalSources,
            totalImages: progressData.images_found || prev.totalImages,
            elapsedTime: Math.floor((new Date().getTime() - startTimeRef.current.getTime()) / 1000)
          }));
        }
      }
    } catch (error) {
      console.error('Error polling progress:', error);
    }
  }, [taskId, isActive]);

  // Start polling when active
  useEffect(() => {
    if (isActive && taskId) {
      startTimeRef.current = new Date();
      pollingIntervalRef.current = setInterval(pollProgress, 1000); // Poll every second
    } else {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
    
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [isActive, taskId, pollProgress]);

  // Streaming de texto constante - EFECTO STAR WARS SIN PERSPECTIVA
  useEffect(() => {
    if (!isActive || currentStep < 0 || currentStep >= steps.length) return;

    const currentStepData = steps[currentStep];
    if (currentStepData.status !== 'active') return;

    // Párrafos de texto constante que fluyen hacia arriba
    const textParagraphs = [
      "Analizando datos en tiempo real mediante algoritmos avanzados de procesamiento semántico y extracción de información académica especializada en investigación científica multidisciplinaria.",
      "Los resultados preliminares indican patrones complejos que requieren análisis multidisciplinario para una comprensión integral del dominio investigativo y sus implicaciones teóricas.",
      "La metodología implementada utiliza técnicas de minería de datos que facilitan la identificación de correlaciones significativas entre diferentes variables del estudio académico.",
      "El proceso de validación científica asegura la credibilidad y precisión de toda la información recopilada durante esta fase de investigación profunda y exhaustiva.",
      "Las fuentes consultadas provienen de repositorios académicos reconocidos internacionalmente por su rigor científico y calidad editorial en publicaciones especializadas.",
      "La síntesis de hallazgos genera insights únicos que proporcionan una perspectiva integral del tema bajo investigación con enfoques innovadores y metodologías avanzadas.",
      "Los algoritmos de análisis de similitud textual permiten identificar coincidencias y diferencias entre diversas fuentes bibliográficas especializadas en el área temática.",
      "El framework académico empleado garantiza el cumplimiento de los más altos estándares de calidad científica establecidos por la comunidad investigativa internacional.",
      "La integración de múltiples bases de datos académicas permite una cobertura exhaustiva del panorama científico actual con análisis comparativo de tendencias emergentes.",
      "El sistema de evaluación continua monitorea la calidad de las fuentes consultadas aplicando criterios de relevancia académica y factorización de impacto científico.",
      "Las técnicas de procesamiento de lenguaje natural facilitan la extracción automática de conceptos clave y relaciones semánticas entre términos especializados del dominio.",
      "La validación cruzada de información mediante múltiples algoritmos de verificación asegura la confiabilidad de los datos procesados en cada etapa del análisis."
    ];

    let paragraphIndex = 0;
    
    // Generar texto constante fluyendo
    const generateStreamingText = () => {
      const newParagraph = {
        timestamp: new Date().toISOString(),
        message: textParagraphs[paragraphIndex],
        type: 'info' as const,
        id: `flowing-${Date.now()}-${paragraphIndex}`
      };
      
      setStreamingData(prev => [...prev, newParagraph]);
      
      paragraphIndex = (paragraphIndex + 1) % textParagraphs.length;
    };

    // Iniciar el flujo inmediatamente
    generateStreamingText();
    
    // Continuar agregando párrafos cada 3 segundos
    const streamingInterval = setInterval(generateStreamingText, 3000);

    return () => {
      clearInterval(streamingInterval);
    };
  }, [currentStep, isActive, steps, query, taskId]);

  // Clear streaming data when step changes
  useEffect(() => {
    if (currentStep >= 0 && steps[currentStep]?.status === 'active') {
      setStreamingData([]);
    }
  }, [currentStep]);

  const getStepIcon = (step: ProgressStep, index: number) => {
    const iconProps = { className: "w-3 h-3" };
    
    switch (step.status) {
      case 'completed':
        return <CheckCircle {...iconProps} className="w-3 h-3 text-green-400" />;
      case 'error':
        return <AlertCircle {...iconProps} className="w-3 h-3 text-red-400" />;
      case 'active':
        if (step.id.includes('search_initial')) return <Search {...iconProps} className="w-3 h-3 text-blue-400 animate-pulse" />;
        if (step.id.includes('search_specific')) return <Database {...iconProps} className="w-3 h-3 text-purple-400 animate-pulse" />;
        if (step.id.includes('content')) return <FileText {...iconProps} className="w-3 h-3 text-orange-400 animate-pulse" />;
        if (step.id.includes('image')) return <Image {...iconProps} className="w-3 h-3 text-pink-400 animate-pulse" />;
        if (step.id.includes('analysis')) return <Cpu {...iconProps} className="w-3 h-3 text-green-400 animate-pulse" />;
        if (step.id.includes('report')) return <Download {...iconProps} className="w-3 h-3 text-indigo-400 animate-pulse" />;
        return <Activity {...iconProps} className="w-3 h-3 text-blue-400 animate-pulse" />;
      default:
        return <div className="w-3 h-3 rounded-full bg-gray-600"></div>;
    }
  };

  // Calculate time remaining
  const getTimeRemaining = () => {
    if (overallProgress === 0) return 'Calculando...';
    const elapsed = statistics.elapsedTime;
    const estimated = (elapsed / overallProgress) * 100;
    const remaining = Math.max(0, estimated - elapsed);
    return remaining > 0 ? `${Math.ceil(remaining)}s restantes` : 'Finalizando...';
  };

  if (!isActive) return null;

  return (
    <div className={`bg-[#1E1E1F] rounded-xl border border-[rgba(255,255,255,0.08)] overflow-hidden ${className} max-w-3xl mx-auto`}>
      {/* Header minimalista y profesional */}
      <div className="p-4 border-b border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-3 h-3 text-white" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-[#DADADA]">
                Investigación Profunda
              </h3>
              <p className="text-xs text-[#ACACAC]">
                Análisis académico en tiempo real • {getTimeRemaining()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-4 text-xs text-[#ACACAC]">
              <span className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-blue-400 rounded-full"></div>
                {statistics.totalSources} fuentes
              </span>
              <span className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                {statistics.totalImages} imágenes
              </span>
            </div>
            {onCancel && (
              <button 
                onClick={onCancel}
                className="p-1.5 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
        
        {/* Barra de progreso elegante */}
        <div className="w-full bg-[#2A2A2B] rounded-full h-2 overflow-hidden">
          <div 
            className="h-2 rounded-full transition-all duration-1000 ease-out relative"
            style={{ 
              width: `${Math.max(5, overallProgress)}%`,
              background: 'linear-gradient(90deg, #1e90ff 0%, #00bfff 50%, #87ceeb 100%)'
            }}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
            <div className="absolute right-0 top-0 w-1 h-full bg-white/60 animate-pulse"></div>
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 text-xs text-[#ACACAC]">
          <span>Paso {Math.min(currentStep + 1, steps.length)} de {steps.length}</span>
          <span className="text-blue-400 font-semibold">{Math.round(overallProgress)}%</span>
        </div>
      </div>

      {/* Contenido principal rediseñado */}
      <div className="p-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Proceso de investigación */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-[#DADADA] flex items-center gap-2">
              <div className="w-1 h-3 bg-purple-500 rounded-full"></div>
              PROCESO DE INVESTIGACIÓN
            </h4>
            
            <div className="space-y-2">
              {steps.map((step, index) => {
                const isCurrentStep = index === currentStep;
                
                return (
                  <div key={step.id} className="flex gap-2 items-start">
                    <div className={`flex-shrink-0 w-6 h-6 rounded-lg flex items-center justify-center border transition-all duration-300 ${
                      step.status === 'completed' ? 'bg-green-500/20 border-green-500/60' :
                      step.status === 'error' ? 'bg-red-500/20 border-red-500/60' :
                      step.status === 'active' ? 'bg-blue-500/20 border-blue-500/60' :
                      'bg-[#2A2A2B] border-[rgba(255,255,255,0.1)]'
                    }`}>
                      {getStepIcon(step, index)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h5 className={`text-xs font-medium transition-colors ${
                          step.status === 'completed' ? 'text-green-400' :
                          step.status === 'error' ? 'text-red-400' :
                          step.status === 'active' ? 'text-blue-400' :
                          'text-[#ACACAC]'
                        }`}>
                          {step.title}
                        </h5>
                        
                        {step.status === 'active' && step.progress !== undefined && (
                          <span className="text-xs text-blue-400 bg-blue-500/20 px-1.5 py-0.5 rounded-full">
                            {step.progress}%
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-[#ACACAC] mb-1">
                        {step.description}
                      </p>

                      {step.status === 'active' && step.progress !== undefined && (
                        <div className="w-full bg-[#2A2A2B] rounded-full h-1">
                          <div 
                            className="bg-gradient-to-r from-blue-500 to-purple-500 h-1 rounded-full transition-all duration-300"
                            style={{ width: `${step.progress}%` }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Datos en tiempo real - TEXTO CONSTANTE FLUYENDO HACIA ARRIBA */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-[#DADADA] flex items-center gap-2">
              <div className="w-1 h-3 bg-blue-500 rounded-full"></div>
              DATOS EN TIEMPO REAL
            </h4>
            
            <div className="bg-[#2A2A2B] rounded-xl p-3 h-48 overflow-hidden relative">
              {streamingData.length === 0 ? (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-xs text-[#7f7f7f] italic flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse"></div>
                    Esperando datos del análisis...
                  </div>
                </div>
              ) : (
                <div className="star-wars-flow h-full overflow-hidden">
                  <div className="streaming-paragraphs">
                    {streamingData.map((data, index) => (
                      <div key={data.id} className="flowing-paragraph">
                        <p className="text-xs text-[#DADADA] leading-relaxed mb-3">
                          {data.message}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeepResearchProgress;