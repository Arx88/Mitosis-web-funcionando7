#!/bin/bash

echo "🚀 Setting up Mitosis for stable production mode..."

# Navigate to frontend directory
cd /app/frontend

echo "📦 Installing frontend dependencies..."
if ! yarn install; then
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi

echo "🏗️ Building frontend for production..."
if ! npm run build; then
    echo "❌ Failed to build frontend"
    exit 1
fi

echo "🌐 Installing http-server globally..."
if ! npm install -g http-server; then
    echo "❌ Failed to install http-server"
    exit 1
fi

# Navigate to backend directory
cd /app/backend

echo "📦 Installing backend dependencies..."
if ! pip install -r requirements.txt; then
    echo "❌ Failed to install backend dependencies"
    exit 1
fi

echo "⚙️ Configuring supervisor for production mode..."
# Ensure supervisor is configured for production mode
cat > /etc/supervisor/conf.d/supervisord.conf << 'EOF'
[program:backend]
command=/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true

[program:frontend]
command=http-server dist -p 3000 -a 0.0.0.0
environment=HOST="0.0.0.0",PORT="3000",
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
command=/usr/bin/mongod --bind_ip_all
autostart=true
autorestart=true
stderr_logfile=/var/log/mongodb.err.log
stdout_logfile=/var/log/mongodb.out.log
EOF

echo "🔄 Reloading supervisor configuration..."
supervisorctl reread
supervisorctl update

echo "🚀 Starting all services..."
supervisorctl restart all

# Wait a few seconds for services to start
sleep 5

echo "✅ Checking service status..."
supervisorctl status

# Verify production mode
echo "🔍 Verifying production mode..."
if curl -s http://localhost:3000 | grep -q "@vite/client"; then
    echo "❌ WARNING: Still running in development mode!"
    exit 1
else
    echo "✅ Running in production mode!"
fi

echo ""
echo "🎉 Setup complete! Mitosis is now running in stable production mode."
echo "🌐 Application available at: https://11a8329d-458b-411d-ad58-e540e377cb3b.preview.emergentagent.com"
echo ""
echo "📋 Service status:"
supervisorctl status