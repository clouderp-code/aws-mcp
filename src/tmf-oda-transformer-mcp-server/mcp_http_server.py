#!/usr/bin/env python3
"""
MCP HTTP Transport Server for TMF ODA Transformer
This implements the proper MCP HTTP transport protocol for Cursor compatibility.
"""

import asyncio
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import traceback
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
import logging
import argparse
from loguru import logger

# Add the MCP server to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Parse command-line arguments
parser = argparse.ArgumentParser(description="TMF ODA Transformer MCP HTTP Server")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
args = parser.parse_args()

# Configure logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Set log level based on debug flag
LOG_LEVEL = "DEBUG" if args.debug else "INFO"

# Configure loguru for both console and file output
logger.remove()  # Remove default handler

# Add console handler
logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format="{time:HH:mm:ss} | {level} | SERVER | {module}:{function} | {message}",
    colorize=True,
    catch=True
)

# Add server log file handler
server_log_file = LOG_DIR / f"server_{datetime.now().strftime('%Y-%m-%d')}.log"
logger.add(
    server_log_file,
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | SERVER | {module}:{function}:{line} | {message}",
    rotation="100 MB",
    retention="30 days",
    catch=True
)

# Create a separate dual logger for server operations  
class DualLogger:
    def __init__(self):
        self.server_log = LOG_DIR / f"server_{datetime.now().strftime('%Y-%m-%d')}.log"
        
    def _write_to_file(self, level: str, message: str):
        """Write to server log file."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} | {level} | SERVER | {message}\n"
            with open(self.server_log, "a", encoding="utf-8") as f:
                f.write(log_entry)
                f.flush()
        except Exception as e:
            print(f"Server logging error: {e}")
        
    def info(self, message: str):
        print(f"[SERVER] {message}")
        logger.info(message)
        self._write_to_file("INFO", message)
        
    def debug(self, message: str):
        if LOG_LEVEL == "DEBUG":
            print(f"[SERVER DEBUG] {message}")
        logger.debug(message)
        self._write_to_file("DEBUG", message)
        
    def error(self, message: str):
        print(f"[SERVER ERROR] {message}")
        logger.error(message)
        self._write_to_file("ERROR", message)

dual_logger = DualLogger()

# Also configure Python's logging to capture uvicorn and other HTTP errors
import logging
logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "uvicorn.log"),
        logging.StreamHandler()
    ]
)

dual_logger.info("=== MCP HTTP Server Starting ===")
dual_logger.info(f"Log directory: {LOG_DIR}")
dual_logger.info(f"Log files will be rotated daily and kept for 7 days")

# Import MCP server and tools directly
try:
    from awslabs.tmf_oda_transformer_mcp_server.server import (
        mcp,
        raw_analysis_tool,
        stripped_schema_tool,
        get_job_logs_tool,
        test_runner_tool,
        journeys_tool,
        run_jobs_tool
    )
    from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool
    print("✅ MCP server and tools imported successfully")
except ImportError as e:
    print(f"❌ Error importing MCP server: {e}")
    traceback.print_exc()
    sys.exit(1)

# FastAPI app
app = FastAPI(
    title="TMF ODA Transformer MCP HTTP Transport",
    description="MCP HTTP transport server for TMF ODA transformation tools",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    start_time = datetime.now()
    
    # Log incoming request
    dual_logger.info(f"📥 HTTP Request: {request.method} {request.url}")
    dual_logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Process request
    try:
        response = await call_next(request)
        
        # Log successful response
        duration = (datetime.now() - start_time).total_seconds()
        dual_logger.info(f"📤 HTTP Response: {response.status_code} ({duration:.3f}s)")
        
        return response
        
    except Exception as e:
        # Log error response
        duration = (datetime.now() - start_time).total_seconds()
        dual_logger.error(f"❌ HTTP Request failed: {request.method} {request.url} ({duration:.3f}s)")
        logger.error(f"Exception: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        raise

# Store server state
server_state = {
    "initialized": False,
    "session_id": None,
    "client_info": None
}

# Tool registry with direct function references
TOOLS = {
    "raw-analysis": {
        "func": raw_analysis_tool,
        "description": "Execute raw analysis stage of transformation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journey_id": {"type": "string", "description": "Journey ID", "default": "JRN-DEMO-001"},
                "stage_id": {"type": "string", "description": "Stage ID", "default": "raw_analysis", "enum": ["raw_analysis", "stripped_schema", "data_mapping", "compliance_validation"]},
                "triggered_by": {"type": "string", "description": "Who triggered this", "default": "mcp-server"},
                "reason": {"type": "string", "description": "Reason for execution", "default": "MCP Server execution"}
            },
            "required": ["journey_id"]
        }
    },
    "stripped-schema": {
        "func": stripped_schema_tool,
        "description": "Execute stripped schema stage of transformation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journey_id": {"type": "string", "description": "Journey ID", "default": "JRN-DEMO-001"},
                "stage_id": {"type": "string", "description": "Stage ID", "default": "stripped_schema", "enum": ["raw_analysis", "stripped_schema", "data_mapping", "compliance_validation"]},
                "triggered_by": {"type": "string", "description": "Who triggered this", "default": "mcp-server"},
                "reason": {"type": "string", "description": "Reason for execution", "default": "MCP Server execution"}
            },
            "required": ["journey_id"]
        }
    },
    "get-job-logs": {
        "func": get_job_logs_tool,
        "description": "Retrieve job execution logs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journey_id": {"type": "string", "description": "Journey ID", "default": "JRN-DEMO-001"},
                "stage_name": {"type": "string", "description": "Stage name", "default": "raw_analysis"},
                "job_id": {"type": "string", "description": "Job ID", "default": "JOB-001-20240101120000"},
                "step_name": {"type": "string", "description": "Step name", "default": "schema_parsing"}
            },
            "required": ["journey_id", "stage_name", "job_id", "step_name"]
        }
    },
    "test-runner": {
        "func": test_runner_tool,
        "description": "Run comprehensive tool verification tests",
        "inputSchema": {
            "type": "object",
            "properties": {
                "test_type": {"type": "string", "description": "Type of tests to run", "enum": ["quick", "comprehensive", "imports"]},
                "include_performance": {"type": "boolean", "description": "Include performance tests"}
            },
            "required": []
        }
    },
    "journeys": {
        "func": journeys_tool,
        "description": "Core journey management (CRUD, stages, rules). For jobs use 'run-jobs', for logs/reports use 'logs-and-reports'",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": [
                        "read", "list", "create", "update", "delete",
                        "list_stages", "add_stage", "update_stage", "delete_stage", "add_default_stages",
                        "list_rules", "add_rule", "update_rule", "delete_rule",
                        "update_job_status", "get_job_metrics", "get_job_timeline", "batch_cancel_jobs",
                        "export_complete", "import_complete", "dashboard", "get_journey_summary",
                        "clean_all", "get_comprehensive"
                    ],
                    "default": "read"
                },
                "journey_id": {"type": "string", "description": "Journey ID for operations", "default": ""},
                "job_id": {"type": "string", "description": "Job ID for job-related operations", "default": ""},
                "stage_id": {"type": "string", "description": "Stage ID for stage/job operations", "default": ""},
                "rule_id": {"type": "string", "description": "Rule ID for rule operations", "default": ""},
                "journey_data": {"type": "object", "description": "Journey data for create/update operations (can include 'include_default_stages': true)", "default": None},
                "stage_data": {"type": "object", "description": "Stage data for stage operations", "default": None},
                "rule_data": {"type": "object", "description": "Rule data for rule operations", "default": None},
                "job_data": {"type": "object", "description": "Job data for job operations", "default": None},
                "triggered_by": {"type": "string", "description": "Who triggered the job execution", "default": "mcp-user"},
                "reason": {"type": "string", "description": "Reason for job execution", "default": "MCP Server execution"},
                "job_status": {"type": "string", "description": "Job status for updates", "enum": ["pending", "running", "completed", "failed", "cancelled"], "default": ""},
                "progress": {"type": "integer", "description": "Job progress percentage (0-100)", "default": None},
                "current_step": {"type": "string", "description": "Current step for job updates", "default": ""},
                "error_message": {"type": "string", "description": "Error message for failed jobs", "default": ""},
                "step_name": {"type": "string", "description": "Step name for log operations", "default": ""},
                "log_level": {"type": "string", "description": "Log level", "enum": ["error", "warning", "info", "debug"], "default": ""},
                "log_message": {"type": "string", "description": "Log message content", "default": ""},
                "search_query": {"type": "string", "description": "Search query for log search", "default": ""},
                "status_filter": {"type": "string", "description": "Filter by status", "default": ""},
                "rule_type": {"type": "string", "description": "Filter by rule type", "default": ""},
                "level_filter": {"type": "string", "description": "Filter by log level", "default": ""},
                "step_filter": {"type": "string", "description": "Filter by step name", "default": ""},
                "limit": {"type": "integer", "description": "Maximum results to return", "default": 50},
                "include_stages": {"type": "boolean", "description": "Include stage details", "default": True},
                "include_job_history": {"type": "boolean", "description": "Include job history", "default": True},
                "include_all": {"type": "boolean", "description": "Include all available details", "default": False},
                "output_file": {"type": "string", "description": "Output file path for export", "default": ""},
                "input_file": {"type": "string", "description": "Input file path for import", "default": ""},
                "export_format": {"type": "string", "description": "Export format", "enum": ["json", "csv", "txt"], "default": "json"},
                "job_ids": {"type": "string", "description": "Comma-separated job IDs for batch operations", "default": ""},
                "report_type": {"type": "string", "description": "Type of report to create", "default": ""},
                "report_title": {"type": "string", "description": "Title for generated reports", "default": ""}
            },
            "required": []
        }
    },
    "run-jobs": {
        "func": run_jobs_tool,
        "description": "Enhanced job lifecycle management for transformation stages (create, run, status, get, cancel, retry, list)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journey_id": {"type": "string", "description": "Journey ID", "default": "JRN-DEMO-001"},
                "stage_id": {
                    "type": "string", 
                    "description": "Stage ID to execute", 
                    "default": "raw_analysis", 
                    "enum": ["raw_analysis", "stripped_schema", "tmf_mapping", "migration_planning", "data_migration", "verification_validation"]
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform on the job",
                    "default": "run",
                    "enum": ["run", "create", "status", "cancel", "retry", "list", "get"]
                },
                "job_id": {"type": "string", "description": "Job ID for status/cancel/retry/get operations", "default": ""},
                "triggered_by": {"type": "string", "description": "Who triggered this", "default": "mcp-server"},
                "reason": {"type": "string", "description": "Reason for execution", "default": "MCP Server execution"},
                "job_config": {"type": "object", "description": "Optional job configuration parameters", "default": None},
                "wait_for_completion": {"type": "boolean", "description": "Wait for job completion", "default": True},
                "progress_callback": {"type": "boolean", "description": "Include real-time progress updates", "default": False}
            },
            "required": ["journey_id"]
        }
    },
    "logs-and-reports": {
        "func": logs_and_reports_tool,
        "description": "Comprehensive logs and reports management with search, filter, export, and analysis capabilities",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string", 
                    "description": "Action to perform",
                    "enum": [
                        "get_job_logs", "add_log_entry", "search_logs", "get_logs_by_level",
                        "export_job_logs", "get_error_summary", "list_available_logs",
                        "get_job_reports", "create_job_report", "generate_summary_report",
                        "generate_performance_report", "generate_error_analysis_report",
                        "list_available_reports", "export_reports", "analyze_job_performance",
                        "analyze_error_patterns", "generate_insights", "get_recommendations"
                    ],
                    "default": "get_job_logs"
                },
                "journey_id": {"type": "string", "description": "Journey ID", "default": ""},
                "job_id": {"type": "string", "description": "Job ID", "default": ""},
                "stage_name": {"type": "string", "description": "Stage name", "default": ""},
                "step_name": {"type": "string", "description": "Step name", "default": ""},
                "log_level": {"type": "string", "description": "Log level", "enum": ["error", "warning", "info", "debug"], "default": ""},
                "log_message": {"type": "string", "description": "Log message content", "default": ""},
                "log_details": {"type": "object", "description": "Additional log details (JSON object)", "default": {}},
                "log_source": {"type": "string", "description": "Log source identifier", "default": "mcp-server"},
                "search_query": {"type": "string", "description": "Search query", "default": ""},
                "level_filter": {"type": "string", "description": "Filter by log level", "default": ""},
                "step_filter": {"type": "string", "description": "Filter by step name", "default": ""},
                "time_from": {"type": "string", "description": "Filter logs from timestamp (ISO format)", "default": ""},
                "time_to": {"type": "string", "description": "Filter logs to timestamp (ISO format)", "default": ""},
                "report_type": {"type": "string", "description": "Type of report (summary, performance, error_analysis, custom)", "default": ""},
                "report_title": {"type": "string", "description": "Title for generated reports", "default": ""},
                "report_content": {"type": "object", "description": "Custom report content (JSON object)", "default": {}},
                "output_file": {"type": "string", "description": "Output file path for export operations", "default": ""},
                "export_format": {"type": "string", "description": "Export format", "enum": ["json", "csv", "txt", "html"], "default": "json"},
                "limit": {"type": "integer", "description": "Maximum results", "default": 100},
                "offset": {"type": "integer", "description": "Number of results to skip (pagination)", "default": 0},
                "include_details": {"type": "boolean", "description": "Include detailed information in results", "default": True},
                "analysis_period": {"type": "string", "description": "Analysis period (24h, 7d, 30d, all)", "default": "24h"},
                "include_recommendations": {"type": "boolean", "description": "Include recommendations in analysis", "default": True}
            },
            "required": []
        }
    }
}

class MCPContext:
    """MCP context for tool execution."""
    def __init__(self):
        self.errors = []
    
    async def error(self, message: str):
        """Handle error messages."""
        self.errors.append(message)
        print(f"MCP Error: {message}")

# Global context
ctx = MCPContext()

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "service": "TMF ODA Transformer MCP HTTP Transport",
        "version": "1.0.0",
        "protocol": "mcp",
        "transport": "http",
        "status": "running",
        "mcp_version": "2024-11-05",
        "tools_count": len(TOOLS),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/")
async def handle_root_mcp(request: Request):
    """Handle MCP requests at root path (some clients expect this)."""
    try:
        data = await request.json()
        method = data.get("method", "")
        
        # Route to appropriate MCP endpoint
        if method == "initialize":
            return await initialize_server(request)
        elif method == "tools/list":
            return await list_tools(request)
        elif method == "tools/call":
            return await call_tool(request)
        elif method == "ping":
            return await ping_server(request)
        else:
            return {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    except Exception as e:
        print(f"Error handling root MCP request: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
        )

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mcp_server": "running",
        "initialized": server_state["initialized"],
        "tools_available": len(TOOLS),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/mcp/server/initialize")
async def initialize_server(request: Request):
    """Initialize MCP server."""
    try:
        data = await request.json()
        
        # Extract client info
        client_info = data.get("params", {}).get("clientInfo", {})
        protocol_version = data.get("params", {}).get("protocolVersion", "2024-11-05")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Update server state
        server_state.update({
            "initialized": True,
            "session_id": session_id,
            "client_info": client_info
        })
        
        print(f"✅ MCP server initialized for client: {client_info.get('name', 'Unknown')}")
        
        # Return initialization response
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {
                "protocolVersion": protocol_version,
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    }
                },
                "serverInfo": {
                    "name": "TMF ODA Transformer MCP Server",
                    "version": "1.0.0"
                },
                "instructions": """
