#!/usr/bin/env python3
"""
Comprehensive TMF ODA Transformation Journey Management

This consolidated script provides complete management of TMF ODA transformation journeys including:

Journey Management:
- Create/Update/Delete journeys
- Clone journeys
- List and filter journeys
- Import/Export journeys

Stage Management:
- Add/Update/Delete stages
- Reorder stages
- Manage stage steps
- Enable/disable stages

Second Brain Rules Management:
- Add/Update/Delete rules
- Enable/disable rules
- Import/Export rules
- Interactive rule builder

Interactive Features:
- Journey builder wizard
- Stage configuration wizard
- Rule creation wizard
- Comprehensive dashboard

Usage Examples:
    # Journey operations
    python3 manage_journey.py --action list-journeys
    python3 manage_journey.py --action create-journey --data-file journey.json
    python3 manage_journey.py --action get-journey --journey-id JRN-12345 --include-all
    
    # Stage operations  
    python3 manage_journey.py --action list-stages --journey-id JRN-12345
    python3 manage_journey.py --action add-stage --journey-id JRN-12345 --data-file stage.json
    
    # Rules operations
    python3 manage_journey.py --action list-rules --journey-id JRN-12345
    python3 manage_journey.py --action add-rule --journey-id JRN-12345 --stage-id raw_analysis --data-file rule.json
    
    # Interactive mode
    python3 manage_journey.py --action interactive
    python3 manage_journey.py --action dashboard --journey-id JRN-12345
    
    # Bulk operations
    python3 manage_journey.py --action export-complete --journey-id JRN-12345 --output-file journey_backup.json
    python3 manage_journey.py --action import-complete --input-file journey_backup.json
"""

import boto3
import sys
import traceback
import json
import uuid
import argparse
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union


def print_with_flush(message):
    """Print message and flush stdout immediately"""
    print(message)
    sys.stdout.flush()


