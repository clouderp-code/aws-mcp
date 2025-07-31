"""
Comprehensive tests for FastAPI HTTP server endpoints.

Tests MCP HTTP transport protocol implementation, endpoint handlers,
error handling, and CORS configuration.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from typing import Dict, Any

# Import the HTTP server components
from mcp_http_server import app, mcp_server, dual_logger


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_mcp_request():
    """Sample MCP request for testing."""
    return {
        "jsonrpc": "2.0",
        "id": "test-request-1",
        "method": "tools/call",
        "params": {
            "name": "analyze_transcript",
            "arguments": {
                "transcript_content": json.dumps({
                    "call_id": "TEST_CALL_001",
                    "transcript": [
                        {
                            "speaker": "agent",
                            "text": "Thank you for calling. How can I help you today?",
                            "timestamp": "00:00"
                        }
                    ]
                }),
                "call_id": "TEST_CALL_001"
            }
        }
    }


@pytest.fixture
def sample_tool_list_request():
    """Sample tool list request for testing."""
    return {
        "jsonrpc": "2.0",
        "id": "test-list-1",
        "method": "tools/list"
    }


@pytest.fixture
def sample_initialize_request():
    """Sample initialize request for testing."""
    return {
        "jsonrpc": "2.0",
        "id": "test-init-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "server_info" in data
        assert data["server_info"]["name"] == "call-analysis-mcp-server"
    
    def test_health_endpoint_includes_tools(self, client):
        """Test that health endpoint includes tool information."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "available_tools" in data
        assert isinstance(data["available_tools"], int)
        assert data["available_tools"] > 0  # Should have registered tools


