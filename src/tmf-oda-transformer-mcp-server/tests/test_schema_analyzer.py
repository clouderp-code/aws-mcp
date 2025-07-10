"""
Tests for the schema-analyzer tool of TMF ODA transformer MCP server.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import schema_analyzer_tool
from awslabs.tmf_oda_transformer_mcp_server.models import (
    TMFODAComponentType, 
    SchemaFormat, 
    ComplianceLevel,
    SchemaAnalysisReport
)
from awslabs.tmf_oda_transformer_mcp_server.consts import (
    ERROR_EMPTY_WORKSPACE_DIR,
    ERROR_INVALID_WORKSPACE_DIR,
    ERROR_INVALID_SCHEMA_FORMAT,
    ERROR_INVALID_ODA_COMPONENT_TYPE,
    ERROR_NO_SCHEMAS_FOUND,
    ERROR_SCHEMA_ANALYSIS_FAILED
)


@pytest.mark.asyncio
class TestSchemaAnalyzer:
    """Test cases for the schema-analyzer tool."""

    async def test_schema_analyzer_success(self, mock_context, temp_workspace):
        """Test successful schema analysis with valid workspace and parameters."""
        result = await schema_analyzer_tool(
            ctx=mock_context,
            workspace_dir=temp_workspace,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            schema_format=None
        )
        
        # Verify the result structure
        assert isinstance(result, SchemaAnalysisReport)
        assert result.workspace_dir == temp_workspace
        assert result.oda_component_type == TMFODAComponentType.CUSTOMER_MANAGEMENT
        assert result.total_files_found > 0
        assert result.total_files_analyzed >= 0
        assert result.analysis_duration > 0
        assert 'compliant_count' in result.summary
        assert 'partially_compliant_count' in result.summary
        assert 'non_compliant_count' in result.summary
        
        # Verify context was not called with errors
        mock_context.error.assert_not_called()

    async def test_schema_analyzer_with_specific_format(self, mock_context, temp_workspace):
        """Test schema analysis with specific format filter."""
        result = await schema_analyzer_tool(
            ctx=mock_context,
            workspace_dir=temp_workspace,
            oda_component_type=TMFODAComponentType.ORDER_MANAGEMENT,
            schema_format=SchemaFormat.JSON_SCHEMA
        )
        
        assert isinstance(result, SchemaAnalysisReport)
        assert result.schema_format_filter == SchemaFormat.JSON_SCHEMA
        assert result.total_files_found >= 0
        mock_context.error.assert_not_called()

    async def test_schema_analyzer_empty_workspace_dir(self, mock_context):
        """Test schema analyzer with empty workspace directory."""
        with pytest.raises(ValueError, match=ERROR_EMPTY_WORKSPACE_DIR):
            await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir="",
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_EMPTY_WORKSPACE_DIR)

    async def test_schema_analyzer_whitespace_workspace_dir(self, mock_context):
        """Test schema analyzer with whitespace-only workspace directory."""
        with pytest.raises(ValueError, match=ERROR_EMPTY_WORKSPACE_DIR):
            await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir="   ",
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_EMPTY_WORKSPACE_DIR)

    async def test_schema_analyzer_invalid_workspace_dir(self, mock_context):
        """Test schema analyzer with non-existent workspace directory."""
        with pytest.raises(ValueError, match=ERROR_INVALID_WORKSPACE_DIR):
            await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir="/non/existent/directory",
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_INVALID_WORKSPACE_DIR)

    async def test_schema_analyzer_file_as_workspace_dir(self, mock_context, temp_workspace):
        """Test schema analyzer with file path instead of directory."""
        # Create a test file
        test_file = Path(temp_workspace) / "test_file.txt"
        test_file.write_text("test content")
        
        with pytest.raises(ValueError, match=ERROR_INVALID_WORKSPACE_DIR):
            await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir=str(test_file),
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_INVALID_WORKSPACE_DIR)

    async def test_schema_analyzer_invalid_schema_format(self, mock_context, temp_workspace):
        """Test schema analyzer with invalid schema format."""
        with pytest.raises(ValueError, match=ERROR_INVALID_SCHEMA_FORMAT):
            await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir=temp_workspace,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format="invalid-format"  # This should trigger validation error
            )
        
        mock_context.error.assert_called_once_with(ERROR_INVALID_SCHEMA_FORMAT)

    async def test_schema_analyzer_invalid_oda_component_type(self, mock_context, temp_workspace):
        """Test schema analyzer with invalid ODA component type."""
        with pytest.raises(ValueError, match=ERROR_INVALID_ODA_COMPONENT_TYPE):
            await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir=temp_workspace,
                oda_component_type="invalid-component-type",  # This should trigger validation error
                schema_format=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_INVALID_ODA_COMPONENT_TYPE)

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._discover_schema_files')
    async def test_schema_analyzer_no_schemas_found(self, mock_discover, mock_context, temp_workspace):
        """Test schema analyzer when no schema files are found."""
        mock_discover.return_value = []
        
        with pytest.raises(ValueError, match=ERROR_NO_SCHEMAS_FOUND):
            await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir=temp_workspace,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_NO_SCHEMAS_FOUND)

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._discover_schema_files')
    @patch('awslabs.tmf_oda_transformer_mcp_server.server._analyze_schema_file')
    async def test_schema_analyzer_analysis_timeout(self, mock_analyze, mock_discover, mock_context, temp_workspace):
        """Test schema analyzer when analysis times out."""
        mock_discover.return_value = ["/path/to/schema.json"]
        mock_analyze.side_effect = asyncio.TimeoutError()
        
        # This should still complete successfully but with no results
        result = await schema_analyzer_tool(
            ctx=mock_context,
            workspace_dir=temp_workspace,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            schema_format=None
        )
        
        assert isinstance(result, SchemaAnalysisReport)
        assert result.total_files_analyzed == 0
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._discover_schema_files')
    async def test_schema_analyzer_discovery_exception(self, mock_discover, mock_context, temp_workspace):
        """Test schema analyzer when file discovery raises an exception."""
        mock_discover.side_effect = Exception("Discovery failed")
        
        with pytest.raises(Exception, match="Schema analysis failed"):
            await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir=temp_workspace,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
        
        mock_context.error.assert_called_once()

    async def test_schema_analyzer_all_oda_component_types(self, mock_context, temp_workspace, oda_component_types):
        """Test schema analyzer with all valid ODA component types."""
        for component_type in oda_component_types:
            # Reset mock for each iteration
            mock_context.reset_mock()
            
            result = await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir=temp_workspace,
                oda_component_type=component_type,
                schema_format=None
            )
            
            assert isinstance(result, SchemaAnalysisReport)
            assert result.oda_component_type == component_type
            mock_context.error.assert_not_called()

    async def test_schema_analyzer_all_schema_formats(self, mock_context, temp_workspace, schema_formats):
        """Test schema analyzer with all valid schema formats."""
        for schema_format in schema_formats:
            # Reset mock for each iteration
            mock_context.reset_mock()
            
            result = await schema_analyzer_tool(
                ctx=mock_context,
                workspace_dir=temp_workspace,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=schema_format
            )
            
            assert isinstance(result, SchemaAnalysisReport)
            assert result.schema_format_filter == schema_format
            mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._discover_schema_files')
    @patch('awslabs.tmf_oda_transformer_mcp_server.server._analyze_schema_file')
    async def test_schema_analyzer_mixed_results(self, mock_analyze, mock_discover, mock_context, temp_workspace):
        """Test schema analyzer with mixed analysis results (some succeed, some fail)."""
        mock_discover.return_value = [
            "/path/to/schema1.json",
            "/path/to/schema2.json", 
            "/path/to/schema3.json"
        ]
        
        # Mock mixed results - some succeed, some fail
        async def mock_analyze_side_effect(schema_file, oda_component_type):
            if "schema1" in schema_file:
                # Create a successful result mock
                result = Mock()
                result.compliance_level = ComplianceLevel.COMPLIANT
                result.compliance_score = 85.0
                result.issues = []
                result.recommendations = []
                return result
            elif "schema2" in schema_file:
                raise Exception("Analysis failed for schema2")
            else:
                # Timeout for schema3
                raise asyncio.TimeoutError()
        
        mock_analyze.side_effect = mock_analyze_side_effect
        
        result = await schema_analyzer_tool(
            ctx=mock_context,
            workspace_dir=temp_workspace,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            schema_format=None
        )
        
        assert isinstance(result, SchemaAnalysisReport)
        assert result.total_files_found == 3
        assert result.total_files_analyzed == 1  # Only one succeeded
        assert result.summary['compliant_count'] == 1
        mock_context.error.assert_not_called()

    async def test_schema_analyzer_performance_timing(self, mock_context, temp_workspace):
        """Test that schema analyzer measures and reports timing correctly."""
        import time
        start_time = time.time()
        
        result = await schema_analyzer_tool(
            ctx=mock_context,
            workspace_dir=temp_workspace,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            schema_format=None
        )
        
        end_time = time.time()
        
        assert isinstance(result, SchemaAnalysisReport)
        assert result.analysis_duration > 0
        assert result.analysis_duration <= (end_time - start_time) + 1  # Allow some tolerance
        assert result.analysis_timestamp is not None
        mock_context.error.assert_not_called()

    async def test_schema_analyzer_summary_calculations(self, mock_context, temp_workspace):
        """Test that summary statistics are calculated correctly."""
        result = await schema_analyzer_tool(
            ctx=mock_context,
            workspace_dir=temp_workspace,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            schema_format=None
        )
        
        assert isinstance(result, SchemaAnalysisReport)
        summary = result.summary
        
        # Verify all expected summary fields are present
        required_fields = [
            'compliant_count', 'partially_compliant_count', 'non_compliant_count',
            'avg_compliance_score', 'total_issues', 'total_recommendations'
        ]
        for field in required_fields:
            assert field in summary
            assert isinstance(summary[field], (int, float))
        
        # Verify counts add up correctly
        total_count = (summary['compliant_count'] + 
                      summary['partially_compliant_count'] + 
                      summary['non_compliant_count'])
        assert total_count == result.total_files_analyzed
        
        mock_context.error.assert_not_called() 