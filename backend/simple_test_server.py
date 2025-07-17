#!/usr/bin/env python3
"""
Simple test server to demonstrate autonomous web navigation
"""

import sys
import os
sys.path.append('/app/backend/src')
sys.path.append('/app/backend')

from flask import Flask, request, jsonify
from flask_cors import CORS
from src.tools.tool_manager import ToolManager
import json
import time

app = Flask(__name__)
CORS(app)

# Initialize tool manager
tool_manager = ToolManager()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

@app.route('/api/agent/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for testing autonomous web navigation
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        print(f"🎯 RECEIVED MESSAGE: {message}")
        
        # Detect if it's a web navigation task
        nav_keywords = ['navega', 'navigate', 'abre', 'open', 'visita', 'visit', 've a', 'go to', 
                       'twitter', 'facebook', 'instagram', 'github', 'google', 'stackoverflow']
        
        is_nav_task = any(keyword in message.lower() for keyword in nav_keywords)
        
        if is_nav_task:
            print("🌐 DETECTED WEB NAVIGATION TASK")
            
            # Execute autonomous web navigation
            result = tool_manager.execute_tool(
                'autonomous_web_navigation',
                {
                    'task_description': message,
                    'constraints': {
                        'max_steps': 8,
                        'timeout_per_step': 30,
                        'screenshot_frequency': 'every_step'
                    }
                },
                task_id=f'frontend_task_{int(time.time())}'
            )
            
            if result.get('success'):
                response = f"✅ **Navegación Web Completada**\n\n"
                response += f"🎯 **Tarea:** {message}\n\n"
                response += f"📊 **Resultados:**\n"
                response += f"• Pasos completados: {result.get('completed_steps', 0)}/{result.get('total_steps', 0)}\n"
                response += f"• Tasa de éxito: {result.get('success_rate', 0):.1%}\n"
                response += f"• Screenshots capturados: {len(result.get('screenshots', []))}\n"
                
                if result.get('final_url'):
                    response += f"• URL final: {result.get('final_url')}\n"
                
                response += f"\n🔍 **Detalles de ejecución:**\n"
                logs = result.get('execution_logs', [])
                for log in logs[-5:]:  # Show last 5 logs
                    response += f"• {log.get('message', '')}\n"
                
                return jsonify({
                    'response': response,
                    'navigation_result': result,
                    'task_type': 'web_navigation',
                    'success': True
                })
            else:
                return jsonify({
                    'response': f"❌ Error en navegación web: {result.get('error', 'Error desconocido')}",
                    'navigation_result': result,
                    'task_type': 'web_navigation',
                    'success': False
                })
        else:
            # Regular response for non-navigation tasks
            return jsonify({
                'response': f"Recibido: {message}",
                'task_type': 'regular',
                'success': True
            })
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/agent/tools', methods=['GET'])
def get_tools():
    """Get available tools"""
    try:
        tools = tool_manager.get_available_tools()
        return jsonify({
            'tools': tools,
            'count': len(tools)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting simple test server for autonomous web navigation...")
    print("🌐 Server will run on http://localhost:8001")
    print("🔧 Available tools:", len(tool_manager.get_available_tools()))
    
    # Find and display autonomous web navigation tool
    tools = tool_manager.get_available_tools()
    nav_tool = None
    for tool in tools:
        if tool['name'] == 'autonomous_web_navigation':
            nav_tool = tool
            break
    
    if nav_tool:
        print(f"✅ Autonomous Web Navigation tool found and enabled")
        print(f"   Description: {nav_tool['description']}")
    else:
        print("❌ Autonomous Web Navigation tool not found")
    
    app.run(host='0.0.0.0', port=8001, debug=True)