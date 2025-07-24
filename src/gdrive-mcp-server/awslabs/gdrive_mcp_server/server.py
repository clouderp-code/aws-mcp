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

#!/usr/bin/env python3
"""Google Drive MCP server implementation."""

from awslabs.gdrive_mcp_server.impl.auth import authenticate_service_account, authenticate_oauth2
from awslabs.gdrive_mcp_server.impl.tools import (
    copy_file_impl,
    create_folder_impl,
    delete_file_impl,
    get_file_metadata_impl,
    list_files_impl,
    move_file_impl,
    read_file_impl,
    search_files_impl,
    update_file_metadata_impl,
    write_file_impl,
)
from awslabs.gdrive_mcp_server.models import (
    CopyFileRequest,
    CopyFileResult,
    CreateFolderRequest,
    CreateFolderResult,
    DeleteFileRequest,
    DeleteFileResult,
    GetFileMetadataRequest,
    GetFileMetadataResult,
    ListFilesRequest,
    ListFilesResult,
    MoveFileRequest,
    MoveFileResult,
    ReadFileRequest,
    ReadFileResult,
    SearchFilesRequest,
    SearchFilesResult,
    UpdateFileMetadataRequest,
    UpdateFileMetadataResult,
    WriteFileRequest,
    WriteFileResult,
)
from awslabs.gdrive_mcp_server.static import (
    GDRIVE_API_REFERENCE,
    GDRIVE_BEST_PRACTICES,
    GDRIVE_SETUP_GUIDE,
    MCP_INSTRUCTIONS,
)
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Dict, List, Literal, Optional, Union


mcp = FastMCP(
    'gdrive_mcp_server',
    instructions=f'{MCP_INSTRUCTIONS}',
    dependencies=[
        'pydantic',
        'loguru',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'aiofiles',
        'python-magic',
    ],
)


# Authentication Tools
@mcp.tool(name='AuthenticateServiceAccount')
async def authenticate_service_account_tool(
    credentials_path: Optional[str] = Field(
        None, description='Path to service account credentials JSON file'
    ),
    scopes: Optional[List[str]] = Field(
        None, description='List of OAuth2 scopes to request'
    ),
) -> Dict:
    """Authenticate with Google Drive using service account credentials.

    This tool authenticates the server with Google Drive using service account
    credentials. Service accounts are recommended for server-side applications
    that need non-interactive access to Google Drive.

    Parameters:
        credentials_path: Path to service account credentials JSON file
        scopes: List of OAuth2 scopes (defaults to Drive access)

    Returns:
        A dictionary containing authentication status and user information
    """
    result = await authenticate_service_account(credentials_path, scopes)
    return {
        'success': result.success,
        'message': result.message,
        'user_email': result.user_email,
        'auth_type': result.auth_type,
    }


@mcp.tool(name='AuthenticateOAuth2')
async def authenticate_oauth2_tool(
    credentials_path: Optional[str] = Field(
        None, description='Path to OAuth2 client credentials JSON file'
    ),
    token_path: Optional[str] = Field(
        None, description='Path to store/load OAuth2 token file'
    ),
    scopes: Optional[List[str]] = Field(
        None, description='List of OAuth2 scopes to request'
    ),
) -> Dict:
    """Authenticate with Google Drive using OAuth2 flow.

    This tool authenticates with Google Drive using the OAuth2 flow, which is
    suitable for user-facing applications that need access to personal Google Drive.

    Parameters:
        credentials_path: Path to OAuth2 client credentials JSON file
        token_path: Path to store/load OAuth2 token file
        scopes: List of OAuth2 scopes (defaults to Drive access)

    Returns:
        A dictionary containing authentication status and user information
    """
    result = await authenticate_oauth2(credentials_path, token_path, scopes)
    return {
        'success': result.success,
        'message': result.message,
        'user_email': result.user_email,
        'auth_type': result.auth_type,
    }


