#!/bin/bash
###############################################################################
# MITOSIS - INSTALACIÓN AUTOMÁTICA COMPLETA Y ROBUSTA
# Este script instala y configura todo automáticamente sin intervención manual
###############################################################################

set -e  # Exit on any error

echo "🚀 INICIANDO INSTALACIÓN AUTOMÁTICA DE MITOSIS..."
echo "============================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✅]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

log_error() {
    echo -e "${RED}[❌]${NC} $1"
}

# Función para verificar y instalar dependencias
install_dependencies() {
    log_info "Verificando e instalando dependencias..."
    
    # Backend dependencies
    cd /app/backend
    if [ -f "requirements.txt" ]; then
        log_info "Instalando dependencias de Python..."
        /root/.venv/bin/pip install -r requirements.txt --quiet
        log_success "Dependencias de Python instaladas"
    fi
    
    # Frontend dependencies
    cd /app/frontend
    if [ -f "package.json" ]; then
        log_info "Instalando dependencias de Node.js..."
        yarn install --silent
        log_success "Dependencias de Node.js instaladas"
    fi
    
    # Playwright browsers
    log_info "Verificando navegadores Playwright..."
    if [ ! -d "/pw-browsers/chromium-1124" ]; then
        log_info "Instalando navegadores Playwright..."
        python -m playwright install chromium --quiet
        log_success "Navegadores Playwright instalados"
    else
        log_success "Navegadores Playwright ya instalados"
    fi
}

# Función para detectar el tipo correcto de servidor
detect_server_type() {
    log_info "Detectando tipo de servidor necesario..."
    
    cd /app/backend
    
    # Verificar si usa Flask-SocketIO
    if grep -q "flask_socketio" server.py 2>/dev/null || grep -q "SocketIO" server.py 2>/dev/null; then
        SERVER_TYPE="flask_socketio"
        SERVER_COMMAND="/root/.venv/bin/python server.py"
        log_success "Detectado: Flask con SocketIO - Servidor nativo"
    # Verificar si es Flask normal
    elif grep -q "from flask import" server.py 2>/dev/null; then
        SERVER_TYPE="flask"
        SERVER_COMMAND="/root/.venv/bin/gunicorn -w 1 -b 0.0.0.0:8001 server:app"
        log_success "Detectado: Flask normal - Gunicorn"
    # Si es FastAPI o tiene ASGI
    elif grep -q "FastAPI\|uvicorn\|asgi" server.py 2>/dev/null; then
        SERVER_TYPE="fastapi"
        SERVER_COMMAND="/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1"
        log_success "Detectado: FastAPI/ASGI - Uvicorn"
    else
        # Default a Flask con SocketIO que es lo más común en este proyecto
        SERVER_TYPE="flask_socketio"
        SERVER_COMMAND="/root/.venv/bin/python server.py"
        log_warning "Tipo no detectado, usando Flask nativo por defecto"
    fi
    
    log_info "Tipo de servidor: $SERVER_TYPE"
    log_info "Comando: $SERVER_COMMAND"
}

# Función para crear configuración robusta de supervisor
create_robust_supervisor_config() {
    log_info "Creando configuración robusta de supervisor..."
    
    cat > /etc/supervisor/conf.d/mitosis.conf << EOF
[program:backend]
command=$SERVER_COMMAND
directory=/app/backend
autostart=true
autorestart=true
user=root
environment=PATH="/root/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
           PYTHONPATH="/app/backend:/app/backend/src",
           DEBUG=false,
           FLASK_ENV=production
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
stderr_logfile_maxbytes=50MB
stdout_logfile_maxbytes=50MB
stderr_logfile_backups=5
stdout_logfile_backups=5
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true

[program:frontend]
command=yarn start
environment=HOST="0.0.0.0",
           PORT="3000",
           NODE_ENV="production",
           CI="false"
directory=/app/frontend
autostart=true
autorestart=true
user=root
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
stderr_logfile_maxbytes=50MB
stdout_logfile_maxbytes=50MB
stderr_logfile_backups=5
stdout_logfile_backups=5
stopsignal=TERM
stopwaitsecs=50
stopasgroup=true
killasgroup=true

[program:mongodb]
command=/usr/bin/mongod --bind_ip_all --dbpath=/var/lib/mongodb --logpath=/var/log/mongodb/mongod.log --fork --config /etc/mongod.conf
autostart=true
autorestart=true
user=root
stderr_logfile=/var/log/supervisor/mongodb.err.log
stdout_logfile=/var/log/supervisor/mongodb.out.log
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true

[group:mitosis]
programs=backend,frontend,mongodb
priority=999
EOF

    log_success "Configuración de supervisor creada"
}

# Función para verificar y corregir estructura de archivos
verify_file_structure() {
    log_info "Verificando estructura de archivos..."
    
    # Crear directorios necesarios
    mkdir -p /var/log/mongodb
    mkdir -p /var/log/supervisor
    mkdir -p /app/backend/uploads
    mkdir -p /app/backend/downloads
    mkdir -p /app/backend/logs
    
    # Verificar permisos
    chown -R root:root /app
    chmod +x /app/backend/server.py 2>/dev/null || true
    
    # Crear archivo de configuración de MongoDB si no existe
    if [ ! -f "/etc/mongod.conf" ]; then
        cat > /etc/mongod.conf << EOF
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
net:
  port: 27017
  bindIp: 127.0.0.1,0.0.0.0
processManagement:
  fork: true
  pidFilePath: /var/run/mongodb/mongod.pid
EOF
    fi
    
    log_success "Estructura de archivos verificada"
}

