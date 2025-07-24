# Google Drive MCP Server API Reference

This document provides detailed reference information for all tools available in the Google Drive MCP server.

## Authentication

Before using any tools, authentication must be configured using environment variables or explicit credentials.

### Environment Variables

**Service Account:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

**OAuth2:**
```bash
export GDRIVE_CLIENT_CREDENTIALS="/path/to/client-credentials.json"
export GDRIVE_TOKEN_FILE="/path/to/token.json"
```

## File Operations

### ReadFile

Read file contents from Google Drive.

**Parameters:**
- `file_id` (string, required): Google Drive file ID
- `export_format` (string, optional): Export format for Google Workspace files
- `encoding` (string, default: "utf-8"): Text encoding for content
- `include_metadata` (boolean, default: false): Include file metadata in response

**Export Formats for Google Workspace Files:**
- Google Docs: `text/plain`, `application/pdf`, `text/html`
- Google Sheets: `text/csv`, `application/pdf`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Google Slides: `text/plain`, `application/pdf`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`

**Example:**
```json
{
  "file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "export_format": "text/plain",
  "include_metadata": true
}
```

**Response:**
```json
{
  "success": true,
  "content": "File content here...",
  "content_type": "text/plain",
  "encoding": "utf-8",
  "metadata": { /* FileMetadata object */ },
  "message": "Successfully read file"
}
```

### WriteFile

Create or update files in Google Drive.

**Parameters:**
- `name` (string, required): File name
- `content` (string/bytes, required): File content
- `mime_type` (string, optional): MIME type of the file
- `parent_folder_id` (string, optional): Parent folder ID
- `file_id` (string, optional): File ID for updates
- `encoding` (string, default: "utf-8"): Text encoding
- `description` (string, optional): File description
- `properties` (object, optional): Custom properties

**Example:**
```json
{
  "name": "my-document.txt",
  "content": "Hello, World!",
  "mime_type": "text/plain",
  "parent_folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "description": "A test document"
}
```

**Response:**
```json
{
  "success": true,
  "file_id": "1ABC123DEF456GHI789JKL",
  "file_url": "https://drive.google.com/file/d/1ABC123DEF456GHI789JKL/view",
  "message": "Successfully created file my-document.txt",
  "metadata": { /* FileMetadata object */ }
}
```

### DeleteFile

Delete files from Google Drive.

**Parameters:**
- `file_id` (string, required): Google Drive file ID
- `permanent` (boolean, default: false): Permanent deletion vs trash

**Example:**
```json
{
  "file_id": "1ABC123DEF456GHI789JKL",
  "permanent": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Moved file to trash",
  "file_id": "1ABC123DEF456GHI789JKL"
}
```

### CopyFile

Copy files within Google Drive.

**Parameters:**
- `file_id` (string, required): Source file ID
- `name` (string, optional): Name for copied file
- `parent_folder_id` (string, optional): Destination folder ID
- `description` (string, optional): Description for copied file

**Example:**
```json
{
  "file_id": "1ABC123DEF456GHI789JKL",
  "name": "Copy of my-document.txt",
  "parent_folder_id": "1DEF456GHI789JKL123ABC"
}
```

### MoveFile

Move files between folders.

**Parameters:**
- `file_id` (string, required): File ID to move
- `destination_folder_id` (string, required): Destination folder ID
- `remove_parents` (array, optional): Parent folder IDs to remove

**Example:**
```json
{
  "file_id": "1ABC123DEF456GHI789JKL",
  "destination_folder_id": "1DEF456GHI789JKL123ABC"
}
```

## Search and Discovery

### SearchFiles

Search for files in Google Drive with advanced filtering.

**Parameters:**
- `query` (string, optional): Search query string
- `file_types` (array, optional): List of MIME types to filter by
- `folder_id` (string, optional): Folder ID to search within
- `include_trashed` (boolean, default: false): Include trashed files
- `max_results` (integer, default: 100): Maximum number of results
- `order_by` (string, optional): Sort order (name, modifiedTime, etc.)
- `fields` (array, optional): Specific fields to retrieve

**Common MIME Types:**
- Text files: `text/plain`
- Google Docs: `application/vnd.google-apps.document`
- Google Sheets: `application/vnd.google-apps.spreadsheet`
- Google Slides: `application/vnd.google-apps.presentation`
- Folders: `application/vnd.google-apps.folder`
- PDF: `application/pdf`
- Images: `image/jpeg`, `image/png`

**Example:**
```json
{
  "query": "meeting notes",
  "file_types": ["text/plain", "application/vnd.google-apps.document"],
  "max_results": 20,
  "order_by": "modifiedTime desc"
}
```

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "id": "1ABC123DEF456GHI789JKL",
      "name": "Meeting Notes.txt",
      "mime_type": "text/plain",
      "size": 1024,
      "modified_time": "2023-12-01T10:30:00Z",
      "web_view_link": "https://drive.google.com/file/d/1ABC123DEF456GHI789JKL/view"
    }
  ],
  "total_count": 1,
  "next_page_token": null,
  "message": "Found 1 files matching search criteria"
}
```

