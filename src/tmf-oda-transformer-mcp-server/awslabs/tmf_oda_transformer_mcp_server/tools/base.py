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

"""Base functionality for MCP tools."""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger
from mcp.server.fastmcp import Context

from ..consts import (
    ERROR_EMPTY_WORKSPACE_DIR,
    ERROR_INVALID_WORKSPACE_DIR,
    ERROR_INVALID_SCHEMA_FORMAT,
    ERROR_INVALID_ODA_COMPONENT_TYPE,
    ERROR_EMPTY_CONNECTION_STRING,
    ERROR_INVALID_DATABASE_TYPE,
    SUPPORTED_DATABASE_TYPES,
    SUPPORTED_SCHEMA_FORMATS,
    TMF_ODA_COMPONENT_TYPES,
    DEFAULT_ANALYSIS_TIMEOUT,
)
from ..models import (
    TMFODAComponentType,
    SchemaFormat,
    DatabaseType,
)


class BaseToolMixin:
    """Base mixin class for common tool functionality."""

    @staticmethod
    async def validate_workspace_dir(ctx: Context, workspace_dir: str) -> None:
        """Validate workspace directory parameter."""
        if not workspace_dir or workspace_dir.strip() == '':
            await ctx.error(ERROR_EMPTY_WORKSPACE_DIR)
            raise ValueError(ERROR_EMPTY_WORKSPACE_DIR)
        
        from pathlib import Path
        if not Path(workspace_dir).exists() or not Path(workspace_dir).is_dir():
            await ctx.error(ERROR_INVALID_WORKSPACE_DIR)
            raise ValueError(ERROR_INVALID_WORKSPACE_DIR)

    @staticmethod
    async def validate_schema_format(ctx: Context, schema_format: Optional[SchemaFormat]) -> None:
        """Validate schema format parameter."""
        if schema_format and schema_format not in SUPPORTED_SCHEMA_FORMATS:
            await ctx.error(ERROR_INVALID_SCHEMA_FORMAT)
            raise ValueError(ERROR_INVALID_SCHEMA_FORMAT)

    @staticmethod
    async def validate_oda_component_type(ctx: Context, oda_component_type: TMFODAComponentType) -> None:
        """Validate ODA component type parameter."""
        if oda_component_type not in TMF_ODA_COMPONENT_TYPES:
            await ctx.error(ERROR_INVALID_ODA_COMPONENT_TYPE)
            raise ValueError(ERROR_INVALID_ODA_COMPONENT_TYPE)

    @staticmethod
    async def validate_connection_string(ctx: Context, connection_string: str) -> None:
        """Validate database connection string parameter."""
        if not connection_string or connection_string.strip() == '':
            await ctx.error(ERROR_EMPTY_CONNECTION_STRING)
            raise ValueError(ERROR_EMPTY_CONNECTION_STRING)

    @staticmethod
    async def validate_database_type(ctx: Context, database_type: DatabaseType) -> None:
        """Validate database type parameter."""
        if database_type not in SUPPORTED_DATABASE_TYPES:
            await ctx.error(ERROR_INVALID_DATABASE_TYPE)
            raise ValueError(ERROR_INVALID_DATABASE_TYPE)

    @staticmethod
    async def validate_journey_id(ctx: Context, journey_id: str) -> None:
        """Validate journey ID parameter."""
        if not journey_id or journey_id.strip() == '':
            error_msg = "Journey ID cannot be empty"
            await ctx.error(error_msg)
            raise ValueError(error_msg)

    @staticmethod
    async def validate_stage_id(ctx: Context, stage_id: str) -> None:
        """Validate stage ID parameter."""
        if not stage_id or stage_id.strip() == '':
            error_msg = "Stage ID cannot be empty"
            await ctx.error(error_msg)
            raise ValueError(error_msg)

    @staticmethod
    def create_tool_result(
        status: str,
        message: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a standardized tool result."""
        if end_time is None:
            end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        result = {
            'status': status,
            'message': message,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'timestamp': end_time.isoformat(),  # Add timestamp for backward compatibility
            'duration_seconds': duration,
            **kwargs
        }
        
        return result

    @staticmethod
    def create_error_result(
        error_msg: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a standardized error result."""
        if end_time is None:
            end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        result = {
            'status': 'error',
            'message': error_msg,
            'error_message': error_msg,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            **kwargs
        }
        
        return result

    @staticmethod
    async def execute_with_timeout(
        operation,
        timeout: int = DEFAULT_ANALYSIS_TIMEOUT,
        operation_name: str = "Operation"
    ):
        """Execute an operation with timeout."""
        try:
            return await asyncio.wait_for(operation, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f'{operation_name} timeout after {timeout} seconds')
            raise asyncio.TimeoutError(f'{operation_name} timeout after {timeout} seconds')

    @staticmethod
    def log_tool_start(tool_name: str, **params):
        """Log tool execution start."""
        logger.info(f'Starting {tool_name} with parameters: {params}')

    @staticmethod
    def log_tool_success(tool_name: str, duration: float, **results):
        """Log tool execution success."""
        logger.success(f'{tool_name} completed successfully in {duration:.2f}s')

    @staticmethod
    def log_tool_error(tool_name: str, error: Exception, duration: float):
        """Log tool execution error."""
        logger.error(f'{tool_name} failed after {duration:.2f}s: {str(error)}')


class NoOpCtx:
    """A No-op context class for error handling in MCP tools."""
    
    async def error(self, message):
        """Do nothing - used for testing.
        
        Args:
            message: The error message
        """
        pass 