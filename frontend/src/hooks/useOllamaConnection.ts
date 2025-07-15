import { useState, useEffect } from 'react';

interface OllamaModel {
  name: string;
  label: string;
  size?: string;
  modified?: string;
}

interface UseOllamaConnectionProps {
  endpoint: string;
  enabled: boolean;
}

export const useOllamaConnection = ({ endpoint, enabled }: UseOllamaConnectionProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = async () => {
    if (!enabled || !endpoint) {
      setModels([]);
      setIsConnected(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/agent/ollama/models`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          endpoint: endpoint
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      const formattedModels = data.models.map((model: string) => ({
        name: model,
        label: model.charAt(0).toUpperCase() + model.slice(1).replace(/[.-]/g, ' ')
      }));

      setModels(formattedModels);
      setIsConnected(true);
      
      // Also check connection when fetching models
      await checkConnection();
    } catch (err) {
      console.error('Error fetching Ollama models:', err);
      setError(err instanceof Error ? err.message : 'Error desconocido');
      setIsConnected(false);
      setModels([]);
    } finally {
      setIsLoading(false);
    }
  };

  const checkConnection = async () => {
    if (!enabled || !endpoint) {
      setIsConnected(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/agent/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const ollamaHealthy = data.services?.ollama || false;
      
      setIsConnected(ollamaHealthy);
      
      if (!ollamaHealthy && data.services?.ollama?.error) {
        setError(data.services.ollama.error);
      }
    } catch (err) {
      console.error('Error checking Ollama connection:', err);
      setError(err instanceof Error ? err.message : 'Error de conexión');
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (enabled && endpoint) {
      checkConnection();
      fetchModels();
    } else {
      setIsConnected(false);
      setModels([]);
      setError(null);
    }
  }, [enabled, endpoint]);

  return {
    isConnected,
    isLoading,
    models,
    error,
    fetchModels,
    checkConnection
  };
};