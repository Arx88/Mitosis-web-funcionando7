#!/usr/bin/env python3
"""
Servidor de prueba simplificado para testing del agente
"""

import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Importar servicios
from src.services.ollama_service import OllamaService
from src.tools.tool_manager import ToolManager

# Configuración
HOST = '0.0.0.0'
PORT = 8001
DEBUG = True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Inicializar servicios
ollama_service = OllamaService()
tool_manager = ToolManager()

# Hacer servicios disponibles globalmente
app.ollama_service = ollama_service
app.tool_manager = tool_manager

@app.route('/')
def home():
    return jsonify({
        'message': 'Mitosis Agent Backend - Test Server',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'ollama': ollama_service.is_healthy(),
            'tools': len(tool_manager.get_available_tools())
        }
    })

@app.route('/api/agent/status')
def agent_status():
    try:
        tools = tool_manager.get_available_tools()
        return jsonify({
            'status': 'ready',
            'ollama_status': 'connected' if ollama_service.is_healthy() else 'disconnected',
            'available_models': ollama_service.get_available_models(),
            'current_model': ollama_service.get_current_model(),
            'tools_count': len(tools),
            'tools': [tool['name'] for tool in tools]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/agent/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Generar respuesta usando Ollama
        response = ollama_service.generate_response(message, use_tools=True)
        
        # Procesar tool calls si existen
        tool_results = []
        if response.get('tool_calls'):
            for tool_call in response['tool_calls']:
                tool_name = tool_call.get('tool')
                parameters = tool_call.get('parameters', {})
                
                if tool_name:
                    result = tool_manager.execute_tool(tool_name, parameters)
                    tool_results.append({
                        'tool': tool_name,
                        'parameters': parameters,
                        'result': result
                    })
        
        return jsonify({
            'response': response.get('response', ''),
            'tool_calls': response.get('tool_calls', []),
            'tool_results': tool_results,
            'timestamp': datetime.now().isoformat(),
            'model': response.get('model', 'unknown')
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/agent/tools')
def get_tools():
    try:
        tools = tool_manager.get_available_tools()
        return jsonify({
            'tools': tools,
            'count': len(tools)
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/agent/tools/<tool_name>/execute', methods=['POST'])
def execute_tool(tool_name):
    try:
        data = request.get_json()
        parameters = data.get('parameters', {})
        
        result = tool_manager.execute_tool(tool_name, parameters)
        
        return jsonify({
            'tool': tool_name,
            'parameters': parameters,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'tool': tool_name,
            'timestamp': datetime.now().isoformat()
        }), 500

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print(f"🚀 Iniciando Test Server...")
    print(f"🔗 Host: {HOST}:{PORT}")
    print(f"🛠️  Debug: {DEBUG}")
    
    # Verificar conexión con Ollama
    if ollama_service.is_healthy():
        print("✅ Ollama conectado exitosamente")
        models = ollama_service.get_available_models()
        print(f"📚 Modelos disponibles: {models}")
    else:
        print("⚠️  Advertencia: Ollama en modo simulado")
    
    # Mostrar herramientas disponibles
    tools = tool_manager.get_available_tools()
    print(f"🔧 Herramientas disponibles: {len(tools)}")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")
    
    print("🎯 Servidor listo para recibir conexiones")
    app.run(host=HOST, port=PORT, debug=DEBUG)

