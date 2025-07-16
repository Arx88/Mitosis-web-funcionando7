#!/usr/bin/env python3
"""
Memory Management Methods Testing - Comprehensive Test Suite
Testing the new compress_old_memory and export_memory_data methods
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

class MemoryManagementTester:
    def __init__(self):
        # Get backend URL from frontend .env
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip()
                        break
                else:
                    self.base_url = "http://localhost:8001"
        except:
            self.base_url = "http://localhost:8001"
        
        self.api_base = f"{self.base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, success: bool, duration: float, details: str = ""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = f"{status} ({duration:.2f}s) - {test_name}"
        if details:
            result += f": {details}"
        
        self.test_results.append(result)
        print(result)
        
    def test_backend_health(self) -> bool:
        """Test backend health and memory system availability"""
        print("\n🔍 Testing Backend Health and Memory System...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                details = f"Status: {data.get('status')}, Ollama: {services.get('ollama')}, Tools: {services.get('tools')}, Database: {services.get('database')}"
                self.log_test("Backend Health Check", True, duration, details)
                return True
            else:
                self.log_test("Backend Health Check", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Backend Health Check", False, 0, str(e))
            return False
    
    def test_memory_system_initialization(self) -> bool:
        """Test memory system initialization"""
        print("\n🧠 Testing Memory System Initialization...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.api_base}/agent/memory/stats", timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                system_info = data.get('system_info', {})
                initialized = system_info.get('initialized', False)
                
                if initialized:
                    # Count memory components
                    components = []
                    if 'working_memory' in data:
                        components.append('working_memory')
                    if 'episodic_memory' in data:
                        components.append('episodic_memory')
                    if 'semantic_memory' in data:
                        components.append('semantic_memory')
                    if 'procedural_memory' in data:
                        components.append('procedural_memory')
                    if 'embedding_service' in data:
                        components.append('embedding_service')
                    if 'semantic_indexer' in data:
                        components.append('semantic_indexer')
                    
                    details = f"Initialized: {initialized}, Components: {len(components)} ({', '.join(components)})"
                    self.log_test("Memory System Initialization", True, duration, details)
                    return True
                else:
                    self.log_test("Memory System Initialization", False, duration, "Memory system not initialized")
                    return False
            else:
                self.log_test("Memory System Initialization", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Memory System Initialization", False, 0, str(e))
            return False
    
    def setup_test_memory_data(self) -> bool:
        """Setup some test memory data for compression and export tests"""
        print("\n📝 Setting up test memory data...")
        
        try:
            # Store test episode
            episode_data = {
                "user_query": "Test query for memory compression",
                "agent_response": "Test response for memory compression testing",
                "success": True,
                "context": {
                    "task_type": "test_compression",
                    "complexity": "low",
                    "test_data": True
                },
                "tools_used": ["test_tool"],
                "importance": 2,
                "metadata": {"test": True}
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/memory/store-episode", 
                                       json=episode_data, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                episode_result = response.json()
                episode_id = episode_result.get('episode_id')
                self.log_test("Setup Test Episode", True, duration, f"Episode ID: {episode_id}")
            else:
                self.log_test("Setup Test Episode", False, duration, f"HTTP {response.status_code}")
                return False
            
            # Store test knowledge
            knowledge_data = {
                "content": "Test knowledge for compression testing",
                "type": "fact",
                "subject": "test_compression",
                "predicate": "is_used_for",
                "object": "testing memory compression functionality",
                "confidence": 0.8,
                "context": {"test": True}
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/memory/store-knowledge", 
                                       json=knowledge_data, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                knowledge_result = response.json()
                knowledge_id = knowledge_result.get('knowledge_id')
                self.log_test("Setup Test Knowledge", True, duration, f"Knowledge ID: {knowledge_id}")
            else:
                self.log_test("Setup Test Knowledge", False, duration, f"HTTP {response.status_code}")
                return False
            
            # Store test procedure
            procedure_data = {
                "name": "Test Compression Procedure",
                "description": "A test procedure for compression testing",
                "steps": [
                    {"step": 1, "action": "Initialize test"},
                    {"step": 2, "action": "Execute compression"},
                    {"step": 3, "action": "Verify results"}
                ],
                "category": "test",
                "effectiveness": 0.7,
                "usage_count": 1,
                "metadata": {"test": True}
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/memory/store-procedure", 
                                       json=procedure_data, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                procedure_result = response.json()
                procedure_id = procedure_result.get('procedure_id')
                self.log_test("Setup Test Procedure", True, duration, f"Procedure ID: {procedure_id}")
                return True
            else:
                self.log_test("Setup Test Procedure", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Setup Test Memory Data", False, 0, str(e))
            return False
    
    def test_compress_memory_endpoint(self) -> bool:
        """Test the new /api/agent/memory/compress endpoint"""
        print("\n🗜️ Testing Memory Compression Endpoint...")
        
        try:
            # Test with default parameters
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/agent/memory/compress", 
                                       json={}, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if compression statistics are returned
                if 'compressed_episodes' in data or 'compressed_concepts' in data or 'compressed_facts' in data:
                    details = f"Episodes: {data.get('compressed_episodes', 0)}, Concepts: {data.get('compressed_concepts', 0)}, Facts: {data.get('compressed_facts', 0)}, Procedures: {data.get('compressed_procedures', 0)}"
                    self.log_test("Memory Compression (Default)", True, duration, details)
                else:
                    self.log_test("Memory Compression (Default)", False, duration, "No compression statistics returned")
                    return False
            else:
                self.log_test("Memory Compression (Default)", False, duration, f"HTTP {response.status_code}")
                return False
            
            # Test with custom parameters
            compression_config = {
                "compression_threshold_days": 1,  # Very short threshold for testing
                "compression_ratio": 0.3
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/agent/memory/compress", 
                                       json=compression_config, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check compression results
                total_compressed = (data.get('compressed_episodes', 0) + 
                                  data.get('compressed_concepts', 0) + 
                                  data.get('compressed_facts', 0) + 
                                  data.get('compressed_procedures', 0))
                
                details = f"Total compressed items: {total_compressed}, Space saved: {data.get('total_space_saved_kb', 0):.2f} KB"
                self.log_test("Memory Compression (Custom)", True, duration, details)
                return True
            else:
                self.log_test("Memory Compression (Custom)", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Memory Compression", False, 0, str(e))
            return False
    
    def test_export_memory_endpoint(self) -> bool:
        """Test the new /api/agent/memory/export endpoint"""
        print("\n📤 Testing Memory Export Endpoint...")
        
        try:
            # Test JSON export
            export_config = {
                "export_format": "json",
                "include_compressed": True
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/agent/memory/export", 
                                       json=export_config, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check export structure
                if 'memory_data' in data and 'export_stats' in data:
                    memory_data = data['memory_data']
                    export_stats = data['export_stats']
                    
                    # Verify memory data structure
                    expected_sections = ['working_memory', 'episodic_memory', 'semantic_memory', 'procedural_memory']
                    found_sections = [section for section in expected_sections if section in memory_data]
                    
                    details = f"Format: JSON, Sections: {len(found_sections)}/{len(expected_sections)}, Episodes: {export_stats.get('total_episodes', 0)}, Size: {export_stats.get('export_size_estimate_kb', 0):.2f} KB"
                    self.log_test("Memory Export (JSON)", True, duration, details)
                else:
                    self.log_test("Memory Export (JSON)", False, duration, "Invalid export structure")
                    return False
            else:
                self.log_test("Memory Export (JSON)", False, duration, f"HTTP {response.status_code}")
                return False
            
            # Test CSV export
            export_config = {
                "export_format": "csv",
                "include_compressed": False
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/agent/memory/export", 
                                       json=export_config, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if 'export_stats' in data:
                    export_stats = data['export_stats']
                    details = f"Format: CSV, Episodes: {export_stats.get('total_episodes', 0)}, Concepts: {export_stats.get('total_concepts', 0)}, Facts: {export_stats.get('total_facts', 0)}"
                    self.log_test("Memory Export (CSV)", True, duration, details)
                else:
                    self.log_test("Memory Export (CSV)", False, duration, "No export statistics")
                    return False
            else:
                self.log_test("Memory Export (CSV)", False, duration, f"HTTP {response.status_code}")
                return False
            
            # Test YAML export
            export_config = {
                "export_format": "yaml",
                "include_compressed": True
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/agent/memory/export", 
                                       json=export_config, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if 'metadata' in data and data['metadata'].get('export_format') == 'yaml':
                    export_stats = data.get('export_stats', {})
                    details = f"Format: YAML, Procedures: {export_stats.get('total_procedures', 0)}, Strategies: {export_stats.get('total_strategies', 0)}"
                    self.log_test("Memory Export (YAML)", True, duration, details)
                    return True
                else:
                    self.log_test("Memory Export (YAML)", False, duration, "Invalid YAML export format")
                    return False
            else:
                self.log_test("Memory Export (YAML)", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Memory Export", False, 0, str(e))
            return False
    
    def test_memory_routes_integration(self) -> bool:
        """Test integration between memory routes and agent routes"""
        print("\n🔗 Testing Memory Routes Integration...")
        
        try:
            # Test memory routes compress endpoint
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/memory/compress-memory", 
                                       json={"config": {"compression_threshold_days": 7}}, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    details = f"Compressed items: {data.get('compressed_items', 0)}, Memory saved: {data.get('memory_saved', 0)}"
                    self.log_test("Memory Routes Compress", True, duration, details)
                else:
                    self.log_test("Memory Routes Compress", False, duration, "Compression not successful")
                    return False
            else:
                self.log_test("Memory Routes Compress", False, duration, f"HTTP {response.status_code}")
                return False
            
            # Test memory routes export endpoint
            start_time = time.time()
            response = self.session.get(f"{self.api_base}/memory/export-memory", timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    export_data = data.get('export_data', {})
                    details = f"Export successful, Data sections: {len(export_data.get('memory_data', {}))}"
                    self.log_test("Memory Routes Export", True, duration, details)
                    return True
                else:
                    self.log_test("Memory Routes Export", False, duration, "Export not successful")
                    return False
            else:
                self.log_test("Memory Routes Export", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Memory Routes Integration", False, 0, str(e))
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling for invalid parameters"""
        print("\n⚠️ Testing Error Handling...")
        
        try:
            # Test compress with invalid parameters
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/agent/memory/compress", 
                                       json={"compression_ratio": 2.0}, timeout=10)  # Invalid ratio > 1.0
            duration = time.time() - start_time
            
            # Should still work but handle invalid parameters gracefully
            if response.status_code in [200, 400]:
                self.log_test("Error Handling (Invalid Compress)", True, duration, f"HTTP {response.status_code}")
            else:
                self.log_test("Error Handling (Invalid Compress)", False, duration, f"HTTP {response.status_code}")
                return False
            
            # Test export with invalid format
            start_time = time.time()
            response = self.session.post(f"{self.api_base}/agent/memory/export", 
                                       json={"export_format": "invalid_format"}, timeout=10)
            duration = time.time() - start_time
            
            # Should handle gracefully
            if response.status_code in [200, 400]:
                self.log_test("Error Handling (Invalid Export)", True, duration, f"HTTP {response.status_code}")
                return True
            else:
                self.log_test("Error Handling (Invalid Export)", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling", False, 0, str(e))
            return False
    
    def test_memory_analytics_integration(self) -> bool:
        """Test integration with memory analytics"""
        print("\n📊 Testing Memory Analytics Integration...")
        
        try:
            # Get memory analytics before operations
            start_time = time.time()
            response = self.session.get(f"{self.api_base}/memory/memory-analytics", timeout=15)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check analytics structure
                if 'overview' in data and 'memory_efficiency' in data and 'learning_insights' in data:
                    overview = data['overview']
                    efficiency = data['memory_efficiency']
                    insights = data['learning_insights']
                    
                    details = f"Components tracked: {len(overview)}, Capacity used: {efficiency.get('total_capacity_used', 0)}, Episode success rate: {insights.get('episode_success_rate', 0):.2f}"
                    self.log_test("Memory Analytics Integration", True, duration, details)
                    return True
                else:
                    self.log_test("Memory Analytics Integration", False, duration, "Invalid analytics structure")
                    return False
            else:
                self.log_test("Memory Analytics Integration", False, duration, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Memory Analytics Integration", False, 0, str(e))
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite for memory management methods"""
        print("🧪 MEMORY MANAGEMENT METHODS TESTING - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"🔗 Backend URL: {self.base_url}")
        print(f"📅 Test started: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Test sequence
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Memory System Initialization", self.test_memory_system_initialization),
            ("Setup Test Memory Data", self.setup_test_memory_data),
            ("Memory Compression Endpoint", self.test_compress_memory_endpoint),
            ("Memory Export Endpoint", self.test_export_memory_endpoint),
            ("Memory Routes Integration", self.test_memory_routes_integration),
            ("Error Handling", self.test_error_handling),
            ("Memory Analytics Integration", self.test_memory_analytics_integration)
        ]
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                if not success:
                    print(f"⚠️ Test '{test_name}' failed, but continuing with remaining tests...")
            except Exception as e:
                print(f"❌ Test '{test_name}' crashed: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 MEMORY MANAGEMENT TESTING SUMMARY")
        print("=" * 80)
        
        for result in self.test_results:
            print(result)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.total_tests - self.passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"\n✅ MEMORY MANAGEMENT METHODS: WORKING CORRECTLY ({success_rate:.1f}% success rate)")
            return True
        else:
            print(f"\n❌ MEMORY MANAGEMENT METHODS: ISSUES DETECTED ({success_rate:.1f}% success rate)")
            return False

def main():
    """Main test execution"""
    tester = MemoryManagementTester()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()