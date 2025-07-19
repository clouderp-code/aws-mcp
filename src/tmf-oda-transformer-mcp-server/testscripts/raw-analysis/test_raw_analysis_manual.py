#!/usr/bin/env python3
"""
Manual test script to run raw_analysis stage directly and debug local logging
"""

import sys
import os
import traceback
import json

# Add the project root to Python path
sys.path.insert(0, '/opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server')

def test_manual_execution():
    print("🧪 MANUAL RAW ANALYSIS TEST")
    print("=" * 60)
    
    try:
        # Import required modules
        print("📦 Importing modules...")
        from awslabs.tmf_oda_transformer_mcp_server.scripts.stages.raw_analysis import RawAnalysisStage
        print("✅ Modules imported successfully")
        
        # Create realistic test parameters
        journey_id = "ECAF1EA28790"
        stage_id = "raw_analysis"
        job_id = "MANUAL-TEST-001"
        
        print(f"🏗️ Creating stage instance...")
        print(f"  Journey ID: {journey_id}")
        print(f"  Stage ID: {stage_id}")
        print(f"  Job ID: {job_id}")
        
        # Create stage instance
        stage = RawAnalysisStage(
            journey_id=journey_id,
            stage_id=stage_id,
            job_id=job_id,
            region_name="us-east-1"
        )
        
        print("✅ Stage instance created")
        
        # Check logging setup
        print("\n📁 LOGGING SETUP CHECK:")
        print(f"  Local log file: {getattr(stage, 'local_log_file', 'NOT SET')}")
        print(f"  Local logger exists: {hasattr(stage, 'local_logger')}")
        
        if hasattr(stage, 'local_log_file'):
            log_dir = os.path.dirname(stage.local_log_file)
            print(f"  Log directory: {log_dir}")
            print(f"  Log directory exists: {os.path.exists(log_dir)}")
            print(f"  Log directory writable: {os.access(log_dir, os.W_OK) if os.path.exists(log_dir) else 'N/A'}")
        
        # Test each step
        steps = stage.steps
        print(f"\n🔧 TESTING {len(steps)} STEPS:")
        
        for i, step_config in enumerate(steps, 1):
            step_id = step_config['id']
            step_name = step_config['name']
            
            print(f"\n📝 Step {i}/{len(steps)}: {step_name} ({step_id})")
            print("-" * 40)
            
            try:
                # Execute the step
                result = stage.execute_step(step_id, step_config)
                
                print(f"✅ Step completed with status: {result.get('status', 'unknown')}")
                
                if result.get('status') == 'completed':
                    summary = result.get('summary', 'No summary')
                    print(f"📊 Summary: {summary}")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"❌ Error: {error}")
                
                # Check if log file was created/updated
                if hasattr(stage, 'local_log_file') and os.path.exists(stage.local_log_file):
                    file_size = os.path.getsize(stage.local_log_file)
                    print(f"📄 Log file size: {file_size} bytes")
                    
                    # Show last few lines
                    with open(stage.local_log_file, 'r') as f:
                        lines = f.readlines()
                        print(f"📝 Last 3 log lines:")
                        for line in lines[-3:]:
                            print(f"    {line.strip()}")
                
            except Exception as step_error:
                print(f"❌ Step {step_id} failed: {str(step_error)}")
                print("🔍 Step error traceback:")
                traceback.print_exc()
                break
        
        # Final log file check
        print("\n📄 FINAL LOG FILE CHECK:")
        if hasattr(stage, 'local_log_file'):
            if os.path.exists(stage.local_log_file):
                file_size = os.path.getsize(stage.local_log_file)
                print(f"✅ Log file exists: {stage.local_log_file} ({file_size} bytes)")
                
                # Check for any report files
                log_dir = os.path.dirname(stage.local_log_file)
                report_files = [f for f in os.listdir(log_dir) if f.startswith('step1-report_')]
                if report_files:
                    print(f"📊 Report files found: {report_files}")
                else:
                    print("📊 No report files found")
                    
            else:
                print(f"❌ Log file does not exist: {stage.local_log_file}")
        else:
            print("❌ No local_log_file attribute set")
        
        print("\n🎯 TEST COMPLETED")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("🔍 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_manual_execution() 