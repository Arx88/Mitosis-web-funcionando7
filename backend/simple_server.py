#!/usr/bin/env python3
"""
Servidor simple para depurar problemas
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

# Añadir directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Crear app Flask
app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check básico"""
    return jsonify({
        "status": "healthy",
        "server": "simple",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        "message": "Server is working",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    print("Starting simple server...")
    app.run(host='0.0.0.0', port=8001, debug=False)