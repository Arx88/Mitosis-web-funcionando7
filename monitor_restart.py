#!/usr/bin/env python3
"""
Monitor de reinicies del sistema - Detecta cuándo se reinician los servicios
"""

import time
import subprocess
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/restart_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_service_status():
    """Obtener estado de todos los servicios"""
    try:
        result = subprocess.run(['sudo', 'supervisorctl', 'status'], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        return ""

def parse_uptime(status_line):
    """Parsear tiempo de ejecución desde línea de estado"""
    if 'uptime' in status_line:
        parts = status_line.split('uptime')
        if len(parts) > 1:
            return parts[1].strip()
    return None

def monitor_services():
    """Monitorear servicios continuamente"""
    logger.info("🔍 Iniciando monitoreo de servicios...")
    
    previous_status = {}
    
    while True:
        try:
            current_status = get_service_status()
            lines = current_status.strip().split('\n')
            
            current_services = {}
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        service_name = parts[0]
                        status = parts[1]
                        uptime = parse_uptime(line)
                        
                        current_services[service_name] = {
                            'status': status,
                            'uptime': uptime,
                            'full_line': line
                        }
            
            # Comparar con estado anterior
            for service_name, current_info in current_services.items():
                if service_name in previous_status:
                    prev_info = previous_status[service_name]
                    
                    # Detectar reinicio
                    if prev_info['status'] == 'RUNNING' and current_info['status'] == 'RUNNING':
                        if current_info['uptime'] and prev_info['uptime']:
                            # Convertir uptime a segundos para comparar
                            current_seconds = parse_uptime_to_seconds(current_info['uptime'])
                            prev_seconds = parse_uptime_to_seconds(prev_info['uptime'])
                            
                            if current_seconds < prev_seconds:
                                logger.warning(f"🔄 REINICIO DETECTADO: {service_name}")
                                logger.info(f"   Anterior: {prev_info['full_line']}")
                                logger.info(f"   Actual: {current_info['full_line']}")
                    
                    # Detectar cambio de estado
                    if prev_info['status'] != current_info['status']:
                        logger.warning(f"⚠️ CAMBIO DE ESTADO: {service_name}")
                        logger.info(f"   {prev_info['status']} -> {current_info['status']}")
                        logger.info(f"   Línea: {current_info['full_line']}")
                else:
                    # Nuevo servicio
                    logger.info(f"✅ Nuevo servicio detectado: {service_name} - {current_info['status']}")
            
            previous_status = current_services
            
            # Dormir por 30 segundos
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo monitoreo...")
            break
        except Exception as e:
            logger.error(f"❌ Error en monitoreo: {e}")
            time.sleep(10)

def parse_uptime_to_seconds(uptime_str):
    """Convertir string de uptime a segundos"""
    try:
        # Formato: "0:03:57" o "0:12:33"
        parts = uptime_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
    except:
        pass
    return 0

if __name__ == "__main__":
    monitor_services()