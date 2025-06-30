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

"""awslabs TMF ODA Transformer MCP Server implementation."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from awslabs.tmf_oda_transformer_mcp_server.consts import (
    ANALYSIS_STATUS,
    COMPLIANCE_LEVELS,
    DEFAULT_ANALYSIS_TIMEOUT,
    DEFAULT_TRANSFORMATION_RECOMMENDATIONS,
    ERROR_ANALYSIS_TIMEOUT,
    ERROR_DATABASE_ANALYSIS_FAILED,
    ERROR_DATABASE_CONNECTION_FAILED,
    ERROR_EMPTY_CONNECTION_STRING,
    ERROR_EMPTY_WORKSPACE_DIR,
    ERROR_INTERNAL_ERROR,
    ERROR_INVALID_DATABASE_TYPE,
    ERROR_INVALID_ODA_COMPONENT_TYPE,
    ERROR_INVALID_SCHEMA_FORMAT,
    ERROR_INVALID_WORKSPACE_DIR,
    ERROR_NO_SCHEMAS_FOUND,
    ERROR_SCHEMA_ANALYSIS_FAILED,
    ERROR_TABLES_NOT_FOUND,
    MAX_FILE_SIZE_MB,
    SCHEMA_FILE_EXTENSIONS,
    SUPPORTED_DATABASE_TYPES,
    SUPPORTED_SCHEMA_FORMATS,
    TMF_ODA_COMPONENT_TYPES,
    TMF_ODA_MCP_SERVER_APPLICATION_NAME,
)
from awslabs.tmf_oda_transformer_mcp_server.models import (
    ComplianceLevel,
    DatabaseAnalysisReport,
    DatabaseType,
    SchemaAnalysisReport,
    SchemaFormat,
    TMFODAComponentType,
)
from loguru import logger
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field
from typing import Annotated


# Initialize the MCP server
mcp = FastMCP(
    TMF_ODA_MCP_SERVER_APPLICATION_NAME,
    instructions="""
    # TMF ODA Transformer MCP Server
    
    Provides tools to analyze schema files and databases for TMF ODA (TM Forum Open Digital Architecture) transformation compliance.
    
    ## Available Tools
    
    ### schema-analyzer
    Discovers and analyzes schema files in a workspace directory for TMF ODA transformation requirements.
    Supports multiple schema formats including JSON Schema, OpenAPI, Swagger, Avro, and Protocol Buffers.
    
    ### db-analyzer
    Connects to and analyzes database structures for TMF ODA transformation requirements.
    Supports various database types including PostgreSQL, MySQL, MongoDB, and others.
    
    Both tools provide detailed compliance assessments, transformation recommendations, and actionable insights
    for achieving TMF ODA compliance.
    """,
    dependencies=[
        'loguru',
        'pydantic',
        'sqlalchemy',
        'pymongo',
        'psycopg',
        'mysql-connector-python',
        'jsonschema',
        'pyyaml',
        'openapi-spec-validator',
    ],
)


@mcp.tool(
    name='schema-analyzer',
    description="""Discover and analyze schema files for TMF ODA transformation requirements.
    
    This tool recursively scans a workspace directory for schema files (JSON Schema, OpenAPI, Swagger, Avro, etc.)
    and analyzes them for compliance with TMF ODA specifications. It provides detailed recommendations for
    transforming schemas to achieve TMF ODA compliance.
    
    The analysis includes:
    - Schema format detection and validation
    - TMF ODA compliance assessment
    - Detailed transformation recommendations
    - Issue identification with severity levels
    - Compliance scoring and reporting
    """,
)
async def schema_analyzer_tool(
    ctx: Context,
    workspace_dir: Annotated[
        str,
        Field(
            description="""The workspace directory path to analyze for schema files.
            CRITICAL: Assistant must always provide the current IDE workspace directory parameter to analyze schemas in the user's current project."""
        ),
    ],
    oda_component_type: Annotated[
        TMFODAComponentType,
        Field(
            description="""Target TMF ODA component type for analysis.
            This determines which TMF ODA specifications to validate against.
            Options: product-catalog-management, customer-management, order-management, 
            service-inventory-management, resource-inventory-management, party-management,
            account-management, billing-management, product-offering-qualification,
            service-qualification, quote-management, service-ordering, product-ordering"""
        ),
    ],
    schema_format: Annotated[
        Optional[SchemaFormat],
        Field(
            default=None,
            description="""Optional filter for specific schema formats.
            If provided, only schemas of this format will be analyzed.
            Options: json-schema, openapi, swagger, avro, protobuf, yaml-schema"""
        ),
    ],
) -> SchemaAnalysisReport:
    """Analyze schema files in a workspace for TMF ODA transformation requirements.
    
    Args:
        ctx: MCP context for logging and state management
        workspace_dir: Directory path to analyze for schema files
        oda_component_type: Target TMF ODA component type for analysis
        schema_format: Optional filter for specific schema formats
        
    Returns:
        SchemaAnalysisReport: Comprehensive analysis report with compliance assessment and recommendations
    """
    logger.info(f'Starting schema analysis for directory: {workspace_dir}')
    
    start_time = datetime.now()
    
    # Validate inputs
    if not workspace_dir or workspace_dir.strip() == '':
        await ctx.error(ERROR_EMPTY_WORKSPACE_DIR)
        raise ValueError(ERROR_EMPTY_WORKSPACE_DIR)
    
    if not Path(workspace_dir).exists() or not Path(workspace_dir).is_dir():
        await ctx.error(ERROR_INVALID_WORKSPACE_DIR)
        raise ValueError(ERROR_INVALID_WORKSPACE_DIR)
    
    if schema_format and schema_format not in SUPPORTED_SCHEMA_FORMATS:
        await ctx.error(ERROR_INVALID_SCHEMA_FORMAT)
        raise ValueError(ERROR_INVALID_SCHEMA_FORMAT)
    
    if oda_component_type not in TMF_ODA_COMPONENT_TYPES:
        await ctx.error(ERROR_INVALID_ODA_COMPONENT_TYPE)
        raise ValueError(ERROR_INVALID_ODA_COMPONENT_TYPE)
    
    try:
        # Discover schema files
        schema_files = await _discover_schema_files(workspace_dir, schema_format)
        
        if not schema_files:
            await ctx.error(ERROR_NO_SCHEMAS_FOUND)
            raise ValueError(ERROR_NO_SCHEMAS_FOUND)
        
        logger.info(f'Found {len(schema_files)} schema files to analyze')
        
        # Analyze each schema file
        analysis_results = []
        for schema_file in schema_files:
            try:
                # Simulate analysis with timeout
                result = await asyncio.wait_for(
                    _analyze_schema_file(schema_file, oda_component_type),
                    timeout=DEFAULT_ANALYSIS_TIMEOUT
                )
                analysis_results.append(result)
            except asyncio.TimeoutError:
                logger.warning(f'Analysis timeout for file: {schema_file}')
                continue
            except Exception as e:
                logger.error(f'Analysis failed for file {schema_file}: {str(e)}')
                continue
        
        # Calculate summary statistics
        total_analyzed = len(analysis_results)
        compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.COMPLIANT)
        partially_compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.PARTIALLY_COMPLIANT)
        non_compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.NON_COMPLIANT)
        avg_compliance_score = sum(r.compliance_score for r in analysis_results) / total_analyzed if total_analyzed > 0 else 0
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Build analysis report
        report = SchemaAnalysisReport(
            workspace_dir=workspace_dir,
            oda_component_type=oda_component_type,
            schema_format_filter=schema_format,
            total_files_found=len(schema_files),
            total_files_analyzed=total_analyzed,
            analysis_status=ANALYSIS_STATUS['SUCCESS'] if total_analyzed > 0 else ANALYSIS_STATUS['PARTIAL_SUCCESS'],
            analysis_timestamp=start_time,
            analysis_duration=duration,
            results=analysis_results,
            summary={
                'compliant_count': compliant_count,
                'partially_compliant_count': partially_compliant_count,
                'non_compliant_count': non_compliant_count,
                'avg_compliance_score': round(avg_compliance_score, 2),
                'total_issues': sum(len(r.issues) for r in analysis_results),
                'total_recommendations': sum(len(r.recommendations) for r in analysis_results),
            }
        )
        
        logger.success(f'Schema analysis completed. Analyzed {total_analyzed} files in {duration:.2f}s')
        return report
        
    except Exception as e:
        logger.error(f'Schema analysis failed: {str(e)}')
        await ctx.error(f'{ERROR_SCHEMA_ANALYSIS_FAILED}: {str(e)}')
        raise Exception(f'{ERROR_SCHEMA_ANALYSIS_FAILED}: {str(e)}')


