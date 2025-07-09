# job_executor.py (continued)
# job_executor.py
import boto3
import json
import logging
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List


class TransformationJobExecutor:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.table = self.dynamodb.Table('TransformationSystem')
        self.logs_bucket = 'transformation-journey-logs'
        self.reports_bucket = 'transformation-journey-reports'

        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

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
                    'progress': 0,
                    'triggeredBy': triggered_by,
                    'triggerReason': reason,
                    'retryAttempt': 0,
                    's3Config': {
                        'logsBucket': self.logs_bucket,
                        'logsPrefix': f'journeys/{journey_id}/stages/{stage_id}/executions/{job_id}/',
                        'reportsBucket': self.reports_bucket,
                        'reportsPrefix': f'journeys/{journey_id}/stages/{stage_id}/executions/{job_id}/',
                        'region': 'us-east-1',
                    },
                    'currentStepIndex': 0,
                    'currentStepId': stage_def['steps'][0]['id'],
                    'stepResults': {
                        step['id']: {'status': 'pending', 'progress': 0}
                        for step in stage_def['steps']
                    },
                    'jobMetrics': {
                        'totalLogs': 0,
                        'totalErrors': 0,
                        'totalWarnings': 0,
                        'overallProgress': 0,
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
        """Execute all steps in a job"""
        try:
            # Get job data
            job_data = self.get_job_execution(journey_id, job_id)
            if not job_data:
                raise Exception(f'Job {job_id} not found')

            stage_def = self.get_stage_definition(journey_id, job_data['stageId'])
            steps = stage_def['steps']

            self.logger.info(f'🚀 Executing job {job_id} with {len(steps)} steps')

            # Execute each step
            for step_index, step in enumerate(steps):
                step_id = step['id']
                self.logger.info(f'📝 Starting step {step_index + 1}/{len(steps)}: {step["name"]}')

                # Update step to in_progress
                self.update_step_status(journey_id, job_id, step_id, 'in_progress', step_index)

                # Execute step
                step_result = self.execute_step(job_data, step, step_index)

                # Update step with results
                self.update_step_results(journey_id, job_id, step_id, step_result)

                # Update job progress
                progress = ((step_index + 1) / len(steps)) * 100
                self.update_job_progress(journey_id, job_id, progress, step_index + 1)

                self.logger.info(f'✅ Completed step: {step["name"]}')

            # Complete the job
            self.complete_job(journey_id, job_id)
            self.logger.info(f'🎉 Job {job_id} completed successfully')

        except Exception as e:
            self.logger.error(f'❌ Error executing job {job_id}: {str(e)}')
            self.fail_job(journey_id, job_id, str(e))
            raise

    def execute_step(self, job_data: Dict, step: Dict, step_index: int) -> Dict:
        """Execute a single step and return results"""
        step_id = step['id']
        job_id = job_data['jobId']
        journey_id = job_data['journeyId']
        stage_id = job_data['stageId']

        start_time = datetime.utcnow()
        logs = []

        try:
            # Log step start
            logs.append(
                self.create_log_entry(
                    'INFO', f'Starting step: {step["name"]}', job_id, journey_id, stage_id, step_id
                )
            )

            # Simulate step execution based on step type
            if step_id == 'schema_parsing':
                result = self.execute_schema_parsing(logs, job_id, journey_id, stage_id, step_id)
            elif step_id == 'relationship_discovery':
                result = self.execute_relationship_discovery(
                    logs, job_id, journey_id, stage_id, step_id
                )
            elif step_id == 'data_type_analysis':
                result = self.execute_data_type_analysis(
                    logs, job_id, journey_id, stage_id, step_id
                )
            elif step_id == 'tmf_relevance_filtering':
                result = self.execute_tmf_filtering(logs, job_id, journey_id, stage_id, step_id)
            elif step_id == 'simplified_schema_creation':
                result = self.execute_schema_creation(logs, job_id, journey_id, stage_id, step_id)
            else:
                result = self.execute_generic_step(
                    step, logs, job_id, journey_id, stage_id, step_id
                )

            end_time = datetime.utcnow()
            duration = str(end_time - start_time)

            # Log step completion
            logs.append(
                self.create_log_entry(
                    'SUCCESS',
                    f'Step completed: {step["name"]}',
                    job_id,
                    journey_id,
                    stage_id,
                    step_id,
                    metadata=result.get('metrics', {}),
                )
            )

            # Store logs in S3
            self.store_step_logs(job_data, step_id, logs)

            # Generate and store step report
            report = self.generate_step_report(step, result, logs, start_time, end_time)
            self.store_step_report(job_data, step_id, report)

            return {
                'status': 'completed',
                'startTime': start_time.isoformat() + 'Z',
                'endTime': end_time.isoformat() + 'Z',
                'duration': duration,
                'progress': 100,
                'logSummary': {
                    'totalLogs': len(logs),
                    'infoLogs': len([l for l in logs if l['level'] == 'INFO']),
                    'warnLogs': len([l for l in logs if l['level'] == 'WARN']),
                    'errorLogs': len([l for l in logs if l['level'] == 'ERROR']),
                    'successLogs': len([l for l in logs if l['level'] == 'SUCCESS']),
                },
                'metrics': result.get('metrics', {}),
                'summary': result.get('summary', {}),
                's3Pointers': {
                    'logsKey': f'journeys/{journey_id}/stages/{stage_id}/executions/{job_id}/logs/{step_id}.json',
                    'reportKey': f'journeys/{journey_id}/stages/{stage_id}/executions/{job_id}/reports/{step_id}.json',
                },
            }

        except Exception as e:
            end_time = datetime.utcnow()
            logs.append(
                self.create_log_entry(
                    'ERROR', f'Step failed: {str(e)}', job_id, journey_id, stage_id, step_id
                )
            )

            # Store error logs
            self.store_step_logs(job_data, step_id, logs)

            return {
                'status': 'failed',
                'startTime': start_time.isoformat() + 'Z',
                'endTime': end_time.isoformat() + 'Z',
                'duration': str(end_time - start_time),
                'progress': 0,
                'errorMessage': str(e),
                'logSummary': {'totalLogs': len(logs), 'errorLogs': 1},
            }

    def execute_schema_parsing(
        self, logs: List, job_id: str, journey_id: str, stage_id: str, step_id: str
    ) -> Dict:
        """Simulate schema parsing step execution"""
        logs.append(
            self.create_log_entry(
                'INFO',
                'Loading schema file: sample_schema.sql',
                job_id,
                journey_id,
                stage_id,
                step_id,
                metadata={'fileName': 'sample_schema.sql', 'fileSizeMB': 25},
            )
        )

        time.sleep(2)  # Simulate processing time

        logs.append(
            self.create_log_entry(
                'INFO', 'Parsing SQL statements...', job_id, journey_id, stage_id, step_id
            )
        )

        time.sleep(3)

        logs.append(
            self.create_log_entry(
                'WARN',
                'Found legacy data type: MONEY',
                job_id,
                journey_id,
                stage_id,
                step_id,
                metadata={'legacyType': 'MONEY', 'modernEquivalent': 'DECIMAL'},
            )
        )

        time.sleep(2)

        return {
            'metrics': {
                'tablesProcessed': 125,
                'columnsProcessed': 1547,
                'constraintsFound': 89,
                'filesProcessed': 1,
                'fileSizeMB': 25,
            },
            'summary': {
                'success': True,
                'primaryMessage': 'Schema parsing completed successfully',
                'keyAchievements': [
                    'Parsed 125 tables',
                    'Identified 1547 columns',
                    'Found 89 constraints',
                ],
            },
        }

    def execute_relationship_discovery(
        self, logs: List, job_id: str, journey_id: str, stage_id: str, step_id: str
    ) -> Dict:
        """Simulate relationship discovery step execution"""
        logs.append(
            self.create_log_entry(
                'INFO',
                'Analyzing foreign key constraints...',
                job_id,
                journey_id,
                stage_id,
                step_id,
            )
        )
        time.sleep(2)

        logs.append(
            self.create_log_entry(
                'INFO', 'Building dependency graph...', job_id, journey_id, stage_id, step_id
            )
        )
        time.sleep(3)

        logs.append(
            self.create_log_entry(
                'INFO',
                'Checking for circular dependencies...',
                job_id,
                journey_id,
                stage_id,
                step_id,
            )
        )
        time.sleep(1)

        return {
            'metrics': {
                'relationshipsFound': 67,
                'foreignKeysAnalyzed': 45,
                'dependencyGraphNodes': 125,
                'circularDependencies': 0,
            },
            'summary': {
                'success': True,
                'primaryMessage': 'Relationship discovery completed',
                'keyAchievements': [
                    'Discovered 67 table relationships',
                    'Analyzed 45 foreign key constraints',
                    'Built complete dependency graph',
                ],
            },
        }

    def execute_data_type_analysis(
        self, logs: List, job_id: str, journey_id: str, stage_id: str, step_id: str
    ) -> Dict:
        """Simulate data type analysis step execution"""
        logs.append(
            self.create_log_entry(
                'INFO', 'Analyzing column data types...', job_id, journey_id, stage_id, step_id
            )
        )
        time.sleep(2)

        logs.append(
            self.create_log_entry(
                'WARN',
                'Found deprecated data type usage',
                job_id,
                journey_id,
                stage_id,
                step_id,
                metadata={'deprecatedTypes': ['TEXT', 'MONEY']},
            )
        )
        time.sleep(1)

        return {
            'metrics': {
                'columnsAnalyzed': 1547,
                'uniqueDataTypes': 23,
                'legacyTypesFound': 8,
                'constraintsAnalyzed': 89,
            },
            'summary': {
                'success': True,
                'primaryMessage': 'Data type analysis completed',
                'keyAchievements': [
                    'Analyzed 1547 columns',
                    'Identified 23 unique data types',
                    'Found 8 legacy types requiring migration',
                ],
            },
        }

    def execute_tmf_filtering(
        self, logs: List, job_id: str, journey_id: str, stage_id: str, step_id: str
    ) -> Dict:
        """Simulate TMF relevance filtering step execution"""
        logs.append(
            self.create_log_entry(
                'INFO',
                'Applying TMF Customer Management filters...',
                job_id,
                journey_id,
                stage_id,
                step_id,
            )
        )
        time.sleep(3)

        logs.append(
            self.create_log_entry(
                'INFO',
                'Evaluating table relevance scores...',
                job_id,
                journey_id,
                stage_id,
                step_id,
            )
        )
        time.sleep(2)

        return {
            'metrics': {
                'tablesEvaluated': 125,
                'tmfRelevantTables': 34,
                'customerRelatedTables': 28,
                'supportingTables': 6,
            },
            'summary': {
                'success': True,
                'primaryMessage': 'TMF filtering completed',
                'keyAchievements': [
                    'Identified 34 TMF-relevant tables',
                    '28 customer-related core tables',
                    '6 supporting reference tables',
                ],
            },
        }

    def execute_schema_creation(
        self, logs: List, job_id: str, journey_id: str, stage_id: str, step_id: str
    ) -> Dict:
        """Simulate simplified schema creation step execution"""
        logs.append(
            self.create_log_entry(
                'INFO',
                'Creating simplified schema structure...',
                job_id,
                journey_id,
                stage_id,
                step_id,
            )
        )
        time.sleep(2)

        logs.append(
            self.create_log_entry(
                'INFO',
                'Optimizing for TMF compatibility...',
                job_id,
                journey_id,
                stage_id,
                step_id,
            )
        )
        time.sleep(3)

        return {
            'metrics': {
                'simplifiedTables': 34,
                'columnsRetained': 456,
                'relationshipsPreserved': 28,
                'tmfCompatibilityScore': 92,
            },
            'summary': {
                'success': True,
                'primaryMessage': 'Simplified schema created',
                'keyAchievements': [
                    'Created 34-table simplified schema',
                    'Retained 456 essential columns',
                    'Achieved 92% TMF compatibility',
                ],
            },
        }

    def execute_generic_step(
        self, step: Dict, logs: List, job_id: str, journey_id: str, stage_id: str, step_id: str
    ) -> Dict:
        """Execute a generic step"""
        logs.append(
            self.create_log_entry(
                'INFO', f'Processing {step["name"]}...', job_id, journey_id, stage_id, step_id
            )
        )
        time.sleep(3)

        return {
            'metrics': {'itemsProcessed': 100},
            'summary': {
                'success': True,
                'primaryMessage': f'{step["name"]} completed',
                'keyAchievements': ['Step completed successfully'],
            },
        }

    def create_log_entry(
        self,
        level: str,
        message: str,
        job_id: str,
        journey_id: str,
        stage_id: str,
        step_id: str,
        details: str = None,
        metadata: Dict = None,
    ) -> Dict:
        """Create a structured log entry"""
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'jobId': job_id,
            'journeyId': journey_id,
            'stageId': stage_id,
            'stepId': step_id,
            'message': message,
            'details': details,
            'metadata': metadata or {},
            'requestId': str(uuid.uuid4())[:8],
        }

    def store_step_logs(self, job_data: Dict, step_id: str, logs: List):
        """Store step logs in S3"""
        logs_key = f'journeys/{job_data["journeyId"]}/stages/{job_data["stageId"]}/executions/{job_data["jobId"]}/logs/{step_id}.json'

        try:
            self.s3.put_object(
                Bucket=self.logs_bucket,
                Key=logs_key,
                Body=json.dumps(logs, indent=2),
                ContentType='application/json',
            )
            self.logger.info(
                f'📄 Stored logs for step {step_id} at s3://{self.logs_bucket}/{logs_key}'
            )
        except Exception as e:
            self.logger.error(f'❌ Error storing logs: {str(e)}')

    def store_step_report(self, job_data: Dict, step_id: str, report: Dict):
        """Store step report in S3"""
        report_key = f'journeys/{job_data["journeyId"]}/stages/{job_data["stageId"]}/executions/{job_data["jobId"]}/reports/{step_id}.json'

        try:
            self.s3.put_object(
                Bucket=self.reports_bucket,
                Key=report_key,
                Body=json.dumps(report, indent=2),
                ContentType='application/json',
            )
            self.logger.info(
                f'📊 Stored report for step {step_id} at s3://{self.reports_bucket}/{report_key}'
            )
        except Exception as e:
            self.logger.error(f'❌ Error storing report: {str(e)}')

    def generate_step_report(
        self, step: Dict, result: Dict, logs: List, start_time: datetime, end_time: datetime
    ) -> Dict:
        """Generate a comprehensive step report"""
        return {
            'stepId': step['id'],
            'stepName': step['name'],
            'description': step['description'],
            'execution': {
                'startTime': start_time.isoformat() + 'Z',
                'endTime': end_time.isoformat() + 'Z',
                'duration': str(end_time - start_time),
                'status': result.get('status', 'completed'),
            },
            'metrics': result.get('metrics', {}),
            'summary': result.get('summary', {}),
            'logAnalysis': {
                'totalLogs': len(logs),
                'logLevels': {
                    'info': len([l for l in logs if l['level'] == 'INFO']),
                    'warn': len([l for l in logs if l['level'] == 'WARN']),
                    'error': len([l for l in logs if l['level'] == 'ERROR']),
                    'success': len([l for l in logs if l['level'] == 'SUCCESS']),
                },
                'keyEvents': [l['message'] for l in logs if l['level'] in ['SUCCESS', 'ERROR']],
            },
            'recommendations': self.generate_recommendations(step['id'], result),
            'generatedAt': datetime.utcnow().isoformat() + 'Z',
        }

    def generate_recommendations(self, step_id: str, result: Dict) -> List[str]:
        """Generate recommendations based on step results"""
        recommendations = []

        if step_id == 'schema_parsing':
            if result.get('metrics', {}).get('legacyTypesFound', 0) > 0:
                recommendations.append('Consider modernizing legacy data types before TMF mapping')
        elif step_id == 'relationship_discovery':
            if result.get('metrics', {}).get('circularDependencies', 0) > 0:
                recommendations.append('Resolve circular dependencies before proceeding')

        recommendations.append('Proceed to next step')
        return recommendations

    # Helper methods for DynamoDB operations
    def get_journey(self, journey_id: str) -> Dict:
        """Get journey metadata"""
        try:
            response = self.table.get_item(Key={'PK': f'JOURNEY#{journey_id}', 'SK': 'METADATA'})
            return response.get('Item', {}).get('Data')
        except Exception as e:
            self.logger.error(f'Error getting journey: {str(e)}')
            return None

    def get_stage_definition(self, journey_id: str, stage_id: str) -> Dict:
        """Get stage definition"""
        try:
            # Query for stage by stage_id
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'JOURNEY#{journey_id}',
                    ':sk_prefix': 'STAGE#',
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
        """Update journey with current job information"""
        try:
            self.table.update_item(
                Key={'PK': f'JOURNEY#{journey_id}', 'SK': 'METADATA'},
                UpdateExpression='SET #data.currentJobs.#stage_id = :job_info, #data.stageSummary.#stage_id.lastJobId = :job_id, #data.stageSummary.#stage_id.totalExecutions = #data.stageSummary.#stage_id.totalExecutions + :inc, #data.stageSummary.#stage_id.lastStatus = :status, #data.aggregates.totalJobs = #data.aggregates.totalJobs + :inc, UpdatedAt = :updated_at',
                ExpressionAttributeNames={'#data': 'Data', '#stage_id': stage_id},
                ExpressionAttributeValues={
                    ':job_info': {
                        'jobId': job_id,
                        'executionNumber': execution_number,
                        'status': 'in_progress',
                        'startTime': datetime.utcnow().isoformat() + 'Z',
                    },
                    ':job_id': job_id,
                    ':status': 'in_progress',
                    ':inc': 1,
                    ':updated_at': datetime.utcnow().isoformat() + 'Z',
                },
            )
        except Exception as e:
            self.logger.error(f'Error updating journey current job: {str(e)}')

    def update_step_status(
        self, journey_id: str, job_id: str, step_id: str, status: str, step_index: int
    ):
        """Update step status in job execution"""
        try:
            # Find and update the job item
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
                item = response['Items'][0]
                self.table.update_item(
                    Key={'PK': item['PK'], 'SK': item['SK']},
                    UpdateExpression='SET #data.stepResults.#step_id.#status = :status, #data.currentStepIndex = :step_index, #data.currentStepId = :step_id, #data.stepResults.#step_id.startTime = :start_time, UpdatedAt = :updated_at',
                    ExpressionAttributeNames={
                        '#data': 'Data',
                        '#step_id': step_id,
                        '#status': 'status',
                    },
                    ExpressionAttributeValues={
                        ':status': status,
                        ':step_index': step_index,
                        ':step_id': step_id,
                        ':start_time': datetime.utcnow().isoformat() + 'Z',
                        ':updated_at': datetime.utcnow().isoformat() + 'Z',
                    },
                )
        except Exception as e:
            self.logger.error(f'Error updating step status: {str(e)}')

    def update_step_results(self, journey_id: str, job_id: str, step_id: str, step_result: Dict):
        """Update step results in job execution"""
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
                item = response['Items'][0]
                self.table.update_item(
                    Key={'PK': item['PK'], 'SK': item['SK']},
                    UpdateExpression='SET #data.stepResults.#step_id = :step_result, UpdatedAt = :updated_at',
                    ExpressionAttributeNames={'#data': 'Data', '#step_id': step_id},
                    ExpressionAttributeValues={
                        ':step_result': step_result,
                        ':updated_at': datetime.utcnow().isoformat() + 'Z',
                    },
                )
        except Exception as e:
            self.logger.error(f'Error updating step results: {str(e)}')

    def update_job_progress(
        self, journey_id: str, job_id: str, progress: float, current_step_index: int
    ):
        """Update job progress"""
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
                item = response['Items'][0]
                self.table.update_item(
                    Key={'PK': item['PK'], 'SK': item['SK']},
                    UpdateExpression='SET #data.progress = :progress, #data.currentStepIndex = :step_index, #data.jobMetrics.overallProgress = :progress, UpdatedAt = :updated_at',
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
            end_time = datetime.utcnow().isoformat() + 'Z'

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
                item = response['Items'][0]
                start_time = datetime.fromisoformat(
                    item['Data']['startTime'].replace('Z', '+00:00')
                )
                end_time_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = str(end_time_dt - start_time)

                self.table.update_item(
                    Key={'PK': item['PK'], 'SK': item['SK']},
                    UpdateExpression='SET #data.#status = :status, #data.endTime = :end_time, #data.#duration = :duration, #data.progress = :progress, UpdatedAt = :updated_at',
                    ExpressionAttributeNames={
                        '#data': 'Data',
                        '#status': 'status',
                        '#duration': 'duration',
                    },
                    ExpressionAttributeValues={
                        ':status': 'completed',
                        ':end_time': end_time,
                        ':duration': duration,
                        ':progress': Decimal('100'),
                        ':updated_at': end_time,
                    },
                )

                # Update journey current job status
                stage_id = item['Data']['stageId']
                self.table.update_item(
                    Key={'PK': f'JOURNEY#{journey_id}', 'SK': 'METADATA'},
                    UpdateExpression='SET #data.currentJobs.#stage_id.#status = :status, #data.currentJobs.#stage_id.endTime = :end_time, #data.stageSummary.#stage_id.lastStatus = :status, #data.aggregates.completedJobs = #data.aggregates.completedJobs + :inc, UpdatedAt = :updated_at',
                    ExpressionAttributeNames={
                        '#data': 'Data',
                        '#stage_id': stage_id,
                        '#status': 'status',
                    },
                    ExpressionAttributeValues={
                        ':status': 'completed',
                        ':end_time': end_time,
                        ':inc': 1,
                        ':updated_at': end_time,
                    },
                )

        except Exception as e:
            self.logger.error(f'Error completing job: {str(e)}')

    def fail_job(self, journey_id: str, job_id: str, error_message: str):
        """Mark job as failed"""
        try:
            end_time = datetime.utcnow().isoformat() + 'Z'

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
                item = response['Items'][0]

                self.table.update_item(
                    Key={'PK': item['PK'], 'SK': item['SK']},
                    UpdateExpression='SET #data.#status = :status, #data.endTime = :end_time, #data.errorMessage = :error, UpdatedAt = :updated_at',
                    ExpressionAttributeNames={'#data': 'Data', '#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':end_time': end_time,
                        ':error': error_message,
                        ':updated_at': end_time,
                    },
                )

                # Update journey aggregates
                stage_id = item['Data']['stageId']
                self.table.update_item(
                    Key={'PK': f'JOURNEY#{journey_id}', 'SK': 'METADATA'},
                    UpdateExpression='SET #data.currentJobs.#stage_id.#status = :status, #data.stageSummary.#stage_id.lastStatus = :status, #data.aggregates.failedJobs = #data.aggregates.failedJobs + :inc, UpdatedAt = :updated_at',
                    ExpressionAttributeNames={
                        '#data': 'Data',
                        '#stage_id': stage_id,
                        '#status': 'status',
                    },
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':inc': 1,
                        ':updated_at': end_time,
                    },
                )

        except Exception as e:
            self.logger.error(f'Error failing job: {str(e)}')
