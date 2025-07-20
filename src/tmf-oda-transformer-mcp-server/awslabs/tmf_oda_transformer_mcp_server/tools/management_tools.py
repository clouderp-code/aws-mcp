"""
Core Journey Management Tools for TMF ODA Transformer MCP Server.
Focused on journey, stage, and rule management with clean separation of concerns.

🚀 SEPARATION OF CONCERNS:
- This tool: Journey CRUD, stage management, rules management, essential job utilities
- 'run-jobs' tool: Job creation, execution, status, cancel, retry, list
- 'logs-and-reports' tool: Logs retrieval, search, reports generation, analysis
"""

import os
import sys
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Annotated
from pathlib import Path
from loguru import logger

# Configure logging to use the same log file as the server
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Create dedicated journey tools logger
TOOLS_LOG_FILE = LOG_DIR / f"journey_tools_{datetime.now().strftime('%Y-%m-%d')}.log"

class JourneyToolsLogger:
    """Dedicated logger for journey tools with file and console output."""
    
    def __init__(self):
        self.log_file = TOOLS_LOG_FILE
        
    def _write_to_file(self, level: str, message: str):
        """Write log entry to file."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} | {level} | JOURNEY_TOOLS | {message}\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
                f.flush()
        except Exception as e:
            print(f"Journey tools logging error: {e}")
    
    def info(self, message: str):
        print(f"[JOURNEY_TOOLS] {message}")
        self._write_to_file("INFO", message)
        
    def debug(self, message: str):
        print(f"[JOURNEY_TOOLS DEBUG] {message}")
        self._write_to_file("DEBUG", message)
        
    def error(self, message: str):
        print(f"[JOURNEY_TOOLS ERROR] {message}")
        self._write_to_file("ERROR", message)

# Create the tools logger instance
tools_logger = JourneyToolsLogger()

# Keep the original logger for compatibility but add our custom logger
# Add file handler if not already configured
try:
    log_file = LOG_DIR / f"mcp_server_{datetime.now().strftime('%Y-%m-%d')}.log"
    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
        rotation="100 MB",
        retention="30 days",
        catch=True,
        filter=lambda record: "management_tools" in record["module"]  # Only logs from this module
    )
except Exception:
    pass  # If logger already configured, continue

from .base import BaseToolMixin

# Import the simplified service
from ..services.simple_journey_service import SimpleJourneyService


class JourneyAction:
    """Journey action constants - Focused on core journey management."""
    # Core CRUD operations
    CREATE = 'create'
    READ = 'read'  
    UPDATE = 'update'
    DELETE = 'delete'
    LIST = 'list'
    
    # Stage management
    LIST_STAGES = 'list_stages'
    ADD_STAGE = 'add_stage'
    UPDATE_STAGE = 'update_stage'
    DELETE_STAGE = 'delete_stage'
    ADD_DEFAULT_STAGES = 'add_default_stages'
    
    # Rules management
    LIST_RULES = 'list_rules'
    ADD_RULE = 'add_rule'
    UPDATE_RULE = 'update_rule'
    DELETE_RULE = 'delete_rule'
    
    # Job management (only unique actions not in run-jobs tool)
    UPDATE_JOB_STATUS = 'update_job_status'
    GET_JOB_METRICS = 'get_job_metrics'
    GET_JOB_TIMELINE = 'get_job_timeline'
    BATCH_CANCEL_JOBS = 'batch_cancel_jobs'
    
    # Journey utilities
    EXPORT_COMPLETE = 'export_complete'
    IMPORT_COMPLETE = 'import_complete'
    DASHBOARD = 'dashboard'
    GET_JOURNEY_SUMMARY = 'get_journey_summary'
    CLEAN_ALL = 'clean_all'
    GET_COMPREHENSIVE = 'get_comprehensive'


async def journeys_tool(
    ctx,
    action: str = "read",
    journey_id: str = "",
    job_id: str = "",
    stage_id: str = "",
    rule_id: str = "",
    name: str = "",
    description: str = "",
    odaComponentType: str = "",
    journey_data: Optional[Dict[str, Any]] = None,
    stage_data: Optional[Dict[str, Any]] = None,
    rule_data: Optional[Dict[str, Any]] = None,
    job_data: Optional[Dict[str, Any]] = None,
    triggered_by: str = "mcp-user",
    reason: str = "MCP Server execution",
    job_status: str = "",
    progress: Optional[int] = None,
    current_step: str = "",
    error_message: str = "",
    step_name: str = "",
    log_level: str = "",
    log_message: str = "",
    search_query: str = "",
    status_filter: str = "",
    rule_type: str = "",
    level_filter: str = "",
    step_filter: str = "",
    limit: int = 50,
    include_stages: bool = True,
    include_job_history: bool = True,
    include_all: bool = False,
    output_file: str = "",
    input_file: str = "",
    export_format: str = "json",
    job_ids: str = "",
    report_type: str = "",
    report_title: str = "",
) -> Dict[str, Any]:
    """
    Core journey management tool with clean separation of concerns.
    
    Focused on journey, stage, and rule management ONLY.
    For specialized operations, use dedicated tools:
    
    📋 Core Actions Supported:
    - Journey CRUD: create, read, update, delete, list
    - Stage Management: list_stages, add_stage, update_stage, delete_stage, add_default_stages  
    - Rules Management: list_rules, add_rule, update_rule, delete_rule
    - Job Utilities: update_job_status, get_job_metrics, get_job_timeline, batch_cancel_jobs
    - Journey Utilities: export_complete, import_complete, dashboard, get_journey_summary
    
    🚀 For Job Operations, Use:
    - run-jobs tool: job creation, execution, status, cancel, retry, list
    
    📊 For Logs & Reports, Use:
    - logs-and-reports tool: logs retrieval, search, reports generation, analysis
    """
    try:
        start_time = datetime.now()
        tools_logger.info(f"🚀 Starting journeys_tool action: {action}")
        
        # Add print statements for debugging
        print(f"=== JOURNEYS TOOL DEBUG ===")
        print(f"action: {action}")
        print(f"name: {name}")
        print(f"description: {description}")
        print(f"odaComponentType: {odaComponentType}")
        print(f"journey_data: {journey_data}")
        print(f"=== END JOURNEYS TOOL DEBUG ===")
        
        # Log key parameters only
        tools_logger.debug(f"Parameters: action={action}, name={name}, description={description}, odaComponentType={odaComponentType}")
        
        # Action mapping - Focused on core journey management
        action_map = {
            # Core CRUD operations
            'list': JourneyAction.LIST,
            'read': JourneyAction.READ,
            'create': JourneyAction.CREATE,
            'update': JourneyAction.UPDATE,
            'delete': JourneyAction.DELETE,
            
            # Stage management
            'list_stages': JourneyAction.LIST_STAGES,
            'add_stage': JourneyAction.ADD_STAGE,
            'update_stage': JourneyAction.UPDATE_STAGE,
            'delete_stage': JourneyAction.DELETE_STAGE,
            'add_default_stages': JourneyAction.ADD_DEFAULT_STAGES,
            
            # Rules management
            'list_rules': JourneyAction.LIST_RULES,
            'add_rule': JourneyAction.ADD_RULE,
            'update_rule': JourneyAction.UPDATE_RULE,
            'delete_rule': JourneyAction.DELETE_RULE,
            
            # Job management (only unique actions not in run-jobs tool)
            'update_job_status': JourneyAction.UPDATE_JOB_STATUS,
            'get_job_metrics': JourneyAction.GET_JOB_METRICS,
            'get_job_timeline': JourneyAction.GET_JOB_TIMELINE,
            'batch_cancel_jobs': JourneyAction.BATCH_CANCEL_JOBS,
            
            # Journey utilities
            'export_complete': JourneyAction.EXPORT_COMPLETE,
            'import_complete': JourneyAction.IMPORT_COMPLETE,
            'dashboard': JourneyAction.DASHBOARD,
            'get_journey_summary': JourneyAction.GET_JOURNEY_SUMMARY,
            'clean_all': JourneyAction.CLEAN_ALL,
            'get_comprehensive': JourneyAction.GET_COMPREHENSIVE
        }
        
        action = action_map.get(action.lower(), action.lower())
        
        # Create simplified journey service
        journey_service = SimpleJourneyService()
        
        # Route to appropriate operation based on action
        if action in [JourneyAction.LIST, JourneyAction.READ]:
            result = await _handle_journey_read(
                ctx, journey_service, journey_id, stage_id,
                include_stages, include_job_history, limit, start_time
            )
        elif action == JourneyAction.CREATE:
            # Debug logging to see what parameters we received
            tools_logger.debug(f"CREATE action: name='{name}', description='{description[:50]}...', odaComponentType='{odaComponentType}'")
            
            # Build journey_data from individual parameters if not provided
            if journey_data is None:
                journey_data = {}
            
            # Prioritize individual parameters over journey_data contents
            if name:
                journey_data['name'] = name
            if description:
                journey_data['description'] = description  
            if odaComponentType:
                journey_data['odaComponentType'] = odaComponentType
                
            # Add other non-empty parameters
            func_locals = locals()
            for param_name, param_value in func_locals.items():
                if param_name not in ['ctx', 'action', 'journey_service', 'start_time', 'journey_data', 'stage_data', 'rule_data', 'job_data', 'name', 'description', 'odaComponentType']:
                    if isinstance(param_value, str) and param_value:
                        journey_data[param_name] = param_value
                    elif isinstance(param_value, (int, bool, list, dict)) and param_value is not None:
                        journey_data[param_name] = param_value
            
            tools_logger.debug(f"Final journey_data keys: {list(journey_data.keys())}")
            
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
        elif action == JourneyAction.LIST_STAGES:
            result = await _handle_list_stages(
                ctx, journey_service, journey_id, start_time
            )
        elif action == JourneyAction.ADD_DEFAULT_STAGES:
            result = await _handle_add_default_stages(
                ctx, journey_service, journey_id, start_time
            )
        elif action == JourneyAction.LIST_RULES:
            result = await _handle_list_rules(
                ctx, journey_service, journey_id, stage_id, rule_type, 
                rule_data.get('priority') if rule_data else None, start_time
            )
        elif action == JourneyAction.ADD_RULE:
            result = await _handle_add_rule(
                ctx, journey_service, journey_id, stage_id, rule_data, start_time
            )
        elif action == JourneyAction.UPDATE_RULE:
            result = await _handle_update_rule(
                ctx, journey_service, journey_id, rule_id, rule_data, start_time
            )
        elif action == JourneyAction.DELETE_RULE:
            result = await _handle_delete_rule(
                ctx, journey_service, journey_id, rule_id, start_time
            )
        elif action == 'get_comprehensive':
            result = await _handle_get_comprehensive(
                ctx, journey_service, journey_id, start_time
            )
        elif action == 'clean_all':
            result = await _handle_clean_all_data(
                ctx, journey_service, start_time
            )
        else:
            # For now, other actions return a placeholder
            result = BaseToolMixin.create_tool_result(
                status='error',
                message=f'Action {action} not implemented in simplified version yet',
                start_time=start_time,
                operation=action,
                journey_id=journey_id
            )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in journeys_tool: {str(e)}")
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Tool execution failed: {str(e)}',
            start_time=datetime.now(),
            operation=action or 'unknown'
        )


# Essential handler functions
async def _handle_journey_read(
    ctx,
    journey_service,
    journey_id: Optional[str],
    stage_id: Optional[str],
    include_stages: bool,
    include_job_history: bool,
    limit: int,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey read/list operation."""
    try:
        if journey_id:
            # Get specific journey
            journey = await journey_service.get_journey(journey_id)
            if not journey:
                raise ValueError(f"Journey {journey_id} not found")
            
            result_data = {
                'journey': journey,
                'journey_id': journey_id,
                'include_stages': include_stages,
                'include_job_history': include_job_history
            }
            
            # Note: stages and job history will be implemented later
            if include_stages:
                result_data['stages'] = []  # TODO: Implement in SimpleJourneyService
            
            if include_job_history:
                result_data['job_history'] = []  # TODO: Implement in SimpleJourneyService
            
            return BaseToolMixin.create_tool_result(
                status='success',
                message=f'Retrieved journey {journey_id} details',
                start_time=start_time,
                operation='read_journey',
                **result_data
            )
        else:
            # List all journeys
            result = await journey_service.list_journeys(limit=limit)
            journeys = result.get('journeys', [])
            total_journeys = result.get('total_journeys', 0)
            
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
        logger.error(f'❌ Failed to read journey: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey read operation failed: {str(e)}',
            start_time=start_time,
            operation='read_journey',
            journey_id=journey_id
        )


