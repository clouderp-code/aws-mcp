#!/usr/bin/env python3
"""
Simple verification script that outputs results to a file.
This avoids Cursor's terminal integration issues.
"""

import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def write_result(message, success=True):
    """Write result to output file and print."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = {
        "timestamp": timestamp,
        "message": message,
        "success": success
    }
    
    # Write to file
    with open("verification_results.json", "a") as f:
        f.write(json.dumps(result) + "\n")
    
    # Also print
    status = "✅" if success else "❌"
    print(f"{status} {message}")

def test_imports():
    """Test basic imports."""
    write_result("Starting import verification...", True)
    
    try:
        # Test server imports
        from awslabs.tmf_oda_transformer_mcp_server.server import (
            schema_analyzer_tool,
            db_analyzer_tool,
            raw_analysis_tool,
            stripped_schema_tool,
            get_job_logs_tool,
            test_runner_tool
        )
        write_result("Server tools imported successfully", True)
        
        # Test model imports
        from awslabs.tmf_oda_transformer_mcp_server.models import (
            TMFODAComponentType,
            DatabaseType,
            SchemaFormat,
            ComplianceLevel
        )
        write_result("Models imported successfully", True)
        
        # Test scripts imports
        from awslabs.tmf_oda_transformer_mcp_server.scripts import (
            TransformationJobExecutor,
            AWSClientManager
        )
        write_result("Scripts imported successfully", True)
        
        write_result("All imports successful!", True)
        return True
        
    except ImportError as e:
        write_result(f"Import error: {e}", False)
        return False
    except Exception as e:
        write_result(f"Unexpected error: {e}", False)
        return False

def test_tool_validation():
    """Test basic tool validation."""
    write_result("Starting tool validation...", True)
    
    try:
        from unittest.mock import AsyncMock
        import asyncio
        
        # Import tools
        from awslabs.tmf_oda_transformer_mcp_server.server import (
            schema_analyzer_tool,
            db_analyzer_tool
        )
        from awslabs.tmf_oda_transformer_mcp_server.models import (
            TMFODAComponentType,
            DatabaseType
        )
        
        # Create proper async mock context
        ctx = AsyncMock()
        ctx.error = AsyncMock()
        
        async def test_validation():
            # Test schema analyzer with empty workspace
            try:
                await schema_analyzer_tool(
                    ctx=ctx,
                    workspace_dir="",
                    oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                    schema_format=None
                )
                write_result("Schema analyzer should have failed with empty workspace", False)
                return False
            except ValueError:
                write_result("Schema analyzer correctly validates empty workspace", True)
            except Exception as e:
                write_result(f"Schema analyzer validation error: {e}", False)
                return False
            
            # Test db analyzer with empty connection
            try:
                await db_analyzer_tool(
                    ctx=ctx,
                    connection_string="",
                    database_type=DatabaseType.POSTGRESQL,
                    oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                    tables_filter=None
                )
                write_result("DB analyzer should have failed with empty connection", False)
                return False
            except ValueError:
                write_result("DB analyzer correctly validates empty connection", True)
            except Exception as e:
                write_result(f"DB analyzer validation error: {e}", False)
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

def main():
    """Main verification function."""
    # Clear previous results
    if os.path.exists("verification_results.json"):
        os.remove("verification_results.json")
    
    write_result("🚀 TMF ODA Transformer MCP Server - Simple Verification", True)
    write_result("=" * 60, True)
    
    # Run tests
    tests = [
        ("Import Tests", test_imports),
        ("Tool Validation", test_tool_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        write_result(f"Running {test_name}...", True)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            write_result(f"{test_name} failed with exception: {e}", False)
            results.append((test_name, False))
    
    # Summary
    write_result("=" * 60, True)
    write_result("🎯 VERIFICATION SUMMARY", True)
    write_result("=" * 60, True)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        write_result(f"{status}: {test_name}", result)
    
    write_result(f"Results: {passed}/{total} tests passed", True)
    write_result(f"Success rate: {passed/total*100:.1f}%", True)
    
    if passed == total:
        write_result("🎉 ALL TESTS PASSED!", True)
        write_result("✅ TMF ODA Transformer MCP Server is ready!", True)
    else:
        write_result(f"⚠️ {total - passed} test(s) failed.", False)
    
    write_result("Results written to verification_results.json", True)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 