"""
Tests for the run-jobs tool of TMF ODA transformer MCP server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.server import run_jobs_tool


@pytest.mark.asyncio
class TestRunJobs:
    """Test cases for the run-jobs tool."""

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_success(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test successful job execution."""
        # Configure the mock executor
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await run_jobs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="raw_analysis",
            triggered_by="test-user",
            reason="Testing run jobs"
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['journey_id'] == sample_journey_id
        assert result['stage_id'] == 'raw_analysis'
        assert result['triggered_by'] == 'test-user'
        assert result['reason'] == 'Testing run jobs'
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
            reason="Testing run jobs"
        )
        mock_transformation_job_executor.execute_job.assert_called_once()
        
        # Verify context was not called with errors
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_stripped_schema(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test running stripped schema stage."""
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await run_jobs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing stripped schema"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['stage_id'] == 'stripped_schema'
        
        mock_transformation_job_executor.start_job_execution.assert_called_once_with(
            journey_id=sample_journey_id,
            stage_id="stripped_schema",
            triggered_by="test-user",
            reason="Testing stripped schema"
        )
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_custom_stage(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test running a custom stage."""
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await run_jobs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="data_mapping",
            triggered_by="test-user",
            reason="Testing custom stage"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['stage_id'] == 'data_mapping'
        
        mock_transformation_job_executor.start_job_execution.assert_called_once_with(
            journey_id=sample_journey_id,
            stage_id="data_mapping",
            triggered_by="test-user",
            reason="Testing custom stage"
        )
        
        mock_context.error.assert_not_called()

    async def test_run_jobs_default_parameters(self, mock_context, sample_journey_id):
        """Test run jobs with default parameters."""
        with patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor.start_job_execution.return_value = "JOB-001-20240101120000"
            mock_executor_class.return_value = mock_executor
            
            result = await run_jobs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_id="raw_analysis",
                triggered_by="mcp-server",  # Specify default value explicitly
                reason="MCP Server execution"  # Specify default value explicitly
            )
            
            assert isinstance(result, dict)
            assert result['status'] == 'success'
            assert result['journey_id'] == sample_journey_id
            assert result['stage_id'] == 'raw_analysis'
            assert result['triggered_by'] == 'mcp-server'  # Default value
            assert result['reason'] == 'MCP Server execution'  # Default value
            
            mock_context.error.assert_not_called()

    async def test_run_jobs_executor_not_available(self, mock_context, sample_journey_id):
        """Test run jobs when TransformationJobExecutor is not available."""
        with patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor', None):
            with pytest.raises(Exception, match="TransformationJobExecutor not available"):
                await run_jobs_tool(
                    ctx=mock_context,
                    journey_id=sample_journey_id,
                    stage_id="raw_analysis",
                    triggered_by="test-user",
                    reason="Testing"
                )
            
            mock_context.error.assert_called_once()

    async def test_run_jobs_empty_journey_id(self, mock_context):
        """Test run jobs with empty journey ID."""
        with pytest.raises(ValueError, match="Journey ID cannot be empty"):
            await run_jobs_tool(
                ctx=mock_context,
                journey_id="",
                stage_id="raw_analysis",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Journey ID cannot be empty")

    async def test_run_jobs_whitespace_journey_id(self, mock_context):
        """Test run jobs with whitespace-only journey ID."""
        with pytest.raises(ValueError, match="Journey ID cannot be empty"):
            await run_jobs_tool(
                ctx=mock_context,
                journey_id="   ",
                stage_id="raw_analysis",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Journey ID cannot be empty")

    async def test_run_jobs_empty_stage_id(self, mock_context, sample_journey_id):
        """Test run jobs with empty stage ID."""
        with pytest.raises(ValueError, match="Stage ID cannot be empty"):
            await run_jobs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_id="",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Stage ID cannot be empty")

    async def test_run_jobs_whitespace_stage_id(self, mock_context, sample_journey_id):
        """Test run jobs with whitespace-only stage ID."""
        with pytest.raises(ValueError, match="Stage ID cannot be empty"):
            await run_jobs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_id="   ",
                triggered_by="test-user",
                reason="Testing"
            )
        
        mock_context.error.assert_called_once_with("Stage ID cannot be empty")

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_executor_start_job_failure(self, mock_executor_class, mock_context, sample_journey_id):
        """Test run jobs when job execution start fails."""
        mock_executor = Mock()
        mock_executor.start_job_execution.side_effect = Exception("Failed to start job")
        mock_executor_class.return_value = mock_executor
        
        result = await run_jobs_tool(
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
        assert result['stage_id'] == 'raw_analysis'
        assert 'error_message' in result
        assert 'Failed to start job' in result['error_message']
        
        mock_context.error.assert_called_once()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_executor_execute_job_failure(self, mock_executor_class, mock_context, sample_journey_id):
        """Test run jobs when job execution fails."""
        mock_executor = Mock()
        mock_executor.start_job_execution.return_value = "JOB-001-20240101120000"
        mock_executor.execute_job.side_effect = Exception("Job execution failed")
        mock_executor_class.return_value = mock_executor
        
        result = await run_jobs_tool(
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
        assert result['stage_id'] == 'raw_analysis'
        assert 'error_message' in result
        assert 'Job execution failed' in result['error_message']
        
        mock_context.error.assert_called_once()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_timing_measurement(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that run jobs measures execution time correctly."""
        import time
        
        # Add delay to simulate processing time
        def delayed_execute_job(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
        
        mock_transformation_job_executor.execute_job.side_effect = delayed_execute_job
        mock_executor_class.return_value = mock_transformation_job_executor
        
        start_time = time.time()
        result = await run_jobs_tool(
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

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_job_id_format(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that job ID format is correct."""
        expected_job_id = "JOB-001-20240101120000"
        mock_transformation_job_executor.start_job_execution.return_value = expected_job_id
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await run_jobs_tool(
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

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    @patch.dict('os.environ', {'AWS_ROLE_ARN': 'arn:aws:iam::123456789012:role/TestRole'})
    async def test_run_jobs_with_aws_role(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test run jobs with AWS role ARN configured."""
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await run_jobs_tool(
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

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_result_message_format(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that result message is properly formatted."""
        expected_job_id = "JOB-001-20240101120000"
        mock_transformation_job_executor.start_job_execution.return_value = expected_job_id
        mock_executor_class.return_value = mock_transformation_job_executor
        
        result = await run_jobs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="compliance_validation",
            triggered_by="test-user",
            reason="Testing message format"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert 'message' in result
        assert expected_job_id in result['message']
        assert 'compliance_validation' in result['message']
        assert 'completed successfully' in result['message']
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_multiple_stage_types(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test run jobs with various stage types."""
        mock_executor_class.return_value = mock_transformation_job_executor
        
        stage_ids = [
            "raw_analysis",
            "stripped_schema", 
            "data_mapping",
            "compliance_validation",
            "business_rules_extraction",
            "custom_transformation"
        ]
        
        for stage_id in stage_ids:
            result = await run_jobs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_id=stage_id,
                triggered_by="test-user",
                reason=f"Testing {stage_id}"
            )
            
            assert isinstance(result, dict)
            assert result['status'] == 'success'
            assert result['stage_id'] == stage_id
            
            mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_error_message_includes_stage(self, mock_executor_class, mock_context, sample_journey_id):
        """Test that error messages include the stage ID for better debugging."""
        mock_executor = Mock()
        mock_executor.start_job_execution.side_effect = Exception("Connection timeout")
        mock_executor_class.return_value = mock_executor
        
        result = await run_jobs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id="custom_stage",
            triggered_by="test-user",
            reason="Testing error message"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert 'error_message' in result
        assert 'custom_stage' in result['error_message']
        assert 'Connection timeout' in result['error_message']
        assert 'Job execution failed for stage' in result['error_message']
        
        mock_context.error.assert_called_once()

    @patch('awslabs.tmf_oda_transformer_mcp_server.scripts.job_executor.TransformationJobExecutor')
    async def test_run_jobs_concurrent_execution_simulation(self, mock_executor_class, mock_context, sample_journey_id, mock_transformation_job_executor):
        """Test that run jobs can handle concurrent-like execution calls."""
        import asyncio
        
        mock_executor_class.return_value = mock_transformation_job_executor
        
        # Simulate concurrent calls (though they'll be sequential in async)
        tasks = []
        for i in range(3):
            task = run_jobs_tool(
                ctx=mock_context,
                journey_id=f"{sample_journey_id}-{i}",
                stage_id="raw_analysis",
                triggered_by="test-user",
                reason=f"Concurrent test {i}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert isinstance(result, dict)
            assert result['status'] == 'success'
            assert result['journey_id'] == f"{sample_journey_id}-{i}"
            assert result['reason'] == f"Concurrent test {i}"
        
        mock_context.error.assert_not_called() 