#!/usr/bin/env python3
"""
Memory System Integration Test for Mitosis Application
Tests the memory system integration to identify why the chat endpoint is failing (Error 500)
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://db80532a-c4d1-4d24-b7d1-05601dfdd999.preview.emergentagent.com"
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
        """Test memory system initialization and component availability"""
        start_time = time.time()
        try:
            response = requests.get(f"{API_BASE}/memory/analytics", timeout=15)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                components = data.get('components', {})
                
                # Check for all 6 expected components
                expected_components = [
                    'WorkingMemory', 'EpisodicMemory', 'SemanticMemory', 
                    'ProceduralMemory', 'EmbeddingService', 'SemanticIndexer'
                ]
                
                found_components = []
                for comp_name, comp_data in components.items():
                    if comp_data.get('initialized', False):
                        found_components.append(comp_name)
                
                if len(found_components) >= 6:
                    details = f"All {len(found_components)} components initialized: {', '.join(found_components)}"
                    self.log_result("Memory System Initialization", "✅ PASSED", details, duration)
                    return True
                else:
                    details = f"Only {len(found_components)}/6 components initialized: {', '.join(found_components)}"
                    self.log_result("Memory System Initialization", "❌ FAILED", details, duration)
                    return False
            else:
                self.log_result("Memory System Initialization", "❌ FAILED", f"HTTP {response.status_code}: {response.text}", duration)
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
                enhanced_indicators = []
                if 'enhanced_agent' in str(data).lower():
                    enhanced_indicators.append('enhanced_agent')
                if 'enhanced_memory' in str(data).lower():
                    enhanced_indicators.append('enhanced_memory')
                if 'enhanced_task_manager' in str(data).lower():
                    enhanced_indicators.append('enhanced_task_manager')
                
                if len(enhanced_indicators) > 0:
                    details = f"Enhanced components detected: {', '.join(enhanced_indicators)}"
                    self.log_result("Enhanced Agent Availability", "✅ PASSED", details, duration)
                    return True
                else:
                    details = "No enhanced components detected in status response"
                    self.log_result("Enhanced Agent Availability", "⚠️ PARTIAL", details, duration)
                    return False
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
            
            response = requests.post(f"{API_BASE}/memory/context", json=payload, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'context' in data or 'results' in data:
                    details = f"Context retrieval working, response structure: {list(data.keys())}"
                    self.log_result("Memory Context Retrieval", "✅ PASSED", details, duration)
                    return True
                else:
                    details = f"Unexpected response structure: {data}"
                    self.log_result("Memory Context Retrieval", "⚠️ PARTIAL", details, duration)
                    return False
            else:
                self.log_result("Memory Context Retrieval", "❌ FAILED", f"HTTP {response.status_code}: {response.text}", duration)
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
                    details = f"Chat working, response length: {len(data.get('response', ''))}"
                    self.log_result("Chat Endpoint Test", "✅ PASSED", details, duration)
                    return True
                else:
                    details = f"Unexpected response structure: {list(data.keys())}"
                    self.log_result("Chat Endpoint Test", "⚠️ PARTIAL", details, duration)
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
            
            response = requests.post(f"{API_BASE}/memory/episodes", json=episode_payload, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                details = "Episode storage working correctly"
                self.log_result("Memory Operations Test", "✅ PASSED", details, duration)
                return True
            else:
                details = f"Episode storage failed: HTTP {response.status_code}"
                self.log_result("Memory Operations Test", "❌ FAILED", details, duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory Operations Test", "❌ FAILED", f"Error: {str(e)}", duration)
            return False
    
    def test_dependency_imports(self):
        """Test for missing dependencies that might cause import errors"""
        start_time = time.time()
        try:
            # Test if we can access the backend logs or error information
            response = requests.get(f"{API_BASE}/agent/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                # If health check passes, basic imports are working
                details = "Basic imports and dependencies appear to be working"
                self.log_result("Dependency Check", "✅ PASSED", details, duration)
                return True
            else:
                details = f"Health check failed, possible dependency issues: HTTP {response.status_code}"
                self.log_result("Dependency Check", "❌ FAILED", details, duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Dependency Check", "❌ FAILED", f"Connection error: {str(e)}", duration)
            return False
    
    def run_comprehensive_test(self):
        """Run all tests and provide comprehensive analysis"""
        print("🧠 MEMORY SYSTEM INTEGRATION TESTING - COMPREHENSIVE ANALYSIS")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        tests = [
            self.test_backend_health,
            self.test_dependency_imports,
            self.test_memory_system_initialization,
            self.test_enhanced_agent_availability,
            self.test_memory_context_retrieval,
            self.test_memory_operations,
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
            status_symbol = "✅" if result['status'] == "✅ PASSED" else "❌" if result['status'] == "❌ FAILED" else "⚠️"
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
            enhanced_failed = any("Enhanced" in r['test'] for r in failed_tests)
            
            if chat_failed:
                print("\n🚨 CHAT ENDPOINT FAILURE ANALYSIS:")
                if memory_failed:
                    print("   - Memory system issues detected - likely cause of chat failure")
                if enhanced_failed:
                    print("   - Enhanced agent components not available - may cause import errors")
                if not memory_failed and not enhanced_failed:
                    print("   - Chat failure appears isolated - check backend logs for specific error")
        
        return success_rate

if __name__ == "__main__":
    tester = MemoryIntegrationTester()
    success_rate = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 80 else 1)