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

"""Tests for Google Drive authentication."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from awslabs.gdrive_mcp_server.impl.auth import GoogleDriveAuth
from awslabs.gdrive_mcp_server.models import AuthRequest


@pytest.fixture
def auth_instance():
    """Create a GoogleDriveAuth instance for testing."""
    return GoogleDriveAuth()


@pytest.mark.asyncio
async def test_service_account_auth_success(auth_instance):
    """Test successful service account authentication."""
    with patch('awslabs.gdrive_mcp_server.impl.auth.google_auth.ServiceAccountCredentials') as mock_creds, \
         patch('awslabs.gdrive_mcp_server.impl.auth.google_auth.build') as mock_build, \
         patch('os.path.exists', return_value=True):
        
        # Mock credentials
        mock_creds_instance = MagicMock()
        mock_creds_instance.service_account_email = 'test@example.com'
        mock_creds.from_service_account_file.return_value = mock_creds_instance
        
        # Mock service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Test authentication
        request = AuthRequest(
            auth_type='service_account',
            credentials_path='/path/to/creds.json'
        )
        
        result = await auth_instance.authenticate(request)
        
        assert result.success is True
        assert result.auth_type == 'service_account'
        assert result.user_email == 'test@example.com'
        assert auth_instance.is_authenticated() is True


@pytest.mark.asyncio
async def test_service_account_auth_file_not_found(auth_instance):
    """Test service account authentication with missing credentials file."""
    with patch('os.path.exists', return_value=False):
        request = AuthRequest(
            auth_type='service_account',
            credentials_path='/nonexistent/creds.json'
        )
        
        result = await auth_instance.authenticate(request)
        
        assert result.success is False
        assert 'not found' in result.message
        assert auth_instance.is_authenticated() is False


@pytest.mark.asyncio
async def test_oauth2_auth_success(auth_instance):
    """Test successful OAuth2 authentication."""
    with patch('awslabs.gdrive_mcp_server.impl.auth.google_auth.InstalledAppFlow') as mock_flow, \
         patch('awslabs.gdrive_mcp_server.impl.auth.google_auth.build') as mock_build, \
         patch('os.path.exists', return_value=False), \
         patch('builtins.open', create=True) as mock_open, \
         patch('pickle.dump') as mock_dump:
        
        # Mock OAuth2 flow
        mock_flow_instance = MagicMock()
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_flow_instance.run_local_server.return_value = mock_creds
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance
        
        # Mock service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Test authentication
        request = AuthRequest(
            auth_type='oauth2',
            credentials_path='/path/to/client_creds.json',
            token_path='/path/to/token.pickle'
        )
        
        result = await auth_instance.authenticate(request)
        
        assert result.success is True
        assert result.auth_type == 'oauth2'
        assert auth_instance.is_authenticated() is True


@pytest.mark.asyncio
async def test_unsupported_auth_type(auth_instance):
    """Test unsupported authentication type."""
    request = AuthRequest(
        auth_type='unsupported',  # type: ignore
        credentials_path='/path/to/creds.json'
    )
    
    result = await auth_instance.authenticate(request)
    
    assert result.success is False
    assert 'Unsupported authentication type' in result.message
    assert auth_instance.is_authenticated() is False


def test_get_service_not_authenticated():
    """Test getting service when not authenticated."""
    auth = GoogleDriveAuth()
    service = auth.get_service()
    assert service is None


def test_is_authenticated_false():
    """Test is_authenticated returns False when not authenticated."""
    auth = GoogleDriveAuth()
    assert auth.is_authenticated() is False 