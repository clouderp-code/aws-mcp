"""
Pytest configuration and shared fixtures for TMF ODA transformer MCP server tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from awslabs.tmf_oda_transformer_mcp_server.models import TMFODAComponentType, SchemaFormat, DatabaseType


@pytest.fixture
def mock_context():
    """Create a mock MCP context for testing."""
    ctx = Mock()
    ctx.error = AsyncMock()
    return ctx


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing schema analysis."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test schema files
        schema_dir = Path(temp_dir) / "schemas"
        schema_dir.mkdir()
        
        # Create a JSON schema file
        json_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["id", "name"]
        }
        
        (schema_dir / "customer.json").write_text(
            '{"type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}'
        )
        
        # Create an OpenAPI schema file
        (schema_dir / "api.yaml").write_text("""
openapi: 3.0.0
info:
  title: Customer API
  version: 1.0.0
paths:
  /customers:
    get:
      responses:
        200:
          description: List of customers
""")
        
        # Create an Avro schema file
        (schema_dir / "product.avsc").write_text("""
{
  "type": "record",
  "name": "Product",
  "fields": [
    {"name": "id", "type": "string"},
    {"name": "name", "type": "string"},
    {"name": "price", "type": "double"}
  ]
}
""")
        
        yield temp_dir


@pytest.fixture
def sample_journey_id():
    """Sample journey ID for testing."""
    return "JRN-TEST-001"


@pytest.fixture
def sample_job_id():
    """Sample job ID for testing."""
    return "JOB-001-20240101120000"


@pytest.fixture
def valid_connection_strings():
    """Valid database connection strings for testing."""
    return {
        "postgresql": "postgresql://user:password@localhost:5432/testdb",
        "mysql": "mysql://user:password@localhost:3306/testdb",
        "mongodb": "mongodb://user:password@localhost:27017/testdb"
    }


@pytest.fixture
def oda_component_types():
    """All valid TMF ODA component types."""
    return [
        TMFODAComponentType.CUSTOMER_MANAGEMENT,
        TMFODAComponentType.ORDER_MANAGEMENT,
        TMFODAComponentType.PRODUCT_CATALOG_MANAGEMENT,
        TMFODAComponentType.PARTY_MANAGEMENT,
        TMFODAComponentType.ACCOUNT_MANAGEMENT,
        TMFODAComponentType.BILLING_MANAGEMENT,
    ]


@pytest.fixture
def schema_formats():
    """All valid schema formats."""
    return [
        SchemaFormat.JSON_SCHEMA,
        SchemaFormat.OPENAPI,
        SchemaFormat.SWAGGER,
        SchemaFormat.AVRO,
        SchemaFormat.PROTOBUF,
        SchemaFormat.YAML_SCHEMA,
    ]


@pytest.fixture
def database_types():
    """All valid database types."""
    return [
        DatabaseType.POSTGRESQL,
        DatabaseType.MYSQL,
        DatabaseType.MONGODB,
        DatabaseType.ORACLE,
        DatabaseType.SQLSERVER,
        DatabaseType.DYNAMODB,
        DatabaseType.CASSANDRA,
    ]


@pytest.fixture(autouse=True)
def mock_aws_credentials():
    """Mock AWS credentials to avoid actual AWS calls during testing."""
    os.environ["AWS_ACCESS_KEY_ID"] = "test_key"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test_secret"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    yield
    # Clean up
    for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"]:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def mock_transformation_job_executor():
    """Mock TransformationJobExecutor for testing job execution tools."""
    mock_executor = Mock()
    mock_executor.start_job_execution = Mock(return_value="JOB-001-20240101120000")
    mock_executor.execute_job = Mock()
    return mock_executor 