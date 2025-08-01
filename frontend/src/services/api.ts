// Servicio para comunicación con el backend del agente
import { API_CONFIG, getApiUrl } from '../config/api';

// Usar directamente la URL base sin duplicar /api/agent
const API_BASE_URL = API_CONFIG.backend.url;

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
  // Plan structure from backend
  plan?: {
    steps: Array<{
      id: string;
      title: string;
      description: string;
      tool: string;
      status: string;
      estimated_time: string;
      completed: boolean;
      active: boolean;
    }>;
    total_steps: number;
    estimated_total_time: string;
    task_type: string;
  };
  // Nuevos campos para orquestación
  orchestration_enabled?: boolean;
  task_id?: string;
  execution_status?: 'orchestrating' | 'completed' | 'failed';
  websocket_enabled?: boolean;
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

// Nuevas interfaces para Execution Engine y Context Manager
export interface TaskAnalysis {
  task_type: string;
  complexity: string;
  estimated_duration: number;
  required_tools: string[];
  success_probability: number;
  risk_factors: string[];
  analysis_timestamp: string;
}

export interface ExecutionPlan {
  task_id: string;
  title: string;
  steps: Array<{
    id: string;
    title: string;
    description: string;
    tool: string;
    parameters: Record<string, any>;
    dependencies: string[];
    estimated_duration: number;
    complexity: string;
    required_skills: string[];
  }>;
  total_estimated_duration: number;
  complexity_score: number;
  required_tools: string[];
  success_probability: number;
  risk_factors: string[];
  prerequisites: string[];
}

export interface ExecutionStatus {
  task_id: string;
  status: string;
  progress: number;
  current_step: number;
  total_steps: number;
  execution_time: number;
  success_rate: number;
  steps: Array<{
    id: string;
    title: string;
    status: string;
    execution_time: number;
    retry_count: number;
  }>;
}

export interface ContextInfo {
  session_id: string;
  task_id: string;
  created_at: string;
  last_accessed: string;
  is_active: boolean;
  variables: Record<string, any>;
  variables_count: number;
  expired_variables: number;
  checkpoints_count: number;
  metadata: Record<string, any>;
}

export interface ContextVariable {
  key: string;
  value: any;
  type: string;
  scope: string;
  created_at: string;
  updated_at: string;
  expires_at?: string;
  source_step?: string;
}

export interface ContextCheckpoint {
  checkpoint_id: string;
  step_id: string;
  timestamp: string;
  description: string;
  auto_created: boolean;
  variables_count: number;
}

// Nuevas interfaces para orquestación
export interface OrchestrationResult {
  task_id: string;
  success: boolean;
  total_execution_time: number;
  steps_completed: number;
  steps_failed: number;
  adaptations_made: number;
  resource_usage: Record<string, any>;
  error?: string;
  execution_plan?: {
    id: string;
    title: string;
    strategy: string;
    total_steps: number;
    estimated_duration: number;
    complexity_score: number;
    success_probability: number;
  };
}

export interface OrchestrationStatus {
  task_id: string;
  status: 'planning' | 'executing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  start_time: number;
  elapsed_time: number;
  current_step?: string;
  total_steps?: number;
  context: Record<string, any>;
}

export interface OrchestrationMetrics {
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  avg_execution_time: number;
  success_rate: number;
  active_tasks: number;
}

class AgentAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async sendMessage(message: string, context: any = {}): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.chat}`, {
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
      const response = await fetch(`${this.baseUrl}/api/agent/status`);
      
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
      const response = await fetch(`${this.baseUrl}/api/agent/tools`);
      
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

      const response = await fetch(`${this.baseUrl}/api/agent/upload-files`, {
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
      const response = await fetch(`${this.baseUrl}/api/agent/get-task-files/${taskId}`);
      
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
      const response = await fetch(`${this.baseUrl}/api/agent/download/${fileId}`);
      
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
      const response = await fetch(`${this.baseUrl}/api/agent/download-all/${taskId}`);
      
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
      const response = await fetch(`${this.baseUrl}/api/agent/download-selected`, {
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

  async generateShareLink(taskId: string): Promise<{ link: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agent/generate-share-link`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: taskId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating share link:', error);
      throw error;
    }
  }

  // ==========================================
  // EXECUTION ENGINE API METHODS
  // ==========================================

  async analyzeTask(taskTitle: string, taskDescription: string = ''): Promise<TaskAnalysis> {
    try {
      const response = await fetch(`${this.baseUrl}/task/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_title: taskTitle,
          task_description: taskDescription
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.analysis;
    } catch (error) {
      console.error('Error analyzing task:', error);
      throw error;
    }
  }

  async generateExecutionPlan(taskId: string, taskTitle: string, taskDescription: string = ''): Promise<ExecutionPlan> {
    try {
      const response = await fetch(`${this.baseUrl}/task/plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: taskId,
          task_title: taskTitle,
          task_description: taskDescription
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.execution_plan;
    } catch (error) {
      console.error('Error generating execution plan:', error);
      throw error;
    }
  }

  async executeTask(taskId: string, taskTitle: string, taskDescription: string = '', config: any = {}): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/task/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: taskId,
          task_title: taskTitle,
          task_description: taskDescription,
          config: config
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error executing task:', error);
      throw error;
    }
  }

  async getExecutionStatus(taskId: string): Promise<ExecutionStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/task/execution-status/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.execution_status;
    } catch (error) {
      console.error('Error getting execution status:', error);
      throw error;
    }
  }

  async stopTaskExecution(taskId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/task/stop/${taskId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error stopping task execution:', error);
      throw error;
    }
  }

  async cleanupTaskExecution(taskId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/task/cleanup/${taskId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error cleaning up task execution:', error);
      throw error;
    }
  }

  // ==========================================
  // CONTEXT MANAGER API METHODS
  // ==========================================

  async getContextInfo(taskId: string): Promise<ContextInfo> {
    try {
      const response = await fetch(`${this.baseUrl}/context/info/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.context_info;
    } catch (error) {
      console.error('Error getting context info:', error);
      throw error;
    }
  }

  async getContextVariables(taskId: string, scope?: string): Promise<Record<string, any>> {
    try {
      const url = scope ? `${this.baseUrl}/context/variables/${taskId}?scope=${scope}` : `${this.baseUrl}/context/variables/${taskId}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.variables || {};
    } catch (error) {
      console.error('Error getting context variables:', error);
      throw error;
    }
  }

  async setContextVariable(taskId: string, key: string, value: any, type: string = 'object', scope: string = 'task'): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/context/variables/${taskId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          key,
          value,
          type,
          scope
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error setting context variable:', error);
      throw error;
    }
  }

  async getContextCheckpoints(taskId: string): Promise<ContextCheckpoint[]> {
    try {
      const response = await fetch(`${this.baseUrl}/context/checkpoints/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.checkpoints || [];
    } catch (error) {
      console.error('Error getting context checkpoints:', error);
      throw error;
    }
  }

  async createCheckpoint(taskId: string, description: string = ''): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/context/checkpoints/${taskId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating checkpoint:', error);
      throw error;
    }
  }

  async restoreCheckpoint(taskId: string, checkpointId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/context/checkpoints/${taskId}/restore`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          checkpoint_id: checkpointId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error restoring checkpoint:', error);
      throw error;
    }
  }

  async getContextStatistics(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/context/statistics`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting context statistics:', error);
      throw error;
    }
  }

  // ==========================================
  // ORCHESTRATION API METHODS
  // ==========================================

  async orchestrateTask(taskDescription: string, userId: string = 'default_user', sessionId?: string, options: any = {}): Promise<OrchestrationResult> {
    try {
      const response = await fetch(`${this.baseUrl}/orchestrate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_description: taskDescription,
          user_id: userId,
          session_id: sessionId || this.generateSessionId(),
          priority: options.priority || 1,
          constraints: options.constraints || {},
          preferences: options.preferences || {},
          metadata: options.metadata || {}
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
      console.error('Error orchestrating task:', error);
      throw error;
    }
  }

  async getOrchestrationStatus(taskId: string): Promise<OrchestrationStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/orchestration/status/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (error) {
      console.error('Error getting orchestration status:', error);
      throw error;
    }
  }

  async getOrchestrationMetrics(): Promise<OrchestrationMetrics> {
    try {
      const response = await fetch(`${this.baseUrl}/orchestration/metrics`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (error) {
      console.error('Error getting orchestration metrics:', error);
      throw error;
    }
  }

  async getActiveOrchestrations(): Promise<OrchestrationStatus[]> {
    try {
      const response = await fetch(`${this.baseUrl}/orchestration/active`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (error) {
      console.error('Error getting active orchestrations:', error);
      throw error;
    }
  }

  async cancelOrchestration(taskId: string): Promise<{success: boolean, message: string}> {
    try {
      const response = await fetch(`${this.baseUrl}/orchestration/cancel/${taskId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
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
      console.error('Error cancelling orchestration:', error);
      throw error;
    }
  }

  async getOrchestrationRecommendations(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/orchestration/recommendations`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (error) {
      console.error('Error getting orchestration recommendations:', error);
      throw error;
    }
  }

  async getTaskStatus(taskId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/task/status/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (error) {
      console.error('Error getting task status:', error);
      throw error;
    }
  }

  // Helper method to generate session ID
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // ==========================================
  // PLAN TEMPLATES API METHODS
  // ==========================================

  async getPlanTemplates(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/plans/templates`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting plan templates:', error);
      throw error;
    }
  }
}

export const agentAPI = new AgentAPI();

