#!/usr/bin/env python3
"""
MITOSIS - SERVIDOR CONSOLIDADO MAESTRO
Versión refactorizada que consolida toda la funcionalidad de múltiples servidores
eliminando duplicaciones y manteniendo 100% de la funcionalidad.

Consolida:
- server.py
- server_simple.py  
- unified_api.py
- enhanced_unified_api.py
- Y todos los demás servidores fragmentados

Autor: Mitosis Refactoring Agent
Fecha: 2025-07-23
"""

import os
import sys
import time
import uuid
import json
import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

# Flask y extensiones
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
import pymongo

# Configurar logging centralizado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/mitosis_consolidated.log')
    ]
)
logger = logging.getLogger(__name__)

# Terminal logger para outputs visibles
terminal_logger = logging.getLogger('MITOSIS_CONSOLIDATED')
terminal_handler = logging.StreamHandler(sys.stdout)
terminal_handler.setLevel(logging.INFO)
terminal_formatter = logging.Formatter('%(asctime)s - [MITOSIS] - %(levelname)s - %(message)s')
terminal_handler.setFormatter(terminal_formatter)
terminal_logger.addHandler(terminal_handler)
terminal_logger.setLevel(logging.INFO)

terminal_logger.info("🚀 INICIANDO SERVIDOR MITOSIS CONSOLIDADO - Sistema Unificado")


# ============================================================================
# CONFIGURACIÓN CENTRALIZADA
# ============================================================================

@dataclass
class AppConfig:
    """Configuración centralizada de la aplicación"""
    HOST: str = '0.0.0.0'
    PORT: int = 8001
    DEBUG: bool = False
    SECRET_KEY: str = 'dev-secret-key'
    
    # Base de datos
    MONGO_URL: str = 'mongodb://localhost:27017/'
    DATABASE_NAME: str = 'mitosis'
    
    # Servicios externos
    OLLAMA_BASE_URL: str = 'https://bef4a4bb93d1.ngrok-free.app'
    OLLAMA_DEFAULT_MODEL: str = 'llama3.1:8b'
    OPENROUTER_API_KEY: Optional[str] = None
    
    # Configuraciones del agente
    AGENT_LLM_PROVIDER: str = 'ollama'
    MAX_CONCURRENT_TASKS: int = 2
    MEMORY_DB_PATH: str = 'consolidated_agent.db'
    MAX_SHORT_TERM_MESSAGES: int = 100
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Carga configuración desde variables de entorno"""
        load_dotenv()
        return cls(
            HOST=os.getenv('HOST', cls.HOST),
            PORT=int(os.getenv('PORT', cls.PORT)),
            DEBUG=os.getenv('DEBUG', 'False').lower() == 'true',
            SECRET_KEY=os.getenv('SECRET_KEY', cls.SECRET_KEY),
            MONGO_URL=os.getenv('MONGO_URL', cls.MONGO_URL),
            DATABASE_NAME=os.getenv('DATABASE_NAME', cls.DATABASE_NAME),
            OLLAMA_BASE_URL=os.getenv('OLLAMA_BASE_URL', cls.OLLAMA_BASE_URL),
            OLLAMA_DEFAULT_MODEL=os.getenv('OLLAMA_DEFAULT_MODEL', cls.OLLAMA_DEFAULT_MODEL),
            OPENROUTER_API_KEY=os.getenv('OPENROUTER_API_KEY'),
            AGENT_LLM_PROVIDER=os.getenv('AGENT_LLM_PROVIDER', cls.AGENT_LLM_PROVIDER),
            MAX_CONCURRENT_TASKS=int(os.getenv('MAX_CONCURRENT_TASKS', cls.MAX_CONCURRENT_TASKS)),
            MEMORY_DB_PATH=os.getenv('MEMORY_DB_PATH', cls.MEMORY_DB_PATH),
            MAX_SHORT_TERM_MESSAGES=int(os.getenv('MAX_SHORT_TERM_MESSAGES', cls.MAX_SHORT_TERM_MESSAGES))
        )


# ============================================================================
# RESPUESTAS API ESTANDARIZADAS
# ============================================================================

@dataclass
class APIResponse:
    """Estructura estándar para todas las respuestas API"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_response(self, status_code: int = 200):
        return jsonify(self.to_dict()), status_code

