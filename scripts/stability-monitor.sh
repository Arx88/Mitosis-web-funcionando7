#!/bin/bash

# =============================================================================
# SISTEMA DE MONITOREO Y AUTO-CORRECCIÓN
# =============================================================================

echo "🔍 INICIANDO MONITOREO DE ESTABILIDAD..."

# Función para verificar si está en modo desarrollo
check_development_mode() {
    if pgrep -f "vite.*--host" > /dev/null; then
        return 0  # Está en desarrollo
    else
        return 1  # No está en desarrollo
    fi
}

# Función para verificar si el frontend está sirviendo archivos estáticos
check_production_mode() {
    if pgrep -f "serve.*dist" > /dev/null; then
        return 0  # Está en producción
    else
        return 1  # No está en producción
    fi
}

# Función para auto-corregir
auto_correct() {
    echo "🚨 MODO DESARROLLO DETECTADO - INICIANDO AUTO-CORRECCIÓN..."
    
    # Parar frontend
    sudo supervisorctl stop frontend
    sleep 3
    
    # Ejecutar auto-build
    /app/scripts/auto-build.sh
    
    # Reiniciar frontend en producción
    sudo supervisorctl start frontend
    sleep 5
    
    # Verificar corrección
    if check_production_mode; then
        echo "✅ AUTO-CORRECCIÓN EXITOSA - AHORA EN PRODUCCIÓN"
    else
        echo "❌ AUTO-CORRECCIÓN FALLÓ - REVISIÓN MANUAL REQUERIDA"
    fi
}

# Monitoreo continuo
while true; do
    if check_development_mode; then
        echo "⚠️  $(date): Modo desarrollo detectado - ejecutando auto-corrección..."
        auto_correct
    elif check_production_mode; then
        echo "✅ $(date): Sistema estable en producción"
    else
        echo "❓ $(date): Estado desconocido - verificando..."
        sudo supervisorctl status frontend
    fi
    
    sleep 30  # Verificar cada 30 segundos
done