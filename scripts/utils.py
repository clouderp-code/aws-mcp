# utils.py
import boto3
from typing import Dict, List


class TransformationUtils:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.table = self.dynamodb.Table('TransformationSystem')

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
