#!/usr/bin/env python3
"""
Test script to demonstrate autonomous web navigation functionality
"""

import sys
import os
sys.path.append('/app/backend/src')
sys.path.append('/app/backend')

from src.tools.autonomous_web_navigation import AutonomousWebNavigation
from src.tools.tool_manager import ToolManager
import json

def test_web_navigation():
    """Test autonomous web navigation functionality"""
    print("🌐 TESTING AUTONOMOUS WEB NAVIGATION")
    print("=" * 50)
    
    # Test 1: Direct tool usage
    print("\n1. TESTING DIRECT TOOL USAGE")
    print("-" * 30)
    
    tool = AutonomousWebNavigation()
    
    # Test Google navigation
    print("Testing Google navigation...")
    result = tool.execute({
        'task_description': 'Navegar a Google.com y tomar un screenshot',
        'target_url': 'https://google.com',
        'constraints': {
            'max_steps': 5,
            'timeout_per_step': 20,
            'screenshot_frequency': 'every_step'
        }
    })
    
    print(f"✅ Google navigation result: Success={result.get('success')}, Steps={result.get('completed_steps')}/{result.get('total_steps')}")
    
    # Test 2: Tool manager integration
    print("\n2. TESTING TOOL MANAGER INTEGRATION")
    print("-" * 40)
    
    try:
        tool_manager = ToolManager()
        
        # Test GitHub navigation
        print("Testing GitHub navigation through tool manager...")
        result = tool_manager.execute_tool(
            'autonomous_web_navigation',
            {
                'task_description': 'Navegar a GitHub.com y buscar el botón de registro',
                'target_url': 'https://github.com',
                'constraints': {
                    'max_steps': 8,
                    'timeout_per_step': 30,
                    'screenshot_frequency': 'every_step'
                }
            },
            task_id='test_github_nav'
        )
        
        print(f"✅ GitHub navigation result: Success={result.get('success')}, Steps={result.get('completed_steps')}/{result.get('total_steps')}")
        
        # Test Twitter navigation
        print("Testing Twitter navigation through tool manager...")
        result = tool_manager.execute_tool(
            'autonomous_web_navigation',
            {
                'task_description': 'Navegar a Twitter.com y explorar la página',
                'target_url': 'https://twitter.com',
                'constraints': {
                    'max_steps': 6,
                    'timeout_per_step': 25,
                    'screenshot_frequency': 'every_step'
                }
            },
            task_id='test_twitter_nav'
        )
        
        print(f"✅ Twitter navigation result: Success={result.get('success')}, Steps={result.get('completed_steps')}/{result.get('total_steps')}")
        
        # Test Stack Overflow navigation
        print("Testing Stack Overflow navigation through tool manager...")
        result = tool_manager.execute_tool(
            'autonomous_web_navigation',
            {
                'task_description': 'Navegar a Stack Overflow y buscar información sobre Python',
                'target_url': 'https://stackoverflow.com',
                'constraints': {
                    'max_steps': 7,
                    'timeout_per_step': 25,
                    'screenshot_frequency': 'every_step'
                }
            },
            task_id='test_stackoverflow_nav'
        )
        
        print(f"✅ Stack Overflow navigation result: Success={result.get('success')}, Steps={result.get('completed_steps')}/{result.get('total_steps')}")
        
    except Exception as e:
        print(f"❌ Error in tool manager test: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 AUTONOMOUS WEB NAVIGATION TEST COMPLETE")
    print("=" * 50)
    
    # Show tool capabilities
    print("\n3. TOOL CAPABILITIES")
    print("-" * 20)
    tool_info = tool.get_tool_info()
    print(f"Version: {tool_info['version']}")
    print(f"Category: {tool_info['category']}")
    print(f"Playwright Status: {tool_info['playwright_status']}")
    print("\nSupported Tasks:")
    for task in tool_info['supported_tasks']:
        print(f"  • {task}")
    
    print("\nCapabilities:")
    for cap in tool_info['capabilities']:
        print(f"  • {cap}")

if __name__ == "__main__":
    test_web_navigation()