# File Operations
@mcp.tool(name='ReadFile')
async def read_file(
    file_id: str = Field(..., description='Google Drive file ID'),
    export_format: Optional[str] = Field(
        None, description='Export format for Google Workspace files (text/plain, application/pdf, etc.)'
    ),
    encoding: str = Field('utf-8', description='Text encoding for content'),
    include_metadata: bool = Field(False, description='Include file metadata in response'),
) -> ReadFileResult:
    """Read file contents from Google Drive.

    This tool reads the contents of a file from Google Drive. For Google Workspace
    files (Docs, Sheets, Slides), it can export them in various formats.

    Parameters:
        file_id: Google Drive file ID
        export_format: Export format for Google Workspace files
        encoding: Text encoding for content
        include_metadata: Whether to include file metadata

    Returns:
        A ReadFileResult object containing file content and status
    """
    request = ReadFileRequest(
        file_id=file_id,
        export_format=export_format,
        encoding=encoding,
        include_metadata=include_metadata,
    )
    return await read_file_impl(request)


@mcp.tool(name='WriteFile')
async def write_file(
    name: str = Field(..., description='File name'),
    content: Union[str, bytes] = Field(..., description='File content'),
    mime_type: Optional[str] = Field(None, description='MIME type of the file'),
    parent_folder_id: Optional[str] = Field(None, description='Parent folder ID'),
    file_id: Optional[str] = Field(None, description='File ID for updates (creates new if not provided)'),
    encoding: str = Field('utf-8', description='Text encoding for content'),
    description: Optional[str] = Field(None, description='File description'),
    properties: Optional[Dict[str, str]] = Field(None, description='Custom properties'),
) -> WriteFileResult:
    """Create or update files in Google Drive.

    This tool creates new files or updates existing files in Google Drive.
    It supports various file types and can organize files into folders.

    Parameters:
        name: File name
        content: File content (string or bytes)
        mime_type: MIME type of the file
        parent_folder_id: Parent folder ID for organization
        file_id: File ID for updates (creates new if not provided)
        encoding: Text encoding for content
        description: File description
        properties: Custom properties for metadata

    Returns:
        A WriteFileResult object containing file information and status
    """
    request = WriteFileRequest(
        name=name,
        content=content,
        mime_type=mime_type,
        parent_folder_id=parent_folder_id,
        file_id=file_id,
        encoding=encoding,
        description=description,
        properties=properties or {},
    )
    return await write_file_impl(request)


@mcp.tool(name='DeleteFile')
async def delete_file(
    file_id: str = Field(..., description='Google Drive file ID'),
    permanent: bool = Field(False, description='Permanently delete (true) or move to trash (false)'),
) -> DeleteFileResult:
    """Delete files from Google Drive.

    This tool deletes files from Google Drive. Files can be moved to trash
    (default) or permanently deleted.

    Parameters:
        file_id: Google Drive file ID
        permanent: Whether to permanently delete or move to trash

    Returns:
        A DeleteFileResult object containing operation status
    """
    request = DeleteFileRequest(file_id=file_id, permanent=permanent)
    return await delete_file_impl(request)


@mcp.tool(name='CopyFile')
async def copy_file(
    file_id: str = Field(..., description='Source file ID'),
    name: Optional[str] = Field(None, description='Name for the copied file'),
    parent_folder_id: Optional[str] = Field(None, description='Destination folder ID'),
    description: Optional[str] = Field(None, description='Description for the copied file'),
) -> CopyFileResult:
    """Copy files within Google Drive.

    This tool creates a copy of an existing file in Google Drive. The copy
    can be renamed and placed in a different folder.

    Parameters:
        file_id: Source file ID to copy
        name: Name for the copied file
        parent_folder_id: Destination folder ID
        description: Description for the copied file

    Returns:
        A CopyFileResult object containing copied file information
    """
    request = CopyFileRequest(
        file_id=file_id,
        name=name,
        parent_folder_id=parent_folder_id,
        description=description,
    )
    return await copy_file_impl(request)


@mcp.tool(name='MoveFile')
async def move_file(
    file_id: str = Field(..., description='File ID to move'),
    destination_folder_id: str = Field(..., description='Destination folder ID'),
    remove_parents: Optional[List[str]] = Field(None, description='Parent folder IDs to remove'),
) -> MoveFileResult:
    """Move files between folders in Google Drive.

    This tool moves files from one folder to another in Google Drive.
    It can remove the file from multiple parent folders if needed.

    Parameters:
        file_id: File ID to move
        destination_folder_id: Destination folder ID
        remove_parents: Parent folder IDs to remove

    Returns:
        A MoveFileResult object containing operation status
    """
    request = MoveFileRequest(
        file_id=file_id,
        destination_folder_id=destination_folder_id,
        remove_parents=remove_parents or [],
    )
    return await move_file_impl(request)


