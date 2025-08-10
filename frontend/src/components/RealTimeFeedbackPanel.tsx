import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface CollectedDataItem {
  id: string;
  source: string;
  data_type: string;
  title: string;
  content: string;
  url?: string;
  metadata?: any;
  timestamp: number;
}

interface ProgressSummary {
  total_data_collected: number;
  active_steps: number;
  completed_steps: number;
  data_sources: string[];
  collection_efficiency: number;
}

interface FeedbackData {
  success: boolean;
  task_id: string;
  collected_data: CollectedDataItem[];
  progress_summary: ProgressSummary;
  collection_document: string;
  data_count: number;
  has_data: boolean;
  timestamp: string;
}

interface RealTimeFeedbackPanelProps {
  taskId: string;
  isVisible: boolean;
  showDocument?: boolean;
}

const RealTimeFeedbackPanel: React.FC<RealTimeFeedbackPanelProps> = ({ 
  taskId, 
  isVisible,
  showDocument = false 
}) => {
  const [feedbackData, setFeedbackData] = useState<FeedbackData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'live' | 'document'>('live');
  const feedbackRef = useRef<HTMLDivElement>(null);

  // Función para obtener feedback del servidor usando la ruta correcta
  const fetchFeedback = async () => {
    if (!taskId) return;
    
    try {
      setIsLoading(true);
      const response = await fetch(`/api/agent/get-task-feedback/${taskId}`);
      if (response.ok) {
        const data: FeedbackData = await response.json();
        setFeedbackData(data);
      }
    } catch (error) {
      console.error('Error fetching feedback:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isVisible && taskId) {
      fetchFeedback();
      
      // Actualizar cada 5 segundos para mostrar información en tiempo real
      const interval = setInterval(fetchFeedback, 5000);
      return () => clearInterval(interval);
    }
  }, [taskId, isVisible]);

  // Auto-scroll al final cuando hay nueva información
  useEffect(() => {
    if (feedbackRef.current) {
      feedbackRef.current.scrollTop = feedbackRef.current.scrollHeight;
    }
  }, [feedbackData?.collected_data]);

  if (!isVisible) return null;

  const getDataTypeIcon = (dataType: string) => {
    switch (dataType) {
      case 'search_result': return '🔍';
      case 'scraped_content': return '📄';
      case 'website_visit': return '🌐';
      case 'screenshot': return '📸';
      case 'insight': return '💡';
      default: return '📊';
    }
  };

  const getDataTypeColor = (dataType: string) => {
    switch (dataType) {
      case 'search_result': return 'text-blue-600';
      case 'scraped_content': return 'text-green-600';
      case 'website_visit': return 'text-purple-600';
      case 'screenshot': return 'text-orange-600';
      case 'insight': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  return (
    <Card className="h-full max-h-[600px] flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-blue-500">🔄</span>
            Información Recolectada en Tiempo Real
            {isLoading && (
              <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            )}
          </div>
          
          {showDocument && feedbackData?.has_data && (
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('live')}
                className={`text-xs px-3 py-1 rounded-md transition-all ${
                  activeTab === 'live' 
                    ? 'bg-white shadow-sm text-gray-900' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                📊 En Vivo
              </button>
              <button
                onClick={() => setActiveTab('document')}
                className={`text-xs px-3 py-1 rounded-md transition-all ${
                  activeTab === 'document' 
                    ? 'bg-white shadow-sm text-gray-900' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                📄 Documento
              </button>
            </div>
          )}
        </CardTitle>
        
        {feedbackData?.progress_summary && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-1">
              <span className="text-blue-500">📊</span>
              <span>{feedbackData.progress_summary.total_data_collected} datos</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-green-500">✅</span>
              <span>{feedbackData.progress_summary.completed_steps} completados</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-orange-500">🔄</span>
              <span>{feedbackData.progress_summary.active_steps} activos</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-purple-500">🎯</span>
              <span>{(feedbackData.progress_summary.collection_efficiency * 100).toFixed(0)}% eficiencia</span>
            </div>
          </div>
        )}

        {feedbackData?.progress_summary?.data_sources && feedbackData.progress_summary.data_sources.length > 0 && (
          <div className="text-xs text-gray-600 border-t pt-2">
            <div className="flex justify-between">
              <span>Fuentes:</span>
              <span className="font-medium">
                {feedbackData.progress_summary.data_sources.length} sitios únicos
              </span>
            </div>
            <div className="flex flex-wrap gap-1 mt-1">
              {feedbackData.progress_summary.data_sources.slice(0, 3).map((source, index) => (
                <span key={index} className="bg-gray-100 px-2 py-1 rounded text-xs">
                  {source.length > 20 ? source.substring(0, 20) + '...' : source}
                </span>
              ))}
              {feedbackData.progress_summary.data_sources.length > 3 && (
                <span className="text-gray-500 text-xs">
                  +{feedbackData.progress_summary.data_sources.length - 3} más
                </span>
              )}
            </div>
          </div>
        )}
      </CardHeader>
      
      <CardContent className="flex-1 overflow-hidden p-3">
        {activeTab === 'live' ? (
          <div 
            ref={feedbackRef}
            className="h-full overflow-y-auto space-y-3 pr-2"
            style={{ maxHeight: '400px' }}
          >
            {!feedbackData?.has_data ? (
              <div className="text-center text-gray-500 text-sm py-8">
                <div className="animate-pulse">
                  📡 Esperando información del agente...
                </div>
                <div className="text-xs text-gray-400 mt-2">
                  Los datos aparecerán aquí cuando el agente comience a recolectar información
                </div>
              </div>
            ) : (
              feedbackData.collected_data.map((item, index) => (
                <div 
                  key={item.id || index}
                  className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-lg flex-shrink-0">
                      {getDataTypeIcon(item.data_type)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start mb-1">
                        <div className={`text-sm font-medium ${getDataTypeColor(item.data_type)}`}>
                          {item.title}
                        </div>
                        <div className="text-xs text-gray-500">
                          {formatTimestamp(item.timestamp)}
                        </div>
                      </div>
                      
                      <div className="text-xs text-gray-600 mb-2">
                        <span className="font-medium">Fuente:</span> {item.source}
                      </div>
                      
                      <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                        {item.content.length > 200 
                          ? item.content.substring(0, 200) + '...' 
                          : item.content
                        }
                      </div>
                      
                      {item.url && (
                        <div className="text-xs text-blue-600 mt-2 truncate">
                          <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                            🔗 {item.url}
                          </a>
                        </div>
                      )}
                      
                      {item.metadata && (
                        <div className="text-xs text-gray-500 mt-1">
                          <span className="font-medium">Meta:</span> 
                          <span className="ml-1">
                            {Object.entries(item.metadata).map(([key, value]) => (
                              <span key={key} className="inline-block mr-2">
                                {key}: {String(value)}
                              </span>
                            ))}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          <div className="h-full overflow-y-auto space-y-2">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                📄 Documento de Recolección
                <span className="text-xs text-gray-500">
                  ({feedbackData?.data_count || 0} elementos)
                </span>
              </h3>
              <div className="text-sm text-gray-700 whitespace-pre-wrap font-mono text-xs">
                {feedbackData?.collection_document || 'No hay documento disponible aún...'}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RealTimeFeedbackPanel;