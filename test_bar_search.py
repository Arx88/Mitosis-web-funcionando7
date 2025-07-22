#!/usr/bin/env python3
"""
Test específico para la tarea: "Busca los mejores bares de España 2025"
Verificación visual del plan de acción
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api/agent"

def test_bar_search_task():
    """Prueba específica para la búsqueda de bares"""
    print("🍺 Procesando tarea: 'Busca los mejores bares de España 2025'")
    print("=" * 70)
    
    # Tarea específica del usuario
    message = "Busca los mejores bares de España 2025"
    task_id = f"bares-espana-{int(time.time())}"
    
    payload = {
        "message": message,
        "context": {
            "task_id": task_id,
            "previous_messages": [],
            "search_mode": None
        }
    }
    
    print(f"📤 Enviando mensaje: {message}")
    print(f"🆔 Task ID: {task_id}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        print("\n🔄 Enviando request al backend...")
        response = requests.post(
            f"{API_BASE}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta recibida exitosamente")
            
            # Verificar respuesta del agente
            if "response" in data:
                response_text = data["response"]
                print(f"💬 Respuesta del agente: {response_text[:200]}...")
            
            # Verificar si hay un plan
            if "plan" in data and data["plan"]:
                plan = data["plan"]
                print(f"\n📋 ¡PLAN DE ACCIÓN GENERADO!")
                print(f"📊 Detalles del plan:")
                print(f"   - Título: {plan.get('title', 'N/A')}")
                print(f"   - Complejidad: {plan.get('complexity', 'N/A')}")
                print(f"   - Tiempo estimado: {plan.get('estimated_time', 'N/A')} segundos")
                print(f"   - Probabilidad de éxito: {plan.get('success_probability', 'N/A')}%")
                
                # Verificar pasos del plan
                steps = plan.get("steps", [])
                print(f"\n🔍 ANÁLISIS DE PASOS DEL PLAN:")
                print(f"   - Total de pasos: {len(steps)}")
                
                completed_steps = []
                active_steps = []
                pending_steps = []
                
                for i, step in enumerate(steps):
                    step_num = i + 1
                    title = step.get("title", "Sin título")
                    status = step.get("status", "N/A")
                    completed = step.get("completed", False)
                    active = step.get("active", False)
                    
                    print(f"   {step_num}. {title}")
                    print(f"      📊 Status: {status}")
                    print(f"      ✅ Completado: {completed}")
                    print(f"      🔄 Activo: {active}")
                    
                    if completed:
                        completed_steps.append(step)
                    elif active:
                        active_steps.append(step)
                    else:
                        pending_steps.append(step)
                
                print(f"\n📈 RESUMEN DEL ESTADO:")
                print(f"   ✅ Pasos completados: {len(completed_steps)}")
                print(f"   🔄 Pasos activos: {len(active_steps)}")
                print(f"   ⏳ Pasos pendientes: {len(pending_steps)}")
                
                # Verificar si hay auto-completado problemático
                if len(completed_steps) > 0:
                    print(f"\n⚠️  ATENCIÓN: Se detectaron {len(completed_steps)} pasos completados automáticamente")
                    print(f"📋 Pasos completados:")
                    for step in completed_steps:
                        print(f"   - {step.get('title', 'N/A')}")
                    return "PROBLEMA_DETECTADO"
                else:
                    print(f"\n✅ CORRECTO: No hay pasos completados automáticamente")
                    return "FUNCIONANDO_CORRECTAMENTE"
                    
            else:
                print(f"❌ No se encontró un plan en la respuesta")
                print(f"📄 Claves disponibles: {list(data.keys())}")
                return "SIN_PLAN"
                
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return "ERROR_HTTP"
            
    except Exception as e:
        print(f"💥 Error durante la prueba: {str(e)}")
        return "ERROR_EXCEPCION"

def main():
    print("🚀 VERIFICACIÓN VISUAL DEL PLAN DE ACCIÓN")
    print("🍺 Tarea: Busca los mejores bares de España 2025")
    print("🎯 Objetivo: Verificar que el plan se genere sin auto-completado")
    print("\n" + "=" * 70)
    
    # Ejecutar test
    result = test_bar_search_task()
    
    print("\n" + "=" * 70)
    print("🎯 RESULTADO FINAL:")
    
    if result == "FUNCIONANDO_CORRECTAMENTE":
        print("✅ ¡ÉXITO! El plan de acción se genera correctamente")
        print("📋 Los pasos no se marcan como completados automáticamente")
        print("🎉 El sistema está funcionando como se espera")
    elif result == "PROBLEMA_DETECTADO":
        print("❌ PROBLEMA: Se detectó auto-completado de pasos")
        print("🔧 Es necesario revisar la función simulate_plan_execution")
    elif result == "SIN_PLAN":
        print("⚠️  ADVERTENCIA: No se generó un plan de acción")
        print("🔍 Verificar la lógica de generación de planes")
    else:
        print("❌ ERROR: No se pudo completar la verificación")
        print("🔧 Revisar conectividad y configuración del backend")
    
    print("\n💡 Para verificación visual completa, revisar la interfaz web:")
    print("🌐 https://929fd28d-e48b-4d30-b963-581487842c96.preview.emergentagent.com")

if __name__ == "__main__":
    main()