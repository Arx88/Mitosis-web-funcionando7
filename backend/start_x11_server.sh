#!/bin/bash

# 🖥️ START X11 VIRTUAL DISPLAY SERVER FOR REAL BROWSER NAVIGATION
# Script para iniciar servidor X11 virtual con Xvfb para navegación visual

echo "🖥️ INICIANDO SERVIDOR X11 VIRTUAL PARA NAVEGACIÓN REAL..."

# Configurar variables de entorno
export DISPLAY=:99
export XVFB_WHD=1920x1080x24

# Matar procesos X11 existentes si los hay
pkill -f "Xvfb :99" 2>/dev/null || true
pkill -f "fluxbox" 2>/dev/null || true
pkill -f "x11vnc" 2>/dev/null || true

# Esperar un momento para que los procesos terminen
sleep 2

echo "🚀 Iniciando Xvfb en display :99..."
# Iniciar Xvfb (X11 Virtual Framebuffer)
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Esperar que Xvfb se inicie
sleep 3

# Verificar que Xvfb está corriendo
if ps -p $XVFB_PID > /dev/null; then
    echo "✅ Xvfb iniciado correctamente (PID: $XVFB_PID)"
else
    echo "❌ Error: Xvfb no se pudo iniciar"
    exit 1
fi

echo "🚀 Iniciando fluxbox window manager..."
# Iniciar fluxbox como window manager
DISPLAY=:99 fluxbox &
FLUXBOX_PID=$!

# Esperar que fluxbox se inicie
sleep 2

echo "🚀 Iniciando x11vnc para acceso remoto (puerto 5900)..."
# Iniciar x11vnc para poder ver el display remotamente si es necesario
DISPLAY=:99 x11vnc -forever -nopw -display :99 -rfbport 5900 &
VNC_PID=$!

# Verificar que todo está funcionando
echo "🔍 Verificando servicios X11..."

if ps -p $XVFB_PID > /dev/null; then
    echo "✅ Xvfb: FUNCIONANDO (PID: $XVFB_PID)"
else
    echo "❌ Xvfb: NO FUNCIONANDO"
fi

if ps -p $FLUXBOX_PID > /dev/null; then
    echo "✅ Fluxbox: FUNCIONANDO (PID: $FLUXBOX_PID)"
else
    echo "❌ Fluxbox: NO FUNCIONANDO"
fi

if ps -p $VNC_PID > /dev/null; then
    echo "✅ x11vnc: FUNCIONANDO (PID: $VNC_PID)"
else
    echo "❌ x11vnc: NO FUNCIONANDO"
fi

# Test del display
echo "🧪 Probando display X11..."
DISPLAY=:99 xdpyinfo >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Display :99 funcionando correctamente"
    
    # Información del display
    echo "📊 Información del display:"
    DISPLAY=:99 xdpyinfo | grep -E "dimensions|resolution" | head -2
else
    echo "❌ Error: Display :99 no responde"
    exit 1
fi

echo ""
echo "🎉 SERVIDOR X11 VIRTUAL CONFIGURADO EXITOSAMENTE!"
echo "=================================================="
echo "🖥️  Display: :99"
echo "📏 Resolución: 1920x1080x24"
echo "🌐 VNC Puerto: 5900 (para acceso remoto)"
echo "🔧 Window Manager: fluxbox"
echo "📍 PIDs: Xvfb=$XVFB_PID, Fluxbox=$FLUXBOX_PID, VNC=$VNC_PID"
echo "=================================================="
echo ""
echo "💡 Para usar en browser-use:"
echo "   export DISPLAY=:99"
echo "   browser_session = BrowserSession(headless=False)"
echo ""
echo "🔍 Para ver la pantalla remotamente:"
echo "   Conectar VNC cliente a localhost:5900"
echo ""

# Mantener el script corriendo y monitorear los procesos
echo "🔄 Monitoreando servicios X11... (Ctrl+C para detener)"

trap 'echo "🛑 Deteniendo servicios X11..."; kill $XVFB_PID $FLUXBOX_PID $VNC_PID 2>/dev/null; exit 0' INT TERM

# Loop infinito para mantener el script activo
while true; do
    sleep 10
    
    # Verificar que los servicios sigan corriendo
    if ! ps -p $XVFB_PID > /dev/null; then
        echo "⚠️ Xvfb se detuvo, reiniciando..."
        Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
        XVFB_PID=$!
    fi
    
    if ! ps -p $FLUXBOX_PID > /dev/null; then
        echo "⚠️ Fluxbox se detuvo, reiniciando..."
        DISPLAY=:99 fluxbox &
        FLUXBOX_PID=$!
    fi
    
    if ! ps -p $VNC_PID > /dev/null; then
        echo "⚠️ x11vnc se detuvo, reiniciando..."
        DISPLAY=:99 x11vnc -forever -nopw -display :99 -rfbport 5900 &
        VNC_PID=$!
    fi
done