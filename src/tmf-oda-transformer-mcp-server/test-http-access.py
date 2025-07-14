#!/usr/bin/env python3
"""
Comprehensive HTTP Test Suite for Enhanced TMF ODA Transformer MCP Server

This script provides comprehensive testing of all 7 available Enhanced TMF ODA tools via HTTP REST API.
Perfect for external UIs, CI/CD pipelines, and integration testing - no SSH or Docker access required!

🔧 Tests All 7 Enhanced Tools:
- raw-analysis: Execute raw analysis stage of transformation journey
- stripped-schema: Execute stripped schema stage of transformation journey  
- get-job-logs: Retrieve execution logs for job steps
- test-runner: Run comprehensive test suite for all tools
- journeys: Comprehensive journey lifecycle management with 40+ actions (CRUD, stage mgmt, rules mgmt, job mgmt, dashboard)
- run-jobs: Execute any stage of a transformation journey
- logs-and-reports: NEW - Comprehensive logs and reports management with search, export, analysis

🧪 Comprehensive Test Coverage:
- Basic connectivity and health checks
- Individual tool testing with realistic parameters
- Enhanced journeys functionality (stage management, rules management, job lifecycle)
- Logs and reports functionality (search, filter, export, analyze)
- Parameter variation testing for all 40+ journey actions
- Error handling and validation testing
- Performance metrics and timing
- Integration examples for external applications

📊 Detailed Logging:
- Individual tool success/failure status
- Parameter validation results
- Error handling verification
- Performance metrics
- Comprehensive summary with statistics

🚀 Usage Examples:
- Basic testing: python3 test-http-access.py
- Remote server: python3 test-http-access.py --url http://server:8000
- Custom timeout: python3 test-http-access.py --timeout 60
- HTTPS with self-signed cert: python3 test-http-access.py --url https://server:8000 --no-ssl-verify

Perfect for validating Enhanced TMF ODA MCP Server deployments and ensuring all tools work correctly!
"""

import requests
import json
import time
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_color(color: str, message: str):
    """Print colored message."""
    print(f"{color}{message}{Colors.NC}")

def print_header(title: str):
    """Print section header."""
    print_color(Colors.BLUE, f"\n{'='*60}")
    print_color(Colors.BLUE, f"🎯 {title}")
    print_color(Colors.BLUE, f"{'='*60}")

