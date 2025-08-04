"""
Wrapper para integrar OllamaService de Mitosis con browser-use
Implementa el protocolo BaseChatModel requerido por browser-use
"""

import asyncio
import logging
from typing import List, Union, Optional, Any, Type
from dataclasses import dataclass

# Importaciones de browser-use
from browser_use.llm.base import BaseChatModel
from browser_use.llm.messages import UserMessage, SystemMessage, AssistantMessage, BaseMessage
from browser_use.llm.views import ChatInvokeCompletion

# Importación del OllamaService de Mitosis
try:
    from ..services.ollama_service import OllamaService
except ImportError:
    # Fallback para cuando se importa directamente
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from services.ollama_service import OllamaService

logger = logging.getLogger(__name__)


@dataclass
class MitosisOllamaChatModel(BaseChatModel):
    """
    Wrapper que adapta OllamaService de Mitosis para browser-use
    Implementa el protocolo BaseChatModel requerido por browser-use
    """
    
    model: str = "llama3.1:8b"
    host: str = "https://66bd0d09b557.ngrok-free.app"
    ollama_service: Optional[OllamaService] = None
    
    def __post_init__(self):
        """Inicializar OllamaService después de la creación del dataclass"""
        if self.ollama_service is None:
            self.ollama_service = OllamaService(base_url=self.host)
        logger.info(f"🤖 MitosisOllamaChatModel inicializado - Model: {self.model}, Host: {self.host}")

    @property
    def provider(self) -> str:
        return "mitosis-ollama"
    
    @property
    def model_name(self) -> str:
        return self.model
    
    @property
    def name(self) -> str:
        return f"{self.provider}-{self.model}"

    def _convert_browser_use_messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """
        Convierte mensajes de browser-use a un prompt unificado para Ollama
        
        Args:
            messages: Lista de mensajes de browser-use
            
        Returns:
            str: Prompt unificado para Ollama
        """
        prompt_parts = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                prompt_parts.append(f"SYSTEM: {message.content}")
            elif isinstance(message, UserMessage):
                # Manejar contenido que puede ser texto o lista de contenidos
                if isinstance(message.content, str):
                    prompt_parts.append(f"USER: {message.content}")
                elif isinstance(message.content, list):
                    # Extraer solo texto, ignorar imágenes por ahora
                    text_content = []
                    for content in message.content:
                        if hasattr(content, 'text'):
                            text_content.append(content.text)
                        elif isinstance(content, str):
                            text_content.append(content)
                    prompt_parts.append(f"USER: {' '.join(text_content)}")
            elif isinstance(message, AssistantMessage):
                prompt_parts.append(f"ASSISTANT: {message.content}")
        
        # Agregar prompt final para respuesta del asistente
        prompt_parts.append("ASSISTANT:")
        
        return "\n\n".join(prompt_parts)

    async def ainvoke(
        self, 
        messages: List[Union[UserMessage, SystemMessage, AssistantMessage]], 
        output_format: Optional[Type] = None
    ) -> ChatInvokeCompletion:
        """
        Método principal requerido por browser-use para invocar el modelo
        
        Args:
            messages: Lista de mensajes para procesar
            output_format: Formato de salida opcional (para structured output)
            
        Returns:
            ChatInvokeCompletion: Respuesta del modelo
        """
        try:
            logger.info(f"🧠 Procesando {len(messages)} mensajes con {self.model}")
            
            # Convertir mensajes de browser-use a prompt para Ollama
            prompt = self._convert_browser_use_messages_to_prompt(messages)
            
            logger.debug(f"📝 Prompt generado: {prompt[:200]}...")
            
            # Preparar opciones específicas para browser-use (más determinístico)
            options = {
                "temperature": 0.3,  # Más determinístico para navegación
                "top_p": 0.8,
                "max_tokens": 1500,  # Suficiente para respuestas de navegación
                "stop": ["USER:", "SYSTEM:", "\n\nUSER:", "\n\nSYSTEM:"]
            }
            
            # Llamar a OllamaService de manera asíncrona
            response_data = await asyncio.to_thread(
                self.ollama_service.generate_response,
                prompt=prompt,
                model=self.model,
                **options
            )
            
            # Extraer respuesta del resultado
            if isinstance(response_data, dict):
                if 'error' in response_data:
                    logger.error(f"❌ Error en Ollama: {response_data['error']}")
                    response_text = "Lo siento, hubo un error procesando la solicitud."
                else:
                    response_text = response_data.get('response', response_data.get('content', ''))
            else:
                response_text = str(response_data)
            
            # Limpiar respuesta
            response_text = response_text.strip()
            if response_text.startswith("ASSISTANT:"):
                response_text = response_text[10:].strip()
            
            logger.info(f"✅ Respuesta generada: {len(response_text)} caracteres")
            logger.debug(f"📤 Respuesta: {response_text[:100]}...")
            
            # Si se requiere formato estructurado, intentar parsear
            if output_format:
                try:
                    # Intento básico de parsing estructurado
                    # Esto puede necesitar mejoras según los requerimientos específicos
                    import json
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_str = response_text[json_start:json_end].strip()
                        parsed_data = json.loads(json_str)
                        return ChatInvokeCompletion(response=output_format(**parsed_data))
                    else:
                        # Fallback: usar respuesta como string
                        return ChatInvokeCompletion(response=response_text)
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo parsear formato estructurado: {e}")
                    return ChatInvokeCompletion(response=response_text)
            
            return ChatInvokeCompletion(response=response_text)
            
        except Exception as e:
            logger.error(f"❌ Error en MitosisOllamaChatModel.ainvoke: {str(e)}")
            return ChatInvokeCompletion(
                response="Lo siento, hubo un problema procesando tu solicitud. Por favor intenta de nuevo."
            )

    def get_client(self):
        """
        Método de compatibilidad con browser-use
        Retorna self ya que este wrapper actúa como cliente
        """
        return self

    @classmethod
    def create_from_mitosis_config(
        cls, 
        ollama_service: OllamaService, 
        model: str = "llama3.1:8b"
    ) -> "MitosisOllamaChatModel":
        """
        Factory method para crear desde configuración existente de Mitosis
        
        Args:
            ollama_service: Instancia existente de OllamaService
            model: Modelo a usar
            
        Returns:
            MitosisOllamaChatModel: Instancia configurada
        """
        return cls(
            model=model,
            host=ollama_service.base_url,
            ollama_service=ollama_service
        )