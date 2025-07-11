# utils.py
import boto3
import os
from typing import Dict, List, Optional

# Import AWS client utilities from the local scripts directory
from .aws_client_utils import AWSClientManager


class TransformationUtils:
    def __init__(self, region_name: str = None, role_arn: Optional[str] = None):
        """
        Initialize TransformationUtils with optional role ARN support.
        
        Args:
            region_name: AWS region name (optional)
            role_arn: AWS role ARN to assume (optional)
        """
        self.role_arn = role_arn or os.environ.get('AWS_ROLE_ARN')
        
        # Create AWS client manager
        self.client_manager = AWSClientManager(role_arn=self.role_arn, region_name=region_name)
        
        # Create AWS clients using the client manager
        self.dynamodb = self.client_manager.create_resource('dynamodb')
        self.s3 = self.client_manager.create_client('s3')
        self.table = self.dynamodb.Table('TransformationSystem')
        
        # Get region from client manager
        self.region_name = self.client_manager.region_name

    def list_journeys(self) -> List[Dict]:
        """List all transformation journeys"""
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :gsi1pk',
                ExpressionAttributeValues={':gsi1pk': 'JOURNEYS'},
                ScanIndexForward=False,
            )

            journeys = []
            for item in response['Items']:
                journey_data = item['Data']
                journeys.append(
                    {
                        'journeyId': journey_data['journeyId'],
                        'name': journey_data['name'],
                        'status': journey_data['status'],
                        'createdAt': journey_data.get('createdAt'),
                        'currentStage': journey_data.get('currentStageId'),
                        'progress': journey_data.get('overallProgress', 0),
                    }
                )

            return journeys

        except Exception as e:
            print(f'Error listing journeys: {str(e)}')
            return []

    def get_journey_status(self, journey_id: str) -> Dict:
        """Get detailed journey status"""
        try:
            response = self.table.get_item(Key={'PK': f'JOURNEY#{journey_id}', 'SK': 'METADATA'})

            if 'Item' not in response:
                return None

            return response['Item']['Data']

        except Exception as e:
            print(f'Error getting journey status: {str(e)}')
            return None

    def get_journey_stages(self, journey_id: str) -> List[Dict]:
        """Get all stages and their steps for a journey"""
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :gsi1pk',
                ExpressionAttributeValues={':gsi1pk': f'JOURNEY#{journey_id}#STAGES'},
                ScanIndexForward=True,  # Order by GSI1SK (stage order)
            )

            stages = []
            for item in response['Items']:
                stage_data = item['Data']
                stages.append({
                    'stageId': stage_data['stageId'],
                    'name': stage_data['name'],
                    'description': stage_data['description'],
                    'order': stage_data['order'],
                    'canSkip': stage_data.get('canSkip', False),
                    'estimatedDuration': stage_data.get('estimatedDuration', 'N/A'),
                    'steps': stage_data.get('steps', [])
                })

            return stages

        except Exception as e:
            print(f'Error getting journey stages: {str(e)}')
            return []

    def get_stage_jobs(self, journey_id: str, stage_id: str, limit: int = 10) -> List[Dict]:
        """Get job executions for a stage"""
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :gsi1pk',
                ExpressionAttributeValues={':gsi1pk': f'STAGE#{journey_id}#{stage_id}'},
                ScanIndexForward=False,
                Limit=limit,
            )

            jobs = []
            for item in response['Items']:
                job_data = item['Data']
                jobs.append(
                    {
                        'jobId': job_data['jobId'],
                        'executionNumber': job_data['executionNumber'],
                        'status': job_data['status'],
                        'startTime': job_data['startTime'],
                        'endTime': job_data.get('endTime'),
                        'duration': job_data.get('duration'),
                        'progress': job_data.get('progress', 0),
                    }
                )

            return jobs

        except Exception as e:
            print(f'Error getting stage jobs: {str(e)}')
            return []

    def download_logs(
        self, journey_id: str, stage_id: str, job_id: str, step_id: str, output_file: str
    ):
        """Download logs for a specific step"""
        try:
            logs_key = (
                f'journeys/{journey_id}/stages/{stage_id}/executions/{job_id}/logs/{step_id}.json'
            )

            self.s3.download_file(
                Bucket='transformation-journey-logs', Key=logs_key, Filename=output_file
            )

            print(f'✅ Downloaded logs to: {output_file}')

        except Exception as e:
            print(f'❌ Error downloading logs: {str(e)}')

    def download_report(
        self, journey_id: str, stage_id: str, job_id: str, step_id: str, output_file: str
    ):
        """Download report for a specific step"""
        try:
            report_key = f'journeys/{journey_id}/stages/{stage_id}/executions/{job_id}/reports/{step_id}.json'

            self.s3.download_file(
                Bucket='transformation-journey-reports', Key=report_key, Filename=output_file
            )

            print(f'✅ Downloaded report to: {output_file}')

        except Exception as e:
            print(f'❌ Error downloading report: {str(e)}')

    def get_job_details(self, journey_id: str, job_id: str) -> Dict:
        """Get detailed job execution data"""
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'JOURNEY#{journey_id}',
                    ':sk_prefix': 'JOB#',
                    ':job_id': job_id,
                },
                FilterExpression='#data.jobId = :job_id',
                ExpressionAttributeNames={'#data': 'Data'},
            )

            if response['Items']:
                return response['Items'][0]['Data']
            return None

        except Exception as e:
            print(f'Error getting job details: {str(e)}')
            return None

    def get_logs_content(self, journey_id: str, stage_name: str, job_id: str, step_name: str) -> Dict:
        """Get logs content for a specific step from S3"""
        try:
            logs_key = f'journeys/{journey_id}/stages/{stage_name}/executions/{job_id}/logs/{step_name}.json'
            
            response = self.s3.get_object(
                Bucket='transformation-journey-logs',
                Key=logs_key
            )
            
            import json
            logs_content = json.loads(response['Body'].read())
            
            return {
                'success': True,
                'logs': logs_content,
                'location': f's3://transformation-journey-logs/{logs_key}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to retrieve logs for {step_name}'
            } 