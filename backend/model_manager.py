"""
Gestor de Modelos para el agente Mitosis
Unifica el acceso a modelos de Ollama y OpenRouter
"""

import logging
from typing import List, Dict, Optional, Any, Union
from enum import Enum
import json
import time
from dataclasses import dataclass

from ollama_service import OllamaService, OllamaModel
from openrouter_service import OpenRouterService, OpenRouterModel

class ModelProvider(Enum):
    """Proveedores de modelos disponibles"""
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"

@dataclass
class UnifiedModel:
    """Representa un modelo unificado de cualquier proveedor"""
    id: str
    name: str
    provider: ModelProvider
    description: str = ""
    context_length: int = 0
    cost_per_1k_tokens: float = 0.0
    size_mb: float = 0.0
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []

class ModelManager:
    """Gestor unificado de modelos de lenguaje"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", 
                 openrouter_api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Inicializar servicios
        self.ollama_service = OllamaService(ollama_url)
        self.openrouter_service = OpenRouterService(openrouter_api_key)
        
        # Estado del gestor
        self.unified_models: List[UnifiedModel] = []
        self.current_model: Optional[UnifiedModel] = None
        self.last_refresh: Optional[float] = None
        
        # Configuración
        self.auto_fallback = True  # Cambiar automáticamente entre proveedores
        self.prefer_local = True   # Preferir modelos locales cuando sea posible
        
    def refresh_models(self) -> bool:
        """Actualiza la lista de modelos disponibles de todos los proveedores"""
        self.unified_models = []
        success = False
        
        # Obtener modelos de Ollama
        if self.ollama_service.is_available():
            try:
                ollama_models = self.ollama_service.detect_models()
                for model in ollama_models:
                    unified_model = UnifiedModel(
                        id=f"ollama:{model.name}",
                        name=model.name,
                        provider=ModelProvider.OLLAMA,
                        description=f"Modelo local de Ollama: {model.name}",
                        size_mb=round(model.size / (1024 * 1024), 2),
                        cost_per_1k_tokens=0.0,  # Modelos locales son gratuitos
                        capabilities=self._infer_capabilities(model.name)
                    )
                    self.unified_models.append(unified_model)
                
                self.logger.info(f"Cargados {len(ollama_models)} modelos de Ollama")
                success = True
                
            except Exception as e:
                self.logger.error(f"Error al cargar modelos de Ollama: {e}")
        
        # Obtener modelos de OpenRouter
        if self.openrouter_service.is_available() and self.openrouter_service.api_key:
            try:
                openrouter_models = self.openrouter_service.fetch_models()
                for model in openrouter_models:
                    unified_model = UnifiedModel(
                        id=f"openrouter:{model.id}",
                        name=model.name,
                        provider=ModelProvider.OPENROUTER,
                        description=model.description,
                        context_length=model.context_length,
                        cost_per_1k_tokens=model.pricing.get('prompt', 0.0),
                        capabilities=self._infer_capabilities(model.name)
                    )
                    self.unified_models.append(unified_model)
                
                self.logger.info(f"Cargados {len(openrouter_models)} modelos de OpenRouter")
                success = True
                
            except Exception as e:
                self.logger.error(f"Error al cargar modelos de OpenRouter: {e}")
        
        self.last_refresh = time.time()
        self.logger.info(f"Total de modelos unificados: {len(self.unified_models)}")
        
        return success
    
    def _infer_capabilities(self, model_name: str) -> List[str]:
        """Infiere las capacidades de un modelo basándose en su nombre"""
        capabilities = []
        name_lower = model_name.lower()
        
        # Capacidades de código
        if any(keyword in name_lower for keyword in ['code', 'coder', 'coding', 'starcoder', 'codellama']):
            capabilities.extend(['code_generation', 'code_analysis', 'debugging'])
        
        # Capacidades de chat
        if any(keyword in name_lower for keyword in ['chat', 'instruct', 'assistant']):
            capabilities.append('conversational')
        
        # Capacidades de análisis
        if any(keyword in name_lower for keyword in ['claude', 'gpt-4', 'gemini']):
            capabilities.extend(['analysis', 'reasoning', 'research'])
        
        # Capacidades multimodales
        if any(keyword in name_lower for keyword in ['vision', 'multimodal', 'gpt-4v']):
            capabilities.append('vision')
        
        # Capacidades de tamaño
        if any(keyword in name_lower for keyword in ['large', '70b', '65b', '175b']):
            capabilities.append('large_context')
        elif any(keyword in name_lower for keyword in ['small', '7b', '13b', 'tiny']):
            capabilities.append('efficient')
        
        # Capacidades generales por defecto
        if not capabilities:
            capabilities.append('general')
        
        return capabilities
    
    def get_available_models(self, provider: Optional[ModelProvider] = None) -> List[UnifiedModel]:
        """Obtiene la lista de modelos disponibles, opcionalmente filtrada por proveedor"""
        if provider:
            return [model for model in self.unified_models if model.provider == provider]
        return self.unified_models.copy()
    
    def find_models_by_capability(self, capability: str) -> List[UnifiedModel]:
        """Encuentra modelos que tengan una capacidad específica"""
        return [
            model for model in self.unified_models 
            if capability in model.capabilities
        ]
    
    def select_best_model(self, task_type: str = "general", 
                         max_cost: float = 0.01,
                         prefer_local: Optional[bool] = None) -> Optional[UnifiedModel]:
        """Selecciona el mejor modelo para una tarea específica"""
        if prefer_local is None:
            prefer_local = self.prefer_local
        
        # Mapear tipos de tarea a capacidades
        task_capabilities = {
            "code": ["code_generation", "code_analysis"],
            "chat": ["conversational"],
            "analysis": ["analysis", "reasoning"],
            "research": ["research", "analysis"],
            "general": ["general", "conversational"]
        }
        
        required_capabilities = task_capabilities.get(task_type, ["general"])
        
        # Encontrar modelos candidatos
        candidates = []
        for capability in required_capabilities:
            candidates.extend(self.find_models_by_capability(capability))
        
        # Si no hay candidatos específicos, usar todos los modelos
        if not candidates:
            candidates = self.unified_models
        
        # Filtrar por costo
        affordable_candidates = [
            model for model in candidates 
            if model.cost_per_1k_tokens <= max_cost
        ]
        
        if not affordable_candidates:
            affordable_candidates = candidates  # Si ninguno es asequible, usar todos
        
        # Aplicar preferencias de selección
        if prefer_local:
            # Preferir modelos locales primero
            local_models = [m for m in affordable_candidates if m.provider == ModelProvider.OLLAMA]
            if local_models:
                # Seleccionar el modelo local más grande (mejor calidad)
                return max(local_models, key=lambda m: m.size_mb)
            else:
                # Si no hay modelos locales, usar el más barato de OpenRouter
                openrouter_models = [m for m in affordable_candidates if m.provider == ModelProvider.OPENROUTER]
                if openrouter_models:
                    return min(openrouter_models, key=lambda m: m.cost_per_1k_tokens)
        else:
            # Preferir el modelo más barato independientemente del proveedor
            return min(affordable_candidates, key=lambda m: m.cost_per_1k_tokens)
        
        return None
    
    def load_model(self, model: Union[UnifiedModel, str]) -> bool:
        """Carga un modelo específico"""
        if isinstance(model, str):
            # Buscar el modelo por ID
            target_model = next((m for m in self.unified_models if m.id == model), None)
            if not target_model:
                self.logger.error(f"Modelo {model} no encontrado")
                return False
            model = target_model
        
        try:
            if model.provider == ModelProvider.OLLAMA:
                # Extraer el nombre real del modelo (sin el prefijo "ollama:")
                model_name = model.id.replace("ollama:", "")
                success = self.ollama_service.load_model(model_name)
                
            elif model.provider == ModelProvider.OPENROUTER:
                # OpenRouter no requiere carga previa, solo verificar disponibilidad
                success = self.openrouter_service.is_available()
                
            else:
                self.logger.error(f"Proveedor desconocido: {model.provider}")
                return False
            
            if success:
                self.current_model = model
                self.logger.info(f"Modelo cargado: {model.name} ({model.provider.value})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error al cargar modelo {model.name}: {e}")
            return False
    
    def generate_response(self, prompt: str, model: Optional[UnifiedModel] = None,
                         max_tokens: int = 1000, temperature: float = 0.7,
                         **kwargs) -> Optional[str]:
        """Genera una respuesta usando el modelo especificado o el actual"""
        target_model = model or self.current_model
        
        if not target_model:
            self.logger.error("No hay modelo especificado o cargado")
            return None
        
        try:
            if target_model.provider == ModelProvider.OLLAMA:
                model_name = target_model.id.replace("ollama:", "")
                # Convertir parámetros de OpenAI a formato Ollama
                ollama_options = {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
                return self.ollama_service.generate_response(
                    prompt, model_name, options=ollama_options
                )
                
            elif target_model.provider == ModelProvider.OPENROUTER:
                model_id = target_model.id.replace("openrouter:", "")
                return self.openrouter_service.generate_response(
                    prompt, model_id, max_tokens=max_tokens, 
                    temperature=temperature, **kwargs
                )
                
        except Exception as e:
            self.logger.error(f"Error al generar respuesta: {e}")
            
            # Intentar fallback si está habilitado
            if self.auto_fallback and target_model != self.current_model:
                self.logger.info("Intentando fallback con modelo alternativo")
                fallback_model = self.select_best_model()
                if fallback_model and fallback_model.id != target_model.id:
                    return self.generate_response(prompt, fallback_model, max_tokens, temperature, **kwargs)
        
        return None
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       model: Optional[UnifiedModel] = None,
                       max_tokens: int = 1000, temperature: float = 0.7,
                       **kwargs) -> Optional[str]:
        """Realiza una conversación usando el formato de chat"""
        target_model = model or self.current_model
        
        if not target_model:
            self.logger.error("No hay modelo especificado o cargado")
            return None
        
        try:
            if target_model.provider == ModelProvider.OLLAMA:
                model_name = target_model.id.replace("ollama:", "")
                ollama_options = {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
                return self.ollama_service.chat_completion(
                    messages, model_name, options=ollama_options
                )
                
            elif target_model.provider == ModelProvider.OPENROUTER:
                model_id = target_model.id.replace("openrouter:", "")
                return self.openrouter_service.chat_completion(
                    messages, model_id, max_tokens=max_tokens,
                    temperature=temperature, **kwargs
                )
                
        except Exception as e:
            self.logger.error(f"Error en chat completion: {e}")
            
            # Intentar fallback si está habilitado
            if self.auto_fallback and target_model != self.current_model:
                self.logger.info("Intentando fallback con modelo alternativo")
                fallback_model = self.select_best_model()
                if fallback_model and fallback_model.id != target_model.id:
                    return self.chat_completion(messages, fallback_model, max_tokens, temperature, **kwargs)
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del gestor de modelos"""
        return {
            "total_models": len(self.unified_models),
            "ollama_models": len([m for m in self.unified_models if m.provider == ModelProvider.OLLAMA]),
            "openrouter_models": len([m for m in self.unified_models if m.provider == ModelProvider.OPENROUTER]),
            "current_model": {
                "id": self.current_model.id,
                "name": self.current_model.name,
                "provider": self.current_model.provider.value
            } if self.current_model else None,
            "ollama_available": self.ollama_service.is_available(),
            "openrouter_available": self.openrouter_service.is_available(),
            "last_refresh": self.last_refresh,
            "settings": {
                "auto_fallback": self.auto_fallback,
                "prefer_local": self.prefer_local
            }
        }

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear gestor de modelos
    manager = ModelManager()
    
    # Actualizar lista de modelos
    if manager.refresh_models():
        print("✅ Modelos actualizados")
        
        # Mostrar estado
        status = manager.get_status()
        print(f"📊 Total de modelos: {status['total_models']}")
        print(f"🏠 Modelos locales (Ollama): {status['ollama_models']}")
        print(f"☁️ Modelos remotos (OpenRouter): {status['openrouter_models']}")
        
        # Seleccionar mejor modelo para código
        best_code_model = manager.select_best_model("code")
        if best_code_model:
            print(f"🎯 Mejor modelo para código: {best_code_model.name} ({best_code_model.provider.value})")
            
            # Cargar y probar el modelo
            if manager.load_model(best_code_model):
                response = manager.generate_response(
                    "Escribe una función en Python que calcule el factorial de un número",
                    max_tokens=200
                )
                if response:
                    print(f"🤖 Respuesta: {response[:100]}...")
    else:
        print("❌ Error al actualizar modelos")

