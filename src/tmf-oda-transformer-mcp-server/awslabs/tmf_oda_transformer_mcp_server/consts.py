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

"""Constants for TMF ODA Transformer MCP Server."""

# Application constants
TMF_ODA_MCP_SERVER_APPLICATION_NAME = 'awslabs.tmf-oda-transformer-mcp-server'
DEFAULT_ANALYSIS_TIMEOUT = 300  # 5 minutes
MAX_FILE_SIZE_MB = 100

# TMF ODA Component Types
TMF_ODA_COMPONENT_TYPES = [
    'product-catalog-management',
    'customer-management',
    'order-management',
    'service-inventory-management',
    'resource-inventory-management',
    'party-management',
    'account-management',
    'billing-management',
    'product-offering-qualification',
    'service-qualification',
    'quote-management',
    'service-ordering',
    'product-ordering',
]

# Supported schema formats
SUPPORTED_SCHEMA_FORMATS = [
    'json-schema',
    'openapi',
    'swagger',
    'avro',
    'protobuf',
    'yaml-schema',
]

# Supported database types
SUPPORTED_DATABASE_TYPES = [
    'postgresql',
    'mysql',
    'mongodb',
    'oracle',
    'sqlserver',
    'dynamodb',
    'cassandra',
]

# File extensions for schema discovery
SCHEMA_FILE_EXTENSIONS = [
    '.json',
    '.yaml', 
    '.yml',
    '.avsc',
    '.proto',
    '.openapi',
    '.swagger',
]

# Error messages for schema analyzer
ERROR_EMPTY_WORKSPACE_DIR = 'Workspace directory path is required for schema analysis'
ERROR_INVALID_WORKSPACE_DIR = 'Provided workspace directory does not exist or is not accessible'
ERROR_INVALID_SCHEMA_FORMAT = 'Unsupported schema format specified'
ERROR_INVALID_ODA_COMPONENT_TYPE = 'Invalid TMF ODA component type specified'
ERROR_NO_SCHEMAS_FOUND = 'No schema files found in the specified workspace directory'
ERROR_SCHEMA_PARSE_FAILED = 'Failed to parse schema file'
ERROR_SCHEMA_ANALYSIS_FAILED = 'Schema analysis failed due to error'

# Error messages for database analyzer  
ERROR_EMPTY_CONNECTION_STRING = 'Database connection string is required'
ERROR_INVALID_DATABASE_TYPE = 'Unsupported database type specified'
ERROR_DATABASE_CONNECTION_FAILED = 'Failed to establish database connection'
ERROR_DATABASE_ANALYSIS_FAILED = 'Database analysis failed due to error'
ERROR_TABLES_NOT_FOUND = 'No tables found matching the specified filter'

# General error messages
ERROR_ANALYSIS_TIMEOUT = 'Analysis operation timed out'
ERROR_FILE_TOO_LARGE = f'File size exceeds maximum limit of {MAX_FILE_SIZE_MB}MB'
ERROR_INSUFFICIENT_PERMISSIONS = 'Insufficient permissions to access the specified resource'
ERROR_INTERNAL_ERROR = 'Internal server error occurred during analysis'

# TMF ODA compliance levels
COMPLIANCE_LEVELS = {
    'COMPLIANT': 'Fully compliant with TMF ODA specifications',
    'PARTIALLY_COMPLIANT': 'Partially compliant, minor modifications needed',
    'NON_COMPLIANT': 'Not compliant, significant transformation required',
    'UNKNOWN': 'Compliance status could not be determined',
}

# Analysis result statuses
ANALYSIS_STATUS = {
    'SUCCESS': 'Analysis completed successfully',
    'PARTIAL_SUCCESS': 'Analysis completed with some warnings',
    'FAILED': 'Analysis failed to complete',
    'TIMEOUT': 'Analysis timed out',
}

# TMF ODA reference documentation
TMF_ODA_DOCS_BASE_URL = 'https://www.tmforum.org/oda/'
TMF_ODA_API_CONFORMANCE_URL = f'{TMF_ODA_DOCS_BASE_URL}api-conformance/'

# Default transformation recommendations
DEFAULT_TRANSFORMATION_RECOMMENDATIONS = [
    'Review API endpoint structures for RESTful compliance',
    'Validate data models against TMF Open API specifications',
    'Ensure proper event notification implementation',
    'Implement standard TMF error handling patterns',
    'Add required TMF metadata fields to data models',
    'Validate security implementation according to TMF guidelines',
] 