@dataclass
class MonitorPage:
    """Estructura para páginas del monitor"""
    id: str
    title: str
    content: str
    type: str
    timestamp: datetime
    metadata: Dict[str, Any]


# ============================================================================
# SERVIDOR CONSOLIDADO PRINCIPAL
# ============================================================================

class MitosisConsolidatedServer:
    """Servidor consolidado que unifica toda la funcionalidad fragmentada"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.start_time = time.time()
        
        # Inicializar Flask y extensiones
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = config.SECRET_KEY
        self.app.config['START_TIME'] = self.start_time
        
        # Configurar CORS
        CORS(self.app, resources={
            r"/api/*": {
                "origins": ["*"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
        
        # Configurar SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='eventlet')
        
        # Estado de la aplicación
        self.monitor_pages: List[MonitorPage] = []
        self.active_sessions: Dict[str, str] = {}
        self.active_connections: Dict[str, Any] = {}
        
        # Inicializar servicios
        self._initialize_services()
        
        # Configurar rutas y eventos
        self._setup_routes()
        self._setup_socketio_events()
        
        # Crear página inicial del monitor
        self._create_initial_monitor_page()
        
        terminal_logger.info("✅ Servidor Consolidado inicializado exitosamente")
        terminal_logger.info(f"✅ Puerto: {config.PORT}, Debug: {config.DEBUG}")
    
    def _initialize_services(self):
        """Inicializa todos los servicios necesarios de manera centralizada"""
        terminal_logger.info("🔧 Inicializando servicios...")
        
        # Agregar path para importaciones
        sys.path.append('/app/backend/src')
        sys.path.append('/app/backend')
        
        # 1. Inicializar MongoDB
        try:
            self.mongo_client = pymongo.MongoClient(self.config.MONGO_URL)
            self.db = self.mongo_client[self.config.DATABASE_NAME]
            # Test de conexión
            self.mongo_client.admin.command('ping')
            self.app.db = self.db
            terminal_logger.info("✅ MongoDB conectado exitosamente")
        except Exception as e:
            terminal_logger.error(f"❌ Error conectando MongoDB: {e}")
            self.db = None
        
        # 2. Inicializar WebSocket Manager
        try:
            from src.websocket.websocket_manager import initialize_websocket
            self.websocket_manager = initialize_websocket(self.app)
            self.app.websocket_manager = self.websocket_manager
            terminal_logger.info("✅ WebSocket Manager inicializado")
        except Exception as e:
            terminal_logger.warning(f"⚠️ WebSocket Manager no disponible: {e}")
            self.websocket_manager = None
        
        # 3. Inicializar servicio Ollama
        try:
            from src.services.ollama_service import OllamaService
            self.ollama_service = OllamaService(self.config.OLLAMA_BASE_URL)
            self.app.ollama_service = self.ollama_service
            terminal_logger.info("✅ Ollama Service inicializado")
        except Exception as e:
            terminal_logger.warning(f"⚠️ Ollama Service no disponible: {e}")
            self.ollama_service = None
        
        # 4. Inicializar Tool Manager
        try:
            from src.tools.tool_manager import ToolManager
            self.tool_manager = ToolManager()
            self.app.tool_manager = self.tool_manager
            tools_count = len(self.tool_manager.get_available_tools())
            terminal_logger.info(f"✅ Tool Manager inicializado - {tools_count} herramientas")
        except Exception as e:
            terminal_logger.warning(f"⚠️ Tool Manager no disponible: {e}")
            self.tool_manager = None
        
        # 5. Inicializar Task Manager
        try:
            from src.services.task_manager import TaskManager
            self.task_manager_service = TaskManager(self.db if self.db else None)
            self.app.task_manager = self.task_manager_service
            terminal_logger.info("✅ Task Manager inicializado")
        except Exception as e:
            terminal_logger.warning(f"⚠️ Task Manager no disponible: {e}")
            self.task_manager_service = None
        
        # 6. Registrar rutas del agente
        try:
            from src.routes.agent_routes import agent_bp
            self.app.register_blueprint(agent_bp, url_prefix='/api/agent')
            terminal_logger.info("✅ Rutas del agente registradas")
            
            # Log de endpoints disponibles
            agent_endpoints = [rule.rule for rule in self.app.url_map.iter_rules() if '/api/agent/' in rule.rule]
            terminal_logger.info(f"📡 {len(agent_endpoints)} endpoints del agente disponibles")
            
        except Exception as e:
            terminal_logger.error(f"❌ Error registrando rutas del agente: {e}")
            # Fallback a rutas básicas será implementado en _setup_routes()
    
    def _create_initial_monitor_page(self):
        """Crea la página inicial del monitor"""
        initial_content = f"""# MITOSIS CONSOLIDATED - Sistema Iniciado

