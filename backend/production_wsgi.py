#!/usr/bin/env python3
"""
Production WSGI Server - OPTIMIZADO PARA MODO PRODUCCIÓN
Usa SocketIO app con gunicorn + eventlet para máxima compatibilidad WebSocket
"""

import os
import sys
sys.path.insert(0, '/app/backend')

# Configurar variables de entorno para producción
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Importar la Flask app y socketio
from server import app, socketio

# CRÍTICO: Para gunicorn con eventlet + SocketIO
# Usar SocketIO como wrapper de la app Flask 
def application(environ, start_response):
    """WSGI callable que funciona con gunicorn + eventlet + SocketIO"""
    return socketio.wsgi_app(environ, start_response)

if __name__ == '__main__':
    # Para testing directo con SocketIO
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
