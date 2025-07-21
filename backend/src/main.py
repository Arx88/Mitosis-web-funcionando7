#!/usr/bin/env python3
"""
Agente General - Backend Principal
Servidor Flask que integra Ollama con un sistema de herramientas extensible
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar módulos del agente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routes.agent_routes import agent_bp
from tools.tool_manager import ToolManager
from services.ollama_service import OllamaService
from services.database import DatabaseService

# Configuración
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8001))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Inicializar servicios
ollama_service = OllamaService()
tool_manager = ToolManager()
database_service = DatabaseService()

# Inicializar sistema de memoria avanzado
try:
    from memory.advanced_memory_manager import AdvancedMemoryManager
    memory_manager = AdvancedMemoryManager()
    logger.info("✅ Advanced Memory Manager initialized")
except Exception as e:
    logger.warning(f"⚠️ Could not initialize Advanced Memory Manager: {e}")
    memory_manager = None

# Inicializar gestor de contexto inteligente
# Mejora implementada según UPGRADE.md Sección 1: Sistema de Contexto Dinámico Avanzado
try:
    from context.intelligent_context_manager import IntelligentContextManager
    intelligent_context_manager = IntelligentContextManager(
        memory_manager=memory_manager,
        task_manager=None,  # TODO: Implementar task_manager cuando esté disponible
        model_manager=ollama_service  # Usar ollama_service como model_manager
    )
    logger.info("✅ Intelligent Context Manager initialized")
except Exception as e:
    logger.warning(f"⚠️ Could not initialize Intelligent Context Manager: {e}")
    intelligent_context_manager = None

# Inicializar WebSocket manager para comunicación en tiempo real
# Mejora implementada según UPGRADE.md Sección 3: WebSockets para Comunicación en Tiempo Real
from websocket.websocket_manager import initialize_websocket
websocket_manager = initialize_websocket(app)

# Hacer servicios disponibles globalmente
app.ollama_service = ollama_service
app.tool_manager = tool_manager
app.database_service = database_service
app.websocket_manager = websocket_manager
app.memory_manager = memory_manager
app.intelligent_context_manager = intelligent_context_manager

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
@app.route('/api/health')
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

if __name__ == '__main__':
    print(f"🚀 Iniciando Agente General Backend...")
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
        print("   Verifica la configuración del endpoint de Ollama en el archivo .env")
    
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
    print("🔗 WebSocket support enabled for real-time updates")
    
    # Usar SocketIO run para soporte WebSocket
    if websocket_manager and websocket_manager.socketio:
        websocket_manager.socketio.run(app, host=HOST, port=PORT, debug=DEBUG)
    else:
        print("⚠️ WebSocket manager not available, falling back to regular Flask")
        app.run(host=HOST, port=PORT, debug=DEBUG)