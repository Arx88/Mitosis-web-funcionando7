#!/usr/bin/env python3
"""
SISTEMA DE MONITOREO DE FALLBACKS
Herramientas para monitorear, reportar y prevenir el uso excesivo de fallbacks
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import os

logger = logging.getLogger(__name__)

class FallbackMonitor:
    """
    Monitor que rastrea el uso de fallbacks y proporciona métricas para prevenir su abuso
    """
    
    def __init__(self):
        self.monitoring_file = "/app/backend/static/fallback_monitoring.json"
        self.stats_file = "/app/backend/static/fallback_stats.json"
        self.alert_thresholds = {
            'fallback_rate': 0.3,  # 30% de fallbacks es preocupante
            'consecutive_fallbacks': 5,
            'hourly_fallbacks': 20
        }
    
    def record_plan_generation(self, task_id: str, plan_source: str, success: bool, 
                              attempts: int = 1, error_reason: str = None):
        """
        Registra el resultado de generación de un plan
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'task_id': task_id,
            'plan_source': plan_source,
            'success': success,
            'attempts': attempts,
            'is_fallback': 'fallback' in plan_source.lower(),
            'error_reason': error_reason
        }
        
        self._save_record(record)
        logger.info(f"📊 Plan generation recorded: {plan_source} - Success: {success}")
        
        # Verificar alertas
        self._check_fallback_alerts()
    
    def record_step_validation(self, task_id: str, step_id: str, validation_system: str,
                              meets_requirements: bool, completeness_score: float,
                              required_retry: bool = False):
        """
        Registra el resultado de validación de un paso
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'task_id': task_id,
            'step_id': step_id,
            'validation_system': validation_system,
            'meets_requirements': meets_requirements,
            'completeness_score': completeness_score,
            'required_retry': required_retry,
            'is_fallback_validation': validation_system in ['enhanced_permissive', 'minimal_criteria', 'error_recovery']
        }
        
        self._save_validation_record(record)
        
        if required_retry:
            logger.warning(f"⚠️ Step required retry: {step_id} - Score: {completeness_score}%")
        
    def get_fallback_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Obtiene estadísticas de fallbacks para las últimas N horas
        """
        try:
            records = self._load_records()
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_records = [
                r for r in records 
                if datetime.fromisoformat(r['timestamp']) > cutoff_time
            ]
            
            if not recent_records:
                return {
                    'total_plans': 0,
                    'fallback_count': 0,
                    'fallback_rate': 0.0,
                    'success_rate': 0.0,
                    'alert_level': 'none'
                }
            
            total_plans = len(recent_records)
            fallback_plans = sum(1 for r in recent_records if r['is_fallback'])
            successful_plans = sum(1 for r in recent_records if r['success'])
            
            fallback_rate = fallback_plans / total_plans if total_plans > 0 else 0
            success_rate = successful_plans / total_plans if total_plans > 0 else 0
            
            # Calcular nivel de alerta
            alert_level = 'none'
            if fallback_rate > self.alert_thresholds['fallback_rate']:
                alert_level = 'high'
            elif fallback_rate > self.alert_thresholds['fallback_rate'] * 0.7:
                alert_level = 'medium'
            elif fallback_rate > self.alert_thresholds['fallback_rate'] * 0.4:
                alert_level = 'low'
            
            # Análisis de fuentes de planes
            plan_sources = Counter(r['plan_source'] for r in recent_records)
            
            # Análisis de razones de error
            error_reasons = Counter(
                r['error_reason'] for r in recent_records 
                if r['error_reason'] and not r['success']
            )
            
            stats = {
                'period_hours': hours,
                'total_plans': total_plans,
                'fallback_count': fallback_plans,
                'fallback_rate': round(fallback_rate, 3),
                'success_rate': round(success_rate, 3),
                'alert_level': alert_level,
                'plan_sources': dict(plan_sources),
                'error_reasons': dict(error_reasons),
                'avg_attempts': sum(r['attempts'] for r in recent_records) / total_plans if total_plans > 0 else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating fallback statistics: {e}")
            return {'error': str(e)}
    
    def get_validation_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Obtiene estadísticas de validaciones para las últimas N horas
        """
        try:
            records = self._load_validation_records()
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_records = [
                r for r in records 
                if datetime.fromisoformat(r['timestamp']) > cutoff_time
            ]
            
            if not recent_records:
                return {
                    'total_validations': 0,
                    'fallback_validations': 0,
                    'avg_score': 0.0,
                    'retry_rate': 0.0
                }
            
            total_validations = len(recent_records)
            fallback_validations = sum(1 for r in recent_records if r['is_fallback_validation'])
            validations_passed = sum(1 for r in recent_records if r['meets_requirements'])
            retries_required = sum(1 for r in recent_records if r['required_retry'])
            
            avg_score = sum(r['completeness_score'] for r in recent_records) / total_validations
            retry_rate = retries_required / total_validations if total_validations > 0 else 0
            pass_rate = validations_passed / total_validations if total_validations > 0 else 0
            
            # Análisis por sistema de validación
            validation_systems = Counter(r['validation_system'] for r in recent_records)
            
            stats = {
                'period_hours': hours,
                'total_validations': total_validations,
                'fallback_validations': fallback_validations,
                'fallback_validation_rate': round(fallback_validations / total_validations, 3) if total_validations > 0 else 0,
                'avg_completeness_score': round(avg_score, 2),
                'retry_rate': round(retry_rate, 3),
                'pass_rate': round(pass_rate, 3),
                'validation_systems': dict(validation_systems)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating validation statistics: {e}")
            return {'error': str(e)}
    
    def generate_improvement_report(self) -> Dict[str, Any]:
        """
        Genera un reporte con recomendaciones para reducir el uso de fallbacks
        """
        try:
            plan_stats = self.get_fallback_statistics(24)
            validation_stats = self.get_validation_statistics(24)
            
            recommendations = []
            priority_level = 'low'
            
            # Analizar tasa de fallbacks en planes
            if plan_stats.get('fallback_rate', 0) > self.alert_thresholds['fallback_rate']:
                priority_level = 'high'
                recommendations.extend([
                    "Investigar por qué Ollama falla frecuentemente",
                    "Revisar conectividad y recursos del servicio Ollama",
                    "Considerar mejorar los prompts de generación de planes",
                    "Implementar caché de planes para consultas similares"
                ])
            
            # Analizar tasas de retry en validaciones
            if validation_stats.get('retry_rate', 0) > 0.4:  # 40% de retries es mucho
                priority_level = max(priority_level, 'medium')
                recommendations.extend([
                    "Revisar criterios de validación - podrían ser muy estrictos",
                    "Analizar herramientas que fallan más frecuentemente",
                    "Mejorar calidad de resultados de herramientas",
                    "Optimizar mapeo de herramientas a funciones"
                ])
            
            # Analizar scores de completitud
            if validation_stats.get('avg_completeness_score', 0) < 60:
                recommendations.extend([
                    "Mejorar calidad de ejecución de herramientas",
                    "Revisar parámetros de herramientas para mejores resultados",
                    "Considerar pre-procesamiento de queries de búsqueda",
                    "Implementar post-procesamiento de resultados"
                ])
            
            # Analizar errores frecuentes
            common_errors = plan_stats.get('error_reasons', {})
            if common_errors:
                most_common_error = max(common_errors.items(), key=lambda x: x[1])
                recommendations.append(f"Priorizar solución de error: {most_common_error[0]} ({most_common_error[1]} ocurrencias)")
            
            if not recommendations:
                recommendations.append("Sistema funcionando bien, sin mejoras críticas necesarias")
                priority_level = 'none'
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'priority_level': priority_level,
                'plan_statistics': plan_stats,
                'validation_statistics': validation_stats,
                'recommendations': recommendations,
                'summary': {
                    'total_issues_found': len([r for r in recommendations if 'funcionando bien' not in r]),
                    'fallback_health': 'poor' if priority_level == 'high' else 'fair' if priority_level == 'medium' else 'good'
                }
            }
            
            # Guardar reporte
            self._save_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating improvement report: {e}")
            return {'error': str(e)}
    
    def _check_fallback_alerts(self):
        """
        Verifica si hay condiciones de alerta por exceso de fallbacks
        """
        try:
            # Verificar últimos 10 registros para fallbacks consecutivos
            records = self._load_records()[-10:]
            consecutive_fallbacks = 0
            
            for record in reversed(records):
                if record['is_fallback']:
                    consecutive_fallbacks += 1
                else:
                    break
            
            if consecutive_fallbacks >= self.alert_thresholds['consecutive_fallbacks']:
                logger.error(f"🚨 ALERT: {consecutive_fallbacks} fallbacks consecutivos detectados!")
                self._send_alert(f"Fallbacks consecutivos: {consecutive_fallbacks}")
            
            # Verificar fallbacks por hora
            hour_stats = self.get_fallback_statistics(1)
            if hour_stats.get('fallback_count', 0) >= self.alert_thresholds['hourly_fallbacks']:
                logger.error(f"🚨 ALERT: {hour_stats['fallback_count']} fallbacks en la última hora!")
                self._send_alert(f"Fallbacks por hora: {hour_stats['fallback_count']}")
                
        except Exception as e:
            logger.error(f"Error checking fallback alerts: {e}")
    
    def _save_record(self, record: dict):
        """Guarda un registro de generación de plan"""
        try:
            records = self._load_records()
            records.append(record)
            
            # Mantener solo últimos 1000 registros
            if len(records) > 1000:
                records = records[-1000:]
            
            os.makedirs(os.path.dirname(self.monitoring_file), exist_ok=True)
            with open(self.monitoring_file, 'w') as f:
                json.dump(records, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving monitoring record: {e}")
    
    def _save_validation_record(self, record: dict):
        """Guarda un registro de validación"""
        try:
            validation_file = self.monitoring_file.replace('.json', '_validations.json')
            
            records = self._load_validation_records()
            records.append(record)
            
            # Mantener solo últimos 2000 registros de validación
            if len(records) > 2000:
                records = records[-2000:]
            
            os.makedirs(os.path.dirname(validation_file), exist_ok=True)
            with open(validation_file, 'w') as f:
                json.dump(records, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving validation record: {e}")
    
    def _load_records(self) -> List[dict]:
        """Carga registros de generación de planes"""
        try:
            if os.path.exists(self.monitoring_file):
                with open(self.monitoring_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading monitoring records: {e}")
            return []
    
    def _load_validation_records(self) -> List[dict]:
        """Carga registros de validación"""
        try:
            validation_file = self.monitoring_file.replace('.json', '_validations.json')
            if os.path.exists(validation_file):
                with open(validation_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading validation records: {e}")
            return []
    
    def _save_report(self, report: dict):
        """Guarda un reporte de mejoras"""
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, 'w') as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving improvement report: {e}")
    
    def _send_alert(self, message: str):
        """Envía una alerta (puede ser expandido para notificaciones reales)"""
        alert_log = f"🚨 FALLBACK ALERT: {message} - {datetime.now().isoformat()}"
        logger.error(alert_log)
        
        # En futuro, podría enviar notificaciones por email, webhook, etc.
        try:
            alert_file = "/app/backend/static/fallback_alerts.log"
            os.makedirs(os.path.dirname(alert_file), exist_ok=True)
            with open(alert_file, 'a') as f:
                f.write(alert_log + '\n')
        except Exception as e:
            logger.error(f"Error writing alert log: {e}")


# Instancia global del monitor
fallback_monitor = FallbackMonitor()


def record_plan_generation_result(task_id: str, plan_source: str, success: bool, 
                                 attempts: int = 1, error_reason: str = None):
    """
    Función helper para registrar resultados de generación de planes
    """
    fallback_monitor.record_plan_generation(task_id, plan_source, success, attempts, error_reason)


def record_step_validation_result(task_id: str, step_id: str, validation_system: str,
                                 meets_requirements: bool, completeness_score: float,
                                 required_retry: bool = False):
    """
    Función helper para registrar resultados de validación de pasos
    """
    fallback_monitor.record_step_validation(
        task_id, step_id, validation_system, meets_requirements, 
        completeness_score, required_retry
    )


def get_fallback_health_report() -> Dict[str, Any]:
    """
    Función helper para obtener un reporte de salud de fallbacks
    """
    return fallback_monitor.generate_improvement_report()


def is_fallback_rate_healthy() -> bool:
    """
    Verifica si la tasa de fallbacks está en niveles saludables
    """
    try:
        stats = fallback_monitor.get_fallback_statistics(6)  # Últimas 6 horas
        return stats.get('alert_level', 'none') in ['none', 'low']
    except:
        return True  # Asumir saludable si hay error