#!/bin/bash

# =============================================================================
# SISTEMA PREVENTIVO DE ROBUSTEZ - EJECUTAR CADA VEZ QUE SE HAGAN CAMBIOS
# =============================================================================

echo "🛡️  SISTEMA PREVENTIVO ACTIVADO - GARANTIZANDO ROBUSTEZ..."

# Función para verificar y corregir el estado
check_and_fix() {
    local service=$1
    local expected_state=$2
    
    echo "🔍 Verificando $service..."
    
    case $service in
        "frontend")
            if pgrep -f "serve.*dist" > /dev/null; then
                echo "✅ $service: Correcto (modo producción)"
            else
                echo "⚠️  $service: Incorrecto - Corrigiendo..."
                cd /app/frontend
                npm run build
                sudo supervisorctl restart frontend
                sleep 3
                if pgrep -f "serve.*dist" > /dev/null; then
                    echo "✅ $service: Corregido"
                else
                    echo "❌ $service: Fallo en corrección"
                fi
            fi
            ;;
        "backend")
            if curl -s http://localhost:8001/health > /dev/null; then
                echo "✅ $service: Funcionando"
            else
                echo "⚠️  $service: No responde - Corrigiendo..."
                sudo supervisorctl restart backend
                sleep 5
                if curl -s http://localhost:8001/health > /dev/null; then
                    echo "✅ $service: Corregido"
                else
                    echo "❌ $service: Fallo en corrección"
                fi
            fi
            ;;
    esac
}

# Verificar todos los servicios
echo "🔄 VERIFICACIÓN COMPLETA DE SERVICIOS..."
check_and_fix "backend"
check_and_fix "frontend"

# Verificar que no hay procesos Vite corriendo
if pgrep -f "vite.*--host" > /dev/null; then
    echo "🚨 ALERTA: Proceso Vite detectado - Terminando..."
    pkill -f "vite.*--host"
    echo "✅ Proceso Vite terminado"
fi

# Verificar configuración de package.json
if grep -q '"start": "vite' /app/frontend/package.json; then
    echo "⚠️  package.json tiene comando peligroso - Corrigiendo..."
    sed -i 's/"start": "vite.*"/"start": "echo '\''⚠️  USANDO MODO PRODUCCIÓN AUTOMÁTICO'\'' \&\& \/app\/scripts\/auto-build.sh \&\& serve -s dist -l 3000"/' /app/frontend/package.json
    echo "✅ package.json corregido"
fi

# Verificar estado final
echo "📊 ESTADO FINAL:"
echo "Backend: $(curl -s http://localhost:8001/health >/dev/null && echo "✅ OK" || echo "❌ ERROR")"
echo "Frontend: $(pgrep -f "serve.*dist" >/dev/null && echo "✅ OK (producción)" || echo "❌ ERROR")"
echo "MongoDB: $(sudo supervisorctl status mongodb | grep -q "RUNNING" && echo "✅ OK" || echo "❌ ERROR")"

echo "🎉 SISTEMA PREVENTIVO COMPLETADO"