#!/bin/bash

# =============================================================================
# AUTO-BUILD SCRIPT - GARANTIZA SIEMPRE PRODUCCIÓN
# =============================================================================

echo "🔧 INICIANDO AUTO-BUILD ROBUSTO..."

# Verificar si estamos en modo desarrollo
if pgrep -f "vite.*--host" > /dev/null; then
    echo "⚠️  MODO DESARROLLO DETECTADO - CORRIGIENDO..."
    sudo supervisorctl stop frontend
    sleep 2
fi

# Navegar al directorio frontend
cd /app/frontend

# Limpiar builds anteriores
echo "🧹 Limpiando builds anteriores..."
rm -rf dist/ node_modules/.vite/ 2>/dev/null || true

# Verificar que node_modules existe
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias..."
    yarn install --frozen-lockfile
fi

# Construir para producción
echo "🏗️  Construyendo para producción..."
npm run build

# Verificar que el build fue exitoso
if [ ! -d "dist" ]; then
    echo "❌ ERROR: Build falló - dist/ no existe"
    exit 1
fi

# Verificar que hay archivos en dist
if [ ! -f "dist/index.html" ]; then
    echo "❌ ERROR: Build incompleto - falta index.html"
    exit 1
fi

# Instalar serve globalmente si no existe
if ! command -v serve &> /dev/null; then
    echo "📦 Instalando serve..."
    npm install -g serve
fi

echo "✅ AUTO-BUILD COMPLETADO EXITOSAMENTE"
echo "📁 Archivos de producción listos en /app/frontend/dist/"