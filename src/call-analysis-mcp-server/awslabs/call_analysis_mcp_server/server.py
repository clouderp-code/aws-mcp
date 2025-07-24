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

"""Call Analysis MCP Server - AI-Powered Call Transcript Analysis.

This is a Model Context Protocol (MCP) server that enables AI assistants to analyze
call transcripts stored in S3 and generate comprehensive analysis reports with KPIs,
sentiment analysis, compliance metrics, and performance indicators.

The server provides comprehensive tools for:
- Reading call transcripts from S3 buckets
- Performing detailed sentiment and topic analysis
- Generating compliance and performance KPIs
- Creating comprehensive analysis reports in JSON and Markdown formats
- Uploading analysis results back to S3 for UI display
- Batch processing of multiple transcripts
- Interactive dashboard generation
- Business intelligence insights for management queries

All functionality is organized into modular services for maintainability and extensibility.
"""

import asyncio
import logging
import os

from loguru import logger
from mcp.server.fastmcp import FastMCP

from .consts import CALL_ANALYSIS_MCP_SERVER_APPLICATION_NAME
from .tools import (
    transcript_analyzer_tool, batch_analysis_tool, s3_reader_tool,
    s3_uploader_tool, generate_report_tool, create_dashboard_tool,
    business_intelligence_tool, local_scripts_analysis_tool,
)


def create_server() -> FastMCP:
    """Create and configure the Call Analysis MCP server."""
    
    # Initialize the FastMCP server
    mcp = FastMCP(CALL_ANALYSIS_MCP_SERVER_APPLICATION_NAME)
    
    # Register all analysis tools
    logger.info("Registering Call Analysis MCP tools...")
    
    # Register all tools
    transcript_analyzer_tool(mcp)
    batch_analysis_tool(mcp)
    business_intelligence_tool(mcp)
    local_scripts_analysis_tool(mcp)
    s3_reader_tool(mcp)
    s3_uploader_tool(mcp)
    generate_report_tool(mcp)
    create_dashboard_tool(mcp)
    
    logger.info("Call Analysis MCP Server initialized successfully")
    return mcp


async def main():
    """Main entry point for the MCP server."""
    
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.remove()  # Remove default handler
    logger.add(
        lambda msg: print(msg, end=""),
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    logger.info(f"Starting {CALL_ANALYSIS_MCP_SERVER_APPLICATION_NAME}")
    
    # Validate AWS configuration
    aws_region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    logger.info(f"Using AWS region: {aws_region}")
    
    # Check for required environment variables
    required_env_vars = []
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing optional environment variables: {missing_vars}")
        logger.info("Server will still start, but some features may require these variables")
    
    # Log configuration information
    logger.info("Call Analysis MCP Server Configuration:")
    logger.info(f"  - AWS Region: {aws_region}")
    logger.info(f"  - Log Level: {log_level}")
    logger.info(f"  - AWS Profile: {os.getenv('AWS_PROFILE', 'default')}")
    
    # Create and run the server
    try:
        server = create_server()
        
        # Register server info
        @server.list_resources()
        async def list_resources():
            return [
                {
                    "uri": "call-analysis://transcripts",
                    "name": "Call Transcripts",
                    "description": "Access to call transcript analysis capabilities",
                    "mimeType": "application/json"
                },
                {
                    "uri": "call-analysis://reports",
                    "name": "Analysis Reports",
                    "description": "Generated analysis reports and dashboards",
                    "mimeType": "text/markdown"
                },
                {
                    "uri": "call-analysis://business-intelligence",
                    "name": "Business Intelligence",
                    "description": "Business intelligence insights and management queries",
                    "mimeType": "application/json"
                },
                {
                    "uri": "call-analysis://local-scripts",
                    "name": "Local Scripts Analysis",
                    "description": "Analyze local script files and generate enhanced BI reports with evidence trails",
                    "mimeType": "application/json"
                }
            ]
        
        @server.get_resource()
        async def get_resource(uri: str):
            if uri == "call-analysis://transcripts":
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": """{
                                "description": "Call Analysis MCP Server provides comprehensive analysis of call transcripts",
                                "features": [
                                    "Sentiment analysis with emotion detection",
                                    "Topic extraction and categorization",
                                    "Compliance monitoring and scoring",
                                    "Performance KPIs and metrics",
                                    "Conversation flow analysis",
                                    "Batch processing capabilities",
                                    "Interactive dashboard generation",
                                    "Business intelligence insights"
                                ],
                                "supported_formats": [".txt", ".json", ".csv", ".tsv"]
                            }"""
                        }
                    ]
                }
            elif uri == "call-analysis://reports":
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "text/markdown",
                            "text": """# Call Analysis Reports

The Call Analysis MCP Server generates comprehensive reports including:

## Analysis Output Formats
- **analysis.json**: Complete analysis data with all metrics and KPIs
- **analysis.md**: Human-readable markdown report with insights
- **dashboard.html**: Interactive web dashboard for visualization

## Key Metrics Tracked
- Customer satisfaction scores
- Agent performance indicators  
- Compliance adherence
- Sentiment trends
- Topic analysis
- Conversation quality metrics

## Batch Processing
- Process multiple transcripts simultaneously
- Generate comparative analysis
- Create executive summaries
- Track trends across calls
"""
                        }
                    ]
                }
            elif uri == "call-analysis://business-intelligence":
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": """{
                                "description": "Business Intelligence capabilities for management insights",
                                "query_types": [
                                    "Overall call quality assessment",
                                    "Deal risk identification",
                                    "Pipeline health analysis",
                                    "Agent training needs",
                                    "Churn risk detection",
                                    "New opportunity identification",
                                    "Recurring objection patterns"
                                ],
                                "output_format": "Structured insights with actionable recommendations"
                            }"""
                        }
                    ]
                }
            elif uri == "call-analysis://local-scripts":
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": """{
                                "description": "Local script file analysis capabilities",
                                "features": [
                                    "Read script files from local transcripts folder",
                                    "Process multiple script*.json files",
                                    "Generate enhanced business intelligence with evidence trails",
                                    "Output comprehensive analysis reports",
                                    "Support various transcript formats (JSON with speaker/text pairs)"
                                ],
                                "input_format": "Local JSON script files with transcript data",
                                "output_format": "Enhanced BI analysis with evidence references"
                            }"""
                        }
                    ]
                }
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        logger.info("Call Analysis MCP Server is ready to process requests")
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Shutting down Call Analysis MCP Server...")
    except Exception as e:
        logger.error(f"Error running Call Analysis MCP Server: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 