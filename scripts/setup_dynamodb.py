# setup_dynamodb.py
import boto3
import sys
import traceback
from datetime import datetime


def print_with_flush(message):
    """Print message and flush stdout immediately"""
    print(message)
    sys.stdout.flush()


def create_transformation_table():
    """Create the TransformationSystem DynamoDB table"""
    print_with_flush('🔧 Starting DynamoDB table creation...')

    try:
        print_with_flush('🔗 Creating DynamoDB client...')
        
        # Import AWS client utilities
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from aws_client_utils import create_aws_client
        
        role_arn = os.environ.get('AWS_ROLE_ARN')
        if role_arn:
            print_with_flush(f'🔑 Using role ARN: {role_arn}')
            dynamodb = create_aws_client('dynamodb', role_arn=role_arn)
        else:
            print_with_flush('🔑 Using default credential chain')
            dynamodb = boto3.client('dynamodb')
        
        print_with_flush('✅ DynamoDB client created successfully')
    except Exception as e:
        print_with_flush(f'❌ Failed to create DynamoDB client: {str(e)}')
        traceback.print_exc()
        return False

    table_definition = {
        'TableName': 'TransformationSystem',
        'AttributeDefinitions': [
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
        ],
        'KeySchema': [
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST',
        'StreamSpecification': {'StreamEnabled': True, 'StreamViewType': 'NEW_AND_OLD_IMAGES'},
    }

    try:
        print_with_flush('📋 Table definition prepared, attempting to create table...')
        response = dynamodb.create_table(**table_definition)
        print_with_flush(
            f'✅ Table creation initiated: {response["TableDescription"]["TableName"]}'
        )
        print_with_flush(f'🕐 Table Status: {response["TableDescription"]["TableStatus"]}')

        # Wait for table to be active
        print_with_flush('⏳ Waiting for table to become active...')
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName='TransformationSystem')
        print_with_flush('✅ Table is now active!')

        return True

    except dynamodb.exceptions.ResourceInUseException:
        print_with_flush('⚠️  Table already exists')
        return True
    except Exception as e:
        print_with_flush(f'❌ Error creating table: {str(e)}')
        traceback.print_exc()
        return False


def create_s3_buckets():
    """Create S3 buckets for logs and reports"""
    print_with_flush('🪣 Starting S3 bucket creation...')

    try:
        print_with_flush('🔗 Creating S3 client...')
        
        # Import AWS client utilities  
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from aws_client_utils import create_aws_client
        
        role_arn = os.environ.get('AWS_ROLE_ARN')
        if role_arn:
            print_with_flush(f'🔑 Using role ARN: {role_arn}')
            s3 = create_aws_client('s3', role_arn=role_arn)
        else:
            print_with_flush('🔑 Using default credential chain')
            s3 = boto3.client('s3')
        
        print_with_flush('✅ S3 client created successfully')
    except Exception as e:
        print_with_flush(f'❌ Failed to create S3 client: {str(e)}')
        traceback.print_exc()
        return False

    bucket_names = ['transformation-journey-logs', 'transformation-journey-reports']

    for bucket_name in bucket_names:
        try:
            print_with_flush(f'�� Creating S3 bucket: {bucket_name}...')
            s3.create_bucket(Bucket=bucket_name)
            print_with_flush(f'✅ Created S3 bucket: {bucket_name}')
        except s3.exceptions.BucketAlreadyExists:
            print_with_flush(f'⚠️  S3 bucket already exists: {bucket_name}')
        except Exception as e:
            print_with_flush(f'❌ Error creating bucket {bucket_name}: {str(e)}')
            traceback.print_exc()

    return True


