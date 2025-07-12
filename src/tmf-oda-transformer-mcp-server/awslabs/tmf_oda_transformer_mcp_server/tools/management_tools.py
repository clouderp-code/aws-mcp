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

"""Management tools for TMF ODA Transformer MCP Server."""

from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger
from mcp.server.fastmcp import Context
from pydantic import Field
from typing import Annotated

from ..models import JourneyCreateData, JourneyUpdateData
from ..services import JourneyService
from .base import BaseToolMixin


# Journey management models from server.py
class JourneyAction:
    """Journey action enumeration."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


async def journeys_tool(
    ctx: Context,
    action: Annotated[
        str,
        Field(
            default="read",
            description="""Action to perform on journeys.
            - 'list'/'read': List all journeys or get specific journey details (default)
            - 'create': Create a new journey with provided data
            - 'update': Update existing journey properties
            - 'delete': Delete journey and associated data"""
        ),
    ] = "read",
    journey_id: Annotated[
        str,
        Field(
            default="",
            description="""Journey ID for specific operations.
            - READ: Optional, if provided gets detailed info for specific journey
            - CREATE: Optional, if not provided will auto-generate
            - UPDATE/DELETE: Required
            Example: 'JRN-SAMPLE-001'"""
        ),
    ] = "",
    journey_data: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="""Journey creation/update data (JSON object).
            Required for CREATE action, optional for UPDATE.
            CREATE example: {"name": "My Journey", "oda_component_type": "customer-management"}
            UPDATE example: {"status": "completed", "overall_progress": 100}"""
        ),
    ] = None,
    stage_id: Annotated[
        str,
        Field(
            default="",
            description="""Optional stage ID to get job execution details for a specific stage.
            Only used with READ action when journey_id is also provided.
            Example: 'raw_analysis', 'stripped_schema'"""
        ),
    ] = "",
    include_stages: Annotated[
        bool,
        Field(
            default=True,
            description="""Whether to include detailed stage information when reading a specific journey.
            Set to false for faster response if stage details are not needed."""
        ),
    ] = True,
    include_job_history: Annotated[
        bool,
        Field(
            default=True,
            description="""Whether to include job execution history when reading stages.
            Set to false for faster response if job history is not needed."""
        ),
    ] = True,
    job_limit: Annotated[
        int,
        Field(
            default=10,
            description="""Maximum number of job executions to retrieve per stage.
            Applies when include_job_history is true."""
        ),
    ] = 10,
) -> Dict[str, Any]:
    """Comprehensive TMF ODA transformation journey management with full CRUD operations.
    
    Args:
        ctx: MCP context for logging and state management
        action: Action to perform (list/read, create, update, delete)
        journey_id: Journey ID for specific operations
        journey_data: Data for create/update operations
        stage_id: Optional stage ID for specific stage job details (READ only)
        include_stages: Whether to include detailed stage information (READ only)
        include_job_history: Whether to include job execution history (READ only)
        job_limit: Maximum number of job executions per stage (READ only)
        
    Returns:
        Dict[str, Any]: Operation result with status and details
    """
    tool_name = "journeys"
    start_time = datetime.now()
    
    # Handle empty inputs
    if not journey_id:
        journey_id = None
    if not stage_id:
        stage_id = None
    
    try:
        # Log tool start
        BaseToolMixin.log_tool_start(
            tool_name,
            action=action,
            journey_id=journey_id,
            has_journey_data=journey_data is not None,
            stage_id=stage_id
        )
        
        # Validate action
        valid_actions = [JourneyAction.CREATE, JourneyAction.READ, JourneyAction.UPDATE, JourneyAction.DELETE, JourneyAction.LIST]
        if action.lower() not in valid_actions:
            error_msg = f"Invalid action: {action}. Valid actions: {valid_actions}"
            logger.error(error_msg)
            await ctx.error(error_msg)
            return BaseToolMixin.create_error_result(error_msg, start_time, action=action)
        
        # Normalize action
        action = action.lower()
        
        # Create journey service
        journey_service = JourneyService()
        
        # Route to appropriate operation
        if action in [JourneyAction.LIST, JourneyAction.READ]:
            result = await _handle_journey_read(
                ctx, journey_service, journey_id, stage_id,
                include_stages, include_job_history, job_limit, start_time
            )
        elif action == JourneyAction.CREATE:
            result = await _handle_journey_create(
                ctx, journey_service, journey_id, journey_data, start_time
            )
        elif action == JourneyAction.UPDATE:
            result = await _handle_journey_update(
                ctx, journey_service, journey_id, journey_data, start_time
            )
        elif action == JourneyAction.DELETE:
            result = await _handle_journey_delete(
                ctx, journey_service, journey_id, start_time
            )
        else:
            error_msg = f"Unsupported action: {action}"
            logger.error(error_msg)
            await ctx.error(error_msg)
            return BaseToolMixin.create_error_result(error_msg, start_time, action=action)
        
        # Log success
        duration = result.get('duration_seconds', 0)
        BaseToolMixin.log_tool_success(tool_name, duration, action=action, journey_id=journey_id)
        
        return result
        
    except Exception as e:
        # Log error and return error result
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_error(tool_name, e, duration)
        error_msg = f'Journey {action} operation failed: {str(e)}'
        await ctx.error(error_msg)
        
        return BaseToolMixin.create_error_result(
            error_msg, start_time,
            operation=f'journey_{action}' if action == 'read' else f'{action}_journey',
            action=action,
            journey_id=journey_id
        )


# Helper functions for journey CRUD operations

async def _handle_journey_read(
    ctx: Context,
    journey_service: JourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    include_stages: bool,
    include_job_history: bool,
    job_limit: int,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey read/list operations."""
    try:
        if not journey_id:
            # List all journeys
            journeys = await journey_service.list_journeys()
            
            # Build summary statistics
            total_journeys = len(journeys)
            status_counts = {}
            for journey in journeys:
                status = journey.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return BaseToolMixin.create_tool_result(
                status='success',
                message=f'Retrieved {total_journeys} transformation journeys from {journey_service.get_data_source()}',
                start_time=start_time,
                operation='list_all_journeys',
                data_source=journey_service.get_data_source(),
                summary={
                    'total_journeys': total_journeys,
                    'status_distribution': status_counts,
                    'active_journeys': len([j for j in journeys if j.get('status') in ['running', 'pending']]),
                    'completed_journeys': len([j for j in journeys if j.get('status') == 'completed']),
                    'failed_journeys': len([j for j in journeys if j.get('status') == 'failed'])
                },
                journeys=journeys
            )
        
        # Get specific journey details
        journey_details = await journey_service.get_journey_details(
            journey_id=journey_id,
            stage_id=stage_id,
            include_stages=include_stages,
            include_job_history=include_job_history,
            job_limit=job_limit
        )
        
        if not journey_details:
            error_msg = f'Journey {journey_id} not found'
            logger.error(error_msg)
            # Don't call ctx.error() here - let the main function handle it
            raise ValueError(error_msg)
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved comprehensive information for journey {journey_id}',
            start_time=start_time,
            operation='get_journey_details',
            journey_id=journey_id,
            data_source=journey_service.get_data_source(),
            **journey_details
        )
        
    except Exception as e:
        error_msg = f'Failed to read journey information: {str(e)}'
        logger.error(error_msg)
        # Don't call ctx.error() here - let the main function handle it
        raise


