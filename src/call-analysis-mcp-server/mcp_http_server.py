#!/usr/bin/env python3
"""
MCP HTTP Transport Server for Call Analysis
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
parser = argparse.ArgumentParser(description="Call Analysis MCP HTTP Server")
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
logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "uvicorn.log"),
        logging.StreamHandler()
    ]
)

dual_logger.info("=== Call Analysis MCP HTTP Server Starting ===")
dual_logger.info(f"Log directory: {LOG_DIR}")
dual_logger.info(f"Log files will be rotated daily and kept for 30 days")

# Import MCP server and tools directly
try:
    from awslabs.call_analysis_mcp_server.server import create_server
    from awslabs.call_analysis_mcp_server.tools.analysis_tools import (
        transcript_analyzer_tool, batch_analysis_tool, business_intelligence_tool, 
        local_scripts_analysis_tool, qa_analysis_tool
    )
    from awslabs.call_analysis_mcp_server.tools.s3_tools import s3_reader_tool, s3_uploader_tool
    from awslabs.call_analysis_mcp_server.tools.reporting_tools import generate_report_tool, create_dashboard_tool
    print("✅ Call Analysis MCP server and tools imported successfully")
except ImportError as e:
    print(f"❌ Error importing Call Analysis MCP server: {e}")
    traceback.print_exc()
    sys.exit(1)

# FastAPI app
app = FastAPI(
    title="Call Analysis MCP HTTP Transport",
    description="MCP HTTP transport server for AI-powered call transcript analysis tools",
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
    "analyze-transcript": {
        "description": "Analyze a single call transcript from S3 and generate comprehensive AI-powered analysis with KPIs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "s3_bucket": {
                    "type": "string",
                    "description": "S3 bucket containing the transcript file"
                },
                "s3_key": {
                    "type": "string", 
                    "description": "S3 key path to the transcript file"
                },
                "output_bucket": {
                    "type": "string",
                    "description": "S3 bucket for output files"
                },
                "output_prefix": {
                    "type": "string",
                    "description": "Prefix for output files",
                    "default": ""
                },
                "analysis_options": {
                    "type": "object",
                    "description": "Dictionary of analysis options to enable/disable",
                    "default": None
                },
                "aws_region": {
                    "type": "string",
                    "description": "AWS region for S3 operations",
                    "default": "us-east-1"
                }
            },
            "required": ["s3_bucket", "s3_key", "output_bucket"]
        }
    },
    "analyze-transcript-batch": {
        "description": "Analyze multiple call transcripts from an S3 folder and generate AI-powered batch analysis report",
        "inputSchema": {
            "type": "object",
            "properties": {
                "s3_bucket": {
                    "type": "string",
                    "description": "S3 bucket containing transcript files"
                },
                "s3_prefix": {
                    "type": "string",
                    "description": "S3 prefix/folder path containing transcripts"
                },
                "output_bucket": {
                    "type": "string",
                    "description": "S3 bucket for output files"
                },
                "output_prefix": {
                    "type": "string",
                    "description": "Prefix for output files",
                    "default": "batch_analysis"
                },
                "max_files": {
                    "type": "integer",
                    "description": "Maximum number of files to process",
                    "default": 100
                },
                "analysis_options": {
                    "type": "object",
                    "description": "Dictionary of analysis options to enable/disable",
                    "default": None
                },
                "aws_region": {
                    "type": "string",
                    "description": "AWS region for S3 operations",
                    "default": "us-east-1"
                }
            },
            "required": ["s3_bucket", "s3_prefix", "output_bucket"]
        }
    },
    "generate-business-intelligence": {
        "description": "Generate AI-powered business intelligence insights from call analysis results to answer management queries",
        "inputSchema": {
            "type": "object",
            "properties": {
                "analysis_s3_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of S3 URLs containing analysis JSON files"
                },
                "output_bucket": {
                    "type": "string",
                    "description": "S3 bucket for output business intelligence file"
                },
                "time_period": {
                    "type": "string",
                    "description": "Description of time period analyzed",
                    "default": "Today"
                },
                "output_key": {
                    "type": "string",
                    "description": "S3 key for output file",
                    "default": "business_intelligence.json"
                },
                "aws_region": {
                    "type": "string",
                    "description": "AWS region for S3 operations",
                    "default": "us-east-1"
                }
            },
            "required": ["analysis_s3_urls", "output_bucket"]
        }
    },
    "analyze-local-scripts": {
        "description": "Analyze local script files from transcripts folder and generate AI-enhanced business intelligence report with evidence trails",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scripts_folder": {
                    "type": "string",
                    "description": "Path to folder containing script files",
                    "default": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts"
                },
                "script_pattern": {
                    "type": "string",
                    "description": "File pattern to match",
                    "default": "script*.json"
                },
                "output_file": {
                    "type": "string",
                    "description": "Path for output analysis report",
                    "default": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/local_analysis_report.json"
                },
                "time_period": {
                    "type": "string",
                    "description": "Description of time period for the analysis",
                    "default": "Current Script Collection"
                },
                "max_scripts": {
                    "type": "integer",
                    "description": "Maximum number of scripts to process",
                    "default": 50
                },
                "analysis_options": {
                    "type": "object",
                    "description": "Dictionary of analysis options to enable/disable",
                    "default": None
                }
            },
            "required": []
        }
    },
    "ask-analysis-question": {
        "description": "Ask natural language questions about call analysis and business intelligence reports to get specific insights with evidence",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Natural language question about the call analysis data"
                },
                "report_file_path": {
                    "type": "string",
                    "description": "Path to the business intelligence report JSON file",
                    "default": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/ai_enhanced_analysis_all_scripts_report.json"
                },
                "context_type": {
                    "type": "string",
                    "description": "Type of context to focus on",
                    "enum": ["auto", "quality", "deals", "churn", "opportunities", "training", "pipeline"],
                    "default": "auto"
                }
            },
            "required": ["question"]
        }
    },
    "read-s3-transcript": {
        "description": "Read and parse call transcript files from S3",
        "inputSchema": {
            "type": "object",
            "properties": {
                "s3_bucket": {
                    "type": "string",
                    "description": "S3 bucket name"
                },
                "s3_key": {
                    "type": "string",
                    "description": "S3 object key"
                },
                "aws_region": {
                    "type": "string",
                    "description": "AWS region",
                    "default": "us-east-1"
                }
            },
            "required": ["s3_bucket", "s3_key"]
        }
    },
    "upload-to-s3": {
        "description": "Upload analysis results to S3",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to upload"
                },
                "s3_bucket": {
                    "type": "string",
                    "description": "S3 bucket name"
                },
                "s3_key": {
                    "type": "string",
                    "description": "S3 object key"
                },
                "content_type": {
                    "type": "string",
                    "description": "Content type",
                    "default": "application/json"
                },
                "aws_region": {
                    "type": "string",
                    "description": "AWS region",
                    "default": "us-east-1"
                }
            },
            "required": ["content", "s3_bucket", "s3_key"]
        }
    },
    "generate-report": {
        "description": "Generate markdown report from analysis results",
        "inputSchema": {
            "type": "object",
            "properties": {
                "analysis_result": {
                    "type": "object",
                    "description": "Analysis result object"
                },
                "report_type": {
                    "type": "string",
                    "description": "Type of report to generate",
                    "enum": ["detailed", "summary", "executive"],
                    "default": "detailed"
                }
            },
            "required": ["analysis_result"]
        }
    },
    "create-dashboard": {
        "description": "Create interactive dashboard from analysis data",
        "inputSchema": {
            "type": "object",
            "properties": {
                "analysis_data": {
                    "type": "array",
                    "description": "List of analysis results"
                },
                "dashboard_title": {
                    "type": "string",
                    "description": "Title for the dashboard",
                    "default": "Call Analysis Dashboard"
                },
                "output_path": {
                    "type": "string",
                    "description": "Output path for dashboard file",
                    "default": "dashboard.html"
                }
            },
            "required": ["analysis_data"]
        }
    }
}

# Direct tool function mapping
async def analyze_transcript_wrapper(**kwargs):
    """Wrapper for analyze_transcript tool."""
    # Remove default None values
    clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    
    # Import and call the tool function directly
    from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
    from awslabs.call_analysis_mcp_server.services.s3_service import S3Service
    
    # Initialize services
    s3_service = S3Service(region=clean_kwargs.get('aws_region', 'us-east-1'))
    analyzer = TranscriptAnalyzer()
    
    # Call the analysis function
    start_time = datetime.now()
    try:
        # Read transcript from S3
        transcript_content = s3_service.read_transcript(clean_kwargs['s3_bucket'], clean_kwargs['s3_key'])
        
        # Parse transcript into segments
        transcript_segments = analyzer.parse_transcript(transcript_content)
        
        # Perform analysis
        analysis_result = await analyzer.analyze_transcript(
            transcript_segments=transcript_segments,
            call_id=clean_kwargs['s3_key'].split('/')[-1].split('.')[0],
            analysis_options=clean_kwargs.get('analysis_options')
        )
        
        # Set metadata
        analysis_result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
        analysis_result.transcript_source = f"s3://{clean_kwargs['s3_bucket']}/{clean_kwargs['s3_key']}"
        
        # Generate output files
        base_filename = clean_kwargs['s3_key'].split('/')[-1].split('.')[0]
        output_prefix = clean_kwargs.get('output_prefix', '')
        
        if output_prefix:
            json_key = f"{output_prefix}/{base_filename}_analysis.json"
        else:
            json_key = f"{base_filename}_analysis.json"
        
        # Upload results
        json_content = analysis_result.model_dump_json(indent=2)
        json_url = s3_service.upload_analysis_json(
            content=json_content,
            bucket=clean_kwargs['output_bucket'],
            key=json_key
        )
        
        return {
            "status": "success",
            "call_id": analysis_result.call_id,
            "analysis_timestamp": analysis_result.analysis_timestamp.isoformat(),
            "processing_time_seconds": analysis_result.processing_time_seconds,
            "output_files": {
                "analysis_json": {
                    "s3_url": json_url,
                    "bucket": clean_kwargs['output_bucket'],
                    "key": json_key
                }
            },
            "summary": {
                "overall_sentiment": analysis_result.sentiment_analysis.overall_sentiment if analysis_result.sentiment_analysis else "unknown",
                "customer_satisfaction_score": analysis_result.performance_kpis.customer_satisfaction_score if analysis_result.performance_kpis else 0,
                "compliance_score": analysis_result.compliance_metrics.compliance_score if analysis_result.compliance_metrics else 0
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "processing_time_seconds": (datetime.now() - start_time).total_seconds()
        }

async def ask_analysis_question_wrapper(**kwargs):
    """Wrapper for ask_analysis_question tool."""
    # Import the Q&A function directly
    from awslabs.call_analysis_mcp_server.tools.analysis_tools import (
        _analyze_question_intent, _generate_intelligent_response
    )
    
    import os
    import json
    
    question = kwargs['question']
    report_file_path = kwargs.get('report_file_path', '/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/ai_enhanced_analysis_all_scripts_report.json')
    context_type = kwargs.get('context_type', 'auto')
    
    start_time = datetime.now()
    
    try:
        # Load the business intelligence report
        if not os.path.exists(report_file_path):
            return {
                "status": "error",
                "error_message": f"Report file not found: {report_file_path}",
                "suggestion": "Run analyze_local_scripts first to generate the report"
            }
        
        with open(report_file_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # Analyze the question to determine intent and context
        question_analysis = _analyze_question_intent(question.lower())
        
        # Generate intelligent response based on question type
        if context_type == "auto":
            context_type = question_analysis["primary_context"]
        
        response = _generate_intelligent_response(question, question_analysis, report_data, context_type)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "success",
            "question": question,
            "answer": response["answer"],
            "key_metrics": response["metrics"],
            "supporting_data": response["supporting_data"],
            "insights": response["insights"],
            "evidence": response.get("evidence", []),
            "recommendations": response.get("recommendations", []),
            "context_analyzed": context_type,
            "question_type": question_analysis["question_type"],
            "report_metadata": {
                "analysis_period": report_data.get("analysis_period", "Unknown"),
                "total_calls": report_data.get("total_calls_analyzed", 0),
                "analysis_timestamp": report_data.get("analysis_timestamp", "Unknown")
            },
            "processing_time_seconds": processing_time
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "processing_time_seconds": (datetime.now() - start_time).total_seconds()
        }

async def analyze_transcript_batch_wrapper(**kwargs):
    """Wrapper for analyze-transcript-batch tool."""
    try:
        s3_bucket = kwargs['s3_bucket']
        s3_prefix = kwargs['s3_prefix']
        output_bucket = kwargs['output_bucket']
        output_prefix = kwargs.get('output_prefix', 'batch_analysis')
        max_files = kwargs.get('max_files', 100)
        analysis_options = kwargs.get('analysis_options', None)
        aws_region = kwargs.get('aws_region', 'us-east-1')
        
        # Import the actual tool function
        from awslabs.call_analysis_mcp_server.tools.analysis_tools import batch_analysis_tool
        
        # Create a mock MCP context for the tool
        class MockMCP:
            async def error(self, message):
                print(f"Error: {message}")
        
        mcp = MockMCP()
        
        # Call the tool function
        result = await batch_analysis_tool(mcp, s3_bucket=s3_bucket, s3_prefix=s3_prefix, 
                                         output_bucket=output_bucket, output_prefix=output_prefix,
                                         max_files=max_files, analysis_options=analysis_options,
                                         aws_region=aws_region)
        
        return {
            "success": True,
            "result": result,
            "s3_bucket": s3_bucket,
            "s3_prefix": s3_prefix,
            "output_bucket": output_bucket
        }
        
    except Exception as e:
        print(f"Error in analyze_transcript_batch_wrapper: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_business_intelligence_wrapper(**kwargs):
    """Wrapper for generate-business-intelligence tool."""
    try:
        analysis_s3_urls = kwargs['analysis_s3_urls']
        output_bucket = kwargs['output_bucket']
        time_period = kwargs.get('time_period', 'Today')
        output_key = kwargs.get('output_key', 'business_intelligence.json')
        aws_region = kwargs.get('aws_region', 'us-east-1')
        
        # Import the actual tool function
        from awslabs.call_analysis_mcp_server.tools.analysis_tools import business_intelligence_tool
        
        # Create a mock MCP context for the tool
        class MockMCP:
            async def error(self, message):
                print(f"Error: {message}")
        
        mcp = MockMCP()
        
        # Call the tool function
        result = await business_intelligence_tool(mcp, analysis_s3_urls=analysis_s3_urls,
                                               output_bucket=output_bucket, time_period=time_period,
                                               output_key=output_key, aws_region=aws_region)
        
        return {
            "success": True,
            "result": result,
            "analysis_s3_urls": analysis_s3_urls,
            "output_bucket": output_bucket
        }
        
    except Exception as e:
        print(f"Error in generate_business_intelligence_wrapper: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def analyze_local_scripts_wrapper(**kwargs):
    """Wrapper for analyze-local-scripts tool."""
    try:
        scripts_folder = kwargs.get('scripts_folder', '/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts')
        script_pattern = kwargs.get('script_pattern', 'script*.json')
        output_file = kwargs.get('output_file', '/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/local_analysis_report.json')
        time_period = kwargs.get('time_period', 'Current Script Collection')
        max_scripts = kwargs.get('max_scripts', 50)
        analysis_options = kwargs.get('analysis_options', None)
        
        # Import the actual tool function
        from awslabs.call_analysis_mcp_server.tools.analysis_tools import local_scripts_analysis_tool
        
        # Create a mock MCP context for the tool
        class MockMCP:
            async def error(self, message):
                print(f"Error: {message}")
        
        mcp = MockMCP()
        
        # Call the tool function
        result = await local_scripts_analysis_tool(mcp, scripts_folder=scripts_folder,
                                                 script_pattern=script_pattern, output_file=output_file,
                                                 time_period=time_period, max_scripts=max_scripts,
                                                 analysis_options=analysis_options)
        
        return {
            "success": True,
            "result": result,
            "scripts_folder": scripts_folder,
            "output_file": output_file
        }
        
    except Exception as e:
        print(f"Error in analyze_local_scripts_wrapper: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def read_s3_transcript_wrapper(**kwargs):
    """Wrapper for read-s3-transcript tool."""
    try:
        s3_bucket = kwargs['s3_bucket']
        s3_key = kwargs['s3_key']
        aws_region = kwargs.get('aws_region', 'us-east-1')
        
        # Import the actual tool function
        from awslabs.call_analysis_mcp_server.tools.s3_tools import s3_reader_tool
        
        # Create a mock MCP context for the tool
        class MockMCP:
            async def error(self, message):
                print(f"Error: {message}")
        
        mcp = MockMCP()
        
        # Call the tool function
        result = await s3_reader_tool(mcp, s3_bucket=s3_bucket, s3_key=s3_key, aws_region=aws_region)
        
        return {
            "success": True,
            "result": result,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key
        }
        
    except Exception as e:
        print(f"Error in read_s3_transcript_wrapper: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def upload_to_s3_wrapper(**kwargs):
    """Wrapper for upload-to-s3 tool."""
    try:
        content = kwargs['content']
        s3_bucket = kwargs['s3_bucket']
        s3_key = kwargs['s3_key']
        content_type = kwargs.get('content_type', 'application/json')
        aws_region = kwargs.get('aws_region', 'us-east-1')
        
        # Import the actual tool function
        from awslabs.call_analysis_mcp_server.tools.s3_tools import s3_uploader_tool
        
        # Create a mock MCP context for the tool
        class MockMCP:
            async def error(self, message):
                print(f"Error: {message}")
        
        mcp = MockMCP()
        
        # Call the tool function
        result = await s3_uploader_tool(mcp, content=content, s3_bucket=s3_bucket, 
                                       s3_key=s3_key, content_type=content_type, aws_region=aws_region)
        
        return {
            "success": True,
            "result": result,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key
        }
        
    except Exception as e:
        print(f"Error in upload_to_s3_wrapper: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_report_wrapper(**kwargs):
    """Wrapper for generate-report tool."""
    try:
        analysis_result = kwargs['analysis_result']
        report_type = kwargs.get('report_type', 'detailed')
        
        # Import the actual tool function
        from awslabs.call_analysis_mcp_server.tools.reporting_tools import generate_report_tool
        
        # Create a mock MCP context for the tool
        class MockMCP:
            async def error(self, message):
                print(f"Error: {message}")
        
        mcp = MockMCP()
        
        # Call the tool function
        result = await generate_report_tool(mcp, analysis_result=analysis_result, report_type=report_type)
        
        return {
            "success": True,
            "result": result,
            "report_type": report_type
        }
        
    except Exception as e:
        print(f"Error in generate_report_wrapper: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def create_dashboard_wrapper(**kwargs):
    """Wrapper for create-dashboard tool."""
    try:
        analysis_data = kwargs['analysis_data']
        dashboard_title = kwargs.get('dashboard_title', 'Call Analysis Dashboard')
        output_path = kwargs.get('output_path', 'dashboard.html')
        
        # Import the actual tool function
        from awslabs.call_analysis_mcp_server.tools.reporting_tools import create_dashboard_tool
        
        # Create a mock MCP context for the tool
        class MockMCP:
            async def error(self, message):
                print(f"Error: {message}")
        
        mcp = MockMCP()
        
        # Call the tool function
        result = await create_dashboard_tool(mcp, analysis_data=analysis_data, 
                                           dashboard_title=dashboard_title, output_path=output_path)
        
        return {
            "success": True,
            "result": result,
            "dashboard_title": dashboard_title,
            "output_path": output_path
        }
        
    except Exception as e:
        print(f"Error in create_dashboard_wrapper: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Direct tool function mapping
TOOL_FUNCTIONS = {
    "analyze-transcript": analyze_transcript_wrapper,
    "analyze-transcript-batch": analyze_transcript_batch_wrapper,
    "generate-business-intelligence": generate_business_intelligence_wrapper,
    "analyze-local-scripts": analyze_local_scripts_wrapper,
    "ask-analysis-question": ask_analysis_question_wrapper,
    "read-s3-transcript": read_s3_transcript_wrapper,
    "upload-to-s3": upload_to_s3_wrapper,
    "generate-report": generate_report_wrapper,
    "create-dashboard": create_dashboard_wrapper,
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

def get_tool_function(tool_name: str):
    """Get the actual tool function for execution."""
    return TOOL_FUNCTIONS.get(tool_name)

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "service": "Call Analysis MCP HTTP Transport",
        "version": "1.0.0",
        "protocol": "mcp",
        "transport": "http",
        "status": "running",
        "mcp_version": "2024-11-05",
        "tools_count": len(TOOLS),
        "timestamp": datetime.now().isoformat(),
        "description": "AI-powered call transcript analysis with business intelligence insights"
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

@app.get("/tools")
async def get_tools():
    """REST API endpoint to list available tools."""
    tools = []
    for tool_name, tool_info in TOOLS.items():
        tools.append({
            "name": tool_name,
            "description": tool_info["description"],
            "schema": tool_info["inputSchema"]
        })
    
    return {
        "tools": tools,
        "count": len(tools),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/tools/{tool_name}")
async def call_tool_rest(tool_name: str, request: Request):
    """REST API endpoint to call a specific tool."""
    try:
        data = await request.json()
        
        # Check if tool exists
        if tool_name not in TOOLS:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        tool_info = TOOLS[tool_name]
        
        # Get tool function
        tool_func = get_tool_function(tool_name)
        if not tool_func:
            raise HTTPException(status_code=500, detail=f"Tool function for '{tool_name}' not found")
        
        # Apply defaults for missing arguments
        schema_props = tool_info["inputSchema"]["properties"]
        final_args = {}
        
        for prop_name, prop_info in schema_props.items():
            if prop_name in data:
                final_args[prop_name] = data[prop_name]
            elif "default" in prop_info:
                final_args[prop_name] = prop_info["default"]
        
        # Log the tool call
        dual_logger.info(f"🔧 REST API Tool Call: {tool_name}")
        dual_logger.debug(f"Tool arguments: {json.dumps(final_args, indent=2, default=str)}")
        
        # Call the tool function
        result = await tool_func(**final_args)
        
        # Convert result to JSON-serializable format
        if hasattr(result, 'dict'):
            result_data = result.dict()
        elif hasattr(result, '__dict__'):
            result_data = result.__dict__
        else:
            result_data = result
        
        # Log successful result
        dual_logger.info(f"✅ REST API Tool {tool_name} completed successfully")
        dual_logger.debug(f"Result type: {type(result_data)}")
        
        return {
            "result": result_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        dual_logger.error(f"❌ REST API Tool {tool_name} execution failed: {str(e)}")
        dual_logger.error(f"Exception details: {traceback.format_exc()}")
        
        print(f"Error calling tool {tool_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

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
        
        print(f"✅ Call Analysis MCP server initialized for client: {client_info.get('name', 'Unknown')}")
        
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
                    "name": "Call Analysis MCP Server",
                    "version": "1.0.0"
                },
                "instructions": """
