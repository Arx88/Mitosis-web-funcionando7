#!/usr/bin/env python3
"""
New intelligent planning endpoint that bypasses the broken code
"""
import sys
import os
import time
sys.path.append('/app/backend')

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["*"]}})

# Import our intelligent planner
from src.utils.intelligent_planner import generate_intelligent_plan

# Import Ollama service
sys.path.append('/app/backend/src')
from services.ollama_service import OllamaService

@app.route('/api/intelligent-plan', methods=['POST'])
def generate_intelligent_plan_endpoint():
    """Generate intelligent plan using the new planner"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', '') or data.get('task_title', '')
        task_id = data.get('task_id', f'task-{int(time.time())}')
        
        if not message:
            return jsonify({'error': 'Message or task_title required'}), 400
        
        logger.info(f"🧠 Generating intelligent plan for: {message[:50]}...")
        
        # Initialize Ollama service
        ollama_service = OllamaService()
        
        # Generate intelligent plan
        result = generate_intelligent_plan(message, task_id, ollama_service)
        
        logger.info(f"✅ Intelligent plan generated successfully")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error in intelligent planning: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health-check', methods=['GET'])
def health_check():
    """Simple health check"""
    return jsonify({'status': 'healthy', 'service': 'intelligent_planner'})

if __name__ == '__main__':
    print("🧠 Starting Intelligent Planning Service...")
    app.run(host='0.0.0.0', port=8002, debug=False)