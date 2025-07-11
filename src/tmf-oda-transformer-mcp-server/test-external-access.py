#!/usr/bin/env python3
"""
External Test Script for TMF ODA Transformer MCP Server
This script tests all 6 tools as if called from an external UI/application.
Now supports remote Docker host connections.
"""

import asyncio
import json
import time
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import subprocess
import tempfile
import os
import socket

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

class MCPExternalTester:
    """External tester for TMF ODA MCP Server tools."""
    
    def __init__(self, container_name: str = "tmf-oda-mcp-server", 
                 remote_host: Optional[str] = None, 
                 remote_port: Optional[int] = None,
                 ssh_user: Optional[str] = None):
        self.container_name = container_name
        self.remote_host = remote_host
        self.remote_port = remote_port or 22
        self.ssh_user = ssh_user
        self.test_results = []
        self.start_time = None
        self.is_remote = bool(remote_host)
        
        # Build Docker connection command prefix
        if self.is_remote:
            if ssh_user:
                self.docker_prefix = ["ssh", f"{ssh_user}@{remote_host}", "-p", str(self.remote_port)]
            else:
                self.docker_prefix = ["ssh", remote_host, "-p", str(self.remote_port)]
        else:
            self.docker_prefix = []
            
        print_color(Colors.CYAN, f"🔗 Connection mode: {'Remote' if self.is_remote else 'Local'}")
        if self.is_remote:
            print_color(Colors.CYAN, f"🌐 Remote host: {remote_host}:{self.remote_port}")
            if ssh_user:
                print_color(Colors.CYAN, f"👤 SSH user: {ssh_user}")
    
    def test_network_connectivity(self) -> bool:
        """Test network connectivity to remote host."""
        if not self.is_remote:
            return True
            
        print_header("Network Connectivity Test")
        
        try:
            # Test basic connectivity
            print_color(Colors.BLUE, f"🔍 Testing connection to {self.remote_host}:{self.remote_port}...")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.remote_host, self.remote_port))
            sock.close()
            
            if result == 0:
                print_color(Colors.GREEN, "✅ Network connectivity OK")
                
                # Test SSH connection
                try:
                    ssh_cmd = self.docker_prefix + ["echo", "SSH test successful"]
                    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        print_color(Colors.GREEN, "✅ SSH connection working")
                        return True
                    else:
                        print_color(Colors.RED, f"❌ SSH connection failed: {result.stderr}")
                        return False
                except Exception as e:
                    print_color(Colors.RED, f"❌ SSH test failed: {e}")
                    return False
            else:
                print_color(Colors.RED, f"❌ Cannot connect to {self.remote_host}:{self.remote_port}")
                return False
                
        except Exception as e:
            print_color(Colors.RED, f"❌ Network connectivity test failed: {e}")
            return False
    
    def run_docker_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """Run a command inside the Docker container (local or remote)."""
        if self.is_remote:
            # For remote: ssh user@host "docker exec container command"
            docker_cmd = self.docker_prefix + [
                f"docker exec {self.container_name} bash -c '{command}'"
            ]
        else:
            # For local: docker exec container command
            docker_cmd = [
                "docker", "exec", self.container_name,
                "bash", "-c", command
            ]
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def run_docker_ps(self) -> Tuple[bool, str, str]:
        """Run docker ps command (local or remote)."""
        if self.is_remote:
            docker_cmd = self.docker_prefix + [
                f"docker ps -q -f name={self.container_name}"
            ]
        else:
            docker_cmd = ["docker", "ps", "-q", "-f", f"name={self.container_name}"]
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def test_container_status(self) -> bool:
        """Test if the container is running and accessible."""
        print_header("Container Status Check")
        
        # Check if container is running
        try:
            success, stdout, stderr = self.run_docker_ps()
            
            if not success:
                print_color(Colors.RED, f"❌ Failed to check container status: {stderr}")
                return False
            
            if not stdout.strip():
                print_color(Colors.RED, f"❌ Container '{self.container_name}' is not running")
                return False
            
            print_color(Colors.GREEN, f"✅ Container '{self.container_name}' is running")
            
            # Test basic connectivity
            success, stdout, stderr = self.run_docker_command("echo 'Connection test'")
            if success:
                print_color(Colors.GREEN, "✅ Container communication working")
                return True
            else:
                print_color(Colors.RED, f"❌ Container communication failed: {stderr}")
                return False
                
        except Exception as e:
            print_color(Colors.RED, f"❌ Error checking container: {e}")
            return False
    
    def test_python_environment(self) -> bool:
        """Test Python environment and dependencies."""
        print_header("Python Environment Test")
        
        tests = [
            ("Python version", "python --version"),
            ("Import awslabs.tmf_oda_transformer_mcp_server", 
             "python -c 'import awslabs.tmf_oda_transformer_mcp_server; print(\"✅ MCP server module imported\")'"),
            ("Import all tools", 
             '''python -c "
from awslabs.tmf_oda_transformer_mcp_server.server import (
    schema_analyzer_tool,
    db_analyzer_tool,
    raw_analysis_tool,
    stripped_schema_tool,
    get_job_logs_tool,
    test_runner_tool
)
print('✅ All 6 tools imported successfully')
"'''),
            ("Import models", 
             "python -c 'from awslabs.tmf_oda_transformer_mcp_server.models import TMFODAComponentType, DatabaseType; print(\"✅ Models imported\")'")
        ]
        
        all_passed = True
        for test_name, command in tests:
            success, stdout, stderr = self.run_docker_command(command)
            if success:
                print_color(Colors.GREEN, f"✅ {test_name}: {stdout.strip()}")
            else:
                print_color(Colors.RED, f"❌ {test_name}: {stderr.strip()}")
                all_passed = False
        
        return all_passed
    
    def test_tool_validation(self) -> Dict[str, Any]:
        """Test all tools with validation scenarios."""
        print_header("Tool Validation Tests")
        
        test_script = '''
import asyncio
import json
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import (
    schema_analyzer_tool,
    db_analyzer_tool,
    raw_analysis_tool,
    stripped_schema_tool,
    get_job_logs_tool,
    test_runner_tool
)
from awslabs.tmf_oda_transformer_mcp_server.models import TMFODAComponentType, DatabaseType

async def test_all_tools():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    
    results = {}
    
    # Test 1: Schema Analyzer
    try:
        await schema_analyzer_tool(
            ctx=ctx,
            workspace_dir="",
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            schema_format=None
        )
        results["schema_analyzer"] = "❌ Should have failed with empty workspace"
    except ValueError:
        results["schema_analyzer"] = "✅ Correctly validates empty workspace"
    except Exception as e:
        results["schema_analyzer"] = f"❌ Unexpected error: {e}"
    
    # Test 2: Database Analyzer
    try:
        await db_analyzer_tool(
            ctx=ctx,
            connection_string="",
            database_type=DatabaseType.POSTGRESQL,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            tables_filter=None
        )
        results["db_analyzer"] = "❌ Should have failed with empty connection"
    except ValueError:
        results["db_analyzer"] = "✅ Correctly validates empty connection"
    except Exception as e:
        results["db_analyzer"] = f"❌ Unexpected error: {e}"
    
    # Test 3: Raw Analysis
    try:
        await raw_analysis_tool(
            ctx=ctx,
            journey_id="",
            stage_id="raw_analysis",
            triggered_by="test",
            reason="test"
        )
        results["raw_analysis"] = "❌ Should have failed with empty journey ID"
    except ValueError:
        results["raw_analysis"] = "✅ Correctly validates empty journey ID"
    except Exception as e:
        results["raw_analysis"] = f"❌ Unexpected error: {e}"
    
    # Test 4: Stripped Schema
    try:
        await stripped_schema_tool(
            ctx=ctx,
            journey_id="",
            stage_id="stripped_schema",
            triggered_by="test",
            reason="test"
        )
        results["stripped_schema"] = "❌ Should have failed with empty journey ID"
    except ValueError:
        results["stripped_schema"] = "✅ Correctly validates empty journey ID"
    except Exception as e:
        results["stripped_schema"] = f"❌ Unexpected error: {e}"
    
    # Test 5: Get Job Logs
    try:
        await get_job_logs_tool(
            ctx=ctx,
            journey_id="",
            stage_name="raw_analysis",
            job_id="JOB-001-20240101120000",
            step_name="schema_parsing"
        )
        results["get_job_logs"] = "❌ Should have failed with empty journey ID"
    except ValueError:
        results["get_job_logs"] = "✅ Correctly validates empty journey ID"
    except Exception as e:
        results["get_job_logs"] = f"❌ Unexpected error: {e}"
    
            # Test 6: Test Runner (Quick mode)
        try:
            result = await test_runner_tool(
                ctx=ctx,
                test_type="quick",
                include_performance=False
            )
            if result.get("status") == "success":
                results["test_runner"] = f"✅ Test runner passed: {result.get('tests_passed', 0)}/{result.get('total_tests', 0)} tests"
            else:
                results["test_runner"] = f"⚠️ Test runner partial: {result.get('message', 'Unknown')}"
        except Exception as e:
            results["test_runner"] = f"❌ Test runner error: {e}"
        
        # Test 7: Journeys Tool (READ operation)
        try:
            result = await journeys_tool(
                ctx=ctx,
                action="read",
                journey_id=None,
                journey_data=None,
                stage_id=None,
                include_stages=True,
                include_job_history=True,
                job_limit=10
            )
            if result.get("status") == "success":
                journeys_count = len(result.get("journeys", []))
                results["journeys_read"] = f"✅ Journeys list retrieved: {journeys_count} journeys"
            else:
                results["journeys_read"] = f"⚠️ Journeys read partial: {result.get('message', 'Unknown')}"
        except Exception as e:
            results["journeys_read"] = f"❌ Journeys read error: {e}"
        
        # Test 8: Journeys Tool (CREATE operation)
        try:
            result = await journeys_tool(
                ctx=ctx,
                action="create",
                journey_id=None,
                journey_data={
                    "name": "External Test Journey",
                    "description": "Test journey created via external test",
                    "oda_component_type": "customer-management",
                    "priority": "low"
                },
                stage_id=None,
                include_stages=True,
                include_job_history=True,
                job_limit=10
            )
            if result.get("status") == "success":
                journey_id = result.get("journey_id", "Unknown")
                results["journeys_create"] = f"✅ Journey created: {journey_id}"
            else:
                results["journeys_create"] = f"⚠️ Journey creation partial: {result.get('message', 'Unknown')}"
        except Exception as e:
            results["journeys_create"] = f"❌ Journey creation error: {e}"
    
    print(json.dumps(results, indent=2))

asyncio.run(test_all_tools())
'''
        
        # Write test script to temporary file and execute
        success, stdout, stderr = self.run_docker_command(f"python -c '{test_script}'", timeout=60)
        
        if success:
            try:
                results = json.loads(stdout.strip())
                for tool, result in results.items():
                    if result.startswith("✅"):
                        print_color(Colors.GREEN, f"{tool}: {result}")
                    elif result.startswith("⚠️"):
                        print_color(Colors.YELLOW, f"{tool}: {result}")
                    else:
                        print_color(Colors.RED, f"{tool}: {result}")
                return results
            except json.JSONDecodeError:
                print_color(Colors.RED, f"❌ Failed to parse results: {stdout}")
                print_color(Colors.RED, f"Error: {stderr}")
                return {}
        else:
            print_color(Colors.RED, f"❌ Tool validation failed: {stderr}")
            return {}
    
    def test_comprehensive_workflow(self) -> bool:
        """Test a comprehensive workflow using multiple tools."""
        print_header("Comprehensive Workflow Test")
        
        workflow_script = '''
import asyncio
import json
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import test_runner_tool

async def run_comprehensive_test():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    
    try:
        result = await test_runner_tool(
            ctx=ctx,
            test_type="comprehensive",
            include_performance=True
        )
        
        print(json.dumps({
            "status": result.get("status"),
            "message": result.get("message"),
            "tests_passed": result.get("tests_passed", 0),
            "tests_failed": result.get("tests_failed", 0),
            "total_tests": result.get("total_tests", 0),
            "success_rate": result.get("success_rate", 0),
            "duration": result.get("duration_seconds", 0)
        }, indent=2))
        
        return result.get("status") == "success"
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return False

result = asyncio.run(run_comprehensive_test())
exit(0 if result else 1)
'''
        
        success, stdout, stderr = self.run_docker_command(f"python -c '{workflow_script}'", timeout=120)
        
        if success:
            try:
                results = json.loads(stdout.strip())
                print_color(Colors.GREEN, f"✅ Workflow Status: {results.get('status', 'unknown')}")
                print_color(Colors.BLUE, f"📊 Tests: {results.get('tests_passed', 0)}/{results.get('total_tests', 0)} passed")
                print_color(Colors.BLUE, f"📈 Success Rate: {results.get('success_rate', 0)}%")
                print_color(Colors.BLUE, f"⏱️ Duration: {results.get('duration', 0):.2f}s")
                return results.get('status') == 'success'
            except json.JSONDecodeError:
                print_color(Colors.YELLOW, f"⚠️ Workflow completed but results unparseable")
                print_color(Colors.BLUE, f"Output: {stdout}")
                return True
        else:
            print_color(Colors.RED, f"❌ Comprehensive workflow failed: {stderr}")
            return False
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance characteristics."""
        print_header("Performance Metrics Test")
        
        metrics = {}
        
        # Test 1: Import time
        start_time = time.time()
        success, stdout, stderr = self.run_docker_command(
            "python -c 'from awslabs.tmf_oda_transformer_mcp_server.server import *'"
        )
        import_time = time.time() - start_time
        
        if success:
            metrics["import_time"] = import_time
            print_color(Colors.GREEN, f"✅ Import time: {import_time:.3f}s")
        else:
            print_color(Colors.RED, f"❌ Import failed: {stderr}")
            metrics["import_time"] = None
        
        # Test 2: Quick test runner performance
        start_time = time.time()
        success, stdout, stderr = self.run_docker_command(
            '''python -c "
import asyncio
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import test_runner_tool

async def perf_test():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    result = await test_runner_tool(ctx, test_type='quick', include_performance=False)
    return result

asyncio.run(perf_test())
"''', timeout=60)
        test_runner_time = time.time() - start_time
        
        if success:
            metrics["test_runner_time"] = test_runner_time
            print_color(Colors.GREEN, f"✅ Test runner time: {test_runner_time:.3f}s")
        else:
            print_color(Colors.RED, f"❌ Test runner performance test failed: {stderr}")
            metrics["test_runner_time"] = None
        
        return metrics
    
    def generate_external_api_examples(self):
        """Generate examples for external API integration."""
        print_header("External API Integration Examples")
        
        print_color(Colors.CYAN, "🔌 For External UI Integration:")
        
        # Generate Docker command examples based on connection type
        if self.is_remote:
            docker_example = '''
# Remote Docker Connection Example:
import subprocess
import json

def call_tmf_oda_tool_remote(tool_name, parameters):
    \"\"\"Call TMF ODA tool from external application via remote Docker.\"\"\"
    
    script = f\"\"\"
import asyncio
import json
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import {tool_name}
from awslabs.tmf_oda_transformer_mcp_server.models import *

async def call_tool():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    
    try:
        result = await {tool_name}(ctx=ctx, **{parameters})
        print(json.dumps(result, default=str, indent=2))
        return True
    except Exception as e:
        print(json.dumps({{"error": str(e)}}, indent=2))
        return False

asyncio.run(call_tool())
\"\"\"
    
    # For remote connection
    cmd = ["ssh", "user@remote_host", "-p", "22",
           f"docker exec container_name python -c '{script}'"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr

# Example usage:
# result, error = call_tmf_oda_tool_remote("test_runner_tool", {"test_type": "quick"})
'''
        else:
            docker_example = '''
# Local Docker Connection Example:
import subprocess
import json

def call_tmf_oda_tool(tool_name, parameters):
    \"\"\"Call TMF ODA tool from external application.\"\"\"
    
    script = f\"\"\"
import asyncio
import json
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import {tool_name}
from awslabs.tmf_oda_transformer_mcp_server.models import *

async def call_tool():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    
    try:
        result = await {tool_name}(ctx=ctx, **{parameters})
        print(json.dumps(result, default=str, indent=2))
        return True
    except Exception as e:
        print(json.dumps({{"error": str(e)}}, indent=2))
        return False

asyncio.run(call_tool())
\"\"\"
    
    cmd = ["docker", "exec", "tmf-oda-mcp-server", "python", "-c", script]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr

# Example usage:
# result, error = call_tmf_oda_tool("test_runner_tool", {"test_type": "quick"})
'''
        
        print_color(Colors.BLUE, docker_example)
        
        print_color(Colors.CYAN, "\n🌐 REST API Wrapper Example:")
        print_color(Colors.BLUE, f'''
# Flask/FastAPI wrapper for HTTP access:
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/tmf-oda/<tool_name>', methods=['POST'])
def call_tmf_tool(tool_name):
    try:
        parameters = request.json
        result, error = call_tmf_oda_tool{"_remote" if self.is_remote else ""}(tool_name, parameters)
        
        if error:
            return jsonify({{"error": error}}), 500
        
        return jsonify({{"result": json.loads(result)}}), 200
        
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
''')
        
        print_color(Colors.CYAN, "\n🚀 Usage Instructions:")
        if self.is_remote:
            print_color(Colors.BLUE, f"""
