#!/usr/bin/env python3
"""
Test script for DeepResearch functionality
This script tests the DeepResearch progress tracking API endpoint and the Chat API with [DeepResearch] prefix
"""

import requests
import json
import time
import uuid
from datetime import datetime

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

def test_deep_research_progress_endpoint():
    """Test the DeepResearch progress tracking API endpoint"""
    print("\n" + "="*80)
    print("TEST: DeepResearch Progress Tracking API")
    
    # Create a task ID for testing
    task_id = f"test-{uuid.uuid4()}"
    
    # Test the progress tracking endpoint
    url = f"{BASE_URL}{API_PREFIX}/deep-research/progress/{task_id}"
    print(f"URL: {url}")
    print(f"METHOD: GET")
    
    # Send the request
    response = requests.get(url, timeout=10)
    status_code = response.status_code
    print(f"STATUS: {status_code}")
    
    # Process response
    try:
        response_data = response.json()
        print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
    except:
        response_data = response.text
        print(f"RESPONSE: {response_data}")
    
    # Check if the response has the expected structure
    expected_keys = ["task_id", "is_active", "current_progress", "current_step", "steps"]
    missing_keys = []
    
    for key in expected_keys:
        if key not in response_data:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Missing expected keys: {', '.join(missing_keys)}")
        return False, response_data
    
    # Check if steps has the expected structure
    steps = response_data.get("steps", [])
    if not steps or len(steps) == 0:
        print("❌ No steps found in the response")
        return False, response_data
    
    # Check if each step has the expected structure
    expected_step_keys = ["id", "title", "description", "status"]
    for i, step in enumerate(steps):
        for key in expected_step_keys:
            if key not in step:
                print(f"❌ Step {i+1} is missing key: {key}")
                return False, response_data
    
    print(f"✅ DeepResearch progress tracking API endpoint is working correctly")
    print(f"Found {len(steps)} steps with the expected structure")
    
    return True, response_data

def test_deep_research_chat_api():
    """Test the Chat API with [DeepResearch] prefix"""
    print("\n" + "="*80)
    print("TEST: Chat API with [DeepResearch] prefix")
    
    # Create a task ID for testing
    task_id = f"test-{uuid.uuid4()}"
    
    # Test the Chat API with DeepResearch prefix
    url = f"{BASE_URL}{API_PREFIX}/chat"
    print(f"URL: {url}")
    print(f"METHOD: POST")
    
    # Create a message with DeepResearch prefix
    data = {
        "message": "[DeepResearch] renewable energy trends",
        "search_mode": "deepsearch",
        "context": {
            "task_id": task_id
        }
    }
    
    print(f"DATA: {json.dumps(data, indent=2)}")
    
    # Send the request
    response = requests.post(url, json=data, timeout=30)
    status_code = response.status_code
    print(f"STATUS: {status_code}")
    
    # Process response
    try:
        response_data = response.json()
        print(f"RESPONSE: {json.dumps(response_data, indent=2)}")
    except:
        response_data = response.text
        print(f"RESPONSE: {response_data}")
    
    # Check if the response has the expected structure
    expected_keys = ["response", "tool_results", "search_mode"]
    missing_keys = []
    
    for key in expected_keys:
        if key not in response_data:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Missing expected keys: {', '.join(missing_keys)}")
        return False, response_data
    
    # Check if search_mode is set to deepsearch
    if response_data.get("search_mode") != "deepsearch":
        print(f"❌ Expected search_mode to be 'deepsearch', got '{response_data.get('search_mode')}'")
        return False, response_data
    
    # Check if search_data is present and has the expected structure
    search_data = response_data.get("search_data")
    if not search_data:
        print("❌ No search_data found in the response")
        return False, response_data
    
    # Check if search_data has the expected structure
    expected_search_data_keys = ["query", "directAnswer", "sources", "type", "key_findings", "recommendations"]
    missing_search_data_keys = []
    
    for key in expected_search_data_keys:
        if key not in search_data:
            missing_search_data_keys.append(key)
    
    if missing_search_data_keys:
        print(f"❌ search_data is missing expected keys: {', '.join(missing_search_data_keys)}")
        return False, response_data
    
    # Check if type is set to deepsearch
    if search_data.get("type") != "deepsearch":
        print(f"❌ Expected search_data.type to be 'deepsearch', got '{search_data.get('type')}'")
        return False, response_data
    
    print(f"✅ Chat API with [DeepResearch] prefix is working correctly")
    print(f"search_mode is set to 'deepsearch' and search_data has the expected structure")
    
    # Now test the progress tracking endpoint for this task
    print("\nTesting progress tracking for the task...")
    
    # Wait a moment for the task to start
    time.sleep(2)
    
    # Test the progress tracking endpoint
    progress_url = f"{BASE_URL}{API_PREFIX}/deep-research/progress/{task_id}"
    progress_response = requests.get(progress_url, timeout=10)
    
    try:
        progress_data = progress_response.json()
        print(f"PROGRESS DATA: {json.dumps(progress_data, indent=2)}")
        
        # Check if the task is active
        if progress_data.get("is_active"):
            print(f"✅ Task is active and progress tracking is working")
            print(f"Current progress: {progress_data.get('current_progress')}%")
            print(f"Current step: {progress_data.get('current_step')}")
        else:
            print(f"⚠️ Task is not active, but progress tracking endpoint is working")
    except:
        print(f"❌ Error getting progress data")
    
    return True, response_data

def main():
    """Run all tests"""
    print("Starting DeepResearch Functionality Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: DeepResearch Progress Tracking API
    progress_success, progress_data = test_deep_research_progress_endpoint()
    
    # Test 2: Chat API with [DeepResearch] prefix
    chat_success, chat_data = test_deep_research_chat_api()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"DeepResearch Progress Tracking API: {'✅ PASSED' if progress_success else '❌ FAILED'}")
    print(f"Chat API with [DeepResearch] prefix: {'✅ PASSED' if chat_success else '❌ FAILED'}")
    print("="*80)
    
    return 0 if progress_success and chat_success else 1

if __name__ == "__main__":
    main()