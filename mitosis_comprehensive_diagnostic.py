#!/usr/bin/env python3
"""
MITOSIS COMPREHENSIVE BACKEND DIAGNOSTIC SCRIPT
===============================================

This script performs a comprehensive diagnostic of the Mitosis backend system
to identify exactly what's happening with the system. The user reports that the 
agent "says it completes tasks but doesn't deliver results".

DIAGNOSTIC AREAS:
1. General Backend State (health endpoints, MongoDB, Ollama connections)
2. Main Agent System (chat endpoint testing with real messages)
3. Memory System (advanced memory system initialization and integration)
4. Tools System (availability and functionality)
5. Problem Diagnosis (identify what's using fallback vs advanced implementation)

This diagnostic will determine if we need to:
A) Continue with planned UPGRADE.md v2.0 improvements
B) Fix fundamental problems first
C) Verify that the advanced system is actually active vs using fallbacks
"""

import requests
import json
import sys
import uuid
import os
import time
from datetime import datetime
from pathlib import Path

# Configuration - Use the external URL from frontend .env
try:
    with open('/app/frontend/.env', 'r') as env_file:
        for line in env_file:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.strip().split('=', 1)[1].strip('"\'')
                break
except Exception as e:
    print(f"Error reading .env file: {e}")
    backend_url = "http://localhost:8001"

BASE_URL = "http://localhost:8001"  # Use local URL since external URL has issues
print(f"🔍 MITOSIS COMPREHENSIVE DIAGNOSTIC")
print(f"🌐 Using backend URL: {BASE_URL}")
print(f"📅 Diagnostic started at: {datetime.now().isoformat()}")
print("="*80)

# Test results storage
diagnostic_results = {
    "timestamp": datetime.now().isoformat(),
    "backend_url": BASE_URL,
    "sections": {},
    "summary": {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "critical_issues": [],
        "recommendations": []
    }
}

def log_test(section, test_name, passed, details=None, critical=False):
    """Log a test result"""
    if section not in diagnostic_results["sections"]:
        diagnostic_results["sections"][section] = {
            "tests": [],
            "passed": 0,
            "failed": 0
        }
    
    diagnostic_results["sections"][section]["tests"].append({
        "name": test_name,
        "passed": passed,
        "details": details,
        "critical": critical,
        "timestamp": datetime.now().isoformat()
    })
    
    diagnostic_results["summary"]["total_tests"] += 1
    
    if passed:
        diagnostic_results["sections"][section]["passed"] += 1
        diagnostic_results["summary"]["passed_tests"] += 1
        status = "✅ PASSED"
    else:
        diagnostic_results["sections"][section]["failed"] += 1
        diagnostic_results["summary"]["failed_tests"] += 1
        status = "❌ FAILED"
        
        if critical:
            diagnostic_results["summary"]["critical_issues"].append({
                "section": section,
                "test": test_name,
                "details": details
            })
    
    print(f"   {status}: {test_name}")
    if details:
        print(f"      Details: {details}")

