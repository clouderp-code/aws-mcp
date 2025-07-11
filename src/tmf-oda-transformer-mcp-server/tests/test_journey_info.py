"""
Tests for the journey-info tool of TMF ODA transformer MCP server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, call
from awslabs.tmf_oda_transformer_mcp_server.server import journey_info_tool


@pytest.mark.asyncio
class TestJourneyInfo:
    """Test cases for the journey-info tool."""

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_list_all_journeys_success(self, mock_utils_class, mock_context):
        """Test successful listing of all journeys."""
        # Mock TransformationUtils instance and methods
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        
        # Mock journey data
        mock_journeys = [
            {
                'journeyId': 'JRN-TEST-001',
                'name': 'Customer Data Migration',
                'status': 'running',
                'createdAt': '2024-01-01T12:00:00Z',
                'currentStage': 'raw_analysis',
                'progress': 45
            },
            {
                'journeyId': 'JRN-TEST-002',
                'name': 'Product Catalog Transformation',
                'status': 'completed',
                'createdAt': '2024-01-02T14:00:00Z',
                'currentStage': 'final_validation',
                'progress': 100
            },
            {
                'journeyId': 'JRN-TEST-003',
                'name': 'Order Management Setup',
                'status': 'failed',
                'createdAt': '2024-01-03T10:00:00Z',
                'currentStage': 'stripped_schema',
                'progress': 25
            }
        ]
        
        mock_utils.list_journeys.return_value = mock_journeys
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=None,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert result['operation'] == 'list_all_journeys'
        assert result['status'] == 'success'
        assert 'timestamp' in result
        assert 'duration_seconds' in result
        
        # Verify summary statistics
        summary = result['summary']
        assert summary['total_journeys'] == 3
        assert summary['status_distribution']['running'] == 1
        assert summary['status_distribution']['completed'] == 1
        assert summary['status_distribution']['failed'] == 1
        assert summary['active_journeys'] == 1  # running
        assert summary['completed_journeys'] == 1
        assert summary['failed_journeys'] == 1
        
        # Verify journeys data
        assert len(result['journeys']) == 3
        assert result['journeys'][0]['journeyId'] == 'JRN-TEST-001'
        assert result['message'] == 'Retrieved 3 transformation journeys'
        
        # Verify mocks were called correctly
        mock_utils_class.assert_called_once()
        mock_utils.list_journeys.assert_called_once()
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_list_all_journeys_empty(self, mock_utils_class, mock_context):
        """Test listing all journeys when no journeys exist."""
        # Mock TransformationUtils instance
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        mock_utils.list_journeys.return_value = []
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=None,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        assert isinstance(result, dict)
        assert result['operation'] == 'list_all_journeys'
        assert result['status'] == 'success'
        assert result['summary']['total_journeys'] == 0
        assert result['summary']['active_journeys'] == 0
        assert len(result['journeys']) == 0
        assert result['message'] == 'Retrieved 0 transformation journeys'
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_get_journey_details_success(self, mock_utils_class, mock_context, sample_journey_id):
        """Test successful retrieval of detailed journey information."""
        # Mock TransformationUtils instance
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        
        # Mock journey status data
        mock_journey_status = {
            'journeyId': sample_journey_id,
            'name': 'Customer Data Migration',
            'status': 'running',
            'overallProgress': 65,
            'currentStageId': 'raw_analysis',
            'createdAt': '2024-01-01T12:00:00Z',
            'currentJobs': {
                'raw_analysis': {
                    'jobId': 'JOB-001-20240101120000',
                    'status': 'completed'
                }
            },
            'aggregates': {
                'totalJobs': 5,
                'completedJobs': 3,
                'failedJobs': 1
            }
        }
        
        # Mock stages data
        mock_stages = [
            {
                'stageId': 'raw_analysis',
                'name': 'Raw Analysis',
                'description': 'Initial data analysis',
                'order': 1,
                'canSkip': False,
                'estimatedDuration': '30 minutes',
                'steps': [
                    {
                        'id': 'schema_parsing',
                        'name': 'Schema Parsing',
                        'description': 'Parse database schemas',
                        'order': 1,
                        'estimatedDuration': '10 minutes'
                    }
                ]
            },
            {
                'stageId': 'stripped_schema',
                'name': 'Stripped Schema',
                'description': 'Schema simplification',
                'order': 2,
                'canSkip': False,
                'estimatedDuration': '20 minutes',
                'steps': []
            }
        ]
        
        # Mock job data for each stage
        mock_jobs_raw = [
            {
                'jobId': 'JOB-001-20240101120000',
                'executionNumber': 1,
                'status': 'completed',
                'startTime': '2024-01-01T12:00:00Z',
                'endTime': '2024-01-01T12:30:00Z',
                'duration': '30 minutes',
                'progress': 100
            }
        ]
        
        mock_jobs_stripped = []
        
        mock_utils.get_journey_status.return_value = mock_journey_status
        mock_utils.get_journey_stages.return_value = mock_stages
        mock_utils.get_stage_jobs.side_effect = [mock_jobs_raw, mock_jobs_stripped]
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert result['operation'] == 'get_journey_details'
        assert result['journey_id'] == sample_journey_id
        assert result['status'] == 'success'
        assert 'timestamp' in result
        assert 'duration_seconds' in result
        
        # Verify journey status
        assert result['journey_status'] == mock_journey_status
        
        # Verify stages information
        assert result['stages']['total_stages'] == 2
        assert len(result['stages']['stages_list']) == 2
        assert result['stages']['stages_list'][0]['stageId'] == 'raw_analysis'
        
        # Verify stage job summary
        assert 'stage_job_summary' in result
        assert 'raw_analysis' in result['stage_job_summary']
        assert 'stripped_schema' in result['stage_job_summary']
        assert result['stage_job_summary']['raw_analysis']['total_jobs'] == 1
        assert result['stage_job_summary']['stripped_schema']['total_jobs'] == 0
        
        # Verify summary
        summary = result['summary']
        assert summary['journey_name'] == 'Customer Data Migration'
        assert summary['current_status'] == 'running'
        assert summary['overall_progress'] == 65
        assert summary['total_stages'] == 2
        assert summary['total_job_executions'] == 1
        
        # Verify method calls
        mock_utils.get_journey_status.assert_called_once_with(sample_journey_id)
        mock_utils.get_journey_stages.assert_called_once_with(sample_journey_id)
        assert mock_utils.get_stage_jobs.call_count == 2
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_get_journey_details_with_stage_id(self, mock_utils_class, mock_context, sample_journey_id):
        """Test retrieval of journey details for a specific stage."""
        # Mock TransformationUtils instance
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        
        mock_journey_status = {
            'journeyId': sample_journey_id,
            'name': 'Test Journey',
            'status': 'running'
        }
        
        mock_stages = [
            {
                'stageId': 'raw_analysis',
                'name': 'Raw Analysis',
                'description': 'Initial analysis',
                'order': 1
            }
        ]
        
        mock_stage_jobs = [
            {
                'jobId': 'JOB-001-20240101120000',
                'executionNumber': 1,
                'status': 'completed',
                'startTime': '2024-01-01T12:00:00Z',
                'progress': 100
            },
            {
                'jobId': 'JOB-002-20240101140000',
                'executionNumber': 2,
                'status': 'failed',
                'startTime': '2024-01-01T14:00:00Z',
                'progress': 50
            }
        ]
        
        mock_utils.get_journey_status.return_value = mock_journey_status
        mock_utils.get_journey_stages.return_value = mock_stages
        mock_utils.get_stage_jobs.return_value = mock_stage_jobs
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id='raw_analysis',
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        
        # Verify stage details
        assert 'stage_details' in result
        stage_details = result['stage_details']
        assert stage_details['stage_id'] == 'raw_analysis'
        assert stage_details['total_jobs'] == 2
        assert len(stage_details['jobs']) == 2
        assert stage_details['jobs'][0]['jobId'] == 'JOB-001-20240101120000'
        
        # Verify message
        assert 'stage raw_analysis with 2 job executions' in result['message']
        
        # Verify method calls
        mock_utils.get_stage_jobs.assert_called_once_with(sample_journey_id, 'raw_analysis', limit=10)
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_get_journey_details_no_stages(self, mock_utils_class, mock_context, sample_journey_id):
        """Test journey details retrieval without stage information."""
        # Mock TransformationUtils instance
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        
        mock_journey_status = {
            'journeyId': sample_journey_id,
            'name': 'Test Journey',
            'status': 'pending'
        }
        
        mock_utils.get_journey_status.return_value = mock_journey_status
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id=None,
            include_stages=False,
            include_job_history=False,
            job_limit=10
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert result['journey_status'] == mock_journey_status
        
        # Verify stages and job history were not requested
        assert 'stages' not in result
        assert 'stage_job_summary' not in result
        assert 'stage_details' not in result
        
        # Verify method calls
        mock_utils.get_journey_status.assert_called_once_with(sample_journey_id)
        mock_utils.get_journey_stages.assert_not_called()
        mock_utils.get_stage_jobs.assert_not_called()
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_journey_not_found(self, mock_utils_class, mock_context):
        """Test retrieval of non-existent journey."""
        # Mock TransformationUtils instance
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        mock_utils.get_journey_status.return_value = None
        
        invalid_journey_id = 'JRN-NONEXISTENT'
        
        # The function catches the ValueError and returns an error result instead of raising it
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=invalid_journey_id,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify error result structure
        assert isinstance(result, dict)
        assert result['operation'] == 'get_journey_info'
        assert result['journey_id'] == invalid_journey_id
        assert result['status'] == 'error'
        assert 'error_message' in result
        assert f'Journey {invalid_journey_id} not found' in result['error_message']
        
        # The function calls error twice: once when the ValueError is raised, once when it's caught
        assert mock_context.error.call_count == 2
        mock_context.error.assert_has_calls([
            call(f'Journey {invalid_journey_id} not found'),
            call(f'Failed to retrieve journey information: Journey {invalid_journey_id} not found')
        ])

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils', None)
    async def test_transformation_utils_not_available(self, mock_context, sample_journey_id):
        """Test journey info tool when TransformationUtils is not available."""
        with pytest.raises(Exception, match="TransformationUtils not available"):
            await journey_info_tool(
                ctx=mock_context,
                journey_id=sample_journey_id,
                stage_id=None,
                include_stages=True,
                include_job_history=True,
                job_limit=10
            )
        
        mock_context.error.assert_called_once_with("TransformationUtils not available - cannot retrieve journey information")

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_journey_info_exception_handling(self, mock_utils_class, mock_context, sample_journey_id):
        """Test exception handling in journey info tool."""
        # Mock TransformationUtils to raise an exception
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        mock_utils.get_journey_status.side_effect = Exception("Database connection failed")
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify error result structure
        assert isinstance(result, dict)
        assert result['operation'] == 'get_journey_info'
        assert result['journey_id'] == sample_journey_id
        assert result['status'] == 'error'
        assert 'error_message' in result
        assert 'Database connection failed' in result['error_message']
        assert 'duration_seconds' in result
        
        mock_context.error.assert_called_once()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_list_journeys_exception_handling(self, mock_utils_class, mock_context):
        """Test exception handling when listing journeys fails."""
        # Mock TransformationUtils to raise an exception
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        mock_utils.list_journeys.side_effect = Exception("DynamoDB access denied")
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=None,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify error result structure
        assert isinstance(result, dict)
        assert result['operation'] == 'get_journey_info'
        assert result['status'] == 'error'
        assert 'DynamoDB access denied' in result['error_message']
        
        mock_context.error.assert_called_once()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_journey_info_with_job_limit(self, mock_utils_class, mock_context, sample_journey_id):
        """Test journey info tool with custom job limit."""
        # Mock TransformationUtils instance
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        
        mock_journey_status = {'journeyId': sample_journey_id, 'name': 'Test Journey'}
        mock_stages = [{'stageId': 'raw_analysis', 'name': 'Raw Analysis'}]
        mock_jobs = [{'jobId': f'JOB-{i:03d}', 'status': 'completed'} for i in range(20)]
        
        mock_utils.get_journey_status.return_value = mock_journey_status
        mock_utils.get_journey_stages.return_value = mock_stages
        mock_utils.get_stage_jobs.return_value = mock_jobs
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id='raw_analysis',
            include_stages=True,
            include_job_history=True,
            job_limit=5
        )
        
        # Verify job limit was passed correctly
        mock_utils.get_stage_jobs.assert_called_once_with(sample_journey_id, 'raw_analysis', limit=5)
        
        # Verify result contains the jobs (mocked to return all 20, but limit should be passed)
        assert result['stage_details']['total_jobs'] == 20
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_journey_info_stages_without_job_history(self, mock_utils_class, mock_context, sample_journey_id):
        """Test journey info with stages but without job history."""
        # Mock TransformationUtils instance
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        
        mock_journey_status = {'journeyId': sample_journey_id, 'name': 'Test Journey'}
        mock_stages = [
            {'stageId': 'raw_analysis', 'name': 'Raw Analysis'},
            {'stageId': 'stripped_schema', 'name': 'Stripped Schema'}
        ]
        
        mock_utils.get_journey_status.return_value = mock_journey_status
        mock_utils.get_journey_stages.return_value = mock_stages
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id=None,
            include_stages=True,
            include_job_history=False,
            job_limit=10
        )
        
        # Verify stages are included but job history is not
        assert 'stages' in result
        assert result['stages']['total_stages'] == 2
        assert 'stage_job_summary' not in result
        assert 'stage_details' not in result
        
        # Verify get_stage_jobs was not called
        mock_utils.get_stage_jobs.assert_not_called()
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_journey_info_complex_status_distribution(self, mock_utils_class, mock_context):
        """Test journey info with complex status distribution."""
        # Mock TransformationUtils instance
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        
        # Create journeys with various statuses
        mock_journeys = [
            {'journeyId': 'JRN-001', 'status': 'running', 'progress': 50},
            {'journeyId': 'JRN-002', 'status': 'running', 'progress': 75},
            {'journeyId': 'JRN-003', 'status': 'pending', 'progress': 0},
            {'journeyId': 'JRN-004', 'status': 'completed', 'progress': 100},
            {'journeyId': 'JRN-005', 'status': 'completed', 'progress': 100},
            {'journeyId': 'JRN-006', 'status': 'failed', 'progress': 25},
            {'journeyId': 'JRN-007', 'status': 'paused', 'progress': 60},
        ]
        
        mock_utils.list_journeys.return_value = mock_journeys
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=None,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify status distribution
        status_dist = result['summary']['status_distribution']
        assert status_dist['running'] == 2
        assert status_dist['pending'] == 1
        assert status_dist['completed'] == 2
        assert status_dist['failed'] == 1
        assert status_dist['paused'] == 1
        
        # Verify categorization
        assert result['summary']['active_journeys'] == 3  # running + pending
        assert result['summary']['completed_journeys'] == 2
        assert result['summary']['failed_journeys'] == 1
        
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_journey_info_job_status_distribution(self, mock_utils_class, mock_context, sample_journey_id):
        """Test journey info with job status distribution calculation."""
        # Mock TransformationUtils instance
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        
        mock_journey_status = {'journeyId': sample_journey_id, 'name': 'Test Journey'}
        mock_stages = [
            {'stageId': 'raw_analysis', 'name': 'Raw Analysis'},
            {'stageId': 'stripped_schema', 'name': 'Stripped Schema'}
        ]
        
        # Jobs with various statuses
        mock_jobs_stage1 = [
            {'jobId': 'JOB-001', 'status': 'completed'},
            {'jobId': 'JOB-002', 'status': 'completed'},
            {'jobId': 'JOB-003', 'status': 'failed'}
        ]
        
        mock_jobs_stage2 = [
            {'jobId': 'JOB-004', 'status': 'in_progress'},
            {'jobId': 'JOB-005', 'status': 'completed'}
        ]
        
        mock_utils.get_journey_status.return_value = mock_journey_status
        mock_utils.get_journey_stages.return_value = mock_stages
        mock_utils.get_stage_jobs.side_effect = [mock_jobs_stage1, mock_jobs_stage2]
        
        result = await journey_info_tool(
            ctx=mock_context,
            journey_id=sample_journey_id,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify job status distribution (only from recent_jobs, which are first 3 of each stage)
        job_status_dist = result['summary']['job_status_distribution']
        assert job_status_dist['completed'] == 3  # 2 from stage1 + 1 from stage2 (limited to 3 each)
        assert job_status_dist['failed'] == 1
        assert job_status_dist['in_progress'] == 1
        
        mock_context.error.assert_not_called() 