import React, { useState, useEffect } from 'react';
import { 
  AlertCircle, Search, TrendingUp, Clock, Target, 
  CheckCircle, XCircle, ArrowRight, Code, Database,
  Network, Server, Cpu, HardDrive, Zap, Bug,
  ChevronDown, ChevronRight, Copy, Download,
  RefreshCw, Filter, Calendar
} from 'lucide-react';

interface ErrorAnalysis {
  error_id: string;
  error_message: string;
  error_type: string;
  stack_trace: string;
  timestamp: number;
  context: Record<string, any>;
  root_cause?: string;
  suggested_fixes: string[];
  similar_errors: string[];
  confidence_score: number;
}

interface ErrorPattern {
  pattern_name: string;
  frequency: number;
  last_occurrence: number;
  affected_components: string[];
  resolution_rate: number;
}

interface ErrorAnalysisPanelProps {
  websocket?: WebSocket;
  onErrorSelect?: (error: ErrorAnalysis) => void;
}

const ERROR_TYPE_ICONS: Record<string, React.ComponentType<any>> = {
  'ConnectionError': Network,
  'TimeoutError': Clock,
  'MemoryError': Cpu,
  'DiskError': HardDrive,
  'DatabaseError': Database,
  'APIError': Server,
  'ValidationError': CheckCircle,
  'SystemError': Zap,
  'default': Bug
};

const SEVERITY_COLORS = {
  high: 'bg-red-100 border-red-500 text-red-800',
  medium: 'bg-yellow-100 border-yellow-500 text-yellow-800',
  low: 'bg-blue-100 border-blue-500 text-blue-800'
};

