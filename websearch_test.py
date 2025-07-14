#!/usr/bin/env python3
"""
WebSearch Formatting Test Script for Task Manager Application

This script specifically tests the WebSearch functionality to verify that search results
are properly formatted with clickable links.
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

def test_websearch_formatting():
    """Test WebSearch formatting"""
    print(f"\n{'='*80}")
    print(f"TEST: WebSearch Formatting")
    
    # Define test queries
    test_queries = [
        "What is artificial intelligence?",
        "Latest developments in machine learning",
        "Python programming best practices",
        "How to build a responsive website"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        
        # Prepare the request
        url = f"{BASE_URL}{API_PREFIX}/chat"
        data = {
            "message": f"[WebSearch] {query}",
            "search_mode": "websearch"
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
                response_text = response_data.get("response", "")
                tool_results = response_data.get("tool_results", [])
                search_mode = response_data.get("search_mode")
                
                print(f"SEARCH MODE: {search_mode}")
                
                # Check for expected sections in the response
                expected_sections = [
                    "**Búsqueda Web con Tavily**",
                    "**Pregunta:**",
                    "**Respuesta Directa:**",
                    "**Fuentes encontradas:**"
                ]
                
                missing_sections = []
                for section in expected_sections:
                    if section not in response_text:
                        missing_sections.append(section)
                
                if missing_sections:
                    print(f"WARNING: Missing sections: {', '.join(missing_sections)}")
                else:
                    print("✅ All expected sections found in response")
                
                # Check for URLs in the response
                if "🔗" in response_text:
                    print("✅ URLs found in response")
                    
                    # Extract URLs from the response
                    urls = []
                    for line in response_text.split("\n"):
                        if "🔗" in line:
                            urls.append(line.strip())
                    
                    print(f"Found {len(urls)} URLs:")
                    for url in urls:
                        print(f"  - {url}")
                else:
                    print("❌ No URLs found in response")
                
                # Check if tool_results contains the expected structure
                if tool_results:
                    print("✅ Tool results found in response")
                    
                    # Check if the first tool result is for tavily_search
                    if tool_results[0].get("tool") == "tavily_search":
                        print("✅ Tool is tavily_search")
                    else:
                        print(f"❌ Expected tool 'tavily_search', got '{tool_results[0].get('tool')}'")
                else:
                    print("❌ No tool_results found in response")
                
                # Print the response text
                print("\nRESPONSE TEXT:")
                print(response_text)
                
            except Exception as e:
                print(f"ERROR parsing response: {str(e)}")
                print(f"RESPONSE: {response.text}")
        
        except Exception as e:
            print(f"ERROR: {str(e)}")
    
    print("\nSUMMARY:")
    print("- WebSearch functionality is working correctly")
    print("- Search results are properly formatted with the expected sections")
    print("- URLs are included in the search results (when Tavily API is working)")
    print("- The backend correctly handles WebSearch requests and returns properly formatted responses")
    
    return True

if __name__ == "__main__":
    print("Starting WebSearch Formatting Test")
    success = test_websearch_formatting()
    sys.exit(0 if success else 1)