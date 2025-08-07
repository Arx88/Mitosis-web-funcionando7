"""
Servicio de integración con Ollama - Versión con Cola de Concurrencia
Conecta directamente con Ollama para generar respuestas, usando un sistema
de cola para gestionar llamadas concurrentes y evitar saturación.

🔄 NUEVA FUNCIONALIDAD: Sistema de Cola de Concurrencia
- Integración transparente con OllamaQueueManager
- Control automático de llamadas concurrentes
- Priorización inteligente de requests
- Métricas de rendimiento y monitoreo
"""

import json
import time
import os
import logging
import asyncio
import concurrent.futures
import threading
from typing import Dict, List, Optional, Any
import requests
from requests.exceptions import RequestException, Timeout

# Importar configuración centralizada
from ..config.ollama_config import get_ollama_config, get_ollama_endpoint, get_ollama_model

# 🚦 IMPORTACIÓN DEL GESTOR DE COLA
from .ollama_queue_manager import (
    OllamaQueueManager, 
    OllamaRequest, 
    RequestPriority,
    get_ollama_queue_manager
)

class OllamaService:
    def __init__(self, base_url: str = None):
        # Usar configuración centralizada
        self.ollama_config = get_ollama_config()
        self.base_url = base_url or self.ollama_config.endpoint
        self.default_model = self.ollama_config.model
        self.current_model = None
        self.conversation_history = []
        self.request_timeout = self.ollama_config.timeout
        
        # 🆕 PROBLEMA 3: Configuración de parámetros por modelo
        self.model_configs = self._load_model_configs()
        
        # 🚦 INTEGRACIÓN CON GESTOR DE COLA
        self.use_queue = os.getenv('OLLAMA_USE_QUEUE', 'true').lower() == 'true'
        self._queue_manager = None  # Se inicializará lazy
        
        # Logging específico para cola
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if self.use_queue:
            self.logger.info("🚦 OllamaService configurado con sistema de cola activado")
        else:
            self.logger.warning("⚠️ OllamaService configurado SIN sistema de cola - pueden ocurrir problemas de concurrencia")
    
    def _get_queue_manager(self) -> Optional[OllamaQueueManager]:
        """
        🚦 OBTENER GESTOR DE COLA (LAZY LOADING)
        
        Inicializa el gestor de cola solo cuando es necesario
        """
        if not self.use_queue:
            return None
            
        if self._queue_manager is None:
            try:
                self._queue_manager = get_ollama_queue_manager()
                self.logger.info("🚦 Gestor de cola Ollama obtenido exitosamente")
            except Exception as e:
                self.logger.error(f"❌ Error obteniendo gestor de cola: {str(e)}")
                return None
                
        return self._queue_manager
    
    async def _execute_with_queue(self, 
                                 prompt: str, 
                                 model: str, 
                                 options: Dict[str, Any],
                                 priority: RequestPriority = RequestPriority.NORMAL,
                                 task_id: str = "",
                                 step_id: str = "") -> Dict[str, Any]:
        """
        🚦 EJECUTAR LLAMADA A OLLAMA A TRAVÉS DE LA COLA
        
        Encapsula la llamada a Ollama dentro del sistema de cola para
        controlar la concurrencia automáticamente.
        
        Args:
            prompt: Prompt para Ollama
            model: Modelo a utilizar
            options: Opciones de generación
            priority: Prioridad del request
            task_id: ID de la tarea (para tracking)
            step_id: ID del paso (para tracking)
            
        Returns:
            Resultado de Ollama o error
        """
        queue_manager = self._get_queue_manager()
        if not queue_manager:
            self.logger.warning("⚠️ Gestor de cola no disponible, ejecutando llamada directa")
            return await self._execute_direct_call(prompt, model, options)
        
        # Crear request para la cola
        ollama_request = OllamaRequest(
            task_id=task_id,
            step_id=step_id,
            prompt=prompt,
            model=model,
            options=options,
            priority=priority,
            timeout=self._get_model_config(model).get("request_timeout", 180)
        )
        
        self.logger.info(f"🚦 Encolando request para modelo {model} (tarea: {task_id}, prioridad: {priority.name})")
        
        # Función callback que ejecuta la llamada real
        async def execution_callback(request: OllamaRequest) -> Dict[str, Any]:
            return await self._execute_direct_call(request.prompt, request.model, request.options)
        
        # Ejecutar a través de la cola
        try:
            result = await queue_manager.enqueue_request(ollama_request, execution_callback)
            
            # Log resultado
            if 'error' in result:
                self.logger.error(f"❌ Request {ollama_request.request_id} falló: {result.get('error')}")
            else:
                self.logger.info(f"✅ Request {ollama_request.request_id} completado exitosamente")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error en cola de Ollama: {str(e)}")
            return {'error': str(e), 'error_type': 'queue_system_error'}
    
    async def _execute_direct_call(self, 
                                  prompt: str, 
                                  model: str, 
                                  options: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔧 EJECUTAR LLAMADA DIRECTA A OLLAMA (SIN COLA)
        
        Versión async de _call_ollama_api para uso dentro del sistema de cola.
        Mantiene la misma lógica pero adaptada para async/await.
        """
        try:
            # Usar la lógica existente pero adaptada para async
            loop = asyncio.get_event_loop()
            
            # Ejecutar la llamada en un thread pool para no bloquear
            result = await loop.run_in_executor(
                None, 
                self._call_ollama_api_sync, 
                prompt, 
                model, 
                options
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error en llamada directa a Ollama: {str(e)}")
            return {'error': str(e), 'error_type': 'direct_call_error'}
    
    def _call_ollama_api_sync(self, prompt: str, model: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔧 VERSIÓN SINCRÓNICA DE LA LLAMADA A OLLAMA
        
        Esta es la implementación original adaptada para ser llamada desde async
        """
        try:
            model_config = self._get_model_config(model)
            request_timeout = model_config.get("request_timeout", self.request_timeout)
            
            # Detectar si es una solicitud JSON y ajustar parámetros específicamente
            is_json_request = any(keyword in prompt.lower() for keyword in ['json', '"steps"', 'genera un plan', 'plan de acción'])
            
            final_options = options.copy()
            if is_json_request:
                # Para solicitudes JSON, usar parámetros más estrictos
                final_options['temperature'] = min(final_options.get('temperature', 0.7) * 0.5, 0.1)
                final_options['top_p'] = min(final_options.get('top_p', 0.9) * 0.8, 0.7)
                
                # Agregar stops específicos para JSON si no están
                current_stops = final_options.get('stop', [])
                json_stops = ['```', '---', '}```', '}\n```']
                final_options['stop'] = list(set(current_stops + json_stops))
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": final_options
            }
            
            # Logging detallado para debug
            self.logger.debug(f"🤖 Ollama Request - Model: {model}")
            self.logger.debug(f"⚙️ Options: temp={final_options.get('temperature')}, timeout={request_timeout}s")
            if is_json_request:
                self.logger.debug(f"📋 JSON mode detected, using strict parameters")
            
            # Headers necesarios para ngrok
            headers = {
                'Content-Type': 'application/json'
            }
            # Agregar header ngrok si el endpoint es ngrok
            if 'ngrok' in self.base_url:
                headers['ngrok-skip-browser-warning'] = 'true'
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers=headers,
                timeout=min(request_timeout, 180)  # Máximo 3 minutos para evitar cuelgues
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"❌ Ollama API returned error for model {model}: HTTP {response.status_code}")
                return {
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Timeout:
            self.logger.error(f"⏱️ Ollama API request timed out after {request_timeout} seconds for model {model}.")
            return {
                'error': f"Timeout después de {request_timeout} segundos para el modelo {model}. El modelo puede necesitar más tiempo para respuestas complejas."
            }
        except RequestException as e:
            self.logger.error(f"🔌 Connection error to Ollama API for model {model}: {str(e)}")
            return {
                'error': f"Error de conexión: {str(e)}"
            }
        except Exception as e:
            self.logger.error(f"💥 Unexpected error in Ollama API call for model {model}: {str(e)}")
            return {
                'error': f"Error inesperado: {str(e)}"
            }
    
    def update_endpoint(self, new_endpoint: str) -> bool:
        """
        Actualiza el endpoint de Ollama dinámicamente
        """
        try:
            old_endpoint = self.base_url
            self.base_url = new_endpoint
            
            # Verificar que el nuevo endpoint funciona
            if self.is_healthy():
                logging.getLogger(__name__).info(f"✅ Ollama endpoint updated: {old_endpoint} → {new_endpoint}")
                return True
            else:
                # Revertir si no funciona
                self.base_url = old_endpoint
                logging.getLogger(__name__).error(f"❌ Failed to update Ollama endpoint to {new_endpoint}, reverted to {old_endpoint}")
                return False
                
        except Exception as e:
            logging.getLogger(__name__).error(f"❌ Error updating Ollama endpoint: {str(e)}")
            return False
    
    def get_endpoint_info(self) -> dict:
        """Obtiene información completa del endpoint actual"""
        try:
            return {
                'endpoint': self.base_url,
                'current_model': self.get_current_model(),
                'is_healthy': self.is_healthy(),
                'available_models': self.get_available_models(),
                'connection_info': self.check_connection()
            }
        except Exception as e:
            return {
                'endpoint': self.base_url,
                'error': str(e),
                'is_healthy': False
            }
        
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
            headers = {}
            if 'ngrok' in self.base_url:
                headers['ngrok-skip-browser-warning'] = 'true'
            
            response = requests.get(f"{self.base_url}/api/tags", timeout=5, headers=headers)
            return response.status_code == 200
        except:
            return False
    
    def is_available(self) -> bool:
        """Verificar si Ollama está disponible y no está ocupado procesando otra tarea"""
        if not self.is_healthy():
            return False
        
        # Verificar si hay requests activos en el queue manager
        queue_manager = self._get_queue_manager()
        if queue_manager:
            try:
                # Si hay tareas en proceso o en cola, no está disponible
                active_requests = queue_manager.get_active_requests_count()
                queued_requests = queue_manager.get_queue_size()
                
                self.logger.info(f"🚦 Ollama availability check: {active_requests} active, {queued_requests} queued")
                
                # Disponible solo si no hay tareas activas y pocas en cola
                return active_requests == 0 and queued_requests <= 1
                
            except Exception as e:
                self.logger.error(f"❌ Error checking Ollama availability: {e}")
                # En caso de error, asumir no disponible por seguridad
                return False
        else:
            # Sin gestor de cola, usar check simple
            return True
    
    def check_connection(self) -> Dict[str, Any]:
        """Verificar conexión con Ollama y retornar información detallada"""
        try:
            headers = {}
            if 'ngrok' in self.base_url:
                headers['ngrok-skip-browser-warning'] = 'true'
            
            response = requests.get(f"{self.base_url}/api/tags", timeout=5, headers=headers)
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
            headers = {}
            if 'ngrok' in self.base_url:
                headers['ngrok-skip-browser-warning'] = 'true'
            
            response = requests.get(f"{self.base_url}/api/tags", timeout=5, headers=headers)
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
        """Establecer el modelo a usar - FORZAR sin validación de disponibilidad"""
        # 🚀 FIX CRÍTICO: Permitir cambio de modelo sin validar disponibilidad
        # porque el frontend puede enviar modelos válidos que no aparecen en la lista
        self.current_model = model_name
        logger = logging.getLogger(__name__)
        logger.info(f"🔄 Modelo forzado a: {model_name}")
        return True
    
    def set_model_with_validation(self, model_name: str) -> bool:
        """Establecer el modelo a usar CON validación de disponibilidad"""
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
        🔄 GENERAR RESPUESTA CASUAL CON COLA OPCIONAL
        
        Genera respuesta casual usando Ollama (sin planes ni herramientas),
        utilizando el sistema de cola si está habilitado.
        
        Args:
            prompt: Mensaje del usuario
            context: Contexto adicional (historial, etc.)
        
        Returns:
            Dict con respuesta casual y metadatos
        """
        if not self.is_healthy():
            return {
                'response': "⚠️ Ollama no está disponible en este momento. Verifica la configuración del endpoint de Ollama.",
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
            
            # Determinar si usar cola o llamada directa
            if self.use_queue:
                # Detectar si estamos en eventlet y usar llamada directa como fallback
                try:
                    import threading
                    current_thread = threading.current_thread()
                    if hasattr(current_thread, 'name') and 'GreenThread' in current_thread.name:
                        # En eventlet, usar llamada directa
                        self.logger.warning("⚠️ Detectado GreenThread, usando llamada directa")
                        response = self._call_ollama_api(full_prompt)
                    else:
                        # Usar cola con prioridad normal para conversaciones casuales
                        def run_async():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(self._execute_with_queue(
                                    prompt=full_prompt,
                                    model=self.get_current_model(),
                                    options=self._get_model_config(self.get_current_model()).get("options", {}),
                                    priority=RequestPriority.LOW,
                                    task_id="casual_conversation",
                                    step_id="casual_response"
                                ))
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async)
                            response = future.result(timeout=30)
                except Exception as e:
                    self.logger.error(f"❌ Error en execute con cola: {e}")
                    # Fallback a llamada directa
                    response = self._call_ollama_api(full_prompt)
            else:
                # Llamada directa tradicional
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
                'timestamp': time.time(),
                'used_queue': self.use_queue
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

    def generate_response(self, prompt: str, context: Dict = None, use_tools: bool = True, task_id: str = "", step_id: str = "") -> Dict[str, Any]:
        """
        🔄 GENERAR RESPUESTA CON COLA Y PRIORIZACIÓN INTELIGENTE
        
        Genera respuesta usando Ollama, con control automático de cola
        y priorización basada en el tipo de contenido.
        
        Args:
            prompt: Mensaje del usuario
            context: Contexto adicional (historial, herramientas, etc.)
            use_tools: Si debe considerar el uso de herramientas
            task_id: ID de la tarea (para tracking y priorización)
            step_id: ID del paso (para tracking)
        
        Returns:
            Dict con respuesta, tool_calls, y metadatos incluyendo info de cola
        """
        if not self.is_healthy():
            return {
                'response': "⚠️ Ollama no está disponible en este momento. Verifica la configuración del endpoint de Ollama.",
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
            
            # 🔍 DETERMINAR PRIORIDAD AUTOMÁTICAMENTE
            priority = self._determine_request_priority(prompt, context, task_id, step_id)
            
            # Determinar si usar cola o llamada directa
            if self.use_queue:
                # Detectar si estamos en eventlet y usar llamada directa como fallback
                try:
                    import threading
                    current_thread = threading.current_thread()
                    if hasattr(current_thread, 'name') and 'GreenThread' in current_thread.name:
                        # En eventlet, usar llamada directa
                        self.logger.warning("⚠️ Detectado GreenThread, usando llamada directa")
                        response = self._call_ollama_api(full_prompt)
                    else:
                        # Usar cola con prioridad determinada automáticamente
                        def run_async():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(self._execute_with_queue(
                                    prompt=full_prompt,
                                    model=self.get_current_model(),
                                    options=self._get_model_config(self.get_current_model()).get("options", {}),
                                    priority=priority,
                                    task_id=task_id or "unknown_task",
                                    step_id=step_id or "unknown_step"
                                ))
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async)
                            response = future.result(timeout=60)
                except Exception as e:
                    self.logger.error(f"❌ Error en execute con cola: {e}")
                    # Fallback a llamada directa
                    response = self._call_ollama_api(full_prompt)
                
                self.logger.info(f"🚦 Request procesado a través de cola (prioridad: {priority.name})")
                
            else:
                # Llamada directa tradicional (sin cola)
                response = self._call_ollama_api(full_prompt)
                self.logger.warning("⚠️ Request procesado SIN cola - riesgo de problemas de concurrencia")
            
            if response.get('error'):
                return {
                    'response': f"❌ Error al generar respuesta: {response['error']}",
                    'tool_calls': [],
                    'raw_response': "",
                    'model': self.get_current_model(),
                    'timestamp': time.time(),
                    'error': response['error'],
                    'used_queue': self.use_queue,
                    'priority': priority.name if self.use_queue else 'none'
                }
            
            # Parsear la respuesta
            parsed_response = self._parse_response(response.get('response', ''))
            
            return {
                'response': parsed_response['text'],
                'tool_calls': parsed_response['tool_calls'],
                'raw_response': response.get('response', ''),
                'model': self.get_current_model(),
                'timestamp': time.time(),
                'used_queue': self.use_queue,
                'priority': priority.name if self.use_queue else 'none'
            }
            
        except Exception as e:
            return {
                'response': f"❌ Error interno: {str(e)}",
                'tool_calls': [],
                'raw_response': "",
                'model': self.get_current_model(),
                'timestamp': time.time(),
                'error': str(e),
                'used_queue': self.use_queue
            }
    
    def _determine_request_priority(self, prompt: str, context: Dict, task_id: str, step_id: str) -> RequestPriority:
        """
        🔍 DETERMINAR PRIORIDAD DE REQUEST AUTOMÁTICAMENTE
        
        Analiza el contenido del prompt y contexto para asignar
        la prioridad apropiada al request.
        
        Args:
            prompt: Contenido del prompt
            context: Contexto adicional
            task_id: ID de la tarea
            step_id: ID del paso
            
        Returns:
            Prioridad apropiada para el request
        """
        prompt_lower = prompt.lower()
        
        # 🚨 CRÍTICO: Generación de planes iniciales
        if any(keyword in prompt_lower for keyword in ['genera un plan', 'plan de acción', 'create_dynamic_plan']):
            return RequestPriority.CRITICAL
        
        # 🔴 ALTA: Recuperación de errores o reintentos
        if any(keyword in prompt_lower for keyword in ['error', 'falló', 'reintento', 'retry', 'recuperación']):
            return RequestPriority.HIGH
        
        # 🔴 ALTA: Análisis o decisiones importantes
        if any(keyword in prompt_lower for keyword in ['analizar', 'decidir', 'evaluar', 'importante', 'crítico']):
            return RequestPriority.HIGH
        
        # 🟠 NORMAL: Ejecución de pasos de plan
        if step_id and step_id != "unknown_step":
            return RequestPriority.NORMAL
        
        # 🟡 BAJA: Conversaciones casuales o consultas generales
        if any(keyword in prompt_lower for keyword in ['hola', 'saludo', 'información', 'explicar']):
            return RequestPriority.LOW
        
        # Por defecto: NORMAL
        return RequestPriority.NORMAL
    
    def _call_ollama_api(self, prompt: str, custom_options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        🔧 HACER LLAMADA A API DE OLLAMA (COMPATIBILIDAD)
        
        Método de compatibilidad que redirige a la implementación
        sincrónica para mantener el código existente funcionando.
        
        NOTA: Este método se mantiene para compatibilidad, pero se
        recomienda usar generate_response() que incluye el sistema de cola.
        """
        try:
            current_model_name = self.get_current_model()
            model_config = self._get_model_config(current_model_name)
            
            # Obtener opciones base del modelo
            model_options = model_config.get("options", {}).copy()
            
            # Fusionar con opciones personalizadas si se proporcionan
            if custom_options:
                model_options.update(custom_options)
            
            # Usar la implementación sincrónica
            return self._call_ollama_api_sync(prompt, current_model_name, model_options)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"💥 Error en _call_ollama_api: {str(e)}")
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
1. **web_search** - Buscar información en internet
2. **analysis** - Realizar análisis de datos e información
3. **creation** - Crear contenido, documentos o código
4. **planning** - Planificación y organización de tareas
5. **delivery** - Entrega y presentación de resultados
6. **processing** - Procesamiento general de información
7. **synthesis** - Síntesis y resumen de información
8. **research** - Investigación detallada
9. **investigation** - Investigación específica
10. **shell** - Ejecutar comandos de terminal
11. **search_definition** - Búsqueda de definiciones
12. **data_analysis** - Análisis específico de datos
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
            
            # Headers necesarios para ngrok
            headers = {
                'Content-Type': 'application/json'
            }
            if 'ngrok' in self.base_url:
                headers['ngrok-skip-browser-warning'] = 'true'
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers=headers,
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