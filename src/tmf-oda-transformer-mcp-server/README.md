# TMF ODA Transformer MCP Server

An AWS Labs Model Context Protocol (MCP) server that provides comprehensive tools for analyzing and transforming data structures for TMF ODA (TM Forum Open Digital Architecture) compliance.

## Overview

This MCP server provides specialized tools to analyze schema files and databases, execute transformation workflows, and manage TMF ODA compliance journeys. It helps developers understand how their current data structures align with TMF Open Digital Architecture specifications and provides actionable transformation pathways.

## ✨ Features

- **🔍 Schema Analysis**: Discover and analyze schema files (JSON Schema, OpenAPI, Avro, etc.) for TMF ODA transformation
- **🗄️ Database Analysis**: Analyze database structures and suggest TMF ODA-compliant transformations for multiple database types
- **⚡ Transformation Workflows**: Execute multi-stage transformation journeys with proper job management
- **📋 Job Monitoring**: Track and retrieve detailed execution logs from transformation processes
- **🔒 AWS Integration**: Secure credential handling with support for EC2 instance roles and role assumption
- **🧪 Comprehensive Testing**: 71+ test cases ensuring reliability and quality
- **🔧 Built-in Test Runner**: Run verification tests directly through MCP interface
- **📊 Multi-format Support**: Support for various schema formats and database types

## 🛠️ Tools

### 🔍 schema-analyzer
Discovers and analyzes schema files in a workspace for TMF ODA transformation requirements.

**Parameters:**
- `workspace_dir` *(required)*: Directory path to analyze for schema files
- `oda_component_type` *(required)*: Target TMF ODA component type for analysis
- `schema_format` *(optional)*: Filter for specific schema formats (json-schema, openapi, swagger, avro, protobuf, yaml-schema)

**Returns:** Comprehensive analysis report with:
- Schema compliance assessment and scoring
- Detailed transformation recommendations
- Issue identification with severity levels
- Summary statistics and metadata

**Example Usage:**
```
Analyze all JSON schemas in my current workspace for TMF ODA Product Catalog transformation.
```

### 🗄️ db-analyzer
Connects to and analyzes database structures for TMF ODA transformation requirements.

**Parameters:**
- `connection_string` *(required)*: Database connection string (PostgreSQL, MySQL, MongoDB, etc.)
- `database_type` *(required)*: Type of database (postgresql, mysql, mongodb, oracle, sqlserver, dynamodb, cassandra)
- `oda_component_type` *(required)*: Target TMF ODA component type for analysis
- `tables_filter` *(optional)*: Filter for specific tables/collections (e.g., 'user_*,product_*')

**Returns:** Database analysis report with:
- Table/collection compliance assessment
- Schema mapping recommendations
- Column/field transformation suggestions
- Security and performance considerations

**Example Usage:**
```
Analyze my PostgreSQL database at "postgresql://user:pass@localhost:5432/mydb" for TMF ODA Customer Management compatibility.
```

### ⚡ raw-analysis
Executes the raw analysis stage of a TMF ODA transformation journey.

**Parameters:**
- `journey_id` *(required)*: Unique identifier for the transformation journey (e.g., 'JRN-SAMPLE-001')
- `stage_id` *(optional)*: Stage identifier (defaults to 'raw_analysis')
- `triggered_by` *(optional)*: Who triggered the execution (defaults to 'mcp-server')
- `reason` *(optional)*: Reason for execution (defaults to 'MCP Server execution')

**Returns:** Job execution result with:
- Job ID and execution status
- Timing information and duration
- Success/error details and messages
- Stage-specific processing information

**Processing Includes:**
- Schema file parsing and structure analysis
- Relationship discovery between entities
- Data type analysis for TMF ODA compatibility
- Business rules extraction and complexity assessment

**Example Usage:**
```
Execute raw analysis for journey 'JRN-CUSTOMER-001' to analyze the initial database schema.
```

### 🔧 stripped-schema
Executes the stripped schema stage of a TMF ODA transformation journey.

