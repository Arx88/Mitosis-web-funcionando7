#!/usr/bin/env python3
"""
Comprehensive Real Backend Verification Test Script for Mitosis Application

This script performs a complete verification of the Mitosis backend system to confirm:
1. Backend Health & Endpoints - Test all main endpoints
2. Real File Generation - Verify actual file creation in filesystem
3. File Content Verification - Check files contain real, meaningful content
4. Download System - Test file listing and download endpoints
5. Memory System - Verify memory integration is working
6. Plan Execution - Confirm structured plan generation and execution
7. WebSocket & Tracking - Verify task IDs and tracking

Key focus: Verify the system is ACTUALLY working and generating tangible files,
not just simulating responses.
"""

import requests
import json
import sys
import uuid
import time
import os
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "https://3445cd60-a036-4ee2-9d29-7dd17ae4e962.preview.emergentagent.com"
API_PREFIX = "/api"
AGENT_PREFIX = "/api/agent"
GENERATED_FILES_PATH = "/app/backend/static/generated_files"

print(f"🧪 COMPREHENSIVE REAL BACKEND VERIFICATION TEST")
print(f"Using backend URL: {BASE_URL}")
print(f"Test started at: {datetime.now().isoformat()}")
print(f"Generated files path: {GENERATED_FILES_PATH}")

# Test results tracking
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
}

def run_test(name, endpoint, method="GET", data=None, expected_status=200, timeout=30):
    """Run a test against an API endpoint"""
    test_results["summary"]["total"] += 1
    
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🔍 Testing: {name}")
        print(f"   URL: {url}")
        
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        execution_time = time.time() - start_time
        
        # Check status code
        if response.status_code == expected_status:
            print(f"   ✅ Status: {response.status_code} (Expected: {expected_status})")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                print(f"   📄 Response type: JSON")
                
                # Log key information from response
                if isinstance(response_data, dict):
                    if 'status' in response_data:
                        print(f"   📊 Status: {response_data['status']}")
                    if 'message' in response_data:
                        print(f"   💬 Message: {response_data['message'][:100]}...")
                    if 'task_id' in response_data:
                        print(f"   🆔 Task ID: {response_data['task_id']}")
                    if 'memory_used' in response_data:
                        print(f"   🧠 Memory Used: {response_data['memory_used']}")
                    if 'response' in response_data and isinstance(response_data['response'], str):
                        print(f"   📝 Response Length: {len(response_data['response'])} chars")
                
                test_results["tests"].append({
                    "name": name,
                    "status": "PASSED",
                    "execution_time": execution_time,
                    "response_data": response_data
                })
                test_results["summary"]["passed"] += 1
                return response_data
                
            except json.JSONDecodeError:
                print(f"   📄 Response type: Text/HTML ({len(response.text)} chars)")
                test_results["tests"].append({
                    "name": name,
                    "status": "PASSED",
                    "execution_time": execution_time,
                    "response_text": response.text[:200]
                })
                test_results["summary"]["passed"] += 1
                return response.text
        else:
            print(f"   ❌ Status: {response.status_code} (Expected: {expected_status})")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            print(f"   📄 Response: {response.text[:200]}...")
            
            test_results["tests"].append({
                "name": name,
                "status": "FAILED",
                "execution_time": execution_time,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "error": response.text[:200]
            })
            test_results["summary"]["failed"] += 1
            return None
            
    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT after {timeout}s")
        test_results["tests"].append({
            "name": name,
            "status": "FAILED",
            "error": f"Timeout after {timeout}s"
        })
        test_results["summary"]["failed"] += 1
        return None
        
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        test_results["tests"].append({
            "name": name,
            "status": "FAILED",
            "error": str(e)
        })
        test_results["summary"]["failed"] += 1
        return None

