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

"""Utility functions for Google Drive operations."""

import io
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Union

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from loguru import logger

from awslabs.gdrive_mcp_server.impl.auth import get_authenticated_service
from awslabs.gdrive_mcp_server.models import FileInfo, FileMetadata, FilePermission


def get_mime_type(filename: str, content: Union[str, bytes] = None) -> str:
    """Determine MIME type from filename and content.
    
    Args:
        filename: Name of the file.
        content: File content for additional type detection.
        
    Returns:
        MIME type string.
    """
    mime_type, _ = mimetypes.guess_type(filename)
    
    if mime_type:
        return mime_type
    
    # Default based on content type
    if isinstance(content, str):
        return 'text/plain'
    elif isinstance(content, bytes):
        return 'application/octet-stream'
    
    return 'application/octet-stream'


def build_query(
    search_query: Optional[str] = None,
    file_types: Optional[List[str]] = None,
    folder_id: Optional[str] = None,
    include_trashed: bool = False
) -> str:
    """Build Google Drive API query string.
    
    Args:
        search_query: Text search query.
        file_types: List of MIME types to filter by.
        folder_id: Folder ID to search within.
        include_trashed: Whether to include trashed files.
        
    Returns:
        Query string for Google Drive API.
    """
    query_parts = []
    
    if search_query:
        # Escape quotes in search query
        escaped_query = search_query.replace("'", "\\'")
        query_parts.append(f"name contains '{escaped_query}' or fullText contains '{escaped_query}'")
    
    if file_types:
        mime_conditions = [f"mimeType='{mime_type}'" for mime_type in file_types]
        query_parts.append(f"({' or '.join(mime_conditions)})")
    
    if folder_id:
        query_parts.append(f"'{folder_id}' in parents")
    
    if not include_trashed:
        query_parts.append("trashed=false")
    
    return ' and '.join(query_parts) if query_parts else None


def convert_api_file_to_file_info(api_file: Dict) -> FileInfo:
    """Convert Google Drive API file to FileInfo model.
    
    Args:
        api_file: File data from Google Drive API.
        
    Returns:
        FileInfo model instance.
    """
    return FileInfo(
        id=api_file.get('id', ''),
        name=api_file.get('name', ''),
        mime_type=api_file.get('mimeType', ''),
        size=int(api_file.get('size', 0)) if api_file.get('size') else None,
        created_time=_parse_datetime(api_file.get('createdTime')),
        modified_time=_parse_datetime(api_file.get('modifiedTime')),
        web_view_link=api_file.get('webViewLink'),
        download_link=api_file.get('webContentLink')
    )


def convert_api_file_to_metadata(api_file: Dict) -> FileMetadata:
    """Convert Google Drive API file to FileMetadata model.
    
    Args:
        api_file: File data from Google Drive API.
        
    Returns:
        FileMetadata model instance.
    """
    file_info = convert_api_file_to_file_info(api_file)
    
    permissions = []
    if 'permissions' in api_file:
        for perm in api_file['permissions']:
            permissions.append(FilePermission(
                role=perm.get('role', ''),
                type=perm.get('type', ''),
                email=perm.get('emailAddress'),
                display_name=perm.get('displayName')
            ))
    
    return FileMetadata(
        file_info=file_info,
        description=api_file.get('description'),
        parents=api_file.get('parents', []),
        permissions=permissions,
        properties=api_file.get('properties', {}),
        app_properties=api_file.get('appProperties', {}),
        starred=api_file.get('starred', False),
        trashed=api_file.get('trashed', False),
        version=int(api_file.get('version', 0)) if api_file.get('version') else None,
        original_filename=api_file.get('originalFilename')
    )


def _parse_datetime(datetime_str: Optional[str]) -> Optional[datetime]:
    """Parse RFC3339 datetime string.
    
    Args:
        datetime_str: RFC3339 formatted datetime string.
        
    Returns:
        Parsed datetime object or None.
    """
    if not datetime_str:
        return None
    
    try:
        # Remove timezone suffix for parsing
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str[:-1] + '+00:00'
        
        return datetime.fromisoformat(datetime_str)
    except (ValueError, TypeError):
        logger.warning(f'Failed to parse datetime: {datetime_str}')
        return None


