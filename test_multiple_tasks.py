#!/usr/bin/env python3
"""
Test para verificar que el plan aparezca en múltiples tareas nuevas
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api/agent"

def test_multiple_tasks():
    """Prueba múltiples tareas para verificar que el plan aparece en cada una"""
    print("🧪 PROBANDO MÚLTIPLES TAREAS CON PLAN DE ACCIÓN")
    print("=" * 70)
    
    tasks = [
        "Busca los mejores bares de España 2025",
        "Analiza las tendencias de marketing digital",
        "Investiga sobre inteligencia artificial",
        "Crea un informe sobre blockchain",
        "Planifica un viaje a París"
    ]
    
    for i, task in enumerate(tasks):
        print(f"\n📋 TAREA {i+1}: {task}")
        print("-" * 50)
        
        task_id = f"test-task-{i+1}-{int(time.time())}"
        
        payload = {
            "message": task,
            "context": {
                "task_id": task_id,
                "previous_messages": [],
                "search_mode": None
            }
        }
        
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
                
                # Verificar si hay un plan
                if "plan" in data and data["plan"]:
                    plan = data["plan"]
                    steps = plan.get("steps", [])
                    
                    print(f"✅ Plan generado: {len(steps)} pasos")
                    
                    # Mostrar detalles del plan
                    for j, step in enumerate(steps):
                        title = step.get("title", "Sin título")
                        elapsed_time = step.get("elapsed_time", "N/A")
                        active = step.get("active", False)
                        
                        status_icon = "🔄" if active else "⏳"
                        print(f"   {j+1}. {status_icon} {title}")
                        if elapsed_time and elapsed_time != "N/A":
                            print(f"      ⏱️  {elapsed_time}")
                    
                    print(f"✅ ÉXITO: Plan aparece correctamente")
                else:
                    print(f"❌ FALLO: No se generó plan")
                    
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"💥 Error: {str(e)}")
            
        # Esperar un poco entre tareas
        time.sleep(1)
    
    print("\n" + "=" * 70)
    print("🏁 RESULTADO: Verificación de múltiples tareas completada")

def main():
    print("🚀 VERIFICACIÓN DE PLANES EN MÚLTIPLES TAREAS")
    print("🎯 Objetivo: Confirmar que el plan aparece en TODAS las tareas nuevas")
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_multiple_tasks()

if __name__ == "__main__":
    main()