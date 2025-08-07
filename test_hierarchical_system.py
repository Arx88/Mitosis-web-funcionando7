#!/usr/bin/env python3
"""
🧪 TEST DEL SISTEMA JERÁRQUICO DE BÚSQUEDA WEB
Valida que la implementación del sistema jerárquico funcione correctamente
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8001"
TEST_TASK_ID = f"test-hierarchical-{int(time.time())}"

def log_test(message, status="INFO"):
    """Log con formato consistente"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_icon = "✅" if status == "SUCCESS" else "❌" if status == "ERROR" else "🔍"
    print(f"[{timestamp}] {status_icon} {message}")

def test_backend_health():
    """Test 1: Verificar que el backend esté funcionando"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            log_test("Backend health check: PASSED", "SUCCESS")
            return True
        else:
            log_test(f"Backend health check failed: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log_test(f"Backend connection failed: {str(e)}", "ERROR")
        return False

def test_create_hierarchical_task():
    """Test 2: Crear una tarea que use búsqueda jerárquica"""
    try:
        payload = {
            "message": "Busca información sobre energía solar análisis 2024 actualidad"
        }
        
        log_test("Enviando tarea para generar plan jerárquico...")
        response = requests.post(
            f"{BASE_URL}/api/agent/chat",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            plan = data.get('plan', {})
            steps = plan.get('steps', [])
            
            log_test(f"Plan generado exitosamente - Task ID: {task_id}", "SUCCESS")
            log_test(f"Plan contiene {len(steps)} pasos", "INFO")
            
            # Verificar que el primer paso use web_search
            if steps and len(steps) > 0:
                first_step = steps[0]
                if first_step.get('tool') == 'web_search':
                    log_test("Primer paso usa web_search correctamente", "SUCCESS")
                    return task_id, steps
                else:
                    log_test(f"Primer paso usa {first_step.get('tool')} en lugar de web_search", "ERROR")
                    return None, []
            else:
                log_test("Plan no contiene pasos", "ERROR")
                return None, []
        else:
            log_test(f"Error creando tarea: {response.status_code}", "ERROR")
            return None, []
            
    except Exception as e:
        log_test(f"Error en creación de tarea: {str(e)}", "ERROR")
        return None, []

def test_execute_hierarchical_step(task_id, step_number=1):
    """Test 3: Ejecutar el primer paso que debería usar el sistema jerárquico"""
    try:
        log_test(f"Ejecutando paso {step_number} con sistema jerárquico...")
        
        response = requests.post(
            f"{BASE_URL}/api/agent/execute-step-detailed/{task_id}/step-{step_number}",
            timeout=120  # 2 minutos para búsquedas jerárquicas
        )
        
        if response.status_code == 200:
            data = response.json()
            step_result = data.get('step_result', {})
            
            # Verificar características del sistema jerárquico
            hierarchical_info = step_result.get('hierarchical_info', {})
            results_count = step_result.get('results_count', 0)
            searches_performed = step_result.get('searches_performed', 0)
            confidence_score = step_result.get('confidence_score', 0)
            
            log_test(f"Ejecución jerárquica completada:", "SUCCESS")
            log_test(f"  • Búsquedas realizadas: {searches_performed}")
            log_test(f"  • Resultados obtenidos: {results_count}")
            log_test(f"  • Puntuación de confianza: {confidence_score}%")
            
            # Validar que sea realmente jerárquico
            if searches_performed > 1:
                log_test("✅ SISTEMA JERÁRQUICO VERIFICADO: Múltiples búsquedas ejecutadas", "SUCCESS")
            else:
                log_test("⚠️ Sistema no parece jerárquico: Solo 1 búsqueda ejecutada", "ERROR")
            
            if hierarchical_info:
                log_test("✅ INFORMACIÓN JERÁRQUICA PRESENTE", "SUCCESS")
                log_test(f"  • Sub-tareas ejecutadas: {hierarchical_info.get('sub_tasks_executed', 0)}")
                log_test(f"  • Criterio cumplido: {hierarchical_info.get('meets_criteria', False)}")
            else:
                log_test("❌ Información jerárquica faltante", "ERROR")
            
            return step_result
            
        else:
            log_test(f"Error ejecutando paso: {response.status_code}", "ERROR")
            return None
            
    except Exception as e:
        log_test(f"Error en ejecución jerárquica: {str(e)}", "ERROR")
        return None

def test_hierarchical_features(step_result):
    """Test 4: Validar características específicas del sistema jerárquico"""
    if not step_result:
        log_test("No hay resultado de paso para validar", "ERROR")
        return False
    
    score = 0
    max_score = 6
    
    # Característica 1: Múltiples búsquedas
    searches_performed = step_result.get('searches_performed', 0)
    if searches_performed > 1:
        log_test(f"✅ Múltiples búsquedas: {searches_performed} ejecutadas", "SUCCESS")
        score += 1
    else:
        log_test(f"❌ Solo {searches_performed} búsqueda ejecutada", "ERROR")
    
    # Característica 2: Información jerárquica
    hierarchical_info = step_result.get('hierarchical_info', {})
    if hierarchical_info:
        log_test("✅ Información jerárquica presente", "SUCCESS")
        score += 1
    else:
        log_test("❌ Información jerárquica faltante", "ERROR")
    
    # Característica 3: Puntuación de confianza
    confidence_score = step_result.get('confidence_score', 0)
    if confidence_score > 0:
        log_test(f"✅ Puntuación de confianza: {confidence_score}%", "SUCCESS")
        score += 1
    else:
        log_test("❌ Sin puntuación de confianza", "ERROR")
    
    # Característica 4: Resultados múltiples
    results_count = step_result.get('results_count', 0)
    if results_count >= 3:
        log_test(f"✅ Resultados suficientes: {results_count}", "SUCCESS")
        score += 1
    else:
        log_test(f"⚠️ Pocos resultados: {results_count}", "ERROR")
    
    # Característica 5: Tipo jerárquico
    result_type = step_result.get('type', '')
    if 'hierarchical' in result_type:
        log_test("✅ Tipo marcado como jerárquico", "SUCCESS")
        score += 1
    else:
        log_test(f"⚠️ Tipo no jerárquico: {result_type}", "ERROR")
    
    # Característica 6: Summary descriptivo
    summary = step_result.get('summary', '')
    if 'jerárquica' in summary.lower():
        log_test("✅ Summary incluye referencia jerárquica", "SUCCESS")
        score += 1
    else:
        log_test("⚠️ Summary no menciona funcionalidad jerárquica", "ERROR")
    
    success_rate = (score / max_score) * 100
    log_test(f"📊 PUNTUACIÓN CARACTERÍSTICAS JERÁRQUICAS: {score}/{max_score} ({success_rate:.1f}%)")
    
    return success_rate >= 80

def main():
    """Ejecutar todos los tests del sistema jerárquico"""
    print("🧪 INICIANDO TESTING DEL SISTEMA JERÁRQUICO")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_backend_health():
        print("\n❌ TESTING ABORTADO: Backend no disponible")
        sys.exit(1)
    
    print()
    
    # Test 2: Crear tarea jerárquica
    task_id, steps = test_create_hierarchical_task()
    if not task_id:
        print("\n❌ TESTING ABORTADO: No se pudo crear tarea")
        sys.exit(1)
    
    print()
    
    # Test 3: Ejecutar paso jerárquico
    step_result = test_execute_hierarchical_step(task_id)
    if not step_result:
        print("\n❌ TESTING ABORTADO: No se pudo ejecutar paso jerárquico")
        sys.exit(1)
    
    print()
    
    # Test 4: Validar características jerárquicas
    hierarchical_success = test_hierarchical_features(step_result)
    
    print()
    print("=" * 60)
    print("🎯 RESUMEN DEL TESTING")
    print(f"📋 Task ID: {task_id}")
    print(f"🔍 Pasos en plan: {len(steps)}")
    
    if hierarchical_success:
        print("✅ SISTEMA JERÁRQUICO: FUNCIONANDO CORRECTAMENTE")
        print("🎉 TESTING COMPLETADO CON ÉXITO")
    else:
        print("⚠️ SISTEMA JERÁRQUICO: NECESITA MEJORAS")
        print("🔧 TESTING COMPLETADO CON PROBLEMAS")
    
    return hierarchical_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)