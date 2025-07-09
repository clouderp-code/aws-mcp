#!/usr/bin/env python3
"""
Test script for AWS Role ARN functionality in TMF ODA Transformer

This script tests the role ARN assumption functionality to ensure external machines
can properly authenticate with AWS services.
"""

import os
import sys
import argparse
from aws_client_utils import AWSClientManager, test_aws_credentials


def test_role_arn_functionality(role_arn: str, region_name: str = None):
    """
    Test role ARN assumption functionality.
    
    Args:
        role_arn: AWS role ARN to test
        region_name: AWS region name (optional)
    """
    print("🔬 Testing TMF ODA Transformer Role ARN Functionality")
    print("=" * 60)
    
    try:
        # Test 1: Test credentials
        print(f"🔐 Test 1: Testing credential assumption for role: {role_arn}")
        identity = test_aws_credentials(role_arn=role_arn, region_name=region_name)
        print(f"✅ Successfully assumed role!")
        print(f"   Account: {identity['Account']}")
        print(f"   ARN: {identity['Arn']}")
        print(f"   User ID: {identity['UserId']}")
        
        # Test 2: Test client manager
        print(f"\n🔧 Test 2: Testing AWS Client Manager")
        client_manager = AWSClientManager(role_arn=role_arn, region_name=region_name)
        print(f"✅ AWS Client Manager created successfully")
        print(f"   Region: {client_manager.region_name}")
        
        # Test 3: Test DynamoDB client
        print(f"\n📊 Test 3: Testing DynamoDB client creation")
        dynamodb = client_manager.create_resource('dynamodb')
        print(f"✅ DynamoDB resource created successfully")
        
        # Test 4: Test S3 client
        print(f"\n🪣 Test 4: Testing S3 client creation")
        s3 = client_manager.create_client('s3')
        print(f"✅ S3 client created successfully")
        
        # Test 5: Test job executor
        print(f"\n⚙️ Test 5: Testing Job Executor with role ARN")
        from job_executor import TransformationJobExecutor
        executor = TransformationJobExecutor(role_arn=role_arn, region_name=region_name)
        print(f"✅ Job Executor created successfully")
        
        # Test 6: Test stage base class
        print(f"\n🎭 Test 6: Testing Stage Base Class with role ARN")
        from stages.base_stage import BaseStage
        
        # Create a dummy stage implementation for testing
        class TestStage(BaseStage):
            @property
            def stage_name(self):
                return "Test Stage"
            
            @property
            def stage_description(self):
                return "Test stage for role ARN validation"
            
            @property
            def steps(self):
                return [{"id": "test", "name": "Test Step"}]
            
            def execute_step(self, step_id, step_data):
                return {"status": "completed"}
        
        test_stage = TestStage('test-journey', 'test-stage', 'test-job', region_name, role_arn)
        print(f"✅ Stage created successfully")
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Role ARN functionality is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function for command-line testing."""
    parser = argparse.ArgumentParser(description='Test TMF ODA Transformer Role ARN functionality')
    parser.add_argument('--role-arn', required=True, help='AWS role ARN to test')
    parser.add_argument('--region', help='AWS region name (optional)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Test the role ARN functionality
    success = test_role_arn_functionality(args.role_arn, args.region)
    
    if success:
        print(f"\n✅ Role ARN test completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Role ARN test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 