def seed_sample_journey():
    """Create a sample transformation journey"""
    print_with_flush('🌱 Starting sample journey creation...')

    try:
        print_with_flush('🔗 Creating DynamoDB resource...')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('TransformationSystem')
        print_with_flush('✅ DynamoDB resource created successfully')
    except Exception as e:
        print_with_flush(f'❌ Failed to create DynamoDB resource: {str(e)}')
        traceback.print_exc()
        return None

    journey_id = 'JRN-SAMPLE-001'
    timestamp = datetime.utcnow().isoformat() + 'Z'

    print_with_flush(f'📝 Creating sample journey with ID: {journey_id}')

    # 1. Journey Metadata
    journey_item = {
        'PK': f'JOURNEY#{journey_id}',
        'SK': 'METADATA',
        'EntityType': 'Journey',
        'GSI1PK': 'JOURNEYS',
        'GSI1SK': timestamp,
        'CreatedAt': timestamp,
        'UpdatedAt': timestamp,
        'Data': {
            'journeyId': journey_id,
            'name': 'Sample Customer Management Transformation',
            'description': 'Example transformation for testing',
            'status': 'pending',
            'createdBy': 'system',
            'priority': 'medium',
            'source': {
                'type': 'schema-based',
                'schemaId': 'schema-sample-001',
                'schemaName': 'Sample Customer DB',
                'schemaVersion': '1.0.0',
            },
            'configuration': {
                'timeout': 300,
                'maxDepth': 3,
                'tmfSpecVersion': '4.0.0',
                'outputFormat': 'json',
                'retryAttempts': 3,
            },
            'currentStageIndex': 0,
            'currentStageId': 'raw_analysis',
            'overallProgress': 0,
            'currentJobs': {},
            'aggregates': {
                'totalJobs': 0,
                'completedJobs': 0,
                'failedJobs': 0,
                'totalExecutionTime': '0m',
                'totalLogs': 0,
                'totalErrors': 0,
                'totalWarnings': 0,
            },
            'stageSummary': {
                'raw_analysis': {'totalExecutions': 0, 'lastStatus': 'pending'},
                'stripped_schema': {'totalExecutions': 0, 'lastStatus': 'pending'},
                'tmf_mapping': {'totalExecutions': 0, 'lastStatus': 'pending'},
            },
        },
    }

    # 2. Stage Definitions
    stages = [
        {
            'PK': f'JOURNEY#{journey_id}',
            'SK': 'STAGE#00#raw_analysis',
            'EntityType': 'StageDefinition',
            'GSI1PK': f'JOURNEY#{journey_id}#STAGES',
            'GSI1SK': '00',
            'Data': {
                'stageId': 'raw_analysis',
                'name': 'Raw Input Analysis',
                'description': 'Analyze the raw customer database schema',
                'order': 0,
                'canSkip': False,
                'estimatedDuration': '10m',
                'steps': [
                    {
                        'id': 'schema_parsing',
                        'name': 'Schema File Parsing',
                        'description': 'Parse SQL schema files',
                        'order': 0,
                        'estimatedDuration': '3m',
                    },
                    {
                        'id': 'relationship_discovery',
                        'name': 'Relationship Discovery',
                        'description': 'Identify table relationships',
                        'order': 1,
                        'estimatedDuration': '4m',
                    },
                    {
                        'id': 'data_type_analysis',
                        'name': 'Data Type Analysis',
                        'description': 'Analyze column data types',
                        'order': 2,
                        'estimatedDuration': '3m',
                    },
                ],
            },
        },
        {
            'PK': f'JOURNEY#{journey_id}',
            'SK': 'STAGE#01#stripped_schema',
            'EntityType': 'StageDefinition',
            'GSI1PK': f'JOURNEY#{journey_id}#STAGES',
            'GSI1SK': '01',
            'Data': {
                'stageId': 'stripped_schema',
                'name': 'Create Stripped Schema',
                'description': 'Create TMF-focused simplified schema',
                'order': 1,
                'canSkip': False,
                'estimatedDuration': '8m',
                'steps': [
                    {
                        'id': 'tmf_relevance_filtering',
                        'name': 'TMF Relevance Filtering',
                        'description': 'Filter tables for TMF relevance',
                        'order': 0,
                        'estimatedDuration': '4m',
                    },
                    {
                        'id': 'simplified_schema_creation',
                        'name': 'Simplified Schema Creation',
                        'description': 'Generate simplified schema',
                        'order': 1,
                        'estimatedDuration': '4m',
                    },
                ],
            },
        },
    ]

    try:
        # Insert journey
        print_with_flush('💾 Inserting journey metadata...')
        table.put_item(Item=journey_item)
        print_with_flush(f'✅ Created sample journey: {journey_id}')

        # Insert stages
        print_with_flush('📋 Inserting stage definitions...')
        for stage in stages:
            table.put_item(Item=stage)
            print_with_flush(f'✅ Created stage: {stage["Data"]["name"]}')

        return journey_id

    except Exception as e:
        print_with_flush(f'❌ Error creating sample data: {str(e)}')
        traceback.print_exc()
        return None


def main():
    """Main function with comprehensive error handling"""
    print_with_flush('🚀 Setting up Transformation System Infrastructure...')
    print_with_flush('=' * 60)

    # Test AWS credentials and region
    try:
        print_with_flush('🔐 Testing AWS credentials...')
        
        # Import AWS client utilities  
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from aws_client_utils import test_aws_credentials
        
        role_arn = os.environ.get('AWS_ROLE_ARN')
        if role_arn:
            print_with_flush(f'🔑 Testing credentials with role ARN: {role_arn}')
            identity = test_aws_credentials(role_arn=role_arn)
        else:
            print_with_flush('🔑 Testing credentials with default credential chain')
            identity = test_aws_credentials()
        
        print_with_flush(f'✅ AWS Identity: {identity["Arn"]}')
        print_with_flush(f'✅ AWS Account: {identity["Account"]}')

        # Get current region
        session = boto3.Session()
        region = session.region_name
        print_with_flush(f'✅ AWS Region: {region}')

    except Exception as e:
        print_with_flush(f'❌ AWS authentication failed: {str(e)}')
        traceback.print_exc()
        return False

    print_with_flush('=' * 60)

    # Create DynamoDB table
    print_with_flush('🗄️  Step 1: Creating DynamoDB table...')
    if create_transformation_table():
        print_with_flush('✅ DynamoDB table setup complete')
    else:
        print_with_flush('❌ DynamoDB table setup failed')
        return False

    print_with_flush('=' * 60)

    # Create S3 buckets
    print_with_flush('🪣 Step 2: Creating S3 buckets...')
    if create_s3_buckets():
        print_with_flush('✅ S3 buckets setup complete')
    else:
        print_with_flush('❌ S3 buckets setup failed')
        return False

    print_with_flush('=' * 60)

    # Create sample journey
    print_with_flush('🌱 Step 3: Creating sample journey...')
    journey_id = seed_sample_journey()
    if journey_id:
        print_with_flush(f'✅ Sample journey created: {journey_id}')
    else:
        print_with_flush('❌ Sample journey creation failed')
        return False

    print_with_flush('=' * 60)
    print_with_flush('🎉 Infrastructure setup complete!')
    print_with_flush('=' * 60)

    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_with_flush('\n⚠️  Setup interrupted by user')
        sys.exit(1)
    except Exception as e:
        print_with_flush(f'\n❌ Unexpected error: {str(e)}')
        traceback.print_exc()
        sys.exit(1)
