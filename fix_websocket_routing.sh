#!/bin/bash

echo "🔧 ARREGLANDO ROUTING DE WEBSOCKET EN MITOSIS"
echo "============================================="

# Verificar servicios
echo "🔍 Verificando servicios actuales..."
sudo supervisorctl status

# Verificar puertos
echo "🔍 Verificando puertos ocupados..."
netstat -tlnp | grep -E ":8001|:3000"

# Verificar conexión WebSocket directa al backend
echo "🔍 Testear WebSocket directo al backend..."
curl -s "http://localhost:8001/socket.io/?EIO=4&transport=polling" | head -1

# Verificar conexión WebSocket externa
echo "🔍 Testear WebSocket externo..."
curl -s "https://31ac0422-78aa-4076-a1b1-c3e7b8886947.preview.emergentagent.com/socket.io/?EIO=4&transport=polling" | head -1

# Crear archivo de configuración para el routing correcto
echo "🔧 Creando configuración de routing WebSocket..."

# Buscar si hay configuración de nginx o similar
if [ -f "/etc/nginx/nginx.conf" ]; then
    echo "📝 Configuración nginx encontrada"
    # Backup
    sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
    
    # Agregar configuración WebSocket
    sudo tee /etc/nginx/conf.d/websocket.conf > /dev/null <<EOF
upstream backend {
    server 127.0.0.1:8001;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name _;
    
    # WebSocket routing
    location /socket.io/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # API routing
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Frontend routing
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Reiniciar nginx
    sudo nginx -t && sudo systemctl restart nginx
    echo "✅ Nginx configurado para WebSocket routing"
else
    echo "⚠️  No se encontró nginx, implementando solución alternativa..."
    
    # Crear un proxy simple usando Python
    cat > /app/websocket_proxy.py << 'EOF'
#!/usr/bin/env python3
"""
WebSocket Proxy para routing correcto
"""
import asyncio
import websockets
import requests
from flask import Flask, request, Response
import threading

app = Flask(__name__)

@app.route('/socket.io/<path:path>', methods=['GET', 'POST'])
def proxy_websocket(path):
    """Proxy WebSocket requests to backend"""
    url = f"http://localhost:8001/socket.io/{path}"
    
    # Forward query parameters
    if request.query_string:
        url += "?" + request.query_string.decode()
    
    # Forward headers
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'connection']}
    
    # Forward request to backend
    if request.method == 'GET':
        response = requests.get(url, headers=headers)
    else:
        response = requests.post(url, headers=headers, data=request.data)
    
    # Return response with proper headers
    return Response(
        response.content,
        status=response.status_code,
        headers=dict(response.headers)
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=False)
EOF
    
    chmod +x /app/websocket_proxy.py
    
    # Agregar al supervisor
    sudo tee /etc/supervisor/conf.d/websocket_proxy.conf > /dev/null <<EOF
[program:websocket_proxy]
command=/root/.venv/bin/python /app/websocket_proxy.py
directory=/app
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/websocket_proxy.err.log
stdout_logfile=/var/log/supervisor/websocket_proxy.out.log
stopsignal=TERM
stopwaitsecs=10
stopasgroup=true
killasgroup=true
environment=PYTHONPATH="/app"
EOF
    
    echo "✅ WebSocket proxy configurado en puerto 8002"
fi

# Reiniciar supervisord
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

echo "🎯 Esperando servicios..."
sleep 5

# Verificar servicios después del restart
echo "🔍 Verificando servicios después del restart..."
sudo supervisorctl status

# Testear la conexión WebSocket
echo "🔍 Testeando WebSocket después del fix..."
curl -s "http://localhost:8001/socket.io/?EIO=4&transport=polling" | head -1

echo "✅ WEBSOCKET ROUTING CONFIGURADO"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8001"
echo "WebSocket: http://localhost:8001/socket.io/"