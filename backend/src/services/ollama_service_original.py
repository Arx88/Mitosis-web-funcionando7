"""
Servicio de integración con Ollama
Maneja la comunicación con el modelo de lenguaje
"""

import json
import requests
from typing import Dict, List, Optional, Any
import time

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.default_model = "llama3.2"
        self.current_model = None
        self.conversation_history = []
        
    def is_healthy(self) -> bool:
        """Verificar si Ollama está disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self) -> List[str]:
        """Obtener lista de modelos disponibles"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except:
            pass
        return []
    
    def set_model(self, model_name: str) -> bool:
        """Establecer el modelo a usar"""
        available_models = self.get_available_models()
        if model_name in available_models:
            self.current_model = model_name
            return True
        return False
    
    def get_current_model(self) -> str:
        """Obtener el modelo actual"""
        if self.current_model:
            return self.current_model
        
        # Intentar usar el modelo por defecto
        available_models = self.get_available_models()
        if available_models:
            self.current_model = available_models[0]
            return self.current_model
        
        return self.default_model
    
    def generate_response(self, prompt: str, context: Dict = None, use_tools: bool = True) -> Dict[str, Any]:
        """
        Generar respuesta usando Ollama
        
        Args:
            prompt: Mensaje del usuario
            context: Contexto adicional (historial, herramientas, etc.)
            use_tools: Si debe considerar el uso de herramientas
        
        Returns:
            Dict con respuesta, tool_calls, y metadatos
        """
        model = self.get_current_model()
        
        # Construir el prompt con contexto de herramientas
        system_prompt = self._build_system_prompt(use_tools)
        full_prompt = self._build_full_prompt(prompt, context, system_prompt)
        
        try:
            # Llamada a Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Parsear respuesta para detectar llamadas a herramientas
                parsed_response = self._parse_response(response_text)
                
                return {
                    'response': parsed_response['text'],
                    'tool_calls': parsed_response['tool_calls'],
                    'raw_response': response_text,
                    'model': model,
                    'timestamp': time.time()
                }
            else:
                return {
                    'response': 'Error al comunicarse con Ollama',
                    'tool_calls': [],
                    'error': f"HTTP {response.status_code}",
                    'timestamp': time.time()
                }
                
        except Exception as e:
            return {
                'response': f'Error de conexión con Ollama: {str(e)}',
                'tool_calls': [],
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _build_system_prompt(self, use_tools: bool) -> str:
        """Construir prompt del sistema"""
        base_prompt = """Eres un asistente de IA general llamado 'Agente General' que puede ayudar con una amplia variedad de tareas. 
Eres inteligente, útil y puedes usar herramientas para realizar acciones concretas."""
        
        if use_tools:
            tools_prompt = """
HERRAMIENTAS DISPONIBLES:
Para usar una herramienta, incluye en tu respuesta un bloque JSON con el siguiente formato:
```json
{
  "tool_call": {
    "tool": "nombre_herramienta",
    "parameters": {
      "parametro": "valor"
    }
  }
}
```

Herramientas disponibles:
1. **shell** - Ejecutar comandos de terminal
   - Parámetros: {"command": "comando a ejecutar"}
   - Ejemplo: {"tool": "shell", "parameters": {"command": "ls -la"}}

2. **web_search** - Buscar información en internet
   - Parámetros: {"query": "términos de búsqueda"}
   - Ejemplo: {"tool": "web_search", "parameters": {"query": "Python tutorial"}}

3. **file_manager** - Gestionar archivos y directorios
   - Parámetros: {"action": "read/write/create/delete", "path": "ruta", "content": "contenido"}
   - Ejemplo: {"tool": "file_manager", "parameters": {"action": "read", "path": "/tmp/file.txt"}}

IMPORTANTE: 
- Siempre explica qué vas a hacer antes de usar una herramienta
- Usa las herramientas solo cuando sea necesario
- Puedes usar múltiples herramientas en una sola respuesta
- Después de usar una herramienta, explica los resultados
"""
            return base_prompt + tools_prompt
        
        return base_prompt
    
    def _build_full_prompt(self, prompt: str, context: Dict, system_prompt: str) -> str:
        """Construir prompt completo con contexto"""
        full_prompt = f"{system_prompt}\n\n"
        
        # Añadir contexto si está disponible
        if context:
            if 'task_id' in context:
                full_prompt += f"ID de tarea: {context['task_id']}\n"
            
            if 'previous_messages' in context and context['previous_messages']:
                full_prompt += "Conversación anterior:\n"
                for msg in context['previous_messages'][-3:]:  # Últimos 3 mensajes
                    sender = "Usuario" if msg.get('sender') == 'user' else "Asistente"
                    full_prompt += f"{sender}: {msg.get('content', '')}\n"
                full_prompt += "\n"
        
        full_prompt += f"Usuario: {prompt}\nAsistente: "
        
        return full_prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parsear respuesta para extraer texto y tool calls"""
        import re
        
        # Buscar bloques JSON en la respuesta
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        tool_calls = []
        clean_text = response_text
        
        for match in matches:
            try:
                data = json.loads(match)
                if 'tool_call' in data:
                    tool_calls.append(data['tool_call'])
                    # Remover el bloque JSON del texto
                    clean_text = clean_text.replace(f'```json\n{match}\n```', '')
            except json.JSONDecodeError:
                continue
        
        return {
            'text': clean_text.strip(),
            'tool_calls': tool_calls
        }