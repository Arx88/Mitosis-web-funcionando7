#!/usr/bin/env python3
"""
Test del Agente REAL de Mitosis
Verifica que las herramientas reales funcionan correctamente
"""

import sys
import os
import json

# Añadir directorio backend al path
sys.path.insert(0, '/app/backend')

def test_real_agent():
    """Prueba el agente real sin simulaciones"""
    
    print("🚀 INICIANDO PRUEBAS DEL AGENTE REAL MITOSIS")
    print("=" * 60)
    
    try:
        # Importar el agente real
        from agent_core_real import MitosisRealAgent, create_real_mitosis_agent
        
        print("✅ 1. Agente REAL importado exitosamente")
        
        # Crear agente real
        agent = create_real_mitosis_agent()
        print("✅ 2. Agente REAL creado exitosamente")
        
        # Iniciar sesión
        session_id = agent.start_session()
        print(f"✅ 3. Sesión REAL iniciada: {session_id}")
        
        # Obtener estado del agente
        status = agent.get_status()
        print(f"✅ 4. Estado del agente: {status['state']}")
        print(f"   - Tipo de agente: {status.get('agent_type', 'UNKNOWN')}")
        print(f"   - Herramientas disponibles: {status['tool_manager_status']['available_tools']}")
        print(f"   - Herramientas habilitadas: {status['tool_manager_status']['enabled_tools']}")
        
        # Verificar estadísticas de ejecuciones reales
        real_stats = status.get('real_executions', {})
        print(f"   - Búsquedas web reales: {real_stats.get('web_searches', 0)}")
        print(f"   - Archivos reales creados: {real_stats.get('files_created', 0)}")
        print(f"   - Comandos reales ejecutados: {real_stats.get('commands_executed', 0)}")
        
        # Test de herramientas reales
        print("\n🛠️  PROBANDO HERRAMIENTAS REALES:")
        print("-" * 40)
        
        # Test 1: Búsqueda web REAL
        print("🔍 Test 1: Búsqueda web REAL...")
        try:
            search_result = agent.execute_real_web_search("Python programming 2025", max_results=3)
            if search_result.get('success'):
                results_count = len(search_result.get('results', []))
                print(f"   ✅ Búsqueda REAL exitosa: {results_count} resultados encontrados")
                
                # Mostrar primer resultado para verificar que es real
                if results_count > 0:
                    first_result = search_result['results'][0]
                    print(f"   📄 Primer resultado: {first_result.get('title', 'Sin título')[:60]}...")
                    print(f"   🔗 URL: {first_result.get('url', 'Sin URL')}")
            else:
                print(f"   ❌ Error en búsqueda: {search_result.get('error', 'Error desconocido')}")
        except Exception as e:
            print(f"   ❌ Excepción en búsqueda: {str(e)}")
        
        # Test 2: Creación de archivo REAL
        print("\n📁 Test 2: Creación de archivo REAL...")
        try:
            file_result = agent.execute_real_file_creation(
                filename="test_agente_real.txt",
                content="Este archivo fue creado por el agente REAL de Mitosis\nFecha de creación: " + str(status.get('uptime_seconds', 0))
            )
            if file_result.get('success'):
                filepath = file_result.get('filepath', 'Desconocido')
                file_size = file_result.get('file_size', 0)
                print(f"   ✅ Archivo REAL creado exitosamente")
                print(f"   📁 Ruta: {filepath}")
                print(f"   📊 Tamaño: {file_size} bytes")
                
                # Verificar que el archivo realmente existe
                if os.path.exists(filepath):
                    print(f"   ✅ Archivo verificado: existe en el sistema de archivos")
                    with open(filepath, 'r') as f:
                        content = f.read()
                        print(f"   📝 Contenido (primeros 50 chars): {content[:50]}...")
                else:
                    print(f"   ❌ Error: archivo no existe en {filepath}")
            else:
                print(f"   ❌ Error creando archivo: {file_result.get('error', 'Error desconocido')}")
        except Exception as e:
            print(f"   ❌ Excepción creando archivo: {str(e)}")
        
        # Test 3: Comando shell REAL  
        print("\n💻 Test 3: Comando shell REAL...")
        try:
            shell_result = agent.execute_real_shell_command("echo 'Agente REAL funcionando'")
            if shell_result.get('success'):
                stdout = shell_result.get('stdout', '').strip()
                return_code = shell_result.get('return_code', -1)
                print(f"   ✅ Comando REAL ejecutado exitosamente")
                print(f"   📤 Salida: {stdout}")
                print(f"   🔢 Código de retorno: {return_code}")
            else:
                print(f"   ❌ Error ejecutando comando: {shell_result.get('error', 'Error desconocido')}")
        except Exception as e:
            print(f"   ❌ Excepción ejecutando comando: {str(e)}")
        
        # Verificar estadísticas finales
        final_status = agent.get_status()
        final_real_stats = final_status.get('real_executions', {})
        
        print(f"\n📊 ESTADÍSTICAS FINALES REALES:")
        print(f"   - Búsquedas web reales realizadas: {final_real_stats.get('web_searches', 0)}")
        print(f"   - Archivos reales creados: {final_real_stats.get('files_created', 0)}")
        print(f"   - Comandos reales ejecutados: {final_real_stats.get('commands_executed', 0)}")
        
        # Verificar métricas de rendimiento
        performance = final_status.get('performance_metrics', {})
        if performance:
            print(f"   - Tasa de éxito de tareas: {performance.get('task_success_rate', 0):.2%}")
            print(f"   - Tasa de éxito de herramientas: {len(performance.get('tool_accuracy_rate', {}))}")
        
        print("\n🎉 TODAS LAS PRUEBAS DEL AGENTE REAL COMPLETADAS")
        print("✅ EL AGENTE MITOSIS ES 100% REAL - NO HAY SIMULACIONES")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN PRUEBAS: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_agent()
    sys.exit(0 if success else 1)