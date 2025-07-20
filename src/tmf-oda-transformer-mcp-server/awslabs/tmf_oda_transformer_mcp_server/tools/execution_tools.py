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
from datetime import datetime, timezone
from typing import Dict, Any, Optional


def _get_clean_journey_id(journey_id: str) -> str:
    """Helper function to get clean journey ID for job executor.
    Strips JRN- prefix if present to match DynamoDB storage format."""
    return journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id

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
            
            # Get clean journey ID for job executor
            clean_journey_id = _get_clean_journey_id(journey_id)
            
            # Start job execution
            job_id = executor.start_job_execution(
                journey_id=clean_journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason,
            )
            
            # Execute the job
            executor.execute_job(clean_journey_id, job_id)
            
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
            
            # Get clean journey ID for job executor
            clean_journey_id = _get_clean_journey_id(journey_id)
            
            # Start job execution
            job_id = executor.start_job_execution(
                journey_id=clean_journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason,
            )
            
            # Execute the job
            executor.execute_job(clean_journey_id, job_id)
            
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
            Available stages: 'raw_analysis', 'stripped_schema', 'tmf_mapping', 
            'migration_planning', 'data_migration', 'verification_validation'"""
        ),
    ],
    action: Annotated[
        str,
        Field(
            default="run",
            description="""Action to perform on the job.
            - 'run': Create and execute a job (default)
            - 'create': Create job without executing
            - 'status': Get job status and progress
            - 'get': Get comprehensive job information and details
            - 'cancel': Cancel a running job
            - 'retry': Retry a failed job
            - 'list': List jobs for the stage"""
        ),
    ] = "run",
    job_id: Annotated[
        str,
        Field(
            default="",
            description="""Job ID for status, get, cancel, or retry operations.
            Required for status, get, cancel, and retry actions."""
        ),
    ] = "",
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
    job_config: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="""Optional job configuration parameters.
            Can include timeout, retry_attempts, priority, etc."""
        ),
    ] = None,
    wait_for_completion: Annotated[
        bool,
        Field(
            default=True,
            description="""Whether to wait for job completion before returning.
            If False, returns immediately after starting the job."""
        ),
    ] = True,
    progress_callback: Annotated[
        bool,
        Field(
            default=False,
            description="""Whether to include real-time progress updates.
            Provides step-by-step execution status."""
        ),
    ] = False,
) -> Dict[str, Any]:
    """Enhanced job management tool for TMF ODA transformation journeys.
    
    This tool provides comprehensive job management capabilities including:
    - Creating and executing transformation jobs for specific journey stages
    - Retrieving detailed job information and comprehensive status
    - Monitoring job status and progress in real-time
    - Managing job lifecycle (create, run, cancel, retry)
    - Integration with journey management system
    - Advanced error handling and recovery
    
    Args:
        ctx: MCP context for logging and state management
        journey_id: The journey ID for the transformation process
        stage_id: The stage ID to execute
        action: Action to perform (run, create, status, get, cancel, retry, list)
        job_id: Job ID for operations requiring existing job reference
        triggered_by: Who triggered this job execution
        reason: The reason for executing this job
        job_config: Optional job configuration parameters
        wait_for_completion: Whether to wait for job completion
        progress_callback: Whether to provide real-time progress updates
        
    Returns:
        Dict[str, Any]: Job execution result with status, progress, and details
    """
    tool_name = "run-jobs"
    start_time = datetime.now()
    
    # Validate inputs (outside try-catch so exceptions can propagate for testing)
    await BaseToolMixin.validate_journey_id(ctx, journey_id)
    if action in ['run', 'create', 'list']:
        await BaseToolMixin.validate_stage_id(ctx, stage_id)
    if action in ['status', 'cancel', 'retry', 'get'] and not job_id:
        raise ValueError(f"job_id is required for action '{action}'")
    
    # Check if TransformationJobExecutor is available
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
            action=action,
            job_id=job_id,
            triggered_by=triggered_by,
            reason=reason
        )
        
        # Initialize job executor and journey service
        executor = TransformationJobExecutor(role_arn=os.environ.get('AWS_ROLE_ARN'))
        
        # Route to appropriate action handler
        if action == "run":
            result = await _handle_job_run(
                ctx, executor, journey_id, stage_id, triggered_by, reason, 
                job_config, wait_for_completion, progress_callback, start_time
            )
        elif action == "create":
            result = await _handle_job_create(
                ctx, executor, journey_id, stage_id, triggered_by, reason, 
                job_config, start_time
            )
        elif action == "status":
            result = await _handle_job_status(
                ctx, executor, journey_id, job_id, progress_callback, start_time
            )
        elif action == "get":
            result = await _handle_job_get(
                ctx, executor, journey_id, job_id, start_time
            )
        elif action == "cancel":
            result = await _handle_job_cancel(
                ctx, executor, journey_id, job_id, reason, start_time
            )
        elif action == "retry":
            result = await _handle_job_retry(
                ctx, executor, journey_id, job_id, reason, start_time
            )
        elif action == "list":
            result = await _handle_job_list(
                ctx, executor, journey_id, stage_id, start_time
            )
        else:
            raise ValueError(f"Unknown action: {action}")
        
        # Log success
        duration = result['duration_seconds']
        BaseToolMixin.log_tool_success(
            tool_name, duration, 
            action=action, 
            job_id=result.get('job_id', job_id), 
            stage_id=stage_id
        )
        
        return result
            
    except Exception as e:
        # Log error and return error result
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_error(tool_name, e, duration)
        await ctx.error(f'{tool_name} failed: {str(e)}')
        
        return BaseToolMixin.create_error_result(
            f'{tool_name} action {action} failed: {str(e)}', start_time,
            journey_id=journey_id,
            stage_id=stage_id,
            action=action,
            job_id=job_id
        )


# =====================================================================
# JOB ACTION HANDLERS
# =====================================================================

async def _handle_job_run(
    ctx: Context,
    executor,
    journey_id: str,
    stage_id: str,
    triggered_by: str,
    reason: str,
    job_config: Optional[Dict[str, Any]],
    wait_for_completion: bool,
    progress_callback: bool,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle job creation and execution."""
    try:
        logger.info(f"🚀 Creating and executing job for journey {journey_id}, stage {stage_id}")
        
        # Get clean journey ID for job executor
        clean_journey_id = _get_clean_journey_id(journey_id)
        
        # Apply job configuration if provided
        if job_config:
            # TODO: Apply job configuration to executor
            logger.info(f"📋 Applying job configuration: {job_config}")
        
        # Start job execution
        job_id = executor.start_job_execution(
            journey_id=clean_journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason,
        )
        
        logger.info(f"✅ Job created with ID: {job_id}")
        
        # If not waiting for completion, return immediately
        if not wait_for_completion:
            return BaseToolMixin.create_tool_result(
                status='success',
                message=f'Job {job_id} started for stage {stage_id}',
                start_time=start_time,
                job_id=job_id,
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason,
                execution_status='started',
                wait_for_completion=False
            )
        
        # Execute the job and monitor progress
        try:
            if progress_callback:
                logger.info(f"🔄 Executing job {job_id} with progress monitoring...")
                # TODO: Implement progress monitoring during execution
                await _execute_job_with_progress(ctx, executor, clean_journey_id, job_id)
            else:
                logger.info(f"🔄 Executing job {job_id}...")
                executor.execute_job(clean_journey_id, job_id)
            
            # Get final job status
            job_details = await _get_job_details(executor, clean_journey_id, job_id)
            
            return BaseToolMixin.create_tool_result(
                status='success',
                message=f'Job {job_id} for stage {stage_id} completed successfully',
                start_time=start_time,
                job_id=job_id,
                journey_id=journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by,
                reason=reason,
                execution_status='completed',
                job_details=job_details,
                wait_for_completion=True
            )
            
        except Exception as e:
            logger.error(f"❌ Job execution failed: {str(e)}")
            
            # Get job details for error analysis
            job_details = await _get_job_details(executor, clean_journey_id, job_id)
            
            return BaseToolMixin.create_error_result(
                f'Job {job_id} execution failed: {str(e)}', start_time,
                journey_id=journey_id,
                stage_id=stage_id,
                job_id=job_id,
                execution_status='failed',
                error_details=str(e),
                job_details=job_details
            )
            
    except Exception as e:
        logger.error(f"❌ Job creation failed: {str(e)}")
        return BaseToolMixin.create_error_result(
            f'Job creation failed for stage {stage_id}: {str(e)}', start_time,
            journey_id=journey_id,
            stage_id=stage_id,
            execution_status='creation_failed',
            error_details=str(e)
        )


