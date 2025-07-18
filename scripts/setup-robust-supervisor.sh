#!/bin/bash

# =============================================================================
# CONFIGURACIÓN ROBUSTA DE SUPERVISOR - INMUNE A CAMBIOS
# =============================================================================

echo "🛡️  CONFIGURANDO SUPERVISOR ROBUSTO..."

# Crear configuración robusta
cat > /etc/supervisor/conf.d/supervisord.conf << 'EOF'
[program:backend]
command=/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --no-use-colors --log-level info
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
command=bash -c '/app/scripts/auto-build.sh && serve -s /app/frontend/dist -l 3000 --no-clipboard'
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true

[program:mongodb]
command=/usr/bin/mongod --bind_ip_all --quiet
autostart=true
autorestart=true
stderr_logfile=/var/log/mongodb.err.log
stdout_logfile=/var/log/mongodb.out.log

[program:stability-monitor]
command=/app/scripts/stability-monitor.sh
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/stability-monitor.err.log
stdout_logfile=/var/log/supervisor/stability-monitor.out.log
EOF

echo "✅ CONFIGURACIÓN ROBUSTA CREADA"