async def _handle_journey_create(
    ctx,
    journey_service,
    journey_id: Optional[str],
    journey_data: Dict[str, Any],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey creation."""
    try:
        # Safety check to ensure journey_data is never None
        if journey_data is None:
            journey_data = {}
        
        # Clean debug logging
        tools_logger.debug(f"Creating journey with {len(journey_data)} parameters")
        tools_logger.info(f"🆕 Creating journey: {journey_data.get('name', 'Unnamed')}")
        
        # Validate required fields
        required_fields = ['name', 'description', 'odaComponentType']
        for field in required_fields:
            if field not in journey_data:
                error_msg = f'Missing required field: {field}'
                tools_logger.error(f'❌ {error_msg} (available: {list(journey_data.keys())})')
                return BaseToolMixin.create_tool_result(
                    status='error',
                    message=error_msg,
                    start_time=start_time,
                    operation='create_journey'
                )
        
        # Create journey using simplified service
        result = await journey_service.create_journey(journey_data)
        
        tools_logger.info(f'✅ Journey created successfully: {result.get("journeyId")}')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=result.get('message', f'Journey created successfully'),
            start_time=start_time,
            operation='create_journey',
            journey_id=result.get('journeyId'),
            journey_data=result
        )
        
    except Exception as e:
        tools_logger.error(f'❌ Failed to create journey: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey create operation failed: {str(e)}',
            start_time=start_time,
            operation='create_journey',
            journey_id=journey_id
        )


async def _handle_journey_update(
    ctx,
    journey_service,
    journey_id: str,
    journey_data: Dict[str, Any],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey update operation."""
    try:
        logger.info(f'🔄 Updating journey {journey_id} via SimpleJourneyService')
        
        # Use simplified service for update
        result = await journey_service.update_journey(journey_id, journey_data)
        
        logger.info(f'✅ Journey {journey_id} updated successfully via SimpleJourneyService')
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=result.get('message', f'Journey {journey_id} updated successfully'),
            start_time=start_time,
            operation='update_journey',
            journey_id=journey_id,
            updated_data=result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed to update journey {journey_id}: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey update operation failed: {str(e)}',
            start_time=start_time,
            operation='update_journey',
            journey_id=journey_id
        )