async def download_file_content(
    file_id: str,
    export_format: Optional[str] = None
) -> tuple[bytes, str]:
    """Download file content from Google Drive.
    
    Args:
        file_id: Google Drive file ID.
        export_format: Export format for Google Workspace files.
        
    Returns:
        Tuple of (content_bytes, mime_type).
    """
    service = get_authenticated_service()
    if not service:
        raise Exception('Not authenticated with Google Drive')
    
    try:
        # Get file metadata to determine if it's a Google Workspace file
        file_metadata = service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get('mimeType', '')
        
        # Handle Google Workspace files
        if mime_type.startswith('application/vnd.google-apps.'):
            if not export_format:
                # Default export formats for Google Workspace files
                export_formats = {
                    'application/vnd.google-apps.document': 'text/plain',
                    'application/vnd.google-apps.spreadsheet': 'text/csv',
                    'application/vnd.google-apps.presentation': 'text/plain',
                    'application/vnd.google-apps.drawing': 'image/png',
                }
                export_format = export_formats.get(mime_type, 'application/pdf')
            
            request = service.files().export_media(fileId=file_id, mimeType=export_format)
            content_type = export_format
        else:
            # Handle regular files
            request = service.files().get_media(fileId=file_id)
            content_type = mime_type
        
        # Download the content
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        content = fh.getvalue()
        return content, content_type
        
    except HttpError as e:
        logger.error(f'Failed to download file {file_id}: {e}')
        raise Exception(f'Failed to download file: {e}')


async def upload_file_content(
    content: Union[str, bytes],
    filename: str,
    mime_type: Optional[str] = None,
    file_id: Optional[str] = None,
    parent_folder_id: Optional[str] = None,
    description: Optional[str] = None,
    properties: Optional[Dict[str, str]] = None
) -> Dict:
    """Upload file content to Google Drive.
    
    Args:
        content: File content to upload.
        filename: Name of the file.
        mime_type: MIME type of the file.
        file_id: ID for updating existing file.
        parent_folder_id: Parent folder ID.
        description: File description.
        properties: Custom properties.
        
    Returns:
        File metadata from Google Drive API.
    """
    service = get_authenticated_service()
    if not service:
        raise Exception('Not authenticated with Google Drive')
    
    try:
        # Convert content to bytes if needed
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        else:
            content_bytes = content
        
        # Determine MIME type
        if not mime_type:
            mime_type = get_mime_type(filename, content)
        
        # Create media upload
        media = MediaIoBaseUpload(
            io.BytesIO(content_bytes),
            mimetype=mime_type,
            resumable=True
        )
        
        # Prepare file metadata
        file_metadata = {'name': filename}
        
        if description:
            file_metadata['description'] = description
        
        if properties:
            file_metadata['properties'] = properties
        
        if parent_folder_id and not file_id:
            file_metadata['parents'] = [parent_folder_id]
        
        # Upload or update file
        if file_id:
            # Update existing file
            result = service.files().update(
                fileId=file_id,
                body=file_metadata,
                media_body=media,
                fields='id,name,mimeType,size,webViewLink,webContentLink,createdTime,modifiedTime'
            ).execute()
        else:
            # Create new file
            result = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,mimeType,size,webViewLink,webContentLink,createdTime,modifiedTime'
            ).execute()
        
        return result
        
    except HttpError as e:
        logger.error(f'Failed to upload file {filename}: {e}')
        raise Exception(f'Failed to upload file: {e}')


def handle_drive_api_error(error: HttpError) -> str:
    """Handle Google Drive API errors and return user-friendly messages.
    
    Args:
        error: HttpError from Google Drive API.
        
    Returns:
        User-friendly error message.
    """
    error_details = error.error_details if hasattr(error, 'error_details') else []
    
    if error.resp.status == 404:
        return 'File or folder not found'
    elif error.resp.status == 403:
        return 'Permission denied or quota exceeded'
    elif error.resp.status == 400:
        return 'Invalid request parameters'
    elif error.resp.status == 401:
        return 'Authentication required'
    elif error.resp.status == 429:
        return 'API rate limit exceeded'
    else:
        return f'Google Drive API error: {error}' 