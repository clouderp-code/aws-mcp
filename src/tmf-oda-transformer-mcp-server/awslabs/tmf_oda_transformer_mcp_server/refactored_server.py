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

"""TMF ODA Transformer MCP Server - Refactored and Modularized.

This is a Model Context Protocol (MCP) server that enables AI assistants to transform
customer database schemas and APIs into TMF ODA (Open Digital Architecture) compliant formats.

The server provides comprehensive tools for:
- Schema analysis and TMF ODA compliance assessment
- Database structure analysis for transformation planning
- Journey management for multi-stage transformation processes
- Job execution and monitoring capabilities
- Testing and validation utilities

All functionality has been refactored into organized modules for better maintainability.
"""

import asyncio
import logging
import os

from loguru import logger
from mcp.server.fastmcp import FastMCP

from .consts import TMF_ODA_MCP_SERVER_APPLICATION_NAME
from .tools import (
    schema_analyzer_tool,
    db_analyzer_tool,
    raw_analysis_tool,
    stripped_schema_tool,
    run_jobs_tool,
    journeys_tool,
    get_job_logs_tool,
    test_runner_tool,
)

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Initialize the FastMCP server
mcp = FastMCP(TMF_ODA_MCP_SERVER_APPLICATION_NAME)

# Register all tools with the MCP server
logger.info("Registering TMF ODA transformation tools...")

# Analysis Tools
mcp.tool()(schema_analyzer_tool)
mcp.tool()(db_analyzer_tool)

# Execution Tools  
mcp.tool()(raw_analysis_tool)
mcp.tool()(stripped_schema_tool)
mcp.tool()(run_jobs_tool)

# Management Tools
mcp.tool()(journeys_tool)

# Utility Tools
mcp.tool()(get_job_logs_tool)
mcp.tool()(test_runner_tool)

logger.success("All 8 TMF ODA tools registered successfully!")


def main():
    """Main entry point for the TMF ODA Transformer MCP Server."""
    logger.info(f"Starting {TMF_ODA_MCP_SERVER_APPLICATION_NAME}")
    logger.info("🚀 TMF ODA Transformer MCP Server ready for AI assistant integration")
    logger.info("📋 Available tools:")
    logger.info("   🔍 schema-analyzer: Analyze workspace schemas for TMF ODA compliance")
    logger.info("   🗄️  db-analyzer: Analyze database structures for transformation")
    logger.info("   ⚡ raw-analysis: Execute raw analysis stage")
    logger.info("   🔧 stripped-schema: Execute schema stripping stage")
    logger.info("   🎯 run-jobs: Execute any transformation stage")
    logger.info("   📊 journeys: Comprehensive journey management (CRUD)")
    logger.info("   📝 get-job-logs: Retrieve detailed execution logs")
    logger.info("   🧪 test-runner: Comprehensive tool validation testing")
    
    # Run the MCP server
    asyncio.run(mcp.run())


if __name__ == "__main__":
    main() 