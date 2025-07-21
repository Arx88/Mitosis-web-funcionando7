#!/usr/bin/env python3
"""
Script de Inicio Mejorado para Mitosis-Beta Backend
Punto de entrada con capacidades de ejecución autónoma y salida en terminal
"""

import os
import sys
import logging
import time
from datetime import datetime

# Añadir directorio actual al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Muestra el banner de inicio del sistema mejorado"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ███╗   ███╗██╗████████╗ ██████╗ ███████╗██╗███████╗    ██╗   ██╗███████╗ ║
║    ████╗ ████║██║╚══██╔══╝██╔═══██╗██╔════╝██║██╔════╝    ██║   ██║██╔════╝ ║
║    ██╔████╔██║██║   ██║   ██║   ██║███████╗██║███████╗    ██║   ██║███████╗ ║
║    ██║╚██╔╝██║██║   ██║   ██║   ██║╚════██║██║╚════██║    ╚██╗ ██╔╝╚════██║ ║
║    ██║ ╚═╝ ██║██║   ██║   ╚██████╔╝███████║██║███████║     ╚████╔╝ ███████║ ║
║    ╚═╝     ╚═╝╚═╝   ╚═╝    ╚═════╝ ╚══════╝╚═╝╚══════╝      ╚═══╝  ╚══════╝ ║
║                                                                              ║
║                     🚀 ENHANCED BACKEND CON EJECUCIÓN AUTÓNOMA 🚀            ║
║                            ⚡ Salida en Terminal en Tiempo Real ⚡            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print(f"📅 Fecha de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Versión de Python: {sys.version.split()[0]}")
    print(f"📁 Directorio de trabajo: {os.getcwd()}")
    print("=" * 80)

def check_dependencies():
    """Verifica las dependencias necesarias"""
    print("🔍 Verificando dependencias...")
    
    required_modules = [
        'flask',
        'flask_cors', 
        'flask_socketio',
        'asyncio'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - FALTANTE")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️ Módulos faltantes: {', '.join(missing_modules)}")
        print(f"💡 Instalar con: pip install {' '.join(missing_modules)}")
        return False
    
    print("✅ Todas las dependencias están disponibles")
    return True

def create_config():
    """Crea configuración basada en variables de entorno"""
    print("⚙️ Creando configuración...")
    
    config = {
        'OLLAMA_URL': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY', ''),
        'PREFER_LOCAL_MODELS': os.getenv('PREFER_LOCAL_MODELS', 'true').lower() == 'true',
        'MAX_COST_PER_1K_TOKENS': float(os.getenv('MAX_COST_PER_1K_TOKENS', '0.01')),
        'MEMORY_DB_PATH': os.getenv('MEMORY_DB_PATH', 'enhanced_agent.db'),
        'MAX_SHORT_TERM_MESSAGES': int(os.getenv('MAX_SHORT_TERM_MESSAGES', '100')),
        'MAX_CONCURRENT_TASKS': int(os.getenv('MAX_CONCURRENT_TASKS', '3')),
        'DEBUG_MODE': os.getenv('DEBUG', 'true').lower() == 'true',
        'HOST': os.getenv('HOST', '0.0.0.0'),
        'PORT': int(os.getenv('PORT', '8001'))
    }
    
    print("📋 Configuración actual:")
    for key, value in config.items():
        # Ocultar claves API por seguridad
        if 'KEY' in key or 'TOKEN' in key:
            display_value = f"{'*' * (len(str(value)) - 4)}{str(value)[-4:]}" if value else "No configurado"
        else:
            display_value = value
        print(f"   {key}: {display_value}")
    
    return config

