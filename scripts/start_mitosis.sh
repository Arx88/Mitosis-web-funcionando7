#!/bin/bash

# =============================================================================
# MITOSIS STARTUP SCRIPT - INSTALACIÓN Y ARRANQUE ROBUSTO
# Versión: 2.0 - Julio 2025
# =============================================================================

echo "🚀 INICIANDO MITOSIS - SISTEMA DE AGENTE AUTÓNOMO..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función de logging mejorada
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/mitosis-startup.log
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a /var/log/mitosis-startup.log
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}" | tee -a /var/log/mitosis-startup.log
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a /var/log/mitosis-startup.log
}

log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}" | tee -a /var/log/mitosis-startup.log
}

# =============================================================================
# VERIFICACIONES PREVIAS CRÍTICAS
# =============================================================================

log_info "🔍 INICIANDO VERIFICACIONES PREVIAS..."

# Verificar que estamos en el directorio correcto
if [ ! -d "/app" ]; then
    log_error "Directorio /app no encontrado. ¿Estás ejecutando desde el contenedor correcto?"
    exit 1
fi

cd /app

# Verificar archivos críticos del backend
log_info "🔍 Verificando archivos críticos del backend..."

if [ ! -f "/app/backend/server.py" ]; then
    log_error "Archivo server.py no encontrado en /app/backend/"
    exit 1
fi

if [ ! -f "/app/backend/requirements.txt" ]; then
    log_error "Archivo requirements.txt no encontrado en /app/backend/"
    exit 1
fi

# Verificar archivos críticos del frontend
log_info "🔍 Verificando archivos críticos del frontend..."

if [ ! -f "/app/frontend/package.json" ]; then
    log_error "Archivo package.json no encontrado en /app/frontend/"
    exit 1
fi

log_success "Verificaciones previas completadas"

# =============================================================================
# CORRECCIÓN AUTOMÁTICA DE CONFIGURACIÓN DEL SUPERVISOR
# =============================================================================

log_info "🔧 VERIFICANDO Y CORRIGIENDO CONFIGURACIÓN DEL SUPERVISOR..."

SUPERVISOR_CONFIG="/etc/supervisor/conf.d/supervisord.conf"

if [ -f "$SUPERVISOR_CONFIG" ]; then
    # Verificar si existe el error del server_simple.py
    if grep -q "server_simple.py" "$SUPERVISOR_CONFIG"; then
        log_warning "Detectado error en configuración del supervisor (server_simple.py)"
        
        # Crear backup
        sudo cp "$SUPERVISOR_CONFIG" "$SUPERVISOR_CONFIG.backup.$(date +%s)"
        log_info "Backup creado en $SUPERVISOR_CONFIG.backup.$(date +%s)"
        
        # Corregir la configuración
        sudo sed -i 's/server_simple.py/server.py/g' "$SUPERVISOR_CONFIG"
        log_success "Configuración del supervisor corregida (server_simple.py → server.py)"
    else
        log_success "Configuración del supervisor está correcta"
    fi
else
    log_error "Archivo de configuración del supervisor no encontrado en $SUPERVISOR_CONFIG"
    exit 1
fi

# =============================================================================
# INSTALACIÓN DE DEPENDENCIAS DEL BACKEND
# =============================================================================

log_info "📦 INSTALANDO DEPENDENCIAS DEL BACKEND..."

# Verificar que el entorno virtual existe
if [ ! -d "/root/.venv" ]; then
    log_warning "Entorno virtual no encontrado, creándolo..."
    python3 -m venv /root/.venv
fi

# Activar entorno virtual
source /root/.venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias críticas del backend
log_info "Instalando dependencias críticas..."

# Lista de dependencias críticas con versiones específicas
CRITICAL_DEPENDENCIES=(
    "fastapi==0.104.1"
    "uvicorn[standard]==0.24.0"  
    "python-dotenv==1.0.1"
    "pymongo==4.8.0"
    "requests==2.32.3"
    "sentence-transformers==3.0.1"
    "transformers==4.42.4"
)

for dep in "${CRITICAL_DEPENDENCIES[@]}"; do
    log_info "Instalando $dep..."
    pip install "$dep" --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
    if [ $? -eq 0 ]; then
        log_success "✅ $dep instalado correctamente"
    else
        log_error "❌ Error instalando $dep"
        exit 1
    fi
done

# Instalar todas las dependencias del requirements.txt
log_info "Instalando dependencias completas del backend..."
cd /app/backend
pip install -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Verificar importaciones críticas
log_info "🔍 Verificando importaciones críticas..."

python3 -c "
import multidict; print('✅ multidict OK')
import attrs; print('✅ attrs OK') 
import aiohttp; print('✅ aiohttp OK')
import fastapi; print('✅ fastapi OK')
import uvicorn; print('✅ uvicorn OK')
"