# Call Analysis MCP Server

Provides AI-powered tools for call transcript analysis and business intelligence insights.

Available tools:
- analyze-transcript: Analyze single call transcript from S3
- analyze-transcript-batch: Batch analysis of multiple transcripts
- generate-business-intelligence: Generate management insights
- analyze-local-scripts: Analyze local script files
- ask-analysis-question: Q&A with evidence-backed answers
- read-s3-transcript: Read transcript files from S3
- upload-to-s3: Upload analysis results to S3
- generate-report: Generate markdown reports
- create-dashboard: Create interactive dashboards
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

@app.post("/mcp/request")
async def unified_mcp_request(request: Request):
    """Unified MCP request endpoint for langgraph connector compatibility."""
    try:
        data = await request.json()
        method = data.get("method", "")
        params = data.get("params", {})
        request_id = data.get("id")
        
        dual_logger.info(f"🔧 Unified MCP Request: {method}")
        dual_logger.debug(f"Request params: {json.dumps(params, indent=2, default=str)}")
        
        # Route to appropriate handler based on method
        if method == "initialize":
            return await handle_mcp_initialize(data)
        elif method == "tools/list":
            return await handle_mcp_tools_list(data)
        elif method == "tools/call":
            return await handle_mcp_tools_call(data)
        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            
    except Exception as e:
        dual_logger.error(f"❌ Unified MCP request failed: {str(e)}")
        return {
            "jsonrpc": "2.0",
            "id": data.get("id", None),
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }

