"""
Comprehensive end-to-end integration tests.

Tests the complete workflow from transcript input through analysis
to business intelligence insights and reporting, including MCP protocol
integration and HTTP server functionality.
"""

import pytest
import json
import asyncio
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from fastapi.testclient import TestClient

# Import all the components for integration testing
from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
from awslabs.call_analysis_mcp_server.services.business_intelligence import BusinessIntelligenceAnalyzer
from awslabs.call_analysis_mcp_server.services.ai_analyzer import AIAnalyzer
from awslabs.call_analysis_mcp_server.services.s3_service import S3Service
from awslabs.call_analysis_mcp_server.services.report_generator import ReportGenerator

from awslabs.call_analysis_mcp_server.models import (
    CallAnalysisResult,
    BusinessIntelligenceInsights,
    TranscriptSegment,
    CallParticipant,
    SentimentType,
    RiskLevel
)

# Import MCP tools for integration testing
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


@pytest.fixture
def comprehensive_transcript():
    """Comprehensive test transcript with multiple business indicators."""
    return json.dumps({
        "call_id": "INTEGRATION_TEST_001",
        "metadata": {
            "date": "2024-01-15",
            "agent": "John Smith",
            "customer": "StarNet Solutions",
            "account_value": 50000
        },
        "transcript": [
            {
                "speaker": "agent",
                "text": "Thank you for calling StarNet Solutions support. My name is John. How can I help you today?",
                "timestamp": "00:00",
                "duration": 6.0
            },
            {
                "speaker": "customer",
                "text": "Hi John. I'm really frustrated with our current service. It's been down three times this month and it's costing us money.",
                "timestamp": "00:06",
                "duration": 8.0
            },
            {
                "speaker": "agent", 
                "text": "I completely understand your frustration, and I sincerely apologize for the service interruptions. Let me look into your account right away to see what's happening.",
                "timestamp": "00:14",
                "duration": 10.0
            },
            {
                "speaker": "customer",
                "text": "The price we're paying doesn't justify this level of service. We're seriously considering switching to TechCorp - they're offering us a 30% discount.",
                "timestamp": "00:24",
                "duration": 9.0
            },
            {
                "speaker": "agent",
                "text": "I want to make this right for you. Let me escalate this to our technical team immediately and see what we can do about pricing. We value your business greatly.",
                "timestamp": "00:33",
                "duration": 11.0
            },
            {
                "speaker": "customer",
                "text": "Well, we are expanding our operations next quarter and will need additional services. If you can resolve these issues, we might consider staying.",
                "timestamp": "00:44",
                "duration": 9.0
            },
            {
                "speaker": "agent",
                "text": "That's excellent news about your expansion! I'd love to discuss how we can support your growth. Let me connect you with our account manager for those additional services.",
                "timestamp": "00:53",
                "duration": 10.0
            },
            {
                "speaker": "customer",
                "text": "Okay, but first fix the reliability issues. We can't afford more downtime during our busy season.",
                "timestamp": "01:03",
                "duration": 7.0
            },
            {
                "speaker": "agent",
                "text": "Absolutely. I'm creating a priority ticket right now and our senior technical team will address this within the next 2 hours. You have my personal commitment on this.",
                "timestamp": "01:10",
                "duration": 12.0
            }
        ]
    })


