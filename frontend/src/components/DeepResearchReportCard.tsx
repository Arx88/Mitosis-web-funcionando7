import React, { useState } from 'react';
import { 
  Download, 
  FileText, 
  Eye, 
  Brain, 
  Clock, 
  Search, 
  File, 
  Image, 
  Calendar, 
  CheckCircle,
  BarChart3,
  Target,
  TrendingUp,
  BookOpen,
  Database,
  Users,
  Lightbulb
} from 'lucide-react';

interface DeepResearchReportCardProps {
  query: string;
  executiveSummary: string;
  sourcesAnalyzed: number;
  imagesCollected: number;
  reportFile?: string;
  duration?: number; // en segundos
  readingTime?: number; // en minutos
  timestamp: string;
  onDownloadPDF: () => void;
  onDownloadMarkdown: () => void;
  onViewInConsole: () => void;
  onUseAsMemory: () => void;
  onClose?: () => void;
  keyFindings?: string[];
  recommendations?: string[];
}

export const DeepResearchReportCard: React.FC<DeepResearchReportCardProps> = ({
  query,
  executiveSummary,
  sourcesAnalyzed,
  imagesCollected,
  reportFile,
  duration = 0,
  readingTime = 0,
  timestamp,
  onDownloadPDF,
  onDownloadMarkdown,
  onViewInConsole,
  onUseAsMemory,
  onClose,
  keyFindings = [],
  recommendations = []
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const estimatedReadingTime = readingTime || Math.ceil(executiveSummary.split(' ').length / 200);

  return (
    <div className="bg-[#383739] border border-[rgba(255,255,255,0.08)] rounded-lg overflow-hidden mb-4 max-w-full">
      {/* Header compacto */}
      <div className="p-3 border-b border-[rgba(255,255,255,0.08)]">
        <div className="flex items-start gap-2 mb-2">
          <div className="w-8 h-8 bg-[#404142] rounded-lg flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-4 h-4 text-[#DADADA]" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold text-[#ACACAC] uppercase tracking-wider">INVESTIGACIÓN</span>
              <div className="h-1 w-4 bg-[#ACACAC] rounded"></div>
            </div>
            <h3 className="text-base font-bold text-[#DADADA] mb-1 leading-tight">
              Análisis Completado
            </h3>
            <p className="text-[#ACACAC] text-xs font-medium mb-1 line-clamp-1">
              {query.length > 50 ? query.substring(0, 50) + '...' : query}
            </p>
            <div className="flex items-center gap-2 text-xs text-[#7f7f7f]">
              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                <span>{new Date(timestamp).toLocaleDateString('es-ES', { 
                  month: 'short', 
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}</span>
              </div>
              <div className="flex items-center gap-1">
                <CheckCircle className="w-3 h-3 text-[#ACACAC]" />
                <span className="text-[#ACACAC] font-medium">Finalizado</span>
              </div>
            </div>
          </div>
          {onClose && (
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onClose();
              }}
              className="w-6 h-6 bg-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.12)] rounded-lg flex items-center justify-center transition-colors flex-shrink-0"
              title="Cerrar informe"
            >
              <svg className="w-3 h-3 text-[#DADADA]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Resumen y métricas compactos */}
      <div className="p-3 border-b border-[rgba(255,255,255,0.08)]">
        <div className="text-[#DADADA] text-xs leading-relaxed mb-2">
          {executiveSummary.length > 120 
            ? executiveSummary.substring(0, 120) + "..." 
            : executiveSummary}
        </div>
        
        {/* Métricas en una fila compacta */}
        <div className="grid grid-cols-4 gap-2">
          <div className="bg-[#2A2A2B] border border-[rgba(255,255,255,0.06)] rounded-lg p-2 text-center">
            <div className="text-sm font-bold text-[#DADADA] mb-0.5">{sourcesAnalyzed}</div>
            <div className="text-xs text-[#ACACAC] font-medium">Fuentes</div>
          </div>

          <div className="bg-[#2A2A2B] border border-[rgba(255,255,255,0.06)] rounded-lg p-2 text-center">
            <div className="text-sm font-bold text-[#DADADA] mb-0.5">{imagesCollected}</div>
            <div className="text-xs text-[#ACACAC] font-medium">Archivos</div>
          </div>

          <div className="bg-[#2A2A2B] border border-[rgba(255,255,255,0.06)] rounded-lg p-2 text-center">
            <div className="text-sm font-bold text-[#DADADA] mb-0.5">{formatDuration(duration)}</div>
            <div className="text-xs text-[#ACACAC] font-medium">Tiempo</div>
          </div>

          <div className="bg-[#2A2A2B] border border-[rgba(255,255,255,0.06)] rounded-lg p-2 text-center">
            <div className="text-sm font-bold text-[#DADADA] mb-0.5">{estimatedReadingTime}min</div>
            <div className="text-xs text-[#ACACAC] font-medium">Lectura</div>
          </div>
        </div>
      </div>

      {/* Botones de acción compactos */}
      <div className="p-3">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-1 mb-2">
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onDownloadPDF();
            }}
            className="flex items-center justify-center gap-1 px-2 py-1.5 bg-[#404142] hover:bg-[#4a4b4c] text-[#DADADA] rounded text-xs font-medium transition-colors"
          >
            <Download className="w-3 h-3 text-red-400" />
            PDF
          </button>

          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onDownloadMarkdown();
            }}
            className="flex items-center justify-center gap-1 px-2 py-1.5 bg-[#404142] hover:bg-[#4a4b4c] text-[#DADADA] rounded text-xs font-medium transition-colors"
          >
            <FileText className="w-3 h-3 text-blue-400" />
            MD
          </button>

          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onViewInConsole();
            }}
            className="flex items-center justify-center gap-1 px-2 py-1.5 bg-[#404142] hover:bg-[#4a4b4c] text-[#DADADA] rounded text-xs font-medium transition-colors"
          >
            <Eye className="w-3 h-3 text-green-400" />
            Ver
          </button>

          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onUseAsMemory();
            }}
            className="flex items-center justify-center gap-1 px-2 py-1.5 bg-[#404142] hover:bg-[#4a4b4c] text-[#DADADA] rounded text-xs font-medium transition-colors"
          >
            <Brain className="w-3 h-3 text-purple-400" />
            Memoria
          </button>
        </div>

        {/* Expandible content para hallazgos y recomendaciones MÁS COMPACTO */}
        {(keyFindings.length > 0 || recommendations.length > 0) && (
          <div className="border-t border-[rgba(255,255,255,0.08)] pt-2">
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="flex items-center gap-2 text-[#ACACAC] hover:text-[#DADADA] text-xs font-medium transition-colors mb-2"
            >
              <BarChart3 className="w-3 h-3" />
              {isExpanded ? 'Ocultar detalles' : 'Mostrar hallazgos'}
            </button>
            
            {isExpanded && (
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {keyFindings.length > 0 && (
                  <div className="bg-gradient-to-br from-[rgba(59,130,246,0.1)] to-[rgba(99,102,241,0.1)] border border-blue-500/20 rounded-lg p-2">
                    <h4 className="flex items-center gap-1 text-xs font-semibold text-white mb-1">
                      <Target className="w-3 h-3 text-blue-400" />
                      Hallazgos ({keyFindings.length})
                    </h4>
                    <div className="space-y-1">
                      {keyFindings.slice(0, 1).map((finding, index) => (
                        <div key={index} className="flex items-start gap-1 p-1.5 bg-[rgba(255,255,255,0.05)] rounded border border-[rgba(255,255,255,0.1)]">
                          <div className="w-3 h-3 bg-blue-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                            <span className="text-blue-400 font-bold text-xs">{index + 1}</span>
                          </div>
                          <p className="text-xs text-[#DADADA] leading-relaxed">{finding.substring(0, 80)}...</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {recommendations.length > 0 && (
                  <div className="bg-gradient-to-br from-[rgba(16,185,129,0.1)] to-[rgba(5,150,105,0.1)] border border-green-500/20 rounded-lg p-2">
                    <h4 className="flex items-center gap-1 text-xs font-semibold text-white mb-1">
                      <Lightbulb className="w-3 h-3 text-green-400" />
                      Recomendaciones ({recommendations.length})
                    </h4>
                    <div className="space-y-1">
                      {recommendations.slice(0, 1).map((recommendation, index) => (
                        <div key={index} className="flex items-start gap-1 p-1.5 bg-[rgba(255,255,255,0.05)] rounded border border-[rgba(255,255,255,0.1)]">
                          <div className="w-3 h-3 bg-green-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                            <span className="text-green-400 font-bold text-xs">{index + 1}</span>
                          </div>
                          <p className="text-xs text-[#DADADA] leading-relaxed">{recommendation.substring(0, 80)}...</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};