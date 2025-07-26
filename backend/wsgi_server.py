#!/usr/bin/env python3
"""
WSGI Server para Flask + SocketIO - SOLUCIÓN DEFINITIVA CORRECTA
Compatible con gunicorn + eventlet worker
"""

import os
import sys
sys.path.insert(0, '/app/backend')

# Importar la aplicación ya configurada
from server import app, socketio

# Para gunicorn, necesitamos el objeto de la aplicación WSGI
# Usar app de Flask directamente ya que socketio se maneja internamente
application = app

if __name__ == '__main__':
    # Para testing directo
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
