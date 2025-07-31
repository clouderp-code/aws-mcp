"""
Comprehensive tests for S3Service.

Tests S3 operations including reading transcripts, uploading analysis results,
listing files, and error handling with mocked AWS S3 operations.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Any

from awslabs.call_analysis_mcp_server.services.s3_service import S3Service


@pytest.fixture
def s3_service():
    """Create an S3Service instance for testing."""
    with patch('boto3.client'):
        return S3Service(region='us-east-1')


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    return Mock()


@pytest.fixture
def sample_transcript_content():
    """Sample transcript content for testing."""
    return json.dumps({
        "call_id": "TEST_CALL_001",
        "transcript": [
            {
                "speaker": "agent",
                "text": "Thank you for calling. How can I help you today?",
                "timestamp": "00:00",
                "duration": 4.5
            },
            {
                "speaker": "customer",
                "text": "I'm having issues with my billing.",
                "timestamp": "00:05",
                "duration": 3.2
            }
        ]
    })


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for testing."""
    return {
        "call_id": "TEST_CALL_001",
        "analysis_timestamp": datetime.now().isoformat(),
        "sentiment_analysis": {
            "overall_sentiment": "neutral",
            "customer_sentiment": "neutral",
            "agent_sentiment": "positive"
        },
        "performance_kpis": {
            "customer_satisfaction_score": 7.5,
            "agent_professionalism_score": 8.5
        }
    }


class TestS3ServiceInitialization:
    """Test S3Service initialization and configuration."""
    
    @patch('boto3.client')
    def test_initialization_with_default_region(self, mock_boto_client):
        """Test S3Service initialization with default region."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        assert service.region == 'us-east-1'  # Default region
        assert service.s3_client == mock_client
        mock_boto_client.assert_called_once_with('s3', region_name='us-east-1')
    
    @patch('boto3.client')
    def test_initialization_with_custom_region(self, mock_boto_client):
        """Test S3Service initialization with custom region."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        service = S3Service(region='us-west-2')
        
        assert service.region == 'us-west-2'
        assert service.s3_client == mock_client
        mock_boto_client.assert_called_once_with('s3', region_name='us-west-2')
    
    @patch('boto3.client')
    def test_initialization_with_credentials_error(self, mock_boto_client):
        """Test handling of credentials error during initialization."""
        mock_boto_client.side_effect = NoCredentialsError()
        
        with pytest.raises(NoCredentialsError):
            S3Service()


class TestReadTranscript:
    """Test transcript reading functionality."""
    
    @patch('boto3.client')
    def test_read_transcript_success(self, mock_boto_client, sample_transcript_content):
        """Test successful transcript reading."""
        mock_client = Mock()
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = sample_transcript_content.encode('utf-8')
        mock_client.get_object.return_value = mock_response
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        result = service.read_transcript('test-bucket', 'transcripts/call.json')
        
        assert result == sample_transcript_content
        mock_client.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='transcripts/call.json'
        )
    
    @patch('boto3.client')
    def test_read_transcript_file_not_found(self, mock_boto_client):
        """Test handling of file not found error."""
        mock_client = Mock()
        mock_client.get_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchKey'}},
            operation_name='GetObject'
        )
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        with pytest.raises(ClientError):
            service.read_transcript('test-bucket', 'non-existent.json')
    
    @patch('boto3.client')
    def test_read_transcript_access_denied(self, mock_boto_client):
        """Test handling of access denied error."""
        mock_client = Mock()
        mock_client.get_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied'}},
            operation_name='GetObject'
        )
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        with pytest.raises(ClientError):
            service.read_transcript('test-bucket', 'restricted.json')
    
    @patch('boto3.client')
    def test_read_transcript_with_encoding(self, mock_boto_client):
        """Test reading transcript with different encodings."""
        mock_client = Mock()
        
        # Test UTF-8 with BOM
        utf8_bom_content = b'\xef\xbb\xbf{"test": "content"}'
        mock_response = {'Body': Mock()}
        mock_response['Body'].read.return_value = utf8_bom_content
        mock_client.get_object.return_value = mock_response
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        result = service.read_transcript('test-bucket', 'utf8_bom.json')
        
        # Should handle BOM correctly
        assert result == '{"test": "content"}'


