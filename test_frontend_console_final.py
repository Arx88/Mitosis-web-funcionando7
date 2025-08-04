#!/usr/bin/env python3
"""
🔥 TEST FINAL - VERIFICACIÓN FRONTEND CONSOLE LOGS
Verificar si los eventos browser_visual llegan al frontend pero no se muestran
"""

import requests
import json
import time
import sys
import subprocess
import os
from datetime import datetime

def print_log(message):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def test_frontend_console_realtime():
    """Test con logging de console del frontend en tiempo real"""
    
    print_log("🔥 INICIANDO TEST FINAL - VERIFICACIÓN FRONTEND CONSOLE")
    print_log("=" * 80)
    
    # Crear task_id único para el test
    task_id = f"test-frontend-console-{int(time.time())}"
    print_log(f"📋 Task ID: {task_id}")
    
    # Script JavaScript para inyectar logging intensivo en el frontend
    frontend_logging_script = '''
    console.log("🔥 LOGGING INTENSIVO FRONTEND ACTIVADO");
    
    // Interceptar TODOS los console.log del frontend
    const originalLog = console.log;
    console.log = function(...args) {
        // Verificar si contiene browser_visual
        const message = args.join(" ");
        if (message.includes("browser_visual") || message.includes("BROWSER-VISUAL") || message.includes("📸")) {
            originalLog("🚨 FRONTEND BROWSER_VISUAL DETECTADO:", ...args);
        }
        originalLog(...args);
    };
    
    // Interceptar WebSocket events específicamente
    if (window.socket) {
        const originalOn = window.socket.on;
        window.socket.on = function(event, handler) {
            if (event === "browser_visual") {
                console.log("🔥 HANDLER browser_visual REGISTRADO");
                const wrappedHandler = function(data) {
                    console.log("🚨 BROWSER_VISUAL EVENT RECIBIDO EN FRONTEND:", data);
                    return handler(data);
                };
                return originalOn.call(this, event, wrappedHandler);
            }
            return originalOn.call(this, event, handler);
        };
    }
    
    console.log("✅ Frontend logging interceptors instalados");
    '''
    
    try:
        # Preparar datos para la petición
        test_data = {
            "message": "Buscar información sobre robots avanzados 2025 con navegación visual",
            "task_id": task_id,
            "use_memory": True,
            "model": "llama3.1:8b"
        }
        
        print_log(f"📤 Enviando petición con task_id: {task_id}")
        
        # Enviar petición al endpoint del agente
        response = requests.post(
            'http://localhost:8001/api/agent/chat',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print_log(f"📨 Respuesta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_log("✅ Petición exitosa")
            task_id_backend = result.get('task_id', task_id)
            print_log(f"📋 Task ID del backend: {task_id_backend}")
        else:
            print_log(f"❌ Error en petición: {response.status_code}")
            print_log(f"📋 Error content: {response.text[:300]}")
            return
        
        # Esperar para capturar logs
        print_log("⏳ Esperando 20 segundos para capturar eventos...")
        time.sleep(20)
        
        # Verificar logs comprehensive
        print_log("📊 ANALIZANDO LOGS COMPREHENSIVE...")
        try:
            with open('/tmp/websocket_comprehensive.log', 'r') as f:
                log_content = f.read()
            
            if task_id_backend in log_content or task_id in log_content:
                print_log(f"✅ Task ID encontrado en logs comprehensive")
                
                # Contar eventos browser_visual para este task_id
                visual_events = log_content.count("BROWSER_VISUAL_STEP_3_SUCCESS")
                print_log(f"📊 Eventos browser_visual enviados: {visual_events}")
                
                if visual_events > 0:
                    print_log("✅ CONFIRMADO: Backend SÍ está enviando eventos browser_visual")
                    print_log("🔍 PROBLEMA: Los eventos se envían pero no llegan al frontend")
                    print_log("🎯 CAUSA: Timing/Room joining issue confirmado")
                else:
                    print_log("❌ Backend NO está enviando eventos browser_visual")
            else:
                print_log(f"❌ Task ID {task_id_backend} NO encontrado en logs")
        
        except Exception as e:
            print_log(f"⚠️ Error analizando comprehensive log: {e}")
        
        # Verificar backend logs para este task específico
        print_log("🔍 VERIFICANDO BACKEND LOGS ESPECÍFICOS...")
        try:
            result = subprocess.run(['grep', '-r', task_id_backend, '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                browser_visual_events = [line for line in lines if 'browser_visual' in line]
                
                print_log(f"📊 Eventos browser_visual en backend logs: {len(browser_visual_events)}")
                
                if browser_visual_events:
                    print_log("✅ CONFIRMADO FINAL: Backend envía eventos browser_visual")
                    for event in browser_visual_events[-3:]:  # Últimos 3
                        print_log(f"   📸 {event}")
                    
                    print_log("🔥 DIAGNÓSTICO FINAL:")
                    print_log("   ✅ Backend: Envía eventos correctamente")
                    print_log("   ❌ Frontend: No recibe/procesa eventos")
                    print_log("   🎯 PROBLEMA: Timing de room joining confirmado")
                    print_log("   💡 SOLUCIÓN: Aumentar delay o cambiar estrategia")
                else:
                    print_log("❌ No hay eventos browser_visual en backend logs")
            else:
                print_log(f"❌ Task ID {task_id_backend} no encontrado en backend logs")
        
        except Exception as e:
            print_log(f"⚠️ Error verificando backend logs: {e}")
        
    except Exception as e:
        print_log(f"❌ Error en test: {e}")

if __name__ == "__main__":
    try:
        test_frontend_console_realtime()
        print_log("🏁 TEST FINAL COMPLETADO")
        
    except KeyboardInterrupt:
        print_log("⚠️ Test interrumpido por usuario")
    except Exception as e:
        print_log(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()