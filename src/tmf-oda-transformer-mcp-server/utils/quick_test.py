#!/usr/bin/env python3
"""
Quick test to verify TMF ODA Transformer MCP Server imports and basic functionality.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test basic imports."""
    print("🔍 Testing Basic Imports...")
    
    try:
        # Test server imports
        from awslabs.tmf_oda_transformer_mcp_server.server import (
            schema_analyzer_tool,
            db_analyzer_tool,
            raw_analysis_tool,
            stripped_schema_tool,
            get_job_logs_tool
        )
        print("  ✅ Server tools imported successfully")
        
        # Test model imports
        from awslabs.tmf_oda_transformer_mcp_server.models import (
            TMFODAComponentType,
            DatabaseType,
            SchemaFormat,
            ComplianceLevel
        )
        print("  ✅ Models imported successfully")
        
        # Test scripts imports
        from awslabs.tmf_oda_transformer_mcp_server.scripts import (
            TransformationJobExecutor,
            AWSClientManager
        )
        print("  ✅ Scripts imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def test_enums():
    """Test enum values."""
    print("\n📋 Testing Enum Values...")
    
    try:
        from awslabs.tmf_oda_transformer_mcp_server.models import TMFODAComponentType, DatabaseType
        
        # Test TMF ODA component types
        components = [
            TMFODAComponentType.CUSTOMER_MANAGEMENT,
            TMFODAComponentType.ORDER_MANAGEMENT,
            TMFODAComponentType.PRODUCT_CATALOG_MANAGEMENT
        ]
        print(f"  ✅ TMF ODA Component Types: {len(components)} tested")
        
        # Test database types  
        db_types = [
            DatabaseType.POSTGRESQL,
            DatabaseType.MYSQL,
            DatabaseType.MONGODB
        ]
        print(f"  ✅ Database Types: {len(db_types)} tested")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enum test error: {e}")
        return False

def test_constants():
    """Test constants and configuration."""
    print("\n⚙️ Testing Constants...")
    
    try:
        from awslabs.tmf_oda_transformer_mcp_server.consts import (
            TMF_ODA_COMPONENT_TYPES,
            SUPPORTED_DATABASE_TYPES,
            SUPPORTED_SCHEMA_FORMATS
        )
        
        print(f"  ✅ TMF ODA Component Types: {len(TMF_ODA_COMPONENT_TYPES)} available")
        print(f"  ✅ Supported Database Types: {len(SUPPORTED_DATABASE_TYPES)} available")
        print(f"  ✅ Supported Schema Formats: {len(SUPPORTED_SCHEMA_FORMATS)} available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Constants test error: {e}")
        return False

def test_directory_structure():
    """Test directory structure."""
    print("\n📁 Testing Directory Structure...")
    
    try:
        current_dir = Path(__file__).parent
        
        # Check main files
        files_to_check = [
            "awslabs/tmf_oda_transformer_mcp_server/server.py",
            "awslabs/tmf_oda_transformer_mcp_server/models.py",
            "awslabs/tmf_oda_transformer_mcp_server/consts.py",
            "awslabs/tmf_oda_transformer_mcp_server/scripts/__init__.py",
            "awslabs/tmf_oda_transformer_mcp_server/scripts/job_executor.py",
            "awslabs/tmf_oda_transformer_mcp_server/scripts/aws_client_utils.py",
            "tests/conftest.py",
            "tests/test_schema_analyzer.py"
        ]
        
        missing_files = []
        for file_path in files_to_check:
            full_path = current_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"  ❌ Missing files: {missing_files}")
            return False
        else:
            print(f"  ✅ All {len(files_to_check)} key files found")
            return True
            
    except Exception as e:
        print(f"  ❌ Directory structure test error: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 TMF ODA Transformer MCP Server - Quick Test")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Enums", test_enums), 
        ("Constants", test_constants),
        ("Directory Structure", test_directory_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 QUICK TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    print(f"📈 Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL QUICK TESTS PASSED!")
        print("✅ TMF ODA Transformer MCP Server structure is correct!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\nExit code: {0 if success else 1}") 