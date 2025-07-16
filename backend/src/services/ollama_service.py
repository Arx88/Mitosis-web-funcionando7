"""
Servicio de integración con Ollama - Versión Real
Conecta directamente con Ollama para generar respuestas
"""

import json
import time
import os
from typing import Dict, List, Optional, Any
import requests
from requests.exceptions import RequestException, Timeout

class OllamaService:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.default_model = "llama3.1:8b"
        self.current_model = None
        self.conversation_history = []
        self.request_timeout = 30  # Timeout para requests a Ollama
        
    def is_healthy(self) -> bool:
        """Verificar si Ollama está disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_connection(self) -> Dict[str, Any]:
        """Verificar conexión con Ollama y retornar información detallada"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                return {
                    'status': 'connected',
                    'url': self.base_url,
                    'models_available': len(models),
                    'current_model': self.current_model or self.default_model,
                    'healthy': True
                }
        except Exception as e:
            return {
                'status': 'error',
                'url': self.base_url,
                'error': str(e),
                'healthy': False
            }
        
        return {
            'status': 'disconnected',
            'url': self.base_url,
            'healthy': False
        }
    
    def get_available_models(self) -> List[str]:
        """Obtener lista de modelos disponibles desde Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                return models
        except:
            pass
        
        # Fallback a modelos conocidos si no se puede conectar
        return [
            "llama3.2",
            "llama3.1", 
            "mistral",
            "codellama",
            "phi3"
        ]
    
    def set_model(self, model_name: str) -> bool:
        """Establecer el modelo a usar"""
        available_models = self.get_available_models()
        if model_name in available_models:
            self.current_model = model_name
            return True
        return False
    
    def get_current_model(self) -> str:
        """Obtener el modelo actual"""
        return self.current_model or self.default_model
    
    def generate_response(self, prompt: str, context: Dict = None, use_tools: bool = True) -> Dict[str, Any]:
        """
        Generar respuesta usando Ollama real
        
        Args:
            prompt: Mensaje del usuario
            context: Contexto adicional (historial, herramientas, etc.)
            use_tools: Si debe considerar el uso de herramientas
        
        Returns:
            Dict con respuesta, tool_calls, y metadatos
        """
        if not self.is_healthy():
            return {
                'response': "⚠️ Ollama no está disponible en este momento. Asegúrate de que esté ejecutándose en localhost:11434",
                'tool_calls': [],
                'raw_response': "",
                'model': self.get_current_model(),
                'timestamp': time.time(),
                'error': 'Ollama no disponible'
            }
        
        try:
            # Construir el prompt completo
            system_prompt = self._build_system_prompt(use_tools, conversation_mode=False)
            full_prompt = self._build_full_prompt(prompt, context, system_prompt)
            
            # Hacer la llamada a Ollama
            response = self._call_ollama_api(full_prompt)
            
            if response.get('error'):
                return {
                    'response': f"❌ Error al generar respuesta: {response['error']}",
                    'tool_calls': [],
                    'raw_response': "",
                    'model': self.get_current_model(),
                    'timestamp': time.time(),
                    'error': response['error']
                }
            
            # Parsear la respuesta
            parsed_response = self._parse_response(response.get('response', ''))
            
            return {
                'response': parsed_response['text'],
                'tool_calls': parsed_response['tool_calls'],
                'raw_response': response.get('response', ''),
                'model': self.get_current_model(),
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'response': f"❌ Error interno: {str(e)}",
                'tool_calls': [],
                'raw_response': "",
                'model': self.get_current_model(),
                'timestamp': time.time(),
                'error': str(e)
            }
    
    def _call_ollama_api(self, prompt: str) -> Dict[str, Any]:
        """Hacer llamada real a la API de Ollama"""
        try:
            payload = {
                "model": self.get_current_model(),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Timeout:
            return {
                'error': f"Timeout después de {self.request_timeout} segundos"
            }
        except RequestException as e:
            return {
                'error': f"Error de conexión: {str(e)}"
            }
        except Exception as e:
            return {
                'error': f"Error inesperado: {str(e)}"
            }
    
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
    
    def _build_system_prompt(self, use_tools: bool, conversation_mode: bool = False) -> str:
        """Construir prompt del sistema"""
        
        # Sistema prompt para conversación casual (sin planes ni herramientas)
        if conversation_mode:
            return """Eres un asistente de IA general llamado 'Agente General' que puede ayudar con una amplia variedad de tareas. 
Eres inteligente, útil y amigable.

IMPORTANTE: Estás en modo conversación casual. Responde de manera natural y amigable sin generar planes de acción ni mencionar herramientas.

Para preguntas personales como "¿Cómo te llamas?", "¿Quién eres?", responde de manera simple y directa.
Para saludos como "Hola", "¿Cómo estás?", responde amigablemente.
Para agradecimientos como "Gracias", responde cortésmente.

Mantén las respuestas breves, naturales y conversacionales.
Responde en español de manera clara y amigable."""
        
        # Sistema prompt para tareas (con planes y herramientas)
        base_prompt = """Eres un asistente de IA general llamado 'Agente General' que puede ayudar con una amplia variedad de tareas. 
Eres inteligente, útil y puedes usar herramientas para realizar acciones concretas.

IMPORTANTE: Cuando recibas una tarea, SIEMPRE debes generar un PLAN DE ACCIÓN ESPECÍFICO y DETALLADO paso a paso.

El plan debe ser:
1. ESPECÍFICO para la tarea solicitada (no genérico)
2. DETALLADO con pasos concretos
3. ESTRUCTURADO en orden lógico
4. PRÁCTICO y realizable

Formato del plan:
**PLAN DE ACCIÓN:**
1. [Paso específico 1]
2. [Paso específico 2]
3. [Paso específico 3]
4. [Paso específico 4]
5. [Paso específico 5]

Después del plan, explica brevemente qué vas a hacer y qué herramientas utilizarás.

Responde en español de manera clara y concisa."""
        
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
2. **web_search** - Buscar información en internet
3. **file_manager** - Gestionar archivos y directorios
4. **deep_research** - Investigación profunda
5. **tavily_search** - Búsqueda avanzada web
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
    
    def chat_streaming(self, prompt: str, context: Dict = None, use_tools: bool = True):
        """
        Generar respuesta streaming usando Ollama
        Devuelve un generator que produce chunks de respuesta
        """
        if not self.is_healthy():
            yield {
                'response': "⚠️ Ollama no está disponible en este momento.",
                'done': True,
                'error': 'Ollama no disponible'
            }
            return
        
        try:
            system_prompt = self._build_system_prompt(use_tools, conversation_mode=False)
            full_prompt = self._build_full_prompt(prompt, context, system_prompt)
            
            payload = {
                "model": self.get_current_model(),
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.request_timeout,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            yield chunk
                        except json.JSONDecodeError:
                            continue
            else:
                yield {
                    'response': f"❌ Error HTTP {response.status_code}: {response.text}",
                    'done': True,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            yield {
                'response': f"❌ Error: {str(e)}",
                'done': True,
                'error': str(e)
            }