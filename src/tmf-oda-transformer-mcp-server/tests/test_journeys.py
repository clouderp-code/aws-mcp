"""
Tests for the journeys tool of TMF ODA transformer MCP server.
Tests comprehensive CRUD operations: Create, Read, Update, Delete.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, call
from awslabs.tmf_oda_transformer_mcp_server.server import journeys_tool


@pytest.mark.asyncio
class TestJourneys:
    """Test cases for the journeys tool with CRUD operations."""

    # ============================================================================
    # READ OPERATIONS (Backward Compatible)
    # ============================================================================

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_list_all_journeys_success(self, mock_utils_class, mock_context):
        """Test successful listing of all journeys (READ - default action)."""
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
        
        result = await journeys_tool(
            ctx=mock_context,
            action='read',  # Default action for backward compatibility
            journey_id=None,
            journey_data=None,
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
        assert result['data_source'] == 'DynamoDB'
        
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
        assert result['message'] == 'Retrieved 3 transformation journeys from DynamoDB'
        
        # Verify mocks were called correctly
        mock_utils_class.assert_called_once()
        mock_utils.list_journeys.assert_called_once()
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
            }
        ]
        
        # Mock job data
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
        
        mock_utils.get_journey_status.return_value = mock_journey_status
        mock_utils.get_journey_stages.return_value = mock_stages
        mock_utils.get_stage_jobs.return_value = mock_jobs_raw
        
        result = await journeys_tool(
            ctx=mock_context,
            action='read',
            journey_id=sample_journey_id,
            journey_data=None,
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
        assert result['data_source'] == 'DynamoDB'
        
        # Verify journey status
        assert result['journey_status'] == mock_journey_status
        
        # Verify stages information
        assert result['stages']['total_stages'] == 1
        assert len(result['stages']['stages_list']) == 1
        assert result['stages']['stages_list'][0]['stageId'] == 'raw_analysis'
        
        mock_context.error.assert_not_called()

    # ============================================================================
    # CREATE OPERATIONS
    # ============================================================================

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils', None)
    async def test_create_journey_fallback_success(self, mock_context):
        """Test successful journey creation using fallback JSON system."""
        journey_data = {
            'name': 'Test Product Catalog Journey',
            'description': 'A test journey for product catalog transformation',
            'oda_component_type': 'product-catalog-management',
            'source_type': 'database',
            'priority': 'high'
        }
        
        with patch('awslabs.tmf_oda_transformer_mcp_server.server.journey_manager') as mock_manager:
            mock_manager.create_journey.return_value = 'JRN-TEST-001'
            
            result = await journeys_tool(
                ctx=mock_context,
                action='create',
                journey_id=None,
                journey_data=journey_data,
                stage_id=None,
                include_stages=True,
                include_job_history=True,
                job_limit=10
            )
            
            # Verify the result structure
            assert isinstance(result, dict)
            assert result['operation'] == 'create_journey'
            assert result['action'] == 'create'
            assert result['status'] == 'success'
            assert result['data_source'] == 'Local JSON (fallback)'
            assert result['journey_id'] == 'JRN-TEST-001'
            
            # Verify journey data was passed correctly
            assert result['journey_data']['name'] == 'Test Product Catalog Journey'
            assert result['journey_data']['oda_component_type'] == 'product-catalog-management'
            
            # Verify manager was called correctly
            mock_manager.create_journey.assert_called_once()
            mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_create_journey_dynamodb_simulated(self, mock_utils_class, mock_context):
        """Test journey creation with DynamoDB (simulated for now)."""
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        
        journey_data = {
            'name': 'Customer Management Migration',
            'description': 'Migrate legacy customer data to TMF ODA',
            'oda_component_type': 'customer-management',
            'source_type': 'schema',
            'priority': 'medium'
        }
        
        result = await journeys_tool(
            ctx=mock_context,
            action='create',
            journey_id='JRN-CUSTOM-001',
            journey_data=journey_data,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert result['operation'] == 'create_journey'
        assert result['action'] == 'create'
        assert result['status'] == 'success'
        assert result['data_source'] == 'DynamoDB'
        assert result['journey_id'] == 'JRN-CUSTOM-001'
        assert '(DynamoDB - simulated)' in result['message']
        
        mock_context.error.assert_not_called()

    async def test_create_journey_missing_data(self, mock_context):
        """Test journey creation with missing journey_data."""
        result = await journeys_tool(
            ctx=mock_context,
            action='create',
            journey_id=None,
            journey_data=None,  # Missing required data
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert 'journey_data is required for CREATE action' in result['error_message']

    async def test_create_journey_invalid_data(self, mock_context):
        """Test journey creation with invalid journey_data."""
        invalid_data = {
            'name': '',  # Empty name should fail validation
            'oda_component_type': 'invalid-type'  # Invalid component type
        }
        
        result = await journeys_tool(
            ctx=mock_context,
            action='create',
            journey_id=None,
            journey_data=invalid_data,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert 'Invalid journey_data format' in result['error_message']

    # ============================================================================
    # UPDATE OPERATIONS
    # ============================================================================

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils', None)
    async def test_update_journey_fallback_success(self, mock_context):
        """Test successful journey update using fallback JSON system."""
        journey_id = 'JRN-TEST-001'
        update_data = {
            'status': 'completed',
            'overall_progress': 100,
            'current_stage': 'compliance_validation'
        }
        
        with patch('awslabs.tmf_oda_transformer_mcp_server.server.journey_manager') as mock_manager:
            # Mock existing journey
            mock_manager.get_journey_status.return_value = {
                'journey_id': journey_id,
                'name': 'Test Journey',
                'status': 'running',
                'overall_progress': 50
            }
            mock_manager.update_journey_status.return_value = True
            
            result = await journeys_tool(
                ctx=mock_context,
                action='update',
                journey_id=journey_id,
                journey_data=update_data,
                stage_id=None,
                include_stages=True,
                include_job_history=True,
                job_limit=10
            )
            
            # Verify the result structure
            assert isinstance(result, dict)
            assert result['operation'] == 'update_journey'
            assert result['action'] == 'update'
            assert result['status'] == 'success'
            assert result['data_source'] == 'Local JSON (fallback)'
            assert result['journey_id'] == journey_id
            
            # Verify update data
            assert result['update_data']['status'] == 'completed'
            assert result['update_data']['overall_progress'] == 100
            assert 'status' in result['updates_applied']
            
            # Verify manager was called correctly
            mock_manager.get_journey_status.assert_called_once_with(journey_id)
            mock_manager.update_journey_status.assert_called_once()
            mock_context.error.assert_not_called()

    async def test_update_journey_missing_id(self, mock_context):
        """Test journey update with missing journey_id."""
        result = await journeys_tool(
            ctx=mock_context,
            action='update',
            journey_id=None,  # Missing required ID
            journey_data={'status': 'completed'},
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert 'journey_id is required for UPDATE action' in result['error_message']

    async def test_update_journey_missing_data(self, mock_context):
        """Test journey update with missing journey_data."""
        result = await journeys_tool(
            ctx=mock_context,
            action='update',
            journey_id='JRN-TEST-001',
            journey_data=None,  # Missing required data
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert 'journey_data is required for UPDATE action' in result['error_message']

    # ============================================================================
    # DELETE OPERATIONS
    # ============================================================================

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils', None)
    async def test_delete_journey_fallback_success(self, mock_context):
        """Test successful journey deletion using fallback JSON system."""
        journey_id = 'JRN-TEST-001'
        
        with patch('awslabs.tmf_oda_transformer_mcp_server.server.journey_manager') as mock_manager:
            # Mock existing journey and jobs
            mock_journey = {
                'journey_id': journey_id,
                'name': 'Test Journey',
                'status': 'completed'
            }
            mock_jobs = {'raw_analysis': [], 'stripped_schema': []}
            
            mock_manager.get_journey_status.return_value = mock_journey
            mock_manager._load_journeys.return_value = {journey_id: mock_journey}
            mock_manager._load_jobs.return_value = {journey_id: mock_jobs}
            
            result = await journeys_tool(
                ctx=mock_context,
                action='delete',
                journey_id=journey_id,
                journey_data=None,
                stage_id=None,
                include_stages=True,
                include_job_history=True,
                job_limit=10
            )
            
            # Verify the result structure
            assert isinstance(result, dict)
            assert result['operation'] == 'delete_journey'
            assert result['action'] == 'delete'
            assert result['status'] == 'success'
            assert result['data_source'] == 'Local JSON (fallback)'
            assert result['journey_id'] == journey_id
            assert result['deleted_journey'] == mock_journey
            
            # Verify manager was called correctly
            mock_manager.get_journey_status.assert_called_once_with(journey_id)
            mock_manager._load_journeys.assert_called_once()
            mock_manager._load_jobs.assert_called_once()
            mock_manager._save_journeys.assert_called_once()
            mock_manager._save_jobs.assert_called_once()
            mock_context.error.assert_not_called()

    async def test_delete_journey_missing_id(self, mock_context):
        """Test journey deletion with missing journey_id."""
        result = await journeys_tool(
            ctx=mock_context,
            action='delete',
            journey_id=None,  # Missing required ID
            journey_data=None,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert 'journey_id is required for DELETE action' in result['error_message']

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils', None)
    async def test_delete_journey_not_found(self, mock_context):
        """Test journey deletion when journey doesn't exist."""
        journey_id = 'JRN-NONEXISTENT'
        
        with patch('awslabs.tmf_oda_transformer_mcp_server.server.journey_manager') as mock_manager:
            mock_manager.get_journey_status.return_value = None  # Journey not found
            
            result = await journeys_tool(
                ctx=mock_context,
                action='delete',
                journey_id=journey_id,
                journey_data=None,
                stage_id=None,
                include_stages=True,
                include_job_history=True,
                job_limit=10
            )
            
            # Should return error result
            assert isinstance(result, dict)
            assert result['status'] == 'error'
            assert f'Journey {journey_id} not found for deletion' in result['error_message']

    # ============================================================================
    # ERROR HANDLING & EDGE CASES
    # ============================================================================

    async def test_unsupported_action(self, mock_context):
        """Test handling of unsupported action."""
        result = await journeys_tool(
            ctx=mock_context,
            action='invalid_action',
            journey_id=None,
            journey_data=None,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Should return error result
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert 'Invalid action' in result['error_message']

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_journeys_exception_handling(self, mock_utils_class, mock_context):
        """Test exception handling in journeys tool."""
        # Mock TransformationUtils to raise an exception
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        mock_utils.list_journeys.side_effect = Exception("Database connection failed")
        
        result = await journeys_tool(
            ctx=mock_context,
            action='read',
            journey_id=None,
            journey_data=None,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Verify error result structure
        assert isinstance(result, dict)
        assert result['operation'] == 'journey_read'
        assert result['action'] == 'read'
        assert result['status'] == 'error'
        assert 'Database connection failed' in result['error_message']
        assert 'duration_seconds' in result
        
        mock_context.error.assert_called_once()

    # ============================================================================
    # BACKWARD COMPATIBILITY TESTS
    # ============================================================================

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_backward_compatibility_default_action(self, mock_utils_class, mock_context):
        """Test that default action maintains backward compatibility."""
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        mock_utils.list_journeys.return_value = []
        
        # Call without specifying action (should default to 'read')
        result = await journeys_tool(
            ctx=mock_context,
            # action parameter omitted - should default to 'read'
            journey_id=None,
            journey_data=None,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        # Should work exactly like the old journey-info tool
        assert isinstance(result, dict)
        assert result['operation'] == 'list_all_journeys'
        assert result['status'] == 'success'
        
        mock_utils.list_journeys.assert_called_once()
        mock_context.error.assert_not_called()

    @patch('awslabs.tmf_oda_transformer_mcp_server.server.TransformationUtils')
    async def test_backward_compatibility_list_action(self, mock_utils_class, mock_context):
        """Test that 'list' action works the same as 'read'."""
        mock_utils = Mock()
        mock_utils_class.return_value = mock_utils
        mock_utils.list_journeys.return_value = []
        
        result = await journeys_tool(
            ctx=mock_context,
            action='list',  # Alternative to 'read'
            journey_id=None,
            journey_data=None,
            stage_id=None,
            include_stages=True,
            include_job_history=True,
            job_limit=10
        )
        
        assert isinstance(result, dict)
        assert result['operation'] == 'list_all_journeys'
        assert result['status'] == 'success'
        
        mock_utils.list_journeys.assert_called_once()
        mock_context.error.assert_not_called() 