#!/usr/bin/env python3
"""
Focused Real File Generation Test

This test specifically focuses on verifying that the backend is creating real files
when document creation requests are made.
"""

import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "https://0c432462-b347-4890-be94-906c923a463b.preview.emergentagent.com"
GENERATED_FILES_PATH = "/app/backend/static/generated_files"

print(f"🧪 FOCUSED REAL FILE GENERATION TEST")
print(f"Test started at: {datetime.now().isoformat()}")

# Get initial file count
initial_files = set(os.listdir(GENERATED_FILES_PATH)) if os.path.exists(GENERATED_FILES_PATH) else set()
print(f"📁 Initial files count: {len(initial_files)}")

# Test document creation with a unique request
unique_id = int(time.time())
test_message = f"Crea un documento técnico sobre desarrollo web moderno en 2025 - Test {unique_id}"

print(f"\n🚀 Sending document creation request:")
print(f"   Message: {test_message}")

try:
    response = requests.post(
        f"{BASE_URL}/api/agent/chat",
        json={"message": test_message},
        timeout=60
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Task ID: {data.get('task_id', 'N/A')}")
        print(f"   Memory Used: {data.get('memory_used', 'N/A')}")
        print(f"   Response Length: {len(data.get('response', ''))}")
        
        # Wait for file generation
        print(f"\n⏳ Waiting 30 seconds for file generation...")
        time.sleep(30)
        
        # Check for new files
        current_files = set(os.listdir(GENERATED_FILES_PATH)) if os.path.exists(GENERATED_FILES_PATH) else set()
        new_files = current_files - initial_files
        
        print(f"\n📊 RESULTS:")
        print(f"   Initial files: {len(initial_files)}")
        print(f"   Current files: {len(current_files)}")
        print(f"   New files created: {len(new_files)}")
        
        if new_files:
            print(f"\n🆕 NEW FILES CREATED:")
            for file in sorted(new_files):
                file_path = os.path.join(GENERATED_FILES_PATH, file)
                size = os.path.getsize(file_path)
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"   📄 {file} ({size} bytes, {mtime.strftime('%H:%M:%S')})")
                
                # Check content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    preview = content[:100].replace('\n', ' ')
                    print(f"      Preview: {preview}...")
            
            print(f"\n✅ FILE GENERATION CONFIRMED: {len(new_files)} files created")
        else:
            print(f"\n⚠️  NO NEW FILES DETECTED")
            
    else:
        print(f"   ❌ Request failed: {response.text}")
        
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

print(f"\n🏁 Test completed at: {datetime.now().isoformat()}")