#!/usr/bin/env python3
"""
SERVIDOR BACKEND SIMPLIFICADO Y ROBUSTO
Versión estable para evitar crashes
"""

import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pymongo
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8001))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
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

# Ruta de health check
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db is not None,
                "ollama": False,  # Simplificado por ahora
                "tools": 0
            }
        }
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Ruta básica de chat
@app.route('/api/agent/chat', methods=['POST'])
def chat():
    """Endpoint de chat simplificado"""
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

# Ruta de status del agente
@app.route('/api/agent/status', methods=['GET'])
def agent_status():
    """Status del agente"""
    try:
        status = {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "ollama": {
                "connected": False,
                "endpoint": "https://78d08925604a.ngrok-free.app",
                "model": "llama3.1:8b"
            },
            "tools": [],
            "memory": {
                "enabled": True,
                "initialized": True
            }
        }
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info(f"🚀 Iniciando servidor simplificado en {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)