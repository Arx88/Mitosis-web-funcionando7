"""
Servicio de Ollama para el agente Mitosis
Proporciona integración con modelos de lenguaje locales a través de Ollama
"""

import requests
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time

@dataclass
class OllamaModel:
    """Representa un modelo de Ollama disponible"""
    name: str
    size: int
    digest: str
    modified_at: str
    details: Dict[str, Any]

class OllamaService:
    """Servicio para interactuar con Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.available_models: List[OllamaModel] = []
        self.current_model: Optional[str] = None
        
    def is_available(self) -> bool:
        """Verifica si Ollama está disponible y funcionando"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Ollama no está disponible: {e}")
            return False
    
    def detect_models(self) -> List[OllamaModel]:
        """Detecta automáticamente todos los modelos de Ollama instalados"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_data in data.get('models', []):
                model = OllamaModel(
                    name=model_data.get('name', ''),
                    size=model_data.get('size', 0),
                    digest=model_data.get('digest', ''),
                    modified_at=model_data.get('modified_at', ''),
                    details=model_data.get('details', {})
                )
                models.append(model)
            
            self.available_models = models
            self.logger.info(f"Detectados {len(models)} modelos de Ollama: {[m.name for m in models]}")
            return models
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al detectar modelos de Ollama: {e}")
            return []
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene información detallada de un modelo específico"""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al obtener información del modelo {model_name}: {e}")
            return None
    
    def load_model(self, model_name: str) -> bool:
        """Carga un modelo específico en memoria"""
        try:
            # Verificar que el modelo existe
            if not any(model.name == model_name for model in self.available_models):
                self.logger.error(f"Modelo {model_name} no encontrado en la lista de modelos disponibles")
                return False
            
            # Cargar el modelo haciendo una solicitud simple
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "Hello",
                    "stream": False,
                    "options": {"num_predict": 1}
                },
                timeout=30
            )
            response.raise_for_status()
            
            self.current_model = model_name
            self.logger.info(f"Modelo {model_name} cargado exitosamente")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al cargar el modelo {model_name}: {e}")
            return False
    
    def generate_response(self, prompt: str, model_name: Optional[str] = None, 
                         stream: bool = False, options: Optional[Dict] = None) -> Optional[str]:
        """Genera una respuesta usando el modelo especificado"""
        target_model = model_name or self.current_model
        
        if not target_model:
            self.logger.error("No hay modelo especificado o cargado")
            return None
        
        try:
            payload = {
                "model": target_model,
                "prompt": prompt,
                "stream": stream
            }
            
            if options:
                payload["options"] = options
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            if stream:
                # Manejar respuesta en streaming
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        if 'response' in data:
                            full_response += data['response']
                        if data.get('done', False):
                            break
                return full_response
            else:
                # Respuesta completa
                data = response.json()
                return data.get('response', '')
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al generar respuesta con {target_model}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error al decodificar respuesta JSON: {e}")
            return None
    
    def chat_completion(self, messages: List[Dict[str, str]], model_name: Optional[str] = None,
                       options: Optional[Dict] = None) -> Optional[str]:
        """Realiza una conversación usando el formato de chat"""
        target_model = model_name or self.current_model
        
        if not target_model:
            self.logger.error("No hay modelo especificado o cargado")
            return None
        
        try:
            payload = {
                "model": target_model,
                "messages": messages,
                "stream": False
            }
            
            if options:
                payload["options"] = options
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('message', {}).get('content', '')
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en chat completion con {target_model}: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Retorna una lista de nombres de modelos disponibles"""
        return [model.name for model in self.available_models]
    
    def get_model_details(self) -> List[Dict[str, Any]]:
        """Retorna detalles completos de todos los modelos disponibles"""
        return [
            {
                "name": model.name,
                "size": model.size,
                "size_mb": round(model.size / (1024 * 1024), 2),
                "digest": model.digest,
                "modified_at": model.modified_at,
                "details": model.details
            }
            for model in self.available_models
        ]
    
    def select_best_model(self, task_type: str = "general") -> Optional[str]:
        """Selecciona el mejor modelo disponible para un tipo de tarea específico"""
        if not self.available_models:
            return None
        
        # Lógica simple de selección basada en el nombre del modelo
        # Esto se puede expandir con más criterios sofisticados
        model_preferences = {
            "code": ["codellama", "deepseek-coder", "starcoder"],
            "chat": ["llama", "mistral", "gemma"],
            "general": ["llama", "mistral", "gemma", "qwen"],
            "small": ["phi", "tinyllama", "gemma:2b"]
        }
        
        preferred_models = model_preferences.get(task_type, model_preferences["general"])
        available_names = [model.name.lower() for model in self.available_models]
        
        # Buscar el primer modelo preferido que esté disponible
        for preferred in preferred_models:
            for available_name in available_names:
                if preferred in available_name:
                    # Encontrar el modelo original con el nombre exacto
                    for model in self.available_models:
                        if model.name.lower() == available_name:
                            return model.name
        
        # Si no se encuentra ningún modelo preferido, retornar el primero disponible
        return self.available_models[0].name if self.available_models else None
    
    def health_check(self) -> Dict[str, Any]:
        """Realiza una verificación de salud del servicio Ollama"""
        health_status = {
            "service_available": False,
            "models_detected": 0,
            "current_model": self.current_model,
            "last_check": time.time()
        }
        
        try:
            if self.is_available():
                health_status["service_available"] = True
                models = self.detect_models()
                health_status["models_detected"] = len(models)
                health_status["available_models"] = [m.name for m in models]
            
        except Exception as e:
            health_status["error"] = str(e)
            self.logger.error(f"Error en health check: {e}")
        
        return health_status

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear instancia del servicio
    ollama = OllamaService()
    
    # Verificar disponibilidad
    if ollama.is_available():
        print("✅ Ollama está disponible")
        
        # Detectar modelos
        models = ollama.detect_models()
        print(f"📦 Modelos detectados: {len(models)}")
        
        for model in models:
            print(f"  - {model.name} ({model.size_mb:.1f} MB)")
        
        # Seleccionar y cargar un modelo
        if models:
            best_model = ollama.select_best_model("general")
            print(f"🎯 Mejor modelo seleccionado: {best_model}")
            
            if ollama.load_model(best_model):
                print(f"✅ Modelo {best_model} cargado")
                
                # Probar generación
                response = ollama.generate_response("Hola, ¿cómo estás?")
                if response:
                    print(f"🤖 Respuesta: {response}")
    else:
        print("❌ Ollama no está disponible")

