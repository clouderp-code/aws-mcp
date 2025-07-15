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

"""Enhanced Management tools for TMF ODA Transformer MCP Server.

This module provides comprehensive journey lifecycle management including:
- Journey CRUD operations
- Stage management (add, update, delete, list)
- Second Brain rules management
- Job lifecycle management
- Logs and reports management
- Import/export functionality
- Interactive features and dashboards
"""

import json
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union

from loguru import logger
from mcp.server.fastmcp import Context
from pydantic import Field
from typing import Annotated

from ..models import JourneyCreateData, JourneyUpdateData
from ..services import JourneyService
from .base import BaseToolMixin


# Enhanced action enumerations
class JourneyAction:
    """Journey action enumeration."""
    # Basic CRUD
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    
    # Stage Management
    LIST_STAGES = "list_stages"
    ADD_STAGE = "add_stage"
    UPDATE_STAGE = "update_stage"
    DELETE_STAGE = "delete_stage"
    ADD_DEFAULT_STAGES = "add_default_stages"
    
    # Rules Management
    LIST_RULES = "list_rules"
    ADD_RULE = "add_rule"
    UPDATE_RULE = "update_rule"
    DELETE_RULE = "delete_rule"
    
    # Job Management
    LIST_JOBS = "list_jobs"
    GET_JOB = "get_job"
    RUN_JOB = "run_job"
    CANCEL_JOB = "cancel_job"
    UPDATE_JOB_STATUS = "update_job_status"
    RETRY_JOB = "retry_job"
    GET_JOB_METRICS = "get_job_metrics"
    GET_JOB_TIMELINE = "get_job_timeline"
    BATCH_CANCEL_JOBS = "batch_cancel_jobs"
    
    # Logs and Reports
    GET_JOB_LOGS = "get_job_logs"
    GET_JOB_REPORTS = "get_job_reports"
    ADD_LOG_ENTRY = "add_log_entry"
    SEARCH_LOGS = "search_logs"
    GET_LOGS_BY_LEVEL = "get_logs_by_level"
    EXPORT_JOB_LOGS = "export_job_logs"
    GET_ERROR_SUMMARY = "get_error_summary"
    LIST_AVAILABLE_LOGS = "list_available_logs"
    GENERATE_SUMMARY_REPORT = "generate_summary_report"
    CREATE_JOB_REPORT = "create_job_report"
    GENERATE_PERFORMANCE_REPORT = "generate_performance_report"
    
    # Import/Export
    EXPORT_COMPLETE = "export_complete"
    IMPORT_COMPLETE = "import_complete"
    
    # Interactive Features
    DASHBOARD = "dashboard"
    GET_JOURNEY_SUMMARY = "get_journey_summary"