export const ErrorAnalysisPanel: React.FC<ErrorAnalysisPanelProps> = ({
  websocket,
  onErrorSelect
}) => {
  const [errorAnalyses, setErrorAnalyses] = useState<ErrorAnalysis[]>([]);
  const [errorPatterns, setErrorPatterns] = useState<ErrorPattern[]>([]);
  const [selectedError, setSelectedError] = useState<ErrorAnalysis | null>(null);
  const [expandedErrors, setExpandedErrors] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [showPatterns, setShowPatterns] = useState<boolean>(false);

  useEffect(() => {
    loadErrorAnalyses();
    loadErrorPatterns();

    if (websocket) {
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_error_analysis') {
          handleNewErrorAnalysis(data.payload);
        } else if (data.type === 'error_pattern_update') {
          updateErrorPatterns(data.payload);
        }
      };
    }
  }, [websocket, timeRange, filterType]);

  const loadErrorAnalyses = async () => {
    try {
      const params = new URLSearchParams({
        time_range: timeRange,
        error_type: filterType !== 'all' ? filterType : '',
        search: searchQuery
      });
      
      const response = await fetch(`/api/error-analyses?${params}`);
      const data = await response.json();
      setErrorAnalyses(data);
    } catch (error) {
      console.error('Error loading error analyses:', error);
    }
  };

  const loadErrorPatterns = async () => {
    try {
      const response = await fetch('/api/error-patterns');
      const data = await response.json();
      setErrorPatterns(data);
    } catch (error) {
      console.error('Error loading error patterns:', error);
    }
  };

  const handleNewErrorAnalysis = (analysis: ErrorAnalysis) => {
    setErrorAnalyses(prev => [analysis, ...prev]);
  };

  const updateErrorPatterns = (patterns: ErrorPattern[]) => {
    setErrorPatterns(patterns);
  };

  const triggerErrorAnalysis = async (errorId: string) => {
    setIsAnalyzing(true);
    try {
      const response = await fetch(`/api/error-analyses/${errorId}/reanalyze`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const updatedAnalysis = await response.json();
        setErrorAnalyses(prev => prev.map(analysis => 
          analysis.error_id === errorId ? updatedAnalysis : analysis
        ));
      }
    } catch (error) {
      console.error('Error triggering analysis:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const toggleErrorExpansion = (errorId: string) => {
    setExpandedErrors(prev => {
      const newSet = new Set(prev);
      if (newSet.has(errorId)) {
        newSet.delete(errorId);
      } else {
        newSet.add(errorId);
      }
      return newSet;
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportErrorData = (analysis: ErrorAnalysis) => {
    const data = {
      error_id: analysis.error_id,
      error_message: analysis.error_message,
      error_type: analysis.error_type,
      timestamp: new Date(analysis.timestamp * 1000).toISOString(),
      root_cause: analysis.root_cause,
      suggested_fixes: analysis.suggested_fixes,
      confidence_score: analysis.confidence_score,
      stack_trace: analysis.stack_trace,
      context: analysis.context
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `error_analysis_${analysis.error_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getSeverityFromConfidence = (confidence: number): 'high' | 'medium' | 'low' => {
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  };

  const getErrorTypeIcon = (errorType: string) => {
    const IconComponent = ERROR_TYPE_ICONS[errorType] || ERROR_TYPE_ICONS.default;
    return <IconComponent className="w-5 h-5" />;
  };

  const filteredErrors = errorAnalyses.filter(analysis => {
    const matchesType = filterType === 'all' || analysis.error_type === filterType;
    const matchesSearch = searchQuery === '' || 
      analysis.error_message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      analysis.error_type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const errorTypes = Array.from(new Set(errorAnalyses.map(e => e.error_type)));

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="p-6 border-b">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Análisis de Errores</h2>
            <p className="text-gray-600">Diagnóstico automático de causa raíz</p>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => setShowPatterns(!showPatterns)}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg flex items-center space-x-2"
            >
              <TrendingUp className="w-4 h-4" />
              <span>Patrones</span>
            </button>
            
            <button
              onClick={loadErrorAnalyses}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Actualizar</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex space-x-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Buscar errores..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg"
              />
            </div>
          </div>
          
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 border rounded-lg"
          >
            <option value="all">Todos los tipos</option>
            {errorTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border rounded-lg"
          >
            <option value="1h">Última hora</option>
            <option value="24h">Últimas 24 horas</option>
            <option value="7d">Últimos 7 días</option>
            <option value="30d">Últimos 30 días</option>
          </select>
        </div>
      </div>

      {/* Error Patterns Panel */}
      {showPatterns && (
        <div className="p-6 bg-purple-50 border-b">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Patrones de Errores Detectados</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {errorPatterns.map((pattern, index) => (
              <div key={index} className="bg-white p-4 rounded-lg border">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{pattern.pattern_name}</h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    pattern.resolution_rate > 0.8 ? 'bg-green-100 text-green-800' :
                    pattern.resolution_rate > 0.5 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {(pattern.resolution_rate * 100).toFixed(0)}% resuelto
                  </span>
                </div>
                
                <div className="space-y-1 text-sm text-gray-600">
                  <p>Frecuencia: {pattern.frequency} ocurrencias</p>
                  <p>Última vez: {new Date(pattern.last_occurrence * 1000).toLocaleDateString()}</p>
                  <p>Componentes: {pattern.affected_components.join(', ')}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error List */}
      <div className="divide-y">
        {filteredErrors.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Bug className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No se encontraron errores para los filtros seleccionados</p>
          </div>
        ) : (
          filteredErrors.map((analysis) => {
            const isExpanded = expandedErrors.has(analysis.error_id);
            const severity = getSeverityFromConfidence(analysis.confidence_score);
            
            return (
              <div key={analysis.error_id} className="p-6">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    {getErrorTypeIcon(analysis.error_type)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h3 className="text-lg font-medium text-gray-900">
                            {analysis.error_type}
                          </h3>
                          
                          <span className={`px-2 py-1 text-xs rounded-full border-l-4 ${SEVERITY_COLORS[severity]}`}>
                            Confianza: {(analysis.confidence_score * 100).toFixed(0)}%
                          </span>
                          
                          <span className="text-sm text-gray-500">
                            {new Date(analysis.timestamp * 1000).toLocaleString()}
                          </span>
                        </div>
                        
                        <p className="text-gray-700 mb-3">{analysis.error_message}</p>
                        
                        {analysis.root_cause && (
                          <div className="bg-blue-50 border-l-4 border-blue-500 p-3 mb-3">
                            <div className="flex items-center space-x-2 mb-1">
                              <Target className="w-4 h-4 text-blue-600" />
                              <span className="font-medium text-blue-900">Causa Raíz Identificada</span>
                            </div>
                            <p className="text-blue-800">{analysis.root_cause}</p>
                          </div>
                        )}
                        
                        {analysis.suggested_fixes.length > 0 && (
                          <div className="bg-green-50 border-l-4 border-green-500 p-3 mb-3">
                            <div className="flex items-center space-x-2 mb-2">
                              <CheckCircle className="w-4 h-4 text-green-600" />
                              <span className="font-medium text-green-900">Soluciones Sugeridas</span>
                            </div>
                            <ul className="space-y-1">
                              {analysis.suggested_fixes.map((fix, index) => (
                                <li key={index} className="flex items-start space-x-2 text-green-800">
                                  <ArrowRight className="w-3 h-3 mt-1 flex-shrink-0" />
                                  <span className="text-sm">{fix}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {analysis.similar_errors.length > 0 && (
                          <div className="bg-yellow-50 border-l-4 border-yellow-500 p-3 mb-3">
                            <div className="flex items-center space-x-2 mb-1">
                              <TrendingUp className="w-4 h-4 text-yellow-600" />
                              <span className="font-medium text-yellow-900">
                                Errores Similares ({analysis.similar_errors.length})
                              </span>
                            </div>
                            <p className="text-yellow-800 text-sm">
                              Se encontraron errores similares en el historial
                            </p>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex space-x-2 ml-4">
                        <button
                          onClick={() => triggerErrorAnalysis(analysis.error_id)}
                          disabled={isAnalyzing}
                          className="p-2 text-gray-400 hover:text-blue-600 disabled:opacity-50"
                          title="Re-analizar"
                        >
                          <RefreshCw className={`w-4 h-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
                        </button>
                        
                        <button
                          onClick={() => copyToClipboard(analysis.error_message)}
                          className="p-2 text-gray-400 hover:text-blue-600"
                          title="Copiar mensaje"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                        
                        <button
                          onClick={() => exportErrorData(analysis)}
                          className="p-2 text-gray-400 hover:text-blue-600"
                          title="Exportar datos"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        
                        <button
                          onClick={() => toggleErrorExpansion(analysis.error_id)}
                          className="p-2 text-gray-400 hover:text-blue-600"
                          title={isExpanded ? "Contraer" : "Expandir"}
                        >
                          {isExpanded ? 
                            <ChevronDown className="w-4 h-4" /> : 
                            <ChevronRight className="w-4 h-4" />
                          }
                        </button>
                      </div>
                    </div>
                    
                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="mt-4 space-y-4">
                        {/* Context */}
                        {Object.keys(analysis.context).length > 0 && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Contexto</h4>
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                                {JSON.stringify(analysis.context, null, 2)}
                              </pre>
                            </div>
                          </div>
                        )}
                        
                        {/* Stack Trace */}
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Stack Trace</h4>
                          <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto">
                            <pre className="text-sm font-mono whitespace-pre-wrap">
                              {analysis.stack_trace}
                            </pre>
                          </div>
                        </div>
                        
                        {/* Actions */}
                        <div className="flex space-x-3 pt-3 border-t">
                          <button
                            onClick={() => {
                              setSelectedError(analysis);
                              if (onErrorSelect) onErrorSelect(analysis);
                            }}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm"
                          >
                            Investigar Más
                          </button>
                          
                          <button
                            onClick={() => {
                              // Mark as resolved or create task
                            }}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm"
                          >
                            Marcar como Resuelto
                          </button>
                          
                          <button
                            onClick={() => {
                              // Create task from error
                            }}
                            className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm"
                          >
                            Crear Tarea
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default ErrorAnalysisPanel;

