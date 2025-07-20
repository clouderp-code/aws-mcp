"""Simplified Journey Service - Direct DynamoDB operations for TMF ODA Transformer."""

import boto3
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

# Configure logging to use the same log file as the server
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Remove default handler and add file handler if not already configured
if not logger._core.handlers:
    logger.remove()
    
    # Add file handler
    log_file = LOG_DIR / f"mcp_server_{datetime.now().strftime('%Y-%m-%d')}.log"
    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
        rotation="100 MB",
        retention="30 days",
        catch=True
    )


class SimpleJourneyService:
    """Simplified journey service with direct DynamoDB operations."""

    def __init__(self):
        """Initialize the service with direct DynamoDB connection."""
        self._setup_dynamodb()
        logger.info("SimpleJourneyService initialized with direct DynamoDB connection")

    def _setup_dynamodb(self):
        """Setup DynamoDB connection."""
        try:
            # Try to import AWS client utilities
            current_dir = os.path.dirname(os.path.abspath(__file__))
            scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            
            try:
                from aws_client_utils import create_aws_resource
                role_arn = os.environ.get('AWS_ROLE_ARN')
                if role_arn:
                    self.dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                else:
                    self.dynamodb = boto3.resource('dynamodb')
            except ImportError:
                self.dynamodb = boto3.resource('dynamodb')
            
            self.table = self.dynamodb.Table('TransformationSystem')
            logger.info("✅ DynamoDB connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup DynamoDB: {str(e)}")
            raise

    def _clean_journey_id(self, journey_id: str) -> str:
        """Remove JRN- prefix if present to get clean ID for DynamoDB operations."""
        clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
        logger.debug(f"🧹 Cleaned journey ID: {journey_id} → {clean_id}")
        return clean_id

    async def list_journeys(self, limit: int = 50) -> Dict[str, Any]:
        """List all journeys from DynamoDB."""
        try:
            logger.info(f"📋 Listing journeys (limit: {limit})")
            
            # Scan for all journey metadata with pagination to get ALL records
            journeys = []
            scan_kwargs = {
                'FilterExpression': 'SK = :sk',
                'ExpressionAttributeValues': {':sk': 'METADATA'}
            }
            
            # Paginate through ALL results
            while True:
                response = self.table.scan(**scan_kwargs)
                
                for item in response.get('Items', []):
                    # Extract journey ID from PK (JOURNEY#{id})
                    pk = item.get('PK', '')
                    if pk.startswith('JOURNEY#'):
                        journey_id = pk.replace('JOURNEY#', '')
                        data = item.get('Data', {})
                        
                        journey = {
                            'journeyId': f'JRN-{journey_id}',  # Add JRN- prefix for API
                            **data  # Include ALL data from DynamoDB
                        }
                        journeys.append(journey)
                
                # Check if there are more items to scan
                if 'LastEvaluatedKey' not in response:
                    break
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            
            # Apply limit after getting all results
            total_journeys = len(journeys)
            if limit > 0:
                journeys = journeys[:limit]
            
            logger.info(f"✅ Found {len(journeys)} journeys (total: {total_journeys})")
            return {
                'journeys': journeys,
                'total_journeys': total_journeys,
                'limit': limit
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to list journeys: {str(e)}")
            raise

    async def get_journey(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific journey by ID."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"🔍 Getting journey: {journey_id} (clean_id: {clean_id})")
            
            response = self.table.get_item(
                Key={
                    'PK': f'JOURNEY#{clean_id}',
                    'SK': 'METADATA'
                }
            )
            
            if 'Item' not in response:
                logger.warning(f"⚠️ Journey not found: {journey_id}")
                return None
            
            item = response['Item']
            data = item.get('Data', {})
            
            # Return ALL data from DynamoDB, not just selected fields
            journey = {
                'journeyId': f'JRN-{clean_id}',
                **data  # Include all stored data
            }
            
            logger.info(f"✅ Found journey: {journey_id}")
            return journey
            
        except Exception as e:
            logger.error(f"❌ Failed to get journey {journey_id}: {str(e)}")
            raise

    async def delete_journey(self, journey_id: str) -> Dict[str, Any]:
        """Delete a journey and all associated data from DynamoDB."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"🗑️ Deleting journey: {journey_id} (clean_id: {clean_id})")
            
            # First verify journey exists
            existing_journey = await self.get_journey(journey_id)
            if not existing_journey:
                raise ValueError(f'Journey {journey_id} not found for deletion')
            
            # Get all items for this journey
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={':pk': f'JOURNEY#{clean_id}'}
            )
            
            items_to_delete = response.get('Items', [])
            logger.info(f"📊 Found {len(items_to_delete)} items to delete for journey {journey_id}")
            
            # Delete all items
            deleted_count = 0
            for item in items_to_delete:
                try:
                    self.table.delete_item(
                        Key={
                            'PK': item['PK'],
                            'SK': item['SK']
                        }
                    )
                    deleted_count += 1
                    entity_type = item.get('EntityType', 'Unknown')
                    logger.debug(f"   ✅ Deleted {entity_type}: {item['SK']}")
                except Exception as e:
                    logger.error(f"   ❌ Failed to delete item {item.get('SK', 'Unknown')}: {str(e)}")
            
            logger.info(f"✅ Successfully deleted journey {journey_id}: {deleted_count} items removed")
            
            return {
                'deleted_journey': existing_journey,
                'deleted_items_count': deleted_count,
                'success': True,
                'message': f'Journey {journey_id} deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to delete journey {journey_id}: {str(e)}")
            raise

    async def create_journey(self, journey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new journey in DynamoDB following the reference pattern."""
        try:
            # Generate new journey ID (matching reference pattern)
            import uuid
            clean_id = uuid.uuid4().hex.upper().replace("-", "")[:12]
            journey_id = f'JRN-{clean_id}'
            
            logger.info(f"🆕 Creating comprehensive journey: {journey_id}")
            
            # Get current timestamp (matching reference pattern)
            now = datetime.utcnow().isoformat().replace('+00:00', 'Z')
            
            # Extract journey name and component type from input
            journey_name = journey_data.get('name', 'New Journey')
            oda_component_type = journey_data.get('odaComponentType', 'customer-management')
            description = journey_data.get('description', f'Complete TMF ODA transformation journey for {oda_component_type}')
            
            # Create comprehensive journey metadata (following reference script exactly)
            journey_item = {
                'PK': f'JOURNEY#{clean_id}',
                'SK': 'METADATA',
                'EntityType': 'Journey',
                'GSI1PK': 'JOURNEYS',
                'GSI1SK': now,
                'CreatedAt': now,
                'UpdatedAt': now,
                'Data': {
                    'journeyId': journey_id,
                    'name': journey_name,
                    'description': description,
                    'status': 'pending',
                    'createdBy': 'mcp-server',
                    'priority': 'high',
                    'odaComponentType': oda_component_type,
                    'source': {
                        'type': 'schema-based',
                        'schemaId': f'schema-{oda_component_type}-001',
                        'schemaName': f'{oda_component_type.replace("-", " ").title()} Database',
                        'schemaVersion': '1.0.0',
                    },
                    'configuration': {
                        'timeout': 1800,  # 30 minutes for complete journey
                        'maxDepth': 5,
                        'tmfSpecVersion': '4.0.0',
                        'outputFormat': 'json',
                        'retryAttempts': 3,
                        'enableDetailedLogging': True,
                        'validateAtEachStage': True,
                        'secondBrainEnabled': True,
                        'ruleEngineVersion': 'v1.0',
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
                        'totalRules': 0,
                        'activeRules': 0,
                    },
                    'stageSummary': {
                        'raw_analysis': {'totalExecutions': 0, 'lastStatus': 'pending', 'rulesCount': 0},
                        'stripped_schema': {'totalExecutions': 0, 'lastStatus': 'pending', 'rulesCount': 0},
                        'tmf_mapping': {'totalExecutions': 0, 'lastStatus': 'pending', 'rulesCount': 0},
                        'migration_planning': {'totalExecutions': 0, 'lastStatus': 'pending', 'rulesCount': 0},
                        'data_migration': {'totalExecutions': 0, 'lastStatus': 'pending', 'rulesCount': 0},
                        'verification_validation': {'totalExecutions': 0, 'lastStatus': 'pending', 'rulesCount': 0},
                    },
                    'secondBrainConfig': {
                        'enabled': True,
                        'ruleTypes': ['field_mapping', 'contextual_recommendations', 'data_interpretation', 'validation_rules'],
                        'priorityLevels': ['low', 'medium', 'high', 'critical'],
                        'scopes': ['global', 'project', 'stage'],
                        'defaultScope': 'global',
                        'autoApplyRules': True,
                        'customRulesEnabled': True,
                    },
                    # Merge any additional fields from input
                    **{k: v for k, v in journey_data.items() if k not in ['name', 'description', 'odaComponentType']}
                }
            }
            
            # Create the six default stages (following reference script exactly)
            stages = self._get_default_stages(clean_id, journey_id)
            
            # Store journey metadata in DynamoDB
            logger.info("💾 Storing journey metadata...")
            self.table.put_item(Item=journey_item)
            
            # Store all stages in DynamoDB
            logger.info("📋 Storing stage definitions...")
            for stage in stages:
                self.table.put_item(Item=stage)
                stage_name = stage["Data"]["name"]
                step_count = len(stage["Data"]["steps"])
                duration = stage["Data"]["estimatedDuration"]
                logger.info(f"✅ Created stage: {stage_name} ({step_count} steps, ~{duration})")
            
            logger.info(f"✅ Successfully created comprehensive journey: {journey_id}")
            
            return {
                'journeyId': journey_id,
                'success': True,
                'message': f'Journey {journey_id} created successfully with 6 stages',
                'totalStages': 6,
                **journey_item['Data']
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create journey: {str(e)}")
            raise

    def _get_default_stages(self, clean_id: str, journey_id: str) -> List[Dict[str, Any]]:
        """Get the six default stages following the reference script pattern."""
        return [
            # Stage 0: Raw Input Analysis
            {
                'PK': f'JOURNEY#{clean_id}',
                'SK': 'STAGE#00#raw_analysis',
                'EntityType': 'StageDefinition',
                'GSI1PK': f'JOURNEY#{clean_id}#STAGES',
                'GSI1SK': '00',
                'Data': {
                    'stageId': 'raw_analysis',
                    'name': 'Raw Input Analysis',
                    'description': 'Analyze the raw database schema and structure with AI-guided insights',
                    'order': 0,
                    'canSkip': False,
                    'estimatedDuration': '15m',
                    'status': 'pending',
                    'secondBrainEnabled': True,
                    'ruleTypes': ['field_mapping', 'contextual_recommendations', 'data_interpretation'],
                    'steps': [
                        {
                            'id': 'schema_parsing',
                            'name': 'Schema File Parsing',
                            'description': 'Parse SQL schema files and extract structure',
                            'order': 0,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations', 'data_interpretation'],
                        },
                        {
                            'id': 'relationship_discovery',
                            'name': 'Relationship Discovery',
                            'description': 'Identify table relationships and foreign keys',
                            'order': 1,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping', 'contextual_recommendations'],
                        },
                        {
                            'id': 'data_type_analysis',
                            'name': 'Data Type Analysis',
                            'description': 'Analyze column data types and constraints',
                            'order': 2,
                            'estimatedDuration': '3m',
                            'aiAssisted': True,
                            'applicableRules': ['data_interpretation'],
                        },
                        {
                            'id': 'business_rules_extraction',
                            'name': 'Business Rules Extraction',
                            'description': 'Extract business rules from schema constraints',
                            'order': 3,
                            'estimatedDuration': '2m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations', 'data_interpretation'],
                        },
                    ],
                },
            },
            # Stage 1: Create Stripped Document/Schema
            {
                'PK': f'JOURNEY#{clean_id}',
                'SK': 'STAGE#01#stripped_schema',
                'EntityType': 'StageDefinition',
                'GSI1PK': f'JOURNEY#{clean_id}#STAGES',
                'GSI1SK': '01',
                'Data': {
                    'stageId': 'stripped_schema',
                    'name': 'Create Stripped Document',
                    'description': 'Create TMF-focused simplified schema removing unnecessary complexity',
                    'order': 1,
                    'canSkip': False,
                    'estimatedDuration': '12m',
                    'status': 'pending',
                    'secondBrainEnabled': True,
                    'ruleTypes': ['field_mapping', 'data_interpretation'],
                    'steps': [
                        {
                            'id': 'schema_stripping',
                            'name': 'Schema Stripping',
                            'description': 'Remove non-TMF relevant tables and columns',
                            'order': 0,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['data_interpretation'],
                        },
                        {
                            'id': 'core_structure_extraction',
                            'name': 'Core Structure Extraction',
                            'description': 'Extract core business entities and relationships',
                            'order': 1,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping', 'data_interpretation'],
                        },
                        {
                            'id': 'data_model_simplification',
                            'name': 'Data Model Simplification',
                            'description': 'Simplify complex relationships for TMF mapping',
                            'order': 2,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping'],
                        },
                    ],
                },
            },
            # Stage 2: TMF Schema Mapping
            {
                'PK': f'JOURNEY#{clean_id}',
                'SK': 'STAGE#02#tmf_mapping',
                'EntityType': 'StageDefinition',
                'GSI1PK': f'JOURNEY#{clean_id}#STAGES',
                'GSI1SK': '02',
                'Data': {
                    'stageId': 'tmf_mapping',
                    'name': 'TMF Schema Mapping',
                    'description': 'Map the stripped schema to TMF ODA standards and APIs',
                    'order': 2,
                    'canSkip': False,
                    'estimatedDuration': '20m',
                    'status': 'pending',
                    'secondBrainEnabled': True,
                    'ruleTypes': ['field_mapping', 'contextual_recommendations'],
                    'steps': [
                        {
                            'id': 'tmf_api_matching',
                            'name': 'TMF API Matching',
                            'description': 'Match entities to appropriate TMF API specifications',
                            'order': 0,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping', 'contextual_recommendations'],
                        },
                        {
                            'id': 'attribute_mapping',
                            'name': 'Attribute Mapping',
                            'description': 'Map database columns to TMF API attributes',
                            'order': 1,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping'],
                        },
                        {
                            'id': 'relationship_mapping',
                            'name': 'Relationship Mapping',
                            'description': 'Map database relationships to TMF API relationships',
                            'order': 2,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping', 'contextual_recommendations'],
                        },
                        {
                            'id': 'api_coverage_analysis',
                            'name': 'API Coverage Analysis',
                            'description': 'Analyze coverage of TMF API specifications',
                            'order': 3,
                            'estimatedDuration': '3m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations'],
                        },
                        {
                            'id': 'gap_identification',
                            'name': 'Gap Identification',
                            'description': 'Identify gaps and missing mappings',
                            'order': 4,
                            'estimatedDuration': '3m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations'],
                        },
                    ],
                },
            },
            # Stage 3: Data Migration Planning
            {
                'PK': f'JOURNEY#{clean_id}',
                'SK': 'STAGE#03#migration_planning',
                'EntityType': 'StageDefinition',
                'GSI1PK': f'JOURNEY#{clean_id}#STAGES',
                'GSI1SK': '03',
                'Data': {
                    'stageId': 'migration_planning',
                    'name': 'Data Migration Planning',
                    'description': 'Plan and prepare data migration strategies and scripts',
                    'order': 3,
                    'canSkip': False,
                    'estimatedDuration': '18m',
                    'status': 'pending',
                    'secondBrainEnabled': True,
                    'ruleTypes': ['contextual_recommendations', 'validation_rules'],
                    'steps': [
                        {
                            'id': 'migration_strategy_planning',
                            'name': 'Migration Strategy Planning',
                            'description': 'Plan the overall data migration approach',
                            'order': 0,
                            'estimatedDuration': '6m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations'],
                        },
                        {
                            'id': 'etl_script_generation',
                            'name': 'ETL Script Generation',
                            'description': 'Generate Extract, Transform, Load scripts',
                            'order': 1,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations'],
                        },
                        {
                            'id': 'data_validation_rules',
                            'name': 'Data Validation Rules',
                            'description': 'Create validation rules for data integrity',
                            'order': 2,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules'],
                        },
                        {
                            'id': 'rollback_procedures',
                            'name': 'Rollback Procedures',
                            'description': 'Prepare rollback and recovery procedures',
                            'order': 3,
                            'estimatedDuration': '3m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations'],
                        },
                    ],
                },
            },
            # Stage 4: Data Migration
            {
                'PK': f'JOURNEY#{clean_id}',
                'SK': 'STAGE#04#data_migration',
                'EntityType': 'StageDefinition',
                'GSI1PK': f'JOURNEY#{clean_id}#STAGES',
                'GSI1SK': '04',
                'Data': {
                    'stageId': 'data_migration',
                    'name': 'Data Migration',
                    'description': 'Execute the actual data migration from legacy systems to TMF-compliant structure',
                    'order': 4,
                    'canSkip': False,
                    'estimatedDuration': '25m',
                    'status': 'pending',
                    'secondBrainEnabled': True,
                    'ruleTypes': ['data_interpretation', 'validation_rules'],
                    'steps': [
                        {
                            'id': 'candidate_dataset_selection',
                            'name': 'Candidate Dataset Selection',
                            'description': 'Select and prepare candidate datasets for migration',
                            'order': 0,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['data_interpretation'],
                        },
                        {
                            'id': 'data_transfer',
                            'name': 'Data Transfer',
                            'description': 'Execute the actual data transfer from legacy to TMF systems',
                            'order': 1,
                            'estimatedDuration': '12m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules'],
                        },
                        {
                            'id': 'tmf_api_compliance_test',
                            'name': 'TMF API Compliance Test',
                            'description': 'Test migrated data against TMF API compliance requirements',
                            'order': 2,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules'],
                        },
                        {
                            'id': 'mark_completion',
                            'name': 'Mark Completion',
                            'description': 'Mark migration tasks as completed and update status',
                            'order': 3,
                            'estimatedDuration': '3m',
                            'aiAssisted': False,
                            'applicableRules': [],
                        },
                    ],
                },
            },
            # Stage 5: Verification & Validation
            {
                'PK': f'JOURNEY#{clean_id}',
                'SK': 'STAGE#05#verification_validation',
                'EntityType': 'StageDefinition',
                'GSI1PK': f'JOURNEY#{clean_id}#STAGES',
                'GSI1SK': '05',
                'Data': {
                    'stageId': 'verification_validation',
                    'name': 'Verification & Validation',
                    'description': 'Validate the mapping and migration results against TMF standards',
                    'order': 5,
                    'canSkip': False,
                    'estimatedDuration': '22m',
                    'status': 'pending',
                    'secondBrainEnabled': True,
                    'ruleTypes': ['contextual_recommendations', 'validation_rules'],
                    'steps': [
                        {
                            'id': 'mapping_validation',
                            'name': 'Mapping Validation',
                            'description': 'Validate the accuracy of schema mappings',
                            'order': 0,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules'],
                        },
                        {
                            'id': 'api_compliance_check',
                            'name': 'API Compliance Check',
                            'description': 'Check compliance with TMF API standards',
                            'order': 1,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules', 'contextual_recommendations'],
                        },
                        {
                            'id': 'data_integrity_verification',
                            'name': 'Data Integrity Verification',
                            'description': 'Verify data integrity and consistency',
                            'order': 2,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules'],
                        },
                        {
                            'id': 'performance_assessment',
                            'name': 'Performance Assessment',
                            'description': 'Assess performance implications of the mapping',
                            'order': 3,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations'],
                        },
                        {
                            'id': 'final_report_generation',
                            'name': 'Final Report Generation',
                            'description': 'Generate comprehensive final report',
                            'order': 4,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations'],
                        },
                    ],
                },
            },
        ]

    async def update_journey(self, journey_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing journey in DynamoDB."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"🔄 Updating journey: {journey_id} (clean_id: {clean_id})")
            
            # Get existing journey
            existing_journey = await self.get_journey(journey_id)
            if not existing_journey:
                raise ValueError(f'Journey {journey_id} not found for update')
            
            # Get current metadata
            response = self.table.get_item(
                Key={
                    'PK': f'JOURNEY#{clean_id}',
                    'SK': 'METADATA'
                }
            )
            
            current_data = response['Item']['Data']
            
            # Update ALL fields from update_data
            current_data['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
            
            # Apply all update fields (merge update_data into current_data)
            for key, value in update_data.items():
                # Handle field name mapping if needed
                if key == 'overall_progress':
                    current_data['overallProgress'] = value
                elif key == 'current_stage':
                    current_data['currentStage'] = value
                else:
                    current_data[key] = value
                    
            logger.info(f"🔄 Updated fields: {list(update_data.keys())}")
            
            # Save back to DynamoDB
            self.table.put_item(
                Item={
                    'PK': f'JOURNEY#{clean_id}',
                    'SK': 'METADATA',
                    'EntityType': 'Journey',
                    'Data': current_data,
                    'TTL': int((datetime.utcnow().timestamp() + 86400 * 365))
                }
            )
            
            logger.info(f"✅ Successfully updated journey: {journey_id}")
            
            return {
                'journeyId': journey_id,
                'success': True,
                'message': f'Journey {journey_id} updated successfully',
                **current_data
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update journey {journey_id}: {str(e)}")
            raise 

    # =====================================================================
    # ENHANCED METHODS FOR COMPREHENSIVE JOURNEY ECOSYSTEM
    # =====================================================================

    async def list_journey_stages(self, journey_id: str) -> Dict[str, Any]:
        """List all stages for a journey with their rules and jobs."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"📋 Listing stages for journey: {journey_id}")
            
            # Get all records for this journey
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={':pk': f'JOURNEY#{clean_id}'}
            )
            
            stages = {}
            for item in response.get('Items', []):
                sk = item.get('SK', '')
                entity_type = item.get('EntityType', '')
                
                if sk.startswith('STAGE#'):
                    # Parse stage: STAGE#{order}#{stage_id}
                    stage_parts = sk.split('#')
                    if len(stage_parts) >= 3:
                        stage_id = stage_parts[2]
                        if stage_id not in stages:
                            stages[stage_id] = {
                                'stage_id': stage_id,
                                'stage_order': stage_parts[1],
                                'data': item.get('Data', {}),
                                'rules': [],
                                'jobs': []
                            }
                
                elif sk.startswith('RULE#'):
                    # Parse rule: RULE#{stage_id}#{rule_number}#{rule_id}
                    rule_parts = sk.split('#')
                    if len(rule_parts) >= 4:
                        stage_id = rule_parts[1]
                        if stage_id not in stages:
                            stages[stage_id] = {
                                'stage_id': stage_id,
                                'stage_order': '99',  # Default if no stage definition
                                'data': {},
                                'rules': [],
                                'jobs': []
                            }
                        
                        stages[stage_id]['rules'].append({
                            'rule_id': rule_parts[3],
                            'rule_number': rule_parts[2],
                            'sk': sk,
                            'entity_type': entity_type,
                            'data': item.get('Data', {})
                        })
                
                elif sk.startswith('JOB#'):
                    # Parse job: JOB#{job_number}#{stage_id}#{job_number}#{timestamp}
                    job_parts = sk.split('#')
                    if len(job_parts) >= 4:
                        stage_id = job_parts[2]
                        if stage_id not in stages:
                            stages[stage_id] = {
                                'stage_id': stage_id,
                                'stage_order': '99',  # Default if no stage definition
                                'data': {},
                                'rules': [],
                                'jobs': []
                            }
                        
                        stages[stage_id]['jobs'].append({
                            'job_number': job_parts[1],
                            'timestamp': job_parts[4] if len(job_parts) > 4 else '',
                            'sk': sk,
                            'entity_type': entity_type,
                            'data': item.get('Data', {})
                        })
            
            # Sort stages by order
            sorted_stages = sorted(stages.values(), key=lambda x: int(x['stage_order']))
            
            logger.info(f"✅ Found {len(sorted_stages)} stages for journey {journey_id}")
            
            return {
                'journey_id': journey_id,
                'stages': sorted_stages,
                'total_stages': len(sorted_stages),
                'total_rules': sum(len(stage['rules']) for stage in sorted_stages),
                'total_jobs': sum(len(stage['jobs']) for stage in sorted_stages)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to list stages for journey {journey_id}: {str(e)}")
            raise

    async def get_journey_comprehensive(self, journey_id: str) -> Dict[str, Any]:
        """Get complete journey data including metadata, stages, rules, and jobs."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"🔍 Getting comprehensive data for journey: {journey_id}")
            
            # Get basic journey metadata
            journey_metadata = await self.get_journey(journey_id)
            if not journey_metadata:
                raise ValueError(f'Journey {journey_id} not found')
            
            # Get stages with rules and jobs
            stages_data = await self.list_journey_stages(journey_id)
            
            # Combine data
            comprehensive_data = {
                'journey_metadata': journey_metadata,
                'stages': stages_data['stages'],
                'summary': {
                    'total_stages': stages_data['total_stages'],
                    'total_rules': stages_data['total_rules'],
                    'total_jobs': stages_data['total_jobs']
                }
            }
            
            logger.info(f"✅ Retrieved comprehensive data for journey {journey_id}")
            
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get comprehensive journey data {journey_id}: {str(e)}")
            raise

    async def delete_journey_comprehensive(self, journey_id: str) -> Dict[str, Any]:
        """Delete journey and ALL related records (metadata, stages, rules, jobs) with detailed reporting."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"🗑️ Comprehensive deletion of journey: {journey_id} (clean_id: {clean_id})")
            
            # Get comprehensive data before deletion for reporting
            try:
                pre_delete_data = await self.get_journey_comprehensive(journey_id)
                logger.info(f"📊 Journey has {pre_delete_data['summary']['total_stages']} stages, {pre_delete_data['summary']['total_rules']} rules, {pre_delete_data['summary']['total_jobs']} jobs")
            except:
                pre_delete_data = None
                logger.warning("⚠️ Could not get pre-deletion summary, proceeding with deletion")
            
            # Query ALL items for this journey with pagination
            all_items = []
            last_evaluated_key = None
            
            while True:
                query_params = {
                    'KeyConditionExpression': 'PK = :pk',
                    'ExpressionAttributeValues': {':pk': f'JOURNEY#{clean_id}'}
                }
                
                if last_evaluated_key:
                    query_params['ExclusiveStartKey'] = last_evaluated_key
                
                response = self.table.query(**query_params)
                all_items.extend(response.get('Items', []))
                
                if 'LastEvaluatedKey' not in response:
                    break
                last_evaluated_key = response['LastEvaluatedKey']
            
            if not all_items:
                logger.warning(f"⚠️ No records found for journey {journey_id}")
                return {
                    'journey_id': journey_id,
                    'deleted_items_count': 0,
                    'deletion_summary': {},
                    'success': True,
                    'message': f'Journey {journey_id} not found (already deleted)'
                }
            
            # Categorize and delete all items
            deleted_count = 0
            deletion_summary = {
                'metadata': 0,
                'stages': 0,
                'rules': 0,
                'jobs': 0,
                'other': 0
            }
            
            # Track specific deletions for detailed reporting
            detailed_deletions = {
                'metadata': [],
                'stages': [],
                'rules': [],
                'jobs': [],
                'other': []
            }
            
            for item in all_items:
                try:
                    sk = item.get('SK', '')
                    entity_type = item.get('EntityType', 'Unknown')
                    
                    # Categorize the item
                    if sk == 'METADATA':
                        category = 'metadata'
                    elif sk.startswith('STAGE#'):
                        category = 'stages'
                    elif sk.startswith('RULE#'):
                        category = 'rules'
                    elif sk.startswith('JOB#'):
                        category = 'jobs'
                    else:
                        category = 'other'
                    
                    # Delete the item
                    self.table.delete_item(
                        Key={
                            'PK': item['PK'],
                            'SK': item['SK']
                        }
                    )
                    
                    deleted_count += 1
                    deletion_summary[category] += 1
                    detailed_deletions[category].append({
                        'sk': sk,
                        'entity_type': entity_type
                    })
                    
                    logger.debug(f"   ✅ Deleted {entity_type} ({category}): {sk}")
                    
                except Exception as e:
                    logger.error(f"   ❌ Failed to delete item {item.get('SK', 'Unknown')}: {str(e)}")
            
            logger.info(f"✅ Successfully deleted journey {journey_id}")
            logger.info(f"   📊 Deletion summary: {deletion_summary}")
            logger.info(f"   🔢 Total items deleted: {deleted_count}")
            
            return {
                'journey_id': journey_id,
                'deleted_items_count': deleted_count,
                'deletion_summary': deletion_summary,
                'detailed_deletions': detailed_deletions,
                'pre_delete_summary': pre_delete_data['summary'] if pre_delete_data else None,
                'success': True,
                'message': f'Journey {journey_id} and all related records deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to comprehensively delete journey {journey_id}: {str(e)}")
            raise

    async def clean_all_journey_data(self) -> Dict[str, Any]:
        """Clean ALL journey data from the system - comprehensive cleanup."""
        try:
            logger.info("🧹 Starting comprehensive cleanup of ALL journey data")
            
            # Get all journeys
            all_journeys = await self.list_journeys(limit=0)  # No limit
            journey_list = all_journeys.get('journeys', [])
            
            if not journey_list:
                logger.info("ℹ️ No journeys found to clean")
                return {
                    'cleaned_journeys': 0,
                    'total_items_deleted': 0,
                    'cleanup_summary': {},
                    'success': True,
                    'message': 'No journey data found to clean'
                }
            
            # Delete each journey comprehensively
            total_deleted = 0
            total_summary = {
                'metadata': 0,
                'stages': 0,
                'rules': 0,
                'jobs': 0,
                'other': 0
            }
            
            cleaned_journeys = []
            
            for journey in journey_list:
                journey_id = journey.get('journeyId')
                if journey_id:
                    try:
                        delete_result = await self.delete_journey_comprehensive(journey_id)
                        
                        total_deleted += delete_result['deleted_items_count']
                        
                        # Accumulate summary
                        for category, count in delete_result['deletion_summary'].items():
                            total_summary[category] += count
                        
                        cleaned_journeys.append({
                            'journey_id': journey_id,
                            'items_deleted': delete_result['deleted_items_count'],
                            'summary': delete_result['deletion_summary']
                        })
                        
                        logger.info(f"✅ Cleaned journey {journey_id}: {delete_result['deleted_items_count']} items")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to clean journey {journey_id}: {str(e)}")
            
            logger.info(f"🎉 Comprehensive cleanup completed!")
            logger.info(f"   📊 Cleaned {len(cleaned_journeys)} journeys")
            logger.info(f"   🔢 Total items deleted: {total_deleted}")
            logger.info(f"   📋 Summary: {total_summary}")
            
            return {
                'cleaned_journeys': len(cleaned_journeys),
                'total_items_deleted': total_deleted,
                'cleanup_summary': total_summary,
                'journey_details': cleaned_journeys,
                'success': True,
                'message': f'Successfully cleaned {len(cleaned_journeys)} journeys with {total_deleted} total items'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed comprehensive cleanup: {str(e)}")
            raise

    async def add_default_stages(self, journey_id: str) -> Dict[str, Any]:
        """Add the 6 default transformation stages to a journey."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"🏗️ Adding default stages to journey: {journey_id}")
            
            # Verify journey exists
            existing_journey = await self.get_journey(journey_id)
            if not existing_journey:
                raise ValueError(f'Journey {journey_id} not found')
            
            # Define the 6 default transformation stages
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
                    'steps': ['initialize', 'validate_input', 'analyze_schema', 'generate_report', 'finalize']
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
                    'steps': ['initialize', 'validate_input', 'strip_schema', 'validate_output', 'finalize']
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
                    'steps': ['initialize', 'validate_input', 'map_schema', 'validate_mapping', 'finalize']
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
                    'steps': ['initialize', 'analyze_data', 'plan_migration', 'validate_plan', 'finalize']
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
                    'steps': ['initialize', 'prepare_migration', 'execute_migration', 'verify_migration', 'finalize']
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
                    'steps': ['initialize', 'verify_data', 'validate_results', 'generate_report', 'finalize']
                }
            ]
            
            logger.info(f"📋 Preparing to add {len(default_stages)} default stages")
            
            # Add each stage to DynamoDB
            successful_adds = 0
            failed_stages = []
            
            for stage_data in default_stages:
                stage_id = stage_data['stageId']
                try:
                    timestamp = datetime.utcnow().isoformat() + 'Z'
                    
                    stage_item = {
                        'PK': f'JOURNEY#{clean_id}',
                        'SK': f'STAGE#{int(stage_data["order"]):02d}#{stage_id}',
                        'EntityType': 'StageDefinition',
                        'GSI1PK': f'JOURNEY#{clean_id}#STAGES',
                        'GSI1SK': f'{int(stage_data["order"]):02d}',
                        'CreatedAt': timestamp,
                        'UpdatedAt': timestamp,
                        'Data': stage_data,
                        'TTL': int((datetime.utcnow().timestamp() + 86400 * 365))  # 1 year TTL
                    }
                    
                    self.table.put_item(Item=stage_item)
                    successful_adds += 1
                    logger.debug(f"   ✅ Added stage: {stage_id}")
                    
                except Exception as e:
                    failed_stages.append(stage_id)
                    logger.error(f"   ❌ Failed to add stage {stage_id}: {str(e)}")
            
            if successful_adds == 0:
                raise Exception(f"Failed to add any default stages to journey {journey_id}")
            
            status = 'success' if successful_adds == len(default_stages) else 'partial'
            message = f'Added {successful_adds}/{len(default_stages)} default stages to journey {journey_id}'
            
            if failed_stages:
                message += f'. Failed stages: {", ".join(failed_stages)}'
            
            logger.info(f"✅ Default stages operation completed: {message}")
            
            return {
                'journey_id': journey_id,
                'stages_added': successful_adds,
                'total_stages': len(default_stages),
                'failed_stages': failed_stages,
                'success': status == 'success',
                'message': message
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add default stages to journey {journey_id}: {str(e)}")
            raise

    # =====================================================================
    # SECOND BRAIN RULE MANAGEMENT METHODS  
    # =====================================================================
    
    def _validate_rule_structure(self, rule_data: Dict[str, Any]) -> bool:
        """Validate Second Brain rule structure and content."""
        required_fields = ['title', 'description', 'type', 'priority', 'scope', 'content']
        
        # Valid configuration
        valid_rule_types = [
            'field_mapping', 'contextual_recommendations', 'data_interpretation',
            'validation_rules', 'business_logic', 'compliance_check'
        ]
        valid_priorities = ['low', 'medium', 'high', 'critical']
        valid_scopes = ['global', 'project', 'stage']
        
        # Check required fields
        for field in required_fields:
            if field not in rule_data:
                logger.error(f'❌ Missing required field: {field}')
                return False
        
        # Validate rule type
        if rule_data['type'] not in valid_rule_types:
            logger.error(f'❌ Invalid rule type: {rule_data["type"]}. Valid types: {valid_rule_types}')
            return False
        
        # Validate priority
        if rule_data['priority'] not in valid_priorities:
            logger.error(f'❌ Invalid priority: {rule_data["priority"]}. Valid priorities: {valid_priorities}')
            return False
        
        # Validate scope
        if rule_data['scope'] not in valid_scopes:
            logger.error(f'❌ Invalid scope: {rule_data["scope"]}. Valid scopes: {valid_scopes}')
            return False
        
        # Validate content structure
        content = rule_data.get('content', {})
        if not isinstance(content, dict):
            logger.error('❌ Content must be a dictionary')
            return False
        
        return True
    
    def _generate_rule_id(self, stage_id: str, rule_type: str) -> str:
        """Generate a unique rule ID."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        return f'rule-{stage_id}-{rule_type}-{unique_id}'
    
    def _convert_floats_to_decimal(self, obj):
        """Convert float values to Decimal for DynamoDB compatibility."""
        from decimal import Decimal
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        else:
            return obj

    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None, priority: Optional[str] = None) -> Dict[str, Any]:
        """List Second Brain rules for a journey with optional filtering."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"📋 Listing rules for journey: {journey_id}")
            
            # Verify journey exists
            existing_journey = await self.get_journey(journey_id)
            if not existing_journey:
                raise ValueError(f'Journey {journey_id} not found')
            
            # Query all rules for the journey using GSI1
            try:
                response = self.table.query(
                    IndexName='GSI1',
                    KeyConditionExpression='GSI1PK = :pk',
                    ExpressionAttributeValues={
                        ':pk': f'JOURNEY#{clean_id}#RULES'
                    }
                )
            except Exception:
                # Fallback to scanning if GSI1 doesn't exist
                response = self.table.query(
                    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                    ExpressionAttributeValues={
                        ':pk': f'JOURNEY#{clean_id}',
                        ':sk_prefix': 'RULE#'
                    }
                )
            
            rules = []
            for item in response.get('Items', []):
                rule_data = item.get('Data', {})
                
                # Apply filters
                if stage_id and rule_data.get('stageId') != stage_id:
                    continue
                if rule_type and rule_data.get('type') != rule_type:
                    continue
                if priority and rule_data.get('priority') != priority:
                    continue
                
                rules.append({
                    'ruleId': rule_data.get('ruleId'),
                    'stageId': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'createdAt': item.get('CreatedAt'),
                    'updatedAt': item.get('UpdatedAt')
                })
            
            logger.info(f"✅ Found {len(rules)} rules for journey {journey_id}")
            
            return {
                'journey_id': journey_id,
                'rules': rules,
                'total_rules': len(rules),
                'filters': {
                    'stage_id': stage_id,
                    'rule_type': rule_type,
                    'priority': priority
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to list rules for journey {journey_id}: {str(e)}")
            raise

    async def get_rule(self, journey_id: str, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific Second Brain rule by ID."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"🔍 Getting rule {rule_id} for journey: {journey_id}")
            
            # Query all rules and find the one with matching rule_id
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'JOURNEY#{clean_id}',
                    ':sk_prefix': 'RULE#'
                }
            )
            
            for item in response.get('Items', []):
                rule_data = item.get('Data', {})
                if rule_data.get('ruleId') == rule_id:
                    logger.info(f"✅ Found rule: {rule_id}")
                    return rule_data
            
            logger.warning(f"⚠️ Rule not found: {rule_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get rule {rule_id}: {str(e)}")
            raise

    async def add_rule(self, journey_id: str, stage_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new Second Brain rule to a journey."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"➕ Adding new rule to journey: {journey_id}, stage: {stage_id}")
            
            # Verify journey exists
            existing_journey = await self.get_journey(journey_id)
            if not existing_journey:
                raise ValueError(f'Journey {journey_id} not found')
            
            # Validate rule structure
            if not self._validate_rule_structure(rule_data):
                raise ValueError('Invalid rule structure')
            
            # Generate rule ID if not provided
            if 'ruleId' not in rule_data:
                rule_data['ruleId'] = self._generate_rule_id(stage_id, rule_data['type'])
            
            # Convert floats to Decimal for DynamoDB
            rule_data = self._convert_floats_to_decimal(rule_data)
            
            # Get current rules count for ordering
            rules_result = await self.list_rules(journey_id, stage_id=stage_id)
            rule_index = len(rules_result.get('rules', []))
            
            # Create DynamoDB item
            timestamp = datetime.utcnow().isoformat().replace('+00:00', 'Z')
            
            rule_item = {
                'PK': f'JOURNEY#{clean_id}',
                'SK': f'RULE#{stage_id}#{rule_index:03d}#{rule_data["ruleId"]}',
                'EntityType': 'SecondBrainRule',
                'GSI1PK': f'JOURNEY#{clean_id}#RULES',
                'GSI1SK': f'{stage_id}#{rule_data["priority"]}#{rule_index:03d}',
                'CreatedAt': timestamp,
                'UpdatedAt': timestamp,
                'Data': {
                    'ruleId': rule_data['ruleId'],
                    'journeyId': clean_id,
                    'stageId': stage_id,
                    'title': rule_data['title'],
                    'description': rule_data['description'],
                    'type': rule_data['type'],
                    'priority': rule_data['priority'],
                    'scope': rule_data['scope'],
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data['content'],
                    'metadata': {
                        'createdBy': rule_data.get('createdBy', 'mcp-server'),
                        'version': rule_data.get('version', '1.0'),
                        'tags': rule_data.get('tags', [stage_id, rule_data['type'], rule_data['priority']]),
                        'applicableStages': rule_data.get('applicableStages', [stage_id]),
                        'ruleEngine': 'second_brain_v1'
                    }
                }
            }
            
            # Insert the rule
            self.table.put_item(Item=rule_item)
            
            logger.info(f"✅ Successfully added rule: {rule_data['ruleId']}")
            
            return {
                'journey_id': journey_id,
                'stage_id': stage_id,
                'rule_id': rule_data['ruleId'],
                'success': True,
                'message': f'Rule {rule_data["ruleId"]} added successfully to stage {stage_id}',
                'rule_data': rule_data
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add rule: {str(e)}")
            raise

    async def update_rule(self, journey_id: str, rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Second Brain rule."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"✏️ Updating rule: {rule_id}")
            
            # Verify journey exists
            existing_journey = await self.get_journey(journey_id)
            if not existing_journey:
                raise ValueError(f'Journey {journey_id} not found')
            
            # Get existing rule
            existing_rule = await self.get_rule(journey_id, rule_id)
            if not existing_rule:
                raise ValueError(f'Rule {rule_id} not found')
            
            # Validate updated rule structure
            if not self._validate_rule_structure(rule_data):
                raise ValueError('Invalid rule structure')
            
            # Convert floats to Decimal
            rule_data = self._convert_floats_to_decimal(rule_data)
            
            # Find the existing item in DynamoDB
            stage_id = existing_rule['stageId']
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'JOURNEY#{clean_id}',
                    ':sk_prefix': f'RULE#{stage_id}'
                }
            )
            
            target_item = None
            for item in response.get('Items', []):
                if item.get('Data', {}).get('ruleId') == rule_id:
                    target_item = item
                    break
            
            if not target_item:
                raise ValueError(f'Rule item not found in database: {rule_id}')
            
            # Update the rule data
            timestamp = datetime.utcnow().isoformat().replace('+00:00', 'Z')
            
            updated_data = existing_rule.copy()
            updated_data.update(rule_data)
            updated_data['ruleId'] = rule_id  # Preserve original rule ID
            updated_data['journeyId'] = clean_id
            updated_data['stageId'] = stage_id
            
            target_item['UpdatedAt'] = timestamp
            target_item['Data'] = updated_data
            
            # Put the updated item
            self.table.put_item(Item=target_item)
            
            logger.info(f"✅ Successfully updated rule: {rule_id}")
            
            return {
                'journey_id': journey_id,
                'rule_id': rule_id,
                'success': True,
                'message': f'Rule {rule_id} updated successfully',
                'updated_data': updated_data
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update rule {rule_id}: {str(e)}")
            raise

    async def delete_rule(self, journey_id: str, rule_id: str) -> Dict[str, Any]:
        """Delete a Second Brain rule."""
        try:
            clean_id = self._clean_journey_id(journey_id)
            logger.info(f"🗑️ Deleting rule: {rule_id}")
            
            # Verify journey exists
            existing_journey = await self.get_journey(journey_id)
            if not existing_journey:
                raise ValueError(f'Journey {journey_id} not found')
            
            # Get existing rule to find the exact item
            existing_rule = await self.get_rule(journey_id, rule_id)
            if not existing_rule:
                raise ValueError(f'Rule {rule_id} not found')
            
            stage_id = existing_rule['stageId']
            
            # Find the exact item to delete
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'JOURNEY#{clean_id}',
                    ':sk_prefix': f'RULE#{stage_id}'
                }
            )
            
            target_item = None
            for item in response.get('Items', []):
                if item.get('Data', {}).get('ruleId') == rule_id:
                    target_item = item
                    break
            
            if not target_item:
                raise ValueError(f'Rule item not found in database: {rule_id}')
            
            # Delete the item
            self.table.delete_item(
                Key={
                    'PK': target_item['PK'],
                    'SK': target_item['SK']
                }
            )
            
            logger.info(f"✅ Successfully deleted rule: {rule_id}")
            
            return {
                'journey_id': journey_id,
                'rule_id': rule_id,
                'deleted_rule': existing_rule,
                'success': True,
                'message': f'Rule {rule_id} deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to delete rule {rule_id}: {str(e)}")
            raise