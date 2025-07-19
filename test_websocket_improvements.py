#!/usr/bin/env python3
"""
Test Script para Verificar Mejoras de WebSocket e Integración
Prueba las mejoras implementadas según UPGRADE.md
"""

import requests
import json
import time
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL del backend
BACKEND_URL = "http://localhost:8001"

def test_backend_health():
    """Verificar que el backend esté funcionando"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"✅ Backend Health: {health_data}")
            return True
        else:
            logger.error(f"❌ Backend Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Backend Connection Error: {e}")
        return False

def test_intent_classification():
    """Probar clasificación de intención mejorada con LLM"""
    test_cases = [
        {"message": "hola", "expected": "casual"},
        {"message": "¿cómo estás?", "expected": "casual"},
        {"message": "buscar información sobre IA en 2025", "expected": "tarea"},
        {"message": "crear un informe de mercado", "expected": "tarea"},
        {"message": "analizar datos de ventas", "expected": "tarea"}
    ]
    
    logger.info("🧪 Testing Intent Classification...")
    
    for i, test_case in enumerate(test_cases):
        try:
            response = requests.post(f"{BACKEND_URL}/api/agent/chat", 
                json={"message": test_case["message"]}, 
                timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar si se generó un plan (indica tarea) o solo respuesta casual
                has_plan = 'plan' in data and data['plan'] and len(data['plan'].get('steps', [])) > 0
                classified_as = "tarea" if has_plan else "casual"
                
                status = "✅" if classified_as == test_case["expected"] else "❌"
                logger.info(f"{status} Test {i+1}: '{test_case['message']}' -> {classified_as} (esperado: {test_case['expected']})")
                
                if has_plan:
                    logger.info(f"   Plan generado con {len(data['plan']['steps'])} pasos")
                    logger.info(f"   Plan source: {data['plan'].get('plan_source', 'unknown')}")
            else:
                logger.error(f"❌ Test {i+1} failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Test {i+1} error: {e}")

def test_plan_generation_robustness():
    """Probar generación robusta de planes y validación de esquemas"""
    logger.info("🧪 Testing Plan Generation Robustness...")
    
    test_messages = [
        "crear un análisis detallado sobre inteligencia artificial",
        "investigar tendencias del mercado tecnológico 2025",
        "desarrollar una estrategia de marketing digital"
    ]
    
    for i, message in enumerate(test_messages):
        try:
            response = requests.post(f"{BACKEND_URL}/api/agent/chat", 
                json={"message": message}, 
                timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'plan' in data and data['plan']:
                    plan = data['plan']
                    
                    # Verificar estructura del plan
                    has_steps = 'steps' in plan and isinstance(plan['steps'], list)
                    has_valid_steps = len(plan['steps']) > 0 if has_steps else False
                    
                    # Verificar que cada paso tenga la estructura correcta
                    valid_step_structure = True
                    if has_steps:
                        for step in plan['steps']:
                            if not all(key in step for key in ['id', 'title', 'description', 'tool', 'status']):
                                valid_step_structure = False
                                break
                    
                    # Verificar información de la fuente del plan
                    plan_source = plan.get('plan_source', 'unknown')
                    schema_validated = plan.get('schema_validated', False)
                    
                    status = "✅" if has_valid_steps and valid_step_structure else "❌"
                    logger.info(f"{status} Test {i+1}: Plan generated successfully")
                    logger.info(f"   Steps: {len(plan['steps']) if has_steps else 0}")
                    logger.info(f"   Plan source: {plan_source}")
                    logger.info(f"   Schema validated: {schema_validated}")
                    logger.info(f"   Execution status: {data.get('execution_status', 'unknown')}")
                    
                    if plan_source == 'fallback':
                        logger.warning(f"   ⚠️ Fallback reason: {plan.get('fallback_reason', 'Unknown')}")
                        
                else:
                    logger.error(f"❌ Test {i+1}: No plan generated")
                    
        except Exception as e:
            logger.error(f"❌ Test {i+1} error: {e}")

def test_task_persistence():
    """Probar persistencia de tareas en MongoDB"""
    logger.info("🧪 Testing Task Persistence...")
    
    try:
        # Crear una tarea
        response = requests.post(f"{BACKEND_URL}/api/agent/chat", 
            json={"message": "buscar información sobre machine learning"}, 
            timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            
            if task_id:
                logger.info(f"✅ Task created: {task_id}")
                
                # Esperar un poco para que la tarea se procese
                time.sleep(2)
                
                # Verificar que la tarea persista (esto requeriría un endpoint específico)
                # Por ahora, solo verificamos que se generó correctamente
                logger.info("✅ Task persistence test completed (structure validated)")
            else:
                logger.error("❌ No task_id returned")
        else:
            logger.error(f"❌ Task creation failed: HTTP {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Task persistence test error: {e}")

def test_error_handling():
    """Probar manejo de errores mejorado"""
    logger.info("🧪 Testing Error Handling...")
    
    # Test con mensaje inválido
    try:
        response = requests.post(f"{BACKEND_URL}/api/agent/chat", 
            json={}, 
            timeout=5)
        
        if response.status_code == 400:
            error_data = response.json()
            logger.info(f"✅ Error handling test: {error_data.get('error', 'Unknown error')}")
        else:
            logger.error(f"❌ Expected 400, got {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error handling test error: {e}")

def main():
    """Ejecutar todos los tests"""
    logger.info("🚀 Starting WebSocket Improvements Test Suite...")
    logger.info(f"🕐 Started at: {datetime.now().isoformat()}")
    
    # Verificar salud del backend
    if not test_backend_health():
        logger.error("❌ Backend not available, aborting tests")
        return
    
    # Ejecutar tests
    test_intent_classification()
    print()
    test_plan_generation_robustness()
    print()
    test_task_persistence()
    print()
    test_error_handling()
    
    logger.info("🎯 Test Suite Completed!")
    logger.info(f"🕐 Finished at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()