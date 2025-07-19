#!/usr/bin/env python3
"""
Debug script to test raw_analysis stage execution directly
"""

import sys
import os
import traceback

# Add the project root to Python path
sys.path.insert(0, '/opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server')

def test_raw_analysis():
    print("🧪 DEBUGGING RAW ANALYSIS STAGE")
    print("=" * 60)
    
    try:
        # Import the stage
        print("📦 Importing RawAnalysisStage...")
        from awslabs.tmf_oda_transformer_mcp_server.scripts.stages.raw_analysis import RawAnalysisStage
        print("✅ Import successful")
        
        # Create instance
        print("🏗️ Creating RawAnalysisStage instance...")
        stage = RawAnalysisStage(
            journey_id="TEST-JOURNEY",
            stage_id="raw_analysis", 
            job_id="TEST-JOB-001",
            region_name="us-east-1"
        )
        print("✅ Instance created successfully")
        
        # Check if local logger was set up
        print(f"📁 Local log file: {getattr(stage, 'local_log_file', 'NOT SET')}")
        print(f"🔍 Local logger exists: {hasattr(stage, 'local_logger')}")
        
        # Test step execution
        print("🔧 Testing schema_parsing step...")
        result = stage.execute_step('schema_parsing', {})
        print(f"✅ Step result: {result.get('status', 'unknown')}")
        
        # Check if log file was created
        if hasattr(stage, 'local_log_file') and os.path.exists(stage.local_log_file):
            print(f"📄 Log file created: {stage.local_log_file}")
            with open(stage.local_log_file, 'r') as f:
                content = f.read()
                print(f"📏 Log file size: {len(content)} characters")
                print("📝 First 500 characters:")
                print(content[:500])
        else:
            print("❌ No log file found")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("🔍 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_raw_analysis() 