"""
AWS Client Utilities for TMF ODA Transformer

This module provides utilities for creating AWS clients with support for:
- Instance roles (for EC2 instances)
- Role ARN assumption (for external machines)
- Automatic credential detection
"""

import boto3
import os
import json
from typing import Optional, Dict, Any
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

# Cache for assumed role credentials
_assumed_role_cache = {}
_cache_expiry_buffer = 5  # minutes before expiry to refresh


class AWSClientManager:
    """
    Manages AWS client creation with support for role assumption.
    
    This class provides a unified interface for creating AWS clients that can:
    1. Use instance roles (default for EC2 instances)
    2. Assume a role using ARN (for external machines)
    3. Use standard credential chain (profiles, environment variables, etc.)
    """
    
    def __init__(self, role_arn: Optional[str] = None, region_name: Optional[str] = None):
        """
        Initialize the AWS client manager.
        
        Args:
            role_arn: Optional role ARN to assume
            region_name: Optional AWS region name
        """
        self.role_arn = role_arn or os.environ.get('AWS_ROLE_ARN')
        self.region_name = region_name or self._get_default_region()
        self.session_name = f"TMF-ODA-Transformer-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Log the configuration
        if self.role_arn:
            logger.info(f"AWS Client Manager configured with role ARN: {self.role_arn}")
        else:
            logger.info("AWS Client Manager configured with default credential chain")
        logger.info(f"AWS Region: {self.region_name}")
    
    def _get_default_region(self) -> str:
        """Get the default AWS region."""
        # Try environment variable first
        region = os.environ.get('AWS_REGION')
        if region:
            return region
        
        # Try boto3 session default region
        try:
            session = boto3.Session()
            region = session.region_name
            if region:
                return region
        except Exception:
            pass
        
        # Fallback to us-east-2
        return 'us-east-2'
    
    def _get_assumed_role_credentials(self) -> Dict[str, Any]:
        """
        Get credentials by assuming the configured role.
        
        Returns:
            Dict containing AWS credentials
        """
        if not self.role_arn:
            raise ValueError("Role ARN is required for role assumption")
        
        # Check cache first
        cache_key = f"{self.role_arn}#{self.region_name}"
        if cache_key in _assumed_role_cache:
            cached_creds = _assumed_role_cache[cache_key]
            # Check if credentials are still valid (with buffer)
            expiry = cached_creds.get('Expiration')
            if expiry and datetime.now(timezone.utc) < expiry - timedelta(minutes=_cache_expiry_buffer):
                logger.debug("Using cached assumed role credentials")
                return cached_creds
        
        # Assume role
        try:
            logger.info(f"Assuming role: {self.role_arn}")
            
            # Create STS client with default credentials
            sts_client = boto3.client('sts', region_name=self.region_name)
            
            # Assume the role
            response = sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName=self.session_name,
                DurationSeconds=3600  # 1 hour
            )
            
            credentials = response['Credentials']
            
            # Cache the credentials
            _assumed_role_cache[cache_key] = credentials
            
            logger.info(f"Successfully assumed role: {self.role_arn}")
            return credentials
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"Failed to assume role {self.role_arn}: {error_code} - {error_msg}")
            raise Exception(f"Role assumption failed: {error_code} - {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected error assuming role {self.role_arn}: {str(e)}")
            raise Exception(f"Role assumption failed: {str(e)}")
    
    def _create_session(self) -> boto3.Session:
        """
        Create a boto3 session with appropriate credentials.
        
        Returns:
            boto3.Session with configured credentials
        """
        if self.role_arn:
            # Use assumed role credentials
            credentials = self._get_assumed_role_credentials()
            return boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=self.region_name
            )
        else:
            # Use default credential chain
            return boto3.Session(region_name=self.region_name)
    
    def create_client(self, service_name: str, config: Optional[Config] = None) -> Any:
        """
        Create an AWS service client.
        
        Args:
            service_name: Name of the AWS service (e.g., 'dynamodb', 's3')
            config: Optional boto3 Config object
            
        Returns:
            AWS service client
        """
        try:
            session = self._create_session()
            
            # Create default config if none provided
            if config is None:
                config = Config(
                    retries={'max_attempts': 3, 'mode': 'adaptive'},
                    user_agent_extra='TMF-ODA-Transformer/1.0'
                )
            
            client = session.client(service_name, config=config)
            logger.debug(f"Created {service_name} client successfully")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create {service_name} client: {str(e)}")
            raise Exception(f"Failed to create {service_name} client: {str(e)}")
    
    def create_resource(self, service_name: str, config: Optional[Config] = None) -> Any:
        """
        Create an AWS service resource.
        
        Args:
            service_name: Name of the AWS service (e.g., 'dynamodb', 's3')
            config: Optional boto3 Config object
            
        Returns:
            AWS service resource
        """
        try:
            session = self._create_session()
            
            # Create default config if none provided
            if config is None:
                config = Config(
                    retries={'max_attempts': 3, 'mode': 'adaptive'},
                    user_agent_extra='TMF-ODA-Transformer/1.0'
                )
            
            resource = session.resource(service_name, config=config)
            logger.debug(f"Created {service_name} resource successfully")
            return resource
            
        except Exception as e:
            logger.error(f"Failed to create {service_name} resource: {str(e)}")
            raise Exception(f"Failed to create {service_name} resource: {str(e)}")
    
    def test_credentials(self) -> Dict[str, Any]:
        """
        Test the current credentials and return caller identity.
        
        Returns:
            Dict containing caller identity information
        """
        try:
            session = self._create_session()
            sts_client = session.client('sts')
            
            identity = sts_client.get_caller_identity()
            logger.info(f"Credentials test successful - Account: {identity['Account']}, ARN: {identity['Arn']}")
            return identity
            
        except Exception as e:
            logger.error(f"Credentials test failed: {str(e)}")
            raise Exception(f"Credentials test failed: {str(e)}")


