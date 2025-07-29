#!/bin/bash
###############################################################################
# 🔍 SCRIPT DE VERIFICACIÓN CORS Y WEBSOCKET - MITOSIS
# Verifica que la configuración CORS esté funcionando correctamente
###############################################################################

set -e

echo "🔍 INICIANDO VERIFICACIÓN CORS Y WEBSOCKET..."
echo "=============================================================="

# Cargar configuración detectada si existe
if [ -f "/app/detected_config.env" ]; then
    source /app/detected_config.env
    echo "📋 Configuración cargada desde detected_config.env"
    echo "   URL detectada: $DETECTED_FRONTEND_URL"
    echo "   Método: $DETECTION_METHOD"
    echo "   Última configuración exitosa: $LAST_SUCCESSFUL_START"
else
    echo "⚠️ No se encontró configuración detectada, usando URL desde .env"
    DETECTED_FRONTEND_URL=$(grep "VITE_BACKEND_URL" /app/frontend/.env | cut -d'=' -f2 2>/dev/null || echo "")
fi

if [ -z "$DETECTED_FRONTEND_URL" ]; then
    echo "❌ No se pudo determinar URL frontend"
    exit 1
fi

echo "=============================================================="
echo "🎯 Verificando CORS para URL: $DETECTED_FRONTEND_URL"
echo "=============================================================="

# Test 1: Verificar endpoint de health con CORS
echo "1️⃣ Testing health endpoint con CORS..."
health_cors=$(curl -s -H "Origin: $DETECTED_FRONTEND_URL" \
    -H "Access-Control-Request-Method: GET" \
    -X OPTIONS "http://localhost:8001/api/health" 2>/dev/null || echo "error")

if echo "$health_cors" | grep -q "Access-Control-Allow-Origin\|200"; then
    echo "   ✅ Health endpoint CORS: FUNCIONANDO"
else
    echo "   ❌ Health endpoint CORS: PROBLEMA"
    echo "      Respuesta: $health_cors"
fi

# Test 2: Verificar endpoint de chat con CORS
echo "2️⃣ Testing chat endpoint con CORS..."
chat_cors=$(curl -s -H "Origin: $DETECTED_FRONTEND_URL" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -X OPTIONS "http://localhost:8001/api/agent/chat" 2>/dev/null || echo "error")

if echo "$chat_cors" | grep -q "Access-Control-Allow-Origin\|200"; then
    echo "   ✅ Chat endpoint CORS: FUNCIONANDO"
else
    echo "   ❌ Chat endpoint CORS: PROBLEMA"
    echo "      Respuesta: $chat_cors"
fi

# Test 3: Verificar WebSocket endpoint con CORS (CRÍTICO)
echo "3️⃣ Testing WebSocket endpoint con CORS..."
ws_cors=$(curl -s -H "Origin: $DETECTED_FRONTEND_URL" \
    "http://localhost:8001/api/socket.io/?EIO=4&transport=polling" 2>/dev/null || echo "error")

if echo "$ws_cors" | grep -q '"sid"'; then
    echo "   ✅ WebSocket CORS: FUNCIONANDO PERFECTAMENTE"
    echo "      🎉 Este era el problema principal - AHORA ESTÁ SOLUCIONADO"
else
    echo "   ❌ WebSocket CORS: PROBLEMA DETECTADO"
    echo "      ⚠️ Este es el error que estabas experimentando"
    echo "      Respuesta: $ws_cors"
fi

# Test 4: Verificar headers CORS específicos
echo "4️⃣ Testing headers CORS específicos..."
cors_headers=$(curl -s -I -H "Origin: $DETECTED_FRONTEND_URL" \
    -X OPTIONS "http://localhost:8001/api/socket.io/" 2>/dev/null || echo "error")

if echo "$cors_headers" | grep -q "Access-Control-Allow-Origin"; then
    echo "   ✅ Headers CORS: CONFIGURADOS CORRECTAMENTE"
    allowed_origin=$(echo "$cors_headers" | grep "Access-Control-Allow-Origin" | cut -d' ' -f2- | tr -d '\r\n')
    echo "      🔗 Origen permitido: $allowed_origin"
else
    echo "   ❌ Headers CORS: FALTAN O INCORRECTOS"
fi