async def _handle_journey_create(
    ctx: Context,
    journey_service: JourneyService,
    journey_id: Optional[str],
    journey_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey creation operations."""
    try:
        if not journey_data:
            error_msg = "journey_data is required for CREATE action"
            logger.error(error_msg)
            # Don't call ctx.error() here - let the main function handle it
            raise ValueError(error_msg)
        
        # Validate and parse journey data
        try:
            create_data = JourneyCreateData(**journey_data)
        except Exception as e:
            error_msg = f"Invalid journey_data format: {str(e)}"
            logger.error(error_msg)
            # Don't call ctx.error() here - let the main function handle it
            raise ValueError(error_msg)
        
        # Create journey
        created_journey_id = await journey_service.create_journey(
            journey_id=journey_id,
            journey_data=create_data.model_dump()
        )
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Journey {created_journey_id} created successfully' + (' (DynamoDB - simulated)' if journey_service.get_data_source() == 'DynamoDB' else ''),
            start_time=start_time,
            operation='create_journey',
            action='create',
            journey_id=created_journey_id,
            journey_data=create_data.model_dump(),
            data_source=journey_service.get_data_source()
        )
        
    except Exception as e:
        error_msg = f'Failed to create journey: {str(e)}'
        logger.error(error_msg)
        # Don't call ctx.error() here - let the main function handle it
        raise


async def _handle_journey_update(
    ctx: Context,
    journey_service: JourneyService,
    journey_id: Optional[str],
    journey_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey update operations."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for UPDATE action"
            logger.error(error_msg)
            # Don't call ctx.error() here - let the main function handle it
            raise ValueError(error_msg)
        
        if not journey_data:
            error_msg = "journey_data is required for UPDATE action"
            logger.error(error_msg)
            # Don't call ctx.error() here - let the main function handle it
            raise ValueError(error_msg)
        
        # Validate and parse update data
        try:
            update_data = JourneyUpdateData(**journey_data)
        except Exception as e:
            error_msg = f"Invalid journey_data format for update: {str(e)}"
            logger.error(error_msg)
            # Don't call ctx.error() here - let the main function handle it
            raise ValueError(error_msg)
        
        # Update journey
        update_result = await journey_service.update_journey(
            journey_id=journey_id,
            journey_data=update_data.model_dump()
        )
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Journey {journey_id} updated successfully',
            start_time=start_time,
            operation='update_journey',
            action='update',
            journey_id=journey_id,
            update_data={k: v for k, v in update_data.model_dump().items() if v is not None},
            data_source=journey_service.get_data_source(),
            **update_result
        )
        
    except Exception as e:
        error_msg = f'Failed to update journey: {str(e)}'
        logger.error(error_msg)
        # Don't call ctx.error() here - let the main function handle it
        raise


async def _handle_journey_delete(
    ctx: Context,
    journey_service: JourneyService,
    journey_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey deletion operations."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for DELETE action"
            logger.error(error_msg)
            # Don't call ctx.error() here - let the main function handle it
            raise ValueError(error_msg)
        
        # Delete journey
        delete_result = await journey_service.delete_journey(journey_id=journey_id)
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Journey {journey_id} deleted successfully',
            start_time=start_time,
            operation='delete_journey',
            action='delete',
            journey_id=journey_id,
            data_source=journey_service.get_data_source(),
            **delete_result
        )
        
    except Exception as e:
        error_msg = f'Failed to delete journey: {str(e)}'
        logger.error(error_msg)
        # Don't call ctx.error() here - let the main function handle it
        raise 