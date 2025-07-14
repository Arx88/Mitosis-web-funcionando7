#!/bin/bash
# Script de inicio para el backend del Agente General

echo "🚀 Iniciando Agente General Backend..."

# Verificar que Python está disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    exit 1
fi

# Cambiar al directorio del backend
cd /app/agent_backend

# Verificar que las dependencias están instaladas
echo "📦 Verificando dependencias..."
if ! pip list | grep -q flask; then
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
fi

# Verificar conexión con Ollama
echo "🧠 Verificando conexión con Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama está conectado"
else
    echo "⚠️  Advertencia: Ollama no está disponible en localhost:11434"
    echo "   Asegúrate de que Ollama esté ejecutándose con: ollama serve"
fi

# Iniciar el servidor
echo "🎯 Iniciando servidor en http://localhost:5000"
python3 src/main.py