@app.post("/mcp/notification")
async def mcp_notification(request: Request):
    """Handle MCP notifications."""
    try:
        data = await request.json()
        method = data.get("method", "")
        
        dual_logger.info(f"📢 MCP Notification: {method}")
        
        # For notifications, we just acknowledge them
        # No response is needed for notifications
        return JSONResponse(content={}, status_code=200)
        
    except Exception as e:
        dual_logger.error(f"❌ MCP notification failed: {str(e)}")
        return JSONResponse(content={}, status_code=500)

async def handle_mcp_initialize(data: Dict[str, Any]):
    """Handle MCP initialize request."""
    params = data.get("params", {})
    client_info = params.get("clientInfo", {})
    protocol_version = params.get("protocolVersion", "2024-11-05")
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Update server state
    server_state.update({
        "initialized": True,
        "session_id": session_id,
        "client_info": client_info
    })
    
    dual_logger.info(f"✅ MCP server initialized for client: {client_info.get('name', 'Unknown')}")
    
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
                "name": "Call Analysis MCP Server",
                "version": "1.0.0"
            }
        }
    }

async def handle_mcp_tools_list(data: Dict[str, Any]):
    """Handle MCP tools/list request."""
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

async def handle_mcp_tools_call(data: Dict[str, Any]):
    """Handle MCP tools/call request."""
    params = data.get("params", {})
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if not tool_name:
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "error": {
                "code": -32602,
                "message": "Tool name is required"
            }
        }
    
    # Get tool from registry
    tool_info = TOOLS.get(tool_name)
    if not tool_info:
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "error": {
                "code": -32601,
                "message": f"Tool '{tool_name}' not found"
            }
        }
    
    # Get tool function
    tool_func = get_tool_function(tool_name)
    if not tool_func:
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "error": {
                "code": -32603,
                "message": f"Tool function for '{tool_name}' not found"
            }
        }

    # Reset context errors
    ctx.errors = []
    
    # Log the tool call with detailed information
    logger.info(f"🔧 MCP Tool Call: {tool_name}")
    logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2, default=str)}")
    
    try:
        # Apply defaults for missing arguments
        schema_props = tool_info["inputSchema"]["properties"]
        final_args = {}
        
        for prop_name, prop_info in schema_props.items():
            if prop_name in arguments:
                final_args[prop_name] = arguments[prop_name]
            elif "default" in prop_info:
                final_args[prop_name] = prop_info["default"]
        
        result = await tool_func(**final_args)
        
        # Convert result to JSON-serializable format
        if hasattr(result, 'dict'):
            result_data = result.dict()
        elif hasattr(result, '__dict__'):
            result_data = result.__dict__
        else:
            result_data = result
        
        # Log the successful result
        logger.info(f"✅ Tool {tool_name} completed successfully")
        logger.debug(f"Tool result type: {type(result_data)}")
        
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
        
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "error": {
                "code": -32603,
                "message": error_msg
            }
        }

