"""
Servicio de integración con Ollama - Versión Dummy
Simula la comunicación con el modelo de lenguaje sin requerir Ollama
"""

import json
import time
from typing import Dict, List, Optional, Any
import random

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.default_model = "llama3.2"
        self.current_model = None
        self.conversation_history = []
        
        # Respuestas predefinidas para simular el comportamiento de Ollama
        self.dummy_responses = [
            "Entiendo tu solicitud. Voy a ayudarte con eso.",
            "Basándome en la información proporcionada, puedo sugerir lo siguiente:",
            "He analizado tu consulta y aquí está mi respuesta:",
            "Permíteme procesar esa información y proporcionarte una respuesta útil.",
            "Excelente pregunta. Aquí tienes mi análisis:",
            "Voy a usar las herramientas disponibles para ayudarte con esta tarea.",
            "Entiendo lo que necesitas. Déjame trabajar en eso para ti.",
            "Basándome en tu solicitud, voy a proceder de la siguiente manera:"
        ]
        
    def is_healthy(self) -> bool:
        """Verificar si Ollama está disponible - Siempre True en modo dummy"""
        return True
    
    def get_available_models(self) -> List[str]:
        """Obtener lista de modelos disponibles - Lista predefinida"""
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
        if self.current_model:
            return self.current_model
        return self.default_model
    
    def generate_response(self, prompt: str, context: Dict = None, use_tools: bool = True) -> Dict[str, Any]:
        """
        Generar respuesta usando simulación de Ollama
        
        Args:
            prompt: Mensaje del usuario
            context: Contexto adicional (historial, herramientas, etc.)
            use_tools: Si debe considerar el uso de herramientas
        
        Returns:
            Dict con respuesta, tool_calls, y metadatos
        """
        model = self.get_current_model()
        
        # Simular tiempo de procesamiento
        time.sleep(random.uniform(0.5, 2.0))
        
        # Generar respuesta basada en el prompt
        response_text = self._generate_dummy_response(prompt, use_tools)
        
        # Parsear respuesta para detectar llamadas a herramientas
        parsed_response = self._parse_response(response_text)
        
        return {
            'response': parsed_response['text'],
            'tool_calls': parsed_response['tool_calls'],
            'raw_response': response_text,
            'model': model,
            'timestamp': time.time()
        }
    
    def _generate_dummy_response(self, prompt: str, use_tools: bool) -> str:
        """Generar respuesta dummy basada en el prompt"""
        prompt_lower = prompt.lower()
        
        # Detectar tipo de solicitud y generar respuesta apropiada
        if any(word in prompt_lower for word in ['buscar', 'search', 'investigar', 'información']):
            if use_tools:
                return f"""Voy a buscar información sobre tu consulta: "{prompt}"

```json
{{
  "tool_call": {{
    "tool": "web_search",
    "parameters": {{
      "query": "{prompt[:50]}..."
    }}
  }}
}}
```

Te ayudo a encontrar la información más relevante sobre este tema."""
            else:
                return f"Basándome en mi conocimiento, puedo decirte que {prompt} es un tema interesante. {random.choice(self.dummy_responses)}"
        
        elif any(word in prompt_lower for word in ['archivo', 'file', 'documento', 'leer']):
            if use_tools:
                return f"""Voy a ayudarte con el manejo de archivos.

```json
{{
  "tool_call": {{
    "tool": "file_manager",
    "parameters": {{
      "action": "read",
      "path": "/tmp/example.txt"
    }}
  }}
}}
```

Procesando tu solicitud de archivo..."""
            else:
                return "Entiendo que necesitas ayuda con archivos. Te puedo asistir con la gestión de documentos."
        
        elif any(word in prompt_lower for word in ['ejecutar', 'comando', 'shell', 'terminal']):
            if use_tools:
                return f"""Voy a ejecutar el comando solicitado.

```json
{{
  "tool_call": {{
    "tool": "shell",
    "parameters": {{
      "command": "echo 'Ejecutando comando...'"
    }}
  }}
}}
```

Procesando comando..."""
            else:
                return "Entiendo que quieres ejecutar un comando. Te puedo ayudar con tareas de terminal."
        
        elif any(word in prompt_lower for word in ['crear', 'generar', 'hacer', 'desarrollar']):
            return f"Perfecto, voy a ayudarte a crear lo que necesitas. {random.choice(self.dummy_responses)} Basándome en tu solicitud '{prompt}', puedo sugerir varios enfoques para lograr el resultado deseado."
        
        elif any(word in prompt_lower for word in ['explicar', 'qué es', 'cómo', 'por qué']):
            return f"Excelente pregunta sobre '{prompt}'. {random.choice(self.dummy_responses)} Te explico de manera detallada para que puedas entender completamente el concepto."
        
        else:
            # Respuesta genérica
            base_response = random.choice(self.dummy_responses)
            return f"{base_response} Respecto a tu consulta: '{prompt}', puedo proporcionarte información útil y asistencia personalizada."
    
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
2. **web_search** - Buscar información en internet
3. **file_manager** - Gestionar archivos y directorios
4. **deep_research** - Investigación profunda
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

