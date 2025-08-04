#!/usr/bin/env python3
"""
🔥 TEST NAVEGACIÓN VISUAL CON LOGGING INTENSIVO
Objetivo: Encontrar EXACTAMENTE donde se interrumpe el flujo de browser_visual events
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

def clear_comprehensive_log():
    """Limpiar log comprehensive"""
    try:
        with open('/tmp/websocket_comprehensive.log', 'w') as f:
            f.write(f"=== LOGGING INTENSIVO INICIADO - {datetime.now().isoformat()} ===\n")
        print_log("✅ Log comprehensive limpiado")
    except Exception as e:
        print_log(f"⚠️ Error limpiando log: {e}")

def monitor_comprehensive_log():
    """Monitorear log comprehensive en tiempo real"""
    print_log("🔍 Iniciando monitoreo de log comprehensive...")
    try:
        process = subprocess.Popen(['tail', '-f', '/tmp/websocket_comprehensive.log'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        return process
    except Exception as e:
        print_log(f"❌ Error iniciando monitoreo de log: {e}")
        return None

def check_websocket_manager_status():
    """Verificar estado del WebSocket Manager"""
    print_log("🔍 VERIFICANDO ESTADO WEBSOCKET MANAGER...")
    
    # Test backend logs para WebSocket Manager
    try:
        result = subprocess.run(['grep', '-r', 'WebSocket Manager', '/var/log/supervisor/backend.err.log'], 
                              capture_output=True, text=True, timeout=5)
        if result.stdout:
            print_log("✅ WebSocket Manager logs encontrados:")
            for line in result.stdout.strip().split('\n')[-3:]:
                print_log(f"   - {line}")
        else:
            print_log("❌ No se encontraron logs de WebSocket Manager")
    except Exception as e:
        print_log(f"⚠️ Error verificando logs WebSocket Manager: {e}")

def test_navegacion_visual_logging():
    """Test navegación visual con logging intensivo"""
    
    print_log("🚀 INICIANDO TEST NAVEGACIÓN VISUAL CON LOGGING INTENSIVO")
    print_log("=" * 80)
    
    # Limpiar log comprehensive
    clear_comprehensive_log()
    
    # Verificar estado WebSocket Manager
    check_websocket_manager_status()
    
    # Crear task_id único para el test
    task_id = f"test-navegacion-logging-{int(time.time())}"
    print_log(f"📋 Task ID: {task_id}")
    
    # Preparar datos para la petición
    test_data = {
        "message": "Buscar información sobre inteligencia artificial 2025",
        "task_id": task_id,
        "use_memory": True,
        "model": "llama3.1:8b"
    }
    
    print_log(f"📤 Enviando petición a backend con task_id: {task_id}")
    print_log(f"📋 Datos: {json.dumps(test_data, indent=2)}")
    
    # Iniciar monitoreo de log en background
    log_monitor = monitor_comprehensive_log()
    
    try:
        # Enviar petición al endpoint del agente
        print_log("🌐 Enviando petición HTTP al backend...")
        
        response = requests.post(
            'http://localhost:8001/api/agent/chat',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print_log(f"📨 Respuesta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_log("✅ Petición exitosa")
            print_log(f"📋 Respuesta: {json.dumps(result, indent=2)[:500]}...")
        else:
            print_log(f"❌ Error en petición: {response.status_code}")
            print_log(f"📋 Error content: {response.text[:500]}")
        
        # Esperar para que el proceso termine y genere logs
        print_log("⏳ Esperando 15 segundos para captura de logs...")
        time.sleep(15)
        
    except Exception as e:
        print_log(f"❌ Error en petición: {e}")
    
    finally:
        # Detener monitoreo de log
        if log_monitor:
            log_monitor.terminate()
            print_log("🔍 Monitoreo de log detenido")
    
    # Analizar comprehensive log
    analyze_comprehensive_log()

def analyze_comprehensive_log():
    """Analizar el log comprehensive para encontrar el problema"""
    print_log("📊 ANALIZANDO LOG COMPREHENSIVE...")
    print_log("=" * 80)
    
    try:
        with open('/tmp/websocket_comprehensive.log', 'r') as f:
            log_content = f.read()
        
        if not log_content.strip():
            print_log("❌ CRÍTICO: Log comprehensive está VACÍO")
            print_log("🔍 Esto indica que _emit_browser_visual() NO se está ejecutando")
            return
        
        print_log(f"📄 Log comprehensive contiene {len(log_content)} caracteres")
        
        # Buscar patrones críticos
        patterns = [
            ("EMIT_BROWSER_VISUAL START", "🚀 Función _emit_browser_visual iniciada"),
            ("BROWSER_VISUAL_STEP_2_FAIL", "❌ FALLO: No task_id disponible"),
            ("BROWSER_VISUAL_STEP_3", "🔧 Intentando método Flask SocketIO"),
            ("BROWSER_VISUAL_STEP_3_SUCCESS", "✅ Flask SocketIO exitoso"),
            ("BROWSER_VISUAL_STEP_4", "🔄 Fallback a WebSocket Manager"),
            ("BROWSER_VISUAL_STEP_4_SUCCESS", "✅ WebSocket Manager exitoso"),
            ("BROWSER_VISUAL_STEP_5", "⚠️ Fallback final - solo mensaje"),
            ("COMPLETE_FAILURE", "❌ FALLO COMPLETO")
        ]
        
        found_patterns = []
        for pattern, description in patterns:
            if pattern in log_content:
                count = log_content.count(pattern)
                found_patterns.append((pattern, description, count))
                print_log(f"✅ ENCONTRADO: {description} ({count} veces)")
            else:
                print_log(f"❌ NO ENCONTRADO: {description}")
        
        print_log("=" * 80)
        
        # Mostrar fragmentos relevantes del log
        lines = log_content.split('\n')
        relevant_lines = [line for line in lines if any(p[0] in line for p in patterns)]
        
        if relevant_lines:
            print_log("📋 FRAGMENTOS RELEVANTES DEL LOG:")
            for line in relevant_lines[-10:]:  # Últimas 10 líneas relevantes
                print_log(f"   {line}")
        else:
            print_log("❌ No se encontraron líneas relevantes en el log")
        
        # Diagnóstico final
        if "EMIT_BROWSER_VISUAL START" not in log_content:
            print_log("🔥 DIAGNÓSTICO: _emit_browser_visual() NO se está ejecutando")
            print_log("🔍 CAUSA PROBABLE: La herramienta web no está llamando esta función")
        elif "BROWSER_VISUAL_STEP_3_SUCCESS" in log_content:
            print_log("🔥 DIAGNÓSTICO: Flask SocketIO funcionando - problema podría ser en frontend")
        elif "BROWSER_VISUAL_STEP_4_SUCCESS" in log_content:
            print_log("🔥 DIAGNÓSTICO: WebSocket Manager funcionando - problema podría ser en frontend")
        elif "COMPLETE_FAILURE" in log_content:
            print_log("🔥 DIAGNÓSTICO: FALLO COMPLETO en backend - ningún método funciona")
        else:
            print_log("🔥 DIAGNÓSTICO: _emit_browser_visual() se ejecuta pero falla parcialmente")
    
    except Exception as e:
        print_log(f"❌ Error analizando log comprehensive: {e}")

def check_backend_logs():
    """Verificar logs del backend para eventos browser_visual"""
    print_log("🔍 VERIFICANDO LOGS DEL BACKEND...")
    
    try:
        # Buscar eventos browser_visual en logs del backend
        result = subprocess.run(['grep', '-r', 'browser_visual', '/var/log/supervisor/backend.err.log'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.stdout:
            print_log("✅ Eventos browser_visual encontrados en backend logs:")
            lines = result.stdout.strip().split('\n')
            for line in lines[-5:]:  # Últimas 5 líneas
                print_log(f"   {line}")
        else:
            print_log("❌ NO se encontraron eventos browser_visual en backend logs")
        
        # Buscar también eventos WebSocket generales
        result2 = subprocess.run(['grep', '-r', 'emitting event', '/var/log/supervisor/backend.err.log'], 
                               capture_output=True, text=True, timeout=10)
        
        if result2.stdout:
            print_log("📡 Eventos WebSocket generales encontrados:")
            lines = result2.stdout.strip().split('\n')
            for line in lines[-3:]:  # Últimas 3 líneas
                print_log(f"   {line}")
        else:
            print_log("❌ NO se encontraron eventos WebSocket en backend logs")
    
    except Exception as e:
        print_log(f"⚠️ Error verificando backend logs: {e}")

if __name__ == "__main__":
    try:
        print_log("🔥 INICIANDO DIAGNÓSTICO COMPLETO DE NAVEGACIÓN VISUAL")
        print_log(f"📅 Fecha: {datetime.now().isoformat()}")
        print_log("=" * 80)
        
        # Verificar logs del backend primero
        check_backend_logs()
        
        # Ejecutar test principal
        test_navegacion_visual_logging()
        
        print_log("=" * 80)
        print_log("🏁 DIAGNÓSTICO COMPLETO - Revisar resultados arriba")
        
    except KeyboardInterrupt:
        print_log("⚠️ Test interrumpido por usuario")
    except Exception as e:
        print_log(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()