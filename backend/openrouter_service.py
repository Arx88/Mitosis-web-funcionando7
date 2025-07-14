"""
Servicio de OpenRouter para el agente Mitosis
Proporciona acceso a múltiples modelos de lenguaje a través de la API de OpenRouter
"""

import requests
import json
import logging
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time

@dataclass
class OpenRouterModel:
    """Representa un modelo disponible en OpenRouter"""
    id: str
    name: str
    description: str
    pricing: Dict[str, float]
    context_length: int
    architecture: Dict[str, Any]
    top_provider: Dict[str, Any]
    per_request_limits: Optional[Dict[str, Any]] = None

class OpenRouterService:
    """Servicio para interactuar con OpenRouter"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.available_models: List[OpenRouterModel] = []
        self.app_name = "Mitosis-Agent"
        self.site_url = "https://github.com/mitosis-agent"
        
        if not self.api_key:
            self.logger.warning("No se encontró API key de OpenRouter. Algunas funciones no estarán disponibles.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene los headers necesarios para las solicitudes a OpenRouter"""
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def is_available(self) -> bool:
        """Verifica si OpenRouter está disponible"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"OpenRouter no está disponible: {e}")
            return False
    
    def fetch_models(self) -> List[OpenRouterModel]:
        """Obtiene la lista de modelos disponibles en OpenRouter"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self._get_headers(),
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_data in data.get('data', []):
                model = OpenRouterModel(
                    id=model_data.get('id', ''),
                    name=model_data.get('name', ''),
                    description=model_data.get('description', ''),
                    pricing=model_data.get('pricing', {}),
                    context_length=model_data.get('context_length', 0),
                    architecture=model_data.get('architecture', {}),
                    top_provider=model_data.get('top_provider', {}),
                    per_request_limits=model_data.get('per_request_limits')
                )
                models.append(model)
            
            self.available_models = models
            self.logger.info(f"Obtenidos {len(models)} modelos de OpenRouter")
            return models
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al obtener modelos de OpenRouter: {e}")
            return []
    
    def generate_response(self, prompt: str, model_id: str, 
                         max_tokens: int = 1000, temperature: float = 0.7,
                         stream: bool = False, **kwargs) -> Optional[str]:
        """Genera una respuesta usando un modelo específico de OpenRouter"""
        if not self.api_key:
            self.logger.error("API key de OpenRouter no configurada")
            return None
        
        try:
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            if stream:
                # Manejar respuesta en streaming
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        full_response += delta['content']
                            except json.JSONDecodeError:
                                continue
                return full_response
            else:
                # Respuesta completa
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al generar respuesta con {model_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error al decodificar respuesta JSON: {e}")
            return None
    
    def chat_completion(self, messages: List[Dict[str, str]], model_id: str,
                       max_tokens: int = 1000, temperature: float = 0.7,
                       **kwargs) -> Optional[str]:
        """Realiza una conversación usando el formato de chat"""
        if not self.api_key:
            self.logger.error("API key de OpenRouter no configurada")
            return None
        
        try:
            payload = {
                "model": model_id,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en chat completion con {model_id}: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Retorna una lista de IDs de modelos disponibles"""
        return [model.id for model in self.available_models]
    
    def get_model_details(self) -> List[Dict[str, Any]]:
        """Retorna detalles completos de todos los modelos disponibles"""
        return [
            {
                "id": model.id,
                "name": model.name,
                "description": model.description,
                "pricing": model.pricing,
                "context_length": model.context_length,
                "architecture": model.architecture,
                "top_provider": model.top_provider,
                "per_request_limits": model.per_request_limits
            }
            for model in self.available_models
        ]
    
    def find_models_by_criteria(self, 
                               max_cost_per_1k_tokens: Optional[float] = None,
                               min_context_length: Optional[int] = None,
                               provider: Optional[str] = None,
                               architecture_type: Optional[str] = None) -> List[OpenRouterModel]:
        """Encuentra modelos que cumplan con criterios específicos"""
        filtered_models = self.available_models.copy()
        
        if max_cost_per_1k_tokens is not None:
            filtered_models = [
                model for model in filtered_models
                if model.pricing.get('prompt', float('inf')) <= max_cost_per_1k_tokens
            ]
        
        if min_context_length is not None:
            filtered_models = [
                model for model in filtered_models
                if model.context_length >= min_context_length
            ]
        
        if provider is not None:
            filtered_models = [
                model for model in filtered_models
                if provider.lower() in model.top_provider.get('name', '').lower()
            ]
        
        if architecture_type is not None:
            filtered_models = [
                model for model in filtered_models
                if architecture_type.lower() in model.architecture.get('tokenizer', '').lower()
            ]
        
        return filtered_models
    
    def select_best_model(self, task_type: str = "general", 
                         budget_per_1k_tokens: float = 0.01) -> Optional[str]:
        """Selecciona el mejor modelo disponible para un tipo de tarea y presupuesto"""
        if not self.available_models:
            return None
        
        # Criterios de selección por tipo de tarea
        task_criteria = {
            "code": {
                "preferred_names": ["claude", "gpt-4", "codellama", "deepseek"],
                "min_context": 8000
            },
            "chat": {
                "preferred_names": ["gpt", "claude", "llama", "mistral"],
                "min_context": 4000
            },
            "general": {
                "preferred_names": ["gpt", "claude", "llama"],
                "min_context": 4000
            },
            "analysis": {
                "preferred_names": ["claude", "gpt-4", "gemini"],
                "min_context": 16000
            }
        }
        
        criteria = task_criteria.get(task_type, task_criteria["general"])
        
        # Filtrar por presupuesto y contexto mínimo
        suitable_models = self.find_models_by_criteria(
            max_cost_per_1k_tokens=budget_per_1k_tokens,
            min_context_length=criteria["min_context"]
        )
        
        if not suitable_models:
            # Si no hay modelos dentro del presupuesto, usar todos los disponibles
            suitable_models = self.available_models
        
        # Buscar modelos preferidos
        for preferred_name in criteria["preferred_names"]:
            for model in suitable_models:
                if preferred_name.lower() in model.name.lower():
                    return model.id
        
        # Si no se encuentra ningún modelo preferido, retornar el más barato
        if suitable_models:
            cheapest_model = min(
                suitable_models,
                key=lambda m: m.pricing.get('prompt', float('inf'))
            )
            return cheapest_model.id
        
        return None
    
    def get_model_cost_estimate(self, model_id: str, input_tokens: int, 
                               output_tokens: int) -> Optional[float]:
        """Estima el costo de usar un modelo específico"""
        model = next((m for m in self.available_models if m.id == model_id), None)
        if not model:
            return None
        
        prompt_cost = model.pricing.get('prompt', 0) * (input_tokens / 1000)
        completion_cost = model.pricing.get('completion', 0) * (output_tokens / 1000)
        
        return prompt_cost + completion_cost
    
    def health_check(self) -> Dict[str, Any]:
        """Realiza una verificación de salud del servicio OpenRouter"""
        health_status = {
            "service_available": False,
            "api_key_configured": bool(self.api_key),
            "models_fetched": 0,
            "last_check": time.time()
        }
        
        try:
            if self.is_available():
                health_status["service_available"] = True
                if self.api_key:
                    models = self.fetch_models()
                    health_status["models_fetched"] = len(models)
                    health_status["available_models"] = [m.id for m in models[:10]]  # Primeros 10
            
        except Exception as e:
            health_status["error"] = str(e)
            self.logger.error(f"Error en health check: {e}")
        
        return health_status

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear instancia del servicio
    openrouter = OpenRouterService()
    
    # Verificar disponibilidad
    if openrouter.is_available():
        print("✅ OpenRouter está disponible")
        
        if openrouter.api_key:
            # Obtener modelos
            models = openrouter.fetch_models()
            print(f"📦 Modelos obtenidos: {len(models)}")
            
            # Mostrar algunos modelos
            for model in models[:5]:
                cost = model.pricing.get('prompt', 0)
                print(f"  - {model.name} (${cost:.6f}/1k tokens)")
            
            # Seleccionar mejor modelo
            best_model = openrouter.select_best_model("general")
            print(f"🎯 Mejor modelo seleccionado: {best_model}")
            
            # Probar generación (solo si hay API key)
            if best_model:
                response = openrouter.generate_response(
                    "Hola, ¿cómo estás?", 
                    best_model,
                    max_tokens=50
                )
                if response:
                    print(f"🤖 Respuesta: {response}")
        else:
            print("⚠️ API key no configurada. Solo funciones de consulta disponibles.")
    else:
        print("❌ OpenRouter no está disponible")