async def _handle_journey_delete(
    ctx,
    journey_service,
    journey_id: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle journey deletion operation."""
    try:
        logger.info(f'🗑️ Comprehensively deleting journey {journey_id} with all related records')
        
        # Use the comprehensive deletion method for complete cleanup
        result = await journey_service.delete_journey_comprehensive(journey_id)
        
        logger.info(f'✅ Journey {journey_id} comprehensively deleted: {result["deleted_items_count"]} items')
        
        # Remove standard parameters from result to avoid conflicts
        standard_params = {'status', 'message', 'start_time', 'operation', 'journey_id', 'timestamp', 'end_time', 'duration_seconds'}
        filtered_result = {k: v for k, v in result.items() if k not in standard_params}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=result.get('message', f'Journey {journey_id} and all related records deleted successfully'),
            start_time=start_time,
            operation='delete_journey',
            journey_id=journey_id,
            **filtered_result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed to delete journey {journey_id}: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Journey delete operation failed: {str(e)}',
            start_time=start_time,
            operation='delete_journey',
            journey_id=journey_id
        )


async def _handle_list_stages(
    ctx,
    journey_service,
    journey_id: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle listing stages with rules and jobs for a journey."""
    try:
        logger.info(f'📋 Listing stages with rules and jobs for journey {journey_id}')
        
        result = await journey_service.list_journey_stages(journey_id)
        
        logger.info(f'✅ Found {result["total_stages"]} stages, {result["total_rules"]} rules, {result["total_jobs"]} jobs')
        
        # Remove standard parameters from result to avoid conflicts
        standard_params = {'status', 'message', 'start_time', 'operation', 'journey_id', 'timestamp', 'end_time', 'duration_seconds'}
        filtered_result = {k: v for k, v in result.items() if k not in standard_params}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved {result["total_stages"]} stages with {result["total_rules"]} rules and {result["total_jobs"]} jobs',
            start_time=start_time,
            operation='list_stages',
            journey_id=journey_id,
            **filtered_result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed to list stages for journey {journey_id}: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'List stages operation failed: {str(e)}',
            start_time=start_time,
            operation='list_stages',
            journey_id=journey_id
        )


