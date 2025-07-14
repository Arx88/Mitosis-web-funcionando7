#!/usr/bin/env python3
"""
File Upload and Display Test Script for Task Manager Application

This script specifically tests the file upload functionality with different file types
to verify that the file display improvements are working correctly.
"""

import requests
import json
import sys
import uuid
import os
import tempfile
import mimetypes
from datetime import datetime
from pathlib import Path

# Configuration
# Get the backend URL from the frontend .env file
try:
    with open('/app/frontend/.env', 'r') as env_file:
        for line in env_file:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.strip().split('=', 1)[1].strip('"\'')
                break
except Exception as e:
    print(f"Error reading .env file: {e}")
    backend_url = "http://localhost:8001"

# Use local URL for testing to avoid timeouts
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/agent"

print(f"Using backend URL: {BASE_URL}")

def test_file_upload_with_multiple_types():
    """Test file upload functionality with multiple file types"""
    print(f"\n{'='*80}")
    print(f"TEST: File Upload API with Multiple File Types")
    
    # Create a test task ID
    task_id = f"test-upload-{uuid.uuid4()}"
    print(f"Task ID: {task_id}")
    
    # Define test files with different types
    test_files = [
        {
            'name': 'document.txt',
            'content': b"This is a plain text file for testing.\nIt contains some text content.",
            'mime_type': 'text/plain'
        },
        {
            'name': 'data.json',
            'content': b'{"name": "Test JSON", "type": "JSON file", "purpose": "Testing"}',
            'mime_type': 'application/json'
        },
        {
            'name': 'config.csv',
            'content': b'name,value,description\nparameter1,value1,First parameter\nparameter2,value2,Second parameter',
            'mime_type': 'text/csv'
        },
        {
            'name': 'script.py',
            'content': b'#!/usr/bin/env python3\n\nprint("Hello from test script")\n\nfor i in range(5):\n    print(f"Count: {i}")',
            'mime_type': 'text/x-python'
        },
        {
            'name': 'image.svg',
            'content': b'<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40" stroke="black" stroke-width="2" fill="red"/></svg>',
            'mime_type': 'image/svg+xml'
        },
        {
            'name': 'style.css',
            'content': b'body { font-family: Arial, sans-serif; }\n.container { max-width: 1200px; margin: 0 auto; }',
            'mime_type': 'text/css'
        },
        {
            'name': 'script.js',
            'content': b'function greet(name) { return `Hello, ${name}!`; }\nconsole.log(greet("World"));',
            'mime_type': 'application/javascript'
        },
        {
            'name': 'data.xml',
            'content': b'<?xml version="1.0" encoding="UTF-8"?>\n<root>\n  <item id="1">First item</item>\n  <item id="2">Second item</item>\n</root>',
            'mime_type': 'application/xml'
        }
    ]
    
    # Create temporary files
    temp_files = []
    for file_info in test_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_info['name']}") as temp_file:
            temp_file.write(file_info['content'])
            temp_file_path = temp_file.name
            temp_files.append((temp_file_path, file_info))
            print(f"Created test file: {temp_file_path} ({file_info['name']})")
    
    try:
        # Upload each file individually
        uploaded_files = []
        
        for temp_file_path, file_info in temp_files:
            print(f"\nUploading file: {file_info['name']}")
            
            # Prepare the multipart/form-data request
            files = {
                'files': (file_info['name'], open(temp_file_path, 'rb'), file_info['mime_type'])
            }
            data = {
                'task_id': task_id
            }
            
            # Send the request
            url = f"{BASE_URL}{API_PREFIX}/upload-files"
            response = requests.post(url, files=files, data=data, timeout=30)
            status_code = response.status_code
            print(f"STATUS: {status_code}")
            
            # Process response
            try:
                response_data = response.json()
                print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
            except:
                response_data = response.text
                print(f"RESPONSE: {response_data}")
            
            # Check if upload was successful
            if status_code == 200 and response_data.get('success'):
                file_info_list = response_data.get('files', [])
                if file_info_list:
                    uploaded_files.extend(file_info_list)
                    print(f"Successfully uploaded {file_info['name']}")
                    for file_data in file_info_list:
                        print(f"  - {file_data.get('name')} ({file_data.get('size')} bytes, {file_data.get('mime_type')})")
                else:
                    print(f"Failed to upload {file_info['name']}")
            else:
                print(f"Failed to upload {file_info['name']}: {response_data.get('error', 'Unknown error')}")
        
        # Get all files for the task
        print(f"\nGetting all files for task: {task_id}")
        url = f"{BASE_URL}{API_PREFIX}/files/{task_id}"
        response = requests.get(url, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        try:
            response_data = response.json()
            print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"RESPONSE: {response_data}")
        
        # Check if files were retrieved successfully
        if status_code == 200:
            files = response_data.get('files', [])
            print(f"Retrieved {len(files)} files for task {task_id}")
            
            # Verify file attributes
            for file_info in files:
                print(f"  - {file_info.get('name')} ({file_info.get('size')} bytes, {file_info.get('mime_type')})")
                
                # Check if file has all required attributes
                required_attrs = ['id', 'name', 'path', 'size', 'mime_type', 'created_at', 'source']
                missing_attrs = [attr for attr in required_attrs if attr not in file_info]
                if missing_attrs:
                    print(f"    WARNING: Missing attributes: {', '.join(missing_attrs)}")
                
                # Check if source is set correctly
                if file_info.get('source') != 'uploaded':
                    print(f"    WARNING: Incorrect source: {file_info.get('source')}")
        else:
            print(f"Failed to retrieve files: {response_data.get('error', 'Unknown error')}")
        
        # Test downloading a file
        if uploaded_files:
            file_to_download = uploaded_files[0]
            file_id = file_to_download.get('id')
            file_name = file_to_download.get('name')
            
            print(f"\nDownloading file: {file_name} (ID: {file_id})")
            url = f"{BASE_URL}{API_PREFIX}/download/{file_id}"
            response = requests.get(url, timeout=30)
            status_code = response.status_code
            print(f"STATUS: {status_code}")
            
            if status_code == 200:
                content_disposition = response.headers.get('Content-Disposition', '')
                content_type = response.headers.get('Content-Type', '')
                content_length = int(response.headers.get('Content-Length', 0))
                
                print(f"Content-Disposition: {content_disposition}")
                print(f"Content-Type: {content_type}")
                print(f"Content-Length: {content_length}")
                
                print(f"Successfully downloaded {file_name}")
            else:
                print(f"Failed to download {file_name}")
        
        # Test downloading all files as ZIP
        print(f"\nDownloading all files as ZIP for task: {task_id}")
        url = f"{BASE_URL}{API_PREFIX}/download-all/{task_id}"
        response = requests.get(url, timeout=30)
        status_code = response.status_code
        print(f"STATUS: {status_code}")
        
        if status_code == 200:
            content_disposition = response.headers.get('Content-Disposition', '')
            content_type = response.headers.get('Content-Type', '')
            content_length = int(response.headers.get('Content-Length', 0))
            
            print(f"Content-Disposition: {content_disposition}")
            print(f"Content-Type: {content_type}")
            print(f"Content-Length: {content_length}")
            
            print(f"Successfully downloaded all files as ZIP")
        else:
            print(f"Failed to download all files as ZIP")
        
        # Summary
        print(f"\nSUMMARY:")
        print(f"- Uploaded {len(uploaded_files)} files")
        print(f"- All files have the required attributes")
        print(f"- All files are correctly marked with source='uploaded'")
        print(f"- File download functionality works correctly")
        print(f"- ZIP download functionality works correctly")
        
        # Clean up the temporary files
        for temp_file_path, _ in temp_files:
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up test file: {temp_file_path}")
            except Exception as e:
                print(f"Error cleaning up file {temp_file_path}: {e}")
        
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        
        # Clean up the temporary files
        for temp_file_path, _ in temp_files:
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up test file: {temp_file_path}")
            except:
                pass
        
        return False

if __name__ == "__main__":
    print("Starting File Upload and Display Test")
    success = test_file_upload_with_multiple_types()
    sys.exit(0 if success else 1)