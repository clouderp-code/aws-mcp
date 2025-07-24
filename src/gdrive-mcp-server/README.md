# Google Drive MCP Server

An AWS Labs Model Context Protocol (MCP) server that provides seamless integration with Google Drive, enabling AI assistants to read, write, search, and manage files in Google Drive.

## Features

### Core Functionality
- **File Operations**: Read, write, update, and delete files in Google Drive
- **Search Capabilities**: Advanced search across files and folders with metadata filtering
- **Folder Management**: Create, organize, and manage folder structures
- **Permission Management**: Handle file sharing and permissions
- **Metadata Access**: Retrieve and update file metadata, comments, and properties

### Supported File Types
- **Documents**: Google Docs, plain text, markdown
- **Spreadsheets**: Google Sheets, CSV, Excel files
- **Presentations**: Google Slides, PowerPoint files
- **Media**: Images, videos, audio files
- **Archives**: ZIP, PDF, and other document formats
- **Code**: Source code files with syntax preservation

## Installation

### Prerequisites
- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- Google Cloud Project with Drive API enabled
- Service Account or OAuth2 credentials

### Install uv (if not already installed)
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

### Install from Source
```bash
cd /opt/mycode/aws-mcp/src/gdrive-mcp-server

# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or .venv\Scripts\activate on Windows

# Install the package
uv pip install -e .
```

### Development Installation
```bash
cd /opt/mycode/aws-mcp/src/gdrive-mcp-server

# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or .venv\Scripts\activate on Windows

# Install with development dependencies
uv pip install -e ".[dev]"
```

**Note**: The `uv venv` command creates a `.venv` directory in your project. This directory is included in `.gitignore` and contains your isolated Python environment.

To deactivate the virtual environment when you're done:
```bash
deactivate
```

## Quick Start Guide

This section shows you how to quickly set up and test the Google Drive MCP server with service account authentication.

### 1. Prerequisites Setup

**Download Service Account Credentials:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Drive API
4. Create a Service Account and download the JSON key file
5. Save it as `/opt/mycode/aws-mcp/src/gdrive-mcp-server/service-account.json`

