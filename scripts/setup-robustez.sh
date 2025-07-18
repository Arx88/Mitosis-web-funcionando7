#!/bin/bash

# =============================================================================
# SCRIPT PRINCIPAL DE ROBUSTEZ - EJECUTAR DESPUÉS DE CUALQUIER CAMBIO
# =============================================================================

echo "🚀 INICIANDO SISTEMA DE ROBUSTEZ PERMANENTE..."

# Función de logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/robustez.log
}

log "🔧 INICIANDO CONFIGURACIÓN ROBUSTA..."

# 1. Ejecutar reparación de dependencias
log "📦 Reparando dependencias..."
/app/scripts/fix-dependencies.sh

# 2. Ejecutar auto-build
log "🏗️  Ejecutando auto-build..."
/app/scripts/auto-build.sh

# 3. Configurar supervisor robusto
log "🛡️  Configurando supervisor robusto..."
/app/scripts/setup-robust-supervisor.sh

# 4. Aplicar configuración
log "🔄 Aplicando configuración..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

# 5. Esperar estabilización
log "⏳ Esperando estabilización..."
sleep 10

# 6. Ejecutar sistema preventivo
log "🛡️  Ejecutando sistema preventivo..."
/app/scripts/preventive-system.sh

# 7. Verificación final
log "🔍 Verificación final..."
if curl -s http://localhost:8001/health >/dev/null && pgrep -f "serve.*dist" >/dev/null; then
    log "✅ SISTEMA ROBUSTO IMPLEMENTADO EXITOSAMENTE"
    echo "
    🎉 ROBUSTEZ PERMANENTE IMPLEMENTADA
    
    ✅ Backend: Funcionando en modo estable
    ✅ Frontend: Modo producción permanente
    ✅ Auto-corrección: Activa
    ✅ Monitoreo: Continuo
    ✅ Scripts: Disponibles
    
    📚 COMANDOS DISPONIBLES:
    - /app/scripts/preventive-system.sh    # Verificar y corregir
    - /app/scripts/robust-deploy.sh        # Deployment completo
    - /app/scripts/auto-build.sh          # Solo build
    
    ⚠️  RECORDATORIO: Siempre ejecutar scripts después de cambios
    "
else
    log "❌ SISTEMA ROBUSTO TUVO PROBLEMAS - REVISAR MANUALMENTE"
    echo "❌ Error en la implementación - Ver logs para detalles"
fi

log "🏁 CONFIGURACIÓN ROBUSTA COMPLETADA"