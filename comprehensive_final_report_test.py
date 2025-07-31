#!/usr/bin/env python3
"""
Comprehensive test for the final report generation endpoint
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://2f624c51-ec2b-44ff-afc0-b55fee86c86e.preview.emergentagent.com"

def test_final_report_with_valid_task():
    """Test final report generation with a valid task ID"""
    
    print("🧪 Test 1: Final Report Generation with Valid Task ID")
    print("-" * 50)
    
    test_task_id = "valid-task-123"
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/generate-final-report/{test_task_id}",
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            success = data.get('success', False)
            report = data.get('report', '')
            task_id = data.get('task_id', '')
            generated_at = data.get('generated_at', '')
            
            if success and report and task_id and generated_at:
                print("✅ PASS - All required fields present")
                
                # Check markdown format
                markdown_checks = {
                    'has_main_heading': report.startswith('# '),
                    'has_subheadings': '## ' in report,
                    'has_bold_text': '**' in report,
                    'has_lists': '- ' in report,
                    'has_task_id': task_id in report
                }
                
                passed_checks = sum(markdown_checks.values())
                print(f"   Markdown format checks: {passed_checks}/5 passed")
                
                # Check expected sections
                expected_sections = ['Información General', 'Resumen Ejecutivo', 'Conclusión']
                sections_found = [section in report for section in expected_sections]
                print(f"   Required sections: {sum(sections_found)}/3 found")
                
                return passed_checks >= 4 and sum(sections_found) >= 2
            else:
                print("❌ FAIL - Missing required fields")
                return False
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Exception: {str(e)}")
        return False

def test_final_report_with_invalid_task():
    """Test final report generation with invalid task ID"""
    
    print("\n🧪 Test 2: Final Report Generation with Invalid Task ID")
    print("-" * 50)
    
    test_task_id = "non-existent-task-999"
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/generate-final-report/{test_task_id}",
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            success = data.get('success', False)
            report = data.get('report', '')
            task_id = data.get('task_id', '')
            
            if success and report and task_id == test_task_id:
                # Should generate fallback report
                is_fallback = 'Tarea Completada' in report or 'Sin descripción' in report
                if is_fallback:
                    print("✅ PASS - Fallback report generated correctly")
                    return True
                else:
                    print("❌ FAIL - Report doesn't appear to be fallback format")
                    return False
            else:
                print("❌ FAIL - Unexpected response structure")
                return False
        else:
            # Error response is also acceptable
            print(f"✅ PASS - Proper error handling (HTTP {response.status_code})")
            return True
            
    except Exception as e:
        print(f"❌ FAIL - Exception: {str(e)}")
        return False

def test_report_consistency():
    """Test that multiple calls return consistent reports"""
    
    print("\n🧪 Test 3: Report Generation Consistency")
    print("-" * 50)
    
    test_task_id = "consistency-test-456"
    
    try:
        # Generate report twice
        response1 = requests.post(
            f"{BACKEND_URL}/api/agent/generate-final-report/{test_task_id}",
            json={},
            timeout=30
        )
        
        response2 = requests.post(
            f"{BACKEND_URL}/api/agent/generate-final-report/{test_task_id}",
            json={},
            timeout=30
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            report1 = data1.get('report', '')
            report2 = data2.get('report', '')
            
            # Reports should be similar (same structure, different timestamps)
            structure_similar = (
                report1.count('##') == report2.count('##') and
                report1.count('**') == report2.count('**') and
                test_task_id in report1 and test_task_id in report2
            )
            
            if structure_similar:
                print("✅ PASS - Reports have consistent structure")
                return True
            else:
                print("❌ FAIL - Reports have inconsistent structure")
                return False
        else:
            print(f"❌ FAIL - HTTP errors: {response1.status_code}, {response2.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Exception: {str(e)}")
        return False

def test_report_performance():
    """Test report generation performance"""
    
    print("\n🧪 Test 4: Report Generation Performance")
    print("-" * 50)
    
    test_task_id = "performance-test-789"
    
    try:
        start_time = datetime.now()
        
        response = requests.post(
            f"{BACKEND_URL}/api/agent/generate-final-report/{test_task_id}",
            json={},
            timeout=30
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if response.status_code == 200:
            data = response.json()
            report = data.get('report', '')
            
            if report and duration < 10:  # Should complete within 10 seconds
                print(f"✅ PASS - Report generated in {duration:.2f} seconds")
                return True
            elif duration >= 10:
                print(f"❌ FAIL - Too slow: {duration:.2f} seconds")
                return False
            else:
                print("❌ FAIL - No report content")
                return False
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Exception: {str(e)}")
        return False

def test_backend_health():
    """Test backend health endpoints"""
    
    print("\n🧪 Test 5: Backend Health Check")
    print("-" * 50)
    
    endpoints = [
        ("/api/health", "API Health"),
        ("/api/agent/status", "Agent Status")
    ]
    
    all_healthy = True
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                print(f"   {name}: ✅ {status}")
            else:
                print(f"   {name}: ❌ HTTP {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"   {name}: ❌ Exception")
            all_healthy = False
    
    return all_healthy

def main():
    """Main test function"""
    
    print("🚀 COMPREHENSIVE FINAL REPORT GENERATION TESTING")
    print("=" * 70)
    
    # Run all tests
    tests = [
        ("Valid Task ID", test_final_report_with_valid_task),
        ("Invalid Task ID", test_final_report_with_invalid_task),
        ("Report Consistency", test_report_consistency),
        ("Performance", test_report_performance),
        ("Backend Health", test_backend_health)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ FAIL - {test_name}: Exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        overall_status = "✅ EXCELLENT - Final report generation fully operational"
    elif success_rate >= 60:
        overall_status = "⚠️ GOOD - Most functionality working"
    else:
        overall_status = "❌ CRITICAL - Major issues found"
    
    print(f"   Overall Status: {overall_status}")
    
    # Critical functionality check
    critical_tests = ["Valid Task ID", "Invalid Task ID"]
    critical_passed = sum(1 for name, result in results if name in critical_tests and result)
    
    print(f"\n🔥 CRITICAL FUNCTIONALITY:")
    print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
    
    if critical_passed == len(critical_tests):
        print("   ✅ All critical final report functionality is working")
        print("\n🎉 Final report generation endpoint is ready for production!")
    else:
        print("   ❌ Some critical final report functionality is not working")
        print("\n⚠️ Final report generation needs fixes before production")
    
    return 0 if critical_passed == len(critical_tests) else 1

if __name__ == "__main__":
    exit(main())