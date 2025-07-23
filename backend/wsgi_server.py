#!/usr/bin/env python3
"""
WSGI Server para Flask + SocketIO - SOLUCIÓN DEFINITIVA CORRECTA
Usa el middleware SocketIO correctamente
"""

import os
import sys
sys.path.insert(0, '/app/backend')

from server import app, socketio

# Para gunicorn con eventlet - usar el middleware de SocketIO
def application(environ, start_response):
    return socketio.wsgi_app(environ, start_response)

if __name__ == '__main__':
    # Para testing directo
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
