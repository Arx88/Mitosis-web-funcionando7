#!/usr/bin/env python3
"""
SIMPLIFIED WEBSOCKET STEP PROGRESSION TEST
Focus on the core WebSocket step progression issue without complex task creation.
"""

import requests
import json
import time
from datetime import datetime

# Backend URL
BACKEND_URL = "https://812df669-341c-4e0c-88be-55ef79256b5b.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_basic_backend_functionality():
    """Test basic backend functionality"""
    print("🧪 TESTING BASIC BACKEND FUNCTIONALITY")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Origin': 'https://812df669-341c-4e0c-88be-55ef79256b5b.preview.emergentagent.com'
    })
    
    results = {}
    
    # Test 1: Health endpoint
    try:
        print("\n🔍 Testing health endpoint...")
        response = session.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint working - Status: {data.get('status', 'unknown')}")
            results['health'] = True
        else:
            print(f"❌ Health endpoint failed - Status: {response.status_code}")
            results['health'] = False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        results['health'] = False
    
    # Test 2: Simple chat
    try:
        print("\n🔍 Testing simple chat...")
        response = session.post(f"{API_BASE}/agent/chat", 
                              json={"message": "Hola, test simple"}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id', '')
            memory_used = data.get('memory_used', False)
            print(f"✅ Chat working - Task ID: {task_id}, Memory: {memory_used}")
            results['chat'] = True
            results['task_id'] = task_id
        else:
            print(f"❌ Chat failed - Status: {response.status_code}")
            results['chat'] = False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        results['chat'] = False
    
    # Test 3: Plan generation
    try:
        print("\n🔍 Testing plan generation...")
        response = session.post(f"{API_BASE}/agent/chat", 
                              json={"message": "Crear un análisis simple de blockchain"}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            plan = data.get('plan', [])
            enhanced_title = data.get('enhanced_title', '')
            if plan and len(plan) > 0:
                print(f"✅ Plan generation working - {len(plan)} steps, Title: {enhanced_title}")
                results['plan_generation'] = True
                results['plan'] = plan
            else:
                print(f"❌ Plan generation failed - No plan in response")
                results['plan_generation'] = False
        else:
            print(f"❌ Plan generation failed - Status: {response.status_code}")
            results['plan_generation'] = False
    except Exception as e:
        print(f"❌ Plan generation error: {e}")
        results['plan_generation'] = False
    
    # Test 4: WebSocket endpoint accessibility
    try:
        print("\n🔍 Testing WebSocket endpoint accessibility...")
        response = session.get(f"{BACKEND_URL}/api/socket.io/", timeout=10)
        # Socket.IO endpoints typically return 400 for GET requests without proper handshake
        if response.status_code in [200, 400]:
            print(f"✅ WebSocket endpoint accessible - Status: {response.status_code}")
            results['websocket_endpoint'] = True
        else:
            print(f"❌ WebSocket endpoint not accessible - Status: {response.status_code}")
            results['websocket_endpoint'] = False
    except Exception as e:
        print(f"❌ WebSocket endpoint error: {e}")
        results['websocket_endpoint'] = False
    
    # Test 5: Agent status
    try:
        print("\n🔍 Testing agent status...")
        response = session.get(f"{API_BASE}/agent/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', '')
            memory = data.get('memory', {})
            tools_count = data.get('tools_count', 0)
            print(f"✅ Agent status working - Status: {status}, Memory enabled: {memory.get('enabled', False)}, Tools: {tools_count}")
            results['agent_status'] = True
        else:
            print(f"❌ Agent status failed - Status: {response.status_code}")
            results['agent_status'] = False
    except Exception as e:
        print(f"❌ Agent status error: {e}")
        results['agent_status'] = False
    
    # Test 6: Task execution endpoints
    if results.get('task_id'):
        print("\n🔍 Testing task execution endpoints...")
        task_id = results['task_id']
        execution_endpoints = [
            f"{API_BASE}/agent/start-task-execution/{task_id}",
            f"{API_BASE}/agent/execute-task",
            f"{API_BASE}/agent/execute/{task_id}"
        ]
        
        execution_available = False
        for endpoint in execution_endpoints:
            try:
                response = session.post(endpoint, json={"task_id": task_id}, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Task execution endpoint working: {endpoint}")
                    execution_available = True
                    break
                elif response.status_code == 404:
                    print(f"❌ Task execution endpoint not found: {endpoint}")
                else:
                    print(f"⚠️ Task execution endpoint returned {response.status_code}: {endpoint}")
            except Exception as e:
                print(f"❌ Task execution endpoint error {endpoint}: {e}")
        
        results['task_execution'] = execution_available
    else:
        results['task_execution'] = False
        print("\n⚠️ Skipping task execution test - No task ID available")
    
    return results

def analyze_websocket_step_progression_issue(results):
    """Analyze the WebSocket step progression issue based on test results"""
    print("\n" + "=" * 60)
    print("🔍 WEBSOCKET STEP PROGRESSION ISSUE ANALYSIS")
    print("=" * 60)
    
    # Calculate success rate
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v is True)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n📊 BACKEND FUNCTIONALITY RESULTS:")
    print(f"   Tests Passed: {passed_tests}/{total_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    # Analyze specific issues
    print(f"\n🔍 SPECIFIC ISSUE ANALYSIS:")
    
    # Issue 1: Basic backend connectivity
    if results.get('health') and results.get('chat'):
        print("   ✅ BACKEND CONNECTIVITY: Backend is accessible and responding")
    else:
        print("   ❌ BACKEND CONNECTIVITY: Backend has connectivity issues")
    
    # Issue 2: Plan generation capability
    if results.get('plan_generation'):
        print("   ✅ PLAN GENERATION: Backend can generate task plans")
        if 'plan' in results:
            plan = results['plan']
            print(f"      📋 Plan has {len(plan)} steps")
            for i, step in enumerate(plan[:3], 1):  # Show first 3 steps
                title = step.get('title', 'No title')
                tool = step.get('tool', 'No tool')
                print(f"      Step {i}: {title} (Tool: {tool})")
    else:
        print("   ❌ PLAN GENERATION: Backend cannot generate task plans")
    
    # Issue 3: WebSocket infrastructure
    if results.get('websocket_endpoint'):
        print("   ✅ WEBSOCKET INFRASTRUCTURE: WebSocket endpoint is accessible")
    else:
        print("   ❌ WEBSOCKET INFRASTRUCTURE: WebSocket endpoint not accessible")
    
    # Issue 4: Task execution capability
    if results.get('task_execution'):
        print("   ✅ TASK EXECUTION: Task execution endpoints are available")
    else:
        print("   ❌ TASK EXECUTION: No working task execution endpoints found")
        print("      🔍 ROOT CAUSE: This is likely why steps don't progress - tasks aren't executed")
    
    # Issue 5: Agent status and memory
    if results.get('agent_status'):
        print("   ✅ AGENT STATUS: Agent status endpoint working")
    else:
        print("   ❌ AGENT STATUS: Agent status endpoint not working")
    
    # Root cause analysis for user's reported issues
    print(f"\n🎯 ROOT CAUSE ANALYSIS FOR USER ISSUES:")
    
    # Issue 1: Agent jumps from step 3 back to step 2
    if not results.get('task_execution'):
        print("   🔍 STEP JUMPING (3→2): Likely caused by missing task execution")
        print("      - Tasks are created with plans but never executed")
        print("      - Frontend may be showing cached/stale step data")
        print("      - No real-time WebSocket events are emitted during execution")
    
    # Issue 2: Steps being marked as "HECHO" (done) prematurely
    if not results.get('task_execution'):
        print("   🔍 PREMATURE COMPLETION: Likely caused by missing task execution")
        print("      - Steps may be marked complete without actual execution")
        print("      - No validation of step completion results")
        print("      - WebSocket events not emitted for real completion")
    
    # Issue 3: Frontend sync issues
    if not results.get('task_execution') or not results.get('websocket_endpoint'):
        print("   🔍 FRONTEND SYNC ISSUES: Multiple causes identified")
        print("      - WebSocket endpoint accessible but no events emitted")
        print("      - Task execution not triggering real-time updates")
        print("      - Frontend receiving plan data but no execution progress")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    
    if success_rate >= 80:
        print("   ✅ BACKEND STATUS: Backend mostly functional")
        if not results.get('task_execution'):
            print("   ⚠️ CRITICAL ISSUE: Task execution missing - this explains user's issues")
    elif success_rate >= 60:
        print("   ⚠️ BACKEND STATUS: Backend partially functional")
        print("   🔧 MULTIPLE ISSUES: Several components need fixing")
    else:
        print("   ❌ BACKEND STATUS: Backend has critical issues")
        print("   🚨 URGENT: Multiple system failures detected")
    
    return {
        'success_rate': success_rate,
        'critical_issue': not results.get('task_execution'),
        'websocket_accessible': results.get('websocket_endpoint', False),
        'plan_generation_working': results.get('plan_generation', False),
        'backend_responsive': results.get('health', False) and results.get('chat', False)
    }

def main():
    """Main testing function"""
    print("🧪 MITOSIS BACKEND WEBSOCKET STEP PROGRESSION DIAGNOSIS")
    print("🎯 FOCUS: Identifying root cause of step progression issues")
    print("⚠️ USER ISSUES: Step jumps (3→2), premature completion, frontend sync")
    
    # Run basic functionality tests
    results = test_basic_backend_functionality()
    
    # Analyze WebSocket step progression issues
    analysis = analyze_websocket_step_progression_issue(results)
    
    # Save results
    output = {
        'test_results': results,
        'analysis': analysis,
        'timestamp': datetime.now().isoformat(),
        'backend_url': BACKEND_URL
    }
    
    with open('/app/websocket_diagnosis.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n💾 Diagnosis results saved to: /app/websocket_diagnosis.json")
    
    # Final recommendations
    print(f"\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS FOR MAIN AGENT")
    print("=" * 60)
    
    if analysis['critical_issue']:
        print("❌ CRITICAL ISSUE IDENTIFIED: Task execution endpoints missing")
        print("📋 PRIMARY RECOMMENDATION: Implement task execution endpoints")
        print("🔧 SPECIFIC ACTIONS NEEDED:")
        print("   1. Add /api/agent/start-task-execution/<task_id> endpoint")
        print("   2. Implement automatic task execution after plan generation")
        print("   3. Add WebSocket event emission during task execution")
        print("   4. Emit task_progress and step_completed events in real-time")
        print("   5. Ensure step sequence validation (1→2→3→4)")
    
    if analysis['websocket_accessible'] and analysis['plan_generation_working']:
        print("✅ POSITIVE: WebSocket infrastructure and plan generation working")
        print("📋 SECONDARY RECOMMENDATION: Focus on connecting execution to WebSocket")
    
    if analysis['backend_responsive']:
        print("✅ POSITIVE: Backend is responsive and basic functionality works")
        print("📋 TERTIARY RECOMMENDATION: Issue is in execution layer, not basic backend")
    
    print(f"\n🔍 USER ISSUE RESOLUTION:")
    print("   ISSUE 1 (Step jumping 3→2): Fix task execution to emit proper step events")
    print("   ISSUE 2 (Premature HECHO): Add step completion validation in execution")
    print("   ISSUE 3 (Frontend sync): Connect task execution to WebSocket events")
    
    return 0 if analysis['success_rate'] >= 60 else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)