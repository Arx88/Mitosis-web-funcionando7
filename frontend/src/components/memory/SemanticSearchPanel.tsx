import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Search, Brain, Clock, Star, Filter } from 'lucide-react';

interface SearchResult {
  id: string;
  content: string;
  similarity: number;
  type: 'episode' | 'concept' | 'fact' | 'procedure';
  metadata: {
    timestamp?: string;
    category?: string;
    importance?: number;
    confidence?: number;
  };
}

interface SemanticSearchResult {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_timestamp: string;
}

export const SemanticSearchPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SemanticSearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['all']);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/memory/semantic-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          max_results: 10,
          memory_types: selectedTypes
        }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [query, selectedTypes]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'episode':
        return 'bg-blue-100 text-blue-800';
      case 'concept':
        return 'bg-green-100 text-green-800';
      case 'fact':
        return 'bg-yellow-100 text-yellow-800';
      case 'procedure':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'episode':
        return '📚';
      case 'concept':
        return '💡';
      case 'fact':
        return '📝';
      case 'procedure':
        return '⚙️';
      default:
        return '🔍';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getSimilarityColor = (similarity: number) => {
    if (similarity > 0.8) return 'text-green-600';
    if (similarity > 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Búsqueda Semántica en Memoria
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Barra de búsqueda */}
            <div className="flex gap-2">
              <Input
                placeholder="Buscar en la memoria del agente..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="flex-1"
              />
              <Button 
                onClick={handleSearch}
                disabled={loading || !query.trim()}
                className="px-6"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Search className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* Filtros de tipo */}
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-gray-600 flex items-center gap-1">
                <Filter className="h-3 w-3" />
                Filtros:
              </span>
              {['all', 'episode', 'concept', 'fact', 'procedure'].map(type => (
                <Badge
                  key={type}
                  variant={selectedTypes.includes(type) ? "default" : "secondary"}
                  className="cursor-pointer"
                  onClick={() => {
                    if (type === 'all') {
                      setSelectedTypes(['all']);
                    } else {
                      setSelectedTypes(prev => 
                        prev.includes(type) 
                          ? prev.filter(t => t !== type)
                          : [...prev.filter(t => t !== 'all'), type]
                      );
                    }
                  }}
                >
                  {type === 'all' ? 'Todo' : type}
                </Badge>
              ))}
            </div>

            {/* Error */}
            {error && (
              <div className="p-3 text-red-600 bg-red-50 rounded-lg">
                Error: {error}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Resultados */}
      {results && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Resultados de búsqueda
            </CardTitle>
            <p className="text-sm text-gray-600">
              {results.total_results} resultados para "{results.query}"
            </p>
          </CardHeader>
          <CardContent>
            {results.results.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No se encontraron resultados relevantes</p>
                <p className="text-sm">Intenta con términos diferentes</p>
              </div>
            ) : (
              <div className="space-y-4">
                {results.results.map((result) => (
                  <div 
                    key={result.id}
                    className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{getTypeIcon(result.type)}</span>
                        <Badge className={getTypeColor(result.type)}>
                          {result.type}
                        </Badge>
                        <span className={`text-sm font-medium ${getSimilarityColor(result.similarity)}`}>
                          {Math.round(result.similarity * 100)}% similitud
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {result.metadata.importance && (
                          <div className="flex items-center gap-1 text-sm text-gray-600">
                            <Star className="h-3 w-3" />
                            {Math.round(result.metadata.importance * 100)}%
                          </div>
                        )}
                        {result.metadata.timestamp && (
                          <div className="flex items-center gap-1 text-sm text-gray-600">
                            <Clock className="h-3 w-3" />
                            {formatTimestamp(result.metadata.timestamp)}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-sm text-gray-800 mb-2">
                      {result.content}
                    </div>

                    {result.metadata.category && (
                      <div className="flex items-center gap-2 text-xs text-gray-600">
                        <span>Categoría: {result.metadata.category}</span>
                        {result.metadata.confidence && (
                          <span>• Confianza: {Math.round(result.metadata.confidence * 100)}%</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SemanticSearchPanel;