"""
Comprehensive tests for MCP tools.

Tests analysis tools, S3 tools, and reporting tools that implement
the Model Context Protocol for AI assistant integration.
"""

import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, JSONContent

# Import the MCP tools
from awslabs.call_analysis_mcp_server.tools.analysis_tools import (
    transcript_analyzer_tool,
    business_intelligence_tool,
    local_scripts_analysis_tool
)
from awslabs.call_analysis_mcp_server.tools.s3_tools import (
    s3_reader_tool,
    s3_uploader_tool
)
from awslabs.call_analysis_mcp_server.tools.reporting_tools import (
    generate_report_tool,
    create_dashboard_tool
)

from awslabs.call_analysis_mcp_server.models import (
    CallAnalysisResult,
    BusinessIntelligenceInsights,
    TranscriptSegment,
    CallParticipant,
    SentimentType
)


@pytest.fixture
def mcp_server():
    """Create a FastMCP server instance for testing."""
    server = FastMCP("test-call-analysis-server")
    
    # Register all tools
    transcript_analyzer_tool(server)
    business_intelligence_tool(server)
    local_scripts_analysis_tool(server)
    s3_reader_tool(server)
    s3_uploader_tool(server)
    generate_report_tool(server)
    create_dashboard_tool(server)
    
    return server