if [ $? -eq 0 ]; then
    log_success "Todas las importaciones críticas verificadas"
else
    log_error "Error en verificación de importaciones críticas"
    exit 1
fi

# =============================================================================
# INSTALACIÓN DE DEPENDENCIAS DEL FRONTEND
# =============================================================================

log_info "🎨 INSTALANDO DEPENDENCIAS DEL FRONTEND..."

cd /app/frontend

# Verificar que yarn está disponible
if ! command -v yarn &> /dev/null; then
    log_error "Yarn no está disponible. Instalándolo..."
    npm install -g yarn
fi

# Instalar dependencias del frontend
yarn install

if [ $? -eq 0 ]; then
    log_success "Dependencias del frontend instaladas correctamente"
else
    log_error "Error instalando dependencias del frontend"
    exit 1
fi

# =============================================================================
# CONSTRUCCIÓN ROBUSTA DEL FRONTEND
# =============================================================================

log_info "🏗️ CONSTRUYENDO FRONTEND PARA PRODUCCIÓN..."

cd /app/frontend

# Limpiar builds anteriores
if [ -d "dist" ]; then
    rm -rf dist
    log_info "Build anterior limpiado"
fi

# Construir para producción
yarn build

if [ $? -eq 0 ]; then
    log_success "Frontend construido exitosamente"
else
    log_error "Error construyendo el frontend"
    exit 1
fi

# Verificar que se creó el directorio dist
if [ ! -d "dist" ]; then
    log_error "Directorio dist no fue creado después del build"
    exit 1
fi

# Instalar serve globalmente si no existe
if ! command -v serve &> /dev/null; then
    log_info "Instalando serve para producción..."
    npm install -g serve
fi

# =============================================================================
# CONFIGURACIÓN Y ARRANQUE DE SERVICIOS
# =============================================================================

log_info "🛠️ CONFIGURANDO SERVICIOS..."

# Detener todos los servicios primero
sudo supervisorctl stop all

# Recargar configuración del supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Esperar un momento para la estabilización
sleep 3

# Arrancar servicios en orden específico
log_info "🚀 INICIANDO SERVICIOS..."

# 1. MongoDB primero
sudo supervisorctl start mongodb
sleep 3

# 2. Backend
sudo supervisorctl start backend
sleep 5

# 3. Frontend
sudo supervisorctl start frontend
sleep 3

# 4. Servicios de monitoreo
sudo supervisorctl start stability-monitor

# =============================================================================
# VERIFICACIÓN FINAL Y HEALTH CHECK
# =============================================================================

log_info "🔍 REALIZANDO VERIFICACIONES FINALES..."

# Verificar estado de servicios
SERVICES=("mongodb" "backend" "frontend" "stability-monitor")

for service in "${SERVICES[@]}"; do
    status=$(sudo supervisorctl status $service 2>/dev/null | awk '{print $2}')
    if [ "$status" = "RUNNING" ]; then
        log_success "$service está ejecutándose correctamente"
    else
        log_warning "$service no está ejecutándose correctamente: $status"
    fi
done

# Health check del backend
log_info "🏥 Realizando health check del backend..."
sleep 5  # Dar tiempo al backend para inicializarse

backend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/health 2>/dev/null)

if [ "$backend_health" = "200" ]; then
    log_success "Backend health check exitoso"
else
    log_warning "Backend health check falló (HTTP $backend_health)"
fi

# Health check del frontend
log_info "🌐 Realizando health check del frontend..."

frontend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)

if [ "$frontend_health" = "200" ]; then
    log_success "Frontend health check exitoso"
else
    log_warning "Frontend health check falló (HTTP $frontend_health)"
fi

# =============================================================================
# RESUMEN FINAL
# =============================================================================

echo ""
echo "=========================================="
echo "🎉 MITOSIS STARTUP COMPLETADO"
echo "=========================================="
echo ""

# Estado final de servicios
echo "📊 ESTADO DE SERVICIOS:"
sudo supervisorctl status

echo ""
echo "🌐 ENDPOINTS DISPONIBLES:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8001"
echo "  - Health Check: http://localhost:8001/api/health"
echo ""

echo "📚 COMANDOS ÚTILES:"
echo "  - Ver logs: sudo supervisorctl tail -f <servicio>"
echo "  - Reiniciar servicio: sudo supervisorctl restart <servicio>"
echo "  - Estado de servicios: sudo supervisorctl status"
echo ""

echo "📋 ARCHIVOS DE LOG:"
echo "  - Startup: /var/log/mitosis-startup.log"
echo "  - Backend: /var/log/supervisor/backend.*.log"
echo "  - Frontend: /var/log/supervisor/frontend.*.log"
echo ""

log_success "🚀 MITOSIS está listo para usar!"

echo "✨ Para futuras ejecuciones, simplemente ejecuta:"
echo "   ./scripts/start_mitosis.sh"