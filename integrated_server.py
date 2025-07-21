#!/usr/bin/env python3
"""
SERVIDOR INTEGRADO FRONTEND + BACKEND
Sirve el frontend y el backend desde el mismo puerto para evitar CORS
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
import subprocess

# Añadir el backend al path
sys.path.append('/app/backend')
sys.path.append('/app/backend/src')

from backend.server import app as backend_app, socketio as backend_socketio

# Crear app integrada
integrated_app = Flask(__name__, static_folder='/app/frontend/build', static_url_path='')

# Configurar CORS
CORS(integrated_app, resources={r"/*": {"origins": "*"}})

# Inicializar SocketIO
integrated_socketio = SocketIO(integrated_app, cors_allowed_origins="*")

# Registrar todas las rutas del backend
@integrated_app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def backend_proxy(path):
    """Proxy para rutas del backend"""
    try:
        with backend_app.test_client() as client:
            # Reenviar la solicitud al backend
            if request.method == 'GET':
                response = client.get(f'/api/{path}', 
                                    headers=dict(request.headers),
                                    query_string=request.query_string)
            elif request.method == 'POST':
                response = client.post(f'/api/{path}',
                                     data=request.get_data(),
                                     headers=dict(request.headers),
                                     content_type=request.content_type)
            elif request.method == 'PUT':
                response = client.put(f'/api/{path}',
                                    data=request.get_data(),
                                    headers=dict(request.headers),
                                    content_type=request.content_type)
            elif request.method == 'DELETE':
                response = client.delete(f'/api/{path}',
                                       headers=dict(request.headers))
            elif request.method == 'OPTIONS':
                return jsonify({}), 200
                
            return response.get_data(), response.status_code, dict(response.headers)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Servir frontend
@integrated_app.route('/')
def serve_frontend():
    """Servir el frontend"""
    return send_from_directory('/app/frontend/build', 'index.html')

@integrated_app.route('/<path:path>')
def serve_static(path):
    """Servir archivos estáticos del frontend"""
    try:
        return send_from_directory('/app/frontend/build', path)
    except:
        # Si no encuentra el archivo, servir index.html para SPA routing
        return send_from_directory('/app/frontend/build', 'index.html')

if __name__ == '__main__':
    print("🚀 Iniciando servidor integrado...")
    integrated_socketio.run(integrated_app, host='0.0.0.0', port=3000, debug=True)