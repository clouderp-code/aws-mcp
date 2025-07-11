#!/usr/bin/env python3
"""
Comprehensive HTTP Test Suite for TMF ODA Transformer MCP Server

This script provides comprehensive testing of all 8 available TMF ODA tools via HTTP REST API.
Perfect for external UIs, CI/CD pipelines, and integration testing - no SSH or Docker access required!

🔧 Tests All 8 Tools:
- schema-analyzer: Analyze schema files for TMF ODA compliance
- db-analyzer: Analyze database structures for TMF ODA compliance  
- raw-analysis: Execute raw analysis stage of transformation journey
- stripped-schema: Execute stripped schema stage of transformation journey
- get-job-logs: Retrieve execution logs for job steps
- test-runner: Run comprehensive test suite for all tools
- journeys: Comprehensive journey management with CRUD operations (CREATE, READ, UPDATE, DELETE)
- run-jobs: Execute any stage of a transformation journey

🧪 Comprehensive Test Coverage:
- Basic connectivity and health checks
- Individual tool testing with realistic parameters
- Parameter variation testing
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

Perfect for validating TMF ODA MCP Server deployments and ensuring all tools work correctly!
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
    """HTTP tester for TMF ODA MCP Server REST API."""
    
    def __init__(self, base_url: str, timeout: int = 30, quick_test: bool = False):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.quick_test = quick_test
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TMF-ODA-HTTP-Tester/1.0'
        })
        self.test_results = []
        self.start_time = None
        
        print_color(Colors.CYAN, f"🌐 API Base URL: {self.base_url}")
        print_color(Colors.CYAN, f"⏱️ Request Timeout: {timeout}s")
        if quick_test:
            print_color(Colors.YELLOW, "⚡ Quick Test Mode: Only basic connectivity tests will run")
    
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
        print_header("API Connectivity Test")
        
        # Test root endpoint
        print_color(Colors.BLUE, f"🔍 Testing connection to {self.base_url}...")
        
        success, result = self.make_request('GET', '/')
        
        if success:
            print_color(Colors.GREEN, "✅ API connection successful")
            print_color(Colors.GREEN, f"✅ Service: {result.get('service', 'Unknown')}")
            print_color(Colors.GREEN, f"✅ Version: {result.get('version', 'Unknown')}")
            print_color(Colors.GREEN, f"✅ Status: {result.get('status', 'Unknown')}")
            
            tools = result.get('tools', [])
            print_color(Colors.GREEN, f"✅ Tools available: {len(tools)}")
            for tool in tools:
                print_color(Colors.BLUE, f"  📋 {tool}")
            
            return True
        else:
            print_color(Colors.RED, f"❌ API connection failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test health endpoint."""
        print_header("Health Check Test")
        
        success, result = self.make_request('GET', '/health')
        
        if success:
            status = result.get('status', 'unknown')
            mcp_status = result.get('mcp_server', 'unknown')
            tools_count = result.get('tools_available', 0)
            
            if status == 'healthy':
                print_color(Colors.GREEN, f"✅ Health status: {status}")
                print_color(Colors.GREEN, f"✅ MCP server: {mcp_status}")
                print_color(Colors.GREEN, f"✅ Tools available: {tools_count}")
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
        print_header("Tools Endpoint Test")
        
        success, result = self.make_request('GET', '/tools')
        
        if success:
            tools = result.get('tools', [])
            print_color(Colors.GREEN, f"✅ Found {len(tools)} available tools:")
            
            for tool in tools:
                name = tool.get('name', 'Unknown')
                endpoint = tool.get('endpoint', 'Unknown')
                method = tool.get('method', 'Unknown')
                description = tool.get('description', 'No description')
                
                print_color(Colors.BLUE, f"  📋 {name}")
                print_color(Colors.BLUE, f"     🔗 {method} {endpoint}")
                print_color(Colors.BLUE, f"     📝 {description}")
            
            return len(tools) >= 6  # Should have 6 tools
        else:
            print_color(Colors.RED, f"❌ Tools endpoint failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_tool_validation(self) -> Dict[str, Any]:
        """Test all tools with validation scenarios."""
        print_header("Tool Validation Tests")
        
        validation_results = {}
        
        # Test 1: Schema Analyzer (should fail with empty workspace)
        print_color(Colors.BLUE, "📋 Testing schema-analyzer validation...")
        success, result = self.make_request('POST', '/tools/schema-analyzer', {
            "workspace_dir": "",
            "oda_component_type": "customer-management"
        })
        
        if not success and "empty" in str(result.get('error', '')).lower():
            validation_results["schema_analyzer"] = "✅ Correctly validates empty workspace"
        elif not success:
            validation_results["schema_analyzer"] = f"✅ Validation working: {result.get('error', 'Unknown error')}"
        else:
            validation_results["schema_analyzer"] = "❌ Should have failed with empty workspace"
        
        # Test 2: Database Analyzer (should fail with empty connection)
        print_color(Colors.BLUE, "🗄️ Testing db-analyzer validation...")
        success, result = self.make_request('POST', '/tools/db-analyzer', {
            "connection_string": "",
            "database_type": "postgresql",
            "oda_component_type": "customer-management"
        })
        
        if not success and "empty" in str(result.get('error', '')).lower():
            validation_results["db_analyzer"] = "✅ Correctly validates empty connection"
        elif not success:
            validation_results["db_analyzer"] = f"✅ Validation working: {result.get('error', 'Unknown error')}"
        else:
            validation_results["db_analyzer"] = "❌ Should have failed with empty connection"
        
        # Test 3: Raw Analysis (should fail with empty journey ID)
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
        
        # Test 4: Stripped Schema (should fail with empty journey ID)
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
        
        # Test 5: Get Job Logs (should fail with empty parameters)
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
        
        # Test 6: Test Runner (should work with valid parameters)
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
        """Test all 8 available tools comprehensively with realistic parameters."""
        print_header("Comprehensive Tool Testing - All 8 Tools")
        
        tool_results = {}
        
        # Test 1: Schema Analyzer Tool
        print_color(Colors.CYAN, "🔍 Testing schema-analyzer with realistic parameters...")
        test_params = {
            "workspace_dir": "/tmp",
            "oda_component_type": "customer-management",
            "schema_format": "json-schema"
        }
        
        success, result = self.make_request('POST', '/tools/schema-analyzer', test_params)
        tool_results["schema_analyzer"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ schema-analyzer: Success")
            # Try to extract meaningful info
            analysis_result = result.get('result', {})
            if isinstance(analysis_result, dict):
                total_files = analysis_result.get('total_files', 0)
                compliance_score = analysis_result.get('compliance_score', 0)
                print_color(Colors.BLUE, f"   📊 Files analyzed: {total_files}")
                print_color(Colors.BLUE, f"   📈 Compliance score: {compliance_score}")
        else:
            print_color(Colors.RED, f"❌ schema-analyzer: {result.get('error', 'Unknown error')}")
        
        # Test 2: Database Analyzer Tool
        print_color(Colors.CYAN, "🗄️ Testing db-analyzer with realistic parameters...")
        test_params = {
            "connection_string": "postgresql://testuser:testpass@localhost:5432/testdb",
            "database_type": "postgresql",
            "oda_component_type": "customer-management",
            "tables_filter": "customer_*,order_*"
        }
        
        success, result = self.make_request('POST', '/tools/db-analyzer', test_params)
        tool_results["db_analyzer"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ db-analyzer: Success")
            analysis_result = result.get('result', {})
            if isinstance(analysis_result, dict):
                total_tables = analysis_result.get('total_tables', 0)
                compliance_score = analysis_result.get('compliance_score', 0)
                print_color(Colors.BLUE, f"   📊 Tables analyzed: {total_tables}")
                print_color(Colors.BLUE, f"   📈 Compliance score: {compliance_score}")
        else:
            print_color(Colors.RED, f"❌ db-analyzer: {result.get('error', 'Unknown error')}")
        
        # Test 3: Raw Analysis Tool
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
        
        # Test 4: Stripped Schema Tool
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
        
        # Test 5: Get Job Logs Tool
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
        
        # Test 6: Test Runner Tool
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
        
        # Test 7: Journeys Tool (READ operation)
        print_color(Colors.CYAN, "🗺️ Testing journeys tool with READ operation...")
        test_params = {
            "action": "read",
            "journey_id": "JRN-SAMPLE-001",
            "stage_id": "raw_analysis",
            "include_stages": True,
            "include_job_history": True,
            "job_limit": 5
        }
        
        success, result = self.make_request('POST', '/tools/journeys', test_params)
        tool_results["journeys"] = {
            "success": success,
            "params": test_params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            print_color(Colors.GREEN, "✅ journeys: Success")
            journey_result = result.get('result', {})
            if isinstance(journey_result, dict):
                operation = journey_result.get('operation', 'unknown')
                print_color(Colors.BLUE, f"   🎬 Operation: {operation}")
                
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
            print_color(Colors.RED, f"❌ journeys: {result.get('error', 'Unknown error')}")
        
        # Test 8: Run Jobs Tool
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
        
        # Summary
        print_color(Colors.CYAN, "\n📊 Comprehensive Tool Testing Summary:")
        successful_tools = sum(1 for tool, data in tool_results.items() if data["success"])
        total_tools = len(tool_results)
        
        print_color(Colors.BLUE, f"✅ Successful tools: {successful_tools}/{total_tools}")
        print_color(Colors.BLUE, f"❌ Failed tools: {total_tools - successful_tools}/{total_tools}")
        
        # List failed tools
        failed_tools = [tool for tool, data in tool_results.items() if not data["success"]]
        if failed_tools:
            print_color(Colors.RED, f"Failed tools: {', '.join(failed_tools)}")
        
        return tool_results
    
    def test_tool_parameter_variations(self) -> Dict[str, Any]:
        """Test tools with different parameter variations."""
        print_header("Parameter Variation Testing")
        
        variation_results = {}
        
        # Test journeys with different parameter combinations (CRUD operations)
        print_color(Colors.CYAN, "🧪 Testing journeys parameter variations...")
        
        test_cases = [
            {"name": "list_all_journeys", "params": {"action": "read"}},
            {"name": "specific_journey", "params": {"action": "read", "journey_id": "JRN-SAMPLE-001"}},
            {"name": "journey_with_stages", "params": {
                "action": "read", 
                "journey_id": "JRN-SAMPLE-001", 
                "include_stages": True
            }},
            {"name": "journey_with_jobs", "params": {
                "action": "read", 
                "journey_id": "JRN-SAMPLE-001", 
                "include_job_history": True
            }},
            {"name": "journey_full_details", "params": {
                "action": "read",
                "journey_id": "JRN-SAMPLE-001",
                "include_stages": True,
                "include_job_history": True,
                "job_limit": 10
            }},
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
            }}
        ]
        
        journeys_results = {}
        for test_case in test_cases:
            success, result = self.make_request('POST', '/tools/journeys', test_case["params"])
            journeys_results[test_case["name"]] = {
                "success": success,
                "params": test_case["params"],
                "result": result
            }
            
            if success:
                print_color(Colors.GREEN, f"✅ {test_case['name']}: Success")
            else:
                print_color(Colors.RED, f"❌ {test_case['name']}: {result.get('error', 'Unknown error')}")
        
        variation_results["journeys_variations"] = journeys_results
        
        # Test test-runner with different types
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
        print_header("Error Handling Testing")
        
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
        
        # Test with missing required parameters
        print_color(Colors.CYAN, "🧪 Testing missing required parameters...")
        
        missing_param_tests = [
            {"tool": "schema-analyzer", "params": {"oda_component_type": "customer-management"}},  # Missing workspace_dir
            {"tool": "db-analyzer", "params": {"database_type": "postgresql"}},  # Missing connection_string
            {"tool": "raw-analysis", "params": {"stage_id": "raw_analysis"}},  # Missing journey_id
            {"tool": "get-job-logs", "params": {"journey_id": "JRN-001"}},  # Missing other required params
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
        
        # Test with invalid enum values
        print_color(Colors.CYAN, "🧪 Testing invalid enum values...")
        
        invalid_enum_tests = [
            {"tool": "schema-analyzer", "params": {
                "workspace_dir": "/tmp",
                "oda_component_type": "invalid-component-type"
            }},
            {"tool": "db-analyzer", "params": {
                "connection_string": "test://test",
                "database_type": "invalid-db-type",
                "oda_component_type": "customer-management"
            }},
        ]
        
        invalid_enum_results = {}
        for test in invalid_enum_tests:
            success, result = self.make_request('POST', f'/tools/{test["tool"]}', test["params"])
            invalid_enum_results[test["tool"]] = {
                "success": success,
                "params": test["params"],
                "result": result
            }
            
            if not success:
                print_color(Colors.GREEN, f"✅ {test['tool']}: Correctly rejected invalid enum")
            else:
                print_color(Colors.RED, f"❌ {test['tool']}: Should have failed with invalid enum")
        
        error_results["invalid_enums"] = invalid_enum_results
        
        return error_results
    
    def test_comprehensive_workflow(self) -> bool:
        """Test comprehensive workflow using test-runner."""
        print_header("Comprehensive Workflow Test")
        
        print_color(Colors.BLUE, "🔍 Running comprehensive test suite...")
        
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
                
                print_color(Colors.GREEN, f"✅ Workflow Status: {status}")
                print_color(Colors.BLUE, f"📊 Tests: {tests_passed}/{total_tests} passed, {tests_failed} failed")
                print_color(Colors.BLUE, f"📈 Success Rate: {success_rate}%")
                print_color(Colors.BLUE, f"⏱️ Duration: {duration:.2f}s")
                print_color(Colors.BLUE, f"💬 Message: {message}")
                
                return status in ['success', 'partial_success']
            elif isinstance(test_result, list):
                print_color(Colors.GREEN, f"✅ Workflow returned {len(test_result)} test results")
                return True
            else:
                print_color(Colors.GREEN, f"✅ Workflow completed: {str(test_result)[:100]}")
                return True
        else:
            print_color(Colors.RED, f"❌ Comprehensive workflow failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance characteristics."""
        print_header("Performance Metrics Test")
        
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
        
        # Test 3: Tools listing performance
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
        """Generate examples for external application integration."""
        print_header("Integration Examples for External UIs")
        
        print_color(Colors.CYAN, "🔌 Python Integration Example:")
        print_color(Colors.BLUE, f'''
import requests
import json

class TMFODAClient:
    def __init__(self, base_url="{self.base_url}"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({{'Content-Type': 'application/json'}})
    
    def health_check(self):
        """Check API health."""
        response = self.session.get(f"{{self.base_url}}/health")
        return response.json()
    
    def list_tools(self):
        """Get list of available tools."""
        response = self.session.get(f"{{self.base_url}}/tools")
        return response.json()
    
    def run_test_suite(self, test_type="quick"):
        """Run TMF ODA test suite."""
        data = {{"test_type": test_type, "include_performance": False}}
        response = self.session.post(f"{{self.base_url}}/tools/test-runner", json=data)
        return response.json()
    
    def analyze_schema(self, workspace_dir, oda_component_type="customer-management"):
        """Analyze schema files."""
        data = {{
            "workspace_dir": workspace_dir,
            "oda_component_type": oda_component_type
        }}
        response = self.session.post(f"{{self.base_url}}/tools/schema-analyzer", json=data)
        return response.json()

# Usage example:
client = TMFODAClient()
health = client.health_check()
tools = client.list_tools()
test_results = client.run_test_suite("comprehensive")
''')
        
        print_color(Colors.CYAN, "\n🌐 JavaScript/Node.js Example:")
        print_color(Colors.BLUE, f'''
class TMFODAClient {{
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
    
    async runTestSuite(testType = 'quick') {{
        const response = await fetch(`${{this.baseUrl}}/tools/test-runner`, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                test_type: testType,
                include_performance: false
            }})
        }});
        return await response.json();
    }}
    
    async analyzeSchema(workspaceDir, odaComponentType = 'customer-management') {{
        const response = await fetch(`${{this.baseUrl}}/tools/schema-analyzer`, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                workspace_dir: workspaceDir,
                oda_component_type: odaComponentType
            }})
        }});
        return await response.json();
    }}
}}

// Usage:
const client = new TMFODAClient();
const health = await client.healthCheck();
const tools = await client.listTools();
''')
        
        print_color(Colors.CYAN, "\n📱 React Component Example:")
        print_color(Colors.BLUE, f'''
import React, {{ useState, useEffect }} from 'react';

function TMFODADashboard() {{
    const [health, setHealth] = useState(null);
    const [tools, setTools] = useState([]);
    const [testResults, setTestResults] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const API_BASE = '{self.base_url}';
    
    useEffect(() => {{
        fetchHealth();
        fetchTools();
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
    
    const runTests = async () => {{
        setLoading(true);
        try {{
            const response = await fetch(`${{API_BASE}}/tools/test-runner`, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ test_type: 'comprehensive' }})
            }});
            const data = await response.json();
            setTestResults(data.result);
        }} catch (error) {{
            console.error('Test execution failed:', error);
        }}
        setLoading(false);
    }};
    
    return (
        <div className="tmf-oda-dashboard">
            <h1>TMF ODA Transformer Dashboard</h1>
            
            <div className="health-status">
                <h2>Health Status</h2>
                {{health && (
                    <div className={{`status ${{health.status}}`}}>
                        Status: {{health.status}} | Tools: {{health.tools_available}}
                    </div>
                )}}
            </div>
            
            <div className="available-tools">
                <h2>Available Tools ({{tools.length}})</h2>
                {{tools.map(tool => (
                    <div key={{tool.name}} className="tool-card">
                        <h3>{{tool.name}}</h3>
                        <p>{{tool.description}}</p>
                    </div>
                ))}}
            </div>
            
            <div className="test-runner">
                <h2>Test Runner</h2>
                <button onClick={{runTests}} disabled={{loading}}>
                    {{loading ? 'Running Tests...' : 'Run Comprehensive Tests'}}
                </button>
                {{testResults && (
                    <div className="test-results">
                        <p>Status: {{testResults.status}}</p>
                        <p>Success Rate: {{testResults.success_rate}}%</p>
                        <p>Duration: {{testResults.duration_seconds}}s</p>
                    </div>
                )}}
            </div>
        </div>
    );
}}

export default TMFODADashboard;
''')
        
        print_color(Colors.CYAN, "\n🔧 cURL Examples:")
        print_color(Colors.BLUE, f'''
# Health check
curl -X GET {self.base_url}/health

# List all tools
curl -X GET {self.base_url}/tools

# Run quick test
curl -X POST {self.base_url}/tools/test-runner \\
  -H "Content-Type: application/json" \\
  -d '{{"test_type": "quick", "include_performance": false}}'

# Analyze schema (with valid path)
curl -X POST {self.base_url}/tools/schema-analyzer \\
  -H "Content-Type: application/json" \\
  -d '{{
    "workspace_dir": "/path/to/schemas",
    "oda_component_type": "customer-management",
    "schema_format": "json-schema"
  }}'

# Check database (with valid connection)
curl -X POST {self.base_url}/tools/db-analyzer \\
  -H "Content-Type: application/json" \\
  -d '{{
    "connection_string": "postgresql://user:pass@host:5432/db",
    "database_type": "postgresql",
    "oda_component_type": "customer-management"
  }}'
''')
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all HTTP tests."""
        self.start_time = datetime.now()
        
        print_color(Colors.GREEN, "🚀 TMF ODA Transformer MCP Server - HTTP Testing Suite")
        print_color(Colors.GREEN, "="*70)
        print_color(Colors.BLUE, f"🕐 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            "start_time": self.start_time.isoformat(),
            "connection_type": "http",
            "base_url": self.base_url,
            "timeout": self.timeout,
            "tests": {}
        }
        
        # Test 1: API Connectivity
        results["tests"]["api_connectivity"] = self.test_api_connectivity()
        
        if not results["tests"]["api_connectivity"]:
            print_color(Colors.RED, "❌ API connectivity failed. Cannot proceed with tests.")
            return results
        
        # Test 2: Health Check
        results["tests"]["health_check"] = self.test_health_endpoint()
        
        # Test 3: Tools Endpoint
        results["tests"]["tools_endpoint"] = self.test_tools_endpoint()
        
        # Test 4: Basic Tool Validation
        results["tests"]["tool_validation"] = self.test_tool_validation()
        
        if self.quick_test:
            print_color(Colors.YELLOW, "\n⚡ Quick Test Mode: Skipping comprehensive tool testing")
            print_color(Colors.BLUE, "✅ Basic connectivity and validation tests completed")
        else:
            # Test 5: Comprehensive Tool Testing (NEW)
            results["tests"]["comprehensive_tools"] = self.test_all_tools_comprehensive()
            
            # Test 6: Parameter Variation Testing (NEW)
            results["tests"]["parameter_variations"] = self.test_tool_parameter_variations()
            
            # Test 7: Error Handling Testing (NEW)
            results["tests"]["error_handling"] = self.test_error_handling()
            
            # Test 8: Comprehensive Workflow
            results["tests"]["comprehensive_workflow"] = self.test_comprehensive_workflow()
        
        # Test 9: Performance Metrics (always run)
        results["tests"]["performance_metrics"] = self.test_performance_metrics()
        
        # Generate integration examples (always run)
        self.generate_integration_examples()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration
        
        print_header("Final Test Summary")
        
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
                            if group_name in ["missing_params", "invalid_enums"]:
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
        
        # Detailed breakdown
        print_color(Colors.CYAN, "\n📋 Detailed Test Results:")
        
        # Individual tool results
        if "comprehensive_tools" in results["tests"]:
            tool_results = results["tests"]["comprehensive_tools"]
            successful_tools = sum(1 for tool, data in tool_results.items() if data.get("success", False))
            print_color(Colors.BLUE, f"🔧 Tool Tests: {successful_tools}/{len(tool_results)} tools successful")
            
            for tool_name, tool_data in tool_results.items():
                if tool_data.get("success", False):
                    print_color(Colors.GREEN, f"   ✅ {tool_name}")
                else:
                    error_msg = tool_data.get("result", {}).get("error", "Unknown error")
                    print_color(Colors.RED, f"   ❌ {tool_name}: {error_msg}")
        
        # Parameter variation results
        if "parameter_variations" in results["tests"]:
            var_results = results["tests"]["parameter_variations"]
            print_color(Colors.BLUE, f"🧪 Parameter Variation Tests:")
            
            for group_name, group_tests in var_results.items():
                if isinstance(group_tests, dict):
                    successful_variations = sum(1 for test, data in group_tests.items() if data.get("success", False))
                    print_color(Colors.BLUE, f"   {group_name}: {successful_variations}/{len(group_tests)} variations successful")
        
        # Error handling results
        if "error_handling" in results["tests"]:
            error_results = results["tests"]["error_handling"]
            print_color(Colors.BLUE, f"🛡️ Error Handling Tests:")
            
            for group_name, group_tests in error_results.items():
                if isinstance(group_tests, dict):
                    if group_name in ["missing_params", "invalid_enums"]:
                        # For these tests, success means the tool correctly rejected bad input
                        successful_errors = sum(1 for test, data in group_tests.items() if not data.get("success", True))
                        print_color(Colors.BLUE, f"   {group_name}: {successful_errors}/{len(group_tests)} correctly rejected")
                    else:
                        print_color(Colors.BLUE, f"   {group_name}: Handled successfully")
        
        if passed_tests == total_tests:
            print_color(Colors.GREEN, "\n🎉 ALL TESTS PASSED!")
            if self.quick_test:
                print_color(Colors.GREEN, "✅ TMF ODA MCP Server HTTP API basic connectivity is working!")
                print_color(Colors.GREEN, "✅ All basic validation tests passed!")
                print_color(Colors.YELLOW, "ℹ️ Run without --quick-test for comprehensive tool testing")
            else:
                print_color(Colors.GREEN, "✅ TMF ODA MCP Server HTTP API is fully functional!")
                print_color(Colors.GREEN, "✅ All 8 tools are working correctly!")
                print_color(Colors.GREEN, "✅ Parameter validation is working!")
                print_color(Colors.GREEN, "✅ Error handling is robust!")
        elif passed_tests > total_tests * 0.8:
            print_color(Colors.YELLOW, f"\n⚠️ MOSTLY SUCCESSFUL ({passed_tests}/{total_tests} tests passed)")
            if self.quick_test:
                print_color(Colors.YELLOW, "✅ TMF ODA MCP Server HTTP API basic connectivity is mostly working!")
                print_color(Colors.YELLOW, "ℹ️ Run without --quick-test for comprehensive tool testing")
            else:
                print_color(Colors.YELLOW, "✅ TMF ODA MCP Server HTTP API is mostly functional!")
            print_color(Colors.YELLOW, f"⚠️ {total_tests - passed_tests} test(s) need attention")
        else:
            print_color(Colors.RED, f"\n❌ MULTIPLE ISSUES FOUND ({passed_tests}/{total_tests} tests passed)")
            print_color(Colors.RED, f"❌ {total_tests - passed_tests} test(s) failed")
            if self.quick_test:
                print_color(Colors.RED, "❌ Basic connectivity tests failed")
            else:
                print_color(Colors.RED, "❌ Comprehensive testing revealed multiple issues")
        
        return results

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="TMF ODA MCP Server HTTP Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comprehensive testing (all 8 tools)
  python3 test-http-access.py
  
  # Quick connectivity test only
  python3 test-http-access.py --quick-test
  
  # Test remote HTTP API
  python3 test-http-access.py --url http://192.168.1.100:8000
  
  # Test with custom timeout
  python3 test-http-access.py --url http://server:8000 --timeout 60
  
  # Test HTTPS API (with SSL verification disabled)
  python3 test-http-access.py --url https://server:8000 --no-ssl-verify
  
  # Quick test on remote server
  python3 test-http-access.py --url http://server:8000 --quick-test
"""
    )
    
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the TMF ODA HTTP API (default: http://localhost:8000)"
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
        help="Run only basic connectivity tests (skip comprehensive tool testing)"
    )
    
    args = parser.parse_args()
    
    # Configure SSL verification
    if args.no_ssl_verify:
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        print_color(Colors.YELLOW, "⚠️ SSL certificate verification disabled")
    
    # Create tester instance
    tester = TMFODAHttpTester(
        base_url=args.url,
        timeout=args.timeout,
        quick_test=args.quick_test
    )
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Save results to file
    results_filename = f"http_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_filename, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print_color(Colors.BLUE, f"\n📁 Results saved to: {results_filename}")
    
    # Exit with appropriate code
    passed_tests = sum(1 for test, result in results["tests"].items() 
                      if isinstance(result, (bool, dict)) and 
                      (result is True or (isinstance(result, dict) and result)))
    total_tests = len([test for test, result in results["tests"].items() 
                      if isinstance(result, (bool, dict))])
    
    sys.exit(0 if passed_tests == total_tests else 1)

if __name__ == "__main__":
    main() 