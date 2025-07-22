#!/usr/bin/env python3
"""
Test del Sistema de Clasificación de Intenciones - NEWUPGRADE.md
Prueba la nueva implementación del IntentionClassifier con LLM dedicado
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuración de la URL del backend
BACKEND_URL = "https://21a4481d-b7bc-4f4d-8638-6bc680072ee5.preview.emergentagent.com"

class IntentionClassificationTester:
    """Tester para el sistema de clasificación de intenciones"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Registra el resultado de un test"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = {
            "test_name": test_name,
            "status": status,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def test_chat_endpoint_basic(self) -> bool:
        """Test básico del endpoint de chat"""
        try:
            response = requests.post(
                f"{self.backend_url}/api/agent/chat",
                json={"message": "Test básico de conexión"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                has_response = "response" in data
                has_timestamp = "timestamp" in data
                
                self.log_test(
                    "Chat Endpoint Basic Connection",
                    has_response and has_timestamp,
                    f"Status: {response.status_code}, Response keys: {list(data.keys())}"
                )
                return has_response and has_timestamp
            else:
                self.log_test(
                    "Chat Endpoint Basic Connection",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Chat Endpoint Basic Connection",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_intention_classification_metadata(self, message: str, expected_type: str) -> Dict[str, Any]:
        """Test de clasificación de intención específica"""
        try:
            response = requests.post(
                f"{self.backend_url}/api/agent/chat",
                json={"message": message},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar que existe metadata de clasificación
                has_intention_metadata = "intention_classification" in data
                
                if has_intention_metadata:
                    intention_data = data["intention_classification"]
                    classified_type = intention_data.get("type", "unknown")
                    confidence = intention_data.get("confidence", 0.0)
                    reasoning = intention_data.get("reasoning", "")
                    
                    # Verificar que el tipo clasificado coincide con el esperado
                    type_matches = classified_type == expected_type
                    has_confidence = confidence > 0.0
                    has_reasoning = len(reasoning) > 0
                    
                    success = type_matches and has_confidence and has_reasoning
                    
                    details = (f"Mensaje: '{message}' | "
                             f"Esperado: {expected_type} | "
                             f"Clasificado: {classified_type} | "
                             f"Confianza: {confidence:.2f} | "
                             f"Razonamiento: {reasoning[:100]}...")
                    
                    self.log_test(
                        f"Intention Classification - {expected_type}",
                        success,
                        details
                    )
                    
                    return {
                        "success": success,
                        "classified_type": classified_type,
                        "confidence": confidence,
                        "reasoning": reasoning,
                        "expected_type": expected_type,
                        "type_matches": type_matches
                    }
                else:
                    self.log_test(
                        f"Intention Classification - {expected_type}",
                        False,
                        f"No intention_classification metadata found in response"
                    )
                    return {"success": False, "error": "No intention metadata"}
            else:
                self.log_test(
                    f"Intention Classification - {expected_type}",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log_test(
                f"Intention Classification - {expected_type}",
                False,
                f"Exception: {str(e)}"
            )
            return {"success": False, "error": str(e)}
    
    def test_all_intention_categories(self):
        """Test de todas las 7 categorías de intención"""
        
        test_cases = [
            # CASUAL_CONVERSATION
            {
                "message": "Hola, ¿cómo estás?",
                "expected_type": "casual_conversation",
                "description": "Saludo simple"
            },
            {
                "message": "Buenos días, ¿qué tal?",
                "expected_type": "casual_conversation", 
                "description": "Saludo matutino"
            },
            
            # INFORMATION_REQUEST
            {
                "message": "¿Cuál es la capital de Francia?",
                "expected_type": "information_request",
                "description": "Pregunta de información factual"
            },
            {
                "message": "¿Qué sabes sobre inteligencia artificial?",
                "expected_type": "information_request",
                "description": "Consulta de conocimiento"
            },
            
            # SIMPLE_TASK
            {
                "message": "Crea un archivo de texto",
                "expected_type": "simple_task",
                "description": "Tarea simple de creación"
            },
            {
                "message": "Escribe una lista de compras",
                "expected_type": "simple_task",
                "description": "Tarea simple de escritura"
            },
            
            # COMPLEX_TASK
            {
                "message": "Desarrolla una aplicación web con dashboard de analytics",
                "expected_type": "complex_task",
                "description": "Tarea compleja de desarrollo"
            },
            {
                "message": "Crear un plan de marketing digital completo para una startup tecnológica",
                "expected_type": "complex_task",
                "description": "Tarea compleja de planificación"
            },
            
            # TASK_MANAGEMENT
            {
                "message": "¿Cuál es el estado de mis tareas?",
                "expected_type": "task_management",
                "description": "Consulta de estado de tareas"
            },
            {
                "message": "Pausar la tarea actual",
                "expected_type": "task_management",
                "description": "Comando de gestión de tareas"
            },
            
            # AGENT_CONFIGURATION
            {
                "message": "Cambia tu configuración de modelo",
                "expected_type": "agent_configuration",
                "description": "Solicitud de configuración"
            },
            {
                "message": "Configura el modo debug",
                "expected_type": "agent_configuration",
                "description": "Configuración de sistema"
            },
            
            # UNCLEAR
            {
                "message": "Esto... bueno... no sé...",
                "expected_type": "unclear",
                "description": "Mensaje ambiguo"
            }
        ]
        
        print("🎯 TESTING ALL INTENTION CATEGORIES")
        print("=" * 60)
        
        category_results = {}
        
        for test_case in test_cases:
            message = test_case["message"]
            expected_type = test_case["expected_type"]
            description = test_case["description"]
            
            print(f"\n📝 Testing: {description}")
            print(f"   Message: '{message}'")
            print(f"   Expected: {expected_type}")
            
            result = self.test_intention_classification_metadata(message, expected_type)
            
            if expected_type not in category_results:
                category_results[expected_type] = []
            category_results[expected_type].append(result)
            
            # Pequeña pausa entre tests
            time.sleep(1)
        
        return category_results
    
    def test_confidence_scores(self):
        """Test de scores de confianza"""
        print("\n🎯 TESTING CONFIDENCE SCORES")
        print("=" * 40)
        
        high_confidence_cases = [
            "Hola, ¿cómo estás?",  # Muy claro - casual
            "¿Cuál es la capital de España?",  # Muy claro - información
            "Crear un dashboard completo de ventas con gráficos interactivos"  # Muy claro - tarea compleja
        ]
        
        confidence_results = []
        
        for message in high_confidence_cases:
            try:
                response = requests.post(
                    f"{self.backend_url}/api/agent/chat",
                    json={"message": message},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "intention_classification" in data:
                        confidence = data["intention_classification"].get("confidence", 0.0)
                        confidence_results.append({
                            "message": message,
                            "confidence": confidence,
                            "high_confidence": confidence >= 0.8
                        })
                        
                        self.log_test(
                            f"Confidence Score Test",
                            confidence >= 0.7,  # Umbral mínimo aceptable
                            f"Message: '{message[:30]}...' | Confidence: {confidence:.2f}"
                        )
                
                time.sleep(1)
                
            except Exception as e:
                self.log_test(
                    "Confidence Score Test",
                    False,
                    f"Exception: {str(e)}"
                )
        
        return confidence_results
    
    def test_extracted_entities(self):
        """Test de extracción de entidades"""
        print("\n🎯 TESTING ENTITY EXTRACTION")
        print("=" * 40)
        
        entity_test_cases = [
            {
                "message": "Crear un informe de ventas para el Q4 2024",
                "expected_entities": ["task_title", "time_constraints"]
            },
            {
                "message": "Desarrollar una aplicación web urgente con base de datos",
                "expected_entities": ["task_title", "mentioned_tools", "priority_level"]
            }
        ]
        
        for test_case in entity_test_cases:
            try:
                response = requests.post(
                    f"{self.backend_url}/api/agent/chat",
                    json={"message": test_case["message"]},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "intention_classification" in data:
                        extracted_entities = data["intention_classification"].get("extracted_entities", {})
                        
                        entities_found = len(extracted_entities) > 0
                        
                        self.log_test(
                            "Entity Extraction Test",
                            entities_found,
                            f"Message: '{test_case['message'][:40]}...' | Entities: {list(extracted_entities.keys())}"
                        )
                
                time.sleep(1)
                
            except Exception as e:
                self.log_test(
                    "Entity Extraction Test",
                    False,
                    f"Exception: {str(e)}"
                )
    
    def test_contextual_responses(self):
        """Test de respuestas contextualizadas por intención"""
        print("\n🎯 TESTING CONTEXTUAL RESPONSES")
        print("=" * 40)
        
        contextual_cases = [
            {
                "message": "Hola",
                "expected_type": "casual_conversation",
                "should_contain": ["conversación", "casual", "cordial"]
            },
            {
                "message": "Crear un análisis de mercado",
                "expected_type": "complex_task",
                "should_contain": ["plan", "ejecución", "autónoma", "pasos"]
            }
        ]
        
        for test_case in contextual_cases:
            try:
                response = requests.post(
                    f"{self.backend_url}/api/agent/chat",
                    json={"message": test_case["message"]},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", "").lower()
                    
                    # Verificar que la respuesta está contextualizada
                    contextual_words_found = any(
                        word in response_text 
                        for word in test_case["should_contain"]
                    )
                    
                    self.log_test(
                        "Contextual Response Test",
                        contextual_words_found,
                        f"Message: '{test_case['message']}' | Response contains contextual words: {contextual_words_found}"
                    )
                
                time.sleep(1)
                
            except Exception as e:
                self.log_test(
                    "Contextual Response Test",
                    False,
                    f"Exception: {str(e)}"
                )
    
    def run_comprehensive_test(self):
        """Ejecuta todos los tests del sistema de clasificación"""
        print("🚀 INICIANDO TESTS DEL SISTEMA DE CLASIFICACIÓN DE INTENCIONES")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Test 1: Conexión básica
        print("\n1️⃣ TESTING BASIC CONNECTIVITY")
        basic_success = self.test_chat_endpoint_basic()
        
        if not basic_success:
            print("❌ CRITICAL: Basic connectivity failed. Stopping tests.")
            return self.generate_final_report()
        
        # Test 2: Todas las categorías de intención
        print("\n2️⃣ TESTING ALL INTENTION CATEGORIES")
        category_results = self.test_all_intention_categories()
        
        # Test 3: Scores de confianza
        print("\n3️⃣ TESTING CONFIDENCE SCORES")
        confidence_results = self.test_confidence_scores()
        
        # Test 4: Extracción de entidades
        print("\n4️⃣ TESTING ENTITY EXTRACTION")
        self.test_extracted_entities()
        
        # Test 5: Respuestas contextualizadas
        print("\n5️⃣ TESTING CONTEXTUAL RESPONSES")
        self.test_contextual_responses()
        
        # Generar reporte final
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Genera el reporte final de tests"""
        print("\n" + "=" * 80)
        print("📊 REPORTE FINAL - SISTEMA DE CLASIFICACIÓN DE INTENCIONES")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📈 ESTADÍSTICAS GENERALES:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Tests Passed: {self.passed_tests}")
        print(f"   Tests Failed: {self.total_tests - self.passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n🎯 EVALUACIÓN DEL SISTEMA:")
        if success_rate >= 95:
            evaluation = "✅ EXCELENTE - Sistema funcionando perfectamente"
        elif success_rate >= 85:
            evaluation = "✅ BUENO - Sistema funcionando correctamente con mejoras menores"
        elif success_rate >= 70:
            evaluation = "⚠️ ACEPTABLE - Sistema funcional pero necesita mejoras"
        else:
            evaluation = "❌ CRÍTICO - Sistema requiere correcciones importantes"
        
        print(f"   {evaluation}")
        
        print(f"\n📋 RESUMEN DE TESTS:")
        for result in self.test_results:
            print(f"   {result['status']}: {result['test_name']}")
            if result['details']:
                print(f"      └─ {result['details'][:100]}...")
        
        print(f"\n🔍 ANÁLISIS DE FUNCIONALIDAD:")
        
        # Verificar si el sistema de clasificación está funcionando
        intention_tests = [r for r in self.test_results if "Intention Classification" in r['test_name']]
        intention_success_rate = (len([r for r in intention_tests if r['passed']]) / len(intention_tests) * 100) if intention_tests else 0
        
        print(f"   Clasificación de Intenciones: {intention_success_rate:.1f}% éxito")
        
        if intention_success_rate >= 80:
            print("   ✅ Sistema de clasificación LLM operativo")
        else:
            print("   ❌ Sistema de clasificación LLM requiere atención")
        
        # Verificar metadata
        metadata_tests = [r for r in self.test_results if "metadata" in r['details'].lower()]
        if metadata_tests:
            print("   ✅ Metadata de clasificación presente en respuestas")
        else:
            print("   ⚠️ Verificar metadata de clasificación en respuestas")
        
        print(f"\n⏰ Test completado: {datetime.now().isoformat()}")
        print("=" * 80)
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "success_rate": success_rate,
            "evaluation": evaluation,
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Función principal"""
    tester = IntentionClassificationTester()
    
    try:
        final_report = tester.run_comprehensive_test()
        
        # Guardar reporte en archivo
        with open('/app/intention_classification_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Reporte guardado en: /app/intention_classification_test_results.json")
        
        return final_report["success_rate"] >= 70  # Umbral mínimo de éxito
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrumpidos por el usuario")
        return False
    except Exception as e:
        print(f"\n❌ Error crítico durante los tests: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)