To run this script from another machine:
1. Ensure SSH access to {self.remote_host}
2. Run: python3 test-external-access.py --host {self.remote_host} --port {self.remote_port}
3. Add --user <username> if different SSH user needed
4. Make sure Docker is running on the remote host
""")
        else:
            print_color(Colors.BLUE, """
To run this script locally:
1. Ensure Docker is running
2. Run: python3 test-external-access.py
3. Container will be accessed directly
""")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all external tests."""
        self.start_time = datetime.now()
        
        print_color(Colors.GREEN, "🚀 TMF ODA Transformer MCP Server - External Testing Suite")
        print_color(Colors.GREEN, "="*70)
        print_color(Colors.BLUE, f"🕐 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            "start_time": self.start_time.isoformat(),
            "connection_type": "remote" if self.is_remote else "local",
            "remote_host": self.remote_host,
            "remote_port": self.remote_port,
            "tests": {}
        }
        
        # Test 0: Network connectivity (for remote connections)
        if self.is_remote:
            results["tests"]["network_connectivity"] = self.test_network_connectivity()
            if not results["tests"]["network_connectivity"]:
                print_color(Colors.RED, "❌ Network connectivity failed. Cannot proceed with tests.")
                return results
        
        # Test 1: Container Status
        results["tests"]["container_status"] = self.test_container_status()
        
        if not results["tests"]["container_status"]:
            print_color(Colors.RED, "❌ Container tests failed. Cannot proceed with tool tests.")
            return results
        
        # Test 2: Python Environment
        results["tests"]["python_environment"] = self.test_python_environment()
        
        # Test 3: Tool Validation
        results["tests"]["tool_validation"] = self.test_tool_validation()
        
        # Test 4: Comprehensive Workflow
        results["tests"]["comprehensive_workflow"] = self.test_comprehensive_workflow()
        
        # Test 5: Performance Metrics
        results["tests"]["performance_metrics"] = self.test_performance_metrics()
        
        # Generate examples
        self.generate_external_api_examples()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration
        
        print_header("Final Test Summary")
        passed_tests = sum(1 for test, result in results["tests"].items() 
                          if isinstance(result, bool) and result)
        total_tests = len([test for test, result in results["tests"].items() 
                          if isinstance(result, bool)])
        
        print_color(Colors.BLUE, f"⏱️ Total duration: {duration:.2f} seconds")
        print_color(Colors.BLUE, f"📊 Tests passed: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print_color(Colors.GREEN, "🎉 ALL EXTERNAL TESTS PASSED!")
            print_color(Colors.GREEN, "✅ TMF ODA MCP Server is ready for external UI integration!")
        else:
            print_color(Colors.YELLOW, f"⚠️ {total_tests - passed_tests} test(s) need attention")
        
        return results

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="TMF ODA MCP Server External Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test local Docker container
  python3 test-external-access.py
  
  # Test remote Docker container
  python3 test-external-access.py --host 192.168.1.100
  
  # Test with specific SSH port and user
  python3 test-external-access.py --host 192.168.1.100 --port 2222 --user myuser
  
  # Test specific container name
  python3 test-external-access.py --container my-tmf-container
"""
    )
    
    parser.add_argument(
        "--host",
        type=str,
        help="Remote host IP or hostname (if not provided, uses local Docker)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=22,
        help="SSH port for remote connection (default: 22)"
    )
    
    parser.add_argument(
        "--user",
        type=str,
        help="SSH username for remote connection (default: current user)"
    )
    
    parser.add_argument(
        "--container",
        type=str,
        default="tmf-oda-mcp-server",
        help="Docker container name (default: tmf-oda-mcp-server)"
    )
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = MCPExternalTester(
        container_name=args.container,
        remote_host=args.host,
        remote_port=args.port,
        ssh_user=args.user
    )
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Save results to file
    results_filename = f"external_test_results_{'remote' if args.host else 'local'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_filename, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print_color(Colors.BLUE, f"\n📁 Results saved to: {results_filename}")
    
    # Exit with appropriate code
    passed_tests = sum(1 for test, result in results["tests"].items() 
                      if isinstance(result, bool) and result)
    total_tests = len([test for test, result in results["tests"].items() 
                      if isinstance(result, bool)])
    
    sys.exit(0 if passed_tests == total_tests else 1)

if __name__ == "__main__":
    main() 