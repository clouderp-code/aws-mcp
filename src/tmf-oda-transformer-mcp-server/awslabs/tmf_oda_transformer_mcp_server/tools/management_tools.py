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
from datetime import datetime, timezone, timedelta
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


# Missing function definitions with actual DynamoDB operations
async def _handle_list_rules(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    stage_id: Optional[str] = None,
    rule_type: Optional[str] = None,
    start_time: datetime = None
) -> Dict[str, Any]:
    """Handle list rules operation with actual DynamoDB query."""
    try:
        if not journey_id:
            raise ValueError("journey_id is required")
        
        # Setup DynamoDB connection
        import os, sys, boto3
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        try:
            from aws_client_utils import create_aws_resource
            role_arn = os.environ.get('AWS_ROLE_ARN')
            dynamodb = create_aws_resource('dynamodb', role_arn=role_arn) if role_arn else boto3.resource('dynamodb')
        except ImportError:
            dynamodb = boto3.resource('dynamodb')
        
        table = dynamodb.Table('TransformationSystem')
        
        # Clean journey ID and validate journey exists
        clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
        response = table.get_item(Key={'PK': f'JOURNEY#{clean_id}', 'SK': 'METADATA'})
        if 'Item' not in response:
            raise ValueError(f"Journey not found: {journey_id}")
        
        # Query rules using GSI1
        if stage_id:
            # When filtering by stage, use KeyConditionExpression for both GSI1PK and GSI1SK
            query_params = {
                'IndexName': 'GSI1',
                'KeyConditionExpression': 'GSI1PK = :pk AND begins_with(GSI1SK, :stage_id)',
                'ExpressionAttributeValues': {
                    ':pk': f'JOURNEY#{clean_id}#RULES',
                    ':stage_id': stage_id
                }
            }
            logger.debug(f'Adding stage filter for stage_id: {stage_id}')
        else:
            # When no stage filter, just query by GSI1PK
            query_params = {
                'IndexName': 'GSI1',
                'KeyConditionExpression': 'GSI1PK = :pk',
                'ExpressionAttributeValues': {':pk': f'JOURNEY#{clean_id}#RULES'}
            }
        
        rules_response = table.query(**query_params)
        logger.debug(f'DynamoDB query response: {rules_response}')
        rules = []
        
        for item in rules_response.get('Items', []):
            rule_data = item.get('Data', {})
            
            # Debug logging to see what we're getting
            logger.debug(f'Processing rule item: {item}')
            logger.debug(f'Rule data: {rule_data}')
            
            # Apply rule type filter if provided
            if rule_type and rule_data.get('type') != rule_type:
                continue
                
            # Format rule following the expected structure
            rule = {
                'rule_id': rule_data.get('ruleId'),
                'ruleId': rule_data.get('ruleId'),  # Add camelCase for test compatibility
                'journey_id': rule_data.get('journeyId'),
                'journeyId': rule_data.get('journeyId'),  # Add camelCase for test compatibility
                'stage_id': rule_data.get('stageId'),
                'stageId': rule_data.get('stageId'),  # Add camelCase for test compatibility
                'name': rule_data.get('title'),  # Add name field for test compatibility
                'title': rule_data.get('title'),
                'description': rule_data.get('description'),
                'type': rule_data.get('type'),
                'priority': rule_data.get('priority'),
                'scope': rule_data.get('scope'),
                'status': rule_data.get('status', 'active'),
                'context': rule_data.get('context', {}),
                'content': rule_data.get('content', {}),
                'metadata': rule_data.get('metadata', {}),
                'created_at': item.get('CreatedAt'),
                'updated_at': item.get('UpdatedAt')
            }
            rules.append(rule)
        
        # Sort rules by stage_id and priority
        rules.sort(key=lambda x: (x.get('stage_id', ''), x.get('priority', 'medium')))
        
        logger.info(f'Successfully retrieved {len(rules)} rules for journey {journey_id}')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved {len(rules)} rules for journey {journey_id}',
            start_time=start_time,
            operation='list_rules',
            journey_id=journey_id,
            stage_id=stage_id,
            rule_type=rule_type,
            rules=rules,
            total_rules=len(rules)
        )
        
    except Exception as e:
        logger.error(f'Failed to list rules: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey list_rules operation failed: {str(e)}',
            start_time=start_time,
            operation='list_rules',
            journey_id=journey_id,
            stage_id=stage_id,
            rule_type=rule_type
        )