def make_request(endpoint, method="GET", data=None, timeout=30):
    """Make a request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response.status_code, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    except requests.exceptions.RequestException as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)

# =============================================================================
# SECTION 1: GENERAL BACKEND STATE
# =============================================================================
def test_general_backend_state():
    """Test general backend health and service connections"""
    print("\n🏥 SECTION 1: GENERAL BACKEND STATE")
    print("-" * 50)
    
    # Test 1.1: Main health endpoint
    print("🔍 Testing main health endpoint...")
    status, response = make_request("/api/health")
    
    if status == 200 and isinstance(response, dict):
        services = response.get('services', {})
        ollama_healthy = services.get('ollama', False)
        tools_count = services.get('tools', 0)
        database_connected = services.get('database', False)
        
        log_test("general_backend", "Main Health Endpoint", True, 
                f"Ollama: {ollama_healthy}, Tools: {tools_count}, Database: {database_connected}")
        
        # Sub-tests for each service
        log_test("general_backend", "Ollama Connection", ollama_healthy, 
                f"Ollama service healthy: {ollama_healthy}", critical=not ollama_healthy)
        
        log_test("general_backend", "Database Connection", database_connected, 
                f"MongoDB connected: {database_connected}", critical=not database_connected)
        
        log_test("general_backend", "Tools Availability", tools_count > 0, 
                f"Tools available: {tools_count}", critical=tools_count == 0)
    else:
        log_test("general_backend", "Main Health Endpoint", False, 
                f"Status: {status}, Response: {response}", critical=True)
    
    # Test 1.2: Agent health endpoint
    print("🔍 Testing agent health endpoint...")
    status, response = make_request("/api/agent/health")
    
    if status == 200 and isinstance(response, dict):
        log_test("general_backend", "Agent Health Endpoint", True, 
                f"Agent health endpoint responding correctly")
        
        # Check for detailed agent status
        if 'ollama' in response:
            ollama_info = response['ollama']
            endpoint = ollama_info.get('endpoint', 'Unknown')
            model = ollama_info.get('model', 'Unknown')
            log_test("general_backend", "Ollama Configuration", True, 
                    f"Endpoint: {endpoint}, Model: {model}")
    else:
        log_test("general_backend", "Agent Health Endpoint", False, 
                f"Status: {status}, Response: {response}", critical=True)
    
    # Test 1.3: Agent status endpoint
    print("🔍 Testing agent status endpoint...")
    status, response = make_request("/api/agent/status")
    
    if status == 200:
        log_test("general_backend", "Agent Status Endpoint", True, 
                f"Agent status endpoint responding")
    else:
        log_test("general_backend", "Agent Status Endpoint", False, 
                f"Status: {status}, Response: {response}")

# =============================================================================
# SECTION 2: MAIN AGENT SYSTEM
# =============================================================================
def test_main_agent_system():
    """Test the main agent system with real messages"""
    print("\n🤖 SECTION 2: MAIN AGENT SYSTEM")
    print("-" * 50)
    
    # Test 2.1: Basic chat functionality
    print("🔍 Testing basic chat functionality...")
    
    test_messages = [
        {
            "name": "Simple Greeting",
            "message": "Hola, ¿cómo estás?",
            "expected_fields": ["response", "task_id", "memory_used", "status"]
        },
        {
            "name": "Task Request",
            "message": "Ayúdame a crear un plan para desarrollar una aplicación web",
            "expected_fields": ["response", "task_id", "memory_used", "status"]
        },
        {
            "name": "Information Request",
            "message": "¿Qué herramientas tienes disponibles?",
            "expected_fields": ["response", "task_id", "memory_used", "status"]
        }
    ]
    
    for test_msg in test_messages:
        print(f"   Testing: {test_msg['name']}")
        
        data = {
            "message": test_msg["message"],
            "context": {
                "task_id": f"diagnostic-{uuid.uuid4()}",
                "previous_messages": []
            }
        }
        
        status, response = make_request("/api/agent/chat", "POST", data, timeout=45)
        
        if status == 200 and isinstance(response, dict):
            # Check for expected fields
            missing_fields = []
            for field in test_msg["expected_fields"]:
                if field not in response:
                    missing_fields.append(field)
            
            if not missing_fields:
                # Check response quality
                response_text = response.get("response", "")
                memory_used = response.get("memory_used", False)
                task_id = response.get("task_id", "")
                status_field = response.get("status", "")
                
                # Analyze response quality
                is_substantial = len(response_text) > 50  # More than just basic confirmation
                has_memory = memory_used is True
                has_task_id = bool(task_id)
                has_status = bool(status_field)
                
                quality_score = sum([is_substantial, has_memory, has_task_id, has_status])
                
                log_test("main_agent", f"Chat - {test_msg['name']}", quality_score >= 3, 
                        f"Response length: {len(response_text)}, Memory: {memory_used}, Task ID: {bool(task_id)}, Status: {status_field}")
                
                # Specific test for memory integration
                log_test("main_agent", f"Memory Integration - {test_msg['name']}", has_memory, 
                        f"Memory used flag: {memory_used}", critical=not has_memory)
                
            else:
                log_test("main_agent", f"Chat - {test_msg['name']}", False, 
                        f"Missing fields: {missing_fields}", critical=True)
        else:
            log_test("main_agent", f"Chat - {test_msg['name']}", False, 
                    f"Status: {status}, Response: {response}", critical=True)
        
        time.sleep(1)  # Brief pause between requests

# =============================================================================
# SECTION 3: MEMORY SYSTEM
# =============================================================================
def test_memory_system():
    """Test the advanced memory system"""
    print("\n🧠 SECTION 3: MEMORY SYSTEM")
    print("-" * 50)
    
    # Test 3.1: Memory system initialization
    print("🔍 Testing memory system initialization...")
    status, response = make_request("/api/memory/analytics")
    
    if status == 200 and isinstance(response, dict):
        # Check for memory components
        components = response.get("components", {})
        if components:
            component_names = list(components.keys())
            expected_components = ["working_memory", "episodic_memory", "semantic_memory", 
                                 "procedural_memory", "embedding_service", "semantic_indexer"]
            
            found_components = [comp for comp in expected_components if comp in component_names]
            
            log_test("memory_system", "Memory Components Initialization", 
                    len(found_components) >= 4, 
                    f"Found components: {found_components}")
        else:
            log_test("memory_system", "Memory Components Initialization", False, 
                    "No memory components found", critical=True)
    else:
        log_test("memory_system", "Memory Analytics Endpoint", False, 
                f"Status: {status}, Response: {response}")
    
    # Test 3.2: Memory operations
    print("🔍 Testing memory operations...")
    
    # Test episode storage
    episode_data = {
        "content": "Test episode for diagnostic",
        "context": {"type": "diagnostic", "timestamp": datetime.now().isoformat()},
        "importance": 0.7
    }
    
    status, response = make_request("/api/memory/episodes", "POST", episode_data)
    
    if status == 200 and isinstance(response, dict):
        episode_id = response.get("episode_id")
        log_test("memory_system", "Episode Storage", bool(episode_id), 
                f"Episode ID: {episode_id}")
    else:
        log_test("memory_system", "Episode Storage", False, 
                f"Status: {status}, Response: {response}")
    
    # Test 3.3: Memory integration with chat
    print("🔍 Testing memory integration with chat...")
    
    # Send a message that should use memory
    data = {
        "message": "Recuerda que estamos haciendo un diagnóstico del sistema",
        "context": {
            "task_id": f"memory-test-{uuid.uuid4()}",
            "previous_messages": []
        }
    }
    
    status, response = make_request("/api/agent/chat", "POST", data, timeout=30)
    
    if status == 200 and isinstance(response, dict):
        memory_used = response.get("memory_used", False)
        log_test("memory_system", "Memory Integration with Chat", memory_used, 
                f"Memory used in chat: {memory_used}", critical=not memory_used)
    else:
        log_test("memory_system", "Memory Integration with Chat", False, 
                f"Status: {status}, Response: {response}")

# =============================================================================
# SECTION 4: TOOLS SYSTEM
# =============================================================================
def test_tools_system():
    """Test the tools system availability and functionality"""
    print("\n🔧 SECTION 4: TOOLS SYSTEM")
    print("-" * 50)
    
    # Test 4.1: Tools availability
    print("🔍 Testing tools availability...")
    status, response = make_request("/api/agent/tools")
    
    if status == 200 and isinstance(response, dict):
        tools = response.get("tools", [])
        tool_names = [tool.get("name") for tool in tools]
        
        log_test("tools_system", "Tools Endpoint", True, 
                f"Found {len(tools)} tools: {tool_names}")
        
        # Check for critical tools
        critical_tools = ["web_search", "deep_research", "comprehensive_research"]
        found_critical = [tool for tool in critical_tools if tool in tool_names]
        
        log_test("tools_system", "Critical Tools Available", 
                len(found_critical) >= 2, 
                f"Critical tools found: {found_critical}")
        
    else:
        log_test("tools_system", "Tools Endpoint", False, 
                f"Status: {status}, Response: {response}", critical=True)
    
    # Test 4.2: Web search functionality
    print("🔍 Testing web search functionality...")
    
    search_data = {
        "message": "[WebSearch] inteligencia artificial 2025",
        "search_mode": "websearch"
    }
    
    status, response = make_request("/api/agent/chat", "POST", search_data, timeout=45)
    
    if status == 200 and isinstance(response, dict):
        search_mode = response.get("search_mode")
        search_data_field = response.get("search_data", {})
        
        web_search_working = (search_mode == "websearch" and 
                             search_data_field and 
                             "sources" in search_data_field)
        
        log_test("tools_system", "Web Search Functionality", web_search_working, 
                f"Search mode: {search_mode}, Has search data: {bool(search_data_field)}")
    else:
        log_test("tools_system", "Web Search Functionality", False, 
                f"Status: {status}, Response: {response}")
    
    # Test 4.3: Deep research functionality
    print("🔍 Testing deep research functionality...")
    
    deep_search_data = {
        "message": "[DeepSearch] machine learning applications",
        "search_mode": "deepsearch"
    }
    
    status, response = make_request("/api/agent/chat", "POST", deep_search_data, timeout=60)
    
    if status == 200 and isinstance(response, dict):
        search_mode = response.get("search_mode")
        created_files = response.get("created_files", [])
        
        deep_search_working = (search_mode == "deepsearch" and 
                              len(created_files) > 0)
        
        log_test("tools_system", "Deep Research Functionality", deep_search_working, 
                f"Search mode: {search_mode}, Created files: {len(created_files)}")
    else:
        log_test("tools_system", "Deep Research Functionality", False, 
                f"Status: {status}, Response: {response}")

# =============================================================================
# SECTION 5: PROBLEM DIAGNOSIS
# =============================================================================
def test_problem_diagnosis():
    """Diagnose specific problems and identify fallback usage"""
    print("\n🔍 SECTION 5: PROBLEM DIAGNOSIS")
    print("-" * 50)
    
    # Test 5.1: Check if using server_simple.py vs full system
    print("🔍 Checking which server implementation is active...")
    
    # Look for indicators of which server is running
    status, response = make_request("/api/agent/status")
    
    if status == 200 and isinstance(response, dict):
        # Check for advanced features that would indicate full system
        has_websocket = "websocket" in str(response).lower()
        has_task_manager = "task_manager" in str(response).lower()
        has_advanced_memory = "advanced_memory" in str(response).lower()
        
        advanced_features_count = sum([has_websocket, has_task_manager, has_advanced_memory])
        
        log_test("problem_diagnosis", "Advanced System Active", 
                advanced_features_count >= 1, 
                f"Advanced features detected: WebSocket={has_websocket}, TaskManager={has_task_manager}, AdvancedMemory={has_advanced_memory}")
    else:
        log_test("problem_diagnosis", "Server Implementation Check", False, 
                f"Could not determine server implementation")
    
    # Test 5.2: Check response quality vs claims
    print("🔍 Testing response quality vs completion claims...")
    
    task_request = {
        "message": "Crea un documento con información sobre Python para principiantes",
        "context": {
            "task_id": f"quality-test-{uuid.uuid4()}",
            "previous_messages": []
        }
    }
    
    status, response = make_request("/api/agent/chat", "POST", task_request, timeout=45)
    
    if status == 200 and isinstance(response, dict):
        response_text = response.get("response", "")
        created_files = response.get("created_files", [])
        tool_results = response.get("tool_results", [])
        status_field = response.get("status", "")
        
        # Analyze if the response claims completion but doesn't deliver
        claims_completion = any(word in response_text.lower() for word in 
                              ["completado", "terminado", "finalizado", "listo", "creado"])
        
        actually_delivered = len(created_files) > 0 or len(tool_results) > 0
        
        response_quality_issue = claims_completion and not actually_delivered
        
        log_test("problem_diagnosis", "Response Quality vs Claims", 
                not response_quality_issue, 
                f"Claims completion: {claims_completion}, Actually delivered: {actually_delivered}, Files created: {len(created_files)}")
        
        if response_quality_issue:
            diagnostic_results["summary"]["critical_issues"].append({
                "section": "problem_diagnosis",
                "test": "Response Quality Issue",
                "details": "Agent claims task completion but doesn't deliver actual results"
            })
    
    # Test 5.3: Check for fallback patterns
    print("🔍 Checking for fallback patterns...")
    
    # Test multiple requests to see consistency
    consistency_results = []
    
    for i in range(3):
        test_data = {
            "message": f"Test message {i+1} for consistency check",
            "context": {
                "task_id": f"consistency-{i+1}-{uuid.uuid4()}",
                "previous_messages": []
            }
        }
        
        status, response = make_request("/api/agent/chat", "POST", test_data, timeout=30)
        
        if status == 200 and isinstance(response, dict):
            consistency_results.append({
                "memory_used": response.get("memory_used", False),
                "has_task_id": bool(response.get("task_id")),
                "response_length": len(response.get("response", "")),
                "status": response.get("status", "")
            })
        
        time.sleep(1)
    
    if consistency_results:
        memory_consistency = all(r["memory_used"] for r in consistency_results)
        task_id_consistency = all(r["has_task_id"] for r in consistency_results)
        
        log_test("problem_diagnosis", "System Consistency", 
                memory_consistency and task_id_consistency, 
                f"Memory consistent: {memory_consistency}, Task ID consistent: {task_id_consistency}")

# =============================================================================
# MAIN DIAGNOSTIC EXECUTION
# =============================================================================
def run_comprehensive_diagnostic():
    """Run the complete diagnostic"""
    
    print("🚀 Starting comprehensive Mitosis backend diagnostic...")
    
    try:
        test_general_backend_state()
        test_main_agent_system()
        test_memory_system()
        test_tools_system()
        test_problem_diagnosis()
        
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
        diagnostic_results["summary"]["critical_issues"].append({
            "section": "diagnostic_execution",
            "test": "Diagnostic Execution",
            "details": f"Error during diagnostic: {e}"
        })
    
    # Generate final report
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE DIAGNOSTIC REPORT")
    print("="*80)
    
    total = diagnostic_results["summary"]["total_tests"]
    passed = diagnostic_results["summary"]["passed_tests"]
    failed = diagnostic_results["summary"]["failed_tests"]
    
    print(f"📈 OVERALL RESULTS:")
    print(f"   Total Tests: {total}")
    print(f"   Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"   Failed: {failed} ({failed/total*100:.1f}%)")
    
    print(f"\n📋 SECTION BREAKDOWN:")
    for section_name, section_data in diagnostic_results["sections"].items():
        section_total = section_data["passed"] + section_data["failed"]
        section_passed = section_data["passed"]
        print(f"   {section_name}: {section_passed}/{section_total} ({section_passed/section_total*100:.1f}%)")
    
    # Critical issues
    critical_issues = diagnostic_results["summary"]["critical_issues"]
    if critical_issues:
        print(f"\n🚨 CRITICAL ISSUES FOUND ({len(critical_issues)}):")
        for issue in critical_issues:
            print(f"   ❌ {issue['section']}: {issue['test']}")
            print(f"      {issue['details']}")
    else:
        print(f"\n✅ NO CRITICAL ISSUES FOUND")
    
    # Recommendations
    print(f"\n💡 DIAGNOSTIC RECOMMENDATIONS:")
    
    if failed == 0:
        print("   ✅ System appears to be functioning correctly")
        print("   ✅ Ready to continue with UPGRADE.md v2.0 improvements")
    elif len(critical_issues) > 0:
        print("   🔧 Fix critical issues before proceeding with upgrades")
        print("   🔍 Focus on fundamental system problems first")
    else:
        print("   ⚠️  Minor issues detected but system is generally functional")
        print("   📈 Can proceed with improvements while monitoring issues")
    
    # Specific recommendations based on results
    memory_section = diagnostic_results["sections"].get("memory_system", {})
    if memory_section.get("failed", 0) > 0:
        print("   🧠 Memory system needs attention - check advanced memory manager initialization")
    
    tools_section = diagnostic_results["sections"].get("tools_system", {})
    if tools_section.get("failed", 0) > 0:
        print("   🔧 Tools system needs attention - verify tool availability and functionality")
    
    agent_section = diagnostic_results["sections"].get("main_agent", {})
    if agent_section.get("failed", 0) > 0:
        print("   🤖 Main agent system needs attention - check response quality and integration")
    
    print(f"\n📅 Diagnostic completed at: {datetime.now().isoformat()}")
    print("="*80)
    
    # Save detailed results to file
    try:
        with open('/app/mitosis_diagnostic_results.json', 'w') as f:
            json.dump(diagnostic_results, f, indent=2)
        print(f"📄 Detailed results saved to: /app/mitosis_diagnostic_results.json")
    except Exception as e:
        print(f"⚠️  Could not save detailed results: {e}")

if __name__ == "__main__":
    run_comprehensive_diagnostic()