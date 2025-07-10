"""
Tests for the raw-analysis tool of TMF ODA transformer MCP server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import raw_analysis_tool


@pytest.mark.asyncio
class TestRawAnalysis:
    """Test cases for the raw-analysis tool."""

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor')
    async def test_raw_analysis_success(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test successful raw analysis execution."""
        # Configure the mock executor
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await raw_analysis_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="raw_analysis",
            triggered_by="test-user",
            reason="Testing raw analysis"
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['journey_id'] == sample_journey_id
        assert result['stage_id'] == 'raw_analysis'
        assert result['triggered_by'] == 'test-user'
        assert result['reason'] == 'Testing raw analysis'
        assert 'job_id' in result
        assert 'start_time' in result
        assert 'end_time' in result
        assert 'duration_seconds' in result
        assert 'message' in result
        
        # Verify executor methods were called
        mock_transformation_job_executor.start_job_execution.assert_called_once_with(
            journey_id=sample_journey_id,
            stage_id="raw_analysis",
            triggered_by="test-user",
            reason="Testing raw analysis"
        )
        mock_transformation_job_executor.execute_job.assert_called_once()
        
        # Verify context was not called with errors
        mock_context.error.assert_not_called()

    async def test_raw_analysis_default_parameters(self, mock_context, sample_journey_id):
        """Test raw analysis with default parameters."""
        with patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor.start_job_execution.return_value = "JOB-001-20240101120000"
            mock_executor_class.return_value = mock_executor
            
            result = await raw_analysis_tool(
                ctx=mock_context,
                journey_id=sample_journey_id
                # Using all default parameters
            )
            
            assert isinstance(result, dict)
            assert result['status'] == 'success'
            assert result['journey_id'] == sample_journey_id
            assert result['stage_id'] == 'raw_analysis'  # Default value
            assert result['triggered_by'] == 'mcp-server'  # Default value
            assert result['reason'] == 'MCP Server execution'  # Default value
            
            mock_context.error.assert_not_called()

    async def test_raw_analysis_executor_not_available(self, mock_context, sample_journey_id):
        """Test raw analysis when TransformationJobExecutor is not available."""
        with patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor', None):
            with pytest.raises(Exception, match="TransformationJobExecutor not available"):
                await raw_analysis_tool(
                    ctx=mock_context,
                    journey_id=sample_journey_id,
                    stage_id="raw_analysis",
                    triggered_by="test-user",
                    reason="Testing"
                )
            
            mock_context.error.assert_called_once()

    async def test_raw_analysis_empty_journey_id(self, mock_context):
        """Test raw analysis with empty journey ID."""
        with pytest.raises(ValueError, match="Journey ID cannot be empty"):
            await raw_analysis_tool(
                ctx=mock_context,
                journey_id="",
                stage_id="raw_analysis",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Journey ID cannot be empty")

    async def test_raw_analysis_whitespace_journey_id(self, mock_context):
        """Test raw analysis with whitespace-only journey ID."""
        with pytest.raises(ValueError, match="Journey ID cannot be empty"):
            await raw_analysis_tool(
                ctx=mock_context,
                journey_id="   ",
                stage_id="raw_analysis",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Journey ID cannot be empty")

    async def test_raw_analysis_empty_stage_id(self, mock_context, sample_journey_id):
        """Test raw analysis with empty stage ID."""
        with pytest.raises(ValueError, match="Stage ID cannot be empty"):
            await raw_analysis_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_id="",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Stage ID cannot be empty")

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor')
    async def test_raw_analysis_executor_start_job_failure(self, mock_executor_class, mock_context, sample_journey_id):
        """Test raw analysis when job execution start fails."""
        mock_executor = Mock()
        mock_executor.start_job_execution.side_effect = Exception("Failed to start job")
        mock_executor_class.return_value = mock_executor
        
        result = await raw_analysis_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="raw_analysis",
            triggered_by="test-user",
            reason="Testing"
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert result['journey_id'] == sample_journey_id
        assert 'error_message' in result
        assert 'Failed to start job' in result['error_message']
        
        mock_context.error.assert_called_once()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor')
    async def test_raw_analysis_executor_execute_job_failure(self, mock_executor_class, mock_context, sample_journey_id):
        """Test raw analysis when job execution fails."""
        mock_executor = Mock()
        mock_executor.start_job_execution.return_value = "JOB-001-20240101120000"
        mock_executor.execute_job.side_effect = Exception("Job execution failed")
        mock_executor_class.return_value = mock_executor
        
        result = await raw_analysis_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="raw_analysis",
            triggered_by="test-user",
            reason="Testing"
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert result['journey_id'] == sample_journey_id
        assert 'error_message' in result
        assert 'Job execution failed' in result['error_message']
        
        mock_context.error.assert_called_once()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor')
    async def test_raw_analysis_custom_stage_id(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test raw analysis with custom stage ID."""
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await raw_analysis_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="custom_raw_analysis",
            triggered_by="test-user",
            reason="Testing custom stage"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['stage_id'] == 'custom_raw_analysis'
        
        mock_transformation_job_executor.start_job_execution.assert_called_once_with(
            journey_id=sample_journey_id,
            stage_id="custom_raw_analysis",
            triggered_by="test-user",
            reason="Testing custom stage"
        )
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor')
    async def test_raw_analysis_timing_measurement(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that raw analysis measures execution time correctly."""
        import time
        
        # Add delay to simulate processing time
        def delayed_execute_job(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
        
        mock_transformation_job_executor.execute_job.side_effect = delayed_execute_job
        mock_executor_class.return_value = mock_transformation_job_executor
        
        start_time = time.time()
        result = await raw_analysis_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="raw_analysis",
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

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor')
    async def test_raw_analysis_job_id_format(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that job ID format is correct."""
        expected_job_id = "JOB-001-20240101120000"
        mock_transformation_job_executor.start_job_execution.return_value = expected_job_id
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await raw_analysis_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="raw_analysis",
            triggered_by="test-user",
            reason="Testing job ID"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['job_id'] == expected_job_id
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor')
    @patch.dict('os.environ', {'AWS_ROLE_ARN': 'arn:aws:iam::123456789012:role/TestRole'})
    async def test_raw_analysis_with_aws_role(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test raw analysis with AWS role ARN configured."""
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await raw_analysis_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="raw_analysis",
            triggered_by="test-user",
            reason="Testing with AWS role"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        
        # Verify executor was created with role ARN
        mock_executor_class.assert_called_once_with(role_arn='arn:aws:iam::123456789012:role/TestRole')
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationJobExecutor')
    async def test_raw_analysis_result_message_format(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that result message is properly formatted."""
        expected_job_id = "JOB-001-20240101120000"
        mock_transformation_job_executor.start_job_execution.return_value = expected_job_id
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await raw_analysis_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="raw_analysis",
            triggered_by="test-user",
            reason="Testing message format"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert 'message' in result
        assert expected_job_id in result['message']
        assert 'completed successfully' in result['message']
        
        mock_context.error.assert_not_called() 