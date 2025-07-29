#!/usr/bin/env python3
"""
Production WSGI Server - OPTIMIZADO PARA MODO PRODUCCIÓN
Usa Flask app con gunicorn + eventlet para máxima compatibilidad SocketIO
"""

import os
import sys
sys.path.insert(0, '/app/backend')

# Configurar variables de entorno para producción
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Importar la Flask app y socketio
from server import app, socketio

# Para gunicorn con eventlet - configuración correcta
# El SocketIO maneja el WSGI automáticamente cuando se usa con gunicorn
application = app

# Aplicar SocketIO al app para que funcione con gunicorn
if hasattr(socketio, 'wsgi_app'):
    application = socketio.wsgi_app
else:
    # Alternativa si wsgi_app no existe
    application = app

if __name__ == '__main__':
    # Para testing directo con SocketIO
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
