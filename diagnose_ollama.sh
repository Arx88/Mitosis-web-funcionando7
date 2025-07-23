#!/bin/bash
###############################################################################
# 🔍 DIAGNÓSTICO ESPECÍFICO OLLAMA - VERIFICACIÓN COMPLETA
###############################################################################

echo "🔍 DIAGNÓSTICO ESPECÍFICO DE CONEXIÓN OLLAMA"
echo "=============================================================="

# ========================================================================
# TEST 1: CONEXIÓN DIRECTA A OLLAMA
# ========================================================================

echo "🔍 TEST 1: CONEXIÓN DIRECTA A OLLAMA..."

echo "   Endpoint 1: https://bef4a4bb93d1.ngrok-free.app"
if curl -s -f "https://bef4a4bb93d1.ngrok-free.app/api/tags" >/dev/null 2>&1; then
    echo "   ✅ Endpoint 1: CONECTADO"
    models_count=$(curl -s "https://bef4a4bb93d1.ngrok-free.app/api/tags" | grep -o '"name":' | wc -l)
    echo "      📊 Modelos disponibles: $models_count"
    echo "      🤖 Modelos: $(curl -s 'https://bef4a4bb93d1.ngrok-free.app/api/tags' | grep -o '"name":"[^"]*"' | head -3 | cut -d':' -f2 | tr -d '"' | tr '\n' ', ')"
else
    echo "   ❌ Endpoint 1: NO CONECTADO"
fi

echo "   Endpoint 2: https://78d08925604a.ngrok-free.app"
if curl -s -f "https://78d08925604a.ngrok-free.app/api/tags" >/dev/null 2>&1; then
    echo "   ✅ Endpoint 2: CONECTADO"
else
    echo "   ❌ Endpoint 2: NO CONECTADO"
fi

# ========================================================================
# TEST 2: VERIFICACIÓN BACKEND OLLAMA SERVICE
# ========================================================================

echo ""
echo "🔍 TEST 2: BACKEND OLLAMA SERVICE..."

# Status del agente
agent_status=$(curl -s http://localhost:8001/api/agent/status 2>/dev/null)
if echo "$agent_status" | grep -q "ollama"; then
    echo "   ✅ Backend reporta Ollama:"
    ollama_connected=$(echo "$agent_status" | grep -o '"connected":[a-z]*' | head -1 | cut -d':' -f2)
    ollama_endpoint=$(echo "$agent_status" | grep -o '"endpoint":"[^"]*"' | cut -d':' -f2- | tr -d '"')
    ollama_model=$(echo "$agent_status" | grep -o '"model":"[^"]*"' | cut -d':' -f2 | tr -d '"')
    echo "      🔗 Conectado: $ollama_connected"
    echo "      🌐 Endpoint: $ollama_endpoint"
    echo "      🤖 Modelo: $ollama_model"
else
    echo "   ❌ Backend NO reporta información de Ollama"
fi

# Health check específico de Ollama
ollama_check=$(curl -s -X POST -H "Content-Type: application/json" \
    -d '{"endpoint":"https://bef4a4bb93d1.ngrok-free.app"}' \
    http://localhost:8001/api/agent/ollama/check 2>/dev/null)
if echo "$ollama_check" | grep -q "is_connected"; then
    echo "   ✅ Ollama check endpoint funciona:"
    is_connected=$(echo "$ollama_check" | grep -o '"is_connected":[a-z]*' | cut -d':' -f2)
    echo "      📡 Connection status: $is_connected"
else
    echo "   ❌ Ollama check endpoint NO funciona"
fi

# ========================================================================
# TEST 3: GENERACIÓN REAL CON OLLAMA
# ========================================================================

echo ""
echo "🔍 TEST 3: GENERACIÓN REAL CON OLLAMA..."

# Test de generación de plan
echo "   Probando generación de plan..."
plan_response=$(curl -s -X POST -H "Content-Type: application/json" \
    -d '{"message":"Crear un plan simple de testing", "task_title":"Test Ollama"}' \
    http://localhost:8001/api/agent/generate-plan 2>/dev/null)

if echo "$plan_response" | grep -q "plan"; then
    echo "   ✅ GENERACIÓN DE PLAN: EXITOSA"
    steps_count=$(echo "$plan_response" | grep -o '"title":"[^"]*"' | wc -l)
    enhanced_title=$(echo "$plan_response" | grep -o '"enhanced_title":"[^"]*"' | cut -d':' -f2 | tr -d '"')
    echo "      📝 Título mejorado: $enhanced_title"
    echo "      📊 Pasos generados: $steps_count"
    echo "      🎯 Primera tarea: $(echo "$plan_response" | grep -o '"title":"[^"]*"' | head -1 | cut -d':' -f2 | tr -d '"')"
else
    echo "   ❌ GENERACIÓN DE PLAN: FALLÓ"
    echo "      Error: $plan_response"
fi

echo "   Probando generación de sugerencias..."
suggestions_response=$(curl -s -X POST http://localhost:8001/api/agent/generate-suggestions 2>/dev/null)

if echo "$suggestions_response" | grep -q "suggestions"; then
    echo "   ✅ GENERACIÓN DE SUGERENCIAS: EXITOSA"
    suggestions_count=$(echo "$suggestions_response" | grep -o '"title":"[^"]*"' | wc -l)
    echo "      💡 Sugerencias generadas: $suggestions_count"
    echo "      📝 Primera sugerencia: $(echo "$suggestions_response" | grep -o '"title":"[^"]*"' | head -1 | cut -d':' -f2 | tr -d '"')"
else
    echo "   ❌ GENERACIÓN DE SUGERENCIAS: FALLÓ"
fi

# ========================================================================
# TEST 4: PRUEBA DIRECTA DE CHAT CON OLLAMA
# ========================================================================

echo ""
echo "🔍 TEST 4: PRUEBA DIRECTA CHAT CON OLLAMA..."

# Probar chat directo
echo "   Enviando prompt directo a Ollama..."
direct_ollama=$(curl -s -X POST "https://bef4a4bb93d1.ngrok-free.app/api/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama3.1:8b",
        "prompt": "Responde brevemente: ¿Estás funcionando correctamente?",
        "stream": false
    }' 2>/dev/null)

if echo "$direct_ollama" | grep -q "response"; then
    echo "   ✅ CHAT DIRECTO CON OLLAMA: EXITOSO"
    response_text=$(echo "$direct_ollama" | grep -o '"response":"[^"]*"' | cut -d':' -f2- | tr -d '"' | head -c 100)
    echo "      🤖 Respuesta: $response_text..."
else
    echo "   ❌ CHAT DIRECTO CON OLLAMA: FALLÓ"
    echo "      Error: $(echo "$direct_ollama" | head -c 200)"
fi

# ========================================================================
# TEST 5: VERIFICAR CONFIGURACIÓN EN .ENV
# ========================================================================

echo ""
echo "🔍 TEST 5: CONFIGURACIÓN BACKEND..."

echo "   Variables de entorno Ollama:"
if [ -f "/app/backend/.env" ]; then
    echo "   ✅ Archivo .env encontrado"
    
    ollama_url=$(grep "OLLAMA_BASE_URL" /app/backend/.env | cut -d'=' -f2)
    ollama_model=$(grep "OLLAMA_DEFAULT_MODEL" /app/backend/.env | cut -d'=' -f2)
    llm_provider=$(grep "AGENT_LLM_PROVIDER" /app/backend/.env | cut -d'=' -f2)
    
    echo "      🌐 OLLAMA_BASE_URL: $ollama_url"
    echo "      🤖 OLLAMA_DEFAULT_MODEL: $ollama_model"
    echo "      🔧 AGENT_LLM_PROVIDER: $llm_provider"
    
    # Verificar si el endpoint en .env coincide con el que funciona
    if echo "$ollama_url" | grep -q "bef4a4bb93d1"; then
        echo "      ✅ Endpoint configurado correctamente"
    else
        echo "      ⚠️ Endpoint puede necesitar actualización"
    fi
else
    echo "   ❌ Archivo .env NO encontrado"
fi

# ========================================================================
# REPORTE FINAL
# ========================================================================

echo ""
echo "🎯 REPORTE FINAL - DIAGNÓSTICO OLLAMA"
echo "=============================================================="

# Verificar todos los tests
ollama_direct=false
backend_ollama=false
plan_generation=false
suggestions_generation=false
direct_chat=false

# Test 1: Conexión directa
if curl -s -f "https://bef4a4bb93d1.ngrok-free.app/api/tags" >/dev/null 2>&1; then
    ollama_direct=true
fi

# Test 2: Backend status
if curl -s http://localhost:8001/api/agent/status | grep -q '"connected":true'; then
    backend_ollama=true
fi

# Test 3: Plan generation
if curl -s -X POST -H "Content-Type: application/json" \
    -d '{"message":"test", "task_title":"test"}' \
    http://localhost:8001/api/agent/generate-plan | grep -q "plan"; then
    plan_generation=true
fi

# Test 4: Suggestions
if curl -s -X POST http://localhost:8001/api/agent/generate-suggestions | grep -q "suggestions"; then
    suggestions_generation=true
fi

# Test 5: Direct chat
if curl -s -X POST "https://bef4a4bb93d1.ngrok-free.app/api/generate" \
    -H "Content-Type: application/json" \
    -d '{"model": "llama3.1:8b", "prompt": "test", "stream": false}' | grep -q "response"; then
    direct_chat=true
fi

echo "RESULTADOS:"

if $ollama_direct; then
    echo "✅ CONEXIÓN OLLAMA DIRECTA: OK"
else
    echo "❌ CONEXIÓN OLLAMA DIRECTA: FAIL"
fi

if $backend_ollama; then
    echo "✅ BACKEND OLLAMA STATUS: OK"
else
    echo "❌ BACKEND OLLAMA STATUS: FAIL"
fi

if $plan_generation; then
    echo "✅ GENERACIÓN DE PLANES: OK"
else
    echo "❌ GENERACIÓN DE PLANES: FAIL"
fi

if $suggestions_generation; then
    echo "✅ GENERACIÓN DE SUGERENCIAS: OK"
else
    echo "❌ GENERACIÓN DE SUGERENCIAS: FAIL"
fi

if $direct_chat; then
    echo "✅ CHAT DIRECTO OLLAMA: OK"
else
    echo "❌ CHAT DIRECTO OLLAMA: FAIL"
fi

echo ""

if $ollama_direct && $backend_ollama && $plan_generation && $suggestions_generation; then
    echo "🎉 VEREDICTO: OLLAMA ESTÁ FUNCIONANDO PERFECTAMENTE"
    echo "   ✅ Todas las funcionalidades de IA están operativas"
    echo "   ✅ El problema puede estar en el frontend/UX"
    echo ""
    echo "💡 POSIBLES CAUSAS SI PARECE NO FUNCIONAR:"
    echo "   1. Error en la interfaz de usuario"
    echo "   2. Problema de comunicación frontend-backend"  
    echo "   3. WebSocket no funcionando para updates en tiempo real"
    echo "   4. Racing conditions en la UI"
    echo ""
    echo "🔧 PRÓXIMOS PASOS RECOMENDADOS:"
    echo "   1. Verificar console del navegador para errores JS"
    echo "   2. Revisar network tab para llamadas API fallidas"
    echo "   3. Testear funcionalidad desde la interfaz directamente"
else
    echo "⚠️ VEREDICTO: PROBLEMAS DETECTADOS EN OLLAMA"
    echo ""
    echo "🔧 ACCIONES REQUERIDAS:"
    if ! $ollama_direct; then
        echo "   - Verificar conexión de red a ngrok"
        echo "   - Revisar endpoints de Ollama"
    fi
    if ! $backend_ollama; then
        echo "   - Revisar configuración backend Ollama service"
        echo "   - Verificar variables de entorno"
    fi
    if ! $plan_generation || ! $suggestions_generation; then
        echo "   - Revisar integración LLM en backend"
        echo "   - Verificar logs de errores en generación"
    fi
fi

echo "=============================================================="
echo "🔍 DIAGNÓSTICO COMPLETADO"