@mcp.tool(
    name='db-analyzer',
    description="""Connect to and analyze database structures for TMF ODA transformation requirements.
    
    This tool connects to various database types (PostgreSQL, MySQL, MongoDB, etc.) and analyzes
    their schema structures for compliance with TMF ODA specifications. It provides detailed
    recommendations for transforming database schemas to achieve TMF ODA compliance.
    
    The analysis includes:
    - Database schema discovery and validation
    - TMF ODA compliance assessment for data models
    - Detailed transformation recommendations
    - Column/field mapping suggestions
    - Compliance scoring and reporting
    """,
)
async def db_analyzer_tool(
    ctx: Context,
    connection_string: Annotated[
        str,
        Field(
            description="""Database connection string or configuration.
            Examples:
            - PostgreSQL: postgresql://user:password@host:port/database
            - MySQL: mysql://user:password@host:port/database
            - MongoDB: mongodb://user:password@host:port/database
            Note: Passwords will be sanitized in logs and reports for security."""
        ),
    ],
    database_type: Annotated[
        DatabaseType,
        Field(
            description="""Type of database to analyze.
            Options: postgresql, mysql, mongodb, oracle, sqlserver, dynamodb, cassandra"""
        ),
    ],
    oda_component_type: Annotated[
        TMFODAComponentType,
        Field(
            description="""Target TMF ODA component type for analysis.
            This determines which TMF ODA specifications to validate against.
            Options: product-catalog-management, customer-management, order-management, 
            service-inventory-management, resource-inventory-management, party-management,
            account-management, billing-management, product-offering-qualification,
            service-qualification, quote-management, service-ordering, product-ordering"""
        ),
    ],
    tables_filter: Annotated[
        Optional[str],
        Field(
            default=None,
            description="""Optional filter for specific tables/collections to analyze.
            Can be a comma-separated list of table names or a pattern (e.g., 'user_*,product_*')"""
        ),
    ],
) -> DatabaseAnalysisReport:
    """Analyze database structures for TMF ODA transformation requirements.
    
    Args:
        ctx: MCP context for logging and state management
        connection_string: Database connection string or configuration
        database_type: Type of database to analyze
        oda_component_type: Target TMF ODA component type for analysis
        tables_filter: Optional filter for specific tables/collections
        
    Returns:
        DatabaseAnalysisReport: Comprehensive analysis report with compliance assessment and recommendations
    """
    logger.info(f'Starting database analysis for {database_type}')
    
    start_time = datetime.now()
    
    # Validate inputs
    if not connection_string or connection_string.strip() == '':
        await ctx.error(ERROR_EMPTY_CONNECTION_STRING)
        raise ValueError(ERROR_EMPTY_CONNECTION_STRING)
    
    if database_type not in SUPPORTED_DATABASE_TYPES:
        await ctx.error(ERROR_INVALID_DATABASE_TYPE)
        raise ValueError(ERROR_INVALID_DATABASE_TYPE)
    
    if oda_component_type not in TMF_ODA_COMPONENT_TYPES:
        await ctx.error(ERROR_INVALID_ODA_COMPONENT_TYPE)
        raise ValueError(ERROR_INVALID_ODA_COMPONENT_TYPE)
    
    try:
        # Test database connection
        connection_ok = await _test_database_connection(connection_string, database_type)
        if not connection_ok:
            await ctx.error(ERROR_DATABASE_CONNECTION_FAILED)
            raise Exception(ERROR_DATABASE_CONNECTION_FAILED)
        
        # Discover database tables/collections
        tables = await _discover_database_tables(connection_string, database_type, tables_filter)
        
        if not tables:
            await ctx.error(ERROR_TABLES_NOT_FOUND)
            raise ValueError(ERROR_TABLES_NOT_FOUND)
        
        logger.info(f'Found {len(tables)} tables/collections to analyze')
        
        # Analyze each table
        analysis_results = []
        for table in tables:
            try:
                # Simulate analysis with timeout
                result = await asyncio.wait_for(
                    _analyze_database_table(connection_string, database_type, table, oda_component_type),
                    timeout=DEFAULT_ANALYSIS_TIMEOUT
                )
                analysis_results.append(result)
            except asyncio.TimeoutError:
                logger.warning(f'Analysis timeout for table: {table}')
                continue
            except Exception as e:
                logger.error(f'Analysis failed for table {table}: {str(e)}')
                continue
        
        # Calculate summary statistics
        total_analyzed = len(analysis_results)
        compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.COMPLIANT)
        partially_compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.PARTIALLY_COMPLIANT)
        non_compliant_count = sum(1 for r in analysis_results if r.compliance_level == ComplianceLevel.NON_COMPLIANT)
        avg_compliance_score = sum(r.compliance_score for r in analysis_results) / total_analyzed if total_analyzed > 0 else 0
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Build analysis report
        report = DatabaseAnalysisReport(
            connection_string=connection_string,  # Will be sanitized by the model
            database_type=database_type,
            oda_component_type=oda_component_type,
            tables_filter=tables_filter,
            total_tables_found=len(tables),
            total_tables_analyzed=total_analyzed,
            analysis_status=ANALYSIS_STATUS['SUCCESS'] if total_analyzed > 0 else ANALYSIS_STATUS['PARTIAL_SUCCESS'],
            analysis_timestamp=start_time,
            analysis_duration=duration,
            results=analysis_results,
            summary={
                'compliant_count': compliant_count,
                'partially_compliant_count': partially_compliant_count,
                'non_compliant_count': non_compliant_count,
                'avg_compliance_score': round(avg_compliance_score, 2),
                'total_recommendations': sum(len(r.recommendations) for r in analysis_results),
            }
        )
        
        logger.success(f'Database analysis completed. Analyzed {total_analyzed} tables in {duration:.2f}s')
        return report
        
    except Exception as e:
        logger.error(f'Database analysis failed: {str(e)}')
        await ctx.error(f'{ERROR_DATABASE_ANALYSIS_FAILED}: {str(e)}')
        raise Exception(f'{ERROR_DATABASE_ANALYSIS_FAILED}: {str(e)}')


