# 📡 Mitosis API Documentation

**Versión**: 2.0.0 (Post-Refactorización)  
**Última actualización**: Enero 2025

---

## Estructura General

Todas las APIs del backend están prefijadas con `/api` para cumplir con las reglas de ingress de Kubernetes.

**Base URL**: `https://6a42dbad-573b-4631-929d-0d271703ed7e.preview.emergentagent.com/api`

---

## 🔧 Core System APIs

### Health Check
**Endpoint**: `GET /api/health`  
**Descripción**: Verificación general de salud del sistema

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-26T18:45:00Z",
  "services": {
    "database": true,
    "ollama": true,
    "tools": 12
  },
  "uptime": "2h 34m"
}
```

### Agent Health
**Endpoint**: `GET /api/agent/health`  
**Descripción**: Estado específico del agente

**Response**:
```json
{
  "status": "running",
  "agent_id": "mitosis-agent",
  "version": "2.0.0",
  "capabilities": {
    "autonomous_execution": true,
    "real_time_monitoring": true,
    "multi_tool_support": true
  }
}
```

### Agent Status
**Endpoint**: `GET /api/agent/status`  
**Descripción**: Estado completo y configuración del agente

**Response**:
```json
{
  "status": "running",
  "agent_id": "mitosis-agent",
  "tools_available": 12,
  "ollama": {
    "connected": true,
    "endpoint": "https://bef4a4bb93d1.ngrok-free.app",
    "model": "llama3.1:8b",
    "health": "ok"
  },
  "database": {
    "connected": true,
    "collections": ["tasks", "memory", "files"]
  },
  "memory": {
    "total_entries": 1250,
    "last_updated": "2025-01-26T18:44:32Z"
  }
}
```

---

## 🤖 Agent Interaction APIs

### Chat Interface
**Endpoint**: `POST /api/agent/chat`  
**Descripción**: Interfaz principal para comunicación con el agente

**Request Body**:
```json
{
  "message": "Crear un análisis de mercado para productos de software en 2025",
  "task_id": "optional-task-id",
  "memory_context": true
}
```

**Response**:
```json
{
  "response": "Plan generado exitosamente. Iniciando análisis de mercado...",
  "task_id": "task-uuid-12345",
  "timestamp": "2025-01-26T18:45:00Z",
  "plan": {
    "title": "Análisis de Mercado de Software 2025",
    "description": "Análisis completo del mercado de software con tendencias y predicciones",
    "steps": [
      {
        "id": "step-1",
        "title": "Investigación de mercado",
        "description": "Recopilar datos actuales del mercado",
        "tool": "web_search_tool",
        "status": "pending",
        "estimated_time": "2-3 minutos"
      }
    ],
    "estimated_total_time": "8-12 minutos",
    "complexity": "medium"
  },
  "enhanced_title": "Análisis de Mercado de Software 2025",
  "memory_used": true
}
```

---

## 🔧 Tools Management APIs

### Available Tools
**Endpoint**: `GET /api/tools/available`  
**Descripción**: Lista todas las herramientas disponibles

**Response**:
```json
{
  "tools_count": 12,
  "tools": [
    {
      "name": "web_search_tool",
      "description": "Búsqueda web inteligente con Playwright",
      "version": "2.0.0",
      "category": "search",
      "parameters": ["query", "num_results", "search_type"]
    },
    {
      "name": "shell_tool",
      "description": "Ejecución de comandos del sistema",
      "version": "2.0.0", 
      "category": "system",
      "parameters": ["command", "timeout", "working_dir"]
    }
  ],
  "auto_discovery": true,
  "lazy_loading": true
}
```

---

## 📡 WebSocket Events

### Eventos Enviados por el Servidor

#### task_progress
Progreso de una tarea en ejecución
```json
{
  "task_id": "task-uuid-12345",
  "progress": 50,
  "current_step": "step-2",
  "step_title": "Análisis de datos",
  "estimated_remaining": "4 minutos"
}
```

#### step_completed
Un paso se ha completado
```json
{
  "task_id": "task-uuid-12345",
  "step_id": "step-2",
  "status": "completed",
  "result": {
    "success": true,
    "output": "Análisis completado",
    "execution_time": 3.45
  },
  "files_created": ["analysis_results.json"]
}
```

#### task_completed
Tarea completada
```json
{
  "task_id": "task-uuid-12345",
  "status": "completed",
  "final_result": {
    "success": true,
    "summary": "Análisis de mercado completado exitosamente",
    "files_generated": 3,
    "total_execution_time": 720
  },
  "download_links": [
    "/api/files/download/file-uuid-789"
  ]
}
```

---

**🚀 Mitosis API v2.0.0**  
*Potenciando la automatización inteligente*