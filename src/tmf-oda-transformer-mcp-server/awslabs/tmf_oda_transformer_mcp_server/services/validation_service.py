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

"""Validation service for TMF ODA Transformer."""

from typing import Dict, Any, List, Optional

from loguru import logger

from ..models import TMFODAComponentType, SchemaFormat, DatabaseType
from ..consts import (
    SUPPORTED_SCHEMA_FORMATS,
    SUPPORTED_DATABASE_TYPES,
    TMF_ODA_COMPONENT_TYPES,
)


class ValidationService:
    """Service for validation operations."""

    def __init__(self):
        """Initialize the validation service."""
        pass

    def validate_workspace_directory(self, workspace_dir: str) -> Dict[str, Any]:
        """Validate workspace directory.
        
        Args:
            workspace_dir: Directory path to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        from pathlib import Path
        
        result = {
            'valid': False,
            'exists': False,
            'is_directory': False,
            'readable': False,
            'issues': []
        }
        
        try:
            if not workspace_dir or workspace_dir.strip() == '':
                result['issues'].append('Workspace directory path cannot be empty')
                return result
            
            path = Path(workspace_dir)
            
            # Check if path exists
            if not path.exists():
                result['issues'].append(f'Path does not exist: {workspace_dir}')
                return result
            result['exists'] = True
            
            # Check if it's a directory
            if not path.is_dir():
                result['issues'].append(f'Path is not a directory: {workspace_dir}')
                return result
            result['is_directory'] = True
            
            # Check if readable
            try:
                list(path.iterdir())
                result['readable'] = True
            except PermissionError:
                result['issues'].append(f'Directory is not readable: {workspace_dir}')
                return result
            
            result['valid'] = True
            
        except Exception as e:
            result['issues'].append(f'Error validating workspace directory: {str(e)}')
        
        return result

    def validate_schema_format(self, schema_format: Optional[SchemaFormat]) -> Dict[str, Any]:
        """Validate schema format.
        
        Args:
            schema_format: Schema format to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': True,
            'supported': True,
            'issues': []
        }
        
        if schema_format is None:
            # None is valid (means no filter)
            return result
        
        if schema_format not in SUPPORTED_SCHEMA_FORMATS:
            result['valid'] = False
            result['supported'] = False
            result['issues'].append(f'Unsupported schema format: {schema_format}')
            result['issues'].append(f'Supported formats: {SUPPORTED_SCHEMA_FORMATS}')
        
        return result

    def validate_oda_component_type(self, oda_component_type: TMFODAComponentType) -> Dict[str, Any]:
        """Validate TMF ODA component type.
        
        Args:
            oda_component_type: Component type to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': True,
            'supported': True,
            'issues': []
        }
        
        if oda_component_type not in TMF_ODA_COMPONENT_TYPES:
            result['valid'] = False
            result['supported'] = False
            result['issues'].append(f'Unsupported TMF ODA component type: {oda_component_type}')
            result['issues'].append(f'Supported types: {TMF_ODA_COMPONENT_TYPES}')
        
        return result

    def validate_database_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Validate database connection string.
        
        Args:
            connection_string: Connection string to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': False,
            'has_required_parts': False,
            'issues': []
        }
        
        try:
            if not connection_string or connection_string.strip() == '':
                result['issues'].append('Connection string cannot be empty')
                return result
            
            # Basic connection string validation
            connection_string = connection_string.strip()
            
            # Check for common connection string patterns
            common_prefixes = ['postgresql://', 'mysql://', 'mongodb://', 'sqlite://', 'oracle://', 'mssql://']
            
            has_valid_prefix = any(connection_string.startswith(prefix) for prefix in common_prefixes)
            
            if has_valid_prefix:
                result['has_required_parts'] = True
                result['valid'] = True
            else:
                # Check for other valid patterns (like host:port format)
                if ':' in connection_string and '@' in connection_string:
                    result['has_required_parts'] = True
                    result['valid'] = True
                else:
                    result['issues'].append('Connection string does not appear to be in a valid format')
                    result['issues'].append('Expected formats: protocol://user:password@host:port/database or similar')
        
        except Exception as e:
            result['issues'].append(f'Error validating connection string: {str(e)}')
        
        return result

    def validate_database_type(self, database_type: DatabaseType) -> Dict[str, Any]:
        """Validate database type.
        
        Args:
            database_type: Database type to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': True,
            'supported': True,
            'issues': []
        }
        
        if database_type not in SUPPORTED_DATABASE_TYPES:
            result['valid'] = False
            result['supported'] = False
            result['issues'].append(f'Unsupported database type: {database_type}')
            result['issues'].append(f'Supported types: {SUPPORTED_DATABASE_TYPES}')
        
        return result

    def validate_journey_id(self, journey_id: str) -> Dict[str, Any]:
        """Validate journey ID.
        
        Args:
            journey_id: Journey ID to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': False,
            'format_valid': False,
            'issues': []
        }
        
        try:
            if not journey_id or journey_id.strip() == '':
                result['issues'].append('Journey ID cannot be empty')
                return result
            
            # Basic format validation
            journey_id = journey_id.strip()
            
            # Check for valid journey ID format (e.g., JRN-XXXXXX-XXX)
            if len(journey_id) >= 3:
                result['format_valid'] = True
                result['valid'] = True
            else:
                result['issues'].append('Journey ID appears to be too short')
                result['issues'].append('Expected format: JRN-XXXXXX-XXX or similar')
        
        except Exception as e:
            result['issues'].append(f'Error validating journey ID: {str(e)}')
        
        return result

    def validate_stage_id(self, stage_id: str) -> Dict[str, Any]:
        """Validate stage ID.
        
        Args:
            stage_id: Stage ID to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': False,
            'known_stage': False,
            'issues': []
        }
        
        try:
            if not stage_id or stage_id.strip() == '':
                result['issues'].append('Stage ID cannot be empty')
                return result
            
            stage_id = stage_id.strip()
            
            # Check for known stage IDs
            known_stages = [
                'raw_analysis',
                'stripped_schema',
                'data_mapping',
                'compliance_validation'
            ]
            
            if stage_id in known_stages:
                result['known_stage'] = True
            
            # Basic validation - any non-empty string is valid
            result['valid'] = True
        
        except Exception as e:
            result['issues'].append(f'Error validating stage ID: {str(e)}')
        
        return result

    def validate_journey_data(self, journey_data: Dict[str, Any], operation: str = 'create') -> Dict[str, Any]:
        """Validate journey data for create/update operations.
        
        Args:
            journey_data: Journey data to validate
            operation: Operation type ('create' or 'update')
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': True,
            'has_required_fields': True,
            'field_validations': {},
            'issues': []
        }
        
        try:
            if not journey_data:
                result['issues'].append('Journey data cannot be empty')
                result['valid'] = False
                result['has_required_fields'] = False
                return result
            
            # Required fields for create operation
            if operation == 'create':
                required_fields = ['name']
                for field in required_fields:
                    if field not in journey_data:
                        result['issues'].append(f'Required field missing: {field}')
                        result['has_required_fields'] = False
                        result['valid'] = False
            
            # Validate individual fields
            if 'name' in journey_data:
                name_validation = self._validate_journey_name(journey_data['name'])
                result['field_validations']['name'] = name_validation
                if not name_validation['valid']:
                    result['valid'] = False
            
            if 'oda_component_type' in journey_data:
                component_validation = self.validate_oda_component_type(journey_data['oda_component_type'])
                result['field_validations']['oda_component_type'] = component_validation
                if not component_validation['valid']:
                    result['valid'] = False
            
            if 'status' in journey_data:
                status_validation = self._validate_journey_status(journey_data['status'])
                result['field_validations']['status'] = status_validation
                if not status_validation['valid']:
                    result['valid'] = False
            
            if 'overall_progress' in journey_data:
                progress_validation = self._validate_progress(journey_data['overall_progress'])
                result['field_validations']['overall_progress'] = progress_validation
                if not progress_validation['valid']:
                    result['valid'] = False
        
        except Exception as e:
            result['issues'].append(f'Error validating journey data: {str(e)}')
            result['valid'] = False
        
        return result

    def _validate_journey_name(self, name: str) -> Dict[str, Any]:
        """Validate journey name.
        
        Args:
            name: Journey name to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': False,
            'issues': []
        }
        
        if not name or name.strip() == '':
            result['issues'].append('Journey name cannot be empty')
            return result
        
        if len(name.strip()) < 3:
            result['issues'].append('Journey name must be at least 3 characters long')
            return result
        
        if len(name.strip()) > 200:
            result['issues'].append('Journey name cannot exceed 200 characters')
            return result
        
        result['valid'] = True
        return result

    def _validate_journey_status(self, status: str) -> Dict[str, Any]:
        """Validate journey status.
        
        Args:
            status: Journey status to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': False,
            'known_status': False,
            'issues': []
        }
        
        known_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
        
        if not status or status.strip() == '':
            result['issues'].append('Journey status cannot be empty')
            return result
        
        if status.lower() in known_statuses:
            result['known_status'] = True
        
        result['valid'] = True
        return result

    def _validate_progress(self, progress: int) -> Dict[str, Any]:
        """Validate progress value.
        
        Args:
            progress: Progress value to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'valid': False,
            'in_range': False,
            'issues': []
        }
        
        try:
            progress_int = int(progress)
            
            if progress_int < 0:
                result['issues'].append('Progress cannot be negative')
                return result
            
            if progress_int > 100:
                result['issues'].append('Progress cannot exceed 100')
                return result
            
            result['in_range'] = True
            result['valid'] = True
        
        except (ValueError, TypeError):
            result['issues'].append('Progress must be a valid integer')
        
        return result 