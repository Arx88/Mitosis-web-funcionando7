import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Brain, Database, Search, Lightbulb, Clock, Activity } from 'lucide-react';

interface MemoryStats {
  overview: {
    working_memory: {
      capacity_used: string;
      total_contexts: number;
      ttl_minutes: number;
    };
    episodic_memory: {
      total_episodes: number;
      success_rate: number;
      average_importance: number;
    };
    semantic_memory: {
      total_concepts: number;
      total_facts: number;
      average_fact_confidence: number;
    };
    procedural_memory: {
      total_procedures: number;
      total_strategies: number;
      average_procedure_effectiveness: number;
    };
    embedding_service: {
      total_documents: number;
      model_name: string;
      is_initialized: boolean;
    };
  };
  memory_efficiency: {
    total_capacity_used: number;
    embedding_efficiency: number;
    search_performance: number;
  };
  learning_insights: {
    episode_success_rate: number;
    knowledge_confidence: number;
    procedure_effectiveness: number;
  };
}

export const MemoryAnalyticsPanel: React.FC = () => {
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMemoryStats = async () => {
      try {
        const response = await fetch('/api/memory/memory-analytics');
        if (!response.ok) {
          throw new Error('Failed to fetch memory analytics');
        }
        const data = await response.json();
        setMemoryStats(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchMemoryStats();
    
    // Actualizar cada 30 segundos
    const interval = setInterval(fetchMemoryStats, 30000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Cargando análisis de memoria...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-600 bg-red-50 rounded-lg">
        Error: {error}
      </div>
    );
  }

  if (!memoryStats) {
    return (
      <div className="p-4 text-gray-600 bg-gray-50 rounded-lg">
        No se pudieron cargar las estadísticas de memoria
      </div>
    );
  }

  const workingMemoryUsage = memoryStats.overview.working_memory.capacity_used;
  const [used, total] = workingMemoryUsage.split('/').map(Number);
  const workingMemoryPercentage = total > 0 ? (used / total) * 100 : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {/* Memoria de Trabajo */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Memoria de Trabajo</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{used}/{total}</div>
          <Progress value={workingMemoryPercentage} className="mt-2" />
          <p className="text-xs text-muted-foreground mt-2">
            {memoryStats.overview.working_memory.total_contexts} contextos activos
          </p>
          <p className="text-xs text-muted-foreground">
            TTL: {memoryStats.overview.working_memory.ttl_minutes} minutos
          </p>
        </CardContent>
      </Card>

      {/* Memoria Episódica */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Memoria Episódica</CardTitle>
          <Database className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {memoryStats.overview.episodic_memory.total_episodes}
          </div>
          <p className="text-xs text-muted-foreground">episodios almacenados</p>
          <div className="flex items-center mt-2">
            <Badge variant={memoryStats.overview.episodic_memory.success_rate > 0.7 ? "default" : "secondary"}>
              {Math.round(memoryStats.overview.episodic_memory.success_rate * 100)}% éxito
            </Badge>
          </div>
          <Progress 
            value={memoryStats.overview.episodic_memory.average_importance * 100} 
            className="mt-2" 
          />
          <p className="text-xs text-muted-foreground mt-1">
            Importancia promedio: {Math.round(memoryStats.overview.episodic_memory.average_importance * 100)}%
          </p>
        </CardContent>
      </Card>

      {/* Memoria Semántica */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Memoria Semántica</CardTitle>
          <Brain className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {memoryStats.overview.semantic_memory.total_concepts}
          </div>
          <p className="text-xs text-muted-foreground">conceptos</p>
          <div className="text-lg font-semibold mt-1">
            {memoryStats.overview.semantic_memory.total_facts}
          </div>
          <p className="text-xs text-muted-foreground">hechos</p>
          <Progress 
            value={memoryStats.overview.semantic_memory.average_fact_confidence * 100} 
            className="mt-2" 
          />
          <p className="text-xs text-muted-foreground mt-1">
            Confianza: {Math.round(memoryStats.overview.semantic_memory.average_fact_confidence * 100)}%
          </p>
        </CardContent>
      </Card>

      {/* Memoria Procedimental */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Memoria Procedimental</CardTitle>
          <Lightbulb className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {memoryStats.overview.procedural_memory.total_procedures}
          </div>
          <p className="text-xs text-muted-foreground">procedimientos</p>
          <div className="text-lg font-semibold mt-1">
            {memoryStats.overview.procedural_memory.total_strategies}
          </div>
          <p className="text-xs text-muted-foreground">estrategias</p>
          <Progress 
            value={memoryStats.overview.procedural_memory.average_procedure_effectiveness * 100} 
            className="mt-2" 
          />
          <p className="text-xs text-muted-foreground mt-1">
            Efectividad: {Math.round(memoryStats.overview.procedural_memory.average_procedure_effectiveness * 100)}%
          </p>
        </CardContent>
      </Card>

      {/* Servicio de Embeddings */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Embeddings</CardTitle>
          <Search className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {memoryStats.overview.embedding_service.total_documents}
          </div>
          <p className="text-xs text-muted-foreground">documentos indexados</p>
          <div className="flex items-center mt-2">
            <Badge variant={memoryStats.overview.embedding_service.is_initialized ? "default" : "destructive"}>
              {memoryStats.overview.embedding_service.is_initialized ? "Activo" : "Inactivo"}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Modelo: {memoryStats.overview.embedding_service.model_name}
          </p>
        </CardContent>
      </Card>

      {/* Eficiencia General */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Eficiencia General</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {memoryStats.memory_efficiency.total_capacity_used}
          </div>
          <p className="text-xs text-muted-foreground">elementos almacenados</p>
          
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span>Episodios exitosos</span>
              <span>{Math.round(memoryStats.learning_insights.episode_success_rate * 100)}%</span>
            </div>
            <Progress value={memoryStats.learning_insights.episode_success_rate * 100} />
            
            <div className="flex justify-between text-sm">
              <span>Confianza en conocimiento</span>
              <span>{Math.round(memoryStats.learning_insights.knowledge_confidence * 100)}%</span>
            </div>
            <Progress value={memoryStats.learning_insights.knowledge_confidence * 100} />
            
            <div className="flex justify-between text-sm">
              <span>Efectividad de procedimientos</span>
              <span>{Math.round(memoryStats.learning_insights.procedure_effectiveness * 100)}%</span>
            </div>
            <Progress value={memoryStats.learning_insights.procedure_effectiveness * 100} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MemoryAnalyticsPanel;