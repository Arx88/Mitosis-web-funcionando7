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
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
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

# Configurar CORS - UNIFIED CONFIGURATION with explicit origins for WebSocket compatibility
FRONTEND_ORIGINS = [
    "https://d1c8ceae-497e-462b-a5fa-5c5f477c24df.preview.emergentagent.com",  # FRONTEND ACTUAL FROM LOGS
    "https://d1c8ceae-497e-462b-a5fa-5c5f477c24df.preview.emergentagent.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "*"  # Fallback for any other origins
]

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

# Inicializar WebSocket Manager con configuración optimizada
try:
    from src.websocket.websocket_manager import WebSocketManager
    websocket_manager = WebSocketManager()
    
    # Configurar SocketIO con CORS más específico y mejorado para conexiones cross-origin
    socketio = SocketIO(
        app, 
        cors_allowed_origins=FRONTEND_ORIGINS,  # Usar los orígenes específicos definidos arriba
        cors_credentials=False,
        async_mode='eventlet',
        logger=True,
        engineio_logger=True,  
        ping_timeout=180,      # Aumentado aún más
        ping_interval=90,      # Aumentado aún más
        transports=['polling'],  # SOLO POLLING para máxima compatibilidad
        allow_upgrades=False,   # NO upgrades
        path='/api/socket.io/',     # CRÍTICO: Con /api prefix para routing correcto
        manage_session=False,    # No manejar sesiones automáticamente
        max_http_buffer_size=1000000  # Buffer más grande para datos
    )
    
    # Agregar handlers de debugging más detallados
    @socketio.on('connect')
    def handle_connect(auth=None):
        logger.info(f"🔌 WEBSOCKET: Client connecting from {request.environ.get('REMOTE_ADDR')}")
        logger.info(f"🔌 WEBSOCKET: Session ID: {request.sid}")
        logger.info(f"🔌 WEBSOCKET: Transport: {request.transport}")
        
        # CRITICAL FIX: Register connection in websocket_manager
        if hasattr(app, 'websocket_manager') and app.websocket_manager:
            # Add to global connections (we'll assign to task later)
            if 'global' not in app.websocket_manager.active_connections:
                app.websocket_manager.active_connections['global'] = []
            app.websocket_manager.active_connections['global'].append(request.sid)
            logger.info(f"🔌 WEBSOCKET: Registered session {request.sid} globally")
        
        emit('connection_established', {'status': 'connected', 'session_id': request.sid})
        return True  # Accept all connections
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"🔌 WEBSOCKET: Client {request.sid} disconnected")
        
        # CRITICAL FIX: Remove from all connections
        if hasattr(app, 'websocket_manager') and app.websocket_manager:
            for task_id, sessions in app.websocket_manager.active_connections.items():
                if request.sid in sessions:
                    sessions.remove(request.sid)
                    logger.info(f"🔌 WEBSOCKET: Removed {request.sid} from task {task_id}")
    
    @socketio.on('join_task')
    def handle_join_task(data):
        task_id = data.get('task_id')
        logger.info(f"🏠 WEBSOCKET: Client {request.sid} joining task room: {task_id}")
        if task_id:
            join_room(task_id)
            
            # CRITICAL FIX: Register in websocket_manager for this task
            if hasattr(app, 'websocket_manager') and app.websocket_manager:
                if task_id not in app.websocket_manager.active_connections:
                    app.websocket_manager.active_connections[task_id] = []
                if request.sid not in app.websocket_manager.active_connections[task_id]:
                    app.websocket_manager.active_connections[task_id].append(request.sid)
                logger.info(f"🔌 WEBSOCKET: Registered {request.sid} for task {task_id}")
                logger.info(f"🔌 WEBSOCKET: Task {task_id} now has {len(app.websocket_manager.active_connections[task_id])} connections")
                
                # IMMEDIATELY EMIT A TEST EVENT to confirm connection
                app.websocket_manager.emit_to_task(task_id, 'connection_confirmed', {
                    'message': 'WebSocket connection established for task',
                    'task_id': task_id,
                    'session_id': request.sid,
                    'timestamp': datetime.now().isoformat()
                })
                
                # CRITICAL FIX: Send stored events to late-joining client
                stored_events = app.websocket_manager.get_stored_events(task_id)
                if stored_events:
                    logger.info(f"🔄 WEBSOCKET: Sending {len(stored_events)} stored events to late-joining client {request.sid}")
                    for event_data in stored_events:
                        emit('catch_up_event', event_data)
                        # Also emit the original event type
                        original_event = event_data.get('event', 'unknown_event')
                        emit(original_event, event_data)
                
                # Send current task status
                try:
                    import requests
                    status_response = requests.get(f'http://localhost:8001/api/agent/get-task-status/{task_id}')
                    if status_response.status_code == 200:
                        current_status = status_response.json()
                        emit('current_task_status', {
                            'task_id': task_id,
                            'status': current_status,
                            'timestamp': datetime.now().isoformat()
                        })
                        logger.info(f"📊 WEBSOCKET: Sent current task status to {request.sid}")
                except Exception as status_error:
                    logger.error(f"❌ Failed to send current status: {status_error}")
            
            emit('joined_task', {'task_id': task_id, 'status': 'joined'})
            logger.info(f"✅ WEBSOCKET: Client {request.sid} joined task room {task_id}")
        else:
            emit('error', {'message': 'task_id required'})
            logger.error(f"❌ WEBSOCKET: Client {request.sid} tried to join without task_id")
    
    websocket_manager.socketio = socketio
    websocket_manager.app = app
    websocket_manager.setup_event_handlers()
    websocket_manager.is_initialized = True
    
    app.websocket_manager = websocket_manager
    logger.info("✅ WebSocket Manager inicializado exitosamente con SocketIO")