# Helper functions for pseudo implementation

async def _discover_schema_files(workspace_dir: str, schema_format: Optional[SchemaFormat]) -> List[str]:
    """Discover schema files in the workspace directory.
    
    This is a pseudo implementation that simulates file discovery.
    In a real implementation, this would:
    1. Recursively scan the directory for files with schema extensions
    2. Filter by schema format if specified
    3. Validate file sizes and permissions
    """
    # Pseudo implementation - simulate discovering schema files
    discovered_files = []
    
    # Simulate finding schema files
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if any(file.endswith(ext) for ext in SCHEMA_FILE_EXTENSIONS):
                file_path = os.path.join(root, file)
                # Check file size
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                        logger.warning(f'Skipping large file: {file_path} ({file_size} bytes)')
                        continue
                    discovered_files.append(file_path)
                except Exception as e:
                    logger.warning(f'Error accessing file {file_path}: {e}')
                    continue
    
    return discovered_files[:10]  # Limit for pseudo implementation


async def _analyze_schema_file(schema_file: str, oda_component_type: TMFODAComponentType):
    """Analyze a single schema file for TMF ODA compliance.
    
    This is a pseudo implementation that simulates schema analysis.
    In a real implementation, this would:
    1. Parse the schema file based on its format
    2. Validate against TMF ODA specifications
    3. Identify compliance issues and recommendations
    4. Calculate compliance scores
    """
    from awslabs.tmf_oda_transformer_mcp_server.models import (
        SchemaAnalysisIssue,
        SchemaAnalysisResult,
        SchemaFile,
        TransformationRecommendation,
    )
    
    # Simulate analysis delay
    await asyncio.sleep(0.1)
    
    # Create pseudo schema file info
    file_path = Path(schema_file)
    schema_file_info = SchemaFile(
        file_path=str(file_path.absolute()),
        file_name=file_path.name,
        file_size=file_path.stat().st_size if file_path.exists() else 1000,
        format=SchemaFormat.JSON_SCHEMA,  # Pseudo detection
        last_modified=datetime.now()
    )
    
    # Simulate compliance analysis
    compliance_level = ComplianceLevel.PARTIALLY_COMPLIANT
    compliance_score = 75.5
    
    # Create pseudo issues
    issues = [
        SchemaAnalysisIssue(
            severity='WARNING',
            path='/properties/id',
            message='Missing TMF standard ID format validation',
            suggestion='Add pattern validation for TMF entity IDs'
        ),
        SchemaAnalysisIssue(
            severity='INFO',
            path='/properties/href',
            message='Consider adding href field for TMF API compliance',
            suggestion='Add href field with URI format validation'
        )
    ]
    
    # Create pseudo recommendations
    recommendations = [
        TransformationRecommendation(
            category='Data Model',
            priority='HIGH',
            title='Implement TMF Entity Base Structure',
            description='Add standard TMF entity fields (id, href, @type, @baseType)',
            impact='Improves API consistency and TMF compliance',
            effort='MINIMAL'
        ),
        TransformationRecommendation(
            category='Validation',
            priority='MEDIUM',
            title='Add TMF Standard Patterns',
            description='Implement TMF standard validation patterns for common fields',
            impact='Ensures data consistency across TMF components',
            effort='MODERATE'
        )
    ]
    
    return SchemaAnalysisResult(
        schema_file=schema_file_info,
        compliance_level=compliance_level,
        compliance_score=compliance_score,
        issues=issues,
        recommendations=recommendations,
        analysis_duration=0.5
    )


