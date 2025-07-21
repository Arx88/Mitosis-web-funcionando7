#!/usr/bin/env python3
"""
Start Enhanced Backend - El Punto de Entrada Mejorado
Nuevo punto de entrada para iniciar el backend del agente Mitosis-Beta
con ejecución autónoma y salida en terminal
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Añadir directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def print_banner():
    """Muestra un banner ASCII art al inicio"""
    banner = """
████████████████████████████████████████████████████████████████████████████████
█                                                                              █
█  ███    ███ ██ ████████  ██████  ███████ ██ ███████       ██████  ███████   █
█  ████  ████ ██    ██    ██    ██ ██      ██ ██           ██       ██        █
█  ██ ████ ██ ██    ██    ██    ██ ███████ ██ ███████      ██   ███ ███████   █
█  ██  ██  ██ ██    ██    ██    ██      ██ ██      ██      ██    ██      ██   █
█  ██      ██ ██    ██     ██████  ███████ ██ ███████       ██████  ███████   █
█                                                                              █
█               🚀 ENHANCED BACKEND WITH AUTONOMOUS EXECUTION 🚀                █
█                          🖥️  REAL-TIME TERMINAL OUTPUT 🖥️                    █
█                                                                              █
████████████████████████████████████████████████████████████████████████████████
    """
    print(banner)
    print(f"🗓️  Fecha de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    print(f"📁 Working directory: {current_dir}")
    print()

def check_dependencies():
    """Verifica las dependencias básicas"""
    required_modules = ['flask', 'flask_cors', 'flask_socketio', 'asyncio']
    missing_modules = []
    
    print("🔍 Verificando dependencias...")
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"   ❌ {module} - FALTANTE")
    
    if missing_modules:
        print()
        print("⚠️  Dependencias faltantes detectadas:")
        for module in missing_modules:
            print(f"   pip install {module}")
        print()
        return False
    
    print("   🎉 Todas las dependencias están disponibles")
    print()
    return True

def create_config() -> Dict[str, Any]:
    """Crea la configuración del agente desde variables de entorno"""
    print("⚙️  Cargando configuración desde variables de entorno...")
    
    config = {
        'OLLAMA_URL': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY', ''),
        'PREFER_LOCAL_MODELS': os.getenv('PREFER_LOCAL_MODELS', 'true').lower() == 'true',
        'MAX_COST_PER_1K_TOKENS': float(os.getenv('MAX_COST_PER_1K_TOKENS', '0.01')),
        'MEMORY_DB_PATH': os.getenv('MEMORY_DB_PATH', 'enhanced_agent.db'),
        'MAX_SHORT_TERM_MESSAGES': int(os.getenv('MAX_SHORT_TERM_MESSAGES', '100')),
        'MAX_CONCURRENT_TASKS': int(os.getenv('MAX_CONCURRENT_TASKS', '3')),
        'DEBUG_MODE': os.getenv('DEBUG_MODE', 'true').lower() == 'true',
        'HOST': os.getenv('HOST', '0.0.0.0'),
        'PORT': int(os.getenv('PORT', '8001'))
    }
    
    print("   📋 Configuración cargada:")
    for key, value in config.items():
        # Ocultar claves API por seguridad
        display_value = value
        if 'API_KEY' in key and value:
            display_value = f"{value[:8]}..." if len(str(value)) > 8 else "***"
        print(f"      {key}: {display_value}")
    
    print()
    return config

def main():
    """Función principal"""
    try:
        # Mostrar banner
        print_banner()
        
        # Verificar dependencias
        if not check_dependencies():
            print("❌ No se puede continuar sin las dependencias requeridas")
            sys.exit(1)
        
        # Configurar logging global
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Crear configuración
        config = create_config()
        
        # Importar y crear API mejorada
        try:
            from enhanced_unified_api import EnhancedUnifiedMitosisAPI
            print("📦 Creando instancia de Enhanced Unified Mitosis API...")
            
            api = EnhancedUnifiedMitosisAPI(config)
            print("   ✅ API mejorada inicializada exitosamente")
            
        except ImportError as e:
            print(f"❌ Error importando Enhanced Unified API: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error inicializando API mejorada: {e}")
            sys.exit(1)
        
        # Información de características habilitadas
        print()
        print("🌟 CARACTERÍSTICAS MEJORADAS HABILITADAS:")
        print("   ✅ Ejecución autónoma de tareas completas")
        print("   ✅ Salida en tiempo real en terminal formateada")
        print("   ✅ Monitoreo de progreso paso a paso automático")
        print("   ✅ Entrega de resultados finales estructurada")
        print("   ✅ Compatibilidad total con UI existente y paginador")
        print("   ✅ WebSockets para actualizaciones en tiempo real")
        print()
        
        # Listado de endpoints disponibles
        print("📡 ENDPOINTS API DISPONIBLES:")
        print("   🔹 POST /api/agent/initialize-task - Iniciar tarea autónoma")
        print("   🔹 POST /api/agent/start-task-execution/<task_id> - Iniciar ejecución")
        print("   🔹 GET  /api/agent/get-task-plan/<task_id> - Obtener plan de tarea")
        print("   🔹 POST /api/agent/execute-step/<task_id>/<step_id> - Ejecutar paso")
        print("   🔹 POST /api/agent/chat - Chat con ejecución autónoma")
        print("   🔹 GET  /api/agent/status - Estado mejorado del agente")
        print("   🔹 GET  /api/health - Health check mejorado")
        print()
        
        print("🔌 EVENTOS WEBSOCKET:")
        print("   🔸 connect/disconnect - Conexión de clientes")
        print("   🔸 join_task_room - Unirse a sala de tarea")
        print("   🔸 new_monitor_page - Nueva página del monitor")
        print("   🔸 autonomous_execution_completed - Ejecución finalizada")
        print()
        
        # Iniciar servidor
        host = config['HOST']
        port = config['PORT']
        debug = config['DEBUG_MODE']
        
        print("=" * 80)
        print(f"🚀 INICIANDO SERVIDOR EN {host}:{port}")
        print(f"🛠️  Modo debug: {'HABILITADO' if debug else 'DESHABILITADO'}")
        print("🖥️  Monitorea esta terminal para ver actividad en tiempo real")
        print("🌐 La UI existente funcionará sin cambios")
        print("=" * 80)
        print()
        
        # Ejecutar servidor
        api.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print()
        print("🛑 Interrupción por teclado detectada")
        print("🧹 Realizando apagado limpio...")
        
        # Apagado limpio
        if 'api' in locals():
            api.shutdown()
        
        print("👋 Enhanced Unified Mitosis API apagada exitosamente")
        sys.exit(0)
        
    except Exception as e:
        print()
        print(f"💥 Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Cleanup final
        if 'api' in locals():
            try:
                api.shutdown()
            except:
                pass


if __name__ == "__main__":
    main()