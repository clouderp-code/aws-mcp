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

"""Folder operations implementation for Google Drive MCP server."""

from googleapiclient.errors import HttpError
from loguru import logger

from awslabs.gdrive_mcp_server.impl.auth import get_authenticated_service
from awslabs.gdrive_mcp_server.impl.tools.utils import (
    convert_api_file_to_file_info,
    handle_drive_api_error,
)
from awslabs.gdrive_mcp_server.models import (
    CreateFolderRequest,
    CreateFolderResult,
    ListFilesRequest,
    ListFilesResult,
)


async def create_folder_impl(request: CreateFolderRequest) -> CreateFolderResult:
    """Create a new folder in Google Drive.
    
    Args:
        request: Create folder request parameters.
        
    Returns:
        CreateFolderResult with folder information.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return CreateFolderResult(
                success=False,
                message='Not authenticated with Google Drive'
            )
        
        # Prepare folder metadata
        folder_metadata = {
            'name': request.name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if request.description:
            folder_metadata['description'] = request.description
        
        if request.parent_folder_id:
            folder_metadata['parents'] = [request.parent_folder_id]
        
        # Create the folder
        folder = service.files().create(
            body=folder_metadata,
            fields='id,name,webViewLink'
        ).execute()
        
        return CreateFolderResult(
            success=True,
            folder_id=folder['id'],
            folder_url=folder.get('webViewLink'),
            message=f'Successfully created folder {request.name}'
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to create folder {request.name}: {error_msg}')
        return CreateFolderResult(
            success=False,
            message=f'Failed to create folder: {error_msg}'
        )
    except Exception as e:
        logger.error(f'Unexpected error creating folder {request.name}: {e}')
        return CreateFolderResult(
            success=False,
            message=f'Unexpected error: {str(e)}'
        )


async def list_files_impl(request: ListFilesRequest) -> ListFilesResult:
    """List files and folders in a Google Drive folder.
    
    Args:
        request: List files request parameters.
        
    Returns:
        ListFilesResult with files and folders.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return ListFilesResult(
                success=False,
                message='Not authenticated with Google Drive'
            )
        
        # Build query for listing files
        query_parts = []
        
        if request.folder_id:
            query_parts.append(f"'{request.folder_id}' in parents")
        else:
            # List root folder
            query_parts.append("'root' in parents")
        
        query_parts.append("trashed=false")
        
        query = ' and '.join(query_parts)
        
        # Execute the query
        results = service.files().list(
            q=query,
            pageSize=request.max_results,
            pageToken=request.page_token,
            orderBy=request.order_by,
            fields='nextPageToken,files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink,webContentLink)'
        ).execute()
        
        all_items = results.get('files', [])
        
        # Separate files and folders
        files = []
        folders = []
        
        for item in all_items:
            file_info = convert_api_file_to_file_info(item)
            
            if item.get('mimeType') == 'application/vnd.google-apps.folder':
                if request.include_folders:
                    folders.append(file_info)
            else:
                files.append(file_info)
        
        return ListFilesResult(
            success=True,
            files=files,
            folders=folders,
            next_page_token=results.get('nextPageToken'),
            message=f'Successfully listed {len(files)} files and {len(folders)} folders'
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to list files in folder {request.folder_id}: {error_msg}')
        return ListFilesResult(
            success=False,
            message=f'Failed to list files: {error_msg}'
        )
    except Exception as e:
        logger.error(f'Unexpected error listing files in folder {request.folder_id}: {e}')
        return ListFilesResult(
            success=False,
            message=f'Unexpected error: {str(e)}'
        ) 