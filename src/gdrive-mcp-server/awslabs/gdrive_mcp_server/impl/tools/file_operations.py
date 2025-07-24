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

"""File operations implementation for Google Drive MCP server."""

from typing import Union

from googleapiclient.errors import HttpError
from loguru import logger

from awslabs.gdrive_mcp_server.impl.auth import get_authenticated_service
from awslabs.gdrive_mcp_server.impl.tools.utils import (
    convert_api_file_to_metadata,
    download_file_content,
    handle_drive_api_error,
    upload_file_content,
)
from awslabs.gdrive_mcp_server.models import (
    CopyFileRequest,
    CopyFileResult,
    DeleteFileRequest,
    DeleteFileResult,
    MoveFileRequest,
    MoveFileResult,
    ReadFileRequest,
    ReadFileResult,
    WriteFileRequest,
    WriteFileResult,
)


async def read_file_impl(request: ReadFileRequest) -> ReadFileResult:
    """Read file content from Google Drive.
    
    Args:
        request: Read file request parameters.
        
    Returns:
        ReadFileResult with file content and metadata.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return ReadFileResult(
                success=False,
                message='Not authenticated with Google Drive'
            )
        
        # Download file content
        content_bytes, content_type = await download_file_content(
            request.file_id,
            request.export_format
        )
        
        # Convert content to string if it's text
        content: Union[str, bytes]
        if content_type.startswith('text/') or content_type in [
            'application/json',
            'application/xml',
            'application/javascript'
        ]:
            try:
                content = content_bytes.decode(request.encoding)
            except UnicodeDecodeError:
                logger.warning(f'Failed to decode file as {request.encoding}, returning bytes')
                content = content_bytes
        else:
            content = content_bytes
        
        # Get metadata if requested
        metadata = None
        if request.include_metadata:
            try:
                file_data = service.files().get(
                    fileId=request.file_id,
                    fields='*'
                ).execute()
                metadata = convert_api_file_to_metadata(file_data)
            except HttpError as e:
                logger.warning(f'Failed to get metadata for file {request.file_id}: {e}')
        
        return ReadFileResult(
            success=True,
            content=content,
            metadata=metadata,
            content_type=content_type,
            encoding=request.encoding if isinstance(content, str) else None,
            message=f'Successfully read file {request.file_id}'
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to read file {request.file_id}: {error_msg}')
        return ReadFileResult(
            success=False,
            message=f'Failed to read file: {error_msg}'
        )
    except Exception as e:
        logger.error(f'Unexpected error reading file {request.file_id}: {e}')
        return ReadFileResult(
            success=False,
            message=f'Unexpected error: {str(e)}'
        )


async def write_file_impl(request: WriteFileRequest) -> WriteFileResult:
    """Write file content to Google Drive.
    
    Args:
        request: Write file request parameters.
        
    Returns:
        WriteFileResult with file information.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return WriteFileResult(
                success=False,
                message='Not authenticated with Google Drive'
            )
        
        # Upload file content
        file_data = await upload_file_content(
            content=request.content,
            filename=request.name,
            mime_type=request.mime_type,
            file_id=request.file_id,
            parent_folder_id=request.parent_folder_id,
            description=request.description,
            properties=request.properties
        )
        
        # Get detailed metadata
        detailed_file = service.files().get(
            fileId=file_data['id'],
            fields='*'
        ).execute()
        
        metadata = convert_api_file_to_metadata(detailed_file)
        
        action = 'updated' if request.file_id else 'created'
        
        return WriteFileResult(
            success=True,
            file_id=file_data['id'],
            file_url=file_data.get('webViewLink'),
            message=f'Successfully {action} file {request.name}',
            metadata=metadata
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to write file {request.name}: {error_msg}')
        return WriteFileResult(
            success=False,
            message=f'Failed to write file: {error_msg}'
        )
    except Exception as e:
        logger.error(f'Unexpected error writing file {request.name}: {e}')
        return WriteFileResult(
            success=False,
            message=f'Unexpected error: {str(e)}'
        )


async def delete_file_impl(request: DeleteFileRequest) -> DeleteFileResult:
    """Delete file from Google Drive.
    
    Args:
        request: Delete file request parameters.
        
    Returns:
        DeleteFileResult with operation status.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return DeleteFileResult(
                success=False,
                message='Not authenticated with Google Drive',
                file_id=request.file_id
            )
        
        if request.permanent:
            # Permanently delete the file
            service.files().delete(fileId=request.file_id).execute()
            message = f'Permanently deleted file {request.file_id}'
        else:
            # Move to trash
            service.files().update(
                fileId=request.file_id,
                body={'trashed': True}
            ).execute()
            message = f'Moved file {request.file_id} to trash'
        
        return DeleteFileResult(
            success=True,
            message=message,
            file_id=request.file_id
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to delete file {request.file_id}: {error_msg}')
        return DeleteFileResult(
            success=False,
            message=f'Failed to delete file: {error_msg}',
            file_id=request.file_id
        )
    except Exception as e:
        logger.error(f'Unexpected error deleting file {request.file_id}: {e}')
        return DeleteFileResult(
            success=False,
            message=f'Unexpected error: {str(e)}',
            file_id=request.file_id
        )


async def copy_file_impl(request: CopyFileRequest) -> CopyFileResult:
    """Copy file in Google Drive.
    
    Args:
        request: Copy file request parameters.
        
    Returns:
        CopyFileResult with copied file information.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return CopyFileResult(
                success=False,
                message='Not authenticated with Google Drive'
            )
        
        # Prepare copy metadata
        copy_metadata = {}
        
        if request.name:
            copy_metadata['name'] = request.name
        
        if request.description:
            copy_metadata['description'] = request.description
        
        if request.parent_folder_id:
            copy_metadata['parents'] = [request.parent_folder_id]
        
        # Copy the file
        copied_file = service.files().copy(
            fileId=request.file_id,
            body=copy_metadata,
            fields='id,name,webViewLink'
        ).execute()
        
        return CopyFileResult(
            success=True,
            file_id=copied_file['id'],
            file_url=copied_file.get('webViewLink'),
            message=f'Successfully copied file to {copied_file["name"]}'
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to copy file {request.file_id}: {error_msg}')
        return CopyFileResult(
            success=False,
            message=f'Failed to copy file: {error_msg}'
        )
    except Exception as e:
        logger.error(f'Unexpected error copying file {request.file_id}: {e}')
        return CopyFileResult(
            success=False,
            message=f'Unexpected error: {str(e)}'
        )


async def move_file_impl(request: MoveFileRequest) -> MoveFileResult:
    """Move file in Google Drive.
    
    Args:
        request: Move file request parameters.
        
    Returns:
        MoveFileResult with operation status.
    """
    try:
        service = get_authenticated_service()
        if not service:
            return MoveFileResult(
                success=False,
                message='Not authenticated with Google Drive',
                file_id=request.file_id
            )
        
        # Get current parents if none specified to remove
        current_parents = request.remove_parents
        if not current_parents:
            file_data = service.files().get(
                fileId=request.file_id,
                fields='parents'
            ).execute()
            current_parents = file_data.get('parents', [])
        
        # Move the file
        service.files().update(
            fileId=request.file_id,
            addParents=request.destination_folder_id,
            removeParents=','.join(current_parents),
            fields='id,parents'
        ).execute()
        
        return MoveFileResult(
            success=True,
            file_id=request.file_id,
            message=f'Successfully moved file {request.file_id}'
        )
        
    except HttpError as e:
        error_msg = handle_drive_api_error(e)
        logger.error(f'Failed to move file {request.file_id}: {error_msg}')
        return MoveFileResult(
            success=False,
            message=f'Failed to move file: {error_msg}',
            file_id=request.file_id
        )
    except Exception as e:
        logger.error(f'Unexpected error moving file {request.file_id}: {e}')
        return MoveFileResult(
            success=False,
            message=f'Unexpected error: {str(e)}',
            file_id=request.file_id
        ) 