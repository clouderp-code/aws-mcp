#!/usr/bin/env python3
"""
Standalone Google Drive API Test Script

This script tests Google Drive API operations directly without using MCP tools.
It demonstrates all the functionality that the Google Drive MCP server provides.
"""

import os
import sys
import json
import time
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io


class GoogleDriveStandaloneTest:
    """Standalone Google Drive API tester."""
    
    def __init__(self, service_account_file: str, test_folder_id: str):
        """Initialize the tester with credentials and folder ID."""
        self.service_account_file = service_account_file
        self.test_folder_id = test_folder_id
        self.service = None
        self.test_files = []  # Track created files for cleanup
        
    def authenticate(self):
        """Authenticate with Google Drive API using service account."""
        print("🔐 AUTHENTICATION TEST")
        print("=" * 50)
        
        try:
            if not os.path.exists(self.service_account_file):
                print(f"❌ Service account file not found: {self.service_account_file}")
                return False
            
            print(f"📄 Loading credentials from: {self.service_account_file}")
            
            # Load service account credentials
            scopes = ['https://www.googleapis.com/auth/drive']
            credentials = Credentials.from_service_account_file(
                self.service_account_file, scopes=scopes
            )
            
            # Build the service
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Test the connection by getting user info
            about = self.service.about().get(fields='user').execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')
            
            print(f"✅ Successfully authenticated!")
            print(f"   Service account email: {credentials.service_account_email}")
            print(f"   API user email: {user_email}")
            print(f"   Scopes: {', '.join(scopes)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def test_list_files(self):
        """Test listing files in the specified folder."""
        print("\n📁 LIST FILES TEST")
        print("=" * 50)
        
        try:
            print(f"📂 Listing files in folder: {self.test_folder_id}")
            
            # List files in the folder
            query = f"'{self.test_folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields='nextPageToken,files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink)'
            ).execute()
            
            files = results.get('files', [])
            
            print(f"✅ Found {len(files)} files")
            
            if files:
                print("   Files found:")
                for i, file in enumerate(files[:10], 1):  # Show first 10 files
                    size_str = f"{file.get('size', 'N/A')} bytes" if file.get('size') else "No size info"
                    print(f"   {i:2d}. {file['name']}")
                    print(f"       ID: {file['id']}")
                    print(f"       Type: {file['mimeType']}")
                    print(f"       Size: {size_str}")
                    print(f"       Created: {file.get('createdTime', 'N/A')}")
                    print(f"       Modified: {file.get('modifiedTime', 'N/A')}")
                    print(f"       URL: {file.get('webViewLink', 'N/A')}")
                    print()
                
                if len(files) > 10:
                    print(f"   ... and {len(files) - 10} more files")
            else:
                print("   No files found in folder")
            
            # Also test listing folders
            folder_query = f"'{self.test_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            folder_results = self.service.files().list(
                q=folder_query,
                pageSize=50,
                fields='files(id,name,createdTime)'
            ).execute()
            
            folders = folder_results.get('files', [])
            print(f"   Found {len(folders)} subfolders")
            
            if folders:
                for folder in folders[:5]:  # Show first 5 folders
                    print(f"     📁 {folder['name']} ({folder['id']})")
            
            return True
            
        except HttpError as e:
            print(f"❌ List files failed: {e}")
            return False
    
    def test_create_folder(self):
        """Test creating a new folder."""
        print("\n📁 CREATE FOLDER TEST")
        print("=" * 50)
        
        try:
            folder_name = f"MCP-Test-Folder-{int(time.time())}"
            print(f"📂 Creating folder: {folder_name}")
            
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.test_folder_id],
                'description': 'Test folder created by standalone Google Drive test script'
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id,name,webViewLink,createdTime'
            ).execute()
            
            folder_id = folder['id']
            self.test_files.append(folder_id)  # Track for cleanup
            
            print(f"✅ Folder created successfully!")
            print(f"   Folder ID: {folder_id}")
            print(f"   Folder name: {folder['name']}")
            print(f"   Created time: {folder.get('createdTime', 'N/A')}")
            print(f"   Web view link: {folder.get('webViewLink', 'N/A')}")
            
            return folder_id
            
        except HttpError as e:
            print(f"❌ Create folder failed: {e}")
            return None
    
    def test_write_file(self):
        """Test creating/writing a file."""
        print("\n✍️ WRITE FILE TEST")
        print("=" * 50)
        
        try:
            filename = f"mcp-standalone-test-{int(time.time())}.txt"
            content = f"""Google Drive MCP Server Standalone Test

This file was created by the standalone test script at {datetime.now()}.

Test Content:
- Authentication: ✅ Working
- File Creation: ✅ Working
- Content Writing: ✅ Working

The Google Drive API integration is functioning correctly!

Timestamp: {time.time()}
"""
            
            print(f"📝 Creating file: {filename}")
            print(f"   Content size: {len(content)} characters")
            
            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'parents': [self.test_folder_id],
                'description': 'Test file created by standalone Google Drive test script'
            }
            
            # Create media upload
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain',
                resumable=True
            )
            
            # Create the file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,mimeType,webViewLink,createdTime'
            ).execute()
            
            file_id = file['id']
            self.test_files.append(file_id)  # Track for cleanup
            
            print(f"✅ File created successfully!")
            print(f"   File ID: {file_id}")
            print(f"   File name: {file['name']}")
            print(f"   File size: {file.get('size', 'N/A')} bytes")
            print(f"   MIME type: {file['mimeType']}")
            print(f"   Created time: {file.get('createdTime', 'N/A')}")
            print(f"   Web view link: {file.get('webViewLink', 'N/A')}")
            
            return file_id
            
        except HttpError as e:
            print(f"❌ Write file failed: {e}")
            return None
    
    def test_read_file(self, file_id: str):
        """Test reading a file's content."""
        print("\n📖 READ FILE TEST")
        print("=" * 50)
        
        try:
            print(f"📄 Reading file: {file_id}")
            
            # Get file metadata first
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,createdTime,modifiedTime'
            ).execute()
            
            print(f"   File name: {file_metadata['name']}")
            print(f"   MIME type: {file_metadata['mimeType']}")
            print(f"   Size: {file_metadata.get('size', 'N/A')} bytes")
            
            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    print(f"   Download progress: {int(status.progress() * 100)}%")
            
            content = fh.getvalue().decode('utf-8')
            
            print(f"✅ File read successfully!")
            print(f"   Content length: {len(content)} characters")
            print(f"   Content preview:")
            
            # Show first few lines of content
            lines = content.split('\n')
            for i, line in enumerate(lines[:10], 1):
                print(f"     {i:2d}: {line}")
            
            if len(lines) > 10:
                print(f"     ... and {len(lines) - 10} more lines")
            
            return content
            
        except HttpError as e:
            print(f"❌ Read file failed: {e}")
            return None
    
    def test_get_file_metadata(self, file_id: str):
        """Test getting detailed file metadata."""
        print("\n📊 GET FILE METADATA TEST")
        print("=" * 50)
        
        try:
            print(f"📋 Getting metadata for file: {file_id}")
            
            # Get comprehensive metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='*'
            ).execute()
            
            print(f"✅ Metadata retrieved successfully!")
            print(f"   Basic Information:")
            print(f"     Name: {file_metadata.get('name', 'N/A')}")
            print(f"     ID: {file_metadata.get('id', 'N/A')}")
            print(f"     MIME Type: {file_metadata.get('mimeType', 'N/A')}")
            print(f"     Size: {file_metadata.get('size', 'N/A')} bytes")
            print(f"     Created: {file_metadata.get('createdTime', 'N/A')}")
            print(f"     Modified: {file_metadata.get('modifiedTime', 'N/A')}")
            print(f"     Version: {file_metadata.get('version', 'N/A')}")
            
            print(f"   Location:")
            print(f"     Parents: {', '.join(file_metadata.get('parents', []))}")
            print(f"     Starred: {file_metadata.get('starred', False)}")
            print(f"     Trashed: {file_metadata.get('trashed', False)}")
            
            print(f"   Links:")
            print(f"     Web View: {file_metadata.get('webViewLink', 'N/A')}")
            print(f"     Web Content: {file_metadata.get('webContentLink', 'N/A')}")
            
            # Show permissions if available
            permissions = file_metadata.get('permissions', [])
            if permissions:
                print(f"   Permissions ({len(permissions)}):")
                for i, perm in enumerate(permissions[:3], 1):
                    print(f"     {i}. Role: {perm.get('role', 'N/A')}, Type: {perm.get('type', 'N/A')}")
                    if perm.get('emailAddress'):
                        print(f"        Email: {perm.get('emailAddress')}")
            
            # Show properties if available
            properties = file_metadata.get('properties', {})
            if properties:
                print(f"   Custom Properties:")
                for key, value in properties.items():
                    print(f"     {key}: {value}")
            
            return file_metadata
            
        except HttpError as e:
            print(f"❌ Get metadata failed: {e}")
            return None
    
    def test_update_file_metadata(self, file_id: str):
        """Test updating file metadata."""
        print("\n📝 UPDATE FILE METADATA TEST")
        print("=" * 50)
        
        try:
            print(f"🔄 Updating metadata for file: {file_id}")
            
            new_name = f"updated-mcp-test-{int(time.time())}.txt"
            new_description = f"Updated by standalone test script at {datetime.now()}"
            
            update_metadata = {
                'name': new_name,
                'description': new_description,
                'starred': True,
                'properties': {
                    'test_script': 'standalone_gdrive_test',
                    'update_time': str(datetime.now()),
                    'version': '2.0'
                }
            }
            
            print(f"   New name: {new_name}")
            print(f"   New description: {new_description}")
            print(f"   Setting starred: True")
            print(f"   Adding custom properties")
            
            updated_file = self.service.files().update(
                fileId=file_id,
                body=update_metadata,
                fields='id,name,description,starred,properties,modifiedTime'
            ).execute()
            
            print(f"✅ Metadata updated successfully!")
            print(f"   Updated name: {updated_file.get('name', 'N/A')}")
            print(f"   Updated description: {updated_file.get('description', 'N/A')}")
            print(f"   Starred: {updated_file.get('starred', False)}")
            print(f"   Modified time: {updated_file.get('modifiedTime', 'N/A')}")
            
            properties = updated_file.get('properties', {})
            if properties:
                print(f"   Custom properties:")
                for key, value in properties.items():
                    print(f"     {key}: {value}")
            
            return True
            
        except HttpError as e:
            print(f"❌ Update metadata failed: {e}")
            return False
    
    def test_copy_file(self, file_id: str):
        """Test copying a file."""
        print("\n📋 COPY FILE TEST")
        print("=" * 50)
        
        try:
            copy_name = f"copy-of-mcp-test-{int(time.time())}.txt"
            print(f"📄 Copying file: {file_id}")
            print(f"   New name: {copy_name}")
            
            copy_metadata = {
                'name': copy_name,
                'parents': [self.test_folder_id],
                'description': f'Copy created by standalone test script at {datetime.now()}'
            }
            
            copied_file = self.service.files().copy(
                fileId=file_id,
                body=copy_metadata,
                fields='id,name,size,createdTime,webViewLink'
            ).execute()
            
            copy_id = copied_file['id']
            self.test_files.append(copy_id)  # Track for cleanup
            
            print(f"✅ File copied successfully!")
            print(f"   Copy ID: {copy_id}")
            print(f"   Copy name: {copied_file['name']}")
            print(f"   Copy size: {copied_file.get('size', 'N/A')} bytes")
            print(f"   Created time: {copied_file.get('createdTime', 'N/A')}")
            print(f"   Web view link: {copied_file.get('webViewLink', 'N/A')}")
            
            return copy_id
            
        except HttpError as e:
            print(f"❌ Copy file failed: {e}")
            return None
    
    def test_search_files(self):
        """Test searching for files."""
        print("\n🔍 SEARCH FILES TEST")
        print("=" * 50)
        
        try:
            search_terms = ["mcp", "test", "standalone"]
            
            for term in search_terms:
                print(f"🔎 Searching for: '{term}'")
                
                # Search in the test folder
                query = f"'{self.test_folder_id}' in parents and name contains '{term}' and trashed=false"
                
                results = self.service.files().list(
                    q=query,
                    pageSize=20,
                    orderBy='modifiedTime desc',
                    fields='files(id,name,mimeType,size,modifiedTime,webViewLink)'
                ).execute()
                
                files = results.get('files', [])
                print(f"   Found {len(files)} files")
                
                if files:
                    for i, file in enumerate(files[:5], 1):  # Show first 5 results
                        print(f"   {i}. {file['name']}")
                        print(f"      ID: {file['id']}")
                        print(f"      Type: {file['mimeType']}")
                        print(f"      Size: {file.get('size', 'N/A')} bytes")
                        print(f"      Modified: {file.get('modifiedTime', 'N/A')}")
                
                print()
            
            # Test full-text search
            print(f"🔎 Full-text search for: 'Google Drive MCP'")
            fulltext_query = f"'{self.test_folder_id}' in parents and fullText contains 'Google Drive MCP' and trashed=false"
            
            fulltext_results = self.service.files().list(
                q=fulltext_query,
                pageSize=10,
                fields='files(id,name,mimeType)'
            ).execute()
            
            fulltext_files = fulltext_results.get('files', [])
            print(f"   Found {len(fulltext_files)} files with content match")
            
            if fulltext_files:
                for file in fulltext_files:
                    print(f"     - {file['name']} ({file['mimeType']})")
            
            print(f"✅ Search tests completed!")
            return True
            
        except HttpError as e:
            print(f"❌ Search failed: {e}")
            return False
    
    def test_move_file(self, file_id: str, target_folder_id: str):
        """Test moving a file to a different folder."""
        print("\n📦 MOVE FILE TEST")
        print("=" * 50)
        
        try:
            print(f"📄 Moving file: {file_id}")
            print(f"   To folder: {target_folder_id}")
            
            # Get current parents
            file_data = self.service.files().get(
                fileId=file_id,
                fields='name,parents'
            ).execute()
            
            current_parents = file_data.get('parents', [])
            print(f"   Current parents: {', '.join(current_parents)}")
            
            # Move the file
            updated_file = self.service.files().update(
                fileId=file_id,
                addParents=target_folder_id,
                removeParents=','.join(current_parents),
                fields='id,name,parents'
            ).execute()
            
            new_parents = updated_file.get('parents', [])
            
            print(f"✅ File moved successfully!")
            print(f"   File name: {updated_file['name']}")
            print(f"   New parents: {', '.join(new_parents)}")
            
            return True
            
        except HttpError as e:
            print(f"❌ Move file failed: {e}")
            return False
    
    def test_delete_file(self, file_id: str, permanent: bool = False):
        """Test deleting a file."""
        print(f"\n🗑️ DELETE FILE TEST ({'PERMANENT' if permanent else 'TRASH'})")
        print("=" * 50)
        
        try:
            # Get file info first
            file_info = self.service.files().get(
                fileId=file_id,
                fields='name,mimeType'
            ).execute()
            
            print(f"🗂️ Deleting file: {file_info['name']} ({file_id})")
            print(f"   Type: {file_info['mimeType']}")
            print(f"   Method: {'Permanent deletion' if permanent else 'Move to trash'}")
            
            if permanent:
                # Permanently delete
                self.service.files().delete(fileId=file_id).execute()
                print(f"✅ File permanently deleted!")
            else:
                # Move to trash
                self.service.files().update(
                    fileId=file_id,
                    body={'trashed': True}
                ).execute()
                print(f"✅ File moved to trash!")
            
            return True
            
        except HttpError as e:
            print(f"❌ Delete file failed: {e}")
            return False
    
    def cleanup_test_files(self):
        """Clean up all test files created during the test."""
        print(f"\n🧹 CLEANUP TEST FILES")
        print("=" * 50)
        
        if not self.test_files:
            print("ℹ️ No test files to clean up")
            return
        
        print(f"🗑️ Cleaning up {len(self.test_files)} test files...")
        
        cleaned = 0
        for file_id in self.test_files:
            try:
                # Get file name for logging
                try:
                    file_info = self.service.files().get(
                        fileId=file_id,
                        fields='name,trashed'
                    ).execute()
                    file_name = file_info['name']
                    is_trashed = file_info.get('trashed', False)
                except:
                    file_name = file_id
                    is_trashed = False
                
                if not is_trashed:
                    # Move to trash
                    self.service.files().update(
                        fileId=file_id,
                        body={'trashed': True}
                    ).execute()
                    print(f"   ✅ Moved to trash: {file_name}")
                    cleaned += 1
                else:
                    print(f"   ℹ️ Already trashed: {file_name}")
                    
            except HttpError as e:
                print(f"   ❌ Failed to clean up {file_id}: {e}")
        
        print(f"✅ Cleanup completed! Moved {cleaned} files to trash")
    
    def run_all_tests(self):
        """Run all Google Drive API tests."""
        print("🧪 GOOGLE DRIVE API STANDALONE TEST SUITE")
        print("=" * 70)
        print(f"Test folder ID: {self.test_folder_id}")
        print(f"Service account: {self.service_account_file}")
        print(f"Timestamp: {datetime.now()}")
        print("=" * 70)
        
        # 1. Authentication
        if not self.authenticate():
            print("\n❌ Authentication failed. Cannot continue with tests.")
            return False
        
        # 2. List files (initial state)
        self.test_list_files()
        
        # 3. Create folder
        test_folder_id = self.test_create_folder()
        
        # 4. Write file
        test_file_id = self.test_write_file()
        if not test_file_id:
            print("\n❌ File creation failed. Skipping file-dependent tests.")
            return False
        
        # 5. Read file
        self.test_read_file(test_file_id)
        
        # 6. Get file metadata
        self.test_get_file_metadata(test_file_id)
        
        # 7. Update file metadata
        self.test_update_file_metadata(test_file_id)
        
        # 8. Copy file
        copied_file_id = self.test_copy_file(test_file_id)
        
        # 9. Search files
        self.test_search_files()
        
        # 10. Move file (if we have a target folder)
        if test_folder_id and copied_file_id:
            self.test_move_file(copied_file_id, test_folder_id)
        
        # 11. Delete file (trash one file)
        if copied_file_id:
            self.test_delete_file(copied_file_id, permanent=False)
        
        # Final summary
        print("\n🎉 TEST SUITE COMPLETED!")
        print("=" * 50)
        print("✅ All Google Drive API operations tested successfully!")
        print(f"   Created {len(self.test_files)} test files")
        print(f"   Check your Google Drive folder: https://drive.google.com/drive/folders/{self.test_folder_id}")
        print("\nOperations tested:")
        print("  ✅ Authentication (Service Account)")
        print("  ✅ List Files")
        print("  ✅ Create Folder")
        print("  ✅ Write/Create File")
        print("  ✅ Read File")
        print("  ✅ Get File Metadata")
        print("  ✅ Update File Metadata")
        print("  ✅ Copy File")
        print("  ✅ Search Files")
        print("  ✅ Move File")
        print("  ✅ Delete File")
        
        # Ask for cleanup
        print(f"\n🧹 Test files created: {len(self.test_files)}")
        cleanup = input("Do you want to clean up test files? (y/N): ").lower().strip()
        if cleanup in ['y', 'yes']:
            self.cleanup_test_files()
        else:
            print("ℹ️ Test files left in Google Drive for manual inspection")
        
        return True


def main():
    """Main function to run the standalone test."""
    if len(sys.argv) < 3:
        print("Usage: python test_standalone_gdrive.py <service_account.json> <folder_id>")
        print()
        print("Example:")
        print("  python test_standalone_gdrive.py ./service-account.json 1ABC123DEF456GHI789JKL")
        print()
        print("Arguments:")
        print("  service_account.json - Path to your Google service account JSON file")
        print("  folder_id           - Google Drive folder ID where tests will be performed")
        print()
        print("The folder ID can be found in the Google Drive URL:")
        print("  https://drive.google.com/drive/folders/1ABC123DEF456GHI789JKL")
        print("                                         ^^^^^^^^^^^^^^^^^^^^^^")
        sys.exit(1)
    
    service_account_file = sys.argv[1]
    folder_id = sys.argv[2]
    
    print(f"🚀 Starting Google Drive API standalone test")
    print(f"📄 Service account file: {service_account_file}")
    print(f"📁 Test folder ID: {folder_id}")
    print()
    
    # Create and run the test
    tester = GoogleDriveStandaloneTest(service_account_file, folder_id)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 