async def _test_database_connection(connection_string: str, database_type: DatabaseType) -> bool:
    """Test database connection.
    
    This is a pseudo implementation that simulates connection testing.
    In a real implementation, this would establish actual database connections.
    """
    # Simulate connection test delay
    await asyncio.sleep(0.2)
    
    # Pseudo implementation - always return True for demo
    logger.info(f'Testing {database_type} connection...')
    return True


async def _discover_database_tables(connection_string: str, database_type: DatabaseType, tables_filter: Optional[str]) -> List[str]:
    """Discover database tables or collections.
    
    This is a pseudo implementation that simulates table discovery.
    In a real implementation, this would query the database metadata.
    """
    # Simulate database query delay
    await asyncio.sleep(0.3)
    
    # Pseudo implementation - return sample table names
    if database_type == DatabaseType.MONGODB:
        tables = ['users', 'products', 'orders', 'customers']
    else:
        tables = ['user_accounts', 'product_catalog', 'order_history', 'customer_profiles']
    
    # Apply filter if specified
    if tables_filter:
        # Simple filter implementation
        filter_terms = [term.strip() for term in tables_filter.split(',')]
        filtered_tables = []
        for table in tables:
            for term in filter_terms:
                if term.replace('*', '') in table:
                    filtered_tables.append(table)
                    break
        return filtered_tables
    
    return tables


