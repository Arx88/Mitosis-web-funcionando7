#!/usr/bin/env python3
"""
Mitosis-Beta Enhanced Server
Servidor principal que utiliza la nueva implementación mejorada con ejecución autónoma
"""

import os
import sys
import logging
from typing import Optional

# Añadir directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Función principal del servidor"""
    
    print("🚀 Iniciando Mitosis-Beta Enhanced Server...")
    
    # Configurar logging básico
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Intentar usar la API mejorada
        print("📦 Cargando Enhanced Unified API...")
        from enhanced_unified_api import EnhancedUnifiedMitosisAPI
        
        # Crear configuración básica
        try:
            from agent_core import AgentConfig
            config = AgentConfig()
            # Configurar desde variables de entorno
            config.ollama_url = os.getenv('OLLAMA_BASE_URL', 'https://bef4a4bb93d1.ngrok-free.app')
            config.openrouter_api_key = os.getenv('OPENROUTER_API_KEY', '')
            config.prefer_local_models = True
            config.memory_db_path = os.getenv('MEMORY_DB_PATH', 'mitosis_memory.db')
            config.debug_mode = os.getenv('DEBUG', 'true').lower() == 'true'
        except ImportError:
            config = {
                'OLLAMA_BASE_URL': os.getenv('OLLAMA_BASE_URL', 'https://bef4a4bb93d1.ngrok-free.app'),
                'MONGO_URL': os.getenv('MONGO_URL', 'mongodb://localhost:27017/task_manager'),
                'DEBUG_MODE': os.getenv('DEBUG', 'true').lower() == 'true',
                'HOST': os.getenv('HOST', '0.0.0.0'),
                'PORT': int(os.getenv('PORT', '8001'))
            }
        
        # Crear API mejorada
        enhanced_api = EnhancedUnifiedMitosisAPI(config)
        print("✅ Enhanced Unified API cargada exitosamente")
        
        # Usar la aplicación Flask de la API mejorada
        app = enhanced_api.app if hasattr(enhanced_api, 'app') else None
        
        if app is None:
            raise Exception("No se pudo obtener la aplicación Flask de la API mejorada")
        
        # Modo de ejecución - usar el método run de la API mejorada directamente
        print("🔄 Iniciando en modo Enhanced API con ejecución autónoma...")
        print("📡 Endpoints mejorados disponibles:")
        print("   - POST /api/agent/initialize-task")
        print("   - POST /api/agent/chat (con detección autónoma)")
        print("   - GET /api/agent/status (mejorado)")
        print("   - GET /api/health (mejorado)")
        print("🖥️  Salida en tiempo real habilitada en terminal")
        
        # La API mejorada se encarga de todo
        enhanced_api.run(
            host=config['HOST'], 
            port=config['PORT'], 
            debug=config['DEBUG_MODE']
        )
        
    except ImportError as e:
        print(f"⚠️ Enhanced API no disponible: {e}")
        print("📍 Intentando fallback a API estándar...")
        
        try:
            # Fallback a la API unificada estándar
            from unified_api import UnifiedMitosisAPI
            from agent_core import AgentConfig
            
            config = AgentConfig()
            api = UnifiedMitosisAPI(config)
            app = api.app
            
            print("✅ API estándar cargada como fallback")
            
            # Ejecutar con Flask estándar
            app.run(
                host='0.0.0.0',
                port=8001,
                debug=True
            )
            
        except ImportError as fallback_error:
            print(f"❌ Error cargando API de fallback: {fallback_error}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()