class TestListTranscripts:
    """Test transcript listing functionality."""
    
    @patch('boto3.client')
    def test_list_transcripts_success(self, mock_boto_client):
        """Test successful transcript listing."""
        mock_client = Mock()
        mock_response = {
            'Contents': [
                {
                    'Key': 'transcripts/call1.json',
                    'Size': 1024,
                    'LastModified': datetime(2024, 1, 1, 12, 0, 0)
                },
                {
                    'Key': 'transcripts/call2.json',
                    'Size': 2048,
                    'LastModified': datetime(2024, 1, 2, 12, 0, 0)
                }
            ]
        }
        mock_client.list_objects_v2.return_value = mock_response
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        result = service.list_transcripts('test-bucket', 'transcripts/', max_files=10)
        
        assert len(result) == 2
        assert result[0]['key'] == 'transcripts/call1.json'
        assert result[0]['size'] == 1024
        assert result[1]['key'] == 'transcripts/call2.json'
        assert result[1]['size'] == 2048
        
        mock_client.list_objects_v2.assert_called_once_with(
            Bucket='test-bucket',
            Prefix='transcripts/',
            MaxKeys=10
        )
    
    @patch('boto3.client')
    def test_list_transcripts_empty_bucket(self, mock_boto_client):
        """Test listing transcripts from empty bucket."""
        mock_client = Mock()
        mock_response = {}  # No 'Contents' key means empty
        mock_client.list_objects_v2.return_value = mock_response
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        result = service.list_transcripts('empty-bucket')
        
        assert result == []
    
    @patch('boto3.client')
    def test_list_transcripts_with_prefix_filter(self, mock_boto_client):
        """Test listing transcripts with prefix filtering."""
        mock_client = Mock()
        mock_response = {
            'Contents': [
                {
                    'Key': 'calls/2024/january/call1.json',
                    'Size': 1024,
                    'LastModified': datetime(2024, 1, 1, 12, 0, 0)
                }
            ]
        }
        mock_client.list_objects_v2.return_value = mock_response
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        result = service.list_transcripts('test-bucket', 'calls/2024/january/')
        
        assert len(result) == 1
        assert result[0]['key'] == 'calls/2024/january/call1.json'
        
        mock_client.list_objects_v2.assert_called_once_with(
            Bucket='test-bucket',
            Prefix='calls/2024/january/',
            MaxKeys=1000  # Default max_files
        )
    
    @patch('boto3.client')
    def test_list_transcripts_pagination(self, mock_boto_client):
        """Test handling of paginated results."""
        mock_client = Mock()
        
        # First page
        first_response = {
            'Contents': [
                {
                    'Key': 'call1.json',
                    'Size': 1024,
                    'LastModified': datetime(2024, 1, 1, 12, 0, 0)
                }
            ],
            'IsTruncated': True,
            'NextContinuationToken': 'token123'
        }
        
        # Second page
        second_response = {
            'Contents': [
                {
                    'Key': 'call2.json',
                    'Size': 2048,
                    'LastModified': datetime(2024, 1, 2, 12, 0, 0)
                }
            ],
            'IsTruncated': False
        }
        
        mock_client.list_objects_v2.side_effect = [first_response, second_response]
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        result = service.list_transcripts('test-bucket', max_files=10)
        
        assert len(result) == 2
        assert result[0]['key'] == 'call1.json'
        assert result[1]['key'] == 'call2.json'
        
        # Should make two calls for pagination
        assert mock_client.list_objects_v2.call_count == 2


