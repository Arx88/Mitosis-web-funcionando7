import React from 'react';
import { Globe, ExternalLink, Clock, Star } from 'lucide-react';

interface SearchResult {
  title?: string;
  url?: string;
  content?: string;
  snippet?: string;
}

interface SearchResultsProps {
  query: string;
  directAnswer?: string;
  sources?: SearchResult[];
  type?: 'websearch' | 'deepsearch';
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  query,
  directAnswer,
  sources = [],
  type = 'websearch'
}) => {
  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch {
      return url;
    }
  };

  const truncateText = (text: string, maxLength: number = 200) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <div className="space-y-4 text-[#DADADA]">
      {/* Direct Answer */}
      {directAnswer && (
        <div className="bg-gradient-to-r from-[#1E1E1F] to-[#252526] rounded-xl p-5 border border-green-500/20">
          <div className="flex items-center gap-2 mb-3">
            <Star className="w-5 h-5 text-green-400" />
            <h4 className="text-base font-semibold text-green-400">Respuesta Directa:</h4>
          </div>
          <div className="text-[#DADADA] leading-relaxed">
            {directAnswer.split('\n').map((paragraph, index) => (
              paragraph.trim() && (
                <p key={index} className="mb-2 last:mb-0">
                  {paragraph}
                </p>
              )
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {sources.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-2">
            <Clock className="w-4 h-4 text-blue-400" />
            <h4 className="text-base font-semibold text-blue-400">
              Fuentes encontradas:
            </h4>
          </div>
          
          <div className="space-y-3">
            {sources.map((source, index) => (
              <div 
                key={index}
                className="group bg-[#1E1E1F] rounded-xl p-4 border border-[rgba(255,255,255,0.08)] hover:border-blue-500/30 transition-all duration-200"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center text-blue-400 font-mono text-sm font-bold">
                    {index + 1}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <h5 className="font-semibold text-[#DADADA] line-clamp-2 group-hover:text-blue-400 transition-colors">
                        {source.title || 'Resultado sin título'}
                      </h5>
                      {source.url && (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-shrink-0 p-1.5 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 transition-colors"
                          title="Abrir enlace"
                        >
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    
                    {source.content && (
                      <p className="text-sm text-[#ACACAC] leading-relaxed mb-2">
                        {truncateText(source.content)}
                      </p>
                    )}
                    
                    {source.url && (
                      <div className="flex items-center gap-2 text-xs">
                        <div className="w-1 h-1 bg-blue-400 rounded-full"></div>
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 transition-colors truncate max-w-[300px]"
                          title={source.url}
                        >
                          🔗 {formatUrl(source.url)}
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary - Solo mostrar si hay fuentes */}
      {sources.length > 0 && (
        <div className="p-4 bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-xl border border-green-500/20">
          <div className="flex items-center gap-2 text-green-400">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium">
              Búsqueda completada • {sources.length} fuente{sources.length !== 1 ? 's' : ''} encontrada{sources.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};