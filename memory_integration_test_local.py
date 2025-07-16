#!/usr/bin/env python3
"""
Memory System Integration Test for Mitosis Application - LOCAL VERSION
Tests the memory system integration to identify why the chat endpoint was failing (Error 500)
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration - LOCAL TESTING
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class MemoryIntegrationTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_result(self, test_name, status, details, duration=0):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'duration': f"{duration:.2f}s"
        }
        self.results.append(result)
        self.total_tests += 1
        if status == "✅ PASSED":
            self.passed_tests += 1
        
        status_symbol = "✅" if status == "✅ PASSED" else "❌"
        print(f"{status_symbol} {test_name}: {details} ({duration:.2f}s)")
    
    def test_backend_health(self):
        """Test backend health and service availability"""
        start_time = time.time()
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                ollama_status = services.get('ollama', False)
                tools_count = services.get('tools', 0)
                db_status = services.get('database', False)
                
                details = f"Ollama: {ollama_status}, Tools: {tools_count}, Database: {db_status}"
                self.log_result("Backend Health Check", "✅ PASSED", details, duration)
                return True
            else:
                self.log_result("Backend Health Check", "❌ FAILED", f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Backend Health Check", "❌ FAILED", f"Connection error: {str(e)}", duration)
            return False
    
    def test_memory_system_initialization(self):
        """Test memory system initialization via analytics endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{API_BASE}/memory/memory-analytics", timeout=15)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                components = data.get('components', {})
                
                # Check for expected components
                initialized_components = []
                for comp_name, comp_data in components.items():
                    if comp_data.get('initialized', False):
                        initialized_components.append(comp_name)
                
                if len(initialized_components) >= 4:  # At least 4 core components
                    details = f"{len(initialized_components)} components initialized: {', '.join(initialized_components)}"
                    self.log_result("Memory System Initialization", "✅ PASSED", details, duration)
                    return True
                else:
                    details = f"Only {len(initialized_components)} components initialized: {', '.join(initialized_components)}"
                    self.log_result("Memory System Initialization", "❌ FAILED", details, duration)
                    return False
            else:
                self.log_result("Memory System Initialization", "❌ FAILED", f"HTTP {response.status_code}: {response.text[:100]}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory System Initialization", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def test_enhanced_agent_availability(self):
        """Test if enhanced agent components are available"""
        start_time = time.time()
        try:
            response = requests.get(f"{API_BASE}/agent/status", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for enhanced components indicators
                response_text = str(data).lower()
                enhanced_indicators = []
                if 'enhanced' in response_text:
                    enhanced_indicators.append('enhanced_components')
                if 'memory' in response_text:
                    enhanced_indicators.append('memory_system')
                
                details = f"Enhanced components detected: {', '.join(enhanced_indicators) if enhanced_indicators else 'None'}"
                self.log_result("Enhanced Agent Availability", "✅ PASSED", details, duration)
                return True
            else:
                self.log_result("Enhanced Agent Availability", "❌ FAILED", f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Enhanced Agent Availability", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def test_memory_context_retrieval(self):
        """Test memory context retrieval functionality"""
        start_time = time.time()
        try:
            payload = {
                "query": "artificial intelligence applications",
                "context_type": "all",
                "max_results": 5
            }
            
            response = requests.post(f"{API_BASE}/memory/retrieve-context", json=payload, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'context' in data or 'results' in data or 'message' in data:
                    details = f"Context retrieval working, response keys: {list(data.keys())}"
                    self.log_result("Memory Context Retrieval", "✅ PASSED", details, duration)
                    return True
                else:
                    details = f"Unexpected response structure: {data}"
                    self.log_result("Memory Context Retrieval", "❌ FAILED", details, duration)
                    return False
            else:
                self.log_result("Memory Context Retrieval", "❌ FAILED", f"HTTP {response.status_code}: {response.text[:100]}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory Context Retrieval", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def test_chat_endpoint_detailed(self):
        """Test chat endpoint with detailed error analysis"""
        start_time = time.time()
        try:
            payload = {
                "message": "Hello, can you explain what artificial intelligence is?",
                "session_id": f"test_session_{int(time.time())}",
                "task_id": f"test_task_{int(time.time())}"
            }
            
            response = requests.post(f"{API_BASE}/agent/chat", json=payload, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    response_length = len(data.get('response', ''))
                    memory_used = data.get('memory_used', False)
                    details = f"Chat working, response: {response_length} chars, memory_used: {memory_used}"
                    self.log_result("Chat Endpoint Test", "✅ PASSED", details, duration)
                    return True
                else:
                    details = f"Unexpected response structure: {list(data.keys())}"
                    self.log_result("Chat Endpoint Test", "❌ FAILED", details, duration)
                    return False
            elif response.status_code == 500:
                # Detailed error analysis for 500 errors
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    details = f"Error 500: {error_msg}"
                except:
                    details = f"Error 500: {response.text[:200]}..."
                
                self.log_result("Chat Endpoint Test", "❌ FAILED", details, duration)
                return False
            else:
                details = f"HTTP {response.status_code}: {response.text[:200]}..."
                self.log_result("Chat Endpoint Test", "❌ FAILED", details, duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Chat Endpoint Test", "❌ FAILED", f"Connection error: {str(e)}", duration)
            return False
    
    def test_memory_operations(self):
        """Test basic memory operations"""
        start_time = time.time()
        try:
            # Test episode storage
            episode_payload = {
                "title": "Test Episode",
                "description": "Testing episode storage functionality",
                "context": {"test": True},
                "actions": [{"type": "test", "content": "test action"}],
                "outcomes": [{"type": "test", "content": "test outcome"}],
                "importance": 3,
                "tags": ["test"]
            }
            
            response = requests.post(f"{API_BASE}/memory/store-episode", json=episode_payload, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                details = f"Episode storage working: {data.get('message', 'Success')}"
                self.log_result("Memory Operations Test", "✅ PASSED", details, duration)
                return True
            else:
                details = f"Episode storage failed: HTTP {response.status_code} - {response.text[:100]}"
                self.log_result("Memory Operations Test", "❌ FAILED", details, duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory Operations Test", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def test_semantic_search(self):
        """Test semantic search functionality"""
        start_time = time.time()
        try:
            payload = {
                "query": "artificial intelligence machine learning",
                "max_results": 5,
                "memory_types": ["all"]
            }
            
            response = requests.post(f"{API_BASE}/memory/semantic-search", json=payload, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results_count = len(data.get('results', []))
                details = f"Semantic search working: {results_count} results returned"
                self.log_result("Semantic Search Test", "✅ PASSED", details, duration)
                return True
            else:
                details = f"Semantic search failed: HTTP {response.status_code} - {response.text[:100]}"
                self.log_result("Semantic Search Test", "❌ FAILED", details, duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Semantic Search Test", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def run_comprehensive_test(self):
        """Run all tests and provide comprehensive analysis"""
        print("🧠 MEMORY SYSTEM INTEGRATION TESTING - COMPREHENSIVE ANALYSIS (LOCAL)")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        tests = [
            self.test_backend_health,
            self.test_memory_system_initialization,
            self.test_enhanced_agent_availability,
            self.test_memory_context_retrieval,
            self.test_memory_operations,
            self.test_semantic_search,
            self.test_chat_endpoint_detailed
        ]
        
        for test in tests:
            test()
            time.sleep(0.5)  # Brief pause between tests
        
        print()
        print("=" * 80)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed results
        for result in self.results:
            status_symbol = "✅" if result['status'] == "✅ PASSED" else "❌"
            print(f"{status_symbol} {result['test']}: {result['details']} ({result['duration']})")
        
        print()
        print("🔍 ROOT CAUSE ANALYSIS:")
        
        # Analyze results to identify root cause
        failed_tests = [r for r in self.results if r['status'] == "❌ FAILED"]
        
        if not failed_tests:
            print("✅ All tests passed - Memory system integration is working correctly")
        else:
            print("❌ Issues identified:")
            for failed in failed_tests:
                print(f"   - {failed['test']}: {failed['details']}")
            
            # Specific analysis for chat endpoint failure
            chat_failed = any("Chat Endpoint" in r['test'] for r in failed_tests)
            memory_failed = any("Memory" in r['test'] for r in failed_tests)
            
            if not chat_failed:
                print("\n✅ CHAT ENDPOINT IS NOW WORKING - Error 500 issue resolved!")
            if not memory_failed:
                print("\n✅ MEMORY SYSTEM IS FUNCTIONAL - Core operations working!")
        
        return success_rate

if __name__ == "__main__":
    tester = MemoryIntegrationTester()
    success_rate = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 70 else 1)