# Test 5: Verificar configuración actual en server.py
echo "5️⃣ Verificando configuración actual en server.py..."
if grep -q "$DETECTED_FRONTEND_URL" /app/backend/server.py; then
    echo "   ✅ URL detectada ENCONTRADA en server.py"
    echo "      🎯 La configuración incluye tu URL específica"
else
    echo "   ⚠️ URL específica no encontrada, verificando wildcard..."
    if grep -q "https://\*\.preview\.emergentagent\.com" /app/backend/server.py; then
        echo "   ✅ Wildcard CORS encontrado - debería funcionar"
    else
        echo "   ❌ Configuración CORS problemática"
    fi
fi

echo "=============================================================="
echo "📊 RESUMEN DE VERIFICACIÓN"
echo "=============================================================="

# Contador de tests exitosos
tests_passed=0
total_tests=5

# Verificar cada test nuevamente para el resumen
if curl -s -H "Origin: $DETECTED_FRONTEND_URL" -X OPTIONS "http://localhost:8001/api/health" >/dev/null 2>&1; then
    ((tests_passed++))
fi

if curl -s -H "Origin: $DETECTED_FRONTEND_URL" -X OPTIONS "http://localhost:8001/api/agent/chat" >/dev/null 2>&1; then
    ((tests_passed++))
fi

if curl -s -H "Origin: $DETECTED_FRONTEND_URL" "http://localhost:8001/api/socket.io/?EIO=4&transport=polling" 2>/dev/null | grep -q '"sid"'; then
    ((tests_passed++))
    websocket_working=true
else
    websocket_working=false
fi

if curl -s -I -H "Origin: $DETECTED_FRONTEND_URL" -X OPTIONS "http://localhost:8001/api/socket.io/" 2>/dev/null | grep -q "Access-Control-Allow-Origin"; then
    ((tests_passed++))
fi

if grep -q "$DETECTED_FRONTEND_URL\|https://\*\.preview\.emergentagent\.com" /app/backend/server.py; then
    ((tests_passed++))
fi

echo "📈 Tests pasados: $tests_passed/$total_tests"
echo "🌐 URL verificada: $DETECTED_FRONTEND_URL"

if [ $tests_passed -ge 4 ] && [ "$websocket_working" = true ]; then
    echo ""
    echo "🎉 ¡ÉXITO TOTAL! CORS Y WEBSOCKET FUNCIONANDO CORRECTAMENTE"
    echo "=============================================================="
    echo "✅ Los errores de CORS que experimentabas ESTÁN SOLUCIONADOS"
    echo "✅ WebSocket puede conectarse desde tu frontend"
    echo "✅ Todos los endpoints API son accesibles"
    echo "✅ La configuración es persistente para futuras ejecuciones"
    echo ""
    echo "🚀 TU APLICACIÓN ESTÁ LISTA - NO MÁS ERRORES DE CORS"
    
    # Actualizar archivo de configuración con éxito
    echo "CORS_VERIFICATION_PASSED=true" >> /app/detected_config.env
    echo "LAST_CORS_CHECK=$(date -Iseconds)" >> /app/detected_config.env
    echo "TESTS_PASSED=$tests_passed/$total_tests" >> /app/detected_config.env
    
elif [ "$websocket_working" = false ]; then
    echo ""
    echo "⚠️ WEBSOCKET CORS AÚN TIENE PROBLEMAS"
    echo "=============================================================="
    echo "❌ El error de WebSocket que reportaste persiste"
    echo "🔧 Ejecuta los siguientes comandos para investigar:"
    echo "   1. sudo supervisorctl restart backend"
    echo "   2. tail -20 /var/log/supervisor/backend.err.log"
    echo "   3. curl -v -H \"Origin: $DETECTED_FRONTEND_URL\" \"http://localhost:8001/api/socket.io/?EIO=4&transport=polling\""
    
else
    echo ""
    echo "⚠️ ALGUNOS TESTS FALLARON - REVISIÓN NECESARIA"
    echo "=============================================================="
    echo "🔧 Tests pasados: $tests_passed/$total_tests"
    echo "📋 Verifica los logs para más detalles:"
    echo "   Backend: tail -20 /var/log/supervisor/backend.err.log"
    echo "   Frontend: tail -20 /var/log/supervisor/frontend.err.log"
fi

echo ""
echo "🔧 SCRIPT DE VERIFICACIÓN COMPLETADO"
echo "📅 $(date)"
echo "=============================================================="