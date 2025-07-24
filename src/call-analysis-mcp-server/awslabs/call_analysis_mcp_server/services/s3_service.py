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

"""S3 service for transcript and analysis file operations."""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Any, Optional

from loguru import logger

from ..consts import SUPPORTED_TRANSCRIPT_FORMATS, MAX_TRANSCRIPT_SIZE_MB


class S3Service:
    """Service for S3 operations related to call analysis."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize S3 service.
        
        Args:
            region: AWS region for S3 operations
        """
        self.region = region
        try:
            self.s3_client = boto3.client('s3', region_name=region)
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Error initializing S3 client: {str(e)}")
            raise
    
    def list_transcript_files(self, bucket: str, prefix: str = "", max_files: int = 100) -> List[str]:
        """List transcript files in S3 bucket.
        
        Args:
            bucket: S3 bucket name
            prefix: S3 prefix/folder to search in
            max_files: Maximum number of files to return
            
        Returns:
            List of S3 keys for transcript files
        """
        try:
            transcript_files = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            page_iterator = paginator.paginate(
                Bucket=bucket,
                Prefix=prefix,
                PaginationConfig={'MaxItems': max_files}
            )
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Check if file has supported transcript format
                        if any(key.lower().endswith(fmt) for fmt in SUPPORTED_TRANSCRIPT_FORMATS):
                            # Check file size
                            size_mb = obj['Size'] / (1024 * 1024)
                            if size_mb <= MAX_TRANSCRIPT_SIZE_MB:
                                transcript_files.append(key)
                            else:
                                logger.warning(f"Skipping large file {key}: {size_mb:.2f}MB > {MAX_TRANSCRIPT_SIZE_MB}MB")
            
            logger.info(f"Found {len(transcript_files)} transcript files in s3://{bucket}/{prefix}")
            return transcript_files
            
        except ClientError as e:
            logger.error(f"Error listing files in S3 bucket {bucket}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing S3 files: {str(e)}")
            raise
    
    def read_transcript(self, bucket: str, key: str) -> str:
        """Read transcript content from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Transcript content as string
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            logger.info(f"Successfully read transcript from s3://{bucket}/{key}")
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"Transcript file not found: s3://{bucket}/{key}")
                raise FileNotFoundError(f"Transcript file not found: s3://{bucket}/{key}")
            elif error_code == 'NoSuchBucket':
                logger.error(f"S3 bucket not found: {bucket}")
                raise FileNotFoundError(f"S3 bucket not found: {bucket}")
            else:
                logger.error(f"Error reading transcript from S3: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error reading transcript: {str(e)}")
            raise
    
    def upload_analysis_json(self, content: str, bucket: str, key: str) -> str:
        """Upload analysis JSON to S3.
        
        Args:
            content: JSON content to upload
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            S3 URL of uploaded file
        """
        return self.upload_file_content(
            content=content,
            bucket=bucket,
            key=key,
            content_type="application/json"
        )
    
    def upload_analysis_markdown(self, content: str, bucket: str, key: str) -> str:
        """Upload analysis markdown to S3.
        
        Args:
            content: Markdown content to upload
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            S3 URL of uploaded file
        """
        return self.upload_file_content(
            content=content,
            bucket=bucket,
            key=key,
            content_type="text/markdown"
        )
    
    def upload_file_content(self, content: str, bucket: str, key: str, content_type: str = "text/plain") -> str:
        """Upload content to S3.
        
        Args:
            content: Content to upload
            bucket: S3 bucket name
            key: S3 object key
            content_type: MIME type of content
            
        Returns:
            S3 URL of uploaded file
        """
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType=content_type,
                Metadata={
                    'analysis-version': '1.0',
                    'generated-by': 'call-analysis-mcp-server'
                }
            )
            
            s3_url = f"s3://{bucket}/{key}"
            logger.info(f"Successfully uploaded file to {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {str(e)}")
            raise
    
    def get_file_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
        """Get metadata for an S3 file.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Dictionary containing file metadata
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            return {
                'ContentLength': response.get('ContentLength'),
                'LastModified': response.get('LastModified'),
                'ContentType': response.get('ContentType'),
                'ETag': response.get('ETag'),
                'Metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Error getting metadata for s3://{bucket}/{key}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting file metadata: {str(e)}")
            raise
    
    def check_bucket_access(self, bucket: str) -> bool:
        """Check if bucket exists and is accessible.
        
        Args:
            bucket: S3 bucket name
            
        Returns:
            True if bucket is accessible, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=bucket)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket {bucket} does not exist")
            elif error_code == '403':
                logger.error(f"Access denied to bucket {bucket}")
            else:
                logger.error(f"Error accessing bucket {bucket}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking bucket access: {str(e)}")
            return False 