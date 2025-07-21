#!/bin/bash
# Monitor de salud continuo para Mitosis

while true; do
    # Verificar backend
    if ! curl -s -f http://localhost:8001/health >/dev/null 2>&1; then
        echo "$(date): Backend no responde, reiniciando..." >> /var/log/mitosis_health.log
        sudo supervisorctl restart backend
    fi
    
    # Verificar frontend
    if ! curl -s -f http://localhost:3000 >/dev/null 2>&1; then
        echo "$(date): Frontend no responde, reiniciando..." >> /var/log/mitosis_health.log
        sudo supervisorctl restart frontend
    fi
    
    # Esperar 30 segundos antes de la próxima verificación
    sleep 30
done
