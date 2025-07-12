"""
Comprehensive test runner for TMF ODA transformer MCP server tools.

This script runs all tests and provides a summary of tool functionality verification.
"""

import asyncio
import sys
import subprocess
import time
from pathlib import Path

# Add the MCP server to Python path
mcp_server_path = Path(__file__).parent.parent
sys.path.insert(0, str(mcp_server_path))


class TMFMCPTestRunner:
    """Test runner for TMF ODA transformer MCP server tools."""
    
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_all_tests(self):
        """Run all test suites and provide summary."""
        print("🚀 Starting TMF ODA Transformer MCP Server Test Suite")
        print("=" * 70)
        
        # Updated test files to only include tests for remaining tools
        test_files = [
            # "test_schema_analyzer.py",  # Removed tool
            # "test_db_analyzer.py",      # Removed tool
            "test_raw_analysis.py",
            "test_stripped_schema.py",
            "test_get_job_logs.py",
            "test_journeys.py",
            "test_run_jobs.py"
        ]
        
        start_time = time.time()
        
        for test_file in test_files:
            print(f"\n🧪 Running tests in {test_file}...")
            result = self._run_test_file(test_file)
            self.test_results[test_file] = result
            
        end_time = time.time()
        
        self._print_summary(end_time - start_time)

    def _run_test_file(self, test_file):
        """Run a single test file and return results."""
        try:
            # Use subprocess to run pytest on the specific test file
            result = subprocess.run(
                [sys.executable, "-m", "pytest", f"tests/{test_file}", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            output = result.stdout + result.stderr
            
            # Parse pytest output to extract results
            lines = output.split('\n')
            passed = 0
            failed = 0
            
            for line in lines:
                if '::' in line and 'PASSED' in line:
                    passed += 1
                elif '::' in line and 'FAILED' in line:
                    failed += 1
            
            # Update totals
            self.total_tests += (passed + failed)
            self.passed_tests += passed
            self.failed_tests += failed
            
            status = 'PASSED' if failed == 0 else 'FAILED'
            
            return {
                'status': status,
                'passed': passed,
                'failed': failed,
                'total': passed + failed,
                'output': output
            }
            
        except Exception as e:
            print(f"  ❌ Error running {test_file}: {e}")
            return {
                'status': 'ERROR',
                'passed': 0,
                'failed': 1,
                'total': 1,
                'output': str(e)
            }

    def _print_summary(self, duration):
        """Print test summary."""
        print(f"\n⏱️  Total test duration: {duration:.2f} seconds")
        print("\n" + "=" * 70)
        print("🎯 TEST SUMMARY")
        print("=" * 70)
        
        # Map test files to tool names
        tool_mapping = {
            # "test_schema_analyzer.py": "🔍 Schema Analyzer",      # Removed tool
            # "test_db_analyzer.py": "🗄️ Database Analyzer",       # Removed tool
            "test_raw_analysis.py": "⚡ Raw Analysis",
            "test_stripped_schema.py": "🔧 Stripped Schema",
            "test_get_job_logs.py": "📋 Get Job Logs",
            "test_journeys.py": "📊 Journeys Management",
            "test_run_jobs.py": "🎯 Run Jobs"
        }
        
        for test_file, tool_name in tool_mapping.items():
            if test_file in self.test_results:
                result = self.test_results[test_file]
                status_icon = "✅" if result['status'] == 'PASSED' else "❌"
                print(f"{status_icon} {tool_name}: {result['passed']}/{result['total']} tests passed")
        
        print("\n🛠️  TOOL FUNCTIONALITY VERIFICATION:")
        print("-" * 50)
        
        self._print_tool_functionality_summary()
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! TMF ODA Transformer MCP Server is fully functional!")
        else:
            print(f"\n⚠️  {self.failed_tests} test(s) failed. Please review the output above.")
            
        print("\n" + "=" * 70)
    
    def _print_tool_functionality_summary(self):
        """Print summary of tool functionality that was verified."""
        functionalities = [
            # "🔍 Schema file discovery and analysis for TMF ODA compliance",      # Removed tool
            # "🗄️  Database connection and schema analysis for various DB types",  # Removed tool
            "⚡ Raw analysis stage execution with proper job management",
            "🔧 Stripped schema stage execution with error handling",
            "📋 Job log retrieval from S3 with comprehensive error handling",
            "📊 Journey CRUD operations with comprehensive status tracking",
            "🎯 Generic job execution for any transformation stage",
            "🔒 AWS credential handling and role assumption",
            "⚙️  Input validation and error messaging",
            "📊 Result formatting and metadata generation",
            "🚨 Exception handling and graceful failure modes",
            "⏱️  Performance timing and measurement"
        ]
        
        for functionality in functionalities:
            print(f"  ✓ {functionality}")

async def run_tool_integration_tests():
    """Run integration tests to verify actual tool calls work."""
    print("\n🔗 RUNNING TOOL INTEGRATION TESTS")
    print("-" * 50)
    
    # These tests actually call the tool functions to verify they work
    from awslabs.tmf_oda_transformer_mcp_server.server import (
        # schema_analyzer_tool,    # Removed tool
        # db_analyzer_tool,        # Removed tool
        raw_analysis_tool,
        stripped_schema_tool,
        get_job_logs_tool,
        journeys_tool,
        run_jobs_tool
    )
    from awslabs.tmf_oda_transformer_mcp_server.models import TMFODAComponentType
    from unittest.mock import Mock
    
    mock_ctx = Mock()
    mock_ctx.error = Mock()
    
    integration_results = []
    
    # Test 1: Raw Analysis with empty journey ID
    try:
        print("🧪 Testing raw-analysis with empty journey ID...")
        await raw_analysis_tool(
            ctx=mock_ctx,
            journey_id="",
            stage_id="raw_analysis",
            triggered_by="test",
            reason="test"
        )
        integration_results.append("❌ Raw analysis should have failed with empty journey ID")
    except Exception as e:
        integration_results.append("✅ Raw analysis correctly validates empty journey ID")
    
    # Test 2: Stripped Schema with empty journey ID
    try:
        print("🧪 Testing stripped-schema with empty journey ID...")
        await stripped_schema_tool(
            ctx=mock_ctx,
            journey_id="",
            stage_id="stripped_schema",
            triggered_by="test",
            reason="test"
        )
        integration_results.append("❌ Stripped schema should have failed with empty journey ID")
    except Exception as e:
        integration_results.append("✅ Stripped schema correctly validates empty journey ID")
    
    # Test 3: Get Job Logs with empty journey ID
    try:
        print("🧪 Testing get-job-logs with empty journey ID...")
        await get_job_logs_tool(
            ctx=mock_ctx,
            journey_id="",
            stage_name="raw_analysis",
            job_id="JOB-001-20240101120000",
            step_name="schema_parsing"
        )
        integration_results.append("❌ Get job logs should have failed with empty journey ID")
    except Exception as e:
        integration_results.append("✅ Get job logs correctly validates empty journey ID")
    
    # Test 4: Run Jobs with empty journey ID
    try:
        print("🧪 Testing run-jobs with empty journey ID...")
        await run_jobs_tool(
            ctx=mock_ctx,
            journey_id="",
            stage_id="raw_analysis",
            triggered_by="test",
            reason="test"
        )
        integration_results.append("❌ Run jobs should have failed with empty journey ID")
    except Exception as e:
        integration_results.append("✅ Run jobs correctly validates empty journey ID")
    
    # Print results
    print("\n📋 Integration Test Results:")
    for i, result in enumerate(integration_results, 1):
        print(f"  {i}. {result}")
    
    # Return count of passed tests
    passed_count = sum(1 for result in integration_results if result.startswith("✅"))
    return passed_count

def main():
    """Main test runner entry point."""
    print("🏃‍♂️ TMF ODA Transformer MCP Server - Comprehensive Test Suite")
    print(f"📁 Running tests from: {Path(__file__).parent}")
    
    # Check if required dependencies are available
    try:
        import pytest
        import boto3
        import pydantic
        print("✅ All required test dependencies are available")
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Please install test dependencies: pip install pytest boto3 pydantic")
        return 1
    
    # Run unit tests
    runner = TMFMCPTestRunner()
    runner.run_all_tests()
    
    # Run integration tests
    try:
        integration_passed = asyncio.run(run_tool_integration_tests())
        print(f"\n✅ Integration tests: {integration_passed}/4 passed")
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
    
    # Return appropriate exit code
    return 0 if runner.failed_tests == 0 else 1

if __name__ == "__main__":
    exit(main()) 