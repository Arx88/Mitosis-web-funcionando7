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

# Para gunicorn con eventlet y SocketIO - usar el app directamente
# SocketIO se integra automáticamente con el app Flask
application = app

# Debug logging para verificar configuración
import logging
logger = logging.getLogger(__name__)
logger.info(f"🔧 WSGI Application configured: {type(application)}")
logger.info(f"🔧 SocketIO integrated with Flask app")
logger.info(f"🔧 SocketIO path configured: /api/socket.io/")

if __name__ == '__main__':
    # Para testing directo con SocketIO
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
