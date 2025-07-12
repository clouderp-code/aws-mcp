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

"""Execution tools for TMF ODA Transformer MCP Server."""

import os
import sys
from datetime import datetime
from typing import Dict, Any

from loguru import logger
from mcp.server.fastmcp import Context
from pydantic import Field
from typing import Annotated

from .base import BaseToolMixin


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
    ] = "raw_analysis",
    triggered_by: Annotated[
        str,
        Field(
            default="mcp-server",
            description="""Who or what triggered this job execution.
            This is used for auditing and tracking purposes."""
        ),
    ] = "mcp-server",
    reason: Annotated[
        str,
        Field(
            default="MCP Server execution",
            description="""The reason for executing this job.
            This provides context for why the job was started."""
        ),
    ] = "MCP Server execution",
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
    tool_name = "raw-analysis"
    start_time = datetime.now()
    
    # Validate inputs (outside try-catch so exceptions can propagate for testing)
    await BaseToolMixin.validate_journey_id(ctx, journey_id)
    await BaseToolMixin.validate_stage_id(ctx, stage_id)
    
    # Check if TransformationJobExecutor is available (outside try-catch so exceptions can propagate for testing)
    try:
        from ..scripts.job_executor import TransformationJobExecutor
        if TransformationJobExecutor is None:
            raise ImportError("TransformationJobExecutor is None")
    except ImportError:
        error_msg = "TransformationJobExecutor not available - cannot execute raw analysis"
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise Exception(error_msg)
    
    try:
        # Log tool start
        BaseToolMixin.log_tool_start(
            tool_name,
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason
        )
        
        # Execute job
        try:
            # Force reload of job executor to get latest version
            import importlib
            if 'job_executor' in sys.modules:
                importlib.reload(sys.modules['job_executor'])
                from ..scripts.job_executor import TransformationJobExecutor
            
            executor = TransformationJobExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
            
            # Start job execution
            job_id = executor.start_job_execution(
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason,
            )
            
            # Execute the job
            executor.execute_job(journey_id, job_id)
            
            # Create success result
            result = BaseToolMixin.create_tool_result(
                status='success',
                message=f'Raw analysis job {job_id} completed successfully',
                start_time=start_time,
                job_id=job_id,
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason
            )
            
            # Log success
            duration = result['duration_seconds']
            BaseToolMixin.log_tool_success(tool_name, duration, job_id=job_id)
            
            return result
            
        except Exception as e:
            error_msg = f'Raw analysis job execution failed: {str(e)}'
            logger.error(error_msg)
            await ctx.error(error_msg)
            
            return BaseToolMixin.create_error_result(
                error_msg, start_time,
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason
            )
        
    except Exception as e:
        # Log error and return error result
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_error(tool_name, e, duration)
        await ctx.error(f'{tool_name} failed: {str(e)}')
        
        return BaseToolMixin.create_error_result(
            f'{tool_name} failed: {str(e)}', start_time,
            journey_id=journey_id,
            stage_id=stage_id
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
    ] = "stripped_schema",
    triggered_by: Annotated[
        str,
        Field(
            default="mcp-server",
            description="""Who or what triggered this job execution.
            This is used for auditing and tracking purposes."""
        ),
    ] = "mcp-server",
    reason: Annotated[
        str,
        Field(
            default="MCP Server execution",
            description="""The reason for executing this job.
            This provides context for why the job was started."""
        ),
    ] = "MCP Server execution",
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
    tool_name = "stripped-schema"
    start_time = datetime.now()
    
    # Validate inputs (outside try-catch so exceptions can propagate for testing)
    await BaseToolMixin.validate_journey_id(ctx, journey_id)
    await BaseToolMixin.validate_stage_id(ctx, stage_id)
    
    # Check if TransformationJobExecutor is available (outside try-catch so exceptions can propagate for testing)
    try:
        from ..scripts.job_executor import TransformationJobExecutor
        if TransformationJobExecutor is None:
            raise ImportError("TransformationJobExecutor is None")
    except ImportError:
        error_msg = "TransformationJobExecutor not available - cannot execute stripped schema"
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise Exception(error_msg)
    
    try:
        # Log tool start
        BaseToolMixin.log_tool_start(
            tool_name,
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason
        )
        
        # Execute job
        try:
            # Force reload of job executor to get latest version
            import importlib
            if 'job_executor' in sys.modules:
                importlib.reload(sys.modules['job_executor'])
                from ..scripts.job_executor import TransformationJobExecutor
            
            executor = TransformationJobExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
            
            # Start job execution
            job_id = executor.start_job_execution(
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason,
            )
            
            # Execute the job
            executor.execute_job(journey_id, job_id)
            
            # Create success result
            result = BaseToolMixin.create_tool_result(
                status='success',
                message=f'Stripped schema job {job_id} completed successfully',
                start_time=start_time,
                job_id=job_id,
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason
            )
            
            # Log success
            duration = result['duration_seconds']
            BaseToolMixin.log_tool_success(tool_name, duration, job_id=job_id)
            
            return result
            
        except Exception as e:
            error_msg = f'Stripped schema job execution failed: {str(e)}'
            logger.error(error_msg)
            await ctx.error(error_msg)
            
            return BaseToolMixin.create_error_result(
                error_msg, start_time,
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason
            )
        
    except Exception as e:
        # Log error and return error result
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_error(tool_name, e, duration)
        await ctx.error(f'{tool_name} failed: {str(e)}')
        
        return BaseToolMixin.create_error_result(
            f'{tool_name} failed: {str(e)}', start_time,
            journey_id=journey_id,
            stage_id=stage_id
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
    ] = "mcp-server",
    reason: Annotated[
        str,
        Field(
            default="MCP Server execution",
            description="""The reason for executing this job.
            This provides context for why the job was started."""
        ),
    ] = "MCP Server execution",
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
    tool_name = "run-jobs"
    start_time = datetime.now()
    
    # Validate inputs (outside try-catch so exceptions can propagate for testing)
    await BaseToolMixin.validate_journey_id(ctx, journey_id)
    await BaseToolMixin.validate_stage_id(ctx, stage_id)
    
    # Check if TransformationJobExecutor is available (outside try-catch so exceptions can propagate for testing)
    try:
        from ..scripts.job_executor import TransformationJobExecutor
        if TransformationJobExecutor is None:
            raise ImportError("TransformationJobExecutor is None")
    except ImportError:
        error_msg = "TransformationJobExecutor not available - cannot execute job"
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise Exception(error_msg)
    
    try:
        # Log tool start
        BaseToolMixin.log_tool_start(
            tool_name,
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason
        )
        
        # Execute job
        try:
            # Force reload of job executor to get latest version
            import importlib
            if 'job_executor' in sys.modules:
                importlib.reload(sys.modules['job_executor'])
                from ..scripts.job_executor import TransformationJobExecutor
            
            executor = TransformationJobExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
            
            # Start job execution
            job_id = executor.start_job_execution(
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason,
            )
            
            # Execute the job
            executor.execute_job(journey_id, job_id)
            
            # Create success result
            result = BaseToolMixin.create_tool_result(
                status='success',
                message=f'Job {job_id} for stage {stage_id} completed successfully',
                start_time=start_time,
                job_id=job_id,
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason
            )
            
            # Log success
            duration = result['duration_seconds']
            BaseToolMixin.log_tool_success(tool_name, duration, job_id=job_id, stage_id=stage_id)
            
            return result
            
        except Exception as e:
            error_msg = f'Job execution failed for stage {stage_id}: {str(e)}'
            logger.error(error_msg)
            await ctx.error(error_msg)
            
            return BaseToolMixin.create_error_result(
                error_msg, start_time,
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason
            )
        
    except Exception as e:
        # Log error and return error result
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_error(tool_name, e, duration)
        await ctx.error(f'{tool_name} failed: {str(e)}')
        
        return BaseToolMixin.create_error_result(
            f'{tool_name} failed: {str(e)}', start_time,
            journey_id=journey_id,
            stage_id=stage_id
        ) 