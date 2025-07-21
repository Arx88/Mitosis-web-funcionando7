#!/usr/bin/env python3
"""
Mitosis-Beta Enhanced Server - Servidor Principal con Ejecución Autónoma
Servidor Flask que integra el núcleo autónomo con salida en terminal
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

# Intentar usar la API mejorada primero
try:
    from enhanced_unified_api import EnhancedUnifiedMitosisAPI
    USE_ENHANCED_API = True
    print("🚀 Usando Enhanced Unified API con capacidades autónomas")
except ImportError as e:
    print(f"⚠️ Enhanced API no disponible: {e}")
    print("📍 Usando API base como fallback")
    USE_ENHANCED_API = False

# Configuración
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8001))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

if USE_ENHANCED_API:
    # Usar API mejorada
    print("✨ Inicializando Mitosis-Beta con capacidades autónomas mejoradas...")
    
    # Crear configuración
    config = {
        'OLLAMA_URL': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY', ''),
        'DEBUG_MODE': DEBUG,
        'HOST': HOST,
        'PORT': PORT
    }
    
    # Crear API mejorada
    enhanced_api = EnhancedUnifiedMitosisAPI(config)
    app = enhanced_api.app
    socketio = enhanced_api.socketio
    
    print("🎯 CARACTERÍSTICAS MEJORADAS HABILITADAS:")
    print("   ✅ Ejecución autónoma de tareas completas")
    print("   ✅ Salida en tiempo real en terminal formateada")
    print("   ✅ Monitoreo de progreso paso a paso automático")
    print("   ✅ Entrega de resultados finales estructurada")
    print("   ✅ Compatibilidad total con UI existente")
    print("   ✅ WebSockets para actualizaciones en tiempo real")
    
else:
    # Fallback al servidor original
    from src.routes.agent_routes import agent_bp
    from src.tools.tool_manager import ToolManager
    from src.services.ollama_service import OllamaService
    from src.services.database import DatabaseService
    from src.utils.json_encoder import MongoJSONEncoder
    from src.websocket.websocket_manager import initialize_websocket

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
                "https://8d16e29e-d31b-4df5-8776-8ccd6eb88863.preview.emergentagent.com",
                "*"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Inicializar WebSocket
    print("🔌 Initializing WebSocket for real-time updates...")
    websocket_manager = initialize_websocket(app)
    socketio = websocket_manager.socketio if websocket_manager else None
    print("✅ WebSocket initialized successfully")

    # Hacer WebSocket manager disponible globalmente
    app.websocket_manager = websocket_manager

    # Inicializar servicios
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    print(f"🧠 Inicializando Ollama con URL: {ollama_base_url}")
    ollama_service = OllamaService(base_url=ollama_base_url)
    tool_manager = ToolManager()
    database_service = DatabaseService()

    # Hacer servicios disponibles globalmente
    app.ollama_service = ollama_service
    app.tool_manager = tool_manager
    app.database_service = database_service

    # Registrar blueprints
    app.register_blueprint(agent_bp, url_prefix='/api/agent')

    # Importar rutas de memoria
    from src.routes.memory_routes import memory_bp
    app.register_blueprint(memory_bp, url_prefix='/api/memory')

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

# Servir archivos estáticos del frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print(f"🚀 Iniciando Mitosis-Beta Enhanced Server...")
    print(f"🔗 Host: {HOST}:{PORT}")
    print(f"🛠️  Debug: {DEBUG}")
    print(f"🔧 Puerto configurado: {PORT}")
    
    if USE_ENHANCED_API:
        print("🌟 Ejecutando con capacidades autónomas mejoradas")
        print("📊 Monitorea la terminal para ver actividad en tiempo real")
        print("🔗 La UI existente funcionará sin cambios")
        
        # Ejecutar con la API mejorada
        enhanced_api.run(host=HOST, port=PORT, debug=DEBUG)
    else:
        print("📍 Ejecutando con configuración base")
        
        # Verificar servicios base
        if 'ollama_service' in locals():
            if ollama_service.is_healthy():
                print("✅ Ollama conectado exitosamente")
            else:
                print("⚠️  Advertencia: No se pudo conectar a Ollama")
        
        if 'database_service' in locals():
            if database_service.is_connected():
                print("✅ MongoDB conectado exitosamente")
            else:
                print("⚠️  Advertencia: No se pudo conectar a MongoDB")
        
        # Ejecutar servidor
        if socketio:
            print("🔌 Starting server with WebSocket support...")
            socketio.run(app, host=HOST, port=PORT, debug=DEBUG, allow_unsafe_werkzeug=True)
        else:
            print("⚠️  WebSocket not initialized, starting without WebSocket support")
            app.run(host=HOST, port=PORT, debug=DEBUG)

# Hacer disponible para uvicorn
if USE_ENHANCED_API:
    # Para uvicorn cuando se usa la API mejorada, necesitamos export el app de Flask
    app = enhanced_api.app if 'enhanced_api' in locals() else app
else:
    # Para el servidor base, usar la aplicación Flask directamente
    pass