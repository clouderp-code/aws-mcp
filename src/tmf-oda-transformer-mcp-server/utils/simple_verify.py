#!/usr/bin/env python3
"""
Simple verification script for TMF ODA Transformer MCP Server.

This script performs basic verification of the server components.
"""

import sys
import traceback
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def write_result(message, success):
    """Write a result message with appropriate formatting."""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def test_imports():
    """Test that all required modules can be imported."""
    write_result("Starting import tests...", True)
    
    try:
        # Test server module imports
        from awslabs.tmf_oda_transformer_mcp_server.server import (
            # schema_analyzer_tool,  # Removed tool
            # db_analyzer_tool,      # Removed tool
            raw_analysis_tool,
            stripped_schema_tool,
            get_job_logs_tool,
            journeys_tool,
            run_jobs_tool,
            test_runner_tool
        )
        write_result("Server tools imported successfully", True)
        
        # Test models
        from awslabs.tmf_oda_transformer_mcp_server.models import (
            TMFODAComponentType,
            DatabaseType,
            SchemaFormat,
            ComplianceLevel
        )
        write_result("Models imported successfully", True)
        
        # Test services
        from awslabs.tmf_oda_transformer_mcp_server.services import (
            # SchemaAnalysisService,      # Removed service
            # DatabaseAnalysisService,    # Removed service
            SimpleJourneyService,
            ValidationService
        )
        write_result("Services imported successfully", True)
        
        return True
        
    except Exception as e:
        write_result(f"Import failed: {e}", False)
        write_result(f"Traceback: {traceback.format_exc()}", False)
        return False

def test_tool_validation():
    """Test basic tool validation."""
    write_result("Starting tool validation...", True)
    
    try:
        from unittest.mock import AsyncMock
        import asyncio
        
        # Import tools
        from awslabs.tmf_oda_transformer_mcp_server.server import (
            # schema_analyzer_tool,  # Removed tool
            # db_analyzer_tool,      # Removed tool
            raw_analysis_tool,
            stripped_schema_tool,
            get_job_logs_tool,
            run_jobs_tool
        )
        from awslabs.tmf_oda_transformer_mcp_server.models import (
            TMFODAComponentType,
            # DatabaseType               # Not needed anymore
        )
        
        # Create proper async mock context
        ctx = AsyncMock()
        ctx.error = AsyncMock()
        
        async def test_validation():
            # Test raw analysis with empty journey ID
            try:
                await raw_analysis_tool(
                    ctx=ctx,
                    journey_id="",
                    stage_id="raw_analysis",
                    triggered_by="test",
                    reason="test"
                )
                write_result("Raw analysis should have failed with empty journey ID", False)
                return False
            except ValueError:
                write_result("Raw analysis correctly validates empty journey ID", True)
            except Exception as e:
                write_result(f"Raw analysis validation error: {e}", False)
                return False
            
            # Test stripped schema with empty journey ID
            try:
                await stripped_schema_tool(
                    ctx=ctx,
                    journey_id="",
                    stage_id="stripped_schema",
                    triggered_by="test",
                    reason="test"
                )
                write_result("Stripped schema should have failed with empty journey ID", False)
                return False
            except ValueError:
                write_result("Stripped schema correctly validates empty journey ID", True)
            except Exception as e:
                write_result(f"Stripped schema validation error: {e}", False)
                return False
            
            # Test get job logs with empty journey ID
            try:
                await get_job_logs_tool(
                    ctx=ctx,
                    journey_id="",
                    stage_name="raw_analysis",
                    job_id="JOB-001-20240101120000",
                    step_name="schema_parsing"
                )
                write_result("Get job logs should have failed with empty journey ID", False)
                return False
            except ValueError:
                write_result("Get job logs correctly validates empty journey ID", True)
            except Exception as e:
                write_result(f"Get job logs validation error: {e}", False)
                return False
            
            # Test run jobs with empty journey ID
            try:
                await run_jobs_tool(
                    ctx=ctx,
                    journey_id="",
                    stage_id="raw_analysis",
                    triggered_by="test",
                    reason="test"
                )
                write_result("Run jobs should have failed with empty journey ID", False)
                return False
            except ValueError:
                write_result("Run jobs correctly validates empty journey ID", True)
            except Exception as e:
                write_result(f"Run jobs validation error: {e}", False)
                return False
            
            return True
        
        result = asyncio.run(test_validation())
        if result:
            write_result("Tool validation tests passed", True)
        return result
        
    except Exception as e:
        write_result(f"Tool validation failed: {e}", False)
        write_result(f"Traceback: {traceback.format_exc()}", False)
        return False

def test_basic_functionality():
    """Test basic functionality without actual execution."""
    write_result("Starting basic functionality tests...", True)
    
    try:
        # Test that key classes can be instantiated
        from awslabs.tmf_oda_transformer_mcp_server.models import TMFODAComponentType
        
        # Test enum values
        component_type = TMFODAComponentType.CUSTOMER_MANAGEMENT
        write_result(f"Component type created: {component_type}", True)
        
        return True
        
    except Exception as e:
        write_result(f"Basic functionality test failed: {e}", False)
        return False

def main():
    """Main verification function."""
    print("🚀 TMF ODA Transformer MCP Server - Simple Verification")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_tool_validation,
        test_basic_functionality
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            write_result(f"Test {test.__name__} failed with exception: {e}", False)
            results.append(False)
    
    print("\n" + "=" * 60)
    print("🎯 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests passed: {passed}/{total}")
    print(f"📈 Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("✅ TMF ODA Transformer MCP Server basic functionality verified!")
    else:
        print(f"\n⚠️  {total - passed} verification(s) failed.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 