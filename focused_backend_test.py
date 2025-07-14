#!/usr/bin/env python3
"""
Focused Backend API Test Script for Review Request
Testing specific endpoints mentioned in the review:
1. POST /api/agent/chat (with WebSearch/DeepSearch prefixes)
2. POST /api/agent/upload-files
3. GET /api/agent/deep-research/progress/{task_id}
4. POST /api/agent/create-test-files/{task_id}
"""

import requests
import json
import uuid
import tempfile
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"

def test_chat_api_with_websearch():
    """Test Chat API with [WebSearch] prefix"""
    print(f"\n{'='*80}")
    print(f"TEST: Chat API with [WebSearch] prefix")
    
    url = f"{BASE_URL}{API_PREFIX}/chat"
    data = {
        "message": "[WebSearch] artificial intelligence trends 2025",
        "search_mode": "websearch"
    }
    
    print(f"URL: {url}")
    print(f"DATA: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        response_data = response.json()
        print(f"RESPONSE KEYS: {list(response_data.keys())}")
        
        # Check for expected structure
        success = (
            status_code == 200 and
            response_data.get("search_mode") == "websearch" and
            "search_data" in response_data and
            "sources" in response_data.get("search_data", {})
        )
        
        if success:
            search_data = response_data["search_data"]
            print(f"✅ WebSearch successful:")
            print(f"   - Sources found: {len(search_data.get('sources', []))}")
            print(f"   - Images found: {len(search_data.get('images', []))}")
            print(f"   - Direct answer: {search_data.get('directAnswer', '')[:100]}...")
        else:
            print(f"❌ WebSearch failed")
            
        return success, response_data
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None

def test_chat_api_with_deepsearch():
    """Test Chat API with [DeepResearch] prefix"""
    print(f"\n{'='*80}")
    print(f"TEST: Chat API with [DeepResearch] prefix")
    
    task_id = f"test-deepresearch-{uuid.uuid4()}"
    url = f"{BASE_URL}{API_PREFIX}/chat"
    data = {
        "message": "[DeepResearch] artificial intelligence in education",
        "search_mode": "deepsearch",
        "context": {
            "task_id": task_id
        }
    }
    
    print(f"URL: {url}")
    print(f"TASK_ID: {task_id}")
    print(f"DATA: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=60)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        response_data = response.json()
        print(f"RESPONSE KEYS: {list(response_data.keys())}")
        
        # Check for expected structure
        success = (
            status_code == 200 and
            response_data.get("search_mode") == "deepsearch" and
            "search_data" in response_data and
            "created_files" in response_data
        )
        
        if success:
            search_data = response_data["search_data"]
            created_files = response_data["created_files"]
            print(f"✅ DeepResearch successful:")
            print(f"   - Sources analyzed: {search_data.get('sources_analyzed', 0)}")
            print(f"   - Key findings: {len(search_data.get('key_findings', []))}")
            print(f"   - Recommendations: {len(search_data.get('recommendations', []))}")
            print(f"   - Created files: {len(created_files)}")
            
            if created_files:
                for file_info in created_files:
                    print(f"     - {file_info.get('name')} ({file_info.get('size')} bytes)")
        else:
            print(f"❌ DeepResearch failed")
            
        return success, response_data, task_id
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None, None

def test_file_upload_api():
    """Test File Upload API"""
    print(f"\n{'='*80}")
    print(f"TEST: File Upload API")
    
    task_id = f"test-upload-{uuid.uuid4()}"
    url = f"{BASE_URL}{API_PREFIX}/upload-files"
    
    print(f"URL: {url}")
    print(f"TASK_ID: {task_id}")
    
    try:
        # Create a test file
        test_content = b"This is a test file for upload functionality testing.\nCreated for backend API testing."
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        # Prepare the upload
        files = {
            'files': ('test_upload.txt', open(temp_file_path, 'rb'), 'text/plain')
        }
        data = {
            'task_id': task_id
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        response_data = response.json()
        print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        
        # Check for expected structure
        success = (
            status_code == 200 and
            response_data.get("success") == True and
            "files" in response_data and
            len(response_data["files"]) > 0
        )
        
        if success:
            uploaded_files = response_data["files"]
            print(f"✅ File upload successful:")
            for file_info in uploaded_files:
                print(f"   - {file_info.get('name')} ({file_info.get('size')} bytes)")
                print(f"     ID: {file_info.get('id')}")
                print(f"     Source: {file_info.get('source')}")
        else:
            print(f"❌ File upload failed")
        
        # Clean up
        os.unlink(temp_file_path)
        
        return success, response_data
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None

def test_progress_tracking_api(task_id):
    """Test DeepResearch Progress Tracking API"""
    print(f"\n{'='*80}")
    print(f"TEST: DeepResearch Progress Tracking API")
    
    url = f"{BASE_URL}{API_PREFIX}/deep-research/progress/{task_id}"
    
    print(f"URL: {url}")
    print(f"TASK_ID: {task_id}")
    
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        response_data = response.json()
        print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        
        # Check for expected structure
        success = (
            status_code == 200 and
            "task_id" in response_data and
            "current_progress" in response_data and
            "steps" in response_data
        )
        
        if success:
            print(f"✅ Progress tracking successful:")
            print(f"   - Task ID: {response_data.get('task_id')}")
            print(f"   - Current progress: {response_data.get('current_progress')}%")
            print(f"   - Is active: {response_data.get('is_active')}")
            print(f"   - Steps defined: {len(response_data.get('steps', []))}")
        else:
            print(f"❌ Progress tracking failed")
            
        return success, response_data
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None

def test_create_test_files_api():
    """Test Create Test Files API"""
    print(f"\n{'='*80}")
    print(f"TEST: Create Test Files API")
    
    task_id = f"test-files-{uuid.uuid4()}"
    url = f"{BASE_URL}{API_PREFIX}/create-test-files/{task_id}"
    
    print(f"URL: {url}")
    print(f"TASK_ID: {task_id}")
    
    try:
        response = requests.post(url, timeout=10)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        response_data = response.json()
        print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        
        # Check for expected structure
        success = (
            status_code == 200 and
            response_data.get("success") == True and
            "files" in response_data and
            len(response_data["files"]) > 0
        )
        
        if success:
            created_files = response_data["files"]
            print(f"✅ Test files creation successful:")
            print(f"   - Files created: {len(created_files)}")
            for file_info in created_files:
                print(f"     - {file_info.get('name')} ({file_info.get('size')} bytes)")
                print(f"       Source: {file_info.get('source')}")
        else:
            print(f"❌ Test files creation failed")
            
        return success, response_data
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None

def main():
    """Run all focused tests"""
    print("="*80)
    print("FOCUSED BACKEND API TESTING - REVIEW REQUEST")
    print("="*80)
    print(f"Testing specific endpoints mentioned in review:")
    print(f"1. POST /api/agent/chat (with WebSearch/DeepSearch prefixes)")
    print(f"2. POST /api/agent/upload-files")
    print(f"3. GET /api/agent/deep-research/progress/{{task_id}}")
    print(f"4. POST /api/agent/create-test-files/{{task_id}}")
    print("="*80)
    
    results = []
    
    # Test 1: Chat API with WebSearch
    success, data = test_chat_api_with_websearch()
    results.append(("Chat API with [WebSearch]", success))
    
    # Test 2: Chat API with DeepSearch
    success, data, task_id = test_chat_api_with_deepsearch()
    results.append(("Chat API with [DeepResearch]", success))
    
    # Test 3: Progress Tracking (if we have a task_id from DeepSearch)
    if task_id:
        success, data = test_progress_tracking_api(task_id)
        results.append(("DeepResearch Progress Tracking", success))
    
    # Test 4: File Upload API
    success, data = test_file_upload_api()
    results.append(("File Upload API", success))
    
    # Test 5: Create Test Files API
    success, data = test_create_test_files_api()
    results.append(("Create Test Files API", success))
    
    # Summary
    print(f"\n{'='*80}")
    print("FOCUSED TEST SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {passed_tests/total_tests*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    if failed_tests > 0:
        print(f"\n⚠️  {failed_tests} test(s) failed. Check the detailed output above for issues.")
    else:
        print(f"\n🎉 All tests passed! Backend APIs are working correctly for welcome page functionality.")

if __name__ == "__main__":
    main()