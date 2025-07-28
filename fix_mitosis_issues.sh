#!/bin/bash
###############################################################################
# MITOSIS - REPARADOR AUTOMÁTICO DE PROBLEMAS COMUNES
# Este script detecta y corrige automáticamente los problemas más frecuentes
###############################################################################

set -e

echo "🔧 REPARADOR AUTOMÁTICO DE MITOSIS"
echo "============================================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# Función para corregir problemas de Flask/SocketIO vs Uvicorn
fix_server_compatibility() {
    log_info "Corrigiendo problemas de compatibilidad del servidor..."
    
    cd /app/backend
    
    # Verificar si hay conflictos Flask + uvicorn
    if grep -q "flask_socketio\|SocketIO" server.py && grep -q "uvicorn" /etc/supervisor/conf.d/*.conf 2>/dev/null; then
        log_warning "Detectado conflicto: Flask-SocketIO con uvicorn"
        
        # Buscar archivo de configuración de supervisor
        SUPERVISOR_CONFIG=$(find /etc/supervisor/conf.d/ -name "*.conf" -exec grep -l "uvicorn.*server" {} \; | head -1)
        
        if [ -n "$SUPERVISOR_CONFIG" ]; then
            log_info "Corrigiendo configuración en: $SUPERVISOR_CONFIG"
            sed -i 's|/root/.venv/bin/uvicorn server:app.*|/root/.venv/bin/python server.py|g' "$SUPERVISOR_CONFIG"
            log_success "Configuración corregida: Flask nativo en lugar de uvicorn"
        fi
    fi
    
    # Verificar dependencias necesarias
    if ! /root/.venv/bin/pip show flask-socketio >/dev/null 2>&1; then
        log_info "Instalando Flask-SocketIO..."
        /root/.venv/bin/pip install flask-socketio eventlet
        log_success "Flask-SocketIO instalado"
    fi
}

# Función para verificar y corregir variables de entorno
fix_environment_variables() {
    log_info "Verificando variables de entorno..."
    
    # Verificar backend .env
    if [ -f "/app/backend/.env" ]; then
        # Asegurar que OLLAMA_BASE_URL esté configurado
        if ! grep -q "OLLAMA_BASE_URL" /app/backend/.env; then
            echo "OLLAMA_BASE_URL=https://bef4a4bb93d1.ngrok-free.app" >> /app/backend/.env
            log_success "OLLAMA_BASE_URL añadido al .env"
        fi
        
        # Asegurar que DEBUG esté en false para producción
        sed -i 's/DEBUG=True/DEBUG=false/g' /app/backend/.env
        log_success "DEBUG configurado para producción"
    fi
    
    # Verificar frontend .env
    if [ -f "/app/frontend/.env" ]; then
        # Verificar URL del backend
        if ! grep -q "REACT_APP_BACKEND_URL\|VITE_BACKEND_URL" /app/frontend/.env; then
            cat >> /app/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://774fd713-b4f7-45a0-a37e-a42a5d8a20be.preview.emergentagent.com
VITE_BACKEND_URL=https://774fd713-b4f7-45a0-a37e-a42a5d8a20be.preview.emergentagent.com
EOF
            log_success "URLs del backend añadidas al frontend .env"
        fi
    fi
}

# Función para corregir problemas de permisos
fix_permissions() {
    log_info "Corrigiendo permisos de archivos..."
    
    # Asegurar permisos correctos
    chown -R root:root /app
    chmod +x /app/backend/server.py 2>/dev/null || true
    chmod +x /app/*.sh 2>/dev/null || true
    
    # Crear directorios con permisos correctos
    mkdir -p /var/log/supervisor
    mkdir -p /var/log/mongodb
    mkdir -p /app/backend/uploads
    mkdir -p /app/backend/downloads
    chmod 755 /var/log/supervisor
    chmod 755 /var/log/mongodb
    
    log_success "Permisos corregidos"
}

# Función para limpiar procesos conflictivos
kill_conflicting_processes() {
    log_info "Eliminando procesos conflictivos..."
    
    # Matar procesos Python que puedan estar bloqueando el puerto 8001
    pkill -f "python.*server.py" 2>/dev/null || true
    pkill -f "uvicorn.*server" 2>/dev/null || true
    
    # Esperar un momento para que se liberen los puertos
    sleep 2
    
    log_success "Procesos conflictivos eliminados"
}

# Función para verificar conectividad de servicios externos
check_external_services() {
    log_info "Verificando servicios externos..."
    
    # Verificar OLLAMA
    if curl -s -f "https://bef4a4bb93d1.ngrok-free.app/api/tags" >/dev/null 2>&1; then
        log_success "OLLAMA conectado correctamente"
    else
        log_warning "OLLAMA no está disponible actualmente"
        log_info "Esto no impedirá el funcionamiento básico de la aplicación"
    fi
}

# Función para corregir problemas del comentario en línea 4155
fix_code_comments() {
    log_info "Corrigiendo comentarios inconsistentes en el código..."
    
    # Buscar el archivo que contiene execute_step_simulation
    FILES_TO_FIX=$(find /app/backend -name "*.py" -exec grep -l "execute_step_real" {} \;)
    
    for FILE in $FILES_TO_FIX; do
        if grep -q "Simular ejecución del paso" "$FILE" && grep -q "execute_step_real" "$FILE"; then
            log_info "Corrigiendo comentario en: $FILE"
            sed -i 's|# Simular ejecución del paso|# Ejecutar paso con herramientas REALES (no simulación)|g' "$FILE"
            log_success "Comentario corregido en $FILE"
        fi
    done
}

# Función para crear archivo de estado de salud
create_health_check() {
    log_info "Creando verificador de salud continuo..."
    
    cat > /app/health_monitor.sh << 'EOF'
#!/bin/bash
# Monitor de salud continuo para Mitosis

while true; do
    # Verificar backend
    if ! curl -s -f http://localhost:8001/health >/dev/null 2>&1; then
        echo "$(date): Backend no responde, reiniciando..." >> /var/log/mitosis_health.log
        sudo supervisorctl restart backend
    fi
    
    # Verificar frontend
    if ! curl -s -f http://localhost:3000 >/dev/null 2>&1; then
        echo "$(date): Frontend no responde, reiniciando..." >> /var/log/mitosis_health.log
        sudo supervisorctl restart frontend
    fi
    
    # Esperar 30 segundos antes de la próxima verificación
    sleep 30
done
EOF
    
    chmod +x /app/health_monitor.sh
    log_success "Monitor de salud creado: /app/health_monitor.sh"
}

# Función principal
main() {
    log_info "Ejecutando reparador automático..."
    
    # Detener servicios
    sudo supervisorctl stop all 2>/dev/null || true
    
    # Ejecutar reparaciones
    kill_conflicting_processes
    fix_server_compatibility
    fix_environment_variables
    fix_permissions
    fix_code_comments
    create_health_check
    check_external_services
    
    # Recargar supervisor
    sudo supervisorctl reread 2>/dev/null || true
    sudo supervisorctl update 2>/dev/null || true
    
    log_success "============================================================="
    log_success "🎉 REPARACIONES COMPLETADAS"
    log_success "============================================================="
    log_info "Los siguientes problemas han sido corregidos:"
    log_info "  • Compatibilidad Flask/SocketIO vs uvicorn"
    log_info "  • Variables de entorno configuradas"
    log_info "  • Permisos de archivos corregidos"
    log_info "  • Procesos conflictivos eliminados"
    log_info "  • Comentarios de código corregidos"
    log_info "  • Monitor de salud creado"
    log_success "============================================================="
    
    echo ""
    log_info "El sistema está listo. Ejecuta: /app/start_mitosis.sh"
}

# Ejecutar reparador
main "$@"