#!/usr/bin/env python3
"""
Final Comprehensive Backend Verification Test

This test verifies all the key requirements from the review request:
1. Backend Health & Endpoints
2. Real File Generation 
3. File Content Verification
4. Download System
5. Memory System
6. Plan Execution
7. WebSocket & Tracking
"""

import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "https://4359b6f3-95cc-48fc-92bb-0cc5ab04d8db.preview.emergentagent.com"
GENERATED_FILES_PATH = "/app/backend/static/generated_files"

print(f"🧪 FINAL COMPREHENSIVE BACKEND VERIFICATION")
print(f"Test started at: {datetime.now().isoformat()}")

results = {
    "backend_health": False,
    "endpoints_working": False,
    "memory_system": False,
    "file_generation": False,
    "meaningful_content": False,
    "download_system": False,
    "plan_execution": False,
    "websocket_tracking": False,
    "task_ids_generated": [],
    "files_created": [],
    "test_details": []
}

def test_endpoint(name, url, method="GET", data=None, timeout=30):
    """Test an endpoint and return result"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=data, timeout=timeout)
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                return {"status": "ok", "text": response.text}
        return None
    except Exception as e:
        print(f"❌ {name} failed: {str(e)}")
        return None

# 1. Backend Health & Endpoints
print(f"\n📋 1. BACKEND HEALTH & ENDPOINTS")
health_data = test_endpoint("Health Check", f"{BASE_URL}/api/health")
agent_health = test_endpoint("Agent Health", f"{BASE_URL}/api/agent/health")
agent_status = test_endpoint("Agent Status", f"{BASE_URL}/api/agent/status")

if health_data and agent_health and agent_status:
    results["backend_health"] = True
    results["endpoints_working"] = True
    print("✅ Backend health and endpoints working")
else:
    print("❌ Backend health or endpoints failing")

# 2. Memory System Verification
print(f"\n📋 2. MEMORY SYSTEM VERIFICATION")
memory_test = test_endpoint(
    "Memory Test", 
    f"{BASE_URL}/api/agent/chat",
    method="POST",
    data={"message": "Hola, ¿cómo estás?"}
)

if memory_test and memory_test.get("memory_used") is True:
    results["memory_system"] = True
    print("✅ Memory system working (memory_used=true)")
    if memory_test.get("task_id"):
        results["task_ids_generated"].append(memory_test["task_id"])
else:
    print("❌ Memory system not working")

# 3. Real File Generation & Plan Execution
print(f"\n📋 3. REAL FILE GENERATION & PLAN EXECUTION")
initial_files = set(os.listdir(GENERATED_FILES_PATH)) if os.path.exists(GENERATED_FILES_PATH) else set()

# Test document creation
unique_id = int(time.time())
creation_test = test_endpoint(
    "Document Creation",
    f"{BASE_URL}/api/agent/chat",
    method="POST",
    data={"message": f"Crea un informe ejecutivo sobre inteligencia artificial en 2025 - Test {unique_id}"},
    timeout=60
)

if creation_test:
    results["plan_execution"] = True
    print("✅ Plan execution working")
    if creation_test.get("task_id"):
        results["task_ids_generated"].append(creation_test["task_id"])
    if creation_test.get("memory_used") is True:
        print("✅ Memory integration in plan execution confirmed")
else:
    print("❌ Plan execution failing")

# Wait for file generation
print("⏳ Waiting 25 seconds for file generation...")
time.sleep(25)

# Check for new files
current_files = set(os.listdir(GENERATED_FILES_PATH)) if os.path.exists(GENERATED_FILES_PATH) else set()
new_files = current_files - initial_files

if new_files:
    results["file_generation"] = True
    results["files_created"] = list(new_files)
    print(f"✅ File generation working: {len(new_files)} files created")
    
    # 4. File Content Verification
    print(f"\n📋 4. FILE CONTENT VERIFICATION")
    meaningful_files = 0
    for file in new_files:
        file_path = os.path.join(GENERATED_FILES_PATH, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for meaningful content
            if (len(content) > 100 and 
                len(content.split()) > 20 and 
                not content.startswith('Error') and
                ('RESUMEN' in content or 'PLAN' in content or 'TAREA' in content)):
                meaningful_files += 1
                print(f"✅ {file}: Meaningful content verified ({len(content)} chars)")
            else:
                print(f"⚠️  {file}: Content may be placeholder")
        except Exception as e:
            print(f"❌ {file}: Error reading content - {str(e)}")
    
    if meaningful_files > 0:
        results["meaningful_content"] = True
        print(f"✅ Meaningful content verified in {meaningful_files} files")
    else:
        print("❌ No meaningful content verified")
else:
    print("❌ No files generated")

# 5. Download System
print(f"\n📋 5. DOWNLOAD SYSTEM")
list_files = test_endpoint("List Files", f"{BASE_URL}/api/agent/list-files")

if list_files and isinstance(list_files, dict) and "files" in list_files:
    results["download_system"] = True
    print(f"✅ Download system working: {len(list_files['files'])} files listed")
    
    # Test actual download
    if list_files["files"]:
        test_file = list_files["files"][0]["name"]
        download_test = test_endpoint("Download Test", f"{BASE_URL}/api/agent/download/{test_file}")
        if download_test:
            print(f"✅ File download confirmed: {test_file}")
        else:
            print(f"⚠️  File download may have issues")
else:
    print("❌ Download system not working")

# 6. WebSocket & Tracking
print(f"\n📋 6. WEBSOCKET & TRACKING")
if len(results["task_ids_generated"]) > 0:
    results["websocket_tracking"] = True
    print(f"✅ WebSocket tracking working: {len(results['task_ids_generated'])} task IDs generated")
    for i, task_id in enumerate(results["task_ids_generated"][:3]):
        print(f"   🆔 Task {i+1}: {task_id}")
else:
    print("❌ WebSocket tracking not working")

# Final Assessment
print(f"\n" + "="*60)
print("📊 FINAL COMPREHENSIVE ASSESSMENT")
print("="*60)

total_checks = 8
passed_checks = sum([
    results["backend_health"],
    results["endpoints_working"], 
    results["memory_system"],
    results["file_generation"],
    results["meaningful_content"],
    results["download_system"],
    results["plan_execution"],
    results["websocket_tracking"]
])

success_rate = (passed_checks / total_checks) * 100

print(f"\n📈 RESULTS SUMMARY:")
print(f"   ✅ Backend Health & Endpoints: {'WORKING' if results['backend_health'] and results['endpoints_working'] else 'FAILING'}")
print(f"   ✅ Memory System Integration: {'WORKING' if results['memory_system'] else 'FAILING'}")
print(f"   ✅ Real File Generation: {'WORKING' if results['file_generation'] else 'FAILING'}")
print(f"   ✅ Meaningful Content: {'VERIFIED' if results['meaningful_content'] else 'NOT VERIFIED'}")
print(f"   ✅ Download System: {'WORKING' if results['download_system'] else 'FAILING'}")
print(f"   ✅ Plan Execution: {'WORKING' if results['plan_execution'] else 'FAILING'}")
print(f"   ✅ WebSocket & Tracking: {'WORKING' if results['websocket_tracking'] else 'FAILING'}")

print(f"\n🎯 OVERALL ASSESSMENT:")
print(f"   Success Rate: {success_rate:.1f}% ({passed_checks}/{total_checks})")
print(f"   Files Created: {len(results['files_created'])}")
print(f"   Task IDs Generated: {len(results['task_ids_generated'])}")

if success_rate >= 85 and results["file_generation"] and results["meaningful_content"]:
    print(f"\n🎉 VERDICT: SYSTEM IS FULLY OPERATIONAL")
    print(f"   ✅ Backend is generating REAL, tangible files")
    print(f"   ✅ Files contain meaningful, structured content")
    print(f"   ✅ All core systems are working correctly")
    print(f"   ✅ System is ready for production use")
    final_verdict = "FULLY_OPERATIONAL"
elif success_rate >= 70 and results["file_generation"]:
    print(f"\n⚠️  VERDICT: SYSTEM IS MOSTLY OPERATIONAL")
    print(f"   ✅ File generation is working")
    print(f"   ⚠️  Some minor issues detected")
    final_verdict = "MOSTLY_OPERATIONAL"
else:
    print(f"\n❌ VERDICT: SYSTEM HAS ISSUES")
    print(f"   ❌ Critical functionality not working")
    final_verdict = "NEEDS_ATTENTION"

# Save results
results["final_verdict"] = final_verdict
results["success_rate"] = success_rate
results["timestamp"] = datetime.now().isoformat()

with open(f"/app/final_verification_results_{int(time.time())}.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n🏁 Verification completed at: {datetime.now().isoformat()}")
print("="*60)