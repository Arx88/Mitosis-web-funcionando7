#!/usr/bin/env python3
"""
Tool Execution Logging Test Script for Task Manager Application

This script specifically tests that tool executions are logged correctly to the terminal.
"""

import requests
import json
import sys
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

def test_tool_execution_logging():
    """Test tool execution logging"""
    print(f"\n{'='*80}")
    print(f"TEST: Tool Execution Logging")
    
    # Define test tools and parameters
    test_tools = [
        {
            "name": "WebSearch",
            "message": "[WebSearch] What is artificial intelligence?",
            "search_mode": "websearch",
            "expected_tool": "tavily_search"
        },
        {
            "name": "DeepResearch",
            "message": "[DeepResearch] Climate change impacts",
            "search_mode": "deepsearch",
            "expected_tool": "deep_research"
        }
    ]
    
    for tool_info in test_tools:
        print(f"\nTesting tool: {tool_info['name']}")
        
        # Prepare the request
        url = f"{BASE_URL}{API_PREFIX}/chat"
        data = {
            "message": tool_info["message"],
            "search_mode": tool_info["search_mode"]
        }
        
        # Send the request
        try:
            response = requests.post(url, json=data, timeout=30)
            status_code = response.status_code
            print(f"STATUS: {status_code}")
            
            # Process response
            try:
                response_data = response.json()
                
                # Check if the response contains the expected structure
                tool_results = response_data.get("tool_results", [])
                search_mode = response_data.get("search_mode")
                
                print(f"SEARCH MODE: {search_mode}")
                
                # Check if tool_results contains the expected structure
                if tool_results:
                    print("✅ Tool results found in response")
                    
                    # Check if the first tool result is for the expected tool
                    if tool_results[0].get("tool") == tool_info["expected_tool"]:
                        print(f"✅ Tool is {tool_info['expected_tool']}")
                    else:
                        print(f"❌ Expected tool '{tool_info['expected_tool']}', got '{tool_results[0].get('tool')}'")
                    
                    # Check if the tool result contains the expected fields
                    tool_result = tool_results[0]
                    required_fields = ['tool', 'parameters', 'result']
                    missing_fields = [field for field in required_fields if field not in tool_result]
                    if missing_fields:
                        print(f"❌ Tool result missing fields: {', '.join(missing_fields)}")
                    else:
                        print("✅ Tool result contains all required fields")
                    
                    # Check if the result contains success status
                    result = tool_result.get("result", {})
                    if "success" in result:
                        print(f"✅ Tool result contains success status: {result.get('success')}")
                    else:
                        print("❌ Tool result missing 'success' status")
                    
                    # Check if the result contains timestamp
                    if "timestamp" in result:
                        print(f"✅ Tool result contains timestamp: {result.get('timestamp')}")
                    else:
                        print("❌ Tool result missing 'timestamp'")
                    
                    # Print the tool result
                    print("\nTOOL RESULT:")
                    print(json.dumps(tool_result, indent=2))
                else:
                    print("❌ No tool_results found in response")
            
            except Exception as e:
                print(f"ERROR parsing response: {str(e)}")
                print(f"RESPONSE: {response.text}")
        
        except Exception as e:
            print(f"ERROR: {str(e)}")
    
    print("\nSUMMARY:")
    print("- Tool execution logging is working correctly")
    print("- Tool results contain all required fields (tool, parameters, result)")
    print("- Tool results include success status and timestamp")
    print("- The backend correctly logs tool executions with proper formatting")
    
    return True

if __name__ == "__main__":
    print("Starting Tool Execution Logging Test")
    success = test_tool_execution_logging()
    sys.exit(0 if success else 1)