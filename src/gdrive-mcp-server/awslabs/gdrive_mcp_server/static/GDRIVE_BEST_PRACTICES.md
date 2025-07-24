# Google Drive MCP Server Best Practices

This document outlines best practices for using the Google Drive MCP server effectively and securely.

## Authentication Best Practices

### Service Account vs OAuth2

**Use Service Account when:**
- Building server-side applications
- Need non-interactive access
- Working with shared/organizational data
- Requiring consistent access without user intervention

**Use OAuth2 when:**
- Building user-facing applications
- Need access to personal Google Drive
- Want granular permission control
- User consent is required

### Credential Management

1. **Never hardcode credentials** in your source code
2. **Use environment variables** for credential paths
3. **Store credentials securely** outside of your project directory
4. **Rotate credentials regularly** as part of security hygiene
5. **Use least privilege** - request only necessary scopes

## File Operations Best Practices

### Reading Files

```python
# Good: Handle encoding properly
result = await read_file_impl(ReadFileRequest(
    file_id="your_file_id",
    export_format="text/plain",  # Specify format for Google Workspace files
    encoding="utf-8",
    include_metadata=True  # Get metadata when needed
))

# Check success before using content
if result.success:
    process_content(result.content)
else:
    handle_error(result.message)
```

### Writing Files

```python
# Good: Specify MIME type and organize properly
result = await write_file_impl(WriteFileRequest(
    name="report.txt",
    content="Your content here",
    mime_type="text/plain",
    parent_folder_id="folder_id",  # Organize in folders
    description="Generated report from analysis"
))
```

### File Organization

1. **Use descriptive names** with proper extensions
2. **Organize in folder hierarchies** rather than dumping in root
3. **Set appropriate descriptions** for better searchability
4. **Use custom properties** for metadata and tagging

## Search Best Practices

### Efficient Searching

```python
# Good: Use specific queries and filters
result = await search_files_impl(SearchFilesRequest(
    query="meeting notes",
    file_types=["text/plain", "application/vnd.google-apps.document"],
    folder_id="specific_folder_id",  # Limit scope
    max_results=50,  # Reasonable limit
    order_by="modifiedTime desc"  # Most recent first
))
```

### Search Optimization

1. **Be specific** in search queries
2. **Use MIME type filters** to narrow results
3. **Search within specific folders** when possible
4. **Limit result count** to avoid overwhelming responses
5. **Use pagination** for large result sets

## Error Handling

### Robust Error Handling

```python
async def safe_file_operation(file_id: str):
    try:
        result = await read_file_impl(ReadFileRequest(file_id=file_id))
        
        if not result.success:
            if "not found" in result.message.lower():
                # Handle file not found
                logger.warning(f"File {file_id} not found")
                return None
            elif "permission" in result.message.lower():
                # Handle permission denied
                logger.error(f"Access denied to file {file_id}")
                return None
            else:
                # Handle other errors
                logger.error(f"Error reading file {file_id}: {result.message}")
                return None
        
        return result.content
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
```

### Common Error Scenarios

1. **Authentication expired** - Implement token refresh
2. **Rate limiting** - Implement exponential backoff
3. **Network issues** - Add retry logic
4. **File not found** - Validate file IDs before operations
5. **Permission denied** - Check sharing settings

## Performance Optimization

### Batch Operations

```python
# Good: Batch similar operations
async def process_multiple_files(file_ids: List[str]):
    tasks = []
    for file_id in file_ids:
        task = read_file_impl(ReadFileRequest(file_id=file_id))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### Caching Strategy

1. **Cache file metadata** for frequently accessed files
2. **Cache folder listings** to reduce API calls
3. **Implement TTL** for cached data
4. **Use file modification time** to invalidate cache

### API Quota Management

1. **Monitor quota usage** in Google Cloud Console
2. **Implement rate limiting** in your application
3. **Use exponential backoff** for rate limit errors
4. **Batch requests** when possible

## Security Considerations

### Data Protection

1. **Encrypt sensitive data** before uploading
2. **Use secure connections** (HTTPS only)
3. **Validate file types** before processing
4. **Sanitize file names** to prevent path traversal

### Access Control

1. **Principle of least privilege** - minimal necessary permissions
2. **Regular access reviews** - audit file permissions
3. **Secure credential storage** - use proper secret management
4. **Log access patterns** for security monitoring

### Privacy Compliance

1. **Data minimization** - only access necessary data
2. **Retention policies** - delete data when no longer needed
3. **User consent** - ensure proper authorization
4. **Audit trails** - maintain logs of data access

## Monitoring and Logging

### Comprehensive Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def logged_file_operation(file_id: str):
    logger.info(f"Starting file operation for {file_id}")
    
    try:
        result = await read_file_impl(ReadFileRequest(file_id=file_id))
        
        if result.success:
            logger.info(f"Successfully read file {file_id}")
        else:
            logger.error(f"Failed to read file {file_id}: {result.message}")
        
        return result
        
    except Exception as e:
        logger.exception(f"Exception reading file {file_id}")
        raise
```

### Metrics to Track

1. **API call frequency** and patterns
2. **Error rates** by operation type
3. **Response times** for different operations
4. **Quota usage** and remaining limits
5. **File size** and transfer volumes

## Testing Strategies

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_read_file_success():
    # Mock the Google Drive service
    with patch('awslabs.gdrive_mcp_server.impl.auth.get_authenticated_service') as mock_service:
        mock_service.return_value = AsyncMock()
        
        # Test file reading
        result = await read_file_impl(ReadFileRequest(file_id="test_id"))
        
        assert result.success
        assert result.content is not None
```

### Integration Testing

1. **Test with real API** using test credentials
2. **Create test files** for consistent testing
3. **Clean up test data** after tests
4. **Test error scenarios** with invalid inputs

## Deployment Considerations

### Production Deployment

1. **Environment separation** - dev/staging/prod
2. **Configuration management** - externalize settings
3. **Health checks** - monitor service status
4. **Graceful degradation** - fallback mechanisms

### Scaling Considerations

1. **Connection pooling** for API clients
2. **Load balancing** for multiple instances
3. **Circuit breakers** for external API calls
4. **Async processing** for heavy operations

## Troubleshooting Guide

### Common Issues

1. **Authentication failures**
   - Check credential files and paths
   - Verify API enabled in Google Cloud Console
   - Ensure proper permissions

2. **File access errors**
   - Verify file sharing settings
   - Check file ownership
   - Confirm user permissions

3. **API rate limits**
   - Implement exponential backoff
   - Check quota settings
   - Consider request batching

4. **Large file handling**
   - Use resumable uploads for large files
   - Implement progress tracking
   - Handle timeout scenarios

### Debug Tools

1. **Enable debug logging** for detailed output
2. **Use API explorer** for manual testing
3. **Monitor network traffic** for API calls
4. **Test with minimal examples** to isolate issues 