### ListFiles

List files and folders in a Google Drive folder.

**Parameters:**
- `folder_id` (string, optional): Folder ID to list (root if None)
- `include_folders` (boolean, default: true): Include subfolders
- `max_results` (integer, default: 100): Maximum number of results
- `page_token` (string, optional): Pagination token
- `order_by` (string, default: "name"): Sort order

**Example:**
```json
{
  "folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "max_results": 50,
  "order_by": "modifiedTime desc"
}
```

## Folder Management

### CreateFolder

Create new folders in Google Drive.

**Parameters:**
- `name` (string, required): Folder name
- `parent_folder_id` (string, optional): Parent folder ID
- `description` (string, optional): Folder description

**Example:**
```json
{
  "name": "Project Documents",
  "parent_folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "description": "Documents for the current project"
}
```

**Response:**
```json
{
  "success": true,
  "folder_id": "1NEW123FOLDER456ID789ABC",
  "folder_url": "https://drive.google.com/drive/folders/1NEW123FOLDER456ID789ABC",
  "message": "Successfully created folder Project Documents"
}
```

## Metadata Operations

### GetFileMetadata

Retrieve detailed file metadata.

**Parameters:**
- `file_id` (string, required): Google Drive file ID
- `include_permissions` (boolean, default: true): Include permissions
- `include_properties` (boolean, default: true): Include custom properties

**Example:**
```json
{
  "file_id": "1ABC123DEF456GHI789JKL",
  "include_permissions": true,
  "include_properties": true
}
```

**Response:**
```json
{
  "success": true,
  "metadata": {
    "file_info": {
      "id": "1ABC123DEF456GHI789JKL",
      "name": "my-document.txt",
      "mime_type": "text/plain",
      "size": 1024,
      "created_time": "2023-12-01T09:00:00Z",
      "modified_time": "2023-12-01T10:30:00Z",
      "web_view_link": "https://drive.google.com/file/d/1ABC123DEF456GHI789JKL/view"
    },
    "description": "A test document",
    "parents": ["1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"],
    "permissions": [
      {
        "role": "owner",
        "type": "user",
        "email": "user@example.com"
      }
    ],
    "properties": {},
    "starred": false,
    "trashed": false
  },
  "message": "Successfully retrieved metadata"
}
```

### UpdateFileMetadata

Update file metadata and properties.

**Parameters:**
- `file_id` (string, required): Google Drive file ID
- `name` (string, optional): New file name
- `description` (string, optional): New description
- `properties` (object, optional): Custom properties to update
- `starred` (boolean, optional): Star status

**Example:**
```json
{
  "file_id": "1ABC123DEF456GHI789JKL",
  "name": "updated-document.txt",
  "description": "Updated description",
  "properties": {
    "project": "alpha",
    "version": "1.1"
  },
  "starred": true
}
```

## Data Models

### FileInfo

Basic file information structure:
```json
{
  "id": "string",
  "name": "string",
  "mime_type": "string",
  "size": "integer",
  "created_time": "datetime",
  "modified_time": "datetime",
  "web_view_link": "string",
  "download_link": "string"
}
```

### FileMetadata

Extended file metadata structure:
```json
{
  "file_info": "FileInfo",
  "description": "string",
  "parents": ["string"],
  "permissions": ["FilePermission"],
  "properties": "object",
  "app_properties": "object",
  "starred": "boolean",
  "trashed": "boolean",
  "version": "integer",
  "original_filename": "string"
}
```

### FilePermission

File permission structure:
```json
{
  "role": "string",
  "type": "string",
  "email": "string",
  "display_name": "string"
}
```

## Error Handling

All operations return a response with a `success` field. When `success` is false, check the `message` field for error details.

### Common Error Messages

- `"Not authenticated with Google Drive"` - Authentication required
- `"File or folder not found"` - Invalid file/folder ID
- `"Permission denied or quota exceeded"` - Access or quota issues
- `"Invalid request parameters"` - Malformed request
- `"API rate limit exceeded"` - Too many requests

### HTTP Status Code Mappings

- 200: Success
- 400: Bad Request - Invalid parameters
- 401: Unauthorized - Authentication required
- 403: Forbidden - Permission denied or quota exceeded
- 404: Not Found - File/folder not found
- 429: Too Many Requests - Rate limit exceeded

## Rate Limits and Quotas

Google Drive API has various quotas and limits:

- **Queries per day**: 1,000,000,000
- **Queries per 100 seconds per user**: 1,000
- **Queries per 100 seconds**: 10,000

Implement exponential backoff when encountering rate limits. 