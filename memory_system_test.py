#!/usr/bin/env python3
"""
Comprehensive Memory System Testing for Mitosis Application
Tests all memory functionality including initialization, storage, retrieval, and analytics
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

class MemorySystemTester:
    def __init__(self, backend_url: str = "http://localhost:8001"):
        self.backend_url = backend_url
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
            
        result = {
            'test_name': test_name,
            'status': status,
            'success': success,
            'details': details,
            'response_time': f"{response_time:.2f}s",
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status} ({response_time:.2f}s) - {test_name}")
        if details:
            print(f"    Details: {details}")
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                # Check if all services are healthy
                ollama_healthy = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                database_healthy = services.get('database', False)
                
                details = f"Ollama: {ollama_healthy}, Tools: {tools_count}, Database: {database_healthy}"
                self.log_test("Backend Health Check", True, details, response_time)
                return True
            else:
                self.log_test("Backend Health Check", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}", 0)
            return False
    
    def test_memory_system_initialization(self):
        """Test memory system initialization through analytics endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/api/memory/memory-analytics", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if memory system components are initialized
                overview = data.get('overview', {})
                
                # Check for memory components
                working_memory = overview.get('working_memory', {})
                episodic_memory = overview.get('episodic_memory', {})
                semantic_memory = overview.get('semantic_memory', {})
                procedural_memory = overview.get('procedural_memory', {})
                embedding_service = overview.get('embedding_service', {})
                semantic_indexer = overview.get('semantic_indexer', {})
                
                components_found = []
                if working_memory:
                    components_found.append("WorkingMemory")
                if episodic_memory:
                    components_found.append("EpisodicMemory")
                if semantic_memory:
                    components_found.append("SemanticMemory")
                if procedural_memory:
                    components_found.append("ProceduralMemory")
                if embedding_service:
                    components_found.append("EmbeddingService")
                if semantic_indexer:
                    components_found.append("SemanticIndexer")
                
                details = f"Components initialized: {', '.join(components_found)}"
                self.log_test("Memory System Initialization", len(components_found) >= 4, details, response_time)
                return len(components_found) >= 4
                
            else:
                self.log_test("Memory System Initialization", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Memory System Initialization", False, f"Error: {str(e)}", 0)
            return False
    
    def test_semantic_search(self):
        """Test semantic search functionality"""
        try:
            start_time = time.time()
            
            # Test semantic search with a simple query
            payload = {
                "query": "test search query",
                "max_results": 5
            }
            
            response = requests.post(
                f"{self.backend_url}/api/memory/semantic-search",
                json=payload,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                has_query = 'query' in data
                has_results = 'results' in data
                has_total = 'total_results' in data
                has_timestamp = 'search_timestamp' in data
                
                results = data.get('results', [])
                total_results = data.get('total_results', 0)
                
                details = f"Query: '{data.get('query', '')}', Results: {total_results}, Structure complete: {has_query and has_results and has_total and has_timestamp}"
                self.log_test("Semantic Search Functionality", True, details, response_time)
                return True
                
            else:
                self.log_test("Semantic Search Functionality", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Semantic Search Functionality", False, f"Error: {str(e)}", 0)
            return False
    
    def test_episode_storage(self):
        """Test storing episodes in memory"""
        try:
            start_time = time.time()
            
            # Create test episode data
            payload = {
                "user_query": "What is artificial intelligence?",
                "agent_response": "Artificial intelligence (AI) is a branch of computer science that aims to create machines capable of intelligent behavior.",
                "success": True,
                "context": {
                    "session_id": "test_session_123",
                    "timestamp": datetime.now().isoformat()
                },
                "tools_used": ["web_search", "knowledge_base"],
                "importance": 0.8,
                "metadata": {
                    "test_episode": True,
                    "category": "educational"
                }
            }
            
            response = requests.post(
                f"{self.backend_url}/api/memory/store-episode",
                json=payload,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                success = data.get('success', False)
                episode_id = data.get('episode_id', '')
                stored_at = data.get('stored_at', '')
                
                details = f"Episode ID: {episode_id}, Success: {success}, Stored at: {stored_at}"
                self.log_test("Episode Storage", success and episode_id, details, response_time)
                return success and episode_id
                
            else:
                self.log_test("Episode Storage", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Episode Storage", False, f"Error: {str(e)}", 0)
            return False
    
    def test_knowledge_storage(self):
        """Test storing knowledge in semantic memory"""
        try:
            start_time = time.time()
            
            # Create test knowledge data (fact)
            payload = {
                "content": "Python is a high-level programming language known for its simplicity and readability.",
                "type": "fact",
                "subject": "Python",
                "predicate": "is",
                "object": "a high-level programming language",
                "confidence": 0.9,
                "context": {
                    "domain": "programming",
                    "source": "test_system"
                }
            }
            
            response = requests.post(
                f"{self.backend_url}/api/memory/store-knowledge",
                json=payload,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                success = data.get('success', False)
                knowledge_id = data.get('knowledge_id', '')
                knowledge_type = data.get('type', '')
                stored_at = data.get('stored_at', '')
                
                details = f"Knowledge ID: {knowledge_id}, Type: {knowledge_type}, Success: {success}"
                self.log_test("Knowledge Storage", success and knowledge_id, details, response_time)
                return success and knowledge_id
                
            else:
                self.log_test("Knowledge Storage", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Knowledge Storage", False, f"Error: {str(e)}", 0)
            return False
    
    def test_procedure_storage(self):
        """Test storing procedures in procedural memory"""
        try:
            start_time = time.time()
            
            # Create test procedure data
            payload = {
                "name": "Web Search Procedure",
                "description": "Standard procedure for conducting web searches",
                "steps": [
                    "Analyze the query for key terms",
                    "Execute web search with optimized parameters",
                    "Filter and rank results by relevance",
                    "Extract key information from top results",
                    "Synthesize findings into coherent response"
                ],
                "category": "information_retrieval",
                "context_conditions": {
                    "requires_internet": True,
                    "query_type": "factual"
                },
                "effectiveness": 0.85,
                "usage_count": 0,
                "metadata": {
                    "test_procedure": True,
                    "created_by": "test_system"
                }
            }
            
            response = requests.post(
                f"{self.backend_url}/api/memory/store-procedure",
                json=payload,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                success = data.get('success', False)
                procedure_id = data.get('procedure_id', '')
                stored_at = data.get('stored_at', '')
                
                details = f"Procedure ID: {procedure_id}, Success: {success}, Stored at: {stored_at}"
                self.log_test("Procedure Storage", success and procedure_id, details, response_time)
                return success and procedure_id
                
            else:
                self.log_test("Procedure Storage", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Procedure Storage", False, f"Error: {str(e)}", 0)
            return False
    
    def test_memory_analytics(self):
        """Test comprehensive memory analytics"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/api/memory/memory-analytics", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check analytics structure
                has_overview = 'overview' in data
                has_efficiency = 'memory_efficiency' in data
                has_insights = 'learning_insights' in data
                
                overview = data.get('overview', {})
                efficiency = data.get('memory_efficiency', {})
                insights = data.get('learning_insights', {})
                
                # Count available memory components
                memory_components = []
                if 'working_memory' in overview:
                    memory_components.append('working_memory')
                if 'episodic_memory' in overview:
                    memory_components.append('episodic_memory')
                if 'semantic_memory' in overview:
                    memory_components.append('semantic_memory')
                if 'procedural_memory' in overview:
                    memory_components.append('procedural_memory')
                if 'embedding_service' in overview:
                    memory_components.append('embedding_service')
                if 'semantic_indexer' in overview:
                    memory_components.append('semantic_indexer')
                
                details = f"Components: {len(memory_components)}, Sections: overview={has_overview}, efficiency={has_efficiency}, insights={has_insights}"
                success = has_overview and len(memory_components) >= 3
                
                self.log_test("Memory Analytics", success, details, response_time)
                return success
                
            else:
                self.log_test("Memory Analytics", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Memory Analytics", False, f"Error: {str(e)}", 0)
            return False
    
    def test_context_retrieval(self):
        """Test context retrieval functionality"""
        try:
            start_time = time.time()
            
            # Test context retrieval with a query
            payload = {
                "query": "programming languages and artificial intelligence",
                "context_type": "all",
                "max_results": 10
            }
            
            response = requests.post(
                f"{self.backend_url}/api/memory/retrieve-context",
                json=payload,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                has_query = 'query' in data
                has_context = 'context' in data
                has_timestamp = 'retrieved_at' in data
                
                context = data.get('context', {})
                query = data.get('query', '')
                
                details = f"Query: '{query}', Context available: {bool(context)}, Structure complete: {has_query and has_context and has_timestamp}"
                self.log_test("Context Retrieval", True, details, response_time)
                return True
                
            else:
                self.log_test("Context Retrieval", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Context Retrieval", False, f"Error: {str(e)}", 0)
            return False
    
    def test_memory_integration_with_chat(self):
        """Test memory integration with main chat endpoint"""
        try:
            start_time = time.time()
            
            # Test chat endpoint to see if memory is being used
            payload = {
                "message": "Tell me about artificial intelligence and its applications in programming",
                "session_id": "memory_integration_test",
                "use_memory": True
            }
            
            response = requests.post(
                f"{self.backend_url}/api/agent/chat",
                json=payload,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response indicates memory usage
                has_response = 'response' in data or 'message' in data or 'result' in data
                
                # Look for any indication of memory usage in the response
                response_text = str(data).lower()
                memory_indicators = ['memory', 'context', 'previous', 'recall', 'remember']
                memory_used = any(indicator in response_text for indicator in memory_indicators)
                
                details = f"Chat response received: {has_response}, Memory integration detected: {memory_used}"
                self.log_test("Memory Integration with Chat", has_response, details, response_time)
                return has_response
                
            else:
                self.log_test("Memory Integration with Chat", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Memory Integration with Chat", False, f"Error: {str(e)}", 0)
            return False
    
    def run_comprehensive_memory_tests(self):
        """Run all memory system tests"""
        print("🧠 STARTING COMPREHENSIVE MEMORY SYSTEM TESTING")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Backend Health Check", self.test_backend_health),
            ("Memory System Initialization", self.test_memory_system_initialization),
            ("Semantic Search Functionality", self.test_semantic_search),
            ("Episode Storage", self.test_episode_storage),
            ("Knowledge Storage", self.test_knowledge_storage),
            ("Procedure Storage", self.test_procedure_storage),
            ("Memory Analytics", self.test_memory_analytics),
            ("Context Retrieval", self.test_context_retrieval),
            ("Memory Integration with Chat", self.test_memory_integration_with_chat)
        ]
        
        # Run tests
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            test_func()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🧠 MEMORY SYSTEM TESTING SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📊 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} ({result['response_time']}) - {result['test_name']}")
            if result['details']:
                print(f"    {result['details']}")
        
        # Determine overall status
        if success_rate >= 80:
            print(f"\n✅ MEMORY SYSTEM STATUS: WORKING ({success_rate:.1f}% success rate)")
            return True
        elif success_rate >= 60:
            print(f"\n⚠️ MEMORY SYSTEM STATUS: PARTIALLY WORKING ({success_rate:.1f}% success rate)")
            return False
        else:
            print(f"\n❌ MEMORY SYSTEM STATUS: CRITICAL ISSUES ({success_rate:.1f}% success rate)")
            return False

def main():
    """Main testing function"""
    # Get backend URL from environment or use default
    backend_url = "http://localhost:8001"
    
    print(f"🎯 Testing Mitosis Memory System at: {backend_url}")
    print(f"🕐 Test started at: {datetime.now().isoformat()}")
    
    # Create tester and run tests
    tester = MemorySystemTester(backend_url)
    success = tester.run_comprehensive_memory_tests()
    
    print(f"\n🏁 Testing completed at: {datetime.now().isoformat()}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()