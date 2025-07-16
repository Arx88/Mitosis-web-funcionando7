#!/usr/bin/env python3
"""
Task Manager - Backend Principal
Servidor Flask que integra Ollama con un sistema de herramientas extensible
"""

import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar módulos del agente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.routes.agent_routes import agent_bp
from src.tools.tool_manager import ToolManager
from src.services.ollama_service import OllamaService
from src.services.database import DatabaseService
from src.utils.json_encoder import MongoJSONEncoder
from src.websocket.websocket_manager import initialize_websocket

# Configuración
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8001))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.json_encoder = MongoJSONEncoder

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000", 
            "http://localhost:5173",
            "https://55d42e38-7068-412e-8a40-007797d2661f.preview.emergentagent.com",
            "*"  # Allow all origins for now to fix connectivity issues
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 🚀 Inicializar WebSocket para updates en tiempo real
print("🔌 Initializing WebSocket for real-time updates...")
websocket_manager = initialize_websocket(app)
print("✅ WebSocket initialized successfully")

# Inicializar servicios con configuración correcta
ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
print(f"🧠 Inicializando Ollama con URL: {ollama_base_url}")
ollama_service = OllamaService(base_url=ollama_base_url)
tool_manager = ToolManager()
database_service = DatabaseService()

# Inicializar Enhanced Components
print("🚀 Inicializando Enhanced Components...")
try:
    # Importar desde el directorio raíz del backend
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from enhanced_agent_core import EnhancedMitosisAgent
    from enhanced_memory_manager import EnhancedMemoryManager
    from enhanced_task_manager import EnhancedTaskManager
    
    # Crear enhanced components
    enhanced_memory = EnhancedMemoryManager()
    enhanced_task_manager = EnhancedTaskManager(enhanced_memory)
    enhanced_agent = EnhancedMitosisAgent()
    
    print("✅ Enhanced components inicializados exitosamente")
except ImportError as e:
    print(f"⚠️ Error importando enhanced components: {e}")
    enhanced_agent = None
    enhanced_memory = None
    enhanced_task_manager = None
except Exception as e:
    print(f"⚠️ Error inicializando enhanced components: {e}")
    enhanced_agent = None
    enhanced_memory = None
    enhanced_task_manager = None

# Hacer servicios disponibles globalmente
app.ollama_service = ollama_service
app.tool_manager = tool_manager
app.database_service = database_service

# Hacer enhanced components disponibles globalmente
app.enhanced_agent = enhanced_agent
app.enhanced_memory = enhanced_memory
app.enhanced_task_manager = enhanced_task_manager

# Registrar blueprints
app.register_blueprint(agent_bp, url_prefix='/api/agent')

# Servir archivos estáticos del frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Endpoint de salud
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'ollama': ollama_service.is_healthy(),
            'tools': len(tool_manager.get_available_tools()),
            'database': database_service.is_connected()
        }
    })

# Endpoint de estadísticas de la base de datos
@app.route('/api/stats')
def get_stats():
    stats = database_service.get_stats()
    return jsonify(stats)

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Convertir Flask WSGI app a ASGI para uvicorn
try:
    from asgiref.wsgi import WsgiToAsgi
    
    # Crear aplicación ASGI
    asgi_app = WsgiToAsgi(app)
    
except ImportError:
    # Si asgiref no está disponible, mantener la aplicación Flask
    print("asgiref not available, using Flask directly")
    asgi_app = app

if __name__ == '__main__':
    print(f"🚀 Iniciando Task Manager Backend...")
    print(f"🔗 Host: {HOST}:{PORT}")
    print(f"🛠️  Debug: {DEBUG}")
    print(f"🔧 Puerto configurado: {PORT}")
    print(f"🧠 Conectando a Ollama...")
    
    # Verificar conexión con Ollama
    if ollama_service.is_healthy():
        print("✅ Ollama conectado exitosamente")
        models = ollama_service.get_available_models()
        print(f"📚 Modelos disponibles: {models}")
    else:
        print("⚠️  Advertencia: No se pudo conectar a Ollama")
        print("   Asegúrate de que Ollama esté ejecutándose en localhost:11434")
    
    # Verificar conexión con MongoDB
    if database_service.is_connected():
        print("✅ MongoDB conectado exitosamente")
        stats = database_service.get_stats()
        print(f"📊 Estadísticas DB: {stats}")
    else:
        print("⚠️  Advertencia: No se pudo conectar a MongoDB")
    
    # Mostrar herramientas disponibles
    tools = tool_manager.get_available_tools()
    print(f"🔧 Herramientas disponibles: {len(tools)}")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")
    
    print("🎯 Servidor listo para recibir conexiones")
    
    # 🚀 Ejecutar con SocketIO
    socketio = websocket_manager.socketio
    if socketio:
        print("🔌 Starting server with WebSocket support...")
        socketio.run(app, host=HOST, port=PORT, debug=DEBUG, allow_unsafe_werkzeug=True)
    else:
        print("⚠️  WebSocket not initialized, starting without WebSocket support")
        app.run(host=HOST, port=PORT, debug=DEBUG)

# Hacer disponible para uvicorn
app = asgi_app