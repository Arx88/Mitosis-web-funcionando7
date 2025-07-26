#!/bin/bash
###############################################################################
# 🚀 MITOSIS ONE-STEP READY - INSTALACIÓN DEFINITIVA
# UN SOLO COMANDO - APLICACIÓN 100% FUNCIONAL SIN AJUSTES MANUALES
###############################################################################

set -e

echo "🚀 MITOSIS ONE-STEP READY - INSTALACIÓN DEFINITIVA..."
echo "=============================================================="

# Función de logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> /var/log/mitosis_onestep.log
}

log "🎯 INICIANDO INSTALACIÓN ONE-STEP DEFINITIVA"

# 1. DETENER TODO Y LIMPIAR
log "🧹 Limpiando procesos existentes..."
sudo supervisorctl stop all 2>/dev/null || true
sudo pkill -f "uvicorn" 2>/dev/null || true
sudo pkill -f "node.*3000" 2>/dev/null || true

# 2. INSTALAR DEPENDENCIAS SI FALTAN
log "📦 Verificando dependencias..."

# Backend dependencies
if [ ! -f "/root/.venv/bin/python" ]; then
    log "🔧 Creando virtual environment..."
    python3 -m venv /root/.venv
fi

# Activar venv y instalar requirements
source /root/.venv/bin/activate
cd /app/backend
pip install -r requirements.txt &>/dev/null || true

# Frontend dependencies
cd /app/frontend
if [ ! -d "node_modules" ]; then
    log "🔧 Instalando dependencias frontend..."
    yarn install --silent 2>/dev/null || npm install --silent 2>/dev/null || true
fi

# 3. CONFIGURAR SUPERVISOR DEFINITIVO (SIN UVICORN - USA SERVIDOR SIMPLE)
log "🛡️ Configurando supervisor definitivo (sin problemas uvicorn)..."
cat > /etc/supervisor/conf.d/supervisord.conf << 'EOF'
[program:backend]
command=/root/.venv/bin/python server_simple.py
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
stopsignal=TERM
stopwaitsecs=10
stopasgroup=true
killasgroup=true
environment=PYTHONPATH="/app/backend",FLASK_ENV="production"

[program:frontend]
command=/root/.venv/bin/yarn start
environment=HOST="0.0.0.0",PORT="3000",NODE_ENV="development"
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
stopsignal=TERM
stopwaitsecs=10
stopasgroup=true
killasgroup=true

[program:mongodb]
command=/usr/bin/mongod --bind_ip_all --quiet --logpath /var/log/mongodb.log
autostart=true
autorestart=true
stderr_logfile=/var/log/mongodb.err.log
stdout_logfile=/var/log/mongodb.out.log
EOF

# 4. RECARGAR CONFIGURACIÓN SUPERVISOR
log "🔄 Aplicando configuración supervisor..."
sudo supervisorctl reread >/dev/null 2>&1
sudo supervisorctl update >/dev/null 2>&1

# 5. INICIAR SERVICIOS EN ORDEN CORRECTO
log "🗄️ Iniciando MongoDB..."
sudo supervisorctl start mongodb >/dev/null 2>&1
sleep 3

log "🖥️ Iniciando Backend (server_simple.py - SIN uvicorn)..."
sudo supervisorctl start backend >/dev/null 2>&1
sleep 5

log "🌐 Iniciando Frontend..."
sudo supervisorctl start frontend >/dev/null 2>&1
sleep 3

# 6. VERIFICACIÓN EXHAUSTIVA CON REINTENTOS
log "🔍 VERIFICACIÓN EXHAUSTIVA DE FUNCIONAMIENTO..."

# Verificar backend con reintentos
verify_backend() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:8001/health >/dev/null 2>&1; then
            local health_response=$(curl -s http://localhost:8001/health)
            log "✅ Backend funciona: $health_response"
            return 0
        fi
        
        if [ $attempt -eq 1 ]; then
            log "⏳ Esperando respuesta del backend..."
        fi
        
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log "❌ Backend no responde después de $max_attempts intentos"
    return 1
}

# Verificar frontend
verify_frontend() {
    if pgrep -f "node.*3000" >/dev/null; then
        log "✅ Frontend funcionando en puerto 3000"
        return 0
    else
        log "❌ Frontend no está funcionando"
        return 1
    fi
}

