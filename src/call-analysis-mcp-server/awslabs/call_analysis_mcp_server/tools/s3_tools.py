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

"""S3 tools for transcript file operations."""

from typing import Dict, List

from loguru import logger
from mcp.server.fastmcp import FastMCP

from ..services.s3_service import S3Service


def s3_reader_tool(mcp: FastMCP) -> None:
    """Register the S3 reader tool."""
    
    @mcp.tool(description="List and read transcript files from S3")
    def list_s3_transcripts(
        s3_bucket: str,
        s3_prefix: str = "",
        max_files: int = 50,
        aws_region: str = "us-east-1"
    ) -> Dict:
        """
        List transcript files in an S3 bucket/prefix.
        
        Args:
            s3_bucket: S3 bucket name
            s3_prefix: S3 prefix/folder path
            max_files: Maximum number of files to list
            aws_region: AWS region
            
        Returns:
            Dictionary containing list of transcript files
        """
        try:
            s3_service = S3Service(region=aws_region)
            
            transcript_files = s3_service.list_transcript_files(
                bucket=s3_bucket,
                prefix=s3_prefix,
                max_files=max_files
            )
            
            # Get file metadata
            file_details = []
            for file_key in transcript_files:
                try:
                    metadata = s3_service.get_file_metadata(s3_bucket, file_key)
                    file_details.append({
                        "key": file_key,
                        "size_bytes": metadata.get("ContentLength", 0),
                        "last_modified": metadata.get("LastModified", "").isoformat() if metadata.get("LastModified") else "",
                        "content_type": metadata.get("ContentType", ""),
                        "s3_url": f"s3://{s3_bucket}/{file_key}"
                    })
                except Exception as e:
                    logger.warning(f"Could not get metadata for {file_key}: {str(e)}")
                    file_details.append({
                        "key": file_key,
                        "s3_url": f"s3://{s3_bucket}/{file_key}",
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "bucket": s3_bucket,
                "prefix": s3_prefix,
                "files_found": len(file_details),
                "files": file_details
            }
            
        except Exception as e:
            logger.error(f"Error listing S3 transcripts: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            }


def s3_uploader_tool(mcp: FastMCP) -> None:
    """Register the S3 uploader tool."""
    
    @mcp.tool(description="Upload analysis results to S3")
    def upload_analysis_results(
        content: str,
        s3_bucket: str,
        s3_key: str,
        content_type: str = "application/json",
        aws_region: str = "us-east-1"
    ) -> Dict:
        """
        Upload analysis content to S3.
        
        Args:
            content: Content to upload
            s3_bucket: S3 bucket name
            s3_key: S3 key for the file
            content_type: MIME type of the content
            aws_region: AWS region
            
        Returns:
            Dictionary containing upload results
        """
        try:
            s3_service = S3Service(region=aws_region)
            
            if content_type == "application/json":
                s3_url = s3_service.upload_analysis_json(
                    content=content,
                    bucket=s3_bucket,
                    key=s3_key
                )
            elif content_type == "text/markdown":
                s3_url = s3_service.upload_analysis_markdown(
                    content=content,
                    bucket=s3_bucket,
                    key=s3_key
                )
            else:
                s3_url = s3_service.upload_file_content(
                    content=content,
                    bucket=s3_bucket,
                    key=s3_key,
                    content_type=content_type
                )
            
            return {
                "status": "success",
                "s3_url": s3_url,
                "bucket": s3_bucket,
                "key": s3_key,
                "content_type": content_type,
                "content_size_bytes": len(content.encode('utf-8'))
            }
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            } 