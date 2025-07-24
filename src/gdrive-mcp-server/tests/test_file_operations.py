# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for Google Drive file operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from awslabs.gdrive_mcp_server.impl.tools.file_operations import (
    read_file_impl,
    write_file_impl,
    delete_file_impl,
)
from awslabs.gdrive_mcp_server.models import (
    ReadFileRequest,
    WriteFileRequest,
    DeleteFileRequest,
)


@pytest.mark.asyncio
async def test_read_file_success():
    """Test successful file reading."""
    with patch('awslabs.gdrive_mcp_server.impl.auth.get_authenticated_service') as mock_get_service, \
         patch('awslabs.gdrive_mcp_server.impl.tools.file_operations.download_file_content') as mock_download:
        
        # Mock authenticated service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Mock download content
        mock_download.return_value = (b'Hello, World!', 'text/plain')
        
        # Test file reading
        request = ReadFileRequest(
            file_id='test_file_id',
            encoding='utf-8',
            include_metadata=False
        )
        
        result = await read_file_impl(request)
        
        assert result.success is True
        assert result.content == 'Hello, World!'
        assert result.content_type == 'text/plain'
        assert result.encoding == 'utf-8'


@pytest.mark.asyncio
async def test_read_file_not_authenticated():
    """Test file reading when not authenticated."""
    with patch('awslabs.gdrive_mcp_server.impl.auth.get_authenticated_service') as mock_get_service:
        # Mock no authentication
        mock_get_service.return_value = None
        
        request = ReadFileRequest(file_id='test_file_id')
        result = await read_file_impl(request)
        
        assert result.success is False
        assert 'Not authenticated' in result.message


@pytest.mark.asyncio
async def test_write_file_success():
    """Test successful file writing."""
    with patch('awslabs.gdrive_mcp_server.impl.auth.get_authenticated_service') as mock_get_service, \
         patch('awslabs.gdrive_mcp_server.impl.tools.file_operations.upload_file_content') as mock_upload:
        
        # Mock authenticated service
        mock_service = MagicMock()
        mock_service.files().get().execute.return_value = {
            'id': 'new_file_id',
            'name': 'test.txt',
            'mimeType': 'text/plain',
            'webViewLink': 'https://drive.google.com/file/d/new_file_id/view'
        }
        mock_get_service.return_value = mock_service
        
        # Mock upload
        mock_upload.return_value = {
            'id': 'new_file_id',
            'name': 'test.txt',
            'webViewLink': 'https://drive.google.com/file/d/new_file_id/view'
        }
        
        # Test file writing
        request = WriteFileRequest(
            name='test.txt',
            content='Hello, World!',
            mime_type='text/plain'
        )
        
        result = await write_file_impl(request)
        
        assert result.success is True
        assert result.file_id == 'new_file_id'
        assert result.file_url == 'https://drive.google.com/file/d/new_file_id/view'


@pytest.mark.asyncio
async def test_write_file_not_authenticated():
    """Test file writing when not authenticated."""
    with patch('awslabs.gdrive_mcp_server.impl.auth.get_authenticated_service') as mock_get_service:
        # Mock no authentication
        mock_get_service.return_value = None
        
        request = WriteFileRequest(name='test.txt', content='Hello, World!')
        result = await write_file_impl(request)
        
        assert result.success is False
        assert 'Not authenticated' in result.message


@pytest.mark.asyncio
async def test_delete_file_success():
    """Test successful file deletion."""
    with patch('awslabs.gdrive_mcp_server.impl.auth.get_authenticated_service') as mock_get_service:
        # Mock authenticated service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Test file deletion (trash)
        request = DeleteFileRequest(file_id='test_file_id', permanent=False)
        result = await delete_file_impl(request)
        
        assert result.success is True
        assert 'trash' in result.message.lower()
        assert result.file_id == 'test_file_id'
        
        # Verify the correct API call was made
        mock_service.files().update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_file_permanent():
    """Test permanent file deletion."""
    with patch('awslabs.gdrive_mcp_server.impl.auth.get_authenticated_service') as mock_get_service:
        # Mock authenticated service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Test permanent file deletion
        request = DeleteFileRequest(file_id='test_file_id', permanent=True)
        result = await delete_file_impl(request)
        
        assert result.success is True
        assert 'permanently' in result.message.lower()
        assert result.file_id == 'test_file_id'
        
        # Verify the correct API call was made
        mock_service.files().delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_file_not_authenticated():
    """Test file deletion when not authenticated."""
    with patch('awslabs.gdrive_mcp_server.impl.auth.get_authenticated_service') as mock_get_service:
        # Mock no authentication
        mock_get_service.return_value = None
        
        request = DeleteFileRequest(file_id='test_file_id')
        result = await delete_file_impl(request)
        
        assert result.success is False
        assert 'Not authenticated' in result.message 