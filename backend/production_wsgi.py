#!/usr/bin/env python3
"""
Production WSGI Server - OPTIMIZADO PARA SOCKETIO CON GUNICORN
Configuración correcta para Flask-SocketIO con eventlet worker
"""

import os
import sys
sys.path.insert(0, '/app/backend')

# Configurar variables de entorno para producción
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Importar la Flask app y socketio
from server import app, socketio

# CONFIGURACIÓN CORRECTA PARA FLASK-SOCKETIO CON GUNICORN + EVENTLET
# Usar socketio.wsgi_app para que funcione correctamente con WebSockets
application = socketio.wsgi_app

if __name__ == '__main__':
    # Para testing directo con SocketIO
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
