#!/bin/bash

# =============================================================================
# DEPLOYMENT ROBUSTO - EJECUTAR ANTES DE CUALQUIER CAMBIO
# =============================================================================

echo "🚀 INICIANDO DEPLOYMENT ROBUSTO..."

# Parar todos los servicios
echo "🛑 Parando servicios..."
sudo supervisorctl stop all

# Ejecutar auto-build
echo "🏗️  Ejecutando auto-build..."
/app/scripts/auto-build.sh

# Configurar supervisor robusto
echo "🛡️  Configurando supervisor..."
/app/scripts/setup-robust-supervisor.sh

# Recargar configuración de supervisor
echo "🔄 Recargando supervisor..."
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar servicios
echo "▶️  Iniciando servicios..."
sudo supervisorctl start all

# Esperar a que se estabilicen
echo "⏳ Esperando estabilización..."
sleep 10

# Verificar estado
echo "🔍 Verificando estado..."
sudo supervisorctl status

# Verificar que el frontend está en producción
if pgrep -f "serve.*dist" > /dev/null; then
    echo "✅ SUCCESS: Frontend en modo producción"
else
    echo "❌ ERROR: Frontend no está en producción"
    exit 1
fi

# Verificar que el backend está funcionando
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ SUCCESS: Backend funcionando"
else
    echo "❌ ERROR: Backend no responde"
    exit 1
fi

echo "🎉 DEPLOYMENT ROBUSTO COMPLETADO"