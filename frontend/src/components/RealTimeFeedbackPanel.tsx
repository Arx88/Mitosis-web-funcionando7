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
      setIsLoading(true);
      fetchFeedback().finally(() => setIsLoading(false));
      
      // Actualizar cada 3 segundos
      const interval = setInterval(fetchFeedback, 3000);
      return () => clearInterval(interval);
    }
  }, [taskId, isVisible]);

  // Auto-scroll al final cuando hay nuevo feedback
  useEffect(() => {
    if (feedbackRef.current) {
      feedbackRef.current.scrollTop = feedbackRef.current.scrollHeight;
    }
  }, [feedbackHistory]);

  if (!isVisible) return null;

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'website_visit': return '🌐';
      case 'information_extraction': return '📊';
      case 'step_progress': return '⚡';
      case 'screenshot_with_context': return '📸';
      default: return '📄';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'website_visit': return 'text-blue-600';
      case 'information_extraction': return 'text-green-600';
      case 'step_progress': return 'text-purple-600';
      case 'screenshot_with_context': return 'text-orange-600';
      default: return 'text-gray-600';
    }
  };

  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  return (
    <Card className="h-full max-h-96 flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <span className="text-blue-500">🔄</span>
          Información Recolectada en Tiempo Real
          {isLoading && (
            <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          )}
        </CardTitle>
        
        {currentSummary?.statistics && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-1">
              <span className="text-blue-500">🌐</span>
              <span>{currentSummary.statistics.sources_visited} sitios</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-green-500">📊</span>
              <span>{currentSummary.statistics.information_extracted} extracciones</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-orange-500">📸</span>
              <span>{currentSummary.statistics.screenshots_captured} capturas</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-purple-500">⚡</span>
              <span>{currentSummary.statistics.steps_completed} pasos</span>
            </div>
          </div>
        )}

        {currentSummary?.data_quality && (
          <div className="text-xs text-gray-600 border-t pt-2">
            <div className="flex justify-between">
              <span>Contenido total:</span>
              <span className="font-medium">
                {Math.round(currentSummary.data_quality.total_content_characters / 1000)}k caracteres
              </span>
            </div>
            <div className="flex justify-between">
              <span>Eficiencia:</span>
              <span className="font-medium">
                {(currentSummary.data_quality.extraction_efficiency * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}
      </CardHeader>
      
      <CardContent className="flex-1 overflow-hidden p-3">
        <div 
          ref={feedbackRef}
          className="h-full overflow-y-auto space-y-2 pr-2"
          style={{ maxHeight: '250px' }}
        >
          {feedbackHistory.length === 0 ? (
            <div className="text-center text-gray-500 text-sm py-8">
              <div className="animate-pulse">
                📡 Esperando información del agente...
              </div>
            </div>
          ) : (
            feedbackHistory.map((feedback, index) => (
              <div 
                key={index}
                className="border-l-2 border-gray-200 pl-3 py-1 hover:bg-gray-50 rounded-r transition-colors"
              >
                <div className="flex items-start gap-2">
                  <span className="text-lg flex-shrink-0">
                    {getTypeIcon(feedback.type)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium ${getTypeColor(feedback.type)}`}>
                      {feedback.message}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {formatTime(feedback.timestamp)}
                    </div>
                    
                    {/* Información adicional específica por tipo */}
                    {feedback.data && feedback.type === 'website_visit' && feedback.data.content_preview && (
                      <div className="text-xs text-gray-600 mt-1 bg-gray-100 p-2 rounded">
                        <div className="font-medium">Vista previa:</div>
                        <div className="truncate">{feedback.data.content_preview}</div>
                      </div>
                    )}
                    
                    {feedback.data && feedback.type === 'information_extraction' && (
                      <div className="text-xs text-gray-600 mt-1">
                        <span className="font-medium">Relevancia:</span> 
                        <span className="ml-1 text-green-600">
                          {(feedback.data.relevance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                    
                    {feedback.data && feedback.type === 'step_progress' && (
                      <div className="text-xs text-gray-600 mt-1">
                        <div className="w-full bg-gray-200 rounded-full h-1">
                          <div 
                            className="bg-purple-500 h-1 rounded-full transition-all"
                            style={{ width: `${feedback.data.completion_percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default RealTimeFeedbackPanel;