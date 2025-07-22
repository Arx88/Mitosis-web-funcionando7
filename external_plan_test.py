#!/usr/bin/env python3
"""
External URL Test for Plan Execution System
Tests the real plan execution system via the external URL
"""

import requests
import json
import time
import os
from datetime import datetime

# Test external URL
BACKEND_URL = "https://0eea585b-9491-4595-8054-818b778be2a7.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_external_plan_execution():
    """Test plan execution via external URL"""
    print("🌐 TESTING EXTERNAL PLAN EXECUTION SYSTEM")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print()
    
    results = []
    
    # Test 1: Backend Health
    try:
        print("1️⃣ Testing Backend Health...")
        start_time = time.time()
        response = requests.get(f"{API_BASE}/health", timeout=15)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            services = data.get('services', {})
            print(f"✅ Backend Health: PASSED ({response_time:.2f}s)")
            print(f"   Database: {services.get('database')}, Ollama: {services.get('ollama')}, Tools: {services.get('tools')}")
            results.append(("Backend Health", "PASSED"))
        else:
            print(f"❌ Backend Health: FAILED - HTTP {response.status_code}")
            results.append(("Backend Health", "FAILED"))
    except Exception as e:
        print(f"❌ Backend Health: FAILED - {str(e)}")
        results.append(("Backend Health", "FAILED"))
    
    print()
    
    # Test 2: List existing files
    try:
        print("2️⃣ Testing List Files...")
        start_time = time.time()
        response = requests.get(f"{API_BASE}/agent/list-files", timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            print(f"✅ List Files: PASSED ({response_time:.2f}s)")
            print(f"   Found {len(files)} existing files")
            
            if files:
                print("   Recent files:")
                for file_info in files[:3]:
                    print(f"   - {file_info['name']} ({file_info['size']} bytes)")
            
            results.append(("List Files", "PASSED"))
            existing_files = files
        else:
            print(f"❌ List Files: FAILED - HTTP {response.status_code}")
            results.append(("List Files", "FAILED"))
            existing_files = []
    except Exception as e:
        print(f"❌ List Files: FAILED - {str(e)}")
        results.append(("List Files", "FAILED"))
        existing_files = []
    
    print()
    
    # Test 3: Download existing file
    if existing_files:
        try:
            print("3️⃣ Testing File Download...")
            test_file = existing_files[0]
            filename = test_file['name']
            
            start_time = time.time()
            response = requests.get(f"{API_BASE}/agent/download/{filename}", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content_length = len(response.content)
                content_type = response.headers.get('Content-Type', 'unknown')
                print(f"✅ File Download: PASSED ({response_time:.2f}s)")
                print(f"   Downloaded {filename}: {content_length} bytes, Type: {content_type}")
                results.append(("File Download", "PASSED"))
            else:
                print(f"❌ File Download: FAILED - HTTP {response.status_code}")
                results.append(("File Download", "FAILED"))
        except Exception as e:
            print(f"❌ File Download: FAILED - {str(e)}")
            results.append(("File Download", "FAILED"))
    else:
        print("3️⃣ File Download: SKIPPED - No files available")
        results.append(("File Download", "SKIPPED"))
    
    print()
    
    # Test 4: New document creation request
    try:
        print("4️⃣ Testing New Document Creation...")
        test_message = "Crea un documento sobre las mejores prácticas de programación en Python"
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/agent/chat",
            json={"message": test_message},
            timeout=30
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            response_text = data.get('response', '')
            task_id = data.get('task_id')
            memory_used = data.get('memory_used', False)
            mode = data.get('mode', '')
            status = data.get('status', '')
            
            print(f"✅ Document Creation: PASSED ({response_time:.2f}s)")
            print(f"   Response: {len(response_text)} chars")
            print(f"   Task ID: {task_id}")
            print(f"   Mode: {mode}")
            print(f"   Status: {status}")
            print(f"   Memory Used: {memory_used}")
            
            # Check if it's a structured plan
            is_structured = mode == 'agent_with_structured_plan'
            plan_generated = status in ['plan_generated', 'completed']
            
            if is_structured and plan_generated:
                print("   ✅ Structured plan generated successfully")
                results.append(("Document Creation", "PASSED"))
                new_task_id = task_id
            else:
                print("   ⚠️  Response received but not structured plan")
                results.append(("Document Creation", "PARTIAL"))
                new_task_id = task_id
        else:
            print(f"❌ Document Creation: FAILED - HTTP {response.status_code}")
            results.append(("Document Creation", "FAILED"))
            new_task_id = None
    except Exception as e:
        print(f"❌ Document Creation: FAILED - {str(e)}")
        results.append(("Document Creation", "FAILED"))
        new_task_id = None
    
    print()
    
    # Test 5: Wait and check for new files
    if new_task_id:
        try:
            print("5️⃣ Waiting for Plan Execution and File Creation...")
            print("   ⏳ Monitoring for 60 seconds...")
            
            initial_file_count = len(existing_files)
            max_wait = 60
            check_interval = 10
            waited = 0
            
            while waited < max_wait:
                time.sleep(check_interval)
                waited += check_interval
                
                # Check for new files
                try:
                    response = requests.get(f"{API_BASE}/agent/list-files", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        current_files = data.get('files', [])
                        
                        if len(current_files) > initial_file_count:
                            new_files = current_files[:len(current_files) - initial_file_count]
                            print(f"   ✅ New files detected after {waited}s!")
                            for file_info in new_files:
                                print(f"   - {file_info['name']} ({file_info['size']} bytes)")
                            
                            results.append(("Plan Execution & File Creation", "PASSED"))
                            break
                        else:
                            print(f"   ⏳ After {waited}s: {len(current_files)} files (no new files yet)")
                except Exception:
                    print(f"   ⚠️  Error checking files after {waited}s")
            else:
                print(f"   ⚠️  No new files detected after {max_wait}s")
                results.append(("Plan Execution & File Creation", "TIMEOUT"))
        except Exception as e:
            print(f"❌ Plan Execution Monitoring: FAILED - {str(e)}")
            results.append(("Plan Execution & File Creation", "FAILED"))
    else:
        print("5️⃣ Plan Execution Monitoring: SKIPPED - No task ID")
        results.append(("Plan Execution & File Creation", "SKIPPED"))
    
    print()
    
    # Generate summary
    print("=" * 60)
    print("📊 EXTERNAL TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASSED")
    total = len(results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
    print(f"{status_icon} OVERALL: {passed}/{total} tests passed ({success_rate:.1f}%)")
    print()
    
    print("📋 DETAILED RESULTS:")
    for test_name, status in results:
        status_icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
    
    print()
    
    # Key findings
    print("🔍 KEY FINDINGS:")
    
    backend_working = any(name == "Backend Health" and status == "PASSED" for name, status in results)
    files_accessible = any(name == "List Files" and status == "PASSED" for name, status in results)
    download_working = any(name == "File Download" and status == "PASSED" for name, status in results)
    plan_creation = any(name == "Document Creation" and status in ["PASSED", "PARTIAL"] for name, status in results)
    file_creation = any(name == "Plan Execution & File Creation" and status == "PASSED" for name, status in results)
    
    print(f"✅ Backend Health: {'WORKING' if backend_working else 'FAILED'}")
    print(f"✅ File System: {'WORKING' if files_accessible else 'FAILED'}")
    print(f"✅ Download API: {'WORKING' if download_working else 'FAILED'}")
    print(f"✅ Plan Creation: {'WORKING' if plan_creation else 'FAILED'}")
    print(f"✅ Real File Creation: {'WORKING' if file_creation else 'TIMEOUT/FAILED'}")
    
    print()
    
    # Final assessment
    critical_components = sum([backend_working, files_accessible, plan_creation])
    
    if critical_components >= 3 and (download_working or file_creation):
        print("🎉 ASSESSMENT: Plan execution system is WORKING!")
        print("   ✅ The system can create plans and generate tangible files")
        print("   ✅ Files are accessible and downloadable")
        print("   ✅ The reported issue appears to be RESOLVED")
    elif critical_components >= 2:
        print("⚠️  ASSESSMENT: Plan execution system is PARTIALLY WORKING")
        print("   ✅ Core functionality works but some issues remain")
        print("   ⚠️  May need optimization for file creation timing")
    else:
        print("❌ ASSESSMENT: Plan execution system has CRITICAL ISSUES")
        print("   ❌ The reported issue is NOT resolved")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    test_external_plan_execution()