@pytest.fixture
def mcp_server_with_tools():
    """Create a fully configured MCP server with all tools."""
    server = FastMCP("integration-test-server")
    
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
def mock_s3_environment():
    """Mock S3 environment for integration testing."""
    with patch('boto3.client') as mock_boto:
        mock_client = Mock()
        
        # Mock S3 operations
        mock_client.get_object.return_value = {
            'Body': Mock()
        }
        mock_client.put_object.return_value = {}
        mock_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'transcript1.json', 'Size': 1024, 'LastModified': datetime.now()},
                {'Key': 'transcript2.json', 'Size': 2048, 'LastModified': datetime.now()}
            ]
        }
        mock_client.head_object.return_value = {'ContentLength': 1024}
        
        mock_boto.return_value = mock_client
        yield mock_client


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_transcript_analysis_workflow(self, comprehensive_transcript, mock_s3_environment):
        """Test complete workflow from transcript to analysis results."""
        # Setup mock S3 content
        mock_s3_environment.get_object.return_value['Body'].read.return_value = comprehensive_transcript.encode('utf-8')
        
        # Initialize components
        s3_service = S3Service()
        transcript_analyzer = TranscriptAnalyzer()
        
        # Step 1: Read transcript from S3
        transcript_content = s3_service.read_transcript('test-bucket', 'call.json')
        assert transcript_content == comprehensive_transcript
        
        # Step 2: Parse transcript
        segments = transcript_analyzer.parse_transcript(transcript_content)
        assert len(segments) > 0
        assert isinstance(segments[0], TranscriptSegment)
        
        # Step 3: Analyze transcript
        analysis_result = await transcript_analyzer.analyze_transcript(
            transcript_segments=segments,
            call_id="INTEGRATION_TEST_001",
            analysis_options={
                "sentiment_analysis": True,
                "performance_metrics": True,
                "compliance_check": True,
                "conversation_flow": True,
                "topic_extraction": True
            }
        )
        
        # Verify analysis result
        assert isinstance(analysis_result, CallAnalysisResult)
        assert analysis_result.call_id == "INTEGRATION_TEST_001"
        assert analysis_result.sentiment_analysis is not None
        assert analysis_result.performance_kpis is not None
        
        # Step 4: Upload analysis results
        analysis_json = analysis_result.model_dump_json()
        upload_result = s3_service.upload_analysis_results(
            content=analysis_json,
            bucket='results-bucket',
            key='analysis.json'
        )
        
        assert 's3_url' in upload_result
        assert upload_result['s3_url'] == 's3://results-bucket/analysis.json'
    
    @pytest.mark.asyncio
    async def test_business_intelligence_generation_workflow(self, comprehensive_transcript, mock_s3_environment):
        """Test business intelligence generation from analysis results."""
        # Setup transcript analysis
        mock_s3_environment.get_object.return_value['Body'].read.return_value = comprehensive_transcript.encode('utf-8')
        
        transcript_analyzer = TranscriptAnalyzer()
        bi_analyzer = BusinessIntelligenceAnalyzer()
        
        # Analyze transcript
        segments = transcript_analyzer.parse_transcript(comprehensive_transcript)
        analysis_result = await transcript_analyzer.analyze_transcript(
            transcript_segments=segments,
            call_id="INTEGRATION_TEST_001",
            analysis_options={"sentiment_analysis": True, "performance_metrics": True}
        )
        
        # Generate business intelligence
        bi_insights = bi_analyzer.generate_business_intelligence(
            analysis_results=[analysis_result],
            transcript_segments_list=[segments],
            time_period="Integration Test"
        )
        
        # Verify BI insights
        assert isinstance(bi_insights, BusinessIntelligenceInsights)
        assert bi_insights.time_period == "Integration Test"
        assert isinstance(bi_insights.deals_at_risk, list)
        assert isinstance(bi_insights.churn_risks, list)
        assert isinstance(bi_insights.opportunities, list)
        
        # Should detect deal risks from the transcript
        if len(bi_insights.deals_at_risk) > 0:
            deal_risk = bi_insights.deals_at_risk[0]
            assert deal_risk.account_name is not None
            assert deal_risk.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Should detect opportunities from the transcript
        if len(bi_insights.opportunities) > 0:
            opportunity = bi_insights.opportunities[0]
            assert opportunity.opportunity_type is not None
            assert 0.0 <= opportunity.confidence_score <= 1.0