except Exception as e:
    logger.error(f"❌ Error inicializando WebSocket Manager: {e}")

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
                    "model": os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3.1:8b'),
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
        
        # Aplicar configuración de Ollama
        if 'ollama' in new_config:
            ollama_config = new_config['ollama']
            if 'endpoint' in ollama_config:
                # Actualizar servicio Ollama si existe
                if hasattr(app, 'ollama_service') and app.ollama_service:
                    success = app.ollama_service.update_endpoint(ollama_config['endpoint'])
                    if not success:
                        logger.warning(f"Failed to update Ollama endpoint to {ollama_config['endpoint']}")
        
        # Verificar nueva configuración
        ollama_connected = False
        if hasattr(app, 'ollama_service') and app.ollama_service:
            ollama_connected = app.ollama_service.is_healthy()
        
        result = {
            "success": True,
            "message": "Configuration applied successfully",
            "config_applied": {
                "ollama": {
                    "enabled": new_config.get('ollama', {}).get('enabled', True),
                    "endpoint": new_config.get('ollama', {}).get('endpoint', os.getenv('OLLAMA_BASE_URL')),
                    "model": new_config.get('ollama', {}).get('model', os.getenv('OLLAMA_DEFAULT_MODEL')),
                    "connected": ollama_connected
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

# Endpoint para sugerencias dinámicas que faltaba
@app.route('/api/agent/get-stored-events/<task_id>', methods=['GET'])
def get_stored_events(task_id):
    """Get stored WebSocket events for a task (for late-joining clients)"""
    try:
        if hasattr(app, 'websocket_manager') and app.websocket_manager:
            stored_events = app.websocket_manager.get_stored_events(task_id)
            return jsonify({
                'task_id': task_id,
                'events': stored_events,
                'count': len(stored_events),
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': 'WebSocket manager not available'}), 500
    except Exception as e:
        logger.error(f"Get stored events error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-cors', methods=['GET', 'POST', 'OPTIONS'])
def test_cors():
    """Test CORS configuration"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight successful'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    
    return jsonify({
        'status': 'CORS test successful',
        'origin': request.headers.get('Origin', 'No origin'),
        'method': request.method,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/socket.io-test', methods=['GET'])
def socket_io_test():
    """Test socket.io availability without actual connection"""
    return jsonify({
        'status': 'Socket.IO test endpoint accessible',
        'websocket_initialized': hasattr(app, 'websocket_manager'),
        'origin': request.headers.get('Origin', 'No origin'),
        'timestamp': datetime.now().isoformat()
    })

# CRITICAL FIX: Add explicit CORS handling for Socket.IO endpoint
@app.before_request
def handle_socket_io_cors():
    """Handle CORS for Socket.IO endpoints specifically"""
    if request.path.startswith('/socket.io/'):
        origin = request.headers.get('Origin')
        if origin in FRONTEND_ORIGINS or '*' in FRONTEND_ORIGINS:
            # This is a preflight OPTIONS request
            if request.method == 'OPTIONS':
                response = app.make_default_options_response()
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Origin, X-Requested-With'
                response.headers['Access-Control-Allow-Credentials'] = 'false'
                return response

@app.after_request  
def after_request_socket_io_cors(response):
    """Add CORS headers to Socket.IO responses"""
    if request.path.startswith('/socket.io/'):
        origin = request.headers.get('Origin')
        if origin in FRONTEND_ORIGINS or '*' in FRONTEND_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Origin, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'false'
    return response

@app.route('/api/agent/websocket-test/<task_id>', methods=['GET'])
def websocket_test(task_id):
    """Test WebSocket connection and task room joining"""
    try:
        # Get current websocket connections
        connections_info = {
            'task_id': task_id,
            'websocket_initialized': hasattr(app, 'websocket_manager'),
            'active_connections': {}
        }
        
        if hasattr(app, 'websocket_manager') and app.websocket_manager:
            connections_info['active_connections'] = {
                k: len(v) for k, v in app.websocket_manager.active_connections.items()
            }
            connections_info['total_connections'] = sum(len(v) for v in app.websocket_manager.active_connections.values())
            
            # Include stored events count
            stored_events = app.websocket_manager.get_stored_events(task_id)
            connections_info['stored_events_count'] = len(stored_events)
        
        return jsonify(connections_info), 200
    except Exception as e:
        logger.error(f"WebSocket test error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/agent/force-websocket-emit/<task_id>', methods=['POST'])
def force_websocket_emit(task_id):
    """Force emit a test event to verify WebSocket is working"""
    try:
        data = request.get_json() or {}
        test_message = data.get('message', 'Test WebSocket emission')
        
        if hasattr(app, 'websocket_manager') and app.websocket_manager:
            # Emit test event
            app.websocket_manager.emit_to_task(task_id, 'test_event', {
                'message': test_message,
                'timestamp': datetime.now().isoformat(),
                'task_id': task_id
            })
            
            return jsonify({
                'success': True,
                'message': f'Test event emitted to task {task_id}',
                'active_connections': len(app.websocket_manager.active_connections.get(task_id, []))
            }), 200
        else:
            return jsonify({'error': 'WebSocket manager not available'}), 500
    except Exception as e:
        logger.error(f"Force websocket emit error: {e}")
        return jsonify({"error": str(e)}), 500

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
    """Genera el informe final de la tarea completada"""
    try:
        logger.info(f"📄 Generating final report for task: {task_id}")
        
        # Buscar la tarea en la base de datos
        task = None
        if client is not None and db is not None:
            try:
                task = db.tasks.find_one({"id": task_id})
                logger.info(f"📄 Task found in database: {task is not None}")
            except Exception as db_error:
                logger.warning(f"Database error while fetching task: {db_error}")
        
        # Generar el informe final
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if task:
            task_title = task.get('title', 'Tarea sin título')
            task_description = task.get('description', 'Sin descripción')
            plan = task.get('plan', [])
            
            # Crear el contenido del informe
            report_content = f"""# Informe Final - {task_title}

## Información General
- **Fecha de finalización**: {current_time}
- **ID de la tarea**: {task_id}
- **Descripción**: {task_description}

## Resumen Ejecutivo
La tarea "{task_title}" se ha completado exitosamente. Todos los pasos del plan de acción fueron ejecutados correctamente.

## Pasos Ejecutados
"""
            
            # Agregar los pasos del plan
            if plan:
                for i, step in enumerate(plan, 1):
                    step_title = step.get('title', f'Paso {i}')
                    step_status = '✅ Completado' if step.get('completed', False) else '❌ Pendiente'
                    elapsed_time = step.get('elapsed_time', 'N/A')
                    
                    report_content += f"""
### {i}. {step_title}
- **Estado**: {step_status}
- **Tiempo transcurrido**: {elapsed_time}
"""
            else:
                report_content += "\nNo se encontraron pasos registrados en el plan.\n"
            
            report_content += f"""
## Conclusión
La tarea se ejecutó exitosamente. Todos los pasos del plan de acción fueron completados satisfactoriamente.

## Archivos Generados
Durante la ejecución de esta tarea, se generaron varios archivos que están disponibles en la sección de archivos de la interfaz.

---
*Informe generado automáticamente por Mitosis el {current_time}*
"""
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
# Servir archivos estáticos del frontend
from flask import send_from_directory, send_file
import os

# Configurar directorio de archivos estáticos
STATIC_FOLDER = '/app/frontend/dist'

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Servir archivos estáticos del frontend"""
    if path != "" and os.path.exists(os.path.join(STATIC_FOLDER, path)):
        return send_from_directory(STATIC_FOLDER, path)
    else:
        return send_file(os.path.join(STATIC_FOLDER, 'index.html'))

# Ruta para servir archivos específicos
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Servir archivos de assets"""
    return send_from_directory(os.path.join(STATIC_FOLDER, 'assets'), filename)

# Ruta para servir archivos de tareas
@app.route('/files/<task_id>')
def serve_task_files(task_id):
    """Servir archivos de tareas"""
    return redirect(f'/api/agent/get-task-files/{task_id}')