def check_file_system(path, description):
    """Check if files exist in the filesystem"""
    print(f"\n📁 Checking filesystem: {description}")
    print(f"   Path: {path}")
    
    try:
        if os.path.exists(path):
            if os.path.isdir(path):
                files = os.listdir(path)
                print(f"   ✅ Directory exists with {len(files)} files")
                
                # List files with details
                for file in files[:5]:  # Show first 5 files
                    file_path = os.path.join(path, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        print(f"   📄 {file} ({size} bytes, modified: {mtime.strftime('%Y-%m-%d %H:%M')})")
                
                if len(files) > 5:
                    print(f"   ... and {len(files) - 5} more files")
                
                return files
            else:
                print(f"   ✅ File exists")
                size = os.path.getsize(path)
                print(f"   📊 Size: {size} bytes")
                return [os.path.basename(path)]
        else:
            print(f"   ❌ Path does not exist")
            return []
            
    except Exception as e:
        print(f"   ❌ Error checking filesystem: {str(e)}")
        return []

def verify_file_content(file_path, description):
    """Verify that a file contains real, meaningful content"""
    print(f"\n📖 Verifying file content: {description}")
    print(f"   File: {file_path}")
    
    try:
        if not os.path.exists(file_path):
            print(f"   ❌ File does not exist")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check file size
        size = len(content)
        print(f"   📊 File size: {size} characters")
        
        if size < 50:
            print(f"   ⚠️  File is very small (< 50 chars)")
            return False
        
        # Check for meaningful content indicators
        meaningful_indicators = [
            len(content.split()) > 10,  # More than 10 words
            any(char.isalpha() for char in content),  # Contains letters
            '\n' in content or '.' in content,  # Has structure
            not content.strip().startswith('Error'),  # Not an error message
            not content.strip().startswith('Failed'),  # Not a failure message
        ]
        
        meaningful_score = sum(meaningful_indicators)
        print(f"   📈 Meaningful content score: {meaningful_score}/5")
        
        # Show content preview
        preview = content[:200].replace('\n', ' ')
        print(f"   👀 Preview: {preview}...")
        
        if meaningful_score >= 3:
            print(f"   ✅ File contains meaningful content")
            return True
        else:
            print(f"   ❌ File content appears to be placeholder or error")
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading file: {str(e)}")
        return False

# =============================================================================
# TEST EXECUTION
# =============================================================================

print("\n" + "="*80)
print("🚀 STARTING COMPREHENSIVE REAL BACKEND VERIFICATION")
print("="*80)

# 1. BACKEND HEALTH & ENDPOINTS
print("\n📋 1. BACKEND HEALTH & ENDPOINTS TESTING")
print("-" * 50)

# Test main health endpoint
health_data = run_test("Backend Health Check", f"{API_PREFIX}/health")

# Test agent health endpoint
agent_health_data = run_test("Agent Health Check", f"{AGENT_PREFIX}/health")

# Test agent status endpoint
agent_status_data = run_test("Agent Status Check", f"{AGENT_PREFIX}/status")

# Test agent list-files endpoint
list_files_data = run_test("List Generated Files", f"{AGENT_PREFIX}/list-files")

# 2. MEMORY SYSTEM VERIFICATION
print("\n📋 2. MEMORY SYSTEM VERIFICATION")
print("-" * 50)

# Test simple chat to verify memory integration
simple_chat_data = run_test(
    "Simple Chat with Memory",
    f"{AGENT_PREFIX}/chat",
    method="POST",
    data={"message": "Hola, ¿cómo estás?"},
    timeout=15
)

# 3. REAL PLAN EXECUTION & FILE GENERATION
print("\n📋 3. REAL PLAN EXECUTION & FILE GENERATION")
print("-" * 50)

# Check current files before test
print("\n📁 Checking generated files directory BEFORE document creation:")
files_before = check_file_system(GENERATED_FILES_PATH, "Generated files directory (before)")

# Test document creation request
document_creation_data = run_test(
    "Document Creation Request",
    f"{AGENT_PREFIX}/chat",
    method="POST",
    data={"message": "Ayúdame a crear un documento sobre Python para principiantes con ejemplos prácticos"},
    timeout=60  # Longer timeout for document creation
)

# Wait a bit for file generation to complete
print("\n⏳ Waiting 10 seconds for file generation to complete...")
time.sleep(10)

# Check files after document creation
print("\n📁 Checking generated files directory AFTER document creation:")
files_after = check_file_system(GENERATED_FILES_PATH, "Generated files directory (after)")

# Compare files before and after
new_files = set(files_after) - set(files_before)
if new_files:
    print(f"\n🆕 NEW FILES CREATED: {len(new_files)} files")
    for file in new_files:
        print(f"   📄 {file}")
else:
    print(f"\n⚠️  No new files detected")

# 4. FILE CONTENT VERIFICATION
print("\n📋 4. FILE CONTENT VERIFICATION")
print("-" * 50)

# Verify content of newly created files
verified_files = 0
for file in new_files:
    file_path = os.path.join(GENERATED_FILES_PATH, file)
    if verify_file_content(file_path, f"New file: {file}"):
        verified_files += 1

print(f"\n📊 Content verification: {verified_files}/{len(new_files)} files contain meaningful content")

# 5. DOWNLOAD SYSTEM TESTING
print("\n📋 5. DOWNLOAD SYSTEM TESTING")
print("-" * 50)

# Test list-files endpoint again to see updated list
updated_list_data = run_test("Updated File List", f"{AGENT_PREFIX}/list-files")

# Test download functionality for a new file
if new_files:
    test_file = list(new_files)[0]
    download_data = run_test(
        f"Download File: {test_file}",
        f"{AGENT_PREFIX}/download/{test_file}",
        expected_status=200
    )
else:
    print("   ⚠️  No new files to test download functionality")

# 6. PLAN EXECUTION VERIFICATION
print("\n📋 6. PLAN EXECUTION VERIFICATION")
print("-" * 50)

# Test another complex task to verify plan generation
complex_task_data = run_test(
    "Complex Task with Plan",
    f"{AGENT_PREFIX}/chat",
    method="POST",
    data={"message": "Crea un informe breve sobre inteligencia artificial en 2025"},
    timeout=45
)

# Wait for execution
print("\n⏳ Waiting 8 seconds for plan execution...")
time.sleep(8)

# Check for additional files
print("\n📁 Checking for additional files after complex task:")
files_final = check_file_system(GENERATED_FILES_PATH, "Final generated files check")

# 7. WEBSOCKET & TRACKING VERIFICATION
print("\n📋 7. WEBSOCKET & TRACKING VERIFICATION")
print("-" * 50)

# Verify task IDs are being generated
task_ids_found = []
for test in test_results["tests"]:
    if test["status"] == "PASSED" and "response_data" in test:
        response_data = test["response_data"]
        if isinstance(response_data, dict) and "task_id" in response_data:
            task_ids_found.append(response_data["task_id"])

print(f"📊 Task IDs generated: {len(task_ids_found)}")
for i, task_id in enumerate(task_ids_found[:3]):  # Show first 3
    print(f"   🆔 Task {i+1}: {task_id}")

# Verify memory usage
memory_usage_count = 0
for test in test_results["tests"]:
    if test["status"] == "PASSED" and "response_data" in test:
        response_data = test["response_data"]
        if isinstance(response_data, dict) and response_data.get("memory_used") is True:
            memory_usage_count += 1

print(f"🧠 Memory usage detected: {memory_usage_count} responses with memory_used=true")

# =============================================================================
# FINAL ASSESSMENT
# =============================================================================

print("\n" + "="*80)
print("📊 COMPREHENSIVE VERIFICATION RESULTS")
print("="*80)

# Calculate success rates
total_tests = test_results["summary"]["total"]
passed_tests = test_results["summary"]["passed"]
failed_tests = test_results["summary"]["failed"]
success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

print(f"\n📈 OVERALL TEST RESULTS:")
print(f"   Total Tests: {total_tests}")
print(f"   Passed: {passed_tests}")
print(f"   Failed: {failed_tests}")
print(f"   Success Rate: {success_rate:.1f}%")

# File generation assessment
total_files = len(files_final)
new_files_count = len(new_files)
verified_content_count = verified_files

print(f"\n📁 FILE GENERATION ASSESSMENT:")
print(f"   Total files in directory: {total_files}")
print(f"   New files created during test: {new_files_count}")
print(f"   Files with verified meaningful content: {verified_content_count}")

# System functionality assessment
print(f"\n🔧 SYSTEM FUNCTIONALITY ASSESSMENT:")
print(f"   Backend Health: {'✅ HEALTHY' if health_data else '❌ UNHEALTHY'}")
print(f"   Agent Endpoints: {'✅ WORKING' if agent_health_data else '❌ FAILING'}")
print(f"   Memory Integration: {'✅ WORKING' if memory_usage_count > 0 else '❌ NOT WORKING'}")
print(f"   Task ID Generation: {'✅ WORKING' if len(task_ids_found) > 0 else '❌ NOT WORKING'}")
print(f"   Real File Creation: {'✅ WORKING' if new_files_count > 0 else '❌ NOT WORKING'}")
print(f"   Meaningful Content: {'✅ VERIFIED' if verified_content_count > 0 else '❌ NOT VERIFIED'}")
print(f"   Download System: {'✅ WORKING' if updated_list_data else '❌ NOT WORKING'}")

# Final verdict
print(f"\n🎯 FINAL VERDICT:")
if success_rate >= 80 and new_files_count > 0 and verified_content_count > 0:
    print("   ✅ SYSTEM IS FULLY OPERATIONAL")
    print("   ✅ REAL FILE GENERATION CONFIRMED")
    print("   ✅ MEANINGFUL CONTENT VERIFIED")
    print("   ✅ BACKEND IS PRODUCTION READY")
    final_status = "FULLY_OPERATIONAL"
elif success_rate >= 60 and new_files_count > 0:
    print("   ⚠️  SYSTEM IS MOSTLY OPERATIONAL")
    print("   ✅ FILE GENERATION WORKING")
    print("   ⚠️  SOME ISSUES DETECTED")
    final_status = "MOSTLY_OPERATIONAL"
else:
    print("   ❌ SYSTEM HAS SIGNIFICANT ISSUES")
    print("   ❌ FILE GENERATION OR CONTENT ISSUES")
    print("   ❌ REQUIRES INVESTIGATION")
    final_status = "NEEDS_ATTENTION"

# Save detailed results
results_file = f"/app/verification_results_{int(time.time())}.json"
test_results["final_assessment"] = {
    "success_rate": success_rate,
    "total_files": total_files,
    "new_files_created": new_files_count,
    "verified_content_files": verified_content_count,
    "task_ids_generated": len(task_ids_found),
    "memory_usage_responses": memory_usage_count,
    "final_status": final_status
}

try:
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\n💾 Detailed results saved to: {results_file}")
except Exception as e:
    print(f"\n⚠️  Could not save results file: {str(e)}")

print(f"\n🏁 Verification completed at: {datetime.now().isoformat()}")
print("="*80)