# Global instance for backward compatibility
_default_client_manager = None


def get_default_client_manager() -> AWSClientManager:
    """Get the default AWS client manager instance."""
    global _default_client_manager
    if _default_client_manager is None:
        _default_client_manager = AWSClientManager()
    return _default_client_manager


def create_aws_client(service_name: str, 
                     role_arn: Optional[str] = None, 
                     region_name: Optional[str] = None,
                     config: Optional[Config] = None) -> Any:
    """
    Create an AWS service client with optional role assumption.
    
    Args:
        service_name: Name of the AWS service
        role_arn: Optional role ARN to assume
        region_name: Optional AWS region
        config: Optional boto3 Config object
        
    Returns:
        AWS service client
    """
    client_manager = AWSClientManager(role_arn=role_arn, region_name=region_name)
    return client_manager.create_client(service_name, config=config)


def create_aws_resource(service_name: str, 
                       role_arn: Optional[str] = None, 
                       region_name: Optional[str] = None,
                       config: Optional[Config] = None) -> Any:
    """
    Create an AWS service resource with optional role assumption.
    
    Args:
        service_name: Name of the AWS service
        role_arn: Optional role ARN to assume
        region_name: Optional AWS region
        config: Optional boto3 Config object
        
    Returns:
        AWS service resource
    """
    client_manager = AWSClientManager(role_arn=role_arn, region_name=region_name)
    return client_manager.create_resource(service_name, config=config)


def test_aws_credentials(role_arn: Optional[str] = None, 
                        region_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Test AWS credentials with optional role assumption.
    
    Args:
        role_arn: Optional role ARN to assume
        region_name: Optional AWS region
        
    Returns:
        Dict containing caller identity information
    """
    client_manager = AWSClientManager(role_arn=role_arn, region_name=region_name)
    return client_manager.test_credentials() 