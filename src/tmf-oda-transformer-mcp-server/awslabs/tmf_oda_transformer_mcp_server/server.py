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
    # schema_analyzer_tool,  # Commented out for focus on core execution tools
    # db_analyzer_tool,      # Commented out for focus on core execution tools
    raw_analysis_tool,
    stripped_schema_tool,
    run_jobs_tool,
    journeys_tool,
    get_job_logs_tool,
    test_runner_tool,
)

# Expose objects that tests expect to mock
try:
    from .scripts.utils import TransformationUtils
    logger.info("Successfully imported TransformationUtils")
except ImportError:
    TransformationUtils = None
    logger.info("TransformationUtils not available")

try:
    from .managers import FallbackJourneyManager
    journey_manager = FallbackJourneyManager()
    logger.info("Successfully initialized journey_manager")
except ImportError:
    journey_manager = None
    logger.info("journey_manager not available")

# Additional objects that tests expect to mock
try:
    from .scripts.aws_client_utils import create_aws_client
    logger.info("Successfully imported create_aws_client")
except ImportError:
    create_aws_client = None
    logger.info("create_aws_client not available")

try:
    from .scripts.job_executor import TransformationJobExecutor
    logger.info("Successfully imported TransformationJobExecutor")
except ImportError:
    TransformationJobExecutor = None
    logger.info("TransformationJobExecutor not available")

# Database and schema analysis helper functions that tests expect to mock
# COMMENTED OUT - Focusing on core execution tools for now
# def _test_database_connection(connection_string, database_type):
#     """Mock-able database connection test function."""
#     from .services import DatabaseAnalysisService
#     service = DatabaseAnalysisService()
#     return service._test_database_connection(connection_string, database_type)

# def _discover_database_tables(connection_string, database_type, table_filter=None):
#     """Mock-able database table discovery function."""
#     from .services import DatabaseAnalysisService
#     service = DatabaseAnalysisService()
#     return service._discover_database_tables(connection_string, database_type, table_filter)

# def _analyze_database_table(connection_string, database_type, table_name):
#     """Mock-able database table analysis function."""
#     from .services import DatabaseAnalysisService
#     service = DatabaseAnalysisService()
#     return service._analyze_database_table(connection_string, database_type, table_name)

# def _discover_schema_files(workspace_dir, schema_format=None):
#     """Mock-able schema file discovery function."""
#     from .services import SchemaAnalysisService
#     service = SchemaAnalysisService()
#     return service._discover_schema_files(workspace_dir, schema_format)

# def _analyze_schema_file(file_path, schema_format, oda_component_type):
#     """Mock-able schema file analysis function."""
#     from .services import SchemaAnalysisService
#     service = SchemaAnalysisService()
#     return service._analyze_schema_file(file_path, schema_format, oda_component_type)

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

# Analysis Tools (COMMENTED OUT - Focusing on core execution tools)
# mcp.tool()(schema_analyzer_tool)
# mcp.tool()(db_analyzer_tool)

# Execution Tools  
mcp.tool()(raw_analysis_tool)
mcp.tool()(stripped_schema_tool)
mcp.tool()(run_jobs_tool)

# Management Tools
mcp.tool()(journeys_tool)

# Utility Tools
mcp.tool()(get_job_logs_tool)
mcp.tool()(test_runner_tool)

logger.success("Core 6 TMF ODA tools registered successfully (analysis tools temporarily disabled)!")


def main():
    """Main entry point for the TMF ODA Transformer MCP Server."""
    logger.info(f"Starting {TMF_ODA_MCP_SERVER_APPLICATION_NAME}")
    logger.info("🚀 TMF ODA Transformer MCP Server ready for AI assistant integration")
    logger.info("📋 Available tools (6 core tools - analysis tools temporarily disabled):")
    # logger.info("   🔍 schema-analyzer: Analyze workspace schemas for TMF ODA compliance")  # DISABLED
    # logger.info("   🗄️  db-analyzer: Analyze database structures for transformation")        # DISABLED
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