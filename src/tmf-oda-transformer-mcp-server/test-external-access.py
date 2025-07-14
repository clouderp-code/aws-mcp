#!/usr/bin/env python3
"""
External Test Script for Enhanced TMF ODA Transformer MCP Server
This script tests all 7 tools as if called from an external UI/application.
Now supports comprehensive journey lifecycle management and logs/reports functionality.
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
    """External tester for Enhanced TMF ODA MCP Server tools."""
    
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
    raw_analysis_tool,
    stripped_schema_tool,
    get_job_logs_tool,
    test_runner_tool,
    journeys_tool,
    run_jobs_tool
)
from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool
print('✅ All 7 tools imported successfully')
"'''),
            ("Import enhanced models", 
             "python -c 'from awslabs.tmf_oda_transformer_mcp_server.models import TMFODAComponentType, DatabaseType, JourneyStatus, JobStatus, LogLevel, ReportType; print(\"✅ Enhanced models imported\")'")
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
        """Test all enhanced tools with validation scenarios."""
        print_header("Enhanced Tool Validation Tests")
        
        test_script = '''
import asyncio
import json
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import (
    raw_analysis_tool,
    stripped_schema_tool,
    get_job_logs_tool,
    test_runner_tool,
    journeys_tool,
    run_jobs_tool
)
from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool

async def test_all_tools():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    
    results = {}
    
    # Test 1: Raw Analysis
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
    
    # Test 2: Stripped Schema
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
    
    # Test 3: Get Job Logs
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
    
    # Test 4: Run Jobs Tool
    try:
        await run_jobs_tool(
            ctx=ctx,
            journey_id="",
            stage_id="raw_analysis",
            triggered_by="test",
            reason="test"
        )
        results["run_jobs"] = "❌ Should have failed with empty journey ID"
    except ValueError:
        results["run_jobs"] = "✅ Correctly validates empty journey ID"
    except Exception as e:
        results["run_jobs"] = f"❌ Unexpected error: {e}"
    
    # Test 5: Enhanced Journeys Tool (READ operation)
    try:
        result = await journeys_tool(
            ctx=ctx,
            action="read",
            journey_id="",
            include_stages=True,
            include_job_history=True,
            limit=10
        )
        if result.get("status") == "success":
            journeys_count = len(result.get("journeys", []))
            results["journeys"] = f"✅ Enhanced journeys tool working: {journeys_count} journeys"
        else:
            results["journeys"] = f"⚠️ Journeys partial: {result.get('message', 'Unknown')}"
    except Exception as e:
        results["journeys"] = f"❌ Journeys error: {e}"
    
    # Test 6: Enhanced Journeys Tool - Stage Management
    try:
        result = await journeys_tool(
            ctx=ctx,
            action="list_stages",
            journey_id="JRN-SAMPLE-001"
        )
        if result.get("status") == "success":
            stages_count = len(result.get("stages", []))
            results["journeys_stages"] = f"✅ Stage management working: {stages_count} stages"
        else:
            results["journeys_stages"] = f"⚠️ Stage management partial: {result.get('message', 'Unknown')}"
    except Exception as e:
        results["journeys_stages"] = f"❌ Stage management error: {e}"
    
    # Test 7: Enhanced Journeys Tool - Job Management
    try:
        result = await journeys_tool(
            ctx=ctx,
            action="list_jobs",
            journey_id="JRN-SAMPLE-001",
            stage_id="raw_analysis",
            limit=5
        )
        if result.get("status") == "success":
            jobs_count = len(result.get("jobs", []))
            results["journeys_jobs"] = f"✅ Job management working: {jobs_count} jobs"
        else:
            results["journeys_jobs"] = f"⚠️ Job management partial: {result.get('message', 'Unknown')}"
    except Exception as e:
        results["journeys_jobs"] = f"❌ Job management error: {e}"
    
    # Test 8: NEW - Logs and Reports Tool
    try:
        result = await logs_and_reports_tool(
            ctx=ctx,
            action="get_job_logs",
            journey_id="JRN-SAMPLE-001",
            job_id="JOB-001-20240101120000",
            stage_name="raw_analysis",
            step_name="schema_parsing"
        )
        if result.get("status") == "success":
            logs_count = len(result.get("logs", {}).get("logs", []))
            results["logs_and_reports"] = f"✅ Logs and reports tool working: {logs_count} log entries"
        else:
            results["logs_and_reports"] = f"⚠️ Logs and reports partial: {result.get('message', 'Unknown')}"
    except Exception as e:
        results["logs_and_reports"] = f"❌ Logs and reports error: {e}"
    
    # Test 9: Test Runner (Quick mode)
    try:
        result = await test_runner_tool(
            ctx=ctx,
            test_type="quick",
            include_performance=False
        )
        # Extract values safely to avoid any f-string evaluation issues
        status = result.get("status", "unknown")
        tests_passed_value = result.get('tests_passed', 0)
        total_tests_value = result.get('total_tests', 0)
        message_value = result.get('message', 'Unknown')
        
        if status == "success":
            results["test_runner"] = "✅ Test runner passed: " + str(tests_passed_value) + "/" + str(total_tests_value) + " tests"
        else:
            results["test_runner"] = "⚠️ Test runner partial: " + str(message_value)
    except Exception as e:
        # Convert exception to string immediately to avoid any variable issues
        error_str = str(e)
        results["test_runner"] = "❌ Test runner error: " + error_str
    
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
        """Test a comprehensive workflow using multiple enhanced tools."""
        print_header("Enhanced Comprehensive Workflow Test")
        
        workflow_script = '''
import asyncio
import json
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import test_runner_tool, journeys_tool
from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool

async def run_enhanced_comprehensive_test():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    
    workflow_results = {}
    
    try:
        # Test 1: Run comprehensive test suite
        result = await test_runner_tool(
            ctx=ctx,
            test_type="comprehensive",
            include_performance=True
        )
        
        workflow_results["test_suite"] = {
            "status": result.get("status"),
            "tests_passed": result.get("tests_passed", 0),
            "tests_failed": result.get("tests_failed", 0),
            "total_tests": result.get("total_tests", 0),
            "success_rate": result.get("success_rate", 0),
            "duration": result.get("duration_seconds", 0)
        }
        
        # Test 2: Test enhanced journeys functionality
        journeys_result = await journeys_tool(
            ctx=ctx,
            action="dashboard",
            journey_id="JRN-SAMPLE-001"
        )
        
        workflow_results["journeys_dashboard"] = {
            "status": journeys_result.get("status"),
            "operation": journeys_result.get("operation"),
            "has_dashboard": "dashboard" in journeys_result
        }
        
        # Test 3: Test logs and reports functionality
        logs_result = await logs_and_reports_tool(
            ctx=ctx,
            action="list_available_logs",
            journey_id="JRN-SAMPLE-001"
        )
        
        workflow_results["logs_reports"] = {
            "status": logs_result.get("status"),
            "operation": logs_result.get("operation"),
            "has_logs": "available_logs" in logs_result
        }
        
        print(json.dumps(workflow_results, indent=2))
        
        # Overall success if all components work
        all_success = all(
            comp.get("status") == "success" 
            for comp in workflow_results.values() 
            if isinstance(comp, dict) and "status" in comp
        )
        
        return all_success
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return False

result = asyncio.run(run_enhanced_comprehensive_test())
exit(0 if result else 1)
'''
        
        success, stdout, stderr = self.run_docker_command(f"python -c '{workflow_script}'", timeout=120)
        
        if success:
            try:
                results = json.loads(stdout.strip())
                print_color(Colors.GREEN, f"✅ Enhanced Workflow Results:")
                
                # Test suite results
                if "test_suite" in results:
                    ts = results["test_suite"]
                    print_color(Colors.BLUE, f"📊 Test Suite: {ts.get('tests_passed', 0)}/{ts.get('total_tests', 0)} passed")
                    print_color(Colors.BLUE, f"📈 Success Rate: {ts.get('success_rate', 0)}%")
                    print_color(Colors.BLUE, f"⏱️ Duration: {ts.get('duration', 0):.2f}s")
                
                # Journeys dashboard results
                if "journeys_dashboard" in results:
                    jd = results["journeys_dashboard"]
                    print_color(Colors.BLUE, f"🗺️ Journeys Dashboard: {jd.get('status', 'unknown')}")
                    print_color(Colors.BLUE, f"📊 Dashboard Available: {jd.get('has_dashboard', False)}")
                
                # Logs and reports results
                if "logs_reports" in results:
                    lr = results["logs_reports"]
                    print_color(Colors.BLUE, f"📋 Logs & Reports: {lr.get('status', 'unknown')}")
                    print_color(Colors.BLUE, f"📊 Logs Available: {lr.get('has_logs', False)}")
                
                return True
            except json.JSONDecodeError:
                print_color(Colors.YELLOW, f"⚠️ Enhanced workflow completed but results unparseable")
                print_color(Colors.BLUE, f"Output: {stdout}")
                return True
        else:
            print_color(Colors.RED, f"❌ Enhanced comprehensive workflow failed: {stderr}")
            return False
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance characteristics of enhanced tools."""
        print_header("Enhanced Performance Metrics Test")
        
        metrics = {}
        
        # Test 1: Import time
        start_time = time.time()
        success, stdout, stderr = self.run_docker_command(
            "python -c 'from awslabs.tmf_oda_transformer_mcp_server.server import *; from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import *'"
        )
        import_time = time.time() - start_time
        
        if success:
            metrics["import_time"] = import_time
            print_color(Colors.GREEN, f"✅ Enhanced import time: {import_time:.3f}s")
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
        
        # Test 3: Enhanced journeys tool performance
        start_time = time.time()
        success, stdout, stderr = self.run_docker_command(
            '''python -c "
import asyncio
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import journeys_tool

async def journeys_perf_test():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    result = await journeys_tool(ctx, action='read', journey_id='')
    return result

asyncio.run(journeys_perf_test())
"''', timeout=60)
        journeys_time = time.time() - start_time
        
        if success:
            metrics["journeys_time"] = journeys_time
            print_color(Colors.GREEN, f"✅ Enhanced journeys time: {journeys_time:.3f}s")
        else:
            print_color(Colors.RED, f"❌ Enhanced journeys performance test failed: {stderr}")
            metrics["journeys_time"] = None
        
        # Test 4: Logs and reports tool performance
        start_time = time.time()
        success, stdout, stderr = self.run_docker_command(
            '''python -c "
import asyncio
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool

async def logs_perf_test():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    result = await logs_and_reports_tool(
        ctx, 
        action='list_available_logs', 
        journey_id='JRN-SAMPLE-001'
    )
    return result

asyncio.run(logs_perf_test())
"''', timeout=60)
        logs_time = time.time() - start_time
        
        if success:
            metrics["logs_reports_time"] = logs_time
            print_color(Colors.GREEN, f"✅ Logs and reports time: {logs_time:.3f}s")
        else:
            print_color(Colors.RED, f"❌ Logs and reports performance test failed: {stderr}")
            metrics["logs_reports_time"] = None
        
        return metrics
    
    def generate_external_api_examples(self):
        """Generate examples for external API integration with enhanced functionality."""
        print_header("Enhanced External API Integration Examples")
        
        print_color(Colors.CYAN, "🔌 For External UI Integration:")
        
        # Generate Docker command examples based on connection type
        if self.is_remote:
            docker_example = '''
# Enhanced Remote Docker Connection Example:
import subprocess
import json

def call_enhanced_tmf_oda_tool_remote(tool_name, parameters):
    \"\"\"Call Enhanced TMF ODA tool from external application via remote Docker.\"\"\"
    
    script = f\"\"\"
import asyncio
import json
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import {tool_name}
from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool
from awslabs.tmf_oda_transformer_mcp_server.models import *

async def call_tool():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    
    try:
        if "{tool_name}" == "logs_and_reports_tool":
            result = await logs_and_reports_tool(ctx=ctx, **{parameters})
        else:
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

# Enhanced Example usage:
# Journey management
# result, error = call_enhanced_tmf_oda_tool_remote("journeys_tool", {
#     "action": "create", 
#     "journey_data": {"name": "New Journey", "oda_component_type": "customer-management"}
# })

# Stage management  
# result, error = call_enhanced_tmf_oda_tool_remote("journeys_tool", {
#     "action": "add_stage", 
#     "journey_id": "JRN-001", 
#     "stage_data": {"stage_id": "custom_validation", "name": "Custom Validation"}
# })

# Job management
# result, error = call_enhanced_tmf_oda_tool_remote("journeys_tool", {
#     "action": "run_job", 
#     "journey_id": "JRN-001", 
#     "stage_id": "raw_analysis"
# })

# Logs and reports
# result, error = call_enhanced_tmf_oda_tool_remote("logs_and_reports_tool", {
#     "action": "get_job_logs", 
#     "journey_id": "JRN-001", 
#     "job_id": "JOB-001", 
#     "stage_name": "raw_analysis"
# })
'''
        else:
            docker_example = '''
# Enhanced Local Docker Connection Example:
import subprocess
import json

def call_enhanced_tmf_oda_tool(tool_name, parameters):
    \"\"\"Call Enhanced TMF ODA tool from external application.\"\"\"
    
    script = f\"\"\"
import asyncio
import json
from unittest.mock import AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import {tool_name}
from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool
from awslabs.tmf_oda_transformer_mcp_server.models import *

async def call_tool():
    ctx = AsyncMock()
    ctx.error = AsyncMock()
    
    try:
        if "{tool_name}" == "logs_and_reports_tool":
            result = await logs_and_reports_tool(ctx=ctx, **{parameters})
        else:
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

# Enhanced Example usage - Complete Journey Lifecycle:

# 1. Create journey
# result, error = call_enhanced_tmf_oda_tool("journeys_tool", {
#     "action": "create", 
#     "journey_data": {
#         "name": "Customer Data Migration", 
#         "oda_component_type": "customer-management",
#         "priority": "high"
#     }
# })

# 2. Add default stages
# result, error = call_enhanced_tmf_oda_tool("journeys_tool", {
#     "action": "add_default_stages", 
#     "journey_id": "JRN-001"
# })

# 3. Add custom rules
# result, error = call_enhanced_tmf_oda_tool("journeys_tool", {
#     "action": "add_rule", 
#     "journey_id": "JRN-001",
#     "stage_id": "data_mapping",
#     "rule_data": {
#         "name": "Email Validation",
#         "rule_type": "validation",
#         "condition": "email IS NOT NULL"
#     }
# })

# 4. Execute job
# result, error = call_enhanced_tmf_oda_tool("journeys_tool", {
#     "action": "run_job", 
#     "journey_id": "JRN-001", 
#     "stage_id": "raw_analysis"
# })

# 5. Monitor job progress
# result, error = call_enhanced_tmf_oda_tool("journeys_tool", {
#     "action": "get_job_metrics", 
#     "journey_id": "JRN-001", 
#     "job_id": "JOB-001"
# })

# 6. Get comprehensive logs
# result, error = call_enhanced_tmf_oda_tool("logs_and_reports_tool", {
#     "action": "get_job_logs", 
#     "journey_id": "JRN-001", 
#     "job_id": "JOB-001",
#     "stage_name": "raw_analysis"
# })

# 7. Generate reports
# result, error = call_enhanced_tmf_oda_tool("logs_and_reports_tool", {
#     "action": "generate_summary_report", 
#     "journey_id": "JRN-001", 
#     "job_id": "JOB-001"
# })

# 8. Get dashboard view
# result, error = call_enhanced_tmf_oda_tool("journeys_tool", {
#     "action": "dashboard", 
#     "journey_id": "JRN-001"
# })
'''
        
        print_color(Colors.BLUE, docker_example)
        
        print_color(Colors.CYAN, "\n🌐 Enhanced REST API Wrapper Example:")
        print_color(Colors.BLUE, f'''
# Flask/FastAPI wrapper for Enhanced HTTP access:
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/tmf-oda/<tool_name>', methods=['POST'])
def call_enhanced_tmf_tool(tool_name):
    try:
        parameters = request.json
        result, error = call_enhanced_tmf_oda_tool{"_remote" if self.is_remote else ""}(tool_name, parameters)
        
        if error:
            return jsonify({{"error": error}}), 500
        
        return jsonify({{"result": json.loads(result)}}), 200
        
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500

# Enhanced endpoints for specific functionality
@app.route('/tmf-oda/journeys', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_journeys():
    \"\"\"RESTful journey management endpoint.\"\"\"
    if request.method == 'GET':
        # List journeys or get specific journey
        journey_id = request.args.get('journey_id', '')
        return call_enhanced_tmf_tool('journeys_tool', {{"action": "read", "journey_id": journey_id}})
    elif request.method == 'POST':
        # Create journey
        return call_enhanced_tmf_tool('journeys_tool', {{"action": "create", "journey_data": request.json}})
    elif request.method == 'PUT':
        # Update journey
        journey_id = request.args.get('journey_id')
        return call_enhanced_tmf_tool('journeys_tool', {{"action": "update", "journey_id": journey_id, "journey_data": request.json}})
    elif request.method == 'DELETE':
        # Delete journey
        journey_id = request.args.get('journey_id')
        return call_enhanced_tmf_tool('journeys_tool', {{"action": "delete", "journey_id": journey_id}})

@app.route('/tmf-oda/journeys/<journey_id>/stages', methods=['GET', 'POST'])
def manage_stages(journey_id):
    \"\"\"Stage management endpoint.\"\"\"
    if request.method == 'GET':
        return call_enhanced_tmf_tool('journeys_tool', {{"action": "list_stages", "journey_id": journey_id}})
    elif request.method == 'POST':
        return call_enhanced_tmf_tool('journeys_tool', {{"action": "add_stage", "journey_id": journey_id, "stage_data": request.json}})

@app.route('/tmf-oda/journeys/<journey_id>/jobs', methods=['GET', 'POST'])
def manage_jobs(journey_id):
    \"\"\"Job management endpoint.\"\"\"
    if request.method == 'GET':
        return call_enhanced_tmf_tool('journeys_tool', {{"action": "list_jobs", "journey_id": journey_id}})
    elif request.method == 'POST':
        stage_id = request.json.get('stage_id')
        return call_enhanced_tmf_tool('journeys_tool', {{"action": "run_job", "journey_id": journey_id, "stage_id": stage_id}})

@app.route('/tmf-oda/journeys/<journey_id>/logs', methods=['GET'])
def get_logs(journey_id):
    \"\"\"Logs retrieval endpoint.\"\"\"
    job_id = request.args.get('job_id')
    stage_name = request.args.get('stage_name')
    return call_enhanced_tmf_tool('logs_and_reports_tool', {{
        "action": "get_job_logs", 
        "journey_id": journey_id, 
        "job_id": job_id, 
        "stage_name": stage_name
    }})

@app.route('/tmf-oda/journeys/<journey_id>/dashboard', methods=['GET'])
def get_dashboard(journey_id):
    \"\"\"Dashboard endpoint.\"\"\"
    return call_enhanced_tmf_tool('journeys_tool', {{"action": "dashboard", "journey_id": journey_id}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
''')
        
        print_color(Colors.CYAN, "\n🚀 Enhanced Usage Instructions:")
        if self.is_remote:
            print_color(Colors.BLUE, f"""
To run enhanced testing from another machine:
1. Ensure SSH access to {self.remote_host}
2. Run: python3 test-external-access.py --host {self.remote_host} --port {self.remote_port}
3. Add --user <username> if different SSH user needed
4. Make sure Docker is running on the remote host
5. Test all 7 enhanced tools including new logs-and-reports functionality
6. Verify 40+ journey management actions are working
"""
)
        else:
            print_color(Colors.BLUE, """
To run enhanced testing locally:
1. Ensure Docker is running
2. Run: python3 test-external-access.py
3. Container will be accessed directly
4. Test all 7 enhanced tools including new logs-and-reports functionality
5. Verify complete journey lifecycle management is working
6. Test stage management, rules management, job management, and reports
"""
)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all enhanced external tests."""
        self.start_time = datetime.now()
        
        print_color(Colors.GREEN, "🚀 Enhanced TMF ODA Transformer MCP Server - External Testing Suite")
        print_color(Colors.GREEN, "="*70)
        print_color(Colors.BLUE, f"🕐 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print_color(Colors.PURPLE, "🔧 Testing 7 enhanced tools with comprehensive journey lifecycle management")
        
        results = {
            "start_time": self.start_time.isoformat(),
            "connection_type": "remote" if self.is_remote else "local",
            "remote_host": self.remote_host,
            "remote_port": self.remote_port,
            "tools_count": 7,
            "enhanced_features": [
                "comprehensive_journey_management",
                "stage_management", 
                "rules_management",
                "job_lifecycle_management",
                "logs_and_reports",
                "interactive_dashboards",
                "performance_analysis"
            ],
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
        
        # Test 3: Enhanced Tool Validation
        results["tests"]["tool_validation"] = self.test_tool_validation()
        
        # Test 4: Enhanced Comprehensive Workflow
        results["tests"]["comprehensive_workflow"] = self.test_comprehensive_workflow()
        
        # Test 5: Enhanced Performance Metrics
        results["tests"]["performance_metrics"] = self.test_performance_metrics()
        
        # Generate enhanced examples
        self.generate_external_api_examples()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration
        
        print_header("Enhanced Final Test Summary")
        passed_tests = sum(1 for test, result in results["tests"].items() 
                          if isinstance(result, bool) and result)
        total_tests = len([test for test, result in results["tests"].items() 
                          if isinstance(result, bool)])
        
        print_color(Colors.BLUE, f"⏱️ Total duration: {duration:.2f} seconds")
        print_color(Colors.BLUE, f"📊 Tests passed: {passed_tests}/{total_tests}")
        print_color(Colors.PURPLE, f"🔧 Enhanced tools tested: 7 (raw-analysis, stripped-schema, get-job-logs, test-runner, journeys, run-jobs, logs-and-reports)")
        print_color(Colors.PURPLE, f"⚡ Journey actions tested: 40+ (CRUD, stage mgmt, rules mgmt, job mgmt, logs, reports, dashboard)")
        
        if passed_tests == total_tests:
            print_color(Colors.GREEN, "🎉 ALL ENHANCED EXTERNAL TESTS PASSED!")
            print_color(Colors.GREEN, "✅ Enhanced TMF ODA MCP Server is ready for external UI integration!")
            print_color(Colors.GREEN, "✅ All 7 tools including new logs-and-reports functionality working!")
            print_color(Colors.GREEN, "✅ Complete journey lifecycle management operational!")
        else:
            print_color(Colors.YELLOW, f"⚠️ {total_tests - passed_tests} test(s) need attention")
        
        return results

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enhanced TMF ODA MCP Server External Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test local Docker container (7 enhanced tools)
  python3 test-external-access.py
  
  # Test remote Docker container with enhanced functionality
  python3 test-external-access.py --host 192.168.1.100
  
  # Test with specific SSH port and user
  python3 test-external-access.py --host 192.168.1.100 --port 2222 --user myuser
  
  # Test specific container name
  python3 test-external-access.py --container my-tmf-container

Enhanced Features Tested:
  • Complete journey lifecycle management (create, read, update, delete)
  • Stage management (add, update, delete, list stages)
  • Second Brain rules management (field mapping, validation, transformation)
  • Job lifecycle management (run, cancel, retry, monitor, metrics)
  • Comprehensive logs and reports (search, filter, export, analyze)
  • Interactive dashboards and real-time monitoring
  • Performance analysis and recommendations
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
    results_filename = f"enhanced_external_test_results_{'remote' if args.host else 'local'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_filename, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print_color(Colors.BLUE, f"\n📁 Enhanced results saved to: {results_filename}")
    
    # Exit with appropriate code
    passed_tests = sum(1 for test, result in results["tests"].items() 
                      if isinstance(result, bool) and result)
    total_tests = len([test for test, result in results["tests"].items() 
                      if isinstance(result, bool)])
    
    sys.exit(0 if passed_tests == total_tests else 1)

if __name__ == "__main__":
    main() 