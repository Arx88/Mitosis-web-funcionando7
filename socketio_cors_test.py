#!/usr/bin/env python3
"""
SOCKET.IO CORS FIX TESTING
Test the critical Socket.IO CORS fix that was just applied.

SPECIFIC TESTING REQUEST:
Test the critical Socket.IO CORS fix that was just applied. The previous test showed that 
Socket.IO endpoint (/socket.io/) was missing CORS headers. I've now added explicit CORS 
handling for the Socket.IO endpoint with before_request and after_request hooks.

SPECIFIC TESTS NEEDED:
1. Socket.IO CORS Headers: Test /socket.io/ endpoint with Origin header to verify Access-Control-Allow-Origin is returned
2. Socket.IO OPTIONS Preflight: Test OPTIONS request to /socket.io/ to verify preflight CORS headers are returned  
3. WebSocket Connection Simulation: Verify that a WebSocket handshake request to /socket.io/ gets proper CORS headers
4. Origin Validation: Test with the specific frontend origin (https://b3718c6d-d2fa-4fa9-9fbd-4ac26e0c8cc4.preview.emergentagent.com) to ensure it's allowed

CRITICAL CHANGES MADE:
- Added @app.before_request handler for Socket.IO CORS preflight
- Added @app.after_request handler to add CORS headers to Socket.IO responses  
- Explicit CORS headers for Socket.IO: Access-Control-Allow-Origin, Access-Control-Allow-Methods, Access-Control-Allow-Headers

Backend URL: https://b3718c6d-d2fa-4fa9-9fbd-4ac26e0c8cc4.preview.emergentagent.com

Expected Outcome: Socket.IO endpoint should now return proper CORS headers, resolving the 
"Access to XMLHttpRequest has been blocked by CORS policy" error that was preventing WebSocket connections.
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL and frontend origin for CORS testing
BACKEND_URL = "https://b3718c6d-d2fa-4fa9-9fbd-4ac26e0c8cc4.preview.emergentagent.com"
FRONTEND_ORIGIN = "https://b3718c6d-d2fa-4fa9-9fbd-4ac26e0c8cc4.preview.emergentagent.com"
SOCKET_IO_ENDPOINT = f"{BACKEND_URL}/socket.io/"

class SocketIOCORSTester:
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
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)[:500]}...")
    
    def test_socket_io_cors_headers(self) -> bool:
        """Test 1: Socket.IO CORS Headers - Test /socket.io/ endpoint with Origin header"""
        try:
            print(f"\n🔍 Testing Socket.IO endpoint: {SOCKET_IO_ENDPOINT}")
            print(f"🌐 Using Origin header: {FRONTEND_ORIGIN}")
            
            # Create session with Origin header
            headers = {
                'Origin': FRONTEND_ORIGIN,
                'User-Agent': 'Mozilla/5.0 (compatible; CORS-Test/1.0)',
                'Accept': '*/*'
            }
            
            response = requests.get(SOCKET_IO_ENDPOINT, headers=headers, timeout=10)
            
            # Check response status (200 or 400 are both acceptable for Socket.IO)
            status_ok = response.status_code in [200, 400]
            
            # Check CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            # Check if Origin is allowed
            origin_allowed = (
                cors_headers['Access-Control-Allow-Origin'] == FRONTEND_ORIGIN or
                cors_headers['Access-Control-Allow-Origin'] == '*'
            )
            
            # Check if required headers are present
            has_cors_headers = cors_headers['Access-Control-Allow-Origin'] is not None
            
            print(f"   Status Code: {response.status_code}")
            print(f"   CORS Headers: {cors_headers}")
            
            if status_ok and origin_allowed and has_cors_headers:
                self.log_test("Socket.IO CORS Headers", True, 
                            f"Socket.IO CORS headers working - Status: {response.status_code}, Origin allowed: {origin_allowed}")
                return True
            else:
                self.log_test("Socket.IO CORS Headers", False, 
                            f"Socket.IO CORS headers missing - Status OK: {status_ok}, Origin allowed: {origin_allowed}, Has CORS: {has_cors_headers}", 
                            {'status': response.status_code, 'headers': dict(response.headers)})
                return False
                
        except Exception as e:
            self.log_test("Socket.IO CORS Headers", False, f"Exception: {str(e)}")
            return False
    
    def test_socket_io_options_preflight(self) -> bool:
        """Test 2: Socket.IO OPTIONS Preflight - Test OPTIONS request to /socket.io/"""
        try:
            print(f"\n🔍 Testing Socket.IO OPTIONS preflight: {SOCKET_IO_ENDPOINT}")
            
            # Create OPTIONS request with CORS headers
            headers = {
                'Origin': FRONTEND_ORIGIN,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type, Authorization, Accept, Origin, X-Requested-With',
                'User-Agent': 'Mozilla/5.0 (compatible; CORS-Test/1.0)'
            }
            
            response = requests.options(SOCKET_IO_ENDPOINT, headers=headers, timeout=10)
            
            # Check response status (200, 204, or 400 are acceptable for OPTIONS)
            status_ok = response.status_code in [200, 204, 400]
            
            # Check CORS preflight headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            # Check if Origin is allowed
            origin_allowed = (
                cors_headers['Access-Control-Allow-Origin'] == FRONTEND_ORIGIN or
                cors_headers['Access-Control-Allow-Origin'] == '*'
            )
            
            # Check if required methods are allowed
            methods_allowed = cors_headers['Access-Control-Allow-Methods'] is not None
            headers_allowed = cors_headers['Access-Control-Allow-Headers'] is not None
            
            print(f"   Status Code: {response.status_code}")
            print(f"   CORS Headers: {cors_headers}")
            
            if status_ok and origin_allowed and methods_allowed:
                self.log_test("Socket.IO OPTIONS Preflight", True, 
                            f"Socket.IO OPTIONS preflight working - Status: {response.status_code}, Origin: {origin_allowed}, Methods: {methods_allowed}")
                return True
            else:
                self.log_test("Socket.IO OPTIONS Preflight", False, 
                            f"Socket.IO OPTIONS preflight failed - Status OK: {status_ok}, Origin: {origin_allowed}, Methods: {methods_allowed}", 
                            {'status': response.status_code, 'headers': dict(response.headers)})
                return False
                
        except Exception as e:
            self.log_test("Socket.IO OPTIONS Preflight", False, f"Exception: {str(e)}")
            return False
    
    def test_websocket_handshake_simulation(self) -> bool:
        """Test 3: WebSocket Connection Simulation - Verify WebSocket handshake gets proper CORS headers"""
        try:
            print(f"\n🔍 Testing WebSocket handshake simulation")
            
            # Simulate WebSocket handshake request
            headers = {
                'Origin': FRONTEND_ORIGIN,
                'Connection': 'Upgrade',
                'Upgrade': 'websocket',
                'Sec-WebSocket-Version': '13',
                'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
                'User-Agent': 'Mozilla/5.0 (compatible; WebSocket-Test/1.0)'
            }
            
            # Test with Socket.IO transport parameter
            websocket_url = f"{SOCKET_IO_ENDPOINT}?transport=websocket"
            
            response = requests.get(websocket_url, headers=headers, timeout=10)
            
            # Check response (may not upgrade but should have CORS headers)
            status_acceptable = response.status_code in [200, 400, 426, 501]  # Various acceptable responses
            
            # Check CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            # Check if Origin is allowed
            origin_allowed = (
                cors_headers['Access-Control-Allow-Origin'] == FRONTEND_ORIGIN or
                cors_headers['Access-Control-Allow-Origin'] == '*'
            )
            
            has_cors_headers = cors_headers['Access-Control-Allow-Origin'] is not None
            
            print(f"   Status Code: {response.status_code}")
            print(f"   CORS Headers: {cors_headers}")
            
            if status_acceptable and origin_allowed and has_cors_headers:
                self.log_test("WebSocket Handshake Simulation", True, 
                            f"WebSocket handshake CORS working - Status: {response.status_code}, Origin allowed: {origin_allowed}")
                return True
            else:
                self.log_test("WebSocket Handshake Simulation", False, 
                            f"WebSocket handshake CORS failed - Status OK: {status_acceptable}, Origin: {origin_allowed}, CORS: {has_cors_headers}", 
                            {'status': response.status_code, 'headers': dict(response.headers)})
                return False
                
        except Exception as e:
            self.log_test("WebSocket Handshake Simulation", False, f"Exception: {str(e)}")
            return False
    
    def test_origin_validation(self) -> bool:
        """Test 4: Origin Validation - Test with specific frontend origin to ensure it's allowed"""
        try:
            print(f"\n🔍 Testing origin validation with frontend origin")
            
            # Test with the exact frontend origin
            test_origins = [
                FRONTEND_ORIGIN,
                "https://b3718c6d-d2fa-4fa9-9fbd-4ac26e0c8cc4.preview.emergentagent.com",  # Alternative origin
                "http://localhost:3000",  # Development origin
                "https://invalid-origin.com"  # Should be rejected or handled gracefully
            ]
            
            results = {}
            
            for origin in test_origins:
                headers = {'Origin': origin}
                
                try:
                    response = requests.get(SOCKET_IO_ENDPOINT, headers=headers, timeout=5)
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    
                    # Check if origin is allowed
                    origin_allowed = (cors_origin == origin or cors_origin == '*')
                    
                    results[origin] = {
                        'status': response.status_code,
                        'cors_origin': cors_origin,
                        'allowed': origin_allowed
                    }
                    
                    print(f"   Origin: {origin} -> CORS: {cors_origin}, Allowed: {origin_allowed}")
                    
                except Exception as e:
                    results[origin] = {'error': str(e), 'allowed': False}
                    print(f"   Origin: {origin} -> Error: {str(e)}")
            
            # Check if the main frontend origin is allowed
            main_origin_result = results.get(FRONTEND_ORIGIN, {})
            main_origin_allowed = main_origin_result.get('allowed', False)
            
            # Check if at least the main origin works
            if main_origin_allowed:
                allowed_count = sum(1 for r in results.values() if r.get('allowed', False))
                self.log_test("Origin Validation", True, 
                            f"Origin validation working - Main origin allowed: {main_origin_allowed}, Total allowed: {allowed_count}/{len(test_origins)}")
                return True
            else:
                self.log_test("Origin Validation", False, 
                            f"Origin validation failed - Main origin not allowed: {main_origin_allowed}", results)
                return False
                
        except Exception as e:
            self.log_test("Origin Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_socket_io_polling_transport(self) -> bool:
        """Test 5: Socket.IO Polling Transport - Test polling transport with CORS"""
        try:
            print(f"\n🔍 Testing Socket.IO polling transport")
            
            # Test Socket.IO polling transport
            polling_url = f"{SOCKET_IO_ENDPOINT}?transport=polling"
            
            headers = {
                'Origin': FRONTEND_ORIGIN,
                'Content-Type': 'text/plain;charset=UTF-8',
                'Accept': '*/*'
            }
            
            response = requests.get(polling_url, headers=headers, timeout=10)
            
            # Check response status
            status_ok = response.status_code in [200, 400]
            
            # Check CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            origin_allowed = (
                cors_headers['Access-Control-Allow-Origin'] == FRONTEND_ORIGIN or
                cors_headers['Access-Control-Allow-Origin'] == '*'
            )
            
            has_cors_headers = cors_headers['Access-Control-Allow-Origin'] is not None
            
            print(f"   Status Code: {response.status_code}")
            print(f"   CORS Headers: {cors_headers}")
            print(f"   Response Length: {len(response.text)} chars")
            
            if status_ok and origin_allowed and has_cors_headers:
                self.log_test("Socket.IO Polling Transport", True, 
                            f"Socket.IO polling CORS working - Status: {response.status_code}, Origin allowed: {origin_allowed}")
                return True
            else:
                self.log_test("Socket.IO Polling Transport", False, 
                            f"Socket.IO polling CORS failed - Status OK: {status_ok}, Origin: {origin_allowed}, CORS: {has_cors_headers}", 
                            {'status': response.status_code, 'headers': dict(response.headers)})
                return False
                
        except Exception as e:
            self.log_test("Socket.IO Polling Transport", False, f"Exception: {str(e)}")
            return False
    
    def test_cors_fix_verification(self) -> bool:
        """Test 6: CORS Fix Verification - Comprehensive verification of the CORS fix"""
        try:
            print(f"\n🔍 Testing comprehensive CORS fix verification")
            
            # Test multiple scenarios that would have failed before the fix
            test_scenarios = [
                {
                    'name': 'Basic GET with Origin',
                    'method': 'GET',
                    'url': SOCKET_IO_ENDPOINT,
                    'headers': {'Origin': FRONTEND_ORIGIN}
                },
                {
                    'name': 'OPTIONS Preflight',
                    'method': 'OPTIONS',
                    'url': SOCKET_IO_ENDPOINT,
                    'headers': {
                        'Origin': FRONTEND_ORIGIN,
                        'Access-Control-Request-Method': 'GET',
                        'Access-Control-Request-Headers': 'Content-Type'
                    }
                },
                {
                    'name': 'POST with Origin',
                    'method': 'POST',
                    'url': SOCKET_IO_ENDPOINT,
                    'headers': {
                        'Origin': FRONTEND_ORIGIN,
                        'Content-Type': 'application/json'
                    }
                }
            ]
            
            results = {}
            
            for scenario in test_scenarios:
                try:
                    if scenario['method'] == 'GET':
                        response = requests.get(scenario['url'], headers=scenario['headers'], timeout=5)
                    elif scenario['method'] == 'OPTIONS':
                        response = requests.options(scenario['url'], headers=scenario['headers'], timeout=5)
                    elif scenario['method'] == 'POST':
                        response = requests.post(scenario['url'], headers=scenario['headers'], timeout=5)
                    
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    origin_allowed = (cors_origin == FRONTEND_ORIGIN or cors_origin == '*')
                    
                    results[scenario['name']] = {
                        'status': response.status_code,
                        'cors_origin': cors_origin,
                        'allowed': origin_allowed,
                        'success': origin_allowed and response.status_code in [200, 204, 400]
                    }
                    
                    print(f"   {scenario['name']}: Status {response.status_code}, CORS: {cors_origin}, Allowed: {origin_allowed}")
                    
                except Exception as e:
                    results[scenario['name']] = {'error': str(e), 'success': False}
                    print(f"   {scenario['name']}: Error - {str(e)}")
            
            # Check if all scenarios pass
            successful_scenarios = sum(1 for r in results.values() if r.get('success', False))
            total_scenarios = len(test_scenarios)
            
            if successful_scenarios >= 2:  # At least 2 out of 3 should work
                self.log_test("CORS Fix Verification", True, 
                            f"CORS fix verification successful - {successful_scenarios}/{total_scenarios} scenarios working")
                return True
            else:
                self.log_test("CORS Fix Verification", False, 
                            f"CORS fix verification failed - Only {successful_scenarios}/{total_scenarios} scenarios working", results)
                return False
                
        except Exception as e:
            self.log_test("CORS Fix Verification", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Socket.IO CORS tests"""
        print("🧪 STARTING SOCKET.IO CORS FIX TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing critical Socket.IO CORS fix")
        print("📋 TESTING: Socket.IO CORS headers, OPTIONS preflight, WebSocket handshake, origin validation")
        print(f"🌐 FRONTEND ORIGIN: {FRONTEND_ORIGIN}")
        print(f"🔗 SOCKET.IO ENDPOINT: {SOCKET_IO_ENDPOINT}")
        print("=" * 80)
        
        # Test sequence focused on Socket.IO CORS
        tests = [
            ("Socket.IO CORS Headers", self.test_socket_io_cors_headers),
            ("Socket.IO OPTIONS Preflight", self.test_socket_io_options_preflight),
            ("WebSocket Handshake Simulation", self.test_websocket_handshake_simulation),
            ("Origin Validation", self.test_origin_validation),
            ("Socket.IO Polling Transport", self.test_socket_io_polling_transport),
            ("CORS Fix Verification", self.test_cors_fix_verification)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 80)
        print("🎯 SOCKET.IO CORS FIX TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ SOCKET.IO CORS FIX WORKING PERFECTLY"
        elif success_rate >= 70:
            overall_status = "⚠️ SOCKET.IO CORS MOSTLY WORKING - Minor issues detected"
        elif success_rate >= 50:
            overall_status = "⚠️ SOCKET.IO CORS PARTIAL - Significant issues found"
        else:
            overall_status = "❌ SOCKET.IO CORS CRITICAL - Major issues preventing functionality"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for Socket.IO CORS
        critical_tests = ["Socket.IO CORS Headers", "Socket.IO OPTIONS Preflight", "Origin Validation"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL SOCKET.IO CORS FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical Socket.IO CORS functionality is working")
            print("   🎯 CONCLUSION: Socket.IO CORS fix is successful - WebSocket connections should work")
        else:
            print("   ❌ Some critical Socket.IO CORS functionality is not working")
            print("   🎯 CONCLUSION: Socket.IO CORS fix needs additional work")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'cors_fix_working': critical_passed >= 2,  # If 2+ critical tests pass, CORS fix is working
            'websocket_ready': critical_passed == len(critical_tests)  # All critical tests must pass for WebSocket readiness
        }

def main():
    """Main testing function"""
    tester = SocketIOCORSTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/socketio_cors_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT FOR MAIN AGENT")
    print("=" * 80)
    
    if results['websocket_ready']:
        print("✅ SOCKET.IO CORS DIAGNOSIS: Socket.IO CORS fix is working perfectly")
        print("📋 RECOMMENDATION: WebSocket connections should now work without CORS policy errors")
        print("🔧 NEXT STEPS: Frontend WebSocket connections should be able to connect successfully")
        print("🎉 SUCCESS: The 'Access to XMLHttpRequest has been blocked by CORS policy' error should be resolved")
    elif results['cors_fix_working']:
        print("⚠️ SOCKET.IO CORS DIAGNOSIS: Socket.IO CORS fix is mostly working but has minor issues")
        print("📋 RECOMMENDATION: Most WebSocket functionality should work, but some edge cases may fail")
        print("🔧 NEXT STEPS: Test frontend WebSocket connections and address any remaining issues")
    else:
        print("❌ SOCKET.IO CORS DIAGNOSIS: Socket.IO CORS fix is not working properly")
        print("📋 RECOMMENDATION: WebSocket connections will likely still fail with CORS policy errors")
        print("🔧 NEXT STEPS: Review and fix the Socket.IO CORS configuration")
    
    # Specific findings
    print(f"\n🔍 SPECIFIC FINDINGS:")
    
    cors_headers_result = next((r for r in results['test_results'] if r['test_name'] == 'Socket.IO CORS Headers'), None)
    if cors_headers_result and cors_headers_result['success']:
        print("   ✅ Socket.IO endpoint returns proper CORS headers with Origin")
    elif cors_headers_result:
        print("   ❌ Socket.IO endpoint missing CORS headers or not allowing Origin")
    
    options_result = next((r for r in results['test_results'] if r['test_name'] == 'Socket.IO OPTIONS Preflight'), None)
    if options_result and options_result['success']:
        print("   ✅ Socket.IO OPTIONS preflight requests work correctly")
    elif options_result:
        print("   ❌ Socket.IO OPTIONS preflight requests failing")
    
    origin_result = next((r for r in results['test_results'] if r['test_name'] == 'Origin Validation'), None)
    if origin_result and origin_result['success']:
        print("   ✅ Frontend origin is properly validated and allowed")
    elif origin_result:
        print("   ❌ Frontend origin validation issues detected")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 SOCKET.IO CORS TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ SOCKET.IO CORS TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)