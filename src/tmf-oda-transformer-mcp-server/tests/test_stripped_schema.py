"""
Tests for the stripped-schema tool of TMF ODA transformer MCP server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import stripped_schema_tool


@pytest.mark.asyncio
class TestStrippedSchema:
    """Test cases for the stripped-schema tool."""

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_success(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test successful stripped schema execution."""
        # Configure the mock executor
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing stripped schema"
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['journey_id'] == sample_journey_id
        assert result['stage_id'] == 'stripped_schema'
        assert result['triggered_by'] == 'test-user'
        assert result['reason'] == 'Testing stripped schema'
        assert 'job_id' in result
        assert 'start_time' in result
        assert 'end_time' in result
        assert 'duration_seconds' in result
        assert 'message' in result
        
        # Verify executor methods were called
        mock_transformation_job_executor.start_job_execution.assert_called_once_with(
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing stripped schema"
        )
        mock_transformation_job_executor.execute_job.assert_called_once()
        
        # Verify context was not called with errors
        mock_context.error.assert_not_called()

    async def test_stripped_schema_default_parameters(self, mock_context, sample_journey_id):
        """Test stripped schema with default parameters."""
        with patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor.start_job_execution.return_value = "JOB-002-20240101120000"
            mock_executor_class.return_value = mock_executor
            
            result = await stripped_schema_tool(
                ctx=mock_context,
                journey_id=sample_journey_id
                # Using all default parameters
            )
            
            assert isinstance(result, dict)
            assert result['status'] == 'success'
            assert result['journey_id'] == sample_journey_id
            assert result['stage_id'] == 'stripped_schema'  # Default value
            assert result['triggered_by'] == 'mcp-server'  # Default value
            assert result['reason'] == 'MCP Server execution'  # Default value
            
            mock_context.error.assert_not_called()

    async def test_stripped_schema_executor_not_available(self, mock_context, sample_journey_id):
        """Test stripped schema when TransformationJobExecutor is not available."""
        with patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor', None):
            with pytest.raises(Exception, match="TransformationJobExecutor not available"):
                await stripped_schema_tool(
                    ctx=mock_context,
                    journey_id=sample_journey_id,
                    stage_id="stripped_schema",
                    triggered_by="test-user",
                    reason="Testing"
                )
            
            mock_context.error.assert_called_once()

    async def test_stripped_schema_empty_journey_id(self, mock_context):
        """Test stripped schema with empty journey ID."""
        with pytest.raises(ValueError, match="Journey ID cannot be empty"):
            await stripped_schema_tool(
                ctx=mock_context,
                journey_id="",
                stage_id="stripped_schema",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Journey ID cannot be empty")

    async def test_stripped_schema_whitespace_journey_id(self, mock_context):
        """Test stripped schema with whitespace-only journey ID."""
        with pytest.raises(ValueError, match="Journey ID cannot be empty"):
            await stripped_schema_tool(
                ctx=mock_context,
                journey_id="   ",
                stage_id="stripped_schema",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Journey ID cannot be empty")

    async def test_stripped_schema_empty_stage_id(self, mock_context, sample_journey_id):
        """Test stripped schema with empty stage ID."""
        with pytest.raises(ValueError, match="Stage ID cannot be empty"):
            await stripped_schema_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_id="",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Stage ID cannot be empty")

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_executor_start_job_failure(self, mock_executor_class, mock_context, sample_journey_id):
        """Test stripped schema when job execution start fails."""
        mock_executor = Mock()
        mock_executor.start_job_execution.side_effect = Exception("Failed to start stripped schema job")
        mock_executor_class.return_value = mock_executor
        
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing"
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert result['journey_id'] == sample_journey_id
        assert 'error_message' in result
        assert 'Failed to start stripped schema job' in result['error_message']
        
        mock_context.error.assert_called_once()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_executor_execute_job_failure(self, mock_executor_class, mock_context, sample_journey_id):
        """Test stripped schema when job execution fails."""
        mock_executor = Mock()
        mock_executor.start_job_execution.return_value = "JOB-002-20240101120000"
        mock_executor.execute_job.side_effect = Exception("Stripped schema job execution failed")
        mock_executor_class.return_value = mock_executor
        
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing"
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert result['journey_id'] == sample_journey_id
        assert 'error_message' in result
        assert 'Stripped schema job execution failed' in result['error_message']
        
        mock_context.error.assert_called_once()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_custom_stage_id(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test stripped schema with custom stage ID."""
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="custom_stripped_schema",
            triggered_by="test-user",
            reason="Testing custom stage"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['stage_id'] == 'custom_stripped_schema'
        
        mock_transformation_job_executor.start_job_execution.assert_called_once_with(
            journey_id=sample_journey_id,
            stage_id="custom_stripped_schema",
            triggered_by="test-user",
            reason="Testing custom stage"
        )
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_timing_measurement(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that stripped schema measures execution time correctly."""
        import time
        
        # Add delay to simulate processing time
        def delayed_execute_job(*args, **kwargs):
            time.sleep(0.15)  # 150ms delay
        
        mock_transformation_job_executor.execute_job.side_effect = delayed_execute_job
        mock_executor_class.return_value = mock_transformation_job_executor
        
        start_time = time.time()
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing timing"
        )
        end_time = time.time()
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert 'duration_seconds' in result
        assert result['duration_seconds'] > 0
        assert result['duration_seconds'] <= (end_time - start_time) + 1  # Allow some tolerance
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_job_id_format(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that job ID format is correct."""
        expected_job_id = "JOB-002-20240101120000"
        mock_transformation_job_executor.start_job_execution.return_value = expected_job_id
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing job ID"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['job_id'] == expected_job_id
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    @patch.dict('os.environ', {'AWS_ROLE_ARN': 'arn:aws:iam::123456789012:role/TestRole'})
    async def test_stripped_schema_with_aws_role(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test stripped schema with AWS role ARN configured."""
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing with AWS role"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        
        # Verify executor was created with role ARN
        mock_executor_class.assert_called_once_with(role_arn='arn:aws:iam::123456789012:role/TestRole')
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_result_message_format(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that result message is properly formatted."""
        expected_job_id = "JOB-002-20240101120000"
        mock_transformation_job_executor.start_job_execution.return_value = expected_job_id
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing message format"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert 'message' in result
        assert expected_job_id in result['message']
        assert 'completed successfully' in result['message']
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_sequential_after_raw_analysis(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test stripped schema as second stage after raw analysis."""
        mock_executor_class.return_value = mock_transformation_job_executor
        
        # First execute raw analysis
        raw_result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Second stage after raw analysis"
        )
        
        assert isinstance(raw_result, dict)
        assert raw_result['status'] == 'success'
        assert raw_result['reason'] == "Second stage after raw analysis"
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_different_journey_id(self, mock_executor_class, mock_context, mock_transformation_job_executor):
        """Test stripped schema with different journey ID format."""
        journey_id = "JRN-CUSTOMER-ANALYSIS-2024"
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=journey_id,
            stage_id="stripped_schema",
            triggered_by="automated-system",
            reason="Customer analysis workflow"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['journey_id'] == journey_id
        assert result['triggered_by'] == 'automated-system'
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_stripped_schema_error_recovery(self, mock_executor_class, mock_context, sample_journey_id):
        """Test error handling and recovery in stripped schema execution."""
        mock_executor = Mock()
        mock_executor.start_job_execution.return_value = "JOB-002-20240101120000"
        mock_executor.execute_job.side_effect = [
            Exception("Temporary failure"),  # First call fails
        ]
        mock_executor_class.return_value = mock_executor
        
        result = await stripped_schema_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing error recovery"
        )
        
        # Should return error result but handle gracefully
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert 'error_message' in result
        assert 'Temporary failure' in result['error_message']
        
        mock_context.error.assert_called_once() 