async def _handle_get_comprehensive(
    ctx,
    journey_service,
    journey_id: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle getting comprehensive journey data including all related records."""
    try:
        logger.info(f'🔍 Getting comprehensive data for journey {journey_id}')
        
        result = await journey_service.get_journey_comprehensive(journey_id)
        
        summary = result['summary']
        logger.info(f'✅ Retrieved comprehensive data: {summary["total_stages"]} stages, {summary["total_rules"]} rules, {summary["total_jobs"]} jobs')
        
        # Remove standard parameters from result to avoid conflicts
        standard_params = {'status', 'message', 'start_time', 'operation', 'journey_id', 'timestamp', 'end_time', 'duration_seconds'}
        filtered_result = {k: v for k, v in result.items() if k not in standard_params}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved comprehensive journey data with {summary["total_stages"]} stages, {summary["total_rules"]} rules, and {summary["total_jobs"]} jobs',
            start_time=start_time,
            operation='get_comprehensive',
            journey_id=journey_id,
            **filtered_result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed to get comprehensive data for journey {journey_id}: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Get comprehensive operation failed: {str(e)}',
            start_time=start_time,
            operation='get_comprehensive',
            journey_id=journey_id
        )


async def _handle_clean_all_data(
    ctx,
    journey_service,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle comprehensive cleanup of ALL journey data."""
    try:
        logger.info('🧹 Starting comprehensive cleanup of ALL journey data')
        
        result = await journey_service.clean_all_journey_data()
        
        logger.info(f'🎉 Cleanup completed: {result["cleaned_journeys"]} journeys, {result["total_items_deleted"]} total items')
        
        # Remove standard parameters from result to avoid conflicts
        standard_params = {'status', 'message', 'start_time', 'operation', 'journey_id', 'timestamp', 'end_time', 'duration_seconds'}
        filtered_result = {k: v for k, v in result.items() if k not in standard_params}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Successfully cleaned {result["cleaned_journeys"]} journeys with {result["total_items_deleted"]} total items',
            start_time=start_time,
            operation='clean_all_data',
            **filtered_result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed comprehensive cleanup: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Comprehensive cleanup failed: {str(e)}',
            start_time=start_time,
            operation='clean_all_data'
        )