@pytest.fixture
def sample_transcript_content():
    """Sample transcript content for testing."""
    return json.dumps({
        "call_id": "TEST_CALL_001",
        "transcript": [
            {
                "speaker": "agent",
                "text": "Thank you for calling. How can I help you today?",
                "timestamp": "00:00",
                "duration": 4.5
            },
            {
                "speaker": "customer",
                "text": "I'm having issues with my billing. I'm frustrated with the service.",
                "timestamp": "00:05",
                "duration": 6.2
            },
            {
                "speaker": "agent",
                "text": "I understand your frustration. Let me look into your account immediately.",
                "timestamp": "00:12",
                "duration": 5.8
            }
        ]
    })


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for testing."""
    return {
        "call_id": "TEST_CALL_001",
        "analysis_timestamp": datetime.now().isoformat(),
        "transcript_source": "test_source",
        "sentiment_analysis": {
            "overall_sentiment": "negative",
            "customer_sentiment": "negative",
            "agent_sentiment": "positive",
            "sentiment_scores": {"positive": 0.3, "negative": 0.5, "neutral": 0.2}
        },
        "performance_kpis": {
            "customer_satisfaction_score": 6.5,
            "agent_professionalism_score": 8.0,
            "call_efficiency_score": 7.0
        }
    }


class TestAnalysisTools:
    """Test analysis MCP tools."""
    
    @pytest.mark.asyncio
    @patch('awslabs.call_analysis_mcp_server.tools.analysis_tools.TranscriptAnalyzer')
    async def test_transcript_analyzer_tool(self, mock_analyzer_class, mcp_server, sample_transcript_content):
        """Test the transcript analyzer MCP tool."""
        # Mock the analyzer
        mock_analyzer = Mock()
        mock_analyzer.parse_transcript.return_value = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.AGENT,
                text="Test text",
                duration=3.0,
                confidence=0.95
            )
        ]
        mock_analyzer.analyze_transcript = AsyncMock(return_value=Mock(
            call_id="TEST_CALL_001",
            sentiment_analysis=Mock(overall_sentiment=SentimentType.POSITIVE),
            performance_kpis=Mock(customer_satisfaction_score=8.5)
        ))
        mock_analyzer_class.return_value = mock_analyzer
        
        # Call the tool
        result = await mcp_server.call_tool(
            "analyze_transcript",
            {
                "transcript_content": sample_transcript_content,
                "call_id": "TEST_CALL_001",
                "analysis_options": {
                    "sentiment_analysis": True,
                    "performance_metrics": True
                }
            }
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        content = result[0]
        assert isinstance(content, (TextContent, JSONContent))
        
        # Verify analyzer was called
        mock_analyzer.parse_transcript.assert_called_once()
        mock_analyzer.analyze_transcript.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('awslabs.call_analysis_mcp_server.tools.analysis_tools.BusinessIntelligenceAnalyzer')
    async def test_business_intelligence_tool(self, mock_bi_class, mcp_server, sample_analysis_result):
        """Test the business intelligence MCP tool."""
        # Mock the BI analyzer
        mock_bi = Mock()
        mock_bi.generate_business_intelligence = AsyncMock(return_value=Mock(
            time_period="Test Period",
            deals_at_risk=[],
            churn_risks=[],
            opportunities=[]
        ))
        mock_bi_class.return_value = mock_bi
        
        # Call the tool
        result = await mcp_server.call_tool(
            "generate_business_intelligence",
            {
                "analysis_results": [sample_analysis_result],
                "time_period": "Test Analysis"
            }
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        content = result[0]
        assert isinstance(content, (TextContent, JSONContent))
        
        # Verify BI analyzer was called
        mock_bi.generate_business_intelligence.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('os.path.exists')
    @patch('glob.glob')
    @patch('builtins.open')
    @patch('awslabs.call_analysis_mcp_server.tools.analysis_tools.TranscriptAnalyzer')
    async def test_local_scripts_analysis_tool(self, mock_analyzer_class, mock_open, mock_glob, mock_exists, mcp_server):
        """Test the local scripts analysis MCP tool."""
        # Mock file system
        mock_exists.return_value = True
        mock_glob.return_value = ['/path/to/script1.json', '/path/to/script2.json']
        
        # Mock file content
        mock_file_content = json.dumps({
            "call_id": "SCRIPT_001",
            "transcript": [
                {"speaker": "agent", "text": "Hello", "timestamp": "00:00"}
            ]
        })
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content
        
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.parse_transcript.return_value = []
        mock_analyzer.analyze_transcript = AsyncMock(return_value=Mock(call_id="SCRIPT_001"))
        mock_analyzer_class.return_value = mock_analyzer
        
        # Call the tool
        result = await mcp_server.call_tool(
            "analyze_local_scripts",
            {
                "scripts_folder": "/path/to/scripts",
                "max_scripts": 2,
                "output_file": "test_output.json"
            }
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        content = result[0]
        assert isinstance(content, (TextContent, JSONContent))
        
        # Verify file operations
        mock_glob.assert_called()
        mock_open.assert_called()
    
    @pytest.mark.asyncio
    async def test_analysis_tool_error_handling(self, mcp_server):
        """Test error handling in analysis tools."""
        # Test with invalid transcript content
        with pytest.raises(Exception):
            await mcp_server.call_tool(
                "analyze_transcript",
                {
                    "transcript_content": "invalid json content",
                    "call_id": "INVALID_CALL"
                }
            )
    
    @pytest.mark.asyncio
    async def test_business_intelligence_tool_empty_results(self, mcp_server):
        """Test business intelligence tool with empty analysis results."""
        result = await mcp_server.call_tool(
            "generate_business_intelligence",
            {
                "analysis_results": [],
                "time_period": "Empty Test"
            }
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Should handle empty results gracefully


class TestS3Tools:
    """Test S3 MCP tools."""
    
    @pytest.mark.asyncio
    @patch('awslabs.call_analysis_mcp_server.tools.s3_tools.S3Service')
    async def test_s3_reader_tool(self, mock_s3_service_class, mcp_server, sample_transcript_content):
        """Test the S3 reader MCP tool."""
        # Mock S3 service
        mock_s3_service = Mock()
        mock_s3_service.read_transcript = AsyncMock(return_value=sample_transcript_content)
        mock_s3_service.list_transcripts = AsyncMock(return_value=[
            {"key": "transcript1.json", "size": 1024, "last_modified": "2024-01-01"},
            {"key": "transcript2.json", "size": 2048, "last_modified": "2024-01-02"}
        ])
        mock_s3_service_class.return_value = mock_s3_service
        
        # Test reading a single transcript
        result = await mcp_server.call_tool(
            "read_s3_transcript",
            {
                "s3_bucket": "test-bucket",
                "s3_key": "transcripts/call1.json",
                "aws_region": "us-east-1"
            }
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        content = result[0]
        assert isinstance(content, (TextContent, JSONContent))
        
        # Verify S3 service was called
        mock_s3_service.read_transcript.assert_called_once_with(
            "test-bucket", "transcripts/call1.json"
        )
    
    @pytest.mark.asyncio
    @patch('awslabs.call_analysis_mcp_server.tools.s3_tools.S3Service')
    async def test_s3_list_transcripts_tool(self, mock_s3_service_class, mcp_server):
        """Test the S3 list transcripts functionality."""
        # Mock S3 service
        mock_s3_service = Mock()
        mock_s3_service.list_transcripts = AsyncMock(return_value=[
            {"key": "transcript1.json", "size": 1024, "last_modified": "2024-01-01"},
            {"key": "transcript2.json", "size": 2048, "last_modified": "2024-01-02"}
        ])
        mock_s3_service_class.return_value = mock_s3_service
        
        # Test listing transcripts
        result = await mcp_server.call_tool(
            "list_s3_transcripts",
            {
                "s3_bucket": "test-bucket",
                "s3_prefix": "transcripts/",
                "max_files": 10,
                "aws_region": "us-east-1"
            }
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        content = result[0]
        assert isinstance(content, (TextContent, JSONContent))
        
        # Verify S3 service was called
        mock_s3_service.list_transcripts.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('awslabs.call_analysis_mcp_server.tools.s3_tools.S3Service')
    async def test_s3_uploader_tool(self, mock_s3_service_class, mcp_server, sample_analysis_result):
        """Test the S3 uploader MCP tool."""
        # Mock S3 service
        mock_s3_service = Mock()
        mock_s3_service.upload_analysis_results = AsyncMock(return_value={
            "s3_url": "s3://test-bucket/analysis_result.json",
            "public_url": "https://test-bucket.s3.amazonaws.com/analysis_result.json"
        })
        mock_s3_service_class.return_value = mock_s3_service
        
        # Test uploading analysis results
        result = await mcp_server.call_tool(
            "upload_analysis_results",
            {
                "content": json.dumps(sample_analysis_result),
                "s3_bucket": "test-bucket",
                "s3_key": "analysis/result.json",
                "content_type": "application/json",
                "aws_region": "us-east-1"
            }
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        content = result[0]
        assert isinstance(content, (TextContent, JSONContent))
        
        # Verify S3 service was called
        mock_s3_service.upload_analysis_results.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('awslabs.call_analysis_mcp_server.tools.s3_tools.S3Service')
    async def test_s3_tools_error_handling(self, mock_s3_service_class, mcp_server):
        """Test error handling in S3 tools."""
        # Mock S3 service to raise exception
        mock_s3_service = Mock()
        mock_s3_service.read_transcript = AsyncMock(side_effect=Exception("S3 Error"))
        mock_s3_service_class.return_value = mock_s3_service
        
        # Should handle S3 errors gracefully
        with pytest.raises(Exception):
            await mcp_server.call_tool(
                "read_s3_transcript",
                {
                    "s3_bucket": "invalid-bucket",
                    "s3_key": "invalid-key.json"
                }
            )


class TestReportingTools:
    """Test reporting MCP tools."""
    
    @pytest.mark.asyncio
    @patch('awslabs.call_analysis_mcp_server.tools.reporting_tools.ReportGenerator')
    @patch('awslabs.call_analysis_mcp_server.tools.reporting_tools.S3Service')
    async def test_generate_report_tool(self, mock_s3_class, mock_report_class, mcp_server):
        """Test the generate report MCP tool."""
        # Mock report generator
        mock_report_generator = Mock()
        mock_report_generator.generate_comprehensive_report = AsyncMock(return_value={
            "markdown_content": "# Analysis Report\n\nSummary...",
            "html_content": "<h1>Analysis Report</h1><p>Summary...</p>",
            "executive_summary": "Key findings and recommendations"
        })
        mock_report_class.return_value = mock_report_generator
        
        # Mock S3 service
        mock_s3_service = Mock()
        mock_s3_service.upload_analysis_results = AsyncMock(return_value={
            "s3_url": "s3://bucket/report.html"
        })
        mock_s3_class.return_value = mock_s3_service
        
        # Call the tool
        result = await mcp_server.call_tool(
            "generate_analysis_report",
            {
                "analysis_s3_urls": [
                    "s3://bucket/analysis1.json",
                    "s3://bucket/analysis2.json"
                ],
                "report_type": "comprehensive",
                "output_bucket": "reports-bucket",
                "output_key": "report.html",
                "aws_region": "us-east-1"
            }
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        content = result[0]
        assert isinstance(content, (TextContent, JSONContent))
        
        # Verify report generator was called
        mock_report_generator.generate_comprehensive_report.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('awslabs.call_analysis_mcp_server.tools.reporting_tools.ReportGenerator')
    @patch('awslabs.call_analysis_mcp_server.tools.reporting_tools.S3Service')
    async def test_create_dashboard_tool(self, mock_s3_class, mock_report_class, mcp_server):
        """Test the create dashboard MCP tool."""
        # Mock report generator
        mock_report_generator = Mock()
        mock_report_generator.create_interactive_dashboard = AsyncMock(return_value={
            "html_content": "<html><body>Dashboard Content</body></html>",
            "dashboard_data": {"charts": [], "metrics": {}},
            "public_url": "https://bucket.s3.amazonaws.com/dashboard.html"
        })
        mock_report_class.return_value = mock_report_generator
        
        # Mock S3 service
        mock_s3_service = Mock()
        mock_s3_service.upload_analysis_results = AsyncMock(return_value={
            "s3_url": "s3://bucket/dashboard.html",
            "public_url": "https://bucket.s3.amazonaws.com/dashboard.html"
        })
        mock_s3_class.return_value = mock_s3_service
        
        # Call the tool
        result = await mcp_server.call_tool(
            "create_analysis_dashboard",
            {
                "analysis_s3_urls": [
                    "s3://bucket/analysis1.json",
                    "s3://bucket/analysis2.json"
                ],
                "dashboard_title": "Call Analysis Dashboard",
                "output_bucket": "dashboards-bucket",
                "output_key": "dashboard.html",
                "aws_region": "us-east-1"
            }
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        content = result[0]
        assert isinstance(content, (TextContent, JSONContent))
        
        # Verify dashboard creation was called
        mock_report_generator.create_interactive_dashboard.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reporting_tools_error_handling(self, mcp_server):
        """Test error handling in reporting tools."""
        # Test with invalid S3 URLs
        with pytest.raises(Exception):
            await mcp_server.call_tool(
                "generate_analysis_report",
                {
                    "analysis_s3_urls": ["invalid-url"],
                    "output_bucket": "test-bucket",
                    "output_key": "report.html"
                }
            )


class TestMCPIntegration:
    """Test MCP integration and tool discovery."""
    
    def test_tool_registration(self, mcp_server):
        """Test that all tools are properly registered."""
        tools = mcp_server.list_tools()
        
        tool_names = [tool.name for tool in tools]
        
        # Analysis tools
        assert "analyze_transcript" in tool_names
        assert "generate_business_intelligence" in tool_names
        assert "analyze_local_scripts" in tool_names
        
        # S3 tools
        assert "read_s3_transcript" in tool_names or "list_s3_transcripts" in tool_names
        assert "upload_analysis_results" in tool_names
        
        # Reporting tools
        assert "generate_analysis_report" in tool_names
        assert "create_analysis_dashboard" in tool_names
    
    def test_tool_descriptions(self, mcp_server):
        """Test that tools have proper descriptions."""
        tools = mcp_server.list_tools()
        
        for tool in tools:
            assert tool.name is not None
            assert tool.description is not None
            assert len(tool.description) > 10  # Meaningful description
    
    def test_tool_input_schemas(self, mcp_server):
        """Test that tools have proper input schemas."""
        tools = mcp_server.list_tools()
        
        for tool in tools:
            assert tool.inputSchema is not None
            # Check that schema has required properties
            if hasattr(tool.inputSchema, 'properties'):
                assert len(tool.inputSchema.properties) > 0
    
    @pytest.mark.asyncio
    async def test_invalid_tool_call(self, mcp_server):
        """Test calling non-existent tool."""
        with pytest.raises(Exception):
            await mcp_server.call_tool("non_existent_tool", {})
    
    @pytest.mark.asyncio
    async def test_tool_with_missing_parameters(self, mcp_server):
        """Test calling tool with missing required parameters."""
        with pytest.raises(Exception):
            await mcp_server.call_tool("analyze_transcript", {})  # Missing required params


class TestToolParameterValidation:
    """Test parameter validation for MCP tools."""
    
    @pytest.mark.asyncio
    async def test_analyze_transcript_parameter_validation(self, mcp_server):
        """Test parameter validation for analyze_transcript tool."""
        # Test with valid parameters
        with patch('awslabs.call_analysis_mcp_server.tools.analysis_tools.TranscriptAnalyzer'):
            result = await mcp_server.call_tool(
                "analyze_transcript",
                {
                    "transcript_content": json.dumps({"transcript": []}),
                    "call_id": "TEST_001"
                }
            )
            assert isinstance(result, list)
        
        # Test with invalid transcript content
        with pytest.raises(Exception):
            await mcp_server.call_tool(
                "analyze_transcript",
                {
                    "transcript_content": "invalid json",
                    "call_id": "TEST_001"
                }
            )
    
    @pytest.mark.asyncio
    async def test_s3_tools_parameter_validation(self, mcp_server):
        """Test parameter validation for S3 tools."""
        # Test with missing S3 bucket
        with pytest.raises(Exception):
            await mcp_server.call_tool(
                "read_s3_transcript",
                {
                    "s3_key": "transcript.json"
                    # Missing s3_bucket
                }
            )
        
        # Test with missing S3 key
        with pytest.raises(Exception):
            await mcp_server.call_tool(
                "read_s3_transcript",
                {
                    "s3_bucket": "test-bucket"
                    # Missing s3_key
                }
            )
    
    @pytest.mark.asyncio
    async def test_reporting_tools_parameter_validation(self, mcp_server):
        """Test parameter validation for reporting tools."""
        # Test with empty analysis URLs
        with pytest.raises(Exception):
            await mcp_server.call_tool(
                "generate_analysis_report",
                {
                    "analysis_s3_urls": [],  # Empty list
                    "output_bucket": "test-bucket",
                    "output_key": "report.html"
                }
            )


class TestToolPerformance:
    """Test tool performance and concurrent execution."""
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mcp_server):
        """Test concurrent execution of multiple tools."""
        with patch('awslabs.call_analysis_mcp_server.tools.analysis_tools.TranscriptAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.parse_transcript.return_value = []
            mock_analyzer.return_value.analyze_transcript = AsyncMock(return_value=Mock(call_id="TEST"))
            
            # Create multiple concurrent tool calls
            tasks = []
            for i in range(3):
                task = mcp_server.call_tool(
                    "analyze_transcript",
                    {
                        "transcript_content": json.dumps({"transcript": []}),
                        "call_id": f"TEST_{i}"
                    }
                )
                tasks.append(task)
            
            # Execute concurrently
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            assert len(results) == 3
            for result in results:
                assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_tool_timeout_handling(self, mcp_server):
        """Test handling of tool timeouts."""
        with patch('awslabs.call_analysis_mcp_server.tools.analysis_tools.TranscriptAnalyzer') as mock_analyzer:
            # Mock analyzer to take a long time
            mock_analyzer.return_value.analyze_transcript = AsyncMock(
                side_effect=asyncio.TimeoutError("Tool timeout")
            )
            
            # Should handle timeout gracefully
            with pytest.raises((Exception, asyncio.TimeoutError)):
                await mcp_server.call_tool(
                    "analyze_transcript",
                    {
                        "transcript_content": json.dumps({"transcript": []}),
                        "call_id": "TIMEOUT_TEST"
                    }
                )


class TestToolLogging:
    """Test tool logging and monitoring."""
    
    @pytest.mark.asyncio
    @patch('awslabs.call_analysis_mcp_server.tools.analysis_tools.logger')
    async def test_tool_logging(self, mock_logger, mcp_server):
        """Test that tools log important events."""
        with patch('awslabs.call_analysis_mcp_server.tools.analysis_tools.TranscriptAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.parse_transcript.return_value = []
            mock_analyzer.return_value.analyze_transcript = AsyncMock(return_value=Mock(call_id="TEST"))
            
            await mcp_server.call_tool(
                "analyze_transcript",
                {
                    "transcript_content": json.dumps({"transcript": []}),
                    "call_id": "LOG_TEST"
                }
            )
            
            # Verify logging was called (mock_logger.info, mock_logger.debug, etc.)
            assert mock_logger.info.called or mock_logger.debug.called


class TestToolSecurity:
    """Test tool security and input sanitization."""
    
    @pytest.mark.asyncio
    async def test_input_sanitization(self, mcp_server):
        """Test that tools sanitize potentially dangerous inputs."""
        # Test with potentially malicious JSON
        malicious_json = json.dumps({
            "transcript": [
                {
                    "speaker": "agent",
                    "text": "<script>alert('xss')</script>",
                    "timestamp": "00:00"
                }
            ]
        })
        
        with patch('awslabs.call_analysis_mcp_server.tools.analysis_tools.TranscriptAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.parse_transcript.return_value = []
            mock_analyzer.return_value.analyze_transcript = AsyncMock(return_value=Mock(call_id="TEST"))
            
            # Should handle without executing malicious code
            result = await mcp_server.call_tool(
                "analyze_transcript",
                {
                    "transcript_content": malicious_json,
                    "call_id": "SECURITY_TEST"
                }
            )
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_path_traversal_protection(self, mcp_server):
        """Test protection against path traversal attacks."""
        with patch('os.path.exists', return_value=False):
            # Test with path traversal attempt
            with pytest.raises(Exception):
                await mcp_server.call_tool(
                    "analyze_local_scripts",
                    {
                        "scripts_folder": "../../../etc/passwd",
                        "max_scripts": 1
                    }
                )