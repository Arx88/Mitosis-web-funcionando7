#!/bin/bash

# Script de construcción para producción
# Asegura que la aplicación se construya correctamente durante la instalación

set -e  # Salir en caso de error

echo "🚀 Iniciando construcción para producción..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para logging con timestamp
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Verificar que estamos en el directorio correcto
if [ ! -f "package.json" ]; then
    error "No se encontró package.json. Este script debe ejecutarse desde el directorio frontend."
fi

# Verificar dependencias de Node.js
if ! command -v node &> /dev/null; then
    error "Node.js no está instalado"
fi

if ! command -v yarn &> /dev/null; then
    error "Yarn no está instalado"
fi

# Verificar si existe archivo de configuración de build
if [ ! -f "vite.config.js" ] && [ ! -f "vite.config.ts" ]; then
    warn "No se encontró vite.config.js/ts"
fi

# Limpiar builds anteriores
log "Limpiando builds anteriores..."
rm -rf dist/
rm -rf build/

# Instalar dependencias
log "Instalando dependencias..."
yarn install --frozen-lockfile

# Construir para producción
log "Construyendo aplicación para producción..."
yarn build

# Verificar que la construcción fue exitosa
if [ ! -d "dist" ]; then
    error "La construcción falló - no se encontró directorio dist/"
fi

# Verificar archivos importantes
if [ ! -f "dist/index.html" ]; then
    error "La construcción falló - no se encontró index.html"
fi

# Contar archivos generados
FILE_COUNT=$(find dist -type f | wc -l)
log "Se generaron $FILE_COUNT archivos en dist/"

# Verificar que existe serve globalmente
if ! command -v serve &> /dev/null; then
    log "Instalando serve globalmente..."
    npm install -g serve
fi

# Verificar que existe http-server globalmente (alternativa)
if ! command -v http-server &> /dev/null; then
    log "Instalando http-server globalmente..."
    npm install -g http-server
fi

# Actualizar configuración de supervisor
log "Actualizando configuración de supervisor..."
SUPERVISOR_CONFIG="/etc/supervisor/conf.d/supervisord.conf"

if [ -f "$SUPERVISOR_CONFIG" ]; then
    # Crear backup
    cp "$SUPERVISOR_CONFIG" "$SUPERVISOR_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Actualizar configuración del frontend
    if grep -q "command=yarn start" "$SUPERVISOR_CONFIG"; then
        sed -i 's|command=yarn start|command=http-server dist -p 3000 -a 0.0.0.0 --cors|g' "$SUPERVISOR_CONFIG"
        log "Configuración de supervisor actualizada para usar http-server"
    elif grep -q "command=serve" "$SUPERVISOR_CONFIG"; then
        log "Configuración de supervisor ya está usando serve"
    else
        warn "No se encontró configuración de frontend en supervisor"
    fi
else
    warn "No se encontró configuración de supervisor"
fi

# Reiniciar servicio frontend
log "Reiniciando servicio frontend..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart frontend
    log "Servicio frontend reiniciado"
else
    warn "supervisorctl no está disponible"
fi

# Verificar que el servicio está corriendo
log "Verificando estado de servicios..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl status
fi

# Verificar que la aplicación responde
log "Verificando que la aplicación responde..."
sleep 3
if curl -s http://localhost:3000 > /dev/null; then
    log "✅ Aplicación funcionando correctamente en modo producción"
else
    warn "La aplicación no responde en localhost:3000"
fi

# Mostrar información de la construcción
log "Información de la construcción:"
log "- Directorio: $(pwd)"
log "- Archivos generados: $FILE_COUNT"
log "- Tamaño total: $(du -sh dist/ | cut -f1)"
log "- Modo: Producción"

# Mostrar archivos principales
log "Archivos principales generados:"
find dist -name "*.html" -o -name "*.js" -o -name "*.css" | head -10

log "🎉 Construcción para producción completada exitosamente!"