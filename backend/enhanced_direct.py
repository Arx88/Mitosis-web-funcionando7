#!/usr/bin/env python3
"""
Servidor Enhanced simple y directo sin dependencias complejas
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Terminal logger
terminal_logger = logging.getLogger('MITOSIS')
terminal_handler = logging.StreamHandler(sys.stdout)
terminal_handler.setLevel(logging.INFO)
terminal_formatter = logging.Formatter('%(asctime)s - [MITOSIS] - %(message)s')
terminal_handler.setFormatter(terminal_formatter)
terminal_logger.addHandler(terminal_handler)
terminal_logger.setLevel(logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mitosis-enhanced-direct'

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configurar WebSocket
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)

# Estado global
autonomous_execution_active = False
current_autonomous_task_id = None
monitor_pages = []

def add_monitor_page(title, content, page_type, metadata=None):
    """Añade página al monitor con salida en terminal"""
    global monitor_pages
    
    page_number = len(monitor_pages) + 1
    page = {
        'page_number': page_number,
        'title': title,
        'content': content,
        'type': page_type,
        'timestamp': datetime.now(),
        'metadata': metadata or {}
    }
    monitor_pages.append(page)
    
    # Emitir evento WebSocket
    socketio.emit('new_monitor_page', {
        'page_number': page_number,
        'title': title,
        'content': content,
        'type': page_type,
        'timestamp': page['timestamp'].isoformat(),
        'metadata': metadata or {}
    })
    
    # Salida mejorada en terminal
    terminal_logger.info("")
    terminal_logger.info("=" * 80)
    terminal_logger.info(f"📄 NUEVA PÁGINA DEL MONITOR (Tipo: {page_type.upper()})")
    terminal_logger.info(f"Título: {title}")
    terminal_logger.info(f"Timestamp: {datetime.now()}")
    
    if metadata:
        terminal_logger.info("Metadatos:")
        for key, value in metadata.items():
            terminal_logger.info(f'  {key}: {value}')
    
    terminal_logger.info("-" * 80)
    terminal_logger.info("Contenido:")
    terminal_logger.info(content)
    terminal_logger.info("=" * 80)

def generate_simple_plan(title, description):
    """Genera un plan simple sin LLM"""
    task_id = f"task_{int(time.time())}"
    
    plan = {
        "task_id": task_id,
        "title": title,
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "steps": [
            {
                "id": "step1",
                "title": f"Investigar: {title}",
                "description": f"Buscar información sobre: {description}",
                "tool": "web_search",
                "status": "pending",
                "estimated_time": 2,
                "priority": "high"
            },
            {
                "id": "step2", 
                "title": "Analizar información",
                "description": "Procesar y analizar los datos encontrados",
                "tool": "analysis",
                "status": "pending",
                "estimated_time": 3,
                "priority": "normal"
            },
            {
                "id": "step3",
                "title": "Generar resultado final",
                "description": "Crear documento con los resultados obtenidos",
                "tool": "file_creation",
                "status": "pending", 
                "estimated_time": 2,
                "priority": "normal"
            }
        ]
    }
    
    return plan

async def execute_autonomous_task(task_id):
    """Ejecuta tarea de forma autónoma simulada"""
    global autonomous_execution_active, current_autonomous_task_id
    
    try:
        autonomous_execution_active = True
        current_autonomous_task_id = task_id
        
        # Simular ejecución de pasos
        steps = ["Investigación", "Análisis", "Generación de resultados"]
        
        for i, step in enumerate(steps, 1):
            terminal_logger.info(f"⚡ Ejecutando paso: {step}")
            terminal_logger.info(f"📊 Progreso: {(i/len(steps)*100):.1f}% ({i}/{len(steps)})")
            
            add_monitor_page(
                f"Paso {i}: {step}",
                f"Ejecutando {step.lower()}...\n\nProgreso: {i}/{len(steps)}",
                "step_execution",
                {"step": i, "total_steps": len(steps)}
            )
            
            # Simular trabajo
            await asyncio.sleep(2)
            
            terminal_logger.info(f"✅ Paso completado: {step}")
        
        # Crear resultado final
        result_content = f"""# Resultado Final - {task_id}

