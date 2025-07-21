import { useState, useEffect } from 'react';

interface OllamaModel {
  name: string;
  label: string;
  size?: string;
  modified?: string;
  parameter_size?: string;
  quantization?: string;
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
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';
      console.log(`🔍 Obteniendo modelos de: ${endpoint}`);
      
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

      // Handle both old format (array of strings) and new format (array of objects)
      const formattedModels = data.models.map((model: any) => {
        let modelName: string;
        let modelSize: string | undefined;
        
        if (typeof model === 'string') {
          // Old format - just model name as string
          modelName = model;
          modelSize = undefined;
        } else if (model && typeof model === 'object') {
          // New format - object with name and size
          modelName = model.name || '';
          modelSize = model.size;
        } else {
          // Fallback for unexpected format
          modelName = String(model || '');
          modelSize = undefined;
        }
        
        // Ensure modelName is always a string
        if (!modelName || typeof modelName !== 'string') {
          modelName = 'Unknown Model';
        }
        
        return {
          name: modelName,
          label: modelSize 
            ? `${modelName} (${modelSize})` 
            : modelName.charAt(0).toUpperCase() + modelName.slice(1).replace(/[.-]/g, ' '),
          size: modelSize
        };
      });

      setModels(formattedModels);
      setIsConnected(true);
      
      console.log(`✅ ${formattedModels.length} modelos obtenidos de ${endpoint}`);
      
      // Show fallback warning if applicable
      if (data.fallback) {
        console.warn(`⚠️ Usando modelos fallback: ${data.warning}`);
        setError(`Conexión limitada: ${data.warning}`);
      }
      
    } catch (err) {
      console.error('❌ Error fetching Ollama models:', err);
      setError(err instanceof Error ? err.message : 'Error desconocido obteniendo modelos');
      setIsConnected(false);
      setModels([]);
    } finally {
      setIsLoading(false);
    }
  };

  const checkConnection = async () => {
    console.log('🔍 checkConnection called', { enabled, endpoint });
    if (!enabled || !endpoint) {
      setIsConnected(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
      console.log('🌐 Making request to backend:', `${backendUrl}/api/agent/ollama/check`);
      const response = await fetch(`${backendUrl}/api/agent/ollama/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          endpoint: endpoint
        })
      });
      
      console.log('📡 Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('📊 Response data:', data);
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      setIsConnected(data.is_connected);
      console.log('✅ Connection status updated:', data.is_connected);
      
      if (!data.is_connected) {
        setError('No se pudo conectar con el endpoint de Ollama');
      }
    } catch (err) {
      console.error('❌ Error checking Ollama connection:', err);
      setError(err instanceof Error ? err.message : 'Error de conexión');
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    console.log('🔄 useOllamaConnection useEffect triggered', { enabled, endpoint });
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