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

# Add the MCP server to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import MCP server and tools directly
try:
    from awslabs.tmf_oda_transformer_mcp_server.server import (
        mcp,
        schema_analyzer_tool,
        db_analyzer_tool,
        raw_analysis_tool,
        stripped_schema_tool,
        get_job_logs_tool,
        test_runner_tool,
        journeys_tool,
        run_jobs_tool
    )
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

# Store server state
server_state = {
    "initialized": False,
    "session_id": None,
    "client_info": None
}

# Tool registry with direct function references
TOOLS = {
    "schema-analyzer": {
        "func": schema_analyzer_tool,
        "description": "Analyze schema files for TMF ODA compliance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": {"type": "string", "description": "Directory path to analyze", "default": "/opt/mycode/aws-mcp"},
                "oda_component_type": {"type": "string", "description": "TMF ODA component type", "default": "product-catalog-management"},
                "schema_format": {"type": "string", "description": "Optional schema format filter", "default": None}
            },
            "required": []
        }
    },
    "db-analyzer": {
        "func": db_analyzer_tool,
        "description": "Analyze database structures for TMF ODA compliance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "connection_string": {"type": "string", "description": "Database connection string", "default": "postgresql://demo:demo@localhost:5432/tmf_demo"},
                "database_type": {"type": "string", "description": "Database type", "default": "postgresql"},
                "oda_component_type": {"type": "string", "description": "TMF ODA component type", "default": "product-catalog-management"},
                "tables_filter": {"type": "string", "description": "Optional tables filter", "default": None}
            },
            "required": []
        }
    },
    "raw-analysis": {
        "func": raw_analysis_tool,
        "description": "Execute raw analysis stage of transformation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journey_id": {"type": "string", "description": "Journey ID", "default": "JRN-DEMO-001"},
                "stage_id": {"type": "string", "description": "Stage ID", "default": "raw_analysis"},
                "triggered_by": {"type": "string", "description": "Who triggered this", "default": "mcp-server"},
                "reason": {"type": "string", "description": "Reason for execution", "default": "MCP Server execution"}
            },
            "required": []
        }
    },
    "stripped-schema": {
        "func": stripped_schema_tool,
        "description": "Execute stripped schema stage of transformation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journey_id": {"type": "string", "description": "Journey ID", "default": "JRN-DEMO-001"},
                "stage_id": {"type": "string", "description": "Stage ID", "default": "stripped_schema"},
                "triggered_by": {"type": "string", "description": "Who triggered this", "default": "mcp-server"},
                "reason": {"type": "string", "description": "Reason for execution", "default": "MCP Server execution"}
            },
            "required": []
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
            "required": []
        }
    },
    "test-runner": {
        "func": test_runner_tool,
        "description": "Run comprehensive tool verification tests",
        "inputSchema": {
            "type": "object",
            "properties": {
                "test_type": {"type": "string", "description": "Type of tests to run"},
                "include_performance": {"type": "boolean", "description": "Include performance tests"}
            },
            "required": []
        }
    },
    "journeys": {
        "func": journeys_tool,
        "description": "Comprehensive journey management with CRUD operations (CREATE, READ, UPDATE, DELETE)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journey_id": {"type": "string", "description": "Optional journey ID", "default": None},
                "stage_id": {"type": "string", "description": "Optional stage ID", "default": None},
                "include_stages": {"type": "boolean", "description": "Include stage details", "default": True},
                "include_job_history": {"type": "boolean", "description": "Include job history", "default": True},
                "job_limit": {"type": "integer", "description": "Job limit", "default": 10}
            },
            "required": []
        }
    },
    "run-jobs": {
        "func": run_jobs_tool,
        "description": "Execute any transformation stage",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journey_id": {"type": "string", "description": "Journey ID", "default": "JRN-DEMO-001"},
                "stage_id": {"type": "string", "description": "Stage ID to execute", "default": "raw_analysis"},
                "triggered_by": {"type": "string", "description": "Who triggered this", "default": "mcp-server"},
                "reason": {"type": "string", "description": "Reason for execution", "default": "MCP Server execution"}
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

Provides tools to analyze schema files and databases for TMF ODA (TM Forum Open Digital Architecture) transformation compliance.

Available tools:
- schema-analyzer: Analyze schema files for TMF ODA compliance
- db-analyzer: Analyze database structures for TMF ODA compliance  
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
        
        # Reset context errors
        ctx.errors = []
        
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
    """Simple tools list for compatibility."""
    return {
        "tools": [
            {
                "name": tool_name,
                "description": tool_info["description"]
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
    try:
        data = await request.json()
        
        # Get tool from registry
        tool_info = TOOLS.get(tool_name)
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Reset context errors
        ctx.errors = []
        
        # Call tool function
        tool_func = tool_info["func"]
        
        # Apply defaults for missing arguments
        schema_props = tool_info["inputSchema"]["properties"]
        final_args = {}
        
        for prop_name, prop_info in schema_props.items():
            if prop_name in data:
                final_args[prop_name] = data[prop_name]
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
        
        return {
            "result": result_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error calling tool {tool_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting TMF ODA Transformer MCP HTTP Transport Server...")
    print("📡 Server will be available at: http://0.0.0.0:8000")
    print("🔗 MCP Server Info: http://0.0.0.0:8000/mcp/server/info")
    print("🏥 Health check: http://0.0.0.0:8000/health")
    print("📋 Tools list: http://0.0.0.0:8000/tools")
    print(f"🔧 Available tools: {', '.join(TOOLS.keys())}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        access_log=True,
        log_level="info"
    ) 