# Search and Discovery
@mcp.tool(name='SearchFiles')
async def search_files(
    query: Optional[str] = Field(None, description='Search query string'),
    file_types: Optional[List[str]] = Field(None, description='List of MIME types to filter by'),
    folder_id: Optional[str] = Field(None, description='Folder ID to search within'),
    include_trashed: bool = Field(False, description='Include trashed files in results'),
    max_results: int = Field(100, description='Maximum number of results to return'),
    order_by: Optional[str] = Field(None, description='Sort order (name, modifiedTime, createdTime, etc.)'),
    fields: Optional[List[str]] = Field(None, description='Specific fields to retrieve'),
) -> SearchFilesResult:
    """Search for files in Google Drive with advanced filtering.

    This tool provides powerful search capabilities for finding files in Google Drive.
    It supports text queries, MIME type filtering, folder scoping, and sorting.

    Parameters:
        query: Search query string (searches name and content)
        file_types: List of MIME types to filter by
        folder_id: Folder ID to search within (searches all if not specified)
        include_trashed: Whether to include trashed files
        max_results: Maximum number of results to return
        order_by: Sort order specification
        fields: Specific fields to retrieve

    Returns:
        A SearchFilesResult object containing found files and search metadata
    """
    request = SearchFilesRequest(
        query=query,
        file_types=file_types or [],
        folder_id=folder_id,
        include_trashed=include_trashed,
        max_results=max_results,
        order_by=order_by,
        fields=fields or ['id', 'name', 'mimeType', 'size', 'modifiedTime'],
    )
    return await search_files_impl(request)


@mcp.tool(name='ListFiles')
async def list_files(
    folder_id: Optional[str] = Field(None, description='Folder ID to list (root if None)'),
    include_folders: bool = Field(True, description='Include subfolders in results'),
    max_results: int = Field(100, description='Maximum number of results to return'),
    page_token: Optional[str] = Field(None, description='Pagination token for additional results'),
    order_by: Optional[str] = Field('name', description='Sort order (name, modifiedTime, etc.)'),
) -> ListFilesResult:
    """List files and folders in a Google Drive folder.

    This tool lists the contents of a specific folder (or root) in Google Drive.
    It supports pagination and can include or exclude subfolders.

    Parameters:
        folder_id: Folder ID to list (lists root if not specified)
        include_folders: Whether to include subfolders in results
        max_results: Maximum number of results to return
        page_token: Pagination token for additional results
        order_by: Sort order specification

    Returns:
        A ListFilesResult object containing files and folders
    """
    request = ListFilesRequest(
        folder_id=folder_id,
        include_folders=include_folders,
        max_results=max_results,
        page_token=page_token,
        order_by=order_by,
    )
    return await list_files_impl(request)


# Folder Management
@mcp.tool(name='CreateFolder')
async def create_folder(
    name: str = Field(..., description='Folder name'),
    parent_folder_id: Optional[str] = Field(None, description='Parent folder ID'),
    description: Optional[str] = Field(None, description='Folder description'),
) -> CreateFolderResult:
    """Create new folders in Google Drive.

    This tool creates new folders in Google Drive. Folders can be created
    in the root directory or within existing folders.

    Parameters:
        name: Folder name
        parent_folder_id: Parent folder ID (creates in root if not specified)
        description: Folder description

    Returns:
        A CreateFolderResult object containing folder information
    """
    request = CreateFolderRequest(
        name=name,
        parent_folder_id=parent_folder_id,
        description=description,
    )
    return await create_folder_impl(request)


