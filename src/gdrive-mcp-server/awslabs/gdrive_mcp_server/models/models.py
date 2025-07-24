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

"""Pydantic models for Google Drive MCP server operations."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional, Union


# Base Models
class FilePermission(BaseModel):
    """Model for Google Drive file permissions.
    
    Attributes:
        role: The role granted by this permission (owner, editor, viewer, etc.).
        type: The type of the grantee (user, group, domain, anyone).
        email: Email address of the user or group.
        display_name: Display name of the permission holder.
    """
    role: str = Field(..., description='Permission role (owner, editor, viewer)')
    type: str = Field(..., description='Permission type (user, group, domain, anyone)')
    email: Optional[str] = Field(None, description='Email address of the permission holder')
    display_name: Optional[str] = Field(None, description='Display name of the permission holder')


class FileInfo(BaseModel):
    """Basic file information model.
    
    Attributes:
        id: Unique identifier for the file.
        name: Name of the file.
        mime_type: MIME type of the file.
        size: Size of the file in bytes.
        created_time: When the file was created.
        modified_time: When the file was last modified.
        web_view_link: Link to view the file in Google Drive web interface.
        download_link: Direct download link for the file.
    """
    id: str = Field(..., description='Unique file identifier')
    name: str = Field(..., description='File name')
    mime_type: str = Field(..., description='MIME type of the file')
    size: Optional[int] = Field(None, description='File size in bytes')
    created_time: Optional[datetime] = Field(None, description='File creation timestamp')
    modified_time: Optional[datetime] = Field(None, description='File modification timestamp')
    web_view_link: Optional[str] = Field(None, description='Web view link')
    download_link: Optional[str] = Field(None, description='Download link')


class FileMetadata(BaseModel):
    """Extended file metadata model.
    
    Attributes:
        file_info: Basic file information.
        description: File description.
        parents: List of parent folder IDs.
        permissions: List of file permissions.
        properties: Custom properties dictionary.
        app_properties: Application-specific properties.
        starred: Whether the file is starred.
        trashed: Whether the file is in trash.
        version: File version number.
        original_filename: Original filename if different from current name.
        full_text: Full text content for search indexing.
    """
    file_info: FileInfo = Field(..., description='Basic file information')
    description: Optional[str] = Field(None, description='File description')
    parents: List[str] = Field(default_factory=list, description='Parent folder IDs')
    permissions: List[FilePermission] = Field(default_factory=list, description='File permissions')
    properties: Dict[str, str] = Field(default_factory=dict, description='Custom properties')
    app_properties: Dict[str, str] = Field(default_factory=dict, description='App-specific properties')
    starred: bool = Field(False, description='Whether file is starred')
    trashed: bool = Field(False, description='Whether file is trashed')
    version: Optional[int] = Field(None, description='File version number')
    original_filename: Optional[str] = Field(None, description='Original filename')
    full_text: Optional[str] = Field(None, description='Full text content for search')


# Authentication Models
class AuthRequest(BaseModel):
    """Authentication request model.
    
    Attributes:
        auth_type: Type of authentication (service_account, oauth2).
        credentials_path: Path to credentials file.
        token_path: Path to token file (for OAuth2).
        scopes: List of required OAuth2 scopes.
    """
    auth_type: Literal['service_account', 'oauth2'] = Field(
        ..., description='Authentication type'
    )
    credentials_path: Optional[str] = Field(None, description='Path to credentials file')
    token_path: Optional[str] = Field(None, description='Path to token file (OAuth2)')
    scopes: List[str] = Field(
        default_factory=lambda: ['https://www.googleapis.com/auth/drive'],
        description='OAuth2 scopes'
    )


class AuthResult(BaseModel):
    """Authentication result model.
    
    Attributes:
        success: Whether authentication was successful.
        message: Status message.
        user_email: Authenticated user's email.
        auth_type: Type of authentication used.
    """
    success: bool = Field(..., description='Authentication success status')
    message: str = Field(..., description='Status message')
    user_email: Optional[str] = Field(None, description='Authenticated user email')
    auth_type: Optional[str] = Field(None, description='Authentication type used')


# File Operation Models
class ReadFileRequest(BaseModel):
    """Request model for reading files from Google Drive.
    
    Attributes:
        file_id: Google Drive file ID.
        export_format: Export format for Google Workspace files.
        encoding: Text encoding for content.
        include_metadata: Whether to include file metadata.
    """
    file_id: str = Field(..., description='Google Drive file ID')
    export_format: Optional[str] = Field(
        None, description='Export format (text/plain, application/pdf, etc.)'
    )
    encoding: str = Field('utf-8', description='Text encoding')
    include_metadata: bool = Field(False, description='Include file metadata in response')


class ReadFileResult(BaseModel):
    """Result model for file reading operations.
    
    Attributes:
        success: Whether the operation was successful.
        content: File content as string or bytes.
        metadata: File metadata if requested.
        content_type: MIME type of the content.
        encoding: Encoding used for text content.
        message: Status or error message.
    """
    success: bool = Field(..., description='Operation success status')
    content: Optional[Union[str, bytes]] = Field(None, description='File content')
    metadata: Optional[FileMetadata] = Field(None, description='File metadata')
    content_type: Optional[str] = Field(None, description='Content MIME type')
    encoding: Optional[str] = Field(None, description='Content encoding')
    message: str = Field(..., description='Status message')


class WriteFileRequest(BaseModel):
    """Request model for writing files to Google Drive.
    
    Attributes:
        name: File name.
        content: File content (string or bytes).
        mime_type: MIME type of the file.
        parent_folder_id: ID of parent folder.
        file_id: ID for updating existing file.
        encoding: Text encoding for content.
        description: File description.
        properties: Custom properties.
    """
    name: str = Field(..., description='File name')
    content: Union[str, bytes] = Field(..., description='File content')
    mime_type: Optional[str] = Field(None, description='File MIME type')
    parent_folder_id: Optional[str] = Field(None, description='Parent folder ID')
    file_id: Optional[str] = Field(None, description='File ID for updates')
    encoding: str = Field('utf-8', description='Text encoding')
    description: Optional[str] = Field(None, description='File description')
    properties: Dict[str, str] = Field(default_factory=dict, description='Custom properties')


class WriteFileResult(BaseModel):
    """Result model for file writing operations.
    
    Attributes:
        success: Whether the operation was successful.
        file_id: ID of the created or updated file.
        file_url: Web view URL of the file.
        message: Status or error message.
        metadata: File metadata.
    """
    success: bool = Field(..., description='Operation success status')
    file_id: Optional[str] = Field(None, description='File ID')
    file_url: Optional[str] = Field(None, description='File web view URL')
    message: str = Field(..., description='Status message')
    metadata: Optional[FileMetadata] = Field(None, description='File metadata')


class DeleteFileRequest(BaseModel):
    """Request model for deleting files.
    
    Attributes:
        file_id: Google Drive file ID.
        permanent: Whether to permanently delete (true) or move to trash (false).
    """
    file_id: str = Field(..., description='Google Drive file ID')
    permanent: bool = Field(False, description='Permanent deletion vs trash')


class DeleteFileResult(BaseModel):
    """Result model for file deletion operations.
    
    Attributes:
        success: Whether the operation was successful.
        message: Status or error message.
        file_id: ID of the deleted file.
    """
    success: bool = Field(..., description='Operation success status')
    message: str = Field(..., description='Status message')
    file_id: str = Field(..., description='Deleted file ID')


class CopyFileRequest(BaseModel):
    """Request model for copying files.
    
    Attributes:
        file_id: Source file ID.
        name: Name for the copied file.
        parent_folder_id: Destination folder ID.
        description: Description for the copied file.
    """
    file_id: str = Field(..., description='Source file ID')
    name: Optional[str] = Field(None, description='Name for copied file')
    parent_folder_id: Optional[str] = Field(None, description='Destination folder ID')
    description: Optional[str] = Field(None, description='Description for copied file')


class CopyFileResult(BaseModel):
    """Result model for file copy operations.
    
    Attributes:
        success: Whether the operation was successful.
        file_id: ID of the copied file.
        file_url: Web view URL of the copied file.
        message: Status or error message.
    """
    success: bool = Field(..., description='Operation success status')
    file_id: Optional[str] = Field(None, description='Copied file ID')
    file_url: Optional[str] = Field(None, description='Copied file web view URL')
    message: str = Field(..., description='Status message')


class MoveFileRequest(BaseModel):
    """Request model for moving files.
    
    Attributes:
        file_id: File ID to move.
        destination_folder_id: Destination folder ID.
        remove_parents: Parent folder IDs to remove.
    """
    file_id: str = Field(..., description='File ID to move')
    destination_folder_id: str = Field(..., description='Destination folder ID')
    remove_parents: List[str] = Field(default_factory=list, description='Parent IDs to remove')


class MoveFileResult(BaseModel):
    """Result model for file move operations.
    
    Attributes:
        success: Whether the operation was successful.
        file_id: ID of the moved file.
        message: Status or error message.
    """
    success: bool = Field(..., description='Operation success status')
    file_id: str = Field(..., description='Moved file ID')
    message: str = Field(..., description='Status message')


# Search and Listing Models
class SearchFilesRequest(BaseModel):
    """Request model for searching files.
    
    Attributes:
        query: Search query string.
        file_types: List of MIME types to filter by.
        folder_id: Folder ID to search within.
        include_trashed: Whether to include trashed files.
        max_results: Maximum number of results.
        order_by: Sort order specification.
        fields: Specific fields to retrieve.
    """
    query: Optional[str] = Field(None, description='Search query')
    file_types: List[str] = Field(default_factory=list, description='MIME types to filter by')
    folder_id: Optional[str] = Field(None, description='Folder to search within')
    include_trashed: bool = Field(False, description='Include trashed files')
    max_results: int = Field(100, description='Maximum number of results')
    order_by: Optional[str] = Field(None, description='Sort order (name, modifiedTime, etc.)')
    fields: List[str] = Field(
        default_factory=lambda: ['id', 'name', 'mimeType', 'size', 'modifiedTime'],
        description='Fields to retrieve'
    )


class SearchFilesResult(BaseModel):
    """Result model for file search operations.
    
    Attributes:
        success: Whether the operation was successful.
        files: List of found files.
        total_count: Total number of matching files.
        next_page_token: Token for pagination.
        message: Status or error message.
    """
    success: bool = Field(..., description='Operation success status')
    files: List[FileInfo] = Field(default_factory=list, description='Found files')
    total_count: int = Field(0, description='Total matching files')
    next_page_token: Optional[str] = Field(None, description='Pagination token')
    message: str = Field(..., description='Status message')


class ListFilesRequest(BaseModel):
    """Request model for listing files in a folder.
    
    Attributes:
        folder_id: Folder ID to list (root if None).
        include_folders: Whether to include subfolders.
        max_results: Maximum number of results.
        page_token: Pagination token.
        order_by: Sort order specification.
    """
    folder_id: Optional[str] = Field(None, description='Folder ID (root if None)')
    include_folders: bool = Field(True, description='Include subfolders')
    max_results: int = Field(100, description='Maximum number of results')
    page_token: Optional[str] = Field(None, description='Pagination token')
    order_by: Optional[str] = Field('name', description='Sort order')


class ListFilesResult(BaseModel):
    """Result model for file listing operations.
    
    Attributes:
        success: Whether the operation was successful.
        files: List of files in the folder.
        folders: List of subfolders.
        next_page_token: Token for pagination.
        message: Status or error message.
    """
    success: bool = Field(..., description='Operation success status')
    files: List[FileInfo] = Field(default_factory=list, description='Files in folder')
    folders: List[FileInfo] = Field(default_factory=list, description='Subfolders')
    next_page_token: Optional[str] = Field(None, description='Pagination token')
    message: str = Field(..., description='Status message')


# Folder Management Models
class CreateFolderRequest(BaseModel):
    """Request model for creating folders.
    
    Attributes:
        name: Folder name.
        parent_folder_id: Parent folder ID.
        description: Folder description.
    """
    name: str = Field(..., description='Folder name')
    parent_folder_id: Optional[str] = Field(None, description='Parent folder ID')
    description: Optional[str] = Field(None, description='Folder description')


class CreateFolderResult(BaseModel):
    """Result model for folder creation operations.
    
    Attributes:
        success: Whether the operation was successful.
        folder_id: ID of the created folder.
        folder_url: Web view URL of the folder.
        message: Status or error message.
    """
    success: bool = Field(..., description='Operation success status')
    folder_id: Optional[str] = Field(None, description='Created folder ID')
    folder_url: Optional[str] = Field(None, description='Folder web view URL')
    message: str = Field(..., description='Status message')


# Metadata Management Models
class GetFileMetadataRequest(BaseModel):
    """Request model for getting file metadata.
    
    Attributes:
        file_id: Google Drive file ID.
        include_permissions: Whether to include permissions.
        include_properties: Whether to include custom properties.
    """
    file_id: str = Field(..., description='Google Drive file ID')
    include_permissions: bool = Field(True, description='Include permissions')
    include_properties: bool = Field(True, description='Include custom properties')


class GetFileMetadataResult(BaseModel):
    """Result model for metadata retrieval operations.
    
    Attributes:
        success: Whether the operation was successful.
        metadata: File metadata.
        message: Status or error message.
    """
    success: bool = Field(..., description='Operation success status')
    metadata: Optional[FileMetadata] = Field(None, description='File metadata')
    message: str = Field(..., description='Status message')


class UpdateFileMetadataRequest(BaseModel):
    """Request model for updating file metadata.
    
    Attributes:
        file_id: Google Drive file ID.
        name: New file name.
        description: New file description.
        properties: Custom properties to update.
        starred: Whether to star the file.
    """
    file_id: str = Field(..., description='Google Drive file ID')
    name: Optional[str] = Field(None, description='New file name')
    description: Optional[str] = Field(None, description='New description')
    properties: Dict[str, str] = Field(default_factory=dict, description='Properties to update')
    starred: Optional[bool] = Field(None, description='Star status')


class UpdateFileMetadataResult(BaseModel):
    """Result model for metadata update operations.
    
    Attributes:
        success: Whether the operation was successful.
        metadata: Updated file metadata.
        message: Status or error message.
    """
    success: bool = Field(..., description='Operation success status')
    metadata: Optional[FileMetadata] = Field(None, description='Updated metadata')
    message: str = Field(..., description='Status message') 