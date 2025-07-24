# Google Drive API Setup Guide

This guide walks you through setting up Google Drive API access for the MCP server.

## Prerequisites

- Google account
- Access to Google Cloud Console
- Python 3.10 or higher

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter a project name (e.g., "gdrive-mcp-server")
4. Click **Create**

## Step 2: Enable Google Drive API

1. In the Google Cloud Console, navigate to **APIs & Services** → **Library**
2. Search for "Google Drive API"
3. Click on **Google Drive API**
4. Click **Enable**

## Step 3: Create Credentials

### Option A: Service Account (Recommended for Server Use)

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Enter service account details:
   - Name: "gdrive-mcp-service"
   - Description: "Service account for Google Drive MCP server"
4. Click **Create and Continue**
5. Skip role assignment (click **Continue**)
6. Click **Done**

#### Download Service Account Key

1. Click on the created service account
2. Go to the **Keys** tab
3. Click **Add Key** → **Create new key**
4. Select **JSON** format
5. Click **Create**
6. Save the downloaded JSON file securely

#### Configure Service Account Access

Since service accounts don't have access to personal Google Drive by default, you need to:

1. Share specific folders/files with the service account email
2. OR use domain-wide delegation (for Google Workspace domains)

### Option B: OAuth2 (For Interactive Use)

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External** (for personal accounts) or **Internal** (for organization)
   - Fill in required application information
4. For Application type, select **Desktop application**
5. Enter a name: "gdrive-mcp-client"
6. Click **Create**
7. Download the client configuration JSON file

## Step 4: Set Environment Variables

### For Service Account

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

### For OAuth2

```bash
export GDRIVE_CLIENT_CREDENTIALS="/path/to/your/client-credentials.json"
export GDRIVE_TOKEN_FILE="/path/to/store/token.json"
```

## Step 5: Install Dependencies

```bash
cd /opt/mycode/aws-mcp/src/gdrive-mcp-server
pip install -e .
```

## Step 6: Test Authentication

### Service Account Test

```python
from awslabs.gdrive_mcp_server.impl.auth import authenticate_service_account

# Test service account authentication
result = await authenticate_service_account()
print(f"Authentication result: {result.message}")
```

### OAuth2 Test

```python
from awslabs.gdrive_mcp_server.impl.auth import authenticate_oauth2

# Test OAuth2 authentication (will open browser)
result = await authenticate_oauth2()
print(f"Authentication result: {result.message}")
```

## Step 7: Verify Access

Test basic file listing:

```python
from awslabs.gdrive_mcp_server.impl.tools import list_files_impl
from awslabs.gdrive_mcp_server.models import ListFilesRequest

# List files in root folder
request = ListFilesRequest(max_results=10)
result = await list_files_impl(request)

if result.success:
    print(f"Found {len(result.files)} files")
    for file in result.files:
        print(f"- {file.name} ({file.id})")
else:
    print(f"Error: {result.message}")
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify credentials file path and format
   - Check that the Google Drive API is enabled
   - Ensure service account has access to target files/folders

2. **Permission Denied**
   - For service accounts: Share folders/files with service account email
   - For OAuth2: Ensure user has granted necessary permissions

3. **API Quota Exceeded**
   - Check quotas in Google Cloud Console
   - Implement rate limiting in your application

4. **File Not Found**
   - Verify file IDs are correct
   - Check that files are not in trash
   - Ensure authenticated user has access

### Useful Resources

- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [Python Client Library](https://github.com/googleapis/google-api-python-client)
- [OAuth2 Scopes](https://developers.google.com/identity/protocols/oauth2/scopes#drive)

## Security Considerations

1. **Credential Security**
   - Never commit credentials to version control
   - Use environment variables or secure credential storage
   - Rotate credentials regularly

2. **Access Control**
   - Use least privilege principle
   - Regularly review API quotas and usage
   - Monitor for unusual activity

3. **Data Privacy**
   - Respect user data and privacy
   - Implement proper data handling procedures
   - Consider data retention policies

## Next Steps

Once authentication is working:

1. Start the MCP server: `awslabs.gdrive-mcp-server`
2. Test the available tools
3. Integrate with your AI assistant or application
4. Implement error handling and logging
5. Consider implementing caching for better performance 