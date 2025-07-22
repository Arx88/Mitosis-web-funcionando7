#!/usr/bin/env python3
"""
NEWUPGRADE.MD Focused Verification Test
Quick verification of key improvements from NEWUPGRADE.MD
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://88a3e6b4-ea85-4a85-afbf-1b6b5f983da0.preview.emergentagent.com"

def test_intent_classification():
    """Test Intent Classification System"""
    print("🎯 Testing Intent Classification System...")
    
    test_cases = [
        {"message": "Hola, ¿cómo estás?", "expected": "casual"},
        {"message": "Crea un análisis completo de mercado para productos de IA en 2024", "expected": "complex_task"}
    ]
    
    results = []
    for case in test_cases:
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/agent/chat",
                json={"message": case["message"]},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if response indicates proper classification
                mode = data.get("mode", "")
                response_text = data.get("response", "")
                
                # Look for signs of proper intent classification
                if case["expected"] == "casual" and ("hola" in response_text.lower() or "bien" in response_text.lower()):
                    results.append(f"✅ Casual conversation classified correctly")
                elif case["expected"] == "complex_task" and ("plan" in response_text.lower() or "análisis" in response_text.lower()):
                    results.append(f"✅ Complex task classified correctly")
                else:
                    results.append(f"⚠️ Classification unclear for: {case['message'][:30]}...")
            else:
                results.append(f"❌ HTTP {response.status_code} for: {case['message'][:30]}...")
        except Exception as e:
            results.append(f"❌ Error: {str(e)[:50]}...")
    
    return results

def test_web_browsing():
    """Test Real Web Browsing Implementation"""
    print("🌐 Testing Web Browsing Implementation...")
    
    results = []
    try:
        # Test web search capability
        response = requests.post(
            f"{BACKEND_URL}/api/agent/chat",
            json={"message": "[WebSearch] latest AI developments 2024"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            
            # Look for signs of real web search
            if any(indicator in response_text.lower() for indicator in ["search", "found", "results", "web", "sources"]):
                results.append("✅ Web search functionality detected")
            else:
                results.append("⚠️ Web search response unclear")
        else:
            results.append(f"❌ Web search failed: HTTP {response.status_code}")
    except Exception as e:
        results.append(f"❌ Web search error: {str(e)[:50]}...")
    
    return results

def test_integration():
    """Test Integration Verification"""
    print("🔗 Testing Integration...")
    
    results = []
    
    # Test 1: Health endpoint
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                results.append("✅ Health endpoint working")
            else:
                results.append("⚠️ Health endpoint unhealthy")
        else:
            results.append(f"❌ Health endpoint failed: HTTP {response.status_code}")
    except Exception as e:
        results.append(f"❌ Health endpoint error: {str(e)[:50]}...")
    
    # Test 2: Agent status
    try:
        response = requests.get(f"{BACKEND_URL}/api/agent/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ollama", {}).get("connected"):
                results.append("✅ Agent status shows Ollama connected")
            else:
                results.append("⚠️ Agent status shows Ollama disconnected")
        else:
            results.append(f"❌ Agent status failed: HTTP {response.status_code}")
    except Exception as e:
        results.append(f"❌ Agent status error: {str(e)[:50]}...")
    
    return results

def test_error_handling():
    """Test Robust Error Handling"""
    print("🛡️ Testing Error Handling...")
    
    results = []
    
    # Test with unclear message
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/chat",
            json={"message": "asdfghjkl qwerty invalid unclear message"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            
            if response_text and len(response_text) > 10:
                results.append("✅ System handles unclear input gracefully")
            else:
                results.append("⚠️ Unclear input handling needs improvement")
        else:
            results.append(f"❌ Error handling failed: HTTP {response.status_code}")
    except Exception as e:
        results.append(f"❌ Error handling test failed: {str(e)[:50]}...")
    
    return results

def main():
    """Main test execution"""
    print("🚀 NEWUPGRADE.MD FOCUSED VERIFICATION")
    print("="*60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    print("="*60)
    
    all_results = []
    
    # Run tests
    all_results.extend(test_intent_classification())
    all_results.extend(test_web_browsing())
    all_results.extend(test_integration())
    all_results.extend(test_error_handling())
    
    # Print results
    print("\n📊 TEST RESULTS:")
    print("="*60)
    
    passed = 0
    failed = 0
    warnings = 0
    
    for result in all_results:
        print(result)
        if result.startswith("✅"):
            passed += 1
        elif result.startswith("❌"):
            failed += 1
        elif result.startswith("⚠️"):
            warnings += 1
    
    print("="*60)
    print(f"📈 SUMMARY:")
    print(f"✅ Passed: {passed}")
    print(f"⚠️ Warnings: {warnings}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + warnings + failed}")
    
    success_rate = (passed / (passed + warnings + failed)) * 100 if (passed + warnings + failed) > 0 else 0
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    
    # Overall assessment
    if failed == 0 and passed >= 6:
        print("🎉 EXCELLENT: All critical features working!")
    elif failed <= 2 and passed >= 4:
        print("✅ GOOD: Most features working correctly")
    elif failed <= 4:
        print("⚠️ NEEDS ATTENTION: Some issues found")
    else:
        print("❌ CRITICAL ISSUES: Multiple failures detected")
    
    return failed == 0 and passed >= 6

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)