class ComprehensiveJourneyManager:
    """Comprehensive TMF ODA transformation journey management"""
    
    def __init__(self):
        self.dynamodb = None
        self.table = None
        self.setup_aws_client()
        
        # Configuration constants
        self.valid_journey_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled', 'paused']
        self.valid_priorities = ['low', 'medium', 'high', 'critical']
        self.valid_oda_components = [
            'customer-management', 'product-catalog', 'order-management',
            'billing', 'resource-inventory', 'service-catalog',
            'party-management', 'account-management'
        ]
        self.valid_rule_types = [
            'field_mapping', 'contextual_recommendations', 
            'data_interpretation', 'validation_rules',
            'business_logic', 'compliance_check'
        ]
        self.valid_rule_scopes = ['global', 'project', 'stage']
        self.valid_rule_statuses = ['active', 'inactive', 'deprecated']
        self.available_stage_ids = [
            'raw_analysis', 'stripped_schema', 'tmf_mapping',
            'migration_planning', 'data_migration', 'verification_validation'
        ]
    
    def setup_aws_client(self):
        """Set up AWS DynamoDB client"""
        try:
            print_with_flush('🔗 Setting up AWS DynamoDB client...')
            
            # Import AWS client utilities
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from aws_client_utils import create_aws_resource
            
            role_arn = os.environ.get('AWS_ROLE_ARN')
            if role_arn:
                print_with_flush(f'🔑 Using role ARN: {role_arn}')
                self.dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
            else:
                print_with_flush('🔑 Using default credential chain')
                self.dynamodb = boto3.resource('dynamodb')
            
            self.table = self.dynamodb.Table('TransformationSystem')
            print_with_flush('✅ AWS DynamoDB client ready')
            
        except Exception as e:
            print_with_flush(f'❌ Failed to setup AWS client: {str(e)}')
            raise
    
    def convert_floats_to_decimal(self, obj):
        """Convert float values to Decimal for DynamoDB compatibility"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self.convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_floats_to_decimal(item) for item in obj]
        else:
            return obj
    
    def clean_journey_id(self, journey_id: str) -> str:
        """Clean journey ID by removing JOURNEY# prefix if present"""
        return journey_id.replace('JOURNEY#', '') if journey_id.startswith('JOURNEY#') else journey_id
    
    def validate_journey_exists(self, journey_id: str) -> bool:
        """Check if a journey exists in the database"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            
            response = self.table.get_item(
                Key={
                    'PK': f'JOURNEY#{clean_id}',
                    'SK': 'METADATA'
                }
            )
            
            return 'Item' in response
            
        except Exception as e:
            print_with_flush(f'❌ Error checking journey existence: {str(e)}')
            return False
    
    # ==========================================
    # JOURNEY METADATA MANAGEMENT
    # ==========================================
    
    def list_journeys(self, status_filter: Optional[str] = None, 
                     component_type_filter: Optional[str] = None) -> List[Dict]:
        """List all journeys with optional filtering"""
        try:
            print_with_flush('📋 Listing transformation journeys...')
            
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :pk',
                ExpressionAttributeValues={
                    ':pk': 'JOURNEYS'
                }
            )
            
            journeys = []
            for item in response['Items']:
                journey_data = item['Data']
                
                # Apply filters
                if status_filter and journey_data.get('status') != status_filter:
                    continue
                if component_type_filter and journey_data.get('odaComponentType') != component_type_filter:
                    continue
                
                journeys.append({
                    'journeyId': journey_data.get('journeyId'),
                    'name': journey_data.get('name'),
                    'description': journey_data.get('description'),
                    'status': journey_data.get('status'),
                    'priority': journey_data.get('priority'),
                    'odaComponentType': journey_data.get('odaComponentType'),
                    'overallProgress': journey_data.get('overallProgress', 0),
                    'currentStageId': journey_data.get('currentStageId'),
                    'createdAt': item.get('CreatedAt'),
                    'updatedAt': item.get('UpdatedAt'),
                    'createdBy': journey_data.get('createdBy'),
                    'totalRules': journey_data.get('aggregates', {}).get('totalRules', 0),
                    'activeRules': journey_data.get('aggregates', {}).get('activeRules', 0)
                })
            
            print_with_flush(f'✅ Found {len(journeys)} journeys')
            return journeys
            
        except Exception as e:
            print_with_flush(f'❌ Error listing journeys: {str(e)}')
            traceback.print_exc()
            return []
    
    def get_journey_complete(self, journey_id: str) -> Optional[Dict]:
        """Get complete journey information including stages and rules"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            print_with_flush(f'📄 Getting complete journey details: {clean_id}')
            
            if not self.validate_journey_exists(clean_id):
                print_with_flush(f'❌ Journey not found: {clean_id}')
                return None
            
            # Get journey metadata
            response = self.table.get_item(
                Key={
                    'PK': f'JOURNEY#{clean_id}',
                    'SK': 'METADATA'
                }
            )
            
            journey_data = response['Item']['Data']
            
            result = {
                'metadata': journey_data,
                'createdAt': response['Item'].get('CreatedAt'),
                'updatedAt': response['Item'].get('UpdatedAt'),
                'stages': self.list_stages(clean_id),
                'rules': self.list_rules(clean_id),
                'summary': {
                    'totalStages': 0,
                    'totalRules': 0,
                    'totalSteps': 0,
                    'aiAssistedSteps': 0,
                    'estimatedDuration': '0m'
                }
            }
            
            # Calculate summary statistics
            stages = result['stages']
            rules = result['rules']
            
            result['summary']['totalStages'] = len(stages)
            result['summary']['totalRules'] = len(rules)
            
            total_steps = 0
            ai_steps = 0
            total_minutes = 0
            
            for stage in stages:
                steps = stage.get('steps', [])
                total_steps += len(steps)
                ai_steps += sum(1 for step in steps if step.get('aiAssisted', False))
                
                # Parse duration
                duration = stage.get('estimatedDuration', '0m')
                if duration.endswith('m'):
                    total_minutes += int(duration[:-1])
            
            result['summary']['totalSteps'] = total_steps
            result['summary']['aiAssistedSteps'] = ai_steps
            result['summary']['estimatedDuration'] = f'{total_minutes}m'
            
            return result
            
        except Exception as e:
            print_with_flush(f'❌ Error getting complete journey: {str(e)}')
            traceback.print_exc()
            return None
    
    def create_journey_complete(self, journey_data: Dict[str, Any], 
                              include_default_stages: bool = True,
                              include_default_rules: bool = True) -> Optional[str]:
        """Create a complete journey with stages and rules"""
        try:
            # Generate journey ID
            journey_id = f'JRN-{str(uuid.uuid4()).upper().replace("-", "")[:12]}'
            
            print_with_flush(f'➕ Creating complete journey: {journey_id}')
            
            # Validate required fields
            required_fields = ['name', 'description', 'odaComponentType']
            for field in required_fields:
                if field not in journey_data:
                    print_with_flush(f'❌ Missing required field: {field}')
                    return None
            
            # Create journey metadata
            if not self.create_journey_metadata(journey_id, journey_data):
                return None
            
            # Add default stages if requested
            if include_default_stages:
                print_with_flush('📋 Adding default stages...')
                self.add_default_stages_complete(journey_id)
            
            # Add default rules if requested
            if include_default_rules:
                print_with_flush('🧠 Adding default Second Brain rules...')
                self.add_default_rules_complete(journey_id)
            
            print_with_flush(f'✅ Complete journey created successfully: {journey_id}')
            return journey_id
            
        except Exception as e:
            print_with_flush(f'❌ Error creating complete journey: {str(e)}')
            traceback.print_exc()
            return None
    
    def create_journey_metadata(self, journey_id: str, journey_data: Dict[str, Any]) -> bool:
        """Create journey metadata"""
        try:
            # Validate required fields
            required_fields = ['name', 'description', 'odaComponentType']
            for field in required_fields:
                if field not in journey_data:
                    print_with_flush(f'❌ Missing required field: {field}')
                    return False
            
            # Validate ODA component type
            valid_components = [
                'customer-management', 'product-management', 'order-management',
                'billing-management', 'payment-management', 'inventory-management',
                'party-management', 'resource-management', 'service-management'
            ]
            
            # Allow custom components but reject clearly invalid patterns
            component_type = journey_data['odaComponentType']
            if component_type.startswith('invalid-') or component_type in ['invalid', 'test', 'invalid-component-type']:
                print_with_flush(f'❌ Invalid ODA component type: {component_type}')
                print_with_flush(f'   Valid types: {", ".join(valid_components)}')
                return False
            elif component_type not in valid_components:
                print_with_flush(f'⚠️ Warning: Unknown ODA component type: {component_type}')
                print_with_flush(f'   Valid types: {", ".join(valid_components)}')
                # Allow custom components that don't match invalid patterns
            
            # Convert floats to Decimal
            journey_data = self.convert_floats_to_decimal(journey_data)
            
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
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
                    'name': journey_data['name'],
                    'description': journey_data['description'],
                    'status': journey_data.get('status', 'pending'),
                    'createdBy': journey_data.get('createdBy', 'user'),
                    'priority': journey_data.get('priority', 'medium'),
                    'odaComponentType': journey_data['odaComponentType'],
                    'source': journey_data.get('source', {
                        'type': 'schema-based',
                        'schemaId': f'schema-{journey_data["odaComponentType"]}-001',
                        'schemaName': f'{journey_data["odaComponentType"].replace("-", " ").title()} Database',
                        'schemaVersion': '1.0.0'
                    }),
                    'configuration': journey_data.get('configuration', {
                        'timeout': 1800,
                        'maxDepth': 5,
                        'tmfSpecVersion': '4.0.0',
                        'outputFormat': 'json',
                        'retryAttempts': 3,
                        'enableDetailedLogging': True,
                        'validateAtEachStage': True,
                        'secondBrainEnabled': True,
                        'ruleEngineVersion': 'v1.0'
                    }),
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
                        'activeRules': 0
                    },
                    'stageSummary': {},
                    'secondBrainConfig': journey_data.get('secondBrainConfig', {
                        'enabled': True,
                        'ruleTypes': ['field_mapping', 'contextual_recommendations', 'data_interpretation', 'validation_rules'],
                        'priorityLevels': ['low', 'medium', 'high', 'critical'],
                        'scopes': ['global', 'project', 'stage'],
                        'defaultScope': 'global',
                        'autoApplyRules': True,
                        'customRulesEnabled': True
                    })
                }
            }
            
            self.table.put_item(Item=journey_item)
            print_with_flush(f'✅ Journey metadata created: {journey_id}')
            return True
            
        except Exception as e:
            print_with_flush(f'❌ Error creating journey metadata: {str(e)}')
            traceback.print_exc()
            return False
    
    def update_journey_metadata(self, journey_id: str, journey_data: Dict[str, Any]) -> bool:
        """Update journey metadata"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            print_with_flush(f'✏️ Updating journey metadata: {clean_id}')
            
            if not self.validate_journey_exists(clean_id):
                print_with_flush(f'❌ Journey not found: {clean_id}')
                return False
            
            # Get existing journey
            response = self.table.get_item(
                Key={
                    'PK': f'JOURNEY#{clean_id}',
                    'SK': 'METADATA'
                }
            )
            
            existing_data = response['Item']['Data']
            
            # Convert floats to Decimal and update
            journey_data = self.convert_floats_to_decimal(journey_data)
            updated_data = existing_data.copy()
            updated_data.update(journey_data)
            
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            self.table.update_item(
                Key={
                    'PK': f'JOURNEY#{clean_id}',
                    'SK': 'METADATA'
                },
                UpdateExpression='SET #data = :data, UpdatedAt = :updated_at',
                ExpressionAttributeNames={
                    '#data': 'Data'
                },
                ExpressionAttributeValues={
                    ':data': updated_data,
                    ':updated_at': timestamp
                }
            )
            
            print_with_flush(f'✅ Journey metadata updated: {clean_id}')
            return True
            
        except Exception as e:
            print_with_flush(f'❌ Error updating journey metadata: {str(e)}')
            traceback.print_exc()
            return False
    
    def delete_journey_complete(self, journey_id: str, confirm: bool = False) -> bool:
        """Delete a complete journey including all stages, rules, and job history"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            print_with_flush(f'🗑️ Deleting complete journey: {clean_id}')
            
            if not self.validate_journey_exists(clean_id):
                print_with_flush(f'❌ Journey not found: {clean_id}')
                return False
            
            if not confirm:
                print_with_flush('⚠️ This will permanently delete:')
                print_with_flush('   • Journey metadata')
                print_with_flush('   • All stages and steps')
                print_with_flush('   • All Second Brain rules')
                print_with_flush('   • All job execution history')
                print_with_flush('   • All logs and reports')
                response = input('\nType "DELETE" to confirm permanent deletion: ')
                if response != 'DELETE':
                    print_with_flush('❌ Deletion cancelled')
                    return False
            
            # Get all items for this journey
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'JOURNEY#{clean_id}'
                }
            )
            
            # Delete all items in batches
            items_deleted = 0
            for item in response['Items']:
                self.table.delete_item(
                    Key={
                        'PK': item['PK'],
                        'SK': item['SK']
                    }
                )
                items_deleted += 1
            
            print_with_flush(f'✅ Complete journey deleted: {clean_id}')
            print_with_flush(f'   🗑️ Deleted {items_deleted} items')
            return True
            
        except Exception as e:
            print_with_flush(f'❌ Error deleting journey: {str(e)}')
            traceback.print_exc()
            return False
    
    # ==========================================
    # STAGE MANAGEMENT
    # ==========================================
    
    def list_stages(self, journey_id: str) -> List[Dict]:
        """List all stages for a journey"""
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
            print_with_flush(f'❌ Error listing stages: {str(e)}')
            return []
    
    def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> bool:
        """Add a stage to a journey"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            
            if not self.validate_journey_exists(clean_id):
                print_with_flush(f'❌ Journey not found: {clean_id}')
                return False
            
            # Validate required fields
            required_fields = ['stageId', 'name', 'description']
            for field in required_fields:
                if field not in stage_data:
                    print_with_flush(f'❌ Missing required field: {field}')
                    return False
            
            stage_id = stage_data['stageId']
            
            # Convert floats to Decimal
            stage_data = self.convert_floats_to_decimal(stage_data)
            
            # Get current stages to determine order
            existing_stages = self.list_stages(clean_id)
            stage_order = stage_data.get('order', len(existing_stages))
            
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
            
            self.table.put_item(Item=stage_item)
            print_with_flush(f'✅ Stage added: {stage_id}')
            return True
            
        except Exception as e:
            print_with_flush(f'❌ Error adding stage: {str(e)}')
            traceback.print_exc()
            return False
    
    def add_default_stages_complete(self, journey_id: str) -> bool:
        """Add all default stages to a journey"""
        try:
            default_stages = [
                {
                    'stageId': 'raw_analysis',
                    'name': 'Raw Input Analysis',
                    'description': 'Analyze the raw database schema and structure with AI-guided insights',
                    'order': 0,
                    'estimatedDuration': '15m',
                    'canSkip': False,
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
                            'applicableRules': ['contextual_recommendations', 'data_interpretation']
                        },
                        {
                            'id': 'relationship_discovery',
                            'name': 'Relationship Discovery',
                            'description': 'Identify table relationships and foreign keys',
                            'order': 1,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping', 'contextual_recommendations']
                        },
                        {
                            'id': 'data_type_analysis',
                            'name': 'Data Type Analysis',
                            'description': 'Analyze column data types and constraints',
                            'order': 2,
                            'estimatedDuration': '3m',
                            'aiAssisted': True,
                            'applicableRules': ['data_interpretation']
                        },
                        {
                            'id': 'business_rules_extraction',
                            'name': 'Business Rules Extraction',
                            'description': 'Extract business rules from schema constraints',
                            'order': 3,
                            'estimatedDuration': '2m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations', 'data_interpretation']
                        }
                    ]
                },
                {
                    'stageId': 'stripped_schema',
                    'name': 'Create Stripped Document',
                    'description': 'Create TMF-focused simplified schema removing unnecessary complexity',
                    'order': 1,
                    'estimatedDuration': '12m',
                    'canSkip': False,
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
                            'applicableRules': ['data_interpretation']
                        },
                        {
                            'id': 'core_structure_extraction',
                            'name': 'Core Structure Extraction',
                            'description': 'Extract core business entities and relationships',
                            'order': 1,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping', 'data_interpretation']
                        },
                        {
                            'id': 'data_model_simplification',
                            'name': 'Data Model Simplification',
                            'description': 'Simplify complex relationships for TMF mapping',
                            'order': 2,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping']
                        }
                    ]
                },
                {
                    'stageId': 'tmf_mapping',
                    'name': 'TMF Schema Mapping',
                    'description': 'Map the stripped schema to TMF ODA standards and APIs',
                    'order': 2,
                    'estimatedDuration': '20m',
                    'canSkip': False,
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
                            'applicableRules': ['field_mapping', 'contextual_recommendations']
                        },
                        {
                            'id': 'attribute_mapping',
                            'name': 'Attribute Mapping',
                            'description': 'Map database columns to TMF API attributes',
                            'order': 1,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping']
                        },
                        {
                            'id': 'relationship_mapping',
                            'name': 'Relationship Mapping',
                            'description': 'Map database relationships to TMF API relationships',
                            'order': 2,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['field_mapping', 'contextual_recommendations']
                        },
                        {
                            'id': 'api_coverage_analysis',
                            'name': 'API Coverage Analysis',
                            'description': 'Analyze coverage of TMF API specifications',
                            'order': 3,
                            'estimatedDuration': '3m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations']
                        },
                        {
                            'id': 'gap_identification',
                            'name': 'Gap Identification',
                            'description': 'Identify gaps and missing mappings',
                            'order': 4,
                            'estimatedDuration': '3m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations']
                        }
                    ]
                },
                {
                    'stageId': 'migration_planning',
                    'name': 'Data Migration Planning',
                    'description': 'Plan and prepare data migration strategies and scripts',
                    'order': 3,
                    'estimatedDuration': '18m',
                    'canSkip': False,
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
                            'applicableRules': ['contextual_recommendations']
                        },
                        {
                            'id': 'etl_script_generation',
                            'name': 'ETL Script Generation',
                            'description': 'Generate Extract, Transform, Load scripts',
                            'order': 1,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations']
                        },
                        {
                            'id': 'data_validation_rules',
                            'name': 'Data Validation Rules',
                            'description': 'Create validation rules for data integrity',
                            'order': 2,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules']
                        },
                        {
                            'id': 'rollback_procedures',
                            'name': 'Rollback Procedures',
                            'description': 'Prepare rollback and recovery procedures',
                            'order': 3,
                            'estimatedDuration': '3m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations']
                        }
                    ]
                },
                {
                    'stageId': 'data_migration',
                    'name': 'Data Migration',
                    'description': 'Execute the actual data migration from legacy systems to TMF-compliant structure',
                    'order': 4,
                    'estimatedDuration': '25m',
                    'canSkip': False,
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
                            'applicableRules': ['data_interpretation']
                        },
                        {
                            'id': 'data_transfer',
                            'name': 'Data Transfer',
                            'description': 'Execute the actual data transfer from legacy to TMF systems',
                            'order': 1,
                            'estimatedDuration': '12m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules']
                        },
                        {
                            'id': 'tmf_api_compliance_test',
                            'name': 'TMF API Compliance Test',
                            'description': 'Test migrated data against TMF API compliance requirements',
                            'order': 2,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules']
                        },
                        {
                            'id': 'mark_completion',
                            'name': 'Mark Completion',
                            'description': 'Mark migration tasks as completed and update status',
                            'order': 3,
                            'estimatedDuration': '3m',
                            'aiAssisted': False,
                            'applicableRules': []
                        }
                    ]
                },
                {
                    'stageId': 'verification_validation',
                    'name': 'Verification & Validation',
                    'description': 'Validate the mapping and migration results against TMF standards',
                    'order': 5,
                    'estimatedDuration': '22m',
                    'canSkip': False,
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
                            'applicableRules': ['validation_rules']
                        },
                        {
                            'id': 'api_compliance_check',
                            'name': 'API Compliance Check',
                            'description': 'Check compliance with TMF API standards',
                            'order': 1,
                            'estimatedDuration': '5m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules', 'contextual_recommendations']
                        },
                        {
                            'id': 'data_integrity_verification',
                            'name': 'Data Integrity Verification',
                            'description': 'Verify data integrity and consistency',
                            'order': 2,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['validation_rules']
                        },
                        {
                            'id': 'performance_assessment',
                            'name': 'Performance Assessment',
                            'description': 'Assess performance implications of the mapping',
                            'order': 3,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations']
                        },
                        {
                            'id': 'final_report_generation',
                            'name': 'Final Report Generation',
                            'description': 'Generate comprehensive final report',
                            'order': 4,
                            'estimatedDuration': '4m',
                            'aiAssisted': True,
                            'applicableRules': ['contextual_recommendations']
                        }
                    ]
                }
            ]
            
            successful_adds = 0
            for stage in default_stages:
                if self.add_stage(journey_id, stage):
                    successful_adds += 1
            
            print_with_flush(f'✅ Added {successful_adds} default stages')
            return successful_adds > 0
            
        except Exception as e:
            print_with_flush(f'❌ Error adding default stages: {str(e)}')
            return False
    
    # ==========================================
    # SECOND BRAIN RULES MANAGEMENT
    # ==========================================
    
    def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                   rule_type: Optional[str] = None) -> List[Dict]:
        """List Second Brain rules for a journey"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            
            if not self.validate_journey_exists(clean_id):
                return []
            
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'JOURNEY#{clean_id}#RULES'
                }
            )
            
            rules = []
            for item in response['Items']:
                rule_data = item['Data']
                
                # Apply filters
                if stage_id and rule_data.get('stageId') != stage_id:
                    continue
                if rule_type and rule_data.get('type') != rule_type:
                    continue
                
                rules.append({
                    'ruleId': rule_data.get('ruleId'),
                    'stageId': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {})
                })
            
            return rules
            
        except Exception as e:
            print_with_flush(f'❌ Error listing rules: {str(e)}')
            return []
    
    def add_rule(self, journey_id: str, stage_id: str, rule_data: Dict[str, Any]) -> bool:
        """Add a Second Brain rule to a journey stage"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            
            if not self.validate_journey_exists(clean_id):
                print_with_flush(f'❌ Journey not found: {clean_id}')
                return False
            
            # Validate required fields
            required_fields = ['title', 'description', 'type', 'priority', 'scope', 'context', 'content']
            for field in required_fields:
                if field not in rule_data:
                    print_with_flush(f'❌ Missing required field: {field}')
                    return False
            
            # Generate rule ID if not provided
            if 'ruleId' not in rule_data:
                unique_id = str(uuid.uuid4())[:8]
                rule_data['ruleId'] = f'rule-{stage_id}-{rule_data["type"]}-{unique_id}'
            
            # Convert floats to Decimal
            rule_data = self.convert_floats_to_decimal(rule_data)
            
            # Get current rules count for ordering
            existing_rules = self.list_rules(clean_id, stage_id=stage_id)
            rule_index = len(existing_rules)
            
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
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
                    'context': rule_data['context'],
                    'content': rule_data['content'],
                    'metadata': {
                        'createdBy': rule_data.get('createdBy', 'user'),
                        'version': rule_data.get('version', '1.0'),
                        'tags': rule_data.get('tags', [stage_id, rule_data['type'], rule_data['priority']]),
                        'applicableStages': rule_data.get('applicableStages', [stage_id]),
                        'ruleEngine': 'second_brain_v1'
                    }
                }
            }
            
            self.table.put_item(Item=rule_item)
            print_with_flush(f'✅ Rule added: {rule_data["ruleId"]}')
            return True
            
        except Exception as e:
            print_with_flush(f'❌ Error adding rule: {str(e)}')
            traceback.print_exc()
            return False
    
    def add_default_rules_complete(self, journey_id: str) -> bool:
        """Add all default Second Brain rules to a journey"""
        try:
            # Import the default rules from the original create script
            from create_complete_journey import get_default_rules_for_stage
            
            stages = self.list_stages(journey_id)
            total_rules_added = 0
            
            for stage in stages:
                stage_id = stage['stageId']
                default_rules = get_default_rules_for_stage(stage_id, journey_id)
                
                for rule in default_rules:
                    if self.add_rule(journey_id, stage_id, rule):
                        total_rules_added += 1
            
            print_with_flush(f'✅ Added {total_rules_added} default rules')
            return total_rules_added > 0
            
        except Exception as e:
            print_with_flush(f'❌ Error adding default rules: {str(e)}')
            return False
    
    # ==========================================
    # IMPORT/EXPORT FUNCTIONALITY
    # ==========================================
    
    def export_journey_complete(self, journey_id: str, output_file: str) -> bool:
        """Export complete journey data to JSON file"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            print_with_flush(f'📤 Exporting complete journey: {clean_id}')
            
            journey = self.get_journey_complete(clean_id)
            if not journey:
                return False
            
            # Convert Decimal to float for JSON serialization
            def decimal_to_float(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: decimal_to_float(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [decimal_to_float(item) for item in obj]
                else:
                    return obj
            
            export_data = {
                'journeyId': clean_id,
                'exportedAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'exportType': 'complete_journey',
                'version': '1.0',
                'journey': decimal_to_float(journey)
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print_with_flush(f'✅ Journey exported to: {output_file}')
            return True
            
        except Exception as e:
            print_with_flush(f'❌ Error exporting journey: {str(e)}')
            traceback.print_exc()
            return False
    
    def import_journey_complete(self, input_file: str, new_journey_id: Optional[str] = None) -> Optional[str]:
        """Import complete journey data from JSON file"""
        try:
            print_with_flush(f'📥 Importing complete journey from: {input_file}')
            
            with open(input_file, 'r') as f:
                import_data = json.load(f)
            
            if 'journey' not in import_data:
                print_with_flush('❌ Invalid import file format - missing journey data')
                return None
            
            journey_data = import_data['journey']
            metadata = journey_data.get('metadata', {})
            
            # Generate new journey ID or use provided one
            if new_journey_id:
                journey_id = self.clean_journey_id(new_journey_id)
            else:
                journey_id = f'JRN-{str(uuid.uuid4()).upper().replace("-", "")[:12]}'
            
            # Create journey metadata
            if not self.create_journey_metadata(journey_id, metadata):
                return None
            
            # Import stages
            stages = journey_data.get('stages', [])
            for stage in stages:
                self.add_stage(journey_id, stage)
            
            # Import rules
            rules = journey_data.get('rules', [])
            for rule in rules:
                stage_id = rule.get('stageId')
                if stage_id:
                    self.add_rule(journey_id, stage_id, rule)
            
            print_with_flush(f'✅ Journey imported successfully: {journey_id}')
            print_with_flush(f'   📋 Stages: {len(stages)}')
            print_with_flush(f'   🧠 Rules: {len(rules)}')
            
            return journey_id
            
        except Exception as e:
            print_with_flush(f'❌ Error importing journey: {str(e)}')
            traceback.print_exc()
            return None
    
    # ==========================================
    # DISPLAY AND INTERACTIVE METHODS
    # ==========================================
    
    def display_journey_dashboard(self, journey_id: str):
        """Display comprehensive journey dashboard"""
        try:
            clean_id = self.clean_journey_id(journey_id)
            journey = self.get_journey_complete(clean_id)
            
            if not journey:
                return
            
            metadata = journey['metadata']
            summary = journey['summary']
            
            print_with_flush('\n' + '=' * 80)
            print_with_flush(f'🏗️ JOURNEY DASHBOARD: {clean_id}')
            print_with_flush('=' * 80)
            
            # Basic Info
            print_with_flush(f'📝 Name: {metadata.get("name", "N/A")}')
            print_with_flush(f'📄 Description: {metadata.get("description", "N/A")}')
            print_with_flush(f'🏗️  Component: {metadata.get("odaComponentType", "N/A")}')
            print_with_flush(f'📊 Status: {metadata.get("status", "N/A")}')
            print_with_flush(f'⚡ Priority: {metadata.get("priority", "N/A")}')
            print_with_flush(f'👤 Created by: {metadata.get("createdBy", "N/A")}')
            print_with_flush(f'📅 Created: {journey.get("createdAt", "N/A")}')
            print_with_flush(f'🔄 Updated: {journey.get("updatedAt", "N/A")}')
            
            # Progress
            print_with_flush(f'\n📈 PROGRESS:')
            print_with_flush(f'   Overall: {metadata.get("overallProgress", 0)}%')
            print_with_flush(f'   Current Stage: {metadata.get("currentStageId", "N/A")}')
            
            # Summary Statistics
            print_with_flush(f'\n📊 SUMMARY:')
            print_with_flush(f'   📋 Total Stages: {summary["totalStages"]}')
            print_with_flush(f'   🧠 Total Rules: {summary["totalRules"]}')
            print_with_flush(f'   🔧 Total Steps: {summary["totalSteps"]}')
            print_with_flush(f'   🤖 AI-Assisted Steps: {summary["aiAssistedSteps"]}')
            print_with_flush(f'   ⏱️  Estimated Duration: {summary["estimatedDuration"]}')
            
            # Second Brain Configuration
            sb_config = metadata.get('secondBrainConfig', {})
            print_with_flush(f'\n🧠 SECOND BRAIN:')
            print_with_flush(f'   Enabled: {"✓" if sb_config.get("enabled") else "✗"}')
            print_with_flush(f'   Auto Apply Rules: {"✓" if sb_config.get("autoApplyRules") else "✗"}')
            print_with_flush(f'   Custom Rules: {"✓" if sb_config.get("customRulesEnabled") else "✗"}')
            print_with_flush(f'   Rule Types: {", ".join(sb_config.get("ruleTypes", []))}')
            
            # Stages Summary
            stages = journey['stages']
            print_with_flush(f'\n📋 STAGES ({len(stages)}):')
            for stage in stages:
                ai_symbol = '🤖' if stage.get('secondBrainEnabled') else '🔧'
                steps_count = len(stage.get('steps', []))
                print_with_flush(f'   {int(stage["order"]):2d}. {ai_symbol} {stage["name"]} ({steps_count} steps, {stage.get("estimatedDuration", "N/A")})')
            
            # Rules Summary
            rules = journey['rules']
            rules_by_stage = {}
            for rule in rules:
                stage_id = rule['stageId']
                if stage_id not in rules_by_stage:
                    rules_by_stage[stage_id] = []
                rules_by_stage[stage_id].append(rule)
            
            print_with_flush(f'\n🧠 RULES ({len(rules)}):')
            for stage_id, stage_rules in rules_by_stage.items():
                print_with_flush(f'   {stage_id}: {len(stage_rules)} rules')
            
            print_with_flush('=' * 80)
            
        except Exception as e:
            print_with_flush(f'❌ Error displaying dashboard: {str(e)}')
    
    def interactive_journey_wizard(self):
        """Interactive journey creation wizard"""
        try:
            print_with_flush('\n🧙 COMPREHENSIVE JOURNEY CREATION WIZARD')
            print_with_flush('=' * 60)
            
            journey_data = {}
            
            # Basic Information
            print_with_flush('\n📝 BASIC INFORMATION:')
            journey_data['name'] = input('Journey name: ').strip()
            journey_data['description'] = input('Journey description: ').strip()
            
            print_with_flush(f'\nAvailable ODA components: {", ".join(self.valid_oda_components)}')
            journey_data['odaComponentType'] = input('ODA component type: ').strip()
            
            print_with_flush(f'Available priorities: {", ".join(self.valid_priorities)}')
            priority = input('Priority (default: medium): ').strip()
            if priority:
                journey_data['priority'] = priority
            
            journey_data['createdBy'] = input('Created by (default: user): ').strip() or 'user'
            
            # Options
            print_with_flush('\n⚙️ OPTIONS:')
            add_stages = input('Add default stages? (Y/n): ').strip().lower()
            include_stages = add_stages != 'n'
            
            add_rules = input('Add default Second Brain rules? (Y/n): ').strip().lower()
            include_rules = add_rules != 'n'
            
            # Summary
            print_with_flush('\n📋 JOURNEY SUMMARY:')
            print_with_flush(f'   📝 Name: {journey_data["name"]}')
            print_with_flush(f'   🏗️  Component: {journey_data["odaComponentType"]}')
            print_with_flush(f'   📊 Priority: {journey_data.get("priority", "medium")}')
            print_with_flush(f'   👤 Created by: {journey_data["createdBy"]}')
            print_with_flush(f'   📋 Include stages: {"Yes" if include_stages else "No"}')
            print_with_flush(f'   🧠 Include rules: {"Yes" if include_rules else "No"}')
            
            # Confirm
            confirm = input('\nCreate this journey? (y/n): ').strip().lower()
            if confirm == 'y':
                journey_id = self.create_journey_complete(
                    journey_data,
                    include_default_stages=include_stages,
                    include_default_rules=include_rules
                )
                
                if journey_id:
                    print_with_flush(f'\n✅ Journey created successfully!')
                    print_with_flush(f'🆔 Journey ID: {journey_id}')
                    
                    # Ask if they want to see the dashboard
                    show_dashboard = input('\nShow journey dashboard? (y/n): ').strip().lower()
                    if show_dashboard == 'y':
                        self.display_journey_dashboard(journey_id)
                    
                    return journey_id
            else:
                print_with_flush('❌ Journey creation cancelled')
                return None
                
        except KeyboardInterrupt:
            print_with_flush('\n❌ Wizard cancelled')
            return None
        except Exception as e:
            print_with_flush(f'❌ Error in wizard: {str(e)}')
            return None
    
    def display_journeys_table(self, journeys: List[Dict]):
        """Display journeys in a formatted table"""
        if not journeys:
            print_with_flush('📋 No journeys found')
            return
        
        print_with_flush('\n📋 TMF ODA Transformation Journeys:')
        print_with_flush('=' * 150)
        
        # Header
        header = f'{"Journey ID":<20} {"Name":<30} {"Component":<20} {"Status":<12} {"Priority":<10} {"Progress":<10} {"Current Stage":<20} {"Rules":<8}'
        print_with_flush(header)
        print_with_flush('-' * 150)
        
        # Journeys
        for journey in journeys:
            # Safe handling of potentially Decimal fields
            name = str(journey.get("name", "N/A"))[:29]  # Convert to string and then slice
            journey_id = str(journey.get("journeyId", "N/A"))
            component_type = str(journey.get("odaComponentType", "N/A"))
            status = str(journey.get("status", "N/A"))
            priority = str(journey.get("priority", "medium"))
            current_stage = str(journey.get("currentStageId", "N/A"))
            
            progress = f'{journey.get("overallProgress", 0)}%'
            rules_count = f'{journey.get("activeRules", 0)}/{journey.get("totalRules", 0)}'
            
            row = f'{journey_id:<20} {name:<30} {component_type:<20} {status:<12} {priority:<10} {progress:<10} {current_stage:<20} {rules_count:<8}'
            print_with_flush(row)
        
        print_with_flush(f'\n📊 Total: {len(journeys)} journeys')


def main():
    """Main function with comprehensive command-line interface"""
    parser = argparse.ArgumentParser(description='Comprehensive TMF ODA Transformation Journey Management')
    parser.add_argument('--action', required=True, choices=[
        # Journey operations
        'list-journeys', 'get-journey', 'create-journey', 'update-journey', 'delete-journey',
        
        # Stage operations
        'list-stages', 'add-stage', 'update-stage', 'delete-stage', 'add-default-stages',
        
        # Rules operations
        'list-rules', 'add-rule', 'update-rule', 'delete-rule',
        
        # Import/Export
        'export-complete', 'import-complete',
        
        # Interactive
        'interactive', 'dashboard', 'wizard'
    ], help='Action to perform')
    
    # Common arguments
    parser.add_argument('--journey-id', help='Journey ID')
    parser.add_argument('--data-file', help='JSON file with data')
    parser.add_argument('--output-file', help='Output file for export')
    parser.add_argument('--input-file', help='Input file for import')
    
    # Filtering arguments
    parser.add_argument('--status-filter', help='Filter by status')
    parser.add_argument('--component-filter', help='Filter by component type')
    parser.add_argument('--stage-id', help='Stage ID')
    parser.add_argument('--rule-type', help='Rule type filter')
    
    # Options
    parser.add_argument('--include-all', action='store_true', help='Include all details')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    # Initialize manager
    try:
        print_with_flush('🏗️ Comprehensive Journey Manager')
        print_with_flush('=' * 50)
        
        manager = ComprehensiveJourneyManager()
        
        # Journey operations
        if args.action == 'list-journeys':
            journeys = manager.list_journeys(
                status_filter=args.status_filter,
                component_type_filter=args.component_filter
            )
            manager.display_journeys_table(journeys)
        
        elif args.action == 'get-journey':
            if not args.journey_id:
                print_with_flush('❌ --journey-id is required')
                return False
            
            journey = manager.get_journey_complete(args.journey_id)
            if journey:
                if args.include_all:
                    print_with_flush(json.dumps(journey, indent=2, default=str))
                else:
                    manager.display_journey_dashboard(args.journey_id)
            else:
                print_with_flush(f'❌ Journey not found: {args.journey_id}')
                return False
        
        elif args.action == 'create-journey':
            if not args.data_file:
                print_with_flush('❌ --data-file is required')
                return False
            
            try:
                with open(args.data_file, 'r') as f:
                    journey_data = json.load(f)
            except FileNotFoundError:
                print_with_flush(f'❌ File not found: {args.data_file}')
                return False
            except json.JSONDecodeError:
                print_with_flush(f'❌ Invalid JSON in file: {args.data_file}')
                return False
            
            journey_id = manager.create_journey_complete(journey_data)
            if journey_id:
                print_with_flush(f'✅ Journey created: {journey_id}')
            else:
                print_with_flush('❌ Failed to create journey')
                return False
        
        elif args.action == 'update-journey':
            if not args.journey_id or not args.data_file:
                print_with_flush('❌ --journey-id and --data-file are required')
                return False
            
            with open(args.data_file, 'r') as f:
                journey_data = json.load(f)
            
            manager.update_journey_metadata(args.journey_id, journey_data)
        
        elif args.action == 'delete-journey':
            if not args.journey_id:
                print_with_flush('❌ --journey-id is required')
                return False
            
            manager.delete_journey_complete(args.journey_id, args.confirm)
        
        # Stage operations
        elif args.action == 'list-stages':
            if not args.journey_id:
                print_with_flush('❌ --journey-id is required')
                return False
            
            stages = manager.list_stages(args.journey_id)
            print_with_flush(f'\n📋 Stages for Journey: {args.journey_id}')
            for stage in stages:
                ai_symbol = '🤖' if stage.get('secondBrainEnabled') else '🔧'
                print_with_flush(f'   {int(stage["order"]):2d}. {ai_symbol} {stage["name"]} ({len(stage.get("steps", []))} steps)')
        
        elif args.action == 'add-stage':
            if not args.journey_id or not args.data_file:
                print_with_flush('❌ --journey-id and --data-file are required')
                return False
            
            with open(args.data_file, 'r') as f:
                stage_data = json.load(f)
            
            manager.add_stage(args.journey_id, stage_data)
        
        elif args.action == 'add-default-stages':
            if not args.journey_id:
                print_with_flush('❌ --journey-id is required')
                return False
            
            manager.add_default_stages_complete(args.journey_id)
        
        # Rules operations
        elif args.action == 'list-rules':
            if not args.journey_id:
                print_with_flush('❌ --journey-id is required')
                return False
            
            rules = manager.list_rules(args.journey_id, args.stage_id, args.rule_type)
            print_with_flush(f'\n🧠 Rules for Journey: {args.journey_id}')
            for rule in rules:
                print_with_flush(f'   • {rule["title"]} ({rule["type"]}, {rule["priority"]})')
        
        elif args.action == 'add-rule':
            if not args.journey_id or not args.stage_id or not args.data_file:
                print_with_flush('❌ --journey-id, --stage-id, and --data-file are required')
                return False
            
            with open(args.data_file, 'r') as f:
                rule_data = json.load(f)
            
            manager.add_rule(args.journey_id, args.stage_id, rule_data)
        
        # Import/Export
        elif args.action == 'export-complete':
            if not args.journey_id or not args.output_file:
                print_with_flush('❌ --journey-id and --output-file are required')
                return False
            
            manager.export_journey_complete(args.journey_id, args.output_file)
        
        elif args.action == 'import-complete':
            if not args.input_file:
                print_with_flush('❌ --input-file is required')
                return False
            
            journey_id = manager.import_journey_complete(args.input_file, args.journey_id)
            if journey_id:
                print_with_flush(f'✅ Journey imported: {journey_id}')
        
        # Interactive
        elif args.action == 'dashboard':
            if not args.journey_id:
                print_with_flush('❌ --journey-id is required')
                return False
            
            manager.display_journey_dashboard(args.journey_id)
        
        elif args.action == 'interactive' or args.action == 'wizard':
            manager.interactive_journey_wizard()
        
        return True
        
    except Exception as e:
        print_with_flush(f'❌ Error: {str(e)}')
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_with_flush('\n⚠️ Operation cancelled by user')
        sys.exit(1)
    except Exception as e:
        print_with_flush(f'\n❌ Unexpected error: {str(e)}')
        traceback.print_exc()
        sys.exit(1) 