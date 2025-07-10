"""
Tests for the get-job-logs tool of TMF ODA transformer MCP server.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from botocore.exceptions import ClientError
from awslabs.tmf_oda_transformer_mcp_server.server import get_job_logs_tool


@pytest.mark.asyncio
class TestGetJobLogs:
    """Test cases for the get-job-logs tool."""

    @patch('boto3.client')
    async def test_get_job_logs_success(self, mock_boto_client, mock_context, sample_journey_id, sample_job_id):
        """Test successful job logs retrieval."""
        # Mock S3 client and response
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        # Mock logs data
        mock_logs = [
            {
                'timestamp': '2024-01-01T12:00:00Z',
                'level': 'INFO',
                'message': 'Starting schema parsing',
                'step_id': 'schema_parsing',
                'stage_id': 'raw_analysis',
                'job_id': sample_job_id
            },
            {
                'timestamp': '2024-01-01T12:01:00Z',
                'level': 'INFO',
                'message': 'Schema parsing completed',
                'step_id': 'schema_parsing',
                'stage_id': 'raw_analysis',
                'job_id': sample_job_id
            }
        ]
        
        # Mock S3 get_object response
        mock_response = {
            'Body': Mock(),
            'LastModified': '2024-01-01T12:05:00Z',
            'ContentLength': 1024
        }
        mock_response['Body'].read.return_value = json.dumps(mock_logs).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        result = await get_job_logs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_name="raw_analysis",
            job_id=sample_job_id,
            step_name="schema_parsing"
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['journey_id'] == sample_journey_id
        assert result['stage_name'] == 'raw_analysis'
        assert result['job_id'] == sample_job_id
        assert result['step_name'] == 'schema_parsing'
        assert result['logs_found'] is True
        assert len(result['logs_data']) == 2
        assert result['metadata']['s3_bucket'] == 'transformation-journey-logs'
        assert result['metadata']['total_log_entries'] == 2
        assert result['metadata']['content_length'] == 1024
        
        # Verify S3 client was called correctly
        expected_key = f'journeys/{sample_journey_id}/stages/raw_analysis/executions/{sample_job_id}/logs/schema_parsing.json'
        mock_s3_client.get_object.assert_called_once_with(
            Bucket='transformation-journey-logs',
            Key=expected_key
        )
        
        # Verify context was not called with errors
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.create_aws_client')
    @patch.dict('os.environ', {'AWS_ROLE_ARN': 'arn:aws:iam::123456789012:role/TestRole'})
    async def test_get_job_logs_with_role_arn(self, mock_create_client, mock_context, sample_journey_id, sample_job_id):
        """Test job logs retrieval with AWS role ARN."""
        # Mock S3 client with role ARN
        mock_s3_client = Mock()
        mock_create_client.return_value = mock_s3_client
        
        # Mock logs data
        mock_logs = [{'timestamp': '2024-01-01T12:00:00Z', 'level': 'INFO', 'message': 'Test log'}]
        
        mock_response = {
            'Body': Mock(),
            'LastModified': '2024-01-01T12:05:00Z',
            'ContentLength': 512
        }
        mock_response['Body'].read.return_value = json.dumps(mock_logs).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        result = await get_job_logs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_name="raw_analysis",
            job_id=sample_job_id,
            step_name="schema_parsing"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        
        # Verify role ARN was used
        mock_create_client.assert_called_once_with('s3', role_arn='arn:aws:iam::123456789012:role/TestRole')
        
        mock_context.error.assert_not_called()

    @patch('boto3.client')
    async def test_get_job_logs_not_found(self, mock_boto_client, mock_context, sample_journey_id, sample_job_id):
        """Test job logs retrieval when logs don't exist."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        # Mock NoSuchKey exception
        mock_s3_client.get_object.side_effect = mock_s3_client.exceptions.NoSuchKey(
            error_response={'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            operation_name='GetObject'
        )
        
        result = await get_job_logs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_name="raw_analysis",
            job_id=sample_job_id,
            step_name="missing_step"
        )
        
        # Verify the result structure for not found
        assert isinstance(result, dict)
        assert result['status'] == 'not_found'
        assert result['journey_id'] == sample_journey_id
        assert result['logs_found'] is False
        assert result['logs_data'] is None
        assert result['metadata']['total_log_entries'] == 0
        assert 'may not have executed' in result['message']
        
        mock_context.error.assert_not_called()

    async def test_get_job_logs_empty_journey_id(self, mock_context):
        """Test get job logs with empty journey ID."""
        with pytest.raises(ValueError, match="Journey ID cannot be empty"):
            await get_job_logs_tool(
                ctx=mock_context,
                journey_id="",
                stage_name="raw_analysis",
                job_id="JOB-001-20240101120000",
                step_name="schema_parsing"
            )
        
        mock_context.error.assert_called_once_with("Journey ID cannot be empty")

    async def test_get_job_logs_empty_stage_name(self, mock_context, sample_journey_id):
        """Test get job logs with empty stage name."""
        with pytest.raises(ValueError, match="Stage name cannot be empty"):
            await get_job_logs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_name="",
                job_id="JOB-001-20240101120000",
                step_name="schema_parsing"
            )
        
        mock_context.error.assert_called_once_with("Stage name cannot be empty")

    async def test_get_job_logs_empty_job_id(self, mock_context, sample_journey_id):
        """Test get job logs with empty job ID."""
        with pytest.raises(ValueError, match="Job ID cannot be empty"):
            await get_job_logs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_name="raw_analysis",
                job_id="",
                step_name="schema_parsing"
            )
        
        mock_context.error.assert_called_once_with("Job ID cannot be empty")

    async def test_get_job_logs_empty_step_name(self, mock_context, sample_journey_id, sample_job_id):
        """Test get job logs with empty step name."""
        with pytest.raises(ValueError, match="Step name cannot be empty"):
            await get_job_logs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_name="raw_analysis",
                job_id=sample_job_id,
                step_name=""
            )
        
        mock_context.error.assert_called_once_with("Step name cannot be empty")

    async def test_get_job_logs_whitespace_parameters(self, mock_context):
        """Test get job logs with whitespace-only parameters."""
        with pytest.raises(ValueError, match="Journey ID cannot be empty"):
            await get_job_logs_tool(
                ctx=mock_context,
                journey_id="   ",
                stage_name="raw_analysis",
                job_id="JOB-001-20240101120000",
                step_name="schema_parsing"
            )

    @patch('boto3.client')
    async def test_get_job_logs_s3_error(self, mock_boto_client, mock_context, sample_journey_id, sample_job_id):
        """Test job logs retrieval when S3 operation fails."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        # Mock S3 error (not NoSuchKey)
        mock_s3_client.get_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='GetObject'
        )
        
        with pytest.raises(Exception, match="Error accessing S3 logs"):
            await get_job_logs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_name="raw_analysis",
                job_id=sample_job_id,
                step_name="schema_parsing"
            )
        
        mock_context.error.assert_called_once()

    @patch('boto3.client')
    async def test_get_job_logs_invalid_json(self, mock_boto_client, mock_context, sample_journey_id, sample_job_id):
        """Test job logs retrieval with invalid JSON content."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        # Mock response with invalid JSON
        mock_response = {
            'Body': Mock(),
            'LastModified': '2024-01-01T12:05:00Z',
            'ContentLength': 100
        }
        mock_response['Body'].read.return_value = b'invalid json content {'
        mock_s3_client.get_object.return_value = mock_response
        
        with pytest.raises(Exception, match="Failed to retrieve job logs"):
            await get_job_logs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_name="raw_analysis",
                job_id=sample_job_id,
                step_name="schema_parsing"
            )
        
        mock_context.error.assert_called_once()

    @patch('boto3.client')
    async def test_get_job_logs_different_stages(self, mock_boto_client, mock_context, sample_journey_id, sample_job_id):
        """Test job logs retrieval for different stage types."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        stages_and_steps = [
            ("raw_analysis", "schema_parsing"),
            ("raw_analysis", "relationship_discovery"),
            ("raw_analysis", "data_type_analysis"),
            ("stripped_schema", "schema_stripping"),
            ("stripped_schema", "core_structure_extraction"),
        ]
        
        for stage_name, step_name in stages_and_steps:
            # Mock logs for each stage/step
            mock_logs = [
                {
                    'timestamp': '2024-01-01T12:00:00Z',
                    'level': 'INFO',
                    'message': f'Starting {step_name}',
                    'step_id': step_name,
                    'stage_id': stage_name,
                    'job_id': sample_job_id
                }
            ]
            
            mock_response = {
                'Body': Mock(),
                'LastModified': '2024-01-01T12:05:00Z',
                'ContentLength': 200
            }
            mock_response['Body'].read.return_value = json.dumps(mock_logs).encode('utf-8')
            mock_s3_client.get_object.return_value = mock_response
            
            # Reset mock for each iteration
            mock_context.reset_mock()
            
            result = await get_job_logs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_name=stage_name,
                job_id=sample_job_id,
                step_name=step_name
            )
            
            assert isinstance(result, dict)
            assert result['status'] == 'success'
            assert result['stage_name'] == stage_name
            assert result['step_name'] == step_name
            
            # Verify correct S3 key was used
            expected_key = f'journeys/{sample_journey_id}/stages/{stage_name}/executions/{sample_job_id}/logs/{step_name}.json'
            mock_s3_client.get_object.assert_called_with(
                Bucket='transformation-journey-logs',
                Key=expected_key
            )
            
            mock_context.error.assert_not_called()

    @patch('boto3.client')
    async def test_get_job_logs_large_log_file(self, mock_boto_client, mock_context, sample_journey_id, sample_job_id):
        """Test job logs retrieval with large log file."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        # Create a large number of log entries
        mock_logs = []
        for i in range(1000):
            mock_logs.append({
                'timestamp': f'2024-01-01T12:{i:02d}:00Z',
                'level': 'INFO',
                'message': f'Log entry {i}',
                'step_id': 'schema_parsing',
                'stage_id': 'raw_analysis',
                'job_id': sample_job_id
            })
        
        mock_response = {
            'Body': Mock(),
            'LastModified': '2024-01-01T12:05:00Z',
            'ContentLength': 50000  # 50KB
        }
        mock_response['Body'].read.return_value = json.dumps(mock_logs).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        result = await get_job_logs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_name="raw_analysis",
            job_id=sample_job_id,
            step_name="schema_parsing"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert len(result['logs_data']) == 1000
        assert result['metadata']['total_log_entries'] == 1000
        assert result['metadata']['content_length'] == 50000
        
        mock_context.error.assert_not_called()

    @patch('boto3.client')
    async def test_get_job_logs_empty_log_file(self, mock_boto_client, mock_context, sample_journey_id, sample_job_id):
        """Test job logs retrieval with empty log file."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        # Mock empty logs array
        mock_logs = []
        
        mock_response = {
            'Body': Mock(),
            'LastModified': '2024-01-01T12:05:00Z',
            'ContentLength': 2  # Just "[]"
        }
        mock_response['Body'].read.return_value = json.dumps(mock_logs).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        result = await get_job_logs_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_name="raw_analysis",
            job_id=sample_job_id,
            step_name="schema_parsing"
        )
        
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert len(result['logs_data']) == 0
        assert result['metadata']['total_log_entries'] == 0
        
        mock_context.error.assert_not_called()

    @patch('boto3.client')
    async def test_get_job_logs_boto3_import_error(self, mock_boto_client, mock_context, sample_journey_id, sample_job_id):
        """Test job logs retrieval when boto3 operations fail."""
        # Mock boto3.client to raise an exception
        mock_boto_client.side_effect = Exception("Failed to create S3 client")
        
        with pytest.raises(Exception, match="Failed to retrieve job logs"):
            await get_job_logs_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_name="raw_analysis",
                job_id=sample_job_id,
                step_name="schema_parsing"
            )
        
        mock_context.error.assert_called_once()

    @patch('boto3.client')
    async def test_get_job_logs_s3_key_format(self, mock_boto_client, mock_context):
        """Test that S3 key format is correct for various parameters."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        # Mock NoSuchKey to avoid actual S3 calls
        mock_s3_client.get_object.side_effect = mock_s3_client.exceptions.NoSuchKey(
            error_response={'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            operation_name='GetObject'
        )
        
        test_cases = [
            {
                'journey_id': 'JRN-TEST-001',
                'stage_name': 'raw_analysis',
                'job_id': 'JOB-001-20240101120000',
                'step_name': 'schema_parsing',
                'expected_key': 'journeys/JRN-TEST-001/stages/raw_analysis/executions/JOB-001-20240101120000/logs/schema_parsing.json'
            },
            {
                'journey_id': 'JRN-CUSTOMER-ANALYSIS',
                'stage_name': 'stripped_schema',
                'job_id': 'JOB-002-20240201150000',
                'step_name': 'core_structure_extraction',
                'expected_key': 'journeys/JRN-CUSTOMER-ANALYSIS/stages/stripped_schema/executions/JOB-002-20240201150000/logs/core_structure_extraction.json'
            }
        ]
        
        for test_case in test_cases:
            # Reset mock for each test case
            mock_s3_client.reset_mock()
            mock_context.reset_mock()
            
            result = await get_job_logs_tool(
                ctx=mock_context,
                journey_id=test_case['journey_id'],
                stage_name=test_case['stage_name'],
                job_id=test_case['job_id'],
                step_name=test_case['step_name']
            )
            
            # Verify correct S3 key was used
            mock_s3_client.get_object.assert_called_once_with(
                Bucket='transformation-journey-logs',
                Key=test_case['expected_key']
            )
            
            assert result['status'] == 'not_found'  # Because we're mocking NoSuchKey
            mock_context.error.assert_not_called() 