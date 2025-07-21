#!/bin/bash
###############################################################################
# 🚀 MITOSIS - SCRIPT DE INICIO SIMPLE Y DIRECTO
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

# Detener servicios existentes para limpiar
sudo supervisorctl stop all 2>/dev/null || true

# Recargar configuración de supervisor
sudo supervisorctl reread 2>/dev/null || true
sudo supervisorctl update 2>/dev/null || true

# Iniciar servicios uno por uno
echo "🗄️ Iniciando MongoDB..."
sudo supervisorctl start mongodb 2>/dev/null || sudo supervisorctl start backend 2>/dev/null || true

echo "🖥️ Iniciando Backend..."  
sudo supervisorctl start backend 2>/dev/null || true

echo "🌐 Iniciando Frontend..."
sudo supervisorctl start frontend 2>/dev/null || true

# Verificar servicios
echo "🔍 Verificando servicios..."
sleep 5

# Verificar cada servicio
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