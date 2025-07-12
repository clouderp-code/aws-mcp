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

"""Fallback journey manager for TMF ODA Transformer (local JSON storage)."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from loguru import logger


class FallbackJourneyManager:
    """Self-contained journey management system for TMF ODA transformations using local JSON storage."""
    
    def __init__(self, data_dir: str = "/tmp/tmf_oda_journeys"):
        """Initialize the journey manager with local storage.
        
        Args:
            data_dir: Directory for storing journey data files
        """
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
                    {'id': 'data_type_analysis', 'name': 'Data Type Analysis', 'description': 'Analyze data types for TMF ODA compatibility'},
                    {'id': 'business_rules_extraction', 'name': 'Business Rules Extraction', 'description': 'Extract business rules from stored procedures and constraints'},
                    {'id': 'complexity_assessment', 'name': 'Complexity Assessment', 'description': 'Assess schema complexity and identify potential challenges'}
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
        
        logger.info(f"FallbackJourneyManager initialized with data directory: {self.data_dir}")
    
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
        
        # Initialize jobs file with comprehensive job history
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
                            'steps_completed': 5,
                            'total_steps': 5
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
                            'steps_completed': 5,
                            'total_steps': 5
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
                            'steps_completed': 5,
                            'total_steps': 5
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
    
    def update_journey_status(self, journey_id: str, status: str, progress: int = None, current_stage: str = None) -> bool:
        """Update journey status."""
        journeys = self._load_journeys()
        if journey_id not in journeys:
            return False
        
        journey = journeys[journey_id]
        if status:
            journey['status'] = status
        journey['updated_at'] = datetime.now().isoformat() + 'Z'
        
        if progress is not None:
            journey['overall_progress'] = progress
        
        if current_stage:
            journey['current_stage'] = current_stage
        
        self._save_journeys(journeys)
        return True
    
    def delete_journey(self, journey_id: str) -> Dict[str, Any]:
        """Delete a journey and associated data."""
        journeys = self._load_journeys()
        jobs = self._load_jobs()
        
        # Remove journey and associated jobs
        deleted_journey = journeys.pop(journey_id, None)
        deleted_jobs = jobs.pop(journey_id, None)
        
        if deleted_journey is None:
            raise ValueError(f'Journey {journey_id} not found')
        
        # Save updated data
        self._save_journeys(journeys)
        self._save_jobs(jobs)
        
        logger.info(f"Deleted journey: {journey_id}")
        
        return {
            'deleted_journey': deleted_journey,
            'deleted_jobs_count': len(deleted_jobs) if deleted_jobs else 0
        }
    
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