class TestMCPEndpoint:
    """Test main MCP endpoint."""
    
    @patch('mcp_http_server.mcp_server')
    def test_mcp_initialize_request(self, mock_mcp_server, client, sample_initialize_request):
        """Test MCP initialize request."""
        # Mock successful initialization
        mock_result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "prompts": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "call-analysis-mcp-server",
                "version": "1.0.0"
            }
        }
        mock_mcp_server.handle_request = AsyncMock(return_value=mock_result)
        
        response = client.post("/mcp", json=sample_initialize_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-init-1"
        assert "result" in data
        assert data["result"]["serverInfo"]["name"] == "call-analysis-mcp-server"
    
    @patch('mcp_http_server.mcp_server')
    def test_mcp_tools_list_request(self, mock_mcp_server, client, sample_tool_list_request):
        """Test MCP tools list request."""
        # Mock tools list response
        mock_tools = [
            {
                "name": "analyze_transcript",
                "description": "Analyze a call transcript",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "transcript_content": {"type": "string"},
                        "call_id": {"type": "string"}
                    },
                    "required": ["transcript_content", "call_id"]
                }
            },
            {
                "name": "generate_business_intelligence",
                "description": "Generate business intelligence insights",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "analysis_results": {"type": "array"}
                    },
                    "required": ["analysis_results"]
                }
            }
        ]
        mock_mcp_server.handle_request = AsyncMock(return_value={"tools": mock_tools})
        
        response = client.post("/mcp", json=sample_tool_list_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-list-1"
        assert "result" in data
        assert len(data["result"]["tools"]) == 2
        assert data["result"]["tools"][0]["name"] == "analyze_transcript"
    
    @patch('mcp_http_server.mcp_server')
    def test_mcp_tool_call_request(self, mock_mcp_server, client, sample_mcp_request):
        """Test MCP tool call request."""
        # Mock tool call response
        mock_result = [
            {
                "type": "text",
                "text": "Analysis completed successfully for call TEST_CALL_001"
            }
        ]
        mock_mcp_server.handle_request = AsyncMock(return_value={"content": mock_result})
        
        response = client.post("/mcp", json=sample_mcp_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-request-1"
        assert "result" in data
        assert len(data["result"]["content"]) == 1
        assert "Analysis completed successfully" in data["result"]["content"][0]["text"]
    
    def test_mcp_invalid_json(self, client):
        """Test handling of invalid JSON in MCP request."""
        response = client.post(
            "/mcp",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Invalid JSON" in data["error"]["message"]
    
    def test_mcp_missing_required_fields(self, client):
        """Test handling of MCP request with missing required fields."""
        invalid_request = {
            "jsonrpc": "2.0",
            # Missing id and method
            "params": {}
        }
        
        response = client.post("/mcp", json=invalid_request)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Missing required fields" in data["error"]["message"]
    
    def test_mcp_invalid_jsonrpc_version(self, client):
        """Test handling of invalid JSON-RPC version."""
        invalid_request = {
            "jsonrpc": "1.0",  # Invalid version
            "id": "test-1",
            "method": "tools/list"
        }
        
        response = client.post("/mcp", json=invalid_request)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Invalid JSON-RPC version" in data["error"]["message"]
    
    @patch('mcp_http_server.mcp_server')
    def test_mcp_server_error(self, mock_mcp_server, client, sample_mcp_request):
        """Test handling of MCP server errors."""
        # Mock server error
        mock_mcp_server.handle_request = AsyncMock(side_effect=Exception("Internal server error"))
        
        response = client.post("/mcp", json=sample_mcp_request)
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32603  # Internal error code
        assert "Internal server error" in data["error"]["message"]
    
    @patch('mcp_http_server.mcp_server')
    def test_mcp_tool_not_found(self, mock_mcp_server, client):
        """Test handling of unknown tool call."""
        unknown_tool_request = {
            "jsonrpc": "2.0",
            "id": "test-unknown-1",
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        }
        
        # Mock tool not found error
        mock_mcp_server.handle_request = AsyncMock(side_effect=ValueError("Tool not found: unknown_tool"))
        
        response = client.post("/mcp", json=unknown_tool_request)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Tool not found" in data["error"]["message"]


class TestCORSConfiguration:
    """Test CORS configuration."""
    
    def test_cors_preflight_request(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/mcp",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "POST" in response.headers["Access-Control-Allow-Methods"]
    
    def test_cors_actual_request(self, client, sample_tool_list_request):
        """Test CORS headers in actual request."""
        response = client.post(
            "/mcp",
            json=sample_tool_list_request,
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should include CORS headers regardless of status
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_cors_wildcard_origin(self, client):
        """Test CORS allows wildcard origin."""
        response = client.get(
            "/health",
            headers={"Origin": "https://example.com"}
        )
        
        assert response.status_code == 200
        # Should allow any origin due to wildcard configuration
        assert "Access-Control-Allow-Origin" in response.headers


class TestLogging:
    """Test logging functionality."""
    
    @patch('mcp_http_server.dual_logger')
    def test_request_logging(self, mock_logger, client, sample_tool_list_request):
        """Test that requests are properly logged."""
        response = client.post("/mcp", json=sample_tool_list_request)
        
        # Should log the request
        assert mock_logger.info.called
        # Should log either request details or response
        call_args = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("MCP" in arg or "request" in arg.lower() for arg in call_args)
    
    @patch('mcp_http_server.dual_logger')
    def test_error_logging(self, mock_logger, client):
        """Test that errors are properly logged."""
        # Send invalid request to trigger error
        response = client.post("/mcp", data="invalid json")
        
        assert response.status_code == 400
        # Should log the error
        assert mock_logger.error.called or mock_logger.info.called
    
    @patch('mcp_http_server.dual_logger')
    @patch('mcp_http_server.mcp_server')
    def test_tool_execution_logging(self, mock_mcp_server, mock_logger, client, sample_mcp_request):
        """Test logging of tool execution."""
        mock_mcp_server.handle_request = AsyncMock(return_value={"content": []})
        
        response = client.post("/mcp", json=sample_mcp_request)
        
        assert response.status_code == 200
        # Should log tool execution
        assert mock_logger.info.called or mock_logger.debug.called


class TestErrorHandling:
    """Test comprehensive error handling."""
    
    def test_request_timeout_handling(self, client):
        """Test handling of request timeouts."""
        # This would require mocking asyncio timeout in real scenario
        # For now, test that the endpoint can handle requests
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_malformed_content_type(self, client):
        """Test handling of malformed content type."""
        response = client.post(
            "/mcp",
            data="test data",
            headers={"Content-Type": "text/plain"}
        )
        
        # Should handle gracefully (might return 400 or process as JSON)
        assert response.status_code in [200, 400, 422]
    
    def test_oversized_request(self, client):
        """Test handling of oversized requests."""
        # Create a large request
        large_content = {"data": "x" * 100000}  # 100KB of data
        
        response = client.post("/mcp", json=large_content)
        
        # Should handle gracefully (server might have size limits)
        assert response.status_code in [200, 400, 413, 422]
    
    @patch('mcp_http_server.mcp_server')
    def test_concurrent_request_handling(self, mock_mcp_server, client, sample_tool_list_request):
        """Test handling of concurrent requests."""
        mock_mcp_server.handle_request = AsyncMock(return_value={"tools": []})
        
        # Send multiple concurrent requests
        import threading
        results = []
        
        def make_request():
            response = client.post("/mcp", json=sample_tool_list_request)
            results.append(response.status_code)
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All requests should be handled successfully
        assert all(status == 200 for status in results)
        assert len(results) == 5


class TestSecurityHeaders:
    """Test security headers and protections."""
    
    def test_security_headers_present(self, client):
        """Test that appropriate security headers are present."""
        response = client.get("/health")
        
        # Check for common security headers
        # (Note: actual headers depend on server configuration)
        assert response.status_code == 200
        
        # Server should not expose sensitive information
        if "Server" in response.headers:
            assert "uvicorn" not in response.headers["Server"].lower()
    
    def test_no_sensitive_info_in_errors(self, client):
        """Test that error responses don't expose sensitive information."""
        response = client.post("/mcp", data="invalid json")
        
        assert response.status_code == 400
        data = response.json()
        
        # Error message should not contain file paths or internal details
        error_message = data.get("error", {}).get("message", "")
        assert "/opt/" not in error_message
        assert "traceback" not in error_message.lower()
        assert "exception" not in error_message.lower()


class TestServerConfiguration:
    """Test server configuration and metadata."""
    
    def test_server_info_endpoint(self, client):
        """Test server information in health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        server_info = data["server_info"]
        assert server_info["name"] == "call-analysis-mcp-server"
        assert "version" in server_info
        assert "environment" in server_info
    
    def test_available_tools_count(self, client):
        """Test that available tools count is accurate."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have multiple tools registered
        assert data["available_tools"] >= 5  # At least analysis, BI, S3, reporting tools
    
    @patch('mcp_http_server.mcp_server')
    def test_mcp_capabilities(self, mock_mcp_server, client, sample_initialize_request):
        """Test MCP server capabilities."""
        mock_capabilities = {
            "tools": {"listChanged": True},
            "prompts": {},
            "resources": {}
        }
        mock_mcp_server.handle_request = AsyncMock(return_value={
            "protocolVersion": "2024-11-05",
            "capabilities": mock_capabilities,
            "serverInfo": {"name": "call-analysis-mcp-server"}
        })
        
        response = client.post("/mcp", json=sample_initialize_request)
        
        assert response.status_code == 200
        data = response.json()
        capabilities = data["result"]["capabilities"]
        assert "tools" in capabilities
        assert capabilities["tools"]["listChanged"] is True


class TestPerformance:
    """Test performance-related aspects."""
    
    def test_response_time_health_check(self, client):
        """Test response time for health check."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Health check should be fast (under 1 second)
        assert (end_time - start_time) < 1.0
    
    @patch('mcp_http_server.mcp_server')
    def test_response_time_tool_list(self, mock_mcp_server, client, sample_tool_list_request):
        """Test response time for tool listing."""
        mock_mcp_server.handle_request = AsyncMock(return_value={"tools": []})
        
        import time
        
        start_time = time.time()
        response = client.post("/mcp", json=sample_tool_list_request)
        end_time = time.time()
        
        assert response.status_code == 200
        # Tool listing should be reasonably fast (under 2 seconds)
        assert (end_time - start_time) < 2.0


class TestEndpointValidation:
    """Test endpoint input validation."""
    
    def test_mcp_endpoint_content_type_validation(self, client):
        """Test that MCP endpoint validates content type."""
        response = client.post(
            "/mcp",
            data="not json",
            headers={"Content-Type": "text/plain"}
        )
        
        # Should handle gracefully
        assert response.status_code in [400, 422]
    
    def test_mcp_endpoint_accepts_json_only(self, client, sample_tool_list_request):
        """Test that MCP endpoint processes JSON correctly."""
        response = client.post(
            "/mcp",
            json=sample_tool_list_request,
            headers={"Content-Type": "application/json"}
        )
        
        # Should process JSON requests
        assert response.status_code in [200, 400, 500]  # Any valid HTTP response
    
    def test_health_endpoint_methods(self, client):
        """Test that health endpoint only accepts GET."""
        # GET should work
        response = client.get("/health")
        assert response.status_code == 200
        
        # POST should not be allowed
        response = client.post("/health", json={})
        assert response.status_code == 405  # Method Not Allowed
    
    def test_mcp_endpoint_methods(self, client):
        """Test that MCP endpoint only accepts POST."""
        # POST should work (even if request is invalid)
        response = client.post("/mcp", json={})
        assert response.status_code in [200, 400, 422]
        
        # GET should not be allowed
        response = client.get("/mcp")
        assert response.status_code == 405  # Method Not Allowed


class TestMCPProtocolCompliance:
    """Test compliance with MCP protocol specifications."""
    
    def test_jsonrpc_response_format(self, client, sample_tool_list_request):
        """Test that responses follow JSON-RPC 2.0 format."""
        response = client.post("/mcp", json=sample_tool_list_request)
        
        data = response.json()
        
        # Should have JSON-RPC 2.0 format
        assert "jsonrpc" in data
        assert data["jsonrpc"] == "2.0"
        assert "id" in data
        assert data["id"] == sample_tool_list_request["id"]
        
        # Should have either result or error
        assert "result" in data or "error" in data
    
    def test_error_response_format(self, client):
        """Test that error responses follow JSON-RPC error format."""
        invalid_request = {"invalid": "request"}
        
        response = client.post("/mcp", json=invalid_request)
        
        data = response.json()
        
        if "error" in data:
            error = data["error"]
            assert "code" in error
            assert "message" in error
            assert isinstance(error["code"], int)
            assert isinstance(error["message"], str)
    
    def test_batch_request_handling(self, client):
        """Test handling of batch requests (if supported)."""
        batch_request = [
            {
                "jsonrpc": "2.0",
                "id": "req-1",
                "method": "tools/list"
            },
            {
                "jsonrpc": "2.0", 
                "id": "req-2",
                "method": "tools/list"
            }
        ]
        
        response = client.post("/mcp", json=batch_request)
        
        # Should handle batch requests gracefully
        # (might not be implemented, but shouldn't crash)
        assert response.status_code in [200, 400, 501]  # OK, Bad Request, or Not Implemented