// Configuración centralizada de API y WebSocket
// SISTEMA COMPLETAMENTE DINÁMICO - SIN HARDCODED URLs

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
  // 🚀 AUTODETECCIÓN DINÁMICA - SIN URLs HARDCODEADAS
  try {
    // 1. PRIMERA PRIORIDAD: Variable de entorno si está disponible
    const envUrl = import.meta.env?.VITE_BACKEND_URL || 
                   import.meta.env?.REACT_APP_BACKEND_URL ||
                   (typeof process !== 'undefined' ? process.env.REACT_APP_BACKEND_URL : null);
                   
    if (envUrl && envUrl !== 'undefined' && !envUrl.includes('64a3482e-5c9e-4f08-9906-c7e8583b532a')) {
      console.log('🔧 Using environment backend URL:', envUrl);
      return envUrl;
    }
    
    // 2. DETECCIÓN AUTOMÁTICA: Usar el dominio actual del browser
    if (typeof window !== 'undefined') {
      const currentOrigin = window.location.origin;
      console.log('🔧 AUTO-DETECTED backend URL from browser:', currentOrigin);
      return currentOrigin;
    }
    
    // 3. Si estamos en development mode
    if (import.meta.env?.MODE === 'development') {
      console.log('🔧 Using development backend URL: http://localhost:8001');
      return 'http://localhost:8001';
    }
    
  } catch (e) {
    console.warn('🔧 Error during dynamic URL detection:', e);
  }
  
  // 4. FALLBACK FINAL: Intentar detectar desde browser si está disponible
  if (typeof window !== 'undefined') {
    const detected = window.location.origin;
    console.log('🔧 FALLBACK: Using browser origin as backend URL:', detected);
    return detected;
  }
  
  // 5. ÚLTIMO RECURSO: localhost para desarrollo
  console.warn('🔧 FINAL FALLBACK: Using localhost for local development');
  return 'http://localhost:8001';
}

function getWebSocketUrl(): string {
  const backendUrl = getBackendUrl();
  // CRÍTICO: Usar /api/socket.io/ para routing correcto en producción
  return `${backendUrl}/api/socket.io/`;
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
    url: `${getBackendUrl()}`,  // Solo la URL base
    options: {
      path: '/api/socket.io/',    // PATH EXPLÍCITO  
      transports: ['polling'],     // SOLO POLLING para máxima estabilidad
      upgrade: false,              // NO upgrade a websocket
      reconnection: true,
      reconnectionDelay: 2000,     // Delay más largo para estabilidad
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
console.log('🔧 DYNAMIC API Configuration loaded:', {
  backendUrl: API_CONFIG.backend.url,
  wsUrl: API_CONFIG.websocket.url,
  detectionMethod: 'BROWSER_ORIGIN_AUTO_DETECTION',
  availableEndpoints: Object.keys(API_CONFIG.endpoints).length
});