**Parameters:**
- `journey_id` *(required)*: Unique identifier for the transformation journey
- `stage_id` *(optional)*: Stage identifier (defaults to 'stripped_schema')
- `triggered_by` *(optional)*: Who triggered the execution (defaults to 'mcp-server')
- `reason` *(optional)*: Reason for execution (defaults to 'MCP Server execution')

**Returns:** Job execution result with processing details and status information.

**Processing Includes:**
- Schema stripping to remove non-essential elements
- Core structure extraction for TMF ODA compliance
- Data model simplification and standardization
- Preparation for subsequent transformation stages

**Example Usage:**
```
Execute stripped schema stage for journey 'JRN-CUSTOMER-001' after raw analysis completion.
```

### 📋 get-job-logs
Retrieves detailed execution logs for specific job steps from S3 storage.

**Parameters:**
- `journey_id` *(required)*: The transformation journey identifier
- `stage_name` *(required)*: Stage name (e.g., 'raw_analysis', 'stripped_schema')
- `job_id` *(required)*: Job execution identifier (e.g., 'JOB-016-20250709170359')
- `step_name` *(required)*: Specific step name to retrieve logs for

**Step Names Include:**
- **Raw Analysis**: `schema_parsing`, `relationship_discovery`, `data_type_analysis`, `business_rules_extraction`, `complexity_assessment`
- **Stripped Schema**: `schema_stripping`, `core_structure_extraction`, `data_model_simplification`

**Returns:** Detailed log information including:
- Log entries with timestamps and severity levels
- Processing metrics and execution details
- Error messages and debugging information
- S3 metadata and file information

**Example Usage:**
```
Retrieve logs for schema_parsing step of job 'JOB-016-20250709170359' in journey 'JRN-SAMPLE-001'.
```

### 🧪 test-runner
Runs comprehensive verification tests for all TMF ODA transformer tools directly through the MCP interface.

**Parameters:**
- `test_type` *(optional)*: Type of tests to run (defaults to 'comprehensive')
  - `quick` - Basic import checks only  
  - `comprehensive` - All validation tests
  - `imports` - Import tests only
- `include_performance` *(optional)*: Whether to include performance timing tests (defaults to false)

**Returns:** Comprehensive test results with:
- Pass/fail status for each test category
- Detailed error messages and debugging information
- Success rate calculations and performance metrics
- Actionable recommendations and next steps
- Summary of tools verified and validation results

**Test Coverage Includes:**
- **Import Verification**: Tests that all modules can be imported successfully
- **Parameter Validation**: Verifies tools properly validate input parameters
- **Error Handling**: Ensures tools handle edge cases and errors gracefully
- **Integration Testing**: Validates tool interaction with AWS services
- **Performance Analysis**: Optional timing and resource usage metrics

**Example Usage:**
```
Run comprehensive verification tests to ensure all TMF ODA tools are working correctly.
```

```
Run quick import tests only to verify basic functionality.
```

**Benefits:**
- 🚀 **No Terminal Issues**: Runs directly through Cursor as an MCP tool
- 📊 **Comprehensive Reporting**: Detailed results with recommendations
- ⚡ **Multiple Test Types**: Choose the right level of testing for your needs
- 🔍 **Error Diagnostics**: Specific error messages to help troubleshoot issues
- 📈 **Performance Insights**: Optional timing data for optimization

## 📦 Installation

### Using uvx (Recommended)
```bash
uvx awslabs.tmf-oda-transformer-mcp-server@latest
```

### Using pip
```bash
pip install awslabs.tmf-oda-transformer-mcp-server
```

### Development Installation
```bash
git clone <repository-url>
cd tmf-oda-transformer-mcp-server
pip install -e .
```

## ⚙️ Configuration

