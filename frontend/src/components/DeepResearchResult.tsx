import React, { useState } from 'react';
import { Download, FileText, Eye, Brain, Clock, Search, File, Image, Calendar, CheckCircle } from 'lucide-react';

interface DeepResearchResultProps {
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
  keyFindings?: string[];
  recommendations?: string[];
}

export const DeepResearchResult: React.FC<DeepResearchResultProps> = ({
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
    <div className="bg-[#383739] border border-[rgba(255,255,255,0.08)] rounded-xl p-6 mb-4">
      {/* Header */}
      <div className="flex items-start gap-4 mb-6">
        <div className="w-12 h-12 bg-[#404142] rounded-lg flex items-center justify-center">
          <Search className="w-6 h-6 text-[#DADADA]" />
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-[#DADADA] mb-2 leading-tight">
            🔬 Investigación Profunda Completada
          </h3>
          <p className="text-[#ACACAC] text-sm font-medium mb-1">
            Tema: {query}
          </p>
          <div className="flex items-center gap-2 text-xs text-[#7f7f7f]">
            <Calendar className="w-3 h-3" />
            <span>{new Date(timestamp).toLocaleString()}</span>
            <CheckCircle className="w-3 h-3 text-[#ACACAC] ml-2" />
            <span className="text-[#ACACAC]">Completado exitosamente</span>
          </div>
        </div>
      </div>

      {/* Statistics Panel */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-[#2A2A2B] border border-[rgba(255,255,255,0.06)] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <File className="w-4 h-4 text-[#DADADA]" />
            <span className="text-xs font-medium text-[#DADADA]">FUENTES</span>
          </div>
          <div className="text-2xl font-bold text-[#DADADA]">{sourcesAnalyzed}</div>
          <div className="text-xs text-[#ACACAC]">consultadas</div>
        </div>

        <div className="bg-[#2A2A2B] border border-[rgba(255,255,255,0.06)] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Image className="w-4 h-4 text-[#DADADA]" />
            <span className="text-xs font-medium text-[#DADADA]">IMÁGENES</span>
          </div>
          <div className="text-2xl font-bold text-[#DADADA]">{imagesCollected}</div>
          <div className="text-xs text-[#ACACAC]">recopiladas</div>
        </div>

        <div className="bg-[#2A2A2B] border border-[rgba(255,255,255,0.06)] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-[#DADADA]" />
            <span className="text-xs font-medium text-[#DADADA]">TIEMPO</span>
          </div>
          <div className="text-2xl font-bold text-[#DADADA]">{formatDuration(duration)}</div>
          <div className="text-xs text-[#ACACAC]">procesamiento</div>
        </div>

        <div className="bg-[#2A2A2B] border border-[rgba(255,255,255,0.06)] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-[#DADADA]" />
            <span className="text-xs font-medium text-[#DADADA]">LECTURA</span>
          </div>
          <div className="text-2xl font-bold text-[#DADADA]">{estimatedReadingTime}</div>
          <div className="text-xs text-[#ACACAC]">min aprox.</div>
        </div>
      </div>

      {/* Summary */}
      <div className="mb-6">
        <h4 className="text-lg font-semibold text-[#DADADA] mb-3 flex items-center gap-2">
          <FileText className="w-5 h-5 text-[#DADADA]" />
          Resumen Ejecutivo
        </h4>
        <div className="bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] rounded-lg p-4">
          <p className="text-[#DADADA] text-sm leading-relaxed">
            {executiveSummary}
          </p>
          
          {/* Expandible content */}
          {(keyFindings.length > 0 || recommendations.length > 0) && (
            <div className="mt-4">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-[#ACACAC] hover:text-[#DADADA] text-sm font-medium transition-colors"
              >
                {isExpanded ? 'Ver menos' : 'Ver hallazgos y recomendaciones'}
              </button>
              
              {isExpanded && (
                <div className="mt-4 space-y-4">
                  {keyFindings.length > 0 && (
                    <div>
                      <h5 className="text-sm font-semibold text-[#DADADA] mb-2">🔍 Hallazgos Clave:</h5>
                      <ul className="space-y-1">
                        {keyFindings.slice(0, 3).map((finding, index) => (
                          <li key={index} className="text-sm text-[#ACACAC] flex items-start gap-2">
                            <span className="text-[#DADADA] font-bold">•</span>
                            <span>{finding}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {recommendations.length > 0 && (
                    <div>
                      <h5 className="text-sm font-semibold text-[#DADADA] mb-2">💡 Recomendaciones:</h5>
                      <ul className="space-y-1">
                        {recommendations.slice(0, 3).map((recommendation, index) => (
                          <li key={index} className="text-sm text-[#ACACAC] flex items-start gap-2">
                            <span className="text-[#DADADA] font-bold">•</span>
                            <span>{recommendation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <button
          onClick={onDownloadPDF}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-[#404142] hover:bg-[#4a4b4c] text-[#DADADA] rounded-lg text-sm font-medium transition-colors"
        >
          <Download className="w-4 h-4" />
          PDF
        </button>

        <button
          onClick={onDownloadMarkdown}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-[#404142] hover:bg-[#4a4b4c] text-[#DADADA] rounded-lg text-sm font-medium transition-colors"
        >
          <FileText className="w-4 h-4" />
          .MD
        </button>

        <button
          onClick={onViewInConsole}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-[#404142] hover:bg-[#4a4b4c] text-[#DADADA] rounded-lg text-sm font-medium transition-colors"
        >
          <Eye className="w-4 h-4" />
          Consola
        </button>

        <button
          onClick={onUseAsMemory}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-[#404142] hover:bg-[#4a4b4c] text-[#DADADA] rounded-lg text-sm font-medium transition-colors"
        >
          <Brain className="w-4 h-4" />
          Memoria
        </button>
      </div>
    </div>
  );
};