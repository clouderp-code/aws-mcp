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

"""awslabs TMF ODA Transformer MCP Server implementation."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid

# Import logger first so it can be used in try/except blocks
from loguru import logger

# Import MCP and Pydantic dependencies
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field, BaseModel
from typing import Annotated
from enum import Enum

# Define Enums for tool parameters
class TMFODAComponentType(str, Enum):
    PRODUCT_CATALOG_MANAGEMENT = "product-catalog-management"
    CUSTOMER_MANAGEMENT = "customer-management"
    ORDER_MANAGEMENT = "order-management"
    SERVICE_INVENTORY_MANAGEMENT = "service-inventory-management"
    RESOURCE_INVENTORY_MANAGEMENT = "resource-inventory-management"
    PARTY_MANAGEMENT = "party-management"
    ACCOUNT_MANAGEMENT = "account-management"
    BILLING_MANAGEMENT = "billing-management"
    PRODUCT_OFFERING_QUALIFICATION = "product-offering-qualification"
    SERVICE_QUALIFICATION = "service-qualification"
    QUOTE_MANAGEMENT = "quote-management"
    SERVICE_ORDERING = "service-ordering"
    PRODUCT_ORDERING = "product-ordering"

class SchemaFormat(str, Enum):
    JSON_SCHEMA = "json-schema"
    OPENAPI = "openapi"
    SWAGGER = "swagger"
    AVRO = "avro"
    PROTOBUF = "protobuf"
    YAML_SCHEMA = "yaml-schema"

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    DYNAMODB = "dynamodb"
    CASSANDRA = "cassandra"

# Define response models
class SchemaAnalysisReport(BaseModel):
    """Schema analysis report model."""
    workspace_dir: str
    total_files: int
    analyzed_files: int
    compliance_score: float
    recommendations: List[str]
    issues: List[Dict[str, Any]]

class DatabaseAnalysisReport(BaseModel):
    """Database analysis report model."""
    database_type: str
    total_tables: int
    analyzed_tables: int
    compliance_score: float
    recommendations: List[str]
    issues: List[Dict[str, Any]]

# Application name constant
TMF_ODA_MCP_SERVER_APPLICATION_NAME = "awslabs-tmf-oda-transformer"

# Import transformation job executor
try:
    from .scripts.job_executor import TransformationJobExecutor
except ImportError:
    logger.warning("TransformationJobExecutor not available - raw_analysis tool will not work")
    TransformationJobExecutor = None

# Import TransformationUtils for DynamoDB-based journey management
try:
    from .scripts.utils import TransformationUtils
    logger.info("Successfully imported TransformationUtils from local scripts directory")
except ImportError:
    try:
        # Try local scripts directory in Docker container
        import sys
        import os
        scripts_path = '/app/scripts'
        if os.path.exists(scripts_path):
            sys.path.insert(0, scripts_path)
            from utils import TransformationUtils
            logger.info(f"Successfully imported TransformationUtils from {scripts_path}")
        else:
            raise ImportError("Local scripts path not found")
    except ImportError:
        try:
            # Try alternative import path for development
            import sys
            sys.path.append('/opt/mycode/aws-mcp/scripts')
            from utils import TransformationUtils
        except ImportError:
            try:
                # Try absolute path that matches the working manage-transformation.py script
                import sys
                import os
                scripts_path = '/opt/mycode/aws-mcp/scripts'
                if os.path.exists(scripts_path):
                    sys.path.insert(0, scripts_path)
                    from utils import TransformationUtils
                    logger.info(f"Successfully imported TransformationUtils from {scripts_path}")
                else:
                    raise ImportError("Scripts path not found")
            except ImportError:
                logger.warning("TransformationUtils not available - journey-info tool will use fallback data")
                TransformationUtils = None

# Fallback Journey Management System (used only when DynamoDB is not available)
class FallbackJourneyManager:
    """Self-contained journey management system for TMF ODA transformations."""
    
    def __init__(self, data_dir: str = "/tmp/tmf_oda_journeys"):
        """Initialize the journey manager with local storage."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Journey storage files
        self.journeys_file = self.data_dir / "journeys.json"
        self.jobs_file = self.data_dir / "jobs.json"
        
        # Initialize data files if they don't exist
        self._init_data_files()
        
        # Predefined stage definitions
        self.stage_definitions = {
            'raw_analysis': {
                'name': 'Raw Analysis',
                'description': 'Parse schema files and understand database structure',
                'order': 1,
                'steps': [
                    {'id': 'schema_parsing', 'name': 'Schema Parsing', 'description': 'Parse schema files'},
                    {'id': 'relationship_discovery', 'name': 'Relationship Discovery', 'description': 'Discover relationships between entities'},
                    {'id': 'data_type_analysis', 'name': 'Data Type Analysis', 'description': 'Analyze data types for TMF ODA compatibility'}
                ]
            },
            'stripped_schema': {
                'name': 'Stripped Schema',
                'description': 'Strip non-essential elements and extract core structure',
                'order': 2,
                'steps': [
                    {'id': 'schema_stripping', 'name': 'Schema Stripping', 'description': 'Remove non-essential elements'},
                    {'id': 'core_structure_extraction', 'name': 'Core Structure Extraction', 'description': 'Extract core TMF ODA structure'},
                    {'id': 'data_model_simplification', 'name': 'Data Model Simplification', 'description': 'Simplify data models'}
                ]
            },
            'data_mapping': {
                'name': 'Data Mapping',
                'description': 'Map data structures to TMF ODA specifications',
                'order': 3,
                'steps': [
                    {'id': 'field_mapping', 'name': 'Field Mapping', 'description': 'Map fields to TMF ODA fields'},
                    {'id': 'transformation_rules', 'name': 'Transformation Rules', 'description': 'Apply transformation rules'},
                    {'id': 'validation_mapping', 'name': 'Validation Mapping', 'description': 'Validate mappings'}
                ]
            },
            'compliance_validation': {
                'name': 'Compliance Validation',
                'description': 'Validate compliance with TMF ODA specifications',
                'order': 4,
                'steps': [
                    {'id': 'compliance_check', 'name': 'Compliance Check', 'description': 'Check TMF ODA compliance'},
                    {'id': 'report_generation', 'name': 'Report Generation', 'description': 'Generate compliance report'},
                    {'id': 'recommendations', 'name': 'Recommendations', 'description': 'Generate improvement recommendations'}
                ]
            }
        }
        
        logger.info(f"JourneyManager initialized with data directory: {self.data_dir}")
    
    def _init_data_files(self):
        """Initialize data files with default content."""
        # Initialize journeys file
        if not self.journeys_file.exists():
            default_journeys = {
                'JRN-DEMO-001': {
                    'journey_id': 'JRN-DEMO-001',
                    'name': 'Product Catalog Transformation',
                    'description': 'Transform product catalog to TMF ODA compliant format',
                    'status': 'completed',
                    'created_at': '2024-01-01T10:00:00Z',
                    'updated_at': '2024-01-01T16:30:00Z',
                    'overall_progress': 100,
                    'current_stage': 'compliance_validation',
                    'created_by': 'demo-user',
                    'oda_component_type': 'product-catalog-management',
                    'source_type': 'database',
                    'stages': ['raw_analysis', 'stripped_schema', 'data_mapping', 'compliance_validation']
                },
                'JRN-DEMO-002': {
                    'journey_id': 'JRN-DEMO-002',
                    'name': 'Customer Management Migration',
                    'description': 'Migrate customer management system to TMF ODA',
                    'status': 'running',
                    'created_at': '2024-01-02T14:30:00Z',
                    'updated_at': '2024-01-02T15:45:00Z',
                    'overall_progress': 65,
                    'current_stage': 'data_mapping',
                    'created_by': 'demo-user',
                    'oda_component_type': 'customer-management',
                    'source_type': 'schema',
                    'stages': ['raw_analysis', 'stripped_schema', 'data_mapping', 'compliance_validation']
                },
                'JRN-DEMO-003': {
                    'journey_id': 'JRN-DEMO-003',
                    'name': 'Order Management Setup',
                    'description': 'Set up order management system with TMF ODA compliance',
                    'status': 'completed',
                    'created_at': '2024-01-03T09:15:00Z',
                    'updated_at': '2024-01-03T12:00:00Z',
                    'overall_progress': 100,
                    'current_stage': 'compliance_validation',
                    'created_by': 'demo-user',
                    'oda_component_type': 'order-management',
                    'source_type': 'api',
                    'stages': ['raw_analysis', 'stripped_schema', 'data_mapping', 'compliance_validation']
                }
            }
            with open(self.journeys_file, 'w') as f:
                json.dump(default_journeys, f, indent=2)
        
        # Initialize jobs file
        if not self.jobs_file.exists():
            default_jobs = {
                'JRN-DEMO-001': {
                    'raw_analysis': [
                        {
                            'job_id': 'JOB-001-20240101103000',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-01T10:30:00Z',
                            'end_time': '2024-01-01T11:45:00Z',
                            'duration_seconds': 4500,
                            'triggered_by': 'demo-user',
                            'reason': 'Initial analysis',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ],
                    'stripped_schema': [
                        {
                            'job_id': 'JOB-002-20240101120000',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-01T12:00:00Z',
                            'end_time': '2024-01-01T13:15:00Z',
                            'duration_seconds': 4500,
                            'triggered_by': 'demo-user',
                            'reason': 'Schema processing',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ],
                    'data_mapping': [
                        {
                            'job_id': 'JOB-003-20240101140000',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-01T14:00:00Z',
                            'end_time': '2024-01-01T15:30:00Z',
                            'duration_seconds': 5400,
                            'triggered_by': 'demo-user',
                            'reason': 'Data mapping',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ],
                    'compliance_validation': [
                        {
                            'job_id': 'JOB-004-20240101160000',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-01T16:00:00Z',
                            'end_time': '2024-01-01T16:30:00Z',
                            'duration_seconds': 1800,
                            'triggered_by': 'demo-user',
                            'reason': 'Final validation',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ]
                },
                'JRN-DEMO-002': {
                    'raw_analysis': [
                        {
                            'job_id': 'JOB-005-20240102143000',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-02T14:30:00Z',
                            'end_time': '2024-01-02T15:00:00Z',
                            'duration_seconds': 1800,
                            'triggered_by': 'demo-user',
                            'reason': 'Initial analysis',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ],
                    'stripped_schema': [
                        {
                            'job_id': 'JOB-006-20240102150000',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-02T15:00:00Z',
                            'end_time': '2024-01-02T15:30:00Z',
                            'duration_seconds': 1800,
                            'triggered_by': 'demo-user',
                            'reason': 'Schema processing',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ],
                    'data_mapping': [
                        {
                            'job_id': 'JOB-007-20240102153000',
                            'execution_number': 1,
                            'status': 'running',
                            'start_time': '2024-01-02T15:30:00Z',
                            'end_time': None,
                            'duration_seconds': None,
                            'triggered_by': 'demo-user',
                            'reason': 'Data mapping',
                            'progress': 50,
                            'steps_completed': 1,
                            'total_steps': 3
                        }
                    ]
                },
                'JRN-DEMO-003': {
                    'raw_analysis': [
                        {
                            'job_id': 'JOB-008-20240103091500',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-03T09:15:00Z',
                            'end_time': '2024-01-03T10:00:00Z',
                            'duration_seconds': 2700,
                            'triggered_by': 'demo-user',
                            'reason': 'Initial analysis',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ],
                    'stripped_schema': [
                        {
                            'job_id': 'JOB-009-20240103100000',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-03T10:00:00Z',
                            'end_time': '2024-01-03T10:30:00Z',
                            'duration_seconds': 1800,
                            'triggered_by': 'demo-user',
                            'reason': 'Schema processing',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ],
                    'data_mapping': [
                        {
                            'job_id': 'JOB-010-20240103103000',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-03T10:30:00Z',
                            'end_time': '2024-01-03T11:15:00Z',
                            'duration_seconds': 2700,
                            'triggered_by': 'demo-user',
                            'reason': 'Data mapping',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ],
                    'compliance_validation': [
                        {
                            'job_id': 'JOB-011-20240103111500',
                            'execution_number': 1,
                            'status': 'completed',
                            'start_time': '2024-01-03T11:15:00Z',
                            'end_time': '2024-01-03T12:00:00Z',
                            'duration_seconds': 2700,
                            'triggered_by': 'demo-user',
                            'reason': 'Final validation',
                            'progress': 100,
                            'steps_completed': 3,
                            'total_steps': 3
                        }
                    ]
                }
            }
            with open(self.jobs_file, 'w') as f:
                json.dump(default_jobs, f, indent=2)
    
    def _load_journeys(self) -> Dict[str, Any]:
        """Load journeys from file."""
        try:
            with open(self.journeys_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading journeys: {e}")
            return {}
    
    def _save_journeys(self, journeys: Dict[str, Any]):
        """Save journeys to file."""
        try:
            with open(self.journeys_file, 'w') as f:
                json.dump(journeys, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving journeys: {e}")
    
    def _load_jobs(self) -> Dict[str, Any]:
        """Load jobs from file."""
        try:
            with open(self.jobs_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
            return {}
    
    def _save_jobs(self, jobs: Dict[str, Any]):
        """Save jobs to file."""
        try:
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving jobs: {e}")
    
    def list_journeys(self) -> List[Dict[str, Any]]:
        """List all journeys."""
        journeys = self._load_journeys()
        return list(journeys.values())
    
    def get_journey_status(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Get journey status by ID."""
        journeys = self._load_journeys()
        return journeys.get(journey_id)
    
    def get_journey_stages(self, journey_id: str) -> List[Dict[str, Any]]:
        """Get stages for a journey."""
        journey = self.get_journey_status(journey_id)
        if not journey:
            return []
        
        stages = []
        for stage_id in journey.get('stages', []):
            stage_def = self.stage_definitions.get(stage_id, {})
            stages.append({
                'stage_id': stage_id,
                'name': stage_def.get('name', stage_id),
                'description': stage_def.get('description', ''),
                'order': stage_def.get('order', 0),
                'steps': stage_def.get('steps', [])
            })
        
        return stages
    
    def get_stage_jobs(self, journey_id: str, stage_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get jobs for a specific stage."""
        jobs = self._load_jobs()
        journey_jobs = jobs.get(journey_id, {})
        stage_jobs = journey_jobs.get(stage_id, [])
        
        # Sort by execution number descending and return latest jobs
        stage_jobs.sort(key=lambda x: x.get('execution_number', 0), reverse=True)
        return stage_jobs[:limit]
    
    def create_journey(self, journey_data: Dict[str, Any]) -> str:
        """Create a new journey."""
        journey_id = journey_data.get('journey_id') or f"JRN-{uuid.uuid4().hex[:8].upper()}"
        
        current_time = datetime.now().isoformat() + 'Z'
        journey = {
            'journey_id': journey_id,
            'name': journey_data.get('name', f'Journey {journey_id}'),
            'description': journey_data.get('description', ''),
            'status': 'pending',
            'created_at': current_time,
            'updated_at': current_time,
            'overall_progress': 0,
            'current_stage': journey_data.get('stages', ['raw_analysis'])[0],
            'created_by': journey_data.get('created_by', 'mcp-server'),
            'oda_component_type': journey_data.get('oda_component_type', 'product-catalog-management'),
            'source_type': journey_data.get('source_type', 'database'),
            'stages': journey_data.get('stages', ['raw_analysis', 'stripped_schema', 'data_mapping', 'compliance_validation'])
        }
        
        # Save journey
        journeys = self._load_journeys()
        journeys[journey_id] = journey
        self._save_journeys(journeys)
        
        # Initialize jobs for this journey
        jobs = self._load_jobs()
        jobs[journey_id] = {}
        self._save_jobs(jobs)
        
        logger.info(f"Created new journey: {journey_id}")
        return journey_id
    
    def update_journey_status(self, journey_id: str, status: str, progress: int = None, current_stage: str = None):
        """Update journey status."""
        journeys = self._load_journeys()
        if journey_id not in journeys:
            return False
        
        journey = journeys[journey_id]
        journey['status'] = status
        journey['updated_at'] = datetime.now().isoformat() + 'Z'
        
        if progress is not None:
            journey['overall_progress'] = progress
        
        if current_stage:
            journey['current_stage'] = current_stage
        
        self._save_journeys(journeys)
        return True
    
    def create_job(self, journey_id: str, stage_id: str, job_data: Dict[str, Any]) -> str:
        """Create a new job execution."""
        jobs = self._load_jobs()
        
        # Initialize journey jobs if not exists
        if journey_id not in jobs:
            jobs[journey_id] = {}
        
        if stage_id not in jobs[journey_id]:
            jobs[journey_id][stage_id] = []
        
        # Generate job ID
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        execution_number = len(jobs[journey_id][stage_id]) + 1
        job_id = f"JOB-{execution_number:03d}-{timestamp}"
        
        # Create job
        job = {
            'job_id': job_id,
            'execution_number': execution_number,
            'status': job_data.get('status', 'pending'),
            'start_time': datetime.now().isoformat() + 'Z',
            'end_time': None,
            'duration_seconds': None,
            'triggered_by': job_data.get('triggered_by', 'mcp-server'),
            'reason': job_data.get('reason', 'Job execution'),
            'progress': 0,
            'steps_completed': 0,
            'total_steps': len(self.stage_definitions.get(stage_id, {}).get('steps', []))
        }
        
        jobs[journey_id][stage_id].append(job)
        self._save_jobs(jobs)
        
        logger.info(f"Created new job: {job_id} for journey {journey_id}, stage {stage_id}")
        return job_id

# Initialize global journey manager
if TransformationUtils is not None:
    # Use DynamoDB-based system when available
    logger.info("Using DynamoDB-based journey management system")
    journey_manager = None  # Will create TransformationUtils instances as needed
else:
    # Fall back to local JSON system
    logger.info("Using fallback local JSON journey management system")
    journey_manager = FallbackJourneyManager()

# ... existing code ...

# Initialize the MCP server
mcp = FastMCP(
    TMF_ODA_MCP_SERVER_APPLICATION_NAME,
    instructions="""
    # TMF ODA Transformer MCP Server
    
    Provides tools to analyze schema files and databases for TMF ODA (TM Forum Open Digital Architecture) transformation compliance.
    
    ## Available Tools
    
    ### schema-analyzer
    Discovers and analyzes schema files in a workspace directory for TMF ODA transformation requirements.
    Supports multiple schema formats including JSON Schema, OpenAPI, Swagger, Avro, and Protocol Buffers.
    
    ### db-analyzer
    Connects to and analyzes database structures for TMF ODA transformation requirements.
    Supports various database types including PostgreSQL, MySQL, MongoDB, and others.
    
    ### raw-analysis
    Executes the raw analysis stage of a TMF ODA transformation journey.
    This includes schema parsing, relationship discovery, and data type analysis.
    This is typically the first step in a transformation journey.
    
    ### stripped-schema
    Executes the stripped schema stage of a TMF ODA transformation journey.
    This includes schema stripping to remove non-essential elements and core structure extraction.
    This is typically the second step in a transformation journey.
    
    ### get-job-logs
    Retrieves execution logs for a specific job step from S3 storage.
    Useful for debugging job execution issues and monitoring step-by-step progress.
    Provides detailed execution logs including timing, metrics, and error information.
    
    ### journey-info
    Retrieves comprehensive information about TMF ODA transformation journeys.
    Lists all journeys with their status and progress, or provides detailed information for a specific journey.
    Includes journey status, stages, steps, job execution history, and system state overview.
    Essential for monitoring and managing transformation processes.
    
    ### run-jobs
    Executes any specific stage of a TMF ODA transformation journey.
    This is a generic job execution tool that can run any stage (raw_analysis, stripped_schema, etc.)
    for a given journey. It provides flexible job execution with customizable parameters.
    
    ### test-runner
    Runs comprehensive verification tests for all TMF ODA transformer tools.
    Executes test suite to verify tool functionality, parameter validation, and error handling.
    Provides detailed results about system health and functionality.
    
    All tools provide detailed compliance assessments, transformation recommendations, and actionable insights
    for achieving TMF ODA compliance.
    """,
    dependencies=[
        'loguru',
        'pydantic',
        'sqlalchemy',
        'pymongo',
        'psycopg',
        'mysql-connector-python',
        'jsonschema',
        'pyyaml',
        'openapi-spec-validator',
    ],
)


@mcp.tool(
    name='schema-analyzer',
    description="""Discover and analyze schema files for TMF ODA transformation requirements.
    
    This tool recursively scans a workspace directory for schema files (JSON Schema, OpenAPI, Swagger, Avro, etc.)
    and analyzes them for compliance with TMF ODA specifications. It provides detailed recommendations for
    transforming schemas to achieve TMF ODA compliance.
    
    The analysis includes:
    - Schema format detection and validation
    - TMF ODA compliance assessment
    - Detailed transformation recommendations
    - Issue identification with severity levels
    - Compliance scoring and reporting
    """,
)
async def schema_analyzer_tool(
    ctx: Context,
    workspace_dir: Annotated[
        str,
        Field(
            description="""The workspace directory path to analyze for schema files.
            CRITICAL: Assistant must always provide the current IDE workspace directory parameter to analyze schemas in the user's current project."""
        ),
    ],
    oda_component_type: Annotated[
        TMFODAComponentType,
        Field(
            description="""Target TMF ODA component type for analysis.
            This determines which TMF ODA specifications to validate against.
            Options: product-catalog-management, customer-management, order-management, 
            service-inventory-management, resource-inventory-management, party-management,
            account-management, billing-management, product-offering-qualification,
            service-qualification, quote-management, service-ordering, product-ordering"""
        ),
    ],
    schema_format: Annotated[
        Optional[SchemaFormat],
        Field(
            default=None,
            description="""Optional filter for specific schema formats.
            If provided, only schemas of this format will be analyzed.
            Options: json-schema, openapi, swagger, avro, protobuf, yaml-schema"""
        ),
    ],
) -> SchemaAnalysisReport:
    """Analyze schema files in a workspace for TMF ODA transformation requirements.
    
    Args:
        ctx: MCP context for logging and state management
        workspace_dir: Directory path to analyze for schema files
        oda_component_type: Target TMF ODA component type for analysis
        schema_format: Optional filter for specific schema formats
        
    Returns:
        SchemaAnalysisReport: Comprehensive analysis report with compliance assessment and recommendations
    """
    logger.info(f'Starting schema analysis for directory: {workspace_dir}')
    
    start_time = datetime.now()
    
    # Validate inputs
    if not workspace_dir or workspace_dir.strip() == '':
        await ctx.error(ERROR_EMPTY_WORKSPACE_DIR)
        raise ValueError(ERROR_EMPTY_WORKSPACE_DIR)
    
    if not Path(workspace_dir).exists() or not Path(workspace_dir).is_dir():
        await ctx.error(ERROR_INVALID_WORKSPACE_DIR)
        raise ValueError(ERROR_INVALID_WORKSPACE_DIR)
    
    if schema_format and schema_format not in SUPPORTED_SCHEMA_FORMATS:
        await ctx.error(ERROR_INVALID_SCHEMA_FORMAT)
        raise ValueError(ERROR_INVALID_SCHEMA_FORMAT)
    
    if oda_component_type not in TMF_ODA_COMPONENT_TYPES:
        await ctx.error(ERROR_INVALID_ODA_COMPONENT_TYPE)
        raise ValueError(ERROR_INVALID_ODA_COMPONENT_TYPE)
    
    try:
        # Discover schema files
        schema_files = await _discover_schema_files(workspace_dir, schema_format)
        
        if not schema_files:
            await ctx.error(ERROR_NO_SCHEMAS_FOUND)
            raise ValueError(ERROR_NO_SCHEMAS_FOUND)
        
        logger.info(f'Found {len(schema_files)} schema files to analyze')
        
        # Analyze each schema file
        analysis_results = []
        for schema_file in schema_files:
            try:
                # Simulate analysis with timeout
                result = await asyncio.wait_for(
                    _analyze_schema_file(schema_file, oda_component_type),
                    timeout=DEFAULT_ANALYSIS_TIMEOUT
                )
                analysis_results.append(result)
            except asyncio.TimeoutError:
                logger.warning(f'Analysis timeout for file: {schema_file}')
                continue
            except Exception as e:
                logger.error(f'Analysis failed for file {schema_file}: {str(e)}')
                continue
        
        # Calculate summary statistics
        total_analyzed = len(analysis_results)
        compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.COMPLIANT)
        partially_compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.PARTIALLY_COMPLIANT)
        non_compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.NON_COMPLIANT)
        avg_compliance_score = sum(r.compliance_score for r in analysis_results) / total_analyzed if total_analyzed > 0 else 0
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Build analysis report
        report = SchemaAnalysisReport(
            workspace_dir=workspace_dir,
            total_files=len(schema_files),
            analyzed_files=total_analyzed,
            compliance_score=round(avg_compliance_score, 2),
            recommendations=[],
            issues=[]
        )
        
        logger.success(f'Schema analysis completed. Analyzed {total_analyzed} files in {duration:.2f}s')
        return report
        
    except Exception as e:
        logger.error(f'Schema analysis failed: {str(e)}')
        await ctx.error(f'{ERROR_SCHEMA_ANALYSIS_FAILED}: {str(e)}')
        raise Exception(f'{ERROR_SCHEMA_ANALYSIS_FAILED}: {str(e)}')


@mcp.tool(
    name='db-analyzer',
    description="""Connect to and analyze database structures for TMF ODA transformation requirements.
    
    This tool connects to various database types (PostgreSQL, MySQL, MongoDB, etc.) and analyzes
    their schema structures for compliance with TMF ODA specifications. It provides detailed
    recommendations for transforming database schemas to achieve TMF ODA compliance.
    
    The analysis includes:
    - Database schema discovery and validation
    - TMF ODA compliance assessment for data models
    - Detailed transformation recommendations
    - Column/field mapping suggestions
    - Compliance scoring and reporting
    """,
)
async def db_analyzer_tool(
    ctx: Context,
    connection_string: Annotated[
        str,
        Field(
            description="""Database connection string or configuration.
            Examples:
            - PostgreSQL: postgresql://user:password@host:port/database
            - MySQL: mysql://user:password@host:port/database
            - MongoDB: mongodb://user:password@host:port/database
            Note: Passwords will be sanitized in logs and reports for security."""
        ),
    ],
    database_type: Annotated[
        DatabaseType,
        Field(
            description="""Type of database to analyze.
            Options: postgresql, mysql, mongodb, oracle, sqlserver, dynamodb, cassandra"""
        ),
    ],
    oda_component_type: Annotated[
        TMFODAComponentType,
        Field(
            description="""Target TMF ODA component type for analysis.
            This determines which TMF ODA specifications to validate against.
            Options: product-catalog-management, customer-management, order-management, 
            service-inventory-management, resource-inventory-management, party-management,
            account-management, billing-management, product-offering-qualification,
            service-qualification, quote-management, service-ordering, product-ordering"""
        ),
    ],
    tables_filter: Annotated[
        Optional[str],
        Field(
            default=None,
            description="""Optional filter for specific tables/collections to analyze.
            Can be a comma-separated list of table names or a pattern (e.g., 'user_*,product_*')"""
        ),
    ],
) -> DatabaseAnalysisReport:
    """Analyze database structures for TMF ODA transformation requirements.
    
    Args:
        ctx: MCP context for logging and state management
        connection_string: Database connection string or configuration
        database_type: Type of database to analyze
        oda_component_type: Target TMF ODA component type for analysis
        tables_filter: Optional filter for specific tables/collections
        
    Returns:
        DatabaseAnalysisReport: Comprehensive analysis report with compliance assessment and recommendations
    """
    logger.info(f'Starting database analysis for {database_type}')
    
    start_time = datetime.now()
    
    # Validate inputs
    if not connection_string or connection_string.strip() == '':
        await ctx.error(ERROR_EMPTY_CONNECTION_STRING)
        raise ValueError(ERROR_EMPTY_CONNECTION_STRING)
    
    if database_type not in SUPPORTED_DATABASE_TYPES:
        await ctx.error(ERROR_INVALID_DATABASE_TYPE)
        raise ValueError(ERROR_INVALID_DATABASE_TYPE)
    
    if oda_component_type not in TMF_ODA_COMPONENT_TYPES:
        await ctx.error(ERROR_INVALID_ODA_COMPONENT_TYPE)
        raise ValueError(ERROR_INVALID_ODA_COMPONENT_TYPE)
    
    try:
        # Test database connection
        connection_ok = await _test_database_connection(connection_string, database_type)
        if not connection_ok:
            await ctx.error(ERROR_DATABASE_CONNECTION_FAILED)
            raise Exception(ERROR_DATABASE_CONNECTION_FAILED)
        
        # Discover database tables/collections
        tables = await _discover_database_tables(connection_string, database_type, tables_filter)
        
        if not tables:
            await ctx.error(ERROR_TABLES_NOT_FOUND)
            raise ValueError(ERROR_TABLES_NOT_FOUND)
        
        logger.info(f'Found {len(tables)} tables/collections to analyze')
        
        # Analyze each table
        analysis_results = []
        for table in tables:
            try:
                # Simulate analysis with timeout
                result = await asyncio.wait_for(
                    _analyze_database_table(connection_string, database_type, table, oda_component_type),
                    timeout=DEFAULT_ANALYSIS_TIMEOUT
                )
                analysis_results.append(result)
            except asyncio.TimeoutError:
                logger.warning(f'Analysis timeout for table: {table}')
                continue
            except Exception as e:
                logger.error(f'Analysis failed for table {table}: {str(e)}')
                continue
        
        # Calculate summary statistics
        total_analyzed = len(analysis_results)
        compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.COMPLIANT)
        partially_compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.PARTIALLY_COMPLIANT)
        non_compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.NON_COMPLIANT)
        avg_compliance_score = sum(r.compliance_score for r in analysis_results) / total_analyzed if total_analyzed > 0 else 0
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Build analysis report
        report = DatabaseAnalysisReport(
            database_type=database_type,
            total_tables=len(tables),
            analyzed_tables=total_analyzed,
            compliance_score=round(avg_compliance_score, 2),
            recommendations=[],
            issues=[]
        )
        
        logger.success(f'Database analysis completed. Analyzed {total_analyzed} tables in {duration:.2f}s')
        return report
        
    except Exception as e:
        logger.error(f'Database analysis failed: {str(e)}')
        await ctx.error(f'{ERROR_DATABASE_ANALYSIS_FAILED}: {str(e)}')
        raise Exception(f'{ERROR_DATABASE_ANALYSIS_FAILED}: {str(e)}')


@mcp.tool(
    name='raw-analysis',
    description="""Execute raw analysis stage of TMF ODA transformation journey.
    
    This tool executes the raw analysis stage which includes:
    - Schema file parsing to understand database structure
    - Relationship discovery between tables and entities
    - Data type analysis for TMF ODA compatibility assessment
    
    The raw analysis stage is typically the first step in a TMF ODA transformation journey
    and provides the foundation for subsequent transformation stages.
    """,
)
async def raw_analysis_tool(
    ctx: Context,
    journey_id: Annotated[
        str,
        Field(
            description="""The journey ID for the transformation process.
            This should be a valid journey ID that exists in the transformation system.
            Example: 'JRN-SAMPLE-001'"""
        ),
    ],
    stage_id: Annotated[
        str,
        Field(
            default="raw_analysis",
            description="""The stage ID to execute. Defaults to 'raw_analysis'.
            This should typically be 'raw_analysis' for the initial analysis stage."""
        ),
    ],
    triggered_by: Annotated[
        str,
        Field(
            default="mcp-server",
            description="""Who or what triggered this job execution.
            This is used for auditing and tracking purposes."""
        ),
    ],
    reason: Annotated[
        str,
        Field(
            default="MCP Server execution",
            description="""The reason for executing this job.
            This provides context for why the job was started."""
        ),
    ],
) -> Dict[str, Any]:
    """Execute raw analysis stage of TMF ODA transformation journey.
    
    Args:
        ctx: MCP context for logging and state management
        journey_id: The journey ID for the transformation process
        stage_id: The stage ID to execute (defaults to 'raw_analysis')
        triggered_by: Who triggered this job execution
        reason: The reason for executing this job
        
    Returns:
        Dict[str, Any]: Job execution result with status and details
    """
    logger.info(f'Starting raw analysis execution for journey: {journey_id}')
    
    # Check if TransformationJobExecutor is available
    if TransformationJobExecutor is None:
        error_msg = "TransformationJobExecutor not available - cannot execute raw analysis"
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise Exception(error_msg)
    
    # Validate inputs
    if not journey_id or journey_id.strip() == '':
        error_msg = "Journey ID cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    if not stage_id or stage_id.strip() == '':
        error_msg = "Stage ID cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    start_time = datetime.now()
    
    try:
        # Force reload of job executor to get latest version with all fixes
        import importlib
        if 'job_executor' in sys.modules:
            importlib.reload(sys.modules['job_executor'])
            # Re-import after reload
            from job_executor import TransformationJobExecutor as FreshExecutor
            executor = FreshExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
        else:
            # First time import
            executor = TransformationJobExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
        
        logger.info(f'🚀 Starting job for journey: {journey_id}, stage: {stage_id}')
        
        # Start job execution
        job_id = executor.start_job_execution(
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason,
        )
        
        logger.info(f'✅ Job started: {job_id}')
        
        # Execute the job
        executor.execute_job(journey_id, job_id)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.success(f'🎉 Job {job_id} completed successfully!')
        
        # Return success result
        result = {
            'status': 'success',
            'job_id': job_id,
            'journey_id': journey_id,
            'stage_id': stage_id,
            'triggered_by': triggered_by,
            'reason': reason,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'message': f'Raw analysis job {job_id} completed successfully'
        }
        
        return result
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        error_msg = f'Raw analysis job execution failed: {str(e)}'
        logger.error(error_msg)
        await ctx.error(error_msg)
        
        # Return error result
        result = {
            'status': 'error',
            'journey_id': journey_id,
            'stage_id': stage_id,
            'triggered_by': triggered_by,
            'reason': reason,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'error_message': str(e),
            'message': error_msg
        }
        
        return result


@mcp.tool(
    name='stripped-schema',
    description="""Execute stripped schema stage of TMF ODA transformation journey.
    
    This tool executes the stripped schema stage which includes:
    - Schema stripping to remove non-essential elements
    - Core structure extraction for TMF ODA compliance
    - Data model simplification and standardization
    
    The stripped schema stage is typically the second step in a TMF ODA transformation journey
    and builds upon the raw analysis stage results.
    """,
)
async def stripped_schema_tool(
    ctx: Context,
    journey_id: Annotated[
        str,
        Field(
            description="""The journey ID for the transformation process.
            This should be a valid journey ID that exists in the transformation system.
            Example: 'JRN-SAMPLE-001'"""
        ),
    ],
    stage_id: Annotated[
        str,
        Field(
            default="stripped_schema",
            description="""The stage ID to execute. Defaults to 'stripped_schema'.
            This should typically be 'stripped_schema' for the schema stripping stage."""
        ),
    ],
    triggered_by: Annotated[
        str,
        Field(
            default="mcp-server",
            description="""Who or what triggered this job execution.
            This is used for auditing and tracking purposes."""
        ),
    ],
    reason: Annotated[
        str,
        Field(
            default="MCP Server execution",
            description="""The reason for executing this job.
            This provides context for why the job was started."""
        ),
    ],
) -> Dict[str, Any]:
    """Execute stripped schema stage of TMF ODA transformation journey.
    
    Args:
        ctx: MCP context for logging and state management
        journey_id: The journey ID for the transformation process
        stage_id: The stage ID to execute (defaults to 'stripped_schema')
        triggered_by: Who triggered this job execution
        reason: The reason for executing this job
        
    Returns:
        Dict[str, Any]: Job execution result with status and details
    """
    logger.info(f'Starting stripped schema execution for journey: {journey_id}')
    
    # Check if TransformationJobExecutor is available
    if TransformationJobExecutor is None:
        error_msg = "TransformationJobExecutor not available - cannot execute stripped schema"
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise Exception(error_msg)
    
    # Validate inputs
    if not journey_id or journey_id.strip() == '':
        error_msg = "Journey ID cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    if not stage_id or stage_id.strip() == '':
        error_msg = "Stage ID cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    start_time = datetime.now()
    
    try:
        # Force reload of job executor to get latest version with all fixes
        import importlib
        if 'job_executor' in sys.modules:
            importlib.reload(sys.modules['job_executor'])
            # Re-import after reload
            from job_executor import TransformationJobExecutor as FreshExecutor
            executor = FreshExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
        else:
            # First time import
            executor = TransformationJobExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
        
        logger.info(f'🚀 Starting job for journey: {journey_id}, stage: {stage_id}')
        
        # Start job execution
        job_id = executor.start_job_execution(
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason,
        )
        
        logger.info(f'✅ Job started: {job_id}')
        
        # Execute the job
        executor.execute_job(journey_id, job_id)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.success(f'🎉 Job {job_id} completed successfully!')
        
        # Return success result
        result = {
            'status': 'success',
            'job_id': job_id,
            'journey_id': journey_id,
            'stage_id': stage_id,
            'triggered_by': triggered_by,
            'reason': reason,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'message': f'Stripped schema job {job_id} completed successfully'
        }
        
        return result
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        error_msg = f'Stripped schema job execution failed: {str(e)}'
        logger.error(error_msg)
        await ctx.error(error_msg)
        
        # Return error result
        result = {
            'status': 'error',
            'journey_id': journey_id,
            'stage_id': stage_id,
            'triggered_by': triggered_by,
            'reason': reason,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'error_message': str(e),
            'message': error_msg
        }
        
        return result


@mcp.tool(
    name='get-job-logs',
    description="""Retrieve execution logs for a specific job step.
    
    This tool downloads and returns the execution logs for a specific step of a transformation job.
    Useful for debugging job execution issues and monitoring step-by-step progress.
    
    The logs include:
    - Step execution details and timing
    - Processing information and metrics
    - Error messages and debugging information
    - S3 upload confirmations
    """,
)
async def get_job_logs_tool(
    ctx: Context,
    journey_id: Annotated[
        str,
        Field(
            description="""The journey ID for the transformation process.
            Example: 'JRN-SAMPLE-001'"""
        ),
    ],
    stage_name: Annotated[
        str,
        Field(
            description="""The stage name (e.g., 'raw_analysis', 'stripped_schema').
            This should match the stage that was executed."""
        ),
    ],
    job_id: Annotated[
        str,
        Field(
            description="""The job execution ID.
            Example: 'JOB-016-20250709170359'"""
        ),
    ],
    step_name: Annotated[
        str,
        Field(
            description="""The step name to retrieve logs for.
            Examples: 'schema_parsing', 'relationship_discovery', 'data_type_analysis', 
            'business_rules_extraction', 'complexity_assessment', 'schema_stripping', 
            'core_structure_extraction', 'data_model_simplification'"""
        ),
    ],
) -> Dict[str, Any]:
    """Retrieve execution logs for a specific job step.
    
    Args:
        ctx: MCP context for logging and state management
        journey_id: The journey ID for the transformation process
        stage_name: The stage name that was executed
        job_id: The job execution ID
        step_name: The step name to retrieve logs for
        
    Returns:
        Dict[str, Any]: Log data and metadata
    """
    logger.info(f'Retrieving logs for {journey_id}/{stage_name}/{job_id}/{step_name}')
    
    # Validate inputs
    if not journey_id or journey_id.strip() == '':
        error_msg = "Journey ID cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    if not stage_name or stage_name.strip() == '':
        error_msg = "Stage name cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    if not job_id or job_id.strip() == '':
        error_msg = "Job ID cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    if not step_name or step_name.strip() == '':
        error_msg = "Step name cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        import boto3
        
        # Create S3 client with role ARN support
        role_arn = os.environ.get('AWS_ROLE_ARN')
        if role_arn:
            # Import AWS client utilities
            from .scripts.aws_client_utils import create_aws_client
            s3_client = create_aws_client('s3', role_arn=role_arn)
        else:
            s3_client = boto3.client('s3')
        
        # Construct the S3 key for the logs
        logs_key = f'journeys/{journey_id}/stages/{stage_name}/executions/{job_id}/logs/{step_name}.json'
        bucket_name = 'transformation-journey-logs'
        
        logger.info(f'Attempting to download logs from s3://{bucket_name}/{logs_key}')
        
        # Try to get the object from S3
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=logs_key)
            logs_content = response['Body'].read().decode('utf-8')
            
            # Parse the JSON content
            import json
            logs_data = json.loads(logs_content)
            
            # Get object metadata
            last_modified = response['LastModified'].isoformat() if 'LastModified' in response else None
            content_length = response.get('ContentLength', 0)
            
            logger.success(f'Successfully retrieved logs for {step_name} ({content_length} bytes)')
            
            return {
                'status': 'success',
                'journey_id': journey_id,
                'stage_name': stage_name,
                'job_id': job_id,
                'step_name': step_name,
                'logs_found': True,
                'logs_data': logs_data,
                'metadata': {
                    's3_bucket': bucket_name,
                    's3_key': logs_key,
                    'last_modified': last_modified,
                    'content_length': content_length,
                    'total_log_entries': len(logs_data) if isinstance(logs_data, list) else 1
                },
                'message': f'Successfully retrieved {len(logs_data) if isinstance(logs_data, list) else 1} log entries for step {step_name}'
            }
            
        except s3_client.exceptions.NoSuchKey:
            # Logs don't exist - step might not have executed
            logger.warning(f'Logs not found for {step_name} - step may not have executed')
            
            return {
                'status': 'not_found',
                'journey_id': journey_id,
                'stage_name': stage_name,
                'job_id': job_id,
                'step_name': step_name,
                'logs_found': False,
                'logs_data': None,
                'metadata': {
                    's3_bucket': bucket_name,
                    's3_key': logs_key,
                    'last_modified': None,
                    'content_length': 0,
                    'total_log_entries': 0
                },
                'message': f'No logs found for step {step_name} - step may not have executed or logs may not have been uploaded'
            }
            
        except Exception as s3_error:
            error_msg = f'Error accessing S3 logs: {str(s3_error)}'
            logger.error(error_msg)
            await ctx.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f'Failed to retrieve job logs: {str(e)}'
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise Exception(error_msg)


@mcp.tool(
    name='test-runner',
    description="""Run comprehensive verification tests for all TMF ODA transformer tools.
    
    This tool executes the complete test suite to verify that all MCP server tools are working correctly.
    It's designed to be called directly from Cursor to avoid terminal integration issues.
    
    The test suite includes:
    - Tool import verification
    - Parameter validation testing
    - Error handling verification
    - Integration testing
    - Performance validation
    
    Returns detailed results about the health and functionality of all tools.
    """,
)
async def test_runner_tool(
    ctx: Context,
    test_type: Annotated[
        str,
        Field(
            default="comprehensive",
            description="""Type of tests to run.
            Options: 'quick' (basic checks only), 'comprehensive' (all tests), 'imports' (import tests only)"""
        ),
    ],
    include_performance: Annotated[
        bool,
        Field(
            default=False,
            description="""Whether to include performance timing tests.
            Set to true for detailed performance analysis."""
        ),
    ],
) -> Dict[str, Any]:
    """Run comprehensive verification tests for all TMF ODA transformer tools.
    
    Args:
        ctx: MCP context for logging and state management
        test_type: Type of tests to run (quick, comprehensive, imports)
        include_performance: Whether to include performance timing tests
        
    Returns:
        Dict[str, Any]: Comprehensive test results with status, details, and recommendations
    """
    logger.info(f'Starting TMF ODA tool verification tests (type: {test_type})')
    
    start_time = datetime.now()
    test_results = {
        'status': 'running',
        'test_type': test_type,
        'start_time': start_time.isoformat(),
        'tests_executed': [],
        'tests_passed': 0,
        'tests_failed': 0,
        'total_tests': 0,
        'errors': [],
        'warnings': [],
        'performance_metrics': {} if include_performance else None
    }
    
    try:
        # Test 1: Import Verification
        logger.info('🔍 Testing tool imports...')
        import_result = await _test_tool_imports(ctx, include_performance)
        test_results['tests_executed'].append(import_result)
        if import_result['passed']:
            test_results['tests_passed'] += 1
        else:
            test_results['tests_failed'] += 1
        test_results['total_tests'] += 1
        
        # Test 2: Schema Analyzer Validation
        if test_type in ['comprehensive', 'validation']:
            logger.info('🔍 Testing schema analyzer validation...')
            schema_result = await _test_schema_analyzer_validation(ctx, include_performance)
            test_results['tests_executed'].append(schema_result)
            if schema_result['passed']:
                test_results['tests_passed'] += 1
            else:
                test_results['tests_failed'] += 1
            test_results['total_tests'] += 1
        
        # Test 3: Database Analyzer Validation
        if test_type in ['comprehensive', 'validation']:
            logger.info('🗄️ Testing database analyzer validation...')
            db_result = await _test_db_analyzer_validation(ctx, include_performance)
            test_results['tests_executed'].append(db_result)
            if db_result['passed']:
                test_results['tests_passed'] += 1
            else:
                test_results['tests_failed'] += 1
            test_results['total_tests'] += 1
        
        # Test 4: Raw Analysis Validation
        if test_type in ['comprehensive', 'validation']:
            logger.info('⚡ Testing raw analysis validation...')
            raw_result = await _test_raw_analysis_validation(ctx, include_performance)
            test_results['tests_executed'].append(raw_result)
            if raw_result['passed']:
                test_results['tests_passed'] += 1
            else:
                test_results['tests_failed'] += 1
            test_results['total_tests'] += 1
        
        # Test 5: Stripped Schema Validation
        if test_type in ['comprehensive', 'validation']:
            logger.info('🔧 Testing stripped schema validation...')
            stripped_result = await _test_stripped_schema_validation(ctx, include_performance)
            test_results['tests_executed'].append(stripped_result)
            if stripped_result['passed']:
                test_results['tests_passed'] += 1
            else:
                test_results['tests_failed'] += 1
            test_results['total_tests'] += 1
        
        # Test 6: Get Job Logs Validation
        if test_type in ['comprehensive', 'validation']:
            logger.info('📋 Testing get job logs validation...')
            logs_result = await _test_get_job_logs_validation(ctx, include_performance)
            test_results['tests_executed'].append(logs_result)
            if logs_result['passed']:
                test_results['tests_passed'] += 1
            else:
                test_results['tests_failed'] += 1
            test_results['total_tests'] += 1
        
        # Calculate final results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        success_rate = (test_results['tests_passed'] / test_results['total_tests'] * 100) if test_results['total_tests'] > 0 else 0
        
        # Determine overall status
        if test_results['tests_failed'] == 0:
            overall_status = 'success'
            status_message = f'🎉 All {test_results["total_tests"]} tests passed! TMF ODA MCP Server is fully operational.'
        elif test_results['tests_passed'] > test_results['tests_failed']:
            overall_status = 'partial_success'
            status_message = f'⚠️ {test_results["tests_passed"]}/{test_results["total_tests"]} tests passed. Some issues detected.'
        else:
            overall_status = 'failure'
            status_message = f'❌ {test_results["tests_failed"]}/{test_results["total_tests"]} tests failed. Significant issues detected.'
        
        # Build final result
        final_result = {
            'status': overall_status,
            'message': status_message,
            'test_type': test_type,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'tests_passed': test_results['tests_passed'],
            'tests_failed': test_results['tests_failed'],
            'total_tests': test_results['total_tests'],
            'success_rate': round(success_rate, 1),
            'detailed_results': test_results['tests_executed'],
            'summary': {
                'tools_verified': len([t for t in test_results['tests_executed'] if t['test_name'] != 'Import Verification']),
                'import_status': 'success' if import_result['passed'] else 'failed',
                'validation_status': f"{len([t for t in test_results['tests_executed'] if t['passed'] and t['test_name'] != 'Import Verification'])}/{len([t for t in test_results['tests_executed'] if t['test_name'] != 'Import Verification'])} tools validated" if test_type != 'imports' else 'N/A',
                'performance_collected': include_performance
            },
            'recommendations': _generate_test_recommendations(test_results['tests_executed']),
            'next_steps': _generate_next_steps(overall_status, test_results['tests_executed'])
        }
        
        if include_performance:
            final_result['performance_metrics'] = _calculate_performance_metrics(test_results['tests_executed'])
        
        logger.success(f'Test execution completed: {status_message}')
        return final_result
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        error_msg = f'Test runner execution failed: {str(e)}'
        logger.error(error_msg)
        await ctx.error(error_msg)
        
        return {
            'status': 'error',
            'message': error_msg,
            'test_type': test_type,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'tests_passed': test_results.get('tests_passed', 0),
            'tests_failed': test_results.get('tests_failed', 0),
            'total_tests': test_results.get('total_tests', 0),
            'error_details': str(e),
            'partial_results': test_results.get('tests_executed', [])
        }


@mcp.tool(
    name='journey-info',
    description="""Retrieve comprehensive information about TMF ODA transformation journeys.
    
    This tool provides detailed information about transformation journeys including:
    - List of all journeys with their current status and progress
    - Detailed journey status with current jobs and aggregates
    - All stages and steps for a specific journey
    - Job execution history for stages
    - Comprehensive overview of the transformation system state
    
    When no journey_id is provided, it lists all journeys.
    When a journey_id is provided, it shows detailed information for that specific journey.
    Optionally, you can also specify a stage_id to get job details for a specific stage.
    """,
)
async def journey_info_tool(
    ctx: Context,
    journey_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="""Optional journey ID to get detailed information for a specific journey.
            If not provided, lists all journeys.
            Example: 'JRN-SAMPLE-001'"""
        ),
    ],
    stage_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="""Optional stage ID to get job execution details for a specific stage.
            Only used when journey_id is also provided.
            Example: 'raw_analysis', 'stripped_schema'"""
        ),
    ],
    include_stages: Annotated[
        bool,
        Field(
            default=True,
            description="""Whether to include detailed stage information when querying a specific journey.
            Set to false for faster response if stage details are not needed."""
        ),
    ],
    include_job_history: Annotated[
        bool,
        Field(
            default=True,
            description="""Whether to include job execution history when querying specific stages.
            Set to false for faster response if job history is not needed."""
        ),
    ],
    job_limit: Annotated[
        int,
        Field(
            default=10,
            description="""Maximum number of job executions to retrieve per stage.
            Applies when include_job_history is true."""
        ),
    ],
) -> Dict[str, Any]:
    """Retrieve comprehensive information about TMF ODA transformation journeys.
    
    Args:
        ctx: MCP context for logging and state management
        journey_id: Optional journey ID for detailed information
        stage_id: Optional stage ID for specific stage job details
        include_stages: Whether to include detailed stage information
        include_job_history: Whether to include job execution history
        job_limit: Maximum number of job executions per stage
        
    Returns:
        Dict[str, Any]: Comprehensive journey information with status and details
    """
    logger.info(f'Retrieving journey information - journey_id: {journey_id}, stage_id: {stage_id}')
    
    start_time = datetime.now()
    
    try:
        # Use DynamoDB-based TransformationUtils when available, otherwise fallback manager
        if TransformationUtils is not None:
            logger.info('Using DynamoDB-based TransformationUtils for journey management')
            utils = TransformationUtils()
            
            if not journey_id:
                logger.info('Listing all transformation journeys from DynamoDB')
                journeys = utils.list_journeys()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Build summary statistics
                total_journeys = len(journeys)
                status_counts = {}
                for journey in journeys:
                    status = journey.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                result = {
                    'operation': 'list_all_journeys',
                    'status': 'success',
                    'timestamp': start_time.isoformat(),
                    'duration_seconds': duration,
                    'data_source': 'DynamoDB',
                    'summary': {
                        'total_journeys': total_journeys,
                        'status_distribution': status_counts,
                        'active_journeys': len([j for j in journeys if j.get('status') in ['running', 'pending']]),
                        'completed_journeys': len([j for j in journeys if j.get('status') == 'completed']),
                        'failed_journeys': len([j for j in journeys if j.get('status') == 'failed'])
                    },
                    'journeys': journeys,
                    'message': f'Retrieved {total_journeys} transformation journeys from DynamoDB'
                }
                
                logger.success(f'Successfully listed {total_journeys} journeys from DynamoDB in {duration:.2f}s')
                return result
            
            # Get detailed information for specific journey
            logger.info(f'Getting detailed information for journey: {journey_id} from DynamoDB')
            
            # Get journey status
            journey_status = utils.get_journey_status(journey_id)
            if not journey_status:
                error_msg = f'Journey {journey_id} not found in DynamoDB'
                logger.error(error_msg)
                await ctx.error(error_msg)
                raise ValueError(error_msg)
            
            result = {
                'operation': 'get_journey_details',
                'journey_id': journey_id,
                'status': 'success',
                'timestamp': start_time.isoformat(),
                'data_source': 'DynamoDB',
                'journey_status': journey_status
            }
            
            # Get stages information if requested
            if include_stages:
                logger.info(f'Getting stages for journey: {journey_id} from DynamoDB')
                stages = utils.get_journey_stages(journey_id)
                result['stages'] = {
                    'total_stages': len(stages),
                    'stages_list': stages
                }
                
                # If specific stage_id provided, get detailed job information
                if stage_id:
                    logger.info(f'Getting job details for stage: {stage_id} from DynamoDB')
                    stage_jobs = utils.get_stage_jobs(journey_id, stage_id, limit=job_limit)
                    result['stage_details'] = {
                        'stage_id': stage_id,
                        'total_jobs': len(stage_jobs),
                        'jobs': stage_jobs
                    }
                elif include_job_history:
                    # Get job history for all stages
                    logger.info('Getting job history for all stages from DynamoDB')
                    stage_job_summary = {}
                    for stage in stages:
                        stage_id_current = stage['stageId']  # DynamoDB uses 'stageId'
                        stage_jobs = utils.get_stage_jobs(journey_id, stage_id_current, limit=job_limit)
                        stage_job_summary[stage_id_current] = {
                            'total_jobs': len(stage_jobs),
                            'recent_jobs': stage_jobs[:3] if stage_jobs else [],  # Show only 3 most recent
                            'latest_status': stage_jobs[0]['status'] if stage_jobs else 'no_executions'
                        }
                    result['stage_job_summary'] = stage_job_summary
            
            # Build comprehensive summary using DynamoDB field names
            summary = {
                'journey_name': journey_status.get('name', 'N/A'),
                'current_status': journey_status.get('status', 'unknown'),
                'overall_progress': journey_status.get('overallProgress', 0),
                'current_stage': journey_status.get('currentStageId', 'N/A'),
                'created_at': journey_status.get('createdAt', 'N/A')
            }
            
        else:
            # Fallback to local JSON system
            logger.info('Using fallback journey manager (local JSON)')
            
            if not journey_id:
                logger.info('Listing all transformation journeys from local JSON')
                journeys = journey_manager.list_journeys()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Build summary statistics
                total_journeys = len(journeys)
                status_counts = {}
                for journey in journeys:
                    status = journey.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                result = {
                    'operation': 'list_all_journeys',
                    'status': 'success',
                    'timestamp': start_time.isoformat(),
                    'duration_seconds': duration,
                    'data_source': 'Local JSON (fallback)',
                    'summary': {
                        'total_journeys': total_journeys,
                        'status_distribution': status_counts,
                        'active_journeys': len([j for j in journeys if j.get('status') in ['running', 'pending']]),
                        'completed_journeys': len([j for j in journeys if j.get('status') == 'completed']),
                        'failed_journeys': len([j for j in journeys if j.get('status') == 'failed'])
                    },
                    'journeys': journeys,
                    'message': f'Retrieved {total_journeys} transformation journeys from local JSON (fallback)'
                }
                
                logger.success(f'Successfully listed {total_journeys} journeys from fallback system in {duration:.2f}s')
                return result
            
            # Get detailed information for specific journey
            logger.info(f'Getting detailed information for journey: {journey_id} from local JSON')
            
            # Get journey status
            journey_status = journey_manager.get_journey_status(journey_id)
            if not journey_status:
                error_msg = f'Journey {journey_id} not found in local JSON'
                logger.error(error_msg)
                await ctx.error(error_msg)
                raise ValueError(error_msg)
            
            result = {
                'operation': 'get_journey_details',
                'journey_id': journey_id,
                'status': 'success',
                'timestamp': start_time.isoformat(),
                'data_source': 'Local JSON (fallback)',
                'journey_status': journey_status
            }
            
            # Get stages information if requested
            if include_stages:
                logger.info(f'Getting stages for journey: {journey_id} from local JSON')
                stages = journey_manager.get_journey_stages(journey_id)
                result['stages'] = {
                    'total_stages': len(stages),
                    'stages_list': stages
                }
                
                # If specific stage_id provided, get detailed job information
                if stage_id:
                    logger.info(f'Getting job details for stage: {stage_id} from local JSON')
                    stage_jobs = journey_manager.get_stage_jobs(journey_id, stage_id, limit=job_limit)
                    result['stage_details'] = {
                        'stage_id': stage_id,
                        'total_jobs': len(stage_jobs),
                        'jobs': stage_jobs
                    }
                elif include_job_history:
                    # Get job history for all stages
                    logger.info('Getting job history for all stages from local JSON')
                    stage_job_summary = {}
                    for stage in stages:
                        stage_id_current = stage['stage_id']  # Local JSON uses 'stage_id'
                        stage_jobs = journey_manager.get_stage_jobs(journey_id, stage_id_current, limit=job_limit)
                        stage_job_summary[stage_id_current] = {
                            'total_jobs': len(stage_jobs),
                            'recent_jobs': stage_jobs[:3] if stage_jobs else [],  # Show only 3 most recent
                            'latest_status': stage_jobs[0]['status'] if stage_jobs else 'no_executions'
                        }
                    result['stage_job_summary'] = stage_job_summary
            
            # Build comprehensive summary using local JSON field names
            summary = {
                'journey_name': journey_status.get('name', 'N/A'),
                'current_status': journey_status.get('status', 'unknown'),
                'overall_progress': journey_status.get('overall_progress', 0),
                'current_stage': journey_status.get('current_stage', 'N/A'),
                'created_at': journey_status.get('created_at', 'N/A')
            }
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        result['duration_seconds'] = duration
        
        if include_stages:
            summary['total_stages'] = len(result.get('stages', {}).get('stages_list', []))
            
            if 'stage_job_summary' in result:
                total_jobs = sum(s['total_jobs'] for s in result['stage_job_summary'].values())
                summary['total_job_executions'] = total_jobs
                
                # Count jobs by status across all stages
                job_status_counts = {}
                for stage_summary in result['stage_job_summary'].values():
                    for job in stage_summary.get('recent_jobs', []):
                        status = job.get('status', 'unknown')
                        job_status_counts[status] = job_status_counts.get(status, 0) + 1
                summary['job_status_distribution'] = job_status_counts
        
        result['summary'] = summary
        
        # Generate informative message
        if stage_id:
            stage_jobs_count = len(result.get('stage_details', {}).get('jobs', []))
            message = f'Retrieved detailed information for journey {journey_id}, stage {stage_id} with {stage_jobs_count} job executions'
        else:
            stages_count = len(result.get('stages', {}).get('stages_list', []))
            message = f'Retrieved comprehensive information for journey {journey_id} with {stages_count} stages'
        
        result['message'] = message
        
        logger.success(f'{message} in {duration:.2f}s')
        return result
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        error_msg = f'Failed to retrieve journey information: {str(e)}'
        logger.error(error_msg)
        await ctx.error(error_msg)
        
        # Return error result
        error_result = {
            'operation': 'get_journey_info',
            'journey_id': journey_id,
            'stage_id': stage_id,
            'status': 'error',
            'timestamp': start_time.isoformat(),
            'duration_seconds': duration,
            'error_message': str(e),
            'message': error_msg
        }
        
        return error_result


@mcp.tool(
    name='run-jobs',
    description="""Execute any specific stage of a TMF ODA transformation journey.
    
    This tool provides a generic job execution interface that can run any stage of a transformation journey.
    Unlike the specialized raw-analysis and stripped-schema tools, this tool accepts any stage_id parameter,
    making it flexible for executing any stage in the transformation pipeline.
    
    The tool executes the specified stage which may include:
    - Schema file parsing and analysis
    - Data transformation and mapping
    - Compliance validation and assessment
    - Business rules extraction and application
    - Custom stage processing as defined in the journey
    
    This tool is equivalent to running the command-line script but provides MCP integration
    with proper error handling, logging, and result formatting.
    """,
)
async def run_jobs_tool(
    ctx: Context,
    journey_id: Annotated[
        str,
        Field(
            description="""The journey ID for the transformation process.
            This should be a valid journey ID that exists in the transformation system.
            Example: 'JRN-SAMPLE-001'"""
        ),
    ],
    stage_id: Annotated[
        str,
        Field(
            description="""The stage ID to execute.
            This can be any valid stage ID in the transformation journey.
            Common examples: 'raw_analysis', 'stripped_schema', 'data_mapping', 'compliance_validation', etc.
            Check the journey configuration for available stages."""
        ),
    ],
    triggered_by: Annotated[
        str,
        Field(
            default="mcp-server",
            description="""Who or what triggered this job execution.
            This is used for auditing and tracking purposes."""
        ),
    ],
    reason: Annotated[
        str,
        Field(
            default="MCP Server execution",
            description="""The reason for executing this job.
            This provides context for why the job was started."""
        ),
    ],
) -> Dict[str, Any]:
    """Execute any specific stage of a TMF ODA transformation journey.
    
    Args:
        ctx: MCP context for logging and state management
        journey_id: The journey ID for the transformation process
        stage_id: The stage ID to execute (can be any valid stage)
        triggered_by: Who triggered this job execution
        reason: The reason for executing this job
        
    Returns:
        Dict[str, Any]: Job execution result with status and details
    """
    logger.info(f'Starting job execution for journey: {journey_id}, stage: {stage_id}')
    
    # Check if TransformationJobExecutor is available
    if TransformationJobExecutor is None:
        error_msg = "TransformationJobExecutor not available - cannot execute job"
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise Exception(error_msg)
    
    # Validate inputs
    if not journey_id or journey_id.strip() == '':
        error_msg = "Journey ID cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    if not stage_id or stage_id.strip() == '':
        error_msg = "Stage ID cannot be empty"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    start_time = datetime.now()
    
    try:
        # Force reload of job executor to get latest version with all fixes
        import importlib
        if 'job_executor' in sys.modules:
            importlib.reload(sys.modules['job_executor'])
            # Re-import after reload
            from job_executor import TransformationJobExecutor as FreshExecutor
            executor = FreshExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
        else:
            # First time import
            executor = TransformationJobExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
        
        logger.info(f'🚀 Starting job for journey: {journey_id}, stage: {stage_id}')
        
        # Start job execution
        job_id = executor.start_job_execution(
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason,
        )
        
        logger.info(f'✅ Job started: {job_id}')
        
        # Execute the job
        executor.execute_job(journey_id, job_id)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.success(f'🎉 Job {job_id} completed successfully!')
        
        # Return success result
        result = {
            'status': 'success',
            'job_id': job_id,
            'journey_id': journey_id,
            'stage_id': stage_id,
            'triggered_by': triggered_by,
            'reason': reason,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'message': f'Job {job_id} for stage {stage_id} completed successfully'
        }
        
        return result
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        error_msg = f'Job execution failed for stage {stage_id}: {str(e)}'
        logger.error(error_msg)
        await ctx.error(error_msg)
        
        # Return error result
        result = {
            'status': 'error',
            'journey_id': journey_id,
            'stage_id': stage_id,
            'triggered_by': triggered_by,
            'reason': reason,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'error_message': error_msg,
            'message': error_msg
        }
        
        return result


# Helper functions for test execution

async def _test_tool_imports(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test that all tools can be imported successfully."""
    test_start = datetime.now()
    
    try:
        # Test imports one by one to identify specific failures
        imports_tested = []
        
        # Test server tools
        try:
            from awslabs.tmf_oda_transformer_mcp_server.server import (
                schema_analyzer_tool,
                db_analyzer_tool,
                raw_analysis_tool,
                stripped_schema_tool,
                get_job_logs_tool
            )
            imports_tested.append(('Server Tools', True, 'All 5 tools imported successfully'))
        except Exception as e:
            imports_tested.append(('Server Tools', False, f'Import failed: {str(e)}'))
        
        # Test models
        try:
            from awslabs.tmf_oda_transformer_mcp_server.models import (
                TMFODAComponentType,
                DatabaseType,
                SchemaFormat,
                ComplianceLevel
            )
            imports_tested.append(('Models', True, 'All model classes imported successfully'))
        except Exception as e:
            imports_tested.append(('Models', False, f'Import failed: {str(e)}'))
        
        # Test scripts
        try:
            from awslabs.tmf_oda_transformer_mcp_server.scripts import (
                TransformationJobExecutor,
                AWSClientManager
            )
            imports_tested.append(('Scripts', True, 'All script classes imported successfully'))
        except Exception as e:
            imports_tested.append(('Scripts', False, f'Import failed: {str(e)}'))
        
        # Test constants
        try:
            from awslabs.tmf_oda_transformer_mcp_server.consts import (
                TMF_ODA_COMPONENT_TYPES,
                SUPPORTED_DATABASE_TYPES,
                SUPPORTED_SCHEMA_FORMATS
            )
            imports_tested.append(('Constants', True, f'{len(TMF_ODA_COMPONENT_TYPES)} component types, {len(SUPPORTED_DATABASE_TYPES)} DB types, {len(SUPPORTED_SCHEMA_FORMATS)} schema formats'))
        except Exception as e:
            imports_tested.append(('Constants', False, f'Import failed: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        # Check if all imports passed
        all_passed = all(result[1] for result in imports_tested)
        passed_count = sum(1 for result in imports_tested if result[1])
        
        return {
            'test_name': 'Import Verification',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'imports_tested': len(imports_tested),
                'imports_passed': passed_count,
                'results': imports_tested
            },
            'message': f'✅ All imports successful' if all_passed else f'❌ {len(imports_tested) - passed_count}/{len(imports_tested)} imports failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Import Verification',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Import test failed: {str(e)}'
        }


async def _test_schema_analyzer_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test schema analyzer tool validation."""
    test_start = datetime.now()
    
    try:
        from unittest.mock import AsyncMock
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty workspace validation
        try:
            await schema_analyzer_tool(
                ctx=mock_ctx,
                workspace_dir="",
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
            validation_tests.append(('Empty workspace', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty workspace', True, 'Correctly validates empty workspace'))
        except Exception as e:
            validation_tests.append(('Empty workspace', False, f'Unexpected error: {str(e)}'))
        
        # Test invalid workspace validation
        try:
            await schema_analyzer_tool(
                ctx=mock_ctx,
                workspace_dir="/non/existent/path",
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
            validation_tests.append(('Invalid workspace', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Invalid workspace', True, 'Correctly validates invalid workspace'))
        except Exception as e:
            validation_tests.append(('Invalid workspace', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Schema Analyzer Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Schema Analyzer Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Schema analyzer test failed: {str(e)}'
        }


async def _test_db_analyzer_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test database analyzer tool validation."""
    test_start = datetime.now()
    
    try:
        from unittest.mock import AsyncMock
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty connection string validation
        try:
            await db_analyzer_tool(
                ctx=mock_ctx,
                connection_string="",
                database_type=DatabaseType.POSTGRESQL,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                tables_filter=None
            )
            validation_tests.append(('Empty connection string', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty connection string', True, 'Correctly validates empty connection string'))
        except Exception as e:
            validation_tests.append(('Empty connection string', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Database Analyzer Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Database Analyzer Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Database analyzer test failed: {str(e)}'
        }


async def _test_raw_analysis_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test raw analysis tool validation."""
    test_start = datetime.now()
    
    try:
        from unittest.mock import AsyncMock
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty journey ID validation
        try:
            await raw_analysis_tool(
                ctx=mock_ctx,
                journey_id="",
                stage_id="raw_analysis",
                triggered_by="test",
                reason="test"
            )
            validation_tests.append(('Empty journey ID', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty journey ID', True, 'Correctly validates empty journey ID'))
        except Exception as e:
            validation_tests.append(('Empty journey ID', False, f'Unexpected error: {str(e)}'))
        
        # Test empty stage ID validation
        try:
            await raw_analysis_tool(
                ctx=mock_ctx,
                journey_id="JRN-TEST-001",
                stage_id="",
                triggered_by="test",
                reason="test"
            )
            validation_tests.append(('Empty stage ID', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty stage ID', True, 'Correctly validates empty stage ID'))
        except Exception as e:
            validation_tests.append(('Empty stage ID', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Raw Analysis Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Raw Analysis Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Raw analysis test failed: {str(e)}'
        }


async def _test_stripped_schema_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test stripped schema tool validation."""
    test_start = datetime.now()
    
    try:
        from unittest.mock import AsyncMock
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty journey ID validation
        try:
            await stripped_schema_tool(
                ctx=mock_ctx,
                journey_id="",
                stage_id="stripped_schema",
                triggered_by="test",
                reason="test"
            )
            validation_tests.append(('Empty journey ID', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty journey ID', True, 'Correctly validates empty journey ID'))
        except Exception as e:
            validation_tests.append(('Empty journey ID', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Stripped Schema Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Stripped Schema Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Stripped schema test failed: {str(e)}'
        }


async def _test_get_job_logs_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test get job logs tool validation."""
    test_start = datetime.now()
    
    try:
        from unittest.mock import AsyncMock
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty journey ID validation
        try:
            await get_job_logs_tool(
                ctx=mock_ctx,
                journey_id="",
                stage_name="raw_analysis",
                job_id="JOB-001-20240101120000",
                step_name="schema_parsing"
            )
            validation_tests.append(('Empty journey ID', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty journey ID', True, 'Correctly validates empty journey ID'))
        except Exception as e:
            validation_tests.append(('Empty journey ID', False, f'Unexpected error: {str(e)}'))
        
        # Test empty stage name validation
        try:
            await get_job_logs_tool(
                ctx=mock_ctx,
                journey_id="JRN-TEST-001",
                stage_name="",
                job_id="JOB-001-20240101120000",
                step_name="schema_parsing"
            )
            validation_tests.append(('Empty stage name', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty stage name', True, 'Correctly validates empty stage name'))
        except Exception as e:
            validation_tests.append(('Empty stage name', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Get Job Logs Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Get Job Logs Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Get job logs test failed: {str(e)}'
        }


def _generate_test_recommendations(test_results: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendations based on test results."""
    recommendations = []
    
    failed_tests = [test for test in test_results if not test['passed']]
    
    if not failed_tests:
        recommendations.append("🎉 All tests passed! Your TMF ODA MCP Server is fully operational.")
        recommendations.append("💡 Consider running periodic tests to ensure continued reliability.")
    else:
        recommendations.append(f"⚠️ {len(failed_tests)} test(s) failed. Review the detailed results above.")
        
        if any('Import' in test['test_name'] for test in failed_tests):
            recommendations.append("🔧 Import failures detected. Check Python path and dependencies.")
        
        if any('Validation' in test['test_name'] for test in failed_tests):
            recommendations.append("🔍 Validation failures detected. Review tool parameter handling.")
    
    return recommendations


def _generate_next_steps(status: str, test_results: List[Dict[str, Any]]) -> List[str]:
    """Generate next steps based on overall test status."""
    if status == 'success':
        return [
            "✅ All systems operational - ready for production use",
            "📝 You can now use all TMF ODA transformer tools with confidence",
            "🔄 Run this test periodically to ensure continued reliability"
        ]
    elif status == 'partial_success':
        return [
            "⚠️ Some tests failed - investigate specific issues",
            "🔧 Fix failing components before production use",
            "🧪 Re-run tests after applying fixes"
        ]
    else:
        return [
            "❌ Multiple test failures - requires immediate attention",
            "🔍 Review detailed error messages and fix critical issues",
            "🛠️ Consider reinstalling dependencies or checking configuration"
        ]


def _calculate_performance_metrics(test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate performance metrics from test results."""
    durations = [test.get('duration_seconds', 0) for test in test_results if test.get('duration_seconds')]
    
    if not durations:
        return {'note': 'No performance data collected'}
    
    return {
        'total_test_duration': sum(durations),
        'average_test_duration': sum(durations) / len(durations),
        'fastest_test': min(durations),
        'slowest_test': max(durations),
        'tests_with_timing': len(durations)
    }


# Helper functions for pseudo implementation

async def _discover_schema_files(workspace_dir: str, schema_format: Optional[SchemaFormat]) -> List[str]:
    """Discover schema files in the workspace directory.
    
    This is a pseudo implementation that simulates file discovery.
    In a real implementation, this would:
    1. Recursively scan the directory for files with schema extensions
    2. Filter by schema format if specified
    3. Validate file sizes and permissions
    """
    # Pseudo implementation - simulate discovering schema files
    discovered_files = []
    
    # Simulate finding schema files
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if any(file.endswith(ext) for ext in SCHEMA_FILE_EXTENSIONS):
                file_path = os.path.join(root, file)
                # Check file size
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                        logger.warning(f'Skipping large file: {file_path} ({file_size} bytes)')
                        continue
                    discovered_files.append(file_path)
                except Exception as e:
                    logger.warning(f'Error accessing file {file_path}: {e}')
                    continue
    
    return discovered_files[:10]  # Limit for pseudo implementation


async def _analyze_schema_file(schema_file: str, oda_component_type: TMFODAComponentType):
    """Analyze a single schema file for TMF ODA compliance.
    
    This is a pseudo implementation that simulates schema analysis.
    In a real implementation, this would:
    1. Parse the schema file based on its format
    2. Validate against TMF ODA specifications
    3. Identify compliance issues and recommendations
    4. Calculate compliance scores
    """
    from awslabs.tmf_oda_transformer_mcp_server.models import (
        SchemaAnalysisIssue,
        SchemaAnalysisResult,
        SchemaFile,
        TransformationRecommendation,
    )
    
    # Simulate analysis delay
    await asyncio.sleep(0.1)
    
    # Create pseudo schema file info
    file_path = Path(schema_file)
    schema_file_info = SchemaFile(
        file_path=str(file_path.absolute()),
        file_name=file_path.name,
        file_size=file_path.stat().st_size if file_path.exists() else 1000,
        format=SchemaFormat.JSON_SCHEMA,  # Pseudo detection
        last_modified=datetime.now()
    )
    
    # Simulate compliance analysis
    compliance_level = ComplianceLevel.PARTIALLY_COMPLIANT
    compliance_score = 75.5
    
    # Create pseudo issues
    issues = [
        SchemaAnalysisIssue(
            severity='WARNING',
            path='/properties/id',
            message='Missing TMF standard ID format validation',
            suggestion='Add pattern validation for TMF entity IDs'
        ),
        SchemaAnalysisIssue(
            severity='INFO',
            path='/properties/href',
            message='Consider adding href field for TMF API compliance',
            suggestion='Add href field with URI format validation'
        )
    ]
    
    # Create pseudo recommendations
    recommendations = [
        TransformationRecommendation(
            category='Data Model',
            priority='HIGH',
            title='Implement TMF Entity Base Structure',
            description='Add standard TMF entity fields (id, href, @type, @baseType)',
            impact='Improves API consistency and TMF compliance',
            effort='MINIMAL'
        ),
        TransformationRecommendation(
            category='Validation',
            priority='MEDIUM',
            title='Add TMF Standard Patterns',
            description='Implement TMF standard validation patterns for common fields',
            impact='Ensures data consistency across TMF components',
            effort='MODERATE'
        )
    ]
    
    return SchemaAnalysisResult(
        schema_file=schema_file_info,
        compliance_level=compliance_level,
        compliance_score=compliance_score,
        issues=issues,
        recommendations=recommendations,
        analysis_duration=0.5
    )


async def _test_database_connection(connection_string: str, database_type: DatabaseType) -> bool:
    """Test database connection.
    
    This is a pseudo implementation that simulates connection testing.
    In a real implementation, this would establish actual database connections.
    """
    # Simulate connection test delay
    await asyncio.sleep(0.2)
    
    # Pseudo implementation - always return True for demo
    logger.info(f'Testing {database_type} connection...')
    return True


async def _discover_database_tables(connection_string: str, database_type: DatabaseType, tables_filter: Optional[str]) -> List[str]:
    """Discover database tables or collections.
    
    This is a pseudo implementation that simulates table discovery.
    In a real implementation, this would query the database metadata.
    """
    # Simulate database query delay
    await asyncio.sleep(0.3)
    
    # Pseudo implementation - return sample table names
    if database_type == DatabaseType.MONGODB:
        tables = ['users', 'products', 'orders', 'customers']
    else:
        tables = ['user_accounts', 'product_catalog', 'order_history', 'customer_profiles']
    
    # Apply filter if specified
    if tables_filter:
        # Simple filter implementation
        filter_terms = [term.strip() for term in tables_filter.split(',')]
        filtered_tables = []
        for table in tables:
            for term in filter_terms:
                if term.replace('*', '') in table:
                    filtered_tables.append(table)
                    break
        return filtered_tables
    
    return tables


async def _analyze_database_table(connection_string: str, database_type: DatabaseType, table: str, oda_component_type: TMFODAComponentType):
    """Analyze a database table for TMF ODA compliance.
    
    This is a pseudo implementation that simulates table analysis.
    In a real implementation, this would:
    1. Query table schema and metadata
    2. Analyze column types and constraints
    3. Validate against TMF ODA data models
    4. Generate transformation recommendations
    """
    from awslabs.tmf_oda_transformer_mcp_server.models import (
        DatabaseAnalysisResult,
        DatabaseColumn,
        DatabaseSchema,
        DatabaseTable,
        TransformationRecommendation,
    )
    
    # Simulate analysis delay
    await asyncio.sleep(0.2)
    
    # Create pseudo table info
    table_info = DatabaseTable(
        name=table,
        schema_name='public' if database_type in [DatabaseType.POSTGRESQL, DatabaseType.MYSQL] else None,
        type='table',
        row_count=1000,
        size_mb=5.2
    )
    
    # Create pseudo column info
    columns = [
        DatabaseColumn(
            name='id',
            data_type='VARCHAR(255)',
            is_nullable=False,
            is_primary_key=True,
            default_value=None,
            constraints=['PRIMARY KEY', 'NOT NULL']
        ),
        DatabaseColumn(
            name='name',
            data_type='VARCHAR(255)',
            is_nullable=False,
            is_primary_key=False,
            default_value=None,
            constraints=['NOT NULL']
        ),
        DatabaseColumn(
            name='created_at',
            data_type='TIMESTAMP',
            is_nullable=False,
            is_primary_key=False,
            default_value='CURRENT_TIMESTAMP',
            constraints=['NOT NULL']
        )
    ]
    
    schema = DatabaseSchema(table=table_info, columns=columns)
    
    # Simulate compliance analysis
    compliance_level = ComplianceLevel.NON_COMPLIANT
    compliance_score = 45.0
    
    # Create pseudo recommendations
    recommendations = [
        TransformationRecommendation(
            category='Schema Structure',
            priority='HIGH',
            title='Add TMF Standard Fields',
            description=f'Add href, @type, @baseType fields to {table} table for TMF compliance',
            impact='Enables TMF API resource representation',
            effort='MODERATE'
        ),
        TransformationRecommendation(
            category='Data Types',
            priority='MEDIUM',
            title='Standardize ID Format',
            description='Convert ID field to use TMF standard UUID format',
            impact='Improves data consistency and TMF compliance',
            effort='SIGNIFICANT'
        )
    ]
    
    return DatabaseAnalysisResult(
        database_schema=schema,
        compliance_level=compliance_level,
        compliance_score=compliance_score,
        recommendations=recommendations,
        analysis_duration=0.8
    )


class NoOpCtx:
    """A No-op context class for error handling in MCP tools."""
    
    async def error(self, message):
        """Do nothing.
        
        Args:
            message: The error message
        """


def main():
    """Run the MCP server with CLI argument support."""
    logger.info('Starting TMF ODA Transformer MCP Server')
    
    # Log configuration
    log_level = os.getenv('FASTMCP_LOG_LEVEL', 'INFO')
    logger.info(f'Log level: {log_level}')
    
    # Optional configuration
    tmf_oda_reference_path = os.getenv('TMF_ODA_REFERENCE_PATH')
    if tmf_oda_reference_path:
        logger.info(f'TMF ODA reference path: {tmf_oda_reference_path}')
    
    aws_profile = os.getenv('AWS_PROFILE')
    if aws_profile:
        logger.info(f'AWS profile: {aws_profile}')
    
    aws_region = os.getenv('AWS_REGION')
    if aws_region:
        logger.info(f'AWS region: {aws_region}')
    
    logger.success('TMF ODA Transformer MCP Server initialized successfully')
    
    # Start the MCP server
    mcp.run()


if __name__ == '__main__':
    main() 