#!/usr/bin/env python3
"""
WSGI Server para Flask + SocketIO - SOLUCIÓN DEFINITIVA CORRECTA
Compatible con gunicorn + eventlet worker
"""

import os
import sys
sys.path.insert(0, '/app/backend')

# Importar la aplicación ya configurada
from server import socketio

# El socketio object ya envuelve la Flask app y es WSGI-compatible
application = socketio

if __name__ == '__main__':
    # Para testing directo
    from server import app
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
