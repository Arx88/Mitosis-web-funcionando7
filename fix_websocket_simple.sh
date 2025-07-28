#!/bin/bash

echo "🔧 SOLUCION SIMPLE: BACKEND SIRVE FRONTEND + WEBSOCKET"
echo "===================================================="

# Detener servicios temporalmente
echo "🔄 Deteniendo servicios..."
sudo supervisorctl stop all

# Limpiar configuraciones anteriores
echo "🧹 Limpiando configuraciones anteriores..."
sudo rm -f /etc/supervisor/conf.d/websocket_proxy.conf
sudo rm -f /app/websocket_proxy.py

# Modificar el backend para que sirva el frontend
echo "🔧 Modificando backend para servir archivos estáticos..."

# Crear backup del server.py
cp /app/backend/server.py /app/backend/server.py.backup

# Agregar configuración para servir archivos estáticos
cat >> /app/backend/server.py << 'EOF'

# Servir archivos estáticos del frontend
from flask import send_from_directory, send_file
import os

# Configurar directorio de archivos estáticos
STATIC_FOLDER = '/app/frontend/dist'

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Servir archivos estáticos del frontend"""
    if path != "" and os.path.exists(os.path.join(STATIC_FOLDER, path)):
        return send_from_directory(STATIC_FOLDER, path)
    else:
        return send_file(os.path.join(STATIC_FOLDER, 'index.html'))

# Ruta para servir archivos específicos
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Servir archivos de assets"""
    return send_from_directory(os.path.join(STATIC_FOLDER, 'assets'), filename)

# Ruta para servir archivos de tareas
@app.route('/files/<task_id>')
def serve_task_files(task_id):
    """Servir archivos de tareas"""
    return redirect(f'/api/agent/get-task-files/{task_id}')

EOF

# Modificar configuración del supervisor para remover frontend
echo "🔧 Modificando configuración del supervisor..."

# Crear nueva configuración sin frontend separado
sudo tee /etc/supervisor/conf.d/supervisord.conf > /dev/null <<EOF
[program:backend]
command=/root/.venv/bin/gunicorn -w 1 -k eventlet -b 0.0.0.0:8001 production_wsgi:application --timeout 120 --log-level info --access-logfile /var/log/supervisor/backend-access.log
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
stopsignal=TERM
stopwaitsecs=15
stopasgroup=true
killasgroup=true
environment=PYTHONPATH="/app/backend",FLASK_ENV="production",FLASK_DEBUG="False"

[program:mongodb]
command=/usr/bin/mongod --bind_ip_all --quiet --logpath /var/log/mongodb.log
autostart=true
autorestart=true
stderr_logfile=/var/log/mongodb.err.log
stdout_logfile=/var/log/mongodb.out.log
EOF

# Recargar configuración
sudo supervisorctl reread
sudo supervisorctl update

# Reiniciar servicios
echo "🔄 Reiniciando servicios..."
sudo supervisorctl restart all

# Esperar a que inicien
echo "⏳ Esperando que los servicios inicien..."
sleep 10

# Verificar servicios
echo "🔍 Verificando servicios..."
sudo supervisorctl status

# Testear conexión WebSocket
echo "🔍 Testeando WebSocket..."
curl -s "http://localhost:8001/socket.io/?EIO=4&transport=polling" | head -1

# Testear acceso al frontend
echo "🔍 Testeando acceso al frontend..."
curl -s "http://localhost:8001/" | head -1

echo "✅ SOLUCION IMPLEMENTADA"
echo "🎯 Toda la aplicación ahora corre en el puerto 8001"
echo "🌐 Frontend: http://localhost:8001"
echo "🔌 WebSocket: http://localhost:8001/socket.io/"
echo "🔧 API: http://localhost:8001/api/"