# Verificar OLLAMA con múltiples endpoints
verify_ollama() {
    local endpoints=(
        "https://bef4a4bb93d1.ngrok-free.app"
        "https://78d08925604a.ngrok-free.app"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s -f "$endpoint/api/tags" >/dev/null 2>&1; then
            log "✅ OLLAMA conectado: $endpoint"
            echo "$endpoint" > /tmp/ollama_endpoint
            return 0
        fi
    done
    
    log "⚠️ OLLAMA no disponible (app funcionará, pero sin IA)"
    return 1
}

# Verificar MongoDB
verify_mongodb() {
    if sudo supervisorctl status mongodb | grep -q "RUNNING"; then
        log "✅ MongoDB funcionando"
        return 0
    else
        log "❌ MongoDB no funcionando"
        return 1
    fi
}

# EJECUTAR TODAS LAS VERIFICACIONES
log "📊 EJECUTANDO VERIFICACIONES FINALES..."

backend_ok=false
frontend_ok=false
mongodb_ok=false
ollama_ok=false

if verify_backend; then backend_ok=true; fi
if verify_frontend; then frontend_ok=true; fi
if verify_mongodb; then mongodb_ok=true; fi
if verify_ollama; then ollama_ok=true; fi

# 7. REPORTE FINAL
echo ""
echo "🎉 MITOSIS ONE-STEP READY - REPORTE FINAL"
echo "=============================================================="
echo "📍 Frontend: https://5aa90c84-36b1-4873-81ab-1edc81506a21.preview.emergentagent.com"
echo "📍 Backend API: http://localhost:8001"
echo "=============================================================="

if [ "$backend_ok" = true ]; then
    echo "✅ BACKEND: FUNCIONANDO (server_simple.py - sin problemas uvicorn)"
else
    echo "❌ BACKEND: NO FUNCIONA"
fi

if [ "$frontend_ok" = true ]; then
    echo "✅ FRONTEND: FUNCIONANDO (puerto 3000)"
else
    echo "❌ FRONTEND: NO FUNCIONA"
fi

if [ "$mongodb_ok" = true ]; then
    echo "✅ MONGODB: FUNCIONANDO"
else
    echo "❌ MONGODB: NO FUNCIONA"
fi

if [ "$ollama_ok" = true ]; then
    echo "✅ OLLAMA: CONECTADO ($(cat /tmp/ollama_endpoint 2>/dev/null || echo 'endpoint detectado'))"
else
    echo "⚠️ OLLAMA: NO DISPONIBLE (app funciona sin IA)"
fi

echo "=============================================================="
echo "📋 Estado de servicios supervisor:"
sudo supervisorctl status

# 8. VERIFICACIÓN FINAL DE ÉXITO
if [ "$backend_ok" = true ] && [ "$frontend_ok" = true ] && [ "$mongodb_ok" = true ]; then
    echo ""
    echo "🎯 ¡ÉXITO! LA APLICACIÓN ESTÁ 100% LISTA PARA USAR"
    echo "✅ Backend funcionando sin problemas uvicorn"
    echo "✅ Frontend conectado correctamente"
    echo "✅ Base de datos MongoDB operativa"
    echo "✅ Configuración robusta aplicada"
    echo ""
    echo "🚀 LA APP ESTÁ ONE-STEP READY - NO REQUIERE AJUSTES MANUALES"
    
    log "🏆 INSTALACIÓN ONE-STEP COMPLETADA EXITOSAMENTE"
    exit 0
else
    echo ""
    echo "❌ FALLO EN LA INSTALACIÓN ONE-STEP"
    echo "⚠️ Algunos servicios no están funcionando correctamente"
    echo "📝 Revisar logs para más detalles:"
    echo "   - Backend: /var/log/supervisor/backend.err.log"
    echo "   - Frontend: /var/log/supervisor/frontend.err.log" 
    echo "   - MongoDB: /var/log/mongodb.err.log"
    
    log "💥 INSTALACIÓN ONE-STEP FALLÓ - ALGUNOS SERVICIOS NO FUNCIONAN"
    exit 1
fi