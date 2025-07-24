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

"""Metadata operations implementation for Google Drive MCP server."""

from googleapiclient.errors import HttpError
from loguru import logger

from awslabs.gdrive_mcp_server.impl.auth import get_authenticated_service
from awslabs.gdrive_mcp_server.impl.tools.utils import (
    convert_api_file_to_metadata,
    handle_drive_api_error,
)
from awslabs.gdrive_mcp_server.models import (
    GetFileMetadataRequest,
    GetFileMetadataResult,
    UpdateFileMetadataRequest,
    UpdateFileMetadataResult,
)


async def get_file_metadata_impl(request: GetFileMetadataRequest) -> GetFileMetadataResult:
    """Get file metadata from Google Drive.
    
    Args:
        request: Get metadata request parameters.
        
    Returns:
        GetFileMetadataResult with file metadata.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return GetFileMetadataResult(
                success=False,
                message='Not authenticated with Google Drive'
            )
        
        # Build fields to retrieve
        fields = [
            'id', 'name', 'mimeType', 'size', 'createdTime', 'modifiedTime',
            'webViewLink', 'webContentLink', 'description', 'parents',
            'starred', 'trashed', 'version', 'originalFilename'
        ]
        
        if request.include_permissions:
            fields.append('permissions')
        
        if request.include_properties:
            fields.extend(['properties', 'appProperties'])
        
        # Get file metadata
        file_data = service.files().get(
            fileId=request.file_id,
            fields=','.join(fields)
        ).execute()
        
        metadata = convert_api_file_to_metadata(file_data)
        
        return GetFileMetadataResult(
            success=True,
            metadata=metadata,
            message=f'Successfully retrieved metadata for file {request.file_id}'
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to get metadata for file {request.file_id}: {error_msg}')
        return GetFileMetadataResult(
            success=False,
            message=f'Failed to get metadata: {error_msg}'
        )
    except Exception as e:
        logger.error(f'Unexpected error getting metadata for file {request.file_id}: {e}')
        return GetFileMetadataResult(
            success=False,
            message=f'Unexpected error: {str(e)}'
        )


async def update_file_metadata_impl(request: UpdateFileMetadataRequest) -> UpdateFileMetadataResult:
    """Update file metadata in Google Drive.
    
    Args:
        request: Update metadata request parameters.
        
    Returns:
        UpdateFileMetadataResult with updated metadata.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return UpdateFileMetadataResult(
                success=False,
                message='Not authenticated with Google Drive'
            )
        
        # Prepare update body
        update_body = {}
        
        if request.name:
            update_body['name'] = request.name
        
        if request.description is not None:
            update_body['description'] = request.description
        
        if request.properties:
            update_body['properties'] = request.properties
        
        if request.starred is not None:
            update_body['starred'] = request.starred
        
        # Update file metadata
        updated_file = service.files().update(
            fileId=request.file_id,
            body=update_body,
            fields='*'
        ).execute()
        
        metadata = convert_api_file_to_metadata(updated_file)
        
        return UpdateFileMetadataResult(
            success=True,
            metadata=metadata,
            message=f'Successfully updated metadata for file {request.file_id}'
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to update metadata for file {request.file_id}: {error_msg}')
        return UpdateFileMetadataResult(
            success=False,
            message=f'Failed to update metadata: {error_msg}'
        )
    except Exception as e:
        logger.error(f'Unexpected error updating metadata for file {request.file_id}: {e}')
        return UpdateFileMetadataResult(
            success=False,
            message=f'Unexpected error: {str(e)}'
        ) 