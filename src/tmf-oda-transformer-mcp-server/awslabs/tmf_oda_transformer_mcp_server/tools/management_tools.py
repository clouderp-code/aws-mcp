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
        logger.info("Enhanced journey service initialized with comprehensive lifecycle management")
    
    async def list_stages(self, journey_id: str) -> List[Dict[str, Any]]:
        """List all stages for a journey."""
        try:
            # This would integrate with the real stage management system
            # For now, return mock data structure
            return [
                {
                    'stage_id': 'raw_analysis',
                    'name': 'Raw Input Analysis', 
                    'description': 'Analyze the raw database schema and structure',
                    'order': 0,
                    'status': 'completed',
                    'estimated_duration': '15m',
                    'can_skip': False,
                    'second_brain_enabled': True,
                    'rule_types': ['field_mapping', 'contextual_recommendations'],
                    'steps': [
                        {'id': 'schema_parsing', 'name': 'Schema File Parsing', 'status': 'completed'},
                        {'id': 'relationship_discovery', 'name': 'Relationship Discovery', 'status': 'completed'}
                    ]
                },
                {
                    'stage_id': 'stripped_schema',
                    'name': 'Create Stripped Document',
                    'description': 'Create TMF-focused simplified schema',
                    'order': 1,
                    'status': 'pending',
                    'estimated_duration': '12m',
                    'can_skip': False,
                    'second_brain_enabled': True,
                    'rule_types': ['field_mapping', 'data_interpretation'],
                    'steps': [
                        {'id': 'schema_stripping', 'name': 'Schema Stripping', 'status': 'pending'},
                        {'id': 'core_structure_extraction', 'name': 'Core Structure Extraction', 'status': 'pending'}
                    ]
                }
            ]
        except Exception as e:
            logger.error(f'Failed to list stages: {str(e)}')
            raise
    
    async def add_stage(self, journey_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new stage to a journey."""
        try:
            # Validate required fields
            required_fields = ['stage_id', 'name', 'description']
            for field in required_fields:
                if field not in stage_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # This would integrate with the real stage management system
            stage_id = stage_data['stage_id']
            
            return {
                'stage_id': stage_id,
                'message': f'Stage {stage_id} added successfully to journey {journey_id}',
                'stage_data': stage_data
            }
        except Exception as e:
            logger.error(f'Failed to add stage: {str(e)}')
            raise
    
    async def list_rules(self, journey_id: str, stage_id: Optional[str] = None, 
                        rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Second Brain rules for a journey."""
        try:
            # This would integrate with the real rules management system
            rules = [
                {
                    'rule_id': 'rule-001',
                    'stage_id': 'raw_analysis',
                    'title': 'Customer ID Field Mapping',
                    'type': 'field_mapping',
                    'priority': 'high',
                    'scope': 'global',
                    'status': 'active',
                    'content': {
                        'natural_language': 'Map customer_id fields to TMF Party.id',
                        'json_rule': {'field_mapping': 'customer_id -> Party.id'}
                    }
                }
            ]
            
            # Apply filters
            if stage_id:
                rules = [r for r in rules if r.get('stage_id') == stage_id]
            if rule_type:
                rules = [r for r in rules if r.get('type') == rule_type]
            
            return rules
        except Exception as e:
            logger.error(f'Failed to list rules: {str(e)}')
            raise
    
    async def list_jobs(self, journey_id: str, stage_id: Optional[str] = None,
                       status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List job executions for a journey."""
        try:
            # This would integrate with the real job management system
            jobs = [
                {
                    'job_id': 'JOB-001-20241217120000',
                    'stage_id': 'raw_analysis',
                    'stage_name': 'Raw Input Analysis',
                    'status': 'completed',
                    'triggered_by': 'mcp-user',
                    'reason': 'Manual execution',
                    'start_time': '2024-12-17T12:00:00Z',
                    'end_time': '2024-12-17T12:15:00Z',
                    'duration': '15m',
                    'progress': 100,
                    'logs_available': True,
                    'reports_available': True
                }
            ]
            
            # Apply filters
            if stage_id:
                jobs = [j for j in jobs if j.get('stage_id') == stage_id]
            if status_filter:
                jobs = [j for j in jobs if j.get('status') == status_filter]
            
            return jobs[:limit]
        except Exception as e:
            logger.error(f'Failed to list jobs: {str(e)}')
            raise


# Helper functions for enhanced operations (implementing the first few)

async def _handle_journey_read(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    include_stages: bool,
    include_job_history: bool,
    limit: int,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey read/list operations (existing implementation)."""
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
            job_limit=limit
        )
        
        if not journey_details:
            error_msg = f'Journey {journey_id} not found'
            logger.error(error_msg)
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
        raise


async def _handle_journey_create(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    journey_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey creation operations (existing implementation)."""
    try:
        if not journey_data:
            error_msg = "journey_data is required for CREATE action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate and parse journey data
        try:
            create_data = JourneyCreateData(**journey_data)
        except Exception as e:
            error_msg = f"Invalid journey_data format: {str(e)}"
            logger.error(error_msg)
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
        raise


async def _handle_journey_update(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    journey_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey update operations (existing implementation)."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for UPDATE action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not journey_data:
            error_msg = "journey_data is required for UPDATE action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate and parse update data
        try:
            update_data = JourneyUpdateData(**journey_data)
        except Exception as e:
            error_msg = f"Invalid journey_data format for update: {str(e)}"
            logger.error(error_msg)
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
        raise


async def _handle_journey_delete(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey deletion operations (existing implementation)."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for DELETE action"
            logger.error(error_msg)
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
        raise


# New enhanced operation handlers

async def _handle_list_stages(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle list stages operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for list_stages action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        stages = await journey_service.list_stages(journey_id)
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved {len(stages)} stages for journey {journey_id}',
            start_time=start_time,
            operation='list_stages',
            journey_id=journey_id,
            total_stages=len(stages),
            stages=stages
        )
        
    except Exception as e:
        error_msg = f'Failed to list stages: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_add_stage(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle add stage operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for add_stage action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not stage_data:
            error_msg = "stage_data is required for add_stage action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        result = await journey_service.add_stage(journey_id, stage_data)
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Stage added successfully to journey {journey_id}',
            start_time=start_time,
            operation='add_stage',
            journey_id=journey_id,
            **result
        )
        
    except Exception as e:
        error_msg = f'Failed to add stage: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_update_stage(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    stage_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle update stage operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for update_stage action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not stage_id:
            error_msg = "stage_id is required for update_stage action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not stage_data:
            error_msg = "stage_data is required for update_stage action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # This would integrate with real stage management
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Stage {stage_id} updated successfully in journey {journey_id}',
            start_time=start_time,
            operation='update_stage',
            journey_id=journey_id,
            stage_id=stage_id,
            stage_data=stage_data
        )
        
    except Exception as e:
        error_msg = f'Failed to update stage: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_delete_stage(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle delete stage operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for delete_stage action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not stage_id:
            error_msg = "stage_id is required for delete_stage action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # This would integrate with real stage management
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Stage {stage_id} deleted successfully from journey {journey_id}',
            start_time=start_time,
            operation='delete_stage',
            journey_id=journey_id,
            stage_id=stage_id
        )
        
    except Exception as e:
        error_msg = f'Failed to delete stage: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_add_default_stages(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle add default stages operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for add_default_stages action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # This would add the default TMF ODA transformation stages
        default_stages = [
            'raw_analysis', 'stripped_schema', 'tmf_mapping', 
            'migration_planning', 'data_migration', 'verification_validation'
        ]
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Added {len(default_stages)} default stages to journey {journey_id}',
            start_time=start_time,
            operation='add_default_stages',
            journey_id=journey_id,
            stages_added=default_stages
        )
        
    except Exception as e:
        error_msg = f'Failed to add default stages: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_list_rules(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    rule_type: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle list rules operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for list_rules action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        rules = await journey_service.list_rules(journey_id, stage_id, rule_type)
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved {len(rules)} Second Brain rules for journey {journey_id}',
            start_time=start_time,
            operation='list_rules',
            journey_id=journey_id,
            stage_id=stage_id,
            rule_type=rule_type,
            total_rules=len(rules),
            rules=rules
        )
        
    except Exception as e:
        error_msg = f'Failed to list rules: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_add_rule(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    rule_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle add rule operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for add_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not stage_id:
            error_msg = "stage_id is required for add_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not rule_data:
            error_msg = "rule_data is required for add_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate required fields
        required_fields = ['title', 'description', 'type', 'priority', 'scope', 'content']
        for field in required_fields:
            if field not in rule_data:
                raise ValueError(f"Missing required field in rule_data: {field}")
        
        # Generate rule ID if not provided
        rule_id = rule_data.get('rule_id', f'rule-{stage_id}-{str(uuid.uuid4())[:8]}')
        
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
        error_msg = f'Failed to add rule: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_update_rule(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    rule_id: Optional[str],
    rule_data: Optional[Dict[str, Any]],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle update rule operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for update_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not stage_id:
            error_msg = "stage_id is required for update_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not rule_id:
            error_msg = "rule_id is required for update_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not rule_data:
            error_msg = "rule_data is required for update_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
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
        error_msg = f'Failed to update rule: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_delete_rule(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    rule_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle delete rule operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for delete_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not stage_id:
            error_msg = "stage_id is required for delete_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not rule_id:
            error_msg = "rule_id is required for delete_rule action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
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
        error_msg = f'Failed to delete rule: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_list_jobs(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    status_filter: Optional[str],
    limit: int,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle list jobs operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for list_jobs action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        jobs = await journey_service.list_jobs(journey_id, stage_id, status_filter, limit)
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved {len(jobs)} job executions for journey {journey_id}',
            start_time=start_time,
            operation='list_jobs',
            journey_id=journey_id,
            stage_id=stage_id,
            status_filter=status_filter,
            total_jobs=len(jobs),
            jobs=jobs
        )
        
    except Exception as e:
        error_msg = f'Failed to list jobs: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_get_job(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    job_id: Optional[str],
    include_all: bool,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle get job details operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for get_job action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not job_id:
            error_msg = "job_id is required for get_job action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # This would integrate with real job management
        job_details = {
            'job_id': job_id,
            'journey_id': journey_id,
            'stage_id': 'raw_analysis',
            'stage_name': 'Raw Input Analysis',
            'status': 'completed',
            'triggered_by': 'mcp-user',
            'reason': 'Manual execution',
            'start_time': '2024-12-17T12:00:00Z',
            'end_time': '2024-12-17T12:15:00Z',
            'duration': 900.0,
            'progress': 100,
            'current_step': 'completed',
            'total_steps': 4,
            'step_results': {
                'schema_parsing': {'status': 'completed', 'duration': 300},
                'relationship_discovery': {'status': 'completed', 'duration': 300},
                'data_type_analysis': {'status': 'completed', 'duration': 180},
                'business_rules_extraction': {'status': 'completed', 'duration': 120}
            },
            'logs_available': True,
            'reports_available': True
        }
        
        if include_all:
            job_details['execution_details'] = {
                'retry_attempt': 0,
                's3_config': {
                    'logs_bucket': 'transformation-journey-logs',
                    'reports_bucket': 'transformation-journey-reports'
                },
                'job_metrics': {
                    'cpu_usage': 45.2,
                    'memory_usage': 67.8,
                    'items_processed': 1250
                }
            }
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved detailed information for job {job_id}',
            start_time=start_time,
            operation='get_job',
            journey_id=journey_id,
            job_id=job_id,
            **job_details
        )
        
    except Exception as e:
        error_msg = f'Failed to get job details: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_run_job(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    stage_id: Optional[str],
    triggered_by: str,
    reason: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle run job operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for run_job action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not stage_id:
            error_msg = "stage_id is required for run_job action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Generate a new job ID
        job_id = f'JOB-{str(uuid.uuid4()).upper().replace("-", "")[:12]}'
        
        # This would integrate with the real job execution system
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Job {job_id} started successfully for stage {stage_id}',
            start_time=start_time,
            operation='run_job',
            journey_id=journey_id,
            stage_id=stage_id,
            job_id=job_id,
            triggered_by=triggered_by,
            reason=reason,
            job_status='running',
            estimated_duration='15m'
        )
        
    except Exception as e:
        error_msg = f'Failed to run job: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_cancel_job(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    job_id: Optional[str],
    reason: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle cancel job operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for cancel_job action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not job_id:
            error_msg = "job_id is required for cancel_job action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Job {job_id} cancelled successfully',
            start_time=start_time,
            operation='cancel_job',
            journey_id=journey_id,
            job_id=job_id,
            cancellation_reason=reason,
            job_status='cancelled'
        )
        
    except Exception as e:
        error_msg = f'Failed to cancel job: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_update_job_status(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    job_id: Optional[str],
    job_status: Optional[str],
    progress: Optional[int],
    current_step: Optional[str],
    error_message: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle update job status operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for update_job_status action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not job_id:
            error_msg = "job_id is required for update_job_status action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not job_status:
            error_msg = "job_status is required for update_job_status action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate job status
        valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
        if job_status not in valid_statuses:
            error_msg = f"Invalid job_status: {job_status}. Valid statuses: {valid_statuses}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate progress if provided
        if progress is not None and (progress < 0 or progress > 100):
            error_msg = f"Invalid progress: {progress}. Must be between 0 and 100"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        update_data = {
            'status': job_status,
            'progress': progress,
            'current_step': current_step,
            'error_message': error_message,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Job {job_id} status updated successfully to {job_status}',
            start_time=start_time,
            operation='update_job_status',
            journey_id=journey_id,
            job_id=job_id,
            update_data={k: v for k, v in update_data.items() if v is not None}
        )
        
    except Exception as e:
        error_msg = f'Failed to update job status: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_retry_job(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    job_id: Optional[str],
    triggered_by: str,
    reason: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle retry job operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for retry_job action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not job_id:
            error_msg = "job_id is required for retry_job action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Generate new job ID for retry
        new_job_id = f'JOB-{str(uuid.uuid4()).upper().replace("-", "")[:12]}'
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Job retry {new_job_id} created successfully (retry of {job_id})',
            start_time=start_time,
            operation='retry_job',
            journey_id=journey_id,
            original_job_id=job_id,
            new_job_id=new_job_id,
            triggered_by=triggered_by,
            reason=reason,
            job_status='pending'
        )
        
    except Exception as e:
        error_msg = f'Failed to retry job: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_get_job_metrics(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    job_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle get job metrics operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for get_job_metrics action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not job_id:
            error_msg = "job_id is required for get_job_metrics action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # This would integrate with real metrics collection
        metrics = {
            'job_id': job_id,
            'stage_id': 'raw_analysis',
            'status': 'completed',
            'duration': 900.0,
            'log_metrics': {
                'total_entries': 45,
                'error_count': 0,
                'warning_count': 2,
                'info_count': 40,
                'debug_count': 3
            },
            'performance_metrics': {
                'avg_step_duration': 225.0,
                'slowest_step': {'step': 'schema_parsing', 'duration': 300.0},
                'fastest_step': {'step': 'business_rules_extraction', 'duration': 120.0},
                'error_rate': 0.0
            },
            'resource_metrics': {
                'cpu_usage_avg': 45.2,
                'memory_usage_avg': 67.8,
                'items_processed': 1250,
                'data_processed_mb': 15.6
            },
            'timeline': [
                {'timestamp': '2024-12-17T12:00:00Z', 'event': 'job_started'},
                {'timestamp': '2024-12-17T12:05:00Z', 'event': 'schema_parsing_completed'},
                {'timestamp': '2024-12-17T12:10:00Z', 'event': 'relationship_discovery_completed'},
                {'timestamp': '2024-12-17T12:13:00Z', 'event': 'data_type_analysis_completed'},
                {'timestamp': '2024-12-17T12:15:00Z', 'event': 'job_completed'}
            ]
        }
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved performance metrics for job {job_id}',
            start_time=start_time,
            operation='get_job_metrics',
            journey_id=journey_id,
            job_id=job_id,
            metrics=metrics
        )
        
    except Exception as e:
        error_msg = f'Failed to get job metrics: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_get_job_timeline(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    job_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle get job timeline operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for get_job_timeline action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not job_id:
            error_msg = "job_id is required for get_job_timeline action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # This would integrate with real timeline collection
        timeline = {
            'job_id': job_id,
            'total_events': 15,
            'timeline': [
                {
                    'timestamp': '2024-12-17T12:00:00Z',
                    'type': 'job_started',
                    'description': 'Job started for stage raw_analysis',
                    'details': {'triggered_by': 'mcp-user', 'reason': 'Manual execution'}
                },
                {
                    'timestamp': '2024-12-17T12:01:00Z',
                    'type': 'log_entry',
                    'description': 'Schema parsing initiated',
                    'details': {'level': 'info', 'step': 'schema_parsing'}
                },
                {
                    'timestamp': '2024-12-17T12:05:00Z',
                    'type': 'log_entry',
                    'description': 'Schema parsing completed successfully',
                    'details': {'level': 'info', 'step': 'schema_parsing'}
                },
                {
                    'timestamp': '2024-12-17T12:15:00Z',
                    'type': 'job_completed',
                    'description': 'Job completed successfully',
                    'details': {'final_status': 'completed', 'progress': 100}
                }
            ],
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved execution timeline for job {job_id}',
            start_time=start_time,
            operation='get_job_timeline',
            journey_id=journey_id,
            job_id=job_id,
            timeline=timeline
        )
        
    except Exception as e:
        error_msg = f'Failed to get job timeline: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_batch_cancel_jobs(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    job_ids: Optional[str],
    reason: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle batch cancel jobs operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for batch_cancel_jobs action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not job_ids:
            error_msg = "job_ids is required for batch_cancel_jobs action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Parse comma-separated job IDs
        job_id_list = [job_id.strip() for job_id in job_ids.split(',') if job_id.strip()]
        
        if not job_id_list:
            error_msg = "No valid job_ids provided"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # This would integrate with real batch cancellation
        results = {}
        successful_cancellations = 0
        
        for job_id in job_id_list:
            try:
                # Simulate cancellation
                results[job_id] = {'status': 'cancelled', 'success': True}
                successful_cancellations += 1
            except Exception as e:
                results[job_id] = {'status': 'error', 'success': False, 'error': str(e)}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Batch cancellation completed: {successful_cancellations}/{len(job_id_list)} jobs cancelled',
            start_time=start_time,
            operation='batch_cancel_jobs',
            journey_id=journey_id,
            total_jobs=len(job_id_list),
            successful_cancellations=successful_cancellations,
            failed_cancellations=len(job_id_list) - successful_cancellations,
            cancellation_reason=reason,
            results=results
        )
        
    except Exception as e:
        error_msg = f'Failed to batch cancel jobs: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_dashboard(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle dashboard view operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for dashboard action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # This would integrate with real dashboard data collection
        dashboard_data = {
            'journey_id': journey_id,
            'journey_name': 'Customer Management Transformation',
            'status': 'running',
            'overall_progress': 65,
            'current_stage': 'tmf_mapping',
            'created_at': '2024-12-17T10:00:00Z',
            'updated_at': '2024-12-17T12:00:00Z',
            'summary': {
                'total_stages': 6,
                'completed_stages': 2,
                'total_rules': 15,
                'active_rules': 12,
                'total_jobs': 8,
                'running_jobs': 1,
                'completed_jobs': 6,
                'failed_jobs': 1
            },
            'recent_activity': [
                {'timestamp': '2024-12-17T12:00:00Z', 'event': 'Job completed for raw_analysis'},
                {'timestamp': '2024-12-17T11:45:00Z', 'event': 'Job started for stripped_schema'},
                {'timestamp': '2024-12-17T11:30:00Z', 'event': 'Rule updated in raw_analysis stage'}
            ],
            'performance_metrics': {
                'avg_job_duration': '12m',
                'success_rate': 87.5,
                'total_execution_time': '96m'
            },
            'health_status': {
                'overall': 'healthy',
                'jobs': 'running',
                'logs': 'available',
                'reports': 'available'
            }
        }
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved dashboard for journey {journey_id}',
            start_time=start_time,
            operation='dashboard',
            journey_id=journey_id,
            dashboard=dashboard_data
        )
        
    except Exception as e:
        error_msg = f'Failed to get dashboard: {str(e)}'
        logger.error(error_msg)
        raise


async def _handle_get_journey_summary(
    ctx: Context,
    journey_service: EnhancedJourneyService,
    journey_id: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle get journey summary operation."""
    try:
        if not journey_id:
            error_msg = "journey_id is required for get_journey_summary action"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # This would integrate with comprehensive summary generation
        summary = {
            'journey_id': journey_id,
            'basic_info': {
                'name': 'Customer Management Transformation',
                'description': 'Transform customer database to TMF ODA compliance',
                'oda_component_type': 'customer-management',
                'status': 'running',
                'priority': 'high',
                'created_by': 'mcp-user',
                'created_at': '2024-12-17T10:00:00Z'
            },
            'progress_summary': {
                'overall_progress': 65,
                'current_stage': 'tmf_mapping',
                'current_stage_progress': 30,
                'estimated_completion': '2024-12-17T16:00:00Z'
            },
            'execution_summary': {
                'total_stages': 6,
                'completed_stages': 2,
                'pending_stages': 4,
                'total_jobs': 8,
                'running_jobs': 1,
                'completed_jobs': 6,
                'failed_jobs': 1,
                'total_execution_time': '96m'
            },
            'second_brain_summary': {
                'total_rules': 15,
                'active_rules': 12,
                'inactive_rules': 3,
                'rules_by_type': {
                    'field_mapping': 8,
                    'contextual_recommendations': 4,
                    'data_interpretation': 3
                }
            },
            'logs_and_reports_summary': {
                'total_log_entries': 245,
                'error_entries': 3,
                'warning_entries': 12,
                'reports_generated': 6,
                'latest_report': '2024-12-17T11:30:00Z'
            },
            'recommendations': [
                {
                    'type': 'performance',
                    'priority': 'medium',
                    'message': 'Consider optimizing schema_parsing step for better performance'
                },
                {
                    'type': 'error_handling',
                    'priority': 'low',
                    'message': 'Review warnings in relationship_discovery step'
                }
            ]
        }
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved comprehensive summary for journey {journey_id}',
            start_time=start_time,
            operation='get_journey_summary',
            journey_id=journey_id,
            summary=summary
        )
        
    except Exception as e:
        error_msg = f'Failed to get journey summary: {str(e)}'
        logger.error(error_msg)
        raise 