# TMF ODA Transformer MCP Server

Provides tools for TMF ODA (TM Forum Open Digital Architecture) transformation and journey management.

Available tools:
- raw-analysis: Execute raw analysis stage of transformation
- stripped-schema: Execute stripped schema stage of transformation
- get-job-logs: Retrieve job execution logs
- test-runner: Run comprehensive tool verification tests
- journeys: Comprehensive journey management with CRUD operations
- run-jobs: Execute any transformation stage
                """
            }
        }
        
    except Exception as e:
        print(f"Error initializing server: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/server/ping")
async def ping_server(request: Request):
    """Handle ping requests."""
    try:
        data = await request.json()
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/list")
async def list_tools(request: Request):
    """List available MCP tools."""
    try:
        data = await request.json()
        
        # Build tools list from our registry
        tools = []
        for tool_name, tool_info in TOOLS.items():
            tool_data = {
                "name": tool_name,
                "description": tool_info["description"],
                "inputSchema": tool_info["inputSchema"]
            }
            tools.append(tool_data)
        
        return {
            "jsonrpc": "2.0", 
            "id": data.get("id"),
            "result": {
                "tools": tools
            }
        }
        
    except Exception as e:
        print(f"Error listing tools: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    """Call an MCP tool."""
    try:
        data = await request.json()
        params = data.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        # Get tool from registry
        tool_info = TOOLS.get(tool_name)
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Validate required parameters
        required_params = tool_info["inputSchema"].get("required", [])
        missing_required = [
            param for param in required_params if param not in arguments
        ]
        if missing_required:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required parameters for tool '{tool_name}': {', '.join(missing_required)}"
            )

        # Validate enum values for string properties
        for prop_name, prop_info in tool_info["inputSchema"]["properties"].items():
            if prop_info.get("type") == "string" and "enum" in prop_info:
                if prop_name in arguments and arguments[prop_name] not in prop_info["enum"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid value for parameter '{prop_name}' for tool '{tool_name}': must be one of {', '.join(prop_info['enum'])}"
                    )

        # Reset context errors
        ctx.errors = []
        
        # Log the tool call with detailed information
        logger.info(f"🔧 MCP Tool Call: {tool_name}")
        logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2, default=str)}")
        logger.debug(f"Tool info: {json.dumps(tool_info, indent=2, default=str)}")
        
        print(f"🔧 Calling tool: {tool_name} with arguments: {arguments}")
        
        # Call tool function
        try:
            tool_func = tool_info["func"]
            
            # Apply defaults for missing arguments
            schema_props = tool_info["inputSchema"]["properties"]
            final_args = {}
            
            for prop_name, prop_info in schema_props.items():
                if prop_name in arguments:
                    final_args[prop_name] = arguments[prop_name]
                elif "default" in prop_info:
                    final_args[prop_name] = prop_info["default"]
            
            result = await tool_func(ctx, **final_args)
            
            # Convert result to JSON-serializable format
            if hasattr(result, 'dict'):
                result_data = result.dict()
            elif hasattr(result, '__dict__'):
                result_data = result.__dict__
            else:
                result_data = result
            
            # Log the successful result
            logger.info(f"✅ Tool {tool_name} completed successfully")
            logger.debug(f"Tool result: {json.dumps(result_data, indent=2, default=str)}")
            
            return {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_data, indent=2, default=str)
                        }
                    ]
                }
            }
            
        except Exception as tool_error:
            # Return tool execution error
            error_msg = f"Tool execution failed: {str(tool_error)}"
            if ctx.errors:
                error_msg += f"\nContext errors: {'; '.join(ctx.errors)}"
            
            # Log the error with full details
            logger.error(f"❌ Tool {tool_name} execution failed: {error_msg}")
            logger.error(f"Exception details: {traceback.format_exc()}")
            
            print(f"❌ Tool execution error: {error_msg}")
            
            return {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {
                    "code": -32000,
                    "message": error_msg,
                    "data": {
                        "tool_name": tool_name,
                        "arguments": arguments
                    }
                }
            }
            
    except Exception as e:
        error_msg = f"HTTP Server error: {str(e)}"
        logger.error(f"❌ HTTP Server Exception: {error_msg}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        print(f"Error calling tool: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/server/info")
async def server_info():
    """Get server information."""
    return {
        "name": "TMF ODA Transformer MCP Server",
        "version": "1.0.0",
        "protocol": "mcp",
        "transport": "http",
        "mcp_version": "2024-11-05",
        "capabilities": {
            "tools": {
                "listChanged": False
            }
        },
        "tools_count": len(TOOLS),
        "tools": list(TOOLS.keys()),
        "initialized": server_state["initialized"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/tools")
async def list_tools_simple():
    """Simple tools list for compatibility - now includes parameter schemas."""
    return {
        "tools": [
            {
                "name": tool_name,
                "description": tool_info["description"],
                "inputSchema": tool_info["inputSchema"]
            }
            for tool_name, tool_info in TOOLS.items()
        ]
    }

@app.get("/debug/mcp-methods")
async def debug_mcp_methods():
    """Debug endpoint to inspect MCP object methods."""
    try:
        return {
            "tools_registry": list(TOOLS.keys()),
            "server_state": server_state,
            "has_direct_tools": True,
            "tools_count": len(TOOLS)
        }
    except Exception as e:
        return {"error": str(e)}

# Legacy REST API endpoints for backward compatibility
@app.post("/tools/{tool_name}")
async def call_tool_rest(tool_name: str, request: Request):
    """REST API endpoint for calling tools (legacy compatibility)."""
    # Initialize final_args immediately to avoid UnboundLocalError
    final_args = {}
    
    try:
        data = await request.json()
        
        # Get tool from registry
        tool_info = TOOLS.get(tool_name)
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Reset context errors
        ctx.errors = []
        
        # Validate required parameters
        required_params = tool_info["inputSchema"].get("required", [])
        missing_required = [
            param for param in required_params if param not in data
        ]
        if missing_required:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required parameters for tool '{tool_name}': {', '.join(missing_required)}"
            )

        # Get schema properties for validation
        schema_props = tool_info["inputSchema"]["properties"]

        # Validate enum values for string properties
        for prop_name, prop_info in schema_props.items():
            if prop_info.get("type") == "string" and "enum" in prop_info:
                if prop_name in data and data[prop_name] not in prop_info["enum"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid value for parameter '{prop_name}' for tool '{tool_name}': must be one of {', '.join(prop_info['enum'])}"
                    )

        # Apply defaults for missing arguments AND include ALL JSON data
        final_args = {}
        
        # First, add all data from the JSON request
        for key, value in data.items():
            final_args[key] = value
        
        # Then apply schema defaults for missing arguments
        for prop_name, prop_info in schema_props.items():
            if prop_name not in final_args and "default" in prop_info:
                final_args[prop_name] = prop_info["default"]
        
        # Filter out unknown parameters to prevent "unexpected keyword argument" errors
        # Only keep parameters that are in the tool's schema
        filtered_args = {}
        unknown_params = {}
        
        for key, value in final_args.items():
            if key in schema_props:
                filtered_args[key] = value
            else:
                unknown_params[key] = value
        
        # Add any unknown parameters to the appropriate data parameter if they exist
        if unknown_params and 'journey_data' in schema_props:
            # If journey_data exists in schema, merge unknown params into it
            if filtered_args.get('journey_data') is None:
                filtered_args['journey_data'] = {}
            if isinstance(filtered_args['journey_data'], dict):
                filtered_args['journey_data'].update(unknown_params)
        
        # Use filtered arguments
        final_args = filtered_args
        
        # Get tool function
        tool_func = tool_info["func"]
        
        # Log the tool call for REST API
        logger.info(f"🔧 REST API Tool Call: {tool_name}")
        logger.debug(f"REST API arguments: {json.dumps(final_args, indent=2, default=str)}")
        
        # Add debug output to server logs
        dual_logger.debug(f"=== DEBUGGING TOOL CALL: {tool_name} ===")
        dual_logger.debug(f"Raw request data: {data}")
        dual_logger.debug(f"Filtered arguments: {final_args}")
        dual_logger.debug(f"Unknown parameters: {unknown_params}")
        dual_logger.debug(f"Schema properties: {list(schema_props.keys())}")
        dual_logger.debug(f"=== END DEBUG ===")
        
        # Add print statements for debugging
        print(f"=== DEBUGGING TOOL CALL: {tool_name} ===")
        print(f"Raw request data: {data}")
        print(f"Filtered arguments: {final_args}")
        print(f"Unknown parameters: {unknown_params}")
        print(f"Schema properties: {list(schema_props.keys())}")
        print(f"=== END DEBUG ===")
        
        result = await tool_func(ctx, **final_args)
        
        # Convert result to JSON-serializable format
        if hasattr(result, 'dict'):
            result_data = result.dict()
        elif hasattr(result, '__dict__'):
            result_data = result.__dict__
        else:
            result_data = result
        
        # Log the successful result
        logger.info(f"✅ REST API Tool {tool_name} completed successfully")
        logger.debug(f"REST API result: {json.dumps(result_data, indent=2, default=str)}")
        
        return {
            "result": result_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Log the error with full details
        dual_logger.error(f"❌ REST API Tool {tool_name} execution failed: {str(e)}")
        dual_logger.error(f"Exception details: {traceback.format_exc()}")
        dual_logger.error(f"Tool arguments: {json.dumps(final_args, indent=2, default=str)}")
        
        print(f"Error calling tool {tool_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    dual_logger.info("🚀 Starting TMF ODA Transformer MCP HTTP Transport Server...")
    dual_logger.info("📡 Server will be available at: http://0.0.0.0:8000")
    dual_logger.info("🔗 MCP Server Info: http://0.0.0.0:8000/mcp/server/info")
    dual_logger.info("🏥 Health check: http://0.0.0.0:8000/health")
    dual_logger.info("📋 Tools list: http://0.0.0.0:8000/tools")
    dual_logger.info(f"🔧 Available tools: {', '.join(TOOLS.keys())}")
    
    print("🚀 Starting TMF ODA Transformer MCP HTTP Transport Server...")
    print("📡 Server will be available at: http://0.0.0.0:8000")
    print("🔗 MCP Server Info: http://0.0.0.0:8000/mcp/server/info")
    print("🏥 Health check: http://0.0.0.0:8000/health")
    print("📋 Tools list: http://0.0.0.0:8000/tools")
    print(f"🔧 Available tools: {', '.join(TOOLS.keys())}")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        access_log=True,
        log_level=LOG_LEVEL.lower()
    ) 