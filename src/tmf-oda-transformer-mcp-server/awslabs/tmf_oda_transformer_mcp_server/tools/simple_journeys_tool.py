# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simple Journeys MCP Tool - Following the exact pattern from manage_journey.py"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from decimal import Decimal

from loguru import logger
from mcp.server.fastmcp import Context
from pydantic import Field
from typing import Annotated

from .base import BaseToolMixin


class SimpleJourneysService:
    """Simple service that follows the exact pattern from manage_journey.py"""
    
    def __init__(self):
        self.dynamodb = None
        self.table = None
        self.setup_aws_client()
        
    def setup_aws_client(self):
        """Set up AWS DynamoDB client following manage_journey.py pattern"""
        try:
            logger.info('🔗 Setting up AWS DynamoDB client...')
            
            # Import AWS client utilities
            import os
            import sys
            import boto3
            current_dir = os.path.dirname(os.path.abspath(__file__))
            scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            
            try:
                from aws_client_utils import create_aws_resource
                
                role_arn = os.environ.get('AWS_ROLE_ARN')
                if role_arn:
                    logger.info(f'🔑 Using role ARN: {role_arn}')
                    self.dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                else:
                    logger.info('🔑 Using default credential chain')
                    self.dynamodb = boto3.resource('dynamodb')
            except ImportError:
                logger.warning('aws_client_utils not found, using default boto3')
                self.dynamodb = boto3.resource('dynamodb')
            
            self.table = self.dynamodb.Table('TransformationSystem')
            logger.info('✅ AWS DynamoDB client ready')
            
        except Exception as e:
            logger.error(f'❌ Failed to setup AWS client: {str(e)}')
            raise
    
    def clean_journey_id(self, journey_id: str) -> str:
        """Clean journey ID by removing JRN- prefix if present"""
        return journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
    
    def validate_journey_exists(self, journey_id: str) -> bool:
        """Validate that a journey exists in DynamoDB"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            response = self.table.get_item(
                Key={
                    'PK': f'JOURNEY#{clean_id}',
                    'SK': 'METADATA'
                }
            )
            return 'Item' in response
        except Exception:
            return False
    
    def convert_floats_to_decimal(self, data: Any) -> Any:
        """Convert floats to Decimal for DynamoDB"""
        if isinstance(data, dict):
            return {k: self.convert_floats_to_decimal(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.convert_floats_to_decimal(item) for item in data]
        elif isinstance(data, float):
            return Decimal(str(data))
        else:
            return data
    
    def create_journey_complete(self, journey_data: Dict[str, Any], include_default_stages: bool = True) -> Optional[str]:
        """Create a complete journey with stages following manage_journey.py pattern"""
        try:
            # Generate journey ID
            journey_id = f'JRN-{str(uuid.uuid4()).upper().replace("-", "")[:12]}'
            
            logger.info(f'Creating complete journey: {journey_id}')
            logger.info(f'include_default_stages: {include_default_stages}')
            logger.info(f'journey_data: {journey_data}')
            
            # Validate required fields
            required_fields = ['name', 'description', 'odaComponentType']
            for field in required_fields:
                if field not in journey_data:
                    logger.error(f'Missing required field: {field}')
                    return None
            
            # Create journey metadata
            logger.info('Creating journey metadata...')
            if not self.create_journey_metadata(journey_id, journey_data):
                logger.error('Failed to create journey metadata')
                return None
            
            # Add default stages if requested
            stages_count = 0
            if include_default_stages:
                logger.info('Adding default stages...')
                stages_count = self.add_default_stages_complete(journey_id)
                logger.info(f'add_default_stages_complete returned: {stages_count}')
            else:
                logger.info('Skipping default stages creation')
            
            logger.info(f'Complete journey created successfully: {journey_id} with {stages_count} stages')
            return journey_id
            
        except Exception as e:
            logger.error(f'Error creating complete journey: {str(e)}')
            logger.exception('Full exception details:')
            return None
    
    def create_journey_metadata(self, journey_id: str, journey_data: Dict[str, Any]) -> bool:
        """Create journey metadata following manage_journey.py pattern"""
        try:
            # Convert floats to Decimal
            journey_data = self.convert_floats_to_decimal(journey_data)
            
            clean_id = self.clean_journey_id(journey_id)
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            journey_item = {
                'PK': f'JOURNEY#{clean_id}',
                'SK': 'METADATA',
                'EntityType': 'Journey',
                'GSI1PK': 'JOURNEYS',
                'GSI1SK': timestamp,
                'CreatedAt': timestamp,
                'UpdatedAt': timestamp,
                'Data': {
                    'journeyId': journey_id,
                    'name': journey_data['name'],
                    'description': journey_data['description'],
                    'status': journey_data.get('status', 'pending'),
                    'createdBy': journey_data.get('createdBy', 'mcp-server'),
                    'priority': journey_data.get('priority', 'medium'),
                    'odaComponentType': journey_data['odaComponentType'],
                    'currentStageIndex': 0,
                    'currentStageId': 'raw_analysis',
                    'overallProgress': 0
                }
            }
            
            self.table.put_item(Item=journey_item)
            logger.info(f'Journey metadata created: {journey_id}')
            return True
            
        except Exception as e:
            logger.error(f'Error creating journey metadata: {str(e)}')
            return False
    
    def add_default_stages_complete(self, journey_id: str) -> int:
        """Add all default stages to a journey following manage_journey.py pattern"""
        # Import stage registry to get actual step definitions
        from ..scripts.stages import get_stage_class
        
        def get_stage_steps(stage_id):
            """Get steps from stage class"""
            stage_class = get_stage_class(stage_id)
            if stage_class:
                temp_stage = stage_class('temp', stage_id, 'temp', 'us-east-1', None)
                return temp_stage.steps
            return []
        
        try:
            logger.info(f'Starting add_default_stages_complete for journey: {journey_id}')
            
            default_stages = [
                {
                    'stageId': 'raw_analysis',
                    'name': 'Raw Input Analysis',
                    'description': 'Analyze the raw database schema and structure',
                    'order': 0,
                    'estimatedDuration': '15m',
                    'canSkip': False,
                    'secondBrainEnabled': True,
                    'ruleTypes': ['field_mapping', 'contextual_recommendations'],
                    'steps': get_stage_steps('raw_analysis')
                },
                {
                    'stageId': 'stripped_schema',
                    'name': 'Create Stripped Document',
                    'description': 'Create TMF-focused simplified schema',
                    'order': 1,
                    'estimatedDuration': '12m',
                    'canSkip': False,
                    'secondBrainEnabled': True,
                    'ruleTypes': ['field_mapping', 'data_interpretation'],
                    'steps': get_stage_steps('stripped_schema')
                },
                {
                    'stageId': 'tmf_mapping',
                    'name': 'TMF Schema Mapping',
                    'description': 'Map the stripped schema to TMF ODA standards',
                    'order': 2,
                    'estimatedDuration': '20m',
                    'canSkip': False,
                    'secondBrainEnabled': True,
                    'ruleTypes': ['field_mapping', 'contextual_recommendations'],
                    'steps': get_stage_steps('tmf_mapping')
                },
                {
                    'stageId': 'migration_planning',
                    'name': 'Data Migration Planning',
                    'description': 'Plan and prepare data migration strategies',
                    'order': 3,
                    'estimatedDuration': '18m',
                    'canSkip': False,
                    'secondBrainEnabled': True,
                    'ruleTypes': ['contextual_recommendations'],
                    'steps': get_stage_steps('migration_planning')
                },
                {
                    'stageId': 'data_migration',
                    'name': 'Data Migration',
                    'description': 'Execute actual data migration',
                    'order': 4,
                    'estimatedDuration': '25m',
                    'canSkip': False,
                    'secondBrainEnabled': True,
                    'ruleTypes': ['contextual_recommendations'],
                    'steps': get_stage_steps('data_migration')
                },
                {
                    'stageId': 'verification_validation',
                    'name': 'Verification & Validation',
                    'description': 'Validate mapping and migration results',
                    'order': 5,
                    'estimatedDuration': '22m',
                    'canSkip': False,
                    'secondBrainEnabled': True,
                    'ruleTypes': ['contextual_recommendations', 'validation_rules'],
                    'steps': get_stage_steps('verification_validation')
                }
            ]
            
            logger.info(f'Default stages defined: {len(default_stages)} stages')
            
            successful_adds = 0
            for i, stage in enumerate(default_stages):
                logger.info(f'Adding stage {i+1}/{len(default_stages)}: {stage["stageId"]}')
                if self.add_stage(journey_id, stage):
                    successful_adds += 1
                    logger.info(f'Stage {stage["stageId"]} added successfully')
                else:
                    logger.error(f'Failed to add stage {stage["stageId"]}')
            
            logger.info(f'Added {successful_adds}/{len(default_stages)} default stages')
            return successful_adds
            
        except Exception as e:
            logger.error(f'Error adding default stages: {str(e)}')
            logger.exception('Full exception details:')
            return 0
    
    def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> bool:
        """Add a stage to a journey following manage_journey.py pattern"""
        try:
            logger.info(f'Starting add_stage for journey: {journey_id}, stage: {stage_data.get("stageId")}')
            
            clean_id = self.clean_journey_id(journey_id)
            logger.info(f'Clean journey ID: {clean_id}')
            
            if not self.validate_journey_exists(clean_id):
                logger.error(f'Journey not found: {clean_id}')
                return False
            
            logger.info('Journey exists - proceeding with stage creation')
            
            # Validate required fields
            required_fields = ['stageId', 'name', 'description']
            for field in required_fields:
                if field not in stage_data:
                    logger.error(f'Missing required field: {field}')
                    return False
            
            logger.info('All required fields present')
            
            stage_id = stage_data['stageId']
            
            # Convert floats to Decimal
            stage_data = self.convert_floats_to_decimal(stage_data)
            
            # Get current stages to determine order
            existing_stages = self.list_stages(journey_id)
            stage_order = stage_data.get('order', len(existing_stages))
            
            logger.info(f'Existing stages count: {len(existing_stages)}, stage order: {stage_order}')
            
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            stage_item = {
                'PK': f'JOURNEY#{clean_id}',
                'SK': f'STAGE#{int(stage_order):02d}#{stage_id}',
                'EntityType': 'StageDefinition',
                'GSI1PK': f'JOURNEY#{clean_id}#STAGES',
                'GSI1SK': f'{int(stage_order):02d}',
                'CreatedAt': timestamp,
                'UpdatedAt': timestamp,
                'Data': {
                    'stageId': stage_id,
                    'name': stage_data['name'],
                    'description': stage_data['description'],
                    'order': stage_order,
                    'canSkip': stage_data.get('canSkip', False),
                    'estimatedDuration': stage_data.get('estimatedDuration', '10m'),
                    'status': stage_data.get('status', 'pending'),
                    'secondBrainEnabled': stage_data.get('secondBrainEnabled', True),
                    'ruleTypes': stage_data.get('ruleTypes', ['contextual_recommendations']),
                    'steps': stage_data.get('steps', [])
                }
            }
            
            logger.info(f'Stage item prepared: PK={stage_item["PK"]}, SK={stage_item["SK"]}')
            
            self.table.put_item(Item=stage_item)
            logger.info(f'Stage added to DynamoDB: {stage_id}')
            return True
            
        except Exception as e:
            logger.error(f'Error adding stage: {str(e)}')
            logger.exception('Full exception details:')
            return False
    
    def list_stages(self, journey_id: str) -> List[Dict]:
        """List all stages for a journey following manage_journey.py pattern"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            
            if not self.validate_journey_exists(clean_id):
                return []
            
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'JOURNEY#{clean_id}#STAGES'
                }
            )
            
            stages = []
            for item in response['Items']:
                stage_data = item['Data']
                stages.append({
                    'stageId': stage_data.get('stageId'),
                    'name': stage_data.get('name'),
                    'description': stage_data.get('description'),
                    'order': stage_data.get('order'),
                    'canSkip': stage_data.get('canSkip'),
                    'estimatedDuration': stage_data.get('estimatedDuration'),
                    'status': stage_data.get('status', 'pending'),
                    'secondBrainEnabled': stage_data.get('secondBrainEnabled', False),
                    'ruleTypes': stage_data.get('ruleTypes', []),
                    'steps': stage_data.get('steps', [])
                })
            
            # Sort by order
            stages.sort(key=lambda x: x.get('order', 0))
            return stages
            
        except Exception as e:
            logger.error(f'Error listing stages: {str(e)}')
            return []


