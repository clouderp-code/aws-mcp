#!/usr/bin/env python3
"""Test script for Google Drive MCP Server."""

import os
import asyncio
from awslabs.gdrive_mcp_server.impl.auth import authenticate_service_account
from awslabs.gdrive_mcp_server.impl.tools import (
    list_files_impl, write_file_impl, read_file_impl, search_files_impl
)
from awslabs.gdrive_mcp_server.models import (
    ListFilesRequest, WriteFileRequest, ReadFileRequest, SearchFilesRequest
)

async def test_operations():
    """Test basic Google Drive operations."""
    
    print("🧪 Google Drive MCP Server Test Script")
    print("=" * 50)
    
    # Check credentials file
    creds_file = "./service-account.json"
    if not os.path.exists(creds_file):
        print(f"❌ Credentials file not found: {creds_file}")
        print("   Please download your service account JSON file and save it as 'service-account.json'")
        return
    
    # Get folder ID from environment
    folder_id = os.environ.get('GDRIVE_TEST_FOLDER_ID')
    if not folder_id:
        print("❌ Please set GDRIVE_TEST_FOLDER_ID environment variable")
        print("   Example: export GDRIVE_TEST_FOLDER_ID='1ABC123DEF456GHI789JKL'")
        print("   (Get this from your Google Drive folder URL)")
        return
    
    print(f"📁 Using test folder ID: {folder_id}")
    print(f"🔑 Using credentials: {creds_file}")
    print()
    
    print("🔐 Testing authentication...")
    auth_result = await authenticate_service_account()
    if not auth_result.success:
        print(f"❌ Authentication failed: {auth_result.message}")
        print("   Check your service account JSON file and permissions")
        return
    print(f"✅ Authenticated as: {auth_result.user_email}")
    
    print("\n📁 Testing list files...")
    list_result = await list_files_impl(ListFilesRequest(folder_id=folder_id))
    if list_result.success:
        print(f"✅ Found {len(list_result.files)} files and {len(list_result.folders)} folders")
        if list_result.files:
            print("   Files found:")
            for file in list_result.files[:3]:  # Show first 3 files
                print(f"   - {file.name} ({file.mime_type})")
    else:
        print(f"❌ List files failed: {list_result.message}")
        print("   Check that the folder ID is correct and shared with your service account")
        return
    
    print("\n✍️ Testing write file...")
    test_content = f"Hello from Google Drive MCP Server!\n\nThis is a test file created at {asyncio.get_event_loop().time()}\n\nThe MCP server is working correctly!"
    write_result = await write_file_impl(WriteFileRequest(
        name="mcp-test.txt",
        content=test_content,
        parent_folder_id=folder_id,
        description="Test file created by MCP server test script"
    ))
    if write_result.success:
        print(f"✅ Created file: {write_result.file_id}")
        print(f"   File URL: {write_result.file_url}")
        file_id = write_result.file_id
    else:
        print(f"❌ Write file failed: {write_result.message}")
        return
    
    print("\n📖 Testing read file...")
    read_result = await read_file_impl(ReadFileRequest(
        file_id=file_id,
        include_metadata=True
    ))
    if read_result.success:
        content_preview = read_result.content[:60] + "..." if len(read_result.content) > 60 else read_result.content
        print(f"✅ Read file content: {content_preview}")
        print(f"   File size: {len(read_result.content)} characters")
        print(f"   Content type: {read_result.content_type}")
    else:
        print(f"❌ Read file failed: {read_result.message}")
    
    print("\n🔍 Testing search files...")
    search_result = await search_files_impl(SearchFilesRequest(
        query="mcp-test",
        folder_id=folder_id
    ))
    if search_result.success:
        print(f"✅ Search found {len(search_result.files)} files")
        for file in search_result.files:
            print(f"   - {file.name} ({file.id})")
    else:
        print(f"❌ Search failed: {search_result.message}")
    
    print("\n🎉 All tests completed successfully!")
    print(f"   Check your Google Drive folder: https://drive.google.com/drive/folders/{folder_id}")
    print("   You should see the 'mcp-test.txt' file created by this test.")

if __name__ == "__main__":
    asyncio.run(test_operations()) 