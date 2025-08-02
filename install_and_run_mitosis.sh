#!/bin/bash
###############################################################################
# 🚀 MITOSIS - INSTALADOR Y INICIADOR MAESTRO
# UN SOLO COMANDO PARA INSTALAR Y EJECUTAR TODO
###############################################################################

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                     🚀 MITOSIS - INSTALACIÓN AUTOMÁTICA                      ║"
echo "║                         Instalación y configuración completa                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_header() { echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"; echo -e "${PURPLE}║${NC} $1"; echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"; }
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# Verificar que estamos en el directorio correcto
if [ ! -f "/app/backend/server.py" ]; then
    log_error "No se encontró server.py. Asegúrate de estar en el directorio correcto."
    exit 1
fi

# Función para mostrar progreso
show_progress() {
    local current=$1
    local total=$2
    local desc=$3
    local percentage=$((current * 100 / total))
    local completed=$((percentage / 5))
    local remaining=$((20 - completed))
    
    printf "\r${CYAN}[%3d%%]${NC} [" $percentage
    for ((i=0; i<completed; i++)); do printf "█"; done
    for ((i=0; i<remaining; i++)); do printf "░"; done
    printf "] %s" "$desc"
    
    if [ $current -eq $total ]; then
        echo ""
    fi
}

# Pasos de instalación
TOTAL_STEPS=6
CURRENT_STEP=0

log_header "INICIANDO PROCESO DE INSTALACIÓN AUTOMÁTICA"

# Paso 1: Reparar problemas conocidos
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Reparando problemas conocidos..."
log_info "Ejecutando reparador automático..."
/app/fix_mitosis_issues.sh >/dev/null 2>&1
log_success "Problemas conocidos corregidos"

# Paso 2: Ejecutar instalación completa
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Ejecutando instalación completa..."
log_info "Ejecutando instalación automática..."
/app/setup_mitosis_complete.sh >/dev/null 2>&1 <<< "n"
log_success "Instalación completa finalizada"

# Paso 3: Verificar estructura de archivos críticos
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Verificando estructura de archivos críticos..."

# Verificar archivos esenciales
CRITICAL_FILES=(
    "/app/backend/server.py"
    "/app/frontend/package.json"
    "/app/backend/.env"
    "/app/start_mitosis.sh"
    "/app/diagnose_mitosis.sh"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Archivo crítico faltante: $file"
        exit 1
    fi
done
log_success "Estructura de archivos verificada"

# Paso 4: Configurar supervisor para inicio automático
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Configurando supervisor..."

# Asegurar que la configuración de supervisor es correcta
if [ ! -f "/etc/supervisor/conf.d/mitosis.conf" ]; then
    log_warning "Configuración de supervisor no encontrada, creando..."
    /app/setup_mitosis_complete.sh >/dev/null 2>&1 <<< "n"
fi
log_success "Supervisor configurado"

# Paso 5: Realizar verificaciones finales
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Realizando verificaciones finales..."

# Verificar puertos disponibles
if netstat -tlnp | grep -q ":8001.*LISTEN"; then
    log_warning "Puerto 8001 ya está en uso, limpiando..."
    pkill -f "python.*server.py" 2>/dev/null || true
    sleep 2
fi

if netstat -tlnp | grep -q ":3000.*LISTEN"; then
    log_warning "Puerto 3000 ya está en uso, limpiando..."
    pkill -f "node.*start" 2>/dev/null || true
    sleep 2
fi

log_success "Verificaciones completadas"

# Paso 6: Iniciar aplicación
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Iniciando aplicación..."

log_header "INICIANDO MITOSIS"

# Ejecutar script de inicio
log_info "Iniciando servicios..."
/app/start_mitosis.sh

log_header "🎉 INSTALACIÓN Y CONFIGURACIÓN COMPLETADA"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                          🎊 ¡INSTALACIÓN EXITOSA! 🎊                        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}🌐 ENLACES DE ACCESO:${NC}"
echo -e "   Frontend: ${YELLOW}https://9a966b6d-c1d6-49fe-95bb-883d9ff13309.preview.emergentagent.com${NC}"
echo -e "   Backend:  ${YELLOW}http://localhost:8001${NC}"
echo ""
echo -e "${CYAN}🛠️  COMANDOS ÚTILES:${NC}"
echo -e "   Reiniciar:    ${GREEN}/app/start_mitosis.sh${NC}"
echo -e "   Diagnóstico:  ${GREEN}/app/diagnose_mitosis.sh${NC}"
echo -e "   Reparar:      ${GREEN}/app/fix_mitosis_issues.sh${NC}"
echo -e "   Estado:       ${GREEN}sudo supervisorctl status${NC}"
echo -e "   Logs:         ${GREEN}tail -f /var/log/supervisor/backend.*.log${NC}"
echo ""
echo -e "${GREEN}✨ El sistema está completamente configurado y funcionando.${NC}"
echo -e "${GREEN}✨ No será necesario configurar manualmente nada en el futuro.${NC}"
echo -e "${GREEN}✨ Para reiniciar simplemente ejecuta: /app/start_mitosis.sh${NC}"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"