class SimpleJourneysTool(BaseToolMixin):
    """Simple journeys MCP tool following manage_journey.py pattern"""

    def __init__(self):
        super().__init__()
        # Initialize the simple service
        try:
            self.service = SimpleJourneysService()
            logger.info("SimpleJourneysTool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SimpleJourneysTool: {str(e)}")
            logger.exception('Full exception details:')
            self.service = None

    def get_tool_definition(self):
        """Get the tool definition for the simple journeys tool"""
        return {
            "name": "simple-journeys",
            "description": "Simple journey management tool following manage_journey.py pattern",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["create", "list-stages"]
                    },
                    "journey_data": {
                        "type": "object",
                        "description": "Journey data for create action",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "odaComponentType": {"type": "string"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                            "include_default_stages": {"type": "boolean", "default": True}
                        }
                    },
                    "journey_id": {
                        "type": "string",
                        "description": "Journey ID for operations"
                    }
                },
                "required": ["action"]
            }
        }

    async def execute(self, ctx: Context, action: str, journey_data: Optional[Dict[str, Any]] = None, journey_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute the simple journeys tool"""
        start_time = datetime.now()
        
        try:
            if not self.service:
                raise Exception("SimpleJourneysService not initialized")
                
            if action == "create":
                if not journey_data:
                    raise Exception("journey_data is required for create action")
                
                include_default_stages = journey_data.get('include_default_stages', True)
                
                # Create the journey
                journey_id = self.service.create_journey_complete(journey_data, include_default_stages)
                
                if not journey_id:
                    raise Exception("Failed to create journey")
                
                # Get the stages count
                stages = self.service.list_stages(journey_id)
                stages_count = len(stages)
                
                return self.create_tool_result(
                    status='success',
                    message=f'Journey {journey_id} created successfully with {stages_count} stages',
                    start_time=start_time,
                    operation='create_journey',
                    journey_id=journey_id,
                    stages_count=stages_count,
                    default_stages_created=include_default_stages
                )
                
            elif action == "list-stages":
                if not journey_id:
                    raise Exception("journey_id is required for list-stages action")
                
                stages = self.service.list_stages(journey_id)
                
                return self.create_tool_result(
                    status='success',
                    message=f'Retrieved {len(stages)} stages for journey {journey_id}',
                    start_time=start_time,
                    operation='list_stages',
                    journey_id=journey_id,
                    total_stages=len(stages),
                    stages=stages
                )
                
            else:
                raise Exception(f"Unknown action: {action}")
                
        except Exception as e:
            return self.create_tool_result(
                status='error',
                message=f'Simple journeys operation failed: {str(e)}',
                start_time=start_time,
                operation=action,
                journey_id=journey_id
            )


# Create the tool instance
simple_journeys_tool = SimpleJourneysTool() 