class TestMCPToolsIntegration:
    """Test MCP tools integration."""
    
    @pytest.mark.asyncio
    async def test_mcp_transcript_analysis_tool(self, mcp_server_with_tools, comprehensive_transcript, mock_s3_environment):
        """Test MCP transcript analysis tool end-to-end."""
        # Setup mock S3
        mock_s3_environment.get_object.return_value['Body'].read.return_value = comprehensive_transcript.encode('utf-8')
        
        # Call MCP tool
        result = await mcp_server_with_tools.call_tool(
            "analyze_transcript",
            {
                "s3_bucket": "test-bucket",
                "s3_key": "transcripts/call.json",
                "output_bucket": "results-bucket",
                "output_prefix": "analysis",
                "analysis_options": {
                    "sentiment_analysis": True,
                    "performance_metrics": True,
                    "compliance_check": True
                }
            }
        )
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Result should contain analysis information
        content = result[0]
        if hasattr(content, 'text'):
            assert "analysis" in content.text.lower() or "complete" in content.text.lower()
    
    @pytest.mark.asyncio
    async def test_mcp_business_intelligence_tool(self, mcp_server_with_tools, mock_s3_environment):
        """Test MCP business intelligence tool end-to-end."""
        # Mock analysis result
        analysis_result = {
            "call_id": "TEST_001",
            "sentiment_analysis": {
                "overall_sentiment": "negative",
                "customer_sentiment": "negative"
            },
            "performance_kpis": {
                "customer_satisfaction_score": 4.0
            }
        }
        
        # Call MCP tool
        result = await mcp_server_with_tools.call_tool(
            "generate_business_intelligence",
            {
                "analysis_results": [analysis_result],
                "time_period": "Test Period"
            }
        )
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_mcp_local_scripts_analysis(self, mcp_server_with_tools):
        """Test MCP local scripts analysis tool."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test script files
            script1_path = os.path.join(temp_dir, "script1.json")
            script2_path = os.path.join(temp_dir, "script2.json")
            
            script_content = {
                "call_id": "LOCAL_001",
                "transcript": [
                    {"speaker": "agent", "text": "Hello", "timestamp": "00:00"},
                    {"speaker": "customer", "text": "Hi there", "timestamp": "00:03"}
                ]
            }
            
            with open(script1_path, 'w') as f:
                json.dump(script_content, f)
            with open(script2_path, 'w') as f:
                json.dump(script_content, f)
            
            # Call MCP tool
            result = await mcp_server_with_tools.call_tool(
                "analyze_local_scripts",
                {
                    "scripts_folder": temp_dir,
                    "max_scripts": 2,
                    "output_file": os.path.join(temp_dir, "output.json")
                }
            )
            
            # Verify result
            assert isinstance(result, list)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_mcp_s3_tools_integration(self, mcp_server_with_tools, mock_s3_environment, comprehensive_transcript):
        """Test MCP S3 tools integration."""
        # Setup mock S3
        mock_s3_environment.get_object.return_value['Body'].read.return_value = comprehensive_transcript.encode('utf-8')
        
        # Test S3 reader tool
        read_result = await mcp_server_with_tools.call_tool(
            "list_s3_transcripts",
            {
                "s3_bucket": "test-bucket",
                "s3_prefix": "transcripts/",
                "max_files": 10
            }
        )
        
        assert isinstance(read_result, list)
        assert len(read_result) > 0
        
        # Test S3 uploader tool
        upload_result = await mcp_server_with_tools.call_tool(
            "upload_analysis_results",
            {
                "content": '{"test": "data"}',
                "s3_bucket": "results-bucket",
                "s3_key": "test.json",
                "content_type": "application/json"
            }
        )
        
        assert isinstance(upload_result, list)
        assert len(upload_result) > 0


class TestHTTPServerIntegration:
    """Test HTTP server integration with MCP tools."""
    
    @pytest.fixture
    def http_client(self):
        """Create HTTP client for testing."""
        from mcp_http_server import app
        return TestClient(app)
    
    def test_health_endpoint_integration(self, http_client):
        """Test health endpoint integration."""
        response = http_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "available_tools" in data
        assert data["available_tools"] > 0
    
    @patch('mcp_http_server.mcp_server')
    def test_mcp_protocol_integration(self, mock_mcp_server, http_client):
        """Test MCP protocol integration through HTTP."""
        # Mock MCP server response
        mock_mcp_server.handle_request = AsyncMock(return_value={
            "tools": [
                {
                    "name": "analyze_transcript",
                    "description": "Analyze call transcript",
                    "inputSchema": {"type": "object"}
                }
            ]
        })
        
        # Send MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "integration-test-1",
            "method": "tools/list"
        }
        
        response = http_client.post("/mcp", json=mcp_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "integration-test-1"
        assert "result" in data
    
    @patch('mcp_http_server.mcp_server')
    def test_tool_execution_through_http(self, mock_mcp_server, http_client, comprehensive_transcript):
        """Test tool execution through HTTP endpoint."""
        # Mock tool execution result
        mock_mcp_server.handle_request = AsyncMock(return_value={
            "content": [
                {
                    "type": "text",
                    "text": "Analysis completed successfully"
                }
            ]
        })
        
        # Send tool execution request
        tool_request = {
            "jsonrpc": "2.0",
            "id": "tool-exec-1",
            "method": "tools/call",
            "params": {
                "name": "analyze_transcript",
                "arguments": {
                    "transcript_content": comprehensive_transcript,
                    "call_id": "HTTP_TEST_001"
                }
            }
        }
        
        response = http_client.post("/mcp", json=tool_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "tool-exec-1"
        assert "result" in data
        assert "content" in data["result"]


class TestAIIntegration:
    """Test AI-powered features integration."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI')
    async def test_ai_enhanced_analysis_integration(self, mock_openai, comprehensive_transcript):
        """Test AI-enhanced analysis integration."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "overall_sentiment": "negative",
            "confidence": 0.85,
            "risk_indicators": [
                {
                    "type": "churn_risk",
                    "severity": "high",
                    "evidence": "Customer mentioned switching to competitor"
                }
            ]
        })
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Initialize AI analyzer
        ai_analyzer = AIAnalyzer()
        ai_analyzer.client = mock_client
        ai_analyzer.api_available = True
        
        # Parse transcript
        transcript_analyzer = TranscriptAnalyzer()
        segments = transcript_analyzer.parse_transcript(comprehensive_transcript)
        
        # Test AI-enhanced sentiment analysis
        enhanced_sentiment = await ai_analyzer.enhance_sentiment_analysis(segments)
        
        assert enhanced_sentiment is not None
        assert "overall_sentiment" in enhanced_sentiment
        assert enhanced_sentiment["overall_sentiment"] == "negative"
        assert enhanced_sentiment["confidence"] == 0.85
        
        # Test AI-powered risk assessment
        risk_assessment = await ai_analyzer.assess_deal_risk_with_ai(segments)
        
        assert risk_assessment is not None
        assert "risk_indicators" in risk_assessment
        assert len(risk_assessment["risk_indicators"]) > 0
    
    @pytest.mark.asyncio
    async def test_ai_fallback_integration(self, comprehensive_transcript):
        """Test AI fallback mechanisms integration."""
        # Initialize AI analyzer without API key
        ai_analyzer = AIAnalyzer()
        ai_analyzer.client = None
        ai_analyzer.api_available = False
        
        # Parse transcript
        transcript_analyzer = TranscriptAnalyzer()
        segments = transcript_analyzer.parse_transcript(comprehensive_transcript)
        
        # Test fallback sentiment analysis
        fallback_sentiment = await ai_analyzer.enhance_sentiment_analysis(segments)
        
        assert fallback_sentiment is not None
        assert "overall_sentiment" in fallback_sentiment
        assert fallback_sentiment["overall_sentiment"] in ["positive", "negative", "neutral"]
        
        # Test fallback risk assessment
        fallback_risk = await ai_analyzer.assess_deal_risk_with_ai(segments)
        
        assert fallback_risk is not None
        assert "risk_level" in fallback_risk


class TestErrorHandlingIntegration:
    """Test error handling across all components."""
    
    @pytest.mark.asyncio
    async def test_s3_error_propagation(self, mcp_server_with_tools):
        """Test S3 error propagation through the system."""
        with patch('boto3.client') as mock_boto:
            # Mock S3 client to raise errors
            from botocore.exceptions import ClientError
            mock_client = Mock()
            mock_client.get_object.side_effect = ClientError(
                error_response={'Error': {'Code': 'NoSuchKey'}},
                operation_name='GetObject'
            )
            mock_boto.return_value = mock_client
            
            # Test error handling in MCP tool
            with pytest.raises(Exception):
                await mcp_server_with_tools.call_tool(
                    "analyze_transcript",
                    {
                        "s3_bucket": "test-bucket",
                        "s3_key": "non-existent.json",
                        "output_bucket": "results-bucket"
                    }
                )
    
    @pytest.mark.asyncio
    async def test_invalid_transcript_handling(self, mcp_server_with_tools, mock_s3_environment):
        """Test handling of invalid transcript content."""
        # Setup invalid transcript content
        invalid_content = "Not a valid JSON transcript"
        mock_s3_environment.get_object.return_value['Body'].read.return_value = invalid_content.encode('utf-8')
        
        # Test error handling
        with pytest.raises(Exception):
            await mcp_server_with_tools.call_tool(
                "analyze_transcript",
                {
                    "s3_bucket": "test-bucket",
                    "s3_key": "invalid.json",
                    "output_bucket": "results-bucket"
                }
            )
    
    def test_http_error_handling_integration(self):
        """Test HTTP server error handling integration."""
        from mcp_http_server import app
        client = TestClient(app)
        
        # Test invalid JSON request
        response = client.post("/mcp", data="invalid json")
        assert response.status_code == 400
        
        # Test malformed MCP request
        invalid_mcp = {"invalid": "request"}
        response = client.post("/mcp", json=invalid_mcp)
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data


class TestPerformanceIntegration:
    """Test performance aspects of integration."""
    
    @pytest.mark.asyncio
    async def test_large_transcript_processing(self, mock_s3_environment):
        """Test processing of large transcripts."""
        # Create a large transcript
        large_transcript = {
            "call_id": "LARGE_TEST",
            "transcript": []
        }
        
        # Add many segments
        for i in range(100):
            large_transcript["transcript"].append({
                "speaker": "agent" if i % 2 == 0 else "customer",
                "text": f"This is segment {i} with some sample text content.",
                "timestamp": f"00:{i:02d}",
                "duration": 3.0
            })
        
        large_content = json.dumps(large_transcript)
        mock_s3_environment.get_object.return_value['Body'].read.return_value = large_content.encode('utf-8')
        
        # Process large transcript
        transcript_analyzer = TranscriptAnalyzer()
        segments = transcript_analyzer.parse_transcript(large_content)
        
        assert len(segments) == 100
        
        # Test analysis performance
        import time
        start_time = time.time()
        
        analysis_result = await transcript_analyzer.analyze_transcript(
            transcript_segments=segments,
            call_id="LARGE_TEST",
            analysis_options={"sentiment_analysis": True, "performance_metrics": True}
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on performance requirements)
        assert processing_time < 30.0  # 30 seconds for 100 segments
        assert isinstance(analysis_result, CallAnalysisResult)
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_integration(self, mock_s3_environment, comprehensive_transcript):
        """Test concurrent analysis processing."""
        # Setup mock environment
        mock_s3_environment.get_object.return_value['Body'].read.return_value = comprehensive_transcript.encode('utf-8')
        
        transcript_analyzer = TranscriptAnalyzer()
        
        async def analyze_transcript_task(call_id):
            segments = transcript_analyzer.parse_transcript(comprehensive_transcript)
            return await transcript_analyzer.analyze_transcript(
                transcript_segments=segments,
                call_id=call_id,
                analysis_options={"sentiment_analysis": True}
            )
        
        # Run multiple analyses concurrently
        tasks = [analyze_transcript_task(f"CONCURRENT_{i}") for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 3
        for i, result in enumerate(results):
            assert isinstance(result, CallAnalysisResult)
            assert result.call_id == f"CONCURRENT_{i}"


class TestDataFlow:
    """Test data flow through the entire system."""
    
    @pytest.mark.asyncio
    async def test_complete_data_pipeline(self, comprehensive_transcript, mock_s3_environment):
        """Test complete data pipeline from input to output."""
        # Setup mock environment
        mock_s3_environment.get_object.return_value['Body'].read.return_value = comprehensive_transcript.encode('utf-8')
        
        # Initialize all services
        s3_service = S3Service()
        transcript_analyzer = TranscriptAnalyzer()
        bi_analyzer = BusinessIntelligenceAnalyzer()
        
        # Step 1: Input - Read transcript
        transcript_content = s3_service.read_transcript('input-bucket', 'call.json')
        parsed_data = json.loads(transcript_content)
        assert parsed_data['call_id'] == 'INTEGRATION_TEST_001'
        
        # Step 2: Processing - Analyze transcript
        segments = transcript_analyzer.parse_transcript(transcript_content)
        analysis_result = await transcript_analyzer.analyze_transcript(
            transcript_segments=segments,
            call_id=parsed_data['call_id'],
            analysis_options={
                "sentiment_analysis": True,
                "performance_metrics": True,
                "compliance_check": True
            }
        )
        
        # Verify analysis quality
        assert analysis_result.sentiment_analysis is not None
        assert analysis_result.performance_kpis is not None
        assert analysis_result.compliance_metrics is not None
        
        # Step 3: Intelligence - Generate business insights
        bi_insights = bi_analyzer.generate_business_intelligence(
            analysis_results=[analysis_result],
            transcript_segments_list=[segments],
            time_period="Data Pipeline Test"
        )
        
        # Verify business intelligence
        assert isinstance(bi_insights, BusinessIntelligenceInsights)
        assert bi_insights.time_period == "Data Pipeline Test"
        
        # Step 4: Output - Upload results
        analysis_json = analysis_result.model_dump_json(indent=2)
        bi_json = bi_insights.model_dump_json(indent=2)
        
        analysis_upload = s3_service.upload_analysis_results(
            content=analysis_json,
            bucket='output-bucket',
            key='analysis_result.json'
        )
        
        bi_upload = s3_service.upload_analysis_results(
            content=bi_json,
            bucket='output-bucket',
            key='business_intelligence.json'
        )
        
        # Verify outputs
        assert 's3_url' in analysis_upload
        assert 's3_url' in bi_upload
        assert analysis_upload['s3_url'] == 's3://output-bucket/analysis_result.json'
        assert bi_upload['s3_url'] == 's3://output-bucket/business_intelligence.json'
        
        # Step 5: Validation - Verify data integrity
        # The uploaded content should be valid JSON that can be parsed back
        re_parsed_analysis = CallAnalysisResult.model_validate_json(analysis_json)
        re_parsed_bi = BusinessIntelligenceInsights.model_validate_json(bi_json)
        
        assert re_parsed_analysis.call_id == analysis_result.call_id
        assert re_parsed_bi.time_period == bi_insights.time_period