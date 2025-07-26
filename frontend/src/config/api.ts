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
  // Priorizar process.env en producción (cuando se sirve con 'serve')
  // import.meta.env solo funciona con Vite dev server
  let url;
  
  // Verificar si estamos en producción (NODE_ENV o modo de construcción)
  const isProduction = typeof window !== 'undefined' && window.location.hostname !== 'localhost';
  
  if (isProduction || typeof process !== 'undefined') {
    // En producción, usar process.env
    url = process.env.REACT_APP_BACKEND_URL || 
          (typeof window !== 'undefined' && (window as any).__REACT_APP_BACKEND_URL__);
  } else {
    // En desarrollo, usar import.meta.env
    url = import.meta.env.VITE_BACKEND_URL || 
          import.meta.env.REACT_APP_BACKEND_URL || 
          process.env.REACT_APP_BACKEND_URL;
  }
  
  // Fallback para asegurar que siempre tenemos una URL
  if (!url) {
    console.error('Backend URL not configured in environment variables');
    console.log('🔍 Environment check:', {
      isProduction,
      processEnv: typeof process !== 'undefined' ? process.env.REACT_APP_BACKEND_URL : 'undefined',
      importMetaEnv: typeof import.meta !== 'undefined' ? (import.meta.env?.VITE_BACKEND_URL || import.meta.env?.REACT_APP_BACKEND_URL) : 'undefined'
    });
    // Usar URL externa como fallback
    return 'https://c831651b-a7e8-429e-abcb-944983407842.preview.emergentagent.com';
  }
  
  return url;
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