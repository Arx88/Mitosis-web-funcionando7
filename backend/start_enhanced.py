#!/usr/bin/env python3
"""
Script de inicio mejorado para el backend del agente Mitosis
Garantiza que todas las funcionalidades estén disponibles
"""

import os
import sys
import logging
from enhanced_api import EnhancedMitosisAPI

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Función principal"""
    try:
        logger.info("🚀 Iniciando Agente Mitosis Mejorado")
        
        # Crear y ejecutar la API mejorada
        api = EnhancedMitosisAPI()
        
        # Configurar puerto desde variables de entorno
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '0.0.0.0')
        debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        logger.info(f"🌐 Servidor disponible en http://{host}:{port}")
        logger.info("✅ Todas las funcionalidades del backend están activas")
        logger.info("📡 API endpoints disponibles:")
        logger.info("   - /api/agent/health - Estado del sistema")
        logger.info("   - /api/agent/status - Estado del agente")
        logger.info("   - /api/agent/chat - Chat con el agente")
        logger.info("   - /api/agent/upload-files - Subir archivos")
        logger.info("   - /api/agent/files/<task_id> - Obtener archivos de tarea")
        logger.info("   - /api/agent/download/<file_id> - Descargar archivo")
        logger.info("   - /api/agent/share - Crear enlace de compartir")
        
        # Ejecutar servidor
        api.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo servidor...")
    except Exception as e:
        logger.error(f"❌ Error al iniciar el servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

