#!/usr/bin/env python3
"""
Test para verificar el comportamiento del plan de ejecución
"""

import requests
import json
import time

# Configuración
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api/agent"

def test_plan_generation():
    """Prueba que se genere un plan correctamente"""
    print("🧪 Probando generación de plan...")
    
    # Crear una tarea que requiera un plan
    message = "Crear un informe sobre las tendencias de inteligencia artificial en 2025"
    
    payload = {
        "message": message,
        "context": {
            "task_id": f"test-{int(time.time())}",
            "previous_messages": [],
            "search_mode": None
        }
    }
    
    print(f"📤 Enviando mensaje: {message}")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📡 Respuesta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta recibida exitosamente")
            
            # Verificar si hay un plan
            if "plan" in data:
                plan = data["plan"]
                print(f"📋 Plan encontrado con {len(plan.get('steps', []))} pasos")
                
                # Verificar estado de los pasos
                steps = plan.get("steps", [])
                completed_steps = [step for step in steps if step.get("completed", False)]
                active_steps = [step for step in steps if step.get("active", False)]
                
                print(f"✅ Pasos completados: {len(completed_steps)}")
                print(f"🔄 Pasos activos: {len(active_steps)}")
                print(f"⏳ Pasos pendientes: {len(steps) - len(completed_steps)}")
                
                # Verificar si se están marcando automáticamente como completados
                if len(completed_steps) > 0:
                    print(f"⚠️  PROBLEMA DETECTADO: {len(completed_steps)} pasos ya están marcados como completados")
                    print("🔍 Detalles de pasos completados:")
                    for i, step in enumerate(completed_steps):
                        print(f"   {i+1}. {step.get('title', 'Sin título')} - Status: {step.get('status', 'N/A')}")
                else:
                    print("✅ CORRECTO: Ningún paso está marcado como completado automáticamente")
                
                return plan
            else:
                print("❌ No se encontró un plan en la respuesta")
                return None
                
        else:
            print(f"❌ Error en la respuesta: {response.status_code}")
            print(f"📄 Contenido: {response.text}")
            
    except Exception as e:
        print(f"💥 Error durante la prueba: {str(e)}")
        return None

def test_backend_health():
    """Prueba que el backend esté funcionando"""
    print("🏥 Probando salud del backend...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend saludable: {data}")
            return True
        else:
            print(f"❌ Backend no saludable: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Error conectando al backend: {str(e)}")
        return False

def main():
    print("🚀 Iniciando pruebas del plan de ejecución...")
    print("=" * 60)
    
    # Paso 1: Verificar que el backend esté funcionando
    if not test_backend_health():
        print("❌ El backend no está funcionando. Saliendo...")
        return
    
    print("\n" + "=" * 60)
    
    # Paso 2: Probar la generación de plan
    plan = test_plan_generation()
    
    print("\n" + "=" * 60)
    
    if plan:
        print("✅ RESULTADO: El plan se generó correctamente")
        print("📋 Revisar los detalles anteriores para detectar si hay pasos completados automáticamente")
    else:
        print("❌ RESULTADO: No se pudo generar el plan")
    
    print("\n🎯 OBJETIVO: Verificar que el plan se genere sin marcar pasos como completados automáticamente")

if __name__ == "__main__":
    main()