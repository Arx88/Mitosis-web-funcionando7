#!/usr/bin/env python3
"""
FOCUSED TEST FOR /api/agent/generate-plan ENDPOINT
Testing the specific endpoint requested by the user
"""

import requests
import json
import time
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://15c16a6c-c05b-4a8b-8862-e44571e2a1d6.preview.emergentagent.com"

def test_health_endpoint():
    """Test the /api/health endpoint first"""
    print("🔍 Testing /api/health endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health Status: {data.get('status', 'unknown')}")
            print(f"   📊 Services: {data.get('services', {})}")
            return True
        else:
            print(f"   ❌ Health check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_generate_plan_endpoint():
    """Test the specific /api/agent/generate-plan endpoint"""
    print("\n🎯 Testing /api/agent/generate-plan endpoint...")
    
    # Test data as requested
    test_data = {
        "task_title": "Crear un análisis de mercado para productos orgánicos",
        "task_id": "test-task-123"
    }
    
    print(f"   📤 Sending request with data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(
            f"{BACKEND_URL}/api/agent/generate-plan",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   📥 Response Status Code: {response.status_code}")
        print(f"   📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Response received successfully!")
                print(f"   📋 Response keys: {list(data.keys())}")
                
                # Check for required fields
                has_enhanced_title = 'enhanced_title' in data
                has_plan = 'plan' in data
                
                print(f"\n   🔍 VERIFICATION RESULTS:")
                print(f"   ✅ enhanced_title present: {has_enhanced_title}")
                if has_enhanced_title:
                    print(f"      Enhanced Title: '{data['enhanced_title']}'")
                
                print(f"   ✅ plan present: {has_plan}")
                if has_plan:
                    plan = data['plan']
                    print(f"      Plan type: {type(plan)}")
                    if isinstance(plan, list):
                        print(f"      Plan steps count: {len(plan)}")
                        if len(plan) > 0:
                            print(f"      First step: {plan[0] if plan else 'None'}")
                    else:
                        print(f"      Plan content: {plan}")
                
                # Show other fields
                other_fields = {k: v for k, v in data.items() if k not in ['enhanced_title', 'plan']}
                if other_fields:
                    print(f"   📊 Other response fields:")
                    for key, value in other_fields.items():
                        print(f"      {key}: {value}")
                
                # Overall success
                success = has_enhanced_title and has_plan
                print(f"\n   🎯 ENDPOINT TEST RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
                
                return success, data
                
            except json.JSONDecodeError as e:
                print(f"   ❌ Failed to parse JSON response: {e}")
                print(f"   📄 Raw response: {response.text[:500]}...")
                return False, None
                
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📄 Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   📄 Raw error response: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timed out after 30 seconds")
        return False, None
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection error - backend may be down")
        return False, None
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False, None

def test_with_curl_command():
    """Show the equivalent curl command for manual testing"""
    print("\n🔧 EQUIVALENT CURL COMMAND:")
    curl_cmd = f'''curl -X POST "{BACKEND_URL}/api/agent/generate-plan" \\
  -H "Content-Type: application/json" \\
  -d '{{"task_title": "Crear un análisis de mercado para productos orgánicos", "task_id": "test-task-123"}}'
'''
    print(curl_cmd)

def main():
    """Main test function"""
    print("🧪 FOCUSED BACKEND ENDPOINT TEST")
    print("=" * 50)
    print(f"🎯 Target: {BACKEND_URL}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test 1: Health check
    health_ok = test_health_endpoint()
    
    # Test 2: Generate plan endpoint
    plan_ok, plan_data = test_generate_plan_endpoint()
    
    # Show curl command
    test_with_curl_command()
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 FINAL TEST SUMMARY:")
    print(f"   Health Endpoint: {'✅ WORKING' if health_ok else '❌ FAILED'}")
    print(f"   Generate Plan Endpoint: {'✅ WORKING' if plan_ok else '❌ FAILED'}")
    
    if plan_ok and plan_data:
        print(f"\n🎯 SPECIFIC VERIFICATION:")
        print(f"   ✅ enhanced_title: {plan_data.get('enhanced_title', 'NOT FOUND')}")
        print(f"   ✅ plan: {len(plan_data.get('plan', [])) if isinstance(plan_data.get('plan'), list) else 'NOT A LIST'} steps")
    
    overall_success = health_ok and plan_ok
    print(f"\n🏆 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)