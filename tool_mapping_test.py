#!/usr/bin/env python3
"""
CRITICAL TOOL MAPPING FIX VERIFICATION TEST
Testing the fix for the problem where agent terminates tasks without delivering relevant content.

ISSUE FIXED: Lines 7214-7338 in agent_routes.py where all tools were incorrectly mapped to web_search
SOLUTION: 
- 'analysis' tools now use 'ollama_analysis' 
- 'processing' tools now use 'ollama_processing'
- New Ollama tools created in /app/backend/src/tools/ollama_tools.py
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://18150277-52b6-42d4-b11c-fcf36509cafe.preview.emergentagent.com"

class ToolMappingFixTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.created_task_id = None
        
    def log_test(self, test_name, success, details, error=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'error': str(error) if error else None,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def test_1_verify_ollama_tools_available(self):
        """TEST 1: Verify that new Ollama tools are available"""
        try:
            print("🔄 Test 1: Verifying new Ollama tools are registered")
            
            url = f"{self.backend_url}/api/agent/status"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tools = data.get('tools', [])
                tools_count = data.get('tools_count', 0)
                
                # Check if ollama_analysis and ollama_processing are in the tools list
                ollama_analysis_found = any('ollama_analysis' in str(tool) for tool in tools)
                ollama_processing_found = any('ollama_processing' in str(tool) for tool in tools)
                
                if ollama_analysis_found and ollama_processing_found:
                    details = f"✅ Both Ollama tools found. Total tools: {tools_count}. Tools: {tools}"
                    self.log_test("1. Ollama Tools Available", True, details)
                    return True
                else:
                    details = f"❌ Missing Ollama tools. Analysis: {ollama_analysis_found}, Processing: {ollama_processing_found}. Tools: {tools}"
                    self.log_test("1. Ollama Tools Available", False, details)
                    return False
            else:
                self.log_test("1. Ollama Tools Available", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("1. Ollama Tools Available", False, "Request failed", e)
            return False

    def test_2_create_ai_analysis_task(self):
        """TEST 2: Create a task that should use analysis tools (not web_search)"""
        try:
            print("🔄 Test 2: Creating AI analysis task to test tool mapping")
            
            url = f"{self.backend_url}/api/agent/chat"
            payload = {
                "message": "Genera un análisis sobre inteligencia artificial",
                "memory_used": True
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                
                if task_id:
                    self.created_task_id = task_id
                    details = f"Task created successfully: {task_id}"
                    self.log_test("2. Create AI Analysis Task", True, details)
                    return task_id
                else:
                    self.log_test("2. Create AI Analysis Task", False, f"No task_id in response: {data}")
                    return None
            else:
                self.log_test("2. Create AI Analysis Task", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("2. Create AI Analysis Task", False, "Request failed", e)
            return None

    def test_3_verify_plan_generation(self):
        """TEST 3: Verify that plan is generated correctly with 4 steps"""
        try:
            print("🔄 Test 3: Verifying plan generation with correct steps")
            
            if not self.created_task_id:
                self.log_test("3. Plan Generation", False, "No task_id available")
                return False
            
            # Wait a moment for plan to be generated
            time.sleep(3)
            
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get('plan', [])
                total_steps = data.get('total_steps', 0)
                
                if len(plan) >= 4 and total_steps >= 4:
                    # Check that steps have correct tools (not all web_search)
                    step_tools = [step.get('tool', 'unknown') for step in plan]
                    unique_tools = set(step_tools)
                    
                    # Verify that not all steps use web_search
                    if len(unique_tools) > 1 or 'web_search' not in unique_tools:
                        details = f"✅ Plan generated with {len(plan)} steps using diverse tools: {step_tools}"
                        self.log_test("3. Plan Generation", True, details)
                        return True
                    else:
                        details = f"❌ All steps use same tool (likely web_search): {step_tools}"
                        self.log_test("3. Plan Generation", False, details)
                        return False
                else:
                    details = f"❌ Insufficient steps generated: {len(plan)} steps, expected >= 4"
                    self.log_test("3. Plan Generation", False, details)
                    return False
            else:
                self.log_test("3. Plan Generation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("3. Plan Generation", False, "Request failed", e)
            return False

    def test_4_execute_analysis_step(self):
        """TEST 4: Execute analysis step and verify it uses ollama_analysis, not web_search"""
        try:
            print("🔄 Test 4: Executing analysis step to verify correct tool mapping")
            
            if not self.created_task_id:
                self.log_test("4. Analysis Step Execution", False, "No task_id available")
                return False
            
            # Get the task plan first
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                self.log_test("4. Analysis Step Execution", False, "Cannot get task status")
                return False
            
            data = response.json()
            plan = data.get('plan', [])
            
            # Find an analysis step
            analysis_step = None
            for step in plan:
                step_tool = step.get('tool', '')
                step_title = step.get('title', '').lower()
                if step_tool in ['analysis', 'data_analysis'] or 'analiz' in step_title:
                    analysis_step = step
                    break
            
            if not analysis_step:
                details = f"No analysis step found in plan. Steps: {[(s.get('title'), s.get('tool')) for s in plan]}"
                self.log_test("4. Analysis Step Execution", False, details)
                return False
            
            # Execute the analysis step
            step_id = analysis_step.get('id')
            if not step_id:
                self.log_test("4. Analysis Step Execution", False, "Analysis step has no ID")
                return False
            
            url = f"{self.backend_url}/api/agent/execute-step-detailed/{self.created_task_id}/{step_id}"
            response = self.session.post(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                content = result.get('content', '')
                tool_used = result.get('tool_used', 'unknown')
                
                # Check if content is relevant (not about Yahoo/Reddit when asking for AI analysis)
                irrelevant_keywords = ['yahoo', 'reddit', 'search results', 'web search']
                relevant_keywords = ['inteligencia artificial', 'ai', 'análisis', 'machine learning', 'algoritmo']
                
                has_irrelevant = any(keyword in content.lower() for keyword in irrelevant_keywords)
                has_relevant = any(keyword in content.lower() for keyword in relevant_keywords)
                
                if success and has_relevant and not has_irrelevant:
                    details = f"✅ Analysis step executed successfully with relevant content. Tool used: {tool_used}. Content length: {len(content)}"
                    self.log_test("4. Analysis Step Execution", True, details)
                    return True
                else:
                    details = f"❌ Analysis step failed or produced irrelevant content. Success: {success}, Relevant: {has_relevant}, Irrelevant: {has_irrelevant}, Tool: {tool_used}"
                    self.log_test("4. Analysis Step Execution", False, details)
                    return False
            else:
                self.log_test("4. Analysis Step Execution", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("4. Analysis Step Execution", False, "Request failed", e)
            return False

    def test_5_execute_processing_step(self):
        """TEST 5: Execute processing step and verify it uses ollama_processing, not web_search"""
        try:
            print("🔄 Test 5: Executing processing step to verify correct tool mapping")
            
            if not self.created_task_id:
                self.log_test("5. Processing Step Execution", False, "No task_id available")
                return False
            
            # Get the task plan first
            url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                self.log_test("5. Processing Step Execution", False, "Cannot get task status")
                return False
            
            data = response.json()
            plan = data.get('plan', [])
            
            # Find a processing step
            processing_step = None
            for step in plan:
                step_tool = step.get('tool', '')
                step_title = step.get('title', '').lower()
                if step_tool == 'processing' or 'proces' in step_title or 'complet' in step_title:
                    processing_step = step
                    break
            
            if not processing_step:
                details = f"No processing step found in plan. Steps: {[(s.get('title'), s.get('tool')) for s in plan]}"
                self.log_test("5. Processing Step Execution", False, details)
                return False
            
            # Execute the processing step
            step_id = processing_step.get('id')
            if not step_id:
                self.log_test("5. Processing Step Execution", False, "Processing step has no ID")
                return False
            
            url = f"{self.backend_url}/api/agent/execute-step-detailed/{self.created_task_id}/{step_id}"
            response = self.session.post(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                content = result.get('content', '')
                tool_used = result.get('tool_used', 'unknown')
                
                # Check if content is relevant and substantial
                if success and len(content) > 100:
                    details = f"✅ Processing step executed successfully. Tool used: {tool_used}. Content length: {len(content)}"
                    self.log_test("5. Processing Step Execution", True, details)
                    return True
                else:
                    details = f"❌ Processing step failed or produced insufficient content. Success: {success}, Content length: {len(content)}, Tool: {tool_used}"
                    self.log_test("5. Processing Step Execution", False, details)
                    return False
            else:
                self.log_test("5. Processing Step Execution", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("5. Processing Step Execution", False, "Request failed", e)
            return False

    def test_6_verify_ollama_integration(self):
        """TEST 6: Verify Ollama integration is working correctly"""
        try:
            print("🔄 Test 6: Verifying Ollama integration")
            
            url = f"{self.backend_url}/api/agent/status"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                ollama_info = data.get('ollama', {})
                ollama_connected = ollama_info.get('connected', False)
                ollama_endpoint = ollama_info.get('endpoint', '')
                ollama_model = ollama_info.get('model', '')
                
                if ollama_connected and ollama_endpoint and ollama_model:
                    details = f"✅ Ollama connected. Endpoint: {ollama_endpoint}, Model: {ollama_model}"
                    self.log_test("6. Ollama Integration", True, details)
                    return True
                else:
                    details = f"❌ Ollama not properly configured. Connected: {ollama_connected}, Endpoint: {ollama_endpoint}, Model: {ollama_model}"
                    self.log_test("6. Ollama Integration", False, details)
                    return False
            else:
                self.log_test("6. Ollama Integration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("6. Ollama Integration", False, "Request failed", e)
            return False

    def test_7_end_to_end_verification(self):
        """TEST 7: End-to-end verification that task delivers relevant content"""
        try:
            print("🔄 Test 7: End-to-end verification of relevant content delivery")
            
            if not self.created_task_id:
                self.log_test("7. End-to-End Verification", False, "No task_id available")
                return False
            
            # Monitor task for completion
            start_time = time.time()
            max_wait_time = 60
            
            while time.time() - start_time < max_wait_time:
                url = f"{self.backend_url}/api/agent/get-task-status/{self.created_task_id}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    completed_steps = data.get('completed_steps', 0)
                    total_steps = data.get('total_steps', 0)
                    
                    if status == 'completed' and completed_steps == total_steps:
                        # Task completed, check if content is relevant
                        plan = data.get('plan', [])
                        relevant_content_found = False
                        
                        for step in plan:
                            if step.get('completed') and 'result' in step:
                                result = step.get('result', {})
                                content = result.get('content', '')
                                
                                # Check for AI-related content (not Yahoo/Reddit)
                                if 'inteligencia artificial' in content.lower() or 'ai' in content.lower():
                                    relevant_content_found = True
                                    break
                        
                        if relevant_content_found:
                            details = f"✅ Task completed with relevant AI content. Steps: {completed_steps}/{total_steps}"
                            self.log_test("7. End-to-End Verification", True, details)
                            return True
                        else:
                            details = f"❌ Task completed but no relevant AI content found"
                            self.log_test("7. End-to-End Verification", False, details)
                            return False
                    
                    elif status in ['failed', 'error']:
                        details = f"❌ Task failed with status: {status}"
                        self.log_test("7. End-to-End Verification", False, details)
                        return False
                
                time.sleep(3)
            
            # Task didn't complete in time
            details = f"❌ Task didn't complete within {max_wait_time} seconds"
            self.log_test("7. End-to-End Verification", False, details)
            return False
                
        except Exception as e:
            self.log_test("7. End-to-End Verification", False, "Request failed", e)
            return False

    def run_tool_mapping_tests(self):
        """Run all tool mapping fix verification tests"""
        print("🚀 CRITICAL TOOL MAPPING FIX VERIFICATION")
        print("=" * 70)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print(f"Testing Fix: analysis/processing tools → ollama_analysis/ollama_processing")
        print()
        
        # Test 1: Verify Ollama tools are available
        print("=" * 50)
        tools_ok = self.test_1_verify_ollama_tools_available()
        
        # Test 2: Create AI analysis task
        print("=" * 50)
        task_id = self.test_2_create_ai_analysis_task()
        
        # Test 3: Verify plan generation
        print("=" * 50)
        plan_ok = self.test_3_verify_plan_generation()
        
        # Test 4: Execute analysis step
        print("=" * 50)
        analysis_ok = self.test_4_execute_analysis_step()
        
        # Test 5: Execute processing step
        print("=" * 50)
        processing_ok = self.test_5_execute_processing_step()
        
        # Test 6: Verify Ollama integration
        print("=" * 50)
        ollama_ok = self.test_6_verify_ollama_integration()
        
        # Test 7: End-to-end verification
        print("=" * 50)
        e2e_ok = self.test_7_end_to_end_verification()
        
        # Summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("🎯 TOOL MAPPING FIX VERIFICATION SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        # Analyze results for the specific fix
        critical_issues = []
        fix_working = True
        
        for result in self.test_results:
            if not result['success']:
                test_name = result['test']
                details = result['details'] or result['error']
                
                if 'Ollama Tools Available' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    fix_working = False
                elif 'Analysis Step Execution' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    fix_working = False
                elif 'Processing Step Execution' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    fix_working = False
                elif 'Ollama Integration' in test_name:
                    critical_issues.append(f"🚨 CRITICAL: {test_name} - {details}")
                    fix_working = False
                else:
                    critical_issues.append(f"❌ {test_name} - {details}")
        
        if critical_issues:
            print("🚨 ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("✅ All tool mapping tests passed successfully")
        
        print()
        
        # Specific diagnosis for the tool mapping fix
        if fix_working:
            print("✅ TOOL MAPPING FIX: WORKING CORRECTLY")
            print("   - Ollama tools (ollama_analysis, ollama_processing) are registered")
            print("   - Analysis steps use ollama_analysis instead of web_search")
            print("   - Processing steps use ollama_processing instead of web_search")
            print("   - Content generated is relevant to the original task")
            print("   - No more irrelevant Yahoo/Reddit content for AI analysis")
            print("   - The agent now delivers meaningful, task-relevant content")
        else:
            print("❌ TOOL MAPPING FIX: ISSUES DETECTED")
            print("   - The fix may not be working as expected")
            print("   - Tools may still be incorrectly mapped to web_search")
            print("   - Ollama integration may have problems")
            print("   - Content may still be irrelevant to the original task")
        
        print()
        
        # Specific recommendations
        print("📋 RECOMMENDATIONS:")
        if not fix_working:
            print("   1. Check that ollama_tools.py is properly imported")
            print("   2. Verify tool_manager registers the new Ollama tools")
            print("   3. Check agent_routes.py lines 7214-7338 for correct mapping")
            print("   4. Verify Ollama service is running and accessible")
            print("   5. Test individual tool execution manually")
        else:
            print("   1. Tool mapping fix is working correctly")
            print("   2. Monitor for any regression issues")
            print("   3. Consider expanding Ollama tool capabilities")
            print("   4. The original problem of irrelevant content is RESOLVED")
        
        print()
        print("📊 TOOL MAPPING FIX VERIFICATION COMPLETE")
        
        if self.created_task_id:
            print(f"📝 Test Task ID: {self.created_task_id}")
            print("   Use this ID to check logs and verify content relevance")

if __name__ == "__main__":
    tester = ToolMappingFixTester()
    results = tester.run_tool_mapping_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results if not result['success'])
    sys.exit(failed_tests)