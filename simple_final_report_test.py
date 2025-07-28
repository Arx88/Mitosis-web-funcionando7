#!/usr/bin/env python3
"""
Simple test for the final report generation endpoint
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://2d6bd67a-c88f-4adf-aad2-a25028aa0f12.preview.emergentagent.com"

def test_final_report_endpoint():
    """Test the final report generation endpoint"""
    
    print("🧪 Testing Final Report Generation Endpoint")
    print("=" * 50)
    
    # Test with a sample task ID
    test_task_id = "sample-task-for-testing"
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/generate-final-report/{test_task_id}",
            json={},
            timeout=30
        )
        
        print(f"📡 Request URL: {BACKEND_URL}/api/agent/generate-final-report/{test_task_id}")
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS - Endpoint is working!")
            
            # Check response structure
            success = data.get('success', False)
            report = data.get('report', '')
            task_id = data.get('task_id', '')
            generated_at = data.get('generated_at', '')
            
            print(f"   - Success: {success}")
            print(f"   - Task ID: {task_id}")
            print(f"   - Generated At: {generated_at}")
            print(f"   - Report Length: {len(report)} characters")
            
            if report:
                print("\n📄 Report Preview (first 300 chars):")
                print("-" * 40)
                print(report[:300] + "..." if len(report) > 300 else report)
                print("-" * 40)
                
                # Check markdown format
                markdown_indicators = ['#', '##', '###', '**', '-', '*']
                has_markdown = any(indicator in report for indicator in markdown_indicators)
                print(f"   - Has Markdown Format: {has_markdown}")
                
                # Check for expected sections
                expected_sections = ['Información General', 'Resumen Ejecutivo', 'Conclusión']
                has_sections = [section in report for section in expected_sections]
                print(f"   - Expected Sections: {dict(zip(expected_sections, has_sections))}")
            
            return True
            
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error Text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def test_health_endpoints():
    """Test basic health endpoints"""
    
    print("\n🏥 Testing Health Endpoints")
    print("=" * 30)
    
    endpoints = [
        "/health",
        "/api/health", 
        "/api/agent/status"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                results[endpoint] = f"✅ {status}"
            else:
                results[endpoint] = f"❌ HTTP {response.status_code}"
        except Exception as e:
            results[endpoint] = f"❌ Exception: {str(e)}"
    
    for endpoint, result in results.items():
        print(f"   {endpoint}: {result}")
    
    return all("✅" in result for result in results.values())

def main():
    """Main test function"""
    
    print("🚀 MITOSIS FINAL REPORT GENERATION TESTING")
    print("=" * 60)
    
    # Test health first
    health_ok = test_health_endpoints()
    
    # Test final report generation
    report_ok = test_final_report_endpoint()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    print(f"   Health Endpoints: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Final Report Generation: {'✅ PASS' if report_ok else '❌ FAIL'}")
    
    overall_success = health_ok and report_ok
    print(f"   Overall Status: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    
    if overall_success:
        print("\n🎉 Final report generation endpoint is working correctly!")
    else:
        print("\n⚠️ Issues found with final report generation functionality")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit(main())