async def _handle_job_create(
    ctx: Context,
    executor,
    journey_id: str,
    stage_id: str,
    triggered_by: str,
    reason: str,
    job_config: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle job creation without execution."""
    try:
        logger.info(f"📋 Creating job for journey {journey_id}, stage {stage_id}")
        
        # Get clean journey ID for job executor
        clean_journey_id = _get_clean_journey_id(journey_id)
        
        # Apply job configuration if provided
        if job_config:
            logger.info(f"📋 Applying job configuration: {job_config}")
        
        # Start job execution (creates the job record)
        job_id = executor.start_job_execution(
            journey_id=clean_journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason,
        )
        
        # Get job details
        job_details = await _get_job_details(executor, clean_journey_id, job_id)
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Job {job_id} created for stage {stage_id}',
            start_time=start_time,
            job_id=job_id,
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason,
            execution_status='created',
            job_details=job_details
        )
        
    except Exception as e:
        logger.error(f"❌ Job creation failed: {str(e)}")
        return BaseToolMixin.create_error_result(
            f'Job creation failed for stage {stage_id}: {str(e)}', start_time,
            journey_id=journey_id,
            stage_id=stage_id,
            error_details=str(e)
        )


async def _handle_job_status(
    ctx: Context,
    executor,
    journey_id: str,
    job_id: str,
    progress_callback: bool,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle job status retrieval."""
    try:
        logger.info(f"📊 Getting status for job {job_id}")
        
        # Get clean journey ID for job executor
        clean_journey_id = _get_clean_journey_id(journey_id)
        
        # Get job details
        job_details = await _get_job_details(executor, clean_journey_id, job_id)
        
        if not job_details:
            return BaseToolMixin.create_error_result(
                f'Job {job_id} not found', start_time,
                journey_id=journey_id,
                job_id=job_id
            )
        
        # Include detailed progress if requested
        if progress_callback and job_details.get('status') == 'in_progress':
            step_progress = await _get_job_step_progress(executor, clean_journey_id, job_id)
            job_details['step_progress'] = step_progress
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved status for job {job_id}',
            start_time=start_time,
            job_id=job_id,
            journey_id=journey_id,
            job_status=job_details.get('status', 'unknown'),
            job_progress=job_details.get('progress', 0),
            job_details=job_details
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get job status: {str(e)}")
        return BaseToolMixin.create_error_result(
            f'Failed to get status for job {job_id}: {str(e)}', start_time,
            journey_id=journey_id,
            job_id=job_id,
            error_details=str(e)
        )


async def _handle_job_cancel(
    ctx: Context,
    executor,
    journey_id: str,
    job_id: str,
    reason: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle job cancellation."""
    try:
        logger.info(f"🛑 Cancelling job {job_id}")
        
        # Get clean journey ID for job executor
        clean_journey_id = _get_clean_journey_id(journey_id)
        
        # Get current job status
        job_details = await _get_job_details(executor, clean_journey_id, job_id)
        
        if not job_details:
            return BaseToolMixin.create_error_result(
                f'Job {job_id} not found', start_time,
                journey_id=journey_id,
                job_id=job_id
            )
        
        current_status = job_details.get('status', 'unknown')
        
        if current_status not in ['in_progress', 'pending']:
            return BaseToolMixin.create_error_result(
                f'Job {job_id} cannot be cancelled (status: {current_status})', start_time,
                journey_id=journey_id,
                job_id=job_id,
                current_status=current_status
            )
        
        # TODO: Implement actual job cancellation logic
        # This would involve stopping the running process and updating job status
        logger.warning("Job cancellation not yet implemented - job will continue running")
        
        return BaseToolMixin.create_tool_result(
            status='warning',
            message=f'Job cancellation requested for {job_id} but not yet implemented',
            start_time=start_time,
            job_id=job_id,
            journey_id=journey_id,
            current_status=current_status,
            cancellation_reason=reason
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to cancel job: {str(e)}")
        return BaseToolMixin.create_error_result(
            f'Failed to cancel job {job_id}: {str(e)}', start_time,
            journey_id=journey_id,
            job_id=job_id,
            error_details=str(e)
        )


async def _handle_job_retry(
    ctx: Context,
    executor,
    journey_id: str,
    job_id: str,
    reason: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle job retry."""
    try:
        logger.info(f"🔄 Retrying job {job_id}")
        
        # Get clean journey ID for job executor
        clean_journey_id = _get_clean_journey_id(journey_id)
        
        # Get current job status
        job_details = await _get_job_details(executor, clean_journey_id, job_id)
        
        if not job_details:
            return BaseToolMixin.create_error_result(
                f'Job {job_id} not found', start_time,
                journey_id=journey_id,
                job_id=job_id
            )
        
        current_status = job_details.get('status', 'unknown')
        
        if current_status != 'failed':
            return BaseToolMixin.create_error_result(
                f'Job {job_id} cannot be retried (status: {current_status})', start_time,
                journey_id=journey_id,
                job_id=job_id,
                current_status=current_status
            )
        
        # Extract job details for retry
        stage_id = job_details.get('stageId', '')
        triggered_by = job_details.get('triggeredBy', 'retry')
        
        # Create new job execution
        new_job_id = executor.start_job_execution(
            journey_id=clean_journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=f"Retry of {job_id}: {reason}",
        )
        
        logger.info(f"✅ Retry job created with ID: {new_job_id}")
        
        # Execute the retry job
        executor.execute_job(clean_journey_id, new_job_id)
        
        # Get final job status
        new_job_details = await _get_job_details(executor, clean_journey_id, new_job_id)
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Job {job_id} retried successfully as {new_job_id}',
            start_time=start_time,
            original_job_id=job_id,
            new_job_id=new_job_id,
            journey_id=journey_id,
            stage_id=stage_id,
            retry_reason=reason,
            job_details=new_job_details
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to retry job: {str(e)}")
        return BaseToolMixin.create_error_result(
            f'Failed to retry job {job_id}: {str(e)}', start_time,
            journey_id=journey_id,
            job_id=job_id,
            error_details=str(e)
        )


async def _handle_job_list(
    ctx: Context,
    executor,
    journey_id: str,
    stage_id: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle job listing for a stage."""
    try:
        logger.info(f"📋 Listing jobs for journey {journey_id}, stage {stage_id}")
        
        # TODO: Implement job listing from DynamoDB
        # This would query jobs for the specific journey and stage
        jobs = []  # Placeholder
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved {len(jobs)} jobs for stage {stage_id}',
            start_time=start_time,
            journey_id=journey_id,
            stage_id=stage_id,
            jobs=jobs,
            total_jobs=len(jobs)
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list jobs: {str(e)}")
        return BaseToolMixin.create_error_result(
            f'Failed to list jobs for stage {stage_id}: {str(e)}', start_time,
            journey_id=journey_id,
            stage_id=stage_id,
            error_details=str(e)
        )


async def _handle_job_get(
    ctx: Context,
    executor,
    journey_id: str,
    job_id: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle getting detailed job information."""
    try:
        logger.info(f"📊 Getting detailed information for job {job_id}")
        
        # Get clean journey ID for job executor
        clean_journey_id = _get_clean_journey_id(journey_id)
        
        # Get comprehensive job details
        job_details = await _get_job_details(executor, clean_journey_id, job_id)
        
        if not job_details:
            return BaseToolMixin.create_error_result(
                f'Job {job_id} not found', start_time,
                journey_id=journey_id,
                job_id=job_id
            )
        
        # Get additional job information like step progress and timeline
        job_timeline = await _get_job_timeline(executor, clean_journey_id, job_id)
        step_progress = await _get_job_step_progress(executor, clean_journey_id, job_id)
        
        # Build comprehensive job information
        comprehensive_info = {
            **job_details,
            'timeline': job_timeline,
            'step_progress': step_progress,
            'retrieved_at': datetime.now(timezone.utc).isoformat()
        }
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved comprehensive information for job {job_id}',
            start_time=start_time,
            job_id=job_id,
            journey_id=journey_id,
            operation='get_job_details',
            job_info=comprehensive_info
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get job details: {str(e)}")
        return BaseToolMixin.create_error_result(
            f'Failed to get details for job {job_id}: {str(e)}', start_time,
            journey_id=journey_id,
            job_id=job_id,
            error_details=str(e)
        )


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

async def _execute_job_with_progress(ctx: Context, executor, journey_id: str, job_id: str):
    """Execute job with progress monitoring."""
    # TODO: Implement progress monitoring during job execution
    # This could involve periodic status checks and progress updates
    logger.info("Progress monitoring not yet implemented, executing job normally")
    # Note: journey_id is already clean when passed from _handle_job_run
    executor.execute_job(journey_id, job_id)


async def _get_job_details(executor, journey_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed job information."""
    try:
        # Note: journey_id is already clean when passed from calling functions
        # Use the executor's method to get job execution details
        job_data = executor.get_job_execution(journey_id, job_id)
        return job_data
    except Exception as e:
        logger.error(f"Failed to get job details for {job_id}: {str(e)}")
        return None


async def _get_job_timeline(executor, journey_id: str, job_id: str) -> Dict[str, Any]:
    """Get timeline information for a job."""
    try:
        job_data = executor.get_job_execution(journey_id, job_id)
        if job_data:
            timeline = {
                'created_at': job_data.get('createdAt'),
                'started_at': job_data.get('startTime'),
                'updated_at': job_data.get('updatedAt'),
                'ended_at': job_data.get('endTime'),
                'duration_seconds': None
            }
            
            # Calculate duration if both start and end times are available
            if timeline['started_at'] and timeline['ended_at']:
                try:
                    from datetime import datetime as dt
                    start = dt.fromisoformat(timeline['started_at'].replace('Z', '+00:00'))
                    end = dt.fromisoformat(timeline['ended_at'].replace('Z', '+00:00'))
                    timeline['duration_seconds'] = (end - start).total_seconds()
                except Exception:
                    pass
            
            return timeline
        return {}
    except Exception as e:
        logger.error(f"Failed to get timeline for {job_id}: {str(e)}")
        return {}


async def _get_job_step_progress(executor, journey_id: str, job_id: str) -> Dict[str, Any]:
    """Get detailed step progress for a job."""
    try:
        job_data = executor.get_job_execution(journey_id, job_id)
        if job_data and 'stepResults' in job_data:
            return job_data['stepResults']
        return {}
    except Exception as e:
        logger.error(f"Failed to get step progress for {job_id}: {str(e)}")
        return {} 