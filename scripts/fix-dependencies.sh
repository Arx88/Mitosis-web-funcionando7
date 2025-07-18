#!/bin/bash

# =============================================================================
# REPARACIÓN AUTOMÁTICA DE DEPENDENCIAS
# =============================================================================

echo "🔧 REPARANDO DEPENDENCIAS AUTOMÁTICAMENTE..."

cd /app/backend

# Instalar dependencias críticas individualmente
echo "📦 Instalando dependencias críticas..."

# Dependencias básicas
pip install multidict>=6.0.0
pip install attrs>=25.0.0
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install python-dotenv==1.0.1

# Dependencias de base de datos
pip install pymongo==4.8.0

# Dependencias HTTP
pip install httpx>=0.24.0
pip install requests==2.32.3

# Dependencias básicas de AI
pip install sentence-transformers==3.0.1
pip install transformers==4.42.4

# Verificar importaciones críticas
echo "🔍 Verificando importaciones críticas..."

python3 -c "
try:
    import multidict
    print('✅ multidict OK')
except ImportError as e:
    print(f'❌ multidict ERROR: {e}')

try:
    import attr
    print('✅ attrs OK')
except ImportError as e:
    print(f'❌ attrs ERROR: {e}')

try:
    import aiohttp
    print('✅ aiohttp OK')
except ImportError as e:
    print(f'❌ aiohttp ERROR: {e}')

try:
    import fastapi
    print('✅ fastapi OK')
except ImportError as e:
    print(f'❌ fastapi ERROR: {e}')

try:
    import uvicorn
    print('✅ uvicorn OK')
except ImportError as e:
    print(f'❌ uvicorn ERROR: {e}')
"

echo "✅ REPARACIÓN DE DEPENDENCIAS COMPLETADA"