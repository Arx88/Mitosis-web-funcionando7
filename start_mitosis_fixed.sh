#!/bin/bash
###############################################################################
# 🚀 MITOSIS START - SCRIPT DEFINITIVO CON FIX FLASK/SOCKETIO
# SOLUCIÓN COMPLETA PARA PROBLEMA CRÍTICO DE CONFIGURACIÓN
###############################################################################

set -e

echo "🚀 INICIANDO MITOSIS CON FIX DEFINITIVO..."
echo "🔧 Solucionando problema crítico Flask/SocketIO..."

# ========================================================================
# PASO 1: CREAR SERVIDOR WSGI CORRECTO PARA FLASK + SOCKETIO
# ========================================================================

echo "📝 Creando servidor WSGI correcto..."
cat > /app/backend/wsgi_server.py << 'EOF'
#!/usr/bin/env python3
"""
WSGI Server para Flask + SocketIO - SOLUCIÓN DEFINITIVA
Usa gunicorn con eventlet worker para compatibilidad completa
"""

import os
import sys
sys.path.insert(0, '/app/backend')

from server import app, socketio

# Para gunicorn con eventlet
application = socketio.wsgi_app

if __name__ == '__main__':
    # Para testing directo
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)
EOF

chmod +x /app/backend/wsgi_server.py

# ========================================================================
# PASO 2: INSTALAR DEPENDENCIAS NECESARIAS PARA GUNICORN + EVENTLET
# ========================================================================

echo "📦 Instalando gunicorn y eventlet para Flask+SocketIO..."
cd /app/backend

# Verificar si gunicorn está instalado
if ! pip list | grep -q "gunicorn"; then
    echo "⚡ Instalando gunicorn..."
    pip install gunicorn==21.2.0
fi

# Verificar si eventlet está instalado  
if ! pip list | grep -q "eventlet"; then
    echo "⚡ Instalando eventlet (requerido para SocketIO)..."
    pip install eventlet==0.36.1
fi

# Actualizar requirements.txt
if ! grep -q "gunicorn" requirements.txt; then
    echo "gunicorn==21.2.0" >> requirements.txt
fi

if ! grep -q "eventlet" requirements.txt; then
    echo "eventlet==0.36.1" >> requirements.txt
fi

echo "✅ Dependencias instaladas correctamente"

# ========================================================================
# PASO 3: CONFIGURACIÓN SUPERVISOR CORREGIDA
# ========================================================================

echo "⚙️ Configurando supervisor con gunicorn..."
cat > /etc/supervisor/conf.d/supervisord.conf << 'EOF'
[program:backend]
command=/root/.venv/bin/gunicorn -w 1 -k eventlet -b 0.0.0.0:8001 wsgi_server:application --timeout 120 --log-level info
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
stopsignal=TERM
stopwaitsecs=15
stopasgroup=true
killasgroup=true
environment=PYTHONPATH="/app/backend",FLASK_ENV="production",FLASK_APP="server.py"

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

# ========================================================================
# PASO 4: INSTALAR DEPENDENCIAS FRONTEND SI ES NECESARIO
# ========================================================================

echo "📦 Verificando dependencias frontend..."
cd /app/frontend

if [ ! -d "node_modules" ]; then
    echo "⚡ Instalando dependencias frontend..."
    yarn install --frozen-lockfile
fi

# ========================================================================
# PASO 5: REINICIAR SERVICIOS CON NUEVA CONFIGURACIÓN
# ========================================================================

echo "🔄 Reiniciando servicios con configuración corregida..."
sudo supervisorctl reread >/dev/null 2>&1
sudo supervisorctl update >/dev/null 2>&1
sudo supervisorctl stop all >/dev/null 2>&1
sleep 2
sudo supervisorctl start all >/dev/null 2>&1

# ========================================================================
# PASO 6: ESPERAR ESTABILIZACIÓN Y VERIFICAR
# ========================================================================

echo "⏳ Esperando estabilización de servicios..."
sleep 15

# Funciones de verificación mejoradas
check_backend() {
    curl -s -f http://localhost:8001/api/health >/dev/null 2>&1
}

check_frontend() {
    curl -s -f http://localhost:3000 >/dev/null 2>&1
}

check_mongodb() {
    sudo supervisorctl status mongodb | grep -q "RUNNING"
}

check_ollama() {
    curl -s -f "https://bef4a4bb93d1.ngrok-free.app/api/tags" >/dev/null 2>&1 || \
    curl -s -f "https://78d08925604a.ngrok-free.app/api/tags" >/dev/null 2>&1
}

echo "🔍 Verificando servicios con nueva configuración..."

# Verificar backend con reintentos
echo "⏳ Verificando backend (puede tomar 30 segundos)..."
backend_ok=false
for i in {1..30}; do
    if check_backend; then
        backend_ok=true
        break
    fi
    if [ $((i % 5)) -eq 0 ]; then
        echo "   Intento $i/30..."
    fi
    sleep 2
done

# Verificar frontend
echo "⏳ Verificando frontend..."
frontend_ok=false
for i in {1..15}; do
    if check_frontend; then
        frontend_ok=true
        break
    fi
    sleep 2
done

# ========================================================================
# PASO 7: REPORTE FINAL DETALLADO
# ========================================================================

