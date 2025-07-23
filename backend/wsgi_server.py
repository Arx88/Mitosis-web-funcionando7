#!/usr/bin/env python3
"""
WSGI Server para Flask + SocketIO - SOLUCIÓN DEFINITIVA
Usa gunicorn con eventlet worker para compatibilidad completa
"""

import os
import sys
sys.path.insert(0, '/app/backend')

from server import app, socketio

# Para gunicorn con eventlet - SocketIO wraps the Flask app
application = socketio

if __name__ == '__main__':
    # Para testing directo
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
