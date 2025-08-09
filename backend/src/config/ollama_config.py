"""
🔧 CONFIGURACIÓN CENTRALIZADA DE OLLAMA
Gestiona toda la configuración de Ollama desde un solo lugar
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class OllamaConfig:
    """Configuración centralizada de Ollama"""
    
    _instance = None
    _config_file = Path(__file__).parent / "ollama_runtime_config.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración desde archivo .env y runtime config"""
        
        # 1. Configuración BASE desde .env (valores por defecto)
        self._base_config = {
            "endpoint": os.getenv('OLLAMA_BASE_URL', 'https://277e85fec6fd.ngrok-free.app'),
            "default_model": os.getenv('OLLAMA_DEFAULT_MODEL', 'gpt-oss:20b'),
            "host": os.getenv('OLLAMA_HOST', '277e85fec6fd.ngrok-free.app'),
            "port": int(os.getenv('OLLAMA_PORT', '443')),
            "timeout": int(os.getenv('OLLAMA_TIMEOUT', '180'))
        }
        
        # 2. Configuración RUNTIME (se puede cambiar desde UI)
        self._runtime_config = self._load_runtime_config()
        
    def _load_runtime_config(self) -> Dict[str, Any]:
        """Cargar configuración runtime desde archivo JSON"""
        try:
            if self._config_file.exists():
                with open(self._config_file, 'r') as f:
                    config = json.load(f)
                    logger.info(f"✅ Runtime config loaded: {config}")
                    return config
        except Exception as e:
            logger.warning(f"⚠️ Could not load runtime config: {e}")
        
        return {}
    
    def _save_runtime_config(self):
        """Guardar configuración runtime"""
        try:
            os.makedirs(self._config_file.parent, exist_ok=True)
            with open(self._config_file, 'w') as f:
                json.dump(self._runtime_config, f, indent=2)
            logger.info(f"✅ Runtime config saved: {self._runtime_config}")
        except Exception as e:
            logger.error(f"❌ Could not save runtime config: {e}")
    
    @property
    def endpoint(self) -> str:
        """Endpoint de Ollama (runtime override sobre base)"""
        return self._runtime_config.get('endpoint', self._base_config['endpoint'])
    
    @endpoint.setter
    def endpoint(self, value: str):
        """Establecer nuevo endpoint"""
        self._runtime_config['endpoint'] = value
        self._save_runtime_config()
        logger.info(f"🔄 Ollama endpoint updated to: {value}")
    
    @property
    def model(self) -> str:
        """Modelo actual de Ollama (runtime override sobre base)"""
        return self._runtime_config.get('model', self._base_config['default_model'])
    
    @model.setter
    def model(self, value: str):
        """Establecer nuevo modelo"""
        self._runtime_config['model'] = value
        self._save_runtime_config()
        logger.info(f"🔄 Ollama model updated to: {value}")
    
    @property
    def host(self) -> str:
        """Host de Ollama"""
        return self._runtime_config.get('host', self._base_config['host'])
    
    @property
    def port(self) -> int:
        """Puerto de Ollama"""
        return self._runtime_config.get('port', self._base_config['port'])
    
    @property
    def timeout(self) -> int:
        """Timeout de requests"""
        return self._runtime_config.get('timeout', self._base_config['timeout'])
    
    def get_full_config(self) -> Dict[str, Any]:
        """Obtener configuración completa"""
        return {
            'endpoint': self.endpoint,
            'model': self.model,
            'host': self.host,
            'port': self.port,
            'timeout': self.timeout,
            'base_config': self._base_config,
            'runtime_overrides': self._runtime_config
        }
    
    def update_config(self, **kwargs):
        """Actualizar múltiples valores de configuración"""
        updated = []
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                updated.append(f"{key}={value}")
        
        if updated:
            logger.info(f"🔄 Ollama config updated: {', '.join(updated)}")
    
    def reset_to_defaults(self):
        """Resetear configuración a valores por defecto"""
        self._runtime_config = {}
        self._save_runtime_config()
        logger.info("🔄 Ollama config reset to defaults")

# Instancia global singleton
_ollama_config = None

def get_ollama_config() -> OllamaConfig:
    """Obtener instancia singleton de configuración"""
    global _ollama_config
    if _ollama_config is None:
        _ollama_config = OllamaConfig()
    return _ollama_config

def get_ollama_endpoint() -> str:
    """Función de conveniencia para obtener endpoint"""
    return get_ollama_config().endpoint

def get_ollama_model() -> str:
    """Función de conveniencia para obtener modelo"""
    return get_ollama_config().model

def set_ollama_endpoint(endpoint: str):
    """Función de conveniencia para establecer endpoint"""
    get_ollama_config().endpoint = endpoint

def set_ollama_model(model: str):
    """Función de conveniencia para establecer modelo"""
    get_ollama_config().model = model