// Unified API service for Mitosis Agent
import { io, Socket } from 'socket.io-client';

const getBackendUrl = () => {
  return import.meta.env.VITE_BACKEND_URL || 
         import.meta.env.REACT_APP_BACKEND_URL || 
         process.env.REACT_APP_BACKEND_URL ||
         'http://localhost:5000';
};

const API_BASE_URL = `${getBackendUrl()}/api`;

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
}

export interface MonitorPage {
  id: string;
  title: string;
  content: string;
  type: 'plan' | 'tool-execution' | 'report' | 'file' | 'error' | 'user-message' | 'agent-response' | 'task-creation';
  timestamp: string;
  metadata: {
    lineCount?: number;
    fileSize?: number;
    status?: string;
    session_id?: string;
    task_id?: string;
    error_type?: string;
    [key: string]: any;
  };
}

export interface MonitorPagesResponse {
  pages: MonitorPage[];
  total_pages: number;
  current_page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface AgentStatus {
  state: string;
  uptime_seconds: number;
  statistics: {
    messages_processed?: number;
    tasks_completed?: number;
    [key: string]: any;
  };
  available_models: string[];
  current_model?: string;
  memory_stats: {
    short_term_memory?: {
      current_messages?: number;
      [key: string]: any;
    };
    long_term_memory?: {
      total_knowledge?: number;
      total_tasks?: number;
      [key: string]: any;
    };
    [key: string]: any;
  };
}

export interface ChatResponse {
  response: string;
  session_id: string;
  timestamp: string;
}

export interface TaskResponse {
  task_id: string;
  status: string;
  timestamp: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  goal: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TasksResponse {
  tasks: Task[];
}

class UnifiedAgentAPI {
  private baseUrl: string;
  private socket: Socket | null = null;
  private eventListeners: Map<string, Function[]> = new Map();

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // Initialize WebSocket connection
  initializeSocket(): Socket {
    if (this.socket) {
      return this.socket;
    }

    this.socket = io(getBackendUrl(), {
      transports: ['websocket', 'polling'],
      autoConnect: true
    });

    this.socket.on('connect', () => {
      console.log('Connected to Unified Mitosis API');
      this.emit('socket_connected', { connected: true });
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from Unified Mitosis API');
      this.emit('socket_disconnected', { connected: false });
    });

    this.socket.on('new_monitor_page', (data: MonitorPage) => {
      this.emit('new_monitor_page', data);
    });

    this.socket.on('connected', (data: { room_id: string }) => {
      console.log('Assigned room ID:', data.room_id);
      // Join monitoring room
      this.socket?.emit('join_monitoring', { room_id: data.room_id });
    });

    this.socket.on('monitoring_joined', (data: { status: string }) => {
      console.log('Joined monitoring room:', data.status);
      this.emit('monitoring_ready', data);
    });

    return this.socket;
  }

  // Event system for real-time updates
  on(event: string, callback: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(callback);
  }

  off(event: string, callback: Function): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => callback(data));
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string; uptime: number }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking health:', error);
      throw error;
    }
  }

  // Get agent status
  async getStatus(): Promise<AgentStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting status:', error);
      throw error;
    }
  }

  // Send message to agent
  async sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  // Get all tasks
  async getTasks(): Promise<TasksResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/tasks`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting tasks:', error);
      throw error;
    }
  }

  // Create new task
  async createTask(title: string, description: string, goal: string, tools: string[] = []): Promise<TaskResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/tasks/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          description,
          goal,
          tools
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (error) {
      console.error('Error creating task:', error);
      throw error;
    }
  }

  // Get monitor pages with pagination
  async getMonitorPages(page: number = 1, perPage: number = 10): Promise<MonitorPagesResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/monitor/pages?page=${page}&per_page=${perPage}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting monitor pages:', error);
      throw error;
    }
  }

  // Get latest monitor page
  async getLatestPage(): Promise<MonitorPage & { page_number: number }> {
    try {
      const response = await fetch(`${this.baseUrl}/monitor/latest`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting latest page:', error);
      throw error;
    }
  }

  // Disconnect socket
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export const unifiedAPI = new UnifiedAgentAPI();

// Initialize socket connection on module load
unifiedAPI.initializeSocket();

export default unifiedAPI;

