// Configuración centralizada de API y WebSocket
// Elimina la duplicación de URLs en 8+ archivos

interface ApiConfig {
  backend: {
    url: string;
    wsUrl: string;
  };
  endpoints: {
    chat: string;
    generatePlan: string;
    executeStep: string;
    taskStatus: string;
    health: string;
    startTaskExecution: string;
    getTaskPlan: string;
    uploadFiles: string;
    downloadFile: string;
  };
  websocket: {
    url: string;
    options: {
      transports: string[];
      upgrade: boolean;
      reconnection: boolean;
      reconnectionDelay: number;
      reconnectionAttempts: number;
      timeout: number;
    };
  };
}

function getBackendUrl(): string {
  // Simplificar: usar directamente la URL de producción para builds de producción
  // Esta URL se inyecta en tiempo de compilación por Vite
  const productionUrl = 'https://c831651b-a7e8-429e-abcb-944983407842.preview.emergentagent.com';
  
  // En desarrollo, intentar usar variables de entorno
  if (typeof import !== 'undefined' && import.meta?.env?.MODE === 'development') {
    return import.meta.env.VITE_BACKEND_URL || 
           import.meta.env.REACT_APP_BACKEND_URL || 
           'http://localhost:8001';
  }
  
  // En producción, usar URL fija
  console.log('🔧 Using production backend URL:', productionUrl);
  return productionUrl;
}

function getWebSocketUrl(): string {
  const backendUrl = getBackendUrl();
  // Convertir HTTP URL a WebSocket URL
  return backendUrl.replace(/^https?:\/\//, 'ws://').replace(/^ws:\/\//, 'ws://');
}

export const API_CONFIG: ApiConfig = {
  backend: {
    url: getBackendUrl(),
    wsUrl: getWebSocketUrl()
  },
  endpoints: {
    chat: '/api/agent/chat',
    generatePlan: '/api/agent/generate-plan',
    executeStep: '/api/agent/execute-step-detailed',
    taskStatus: '/api/agent/get-task-status',
    health: '/api/agent/health',
    startTaskExecution: '/api/agent/start-task-execution',
    getTaskPlan: '/api/agent/get-task-plan',
    uploadFiles: '/api/agent/upload-files',
    downloadFile: '/api/agent/download'
  },
  websocket: {
    url: `${getBackendUrl()}/socket.io/`,
    options: {
      transports: ['websocket', 'polling'], // WebSocket first, polling fallback
      upgrade: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      timeout: 20000
    }
  }
};

// Helper functions para fácil acceso
export const getApiUrl = (endpoint: keyof typeof API_CONFIG.endpoints): string => {
  return `${API_CONFIG.backend.url}${API_CONFIG.endpoints[endpoint]}`;
};

export const getWebSocketConfig = () => API_CONFIG.websocket;

// Logging de configuración para debugging
console.log('🔧 API Configuration loaded:', {
  backendUrl: API_CONFIG.backend.url,
  wsUrl: API_CONFIG.websocket.url,
  availableEndpoints: Object.keys(API_CONFIG.endpoints).length
});