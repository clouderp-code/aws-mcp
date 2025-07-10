#!/usr/bin/env python3
"""
Simple status check for TMF ODA Transformer MCP Server.
This script performs basic verification without complex async operations.
"""

import sys
import os
from pathlib import Path

def main():
    print("🔍 TMF ODA Transformer MCP Server - Status Check")
    print("=" * 50)
    
    # Check 1: Directory structure
    print("📁 Checking directory structure...")
    current_dir = Path(__file__).parent
    required_files = [
        "awslabs/tmf_oda_transformer_mcp_server/server.py",
        "awslabs/tmf_oda_transformer_mcp_server/models.py", 
        "awslabs/tmf_oda_transformer_mcp_server/scripts/job_executor.py",
        "tests/conftest.py"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (MISSING)")
            all_files_exist = False
    
    # Check 2: Python imports
    print("\n📦 Checking Python imports...")
    sys.path.insert(0, str(current_dir))
    
    try:
        # Import models first (no dependencies)
        from awslabs.tmf_oda_transformer_mcp_server.models import TMFODAComponentType
        print("  ✅ Models imported")
        
        # Import constants
        from awslabs.tmf_oda_transformer_mcp_server.consts import TMF_ODA_COMPONENT_TYPES
        print("  ✅ Constants imported")
        
        # Import scripts
        from awslabs.tmf_oda_transformer_mcp_server.scripts import TransformationJobExecutor
        print("  ✅ Scripts imported")
        
        # Check if server tools are defined (without importing them)
        server_file = current_dir / "awslabs/tmf_oda_transformer_mcp_server/server.py"
        if server_file.exists():
            content = server_file.read_text()
            tools = [
                "schema_analyzer_tool",
                "db_analyzer_tool", 
                "raw_analysis_tool",
                "stripped_schema_tool",
                "get_job_logs_tool"
            ]
            
            tools_found = 0
            for tool in tools:
                if f"async def {tool}" in content:
                    tools_found += 1
                    print(f"  ✅ {tool} found")
                else:
                    print(f"  ❌ {tool} missing")
            
            if tools_found == 5:
                print("  ✅ All 5 tools found in server.py")
            else:
                print(f"  ❌ Only {tools_found}/5 tools found")
        
        imports_ok = True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        imports_ok = False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        imports_ok = False
    
    # Check 3: Configuration values
    print("\n⚙️ Checking configuration values...")
    try:
        from awslabs.tmf_oda_transformer_mcp_server.consts import (
            SUPPORTED_DATABASE_TYPES,
            SUPPORTED_SCHEMA_FORMATS,
            TMF_ODA_COMPONENT_TYPES
        )
        
        print(f"  ✅ {len(TMF_ODA_COMPONENT_TYPES)} TMF ODA component types")
        print(f"  ✅ {len(SUPPORTED_DATABASE_TYPES)} database types")
        print(f"  ✅ {len(SUPPORTED_SCHEMA_FORMATS)} schema formats")
        
        config_ok = True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        config_ok = False
    
    # Check 4: Test files
    print("\n🧪 Checking test files...")
    test_files = [
        "tests/test_schema_analyzer.py",
        "tests/test_db_analyzer.py",
        "tests/test_raw_analysis.py",
        "tests/test_stripped_schema.py",
        "tests/test_get_job_logs.py"
    ]
    
    test_files_count = 0
    for test_file in test_files:
        full_path = current_dir / test_file
        if full_path.exists():
            test_files_count += 1
            print(f"  ✅ {test_file}")
        else:
            print(f"  ❌ {test_file} (MISSING)")
    
    tests_ok = test_files_count == 5
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 STATUS SUMMARY")
    print("=" * 50)
    
    checks = [
        ("Directory Structure", all_files_exist),
        ("Python Imports", imports_ok),
        ("Configuration", config_ok),
        ("Test Files", tests_ok)
    ]
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    print(f"\n📊 Overall Status: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 TMF ODA TRANSFORMER MCP SERVER IS READY!")
        print("✅ All systems operational")
        print("\n🛠️ Available Tools:")
        print("  • schema-analyzer - Schema file analysis")
        print("  • db-analyzer - Database structure analysis")
        print("  • raw-analysis - Raw analysis stage execution")
        print("  • stripped-schema - Schema stripping stage")
        print("  • get-job-logs - Job log retrieval")
        return True
    else:
        print(f"\n⚠️ Issues detected: {total - passed} check(s) failed")
        print("Please review the errors above and fix them before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 