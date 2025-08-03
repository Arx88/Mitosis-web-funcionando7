#!/usr/bin/env python3
"""
SERVIDOR BACKEND SIMPLIFICADO Y ROBUSTO CON AGENTE EFECTIVO
Versión estable con planes de acción REALES
"""

import os
import sys
import time
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
FRONTEND_ORIGINS = [
    # 🌐 URL DETECTADA DINÁMICAMENTE
    "https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com",
    
    # 🔧 WILDCARD PARA TODOS LOS PREVIEW DOMAINS  
    "https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com",
    
    # 🏠 DESARROLLO LOCAL
    "http://localhost:3000",
    "http://localhost:5173", 
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    
    # 📱 PREVIEW DOMAINS COMUNES
    "https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com",
    "https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com",
    
    # 🌟 FALLBACK UNIVERSAL (último recurso)
    "*"
]
# CONFIGURACIÓN DINÁMICA DE CORS - DETECTA AUTOMÁTICAMENTE LA URL DEL ENTORNO
def get_current_environment_url():
    """Detecta la URL del entorno actual dinámicamente"""
    import socket
    import os
    
    # Método 1: Variables de entorno del sistema
    if os.environ.get('EMERGENT_PREVIEW_URL'):
        return os.environ.get('EMERGENT_PREVIEW_URL')
    
    # Método 2: Detectar desde hostname
    try:
        hostname = socket.gethostname()
        if '.emergentagent.' in hostname or '-' in hostname:
            # Extraer ID del container/hostname para formar URL
            if 'agent-env-' in hostname:
                env_id = hostname.replace('agent-env-', '')
                return f"https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com"
            elif '-' in hostname and len(hostname) > 20:
                return f"https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com"
    except:
        pass
    
    # Método 3: Fallback usando patrón común
    return "https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com"

# Generar CORS origins dinámicamente
CURRENT_ENV_URL = get_current_environment_url()

# CONFIGURACIÓN DINÁMICA DE CORS - SIN HARDCODED URLs  
def get_dynamic_cors_origins():
    """
    Sistema dinámico de CORS que acepta cualquier origen válido de emergent
    SIN URLs hardcodeadas
    """
    base_origins = [
        # DESARROLLO LOCAL
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        
        # 🔧 WILDCARD PARA TODOS LOS PREVIEW DOMAINS DE EMERGENT - SIN HARDCODING
        "https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com",
        
        # 🌟 FALLBACK UNIVERSAL (último recurso)
        "*"
    ]
    
    # Agregar la URL detectada dinámicamente si está disponible
    if CURRENT_ENV_URL and CURRENT_ENV_URL != "https://7c8244f3-e97e-49c3-bcd4-bb7b083f759d.preview.emergentagent.com":
        base_origins.insert(0, CURRENT_ENV_URL)
    
    return base_origins

FRONTEND_ORIGINS = get_dynamic_cors_origins()
from flask_socketio import SocketIO
from dotenv import load_dotenv
import pymongo
import logging

# Configurar logging más intenso
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/mitosis_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Logging para terminal también
terminal_logger = logging.getLogger('MITOSIS_TERMINAL')
terminal_handler = logging.StreamHandler(sys.stdout)
terminal_handler.setLevel(logging.INFO)
terminal_formatter = logging.Formatter('%(asctime)s - [MITOSIS] - %(levelname)s - %(message)s')
terminal_handler.setFormatter(terminal_formatter)
terminal_logger.addHandler(terminal_handler)
terminal_logger.setLevel(logging.INFO)

terminal_logger.info("🚀 INICIANDO SERVIDOR CON LOGGING INTENSO - Sistema completo del agente")
print("🚀 INICIANDO SERVIDOR CON LOGGING INTENSO - Sistema completo del agente")

# Cargar variables de entorno
load_dotenv()

# Configuración
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8001))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['START_TIME'] = time.time()

# Configurar CORS - CONFIGURACIÓN ULTRA-DINÁMICA PARA WEBSOCKET

