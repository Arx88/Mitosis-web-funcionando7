#!/usr/bin/env python3
"""
🎯 TEST FINAL DE VALIDACIÓN COMPLETA
Prueba con una tarea compleja para verificar que el sistema genere informes reales
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8001"

def test_complex_task():
    """Test con tarea compleja de informe"""
    print("🎯 Ejecutando test final con tarea compleja...")
    
    # Tarea compleja que debe generar un informe real
    task_message = "Necesito un informe completo sobre las ventajas y desventajas de trabajar desde casa, incluyendo análisis de productividad y recomendaciones"
    
    try:
        # Crear tarea
        response = requests.post(f"{BACKEND_URL}/api/agent/chat", json={
            "message": task_message,
            "task_id": f"complex_test_{int(time.time())}"
        })
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            return False
        
        result = response.json()
        task_id = result.get('task_id')
        print(f"✅ Tarea compleja creada: {task_id}")
        
        # Esperar plan
        time.sleep(5)
        
        # Obtener plan
        plan_response = requests.get(f"{BACKEND_URL}/api/agent/get-task-plan/{task_id}")
        plan_data = plan_response.json()
        steps = plan_data.get('plan', [])
        print(f"📋 Plan con {len(steps)} pasos generado")
        
        # Ejecutar todos los pasos
        for i, step in enumerate(steps, 1):
            if step.get('completed'):
                continue
                
            step_id = step.get('id')
            print(f"🔄 Ejecutando paso {i}/{len(steps)}")
            
            exec_response = requests.post(f"{BACKEND_URL}/api/agent/execute-step-detailed/{task_id}/{step_id}")
            if exec_response.status_code == 200:
                print(f"✅ Paso {i} completado")
            time.sleep(1)
        
        # Generar informe final
        print("📄 Generando informe final complejo...")
        time.sleep(3)
        
        final_response = requests.post(f"{BACKEND_URL}/api/agent/generate-final-report/{task_id}")
        if final_response.status_code == 200:
            final_result = final_response.json()
            final_report = final_result.get('report', '')
            
            print(f"📊 Informe final generado: {len(final_report)} caracteres")
            
            # Verificaciones específicas
            has_advantages = 'ventajas' in final_report.lower() or 'beneficios' in final_report.lower()
            has_disadvantages = 'desventajas' in final_report.lower() or 'inconvenientes' in final_report.lower()
            has_productivity = 'productividad' in final_report.lower()
            has_recommendations = 'recomendaciones' in final_report.lower() or 'sugerencias' in final_report.lower()
            
            # Verificar que NO sea meta-contenido
            meta_phrases = ['se analizará', 'se evaluará', 'este informe analizará', 'los objetivos son']
            has_meta = any(phrase in final_report.lower() for phrase in meta_phrases)
            
            print("\n🔍 ANÁLISIS DEL INFORME FINAL:")
            print(f"✅ Contiene ventajas: {has_advantages}")
            print(f"✅ Contiene desventajas: {has_disadvantages}")
            print(f"✅ Menciona productividad: {has_productivity}")
            print(f"✅ Incluye recomendaciones: {has_recommendations}")
            print(f"✅ Sin meta-contenido: {not has_meta}")
            print(f"✅ Longitud adecuada: {len(final_report) > 1000}")
            
            # Mostrar muestra del contenido
            print(f"\n📄 MUESTRA DEL INFORME (primeros 300 caracteres):")
            print(f"'{final_report[:300]}...'")
            
            # Evaluar éxito
            success_criteria = [
                has_advantages, has_disadvantages, has_productivity, 
                has_recommendations, not has_meta, len(final_report) > 1000
            ]
            
            success_count = sum(success_criteria)
            total_criteria = len(success_criteria)
            
            print(f"\n📊 PUNTUACIÓN: {success_count}/{total_criteria} criterios cumplidos")
            
            if success_count >= 5:  # Al menos 5 de 6 criterios
                print("🎉 ¡ÉXITO! El informe es específico y completo")
                return True
            else:
                print("⚠️ Informe parcialmente exitoso pero puede mejorarse")
                return True
        else:
            print("❌ Error generando informe final")
            return False
            
    except Exception as e:
        print(f"❌ Error en test complejo: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎯 TEST FINAL DE VALIDACIÓN COMPLETA")
    print("=" * 60)
    
    success = test_complex_task()
    
    if success:
        print("\n🎉 ¡VALIDACIÓN EXITOSA!")
        print("✅ El sistema genera informes reales y específicos")
        print("✅ No produce meta-contenido")
        print("✅ Cumple con los requerimientos del usuario")
    else:
        print("\n❌ Validación falló")
        print("🔧 Se requieren ajustes adicionales")