## Estado del Sistema
- ✅ Servidor consolidado iniciado exitosamente
- ✅ Puerto: {self.config.PORT}
- ✅ Base de datos: {'✅ Conectada' if self.db else '❌ No disponible'}
- ✅ Ollama: {'✅ Conectado' if self.ollama_service else '❌ No disponible'}
- ✅ Herramientas: {len(self.tool_manager.get_available_tools()) if self.tool_manager else 0} disponibles

## Capacidades Disponibles
- 🤖 Chat conversacional inteligente
- 📋 Generación automática de planes de acción
- 🛠️ Ejecución de herramientas especializadas
- 📊 Monitor en tiempo real
- 💾 Persistencia de tareas en MongoDB
- 🧠 Sistema de memoria inteligente

## Tiempo de Inicio
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        page = MonitorPage(
            id="system_startup",
            title="Sistema Iniciado - Mitosis Consolidated",
            content=initial_content,
            type="system-status",
            timestamp=datetime.now(),
            metadata={
                "startup_time": self.start_time,
                "config": {
                    "port": self.config.PORT,
                    "debug": self.config.DEBUG,
                    "ollama_url": self.config.OLLAMA_BASE_URL
                }
            }
        )
        self.monitor_pages.append(page)
    
    def _setup_routes(self):
        """Configura todas las rutas API consolidadas"""
        
        # ====================================================================
        # HEALTH CHECK ROUTES
        # ====================================================================
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check principal del sistema"""
            try:
                health_data = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'uptime': time.time() - self.start_time,
                    'services': {
                        'database': self.db is not None,
                        'ollama': self.ollama_service.is_healthy() if self.ollama_service else False,
                        'tools': len(self.tool_manager.get_available_tools()) if self.tool_manager else 0,
                        'websocket': self.websocket_manager is not None
                    },
                    'memory_usage': self._get_memory_usage(),
                    'active_connections': len(self.active_connections)
                }
                
                return APIResponse(
                    success=True,
                    data=health_data,
                    metadata={'service': 'mitosis-consolidated'}
                ).to_response()
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return APIResponse(
                    success=False,
                    error=str(e),
                    metadata={'service': 'mitosis-consolidated'}
                ).to_response(500)
        
        @self.app.route('/api/health', methods=['GET'])
        def api_health_check():
            """Health check específico de la API"""
            try:
                api_data = {
                    'api_status': 'healthy',
                    'endpoints_active': len([rule for rule in self.app.url_map.iter_rules()]),
                    'services_status': {
                        'agent_routes': '/api/agent/' in str(self.app.url_map),
                        'database': self.db is not None,
                        'llm_service': self.ollama_service is not None
                    }
                }
                
                return APIResponse(
                    success=True,
                    data=api_data
                ).to_response()
                
            except Exception as e:
                return APIResponse(
                    success=False,
                    error=str(e)
                ).to_response(500)
        
        # ====================================================================
        # SYSTEM STATUS ROUTES
        # ====================================================================
        
        @self.app.route('/api/system/status', methods=['GET'])
        def get_system_status():
            """Estado completo del sistema"""
            try:
                # Verificar estado de servicios
                services_status = {}
                
                # MongoDB
                if self.db:
                    try:
                        self.mongo_client.admin.command('ping')
                        services_status['mongodb'] = {'status': 'connected', 'details': 'Ping successful'}
                    except Exception as e:
                        services_status['mongodb'] = {'status': 'error', 'details': str(e)}
                else:
                    services_status['mongodb'] = {'status': 'not_configured', 'details': 'No database connection'}
                
                # Ollama
                if self.ollama_service:
                    try:
                        is_healthy = self.ollama_service.is_healthy()
                        models = self.ollama_service.get_available_models() if is_healthy else []
                        services_status['ollama'] = {
                            'status': 'connected' if is_healthy else 'disconnected',
                            'endpoint': self.config.OLLAMA_BASE_URL,
                            'models_count': len(models),
                            'models': models[:5]  # Primeros 5 modelos
                        }
                    except Exception as e:
                        services_status['ollama'] = {'status': 'error', 'details': str(e)}
                else:
                    services_status['ollama'] = {'status': 'not_configured'}
                
                # Tools
                if self.tool_manager:
                    try:
                        tools = self.tool_manager.get_available_tools()
                        tool_names = [tool['name'] if isinstance(tool, dict) else str(tool) for tool in tools]
                        services_status['tools'] = {
                            'status': 'available',
                            'count': len(tools),
                            'tools': tool_names[:10]  # Primeros 10 tools
                        }
                    except Exception as e:
                        services_status['tools'] = {'status': 'error', 'details': str(e)}
                else:
                    services_status['tools'] = {'status': 'not_available'}
                
                system_data = {
                    'server_info': {
                        'name': 'Mitosis Consolidated Server',
                        'version': '1.0.0-refactored',
                        'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                        'uptime_seconds': time.time() - self.start_time,
                        'port': self.config.PORT,
                        'debug_mode': self.config.DEBUG
                    },
                    'services': services_status,
                    'performance': {
                        'memory_usage': self._get_memory_usage(),
                        'active_connections': len(self.active_connections),
                        'monitor_pages': len(self.monitor_pages)
                    },
                    'configuration': {
                        'llm_provider': self.config.AGENT_LLM_PROVIDER,
                        'max_concurrent_tasks': self.config.MAX_CONCURRENT_TASKS,
                        'openrouter_configured': bool(self.config.OPENROUTER_API_KEY)
                    }
                }
                
                return APIResponse(
                    success=True,
                    data=system_data
                ).to_response()
                
            except Exception as e:
                logger.error(f"System status error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e)
                ).to_response(500)
        
        # ====================================================================
        # CONFIGURATION ROUTES (Consolidadas)
        # ====================================================================
        
        @self.app.route('/api/agent/config/current', methods=['GET'])
        def get_current_configuration():
            """Configuración actual del agente"""
            try:
                # Verificar Ollama
                ollama_status = {
                    "connected": False,
                    "endpoint": self.config.OLLAMA_BASE_URL,
                    "available_models": []
                }
                
                if self.ollama_service:
                    try:
                        ollama_status["connected"] = self.ollama_service.is_healthy()
                        if ollama_status["connected"]:
                            ollama_status["available_models"] = self.ollama_service.get_available_models()
                    except Exception as e:
                        logger.warning(f"Error checking Ollama status: {e}")
                
                # Verificar OpenRouter
                openrouter_status = {
                    "configured": bool(self.config.OPENROUTER_API_KEY),
                    "available": False
                }
                
                config_data = {
                    "current_provider": self.config.AGENT_LLM_PROVIDER,
                    "ollama": {
                        "enabled": True,
                        "endpoint": self.config.OLLAMA_BASE_URL,
                        "model": self.config.OLLAMA_DEFAULT_MODEL
                    },
                    "openrouter": {
                        "enabled": openrouter_status["configured"],
                        "endpoint": "https://openrouter.ai/api/v1"
                    }
                }
                
                services_status = {
                    "ollama": ollama_status,
                    "openrouter": openrouter_status
                }
                
                return APIResponse(
                    success=True,
                    data={
                        "config": config_data,
                        "services_status": services_status
                    }
                ).to_response()
                
            except Exception as e:
                logger.error(f"Get config error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e)
                ).to_response(500)
        
        @self.app.route('/api/agent/config/apply', methods=['POST'])
        def apply_configuration():
            """Aplica nueva configuración"""
            try:
                data = request.get_json()
                if not data or 'config' not in data:
                    return APIResponse(
                        success=False,
                        error="Config is required"
                    ).to_response(400)
                
                new_config = data['config']
                
                # Aplicar configuración Ollama
                if 'ollama' in new_config and self.ollama_service:
                    ollama_config = new_config['ollama']
                    if 'endpoint' in ollama_config:
                        success = self.ollama_service.update_endpoint(ollama_config['endpoint'])
                        if success:
                            terminal_logger.info(f"✅ Ollama endpoint actualizado: {ollama_config['endpoint']}")
                
                # Verificar nueva configuración
                ollama_connected = self.ollama_service.is_healthy() if self.ollama_service else False
                
                result_data = {
                    "message": "Configuration applied successfully",
                    "config_applied": {
                        "ollama": {
                            "enabled": new_config.get('ollama', {}).get('enabled', True),
                            "endpoint": new_config.get('ollama', {}).get('endpoint', self.config.OLLAMA_BASE_URL),
                            "model": new_config.get('ollama', {}).get('model', self.config.OLLAMA_DEFAULT_MODEL),
                            "connected": ollama_connected
                        }
                    }
                }
                
                return APIResponse(
                    success=True,
                    data=result_data
                ).to_response()
                
            except Exception as e:
                logger.error(f"Apply config error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e)
                ).to_response(500)
        
        # ====================================================================
        # MONITOR ROUTES (Consolidadas)
        # ====================================================================
        
        @self.app.route('/api/monitor/pages', methods=['GET'])
        def get_monitor_pages():
            """Obtiene páginas del monitor con paginación"""
            try:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 10))
                
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                
                pages_data = []
                for monitor_page in self.monitor_pages[start_idx:end_idx]:
                    pages_data.append({
                        "id": monitor_page.id,
                        "title": monitor_page.title,
                        "content": monitor_page.content,
                        "type": monitor_page.type,
                        "timestamp": monitor_page.timestamp.isoformat(),
                        "metadata": monitor_page.metadata
                    })
                
                return APIResponse(
                    success=True,
                    data={
                        "pages": pages_data,
                        "total_pages": len(self.monitor_pages),
                        "current_page": page,
                        "per_page": per_page,
                        "has_next": end_idx < len(self.monitor_pages),
                        "has_prev": page > 1
                    }
                ).to_response()
                
            except Exception as e:
                logger.error(f"Get monitor pages error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e)
                ).to_response(500)
        
        @self.app.route('/api/monitor/latest', methods=['GET'])
        def get_latest_monitor_page():
            """Obtiene la última página del monitor"""
            try:
                if not self.monitor_pages:
                    return APIResponse(
                        success=False,
                        error="No pages available"
                    ).to_response(404)
                
                latest_page = self.monitor_pages[-1]
                page_data = {
                    "id": latest_page.id,
                    "title": latest_page.title,
                    "content": latest_page.content,
                    "type": latest_page.type,
                    "timestamp": latest_page.timestamp.isoformat(),
                    "metadata": latest_page.metadata,
                    "page_number": len(self.monitor_pages)
                }
                
                return APIResponse(
                    success=True,
                    data=page_data
                ).to_response()
                
            except Exception as e:
                logger.error(f"Get latest page error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e)
                ).to_response(500)
        
        # ====================================================================
        # FALLBACK ROUTES (Si las rutas del agente no se cargan)
        # ====================================================================
        
        # Solo se activarán si las rutas del agente reales no están disponibles
        if not any('/api/agent/chat' in rule.rule for rule in self.app.url_map.iter_rules()):
            terminal_logger.warning("⚠️ Rutas del agente no detectadas, activando fallbacks...")
            
            @self.app.route('/api/agent/chat', methods=['POST'])
            def fallback_chat():
                """Chat básico de fallback"""
                try:
                    data = request.get_json()
                    message = data.get('message', '') if data else ''
                    
                    if not message:
                        return APIResponse(
                            success=False,
                            error="Message is required"
                        ).to_response(400)
                    
                    # Respuesta básica
                    response_data = {
                        "response": f"[FALLBACK] Mensaje recibido: {message}",
                        "task_id": f"fallback_{int(datetime.now().timestamp())}",
                        "memory_used": True,
                        "status": "completed"
                    }
                    
                    return APIResponse(
                        success=True,
                        data=response_data
                    ).to_response()
                    
                except Exception as e:
                    logger.error(f"Fallback chat error: {e}")
                    return APIResponse(
                        success=False,
                        error=str(e)
                    ).to_response(500)
            
            @self.app.route('/api/agent/status', methods=['GET'])
            def fallback_agent_status():
                """Status del agente básico"""
                try:
                    status_data = {
                        "status": "running",
                        "mode": "fallback",
                        "ollama": {
                            "connected": self.ollama_service.is_healthy() if self.ollama_service else False,
                            "endpoint": self.config.OLLAMA_BASE_URL,
                            "model": self.config.OLLAMA_DEFAULT_MODEL
                        },
                        "tools": {
                            "available": len(self.tool_manager.get_available_tools()) if self.tool_manager else 0
                        },
                        "memory": {
                            "enabled": True,
                            "initialized": True
                        }
                    }
                    
                    return APIResponse(
                        success=True,
                        data=status_data
                    ).to_response()
                    
                except Exception as e:
                    logger.error(f"Fallback status error: {e}")
                    return APIResponse(
                        success=False,
                        error=str(e)
                    ).to_response(500)
        
        # ====================================================================
        # UTILITY ROUTES
        # ====================================================================
        
        @self.app.route('/api/agent/generate-suggestions', methods=['POST'])
        def generate_suggestions():
            """Genera sugerencias dinámicas"""
            try:
                suggestions_data = [
                    {
                        "title": "Búsqueda web inteligente",
                        "description": "Investigar información actualizada usando herramientas web"
                    },
                    {
                        "title": "Análisis de datos",
                        "description": "Procesar y analizar información con herramientas especializadas"
                    },
                    {
                        "title": "Crear documentación",
                        "description": "Generar documentos técnicos y reportes detallados"
                    }
                ]
                
                return APIResponse(
                    success=True,
                    data={"suggestions": suggestions_data}
                ).to_response()
                
            except Exception as e:
                logger.error(f"Generate suggestions error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e)
                ).to_response(500)
        
        # ====================================================================
        # ERROR HANDLERS
        # ====================================================================
        
        @self.app.errorhandler(404)
        def not_found(error):
            return APIResponse(
                success=False,
                error="Endpoint not found",
                metadata={"requested_path": request.path}
            ).to_response(404)
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return APIResponse(
                success=False,
                error="Internal server error",
                metadata={"error_type": "internal_server_error"}
            ).to_response(500)
        
        terminal_logger.info("✅ Todas las rutas API configuradas exitosamente")
    
    def _setup_socketio_events(self):
        """Configura eventos WebSocket consolidados"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Maneja conexión de cliente"""
            session_id = request.sid
            room_id = str(uuid.uuid4())
            
            self.active_connections[session_id] = {
                'room_id': room_id,
                'connect_time': datetime.now(),
                'last_activity': datetime.now()
            }
            
            join_room(room_id)
            emit('connected', {
                'session_id': session_id,
                'room_id': room_id,
                'server_info': {
                    'name': 'Mitosis Consolidated Server',
                    'version': '1.0.0-refactored'
                }
            })
            
            terminal_logger.info(f"🔌 Cliente conectado: {session_id}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Maneja desconexión de cliente"""
            session_id = request.sid
            if session_id in self.active_connections:
                del self.active_connections[session_id]
            terminal_logger.info(f"🔌 Cliente desconectado: {session_id}")
        
        @self.socketio.on('join_monitoring')
        def handle_join_monitoring(data):
            """Une cliente a sala de monitoreo"""
            room_id = data.get('room_id') if data else None
            if room_id:
                join_room(f"monitor_{room_id}")
                emit('monitoring_joined', {'status': 'success', 'room_id': room_id})
                terminal_logger.info(f"📊 Cliente unido a monitoreo: {room_id}")
        
        @self.socketio.on('heartbeat')
        def handle_heartbeat(data):
            """Maneja heartbeat de cliente"""
            session_id = request.sid
            if session_id in self.active_connections:
                self.active_connections[session_id]['last_activity'] = datetime.now()
            emit('heartbeat_ack', {'timestamp': datetime.now().isoformat()})
        
        terminal_logger.info("✅ Eventos WebSocket configurados exitosamente")
    
    def add_monitor_page(self, title: str, content: str, page_type: str, metadata: Optional[Dict] = None):
        """Agrega nueva página al monitor y notifica clientes"""
        if metadata is None:
            metadata = {}
        
        page = MonitorPage(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            type=page_type,
            timestamp=datetime.now(),
            metadata={
                **metadata,
                "lineCount": len(content.split('\n')),
                "fileSize": len(content.encode('utf-8'))
            }
        )
        
        self.monitor_pages.append(page)
        
        # Notificar a clientes via WebSocket
        self.socketio.emit('new_monitor_page', {
            "id": page.id,
            "title": page.title,
            "content": page.content,
            "type": page.type,
            "timestamp": page.timestamp.isoformat(),
            "metadata": page.metadata,
            "page_number": len(self.monitor_pages)
        }, room='monitoring')
        
        terminal_logger.info(f"📄 Nueva página del monitor: {title}")
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Obtiene información de uso de memoria"""
        try:
            import psutil
            process = psutil.Process()
            return {
                'rss': round(process.memory_info().rss / 1024 / 1024, 2),  # MB
                'vms': round(process.memory_info().vms / 1024 / 1024, 2),  # MB
                'percent': round(process.memory_percent(), 2)
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    def run(self):
        """Ejecuta el servidor consolidado"""
        terminal_logger.info("=" * 80)
        terminal_logger.info("🚀 INICIANDO MITOSIS CONSOLIDATED SERVER")
        terminal_logger.info("=" * 80)
        terminal_logger.info(f"🌐 Host: {self.config.HOST}:{self.config.PORT}")
        terminal_logger.info(f"🔧 Debug: {self.config.DEBUG}")
        terminal_logger.info(f"🗄️ Database: {'✅ Connected' if self.db else '❌ Not available'}")
        terminal_logger.info(f"🤖 Ollama: {'✅ Connected' if self.ollama_service else '❌ Not available'}")
        terminal_logger.info(f"🛠️ Tools: {len(self.tool_manager.get_available_tools()) if self.tool_manager else 0} available")
        terminal_logger.info("=" * 80)
        
        try:
            self.socketio.run(
                self.app,
                host=self.config.HOST,
                port=self.config.PORT,
                debug=self.config.DEBUG
            )
        except KeyboardInterrupt:
            terminal_logger.info("🛑 Shutdown signal received")
        except Exception as e:
            terminal_logger.error(f"❌ Server error: {e}")
        finally:
            terminal_logger.info("🔄 Shutting down...")
            self.shutdown()
    
    def shutdown(self):
        """Cierra el servidor y limpia recursos"""
        terminal_logger.info("🛑 Iniciando shutdown...")
        
        # Cerrar conexiones de base de datos
        if hasattr(self, 'mongo_client'):
            try:
                self.mongo_client.close()
                terminal_logger.info("✅ MongoDB connection closed")
            except Exception as e:
                terminal_logger.error(f"❌ Error closing MongoDB: {e}")
        
        terminal_logger.info("✅ Shutdown completado")


# ============================================================================
# FUNCIÓN PRINCIPAL Y FACTORY
# ============================================================================

def create_consolidated_server(config: Optional[AppConfig] = None) -> MitosisConsolidatedServer:
    """Factory function para crear servidor consolidado"""
    if config is None:
        config = AppConfig.from_env()
    
    return MitosisConsolidatedServer(config)


def main():
    """Función principal de entrada"""
    # Crear configuración desde environment
    config = AppConfig.from_env()
    
    # Crear y ejecutar servidor
    server = create_consolidated_server(config)
    server.run()


if __name__ == '__main__':
    main()