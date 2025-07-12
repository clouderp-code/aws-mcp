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

"""Analysis tools for TMF ODA Transformer MCP Server."""

from datetime import datetime
from typing import Optional

from loguru import logger
from mcp.server.fastmcp import Context
from pydantic import Field
from typing import Annotated

from ..models import (
    TMFODAComponentType,
    SchemaFormat,
    DatabaseType,
    SchemaAnalysisReport,
    DatabaseAnalysisReport,
)
from ..services import SchemaAnalysisService, DatabaseAnalysisService
from .base import BaseToolMixin


class AnalysisToolsMixin(BaseToolMixin):
    """Mixin class for analysis tools."""
    
    def __init__(self):
        self.schema_service = SchemaAnalysisService()
        self.database_service = DatabaseAnalysisService()


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
    tool_name = "schema-analyzer"
    start_time = datetime.now()
    
    try:
        # Log tool start
        BaseToolMixin.log_tool_start(
            tool_name,
            workspace_dir=workspace_dir,
            oda_component_type=oda_component_type,
            schema_format=schema_format
        )
        
        # Validate inputs
        await BaseToolMixin.validate_workspace_dir(ctx, workspace_dir)
        await BaseToolMixin.validate_oda_component_type(ctx, oda_component_type)
        await BaseToolMixin.validate_schema_format(ctx, schema_format)
        
        # Execute analysis using service
        service = SchemaAnalysisService()
        report = await service.analyze_workspace(
            workspace_dir=workspace_dir,
            oda_component_type=oda_component_type,
            schema_format=schema_format
        )
        
        # Log success
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_success(
            tool_name,
            duration,
            total_files=report.total_files_found,
            analyzed_files=report.total_files_analyzed,
            compliance_score=report.summary.get('average_compliance_score', 0)
        )
        
        return report
        
    except Exception as e:
        # Log error and re-raise
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_error(tool_name, e, duration)
        await ctx.error(f'{tool_name} failed: {str(e)}')
        raise


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
    tool_name = "db-analyzer"
    start_time = datetime.now()
    
    try:
        # Log tool start (with sanitized connection string)
        from ..utils import sanitize_connection_string
        sanitized_connection = sanitize_connection_string(connection_string)
        BaseToolMixin.log_tool_start(
            tool_name,
            connection_string=sanitized_connection,
            database_type=database_type,
            oda_component_type=oda_component_type,
            tables_filter=tables_filter
        )
        
        # Validate inputs
        await BaseToolMixin.validate_connection_string(ctx, connection_string)
        await BaseToolMixin.validate_database_type(ctx, database_type)
        await BaseToolMixin.validate_oda_component_type(ctx, oda_component_type)
        
        # Execute analysis using service
        service = DatabaseAnalysisService()
        report = await service.analyze_database(
            connection_string=connection_string,
            database_type=database_type,
            oda_component_type=oda_component_type,
            tables_filter=tables_filter
        )
        
        # Log success
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_success(
            tool_name,
            duration,
            total_tables=report.total_tables_found,
            analyzed_tables=report.total_tables_analyzed,
            compliance_score=report.summary.get('average_compliance_score', 0)
        )
        
        return report
        
    except Exception as e:
        # Log error and re-raise
        duration = (datetime.now() - start_time).total_seconds()
        BaseToolMixin.log_tool_error(tool_name, e, duration)
        await ctx.error(f'{tool_name} failed: {str(e)}')
        raise 