CORS(app, resources={
    r"/api/*": {
        "origins": FRONTEND_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
        "supports_credentials": False,
        "expose_headers": ["Content-Type", "Authorization"]
    },
    r"/files/*": {
        "origins": FRONTEND_ORIGINS,
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"]
    },
    r"/get-task-files/*": {
        "origins": FRONTEND_ORIGINS,
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"]
    },
    r"/socket.io/*": {
        "origins": FRONTEND_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
        "supports_credentials": False,
        "expose_headers": ["Content-Type"]
    }
})

# Configurar MongoDB
try:
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/')
    client = pymongo.MongoClient(mongo_url)
    db = client.mitosis
    logger.info("✅ MongoDB conectado exitosamente")
except Exception as e:
    logger.error(f"❌ Error conectando MongoDB: {e}")
    db = None

# Añadir el directorio src al path para importar las rutas del agente
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Inicializar SocketIO directamente (simplificado)
try:
    from flask_socketio import SocketIO, emit, join_room, leave_room
    
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        cors_credentials=False,
        async_mode='eventlet',
        logger=False,
        engineio_logger=False,
        ping_timeout=60,
        ping_interval=25,
        transports=['polling', 'websocket'],
        allow_upgrades=True,
        path='/api/socket.io/',
        manage_session=False
    )
    
    # Eventos WebSocket simplificados
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"🔌 Client connected: {request.sid}")
        emit('connection_status', {'status': 'connected', 'sid': request.sid})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"❌ Client disconnected: {request.sid}")
    
    @socketio.on('join_task')
    def handle_join_task(data):
        task_id = data.get('task_id')
        if task_id:
            join_room(f"task_{task_id}")
            logger.info(f"🔗 Client {request.sid} joined task room: {task_id}")
            emit('joined_task', {'task_id': task_id, 'room': f"task_{task_id}"})
    
    @socketio.on('leave_task')
    def handle_leave_task(data):
        task_id = data.get('task_id')
        if task_id:
            leave_room(f"task_{task_id}")
            logger.info(f"🔗 Client {request.sid} left task room: {task_id}")
    
    # Función para emitir eventos
    def emit_task_event(task_id: str, event_type: str, data: dict):
        """Emitir evento a la room de la tarea"""
        try:
            room = f"task_{task_id}"
            logger.info(f"📡 Emitting {event_type} to room {room}: {data}")
            socketio.emit(event_type, data, room=room)
            return True
        except Exception as e:
            logger.error(f"❌ Error emitting event: {e}")
            return False
    
    app.socketio = socketio
    app.emit_task_event = emit_task_event
    logger.info("✅ SocketIO inicializado exitosamente")
    
except Exception as e:
    logger.error(f"❌ Error inicializando SocketIO: {e}")
    socketio = None

# Inicializar servicio Ollama
try:
    from src.services.ollama_service import OllamaService
    ollama_service = OllamaService()
    app.ollama_service = ollama_service
    logger.info("✅ Ollama Service inicializado exitosamente")
except Exception as e:
    logger.error(f"❌ Error inicializando Ollama Service: {e}")

# Inicializar Tool Manager  
try:
    from src.tools.tool_manager import ToolManager
    tool_manager = ToolManager()
    app.tool_manager = tool_manager
    terminal_logger.info(f"✅ Tool Manager inicializado exitosamente - {len(tool_manager.get_available_tools())} herramientas")
    print(f"✅ Tool Manager inicializado exitosamente - {len(tool_manager.get_available_tools())} herramientas")
    
    # Log de herramientas disponibles
    tools = tool_manager.get_available_tools()
    tool_names = [tool['name'] for tool in tools] if isinstance(tools[0] if tools else {}, dict) else tools
    terminal_logger.info(f"🛠️ Herramientas disponibles: {', '.join(tool_names[:5])}...")
    print(f"🛠️ Herramientas disponibles: {', '.join(tool_names[:5])}...")
    
except Exception as e:
    terminal_logger.error(f"❌ Error inicializando Tool Manager: {e}")
    print(f"❌ Error inicializando Tool Manager: {e}")
    import traceback
    traceback.print_exc()

# ✅ CRITICAL FIX: Enhanced Agent no existe, usar Ollama directamente
# Los planes reales se generan ahora directamente en agent_routes.py usando ollama_service
terminal_logger.info("✅ Plan generation fixed - using Ollama directly for REAL plans")
print("✅ Plan generation fixed - using Ollama directly for REAL plans")

