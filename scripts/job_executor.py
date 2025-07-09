# job_executor.py - Refactored for Stage-based Architecture
import boto3
import json
import logging
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

# Import the stage registry
import sys
import os
# Add the scripts directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from stages import get_stage_class, list_available_stages
from aws_client_utils import AWSClientManager


class TransformationJobExecutor:
    def __init__(self, region_name: str = None, role_arn: Optional[str] = None):
        """
        Initialize the TransformationJobExecutor.
        
        Args:
            region_name: AWS region name (optional)
            role_arn: AWS role ARN to assume (optional)
        """
        self.role_arn = role_arn or os.environ.get('AWS_ROLE_ARN')
        self.region_name = region_name
        
        # Create AWS client manager
        self.client_manager = AWSClientManager(role_arn=self.role_arn, region_name=self.region_name)
        
        # Create AWS clients using the client manager
        self.dynamodb = self.client_manager.create_resource('dynamodb')
        self.s3 = self.client_manager.create_client('s3')
        self.table = self.dynamodb.Table('TransformationSystem')
        self.logs_bucket = 'transformation-journey-logs'
        self.reports_bucket = 'transformation-journey-reports'

        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Log the configuration
        if self.role_arn:
            self.logger.info(f"Job executor configured with role ARN: {self.role_arn}")
        else:
            self.logger.info("Job executor configured with default credential chain")

    def start_job_execution(
        self,
        journey_id: str,
        stage_id: str,
        triggered_by: str = 'system',
        reason: str = 'Automated execution',
    ) -> str:
        """Start a new job execution for a stage"""
        try:
            # Get journey metadata
            journey = self.get_journey(journey_id)
            if not journey:
                raise Exception(f'Journey {journey_id} not found')

            # Get stage definition
            stage_def = self.get_stage_definition(journey_id, stage_id)
            if not stage_def:
                raise Exception(f'Stage {stage_id} not found')

            # Validate stage is available
            if stage_id not in list_available_stages():
                raise Exception(f'Stage {stage_id} not implemented')

            # Generate job ID and execution number
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            execution_number = self.get_next_execution_number(journey_id, stage_id)
            job_id = f'JOB-{execution_number:03d}-{timestamp}'

            # Create job execution record
            job_data = {
                'PK': f'JOURNEY#{journey_id}',
                'SK': f'JOB#{int(stage_def["order"]):02d}#{stage_id}#{execution_number:03d}#{timestamp}',
                'EntityType': 'JobExecution',
                'GSI1PK': f'STAGE#{journey_id}#{stage_id}',
                'GSI1SK': datetime.utcnow().isoformat() + 'Z',
                'CreatedAt': datetime.utcnow().isoformat() + 'Z',
                'UpdatedAt': datetime.utcnow().isoformat() + 'Z',
                'Data': {
                    'jobId': job_id,
                    'journeyId': journey_id,
                    'stageId': stage_id,
                    'stageName': stage_def['name'],
                    'stageOrder': int(stage_def['order']),
                    'executionNumber': execution_number,
                    'status': 'in_progress',
                    'startTime': datetime.utcnow().isoformat() + 'Z',
                    'endTime': None,
                    'duration': None,
                    'progress': Decimal('0'),
                    'triggeredBy': triggered_by,
                    'triggerReason': reason,
                    'retryAttempt': 0,
                    's3Config': {
                        'logsBucket': self.logs_bucket,
                        'logsPrefix': f'journeys/{journey_id}/stages/{stage_id}/executions/{job_id}/',
                        'reportsBucket': self.reports_bucket,
                        'reportsPrefix': f'journeys/{journey_id}/stages/{stage_id}/executions/{job_id}/',
                        'region': self.region_name,
                    },
                    'currentStepIndex': 0,
                    'currentStepId': stage_def['steps'][0]['id'],
                    'stepResults': {
                        step['id']: {'status': 'pending', 'progress': Decimal('0')}
                        for step in stage_def['steps']
                    },
                    'jobMetrics': {
                        'totalLogs': 0,
                        'totalErrors': 0,
                        'totalWarnings': 0,
                        'overallProgress': Decimal('0'),
                        'itemsProcessed': 0,
                        'itemsTotal': 0,
                    },
                },
            }

            # Save job to DynamoDB
            self.table.put_item(Item=job_data)

            # Update journey current job
            self.update_journey_current_job(journey_id, stage_id, job_id, execution_number)

            self.logger.info(f'✅ Started job execution: {job_id} for stage {stage_id}')
            return job_id

        except Exception as e:
            self.logger.error(f'❌ Error starting job execution: {str(e)}')
            raise

    def execute_job(self, journey_id: str, job_id: str):
        """Execute all steps in a job using stage-based architecture"""
        try:
            # Get job data
            job_data = self.get_job_execution(journey_id, job_id)
            if not job_data:
                raise Exception(f'Job {job_id} not found')

            stage_id = job_data['stageId']
            
            # Get stage class
            stage_class = get_stage_class(stage_id)
            if not stage_class:
                raise Exception(f'Stage class not found for stage: {stage_id}')

            # Create stage instance with role ARN support
            stage = stage_class(journey_id, stage_id, job_id, self.region_name, self.role_arn)
            steps = stage.steps

            self.logger.info(f'🚀 Executing job {job_id} with {len(steps)} steps using {stage_class.__name__}')
            
            # DEBUG: Log what steps we're about to execute
            self.logger.info('📋 Steps to execute:')
            for i, step in enumerate(steps):
                self.logger.info(f'  {i+1}. {step["id"]} - {step["name"]}')
            self.logger.info(f'🔢 Total steps in execution list: {len(steps)}')

            # Execute each step using the stage implementation
            for step_index, step in enumerate(steps):
                step_id = step['id']
                self.logger.info(f'📝 Starting step {step_index + 1}/{len(steps)}: {step["name"]} (ID: {step_id})')

                try:
                    # Update step to in_progress
                    self.logger.info(f'🔄 Updating step status to in_progress for {step_id}')
                    self.update_step_status(journey_id, job_id, step_id, 'in_progress', step_index)

                    # Execute step using the stage implementation
                    self.logger.info(f'🚀 Executing step: {step_id}')
                    step_result = stage.execute_step(step_id, step)
                    self.logger.info(f'✅ Step execution completed for {step_id}, result status: {step_result.get("status", "unknown")}')

                    # Update step with results
                    self.logger.info(f'💾 Updating step results for {step_id}')
                    self.update_step_results(journey_id, job_id, step_id, step_result)

                    # Update job progress
                    progress = ((step_index + 1) / len(steps)) * 100
                    self.logger.info(f'📈 Updating job progress to {progress}% (step {step_index + 1}/{len(steps)})')
                    self.update_job_progress(journey_id, job_id, progress, step_index + 1)

                    self.logger.info(f'✅ Completed step: {step["name"]} (ID: {step_id})')
                    
                except Exception as step_error:
                    self.logger.error(f'❌ Error in step {step_id}: {str(step_error)}')
                    self.logger.error(f'Error type: {type(step_error).__name__}')
                    import traceback
                    traceback.print_exc()
                    raise step_error

            # Complete the job
            self.complete_job(journey_id, job_id)
            self.logger.info(f'🎉 Job {job_id} completed successfully')

        except Exception as e:
            self.logger.error(f'❌ Error executing job {job_id}: {str(e)}')
            self.fail_job(journey_id, job_id, str(e))
            raise

    def get_available_stages(self) -> List[str]:
        """Get list of available stage implementations"""
        return list_available_stages()

    def get_stage_info(self, stage_id: str) -> Dict:
        """Get information about a stage implementation"""
        stage_class = get_stage_class(stage_id)
        if not stage_class:
            return None
        
        # Create a temporary instance to get stage info
        temp_stage = stage_class('temp', stage_id, 'temp', self.region_name, self.role_arn)
        return {
            'stage_id': stage_id,
            'stage_name': temp_stage.stage_name,
            'stage_description': temp_stage.stage_description,
            'steps': temp_stage.steps,
            'class_name': stage_class.__name__
        }

    def get_journey(self, journey_id: str) -> Dict:
        """Get journey metadata"""
        try:
            response = self.table.get_item(Key={'PK': f'JOURNEY#{journey_id}', 'SK': 'METADATA'})
            return response.get('Item', {}).get('Data')
        except Exception as e:
            self.logger.error(f'Error getting journey {journey_id}: {str(e)}')
            return None

    def get_stage_definition(self, journey_id: str, stage_id: str) -> Dict:
        """Get stage definition from DynamoDB"""
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'JOURNEY#{journey_id}',
                    ':sk_prefix': f'STAGE#',
                    ':stage_id': stage_id,
                },
                FilterExpression='#data.stageId = :stage_id',
                ExpressionAttributeNames={'#data': 'Data'},
            )

            if response['Items']:
                return response['Items'][0]['Data']
            return None

        except Exception as e:
            self.logger.error(f'Error getting stage definition: {str(e)}')
            return None

    def get_next_execution_number(self, journey_id: str, stage_id: str) -> int:
        """Get the next execution number for a stage"""
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :gsi1pk',
                ExpressionAttributeValues={':gsi1pk': f'STAGE#{journey_id}#{stage_id}'},
                ScanIndexForward=False,
                Limit=1,
            )

            if response['Items']:
                last_execution = response['Items'][0]['Data']['executionNumber']
                return int(last_execution) + 1
            return 1

        except Exception as e:
            self.logger.error(f'Error getting next execution number: {str(e)}')
            return 1

    def get_job_execution(self, journey_id: str, job_id: str) -> Dict:
        """Get job execution data"""
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
            self.logger.error(f'Error getting job execution: {str(e)}')
            return None

    def update_journey_current_job(
        self, journey_id: str, stage_id: str, job_id: str, execution_number: int
    ):
        """Update journey with current job info"""
        try:
            self.table.update_item(
                Key={'PK': f'JOURNEY#{journey_id}', 'SK': 'METADATA'},
                UpdateExpression='SET #data.currentJobs.#stage_id = :job_info, #data.updatedAt = :updated_at',
                ExpressionAttributeNames={
                    '#data': 'Data',
                    '#stage_id': stage_id,
                },
                ExpressionAttributeValues={
                    ':job_info': {
                        'jobId': job_id,
                        'executionNumber': execution_number,
                        'status': 'in_progress',
                        'startTime': datetime.utcnow().isoformat() + 'Z',
                    },
                    ':updated_at': datetime.utcnow().isoformat() + 'Z',
                },
            )
        except Exception as e:
            self.logger.error(f'Error updating journey current job: {str(e)}')

    def update_step_status(
        self, journey_id: str, job_id: str, step_id: str, status: str, step_index: int
    ):
        """Update step status in job record"""
        try:
            # First, get the job to find the correct SK
            job_data = self.get_job_execution(journey_id, job_id)
            if not job_data:
                raise Exception(f'Job {job_id} not found')

            # Build the SK from job data
            stage_id = job_data['stageId']
            execution_number = job_data['executionNumber']
            timestamp = job_id.split('-')[-1]  # Extract timestamp from job_id
            sk = f'JOB#{int(job_data["stageOrder"]):02d}#{stage_id}#{int(execution_number):03d}#{timestamp}'

            self.table.update_item(
                Key={'PK': f'JOURNEY#{journey_id}', 'SK': sk},
                UpdateExpression='SET #data.stepResults.#step_id.#status = :status, #data.currentStepIndex = :step_index, #data.currentStepId = :step_id, #data.updatedAt = :updated_at',
                ExpressionAttributeNames={
                    '#data': 'Data',
                    '#step_id': step_id,
                    '#status': 'status',
                },
                ExpressionAttributeValues={
                    ':status': status,
                    ':step_index': step_index,
                    ':step_id': step_id,
                    ':updated_at': datetime.utcnow().isoformat() + 'Z',
                },
            )
        except Exception as e:
            self.logger.error(f'Error updating step status: {str(e)}')

    def update_step_results(self, journey_id: str, job_id: str, step_id: str, step_result: Dict):
        """Update step results in job record"""
        try:
            # Get job data to find correct SK
            job_data = self.get_job_execution(journey_id, job_id)
            if not job_data:
                raise Exception(f'Job {job_id} not found')

            # Build the SK
            stage_id = job_data['stageId']
            execution_number = job_data['executionNumber']
            timestamp = job_id.split('-')[-1]
            sk = f'JOB#{int(job_data["stageOrder"]):02d}#{stage_id}#{int(execution_number):03d}#{timestamp}'

            # Convert float values to Decimal for DynamoDB compatibility
            step_result_converted = self._convert_floats_to_decimal(step_result)

            self.table.update_item(
                Key={'PK': f'JOURNEY#{journey_id}', 'SK': sk},
                UpdateExpression='SET #data.stepResults.#step_id = :step_result, #data.updatedAt = :updated_at',
                ExpressionAttributeNames={
                    '#data': 'Data',
                    '#step_id': step_id,
                },
                ExpressionAttributeValues={
                    ':step_result': step_result_converted,
                    ':updated_at': datetime.utcnow().isoformat() + 'Z',
                },
            )
        except Exception as e:
            self.logger.error(f'Error updating step results: {str(e)}')

    def _convert_floats_to_decimal(self, obj):
        """Recursively convert float values to Decimal for DynamoDB compatibility"""
        if isinstance(obj, dict):
            return {key: self._convert_floats_to_decimal(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        else:
            return obj

    def update_job_progress(
        self, journey_id: str, job_id: str, progress: float, current_step_index: int
    ):
        """Update job progress"""
        try:
            # Get job data to find correct SK
            job_data = self.get_job_execution(journey_id, job_id)
            if not job_data:
                raise Exception(f'Job {job_id} not found')

            # Build the SK
            stage_id = job_data['stageId']
            execution_number = job_data['executionNumber']
            timestamp = job_id.split('-')[-1]
            sk = f'JOB#{int(job_data["stageOrder"]):02d}#{stage_id}#{int(execution_number):03d}#{timestamp}'

            self.table.update_item(
                Key={'PK': f'JOURNEY#{journey_id}', 'SK': sk},
                UpdateExpression='SET #data.progress = :progress, #data.jobMetrics.overallProgress = :progress, #data.currentStepIndex = :step_index, #data.updatedAt = :updated_at',
                ExpressionAttributeNames={'#data': 'Data'},
                ExpressionAttributeValues={
                    ':progress': Decimal(str(progress)),
                    ':step_index': current_step_index,
                    ':updated_at': datetime.utcnow().isoformat() + 'Z',
                },
            )
        except Exception as e:
            self.logger.error(f'Error updating job progress: {str(e)}')

    def complete_job(self, journey_id: str, job_id: str):
        """Mark job as completed"""
        try:
            # Get job data
            job_data = self.get_job_execution(journey_id, job_id)
            if not job_data:
                raise Exception(f'Job {job_id} not found')

            # Build the SK
            stage_id = job_data['stageId']
            execution_number = job_data['executionNumber']
            timestamp = job_id.split('-')[-1]
            sk = f'JOB#{int(job_data["stageOrder"]):02d}#{stage_id}#{int(execution_number):03d}#{timestamp}'

            # Calculate duration
            from datetime import timezone
            start_time = datetime.fromisoformat(job_data['startTime'].replace('Z', '+00:00'))
            end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
            duration_seconds = (end_time - start_time).total_seconds()
            duration_str = f'{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s'

            # Update job record
            self.table.update_item(
                Key={'PK': f'JOURNEY#{journey_id}', 'SK': sk},
                UpdateExpression='SET #data.#status = :status, #data.endTime = :end_time, #data.#duration = :duration, #data.progress = :progress, #data.updatedAt = :updated_at',
                ExpressionAttributeNames={
                    '#data': 'Data',
                    '#status': 'status',
                    '#duration': 'duration',
                },
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':end_time': end_time.isoformat() + 'Z',
                    ':duration': duration_str,
                    ':progress': Decimal('100'),
                    ':updated_at': datetime.utcnow().isoformat() + 'Z',
                },
            )

            # Update journey aggregates
            self.update_journey_aggregates(journey_id, stage_id, 'completed')

        except Exception as e:
            self.logger.error(f'Error completing job: {str(e)}')

    def fail_job(self, journey_id: str, job_id: str, error_message: str):
        """Mark job as failed"""
        try:
            # Get job data
            job_data = self.get_job_execution(journey_id, job_id)
            if not job_data:
                raise Exception(f'Job {job_id} not found')

            # Build the SK
            stage_id = job_data['stageId']
            execution_number = job_data['executionNumber']
            timestamp = job_id.split('-')[-1]
            sk = f'JOB#{int(job_data["stageOrder"]):02d}#{stage_id}#{int(execution_number):03d}#{timestamp}'

            # Update job record
            self.table.update_item(
                Key={'PK': f'JOURNEY#{journey_id}', 'SK': sk},
                UpdateExpression='SET #data.#status = :status, #data.endTime = :end_time, #data.errorMessage = :error_message, #data.updatedAt = :updated_at',
                ExpressionAttributeNames={
                    '#data': 'Data',
                    '#status': 'status',
                },
                ExpressionAttributeValues={
                    ':status': 'failed',
                    ':end_time': datetime.utcnow().isoformat() + 'Z',
                    ':error_message': error_message,
                    ':updated_at': datetime.utcnow().isoformat() + 'Z',
                },
            )

            # Update journey aggregates
            self.update_journey_aggregates(journey_id, stage_id, 'failed')

        except Exception as e:
            self.logger.error(f'Error failing job: {str(e)}')

    def update_journey_aggregates(self, journey_id: str, stage_id: str, status: str):
        """Update journey aggregate statistics"""
        try:
            # Update journey aggregates based on job completion
            if status == 'completed':
                self.table.update_item(
                    Key={'PK': f'JOURNEY#{journey_id}', 'SK': 'METADATA'},
                    UpdateExpression='ADD #data.aggregates.completedJobs :inc SET #data.aggregates.totalJobs = #data.aggregates.totalJobs + :inc, #data.stageSummary.#stage_id.totalExecutions = #data.stageSummary.#stage_id.totalExecutions + :inc, #data.stageSummary.#stage_id.lastStatus = :status, #data.updatedAt = :updated_at',
                    ExpressionAttributeNames={
                        '#data': 'Data',
                        '#stage_id': stage_id,
                    },
                    ExpressionAttributeValues={
                        ':inc': 1,
                        ':status': status,
                        ':updated_at': datetime.utcnow().isoformat() + 'Z',
                    },
                )
            elif status == 'failed':
                self.table.update_item(
                    Key={'PK': f'JOURNEY#{journey_id}', 'SK': 'METADATA'},
                    UpdateExpression='ADD #data.aggregates.failedJobs :inc SET #data.aggregates.totalJobs = #data.aggregates.totalJobs + :inc, #data.stageSummary.#stage_id.totalExecutions = #data.stageSummary.#stage_id.totalExecutions + :inc, #data.stageSummary.#stage_id.lastStatus = :status, #data.updatedAt = :updated_at',
                    ExpressionAttributeNames={
                        '#data': 'Data',
                        '#stage_id': stage_id,
                    },
                    ExpressionAttributeValues={
                        ':inc': 1,
                        ':status': status,
                        ':updated_at': datetime.utcnow().isoformat() + 'Z',
                    },
                )
        except Exception as e:
            self.logger.error(f'Error updating journey aggregates: {str(e)}')
