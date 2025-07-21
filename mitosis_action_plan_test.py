#!/usr/bin/env python3
"""
Prueba Integral del Sistema de Plan de Acción de Mitosis Mejorado
Enfoque en generación de planes específicos y actualización de progreso
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuración
BACKEND_URL = "https://15ffcb16-6c55-47fc-8da7-e48ddd5d43ae.preview.emergentagent.com/api/agent"

class MitosisActionPlanTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mitosis-Action-Plan-Tester/1.0'
        })
    
    def log_test(self, test_name, success, duration, details):
        """Registra resultado de una prueba"""
        result = {
            'test': test_name,
            'success': success,
            'duration': f"{duration:.2f}s",
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} ({duration:.2f}s) - {test_name}")
        if not success:
            print(f"   Error: {details}")
        else:
            print(f"   Details: {details}")
        print()
    
    def test_generate_plan_endpoint(self):
        """1. Prueba generación de planes mejorados con diferentes tipos de tareas"""
        print("🧪 TESTING: Generación de Planes Mejorados")
        print("=" * 60)
        
        # Casos de prueba para diferentes tipos de tareas
        test_cases = [
            {
                'name': 'Tarea de Investigación',
                'task_title': 'Analizar tendencias de IA en 2025',
                'expected_steps': 5,
                'expected_keywords': ['investigación', 'recopilar', 'analizar', 'conclusiones']
            },
            {
                'name': 'Tarea de Desarrollo',
                'task_title': 'Crear un script de automatización',
                'expected_steps': 5,
                'expected_keywords': ['planificar', 'desarrollar', 'integrar', 'probar', 'finalizar']
            },
            {
                'name': 'Tarea de Búsqueda Simple',
                'task_title': 'Buscar información sobre Python',
                'expected_steps': 3,
                'expected_keywords': ['procesar', 'buscar', 'presentar']
            },
            {
                'name': 'WebSearch Task',
                'task_title': '[WebSearch] noticias tecnología',
                'expected_steps': 4,
                'expected_keywords': ['procesar consulta', 'buscar información', 'filtrar', 'presentar']
            },
            {
                'name': 'DeepSearch Task',
                'task_title': '[DeepResearch] aplicaciones de IA',
                'expected_steps': 4,
                'expected_keywords': ['objetivos', 'recopilar', 'analizar', 'informe']
            },
            {
                'name': 'Tarea de Comparación',
                'task_title': 'Comparar mejores prácticas en desarrollo',
                'expected_steps': 4,
                'expected_keywords': ['criterios', 'comparativos', 'diferencias', 'recomendaciones']
            }
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            
            try:
                response = self.session.post(
                    f"{self.backend_url}/generate-plan",
                    json={
                        'task_title': test_case['task_title'],
                        'context': {'test_mode': True}
                    },
                    timeout=10
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    plan = data.get('plan', [])
                    
                    # Verificar estructura del plan
                    if len(plan) >= 3 and len(plan) <= 6:
                        # Verificar que cada paso tenga la estructura correcta
                        valid_structure = all(
                            'id' in step and 'title' in step and 'completed' in step and 'active' in step
                            for step in plan
                        )
                        
                        if valid_structure:
                            # Verificar que el primer paso esté activo
                            first_step_active = plan[0].get('active', False)
                            
                            # Verificar que los pasos no estén completados inicialmente
                            no_completed_steps = all(not step.get('completed', True) for step in plan)
                            
                            if first_step_active and no_completed_steps:
                                # Verificar contenido específico del plan
                                plan_text = ' '.join([step['title'].lower() for step in plan])
                                keywords_found = sum(1 for keyword in test_case['expected_keywords'] 
                                                   if keyword in plan_text)
                                
                                if keywords_found >= 2:  # Al menos 2 keywords esperadas
                                    self.log_test(
                                        f"Generate Plan - {test_case['name']}",
                                        True,
                                        duration,
                                        f"Plan generado con {len(plan)} pasos específicos y orientados al usuario"
                                    )
                                else:
                                    self.log_test(
                                        f"Generate Plan - {test_case['name']}",
                                        False,
                                        duration,
                                        f"Plan no contiene keywords específicas esperadas. Encontradas: {keywords_found}/4"
                                    )
                            else:
                                self.log_test(
                                    f"Generate Plan - {test_case['name']}",
                                    False,
                                    duration,
                                    f"Estado inicial incorrecto: primer paso activo={first_step_active}, pasos completados={not no_completed_steps}"
                                )
                        else:
                            self.log_test(
                                f"Generate Plan - {test_case['name']}",
                                False,
                                duration,
                                "Estructura de pasos inválida - faltan campos requeridos"
                            )
                    else:
                        self.log_test(
                            f"Generate Plan - {test_case['name']}",
                            False,
                            duration,
                            f"Plan tiene {len(plan)} pasos, esperado 3-6 pasos"
                        )
                else:
                    self.log_test(
                        f"Generate Plan - {test_case['name']}",
                        False,
                        duration,
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(
                    f"Generate Plan - {test_case['name']}",
                    False,
                    duration,
                    f"Exception: {str(e)}"
                )
    
    def test_task_progress_endpoints(self):
        """2. Prueba endpoints de actualización y obtención de progreso"""
        print("🧪 TESTING: Actualización de Progreso de Tareas")
        print("=" * 60)
        
        # Generar task_id único para las pruebas
        test_task_id = str(uuid.uuid4())
        
        # Test 1: Actualizar progreso de pasos
        start_time = time.time()
        try:
            # Marcar step-1 como completado
            response = self.session.post(
                f"{self.backend_url}/update-task-progress",
                json={
                    'task_id': test_task_id,
                    'step_id': 'step-1',
                    'completed': True
                },
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('completed'):
                    self.log_test(
                        "Update Task Progress - Step 1",
                        True,
                        duration,
                        f"Paso step-1 marcado como completado para tarea {test_task_id}"
                    )
                else:
                    self.log_test(
                        "Update Task Progress - Step 1",
                        False,
                        duration,
                        f"Respuesta inválida: {data}"
                    )
            else:
                self.log_test(
                    "Update Task Progress - Step 1",
                    False,
                    duration,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(
                "Update Task Progress - Step 1",
                False,
                duration,
                f"Exception: {str(e)}"
            )
        
        # Test 2: Marcar múltiples pasos como completados
        steps_to_complete = ['step-2', 'step-3']
        for step_id in steps_to_complete:
            start_time = time.time()
            try:
                response = self.session.post(
                    f"{self.backend_url}/update-task-progress",
                    json={
                        'task_id': test_task_id,
                        'step_id': step_id,
                        'completed': True
                    },
                    timeout=10
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('completed'):
                        self.log_test(
                            f"Update Task Progress - {step_id}",
                            True,
                            duration,
                            f"Paso {step_id} marcado como completado"
                        )
                    else:
                        self.log_test(
                            f"Update Task Progress - {step_id}",
                            False,
                            duration,
                            f"Respuesta inválida: {data}"
                        )
                else:
                    self.log_test(
                        f"Update Task Progress - {step_id}",
                        False,
                        duration,
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(
                    f"Update Task Progress - {step_id}",
                    False,
                    duration,
                    f"Exception: {str(e)}"
                )
        
        # Test 3: Obtener progreso de la tarea
        start_time = time.time()
        try:
            response = self.session.get(
                f"{self.backend_url}/get-task-progress/{test_task_id}",
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                task_progress = data.get('task_progress', {})
                
                # Verificar que los pasos marcados estén en el progreso
                expected_steps = ['step-1', 'step-2', 'step-3']
                completed_steps = [step for step in expected_steps if task_progress.get(step, {}).get('completed', False)]
                
                if len(completed_steps) == 3:
                    self.log_test(
                        "Get Task Progress",
                        True,
                        duration,
                        f"Progreso obtenido correctamente: {len(completed_steps)}/3 pasos completados"
                    )
                else:
                    self.log_test(
                        "Get Task Progress",
                        False,
                        duration,
                        f"Progreso incorrecto: {len(completed_steps)}/3 pasos completados. Data: {task_progress}"
                    )
            else:
                self.log_test(
                    "Get Task Progress",
                    False,
                    duration,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(
                "Get Task Progress",
                False,
                duration,
                f"Exception: {str(e)}"
            )
    
    def test_chat_integration_with_progress(self):
        """3. Prueba integración con chat - verificar que herramientas marcan pasos como completados"""
        print("🧪 TESTING: Integración Chat con Actualización de Progreso")
        print("=" * 60)
        
        # Casos de prueba que deberían ejecutar herramientas y actualizar progreso
        test_cases = [
            {
                'name': 'Tarea de Investigación con Herramientas',
                'message': 'Analizar tendencias de IA en 2025',
                'expected_tools': ['web_search'],
                'should_update_progress': True
            },
            {
                'name': 'Tarea de Desarrollo con Shell',
                'message': 'Crear un script de automatización usando ls',
                'expected_tools': ['shell'],
                'should_update_progress': True
            },
            {
                'name': 'WebSearch con Progreso',
                'message': '[WebSearch] noticias tecnología 2025',
                'expected_tools': ['web_search'],
                'should_update_progress': True
            },
            {
                'name': 'DeepSearch con Progreso',
                'message': '[DeepResearch] aplicaciones de IA en medicina',
                'expected_tools': ['deep_research'],
                'should_update_progress': True
            }
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            
            try:
                # Generar task_id único
                task_id = str(uuid.uuid4())
                
                response = self.session.post(
                    f"{self.backend_url}/chat",
                    json={
                        'message': test_case['message'],
                        'context': {
                            'task_id': task_id,
                            'test_mode': True
                        }
                    },
                    timeout=30  # Más tiempo para ejecución de herramientas
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verificar que se ejecutaron herramientas
                    tools_executed = data.get('tools_executed', 0)
                    tool_results = data.get('tool_results', [])
                    mode = data.get('mode', 'unknown')
                    
                    if tools_executed > 0 or tool_results:
                        # Verificar que el progreso se actualizó
                        # Intentar obtener el progreso de la tarea
                        try:
                            progress_response = self.session.get(
                                f"{self.backend_url}/get-task-progress/{task_id}",
                                timeout=5
                            )
                            
                            if progress_response.status_code == 200:
                                progress_data = progress_response.json()
                                task_progress = progress_data.get('task_progress', {})
                                
                                # Contar pasos completados
                                completed_steps = sum(1 for step_data in task_progress.values() 
                                                    if step_data.get('completed', False))
                                
                                if completed_steps > 0:
                                    self.log_test(
                                        f"Chat Integration - {test_case['name']}",
                                        True,
                                        duration,
                                        f"Herramientas ejecutadas ({tools_executed}) y progreso actualizado ({completed_steps} pasos completados)"
                                    )
                                else:
                                    self.log_test(
                                        f"Chat Integration - {test_case['name']}",
                                        False,
                                        duration,
                                        f"Herramientas ejecutadas pero progreso no actualizado. Progress: {task_progress}"
                                    )
                            else:
                                self.log_test(
                                    f"Chat Integration - {test_case['name']}",
                                    False,
                                    duration,
                                    f"No se pudo obtener progreso de tarea. HTTP {progress_response.status_code}"
                                )
                                
                        except Exception as progress_error:
                            self.log_test(
                                f"Chat Integration - {test_case['name']}",
                                False,
                                duration,
                                f"Error obteniendo progreso: {str(progress_error)}"
                            )
                    else:
                        # Para mensajes que no ejecutan herramientas (modo conversación)
                        if mode == 'discussion':
                            self.log_test(
                                f"Chat Integration - {test_case['name']}",
                                True,
                                duration,
                                f"Modo conversación detectado correctamente (sin herramientas)"
                            )
                        else:
                            self.log_test(
                                f"Chat Integration - {test_case['name']}",
                                False,
                                duration,
                                f"No se ejecutaron herramientas esperadas. Mode: {mode}, Tools: {tools_executed}"
                            )
                else:
                    self.log_test(
                        f"Chat Integration - {test_case['name']}",
                        False,
                        duration,
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(
                    f"Chat Integration - {test_case['name']}",
                    False,
                    duration,
                    f"Exception: {str(e)}"
                )
    
    def test_different_task_types(self):
        """4. Prueba diferentes tipos de tareas para verificar planes específicos"""
        print("🧪 TESTING: Diferentes Tipos de Tareas")
        print("=" * 60)
        
        # Casos específicos mencionados en la review request
        specific_tasks = [
            {
                'name': 'Tarea de Investigación Específica',
                'task_title': 'Analizar tendencias de IA en 2025',
                'expected_type': 'research',
                'should_have_keywords': ['investigación', 'analizar', 'recopilar']
            },
            {
                'name': 'Tarea de Desarrollo Específica',
                'task_title': 'Crear un script de automatización',
                'expected_type': 'development',
                'should_have_keywords': ['planificar', 'desarrollar', 'crear']
            },
            {
                'name': 'Tarea de Búsqueda Específica',
                'task_title': 'Buscar información sobre Python',
                'expected_type': 'search',
                'should_have_keywords': ['buscar', 'información', 'procesar']
            },
            {
                'name': 'WebSearch Específico',
                'task_title': '[WebSearch] noticias tecnología',
                'expected_type': 'websearch',
                'should_have_keywords': ['buscar', 'internet', 'filtrar']
            },
            {
                'name': 'DeepSearch Específico',
                'task_title': '[DeepResearch] aplicaciones de IA',
                'expected_type': 'deepresearch',
                'should_have_keywords': ['investigación', 'múltiples fuentes', 'informe']
            }
        ]
        
        for task in specific_tasks:
            start_time = time.time()
            
            try:
                # Generar plan para la tarea
                response = self.session.post(
                    f"{self.backend_url}/generate-plan",
                    json={
                        'task_title': task['task_title'],
                        'context': {'test_mode': True}
                    },
                    timeout=10
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    plan = data.get('plan', [])
                    
                    if plan and len(plan) >= 3:
                        # Verificar que el plan es específico para el tipo de tarea
                        plan_text = ' '.join([step['title'].lower() for step in plan])
                        
                        # Contar keywords específicas encontradas
                        keywords_found = sum(1 for keyword in task['should_have_keywords'] 
                                           if keyword in plan_text)
                        
                        # Verificar que el plan tiene pasos orientados al usuario
                        user_oriented = all(
                            len(step['title']) > 10 and not step['title'].startswith('Step')
                            for step in plan
                        )
                        
                        if keywords_found >= 1 and user_oriented:
                            self.log_test(
                                f"Task Type - {task['name']}",
                                True,
                                duration,
                                f"Plan específico generado con {len(plan)} pasos orientados al usuario"
                            )
                        else:
                            self.log_test(
                                f"Task Type - {task['name']}",
                                False,
                                duration,
                                f"Plan no específico: keywords={keywords_found}, user_oriented={user_oriented}"
                            )
                    else:
                        self.log_test(
                            f"Task Type - {task['name']}",
                            False,
                            duration,
                            f"Plan inválido o muy corto: {len(plan)} pasos"
                        )
                else:
                    self.log_test(
                        f"Task Type - {task['name']}",
                        False,
                        duration,
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(
                    f"Task Type - {task['name']}",
                    False,
                    duration,
                    f"Exception: {str(e)}"
                )
    
    def test_progress_verification(self):
        """5. Verificación del progreso - confirmar que herramientas exitosas actualizan progreso"""
        print("🧪 TESTING: Verificación del Progreso")
        print("=" * 60)
        
        # Test de verificación completa del flujo
        start_time = time.time()
        
        try:
            # 1. Generar un plan
            task_title = "Crear informe sobre mejores prácticas en desarrollo"
            task_id = str(uuid.uuid4())
            
            plan_response = self.session.post(
                f"{self.backend_url}/generate-plan",
                json={
                    'task_title': task_title,
                    'context': {'task_id': task_id}
                },
                timeout=10
            )
            
            if plan_response.status_code != 200:
                raise Exception(f"No se pudo generar plan: {plan_response.status_code}")
            
            plan_data = plan_response.json()
            plan = plan_data.get('plan', [])
            
            if not plan:
                raise Exception("Plan vacío generado")
            
            # 2. Ejecutar chat que debería usar herramientas
            chat_response = self.session.post(
                f"{self.backend_url}/chat",
                json={
                    'message': task_title,
                    'context': {
                        'task_id': task_id,
                        'test_mode': True
                    }
                },
                timeout=30
            )
            
            if chat_response.status_code != 200:
                raise Exception(f"Chat falló: {chat_response.status_code}")
            
            chat_data = chat_response.json()
            tools_executed = chat_data.get('tools_executed', 0)
            
            # 3. Verificar que el progreso se actualizó
            progress_response = self.session.get(
                f"{self.backend_url}/get-task-progress/{task_id}",
                timeout=10
            )
            
            if progress_response.status_code != 200:
                raise Exception(f"No se pudo obtener progreso: {progress_response.status_code}")
            
            progress_data = progress_response.json()
            task_progress = progress_data.get('task_progress', {})
            
            # Contar pasos completados
            completed_steps = sum(1 for step_data in task_progress.values() 
                                if step_data.get('completed', False))
            
            duration = time.time() - start_time
            
            # Verificar flujo completo
            if tools_executed > 0 and completed_steps > 0:
                self.log_test(
                    "Progress Verification - Complete Flow",
                    True,
                    duration,
                    f"Flujo completo exitoso: Plan generado ({len(plan)} pasos) → Herramientas ejecutadas ({tools_executed}) → Progreso actualizado ({completed_steps} pasos completados)"
                )
            else:
                self.log_test(
                    "Progress Verification - Complete Flow",
                    False,
                    duration,
                    f"Flujo incompleto: tools_executed={tools_executed}, completed_steps={completed_steps}"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(
                "Progress Verification - Complete Flow",
                False,
                duration,
                f"Exception: {str(e)}"
            )
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas del sistema de Plan de Acción"""
        print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE PLAN DE ACCIÓN DE MITOSIS")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Ejecutar todas las pruebas
        self.test_generate_plan_endpoint()
        self.test_task_progress_endpoints()
        self.test_chat_integration_with_progress()
        self.test_different_task_types()
        self.test_progress_verification()
        
        # Generar reporte final
        self.generate_final_report()
    
    def generate_final_report(self):
        """Genera reporte final de las pruebas"""
        print("📊 REPORTE FINAL - SISTEMA DE PLAN DE ACCIÓN DE MITOSIS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 ESTADÍSTICAS GENERALES:")
        print(f"   Total de pruebas: {total_tests}")
        print(f"   Pruebas exitosas: {passed_tests}")
        print(f"   Pruebas fallidas: {failed_tests}")
        print(f"   Tasa de éxito: {success_rate:.1f}%")
        print()
        
        # Agrupar resultados por categoría
        categories = {}
        for result in self.test_results:
            category = result['test'].split(' - ')[0]
            if category not in categories:
                categories[category] = {'passed': 0, 'failed': 0, 'tests': []}
            
            if result['success']:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
            
            categories[category]['tests'].append(result)
        
        print("📋 RESULTADOS POR CATEGORÍA:")
        for category, data in categories.items():
            total_cat = data['passed'] + data['failed']
            success_rate_cat = (data['passed'] / total_cat * 100) if total_cat > 0 else 0
            status = "✅" if data['failed'] == 0 else "⚠️" if data['passed'] > data['failed'] else "❌"
            
            print(f"   {status} {category}: {data['passed']}/{total_cat} ({success_rate_cat:.1f}%)")
        
        print()
        
        # Mostrar pruebas fallidas
        if failed_tests > 0:
            print("❌ PRUEBAS FALLIDAS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Evaluación final
        if success_rate >= 90:
            status = "✅ EXCELENTE"
            recommendation = "Sistema de Plan de Acción funcionando perfectamente"
        elif success_rate >= 75:
            status = "⚠️ BUENO"
            recommendation = "Sistema funcional con problemas menores"
        elif success_rate >= 50:
            status = "⚠️ REGULAR"
            recommendation = "Sistema requiere mejoras significativas"
        else:
            status = "❌ CRÍTICO"
            recommendation = "Sistema requiere revisión completa"
        
        print(f"🎯 EVALUACIÓN FINAL: {status}")
        print(f"📝 RECOMENDACIÓN: {recommendation}")
        print()
        
        # Verificación específica de la review request
        print("🔍 VERIFICACIÓN DE REVIEW REQUEST:")
        
        # 1. Generación de Planes Mejorados
        plan_tests = [r for r in self.test_results if 'Generate Plan' in r['test']]
        plan_success = sum(1 for r in plan_tests if r['success'])
        print(f"   1. Generación de Planes Mejorados: {plan_success}/{len(plan_tests)} ({'✅' if plan_success == len(plan_tests) else '❌'})")
        
        # 2. Actualización de Progreso
        progress_tests = [r for r in self.test_results if 'Update Task Progress' in r['test'] or 'Get Task Progress' in r['test']]
        progress_success = sum(1 for r in progress_tests if r['success'])
        print(f"   2. Actualización de Progreso: {progress_success}/{len(progress_tests)} ({'✅' if progress_success == len(progress_tests) else '❌'})")
        
        # 3. Integración con Chat
        chat_tests = [r for r in self.test_results if 'Chat Integration' in r['test']]
        chat_success = sum(1 for r in chat_tests if r['success'])
        print(f"   3. Integración con Chat: {chat_success}/{len(chat_tests)} ({'✅' if chat_success == len(chat_tests) else '❌'})")
        
        # 4. Diferentes Tipos de Tareas
        task_type_tests = [r for r in self.test_results if 'Task Type' in r['test']]
        task_type_success = sum(1 for r in task_type_tests if r['success'])
        print(f"   4. Diferentes Tipos de Tareas: {task_type_success}/{len(task_type_tests)} ({'✅' if task_type_success == len(task_type_tests) else '❌'})")
        
        # 5. Verificación del Progreso
        verification_tests = [r for r in self.test_results if 'Progress Verification' in r['test']]
        verification_success = sum(1 for r in verification_tests if r['success'])
        print(f"   5. Verificación del Progreso: {verification_success}/{len(verification_tests)} ({'✅' if verification_success == len(verification_tests) else '❌'})")
        
        print()
        print("=" * 80)
        print(f"🏁 PRUEBAS COMPLETADAS - {datetime.now().isoformat()}")
        print("=" * 80)

if __name__ == "__main__":
    tester = MitosisActionPlanTester()
    tester.run_all_tests()