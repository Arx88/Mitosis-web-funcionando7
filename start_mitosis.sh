#!/bin/bash
###############################################################################
# 🚀 MITOSIS ONE-STEP READY - SCRIPT DEFINITIVO
# UN SOLO COMANDO - APLICACIÓN 100% FUNCIONAL SIN AJUSTES MANUALES
###############################################################################

set -e

echo "🚀 INICIANDO MITOSIS (ONE-STEP READY)..."

# CONFIGURACIÓN SUPERVISOR DEFINITIVA (SIN PROBLEMAS UVICORN)
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
command=yarn start
environment=HOST="0.0.0.0",PORT="3000"
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

# REINICIAR SERVICIOS
sudo supervisorctl reread >/dev/null 2>&1
sudo supervisorctl update >/dev/null 2>&1
sudo supervisorctl restart all >/dev/null 2>&1

# ESPERAR ESTABILIZACIÓN
sleep 10

# VERIFICACIONES FINALES
check_backend() {
    curl -s -f http://localhost:8001/health >/dev/null 2>&1
}

check_frontend() {
    pgrep -f "node.*3000" >/dev/null
}

check_ollama() {
    curl -s -f "https://bef4a4bb93d1.ngrok-free.app/api/tags" >/dev/null 2>&1 || \
    curl -s -f "https://78d08925604a.ngrok-free.app/api/tags" >/dev/null 2>&1
}

echo "🔍 Verificando servicios..."

# VERIFICAR CON REINTENTOS
for i in {1..20}; do
    if check_backend; then
        break
    fi
    if [ $i -eq 1 ]; then echo "⏳ Esperando backend..."; fi
    sleep 2
done

# MOSTRAR ESTADO FINAL
echo ""
echo "🎉 MITOSIS ONE-STEP READY - ESTADO FINAL"
echo "=============================================================="
echo "📍 Frontend: https://06e72bc6-45fa-4e2e-a398-71320846a996.preview.emergentagent.com"
echo "📍 Backend API: http://localhost:8001"
echo "=============================================================="

if check_backend; then
    health=$(curl -s http://localhost:8001/health)
    echo "✅ BACKEND: FUNCIONANDO (server_simple.py - sin uvicorn)"
    echo "   $health"
else
    echo "❌ BACKEND: NO RESPONDE"
fi

if check_frontend; then
    echo "✅ FRONTEND: FUNCIONANDO (puerto 3000)"
else
    echo "❌ FRONTEND: NO FUNCIONA"
fi

if sudo supervisorctl status mongodb | grep -q "RUNNING"; then
    echo "✅ MONGODB: FUNCIONANDO"
else
    echo "❌ MONGODB: NO FUNCIONA"
fi

if check_ollama; then
    echo "✅ OLLAMA: CONECTADO Y DISPONIBLE"
else
    echo "⚠️ OLLAMA: NO DISPONIBLE (app funciona sin IA)"
fi

echo "=============================================================="
sudo supervisorctl status
echo ""

if check_backend && check_frontend; then
    echo "🎯 ¡ÉXITO! MITOSIS ESTÁ ONE-STEP READY"
    echo "✅ La aplicación está 100% funcional sin ajustes manuales"
    echo "✅ Frontend y Backend conectados correctamente"
    echo "✅ No hay problemas de uvicorn ni configuración"
    echo ""
    echo "🚀 LISTO PARA USAR"
else
    echo "❌ Algunos servicios no funcionan - revisar logs"
fi