#!/usr/bin/env python3
"""
🎯 TEST COMPLETO DEL FIX DEL PLAN ACTIVO
Verificación final de que el problema está resuelto
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8001"

def test_full_plan_progression():
    """Test completo de progresión del plan paso a paso"""
    print("🎯 Test completo de progresión del plan...")
    
    task_message = "Analiza los beneficios del yoga para la salud mental"
    
    try:
        # 1. Crear tarea
        response = requests.post(f"{BACKEND_URL}/api/agent/chat", json={
            "message": task_message,
            "task_id": f"full_test_{int(time.time())}"
        })
        
        if response.status_code != 200:
            print(f"❌ Error creando tarea: {response.status_code}")
            return False
        
        result = response.json()
        task_id = result.get('task_id')
        print(f"✅ Tarea creada: {task_id}")
        
        # 2. Esperar plan
        time.sleep(5)
        
        # 3. Obtener plan inicial
        plan_response = requests.get(f"{BACKEND_URL}/api/agent/get-task-plan/{task_id}")
        if plan_response.status_code != 200:
            print(f"❌ Error obteniendo plan: {plan_response.status_code}")
            return False
        
        plan_data = plan_response.json()
        steps = plan_data.get('plan', [])
        print(f"📋 Plan con {len(steps)} pasos generado")
        
        # 4. Ejecutar cada paso y verificar progresión
        for i, step in enumerate(steps):
            step_id = step.get('id')
            step_title = step.get('title', f'Paso {i+1}')
            
            print(f"\n🔄 EJECUTANDO PASO {i+1}: {step_title}")
            
            # Verificar estado antes de ejecutar
            pre_plan_response = requests.get(f"{BACKEND_URL}/api/agent/get-task-plan/{task_id}")
            if pre_plan_response.status_code == 200:
                pre_plan = pre_plan_response.json().get('plan', [])
                active_steps_before = [s for s in pre_plan if s.get('active')]
                completed_steps_before = [s for s in pre_plan if s.get('completed')]
                
                print(f"   📊 Estado ANTES - Activos: {len(active_steps_before)}, Completados: {len(completed_steps_before)}")
                
                if active_steps_before:
                    print(f"   🔵 Paso activo actual: {active_steps_before[0].get('title')}")
            
            # Ejecutar paso
            exec_response = requests.post(f"{BACKEND_URL}/api/agent/execute-step-detailed/{task_id}/{step_id}")
            
            if exec_response.status_code == 200:
                exec_result = exec_response.json()
                print(f"   ✅ Paso {i+1} ejecutado - Success: {exec_result.get('success')}")
                
                # Esperar un poco para procesamiento
                time.sleep(2)
                
                # Verificar estado después de ejecutar
                post_plan_response = requests.get(f"{BACKEND_URL}/api/agent/get-task-plan/{task_id}")
                if post_plan_response.status_code == 200:
                    post_plan = post_plan_response.json().get('plan', [])
                    active_steps_after = [s for s in post_plan if s.get('active')]
                    completed_steps_after = [s for s in post_plan if s.get('completed')]
                    
                    print(f"   📊 Estado DESPUÉS - Activos: {len(active_steps_after)}, Completados: {len(completed_steps_after)}")
                    
                    # Verificar progresión esperada
                    expected_completed = i + 1
                    actual_completed = len(completed_steps_after)
                    
                    if actual_completed == expected_completed:
                        print(f"   ✅ PROGRESIÓN CORRECTA - {actual_completed} pasos completados como esperado")
                        
                        # Verificar que el siguiente paso esté activo (si no es el último)
                        if i + 1 < len(steps):
                            if active_steps_after and active_steps_after[0].get('id') == steps[i + 1].get('id'):
                                print(f"   ✅ SIGUIENTE PASO ACTIVADO: {active_steps_after[0].get('title')}")
                            else:
                                print(f"   ❌ ERROR: El siguiente paso no está activo")
                                if active_steps_after:
                                    print(f"      Paso activo actual: {active_steps_after[0].get('title')}")
                                    print(f"      Paso esperado: {steps[i + 1].get('title')}")
                                else:
                                    print(f"      No hay pasos activos")
                                return False
                        else:
                            # Es el último paso, no debería haber pasos activos
                            if not active_steps_after:
                                print(f"   ✅ ÚLTIMO PASO - No hay más pasos activos (correcto)")
                            else:
                                print(f"   ⚠️ Último paso pero hay pasos activos: {[s.get('title') for s in active_steps_after]}")
                    else:
                        print(f"   ❌ ERROR EN PROGRESIÓN - Esperados: {expected_completed}, Actuales: {actual_completed}")
                        return False
                else:
                    print(f"   ❌ Error obteniendo plan después de ejecución")
                    return False
            else:
                print(f"   ❌ Error ejecutando paso {i+1}: {exec_response.status_code}")
                return False
        
        # 5. Verificación final
        print(f"\n📊 VERIFICACIÓN FINAL:")
        final_plan_response = requests.get(f"{BACKEND_URL}/api/agent/get-task-plan/{task_id}")
        if final_plan_response.status_code == 200:
            final_plan = final_plan_response.json().get('plan', [])
            all_completed = all(s.get('completed') for s in final_plan)
            any_active = any(s.get('active') for s in final_plan)
            
            print(f"   Total pasos: {len(final_plan)}")
            print(f"   Todos completados: {all_completed}")
            print(f"   Pasos activos: {any_active}")
            
            if all_completed and not any_active:
                print("   🎉 ¡ÉXITO TOTAL! Todos los pasos completados correctamente")
                return True
            else:
                print("   ⚠️ Estado final no es el esperado")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎯 TEST COMPLETO DEL FIX DEL PLAN ACTIVO")
    print("=" * 80)
    
    # Verificar backend
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
    
    # Ejecutar test
    success = test_full_plan_progression()
    
    print("\n" + "=" * 80)
    print("📊 RESULTADOS FINALES:")
    print("=" * 80)
    
    if success:
        print("🎉 ¡FIX EXITOSO!")
        print("✅ El plan progresa correctamente paso a paso")
        print("✅ Los pasos se activan automáticamente")
        print("✅ El backend funciona perfectamente")
        print("\n🔧 PARA EL FRONTEND:")
        print("   El problema está resuelto en el backend.")
        print("   Si el frontend no muestra los cambios, verificar:")
        print("   1. Que esté conectado a WebSocket")
        print("   2. Que procese los eventos step_started/step_completed")
        print("   3. Que actualice el estado del plan en React")
    else:
        print("❌ FIX FALLÓ")
        print("🔧 Se requiere más trabajo en el backend")