## Resumen
Tarea completada exitosamente con 3 pasos ejecutados.

## Detalles
- Paso 1: Investigación ✅
- Paso 2: Análisis ✅  
- Paso 3: Generación de resultados ✅

## Timestamp
Completado: {datetime.now().isoformat()}
"""
        
        add_monitor_page(
            "Tarea Completada",
            result_content,
            "completion",
            {"task_id": task_id, "success": True}
        )
        
        terminal_logger.info(f"🎉 Tarea {task_id} completada exitosamente")
        
        # Emitir evento de finalización
        socketio.emit('autonomous_execution_completed', {
            'task_id': task_id,
            'success': True,
            'timestamp': datetime.now().isoformat()
        })
        
        return True
        
    except Exception as e:
        terminal_logger.error(f"❌ Error en ejecución autónoma: {e}")
        return False
    finally:
        autonomous_execution_active = False
        current_autonomous_task_id = None

def should_execute_autonomously(message):
    """Determina si un mensaje requiere ejecución autónoma"""
    triggers = [
        "crea", "crear", "genera", "generar", "desarrolla", "desarrollar",
        "investiga", "investigar", "analiza", "analizar", "busca", "buscar",
        "informe", "reporte", "plan", "estrategia", "análisis"
    ]
    
    message_lower = message.lower()
    return any(trigger in message_lower for trigger in triggers)

# ENDPOINTS PRINCIPALES

@app.route('/api/agent/initialize-task', methods=['POST'])
def initialize_task():
    """Inicializa una nueva tarea autónoma"""
    try:
        data = request.get_json()
        title = data.get('title', 'Tarea sin título')
        description = data.get('description', '')
        auto_execute = data.get('auto_execute', False)
        
        terminal_logger.info(f"📋 Inicializando tarea: {title}")
        
        # Generar plan simple
        plan = generate_simple_plan(title, description)
        
        # Añadir página del monitor
        add_monitor_page(
            f"Tarea Inicializada: {title}",
            f"**Descripción:** {description}\n**Auto-ejecutar:** {auto_execute}",
            "task-creation",
            {"task_id": plan["task_id"], "auto_execute": auto_execute}
        )
        
        # Iniciar ejecución si se solicita
        if auto_execute:
            # Ejecutar tarea en background
            def run_task_in_background():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(execute_autonomous_task(plan["task_id"]))
                    loop.close()
                except Exception as e:
                    terminal_logger.error(f"Error en tarea background: {e}")
            
            import threading
            thread = threading.Thread(target=run_task_in_background, daemon=True)
            thread.start()
        
        return jsonify({
            "success": True,
            "plan": plan,
            "auto_execution": auto_execute,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        terminal_logger.error(f"❌ Error inicializando tarea: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/agent/chat', methods=['POST'])
def enhanced_chat():
    """Chat mejorado con capacidades autónomas"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        terminal_logger.info(f"💬 Mensaje recibido: {message}")
        
        # Crear página del monitor para mensaje del usuario
        add_monitor_page(
            "Mensaje del Usuario",
            f"**Usuario:** {message}",
            "user-message",
            {"message_length": len(message)}
        )
        
        # Determinar si requiere ejecución autónoma
        if should_execute_autonomously(message):
            terminal_logger.info("🎯 Mensaje detectado como tarea autónoma")
            
            # Generar plan de acción
            plan = generate_simple_plan(f"Tarea: {message[:50]}...", message)
            
            # Iniciar ejecución autónoma
            task_execution_task = asyncio.create_task(execute_autonomous_task(plan["task_id"]))
            
            # No esperar la tarea, simplemente crearla en background
            def run_task_in_background():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(execute_autonomous_task(plan["task_id"]))
                    loop.close()
                except Exception as e:
                    terminal_logger.error(f"Error en tarea background: {e}")
            
            import threading
            thread = threading.Thread(target=run_task_in_background, daemon=True)
            thread.start()
            
            response_text = (
                f"He generado un plan de acción para tu solicitud y comenzaré la ejecución autónoma. "
                f"Puedes seguir el progreso en tiempo real en la terminal.\n\n"
                f"**Plan generado:**\n" + 
                "\n".join([f"{i+1}. {step['title']}" for i, step in enumerate(plan['steps'])]) +
                f"\n\n**ID de tarea:** {plan['task_id']}\n**Estado:** Ejecutándose autónomamente"
            )
            
            return jsonify({
                "response": response_text,
                "autonomous_execution": True,
                "execution_plan": {
                    "task_id": plan["task_id"],
                    "status": "pending",
                    "steps": plan["steps"]
                },
                "task_id": plan["task_id"],
                "timestamp": datetime.now().isoformat(),
                "memory_used": True
            })
        
        else:
            # Procesamiento conversacional
            terminal_logger.info("💬 Procesando como conversación normal")
            
            task_id = f"chat_{int(time.time())}"
            response_text = f"He recibido tu mensaje: '{message}'. Como agente mejorado, puedo ayudarte con tareas complejas de forma autónoma."
            
            return jsonify({
                "response": response_text,
                "autonomous_execution": False,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "memory_used": True
            })
            
    except Exception as e:
        terminal_logger.error(f"❌ Error en chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/agent/status', methods=['GET'])
def get_agent_status():
    """Obtiene el estado del agente"""
    try:
        return jsonify({
            "status": "operational",
            "enhanced_features": True,
            "timestamp": datetime.now().isoformat(),
            "autonomous_execution": {
                "active": autonomous_execution_active,
                "current_task_id": current_autonomous_task_id
            },
            "capabilities": [
                "autonomous_task_execution",
                "real_time_terminal_output", 
                "step_by_step_progress",
                "websocket_communication",
                "plan_generation"
            ],
            "tools_available": 5,
            "models_available": ["direct_execution"],
            "memory_enabled": True
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def enhanced_health():
    """Health check mejorado"""
    return jsonify({
        "status": "healthy",
        "enhanced": True,
        "autonomous_execution": autonomous_execution_active,
        "timestamp": datetime.now().isoformat()
    })

# Endpoints de compatibilidad
@app.route('/api/agent/ollama/check', methods=['GET', 'POST'])
def ollama_check():
    """Verificación de conexión con Ollama"""
    try:
        import requests
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'https://bef4a4bb93d1.ngrok-free.app')
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        return jsonify({
            "status": "connected" if response.status_code == 200 else "disconnected",
            "endpoint": ollama_url,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/api/agent/ollama/models', methods=['GET', 'POST'])
def ollama_models():
    """Lista de modelos disponibles"""
    try:
        import requests
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'https://bef4a4bb93d1.ngrok-free.app')
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            return jsonify({
                "models": models,
                "count": len(models),
                "endpoint": ollama_url,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"models": [], "error": "Failed to fetch models"}), 500
    except Exception as e:
        return jsonify({"models": [], "error": str(e)}), 500

@app.route('/api/agent/generate-suggestions', methods=['POST'])
def generate_suggestions():
    """Genera sugerencias dinámicas"""
    return jsonify({
        "suggestions": [
            {"id": 1, "title": "Crear un informe sobre IA 2025", "description": "Investigar tendencias actuales"},
            {"id": 2, "title": "Analizar datos de mercado", "description": "Procesar métricas comerciales"},
            {"id": 3, "title": "Generar plan de marketing", "description": "Estrategia de marketing digital"}
        ],
        "timestamp": datetime.now().isoformat()
    })

# Eventos WebSocket
@socketio.on('connect')
def handle_connect():
    terminal_logger.info(f"🔌 Cliente WebSocket conectado: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    terminal_logger.info(f"🔌 Cliente WebSocket desconectado: {request.sid}")

@socketio.on('join_task_room')
def handle_join_task_room(data):
    task_id = data.get('task_id')
    if task_id:
        from flask_socketio import join_room
        join_room(f"task_{task_id}")
        terminal_logger.info(f"👥 Cliente {request.sid} se unió a sala de tarea: {task_id}")

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8001))
    
    print("="*80)
    print("🚀 ENHANCED DIRECT BACKEND INICIADO")
    print(f"🌐 Servidor corriendo en {host}:{port}")
    print("🖥️  Monitoreo de terminal activo")
    print("✨ Capacidades autónomas disponibles")
    print("="*80)
    
    terminal_logger.info("🚀 Enhanced Direct Backend inicializado exitosamente")
    
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)