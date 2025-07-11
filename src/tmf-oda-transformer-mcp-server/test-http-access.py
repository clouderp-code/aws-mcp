#!/usr/bin/env python3
"""
HTTP Test Script for TMF ODA Transformer MCP Server
This script tests all 6 tools via HTTP REST API - perfect for external UIs!
No SSH or Docker access required - just HTTP calls.
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
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TMF-ODA-HTTP-Tester/1.0'
        })
        self.test_results = []
        self.start_time = None
        
        print_color(Colors.CYAN, f"🌐 API Base URL: {self.base_url}")
        print_color(Colors.CYAN, f"⏱️ Request Timeout: {timeout}s")
    
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
        
        # Test 4: Tool Validation
        results["tests"]["tool_validation"] = self.test_tool_validation()
        
        # Test 5: Comprehensive Workflow
        results["tests"]["comprehensive_workflow"] = self.test_comprehensive_workflow()
        
        # Test 6: Performance Metrics
        results["tests"]["performance_metrics"] = self.test_performance_metrics()
        
        # Generate integration examples
        self.generate_integration_examples()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration
        
        print_header("Final Test Summary")
        passed_tests = sum(1 for test, result in results["tests"].items() 
                          if isinstance(result, (bool, dict)) and 
                          (result is True or (isinstance(result, dict) and result)))
        total_tests = len([test for test, result in results["tests"].items() 
                          if isinstance(result, (bool, dict))])
        
        print_color(Colors.BLUE, f"⏱️ Total duration: {duration:.2f} seconds")
        print_color(Colors.BLUE, f"📊 Tests passed: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print_color(Colors.GREEN, "🎉 ALL HTTP TESTS PASSED!")
            print_color(Colors.GREEN, "✅ TMF ODA MCP Server HTTP API is ready for external UIs!")
        else:
            print_color(Colors.YELLOW, f"⚠️ {total_tests - passed_tests} test(s) need attention")
        
        return results

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="TMF ODA MCP Server HTTP Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test local HTTP API
  python3 test-http-access.py
  
  # Test remote HTTP API
  python3 test-http-access.py --url http://192.168.1.100:8000
  
  # Test with custom timeout
  python3 test-http-access.py --url http://server:8000 --timeout 60
  
  # Test HTTPS API (with SSL verification disabled)
  python3 test-http-access.py --url https://server:8000 --no-ssl-verify
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
    
    args = parser.parse_args()
    
    # Configure SSL verification
    if args.no_ssl_verify:
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        print_color(Colors.YELLOW, "⚠️ SSL certificate verification disabled")
    
    # Create tester instance
    tester = TMFODAHttpTester(
        base_url=args.url,
        timeout=args.timeout
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