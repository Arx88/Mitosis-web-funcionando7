#!/bin/bash

# =============================================================================
# MONITOREO INTELIGENTE - DETECTA Y CORRIGE AUTOMÁTICAMENTE
# =============================================================================

echo "🤖 INICIANDO MONITOREO INTELIGENTE..."

# Archivo de estado
STATE_FILE="/var/log/robustez_state.log"

# Función para logging detallado
log_detailed() {
    local level=$1
    local message=$2
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" | tee -a "$STATE_FILE"
}

# Función para verificar estado del sistema
check_system_health() {
    local issues=0
    
    # Verificar backend
    if ! curl -s http://localhost:8001/health >/dev/null 2>&1; then
        log_detailed "WARNING" "Backend no responde"
        issues=$((issues + 1))
    fi
    
    # Verificar frontend en producción
    if ! pgrep -f "serve.*dist" >/dev/null 2>&1; then
        log_detailed "WARNING" "Frontend no está en modo producción"
        issues=$((issues + 1))
    fi
    
    # Verificar proceso Vite peligroso
    if pgrep -f "vite.*--host" >/dev/null 2>&1; then
        log_detailed "CRITICAL" "Proceso Vite detectado - PELIGROSO"
        issues=$((issues + 1))
    fi
    
    # Verificar supervisor
    if ! sudo supervisorctl status | grep -q "RUNNING"; then
        log_detailed "WARNING" "Algunos servicios no están corriendo"
        issues=$((issues + 1))
    fi
    
    return $issues
}

# Función de auto-corrección
auto_correct() {
    log_detailed "INFO" "Iniciando auto-corrección..."
    
    # Terminar procesos Vite peligrosos
    if pgrep -f "vite.*--host" >/dev/null 2>&1; then
        log_detailed "ACTION" "Terminando procesos Vite peligrosos"
        pkill -f "vite.*--host"
    fi
    
    # Corregir frontend
    if ! pgrep -f "serve.*dist" >/dev/null 2>&1; then
        log_detailed "ACTION" "Corrigiendo frontend a modo producción"
        cd /app/frontend
        npm run build >/dev/null 2>&1
        sudo supervisorctl restart frontend
    fi
    
    # Corregir backend
    if ! curl -s http://localhost:8001/health >/dev/null 2>&1; then
        log_detailed "ACTION" "Reiniciando backend"
        sudo supervisorctl restart backend
    fi
    
    # Esperar estabilización
    sleep 10
    
    # Verificar corrección
    if check_system_health; then
        log_detailed "SUCCESS" "Auto-corrección exitosa"
        return 0
    else
        log_detailed "ERROR" "Auto-corrección falló"
        return 1
    fi
}

# Función para generar reporte
generate_report() {
    local status=$1
    echo "
    📊 REPORTE DE MONITOREO INTELIGENTE
    ========================================
    Timestamp: $(date)
    Estado: $status
    
    🔍 VERIFICACIONES:
    - Backend: $(curl -s http://localhost:8001/health >/dev/null && echo "✅ OK" || echo "❌ ERROR")
    - Frontend: $(pgrep -f "serve.*dist" >/dev/null && echo "✅ OK (producción)" || echo "❌ ERROR")
    - Vite Peligroso: $(pgrep -f "vite.*--host" >/dev/null && echo "❌ DETECTADO" || echo "✅ LIBRE")
    - Supervisor: $(sudo supervisorctl status | grep -q "RUNNING" && echo "✅ OK" || echo "❌ ERROR")
    
    🤖 ACCIONES AUTOMÁTICAS:
    - Auto-corrección: $([ $status == "HEALTHY" ] && echo "No requerida" || echo "Ejecutada")
    - Procesos terminados: $([ -n "$(pgrep -f "vite.*--host")" ] && echo "Sí" || echo "No")
    
    📈 ESTADÍSTICAS:
    - Uptime Backend: $(ps -p $(pgrep -f "server_simple.py") -o etime= 2>/dev/null || echo "No disponible")
    - Uptime Frontend: $(ps -p $(pgrep -f "serve.*dist") -o etime= 2>/dev/null || echo "No disponible")
    
    ========================================
    "
}

# Bucle principal de monitoreo
main_loop() {
    while true; do
        log_detailed "INFO" "Ejecutando verificación de salud..."
        
        if check_system_health; then
            log_detailed "SUCCESS" "Sistema saludable - sin problemas detectados"
            generate_report "HEALTHY"
        else
            log_detailed "WARNING" "Problemas detectados - iniciando auto-corrección"
            if auto_correct; then
                generate_report "CORRECTED"
            else
                generate_report "FAILED"
                log_detailed "CRITICAL" "Auto-corrección falló - intervención manual requerida"
            fi
        fi
        
        sleep 60  # Verificar cada minuto
    done
}

# Configurar trap para salida limpia
trap 'log_detailed "INFO" "Monitoreo inteligente terminado"; exit 0' INT TERM

# Iniciar monitoreo
log_detailed "INFO" "Monitoreo inteligente iniciado"
main_loop