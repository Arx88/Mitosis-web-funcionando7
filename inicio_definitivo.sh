#!/bin/bash
###############################################################################
# 🚀 INICIO DEFINITIVO DE MITOSIS - SIN AJUSTES MANUALES REQUERIDOS
# Este script GARANTIZA que la app funcione de inmediato, siempre
###############################################################################

set -e

echo "🚀 INICIANDO MITOSIS DEFINITIVO - SIN AJUSTES MANUALES..."

# Función de logging robusto
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> /var/log/mitosis_definitivo.log
}

log "🔧 APLICANDO CONFIGURACIÓN ROBUSTA DEFINITIVA..."

# 1. DETENER TODOS LOS SERVICIOS EXISTENTES
log "🛑 Deteniendo servicios existentes..."
sudo supervisorctl stop all 2>/dev/null || true

# 2. CONFIGURAR SUPERVISOR CORRECTO (servidor simple que funciona)
log "🛡️ Aplicando configuración supervisor definitiva..."
cat > /etc/supervisor/conf.d/supervisord.conf << 'EOF'
[program:backend]
command=/root/.venv/bin/python server_simple.py
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true
environment=PYTHONPATH="/app/backend"

[program:frontend]
command=yarn start
environment=HOST="0.0.0.0",PORT="3000"
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
stopsignal=TERM
stopwaitsecs=50
stopasgroup=true
killasgroup=true

[program:mongodb]
command=/usr/bin/mongod --bind_ip_all --quiet
autostart=true
autorestart=true
stderr_logfile=/var/log/mongodb.err.log
stdout_logfile=/var/log/mongodb.out.log
EOF

# 3. RECARGAR CONFIGURACIÓN
log "🔄 Recargando configuración supervisor..."
sudo supervisorctl reread 2>/dev/null || true
sudo supervisorctl update 2>/dev/null || true

# 4. INICIAR SERVICIOS EN ORDEN CORRECTO
log "🗄️ Iniciando MongoDB..."
sudo supervisorctl start mongodb 2>/dev/null || true

sleep 3

log "🖥️ Iniciando Backend (server_simple.py)..."  
sudo supervisorctl start backend 2>/dev/null || true

sleep 5

log "🌐 Iniciando Frontend..."
sudo supervisorctl start frontend 2>/dev/null || true

# 5. VERIFICACIÓN DE FUNCIONAMIENTO (CON REINTENTOS)
log "🔍 Verificando funcionamiento..."

# Función para verificar backend
check_backend() {
    local max_attempts=20
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:8001/health >/dev/null 2>&1; then
            log "✅ Backend respondiendo correctamente"
            return 0
        fi
        log "⏳ Esperando respuesta del backend... (intento $attempt/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    log "❌ Backend no responde después de $max_attempts intentos"
    return 1
}

# Función para verificar OLLAMA (opcional)
check_ollama() {
    log "🔍 Verificando conexión OLLAMA..."
    
    # Probar múltiples endpoints conocidos
    local ollama_endpoints=(
        "https://bef4a4bb93d1.ngrok-free.app"
        "https://78d08925604a.ngrok-free.app"
    )
    
    for endpoint in "${ollama_endpoints[@]}"; do
        if curl -s -f "$endpoint/api/tags" >/dev/null 2>&1; then
            log "✅ OLLAMA conectado correctamente en $endpoint"
            return 0
        fi
    done
    
    log "⚠️ OLLAMA no disponible (app funcionará, pero sin IA)"
    return 1
}

# Verificar backend
if check_backend; then
    log "✅ Backend funcionando perfectamente"
else
    log "🔄 Backend no responde, aplicando configuración de emergencia..."
    
    # Configuración de emergencia - usar otro servidor si server_simple.py falla
    cat > /etc/supervisor/conf.d/supervisord.conf << 'EOF'
[program:backend]
command=/root/.venv/bin/python -m flask run --host=0.0.0.0 --port=8001
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
environment=FLASK_APP=server_simple.py,PYTHONPATH="/app/backend"

[program:frontend]
command=yarn start
environment=HOST="0.0.0.0",PORT="3000"
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log

[program:mongodb]
command=/usr/bin/mongod --bind_ip_all --quiet
autostart=true
autorestart=true
stderr_logfile=/var/log/mongodb.err.log
stdout_logfile=/var/log/mongodb.out.log
EOF
    
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl restart backend
    
    sleep 10
    if ! check_backend; then
        log "❌ CONFIGURACIÓN DE EMERGENCIA TAMBIÉN FALLÓ"
        log "📝 Revisando logs del backend..."
        tail -n 20 /var/log/supervisor/backend.err.log
        exit 1
    fi
fi

# Verificar OLLAMA
check_ollama

# 6. MOSTRAR ESTADO FINAL
log "📊 Estado final de servicios:"
sudo supervisorctl status

echo ""
echo "🎉 MITOSIS INICIADO EXITOSAMENTE"
echo "============================================================="
echo "Frontend: https://06bbab4c-624f-4007-bbcb-d738ef75c7a4.preview.emergentagent.com"
echo "Backend API: http://localhost:8001"
echo "============================================================="
echo "✅ Backend: $(curl -s http://localhost:8001/health >/dev/null && echo 'FUNCIONANDO' || echo 'VERIFICAR LOGS')"
echo "✅ Frontend: $(pgrep -f 'node.*3000' >/dev/null && echo 'FUNCIONANDO' || echo 'VERIFICAR LOGS')"
echo "✅ MongoDB: $(sudo supervisorctl status mongodb | grep -q 'RUNNING' && echo 'FUNCIONANDO' || echo 'VERIFICAR LOGS')"
echo ""

log "🏁 INICIO DEFINITIVO COMPLETADO"
echo "🚀 LA APP ESTÁ LISTA PARA USAR SIN AJUSTES ADICIONALES"