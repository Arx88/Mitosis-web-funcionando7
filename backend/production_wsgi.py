#!/usr/bin/env python3
"""
Production WSGI Server - OPTIMIZADO PARA MODO PRODUCCIÓN
Usa Flask app con SocketIO para máxima compatibilidad WebSocket
"""

import os
import sys
sys.path.insert(0, '/app/backend')

# Configurar variables de entorno para producción
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Importar la Flask app (SocketIO ya está integrado en ella)
from server import app

# CRÍTICO: Para gunicorn con eventlet + SocketIO en Flask-SocketIO 5.x
# El objeto app ya tiene SocketIO integrado
application = app

if __name__ == '__main__':
    # Para testing directo
    from server import socketio
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
