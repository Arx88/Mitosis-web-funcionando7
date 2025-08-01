#!/usr/bin/env python3
"""
CORS FIX VERIFICATION - TARGETED TESTING
Verify that the CORS fix is working for backend endpoints and identify the Socket.IO routing issue.

Based on initial testing, we found:
1. CORS fix IS working for /api/* endpoints
2. Socket.IO infrastructure is initialized in backend
3. Issue: /socket.io/ path is being intercepted by frontend static serving

This test will verify the CORS fix effectiveness and provide clear diagnosis.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

BACKEND_URL = "https://f600a693-ea20-43b9-acb6-e8ada4e31f8a.preview.emergentagent.com"
FRONTEND_ORIGIN = "https://f600a693-ea20-43b9-acb6-e8ada4e31f8a.preview.emergentagent.com"

class CORSFixVerificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
    
    def test_api_cors_headers(self) -> bool:
        """Test 1: API CORS Headers - Verify CORS fix works for /api/* endpoints"""
        try:
            print(f"\n🔍 Testing API CORS headers with Origin: {FRONTEND_ORIGIN}")
            
            # Test multiple API endpoints
            api_endpoints = [
                '/api/health',
                '/api/agent/status', 
                '/api/agent/websocket-test/test-task',
                '/api/test-cors'
            ]
            
            cors_working_count = 0
            total_endpoints = len(api_endpoints)
            
            for endpoint in api_endpoints:
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", 
                                          headers={'Origin': FRONTEND_ORIGIN}, timeout=10)
                    
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    cors_methods = response.headers.get('Access-Control-Allow-Methods')
                    cors_headers = response.headers.get('Access-Control-Allow-Headers')
                    
                    # Check if CORS is working
                    origin_allowed = (cors_origin == FRONTEND_ORIGIN or cors_origin == '*')
                    has_cors_headers = cors_origin is not None
                    
                    if origin_allowed and has_cors_headers:
                        cors_working_count += 1
                        print(f"   ✅ {endpoint}: CORS working (Origin: {cors_origin})")
                    else:
                        print(f"   ❌ {endpoint}: CORS not working (Origin: {cors_origin})")
                        
                except Exception as e:
                    print(f"   ❌ {endpoint}: Error - {str(e)}")
            
            success_rate = (cors_working_count / total_endpoints) * 100
            
            if cors_working_count >= 3:  # At least 3 out of 4 should work
                self.log_test("API CORS Headers", True, 
                            f"API CORS headers working - {cors_working_count}/{total_endpoints} endpoints ({success_rate:.1f}%)")
                return True
            else:
                self.log_test("API CORS Headers", False, 
                            f"API CORS headers not working properly - Only {cors_working_count}/{total_endpoints} endpoints working")
                return False
                
        except Exception as e:
            self.log_test("API CORS Headers", False, f"Exception: {str(e)}")
            return False
    
    def test_api_options_preflight(self) -> bool:
        """Test 2: API OPTIONS Preflight - Test CORS preflight for API endpoints"""
        try:
            print(f"\n🔍 Testing API OPTIONS preflight")
            
            # Test OPTIONS requests to API endpoints
            api_endpoints = [
                '/api/agent/chat',
                '/api/agent/generate-plan',
                '/api/test-cors'
            ]
            
            preflight_working_count = 0
            
            for endpoint in api_endpoints:
                try:
                    headers = {
                        'Origin': FRONTEND_ORIGIN,
                        'Access-Control-Request-Method': 'POST',
                        'Access-Control-Request-Headers': 'Content-Type, Authorization'
                    }
                    
                    response = requests.options(f"{BACKEND_URL}{endpoint}", 
                                              headers=headers, timeout=10)
                    
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    cors_methods = response.headers.get('Access-Control-Allow-Methods')
                    
                    origin_allowed = (cors_origin == FRONTEND_ORIGIN or cors_origin == '*')
                    methods_allowed = cors_methods is not None
                    
                    if origin_allowed and methods_allowed:
                        preflight_working_count += 1
                        print(f"   ✅ {endpoint}: OPTIONS preflight working")
                    else:
                        print(f"   ❌ {endpoint}: OPTIONS preflight not working")
                        
                except Exception as e:
                    print(f"   ❌ {endpoint}: Error - {str(e)}")
            
            if preflight_working_count >= 2:  # At least 2 out of 3 should work
                self.log_test("API OPTIONS Preflight", True, 
                            f"API OPTIONS preflight working - {preflight_working_count}/{len(api_endpoints)} endpoints")
                return True
            else:
                self.log_test("API OPTIONS Preflight", False, 
                            f"API OPTIONS preflight not working - Only {preflight_working_count}/{len(api_endpoints)} endpoints working")
                return False
                
        except Exception as e:
            self.log_test("API OPTIONS Preflight", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_infrastructure(self) -> bool:
        """Test 3: WebSocket Infrastructure - Verify WebSocket backend is initialized"""
        try:
            print(f"\n🔍 Testing WebSocket infrastructure")
            
            # Test WebSocket test endpoint
            response = requests.get(f"{BACKEND_URL}/api/agent/websocket-test/test-task", 
                                  headers={'Origin': FRONTEND_ORIGIN}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                websocket_initialized = data.get('websocket_initialized', False)
                active_connections = data.get('active_connections', {})
                total_connections = data.get('total_connections', 0)
                
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                origin_allowed = (cors_origin == FRONTEND_ORIGIN or cors_origin == '*')
                
                if websocket_initialized and origin_allowed:
                    self.log_test("WebSocket Infrastructure", True, 
                                f"WebSocket infrastructure working - Initialized: {websocket_initialized}, CORS: {origin_allowed}")
                    return True
                else:
                    self.log_test("WebSocket Infrastructure", False, 
                                f"WebSocket infrastructure issues - Initialized: {websocket_initialized}, CORS: {origin_allowed}", data)
                    return False
            else:
                self.log_test("WebSocket Infrastructure", False, 
                            f"WebSocket test endpoint failed - Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Infrastructure", False, f"Exception: {str(e)}")
            return False
    
    def test_socket_io_path_routing(self) -> bool:
        """Test 4: Socket.IO Path Routing - Diagnose Socket.IO path routing issue"""
        try:
            print(f"\n🔍 Testing Socket.IO path routing")
            
            # Test various Socket.IO paths to understand routing
            socket_paths = [
                '/socket.io/',
                '/socket.io/?transport=polling',
                '/api/socket.io/',
                '/api/socket.io/?transport=polling'
            ]
            
            routing_results = {}
            
            for path in socket_paths:
                try:
                    response = requests.get(f"{BACKEND_URL}{path}", 
                                          headers={'Origin': FRONTEND_ORIGIN}, timeout=5)
                    
                    content_type = response.headers.get('Content-Type', '')
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    
                    # Determine if this is hitting backend or frontend
                    is_backend_response = (
                        content_type.startswith('application/json') or
                        'socket.io' in response.text.lower() or
                        response.status_code == 400  # Socket.IO often returns 400 for invalid requests
                    )
                    
                    is_frontend_response = content_type.startswith('text/html')
                    
                    routing_results[path] = {
                        'status': response.status_code,
                        'content_type': content_type,
                        'cors_origin': cors_origin,
                        'is_backend': is_backend_response,
                        'is_frontend': is_frontend_response,
                        'response_length': len(response.text)
                    }
                    
                    backend_indicator = "🔧 Backend" if is_backend_response else "🌐 Frontend"
                    cors_indicator = f"CORS: {cors_origin}" if cors_origin else "No CORS"
                    
                    print(f"   {path}: {backend_indicator}, Status: {response.status_code}, {cors_indicator}")
                    
                except Exception as e:
                    routing_results[path] = {'error': str(e)}
                    print(f"   {path}: Error - {str(e)}")
            
            # Check if any Socket.IO path reaches the backend
            backend_paths = [path for path, result in routing_results.items() 
                           if result.get('is_backend', False)]
            
            if len(backend_paths) > 0:
                self.log_test("Socket.IO Path Routing", True, 
                            f"Socket.IO routing partially working - {len(backend_paths)} paths reach backend: {backend_paths}")
                return True
            else:
                self.log_test("Socket.IO Path Routing", False, 
                            f"Socket.IO routing not working - All paths serve frontend static files", routing_results)
                return False
                
        except Exception as e:
            self.log_test("Socket.IO Path Routing", False, f"Exception: {str(e)}")
            return False
    
    def test_cors_fix_effectiveness(self) -> bool:
        """Test 5: CORS Fix Effectiveness - Overall assessment of CORS fix"""
        try:
            print(f"\n🔍 Testing overall CORS fix effectiveness")
            
            # Test a real API call that would be used by frontend
            chat_payload = {"message": "Test CORS fix"}
            
            response = requests.post(f"{BACKEND_URL}/api/agent/chat", 
                                   json=chat_payload,
                                   headers={'Origin': FRONTEND_ORIGIN}, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                
                # Check if response is valid and CORS is working
                has_response = 'response' in data or 'task_id' in data
                origin_allowed = (cors_origin == FRONTEND_ORIGIN or cors_origin == '*')
                
                if has_response and origin_allowed:
                    self.log_test("CORS Fix Effectiveness", True, 
                                f"CORS fix effective - API calls work with proper CORS headers")
                    return True
                else:
                    self.log_test("CORS Fix Effectiveness", False, 
                                f"CORS fix not effective - Response: {has_response}, CORS: {origin_allowed}", data)
                    return False
            else:
                self.log_test("CORS Fix Effectiveness", False, 
                            f"CORS fix not effective - API call failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("CORS Fix Effectiveness", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all CORS fix verification tests"""
        print("🧪 STARTING CORS FIX VERIFICATION TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Verify CORS fix effectiveness and diagnose Socket.IO routing")
        print("📋 TESTING: API CORS, OPTIONS preflight, WebSocket infrastructure, Socket.IO routing")
        print(f"🌐 FRONTEND ORIGIN: {FRONTEND_ORIGIN}")
        print("=" * 80)
        
        tests = [
            ("API CORS Headers", self.test_api_cors_headers),
            ("API OPTIONS Preflight", self.test_api_options_preflight),
            ("WebSocket Infrastructure", self.test_websocket_infrastructure),
            ("Socket.IO Path Routing", self.test_socket_io_path_routing),
            ("CORS Fix Effectiveness", self.test_cors_fix_effectiveness)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(1)
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 80)
        print("🎯 CORS FIX VERIFICATION TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine CORS fix status
        api_cors_working = any(r['test_name'] == 'API CORS Headers' and r['success'] for r in self.test_results)
        websocket_infrastructure_working = any(r['test_name'] == 'WebSocket Infrastructure' and r['success'] for r in self.test_results)
        cors_effectiveness = any(r['test_name'] == 'CORS Fix Effectiveness' and r['success'] for r in self.test_results)
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'test_results': self.test_results,
            'api_cors_working': api_cors_working,
            'websocket_infrastructure_working': websocket_infrastructure_working,
            'cors_fix_effective': cors_effectiveness,
            'socket_io_routing_issue': not any(r['test_name'] == 'Socket.IO Path Routing' and r['success'] for r in self.test_results)
        }

def main():
    """Main testing function"""
    tester = CORSFixVerificationTester()
    results = tester.run_all_tests()
    
    # Save results
    results_file = '/app/cors_fix_verification_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL CORS FIX ASSESSMENT")
    print("=" * 80)
    
    if results['api_cors_working'] and results['cors_fix_effective']:
        print("✅ CORS FIX STATUS: CORS fix is working correctly for API endpoints")
        print("📋 FINDING: The CORS configuration changes are effective")
        print("🔧 API COMMUNICATION: Frontend can communicate with backend APIs without CORS errors")
    else:
        print("❌ CORS FIX STATUS: CORS fix is not working properly")
        print("📋 FINDING: CORS configuration needs additional work")
    
    if results['websocket_infrastructure_working']:
        print("✅ WEBSOCKET BACKEND: WebSocket infrastructure is initialized and working")
        print("📋 FINDING: Backend WebSocket system is ready for connections")
    else:
        print("❌ WEBSOCKET BACKEND: WebSocket infrastructure has issues")
    
    if results['socket_io_routing_issue']:
        print("⚠️ SOCKET.IO ROUTING: Socket.IO endpoints are being intercepted by frontend static serving")
        print("📋 FINDING: /socket.io/ path is not reaching the Socket.IO server")
        print("🔧 SOLUTION NEEDED: Configure routing to allow Socket.IO endpoints to reach backend")
    else:
        print("✅ SOCKET.IO ROUTING: Socket.IO endpoints are accessible")
    
    # Overall conclusion
    print(f"\n🎯 OVERALL CONCLUSION:")
    
    if results['api_cors_working'] and results['websocket_infrastructure_working']:
        if results['socket_io_routing_issue']:
            print("⚠️ CORS FIX PARTIALLY SUCCESSFUL:")
            print("   ✅ CORS headers are working correctly for API endpoints")
            print("   ✅ WebSocket backend infrastructure is ready")
            print("   ❌ Socket.IO endpoints are not accessible due to routing issues")
            print("   🔧 NEXT STEP: Fix Socket.IO endpoint routing to complete the fix")
        else:
            print("✅ CORS FIX FULLY SUCCESSFUL:")
            print("   ✅ All CORS headers are working correctly")
            print("   ✅ WebSocket connections should work without CORS errors")
    else:
        print("❌ CORS FIX NOT SUCCESSFUL:")
        print("   ❌ CORS configuration needs additional work")
        print("   🔧 NEXT STEP: Review and fix CORS configuration")
    
    return 0 if results['success_rate'] >= 60 else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)