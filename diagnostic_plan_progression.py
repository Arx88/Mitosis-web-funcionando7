#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO DEL PROBLEMA DE PLAN ACTIVO
Verifica por qué el paso activo no avanza en el frontend
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8001"

def test_plan_progression():
    """Test para verificar la progresión del plan"""
    print("🔍 Diagnóstico del problema de progresión del plan...")
    
    # 1. Crear una tarea de prueba
    task_message = "Busca información sobre los beneficios del ejercicio físico"
    
    try:
        # Crear tarea
        response = requests.post(f"{BACKEND_URL}/api/agent/chat", json={
            "message": task_message,
            "task_id": f"diag_test_{int(time.time())}"
        })
        
        if response.status_code != 200:
            print(f"❌ Error creando tarea: {response.status_code}")
            return False
        
        result = response.json()
        task_id = result.get('task_id')
        print(f"✅ Tarea creada: {task_id}")
        
        # 2. Esperar a que se genere el plan
        print("⏳ Esperando generación del plan...")
        time.sleep(5)
        
        # 3. Obtener el plan inicial
        plan_response = requests.get(f"{BACKEND_URL}/api/agent/get-task-plan/{task_id}")
        if plan_response.status_code != 200:
            print(f"❌ Error obteniendo plan: {plan_response.status_code}")
            return False
        
        plan_data = plan_response.json()
        steps = plan_data.get('plan', [])
        print(f"📋 Plan inicial generado con {len(steps)} pasos")
        
        # Verificar estado inicial del plan
        for i, step in enumerate(steps, 1):
            print(f"  Paso {i}: {step.get('title', 'Sin título')}")
            print(f"    - ID: {step.get('id')}")
            print(f"    - Activo: {step.get('active', False)}")
            print(f"    - Completado: {step.get('completed', False)}")
            print(f"    - Estado: {step.get('status', 'unknown')}")
        
        # 4. Verificar que el primer paso esté activo
        first_step = steps[0] if steps else None
        if first_step and not first_step.get('active'):
            print("🚨 PROBLEMA DETECTADO: El primer paso no está marcado como activo")
            
            # Intentar forzar la activación del primer paso
            print("🔧 Intentando corregir estado del primer paso...")
            
            # Llamar al endpoint que debe marcar el primer paso como activo
            start_response = requests.post(f"{BACKEND_URL}/api/agent/start-task-execution/{task_id}")
            if start_response.status_code == 200:
                print("✅ Iniciación de ejecución de tarea llamada")
                time.sleep(2)
                
                # Verificar plan actualizado
                updated_plan_response = requests.get(f"{BACKEND_URL}/api/agent/get-task-plan/{task_id}")
                if updated_plan_response.status_code == 200:
                    updated_plan_data = updated_plan_response.json()
                    updated_steps = updated_plan_data.get('plan', [])
                    
                    print("📋 Estado del plan después de start-task-execution:")
                    for i, step in enumerate(updated_steps, 1):
                        print(f"  Paso {i}: {step.get('title', 'Sin título')}")
                        print(f"    - Activo: {step.get('active', False)}")
                        print(f"    - Estado: {step.get('status', 'unknown')}")
            else:
                print(f"❌ Error iniciando ejecución: {start_response.status_code}")
        
        # 5. Ejecutar el primer paso manualmente
        if steps:
            first_step_id = steps[0].get('id')
            print(f"🔄 Ejecutando primer paso manualmente: {first_step_id}")
            
            exec_response = requests.post(f"{BACKEND_URL}/api/agent/execute-step-detailed/{task_id}/{first_step_id}")
            
            if exec_response.status_code == 200:
                exec_result = exec_response.json()
                print("✅ Primer paso ejecutado")
                print(f"   Success: {exec_result.get('success')}")
                print(f"   Step result: {exec_result.get('step_result', {}).get('success')}")
                
                # Esperar un poco y verificar el plan actualizado
                time.sleep(3)
                
                final_plan_response = requests.get(f"{BACKEND_URL}/api/agent/get-task-plan/{task_id}")
                if final_plan_response.status_code == 200:
                    final_plan_data = final_plan_response.json()
                    final_steps = final_plan_data.get('plan', [])
                    
                    print("📋 Estado final del plan:")
                    for i, step in enumerate(final_steps, 1):
                        print(f"  Paso {i}: {step.get('title', 'Sin título')}")
                        print(f"    - Activo: {step.get('active', False)}")
                        print(f"    - Completado: {step.get('completed', False)}")
                        print(f"    - Estado: {step.get('status', 'unknown')}")
                    
                    # Verificar si el progreso avanzó
                    active_steps = [s for s in final_steps if s.get('active')]
                    completed_steps = [s for s in final_steps if s.get('completed')]
                    
                    print(f"\n📊 ANÁLISIS DEL PROGRESO:")
                    print(f"   Pasos activos: {len(active_steps)}")
                    print(f"   Pasos completados: {len(completed_steps)}")
                    
                    if len(completed_steps) > 0:
                        print("✅ ¡PROGRESO DETECTADO! Los pasos se están completando")
                        if len(active_steps) > 0:
                            active_step = active_steps[0]
                            print(f"   Paso activo actual: {active_step.get('title')}")
                            print(f"   ID del paso activo: {active_step.get('id')}")
                        return True
                    else:
                        print("❌ NO HAY PROGRESO - Los pasos no se están marcando como completados")
                        return False
            else:
                print(f"❌ Error ejecutando primer paso: {exec_response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO COMPLETO DEL PROBLEMA DE PLAN ACTIVO")
    print("=" * 80)
    
    # Verificar backend disponible
    try:
        health_response = requests.get(f"{BACKEND_URL}/api/health")
        if health_response.status_code == 200:
            print("✅ Backend disponible")
        else:
            print(f"❌ Backend no responde: {health_response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ Error conectando al backend: {e}")
        exit(1)
    
    # Ejecutar diagnósticos
    plan_ok = test_plan_progression()
    
    print("\n" + "=" * 80)
    print("📊 RESULTADOS DEL DIAGNÓSTICO:")
    print("=" * 80)
    
    if plan_ok:
        print("✅ DIAGNÓSTICO EXITOSO: El plan progresa correctamente")
        print("   El problema puede estar en el frontend no actualizando la UI")
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("   1. Verificar eventos WebSocket en el navegador")
        print("   2. Comprobar que el TaskView recibe las actualizaciones")
        print("   3. Revisar que el estado del plan se actualiza en React")
    else:
        print("❌ PROBLEMA CONFIRMADO: El plan no progresa en el backend")
        print("\n🔧 ACCIONES REQUERIDAS:")
        print("   1. Revisar lógica de actualización del plan")
        print("   2. Verificar eventos WebSocket")
        print("   3. Corregir estado inicial del primer paso")