### Basic Configuration (EC2 Instance with Instance Role)
```json
{
  "mcpServers": {
    "awslabs.tmf-oda-transformer-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.tmf-oda-transformer-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Configuration for External Machines (Role ARN)
```json
{
  "mcpServers": {
    "awslabs.tmf-oda-transformer-mcp-server": {
      "command": "uvx", 
      "args": ["awslabs.tmf-oda-transformer-mcp-server@latest"],
      "env": {
        "AWS_ROLE_ARN": "arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "INFO",
        "TMF_ODA_REFERENCE_PATH": "/path/to/tmf-oda-references"
      }
    }
  }
}
```

### Advanced Configuration with Database Support
```json
{
  "mcpServers": {
    "awslabs.tmf-oda-transformer-mcp-server": {
      "command": "uvx", 
      "args": ["awslabs.tmf-oda-transformer-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "your-aws-profile",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "INFO",
        "TMF_ODA_REFERENCE_PATH": "/path/to/tmf-oda-references"
      }
    }
  }
}
```

## 🔧 Environment Variables

- `AWS_ROLE_ARN`: AWS role ARN to assume (for external machines) *(optional)*
- `AWS_PROFILE`: AWS profile for accessing AWS services *(optional)*
- `AWS_REGION`: AWS region for service connections *(optional)*  
- `TMF_ODA_REFERENCE_PATH`: Path to TMF ODA reference schemas *(optional)*
- `FASTMCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## 🔐 AWS Authentication

The TMF ODA Transformer MCP Server supports multiple AWS authentication methods:

### 1. EC2 Instance Role (Recommended for EC2)
When running on an EC2 instance, the server automatically uses the instance role. No additional configuration is required.

### 2. Role ARN Assumption (Recommended for External Machines)
When running from outside AWS, specify the role ARN to assume:

```bash
export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole"
```

**Prerequisites:**
- Your local AWS credentials must have permission to assume the specified role
- The role must have the necessary permissions for DynamoDB and S3 operations

### 3. AWS Profile (Local Development)
Use AWS profiles for local development:

```bash
export AWS_PROFILE="your-profile-name"
```

### 4. Environment Variables
Set AWS credentials directly:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_SESSION_TOKEN="your-session-token"  # Optional
```

## 🔑 Required AWS Permissions

The role or credentials used must have the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/TransformationSystem*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::transformation-journey-logs",
        "arn:aws:s3:::transformation-journey-logs/*",
        "arn:aws:s3:::transformation-journey-reports",
        "arn:aws:s3:::transformation-journey-reports/*"
      ]
    }
  ]
}
```

## 📋 TMF ODA Component Types

The server supports analysis for various TMF ODA component types:

- **Product Catalog Management** - Product and service catalog analysis
- **Customer Management** - Customer data and relationship analysis
- **Order Management** - Order processing and workflow analysis
- **Service Inventory Management** - Service inventory and configuration analysis
- **Resource Inventory Management** - Physical and logical resource analysis
- **Party Management** - Party roles and relationship analysis
- **Account Management** - Billing account and financial analysis
- **Billing Management** - Billing and charging process analysis
- **Product Offering Qualification** - Product qualification workflow analysis
- **Service Qualification** - Service availability and qualification analysis
- **Quote Management** - Pricing and quotation process analysis
- **Service Ordering** - Service order and fulfillment analysis
- **Product Ordering** - Product order and delivery analysis

## 🧪 Testing & Quality Assurance

### Comprehensive Test Suite (71+ Test Cases)

The TMF ODA Transformer MCP Server includes a comprehensive test suite ensuring reliability and quality:

#### Test Coverage
- **✅ Unit Tests**: Individual tool functionality testing
- **✅ Integration Tests**: AWS service interaction testing
- **✅ Error Handling**: Comprehensive error scenario coverage
- **✅ Performance Tests**: Timing and resource usage validation
- **✅ Security Tests**: Credential handling and data protection

#### Running Tests