@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    """Call an MCP tool (legacy endpoint for compatibility)."""
    try:
        data = await request.json()
        return await handle_mcp_tools_call(data)
        
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": data.get("id", None),
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }

if __name__ == "__main__":
    dual_logger.info("🚀 Starting Call Analysis MCP HTTP Transport Server...")
    dual_logger.info(f"📡 Server will be available at: http://0.0.0.0:{args.port}")
    dual_logger.info(f"🔗 MCP Server Info: http://0.0.0.0:{args.port}/mcp/server/info")
    dual_logger.info(f"🏥 Health check: http://0.0.0.0:{args.port}/health")
    dual_logger.info(f"📋 Tools list: http://0.0.0.0:{args.port}/tools")
    dual_logger.info(f"🔧 Available tools: {', '.join(TOOLS.keys())}")
    
    print("🚀 Starting Call Analysis MCP HTTP Transport Server...")
    print(f"📡 Server will be available at: http://0.0.0.0:{args.port}")
    print(f"🔗 MCP Server Info: http://0.0.0.0:{args.port}/")
    print(f"🏥 Health check: http://0.0.0.0:{args.port}/health")
    print(f"📋 Tools list: http://0.0.0.0:{args.port}/tools")
    print(f"🔧 Available tools: {', '.join(TOOLS.keys())}")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        access_log=True,
        log_level=LOG_LEVEL.lower()
    ) 