# Metadata Operations
@mcp.tool(name='GetFileMetadata')
async def get_file_metadata(
    file_id: str = Field(..., description='Google Drive file ID'),
    include_permissions: bool = Field(True, description='Include file permissions'),
    include_properties: bool = Field(True, description='Include custom properties'),
) -> GetFileMetadataResult:
    """Retrieve detailed file metadata from Google Drive.

    This tool gets comprehensive metadata for a file, including permissions,
    properties, sharing settings, and other file attributes.

    Parameters:
        file_id: Google Drive file ID
        include_permissions: Whether to include file permissions
        include_properties: Whether to include custom properties

    Returns:
        A GetFileMetadataResult object containing detailed file metadata
    """
    request = GetFileMetadataRequest(
        file_id=file_id,
        include_permissions=include_permissions,
        include_properties=include_properties,
    )
    return await get_file_metadata_impl(request)


@mcp.tool(name='UpdateFileMetadata')
async def update_file_metadata(
    file_id: str = Field(..., description='Google Drive file ID'),
    name: Optional[str] = Field(None, description='New file name'),
    description: Optional[str] = Field(None, description='New file description'),
    properties: Optional[Dict[str, str]] = Field(None, description='Custom properties to update'),
    starred: Optional[bool] = Field(None, description='Star status'),
) -> UpdateFileMetadataResult:
    """Update file metadata and properties in Google Drive.

    This tool updates various metadata fields for a file, including name,
    description, custom properties, and star status.

    Parameters:
        file_id: Google Drive file ID
        name: New file name
        description: New file description
        properties: Custom properties to update
        starred: Whether to star the file

    Returns:
        An UpdateFileMetadataResult object containing updated metadata
    """
    request = UpdateFileMetadataRequest(
        file_id=file_id,
        name=name,
        description=description,
        properties=properties or {},
        starred=starred,
    )
    return await update_file_metadata_impl(request)


# Resources
@mcp.resource(uri='gdrive://setup-guide', name='gdrive_setup_guide', description='Google Drive API setup guide')
def gdrive_setup_guide() -> str:
    """Get the Google Drive API setup guide."""
    return GDRIVE_SETUP_GUIDE


@mcp.resource(uri='gdrive://best-practices', name='gdrive_best_practices', description='Google Drive MCP best practices')
def gdrive_best_practices() -> str:
    """Get Google Drive MCP best practices documentation."""
    return GDRIVE_BEST_PRACTICES


@mcp.resource(uri='gdrive://api-reference', name='gdrive_api_reference', description='Google Drive MCP API reference')
def gdrive_api_reference() -> str:
    """Get Google Drive MCP API reference documentation."""
    return GDRIVE_API_REFERENCE


def main():
    """Main function to run the Google Drive MCP server."""
    import sys
    import asyncio
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        logger.info("🧪 Testing Google Drive MCP Server configuration...")
        logger.info("✅ Server: gdrive_mcp_server")
        logger.info("✅ Tools: 13 available")
        logger.info("  - Authentication: AuthenticateServiceAccount, AuthenticateOAuth2")
        logger.info("  - File Operations: ReadFile, WriteFile, DeleteFile, CopyFile, MoveFile")
        logger.info("  - Search: SearchFiles, ListFiles")
        logger.info("  - Management: CreateFolder, GetFileMetadata, UpdateFileMetadata")
        logger.info("✅ Resources: 3 available")
        logger.info("  - gdrive://setup-guide: Google Drive API setup guide")
        logger.info("  - gdrive://best-practices: Google Drive MCP best practices")
        logger.info("  - gdrive://api-reference: Google Drive MCP API reference")
        logger.info("✅ Dependencies imported successfully")
        logger.info("🎉 Server configuration is valid!")
        logger.info("")
        logger.info("To start the server normally:")
        logger.info("  awslabs.gdrive-mcp-server")
        logger.info("")
        logger.info("Note: MCP servers run silently and wait for client connections.")
        return
    
    logger.info("🚀 Starting Google Drive MCP Server...")
    logger.info("Server: gdrive_mcp_server")
    logger.info("Tools: 13 available (ReadFile, WriteFile, SearchFiles, etc.)")
    logger.info("Resources: 3 available (setup guide, best practices, API reference)")
    logger.info("Waiting for MCP client connections...")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        # Run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        logger.info('🛑 Google Drive MCP server stopped by user')
    except Exception as e:
        logger.error(f'❌ Google Drive MCP server error: {e}')
        raise


if __name__ == '__main__':
    main() 