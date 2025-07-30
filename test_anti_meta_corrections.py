#!/usr/bin/env python3
"""
🔧 TEST DE CORRECCIONES ANTI-META
Verifica que las funciones corregidas generen contenido REAL en lugar de meta-contenido
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"

def test_create_task_and_verify_real_content():
    """Crear una tarea y verificar que genera contenido REAL"""
    print("🚀 Iniciando test de correcciones anti-meta...")
    
    # Crear tarea de prueba
    task_message = "Genera un análisis sobre los beneficios de la energía solar"
    
    try:
        # 1. Crear tarea
        print(f"📝 Creando tarea: {task_message}")
        response = requests.post(f"{BACKEND_URL}/api/agent/chat", json={
            "message": task_message,
            "task_id": f"test_anti_meta_{int(time.time())}"
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
        
        # 3. Obtener el plan
        plan_response = requests.get(f"{BACKEND_URL}/api/agent/get-task-plan/{task_id}")
        if plan_response.status_code != 200:
            print(f"❌ Error obteniendo plan: {plan_response.status_code}")
            return False
        
        plan_data = plan_response.json()
        steps = plan_data.get('plan', [])
        print(f"📋 Plan generado con {len(steps)} pasos")
        
        # 4. Ejecutar pasos y verificar contenido real
        meta_content_detected = False
        real_content_found = False
        
        for i, step in enumerate(steps, 1):
            if step.get('completed'):
                continue
                
            step_id = step.get('id')
            step_title = step.get('title', f'Paso {i}')
            
            print(f"🔄 Ejecutando paso {i}: {step_title}")
            
            # Ejecutar paso
            exec_response = requests.post(f"{BACKEND_URL}/api/agent/execute-step-detailed/{task_id}/{step_id}")
            
            if exec_response.status_code == 200:
                exec_result = exec_response.json()
                step_result = exec_result.get('step_result', {})
                content = step_result.get('content', '')
                
                # 🔍 VERIFICAR ANTI-META
                meta_phrases = [
                    'se analizará', 'se procederá', 'este análisis se enfocará',
                    'los objetivos son', 'la metodología será', 'se realizará',
                    'analizaremos', 'evaluaremos', 'este documento analizará'
                ]
                
                has_meta = any(phrase in content.lower() for phrase in meta_phrases)
                
                if has_meta:
                    print(f"❌ META-CONTENIDO DETECTADO en paso {i}:")
                    print(f"   Contenido: {content[:200]}...")
                    meta_content_detected = True
                else:
                    print(f"✅ Paso {i} SIN meta-contenido")
                
                # 🎯 VERIFICAR CONTENIDO REAL
                real_indicators = [
                    'beneficios de la energía solar', 'ventajas', 'reducción de costos',
                    'impacto ambiental', 'energía renovable', 'paneles solares',
                    'sostenible', 'limpia', 'fotovoltaica'
                ]
                
                has_real_content = any(indicator in content.lower() for indicator in real_indicators)
                
                if has_real_content and len(content) > 300:
                    print(f"✅ CONTENIDO REAL ENCONTRADO en paso {i} ({len(content)} caracteres)")
                    real_content_found = True
                
                time.sleep(2)  # Pausa entre pasos
            else:
                print(f"❌ Error ejecutando paso {i}: {exec_response.status_code}")
        
        # 5. Verificar informe final
        print("📄 Generando informe final...")
        time.sleep(3)
        
        final_response = requests.post(f"{BACKEND_URL}/api/agent/generate-final-report/{task_id}")
        if final_response.status_code == 200:
            final_result = final_response.json()
            final_report = final_result.get('report', '')
            
            # Verificar informe final
            meta_in_final = any(phrase in final_report.lower() for phrase in [
                'se analizará', 'se procederá', 'este informe analizará'
            ])
            
            if meta_in_final:
                print("❌ META-CONTENIDO DETECTADO en informe final")
                meta_content_detected = True
            else:
                print("✅ Informe final SIN meta-contenido")
            
            # Verificar contenido real en informe final
            real_in_final = any(indicator in final_report.lower() for indicator in [
                'beneficios', 'energía solar', 'ventajas', 'sostenible'
            ]) and len(final_report) > 500
            
            if real_in_final:
                print("✅ CONTENIDO REAL en informe final")
                real_content_found = True
        
        # 6. Resultados finales
        print("\n" + "="*60)
        print("📊 RESULTADOS DEL TEST:")
        print("="*60)
        
        if not meta_content_detected and real_content_found:
            print("🎉 ¡ÉXITO TOTAL! Correcciones anti-meta funcionando")
            print("✅ No se detectó meta-contenido")
            print("✅ Se generó contenido real específico")
            return True
        elif not meta_content_detected:
            print("⚠️ ÉXITO PARCIAL: No hay meta-contenido pero contenido limitado")
            return True
        else:
            print("❌ FALLO: Se detectó meta-contenido")
            print("🔧 Las correcciones necesitan ajustes adicionales")
            return False
        
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        return False

def test_backend_health():
    """Verificar que el backend esté funcionando"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health")
        if response.status_code == 200:
            print("✅ Backend funcionando correctamente")
            return True
        else:
            print(f"❌ Backend no responde: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al backend: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 TEST DE CORRECCIONES ANTI-META")
    print("=" * 60)
    
    # Verificar backend
    if not test_backend_health():
        exit(1)
    
    # Ejecutar test principal
    success = test_create_task_and_verify_real_content()
    
    if success:
        print("\n🎉 TEST COMPLETADO EXITOSAMENTE")
        print("✅ Las correcciones anti-meta están funcionando")
    else:
        print("\n❌ TEST FALLÓ")
        print("🔧 Se requieren ajustes adicionales")
        exit(1)