async def _handle_add_rule(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    stage_id: Optional[str], 
    rule_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle add rule operation with actual DynamoDB storage."""
    try:
        if not journey_id or not stage_id or not rule_data:
            raise ValueError("journey_id, stage_id, and rule_data are required")
        
        # Validate required fields
        required_fields = ['title', 'description', 'type', 'priority', 'scope', 'content']
        for field in required_fields:
            if field not in rule_data:
                raise ValueError(f"Missing required field in rule_data: {field}")
        
        # Setup DynamoDB connection
        import os, sys, boto3
        from decimal import Decimal
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        try:
            from aws_client_utils import create_aws_resource
            role_arn = os.environ.get('AWS_ROLE_ARN')
            dynamodb = create_aws_resource('dynamodb', role_arn=role_arn) if role_arn else boto3.resource('dynamodb')
        except ImportError:
            dynamodb = boto3.resource('dynamodb')
        
        table = dynamodb.Table('TransformationSystem')
        
        # Clean journey ID and validate journey exists
        clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
        response = table.get_item(Key={'PK': f'JOURNEY#{clean_id}', 'SK': 'METADATA'})
        if 'Item' not in response:
            raise ValueError(f"Journey not found: {journey_id}")
        
        # Generate rule ID and get current rules count
        rule_id = rule_data.get('rule_id', f'rule-{stage_id}-{rule_data["type"]}-{str(uuid.uuid4())[:8]}')
        rules_response = table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :pk',
            ExpressionAttributeValues={':pk': f'JOURNEY#{clean_id}#RULES'}
        )
        rule_index = len(rules_response.get('Items', []))
        
        # Convert floats to Decimal for DynamoDB
        def convert_floats(data):
            if isinstance(data, dict):
                return {k: convert_floats(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [convert_floats(item) for item in data]
            elif isinstance(data, float):
                return Decimal(str(data))
            return data
        
        rule_data = convert_floats(rule_data)
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Create rule item following manage_journey.py pattern
        rule_item = {
            'PK': f'JOURNEY#{clean_id}',
            'SK': f'RULE#{stage_id}#{rule_index:03d}#{rule_id}',
            'EntityType': 'SecondBrainRule',
            'GSI1PK': f'JOURNEY#{clean_id}#RULES',
            'GSI1SK': f'{stage_id}#{rule_data["priority"]}#{rule_index:03d}',
            'CreatedAt': timestamp,
            'UpdatedAt': timestamp,
            'Data': {
                'ruleId': rule_id,
                'journeyId': clean_id,
                'stageId': stage_id,
                'title': rule_data['title'],
                'description': rule_data['description'],
                'type': rule_data['type'],
                'priority': rule_data['priority'],
                'scope': rule_data['scope'],
                'status': rule_data.get('status', 'active'),
                'context': rule_data.get('context', {}),
                'content': rule_data['content'],
                'metadata': {
                    'createdBy': rule_data.get('createdBy', 'mcp-user'),
                    'version': rule_data.get('version', '1.0'),
                    'tags': rule_data.get('tags', [stage_id, rule_data['type'], rule_data['priority']]),
                    'applicableStages': rule_data.get('applicableStages', [stage_id]),
                    'ruleEngine': 'second_brain_v1'
                }
            }
        }
        
        # Store rule in DynamoDB
        table.put_item(Item=rule_item)
        logger.info(f'Successfully added rule {rule_id} to DynamoDB')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Second Brain rule {rule_id} added successfully to stage {stage_id}',
            start_time=start_time,
            operation='add_rule',
            journey_id=journey_id,
            stage_id=stage_id,
            rule_id=rule_id,
            rule_data=rule_data
        )
        
    except Exception as e:
        logger.error(f'Failed to add rule: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey add_rule operation failed: {str(e)}',
            start_time=start_time,
            operation='add_rule',
            journey_id=journey_id,
            stage_id=stage_id
        )


async def _handle_update_rule(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    stage_id: Optional[str],
    rule_id: Optional[str],
    rule_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle update rule operation with actual DynamoDB operations."""
    try:
        if not journey_id or not stage_id or not rule_id or not rule_data:
            raise ValueError("journey_id, stage_id, rule_id, and rule_data are required")
        
        # Setup DynamoDB connection  
        import os, sys, boto3
        from decimal import Decimal
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        try:
            from aws_client_utils import create_aws_resource
            role_arn = os.environ.get('AWS_ROLE_ARN')
            dynamodb = create_aws_resource('dynamodb', role_arn=role_arn) if role_arn else boto3.resource('dynamodb')
        except ImportError:
            dynamodb = boto3.resource('dynamodb')
        
        table = dynamodb.Table('TransformationSystem')
        clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
        
        # Find existing rule
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            FilterExpression='#data.ruleId = :rule_id AND #data.stageId = :stage_id',
            ExpressionAttributeNames={'#data': 'Data'},
            ExpressionAttributeValues={
                ':pk': f'JOURNEY#{clean_id}',
                ':sk': 'RULE#',
                ':rule_id': rule_id,
                ':stage_id': stage_id
            }
        )
        
        if not response['Items']:
            raise ValueError(f"Rule not found: {rule_id} in stage {stage_id}")
        
        existing_item = response['Items'][0]
        existing_data = existing_item['Data']
        
        # Convert floats to Decimal and merge data
        def convert_floats(data):
            if isinstance(data, dict):
                return {k: convert_floats(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [convert_floats(item) for item in data]
            elif isinstance(data, float):
                return Decimal(str(data))
            return data
        
        updated_data = existing_data.copy()
        updated_data.update(convert_floats(rule_data))
        updated_data['updatedAt'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Update the rule in DynamoDB
        table.update_item(
            Key={'PK': existing_item['PK'], 'SK': existing_item['SK']},
            UpdateExpression='SET #data = :data, UpdatedAt = :updated_at',
            ExpressionAttributeNames={'#data': 'Data'},
            ExpressionAttributeValues={
                ':data': updated_data,
                ':updated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
        )
        
        logger.info(f'Successfully updated rule {rule_id} in DynamoDB')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Second Brain rule {rule_id} updated successfully in stage {stage_id}',
            start_time=start_time,
            operation='update_rule',
            journey_id=journey_id,
            stage_id=stage_id,
            rule_id=rule_id,
            rule_data=rule_data
        )
        
    except Exception as e:
        logger.error(f'Failed to update rule: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey update_rule operation failed: {str(e)}',
            start_time=start_time,
            operation='update_rule',
            journey_id=journey_id,
            stage_id=stage_id,
            rule_id=rule_id
        )


async def _handle_delete_rule(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    stage_id: Optional[str],
    rule_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle delete rule operation with actual DynamoDB operations."""
    try:
        if not journey_id or not stage_id or not rule_id:
            raise ValueError("journey_id, stage_id, and rule_id are required")
        
        # Setup DynamoDB connection
        import os, sys, boto3
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        try:
            from aws_client_utils import create_aws_resource
            role_arn = os.environ.get('AWS_ROLE_ARN')
            dynamodb = create_aws_resource('dynamodb', role_arn=role_arn) if role_arn else boto3.resource('dynamodb')
        except ImportError:
            dynamodb = boto3.resource('dynamodb')
        
        table = dynamodb.Table('TransformationSystem')
        clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
        
        # Find rule to delete
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            FilterExpression='#data.ruleId = :rule_id AND #data.stageId = :stage_id',
            ExpressionAttributeNames={'#data': 'Data'},
            ExpressionAttributeValues={
                ':pk': f'JOURNEY#{clean_id}',
                ':sk': 'RULE#',
                ':rule_id': rule_id,
                ':stage_id': stage_id
            }
        )
        
        if not response['Items']:
            raise ValueError(f"Rule not found: {rule_id} in stage {stage_id}")
        
        rule_item = response['Items'][0]
        
        # Delete the rule from DynamoDB
        table.delete_item(Key={'PK': rule_item['PK'], 'SK': rule_item['SK']})
        logger.info(f'Successfully deleted rule {rule_id} from DynamoDB')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Second Brain rule {rule_id} deleted successfully from stage {stage_id}',
            start_time=start_time,
            operation='delete_rule',
            journey_id=journey_id,
            stage_id=stage_id,
            rule_id=rule_id
        )
        
    except Exception as e:
        logger.error(f'Failed to delete rule: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey delete_rule operation failed: {str(e)}',
            start_time=start_time,
            operation='delete_rule',
            journey_id=journey_id,
            stage_id=stage_id,
            rule_id=rule_id
        )


# Missing job management handler functions
async def _handle_list_jobs(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    stage_id: Optional[str],
    status_filter: Optional[str],
    limit: int,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle list jobs operation."""
    try:
        if not journey_id:
            raise ValueError("journey_id is required")
        
        # Use the journey manager to get jobs
        if stage_id:
            jobs = journey_service.manager.get_stage_jobs(journey_id, stage_id, limit)
        else:
            jobs = journey_service.manager.get_stage_jobs(journey_id, '', limit)
        
        # Apply status filter if provided
        if status_filter and jobs:
            jobs = [job for job in jobs if job.get('status') == status_filter]
        
        logger.info(f'Successfully retrieved {len(jobs)} jobs for journey {journey_id}')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved {len(jobs)} jobs for journey {journey_id}',
            start_time=start_time,
            operation='list_jobs',
            journey_id=journey_id,
            stage_id=stage_id,
            status_filter=status_filter,
            jobs=jobs,
            total_jobs=len(jobs)
        )
        
    except Exception as e:
        logger.error(f'Failed to list jobs: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey list_jobs operation failed: {str(e)}',
            start_time=start_time,
            operation='list_jobs',
            journey_id=journey_id,
            stage_id=stage_id
        )


async def _handle_run_job(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    stage_id: Optional[str],
    triggered_by: Optional[str],
    reason: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle run job operation with real DynamoDB integration."""
    try:
        if not journey_id:
            raise ValueError("journey_id is required")
        if not stage_id:
            raise ValueError("stage_id is required")
        
        # Setup DynamoDB and job executor
        import os, sys
        
        try:
            # Import and use the real job executor from the scripts package
            from ..scripts.job_executor import TransformationJobExecutor
            
            role_arn = os.environ.get('AWS_ROLE_ARN')
            job_executor = TransformationJobExecutor(role_arn=role_arn)
            
            # Start job execution using real DynamoDB operations
            job_id = job_executor.start_job_execution(
                journey_id=journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id,
                stage_id=stage_id,
                triggered_by=triggered_by or 'mcp-server',
                reason=reason or f'MCP Server job execution for stage {stage_id}'
            )
            
            # Create job info response
            job_info = {
                'job_id': job_id,
                'journey_id': journey_id,
                'stage_id': stage_id,
                'status': 'running',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'job_type': 'transformation',
                'description': f'Job for stage {stage_id}',
                'priority': 'medium',
                'triggered_by': triggered_by or 'mcp-server',
                'reason': reason or f'MCP Server job execution for stage {stage_id}',
                'parameters': {},
                'progress': 0
            }
            
            logger.info(f'Successfully started real job {job_id} for journey {journey_id}, stage {stage_id}')
            
            return BaseToolMixin.create_tool_result(
                status='success',
                message=f'Job {job_id} created and started successfully for stage {stage_id}',
                start_time=start_time,
                operation='run_job',
                journey_id=journey_id,
                stage_id=stage_id,
                job_id=job_id,
                job_info=job_info
            )
            
        except ImportError as ie:
            # Job executor not available - return error instead of simulation
            logger.error(f"Job executor not available: {str(ie)}")
            return BaseToolMixin.create_tool_result(
                status='error',
                message=f'Job executor module not available: {str(ie)}',
                start_time=start_time,
                operation='run_job',
                journey_id=journey_id,
                stage_id=stage_id
            )
        
    except Exception as e:
        logger.error(f'Failed to run job: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey run_job operation failed: {str(e)}',
            start_time=start_time,
            operation='run_job',
            journey_id=journey_id,
            stage_id=stage_id
        )


async def _handle_get_job(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    job_id: Optional[str],
    include_all: Optional[bool],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle get job operation with real DynamoDB operations."""
    try:
        if not journey_id:
            raise ValueError("journey_id is required")
        if not job_id:
            raise ValueError("job_id is required")
        
        # Setup DynamoDB connection
        import os, sys, boto3
        from decimal import Decimal
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        try:
            from aws_client_utils import create_aws_resource
            role_arn = os.environ.get('AWS_ROLE_ARN')
            dynamodb = create_aws_resource('dynamodb', role_arn=role_arn) if role_arn else boto3.resource('dynamodb')
        except ImportError:
            dynamodb = boto3.resource('dynamodb')
        
        table = dynamodb.Table('TransformationSystem')
        clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
        
        # Find the job record in DynamoDB
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            FilterExpression='#data.jobId = :job_id',
            ExpressionAttributeNames={'#data': 'Data'},
            ExpressionAttributeValues={
                ':pk': f'JOURNEY#{clean_id}',
                ':sk': 'JOB#',
                ':job_id': job_id
            }
        )
        
        if not response['Items']:
            # Job not found in DynamoDB - return error instead of simulation
            logger.error(f"Job {job_id} not found in DynamoDB")
            return BaseToolMixin.create_tool_result(
                status='error',
                message=f'Job {job_id} not found',
                start_time=start_time,
                operation='get_job',
                journey_id=journey_id,
                job_id=job_id
            )
        else:
            # Job found, extract real data from DynamoDB
            job_item = response['Items'][0]
            job_data = job_item['Data']
            
            # Convert Decimal values to float for JSON serialization
            def convert_decimal(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: convert_decimal(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimal(v) for v in obj]
                return obj
            
            job_info = {
                'job_id': job_data.get('jobId', job_id),
                'journey_id': journey_id,
                'stage_id': job_data.get('stageId', 'unknown'),
                'status': job_data.get('status', 'unknown'),
                'created_at': job_data.get('startTime', job_data.get('createdAt', datetime.now(timezone.utc).isoformat())),
                'updated_at': job_data.get('updatedAt', datetime.now(timezone.utc).isoformat()),
                'job_type': job_data.get('jobType', 'transformation'),
                'description': job_data.get('description', f'Job {job_id} details'),
                'priority': job_data.get('priority', 'medium'),
                'progress': convert_decimal(job_data.get('progress', 0)),
                'parameters': convert_decimal(job_data.get('parameters', {})),
                'metrics': convert_decimal(job_data.get('jobMetrics', {}))
            }
        
        # Add extra details if include_all is True
        if include_all:
            if response['Items']:
                # Real data from DynamoDB
                job_data = response['Items'][0]['Data']
                step_results = job_data.get('stepResults', {})
                steps = []
                
                for step_id, step_info in step_results.items():
                    if isinstance(step_info, dict):
                        steps.append({
                            'step_id': step_id,
                            'status': step_info.get('status', 'unknown'),
                            'duration': float(step_info.get('duration', 0)) if step_info.get('duration') else None
                        })
                
                # Get log metrics
                job_metrics = job_data.get('jobMetrics', {})
                
                job_info.update({
                    'steps': steps,
                    'logs_count': int(job_metrics.get('totalLogs', 0)) if job_metrics.get('totalLogs') else 0,
                    'error_count': int(job_metrics.get('totalErrors', 0)) if job_metrics.get('totalErrors') else 0,
                    'warning_count': int(job_metrics.get('totalWarnings', 0)) if job_metrics.get('totalWarnings') else 0
                })
            # No simulation - only return real data from DynamoDB
        
        logger.info(f'Successfully retrieved job {job_id} details')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved job {job_id} details',
            start_time=start_time,
            operation='get_job',
            journey_id=journey_id,
            job_id=job_id,
            include_all=include_all,
            job_status=job_info['status'],
            job_info=job_info
        )
        
    except Exception as e:
        logger.error(f'Failed to get job: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey get_job operation failed: {str(e)}',
            start_time=start_time,
            operation='get_job',
            journey_id=journey_id,
            job_id=job_id
        )


async def _handle_journey_read(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    stage_id: Optional[str],
    include_stages: bool,
    include_job_history: bool,
    limit: int,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey read/list operation with real DynamoDB operations."""
    try:
        if journey_id:
            # Get specific journey
            journey = journey_service.manager.get_journey_status(journey_id)
            if not journey:
                raise ValueError(f"Journey {journey_id} not found")
            
            result_data = {
                'journey': journey,
                'journey_id': journey_id,
                'include_stages': include_stages,
                'include_job_history': include_job_history
            }
            
            # Add stages if requested
            if include_stages:
                try:
                    stages = journey_service.manager.list_journey_stages(journey_id)
                    result_data['stages'] = stages
                except:
                    result_data['stages'] = []
            
            # Add job history if requested
            if include_job_history:
                try:
                    jobs = journey_service.manager.list_journey_jobs(journey_id, limit=limit)
                    result_data['job_history'] = jobs
                except:
                    result_data['job_history'] = []
            
            return BaseToolMixin.create_tool_result(
                status='success',
                message=f'Retrieved journey {journey_id} details',
                start_time=start_time,
                operation='read_journey',
                **result_data
            )
        else:
            # List all journeys
            try:
                journeys = journey_service.manager.list_journeys()
                total_journeys = len(journeys) if journeys else 0
                
                # Apply limit
                if limit > 0:
                    journeys = journeys[:limit]
                
                return BaseToolMixin.create_tool_result(
                    status='success',
                    message=f'Retrieved {len(journeys)} journeys (total: {total_journeys})',
                    start_time=start_time,
                    operation='list_journeys',
                    journeys=journeys,
                    total_journeys=total_journeys,
                    limit=limit
                )
            except Exception as e:
                logger.warning(f"Failed to list journeys from DynamoDB: {str(e)}, using fallback")
                # Fallback for development
                return BaseToolMixin.create_tool_result(
                    status='success',
                    message='No journeys found (development mode)',
                    start_time=start_time,
                    operation='list_journeys',
                    journeys=[],
                    total_journeys=0,
                    limit=limit
                )
                
    except Exception as e:
        logger.error(f'Failed to read journey: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey read operation failed: {str(e)}',
            start_time=start_time,
            operation='read_journey',
            journey_id=journey_id
        )


async def _handle_update_job_status(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    job_id: Optional[str],
    job_status: Optional[str],
    progress: Optional[int],
    current_step: Optional[str],
    error_message: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle update job status operation with real DynamoDB operations."""
    try:
        if not journey_id:
            raise ValueError("journey_id is required")
        if not job_id:
            raise ValueError("job_id is required")
        if not job_status:
            raise ValueError("job_status is required")
        
        # Setup DynamoDB connection
        import os, sys, boto3
        from decimal import Decimal
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        try:
            from aws_client_utils import create_aws_resource
            role_arn = os.environ.get('AWS_ROLE_ARN')
            dynamodb = create_aws_resource('dynamodb', role_arn=role_arn) if role_arn else boto3.resource('dynamodb')
        except ImportError:
            dynamodb = boto3.resource('dynamodb')
        
        table = dynamodb.Table('TransformationSystem')
        clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
        
        # Find the job record in DynamoDB
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            FilterExpression='#data.jobId = :job_id',
            ExpressionAttributeNames={'#data': 'Data'},
            ExpressionAttributeValues={
                ':pk': f'JOURNEY#{clean_id}',
                ':sk': 'JOB#',
                ':job_id': job_id
            }
        )
        
        if not response['Items']:
            # Job not found in DynamoDB - return error instead of simulation
            logger.error(f"Job {job_id} not found in DynamoDB")
            return BaseToolMixin.create_tool_result(
                status='error',
                message=f'Job {job_id} not found',
                start_time=start_time,
                operation='update_job_status',
                journey_id=journey_id,
                job_id=job_id
            )
        
        # Job found, update it
        job_item = response['Items'][0]
        
        # Build update expression dynamically
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {'#data': 'Data'}
        
        update_expression_parts.append('#data.#status = :status')
        expression_attribute_names['#status'] = 'status'
        expression_attribute_values[':status'] = job_status
        
        update_expression_parts.append('#data.updatedAt = :updated_at')
        expression_attribute_values[':updated_at'] = datetime.now(timezone.utc).isoformat()
        
        if progress is not None:
            update_expression_parts.append('#data.progress = :progress')
            expression_attribute_values[':progress'] = Decimal(str(progress))
        
        if current_step:
            update_expression_parts.append('#data.currentStep = :current_step')
            expression_attribute_values[':current_step'] = current_step
        
        if error_message:
            update_expression_parts.append('#data.errorMessage = :error_message')
            expression_attribute_values[':error_message'] = error_message
        
        # Perform the update
        table.update_item(
            Key={'PK': job_item['PK'], 'SK': job_item['SK']},
            UpdateExpression='SET ' + ', '.join(update_expression_parts),
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        update_data = {
            'job_id': job_id,
            'status': job_status,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        if progress is not None:
            update_data['progress'] = progress
        if current_step:
            update_data['current_step'] = current_step
        if error_message:
            update_data['error_message'] = error_message
        
        logger.info(f'Successfully updated job {job_id} status to {job_status}')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Job {job_id} status updated to {job_status}',
            start_time=start_time,
            operation='update_job_status',
            journey_id=journey_id,
            job_id=job_id,
            update_data=update_data
        )
        
    except Exception as e:
        logger.error(f'Failed to update job status: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey update_job_status operation failed: {str(e)}',
            start_time=start_time,
            operation='update_job_status',
            journey_id=journey_id,
            job_id=job_id
        )


async def _handle_get_job_metrics(
    ctx: Context,
    journey_service,
    journey_id: Optional[str],
    job_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle get job metrics operation with real DynamoDB operations."""
    try:
        if not journey_id:
            raise ValueError("journey_id is required")
        if not job_id:
            raise ValueError("job_id is required")
        
        # Setup DynamoDB connection
        import os, sys, boto3
        from decimal import Decimal
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'scripts')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        try:
            from aws_client_utils import create_aws_resource
            role_arn = os.environ.get('AWS_ROLE_ARN')
            dynamodb = create_aws_resource('dynamodb', role_arn=role_arn) if role_arn else boto3.resource('dynamodb')
        except ImportError:
            dynamodb = boto3.resource('dynamodb')
        
        table = dynamodb.Table('TransformationSystem')
        clean_id = journey_id.replace('JRN-', '') if journey_id.startswith('JRN-') else journey_id
        
        # Find the job record in DynamoDB
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            FilterExpression='#data.jobId = :job_id',
            ExpressionAttributeNames={'#data': 'Data'},
            ExpressionAttributeValues={
                ':pk': f'JOURNEY#{clean_id}',
                ':sk': 'JOB#',
                ':job_id': job_id
            }
        )
        
        if not response['Items']:
            # Job not found in DynamoDB - return error instead of simulation
            logger.error(f"Job {job_id} not found in DynamoDB")
            return BaseToolMixin.create_tool_result(
                status='error',
                message=f'Job {job_id} not found',
                start_time=start_time,
                operation='get_job_metrics',
                journey_id=journey_id,
                job_id=job_id
            )
        
        # Job found, extract real metrics from DynamoDB
        job_item = response['Items'][0]
        job_data = job_item['Data']
        
        # Calculate basic metrics from job data
        start_time_str = job_data.get('startTime', '')
        end_time_str = job_data.get('endTime', '')
        
        # Calculate duration
        duration = 0.0
        if start_time_str and end_time_str:
            try:
                start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                duration = (end_dt - start_dt).total_seconds()
            except:
                duration = 0.0
        
        # Extract step results and timeline
        step_results = job_data.get('stepResults', {})
        timeline = []
        step_durations = []
        
        for step_id, step_data in step_results.items():
            if isinstance(step_data, dict):
                step_duration = step_data.get('duration', 0)
                if isinstance(step_duration, Decimal):
                    step_duration = float(step_duration)
                step_durations.append(step_duration)
                
                timeline.append({
                    'step': step_id,
                    'status': step_data.get('status', 'unknown'),
                    'duration': step_duration,
                    'start_time': step_data.get('startTime', ''),
                    'end_time': step_data.get('endTime', '')
                })
        
        # Calculate performance metrics
        avg_step_duration = sum(step_durations) / len(step_durations) if step_durations else 0
        slowest_step = None
        fastest_step = None
        
        if timeline:
            sorted_by_duration = sorted(timeline, key=lambda x: x['duration'])
            if sorted_by_duration:
                fastest_step = {'step': sorted_by_duration[0]['step'], 'duration': sorted_by_duration[0]['duration']}
                slowest_step = {'step': sorted_by_duration[-1]['step'], 'duration': sorted_by_duration[-1]['duration']}
        
        # Extract metrics from job data
        job_metrics = job_data.get('jobMetrics', {})
        
        metrics = {
            'job_id': job_id,
            'journey_id': journey_id,
            'stage_id': job_data.get('stageId', 'unknown'),
            'status': job_data.get('status', 'unknown'),
            'duration': duration,
            'start_time': start_time_str,
            'end_time': end_time_str,
            'performance_metrics': {
                'avg_step_duration': avg_step_duration,
                'slowest_step': slowest_step,
                'fastest_step': fastest_step,
                'total_steps': len(step_results),
                'completed_steps': len([s for s in step_results.values() if isinstance(s, dict) and s.get('status') == 'completed']),
                'error_rate': 0.0,  # Calculate from logs if available
                'success_rate': 100.0 if job_data.get('status') == 'completed' else 0.0
            },
            'resource_metrics': {
                'cpu_usage_avg': float(job_metrics.get('cpuUsage', 0)) if job_metrics.get('cpuUsage') else 0.0,
                'memory_usage_avg': float(job_metrics.get('memoryUsage', 0)) if job_metrics.get('memoryUsage') else 0.0,
                'disk_io_avg': float(job_metrics.get('diskIO', 0)) if job_metrics.get('diskIO') else 0.0
            },
            'log_metrics': {
                'total_entries': int(job_metrics.get('totalLogs', 0)) if job_metrics.get('totalLogs') else 0,
                'error_entries': int(job_metrics.get('totalErrors', 0)) if job_metrics.get('totalErrors') else 0,
                'warning_entries': int(job_metrics.get('totalWarnings', 0)) if job_metrics.get('totalWarnings') else 0,
                'info_entries': 0  # Calculate as total - errors - warnings
            },
            'timeline': timeline
        }
        
        # Calculate info entries
        total_logs = metrics['log_metrics']['total_entries']
        error_logs = metrics['log_metrics']['error_entries']
        warning_logs = metrics['log_metrics']['warning_entries']
        metrics['log_metrics']['info_entries'] = max(0, total_logs - error_logs - warning_logs)
        
        logger.info(f'Successfully retrieved job metrics for {job_id}')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved metrics for job {job_id}',
            start_time=start_time,
            operation='get_job_metrics',
            journey_id=journey_id,
            job_id=job_id,
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f'Failed to get job metrics: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey get_job_metrics operation failed: {str(e)}',
            start_time=start_time,
            operation='get_job_metrics',
            journey_id=journey_id,
            job_id=job_id
        )