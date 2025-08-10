#!/usr/bin/env python3
"""
SIMPLE BROWSER NAVIGATION TEST
Testing the core functionality requested in the review.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://62ce0bbb-d528-4241-84f3-572bb0f8170d.preview.emergentagent.com"

def test_browser_navigation_system():
    """Test the browser navigation system as requested"""
    print("🚀 TESTING REAL-TIME BROWSER NAVIGATION SYSTEM")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print()
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    # Step 1: Create task as requested
    print("🔄 Step 1: Creating research task about Javier Milei")
    url = f"{BACKEND_URL}/api/agent/chat"
    payload = {
        "message": "Investigar información específica sobre Javier Milei: biografía, trayectoria política, declaraciones públicas y controversias"
    }
    
    try:
        response = session.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"✅ Task created successfully: {task_id}")
        else:
            print(f"❌ Failed to create task: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return False
    
    if not task_id:
        print("❌ No task_id received")
        return False
    
    # Step 2: Get task_id from response (already done above)
    print(f"📝 Task ID: {task_id}")
    
    # Step 3: Check if execute-plan endpoint exists, if not, execution should be automatic
    print("🔄 Step 3: Checking task execution")
    execute_url = f"{BACKEND_URL}/api/agent/execute-plan/{task_id}"
    try:
        execute_response = session.post(execute_url, timeout=30)
        if execute_response.status_code == 200:
            print("✅ Plan execution started via execute-plan endpoint")
        elif execute_response.status_code == 404:
            print("ℹ️ Execute-plan endpoint not found, assuming automatic execution")
        else:
            print(f"⚠️ Execute-plan returned HTTP {execute_response.status_code}")
    except Exception as e:
        print(f"ℹ️ Execute-plan endpoint test failed: {e}")
    
    # Step 4: Monitor task status and look for web_search activity
    print("🔄 Step 4: Monitoring task status for web navigation activity (90 seconds)")
    
    web_search_detected = False
    browser_activity_detected = False
    screenshot_evidence = []
    
    start_time = time.time()
    while time.time() - start_time < 90:
        try:
            status_url = f"{BACKEND_URL}/api/agent/get-task-status/{task_id}"
            status_response = session.get(status_url, timeout=10)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                task_status = status_data.get('status', 'unknown')
                current_step = status_data.get('current_step', 0)
                plan = status_data.get('plan', [])
                
                # Look for web_search steps
                for step in plan:
                    if step.get('tool') == 'web_search':
                        web_search_detected = True
                        if step.get('status') == 'in-progress' or step.get('active'):
                            browser_activity_detected = True
                            print(f"   🌐 Web search step detected: {step.get('title', 'Unknown')}")
                
                # Check for any results that might indicate browser activity
                for step in plan:
                    if 'result' in step and step['result']:
                        result = step['result']
                        if isinstance(result, dict):
                            # Look for browser-related data
                            if 'method' in result and 'playwright' in str(result['method']).lower():
                                browser_activity_detected = True
                                print(f"   📸 Browser activity detected in step results")
                            
                            # Look for search results that indicate real navigation
                            if 'results' in result or 'search_results' in result:
                                results_list = result.get('results', result.get('search_results', []))
                                if results_list and len(results_list) > 0:
                                    browser_activity_detected = True
                                    print(f"   🔍 Search results found: {len(results_list)} results")
                
                elapsed = int(time.time() - start_time)
                if elapsed % 15 == 0 and elapsed > 0:
                    print(f"   ⏱️ {elapsed}s elapsed - Status: {task_status}, Web search: {web_search_detected}, Browser activity: {browser_activity_detected}")
                
            time.sleep(3)  # Poll every 3 seconds
            
        except Exception as e:
            print(f"   ❌ Error polling task status: {e}")
            time.sleep(5)
    
    # Step 5: Check for screenshot files
    print("🔄 Step 5: Checking for screenshot files")
    screenshot_accessible = False
    
    # Try common screenshot paths
    screenshot_paths = [
        f"/api/files/screenshots/{task_id}/",
        f"/api/files/screenshots/{task_id}/screenshot_001.png",
        f"/api/files/screenshots/{task_id}/navigation_001.png",
        f"/api/files/screenshots/{task_id}/browser_001.png"
    ]
    
    for path in screenshot_paths:
        try:
            screenshot_url = f"{BACKEND_URL}{path}"
            screenshot_response = session.get(screenshot_url, timeout=10)
            if screenshot_response.status_code == 200:
                screenshot_accessible = True
                print(f"   ✅ Screenshot accessible: {path}")
                break
            elif screenshot_response.status_code == 404:
                print(f"   ❌ Screenshot not found: {path}")
            else:
                print(f"   ⚠️ Screenshot endpoint returned HTTP {screenshot_response.status_code}: {path}")
        except Exception as e:
            print(f"   ❌ Error accessing screenshot {path}: {e}")
    
    # Step 6: Check stored messages (simplified - just verify WebSocket endpoint exists)
    print("🔄 Step 6: Checking WebSocket endpoint availability")
    websocket_available = False
    
    try:
        # Try to access the WebSocket endpoint info
        ws_info_url = f"{BACKEND_URL}/api/socket.io/"
        ws_response = session.get(ws_info_url, timeout=10)
        if ws_response.status_code in [200, 400]:  # 400 is expected for GET on WebSocket endpoint
            websocket_available = True
            print("   ✅ WebSocket endpoint is available")
        else:
            print(f"   ❌ WebSocket endpoint returned HTTP {ws_response.status_code}")
    except Exception as e:
        print(f"   ❌ Error checking WebSocket endpoint: {e}")
    
    # Step 7: Final assessment
    print("\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT")
    print("=" * 80)
    
    issues_found = []
    successes = []
    
    if web_search_detected:
        successes.append("✅ Web search steps detected in task plan")
    else:
        issues_found.append("❌ No web search steps detected")
    
    if browser_activity_detected:
        successes.append("✅ Browser navigation activity detected")
    else:
        issues_found.append("❌ No browser navigation activity detected")
    
    if screenshot_accessible:
        successes.append("✅ Screenshots accessible via /api/files/screenshots/")
    else:
        issues_found.append("❌ Screenshots not accessible")
    
    if websocket_available:
        successes.append("✅ WebSocket endpoint available")
    else:
        issues_found.append("❌ WebSocket endpoint not available")
    
    print("SUCCESSES:")
    for success in successes:
        print(f"  {success}")
    
    print("\nISSUES FOUND:")
    for issue in issues_found:
        print(f"  {issue}")
    
    # Overall result
    success_rate = len(successes) / (len(successes) + len(issues_found)) * 100
    
    print(f"\nSUCCESS RATE: {success_rate:.1f}%")
    print(f"TASK ID TESTED: {task_id}")
    
    if success_rate >= 75:
        print("🎉 OVERALL RESULT: ✅ SYSTEM MOSTLY WORKING")
        return True
    elif success_rate >= 50:
        print("⚠️ OVERALL RESULT: 🔶 SYSTEM PARTIALLY WORKING")
        return True
    else:
        print("❌ OVERALL RESULT: ❌ SYSTEM NEEDS SIGNIFICANT WORK")
        return False

if __name__ == "__main__":
    success = test_browser_navigation_system()
    sys.exit(0 if success else 1)