class TestUploadAnalysisResults:
    """Test analysis results upload functionality."""
    
    @patch('boto3.client')
    def test_upload_analysis_results_success(self, mock_boto_client, sample_analysis_result):
        """Test successful analysis results upload."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        result = service.upload_analysis_results(
            content=json.dumps(sample_analysis_result),
            bucket='results-bucket',
            key='analysis/result.json',
            content_type='application/json'
        )
        
        assert result['s3_url'] == 's3://results-bucket/analysis/result.json'
        assert result['bucket'] == 'results-bucket'
        assert result['key'] == 'analysis/result.json'
        
        mock_client.put_object.assert_called_once_with(
            Bucket='results-bucket',
            Key='analysis/result.json',
            Body=json.dumps(sample_analysis_result),
            ContentType='application/json',
            Metadata={'uploaded_by': 'call-analysis-mcp-server'}
        )
    
    @patch('boto3.client')
    def test_upload_analysis_results_with_metadata(self, mock_boto_client):
        """Test upload with custom metadata."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        custom_metadata = {'analysis_version': '1.0', 'processor': 'ai_enhanced'}
        
        result = service.upload_analysis_results(
            content='{"test": "data"}',
            bucket='results-bucket',
            key='test.json',
            metadata=custom_metadata
        )
        
        expected_metadata = {
            'uploaded_by': 'call-analysis-mcp-server',
            'analysis_version': '1.0',
            'processor': 'ai_enhanced'
        }
        
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args[1]['Metadata'] == expected_metadata
    
    @patch('boto3.client')
    def test_upload_analysis_results_error(self, mock_boto_client):
        """Test handling of upload errors."""
        mock_client = Mock()
        mock_client.put_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied'}},
            operation_name='PutObject'
        )
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        with pytest.raises(ClientError):
            service.upload_analysis_results(
                content='{"test": "data"}',
                bucket='restricted-bucket',
                key='test.json'
            )
    
    @patch('boto3.client')
    def test_upload_large_content(self, mock_boto_client):
        """Test upload of large content."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Create large content (1MB+)
        large_content = json.dumps({"data": "x" * 1000000})
        
        service = S3Service()
        result = service.upload_analysis_results(
            content=large_content,
            bucket='results-bucket',
            key='large_analysis.json'
        )
        
        assert result['s3_url'] == 's3://results-bucket/large_analysis.json'
        mock_client.put_object.assert_called_once()


class TestUploadFile:
    """Test file upload functionality."""
    
    @patch('boto3.client')
    @patch('builtins.open', new_callable=MagicMock)
    def test_upload_file_success(self, mock_open, mock_boto_client):
        """Test successful file upload."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock file content
        mock_file = Mock()
        mock_file.read.return_value = b'file content'
        mock_open.return_value.__enter__.return_value = mock_file
        
        service = S3Service()
        result = service.upload_file(
            file_path='/path/to/file.txt',
            bucket='uploads-bucket',
            key='files/file.txt'
        )
        
        assert result['s3_url'] == 's3://uploads-bucket/files/file.txt'
        mock_client.put_object.assert_called_once_with(
            Bucket='uploads-bucket',
            Key='files/file.txt',
            Body=b'file content',
            Metadata={'uploaded_by': 'call-analysis-mcp-server'}
        )
    
    @patch('boto3.client')
    def test_upload_file_not_found(self, mock_boto_client):
        """Test handling of file not found error."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        with pytest.raises(FileNotFoundError):
            service.upload_file(
                file_path='/non/existent/file.txt',
                bucket='uploads-bucket',
                key='file.txt'
            )


class TestGeneratePresignedUrl:
    """Test presigned URL generation."""
    
    @patch('boto3.client')
    def test_generate_presigned_url_success(self, mock_boto_client):
        """Test successful presigned URL generation."""
        mock_client = Mock()
        mock_client.generate_presigned_url.return_value = 'https://test-bucket.s3.amazonaws.com/file.json?AWSAccessKeyId=...'
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        url = service.generate_presigned_url(
            bucket='test-bucket',
            key='file.json',
            expiration=3600
        )
        
        assert url.startswith('https://test-bucket.s3.amazonaws.com/')
        mock_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': 'test-bucket', 'Key': 'file.json'},
            ExpiresIn=3600
        )
    
    @patch('boto3.client')
    def test_generate_presigned_url_error(self, mock_boto_client):
        """Test handling of presigned URL generation error."""
        mock_client = Mock()
        mock_client.generate_presigned_url.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied'}},
            operation_name='GeneratePresignedUrl'
        )
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        with pytest.raises(ClientError):
            service.generate_presigned_url('restricted-bucket', 'file.json')


class TestDeleteObject:
    """Test object deletion functionality."""
    
    @patch('boto3.client')
    def test_delete_object_success(self, mock_boto_client):
        """Test successful object deletion."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        result = service.delete_object('test-bucket', 'file-to-delete.json')
        
        assert result is True
        mock_client.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='file-to-delete.json'
        )
    
    @patch('boto3.client')
    def test_delete_object_not_found(self, mock_boto_client):
        """Test deletion of non-existent object."""
        mock_client = Mock()
        mock_client.delete_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchKey'}},
            operation_name='DeleteObject'
        )
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        # Should handle gracefully (S3 delete is idempotent)
        result = service.delete_object('test-bucket', 'non-existent.json')
        assert result is False
    
    @patch('boto3.client')
    def test_delete_object_access_denied(self, mock_boto_client):
        """Test handling of access denied during deletion."""
        mock_client = Mock()
        mock_client.delete_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied'}},
            operation_name='DeleteObject'
        )
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        with pytest.raises(ClientError):
            service.delete_object('restricted-bucket', 'file.json')


