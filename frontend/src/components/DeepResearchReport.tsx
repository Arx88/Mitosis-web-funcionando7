import React, { useState, useEffect } from 'react';
import { 
  Download, 
  Eye, 
  FileText, 
  Calendar, 
  BarChart3, 
  Globe, 
  Image, 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  FileDown, 
  Share2, 
  ExternalLink,
  BookOpen,
  Target,
  Lightbulb,
  Search,
  ArrowRight,
  Star,
  Database,
  Zap,
  Brain,
  Play,
  X
} from 'lucide-react';
import { AcademicMarkdownRenderer } from './AcademicMarkdownRenderer';
import { MemoryActionButton } from './MemoryActionButton';
import { 
  generateAcademicTitle, 
  generateAcademicMarkdown, 
  downloadAsMarkdown, 
  downloadAsPDF,
  generateFilename,
  saveReportToBackend 
} from '../utils/academicReportUtils';

export interface ResearchReport {
  query: string;
  sourcesAnalyzed: number;
  imagesCollected: number;
  reportFile?: string;
  executiveSummary?: string;
  keyFindings?: string[];
  recommendations?: string[];
  timestamp: string;
  console_report?: string;
  completionTime?: number;
  wordCount?: number;
  processingTime?: number;
}

export interface DeepResearchReportProps {
  report: ResearchReport;
  onDownload: () => void;
  onViewInConsole: () => void;
  onShare?: () => void;
  onAddToMemory?: (report: ResearchReport) => void;
  onClose?: () => void;
  isInMemory?: boolean;
  className?: string;
  taskId?: string;
}

