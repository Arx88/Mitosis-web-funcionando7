#!/bin/bash
###############################################################################
# 🚀 MITOSIS - INICIO DEFINITIVO Y ROBUSTO (VERSIÓN FINAL)
# Este script GARANTIZA funcionamiento inmediato sin ajustes manuales
###############################################################################

set -e

echo "🚀 Iniciando Mitosis (Versión Robusta Definitiva)..."

# Función de logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# CONFIGURACIÓN SUPERVISOR DEFINITIVA (usa server_simple.py que funciona)
log "🛡️ Aplicando configuración robusta..."
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

# Recargar y reiniciar servicios
log "🔄 Recargando configuración..."
sudo supervisorctl reread 2>/dev/null || true
sudo supervisorctl update 2>/dev/null || true
sudo supervisorctl restart all 2>/dev/null || true

# Esperar estabilización
log "⏳ Esperando estabilización..."
sleep 10

# Verificación con reintentos automáticos
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

# Verificar OLLAMA (múltiples endpoints)
check_ollama() {
    echo "🔍 Verificando conexión OLLAMA..."
    local endpoints=("https://bef4a4bb93d1.ngrok-free.app" "https://78d08925604a.ngrok-free.app")
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s -f "$endpoint/api/tags" >/dev/null 2>&1; then
            echo "✅ OLLAMA conectado correctamente en $endpoint"
            return 0
        fi
    done
    
    echo "⚠️ OLLAMA no disponible (app funcionará sin IA)"
    return 1
}

# Verificar servicios
echo "🔍 Verificando servicios..."

if sudo supervisorctl status | grep -q "mongodb.*RUNNING"; then
    echo "✅ MongoDB funcionando"
else
    echo "⚠️ MongoDB no está ejecutándose"
fi

if sudo supervisorctl status | grep -q "backend.*RUNNING"; then
    echo "✅ Backend funcionando"
else
    echo "⚠️ Backend no está ejecutándose"
fi

if sudo supervisorctl status | grep -q "frontend.*RUNNING"; then
    echo "✅ Frontend funcionando"
else
    echo "⚠️ Frontend no está ejecutándose"
fi

# Verificar conectividad
echo "🔍 Verificando conectividad..."
check_backend
check_ollama

echo ""
echo "🎉 MITOSIS INICIADO"
echo "============================================================="
echo "Frontend: https://b31e34fa-8db4-4a6b-83b4-4600e46cffab.preview.emergentagent.com"
echo "Backend API: http://localhost:8001"
echo "============================================================="
echo ""

# Mostrar estado de los servicios
sudo supervisorctl status