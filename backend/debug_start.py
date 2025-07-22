#!/usr/bin/env python3
import traceback
import sys
import os

# Añadir directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from enhanced_unified_api import EnhancedUnifiedMitosisAPI
    
    config = {
        'OLLAMA_URL': 'https://bef4a4bb93d1.ngrok-free.app',
        'DEBUG_MODE': True
    }
    
    print("Creando API...")
    api = EnhancedUnifiedMitosisAPI(config)
    print("✅ API creada exitosamente")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Traceback completo:")
    traceback.print_exc()