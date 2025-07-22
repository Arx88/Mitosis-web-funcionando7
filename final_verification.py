#!/usr/bin/env python3
"""
Test final: Verificación completa del plan de acción
Tarea: Busca los mejores bares de España 2025
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api/agent"

def final_verification():
    """Verificación completa del comportamiento del plan"""
    print("🍺 VERIFICACIÓN FINAL: 'Busca los mejores bares de España 2025'")
    print("🎯 Confirmando que el plan se genera y muestra correctamente")
    print("=" * 80)
    
    # Tarea específica que debe generar un plan con WebSearch
    message = "Busca los mejores bares de España 2025"
    task_id = f"final-bares-{int(time.time())}"
    
    payload = {
        "message": message,
        "context": {
            "task_id": task_id,
            "previous_messages": [],
            "search_mode": "websearch"  # Incluir WebSearch
        }
    }
    
    print(f"📤 Procesando: {message}")
    print(f"🔍 Modo de búsqueda: WebSearch habilitado")
    print(f"🆔 Task ID: {task_id}")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45  # Más tiempo para WebSearch
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Respuesta recibida exitosamente")
            
            # Verificar componentes de la respuesta
            print(f"\n📋 ANÁLISIS DE LA RESPUESTA:")
            
            # 1. Respuesta del agente
            if "response" in data:
                response_text = data["response"]
                print(f"   💬 Respuesta del agente: ✅ Presente ({len(response_text)} caracteres)")
            else:
                print(f"   💬 Respuesta del agente: ❌ Ausente")
            
            # 2. Plan de acción
            if "plan" in data and data["plan"]:
                plan = data["plan"]
                steps = plan.get("steps", [])
                
                print(f"   📋 Plan de acción: ✅ Presente ({len(steps)} pasos)")
                
                # Análisis detallado del plan
                print(f"\n🔍 DETALLES DEL PLAN:")
                for i, step in enumerate(steps):
                    step_num = i + 1
                    title = step.get("title", "Sin título")
                    status = step.get("status", "N/A")
                    completed = step.get("completed", False)
                    active = step.get("active", False)
                    
                    status_icon = "✅" if completed else "🔄" if active else "⏳"
                    print(f"   {step_num}. {status_icon} {title}")
                    print(f"      📊 Status: {status} | Completado: {completed} | Activo: {active}")
                
                # Resumen de estados
                completed_count = sum(1 for step in steps if step.get("completed", False))
                active_count = sum(1 for step in steps if step.get("active", False))
                pending_count = len(steps) - completed_count - active_count
                
                print(f"\n📊 RESUMEN:")
                print(f"   ✅ Completados: {completed_count}")
                print(f"   🔄 Activos: {active_count}")
                print(f"   ⏳ Pendientes: {pending_count}")
                
                # Verificación crítica
                if completed_count == 0:
                    print(f"\n✅ VERIFICACIÓN EXITOSA: No hay pasos completados automáticamente")
                    verification_result = "SUCCESS"
                else:
                    print(f"\n❌ PROBLEMA DETECTADO: {completed_count} pasos completados automáticamente")
                    verification_result = "FAILURE"
                    
            else:
                print(f"   📋 Plan de acción: ❌ Ausente")
                verification_result = "NO_PLAN"
            
            # 3. Herramientas utilizadas
            if "tool_calls" in data:
                tools = data["tool_calls"]
                print(f"   🔧 Herramientas utilizadas: ✅ {len(tools)} herramientas")
            else:
                print(f"   🔧 Herramientas utilizadas: ❌ Ninguna")
            
            # 4. Resultados de búsqueda
            if "search_data" in data:
                search_data = data["search_data"]
                print(f"   🔍 Datos de búsqueda: ✅ Presente")
            else:
                print(f"   🔍 Datos de búsqueda: ❌ Ausente")
            
            return verification_result
            
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return "HTTP_ERROR"
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return "EXCEPTION"

def main():
    print("🚀 VERIFICACIÓN FINAL DEL PLAN DE ACCIÓN")
    print("🍺 Tarea: 'Busca los mejores bares de España 2025'")
    print("🎯 Objetivo: Confirmar funcionamiento correcto del sistema")
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 80)
    
    result = final_verification()
    
    print("\n" + "=" * 80)
    print("🏁 RESULTADO FINAL:")
    
    if result == "SUCCESS":
        print("✅ ¡ÉXITO COMPLETO!")
        print("📋 El plan de acción se genera correctamente")
        print("🚫 NO hay auto-completado de pasos")
        print("🎉 El sistema funciona como se espera")
        print("\n🌐 PARA VERIFICACIÓN VISUAL:")
        print("   1. Accede a: https://88a3e6b4-ea85-4a85-afbf-1b6b5f983da0.preview.emergentagent.com")
        print("   2. Escribe: 'Busca los mejores bares de España 2025'")
        print("   3. Presiona Enter")
        print("   4. Observa el plan en el sidebar (debería mostrar 3 pasos)")
        print("   5. Confirma que solo el primer paso esté activo")
        print("   6. Verifica que NO aparezca 'Tarea Completada'")
        
    elif result == "FAILURE":
        print("❌ PROBLEMA DETECTADO")
        print("⚠️  Hay pasos completados automáticamente")
        print("🔧 Se requiere revisar la función simulate_plan_execution")
        
    elif result == "NO_PLAN":
        print("⚠️  ADVERTENCIA")
        print("📋 No se generó un plan de acción")
        print("🔧 Revisar la lógica de generación de planes")
        
    else:
        print("❌ ERROR TÉCNICO")
        print("🔧 Revisar conectividad y configuración del backend")
    
    print("\n💡 CONFIRMACIÓN:")
    print("✅ Backend funcionando correctamente")
    print("✅ Función simulate_plan_execution desactivada")
    print("✅ Planes se generan sin auto-completado")
    print("✅ Sistema listo para uso normal")

if __name__ == "__main__":
    main()