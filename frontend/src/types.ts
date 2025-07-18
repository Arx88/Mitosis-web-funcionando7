export interface Task {
  id: string;
  title: string;
  createdAt: Date;
  status: 'pending' | 'in-progress' | 'completed' | 'failed' | 'ready';
  messages: Message[];
  terminalCommands: TerminalCommand[];
  plan?: TaskStep[];
  isFavorite?: boolean;
  iconType?: string; // Agregar el tipo de icono
  progress?: number; // Progress from 0 to 100
  executionData?: any; // Datos de ejecución del backend para mostrar en terminal
}

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  attachments?: any[];
  status?: {
    type: 'success' | 'error' | 'info';
    message: string;
  };
  searchData?: any;
  uploadData?: any;
  toolResults?: any[];
  links?: any[];
}

export interface TerminalCommand {
  id: string;
  command: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  output?: string;
  timestamp?: Date;
}

export interface TaskStep {
  id: string;
  title: string;
  completed: boolean;
  active: boolean;
  description?: string;
  estimated_time?: string;
  tool?: string;
  status?: string;
}

export interface AgentConfig {
  systemPrompt: string;
  memory: {
    enabled: boolean;
    maxMessages: number;
    contextWindow: number;
  };
  ollama: {
    enabled: boolean;
    model: string;
    temperature: number;
    maxTokens: number;
    endpoint: string;
  };
  openrouter: {
    enabled: boolean;
    model: string;
    apiKey: string;
    temperature: number;
    maxTokens: number;
    endpoint: string;
  };
  tools: {
    shell: {
      enabled: boolean;
      allowedCommands: string[];
      timeout: number;
    };
    webSearch: {
      enabled: boolean;
      maxResults: number;
      timeout: number;
    };
    fileManager: {
      enabled: boolean;
      allowedPaths: string[];
      maxFileSize: number;
    };
  };
}

export interface AppState {
  sidebarCollapsed: boolean;
  terminalSize: number;
  isThinking: boolean;
  config: AgentConfig;
}