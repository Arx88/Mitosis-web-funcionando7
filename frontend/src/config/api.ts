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
    
    // Si estamos en desarrollo, usar localhost
    if (import.meta.env?.MODE === 'development') {
      console.log('🔧 Using development backend URL: https://022fe56d-38bc-4752-a5da-625969514d2c.preview.emergentagent.com');
      return 'https://022fe56d-38bc-4752-a5da-625969514d2c.preview.emergentagent.com';
    }
    
    // Fallback para producción si no hay variables de entorno
    // Usar la URL actual del window con puerto 8001 (mapeado por el ingress)
    if (typeof window !== 'undefined') {
      const currentUrl = window.location.origin;
      console.log('🔧 Using current origin as backend URL:', currentUrl);
      return currentUrl;
    }
    
  } catch (e) {
    console.warn('🔧 Error getting backend URL from environment:', e);
  }
  
  // Último fallback - esto no debería usarse normalmente
  console.warn('🔧 Using localhost fallback - this should not happen in production');
  return 'https://022fe56d-38bc-4752-a5da-625969514d2c.preview.emergentagent.com';
}

function getWebSocketUrl(): string {
  const backendUrl = getBackendUrl();
  // Para WebSocket, usar la misma URL pero agregar el path de socket.io
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