async def _handle_add_default_stages(
    ctx,
    journey_service,
    journey_id: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle adding default transformation stages to a journey."""
    try:
        logger.info(f'🏗️ Adding default stages to journey {journey_id}')
        
        result = await journey_service.add_default_stages(journey_id)
        
        logger.info(f'✅ Added {result["stages_added"]} default stages to journey {journey_id}')
        
        # Remove standard parameters from result to avoid conflicts
        standard_params = {'status', 'message', 'start_time', 'operation', 'journey_id', 'timestamp', 'end_time', 'duration_seconds'}
        filtered_result = {k: v for k, v in result.items() if k not in standard_params}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=result.get('message', f'Added {result["stages_added"]} default stages to journey {journey_id}'),
            start_time=start_time,
            operation='add_default_stages',
            journey_id=journey_id,
            **filtered_result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed to add default stages to journey {journey_id}: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Add default stages operation failed: {str(e)}',
            start_time=start_time,
            operation='add_default_stages',
            journey_id=journey_id
        )


async def _handle_list_rules(
    ctx,
    journey_service,
    journey_id: str,
    stage_id: Optional[str],
    rule_type: Optional[str],
    priority: Optional[str],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle listing Second Brain rules for a journey."""
    try:
        logger.info(f'📋 Listing rules for journey {journey_id}')
        
        result = await journey_service.list_rules(
            journey_id, 
            stage_id=stage_id, 
            rule_type=rule_type, 
            priority=priority
        )
        
        logger.info(f'✅ Found {result["total_rules"]} rules for journey {journey_id}')
        
        # Remove standard parameters from result to avoid conflicts
        standard_params = {'status', 'message', 'start_time', 'operation', 'journey_id', 'timestamp', 'end_time', 'duration_seconds'}
        filtered_result = {k: v for k, v in result.items() if k not in standard_params}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=f'Retrieved {result["total_rules"]} rules for journey {journey_id}',
            start_time=start_time,
            operation='list_rules',
            journey_id=journey_id,
            **filtered_result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed to list rules for journey {journey_id}: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'List rules operation failed: {str(e)}',
            start_time=start_time,
            operation='list_rules',
            journey_id=journey_id
        )


