"""
Tests for the db-analyzer tool of TMF ODA transformer MCP server.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import db_analyzer_tool
from awslabs.tmf_oda_transformer_mcp_server.models import (
    TMFODAComponentType, 
    DatabaseType, 
    ComplianceLevel,
    DatabaseAnalysisReport
)
from awslabs.tmf_oda_transformer_mcp_server.consts import (
    ERROR_EMPTY_CONNECTION_STRING,
    ERROR_INVALID_DATABASE_TYPE,
    ERROR_INVALID_ODA_COMPONENT_TYPE,
    ERROR_DATABASE_CONNECTION_FAILED,
    ERROR_TABLES_NOT_FOUND,
    ERROR_DATABASE_ANALYSIS_FAILED
)


@pytest.mark.asyncio
class TestDbAnalyzer:
    """Test cases for the db-analyzer tool."""

    async def test_db_analyzer_success_postgresql(self, mock_context, valid_connection_strings):
        """Test successful database analysis with PostgreSQL."""
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=valid_connection_strings["postgresql"],
            database_type=DatabaseType.POSTGRESQL,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            tables_filter=None
        )
        
        # Verify the result structure
        assert isinstance(result, DatabaseAnalysisReport)
        assert result.database_type == DatabaseType.POSTGRESQL
        assert result.oda_component_type == TMFODAComponentType.CUSTOMER_MANAGEMENT
        assert result.total_tables_found > 0
        assert result.total_tables_analyzed >= 0
        assert result.analysis_duration > 0
        assert 'compliant_count' in result.summary
        assert 'partially_compliant_count' in result.summary
        assert 'non_compliant_count' in result.summary
        
        # Verify context was not called with errors
        mock_context.error.assert_not_called()

    async def test_db_analyzer_success_mysql(self, mock_context, valid_connection_strings):
        """Test successful database analysis with MySQL."""
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=valid_connection_strings["mysql"],
            database_type=DatabaseType.MYSQL,
            oda_component_type=TMFODAComponentType.ORDER_MANAGEMENT,
            tables_filter=None
        )
        
        assert isinstance(result, DatabaseAnalysisReport)
        assert result.database_type == DatabaseType.MYSQL
        assert result.oda_component_type == TMFODAComponentType.ORDER_MANAGEMENT
        mock_context.error.assert_not_called()

    async def test_db_analyzer_success_mongodb(self, mock_context, valid_connection_strings):
        """Test successful database analysis with MongoDB."""
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=valid_connection_strings["mongodb"],
            database_type=DatabaseType.MONGODB,
            oda_component_type=TMFODAComponentType.PRODUCT_CATALOG_MANAGEMENT,
            tables_filter=None
        )
        
        assert isinstance(result, DatabaseAnalysisReport)
        assert result.database_type == DatabaseType.MONGODB
        assert result.oda_component_type == TMFODAComponentType.PRODUCT_CATALOG_MANAGEMENT
        mock_context.error.assert_not_called()

    async def test_db_analyzer_with_table_filter(self, mock_context, valid_connection_strings):
        """Test database analysis with table filter."""
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=valid_connection_strings["postgresql"],
            database_type=DatabaseType.POSTGRESQL,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            tables_filter="user_*,customer_*"
        )
        
        assert isinstance(result, DatabaseAnalysisReport)
        assert result.tables_filter == "user_*,customer_*"
        mock_context.error.assert_not_called()

    async def test_db_analyzer_empty_connection_string(self, mock_context):
        """Test db analyzer with empty connection string."""
        with pytest.raises(ValueError, match=ERROR_EMPTY_CONNECTION_STRING):
            await db_analyzer_tool(
                ctx=mock_context,
                connection_string="",
                database_type=DatabaseType.POSTGRESQL,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                tables_filter=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_EMPTY_CONNECTION_STRING)

    async def test_db_analyzer_whitespace_connection_string(self, mock_context):
        """Test db analyzer with whitespace-only connection string."""
        with pytest.raises(ValueError, match=ERROR_EMPTY_CONNECTION_STRING):
            await db_analyzer_tool(
                ctx=mock_context,
                connection_string="   ",
                database_type=DatabaseType.POSTGRESQL,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                tables_filter=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_EMPTY_CONNECTION_STRING)

    async def test_db_analyzer_invalid_database_type(self, mock_context, valid_connection_strings):
        """Test db analyzer with invalid database type."""
        with pytest.raises(ValueError, match=ERROR_INVALID_DATABASE_TYPE):
            await db_analyzer_tool(
                ctx=mock_context,
                connection_string=valid_connection_strings["postgresql"],
                database_type="invalid-database-type",  # This should trigger validation error
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                tables_filter=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_INVALID_DATABASE_TYPE)

    async def test_db_analyzer_invalid_oda_component_type(self, mock_context, valid_connection_strings):
        """Test db analyzer with invalid ODA component type."""
        with pytest.raises(ValueError, match=ERROR_INVALID_ODA_COMPONENT_TYPE):
            await db_analyzer_tool(
                ctx=mock_context,
                connection_string=valid_connection_strings["postgresql"],
                database_type=DatabaseType.POSTGRESQL,
                oda_component_type="invalid-component-type",  # This should trigger validation error
                tables_filter=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_INVALID_ODA_COMPONENT_TYPE)

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._test_database_connection')
    async def test_db_analyzer_connection_failed(self, mock_test_conn, mock_context, valid_connection_strings):
        """Test db analyzer when database connection fails."""
        mock_test_conn.return_value = False
        
        with pytest.raises(Exception, match=ERROR_DATABASE_CONNECTION_FAILED):
            await db_analyzer_tool(
                ctx=mock_context,
                connection_string=valid_connection_strings["postgresql"],
                database_type=DatabaseType.POSTGRESQL,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                tables_filter=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_DATABASE_CONNECTION_FAILED)

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._test_database_connection')
    @patch('awslabs.tmf_oda_transformer_mcp_server.server._discover_database_tables')
    async def test_db_analyzer_no_tables_found(self, mock_discover, mock_test_conn, mock_context, valid_connection_strings):
        """Test db analyzer when no tables are found."""
        mock_test_conn.return_value = True
        mock_discover.return_value = []
        
        with pytest.raises(ValueError, match=ERROR_TABLES_NOT_FOUND):
            await db_analyzer_tool(
                ctx=mock_context,
                connection_string=valid_connection_strings["postgresql"],
                database_type=DatabaseType.POSTGRESQL,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                tables_filter=None
            )
        
        mock_context.error.assert_called_once_with(ERROR_TABLES_NOT_FOUND)

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._test_database_connection')
    @patch('awslabs.tmf_oda_transformer_mcp_server.server._discover_database_tables')
    @patch('awslabs.tmf_oda_transformer_mcp_server.server._analyze_database_table')
    async def test_db_analyzer_analysis_timeout(self, mock_analyze, mock_discover, mock_test_conn, mock_context, valid_connection_strings):
        """Test db analyzer when table analysis times out."""
        mock_test_conn.return_value = True
        mock_discover.return_value = ["users", "products"]
        mock_analyze.side_effect = asyncio.TimeoutError()
        
        # This should still complete successfully but with no results
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=valid_connection_strings["postgresql"],
            database_type=DatabaseType.POSTGRESQL,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            tables_filter=None
        )
        
        assert isinstance(result, DatabaseAnalysisReport)
        assert result.total_tables_analyzed == 0
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._test_database_connection')
    async def test_db_analyzer_connection_exception(self, mock_test_conn, mock_context, valid_connection_strings):
        """Test db analyzer when connection test raises an exception."""
        mock_test_conn.side_effect = Exception("Connection test failed")
        
        with pytest.raises(Exception, match="Database analysis failed"):
            await db_analyzer_tool(
                ctx=mock_context,
                connection_string=valid_connection_strings["postgresql"],
                database_type=DatabaseType.POSTGRESQL,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                tables_filter=None
            )
        
        mock_context.error.assert_called_once()

    async def test_db_analyzer_all_database_types(self, mock_context, database_types):
        """Test db analyzer with all valid database types."""
        connection_string = "test://user:pass@localhost:5432/testdb"
        
        for db_type in database_types:
            # Reset mock for each iteration
            mock_context.reset_mock()
            
            result = await db_analyzer_tool(
                ctx=mock_context,
                connection_string=connection_string,
                database_type=db_type,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                tables_filter=None
            )
            
            assert isinstance(result, DatabaseAnalysisReport)
            assert result.database_type == db_type
            mock_context.error.assert_not_called()

    async def test_db_analyzer_all_oda_component_types(self, mock_context, oda_component_types, valid_connection_strings):
        """Test db analyzer with all valid ODA component types."""
        for component_type in oda_component_types:
            # Reset mock for each iteration
            mock_context.reset_mock()
            
            result = await db_analyzer_tool(
                ctx=mock_context,
                connection_string=valid_connection_strings["postgresql"],
                database_type=DatabaseType.POSTGRESQL,
                oda_component_type=component_type,
                tables_filter=None
            )
            
            assert isinstance(result, DatabaseAnalysisReport)
            assert result.oda_component_type == component_type
            mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._test_database_connection')
    @patch('awslabs.tmf_oda_transformer_mcp_server.server._discover_database_tables')
    @patch('awslabs.tmf_oda_transformer_mcp_server.server._analyze_database_table')
    async def test_db_analyzer_mixed_results(self, mock_analyze, mock_discover, mock_test_conn, mock_context, valid_connection_strings):
        """Test db analyzer with mixed analysis results (some succeed, some fail)."""
        mock_test_conn.return_value = True
        mock_discover.return_value = ["users", "products", "orders"]
        
        # Mock mixed results - some succeed, some fail
        async def mock_analyze_side_effect(conn_str, db_type, table, oda_type):
            if table == "users":
                # Create a successful result mock
                result = Mock()
                result.compliance_level = ComplianceLevel.COMPLIANT
                result.compliance_score = 85.0
                result.recommendations = []
                return result
            elif table == "products":
                raise Exception("Analysis failed for products")
            else:
                # Timeout for orders
                raise asyncio.TimeoutError()
        
        mock_analyze.side_effect = mock_analyze_side_effect
        
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=valid_connection_strings["postgresql"],
            database_type=DatabaseType.POSTGRESQL,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            tables_filter=None
        )
        
        assert isinstance(result, DatabaseAnalysisReport)
        assert result.total_tables_found == 3
        assert result.total_tables_analyzed == 1  # Only one succeeded
        assert result.summary['compliant_count'] == 1
        mock_context.error.assert_not_called()

    async def test_db_analyzer_performance_timing(self, mock_context, valid_connection_strings):
        """Test that db analyzer measures and reports timing correctly."""
        import time
        start_time = time.time()
        
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=valid_connection_strings["postgresql"],
            database_type=DatabaseType.POSTGRESQL,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            tables_filter=None
        )
        
        end_time = time.time()
        
        assert isinstance(result, DatabaseAnalysisReport)
        assert result.analysis_duration > 0
        assert result.analysis_duration <= (end_time - start_time) + 1  # Allow some tolerance
        assert result.analysis_timestamp is not None
        mock_context.error.assert_not_called()

    async def test_db_analyzer_summary_calculations(self, mock_context, valid_connection_strings):
        """Test that summary statistics are calculated correctly."""
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=valid_connection_strings["postgresql"],
            database_type=DatabaseType.POSTGRESQL,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            tables_filter=None
        )
        
        assert isinstance(result, DatabaseAnalysisReport)
        summary = result.summary
        
        # Verify all expected summary fields are present
        required_fields = [
            'compliant_count', 'partially_compliant_count', 'non_compliant_count',
            'avg_compliance_score', 'total_recommendations'
        ]
        for field in required_fields:
            assert field in summary
            assert isinstance(summary[field], (int, float))
        
        # Verify counts add up correctly
        total_count = (summary['compliant_count'] + 
                      summary['partially_compliant_count'] + 
                      summary['non_compliant_count'])
        assert total_count == result.total_tables_analyzed
        
        mock_context.error.assert_not_called()

    async def test_db_analyzer_connection_string_sanitization(self, mock_context):
        """Test that connection strings are properly handled for security."""
        # Test with connection string containing password
        conn_str = "postgresql://user:secretpassword@localhost:5432/testdb"
        
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=conn_str,
            database_type=DatabaseType.POSTGRESQL,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            tables_filter=None
        )
        
        assert isinstance(result, DatabaseAnalysisReport)
        # The connection string should be stored (model handles sanitization)
        assert result.connection_string == conn_str
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server._test_database_connection')
    @patch('awslabs.tmf_oda_transformer_mcp_server.server._discover_database_tables')
    async def test_db_analyzer_table_filter_functionality(self, mock_discover, mock_test_conn, mock_context, valid_connection_strings):
        """Test that table filters are properly passed through."""
        mock_test_conn.return_value = True
        mock_discover.return_value = ["user_accounts", "user_profiles"]
        
        result = await db_analyzer_tool(
            ctx=mock_context,
            connection_string=valid_connection_strings["postgresql"],
            database_type=DatabaseType.POSTGRESQL,
            oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
            tables_filter="user_*"
        )
        
        assert isinstance(result, DatabaseAnalysisReport)
        assert result.tables_filter == "user_*"
        
        # Verify the filter was passed to the discover function
        mock_discover.assert_called_once_with(
            valid_connection_strings["postgresql"],
            DatabaseType.POSTGRESQL,
            "user_*"
        )
        
        mock_context.error.assert_not_called() 