async def journeys_tool(
    ctx: Context,
    action: Annotated[
        str,
        Field(
            default="read",
            description="""Action to perform. Available actions:
            
            **Journey CRUD:**
            - 'list'/'read': List all journeys or get specific journey details
            - 'create': Create a new journey
            - 'update': Update existing journey
            - 'delete': Delete journey and associated data
            
            **Stage Management:**
            - 'list_stages': List stages for a journey
            - 'add_stage': Add a new stage to journey
            - 'update_stage': Update existing stage
            - 'delete_stage': Delete stage from journey
            - 'add_default_stages': Add default transformation stages
            
            **Rules Management:**
            - 'list_rules': List Second Brain rules
            - 'add_rule': Add new rule to stage
            - 'update_rule': Update existing rule
            - 'delete_rule': Delete rule from stage
            
            **Job Management:**
            - 'list_jobs': List job executions
            - 'get_job': Get job details
            - 'run_job': Execute job for stage
            - 'cancel_job': Cancel running job
            - 'update_job_status': Update job status/progress
            - 'retry_job': Retry failed job
            - 'get_job_metrics': Get job performance metrics
            - 'get_job_timeline': Get job execution timeline
            - 'batch_cancel_jobs': Cancel multiple jobs
            
            **Logs and Reports:**
            - 'get_job_logs': Get job execution logs
            - 'get_job_reports': Get job reports
            - 'add_log_entry': Add log entry to job
            - 'search_logs': Search through logs
            - 'get_logs_by_level': Get logs by level (error, warning, etc.)
            - 'export_job_logs': Export logs to file
            - 'get_error_summary': Get error analysis summary
            - 'list_available_logs': List available log sources
            - 'generate_summary_report': Generate job summary report
            - 'create_job_report': Create custom job report
            - 'generate_performance_report': Generate performance analysis
            
            **Import/Export:**
            - 'export_complete': Export complete journey data
            - 'import_complete': Import journey from backup
            
            **Interactive:**
            - 'dashboard': Get journey dashboard view
            - 'get_journey_summary': Get comprehensive journey summary"""
        ),
    ] = "read",
    
    # Core identifiers
    journey_id: Annotated[
        str,
        Field(
            default="",
            description="Journey ID for operations requiring it (most actions)"
        ),
    ] = "",
    
    job_id: Annotated[
        str,
        Field(
            default="",
            description="Job ID for job-related operations"
        ),
    ] = "",
    
    stage_id: Annotated[
        str,
        Field(
            default="",
            description="Stage ID for stage/job operations"
        ),
    ] = "",
    
    rule_id: Annotated[
        str,
        Field(
            default="",
            description="Rule ID for rule operations"
        ),
    ] = "",
    
    # Data payloads
    journey_data: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="Journey data for create/update operations"
        ),
    ] = None,
    
    stage_data: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="Stage data for stage operations"
        ),
    ] = None,
    
    rule_data: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="Rule data for rule operations"
        ),
    ] = None,
    
    job_data: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="Job data for job operations"
        ),
    ] = None,
    
    # Job execution parameters
    triggered_by: Annotated[
        str,
        Field(
            default="mcp-user",
            description="Who triggered the job execution"
        ),
    ] = "mcp-user",
    
    reason: Annotated[
        str,
        Field(
            default="MCP Server execution",
            description="Reason for job execution"
        ),
    ] = "MCP Server execution",
    
    job_status: Annotated[
        str,
        Field(
            default="",
            description="Job status for updates (pending, running, completed, failed, cancelled)"
        ),
    ] = "",
    
    progress: Annotated[
        Optional[int],
        Field(
            default=None,
            description="Job progress percentage (0-100)"
        ),
    ] = None,
    
    current_step: Annotated[
        str,
        Field(
            default="",
            description="Current step for job updates"
        ),
    ] = "",
    
    error_message: Annotated[
        str,
        Field(
            default="",
            description="Error message for failed jobs"
        ),
    ] = "",
    
    # Log parameters
    step_name: Annotated[
        str,
        Field(
            default="",
            description="Step name for log operations"
        ),
    ] = "",
    
    log_level: Annotated[
        str,
        Field(
            default="",
            description="Log level (error, warning, info, debug)"
        ),
    ] = "",
    
    log_message: Annotated[
        str,
        Field(
            default="",
            description="Log message content"
        ),
    ] = "",
    
    search_query: Annotated[
        str,
        Field(
            default="",
            description="Search query for log search operations"
        ),
    ] = "",
    
    # Filtering and options
    status_filter: Annotated[
        str,
        Field(
            default="",
            description="Filter by status (for list operations)"
        ),
    ] = "",
    
    rule_type: Annotated[
        str,
        Field(
            default="",
            description="Filter by rule type"
        ),
    ] = "",
    
    level_filter: Annotated[
        str,
        Field(
            default="",
            description="Filter by log level"
        ),
    ] = "",
    
    step_filter: Annotated[
        str,
        Field(
            default="",
            description="Filter by step name"
        ),
    ] = "",
    
    # List parameters
    limit: Annotated[
        int,
        Field(
            default=50,
            description="Maximum number of results to return"
        ),
    ] = 50,
    
    include_stages: Annotated[
        bool,
        Field(
            default=True,
            description="Include detailed stage information"
        ),
    ] = True,
    
    include_job_history: Annotated[
        bool,
        Field(
            default=True,
            description="Include job execution history"
        ),
    ] = True,
    
    include_all: Annotated[
        bool,
        Field(
            default=False,
            description="Include all available details (comprehensive view)"
        ),
    ] = False,
    
    # File operations
    output_file: Annotated[
        str,
        Field(
            default="",
            description="Output file path for export operations"
        ),
    ] = "",
    
    input_file: Annotated[
        str,
        Field(
            default="",
            description="Input file path for import operations"
        ),
    ] = "",
    
    export_format: Annotated[
        str,
        Field(
            default="json",
            description="Export format (json, csv, txt)"
        ),
    ] = "json",
    
    # Batch operations
    job_ids: Annotated[
        str,
        Field(
            default="",
            description="Comma-separated list of job IDs for batch operations"
        ),
    ] = "",
    
    # Report parameters
    report_type: Annotated[
        str,
        Field(
            default="",
            description="Type of report to create"
        ),
    ] = "",
    
    report_title: Annotated[
        str,
        Field(
            default="",
            description="Title for generated reports"
        ),
    ] = "",
    
) -> Dict[str, Any]:
    """Comprehensive TMF ODA transformation journey lifecycle management.
    
    This tool provides complete journey management capabilities including:
    - Journey CRUD operations
    - Stage management
    - Second Brain rules management  
    - Job lifecycle management
    - Logs and reports management
    - Import/export functionality
    - Interactive dashboards
    
    Args:
        ctx: MCP context for logging and state management
        action: Action to perform (see action description for all options)
        journey_id: Journey ID for operations requiring it
        job_id: Job ID for job-related operations
        stage_id: Stage ID for stage/job operations
        rule_id: Rule ID for rule operations
        journey_data: Journey data for create/update operations
        stage_data: Stage data for stage operations
        rule_data: Rule data for rule operations
        job_data: Job data for job operations
        triggered_by: Who triggered job execution
        reason: Reason for job execution
        job_status: Job status for updates
        progress: Job progress percentage
        current_step: Current step for job updates
        error_message: Error message for failed jobs
        step_name: Step name for log operations
        log_level: Log level
        log_message: Log message content
        search_query: Search query for logs
        status_filter: Filter by status
        rule_type: Filter by rule type
        level_filter: Filter by log level
        step_filter: Filter by step name
        limit: Maximum results to return
        include_stages: Include stage information
        include_job_history: Include job history
        include_all: Include all available details
        output_file: Output file for exports
        input_file: Input file for imports
        export_format: Export format
        job_ids: Comma-separated job IDs for batch operations
        report_type: Type of report to create
        report_title: Title for reports
        
    Returns:
        Dict[str, Any]: Operation result with status and details
    """
    tool_name = "journeys"
    start_time = datetime.now()
    
    # Clean up empty string parameters
    journey_id = journey_id.strip() if journey_id else None
    job_id = job_id.strip() if job_id else None
    stage_id = stage_id.strip() if stage_id else None
    rule_id = rule_id.strip() if rule_id else None
    step_name = step_name.strip() if step_name else None
    log_level = log_level.strip() if log_level else None
    log_message = log_message.strip() if log_message else None
    search_query = search_query.strip() if search_query else None
    status_filter = status_filter.strip() if status_filter else None
    rule_type = rule_type.strip() if rule_type else None
    level_filter = level_filter.strip() if level_filter else None
    step_filter = step_filter.strip() if step_filter else None
    output_file = output_file.strip() if output_file else None
    input_file = input_file.strip() if input_file else None
    export_format = export_format.strip() if export_format else "json"
    job_ids = job_ids.strip() if job_ids else None
    report_type = report_type.strip() if report_type else None
    report_title = report_title.strip() if report_title else None
    job_status = job_status.strip() if job_status else None
    current_step = current_step.strip() if current_step else None
    error_message = error_message.strip() if error_message else None
    
    # Add parameter validation for actions that require specific parameters
    actions_requiring_journey_id = [
        # Operations that need specific journey context
        JourneyAction.UPDATE, JourneyAction.DELETE,
        JourneyAction.LIST_STAGES, JourneyAction.ADD_STAGE, JourneyAction.UPDATE_STAGE,
        JourneyAction.DELETE_STAGE, JourneyAction.ADD_DEFAULT_STAGES,
        JourneyAction.LIST_RULES, JourneyAction.ADD_RULE, JourneyAction.UPDATE_RULE,
        JourneyAction.DELETE_RULE, JourneyAction.LIST_JOBS, JourneyAction.GET_JOB,
        JourneyAction.RUN_JOB, JourneyAction.CANCEL_JOB, JourneyAction.UPDATE_JOB_STATUS,
        JourneyAction.RETRY_JOB, JourneyAction.GET_JOB_METRICS, JourneyAction.GET_JOB_TIMELINE,
        JourneyAction.BATCH_CANCEL_JOBS, JourneyAction.GET_JOB_LOGS, JourneyAction.GET_JOB_REPORTS,
        JourneyAction.ADD_LOG_ENTRY, JourneyAction.SEARCH_LOGS, JourneyAction.GET_LOGS_BY_LEVEL,
        JourneyAction.EXPORT_JOB_LOGS, JourneyAction.GET_ERROR_SUMMARY,
        JourneyAction.LIST_AVAILABLE_LOGS, JourneyAction.GENERATE_SUMMARY_REPORT,
        JourneyAction.CREATE_JOB_REPORT, JourneyAction.GENERATE_PERFORMANCE_REPORT,
        JourneyAction.EXPORT_COMPLETE, JourneyAction.DASHBOARD, JourneyAction.GET_JOURNEY_SUMMARY
    ]
    
    actions_requiring_job_id = [
        JourneyAction.GET_JOB, JourneyAction.CANCEL_JOB, JourneyAction.UPDATE_JOB_STATUS,
        JourneyAction.RETRY_JOB, JourneyAction.GET_JOB_METRICS, JourneyAction.GET_JOB_TIMELINE,
        JourneyAction.GET_JOB_LOGS, JourneyAction.GET_JOB_REPORTS,
        JourneyAction.GENERATE_SUMMARY_REPORT, JourneyAction.CREATE_JOB_REPORT,
        JourneyAction.GENERATE_PERFORMANCE_REPORT
    ]
    
    actions_requiring_stage_id = [
        JourneyAction.UPDATE_STAGE, JourneyAction.DELETE_STAGE, JourneyAction.RUN_JOB,
        JourneyAction.ADD_RULE, JourneyAction.UPDATE_RULE, JourneyAction.DELETE_RULE
    ]
    
    actions_requiring_data = [
        (JourneyAction.CREATE, 'journey_data'), (JourneyAction.UPDATE, 'journey_data'),
        (JourneyAction.ADD_STAGE, 'stage_data'), (JourneyAction.UPDATE_STAGE, 'stage_data'),
        (JourneyAction.ADD_RULE, 'rule_data'), (JourneyAction.UPDATE_RULE, 'rule_data'),
        (JourneyAction.ADD_LOG_ENTRY, 'log_message')
    ]
    
    # Validate required parameters
    if action in actions_requiring_journey_id and not journey_id:
        error_msg = f"journey_id is required for action '{action}'"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if action in actions_requiring_job_id and not job_id:
        error_msg = f"job_id is required for action '{action}'"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if action in actions_requiring_stage_id and not stage_id:
        error_msg = f"stage_id is required for action '{action}'"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check data requirements
    for required_action, required_field in actions_requiring_data:
        if action == required_action:
            if required_field == 'journey_data' and not journey_data:
                error_msg = f"journey_data is required for action '{action}'"
                logger.error(error_msg)
                raise ValueError(error_msg)
            elif required_field == 'stage_data' and not stage_data:
                error_msg = f"stage_data is required for action '{action}'"
                logger.error(error_msg)
                raise ValueError(error_msg)
            elif required_field == 'rule_data' and not rule_data:
                error_msg = f"rule_data is required for action '{action}'"
                logger.error(error_msg)
                raise ValueError(error_msg)
            elif required_field == 'log_message' and not log_message:
                error_msg = f"log_message is required for action '{action}'"
                logger.error(error_msg)
                raise ValueError(error_msg)

    try:
        # Log tool start
        BaseToolMixin.log_tool_start(
            tool_name,
            action=action,
            journey_id=journey_id,
            job_id=job_id,
            stage_id=stage_id
        )
        
        # Validate action
        valid_actions = [
            # Basic CRUD
            JourneyAction.CREATE, JourneyAction.READ, JourneyAction.UPDATE, 
            JourneyAction.DELETE, JourneyAction.LIST,
            # Stage Management
            JourneyAction.LIST_STAGES, JourneyAction.ADD_STAGE, JourneyAction.UPDATE_STAGE,
            JourneyAction.DELETE_STAGE, JourneyAction.ADD_DEFAULT_STAGES,
            # Rules Management
            JourneyAction.LIST_RULES, JourneyAction.ADD_RULE, JourneyAction.UPDATE_RULE,
            JourneyAction.DELETE_RULE,
            # Job Management
            JourneyAction.LIST_JOBS, JourneyAction.GET_JOB, JourneyAction.RUN_JOB,
            JourneyAction.CANCEL_JOB, JourneyAction.UPDATE_JOB_STATUS, JourneyAction.RETRY_JOB,
            JourneyAction.GET_JOB_METRICS, JourneyAction.GET_JOB_TIMELINE, JourneyAction.BATCH_CANCEL_JOBS,
            # Logs and Reports
            JourneyAction.GET_JOB_LOGS, JourneyAction.GET_JOB_REPORTS, JourneyAction.ADD_LOG_ENTRY,
            JourneyAction.SEARCH_LOGS, JourneyAction.GET_LOGS_BY_LEVEL, JourneyAction.EXPORT_JOB_LOGS,
            JourneyAction.GET_ERROR_SUMMARY, JourneyAction.LIST_AVAILABLE_LOGS,
            JourneyAction.GENERATE_SUMMARY_REPORT, JourneyAction.CREATE_JOB_REPORT,
            JourneyAction.GENERATE_PERFORMANCE_REPORT,
            # Import/Export
            JourneyAction.EXPORT_COMPLETE, JourneyAction.IMPORT_COMPLETE,
            # Interactive
            JourneyAction.DASHBOARD, JourneyAction.GET_JOURNEY_SUMMARY
        ]
        
        if action.lower() not in [a.lower() for a in valid_actions]:
            error_msg = f"Invalid action: {action}. Valid actions: {valid_actions}"
            logger.error(error_msg)
            return BaseToolMixin.create_error_result(error_msg, start_time, action=action)
        
        # Normalize action
        action_map = {a.lower(): a for a in valid_actions}
        action = action_map[action.lower()]
        
        # Create journey service (using enhanced version)
        journey_service = EnhancedJourneyService()
        
        # Route to appropriate operation based on action
        if action in [JourneyAction.LIST, JourneyAction.READ]:
            result = await _handle_journey_read(
                ctx, journey_service, journey_id, stage_id,
                include_stages, include_job_history, limit, start_time
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
        
        # Stage Management Operations
        elif action == JourneyAction.LIST_STAGES:
            result = await _handle_list_stages(
                ctx, journey_service, journey_id, start_time
            )
        elif action == JourneyAction.ADD_STAGE:
            result = await _handle_add_stage(
                ctx, journey_service, journey_id, stage_data, start_time
            )
        elif action == JourneyAction.UPDATE_STAGE:
            result = await _handle_update_stage(
                ctx, journey_service, journey_id, stage_id, stage_data, start_time
            )
        elif action == JourneyAction.DELETE_STAGE:
            result = await _handle_delete_stage(
                ctx, journey_service, journey_id, stage_id, start_time
            )
        elif action == JourneyAction.ADD_DEFAULT_STAGES:
            result = await _handle_add_default_stages(
                ctx, journey_service, journey_id, start_time
            )
        
        # Rules Management Operations
        elif action == JourneyAction.LIST_RULES:
            result = await _handle_list_rules(
                ctx, journey_service, journey_id, stage_id, rule_type, start_time
            )
        elif action == JourneyAction.ADD_RULE:
            result = await _handle_add_rule(
                ctx, journey_service, journey_id, stage_id, rule_data, start_time
            )
        elif action == JourneyAction.UPDATE_RULE:
            result = await _handle_update_rule(
                ctx, journey_service, journey_id, stage_id, rule_id, rule_data, start_time
            )
        elif action == JourneyAction.DELETE_RULE:
            result = await _handle_delete_rule(
                ctx, journey_service, journey_id, stage_id, rule_id, start_time
            )
        
        # Job Management Operations
        elif action == JourneyAction.LIST_JOBS:
            result = await _handle_list_jobs(
                ctx, journey_service, journey_id, stage_id, status_filter, limit, start_time
            )
        elif action == JourneyAction.GET_JOB:
            result = await _handle_get_job(
                ctx, journey_service, journey_id, job_id, include_all, start_time
            )
        elif action == JourneyAction.RUN_JOB:
            result = await _handle_run_job(
                ctx, journey_service, journey_id, stage_id, triggered_by, reason, start_time
            )
        elif action == JourneyAction.CANCEL_JOB:
            result = await _handle_cancel_job(
                ctx, journey_service, journey_id, job_id, reason, start_time
            )
        elif action == JourneyAction.UPDATE_JOB_STATUS:
            result = await _handle_update_job_status(
                ctx, journey_service, journey_id, job_id, job_status, progress, 
                current_step, error_message, start_time
            )
        elif action == JourneyAction.RETRY_JOB:
            result = await _handle_retry_job(
                ctx, journey_service, journey_id, job_id, triggered_by, reason, start_time
            )
        elif action == JourneyAction.GET_JOB_METRICS:
            result = await _handle_get_job_metrics(
                ctx, journey_service, journey_id, job_id, start_time
            )
        elif action == JourneyAction.GET_JOB_TIMELINE:
            result = await _handle_get_job_timeline(
                ctx, journey_service, journey_id, job_id, start_time
            )
        elif action == JourneyAction.BATCH_CANCEL_JOBS:
            result = await _handle_batch_cancel_jobs(
                ctx, journey_service, journey_id, job_ids, reason, start_time
            )
        
        # Interactive Operations
        elif action == JourneyAction.DASHBOARD:
            result = await _handle_dashboard(
                ctx, journey_service, journey_id, start_time
            )
        elif action == JourneyAction.GET_JOURNEY_SUMMARY:
            result = await _handle_get_journey_summary(
                ctx, journey_service, journey_id, start_time
            )
        
        # Add placeholders for other operations (to be implemented)
        else:
            # For now, return a "not implemented" response for actions not yet implemented
            result = {
                'status': 'not_implemented',
                'message': f'Action {action} is planned but not yet implemented in the MCP server',
                'operation': action,
                'journey_id': journey_id,
                'available_actions': [
                    JourneyAction.CREATE, JourneyAction.READ, JourneyAction.UPDATE, JourneyAction.DELETE, JourneyAction.LIST,
                    JourneyAction.LIST_STAGES, JourneyAction.ADD_STAGE, JourneyAction.UPDATE_STAGE, JourneyAction.DELETE_STAGE, JourneyAction.ADD_DEFAULT_STAGES,
                    JourneyAction.LIST_RULES, JourneyAction.ADD_RULE, JourneyAction.UPDATE_RULE, JourneyAction.DELETE_RULE,
                    JourneyAction.LIST_JOBS, JourneyAction.GET_JOB, JourneyAction.RUN_JOB, JourneyAction.CANCEL_JOB, JourneyAction.UPDATE_JOB_STATUS, JourneyAction.RETRY_JOB,
                    JourneyAction.GET_JOB_METRICS, JourneyAction.GET_JOB_TIMELINE, JourneyAction.BATCH_CANCEL_JOBS,
                    JourneyAction.DASHBOARD, JourneyAction.GET_JOURNEY_SUMMARY
                ],
                'note': 'This is an extended action from the comprehensive manage_journey.py script that will be implemented in future versions',
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Log success
        duration = result.get('duration_seconds', 0)
        BaseToolMixin.log_tool_success(tool_name, duration, action=action, journey_id=journey_id)
        
        return result
        
    except Exception as e:
        # Log error and return error result
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_error(tool_name, e, duration)
        error_msg = f'Journey {action} operation failed: {str(e)}'
        
        # Create operation name consistent with success cases
        operation_map = {
            'create': 'create_journey',
            'read': 'read_journey', 
            'update': 'update_journey',
            'delete': 'delete_journey',
            'list': 'list_journeys',
            'list_stages': 'list_stages',
            'add_stage': 'add_stage',
            'update_stage': 'update_stage',
            'delete_stage': 'delete_stage',
            'add_default_stages': 'add_default_stages',
            'list_rules': 'list_rules',
            'add_rule': 'add_rule',
            'update_rule': 'update_rule',
            'delete_rule': 'delete_rule',
            'list_jobs': 'list_jobs',
            'get_job': 'get_job',
            'run_job': 'run_job',
            'cancel_job': 'cancel_job',
            'update_job_status': 'update_job_status',
            'retry_job': 'retry_job',
            'get_job_metrics': 'get_job_metrics',
            'get_job_timeline': 'get_job_timeline',
            'batch_cancel_jobs': 'batch_cancel_jobs',
            'dashboard': 'dashboard',
            'get_journey_summary': 'get_journey_summary'
        }
        operation = operation_map.get(action, action)
        
        # For get_job action, avoid using BaseToolMixin to prevent datetime issues
        if action == 'get_job':
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'status': 'error',
                'message': error_msg,
                'error_message': error_msg,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration,
                'operation': operation,
                'action': action,
                'journey_id': journey_id
            }
        else:
            return BaseToolMixin.create_error_result(
                error_msg, start_time,
                operation=operation,
                action=action,
                journey_id=journey_id
            )


# Enhanced Journey Service (extends the existing one)
class EnhancedJourneyService(JourneyService):
    """Enhanced journey service with comprehensive lifecycle management."""
    
    def __init__(self):
        super().__init__()
        # Initialize with FallbackJourneyManager for real stage management
        from ..managers.fallback_manager import FallbackJourneyManager
        self.journey_manager = FallbackJourneyManager()
        logger.info("Enhanced journey service initialized with comprehensive lifecycle management")
    
    async def list_stages(self, journey_id: str) -> List[Dict[str, Any]]:
        """List all stages for a journey."""
        try:
            # Ensure journey exists in local storage first
            await self._ensure_journey_synchronized(journey_id)
            
            # Use real journey manager instead of mock data
            stages = self.journey_manager.get_journey_stages(journey_id)
            return stages
        except Exception as e:
            logger.error(f'Failed to list stages: {str(e)}')
            raise

    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            if stage_id:
                # Get jobs for specific stage using parent class manager
                jobs = self.manager.get_stage_jobs(journey_id, stage_id, limit)
            else:
                # Get all jobs for journey
                jobs = self.manager.get_stage_jobs(journey_id, '', limit)
            
            # Apply status filter if specified
            if status_filter:
                jobs = [job for job in jobs if job.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise
    
    async def _ensure_journey_synchronized(self, journey_id: str):
        """Ensure journey exists in local storage, sync from DynamoDB if needed."""
        try:
            # Check if journey exists in local storage
            fallback_journey = self.journey_manager.get_journey_status(journey_id)
            if fallback_journey:
                return  # Already synchronized
            
            # Get journey from DynamoDB using the parent class manager
            journey = self.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f'Journey {journey_id} not found in DynamoDB')
            
            # Create synchronized entry in local storage
            logger.info(f'Synchronizing journey {journey_id} from DynamoDB to local storage')
            journeys = self.journey_manager._load_journeys()
            
            journeys[journey_id] = {
                'journey_id': journey_id,
                'name': journey.get('name', 'Unknown'),
                'description': journey.get('description', ''),
                'status': journey.get('status', 'pending'),
                'created_at': journey.get('createdAt', journey.get('created_at')),
                'updated_at': journey.get('updatedAt', journey.get('updated_at')),
                'overall_progress': journey.get('overallProgress', journey.get('overall_progress', 0)),
                'current_stage': journey.get('currentStageId', journey.get('current_stage', 'raw_analysis')),
                'created_by': journey.get('createdBy', journey.get('created_by', 'mcp-server')),
                'oda_component_type': journey.get('odaComponentType', journey.get('oda_component_type', 'customer-management')),
                'source_type': journey.get('sourceType', journey.get('source_type', 'database')),
                'stages': []  # Start with empty stages
            }
            self.journey_manager._save_journeys(journeys)
            logger.info(f'Successfully synchronized journey {journey_id} to local storage')
            
        except Exception as e:
            logger.error(f'Failed to synchronize journey {journey_id}: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Normalize field names to handle both camelCase and snake_case
            normalized_stage_data = {}
            for key, value in stage_data.items():
                # Convert camelCase to snake_case for consistency
                if key == 'stageId':
                    normalized_stage_data['stage_id'] = value
                elif key == 'canSkip':
                    normalized_stage_data['can_skip'] = value
                elif key == 'estimatedDuration':
                    normalized_stage_data['estimated_duration'] = value
                elif key == 'secondBrainEnabled':
                    normalized_stage_data['second_brain_enabled'] = value
                else:
                    normalized_stage_data[key] = value
            
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in normalized_stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add stage to the journey using the real manager
            stage_id = normalized_stage_data['stage_id']
            
            # Ensure the journey is synchronized between DynamoDB and local storage
            await self._ensure_journey_synchronized(journey_id)
            
            logger.info(f'Adding stage {stage_id} to journey {journey_id}')
            
            # Update the journey manager's stage definitions with the new stage
            self.journey_manager.stage_definitions[stage_id] = {
                'name': normalized_stage_data['name'],
                'description': normalized_stage_data['description'],
                'order': normalized_stage_data.get('order', len(journey.get('stages', []))),
                'steps': normalized_stage_data.get('steps', [])
            }
            
            # Update the journey's stages list properly
            journeys = self.journey_manager._load_journeys()
            logger.info(f'Loaded journeys: {list(journeys.keys())}')
            
            # Since we ensured the journey exists above, we can use the journey_id directly
            if journey_id in journeys:
                logger.info(f'Found journey: {journey_id}')
                if 'stages' not in journeys[journey_id]:
                    journeys[journey_id]['stages'] = []
                if stage_id not in journeys[journey_id]['stages']:
                    journeys[journey_id]['stages'].append(stage_id)
                    self.journey_manager._save_journeys(journeys)
                    logger.info(f'Stage {stage_id} added to journey {journey_id} stages list: {journeys[journey_id]["stages"]}')
                else:
                    logger.info(f'Stage {stage_id} already exists in journey {journey_id}')
            else:
                logger.error(f'Journey {journey_id} not found in loaded journeys: {list(journeys.keys())}')
                # This shouldn't happen since we created the entry above, but let's handle it
                journeys[journey_id] = {
                    'journey_id': journey_id,
                    'name': journey.get('name', 'Unknown'),
                    'status': journey.get('status', 'pending'),
                    'stages': [stage_id]
                }
                self.journey_manager._save_journeys(journeys)
                logger.info(f'Created new journey entry and added stage {stage_id} to journey {journey_id}')
            
            # Verify the stage was actually added
            updated_stages = self.journey_manager.get_journey_stages(journey_id)
            stage_ids = [s.get('stage_id') for s in updated_stages]
            
            logger.info(f'After adding stage {stage_id}: total stages = {len(updated_stages)}, stage_ids = {stage_ids}')
            
            if stage_id not in stage_ids:
                logger.error(f'Stage {stage_id} was not properly added to journey {journey_id}')
                logger.error(f'Expected stage_ids to contain {stage_id}, but got: {stage_ids}')
                
                # Try to debug the issue
                logger.error(f'Journey data after update: {journeys.get(journey_id, {})}')
                raise ValueError(f'Failed to add stage {stage_id} to journey {journey_id}')
            
            logger.info(f'Successfully added stage {stage_id} to journey {journey_id}. Total stages: {len(updated_stages)}')
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': normalized_stage_data,
                'verification': {
                    'stage_added': True,
                    'total_stages': len(updated_stages),
                    'all_stage_ids': stage_ids
                }
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # Get actual DynamoDB table connection (similar to simple_journeys_tool)
            import os
            import sys
            import boto3
            from decimal import Decimal
            
            # Setup DynamoDB connection
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                
                try:
                    from aws_client_utils import create_aws_resource
                    role_arn = os.environ.get('AWS_ROLE_ARN')
                    if role_arn:
                        dynamodb = create_aws_resource('dynamodb', role_arn=role_arn)
                    else:
                        dynamodb = boto3.resource('dynamodb')
                except ImportError:
                    dynamodb = boto3.resource('dynamodb')
                
                table = dynamodb.Table('TransformationSystem')
                
            except Exception as e:
                logger.error(f'Failed to setup DynamoDB connection: {str(e)}')
                return []
            
            # Clean journey ID
            clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
            
            # Query rules using GSI1 following manage_journey.py pattern
            response = table.query(
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
                    'rule_id': rule_data.get('ruleId'),
                    'stage_id': rule_data.get('stageId'),
                    'title': rule_data.get('title'),
                    'description': rule_data.get('description'),
                    'type': rule_data.get('type'),
                    'priority': rule_data.get('priority'),
                    'scope': rule_data.get('scope'),
                    'status': rule_data.get('status', 'active'),
                    'content': rule_data.get('content', {}),
                    'context': rule_data.get('context', {}),
                    'metadata': rule_data.get('metadata', {})
                })
            
            return rules
            
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50): pass