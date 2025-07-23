#!/usr/bin/env python3
"""
FOCUSED CONSOLIDATED SERVER TESTING
Tests the specific endpoints that were failing
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://fd9f2a9e-19b9-489b-bfc1-3ec126117b53.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_endpoint(name, url, method="GET", data=None, timeout=10):
    """Test a specific endpoint"""
    try:
        print(f"Testing {name}...")
        
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=data, timeout=timeout)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"  ✅ SUCCESS - Response received")
                print(f"  Data keys: {list(json_data.keys())}")
                return True, json_data
            except:
                print(f"  ✅ SUCCESS - Non-JSON response")
                return True, response.text
        else:
            print(f"  ❌ FAILED - HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data}")
                return False, error_data
            except:
                print(f"  Error: {response.text}")
                return False, response.text
                
    except Exception as e:
        print(f"  ❌ EXCEPTION - {str(e)}")
        return False, str(e)

def main():
    print("🔍 FOCUSED CONSOLIDATED SERVER TESTING")
    print("=" * 60)
    print()
    
    # Test the endpoints that were failing
    tests = [
        ("Main Health Check", f"{BACKEND_URL}/health", "GET"),
        ("System Status", f"{API_BASE}/system/status", "GET"),
        ("Agent Config Current", f"{API_BASE}/agent/config/current", "GET"),
        ("Generate Suggestions", f"{API_BASE}/agent/generate-suggestions", "POST"),
        ("Agent Status", f"{API_BASE}/agent/status", "GET"),
    ]
    
    results = []
    
    for test_name, url, method in tests:
        print(f"🧪 {test_name}")
        print("-" * 40)
        
        success, data = test_endpoint(test_name, url, method)
        results.append((test_name, success, data))
        print()
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print()
    
    for test_name, success, data in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - CONSOLIDATED SERVER IS WORKING!")
    elif passed >= total * 0.8:
        print("✅ MOST TESTS PASSED - CONSOLIDATED SERVER IS MOSTLY WORKING")
    else:
        print("❌ SEVERAL TESTS FAILED - CONSOLIDATED SERVER NEEDS ATTENTION")

if __name__ == "__main__":
    main()