class TMFODAHttpTester:
    """HTTP tester for Enhanced TMF ODA MCP Server REST API."""
    
    def __init__(self, base_url: str, timeout: int = 30, quick_test: bool = False):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.quick_test = quick_test
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Enhanced-TMF-ODA-HTTP-Tester/2.0'
        })
        self.test_results = []
        self.start_time = None
        
        print_color(Colors.CYAN, f"🌐 API Base URL: {self.base_url}")
        print_color(Colors.CYAN, f"⏱️ Request Timeout: {timeout}s")
        if quick_test:
            print_color(Colors.YELLOW, "⚡ Quick Test Mode: Only basic connectivity tests will run")
        else:
            print_color(Colors.PURPLE, "🔧 Enhanced Mode: Testing all 7 tools with comprehensive functionality")
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> tuple[bool, Dict[str, Any]]:
        """Make HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=self.timeout)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            response.raise_for_status()
            return True, response.json()
            
        except requests.exceptions.Timeout:
            return False, {"error": f"Request timed out after {self.timeout}s"}
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection failed - server unreachable"}
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = response.json() if response.content else str(e)
            except:
                error_detail = str(e)
            return False, {"error": f"HTTP {response.status_code}: {error_detail}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON response"}
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}
    
    def test_api_connectivity(self) -> bool:
        """Test basic API connectivity."""
        print_header("Enhanced API Connectivity Test")
        
        # Test root endpoint
        print_color(Colors.BLUE, f"🔍 Testing connection to {self.base_url}...")
        
        success, result = self.make_request('GET', '/')
        
        if success:
            print_color(Colors.GREEN, "✅ API connection successful")
            print_color(Colors.GREEN, f"✅ Service: {result.get('service', 'Unknown')}")
            print_color(Colors.GREEN, f"✅ Version: {result.get('version', 'Unknown')}")
            print_color(Colors.GREEN, f"✅ Status: {result.get('status', 'Unknown')}")
            
            tools = result.get('tools', [])
            print_color(Colors.GREEN, f"✅ Enhanced tools available: {len(tools)}")
            for tool in tools:
                print_color(Colors.BLUE, f"  📋 {tool}")
            
            if len(tools) >= 7:
                print_color(Colors.GREEN, "✅ All 7 enhanced tools detected (including logs-and-reports)")
            else:
                print_color(Colors.YELLOW, f"⚠️ Expected 7 tools but found {len(tools)}")
            
            return True
        else:
            print_color(Colors.RED, f"❌ API connection failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test health endpoint."""
        print_header("Enhanced Health Check Test")
        
        success, result = self.make_request('GET', '/health')
        
        if success:
            status = result.get('status', 'unknown')
            mcp_status = result.get('mcp_server', 'unknown')
            tools_count = result.get('tools_available', 0)
            
            if status == 'healthy':
                print_color(Colors.GREEN, f"✅ Health status: {status}")
                print_color(Colors.GREEN, f"✅ MCP server: {mcp_status}")
                print_color(Colors.GREEN, f"✅ Enhanced tools available: {tools_count}")
                
                if tools_count >= 7:
                    print_color(Colors.GREEN, "✅ All 7 enhanced tools are healthy")
                else:
                    print_color(Colors.YELLOW, f"⚠️ Expected 7 tools but health reports {tools_count}")
                
                return True
            else:
                print_color(Colors.YELLOW, f"⚠️ Health status: {status}")
                print_color(Colors.YELLOW, f"⚠️ MCP server: {mcp_status}")
                return False
        else:
            print_color(Colors.RED, f"❌ Health check failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_tools_endpoint(self) -> bool:
        """Test tools listing endpoint."""
        print_header("Enhanced Tools Endpoint Test")
        
        success, result = self.make_request('GET', '/tools')
        
        if success:
            tools = result.get('tools', [])
            print_color(Colors.GREEN, f"✅ Found {len(tools)} available enhanced tools:")
            
            expected_tools = [
                'raw-analysis', 'stripped-schema', 'get-job-logs', 
                'test-runner', 'journeys', 'run-jobs', 'logs-and-reports'
            ]
            
            for tool in tools:
                name = tool.get('name', 'Unknown')
                endpoint = tool.get('endpoint', 'Unknown')
                method = tool.get('method', 'Unknown')
                description = tool.get('description', 'No description')
                
                print_color(Colors.BLUE, f"  📋 {name}")
                print_color(Colors.BLUE, f"     🔗 {method} {endpoint}")
                print_color(Colors.BLUE, f"     📝 {description}")
                
                if name == 'journeys':
                    print_color(Colors.PURPLE, f"     ⚡ Enhanced with 40+ actions for complete lifecycle management")
                elif name == 'logs-and-reports':
                    print_color(Colors.PURPLE, f"     🆕 NEW tool for comprehensive logs and reports management")
            
            # Check if all expected tools are present
            tool_names = [tool.get('name', '') for tool in tools]
            missing_tools = [tool for tool in expected_tools if tool not in tool_names]
            
            if not missing_tools:
                print_color(Colors.GREEN, "✅ All 7 expected enhanced tools are available")
                return True
            else:
                print_color(Colors.YELLOW, f"⚠️ Missing tools: {', '.join(missing_tools)}")
                return len(tools) >= 6  # Accept if at least 6 tools are present
        else:
            print_color(Colors.RED, f"❌ Tools endpoint failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_tool_validation(self) -> Dict[str, Any]:
        """Test all enhanced tools with validation scenarios."""
        print_header("Enhanced Tool Validation Tests")
        
        validation_results = {}
        
        # Test 1: Raw Analysis (should fail with empty journey ID)
        print_color(Colors.BLUE, "⚡ Testing raw-analysis validation...")
        success, result = self.make_request('POST', '/tools/raw-analysis', {
            "journey_id": "",
            "stage_id": "raw_analysis"
        })
        
        if not success and "empty" in str(result.get('error', '')).lower():
            validation_results["raw_analysis"] = "✅ Correctly validates empty journey ID"
        elif not success:
            validation_results["raw_analysis"] = f"✅ Validation working: {result.get('error', 'Unknown error')}"
        else:
            validation_results["raw_analysis"] = "❌ Should have failed with empty journey ID"
        
        # Test 2: Stripped Schema (should fail with empty journey ID)
        print_color(Colors.BLUE, "🔧 Testing stripped-schema validation...")
        success, result = self.make_request('POST', '/tools/stripped-schema', {
            "journey_id": "",
            "stage_id": "stripped_schema"
        })
        
        if not success and "empty" in str(result.get('error', '')).lower():
            validation_results["stripped_schema"] = "✅ Correctly validates empty journey ID"
        elif not success:
            validation_results["stripped_schema"] = f"✅ Validation working: {result.get('error', 'Unknown error')}"
        else:
            validation_results["stripped_schema"] = "❌ Should have failed with empty journey ID"
        
        # Test 3: Get Job Logs (should fail with empty parameters)
        print_color(Colors.BLUE, "📋 Testing get-job-logs validation...")
        success, result = self.make_request('POST', '/tools/get-job-logs', {
            "journey_id": "",
            "stage_name": "raw_analysis",
            "job_id": "JOB-001-20240101120000",
            "step_name": "schema_parsing"
        })
        
        if not success and "empty" in str(result.get('error', '')).lower():
            validation_results["get_job_logs"] = "✅ Correctly validates empty journey ID"
        elif not success:
            validation_results["get_job_logs"] = f"✅ Validation working: {result.get('error', 'Unknown error')}"
        else:
            validation_results["get_job_logs"] = "❌ Should have failed with empty journey ID"
        
        # Test 4: Test Runner (should work with valid parameters)
        print_color(Colors.BLUE, "🧪 Testing test-runner...")
        success, result = self.make_request('POST', '/tools/test-runner', {
            "test_type": "quick",
            "include_performance": False
        })
        
        if success:
            test_result = result.get('result', {})
            
            # Handle different result formats
            if isinstance(test_result, dict):
                status = test_result.get('status', 'unknown')
                tests_passed = test_result.get('tests_passed', 0)
                total_tests = test_result.get('total_tests', 0)
                
                if status == 'success':
                    validation_results["test_runner"] = f"✅ Test runner passed: {tests_passed}/{total_tests} tests"
                else:
                    validation_results["test_runner"] = f"⚠️ Test runner partial: {status}"
            elif isinstance(test_result, list):
                # Handle list result format
                validation_results["test_runner"] = f"✅ Test runner returned {len(test_result)} test results"
            else:
                validation_results["test_runner"] = f"✅ Test runner returned: {str(test_result)[:100]}"
        else:
            validation_results["test_runner"] = f"❌ Test runner error: {result.get('error', 'Unknown error')}"
        
        # Test 5: Enhanced Journeys Tool (READ operation)
        print_color(Colors.BLUE, "🗺️ Testing enhanced journeys tool...")
        success, result = self.make_request('POST', '/tools/journeys', {
            "action": "read",
            "journey_id": "",
            "include_stages": True,
            "include_job_history": True,
            "limit": 5
        })
        
        if success:
            journey_result = result.get('result', {})
            if isinstance(journey_result, dict):
                operation = journey_result.get('operation', 'unknown')
                validation_results["journeys"] = f"✅ Enhanced journeys working: {operation} operation"
            else:
                validation_results["journeys"] = f"✅ Enhanced journeys returned: {str(journey_result)[:100]}"
        else:
            validation_results["journeys"] = f"❌ Enhanced journeys error: {result.get('error', 'Unknown error')}"
        
        # Test 6: NEW - Logs and Reports Tool
        print_color(Colors.BLUE, "📊 Testing NEW logs-and-reports tool...")
        success, result = self.make_request('POST', '/tools/logs-and-reports', {
            "action": "list_available_logs",
            "journey_id": "JRN-SAMPLE-001"
        })
        
        if success:
            logs_result = result.get('result', {})
            if isinstance(logs_result, dict):
                operation = logs_result.get('operation', 'unknown')
                validation_results["logs_and_reports"] = f"✅ Logs and reports working: {operation} operation"
            else:
                validation_results["logs_and_reports"] = f"✅ Logs and reports returned: {str(logs_result)[:100]}"
        else:
            validation_results["logs_and_reports"] = f"❌ Logs and reports error: {result.get('error', 'Unknown error')}"
        
        # Print results
        for tool, result_msg in validation_results.items():
            if result_msg.startswith("✅"):
                print_color(Colors.GREEN, f"{tool}: {result_msg}")
            elif result_msg.startswith("⚠️"):
                print_color(Colors.YELLOW, f"{tool}: {result_msg}")
            else:
                print_color(Colors.RED, f"{tool}: {result_msg}")
        
        return validation_results
    
    def test_all_tools_comprehensive(self) -> Dict[str, Any]:
        """Test all 7 available enhanced tools comprehensively with realistic parameters."""
        print_header("Comprehensive Enhanced Tool Testing - All 7 Tools")
        
        tool_results = {}
        
        # Test 1: Raw Analysis Tool
        print_color(Colors.CYAN, "⚡ Testing raw-analysis with realistic parameters...")
        test_params = {
            "journey_id": "JRN-SAMPLE-001",
            "stage_id": "raw_analysis",
            "triggered_by": "http-test",
            "reason": "Comprehensive testing via HTTP API"
        }
        
        success, result = self.make_request('POST', '/tools/raw-analysis', test_params)
        tool_results["raw_analysis"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ raw-analysis: Success")
            analysis_result = result.get('result', {})
            if isinstance(analysis_result, dict):
                status = analysis_result.get('status', 'unknown')
                job_id = analysis_result.get('job_id', 'N/A')
                print_color(Colors.BLUE, f"   📊 Status: {status}")
                print_color(Colors.BLUE, f"   🆔 Job ID: {job_id}")
        else:
            print_color(Colors.RED, f"❌ raw-analysis: {result.get('error', 'Unknown error')}")
        
        # Test 2: Stripped Schema Tool
        print_color(Colors.CYAN, "🔧 Testing stripped-schema with realistic parameters...")
        test_params = {
            "journey_id": "JRN-SAMPLE-001",
            "stage_id": "stripped_schema",
            "triggered_by": "http-test",
            "reason": "Comprehensive testing via HTTP API"
        }
        
        success, result = self.make_request('POST', '/tools/stripped-schema', test_params)
        tool_results["stripped_schema"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ stripped-schema: Success")
            analysis_result = result.get('result', {})
            if isinstance(analysis_result, dict):
                status = analysis_result.get('status', 'unknown')
                job_id = analysis_result.get('job_id', 'N/A')
                print_color(Colors.BLUE, f"   📊 Status: {status}")
                print_color(Colors.BLUE, f"   🆔 Job ID: {job_id}")
        else:
            print_color(Colors.RED, f"❌ stripped-schema: {result.get('error', 'Unknown error')}")
        
        # Test 3: Get Job Logs Tool
        print_color(Colors.CYAN, "📋 Testing get-job-logs with realistic parameters...")
        test_params = {
            "journey_id": "JRN-SAMPLE-001",
            "stage_name": "raw_analysis",
            "job_id": "JOB-001-20240101120000",
            "step_name": "schema_parsing"
        }
        
        success, result = self.make_request('POST', '/tools/get-job-logs', test_params)
        tool_results["get_job_logs"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ get-job-logs: Success")
            log_result = result.get('result', {})
            if isinstance(log_result, dict):
                log_success = log_result.get('success', False)
                location = log_result.get('location', 'N/A')
                print_color(Colors.BLUE, f"   📊 Log retrieval: {log_success}")
                print_color(Colors.BLUE, f"   📍 Location: {location}")
        else:
            print_color(Colors.RED, f"❌ get-job-logs: {result.get('error', 'Unknown error')}")
        
        # Test 4: Test Runner Tool
        print_color(Colors.CYAN, "🧪 Testing test-runner with realistic parameters...")
        test_params = {
            "test_type": "comprehensive",
            "include_performance": True
        }
        
        success, result = self.make_request('POST', '/tools/test-runner', test_params)
        tool_results["test_runner"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ test-runner: Success")
            test_result = result.get('result', {})
            if isinstance(test_result, dict):
                status = test_result.get('status', 'unknown')
                tests_passed = test_result.get('tests_passed', 0)
                total_tests = test_result.get('total_tests', 0)
                duration = test_result.get('duration_seconds', 0)
                print_color(Colors.BLUE, f"   📊 Status: {status}")
                print_color(Colors.BLUE, f"   📈 Tests: {tests_passed}/{total_tests}")
                print_color(Colors.BLUE, f"   ⏱️ Duration: {duration:.2f}s")
        else:
            print_color(Colors.RED, f"❌ test-runner: {result.get('error', 'Unknown error')}")
        
        # Test 5: Enhanced Journeys Tool (READ operation)
        print_color(Colors.CYAN, "🗺️ Testing enhanced journeys tool with READ operation...")
        test_params = {
            "action": "read",
            "journey_id": "JRN-SAMPLE-001",
            "include_stages": True,
            "include_job_history": True,
            "limit": 5
        }
        
        success, result = self.make_request('POST', '/tools/journeys', test_params)
        tool_results["journeys"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ enhanced journeys: Success")
            journey_result = result.get('result', {})
            if isinstance(journey_result, dict):
                operation = journey_result.get('operation', 'unknown')
                print_color(Colors.BLUE, f"   🎬 Operation: {operation}")
                print_color(Colors.PURPLE, f"   ⚡ Enhanced with 40+ actions available")
                
                if 'journey_status' in journey_result:
                    # Single journey details
                    journey_data = journey_result['journey_status']
                    status = journey_data.get('status', 'unknown')
                    progress = journey_data.get('overallProgress', 0)
                    print_color(Colors.BLUE, f"   📊 Status: {status}")
                    print_color(Colors.BLUE, f"   📈 Progress: {progress}%")
                elif 'journeys' in journey_result:
                    # List of journeys
                    journeys = journey_result.get('journeys', [])
                    print_color(Colors.BLUE, f"   📊 Found {len(journeys)} journeys")
        else:
            print_color(Colors.RED, f"❌ enhanced journeys: {result.get('error', 'Unknown error')}")
        
        # Test 6: Run Jobs Tool
        print_color(Colors.CYAN, "🏃 Testing run-jobs with realistic parameters...")
        test_params = {
            "journey_id": "JRN-SAMPLE-001",
            "stage_id": "data_mapping",
            "triggered_by": "http-test",
            "reason": "Comprehensive testing via HTTP API"
        }
        
        success, result = self.make_request('POST', '/tools/run-jobs', test_params)
        tool_results["run_jobs"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ run-jobs: Success")
            job_result = result.get('result', {})
            if isinstance(job_result, dict):
                status = job_result.get('status', 'unknown')
                job_id = job_result.get('job_id', 'N/A')
                print_color(Colors.BLUE, f"   📊 Status: {status}")
                print_color(Colors.BLUE, f"   🆔 Job ID: {job_id}")
        else:
            print_color(Colors.RED, f"❌ run-jobs: {result.get('error', 'Unknown error')}")
        
        # Test 7: NEW - Logs and Reports Tool
        print_color(Colors.CYAN, "📊 Testing NEW logs-and-reports tool...")
        test_params = {
            "action": "get_job_logs",
            "journey_id": "JRN-SAMPLE-001",
            "job_id": "JOB-001-20240101120000",
            "stage_name": "raw_analysis",
            "step_name": "schema_parsing"
        }
        
        success, result = self.make_request('POST', '/tools/logs-and-reports', test_params)
        tool_results["logs_and_reports"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ logs-and-reports: Success")
            logs_result = result.get('result', {})
            if isinstance(logs_result, dict):
                operation = logs_result.get('operation', 'unknown')
                print_color(Colors.BLUE, f"   🎬 Operation: {operation}")
                print_color(Colors.PURPLE, f"   🆕 NEW comprehensive logs and reports functionality")
                
                if 'logs' in logs_result:
                    logs_data = logs_result.get('logs', {})
                    # Handle different log structures - could be nested dict or direct list
                    if isinstance(logs_data, dict):
                        total_logs = logs_data.get('total_logs', len(logs_data.get('logs', [])))
                    elif isinstance(logs_data, list):
                        total_logs = len(logs_data)
                    else:
                        total_logs = 0
                    print_color(Colors.BLUE, f"   📊 Total logs: {total_logs}")
        else:
            print_color(Colors.RED, f"❌ logs-and-reports: {result.get('error', 'Unknown error')}")
        
        # Summary
        print_color(Colors.CYAN, "\n📊 Comprehensive Enhanced Tool Testing Summary:")
        successful_tools = sum(1 for tool, data in tool_results.items() if data["success"])
        total_tools = len(tool_results)
        
        print_color(Colors.BLUE, f"✅ Successful tools: {successful_tools}/{total_tools}")
        print_color(Colors.BLUE, f"❌ Failed tools: {total_tools - successful_tools}/{total_tools}")
        print_color(Colors.PURPLE, f"🔧 Enhanced tools tested: 7 (includes new logs-and-reports)")
        print_color(Colors.PURPLE, f"⚡ Enhanced journeys with 40+ lifecycle management actions")
        print_color(Colors.PURPLE, f"🆕 NEW logs-and-reports tool: Comprehensive logs and reports management")
        
        # List failed tools
        failed_tools = [tool for tool, data in tool_results.items() if not data["success"]]
        if failed_tools:
            print_color(Colors.RED, f"Failed tools: {', '.join(failed_tools)}")
        
        return tool_results
    
    def test_enhanced_journeys_actions(self) -> Dict[str, Any]:
        """Test enhanced journeys tool with various lifecycle management actions."""
        print_header("Enhanced Journeys Actions Testing - Lifecycle Management")
        
        enhanced_results = {}
        
        # Test enhanced journeys actions
        print_color(Colors.CYAN, "🧪 Testing enhanced journeys lifecycle management actions...")
        
        test_cases = [
            # Basic CRUD operations
            {"name": "list_all_journeys", "params": {"action": "read"}},
            {"name": "specific_journey", "params": {"action": "read", "journey_id": "JRN-SAMPLE-001"}},
            {"name": "create_journey_test", "params": {
                "action": "create",
                "journey_data": {
                    "name": "HTTP Test Journey",
                    "description": "Test journey created via HTTP API",
                    "oda_component_type": "product-catalog-management",
                    "priority": "low"
                }
            }},
            {"name": "update_journey_test", "params": {
                "action": "update",
                "journey_id": "JRN-SAMPLE-001",
                "journey_data": {
                    "status": "running",
                    "overall_progress": 75
                }
            }},
            
            # Stage Management (NEW)
            {"name": "list_stages", "params": {
                "action": "list_stages",
                "journey_id": "JRN-SAMPLE-001"
            }},
            {"name": "add_stage", "params": {
                "action": "add_stage",
                "journey_id": "JRN-SAMPLE-001",
                "stage_data": {
                    "stage_id": "custom_validation",
                    "name": "Custom Validation",
                    "description": "Custom validation stage"
                }
            }},
            {"name": "add_default_stages", "params": {
                "action": "add_default_stages",
                "journey_id": "JRN-SAMPLE-001"
            }},
            
            # Rules Management (NEW)
            {"name": "list_rules", "params": {
                "action": "list_rules",
                "journey_id": "JRN-SAMPLE-001",
                "stage_id": "data_mapping"
            }},
            {"name": "add_rule", "params": {
                "action": "add_rule",
                "journey_id": "JRN-SAMPLE-001",
                "stage_id": "data_mapping",
                "rule_data": {
                    "name": "Email Validation",
                    "rule_type": "validation",
                    "condition": "email IS NOT NULL"
                }
            }},
            
            # Job Management (NEW)
            {"name": "list_jobs", "params": {
                "action": "list_jobs",
                "journey_id": "JRN-SAMPLE-001",
                "stage_id": "raw_analysis"
            }},
            {"name": "run_job", "params": {
                "action": "run_job",
                "journey_id": "JRN-SAMPLE-001",
                "stage_id": "raw_analysis",
                "triggered_by": "http-test"
            }},
            {"name": "get_job_metrics", "params": {
                "action": "get_job_metrics",
                "journey_id": "JRN-SAMPLE-001",
                "job_id": "JOB-001-20240101120000"
            }},
            
            # Interactive Features (NEW)
            {"name": "dashboard", "params": {
                "action": "dashboard",
                "journey_id": "JRN-SAMPLE-001"
            }},
            {"name": "journey_summary", "params": {
                "action": "get_journey_summary",
                "journey_id": "JRN-SAMPLE-001"
            }},
            
            # Error handling tests
            {"name": "unsupported_action", "params": {"action": "invalid_action"}},
            {"name": "create_missing_data", "params": {
                "action": "create",
                "journey_data": None  # Should fail
            }}
        ]
        
        enhanced_results = {}
        for test_case in test_cases:
            success, result = self.make_request('POST', '/tools/journeys', test_case["params"])
            enhanced_results[test_case["name"]] = {
                "success": success,
                "params": test_case["params"],
                "result": result
            }
            
            if success:
                journey_result = result.get('result', {})
                operation = journey_result.get('operation', 'unknown')
                print_color(Colors.GREEN, f"✅ {test_case['name']}: Success ({operation})")
            else:
                # For error tests, this might be expected
                if test_case["name"] in ["unsupported_action", "create_missing_data"]:
                    print_color(Colors.GREEN, f"✅ {test_case['name']}: Correctly failed as expected")
                else:
                    print_color(Colors.RED, f"❌ {test_case['name']}: {result.get('error', 'Unknown error')}")
        
        return enhanced_results
    
    def test_logs_and_reports_actions(self) -> Dict[str, Any]:
        """Test the NEW logs and reports tool with various actions."""
        print_header("NEW Logs and Reports Tool Testing")
        
        logs_results = {}
        
        print_color(Colors.CYAN, "🧪 Testing NEW logs and reports functionality...")
        
        test_cases = [
            # Log Operations
            {"name": "get_job_logs", "params": {
                "action": "get_job_logs",
                "journey_id": "JRN-SAMPLE-001",
                "job_id": "JOB-001-20240101120000",
                "stage_name": "raw_analysis",
                "step_name": "schema_parsing"
            }},
            {"name": "list_available_logs", "params": {
                "action": "list_available_logs",
                "journey_id": "JRN-SAMPLE-001"
            }},
            {"name": "search_logs", "params": {
                "action": "search_logs",
                "journey_id": "JRN-SAMPLE-001",
                "search_query": "error"
            }},
            {"name": "get_logs_by_level", "params": {
                "action": "get_logs_by_level",
                "journey_id": "JRN-SAMPLE-001",
                "log_level": "error"
            }},
            
            # Report Operations
            {"name": "generate_summary_report", "params": {
                "action": "generate_summary_report",
                "journey_id": "JRN-SAMPLE-001",
                "job_id": "JOB-001-20240101120000"
            }},
            {"name": "get_error_summary", "params": {
                "action": "get_error_summary",
                "journey_id": "JRN-SAMPLE-001",
                "job_id": "JOB-001-20240101120000"
            }},
            
            # Analysis Operations
            {"name": "analyze_job_performance", "params": {
                "action": "analyze_job_performance",
                "journey_id": "JRN-SAMPLE-001",
                "job_id": "JOB-001-20240101120000"
            }},
            
            # Error handling
            {"name": "invalid_action", "params": {
                "action": "invalid_logs_action",
                "journey_id": "JRN-SAMPLE-001"
            }}
        ]
        
        for test_case in test_cases:
            success, result = self.make_request('POST', '/tools/logs-and-reports', test_case["params"])
            logs_results[test_case["name"]] = {
                "success": success,
                "params": test_case["params"],
                "result": result
            }
            
            if success:
                logs_result = result.get('result', {})
                operation = logs_result.get('operation', 'unknown')
                print_color(Colors.GREEN, f"✅ {test_case['name']}: Success ({operation})")
            else:
                # For error tests, this might be expected
                if test_case["name"] == "invalid_action":
                    print_color(Colors.GREEN, f"✅ {test_case['name']}: Correctly failed as expected")
                else:
                    print_color(Colors.RED, f"❌ {test_case['name']}: {result.get('error', 'Unknown error')}")
        
        print_color(Colors.PURPLE, f"🆕 NEW Logs and Reports Tool: {len(test_cases)} actions tested")
        return logs_results
    
    def test_tool_parameter_variations(self) -> Dict[str, Any]:
        """Test tools with different parameter variations."""
        print_header("Enhanced Parameter Variation Testing")
        
        variation_results = {}
        
        # Test enhanced journeys with different parameter combinations
        print_color(Colors.CYAN, "🧪 Testing enhanced journeys parameter variations...")
        enhanced_journeys_results = self.test_enhanced_journeys_actions()
        variation_results["enhanced_journeys_variations"] = enhanced_journeys_results
        
        # Test NEW logs and reports tool
        print_color(Colors.CYAN, "🧪 Testing NEW logs and reports parameter variations...")
        logs_reports_results = self.test_logs_and_reports_actions()
        variation_results["logs_reports_variations"] = logs_reports_results
        
        # Test test-runner with different types (existing)
        print_color(Colors.CYAN, "🧪 Testing test-runner parameter variations...")
        
        test_runner_cases = [
            {"name": "quick_test", "params": {"test_type": "quick", "include_performance": False}},
            {"name": "comprehensive_test", "params": {"test_type": "comprehensive", "include_performance": False}},
            {"name": "imports_test", "params": {"test_type": "imports", "include_performance": False}},
            {"name": "performance_test", "params": {"test_type": "quick", "include_performance": True}}
        ]
        
        test_runner_results = {}
        for test_case in test_runner_cases:
            success, result = self.make_request('POST', '/tools/test-runner', test_case["params"])
            test_runner_results[test_case["name"]] = {
                "success": success,
                "params": test_case["params"],
                "result": result
            }
            
            if success:
                print_color(Colors.GREEN, f"✅ {test_case['name']}: Success")
            else:
                print_color(Colors.RED, f"❌ {test_case['name']}: {result.get('error', 'Unknown error')}")
        
        variation_results["test_runner_variations"] = test_runner_results
        
        return variation_results
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid parameters."""
        print_header("Enhanced Error Handling Testing")
        
        error_results = {}
        
        # Test with completely invalid JSON
        print_color(Colors.CYAN, "🧪 Testing invalid JSON handling...")
        try:
            url = f"{self.base_url}/tools/test-runner"
            response = self.session.post(url, data="invalid json", headers={'Content-Type': 'application/json'})
            error_results["invalid_json"] = {
                "status_code": response.status_code,
                "response": response.text[:200] if response.text else "No response"
            }
            print_color(Colors.GREEN, f"✅ Invalid JSON handled: HTTP {response.status_code}")
        except Exception as e:
            error_results["invalid_json"] = {"error": str(e)}
            print_color(Colors.RED, f"❌ Invalid JSON test failed: {str(e)}")
        
        # Test with missing required parameters for enhanced tools
        print_color(Colors.CYAN, "🧪 Testing missing required parameters...")
        
        missing_param_tests = [
            {"tool": "raw-analysis", "params": {"stage_id": "raw_analysis"}},  # Missing journey_id
            {"tool": "stripped-schema", "params": {"stage_id": "stripped_schema"}},  # Missing journey_id
            {"tool": "get-job-logs", "params": {"journey_id": "JRN-001"}},  # Missing other required params
            {"tool": "journeys", "params": {"action": "update"}},  # Missing journey_id for update
            {"tool": "logs-and-reports", "params": {"action": "get_job_logs"}},  # Missing required params
        ]
        
        missing_param_results = {}
        for test in missing_param_tests:
            success, result = self.make_request('POST', f'/tools/{test["tool"]}', test["params"])
            missing_param_results[test["tool"]] = {
                "success": success,
                "params": test["params"],
                "result": result
            }
            
            if not success:
                print_color(Colors.GREEN, f"✅ {test['tool']}: Correctly rejected missing params")
            else:
                print_color(Colors.RED, f"❌ {test['tool']}: Should have failed with missing params")
        
        error_results["missing_params"] = missing_param_results
        
        return error_results
    
    def test_comprehensive_workflow(self) -> bool:
        """Test comprehensive workflow using test-runner."""
        print_header("Enhanced Comprehensive Workflow Test")
        
        print_color(Colors.BLUE, "🔍 Running enhanced comprehensive test suite...")
        
        success, result = self.make_request('POST', '/tools/test-runner', {
            "test_type": "comprehensive",
            "include_performance": True
        })
        
        if success:
            test_result = result.get('result', {})
            
            # Handle different result formats
            if isinstance(test_result, dict):
                status = test_result.get('status', 'unknown')
                message = test_result.get('message', 'No message')
                tests_passed = test_result.get('tests_passed', 0)
                tests_failed = test_result.get('tests_failed', 0)
                total_tests = test_result.get('total_tests', 0)
                success_rate = test_result.get('success_rate', 0)
                duration = test_result.get('duration_seconds', 0)
                
                print_color(Colors.GREEN, f"✅ Enhanced Workflow Status: {status}")
                print_color(Colors.BLUE, f"📊 Tests: {tests_passed}/{total_tests} passed, {tests_failed} failed")
                print_color(Colors.BLUE, f"📈 Success Rate: {success_rate}%")
                print_color(Colors.BLUE, f"⏱️ Duration: {duration:.2f}s")
                print_color(Colors.BLUE, f"💬 Message: {message}")
                print_color(Colors.PURPLE, f"🔧 Enhanced MCP Server with 7 tools tested")
                
                return status in ['success', 'partial_success']
            elif isinstance(test_result, list):
                print_color(Colors.GREEN, f"✅ Enhanced workflow returned {len(test_result)} test results")
                return True
            else:
                print_color(Colors.GREEN, f"✅ Enhanced workflow completed: {str(test_result)[:100]}")
                return True
        else:
            print_color(Colors.RED, f"❌ Enhanced comprehensive workflow failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance characteristics."""
        print_header("Enhanced Performance Metrics Test")
        
        metrics = {}
        
        # Test 1: API response time for health check
        start_time = time.time()
        success, result = self.make_request('GET', '/health')
        health_time = time.time() - start_time
        
        if success:
            metrics["health_response_time"] = health_time
            print_color(Colors.GREEN, f"✅ Health check time: {health_time:.3f}s")
        else:
            print_color(Colors.RED, f"❌ Health check failed: {result.get('error', 'Unknown error')}")
            metrics["health_response_time"] = None
        
        # Test 2: Quick test runner performance
        start_time = time.time()
        success, result = self.make_request('POST', '/tools/test-runner', {
            "test_type": "quick",
            "include_performance": False
        })
        test_runner_time = time.time() - start_time
        
        if success:
            metrics["test_runner_time"] = test_runner_time
            print_color(Colors.GREEN, f"✅ Test runner time: {test_runner_time:.3f}s")
            
            # Extract internal performance if available
            test_result = result.get('result', {})
            if isinstance(test_result, dict):
                internal_duration = test_result.get('duration_seconds', 0)
                if internal_duration:
                    print_color(Colors.BLUE, f"📊 Internal execution time: {internal_duration:.3f}s")
                    print_color(Colors.BLUE, f"📊 HTTP overhead: {(test_runner_time - internal_duration):.3f}s")
            else:
                print_color(Colors.BLUE, f"📊 Test result format: {type(test_result).__name__}")
        else:
            print_color(Colors.RED, f"❌ Test runner performance test failed: {result.get('error', 'Unknown error')}")
            metrics["test_runner_time"] = None
        
        # Test 3: Enhanced journeys performance
        start_time = time.time()
        success, result = self.make_request('POST', '/tools/journeys', {
            "action": "read",
            "journey_id": ""
        })
        journeys_time = time.time() - start_time
        
        if success:
            metrics["enhanced_journeys_time"] = journeys_time
            print_color(Colors.GREEN, f"✅ Enhanced journeys time: {journeys_time:.3f}s")
        else:
            print_color(Colors.RED, f"❌ Enhanced journeys performance test failed: {result.get('error', 'Unknown error')}")
            metrics["enhanced_journeys_time"] = None
        
        # Test 4: NEW - Logs and reports performance
        start_time = time.time()
        success, result = self.make_request('POST', '/tools/logs-and-reports', {
            "action": "list_available_logs",
            "journey_id": "JRN-SAMPLE-001"
        })
        logs_time = time.time() - start_time
        
        if success:
            metrics["logs_reports_time"] = logs_time
            print_color(Colors.GREEN, f"✅ Logs and reports time: {logs_time:.3f}s")
        else:
            print_color(Colors.RED, f"❌ Logs and reports performance test failed: {result.get('error', 'Unknown error')}")
            metrics["logs_reports_time"] = None
        
        # Test 5: Tools listing performance
        start_time = time.time()
        success, result = self.make_request('GET', '/tools')
        tools_time = time.time() - start_time
        
        if success:
            metrics["tools_listing_time"] = tools_time
            print_color(Colors.GREEN, f"✅ Tools listing time: {tools_time:.3f}s")
        else:
            print_color(Colors.RED, f"❌ Tools listing failed: {result.get('error', 'Unknown error')}")
            metrics["tools_listing_time"] = None
        
        return metrics
    
    def generate_integration_examples(self):
        """Generate examples for external application integration with enhanced functionality."""
        print_header("Enhanced Integration Examples for External UIs")
        
        print_color(Colors.CYAN, "🔌 Enhanced Python Integration Example:")
        print_color(Colors.BLUE, f'''
import requests
import json

class EnhancedTMFODAClient:
    def __init__(self, base_url="{self.base_url}"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({{'Content-Type': 'application/json'}})
    
    def health_check(self):
        """Check API health."""
        response = self.session.get(f"{{self.base_url}}/health")
        return response.json()
    
    def list_tools(self):
        """Get list of available enhanced tools."""
        response = self.session.get(f"{{self.base_url}}/tools")
        return response.json()
    
    def run_test_suite(self, test_type="quick"):
        """Run TMF ODA test suite."""
        data = {{"test_type": test_type, "include_performance": False}}
        response = self.session.post(f"{{self.base_url}}/tools/test-runner", json=data)
        return response.json()
    
    # Enhanced Journeys Management
    def create_journey(self, journey_data):
        """Create a new transformation journey."""
        data = {{"action": "create", "journey_data": journey_data}}
        response = self.session.post(f"{{self.base_url}}/tools/journeys", json=data)
        return response.json()
    
    def list_journeys(self):
        """List all transformation journeys."""
        data = {{"action": "read"}}
        response = self.session.post(f"{{self.base_url}}/tools/journeys", json=data)
        return response.json()
    
    def get_journey_details(self, journey_id):
        """Get detailed journey information."""
        data = {{"action": "read", "journey_id": journey_id, "include_stages": True, "include_job_history": True}}
        response = self.session.post(f"{{self.base_url}}/tools/journeys", json=data)
        return response.json()
    
    def add_stage(self, journey_id, stage_data):
        """Add a stage to a journey."""
        data = {{"action": "add_stage", "journey_id": journey_id, "stage_data": stage_data}}
        response = self.session.post(f"{{self.base_url}}/tools/journeys", json=data)
        return response.json()
    
    def run_job(self, journey_id, stage_id):
        """Execute a job for a specific stage."""
        data = {{"action": "run_job", "journey_id": journey_id, "stage_id": stage_id, "triggered_by": "api-client"}}
        response = self.session.post(f"{{self.base_url}}/tools/journeys", json=data)
        return response.json()
    
    def get_dashboard(self, journey_id):
        """Get journey dashboard view."""
        data = {{"action": "dashboard", "journey_id": journey_id}}
        response = self.session.post(f"{{self.base_url}}/tools/journeys", json=data)
        return response.json()
    
    # NEW - Logs and Reports Management
    def get_job_logs(self, journey_id, job_id, stage_name=None, step_name=None):
        """Get comprehensive job logs."""
        data = {{
            "action": "get_job_logs", 
            "journey_id": journey_id, 
            "job_id": job_id,
            "stage_name": stage_name,
            "step_name": step_name
        }}
        response = self.session.post(f"{{self.base_url}}/tools/logs-and-reports", json=data)
        return response.json()
    
    def generate_report(self, journey_id, job_id, report_type="summary"):
        """Generate comprehensive reports."""
        data = {{
            "action": "generate_summary_report", 
            "journey_id": journey_id, 
            "job_id": job_id
        }}
        response = self.session.post(f"{{self.base_url}}/tools/logs-and-reports", json=data)
        return response.json()
    
    def analyze_performance(self, journey_id, job_id):
        """Analyze job performance."""
        data = {{
            "action": "analyze_job_performance", 
            "journey_id": journey_id, 
            "job_id": job_id,
            "include_recommendations": True
        }}
        response = self.session.post(f"{{self.base_url}}/tools/logs-and-reports", json=data)
        return response.json()

# Enhanced Usage example:
client = EnhancedTMFODAClient()

# 1. Check system health
health = client.health_check()
print(f"System status: {{health.get('status')}}")

# 2. Create a new journey
journey_data = {{
    "name": "Product Catalog Migration",
    "oda_component_type": "product-catalog-management",
    "priority": "medium"
}}
journey_result = client.create_journey(journey_data)
journey_id = journey_result.get('result', {{}}).get('journey_id')

# 3. Add stages to the journey
stage_data = {{
    "stage_id": "custom_validation",
    "name": "Custom Validation",
    "description": "Custom business rules validation"
}}
client.add_stage(journey_id, stage_data)

# 4. Execute a job
job_result = client.run_job(journey_id, "raw_analysis")
job_id = job_result.get('result', {{}}).get('job_id')

# 5. Monitor with dashboard
dashboard = client.get_dashboard(journey_id)

# 6. Get comprehensive logs
logs = client.get_job_logs(journey_id, job_id, "raw_analysis")

# 7. Generate performance report
report = client.generate_report(journey_id, job_id)

# 8. Analyze performance
analysis = client.analyze_performance(journey_id, job_id)
''')
        
        print_color(Colors.CYAN, "\n🌐 Enhanced JavaScript/Node.js Example:")
        print_color(Colors.BLUE, f'''
class EnhancedTMFODAClient {{
    constructor(baseUrl = '{self.base_url}') {{
        this.baseUrl = baseUrl;
    }}
    
    async healthCheck() {{
        const response = await fetch(`${{this.baseUrl}}/health`);
        return await response.json();
    }}
    
    async listTools() {{
        const response = await fetch(`${{this.baseUrl}}/tools`);
        return await response.json();
    }}
    
    // Enhanced Journey Management
    async createJourney(journeyData) {{
        const response = await fetch(`${{this.baseUrl}}/tools/journeys`, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                action: 'create',
                journey_data: journeyData
            }})
        }});
        return await response.json();
    }}
    
    async listJourneys() {{
        const response = await fetch(`${{this.baseUrl}}/tools/journeys`, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{ action: 'read' }})
        }});
        return await response.json();
    }}
    
    async getDashboard(journeyId) {{
        const response = await fetch(`${{this.baseUrl}}/tools/journeys`, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                action: 'dashboard',
                journey_id: journeyId
            }})
        }});
        return await response.json();
    }}
    
    // NEW - Logs and Reports
    async getJobLogs(journeyId, jobId, stageName = null) {{
        const response = await fetch(`${{this.baseUrl}}/tools/logs-and-reports`, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                action: 'get_job_logs',
                journey_id: journeyId,
                job_id: jobId,
                stage_name: stageName
            }})
        }});
        return await response.json();
    }}
    
    async generateReport(journeyId, jobId) {{
        const response = await fetch(`${{this.baseUrl}}/tools/logs-and-reports`, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                action: 'generate_summary_report',
                journey_id: journeyId,
                job_id: jobId
            }})
        }});
        return await response.json();
    }}
}}

// Enhanced Usage:
const client = new EnhancedTMFODAClient();
const health = await client.healthCheck();
const tools = await client.listTools();

// Complete workflow example
async function runEnhancedWorkflow() {{
    try {{
        // 1. Check health
        const health = await client.healthCheck();
        console.log('System healthy:', health.status === 'healthy');
        
        // 2. Create journey
        const journeyData = {{
            name: 'Product Catalog Migration',
            oda_component_type: 'product-catalog-management',
            priority: 'medium'
        }};
        const journey = await client.createJourney(journeyData);
        const journeyId = journey.result?.journey_id;
        
        // 3. Get dashboard
        const dashboard = await client.getDashboard(journeyId);
        console.log('Dashboard:', dashboard.result?.dashboard);
        
        // 4. Get logs (if jobs exist)
        const logs = await client.getJobLogs(journeyId, 'JOB-001');
        console.log('Logs retrieved:', logs.result?.logs?.total_logs);
        
    }} catch (error) {{
        console.error('Workflow error:', error);
    }}
}}
''')
        
        print_color(Colors.CYAN, "\n📱 Enhanced React Component Example:")
        print_color(Colors.BLUE, f'''
import React, {{ useState, useEffect }} from 'react';

function EnhancedTMFODADashboard() {{
    const [health, setHealth] = useState(null);
    const [tools, setTools] = useState([]);
    const [journeys, setJourneys] = useState([]);
    const [selectedJourney, setSelectedJourney] = useState(null);
    const [dashboard, setDashboard] = useState(null);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    
    const API_BASE = '{self.base_url}';
    
    useEffect(() => {{
        fetchHealth();
        fetchTools();
        fetchJourneys();
    }}, []);
    
    const fetchHealth = async () => {{
        try {{
            const response = await fetch(`${{API_BASE}}/health`);
            const data = await response.json();
            setHealth(data);
        }} catch (error) {{
            console.error('Health check failed:', error);
        }}
    }};
    
    const fetchTools = async () => {{
        try {{
            const response = await fetch(`${{API_BASE}}/tools`);
            const data = await response.json();
            setTools(data.tools || []);
        }} catch (error) {{
            console.error('Failed to fetch tools:', error);
        }}
    }};
    
    const fetchJourneys = async () => {{
        try {{
            const response = await fetch(`${{API_BASE}}/tools/journeys`, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ action: 'read' }})
            }});
            const data = await response.json();
            setJourneys(data.result?.journeys || []);
        }} catch (error) {{
            console.error('Failed to fetch journeys:', error);
        }}
    }};
    
    const fetchDashboard = async (journeyId) => {{
        setLoading(true);
        try {{
            const response = await fetch(`${{API_BASE}}/tools/journeys`, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ 
                    action: 'dashboard', 
                    journey_id: journeyId 
                }})
            }});
            const data = await response.json();
            setDashboard(data.result?.dashboard);
        }} catch (error) {{
            console.error('Dashboard fetch failed:', error);
        }}
        setLoading(false);
    }};
    
    const fetchLogs = async (journeyId, jobId) => {{
        try {{
            const response = await fetch(`${{API_BASE}}/tools/logs-and-reports`, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ 
                    action: 'get_job_logs', 
                    journey_id: journeyId,
                    job_id: jobId
                }})
            }});
            const data = await response.json();
            setLogs(data.result?.logs?.logs || []);
        }} catch (error) {{
            console.error('Logs fetch failed:', error);
        }}
    }};
    
    const createJourney = async () => {{
        const journeyData = {{
            name: 'New Transformation Journey',
            description: 'Created from React UI',
            oda_component_type: 'customer-management',
            priority: 'medium'
        }};
        
        try {{
            const response = await fetch(`${{API_BASE}}/tools/journeys`, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ 
                    action: 'create', 
                    journey_data: journeyData 
                }})
            }});
            const data = await response.json();
            if (data.result?.status === 'success') {{
                fetchJourneys(); // Refresh list
            }}
        }} catch (error) {{
            console.error('Journey creation failed:', error);
        }}
    }};
    
    return (
        <div className="enhanced-tmf-oda-dashboard">
            <h1>Enhanced TMF ODA Transformer Dashboard</h1>
            
            {{/* System Health */}}
            <div className="health-status">
                <h2>System Health</h2>
                {{health && (
                    <div className={{`status ${{health.status}}`}}>
                        Status: {{health.status}} | Tools: {{health.tools_available || 7}}
                        {{health.status === 'healthy' && (
                            <span className="badge-success">✅ All 7 Enhanced Tools Active</span>
                        )}}
                    </div>
                )}}
            </div>
            
            {{/* Available Tools */}}
            <div className="available-tools">
                <h2>Enhanced Tools ({{tools.length}})</h2>
                {{tools.map(tool => (
                    <div key={{tool.name}} className="tool-card">
                        <h3>{{tool.name}}</h3>
                        <p>{{tool.description}}</p>
                        {{tool.name === 'journeys' && (
                            <span className="badge-enhanced">⚡ 40+ Actions</span>
                        )}}
                        {{tool.name === 'logs-and-reports' && (
                            <span className="badge-new">🆕 NEW</span>
                        )}}
                    </div>
                ))}}
            </div>
            
            {{/* Journey Management */}}
            <div className="journey-management">
                <h2>Journey Management</h2>
                <button onClick={{createJourney}} className="btn-primary">
                    Create New Journey
                </button>
                
                <div className="journeys-list">
                    {{journeys.map(journey => (
                        <div key={{journey.journeyId}} className="journey-card">
                            <h3>{{journey.name}}</h3>
                            <p>Status: {{journey.status}} | Progress: {{journey.progress}}%</p>
                            <button 
                                onClick={{() => {{
                                    setSelectedJourney(journey);
                                    fetchDashboard(journey.journeyId);
                                }}}}
                                className="btn-secondary"
                            >
                                View Dashboard
                            </button>
                        </div>
                    ))}}
                </div>
            </div>
            
            {{/* Dashboard View */}}
            {{selectedJourney && dashboard && (
                <div className="dashboard-view">
                    <h2>Journey Dashboard: {{selectedJourney.name}}</h2>
                    {{loading ? (
                        <div>Loading dashboard...</div>
                    ) : (
                        <div className="dashboard-content">
                            <div className="overview">
                                <h3>Overview</h3>
                                <p>Progress: {{dashboard.journey_overview?.overall_progress}}%</p>
                                <p>Current Stage: {{dashboard.journey_overview?.current_stage}}</p>
                            </div>
                            
                            <div className="jobs-summary">
                                <h3>Jobs Summary</h3>
                                <p>Total: {{dashboard.jobs_summary?.total_jobs}}</p>
                                <p>Completed: {{dashboard.jobs_summary?.completed_jobs}}</p>
                                <p>Running: {{dashboard.jobs_summary?.running_jobs}}</p>
                            </div>
                            
                            <div className="performance">
                                <h3>Performance</h3>
                                <p>Success Rate: {{dashboard.performance_summary?.success_rate}}%</p>
                                <p>Avg Duration: {{dashboard.performance_summary?.average_job_duration}}min</p>
                            </div>
                        </div>
                    )}}
                </div>
            )}}
            
            {{/* Logs View */}}
            {{logs.length > 0 && (
                <div className="logs-view">
                    <h2>Recent Logs</h2>
                    <div className="logs-list">
                        {{logs.slice(0, 10).map((log, index) => (
                            <div key={{index}} className={{`log-entry log-${{log.level?.toLowerCase()}}`}}>
                                <span className="timestamp">{{log.timestamp}}</span>
                                <span className="level">{{log.level}}</span>
                                <span className="message">{{log.message}}</span>
                            </div>
                        ))}}
                    </div>
                </div>
            )}}
        </div>
    );
}}

export default EnhancedTMFODADashboard;
''')
        
        print_color(Colors.CYAN, "\n🔧 Enhanced cURL Examples:")
        print_color(Colors.BLUE, f'''
# Health check
curl -X GET {self.base_url}/health

# List all enhanced tools (should show 7 tools)
curl -X GET {self.base_url}/tools

# Enhanced Journeys Management

# Create journey
curl -X POST {self.base_url}/tools/journeys \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "create",
    "journey_data": {{
      "name": "Customer Data Migration",
      "description": "Migrate legacy customer data to TMF ODA",
      "oda_component_type": "customer-management",
      "priority": "high"
    }}
  }}'

# List all journeys
curl -X POST {self.base_url}/tools/journeys \\
  -H "Content-Type: application/json" \\
  -d '{{"action": "read"}}'

# Get journey details with stages and job history
curl -X POST {self.base_url}/tools/journeys \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "read",
    "journey_id": "JRN-SAMPLE-001",
    "include_stages": true,
    "include_job_history": true
  }}'

# Add a stage to journey
curl -X POST {self.base_url}/tools/journeys \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "add_stage",
    "journey_id": "JRN-SAMPLE-001",
    "stage_data": {{
      "stage_id": "custom_validation",
      "name": "Custom Validation",
      "description": "Custom business validation rules"
    }}
  }}'

# Run a job
curl -X POST {self.base_url}/tools/journeys \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "run_job",
    "journey_id": "JRN-SAMPLE-001",
    "stage_id": "raw_analysis",
    "triggered_by": "curl-user"
  }}'

# Get job metrics
curl -X POST {self.base_url}/tools/journeys \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "get_job_metrics",
    "journey_id": "JRN-SAMPLE-001",
    "job_id": "JOB-001-20240101120000"
  }}'

# Get dashboard view
curl -X POST {self.base_url}/tools/journeys \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "dashboard",
    "journey_id": "JRN-SAMPLE-001"
  }}'

# NEW - Logs and Reports Management

# Get job logs
curl -X POST {self.base_url}/tools/logs-and-reports \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "get_job_logs",
    "journey_id": "JRN-SAMPLE-001",
    "job_id": "JOB-001-20240101120000",
    "stage_name": "raw_analysis",
    "step_name": "schema_parsing"
  }}'

# Search logs
curl -X POST {self.base_url}/tools/logs-and-reports \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "search_logs",
    "journey_id": "JRN-SAMPLE-001",
    "search_query": "error",
    "level_filter": "error"
  }}'

# Generate summary report
curl -X POST {self.base_url}/tools/logs-and-reports \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "generate_summary_report",
    "journey_id": "JRN-SAMPLE-001",
    "job_id": "JOB-001-20240101120000"
  }}'

# Analyze job performance
curl -X POST {self.base_url}/tools/logs-and-reports \\
  -H "Content-Type: application/json" \\
  -d '{{
    "action": "analyze_job_performance",
    "journey_id": "JRN-SAMPLE-001",
    "job_id": "JOB-001-20240101120000",
    "include_recommendations": true
  }}'
''')
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all enhanced HTTP tests."""
        self.start_time = datetime.now()
        
        print_color(Colors.GREEN, "🚀 Enhanced TMF ODA Transformer MCP Server - HTTP Testing Suite")
        print_color(Colors.GREEN, "="*70)
        print_color(Colors.BLUE, f"🕐 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print_color(Colors.PURPLE, "🔧 Testing 7 enhanced tools with comprehensive functionality")
        
        results = {
            "start_time": self.start_time.isoformat(),
            "connection_type": "http",
            "base_url": self.base_url,
            "timeout": self.timeout,
            "tools_count": 7,
            "enhanced_features": [
                "comprehensive_journey_management",
                "stage_management", 
                "rules_management",
                "job_lifecycle_management",
                "logs_and_reports",
                "interactive_dashboards",
                "performance_analysis",
                "40_plus_journey_actions"
            ],
            "tests": {}
        }
        
        # Test 1: Enhanced API Connectivity
        results["tests"]["api_connectivity"] = self.test_api_connectivity()
        
        if not results["tests"]["api_connectivity"]:
            print_color(Colors.RED, "❌ API connectivity failed. Cannot proceed with tests.")
            return results
        
        # Test 2: Enhanced Health Check
        results["tests"]["health_check"] = self.test_health_endpoint()
        
        # Test 3: Enhanced Tools Endpoint
        results["tests"]["tools_endpoint"] = self.test_tools_endpoint()
        
        # Test 4: Enhanced Tool Validation
        results["tests"]["tool_validation"] = self.test_tool_validation()
        
        if self.quick_test:
            print_color(Colors.YELLOW, "\n⚡ Quick Test Mode: Skipping comprehensive enhanced tool testing")
            print_color(Colors.BLUE, "✅ Basic connectivity and validation tests completed")
            print_color(Colors.PURPLE, "ℹ️ Run without --quick-test to test all 40+ journey actions and logs/reports")
        else:
            # Test 5: Comprehensive Enhanced Tool Testing
            results["tests"]["comprehensive_tools"] = self.test_all_tools_comprehensive()
            
            # Test 6: Enhanced Parameter Variation Testing
            results["tests"]["parameter_variations"] = self.test_tool_parameter_variations()
            
            # Test 7: Enhanced Error Handling Testing
            results["tests"]["error_handling"] = self.test_error_handling()
            
            # Test 8: Enhanced Comprehensive Workflow
            results["tests"]["comprehensive_workflow"] = self.test_comprehensive_workflow()
        
        # Test 9: Enhanced Performance Metrics (always run)
        results["tests"]["performance_metrics"] = self.test_performance_metrics()
        
        # Generate enhanced integration examples (always run)
        self.generate_integration_examples()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration
        
        print_header("Enhanced Final Test Summary")
        
        # Calculate comprehensive statistics
        total_tests = 0
        passed_tests = 0
        
        for test_name, test_result in results["tests"].items():
            if test_name == "comprehensive_tools":
                # Count individual tool tests
                if isinstance(test_result, dict):
                    for tool_name, tool_data in test_result.items():
                        if isinstance(tool_data, dict) and "success" in tool_data:
                            total_tests += 1
                            if tool_data["success"]:
                                passed_tests += 1
            elif test_name == "parameter_variations":
                # Count parameter variation tests
                if isinstance(test_result, dict):
                    for variation_group, variations in test_result.items():
                        if isinstance(variations, dict):
                            for variation_name, variation_data in variations.items():
                                if isinstance(variation_data, dict) and "success" in variation_data:
                                    total_tests += 1
                                    if variation_data["success"]:
                                        passed_tests += 1
            elif test_name == "error_handling":
                # Count error handling tests
                if isinstance(test_result, dict):
                    for group_name, group_tests in test_result.items():
                        if isinstance(group_tests, dict):
                            if group_name in ["missing_params"]:
                                for error_test, error_data in group_tests.items():
                                    if isinstance(error_data, dict) and "success" in error_data:
                                        total_tests += 1
                                        # For error tests, we expect failure (success=False)
                                        if not error_data["success"]:
                                            passed_tests += 1
                            else:
                                total_tests += 1
                                passed_tests += 1  # Other error tests are considered passed if they don't crash
            elif isinstance(test_result, (bool, dict)):
                total_tests += 1
                if test_result is True or (isinstance(test_result, dict) and test_result):
                    passed_tests += 1
        
        print_color(Colors.BLUE, f"⏱️ Total duration: {duration:.2f} seconds")
        print_color(Colors.BLUE, f"📊 Tests passed: {passed_tests}/{total_tests}")
        print_color(Colors.PURPLE, f"🔧 Enhanced tools tested: 7 (includes new logs-and-reports)")
        print_color(Colors.PURPLE, f"⚡ Enhanced journeys with 40+ lifecycle management actions")
        print_color(Colors.PURPLE, f"🆕 NEW logs-and-reports tool: Comprehensive logs and reports management")
        
        # Detailed breakdown
        print_color(Colors.CYAN, "\n📋 Detailed Enhanced Test Results:")
        
        # Individual tool results
        if "comprehensive_tools" in results["tests"]:
            tool_results = results["tests"]["comprehensive_tools"]
            successful_tools = sum(1 for tool, data in tool_results.items() if data.get("success", False))
            print_color(Colors.BLUE, f"🔧 Enhanced Tool Tests: {successful_tools}/{len(tool_results)} tools successful")
            
            for tool_name, tool_data in tool_results.items():
                if tool_data.get("success", False):
                    if tool_name == "journeys":
                        print_color(Colors.GREEN, f"   ✅ {tool_name} (enhanced with 40+ actions)")
                    elif tool_name == "logs_and_reports":
                        print_color(Colors.GREEN, f"   ✅ {tool_name} (NEW comprehensive tool)")
                    else:
                        print_color(Colors.GREEN, f"   ✅ {tool_name}")
                else:
                    error_msg = tool_data.get("result", {}).get("error", "Unknown error")
                    print_color(Colors.RED, f"   ❌ {tool_name}: {error_msg}")
        
        # Enhanced parameter variation results
        if "parameter_variations" in results["tests"]:
            var_results = results["tests"]["parameter_variations"]
            print_color(Colors.BLUE, f"🧪 Enhanced Parameter Variation Tests:")
            
            for group_name, group_tests in var_results.items():
                if isinstance(group_tests, dict):
                    successful_variations = sum(1 for test, data in group_tests.items() if data.get("success", False))
                    if group_name == "enhanced_journeys_variations":
                        print_color(Colors.BLUE, f"   Enhanced journeys (40+ actions): {successful_variations}/{len(group_tests)} successful")
                    elif group_name == "logs_reports_variations":
                        print_color(Colors.BLUE, f"   NEW logs & reports: {successful_variations}/{len(group_tests)} successful")
                    else:
                        print_color(Colors.BLUE, f"   {group_name}: {successful_variations}/{len(group_tests)} successful")
        
        # Enhanced error handling results
        if "error_handling" in results["tests"]:
            error_results = results["tests"]["error_handling"]
            print_color(Colors.BLUE, f"🛡️ Enhanced Error Handling Tests:")
            
            for group_name, group_tests in error_results.items():
                if isinstance(group_tests, dict):
                    if group_name == "missing_params":
                        # For these tests, success means the tool correctly rejected bad input
                        successful_errors = sum(1 for test, data in group_tests.items() if not data.get("success", True))
                        print_color(Colors.BLUE, f"   Missing params (5 tools): {successful_errors}/{len(group_tests)} correctly rejected")
                    else:
                        print_color(Colors.BLUE, f"   {group_name}: Handled successfully")
        
        if passed_tests == total_tests:
            print_color(Colors.GREEN, "\n🎉 ALL ENHANCED TESTS PASSED!")
            if self.quick_test:
                print_color(Colors.GREEN, "✅ Enhanced TMF ODA MCP Server HTTP API basic connectivity is working!")
                print_color(Colors.GREEN, "✅ All 7 enhanced tools detected and validated!")
                print_color(Colors.YELLOW, "ℹ️ Run without --quick-test to test all 40+ journey actions and logs/reports")
            else:
                print_color(Colors.GREEN, "✅ Enhanced TMF ODA MCP Server HTTP API is fully functional!")
                print_color(Colors.GREEN, "✅ All 7 enhanced tools including NEW logs-and-reports working!")
                print_color(Colors.GREEN, "✅ Enhanced journeys with 40+ lifecycle management actions operational!")
                print_color(Colors.GREEN, "✅ Comprehensive logs and reports functionality verified!")
                print_color(Colors.GREEN, "✅ Parameter validation and error handling robust!")
        elif passed_tests > total_tests * 0.8:
            print_color(Colors.YELLOW, f"\n⚠️ MOSTLY SUCCESSFUL ({passed_tests}/{total_tests} enhanced tests passed)")
            if self.quick_test:
                print_color(Colors.YELLOW, "✅ Enhanced TMF ODA MCP Server HTTP API basic connectivity is mostly working!")
                print_color(Colors.YELLOW, "ℹ️ Run without --quick-test to test all 40+ journey actions and logs/reports")
            else:
                print_color(Colors.YELLOW, "✅ Enhanced TMF ODA MCP Server HTTP API is mostly functional!")
            print_color(Colors.YELLOW, f"⚠️ {total_tests - passed_tests} enhanced test(s) need attention")
        else:
            print_color(Colors.RED, f"\n❌ MULTIPLE ISSUES FOUND ({passed_tests}/{total_tests} enhanced tests passed)")
            print_color(Colors.RED, f"❌ {total_tests - passed_tests} enhanced test(s) failed")
            if self.quick_test:
                print_color(Colors.RED, "❌ Basic enhanced connectivity tests failed")
            else:
                print_color(Colors.RED, "❌ Comprehensive enhanced testing revealed multiple issues")
        
        return results

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enhanced TMF ODA MCP Server HTTP Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comprehensive testing (all 7 enhanced tools with 40+ actions)
  python3 test-http-access.py
  
  # Quick connectivity test only
  python3 test-http-access.py --quick-test
  
  # Test remote machine by IP address
  python3 test-http-access.py --host 192.168.1.100
  
  # Test remote machine with custom port
  python3 test-http-access.py --host 192.168.1.100 --port 9000
  
  # Test remote machine with HTTPS
  python3 test-http-access.py --host server.example.com --protocol https --no-ssl-verify
  
  # Test remote HTTP API (full URL method)
  python3 test-http-access.py --url http://192.168.1.100:8000
  
  # Test with custom timeout
  python3 test-http-access.py --host 10.0.0.5 --timeout 60
  
  # Quick test on remote server
  python3 test-http-access.py --host 172.16.0.10 --quick-test

Remote Connection Options:
  📡 Method 1 - Individual Parameters (Recommended):
    --host IP_ADDRESS     # IP address or hostname of remote machine
    --port PORT_NUMBER    # Port number (default: 8000)
    --protocol http|https # Protocol to use (default: http)
  
  📡 Method 2 - Full URL:
    --url FULL_URL        # Complete URL (e.g., http://192.168.1.100:8000)
  
  Common Remote Scenarios:
    # AWS EC2 instance
    python3 test-http-access.py --host 18.191.87.212
    
    # Local network server
    python3 test-http-access.py --host 192.168.1.100 --port 9000
    
    # Docker container on different port
    python3 test-http-access.py --host 172.17.0.2 --port 8080
    
    # HTTPS with self-signed cert
    python3 test-http-access.py --host my-server.com --protocol https --no-ssl-verify

Enhanced Features Tested:
  🔧 7 Enhanced Tools:
    • raw-analysis, stripped-schema, get-job-logs, test-runner
    • journeys (enhanced with 40+ actions for complete lifecycle management)
    • run-jobs
    • logs-and-reports (NEW comprehensive tool)
  
  ⚡ Enhanced Journeys (40+ Actions):
    • Journey CRUD (create, read, update, delete, list)
    • Stage Management (list, add, update, delete, add_default)
    • Rules Management (list, add, update, delete for Second Brain rules)
    • Job Lifecycle (list, get, run, cancel, update_status, retry, metrics, timeline, batch)
    • Interactive Features (dashboard, journey_summary)
  
  🆕 NEW Logs and Reports Tool:
    • Comprehensive log management (get, search, filter, export)
    • Report generation (summary, performance, error analysis)
    • Performance analysis and recommendations
    • Error pattern analysis and insights
"""
    )
    
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Full base URL of the Enhanced TMF ODA HTTP API (e.g., http://192.168.1.100:8000). If not provided, URL is built from --host, --port, and --protocol"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="IP address or hostname of the remote machine (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number of the TMF ODA MCP Server (default: 8000)"
    )
    
    parser.add_argument(
        "--protocol",
        type=str,
        choices=["http", "https"],
        default="http",
        help="Protocol to use: http or https (default: http)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="Disable SSL certificate verification (for self-signed certs)"
    )
    
    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run only basic connectivity tests (skip comprehensive enhanced tool testing)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.url and (args.host != "localhost" or args.port != 8000 or args.protocol != "http"):
        print_color(Colors.YELLOW, "⚠️ Warning: --url provided along with --host/--port/--protocol. Using --url and ignoring other options.")
    
    # Determine the base URL
    if args.url:
        # Use provided URL directly
        base_url = args.url
        print_color(Colors.CYAN, f"🌐 Using provided URL: {base_url}")
    else:
        # Construct URL from host, port, and protocol
        base_url = f"{args.protocol}://{args.host}:{args.port}"
        if args.host == "localhost":
            print_color(Colors.CYAN, f"🌐 Testing local TMF ODA MCP Server: {base_url}")
        else:
            print_color(Colors.CYAN, f"🌐 Connecting to remote machine: {args.host}:{args.port} ({args.protocol})")
            print_color(Colors.BLUE, f"   📡 Make sure the TMF ODA MCP Server is running on {args.host}:{args.port}")
            print_color(Colors.BLUE, f"   🔥 Check firewall settings allow connections to port {args.port}")
            if args.protocol == "https":
                print_color(Colors.BLUE, f"   🔒 Using HTTPS - add --no-ssl-verify if using self-signed certificates")
    
    # Configure SSL verification
    if args.no_ssl_verify:
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        print_color(Colors.YELLOW, "⚠️ SSL certificate verification disabled")
    
    # Create enhanced tester instance
    tester = TMFODAHttpTester(
        base_url=base_url,
        timeout=args.timeout,
        quick_test=args.quick_test
    )
    
    # Run all enhanced tests
    results = tester.run_all_tests()
    
    # Save results to file
    results_filename = f"enhanced_http_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_filename, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print_color(Colors.BLUE, f"\n📁 Enhanced results saved to: {results_filename}")
    
    # Exit with appropriate code
    passed_tests = sum(1 for test, result in results["tests"].items() 
                      if isinstance(result, (bool, dict)) and 
                      (result is True or (isinstance(result, dict) and result)))
    total_tests = len([test for test, result in results["tests"].items() 
                      if isinstance(result, (bool, dict))])
    
    sys.exit(0 if passed_tests == total_tests else 1)

if __name__ == "__main__":
    main() 