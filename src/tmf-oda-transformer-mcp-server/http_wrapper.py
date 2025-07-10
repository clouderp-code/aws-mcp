#!/usr/bin/env python3
"""
HTTP Wrapper for TMF ODA Transformer MCP Server
Provides HTTP endpoints for external access to all 6 MCP tools.
"""

import asyncio
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from unittest.mock import AsyncMock
from datetime import datetime
import traceback
import sys
import os
from pathlib import Path

# Add the MCP server to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import MCP tools and models
try:
    from awslabs.tmf_oda_transformer_mcp_server.server import (
        schema_analyzer_tool,
        db_analyzer_tool,
        raw_analysis_tool,
        stripped_schema_tool,
        get_job_logs_tool,
        test_runner_tool
    )
    from awslabs.tmf_oda_transformer_mcp_server.models import (
        TMFODAComponentType,
        DatabaseType,
        SchemaFormat
    )
except ImportError as e:
    print(f"Error importing MCP tools: {e}")
    sys.exit(1)

# FastAPI app
app = FastAPI(
    title="TMF ODA Transformer MCP Server HTTP API",
    description="HTTP API wrapper for TMF ODA transformation tools",
    version="1.0.0"
)

class NoOpContext:
    """No-op context for MCP tools."""
    async def error(self, message):
        print(f"Error: {message}")

# Global context
ctx = NoOpContext()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "TMF ODA Transformer MCP Server",
        "version": "1.0.0",
        "status": "running",
        "tools": [
            "schema-analyzer",
            "db-analyzer", 
            "raw-analysis",
            "stripped-schema",
            "get-job-logs",
            "test-runner"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        # Quick health check
        from awslabs.tmf_oda_transformer_mcp_server.server import test_runner_tool
        
        result = await test_runner_tool(
            ctx=ctx,
            test_type="quick",
            include_performance=False
        )
        
        return {
            "status": "healthy",
            "mcp_server": result.get("status", "unknown"),
            "tools_available": 6,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/tools/schema-analyzer")
async def call_schema_analyzer(request: Request):
    """Call schema analyzer tool."""
    try:
        data = await request.json()
        
        workspace_dir = data.get("workspace_dir", "")
        oda_component_type = TMFODAComponentType(data.get("oda_component_type", "customer-management"))
        schema_format = None
        if data.get("schema_format"):
            schema_format = SchemaFormat(data["schema_format"])
        
        result = await schema_analyzer_tool(
            ctx=ctx,
            workspace_dir=workspace_dir,
            oda_component_type=oda_component_type,
            schema_format=schema_format
        )
        
        return {"result": result, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/db-analyzer")
async def call_db_analyzer(request: Request):
    """Call database analyzer tool."""
    try:
        data = await request.json()
        
        connection_string = data.get("connection_string", "")
        database_type = DatabaseType(data.get("database_type", "postgresql"))
        oda_component_type = TMFODAComponentType(data.get("oda_component_type", "customer-management"))
        tables_filter = data.get("tables_filter")
        
        result = await db_analyzer_tool(
            ctx=ctx,
            connection_string=connection_string,
            database_type=database_type,
            oda_component_type=oda_component_type,
            tables_filter=tables_filter
        )
        
        return {"result": result, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/raw-analysis")
async def call_raw_analysis(request: Request):
    """Call raw analysis tool."""
    try:
        data = await request.json()
        
        journey_id = data.get("journey_id", "")
        stage_id = data.get("stage_id", "raw_analysis")
        triggered_by = data.get("triggered_by", "http_api")
        reason = data.get("reason", "HTTP API call")
        
        result = await raw_analysis_tool(
            ctx=ctx,
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason
        )
        
        return {"result": result, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/stripped-schema")
async def call_stripped_schema(request: Request):
    """Call stripped schema tool."""
    try:
        data = await request.json()
        
        journey_id = data.get("journey_id", "")
        stage_id = data.get("stage_id", "stripped_schema")
        triggered_by = data.get("triggered_by", "http_api")
        reason = data.get("reason", "HTTP API call")
        
        result = await stripped_schema_tool(
            ctx=ctx,
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason=reason
        )
        
        return {"result": result, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/get-job-logs")
async def call_get_job_logs(request: Request):
    """Call get job logs tool."""
    try:
        data = await request.json()
        
        journey_id = data.get("journey_id", "")
        stage_name = data.get("stage_name", "")
        job_id = data.get("job_id", "")
        step_name = data.get("step_name", "")
        
        result = await get_job_logs_tool(
            ctx=ctx,
            journey_id=journey_id,
            stage_name=stage_name,
            job_id=job_id,
            step_name=step_name
        )
        
        return {"result": result, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/test-runner")
async def call_test_runner(request: Request):
    """Call test runner tool."""
    try:
        data = await request.json()
        
        test_type = data.get("test_type", "quick")
        include_performance = data.get("include_performance", False)
        
        result = await test_runner_tool(
            ctx=ctx,
            test_type=test_type,
            include_performance=include_performance
        )
        
        return {"result": result, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tools")
async def list_tools():
    """List available tools."""
    return {
        "tools": [
            {
                "name": "schema-analyzer",
                "endpoint": "/tools/schema-analyzer",
                "method": "POST",
                "description": "Analyze schema files for TMF ODA compliance"
            },
            {
                "name": "db-analyzer", 
                "endpoint": "/tools/db-analyzer",
                "method": "POST",
                "description": "Analyze database structures for TMF ODA compliance"
            },
            {
                "name": "raw-analysis",
                "endpoint": "/tools/raw-analysis", 
                "method": "POST",
                "description": "Execute raw analysis stage of transformation"
            },
            {
                "name": "stripped-schema",
                "endpoint": "/tools/stripped-schema",
                "method": "POST", 
                "description": "Execute stripped schema stage of transformation"
            },
            {
                "name": "get-job-logs",
                "endpoint": "/tools/get-job-logs",
                "method": "POST",
                "description": "Retrieve job execution logs"
            },
            {
                "name": "test-runner",
                "endpoint": "/tools/test-runner",
                "method": "POST",
                "description": "Run comprehensive tool verification tests"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting TMF ODA Transformer HTTP API Server...")
    print("📡 Server will be available at: http://0.0.0.0:8000")
    print("🔗 API documentation: http://0.0.0.0:8000/docs")
    print("🏥 Health check: http://0.0.0.0:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        access_log=True,
        log_level="info"
    ) 