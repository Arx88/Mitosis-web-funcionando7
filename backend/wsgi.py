#!/usr/bin/env python3
"""
Wrapper WSGI para el servidor Mitosis
Asegura compatibilidad con uvicorn y ASGI
"""

import os
import sys
from typing import Any

# Añadir directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Importar el servidor
from server import main

# Variable global para error
init_error_msg = None

# Crear la aplicación
try:
    print("🚀 Inicializando aplicación WSGI para Mitosis...")
    app = main()
    if app is None:
        raise Exception("La función main() retornó None")
    print("✅ Aplicación WSGI inicializada exitosamente")
except Exception as init_error:
    print(f"❌ Error inicializando aplicación WSGI: {init_error}")
    init_error_msg = str(init_error)
    # Crear app de emergencia
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return {"status": "error", "message": f"WSGI init failed: {init_error_msg}"}
    
    @app.route('/api/health')  
    def api_health():
        return {"status": "error", "message": f"WSGI init failed: {init_error_msg}"}

if __name__ == "__main__":
    # Ejecutar con Flask development server para testing
    app.run(host='0.0.0.0', port=8001, debug=True)