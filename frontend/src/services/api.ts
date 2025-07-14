// Servicio para comunicación con el backend del agente
const getBackendUrl = () => {
  return import.meta.env.VITE_BACKEND_URL || 
         import.meta.env.REACT_APP_BACKEND_URL || 
         process.env.REACT_APP_BACKEND_URL;
};

const API_BASE_URL = `${getBackendUrl()}/api/agent`;

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
}

export interface ToolCall {
  tool: string;
  parameters: Record<string, any>;
}

export interface ToolResult {
  tool: string;
  parameters: Record<string, any>;
  result: any;
}

export interface SearchData {
  query: string;
  directAnswer: string;
  sources: Array<{
    title: string;
    content: string;
    url: string;
  }>;
  type: 'websearch' | 'deepsearch';
  key_findings?: string[];
  recommendations?: string[];
}

export interface UploadData {
  files: Array<{
    id: string;
    name: string;
    size: number;
    type: string;
    mime_type: string;
    path: string;
    source: 'uploaded' | 'agent';
  }>;
  count: number;
  total_size: number;
}

export interface ChatResponse {
  response: string;
  tool_calls: ToolCall[];
  tool_results: ToolResult[];
  timestamp: string;
  model?: string;
  search_mode?: 'websearch' | 'deepsearch';
  search_data?: SearchData;
  upload_data?: UploadData;
  created_files?: any[];
}

export interface AgentStatus {
  status: string;
  ollama_status: string;
  available_models: string[];
  current_model: string;
  tools_count: number;
  error?: string;
}

export interface Tool {
  name: string;
  description: string;
  parameters: string[];
}

export interface FileItem {
  id: string;
  name: string;
  path: string;
  size: number;
  type: 'file' | 'directory';
  mime_type?: string;
  created_at: string;
}

class AgentAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async sendMessage(message: string, context: any = {}): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          context
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

  async getTools(): Promise<Tool[]> {
    try {
      const response = await fetch(`${this.baseUrl}/tools`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.tools || [];
    } catch (error) {
      console.error('Error getting tools:', error);
      throw error;
    }
  }

  async uploadFiles(taskId: string, files: FileList): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('task_id', taskId);
      
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const response = await fetch(`${this.baseUrl}/upload-files`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading files:', error);
      throw error;
    }
  }

  async getTaskFiles(taskId: string): Promise<FileItem[]> {
    try {
      const response = await fetch(`${this.baseUrl}/files/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.files || [];
    } catch (error) {
      console.error('Error getting task files:', error);
      throw error;
    }
  }

  async downloadFile(fileId: string): Promise<Blob> {
    try {
      const response = await fetch(`${this.baseUrl}/download/${fileId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  }

  async downloadAllFiles(taskId: string): Promise<Blob> {
    try {
      const response = await fetch(`${this.baseUrl}/download-all/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Error downloading all files:', error);
      throw error;
    }
  }

  async downloadSelectedFiles(fileIds: string[]): Promise<Blob> {
    try {
      const response = await fetch(`${this.baseUrl}/download-selected`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_ids: fileIds
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Error downloading selected files:', error);
      throw error;
    }
  }
}

export const agentAPI = new AgentAPI();

