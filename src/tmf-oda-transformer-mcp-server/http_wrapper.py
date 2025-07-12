#!/usr/bin/env python3
"""
HTTP wrapper for TMF ODA Transformer MCP Server.

This wrapper provides HTTP endpoints for all TMF ODA transformation tools,
allowing external applications to interact with the server via REST API.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Import the tools
from awslabs.tmf_oda_transformer_mcp_server.server import (
    # schema_analyzer_tool,     # Removed tool
    # db_analyzer_tool,         # Removed tool
    raw_analysis_tool,
    stripped_schema_tool,
    get_job_logs_tool,
    test_runner_tool,
    journeys_tool,
    run_jobs_tool
)
from awslabs.tmf_oda_transformer_mcp_server.models import (
    TMFODAComponentType,
    DatabaseType,
    SchemaFormat
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TMF ODA Transformer MCP Server",
    description="HTTP API for TMF ODA transformation tools",
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

# Create a mock context for the tools
ctx = AsyncMock()


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "service": "TMF ODA Transformer MCP Server",
        "version": "1.0.0",
        "status": "operational",
        "tools_available": 6,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# @app.post("/tools/schema-analyzer")
# async def call_schema_analyzer(request: Request):
#     """Call schema analyzer tool."""
#     try:
#         data = await request.json()
#         
#         workspace_dir = data.get("workspace_dir", "")
#         oda_component_type = TMFODAComponentType(data.get("oda_component_type", "customer-management"))
#         schema_format = None
#         if data.get("schema_format"):
#             schema_format = SchemaFormat(data["schema_format"])
#         
#         result = await schema_analyzer_tool(
#             ctx=ctx,
#             workspace_dir=workspace_dir,
#             oda_component_type=oda_component_type,
#             schema_format=schema_format
#         )
#         
#         return {"result": result, "timestamp": datetime.now().isoformat()}
#         
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# @app.post("/tools/db-analyzer")
# async def call_db_analyzer(request: Request):
#     """Call database analyzer tool."""
#     try:
#         data = await request.json()
#         
#         connection_string = data.get("connection_string", "")
#         database_type = DatabaseType(data.get("database_type", "postgresql"))
#         oda_component_type = TMFODAComponentType(data.get("oda_component_type", "customer-management"))
#         tables_filter = data.get("tables_filter")
#         
#         result = await db_analyzer_tool(
#             ctx=ctx,
#             connection_string=connection_string,
#             database_type=database_type,
#             oda_component_type=oda_component_type,
#             tables_filter=tables_filter
#         )
#         
#         return {"result": result, "timestamp": datetime.now().isoformat()}
#         
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


@app.post("/tools/raw-analysis")
async def call_raw_analysis(request: Request):
    """Call raw analysis tool."""
    try:
        data = await request.json()
        
        journey_id = data.get("journey_id", "")
        stage_id = data.get("stage_id", "raw_analysis")
        triggered_by = data.get("triggered_by", "http_api")
        reason = data.get("reason", "HTTP API request")
        
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
        reason = data.get("reason", "HTTP API request")
        
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


@app.post("/tools/run-jobs")
async def call_run_jobs(request: Request):
    """Call run jobs tool."""
    try:
        data = await request.json()
        
        journey_id = data.get("journey_id", "")
        stage_id = data.get("stage_id", "raw_analysis")
        triggered_by = data.get("triggered_by", "http_api")
        reason = data.get("reason", "HTTP API request")
        
        result = await run_jobs_tool(
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
        stage_name = data.get("stage_name", "raw_analysis")
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


@app.post("/tools/journeys")
async def call_journeys(request: Request):
    """Call journeys tool."""
    try:
        data = await request.json()
        
        action = data.get("action", "read")
        journey_id = data.get("journey_id")
        journey_data = data.get("journey_data")
        stage_id = data.get("stage_id")
        include_stages = data.get("include_stages", True)
        include_job_history = data.get("include_job_history", True)
        job_limit = data.get("job_limit", 10)
        
        result = await journeys_tool(
            ctx=ctx,
            action=action,
            journey_id=journey_id,
            journey_data=journey_data,
            stage_id=stage_id,
            include_stages=include_stages,
            include_job_history=include_job_history,
            job_limit=job_limit
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
            # {
            #     "name": "schema-analyzer",
            #     "endpoint": "/tools/schema-analyzer",
            #     "method": "POST",
            #     "description": "Analyze schema files for TMF ODA compliance"
            # },
            # {
            #     "name": "db-analyzer", 
            #     "endpoint": "/tools/db-analyzer",
            #     "method": "POST",
            #     "description": "Analyze database structures for TMF ODA compliance"
            # },
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
                "name": "run-jobs",
                "endpoint": "/tools/run-jobs",
                "method": "POST",
                "description": "Execute any transformation stage"
            },
            {
                "name": "get-job-logs",
                "endpoint": "/tools/get-job-logs",
                "method": "POST",
                "description": "Retrieve job execution logs"
            },
            {
                "name": "journeys",
                "endpoint": "/tools/journeys",
                "method": "POST",
                "description": "Comprehensive journey management (CRUD)"
            },
            {
                "name": "test-runner",
                "endpoint": "/tools/test-runner",
                "method": "POST",
                "description": "Run comprehensive tool verification tests"
            }
        ]
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 