```bash
# Quick verification of all tools
python verify_tools.py

# Run comprehensive test suite
python tests/test_runner.py

# Run specific tool tests
python -m pytest tests/test_schema_analyzer.py -v
python -m pytest tests/test_db_analyzer.py -v
python -m pytest tests/test_raw_analysis.py -v
python -m pytest tests/test_stripped_schema.py -v
python -m pytest tests/test_get_job_logs.py -v

# Run all tests with coverage
python -m pytest tests/ -v --cov
```

#### Test Requirements
```bash
# Install test dependencies
pip install -r tests/requirements-test.txt
```

#### Test Files Structure
```
tests/
├── README.md                 # Comprehensive test documentation
├── conftest.py              # Pytest configuration and fixtures
├── requirements-test.txt    # Test dependencies
├── test_runner.py          # Comprehensive test runner
├── test_schema_analyzer.py # Schema analyzer tool tests
├── test_db_analyzer.py     # Database analyzer tool tests
├── test_raw_analysis.py    # Raw analysis tool tests
├── test_stripped_schema.py # Stripped schema tool tests
└── test_get_job_logs.py    # Job logs retrieval tests
```

## 🚀 Usage Examples

### Schema Analysis Workflow
```
1. Use schema-analyzer to analyze JSON schemas in /path/to/schemas for Product Catalog Management
2. Review compliance assessment and recommendations
3. Execute raw-analysis for journey 'JRN-CATALOG-001' to begin transformation
4. Monitor progress with get-job-logs for detailed execution information
```

### Database Transformation Journey
```
1. Use db-analyzer to analyze PostgreSQL database for Customer Management compatibility
2. Execute raw-analysis stage for journey 'JRN-CUSTOMER-001'
3. Execute stripped-schema stage to simplify data model
4. Retrieve detailed logs for each processing step
```

### Multi-Database Analysis
```
1. Analyze PostgreSQL with db-analyzer for primary customer data
2. Analyze MongoDB with db-analyzer for document storage requirements
3. Execute parallel transformation journeys
4. Monitor all jobs with centralized log retrieval
```

## 🔒 Security

- **🔐 Secure Authentication**: Multiple AWS authentication methods with credential auto-detection
- **🛡️ Data Protection**: Read-only schema analysis with no data extraction
- **🔍 Audit Trail**: Comprehensive logging and execution tracking
- **🚫 Credential Safety**: Automatic password sanitization in logs and reports
- **⚡ Secure Connections**: TLS/SSL for all database and AWS service connections
- **🎯 Least Privilege**: Fine-grained AWS IAM permissions for specific resources only

## 🏗️ Architecture

### Refactored Structure
The MCP server has been refactored for improved maintainability:

```
awslabs/tmf_oda_transformer_mcp_server/
├── server.py              # Main MCP server with all tools
├── models.py              # Data models and enums
├── consts.py             # Constants and configuration
├── scripts/              # Transformation execution scripts
│   ├── __init__.py
│   ├── job_executor.py   # Job execution management
│   ├── aws_client_utils.py # AWS service utilities
│   └── stages/           # Transformation stage implementations
│       ├── __init__.py
│       ├── base_stage.py
│       ├── raw_analysis.py
│       └── stripped_schema.py
└── tests/                # Comprehensive test suite
    └── ... (71+ test cases)
```

### Key Improvements
- **📦 Self-Contained**: All dependencies moved into server directory structure
- **🔧 Modular Design**: Clear separation of concerns with stage-based architecture
- **🧪 Testable**: Comprehensive test coverage with mocking and fixtures
- **📚 Documented**: Extensive documentation and usage examples
- **🔄 Maintainable**: Clean code structure with consistent patterns

## 🤝 Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on contributing to this project.

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd tmf-oda-transformer-mcp-server

# Install in development mode
pip install -e .

# Install test dependencies
pip install -r tests/requirements-test.txt

# Run tests
python verify_tools.py
```

## 📄 License

This project is licensed under the Apache-2.0 License - see the [LICENSE](LICENSE) file for details.

---

**🌟 TMF ODA Transformer MCP Server** - Comprehensive tools for TMF Open Digital Architecture compliance analysis and transformation workflows. 