async def _handle_add_rule(
    ctx,
    journey_service,
    journey_id: str,
    stage_id: str,
    rule_data: Dict[str, Any],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle adding a Second Brain rule to a journey."""
    try:
        logger.info(f'➕ Adding rule to journey {journey_id}, stage {stage_id}')
        
        if not stage_id:
            raise ValueError('stage_id is required for add_rule operation')
        
        if not rule_data:
            raise ValueError('rule_data is required for add_rule operation')
        
        result = await journey_service.add_rule(journey_id, stage_id, rule_data)
        
        logger.info(f'✅ Added rule {result["rule_id"]} to journey {journey_id}')
        
        # Remove standard parameters from result to avoid conflicts
        standard_params = {'status', 'message', 'start_time', 'operation', 'journey_id', 'timestamp', 'end_time', 'duration_seconds'}
        filtered_result = {k: v for k, v in result.items() if k not in standard_params}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=result.get('message', f'Rule {result["rule_id"]} added successfully'),
            start_time=start_time,
            operation='add_rule',
            journey_id=journey_id,
            **filtered_result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed to add rule to journey {journey_id}: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Add rule operation failed: {str(e)}',
            start_time=start_time,
            operation='add_rule',
            journey_id=journey_id
        )


async def _handle_update_rule(
    ctx,
    journey_service,
    journey_id: str,
    rule_id: str,
    rule_data: Dict[str, Any],
    start_time: datetime
) -> Dict[str, Any]:
    """Handle updating a Second Brain rule."""
    try:
        logger.info(f'✏️ Updating rule {rule_id} for journey {journey_id}')
        
        if not rule_id:
            raise ValueError('rule_id is required for update_rule operation')
        
        if not rule_data:
            raise ValueError('rule_data is required for update_rule operation')
        
        result = await journey_service.update_rule(journey_id, rule_id, rule_data)
        
        logger.info(f'✅ Updated rule {rule_id} for journey {journey_id}')
        
        # Remove standard parameters from result to avoid conflicts
        standard_params = {'status', 'message', 'start_time', 'operation', 'journey_id', 'timestamp', 'end_time', 'duration_seconds'}
        filtered_result = {k: v for k, v in result.items() if k not in standard_params}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=result.get('message', f'Rule {rule_id} updated successfully'),
            start_time=start_time,
            operation='update_rule',
            journey_id=journey_id,
            **filtered_result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed to update rule {rule_id}: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Update rule operation failed: {str(e)}',
            start_time=start_time,
            operation='update_rule',
            journey_id=journey_id,
            rule_id=rule_id
        )


async def _handle_delete_rule(
    ctx,
    journey_service,
    journey_id: str,
    rule_id: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Handle deleting a Second Brain rule."""
    try:
        logger.info(f'🗑️ Deleting rule {rule_id} from journey {journey_id}')
        
        if not rule_id:
            raise ValueError('rule_id is required for delete_rule operation')
        
        result = await journey_service.delete_rule(journey_id, rule_id)
        
        logger.info(f'✅ Deleted rule {rule_id} from journey {journey_id}')
        
        # Remove standard parameters from result to avoid conflicts
        standard_params = {'status', 'message', 'start_time', 'operation', 'journey_id', 'timestamp', 'end_time', 'duration_seconds'}
        filtered_result = {k: v for k, v in result.items() if k not in standard_params}
        
        return BaseToolMixin.create_tool_result(
            status='success',
            message=result.get('message', f'Rule {rule_id} deleted successfully'),
            start_time=start_time,
            operation='delete_rule',
            journey_id=journey_id,
            **filtered_result
        )
        
    except Exception as e:
        logger.error(f'❌ Failed to delete rule {rule_id}: {str(e)}')
        return BaseToolMixin.create_tool_result(
            status='error',
            message=f'Delete rule operation failed: {str(e)}',
            start_time=start_time,
            operation='delete_rule',
            journey_id=journey_id,
            rule_id=rule_id
        ) 