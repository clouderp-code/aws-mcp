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

"""Search operations implementation for Google Drive MCP server."""

from googleapiclient.errors import HttpError
from loguru import logger

from awslabs.gdrive_mcp_server.impl.auth import get_authenticated_service
from awslabs.gdrive_mcp_server.impl.tools.utils import (
    build_query,
    convert_api_file_to_file_info,
    handle_drive_api_error,
)
from awslabs.gdrive_mcp_server.models import (
    SearchFilesRequest,
    SearchFilesResult,
)


async def search_files_impl(request: SearchFilesRequest) -> SearchFilesResult:
    """Search for files in Google Drive.
    
    Args:
        request: Search files request parameters.
        
    Returns:
        SearchFilesResult with found files.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return SearchFilesResult(
                success=False,
                message='Not authenticated with Google Drive'
            )
        
        # Build search query
        query = build_query(
            search_query=request.query,
            file_types=request.file_types,
            folder_id=request.folder_id,
            include_trashed=request.include_trashed
        )
        
        # Prepare fields to retrieve
        fields_str = ','.join(request.fields)
        
        # Execute search
        results = service.files().list(
            q=query,
            pageSize=min(request.max_results, 1000),  # Google Drive API limit
            orderBy=request.order_by,
            fields=f'nextPageToken,files({fields_str},createdTime,modifiedTime,webViewLink,webContentLink)'
        ).execute()
        
        files = []
        for file_data in results.get('files', []):
            file_info = convert_api_file_to_file_info(file_data)
            files.append(file_info)
        
        # Count total results if possible
        total_count = len(files)
        
        # If we got the maximum results, there might be more
        if len(files) == min(request.max_results, 1000):
            total_count = f"{len(files)}+"
        
        return SearchFilesResult(
            success=True,
            files=files,
            total_count=len(files),
            next_page_token=results.get('nextPageToken'),
            message=f'Found {len(files)} files matching search criteria'
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to search files: {error_msg}')
        return SearchFilesResult(
            success=False,
            message=f'Search failed: {error_msg}'
        )
    except Exception as e:
        logger.error(f'Unexpected error searching files: {e}')
        return SearchFilesResult(
            success=False,
            message=f'Unexpected error: {str(e)}'
        ) 