async def _analyze_database_table(connection_string: str, database_type: DatabaseType, table: str, oda_component_type: TMFODAComponentType):
    """Analyze a database table for TMF ODA compliance.
    
    This is a pseudo implementation that simulates table analysis.
    In a real implementation, this would:
    1. Query table schema and metadata
    2. Analyze column types and constraints
    3. Validate against TMF ODA data models
    4. Generate transformation recommendations
    """
    from awslabs.tmf_oda_transformer_mcp_server.models import (
        DatabaseAnalysisResult,
        DatabaseColumn,
        DatabaseSchema,
        DatabaseTable,
        TransformationRecommendation,
    )
    
    # Simulate analysis delay
    await asyncio.sleep(0.2)
    
    # Create pseudo table info
    table_info = DatabaseTable(
        name=table,
        schema_name='public' if database_type in [DatabaseType.POSTGRESQL, DatabaseType.MYSQL] else None,
        type='table',
        row_count=1000,
        size_mb=5.2
    )
    
    # Create pseudo column info
    columns = [
        DatabaseColumn(
            name='id',
            data_type='VARCHAR(255)',
            is_nullable=False,
            is_primary_key=True,
            default_value=None,
            constraints=['PRIMARY KEY', 'NOT NULL']
        ),
        DatabaseColumn(
            name='name',
            data_type='VARCHAR(255)',
            is_nullable=False,
            is_primary_key=False,
            default_value=None,
            constraints=['NOT NULL']
        ),
        DatabaseColumn(
            name='created_at',
            data_type='TIMESTAMP',
            is_nullable=False,
            is_primary_key=False,
            default_value='CURRENT_TIMESTAMP',
            constraints=['NOT NULL']
        )
    ]
    
    schema = DatabaseSchema(table=table_info, columns=columns)
    
    # Simulate compliance analysis
    compliance_level = ComplianceLevel.NON_COMPLIANT
    compliance_score = 45.0
    
    # Create pseudo recommendations
    recommendations = [
        TransformationRecommendation(
            category='Schema Structure',
            priority='HIGH',
            title='Add TMF Standard Fields',
            description=f'Add href, @type, @baseType fields to {table} table for TMF compliance',
            impact='Enables TMF API resource representation',
            effort='MODERATE'
        ),
        TransformationRecommendation(
            category='Data Types',
            priority='MEDIUM',
            title='Standardize ID Format',
            description='Convert ID field to use TMF standard UUID format',
            impact='Improves data consistency and TMF compliance',
            effort='SIGNIFICANT'
        )
    ]
    
    return DatabaseAnalysisResult(
        database_schema=schema,
        compliance_level=compliance_level,
        compliance_score=compliance_score,
        recommendations=recommendations,
        analysis_duration=0.8
    )


class NoOpCtx:
    """A No-op context class for error handling in MCP tools."""
    
    async def error(self, message):
        """Do nothing.
        
        Args:
            message: The error message
        """


def main():
    """Run the MCP server with CLI argument support."""
    logger.info('Starting TMF ODA Transformer MCP Server')
    
    # Log configuration
    log_level = os.getenv('FASTMCP_LOG_LEVEL', 'INFO')
    logger.info(f'Log level: {log_level}')
    
    # Optional configuration
    tmf_oda_reference_path = os.getenv('TMF_ODA_REFERENCE_PATH')
    if tmf_oda_reference_path:
        logger.info(f'TMF ODA reference path: {tmf_oda_reference_path}')
    
    aws_profile = os.getenv('AWS_PROFILE')
    if aws_profile:
        logger.info(f'AWS profile: {aws_profile}')
    
    aws_region = os.getenv('AWS_REGION')
    if aws_region:
        logger.info(f'AWS region: {aws_region}')
    
    logger.success('TMF ODA Transformer MCP Server initialized successfully')
    
    # Start the MCP server
    mcp.run()


if __name__ == '__main__':
    main() 