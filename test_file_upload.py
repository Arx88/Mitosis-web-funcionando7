#!/usr/bin/env python3
"""
File Upload Test Script for Task Manager Application

This script specifically tests the file upload functionality of the backend API,
focusing on multiple file uploads.
"""

import requests
import json
import sys
import uuid
import os
import tempfile
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"
UPLOAD_ENDPOINT = f"{API_PREFIX}/upload-files"

def test_multiple_file_upload():
    """Test uploading multiple files at once"""
    print(f"\n{'='*80}")
    print(f"TEST: Multiple File Upload API")
    url = f"{BASE_URL}{UPLOAD_ENDPOINT}"
    print(f"URL: {url}")
    print(f"METHOD: POST (multipart/form-data)")
    
    # Create a unique task ID for this test
    task_id = f"test-upload-{uuid.uuid4()}"
    print(f"Task ID: {task_id}")
    
    try:
        # Create multiple temporary test files with different content and types
        temp_files = []
        file_contents = [
            ("test_text.txt", "This is a plain text file for testing uploads.\nIt contains some text content.", "text/plain"),
            ("test_json.json", '{"name": "Test JSON", "purpose": "Testing file uploads", "type": "JSON"}', "application/json"),
            ("test_csv.csv", "name,age,city\nJohn,30,New York\nMary,25,Los Angeles\nBob,40,Chicago", "text/csv"),
            ("test_python.py", 'print("Hello from Python file")\n\ndef test_function():\n    return "This is a test function"', "text/x-python"),
            ("test_html.html", "<html><head><title>Test HTML</title></head><body><h1>Test HTML File</h1><p>This is a test HTML file for upload testing.</p></body></html>", "text/html")
        ]
        
        for filename, content, mime_type in file_contents:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}') as temp_file:
                temp_file.write(content.encode('utf-8'))
                temp_files.append((temp_file.name, filename, mime_type))
                print(f"Created test file: {temp_file.name} as {filename}")
        
        # Prepare the multipart/form-data request
        files = []
        for temp_path, filename, mime_type in temp_files:
            files.append(('files', (filename, open(temp_path, 'rb'), mime_type)))
        
        data = {
            'task_id': task_id
        }
        
        # Send the request
        print(f"Sending request with {len(files)} files...")
        response = requests.post(url, files=files, data=data, timeout=10)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        # Process response
        try:
            response_data = response.json()
            print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data}")
        
        # Check status code
        if status_code == 200:
            print("✅ Status code check passed (200 OK)")
        else:
            print(f"❌ Status code check failed (expected 200, got {status_code})")
        
        # Check expected keys
        expected_keys = ["success", "message", "files", "task_id"]
        missing_keys = []
        
        for key in expected_keys:
            if key not in response_data:
                missing_keys.append(key)
        
        if not missing_keys:
            print("✅ Response structure check passed (all required keys present)")
        else:
            print(f"❌ Response structure check failed (missing keys: {', '.join(missing_keys)})")
        
        # Check if files were actually uploaded
        if "files" in response_data:
            files_info = response_data.get("files", [])
            if len(files_info) == len(file_contents):
                print(f"✅ File count check passed (expected {len(file_contents)}, got {len(files_info)})")
                print(f"Successfully uploaded {len(files_info)} file(s):")
                for file_info in files_info:
                    print(f"  - {file_info.get('name')} ({file_info.get('size')} bytes, {file_info.get('mime_type')})")
            else:
                print(f"❌ File count check failed (expected {len(file_contents)}, got {len(files_info)})")
        else:
            print("❌ No files were uploaded")
        
        # Verify files are accessible via the Get Task Files API
        print("\nVerifying files are accessible via Get Task Files API...")
        files_url = f"{BASE_URL}{API_PREFIX}/files/{task_id}"
        files_response = requests.get(files_url, timeout=10)
        
        if files_response.status_code == 200:
            files_data = files_response.json()
            if "files" in files_data and len(files_data["files"]) == len(file_contents):
                print(f"✅ Files accessible check passed (all {len(file_contents)} files accessible)")
            else:
                print(f"❌ Files accessible check failed (expected {len(file_contents)}, got {len(files_data.get('files', []))})")
        else:
            print(f"❌ Files accessible check failed (status code: {files_response.status_code})")
        
        # Clean up the temporary files
        for temp_path, _, _ in temp_files:
            try:
                os.unlink(temp_path)
                print(f"Cleaned up test file: {temp_path}")
            except Exception as e:
                print(f"Error cleaning up file {temp_path}: {str(e)}")
        
        # Overall result
        if status_code == 200 and not missing_keys and "files" in response_data and len(response_data["files"]) == len(file_contents):
            print("\n✅ OVERALL RESULT: PASSED")
            return True
        else:
            print("\n❌ OVERALL RESULT: FAILED")
            return False
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("\n❌ OVERALL RESULT: FAILED (Exception)")
        
        # Clean up the temporary files if they exist
        if 'temp_files' in locals():
            for temp_path, _, _ in temp_files:
                try:
                    os.unlink(temp_path)
                    print(f"Cleaned up test file: {temp_path}")
                except:
                    pass
        
        return False

def main():
    """Run the file upload tests"""
    print("Starting Task Manager File Upload Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run the multiple file upload test
    result = test_multiple_file_upload()
    
    # Return exit code based on test result
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())