def main():
    """Función principal de inicio"""
    try:
        # Banner de bienvenida
        print_banner()
        
        # Verificar dependencias
        if not check_dependencies():
            print("❌ Error: No se pueden cargar las dependencias necesarias")
            sys.exit(1)
        
        # Crear configuración
        config = create_config()
        
        # Importar y crear la API mejorada
        print("🚀 Iniciando Enhanced Unified Mitosis API...")
        
        try:
            from enhanced_unified_api import EnhancedUnifiedMitosisAPI
            api = EnhancedUnifiedMitosisAPI(config)
            print("✅ API mejorada inicializada exitosamente")
        except ImportError as e:
            print(f"❌ Error importando Enhanced API: {e}")
            print("💡 Usando servidor base como fallback...")
            # Fallback al servidor original
            from server import app, socketio
            api = app
        
        # Mostrar características habilitadas
        print("\n🌟 CARACTERÍSTICAS HABILITADAS:")
        features = [
            "✅ Ejecución autónoma de tareas completas",
            "✅ Salida en tiempo real en terminal formateada",
            "✅ Monitoreo de progreso paso a paso automático",
            "✅ Entrega de resultados finales estructurada",
            "✅ Compatibilidad total con UI existente",
            "✅ WebSockets para actualizaciones en tiempo real",
            "✅ Detección inteligente de intención autónoma",
            "✅ Sistema de logging mejorado en terminal",
            "✅ Orquestación de tareas complejas",
            "✅ Gestión de herramientas integrada"
        ]
        
        for feature in features:
            print(f"   {feature}")
        
        # Mostrar endpoints disponibles
        print("\n🌐 ENDPOINTS DISPONIBLES:")
        endpoints = [
            "🔹 GET  /api/health - Estado de salud del sistema",
            "🔹 POST /api/agent/initialize-task - Inicializar tarea autónoma",
            "🔹 POST /api/agent/start-task-execution/<task_id> - Iniciar ejecución",
            "🔹 GET  /api/agent/get-task-plan/<task_id> - Obtener plan de tarea",
            "🔹 POST /api/agent/chat - Chat con detección autónoma",
            "🔹 GET  /api/agent/status - Estado detallado del agente",
            "🔹 GET  /api/monitor/pages - Páginas del monitor",
            "🔹 GET  /api/monitor/latest - Última página del monitor"
        ]
        
        for endpoint in endpoints:
            print(f"   {endpoint}")
        
        # Mostrar eventos WebSocket
        print("\n🔌 EVENTOS WEBSOCKET:")
        ws_events = [
            "🔸 connection_status - Estado de conexión",
            "🔸 new_monitor_page - Nueva página en monitor",
            "🔸 autonomous_execution_completed - Ejecución completada",
            "🔸 task_progress_update - Actualización de progreso",
            "🔸 step_status_changed - Cambio de estado de paso"
        ]
        
        for event in ws_events:
            print(f"   {event}")
        
        print("\n" + "=" * 80)
        print("🎯 SISTEMA LISTO PARA EJECUCIÓN AUTÓNOMA")
        print("📊 Monitorea la terminal para ver actividad en tiempo real")
        print("🔗 La UI existente funcionará sin cambios")
        print("=" * 80)
        
        # Iniciar el servidor
        host = config['HOST']
        port = config['PORT']
        debug = config['DEBUG_MODE']
        
        print(f"\n🚀 Iniciando servidor en {host}:{port}")
        print(f"🛠️ Modo debug: {'Activado' if debug else 'Desactivado'}")
        print(f"🌐 Accesible en: http://{host}:{port}")
        
        if hasattr(api, 'run'):
            # API mejorada con WebSocket
            api.run(host=host, port=port, debug=debug)
        else:
            # Fallback al servidor Flask
            api.run(host=host, port=port, debug=debug)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupción del usuario detectada")
        print("🧹 Realizando limpieza...")
        
        # Llamar al método de apagado si está disponible
        if 'api' in locals() and hasattr(api, 'shutdown'):
            api.shutdown()
        
        print("✅ Limpieza completada")
        print("👋 ¡Hasta la vista, baby!")
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print(f"📋 Tipo de error: {type(e).__name__}")
        import traceback
        print(f"🔍 Traceback completo:")
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        print("\n🏁 Proceso de backend finalizado")

if __name__ == "__main__":
    main()