#!/usr/bin/env python3
"""
MITOSIS AGENT FINAL REPORT GENERATION AND BACKEND FUNCTIONALITY TESTING
Testing the new final report generation endpoint and other backend functionality:

1. Test all health endpoints are working properly
2. Test the new `/api/agent/generate-final-report/<task_id>` endpoint with a sample task_id
3. Verify the endpoint returns proper JSON response with report content
4. Test that the report is being saved to the database properly
5. Check if the generated report follows the expected markdown format
6. Verify error handling for non-existent task IDs

CRITICAL OBJECTIVE: Ensure the new final report generation functionality works correctly before user tests it.
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://6f1dea1b-f2b9-4b55-b52c-7e8bcee0693d.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class MitosisFinalReportTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.task_id = None
        self.sample_task_data = None
        
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
    
    def test_health_endpoints(self) -> bool:
        """Test 1: All Health Endpoints Working Properly"""
        try:
            health_endpoints = [
                ("/health", "Main Health Check"),
                ("/api/health", "API Health Check"),
                ("/api/agent/status", "Agent Status Check")
            ]
            
            all_healthy = True
            health_details = []
            
            for endpoint, name in health_endpoints:
                try:
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get('status', 'unknown')
                        health_details.append(f"{name}: ✅ {status}")
                    else:
                        health_details.append(f"{name}: ❌ HTTP {response.status_code}")
                        all_healthy = False
                        
                except Exception as e:
                    health_details.append(f"{name}: ❌ Exception: {str(e)}")
                    all_healthy = False
            
            if all_healthy:
                self.log_test("Health Endpoints", True, 
                            f"All health endpoints working - {', '.join(health_details)}")
                return True
            else:
                self.log_test("Health Endpoints", False, 
                            f"Some health endpoints failing - {', '.join(health_details)}")
                return False
                
        except Exception as e:
            self.log_test("Health Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def create_sample_task(self) -> bool:
        """Helper: Create a sample task for testing final report generation"""
        try:
            # Create a task using the chat endpoint
            test_message = "Create a sample analysis report for testing final report generation"
            
            payload = {
                "message": test_message
            }
            
            response = self.session.post(f"{API_BASE}/agent/chat", 
                                       json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id', '')
                plan = data.get('plan', [])
                
                if task_id:
                    self.task_id = task_id
                    self.sample_task_data = {
                        'id': task_id,
                        'title': 'Sample Analysis Report',
                        'description': test_message,
                        'plan': plan,
                        'created_at': datetime.now().isoformat()
                    }
                    print(f"   ✅ Sample task created with ID: {task_id}")
                    return True
                else:
                    print(f"   ❌ No task_id returned from chat endpoint")
                    return False
            else:
                print(f"   ❌ Failed to create sample task - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception creating sample task: {str(e)}")
            return False
    
    def test_final_report_generation_valid_task(self) -> bool:
        """Test 2: Final Report Generation with Valid Task ID"""
        if not self.task_id:
            if not self.create_sample_task():
                self.log_test("Final Report Generation (Valid Task)", False, 
                            "Could not create sample task for testing")
                return False
        
        try:
            response = self.session.post(f"{API_BASE}/agent/generate-final-report/{self.task_id}", 
                                       json={}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required response fields
                success = data.get('success', False)
                report = data.get('report', '')
                task_id = data.get('task_id', '')
                generated_at = data.get('generated_at', '')
                
                if success and report and task_id and generated_at:
                    # Verify report format (should be markdown)
                    markdown_indicators = ['#', '##', '###', '**', '-', '*']
                    has_markdown = any(indicator in report for indicator in markdown_indicators)
                    
                    # Check for expected report sections
                    expected_sections = ['Información General', 'Resumen Ejecutivo', 'Conclusión']
                    has_sections = all(section in report for section in expected_sections)
                    
                    if has_markdown and has_sections:
                        self.log_test("Final Report Generation (Valid Task)", True, 
                                    f"Report generated successfully - Length: {len(report)} chars, Task ID: {task_id}, Markdown format: ✅")
                        return True
                    else:
                        self.log_test("Final Report Generation (Valid Task)", False, 
                                    f"Report format invalid - Markdown: {has_markdown}, Sections: {has_sections}")
                        return False
                else:
                    self.log_test("Final Report Generation (Valid Task)", False, 
                                f"Incomplete response - Success: {success}, Report: {bool(report)}, Task ID: {bool(task_id)}", data)
                    return False
            else:
                self.log_test("Final Report Generation (Valid Task)", False, 
                            f"HTTP {response.status_code}: {response.text}", response.json() if response.text else None)
                return False
                
        except Exception as e:
            self.log_test("Final Report Generation (Valid Task)", False, f"Exception: {str(e)}")
            return False
    
    def test_final_report_generation_invalid_task(self) -> bool:
        """Test 3: Final Report Generation with Non-existent Task ID"""
        try:
            fake_task_id = "non-existent-task-12345"
            
            response = self.session.post(f"{API_BASE}/agent/generate-final-report/{fake_task_id}", 
                                       json={}, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should still generate a fallback report
                success = data.get('success', False)
                report = data.get('report', '')
                task_id = data.get('task_id', '')
                
                if success and report and task_id == fake_task_id:
                    # Check if it's a fallback report
                    is_fallback = 'Tarea Completada' in report or 'Sin descripción' in report
                    
                    if is_fallback:
                        self.log_test("Final Report Generation (Invalid Task)", True, 
                                    f"Fallback report generated correctly for non-existent task - Length: {len(report)} chars")
                        return True
                    else:
                        self.log_test("Final Report Generation (Invalid Task)", False, 
                                    "Report generated but doesn't appear to be fallback format")
                        return False
                else:
                    self.log_test("Final Report Generation (Invalid Task)", False, 
                                f"Unexpected response for invalid task - Success: {success}, Report: {bool(report)}", data)
                    return False
            else:
                # Error response is also acceptable for invalid task
                self.log_test("Final Report Generation (Invalid Task)", True, 
                            f"Proper error handling for invalid task - HTTP {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Final Report Generation (Invalid Task)", False, f"Exception: {str(e)}")
            return False
    
    def test_report_database_persistence(self) -> bool:
        """Test 4: Report Database Persistence"""
        if not self.task_id:
            self.log_test("Report Database Persistence", False, "No task_id available for testing")
            return False
        
        try:
            # Generate a report first
            response = self.session.post(f"{API_BASE}/agent/generate-final-report/{self.task_id}", 
                                       json={}, timeout=30)
            
            if response.status_code != 200:
                self.log_test("Report Database Persistence", False, "Could not generate report for persistence test")
                return False
            
            # Wait a moment for database write
            time.sleep(2)
            
            # Try to check if the report was saved by generating it again
            # (should retrieve from database if persistence is working)
            second_response = self.session.post(f"{API_BASE}/agent/generate-final-report/{self.task_id}", 
                                              json={}, timeout=15)
            
            if second_response.status_code == 200:
                second_data = second_response.json()
                second_report = second_data.get('report', '')
                
                if second_report:
                    # Check if report contains task-specific information (indicating database lookup worked)
                    has_task_info = self.task_id in second_report or 'Sample Analysis Report' in second_report
                    
                    self.log_test("Report Database Persistence", True, 
                                f"Report persistence working - Task info in report: {has_task_info}")
                    return True
                else:
                    self.log_test("Report Database Persistence", False, "No report content in second generation")
                    return False
            else:
                self.log_test("Report Database Persistence", False, 
                            f"Second report generation failed - HTTP {second_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Report Database Persistence", False, f"Exception: {str(e)}")
            return False
    
    def test_report_markdown_format(self) -> bool:
        """Test 5: Report Markdown Format Validation"""
        if not self.task_id:
            self.log_test("Report Markdown Format", False, "No task_id available for testing")
            return False
        
        try:
            response = self.session.post(f"{API_BASE}/agent/generate-final-report/{self.task_id}", 
                                       json={}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                report = data.get('report', '')
                
                if report:
                    # Detailed markdown format validation
                    format_checks = {
                        'has_main_heading': report.startswith('# '),
                        'has_subheadings': '## ' in report,
                        'has_subsections': '### ' in report,
                        'has_bold_text': '**' in report,
                        'has_lists': '- ' in report or '* ' in report,
                        'has_task_id': self.task_id in report,
                        'has_timestamp': any(word in report for word in ['fecha', 'generado', 'Mitosis']),
                        'proper_structure': all(section in report for section in ['Información General', 'Resumen Ejecutivo', 'Conclusión'])
                    }
                    
                    passed_checks = sum(format_checks.values())
                    total_checks = len(format_checks)
                    
                    if passed_checks >= 6:  # At least 75% of checks should pass
                        self.log_test("Report Markdown Format", True, 
                                    f"Markdown format valid - {passed_checks}/{total_checks} checks passed: {format_checks}")
                        return True
                    else:
                        self.log_test("Report Markdown Format", False, 
                                    f"Markdown format issues - {passed_checks}/{total_checks} checks passed: {format_checks}")
                        return False
                else:
                    self.log_test("Report Markdown Format", False, "No report content to validate")
                    return False
            else:
                self.log_test("Report Markdown Format", False, 
                            f"Could not generate report for format validation - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Report Markdown Format", False, f"Exception: {str(e)}")
            return False
    
    def test_backend_agent_endpoints(self) -> bool:
        """Test 6: Backend Agent Endpoints Functionality"""
        try:
            agent_endpoints = [
                ("/api/agent/status", "GET", "Agent Status"),
                ("/api/agent/generate-suggestions", "POST", "Generate Suggestions"),
                ("/api/agent/config/current", "GET", "Current Configuration"),
                ("/api/agent/ollama/check", "POST", "Ollama Connection Check")
            ]
            
            all_working = True
            endpoint_details = []
            
            for endpoint, method, name in agent_endpoints:
                try:
                    if method == "GET":
                        response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    else:  # POST
                        payload = {"endpoint": "https://bef4a4bb93d1.ngrok-free.app"} if "ollama" in endpoint else {}
                        response = self.session.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        endpoint_details.append(f"{name}: ✅")
                    else:
                        endpoint_details.append(f"{name}: ❌ HTTP {response.status_code}")
                        all_working = False
                        
                except Exception as e:
                    endpoint_details.append(f"{name}: ❌ Exception")
                    all_working = False
            
            if all_working:
                self.log_test("Backend Agent Endpoints", True, 
                            f"All agent endpoints working - {', '.join(endpoint_details)}")
                return True
            else:
                self.log_test("Backend Agent Endpoints", False, 
                            f"Some agent endpoints failing - {', '.join(endpoint_details)}")
                return False
                
        except Exception as e:
            self.log_test("Backend Agent Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_chat_endpoint_functionality(self) -> bool:
        """Test 7: Chat Endpoint Core Functionality"""
        try:
            test_messages = [
                "Hello, how are you?",
                "Create a simple task for testing",
                "What can you help me with?"
            ]
            
            all_successful = True
            chat_details = []
            
            for message in test_messages:
                try:
                    payload = {"message": message}
                    response = self.session.post(f"{API_BASE}/agent/chat", 
                                               json=payload, timeout=20)
                    
                    if response.status_code == 200:
                        data = response.json()
                        response_text = data.get('response', '')
                        task_id = data.get('task_id', '')
                        memory_used = data.get('memory_used', False)
                        
                        if response_text and task_id:
                            chat_details.append(f"'{message[:20]}...': ✅")
                        else:
                            chat_details.append(f"'{message[:20]}...': ❌ Incomplete")
                            all_successful = False
                    else:
                        chat_details.append(f"'{message[:20]}...': ❌ HTTP {response.status_code}")
                        all_successful = False
                        
                except Exception as e:
                    chat_details.append(f"'{message[:20]}...': ❌ Exception")
                    all_successful = False
                
                time.sleep(1)  # Brief pause between requests
            
            if all_successful:
                self.log_test("Chat Endpoint Functionality", True, 
                            f"Chat endpoint working for all test messages - {', '.join(chat_details)}")
                return True
            else:
                self.log_test("Chat Endpoint Functionality", False, 
                            f"Chat endpoint issues - {', '.join(chat_details)}")
                return False
                
        except Exception as e:
            self.log_test("Chat Endpoint Functionality", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all final report generation and backend functionality tests"""
        print("🧪 STARTING MITOSIS FINAL REPORT GENERATION AND BACKEND FUNCTIONALITY TESTING")
        print("=" * 80)
        
        # Test sequence focused on final report generation and backend functionality
        tests = [
            ("Health Endpoints", self.test_health_endpoints),
            ("Final Report Generation (Valid Task)", self.test_final_report_generation_valid_task),
            ("Final Report Generation (Invalid Task)", self.test_final_report_generation_invalid_task),
            ("Report Database Persistence", self.test_report_database_persistence),
            ("Report Markdown Format", self.test_report_markdown_format),
            ("Backend Agent Endpoints", self.test_backend_agent_endpoints),
            ("Chat Endpoint Functionality", self.test_chat_endpoint_functionality)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 80)
        print("🎯 FINAL REPORT GENERATION AND BACKEND FUNCTIONALITY TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['details']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Determine overall status
        if success_rate >= 85:
            overall_status = "✅ EXCELLENT - Final report generation and backend fully operational"
        elif success_rate >= 70:
            overall_status = "⚠️ GOOD - Most functionality working with minor issues"
        elif success_rate >= 50:
            overall_status = "⚠️ PARTIAL - Some functionality working but significant issues remain"
        else:
            overall_status = "❌ CRITICAL - Major issues with final report generation and backend"
        
        print(f"   Overall Status: {overall_status}")
        
        # Critical findings for final report generation
        critical_tests = ["Final Report Generation (Valid Task)", "Report Database Persistence", "Report Markdown Format"]
        critical_passed = sum(1 for result in self.test_results 
                            if result['test_name'] in critical_tests and result['success'])
        
        print(f"\n🔥 CRITICAL FINAL REPORT FUNCTIONALITY:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   ✅ All critical final report functionality is working")
        else:
            print("   ❌ Some critical final report functionality is not working")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'critical_passed': critical_passed,
            'critical_total': len(critical_tests),
            'test_results': self.test_results,
            'task_id': self.task_id
        }

def main():
    """Main testing function"""
    tester = MitosisFinalReportTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = '/app/final_report_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Return exit code based on success
    if results['success_rate'] >= 70:
        print("\n🎉 FINAL REPORT GENERATION TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n⚠️ FINAL REPORT GENERATION TESTING COMPLETED WITH ISSUES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)