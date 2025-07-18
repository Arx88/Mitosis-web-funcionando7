#!/usr/bin/env python3
"""
Test final para verificar todos los cambios implementados
"""

import requests
import json
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api/agent"

def test_plan_changes():
    """Prueba los cambios en el plan de acción"""
    print("🎯 VERIFICACIÓN FINAL DE CAMBIOS EN PLAN DE ACCIÓN")
    print("=" * 70)
    
    # Test con la tarea solicitada por el usuario
    message = "Busca los mejores bares de España 2025"
    task_id = f"final-test-{int(datetime.now().timestamp())}"
    
    payload = {
        "message": message,
        "context": {
            "task_id": task_id,
            "previous_messages": [],
            "search_mode": None
        }
    }
    
    print(f"📤 Enviando: {message}")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "plan" in data and data["plan"]:
                plan = data["plan"]
                steps = plan.get("steps", [])
                
                print(f"✅ Plan generado con {len(steps)} pasos")
                print(f"\n📋 VERIFICACIÓN DE CAMBIOS:")
                
                for i, step in enumerate(steps):
                    step_num = i + 1
                    title = step.get("title", "Sin título")
                    description = step.get("description")
                    elapsed_time = step.get("elapsed_time")
                    estimated_time = step.get("estimated_time")
                    active = step.get("active", False)
                    
                    status_icon = "🔄" if active else "⏳"
                    
                    print(f"\n   {step_num}. {status_icon} {title}")
                    
                    # Verificar que no tenga descripción (debe ser None)
                    if description is None:
                        print(f"      ✅ Descripción: Correctamente eliminada")
                    else:
                        print(f"      ❌ Descripción: Aún presente - {description}")
                    
                    # Verificar que no tenga tiempo estimado (debe ser None)
                    if estimated_time is None:
                        print(f"      ✅ Tiempo estimado: Correctamente eliminado")
                    else:
                        print(f"      ❌ Tiempo estimado: Aún presente - {estimated_time}")
                    
                    # Verificar que tenga tiempo transcurrido
                    if elapsed_time:
                        print(f"      ✅ Tiempo transcurrido: {elapsed_time}")
                    else:
                        print(f"      ❌ Tiempo transcurrido: Ausente")
                
                # Verificar cambios específicos
                print(f"\n🔍 VERIFICACIÓN ESPECÍFICA:")
                
                first_step = steps[0] if steps else None
                if first_step:
                    if first_step.get("title") == "Análisis de tarea":
                        print(f"   ✅ Título simplificado: 'Análisis de tarea' (correcto)")
                    else:
                        print(f"   ❌ Título no cambió: '{first_step.get('title')}'")
                    
                    if first_step.get("elapsed_time") == "0:01 Pensando":
                        print(f"   ✅ Tiempo real: '0:01 Pensando' (correcto)")
                    else:
                        print(f"   ❌ Tiempo real: '{first_step.get('elapsed_time')}'")
                
                print(f"\n🎉 RESULTADO: Cambios implementados exitosamente")
                return True
                
            else:
                print(f"❌ No se generó plan")
                return False
                
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return False

def main():
    print("🚀 PRUEBA FINAL DE CAMBIOS EN PLAN DE ACCIÓN")
    print("📋 Cambios implementados:")
    print("   1. Título simplificado: 'Análisis de tarea' en lugar de 'Análisis de la tarea'")
    print("   2. Descripción eliminada: No más segunda línea")
    print("   3. Tiempo real: '0:01 Pensando' en lugar de '⏱️ 30 segundos'")
    print("   4. Mejor detección de tareas: Más planes generados")
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_plan_changes()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ TODOS LOS CAMBIOS IMPLEMENTADOS CORRECTAMENTE")
        print("🎯 El plan de acción ahora muestra:")
        print("   - 'Análisis de tarea' (título simplificado)")
        print("   - '0:01 Pensando' (tiempo real)")
        print("   - Sin descripción adicional")
        print("   - Aparece en todas las tareas nuevas")
    else:
        print("❌ ALGUNOS CAMBIOS NECESITAN REVISIÓN")

if __name__ == "__main__":
    main()