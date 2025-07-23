#!/usr/bin/env python3
"""
Simple Flask WSGI Server - SOLUCIÓN DIRECTA
Simplemente usa Flask app para gunicorn, SocketIO por separado si es necesario
"""

import os
import sys
sys.path.insert(0, '/app/backend')

# Importar solo la Flask app
from server import app

# Para gunicorn - simplemente la Flask app
application = app

if __name__ == '__main__':
    # Para testing directo con SocketIO
    from server import socketio
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)