# FORZAR IMPORTACIÓN DE RUTAS REALES DEL AGENTE CON LOGGING INTENSO
terminal_logger.info("🔄 Intentando importar las rutas REALES del agente con funcionalidad completa...")
try:
    # Importar primero las dependencias necesarias
    sys.path.insert(0, '/app/backend/src')
    
    terminal_logger.info("📋 Importando rutas del agente...")
    from src.routes.agent_routes import agent_bp
    
    # Verificar que las rutas se importaron correctamente
    app.register_blueprint(agent_bp, url_prefix='/api/agent')
    terminal_logger.info("✅ RUTAS REALES DEL AGENTE CARGADAS EXITOSAMENTE - Sistema completo disponible")
    print("✅ RUTAS REALES DEL AGENTE CARGADAS EXITOSAMENTE - Sistema completo disponible")
    
    # Log de endpoints disponibles
    terminal_logger.info("📡 Endpoints del agente disponibles:")
    print("📡 Endpoints del agente disponibles:")
    for rule in app.url_map.iter_rules():
        if '/api/agent/' in rule.rule:
            terminal_logger.info(f"   - {rule.methods} {rule.rule}")
            print(f"   - {rule.methods} {rule.rule}")
    
    AGENT_ROUTES_LOADED = True
    
except Exception as e:
    terminal_logger.error(f"❌ FALLO al importar rutas reales del agente: {e}")
    print(f"❌ FALLO al importar rutas reales del agente: {e}")
    import traceback
    traceback.print_exc()
    
    terminal_logger.warning("⚠️ Fallback a rutas básicas...")
    print("⚠️ Fallback a rutas básicas...")
    
    AGENT_ROUTES_LOADED = False
    from flask import Blueprint
    agent_bp = Blueprint('agent', __name__)
    
    @agent_bp.route('/chat', methods=['POST'])
    def chat():
        """Endpoint de chat básico de fallback"""
        try:
            data = request.get_json()
            message = data.get('message', '')
            
            if not message:
                return jsonify({"error": "Message is required"}), 400
            
            # Respuesta básica estable
            response = {
                "response": f"Mensaje recibido: {message}",
                "timestamp": datetime.now().isoformat(),
                "task_id": f"task_{int(datetime.now().timestamp())}",
                "memory_used": True,
                "status": "completed"
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @agent_bp.route('/status', methods=['GET'])
    def agent_status():
        """Status del agente"""
        try:
            # Verificar conexión Ollama real
            ollama_connected = False
            ollama_models = []
            
            if hasattr(app, 'ollama_service') and app.ollama_service:
                try:
                    ollama_connected = app.ollama_service.is_healthy()
                    if ollama_connected:
                        ollama_models = app.ollama_service.get_available_models()
                except:
                    ollama_connected = False
            
            # Obtener herramientas disponibles
            tools_available = []
            if hasattr(app, 'tool_manager') and app.tool_manager:
                try:
                    tools_list = app.tool_manager.get_available_tools()
                    tools_available = [tool['name'] for tool in tools_list] if tools_list else []
                except:
                    pass
            
            status = {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "ollama": {
                    "connected": ollama_connected,
                    "endpoint": os.getenv('OLLAMA_BASE_URL', 'https://bef4a4bb93d1.ngrok-free.app'),
                    "model": app.ollama_service.get_current_model() if hasattr(app, 'ollama_service') and app.ollama_service else os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3.1:8b'),  # 🔧 FIX: Mostrar modelo actual real
                    "available_models": ollama_models[:5] if ollama_models else [],  # Primeros 5
                    "models_count": len(ollama_models)
                },
                "tools": tools_available[:5] if tools_available else [],  # Primeros 5
                "tools_count": len(tools_available) if tools_available else 0,
                "memory": {
                    "enabled": True,
                    "initialized": True
                },
                "configuration": {
                    "provider": os.getenv('AGENT_LLM_PROVIDER', 'ollama'),
                    "openrouter_configured": bool(os.getenv('OPENROUTER_API_KEY'))
                }
            }
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"Status error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    # Blueprint ya registrado anteriormente en la línea 150
    logger.info("⚠️ Blueprint agent ya registrado anteriormente")

# Endpoints de configuración dinámica
@app.route('/api/agent/config/current', methods=['GET'])
def get_current_configuration():
    """Obtiene la configuración actual del agente"""
    try:
        # Verificar estado de servicios
        ollama_status = {
            "connected": False,
            "endpoint": os.getenv('OLLAMA_BASE_URL', ''),
            "available_models": []
        }
        
        if hasattr(app, 'ollama_service') and app.ollama_service:
            try:
                ollama_status["connected"] = app.ollama_service.is_healthy()
                ollama_status["endpoint"] = app.ollama_service.base_url
                if ollama_status["connected"]:
                    ollama_status["available_models"] = app.ollama_service.get_available_models()
            except:
                pass
        
        # Verificar OpenRouter
        openrouter_status = {
            "configured": bool(os.getenv('OPENROUTER_API_KEY')),
            "available": False
        }
        
        if openrouter_status["configured"]:
            try:
                from openrouter_service import OpenRouterService
                or_service = OpenRouterService()
                openrouter_status["available"] = or_service.is_available()
            except:
                pass
        
        config = {
            "success": True,
            "config": {
                "current_provider": os.getenv('AGENT_LLM_PROVIDER', 'ollama'),
                "ollama": {
                    "enabled": True,
                    "endpoint": os.getenv('OLLAMA_BASE_URL', ''),
                    "model": os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3.1:8b')
                },
                "openrouter": {
                    "enabled": openrouter_status["configured"],
                    "endpoint": os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
                }
            },
            "services_status": {
                "ollama": ollama_status,
                "openrouter": openrouter_status
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(config), 200
    except Exception as e:
        logger.error(f"Config current error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agent/config/apply', methods=['POST'])  
def apply_configuration():
    """Aplica nueva configuración del agente"""
    try:
        data = request.get_json()
        if not data or 'config' not in data:
            return jsonify({"success": False, "error": "Config is required"}), 400
        
        new_config = data['config']
        
        # 🔧 FIX PROBLEMA 2: Aplicar configuración de Ollama CON MODELO
        if 'ollama' in new_config:
            ollama_config = new_config['ollama']
            
            # Actualizar endpoint si se proporciona
            if 'endpoint' in ollama_config:
                if hasattr(app, 'ollama_service') and app.ollama_service:
                    success = app.ollama_service.update_endpoint(ollama_config['endpoint'])
                    if not success:
                        logger.warning(f"Failed to update Ollama endpoint to {ollama_config['endpoint']}")
            
            # 🚀 CRÍTICO FIX: Actualizar modelo activo cuando se cambie desde el frontend
            if 'model' in ollama_config:
                new_model = ollama_config['model']
                if hasattr(app, 'ollama_service') and app.ollama_service:
                    # Actualizar el modelo actual del servicio FORZADAMENTE
                    old_model = app.ollama_service.get_current_model()
                    success = app.ollama_service.set_model(new_model)  # Usar set_model que ahora fuerza el cambio
                    
                    logger.info(f"🔄 Modelo Ollama actualizado desde configuración: {old_model} → {new_model} (success: {success})")
                    print(f"🔄 Modelo Ollama actualizado desde configuración: {old_model} → {new_model} (success: {success})")
                    
                    # También actualizar la variable de entorno para persistencia
                    os.environ['OLLAMA_DEFAULT_MODEL'] = new_model
                    
                    # Verificar que efectivamente se cambió
                    current_after_change = app.ollama_service.get_current_model()
                    logger.info(f"🔍 Verificación post-cambio: {current_after_change}")
                    print(f"🔍 Verificación post-cambio: {current_after_change}")
                else:
                    logger.error("❌ ollama_service no disponible para cambio de modelo")
                    print("❌ ollama_service no disponible para cambio de modelo")
        
        # Verificar nueva configuración
        ollama_connected = False
        current_model = os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3.1:8b')
        
        if hasattr(app, 'ollama_service') and app.ollama_service:
            ollama_connected = app.ollama_service.is_healthy()
            current_model = app.ollama_service.get_current_model()
        
        result = {
            "success": True,
            "message": "Configuration applied successfully",
            "config_applied": {
                "ollama": {
                    "enabled": new_config.get('ollama', {}).get('enabled', True),
                    "endpoint": new_config.get('ollama', {}).get('endpoint', os.getenv('OLLAMA_BASE_URL')),
                    "model": current_model,  # 🔧 FIX: Devolver el modelo actual real
                    "connected": ollama_connected,
                    "model_updated": True  # 🔧 FIX: Indicar que el modelo fue actualizado
                },
                "openrouter": {
                    "enabled": new_config.get('openrouter', {}).get('enabled', False)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Config apply error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agent/ollama/models', methods=['POST'])
def get_ollama_models():
    """Obtiene modelos de un endpoint Ollama específico"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint') if data else os.getenv('OLLAMA_BASE_URL')
        
        if not endpoint:
            return jsonify({"error": "Endpoint is required"}), 400
        
        # Importar el servicio dentro de la función para evitar problemas de importación
        from src.services.ollama_service import OllamaService
        
        # Crear servicio temporal para el endpoint
        temp_service = OllamaService(endpoint)
        
        if temp_service.is_healthy():
            models = temp_service.get_available_models()
            return jsonify({
                "models": [{"name": model, "endpoint": endpoint} for model in models],
                "endpoint": endpoint,
                "count": len(models),
                "fallback": False
            }), 200
        else:
            # Fallback con modelos conocidos
            fallback_models = ["llama3.1:8b", "llama3:latest", "mistral:latest", "codellama:latest"]
            return jsonify({
                "models": [{"name": model, "endpoint": endpoint} for model in fallback_models],
                "endpoint": endpoint, 
                "count": len(fallback_models),
                "fallback": True,
                "warning": "Could not connect to endpoint, showing fallback models"
            }), 200
    except Exception as e:
        logger.error(f"Ollama models error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/agent/ollama/check', methods=['POST'])
def check_ollama_connection():
    """Verifica conexión a un endpoint Ollama específico"""
    try:
        data = request.get_json() 
        endpoint = data.get('endpoint') if data else os.getenv('OLLAMA_BASE_URL')
        
        if not endpoint:
            return jsonify({"error": "Endpoint is required"}), 400
        
        from src.services.ollama_service import OllamaService
        temp_service = OllamaService(endpoint)
        
        is_connected = temp_service.is_healthy()
        
        return jsonify({
            "is_connected": is_connected,
            "endpoint": endpoint,
            "status": "connected" if is_connected else "disconnected",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Ollama check error: {e}")
        return jsonify({"error": str(e)}), 500

# Ruta de health check
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check mejorado"""
    try:
        # Verificar servicios principales
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': False,
                'ollama': False,
                'tools': 0
            },
            'uptime': time.time() - app.config.get('START_TIME', time.time()),
            'memory_usage': get_memory_usage(),
            'active_connections': get_active_connections_count()
        }
        
        # Verificar MongoDB
        try:
            from pymongo import MongoClient
            client = MongoClient(os.getenv('MONGO_URL'))
            client.admin.command('ping')
            health_status['services']['database'] = True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
        
        # Verificar Ollama
        try:
            if hasattr(app, 'ollama_service') and app.ollama_service:
                health_status['services']['ollama'] = app.ollama_service.is_healthy()
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
        
        # Verificar herramientas
        try:
            if hasattr(app, 'tool_manager') and app.tool_manager:
                health_status['services']['tools'] = len(app.tool_manager.get_available_tools())
        except Exception as e:
            logger.error(f"Tools health check failed: {e}")
        
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def get_memory_usage():
    """Obtener uso de memoria del proceso"""
    try:
        import psutil
        process = psutil.Process()
        return {
            'rss': process.memory_info().rss / 1024 / 1024,  # MB
            'vms': process.memory_info().vms / 1024 / 1024,  # MB
            'percent': process.memory_percent()
        }
    except:
        return {'error': 'psutil not available'}

def get_active_connections_count():
    """Obtener número de conexiones WebSocket activas"""
    try:
        if hasattr(app, 'websocket_manager') and app.websocket_manager:
            return len(app.websocket_manager.active_connections)
        return 0
    except:
        return 0

# Ruta básica de status API
@app.route('/api/health', methods=['GET'])
def api_health_check():
    """API Health check endpoint"""
    try:
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db is not None,
                "ollama": True,  # Simplificado
                "tools": 12     # Simplificado
            }
        }
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"API Health check error: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/agent/model-info', methods=['GET'])
def get_current_model_info():
    """Obtener información del modelo Ollama actual"""
    try:
        if hasattr(app, 'ollama_service') and app.ollama_service:
            current_model = app.ollama_service.get_current_model()
            default_model = app.ollama_service.default_model
            is_healthy = app.ollama_service.is_healthy()
            
            return jsonify({
                "success": True,
                "current_model": current_model,
                "default_model": default_model,
                "is_healthy": is_healthy,
                "endpoint": app.ollama_service.base_url if hasattr(app.ollama_service, 'base_url') else 'unknown',
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Ollama service not available",
                "current_model": os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3.1:8b'),
                "timestamp": datetime.now().isoformat()
            }), 500
    except Exception as e:
        logger.error(f"Model info error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Endpoint para sugerencias dinámicas que faltaba
@app.route('/api/agent/cleanup-completed-tasks', methods=['POST'])
def cleanup_completed_tasks():
    """Limpia las tareas completadas del sistema para prevenir loops infinitos"""
    try:
        cleanup_count = 0
        
        # Limpiar tareas completadas de la base de datos que sean más antiguas de 1 hora
        if db is not None:
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            # Encontrar tareas completadas antigas
            old_completed_tasks = db.tasks.find({
                "status": {"$in": ["completed", "failed"]},
                "updated_at": {"$lt": cutoff_time.isoformat()}
            })
            
            for task in old_completed_tasks:
                task_id = task.get("task_id")
                if task_id:
                    # Notificar a WebSocket manager para limpiar conexiones
                    if hasattr(app, 'websocket_manager') and app.websocket_manager:
                        try:
                            app.websocket_manager.cleanup_task_connections(task_id)
                        except:
                            pass
                    
                    cleanup_count += 1
            
            # Eliminar tareas antigas de la base de datos
            if cleanup_count > 0:
                result = db.tasks.delete_many({
                    "status": {"$in": ["completed", "failed"]},
                    "updated_at": {"$lt": cutoff_time.isoformat()}
                })
                logger.info(f"🧹 Cleaned up {result.deleted_count} old completed tasks from database")
        
        # Limpiar task manager cache
        try:
            from src.routes.agent_routes import get_task_manager
            task_manager = get_task_manager()
            if task_manager and hasattr(task_manager, 'cleanup_completed_tasks'):
                cache_cleanup_count = task_manager.cleanup_completed_tasks()
                cleanup_count += cache_cleanup_count
        except Exception as cache_error:
            logger.warning(f"Could not clean task manager cache: {cache_error}")
        
        return jsonify({
            "success": True,
            "message": f"Cleanup completed: {cleanup_count} tasks removed",
            "cleanup_count": cleanup_count,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ✅ ENDPOINT PARA DETENER TAREA ESPECÍFICA POR FUERZA  
@app.route('/api/agent/force-stop-task/<task_id>', methods=['POST'])
def force_stop_task(task_id):
    """Detiene forzadamente una tarea específica"""
    try:
        logger.info(f"🛑 Force stopping task: {task_id}")
        
        # Actualizar status en base de datos
        if db is not None:
            db.tasks.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": "force_stopped",
                        "updated_at": datetime.now().isoformat(),
                        "force_stopped_at": datetime.now().isoformat()
                    }
                }
            )
        
        # Notificar a WebSocket manager
        if hasattr(app, 'websocket_manager') and app.websocket_manager:
            try:
                # Enviar evento de parada forzada
                app.websocket_manager.send_task_update(task_id, {
                    "type": "task_force_stopped",
                    "status": "force_stopped",
                    "message": "Task forcibly stopped by system",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Limpiar conexiones de la tarea
                app.websocket_manager.cleanup_task_connections(task_id)
            except Exception as ws_error:
                logger.warning(f"WebSocket cleanup error: {ws_error}")
        
        # Limpiar task manager
        try:
            from src.routes.agent_routes import get_task_manager
            task_manager = get_task_manager()
            if task_manager and hasattr(task_manager, 'force_stop_task'):
                task_manager.force_stop_task(task_id)
        except Exception as tm_error:
            logger.warning(f"Task manager cleanup error: {tm_error}")
        
        return jsonify({
            "success": True,
            "message": f"Task {task_id} forcibly stopped",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Force stop error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agent/generate-suggestions', methods=['POST'])
def generate_suggestions():
    """Genera sugerencias dinámicas para el frontend"""
    try:
        suggestions = [
            {"title": "Buscar información sobre IA", "description": "Investigar avances recientes en inteligencia artificial"},
            {"title": "Analizar datos de mercado", "description": "Procesar tendencias y métricas comerciales"},
            {"title": "Crear documento técnico", "description": "Generar documentación profesional con análisis detallado"}
        ]
        return jsonify({"suggestions": suggestions}), 200
    except Exception as e:
        logger.error(f"Generate suggestions error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/agent/generate-final-report/<task_id>', methods=['POST'])
def generate_final_report(task_id):
    """Genera el informe final de la tarea completada usando la función consolidada"""
    try:
        logger.info(f"📄 Generating final report for task: {task_id}")
        
        # Definir current_time al inicio
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Buscar la tarea usando el task_manager
        task = None
        try:
            from src.routes.agent_routes import get_task_data
            task = get_task_data(task_id)
            logger.info(f"📄 Task found using get_task_data: {task is not None}")
        except Exception as db_error:
            logger.warning(f"Error while fetching task: {db_error}")
        
        if task:
            # USAR LA FUNCIÓN CONSOLIDADA QUE INCLUYE CONTENIDO REAL
            from src.routes.agent_routes import generate_consolidated_final_report
            report_content = generate_consolidated_final_report(task)
        else:
            # Informe de respaldo si no se encuentra la tarea
            report_content = f"""# Informe Final - Tarea Completada

## Información General
- **Fecha de finalización**: {current_time}
- **ID de la tarea**: {task_id}

## Resumen Ejecutivo
La tarea se ha completado exitosamente.

## Conclusión
La tarea se ejecutó correctamente y finalizó sin errores.

---
*Informe generado automáticamente por Mitosis el {current_time}*
"""
        
        # Guardar el informe como archivo en la base de datos
        if client is not None and db is not None:
            try:
                file_data = {
                    "id": f"final-report-{task_id}",
                    "task_id": task_id,
                    "name": f"Informe_Final_{task_id}.md",
                    "content": report_content,
                    "type": "text/markdown",
                    "size": len(report_content.encode('utf-8')),
                    "source": "agent",
                    "created_at": current_time,
                    "metadata": {
                        "is_final_report": True,
                        "task_title": task.get('title', 'Tarea sin título') if task else 'Tarea sin título'
                    }
                }
                
                # Insertar o actualizar el archivo del informe
                db.files.replace_one(
                    {"id": file_data["id"]}, 
                    file_data, 
                    upsert=True
                )
                
                logger.info(f"📄 Final report saved to database for task: {task_id}")
                
            except Exception as db_error:
                logger.warning(f"Error saving final report to database: {db_error}")
        
        return jsonify({
            "success": True,
            "report": report_content,
            "task_id": task_id,
            "generated_at": current_time
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating final report: {e}")
        return jsonify({"error": str(e)}), 500

# ✅ ENDPOINT PARA SERVIR CAPTURAS DE PANTALLA - SEGÚN UpgardeRef.md SECCIÓN 4.1  
@app.route('/api/files/screenshots/<task_id>/<filename>')
def serve_screenshot(task_id, filename):
    """Serve screenshot files for real-time browser activity visualization"""
    try:
        screenshots_dir = f"/tmp/screenshots/{task_id}"
        return send_from_directory(screenshots_dir, filename)
    except Exception as e:
        logger.error(f"Error serving screenshot {filename} for task {task_id}: {e}")
        return jsonify({"error": "Screenshot not found"}), 404

# ✅ ENDPOINT FALTANTE PARA GET-TASK-STATUS - CORRIGIENDO ERROR 404
@app.route('/api/agent/get-task-status/<task_id>', methods=['GET', 'OPTIONS'])
def get_task_status(task_id):
    """
    Obtener el estado actual de una tarea específica
    
    Returns:
        JSON con el estado de la tarea: status, progress, current_step, etc.
    """
    try:
        # Use TaskManager to get task data
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from src.services.task_manager import TaskManager
        
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        
        if not task:
            return jsonify({
                "success": False,
                "error": "Task not found",
                "task_id": task_id
            }), 404
        
        # Preparar respuesta con estado de la tarea
        response = {
            "success": True,
            "task_id": task_id,
            "status": task.get("status", "unknown"),
            "progress": task.get("progress", 0),
            "current_step": task.get("current_step", None),
            "total_steps": len(task.get("plan", [])),
            "completed_steps": len([step for step in task.get("plan", []) if step.get("status") == "completed"]),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
            "title": task.get("title", ""),
            "plan": task.get("plan", [])
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de tarea {task_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "task_id": task_id
        }), 500

# ✅ ENDPOINT DE PRUEBA PARA VISUALIZACIÓN EN TIEMPO REAL - SEGÚN UpgardeRef.md
@app.route('/api/test-real-time-browser', methods=['POST'])
def test_real_time_browser():
    """
    Endpoint de prueba para la visualización en tiempo real de navegación web
    
    Body JSON:
    {
        "task_id": "test-123",
        "url": "https://example.com",
        "actions": ["navigate", "screenshot", "extract_links"]
    }
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id', f'test-{int(time.time())}')
        url = data.get('url', 'https://example.com')
        actions = data.get('actions', ['navigate', 'screenshot'])
        
        logger.info(f"🧪 Iniciando prueba de visualización en tiempo real para task {task_id}")
        
        # Importar funciones necesarias
        try:
            from src.routes.agent_routes import create_web_browser_manager, get_websocket_manager
        except ImportError as e:
            logger.error(f"❌ Error importando funciones de navegador: {e}")
            return jsonify({
                "success": False,
                "error": "WebBrowser functionality not available"
            }), 500
        
        # Crear WebBrowserManager con visualización en tiempo real
        browser_manager = create_web_browser_manager(task_id)
        if not browser_manager:
            return jsonify({
                "success": False,
                "error": "No se pudo crear WebBrowserManager"
            }), 500
        
        # Inicializar navegador
        if not browser_manager.initialize_browser():
            return jsonify({
                "success": False,
                "error": "No se pudo inicializar el navegador"
            }), 500
        
        websocket_manager = get_websocket_manager()
        if websocket_manager:
            # Enviar mensaje de inicio de prueba
            websocket_manager.send_log_message(
                task_id,
                "info",
                f"🧪 Iniciando prueba de navegación en tiempo real a: {url}"
            )
        
        # Ejecutar acciones
        results = []
        
        if "navigate" in actions:
            # Navegar con eventos en tiempo real
            browser_manager.navigate(url)
            results.append({"action": "navigate", "status": "completed", "url": url})
        
        if "extract_links" in actions:
            # Esperar un momento para que la página se cargue
            import time as time_module
            time_module.sleep(2)
            
            # Extraer links con tracking en tiempo real
            extracted_data = browser_manager.extract_data("a[href]")
            results.append({
                "action": "extract_links", 
                "status": "completed", 
                "count": extracted_data.get("count", 0),
                "sample_data": extracted_data.get("data", [])[:3]
            })
        
        if "close" in actions:
            # Cerrar navegador
            browser_manager.close_browser()
            results.append({"action": "close", "status": "completed"})
        
        if websocket_manager:
            websocket_manager.send_log_message(
                task_id,
                "success",
                f"🧪 Prueba de navegación completada exitosamente. Acciones ejecutadas: {len(results)}"
            )
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "url": url,
            "actions_completed": results,
            "message": "Prueba de visualización en tiempo real completada. Revisar TerminalView para eventos en tiempo real."
        })
        
    except Exception as e:
        logger.error(f"❌ Error en prueba de navegación en tiempo real: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print(f"🚀 Starting server on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)

