#!/usr/bin/env python3
"""
Test completo del sistema de memoria de Mitosis
Prueba memoria episódica, semántica y procedimental
"""

import asyncio
import requests
import json
import time
from datetime import datetime
import sys
import os

# Configurar el backend URL
BACKEND_URL = "http://localhost:8001"

class MemorySystemTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.session_id = f"test_session_{int(time.time())}"
        
    def log_test(self, test_name, success, details, response_time=None):
        """Registra el resultado de un test"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status}: {test_name}{time_info}")
        if not success:
            print(f"    Error: {details}")
        else:
            print(f"    {details}")
    
    def test_backend_health(self):
        """Verifica que el backend esté funcionando"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "Backend Health Check",
                    True,
                    f"Backend healthy - Services: {health_data.get('services', {})}",
                    response_time
                )
                return True
            else:
                self.log_test(
                    "Backend Health Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Backend Health Check",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_memory_stats(self):
        """Prueba obtener estadísticas de memoria"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/api/agent/memory/stats", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "Memory Stats",
                    True,
                    f"Memory stats retrieved - Total memories: {stats.get('total_memories', 0)}, "
                    f"Episodic: {stats.get('episodic_memory', {}).get('total_episodes', 0)}, "
                    f"Semantic: {stats.get('semantic_memory', {}).get('total_concepts', 0)}",
                    response_time
                )
                return True, stats
            else:
                self.log_test(
                    "Memory Stats",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False, None
                
        except Exception as e:
            self.log_test(
                "Memory Stats",
                False,
                f"Request error: {str(e)}"
            )
            return False, None
    
    def test_memory_search(self):
        """Prueba búsqueda en memoria"""
        try:
            # Datos de prueba para búsqueda
            search_queries = [
                "inteligencia artificial",
                "python programming",
                "machine learning",
                "testing memory system"
            ]
            
            successful_searches = 0
            total_searches = len(search_queries)
            
            for query in search_queries:
                start_time = time.time()
                response = requests.post(
                    f"{self.backend_url}/api/agent/memory/search",
                    json={
                        "query": query,
                        "context_type": "all",
                        "max_results": 5
                    },
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    search_results = response.json()
                    successful_searches += 1
                    self.log_test(
                        f"Memory Search - '{query}'",
                        True,
                        f"Search completed - Results type: {type(search_results)}",
                        response_time
                    )
                else:
                    self.log_test(
                        f"Memory Search - '{query}'",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                        response_time
                    )
            
            overall_success = successful_searches == total_searches
            self.log_test(
                "Memory Search Overall",
                overall_success,
                f"Completed {successful_searches}/{total_searches} searches successfully"
            )
            
            return overall_success
            
        except Exception as e:
            self.log_test(
                "Memory Search",
                False,
                f"Request error: {str(e)}"
            )
            return False
    
    def test_learning_insights(self):
        """Prueba obtener insights de aprendizaje"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/api/agent/memory/learning-insights", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                insights = response.json()
                self.log_test(
                    "Learning Insights",
                    True,
                    f"Insights retrieved - Keys: {list(insights.keys())}",
                    response_time
                )
                return True, insights
            else:
                self.log_test(
                    "Learning Insights",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False, None
                
        except Exception as e:
            self.log_test(
                "Learning Insights",
                False,
                f"Request error: {str(e)}"
            )
            return False, None
    
    def test_memory_integration_with_chat(self):
        """Prueba integración de memoria con chat"""
        try:
            # Crear varias conversaciones para poblar la memoria
            test_conversations = [
                "Explícame qué es la inteligencia artificial",
                "¿Cómo funciona el machine learning?",
                "Cuáles son los beneficios de Python para programación?",
                "Describe los algoritmos de búsqueda más comunes"
            ]
            
            successful_chats = 0
            total_chats = len(test_conversations)
            
            for i, message in enumerate(test_conversations):
                start_time = time.time()
                response = requests.post(
                    f"{self.backend_url}/api/agent/chat",
                    json={
                        "message": message,
                        "context": {
                            "session_id": self.session_id,
                            "user_id": "test_user",
                            "task_id": f"memory_test_{i}"
                        }
                    },
                    timeout=30
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    chat_response = response.json()
                    successful_chats += 1
                    
                    # Verificar si se usó memoria
                    memory_used = chat_response.get('memory_used', False)
                    
                    self.log_test(
                        f"Chat with Memory - Message {i+1}",
                        True,
                        f"Chat completed - Memory used: {memory_used}, "
                        f"Response length: {len(chat_response.get('response', ''))}",
                        response_time
                    )
                else:
                    self.log_test(
                        f"Chat with Memory - Message {i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                        response_time
                    )
                
                # Esperar un poco entre mensajes
                time.sleep(1)
            
            overall_success = successful_chats == total_chats
            self.log_test(
                "Memory Integration with Chat",
                overall_success,
                f"Completed {successful_chats}/{total_chats} chat interactions successfully"
            )
            
            return overall_success
            
        except Exception as e:
            self.log_test(
                "Memory Integration with Chat",
                False,
                f"Request error: {str(e)}"
            )
            return False
    
    def test_enhanced_agent_status(self):
        """Prueba estado del enhanced agent"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/api/agent/enhanced/status", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status = response.json()
                self.log_test(
                    "Enhanced Agent Status",
                    True,
                    f"Enhanced agent available - Cognitive mode: {status.get('cognitive_capabilities', {}).get('current_mode', 'unknown')}, "
                    f"Learning enabled: {status.get('cognitive_capabilities', {}).get('learning_enabled', False)}",
                    response_time
                )
                return True, status
            else:
                self.log_test(
                    "Enhanced Agent Status",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False, None
                
        except Exception as e:
            self.log_test(
                "Enhanced Agent Status",
                False,
                f"Request error: {str(e)}"
            )
            return False, None
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("🧠 INICIANDO PRUEBAS DEL SISTEMA DE MEMORIA DE MITOSIS")
        print("=" * 60)
        
        # Test 1: Backend Health
        if not self.test_backend_health():
            print("❌ Backend no disponible, abortando pruebas")
            return False
        
        print("\n📊 PROBANDO SISTEMA DE MEMORIA...")
        print("-" * 40)
        
        # Test 2: Memory Stats
        self.test_memory_stats()
        
        # Test 3: Memory Search
        self.test_memory_search()
        
        # Test 4: Learning Insights
        self.test_learning_insights()
        
        # Test 5: Enhanced Agent Status
        self.test_enhanced_agent_status()
        
        print("\n🤖 PROBANDO INTEGRACIÓN CON CHAT...")
        print("-" * 40)
        
        # Test 6: Memory Integration with Chat
        self.test_memory_integration_with_chat()
        
        # Estadísticas finales después de las pruebas
        print("\n📈 ESTADÍSTICAS FINALES DE MEMORIA...")
        print("-" * 40)
        self.test_memory_stats()
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📋 RESUMEN DE PRUEBAS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de pruebas: {total_tests}")
        print(f"✅ Exitosas: {passed_tests}")
        print(f"❌ Fallidas: {failed_tests}")
        print(f"📊 Tasa de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ PRUEBAS FALLIDAS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  • {test['test_name']}: {test['details']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = MemorySystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 TODAS LAS PRUEBAS DE MEMORIA PASARON EXITOSAMENTE!")
        sys.exit(0)
    else:
        print("\n⚠️ ALGUNAS PRUEBAS FALLARON - REVISAR CONFIGURACIÓN")
        sys.exit(1)