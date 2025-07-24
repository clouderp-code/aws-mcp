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

"""Google Drive authentication implementation."""

import os
import pickle
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from loguru import logger

from awslabs.gdrive_mcp_server.models import AuthRequest, AuthResult


class GoogleDriveAuth:
    """Google Drive authentication manager."""
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.service = None
        self.credentials = None
        self.scopes = ['https://www.googleapis.com/auth/drive']
    
    async def authenticate(self, auth_request: AuthRequest) -> AuthResult:
        """Authenticate with Google Drive API.
        
        Args:
            auth_request: Authentication request with credentials and type.
            
        Returns:
            AuthResult with success status and user information.
        """
        try:
            self.scopes = auth_request.scopes or self.scopes
            
            if auth_request.auth_type == 'service_account':
                return await self._authenticate_service_account(auth_request)
            elif auth_request.auth_type == 'oauth2':
                return await self._authenticate_oauth2(auth_request)
            else:
                return AuthResult(
                    success=False,
                    message=f'Unsupported authentication type: {auth_request.auth_type}'
                )
        except Exception as e:
            logger.error(f'Authentication failed: {e}')
            return AuthResult(
                success=False,
                message=f'Authentication failed: {str(e)}'
            )
    
    async def _authenticate_service_account(self, auth_request: AuthRequest) -> AuthResult:
        """Authenticate using service account credentials.
        
        Args:
            auth_request: Authentication request.
            
        Returns:
            AuthResult with authentication status.
        """
        try:
            credentials_path = (
                auth_request.credentials_path or 
                os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            )
            
            if not credentials_path:
                return AuthResult(
                    success=False,
                    message='Service account credentials path not provided'
                )
            
            if not os.path.exists(credentials_path):
                return AuthResult(
                    success=False,
                    message=f'Credentials file not found: {credentials_path}'
                )
            
            self.credentials = ServiceAccountCredentials.from_service_account_file(
                credentials_path, scopes=self.scopes
            )
            
            # Build the service
            self.service = build('drive', 'v3', credentials=self.credentials)
            
            # Get service account email
            service_account_email = self.credentials.service_account_email
            
            logger.info(f'Successfully authenticated with service account: {service_account_email}')
            
            return AuthResult(
                success=True,
                message='Successfully authenticated with service account',
                user_email=service_account_email,
                auth_type='service_account'
            )
            
        except Exception as e:
            logger.error(f'Service account authentication failed: {e}')
            return AuthResult(
                success=False,
                message=f'Service account authentication failed: {str(e)}'
            )
    
    async def _authenticate_oauth2(self, auth_request: AuthRequest) -> AuthResult:
        """Authenticate using OAuth2 flow.
        
        Args:
            auth_request: Authentication request.
            
        Returns:
            AuthResult with authentication status.
        """
        try:
            credentials_path = (
                auth_request.credentials_path or 
                os.environ.get('GDRIVE_CLIENT_CREDENTIALS')
            )
            
            token_path = (
                auth_request.token_path or 
                os.environ.get('GDRIVE_TOKEN_FILE', 'token.pickle')
            )
            
            if not credentials_path:
                return AuthResult(
                    success=False,
                    message='OAuth2 client credentials path not provided'
                )
            
            creds = None
            
            # Load existing token if available
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            # If there are no valid credentials, request authorization
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, self.scopes
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for future use
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.credentials = creds
            self.service = build('drive', 'v3', credentials=creds)
            
            # Get user email from token info
            user_email = getattr(creds, 'id_token', {}).get('email', 'Unknown')
            
            logger.info(f'Successfully authenticated with OAuth2: {user_email}')
            
            return AuthResult(
                success=True,
                message='Successfully authenticated with OAuth2',
                user_email=user_email,
                auth_type='oauth2'
            )
            
        except Exception as e:
            logger.error(f'OAuth2 authentication failed: {e}')
            return AuthResult(
                success=False,
                message=f'OAuth2 authentication failed: {str(e)}'
            )
    
    def get_service(self):
        """Get the authenticated Google Drive service.
        
        Returns:
            Google Drive service instance or None if not authenticated.
        """
        return self.service
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated.
        
        Returns:
            True if authenticated, False otherwise.
        """
        return self.service is not None and self.credentials is not None


# Global authentication instance
_auth_instance = GoogleDriveAuth()


async def authenticate_service_account(
    credentials_path: Optional[str] = None,
    scopes: Optional[list] = None
) -> AuthResult:
    """Authenticate using service account.
    
    Args:
        credentials_path: Path to service account credentials file.
        scopes: List of OAuth2 scopes.
        
    Returns:
        AuthResult with authentication status.
    """
    auth_request = AuthRequest(
        auth_type='service_account',
        credentials_path=credentials_path,
        scopes=scopes or ['https://www.googleapis.com/auth/drive']
    )
    return await _auth_instance.authenticate(auth_request)


async def authenticate_oauth2(
    credentials_path: Optional[str] = None,
    token_path: Optional[str] = None,
    scopes: Optional[list] = None
) -> AuthResult:
    """Authenticate using OAuth2 flow.
    
    Args:
        credentials_path: Path to OAuth2 client credentials file.
        token_path: Path to token file.
        scopes: List of OAuth2 scopes.
        
    Returns:
        AuthResult with authentication status.
    """
    auth_request = AuthRequest(
        auth_type='oauth2',
        credentials_path=credentials_path,
        token_path=token_path,
        scopes=scopes or ['https://www.googleapis.com/auth/drive']
    )
    return await _auth_instance.authenticate(auth_request)


def get_authenticated_service():
    """Get the authenticated Google Drive service.
    
    Returns:
        Google Drive service instance or None if not authenticated.
    """
    return _auth_instance.get_service()


def is_authenticated() -> bool:
    """Check if currently authenticated.
    
    Returns:
        True if authenticated, False otherwise.
    """
    return _auth_instance.is_authenticated() 