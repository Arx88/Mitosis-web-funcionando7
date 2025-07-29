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
  // Usar variables de entorno SIEMPRE, tanto en desarrollo como producción
  try {
    // Intentar obtener la URL del backend desde variables de entorno
    const envUrl = import.meta.env?.VITE_BACKEND_URL || 
                   import.meta.env?.REACT_APP_BACKEND_URL ||
                   (typeof process !== 'undefined' ? process.env.REACT_APP_BACKEND_URL : null);
                   
    if (envUrl) {
      console.log('🔧 Using environment backend URL:', envUrl);
      return envUrl;
    }
    
    // Si estamos en desarrollo, usar la URL de environment
    if (import.meta.env?.MODE === 'development') {
      const devUrl = import.meta.env?.VITE_BACKEND_URL || 'http://localhost:8001';
      console.log('🔧 Using development backend URL:', devUrl);
      return devUrl;
    }
    
  } catch (e) {
    console.warn('🔧 Error getting backend URL from environment:', e);
  }
  
  // Último fallback - usar localhost para desarrollo local
  console.warn('🔧 Using localhost fallback for development');
  return 'http://localhost:8001';
}

function getWebSocketUrl(): string {
  const backendUrl = getBackendUrl();
  // FIXED: Usar /socket.io/ directamente sin /api prefix
  return `${backendUrl}/socket.io/`;
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
    url: `${getBackendUrl()}/api/socket.io/`,  // BACK TO /api prefix to match ingress
    options: {
      transports: ['polling', 'websocket'], // POLLING first for k8s compatibility
      upgrade: true,        // Allow upgrade to websocket
      reconnection: true,
      reconnectionDelay: 1000,  // Faster reconnection
      reconnectionAttempts: 10, // More attempts for stability
      timeout: 30000,           // Increased timeout
      forceNew: true            // Force new connection each time
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