**Create a Test Folder in Google Drive:**
1. Open [Google Drive](https://drive.google.com)
2. Create a new folder called "MCP-Test"
3. Share this folder with your service account email (found in the JSON file)
4. Give it "Editor" permissions
5. Copy the folder ID from the URL (e.g., `https://drive.google.com/drive/folders/1ABC...XYZ`)

### 2. Environment Setup

```bash
cd /opt/mycode/aws-mcp/src/gdrive-mcp-server

# Activate virtual environment
source .venv/bin/activate

# Set environment variable for service account
export GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"

# Set your test folder ID (replace with your actual folder ID)
export GDRIVE_TEST_FOLDER_ID="1ABC123DEF456GHI789JKL"
```

### 3. Test Server Configuration

```bash
# Test server configuration
awslabs.gdrive-mcp-server --test
```

### 4. Start the Server

```bash
# Start the MCP server (runs silently, waiting for MCP client connections)
awslabs.gdrive-mcp-server
```

**Note**: The server runs silently and waits for MCP client connections. It's designed to be used by AI assistants or MCP clients, not as a standalone application.

### 5. Run the Test Script

Now run the provided test script to verify all operations work:

```bash
# Run the test script (it's already created for you)
python test_gdrive.py
```

The test script will:
- ✅ Check for your credentials file
- ✅ Authenticate with Google Drive
- ✅ List files in your test folder
- ✅ Create a new test file (`mcp-test.txt`)
- ✅ Read the file back
- ✅ Search for the created file

### 6. Expected Output

You should see output like this:

```
🧪 Google Drive MCP Server Test Script
==================================================
📁 Using test folder ID: 1ABC123DEF456GHI789JKL
🔑 Using credentials: ./service-account.json

🔐 Testing authentication...
✅ Authenticated as: your-service-account@your-project.iam.gserviceaccount.com

📁 Testing list files...
✅ Found 0 files and 0 folders

✍️ Testing write file...
✅ Created file: 1XYZ789ABC123DEF456GHI
   File URL: https://drive.google.com/file/d/1XYZ789ABC123DEF456GHI/view

📖 Testing read file...
✅ Read file content: Hello from Google Drive MCP Server!...
   File size: 123 characters
   Content type: text/plain

🔍 Testing search files...
✅ Search found 1 files
   - mcp-test.txt (1XYZ789ABC123DEF456GHI)

🎉 All tests completed successfully!
   Check your Google Drive folder: https://drive.google.com/drive/folders/1ABC123DEF456GHI789JKL
```

### 7. Verify in Google Drive

1. Go to your "MCP-Test" folder in Google Drive
2. You should see the `mcp-test.txt` file
3. Open it to verify the content was written correctly

## How MCP Clients Use the Server

**Note**: The test script above calls the server functions directly. In real usage, AI assistants and MCP clients communicate with the server using the MCP protocol. Here are examples of how they would interact:

**Authentication:**
```json
{
  "tool": "AuthenticateServiceAccount",
  "parameters": {
    "credentials_path": "./service-account.json"
  }
}
```

**List Files:**
```json
{
  "tool": "ListFiles",
  "parameters": {
    "folder_id": "YOUR_TEST_FOLDER_ID",
    "max_results": 10
  }
}
```

**Write File:**
```json
{
  "tool": "WriteFile",
  "parameters": {
    "name": "document.txt",
    "content": "Hello from AI assistant!",
    "parent_folder_id": "YOUR_TEST_FOLDER_ID"
  }
}
```

These JSON examples show the MCP protocol format - they're not meant to be run directly as Python code.

## Configuration

### Google Drive API Setup

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Drive API

2. **Create Credentials**:
   ```bash
   # For service account (recommended for server usage)
   # Download the service account JSON file
   
   # For OAuth2 (interactive usage)
   # Download the OAuth2 client credentials JSON file
   ```

3. **Set Environment Variables**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
   # OR for OAuth2
   export GDRIVE_CLIENT_CREDENTIALS="/path/to/client-credentials.json"
   export GDRIVE_TOKEN_FILE="/path/to/token.json"
   ```

## Usage

### Starting the Server

```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # On Linux/macOS
# or .venv\Scripts\activate on Windows

# Using the installed script
awslabs.gdrive-mcp-server

# Or using Python module
python -m awslabs.gdrive_mcp_server.server
```

### MCP Tools Available

#### File Operations
- `ReadFile`: Read file contents from Google Drive
- `WriteFile`: Create or update files in Google Drive
- `DeleteFile`: Remove files from Google Drive
- `CopyFile`: Copy files within Google Drive
- `MoveFile`: Move files between folders

#### Search and Discovery
- `SearchFiles`: Advanced file search with filters
- `ListFiles`: List files in folders with pagination
- `SearchContent`: Full-text search within file contents
- `FindByMetadata`: Search files by metadata attributes

#### Folder Management
- `CreateFolder`: Create new folders
- `ListFolders`: Browse folder hierarchies
- `ManageFolderStructure`: Organize folder layouts

#### Metadata and Properties
- `GetFileMetadata`: Retrieve detailed file information
- `UpdateFileMetadata`: Modify file properties
- `ManagePermissions`: Handle file sharing and access

## Examples

### Reading a File
```python
# Read a Google Doc
result = await read_file(
    file_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    export_format="text/plain"
)
print(result.content)
```

### Searching Files
```python
# Search for files by name and type
results = await search_files(
    query="project proposal",
    file_types=["application/vnd.google-apps.document"],
    limit=10
)
for file in results.files:
    print(f"{file.name}: {file.id}")
```

### Writing a File
```python
# Create a new document
result = await write_file(
    name="Meeting Notes.txt",
    content="Meeting notes for project discussion...",
    parent_folder_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    mime_type="text/plain"
)
print(f"Created file: {result.file_id}")
```

## Development

### Project Structure
```
gdrive-mcp-server/
├── awslabs/
│   └── gdrive_mcp_server/
│       ├── __init__.py
│       ├── server.py              # Main MCP server
│       ├── models/                # Pydantic data models
│       ├── impl/                  # Implementation modules
│       │   ├── tools/             # Tool implementations
│       │   ├── auth/              # Authentication handling
│       │   └── utils/             # Utility functions
│       └── static/                # Documentation and constants
├── tests/                         # Test suite
├── pyproject.toml                 # Project configuration
└── README.md                      # This file
```

### Running Tests
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # On Linux/macOS
# or .venv\Scripts\activate on Windows

pytest tests/
```

### Code Formatting
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # On Linux/macOS
# or .venv\Scripts\activate on Windows

ruff format .
ruff check .
```

## Authentication Methods

### Service Account (Recommended)
- Best for server-side applications
- No user interaction required
- Requires service account JSON file

### OAuth2 Flow
- Interactive authentication
- Supports user-specific access
- Requires web browser for initial setup

## Error Handling

The server provides comprehensive error handling for:
- Authentication failures
- API rate limiting
- Network connectivity issues
- Invalid file operations
- Permission denied scenarios

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

Licensed under the Apache License, Version 2.0. See LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in the `static/` directory
- Review the examples in the `tests/` directory 