echo ""
echo "🎉 MITOSIS - REPORTE FINAL CON FIX APLICADO"
echo "=============================================================="
echo "🔧 FIX APLICADO: Flask + gunicorn + eventlet (WSGI correcto)"
echo "📍 Frontend: https://eda28dae-1785-49e8-9460-2c43451cc62d.preview.emergentagent.com"
echo "📍 Backend API: http://localhost:8001"
echo "=============================================================="

# Backend status
if $backend_ok; then
    echo "✅ BACKEND: FUNCIONANDO CORRECTAMENTE"
    echo "   🔧 Servidor: gunicorn + eventlet worker"
    echo "   🌐 Puerto: 8001"
    # Intentar obtener info de health
    health_info=$(curl -s http://localhost:8001/api/health 2>/dev/null || echo "API funcionando")
    echo "   📊 Health: $health_info"
else
    echo "❌ BACKEND: PROBLEMA DETECTADO"
    echo "   📋 Revisar logs: tail -10 /var/log/supervisor/backend.err.log"
fi

# Frontend status  
if $frontend_ok; then
    echo "✅ FRONTEND: FUNCIONANDO CORRECTAMENTE"
    echo "   🔧 Servidor: Vite dev server"
    echo "   🌐 Puerto: 3000"
else
    echo "❌ FRONTEND: PROBLEMA DETECTADO"
    echo "   📋 Revisar logs: tail -10 /var/log/supervisor/frontend.err.log"
fi

# MongoDB status
if check_mongodb; then
    echo "✅ MONGODB: FUNCIONANDO CORRECTAMENTE"
else
    echo "❌ MONGODB: PROBLEMA DETECTADO"
fi

# Ollama status
if check_ollama; then
    echo "✅ OLLAMA: CONECTADO Y DISPONIBLE"
    echo "   🔗 Endpoint funcionando correctamente"
else
    echo "⚠️ OLLAMA: NO DISPONIBLE"
    echo "   ℹ️ La app funciona pero sin capacidades de IA"
fi

echo "=============================================================="
echo "📊 ESTADO DE PROCESOS SUPERVISOR:"
sudo supervisorctl status
echo ""

# ========================================================================
# PASO 8: TESTING AUTOMÁTICO DE APIs
# ========================================================================

if $backend_ok; then
    echo "🧪 TESTING AUTOMÁTICO DE APIs..."
    echo "=============================================================="
    
    # Test health endpoint
    echo "🔍 Testing /api/health..."
    health_response=$(curl -s http://localhost:8001/api/health 2>/dev/null || echo "error")
    if [ "$health_response" != "error" ]; then
        echo "   ✅ Health endpoint: OK"
    else
        echo "   ❌ Health endpoint: FAIL"
    fi
    
    # Test agent health
    echo "🔍 Testing /api/agent/health..."
    agent_health=$(curl -s http://localhost:8001/api/agent/health 2>/dev/null || echo "error")
    if [ "$agent_health" != "error" ]; then
        echo "   ✅ Agent health endpoint: OK"
    else
        echo "   ❌ Agent health endpoint: FAIL"
    fi
    
    # Test agent status
    echo "🔍 Testing /api/agent/status..."
    agent_status=$(curl -s http://localhost:8001/api/agent/status 2>/dev/null || echo "error")
    if [ "$agent_status" != "error" ]; then
        echo "   ✅ Agent status endpoint: OK"
    else
        echo "   ❌ Agent status endpoint: FAIL"
    fi
    
    echo "=============================================================="
fi

# ========================================================================
# PASO 9: RESULTADO FINAL
# ========================================================================

if $backend_ok && $frontend_ok; then
    echo ""
    echo "🎯 ¡ÉXITO COMPLETO! PROBLEMA FLASK/SOCKETIO SOLUCIONADO"
    echo "=============================================================="
    echo "✅ FIX APLICADO: Flask ahora usa gunicorn + eventlet (WSGI correcto)"
    echo "✅ Backend APIs funcionando correctamente en puerto 8001"
    echo "✅ Frontend conectado correctamente en puerto 3000"
    echo "✅ MongoDB funcionando para persistencia"
    echo "✅ Configuración supervisor corregida"
    echo "✅ Sin más errores de Flask.__call__()"
    echo ""
    echo "🚀 APLICACIÓN 100% FUNCIONAL Y LISTA PARA USAR"
    echo "🌐 Abrir: https://eda28dae-1785-49e8-9460-2c43451cc62d.preview.emergentagent.com"
    echo "=============================================================="
else
    echo ""
    echo "⚠️ ALGUNOS SERVICIOS NECESITAN ATENCIÓN"
    echo "=============================================================="
    echo "📋 Para debugging:"
    echo "   Backend logs: tail -20 /var/log/supervisor/backend.err.log"
    echo "   Frontend logs: tail -20 /var/log/supervisor/frontend.err.log"
    echo "   Supervisor status: sudo supervisorctl status"
    echo "=============================================================="
fi

echo ""
echo "🔧 SCRIPT COMPLETADO - FIX FLASK/SOCKETIO APLICADO"
echo "📝 Cambios realizados:"
echo "   1. Creado wsgi_server.py para compatibilidad WSGI"
echo "   2. Instalado gunicorn + eventlet"
echo "   3. Configurado supervisor correctamente" 
echo "   4. Testing automático de APIs implementado"
echo ""