export const DeepResearchReport: React.FC<DeepResearchReportProps> = ({
  report,
  onDownload,
  onViewInConsole,
  onShare,
  onAddToMemory,
  onClose,
  isInMemory = false,
  className = '',
  taskId
}) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [activeTab, setActiveTab] = useState<'overview' | 'findings' | 'recommendations'>('overview');
  const [isAddingToMemory, setIsAddingToMemory] = useState(false);
  const [isViewingConsole, setIsViewingConsole] = useState(false);
  const [memoryFeedback, setMemoryFeedback] = useState<string | null>(null);
  const [consoleFeedback, setConsoleFeedback] = useState<string | null>(null);
  const [addedToConsoleIds, setAddedToConsoleIds] = useState<Set<string>>(new Set());
  
  // Generate academic title
  const academicTitle = generateAcademicTitle(report.query, report.executiveSummary);
  
  // Generate full markdown content
  const markdownContent = generateAcademicMarkdown(
    academicTitle,
    report.query,
    report.executiveSummary || 'Resumen ejecutivo no disponible',
    report.keyFindings || [],
    report.recommendations || [],
    [], // sources - would need to be passed from backend
    {
      sourcesAnalyzed: report.sourcesAnalyzed,
      imagesCollected: report.imagesCollected,
      timestamp: report.timestamp,
      wordCount: report.wordCount,
      processingTime: report.processingTime
    }
  );

  const handleDownloadMarkdown = async () => {
    setIsDownloading(true);
    setDownloadProgress(0);
    
    try {
      // Simulate download progress
      const progressInterval = setInterval(() => {
        setDownloadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 100);
      
      const filename = generateFilename(academicTitle, 'md');
      
      // Save to backend if taskId is available
      if (taskId) {
        await saveReportToBackend(markdownContent, filename, taskId);
      }
      
      await downloadAsMarkdown(markdownContent, filename);
      
      clearInterval(progressInterval);
      setDownloadProgress(100);
      
      setTimeout(() => {
        setIsDownloading(false);
        setDownloadProgress(0);
      }, 1000);
      
    } catch (error) {
      console.error('Error downloading markdown:', error);
      setIsDownloading(false);
      setDownloadProgress(0);
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  // Función para manejar descarga de PDF
  const handleDownloadPDF = async () => {
    setIsDownloading(true);
    setDownloadProgress(0);
    
    try {
      const progressInterval = setInterval(() => {
        setDownloadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 100);
      
      const filename = generateFilename(academicTitle, 'pdf');
      await downloadAsPDF(markdownContent, filename);
      
      clearInterval(progressInterval);
      setDownloadProgress(100);
      
      setTimeout(() => {
        setIsDownloading(false);
        setDownloadProgress(0);
      }, 1000);
      
    } catch (error) {
      console.error('Error downloading PDF:', error);
      setIsDownloading(false);
      setDownloadProgress(0);
    }
  };

  // Función para visualizar PDF - SOLO abrir archivo, NO agregar a consola
  const handleViewPDF = async () => {
    setIsViewingConsole(true);
    setConsoleFeedback('Abriendo archivo...');
    
    try {
      // Solo generar y abrir el PDF
      const filename = generateFilename(academicTitle, 'pdf');
      const pdfBlob = await generatePDFWithCustomCSS(markdownContent, filename);
      const pdfUrl = URL.createObjectURL(pdfBlob);
      
      // Abrir en nueva ventana
      window.open(pdfUrl, '_blank');
      
      setConsoleFeedback('✓ Archivo abierto');
      setTimeout(() => setConsoleFeedback(null), 2000);
    } catch (error) {
      console.error('Error viewing PDF:', error);
      setConsoleFeedback('Error al abrir archivo');
      setTimeout(() => setConsoleFeedback(null), 2000);
    } finally {
      setIsViewingConsole(false);
    }
  };

  // Función para agregar a memoria
  const handleAddToMemory = async () => {
    if (isInMemory || !onAddToMemory) return;
    
    setIsAddingToMemory(true);
    setMemoryFeedback('Agregando a memoria...');
    
    try {
      const result = await onAddToMemory(report);
      if (result === null) {
        // Duplicate detected
        setMemoryFeedback('Ya está en memoria');
        console.warn('Report already exists in memory');
      } else {
        setMemoryFeedback('✓ Agregado a memoria');
      }
    } catch (error) {
      console.error('Error adding to memory:', error);
      setMemoryFeedback('Error al agregar');
    } finally {
      setIsAddingToMemory(false);
      setTimeout(() => setMemoryFeedback(null), 2000);
    }
  };

  return (
    <div className={`space-y-3 max-w-full ${className}`}>
      {/* Header compacto para chat */}
      <div className="bg-[#2a2a2b] rounded-lg border border-[rgba(255,255,255,0.08)] p-3 shadow-sm">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="w-5 h-5 bg-[#404142] rounded flex items-center justify-center flex-shrink-0">
              <CheckCircle className="w-3 h-3 text-green-400" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-semibold text-[#DADADA] truncate">
                Investigación Completada
              </h3>
              <p className="text-xs text-[#ACACAC] truncate">
                {report.query.length > 40 ? report.query.substring(0, 40) + '...' : report.query}
              </p>
            </div>
          </div>
          {onClose && (
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onClose();
              }}
              className="w-5 h-5 bg-[#404142] hover:bg-[#505152] rounded flex items-center justify-center transition-colors flex-shrink-0"
              title="Cerrar informe"
            >
              <X className="w-3 h-3 text-[#ACACAC]" />
            </button>
          )}
        </div>

        {/* Métricas compactas en una línea */}
        <div className="flex items-center gap-3 text-xs text-[#ACACAC] mb-2">
          <span className="flex items-center gap-1">
            <Database className="w-3 h-3" />
            {report.sourcesAnalyzed} fuentes
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {report.processingTime ? formatDuration(report.processingTime) : 'N/A'}
          </span>
          <span className="flex items-center gap-1">
            <FileText className="w-3 h-3" />
            {report.wordCount ? (report.wordCount > 1000 ? `${Math.round(report.wordCount/1000)}k` : report.wordCount) : 'N/A'} palabras
          </span>
        </div>

        {/* Resumen muy compacto */}
        <div className="mb-3">
          <p className="text-xs text-[#DADADA] leading-relaxed line-clamp-2">
            {report.executiveSummary ? 
              report.executiveSummary.substring(0, 120) + (report.executiveSummary.length > 120 ? '...' : '')
              : 'Investigación completada exitosamente.'
            }
          </p>
        </div>
      </div>

      {/* Tabs de navegación más compactas */}
      <div className="bg-[#2a2a2b] rounded-lg border border-[rgba(255,255,255,0.08)] overflow-hidden">
        <div className="flex border-b border-[rgba(255,255,255,0.08)]">
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setActiveTab('overview');
            }}
            className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium transition-all ${
              activeTab === 'overview'
                ? 'bg-[rgba(172,172,172,0.1)] text-[#ACACAC] border-b-2 border-[#ACACAC]'
                : 'text-[#7f7f7f] hover:text-[#ACACAC] hover:bg-[rgba(255,255,255,0.04)]'
            }`}
          >
            <BookOpen className="w-3 h-3" />
            Resumen
          </button>
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setActiveTab('findings');
            }}
            className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium transition-all ${
              activeTab === 'findings'
                ? 'bg-[rgba(172,172,172,0.1)] text-[#ACACAC] border-b-2 border-[#ACACAC]'
                : 'text-[#7f7f7f] hover:text-[#ACACAC] hover:bg-[rgba(255,255,255,0.04)]'
            }`}
          >
            <Target className="w-3 h-3" />
            Hallazgos
          </button>
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setActiveTab('recommendations');
            }}
            className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium transition-all ${
              activeTab === 'recommendations'
                ? 'bg-[rgba(172,172,172,0.1)] text-[#ACACAC] border-b-2 border-[#ACACAC]'
                : 'text-[#7f7f7f] hover:text-[#ACACAC] hover:bg-[rgba(255,255,255,0.04)]'
            }`}
          >
            <Lightbulb className="w-3 h-3" />
            Recomendaciones
          </button>
        </div>

        {/* Contenido de las tabs más compacto */}
        <div className="p-3 max-h-32 overflow-y-auto">
          {activeTab === 'overview' && (
            <div className="space-y-2">
              <div className="prose prose-invert max-w-none">
                <p className="text-xs text-[#DADADA] leading-relaxed">
                  {report.executiveSummary ? 
                    report.executiveSummary.substring(0, 200) + (report.executiveSummary.length > 200 ? '...' : '')
                    : 'Resumen ejecutivo no disponible'
                  }
                </p>
              </div>
            </div>
          )}

          {activeTab === 'findings' && (
            <div className="space-y-2">
              <div className="space-y-1">
                {report.keyFindings && report.keyFindings.length > 0 ? (
                  report.keyFindings.slice(0, 2).map((finding, index) => (
                    <div key={index} className="flex items-start gap-2 p-2 bg-[#1e1e1f] rounded border border-[rgba(255,255,255,0.06)]">
                      <div className="w-4 h-4 bg-[#404142] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-xs text-[#ACACAC] font-bold">{index + 1}</span>
                      </div>
                      <p className="text-xs text-[#DADADA] leading-relaxed">{finding.substring(0, 150)}...</p>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-3 text-[#ACACAC]">
                    <p className="text-xs">No se encontraron hallazgos específicos</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'recommendations' && (
            <div className="space-y-2">
              <div className="space-y-1">
                {report.recommendations && report.recommendations.length > 0 ? (
                  report.recommendations.slice(0, 2).map((recommendation, index) => (
                    <div key={index} className="flex items-start gap-2 p-2 bg-[#1e1e1f] rounded border border-[rgba(255,255,255,0.06)]">
                      <div className="w-4 h-4 bg-[#404142] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <ArrowRight className="w-2 h-2 text-[#ACACAC]" />
                      </div>
                      <p className="text-xs text-[#DADADA] leading-relaxed">{recommendation.substring(0, 150)}...</p>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-3 text-[#ACACAC]">
                    <p className="text-xs">No se generaron recomendaciones específicas</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Botones de acción compactos - SIN agregar a consola */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {/* 1. Descargar PDF */}
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            handleDownloadPDF();
          }}
          disabled={isDownloading}
          className="flex items-center gap-2 px-3 py-2 bg-[#404142] hover:bg-[#505152] text-[#DADADA] rounded text-xs font-medium transition-all disabled:opacity-50 shadow-sm hover:shadow-md"
        >
          <FileDown className="w-3 h-3 text-red-400" />
          <span>PDF</span>
          {isDownloading && downloadProgress > 0 && (
            <div className="absolute inset-0 bg-red-400/20 animate-pulse"></div>
          )}
        </button>
        
        {/* 2. Descargar MD */}
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            handleDownloadMarkdown();
          }}
          disabled={isDownloading}
          className="flex items-center gap-2 px-3 py-2 bg-[#404142] hover:bg-[#505152] text-[#DADADA] rounded text-xs font-medium transition-all disabled:opacity-50 shadow-sm hover:shadow-md"
        >
          <Download className="w-3 h-3 text-blue-400" />
          <span>MD</span>
          {isDownloading && downloadProgress > 0 && (
            <div className="absolute inset-0 bg-blue-400/20 animate-pulse"></div>
          )}
        </button>

        {/* 3. Ver archivo (solo abrir, NO consola) */}
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setIsViewingConsole(true);
            setConsoleFeedback('Abriendo archivo...');
            
            try {
              // Solo abrir el PDF, NO agregar a consola
              const filename = generateFilename(academicTitle, 'pdf');
              generatePDFWithCustomCSS(markdownContent, filename).then(pdfBlob => {
                const pdfUrl = URL.createObjectURL(pdfBlob);
                window.open(pdfUrl, '_blank');
                setConsoleFeedback('✓ Archivo abierto');
                setTimeout(() => setConsoleFeedback(null), 2000);
              });
            } catch (error) {
              setConsoleFeedback('Error al abrir');
              setTimeout(() => setConsoleFeedback(null), 2000);
            } finally {
              setIsViewingConsole(false);
            }
          }}
          disabled={isViewingConsole}
          className="flex items-center gap-2 px-3 py-2 bg-[#404142] hover:bg-[#505152] text-[#DADADA] rounded text-xs font-medium transition-all disabled:opacity-50 shadow-sm hover:shadow-md"
        >
          <Eye className="w-3 h-3 text-green-400" />
          <span>Ver</span>
          {isViewingConsole && (
            <div className="absolute inset-0 bg-green-400/20 animate-pulse"></div>
          )}
        </button>
        
        {/* 4. Usar en memoria */}
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            handleAddToMemory();
          }}
          disabled={isAddingToMemory || isInMemory}
          className="flex items-center gap-2 px-3 py-2 bg-[#404142] hover:bg-[#505152] text-[#DADADA] rounded text-xs font-medium transition-all disabled:opacity-50 shadow-sm hover:shadow-md"
        >
          <Brain className="w-3 h-3 text-purple-400" />
          <span>{isInMemory ? 'En memoria' : 'Memoria'}</span>
          {isAddingToMemory && (
            <div className="absolute inset-0 bg-purple-400/20 animate-pulse"></div>
          )}
        </button>
      </div>

      {/* Feedback messages compacto */}
      {(memoryFeedback || consoleFeedback) && (
        <div className="bg-[#2a2a2b] rounded border border-[rgba(255,255,255,0.08)] p-2">
          <div className="flex items-center gap-2 text-xs">
            {memoryFeedback && (
              <div className="flex items-center gap-1 text-purple-400">
                <Brain className="w-3 h-3" />
                <span>{memoryFeedback}</span>
              </div>
            )}
            {consoleFeedback && (
              <div className="flex items-center gap-1 text-green-400">
                <Eye className="w-3 h-3" />
                <span>{consoleFeedback}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Progress bar compacto */}
      {isDownloading && (
        <div className="bg-[#2a2a2b] rounded border border-[rgba(255,255,255,0.08)] p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#DADADA] font-medium">Generando...</span>
            <span className="text-xs text-[#ACACAC] font-bold">{downloadProgress}%</span>
          </div>
          <div className="w-full bg-[#1e1e1f] rounded-full h-1.5 overflow-hidden">
            <div 
              className="bg-[#ACACAC] h-1.5 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${downloadProgress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default DeepResearchReport;