class TestObjectExists:
    """Test object existence checking."""
    
    @patch('boto3.client')
    def test_object_exists_true(self, mock_boto_client):
        """Test checking existence of existing object."""
        mock_client = Mock()
        mock_client.head_object.return_value = {'ContentLength': 1024}
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        exists = service.object_exists('test-bucket', 'existing-file.json')
        
        assert exists is True
        mock_client.head_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='existing-file.json'
        )
    
    @patch('boto3.client')
    def test_object_exists_false(self, mock_boto_client):
        """Test checking existence of non-existent object."""
        mock_client = Mock()
        mock_client.head_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchKey'}},
            operation_name='HeadObject'
        )
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        exists = service.object_exists('test-bucket', 'non-existent.json')
        
        assert exists is False


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @patch('boto3.client')
    def test_network_error_handling(self, mock_boto_client):
        """Test handling of network errors."""
        mock_client = Mock()
        mock_client.get_object.side_effect = Exception("Network error")
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        with pytest.raises(Exception):
            service.read_transcript('test-bucket', 'file.json')
    
    @patch('boto3.client')
    def test_invalid_bucket_name(self, mock_boto_client):
        """Test handling of invalid bucket names."""
        mock_client = Mock()
        mock_client.get_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'InvalidBucketName'}},
            operation_name='GetObject'
        )
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        with pytest.raises(ClientError):
            service.read_transcript('invalid-bucket-name!', 'file.json')
    
    @patch('boto3.client')
    def test_malformed_content_handling(self, mock_boto_client):
        """Test handling of malformed content."""
        mock_client = Mock()
        # Return binary content that's not valid text
        mock_response = {'Body': Mock()}
        mock_response['Body'].read.return_value = b'\xff\xfe\x00\x00'  # Invalid UTF-8
        mock_client.get_object.return_value = mock_response
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        # Should handle encoding errors gracefully
        with pytest.raises(UnicodeDecodeError):
            service.read_transcript('test-bucket', 'malformed.json')


class TestS3ServiceUtilities:
    """Test utility methods of S3Service."""
    
    @patch('boto3.client')
    def test_get_object_metadata(self, mock_boto_client):
        """Test getting object metadata."""
        mock_client = Mock()
        mock_client.head_object.return_value = {
            'ContentLength': 1024,
            'LastModified': datetime(2024, 1, 1, 12, 0, 0),
            'ContentType': 'application/json',
            'Metadata': {
                'analysis_version': '1.0',
                'uploaded_by': 'test'
            }
        }
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        metadata = service.get_object_metadata('test-bucket', 'file.json')
        
        assert metadata['ContentLength'] == 1024
        assert metadata['ContentType'] == 'application/json'
        assert metadata['Metadata']['analysis_version'] == '1.0'
    
    def test_parse_s3_url(self, s3_service):
        """Test parsing S3 URLs."""
        # Test valid S3 URL
        bucket, key = s3_service.parse_s3_url('s3://my-bucket/path/to/file.json')
        assert bucket == 'my-bucket'
        assert key == 'path/to/file.json'
        
        # Test S3 URL with subdirectories
        bucket, key = s3_service.parse_s3_url('s3://data-bucket/year/month/file.txt')
        assert bucket == 'data-bucket'
        assert key == 'year/month/file.txt'
        
        # Test invalid URL
        with pytest.raises(ValueError):
            s3_service.parse_s3_url('https://example.com/file.json')
    
    def test_build_s3_url(self, s3_service):
        """Test building S3 URLs."""
        url = s3_service.build_s3_url('my-bucket', 'path/to/file.json')
        assert url == 's3://my-bucket/path/to/file.json'
        
        # Test with empty key
        url = s3_service.build_s3_url('my-bucket', '')
        assert url == 's3://my-bucket/'
        
        # Test with key starting with slash
        url = s3_service.build_s3_url('my-bucket', '/path/file.json')
        assert url == 's3://my-bucket/path/file.json'  # Should remove leading slash


class TestConcurrency:
    """Test concurrent operations."""
    
    @pytest.mark.asyncio
    @patch('boto3.client')
    async def test_concurrent_uploads(self, mock_boto_client):
        """Test concurrent upload operations."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        service = S3Service()
        
        # Simulate multiple concurrent uploads
        import asyncio
        
        async def upload_task(index):
            return service.upload_analysis_results(
                content=f'{{"task": {index}}}',
                bucket='test-bucket',
                key=f'task_{index}.json'
            )
        
        tasks = [upload_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All uploads should complete
        assert len(results) == 5
        for i, result in enumerate(results):
            if isinstance(result, dict):
                assert result['key'] == f'task_{i}.json'
        
        # Should have made 5 put_object calls
        assert mock_client.put_object.call_count == 5