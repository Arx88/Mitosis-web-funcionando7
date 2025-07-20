"""
Servicio de integración con Ollama - Versión Real
Conecta directamente con Ollama para generar respuestas
"""

import json
import time
import os
import logging
from typing import Dict, List, Optional, Any
import requests
from requests.exceptions import RequestException, Timeout

class OllamaService:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.1:8b")  # Configurable por defecto
        self.current_model = None
        self.conversation_history = []
        self.request_timeout = 90  # Base timeout, será sobrescrito por configuración por modelo
        
        # 🆕 PROBLEMA 3: Configuración de parámetros por modelo
        self.model_configs = self._load_model_configs()
        
    def _load_model_configs(self) -> dict:
        """Carga las configuraciones de los modelos desde un archivo o define valores por defecto."""
        config_path = os.getenv("OLLAMA_MODEL_CONFIGS_PATH", "/app/backend/config/ollama_model_configs.json")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    configs = json.load(f)
                    
                    # Validar estructura básica de las configuraciones cargadas
                    for model, params in configs.items():
                        if model.startswith('_'):  # Ignorar metadatos
                            continue
                        if not isinstance(params, dict) or "options" not in params:
                            logging.getLogger(__name__).warning(f"⚠️ Configuración inválida para el modelo {model}. Usando valores por defecto.")
                            configs[model] = self._get_default_model_config()
                    
                    logging.getLogger(__name__).info(f"✅ Configuraciones de modelos Ollama cargadas desde {config_path}")
                    return configs
            else:
                logging.getLogger(__name__).info(f"ℹ️ Archivo de configuración no encontrado en {config_path}. Usando valores por defecto.")
                return self._get_default_model_configs()
                
        except Exception as e:
            logging.getLogger(__name__).error(f"❌ Error al cargar configuraciones de modelos desde {config_path}: {e}. Usando valores por defecto.")
            return self._get_default_model_configs()
    
    def _get_default_model_configs(self) -> dict:
        """Define las configuraciones por defecto para los modelos conocidos."""
        return {
            "llama3.1:8b": {
                "options": {
                    "temperature": 0.15,  # Más creativo que 0.1 pero preciso
                    "top_p": 0.7,         # Reduce probabilidad de palabras menos probables
                    "top_k": 20,          # Limita muestreo a las 20 palabras más probables
                    "repeat_penalty": 1.1,# Penaliza repetición de tokens
                    "stop": ["```", "---", "<|eot_id|>", "<|end_of_text|>"]  # Tokens de parada específicos
                },
                "request_timeout": 180    # 3 minutos para Llama3.1:8b
            },
            "qwen3:32b": {
                "options": {
                    "temperature": 0.1,   # Muy bajo para máxima precisión
                    "top_p": 0.6,         # Más restrictivo para evitar divagaciones
                    "top_k": 15,          # Muestreo muy limitado
                    "repeat_penalty": 1.05,# Penalización ligera
                    "stop": ["```json", "</tool_code>", "<|im_end|>", "<|endoftext|>"]  # Tokens específicos Qwen
                },
                "request_timeout": 480    # 8 minutos para Qwen3:32b (modelo grande)
            },
            "deepseek-r1:32b": {
                "options": {
                    "temperature": 0.12,
                    "top_p": 0.65,
                    "top_k": 18,
                    "repeat_penalty": 1.08,
                    "stop": ["```", "---", "<|endofthought|>", "<|end|>"]
                },
                "request_timeout": 420    # 7 minutos para DeepSeek R1
            },
            "default": {
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "stop": []
                },
                "request_timeout": 120    # 2 minutos por defecto
            }
        }
    
    def _get_model_config(self, model_name: str) -> dict:
        """Obtiene la configuración para un modelo dado, con fallback a la configuración por defecto."""
        if model_name in self.model_configs:
            return self.model_configs[model_name]
        else:
            logging.getLogger(__name__).warning(f"⚠️ No hay configuración específica para el modelo '{model_name}', usando configuración por defecto.")
            return self.model_configs.get("default", self.model_configs["default"])
    
    def get_model_info(self, model_name: str = None) -> dict:
        """
        Obtiene información detallada sobre la configuración de un modelo.
        
        Args:
            model_name: Nombre del modelo (si no se especifica, usa el modelo actual)
        
        Returns:
            Dict con información de configuración del modelo
        """
        target_model = model_name or self.get_current_model()
        config = self._get_model_config(target_model)
        
        return {
            'model_name': target_model,
            'config': config,
            'is_optimized': target_model in self.model_configs and target_model != 'default',
            'timeout': config.get('request_timeout', 120),
            'temperature': config.get('options', {}).get('temperature', 0.7),
            'description': config.get('description', 'Sin descripción disponible')
        }
        
        
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
    
    def generate_casual_response(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        """
        Generar respuesta casual usando Ollama (sin planes ni herramientas)
        
        Args:
            prompt: Mensaje del usuario
            context: Contexto adicional (historial, etc.)
        
        Returns:
            Dict con respuesta casual y metadatos
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
            # Construir el prompt con system prompt para conversación casual
            system_prompt = self._build_system_prompt(use_tools=False, conversation_mode=True)
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
            
            # Para conversación casual, no parseamos tool calls, solo devolvemos el texto
            response_text = response.get('response', '').strip()
            
            return {
                'response': response_text,
                'tool_calls': [],
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
        """Hacer llamada real a la API de Ollama con parámetros optimizados"""
        try:
            # Detectar si es una solicitud de JSON estructurado
            is_json_request = 'JSON' in prompt or 'json' in prompt or '"steps"' in prompt
            
            payload = {
                "model": self.get_current_model(),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2 if is_json_request else 0.7,  # Más bajo para JSON
                    "top_p": 0.8 if is_json_request else 0.9,
                    "top_k": 20 if is_json_request else 40,
                    "repeat_penalty": 1.1,
                    "stop": ["```", "---"] if is_json_request else []  # Parar en marcadores comunes
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
        """
        Parsear respuesta para extraer texto y tool calls con estrategias robustas
        Mejora implementada según UPGRADE.md Sección 4: Servicio Ollama y Extracción de Query
        """
        import re
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        
        if not response_text or not isinstance(response_text, str):
            return {'text': '', 'tool_calls': []}
        
        tool_calls = []
        clean_text = response_text
        
        # Estrategia 1: Buscar bloques JSON clásicos con ``` 
        json_pattern_1 = r'```json\s*(\{.*?\})\s*```'
        matches_1 = re.findall(json_pattern_1, response_text, re.DOTALL)
        
        for match in matches_1:
            try:
                data = json.loads(match)
                if 'tool_call' in data:
                    tool_calls.append(data['tool_call'])
                    # Remover el bloque JSON del texto
                    clean_text = clean_text.replace(f'```json\n{match}\n```', '')
                    logger.debug(f"✅ JSON parsing strategy 1 successful: {match[:50]}...")
            except json.JSONDecodeError as e:
                logger.debug(f"⚠️ JSON parsing strategy 1 failed for match: {str(e)}")
                continue
        
        # Estrategia 2: Buscar JSON sin marcadores de bloque
        if not tool_calls:
            json_pattern_2 = r'\{[^{}]*"tool_call"[^{}]*\{[^{}]*\}[^{}]*\}'
            matches_2 = re.findall(json_pattern_2, response_text)
            
            for match in matches_2:
                try:
                    data = json.loads(match)
                    if 'tool_call' in data:
                        tool_calls.append(data['tool_call'])
                        clean_text = clean_text.replace(match, '')
                        logger.debug(f"✅ JSON parsing strategy 2 successful: {match[:50]}...")
                except json.JSONDecodeError as e:
                    logger.debug(f"⚠️ JSON parsing strategy 2 failed: {str(e)}")
                    continue
        
        # Estrategia 3: Buscar cualquier JSON válido y verificar si contiene tool_call
        if not tool_calls:
            json_pattern_3 = r'\{[^}]*\}'
            potential_jsons = re.findall(json_pattern_3, response_text)
            
            for potential_json in potential_jsons:
                try:
                    # Intentar corregir JSON mal formateado
                    corrected_json = potential_json.replace("'", '"')  # Comillas simples por dobles
                    data = json.loads(corrected_json)
                    
                    if isinstance(data, dict) and 'tool_call' in data:
                        tool_calls.append(data['tool_call'])
                        clean_text = clean_text.replace(potential_json, '')
                        logger.debug(f"✅ JSON parsing strategy 3 successful: {potential_json[:50]}...")
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"⚠️ JSON parsing strategy 3 failed for '{potential_json[:30]}...': {str(e)}")
                    continue
        
        # Estrategia 4: Extracción por regex específico de tool_call
        if not tool_calls:
            try:
                tool_pattern = r'"tool_call"\s*:\s*\{[^}]*"tool"\s*:\s*"([^"]+)"[^}]*"parameters"\s*:\s*\{[^}]*\}'
                tool_matches = re.finditer(tool_pattern, response_text)
                
                for tool_match in tool_matches:
                    try:
                        # Intentar construir tool_call básico desde regex
                        full_match = tool_match.group()
                        tool_name_match = re.search(r'"tool"\s*:\s*"([^"]+)"', full_match)
                        params_match = re.search(r'"parameters"\s*:\s*(\{[^}]*\})', full_match)
                        
                        if tool_name_match:
                            tool_call = {
                                "tool": tool_name_match.group(1),
                                "parameters": json.loads(params_match.group(1)) if params_match else {}
                            }
                            tool_calls.append(tool_call)
                            clean_text = clean_text.replace(tool_match.group(), '')
                            logger.debug(f"✅ JSON parsing strategy 4 successful for tool: {tool_call['tool']}")
                            
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.debug(f"⚠️ JSON parsing strategy 4 failed for tool extraction: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.debug(f"⚠️ JSON parsing strategy 4 overall failed: {str(e)}")
        
        # Limpiar texto final
        clean_text = re.sub(r'```\w*\n?', '', clean_text)  # Remover marcadores de código
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text)  # Remover líneas vacías múltiples
        clean_text = clean_text.strip()
        
        if tool_calls:
            logger.info(f"🔧 Successfully extracted {len(tool_calls)} tool calls from Ollama response")
        
        return {
            'text': clean_text,
            'tool_calls': tool_calls
        }
    
    def _build_system_prompt(self, use_tools: bool, conversation_mode: bool = False) -> str:
        """Construir prompt del sistema"""
        
        # Sistema prompt para conversación casual (sin planes ni herramientas)
        if conversation_mode:
            return """Eres un asistente de IA general llamado 'Agente General' que puede ayudar con una amplia variedad de tareas. 
Eres inteligente, útil y amigable.

IMPORTANTE: Estás en modo conversación casual. Responde de manera natural y amigable sin generar planes de acción ni mencionar herramientas.

NUNCA generes planes de acción en este modo.
NUNCA menciones herramientas disponibles.
NUNCA uses formatos estructurados como "**PLAN DE ACCIÓN:**"

Para conversaciones casuales:
- Saludos: Responde amigablemente y pregunta cómo puedes ayudar
- Preguntas sobre ti: Explica que eres un asistente de IA general
- Traducciones simples: Proporciona la traducción directamente
- Explicaciones: Da respuestas claras y concisas
- Preguntas de conocimiento: Responde con la información que tienes

Mantén las respuestas naturales, conversacionales y útiles.
Responde en español de manera clara y amigable."""
        
        # Sistema prompt para tareas (con planes y herramientas)
        base_prompt = """Eres un asistente de IA general llamado 'Agente General' que puede ayudar con una amplia variedad de tareas. 
Eres inteligente, útil y puedes usar herramientas para realizar acciones concretas.

IMPORTANTE: Estás en modo agente. Para tareas complejas, genera un PLAN DE ACCIÓN ESPECÍFICO y DETALLADO paso a paso.

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