# Función para instalar herramientas necesarias
install_tools() {
    log_info "Instalando herramientas adicionales..."
    
    # Instalar gunicorn si se necesita
    if [ "$SERVER_TYPE" = "flask" ]; then
        /root/.venv/bin/pip install gunicorn --quiet
        log_success "Gunicorn instalado"
    fi
    
    # Verificar que MongoDB esté disponible
    if ! command -v mongod &> /dev/null; then
        log_error "MongoDB no está instalado"
        exit 1
    fi
    
    log_success "Herramientas instaladas"
}

# Función para crear script de inicio robusto
create_startup_script() {
    log_info "Creando script de inicio automático..."
    
    cat > /app/start_mitosis.sh << 'EOF'
#!/bin/bash
###############################################################################
# MITOSIS - SCRIPT DE INICIO ROBUSTO
###############################################################################

set -e

echo "🚀 Iniciando Mitosis..."

# Función para verificar si un servicio está funcionando
check_service() {
    local service=$1
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if sudo supervisorctl status $service | grep -q "RUNNING"; then
            echo "✅ $service está funcionando"
            return 0
        fi
        echo "⏳ Esperando a que $service inicie... (intento $attempt/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service no pudo iniciarse"
    return 1
}

# Función para verificar conectividad de backend
check_backend() {
    local max_attempts=15
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:8001/health >/dev/null 2>&1; then
            echo "✅ Backend respondiendo correctamente"
            return 0
        fi
        echo "⏳ Esperando respuesta del backend... (intento $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Backend no responde"
    return 1
}

# Función para verificar OLLAMA
check_ollama() {
    echo "🔍 Verificando conexión OLLAMA..."
    if curl -s -f "https://bef4a4bb93d1.ngrok-free.app/api/tags" >/dev/null 2>&1; then
        echo "✅ OLLAMA conectado correctamente"
        return 0
    else
        echo "⚠️ OLLAMA no está disponible (esto no impedirá el inicio)"
        return 1
    fi
}

echo "📋 Iniciando servicios..."

# Recargar configuración de supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar servicios
sudo supervisorctl start mitosis:*

# Verificar servicios
echo "🔍 Verificando servicios..."
check_service "mongodb"
check_service "backend" 
check_service "frontend"

# Verificar conectividad
echo "🔍 Verificando conectividad..."
check_backend
check_ollama

echo ""
echo "🎉 MITOSIS INICIADO CORRECTAMENTE"
echo "============================================================="
echo "Frontend: https://4773fe74-f588-4919-a5bd-181a9236c6f1.preview.emergentagent.com"
echo "Backend API: http://localhost:8001"
echo "============================================================="
echo ""

# Mostrar estado de los servicios
sudo supervisorctl status mitosis:*
EOF

    chmod +x /app/start_mitosis.sh
    log_success "Script de inicio creado: /app/start_mitosis.sh"
}

# Función para crear script de diagnóstico
create_diagnostic_script() {
    log_info "Creando script de diagnóstico..."
    
    cat > /app/diagnose_mitosis.sh << 'EOF'
#!/bin/bash
###############################################################################
# MITOSIS - SCRIPT DE DIAGNÓSTICO
###############################################################################

echo "🔍 DIAGNÓSTICO DE MITOSIS"
echo "============================================================="

echo "📊 Estado de servicios:"
sudo supervisorctl status mitosis:* || echo "❌ Supervisor no configurado correctamente"

echo ""
echo "🌐 Conectividad:"
echo -n "Backend Health: "
if curl -s -f http://localhost:8001/health >/dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FALLO"
fi

echo -n "OLLAMA: "
if curl -s -f "https://bef4a4bb93d1.ngrok-free.app/api/tags" >/dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FALLO"
fi

echo -n "Frontend: "
if curl -s -f http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FALLO"
fi

echo ""
echo "💽 Espacio en disco:"
df -h / | tail -1

echo ""
echo "🔧 Procesos activos:"
ps aux | grep -E "(python|node|mongod)" | grep -v grep

echo ""
echo "📝 Últimos logs de backend:"
tail -n 10 /var/log/supervisor/backend.err.log 2>/dev/null || echo "No hay logs disponibles"

echo ""
echo "============================================================="
EOF

    chmod +x /app/diagnose_mitosis.sh
    log_success "Script de diagnóstico creado: /app/diagnose_mitosis.sh"
}

# Función principal de instalación
main() {
    log_info "Iniciando instalación automática de Mitosis..."
    
    # Detener servicios existentes
    sudo supervisorctl stop all 2>/dev/null || true
    
    # Pasos de instalación
    install_dependencies
    detect_server_type
    verify_file_structure
    install_tools
    create_robust_supervisor_config
    create_startup_script
    create_diagnostic_script
    
    # Recargar supervisor
    sudo supervisorctl reread
    sudo supervisorctl update
    
    log_success "============================================================="
    log_success "🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE"
    log_success "============================================================="
    log_info "Comandos disponibles:"
    log_info "  • Iniciar:     /app/start_mitosis.sh"
    log_info "  • Diagnóstico: /app/diagnose_mitosis.sh"
    log_info "  • Logs:        tail -f /var/log/supervisor/backend.*.log"
    log_success "============================================================="
    
    echo ""
    read -p "¿Deseas iniciar Mitosis ahora? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Iniciando Mitosis..."
        /app/start_mitosis.sh
    else
        log_info "Para iniciar Mitosis ejecuta: /app/start_mitosis.sh"
    fi
}

# Ejecutar instalación
main "$@"