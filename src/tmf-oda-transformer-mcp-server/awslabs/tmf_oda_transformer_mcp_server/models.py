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

"""Pydantic models for TMF ODA Transformer MCP Server."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ComplianceLevel(str, Enum):
    """TMF ODA compliance levels."""
    
    COMPLIANT = 'COMPLIANT'
    PARTIALLY_COMPLIANT = 'PARTIALLY_COMPLIANT'
    NON_COMPLIANT = 'NON_COMPLIANT'
    UNKNOWN = 'UNKNOWN'


class AnalysisStatus(str, Enum):
    """Analysis operation status."""
    
    SUCCESS = 'SUCCESS'
    PARTIAL_SUCCESS = 'PARTIAL_SUCCESS'
    FAILED = 'FAILED'
    TIMEOUT = 'TIMEOUT'


class TMFODAComponentType(str, Enum):
    """TMF ODA component types."""
    
    PRODUCT_CATALOG_MANAGEMENT = 'product-catalog-management'
    CUSTOMER_MANAGEMENT = 'customer-management'
    ORDER_MANAGEMENT = 'order-management'
    SERVICE_INVENTORY_MANAGEMENT = 'service-inventory-management'
    RESOURCE_INVENTORY_MANAGEMENT = 'resource-inventory-management'
    PARTY_MANAGEMENT = 'party-management'
    ACCOUNT_MANAGEMENT = 'account-management'
    BILLING_MANAGEMENT = 'billing-management'
    PRODUCT_OFFERING_QUALIFICATION = 'product-offering-qualification'
    SERVICE_QUALIFICATION = 'service-qualification'
    QUOTE_MANAGEMENT = 'quote-management'
    SERVICE_ORDERING = 'service-ordering'
    PRODUCT_ORDERING = 'product-ordering'


class SchemaFormat(str, Enum):
    """Supported schema formats."""
    
    JSON_SCHEMA = 'json-schema'
    OPENAPI = 'openapi'
    SWAGGER = 'swagger'
    AVRO = 'avro'
    PROTOBUF = 'protobuf'
    YAML_SCHEMA = 'yaml-schema'


class DatabaseType(str, Enum):
    """Supported database types."""
    
    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    MONGODB = 'mongodb'
    ORACLE = 'oracle'
    SQLSERVER = 'sqlserver'
    DYNAMODB = 'dynamodb'
    CASSANDRA = 'cassandra'


class TransformationRecommendation(BaseModel):
    """A transformation recommendation for TMF ODA compliance."""
    
    category: str = Field(description="Category of the recommendation")
    priority: str = Field(description="Priority level (HIGH, MEDIUM, LOW)")
    title: str = Field(description="Short title of the recommendation")
    description: str = Field(description="Detailed description of the recommendation")
    impact: str = Field(description="Expected impact of implementing the recommendation")
    effort: str = Field(description="Estimated effort required (MINIMAL, MODERATE, SIGNIFICANT)")


class SchemaAnalysisIssue(BaseModel):
    """An issue identified during schema analysis."""
    
    severity: str = Field(description="Issue severity (ERROR, WARNING, INFO)")
    path: str = Field(description="Path to the schema element with the issue")
    message: str = Field(description="Description of the issue")
    suggestion: Optional[str] = Field(None, description="Suggested fix for the issue")


class SchemaFile(BaseModel):
    """Information about a discovered schema file."""
    
    file_path: str = Field(description="Absolute path to the schema file")
    file_name: str = Field(description="Name of the schema file")
    file_size: int = Field(description="Size of the file in bytes")
    format: Optional[SchemaFormat] = Field(None, description="Detected schema format")
    last_modified: datetime = Field(description="Last modification timestamp")


class SchemaAnalysisResult(BaseModel):
    """Result of schema analysis for a single file."""
    
    schema_file: SchemaFile = Field(description="Information about the analyzed schema file")
    compliance_level: ComplianceLevel = Field(description="TMF ODA compliance level")
    compliance_score: float = Field(ge=0.0, le=100.0, description="Compliance score (0-100)")
    issues: List[SchemaAnalysisIssue] = Field(description="List of identified issues")
    recommendations: List[TransformationRecommendation] = Field(description="Transformation recommendations")
    analysis_duration: float = Field(description="Analysis duration in seconds")


class SchemaAnalysisReport(BaseModel):
    """Complete schema analysis report."""
    
    workspace_dir: str = Field(description="Directory that was analyzed")
    oda_component_type: TMFODAComponentType = Field(description="Target TMF ODA component type")
    schema_format_filter: Optional[SchemaFormat] = Field(None, description="Schema format filter applied")
    total_files_found: int = Field(description="Total number of schema files found")
    total_files_analyzed: int = Field(description="Number of files successfully analyzed")
    analysis_status: AnalysisStatus = Field(description="Overall analysis status")
    analysis_timestamp: datetime = Field(description="When the analysis was performed")
    analysis_duration: float = Field(description="Total analysis duration in seconds")
    results: List[SchemaAnalysisResult] = Field(description="Individual schema analysis results")
    summary: Dict[str, Union[int, float]] = Field(description="Summary statistics")


class DatabaseTable(BaseModel):
    """Information about a database table or collection."""
    
    name: str = Field(description="Name of the table/collection")
    schema_name: Optional[str] = Field(None, description="Schema name (for SQL databases)")
    type: str = Field(description="Type (table, view, collection, etc.)")
    row_count: Optional[int] = Field(None, description="Approximate number of rows")
    size_mb: Optional[float] = Field(None, description="Size in MB")


class DatabaseColumn(BaseModel):
    """Information about a database column or field."""
    
    name: str = Field(description="Name of the column/field")
    data_type: str = Field(description="Data type")
    is_nullable: bool = Field(description="Whether the column can be null")
    is_primary_key: bool = Field(description="Whether this is a primary key")
    default_value: Optional[str] = Field(None, description="Default value if any")
    constraints: List[str] = Field(description="List of constraints")


class DatabaseSchema(BaseModel):
    """Database schema information."""
    
    table: DatabaseTable = Field(description="Table information")
    columns: List[DatabaseColumn] = Field(description="Column information")


class DatabaseAnalysisResult(BaseModel):
    """Result of database analysis."""
    
    database_schema: DatabaseSchema = Field(description="Database schema information")
    compliance_level: ComplianceLevel = Field(description="TMF ODA compliance level")
    compliance_score: float = Field(ge=0.0, le=100.0, description="Compliance score (0-100)")
    recommendations: List[TransformationRecommendation] = Field(description="Transformation recommendations")
    analysis_duration: float = Field(description="Analysis duration in seconds")


class DatabaseAnalysisReport(BaseModel):
    """Complete database analysis report."""
    
    connection_string: str = Field(description="Database connection string (sanitized)")
    database_type: DatabaseType = Field(description="Type of database analyzed")
    oda_component_type: TMFODAComponentType = Field(description="Target TMF ODA component type")
    tables_filter: Optional[str] = Field(None, description="Tables filter applied")
    total_tables_found: int = Field(description="Total number of tables found")
    total_tables_analyzed: int = Field(description="Number of tables successfully analyzed")
    analysis_status: AnalysisStatus = Field(description="Overall analysis status")
    analysis_timestamp: datetime = Field(description="When the analysis was performed")
    analysis_duration: float = Field(description="Total analysis duration in seconds")
    results: List[DatabaseAnalysisResult] = Field(description="Individual table analysis results")
    summary: Dict[str, Union[int, float]] = Field(description="Summary statistics")

    @field_validator('connection_string')
    @classmethod
    def sanitize_connection_string(cls, v):
        """Remove sensitive information from connection string."""
        # Remove password from connection string for security
        import re
        sanitized = re.sub(r'password=[^;]*', 'password=***', v, flags=re.IGNORECASE)
        sanitized = re.sub(r':[^@]*@', ':***@', sanitized)
        return sanitized


class JourneyCreateData(BaseModel):
    """Model for creating new journeys."""
    name: str = Field(description="Human-readable name for the journey")
    description: Optional[str] = Field(default="", description="Optional description of the journey")
    oda_component_type: TMFODAComponentType = Field(description="Target TMF ODA component type")
    source_type: str = Field(default="database", description="Source type (database, schema, api)")
    stages: Optional[List[str]] = Field(
        default=["raw_analysis", "stripped_schema", "data_mapping", "compliance_validation"],
        description="List of stage IDs for this journey"
    )
    priority: str = Field(default="medium", description="Journey priority (low, medium, high)")
    source_schema_name: Optional[str] = Field(default=None, description="Source schema name")
    source_schema_id: Optional[str] = Field(default=None, description="Source schema ID")


class JourneyUpdateData(BaseModel):
    """Model for updating existing journeys."""
    name: Optional[str] = Field(default=None, description="Updated journey name")
    description: Optional[str] = Field(default=None, description="Updated description")
    status: Optional[str] = Field(default=None, description="Updated status (pending, running, completed, failed)")
    overall_progress: Optional[int] = Field(default=None, description="Updated progress percentage (0-100)")
    current_stage: Optional[str] = Field(default=None, description="Updated current stage ID")
    priority: Optional[str] = Field(default=None, description="Updated priority") 